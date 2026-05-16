"""ObjectStore contract — bucket-based binary blob storage.

Implementations: S3, OSS, MinIO (all P2).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    key: str
    size: int
    etag: str
    content_type: str | None
    last_modified: float  # unix timestamp


@runtime_checkable
class ObjectStore(Protocol):
    async def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> ObjectMetadata: ...

    async def get(self, key: str) -> bytes: ...

    def stream(self, key: str) -> AsyncIterator[bytes]: ...

    async def delete(self, key: str) -> bool: ...

    async def exists(self, key: str) -> bool: ...

    def list_objects(self, prefix: str = "") -> AsyncIterator[ObjectMetadata]: ...

    async def presigned_url(
        self,
        key: str,
        ttl_seconds: int = 3600,
        method: str = "GET",
    ) -> str: ...


__all__ = ["ObjectMetadata", "ObjectStore"]
