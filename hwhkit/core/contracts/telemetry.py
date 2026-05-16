"""Telemetry contracts — Tracer / Meter / LogEmitter abstractions over OTel.

Default adapter is ``hwhkit.observability.otel`` (P0). Replacement uncommon
but possible (e.g. for testing via ``hwhkit.testing.OtelRecorder``).
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Span(Protocol):
    def set_attribute(self, key: str, value: Any) -> None: ...

    def record_exception(self, exc: Exception) -> None: ...

    def end(self) -> None: ...


@runtime_checkable
class Tracer(Protocol):
    def start_span(self, name: str, **attrs: Any) -> AbstractContextManager[Span]: ...


@runtime_checkable
class Counter(Protocol):
    def add(
        self,
        amount: int | float,
        attributes: dict[str, Any] | None = None,
    ) -> None: ...


@runtime_checkable
class Histogram(Protocol):
    def record(
        self,
        value: int | float,
        attributes: dict[str, Any] | None = None,
    ) -> None: ...


@runtime_checkable
class Meter(Protocol):
    def create_counter(
        self,
        name: str,
        *,
        unit: str = "1",
        description: str = "",
    ) -> Counter: ...

    def create_histogram(
        self,
        name: str,
        *,
        unit: str = "1",
        description: str = "",
    ) -> Histogram: ...


@runtime_checkable
class LogEmitter(Protocol):
    def emit(self, level: str, event: str, **fields: Any) -> None: ...


__all__ = ["Counter", "Histogram", "LogEmitter", "Meter", "Span", "Tracer"]
