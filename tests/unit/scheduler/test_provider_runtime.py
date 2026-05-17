"""Exercise SchedulerProvider runtime paths (scheduler start/stop, lock wrap)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

import pytest
from hwhkit.config.base import Settings
from hwhkit.core.context import AppContext
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.scheduler import SchedulerProvider
from pydantic import BaseModel


class _DummyConfig(BaseModel):
    pass


@pytest.mark.asyncio
async def test_health_check_running_state() -> None:
    p = SchedulerProvider()
    ctx = AppContext()
    ctx.config = Settings()
    await p.setup(ctx)
    await p.start()
    status = await p.health_check()
    assert status.healthy is True
    assert "running" in status.message.lower()
    await p.stop()
    await p.shutdown()


@pytest.mark.asyncio
async def test_add_cron_then_remove() -> None:
    p = SchedulerProvider()
    ctx = AppContext()
    ctx.config = Settings()
    await p.setup(ctx)

    async def job() -> None:
        pass

    p.add_cron_job("hourly", "0 * * * *", job, timezone="UTC")
    assert p.remove_job("hourly") is True
    assert p.remove_job("hourly") is False
    await p.shutdown()


@pytest.mark.asyncio
async def test_add_oneshot() -> None:
    p = SchedulerProvider()
    ctx = AppContext()
    ctx.config = Settings()
    await p.setup(ctx)

    async def job() -> None:
        pass

    future = datetime(2099, 1, 1, tzinfo=UTC)
    p.add_oneshot_job("oneshot", future, job)
    assert p.remove_job("oneshot") is True
    await p.shutdown()


@pytest.mark.asyncio
async def test_lock_wrap_no_lock_provider_runs_unguarded() -> None:
    """When lock_key is set but no DistributedLock in ctx, job still runs."""
    from hwhkit.scheduler.provider import SchedulerProvider as SP

    p = SP()
    ctx = AppContext()
    ctx.config = Settings()
    await p.setup(ctx)

    called: list[int] = []

    async def job() -> None:
        called.append(1)

    wrapped = p._wrap_with_lock("job-id", job, "some-lock-key")
    await wrapped()
    assert called == [1]
    await p.shutdown()


@pytest.mark.asyncio
async def test_lock_wrap_with_held_lock_skips() -> None:
    """When lock acquire returns None (held elsewhere), job is skipped."""

    class _AlwaysHeldLock(IntegrationProvider):
        from hwhkit.core.contracts.lock import DistributedLock as _DL

        name: ClassVar[str] = "lock"
        config_schema: ClassVar[type[BaseModel]] = _DummyConfig
        implements: ClassVar[list[type]] = [_DL]

        async def setup(self, ctx) -> None: ...
        async def health_check(self) -> HealthStatus:
            return HealthStatus.ok()

        async def shutdown(self) -> None: ...
        async def acquire(self, key, ttl, blocking=True):
            return None

        async def release(self, token) -> bool:
            return False

        async def extend(self, token, ttl) -> bool:
            return False

    p = SchedulerProvider()
    ctx = AppContext()
    ctx.config = Settings()
    ctx.register(_AlwaysHeldLock())
    await p.setup(ctx)

    called: list[int] = []

    async def job() -> None:
        called.append(1)

    wrapped = p._wrap_with_lock("job-id", job, "some-lock-key")
    await wrapped()
    assert called == []  # held elsewhere → skipped
    await p.shutdown()


def test_resolve_config_from_ctx() -> None:
    from hwhkit.scheduler.config import SchedulerConfig

    class _S(BaseModel):
        scheduler: SchedulerConfig = SchedulerConfig(timezone="Asia/Shanghai")

    p = SchedulerProvider()
    ctx = AppContext()
    ctx.config = _S()  # type: ignore[assignment]
    cfg = p._resolve_config(ctx)
    assert cfg.timezone == "Asia/Shanghai"
