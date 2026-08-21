"""Question history and mistake analysis (observable performance only)."""
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import Question, QuizAnswer
from app.services.concept_graph import concept_label, load_db_concept_names


async def _hydrate(db: AsyncSession, answers: List[QuizAnswer]) -> List[Dict]:
    question_ids = [a.question_id for a in answers if a.question_id]
    questions: Dict[int, Question] = {}
    if question_ids:
        questions = {
            q.id: q for q in (await db.execute(
                select(Question).where(Question.id.in_(question_ids))
            )).scalars().all()
        }
    names = await load_db_concept_names(db)
    items = []
    for a in answers:
        q = questions.get(a.question_id) if a.question_id else None
        items.append({
            "id": a.id,
            "quizId": a.quiz_id,
            "questionId": a.question_id,
            "question": q.question_text if q else None,
            "conceptId": a.concept_id,
            "concept": concept_label(a.concept_id, names) if a.concept_id else None,
            "selectedAnswer": a.selected_answer,
            "correctAnswer": a.correct_answer or (q.answer if q else None),
            "explanation": q.explanation if q else None,
            "correct": bool(a.correct),
            "difficulty": a.difficulty or (q.difficulty if q else None),
            "timeTaken": a.time_taken,
            "source": q.source if q else None,
            "year": q.year if q else None,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
        })
    return items


async def get_question_history(
    db: AsyncSession,
    user_id: str,
    concept_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    stmt = select(QuizAnswer).where(QuizAnswer.user_id == user_id)
    if concept_id:
        stmt = stmt.where(QuizAnswer.concept_id == concept_id)
    rows = (await db.execute(
        stmt.order_by(QuizAnswer.created_at.desc(), QuizAnswer.id.desc()).limit(limit)
    )).scalars().all()
    return await _hydrate(db, rows)


async def get_mistakes(
    db: AsyncSession,
    user_id: str,
    concept_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    stmt = select(QuizAnswer).where(QuizAnswer.user_id == user_id, QuizAnswer.correct.is_(False))
    if concept_id:
        stmt = stmt.where(QuizAnswer.concept_id == concept_id)
    rows = (await db.execute(
        stmt.order_by(QuizAnswer.created_at.desc(), QuizAnswer.id.desc()).limit(limit)
    )).scalars().all()
    return await _hydrate(db, rows)


def analyze_mistake_patterns(mistakes: List[Dict]) -> List[Dict]:
    """Summarise repeated mistakes. Strictly descriptive, no psychological claims."""
    by_concept: Dict[str, Dict] = {}
    for m in mistakes:
        cid = m.get("conceptId")
        if not cid:
            continue
        bucket = by_concept.setdefault(cid, {
            "conceptId": cid,
            "concept": m.get("concept"),
            "count": 0,
            "difficulties": {},
            "questionIds": set(),
            "repeatedQuestionIds": set(),
        })
        bucket["count"] += 1
        diff = (m.get("difficulty") or "UNKNOWN").upper()
        bucket["difficulties"][diff] = bucket["difficulties"].get(diff, 0) + 1
        qid = m.get("questionId")
        if qid is not None:
            if qid in bucket["questionIds"]:
                bucket["repeatedQuestionIds"].add(qid)
            bucket["questionIds"].add(qid)

    patterns = []
    for bucket in by_concept.values():
        if bucket["count"] < 2:
            continue
        dominant = max(bucket["difficulties"].items(), key=lambda kv: kv[1])
        summary = f"{bucket['count']} incorrect answers on {bucket['concept']}"
        if dominant[0] != "UNKNOWN":
            summary += f", mostly {dominant[0].lower()} questions"
        if bucket["repeatedQuestionIds"]:
            summary += f"; {len(bucket['repeatedQuestionIds'])} question(s) missed more than once"
        patterns.append({
            "conceptId": bucket["conceptId"],
            "concept": bucket["concept"],
            "mistakeCount": bucket["count"],
            "byDifficulty": bucket["difficulties"],
            "repeatedQuestions": sorted(bucket["repeatedQuestionIds"]),
            "summary": summary + ".",
        })
    patterns.sort(key=lambda p: -p["mistakeCount"])
    return patterns
