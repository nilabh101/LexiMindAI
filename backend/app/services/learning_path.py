"""Learning path derived from curriculum order + persisted mastery."""
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    PATH_COMPLETED,
    PATH_CURRENT,
    PATH_LOCKED,
    PATH_NEEDS_REVIEW,
    PATH_RECOMMENDED,
    PREREQUISITE_MASTERY_THRESHOLD,
    STATE_MASTERED,
    WEAK_STATES,
)
from app.models.academic import ConceptMastery
from app.services.concept_graph import (
    curriculum_concepts,
    explain_prerequisite_gap,
    is_prerequisite_mastered,
    load_mastery_map,
)


def _item(concept: Dict, order: int, status: str, row: Optional[ConceptMastery], note: Optional[str]) -> Dict:
    return {
        "id": f"lp-{concept['id']}",
        "conceptId": concept["id"],
        "concept": concept["name"],
        "chapterId": concept.get("chapterId"),
        "subjectId": concept.get("subjectId"),
        "order": order,
        "status": status,
        "state": row.state if row else "NOT_STARTED",
        "mastery": round(float(row.mastery_score), 1) if row else 0.0,
        "attempted": (row.questions_attempted or 0) if row else 0,
        "estimatedMinutes": concept.get("estimatedMinutes") or 30,
        "isCurrentFocus": status == PATH_CURRENT,
        "nextReviewAt": row.next_review_at.isoformat() if row and row.next_review_at else None,
        "note": note,
    }


def build_path(concepts: List[Dict], mastery_rows: List[ConceptMastery]) -> Dict:
    """Pure function so it is directly unit-testable."""
    mastery_map = {r.concept_id: r for r in mastery_rows}
    items: List[Dict] = []
    current_assigned = False

    for order, concept in enumerate(concepts, start=1):
        row = mastery_map.get(concept["id"])
        score = float(row.mastery_score) if row else 0.0
        check = is_prerequisite_mastered(mastery_map, concept["id"])
        note = explain_prerequisite_gap(concept["id"], check["weakPrerequisites"])

        if row and row.state == STATE_MASTERED:
            status = PATH_COMPLETED
        elif row and row.state in WEAK_STATES and (row.questions_attempted or 0) > 0:
            status = PATH_NEEDS_REVIEW
        elif not check["mastered"]:
            status = PATH_LOCKED
        elif not current_assigned:
            status = PATH_CURRENT
            current_assigned = True
        else:
            status = PATH_RECOMMENDED

        if status in (PATH_NEEDS_REVIEW, PATH_CURRENT) and not current_assigned:
            current_assigned = True

        items.append(_item(concept, order, status, row, note))

    # Guarantee exactly one focus item: prefer the first review/current item.
    if not any(i["isCurrentFocus"] for i in items):
        focus = next((i for i in items if i["status"] in (PATH_NEEDS_REVIEW, PATH_RECOMMENDED)), None)
        if focus:
            focus["isCurrentFocus"] = True

    return {
        "items": items,
        "completed": sum(1 for i in items if i["status"] == PATH_COMPLETED),
        "total": len(items),
    }


async def get_learning_path(db: AsyncSession, user_id: str, subject_id: str, chapter_id: Optional[str] = None) -> Dict:
    concepts = curriculum_concepts(subject_id, chapter_id)
    mastery_map = await load_mastery_map(db, user_id)
    path = build_path(concepts, list(mastery_map.values()))
    return {
        "userId": user_id,
        "subjectId": subject_id,
        "prerequisiteThreshold": PREREQUISITE_MASTERY_THRESHOLD,
        **path,
    }
