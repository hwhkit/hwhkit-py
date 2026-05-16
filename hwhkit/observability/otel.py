"""OpenTelemetry SDK initialization.

Returns no-op providers when ``config.enabled = False``; full SDK otherwise.
Supports exporters: ``otlp_http`` / ``otlp_grpc`` / ``console`` / ``none``.

Sampling: parent-based-ratio default (10% prod / 100% dev).
``/healthz``, ``/readyz``, ``/metrics`` paths are excluded by the FastAPI
instrumentation, not by the sampler — see ``instrumentation.py``.

See spec § 4.1, § 4.3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hwhkit.config.schemas import ObservabilityConfig


@dataclass(slots=True)
class OtelHandles:
    """Bundle of OTel SDK objects returned by ``setup_otel``.

    Held by ``AppContext`` so the rest of the framework can request a tracer
    or meter without re-creating providers.

    Field types are ``Any`` to avoid forcing OTel SDK type imports at the
    framework's public surface; concrete types are documented in comments.
    """

    tracer: Any  # opentelemetry.trace.Tracer | NoOpTracer
    meter: Any  # opentelemetry.metrics.Meter | NoOpMeter
    logger_provider: Any | None  # opentelemetry.sdk._logs.LoggerProvider | None
    enabled: bool


def setup_otel(config: ObservabilityConfig) -> OtelHandles:
    """Initialize OTel SDK based on config.

    Idempotent: setting the same provider twice is a no-op in OTel.

    Returns:
        OtelHandles bundle with tracer/meter/logger_provider/enabled fields.
    """
    if not config.enabled:
        return _noop_handles()

    from opentelemetry import metrics, trace

    resource = _build_resource(config)

    tracer_provider = _build_tracer_provider(config, resource)
    trace.set_tracer_provider(tracer_provider)

    meter_provider = _build_meter_provider(config, resource)
    metrics.set_meter_provider(meter_provider)

    logger_provider = _build_logger_provider(config, resource)

    return OtelHandles(
        tracer=trace.get_tracer("hwhkit"),
        meter=metrics.get_meter("hwhkit"),
        logger_provider=logger_provider,
        enabled=True,
    )


# ---- internals --------------------------------------------------------------


def _noop_handles() -> OtelHandles:
    """Return handles backed by OTel's built-in no-op implementations."""
    from opentelemetry import metrics, trace

    return OtelHandles(
        tracer=trace.get_tracer("hwhkit"),
        meter=metrics.get_meter("hwhkit"),
        logger_provider=None,
        enabled=False,
    )


def _build_resource(config: ObservabilityConfig) -> Any:
    from opentelemetry.sdk.resources import Resource

    attrs: dict[str, str] = {}
    if config.service_name:
        attrs["service.name"] = config.service_name
    if config.service_version:
        attrs["service.version"] = config.service_version
    if config.environment:
        attrs["deployment.environment"] = config.environment
    return Resource.create(attrs)


def _build_tracer_provider(config: ObservabilityConfig, resource: Any) -> Any:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    sampler = _build_sampler(config)
    provider = TracerProvider(resource=resource, sampler=sampler)
    exporter = _build_span_exporter(config)
    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider


def _build_sampler(config: ObservabilityConfig) -> Any:
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_OFF,
        ALWAYS_ON,
        ParentBased,
        TraceIdRatioBased,
    )

    s = config.sampler
    if s.type == "always_on":
        return ALWAYS_ON
    if s.type == "always_off":
        return ALWAYS_OFF
    return ParentBased(TraceIdRatioBased(s.ratio))


def _build_span_exporter(config: ObservabilityConfig) -> Any | None:
    if config.exporter == "none":
        return None
    if config.exporter == "console":
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
        )

        return ConsoleSpanExporter()
    if config.exporter == "otlp_http":
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        return OTLPSpanExporter(endpoint=f"{config.endpoint}/v1/traces")
    if config.exporter == "otlp_grpc":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter as _Grpc,
        )

        return _Grpc(endpoint=config.endpoint)
    raise ValueError(f"unknown exporter: {config.exporter}")


def _build_meter_provider(config: ObservabilityConfig, resource: Any) -> Any:
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
    )

    readers: list[Any] = []
    exporter = _build_metric_exporter(config)
    if exporter is not None:
        readers.append(PeriodicExportingMetricReader(exporter, export_interval_millis=10_000))
    return MeterProvider(resource=resource, metric_readers=readers)


def _build_metric_exporter(config: ObservabilityConfig) -> Any | None:
    if config.exporter == "none":
        return None
    if config.exporter == "console":
        from opentelemetry.sdk.metrics.export import (
            ConsoleMetricExporter,
        )

        return ConsoleMetricExporter()
    if config.exporter == "otlp_http":
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )

        return OTLPMetricExporter(endpoint=f"{config.endpoint}/v1/metrics")
    if config.exporter == "otlp_grpc":
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter as _Grpc,
        )

        return _Grpc(endpoint=config.endpoint)
    raise ValueError(f"unknown exporter: {config.exporter}")


def _build_logger_provider(config: ObservabilityConfig, resource: Any) -> Any | None:
    """OTel logs SDK; emits via BatchLogRecordProcessor."""
    if config.exporter == "none":
        return None
    try:
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import (
            BatchLogRecordProcessor,
        )
    except ImportError:
        return None  # SDK without logs API; tolerate

    provider = LoggerProvider(resource=resource)
    exporter = _build_log_exporter(config)
    if exporter is not None:
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return provider


def _build_log_exporter(config: ObservabilityConfig) -> Any | None:
    if config.exporter == "console":
        # Prefer the new name; fall back to old (deprecated) one on older SDKs.
        try:
            from opentelemetry.sdk._logs.export import (
                ConsoleLogRecordExporter as _Console,
            )
        except ImportError:
            try:
                from opentelemetry.sdk._logs.export import (
                    ConsoleLogExporter as _Console,
                )
            except ImportError:
                return None
        return _Console()
    if config.exporter == "otlp_http":
        try:
            from opentelemetry.exporter.otlp.proto.http._log_exporter import (
                OTLPLogExporter,
            )
        except ImportError:
            return None
        return OTLPLogExporter(endpoint=f"{config.endpoint}/v1/logs")
    if config.exporter == "otlp_grpc":
        try:
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
                OTLPLogExporter as _Grpc,
            )
        except ImportError:
            return None
        return _Grpc(endpoint=config.endpoint)
    return None


__all__ = ["OtelHandles", "setup_otel"]
