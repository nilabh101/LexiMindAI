"""Tutor personalization: learner context and grounded tutor actions.

Everything here comes from stored performance and stored academic material —
the tutor never claims a student is struggling unless attempts say so, and
never cites a source that does not exist.
"""
from typing import Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import (
    AcademicNote, ConceptMastery, Question, QuestionConcept, QuizAnswer,
)
from app.services.concept_graph import concept_context, concept_label
from app.services.mistakes import analyze_mistake_patterns, get_mistakes
from app.services.ownership import exclude_foreign
from app.services.weakness import get_weak_concepts

TUTOR_ACTIONS = [
    "EXPLAIN", "SIMPLIFY", "EXAMPLE", "HINT", "TEST_ME", "SIMILAR_QUESTION", "EXPLAIN_MISTAKE",
]

# Legacy short action names used by the Phase 2 UI.
_ACTION_ALIASES = {
    "explain": "EXPLAIN",
    "simplify": "SIMPLIFY",
    "example": "EXAMPLE",
    "hint": "HINT",
    "test": "TEST_ME",
    "test_me": "TEST_ME",
    "similar": "SIMILAR_QUESTION",
    "similar_question": "SIMILAR_QUESTION",
    "mistake": "EXPLAIN_MISTAKE",
    "explain_mistake": "EXPLAIN_MISTAKE",
}


def normalize_action(action: Optional[str]) -> Optional[str]:
    if not action:
        return None
    key = action.strip().lower()
    return _ACTION_ALIASES.get(key, action.strip().upper() if action.strip().upper() in TUTOR_ACTIONS else None)


async def build_student_context(
    db: AsyncSession,
    user_id: Optional[str],
    subject_id: Optional[str] = None,
    concept_id: Optional[str] = None,
) -> Dict:
    """Mastery, weaknesses and recent mistakes for the tutor prompt."""
    if not user_id:
        return {"hasHistory": False}

    mastery_rows = (await db.execute(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)
    )).scalars().all()
    weak = await get_weak_concepts(db, user_id, limit=5)
    mistakes = await get_mistakes(db, user_id, concept_id=concept_id, limit=5)

    current = next((m for m in mastery_rows if m.concept_id == concept_id), None)
    return {
        "hasHistory": bool(mastery_rows),
        "userId": user_id,
        "subjectId": subject_id,
        "conceptId": concept_id,
        "concept": concept_label(concept_id) if concept_id else None,
        "currentMastery": round(current.mastery_score, 1) if current else None,
        "currentState": current.state if current else None,
        "currentAttempts": (current.questions_attempted or 0) if current else 0,
        "weakConcepts": [
            {"conceptId": w["conceptId"], "concept": w["concept"], "mastery": w["mastery"], "reason": w["reason"]}
            for w in weak
        ],
        "recentMistakes": [
            {
                "question": m["question"],
                "concept": m["concept"],
                "selectedAnswer": m["selectedAnswer"],
                "correctAnswer": m["correctAnswer"],
                "difficulty": m["difficulty"],
                "createdAt": m["createdAt"],
            }
            for m in mistakes
        ],
        "mistakePatterns": analyze_mistake_patterns(mistakes),
    }


def describe_student_context(ctx: Dict) -> str:
    """Prompt fragment — only statements supported by stored performance."""
    if not ctx.get("hasHistory"):
        return "No performance history is recorded for this student yet; do not claim they are struggling."
    lines = []
    if ctx.get("currentAttempts"):
        lines.append(
            f"Current concept {ctx.get('concept')}: LexiMind Mastery Score "
            f"{ctx.get('currentMastery')} ({ctx.get('currentState')}) over {ctx['currentAttempts']} attempts."
        )
    for w in ctx.get("weakConcepts") or []:
        lines.append(f"Weak: {w['concept']} (mastery {w['mastery']}) — {w['reason']}")
    for m in (ctx.get("recentMistakes") or [])[:3]:
        lines.append(
            f"Recent mistake on {m['concept']}: answered '{m['selectedAnswer']}'"
            + (f" (correct: '{m['correctAnswer']}')" if m.get("correctAnswer") else "")
        )
    for p in ctx.get("mistakePatterns") or []:
        lines.append(f"Pattern: {p['summary']}")
    return "\n".join(lines) if lines else "No attempts recorded for this concept yet."


def _serialize_question(q: Question) -> Dict:
    return {
        "id": q.id,
        "question": q.question_text,
        "options": q.options,
        "answer": q.answer,
        "explanation": q.explanation,
        "difficulty": q.difficulty,
        "source": q.source,
        "year": q.year,
        "conceptId": q.concept_id,
        "isDemo": bool(q.is_demo),
    }


async def _attempted_question_ids(db: AsyncSession, user_id: Optional[str]) -> List[int]:
    if not user_id:
        return []
    return [r[0] for r in (await db.execute(
        select(QuizAnswer.question_id).where(
            QuizAnswer.user_id == user_id, QuizAnswer.question_id.isnot(None)
        )
    )).all()]


async def _pick_question(
    db: AsyncSession,
    concept_id: Optional[str],
    subject_id: Optional[str],
    difficulty: Optional[str] = None,
    exclude_ids: Optional[List[int]] = None,
    viewer: Optional[str] = None,
) -> Optional[Question]:
    stmt = exclude_foreign(
        select(Question).where(Question.review_status != "REJECTED"),
        Question.document_id,
        viewer,
    )
    if concept_id:
        mapped = select(QuestionConcept.question_id).where(QuestionConcept.concept_id == concept_id)
        stmt = stmt.where(or_(Question.concept_id == concept_id, Question.id.in_(mapped)))
    elif subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty.upper())
    if exclude_ids:
        stmt = stmt.where(Question.id.notin_(exclude_ids))
    rows = list((await db.execute(stmt.limit(20))).scalars().all())
    if not rows:
        return None
    order = {"PYQ": 0, "UPLOADED": 1, "PREMADE": 2, "DEMO": 3, "AI_GENERATED": 4}
    rows.sort(key=lambda r: (order.get(r.source, 9), r.id))
    return rows[0]


async def resolve_action(
    db: AsyncSession,
    action: Optional[str],
    user_id: Optional[str],
    subject_id: Optional[str],
    concept_id: Optional[str],
) -> Dict:
    """Data payload for actions that must be backed by real records."""
    action = normalize_action(action)
    if action == "TEST_ME":
        seen = await _attempted_question_ids(db, user_id)
        q = await _pick_question(db, concept_id, subject_id, exclude_ids=seen, viewer=user_id) \
            or await _pick_question(db, concept_id, subject_id, viewer=user_id)
        return {"action": action, "question": _serialize_question(q) if q else None,
                "empty": q is None,
                "message": None if q else "No question is available for this concept yet."}

    if action == "SIMILAR_QUESTION":
        last_wrong = None
        if user_id:
            mistakes = await get_mistakes(db, user_id, concept_id=concept_id, limit=1)
            last_wrong = mistakes[0] if mistakes else None
        difficulty = (last_wrong or {}).get("difficulty")
        exclude = [last_wrong["questionId"]] if last_wrong and last_wrong.get("questionId") else []
        # Do not hand back the question TEST_ME would serve — "similar" must be a
        # different question when the bank has one.
        seen = await _attempted_question_ids(db, user_id)
        test_me_pick = await _pick_question(db, concept_id, subject_id, exclude_ids=seen, viewer=user_id)
        if test_me_pick:
            exclude = exclude + [test_me_pick.id]
        q = (
            await _pick_question(db, concept_id, subject_id, difficulty, exclude, viewer=user_id)
            or await _pick_question(db, concept_id, subject_id, None, exclude, viewer=user_id)
            or test_me_pick
        )
        return {"action": action, "question": _serialize_question(q) if q else None,
                "basedOn": last_wrong, "empty": q is None,
                "message": None if q else "No similar question is available yet."}

    if action == "EXPLAIN_MISTAKE":
        mistakes = await get_mistakes(db, user_id, concept_id=concept_id, limit=1) if user_id else []
        mistake = mistakes[0] if mistakes else None
        return {"action": action, "mistake": mistake, "empty": mistake is None,
                "message": None if mistake else "No incorrect answers are recorded yet."}

    if action in ("EXPLAIN", "SIMPLIFY", "EXAMPLE", "HINT"):
        notes = await concept_material(db, concept_id, subject_id, viewer=user_id)
        return {"action": action, "notes": notes, "empty": not notes,
                "message": None if notes else "No stored notes cover this concept yet."}

    return {"action": action} if action else {}


async def concept_material(
    db: AsyncSession,
    concept_id: Optional[str],
    subject_id: Optional[str] = None,
    limit: int = 2,
    viewer: Optional[str] = None,
) -> List[Dict]:
    """Stored notes for a concept — the grounding used when no LLM is available."""
    if not concept_id and not subject_id:
        return []
    stmt = exclude_foreign(select(AcademicNote), AcademicNote.source_document_id, viewer)
    if concept_id:
        stmt = stmt.where(AcademicNote.concept_id == concept_id)
    elif subject_id:
        stmt = stmt.where(AcademicNote.subject_id == subject_id)
    rows = (await db.execute(stmt.order_by(AcademicNote.id.asc()).limit(limit))).scalars().all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "summary": n.summary,
            "content": n.content,
            "keyPoints": n.key_points or [],
            "formulas": n.formulas or [],
            "examples": n.examples or [],
            "source": n.source,
            "sourcePages": n.source_pages or [],
            "isDemo": bool(n.is_demo),
        }
        for n in rows
    ]


def action_instruction(action: Optional[str], payload: Dict) -> str:
    action = normalize_action(action)
    guides = {
        "EXPLAIN": "Explain the concept clearly using the retrieved material.",
        "SIMPLIFY": "Simplify the explanation for a beginner.",
        "EXAMPLE": "Give a worked example based on the retrieved material.",
        "HINT": "Give a hint, not the full solution.",
        "TEST_ME": "Present the question below to the student and ask them to attempt it.",
        "SIMILAR_QUESTION": "Present the practice question below, similar to the one they missed.",
        "EXPLAIN_MISTAKE": "Explain the student's recorded incorrect answer below. Do not invent facts.",
    }
    text = guides.get(action or "", "")
    q = payload.get("question")
    if q:
        text += f"\n\nQuestion (source {q.get('source')}"
        if q.get("year"):
            text += f", {q['year']}"
        text += f"): {q.get('question')}"
        if q.get("answer"):
            text += f"\nRecorded answer: {q['answer']}"
    mistake = payload.get("mistake")
    if mistake:
        text += (
            f"\n\nStudent's incorrect attempt on {mistake.get('concept')}:"
            f"\nQuestion: {mistake.get('question')}"
            f"\nTheir answer: {mistake.get('selectedAnswer')}"
        )
        if mistake.get("correctAnswer"):
            text += f"\nCorrect answer: {mistake['correctAnswer']}"
        if mistake.get("explanation"):
            text += f"\nStored explanation: {mistake['explanation']}"
    return text.strip()


def fallback_action_reply(action: Optional[str], payload: Dict) -> Optional[str]:
    """Deterministic, source-only reply used when no LLM is configured."""
    action = normalize_action(action)
    if action in ("TEST_ME", "SIMILAR_QUESTION"):
        q = payload.get("question")
        if not q:
            return payload.get("message")
        label = "Here's a question for you" if action == "TEST_ME" else "Here's a similar question"
        source = q.get("source") + (f" {q['year']}" if q.get("year") else "")
        body = f"{label} ({source}):\n\n{q.get('question')}"
        if q.get("options"):
            body += "\n" + "\n".join(f"- {o}" for o in q["options"])
        return body
    if action == "EXPLAIN_MISTAKE":
        m = payload.get("mistake")
        if not m:
            return payload.get("message")
        body = (
            f"On {m.get('concept')} you answered '{m.get('selectedAnswer')}' to:\n\n{m.get('question')}"
        )
        if m.get("correctAnswer"):
            body += f"\n\nThe recorded correct answer is: {m['correctAnswer']}"
        if m.get("explanation"):
            body += f"\n\nExplanation from the source material: {m['explanation']}"
        elif not m.get("correctAnswer"):
            body += "\n\nNo answer key is stored for this question, so I can't state the correct answer."
        return body

    if action in ("EXPLAIN", "SIMPLIFY", "EXAMPLE", "HINT"):
        notes = payload.get("notes") or []
        if not notes:
            return payload.get("message")
        note = notes[0]
        parts = [f"From your stored notes — {note.get('title')}:"]
        if action == "HINT":
            points = note.get("keyPoints") or []
            parts.append(points[0] if points else (note.get("summary") or note.get("content", ""))[:300])
        elif action == "EXAMPLE":
            examples = note.get("examples") or []
            if examples:
                ex = examples[0]
                parts.append(ex if isinstance(ex, str) else str(ex))
            else:
                parts.append("No worked example is stored for this concept yet.")
        elif action == "SIMPLIFY":
            parts.append(note.get("summary") or (note.get("content") or "")[:400])
            for point in (note.get("keyPoints") or [])[:3]:
                parts.append(f"• {point}")
        else:  # EXPLAIN
            parts.append(note.get("summary") or "")
            parts.append((note.get("content") or "")[:900])
            for formula in (note.get("formulas") or [])[:3]:
                parts.append(f"Formula: {formula}")
        return "\n\n".join(p for p in parts if p)

    return None


def note_sources(notes: List[Dict]) -> List[Dict]:
    """Citations for stored notes — only fields that actually exist are emitted."""
    out = []
    for n in notes:
        entry = {"title": n.get("title"), "source": n.get("source"), "type": "NOTE"}
        pages = n.get("sourcePages") or []
        if pages:
            entry["page"] = pages[0]
        out.append(entry)
    return out
