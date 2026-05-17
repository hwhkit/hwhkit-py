"""Scheduler config schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SchedulerConfig(BaseModel):
    """APScheduler-based scheduler config."""

    timezone: str = Field(default="UTC")
    jobstore: Literal["memory", "redis", "postgres"] = "memory"
    # When jobstore != memory, lock_key_prefix coordinates which scheduler
    # instance "owns" each job (only one instance executes a given lock_key
    # at a time).
    lock_key_prefix: str = "hwhkit:scheduler:lock:"
    # If True, the scheduler refuses to start jobs without lock_key when
    # multiple instances are detected (best-effort fail-fast).
    require_lock_in_distributed_mode: bool = True


__all__ = ["SchedulerConfig"]
