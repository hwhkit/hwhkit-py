"""hwhkit.observability — OpenTelemetry-based three-pillar observability.

Default: disabled. Enable via ``observability.enabled = true`` in config.

Modules:
- ``logging``: structlog config + trace_id/span_id injection bridges.
- ``otel``: OTel SDK initialization (Tracer/Meter/LoggerProvider).
- ``tracing``: ``@traced`` decorator + span context managers.
- ``metrics``: shared meter + standard metric registry.
- ``instrumentation``: auto-instrument FastAPI/SQLAlchemy/Redis/httpx when libs present.

See spec § 4.
"""

from hwhkit.observability.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
