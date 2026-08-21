"""Phase 2 academic intelligence models. Extends the existing Document table."""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Boolean, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    clean_text = Column(Text, nullable=True)
    blocks = Column(JSON, nullable=True)

    document = relationship("Document", back_populates="pages")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=True)
    section = Column(String(500), nullable=True)
    text = Column(Text, nullable=False)
    subject_id = Column(String(80), nullable=True, index=True)
    chapter_id = Column(String(80), nullable=True, index=True)
    concept_id = Column(String(120), nullable=True, index=True)
    embedding = Column(JSON, nullable=True)
    source_type = Column(String(40), nullable=True)

    document = relationship("Document", back_populates="chunks")


class AcademicConcept(Base):
    __tablename__ = "academic_concepts"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(160), unique=True, index=True, nullable=False)
    canonical_name = Column(String(300), nullable=False)
    normalized_name = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=True)
    description_origin = Column(String(20), nullable=True)  # SOURCE | GENERATED | null
    subject_id = Column(String(80), nullable=True, index=True)
    chapter_id = Column(String(80), nullable=True, index=True)
    chapter_name = Column(String(300), nullable=True)
    topic_name = Column(String(300), nullable=True)
    confidence = Column(Float, default=0.0)
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    needs_review = Column(Boolean, default=False)
    review_status = Column(String(20), default="APPROVED")  # APPROVED | NEEDS_REVIEW | REJECTED
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    page_number = Column(Integer, nullable=True)
    question_number = Column(String(40), nullable=True)
    question_text = Column(Text, nullable=False)
    year = Column(Integer, nullable=True)
    marks = Column(Float, nullable=True)
    question_type = Column(String(30), default="UNKNOWN")
    options = Column(JSON, nullable=True)
    answer = Column(Text, nullable=True)  # never invented; only if present in source
    explanation = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    needs_review = Column(Boolean, default=False)
    review_status = Column(String(20), default="NEEDS_REVIEW")
    source = Column(String(30), nullable=False, default="UPLOADED")  # PYQ | UPLOADED | PREMADE | AI_GENERATED | DEMO
    difficulty = Column(String(20), nullable=True)
    difficulty_confidence = Column(Float, nullable=True)
    subject_id = Column(String(80), nullable=True, index=True)
    chapter_id = Column(String(80), nullable=True, index=True)
    concept_id = Column(String(120), nullable=True, index=True)
    parent_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    mappings = relationship("QuestionConcept", back_populates="question", cascade="all, delete-orphan")


class QuestionConcept(Base):
    __tablename__ = "question_concepts"
    __table_args__ = (UniqueConstraint("question_id", "concept_id", "rel_type", name="uq_qc_rel"),)

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(String(120), nullable=False, index=True)
    rel_type = Column(String(20), nullable=False, default="PRIMARY")  # PRIMARY | SECONDARY
    confidence = Column(Float, default=0.0)
    needs_review = Column(Boolean, default=False)

    question = relationship("Question", back_populates="mappings")


class AcademicNote(Base):
    __tablename__ = "academic_notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(400), nullable=False)
    subject_id = Column(String(80), nullable=True, index=True)
    chapter_id = Column(String(80), nullable=True)
    concept_id = Column(String(120), nullable=True, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    formulas = Column(JSON, nullable=True)
    examples = Column(JSON, nullable=True)
    key_points = Column(JSON, nullable=True)
    source = Column(String(30), nullable=False, default="SOURCE_DERIVED")  # SOURCE_DERIVED | AI_GENERATED
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    source_pages = Column(JSON, nullable=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_user_concept_mastery"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(80), nullable=False, index=True)
    concept_id = Column(String(120), nullable=False, index=True)
    mastery_score = Column(Float, default=0.0)
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    last_attempted = Column(DateTime, nullable=True)
    confidence = Column(Float, default=0.0)
    status = Column(String(30), default="not_started")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(String(80), nullable=False, index=True)
    user_id = Column(String(80), nullable=False, index=True)
    subject_id = Column(String(80), nullable=True)
    concept_id = Column(String(120), nullable=True)
    question_ids = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    correct_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(80), nullable=False, index=True)
    quiz_id = Column(String(80), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    selected_answer = Column(Text, nullable=True)
    correct = Column(Boolean, nullable=True)
    time_taken = Column(Float, nullable=True)
    concept_id = Column(String(120), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
