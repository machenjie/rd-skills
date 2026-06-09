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
BOOTSTRAP_TEMPLATE = (
    HOOK_RUNTIME_ROOT / "templates" / "bootstrap" / "changeforge-route-preflight.md"
)
REQUIRED_HOOK_SCRIPTS = (
    "changeforge_common.py",
    "changeforge_session_bootstrap.py",
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
GIT_MUTATION_RE = re.compile(
    r"git\s+(commit|checkout|reset|push|rebase|cherry-pick|clean|stash)\b"
)
STATE_FINDING_FIELDS = (
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
)


def main() -> int:
    errors: list[str] = []

    _validate_required_files(errors)
    _validate_python_files(errors)
    _validate_schema_files(errors)
    _validate_bootstrap_fragment(errors)
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
        if GIT_MUTATION_RE.search(text):
            errors.append(
                f"{relpath(ROOT, path)}: hook scripts must not run mutating git commands"
            )

    stop_script = HOOK_SCRIPTS_DIR / "changeforge_stop_closure_gate.py"
    if stop_script.is_file():
        text = stop_script.read_text(encoding="utf-8")
        if "emit_warning(" in text:
            errors.append("changeforge_stop_closure_gate.py: Stop hook must not use emit_warning")
        if "emit_stop_reminder(" not in text:
            errors.append("changeforge_stop_closure_gate.py: Stop hook must use emit_stop_reminder")

    bootstrap_script = HOOK_SCRIPTS_DIR / "changeforge_session_bootstrap.py"
    if bootstrap_script.is_file():
        bootstrap_text = bootstrap_script.read_text(encoding="utf-8")
        if "is_session_start(" not in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must gate on is_session_start"
            )
        if "emit_session_context(" not in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must use emit_session_context"
            )
        if "emit_stop_reminder(" in bootstrap_text or "emit_block(" in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must not block or emit a stop reminder"
            )
        if '"decision"' in bootstrap_text or "'decision'" in bootstrap_text:
            errors.append(
                "changeforge_session_bootstrap.py: bootstrap must not emit a block decision"
            )

    structure_script = HOOK_SCRIPTS_DIR / "changeforge_post_edit_structure_gate.py"
    if structure_script.is_file():
        structure_text = structure_script.read_text(encoding="utf-8")
        for field in STATE_FINDING_FIELDS:
            if field not in structure_text:
                errors.append(
                    f"changeforge_post_edit_structure_gate.py: structure gate must populate {field}"
                )

    common_script = HOOK_SCRIPTS_DIR / "changeforge_common.py"
    if common_script.is_file():
        common_text = common_script.read_text(encoding="utf-8")
        if "hookSpecificOutput" not in common_text or "additionalContext" not in common_text:
            errors.append(
                "changeforge_common.py: Codex warnings must use hookSpecificOutput.additionalContext"
            )
        if "CHANGEFORGE_AGENT" not in common_text:
            errors.append("changeforge_common.py: detect_runtime must support CHANGEFORGE_AGENT override")
        if "def is_session_start(" not in common_text:
            errors.append("changeforge_common.py: must define is_session_start for the bootstrap")
        if "def emit_session_context(" not in common_text:
            errors.append("changeforge_common.py: must define emit_session_context for the bootstrap")
        for field in STATE_FINDING_FIELDS:
            if field not in common_text:
                errors.append(
                    f"changeforge_common.py: hook state must track {field}"
                )


def _validate_bootstrap_fragment(errors: list[str]) -> None:
    if not BOOTSTRAP_TEMPLATE.is_file():
        errors.append(f"missing bootstrap fragment: {relpath(ROOT, BOOTSTRAP_TEMPLATE)}")
        return
    text = BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
    if USER_ABSOLUTE_PATH_RE.search(text):
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must not contain a user absolute path"
        )
    if "change-forge-router" not in text:
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must point to change-forge-router"
        )
    if "implementation-structure-design" not in text:
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must reference implementation-structure-design"
        )
    if "agent-execution-discipline" not in text:
        errors.append(
            f"{relpath(ROOT, BOOTSTRAP_TEMPLATE)}: bootstrap fragment must reference agent-execution-discipline"
        )


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

    # The route-preflight bootstrap is wired as a SessionStart hook for Claude
    # only. Codex has no stable session-start hook, so it must not declare one;
    # Codex relies on the install-time bootstrap fragment instead.
    if path == CLAUDE_TEMPLATE:
        session_start = hooks.get("SessionStart")
        if not isinstance(session_start, list) or not session_start:
            errors.append(
                f"{relpath(ROOT, path)}: Claude template must wire a SessionStart bootstrap hook"
            )
        elif not any(
            "changeforge_session_bootstrap" in command
            for command, _context in _commands({"SessionStart": session_start})
        ):
            errors.append(
                f"{relpath(ROOT, path)}: SessionStart must invoke changeforge_session_bootstrap"
            )
    if path == CODEX_TEMPLATE and "SessionStart" in hooks:
        errors.append(
            f"{relpath(ROOT, path)}: Codex has no stable session-start hook; "
            "use the install-time bootstrap fragment instead of a SessionStart hook"
        )

    matchers = _post_tool_matchers(hooks)
    if not any("edit" in matcher.casefold() for matcher in matchers):
        errors.append(
            f"{relpath(ROOT, path)}: PostToolUse must include an Edit/Write/MultiEdit matcher"
        )
    if not any("bash" in matcher.casefold() for matcher in matchers):
        errors.append(f"{relpath(ROOT, path)}: PostToolUse must include a Bash matcher")
    if path == CODEX_TEMPLATE and not any(
        "apply_patch" in matcher.casefold() for matcher in matchers
    ):
        errors.append(
            f"{relpath(ROOT, path)}: Codex PostToolUse must include an apply_patch matcher"
        )

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


def _post_tool_matchers(hooks: dict[str, Any]) -> list[str]:
    matchers: list[str] = []
    post = hooks.get("PostToolUse")
    if isinstance(post, list):
        for entry in post:
            if isinstance(entry, dict):
                matcher = entry.get("matcher")
                if isinstance(matcher, str):
                    matchers.append(matcher)
    return matchers


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
