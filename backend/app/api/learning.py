"""
Learning / Adaptive Engine API — Phase 1 stubs.
These routes define the API contract that Phase 2 will implement.
Phase 1 returns sensible demo data so the frontend works end-to-end.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/learning", tags=["learning"])


# ─── Request / Response schemas ───────────────────────────────────────────────

class MasteryUpdateRequest(BaseModel):
    userId: str
    conceptPerformances: List[Dict[str, Any]]  # [{conceptId, correct, total}]

class QuizAttemptRequest(BaseModel):
    userId: str
    quizId: str
    answers: List[Dict[str, Any]]  # [{questionId, userAnswer, isCorrect}]

class LearningPathRequest(BaseModel):
    userId: str
    subjectId: str


# ─── Demo mastery data (Phase 1) ─────────────────────────────────────────────

DEMO_MASTERY = [
    {"userId": "demo-user-1", "conceptId": "limits-dc",             "score": 85, "status": "mastered",     "attemptCount": 4},
    {"userId": "demo-user-1", "conceptId": "derivatives-dc",        "score": 78, "status": "mastered",     "attemptCount": 3},
    {"userId": "demo-user-1", "conceptId": "partial-derivatives-dc","score": 62, "status": "in_progress",  "attemptCount": 2},
    {"userId": "demo-user-1", "conceptId": "euler-theorem-dc",      "score": 30, "status": "in_progress",  "attemptCount": 1},
    {"userId": "demo-user-1", "conceptId": "total-derivatives-dc",  "score": 0,  "status": "not_started",  "attemptCount": 0},
    {"userId": "demo-user-1", "conceptId": "c-basics",              "score": 92, "status": "mastered",     "attemptCount": 5},
    {"userId": "demo-user-1", "conceptId": "loops-c",               "score": 70, "status": "in_progress",  "attemptCount": 2},
    {"userId": "demo-user-1", "conceptId": "discriminant",          "score": 45, "status": "needs_review", "attemptCount": 2},
]

DEMO_LEARNING_PATH = [
    {"id": "lp-1", "conceptId": "limits-dc",             "order": 1, "status": "mastered",     "mastery": 85, "estimatedMinutes": 30, "isCurrentFocus": False},
    {"id": "lp-2", "conceptId": "derivatives-dc",        "order": 2, "status": "mastered",     "mastery": 78, "estimatedMinutes": 35, "isCurrentFocus": False},
    {"id": "lp-3", "conceptId": "partial-derivatives-dc","order": 3, "status": "in_progress",  "mastery": 62, "estimatedMinutes": 40, "isCurrentFocus": False},
    {"id": "lp-4", "conceptId": "euler-theorem-dc",      "order": 4, "status": "in_progress",  "mastery": 30, "estimatedMinutes": 35, "isCurrentFocus": True},
    {"id": "lp-5", "conceptId": "total-derivatives-dc",  "order": 5, "status": "available",    "mastery": 0,  "estimatedMinutes": 40, "isCurrentFocus": False},
    {"id": "lp-6", "conceptId": "matrix-ops",            "order": 6, "status": "locked",       "mastery": 0,  "estimatedMinutes": 45, "isCurrentFocus": False},
]


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/mastery/{user_id}")
def get_mastery(user_id: str):
    """Return mastery scores for all concepts for a user."""
    return [m for m in DEMO_MASTERY if m["userId"] == user_id]

@router.get("/mastery/{user_id}/{concept_id}")
def get_concept_mastery(user_id: str, concept_id: str):
    m = next((m for m in DEMO_MASTERY if m["userId"] == user_id and m["conceptId"] == concept_id), None)
    if not m:
        return {"userId": user_id, "conceptId": concept_id, "score": 0, "status": "not_started", "attemptCount": 0}
    return m

@router.post("/mastery/update")
def update_mastery(req: MasteryUpdateRequest):
    """
    Phase 1 stub — accepts mastery update and returns a success response.
    Phase 2 will actually persist to DB and recalculate the learning path.
    """
    return {
        "status": "updated",
        "userId": req.userId,
        "conceptsUpdated": len(req.conceptPerformances),
        "note": "Phase 1 stub — mastery will be persisted in Phase 2",
    }

@router.get("/learning-path/{user_id}/{subject_id}")
def get_learning_path(user_id: str, subject_id: str):
    """Return the current learning path for a user + subject."""
    return {
        "userId": user_id,
        "subjectId": subject_id,
        "items": DEMO_LEARNING_PATH,
        "generatedAt": "2025-01-16T00:00:00Z",
    }

@router.post("/learning-path/regenerate")
def regenerate_learning_path(req: LearningPathRequest):
    """
    Phase 1 stub — returns demo path.
    Phase 2 will run the prerequisite graph traversal + mastery weighting.
    """
    return {
        "userId": req.userId,
        "subjectId": req.subjectId,
        "items": DEMO_LEARNING_PATH,
        "note": "Phase 1 stub — real adaptive path generation in Phase 2",
    }

@router.post("/quiz-attempt")
def submit_quiz_attempt(req: QuizAttemptRequest):
    """
    Record a quiz attempt.
    Phase 1 calculates score client-side; this just confirms receipt.
    Phase 2 will persist, update mastery, and return updated learning path.
    """
    correct = sum(1 for a in req.answers if a.get("isCorrect"))
    total = len(req.answers)
    score_pct = round((correct / total) * 100) if total > 0 else 0

    return {
        "status": "recorded",
        "userId": req.userId,
        "quizId": req.quizId,
        "score": score_pct,
        "correct": correct,
        "total": total,
        "recommendation": "euler-theorem-dc" if score_pct < 70 else "total-derivatives-dc",
        "note": "Phase 1 stub — mastery update and path recalculation in Phase 2",
    }

@router.get("/weak-concepts/{user_id}")
def get_weak_concepts(user_id: str):
    """Return concepts that need attention."""
    weak = [m for m in DEMO_MASTERY if m["userId"] == user_id and m["status"] in ("needs_review", "in_progress") and m["score"] < 60]
    return {"userId": user_id, "weakConcepts": weak}

@router.get("/recommended/{user_id}")
def get_recommended(user_id: str):
    """Return the next recommended concept to study."""
    current = next((i for i in DEMO_LEARNING_PATH if i["isCurrentFocus"]), None)
    return {
        "userId": user_id,
        "recommendedConceptId": current["conceptId"] if current else "limits-dc",
        "reason": "Current focus based on learning path",
    }

@router.get("/progress/{user_id}")
def get_progress(user_id: str):
    """Return overall progress statistics."""
    mastery_data = [m for m in DEMO_MASTERY if m["userId"] == user_id]
    return {
        "userId": user_id,
        "totalConcepts": len(mastery_data),
        "masteredConcepts": sum(1 for m in mastery_data if m["status"] == "mastered"),
        "inProgressConcepts": sum(1 for m in mastery_data if m["status"] == "in_progress"),
        "needsReviewConcepts": sum(1 for m in mastery_data if m["status"] == "needs_review"),
        "totalQuizAttempts": 12,
        "pyqsSolved": 8,
        "totalStudyMinutes": 340,
        "streak": 7,
        "subjectMastery": [
            {"subjectId": "em1-btech", "mastery": 55},
            {"subjectId": "programming-btech", "mastery": 81},
        ],
    }
