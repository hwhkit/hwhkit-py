"""Feishu (飞书) webhook notifier.

Implements the ``Notifier`` contract (hwhkit.core.contracts.notifier).
Posts Lark card-format messages to a custom bot webhook URL.

If ``secret`` is provided, requests are signed per Feishu's HMAC-SHA256
timestamp scheme: ``StringToSign = f"{timestamp}\\n{secret}"``,
``sign = base64(HMAC-SHA256(StringToSign, b""))``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from hwhkit.core.contracts.notifier import Severity

# Visual mapping of hwhkit severity → Feishu card header color
_TEMPLATE = {
    "info": "blue",
    "warning": "orange",
    "error": "red",
    "critical": "carmine",
}


class FeishuNotifier:
    """Webhook-based Feishu notifier; satisfies the ``Notifier`` protocol."""

    def __init__(
        self,
        webhook_url: str,
        *,
        secret: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        if not webhook_url:
            raise ValueError("webhook_url is required")
        self._url = webhook_url
        self._secret = secret
        self._timeout = timeout

    async def notify(
        self,
        title: str,
        body: str,
        *,
        severity: Severity = "info",
        target: str | None = None,
    ) -> None:
        """Send a card-format message to the configured Feishu webhook.

        Args:
            title:   card header title.
            body:    markdown / plain content for the card body.
            severity: drives card header color (info/warning/error/critical).
            target:   optional ``@user_id`` mention; appended to body.
        """
        payload: dict[str, Any] = self._build_card(title, body, severity, target)
        if self._secret:
            ts = str(int(time.time()))
            payload["timestamp"] = ts
            payload["sign"] = self._sign(ts, self._secret)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._url, json=payload)
            response.raise_for_status()

    # ---- helpers ----------------------------------------------------------
    @staticmethod
    def _sign(timestamp: str, secret: str) -> str:
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    @staticmethod
    def _build_card(
        title: str, body: str, severity: Severity, target: str | None
    ) -> dict[str, Any]:
        content_text = body if target is None else f"{body}\n\n<at user_id={target!r}></at>"
        return {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": _TEMPLATE.get(severity, "blue"),
                },
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": content_text}}],
            },
        }


__all__ = ["FeishuNotifier"]
