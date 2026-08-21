"""
Spaced Review Scheduler — Phase 3.

Review interval progression: 1 → 3 → 7 → 14 → 30 days (capped at 30).
On mastery regression: reset to 1 day.
On mastery improvement/maintenance: advance to next interval.
Early reviews (before next_review_at) use the same advancement logic from UTC now.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


REVIEW_SEQUENCE: List[int] = [1, 3, 7, 14, 30]  # days


def advance_interval(current_days: int) -> int:
    """Return the next interval in REVIEW_SEQUENCE (capped at 30)."""
    try:
        idx = REVIEW_SEQUENCE.index(current_days)
        return REVIEW_SEQUENCE[min(idx + 1, len(REVIEW_SEQUENCE) - 1)]
    except ValueError:
        # current_days not in sequence — find next value above it
        for v in REVIEW_SEQUENCE:
            if v > current_days:
                return v
        return REVIEW_SEQUENCE[-1]


def reset_interval() -> int:
    """Return 1 (first interval after mastery regression)."""
    return REVIEW_SEQUENCE[0]


async def schedule_review(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    mastery_state: str,
) -> None:
    """
    Schedule or initialise the first review when concept reaches PROFICIENT.
    Called by update_concept_mastery when state transitions to PROFICIENT or MASTERED.
    """
    from app.models.academic import ReviewSchedule

    if mastery_state not in ("PROFICIENT", "MASTERED"):
        return

    result = await db.execute(
        select(ReviewSchedule).where(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.concept_id == concept_id,
        )
    )
    existing = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if existing is None:
        # First time reaching PROFICIENT — schedule first review in 1 day
        db.add(ReviewSchedule(
            user_id=user_id,
            concept_id=concept_id,
            next_review_at=now + timedelta(days=1),
            current_interval_days=1,
            review_count=0,
        ))
        await db.flush()


async def apply_review_result(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    mastery_before: float,
    mastery_after: float,
) -> None:
    """
    Advance or reset the review interval based on mastery change.
    mastery_after >= mastery_before → advance_interval()
    mastery_after < mastery_before  → reset_interval()
    Sets next_review_at from current UTC timestamp.
    Works for both on-time and early reviews.
    """
    from app.models.academic import ReviewSchedule

    result = await db.execute(
        select(ReviewSchedule).where(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.concept_id == concept_id,
        )
    )
    row = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if row is None:
        # Create schedule if it doesn't exist yet
        row = ReviewSchedule(
            user_id=user_id,
            concept_id=concept_id,
            current_interval_days=1,
            review_count=0,
        )
        db.add(row)

    if mastery_after >= mastery_before:
        new_interval = advance_interval(row.current_interval_days or 1)
    else:
        new_interval = reset_interval()

    row.current_interval_days = new_interval
    row.next_review_at = now + timedelta(days=new_interval)
    row.review_count = (row.review_count or 0) + 1
    row.updated_at = now
    await db.flush()


async def get_overdue_reviews(db: AsyncSession, user_id: str) -> List[dict]:
    """
    Return ReviewSchedule rows where next_review_at < UTC now,
    ordered by next_review_at ascending (most overdue first).
    """
    from app.models.academic import ReviewSchedule

    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(ReviewSchedule).where(
                ReviewSchedule.user_id == user_id,
                ReviewSchedule.next_review_at <= now,
            ).order_by(ReviewSchedule.next_review_at.asc())
        )
    ).scalars().all()

    return [
        {
            "concept_id": r.concept_id,
            "next_review_at": r.next_review_at.isoformat() if r.next_review_at else None,
            "current_interval_days": r.current_interval_days,
            "review_count": r.review_count,
        }
        for r in rows
    ]
