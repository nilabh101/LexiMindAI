"""Core text processing pipeline — tokenization, lemmatization, frequency analysis."""
import re
import string
from collections import Counter
from typing import List, Dict, Tuple, Any
import math

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data on first use
_NLTK_DOWNLOADED = False

def _ensure_nltk_data():
    global _NLTK_DOWNLOADED
    if _NLTK_DOWNLOADED:
        return
    for pkg in ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger",
                "punkt_tab", "omw-1.4"]:
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass
    _NLTK_DOWNLOADED = True


_ensure_nltk_data()
_lemmatizer = WordNetLemmatizer()
_STOP_WORDS = set(stopwords.words("english"))


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalize line endings."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_sentences(text: str) -> List[str]:
    try:
        return [s.strip() for s in sent_tokenize(text) if s.strip()]
    except Exception:
        return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def extract_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def tokenize(text: str) -> List[str]:
    try:
        return word_tokenize(text)
    except Exception:
        return re.findall(r"\b[a-zA-Z]+\b", text)


def get_clean_tokens(text: str, remove_stopwords: bool = True) -> List[str]:
    """Return lemmatized, lowercased tokens with optional stopword removal."""
    tokens = tokenize(text)
    tokens = [t.lower() for t in tokens if t.isalpha() and len(t) > 1]
    tokens = [_lemmatizer.lemmatize(t) for t in tokens]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in _STOP_WORDS]
    return tokens


def word_frequency(tokens: List[str], top_n: int = 50) -> List[Dict[str, Any]]:
    counter = Counter(tokens)
    total = sum(counter.values())
    return [
        {
            "word": word,
            "count": count,
            "percentage": round((count / total) * 100, 2) if total > 0 else 0.0,
            "rank": i + 1,
        }
        for i, (word, count) in enumerate(counter.most_common(top_n))
    ]


def compute_stats(text: str) -> Dict[str, Any]:
    sentences = extract_sentences(text)
    paragraphs = extract_paragraphs(text)
    all_tokens = tokenize(text)
    words = [t for t in all_tokens if t.isalpha()]
    unique_words = set(w.lower() for w in words)

    word_count = len(words)
    unique_count = len(unique_words)
    char_count = len(text.replace(" ", "").replace("\n", ""))
    sentence_count = len(sentences)
    paragraph_count = len(paragraphs)
    avg_sentence_len = round(word_count / sentence_count, 1) if sentence_count > 0 else 0
    reading_time = round(word_count / 238, 1)  # avg reading speed
    lexical_diversity = round(unique_count / word_count, 4) if word_count > 0 else 0

    # Flesch-Kincaid Grade Level
    syllable_count = sum(_count_syllables(w) for w in words)
    if sentence_count > 0 and word_count > 0:
        fk_grade = round(
            0.39 * (word_count / sentence_count)
            + 11.8 * (syllable_count / word_count)
            - 15.59,
            1,
        )
    else:
        fk_grade = 0.0

    # Vocabulary richness (Yule's K approximation via type-token ratio)
    vocab_richness = round((unique_count / word_count) * 100, 1) if word_count > 0 else 0

    return {
        "word_count": word_count,
        "unique_word_count": unique_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "character_count": char_count,
        "average_sentence_length": avg_sentence_len,
        "reading_time_minutes": reading_time,
        "reading_grade_level": fk_grade,
        "lexical_diversity": lexical_diversity,
        "vocabulary_richness": vocab_richness,
    }


def _count_syllables(word: str) -> int:
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)
