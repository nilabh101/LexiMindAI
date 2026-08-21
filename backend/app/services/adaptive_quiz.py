"""Adaptive quiz construction.

Pipeline: weak concepts → prerequisite check → candidate questions from the
Phase 2 bank → drop recently answered questions → order by target difficulty.
Every decision is traceable to stored performance and question metadata.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    CONSECUTIVE_CORRECT_TO_INCREASE,
    CONSECUTIVE_INCORRECT_TO_DECREASE,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_LADDER,
    concept_state,
    REPEAT_COOLDOWN_DAYS,
    target_difficulties,
)
from app.models.academic import ConceptMastery, Question, QuestionConcept, QuizAnswer
from app.services.concept_graph import (
    concept_label,
    curriculum_concepts,
    explain_prerequisite_gap,
    is_prerequisite_mastered,
    load_mastery_map,
)
from app.services.quiz_bank import _serialize_q, _counts
from app.services.weakness import get_weak_concepts


def next_difficulty(current: Optional[str], consecutive_correct: int, consecutive_incorrect: int) -> str:
    """Transparent in-quiz difficulty controller."""
    level = (current or DEFAULT_DIFFICULTY).upper()
    if level not in DIFFICULTY_LADDER:
        level = DEFAULT_DIFFICULTY
    index = DIFFICULTY_LADDER.index(level)
    if consecutive_correct >= CONSECUTIVE_CORRECT_TO_INCREASE:
        index = min(index + 1, len(DIFFICULTY_LADDER) - 1)
    elif consecutive_incorrect >= CONSECUTIVE_INCORRECT_TO_DECREASE:
        index = max(index - 1, 0)
    return DIFFICULTY_LADDER[index]


async def _recent_question_ids(db: AsyncSession, user_id: str, days: int = REPEAT_COOLDOWN_DAYS) -> set:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (await db.execute(
        select(QuizAnswer.question_id).where(
            QuizAnswer.user_id == user_id,
            QuizAnswer.question_id.isnot(None),
            QuizAnswer.created_at >= cutoff,
        )
    )).all()
    return {r[0] for r in rows}


async def _candidate_questions(
    db: AsyncSession,
    concept_ids: List[str],
    subject_id: Optional[str],
    chapter_id: Optional[str],
    limit: int,
) -> List[Question]:
    stmt = select(Question).where(Question.review_status != "REJECTED")
    if concept_ids:
        mapped = select(QuestionConcept.question_id).where(QuestionConcept.concept_id.in_(concept_ids))
        stmt = stmt.where(or_(Question.concept_id.in_(concept_ids), Question.id.in_(mapped)))
    elif subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if chapter_id:
        stmt = stmt.where(or_(Question.chapter_id == chapter_id, Question.chapter_id.is_(None)))
    return list((await db.execute(stmt.limit(limit))).scalars().all())


def _bank_message(questions: List[Dict], requested: int, targets: List[str], widened: bool) -> Optional[str]:
    """Honest description of what the bank could actually supply."""
    label = ", ".join(concept_label(c) for c in targets) or "this selection"
    if not questions:
        return (
            f"No questions are stored for {label} yet. "
            "Upload notes or a PYQ PDF to build the bank."
        )
    if widened:
        return (
            f"No questions are stored for {label} yet — showing questions from the "
            "rest of this subject instead."
        )
    if len(questions) < requested:
        return f"Only {len(questions)} of {requested} questions are stored for {label} so far."
    return None


def _rank(question: Question, preferred: List[str], recent_ids: set, order: List[str]) -> tuple:
    source_order = {"PYQ": 0, "UPLOADED": 1, "PREMADE": 2, "DEMO": 3, "AI_GENERATED": 4}
    difficulty = (question.difficulty or DEFAULT_DIFFICULTY).upper()
    diff_rank = preferred.index(difficulty) if difficulty in preferred else len(preferred)
    concept_rank = order.index(question.concept_id) if question.concept_id in order else len(order)
    return (
        1 if question.id in recent_ids else 0,   # unseen questions first
        concept_rank,                            # then the primary target concept
        diff_rank,                               # then target difficulty
        source_order.get(question.source, 9),    # then authentic sources
        question.id,                             # deterministic tie-break
    )


async def build_adaptive_quiz(
    db: AsyncSession,
    user_id: str,
    subject_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    question_count: int = 5,
    include_recent: bool = False,
) -> Dict:
    """Build a quiz targeted at what this user most needs to practise."""
    mastery_map = await load_mastery_map(db, user_id)

    # 1. Decide which concepts to target.
    if concept_id:
        target_concepts = [concept_id]
        selection_reason = f"Requested concept: {concept_label(concept_id)}."
    else:
        weak = await get_weak_concepts(db, user_id)
        if subject_id:
            weak = [w for w in weak if not w.get("subjectId") or w["subjectId"] == subject_id]
        target_concepts = [w["conceptId"] for w in weak[:3]]
        if target_concepts:
            selection_reason = "Targeting your weakest concepts: " + ", ".join(
                concept_label(c) for c in target_concepts) + "."
        else:
            curriculum = curriculum_concepts(subject_id, chapter_id)
            target_concepts = [c["id"] for c in curriculum[:3]]
            selection_reason = (
                "No attempt history yet — starting from the beginning of the syllabus."
                if not mastery_map else
                "No weak concepts detected — practising across the current chapter."
            )

    # 2. Prerequisite check on the primary target.
    prerequisite_note = None
    prerequisite_concepts: List[str] = []
    if target_concepts:
        check = is_prerequisite_mastered(mastery_map, target_concepts[0])
        if not check["mastered"]:
            prerequisite_concepts = [p["conceptId"] for p in check["weakPrerequisites"]]
            prerequisite_note = explain_prerequisite_gap(target_concepts[0], check["weakPrerequisites"])
            # Practise the weak prerequisite first.
            target_concepts = prerequisite_concepts + [c for c in target_concepts if c not in prerequisite_concepts]

    # 3. Difficulty target from mastery of the primary concept.
    primary = target_concepts[0] if target_concepts else None
    primary_mastery = mastery_map.get(primary).mastery_score if primary and primary in mastery_map else 0.0
    preferred = target_difficulties(primary_mastery)

    # 4/5. Candidates minus recently answered questions.
    candidates = await _candidate_questions(db, target_concepts, subject_id, chapter_id, question_count * 10)
    widened = False
    if not candidates and target_concepts and not concept_id:
        # Only widen beyond the targets when the caller did not ask for a
        # specific concept — otherwise say the bank is empty instead of
        # quietly serving questions about something else.
        candidates = await _candidate_questions(db, [], subject_id, chapter_id, question_count * 10)
        widened = bool(candidates)
    recent_ids = set() if include_recent else await _recent_question_ids(db, user_id)

    ranked = sorted(candidates, key=lambda q: _rank(q, preferred, recent_ids, target_concepts))
    picked = ranked[:question_count]
    repeated = [q.id for q in picked if q.id in recent_ids]

    questions = [_serialize_q(q) for q in picked]
    quiz_id = f"adaptive-{user_id}-{primary or subject_id or 'mixed'}-{int(datetime.now(timezone.utc).timestamp())}"
    return {
        "quiz_id": quiz_id,
        "user_id": user_id,
        "subject_id": subject_id,
        "concept_id": primary,
        "concept": concept_label(primary) if primary else None,
        "state": concept_state(
            primary_mastery or 0.0,
            mastery_map[primary].questions_attempted if primary in mastery_map else 0,
        ) if primary else None,
        "questions": questions,
        "message": _bank_message(questions, question_count, target_concepts, widened),
        "widened_beyond_targets": widened,
        "target_concepts": target_concepts,
        "target_difficulties": preferred,
        "starting_difficulty": preferred[0] if preferred else DEFAULT_DIFFICULTY,
        "mastery": round(float(primary_mastery or 0.0), 1),
        "selection_reason": selection_reason,
        "prerequisite_note": prerequisite_note,
        "prerequisite_concepts": prerequisite_concepts,
        "repeated_questions": repeated,
        "source_counts": _counts(questions),
        "insufficient_bank": len(questions) < question_count or widened,
        "difficulty_rules": {
            "increaseAfterConsecutiveCorrect": CONSECUTIVE_CORRECT_TO_INCREASE,
            "decreaseAfterConsecutiveIncorrect": CONSECUTIVE_INCORRECT_TO_DECREASE,
        },
    }
