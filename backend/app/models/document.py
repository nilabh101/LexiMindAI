from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    word_count = Column(Integer, default=0)
    unique_word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    paragraph_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    reading_time_minutes = Column(Float, default=0.0)
    reading_grade_level = Column(Float, default=0.0)
    lexical_diversity = Column(Float, default=0.0)
    extracted_text = Column(Text, nullable=True)
    status = Column(String(20), default="UPLOADED")

    # Phase 2 academic metadata (uploader-provided; never invented)
    user_id = Column(String(80), nullable=True, index=True)
    education_level = Column(String(20), nullable=True)
    class_or_year = Column(String(40), nullable=True)
    course = Column(String(120), nullable=True)
    semester = Column(String(40), nullable=True)
    subject = Column(String(200), nullable=True)
    subject_id = Column(String(80), nullable=True, index=True)
    document_type = Column(String(40), nullable=True)  # STUDY_NOTES | PYQ | QUESTION_BANK | REFERENCE | UNKNOWN
    user_document_type = Column(String(40), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    classification_reason = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    ocr_required = Column(Boolean, default=False)
    ocr_message = Column(Text, nullable=True)

    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="analyses")
