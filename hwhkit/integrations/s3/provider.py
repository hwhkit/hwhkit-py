"""S3Provider (P2 placeholder).

Concrete implementation reserved for a future release.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.integrations.s3.config import S3Config

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext


class S3Provider(IntegrationProvider):
    """S3 adapter (placeholder — not yet implemented)."""

    name: ClassVar[str] = "s3"
    config_schema: ClassVar[type[BaseModel]] = S3Config

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        return []

    def __init__(self, config: S3Config | None = None) -> None:
        self._config = config

    async def setup(self, ctx: AppContext) -> None:
        raise NotImplementedError(
            "S3Provider is a P2 placeholder; concrete adapter ships in a future release."
        )

    async def shutdown(self) -> None:
        pass

    async def health_check(self) -> HealthStatus:
        return HealthStatus.fail("S3Provider is a P2 placeholder (not yet implemented)")


__all__ = ["S3Provider"]
