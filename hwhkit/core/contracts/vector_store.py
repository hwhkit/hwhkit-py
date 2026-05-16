"""VectorStore contract — semantic / similarity vector search.

Implementations: Qdrant (P2), Milvus / Pinecone (future).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class VectorRecord:
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SearchHit:
    id: str
    score: float
    payload: dict[str, Any]


@runtime_checkable
class VectorStore(Protocol):
    async def ensure_collection(
        self,
        name: str,
        dim: int,
        distance: str = "cosine",
    ) -> None: ...

    async def upsert(self, collection: str, records: list[VectorRecord]) -> None: ...

    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchHit]: ...

    async def delete(self, collection: str, ids: list[str]) -> int: ...


__all__ = ["SearchHit", "VectorRecord", "VectorStore"]
