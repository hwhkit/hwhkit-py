"""Neo4j adapter config (P2 placeholder)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Neo4jConfig(BaseModel):
    """Neo4j configuration (placeholder)."""

    uri: str = Field(default="bolt://localhost:7687")
    user: str = Field(default="neo4j")
    password: str = Field(default="neo4j")
