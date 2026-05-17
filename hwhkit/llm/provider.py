"""LlmProvider — litellm-backed adapter implementing ``LlmClient`` + ``EmbeddingClient``.

litellm transparently dispatches to OpenAI / Anthropic / DeepSeek / Moonshot /
Ollama / Bedrock / Azure / etc. based on model prefix (e.g. ``openai/gpt-4``,
``anthropic/claude-sonnet-4``, ``ollama/qwen2.5``). The framework does NOT
pre-set API keys — those come from environment variables.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from hwhkit.core.contracts.llm import ChatMessage, ChatResponse
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.llm.config import LlmConfig

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext

_logger = logging.getLogger(__name__)


class LlmProvider(IntegrationProvider):
    """litellm wrapper. Implements ``LlmClient`` + ``EmbeddingClient`` contracts."""

    name: ClassVar[str] = "llm"
    config_schema: ClassVar[type[BaseModel]] = LlmConfig

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        from hwhkit.core.contracts.llm import EmbeddingClient, LlmClient

        return [LlmClient, EmbeddingClient]

    def __init__(self, config: LlmConfig | None = None) -> None:
        self._config = config
        self._litellm: Any = None
        self._is_ready: bool = False

    async def setup(self, ctx: AppContext) -> None:
        try:
            import litellm
        except ImportError as exc:
            raise ImportError(
                "LlmProvider requires hwhkit[llm] extras: pip install 'hwhkit[llm]'"
            ) from exc

        self._litellm = litellm
        # litellm has a global "drop_params" mode useful to avoid 4xx on mixed
        # model providers when caller passes args one provider doesn't support
        litellm.drop_params = True
        self._is_ready = True

    async def shutdown(self) -> None:
        self._litellm = None
        self._is_ready = False

    async def health_check(self) -> HealthStatus:
        if not self._is_ready:
            return HealthStatus.fail("llm provider not ready")
        # Don't ping providers from health_check (too expensive / requires API keys)
        return HealthStatus.ok("litellm loaded")

    # ---- LlmClient contract ----------------------------------------------
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        if not self._is_ready:
            raise RuntimeError("LlmProvider not ready")
        cfg = self._resolved_config()
        result = await self._litellm.acompletion(
            model=model or cfg.default_chat_model,
            messages=[self._serialize(m) for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=cfg.request_timeout_seconds,
        )
        choice = result["choices"][0]
        msg = choice["message"]
        return ChatResponse(
            content=msg.get("content", "") or "",
            model=result.get("model", model),
            finish_reason=choice.get("finish_reason", "stop"),
            usage=dict(result.get("usage", {}) or {}),
            raw=dict(result),
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        if not self._is_ready:
            raise RuntimeError("LlmProvider not ready")
        cfg = self._resolved_config()
        stream = await self._litellm.acompletion(
            model=model or cfg.default_chat_model,
            messages=[self._serialize(m) for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            timeout=cfg.request_timeout_seconds,
        )
        async for chunk in stream:
            try:
                delta = chunk["choices"][0]["delta"]
                content = delta.get("content")
                if content:
                    yield content
            except (KeyError, IndexError):
                continue

    # ---- EmbeddingClient contract ----------------------------------------
    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
    ) -> list[list[float]]:
        if not self._is_ready:
            raise RuntimeError("LlmProvider not ready")
        cfg = self._resolved_config()
        result = await self._litellm.aembedding(
            model=model or cfg.default_embedding_model,
            input=texts,
            timeout=cfg.request_timeout_seconds,
        )
        return [item["embedding"] for item in result["data"]]

    # ---- helpers ----------------------------------------------------------
    @staticmethod
    def _serialize(msg: ChatMessage) -> dict[str, Any]:
        out: dict[str, Any] = {"role": msg.role, "content": msg.content}
        if msg.name is not None:
            out["name"] = msg.name
        return out

    def _resolved_config(self) -> LlmConfig:
        if self._config is None:
            return LlmConfig()
        return self._config


__all__ = ["LlmProvider"]
