"""Transparent difficulty estimate — not a validated psychometric score."""
from typing import Dict, Optional
import re


def estimate_difficulty(
    question_text: str,
    marks: Optional[float] = None,
    question_type: Optional[str] = None,
    concept_count: int = 0,
) -> Dict:
    text = question_text or ""
    score = 1  # 1 easy, 2 medium, 3 hard
    reasons = []

    if marks is not None:
        if marks >= 8:
            score = 3
            reasons.append("high marks")
        elif marks >= 4:
            score = 2
            reasons.append("moderate marks")
        else:
            score = 1
            reasons.append("low marks")

    if question_type in {"PROOF", "LONG_ANSWER"}:
        score = max(score, 3)
        reasons.append(question_type.lower())
    elif question_type in {"NUMERICAL"}:
        score = max(score, 2)
        reasons.append("numerical")
    elif question_type == "MCQ" and score == 1:
        reasons.append("mcq")

    if concept_count >= 3:
        score = max(score, 3)
        reasons.append("multiple concepts")
    elif concept_count == 2:
        score = max(score, 2)
        reasons.append("two concepts")

    depth_hits = len(re.findall(r"\b(prove|verify|hence|deduce|critically|compare|derive)\b", text, re.I))
    calc_hits = len(re.findall(r"[=+\-×÷∂∫]|find|evaluate|calculate", text, re.I))
    if depth_hits >= 2:
        score = max(score, 3)
        reasons.append("reasoning language")
    elif calc_hits >= 3:
        score = max(score, 2)
        reasons.append("calculation complexity")

    label = {1: "EASY", 2: "MEDIUM", 3: "HARD"}[min(3, max(1, score))]
    conf = 0.45 if not reasons else min(0.8, 0.4 + 0.1 * len(reasons))
    return {
        "difficulty": label,
        "difficulty_confidence": round(conf, 2),
        "reason": ", ".join(reasons) if reasons else "default estimate",
    }
