"""Aliyun OSS adapter config (P2 placeholder)."""

from __future__ import annotations

from pydantic import BaseModel


class OssConfig(BaseModel):
    """Aliyun OSS configuration (placeholder)."""

    endpoint: str = "https://oss-cn-hangzhou.aliyuncs.com"
    bucket: str = "hwhkit"
