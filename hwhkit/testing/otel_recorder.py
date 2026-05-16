"""In-memory recorder satisfying Tracer / Meter / LogEmitter contracts.

Lightweight stand-in for the real OTel SDK in unit tests that want to assert
on emitted signals without the export pipeline overhead.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class RecordedSpan:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    exceptions: list[Exception] = field(default_factory=list)


@dataclass
class RecordedLog:
    level: str
    event: str
    fields: dict[str, Any] = field(default_factory=dict)


class _RecorderSpan:
    def __init__(self, recorded: RecordedSpan) -> None:
        self._r = recorded

    def set_attribute(self, key: str, value: Any) -> None:
        self._r.attributes[key] = value

    def record_exception(self, exc: Exception) -> None:
        self._r.exceptions.append(exc)

    def end(self) -> None:
        pass


class _RecorderCounter:
    def __init__(self, recorder: OtelRecorder, name: str) -> None:
        self._rec = recorder
        self._name = name

    def add(self, amount: int | float, attributes: dict[str, Any] | None = None) -> None:
        self._rec._counters.setdefault(self._name, []).append((amount, attributes or {}))


class _RecorderHistogram:
    def __init__(self, recorder: OtelRecorder, name: str) -> None:
        self._rec = recorder
        self._name = name

    def record(self, value: int | float, attributes: dict[str, Any] | None = None) -> None:
        self._rec._histograms.setdefault(self._name, []).append((value, attributes or {}))


class _RecorderLogEmitter:
    def __init__(self, recorder: OtelRecorder) -> None:
        self._rec = recorder

    def emit(self, level: str, event: str, **fields: Any) -> None:
        self._rec.logs.append(RecordedLog(level=level, event=event, fields=fields))


class OtelRecorder:
    """Drop-in fake for Tracer/Meter/LogEmitter that records everything in memory."""

    def __init__(self) -> None:
        self.spans: list[RecordedSpan] = []
        self.logs: list[RecordedLog] = []
        self._counters: dict[str, list[tuple[int | float, dict[str, Any]]]] = {}
        self._histograms: dict[str, list[tuple[int | float, dict[str, Any]]]] = {}
        self.log_emitter = _RecorderLogEmitter(self)

    @contextmanager
    def span(self, name: str, **attrs: Any) -> Iterator[_RecorderSpan]:
        rs = RecordedSpan(name=name, attributes=dict(attrs))
        self.spans.append(rs)
        yield _RecorderSpan(rs)

    def start_span(self, name: str, **attrs: Any) -> Any:
        return self.span(name, **attrs)

    def counter(self, name: str) -> _RecorderCounter:
        return _RecorderCounter(self, name)

    def histogram(self, name: str) -> _RecorderHistogram:
        return _RecorderHistogram(self, name)

    def create_counter(
        self, name: str, *, unit: str = "1", description: str = ""
    ) -> _RecorderCounter:
        return self.counter(name)

    def create_histogram(
        self, name: str, *, unit: str = "1", description: str = ""
    ) -> _RecorderHistogram:
        return self.histogram(name)

    def counter_total(self, name: str) -> int | float:
        return sum(v for v, _ in self._counters.get(name, []))

    def counter_with(self, name: str, attrs: dict[str, Any]) -> int | float:
        return sum(v for v, a in self._counters.get(name, []) if a == attrs)

    def reset(self) -> None:
        self.spans.clear()
        self.logs.clear()
        self._counters.clear()
        self._histograms.clear()


__all__ = ["OtelRecorder", "RecordedLog", "RecordedSpan"]
