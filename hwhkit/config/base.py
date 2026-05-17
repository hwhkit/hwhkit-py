"""Settings base class — root of the layered config tree.

Business code subclasses this to add integration-specific config sections:

    class TradingSettings(Settings):
        postgres: PostgresConfig = Field(default_factory=PostgresConfig)
        redis: RedisConfig = Field(default_factory=RedisConfig)
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from hwhkit.config.schemas import AppConfig, ObservabilityConfig, WebConfig


class Settings(BaseSettings):
    """Root settings. Nested sections delimited by ``__`` in env vars.

    Example: ``HWHKIT_APP__NAME=trading-service``,
             ``HWHKIT_WEB__PORT=9000``,
             ``HWHKIT_OBSERVABILITY__ENABLED=true``.
    """

    model_config = SettingsConfigDict(
        env_prefix="HWHKIT_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # business may add their own sections
    )

    app: AppConfig = Field(default_factory=AppConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)


__all__ = ["Settings"]
