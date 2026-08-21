"""Quiz API — Phase 3: adds POST /adaptive endpoint."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
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


class AdaptiveQuizRequest(BaseModel):
    user_id: str
    subject_id: str
    chapter_id: Optional[str] = None
    concept_id: Optional[str] = None
    question_count: int = 10
    review_requested: bool = False

    @field_validator("question_count", mode="before")
    @classmethod
    def clamp_count(cls, v):
        return max(1, min(int(v) if v else 10, 30))

    @field_validator("user_id", "subject_id", mode="before")
    @classmethod
    def not_empty(cls, v, info):
        field_name = info.field_name
        if not v or not str(v).strip():
            raise ValueError(f"{field_name} must not be empty")
        if len(str(v)) > 128:
            raise ValueError(f"{field_name} must be ≤ 128 characters")
        return v


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


@router.post("/adaptive")
async def adaptive_quiz(req: AdaptiveQuizRequest, db: AsyncSession = Depends(get_db)):
    """
    Assemble an adaptive quiz tailored to the user's mastery level.

    - mastery < 40  → 60%+ EASY questions
    - mastery 40-70 → 60%+ MEDIUM questions
    - mastery ≥ 70  → 60%+ HARD questions

    Questions attempted in the last 7 days are deprioritised.
    No question appears twice in the same session.
    Works entirely from DB (no LLM required).
    """
    from app.services.adaptive_quiz import assemble_adaptive_quiz
    result = await assemble_adaptive_quiz(
        db=db,
        user_id=req.user_id,
        subject_id=req.subject_id,
        chapter_id=req.chapter_id,
        concept_id=req.concept_id,
        question_count=req.question_count,
        review_requested=req.review_requested,
    )
    return {
        "quiz_id": result.quiz_id,
        "questions": result.questions,
        "question_count": len(result.questions),
        "insufficient_bank": result.insufficient_bank,
        "ai_generated_count": result.ai_generated_count,
        "source_counts": result.source_counts,
        "difficulty_distribution": result.difficulty_distribution,
        "concept_id": result.concept_id,
        "subject_id": result.subject_id,
    }


@router.get("/history")
async def get_quiz_history(
    user_id: str = Query(..., max_length=128),
    db: AsyncSession = Depends(get_db),
):
    """Return question attempt history for a user, enriched with concept + subject context."""
    from sqlalchemy import select
    from app.models.academic import QuestionAttempt, Question, AcademicConcept

    attempts = (await db.execute(
        select(QuestionAttempt)
        .where(QuestionAttempt.user_id == user_id)
        .order_by(QuestionAttempt.created_at.desc())
        .limit(200)
    )).scalars().all()

    if not attempts:
        return {"userId": user_id, "attempts": [], "total": 0}

    # Enrich with question text and concept name
    qids = [a.question_id for a in attempts if a.question_id]
    concept_ids = list({a.concept_id for a in attempts if a.concept_id})

    questions_map: Dict[int, Any] = {}
    if qids:
        from sqlalchemy import select as sel
        q_rows = (await db.execute(sel(Question).where(Question.id.in_(qids)))).scalars().all()
        questions_map = {q.id: q for q in q_rows}

    concept_map: Dict[str, str] = {}
    if concept_ids:
        from app.api.education import CONCEPTS as CURR
        for c in CURR:
            cid = c.get("id") or c.get("slug") or ""
            if cid in concept_ids:
                concept_map[cid] = c.get("name", cid)

    return {
        "userId": user_id,
        "total": len(attempts),
        "attempts": [
            {
                "id": a.id,
                "questionId": a.question_id,
                "questionText": (questions_map.get(a.question_id).question_text
                                 if a.question_id and a.question_id in questions_map else None),
                "conceptId": a.concept_id,
                "conceptName": concept_map.get(a.concept_id, a.concept_id),
                "quizId": a.quiz_id,
                "correct": a.correct,
                "difficulty": a.difficulty,
                "timeTaken": a.time_taken,
                "createdAt": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attempts
        ],
    }
