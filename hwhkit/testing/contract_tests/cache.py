"""Reusable conformance tests for ``Cache`` contract.

Any adapter (Redis, Memcached, in-memory fake) must pass these tests to be
considered Cache-compliant.

Usage::

    class TestMyCacheContract(CacheContractTests):
        @pytest.fixture
        async def cache(self) -> Cache:
            yield my_cache_impl
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hwhkit.core.contracts.cache import Cache


class CacheContractTests:
    """Inherit and provide an async ``cache`` fixture.

    All tests assume the cache is empty at start of each test (caller's
    responsibility to provision via fixture cleanup).
    """

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self, cache: Cache) -> None:
        assert await cache.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_set_then_get(self, cache: Cache) -> None:
        await cache.set("k", b"value")
        assert await cache.get("k") == b"value"

    @pytest.mark.asyncio
    async def test_overwrite(self, cache: Cache) -> None:
        await cache.set("k", b"v1")
        await cache.set("k", b"v2")
        assert await cache.get("k") == b"v2"

    @pytest.mark.asyncio
    async def test_delete_existing(self, cache: Cache) -> None:
        await cache.set("k", b"v")
        assert await cache.delete("k") is True
        assert await cache.get("k") is None

    @pytest.mark.asyncio
    async def test_delete_missing(self, cache: Cache) -> None:
        assert await cache.delete("nope") is False

    @pytest.mark.asyncio
    async def test_exists(self, cache: Cache) -> None:
        assert await cache.exists("k") is False
        await cache.set("k", b"v")
        assert await cache.exists("k") is True

    @pytest.mark.asyncio
    async def test_ttl_expiry(self, cache: Cache) -> None:
        await cache.set("k", b"v", ttl=timedelta(milliseconds=50))
        assert await cache.get("k") == b"v"
        await asyncio.sleep(0.1)
        assert await cache.get("k") is None

    @pytest.mark.asyncio
    async def test_incr_from_missing(self, cache: Cache) -> None:
        assert await cache.incr("counter") == 1

    @pytest.mark.asyncio
    async def test_incr_increment(self, cache: Cache) -> None:
        assert await cache.incr("counter") == 1
        assert await cache.incr("counter") == 2
        assert await cache.incr("counter", delta=5) == 7

    @pytest.mark.asyncio
    async def test_expire_on_existing(self, cache: Cache) -> None:
        await cache.set("k", b"v")
        ok = await cache.expire("k", timedelta(seconds=30))
        assert ok is True

    @pytest.mark.asyncio
    async def test_expire_on_missing(self, cache: Cache) -> None:
        ok = await cache.expire("nope", timedelta(seconds=30))
        assert ok is False
