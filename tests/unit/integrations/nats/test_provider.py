"""Unit tests for NatsProvider (no real NATS server)."""

from __future__ import annotations

import pytest
from hwhkit.core.contracts.message_bus import MessageBus
from hwhkit.core.errors import NatsConnectionError
from hwhkit.integrations.nats import NatsConfig, NatsProvider


def test_provider_metadata() -> None:
    p = NatsProvider()
    assert p.name == "nats"
    assert p.config_schema is NatsConfig


def test_implements_message_bus() -> None:
    assert MessageBus in NatsProvider().implements


def test_client_access_before_setup_raises() -> None:
    with pytest.raises(NatsConnectionError, match="before setup"):
        _ = NatsProvider().client


def test_js_access_before_setup_raises() -> None:
    with pytest.raises(NatsConnectionError, match="not initialized"):
        _ = NatsProvider().js


@pytest.mark.asyncio
async def test_health_check_fails_when_not_ready() -> None:
    p = NatsProvider()
    status = await p.health_check()
    assert status.healthy is False


@pytest.mark.asyncio
async def test_publish_when_not_ready() -> None:
    p = NatsProvider()
    with pytest.raises(NatsConnectionError):
        await p.publish("x", b"y")
