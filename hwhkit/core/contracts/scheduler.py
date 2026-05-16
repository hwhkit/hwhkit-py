"""Scheduler contract — recurring & one-off job execution.

Implementations: APScheduler (P0), Celery-beat / Temporal (future).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable

JobFunc = Callable[[], Awaitable[None]]


@runtime_checkable
class Scheduler(Protocol):
    def add_cron_job(
        self,
        job_id: str,
        cron: str,
        func: JobFunc,
        *,
        lock_key: str | None = None,
        timezone: str = "UTC",
    ) -> None: ...

    def add_interval_job(
        self,
        job_id: str,
        interval: timedelta,
        func: JobFunc,
        *,
        lock_key: str | None = None,
    ) -> None: ...

    def add_oneshot_job(
        self,
        job_id: str,
        run_at: datetime,
        func: JobFunc,
    ) -> None: ...

    def remove_job(self, job_id: str) -> bool: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


__all__ = ["JobFunc", "Scheduler"]
