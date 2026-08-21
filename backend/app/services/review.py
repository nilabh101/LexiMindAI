"""Spaced review scheduling — simple, transparent interval ladder.

Intervals: 1 → 3 → 7 → 14 → 30 days (configurable).
Performance at or above REVIEW_PROMOTE_ACCURACY moves one step up the ladder,
performance below REVIEW_DEMOTE_ACCURACY resets to the first interval, anything
in between repeats the current interval.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    REVIEW_DEMOTE_ACCURACY,
    REVIEW_INTERVALS_DAYS,
    REVIEW_PROMOTE_ACCURACY,
)
from app.models.academic import ConceptMastery


def next_interval_days(current: Optional[int], accuracy: float) -> int:
    """Next ladder step given the accuracy (0–1) of the latest session."""
    ladder = REVIEW_INTERVALS_DAYS
    if current is None or current not in ladder:
        index = -1
    else:
        index = ladder.index(current)
    if accuracy < REVIEW_DEMOTE_ACCURACY:
        return ladder[0]
    if accuracy >= REVIEW_PROMOTE_ACCURACY:
        return ladder[min(index + 1, len(ladder) - 1)]
    return ladder[max(index, 0)]


def schedule_next_review(
    current_interval: Optional[int],
    accuracy: float,
    now: Optional[datetime] = None,
) -> Tuple[int, datetime]:
    now = now or datetime.now(timezone.utc)
    interval = next_interval_days(current_interval, accuracy)
    return interval, now + timedelta(days=interval)


async def get_review_schedule(db: AsyncSession, user_id: str) -> List[dict]:
    """All scheduled reviews for a user, soonest first."""
    rows = (await db.execute(
        select(ConceptMastery)
        .where(ConceptMastery.user_id == user_id, ConceptMastery.next_review_at.isnot(None))
        .order_by(ConceptMastery.next_review_at.asc())
    )).scalars().all()
    now = datetime.now(timezone.utc)
    schedule = []
    for r in rows:
        due = r.next_review_at
        due_utc = due if due.tzinfo else due.replace(tzinfo=timezone.utc)
        schedule.append({
            "conceptId": r.concept_id,
            "subjectId": r.subject_id,
            "mastery": r.mastery_score,
            "state": r.state,
            "intervalDays": r.review_interval_days,
            "nextReviewAt": due_utc.isoformat(),
            "due": due_utc <= now,
        })
    return schedule


async def get_due_reviews(db: AsyncSession, user_id: str, now: Optional[datetime] = None) -> List[dict]:
    now = now or datetime.now(timezone.utc)
    return [item for item in await get_review_schedule(db, user_id) if item["due"]]
