"""Per-suite fixtures for observability tests.

OTel SDK uses background threads (BatchSpanProcessor / PeriodicMetricReader)
that flush to stdout. Pytest captures stdout per test, and the writes happen
after teardown — closing the captured stream causes ``I/O operation on
closed file``. We force-shutdown providers after each test to flush before
teardown.

We do NOT reset the global TracerProvider here — OTel only honors the first
``set_tracer_provider`` call per process, so tests that need a specific
provider use a shared session-scoped provider (see test_tracing.py).
"""

from __future__ import annotations

import contextlib
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _shutdown_otel_after_test() -> Any:
    """Force tracer/meter/logger providers to shut down so background threads stop."""
    yield
    with contextlib.suppress(Exception):
        from opentelemetry import metrics, trace

        # Don't shutdown the tracer provider — it's shared across tests via
        # session-scoped pattern. Only flush metrics where stdout-export
        # thread leaks happen.
        _ = trace
        mp = metrics.get_meter_provider()
        if hasattr(mp, "shutdown"):
            with contextlib.suppress(Exception):
                mp.shutdown()
