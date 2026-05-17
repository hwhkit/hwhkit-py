"""Tests for hwhkit.core.integration."""

from __future__ import annotations

from typing import ClassVar

import pytest
from hwhkit.core.contracts import Cache
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from pydantic import BaseModel


class DummyConfig(BaseModel):
    enabled: bool = True


class DummyProvider(IntegrationProvider):
    name: ClassVar[str] = "dummy"
    config_schema: ClassVar[type[BaseModel]] = DummyConfig

    def __init__(self) -> None:
        self.setup_called = False
        self.shutdown_called = False

    async def setup(self, ctx) -> None:
        self.setup_called = True

    async def health_check(self) -> HealthStatus:
        return HealthStatus.ok()

    async def shutdown(self) -> None:
        self.shutdown_called = True


class TestIntegrationProvider:
    def test_concrete_subclass_instantiates(self) -> None:
        p = DummyProvider()
        assert p.name == "dummy"
        assert p.config_schema is DummyConfig
        assert p.implements == []

    @pytest.mark.asyncio
    async def test_lifecycle(self) -> None:
        p = DummyProvider()
        await p.setup(ctx=None)
        assert p.setup_called is True
        assert (await p.health_check()).healthy is True
        await p.shutdown()
        assert p.shutdown_called is True

    def test_missing_abstract_method_cannot_instantiate(self) -> None:
        class Incomplete(IntegrationProvider):
            name: ClassVar[str] = "x"
            config_schema: ClassVar[type[BaseModel]] = DummyConfig

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_default_hooks_no_op(self) -> None:
        p = DummyProvider()
        assert p.fastapi_router() is None
        assert p.fastapi_middlewares() == []
        assert p.fastapi_dependencies() == {}

    def test_implements_declaration(self) -> None:
        class CacheImpl(DummyProvider):
            name: ClassVar[str] = "cache_impl"
            implements: ClassVar[list[type]] = [Cache]

        assert Cache in CacheImpl().implements
