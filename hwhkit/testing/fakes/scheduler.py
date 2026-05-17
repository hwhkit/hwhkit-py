"""In-memory ``Scheduler`` fake — for business unit tests of scheduled-job logic.

Records jobs into a dict; tests can trigger them manually with
``await fake.run(job_id)``. Does NOT actually fire on schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    JobFunc = Callable[[], Awaitable[None]]


@dataclass
class _ScheduledJob:
    job_id: str
    func: JobFunc
    kind: str  # "cron" / "interval" / "oneshot"
    spec: dict[str, object]
    lock_key: str | None = None


class FakeScheduler:
    """In-memory scheduler. Jobs are added but only run when ``run()`` is called."""

    def __init__(self) -> None:
        self._jobs: dict[str, _ScheduledJob] = {}
        self._started: bool = False

    def add_cron_job(
        self,
        job_id: str,
        cron: str,
        func: JobFunc,
        *,
        lock_key: str | None = None,
        timezone: str = "UTC",
    ) -> None:
        self._jobs[job_id] = _ScheduledJob(
            job_id=job_id,
            func=func,
            kind="cron",
            spec={"cron": cron, "timezone": timezone},
            lock_key=lock_key,
        )

    def add_interval_job(
        self,
        job_id: str,
        interval: timedelta,
        func: JobFunc,
        *,
        lock_key: str | None = None,
    ) -> None:
        self._jobs[job_id] = _ScheduledJob(
            job_id=job_id,
            func=func,
            kind="interval",
            spec={"interval": interval},
            lock_key=lock_key,
        )

    def add_oneshot_job(
        self,
        job_id: str,
        run_at: datetime,
        func: JobFunc,
    ) -> None:
        self._jobs[job_id] = _ScheduledJob(
            job_id=job_id,
            func=func,
            kind="oneshot",
            spec={"run_at": run_at},
        )

    def remove_job(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._started = False

    # ---- test-only helpers ------------------------------------------------
    async def run(self, job_id: str) -> None:
        """Manually trigger a scheduled job (test convenience)."""
        await self._jobs[job_id].func()

    @property
    def jobs(self) -> dict[str, _ScheduledJob]:
        return dict(self._jobs)

    @property
    def started(self) -> bool:
        return self._started


__all__ = ["FakeScheduler"]
