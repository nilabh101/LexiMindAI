"""Deterministic document classification. No LLM."""
from typing import Dict, Optional
import re

PYQ_PATTERNS = [
    r"previous\s+year",
    r"question\s+paper",
    r"end\s*sem",
    r"end[\s-]*semester",
    r"examination",
    r"mid[\s-]*sem",
    r"mid[\s-]*semester",
    r"\bpyq\b",
    r"university\s+exam",
    r"board\s+exam",
    r"time\s*:\s*\d+",
    r"maximum\s+marks",
    r"attempt\s+any",
]
QB_PATTERNS = [
    r"question\s+bank",
    r"practice\s+set",
    r"worksheet",
    r"assignment\s+questions",
]
NOTES_PATTERNS = [
    r"\bchapter\b",
    r"\btheorem\b",
    r"\bdefinition\b",
    r"\bformula\b",
    r"\bexample\b",
    r"lecture\s+notes",
    r"study\s+notes",
    r"\bcorollary\b",
    r"\blemma\b",
    r"\bproof\b",
]
REF_PATTERNS = [
    r"textbook",
    r"reference",
    r"bibliography",
    r"isbn",
]


def classify_document(
    filename: str = "",
    metadata: Optional[Dict] = None,
    extracted_text: str = "",
    user_type: Optional[str] = None,
) -> Dict:
    metadata = metadata or {}
    explicit = (user_type or metadata.get("document_type") or metadata.get("user_document_type") or "").upper()
    allowed = {"STUDY_NOTES", "PYQ", "QUESTION_BANK", "REFERENCE", "UNKNOWN"}
    if explicit in allowed and explicit != "UNKNOWN":
        return {
            "type": explicit,
            "confidence": 1.0,
            "reason": "User-selected document type",
        }

    blob = f"{filename}\n{extracted_text[:8000]}".lower()
    scores = {
        "PYQ": _score(blob, PYQ_PATTERNS),
        "QUESTION_BANK": _score(blob, QB_PATTERNS),
        "STUDY_NOTES": _score(blob, NOTES_PATTERNS),
        "REFERENCE": _score(blob, REF_PATTERNS),
    }
    q_hits = len(re.findall(r"(?:^|\n)\s*(?:q(?:uestion)?\s*[.\)]?\s*)?\d+[.)]", extracted_text[:12000], re.I))
    if q_hits >= 5:
        scores["PYQ"] += 2 if scores["PYQ"] else 1
        scores["QUESTION_BANK"] += 1

    best_type, best = max(scores.items(), key=lambda x: x[1])
    if best <= 0:
        return {"type": "UNKNOWN", "confidence": 0.2, "reason": "No strong academic type signals"}
    total = sum(scores.values()) or 1
    confidence = round(min(0.95, 0.35 + best / (total + 2)), 2)
    reasons = []
    if best_type == "PYQ":
        reasons.append("Matched exam/previous-year phrasing or numbered questions")
    elif best_type == "STUDY_NOTES":
        reasons.append("Matched lecture/chapter/theorem/definition language")
    elif best_type == "QUESTION_BANK":
        reasons.append("Matched question-bank/practice phrasing")
    else:
        reasons.append("Matched textbook/reference signals")
    return {"type": best_type, "confidence": confidence, "reason": "; ".join(reasons)}


def _score(blob: str, patterns) -> int:
    return sum(1 for p in patterns if re.search(p, blob, re.I))
