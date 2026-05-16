"""Test that the public API surface is what the design doc promises."""

from __future__ import annotations

import hwhkit
from hwhkit.core import contracts


def test_top_level_facade() -> None:
    assert hwhkit.__version__ == "0.4.0a1"
    # The four "you should know about these" exports
    assert hwhkit.ApiError is not None
    assert hwhkit.AppContext is not None
    assert hwhkit.HealthStatus is not None
    assert hwhkit.IntegrationProvider is not None


def test_contracts_facade() -> None:
    # All 12 contract protocols accessible via hwhkit.contracts
    expected_protocols = {
        "Cache",
        "KvStore",
        "DistributedLock",
        "MessageBus",
        "RelationalDb",
        "ObjectStore",
        "VectorStore",
        "Scheduler",
        "LlmClient",
        "EmbeddingClient",
        "SecretsProvider",
        "Tracer",
        "Meter",
        "LogEmitter",
        "Notifier",
    }
    assert expected_protocols.issubset(set(contracts.__all__))


def test_core_module_complete() -> None:
    from hwhkit import core

    # Error taxonomy
    for name in [
        "ApiError",
        "ConflictError",
        "ForbiddenError",
        "NotFoundError",
        "ValidationError",
        "UnauthorizedError",
        "RateLimitError",
        "InternalError",
        "IntegrationError",
        "DbConnectionError",
        "RedisConnectionError",
        "NatsConnectionError",
    ]:
        assert hasattr(core, name), f"hwhkit.core missing {name}"
    # Building blocks
    for name in [
        "AppContext",
        "IntegrationProvider",
        "HealthStatus",
        "HealthCheck",
        "HealthAggregator",
        "GracefulShutdown",
        "ShutdownTimeout",
    ]:
        assert hasattr(core, name), f"hwhkit.core missing {name}"
