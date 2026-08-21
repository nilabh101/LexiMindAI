"""Document ownership filters shared by every content surface.

Notes, questions and chunks derived from an uploaded PDF inherit that PDF's
owner. Documents uploaded before user ids were recorded have no owner and stay
readable so the Phase 2 demo library keeps working.
"""
from typing import Optional

from sqlalchemy import Select, select

from app.models.document import Document


def foreign_document_ids(viewer: Optional[str]) -> Select:
    """Ids of documents owned by somebody other than the viewer."""
    stmt = select(Document.id).where(Document.user_id.isnot(None))
    if viewer:
        stmt = stmt.where(Document.user_id != viewer)
    return stmt


def visible_documents(stmt: Select, viewer: Optional[str]) -> Select:
    return stmt.where(Document.id.notin_(foreign_document_ids(viewer)))


def exclude_foreign(stmt: Select, column, viewer: Optional[str]) -> Select:
    """Keep rows with no source document or one the viewer may read."""
    return stmt.where(
        (column.is_(None)) | (column.notin_(foreign_document_ids(viewer)))
    )
