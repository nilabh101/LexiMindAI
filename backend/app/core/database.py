from sqlalchemy import inspect, text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=_connect_args,
)

if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


_DOCUMENT_NEW_COLUMNS = [
    ("user_id", "VARCHAR(80)"),
    ("education_level", "VARCHAR(20)"),
    ("class_or_year", "VARCHAR(40)"),
    ("course", "VARCHAR(120)"),
    ("semester", "VARCHAR(40)"),
    ("subject", "VARCHAR(200)"),
    ("subject_id", "VARCHAR(80)"),
    ("document_type", "VARCHAR(40)"),
    ("user_document_type", "VARCHAR(40)"),
    ("classification_confidence", "FLOAT"),
    ("classification_reason", "TEXT"),
    ("error_message", "TEXT"),
    ("raw_text", "TEXT"),
    ("ocr_required", "BOOLEAN DEFAULT 0"),
    ("ocr_message", "TEXT"),
]

# Phase 3: new columns on concept_mastery table
_MASTERY_NEW_COLUMNS = [
    ("questions_incorrect", "INTEGER DEFAULT 0"),
    ("last_correct_at", "DATETIME"),
    ("streak", "INTEGER DEFAULT 0"),
    ("state", "VARCHAR(30) DEFAULT 'NOT_STARTED'"),
    ("next_review_at", "DATETIME"),
    ("updated_at", "DATETIME"),
]


def _migrate_sqlite(sync_conn):
    inspector = inspect(sync_conn)
    tables = inspector.get_table_names()
    if "documents" not in tables:
        return
    # documents table
    cols = {c["name"] for c in inspector.get_columns("documents")}
    for name, ddl in _DOCUMENT_NEW_COLUMNS:
        if name not in cols:
            sync_conn.execute(text(f"ALTER TABLE documents ADD COLUMN {name} {ddl}"))
    # concept_mastery table — Phase 3 additions
    if "concept_mastery" in tables:
        mcols = {c["name"] for c in inspector.get_columns("concept_mastery")}
        for name, ddl in _MASTERY_NEW_COLUMNS:
            if name not in mcols:
                sync_conn.execute(text(f"ALTER TABLE concept_mastery ADD COLUMN {name} {ddl}"))


async def init_db():
    from app.models import document as _document  # noqa: F401
    from app.models import academic as _academic  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_sqlite)
    try:
        from app.services.demo_seed import seed_demo_if_needed, seed_phase3_if_needed
        async with AsyncSessionLocal() as session:
            await seed_demo_if_needed(session)
            await session.commit()
        async with AsyncSessionLocal() as session:
            await seed_phase3_if_needed(session)
            await session.commit()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"[init_db] seed skipped: {exc}")
