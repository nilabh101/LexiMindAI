"""Question and Quiz generation from document content."""
from typing import Dict, List, Any, Optional
import re
import random
from collections import Counter
from app.nlp.text_processor import extract_sentences, get_clean_tokens


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fill_blank(sentence: str, key_word: str) -> str:
    pattern = re.compile(re.escape(key_word), re.IGNORECASE)
    return pattern.sub("_______", sentence, count=1)


def _extract_definitions(text: str) -> List[Dict[str, str]]:
    """Pull 'X is/means/refers to Y' style definitions from text."""
    pattern = re.compile(
        r'([A-Z][a-zA-Z\s\-]{2,50})\s+(?:is|are|refers to|means|defined as|describes)\s+'
        r'([^.!?\n]{15,250})',
        re.IGNORECASE,
    )
    defs = []
    seen_terms = set()
    for m in pattern.finditer(text):
        term = m.group(1).strip()
        definition = m.group(2).strip().rstrip(".,;")
        if len(term) < 3 or len(term) > 60:
            continue
        if term.lower() in seen_terms:
            continue
        if len(definition) < 10:
            continue
        seen_terms.add(term.lower())
        defs.append({"term": term, "definition": definition})
    return defs[:30]


# ─── study questions (open-ended) ─────────────────────────────────────────────

def generate_questions(text: str) -> Dict[str, Any]:
    sentences = extract_sentences(text)
    tokens = get_clean_tokens(text, remove_stopwords=True)
    freq = Counter(tokens)
    top_words = [w for w, _ in freq.most_common(30)]

    easy_q: List[Dict] = []
    medium_q: List[Dict] = []
    hard_q: List[Dict] = []
    application_q: List[Dict] = []
    critical_q: List[Dict] = []

    for sent in sentences:
        words = sent.split()
        if len(words) < 6:
            continue

        # Easy: one per top keyword
        for kw in top_words[:15]:
            if kw.lower() in sent.lower() and len(easy_q) < 5:
                easy_q.append({
                    "question": f"What is the significance of '{kw}' in this document?",
                    "context": sent[:250],
                    "difficulty": "easy",
                    "type": "factual",
                })
                break

        # Medium: comprehension on longer sentences
        if len(words) >= 12 and len(medium_q) < 5:
            snippet = sent[:120] + ("..." if len(sent) > 120 else "")
            medium_q.append({
                "question": f"Explain the following in your own words: \"{snippet}\"",
                "context": sent[:250],
                "difficulty": "medium",
                "type": "comprehension",
            })

        if len(easy_q) >= 5 and len(medium_q) >= 5:
            break

    hard_templates = [
        "Critically analyze the role of '{topic}' as discussed in the document.",
        "How does the document support or challenge conventional views on '{topic}'?",
        "What evidence does the author provide regarding '{topic}'?",
        "Evaluate the argument about '{topic}' presented in the document.",
        "Compare the document's treatment of '{topic}' with your general knowledge.",
    ]
    for i, word in enumerate(top_words[:5]):
        hard_q.append({
            "question": hard_templates[i % len(hard_templates)].format(topic=word),
            "context": f"Based on document content related to '{word}'",
            "difficulty": "hard",
            "type": "analysis",
        })

    app_templates = [
        "How can the concepts in this document be applied in real-world scenarios?",
        "Design a solution using the principles outlined in this document.",
        "What practical implications does this document have for {field}?",
        "Apply the ideas from this document to solve a current problem in society.",
        "How would you implement the recommendations suggested in this document?",
    ]
    for i, tmpl in enumerate(app_templates):
        application_q.append({
            "question": tmpl.format(field=["industry", "education", "research", "policy-making", "technology"][i]),
            "context": "Based on the entire document",
            "difficulty": "application",
            "type": "application",
        })

    critical_templates = [
        "What assumptions underlie the main argument of this document?",
        "Identify any potential biases present in the document.",
        "What alternative perspectives could challenge the claims made here?",
        "How reliable is the evidence presented? Justify your assessment.",
        "What important questions remain unanswered after reading this document?",
    ]
    for tmpl in critical_templates:
        critical_q.append({
            "question": tmpl,
            "context": "Based on critical reading of the entire document",
            "difficulty": "critical",
            "type": "critical_thinking",
        })

    return {
        "easy": easy_q[:5],
        "medium": medium_q[:5],
        "hard": hard_q[:5],
        "application": application_q[:5],
        "critical": critical_q[:5],
        "total": len(easy_q[:5]) + len(medium_q[:5]) + len(hard_q[:5]) + 5 + 5,
    }


# ─── MCQ quiz ─────────────────────────────────────────────────────────────────

def _build_mcqs_from_text(text: str, target: int, seed: int = None) -> List[Dict]:
    """Generate MCQs from a text block. Used by both single and multi-doc quiz."""
    if seed is not None:
        random.seed(seed)

    sentences = extract_sentences(text)
    tokens = get_clean_tokens(text, remove_stopwords=True)
    freq = Counter(tokens)
    top_words = [w for w, _ in freq.most_common(40)]
    top_set = set(top_words)
    defs = _extract_definitions(text)

    mcqs: List[Dict] = []

    # Strategy 1: Definition-based MCQs (best quality)
    other_defs = [d["definition"] for d in defs]
    for d in defs:
        if len(mcqs) >= target:
            break
        wrong_defs = [x for x in other_defs if x != d["definition"]]
        random.shuffle(wrong_defs)
        distractors = wrong_defs[:3]
        # Pad with generic distractors
        pads = [
            "A concept unrelated to the document's content",
            "A historical term predating modern usage",
            "None of the above definitions apply",
            "An unrelated technical concept",
        ]
        while len(distractors) < 3:
            distractors.append(pads[len(distractors)])

        options = [d["definition"][:120]] + [x[:120] for x in distractors[:3]]
        random.shuffle(options)
        mcqs.append({
            "question": f"What is '{d['term']}'?",
            "options": options,
            "answer": d["definition"][:120],
            "difficulty": "medium",
            "explanation": f"As stated in the document: '{d['term']} is {d['definition'][:120]}'.",
            "topic": d["term"],
        })

    # Strategy 2: Fill-in-the-blank from sentences
    for sent in sentences:
        if len(mcqs) >= target:
            break
        words = sent.split()
        if len(words) < 8 or len(words) > 50:
            continue
        # Find a meaningful keyword in this sentence
        candidates = [
            w for w in words
            if len(w) > 4
            and w.lower() in top_set
            and w.isalpha()
        ]
        if not candidates:
            continue
        answer_word = candidates[0]
        blank_q = _fill_blank(sent, answer_word)
        if "______" not in blank_q:
            continue

        wrong_pool = [w for w in top_words if w.lower() != answer_word.lower() and len(w) > 3]
        random.shuffle(wrong_pool)
        distractors = wrong_pool[:3]
        while len(distractors) < 3:
            distractors.append("none of the above")

        options = [answer_word.lower()] + distractors[:3]
        random.shuffle(options)

        difficulty = "easy" if len(words) < 15 else ("medium" if len(words) < 25 else "hard")
        mcqs.append({
            "question": f"Fill in the blank: \"{blank_q[:200]}\"",
            "options": options,
            "answer": answer_word.lower(),
            "difficulty": difficulty,
            "explanation": f"The correct answer '{answer_word}' fits the context: \"{sent[:150]}\"",
            "topic": answer_word,
        })

    # Strategy 3: Concept identification fallback
    if len(mcqs) < target // 2 and top_words:
        for i in range(min(target - len(mcqs), len(top_words) - 3)):
            correct = top_words[i]
            wrong = [w for w in top_words if w != correct]
            random.shuffle(wrong)
            options = [correct] + wrong[:3]
            random.shuffle(options)
            mcqs.append({
                "question": "Which of the following is a key concept discussed in this document?",
                "options": options,
                "answer": correct,
                "difficulty": "easy",
                "explanation": f"'{correct}' is one of the most frequently discussed concepts in the document.",
                "topic": correct,
            })

    return mcqs[:target]


def generate_quiz(text: str, num_questions: int = 10) -> Dict[str, Any]:
    """Generate a full quiz from a single document."""
    mcqs = _build_mcqs_from_text(text, target=num_questions)

    # True/False
    tokens = get_clean_tokens(text, remove_stopwords=True)
    top_words = [w for w, _ in Counter(tokens).most_common(5)]
    topic = top_words[0] if top_words else "the main subject"

    true_false = [
        {
            "question": f"The document contains discussion about '{topic}'.",
            "answer": True,
            "difficulty": "easy",
            "explanation": f"'{topic}' is one of the most frequently occurring topics in the document.",
        },
        {
            "question": f"The document is written in a highly informal, conversational style.",
            "answer": False,
            "difficulty": "easy",
            "explanation": "The document uses structured language typical of formal writing.",
        },
        {
            "question": f"The document presents multiple perspectives on its main topics.",
            "answer": True,
            "difficulty": "medium",
            "explanation": "Documents typically present ideas from various angles.",
        },
        {
            "question": f"'{top_words[1] if len(top_words) > 1 else 'content'}' is never mentioned in the document.",
            "answer": False,
            "difficulty": "easy",
            "explanation": f"'{top_words[1] if len(top_words) > 1 else 'content'}' appears multiple times in the document.",
        },
        {
            "question": "The document concludes with actionable recommendations.",
            "answer": True,
            "difficulty": "medium",
            "explanation": "The document's concluding sections contain recommendations or takeaways.",
        },
    ]

    return {
        "quiz": mcqs,                   # primary MCQ list (for QuizPage)
        "mcq": mcqs,                    # alias kept for backward compat
        "true_false": true_false,
        "total_questions": len(mcqs),
        "answer_key": {
            "mcq": [{"q": i + 1, "answer": q["answer"]} for i, q in enumerate(mcqs)],
            "true_false": [{"q": i + 1, "answer": q["answer"]} for i, q in enumerate(true_false)],
        },
    }


def generate_quiz_from_multiple(texts_with_names: List[Dict[str, str]], num_questions: int = 20) -> Dict[str, Any]:
    """Generate a combined quiz from multiple documents.

    Args:
        texts_with_names: list of {"name": "...", "text": "..."}
        num_questions: total MCQs to generate across all docs
    """
    n_docs = len(texts_with_names)
    per_doc = max(3, num_questions // n_docs)

    all_mcqs: List[Dict] = []
    doc_contributions = []

    for i, doc in enumerate(texts_with_names):
        text = doc.get("text", "")
        name = doc.get("name", f"Document {i + 1}")
        if not text.strip():
            continue

        doc_mcqs = _build_mcqs_from_text(text, target=per_doc, seed=i * 100)
        # Tag each question with its source document
        for q in doc_mcqs:
            q["source_document"] = name
        all_mcqs.extend(doc_mcqs)
        doc_contributions.append({"document": name, "questions_generated": len(doc_mcqs)})

    # Shuffle so questions are mixed across docs
    random.shuffle(all_mcqs)
    all_mcqs = all_mcqs[:num_questions]

    # Number them
    for i, q in enumerate(all_mcqs):
        q["id"] = i + 1

    return {
        "quiz": all_mcqs,
        "mcq": all_mcqs,
        "total_questions": len(all_mcqs),
        "document_count": n_docs,
        "doc_contributions": doc_contributions,
        "answer_key": {
            "mcq": [{"q": i + 1, "answer": q["answer"]} for i, q in enumerate(all_mcqs)],
        },
    }


# ─── flashcards ───────────────────────────────────────────────────────────────

def generate_flashcards(text: str, num_cards: int = 15) -> Dict[str, Any]:
    sentences = extract_sentences(text)
    tokens = get_clean_tokens(text, remove_stopwords=True)
    top_words = [w for w, _ in Counter(tokens).most_common(40)]
    defs = _extract_definitions(text)

    cards: List[Dict] = []

    # Definition cards first (highest quality)
    for d in defs:
        if len(cards) >= num_cards:
            break
        cards.append({
            "id": len(cards) + 1,
            "front": d["term"],
            "back": d["definition"],
            "type": "definition",
        })

    # Context cards from keywords
    for kw in top_words:
        if len(cards) >= num_cards:
            break
        for sent in sentences:
            if kw.lower() in sent.lower() and len(sent.split()) > 8:
                cards.append({
                    "id": len(cards) + 1,
                    "front": f"What role does '{kw}' play in this document?",
                    "back": sent[:300],
                    "type": "context",
                })
                break

    return {"flashcards": cards[:num_cards], "total_cards": min(len(cards), num_cards)}
