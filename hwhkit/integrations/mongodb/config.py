"""MongoDB adapter config (P2 placeholder)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MongoDBConfig(BaseModel):
    """MongoDB configuration (placeholder)."""

    uri: str = Field(default="mongodb://localhost:27017")
    database: str = Field(default="hwhkit")
