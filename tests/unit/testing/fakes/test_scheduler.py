"""Tests for FakeScheduler."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from hwhkit.testing.fakes.scheduler import FakeScheduler


@pytest.mark.asyncio
async def test_add_cron_then_run() -> None:
    s = FakeScheduler()
    called: list[bool] = []

    async def job() -> None:
        called.append(True)

    s.add_cron_job("c", "* * * * *", job, lock_key="lk")
    await s.run("c")
    assert called == [True]
    spec = s.jobs["c"]
    assert spec.kind == "cron"
    assert spec.lock_key == "lk"


@pytest.mark.asyncio
async def test_add_interval() -> None:
    s = FakeScheduler()
    s.add_interval_job("i", timedelta(seconds=30), _noop)
    assert s.jobs["i"].kind == "interval"
    assert s.jobs["i"].spec["interval"] == timedelta(seconds=30)


@pytest.mark.asyncio
async def test_add_oneshot() -> None:
    s = FakeScheduler()
    when = datetime(2030, 1, 1)
    s.add_oneshot_job("o", when, _noop)
    assert s.jobs["o"].kind == "oneshot"
    assert s.jobs["o"].spec["run_at"] == when


@pytest.mark.asyncio
async def test_remove_returns_status() -> None:
    s = FakeScheduler()
    s.add_interval_job("x", timedelta(seconds=1), _noop)
    assert s.remove_job("x") is True
    assert s.remove_job("x") is False


@pytest.mark.asyncio
async def test_start_stop_state() -> None:
    s = FakeScheduler()
    assert s.started is False
    await s.start()
    assert s.started is True
    await s.stop()
    assert s.started is False


async def _noop() -> None:
    pass
