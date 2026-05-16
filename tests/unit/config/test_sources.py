"""Tests for hwhkit.config.sources — layered loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from hwhkit.config import Settings, load_settings


class TestLoadSettings:
    def test_defaults_when_no_sources(self, tmp_path: Path) -> None:
        # change cwd to tmp_path so no stray ./config.yaml is picked up
        s = load_settings(yaml_path=tmp_path / "nonexistent.yaml")
        assert s.app.name == "hwhkit-app"

    def test_yaml_loaded(self, tmp_path: Path) -> None:
        yaml = tmp_path / "config.yaml"
        yaml.write_text("app:\n  name: from-yaml\n  version: 1.2.3\nweb:\n  port: 9090\n")
        s = load_settings(yaml_path=yaml)
        assert s.app.name == "from-yaml"
        assert s.app.version == "1.2.3"
        assert s.web.port == 9090

    def test_overrides_win_over_yaml(self, tmp_path: Path) -> None:
        yaml = tmp_path / "config.yaml"
        yaml.write_text("app:\n  name: from-yaml\n")
        s = load_settings(yaml_path=yaml, overrides={"app": {"name": "from-override"}})
        assert s.app.name == "from-override"

    def test_env_wins_over_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        yaml = tmp_path / "config.yaml"
        yaml.write_text("app:\n  name: from-yaml\n")
        monkeypatch.setenv("HWHKIT_APP__NAME", "from-env")
        s = load_settings(yaml_path=yaml)
        assert s.app.name == "from-env"

    def test_overrides_win_over_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HWHKIT_APP__NAME", "from-env")
        s = load_settings(
            yaml_path=tmp_path / "nonexistent.yaml",
            overrides={"app": {"name": "from-override"}},
        )
        assert s.app.name == "from-override"

    def test_empty_yaml_treated_as_empty_dict(self, tmp_path: Path) -> None:
        yaml = tmp_path / "config.yaml"
        yaml.write_text("")
        s = load_settings(yaml_path=yaml)
        assert s.app.name == "hwhkit-app"

    def test_yaml_root_must_be_mapping(self, tmp_path: Path) -> None:
        yaml = tmp_path / "config.yaml"
        yaml.write_text("- 1\n- 2\n")
        with pytest.raises(ValueError, match="mapping"):
            load_settings(yaml_path=yaml)

    def test_yaml_path_from_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        yaml = tmp_path / "custom.yaml"
        yaml.write_text("app:\n  name: via-env-path\n")
        monkeypatch.setenv("HWHKIT_CONFIG", str(yaml))
        s = load_settings()
        assert s.app.name == "via-env-path"

    def test_deep_merge_preserves_other_keys(self, tmp_path: Path) -> None:
        yaml = tmp_path / "config.yaml"
        yaml.write_text("web:\n  port: 7000\n  cors:\n    allow_origins:\n      - 'https://a'\n")
        s = load_settings(
            yaml_path=yaml,
            overrides={"web": {"port": 8888}},  # 不应该把 cors 顶掉
        )
        assert s.web.port == 8888
        assert s.web.cors.allow_origins == ["https://a"]

    def test_returns_subclass(self, tmp_path: Path) -> None:
        class MySettings(Settings):
            extra: str = "default"

        s = load_settings(MySettings, yaml_path=tmp_path / "nonexistent.yaml")
        assert isinstance(s, MySettings)
        assert s.extra == "default"
