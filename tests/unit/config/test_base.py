"""Tests for hwhkit.config.base + schemas."""

from __future__ import annotations

import pytest
from hwhkit.config import (
    AppConfig,
    LogConfig,
    ObservabilityConfig,
    SamplerConfig,
    Settings,
    WebConfig,
)


class TestAppConfig:
    def test_defaults(self) -> None:
        c = AppConfig()
        assert c.name == "hwhkit-app"
        assert c.version == "0.0.0"
        assert c.environment == "dev"

    def test_environment_validates(self) -> None:
        with pytest.raises(ValueError, match="environment"):
            AppConfig(environment="prodd")  # type: ignore[arg-type]


class TestWebConfig:
    def test_defaults(self) -> None:
        c = WebConfig()
        assert c.host == "0.0.0.0"
        assert c.port == 8000
        assert c.server == "granian"
        assert c.docs_enabled is True
        assert c.admin_routes_enabled is False
        assert c.cors.allow_origins == ["*"]

    def test_cors_nested(self) -> None:
        c = WebConfig.model_validate(
            {"cors": {"allow_origins": ["https://a.test"], "allow_credentials": True}}
        )
        assert c.cors.allow_origins == ["https://a.test"]
        assert c.cors.allow_credentials is True


class TestObservabilityConfig:
    def test_default_disabled(self) -> None:
        c = ObservabilityConfig()
        assert c.enabled is False
        assert c.exporter == "otlp_http"
        assert c.sampler.type == "parent_based_ratio"
        assert c.sampler.ratio == 0.1
        assert c.prometheus_compat_enabled is False
        assert c.log.level == "INFO"
        assert c.log.json_mode is True


class TestSamplerConfig:
    def test_defaults(self) -> None:
        s = SamplerConfig()
        assert s.type == "parent_based_ratio"
        assert s.ratio == 0.1


class TestLogConfig:
    def test_defaults(self) -> None:
        log = LogConfig()
        assert log.level == "INFO"
        assert log.json_mode is True


class TestSettings:
    def test_defaults(self) -> None:
        s = Settings()
        assert isinstance(s.app, AppConfig)
        assert isinstance(s.web, WebConfig)
        assert isinstance(s.observability, ObservabilityConfig)

    def test_extra_sections_allowed(self) -> None:
        """Business may add own sections like 'postgres', 'redis', ..."""
        s = Settings(extra_section={"foo": "bar"})  # type: ignore[call-arg]
        assert s.extra_section == {"foo": "bar"}

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HWHKIT_APP__NAME", "trading-service")
        monkeypatch.setenv("HWHKIT_WEB__PORT", "9001")
        monkeypatch.setenv("HWHKIT_OBSERVABILITY__ENABLED", "true")
        s = Settings()
        assert s.app.name == "trading-service"
        assert s.web.port == 9001
        assert s.observability.enabled is True

    def test_env_nested_delimiter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HWHKIT_OBSERVABILITY__SAMPLER__RATIO", "0.5")
        s = Settings()
        assert s.observability.sampler.ratio == 0.5
