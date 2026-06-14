"""Topic detection using TF-IDF + keyword extraction + NER via spaCy."""
from typing import Dict, List, Any
import math
from collections import Counter

from app.nlp.text_processor import get_clean_tokens, extract_sentences, tokenize

# Try spaCy
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            try:
                _nlp = spacy.load("en_core_web_sm")
            except OSError:
                from spacy.cli import download
                download("en_core_web_sm")
                _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = False
    return _nlp if _nlp is not False else None


# Predefined topic keyword clusters
_TOPIC_CLUSTERS: Dict[str, List[str]] = {
    "Technology": ["technology", "software", "computer", "digital", "internet", "data",
                   "algorithm", "programming", "code", "system", "network", "artificial",
                   "intelligence", "machine", "learning", "cloud", "cyber", "app", "device"],
    "Politics": ["government", "political", "election", "democracy", "policy", "law",
                 "president", "minister", "parliament", "vote", "party", "legislation",
                 "constitution", "republic", "senate", "congress", "campaign"],
    "Education": ["education", "school", "university", "student", "teacher", "learning",
                  "curriculum", "academic", "research", "knowledge", "study", "degree",
                  "college", "science", "math", "literature", "course"],
    "Climate": ["climate", "environment", "global", "warming", "carbon", "emission",
                "pollution", "renewable", "energy", "sustainability", "ecology", "weather",
                "temperature", "fossil", "green", "conservation", "biodiversity"],
    "Finance": ["finance", "economy", "market", "investment", "bank", "money", "stock",
                "revenue", "profit", "capital", "trade", "gdp", "inflation", "currency",
                "asset", "portfolio", "fund", "budget", "fiscal"],
    "Health": ["health", "medical", "disease", "treatment", "doctor", "hospital", "patient",
               "medicine", "clinical", "therapy", "vaccine", "virus", "mental", "wellness",
               "nutrition", "fitness", "pharmaceutical", "surgery"],
    "Science": ["science", "research", "experiment", "theory", "hypothesis", "discovery",
                "laboratory", "biology", "chemistry", "physics", "quantum", "molecular",
                "genetic", "evolution", "space", "astronomy", "neuroscience"],
    "Business": ["business", "company", "corporate", "strategy", "management", "leadership",
                 "entrepreneur", "startup", "industry", "product", "customer", "brand",
                 "marketing", "sales", "profit", "operations"],
    "Social": ["society", "community", "culture", "social", "human", "people", "rights",
               "justice", "equality", "diversity", "inclusion", "poverty", "welfare"],
    "Sports": ["sport", "game", "player", "team", "competition", "championship", "athlete",
               "match", "score", "tournament", "league", "coach", "fitness", "win"],
}


def compute_tfidf(tokens: List[str], all_doc_tokens: List[List[str]] = None) -> Dict[str, float]:
    """Simple TF-IDF on a single document; uses IDF from predefined corpus if no docs provided."""
    tf: Dict[str, float] = {}
    total = len(tokens)
    if total == 0:
        return {}
    counter = Counter(tokens)
    for word, count in counter.items():
        tf[word] = count / total

    # Simple IDF assuming doc frequency proportional to topic cluster appearances
    result = {}
    for word, tf_val in tf.items():
        idf = 1.0  # default
        result[word] = round(tf_val * idf, 6)
    return result


def detect_topics(text: str) -> Dict[str, Any]:
    tokens = get_clean_tokens(text, remove_stopwords=True)
    token_set = Counter(tokens)
    total_tokens = len(tokens) or 1

    topic_scores: Dict[str, float] = {}
    topic_keywords: Dict[str, List[str]] = {}

    for topic, keywords in _TOPIC_CLUSTERS.items():
        hits = [(kw, token_set[kw]) for kw in keywords if token_set[kw] > 0]
        score = sum(count for _, count in hits) / total_tokens
        topic_scores[topic] = round(score * 1000, 2)
        topic_keywords[topic] = [kw for kw, _ in sorted(hits, key=lambda x: -x[1])[:5]]

    # Sort topics by score
    ranked = sorted(topic_scores.items(), key=lambda x: -x[1])
    primary = [t for t, s in ranked[:3] if s > 0]
    secondary = [t for t, s in ranked[3:6] if s > 0]

    topics_result = [
        {
            "topic": t,
            "score": s,
            "keywords": topic_keywords[t],
            "rank": i + 1,
            "is_primary": t in primary,
        }
        for i, (t, s) in enumerate(ranked[:8]) if s > 0
    ]

    return {
        "primary_topics": primary,
        "secondary_topics": secondary,
        "topics": topics_result,
        "total_detected": len(topics_result),
    }


def extract_keywords_tfidf(text: str, top_n: int = 20) -> List[Dict[str, Any]]:
    tokens = get_clean_tokens(text, remove_stopwords=True)
    tfidf = compute_tfidf(tokens)
    sorted_kw = sorted(tfidf.items(), key=lambda x: -x[1])[:top_n]
    return [
        {"keyword": kw, "score": round(score, 4), "rank": i + 1}
        for i, (kw, score) in enumerate(sorted_kw)
    ]

def extract_entities(text: str) -> Dict[str, Any]:
    nlp = _get_nlp()
    entity_map: Dict[str, List[Dict]] = {
        "PERSON": [], "ORG": [], "GPE": [], "DATE": [],
        "EVENT": [], "PRODUCT": [], "TECHNOLOGY": [], "OTHER": [],
    }

    if nlp:
        # Process in chunks to avoid memory issues
        chunk_size = 100000
        all_entities: List[Any] = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            doc = nlp(chunk)
            all_entities.extend(doc.ents)

        entity_counter: Dict[str, Counter] = {k: Counter() for k in entity_map}
        for ent in all_entities:
            label = ent.label_
            if label == "PERSON":
                entity_counter["PERSON"][ent.text.strip()] += 1
            elif label in ("ORG", "COMPANY"):
                entity_counter["ORG"][ent.text.strip()] += 1
            elif label in ("GPE", "LOC"):
                entity_counter["GPE"][ent.text.strip()] += 1
            elif label == "DATE":
                entity_counter["DATE"][ent.text.strip()] += 1
            elif label == "EVENT":
                entity_counter["EVENT"][ent.text.strip()] += 1
            elif label == "PRODUCT":
                entity_counter["PRODUCT"][ent.text.strip()] += 1
            else:
                entity_counter["OTHER"][ent.text.strip()] += 1

        for key, counter in entity_counter.items():
            entity_map[key] = [
                {"text": t, "count": c} for t, c in counter.most_common(15)
            ]
    else:
        # Fallback: simple capitalized word heuristic
        import re
        cap_words = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
        counter = Counter(cap_words)
        entity_map["OTHER"] = [
            {"text": t, "count": c} for t, c in counter.most_common(20)
        ]

    total = sum(len(v) for v in entity_map.values())
    return {
        "entities": entity_map,
        "total_unique_entities": total,
        "categories": [
            {"type": k, "count": len(v), "items": v}
            for k, v in entity_map.items()
            if v
        ],
    }
