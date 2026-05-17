"""Health check protocol + aggregator.

Per spec § 2.5:
- liveness: process-only, always 200 if process is up.
- readiness: aggregates all registered HealthCheck instances; any unhealthy → 503.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

_logger = logging.getLogger(__name__)

HealthCheckFn = Callable[[], "HealthStatus | Awaitable[HealthStatus]"]


@dataclass(frozen=True, slots=True)
class HealthStatus:
    healthy: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str = "ok", **details: Any) -> HealthStatus:
        return cls(healthy=True, message=message, details=dict(details))

    @classmethod
    def fail(cls, message: str, *, details: dict[str, Any] | None = None) -> HealthStatus:
        return cls(healthy=False, message=message, details=details or {})


@runtime_checkable
class HealthCheck(Protocol):
    """Anything with ``name`` + async ``health_check``."""

    name: str

    async def health_check(self) -> HealthStatus: ...


class HealthAggregator:
    """Collects N HealthCheck callables and aggregates results."""

    def __init__(self) -> None:
        self._checks: list[tuple[str, HealthCheckFn]] = []

    def add(self, name: str, check: HealthCheckFn) -> None:
        self._checks.append((name, check))

    async def aggregate(self) -> HealthStatus:
        results: dict[str, dict[str, Any]] = {}
        all_healthy = True
        for name, fn in self._checks:
            try:
                raw = fn()
                status: HealthStatus = await raw if inspect.isawaitable(raw) else raw
            except Exception as exc:
                status = HealthStatus.fail(
                    f"check raised: {exc}", details={"type": type(exc).__name__}
                )
            results[name] = {
                "healthy": status.healthy,
                "message": status.message,
                "details": status.details,
            }
            if not status.healthy:
                all_healthy = False
        return HealthStatus(
            healthy=all_healthy,
            message="ok" if all_healthy else "one or more dependencies unhealthy",
            details={"checks": results},
        )


__all__ = ["HealthAggregator", "HealthCheck", "HealthCheckFn", "HealthStatus"]
