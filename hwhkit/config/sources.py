"""Layered config loader.

Precedence (highest wins):
1. ``overrides`` argument (init kwargs, for tests)
2. Environment variables (``HWHKIT_*``)
3. YAML file at ``yaml_path`` (or ``$HWHKIT_CONFIG``, or ``./config.yaml``)
4. ``.env`` file
5. Defaults in Settings subclass

Implementation uses pydantic-settings's ``settings_customise_sources`` hook to
insert a YAML source between env and dotenv in the priority chain.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import yaml
from pydantic_settings import PydanticBaseSettingsSource

from hwhkit.config.base import Settings

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo
    from pydantic_settings import BaseSettings

T = TypeVar("T", bound=Settings)


class _YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """pydantic-settings source that reads from a YAML file."""

    def __init__(self, settings_cls: type[BaseSettings], yaml_path: Path) -> None:
        super().__init__(settings_cls)
        self._data: dict[str, Any] = {}
        if yaml_path.is_file():
            with yaml_path.open() as f:
                loaded = yaml.safe_load(f) or {}
            if not isinstance(loaded, Mapping):
                raise ValueError(
                    f"YAML root in {yaml_path} must be a mapping, got {type(loaded).__name__}"
                )
            self._data = dict(loaded)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        value = self._data.get(field_name)
        return value, field_name, False

    def __call__(self) -> dict[str, Any]:
        return self._data


def _resolve_yaml_path(explicit: str | Path | None) -> Path:
    if explicit is not None:
        return Path(explicit)
    return Path(os.environ.get("HWHKIT_CONFIG", "config.yaml"))


def load_settings(
    settings_cls: type[T] = Settings,  # type: ignore[assignment]
    *,
    yaml_path: str | Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> T:
    """Load settings with layered sources (kwargs > env > yaml > .env > defaults).

    Args:
        settings_cls: Settings subclass to instantiate.
        yaml_path: Optional explicit YAML path; falls back to ``$HWHKIT_CONFIG``
                   then to ``./config.yaml``.
        overrides: dict applied as init kwargs (test convenience, highest priority).

    Returns:
        Settings instance.
    """
    resolved_yaml = _resolve_yaml_path(yaml_path)
    yaml_source: PydanticBaseSettingsSource | None = None
    if resolved_yaml.is_file():
        yaml_source = _YamlConfigSettingsSource(settings_cls, resolved_yaml)

    # Inject yaml between env and dotenv via the customise hook
    class _Loader(settings_cls):  # type: ignore[misc, valid-type]
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls_: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            sources: list[PydanticBaseSettingsSource] = [
                init_settings,
                env_settings,
            ]
            if yaml_source is not None:
                # Rebind to the actual subclass for proper field resolution
                bound = _YamlConfigSettingsSource(settings_cls_, resolved_yaml)
                sources.append(bound)
            sources.append(dotenv_settings)
            sources.append(file_secret_settings)
            return tuple(sources)

    # InitSettingsSource takes our overrides dict; pydantic flattens nested dicts.
    init_kwargs: dict[str, Any] = overrides or {}
    instance = _Loader(**init_kwargs)
    return instance


__all__ = ["load_settings"]
