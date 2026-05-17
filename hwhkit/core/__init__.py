"""hwhkit core — bootstrap pipeline, AppContext, IntegrationProvider, errors, contracts."""

from hwhkit.core.context import AppContext
from hwhkit.core.errors import (
    ApiError,
    ConflictError,
    DbConnectionError,
    ForbiddenError,
    IntegrationError,
    InternalError,
    NatsConnectionError,
    NotFoundError,
    RateLimitError,
    RedisConnectionError,
    UnauthorizedError,
    ValidationError,
)
from hwhkit.core.health import HealthAggregator, HealthCheck, HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.core.shutdown import GracefulShutdown, ShutdownTimeout

__all__ = [
    "ApiError",
    "AppContext",
    "ConflictError",
    "DbConnectionError",
    "ForbiddenError",
    "GracefulShutdown",
    "HealthAggregator",
    "HealthCheck",
    "HealthStatus",
    "IntegrationError",
    "IntegrationProvider",
    "InternalError",
    "NatsConnectionError",
    "NotFoundError",
    "RateLimitError",
    "RedisConnectionError",
    "ShutdownTimeout",
    "UnauthorizedError",
    "ValidationError",
]
