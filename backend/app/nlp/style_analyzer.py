"""Writing style classification and Document DNA engine."""
from typing import Dict, Any, List
import re
from app.nlp.text_processor import (
    get_clean_tokens, extract_sentences, compute_stats, _count_syllables, tokenize
)
from app.nlp.sentiment import analyze_sentiment_text


_STYLE_PROFILES = {
    "Academic": {
        "keywords": ["therefore", "however", "furthermore", "methodology", "hypothesis",
                     "analysis", "conclude", "evidence", "research", "study", "theory",
                     "literature", "framework", "significant"],
        "avg_sentence_len_min": 20,
        "formality_min": 0.6,
    },
    "Professional": {
        "keywords": ["please", "kindly", "regard", "sincerely", "attached", "following",
                     "concern", "request", "inform", "advise", "meeting", "deadline"],
        "avg_sentence_len_min": 15,
        "formality_min": 0.5,
    },
    "Research": {
        "keywords": ["data", "result", "figure", "table", "experiment", "sample", "control",
                     "variable", "statistic", "correlation", "regression", "measure"],
        "avg_sentence_len_min": 18,
        "formality_min": 0.65,
    },
    "News": {
        "keywords": ["reported", "according", "official", "statement", "confirmed", "source",
                     "breaking", "news", "journalist", "press", "announce"],
        "avg_sentence_len_min": 12,
        "formality_min": 0.45,
    },
    "Storytelling": {
        "keywords": ["once", "story", "character", "plot", "scene", "chapter", "narrator",
                     "protagonist", "adventure", "journey", "suddenly", "finally"],
        "avg_sentence_len_min": 10,
        "formality_min": 0.2,
    },
    "Blog": {
        "keywords": ["today", "share", "think", "believe", "tips", "guide", "check", "awesome",
                     "experience", "definitely", "personally", "honestly"],
        "avg_sentence_len_min": 10,
        "formality_min": 0.15,
    },
    "Casual": {
        "keywords": ["yeah", "okay", "cool", "stuff", "thing", "kind", "sort", "basically",
                     "pretty", "just", "like", "really", "totally"],
        "avg_sentence_len_min": 5,
        "formality_min": 0.0,
    },
    "Corporate": {
        "keywords": ["stakeholder", "synergy", "leverage", "optimize", "deliverable", "kpi",
                     "roi", "milestone", "initiative", "strategy", "alignment", "scalable"],
        "avg_sentence_len_min": 16,
        "formality_min": 0.55,
    },
}

_STYLE_DESCRIPTIONS = {
    "Academic": "Formal, structured writing with technical vocabulary, citations, and systematic argumentation.",
    "Professional": "Clear, concise business communication with formal tone and direct language.",
    "Research": "Data-driven, methodical writing with statistical language and objective analysis.",
    "News": "Informative, factual reporting with concise sentences and attributed statements.",
    "Storytelling": "Narrative-driven writing with descriptive language and character-focused elements.",
    "Blog": "Conversational, personal writing with informal tone and direct reader engagement.",
    "Casual": "Informal everyday language with simple vocabulary and relaxed sentence structure.",
    "Corporate": "Business-jargon-heavy writing focused on strategy, metrics, and organizational goals.",
}


def compute_formality_score(text: str) -> float:
    tokens = tokenize(text)
    words = [t.lower() for t in tokens if t.isalpha()]
    if not words:
        return 0.5
    formal_markers = {"therefore", "however", "furthermore", "nevertheless", "consequently",
                      "regarding", "whereas", "henceforth", "hereby", "pursuant"}
    informal_markers = {"yeah", "okay", "cool", "stuff", "thing", "basically", "pretty",
                        "just", "like", "really", "totally", "awesome", "gonna", "wanna"}
    formal_count = sum(1 for w in words if w in formal_markers)
    informal_count = sum(1 for w in words if w in informal_markers)
    total = len(words)
    score = (formal_count - informal_count) / total + 0.5
    return round(max(0.0, min(1.0, score)), 3)


def classify_writing_style(text: str) -> Dict[str, Any]:
    tokens_lower = [t.lower() for t in tokenize(text) if t.isalpha()]
    token_set = set(tokens_lower)
    sentences = extract_sentences(text)
    stats = compute_stats(text)
    avg_len = stats["average_sentence_length"]
    formality = compute_formality_score(text)

    style_scores: Dict[str, float] = {}
    for style, profile in _STYLE_PROFILES.items():
        keyword_hits = sum(1 for kw in profile["keywords"] if kw in token_set)
        keyword_score = keyword_hits / len(profile["keywords"])
        len_score = min(1.0, avg_len / max(profile["avg_sentence_len_min"], 1))
        formality_score = min(1.0, formality / max(profile["formality_min"], 0.01))
        total_score = 0.5 * keyword_score + 0.25 * len_score + 0.25 * formality_score
        style_scores[style] = round(total_score, 4)

    ranked = sorted(style_scores.items(), key=lambda x: -x[1])
    primary_style = ranked[0][0]
    confidence = round(ranked[0][1] * 100, 1)

    return {
        "primary_style": primary_style,
        "confidence": confidence,
        "description": _STYLE_DESCRIPTIONS[primary_style],
        "formality_score": formality,
        "scores": [{"style": s, "score": round(sc * 100, 1)} for s, sc in ranked],
        "metrics": {
            "avg_sentence_length": avg_len,
            "reading_grade": stats["reading_grade_level"],
            "lexical_diversity": stats["lexical_diversity"],
            "vocabulary_richness": stats["vocabulary_richness"],
        },
    }


def compute_document_dna(text: str, stats: Dict = None) -> Dict[str, Any]:
    """Generate the Document DNA fingerprint with 8 dimensions."""
    if stats is None:
        stats = compute_stats(text)

    sentiment = analyze_sentiment_text(text)
    style = classify_writing_style(text)
    formality = style["formality_score"]

    # Technicality: ratio of long/technical words
    tokens = [t.lower() for t in tokenize(text) if t.isalpha()]
    technical_words = [t for t in tokens if len(t) > 8]
    technicality = round(len(technical_words) / max(len(tokens), 1), 3)

    # Complexity: based on avg sentence length and syllables
    sentences = extract_sentences(text)
    avg_syllables = sum(
        _count_syllables(t) for t in tokens
    ) / max(len(tokens), 1)
    complexity = round(min(1.0, (stats["reading_grade_level"] / 20) + avg_syllables / 5), 3)

    # Creativity: vocabulary richness indicator
    creativity = round(stats["lexical_diversity"], 3)

    # Objectivity: inverse of subjectivity
    objectivity = round(1.0 - sentiment["subjectivity"], 3)

    # Emotionality: based on sentiment polarity magnitude
    emotionality = round(abs(sentiment["polarity"]), 3)

    # Readability: inverse Flesch-Kincaid
    readability = round(max(0, min(1.0, 1 - stats["reading_grade_level"] / 20)), 3)

    # Vocabulary strength
    vocab_strength = round(stats["vocabulary_richness"] / 100, 3)

    dna = {
        "technicality": technicality,
        "complexity": complexity,
        "creativity": creativity,
        "objectivity": objectivity,
        "emotionality": emotionality,
        "readability": readability,
        "formality": formality,
        "vocabulary_strength": vocab_strength,
    }

    radar = [
        {"dimension": k.replace("_", " ").title(), "value": round(v * 100, 1)}
        for k, v in dna.items()
    ]

    return {
        "dna": dna,
        "radar": radar,
        "writing_style": style["primary_style"],
        "dominant_trait": max(dna, key=dna.get),
    }
