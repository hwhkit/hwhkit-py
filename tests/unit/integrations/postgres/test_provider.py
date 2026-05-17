"""Unit tests for PostgresProvider (no real DB)."""

from __future__ import annotations

from typing import ClassVar

import pytest
from hwhkit.core.context import AppContext
from hwhkit.core.contracts.relational_db import RelationalDb
from hwhkit.core.errors import DbConnectionError
from hwhkit.integrations.postgres import PostgresConfig, PostgresProvider
from pydantic import BaseModel


def test_provider_metadata() -> None:
    p = PostgresProvider()
    assert p.name == "postgres"
    assert p.config_schema is PostgresConfig


def test_provider_implements_relational_db_contract() -> None:
    p = PostgresProvider()
    assert RelationalDb in p.implements


def test_engine_access_before_setup_raises() -> None:
    p = PostgresProvider()
    with pytest.raises(DbConnectionError, match="before setup"):
        _ = p.engine


def test_session_before_setup_raises() -> None:
    p = PostgresProvider()
    with pytest.raises(DbConnectionError, match="before setup"):
        p.session()


@pytest.mark.asyncio
async def test_ping_returns_false_when_no_engine() -> None:
    p = PostgresProvider()
    assert await p.ping() is False


@pytest.mark.asyncio
async def test_health_check_fails_when_not_ready() -> None:
    p = PostgresProvider()
    status = await p.health_check()
    assert status.healthy is False


def test_resolve_config_explicit_wins() -> None:
    explicit = PostgresConfig(dsn="postgresql+asyncpg://x:y@h:5432/db")
    p = PostgresProvider(config=explicit)
    # Ctx has no postgres attr; explicit should win
    ctx = AppContext()

    class _S(BaseModel):
        pass

    ctx.config = _S()  # type: ignore[assignment]
    resolved = p._resolve_config(ctx)
    assert resolved.dsn == "postgresql+asyncpg://x:y@h:5432/db"


def test_resolve_config_from_ctx() -> None:
    from pydantic import Field

    class _ConfigWithPg(BaseModel):
        postgres: PostgresConfig = Field(
            default_factory=lambda: PostgresConfig(dsn="postgresql+asyncpg://from-ctx:p@h/db")
        )

    p = PostgresProvider()
    ctx = AppContext()
    ctx.config = _ConfigWithPg()  # type: ignore[assignment]
    resolved = p._resolve_config(ctx)
    assert "from-ctx" in resolved.dsn


def test_resolve_config_defaults() -> None:
    class _NoPg(BaseModel):
        pass

    p = PostgresProvider()
    ctx = AppContext()
    ctx.config = _NoPg()  # type: ignore[assignment]
    resolved = p._resolve_config(ctx)
    assert isinstance(resolved, PostgresConfig)


class _ProviderForAbstractTest(PostgresProvider):
    name: ClassVar[str] = "postgres-test"
