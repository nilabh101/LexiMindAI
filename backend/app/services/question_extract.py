"""Extract actual questions from PYQ / question-bank text. Never generates questions."""
from typing import Dict, List, Optional
import re

Q_START = re.compile(
    r"(?m)^(?:\s*)(?:(?:question|ques)\s*)?(?:q\s*[.\-]?\s*)?(\d{1,3})\s*[.):]\s+",
    re.I,
)
SUBQ = re.compile(r"(?m)^\s*[\(\[]?([a-z]|[ivx]+)[\)\]]\s+", re.I)
MCQ_OPT = re.compile(r"(?m)^\s*(?:\(?([A-Da-d])\)?[.)]\s+)(.+)")
YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
MARKS_RE = re.compile(r"\[\s*(\d+(?:\.\d+)?)\s*(?:marks?|m)\s*\]|\((\d+(?:\.\d+)?)\s*(?:marks?|m)\)", re.I)
QNUM_INLINE = re.compile(r"^(?:q(?:uestion)?\s*)?(\d{1,3})\b", re.I)


def extract_questions(text: str, page_number: Optional[int] = None, document_year: Optional[int] = None) -> List[Dict]:
    if not text or not text.strip():
        return []

    if document_year is None:
        header = YEAR_RE.search(text[:500])
        if header:
            try:
                document_year = int(header.group(1))
            except ValueError:
                document_year = None

    spans = list(Q_START.finditer(text))
    if not spans:
        return _fallback_split(text, page_number, document_year)

    questions: List[Dict] = []
    for i, m in enumerate(spans):
        start = m.start()
        end = spans[i + 1].start() if i + 1 < len(spans) else len(text)
        block = text[start:end].strip()
        qnum = m.group(1)
        questions.extend(_parse_block(block, qnum, page_number, document_year))
    return questions


def _parse_block(block: str, qnum: str, page_number, document_year) -> List[Dict]:
    year = _find_year(block, document_year)
    marks = _find_marks(block)
    options = _find_options(block)
    body = _strip_options(block)
    subparts = _split_subquestions(body)
    if len(subparts) > 1:
        parent_text = subparts[0]["text"]
        out = [_question(
            question_number=str(qnum),
            question_text=parent_text or body,
            page_number=page_number,
            year=year,
            marks=marks,
            options=options if len(subparts) == 1 else None,
        )]
        for sp in subparts[1:]:
            out.append(_question(
                question_number=f"{qnum}({sp['label']})",
                question_text=f"{parent_text}\n({sp['label']}) {sp['text']}".strip() if parent_text else sp["text"],
                page_number=page_number,
                year=year,
                marks=None,
                options=None,
            ))
        return out
    return [_question(str(qnum), body, page_number, year, marks, options)]


def _split_subquestions(body: str) -> List[Dict]:
    matches = list(SUBQ.finditer(body))
    if len(matches) < 2:
        return [{"label": None, "text": body.strip()}]
    # stem is text before first subq
    stem = body[: matches[0].start()].strip()
    parts = [{"label": None, "text": stem}] if stem else []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        parts.append({"label": m.group(1).lower(), "text": body[m.end():end].strip()})
    return parts


def _find_options(block: str) -> Optional[List[str]]:
    opts = []
    for m in MCQ_OPT.finditer(block):
        opts.append(m.group(2).strip())
    if len(opts) >= 2:
        return opts[:6]
    return None


def _strip_options(block: str) -> str:
    lines = []
    for line in block.splitlines():
        if MCQ_OPT.match(line):
            continue
        lines.append(line)
    text = "\n".join(lines).strip()
    text = Q_START.sub("", text, count=1).strip()
    text = MARKS_RE.sub("", text).strip()
    return text


def _find_year(block: str, fallback: Optional[int]) -> Optional[int]:
    m = YEAR_RE.search(block[:200])
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return fallback
    return fallback


def _find_marks(block: str) -> Optional[float]:
    m = MARKS_RE.search(block)
    if not m:
        return None
    raw = m.group(1) or m.group(2)
    try:
        return float(raw)
    except ValueError:
        return None


def _question(question_number, question_text, page_number, year, marks, options):
    text = re.sub(r"\s+", " ", question_text).strip()
    confidence = 0.75 if QNUM_INLINE.search(question_number or "") or question_number else 0.45
    if len(text) < 12:
        confidence = 0.3
    return {
        "page_number": page_number,
        "question_number": question_number,
        "question_text": text,
        "year": year,
        "marks": marks,
        "options": options,
        "answer": None,
        "confidence": confidence,
        "needs_review": confidence < 0.55 or len(text) < 20,
    }


def _fallback_split(text: str, page_number, document_year) -> List[Dict]:
    """If no numbered questions, do not invent them."""
    if re.search(r"\b(question paper|previous year|examinee)\b", text, re.I):
        return [{
            "page_number": page_number,
            "question_number": None,
            "question_text": text.strip()[:2000],
            "year": document_year,
            "marks": None,
            "options": None,
            "answer": None,
            "confidence": 0.25,
            "needs_review": True,
        }]
    return []
