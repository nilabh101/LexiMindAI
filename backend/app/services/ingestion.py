"""Document ingestion: text extraction from TXT, PDF, DOCX."""
import os
import re
import uuid
import chardet
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.core.config import settings


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _safe_filename(filename: str) -> str:
    name = re.sub(r"[^\w\-.]", "_", filename)
    return f"{uuid.uuid4().hex}_{name}"


async def save_upload(file: UploadFile) -> Tuple[Path, str]:
    """Save uploaded file to disk. Returns (path, safe_filename)."""
    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Supported: {settings.allowed_extensions_list}",
        )

    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Basic malicious content check
    if b"<script" in content[:1024] or b"<?php" in content[:512]:
        raise HTTPException(status_code=400, detail="File contains potentially malicious content")

    safe_name = _safe_filename(file.filename)
    save_path = UPLOAD_DIR / safe_name
    save_path.write_bytes(content)
    return save_path, safe_name


def extract_text_from_file(file_path: Path, ext: str) -> str:
    """Extract plain text from supported file types."""
    if ext == "txt":
        return _extract_txt(file_path)
    elif ext == "pdf":
        return _extract_pdf(file_path)
    elif ext == "docx":
        return _extract_docx(file_path)
    raise ValueError(f"Unsupported extension: {ext}")


def _extract_txt(path: Path) -> str:
    raw = path.read_bytes()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    try:
        return raw.decode(encoding, errors="replace")
    except Exception:
        return raw.decode("utf-8", errors="replace")


def _extract_pdf(path: Path) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF extraction failed: {str(e)}")


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"DOCX extraction failed: {str(e)}")
