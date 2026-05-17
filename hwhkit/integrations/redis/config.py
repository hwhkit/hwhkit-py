"""Redis adapter configuration schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RedisConfig(BaseModel):
    """redis.asyncio.Redis client config."""

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL (redis:// or rediss:// for TLS)",
    )
    max_connections: int = Field(default=20, ge=1, le=1000)
    socket_timeout: float = Field(default=5.0, ge=0)
    socket_connect_timeout: float = Field(default=5.0, ge=0)
    health_check_interval: int = Field(default=30, ge=0)
    decode_responses: bool = False  # framework deals in bytes; codec is caller's


__all__ = ["RedisConfig"]
