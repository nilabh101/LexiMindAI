from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
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
    status = Column(String(20), default="processing")

    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="analyses")
