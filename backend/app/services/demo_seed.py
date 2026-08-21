"""Tiny DEMO dataset — clearly labeled, never presented as authentic PYQs.

The demo learner's *attempts* are seeded, but the mastery values themselves are
always computed by the real engine from those attempts — no score is invented.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import (
    AcademicConcept, AcademicNote, ConceptMastery, Question, QuestionConcept, QuizAnswer,
)

DEMO_USER_ID = "demo-user-1"


DEMO_CONCEPTS = [
    {
        "slug": "partial-derivatives-dc",
        "canonical_name": "Partial Derivatives",
        "normalized_name": "partial derivatives",
        "description": "Partial differentiation of functions of several variables.",
        "description_origin": "SOURCE",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
        "chapter_name": "Differential Calculus",
        "topic_name": "Partial Derivatives",
        "confidence": 1.0,
    },
    {
        "slug": "homogeneous-functions",
        "canonical_name": "Homogeneous Functions",
        "normalized_name": "homogeneous functions",
        "description": "f(tx, ty) = t^n f(x, y).",
        "description_origin": "SOURCE",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
        "chapter_name": "Differential Calculus",
        "topic_name": "Homogeneous Functions",
        "confidence": 1.0,
    },
    {
        "slug": "euler-theorem-dc",
        "canonical_name": "Euler's Theorem",
        "normalized_name": "eulers theorem",
        "description": "If f is homogeneous of degree n, then x ∂f/∂x + y ∂f/∂y = n f.",
        "description_origin": "SOURCE",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
        "chapter_name": "Differential Calculus",
        "topic_name": "Euler's Theorem",
        "confidence": 1.0,
    },
]

DEMO_QUESTIONS = [
    {
        "question_text": "[DEMO] If f(x, y) = x³ + y³ + 3x²y, what is the degree of homogeneity?",
        "options": ["2", "3", "4", "1"],
        "answer": "3",
        "explanation": "f(tx, ty) = t³ f(x, y), so degree 3.",
        "question_type": "MCQ",
        "difficulty": "MEDIUM",
        "concept_id": "euler-theorem-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] Euler's theorem states: if f is homogeneous of degree n, then:",
        "options": [
            "x·∂f/∂x + y·∂f/∂y = n·f",
            "x·∂f/∂x · y·∂f/∂y = n·f",
            "∂f/∂x + ∂f/∂y = n",
            "x + y = n·f",
        ],
        "answer": "x·∂f/∂x + y·∂f/∂y = n·f",
        "explanation": "Direct statement of Euler's theorem.",
        "question_type": "MCQ",
        "difficulty": "EASY",
        "concept_id": "euler-theorem-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] For f(x,y) = x²y + y³, find ∂f/∂x.",
        "options": ["2xy", "2xy + y³", "x² + 3y²", "2x + 3y²"],
        "answer": "2xy",
        "explanation": "Treat y as constant: ∂/∂x(x²y) = 2xy.",
        "question_type": "MCQ",
        "difficulty": "EASY",
        "concept_id": "partial-derivatives-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] State the definition of a homogeneous function of degree n.",
        "options": None,
        "answer": "f(tx, ty) = t^n f(x, y) for all t (in the domain).",
        "explanation": None,
        "question_type": "SHORT_ANSWER",
        "difficulty": "EASY",
        "concept_id": "homogeneous-functions",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] Verify Euler's theorem for u = x³ + y³.",
        "options": None,
        "answer": None,
        "explanation": "u is homogeneous of degree 3; x ux + y uy = 3u.",
        "question_type": "PROOF",
        "difficulty": "MEDIUM",
        "concept_id": "euler-theorem-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] Compute the mixed partial ∂²f/∂x∂y for f(x,y) = x²y³.",
        "options": ["6xy²", "2xy³", "6x²y", "2x y³"],
        "answer": "6xy²",
        "explanation": "fx = 2x y³, then fxy = 6x y².",
        "question_type": "MCQ",
        "difficulty": "MEDIUM",
        "concept_id": "partial-derivatives-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] If u = x² + y² + z², then x ux + y uy + z uz equals:",
        "options": ["u", "2u", "3u", "0"],
        "answer": "2u",
        "explanation": "Homogeneous of degree 2.",
        "question_type": "MCQ",
        "difficulty": "MEDIUM",
        "concept_id": "euler-theorem-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] Evaluate lim(x→0) sin(x)/x.",
        "options": ["0", "1", "∞", "undefined"],
        "answer": "1",
        "explanation": "Standard limit: sin(x)/x → 1 as x → 0.",
        "question_type": "MCQ",
        "difficulty": "EASY",
        "concept_id": "limits-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] A function f is continuous at x = a if:",
        "options": [
            "lim(x→a) f(x) = f(a)",
            "f(a) is defined only",
            "lim(x→a) f(x) exists only",
            "f is differentiable at a",
        ],
        "answer": "lim(x→a) f(x) = f(a)",
        "explanation": "Continuity requires the limit to exist and equal the value.",
        "question_type": "MCQ",
        "difficulty": "EASY",
        "concept_id": "limits-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] For f(x, y) = x²y + y³, find ∂f/∂y.",
        "options": ["x² + 3y²", "2xy", "x²y", "3y²"],
        "answer": "x² + 3y²",
        "explanation": "Treat x as constant: ∂/∂y(x²y + y³) = x² + 3y².",
        "question_type": "MCQ",
        "difficulty": "EASY",
        "concept_id": "partial-derivatives-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] If u = log((x³ + y³)/(x + y)), show that x ux + y uy = 2.",
        "options": None,
        "answer": None,
        "explanation": "e^u is homogeneous of degree 2; apply Euler's theorem to e^u.",
        "question_type": "PROOF",
        "difficulty": "HARD",
        "concept_id": "euler-theorem-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] Verify Clairaut's theorem (fxy = fyx) for f(x, y) = x³y².",
        "options": None,
        "answer": None,
        "explanation": "fxy = 6x²y and fyx = 6x²y, so the mixed partials agree.",
        "question_type": "PROOF",
        "difficulty": "HARD",
        "concept_id": "partial-derivatives-dc",
        "subject_id": "em1-btech",
        "chapter_id": "dc-em1",
    },
]

# Demo learner attempt history: limits are solid, Euler's theorem is not.
# (question index into DEMO_QUESTIONS, correct, days ago)
DEMO_ATTEMPTS = [
    (7, True, 6), (8, True, 6), (7, True, 3), (8, True, 3), (7, True, 1), (8, True, 1),
    (1, False, 5), (0, False, 5), (4, False, 4), (6, True, 2), (1, False, 1), (0, False, 1),
    (2, True, 4), (9, True, 4), (5, False, 2),
]


async def seed_demo_if_needed(db: AsyncSession) -> None:
    existing_texts = set((await db.execute(
        select(Question.question_text).where(Question.is_demo.is_(True))
    )).scalars().all())

    for c in DEMO_CONCEPTS:
        exists = await db.execute(select(AcademicConcept).where(AcademicConcept.slug == c["slug"]))
        if exists.scalar_one_or_none():
            continue
        db.add(AcademicConcept(**c, is_demo=True, needs_review=False, review_status="APPROVED"))

    for q in DEMO_QUESTIONS:
        if q["question_text"] in existing_texts:
            continue
        row = Question(
            document_id=None,
            question_text=q["question_text"],
            options=q["options"],
            answer=q["answer"],
            explanation=q["explanation"],
            question_type=q["question_type"],
            difficulty=q["difficulty"],
            difficulty_confidence=0.5,
            concept_id=q["concept_id"],
            subject_id=q["subject_id"],
            chapter_id=q["chapter_id"],
            source="DEMO",
            year=None,
            marks=None,
            confidence=1.0,
            needs_review=False,
            review_status="APPROVED",
            is_demo=True,
        )
        db.add(row)
        await db.flush()
        db.add(QuestionConcept(
            question_id=row.id,
            concept_id=q["concept_id"],
            rel_type="PRIMARY",
            confidence=1.0,
            needs_review=False,
        ))
        if q["concept_id"] == "euler-theorem-dc":
            db.add(QuestionConcept(
                question_id=row.id,
                concept_id="homogeneous-functions",
                rel_type="SECONDARY",
                confidence=0.8,
                needs_review=False,
            ))

    note_exists = await db.execute(
        select(AcademicNote.id).where(AcademicNote.title == "[DEMO] Euler's Theorem — Complete Notes")
    )
    if note_exists.scalars().first():
        await db.flush()
        await seed_demo_learner(db)
        return

    db.add(AcademicNote(
        title="[DEMO] Euler's Theorem — Complete Notes",
        subject_id="em1-btech",
        chapter_id="dc-em1",
        concept_id="euler-theorem-dc",
        content=(
            "# Euler's Theorem on Homogeneous Functions\n\n"
            "A function f(x, y) is homogeneous of degree n if f(tx, ty) = t^n f(x, y).\n\n"
            "Theorem: x · (∂f/∂x) + y · (∂f/∂y) = n · f\n"
        ),
        summary="If f is homogeneous of degree n, then x ∂f/∂x + y ∂f/∂y = n f.",
        formulas=["x·(∂f/∂x) + y·(∂f/∂y) = n·f"],
        key_points=["Homogeneous function definition", "Euler's theorem formula"],
        examples=["f(x,y)=x³+y³ is degree 3"],
        source="SOURCE_DERIVED",
        is_demo=True,
        source_pages=None,
    ))
    await db.flush()
    await seed_demo_learner(db)


async def seed_demo_learner(db: AsyncSession) -> None:
    """Give the demo user a small attempt history (one weak, one mastered concept).

    Only the attempts are seeded; mastery is then computed by the real engine.
    """
    from app.services.mastery import recalculate_concept_mastery
    from app.services.review import schedule_next_review

    existing = await db.execute(
        select(func.count()).select_from(QuizAnswer).where(QuizAnswer.user_id == DEMO_USER_ID)
    )
    if (existing.scalar() or 0) > 0:
        # Attempts already seeded — refresh derived state so databases created by
        # earlier versions pick up newly added mastery/review fields.
        rows = (await db.execute(
            select(ConceptMastery).where(ConceptMastery.user_id == DEMO_USER_ID)
        )).scalars().all()
        for row in rows:
            await recalculate_concept_mastery(
                db, DEMO_USER_ID, row.concept_id, subject_id=row.subject_id or "em1-btech",
            )
        await db.flush()
        return

    demo_questions = list((await db.execute(
        select(Question).where(Question.source == "DEMO").order_by(Question.id.asc())
    )).scalars().all())
    by_text = {q.question_text: q for q in demo_questions}

    now = datetime.now(timezone.utc)
    touched = set()
    for index, correct, days_ago in DEMO_ATTEMPTS:
        question = by_text.get(DEMO_QUESTIONS[index]["question_text"])
        if question is None:
            continue
        db.add(QuizAnswer(
            user_id=DEMO_USER_ID,
            quiz_id=f"demo-quiz-{days_ago}",
            question_id=question.id,
            selected_answer=question.answer if correct else "[DEMO] incorrect answer",
            correct_answer=question.answer,
            correct=correct,
            time_taken=45.0,
            concept_id=question.concept_id,
            difficulty=question.difficulty,
            created_at=now - timedelta(days=days_ago),
        ))
        touched.add(question.concept_id)
    await db.flush()

    for concept_id in touched:
        row = await recalculate_concept_mastery(
            db, DEMO_USER_ID, concept_id, subject_id="em1-btech", session_accuracy=None, now=now,
        )
        accuracy = (row.questions_correct or 0) / max(row.questions_attempted or 1, 1)
        row.review_interval_days, row.next_review_at = schedule_next_review(None, accuracy, now=now)
    await db.flush()
