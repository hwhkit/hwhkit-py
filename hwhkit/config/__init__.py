"""hwhkit.config — layered configuration system based on pydantic-settings.

Precedence (highest wins):
1. config_overrides argument to bootstrap() (for tests)
2. Environment variables
3. YAML file (path from HWHKIT_CONFIG env or ./config.yaml)
4. .env file
5. Defaults in the Settings class

See spec § 1 + § 2.3.
"""

from hwhkit.config.base import Settings
from hwhkit.config.schemas import (
    AppConfig,
    CorsConfig,
    LogConfig,
    ObservabilityConfig,
    SamplerConfig,
    WebConfig,
)
from hwhkit.config.sources import load_settings

__all__ = [
    "AppConfig",
    "CorsConfig",
    "LogConfig",
    "ObservabilityConfig",
    "SamplerConfig",
    "Settings",
    "WebConfig",
    "load_settings",
]
