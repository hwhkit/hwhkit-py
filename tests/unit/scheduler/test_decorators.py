"""Tests for @scheduled_task decorator + registry."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from hwhkit.scheduler.decorators import (
    _REGISTRY,
    _clear_registry,
    register_scheduled_tasks,
    scheduled_task,
)


@pytest.fixture(autouse=True)
def _reset_registry() -> Any:
    _clear_registry()
    yield
    _clear_registry()


def test_requires_exactly_one_schedule_arg() -> None:
    with pytest.raises(ValueError, match="exactly one"):

        @scheduled_task()  # type: ignore[call-overload]
        async def no_schedule() -> None:
            pass


def test_rejects_two_schedule_args() -> None:
    with pytest.raises(ValueError, match="exactly one"):

        @scheduled_task(cron="* * * * *", interval=timedelta(seconds=1))
        async def both() -> None:
            pass


def test_rejects_sync_function() -> None:
    with pytest.raises(TypeError, match="must be async"):

        @scheduled_task(cron="* * * * *")
        def sync_fn() -> None:  # type: ignore[misc]
            pass


def test_registers_cron_in_registry() -> None:
    @scheduled_task(cron="0 * * * *", lock_key="my-job")
    async def hourly() -> None:
        pass

    assert len(_REGISTRY) == 1
    spec = _REGISTRY[0]
    assert spec.cron == "0 * * * *"
    assert spec.lock_key == "my-job"


def test_registers_interval() -> None:
    @scheduled_task(interval=timedelta(seconds=30))
    async def every_30s() -> None:
        pass

    assert _REGISTRY[0].interval == timedelta(seconds=30)


def test_registers_oneshot() -> None:
    when = datetime(2030, 1, 1, 12, 0, 0)

    @scheduled_task(run_at=when)
    async def at_time() -> None:
        pass

    assert _REGISTRY[0].run_at == when


def test_job_id_defaults_to_qualname() -> None:
    @scheduled_task(cron="* * * * *")
    async def my_unique_job_name() -> None:
        pass

    assert any("my_unique_job_name" in s.job_id for s in _REGISTRY)


def test_explicit_job_id() -> None:
    @scheduled_task(cron="* * * * *", job_id="custom-id")
    async def some_job() -> None:
        pass

    assert any(s.job_id == "custom-id" for s in _REGISTRY)


@pytest.mark.asyncio
async def test_register_no_scheduler_is_noop() -> None:
    from hwhkit.core.context import AppContext

    @scheduled_task(interval=timedelta(seconds=10))
    async def task(ctx: AppContext) -> None:
        pass

    ctx = AppContext()
    # No SchedulerProvider registered — should not raise
    await register_scheduled_tasks(ctx)
