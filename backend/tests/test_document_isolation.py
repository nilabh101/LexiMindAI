"""Uploaded documents must only be readable by the user who uploaded them."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.models.document import Document


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with Session() as session:
            yield session
            await session.commit()

    async with Session() as session:
        session.add_all([
            _doc(1, "owned.pdf", "user-a"),
            _doc(2, "other.pdf", "user-b"),
            _doc(3, "legacy.pdf", None),
        ])
        await session.commit()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


def _doc(doc_id: int, name: str, user_id):
    return Document(
        id=doc_id, filename=name, original_filename=name, file_type="pdf",
        file_size=10, extracted_text="text", status="READY", user_id=user_id,
    )


@pytest.mark.asyncio
async def test_listing_hides_other_users_documents(client):
    res = await client.get("/api/documents/", headers={"X-User-Id": "user-a"})
    assert res.status_code == 200
    ids = {d["id"] for d in res.json()}
    assert ids == {1, 3}  # own document plus the unowned legacy one


@pytest.mark.asyncio
async def test_fetching_another_users_document_is_refused(client):
    assert (await client.get("/api/documents/2", headers={"X-User-Id": "user-a"})).status_code == 404
    assert (await client.get("/api/documents/1", headers={"X-User-Id": "user-a"})).status_code == 200


@pytest.mark.asyncio
async def test_deleting_and_searching_another_users_document_is_refused(client):
    assert (await client.delete("/api/documents/2", headers={"X-User-Id": "user-a"})).status_code == 404
    res = await client.get(
        "/api/documents/2/search", params={"query": "text"}, headers={"X-User-Id": "user-a"}
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_conflicting_user_ids_are_rejected(client):
    res = await client.get(
        "/api/documents/1", params={"user_id": "user-b"}, headers={"X-User-Id": "user-a"}
    )
    assert res.status_code == 403
