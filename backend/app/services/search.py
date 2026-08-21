"""Keyword search across academic entities."""
from typing import Dict, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.academic import AcademicConcept, Question, AcademicNote, DocumentChunk
from app.api.education import SUBJECTS, CHAPTERS, CONCEPTS


def _match(q: str, *fields) -> bool:
    n = (q or "").lower().strip()
    if not n:
        return False
    return any(n in (f or "").lower() for f in fields)


async def search_all(db: AsyncSession, query: str, limit: int = 20) -> Dict:
    q = (query or "").strip()
    subjects = [s for s in SUBJECTS if _match(q, s.get("name"), s.get("shortName"), s.get("id"), s.get("description"))]
    chapters = [c for c in CHAPTERS if _match(q, c.get("name"), c.get("id"), c.get("description"))]
    concepts_static = [c for c in CONCEPTS if _match(q, c.get("name"), c.get("id"), c.get("description"))]

    db_concepts = []
    notes = []
    questions = []
    documents = []
    chunks = []
    if q:
        like = f"%{q}%"
        r = await db.execute(
            select(AcademicConcept).where(
                or_(AcademicConcept.canonical_name.ilike(like), AcademicConcept.normalized_name.ilike(like))
            ).limit(limit)
        )
        db_concepts = [
            {"id": c.slug, "name": c.canonical_name, "subjectId": c.subject_id, "isDemo": c.is_demo, "confidence": c.confidence}
            for c in r.scalars().all()
        ]
        r = await db.execute(
            select(AcademicNote).where(
                or_(AcademicNote.title.ilike(like), AcademicNote.content.ilike(like), AcademicNote.summary.ilike(like))
            ).limit(limit)
        )
        notes = [
            {"id": n.id, "title": n.title, "subjectId": n.subject_id, "conceptId": n.concept_id, "source": n.source, "isDemo": n.is_demo}
            for n in r.scalars().all()
        ]
        r = await db.execute(
            select(Question).where(Question.question_text.ilike(like)).limit(limit)
        )
        questions = [
            {"id": qn.id, "question": qn.question_text, "source": qn.source, "year": qn.year, "conceptId": qn.concept_id, "isDemo": qn.is_demo}
            for qn in r.scalars().all()
        ]
        r = await db.execute(
            select(Document).where(
                or_(Document.original_filename.ilike(like), Document.subject.ilike(like), Document.extracted_text.ilike(like))
            ).limit(limit)
        )
        documents = [
            {"id": d.id, "filename": d.original_filename, "status": d.status, "documentType": d.document_type, "subjectId": d.subject_id}
            for d in r.scalars().all()
        ]
        r = await db.execute(
            select(DocumentChunk).where(DocumentChunk.text.ilike(like)).limit(limit)
        )
        chunks = [
            {"id": c.id, "documentId": c.document_id, "page": c.page_number, "section": c.section, "snippet": (c.text or "")[:240]}
            for c in r.scalars().all()
        ]

    return {
        "query": q,
        "subjects": subjects[:limit],
        "chapters": chapters[:limit],
        "concepts": (concepts_static + db_concepts)[:limit],
        "notes": notes,
        "questions": questions,
        "documents": documents,
        "chunks": chunks,
    }
