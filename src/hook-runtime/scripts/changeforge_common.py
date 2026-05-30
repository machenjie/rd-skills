#!/usr/bin/env python3
"""Common helpers for ChangeForge hook runtime scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


STATE_LIST_FIELDS = (
    "changed_paths",
    "structure_findings",
    "risk_surfaces",
    "suggested_skills",
    "suggested_capabilities",
    "suggested_domain_extensions",
    "suggested_gates",
)
KNOWN_RUNTIMES = {"codex", "claude"}
HOOK_MODES = {"off", "monitor", "warn", "block"}
PATH_KEYS = {
    "file",
    "file_path",
    "filePath",
    "path",
    "paths",
    "files",
    "changed_file",
    "changedFile",
    "changed_files",
    "changedFiles",
    "target_file",
    "targetFile",
}
EXCLUDED_PATH_KEYS = {
    "cwd",
    "root",
    "repo",
    "repository",
    "project",
    "project_dir",
    "projectDir",
    "transcript_path",
    "transcriptPath",
}
PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File:\s+(.+?)\s*$")
DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)\s*$")
DIFF_FILE_RE = re.compile(r"^(?:\+\+\+|---)\s+(?:a/|b/)?(.+?)\s*$")


def read_event() -> dict:
    """Read hook event JSON from stdin. Return {} on invalid input."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def detect_runtime(event: dict) -> str:
    """Return codex / claude / unknown."""
    runtime_value = event.get("runtime") or event.get("agent") or event.get("runtimeName")
    if isinstance(runtime_value, str):
        runtime = runtime_value.strip().casefold()
        if "codex" in runtime:
            return "codex"
        if "claude" in runtime:
            return "claude"

    if "hookEventName" in event or "toolName" in event or "toolInput" in event:
        return "codex"
    if "hook_event_name" in event or "tool_name" in event or "tool_input" in event:
        return "claude"
    return "unknown"


def event_name(event: dict) -> str:
    """Normalize hook_event_name / hookEventName."""
    value = (
        event.get("hook_event_name")
        or event.get("hookEventName")
        or event.get("event_name")
        or event.get("eventName")
        or ""
    )
    return value.strip() if isinstance(value, str) else ""


def tool_name(event: dict) -> str:
    """Normalize tool name."""
    value = event.get("tool_name") or event.get("toolName") or event.get("name")
    if isinstance(value, str):
        return value.strip()
    tool = event.get("tool")
    if isinstance(tool, dict):
        name = tool.get("name")
        return name.strip() if isinstance(name, str) else ""
    if isinstance(tool, str):
        return tool.strip()
    return ""


def extract_changed_paths(event: dict) -> list[str]:
    """Extract changed file paths from Edit/Write/MultiEdit/apply_patch payloads."""
    paths: list[str] = []

    def visit(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                normalized_key = str(child_key)
                if normalized_key in EXCLUDED_PATH_KEYS:
                    continue
                if normalized_key in PATH_KEYS:
                    collect_path_value(child_value)
                    continue
                visit(child_value, normalized_key)
            return
        if isinstance(value, list):
            for item in value:
                visit(item, key)
            return
        if isinstance(value, str) and ("*** Begin Patch" in value or "diff --git" in value):
            paths.extend(_extract_paths_from_patch_text(value))

    def collect_path_value(value: Any) -> None:
        if isinstance(value, str):
            candidate = _clean_path(value)
            if _looks_like_file_path(candidate):
                paths.append(candidate)
            return
        if isinstance(value, list):
            for item in value:
                collect_path_value(item)
            return
        if isinstance(value, dict):
            visit(value)

    visit(event)
    return _unique(paths)


def extract_bash_command(event: dict) -> str:
    """Extract Bash command from event."""
    containers: list[Any] = [
        event,
        event.get("tool_input"),
        event.get("toolInput"),
        event.get("input"),
        event.get("arguments"),
        event.get("parameters"),
        event.get("params"),
    ]
    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in ("command", "cmd", "bash", "script"):
            value = container.get(key)
            if isinstance(value, str):
                return value.strip()
    return ""


def repo_root(cwd: str | None) -> Path:
    """Use git rev-parse --show-toplevel; fallback to cwd."""
    base = Path(cwd or os.getcwd()).expanduser()
    try:
        base = base.resolve()
    except OSError:
        pass

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(base),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
    except Exception:
        return base
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).expanduser().resolve()
    return base


def load_state(repo: Path) -> dict:
    """Load per-turn hook state."""
    path = _state_path(repo)
    if not path.is_file():
        return _empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _empty_state()
    if not isinstance(data, dict):
        return _empty_state()
    state = _empty_state()
    state.update({key: value for key, value in data.items() if key in state})
    for key in STATE_LIST_FIELDS:
        if not isinstance(state.get(key), list):
            state[key] = []
    if not isinstance(state.get("validation_seen"), bool):
        state["validation_seen"] = False
    return state


def save_state(repo: Path, state: dict) -> None:
    """Save per-turn hook state."""
    path = _state_path(repo)
    next_state = _empty_state()
    next_state.update({key: value for key, value in state.items() if key in next_state})
    for key in STATE_LIST_FIELDS:
        next_state[key] = _unique(str(item) for item in next_state.get(key, []) if str(item))
    next_state["validation_seen"] = bool(next_state.get("validation_seen"))
    next_state["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(next_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"ChangeForge Hook Runtime warning: unable to save hook state: {exc}")


def emit_warning(runtime: str, message: str) -> None:
    """Emit runtime-compatible additional context."""
    if runtime not in KNOWN_RUNTIMES:
        return
    text = message.strip()
    if text:
        print(text)


def emit_block(runtime: str, reason: str) -> None:
    """Only used when hook mode is block."""
    if runtime not in KNOWN_RUNTIMES:
        return
    print(json.dumps({"decision": "block", "reason": reason.strip()}, sort_keys=True))


def hook_mode() -> str:
    mode = os.environ.get("CHANGEFORGE_HOOK_MODE", "warn").strip().casefold()
    return mode if mode in HOOK_MODES else "warn"


def cwd_from_event(event: dict) -> str | None:
    for key in ("cwd", "project_dir", "projectDir", "workspace", "workspaceRoot"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PWD")


def is_post_tool_use(event: dict) -> bool:
    name = event_name(event)
    return not name or _compact(name) == "posttooluse"


def is_stop(event: dict) -> bool:
    return _compact(event_name(event)) == "stop"


def merge_state(
    repo: Path,
    runtime: str,
    *,
    changed_paths: Iterable[str] = (),
    structure_findings: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
    suggested_skills: Iterable[str] = (),
    suggested_capabilities: Iterable[str] = (),
    suggested_domain_extensions: Iterable[str] = (),
    suggested_gates: Iterable[str] = (),
    validation_seen: bool | None = None,
) -> dict:
    state = load_state(repo)
    state["runtime"] = runtime
    for key, values in (
        ("changed_paths", changed_paths),
        ("structure_findings", structure_findings),
        ("risk_surfaces", risk_surfaces),
        ("suggested_skills", suggested_skills),
        ("suggested_capabilities", suggested_capabilities),
        ("suggested_domain_extensions", suggested_domain_extensions),
        ("suggested_gates", suggested_gates),
    ):
        state[key] = _unique([*state.get(key, []), *[str(value) for value in values if str(value)]])
    if validation_seen is not None:
        state["validation_seen"] = bool(state.get("validation_seen")) or validation_seen
    save_state(repo, state)
    return state


def clear_state(repo: Path, runtime: str) -> None:
    state = _empty_state()
    state["runtime"] = runtime
    save_state(repo, state)


def compact_name(value: str) -> str:
    return _compact(value)


def normalize_path(path: str) -> str:
    return _clean_path(path).replace("\\", "/").lstrip("./")


def _state_path(repo: Path) -> Path:
    cache_root = os.environ.get("XDG_CACHE_HOME")
    base = Path(cache_root).expanduser() if cache_root else Path.home() / ".cache"
    try:
        repo_key = str(repo.expanduser().resolve())
    except OSError:
        repo_key = str(repo)
    repo_hash = hashlib.sha256(repo_key.encode("utf-8")).hexdigest()[:24]
    return base / "changeforge" / "hooks" / repo_hash / "current-turn.json"


def _empty_state() -> dict:
    return {
        "runtime": "unknown",
        "changed_paths": [],
        "structure_findings": [],
        "risk_surfaces": [],
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_domain_extensions": [],
        "suggested_gates": [],
        "validation_seen": False,
        "updated_at": "",
    }


def _extract_paths_from_patch_text(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        patch_match = PATCH_FILE_RE.match(line.strip())
        if patch_match:
            paths.append(_clean_path(patch_match.group(1)))
            continue
        diff_match = DIFF_GIT_RE.match(line.strip())
        if diff_match:
            paths.append(_clean_path(diff_match.group(2)))
            continue
        file_match = DIFF_FILE_RE.match(line.strip())
        if file_match:
            candidate = _clean_path(file_match.group(1))
            if candidate != "/dev/null":
                paths.append(candidate)
    return [path for path in paths if _looks_like_file_path(path)]


def _clean_path(value: str) -> str:
    cleaned = value.strip().strip("'\"")
    for prefix in ("a/", "b/"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned


def _looks_like_file_path(value: str) -> bool:
    if not value or "\n" in value or "\0" in value:
        return False
    if "://" in value:
        return False
    if value.startswith(("{", "[")):
        return False
    if len(value) > 500:
        return False
    return "/" in value or "\\" in value or "." in Path(value).name


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
