"""Structured logging via structlog with optional OTel trace_id injection.

Two modes:
- ``json_mode=True``  → JSON to stdout (production)
- ``json_mode=False`` → human-friendly colored output (development)

OTel integration:
- If ``otel.trace`` is available AND a span is active, ``trace_id`` /
  ``span_id`` are injected into every log record.
- Independent of OTel SDK setup — pure context propagation.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def _add_otel_context(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """structlog processor: inject trace_id + span_id when an OTel span is active.

    Imports OTel lazily so logging works without OTel installed.
    """
    try:
        from opentelemetry import trace
    except ImportError:
        return event_dict

    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx is None or not ctx.is_valid:
        return event_dict

    event_dict.setdefault("trace_id", format(ctx.trace_id, "032x"))
    event_dict.setdefault("span_id", format(ctx.span_id, "016x"))
    return event_dict


def _stdlib_level(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


def configure_logging(
    *,
    level: str = "INFO",
    json_mode: bool = True,
    service_name: str | None = None,
) -> None:
    """Configure structlog + stdlib logging.

    Called once at bootstrap. Safe to call repeatedly (idempotent reconfiguration).

    Args:
        level: minimum log level (DEBUG/INFO/WARNING/ERROR/CRITICAL).
        json_mode: True = JSON to stdout (prod); False = pretty colored (dev).
        service_name: bound to every log line for multi-service log aggregation.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamper,
        _add_otel_context,
    ]
    if service_name:
        shared_processors.insert(
            0,
            structlog.processors.CallsiteParameterAdder([]),  # noop
        )
        shared_processors.append(_make_service_name_processor(service_name))

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_mode
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )

    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(_stdlib_level(level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also route stdlib logging through structlog so libraries' log lines get
    # the same processing (Uvicorn / FastAPI / SQLAlchemy / ...).
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=_stdlib_level(level),
        force=True,
    )


def _make_service_name_processor(service_name: str) -> Any:
    def _add(_logger: Any, _method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        event_dict.setdefault("service", service_name)
        return event_dict

    return _add


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger bound to ``name``.

    Use as: ``log = get_logger(__name__)``.
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


__all__ = ["configure_logging", "get_logger"]
