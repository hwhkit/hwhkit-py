"""Tests for the dataclass payloads in contract modules."""

from __future__ import annotations

from datetime import timedelta

from hwhkit.core.contracts.llm import ChatMessage, ChatResponse
from hwhkit.core.contracts.lock import LockToken
from hwhkit.core.contracts.message_bus import PublishAck
from hwhkit.core.contracts.object_store import ObjectMetadata
from hwhkit.core.contracts.vector_store import SearchHit, VectorRecord


def test_lock_token_frozen() -> None:
    tok = LockToken(key="k", token="t", ttl=timedelta(seconds=30))
    assert tok.key == "k"
    assert tok.token == "t"
    assert tok.ttl.total_seconds() == 30


def test_publish_ack() -> None:
    ack = PublishAck(subject="x.y", sequence=42, duplicate=False)
    assert ack.subject == "x.y"
    assert ack.sequence == 42
    assert ack.duplicate is False


def test_object_metadata() -> None:
    meta = ObjectMetadata(
        key="path/to/file",
        size=1024,
        etag="abc",
        content_type="application/json",
        last_modified=1700000000.0,
    )
    assert meta.size == 1024


def test_vector_record_default_payload() -> None:
    rec = VectorRecord(id="v1", vector=[0.1, 0.2])
    assert rec.payload == {}


def test_search_hit() -> None:
    hit = SearchHit(id="v1", score=0.95, payload={"label": "match"})
    assert hit.score == 0.95


def test_chat_message_optional_name() -> None:
    msg = ChatMessage(role="user", content="hi")
    assert msg.name is None
    msg2 = ChatMessage(role="tool", content="result", name="search_tool")
    assert msg2.name == "search_tool"


def test_chat_response_default_raw() -> None:
    resp = ChatResponse(
        content="hello",
        model="gpt-4",
        finish_reason="stop",
        usage={"prompt_tokens": 5, "completion_tokens": 1},
    )
    assert resp.raw == {}
