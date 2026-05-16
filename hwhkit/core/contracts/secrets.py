"""SecretsProvider contract — runtime secret retrieval.

Implementations: env-var (P0 default), AWS Secrets Manager / Vault / Doppler (future).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretsProvider(Protocol):
    async def get(self, name: str) -> str: ...

    async def get_or_default(self, name: str, default: str) -> str: ...


__all__ = ["SecretsProvider"]
