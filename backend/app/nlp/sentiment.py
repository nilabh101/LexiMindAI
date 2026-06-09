"""Sentiment and emotion analysis pipeline."""
from typing import Dict, List, Any
from textblob import TextBlob
from app.nlp.text_processor import extract_sentences, extract_paragraphs


def analyze_sentiment_text(text: str) -> Dict[str, float]:
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {
        "polarity": polarity,
        "subjectivity": subjectivity,
        "label": label,
        "confidence": round(abs(polarity), 4),
    }


def analyze_document_sentiment(text: str) -> Dict[str, Any]:
    doc_sentiment = analyze_sentiment_text(text)

    sentences = extract_sentences(text)
    sentence_sentiments = []
    pos, neg, neu = 0, 0, 0

    for sent in sentences[:200]:  # cap at 200 for performance
        s = analyze_sentiment_text(sent)
        sentence_sentiments.append({"text": sent[:120], **s})
        if s["label"] == "positive":
            pos += 1
        elif s["label"] == "negative":
            neg += 1
        else:
            neu += 1

    total = len(sentence_sentiments) or 1
    distribution = {
        "positive": round(pos / total * 100, 1),
        "negative": round(neg / total * 100, 1),
        "neutral": round(neu / total * 100, 1),
    }

    # Paragraph-level
    paragraphs = extract_paragraphs(text)
    paragraph_sentiments = []
    for i, para in enumerate(paragraphs[:50]):
        s = analyze_sentiment_text(para)
        paragraph_sentiments.append({"index": i, "preview": para[:100], **s})

    # Trend: polarity over sentence index
    trend = [
        {"index": i, "polarity": s["polarity"]}
        for i, s in enumerate(sentence_sentiments)
    ]

    return {
        "document": doc_sentiment,
        "distribution": distribution,
        "sentence_sentiments": sentence_sentiments[:50],
        "paragraph_sentiments": paragraph_sentiments,
        "trend": trend,
        "mixed": pos > 0 and neg > 0,
    }


# NRC-inspired emotion lexicon (subset)
_EMOTION_LEXICON: Dict[str, List[str]] = {
    "joy": ["happy", "joy", "delight", "pleasure", "wonderful", "great", "love", "smile",
            "laugh", "celebrate", "success", "win", "victory", "amazing", "fantastic",
            "excited", "cheerful", "brilliant", "excellent", "glorious"],
    "sadness": ["sad", "grief", "sorrow", "unhappy", "depressed", "cry", "tears", "loss",
                "miss", "lonely", "hopeless", "tragic", "mourn", "regret", "disappoint"],
    "fear": ["fear", "afraid", "scared", "terror", "horror", "panic", "dread", "nervous",
             "anxiety", "worry", "threat", "danger", "risk", "alarm", "frighten"],
    "anger": ["angry", "rage", "furious", "mad", "hatred", "hate", "hostile", "violent",
              "bitter", "resentment", "outrage", "aggression", "irritate", "frustrate"],
    "trust": ["trust", "faith", "believe", "confident", "reliable", "honest", "loyal",
              "respect", "integrity", "genuine", "sincere", "dependable", "credible"],
    "anticipation": ["expect", "hope", "await", "anticipate", "predict", "future", "plan",
                     "intend", "prepare", "goal", "ambition", "dream", "prospect"],
    "surprise": ["surprise", "shock", "unexpected", "astonish", "amaze", "sudden",
                 "startling", "incredible", "unbelievable", "wonder", "discover"],
    "disgust": ["disgust", "hate", "repulse", "revolve", "awful", "terrible", "horrible",
                "nasty", "filthy", "loathe", "despise", "repel", "nauseate"],
}


def analyze_emotions(text: str) -> Dict[str, Any]:
    words = text.lower().split()
    word_set = set(words)
    scores: Dict[str, float] = {}

    for emotion, lexicon in _EMOTION_LEXICON.items():
        hits = sum(1 for w in lexicon if w in word_set)
        # Normalize by lexicon size and total words
        scores[emotion] = round(hits / len(lexicon), 4)

    total = sum(scores.values()) or 1
    normalized = {e: round(v / total, 4) for e, v in scores.items()}
    dominant = max(scores, key=scores.get) if scores else "neutral"

    return {
        "scores": scores,
        "normalized": normalized,
        "dominant_emotion": dominant,
        "radar": [
            {"emotion": e, "value": round(v * 100, 1)}
            for e, v in normalized.items()
        ],
    }
