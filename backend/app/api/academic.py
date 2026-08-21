"""Academic content, search, review, notes, retrieval."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.document import Document
from app.models.academic import (
    DocumentPage, DocumentChunk, AcademicConcept, Question, QuestionConcept, AcademicNote,
)
from app.core.identity import optional_user_id
from app.services.search import search_all
from app.services.embeddings import RetrievalService
from app.services.ownership import exclude_foreign, foreign_document_ids

router = APIRouter(tags=["academic"])


class ReviewUpdate(BaseModel):
    review_status: str  # APPROVED | NEEDS_REVIEW | REJECTED


def _note_out(n: AcademicNote) -> Dict:
    return {
        "id": n.id,
        "title": n.title,
        "subjectId": n.subject_id,
        "chapterId": n.chapter_id,
        "conceptId": n.concept_id,
        "content": n.content,
        "summary": n.summary,
        "formulas": n.formulas,
        "examples": n.examples,
        "keyPoints": n.key_points,
        "source": n.source,
        "sourceDocumentId": n.source_document_id,
        "sourcePages": n.source_pages,
        "isDemo": n.is_demo,
        "aiLabel": "AI-generated from your study material" if n.source == "AI_GENERATED" else None,
        "createdAt": n.created_at.isoformat() if n.created_at else None,
    }


def _question_out(q: Question) -> Dict:
    return {
        "id": q.id,
        "documentId": q.document_id,
        "pageNumber": q.page_number,
        "questionNumber": q.question_number,
        "question": q.question_text,
        "year": q.year,
        "marks": q.marks,
        "questionType": q.question_type,
        "options": q.options,
        "answer": q.answer,
        "explanation": q.explanation,
        "confidence": q.confidence,
        "needsReview": q.needs_review,
        "reviewStatus": q.review_status,
        "source": q.source,
        "difficulty": q.difficulty,
        "difficultyConfidence": q.difficulty_confidence,
        "subjectId": q.subject_id,
        "chapterId": q.chapter_id,
        "conceptId": q.concept_id,
        "isDemo": q.is_demo,
    }


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1),
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await search_all(db, q, viewer=optional_user_id(request, user_id))


@router.get("/notes")
async def list_notes(
    request: Request,
    subject_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = exclude_foreign(
        select(AcademicNote),
        AcademicNote.source_document_id,
        optional_user_id(request, user_id),
    )
    if subject_id:
        stmt = stmt.where(AcademicNote.subject_id == subject_id)
    if concept_id:
        stmt = stmt.where(AcademicNote.concept_id == concept_id)
    rows = (await db.execute(stmt.order_by(AcademicNote.id.desc()))).scalars().all()
    return [_note_out(n) for n in rows]


@router.get("/notes/{note_id}")
async def get_note(
    note_id: int,
    request: Request,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = exclude_foreign(
        select(AcademicNote).where(AcademicNote.id == note_id),
        AcademicNote.source_document_id,
        optional_user_id(request, user_id),
    )
    n = (await db.execute(stmt)).scalar_one_or_none()
    if not n:
        raise HTTPException(404, "Note not found")
    return _note_out(n)


@router.get("/questions")
async def list_questions(
    request: Request,
    subject_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    source: Optional[str] = None,
    pyq_only: bool = False,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = exclude_foreign(
        select(Question).where(Question.review_status != "REJECTED"),
        Question.document_id,
        optional_user_id(request, user_id),
    )
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if concept_id:
        stmt = stmt.where(Question.concept_id == concept_id)
    if pyq_only:
        stmt = stmt.where(Question.source == "PYQ")
    if source:
        stmt = stmt.where(Question.source == source.upper())
    rows = (await db.execute(stmt.order_by(Question.id.desc()).limit(200))).scalars().all()
    return [_question_out(q) for q in rows]


@router.get("/concepts/extracted")
async def list_extracted_concepts(
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AcademicConcept)
    if subject_id:
        stmt = stmt.where(AcademicConcept.subject_id == subject_id)
    rows = (await db.execute(stmt.limit(200))).scalars().all()
    return [
        {
            "id": c.slug,
            "canonicalName": c.canonical_name,
            "normalizedName": c.normalized_name,
            "description": c.description,
            "descriptionOrigin": c.description_origin,
            "subjectId": c.subject_id,
            "chapterId": c.chapter_id,
            "confidence": c.confidence,
            "sourceDocumentId": c.source_document_id,
            "pageNumber": c.page_number,
            "needsReview": c.needs_review,
            "reviewStatus": c.review_status,
            "isDemo": c.is_demo,
        }
        for c in rows
    ]


@router.get("/review/questions")
async def review_questions(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Question).where(Question.needs_review.is_(True)).limit(100)
    )).scalars().all()
    return [_question_out(q) for q in rows]


@router.get("/review/concepts")
async def review_concepts(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(AcademicConcept).where(AcademicConcept.needs_review.is_(True)).limit(100)
    )).scalars().all()
    return [{"id": c.id, "slug": c.slug, "name": c.canonical_name, "confidence": c.confidence} for c in rows]


@router.get("/review/mappings")
async def review_mappings(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(QuestionConcept).where(QuestionConcept.needs_review.is_(True)).limit(100)
    )).scalars().all()
    return [
        {"id": m.id, "questionId": m.question_id, "conceptId": m.concept_id, "relationship": m.rel_type, "confidence": m.confidence}
        for m in rows
    ]


@router.post("/review/questions/{question_id}")
async def update_question_review(question_id: int, body: ReviewUpdate, db: AsyncSession = Depends(get_db)):
    if body.review_status not in {"APPROVED", "NEEDS_REVIEW", "REJECTED"}:
        raise HTTPException(400, "Invalid review status")
    q = (await db.execute(select(Question).where(Question.id == question_id))).scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Question not found")
    q.review_status = body.review_status
    q.needs_review = body.review_status == "NEEDS_REVIEW"
    return {"id": q.id, "reviewStatus": q.review_status}


@router.get("/retrieve")
async def retrieve(
    request: Request,
    query: str = Query(..., min_length=1),
    subject_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    viewer = optional_user_id(request, user_id)
    chunks = (await db.execute(
        exclude_foreign(select(DocumentChunk), DocumentChunk.document_id, viewer).limit(400)
    )).scalars().all()
    questions = (await db.execute(
        exclude_foreign(
            select(Question).where(Question.source.in_(["PYQ", "DEMO"])),
            Question.document_id,
            viewer,
        ).limit(200)
    )).scalars().all()
    concepts = (await db.execute(select(AcademicConcept).limit(200))).scalars().all()
    svc = RetrievalService()
    return svc.retrieve_context(
        query,
        chunks=[{"id": c.id, "document_id": c.document_id, "page_number": c.page_number, "section": c.section, "text": c.text, "subject_id": c.subject_id, "concept_id": c.concept_id} for c in chunks],
        questions=[{"question_text": q.question_text, "year": q.year, "source": q.source, "concept_id": q.concept_id, "marks": q.marks} for q in questions],
        concepts=[{"canonical_name": c.canonical_name, "slug": c.slug, "name": c.canonical_name} for c in concepts],
        filters={"subject_id": subject_id, "concept_id": concept_id},
    )


@router.get("/documents/{doc_id}/detail")
async def document_detail(
    doc_id: int,
    request: Request,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    viewer = optional_user_id(request, user_id)
    doc = (await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.id.notin_(foreign_document_ids(viewer)),
        )
    )).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    pages = (await db.execute(select(DocumentPage).where(DocumentPage.document_id == doc_id).order_by(DocumentPage.page_number))).scalars().all()
    chunks = (await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))).scalars().all()
    concepts = (await db.execute(select(AcademicConcept).where(AcademicConcept.source_document_id == doc_id))).scalars().all()
    questions = (await db.execute(select(Question).where(Question.document_id == doc_id))).scalars().all()
    mappings = []
    if questions:
        qids = [q.id for q in questions]
        mappings = (await db.execute(select(QuestionConcept).where(QuestionConcept.question_id.in_(qids)))).scalars().all()
    return {
        "document": {
            "id": doc.id,
            "filename": doc.original_filename,
            "fileType": doc.file_type,
            "fileSize": doc.file_size,
            "uploadedAt": doc.upload_date.isoformat() if doc.upload_date else None,
            "status": doc.status,
            "educationLevel": doc.education_level,
            "classOrYear": doc.class_or_year,
            "course": doc.course,
            "semester": doc.semester,
            "subject": doc.subject,
            "subjectId": doc.subject_id,
            "documentType": doc.document_type,
            "classificationConfidence": doc.classification_confidence,
            "classificationReason": doc.classification_reason,
            "errorMessage": doc.error_message,
            "ocrRequired": doc.ocr_required,
            "ocrMessage": doc.ocr_message,
            "wordCount": doc.word_count,
        },
        "pages": [
            {"page": p.page_number, "rawText": p.raw_text, "cleanText": p.clean_text, "blocks": p.blocks}
            for p in pages
        ],
        "chunks": [{"id": c.id, "page": c.page_number, "section": c.section, "text": c.text} for c in chunks],
        "concepts": [
            {"id": c.slug, "name": c.canonical_name, "confidence": c.confidence, "page": c.page_number, "needsReview": c.needs_review, "chapter": c.chapter_name, "topic": c.topic_name}
            for c in concepts
        ],
        "questions": [_question_out(q) for q in questions],
        "mappings": [
            {"questionId": m.question_id, "conceptId": m.concept_id, "relationship": m.rel_type, "confidence": m.confidence, "needsReview": m.needs_review}
            for m in mappings
        ],
    }
