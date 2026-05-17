"""In-memory ``RelationalDb`` fake using aiosqlite.

Real SQL parser + transactions, just not Postgres-specific features
(JSONB, ON CONFLICT RETURNING, etc.). Good enough for business unit tests
of Repository/service-layer code.
"""

from __future__ import annotations

from typing import Any


class FakeRelationalDb:
    """In-memory SQLite + SQLAlchemy AsyncSession factory."""

    def __init__(self, url: str = "sqlite+aiosqlite:///:memory:") -> None:
        self._url = url
        self._engine: Any = None
        self._session_factory: Any = None

    async def _ensure_engine(self) -> Any:
        if self._engine is None:
            from sqlalchemy.ext.asyncio import (
                AsyncSession,
                async_sessionmaker,
                create_async_engine,
            )

            self._engine = create_async_engine(self._url, future=True)
            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._engine

    async def ping(self) -> bool:
        try:
            from sqlalchemy import text

            engine = await self._ensure_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def session(self) -> Any:
        """Return an AsyncSession context manager.

        Note: must call ``ensure_engine`` first via async helper; first call
        materializes the engine lazily on first session() use.
        """
        if self._session_factory is None:
            # Synchronous fallback: create eagerly on first call. The engine
            # construction itself is sync; only operations on it are async.
            from sqlalchemy.ext.asyncio import (
                AsyncSession,
                async_sessionmaker,
                create_async_engine,
            )

            self._engine = create_async_engine(self._url, future=True)
            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._session_factory()

    async def aclose(self) -> None:
        """Dispose the engine; test cleanup."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


__all__ = ["FakeRelationalDb"]
