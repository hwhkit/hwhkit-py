"""hwhkit — production-ready Python framework for trading services and microservices.

See https://hwhkit.louishwh.tech for documentation.
"""

from hwhkit.core import (
    ApiError,
    AppContext,
    HealthStatus,
    IntegrationProvider,
    contracts,
)

__version__ = "0.4.0a1"

__all__ = [
    "ApiError",
    "AppContext",
    "HealthStatus",
    "IntegrationProvider",
    "__version__",
    "contracts",
]
