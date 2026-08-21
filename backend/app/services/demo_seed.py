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
