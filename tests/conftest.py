"""Test fixtures for the daily-song smoke suite.

Env vars are set BEFORE importing any ``app`` module because
``app.config`` (pydantic-settings) reads them at import time and
``app.db`` builds the engine from them.

The DB fixture uses an in-memory SQLite with a ``StaticPool`` so the
single shared connection sees the tables created by ``create_all``
(a fresh connection per checkout would start with an empty DB).
"""
import os

os.environ.setdefault("BOT_TOKEN", "123:test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OWNER_ID", "1")

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base
import app.models  # noqa: F401  (registers tables on Base.metadata)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()
