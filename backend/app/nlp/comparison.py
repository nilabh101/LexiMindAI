"""Document comparison engine."""
from typing import Dict, List, Any
from collections import Counter
import math
from app.nlp.text_processor import get_clean_tokens, compute_stats
from app.nlp.sentiment import analyze_sentiment_text
from app.nlp.style_analyzer import classify_writing_style, compute_document_dna


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    keys = set(vec_a) | set(vec_b)
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return round(dot / (mag_a * mag_b), 4)


def build_tf_vector(tokens: List[str]) -> Dict[str, float]:
    counter = Counter(tokens)
    total = len(tokens) or 1
    return {w: c / total for w, c in counter.items()}


def compare_documents(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    docs: list of {"id": str, "filename": str, "text": str}
    """
    if len(docs) < 2:
        return {"error": "Need at least 2 documents to compare"}

    processed = []
    for doc in docs:
        text = doc["text"]
        tokens = get_clean_tokens(text, remove_stopwords=True)
        stats = compute_stats(text)
        sentiment = analyze_sentiment_text(text)
        style = classify_writing_style(text)
        dna = compute_document_dna(text, stats)
        tf_vec = build_tf_vector(tokens)
        processed.append({
            "id": doc["id"],
            "filename": doc["filename"],
            "tokens": tokens,
            "stats": stats,
            "sentiment": sentiment,
            "style": style,
            "dna": dna,
            "tf_vec": tf_vec,
        })

    # Pairwise similarity matrix
    n = len(processed)
    similarity_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            elif j < i:
                row.append(similarity_matrix[j][i])
            else:
                sim = cosine_similarity(
                    processed[i]["tf_vec"], processed[j]["tf_vec"]
                )
                row.append(round(sim * 100, 1))
        similarity_matrix.append(row)

    # Vocabulary comparison
    vocab_sets = [set(p["tokens"]) for p in processed]
    common_vocab = vocab_sets[0]
    for vs in vocab_sets[1:]:
        common_vocab &= vs
    all_vocab = set()
    for vs in vocab_sets:
        all_vocab |= vs

    jaccard = round(len(common_vocab) / len(all_vocab) * 100, 1) if all_vocab else 0

    # Stat comparison
    stat_comparison = []
    stat_keys = ["word_count", "unique_word_count", "sentence_count",
                 "reading_grade_level", "lexical_diversity"]
    for key in stat_keys:
        stat_comparison.append({
            "metric": key.replace("_", " ").title(),
            "values": [
                {"document": p["filename"], "value": p["stats"].get(key, 0)}
                for p in processed
            ],
        })

    # Sentiment comparison
    sentiment_comparison = [
        {
            "document": p["filename"],
            "polarity": p["sentiment"]["polarity"],
            "subjectivity": p["sentiment"]["subjectivity"],
            "label": p["sentiment"]["label"],
        }
        for p in processed
    ]

    # DNA heatmap data
    dna_dims = ["technicality", "complexity", "creativity", "objectivity",
                "emotionality", "readability", "formality", "vocabulary_strength"]
    dna_heatmap = []
    for dim in dna_dims:
        row = {"dimension": dim.replace("_", " ").title()}
        for p in processed:
            row[p["filename"]] = round(p["dna"]["dna"].get(dim, 0) * 100, 1)
        dna_heatmap.append(row)

    # Style comparison
    style_comparison = [
        {"document": p["filename"], "style": p["style"]["primary_style"],
         "confidence": p["style"]["confidence"]}
        for p in processed
    ]

    # Overall similarity score (average of all pairwise)
    pairs = [
        similarity_matrix[i][j]
        for i in range(n) for j in range(i + 1, n)
    ]
    avg_similarity = round(sum(pairs) / len(pairs), 1) if pairs else 0

    return {
        "documents": [{"id": p["id"], "filename": p["filename"]} for p in processed],
        "similarity_matrix": similarity_matrix,
        "vocabulary_overlap_pct": jaccard,
        "common_vocabulary_size": len(common_vocab),
        "average_similarity": avg_similarity,
        "stat_comparison": stat_comparison,
        "sentiment_comparison": sentiment_comparison,
        "dna_heatmap": dna_heatmap,
        "style_comparison": style_comparison,
        "summary": (
            f"Documents share {round(jaccard, 1)}% vocabulary overlap with "
            f"{avg_similarity}% average content similarity."
        ),
    }
