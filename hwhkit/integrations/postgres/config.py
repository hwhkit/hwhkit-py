"""Postgres adapter configuration schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    """SQLAlchemy 2.0 async engine config.

    DSN example: ``postgresql+asyncpg://user:pwd@host:5432/dbname``
    """

    dsn: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        description="SQLAlchemy URL for asyncpg driver",
    )
    pool_size: int = Field(default=10, ge=1, le=200)
    max_overflow: int = Field(default=5, ge=0, le=200)
    pool_pre_ping: bool = True
    pool_recycle_seconds: int = Field(default=3600, ge=0)
    echo: bool = False  # log every SQL statement; dev-only


__all__ = ["PostgresConfig"]
