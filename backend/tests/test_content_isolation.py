"""Content derived from an uploaded PDF inherits that PDF's owner.

Notes, questions, chunks, search, retrieval, the tutor and adaptive quizzes must
never surface another user's uploaded material. Rows with no source document
(seeded curriculum/demo data) stay visible to everyone.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.models.academic import AcademicNote, DocumentChunk, Question
from app.models.document import Document

OWNER = "user-a"
OTHER = "user-b"


def _doc(doc_id: int, name: str, user_id):
    return Document(
        id=doc_id, filename=name, original_filename=name, file_type="pdf",
        file_size=10, extracted_text="euler theorem text", status="READY", user_id=user_id,
    )


def _note(note_id: int, title: str, doc_id):
    return AcademicNote(
        id=note_id, title=title, subject_id="em1-btech", concept_id="euler-theorem-dc",
        content="Euler theorem content", summary="Euler theorem summary",
        source="SOURCE_DERIVED", source_document_id=doc_id,
    )


def _question(qid: int, text: str, doc_id):
    return Question(
        id=qid, document_id=doc_id, question_text=text, question_type="MCQ",
        options=["a", "b"], answer="a", review_status="APPROVED", source="PYQ",
        difficulty="EASY", subject_id="em1-btech", concept_id="euler-theorem-dc",
    )


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        session.add_all([
            _doc(1, "mine.pdf", OWNER),
            _doc(2, "theirs.pdf", OTHER),
            _note(1, "euler mine", 1),
            _note(2, "euler theirs", 2),
            _note(3, "euler seeded", None),
            _question(1, "euler question mine", 1),
            _question(2, "euler question theirs", 2),
            _question(3, "euler question seeded", None),
            DocumentChunk(id=1, document_id=1, text="euler chunk mine"),
            DocumentChunk(id=2, document_id=2, text="euler chunk theirs"),
        ])
        await session.commit()

    async def override_get_db():
        async with Session() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


H = {"X-User-Id": OWNER}


@pytest.mark.asyncio
async def test_notes_list_excludes_other_users_documents(client):
    res = await client.get("/api/notes", headers=H)
    assert res.status_code == 200
    assert {n["id"] for n in res.json()} == {1, 3}


@pytest.mark.asyncio
async def test_note_detail_of_other_user_is_refused(client):
    assert (await client.get("/api/notes/2", headers=H)).status_code == 404
    assert (await client.get("/api/notes/1", headers=H)).status_code == 200
    assert (await client.get("/api/notes/3", headers=H)).status_code == 200


@pytest.mark.asyncio
async def test_questions_list_excludes_other_users_documents(client):
    res = await client.get("/api/questions", headers=H)
    assert res.status_code == 200
    assert {q["id"] for q in res.json()} == {1, 3}


@pytest.mark.asyncio
async def test_search_excludes_other_users_content(client):
    res = await client.get("/api/search", params={"q": "euler"}, headers=H)
    assert res.status_code == 200
    data = res.json()
    assert {n["id"] for n in data["notes"]} == {1, 3}
    assert {q["id"] for q in data["questions"]} == {1, 3}
    assert {d["id"] for d in data.get("documents", [])} == {1}
    assert all(c["documentId"] != 2 for c in data.get("chunks", []))


@pytest.mark.asyncio
async def test_retrieval_excludes_other_users_chunks(client):
    res = await client.get("/api/retrieve", params={"query": "euler"}, headers=H)
    assert res.status_code == 200
    body = res.text
    assert "chunk theirs" not in body
    assert "question theirs" not in body


@pytest.mark.asyncio
async def test_document_detail_of_other_user_is_refused(client):
    assert (await client.get("/api/documents/2/detail", headers=H)).status_code == 404
    assert (await client.get("/api/documents/1/detail", headers=H)).status_code == 200


@pytest.mark.asyncio
async def test_tutor_actions_never_use_other_users_material(client):
    for action in ("EXPLAIN", "TEST_ME", "SIMILAR_QUESTION"):
        res = await client.post("/api/ai/tutor", json={
            "message": "Explain Euler's theorem",
            "user_id": OWNER,
            "subject_id": "em1-btech",
            "concept_id": "euler-theorem-dc",
            "action": action,
        }, headers=H)
        assert res.status_code == 200, action
        body = res.text
        assert "theirs" not in body, action


@pytest.mark.asyncio
async def test_adaptive_quiz_never_selects_other_users_questions(client):
    res = await client.post("/api/quizzes/adaptive", json={
        "user_id": OWNER,
        "subject_id": "em1-btech",
        "concept_id": "euler-theorem-dc",
        "question_count": 5,
    }, headers=H)
    assert res.status_code == 200
    ids = {q["id"] for q in res.json()["questions"]}
    assert 2 not in ids
    assert ids <= {1, 3}
