"""Smoke test: pytest infrastructure works."""

from __future__ import annotations


def test_truth() -> None:
    assert True


def test_can_import_hwhkit() -> None:
    import hwhkit

    assert hwhkit.__version__ == "0.4.0a1"
