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


# Phase 3 adaptive columns added to existing Phase 2 tables.
_CONCEPT_MASTERY_NEW_COLUMNS = [
    ("questions_incorrect", "INTEGER DEFAULT 0"),
    ("last_correct_at", "DATETIME"),
    ("streak", "INTEGER DEFAULT 0"),
    ("state", "VARCHAR(30) DEFAULT 'NOT_STARTED'"),
    ("subject_id", "VARCHAR(80)"),
    ("next_review_at", "DATETIME"),
    ("review_interval_days", "INTEGER"),
    ("updated_at", "DATETIME"),
]

_QUIZ_ANSWER_NEW_COLUMNS = [
    ("correct_answer", "TEXT"),
    ("difficulty", "VARCHAR(20)"),
]

_NEW_COLUMNS_BY_TABLE = {
    "documents": _DOCUMENT_NEW_COLUMNS,
    "concept_mastery": _CONCEPT_MASTERY_NEW_COLUMNS,
    "quiz_answers": _QUIZ_ANSWER_NEW_COLUMNS,
}


def _migrate_sqlite(sync_conn):
    inspector = inspect(sync_conn)
    tables = set(inspector.get_table_names())
    for table, new_columns in _NEW_COLUMNS_BY_TABLE.items():
        if table not in tables:
            continue
        cols = {c["name"] for c in inspector.get_columns(table)}
        for name, ddl in new_columns:
            if name not in cols:
                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


async def init_db():
    from app.models import document as _document  # noqa: F401
    from app.models import academic as _academic  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_sqlite)
    try:
        from app.services.demo_seed import seed_demo_if_needed
        async with AsyncSessionLocal() as session:
            await seed_demo_if_needed(session)
            await session.commit()
    except Exception as exc:
        print(f"[init_db] demo seed skipped: {exc}")
