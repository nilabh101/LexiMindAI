"""LexiMind Mastery Score — a transparent, deterministic heuristic.

    score = 100 * shrink( (1 - RECENT_W) * weighted_accuracy
                          + RECENT_W * recent_accuracy )

* weighted_accuracy — every attempt counts as `difficulty_weight * recency_weight`
  evidence; a correct HARD answer is worth more than a correct EASY one, and an
  answer from six months ago is worth less than yesterday's.
* recent_accuracy — the same weighting over the last RECENT_WINDOW attempts.
* shrink — with little evidence the value is pulled toward NEUTRAL_PRIOR so a
  single lucky answer cannot yield "MASTERED".

This is a study heuristic, not a validated psychometric measurement.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    EVIDENCE_FULL_WEIGHT_ATTEMPTS,
    NEUTRAL_PRIOR,
    RECENCY_HALF_LIFE_DAYS,
    RECENCY_MIN_WEIGHT,
    RECENT_PERFORMANCE_WEIGHT,
    RECENT_WINDOW,
    concept_state,
    difficulty_weight,
)
from app.models.academic import ConceptMastery, Question, QuizAnswer, QuizSession
from app.services.review import schedule_next_review

# Legacy lowercase statuses kept for Phase 2 API compatibility.
_STATE_TO_STATUS = {
    "NOT_STARTED": "not_started",
    "VERY_WEAK": "needs_review",
    "WEAK": "needs_review",
    "DEVELOPING": "in_progress",
    "PROFICIENT": "in_progress",
    "MASTERED": "mastered",
}


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def recency_weight(attempted_at: Optional[datetime], now: Optional[datetime] = None) -> float:
    """Exponential decay: 0.5 ** (age_days / half-life), floored at a minimum."""
    if attempted_at is None:
        return 1.0
    now = now or datetime.now(timezone.utc)
    age_days = max(0.0, (now - _as_utc(attempted_at)).total_seconds() / 86400.0)
    weight = 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)
    return max(RECENCY_MIN_WEIGHT, weight)


def _weighted_accuracy(attempts: Sequence[Dict], now: datetime) -> float:
    total = 0.0
    earned = 0.0
    for a in attempts:
        w = difficulty_weight(a.get("difficulty")) * recency_weight(a.get("attempted_at"), now)
        total += w
        if a.get("correct"):
            earned += w
    return (earned / total) if total else 0.0


def calculate_mastery(attempts: Iterable[Dict], now: Optional[datetime] = None) -> Dict:
    """Compute the LexiMind Mastery Score from a concept's attempt history.

    `attempts` is an iterable of dicts with keys: correct (bool),
    difficulty (str | None), attempted_at (datetime | None), oldest first.
    """
    now = now or datetime.now(timezone.utc)
    items: List[Dict] = list(attempts)
    attempted = len(items)
    if attempted == 0:
        return {
            "mastery_score": 0.0,
            "confidence": 0.0,
            "state": "NOT_STARTED",
            "status": "not_started",
            "accuracy": 0.0,
            "attempted": 0,
            "correct": 0,
            "incorrect": 0,
            "streak": 0,
        }

    correct = sum(1 for a in items if a.get("correct"))
    overall = _weighted_accuracy(items, now)
    recent_items = items[-RECENT_WINDOW:]
    recent = _weighted_accuracy(recent_items, now)

    blended = (1 - RECENT_PERFORMANCE_WEIGHT) * overall + RECENT_PERFORMANCE_WEIGHT * recent
    evidence = min(1.0, attempted / EVIDENCE_FULL_WEIGHT_ATTEMPTS)
    shrunk = evidence * blended + (1 - evidence) * NEUTRAL_PRIOR

    score = round(shrunk * 100, 1)
    streak = 0
    for a in reversed(items):
        if a.get("correct"):
            streak += 1
        else:
            break

    return {
        "mastery_score": score,
        "confidence": round(min(0.95, 0.2 + 0.1 * attempted), 2),
        "state": concept_state(score, attempted),
        "status": _STATE_TO_STATUS[concept_state(score, attempted)],
        "accuracy": round((correct / attempted) * 100, 1),
        "attempted": attempted,
        "correct": correct,
        "incorrect": attempted - correct,
        "streak": streak,
        "recent_accuracy": round(recent * 100, 1),
    }


def compute_mastery(correct: int, attempted: int) -> Dict:
    """Backwards-compatible helper: mastery from plain counts (no history)."""
    attempts = [{"correct": i < correct, "difficulty": None, "attempted_at": None}
                for i in range(max(attempted, 0))]
    return calculate_mastery(attempts)


async def _load_attempts(db: AsyncSession, user_id: str, concept_ids: Sequence[str]) -> Dict[str, List[Dict]]:
    """Attempt history per concept for one user (single query, no N+1)."""
    if not concept_ids:
        return {}
    rows = (await db.execute(
        select(QuizAnswer).where(
            QuizAnswer.user_id == user_id,
            QuizAnswer.concept_id.in_(list(concept_ids)),
        ).order_by(QuizAnswer.created_at.asc(), QuizAnswer.id.asc())
    )).scalars().all()
    history: Dict[str, List[Dict]] = {cid: [] for cid in concept_ids}
    for r in rows:
        history.setdefault(r.concept_id, []).append({
            "correct": bool(r.correct),
            "difficulty": r.difficulty,
            "attempted_at": _as_utc(r.created_at),
            "question_id": r.question_id,
        })
    return history


async def recalculate_concept_mastery(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    subject_id: Optional[str] = None,
    session_accuracy: Optional[float] = None,
    now: Optional[datetime] = None,
) -> ConceptMastery:
    """Recompute and persist mastery for one user + concept from full history."""
    now = now or datetime.now(timezone.utc)
    attempts = (await _load_attempts(db, user_id, [concept_id])).get(concept_id, [])
    computed = calculate_mastery(attempts, now=now)

    row = (await db.execute(
        select(ConceptMastery).where(
            ConceptMastery.user_id == user_id,
            ConceptMastery.concept_id == concept_id,
        )
    )).scalar_one_or_none()
    if not row:
        row = ConceptMastery(user_id=user_id, concept_id=concept_id)
        db.add(row)

    row.subject_id = subject_id or row.subject_id
    row.mastery_score = computed["mastery_score"]
    row.questions_attempted = computed["attempted"]
    row.questions_correct = computed["correct"]
    row.questions_incorrect = computed["incorrect"]
    row.confidence = computed["confidence"]
    row.state = computed["state"]
    row.status = computed["status"]
    row.streak = computed["streak"]
    row.updated_at = now
    if attempts:
        row.last_attempted = attempts[-1]["attempted_at"] or now
        last_correct = next((a["attempted_at"] for a in reversed(attempts) if a["correct"]), None)
        if last_correct:
            row.last_correct_at = last_correct

    if session_accuracy is not None:
        interval, next_at = schedule_next_review(row.review_interval_days, session_accuracy, now=now)
        row.review_interval_days = interval
        row.next_review_at = next_at
    elif attempts and row.next_review_at is None:
        # Any concept with history gets a review date, based on its overall accuracy.
        accuracy = computed["correct"] / max(computed["attempted"], 1)
        row.review_interval_days, row.next_review_at = schedule_next_review(None, accuracy, now=now)

    return row


async def apply_quiz_results(
    db: AsyncSession,
    user_id: str,
    quiz_id: str,
    answers: List[Dict],
    subject_id: str = None,
) -> Dict:
    """Persist a completed quiz: attempts, session, mastery, review schedule."""
    now = datetime.now(timezone.utc)
    correct_count = 0
    by_concept: Dict[str, Dict[str, int]] = {}

    question_ids = []
    for a in answers:
        qid = a.get("question_id")
        try:
            question_ids.append(int(qid)) if qid not in (None, "", 0, "0") else None
        except (TypeError, ValueError):
            pass
    question_rows = {}
    if question_ids:
        question_rows = {
            q.id: q for q in (await db.execute(
                select(Question).where(Question.id.in_(question_ids))
            )).scalars().all()
        }

    for a in answers:
        qid = a.get("question_id")
        selected = a.get("selected_answer")
        is_correct = bool(a.get("correct") or a.get("isCorrect"))
        time_taken = a.get("time_taken") or a.get("timeTaken")
        qid_int = None
        try:
            if qid not in (None, "", 0, "0"):
                qid_int = int(qid)
        except (TypeError, ValueError):
            qid_int = None

        question = question_rows.get(qid_int) if qid_int else None
        concept_id = a.get("concept_id") or (question.concept_id if question else None)
        difficulty = a.get("difficulty") or (question.difficulty if question else None)
        correct_answer = a.get("correct_answer") or (question.answer if question else None)

        if is_correct:
            correct_count += 1
        db.add(QuizAnswer(
            user_id=user_id,
            quiz_id=quiz_id,
            question_id=qid_int,
            selected_answer=None if selected is None else str(selected),
            correct_answer=correct_answer,
            correct=is_correct,
            time_taken=float(time_taken) if time_taken is not None else None,
            concept_id=concept_id,
            difficulty=(difficulty or "").upper() or None,
            created_at=now,
        ))
        if concept_id:
            bucket = by_concept.setdefault(concept_id, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if is_correct:
                bucket["correct"] += 1

    total = len(answers)
    accuracy = round((correct_count / total) * 100, 1) if total else 0.0
    db.add(QuizSession(
        quiz_id=quiz_id,
        user_id=user_id,
        subject_id=subject_id,
        score=accuracy,
        accuracy=accuracy,
        correct_count=correct_count,
        total_count=total,
        completed_at=now,
        question_ids=[a.get("question_id") for a in answers],
    ))
    await db.flush()

    performances = []
    for concept_id, stats in by_concept.items():
        session_accuracy = stats["correct"] / stats["total"] if stats["total"] else 0.0
        row = await recalculate_concept_mastery(
            db, user_id, concept_id,
            subject_id=subject_id,
            session_accuracy=session_accuracy,
            now=now,
        )
        performances.append({
            "conceptId": concept_id,
            "mastery_score": row.mastery_score,
            "confidence": row.confidence,
            "state": row.state,
            "status": row.status,
            "streak": row.streak,
            "nextReviewAt": row.next_review_at.isoformat() if row.next_review_at else None,
            **stats,
        })

    await db.flush()
    return {
        "quiz_id": quiz_id,
        "user_id": user_id,
        "score": accuracy,
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total,
        "concept_performance": performances,
    }


def build_learning_path(concepts: List[Dict], mastery_rows: List[ConceptMastery]) -> Dict:
    """Legacy Phase 2 shape; Phase 3 logic lives in services.learning_path."""
    from app.services.learning_path import build_path

    return build_path(concepts, mastery_rows)
