"""Per-subsystem config schemas (pydantic models).

Integration-specific configs (PostgresConfig, RedisConfig, ...) live with
their respective adapters in hwhkit.integrations.*; this module hosts the
framework-core schemas only.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Top-level application identity."""

    name: str = "hwhkit-app"
    version: str = "0.0.0"
    environment: Literal["dev", "staging", "prod"] = "dev"
    description: str = ""


class CorsConfig(BaseModel):
    allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = False
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    max_age: int = 600


class WebConfig(BaseModel):
    """FastAPI / HTTP server config."""

    host: str = "0.0.0.0"  # noqa: S104  intentional default for containers
    port: int = 8000
    workers: int = 1
    server: Literal["granian", "uvicorn", "gunicorn"] = "granian"
    docs_enabled: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    admin_routes_enabled: bool = False
    cors: CorsConfig = Field(default_factory=CorsConfig)


class SamplerConfig(BaseModel):
    type: Literal["parent_based_ratio", "always_on", "always_off"] = "parent_based_ratio"
    ratio: float = 0.1  # 10% default (prod); raise to 1.0 in dev


class LogConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    json_mode: bool = True  # JSON to stdout; False = pretty colored for dev


class ObservabilityConfig(BaseModel):
    """OTel three-pillar configuration. Default disabled."""

    enabled: bool = False
    service_name: str = ""  # derives from app.name if empty
    service_version: str = ""  # derives from app.version if empty
    environment: str = ""  # derives from app.environment if empty
    exporter: Literal["otlp_http", "otlp_grpc", "console", "none"] = "otlp_http"
    endpoint: str = "http://localhost:4318"
    sampler: SamplerConfig = Field(default_factory=SamplerConfig)
    prometheus_compat_enabled: bool = False
    log: LogConfig = Field(default_factory=LogConfig)


__all__ = [
    "AppConfig",
    "CorsConfig",
    "LogConfig",
    "ObservabilityConfig",
    "SamplerConfig",
    "WebConfig",
]
