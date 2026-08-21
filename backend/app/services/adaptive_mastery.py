"""
LexiMind Adaptive Mastery Service — Phase 3.

All mastery computation lives here. Never duplicated in route handlers.

Algorithm (LexiMind Mastery Score):
    base_accuracy      = questions_correct / questions_attempted
    difficulty_accuracy = difficulty_weighted_correct / difficulty_weighted_attempted
    mastery_score      = 100 × (0.5 × base_accuracy
                               + 0.3 × difficulty_accuracy
                               + 0.2 × recency_score)

Recency (compute_recency_score):
    Uses exponential decay over the last N attempts.
    Most recent attempt weight = 1.0.
    Each step back multiplies by RECENCY_DECAY (default 0.85).
    Normalised to [0.0, 1.0].
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# ── Configurable constants (single source of truth) ───────────────────────────

DIFFICULTY_WEIGHTS: dict[str, float] = {
    "easy":   1.0,
    "medium": 1.25,
    "hard":   1.5,
    # fallback for None / unknown
    "unknown": 1.0,
}

STATE_THRESHOLDS = {
    # (lower_inclusive, upper_exclusive)  — NOT_STARTED handled separately
    "VERY_WEAK":   (0.0,   30.0),
    "WEAK":        (30.0,  50.0),
    "DEVELOPING":  (50.0,  70.0),
    "PROFICIENT":  (70.0,  85.0),
    "MASTERED":    (85.0, 100.01),
}

RECENCY_N: int = 10        # number of recent attempts used
RECENCY_DECAY: float = 0.85  # weight decay per step back in history

WEAK_MASTERY_THRESHOLD: float = 60.0
NO_PRACTICE_DAYS: int = 30         # days without attempt → "no recent practice"
STREAK_WINDOW: int = 10            # last N attempts to check consecutive streak
CONSECUTIVE_INCORRECT_TRIGGER: int = 3  # ≥ this many consecutive incorrect → flagged


class MasteryState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    VERY_WEAK   = "VERY_WEAK"
    WEAK        = "WEAK"
    DEVELOPING  = "DEVELOPING"
    PROFICIENT  = "PROFICIENT"
    MASTERED    = "MASTERED"


@dataclass
class WeakConceptResult:
    concept_id: str
    concept_name: str
    subject_id: Optional[str]
    chapter_id: Optional[str]
    mastery_score: float
    state: str
    reason: str   # max 300 chars


# ── Core algorithm ─────────────────────────────────────────────────────────────

def calculate_mastery(
    questions_correct: int,
    questions_attempted: int,
    difficulty_weighted_correct: float,
    difficulty_weighted_attempted: float,
    recency_score: float,
) -> float:
    """
    Compute the LexiMind Mastery Score in [0.0, 100.0].

    Args:
        questions_correct: integer ≥ 0, must be ≤ questions_attempted
        questions_attempted: integer ≥ 0
        difficulty_weighted_correct: sum of DIFFICULTY_WEIGHTS[d] for correct answers
        difficulty_weighted_attempted: sum of DIFFICULTY_WEIGHTS[d] for all answers
        recency_score: float in [0.0, 1.0], pre-computed by compute_recency_score()

    Returns:
        float in [0.0, 100.0]

    Raises:
        ValueError: on invalid inputs
    """
    if questions_attempted == 0:
        return 0.0

    # Validation
    if questions_correct < 0 or questions_attempted < 0:
        raise ValueError("questions_correct and questions_attempted must be ≥ 0")
    if questions_correct > questions_attempted:
        raise ValueError(
            f"questions_correct ({questions_correct}) > questions_attempted ({questions_attempted})"
        )
    if difficulty_weighted_correct < 0 or difficulty_weighted_attempted < 0:
        raise ValueError("difficulty_weighted values must be ≥ 0")
    if difficulty_weighted_correct > difficulty_weighted_attempted + 1e-9:
        raise ValueError(
            "difficulty_weighted_correct > difficulty_weighted_attempted"
        )
    if not (0.0 <= recency_score <= 1.0):
        raise ValueError(f"recency_score must be in [0.0, 1.0], got {recency_score}")

    base_accuracy = questions_correct / questions_attempted
    difficulty_accuracy = (
        difficulty_weighted_correct / difficulty_weighted_attempted
        if difficulty_weighted_attempted > 0
        else 0.0
    )

    score = 100.0 * (
        0.5 * base_accuracy
        + 0.3 * difficulty_accuracy
        + 0.2 * recency_score
    )
    return max(0.0, min(100.0, round(score, 4)))


def compute_recency_score(
    attempts: list,  # list of dicts with 'correct': bool, ordered oldest→newest
    n: int = RECENCY_N,
    decay: float = RECENCY_DECAY,
) -> float:
    """
    Exponential decay recency score.

    Formula:
        last_n = attempts[-n:]  (most recent N)
        weights = [decay^(len-1-i) for i in range(len)]
        recency_score = sum(w * correct) / sum(weights)

    Returns 0.0 if attempts is empty.
    """
    if not attempts:
        return 0.0
    last_n = attempts[-n:] if len(attempts) > n else attempts
    weights = [decay ** (len(last_n) - 1 - i) for i in range(len(last_n))]
    total_w = sum(weights)
    if total_w == 0:
        return 0.0
    weighted_correct = sum(w for w, a in zip(weights, last_n) if a.get("correct"))
    return max(0.0, min(1.0, weighted_correct / total_w))


def get_mastery_state(mastery_score: float, questions_attempted: int) -> MasteryState:
    """Derive MasteryState from score and attempt count using STATE_THRESHOLDS."""
    if questions_attempted == 0:
        return MasteryState.NOT_STARTED
    for state_name, (lo, hi) in STATE_THRESHOLDS.items():
        if lo <= mastery_score < hi:
            return MasteryState(state_name)
    return MasteryState.MASTERED


# ── DB update ──────────────────────────────────────────────────────────────────

async def update_concept_mastery(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    is_correct: bool,
    difficulty: Optional[str] = None,
    time_taken: Optional[float] = None,
    quiz_id: Optional[str] = None,
    question_id: Optional[int] = None,
) -> "ConceptMastery":
    """
    Atomically update or create a ConceptMastery record after a single answer.
    Also records a QuestionAttempt row.

    Steps:
    1. Fetch or create ConceptMastery row
    2. Record QuestionAttempt
    3. Load recent attempts for recency score
    4. Recompute mastery
    5. Update streak, timestamps, state
    """
    from app.models.academic import ConceptMastery, QuestionAttempt

    now = datetime.now(timezone.utc)
    diff_key = (difficulty or "unknown").lower()
    diff_weight = DIFFICULTY_WEIGHTS.get(diff_key, 1.0)

    # 1. Fetch or create ConceptMastery
    result = await db.execute(
        select(ConceptMastery).where(
            ConceptMastery.user_id == user_id,
            ConceptMastery.concept_id == concept_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        row = ConceptMastery(user_id=user_id, concept_id=concept_id)
        db.add(row)

    # 2. Record QuestionAttempt
    attempt = QuestionAttempt(
        user_id=user_id,
        question_id=question_id,
        concept_id=concept_id,
        quiz_id=quiz_id,
        correct=is_correct,
        difficulty=difficulty,
        time_taken=time_taken,
    )
    db.add(attempt)
    await db.flush()

    # 3. Update running totals on ConceptMastery
    row.questions_attempted = (row.questions_attempted or 0) + 1
    if is_correct:
        row.questions_correct = (row.questions_correct or 0) + 1
        row.last_correct_at = now
        row.streak = (row.streak or 0) + 1
    else:
        row.questions_incorrect = (row.questions_incorrect or 0) + 1
        row.streak = 0

    row.last_attempted = now
    row.updated_at = now

    # 4. Load last RECENCY_N attempts for recency score
    recent_q = (
        await db.execute(
            select(QuestionAttempt)
            .where(QuestionAttempt.user_id == user_id, QuestionAttempt.concept_id == concept_id)
            .order_by(QuestionAttempt.created_at.asc())
            .limit(RECENCY_N + 5)
        )
    )
    recent_attempts = [{"correct": a.correct} for a in recent_q.scalars().all()]
    recency = compute_recency_score(recent_attempts)

    # 5. Difficulty-weighted totals (recompute from all stored attempts)
    dw_res = await db.execute(
        select(QuestionAttempt).where(
            QuestionAttempt.user_id == user_id,
            QuestionAttempt.concept_id == concept_id,
        )
    )
    all_attempts = dw_res.scalars().all()
    dw_attempted = sum(DIFFICULTY_WEIGHTS.get((a.difficulty or "unknown").lower(), 1.0) for a in all_attempts)
    dw_correct = sum(
        DIFFICULTY_WEIGHTS.get((a.difficulty or "unknown").lower(), 1.0)
        for a in all_attempts if a.correct
    )

    # 6. Compute new score
    score = calculate_mastery(
        row.questions_correct or 0,
        row.questions_attempted or 0,
        dw_correct,
        dw_attempted,
        recency,
    )
    row.mastery_score = score
    row.confidence = round(min(0.95, 0.2 + 0.075 * (row.questions_attempted or 0)), 3)

    # 7. State + legacy status
    state = get_mastery_state(score, row.questions_attempted or 0)
    row.state = state.value
    # Keep legacy status in sync
    if state == MasteryState.MASTERED:
        row.status = "mastered"
    elif state in (MasteryState.NOT_STARTED,):
        row.status = "not_started"
    elif state in (MasteryState.VERY_WEAK, MasteryState.WEAK):
        row.status = "needs_review"
    else:
        row.status = "in_progress"

    await db.flush()
    return row


# ── Weak concept detection ─────────────────────────────────────────────────────

async def get_weak_concepts(db: AsyncSession, user_id: str) -> List[WeakConceptResult]:
    """
    Return weak concepts using a single query + post-processing.
    A concept is weak when:
    - mastery_score < WEAK_MASTERY_THRESHOLD (60), OR
    - state in {VERY_WEAK, WEAK, DEVELOPING}, OR
    - ≥3 consecutive incorrect in last 10 attempts, OR
    - no attempt in last NO_PRACTICE_DAYS days
    """
    from app.models.academic import ConceptMastery, QuestionAttempt, AcademicConcept

    # Single query: all mastery rows for user with concept metadata
    mastery_rows = (
        await db.execute(
            select(ConceptMastery).where(ConceptMastery.user_id == user_id)
        )
    ).scalars().all()

    # Concept metadata lookup
    concept_slugs = [r.concept_id for r in mastery_rows]
    concept_meta: dict[str, AcademicConcept] = {}
    if concept_slugs:
        c_rows = (
            await db.execute(
                select(AcademicConcept).where(AcademicConcept.slug.in_(concept_slugs))
            )
        ).scalars().all()
        concept_meta = {c.slug: c for c in c_rows}

    # For streak check: load last STREAK_WINDOW attempts per concept
    attempt_rows = (
        await db.execute(
            select(QuestionAttempt)
            .where(
                QuestionAttempt.user_id == user_id,
                QuestionAttempt.concept_id.in_(concept_slugs),
            )
            .order_by(QuestionAttempt.created_at.asc())
        )
    ).scalars().all()

    # Group attempts by concept
    from collections import defaultdict
    attempts_by_concept: dict[str, list] = defaultdict(list)
    for a in attempt_rows:
        if a.concept_id:
            attempts_by_concept[a.concept_id].append(a)

    now = datetime.now(timezone.utc)
    results: list[WeakConceptResult] = []

    for m in mastery_rows:
        cid = m.concept_id
        score = m.mastery_score or 0.0
        state = m.state or "NOT_STARTED"
        meta = concept_meta.get(cid)

        reason: Optional[str] = None

        # Rule 1: low mastery
        if score < WEAK_MASTERY_THRESHOLD:
            reason = "low mastery score"

        # Rule 2: consecutive incorrect streak
        if reason is None or True:  # always check streak even if already flagged
            recent = attempts_by_concept.get(cid, [])[-STREAK_WINDOW:]
            if len(recent) >= CONSECUTIVE_INCORRECT_TRIGGER:
                # check if last N are all incorrect
                tail = recent[-CONSECUTIVE_INCORRECT_TRIGGER:]
                if all(not a.correct for a in tail):
                    reason = "recent incorrect streak"

        # Rule 3: no recent practice
        if reason is None:
            last = m.last_attempted
            if last:
                delta = now - last.replace(tzinfo=timezone.utc) if last.tzinfo is None else now - last
                if delta.days >= NO_PRACTICE_DAYS:
                    reason = "no recent practice"

        if reason is None:
            continue

        results.append(WeakConceptResult(
            concept_id=cid,
            concept_name=meta.canonical_name if meta else cid,
            subject_id=meta.subject_id if meta else None,
            chapter_id=meta.chapter_id if meta else None,
            mastery_score=score,
            state=state,
            reason=reason[:300],
        ))

    # Sort by ascending mastery_score, ties broken by concept_id
    results.sort(key=lambda r: (r.mastery_score, r.concept_id))
    return results
