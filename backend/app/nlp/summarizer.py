"""Extractive summarization using sentence scoring (TF-IDF + position weighting)."""
from typing import Dict, List, Any
from app.nlp.text_processor import (
    extract_sentences, get_clean_tokens, compute_stats
)
from collections import Counter
import re


def _score_sentences(sentences: List[str], token_freq: Counter, total_tokens: int) -> List[float]:
    scores = []
    for i, sent in enumerate(sentences):
        tokens = get_clean_tokens(sent, remove_stopwords=True)
        if not tokens:
            scores.append(0.0)
            continue
        tf_score = sum(token_freq.get(t, 0) for t in tokens) / len(tokens)
        # Positional weight: first and last sentences are important
        n = len(sentences)
        pos_weight = 1.0
        if i < n * 0.1:
            pos_weight = 1.3
        elif i > n * 0.9:
            pos_weight = 1.1
        scores.append(tf_score * pos_weight)
    return scores


def _extract_top_sentences(text: str, target_words: int) -> str:
    sentences = extract_sentences(text)
    if not sentences:
        return ""

    tokens = get_clean_tokens(text, remove_stopwords=True)
    freq = Counter(tokens)
    total = len(tokens) or 1

    scores = _score_sentences(sentences, freq, total)
    indexed = sorted(enumerate(scores), key=lambda x: -x[1])

    selected = []
    word_count = 0
    for idx, score in indexed:
        sent = sentences[idx]
        wc = len(sent.split())
        if word_count + wc > target_words * 1.4:
            continue
        selected.append((idx, sent))
        word_count += wc
        if word_count >= target_words:
            break

    # Restore original order
    selected.sort(key=lambda x: x[0])
    return " ".join(s for _, s in selected)


def generate_summaries(text: str) -> Dict[str, Any]:
    stats = compute_stats(text)
    sentences = extract_sentences(text)

    summary_50 = _extract_top_sentences(text, 50)
    summary_100 = _extract_top_sentences(text, 100)
    summary_250 = _extract_top_sentences(text, 250)

    # Bullet-point summary: top 5-8 sentences
    tokens = get_clean_tokens(text, remove_stopwords=True)
    freq = Counter(tokens)
    scores = _score_sentences(sentences, freq, len(tokens) or 1)
    indexed = sorted(enumerate(scores), key=lambda x: -x[1])[:8]
    indexed.sort(key=lambda x: x[0])
    bullet_points = [sentences[i] for i, _ in indexed]

    # Executive summary: formal intro + key points
    first_para = text.split("\n\n")[0][:300] if "\n\n" in text else text[:300]
    executive = f"This document contains {stats['word_count']} words across {stats['sentence_count']} sentences. "
    executive += summary_100

    # Research summary
    research = (
        f"Document Statistics: {stats['word_count']} words, "
        f"{stats['sentence_count']} sentences, "
        f"Grade Level {stats['reading_grade_level']}. "
        + summary_250
    )

    return {
        "summary_50": summary_50,
        "summary_100": summary_100,
        "summary_250": summary_250,
        "bullet_points": bullet_points,
        "executive_summary": executive,
        "research_summary": research,
        "word_counts": {
            "50_word": len(summary_50.split()),
            "100_word": len(summary_100.split()),
            "250_word": len(summary_250.split()),
        },
    }
