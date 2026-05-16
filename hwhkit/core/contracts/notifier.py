"""Notifier contract — outbound human-facing notifications (chat, email, sms).

Implementations: Feishu (P1), DingTalk / email / SMS (future).
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

Severity = Literal["info", "warning", "error", "critical"]


@runtime_checkable
class Notifier(Protocol):
    async def notify(
        self,
        title: str,
        body: str,
        *,
        severity: Severity = "info",
        target: str | None = None,
    ) -> None: ...


__all__ = ["Notifier", "Severity"]
