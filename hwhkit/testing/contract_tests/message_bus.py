"""Reusable conformance tests for ``MessageBus`` contract."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hwhkit.core.contracts.message_bus import Message, MessageBus


class MessageBusContractTests:
    """Inherit and provide an async ``bus`` fixture."""

    @pytest.mark.asyncio
    async def test_publish_then_subscribe_delivers(self, bus: MessageBus) -> None:
        received: list[bytes] = []

        async def handler(msg: Message) -> None:
            received.append(msg.payload)

        sub = await bus.subscribe("trades.executed", handler)
        await asyncio.sleep(0.05)  # let subscriber settle
        await bus.publish("trades.executed", b'{"id":1}')
        # Allow message round-trip
        for _ in range(20):
            if received:
                break
            await asyncio.sleep(0.05)
        await sub.unsubscribe()
        assert received == [b'{"id":1}']

    @pytest.mark.asyncio
    async def test_subscribe_unrelated_subject_not_delivered(self, bus: MessageBus) -> None:
        received: list[bytes] = []

        async def handler(msg: Message) -> None:
            received.append(msg.payload)

        sub = await bus.subscribe("a.b", handler)
        await asyncio.sleep(0.05)
        await bus.publish("a.c", b"unrelated")
        await asyncio.sleep(0.2)
        await sub.unsubscribe()
        assert received == []

    @pytest.mark.asyncio
    async def test_unsubscribe_stops_delivery(self, bus: MessageBus) -> None:
        received: list[bytes] = []

        async def handler(msg: Message) -> None:
            received.append(msg.payload)

        sub = await bus.subscribe("evt", handler)
        await asyncio.sleep(0.05)
        await sub.unsubscribe()
        await asyncio.sleep(0.05)
        await bus.publish("evt", b"after-unsub")
        await asyncio.sleep(0.2)
        assert received == []
