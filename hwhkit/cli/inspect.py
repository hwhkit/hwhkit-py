"""``hwhkit doctor`` / ``hwhkit list`` — project introspection helpers."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Known hwhkit extras that map to integrations
_KNOWN_EXTRAS = {
    "postgres",
    "redis",
    "nats",
    "mysql",
    "qdrant",
    "mongodb",
    "neo4j",
    "s3",
    "oss",
    "scheduler",
    "llm",
    "otel",
    "web",
    "jwt",
    "cli",
}


@dataclass
class DoctorReport:
    problems: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


def list_integrations(project_root: Path) -> set[str]:
    """Return the set of hwhkit extras declared in ``project_root/pyproject.toml``."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return set()
    data = tomllib.loads(pyproject.read_text("utf-8"))
    deps = data.get("project", {}).get("dependencies", [])
    found: set[str] = set()
    for dep in deps:
        # Match "hwhkit[postgres,redis]==X" or "hwhkit[postgres]>=X"
        m = re.match(r"^\s*hwhkit\s*\[([^\]]+)\]", dep)
        if m:
            for extra in m.group(1).split(","):
                extra = extra.strip().lower()
                if extra in _KNOWN_EXTRAS:
                    found.add(extra)
    return found


def diagnose(project_root: Path) -> DoctorReport:
    """Run lightweight checks on the project at ``project_root``."""
    report = DoctorReport()
    pyproject = project_root / "pyproject.toml"

    if not pyproject.is_file():
        report.problems.append("pyproject.toml not found in project root")
        return report

    data = tomllib.loads(pyproject.read_text("utf-8"))
    project = data.get("project", {})
    deps = project.get("dependencies", [])

    has_hwhkit = any(d.strip().lower().startswith("hwhkit") for d in deps)
    if not has_hwhkit:
        report.problems.append("'hwhkit' dependency not declared in pyproject.toml")
    else:
        extras = list_integrations(project_root)
        report.info.append(
            f"hwhkit extras enabled: {sorted(extras)}"
            if extras
            else "hwhkit installed without extras"
        )

    # Check for a main.py file under the package directory
    name = project.get("name", "")
    if name:
        module = name.replace("-", "_")
        main = project_root / module / "main.py"
        if not main.is_file():
            report.problems.append(f"expected {main.relative_to(project_root)} not found")
        else:
            report.info.append(f"entry point: {main.relative_to(project_root)}")

    return report


__all__ = ["DoctorReport", "diagnose", "list_integrations"]
