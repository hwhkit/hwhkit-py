"""Unit tests for LlmProvider (no real LLM calls)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from hwhkit.core.contracts.llm import ChatMessage, EmbeddingClient, LlmClient
from hwhkit.llm import LlmConfig, LlmProvider


def test_provider_metadata() -> None:
    p = LlmProvider()
    assert p.name == "llm"
    assert p.config_schema is LlmConfig


def test_implements_llm_and_embedding_contracts() -> None:
    impls = LlmProvider().implements
    assert LlmClient in impls
    assert EmbeddingClient in impls


@pytest.mark.asyncio
async def test_health_check_fails_before_setup() -> None:
    p = LlmProvider()
    assert (await p.health_check()).healthy is False


@pytest.mark.asyncio
async def test_chat_invokes_litellm() -> None:
    p = LlmProvider()
    p._litellm = type(  # type: ignore[attr-defined]
        "_FakeLitellm",
        (),
        {
            "acompletion": AsyncMock(
                return_value={
                    "model": "fake-model",
                    "choices": [
                        {
                            "message": {"content": "hello"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1},
                }
            )
        },
    )()
    p._is_ready = True

    result = await p.chat(
        [ChatMessage(role="user", content="hi")],
        model="fake-model",
    )
    assert result.content == "hello"
    assert result.model == "fake-model"
    assert result.finish_reason == "stop"
    assert result.usage == {"prompt_tokens": 5, "completion_tokens": 1}


@pytest.mark.asyncio
async def test_embed_invokes_litellm() -> None:
    p = LlmProvider()
    p._litellm = type(  # type: ignore[attr-defined]
        "_FakeLitellm",
        (),
        {
            "aembedding": AsyncMock(
                return_value={"data": [{"embedding": [0.1, 0.2, 0.3]}, {"embedding": [0.4]}]}
            )
        },
    )()
    p._is_ready = True

    result = await p.embed(["text1", "text2"], model="emb-model")
    assert result == [[0.1, 0.2, 0.3], [0.4]]


@pytest.mark.asyncio
async def test_chat_raises_when_not_ready() -> None:
    p = LlmProvider()
    with pytest.raises(RuntimeError, match="not ready"):
        await p.chat([ChatMessage(role="user", content="hi")], model="x")
