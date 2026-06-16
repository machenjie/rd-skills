#!/usr/bin/env python3
"""Common helpers for ChangeForge hook runtime scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from changeforge_state_reducer import reduce_state_update
except ModuleNotFoundError:  # pragma: no cover - importlib test loading fallback
    import importlib.util

    _reducer_path = Path(__file__).with_name("changeforge_state_reducer.py")
    _reducer_spec = importlib.util.spec_from_file_location(
        "changeforge_state_reducer", _reducer_path
    )
    if _reducer_spec is None or _reducer_spec.loader is None:
        raise
    _reducer_module = importlib.util.module_from_spec(_reducer_spec)
    _reducer_spec.loader.exec_module(_reducer_module)
    reduce_state_update = _reducer_module.reduce_state_update


STATE_LIST_FIELDS = (
    "changed_paths",
    "read_paths",
    "read_tools",
    "searched_patterns",
    "structure_findings",
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
    "structure_quality_findings",
    "review_targets",
    "review_findings",
    "repair_findings",
    "risk_surfaces",
    "professional_injections",
    "permission_decisions",
    "reference_loads",
    "subagent_contracts",
    "compaction_snapshots",
    "prompt_signals",
    "suggested_skills",
    "suggested_capabilities",
    "suggested_domain_extensions",
    "suggested_gates",
    "implementation_preflights",
    "pre_edit_structure_findings",
)
STATE_SCALAR_STRING_FIELDS = (
    "turn_stage",
    "owner_skill",
    "reviewer_skill",
)
STATE_BOOL_FIELDS = (
    "stage_route_present",
    "read_intent_seen",
    "read_evidence_seen",
    "reviewed_diff_evidence_seen",
    "review_intent_seen",
    "review_artifact_seen",
    "review_evidence_seen",
    "repair_evidence_seen",
    "permission_gate_seen",
    "professional_contract_seen",
    "implementation_preflight_seen",
    "implementation_preflight_required",
    "implementation_preflight_blocked",
    "pre_edit_missing_read_evidence",
    "pre_edit_missing_reuse_decision",
    "pre_edit_missing_placement_decision",
    "pre_edit_missing_test_plan",
    "edit_without_preflight_seen",
    "post_edit_confirmed_preflight_gap",
    "route_preflight_emitted",
)
KNOWN_RUNTIMES = {"codex", "claude", "copilot", "generic"}
# Runtimes that consume structured JSON stdout. Codex and Claude wrap
# event-specific context in hookSpecificOutput; Copilot command hooks consume
# top-level additionalContext only for context-capable events and top-level
# decision fields for Stop.
JSON_OUTPUT_RUNTIMES = {"codex", "claude", "copilot"}
HOOK_MODES = {"off", "monitor", "warn", "block"}

# Telemetry is an operational fact log written to the user cache. It never
# touches project source, never records prompts, environment variables, secrets,
# or full command output, and always fails open. The schema version lets the
# offline review tooling evolve without breaking older session files.
TELEMETRY_SCHEMA_VERSION = "1"
TELEMETRY_DISABLED_VALUES = {"0", "off", "false", "no"}
TELEMETRY_SUBDIRS = ("sessions", "reports", "suggestions", "promoted")
MAX_TELEMETRY_ITEMS = 50
MAX_TELEMETRY_VALUE_LEN = 300
MAX_STATE_ITEMS = 50
MAX_STATE_VALUE_LEN = 300
MAX_COMMAND_PROGRAM_LEN = 40
ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
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
    """Return codex / claude / copilot / unknown.

    Claude Code, VS Code Copilot, and Codex can all send snake_case event keys,
    so the payload alone is not authoritative. The forced
    ``CHANGEFORGE_AGENT`` env var set by each hook template command is the
    contract; event-key fallback is only for legacy fixtures and best-effort
    local runs.
    """
    forced = os.environ.get("CHANGEFORGE_AGENT", "").strip().casefold()
    if forced in KNOWN_RUNTIMES:
        return forced

    runtime_value = event.get("runtime") or event.get("agent") or event.get("runtimeName")
    if isinstance(runtime_value, str):
        runtime = runtime_value.strip().casefold()
        if "copilot" in runtime:
            return "copilot"
        if "codex" in runtime:
            return "codex"
        if "claude" in runtime:
            return "claude"
        if "generic" in runtime:
            return "generic"

    if "hook_event_name" in event or "tool_name" in event or "tool_input" in event:
        return "codex"
    if "hookEventName" in event or "toolName" in event or "toolInput" in event:
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
    if not isinstance(state.get("active_skill_context"), dict):
        state["active_skill_context"] = {}
    for key in STATE_SCALAR_STRING_FIELDS:
        if not isinstance(state.get(key), str):
            state[key] = ""
    for key in STATE_BOOL_FIELDS:
        if not isinstance(state.get(key), bool):
            state[key] = bool(state.get(key))
    legacy_validation_seen = state.get("validation_seen")
    if not isinstance(state.get("validation_command_seen"), bool):
        state["validation_command_seen"] = bool(legacy_validation_seen)
    # Backward-compatible alias for hook state written by older installations.
    state["validation_seen"] = bool(state.get("validation_command_seen"))
    if not isinstance(state.get("turn_id"), str):
        state["turn_id"] = ""
    return state


def save_state(repo: Path, state: dict) -> None:
    """Save per-turn hook state."""
    path = _state_path(repo)
    next_state = _empty_state()
    next_state.update({key: value for key, value in state.items() if key in next_state})
    for key in STATE_LIST_FIELDS:
        next_state[key] = _capped_state_items(next_state.get(key, []))
    if not isinstance(next_state.get("active_skill_context"), dict):
        next_state["active_skill_context"] = {}
    else:
        next_state["active_skill_context"] = _clean_state_mapping(
            next_state["active_skill_context"]
        )
    for key in STATE_SCALAR_STRING_FIELDS:
        next_state[key] = str(next_state.get(key, "")).strip()[:MAX_STATE_VALUE_LEN]
    for key in STATE_BOOL_FIELDS:
        next_state[key] = bool(next_state.get(key))
    if "validation_command_seen" not in next_state:
        next_state["validation_command_seen"] = bool(next_state.get("validation_seen"))
    next_state["validation_command_seen"] = bool(next_state.get("validation_command_seen"))
    # Keep the legacy key for already-installed state readers while new code uses
    # validation_command_seen for the narrower "command observed" meaning.
    next_state["validation_seen"] = next_state["validation_command_seen"]
    next_state["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(next_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"ChangeForge Hook Runtime warning: unable to save hook state: {exc}", file=sys.stderr)


def emit_warning(runtime: str, hook_event_name: str, message: str) -> None:
    """Emit runtime-compatible additional context for post-tool warnings."""
    if runtime not in KNOWN_RUNTIMES:
        return
    text = message.strip()
    if not text:
        return
    if runtime == "copilot":
        if _compact(hook_event_name) in {"posttooluse", "posttoolusefailure", "notification"}:
            print(json.dumps({"additionalContext": text}, sort_keys=True))
        return
    if runtime in {"codex", "claude"}:
        _emit_hook_specific_context(hook_event_name or "PostToolUse", text)
        return
    print(text)


def emit_stop_reminder(runtime: str, message: str, *, continue_turn: bool) -> None:
    """Emit Stop-compatible output."""
    if runtime not in KNOWN_RUNTIMES:
        return
    text = message.strip()
    if not text:
        return
    if runtime == "copilot":
        if continue_turn:
            print(json.dumps({"decision": "block", "reason": text}, sort_keys=True))
        return
    if runtime == "codex":
        if continue_turn:
            print(json.dumps({"decision": "block", "reason": text}, sort_keys=True))
        else:
            print(json.dumps({"systemMessage": text}, sort_keys=True))
        return
    if runtime == "claude":
        if continue_turn:
            print(json.dumps({"decision": "block", "reason": text}, sort_keys=True))
        else:
            print(json.dumps({"systemMessage": text}, sort_keys=True))
        return


def emit_session_context(runtime: str, message: str, event_name: str = "SessionStart") -> None:
    """Emit additional developer context for a context-injecting hook.

    Used by SessionStart, SubagentStart, and UserPromptSubmit. Codex and Claude
    use hookSpecificOutput.additionalContext; Copilot consumes top-level
    additionalContext for SessionStart and SubagentStart but not
    UserPromptSubmit. This is advisory only: it never emits a block decision,
    never reads references, and fails open. ``event_name`` defaults to
    SessionStart so existing callers keep working.
    """
    if runtime not in KNOWN_RUNTIMES:
        return
    text = message.strip()
    if not text:
        return
    if runtime == "copilot":
        if _compact(event_name) in {"sessionstart", "subagentstart", "notification"}:
            print(json.dumps({"additionalContext": text}, sort_keys=True))
        return
    if runtime in {"codex", "claude"}:
        _emit_hook_specific_context(event_name, text)
        return
    print(text)


def emit_subagent_stop_reminder(runtime: str, message: str) -> None:
    """Emit a SubagentStop-compatible advisory ``systemMessage`` where supported.

    Codex and Claude support advisory ``systemMessage`` output. Claude
    SubagentStop ``additionalContext`` would keep the subagent running, while
    this reminder is intentionally non-continuing. Copilot SubagentStop only
    supports decision control, so this advisory reminder emits nothing there.
    This reminder never returns ``decision: block`` or ``continue: false``.
    """
    if runtime not in KNOWN_RUNTIMES:
        return
    text = message.strip()
    if not text:
        return
    if runtime == "copilot":
        return
    print(json.dumps({"systemMessage": text}, sort_keys=True))


def emit_block(runtime: str, hook_event_name: str, reason: str) -> None:
    """Only used when hook mode is block."""
    if runtime not in KNOWN_RUNTIMES:
        return
    print(json.dumps({"decision": "block", "reason": reason.strip()}, sort_keys=True))


def _emit_hook_specific_context(hook_event_name: str, text: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": hook_event_name,
                    "additionalContext": text,
                }
            },
            sort_keys=True,
        )
    )


def debug_enabled() -> bool:
    return os.environ.get("CHANGEFORGE_HOOK_DEBUG", "").strip().casefold() in {"1", "true", "yes"}


def debug_log(repo: Path, message: str) -> None:
    if not debug_enabled():
        return
    try:
        path = _state_path(repo).with_name("debug.log")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")
    except Exception:
        return


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


def is_pre_tool_use(event: dict) -> bool:
    return _compact(event_name(event)) == "pretooluse"


def is_stop(event: dict) -> bool:
    return _compact(event_name(event)) == "stop"


def is_session_start(event: dict) -> bool:
    return _compact(event_name(event)) == "sessionstart"


def is_user_prompt_submit(event: dict) -> bool:
    return _compact(event_name(event)) == "userpromptsubmit"


def is_subagent_start(event: dict) -> bool:
    return _compact(event_name(event)) == "subagentstart"


def is_subagent_stop(event: dict) -> bool:
    return _compact(event_name(event)) == "subagentstop"


def is_permission_request(event: dict) -> bool:
    """Return true for runtime permission lifecycle events."""
    return _compact(event_name(event)) == "permissionrequest"


def is_compaction_event(event: dict) -> bool:
    """Detect context-compaction events without depending on one vendor field."""
    name = _compact(event_name(event))
    if name in {"compact", "compaction", "contextcompact"}:
        return True
    source = event.get("source") or event.get("reason") or event.get("matcher")
    return isinstance(source, str) and "compact" in source.casefold()


def merge_state(
    repo: Path,
    runtime: str,
    *,
    changed_paths: Iterable[str] = (),
    read_paths: Iterable[str] = (),
    read_tools: Iterable[str] = (),
    searched_patterns: Iterable[str] = (),
    structure_findings: Iterable[str] = (),
    file_naming_findings: Iterable[str] = (),
    reuse_findings: Iterable[str] = (),
    extension_reuse_findings: Iterable[str] = (),
    advanced_refactor_findings: Iterable[str] = (),
    comment_findings: Iterable[str] = (),
    structure_quality_findings: Iterable[str] = (),
    review_targets: Iterable[str] = (),
    review_findings: Iterable[str] = (),
    repair_findings: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
    professional_injections: Iterable[str] = (),
    permission_decisions: Iterable[str] = (),
    reference_loads: Iterable[str] = (),
    subagent_contracts: Iterable[str] = (),
    compaction_snapshots: Iterable[str] = (),
    prompt_signals: Iterable[str] = (),
    suggested_skills: Iterable[str] = (),
    suggested_capabilities: Iterable[str] = (),
    suggested_domain_extensions: Iterable[str] = (),
    suggested_gates: Iterable[str] = (),
    implementation_preflights: Iterable[str] = (),
    pre_edit_structure_findings: Iterable[str] = (),
    validation_command_seen: bool | None = None,
    validation_seen: bool | None = None,
    turn_stage: str | None = None,
    active_skill_context: dict | None = None,
    owner_skill: str | None = None,
    reviewer_skill: str | None = None,
    stage_route_present: bool | None = None,
    read_intent_seen: bool | None = None,
    read_evidence_seen: bool | None = None,
    reviewed_diff_evidence_seen: bool | None = None,
    review_intent_seen: bool | None = None,
    review_artifact_seen: bool | None = None,
    review_evidence_seen: bool | None = None,
    repair_evidence_seen: bool | None = None,
    permission_gate_seen: bool | None = None,
    professional_contract_seen: bool | None = None,
    implementation_preflight_seen: bool | None = None,
    implementation_preflight_required: bool | None = None,
    implementation_preflight_blocked: bool | None = None,
    pre_edit_missing_read_evidence: bool | None = None,
    pre_edit_missing_reuse_decision: bool | None = None,
    pre_edit_missing_placement_decision: bool | None = None,
    pre_edit_missing_test_plan: bool | None = None,
    edit_without_preflight_seen: bool | None = None,
    post_edit_confirmed_preflight_gap: bool | None = None,
) -> dict:
    state = load_state(repo)
    state["runtime"] = runtime
    if not state.get("turn_id"):
        state["turn_id"] = _new_turn_id()
    update = {
        "changed_paths": changed_paths,
        "read_paths": read_paths,
        "read_tools": read_tools,
        "searched_patterns": searched_patterns,
        "structure_findings": structure_findings,
        "file_naming_findings": file_naming_findings,
        "reuse_findings": reuse_findings,
        "extension_reuse_findings": extension_reuse_findings,
        "advanced_refactor_findings": advanced_refactor_findings,
        "comment_findings": comment_findings,
        "structure_quality_findings": structure_quality_findings,
        "review_targets": review_targets,
        "review_findings": review_findings,
        "repair_findings": repair_findings,
        "risk_surfaces": risk_surfaces,
        "professional_injections": professional_injections,
        "permission_decisions": permission_decisions,
        "reference_loads": reference_loads,
        "subagent_contracts": subagent_contracts,
        "compaction_snapshots": compaction_snapshots,
        "prompt_signals": prompt_signals,
        "suggested_skills": suggested_skills,
        "suggested_capabilities": suggested_capabilities,
        "suggested_domain_extensions": suggested_domain_extensions,
        "suggested_gates": suggested_gates,
        "implementation_preflights": implementation_preflights,
        "pre_edit_structure_findings": pre_edit_structure_findings,
        "active_skill_context": active_skill_context,
        "turn_stage": turn_stage,
        "owner_skill": owner_skill,
        "reviewer_skill": reviewer_skill,
        "stage_route_present": stage_route_present,
        "read_intent_seen": read_intent_seen,
        "read_evidence_seen": read_evidence_seen,
        "reviewed_diff_evidence_seen": reviewed_diff_evidence_seen,
        "review_intent_seen": review_intent_seen,
        "review_artifact_seen": review_artifact_seen,
        "review_evidence_seen": review_evidence_seen,
        "repair_evidence_seen": repair_evidence_seen,
        "permission_gate_seen": permission_gate_seen,
        "professional_contract_seen": professional_contract_seen,
        "implementation_preflight_seen": implementation_preflight_seen,
        "implementation_preflight_required": implementation_preflight_required,
        "implementation_preflight_blocked": implementation_preflight_blocked,
        "pre_edit_missing_read_evidence": pre_edit_missing_read_evidence,
        "pre_edit_missing_reuse_decision": pre_edit_missing_reuse_decision,
        "pre_edit_missing_placement_decision": pre_edit_missing_placement_decision,
        "pre_edit_missing_test_plan": pre_edit_missing_test_plan,
        "edit_without_preflight_seen": edit_without_preflight_seen,
        "post_edit_confirmed_preflight_gap": post_edit_confirmed_preflight_gap,
    }
    state = reduce_state_update(
        state, {key: value for key, value in update.items() if value is not None}
    )
    command_seen = validation_command_seen if validation_command_seen is not None else validation_seen
    if command_seen is not None:
        state = reduce_state_update(state, {"validation_command_seen": bool(command_seen)})
        state["validation_seen"] = state["validation_command_seen"]
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


def telemetry_enabled() -> bool:
    """Telemetry defaults on; CHANGEFORGE_TELEMETRY=off (or 0/false/no) disables it."""
    value = os.environ.get("CHANGEFORGE_TELEMETRY", "").strip().casefold()
    return value not in TELEMETRY_DISABLED_VALUES


def telemetry_root(repo: Path) -> Path:
    """Per-repository telemetry directory under the user cache (path-free hash)."""
    return _cache_base() / "changeforge" / "telemetry" / _repo_hash(repo)


def session_id_from_event(event: dict) -> str:
    """Best-effort session/turn identifier from the hook event, never a prompt."""
    for key in (
        "session_id",
        "sessionId",
        "turn_id",
        "turnId",
        "conversation_id",
        "conversationId",
    ):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:120]
    return ""


def summarize_command_program(command: str) -> str:
    """Return only the program token of a command, skipping NAME=value prefixes.

    Full command arguments may contain secrets, so telemetry records only the
    leading executable name (for example ``kubectl`` or ``helm``), truncated.
    """
    for part in command.strip().split():
        if ENV_ASSIGNMENT_RE.match(part):
            continue
        return part[:MAX_COMMAND_PROGRAM_LEN]
    return ""


def write_telemetry_event(
    repo: Path,
    *,
    runtime: str,
    hook_name: str,
    event_name: str,
    mode: str,
    session_id: str = "",
    cwd: str | None = None,
    tool_name: str = "",
    changed_paths: Iterable[str] = (),
    added_paths: Iterable[str] = (),
    command_program: str = "",
    hook_findings: dict[str, Iterable[str]] | None = None,
    suggested_skills: Iterable[str] = (),
    suggested_capabilities: Iterable[str] = (),
    suggested_gates: Iterable[str] = (),
    suggested_domain_extensions: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
    route_manifest_detected: bool = False,
    required_references_detected: bool = False,
    validation_evidence_detected: bool = False,
    residual_risk_detected: bool = False,
    completion_language_detected: bool = False,
    stage_manifest_detected: bool = False,
    manifest_current_stage: str = "",
    manifest_selected_skills: Iterable[str] = (),
    manifest_selected_capabilities: Iterable[str] = (),
    manifest_selected_domain_extensions: Iterable[str] = (),
    manifest_required_references: Iterable[str] = (),
    manifest_required_quality_gates: Iterable[str] = (),
    manifest_skipped_quality_gates: Iterable[str] = (),
    turn_stage: str = "",
    owner_skill: str = "",
    reviewer_skill: str = "",
    read_evidence_seen: bool = False,
    review_evidence_seen: bool = False,
    repair_evidence_seen: bool = False,
    permission_gate_seen: bool = False,
    professional_contract_seen: bool = False,
    implementation_preflight_required: bool = False,
    implementation_preflight_seen: bool = False,
    implementation_preflight_blocked: bool = False,
    edit_without_preflight_seen: bool = False,
    post_edit_confirmed_preflight_gap: bool = False,
) -> None:
    """Append one telemetry record as JSONL. Fails open on any error.

    Telemetry is a runtime fact log for offline review. It records what a hook
    observed, not prompts, environment variables, secrets, or command output.
    """
    if not telemetry_enabled():
        return
    try:
        repo_hash = _repo_hash(repo)
        cwd_hash = _hash_text(cwd.strip()) if isinstance(cwd, str) and cwd.strip() else repo_hash
        root = telemetry_root(repo)
        for sub in TELEMETRY_SUBDIRS:
            (root / sub).mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": TELEMETRY_SCHEMA_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_hash": repo_hash,
            "cwd_hash": cwd_hash,
            "runtime": runtime,
            "hook_name": hook_name,
            "event_name": event_name,
            "session_id": _telemetry_session_id(repo, repo_hash, session_id),
            "mode": mode,
            "tool_name": tool_name,
            "changed_paths": _capped_items(changed_paths),
            "added_paths": _capped_items(added_paths),
            "command_program": command_program[:MAX_COMMAND_PROGRAM_LEN],
            "hook_findings": _clean_findings(hook_findings),
            "suggested_skills": _capped_items(suggested_skills),
            "suggested_capabilities": _capped_items(suggested_capabilities),
            "suggested_gates": _capped_items(suggested_gates),
            "suggested_domain_extensions": _capped_items(suggested_domain_extensions),
            "risk_surfaces": _capped_items(risk_surfaces),
            "route_manifest_detected": bool(route_manifest_detected),
            "required_references_detected": bool(required_references_detected),
            "validation_evidence_detected": bool(validation_evidence_detected),
            "residual_risk_detected": bool(residual_risk_detected),
            "completion_language_detected": bool(completion_language_detected),
            "stage_manifest_detected": bool(stage_manifest_detected),
            "manifest_current_stage": str(manifest_current_stage).strip()[:MAX_TELEMETRY_VALUE_LEN],
            "manifest_selected_skills": _capped_items(manifest_selected_skills),
            "manifest_selected_capabilities": _capped_items(manifest_selected_capabilities),
            "manifest_selected_domain_extensions": _capped_items(
                manifest_selected_domain_extensions
            ),
            "manifest_required_references": _capped_items(manifest_required_references),
            "manifest_required_quality_gates": _capped_items(manifest_required_quality_gates),
            "manifest_skipped_quality_gates": _capped_items(manifest_skipped_quality_gates),
            "turn_stage": str(turn_stage).strip()[:MAX_TELEMETRY_VALUE_LEN],
            "owner_skill": str(owner_skill).strip()[:MAX_TELEMETRY_VALUE_LEN],
            "reviewer_skill": str(reviewer_skill).strip()[:MAX_TELEMETRY_VALUE_LEN],
            "read_evidence_seen": bool(read_evidence_seen),
            "review_evidence_seen": bool(review_evidence_seen),
            "repair_evidence_seen": bool(repair_evidence_seen),
            "permission_gate_seen": bool(permission_gate_seen),
            "professional_contract_seen": bool(professional_contract_seen),
            "implementation_preflight_required": bool(implementation_preflight_required),
            "implementation_preflight_seen": bool(implementation_preflight_seen),
            "implementation_preflight_blocked": bool(implementation_preflight_blocked),
            "edit_without_preflight_seen": bool(edit_without_preflight_seen),
            "post_edit_confirmed_preflight_gap": bool(post_edit_confirmed_preflight_gap),
        }
        target = root / "sessions" / f"{_utc_date()}.jsonl"
        line = json.dumps(record, sort_keys=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception as exc:
        debug_log(repo, f"telemetry write failed open: {exc}")


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _new_turn_id() -> str:
    """Short random identifier for one agent turn (no prompt, no path)."""
    return uuid.uuid4().hex[:12]


def current_turn_id(repo: Path) -> str:
    """Return the persisted per-turn id, or empty string when none exists."""
    try:
        turn = load_state(repo).get("turn_id")
    except Exception:
        return ""
    return turn.strip() if isinstance(turn, str) else ""


def ensure_turn_id(repo: Path) -> str:
    """Return the per-turn id, creating and persisting one when absent.

    The id lives in the cache-side hook state for the life of a turn and is
    reset by clear_state at the Stop event, so telemetry records from one turn
    share a session id without merging unrelated turns into a single day.
    """
    turn = current_turn_id(repo)
    if turn:
        return turn
    turn = _new_turn_id()
    try:
        state = load_state(repo)
        state["turn_id"] = turn
        save_state(repo, state)
    except Exception:
        return turn
    return turn


def _fallback_session_id(repo: Path, repo_hash: str) -> str:
    """Per-turn fallback session id when the runtime supplies none.

    Coarse date-only fallback merged every turn of a repo in one day into one
    session, which corrupted closure review. A per-turn id keeps unrelated turns
    apart while still grouping every hook within one turn.
    """
    try:
        turn = ensure_turn_id(repo)
    except Exception:
        turn = _new_turn_id()
    return f"{repo_hash[:8]}-{_utc_date()}-{turn}"


def _telemetry_session_id(repo: Path, repo_hash: str, provided: str) -> str:
    """Per-turn telemetry session id, even when the runtime supplies one.

    A runtime-supplied session id (for example the Codex CLI session UUID) stays
    stable across an entire CLI run, so recording it verbatim merged every turn
    of that run into one telemetry session and corrupted per-turn closure review.
    Scope the recorded id by the per-turn turn_id so each turn is reviewed on its
    own while the runtime id is preserved as a traceable prefix.
    """
    runtime_id = provided.strip()
    if not runtime_id:
        return _fallback_session_id(repo, repo_hash)
    try:
        turn = ensure_turn_id(repo)
    except Exception:
        turn = _new_turn_id()
    return f"{runtime_id[:80]}:{turn}"


# --- Route / stage manifest parsing -------------------------------------------
# The Stop gate parses the agent's final handoff for the changeforge_route and
# changeforge_stage_route manifests so telemetry records what the route actually
# selected, not merely that a manifest token appeared. This is a minimal,
# dependency-free line parser (the hook runtime must not require PyYAML) and it
# always fails open: a malformed manifest yields empty fields, never an error.
ROUTE_MANIFEST_KEY = "changeforge_route"
STAGE_MANIFEST_KEY = "changeforge_stage_route"
IMPLEMENTATION_PREFLIGHT_KEY = "changeforge_implementation_preflight"
_MANIFEST_LIST_KEYS = (
    "selected_skills",
    "selected_capabilities",
    "selected_domain_extensions",
    "required_references",
    "required_quality_gates",
)
_REQUIRED_ROUTE_MANIFEST_FIELDS = (
    "selected_skills",
    "selected_capabilities",
    "required_references",
    "required_quality_gates",
)


def extract_manifest_fields(text: str) -> dict:
    """Extract route/stage manifest facts from agent final text. Fail open.

    ``changeforge_route`` is not a substring of ``changeforge_stage_route`` (the
    stage key carries ``stage_`` before ``route``), so plain presence checks do
    not cross-trigger between the two manifests.
    """
    result: dict[str, Any] = {
        "route_present": False,
        "stage_present": False,
        "current_stage": "",
        "selected_skills": [],
        "selected_capabilities": [],
        "selected_domain_extensions": [],
        "required_references": [],
        "required_quality_gates": [],
        "skipped_quality_gates": [],
    }
    if not isinstance(text, str) or not text:
        return result
    try:
        result["stage_present"] = STAGE_MANIFEST_KEY in text
        route_block = _manifest_block(text, ROUTE_MANIFEST_KEY)
        stage_at = route_block.find(f"{STAGE_MANIFEST_KEY}:")
        if stage_at != -1:
            # Keep the route segment from absorbing stage-manifest list values
            # when both manifests share a single fenced block.
            route_block = route_block[:stage_at]
        if route_block:
            for key in _MANIFEST_LIST_KEYS:
                result[key] = _manifest_list_field(route_block, key)
            result["skipped_quality_gates"] = _manifest_skipped_gates(route_block)
            result["route_present"] = all(
                result.get(key) for key in _REQUIRED_ROUTE_MANIFEST_FIELDS
            )
        stage_block = _manifest_block(text, STAGE_MANIFEST_KEY)
        if stage_block:
            result["current_stage"] = _manifest_scalar_field(stage_block, "current_stage")
    except Exception:
        return result
    return result


def extract_implementation_preflight_fields(text: str) -> dict:
    """Extract implementation preflight manifest facts from text. Fail open."""
    result: dict[str, Any] = {
        "present": False,
        "read_evidence": [],
        "placement_decision": False,
        "reuse_decision": False,
        "object_boundary": False,
        "test_plan": False,
        "risk": False,
    }
    if not isinstance(text, str) or not text:
        return result
    try:
        block = _manifest_block(text, IMPLEMENTATION_PREFLIGHT_KEY)
        if not block:
            return result
        result["present"] = f"{IMPLEMENTATION_PREFLIGHT_KEY}:" in block
        if not result["present"]:
            return result
        read_values: list[str] = []
        read_section = _manifest_section_block(block, "read_evidence")
        for key in (
            "target_files",
            "sibling_files",
            "caller_callee_paths",
            "nearby_tests",
            "configs_or_docs",
        ):
            read_values.extend(_manifest_list_field(read_section, key))
        result["read_evidence"] = _unique(read_values)
        result["placement_decision"] = _manifest_section_has_required_values(
            block, "placement_decision", ("target_file", "reason")
        )
        result["reuse_decision"] = _manifest_section_has_any_value(
            block,
            "reuse_decision",
            ("direct_reuse", "extension_reuse", "new_code_justification"),
        )
        result["object_boundary"] = _manifest_section_has_value(block, "object_boundary")
        result["test_plan"] = _manifest_section_has_any_value(
            block, "test_plan", ("validation_commands",)
        )
        result["risk"] = _manifest_section_has_any_value(
            block, "risk", ("rollback_or_revert_path", "compatibility_risk")
        )
    except Exception:
        return result
    return result


def _fenced_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    buffer: list[str] = []
    in_block = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if in_block:
                blocks.append("\n".join(buffer))
                buffer = []
                in_block = False
            else:
                in_block = True
            continue
        if in_block:
            buffer.append(line)
    if in_block and buffer:
        blocks.append("\n".join(buffer))
    return blocks


def _manifest_block(text: str, key: str) -> str:
    marker = f"{key}:"
    for block in _fenced_blocks(text):
        if marker in block:
            return block
    index = text.find(marker)
    return text[index:] if index != -1 else ""


def _manifest_unquote(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        value = value[1:-1]
    return value.strip()


def _manifest_list_field(segment: str, key: str) -> list[str]:
    key_re = re.compile(r"^(\s*)" + re.escape(key) + r":\s*(.*)$")
    item_re = re.compile(r"^(\s*)-\s+(.*)$")
    values: list[str] = []
    capturing = False
    key_indent = 0
    for line in segment.splitlines():
        if not capturing:
            match = key_re.match(line)
            if not match:
                continue
            inline = match.group(2).strip()
            if inline.startswith("[") and inline.endswith("]"):
                inner = inline[1:-1].strip()
                if inner:
                    values.extend(_manifest_unquote(part) for part in inner.split(","))
                return [v for v in values if v]
            if inline and inline not in ("|", ">", "|-", ">-"):
                return values  # scalar value, not a list
            key_indent = len(match.group(1))
            capturing = True
            continue
        item = item_re.match(line)
        if item and len(item.group(1)) > key_indent:
            values.append(_manifest_unquote(item.group(2)))
            continue
        if not line.strip():
            continue
        if len(line) - len(line.lstrip()) <= key_indent:
            break
    return [v for v in values if v]


def _manifest_scalar_field(segment: str, key: str) -> str:
    pattern = re.compile(r"^\s*" + re.escape(key) + r":\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(segment)
    return _manifest_unquote(match.group(1)) if match else ""


def _manifest_section_block(segment: str, key: str) -> str:
    key_re = re.compile(r"^(\s*)" + re.escape(key) + r":\s*(.*)$")
    lines = segment.splitlines()
    for index, line in enumerate(lines):
        match = key_re.match(line)
        if not match:
            continue
        key_indent = len(match.group(1))
        block_lines: list[str] = []
        for child in lines[index + 1 :]:
            if not child.strip():
                block_lines.append(child)
                continue
            indent = len(child) - len(child.lstrip())
            if indent <= key_indent:
                break
            block_lines.append(child)
        return "\n".join(block_lines)
    return ""


def _manifest_section_has_value(segment: str, key: str) -> bool:
    key_re = re.compile(r"^(\s*)" + re.escape(key) + r":\s*(.*)$")
    capturing = False
    key_indent = 0
    for line in segment.splitlines():
        if not capturing:
            match = key_re.match(line)
            if not match:
                continue
            inline = match.group(2).strip()
            if inline and inline not in ("{}", "[]", "|", ">", "|-", ">-"):
                return True
            key_indent = len(match.group(1))
            capturing = True
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= key_indent:
            return False
        text = line.strip()
        if text not in ("-", "[]", "{}"):
            return True
    return False


def _manifest_section_has_required_values(
    segment: str,
    section_key: str,
    child_keys: tuple[str, ...],
) -> bool:
    section = _manifest_section_block(segment, section_key)
    if not section:
        return False
    return all(_manifest_child_has_meaningful_value(section, key) for key in child_keys)


def _manifest_section_has_any_value(
    segment: str,
    section_key: str,
    child_keys: tuple[str, ...],
) -> bool:
    section = _manifest_section_block(segment, section_key)
    if not section:
        return False
    return any(_manifest_child_has_meaningful_value(section, key) for key in child_keys)


def _manifest_child_has_meaningful_value(segment: str, key: str) -> bool:
    scalar = _manifest_scalar_field(segment, key)
    if _manifest_meaningful_value(scalar):
        return True
    return any(_manifest_meaningful_value(value) for value in _manifest_list_field(segment, key))


def _manifest_meaningful_value(value: str) -> bool:
    text = _manifest_unquote(str(value or ""))
    if not text:
        return False
    return text.casefold() not in {"yes", "true", "ok", "n/a", "na", "none", "{}", "[]"}


def _manifest_skipped_gates(segment: str) -> list[str]:
    gates: list[str] = []
    for item in _manifest_list_field(segment, "skipped_quality_gates"):
        text = item.strip()
        if text.startswith("gate:"):
            gates.append(text[len("gate:"):].strip())
        elif "=>" in text:
            gates.append(text.split("=>", 1)[0].strip())
        else:
            gates.append(text)
    return [g for g in gates if g]


def _capped_items(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for raw in values:
        text = str(raw).strip()
        if not text:
            continue
        out.append(text[:MAX_TELEMETRY_VALUE_LEN])
        if len(out) >= MAX_TELEMETRY_ITEMS:
            break
    return _unique(out)


def _clean_findings(findings: dict[str, Iterable[str]] | None) -> dict[str, list[str]]:
    if not isinstance(findings, dict):
        return {}
    cleaned: dict[str, list[str]] = {}
    for key, values in findings.items():
        if isinstance(values, (list, tuple)):
            cleaned[str(key)] = _capped_items(values)
    return cleaned


def _state_path(repo: Path) -> Path:
    return _cache_base() / "changeforge" / "hooks" / _repo_hash(repo) / "current-turn.json"


def _cache_base() -> Path:
    """Resolve the ChangeForge cache root, honoring XDG_CACHE_HOME."""
    cache_root = os.environ.get("XDG_CACHE_HOME")
    return Path(cache_root).expanduser() if cache_root else Path.home() / ".cache"


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _repo_hash(repo: Path) -> str:
    """Stable, path-free identifier for a repository root."""
    try:
        repo_key = str(repo.expanduser().resolve())
    except OSError:
        repo_key = str(repo)
    return _hash_text(repo_key)


def _empty_state() -> dict:
    return {
        "runtime": "unknown",
        "changed_paths": [],
        "read_paths": [],
        "read_tools": [],
        "searched_patterns": [],
        "structure_findings": [],
        "file_naming_findings": [],
        "reuse_findings": [],
        "extension_reuse_findings": [],
        "advanced_refactor_findings": [],
        "comment_findings": [],
        "structure_quality_findings": [],
        "review_targets": [],
        "review_findings": [],
        "repair_findings": [],
        "risk_surfaces": [],
        "professional_injections": [],
        "permission_decisions": [],
        "reference_loads": [],
        "subagent_contracts": [],
        "compaction_snapshots": [],
        "prompt_signals": [],
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_domain_extensions": [],
        "suggested_gates": [],
        "implementation_preflights": [],
        "pre_edit_structure_findings": [],
        "active_skill_context": {},
        "turn_stage": "",
        "owner_skill": "",
        "reviewer_skill": "",
        "stage_route_present": False,
        "read_intent_seen": False,
        "read_evidence_seen": False,
        "reviewed_diff_evidence_seen": False,
        "review_intent_seen": False,
        "review_artifact_seen": False,
        "review_evidence_seen": False,
        "repair_evidence_seen": False,
        "permission_gate_seen": False,
        "professional_contract_seen": False,
        "implementation_preflight_seen": False,
        "implementation_preflight_required": False,
        "implementation_preflight_blocked": False,
        "pre_edit_missing_read_evidence": False,
        "pre_edit_missing_reuse_decision": False,
        "pre_edit_missing_placement_decision": False,
        "pre_edit_missing_test_plan": False,
        "edit_without_preflight_seen": False,
        "post_edit_confirmed_preflight_gap": False,
        "validation_command_seen": False,
        "validation_seen": False,
        "route_preflight_emitted": False,
        "turn_id": "",
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


def _capped_state_items(values: Iterable[str]) -> list[str]:
    """Sanitize state list entries so hook state cannot become a corpus."""
    out: list[str] = []
    for raw in values:
        text = str(raw).strip()
        if not text:
            continue
        out.append(text[:MAX_STATE_VALUE_LEN])
        if len(out) >= MAX_STATE_ITEMS:
            break
    return _unique(out)


def _clean_state_mapping(value: dict) -> dict:
    """Keep active context compact, scalar, and prompt-free."""
    cleaned: dict[str, Any] = {}
    for key, raw in value.items():
        name = str(key).strip()[:80]
        if not name:
            continue
        if isinstance(raw, (list, tuple)):
            cleaned[name] = _capped_state_items(str(item) for item in raw)
        elif isinstance(raw, dict):
            cleaned[name] = {
                str(child_key).strip()[:80]: str(child_value).strip()[:MAX_STATE_VALUE_LEN]
                for child_key, child_value in raw.items()
                if str(child_key).strip()
            }
        else:
            cleaned[name] = str(raw).strip()[:MAX_STATE_VALUE_LEN]
    return cleaned
