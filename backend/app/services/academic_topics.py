"""Academic chapter / topic / concept extraction from headings + keywords.

Reuses TF-IDF keyword extraction from existing NLP when helpful.
Does not hallucinate descriptions.
"""
from typing import Dict, List, Optional
import re
from collections import Counter

from app.services.concept_normalize import normalize_name, slugify
from app.nlp.topics import extract_keywords_tfidf


CHAPTER_RE = re.compile(
    r"^(?:chapter|unit|module)\s*[\dIVXLC]*[:.\-\s]+(.+)$",
    re.I,
)
TOPIC_HINTS = re.compile(
    r"^(?:topic|section|sub[\s-]?topic)\s*[\d.]*[:.\-\s]+(.+)$",
    re.I,
)


def extract_academic_structure(pages: List[Dict], subject_id: Optional[str] = None) -> Dict:
    chapters: List[Dict] = []
    topics: List[Dict] = []
    concepts: List[Dict] = []
    current_chapter = None
    current_topic = None

    for page in pages:
        page_no = page.get("page")
        blocks = page.get("blocks") or []
        for block in blocks:
            text = (block.get("text") or "").strip()
            if not text:
                continue
            btype = block.get("type")
            chapter_m = CHAPTER_RE.match(text)
            if chapter_m or (btype == "heading" and text.lower().startswith("chapter")):
                name = (chapter_m.group(1) if chapter_m else re.sub(r"^chapter\s*[\dIVXLC]*[:.\-\s]*", "", text, flags=re.I)).strip()
                if name:
                    current_chapter = name
                    chapters.append(_entry(name, page_no, 0.85))
                continue
            topic_m = TOPIC_HINTS.match(text)
            if topic_m or (btype == "heading" and 3 <= len(text.split()) <= 10):
                name = (topic_m.group(1) if topic_m else text).strip()
                if name and not _is_noise_heading(name):
                    current_topic = name
                    topics.append(_entry(name, page_no, 0.7, parent=current_chapter))
                    concepts.append(_concept(name, page_no, current_chapter, current_topic, subject_id, 0.55, needs_review=True))
                continue
            for name in _inline_concepts(text):
                concepts.append(_concept(name, page_no, current_chapter, current_topic, subject_id, 0.6, needs_review=False))

    # Keyword fallback if structure is sparse
    full = "\n".join((p.get("clean_text") or p.get("raw_text") or "") for p in pages)
    if len(concepts) < 3 and full.strip():
        try:
            kws = extract_keywords_tfidf(full, top_n=12)
        except Exception:
            kws = []
        for kw in kws:
            word = kw.get("keyword") or ""
            if len(word) < 5:
                continue
            concepts.append(_concept(word.title(), None, current_chapter, current_topic, subject_id, 0.35, needs_review=True))

    concepts = _dedupe_concepts(concepts)
    return {
        "chapters": _dedupe_entries(chapters),
        "topics": _dedupe_entries(topics),
        "concepts": concepts,
    }


def _entry(name: str, page, confidence: float, parent: Optional[str] = None) -> Dict:
    return {
        "name": name.strip(),
        "normalized_name": normalize_name(name),
        "confidence": confidence,
        "page": page,
        "parent": parent,
    }


def _concept(name, page, chapter, topic, subject_id, confidence, needs_review):
    return {
        "canonical_name": name.strip(),
        "normalized_name": normalize_name(name),
        "slug": slugify(name),
        "description": None,
        "description_origin": None,
        "subject_id": subject_id,
        "chapter_name": chapter,
        "topic_name": topic,
        "confidence": confidence,
        "page_number": page,
        "needs_review": needs_review or confidence < 0.5,
        "review_status": "NEEDS_REVIEW" if needs_review or confidence < 0.5 else "APPROVED",
    }


def _inline_concepts(text: str) -> List[str]:
    found = []
    for m in re.finditer(r"\b([A-Z][A-Za-z]+(?:'s)?(?:\s+[A-Z][A-Za-z]+){0,3}\s+(?:Theorem|Lemma|Corollary|Law|Rule))\b", text):
        found.append(m.group(1))
    for m in re.finditer(r"(?:definition|theorem|lemma)\s*[:.\-]\s*([A-Z][A-Za-z0-9\s']{3,60})", text, re.I):
        found.append(m.group(1).strip().rstrip("."))
    return found


def _is_noise_heading(name: str) -> bool:
    n = name.lower().strip()
    return n in {"contents", "index", "references", "bibliography", "introduction"} or n.isdigit()


def _dedupe_entries(items: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for it in items:
        key = it["normalized_name"]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _dedupe_concepts(items: List[Dict]) -> List[Dict]:
    by_norm = {}
    for it in items:
        key = it["normalized_name"]
        if not key:
            continue
        prev = by_norm.get(key)
        if not prev or it["confidence"] > prev["confidence"]:
            by_norm[key] = it
    return list(by_norm.values())
