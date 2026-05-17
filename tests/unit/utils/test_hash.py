"""Tests for hwhkit.utils.hash."""

from __future__ import annotations

from hwhkit.utils.hash import (
    constant_time_compare,
    random_token,
    sha256_hex,
    sha256_hmac_hex,
)


def test_sha256_hex_known_value() -> None:
    # https://en.wikipedia.org/wiki/SHA-2 — empty string SHA-256
    assert sha256_hex("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_hex_bytes_and_str_equivalent() -> None:
    assert sha256_hex("hello") == sha256_hex(b"hello")


def test_sha256_hmac_hex_deterministic() -> None:
    a = sha256_hmac_hex("k", "data")
    b = sha256_hmac_hex("k", "data")
    assert a == b
    assert sha256_hmac_hex("k2", "data") != a


def test_constant_time_compare() -> None:
    assert constant_time_compare("abc", "abc") is True
    assert constant_time_compare("abc", "abd") is False
    assert constant_time_compare(b"x", b"x") is True


def test_random_token_unique_and_url_safe() -> None:
    a = random_token()
    b = random_token()
    assert a != b
    assert len(a) >= 40
    # url-safe: no + / =
    assert "+" not in a
    assert "/" not in a
    assert "=" not in a
