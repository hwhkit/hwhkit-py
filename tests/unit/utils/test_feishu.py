"""Tests for hwhkit.utils.notification.feishu."""

from __future__ import annotations

import pytest
import respx
from httpx import HTTPStatusError, Response
from hwhkit.utils.notification.feishu import FeishuNotifier

WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/abc123"


def test_requires_url() -> None:
    with pytest.raises(ValueError, match="webhook_url"):
        FeishuNotifier("")


@pytest.mark.asyncio
async def test_sends_card_payload() -> None:
    notifier = FeishuNotifier(WEBHOOK)
    with respx.mock(base_url=WEBHOOK) as mock:
        route = mock.post("").mock(return_value=Response(200, json={"code": 0}))
        await notifier.notify("hello", "world", severity="info")
        assert route.called
        request = route.calls.last.request
        body = request.read()
        # Verify it's a card payload
        assert b"interactive" in body
        assert b"hello" in body
        assert b"world" in body
        assert b"blue" in body  # severity=info → blue template


@pytest.mark.asyncio
async def test_severity_to_template() -> None:
    notifier = FeishuNotifier(WEBHOOK)
    for sev, color in [("warning", "orange"), ("error", "red"), ("critical", "carmine")]:
        with respx.mock(base_url=WEBHOOK) as mock:
            mock.post("").mock(return_value=Response(200, json={"code": 0}))
            await notifier.notify("t", "b", severity=sev)  # type: ignore[arg-type]
            body = mock.calls.last.request.read()
            assert color.encode() in body


@pytest.mark.asyncio
async def test_signed_request_includes_sign_and_timestamp() -> None:
    notifier = FeishuNotifier(WEBHOOK, secret="topsecret")
    with respx.mock(base_url=WEBHOOK) as mock:
        mock.post("").mock(return_value=Response(200, json={"code": 0}))
        await notifier.notify("t", "b")
        body = mock.calls.last.request.read()
        assert b"timestamp" in body
        assert b"sign" in body


@pytest.mark.asyncio
async def test_non_2xx_raises() -> None:
    notifier = FeishuNotifier(WEBHOOK)
    with respx.mock(base_url=WEBHOOK) as mock:
        mock.post("").mock(return_value=Response(500))
        with pytest.raises(HTTPStatusError):
            await notifier.notify("t", "b")


def test_satisfies_notifier_contract() -> None:
    """FeishuNotifier must satisfy the Notifier protocol structurally."""
    from hwhkit.core.contracts.notifier import Notifier

    n = FeishuNotifier(WEBHOOK)
    assert isinstance(n, Notifier)
