"""Tests for hwhkit.core.context."""

from __future__ import annotations

from typing import ClassVar

import pytest
from hwhkit.core.context import AppContext
from hwhkit.core.contracts import Cache
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from pydantic import BaseModel


class DummyConfig(BaseModel):
    pass


class FakePostgres(IntegrationProvider):
    name: ClassVar[str] = "postgres"
    config_schema: ClassVar[type[BaseModel]] = DummyConfig

    async def setup(self, ctx) -> None: ...
    async def health_check(self) -> HealthStatus:
        return HealthStatus.ok()

    async def shutdown(self) -> None: ...


class FakeRedis(IntegrationProvider):
    name: ClassVar[str] = "redis"
    config_schema: ClassVar[type[BaseModel]] = DummyConfig
    implements: ClassVar[list[type]] = [Cache]

    async def setup(self, ctx) -> None: ...
    async def health_check(self) -> HealthStatus:
        return HealthStatus.ok()

    async def shutdown(self) -> None: ...

    async def get(self, key: str) -> bytes | None:
        return None

    async def set(self, key, value, ttl=None) -> None: ...
    async def delete(self, key) -> bool:
        return True

    async def exists(self, key) -> bool:
        return False

    async def incr(self, key, delta=1) -> int:
        return 0

    async def expire(self, key, ttl) -> bool:
        return True


class FakeRedis2(FakeRedis):
    name: ClassVar[str] = "redis2"


class TestAppContext:
    def test_register_and_get_by_name(self) -> None:
        ctx = AppContext()
        pg = FakePostgres()
        ctx.register(pg)
        assert ctx.get("postgres") is pg

    def test_get_typed(self) -> None:
        ctx = AppContext()
        pg = FakePostgres()
        ctx.register(pg)
        assert ctx.get_typed(FakePostgres) is pg

    def test_get_missing_raises(self) -> None:
        ctx = AppContext()
        with pytest.raises(KeyError):
            ctx.get("nope")

    def test_double_register_raises(self) -> None:
        ctx = AppContext()
        ctx.register(FakePostgres())
        with pytest.raises(ValueError, match="already registered"):
            ctx.register(FakePostgres())

    def test_resolve_contract_via_implements(self) -> None:
        ctx = AppContext()
        redis = FakeRedis()
        ctx.register(redis)
        assert ctx.resolve(Cache) is redis

    def test_explicit_bind_overrides_auto(self) -> None:
        ctx = AppContext()
        r1 = FakeRedis()
        r2 = FakeRedis2()
        ctx.register(r1)
        ctx.register(r2)
        ctx.bind_contract(Cache, "redis2")
        assert ctx.resolve(Cache) is r2

    def test_resolve_unbound_when_multiple_raises(self) -> None:
        ctx = AppContext()
        ctx.register(FakeRedis())
        ctx.register(FakeRedis2())
        with pytest.raises(LookupError, match="multiple"):
            ctx.resolve(Cache)

    def test_resolve_unimplemented_contract_raises(self) -> None:
        ctx = AppContext()
        ctx.register(FakePostgres())
        with pytest.raises(LookupError, match="No integration implements"):
            ctx.resolve(Cache)

    def test_bind_unknown_provider_raises(self) -> None:
        ctx = AppContext()
        with pytest.raises(KeyError):
            ctx.bind_contract(Cache, "ghost")

    def test_integrations_property_is_copy(self) -> None:
        ctx = AppContext()
        pg = FakePostgres()
        ctx.register(pg)
        snap = ctx.integrations
        snap.clear()
        assert "postgres" in ctx.integrations
