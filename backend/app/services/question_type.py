"""Deterministic question type classification. LLM only if caller requests and type is UNKNOWN."""
from typing import Dict, Optional
import re

TYPES = [
    "MCQ",
    "FILL_BLANK",
    "TRUE_FALSE",
    "SHORT_ANSWER",
    "LONG_ANSWER",
    "NUMERICAL",
    "PROOF",
    "UNKNOWN",
]


def classify_question_type(
    question_text: str,
    options: Optional[list] = None,
    marks: Optional[float] = None,
) -> Dict:
    text = question_text or ""
    lower = text.lower()

    if options and len(options) >= 2:
        return {"type": "MCQ", "confidence": 0.92, "reason": "Detected option list"}

    if re.search(r"_{3,}|\bfill in the blanks?\b|\bcomplete the\b", lower):
        return {"type": "FILL_BLANK", "confidence": 0.88, "reason": "Blank / fill-in phrasing"}

    if re.search(r"\btrue\s*or\s*false\b|\bstate whether\b", lower):
        return {"type": "TRUE_FALSE", "confidence": 0.9, "reason": "True/false phrasing"}

    if re.search(r"\b(prove|show that|verify that)\b", lower):
        return {"type": "PROOF", "confidence": 0.85, "reason": "Proof/verify language"}

    if re.search(r"\b(find the value|evaluate|calculate|compute|numerical)\b", lower):
        return {"type": "NUMERICAL", "confidence": 0.8, "reason": "Calculation language"}

    if marks is not None:
        if marks >= 8:
            return {"type": "LONG_ANSWER", "confidence": 0.7, "reason": "High mark value"}
        if marks <= 3:
            return {"type": "SHORT_ANSWER", "confidence": 0.65, "reason": "Low mark value"}

    if re.search(r"\b(explain in detail|write a short note|discuss)\b", lower):
        return {"type": "LONG_ANSWER", "confidence": 0.72, "reason": "Extended-response phrasing"}

    if re.search(r"\b(define|state|write|what is|explain)\b", lower):
        return {"type": "SHORT_ANSWER", "confidence": 0.6, "reason": "Short-response phrasing"}

    if "?" in text or re.match(r"^\d+", text.strip()):
        return {"type": "UNKNOWN", "confidence": 0.35, "reason": "Question-like but type unclear"}

    return {"type": "UNKNOWN", "confidence": 0.2, "reason": "Insufficient signals"}
