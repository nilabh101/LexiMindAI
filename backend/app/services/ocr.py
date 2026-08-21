"""Optional OCR fallback. Never a blocker for text PDFs."""
from pathlib import Path
from typing import Dict


def maybe_ocr_pdf(path: Path, current_text: str, threshold: int = 80) -> Dict:
    if len((current_text or "").strip()) >= threshold:
        return {"used": False, "text": current_text, "required": False, "message": None}

    ocr_text = _try_pymupdf_ocr(path)
    if ocr_text and len(ocr_text.strip()) >= threshold:
        return {
            "used": True,
            "text": ocr_text,
            "required": False,
            "message": "OCR fallback produced extractable text",
        }

    return {
        "used": False,
        "text": current_text or "",
        "required": True,
        "message": "This document requires OCR processing.",
    }


def _try_pymupdf_ocr(path: Path) -> str:
    """Best-effort: Tesseract via PyMuPDF if available. Silent skip otherwise."""
    try:
        import fitz
        doc = fitz.open(str(path))
        parts = []
        for page in doc:
            try:
                tp = page.get_textpage_ocr(language="eng", dpi=200)
                parts.append(page.get_text(textpage=tp) or "")
            except Exception:
                # get_textpage_ocr needs Tesseract installed
                break
        doc.close()
        return "\n\n".join(p for p in parts if p.strip())
    except Exception:
        return ""
