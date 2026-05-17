"""SchedulerProvider — APScheduler-backed adapter implementing ``Scheduler``.

Cron + interval + one-shot jobs. Optional distributed lock via the
``DistributedLock`` contract (resolves from AppContext when ``lock_key`` is
provided on a job, so multi-instance deployments don't double-fire).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.scheduler.config import SchedulerConfig

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from datetime import datetime

    from hwhkit.core.context import AppContext

    JobFunc = Callable[[], Awaitable[None]]

_logger = logging.getLogger(__name__)


class SchedulerProvider(IntegrationProvider):
    """APScheduler async wrapper. Implements ``Scheduler`` contract."""

    name: ClassVar[str] = "scheduler"
    config_schema: ClassVar[type[BaseModel]] = SchedulerConfig

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        from hwhkit.core.contracts.scheduler import Scheduler

        return [Scheduler]

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self._config = config
        self._scheduler: Any = None  # AsyncIOScheduler
        self._ctx: AppContext | None = None
        self._lock_keys: dict[str, str] = {}  # job_id -> lock_key

    async def setup(self, ctx: AppContext) -> None:
        cfg = self._resolve_config(ctx)
        try:
            from apscheduler.schedulers.asyncio import (  # type: ignore[import-untyped]
                AsyncIOScheduler,
            )
        except ImportError as exc:
            raise ImportError(
                "SchedulerProvider requires hwhkit[scheduler] extras: "
                "pip install 'hwhkit[scheduler]'"
            ) from exc

        self._scheduler = AsyncIOScheduler(timezone=cfg.timezone)
        self._ctx = ctx

    async def shutdown(self) -> None:
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._scheduler = None
        self._lock_keys.clear()

    async def health_check(self) -> HealthStatus:
        if self._scheduler is None:
            return HealthStatus.fail("scheduler not initialized")
        if not self._scheduler.running:
            return HealthStatus.ok("scheduler initialized but not started")
        return HealthStatus.ok(f"scheduler running with {len(self._scheduler.get_jobs())} jobs")

    # ---- Scheduler contract ----------------------------------------------
    def add_cron_job(
        self,
        job_id: str,
        cron: str,
        func: JobFunc,
        *,
        lock_key: str | None = None,
        timezone: str = "UTC",
    ) -> None:
        self._require_scheduler()
        wrapped = self._wrap_with_lock(job_id, func, lock_key)
        self._scheduler.add_job(
            wrapped,
            "cron",
            id=job_id,
            timezone=timezone,
            replace_existing=True,
            **_parse_cron(cron),
        )
        if lock_key:
            self._lock_keys[job_id] = lock_key

    def add_interval_job(
        self,
        job_id: str,
        interval: timedelta,
        func: JobFunc,
        *,
        lock_key: str | None = None,
    ) -> None:
        self._require_scheduler()
        wrapped = self._wrap_with_lock(job_id, func, lock_key)
        self._scheduler.add_job(
            wrapped,
            "interval",
            id=job_id,
            seconds=interval.total_seconds(),
            replace_existing=True,
        )
        if lock_key:
            self._lock_keys[job_id] = lock_key

    def add_oneshot_job(
        self,
        job_id: str,
        run_at: datetime,
        func: JobFunc,
    ) -> None:
        self._require_scheduler()
        self._scheduler.add_job(
            func,
            "date",
            id=job_id,
            run_date=run_at,
            replace_existing=True,
        )

    def remove_job(self, job_id: str) -> bool:
        self._require_scheduler()
        try:
            self._scheduler.remove_job(job_id)
            self._lock_keys.pop(job_id, None)
            return True
        except Exception:
            return False

    async def start(self) -> None:
        self._require_scheduler()
        if not self._scheduler.running:
            self._scheduler.start()

    async def stop(self) -> None:
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    # ---- helpers ----------------------------------------------------------
    def _require_scheduler(self) -> None:
        if self._scheduler is None:
            raise RuntimeError("SchedulerProvider not initialized; call setup() first")

    def _wrap_with_lock(
        self,
        job_id: str,
        func: JobFunc,
        lock_key: str | None,
    ) -> JobFunc:
        """Wrap ``func`` so it only runs if it can acquire ``lock_key``."""
        if lock_key is None:
            return func

        async def wrapped() -> None:
            from hwhkit.core.contracts.lock import DistributedLock

            if self._ctx is None:
                await func()
                return
            try:
                lock = self._ctx.resolve(DistributedLock)  # type: ignore[type-abstract]
            except LookupError:
                _logger.warning(
                    "job %s requested lock_key=%s but no DistributedLock impl "
                    "registered; running unguarded",
                    job_id,
                    lock_key,
                )
                await func()
                return
            tok = await lock.acquire(lock_key, timedelta(minutes=5), blocking=False)
            if tok is None:
                _logger.debug("job %s skipped: lock %s held by another instance", job_id, lock_key)
                return
            try:
                await func()
            finally:
                await lock.release(tok)

        return wrapped

    def _resolve_config(self, ctx: AppContext) -> SchedulerConfig:
        if self._config is not None:
            return self._config
        cfg = getattr(ctx.config, "scheduler", None)
        if isinstance(cfg, SchedulerConfig):
            return cfg
        return SchedulerConfig()


def _parse_cron(expr: str) -> dict[str, str]:
    """Parse a standard 5-field cron expression into APScheduler kwargs."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"cron expression must have 5 fields, got {len(parts)}: {expr!r}")
    minute, hour, day, month, day_of_week = parts
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
    }


__all__ = ["SchedulerProvider"]
