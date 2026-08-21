"""End-to-end academic document processing pipeline."""
from pathlib import Path
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.models.academic import (
    DocumentPage, DocumentChunk, AcademicConcept, Question, QuestionConcept, AcademicNote,
)
from app.nlp.text_processor import compute_stats
from app.nlp.summarizer import generate_summaries
from app.services.ingestion import extract_structured_pages
from app.services.academic_cleaner import clean_academic_text, extract_formulas
from app.services.classifier import classify_document
from app.services.chunker import chunk_pages
from app.services.academic_topics import extract_academic_structure
from app.services.concept_normalize import slugify
from app.services.question_extract import extract_questions
from app.services.question_type import classify_question_type
from app.services.concept_mapper import map_question_to_concepts
from app.services.difficulty import estimate_difficulty
from app.services.ocr import maybe_ocr_pdf
from app.api.education import CONCEPTS as CURRICULUM_CONCEPTS, CHAPTERS as CURRICULUM_CHAPTERS


async def process_document_by_id(doc_id: int) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await run_pipeline(session, doc_id)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            async with AsyncSessionLocal() as err_session:
                result = await err_session.execute(select(Document).where(Document.id == doc_id))
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = "FAILED"
                    doc.error_message = str(exc)[:800]
                    await err_session.commit()


async def run_pipeline(db: AsyncSession, doc_id: int) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError("Document not found")

    doc.status = "PROCESSING"
    doc.error_message = None
    await db.flush()

    path = Path("uploads") / doc.filename
    if not path.exists():
        doc.status = "FAILED"
        doc.error_message = "Uploaded file is missing from disk."
        return doc

    try:
        structured = extract_structured_pages(path, doc.file_type)
    except Exception as exc:
        doc.status = "FAILED"
        doc.error_message = f"Unsupported or corrupt file: {exc}"[:800]
        return doc

    pages = structured.get("pages") or []
    raw_text = structured.get("raw_text") or ""
    if structured.get("error") and not pages:
        doc.status = "FAILED"
        doc.error_message = structured["error"]
        return doc

    threshold = settings.OCR_TEXT_THRESHOLD
    if doc.file_type == "pdf":
        ocr = maybe_ocr_pdf(path, raw_text, threshold=threshold)
        if ocr["required"] and not ocr["used"]:
            doc.ocr_required = True
            doc.ocr_message = ocr["message"]
            doc.raw_text = raw_text
            doc.status = "NEEDS_REVIEW"
            doc.error_message = ocr["message"]
            if len(raw_text.strip()) == 0:
                return doc
        elif ocr["used"]:
            raw_text = ocr["text"]
            if not pages:
                pages = [{"page": 1, "raw_text": raw_text, "blocks": [{"type": "paragraph", "text": raw_text}]}]
            doc.ocr_required = False
            doc.ocr_message = ocr.get("message")

    doc.raw_text = raw_text
    clean_pages = []
    for p in pages:
        raw_p = p.get("raw_text") or ""
        clean_p = clean_academic_text(raw_p)
        blocks = p.get("blocks") or []
        clean_blocks = []
        for b in blocks:
            clean_blocks.append({
                "type": b.get("type") or "paragraph",
                "text": clean_academic_text(b.get("text") or ""),
            })
        clean_pages.append({
            "page": p.get("page"),
            "raw_text": raw_p,
            "clean_text": clean_p,
            "blocks": clean_blocks or [{"type": "paragraph", "text": clean_p}] if clean_p else [],
        })

    full_clean = "\n\n".join(p["clean_text"] for p in clean_pages if p.get("clean_text"))
    doc.extracted_text = full_clean
    stats = compute_stats(full_clean or "")
    for k in ("word_count", "unique_word_count", "sentence_count", "paragraph_count",
              "character_count", "reading_time_minutes", "reading_grade_level", "lexical_diversity"):
        setattr(doc, k, stats.get(k, 0))

    classification = classify_document(
        filename=doc.original_filename or "",
        extracted_text=full_clean,
        user_type=doc.user_document_type,
        metadata={"document_type": doc.user_document_type},
    )
    doc.document_type = classification["type"]
    doc.classification_confidence = classification["confidence"]
    doc.classification_reason = classification["reason"]

    await _replace_pages(db, doc.id, clean_pages)

    chunks = chunk_pages(clean_pages, subject_id=doc.subject_id)
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    for ch in chunks:
        db.add(DocumentChunk(
            document_id=doc.id,
            page_number=ch.get("page_number"),
            section=ch.get("section"),
            text=ch.get("text") or "",
            subject_id=doc.subject_id,
            source_type=doc.document_type,
        ))

    structure = extract_academic_structure(clean_pages, subject_id=doc.subject_id)
    curriculum_concepts = _curriculum_concepts(doc.subject_id)
    stored_concepts = []
    for c in structure["concepts"]:
        slug = c["slug"]
        existing = await db.execute(select(AcademicConcept).where(AcademicConcept.slug == slug))
        row = existing.scalar_one_or_none()
        if row:
            if c["confidence"] > (row.confidence or 0):
                row.confidence = c["confidence"]
                row.source_document_id = doc.id
                row.page_number = c.get("page_number")
            stored_concepts.append(_concept_dict(row))
            continue
        row = AcademicConcept(
            slug=slug,
            canonical_name=c["canonical_name"],
            normalized_name=c["normalized_name"],
            description=c.get("description"),
            description_origin=c.get("description_origin"),
            subject_id=doc.subject_id,
            chapter_name=c.get("chapter_name"),
            topic_name=c.get("topic_name"),
            confidence=c["confidence"],
            source_document_id=doc.id,
            page_number=c.get("page_number"),
            needs_review=c.get("needs_review", False),
            review_status=c.get("review_status") or "APPROVED",
        )
        # link chapter id from curriculum if names match
        row.chapter_id = _match_chapter(c.get("chapter_name"), doc.subject_id)
        db.add(row)
        stored_concepts.append({
            "slug": slug,
            "canonical_name": c["canonical_name"],
            "normalized_name": c["normalized_name"],
            "id": slug,
            "name": c["canonical_name"],
        })

    mapping_concepts = stored_concepts + curriculum_concepts

    if doc.document_type in {"PYQ", "QUESTION_BANK"}:
        await db.execute(delete(Question).where(Question.document_id == doc.id, Question.source.in_(["PYQ", "UPLOADED"])))
        all_qs = []
        for p in clean_pages:
            all_qs.extend(extract_questions(p.get("clean_text") or "", page_number=p.get("page")))
        if not all_qs and full_clean:
            all_qs = extract_questions(full_clean)

        source_label = "PYQ" if doc.document_type == "PYQ" else "UPLOADED"
        for qdata in all_qs:
            qtype = classify_question_type(qdata["question_text"], qdata.get("options"), qdata.get("marks"))
            maps = map_question_to_concepts(qdata["question_text"], mapping_concepts, section=None)
            primary = maps[0]["concept_id"] if maps else None
            diff = estimate_difficulty(
                qdata["question_text"],
                marks=qdata.get("marks"),
                question_type=qtype["type"],
                concept_count=len(maps),
            )
            qrow = Question(
                document_id=doc.id,
                page_number=qdata.get("page_number"),
                question_number=qdata.get("question_number"),
                question_text=qdata["question_text"],
                year=qdata.get("year"),
                marks=qdata.get("marks"),
                question_type=qtype["type"],
                options=qdata.get("options"),
                answer=qdata.get("answer"),
                confidence=min(qdata.get("confidence") or 0, qtype["confidence"]),
                needs_review=bool(qdata.get("needs_review") or qtype["confidence"] < 0.5),
                review_status="NEEDS_REVIEW" if (qdata.get("needs_review") or not maps) else "APPROVED",
                source=source_label,
                difficulty=diff["difficulty"],
                difficulty_confidence=diff["difficulty_confidence"],
                subject_id=doc.subject_id,
                concept_id=primary,
            )
            db.add(qrow)
            await db.flush()
            for mp in maps:
                db.add(QuestionConcept(
                    question_id=qrow.id,
                    concept_id=mp["concept_id"],
                    rel_type=mp["relationship"],
                    confidence=mp["confidence"],
                    needs_review=mp["needs_review"],
                ))

    if doc.document_type in {"STUDY_NOTES", "REFERENCE", "UNKNOWN"} and full_clean.strip():
        await _derive_notes(db, doc, full_clean, structure, clean_pages)

    low_conf = classification["confidence"] < 0.45
    if doc.ocr_required:
        doc.status = "NEEDS_REVIEW"
    elif low_conf and doc.document_type == "UNKNOWN":
        doc.status = "NEEDS_REVIEW"
    else:
        doc.status = "READY"
    return doc


async def _replace_pages(db: AsyncSession, doc_id: int, pages):
    await db.execute(delete(DocumentPage).where(DocumentPage.document_id == doc_id))
    for p in pages:
        db.add(DocumentPage(
            document_id=doc_id,
            page_number=p.get("page") or 1,
            raw_text=p.get("raw_text"),
            clean_text=p.get("clean_text"),
            blocks=p.get("blocks"),
        ))


def _curriculum_concepts(subject_id: Optional[str]):
    items = []
    for c in CURRICULUM_CONCEPTS:
        if subject_id and c.get("subjectId") != subject_id:
            continue
        items.append({
            "id": c["id"],
            "slug": c["id"],
            "canonical_name": c["name"],
            "normalized_name": slugify(c["name"]).replace("-", " "),
            "name": c["name"],
        })
    return items


def _match_chapter(name: Optional[str], subject_id: Optional[str]) -> Optional[str]:
    if not name:
        return None
    target = name.lower()
    for ch in CURRICULUM_CHAPTERS:
        if subject_id and ch.get("subjectId") != subject_id:
            continue
        if ch["name"].lower() in target or target in ch["name"].lower():
            return ch["id"]
    return None


def _concept_dict(row: AcademicConcept) -> dict:
    return {
        "slug": row.slug,
        "id": row.slug,
        "canonical_name": row.canonical_name,
        "normalized_name": row.normalized_name,
        "name": row.canonical_name,
    }


async def _derive_notes(db, doc: Document, full_clean: str, structure: dict, pages):
    existing = await db.execute(
        select(AcademicNote).where(
            AcademicNote.source_document_id == doc.id,
            AcademicNote.source == "SOURCE_DERIVED",
        )
    )
    if existing.scalars().first():
        return
    try:
        summaries = generate_summaries(full_clean)
        summary = summaries.get("executive_summary") or summaries.get("short") or None
    except Exception:
        summary = None
        summaries = {}
    formulas = extract_formulas(full_clean)
    key_points = []
    for t in (structure.get("topics") or [])[:8]:
        key_points.append(t["name"])
    title = doc.original_filename.rsplit(".", 1)[0]
    pages_used = [p.get("page") for p in pages if p.get("page") is not None]
    primary_concept = None
    if structure.get("concepts"):
        primary_concept = structure["concepts"][0].get("slug")
    content = full_clean[:12000]
    db.add(AcademicNote(
        title=title,
        subject_id=doc.subject_id,
        concept_id=primary_concept,
        content=content,
        summary=summary,
        formulas=formulas or None,
        examples=None,
        key_points=key_points or None,
        source="SOURCE_DERIVED",
        source_document_id=doc.id,
        source_pages=pages_used[:40],
        is_demo=False,
    ))
