"""AES-256-GCM symmetric encryption.

Format: ``nonce(12 bytes) || ciphertext_with_tag``.

Use ``generate_key()`` to produce keys (32 bytes / 256 bits).
"""

from __future__ import annotations

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_SIZE = 32  # 256-bit AES
NONCE_SIZE = 12  # 96-bit nonce (recommended for GCM)


def generate_key() -> bytes:
    """Return a fresh 32-byte AES-256 key."""
    return secrets.token_bytes(KEY_SIZE)


def encrypt(key: bytes, plaintext: bytes, *, associated_data: bytes | None = None) -> bytes:
    """Encrypt with AES-256-GCM. Returns ``nonce || ciphertext+tag``.

    Args:
        key: 32-byte secret key.
        plaintext: bytes to encrypt.
        associated_data: optional AAD bound to the ciphertext (not encrypted).
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key must be {KEY_SIZE} bytes (got {len(key)})")
    nonce = secrets.token_bytes(NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return nonce + ciphertext


def decrypt(key: bytes, blob: bytes, *, associated_data: bytes | None = None) -> bytes:
    """Decrypt the output of ``encrypt``.

    Raises:
        ValueError: invalid key size or blob too short.
        cryptography.exceptions.InvalidTag: tampered ciphertext or wrong key/AAD.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key must be {KEY_SIZE} bytes (got {len(key)})")
    if len(blob) < NONCE_SIZE + 16:  # nonce + min AES-GCM tag
        raise ValueError("blob too short")
    nonce, ct = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
    return AESGCM(key).decrypt(nonce, ct, associated_data)


__all__ = ["KEY_SIZE", "NONCE_SIZE", "decrypt", "encrypt", "generate_key"]
