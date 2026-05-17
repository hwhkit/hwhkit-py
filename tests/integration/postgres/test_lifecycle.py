"""Lifecycle + connection tests against a real Postgres container."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

if TYPE_CHECKING:
    from hwhkit.integrations.postgres import PostgresProvider

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_setup_then_ping(postgres_provider: PostgresProvider) -> None:
    status = await postgres_provider.health_check()
    assert status.healthy is True


@pytest.mark.asyncio
async def test_session_executes_query(postgres_provider: PostgresProvider) -> None:
    async with postgres_provider.session() as s:
        result = await s.execute(text("SELECT 42 AS answer"))
        row = result.first()
        assert row is not None
        assert row.answer == 42


@pytest.mark.asyncio
async def test_session_create_insert_select(postgres_provider: PostgresProvider) -> None:
    async with postgres_provider.session() as s:
        await s.execute(text("CREATE TABLE smoke (id INT PRIMARY KEY, name VARCHAR)"))
        await s.execute(text("INSERT INTO smoke (id, name) VALUES (1, 'alice')"))
        await s.commit()
        result = await s.execute(text("SELECT name FROM smoke WHERE id = 1"))
        row = result.first()
        assert row is not None
        assert row.name == "alice"
        await s.execute(text("DROP TABLE smoke"))
        await s.commit()


@pytest.mark.asyncio
async def test_rollback_on_exception(postgres_provider: PostgresProvider) -> None:
    async with postgres_provider.session() as s:
        await s.execute(
            text("CREATE TABLE IF NOT EXISTS rollback_test (id INT PRIMARY KEY, val VARCHAR)")
        )
        await s.execute(text("DELETE FROM rollback_test"))
        await s.commit()

    try:
        async with postgres_provider.session() as s:
            await s.execute(text("INSERT INTO rollback_test (id, val) VALUES (1, 'in-tx')"))
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    async with postgres_provider.session() as s:
        result = await s.execute(text("SELECT COUNT(*) AS n FROM rollback_test"))
        row = result.first()
        assert row is not None
        # The insert should be rolled back since session was not committed
        # before the exception. SQLAlchemy auto-rollback on context exit.
        assert row.n == 0
        await s.execute(text("DROP TABLE rollback_test"))
        await s.commit()
