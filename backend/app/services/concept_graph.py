"""Prerequisite graph over Phase 2 concept data.

Edges come from the curriculum configuration (`api.education.CONCEPTS`), which
is the only place in Phase 2 that expresses concept dependencies. Extracted
document concepts have no dependency edges, so they simply have no
prerequisites — they are never locked.
"""
from typing import Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.education import CHAPTERS, CONCEPTS, SUBJECTS
from app.core.adaptive_config import PREREQUISITE_MASTERY_THRESHOLD
from app.models.academic import AcademicConcept, ConceptMastery

_CURRICULUM_BY_ID: Dict[str, Dict] = {c["id"]: c for c in CONCEPTS}
_CHAPTER_BY_ID: Dict[str, Dict] = {c["id"]: c for c in CHAPTERS}
_SUBJECT_BY_ID: Dict[str, Dict] = {s["id"]: s for s in SUBJECTS}


def get_prerequisites(concept_id: str) -> List[str]:
    """Direct prerequisites of a concept (empty for unknown/extracted concepts)."""
    concept = _CURRICULUM_BY_ID.get(concept_id)
    if not concept:
        return []
    return list(concept.get("prerequisites") or [])


def get_dependents(concept_id: str) -> List[str]:
    """Concepts that list `concept_id` as a prerequisite."""
    return [c["id"] for c in CONCEPTS if concept_id in (c.get("prerequisites") or [])]


def get_prerequisite_chain(concept_id: str, _seen: Optional[set] = None) -> List[str]:
    """Transitive prerequisites, deepest first, cycle-safe."""
    seen = _seen if _seen is not None else set()
    chain: List[str] = []
    for prereq in get_prerequisites(concept_id):
        if prereq in seen:
            continue
        seen.add(prereq)
        chain.extend(get_prerequisite_chain(prereq, seen))
        chain.append(prereq)
    return chain


def concept_label(concept_id: Optional[str], db_concepts: Optional[Dict[str, str]] = None) -> str:
    """Human-readable concept name from curriculum, DB concepts, or the slug."""
    if not concept_id:
        return "Unknown concept"
    if concept_id in _CURRICULUM_BY_ID:
        return _CURRICULUM_BY_ID[concept_id]["name"]
    if db_concepts and concept_id in db_concepts:
        return db_concepts[concept_id]
    return concept_id.replace("-", " ").title()


def concept_context(concept_id: str) -> Dict[str, Optional[str]]:
    """Subject/chapter names for a curriculum concept."""
    concept = _CURRICULUM_BY_ID.get(concept_id) or {}
    chapter = _CHAPTER_BY_ID.get(concept.get("chapterId") or "") or {}
    subject = _SUBJECT_BY_ID.get(concept.get("subjectId") or "") or {}
    return {
        "conceptId": concept_id,
        "concept": concept.get("name") or concept_label(concept_id),
        "chapterId": chapter.get("id"),
        "chapter": chapter.get("name"),
        "subjectId": subject.get("id"),
        "subject": subject.get("name"),
        "estimatedMinutes": concept.get("estimatedMinutes"),
        "difficulty": concept.get("difficulty"),
        "description": concept.get("description"),
    }


def curriculum_concepts(subject_id: Optional[str] = None, chapter_id: Optional[str] = None) -> List[Dict]:
    """Curriculum concepts, ordered by chapter order then chapter concept order."""
    items = [c for c in CONCEPTS
             if (not subject_id or c.get("subjectId") == subject_id)
             and (not chapter_id or c.get("chapterId") == chapter_id)]

    def sort_key(c: Dict):
        chapter = _CHAPTER_BY_ID.get(c.get("chapterId") or "") or {}
        concept_ids = chapter.get("conceptIds") or []
        order_in_chapter = concept_ids.index(c["id"]) if c["id"] in concept_ids else 99
        return (chapter.get("order") or 99, order_in_chapter)

    return sorted(items, key=sort_key)


async def load_mastery_map(
    db: AsyncSession,
    user_id: str,
    concept_ids: Optional[Sequence[str]] = None,
) -> Dict[str, ConceptMastery]:
    """All persisted mastery rows for one user, keyed by concept (single query)."""
    stmt = select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    if concept_ids:
        stmt = stmt.where(ConceptMastery.concept_id.in_(list(concept_ids)))
    rows = (await db.execute(stmt)).scalars().all()
    return {r.concept_id: r for r in rows}


async def load_db_concept_names(db: AsyncSession) -> Dict[str, str]:
    rows = (await db.execute(select(AcademicConcept.slug, AcademicConcept.canonical_name))).all()
    return {slug: name for slug, name in rows}


def is_prerequisite_mastered(
    mastery_map: Dict[str, ConceptMastery],
    concept_id: str,
    threshold: float = PREREQUISITE_MASTERY_THRESHOLD,
) -> Dict:
    """Are all direct prerequisites of `concept_id` at/above the threshold?

    Returns {"mastered": bool, "weakPrerequisites": [{conceptId, concept, mastery}]}.
    Concepts with no known prerequisites are always considered ready.
    """
    weak = []
    for prereq in get_prerequisites(concept_id):
        row = mastery_map.get(prereq)
        score = float(row.mastery_score or 0.0) if row else 0.0
        if score < threshold:
            weak.append({
                "conceptId": prereq,
                "concept": concept_label(prereq),
                "mastery": round(score, 1),
                "attempted": (row.questions_attempted or 0) if row else 0,
            })
    return {"mastered": not weak, "weakPrerequisites": weak}


def explain_prerequisite_gap(concept_id: str, weak_prerequisites: List[Dict]) -> Optional[str]:
    """Plain-language explanation of why a concept is gated."""
    if not weak_prerequisites:
        return None
    names = ", ".join(p["concept"] for p in weak_prerequisites)
    unattempted = [p for p in weak_prerequisites if not p.get("attempted")]
    if len(unattempted) == len(weak_prerequisites):
        return (
            f"{concept_label(concept_id)} depends on {names}, which you haven't practised yet. "
            "Start there first."
        )
    scores = ", ".join(
        f"{p['concept']} {p['mastery']:.0f}%" if p.get("attempted") else f"{p['concept']} not started"
        for p in weak_prerequisites
    )
    return (
        f"{concept_label(concept_id)} depends on {names} ({scores}). "
        f"Work on {'those concepts' if len(weak_prerequisites) > 1 else 'that concept'} first."
    )
