"""hwhkit.testing — utilities for testing services built on hwhkit.

Includes:
- ``hwhkit.testing.fakes`` — in-memory implementations of all contracts (W3+).
- ``hwhkit.testing.contract_tests`` — reusable contract conformance test suites (W3+).
- ``hwhkit.testing.otel_recorder`` — in-memory OTel exporter for assertions.
"""

from hwhkit.testing.otel_recorder import OtelRecorder, RecordedLog, RecordedSpan

__all__ = ["OtelRecorder", "RecordedLog", "RecordedSpan"]
