"""
Daily Study Plan — Phase 3.

Builds a time-boxed list of up to 3 study activities for the current day.
Priority: overdue reviews → weak concept practice → next-concept learning.
Total duration does not exceed study_goal_minutes (default 30).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class StudyActivity:
    type: str          # REVIEW | PRACTICE | LEARN
    concept_id: str
    concept_name: str
    duration_minutes: int
    reason: str


async def build_daily_plan(
    db: AsyncSession,
    user_id: str,
    study_goal_minutes: int = 30,
) -> List[StudyActivity]:
    """
    Build today's study plan, capped at study_goal_minutes total.

    Priority:
    1. Overdue spaced reviews — 10 min each
    2. Weak concept practice — 10 min each
    3. Next-concept learning — remaining minutes (up to study_goal_minutes)

    Returns 1–3 activities.
    """
    from app.services.review_scheduler import get_overdue_reviews
    from app.services.adaptive_mastery import get_weak_concepts
    from app.services.recommendation_engine import get_next_recommendation
    from app.api.education import CONCEPTS

    plan: List[StudyActivity] = []
    minutes_used = 0
    concept_ids_added: set[str] = set()

    def _concept_name(cid: str) -> str:
        c = next((x for x in CONCEPTS if (x.get("id") or x.get("slug")) == cid), None)
        return c.get("name") if c else cid

    # 1. Overdue reviews (10 min each)
    overdue = await get_overdue_reviews(db, user_id)
    for r in overdue:
        if minutes_used + 10 > study_goal_minutes:
            break
        if len(plan) >= 3:
            break
        cid = r["concept_id"]
        if cid in concept_ids_added:
            continue
        plan.append(StudyActivity(
            type="REVIEW",
            concept_id=cid,
            concept_name=_concept_name(cid),
            duration_minutes=10,
            reason="Spaced review is due",
        ))
        concept_ids_added.add(cid)
        minutes_used += 10

    # 2. Weak concepts (10 min each)
    if len(plan) < 3 and minutes_used < study_goal_minutes:
        weak = await get_weak_concepts(db, user_id)
        for w in weak:
            if minutes_used + 10 > study_goal_minutes:
                break
            if len(plan) >= 3:
                break
            if w.concept_id in concept_ids_added:
                continue
            plan.append(StudyActivity(
                type="PRACTICE",
                concept_id=w.concept_id,
                concept_name=w.concept_name,
                duration_minutes=10,
                reason=w.reason,
            ))
            concept_ids_added.add(w.concept_id)
            minutes_used += 10

    # 3. Next-concept learning (remaining time)
    if len(plan) < 3 and minutes_used < study_goal_minutes:
        rec = await get_next_recommendation(db, user_id)
        if rec and rec.concept_id not in concept_ids_added:
            remaining = study_goal_minutes - minutes_used
            if remaining > 0:
                plan.append(StudyActivity(
                    type="LEARN",
                    concept_id=rec.concept_id,
                    concept_name=rec.concept_name,
                    duration_minutes=min(remaining, rec.estimated_minutes),
                    reason=rec.reason,
                ))

    # Ensure at least one activity
    if not plan:
        rec = await get_next_recommendation(db, user_id)
        if rec:
            plan.append(StudyActivity(
                type=rec.type.value,
                concept_id=rec.concept_id,
                concept_name=rec.concept_name,
                duration_minutes=min(study_goal_minutes, rec.estimated_minutes),
                reason=rec.reason,
            ))

    return plan
