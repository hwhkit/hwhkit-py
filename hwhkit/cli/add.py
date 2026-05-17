"""``hwhkit add <module>`` — incremental integration add.

For each module:
1. Update ``pyproject.toml`` dependencies to enable the matching ``hwhkit[...]`` extra.
2. Patch ``<project>/<module>/main.py`` via libcst:
   - Add ``from hwhkit.integrations.<x> import XProvider``.
   - Append ``XProvider()`` to the ``integrations=[]`` argument of ``bootstrap()``.
3. Append a ``.env.example`` block with required environment vars.
4. Idempotent: re-running for the same module is a no-op (detects existing
   import + Provider instance).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import libcst as cst

# Module spec for the supported add targets
_MODULE_SPECS: dict[str, dict[str, str]] = {
    "postgres": {
        "import": "from hwhkit.integrations.postgres import PostgresProvider",
        "provider_call": "PostgresProvider()",
        "extra": "postgres",
        "env_block": (
            "\n# Postgres\n"
            "HWHKIT_POSTGRES__DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres\n"
        ),
    },
    "redis": {
        "import": "from hwhkit.integrations.redis import RedisProvider",
        "provider_call": "RedisProvider()",
        "extra": "redis",
        "env_block": "\n# Redis\nHWHKIT_REDIS__URL=redis://localhost:6379/0\n",
    },
    "nats": {
        "import": "from hwhkit.integrations.nats import NatsProvider",
        "provider_call": "NatsProvider()",
        "extra": "nats",
        "env_block": '\n# NATS\nHWHKIT_NATS__SERVERS=["nats://localhost:4222"]\n',
    },
    "scheduler": {
        "import": "from hwhkit.scheduler import SchedulerProvider",
        "provider_call": "SchedulerProvider()",
        "extra": "scheduler",
        "env_block": "\n# Scheduler\nHWHKIT_SCHEDULER__TIMEZONE=UTC\n",
    },
    "llm": {
        "import": "from hwhkit.llm import LlmProvider",
        "provider_call": "LlmProvider()",
        "extra": "llm",
        "env_block": "\n# LLM (litellm)\n# OPENAI_API_KEY=...\n# ANTHROPIC_API_KEY=...\n",
    },
    "otel": {
        "import": "",  # observability is config-only, not an integration
        "provider_call": "",
        "extra": "otel",
        "env_block": (
            "\n# Observability (OTel)\n"
            "HWHKIT_OBSERVABILITY__ENABLED=true\n"
            "HWHKIT_OBSERVABILITY__EXPORTER=otlp_http\n"
            "HWHKIT_OBSERVABILITY__ENDPOINT=http://localhost:4318\n"
        ),
    },
    "auth": {
        "import": "",  # AuthMiddleware is wired via build_app explicitly, not bootstrap
        "provider_call": "",
        "extra": "jwt",
        "env_block": "\n# JWT auth\n# HWHKIT_AUTH__JWKS_URL=https://your-issuer/.well-known/jwks.json\n",
    },
}


@dataclass
class AddResult:
    module: str
    pyproject_modified: bool = False
    main_py_modified: bool = False
    env_modified: bool = False
    skipped_reason: str | None = None
    dry_run: bool = False

    def __str__(self) -> str:
        prefix = "[dry-run] " if self.dry_run else ""
        if self.skipped_reason:
            return f"{prefix}{self.module}: {self.skipped_reason}"
        actions = []
        if self.pyproject_modified:
            actions.append("pyproject.toml extras")
        if self.main_py_modified:
            actions.append("main.py")
        if self.env_modified:
            actions.append(".env.example")
        if not actions:
            return f"{prefix}{self.module}: nothing to do (already added)"
        return f"{prefix}✓ {self.module}: updated {', '.join(actions)}"


def add_modules(project_root: Path, module: str, *, dry_run: bool = False) -> AddResult:
    if module not in _MODULE_SPECS:
        return AddResult(module=module, skipped_reason=f"unknown module: {module}")

    spec = _MODULE_SPECS[module]
    result = AddResult(module=module, dry_run=dry_run)

    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        result.skipped_reason = "pyproject.toml not found"
        return result

    # 1. pyproject extras
    new_pyproject = _add_extra_to_pyproject(pyproject.read_text("utf-8"), spec["extra"])
    if new_pyproject is not None:
        result.pyproject_modified = True
        if not dry_run:
            pyproject.write_text(new_pyproject, encoding="utf-8")

    # 2. main.py (only if Provider exists for this module)
    if spec["provider_call"]:
        main_py = _find_main_py(project_root)
        if main_py is not None:
            new_main = _patch_main_py(
                main_py.read_text("utf-8"), spec["import"], spec["provider_call"]
            )
            if new_main is not None:
                result.main_py_modified = True
                if not dry_run:
                    main_py.write_text(new_main, encoding="utf-8")

    # 3. .env.example
    env_file = project_root / ".env.example"
    if env_file.is_file() and spec["env_block"].strip() not in env_file.read_text("utf-8"):
        result.env_modified = True
        if not dry_run:
            with env_file.open("a", encoding="utf-8") as f:
                f.write(spec["env_block"])

    return result


# ---- pyproject.toml editing (regex-based, scoped to `hwhkit[...]` dep) ----


def _add_extra_to_pyproject(content: str, extra: str) -> str | None:
    """Return modified content with extra added to hwhkit[...] dep, or None if unchanged."""
    pattern = re.compile(r'("hwhkit\s*\[)([^\]]+)(\][^"]*")')
    match = pattern.search(content)
    if not match:
        # Try without brackets: "hwhkit==X" → "hwhkit[extra]==X"
        bare = re.compile(r'("hwhkit)(==|>=|~=|@| )')
        m2 = bare.search(content)
        if not m2:
            return None
        return bare.sub(rf"\1[{extra}]\2", content, count=1)

    existing = [e.strip() for e in match.group(2).split(",")]
    if extra in existing:
        return None  # idempotent
    existing.append(extra)
    new_brackets = ",".join(sorted(existing))
    return pattern.sub(rf"\1{new_brackets}\3", content, count=1)


# ---- main.py CST editing --------------------------------------------------


def _find_main_py(project_root: Path) -> Path | None:
    """Locate the project's ``main.py`` — look one level deep under project_root."""
    for child in project_root.iterdir():
        if not child.is_dir():
            continue
        if child.name in {"tests", ".venv", "venv", "dist", "build", ".git"}:
            continue
        candidate = child / "main.py"
        if candidate.is_file():
            return candidate
    return None


def _patch_main_py(content: str, import_line: str, provider_call: str) -> str | None:
    """Run libcst transformation; return new code or None if unchanged."""
    try:
        module = cst.parse_module(content)
    except cst.ParserSyntaxError:
        return None

    transformer = _AddIntegrationTransformer(import_line=import_line, provider_call=provider_call)
    new_module = module.visit(transformer)
    if not transformer.changed:
        return None
    return new_module.code


class _AddIntegrationTransformer(cst.CSTTransformer):
    """Add an import line + append Provider() to bootstrap(integrations=[...])."""

    def __init__(self, *, import_line: str, provider_call: str) -> None:
        self.import_line = import_line
        self.provider_call = provider_call
        self.changed = False
        # Track if import is already present
        self._import_present = False
        # Track if Provider is already in integrations=[...]
        self._provider_present = False

    # Phase 1: detect existing import / provider
    def visit_Module(self, node: cst.Module) -> None:
        text = node.code
        if self.import_line in text:
            self._import_present = True
        # Strip outer parens of provider call for substring check
        bare_call = self.provider_call.replace("()", "")
        if bare_call in text and self.provider_call in text:
            self._provider_present = True

    # Phase 2: rewrite
    def leave_Module(self, original: cst.Module, updated: cst.Module) -> cst.Module:
        new_body = list(updated.body)
        if not self._import_present:
            # Insert import after existing imports (simplest: at top)
            new_import_stmt = cst.parse_statement(
                self.import_line, config=updated.config_for_parsing
            )
            # Find insertion point: after last leading import
            insert_at = 0
            for i, stmt in enumerate(new_body):
                if (
                    isinstance(stmt, cst.SimpleStatementLine)
                    and stmt.body
                    and isinstance(stmt.body[0], (cst.Import, cst.ImportFrom))
                ):
                    insert_at = i + 1
            new_body.insert(insert_at, new_import_stmt)
            self.changed = True
        return updated.with_changes(body=new_body)

    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        # Find bootstrap(...) call
        func = updated.func
        if not isinstance(func, cst.Name) or func.value != "bootstrap":
            return updated

        # Find the integrations= keyword arg
        new_args = list(updated.args)
        for idx, arg in enumerate(new_args):
            kw = arg.keyword
            if not isinstance(kw, cst.Name) or kw.value != "integrations":
                continue
            value = arg.value
            if not isinstance(value, cst.List):
                continue
            # Check if our Provider() call is already in the list
            already = any(self._element_matches(e) for e in value.elements)
            if already:
                self._provider_present = True
                return updated
            # Append new element
            try:
                new_call = cst.parse_expression(self.provider_call)
            except cst.ParserSyntaxError:
                return updated
            new_elements = list(value.elements) + [cst.Element(value=new_call)]
            new_list = value.with_changes(elements=new_elements)
            new_args[idx] = arg.with_changes(value=new_list)
            self.changed = True
            return updated.with_changes(args=new_args)
        return updated

    def _element_matches(self, element: cst.BaseElement) -> bool:
        # Inspect element.value as code and compare bare names
        try:
            code = cst.Module(body=[]).code_for_node(element.value)
            return code.strip() == self.provider_call.strip()
        except Exception:
            return False


__all__ = ["AddResult", "add_modules"]
