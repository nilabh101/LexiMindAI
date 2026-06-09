"""Question and Quiz generation from document content."""
from typing import Dict, List, Any
import re
import random
from app.nlp.text_processor import extract_sentences, get_clean_tokens
from collections import Counter


def _fill_blank(sentence: str, key_word: str) -> str:
    pattern = re.compile(re.escape(key_word), re.IGNORECASE)
    return pattern.sub("_______", sentence, count=1)


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

    for sent in sentences[:60]:
        words = sent.split()
        if len(words) < 6:
            continue

        # Easy: factual fill-in-the-blank
        for kw in top_words[:10]:
            if kw.lower() in sent.lower() and len(easy_q) < 5:
                easy_q.append({
                    "question": f"What is the significance of '{kw}' in the given context?",
                    "context": sent,
                    "difficulty": "easy",
                    "type": "factual",
                })
                break

        # Medium: comprehension
        if len(words) >= 10 and len(medium_q) < 5:
            medium_q.append({
                "question": f"What does the following statement imply: '{sent[:100]}...'?" if len(sent) > 100 else f"Explain the meaning of: '{sent}'",
                "context": sent,
                "difficulty": "medium",
                "type": "comprehension",
            })

    # Hard: analysis questions based on top topics
    hard_templates = [
        "Critically analyze the role of {topic} as discussed in the document.",
        "How does the document support or challenge conventional understanding of {topic}?",
        "What evidence does the author provide regarding {topic}?",
        "Evaluate the author's argument about {topic}.",
        "Compare and contrast the document's treatment of {topic} with general knowledge.",
    ]
    for i, word in enumerate(top_words[:5]):
        hard_q.append({
            "question": hard_templates[i % len(hard_templates)].format(topic=word),
            "context": f"Based on the full document content related to '{word}'",
            "difficulty": "hard",
            "type": "analysis",
        })

    # Application
    app_templates = [
        "How can the concepts discussed in this document be applied in real-world scenarios?",
        "Design a solution using the principles outlined in this document.",
        "What practical implications does this document have for {field}?",
        "Apply the ideas from this document to solve a current problem in society.",
        "How would you implement the recommendations suggested in this document?",
    ]
    fields = ["industry", "education", "research", "policy-making", "technology"]
    for i, tmpl in enumerate(app_templates):
        application_q.append({
            "question": tmpl.format(field=fields[i % len(fields)]),
            "context": "Based on the entire document",
            "difficulty": "application",
            "type": "application",
        })

    # Critical thinking
    critical_templates = [
        "What assumptions underlie the main argument of this document?",
        "Identify any logical fallacies or biases present in the document.",
        "What alternative perspectives could challenge the claims made here?",
        "How reliable is the evidence presented? Justify your assessment.",
        "What questions remain unanswered after reading this document?",
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
        "total": len(easy_q[:5]) + len(medium_q[:5]) + len(hard_q[:5]) + len(application_q) + len(critical_q),
    }


def generate_quiz(text: str) -> Dict[str, Any]:
    sentences = extract_sentences(text)
    tokens = get_clean_tokens(text, remove_stopwords=True)
    freq = Counter(tokens)
    top_words = [w for w, _ in freq.most_common(20)]

    mcqs: List[Dict] = []
    true_false: List[Dict] = []
    short_answer: List[Dict] = []
    long_answer: List[Dict] = []

    random.seed(42)

    # MCQs
    for i, sent in enumerate(sentences[:40]):
        words = sent.split()
        if len(words) < 8:
            continue
        # Pick a key word to blank out
        candidates = [w for w in words if len(w) > 4 and w.lower() in top_words]
        if not candidates:
            continue
        answer = candidates[0]
        question_text = _fill_blank(sent, answer)
        # Generate 3 wrong options from top words
        wrong_pool = [w for w in top_words if w != answer.lower() and len(w) > 3]
        wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
        while len(wrong) < 3:
            wrong.append("none of the above")
        options = wrong + [answer.lower()]
        random.shuffle(options)

        difficulty = "easy" if len(words) < 15 else ("medium" if len(words) < 25 else "hard")
        mcqs.append({
            "question": question_text,
            "options": options,
            "answer": answer.lower(),
            "difficulty": difficulty,
            "explanation": f"The correct answer '{answer}' appears in the context: '{sent[:120]}'",
        })
        if len(mcqs) >= 10:
            break

    # True/False
    tf_templates = [
        ("The document primarily discusses {topic}.", True),
        ("The text contains no mention of {topic}.", False),
        ("The author presents a balanced view on {topic}.", True),
        ("This document is written in a highly informal style.", False),
        ("The text mentions multiple perspectives on the subject.", True),
    ]
    for tmpl, expected in tf_templates[:5]:
        topic = top_words[0] if top_words else "the main subject"
        true_false.append({
            "question": tmpl.format(topic=topic),
            "answer": expected,
            "difficulty": "easy",
            "explanation": f"Based on the document's content and structure.",
        })

    # Short answer
    short_templates = [
        "Name three key concepts discussed in this document.",
        "What is the main argument presented by the author?",
        "List two examples provided in the document.",
        "Define the term '{word}' as used in this document.",
        "What conclusion does the document reach?",
    ]
    for tmpl in short_templates:
        word = top_words[1] if len(top_words) > 1 else "the key term"
        short_answer.append({
            "question": tmpl.format(word=word),
            "expected_length": "2-3 sentences",
            "difficulty": "medium",
            "answer_hint": f"Refer to relevant sections discussing {word}.",
        })

    # Long answer
    long_templates = [
        "Write a comprehensive summary of this document in your own words.",
        "Critically evaluate the main argument presented in this document.",
        "Discuss the implications of the ideas presented, with examples.",
        "Compare the document's perspective with at least two alternative viewpoints.",
    ]
    for tmpl in long_templates:
        long_answer.append({
            "question": tmpl,
            "expected_length": "1-2 paragraphs",
            "difficulty": "hard",
            "rubric": ["Content accuracy (40%)", "Analysis depth (30%)", "Language quality (30%)"],
        })

    return {
        "mcq": mcqs,
        "true_false": true_false,
        "short_answer": short_answer,
        "long_answer": long_answer,
        "answer_key": {
            "mcq": [{"q": i + 1, "answer": q["answer"]} for i, q in enumerate(mcqs)],
            "true_false": [{"q": i + 1, "answer": q["answer"]} for i, q in enumerate(true_false)],
        },
        "total_questions": len(mcqs) + len(true_false) + len(short_answer) + len(long_answer),
    }
