"""Branch coverage for hwhkit.observability.otel exporter paths."""

from __future__ import annotations

import pytest
from hwhkit.config.schemas import ObservabilityConfig, SamplerConfig
from hwhkit.observability.otel import (
    _build_log_exporter,
    _build_logger_provider,
    _build_meter_provider,
    _build_metric_exporter,
    _build_resource,
    _build_sampler,
    _build_span_exporter,
    _build_tracer_provider,
    setup_otel,
)


def test_build_resource_with_all_attrs() -> None:
    cfg = ObservabilityConfig(
        enabled=True,
        service_name="svc",
        service_version="1.0",
        environment="prod",
    )
    res = _build_resource(cfg)
    # Resource is OTel SDK type; just smoke-check it exists
    assert res is not None


def test_build_resource_with_empty_attrs() -> None:
    cfg = ObservabilityConfig(enabled=True)
    res = _build_resource(cfg)
    assert res is not None


def test_build_sampler_variants() -> None:
    for stype in ("parent_based_ratio", "always_on", "always_off"):
        cfg = ObservabilityConfig(
            enabled=True,
            sampler=SamplerConfig(type=stype),  # type: ignore[arg-type]
        )
        assert _build_sampler(cfg) is not None


def test_build_span_exporter_none() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="none")
    assert _build_span_exporter(cfg) is None


def test_build_span_exporter_console() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="console")
    assert _build_span_exporter(cfg) is not None


def test_build_span_exporter_otlp_http() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="otlp_http", endpoint="http://x")
    assert _build_span_exporter(cfg) is not None


def test_build_span_exporter_otlp_grpc() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="otlp_grpc", endpoint="x:4317")
    assert _build_span_exporter(cfg) is not None


def test_build_metric_exporter_branches() -> None:
    assert _build_metric_exporter(ObservabilityConfig(enabled=True, exporter="none")) is None
    assert _build_metric_exporter(ObservabilityConfig(enabled=True, exporter="console")) is not None
    assert (
        _build_metric_exporter(
            ObservabilityConfig(enabled=True, exporter="otlp_http", endpoint="http://x")
        )
        is not None
    )
    assert (
        _build_metric_exporter(
            ObservabilityConfig(enabled=True, exporter="otlp_grpc", endpoint="x:4317")
        )
        is not None
    )


def test_build_log_exporter_branches() -> None:
    # console
    e = _build_log_exporter(ObservabilityConfig(enabled=True, exporter="console"))
    assert e is not None
    # otlp_http
    e = _build_log_exporter(
        ObservabilityConfig(enabled=True, exporter="otlp_http", endpoint="http://x")
    )
    assert e is not None
    # otlp_grpc
    e = _build_log_exporter(
        ObservabilityConfig(enabled=True, exporter="otlp_grpc", endpoint="x:4317")
    )
    assert e is not None
    # none → caller passes through; helper returns None
    assert _build_log_exporter(ObservabilityConfig(enabled=True, exporter="none")) is None


def test_build_logger_provider_none_exporter() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="none")
    assert _build_logger_provider(cfg, resource=None) is None


def test_build_logger_provider_console() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="console")
    provider = _build_logger_provider(cfg, resource=_build_resource(cfg))
    # LoggerProvider may be None if logs SDK not installed; either is acceptable
    assert provider is None or hasattr(provider, "add_log_record_processor")


def test_build_meter_provider() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="console")
    mp = _build_meter_provider(cfg, _build_resource(cfg))
    assert mp is not None


def test_build_tracer_provider() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="console")
    tp = _build_tracer_provider(cfg, _build_resource(cfg))
    assert tp is not None


def test_setup_otel_otlp_grpc() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="otlp_grpc", endpoint="localhost:4317")
    h = setup_otel(cfg)
    assert h.enabled is True


def test_build_span_exporter_unknown_raises() -> None:
    """Unknown exporter raises ValueError (defensive code path)."""
    cfg = ObservabilityConfig(enabled=True, exporter="console")
    # Manually mutate to bypass pydantic validation
    object.__setattr__(cfg, "exporter", "bogus")
    with pytest.raises(ValueError, match="unknown exporter"):
        _build_span_exporter(cfg)


def test_build_metric_exporter_unknown_raises() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="console")
    object.__setattr__(cfg, "exporter", "bogus")
    with pytest.raises(ValueError, match="unknown exporter"):
        _build_metric_exporter(cfg)
