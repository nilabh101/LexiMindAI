"""Quiz generation from the real question bank. AI questions are labeled AI_GENERATED."""
from typing import Dict, List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import Question
from app.services.llm import generate_text, provider_status
from app.nlp.question_gen import generate_quiz as nlp_generate_quiz


async def generate_quiz(
    db: AsyncSession,
    subject_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_count: int = 5,
    question_type: Optional[str] = None,
    source_material: Optional[str] = None,
) -> Dict:
    q = select(Question).where(Question.review_status != "REJECTED")
    if subject_id:
        q = q.where(Question.subject_id == subject_id)
    if chapter_id:
        q = q.where(or_(Question.chapter_id == chapter_id, Question.chapter_id.is_(None)))
    if concept_id:
        q = q.where(Question.concept_id == concept_id)
    if difficulty:
        q = q.where(or_(Question.difficulty == difficulty.upper(), Question.difficulty == difficulty.lower()))
    if question_type:
        q = q.where(Question.question_type == question_type.upper())

    result = await db.execute(q.limit(question_count * 3))
    rows = list(result.scalars().all())
    # Prefer authentic sources
    order = {"PYQ": 0, "UPLOADED": 1, "PREMADE": 2, "DEMO": 3, "AI_GENERATED": 4}
    rows.sort(key=lambda r: order.get(r.source, 9))
    picked = rows[:question_count]
    questions = [_serialize_q(r) for r in picked]

    generated = []
    if len(questions) < question_count and source_material:
        need = question_count - len(questions)
        generated = _maybe_generate(source_material, need, concept_id, subject_id)
        questions.extend(generated)

    return {
        "quiz_id": f"quiz-{concept_id or subject_id or 'mixed'}-{len(questions)}",
        "questions": questions,
        "source_counts": _counts(questions),
        "insufficient_bank": len(picked) < question_count,
        "ai_generated_count": len(generated),
    }


def _serialize_q(r: Question) -> Dict:
    return {
        "id": r.id,
        "question": r.question_text,
        "question_text": r.question_text,
        "options": r.options,
        "answer": r.answer,
        "explanation": r.explanation,
        "difficulty": (r.difficulty or "UNKNOWN").lower() if r.difficulty else None,
        "question_type": r.question_type,
        "source": r.source,
        "year": r.year,
        "marks": r.marks,
        "concept_id": r.concept_id,
        "subject_id": r.subject_id,
        "is_demo": bool(r.is_demo),
        "needs_review": bool(r.needs_review),
    }


def _counts(questions: List[Dict]) -> Dict:
    out: Dict[str, int] = {}
    for q in questions:
        src = q.get("source") or "UNKNOWN"
        out[src] = out.get(src, 0) + 1
    return out


def _maybe_generate(source_material: str, need: int, concept_id, subject_id) -> List[Dict]:
    status = provider_status()
    items = []
    if status["configured"]:
        prompt = (
            f"Create {need} practice questions grounded ONLY in the study material below. "
            "If the material is insufficient, say so. Return plain questions numbered 1..n.\n\n"
            f"MATERIAL:\n{source_material[:4000]}"
        )
        result = generate_text(prompt, system="You generate academic practice questions from provided notes only.")
        text = result.get("text") or ""
        for i, line in enumerate(text.split("\n")):
            line = line.strip()
            if len(line) < 12:
                continue
            items.append({
                "id": f"ai-{i}",
                "question": line.lstrip("0123456789.)- "),
                "question_text": line.lstrip("0123456789.)- "),
                "options": None,
                "answer": None,
                "explanation": None,
                "difficulty": None,
                "question_type": "UNKNOWN",
                "source": "AI_GENERATED",
                "year": None,
                "marks": None,
                "concept_id": concept_id,
                "subject_id": subject_id,
                "is_demo": False,
                "needs_review": True,
                "label": "AI-generated from your study material",
            })
            if len(items) >= need:
                break
        return items

    # Local NLP quiz from material — still labeled AI_GENERATED / not PYQ
    try:
        quiz = nlp_generate_quiz(source_material, num_questions=need)
        for i, q in enumerate(quiz.get("quiz") or []):
            items.append({
                "id": f"nlp-{i}",
                "question": q.get("question"),
                "question_text": q.get("question"),
                "options": q.get("options"),
                "answer": q.get("answer"),
                "explanation": q.get("explanation"),
                "difficulty": q.get("difficulty"),
                "question_type": "MCQ",
                "source": "AI_GENERATED",
                "year": None,
                "marks": None,
                "concept_id": concept_id,
                "subject_id": subject_id,
                "is_demo": False,
                "needs_review": True,
                "label": "AI-generated from your study material",
            })
    except Exception:
        pass
    return items[:need]
