"""Learning / Adaptive Engine API — Phase 3: full adaptive engine connected."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.academic import (
    ConceptMastery, QuizSession, QuizAnswer, QuestionAttempt, ReviewSchedule
)
from app.services.mastery import apply_quiz_results, build_learning_path
from app.api.education import CONCEPTS, SUBJECTS

router = APIRouter(prefix="/learning", tags=["learning"])


# ── Pydantic schemas ───────────────────────────────────────────────────────────

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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mastery_out(m: ConceptMastery) -> dict:
    return {
        "userId": m.user_id,
        "conceptId": m.concept_id,
        "score": m.mastery_score,
        "mastery_score": m.mastery_score,
        "state": m.state or "NOT_STARTED",
        "status": m.status,
        "attemptCount": m.questions_attempted,
        "questionsAttempted": m.questions_attempted,
        "questionsCorrect": m.questions_correct,
        "questionsIncorrect": getattr(m, "questions_incorrect", 0) or 0,
        "streak": getattr(m, "streak", 0) or 0,
        "lastAttempted": m.last_attempted.isoformat() if m.last_attempted else None,
        "lastCorrectAt": (getattr(m, "last_correct_at", None) or None) and
                         m.last_correct_at.isoformat(),
        "nextReviewAt": (getattr(m, "next_review_at", None) or None) and
                        m.next_review_at.isoformat(),
        "confidence": m.confidence,
    }


# ── Mastery endpoints ──────────────────────────────────────────────────────────

@router.get("/mastery/{user_id}")
async def get_mastery(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    )).scalars().all()
    return [_mastery_out(m) for m in rows]


@router.get("/mastery/{user_id}/{concept_id}")
async def get_concept_mastery(user_id: str, concept_id: str, db: AsyncSession = Depends(get_db)):
    m = (await db.execute(
        select(ConceptMastery).where(
            ConceptMastery.user_id == user_id,
            ConceptMastery.concept_id == concept_id,
        )
    )).scalar_one_or_none()
    if not m:
        return {
            "userId": user_id, "conceptId": concept_id,
            "score": 0, "mastery_score": 0, "state": "NOT_STARTED",
            "status": "not_started", "attemptCount": 0,
        }
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


# ── Learning path endpoint ─────────────────────────────────────────────────────

@router.get("/learning-path/{user_id}/{subject_id}")
async def get_learning_path(user_id: str, subject_id: str, db: AsyncSession = Depends(get_db)):
    from app.services.review_scheduler import get_overdue_reviews
    from app.services.adaptive_mastery import WEAK_MASTERY_THRESHOLD

    concepts = [c for c in CONCEPTS if c.get("subjectId") == subject_id]
    if not concepts:
        concepts = list(CONCEPTS)

    rows = (await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    )).scalars().all()

    overdue_ids = {r["concept_id"] for r in await get_overdue_reviews(db, user_id)}
    mastery_map = {m.concept_id: m for m in rows}

    now = datetime.now(timezone.utc)
    path_items = []
    completed_concepts = []
    weak_concepts = []
    recommended_concepts = []
    current_concept = None

    for i, c in enumerate(concepts):
        cid = c.get("id") or c.get("slug") or ""
        m = mastery_map.get(cid)
        score = (m.mastery_score or 0.0) if m else 0.0
        state = (m.state or "NOT_STARTED") if m else "NOT_STARTED"

        # Phase 3 status precedence
        if cid in overdue_ids and score < 85:
            lp_status = "needs_review"
        elif score >= 85:
            lp_status = "mastered"
        else:
            # Check prerequisites
            from app.services.prerequisite_graph import get_prerequisites
            prereqs = get_prerequisites(cid)
            prereq_weak = any(
                (mastery_map.get(p).mastery_score if mastery_map.get(p) else 0) < 60
                for p in prereqs
            ) if prereqs else False

            if prereq_weak and i > 0:
                lp_status = "locked"
            elif score > 0:
                lp_status = "in_progress"
            else:
                lp_status = "available"

        is_current = (lp_status in ("available", "in_progress") and current_concept is None)
        if is_current:
            current_concept = cid

        # Classify
        if lp_status == "mastered":
            completed_concepts.append(cid)
        if 0 < score < WEAK_MASTERY_THRESHOLD:
            weak_concepts.append(cid)
        if lp_status in ("available",):
            recommended_concepts.append(cid)

        path_items.append({
            "id": cid,
            "conceptId": cid,
            "status": lp_status,
            "isCurrentFocus": is_current,
            "mastery": round(score),
            "estimatedMinutes": c.get("estimatedMinutes", 20),
            "reason": _path_reason(lp_status, score),
        })

    return {
        "userId": user_id,
        "subjectId": subject_id,
        "items": path_items,
        "currentConcept": current_concept,
        "completedConcepts": completed_concepts,
        "weakConcepts": weak_concepts,
        "recommendedConcepts": [
            {"conceptId": cid, "reason": "Next available concept"}
            for cid in recommended_concepts[:3]
        ],
    }


def _path_reason(status: str, score: float) -> str:
    reasons = {
        "mastered": "Mastery ≥ 85%. Well done!",
        "needs_review": "Review scheduled. Keep it fresh.",
        "in_progress": f"Current mastery: {round(score)}%.",
        "available": "Ready to start.",
        "locked": "Complete prerequisites first.",
    }
    return reasons.get(status, "")


@router.post("/learning-path/regenerate")
async def regenerate_learning_path(req: LearningPathRequest, db: AsyncSession = Depends(get_db)):
    return await get_learning_path(req.userId, req.subjectId, db)


# ── Quiz attempt (Phase 3: uses update_concept_mastery + schedule_review) ──────

@router.post("/quiz-attempt")
async def submit_quiz_attempt(req: QuizAttemptRequest, db: AsyncSession = Depends(get_db)):
    from app.services.adaptive_mastery import update_concept_mastery, get_mastery_state, MasteryState
    from app.services.review_scheduler import schedule_review, apply_review_result

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

    # Phase 3: update mastery per concept via adaptive engine
    concept_mastery_before: Dict[str, float] = {}
    for a in normalized:
        cid = a.get("concept_id")
        if not cid:
            continue
        m = (await db.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == req.userId,
                ConceptMastery.concept_id == cid,
            )
        )).scalar_one_or_none()
        if cid not in concept_mastery_before:
            concept_mastery_before[cid] = m.mastery_score if m else 0.0

        try:
            qid_int = int(a["question_id"]) if a.get("question_id") not in (None, 0, "") else None
        except (TypeError, ValueError):
            qid_int = None

        await update_concept_mastery(
            db=db,
            user_id=req.userId,
            concept_id=cid,
            is_correct=bool(a.get("correct")),
            difficulty=a.get("difficulty"),
            time_taken=a.get("time_taken"),
            quiz_id=req.quizId,
            question_id=qid_int,
        )

    # Also update via legacy apply_quiz_results for QuizSession + QuizAnswer records
    result = await apply_quiz_results(db, req.userId, req.quizId, normalized, req.subjectId)

    # Schedule reviews for newly PROFICIENT/MASTERED concepts
    for cid, before_score in concept_mastery_before.items():
        m = (await db.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == req.userId,
                ConceptMastery.concept_id == cid,
            )
        )).scalar_one_or_none()
        if m:
            after_score = m.mastery_score or 0.0
            await schedule_review(db, req.userId, cid, m.state or "NOT_STARTED")
            await apply_review_result(db, req.userId, cid, before_score, after_score)

    # Generate recommendation
    from app.services.recommendation_engine import get_next_recommendation
    rec = await get_next_recommendation(db, req.userId, req.subjectId)
    rec_dict = None
    if rec:
        rec_dict = {
            "conceptId": rec.concept_id,
            "conceptName": rec.concept_name,
            "reason": rec.reason,
            "type": rec.type.value,
            "estimatedMinutes": rec.estimated_minutes,
            "priority": rec.priority,
        }

    return {**result, "recommendation": rec_dict, "status": "recorded"}


# ── Weak concepts ──────────────────────────────────────────────────────────────

@router.get("/weak-concepts/{user_id}")
async def get_weak_concepts_route(user_id: str, db: AsyncSession = Depends(get_db)):
    from app.services.adaptive_mastery import get_weak_concepts
    weak = await get_weak_concepts(db, user_id)
    return {
        "userId": user_id,
        "weakConcepts": [
            {
                "conceptId": w.concept_id,
                "conceptName": w.concept_name,
                "subjectId": w.subject_id,
                "chapterId": w.chapter_id,
                "masteryScore": w.mastery_score,
                "state": w.state,
                "reason": w.reason,
            }
            for w in weak
        ],
    }


# ── Recommendation ─────────────────────────────────────────────────────────────

@router.get("/recommended/{user_id}")
async def get_recommended(
    user_id: str,
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.services.recommendation_engine import get_next_recommendation
    rec = await get_next_recommendation(db, user_id, subject_id)
    if not rec:
        return {"userId": user_id, "recommendation": None}
    return {
        "userId": user_id,
        "recommendedConceptId": rec.concept_id,
        "recommendation": {
            "conceptId": rec.concept_id,
            "conceptName": rec.concept_name,
            "reason": rec.reason,
            "type": rec.type.value,
            "estimatedMinutes": rec.estimated_minutes,
            "priority": rec.priority,
        },
    }


# ── Review schedule ────────────────────────────────────────────────────────────

@router.get("/review-schedule")
async def get_review_schedule(
    user_id: str = Query(..., max_length=128),
    db: AsyncSession = Depends(get_db),
):
    from app.services.review_scheduler import get_overdue_reviews
    overdue = await get_overdue_reviews(db, user_id)
    # Enrich with concept names
    from app.api.education import CONCEPTS as CURR
    for r in overdue:
        c = next((x for x in CURR if (x.get("id") or x.get("slug")) == r["concept_id"]), None)
        r["conceptName"] = c.get("name") if c else r["concept_id"]
    return {"userId": user_id, "overdueReviews": overdue}


# ── Mistakes ───────────────────────────────────────────────────────────────────

@router.get("/mistakes")
async def get_mistakes(
    user_id: str = Query(..., max_length=128),
    concept_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.models.academic import Question

    stmt = (
        select(QuestionAttempt)
        .where(QuestionAttempt.user_id == user_id, QuestionAttempt.correct == False)
        .order_by(QuestionAttempt.created_at.desc())
        .limit(100)
    )
    if concept_id:
        stmt = stmt.where(QuestionAttempt.concept_id == concept_id)

    attempts = (await db.execute(stmt)).scalars().all()

    # Enrich with question text
    qids = [a.question_id for a in attempts if a.question_id]
    questions: Dict[int, Any] = {}
    if qids:
        q_rows = (await db.execute(select(Question).where(Question.id.in_(qids)))).scalars().all()
        questions = {q.id: q for q in q_rows}

    # Compute pattern summaries per concept
    from collections import Counter, defaultdict
    mistakes_by_concept: Dict[str, list] = defaultdict(list)
    for a in attempts:
        if a.concept_id:
            mistakes_by_concept[a.concept_id].append(a)

    pattern_summaries: Dict[str, str] = {}
    for cid, cattempts in mistakes_by_concept.items():
        if len(cattempts) >= 3:
            diff_counter = Counter(a.difficulty for a in cattempts if a.difficulty)
            dominant_diff = diff_counter.most_common(1)[0][0] if diff_counter else "unknown"
            ans_counter = Counter(a.selected_answer for a in cattempts if a.selected_answer)
            common_wrong = ans_counter.most_common(1)[0][0] if ans_counter else "N/A"
            pattern_summaries[cid] = (
                f"Repeated incorrect answers on {dominant_diff.upper()} questions "
                f"({len(cattempts)} mistakes). Most frequent wrong answer: '{common_wrong[:50]}'."
            )[:300]

    result = []
    for a in attempts:
        q = questions.get(a.question_id) if a.question_id else None
        result.append({
            "id": a.id,
            "question_id": a.question_id,
            "concept_id": a.concept_id,
            "question_text": q.question_text if q else None,
            "selected_answer": a.selected_answer,
            "correct_answer": q.answer if q else None,
            "explanation": q.explanation if q else None,
            "explanation_source": "SOURCE" if (q and q.explanation) else None,
            "difficulty": a.difficulty,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "pattern_summary": pattern_summaries.get(a.concept_id),
        })

    return {"userId": user_id, "mistakes": result, "total": len(result)}


# ── Progress ───────────────────────────────────────────────────────────────────

@router.get("/progress/{user_id}")
async def get_progress(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = list((await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    )).scalars().all())

    quiz_count = (await db.execute(
        select(func.count()).select_from(QuizSession).where(QuizSession.user_id == user_id)
    )).scalar() or 0

    total_answered = (await db.execute(
        select(func.count()).select_from(QuizAnswer).where(QuizAnswer.user_id == user_id)
    )).scalar() or 0

    total_correct = (await db.execute(
        select(func.count()).select_from(QuizAnswer).where(
            QuizAnswer.user_id == user_id, QuizAnswer.correct == True
        )
    )).scalar() or 0

    accuracy = round((total_correct / total_answered) * 100, 1) if total_answered else 0.0

    # Subject mastery breakdown
    by_subject: Dict[str, list] = {}
    for c in CONCEPTS:
        m = next((r for r in rows if r.concept_id == c.get("id") or r.concept_id == c.get("slug")), None)
        by_subject.setdefault(c["subjectId"], []).append(m.mastery_score if m else 0)

    subject_mastery = [
        {"subjectId": sid, "mastery": round(sum(vals) / len(vals))}
        for sid, vals in by_subject.items()
    ]

    # Recent quiz sessions (last 5)
    recent_sessions = (await db.execute(
        select(QuizSession)
        .where(QuizSession.user_id == user_id)
        .order_by(QuizSession.completed_at.desc())
        .limit(5)
    )).scalars().all()

    return {
        "userId": user_id,
        "totalConcepts": len(CONCEPTS),
        "masteredConcepts": sum(1 for m in rows if (m.state or m.status) in ("MASTERED", "mastered")),
        "inProgressConcepts": sum(1 for m in rows if (m.state or m.status) in ("DEVELOPING", "in_progress")),
        "needsReviewConcepts": sum(1 for m in rows if (m.state or m.status) in ("VERY_WEAK", "WEAK", "needs_review")),
        "totalQuizAttempts": quiz_count,
        "totalQuestionsAnswered": total_answered,
        "overallAccuracy": accuracy,
        "pyqsSolved": (await db.execute(
            select(func.count()).select_from(QuizAnswer).where(QuizAnswer.user_id == user_id)
        )).scalar() or 0,
        "totalStudyMinutes": 0,
        "studyStreakDays": 0,
        "streak": 0,
        "subjectMastery": subject_mastery,
        "concepts": [_mastery_out(m) for m in rows],
        "recentPerformance": [
            {
                "quizId": s.quiz_id,
                "date": s.completed_at.isoformat() if s.completed_at else None,
                "subjectId": s.subject_id,
                "score": s.score,
                "accuracy": s.accuracy,
                "correctCount": s.correct_count,
                "totalCount": s.total_count,
            }
            for s in recent_sessions
        ],
    }


# ── Daily plan ─────────────────────────────────────────────────────────────────

@router.get("/daily-plan/{user_id}")
async def get_daily_plan(
    user_id: str,
    study_goal_minutes: int = Query(default=30, ge=10, le=120),
    db: AsyncSession = Depends(get_db),
):
    from app.services.study_plan import build_daily_plan
    activities = await build_daily_plan(db, user_id, study_goal_minutes)
    return {
        "userId": user_id,
        "studyGoalMinutes": study_goal_minutes,
        "activities": [
            {
                "type": a.type,
                "conceptId": a.concept_id,
                "conceptName": a.concept_name,
                "durationMinutes": a.duration_minutes,
                "reason": a.reason,
            }
            for a in activities
        ],
    }
