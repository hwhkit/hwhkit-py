"""LlmClient / EmbeddingClient contracts.

Implementations: litellm-backed (P1), direct OpenAI/Anthropic SDK (future).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str
    name: str | None = None


@dataclass(frozen=True, slots=True)
class ChatResponse:
    content: str
    model: str
    finish_reason: str
    usage: dict[str, int]
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LlmClient(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse: ...

    def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]: ...


@runtime_checkable
class EmbeddingClient(Protocol):
    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
    ) -> list[list[float]]: ...


__all__ = ["ChatMessage", "ChatResponse", "EmbeddingClient", "LlmClient", "Role"]
