"""
Adaptive Quiz Assembly — Phase 3.

Assembles a quiz tailored to the student's mastery:
  mastery < 40   → primary tier: EASY   (≥60% of questions)
  mastery 40-70  → primary tier: MEDIUM (≥60%)
  mastery ≥ 70   → primary tier: HARD   (≥60%)

In-session difficulty adjustment:
  3 consecutive correct → tier up (if not already HARD)
  2 consecutive incorrect → tier down (if not already EASY)

Recency: questions attempted in last 7 days are deprioritised.
Session dedup: no same question twice per session.
Works entirely from DB when LLM unavailable.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# ── Configurable constants ─────────────────────────────────────────────────────
ADAPTIVE_CONSTANTS = {
    "CORRECT_STREAK_UP":    3,   # consecutive correct → tier up
    "INCORRECT_STREAK_DOWN": 2,  # consecutive incorrect → tier down
    "RECENCY_WINDOW_DAYS":   7,  # questions answered within N days are deprioritised
    "MIN_QUESTION_COUNT":    1,
    "MAX_QUESTION_COUNT":   30,
    "DEFAULT_QUESTION_COUNT": 10,
    "PRIMARY_TIER_RATIO":   0.6, # target ≥ 60% from primary tier
}

DIFFICULTY_TIERS = ["easy", "medium", "hard"]

MASTERY_TO_PRIMARY_TIER: Dict[str, str] = {}  # built dynamically


def _primary_tier(mastery_score: float) -> str:
    if mastery_score < 40:
        return "easy"
    if mastery_score < 70:
        return "medium"
    return "hard"


def _adjacent_tiers(tier: str) -> List[str]:
    idx = DIFFICULTY_TIERS.index(tier) if tier in DIFFICULTY_TIERS else 1
    adj = []
    if idx > 0:
        adj.append(DIFFICULTY_TIERS[idx - 1])
    if idx < len(DIFFICULTY_TIERS) - 1:
        adj.append(DIFFICULTY_TIERS[idx + 1])
    return adj


def compute_session_difficulty_adjustment(
    streak_correct: int,
    streak_incorrect: int,
    current_tier: str,
) -> str:
    """
    Adjust difficulty tier based on in-session performance.
    Returns the (possibly new) tier name.
    """
    tier_idx = DIFFICULTY_TIERS.index(current_tier) if current_tier in DIFFICULTY_TIERS else 1
    if streak_correct >= ADAPTIVE_CONSTANTS["CORRECT_STREAK_UP"]:
        tier_idx = min(tier_idx + 1, len(DIFFICULTY_TIERS) - 1)
    elif streak_incorrect >= ADAPTIVE_CONSTANTS["INCORRECT_STREAK_DOWN"]:
        tier_idx = max(tier_idx - 1, 0)
    return DIFFICULTY_TIERS[tier_idx]


@dataclass
class AdaptiveQuizResult:
    quiz_id: str
    questions: List[dict]
    insufficient_bank: bool
    ai_generated_count: int
    source_counts: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    concept_id: Optional[str] = None
    subject_id: Optional[str] = None


async def assemble_adaptive_quiz(
    db: AsyncSession,
    user_id: str,
    subject_id: str,
    chapter_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    question_count: int = ADAPTIVE_CONSTANTS["DEFAULT_QUESTION_COUNT"],
    review_requested: bool = False,
) -> AdaptiveQuizResult:
    """
    Assemble an adaptive quiz for the user.

    Selection order (per slot):
    1. Primary-tier questions NOT seen in last 7 days
    2. Primary-tier questions seen in last 7 days
    3. Adjacent-tier questions NOT seen in last 7 days
    4. Adjacent-tier questions seen in last 7 days

    All questions unique within session.
    """
    from app.models.academic import ConceptMastery, QuestionAttempt, Question

    # Clamp question count
    question_count = max(
        ADAPTIVE_CONSTANTS["MIN_QUESTION_COUNT"],
        min(question_count, ADAPTIVE_CONSTANTS["MAX_QUESTION_COUNT"]),
    )

    # Get mastery for primary tier determination
    mastery_score = 0.0
    if concept_id:
        m_row = (
            await db.execute(
                select(ConceptMastery).where(
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept_id == concept_id,
                )
            )
        ).scalar_one_or_none()
        mastery_score = m_row.mastery_score if m_row else 0.0
    elif subject_id:
        rows = (
            await db.execute(
                select(ConceptMastery).where(ConceptMastery.user_id == user_id)
            )
        ).scalars().all()
        scores = [r.mastery_score for r in rows if r.mastery_score is not None]
        mastery_score = sum(scores) / len(scores) if scores else 0.0

    primary_tier = _primary_tier(mastery_score)
    adj_tiers = _adjacent_tiers(primary_tier)

    # Determine recently attempted question IDs
    recency_cutoff = datetime.now(timezone.utc) - timedelta(
        days=ADAPTIVE_CONSTANTS["RECENCY_WINDOW_DAYS"]
    )
    recent_attempt_rows = (
        await db.execute(
            select(QuestionAttempt).where(
                QuestionAttempt.user_id == user_id,
                QuestionAttempt.created_at >= recency_cutoff,
                QuestionAttempt.question_id.isnot(None),
            )
        )
    ).scalars().all()
    recently_seen: set[int] = {a.question_id for a in recent_attempt_rows if a.question_id}

    # Fetch all eligible questions
    q_stmt = select(Question).where(
        Question.review_status != "REJECTED",
    )
    if concept_id:
        q_stmt = q_stmt.where(Question.concept_id == concept_id)
    elif chapter_id:
        q_stmt = q_stmt.where(Question.chapter_id == chapter_id)
    elif subject_id:
        q_stmt = q_stmt.where(Question.subject_id == subject_id)

    all_questions = (await db.execute(q_stmt)).scalars().all()

    # Bucket questions
    primary_fresh = []
    primary_seen  = []
    adj_fresh     = []
    adj_seen      = []

    for q in all_questions:
        diff = (q.difficulty or "medium").lower()
        is_recent = (q.id in recently_seen) and not review_requested
        if diff == primary_tier:
            if is_recent:
                primary_seen.append(q)
            else:
                primary_fresh.append(q)
        elif diff in adj_tiers:
            if is_recent:
                adj_seen.append(q)
            else:
                adj_fresh.append(q)

    # Sort by source priority: PYQ first, then UPLOADED, PREMADE, DEMO, AI_GENERATED
    source_order = {"PYQ": 0, "UPLOADED": 1, "PREMADE": 2, "DEMO": 3, "AI_GENERATED": 4}
    for lst in [primary_fresh, primary_seen, adj_fresh, adj_seen]:
        lst.sort(key=lambda q: source_order.get(q.source or "DEMO", 5))

    # Select questions
    selected: List[Question] = []
    session_ids: set[int] = set()

    def _take(pool: List[Question], n: int) -> int:
        taken = 0
        for q in pool:
            if len(selected) >= n:
                break
            if q.id not in session_ids:
                selected.append(q)
                session_ids.add(q.id)
                taken += 1
        return taken

    target_primary = int(question_count * ADAPTIVE_CONSTANTS["PRIMARY_TIER_RATIO"])
    _take(primary_fresh, target_primary)
    _take(primary_seen,  target_primary)
    _take(adj_fresh,     question_count)
    _take(adj_seen,      question_count)
    # Any remaining gap from primary
    _take(primary_fresh, question_count)

    insufficient = len(selected) < question_count

    quiz_id = str(uuid.uuid4())
    source_counts: Dict[str, int] = {}
    difficulty_dist: Dict[str, int] = {}

    def _q_dict(q: Question) -> dict:
        source_counts[q.source or "UNKNOWN"] = source_counts.get(q.source or "UNKNOWN", 0) + 1
        d = (q.difficulty or "medium").lower()
        difficulty_dist[d] = difficulty_dist.get(d, 0) + 1
        return {
            "id": q.id,
            "question_text": q.question_text,
            "options": q.options,
            "answer": q.answer,
            "explanation": q.explanation,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "concept_id": q.concept_id,
            "subject_id": q.subject_id,
            "year": q.year,
            "marks": q.marks,
            "source": q.source,
        }

    questions_out = [_q_dict(q) for q in selected]

    return AdaptiveQuizResult(
        quiz_id=quiz_id,
        questions=questions_out,
        insufficient_bank=insufficient,
        ai_generated_count=source_counts.get("AI_GENERATED", 0),
        source_counts=source_counts,
        difficulty_distribution=difficulty_dist,
        concept_id=concept_id,
        subject_id=subject_id,
    )
