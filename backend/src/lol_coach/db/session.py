from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from lol_coach.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Async engine using NullPool — each session opens a fresh connection.

    NullPool avoids cross-event-loop pool reuse issues with TestClient and
    short-lived CLI runs. For higher-throughput server use, switch to the
    default pool inside an app lifespan.
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Async context manager wrapping a transactional unit of work."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
