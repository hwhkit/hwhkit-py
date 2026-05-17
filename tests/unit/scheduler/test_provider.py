"""Unit tests for SchedulerProvider (no real APScheduler runs)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from hwhkit.config.base import Settings
from hwhkit.core.context import AppContext
from hwhkit.scheduler import SchedulerConfig, SchedulerProvider


def test_provider_metadata() -> None:
    p = SchedulerProvider()
    assert p.name == "scheduler"
    assert p.config_schema is SchedulerConfig


def test_implements_scheduler_contract() -> None:
    from hwhkit.core.contracts.scheduler import Scheduler

    assert Scheduler in SchedulerProvider().implements


def test_require_scheduler_before_use() -> None:
    p = SchedulerProvider()
    with pytest.raises(RuntimeError, match="not initialized"):
        p.add_interval_job("x", timedelta(seconds=1), _noop)


@pytest.mark.asyncio
async def test_setup_creates_apscheduler() -> None:
    ctx = AppContext()
    ctx.config = Settings()
    p = SchedulerProvider()
    await p.setup(ctx)
    assert p._scheduler is not None
    await p.shutdown()


@pytest.mark.asyncio
async def test_add_then_remove_job() -> None:
    ctx = AppContext()
    ctx.config = Settings()
    p = SchedulerProvider()
    await p.setup(ctx)
    p.add_interval_job("test-job", timedelta(seconds=60), _noop)
    assert p.remove_job("test-job") is True
    assert p.remove_job("test-job") is False
    await p.shutdown()


@pytest.mark.asyncio
async def test_health_check_states() -> None:
    p = SchedulerProvider()
    assert (await p.health_check()).healthy is False

    ctx = AppContext()
    ctx.config = Settings()
    await p.setup(ctx)
    status = await p.health_check()
    assert status.healthy is True  # initialized but not started is healthy
    await p.shutdown()


def test_cron_parsing_invalid() -> None:
    from hwhkit.scheduler.provider import _parse_cron

    with pytest.raises(ValueError, match="5 fields"):
        _parse_cron("* * *")


def test_cron_parsing_valid() -> None:
    from hwhkit.scheduler.provider import _parse_cron

    parsed = _parse_cron("0 */1 * * *")
    assert parsed["minute"] == "0"
    assert parsed["hour"] == "*/1"


async def _noop() -> None:
    pass
