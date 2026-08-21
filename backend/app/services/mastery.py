"""Simple transparent mastery: weighted accuracy. Easy to replace later."""
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import ConceptMastery, QuizAnswer, QuizSession


def compute_mastery(correct: int, attempted: int) -> Dict:
    if attempted <= 0:
        return {
            "mastery_score": 0.0,
            "confidence": 0.0,
            "status": "not_started",
        }
    accuracy = correct / attempted
    # Shrinkage toward 0.5 with few attempts (transparent, not ML)
    weight = min(1.0, attempted / 8)
    mastery = (weight * accuracy + (1 - weight) * 0.5) * 100
    confidence = round(min(0.95, 0.2 + 0.1 * attempted), 2)
    if mastery >= 80:
        status = "mastered"
    elif mastery < 40 and attempted >= 2:
        status = "needs_review"
    else:
        status = "in_progress"
    return {
        "mastery_score": round(mastery, 1),
        "confidence": confidence,
        "status": status,
        "accuracy": round(accuracy * 100, 1),
    }


async def apply_quiz_results(
    db: AsyncSession,
    user_id: str,
    quiz_id: str,
    answers: List[Dict],
    subject_id: str = None,
) -> Dict:
    correct_count = 0
    by_concept: Dict[str, Dict[str, int]] = {}
    now = datetime.now(timezone.utc)

    for a in answers:
        qid = a.get("question_id")
        selected = a.get("selected_answer")
        is_correct = bool(a.get("correct") or a.get("isCorrect"))
        concept_id = a.get("concept_id")
        time_taken = a.get("time_taken") or a.get("timeTaken")
        if is_correct:
            correct_count += 1
        qid_int = None
        try:
            if qid not in (None, "", 0, "0"):
                qid_int = int(qid)
        except (TypeError, ValueError):
            qid_int = None
        db.add(QuizAnswer(
            user_id=user_id,
            quiz_id=quiz_id,
            question_id=qid_int,
            selected_answer=None if selected is None else str(selected),
            correct=is_correct,
            time_taken=float(time_taken) if time_taken is not None else None,
            concept_id=concept_id,
        ))
        if concept_id:
            bucket = by_concept.setdefault(concept_id, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if is_correct:
                bucket["correct"] += 1

    total = len(answers)
    accuracy = round((correct_count / total) * 100, 1) if total else 0.0
    session = QuizSession(
        quiz_id=quiz_id,
        user_id=user_id,
        subject_id=subject_id,
        score=accuracy,
        accuracy=accuracy,
        correct_count=correct_count,
        total_count=total,
        completed_at=now,
        question_ids=[a.get("question_id") for a in answers],
    )
    db.add(session)

    performances = []
    for concept_id, stats in by_concept.items():
        result = await db.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_id == concept_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            row = ConceptMastery(user_id=user_id, concept_id=concept_id)
            db.add(row)
        row.questions_attempted = (row.questions_attempted or 0) + stats["total"]
        row.questions_correct = (row.questions_correct or 0) + stats["correct"]
        row.last_attempted = now
        computed = compute_mastery(row.questions_correct, row.questions_attempted)
        row.mastery_score = computed["mastery_score"]
        row.confidence = computed["confidence"]
        row.status = computed["status"]
        performances.append({"conceptId": concept_id, **computed, **stats})

    await db.flush()
    return {
        "quiz_id": quiz_id,
        "user_id": user_id,
        "score": accuracy,
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total,
        "concept_performance": performances,
    }


def build_learning_path(concepts: List[Dict], mastery_rows: List[ConceptMastery]) -> Dict:
    mastery_map = {m.concept_id: m for m in mastery_rows}
    items = []
    weak = []
    completed = []
    current = None
    for i, c in enumerate(concepts):
        cid = c.get("id") or c.get("slug")
        m = mastery_map.get(cid)
        score = m.mastery_score if m else 0
        status = m.status if m else "not_started"
        prereqs = c.get("prerequisites") or []
        prereq_weak = False
        for p in prereqs:
            pm = mastery_map.get(p)
            if not pm or (pm.mastery_score or 0) < 60:
                prereq_weak = True
                weak.append(p)
                break
        lp_status = "available"
        if status == "mastered":
            lp_status = "mastered"
            completed.append(cid)
        elif prereq_weak and i > 0:
            lp_status = "locked"
        elif status in {"in_progress", "needs_review"}:
            lp_status = status
        elif score == 0:
            lp_status = "available" if i == 0 or not prereq_weak else "locked"
        item = {
            "id": f"lp-{i+1}",
            "conceptId": cid,
            "order": i + 1,
            "status": lp_status if lp_status != "not_started" else "available",
            "mastery": score,
            "estimatedMinutes": c.get("estimatedMinutes") or 30,
            "isCurrentFocus": False,
        }
        items.append(item)

    # Current = first non-mastered unlocked; prefer weak prereq
    for item in items:
        if item["status"] in {"needs_review", "in_progress"}:
            current = item
            break
    if current is None:
        for item in items:
            if item["status"] in {"available"}:
                current = item
                break
    if current:
        current["isCurrentFocus"] = True

    recommended = []
    if weak:
        recommended.append({"conceptId": weak[0], "reason": "weak prerequisite"})
    if current:
        recommended.append({"conceptId": current["conceptId"], "reason": "current concept"})
        nxt = next((it for it in items if it["order"] == current["order"] + 1), None)
        if nxt:
            recommended.append({"conceptId": nxt["conceptId"], "reason": "next prerequisite-dependent concept"})

    return {
        "items": items,
        "currentConcept": current["conceptId"] if current else None,
        "completedConcepts": completed,
        "weakConcepts": list(dict.fromkeys(weak)),
        "recommendedConcepts": recommended,
    }
