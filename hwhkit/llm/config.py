"""LLM provider config schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LlmConfig(BaseModel):
    """litellm-backed LLM provider config.

    Most settings (API keys) are read from environment by litellm directly
    (``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY`` / etc.) — we don't duplicate.
    """

    default_chat_model: str = Field(default="claude-sonnet-4-20250514")
    default_embedding_model: str = Field(default="text-embedding-3-small")
    default_temperature: float = Field(default=0.7, ge=0, le=2)
    default_max_tokens: int | None = Field(default=None, ge=1)
    request_timeout_seconds: float = Field(default=60.0, ge=1)


__all__ = ["LlmConfig"]
