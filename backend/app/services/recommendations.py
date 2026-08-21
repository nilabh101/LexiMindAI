"""Recommendation engine and daily study plan.

Priority order (highest first):
  1. Reviews that are due (spaced repetition).
  2. Weak prerequisites blocking the learner's current path.
  3. Weak concepts.
  4. The current learning-path item (LEARN / PRACTICE).
  5. PYQ practice on concepts that already have mastery.
Every recommendation carries the observable reason behind it.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    DEFAULT_DAILY_STUDY_MINUTES,
    DEFAULT_STUDY_MINUTES,
    MIN_PLAN_BLOCK_MINUTES,
    PATH_CURRENT,
    PATH_NEEDS_REVIEW,
    PATH_RECOMMENDED,
)
from app.models.academic import Question
from app.services.concept_graph import concept_context, concept_label, load_mastery_map
from app.services.learning_path import get_learning_path
from app.services.review import get_due_reviews
from app.services.weakness import get_weak_concepts


def _estimated_minutes(rec_type: str, concept_id: Optional[str]) -> int:
    ctx = concept_context(concept_id) if concept_id else {}
    if rec_type == "LEARN" and ctx.get("estimatedMinutes"):
        return int(ctx["estimatedMinutes"])
    return DEFAULT_STUDY_MINUTES.get(rec_type, 15)


def _recommendation(rec_type: str, concept_id: Optional[str], reason: str, priority: int,
                    mastery: Optional[float] = None, title: Optional[str] = None) -> Dict:
    ctx = concept_context(concept_id) if concept_id else {}
    verb = {"LEARN": "Learn", "REVIEW": "Review", "PRACTICE": "Practice",
            "PYQ": "Attempt PYQs on", "QUIZ": "Take a quiz on"}[rec_type]
    return {
        "type": rec_type,
        "conceptId": concept_id,
        "concept": ctx.get("concept") or (concept_label(concept_id) if concept_id else None),
        "subjectId": ctx.get("subjectId"),
        "subject": ctx.get("subject"),
        "chapterId": ctx.get("chapterId"),
        "chapter": ctx.get("chapter"),
        "title": title or f"{verb} {ctx.get('concept') or concept_label(concept_id)}",
        "reason": reason,
        "estimatedMinutes": _estimated_minutes(rec_type, concept_id),
        "priority": priority,
        "mastery": round(float(mastery), 1) if mastery is not None else None,
    }


async def _pyq_count(db: AsyncSession, concept_id: str) -> int:
    return int((await db.execute(
        select(func.count(Question.id)).where(
            Question.concept_id == concept_id, Question.source == "PYQ"
        )
    )).scalar() or 0)


async def get_recommendations(
    db: AsyncSession,
    user_id: str,
    subject_id: Optional[str] = None,
    limit: int = 5,
) -> List[Dict]:
    now = datetime.now(timezone.utc)
    recs: List[Dict] = []
    seen: set = set()

    def add(rec: Dict):
        key = (rec["type"], rec["conceptId"])
        if key in seen:
            return
        seen.add(key)
        recs.append(rec)

    # 1. Due reviews.
    for due in await get_due_reviews(db, user_id, now):
        if subject_id and due.get("subjectId") and due["subjectId"] != subject_id:
            continue
        add(_recommendation(
            "REVIEW", due["conceptId"],
            f"Scheduled review is due (last interval {due['intervalDays']} day(s), mastery {due['mastery']:.0f}).",
            priority=1, mastery=due["mastery"],
        ))

    # 2/3. Weak prerequisites, then weak concepts.
    weak = await get_weak_concepts(db, user_id)
    if subject_id:
        weak = [w for w in weak if not w.get("subjectId") or w["subjectId"] == subject_id]
    for w in weak:
        for prereq in w.get("weakPrerequisites") or []:
            if prereq["attempted"]:
                reason = (f"{w['concept']} depends on {prereq['concept']}. Your current mastery "
                          f"({prereq['mastery']:.0f}) suggests reviewing this concept first.")
                add(_recommendation("REVIEW", prereq["conceptId"], reason,
                                    priority=1, mastery=prereq["mastery"]))
            else:
                reason = (f"{w['concept']} depends on {prereq['concept']}, which you haven't "
                          "practised yet. Start there.")
                add(_recommendation("LEARN", prereq["conceptId"], reason, priority=1, mastery=0.0))
        add(_recommendation("PRACTICE", w["conceptId"], w["reason"], priority=2, mastery=w["mastery"]))

    # 4. Current learning-path item.
    if subject_id:
        path = await get_learning_path(db, user_id, subject_id)
        for item in path["items"]:
            if item["status"] in (PATH_CURRENT, PATH_NEEDS_REVIEW, PATH_RECOMMENDED):
                rec_type = "LEARN" if not item["attempted"] else "PRACTICE"
                reason = (
                    "Next concept in your learning path — no attempts recorded yet."
                    if not item["attempted"] else
                    f"Current focus in your learning path (mastery {item['mastery']:.0f})."
                )
                add(_recommendation(rec_type, item["conceptId"], reason, priority=3, mastery=item["mastery"]))
                break

    # 5. PYQ practice on concepts already started.
    mastery_map = await load_mastery_map(db, user_id)
    for concept_id, row in sorted(mastery_map.items(), key=lambda kv: -(kv[1].mastery_score or 0)):
        if subject_id and row.subject_id and row.subject_id != subject_id:
            continue
        count = await _pyq_count(db, concept_id)
        if count:
            add(_recommendation(
                "PYQ", concept_id,
                f"{count} previous-year question(s) available for this concept "
                f"(mastery {row.mastery_score:.0f}).",
                priority=4, mastery=row.mastery_score,
            ))
            break

    recs.sort(key=lambda r: (r["priority"], r["mastery"] if r["mastery"] is not None else 100))
    return recs[:limit]


async def get_next_recommendation(db: AsyncSession, user_id: str, subject_id: Optional[str] = None) -> Optional[Dict]:
    recs = await get_recommendations(db, user_id, subject_id, limit=1)
    return recs[0] if recs else None


async def get_daily_plan(
    db: AsyncSession,
    user_id: str,
    subject_id: Optional[str] = None,
    study_minutes: int = DEFAULT_DAILY_STUDY_MINUTES,
) -> Dict:
    """Fill the learner's available study time with real recommendations."""
    minutes = max(MIN_PLAN_BLOCK_MINUTES, int(study_minutes or DEFAULT_DAILY_STUDY_MINUTES))
    recs = await get_recommendations(db, user_id, subject_id, limit=10)
    blocks: List[Dict] = []
    remaining = minutes
    for rec in recs:
        if remaining < MIN_PLAN_BLOCK_MINUTES:
            break
        allotted = min(rec["estimatedMinutes"], remaining)
        if remaining - allotted < MIN_PLAN_BLOCK_MINUTES:
            allotted = remaining
        blocks.append({**rec, "minutes": allotted})
        remaining -= allotted

    return {
        "userId": user_id,
        "subjectId": subject_id,
        "studyMinutes": minutes,
        "plannedMinutes": minutes - remaining,
        "blocks": blocks,
        "empty": not blocks,
        "message": None if blocks else
        "No plan yet — take a quiz or open a concept so LexiMind can learn what you need.",
    }
