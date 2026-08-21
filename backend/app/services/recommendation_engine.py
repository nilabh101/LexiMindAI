"""
Recommendation Engine — Phase 3.

Priority order:
  1. Overdue spaced reviews (next_review_at ≤ now)
  2. Weak prerequisites blocking progress (mastery < 60)
  3. Weak concepts in subject (mastery < 60)
  4. Next concept in learning path
  5. New concept to learn

Tiebreakers: weakness_score → prerequisite_readiness → time_since_last_attempt → path position
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class RecommendationType(str, Enum):
    LEARN    = "LEARN"
    REVIEW   = "REVIEW"
    PRACTICE = "PRACTICE"
    PYQ      = "PYQ"
    QUIZ     = "QUIZ"


@dataclass
class Recommendation:
    concept_id: str
    concept_name: str
    reason: str               # 10–300 chars
    estimated_minutes: int    # 1–120
    priority: int             # 1 (highest) – 5
    type: RecommendationType


async def get_next_recommendation(
    db: AsyncSession,
    user_id: str,
    subject_id: Optional[str] = None,
) -> Optional[Recommendation]:
    """
    Return the single highest-priority recommendation for a user.
    Returns None only if there are no concepts configured at all.
    """
    from app.models.academic import ConceptMastery, ReviewSchedule
    from app.api.education import CONCEPTS, SUBJECTS
    from app.services.prerequisite_graph import (
        get_prerequisites, is_prerequisite_mastered, get_unmastered_prerequisites
    )
    from app.services.adaptive_mastery import WEAK_MASTERY_THRESHOLD, get_mastery_state, MasteryState

    now = datetime.now(timezone.utc)

    # Filter concepts by subject
    concepts = [c for c in CONCEPTS if not subject_id or c.get("subjectId") == subject_id]
    if not concepts:
        concepts = list(CONCEPTS)
    if not concepts:
        return None

    # Load all mastery rows for this user (one query)
    mastery_rows = (
        await db.execute(
            select(ConceptMastery).where(ConceptMastery.user_id == user_id)
        )
    ).scalars().all()
    mastery_map = {r.concept_id: r for r in mastery_rows}

    # Load overdue reviews (one query)
    overdue_rows = (
        await db.execute(
            select(ReviewSchedule).where(
                ReviewSchedule.user_id == user_id,
                ReviewSchedule.next_review_at <= now,
            )
        )
    ).scalars().all()
    overdue_concept_ids = {r.concept_id for r in overdue_rows}

    # ── Priority 1: overdue spaced reviews ────────────────────────────────────
    for c in concepts:
        cid = c.get("id") or c.get("slug") or ""
        if cid in overdue_concept_ids:
            m = mastery_map.get(cid)
            score = m.mastery_score if m else 0.0
            last_str = m.last_attempted.strftime("%Y-%m-%d") if m and m.last_attempted else "never"
            return Recommendation(
                concept_id=cid,
                concept_name=c.get("name") or cid,
                reason=f"Review due. Last attempted: {last_str}. Current mastery: {round(score)}.",
                estimated_minutes=10,
                priority=1,
                type=RecommendationType.REVIEW,
            )

    # ── Priority 2: weak prerequisites blocking progress ──────────────────────
    for c in concepts:
        cid = c.get("id") or c.get("slug") or ""
        prereqs = get_prerequisites(cid)
        for pid in prereqs:
            pm = mastery_map.get(pid)
            p_score = pm.mastery_score if pm else 0.0
            if p_score < WEAK_MASTERY_THRESHOLD:
                # Find prereq concept name
                prereq_c = next((x for x in CONCEPTS if (x.get("id") or x.get("slug")) == pid), None)
                prereq_name = prereq_c.get("name") if prereq_c else pid
                target_name = c.get("name") or cid
                return Recommendation(
                    concept_id=pid,
                    concept_name=prereq_name,
                    reason=(
                        f"{target_name} depends on {prereq_name}. "
                        f"Your current mastery suggests reviewing {prereq_name} first."
                    )[:300],
                    estimated_minutes=15,
                    priority=2,
                    type=RecommendationType.PRACTICE,
                )

    # ── Priority 3: weak concepts in subject ──────────────────────────────────
    weak_candidates = []
    for c in concepts:
        cid = c.get("id") or c.get("slug") or ""
        m = mastery_map.get(cid)
        score = m.mastery_score if m else 0.0
        state = m.state if m else "NOT_STARTED"
        if score < WEAK_MASTERY_THRESHOLD and state != "NOT_STARTED":
            last_att = m.last_attempted if m else None
            hours_since = (
                (now - last_att.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if last_att and last_att.tzinfo is None
                else (now - last_att).total_seconds() / 3600 if last_att else 9999
            )
            weak_candidates.append((score, hours_since, cid, c))

    if weak_candidates:
        weak_candidates.sort(key=lambda x: (x[0], -x[1]))  # lowest score first, oldest first
        score, _, cid, c = weak_candidates[0]
        return Recommendation(
            concept_id=cid,
            concept_name=c.get("name") or cid,
            reason=f"Mastery is {round(score)}%. Practice more questions to strengthen this concept.",
            estimated_minutes=15,
            priority=3,
            type=RecommendationType.PRACTICE,
        )

    # ── Priority 4: next concept in learning path ─────────────────────────────
    for i, c in enumerate(concepts):
        cid = c.get("id") or c.get("slug") or ""
        m = mastery_map.get(cid)
        score = m.mastery_score if m else 0.0
        state_val = get_mastery_state(score, m.questions_attempted if m else 0)
        if state_val not in (MasteryState.MASTERED,):
            prereq_ok = await is_prerequisite_mastered(db, user_id, cid)
            if prereq_ok:
                return Recommendation(
                    concept_id=cid,
                    concept_name=c.get("name") or cid,
                    reason="Next concept on your learning path.",
                    estimated_minutes=c.get("estimatedMinutes") or 20,
                    priority=4,
                    type=RecommendationType.LEARN if score == 0 else RecommendationType.PRACTICE,
                )

    # ── Priority 5: review oldest mastered concept ────────────────────────────
    mastered = [
        (m.last_attempted or datetime(2000, 1, 1), m.concept_id)
        for m in mastery_rows
        if m.state == "MASTERED"
    ]
    if mastered:
        mastered.sort(key=lambda x: (x[0] or datetime(2000, 1, 1)))
        _, cid = mastered[0]
        c = next((x for x in CONCEPTS if (x.get("id") or x.get("slug")) == cid), None)
        name = c.get("name") if c else cid
        return Recommendation(
            concept_id=cid,
            concept_name=name,
            reason="All concepts are mastered. Keep your knowledge fresh!",
            estimated_minutes=10,
            priority=5,
            type=RecommendationType.REVIEW,
        )

    # ── Fallback: first concept ───────────────────────────────────────────────
    if concepts:
        c = concepts[0]
        cid = c.get("id") or c.get("slug") or ""
        return Recommendation(
            concept_id=cid,
            concept_name=c.get("name") or cid,
            reason="Start your learning journey with this concept.",
            estimated_minutes=c.get("estimatedMinutes") or 20,
            priority=5,
            type=RecommendationType.LEARN,
        )

    return None
