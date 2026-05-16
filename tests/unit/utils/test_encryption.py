"""Tests for hwhkit.utils.encryption."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidTag
from hwhkit.utils.encryption import KEY_SIZE, decrypt, encrypt, generate_key


def test_generate_key_size() -> None:
    k = generate_key()
    assert len(k) == KEY_SIZE


def test_encrypt_decrypt_roundtrip() -> None:
    key = generate_key()
    pt = b"the quick brown fox"
    ct = encrypt(key, pt)
    assert ct != pt
    assert len(ct) > len(pt)  # nonce + tag
    assert decrypt(key, ct) == pt


def test_encrypt_with_associated_data() -> None:
    key = generate_key()
    pt = b"data"
    aad = b"context-id"
    ct = encrypt(key, pt, associated_data=aad)
    assert decrypt(key, ct, associated_data=aad) == pt


def test_wrong_aad_fails() -> None:
    key = generate_key()
    ct = encrypt(key, b"x", associated_data=b"ctx-1")
    with pytest.raises(InvalidTag):
        decrypt(key, ct, associated_data=b"ctx-2")


def test_wrong_key_fails() -> None:
    ct = encrypt(generate_key(), b"x")
    with pytest.raises(InvalidTag):
        decrypt(generate_key(), ct)


def test_invalid_key_size() -> None:
    with pytest.raises(ValueError, match="key must"):
        encrypt(b"short", b"x")
    with pytest.raises(ValueError, match="key must"):
        decrypt(b"short", b"x" * 32)


def test_blob_too_short() -> None:
    with pytest.raises(ValueError, match="too short"):
        decrypt(generate_key(), b"x")


def test_each_encrypt_has_different_nonce() -> None:
    """Same key+plaintext should produce different ciphertexts due to random nonce."""
    key = generate_key()
    ct1 = encrypt(key, b"same")
    ct2 = encrypt(key, b"same")
    assert ct1 != ct2
    assert decrypt(key, ct1) == decrypt(key, ct2) == b"same"
