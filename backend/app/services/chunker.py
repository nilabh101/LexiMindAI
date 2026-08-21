"""Semantic-ish chunking by heading / paragraph, not blind character splits."""
from typing import List, Dict, Optional
import re
import uuid


def chunk_pages(pages: List[Dict], subject_id: Optional[str] = None, max_chars: int = 1200) -> List[Dict]:
    chunks: List[Dict] = []
    current_section = None
    buf: List[str] = []
    buf_page = None

    def flush():
        nonlocal buf, buf_page
        text = "\n".join(buf).strip()
        if text:
            chunks.append({
                "id": uuid.uuid4().hex[:12],
                "page_number": buf_page,
                "section": current_section,
                "text": text,
                "subject_id": subject_id,
                "chapter_id": None,
                "concept_id": None,
            })
        buf = []

    for page in pages:
        page_no = page.get("page")
        blocks = page.get("blocks") or []
        if not blocks:
            text = (page.get("clean_text") or page.get("raw_text") or "").strip()
            if text:
                for part in _split_paragraphs(text, max_chars):
                    chunks.append({
                        "id": uuid.uuid4().hex[:12],
                        "page_number": page_no,
                        "section": current_section,
                        "text": part,
                        "subject_id": subject_id,
                        "chapter_id": None,
                        "concept_id": None,
                    })
            continue

        for block in blocks:
            btype = block.get("type") or "paragraph"
            text = (block.get("text") or "").strip()
            if not text:
                continue
            if btype == "heading":
                flush()
                current_section = text
                buf_page = page_no
                buf = [text]
                continue
            if buf_page is None:
                buf_page = page_no
            if buf and sum(len(x) for x in buf) + len(text) > max_chars:
                flush()
                buf_page = page_no
            buf.append(text)
            if buf_page is None:
                buf_page = page_no
        flush()
        buf_page = None

    # Merge tiny leftovers into previous when possible
    merged: List[Dict] = []
    for ch in chunks:
        if merged and len(ch["text"]) < 80 and len(merged[-1]["text"]) + len(ch["text"]) < max_chars:
            merged[-1]["text"] = merged[-1]["text"] + "\n" + ch["text"]
        else:
            merged.append(ch)
    return merged


def _split_paragraphs(text: str, max_chars: int) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, buf = [], ""
    for p in paras:
        if buf and len(buf) + len(p) > max_chars:
            out.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}".strip() if buf else p
    if buf:
        out.append(buf)
    return out
