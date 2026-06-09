"""Document upload, listing, and retrieval endpoints."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from pathlib import Path
import asyncio

from app.core.database import get_db
from app.models.document import Document, Analysis
from app.services.ingestion import save_upload, extract_text_from_file
from app.nlp.text_processor import compute_stats, clean_text, get_clean_tokens, word_frequency
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

    class Config:
        from_attributes = True


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    save_path, safe_name = await save_upload(file)
    ext = Path(file.filename).suffix.lstrip(".").lower()

    text = extract_text_from_file(save_path, ext)
    text = clean_text(text)
    stats = compute_stats(text)

    doc = Document(
        filename=safe_name,
        original_filename=file.filename,
        file_type=ext,
        file_size=save_path.stat().st_size,
        extracted_text=text,
        status="ready",
        **{k: v for k, v in stats.items()},
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    result = DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        upload_date=doc.upload_date.isoformat(),
        word_count=doc.word_count,
        unique_word_count=doc.unique_word_count,
        sentence_count=doc.sentence_count,
        paragraph_count=doc.paragraph_count,
        character_count=doc.character_count,
        reading_time_minutes=doc.reading_time_minutes,
        reading_grade_level=doc.reading_grade_level,
        lexical_diversity=doc.lexical_diversity,
        status=doc.status,
    )
    return result


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
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            original_filename=d.original_filename,
            file_type=d.file_type,
            file_size=d.file_size,
            upload_date=d.upload_date.isoformat(),
            word_count=d.word_count,
            unique_word_count=d.unique_word_count,
            sentence_count=d.sentence_count,
            paragraph_count=d.paragraph_count,
            character_count=d.character_count,
            reading_time_minutes=d.reading_time_minutes,
            reading_grade_level=d.reading_grade_level,
            lexical_diversity=d.lexical_diversity,
            status=d.status,
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        upload_date=doc.upload_date.isoformat(),
        word_count=doc.word_count,
        unique_word_count=doc.unique_word_count,
        sentence_count=doc.sentence_count,
        paragraph_count=doc.paragraph_count,
        character_count=doc.character_count,
        reading_time_minutes=doc.reading_time_minutes,
        reading_grade_level=doc.reading_grade_level,
        lexical_diversity=doc.lexical_diversity,
        status=doc.status,
    )


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
