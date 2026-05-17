"""Unit-level coverage of NatsProvider via mocked nats-py.

Integration tier (tests/integration/nats/) covers the real-container path;
this file drives all the conditional branches with no Docker dependency.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from hwhkit.config.base import Settings
from hwhkit.core.context import AppContext
from hwhkit.core.contracts.message_bus import MessageBus
from hwhkit.core.errors import NatsConnectionError
from hwhkit.integrations.nats import NatsConfig, NatsProvider


def _fake_nc(*, connected: bool = True, ack_seq: int = 42, dup: bool = False) -> Any:
    """Return a MagicMock posing as nats.aio.Client + JetStream context."""
    nc = MagicMock()
    nc.is_connected = connected
    nc.connected_url = "nats://localhost:4222"
    nc.publish = AsyncMock()
    nc.drain = AsyncMock()
    nc.close = AsyncMock()
    nc.subscribe = AsyncMock(return_value=MagicMock(unsubscribe=AsyncMock()))
    reply_msg = MagicMock()
    reply_msg.data = b"pong"
    nc.request = AsyncMock(return_value=reply_msg)

    js = MagicMock()
    js.publish = AsyncMock(return_value=MagicMock(seq=ack_seq, duplicate=dup))
    js.stream_info = AsyncMock()
    js.add_stream = AsyncMock()
    js.subscribe = AsyncMock(return_value=MagicMock(unsubscribe=AsyncMock()))
    nc.jetstream = MagicMock(return_value=js)
    return nc


@pytest.fixture
def provider() -> NatsProvider:
    p = NatsProvider(config=NatsConfig(servers=["nats://x:4222"]))
    return p


@pytest.mark.asyncio
async def test_setup_success(monkeypatch: pytest.MonkeyPatch, provider: NatsProvider) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(return_value=_fake_nc())
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    assert provider._is_ready is True
    assert provider._nc is not None
    assert provider._js is not None
    await provider.shutdown()


@pytest.mark.asyncio
async def test_setup_connection_failure(
    monkeypatch: pytest.MonkeyPatch, provider: NatsProvider
) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(side_effect=ConnectionRefusedError("nope"))
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    with pytest.raises(NatsConnectionError, match="Cannot connect"):
        await provider.setup(ctx)


@pytest.mark.asyncio
async def test_setup_with_ensure_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_nats = MagicMock()
    nc = _fake_nc()
    # stream_info raises -> add_stream called
    nc.jetstream.return_value.stream_info = AsyncMock(side_effect=Exception("not found"))
    fake_nats.connect = AsyncMock(return_value=nc)
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    fake_api = MagicMock()
    fake_api.StreamConfig = MagicMock()
    monkeypatch.setitem(__import__("sys").modules, "nats.js.api", fake_api)

    p = NatsProvider(
        config=NatsConfig(servers=["x"], ensure_stream="TRADES", ensure_subjects=["t.>"])
    )
    ctx = AppContext()
    ctx.config = Settings()
    await p.setup(ctx)
    nc.jetstream.return_value.add_stream.assert_awaited_once()
    await p.shutdown()


@pytest.mark.asyncio
async def test_health_check_connected(
    monkeypatch: pytest.MonkeyPatch, provider: NatsProvider
) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(return_value=_fake_nc(connected=True))
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    status = await provider.health_check()
    assert status.healthy is True
    assert "connected" in status.message.lower()
    await provider.shutdown()


@pytest.mark.asyncio
async def test_health_check_disconnected(
    monkeypatch: pytest.MonkeyPatch, provider: NatsProvider
) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(return_value=_fake_nc(connected=False))
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    status = await provider.health_check()
    assert status.healthy is False
    await provider.shutdown()


@pytest.mark.asyncio
async def test_publish_via_jetstream(
    monkeypatch: pytest.MonkeyPatch, provider: NatsProvider
) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(return_value=_fake_nc(ack_seq=99, dup=True))
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    ack = await provider.publish(
        "test.subj", b"payload", headers={"X": "y"}, deduplication_key="key-1"
    )
    assert ack.sequence == 99
    assert ack.duplicate is True
    await provider.shutdown()


@pytest.mark.asyncio
async def test_publish_jetstream_fallback_to_core(
    monkeypatch: pytest.MonkeyPatch, provider: NatsProvider
) -> None:
    """When JetStream publish fails (no matching stream), fall back to core publish."""
    fake_nats = MagicMock()
    nc = _fake_nc()
    nc.jetstream.return_value.publish = AsyncMock(side_effect=RuntimeError("no stream"))
    fake_nats.connect = AsyncMock(return_value=nc)
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    ack = await provider.publish("test.subj", b"x")
    assert ack.sequence == 0  # core publish sentinel
    nc.publish.assert_awaited_once()
    await provider.shutdown()


@pytest.mark.asyncio
async def test_request_reply(monkeypatch: pytest.MonkeyPatch, provider: NatsProvider) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(return_value=_fake_nc())
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    resp = await provider.request("test.req", b"ping", timeout=timedelta(seconds=1))
    assert resp == b"pong"
    await provider.shutdown()


@pytest.mark.asyncio
async def test_subscribe_ephemeral(monkeypatch: pytest.MonkeyPatch, provider: NatsProvider) -> None:
    fake_nats = MagicMock()
    fake_nats.connect = AsyncMock(return_value=_fake_nc())
    monkeypatch.setitem(__import__("sys").modules, "nats", fake_nats)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)

    async def _h(msg) -> None:
        pass

    sub = await provider.subscribe("test.subj", _h)
    assert sub.subject == "test.subj"
    await sub.unsubscribe()
    await provider.shutdown()


@pytest.mark.asyncio
async def test_publish_when_not_ready(provider: NatsProvider) -> None:
    with pytest.raises(NatsConnectionError):
        await provider.publish("x", b"y")


@pytest.mark.asyncio
async def test_subscribe_when_not_ready(provider: NatsProvider) -> None:
    async def _h(msg) -> None:
        pass

    with pytest.raises(NatsConnectionError):
        await provider.subscribe("x", _h)


@pytest.mark.asyncio
async def test_request_when_not_ready(provider: NatsProvider) -> None:
    with pytest.raises(NatsConnectionError):
        await provider.request("x", b"y")


def test_implements_contract() -> None:
    p = NatsProvider()
    assert MessageBus in p.implements


def test_resolve_config_from_ctx() -> None:
    from pydantic import BaseModel

    class _S(BaseModel):
        nats: NatsConfig = NatsConfig(servers=["nats://ctx-host:1234"])

    p = NatsProvider()
    ctx = AppContext()
    ctx.config = _S()  # type: ignore[assignment]
    cfg = p._resolve_config(ctx)
    assert "ctx-host" in cfg.servers[0]


@pytest.mark.asyncio
async def test_setup_missing_nats_extra(
    monkeypatch: pytest.MonkeyPatch, provider: NatsProvider
) -> None:
    # Make import of 'nats' fail
    import sys

    monkeypatch.setitem(sys.modules, "nats", None)

    ctx = AppContext()
    ctx.config = Settings()
    with pytest.raises(ImportError, match="hwhkit\\[nats\\]"):
        await provider.setup(ctx)
