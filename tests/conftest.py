"""Shared test fixtures.

Environment is set before any ``src`` import so the cached settings point
to a temporary SQLite database and temp data dirs.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker

_tmp = tempfile.mkdtemp(prefix="pvsim-test-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/test.db"
os.environ["LOAD_PROFILES_DIR"] = str(Path(_tmp) / "profiles")
os.environ["SIMULATION_DATA_DIR"] = str(Path(_tmp) / "simdata")
os.environ["APP_PASSWORD"] = "test-password"
os.environ["APP_SECRET_KEY"] = "test-secret-key"

from src.web.database import engine  # noqa: E402
from src.web.main import app  # noqa: E402
from src.web.models import Base  # noqa: E402


class _FakeArq:
    """Minimal stand-in for the arq pool (no Redis in tests)."""

    def __init__(self) -> None:
        self.enqueued: list[tuple[str, tuple]] = []

    async def enqueue_job(self, name: str, *args: object) -> None:
        self.enqueued.append((name, args))

    async def aclose(self) -> None:
        return None


@pytest.fixture
def fake_arq() -> _FakeArq:
    return _FakeArq()


@pytest_asyncio.fixture
async def client(monkeypatch, fake_arq: _FakeArq):
    """httpx async client with the app lifespan and fresh SQLite tables."""

    async def _fake_create_pool(*args: object, **kwargs: object) -> _FakeArq:
        return fake_arq

    monkeypatch.setattr("src.web.main.create_pool", _fake_create_pool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    await engine.dispose()


@pytest_asyncio.fixture
async def logged_client(client):
    """Client authenticated with the single app password."""
    resp = await client.post("/login", data={"password": "test-password"})
    assert resp.status_code == 303
    return client


@pytest_asyncio.fixture
async def db_session():
    """A direct async session for seeding test data."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
