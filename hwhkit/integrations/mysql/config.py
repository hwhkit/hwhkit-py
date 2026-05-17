"""MySQL adapter config (P2 placeholder)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MySQLConfig(BaseModel):
    """MySQL configuration (placeholder)."""

    dsn: str = Field(default="mysql+asyncmy://root:root@localhost:3306/db")
