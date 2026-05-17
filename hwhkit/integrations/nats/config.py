"""NATS adapter config."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NatsConfig(BaseModel):
    """nats.aio.Client config."""

    servers: list[str] = Field(default_factory=lambda: ["nats://localhost:4222"])
    name: str = "hwhkit"
    max_reconnect_attempts: int = 60
    reconnect_time_wait: float = 2.0
    drain_timeout: float = 10.0
    # JetStream storage backing
    jetstream_storage: Literal["file", "memory"] = "file"
    # JetStream stream name to ensure exists on setup
    ensure_stream: str | None = None
    ensure_subjects: list[str] = Field(default_factory=list)


__all__ = ["NatsConfig"]
