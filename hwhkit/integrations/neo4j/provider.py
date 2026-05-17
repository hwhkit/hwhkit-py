"""Neo4jProvider (P2 placeholder).

Concrete implementation reserved for a future release.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.integrations.neo4j.config import Neo4jConfig

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext


class Neo4jProvider(IntegrationProvider):
    """Neo4j adapter (placeholder — not yet implemented)."""

    name: ClassVar[str] = "neo4j"
    config_schema: ClassVar[type[BaseModel]] = Neo4jConfig

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        return []

    def __init__(self, config: Neo4jConfig | None = None) -> None:
        self._config = config

    async def setup(self, ctx: AppContext) -> None:
        raise NotImplementedError(
            "Neo4jProvider is a P2 placeholder; concrete adapter ships in a future release."
        )

    async def shutdown(self) -> None:
        pass

    async def health_check(self) -> HealthStatus:
        return HealthStatus.fail("Neo4jProvider is a P2 placeholder (not yet implemented)")


__all__ = ["Neo4jProvider"]
