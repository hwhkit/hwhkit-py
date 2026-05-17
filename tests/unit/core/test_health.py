"""Tests for hwhkit.core.health."""

from __future__ import annotations

import pytest
from hwhkit.core.health import HealthAggregator, HealthCheck, HealthStatus


class TestHealthStatus:
    def test_ok_factory(self) -> None:
        s = HealthStatus.ok("ok")
        assert s.healthy is True
        assert s.message == "ok"
        assert s.details == {}

    def test_fail_factory(self) -> None:
        s = HealthStatus.fail("db down", details={"err": "refused"})
        assert s.healthy is False
        assert s.details == {"err": "refused"}


class TestHealthCheckProtocol:
    def test_runtime_checkable(self) -> None:
        class C:
            name = "postgres"

            async def health_check(self) -> HealthStatus:
                return HealthStatus.ok()

        assert isinstance(C(), HealthCheck)


class TestHealthAggregator:
    @pytest.mark.asyncio
    async def test_all_healthy(self) -> None:
        agg = HealthAggregator()
        agg.add("a", lambda: HealthStatus.ok())
        agg.add("b", lambda: HealthStatus.ok())
        result = await agg.aggregate()
        assert result.healthy is True
        assert "a" in result.details["checks"]
        assert "b" in result.details["checks"]

    @pytest.mark.asyncio
    async def test_one_unhealthy(self) -> None:
        agg = HealthAggregator()
        agg.add("a", lambda: HealthStatus.ok())
        agg.add("b", lambda: HealthStatus.fail("oops"))
        result = await agg.aggregate()
        assert result.healthy is False
        assert result.details["checks"]["b"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_check_raising_treated_as_unhealthy(self) -> None:
        agg = HealthAggregator()

        def broken() -> HealthStatus:
            raise RuntimeError("kaboom")

        agg.add("broken", broken)
        result = await agg.aggregate()
        assert result.healthy is False
        assert "kaboom" in result.details["checks"]["broken"]["message"]

    @pytest.mark.asyncio
    async def test_async_check(self) -> None:
        async def slow_ok() -> HealthStatus:
            return HealthStatus.ok("slow")

        agg = HealthAggregator()
        agg.add("slow", slow_ok)
        result = await agg.aggregate()
        assert result.healthy is True
