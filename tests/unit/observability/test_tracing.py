"""Tests for hwhkit.observability.tracing."""

from __future__ import annotations

import pytest
from hwhkit.observability.tracing import span, traced
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_SHARED_EXPORTER = InMemorySpanExporter()
_PROCESSOR_INSTALLED = False


def _ensure_processor() -> None:
    """Install our InMemorySpanExporter on whatever TracerProvider is global.

    OTel only honors the first ``set_tracer_provider`` call per process. If
    another test (e.g. ``test_otel.py``) already installed a provider, we
    cannot replace it — but we CAN add a span processor to it via the
    public ``add_span_processor`` API on the SDK ``TracerProvider``.
    """
    global _PROCESSOR_INSTALLED
    if _PROCESSOR_INSTALLED:
        return
    current = trace.get_tracer_provider()
    if not isinstance(current, TracerProvider):
        # Probably the proxy provider — install our own SDK provider.
        current = TracerProvider()
        trace.set_tracer_provider(current)
    current.add_span_processor(SimpleSpanProcessor(_SHARED_EXPORTER))
    _PROCESSOR_INSTALLED = True


@pytest.fixture
def exporter() -> InMemorySpanExporter:
    _ensure_processor()
    _SHARED_EXPORTER.clear()
    return _SHARED_EXPORTER


def test_span_context_manager_records(exporter: InMemorySpanExporter) -> None:
    with span("op-x", user_id=42):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "op-x"
    assert spans[0].attributes["user_id"] == 42


def test_traced_sync(exporter: InMemorySpanExporter) -> None:
    @traced("compute")
    def compute(x: int) -> int:
        return x * 2

    assert compute(3) == 6
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "compute"


def test_traced_default_name(exporter: InMemorySpanExporter) -> None:
    @traced()
    def my_func() -> int:
        return 1

    my_func()
    spans = exporter.get_finished_spans()
    assert spans[0].name.endswith("my_func")


@pytest.mark.asyncio
async def test_traced_async(exporter: InMemorySpanExporter) -> None:
    @traced("async-op")
    async def go() -> str:
        return "done"

    assert await go() == "done"
    spans = exporter.get_finished_spans()
    assert spans[0].name == "async-op"


def test_traced_records_exception(exporter: InMemorySpanExporter) -> None:
    @traced("fail-op")
    def boom() -> None:
        raise RuntimeError("kaboom")

    with pytest.raises(RuntimeError, match="kaboom"):
        boom()
    spans = exporter.get_finished_spans()
    assert spans[0].name == "fail-op"
    assert len(spans[0].events) >= 1
    assert spans[0].events[0].name == "exception"
