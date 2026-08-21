"""Progress aggregation from persisted attempts — no invented statistics."""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adaptive_config import STATE_MASTERED, WEAK_STATES
from app.models.academic import ConceptMastery, QuizAnswer, QuizSession
from app.services.concept_graph import concept_context, curriculum_concepts


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def compute_streak(days_active: List[datetime], today: Optional[datetime] = None) -> int:
    """Consecutive days (ending today or yesterday) with at least one attempt."""
    if not days_active:
        return 0
    today = (today or datetime.now(timezone.utc)).date()
    dates = sorted({_as_utc(d).date() for d in days_active}, reverse=True)
    if dates[0] not in (today, today - timedelta(days=1)):
        return 0
    streak = 1
    for previous, current in zip(dates, dates[1:]):
        if (previous - current).days == 1:
            streak += 1
        else:
            break
    return streak


async def get_progress(db: AsyncSession, user_id: str) -> Dict:
    rows = list((await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    )).scalars().all())
    answers = list((await db.execute(
        select(QuizAnswer).where(QuizAnswer.user_id == user_id)
        .order_by(QuizAnswer.created_at.asc())
    )).scalars().all())
    sessions = list((await db.execute(
        select(QuizSession).where(QuizSession.user_id == user_id)
        .order_by(QuizSession.completed_at.desc().nullslast()).limit(10)
    )).scalars().all())

    total_answers = len(answers)
    total_correct = sum(1 for a in answers if a.correct)
    accuracy = round((total_correct / total_answers) * 100, 1) if total_answers else 0.0
    pyq_solved = int((await db.execute(
        select(func.count(func.distinct(QuizAnswer.question_id))).where(
            QuizAnswer.user_id == user_id, QuizAnswer.question_id.isnot(None)
        )
    )).scalar() or 0)

    mastery_by_concept = {r.concept_id: r for r in rows}
    by_subject: Dict[str, List[float]] = {}
    for concept in curriculum_concepts():
        row = mastery_by_concept.get(concept["id"])
        by_subject.setdefault(concept["subjectId"], []).append(float(row.mastery_score) if row else 0.0)
    for row in rows:
        if row.concept_id not in {c["id"] for c in curriculum_concepts()} and row.subject_id:
            by_subject.setdefault(row.subject_id, []).append(float(row.mastery_score or 0.0))

    subject_mastery = [
        {"subjectId": sid, "mastery": round(sum(vals) / len(vals), 1) if vals else 0.0}
        for sid, vals in sorted(by_subject.items())
    ]
    attempted_rows = [r for r in rows if (r.questions_attempted or 0) > 0]
    overall = round(sum(r.mastery_score or 0 for r in attempted_rows) / len(attempted_rows), 1) if attempted_rows else 0.0

    study_minutes = round(sum((a.time_taken or 0) for a in answers) / 60.0, 1)

    return {
        "userId": user_id,
        "hasHistory": total_answers > 0,
        "overallMastery": overall,
        "totalConcepts": len(curriculum_concepts()),
        "conceptsStarted": len(attempted_rows),
        "masteredConcepts": sum(1 for r in rows if r.state == STATE_MASTERED),
        "weakConcepts": sum(1 for r in rows if r.state in WEAK_STATES and (r.questions_attempted or 0) > 0),
        "inProgressConcepts": sum(
            1 for r in rows
            if r.state not in WEAK_STATES and r.state != STATE_MASTERED and (r.questions_attempted or 0) > 0
        ),
        "needsReviewConcepts": sum(1 for r in rows if r.state in WEAK_STATES and (r.questions_attempted or 0) > 0),
        "totalQuizAttempts": len(sessions) if len(sessions) < 10 else int((await db.execute(
            select(func.count()).select_from(QuizSession).where(QuizSession.user_id == user_id)
        )).scalar() or 0),
        "questionsAnswered": total_answers,
        "questionsCorrect": total_correct,
        "accuracy": accuracy,
        "pyqsSolved": pyq_solved,
        "totalStudyMinutes": study_minutes,
        "streak": compute_streak([a.created_at for a in answers if a.created_at]),
        "subjectMastery": subject_mastery,
        "concepts": [
            {
                **concept_context(r.concept_id),
                "conceptId": r.concept_id,
                "mastery": round(r.mastery_score or 0.0, 1),
                "state": r.state,
                "status": r.status,
                "attempted": r.questions_attempted or 0,
                "correct": r.questions_correct or 0,
                "incorrect": r.questions_incorrect or 0,
                "streak": r.streak or 0,
                "confidence": r.confidence,
                "lastAttemptedAt": _as_utc(r.last_attempted).isoformat() if r.last_attempted else None,
                "nextReviewAt": _as_utc(r.next_review_at).isoformat() if r.next_review_at else None,
            }
            for r in sorted(rows, key=lambda r: -(r.mastery_score or 0))
        ],
        "recentSessions": [
            {
                "quizId": s.quiz_id,
                "subjectId": s.subject_id,
                "score": s.score,
                "accuracy": s.accuracy,
                "correct": s.correct_count,
                "total": s.total_count,
                "completedAt": _as_utc(s.completed_at).isoformat() if s.completed_at else None,
            }
            for s in sessions
        ],
    }
