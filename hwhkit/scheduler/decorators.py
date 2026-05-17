"""``@scheduled_task`` decorator — register a function as a scheduled job at import.

Decorated functions are NOT auto-registered at decoration time; they accumulate
in a module-level registry and are registered when ``register_scheduled_tasks(ctx)``
is called from ``bootstrap()`` (or manually).

Usage::

    from hwhkit.scheduler import scheduled_task

    @scheduled_task(cron="0 */1 * * *", lock_key="hourly-aggregate")
    async def hourly_aggregate(ctx: AppContext) -> None:
        ...
"""

from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from hwhkit.core.context import AppContext


@dataclass
class _ScheduledTaskSpec:
    """Internal record of a @scheduled_task decoration."""

    job_id: str
    func: Any
    cron: str | None = None
    interval: timedelta | None = None
    run_at: datetime | None = None
    lock_key: str | None = None
    timezone: str = "UTC"
    extra: dict[str, Any] = field(default_factory=dict)


_REGISTRY: list[_ScheduledTaskSpec] = []


def scheduled_task(
    *,
    cron: str | None = None,
    interval: timedelta | None = None,
    run_at: datetime | None = None,
    job_id: str | None = None,
    lock_key: str | None = None,
    timezone: str = "UTC",
) -> Callable[..., Any]:
    """Decorator: queue a function for scheduler registration.

    Exactly one of ``cron`` / ``interval`` / ``run_at`` must be specified.

    Function signature: ``async def(ctx: AppContext) -> None``.

    Args:
        cron: 5-field cron expression.
        interval: timedelta for periodic execution.
        run_at: timezone-aware datetime for one-shot.
        job_id: defaults to ``f"{func.__module__}.{func.__qualname__}"``.
        lock_key: distributed lock key; if provided, only one instance runs.
        timezone: APScheduler timezone for cron evaluation.
    """
    schedule_args = [a for a in (cron, interval, run_at) if a is not None]
    if len(schedule_args) != 1:
        raise ValueError("@scheduled_task requires exactly one of: cron, interval, run_at")

    def _decorator(func: Callable[[AppContext], Awaitable[None]]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"@scheduled_task target must be async: {func.__qualname__}")
        resolved_job_id = job_id or f"{func.__module__}.{func.__qualname__}"
        _REGISTRY.append(
            _ScheduledTaskSpec(
                job_id=resolved_job_id,
                func=func,
                cron=cron,
                interval=interval,
                run_at=run_at,
                lock_key=lock_key,
                timezone=timezone,
            )
        )
        return functools.wraps(func)(func)

    return _decorator


async def register_scheduled_tasks(ctx: AppContext) -> None:
    """Push the decorator registry into the active SchedulerProvider.

    Call once from a bootstrap on_startup hook. Idempotent: repeated calls
    just re-register (APScheduler's ``replace_existing=True``).
    """
    from hwhkit.scheduler.provider import SchedulerProvider

    try:
        scheduler = ctx.get_typed(SchedulerProvider)
    except LookupError:
        return  # No scheduler registered; @scheduled_task is a no-op then.

    def _make_bound(func: Any, _ctx: AppContext) -> Callable[[], Awaitable[None]]:
        async def _bound() -> None:
            await func(_ctx)

        return _bound

    for spec in _REGISTRY:
        _bound = _make_bound(spec.func, ctx)

        if spec.cron is not None:
            scheduler.add_cron_job(
                spec.job_id, spec.cron, _bound, lock_key=spec.lock_key, timezone=spec.timezone
            )
        elif spec.interval is not None:
            scheduler.add_interval_job(spec.job_id, spec.interval, _bound, lock_key=spec.lock_key)
        elif spec.run_at is not None:
            scheduler.add_oneshot_job(spec.job_id, spec.run_at, _bound)

    await scheduler.start()


def _clear_registry() -> None:
    """Test helper — reset the module-level registry between tests."""
    _REGISTRY.clear()


__all__ = ["register_scheduled_tasks", "scheduled_task"]
