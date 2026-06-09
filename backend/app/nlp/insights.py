"""AI Insight Generator and Bias Detector."""
from typing import Dict, List, Any


def generate_insights(
    stats: Dict,
    sentiment: Dict,
    topics: Dict,
    style: Dict,
    dna: Dict,
    entities: Dict,
) -> List[Dict[str, str]]:
    insights = []

    # Word count insights
    wc = stats.get("word_count", 0)
    if wc > 5000:
        insights.append({
            "type": "structure",
            "icon": "📄",
            "insight": f"This is an extensive document with {wc:,} words, suggesting in-depth coverage of the subject matter.",
        })
    elif wc > 1000:
        insights.append({
            "type": "structure",
            "icon": "📝",
            "insight": f"The document spans {wc:,} words, indicating moderate depth and structured content.",
        })
    else:
        insights.append({
            "type": "structure",
            "icon": "🗒️",
            "insight": f"This is a concise document with {wc:,} words, likely a brief or summary piece.",
        })

    # Lexical diversity
    ld = stats.get("lexical_diversity", 0)
    if ld > 0.7:
        insights.append({
            "type": "vocabulary",
            "icon": "🔤",
            "insight": "The document demonstrates exceptional vocabulary diversity, suggesting an expert-level author with broad linguistic range.",
        })
    elif ld > 0.4:
        insights.append({
            "type": "vocabulary",
            "icon": "🔤",
            "insight": "The vocabulary diversity is moderate, balancing clarity with variation — typical of professional writing.",
        })
    else:
        insights.append({
            "type": "vocabulary",
            "icon": "🔤",
            "insight": "The document uses highly repetitive terminology, indicating strong thematic focus or a specialized technical domain.",
        })

    # Reading grade
    grade = stats.get("reading_grade_level", 0)
    if grade > 16:
        insights.append({
            "type": "readability",
            "icon": "🎓",
            "insight": f"The reading grade level of {grade} suggests this document targets postgraduate or expert-level readers.",
        })
    elif grade > 12:
        insights.append({
            "type": "readability",
            "icon": "📚",
            "insight": f"At grade level {grade}, this document is suitable for college-educated readers.",
        })
    elif grade > 8:
        insights.append({
            "type": "readability",
            "icon": "📖",
            "insight": f"With a grade level of {grade}, this document is accessible to a general audience.",
        })

    # Sentiment insights
    doc_sent = sentiment.get("document", {})
    polarity = doc_sent.get("polarity", 0)
    subjectivity = doc_sent.get("subjectivity", 0.5)
    if polarity > 0.3:
        insights.append({
            "type": "sentiment",
            "icon": "😊",
            "insight": "The tone remains consistently positive throughout, suggesting an optimistic or promotional writing intent.",
        })
    elif polarity < -0.2:
        insights.append({
            "type": "sentiment",
            "icon": "⚠️",
            "insight": "The document carries a notably negative tone, which may indicate critical analysis, complaint, or cautionary content.",
        })
    else:
        insights.append({
            "type": "sentiment",
            "icon": "⚖️",
            "insight": "The document maintains a neutral-to-balanced tone, characteristic of objective reporting or academic writing.",
        })

    if subjectivity > 0.6:
        insights.append({
            "type": "bias",
            "icon": "💭",
            "insight": "High subjectivity detected — this document leans toward opinion-based or personal narrative writing.",
        })

    # Topic insights
    primary = topics.get("primary_topics", [])
    if primary:
        topic_str = ", ".join(primary[:3])
        insights.append({
            "type": "topic",
            "icon": "🏷️",
            "insight": f"The primary thematic focus of this document centers on: {topic_str}.",
        })

    # Style insights
    primary_style = style.get("primary_style", "")
    if primary_style:
        insights.append({
            "type": "style",
            "icon": "✍️",
            "insight": f"The writing style has been classified as '{primary_style}' — {style.get('description', '')}",
        })

    # Entity insights
    entity_cats = entities.get("categories", [])
    for cat in entity_cats[:3]:
        if cat["count"] > 2:
            top_item = cat["items"][0]["text"] if cat["items"] else ""
            insights.append({
                "type": "entities",
                "icon": "🔍",
                "insight": f"Frequently referenced {cat['type'].lower()} entity: '{top_item}' — appears as a key element in the document.",
            })

    # DNA insights
    dna_scores = dna.get("dna", {})
    dominant = dna.get("dominant_trait", "")
    if dominant:
        insights.append({
            "type": "dna",
            "icon": "🧬",
            "insight": f"The document's dominant characteristic is '{dominant.replace('_', ' ')}' — this defines its overall intellectual fingerprint.",
        })

    return insights[:12]


def analyze_bias(text: str, sentiment: Dict) -> Dict[str, Any]:
    from app.nlp.text_processor import extract_sentences, tokenize
    from collections import Counter

    sentences = extract_sentences(text)
    pos_count, neg_count, neu_count = 0, 0, 0

    from textblob import TextBlob
    polarities = []
    for sent in sentences[:100]:
        p = TextBlob(sent).sentiment.polarity
        polarities.append(p)
        if p > 0.1:
            pos_count += 1
        elif p < -0.1:
            neg_count += 1
        else:
            neu_count += 1

    total = len(sentences[:100]) or 1
    doc_sent = sentiment.get("document", {})
    subjectivity = doc_sent.get("subjectivity", 0.5)
    objectivity = 1.0 - subjectivity

    # Opinion intensity
    opinion_words = {"believe", "think", "feel", "opinion", "view", "consider", "argue",
                     "suggest", "claim", "assert", "contend", "maintain"}
    tokens = [t.lower() for t in tokenize(text) if t.isalpha()]
    opinion_hits = sum(1 for t in tokens if t in opinion_words)
    opinion_intensity = round(min(1.0, opinion_hits / max(len(tokens), 1) * 100), 3)

    framing = "neutral"
    if pos_count / total > 0.5:
        framing = "positive"
    elif neg_count / total > 0.3:
        framing = "negative"

    bias_level = "low"
    if subjectivity > 0.6:
        bias_level = "high"
    elif subjectivity > 0.4:
        bias_level = "medium"

    return {
        "framing": framing,
        "bias_level": bias_level,
        "subjectivity_score": round(subjectivity, 3),
        "objectivity_score": round(objectivity, 3),
        "opinion_intensity": opinion_intensity,
        "positive_framing_pct": round(pos_count / total * 100, 1),
        "negative_framing_pct": round(neg_count / total * 100, 1),
        "neutral_framing_pct": round(neu_count / total * 100, 1),
        "explanation": (
            f"The document exhibits {bias_level} bias with {framing} framing. "
            f"Subjectivity score of {round(subjectivity * 100, 1)}% indicates "
            f"{'heavily opinion-based' if subjectivity > 0.6 else 'moderately subjective' if subjectivity > 0.4 else 'mostly objective'} content."
        ),
    }
