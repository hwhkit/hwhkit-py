"""PostgresProvider — async SQLAlchemy 2.0 adapter implementing ``RelationalDb``.

Lazy-imports SQLAlchemy / asyncpg so the module is importable without the
``[postgres]`` extra installed (only ``setup()`` will fail with a clear hint).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from hwhkit.core.errors import DbConnectionError
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.integrations.postgres.config import PostgresConfig

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext
    from hwhkit.core.contracts.relational_db import Session  # noqa: F401

_logger = logging.getLogger(__name__)


class PostgresProvider(IntegrationProvider):
    """SQLAlchemy 2.0 async engine + session factory.

    Implements ``RelationalDb`` contract via ``session()`` and ``ping()``.
    """

    name: ClassVar[str] = "postgres"
    config_schema: ClassVar[type[BaseModel]] = PostgresConfig

    # implements is wired by inspecting MRO at AppContext.resolve time, but
    # we declare it explicitly to support implements-based contract binding.
    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        from hwhkit.core.contracts.relational_db import RelationalDb

        return [RelationalDb]

    def __init__(self, config: PostgresConfig | None = None) -> None:
        self._config = config
        self._engine: Any = None  # AsyncEngine, set in setup()
        self._session_factory: Any = None  # async_sessionmaker
        self._is_ready: bool = False

    @property
    def engine(self) -> Any:
        """Underlying SQLAlchemy AsyncEngine (escape hatch for adapter-specific code)."""
        if self._engine is None:
            raise DbConnectionError("PostgresProvider.engine accessed before setup()")
        return self._engine

    async def setup(self, ctx: AppContext) -> None:
        """Create the AsyncEngine + session factory; verify connectivity."""
        cfg = self._resolve_config(ctx)
        try:
            from sqlalchemy.ext.asyncio import (
                AsyncSession,
                async_sessionmaker,
                create_async_engine,
            )
        except ImportError as exc:
            raise ImportError(
                "PostgresProvider requires hwhkit[postgres] extras: pip install 'hwhkit[postgres]'"
            ) from exc

        self._engine = create_async_engine(
            cfg.dsn,
            pool_size=cfg.pool_size,
            max_overflow=cfg.max_overflow,
            pool_pre_ping=cfg.pool_pre_ping,
            pool_recycle=cfg.pool_recycle_seconds,
            echo=cfg.echo,
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        # Warm-up ping so a bad DSN fails-fast at boot rather than first request.
        if not await self.ping():
            raise DbConnectionError(f"Cannot connect to Postgres at {cfg.dsn}")
        self._is_ready = True

        # Best-effort OTel instrumentation; tolerated if extras missing.
        try:
            from hwhkit.observability.instrumentation import (
                auto_instrument_sqlalchemy,
            )

            auto_instrument_sqlalchemy(self._engine)
        except Exception as exc:
            _logger.debug("SQLAlchemy auto-instrumentation skipped: %s", exc)

    async def shutdown(self) -> None:
        """Dispose the engine; releases all pooled connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
        self._is_ready = False

    async def health_check(self) -> HealthStatus:
        """Lightweight ``SELECT 1`` to verify connectivity."""
        if not self._is_ready or self._engine is None:
            return HealthStatus.fail("postgres provider not ready")
        if await self.ping():
            return HealthStatus.ok("postgres reachable")
        return HealthStatus.fail("postgres unreachable")

    async def ping(self) -> bool:
        """``RelationalDb`` contract method — quick connectivity probe."""
        if self._engine is None:
            return False
        try:
            from sqlalchemy import text

            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            _logger.warning("postgres ping failed: %s", exc)
            return False

    def session(self) -> Any:
        """``RelationalDb`` contract — return an ``AsyncSession`` context manager.

        Usage::

            async with provider.session() as s:
                result = await s.execute(text("SELECT ..."))
                await s.commit()
        """
        if self._session_factory is None:
            raise DbConnectionError("PostgresProvider.session() called before setup()")
        return self._session_factory()

    # ---- internals --------------------------------------------------------
    def _resolve_config(self, ctx: AppContext) -> PostgresConfig:
        if self._config is not None:
            return self._config
        # Look for ``postgres`` section on the AppContext's settings.
        cfg = getattr(ctx.config, "postgres", None)
        if isinstance(cfg, PostgresConfig):
            return cfg
        return PostgresConfig()  # defaults


__all__ = ["PostgresProvider"]
