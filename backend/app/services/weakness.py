"""Weak concept detection based only on observable performance."""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    RECENT_WINDOW,
    WEAK_CONCEPT_THRESHOLD,
    WEAK_STATES,
)
from app.models.academic import ConceptMastery, QuizAnswer
from app.services.concept_graph import (
    concept_context,
    concept_label,
    get_prerequisites,
    is_prerequisite_mastered,
    load_db_concept_names,
)


async def _recent_attempts_by_concept(
    db: AsyncSession, user_id: str, limit_per_concept: int = RECENT_WINDOW
) -> Dict[str, List[QuizAnswer]]:
    rows = (await db.execute(
        select(QuizAnswer)
        .where(QuizAnswer.user_id == user_id, QuizAnswer.concept_id.isnot(None))
        .order_by(QuizAnswer.created_at.desc(), QuizAnswer.id.desc())
        .limit(500)
    )).scalars().all()
    grouped: Dict[str, List[QuizAnswer]] = {}
    for r in rows:
        bucket = grouped.setdefault(r.concept_id, [])
        if len(bucket) < limit_per_concept:
            bucket.append(r)
    return grouped


def _reasons(row: ConceptMastery, recent: List[QuizAnswer], prereq_check: Dict) -> List[str]:
    reasons: List[str] = []
    wrong_recent = sum(1 for a in recent if not a.correct)
    if recent and wrong_recent:
        reasons.append(f"{wrong_recent} of your last {len(recent)} questions were incorrect.")
    if (row.mastery_score or 0) < WEAK_CONCEPT_THRESHOLD and (row.questions_attempted or 0) > 0:
        reasons.append(
            f"LexiMind Mastery Score is {row.mastery_score:.0f} "
            f"({(row.questions_correct or 0)}/{(row.questions_attempted or 0)} correct overall)."
        )
    if (row.questions_incorrect or 0) >= 3:
        reasons.append(f"{row.questions_incorrect} incorrect answers recorded on this concept.")
    if prereq_check.get("weakPrerequisites"):
        names = ", ".join(p["concept"] for p in prereq_check["weakPrerequisites"])
        reasons.append(f"Prerequisite weakness: {names}.")
    if not reasons:
        reasons.append("Not enough recent practice on this concept.")
    return reasons


async def get_weak_concepts(db: AsyncSession, user_id: str, limit: int = 10) -> List[Dict]:
    """Concepts this user is struggling with, worst first, with observable reasons."""
    rows = (await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    )).scalars().all()
    if not rows:
        return []

    mastery_map = {r.concept_id: r for r in rows}
    recent_map = await _recent_attempts_by_concept(db, user_id)
    db_names = await load_db_concept_names(db)

    weak: List[Dict] = []
    for row in rows:
        if not (row.questions_attempted or 0):
            continue
        recent = list(reversed(recent_map.get(row.concept_id, [])))
        prereq_check = is_prerequisite_mastered(mastery_map, row.concept_id)
        recent_wrong = sum(1 for a in recent if not a.correct)
        is_weak = (
            (row.state in WEAK_STATES)
            or (row.mastery_score or 0) < WEAK_CONCEPT_THRESHOLD
            or (len(recent) >= 3 and recent_wrong * 2 > len(recent))
        )
        if not is_weak:
            continue
        ctx = concept_context(row.concept_id)
        weak.append({
            **ctx,
            "concept": ctx["concept"] if row.concept_id in db_names or ctx["concept"] else concept_label(row.concept_id, db_names),
            "mastery": round(row.mastery_score or 0.0, 1),
            "state": row.state,
            "attempted": row.questions_attempted or 0,
            "correct": row.questions_correct or 0,
            "incorrect": row.questions_incorrect or 0,
            "recentIncorrect": recent_wrong,
            "prerequisites": get_prerequisites(row.concept_id),
            "weakPrerequisites": prereq_check["weakPrerequisites"],
            "reasons": _reasons(row, recent, prereq_check),
            "reason": _reasons(row, recent, prereq_check)[0],
            "lastAttemptedAt": row.last_attempted.isoformat() if row.last_attempted else None,
        })

    weak.sort(key=lambda w: (w["mastery"], -w["recentIncorrect"]))
    return weak[:limit]
