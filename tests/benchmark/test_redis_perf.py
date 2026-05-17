"""Redis benchmark suite — p50/p95/p99 of GET / SET / INCR.

Requires Docker (testcontainers Redis). Tagged ``benchmark`` so the default
``pytest`` run skips them; enable with ``pytest -m benchmark``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hwhkit.integrations.redis import RedisProvider

pytestmark = [pytest.mark.benchmark, pytest.mark.integration]


def test_set_throughput(benchmark, redis_provider: RedisProvider) -> None:
    """Measure SET throughput (single-shot wrapped in async)."""

    async def _set_n(n: int) -> None:
        for i in range(n):
            await redis_provider.set(f"bench:k:{i}", b"x" * 32)

    def runner() -> None:
        asyncio.run(_set_n(100))

    benchmark(runner)


def test_get_latency(benchmark, redis_provider: RedisProvider) -> None:
    """Measure GET latency on a pre-populated key."""

    async def _setup_then_get() -> None:
        await redis_provider.set("bench:hot", b"value")
        for _ in range(100):
            await redis_provider.get("bench:hot")

    def runner() -> None:
        asyncio.run(_setup_then_get())

    benchmark(runner)


def test_incr_atomic(benchmark, redis_provider: RedisProvider) -> None:
    """Measure INCR — atomic counter ops are the canonical Redis use case."""

    async def _incr() -> None:
        for _ in range(100):
            await redis_provider.incr("bench:counter")

    def runner() -> None:
        asyncio.run(_incr())

    benchmark(runner)
