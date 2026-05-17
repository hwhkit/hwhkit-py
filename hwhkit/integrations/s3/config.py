"""S3 adapter config (P2 placeholder)."""

from __future__ import annotations

from pydantic import BaseModel


class S3Config(BaseModel):
    """S3 configuration (placeholder)."""

    endpoint_url: str | None = None
    bucket: str = "hwhkit"
    region: str = "us-east-1"
