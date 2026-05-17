"""Reusable conformance tests for ``RelationalDb`` contract.

Tests use raw SQL via SQLAlchemy ``text()`` to stay portable across dialects
(sqlite-memory fake + real Postgres/MySQL adapters).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

if TYPE_CHECKING:
    from hwhkit.core.contracts.relational_db import RelationalDb


class RelationalDbContractTests:
    """Inherit and provide an async ``db`` fixture (a ``RelationalDb``)."""

    @pytest.mark.asyncio
    async def test_ping_returns_true(self, db: RelationalDb) -> None:
        assert await db.ping() is True

    @pytest.mark.asyncio
    async def test_session_executes_simple_query(self, db: RelationalDb) -> None:
        async with db.session() as s:
            result = await s.execute(text("SELECT 1 AS x"))
            row = result.first()
            assert row is not None
            assert row.x == 1

    @pytest.mark.asyncio
    async def test_session_commit_rollback(self, db: RelationalDb) -> None:
        async with db.session() as s:
            await s.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS contract_test (id INTEGER PRIMARY KEY, name VARCHAR)"
                )
            )
            await s.execute(text("DELETE FROM contract_test"))
            await s.commit()

        # Insert + rollback
        async with db.session() as s:
            await s.execute(text("INSERT INTO contract_test (id, name) VALUES (1, 'rollback')"))
            await s.rollback()

        # Verify not persisted
        async with db.session() as s:
            result = await s.execute(text("SELECT COUNT(*) AS n FROM contract_test"))
            row = result.first()
            assert row is not None
            assert row.n == 0

        # Insert + commit
        async with db.session() as s:
            await s.execute(text("INSERT INTO contract_test (id, name) VALUES (1, 'committed')"))
            await s.commit()

        # Verify persisted
        async with db.session() as s:
            result = await s.execute(text("SELECT name FROM contract_test WHERE id = 1"))
            row = result.first()
            assert row is not None
            assert row.name == "committed"
            await s.execute(text("DROP TABLE contract_test"))
            await s.commit()
