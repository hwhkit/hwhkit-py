"""Lifecycle + connection tests against a real Redis container."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hwhkit.integrations.redis import RedisProvider

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_setup_then_ping(redis_provider: RedisProvider) -> None:
    status = await redis_provider.health_check()
    assert status.healthy is True


@pytest.mark.asyncio
async def test_set_get_bytes(redis_provider: RedisProvider) -> None:
    await redis_provider.set("smoke", b"value")
    assert await redis_provider.get("smoke") == b"value"


@pytest.mark.asyncio
async def test_keys_listing(redis_provider: RedisProvider) -> None:
    await redis_provider.set("user:1", b"a")
    await redis_provider.set("user:2", b"b")
    await redis_provider.set("other:x", b"c")
    user_keys = await redis_provider.list_keys("user:")
    assert sorted(user_keys) == ["user:1", "user:2"]
