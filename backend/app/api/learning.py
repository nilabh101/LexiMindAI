"""Learning / Adaptive Engine API — Phase 2: persisted mastery + deterministic path."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.academic import ConceptMastery, QuizSession, QuizAnswer
from app.services.mastery import apply_quiz_results, build_learning_path
from app.api.education import CONCEPTS, SUBJECTS

router = APIRouter(prefix="/learning", tags=["learning"])


class MasteryUpdateRequest(BaseModel):
    userId: str
    conceptPerformances: List[Dict[str, Any]]


class QuizAttemptRequest(BaseModel):
    userId: str
    quizId: str
    answers: List[Dict[str, Any]]
    subjectId: Optional[str] = None


class LearningPathRequest(BaseModel):
    userId: str
    subjectId: str


def _mastery_out(m: ConceptMastery) -> dict:
    return {
        "userId": m.user_id,
        "conceptId": m.concept_id,
        "score": m.mastery_score,
        "status": m.status,
        "attemptCount": m.questions_attempted,
        "questionsAttempted": m.questions_attempted,
        "questionsCorrect": m.questions_correct,
        "lastAttempted": m.last_attempted.isoformat() if m.last_attempted else None,
        "confidence": m.confidence,
    }


@router.get("/mastery/{user_id}")
async def get_mastery(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ConceptMastery).where(ConceptMastery.user_id == user_id))).scalars().all()
    return [_mastery_out(m) for m in rows]


@router.get("/mastery/{user_id}/{concept_id}")
async def get_concept_mastery(user_id: str, concept_id: str, db: AsyncSession = Depends(get_db)):
    m = (await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id, ConceptMastery.concept_id == concept_id)
    )).scalar_one_or_none()
    if not m:
        return {"userId": user_id, "conceptId": concept_id, "score": 0, "status": "not_started", "attemptCount": 0}
    return _mastery_out(m)


@router.post("/mastery/update")
async def update_mastery(req: MasteryUpdateRequest, db: AsyncSession = Depends(get_db)):
    answers = []
    for p in req.conceptPerformances:
        correct = int(p.get("correct") or 0)
        total = int(p.get("total") or 0)
        for i in range(total):
            answers.append({
                "question_id": 0,
                "selected_answer": None,
                "correct": i < correct,
                "concept_id": p.get("conceptId") or p.get("concept_id"),
            })
    result = await apply_quiz_results(db, req.userId, "mastery-update", answers)
    return {"status": "updated", "userId": req.userId, **result}


@router.get("/learning-path/{user_id}/{subject_id}")
async def get_learning_path(user_id: str, subject_id: str, db: AsyncSession = Depends(get_db)):
    concepts = [c for c in CONCEPTS if c.get("subjectId") == subject_id]
    if not concepts:
        concepts = list(CONCEPTS)
    rows = (await db.execute(select(ConceptMastery).where(ConceptMastery.user_id == user_id))).scalars().all()
    path = build_learning_path(concepts, list(rows))
    return {"userId": user_id, "subjectId": subject_id, **path}


@router.post("/learning-path/regenerate")
async def regenerate_learning_path(req: LearningPathRequest, db: AsyncSession = Depends(get_db)):
    return await get_learning_path(req.userId, req.subjectId, db)


@router.post("/quiz-attempt")
async def submit_quiz_attempt(req: QuizAttemptRequest, db: AsyncSession = Depends(get_db)):
    normalized = []
    for a in req.answers:
        normalized.append({
            "question_id": a.get("questionId") or a.get("question_id"),
            "selected_answer": a.get("userAnswer") or a.get("selected_answer"),
            "correct": a.get("isCorrect") if "isCorrect" in a else a.get("correct"),
            "time_taken": a.get("timeTakenSeconds") or a.get("time_taken"),
            "concept_id": a.get("conceptId") or a.get("concept_id"),
        })
    result = await apply_quiz_results(db, req.userId, req.quizId, normalized, req.subjectId)
    rec = None
    perfs = result.get("concept_performance") or []
    weak = [p for p in perfs if p.get("mastery_score", 100) < 70]
    if weak:
        rec = weak[0].get("conceptId")
    return {**result, "recommendation": rec, "status": "recorded"}


@router.get("/weak-concepts/{user_id}")
async def get_weak_concepts(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ConceptMastery).where(ConceptMastery.user_id == user_id))).scalars().all()
    weak = [m for m in rows if m.status in ("needs_review", "in_progress") and (m.mastery_score or 0) < 60]
    return {"userId": user_id, "weakConcepts": [_mastery_out(m) for m in weak]}


@router.get("/recommended/{user_id}")
async def get_recommended(user_id: str, subject_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    sid = subject_id or (SUBJECTS[0]["id"] if SUBJECTS else "em1-btech")
    path = await get_learning_path(user_id, sid, db)
    recs = path.get("recommendedConcepts") or []
    return {
        "userId": user_id,
        "recommendedConceptId": recs[0]["conceptId"] if recs else path.get("currentConcept"),
        "reason": recs[0]["reason"] if recs else "current concept",
        "recommendedConcepts": recs,
    }


@router.get("/progress/{user_id}")
async def get_progress(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = list((await db.execute(select(ConceptMastery).where(ConceptMastery.user_id == user_id))).scalars().all())
    quiz_count = (await db.execute(select(func.count()).select_from(QuizSession).where(QuizSession.user_id == user_id))).scalar() or 0
    pyq_count = (await db.execute(
        select(func.count()).select_from(QuizAnswer).where(QuizAnswer.user_id == user_id)
    )).scalar() or 0
    by_subject: Dict[str, list] = {}
    for c in CONCEPTS:
        m = next((r for r in rows if r.concept_id == c["id"]), None)
        by_subject.setdefault(c["subjectId"], []).append(m.mastery_score if m else 0)
    subject_mastery = [
        {"subjectId": sid, "mastery": round(sum(vals) / len(vals)) if vals else 0}
        for sid, vals in by_subject.items()
    ]
    return {
        "userId": user_id,
        "totalConcepts": len(rows) or len(CONCEPTS),
        "masteredConcepts": sum(1 for m in rows if m.status == "mastered"),
        "inProgressConcepts": sum(1 for m in rows if m.status == "in_progress"),
        "needsReviewConcepts": sum(1 for m in rows if m.status == "needs_review"),
        "totalQuizAttempts": quiz_count,
        "pyqsSolved": pyq_count,
        "totalStudyMinutes": 0,
        "streak": 0,
        "subjectMastery": subject_mastery,
        "concepts": [_mastery_out(m) for m in rows],
    }
