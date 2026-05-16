"""IntegrationProvider — lifecycle/registration ABC for all framework integrations.

See spec § 2.1.

An IntegrationProvider is the 'adapter' half of hexagonal arch — it implements
zero or more Contract protocols (declared via the ``implements`` class attr)
and exposes a managed lifecycle (setup / health / shutdown).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from fastapi import APIRouter
    from pydantic import BaseModel

    from hwhkit.core.context import AppContext
    from hwhkit.core.health import HealthStatus


class IntegrationProvider(ABC):
    """Lifecycle-managed framework plugin."""

    name: ClassVar[str]
    """Globally unique short identifier, e.g. "postgres" / "redis" / "nats"."""

    config_schema: ClassVar[type[BaseModel]]
    """Pydantic model the integration's config is parsed into."""

    implements: ClassVar[list[type]] = []
    """Contract Protocol classes this integration satisfies.

    Used for automatic contract → adapter binding in ``AppContext.resolve()``.
    """

    # ---- lifecycle (abstract) ------------------------------------------
    @abstractmethod
    async def setup(self, ctx: AppContext) -> None:
        """Initialize connection, warm up, register OTel instrumentation."""

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Lightweight liveness probe; aim for <100ms."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Flush buffers, close connections, cancel subscriptions."""

    # ---- optional hooks (default no-op) --------------------------------
    def fastapi_router(self) -> APIRouter | None:
        """Optional management router this integration exposes."""
        return None

    def fastapi_middlewares(self) -> list[Any]:
        """Optional middleware (e.g. per-request DB session)."""
        return []

    def fastapi_dependencies(self) -> dict[str, Any]:
        """Optional FastAPI Depends() factories."""
        return {}


__all__ = ["IntegrationProvider"]
