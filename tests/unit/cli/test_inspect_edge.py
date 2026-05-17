"""Edge cases for hwhkit.cli.inspect (list_integrations + diagnose)."""

from __future__ import annotations

from pathlib import Path

from hwhkit.cli.inspect import diagnose, list_integrations


def test_list_when_no_pyproject(tmp_path: Path) -> None:
    assert list_integrations(tmp_path) == set()


def test_list_dep_without_brackets(tmp_path: Path) -> None:
    """A plain `hwhkit==X` dep yields an empty extras set (no brackets)."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["hwhkit==0.4.0a1"]\n'
    )
    assert list_integrations(tmp_path) == set()


def test_list_unknown_extra_filtered(tmp_path: Path) -> None:
    """Unknown extras are filtered out (defensive)."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["hwhkit[postgres,bogus]==0.4.0a1"]\n'
    )
    assert list_integrations(tmp_path) == {"postgres"}


def test_diagnose_missing_pyproject(tmp_path: Path) -> None:
    report = diagnose(tmp_path)
    assert any("pyproject.toml not found" in p for p in report.problems)


def test_diagnose_no_hwhkit_dep(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["requests==2.0"]\n'
    )
    report = diagnose(tmp_path)
    assert any("hwhkit" in p for p in report.problems)


def test_diagnose_missing_main(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["hwhkit[web]==0.4.0a1"]\n'
    )
    report = diagnose(tmp_path)
    assert any("main.py" in p for p in report.problems)


def test_diagnose_healthy_with_main(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["hwhkit[web]==0.4.0a1"]\n'
    )
    pkg = tmp_path / "demo"
    pkg.mkdir()
    (pkg / "main.py").write_text("# entry point")
    report = diagnose(tmp_path)
    assert report.problems == []
    assert any("entry point" in i for i in report.info)
