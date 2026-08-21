"""Tiny DEMO dataset — clearly labeled, never presented as authentic PYQs."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import AcademicConcept, Question, AcademicNote, QuestionConcept


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
]


async def seed_demo_if_needed(db: AsyncSession) -> None:
    count = await db.execute(select(func.count()).select_from(Question).where(Question.is_demo.is_(True)))
    if (count.scalar() or 0) > 0:
        return

    for c in DEMO_CONCEPTS:
        exists = await db.execute(select(AcademicConcept).where(AcademicConcept.slug == c["slug"]))
        if exists.scalar_one_or_none():
            continue
        db.add(AcademicConcept(**c, is_demo=True, needs_review=False, review_status="APPROVED"))

    for q in DEMO_QUESTIONS:
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

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3 seed data — ConceptMastery records, extra questions, ReviewSchedule
# ═══════════════════════════════════════════════════════════════════════════════

_PHASE3_DEMO_USER = "demo-user-1"

_EXTRA_DEMO_QUESTIONS = [
    # HARD questions for euler-theorem-dc
    {
        "question_text": "[DEMO] If u = log(x³ + y³ - x²y - xy²), show x·∂u/∂x + y·∂u/∂y = 2.",
        "options": None, "answer": "Euler's theorem applied to log of degree-2 homogeneous expression.",
        "explanation": "Let v = x³+y³-x²y-xy² (degree 3); then u = log(v/x) after manipulation, giving degree 2.",
        "question_type": "PROOF", "difficulty": "HARD",
        "concept_id": "euler-theorem-dc", "subject_id": "em1-btech", "chapter_id": "dc-em1",
    },
    {
        "question_text": "[DEMO] Verify Euler's theorem for f(x,y) = (x²+y²)/(x+y).",
        "options": None, "answer": None,
        "explanation": "f is homogeneous of degree 1; x·fx + y·fy = f.",
        "question_type": "PROOF", "difficulty": "HARD",
        "concept_id": "euler-theorem-dc", "subject_id": "em1-btech", "chapter_id": "dc-em1",
    },
    # EASY question for homogeneous-functions
    {
        "question_text": "[DEMO] Which function is NOT homogeneous? (a) x+y (b) x²+xy+y² (c) x+y+1 (d) x³/y",
        "options": ["x+y", "x²+xy+y²", "x+y+1", "x³/y"],
        "answer": "x+y+1",
        "explanation": "The constant term 1 prevents homogeneity.",
        "question_type": "MCQ", "difficulty": "EASY",
        "concept_id": "homogeneous-functions", "subject_id": "em1-btech", "chapter_id": "dc-em1",
    },
    # MEDIUM for partial-derivatives-dc
    {
        "question_text": "[DEMO] If z = sin(x+y), find ∂²z/∂x².",
        "options": ["-sin(x+y)", "cos(x+y)", "sin(x+y)", "-cos(x+y)"],
        "answer": "-sin(x+y)",
        "explanation": "∂z/∂x = cos(x+y), ∂²z/∂x² = -sin(x+y).",
        "question_type": "MCQ", "difficulty": "MEDIUM",
        "concept_id": "partial-derivatives-dc", "subject_id": "em1-btech", "chapter_id": "dc-em1",
    },
    # HARD for partial-derivatives-dc
    {
        "question_text": "[DEMO] Show that ∂²z/∂x∂y = ∂²z/∂y∂x for z = e^(xy)·sin(x+y).",
        "options": None, "answer": None,
        "explanation": "Both mixed partials equal e^(xy)[cos(x+y) + (x+y)·sin(x+y) + cos(x+y)] by symmetry.",
        "question_type": "PROOF", "difficulty": "HARD",
        "concept_id": "partial-derivatives-dc", "subject_id": "em1-btech", "chapter_id": "dc-em1",
    },
]

_PHASE3_MASTERY_RECORDS = [
    # MASTERED — partial derivatives
    {
        "concept_id": "partial-derivatives-dc",
        "mastery_score": 88.0,
        "questions_attempted": 12,
        "questions_correct": 10,
        "questions_incorrect": 2,
        "streak": 4,
        "state": "MASTERED",
        "status": "mastered",
        "confidence": 0.88,
    },
    # WEAK — Euler's theorem
    {
        "concept_id": "euler-theorem-dc",
        "mastery_score": 35.0,
        "questions_attempted": 6,
        "questions_correct": 2,
        "questions_incorrect": 4,
        "streak": 0,
        "state": "WEAK",
        "status": "needs_review",
        "confidence": 0.55,
    },
    # DEVELOPING — homogeneous functions
    {
        "concept_id": "homogeneous-functions",
        "mastery_score": 62.0,
        "questions_attempted": 8,
        "questions_correct": 5,
        "questions_incorrect": 3,
        "streak": 2,
        "state": "DEVELOPING",
        "status": "in_progress",
        "confidence": 0.7,
    },
]


async def seed_phase3_if_needed(db: AsyncSession) -> None:
    """Seed Phase 3 demo data (ConceptMastery + ReviewSchedule). Idempotent."""
    from app.models.academic import ConceptMastery, ReviewSchedule, QuestionAttempt
    from datetime import datetime, timezone, timedelta

    # Check idempotency — skip if demo mastery already exists
    existing = await db.execute(
        select(func.count()).select_from(ConceptMastery).where(
            ConceptMastery.user_id == _PHASE3_DEMO_USER
        )
    )
    if (existing.scalar() or 0) > 0:
        return

    now = datetime.now(timezone.utc)

    # 1. Extra demo questions
    for q in _EXTRA_DEMO_QUESTIONS:
        row = Question(
            document_id=None,
            question_text=q["question_text"],
            options=q["options"],
            answer=q["answer"],
            explanation=q["explanation"],
            question_type=q["question_type"],
            difficulty=q["difficulty"],
            difficulty_confidence=0.7,
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

    # 2. ConceptMastery records for demo user
    for rec in _PHASE3_MASTERY_RECORDS:
        db.add(ConceptMastery(
            user_id=_PHASE3_DEMO_USER,
            concept_id=rec["concept_id"],
            mastery_score=rec["mastery_score"],
            questions_attempted=rec["questions_attempted"],
            questions_correct=rec["questions_correct"],
            questions_incorrect=rec["questions_incorrect"],
            streak=rec["streak"],
            state=rec["state"],
            status=rec["status"],
            confidence=rec["confidence"],
            last_attempted=now - timedelta(days=1),
            last_correct_at=now - timedelta(days=2) if rec["questions_correct"] > 0 else None,
            next_review_at=now + timedelta(days=3),
            updated_at=now,
        ))

    await db.flush()

    # 3. QuestionAttempt history for WEAK concept (last 4 wrong — triggers streak detection)
    for i in range(4):
        db.add(QuestionAttempt(
            user_id=_PHASE3_DEMO_USER,
            concept_id="euler-theorem-dc",
            correct=(i == 0),  # only first was correct; last 3 wrong
            difficulty="medium",
            created_at=now - timedelta(hours=24 - i * 2),
        ))

    # 4. ReviewSchedule — MASTERED concept has overdue review
    db.add(ReviewSchedule(
        user_id=_PHASE3_DEMO_USER,
        concept_id="partial-derivatives-dc",
        next_review_at=now - timedelta(days=1),  # overdue
        current_interval_days=3,
        review_count=1,
    ))

    await db.flush()
