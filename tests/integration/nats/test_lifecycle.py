"""Lifecycle + publish/subscribe smoke for real NATS."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hwhkit.integrations.nats import NatsProvider

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health_check(nats_provider: NatsProvider) -> None:
    status = await nats_provider.health_check()
    assert status.healthy is True


@pytest.mark.asyncio
async def test_publish_subscribe_roundtrip(nats_provider: NatsProvider) -> None:
    received: list[bytes] = []

    async def handler(msg) -> None:
        received.append(msg.payload)

    sub = await nats_provider.subscribe("test.subj", handler)
    await asyncio.sleep(0.1)  # settle
    ack = await nats_provider.publish("test.subj", b'{"id":1}')
    assert ack.subject == "test.subj"
    # Wait up to 2s for delivery
    for _ in range(40):
        if received:
            break
        await asyncio.sleep(0.05)
    await sub.unsubscribe()
    assert received == [b'{"id":1}']


@pytest.mark.asyncio
async def test_request_reply(nats_provider: NatsProvider) -> None:
    from datetime import timedelta

    async def replier(msg) -> None:
        # Use the underlying client to send the reply (request/reply
        # via NATS uses an inbox subject).
        await nats_provider.client.publish(msg._raw.reply, b"pong")

    sub = await nats_provider.subscribe("test.req", replier)
    await asyncio.sleep(0.1)
    resp = await nats_provider.request("test.req", b"ping", timeout=timedelta(seconds=2))
    await sub.unsubscribe()
    assert resp == b"pong"


@pytest.mark.asyncio
async def test_publish_when_not_ready_after_shutdown(nats_provider: NatsProvider) -> None:
    from hwhkit.core.errors import NatsConnectionError

    await nats_provider.shutdown()
    with pytest.raises(NatsConnectionError):
        await nats_provider.publish("x", b"y")
