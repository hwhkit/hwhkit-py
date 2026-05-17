"""Postgres benchmark suite — session acquire + simple SELECT round-trip."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

if TYPE_CHECKING:
    from hwhkit.integrations.postgres import PostgresProvider

pytestmark = [pytest.mark.benchmark, pytest.mark.integration]


def test_session_acquire_release(benchmark, postgres_provider: PostgresProvider) -> None:
    """How fast can we open + close N async sessions?"""

    async def _churn() -> None:
        for _ in range(50):
            async with postgres_provider.session() as s:
                _ = s

    def runner() -> None:
        asyncio.run(_churn())

    benchmark(runner)


def test_select_1_roundtrip(benchmark, postgres_provider: PostgresProvider) -> None:
    """SELECT 1 latency — pure round-trip cost."""

    async def _roundtrip() -> None:
        async with postgres_provider.session() as s:
            for _ in range(50):
                await s.execute(text("SELECT 1"))

    def runner() -> None:
        asyncio.run(_roundtrip())

    benchmark(runner)
