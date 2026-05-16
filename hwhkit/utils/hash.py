"""Hash + password helpers."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def sha256_hex(data: bytes | str) -> str:
    """SHA-256 of ``data``, returned as 64-char lowercase hex."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_hmac_hex(key: bytes | str, data: bytes | str) -> str:
    """HMAC-SHA256 of ``data`` under ``key``, returned as hex."""
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def constant_time_compare(a: str | bytes, b: str | bytes) -> bool:
    """Timing-safe equality comparison (defends against timing attacks)."""
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hmac.compare_digest(a, b)


def random_token(num_bytes: int = 32) -> str:
    """Cryptographically-secure random URL-safe token (default ~43 chars)."""
    return secrets.token_urlsafe(num_bytes)


__all__ = [
    "constant_time_compare",
    "random_token",
    "sha256_hex",
    "sha256_hmac_hex",
]
