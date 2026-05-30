#!/usr/bin/env python3
"""Validate ChangeForge hook runtime source and templates."""

from __future__ import annotations

import json
import py_compile
import re
from pathlib import Path
from typing import Any

from validation_utils import fail_many, relpath


ROOT = Path(__file__).resolve().parents[1]
HOOK_RUNTIME_ROOT = ROOT / "src" / "hook-runtime"
HOOK_SCRIPTS_DIR = HOOK_RUNTIME_ROOT / "scripts"
HOOK_SCHEMAS_DIR = HOOK_RUNTIME_ROOT / "schemas"
CODEX_TEMPLATE = HOOK_RUNTIME_ROOT / "templates" / "codex" / "hooks.json"
CLAUDE_TEMPLATE = (
    HOOK_RUNTIME_ROOT
    / "templates"
    / "claude"
    / "settings.changeforge-hooks.fragment.json"
)
REQUIRED_HOOK_SCRIPTS = (
    "changeforge_common.py",
    "changeforge_post_edit_structure_gate.py",
    "changeforge_risk_surface_gate.py",
    "changeforge_stop_closure_gate.py",
)
NETWORK_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|urllib|urllib3|socket)\b",
    re.MULTILINE,
)
USER_ABSOLUTE_PATH_RE = re.compile(
    r"(/home/[^ \"]+|/Users/[^ \"]+|/mnt/[a-zA-Z]/Users/[^ \"]+|[A-Za-z]:\\\\Users\\\\)"
)
PROJECT_SOURCE_WRITE_RE = re.compile(
    r"(repo\s*/|cwd\s*/|project\s*/|source\s*/).*(write_text|write_bytes|open\()"
)


def main() -> int:
    errors: list[str] = []

    _validate_required_files(errors)
    _validate_python_files(errors)
    _validate_schema_files(errors)
    codex = _load_json(CODEX_TEMPLATE, errors)
    claude = _load_json(CLAUDE_TEMPLATE, errors)
    if isinstance(codex, dict):
        _validate_template(codex, CODEX_TEMPLATE, timeout_limit=10, errors=errors)
    if isinstance(claude, dict):
        _validate_template(claude, CLAUDE_TEMPLATE, timeout_limit=10000, errors=errors)

    if errors:
        return fail_many("validate-hooks", errors)
    print("validate-hooks: validated hook runtime scripts and templates.")
    return 0


def _validate_required_files(errors: list[str]) -> None:
    if not HOOK_SCRIPTS_DIR.is_dir():
        errors.append("missing hook script directory: src/hook-runtime/scripts")
        return
    for file_name in REQUIRED_HOOK_SCRIPTS:
        path = HOOK_SCRIPTS_DIR / file_name
        if not path.is_file():
            errors.append(f"missing hook script: {relpath(ROOT, path)}")
    for path in (CODEX_TEMPLATE, CLAUDE_TEMPLATE):
        if not path.is_file():
            errors.append(f"missing hook template: {relpath(ROOT, path)}")


def _validate_schema_files(errors: list[str]) -> None:
    if not HOOK_SCHEMAS_DIR.is_dir():
        errors.append("missing hook schema directory: src/hook-runtime/schemas")
        return
    for path in sorted(HOOK_SCHEMAS_DIR.glob("*.json")):
        _load_json(path, errors)


def _validate_python_files(errors: list[str]) -> None:
    if not HOOK_SCRIPTS_DIR.is_dir():
        return
    for path in sorted(HOOK_SCRIPTS_DIR.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{relpath(ROOT, path)}: py_compile failed: {exc.msg}")
        text = path.read_text(encoding="utf-8")
        if NETWORK_IMPORT_RE.search(text):
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not make network requests")
        if "requests." in text or "httpx." in text or "urllib." in text:
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not make network requests")
        if "shutil.rmtree" in text or ".unlink(" in text or ".rename(" in text:
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not modify project source")
        if PROJECT_SOURCE_WRITE_RE.search(text):
            errors.append(f"{relpath(ROOT, path)}: hook scripts must not write project source")

    stop_script = HOOK_SCRIPTS_DIR / "changeforge_stop_closure_gate.py"
    if stop_script.is_file():
        text = stop_script.read_text(encoding="utf-8")
        if "emit_warning(" in text:
            errors.append("changeforge_stop_closure_gate.py: Stop hook must not use emit_warning")
        if "emit_stop_reminder(" not in text:
            errors.append("changeforge_stop_closure_gate.py: Stop hook must use emit_stop_reminder")

    common_script = HOOK_SCRIPTS_DIR / "changeforge_common.py"
    if common_script.is_file():
        common_text = common_script.read_text(encoding="utf-8")
        if "hookSpecificOutput" not in common_text or "additionalContext" not in common_text:
            errors.append(
                "changeforge_common.py: Codex warnings must use hookSpecificOutput.additionalContext"
            )
        if "CHANGEFORGE_AGENT" not in common_text:
            errors.append("changeforge_common.py: detect_runtime must support CHANGEFORGE_AGENT override")


def _load_json(path: Path, errors: list[str]) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{relpath(ROOT, path)}: invalid JSON: {exc}")
        return None


def _validate_template(
    data: dict[str, Any],
    path: Path,
    *,
    timeout_limit: int,
    errors: list[str],
) -> None:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        errors.append(f"{relpath(ROOT, path)}: hooks must be a JSON object")
        return
    for required_event in ("PostToolUse", "Stop"):
        if required_event not in hooks:
            errors.append(f"{relpath(ROOT, path)}: missing {required_event} hook")

    for command, context in _commands(hooks):
        lowered = command.casefold()
        if "src/" in lowered or "src\\" in lowered:
            errors.append(f"{relpath(ROOT, path)}:{context}: hook command must not reference src/")
        if USER_ABSOLUTE_PATH_RE.search(command):
            errors.append(
                f"{relpath(ROOT, path)}:{context}: hook command must not contain a user absolute path"
            )
        if path == CODEX_TEMPLATE and "CHANGEFORGE_AGENT=codex" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Codex hook command must set CHANGEFORGE_AGENT=codex"
            )
        if path == CODEX_TEMPLATE and "/usr/bin/env python3" not in command:
            errors.append(
                f"{relpath(ROOT, path)}:{context}: Codex hook command should use /usr/bin/env python3"
            )

    for timeout, context in _timeouts(hooks):
        if timeout > timeout_limit:
            limit_label = "10000 ms" if timeout_limit == 10000 else "10 seconds"
            errors.append(
                f"{relpath(ROOT, path)}:{context}: timeout {timeout} exceeds {limit_label}"
            )


def _commands(value: Any, context: str = "hooks") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, dict):
        command = value.get("command")
        if isinstance(command, str):
            result.append((command, context))
        for key, child in value.items():
            result.extend(_commands(child, f"{context}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_commands(child, f"{context}[{index}]"))
    return result


def _timeouts(value: Any, context: str = "hooks") -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    if isinstance(value, dict):
        timeout = value.get("timeout")
        if isinstance(timeout, int):
            result.append((timeout, context))
        for key, child in value.items():
            result.extend(_timeouts(child, f"{context}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_timeouts(child, f"{context}[{index}]"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
