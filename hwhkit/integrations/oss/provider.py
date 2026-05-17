"""Aliyun OSSProvider (P2 placeholder).

Concrete implementation reserved for a future release.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.integrations.oss.config import OssConfig

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext


class OssProvider(IntegrationProvider):
    """Aliyun OSS adapter (placeholder — not yet implemented)."""

    name: ClassVar[str] = "oss"
    config_schema: ClassVar[type[BaseModel]] = OssConfig

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        return []

    def __init__(self, config: OssConfig | None = None) -> None:
        self._config = config

    async def setup(self, ctx: AppContext) -> None:
        raise NotImplementedError(
            "Aliyun OSSProvider is a P2 placeholder; concrete adapter ships in a future release."
        )

    async def shutdown(self) -> None:
        pass

    async def health_check(self) -> HealthStatus:
        return HealthStatus.fail("Aliyun OSSProvider is a P2 placeholder (not yet implemented)")


__all__ = ["OssProvider"]
