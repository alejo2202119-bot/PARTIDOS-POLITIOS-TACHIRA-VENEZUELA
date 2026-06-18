"""Async SQLAlchemy 2.0 engine, session factory and FastAPI dependency.

Design goals:
    * NEVER crash the app at import time if the DB is down. The engine is
      created lazily on first use, so importing this module is always safe.
    * Provide an async ``ping()`` for the ``/health`` endpoint.
    * Hand out request-scoped ``AsyncSession`` instances via ``get_session``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger("vpid.database")

# Lazily-initialised globals. They stay ``None`` until the first DB access so
# that a missing/unreachable database does not break process startup.
_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """Declarative base for all ORM models (SQLAlchemy 2.0 typed style)."""


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, creating it on first call.

    ``create_async_engine`` does not open a connection — it only builds the
    pool — so this is safe to call even when Postgres is unavailable.
    """
    global _engine
    if _engine is None:
        logger.debug("Creating async engine for %s", _redacted_url())
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,  # transparently recycle dead connections
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the cached async session factory, building it on first call."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped session.

    The session is rolled back and closed automatically. Route handlers are
    expected to tolerate DB errors and fall back to demo data, so this does not
    swallow exceptions — it only guarantees cleanup.
    """
    factory = get_sessionmaker()
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def ping() -> bool:
    """Return ``True`` if a trivial ``SELECT 1`` succeeds, else ``False``.

    Never raises — used by the health check and by route fallbacks to decide
    whether the database is reachable.
    """
    from sqlalchemy import text

    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.warning("Database ping failed: %s", exc)
        return False


async def dispose_engine() -> None:
    """Dispose of the engine's connection pool (called on app shutdown)."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        logger.debug("Async engine disposed")
    _engine = None
    _sessionmaker = None


def _redacted_url() -> str:
    """Return the DATABASE_URL with any password redacted, for logging."""
    url = settings.DATABASE_URL
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        creds, host = rest.split("@", 1)
        user = creds.split(":", 1)[0]
        return f"{scheme}://{user}:***@{host}"
    return url
