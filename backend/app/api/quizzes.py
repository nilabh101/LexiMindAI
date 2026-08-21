from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.quiz_bank import generate_quiz
from app.services.mastery import apply_quiz_results

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


class GenerateQuizRequest(BaseModel):
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    concept_id: Optional[str] = None
    difficulty: Optional[str] = None
    question_count: int = 5
    question_type: Optional[str] = None
    source_material: Optional[str] = None


class QuizCompleteRequest(BaseModel):
    user_id: str
    quiz_id: str
    subject_id: Optional[str] = None
    answers: List[Dict[str, Any]]


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


@router.post("/complete")
async def complete(req: QuizCompleteRequest, db: AsyncSession = Depends(get_db)):
    return await apply_quiz_results(
        db,
        user_id=req.user_id,
        quiz_id=req.quiz_id,
        answers=req.answers,
        subject_id=req.subject_id,
    )
