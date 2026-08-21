"""Learning / Adaptive Engine API.

Phase 2 routes are preserved; Phase 3 adds mastery detail, weak concepts,
prerequisites, recommendations, review schedule, history and mistakes.
Every route is scoped to a single resolved user (see core.identity).
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import (
    DEFAULT_DAILY_STUDY_MINUTES,
    DIFFICULTY_WEIGHTS,
    PREREQUISITE_MASTERY_THRESHOLD,
    RECENCY_HALF_LIFE_DAYS,
    STATE_THRESHOLDS,
    WEAK_CONCEPT_THRESHOLD,
)
from app.core.database import get_db
from app.core.identity import resolve_user_id
from app.models.academic import ConceptMastery
from app.services import learning_path as learning_path_service
from app.services.concept_graph import (
    concept_context,
    get_dependents,
    get_prerequisites,
    is_prerequisite_mastered,
    load_mastery_map,
)
from app.services.mastery import apply_quiz_results
from app.services.mistakes import analyze_mistake_patterns, get_mistakes, get_question_history
from app.services.progress import get_progress as get_progress_service
from app.services.recommendations import get_daily_plan, get_next_recommendation, get_recommendations
from app.services.review import get_review_schedule
from app.services.weakness import get_weak_concepts as weak_concepts_service

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
        "concept": concept_context(m.concept_id)["concept"],
        "score": m.mastery_score,
        "mastery": m.mastery_score,
        "state": m.state,
        "status": m.status,
        "attemptCount": m.questions_attempted,
        "questionsAttempted": m.questions_attempted,
        "questionsCorrect": m.questions_correct,
        "questionsIncorrect": m.questions_incorrect,
        "streak": m.streak,
        "lastAttempted": m.last_attempted.isoformat() if m.last_attempted else None,
        "lastCorrectAt": m.last_correct_at.isoformat() if m.last_correct_at else None,
        "nextReviewAt": m.next_review_at.isoformat() if m.next_review_at else None,
        "confidence": m.confidence,
        "updatedAt": m.updated_at.isoformat() if m.updated_at else None,
    }


@router.get("/config")
def adaptive_config():
    """Expose the adaptive thresholds so the UI never hardcodes them."""
    return {
        "difficultyWeights": DIFFICULTY_WEIGHTS,
        "stateThresholds": [{"min": lo, "state": state} for lo, state in STATE_THRESHOLDS],
        "weakConceptThreshold": WEAK_CONCEPT_THRESHOLD,
        "prerequisiteMasteryThreshold": PREREQUISITE_MASTERY_THRESHOLD,
        "recencyHalfLifeDays": RECENCY_HALF_LIFE_DAYS,
        "defaultDailyStudyMinutes": DEFAULT_DAILY_STUDY_MINUTES,
        "masteryLabel": "LexiMind Mastery Score",
    }


@router.get("/mastery/{user_id}")
async def get_mastery(user_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    rows = (await db.execute(select(ConceptMastery).where(ConceptMastery.user_id == uid))).scalars().all()
    return [_mastery_out(m) for m in rows]


@router.get("/mastery/{user_id}/{concept_id}")
async def get_concept_mastery(user_id: str, concept_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    m = (await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == uid, ConceptMastery.concept_id == concept_id)
    )).scalar_one_or_none()
    if not m:
        return {
            "userId": uid, "conceptId": concept_id, "concept": concept_context(concept_id)["concept"],
            "score": 0, "mastery": 0, "state": "NOT_STARTED", "status": "not_started", "attemptCount": 0,
        }
    return _mastery_out(m)


@router.post("/mastery/update")
async def update_mastery(req: MasteryUpdateRequest, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, req.userId)
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
                "difficulty": p.get("difficulty"),
            })
    result = await apply_quiz_results(db, uid, "mastery-update", answers)
    return {"status": "updated", "userId": uid, **result}


@router.get("/learning-path/{user_id}/{subject_id}")
async def get_learning_path(user_id: str, subject_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    return await learning_path_service.get_learning_path(db, uid, subject_id)


@router.post("/learning-path/regenerate")
async def regenerate_learning_path(req: LearningPathRequest, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, req.userId)
    return await learning_path_service.get_learning_path(db, uid, req.subjectId)


@router.post("/quiz-attempt")
async def submit_quiz_attempt(req: QuizAttemptRequest, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, req.userId)
    normalized = []
    for a in req.answers:
        normalized.append({
            "question_id": a.get("questionId") or a.get("question_id"),
            "selected_answer": a.get("userAnswer") or a.get("selected_answer"),
            "correct": a.get("isCorrect") if "isCorrect" in a else a.get("correct"),
            "time_taken": a.get("timeTakenSeconds") or a.get("time_taken"),
            "concept_id": a.get("conceptId") or a.get("concept_id"),
            "difficulty": a.get("difficulty"),
        })
    result = await apply_quiz_results(db, uid, req.quizId, normalized, req.subjectId)
    recommendation = await get_next_recommendation(db, uid, req.subjectId)
    return {**result, "recommendation": recommendation, "status": "recorded"}


@router.get("/weak-concepts/{user_id}")
async def get_weak_concepts(user_id: str, request: Request, subject_id: Optional[str] = None,
                            limit: int = 10, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    weak = await weak_concepts_service(db, uid, limit=limit)
    if subject_id:
        weak = [w for w in weak if not w.get("subjectId") or w["subjectId"] == subject_id]
    return {"userId": uid, "weakConcepts": weak, "empty": not weak}


@router.get("/prerequisites/{concept_id}")
async def prerequisites(concept_id: str, request: Request, user_id: Optional[str] = None,
                        db: AsyncSession = Depends(get_db)):
    payload = {
        "conceptId": concept_id,
        **concept_context(concept_id),
        "prerequisites": [concept_context(c) for c in get_prerequisites(concept_id)],
        "dependents": [concept_context(c) for c in get_dependents(concept_id)],
    }
    if user_id:
        uid = resolve_user_id(request, user_id)
        mastery_map = await load_mastery_map(db, uid)
        payload["readiness"] = is_prerequisite_mastered(mastery_map, concept_id)
    return payload


@router.get("/recommendations/{user_id}")
async def recommendations(user_id: str, request: Request, subject_id: Optional[str] = None,
                          limit: int = 5, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    recs = await get_recommendations(db, uid, subject_id, limit=limit)
    return {"userId": uid, "recommendations": recs, "empty": not recs}


@router.get("/recommendations/{user_id}/next")
async def next_recommendation(user_id: str, request: Request, subject_id: Optional[str] = None,
                              db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    rec = await get_next_recommendation(db, uid, subject_id)
    return {"userId": uid, "recommendation": rec, "empty": rec is None}


@router.get("/recommended/{user_id}")
async def get_recommended(user_id: str, request: Request, subject_id: Optional[str] = None,
                          db: AsyncSession = Depends(get_db)):
    """Phase 2 compatible shape, now backed by the recommendation engine."""
    uid = resolve_user_id(request, user_id)
    recs = await get_recommendations(db, uid, subject_id, limit=5)
    return {
        "userId": uid,
        "recommendedConceptId": recs[0]["conceptId"] if recs else None,
        "reason": recs[0]["reason"] if recs else "No performance history yet.",
        "recommendedConcepts": [{"conceptId": r["conceptId"], "reason": r["reason"], "type": r["type"]} for r in recs],
    }


@router.get("/daily-plan/{user_id}")
async def daily_plan(user_id: str, request: Request, subject_id: Optional[str] = None,
                     study_minutes: int = Query(DEFAULT_DAILY_STUDY_MINUTES, ge=5, le=480),
                     db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    return await get_daily_plan(db, uid, subject_id, study_minutes)


@router.get("/review-schedule/{user_id}")
async def review_schedule(user_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    schedule = await get_review_schedule(db, uid)
    return {
        "userId": uid,
        "schedule": schedule,
        "dueCount": sum(1 for s in schedule if s["due"]),
        "empty": not schedule,
    }


@router.get("/history/{user_id}")
async def question_history(user_id: str, request: Request, concept_id: Optional[str] = None,
                           limit: int = 50, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    items = await get_question_history(db, uid, concept_id, limit)
    return {"userId": uid, "history": items, "empty": not items}


@router.get("/mistakes/{user_id}")
async def mistakes(user_id: str, request: Request, concept_id: Optional[str] = None,
                   limit: int = 50, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    items = await get_mistakes(db, uid, concept_id, limit)
    return {
        "userId": uid,
        "mistakes": items,
        "patterns": analyze_mistake_patterns(items),
        "empty": not items,
    }


@router.get("/progress/{user_id}")
async def get_progress(user_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    return await get_progress_service(db, uid)
