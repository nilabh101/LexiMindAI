from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.identity import resolve_user_id
from app.services.adaptive_quiz import build_adaptive_quiz, next_difficulty
from app.services.mastery import apply_quiz_results
from app.services.mistakes import get_question_history
from app.services.quiz_bank import generate_quiz
from app.services.recommendations import get_next_recommendation

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


class GenerateQuizRequest(BaseModel):
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    concept_id: Optional[str] = None
    difficulty: Optional[str] = None
    question_count: int = 5
    question_type: Optional[str] = None
    source_material: Optional[str] = None


class AdaptiveQuizRequest(BaseModel):
    user_id: str
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    concept_id: Optional[str] = None
    question_count: int = 5
    include_recent: bool = False


class QuizCompleteRequest(BaseModel):
    user_id: str
    quiz_id: str
    subject_id: Optional[str] = None
    answers: List[Dict[str, Any]]


class NextDifficultyRequest(BaseModel):
    current_difficulty: Optional[str] = None
    consecutive_correct: int = 0
    consecutive_incorrect: int = 0


@router.post("/generate")
async def generate(req: GenerateQuizRequest, db: AsyncSession = Depends(get_db)):
    return await generate_quiz(
        db,
        subject_id=req.subject_id,
        chapter_id=req.chapter_id,
        concept_id=req.concept_id,
        difficulty=req.difficulty,
        question_count=min(max(req.question_count, 1), 30),
        question_type=req.question_type,
        source_material=req.source_material,
    )


@router.post("/adaptive")
async def adaptive(req: AdaptiveQuizRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Quiz targeted at the user's weak concepts, prerequisites and difficulty band."""
    uid = resolve_user_id(request, req.user_id)
    return await build_adaptive_quiz(
        db,
        user_id=uid,
        subject_id=req.subject_id,
        chapter_id=req.chapter_id,
        concept_id=req.concept_id,
        question_count=min(max(req.question_count, 1), 30),
        include_recent=req.include_recent,
    )


@router.post("/next-difficulty")
def next_difficulty_endpoint(req: NextDifficultyRequest):
    """In-quiz difficulty controller, exposed so the client stays in sync."""
    return {
        "difficulty": next_difficulty(
            req.current_difficulty, req.consecutive_correct, req.consecutive_incorrect
        )
    }


@router.post("/complete")
async def complete(req: QuizCompleteRequest, request: Request, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, req.user_id)
    result = await apply_quiz_results(
        db,
        user_id=uid,
        quiz_id=req.quiz_id,
        answers=req.answers,
        subject_id=req.subject_id,
    )
    result["recommendation"] = await get_next_recommendation(db, uid, req.subject_id)
    return result


@router.get("/history/{user_id}")
async def history(user_id: str, request: Request, concept_id: Optional[str] = None,
                  limit: int = 50, db: AsyncSession = Depends(get_db)):
    uid = resolve_user_id(request, user_id)
    items = await get_question_history(db, uid, concept_id, limit)
    return {"userId": uid, "history": items, "empty": not items}
