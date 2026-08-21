"""Document upload, listing, and retrieval endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from pathlib import Path

from app.core.database import get_db
from app.models.document import Document
from app.services.ingestion import save_upload, extract_text_from_file
from app.nlp.text_processor import compute_stats, clean_text
from pydantic import BaseModel

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_date: str
    word_count: int
    unique_word_count: int
    sentence_count: int
    paragraph_count: int
    character_count: int
    reading_time_minutes: float
    reading_grade_level: float
    lexical_diversity: float
    status: str
    education_level: Optional[str] = None
    class_or_year: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    subject: Optional[str] = None
    subject_id: Optional[str] = None
    document_type: Optional[str] = None
    error_message: Optional[str] = None
    ocr_required: Optional[bool] = False

    class Config:
        from_attributes = True


def _to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        upload_date=doc.upload_date.isoformat() if doc.upload_date else "",
        word_count=doc.word_count or 0,
        unique_word_count=doc.unique_word_count or 0,
        sentence_count=doc.sentence_count or 0,
        paragraph_count=doc.paragraph_count or 0,
        character_count=doc.character_count or 0,
        reading_time_minutes=doc.reading_time_minutes or 0.0,
        reading_grade_level=doc.reading_grade_level or 0.0,
        lexical_diversity=doc.lexical_diversity or 0.0,
        status=doc.status or "UPLOADED",
        education_level=doc.education_level,
        class_or_year=doc.class_or_year,
        course=doc.course,
        semester=doc.semester,
        subject=doc.subject,
        subject_id=doc.subject_id,
        document_type=doc.document_type,
        error_message=doc.error_message,
        ocr_required=bool(doc.ocr_required),
    )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    education_level: Optional[str] = Form(None),
    class_or_year: Optional[str] = Form(None),
    course: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    subject_id: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    process: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    save_path, safe_name = await save_upload(file)
    ext = Path(file.filename).suffix.lstrip(".").lower()

    text = ""
    stats = {}
    extract_error = None
    try:
        text = clean_text(extract_text_from_file(save_path, ext))
        stats = compute_stats(text)
    except Exception as exc:
        extract_error = str(exc)

    valid_cols = {
        "word_count", "unique_word_count", "sentence_count", "paragraph_count",
        "character_count", "reading_time_minutes", "reading_grade_level", "lexical_diversity"
    }
    user_type = (document_type or "").upper() or None
    if user_type == "":
        user_type = None
    doc = Document(
        filename=safe_name,
        original_filename=file.filename,
        file_type=ext,
        file_size=save_path.stat().st_size,
        extracted_text=text or None,
        raw_text=text or None,
        status="UPLOADED",
        user_id=user_id,
        education_level=education_level,
        class_or_year=class_or_year,
        course=course,
        semester=semester,
        subject=subject,
        subject_id=subject_id,
        user_document_type=user_type,
        document_type=user_type,
        error_message=extract_error,
        **{k: v for k, v in stats.items() if k in valid_cols},
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    if process:
        from app.services.pipeline import process_document_by_id
        background_tasks.add_task(process_document_by_id, doc.id)

    return _to_response(doc)


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).order_by(Document.upload_date.desc()).offset(skip).limit(limit)
    )
    docs = result.scalars().all()
    return [_to_response(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_response(doc)


@router.post("/{doc_id}/process", response_model=DocumentResponse)
async def process_document(doc_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "PROCESSING"
    doc.error_message = None
    from app.services.pipeline import process_document_by_id
    background_tasks.add_task(process_document_by_id, doc.id)
    return _to_response(doc)


@router.post("/{doc_id}/retry", response_model=DocumentResponse)
async def retry_document(doc_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await process_document(doc_id, background_tasks, db)


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file from disk
    upload_path = Path("uploads") / doc.filename
    if upload_path.exists():
        upload_path.unlink()

    await db.execute(delete(Document).where(Document.id == doc_id))
    return {"message": f"Document {doc_id} deleted successfully"}


@router.get("/{doc_id}/search")
async def search_in_document(
    doc_id: int,
    query: str = Query(..., min_length=1),
    case_sensitive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Search for a word or phrase — returns total count, every location, context snippets."""
    import re
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.extracted_text:
        raise HTTPException(status_code=422, detail="Document text not available")

    text = doc.extracted_text
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.escape(query)
    matches = list(re.finditer(pattern, text, flags))

    occurrences = []
    for i, m in enumerate(matches[:200]):
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 100)
        snippet = text[start:end].replace("\n", " ").strip()
        line_number = text[: m.start()].count("\n") + 1
        occurrences.append({
            "occurrence_number": i + 1,
            "line": line_number,
            "char_position": m.start(),
            "snippet": f"...{snippet}...",
            "matched_text": m.group(),
        })

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    para_counts = []
    for i, para in enumerate(paragraphs):
        hits = len(re.findall(pattern, para, flags))
        if hits > 0:
            para_counts.append({"paragraph": i + 1, "count": hits})

    return {
        "document_id": doc_id,
        "query": query,
        "case_sensitive": case_sensitive,
        "total_count": len(matches),
        "occurrences": occurrences,
        "paragraph_distribution": para_counts,
        "total_paragraphs_with_match": len(para_counts),
    }
