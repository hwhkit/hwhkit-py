"""Qdrant adapter config (P2 placeholder)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QdrantConfig(BaseModel):
    """Qdrant configuration (placeholder)."""

    url: str = Field(default="http://localhost:6333")
    api_key: str | None = None
