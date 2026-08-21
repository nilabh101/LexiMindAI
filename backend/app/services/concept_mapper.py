"""Map questions to concepts. Exact/normalized/keyword only. Do not guess."""
from typing import Dict, List, Optional
from app.services.concept_normalize import normalize_name


def map_question_to_concepts(
    question_text: str,
    concepts: List[Dict],
    section: Optional[str] = None,
) -> List[Dict]:
    qn = normalize_name(question_text or "")
    q_raw = (question_text or "").lower()
    section_n = normalize_name(section or "")

    scored = []
    for c in concepts:
        name = c.get("canonical_name") or c.get("name") or ""
        slug = c.get("slug") or c.get("id") or ""
        norm = c.get("normalized_name") or normalize_name(name)
        if not norm:
            continue
        score = 0.0
        reason = []
        if norm and norm in qn:
            score = 0.95
            reason.append("exact normalized name in question")
        elif name.lower() in q_raw:
            score = 0.9
            reason.append("exact name in question")
        else:
            tokens = [t for t in norm.split() if len(t) > 3]
            hits = sum(1 for t in tokens if t in qn)
            if tokens and hits == len(tokens) and len(tokens) >= 2:
                score = 0.75
                reason.append("all name tokens present")
            elif tokens and hits / len(tokens) >= 0.7 and len(tokens) >= 2:
                score = 0.55
                reason.append("most name tokens present")
        if section_n and (section_n == norm or norm in section_n or section_n in norm):
            score = max(score, 0.5)
            reason.append("section/topic match")
        if score <= 0:
            continue
        scored.append({
            "concept_id": slug,
            "canonical_name": name,
            "confidence": round(min(score, 0.99), 2),
            "needs_review": score < 0.7,
            "reason": "; ".join(reason),
        })

    scored.sort(key=lambda x: -x["confidence"])
    out = []
    for i, item in enumerate(scored[:4]):
        item["relationship"] = "PRIMARY" if i == 0 else "SECONDARY"
        out.append(item)
    return out
