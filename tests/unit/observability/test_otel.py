"""Tests for hwhkit.observability.otel."""

from __future__ import annotations

from hwhkit.config.schemas import ObservabilityConfig, SamplerConfig
from hwhkit.observability.otel import setup_otel


def test_disabled_returns_noop_handles() -> None:
    cfg = ObservabilityConfig(enabled=False)
    h = setup_otel(cfg)
    assert h.enabled is False
    assert h.logger_provider is None
    # Tracer/Meter are no-op instances from OTel built-ins; just verify shape
    assert h.tracer is not None
    assert h.meter is not None


def test_enabled_console_exporter_initializes() -> None:
    cfg = ObservabilityConfig(
        enabled=True,
        exporter="console",
        service_name="test-svc",
        service_version="0.0.1",
        environment="dev",
    )
    h = setup_otel(cfg)
    assert h.enabled is True
    assert h.tracer is not None
    assert h.meter is not None
    # logger_provider may be None if SDK build doesn't include logs; that's OK
    # under the construction path we hit `_build_logger_provider`.


def test_enabled_none_exporter() -> None:
    cfg = ObservabilityConfig(enabled=True, exporter="none")
    h = setup_otel(cfg)
    assert h.enabled is True
    assert h.logger_provider is None


def test_sampler_always_off_accepted() -> None:
    cfg = ObservabilityConfig(
        enabled=True,
        exporter="console",
        sampler=SamplerConfig(type="always_off"),
    )
    h = setup_otel(cfg)
    assert h.enabled is True


def test_sampler_always_on_accepted() -> None:
    cfg = ObservabilityConfig(
        enabled=True,
        exporter="console",
        sampler=SamplerConfig(type="always_on"),
    )
    h = setup_otel(cfg)
    assert h.enabled is True


def test_otlp_http_exporter_constructs() -> None:
    """We don't actually export — just construct the exporter without raising."""
    cfg = ObservabilityConfig(
        enabled=True,
        exporter="otlp_http",
        endpoint="http://otel-collector:4318",
        service_name="trading",
    )
    h = setup_otel(cfg)
    assert h.enabled is True
