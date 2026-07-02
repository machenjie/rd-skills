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

try:
    from changeforge_compaction_contract import preserve_required_snapshots
except (ImportError, ModuleNotFoundError):  # pragma: no cover - importlib test loading fallback
    import importlib.util

    _contract_path = Path(__file__).with_name("changeforge_compaction_contract.py")
    _contract_spec = importlib.util.spec_from_file_location(
        "changeforge_compaction_contract", _contract_path
    )
    if _contract_spec is None or _contract_spec.loader is None:
        raise
    _contract_module = importlib.util.module_from_spec(_contract_spec)
    _contract_spec.loader.exec_module(_contract_module)
    preserve_required_snapshots = _contract_module.preserve_required_snapshots

_SRC_ROOT = Path(__file__).resolve().parents[2]
if (_SRC_ROOT / "project_memory").is_dir() and str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

try:
    from project_memory.hook_safe.adapter import (
        closure_advice as _hook_memory_closure_advice,
        pre_edit_advice as _hook_memory_pre_edit_advice,
        sanitize_event as _hook_memory_sanitize_event,
        write_event as _hook_memory_write_event,
    )
except Exception:  # pragma: no cover - hook runtime must fail open without support packages.
    _hook_memory_closure_advice = None
    _hook_memory_pre_edit_advice = None
    _hook_memory_sanitize_event = None
    _hook_memory_write_event = None


STATE_LIST_FIELDS = (
    "normalized_events",
    "changed_paths",
    "deleted_paths",
    "generated_paths",
    "read_paths",
    "read_tools",
    "searched_patterns",
    "external_file_changes",
    "config_changes",
    "structure_findings",
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
    "structure_quality_findings",
    "post_edit_structure_findings",
    "review_targets",
    "review_findings",
    "repair_findings",
    "repair_events",
    "rereview_events",
    "validation_results",
    "risk_surfaces",
    "changed_path_risk_surfaces",
    "command_risk_surfaces",
    "command_risks",
    "closure_risk_surfaces",
    "professional_injections",
    "professional_injection_digests",
    "permission_decisions",
    "rollback_points",
    "reference_loads",
    "subagent_contracts",
    "compaction_snapshots",
    "prompt_signals",
    "suggested_skills",
    "suggested_capabilities",
    "suggested_domain_extensions",
    "suggested_gates",
    "context_control_records",
    "tool_output_boundaries",
    "artifact_references",
    "branch_route_repair_summaries",
    "route_repair_forbidden_retries",
    "context_budget_findings",
    "skipped_references",
    "implementation_preflights",
    "senior_programming_judgments",
    "pre_edit_structure_findings",
    "choice_ids",
    "choice_triggers",
    "choice_status",
    "material_choice_surfaces",
    "blocked_tool_category",
    "bounded_paths",
)
STATE_SCALAR_STRING_FIELDS = (
    "turn_stage",
    "owner_skill",
    "reviewer_skill",
    "professional_injection_digest",
    "last_professional_injection_event",
)
STATE_SCALAR_INT_FIELDS = (
    "event_index",
    "last_material_edit_index",
    "last_validation_command_index",
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
    "repository_context_seen",
    "workflow_state_seen",
    "tool_permission_sandbox_seen",
    "skill_efficacy_benchmark_seen",
    "plan_execution_consistency_seen",
    "validation_freshness_seen",
    "implementation_preflight_seen",
    "implementation_preflight_complete",
    "implementation_preflight_required",
    "implementation_preflight_blocked",
    "senior_programming_judgment_seen",
    "senior_programming_judgment_complete",
    "senior_programming_judgment_required",
    "senior_programming_judgment_blocked",
    "choice_gate_seen",
    "choice_gate_blocked",
    "choice_resolution_evidence_seen",
    "pre_edit_missing_read_evidence",
    "pre_edit_missing_reuse_decision",
    "pre_edit_missing_placement_decision",
    "pre_edit_missing_test_plan",
    "pre_edit_missing_senior_programming_judgment",
    "edit_without_preflight_seen",
    "post_edit_confirmed_preflight_gap",
    "route_preflight_emitted",
)
KNOWN_RUNTIMES = {"codex", "claude", "copilot", "generic", "cline", "roo", "openhands"}
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
MEMORY_SCHEMA_VERSION = 1
MEMORY_SUBDIRS = ("events", "projections", "suggestions", "promoted")
MEMORY_TYPES = {
    "route_decision",
    "context_pack",
    "implementation_attempt",
    "validation_result",
    "review_finding",
    "repair_attempt",
    "accepted_decision",
    "rejected_decision",
    "fragile_file",
    "validated_command",
    "hook_false_positive",
    "hook_false_negative",
    "repeat_failure",
}
MEMORY_KINDS = {
    "fragile_file",
    "repeat_failure",
    "validation_pattern",
    "review_finding_pattern",
    "module_convention",
    "generated_source_mapping",
    "route_correction",
    "false_positive_hook",
    "false_negative_hook",
}
MEMORY_KIND_BY_TYPE = {
    "route_decision": "route_correction",
    "context_pack": "generated_source_mapping",
    "implementation_attempt": "module_convention",
    "validation_result": "validation_pattern",
    "validated_command": "validation_pattern",
    "review_finding": "review_finding_pattern",
    "repair_attempt": "review_finding_pattern",
    "accepted_decision": "module_convention",
    "rejected_decision": "module_convention",
    "fragile_file": "fragile_file",
    "hook_false_positive": "false_positive_hook",
    "hook_false_negative": "false_negative_hook",
    "repeat_failure": "repeat_failure",
}
MEMORY_TYPE_BY_KIND = {
    "fragile_file": "fragile_file",
    "repeat_failure": "repeat_failure",
    "validation_pattern": "validation_result",
    "review_finding_pattern": "review_finding",
    "module_convention": "implementation_attempt",
    "generated_source_mapping": "context_pack",
    "route_correction": "route_decision",
    "false_positive_hook": "hook_false_positive",
    "false_negative_hook": "hook_false_negative",
}
MEMORY_PRIVACY_CLASSES = {"safe_bounded", "redacted", "rejected_sensitive"}
MEMORY_SOURCES = {"telemetry", "trajectory", "human", "validator"}
MEMORY_FORBIDDEN_KEY_TOKENS = (
    "prompt",
    "raw_prompt",
    "stdout",
    "stderr",
    "environment",
    "env",
    "secret",
    "password",
    "api_key",
    "apikey",
    "token_value",
)
MEMORY_SECRET_VALUE_RE = re.compile(
    r"(secret|password|api[_-]?key|bearer\s+[a-z0-9._-]{12,}|token=)",
    re.IGNORECASE,
)
MEMORY_OUTCOMES = {"success", "failed", "partial", "blocked", "unknown"}
MAX_MEMORY_SUMMARY_LEN = 240
MAX_TELEMETRY_ITEMS = 50
MAX_TELEMETRY_VALUE_LEN = 300
MAX_STATE_ITEMS = 50
MAX_STATE_VALUE_LEN = 300
MAX_COMMAND_PROGRAM_LEN = 40
MAX_HOOK_OUTPUT_CHARS = 6000
HOOK_OUTPUT_TRUNCATION_NOTICE = "\n...[ChangeForge hook output truncated]"
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
FOLLOW_UP_PROMPT_RE = re.compile(
    r"\b(continue|follow up|re-review|latest fix|same pr|latest commit)\b"
    r"|继续|上面|上述|最新提交|修复已经提交|再审查",
    re.IGNORECASE,
)
STATE_LOCAL_PATH_RE = re.compile(
    r"(/Users/[^\s\"'<>]+|/home/[^\s\"'<>]+|/private/var/[^\s\"'<>]+|"
    r"/var/folders/[^\s\"'<>]+|/tmp/[^\s\"'<>]+|[A-Za-z]:\\Users\\[^\s\"'<>]+)"
)
STATE_SECRET_RE = re.compile(
    r"(sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+|"
    r"(?i:api[_-]?key|access[_-]?token|bearer[_-]?token|password|secret)"
    r"\s*[:=]\s*[A-Za-z0-9_./+=-]{8,})"
)


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
    """Return the detected executor runtime or unknown.

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
        if "openhands" in runtime or "open-hands" in runtime:
            return "openhands"
        if "cline" in runtime:
            return "cline"
        if "roo" in runtime:
            return "roo"
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
    for key in ("active_skill_context", "runtime_adapter"):
        if not isinstance(state.get(key), dict):
            state[key] = {}
    for key in STATE_SCALAR_STRING_FIELDS:
        if not isinstance(state.get(key), str):
            state[key] = ""
    for key in STATE_SCALAR_INT_FIELDS:
        try:
            state[key] = int(state.get(key) or 0)
        except (TypeError, ValueError):
            state[key] = 0
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
        if key == "compaction_snapshots":
            next_state[key] = _capped_compaction_snapshots(next_state.get(key, []))
        elif key == "context_control_records":
            next_state[key] = _capped_context_control_records(next_state.get(key, []))
        elif key == "tool_output_boundaries":
            next_state[key] = _capped_tool_output_boundaries(next_state.get(key, []))
        elif key == "artifact_references":
            next_state[key] = _capped_artifact_references(next_state.get(key, []))
        elif key == "branch_route_repair_summaries":
            next_state[key] = _capped_branch_route_repair_summaries(next_state.get(key, []))
        elif key == "route_repair_forbidden_retries":
            next_state[key] = _capped_state_items(next_state.get(key, []))[:10]
        else:
            next_state[key] = _capped_state_items(next_state.get(key, []))
    for key in ("active_skill_context", "runtime_adapter"):
        if not isinstance(next_state.get(key), dict):
            next_state[key] = {}
        else:
            next_state[key] = _clean_state_mapping(next_state[key])
    for key in STATE_SCALAR_STRING_FIELDS:
        next_state[key] = str(next_state.get(key, "")).strip()[:MAX_STATE_VALUE_LEN]
    for key in STATE_SCALAR_INT_FIELDS:
        try:
            next_state[key] = max(0, int(next_state.get(key) or 0))
        except (TypeError, ValueError):
            next_state[key] = 0
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


def bounded_hook_text(message: object, *, limit: int = MAX_HOOK_OUTPUT_CHARS) -> str:
    """Return bounded hook stdout text for runtime additionalContext payloads."""
    text = str(message or "").strip()
    if len(text) <= limit:
        return text
    if limit <= len(HOOK_OUTPUT_TRUNCATION_NOTICE):
        return text[:limit]
    return text[: limit - len(HOOK_OUTPUT_TRUNCATION_NOTICE)].rstrip() + HOOK_OUTPUT_TRUNCATION_NOTICE


def emit_warning(runtime: str, hook_event_name: str, message: str) -> None:
    """Emit runtime-compatible additional context for post-tool warnings."""
    if runtime not in KNOWN_RUNTIMES:
        return
    text = bounded_hook_text(message)
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
    text = bounded_hook_text(message)
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
    text = bounded_hook_text(message)
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
    text = bounded_hook_text(message)
    if not text:
        return
    if runtime == "copilot":
        return
    print(json.dumps({"systemMessage": text}, sort_keys=True))


def emit_block(runtime: str, hook_event_name: str, reason: str) -> None:
    """Only used when hook mode is block."""
    if runtime not in KNOWN_RUNTIMES:
        return
    print(json.dumps({"decision": "block", "reason": bounded_hook_text(reason)}, sort_keys=True))


def _emit_hook_specific_context(hook_event_name: str, text: str) -> None:
    bounded_text = bounded_hook_text(text)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": hook_event_name,
                    "additionalContext": bounded_text,
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
    if name in {"compact", "compaction", "contextcompact", "precompact", "postcompact", "beforecompact", "aftercompact"}:
        return True
    source = event.get("source") or event.get("reason") or event.get("matcher")
    return isinstance(source, str) and "compact" in source.casefold()


def merge_state(
    repo: Path,
    runtime: str,
    *,
    runtime_adapter: dict | None = None,
    normalized_events: Iterable[str] = (),
    changed_paths: Iterable[str] = (),
    deleted_paths: Iterable[str] = (),
    generated_paths: Iterable[str] = (),
    read_paths: Iterable[str] = (),
    read_tools: Iterable[str] = (),
    searched_patterns: Iterable[str] = (),
    external_file_changes: Iterable[str] = (),
    config_changes: Iterable[str] = (),
    structure_findings: Iterable[str] = (),
    file_naming_findings: Iterable[str] = (),
    reuse_findings: Iterable[str] = (),
    extension_reuse_findings: Iterable[str] = (),
    advanced_refactor_findings: Iterable[str] = (),
    comment_findings: Iterable[str] = (),
    structure_quality_findings: Iterable[str] = (),
    post_edit_structure_findings: Iterable[str] = (),
    review_targets: Iterable[str] = (),
    review_findings: Iterable[str] = (),
    repair_findings: Iterable[str] = (),
    repair_events: Iterable[str] = (),
    rereview_events: Iterable[str] = (),
    validation_results: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
    changed_path_risk_surfaces: Iterable[str] = (),
    command_risk_surfaces: Iterable[str] = (),
    command_risks: Iterable[str] = (),
    closure_risk_surfaces: Iterable[str] = (),
    professional_injections: Iterable[str] = (),
    professional_injection_digests: Iterable[str] = (),
    professional_injection_digest: str | None = None,
    last_professional_injection_event: str | None = None,
    permission_decisions: Iterable[str] = (),
    rollback_points: Iterable[str] = (),
    reference_loads: Iterable[str] = (),
    subagent_contracts: Iterable[str] = (),
    compaction_snapshots: Iterable[str] = (),
    prompt_signals: Iterable[str] = (),
    suggested_skills: Iterable[str] = (),
    suggested_capabilities: Iterable[str] = (),
    suggested_domain_extensions: Iterable[str] = (),
    suggested_gates: Iterable[str] = (),
    context_control_records: Iterable[object] = (),
    tool_output_boundaries: Iterable[object] = (),
    artifact_references: Iterable[str] = (),
    branch_route_repair_summaries: Iterable[object] = (),
    route_repair_forbidden_retries: Iterable[str] = (),
    context_budget_findings: Iterable[str] = (),
    skipped_references: Iterable[str] = (),
    implementation_preflights: Iterable[str] = (),
    senior_programming_judgments: Iterable[str] = (),
    pre_edit_structure_findings: Iterable[str] = (),
    choice_ids: Iterable[str] = (),
    choice_triggers: Iterable[str] = (),
    choice_status: Iterable[str] = (),
    material_choice_surfaces: Iterable[str] = (),
    blocked_tool_category: Iterable[str] = (),
    bounded_paths: Iterable[str] = (),
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
    repository_context_seen: bool | None = None,
    workflow_state_seen: bool | None = None,
    tool_permission_sandbox_seen: bool | None = None,
    skill_efficacy_benchmark_seen: bool | None = None,
    plan_execution_consistency_seen: bool | None = None,
    validation_freshness_seen: bool | None = None,
    implementation_preflight_seen: bool | None = None,
    implementation_preflight_complete: bool | None = None,
    implementation_preflight_required: bool | None = None,
    implementation_preflight_blocked: bool | None = None,
    senior_programming_judgment_seen: bool | None = None,
    senior_programming_judgment_complete: bool | None = None,
    senior_programming_judgment_required: bool | None = None,
    senior_programming_judgment_blocked: bool | None = None,
    choice_gate_seen: bool | None = None,
    choice_gate_blocked: bool | None = None,
    choice_resolution_evidence_seen: bool | None = None,
    pre_edit_missing_read_evidence: bool | None = None,
    pre_edit_missing_reuse_decision: bool | None = None,
    pre_edit_missing_placement_decision: bool | None = None,
    pre_edit_missing_test_plan: bool | None = None,
    pre_edit_missing_senior_programming_judgment: bool | None = None,
    edit_without_preflight_seen: bool | None = None,
    post_edit_confirmed_preflight_gap: bool | None = None,
) -> dict:
    state = load_state(repo)
    state["runtime"] = runtime
    if not state.get("turn_id"):
        state["turn_id"] = _new_turn_id()
    next_event_index = int(state.get("event_index") or 0) + 1
    state["event_index"] = next_event_index
    changed_path_values = list(changed_paths or ())
    deleted_path_values = list(deleted_paths or ())
    generated_path_values = list(generated_paths or ())
    external_change_values = list(external_file_changes or ())
    config_change_values = list(config_changes or ())
    validation_result_values = list(validation_results or ())
    update = {
        "runtime_adapter": runtime_adapter,
        "normalized_events": normalized_events,
        "changed_paths": changed_path_values,
        "deleted_paths": deleted_path_values,
        "generated_paths": generated_path_values,
        "read_paths": read_paths,
        "read_tools": read_tools,
        "searched_patterns": searched_patterns,
        "external_file_changes": external_change_values,
        "config_changes": config_change_values,
        "structure_findings": structure_findings,
        "file_naming_findings": file_naming_findings,
        "reuse_findings": reuse_findings,
        "extension_reuse_findings": extension_reuse_findings,
        "advanced_refactor_findings": advanced_refactor_findings,
        "comment_findings": comment_findings,
        "structure_quality_findings": structure_quality_findings,
        "post_edit_structure_findings": post_edit_structure_findings,
        "review_targets": review_targets,
        "review_findings": review_findings,
        "repair_findings": repair_findings,
        "repair_events": repair_events,
        "rereview_events": rereview_events,
        "validation_results": validation_result_values,
        "risk_surfaces": risk_surfaces,
        "changed_path_risk_surfaces": changed_path_risk_surfaces,
        "command_risk_surfaces": command_risk_surfaces,
        "command_risks": command_risks,
        "closure_risk_surfaces": closure_risk_surfaces,
        "professional_injections": professional_injections,
        "professional_injection_digests": professional_injection_digests,
        "professional_injection_digest": professional_injection_digest,
        "last_professional_injection_event": last_professional_injection_event,
        "permission_decisions": permission_decisions,
        "rollback_points": rollback_points,
        "reference_loads": reference_loads,
        "subagent_contracts": subagent_contracts,
        "compaction_snapshots": compaction_snapshots,
        "prompt_signals": prompt_signals,
        "suggested_skills": suggested_skills,
        "suggested_capabilities": suggested_capabilities,
        "suggested_domain_extensions": suggested_domain_extensions,
        "suggested_gates": suggested_gates,
        "context_control_records": context_control_records,
        "tool_output_boundaries": tool_output_boundaries,
        "artifact_references": artifact_references,
        "branch_route_repair_summaries": branch_route_repair_summaries,
        "route_repair_forbidden_retries": route_repair_forbidden_retries,
        "context_budget_findings": context_budget_findings,
        "skipped_references": skipped_references,
        "implementation_preflights": implementation_preflights,
        "senior_programming_judgments": senior_programming_judgments,
        "pre_edit_structure_findings": pre_edit_structure_findings,
        "choice_ids": choice_ids,
        "choice_triggers": choice_triggers,
        "choice_status": choice_status,
        "material_choice_surfaces": material_choice_surfaces,
        "blocked_tool_category": blocked_tool_category,
        "bounded_paths": bounded_paths,
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
        "repository_context_seen": repository_context_seen,
        "workflow_state_seen": workflow_state_seen,
        "tool_permission_sandbox_seen": tool_permission_sandbox_seen,
        "skill_efficacy_benchmark_seen": skill_efficacy_benchmark_seen,
        "plan_execution_consistency_seen": plan_execution_consistency_seen,
        "validation_freshness_seen": validation_freshness_seen,
        "implementation_preflight_seen": implementation_preflight_seen,
        "implementation_preflight_complete": implementation_preflight_complete,
        "implementation_preflight_required": implementation_preflight_required,
        "implementation_preflight_blocked": implementation_preflight_blocked,
        "senior_programming_judgment_seen": senior_programming_judgment_seen,
        "senior_programming_judgment_complete": senior_programming_judgment_complete,
        "senior_programming_judgment_required": senior_programming_judgment_required,
        "senior_programming_judgment_blocked": senior_programming_judgment_blocked,
        "choice_gate_seen": choice_gate_seen,
        "choice_gate_blocked": choice_gate_blocked,
        "choice_resolution_evidence_seen": choice_resolution_evidence_seen,
        "pre_edit_missing_read_evidence": pre_edit_missing_read_evidence,
        "pre_edit_missing_reuse_decision": pre_edit_missing_reuse_decision,
        "pre_edit_missing_placement_decision": pre_edit_missing_placement_decision,
        "pre_edit_missing_test_plan": pre_edit_missing_test_plan,
        "pre_edit_missing_senior_programming_judgment": pre_edit_missing_senior_programming_judgment,
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
        if command_seen:
            state["last_validation_command_index"] = next_event_index
    material_path_values = [
        *changed_path_values,
        *deleted_path_values,
        *generated_path_values,
        *external_change_values,
        *config_change_values,
    ]
    if material_path_values:
        prior_validation_index = int(state.get("last_validation_command_index") or 0)
        if prior_validation_index and prior_validation_index < next_event_index:
            state = reduce_state_update(
                state,
                {
                    "validation_results": [
                        "stale_after_material_change:validation_before_latest_edit"
                    ]
                },
            )
        state["last_material_edit_index"] = next_event_index
    save_state(repo, state)
    return state


def clear_state(repo: Path, runtime: str) -> None:
    state = _empty_state()
    state["runtime"] = runtime
    save_state(repo, state)


def reset_state_for_new_prompt(repo: Path, runtime: str, event: dict) -> bool:
    """Clear per-turn state for a new prompt unless it is an explicit follow-up.

    The raw prompt is inspected only in memory for continuation cues and is not
    written to state, telemetry, or debug logs.
    """
    if not is_user_prompt_submit(event):
        return False
    if _is_follow_up_prompt(event):
        return False
    clear_state(repo, runtime)
    return True


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


def memory_enabled() -> bool:
    """Project memory follows telemetry's opt-out and adds CHANGEFORGE_MEMORY=off."""
    value = os.environ.get("CHANGEFORGE_MEMORY", "").strip().casefold()
    return telemetry_enabled() and value not in TELEMETRY_DISABLED_VALUES


def memory_root(repo: Path) -> Path:
    """Per-repository memory directory under the user cache (path-free hash)."""
    return _cache_base() / "changeforge" / "memory" / _repo_hash(repo)


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
    normalized_events: Iterable[str] = (),
    changed_paths: Iterable[str] = (),
    deleted_paths: Iterable[str] = (),
    generated_paths: Iterable[str] = (),
    external_file_changes: Iterable[str] = (),
    config_changes: Iterable[str] = (),
    added_paths: Iterable[str] = (),
    command_program: str = "",
    command_risk: str = "",
    permission_decision: str = "",
    hook_findings: dict[str, Iterable[str]] | None = None,
    post_edit_structure_findings: Iterable[str] = (),
    context_control_records: Iterable[object] = (),
    tool_output_boundaries: Iterable[object] = (),
    artifact_references: Iterable[str] = (),
    branch_route_repair_summaries: Iterable[object] = (),
    route_repair_forbidden_retries: Iterable[str] = (),
    context_budget_findings: Iterable[str] = (),
    skipped_references: Iterable[str] = (),
    suggested_skills: Iterable[str] = (),
    suggested_capabilities: Iterable[str] = (),
    suggested_gates: Iterable[str] = (),
    suggested_domain_extensions: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
    changed_path_risk_surfaces: Iterable[str] = (),
    command_risk_surfaces: Iterable[str] = (),
    closure_risk_surfaces: Iterable[str] = (),
    route_manifest_detected: bool = False,
    required_references_detected: bool = False,
    validation_command_detected: bool = False,
    validation_results: Iterable[str] = (),
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
    repository_context_seen: bool = False,
    workflow_state_seen: bool = False,
    tool_permission_sandbox_seen: bool = False,
    skill_efficacy_benchmark_seen: bool = False,
    plan_execution_consistency_seen: bool = False,
    validation_freshness_seen: bool = False,
    validation_result_outcome: str = "",
    validation_result_evidence_strength: str = "",
    validation_result_negative_reason: str = "",
    validation_result_command_kind: str = "",
    validation_result_fresh_after_last_edit: str = "",
    validation_result_coverage_aligned: str = "",
    validation_result_covered_paths: Iterable[str] = (),
    validation_result_covered_risk_surfaces: Iterable[str] = (),
    validation_broker_closure_outcome: str = "",
    validation_broker_selected_scope: str = "",
    validation_broker_negative_evidence: Iterable[str] = (),
    validation_broker_residual_risk: Iterable[str] = (),
    validation_broker_command_ledger: Iterable[dict[str, Any]] = (),
    adapter_name: str = "",
    adapter_supported_checks: Iterable[str] = (),
    adapter_unsupported_checks: Iterable[str] = (),
    adapter_degraded_capabilities: Iterable[str] = (),
    closure_contract_verdict: str = "",
    closure_contract_residual_risk: Iterable[str] = (),
    changeforge_closure: dict[str, Any] | None = None,
    project_memory_available: bool = True,
    project_memory_projection_key: str = "",
    project_memory_included_events: Iterable[str] = (),
    project_memory_excluded_events: Iterable[str] = (),
    project_memory_stale_context_gate: str = "",
    project_memory_residual_risk: Iterable[str] = (),
    implementation_preflight_required: bool = False,
    implementation_preflight_seen: bool = False,
    implementation_preflight_complete: bool = False,
    implementation_preflight_blocked: bool = False,
    senior_programming_judgment_required: bool = False,
    senior_programming_judgment_seen: bool = False,
    senior_programming_judgment_complete: bool = False,
    senior_programming_judgment_blocked: bool = False,
    choice_gate_seen: bool = False,
    choice_gate_blocked: bool = False,
    choice_resolution_evidence_seen: bool = False,
    choice_ids: Iterable[str] = (),
    choice_triggers: Iterable[str] = (),
    choice_status: Iterable[str] = (),
    material_choice_surfaces: Iterable[str] = (),
    blocked_tool_category: Iterable[str] = (),
    bounded_paths: Iterable[str] = (),
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
            "normalized_events": _capped_items(normalized_events),
            "changed_paths": _capped_items(changed_paths),
            "deleted_paths": _capped_items(deleted_paths),
            "generated_paths": _capped_items(generated_paths),
            "external_file_changes": _capped_items(external_file_changes),
            "config_changes": _capped_items(config_changes),
            "added_paths": _capped_items(added_paths),
            "command_program": command_program[:MAX_COMMAND_PROGRAM_LEN],
            "command_risk": _telemetry_enum(
                command_risk,
                {"", "safe", "mutation", "destructive", "release", "migration", "dependency", "network", "unknown"},
            ),
            "permission_decision": _telemetry_enum(
                permission_decision,
                {"", "allow", "warn", "block", "deny", "unknown"},
            ),
            "hook_findings": _clean_findings(hook_findings),
            "post_edit_structure_findings": _capped_items(post_edit_structure_findings),
            "context_control_records": _capped_items(
                json.dumps(record, sort_keys=True)
                for record in _capped_context_control_records(context_control_records)
            ),
            "tool_output_boundaries": _capped_items(
                json.dumps(record, sort_keys=True)
                for record in _capped_tool_output_boundaries(tool_output_boundaries)
            ),
            "artifact_references": _capped_artifact_references(artifact_references),
            "branch_route_repair_summaries": _capped_items(
                json.dumps(record, sort_keys=True)
                for record in _capped_branch_route_repair_summaries(branch_route_repair_summaries)
            ),
            "route_repair_forbidden_retries": _capped_items(route_repair_forbidden_retries),
            "context_budget_findings": _capped_items(context_budget_findings),
            "skipped_references": _capped_items(skipped_references),
            "suggested_skills": _capped_items(suggested_skills),
            "suggested_capabilities": _capped_items(suggested_capabilities),
            "suggested_gates": _capped_items(suggested_gates),
            "suggested_domain_extensions": _capped_items(suggested_domain_extensions),
            "risk_surfaces": _capped_items(risk_surfaces),
            "changed_path_risk_surfaces": _capped_items(changed_path_risk_surfaces),
            "command_risk_surfaces": _capped_items(command_risk_surfaces),
            "closure_risk_surfaces": _capped_items(closure_risk_surfaces),
            "route_manifest_detected": bool(route_manifest_detected),
            "required_references_detected": bool(required_references_detected),
            "validation_command_detected": bool(validation_command_detected),
            "validation_results": _capped_items(validation_results),
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
            "repository_context_seen": bool(repository_context_seen),
            "workflow_state_seen": bool(workflow_state_seen),
            "tool_permission_sandbox_seen": bool(tool_permission_sandbox_seen),
            "skill_efficacy_benchmark_seen": bool(skill_efficacy_benchmark_seen),
            "plan_execution_consistency_seen": bool(plan_execution_consistency_seen),
            "validation_freshness_seen": bool(validation_freshness_seen),
            "validation_result_outcome": _telemetry_enum(
                validation_result_outcome,
                {"", "pass", "fail", "stale", "unknown", "not_run"},
            ),
            "validation_result_evidence_strength": _telemetry_enum(
                validation_result_evidence_strength,
                {"", "strong", "partial", "weak", "negative"},
            ),
            "validation_result_negative_reason": _telemetry_enum(
                validation_result_negative_reason,
                {"", "not_run", "unable_to_run", "stale", "failed", "no_outcome"},
            ),
            "validation_result_command_kind": _telemetry_enum(
                validation_result_command_kind,
                {"", "narrow", "module", "full", "unknown"},
            ),
            "validation_result_fresh_after_last_edit": _telemetry_enum(
                validation_result_fresh_after_last_edit,
                {"", "true", "false", "unknown"},
            ),
            "validation_result_coverage_aligned": _telemetry_enum(
                validation_result_coverage_aligned,
                {"", "true", "false", "unknown"},
            ),
            "validation_result_covered_paths": _capped_items(validation_result_covered_paths),
            "validation_result_covered_risk_surfaces": _capped_items(
                validation_result_covered_risk_surfaces
            ),
            "validation_broker_closure_outcome": _telemetry_enum(
                validation_broker_closure_outcome,
                {"", "ready", "needs_validation", "degraded_ready", "blocked"},
            ),
            "validation_broker_selected_scope": _telemetry_enum(
                validation_broker_selected_scope,
                {"", "narrow", "module", "full", "none"},
            ),
            "validation_broker_negative_evidence": _capped_items(
                validation_broker_negative_evidence
            ),
            "validation_broker_residual_risk": _capped_items(validation_broker_residual_risk),
            "validation_broker_command_ledger": _clean_validation_broker_command_ledger(
                validation_broker_command_ledger
            ),
            "adapter_name": _telemetry_runtime(adapter_name),
            "adapter_supported_checks": _capped_items(adapter_supported_checks),
            "adapter_unsupported_checks": _capped_items(adapter_unsupported_checks),
            "adapter_degraded_capabilities": _capped_items(adapter_degraded_capabilities),
            "closure_contract_verdict": _telemetry_enum(
                closure_contract_verdict,
                {
                    "",
                    "ready",
                    "needs_validation",
                    "needs_review",
                    "needs_repair",
                    "degraded_ready",
                    "blocked",
                },
            ),
            "closure_contract_residual_risk": _capped_items(closure_contract_residual_risk),
            "changeforge_closure": _clean_changeforge_closure(changeforge_closure),
            "project_memory_available": bool(project_memory_available),
            "project_memory_projection_key": _memory_clean_scalar(
                project_memory_projection_key
            ),
            "project_memory_included_events": _capped_items(project_memory_included_events),
            "project_memory_excluded_events": _capped_items(project_memory_excluded_events),
            "project_memory_stale_context_gate": _telemetry_enum(
                project_memory_stale_context_gate,
                {"", "pass", "warn", "block"},
            ),
            "project_memory_residual_risk": _capped_items(project_memory_residual_risk),
            "implementation_preflight_required": bool(implementation_preflight_required),
            "implementation_preflight_seen": bool(implementation_preflight_seen),
            "implementation_preflight_complete": bool(implementation_preflight_complete),
            "implementation_preflight_blocked": bool(implementation_preflight_blocked),
            "senior_programming_judgment_required": bool(senior_programming_judgment_required),
            "senior_programming_judgment_seen": bool(senior_programming_judgment_seen),
            "senior_programming_judgment_complete": bool(senior_programming_judgment_complete),
            "senior_programming_judgment_blocked": bool(senior_programming_judgment_blocked),
            "choice_gate_seen": bool(choice_gate_seen),
            "choice_gate_blocked": bool(choice_gate_blocked),
            "choice_resolution_evidence_seen": bool(choice_resolution_evidence_seen),
            "choice_ids": _capped_items(choice_ids),
            "choice_triggers": _capped_items(choice_triggers),
            "choice_status": _capped_items(choice_status),
            "material_choice_surfaces": _capped_items(material_choice_surfaces),
            "blocked_tool_category": _capped_items(blocked_tool_category),
            "bounded_paths": _capped_items(bounded_paths),
            "edit_without_preflight_seen": bool(edit_without_preflight_seen),
            "post_edit_confirmed_preflight_gap": bool(post_edit_confirmed_preflight_gap),
        }
        target = root / "sessions" / f"{_utc_date()}.jsonl"
        line = json.dumps(record, sort_keys=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        _write_memory_event_from_telemetry_record(repo, record)
    except Exception as exc:
        debug_log(repo, f"telemetry write failed open: {exc}")


def write_memory_event(repo: Path, event: dict[str, Any]) -> None:
    """Append one bounded project memory event. Fails open on any error."""
    if not memory_enabled():
        return
    try:
        if _hook_memory_write_event is not None:
            _hook_memory_write_event(repo, event)
            return
        root = memory_root(repo)
        for sub in MEMORY_SUBDIRS:
            (root / sub).mkdir(parents=True, exist_ok=True)
        record = _sanitize_memory_event(repo, event)
        target = root / "events" / f"{_utc_date()}.jsonl"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception as exc:
        debug_log(repo, f"memory write failed open: {exc}")


def memory_pre_edit_advice(
    repo: Path,
    changed_paths: Iterable[str],
    state: dict | None = None,
    assistant_text: str = "",
) -> dict[str, Any]:
    """Return warning-only memory advice for pre-edit gates."""
    try:
        if _hook_memory_pre_edit_advice is not None:
            return _hook_memory_pre_edit_advice(repo, changed_paths, state, assistant_text)
        events = _read_memory_events(repo)
        paths = _capped_items(changed_paths)
        fragile_paths = _memory_fragile_paths(events, paths)
        owner = str((state or {}).get("owner_skill", "")).strip()
        task = _memory_task_fingerprint(paths, owner, "")
        repeat = _memory_repeat_failure(events, repo_hash=_repo_hash(repo), task=task, paths=paths, owner=owner)
        evidence = _memory_pre_edit_evidence(state or {}, assistant_text)
        if repeat.get("repeated") and evidence["failure_diagnosis_route"]:
            repeat = {**repeat, "allowed_to_continue": True}
        missing: list[str] = []
        if fragile_paths:
            if not evidence["read_file_evidence"]:
                missing.append("read_file_evidence")
            if not evidence["owner_source_of_truth_check"]:
                missing.append("owner_source_of_truth_check")
            if not evidence["same_pattern_scan"]:
                missing.append("same_pattern_scan")
            if not evidence["validator_mapping"]:
                missing.append("validator_mapping")
            if not evidence["nearby_test_evidence"]:
                missing.append("nearby_test_evidence")
            if not evidence["memory_summary_evidence"]:
                missing.append("memory_summary_evidence")
            if not evidence["implementation_preflight"]:
                missing.append("implementation_preflight")
        return {
            "fragile_paths": fragile_paths,
            "repeat_failure": repeat,
            "missing": missing,
        }
    except Exception as exc:
        debug_log(repo, f"memory pre-edit advice failed open: {exc}")
        return {"fragile_paths": [], "repeat_failure": {}, "missing": []}


def memory_closure_advice(repo: Path, state: dict | None = None) -> dict[str, Any]:
    """Return fail-open project-memory closure facts for Stop telemetry."""
    changed_paths = _capped_items((state or {}).get("changed_paths", []))
    if _hook_memory_closure_advice is not None:
        return _hook_memory_closure_advice(repo, state)
    if not memory_enabled():
        return {
            "available": False,
            "status": "disabled_by_policy",
            "projection_key": "",
            "included_events": [],
            "excluded_events": [],
            "stale_context_gate": "not_applicable",
            "residual_risk": [],
        }
    try:
        events = _read_memory_events(repo)
        included: list[dict[str, Any]] = []
        excluded: list[str] = []
        residual: list[str] = []
        for event in events:
            event_id = _memory_event_id(event)
            if event.get("privacy_class") == "rejected_sensitive":
                excluded.append(f"{event_id}:rejected_sensitive")
                residual.append("sensitive_memory_event_excluded")
                continue
            event_paths = _memory_event_paths(event)
            if changed_paths and not _memory_paths_overlap(set(changed_paths), set(event_paths)):
                excluded.append(f"{event_id}:not_relevant_to_changed_paths")
                continue
            included.append(event)
            kind = _memory_event_kind(event)
            if kind == "fragile_file":
                residual.append("project_memory_fragile_file")
            if kind == "repeat_failure":
                residual.append("project_memory_repeat_failure")
            if len(included) >= MAX_TELEMETRY_ITEMS:
                residual.append("project_memory_projection_truncated")
                break
        stale_context_gate = "warn" if residual else "pass"
        return {
            "available": True,
            "status": "available",
            "projection_key": _memory_projection_key(changed_paths, included, excluded),
            "included_events": [_memory_event_id(event) for event in included[:MAX_TELEMETRY_ITEMS]],
            "excluded_events": excluded[:MAX_TELEMETRY_ITEMS],
            "stale_context_gate": stale_context_gate,
            "residual_risk": _unique(residual)[:MAX_TELEMETRY_ITEMS],
        }
    except Exception as exc:
        debug_log(repo, f"memory closure advice failed open: {exc}")
        return {
            "available": False,
            "status": "unavailable_due_error",
            "projection_key": "",
            "included_events": [],
            "excluded_events": [],
            "stale_context_gate": "warn" if changed_paths else "pass",
            "residual_risk": ["project_memory_unavailable"] if changed_paths else [],
        }


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
SENIOR_PROGRAMMING_JUDGMENT_KEY = "senior_programming_judgment"
REPOSITORY_CONTEXT_KEY = "repository_context"
SENIOR_PROGRAMMING_JUDGMENT_REQUIRED_SECTIONS = (
    "purpose",
    "facts",
    "objects",
    "states",
    "behaviors",
    "rules",
    "invariants",
    "boundaries",
    "failure_contract",
    "side_effects",
    "reuse_and_placement",
    "minimality_decision",
    "validation_map",
    "observability_map",
    "residual_risk",
)
SENIOR_PROGRAMMING_JUDGMENT_ALLOWED_SKIP_REASONS = (
    "trivial-local-edit",
    "no-semantic-impact",
    "no-engineering-action",
    "formatting-only",
    "documentation-only-no-behavior-change",
)
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
        result["object_boundary"] = _manifest_object_boundary_complete(block)
        result["test_plan"] = _manifest_section_has_any_value(
            block, "test_plan", ("validation_commands",)
        )
        result["risk"] = _manifest_section_has_any_value(
            block, "risk", ("rollback_or_revert_path", "compatibility_risk")
        )
    except Exception:
        return result
    return result


def extract_senior_programming_judgment_fields(
    text: str,
    required_sections: Iterable[str] | None = None,
) -> dict:
    """Extract senior programming judgment manifest facts from text. Fail open."""
    result: dict[str, Any] = {
        "present": False,
        "required": False,
        "allowed_skip": False,
        "complete": False,
        "sections": [],
        "missing": [],
        "required_sections": [],
        "quality_missing": [],
    }
    if not isinstance(text, str) or not text:
        return result
    try:
        required = tuple(
            section
            for section in _unique(required_sections or SENIOR_PROGRAMMING_JUDGMENT_REQUIRED_SECTIONS)
            if section in SENIOR_PROGRAMMING_JUDGMENT_REQUIRED_SECTIONS
        )
        result["required_sections"] = list(required)
        block = _manifest_block(text, SENIOR_PROGRAMMING_JUDGMENT_KEY)
        if not block:
            return result
        result["present"] = f"{SENIOR_PROGRAMMING_JUDGMENT_KEY}:" in block
        if not result["present"]:
            return result
        required_scalar = _manifest_scalar_field(block, "required").casefold()
        result["required"] = required_scalar not in {"false", "no", "0", "not_required"}
        skip_values = _manifest_field_values(block, "skip_reason", allow_none=True)
        skip_values.extend(_manifest_field_values(block, "skip_reasons", allow_none=True))
        result["allowed_skip"] = _senior_judgment_allowed_skip(skip_values)
        sections = [
            section
            for section in required
            if _senior_judgment_section_complete(block, section)
        ]
        missing = [
            section
            for section in required
            if section not in sections
        ]
        quality_missing = _senior_judgment_quality_missing(block, required)
        missing = _unique([*missing, *quality_missing])
        result["sections"] = sections
        result["quality_missing"] = [] if result["allowed_skip"] else quality_missing
        result["missing"] = [] if result["allowed_skip"] else missing
        result["complete"] = bool(result["allowed_skip"] or not result["missing"])
    except Exception:
        return result
    return result


def _senior_judgment_allowed_skip(skip_values: Iterable[str]) -> bool:
    allowed = set(SENIOR_PROGRAMMING_JUDGMENT_ALLOWED_SKIP_REASONS)
    return any(
        _manifest_unquote(str(value)).strip().casefold() in allowed
        for value in skip_values
    )


def _senior_judgment_section_complete(segment: str, key: str) -> bool:
    if not _manifest_section_has_value(segment, key):
        return False
    section = _manifest_section_block(segment, key)
    if key == "purpose":
        return all(
            _manifest_child_has_meaningful_value(section, child)
            for child in (
                "why_exists",
                "current_behavior",
                "desired_behavior",
                "success_signal",
                "failure_signal",
            )
        )
    if key == "facts":
        return _manifest_section_has_value(section, "source_backed") and _manifest_child_key_seen(
            section,
            "source",
        )
    if key == "objects":
        return _manifest_child_key_seen(section, "owner")
    if key == "reuse_and_placement":
        return _manifest_child_has_meaningful_value(
            section,
            "selected_location",
        ) and (
            _manifest_section_has_value(section, "existing_candidates")
            or _manifest_section_has_value(section, "rejected_locations")
            or _manifest_child_has_meaningful_value(section, "new_code_justification")
            or _manifest_explicit_boolean(section, "no_reuse_candidate_found")
        )
    if key == "minimality_decision":
        return _manifest_child_has_meaningful_value(section, "simplest_correct_path")
    if key == "failure_contract":
        return _manifest_section_has_value(section, "expected_failures") or any(
            _manifest_child_has_meaningful_value(section, child)
            for child in ("rollback_or_compensation", "fallback", "degradation_behavior")
        )
    if key == "side_effects":
        return any(
            _manifest_section_has_value(section, child)
            or _manifest_child_has_meaningful_value(section, child)
            for child in (
                "mutation",
                "persistence",
                "cache",
                "event",
                "external_io",
                "telemetry",
                "generated_output",
                "no_side_effects",
            )
        )
    if key == "validation_map":
        has_mapping = any(
            _manifest_section_has_value(section, child)
            for child in ("acceptance_to_test", "invariant_to_test", "failure_path_to_test")
        )
        return has_mapping and all(
            _manifest_child_has_meaningful_value(section, child)
            for child in (
                "command_or_not_verified",
                "what_evidence_proves",
                "what_evidence_does_not_prove",
            )
        )
    if key == "observability_map":
        return any(
            _manifest_child_has_meaningful_value(section, child)
            or _manifest_section_has_value(section, child)
            for child in (
                "logs",
                "metrics",
                "traces",
                "telemetry",
                "hook_state",
                "report",
                "no_log_rationale",
            )
        )
    if key == "residual_risk":
        return all(
            _manifest_child_key_seen(section, child)
            for child in ("risk", "owner", "next_gate")
        )
    return True


def _senior_judgment_quality_missing(segment: str, required: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for section in required:
        if not _senior_judgment_section_complete(segment, section):
            missing.append(section)
    return _unique(missing)


def extract_repository_context_fields(text: str) -> dict:
    """Extract structured repository_context closure facts from text. Fail open."""
    result: dict[str, Any] = {
        "present": False,
        "context_pack": [],
        "source_of_truth": [],
        "reuse_candidates": [],
        "no_reuse_candidate_found": False,
        "test_candidates": [],
        "validation_candidates": [],
        "rejected_locations": [],
        "graph_freshness": "",
        "residual_risk": [],
        "complete": False,
    }
    if not isinstance(text, str) or not text:
        return result
    try:
        block = _manifest_block(text, REPOSITORY_CONTEXT_KEY)
        if not block:
            return result
        result["present"] = f"{REPOSITORY_CONTEXT_KEY}:" in block
        if not result["present"]:
            return result
        result["context_pack"] = _manifest_field_values(block, "context_pack")
        result["source_of_truth"] = _manifest_field_values(block, "source_of_truth")
        result["reuse_candidates"] = _manifest_field_values(block, "reuse_candidates")
        result["no_reuse_candidate_found"] = _manifest_explicit_boolean(
            block,
            "no_reuse_candidate_found",
        )
        result["test_candidates"] = _manifest_field_values(block, "test_candidates")
        result["validation_candidates"] = _manifest_field_values(block, "validation_candidates")
        result["rejected_locations"] = _manifest_field_values(block, "rejected_locations")
        graph_values = _manifest_field_values(block, "graph_freshness")
        result["graph_freshness"] = graph_values[0] if graph_values else ""
        result["residual_risk"] = _manifest_field_values(
            block,
            "residual_risk",
            allow_none=True,
        )
        result["complete"] = bool(
            (result["context_pack"] or result["source_of_truth"])
            and (result["reuse_candidates"] or result["no_reuse_candidate_found"])
            and (result["test_candidates"] or result["validation_candidates"])
            and result["graph_freshness"]
            and result["residual_risk"]
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


def _manifest_field_values(segment: str, key: str, *, allow_none: bool = False) -> list[str]:
    values = [
        value
        for value in _manifest_list_field(segment, key)
        if _manifest_explicit_value(value, allow_none=allow_none)
    ]
    if values:
        return values
    scalar = _manifest_scalar_field(segment, key)
    if _manifest_explicit_value(scalar, allow_none=allow_none):
        return [scalar]
    if _manifest_section_has_value(segment, key):
        return [key]
    return []


def _manifest_explicit_boolean(segment: str, key: str) -> bool:
    scalar = _manifest_scalar_field(segment, key).casefold()
    if scalar in {"true", "yes", "1", "no_reuse_candidate_found"}:
        return True
    if scalar in {"false", "no", "0", "", "none", "n/a", "na"}:
        return False
    return _manifest_explicit_value(scalar, allow_none=False)


def _manifest_explicit_value(value: str, *, allow_none: bool = False) -> bool:
    text = _manifest_unquote(str(value or ""))
    if not text:
        return False
    if allow_none and text.casefold() in {"none", "n/a", "na", "not_applicable"}:
        return True
    return _manifest_meaningful_value(text)


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
            if inline not in ("", "|", ">", "|-", ">-") and _manifest_meaningful_value(inline):
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
        value = text[1:].strip() if text.startswith("-") else text
        if text not in ("-", "[]", "{}") and _manifest_meaningful_value(value):
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


def _manifest_object_boundary_complete(segment: str) -> bool:
    if not _manifest_section_has_required_values(
        segment,
        "object_boundary",
        ("artifact_type", "owner"),
    ):
        return False
    return _manifest_section_has_any_value(
        segment,
        "object_boundary",
        ("state_or_invariant", "compatibility_notes"),
    )


def _manifest_child_has_meaningful_value(segment: str, key: str) -> bool:
    scalar = _manifest_scalar_field(segment, key)
    if _manifest_meaningful_value(scalar):
        return True
    return any(_manifest_meaningful_value(value) for value in _manifest_list_field(segment, key))


def _manifest_child_key_seen(segment: str, key: str) -> bool:
    pattern = re.compile(r"^\s*(?:-\s*)?" + re.escape(key) + r":\s*(.*)$", re.MULTILINE)
    match = pattern.search(segment)
    if not match:
        return False
    value = match.group(1).strip()
    return _manifest_meaningful_value(value)


def _manifest_meaningful_value(value: str) -> bool:
    text = _manifest_unquote(str(value or ""))
    if not text:
        return False
    folded = text.casefold()
    return folded not in {
        "yes",
        "true",
        "ok",
        "okay",
        "good",
        "done",
        "n/a",
        "na",
        "none",
        "not applicable",
        "not_applicable",
        "unknown",
        "todo",
        "tbd",
        "placeholder",
        "fill me",
        "straightforward",
        "looks straightforward",
        "{}",
        "[]",
    }


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


def _clean_validation_broker_command_ledger(values: Iterable[dict[str, Any]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if isinstance(values, (str, bytes)):
        return out
    for raw in values or ():
        if not isinstance(raw, dict):
            continue
        out.append(
            {
                "command_kind": _telemetry_enum(
                    raw.get("command_kind"),
                    {"", "narrow", "module", "full", "unknown"},
                ),
                "command_display_safe": str(raw.get("command_display_safe") or "").strip()[
                    :MAX_TELEMETRY_VALUE_LEN
                ],
                "scope": _telemetry_enum(
                    raw.get("scope"),
                    {"", "narrow", "module", "full", "none", "unknown"},
                ),
                "outcome": _telemetry_enum(
                    raw.get("outcome"),
                    {
                        "",
                        "passed",
                        "failed",
                        "not_run",
                        "not_verified",
                        "stale",
                        "partial",
                        "unknown",
                    },
                ),
                "finished_at_or_order": str(raw.get("finished_at_or_order") or "").strip()[
                    :MAX_TELEMETRY_VALUE_LEN
                ],
                "covered_paths": _capped_items(raw.get("covered_paths", []) or []),
                "covered_risk_surfaces": _capped_items(
                    raw.get("covered_risk_surfaces", []) or []
                ),
                "evidence_strength": _telemetry_enum(
                    raw.get("evidence_strength"),
                    {"", "none", "weak", "partial", "strong", "negative"},
                ),
            }
        )
        if len(out) >= 10:
            break
    return out


def _clean_changeforge_closure(value: dict[str, Any] | None) -> dict[str, object]:
    source = value if isinstance(value, dict) else {}
    validation = source.get("validation")
    validation_source = validation if isinstance(validation, dict) else {}
    review = source.get("review")
    review_source = review if isinstance(review, dict) else {}
    changed_files = source.get("changed_files")
    changed_source = changed_files if isinstance(changed_files, dict) else {}
    return {
        "adapter": _telemetry_runtime(source.get("adapter")),
        "verdict": _telemetry_enum(
            source.get("verdict"),
            {
                "",
                "ready",
                "needs_validation",
                "needs_review",
                "needs_repair",
                "degraded_ready",
                "blocked",
            },
        ),
        "supported_checks": _capped_items(source.get("supported_checks", []) or []),
        "unsupported_checks": _capped_items(source.get("unsupported_checks", []) or []),
        "degraded_capabilities": _capped_items(source.get("degraded_capabilities", []) or []),
        "present_evidence": _capped_items(source.get("present_evidence", []) or []),
        "missing_evidence": _capped_items(source.get("missing_evidence", []) or []),
        "negative_evidence": _capped_items(source.get("negative_evidence", []) or []),
        "validation": {
            "outcome": _telemetry_enum(
                validation_source.get("outcome"),
                {"", "pass", "fail", "failed", "stale", "not_run", "not_verified", "no_outcome", "unknown"},
            ),
            "freshness": _telemetry_enum(
                validation_source.get("freshness"),
                {"", "current", "stale", "unknown", "not_applicable"},
            ),
            "scope": _telemetry_enum(
                validation_source.get("scope"),
                {"", "narrow", "module", "full", "none", "unknown"},
            ),
            "command_kind": _telemetry_enum(
                validation_source.get("command_kind"),
                {"", "narrow", "module", "full", "unknown"},
            ),
        },
        "review": {
            "review_outcome": str(review_source.get("review_outcome") or "").strip()[
                :MAX_TELEMETRY_VALUE_LEN
            ],
            "repair_present": bool(review_source.get("repair_present")),
            "rereview_present": bool(review_source.get("rereview_present")),
        },
        "changed_files": {
            "changed": _capped_items(changed_source.get("changed", []) or []),
            "deleted": _capped_items(changed_source.get("deleted", []) or []),
            "generated": _capped_items(changed_source.get("generated", []) or []),
        },
        "residual_risk": _capped_items(source.get("residual_risk", []) or []),
        "next_owner": str(source.get("next_owner") or "").strip()[:MAX_TELEMETRY_VALUE_LEN],
    }


def _memory_capped_items(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for raw in values:
        text = _memory_clean_scalar(raw)
        if not text:
            continue
        out.append(text)
        if len(out) >= MAX_TELEMETRY_ITEMS:
            break
    return _unique(out)


def _memory_clean_scalar(value: object) -> str:
    text = str(value or "").replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    if not text or MEMORY_SECRET_VALUE_RE.search(text):
        return ""
    return text[:MAX_TELEMETRY_VALUE_LEN]


def _memory_clean_summary(value: object, *, default: str = "") -> str:
    text = _memory_clean_scalar(value) or default
    return text[:MAX_MEMORY_SUMMARY_LEN]


def _memory_enum(value: object, allowed: set[str], default: str) -> str:
    text = _memory_clean_scalar(value)
    return text if text in allowed else default


def _telemetry_enum(value: object, allowed: set[str]) -> str:
    text = str(value or "").strip()
    return text if text in allowed else ""


def _telemetry_runtime(value: object) -> str:
    text = str(value or "").strip().casefold().replace("_", "-")
    allowed = {
        "",
        "codex",
        "claude",
        "copilot",
        "generic",
        "unknown",
        "cline",
        "roo",
        "openhands",
        "gemini-cli",
        "goose",
    }
    return text if text in allowed else "unknown"


def _sanitize_memory_event(repo: Path, event: dict[str, Any]) -> dict[str, Any]:
    if _hook_memory_sanitize_event is not None:
        return _hook_memory_sanitize_event(repo, event)
    source = event if isinstance(event, dict) else {}
    raw_kind = _memory_enum(source.get("kind"), MEMORY_KINDS, "")
    event_type = _memory_enum(
        source.get("type"),
        MEMORY_TYPES,
        MEMORY_TYPE_BY_KIND.get(raw_kind, "implementation_attempt"),
    )
    kind = raw_kind or MEMORY_KIND_BY_TYPE.get(event_type, "module_convention")
    paths = _memory_clean_paths(repo, source.get("bounded_paths") or source.get("paths", []))
    owner = _memory_clean_scalar(source.get("owner_skill", ""))
    outcome = _memory_enum(source.get("outcome"), MEMORY_OUTCOMES, "unknown")
    timestamp = _memory_clean_scalar(
        source.get("timestamp") or source.get("created_at")
    ) or datetime.now(timezone.utc).isoformat()
    repo_hash = _memory_clean_scalar(source.get("repo_hash") or _repo_hash(repo))
    summary = _memory_clean_summary(
        source.get("summary"),
        default=_memory_summary_from_event(kind, paths, outcome),
    )
    sensitive_input = _memory_contains_forbidden_key(source) or _memory_contains_sensitive_value(source)
    privacy_default = "redacted" if sensitive_input else "safe_bounded"
    event_id = _memory_clean_scalar(source.get("event_id"))
    if not event_id:
        event_id = _memory_deterministic_event_id(repo_hash, timestamp, kind, paths, summary, source)
    elif not event_id.startswith("mem_"):
        event_id = "mem_" + _hash_text(event_id)
    task_fingerprint = _memory_clean_scalar(source.get("task_fingerprint"))
    if not task_fingerprint:
        task_fingerprint = _memory_task_fingerprint(paths, owner, source.get("kind") or source.get("type"))
    return {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "event_id": event_id,
        "repo_hash": repo_hash,
        "commit_sha": _memory_clean_scalar(source.get("commit_sha")),
        "timestamp": timestamp[:80],
        "kind": kind,
        "bounded_paths": paths,
        "summary": summary,
        "privacy_class": _memory_enum(
            source.get("privacy_class"),
            MEMORY_PRIVACY_CLASSES,
            privacy_default,
        ),
        "retention_policy": _memory_clean_scalar(
            source.get("retention_policy")
        ) or _memory_default_retention_policy(kind),
        "source": _memory_enum(source.get("source"), MEMORY_SOURCES, "telemetry"),
        "task_fingerprint": task_fingerprint[:MAX_TELEMETRY_VALUE_LEN],
        "type": event_type,
        "paths": paths,
        "symbols": _memory_capped_items(source.get("symbols", [])),
        "owner_skill": owner,
        "reviewer_skill": _memory_clean_scalar(source.get("reviewer_skill", "")),
        "route_manifest_hash": _memory_clean_scalar(source.get("route_manifest_hash", "")),
        "outcome": outcome,
        "evidence_refs": _memory_capped_items(source.get("evidence_refs", [])),
        "confidence": _memory_confidence(source.get("confidence")),
        "promotion_status": _memory_promotion_status(source.get("promotion_status")),
        "created_at": timestamp[:80],
    }


def _write_memory_event_from_telemetry_record(repo: Path, record: dict[str, Any]) -> None:
    event = _memory_event_from_telemetry_record(repo, record)
    if event:
        write_memory_event(repo, event)


def _memory_event_from_telemetry_record(repo: Path, record: dict[str, Any]) -> dict[str, Any] | None:
    paths = _unique(
        _capped_items(record.get("changed_paths", []))
        + _capped_items(record.get("added_paths", []))
    )
    if not paths and not record.get("validation_command_detected") and not record.get("hook_findings"):
        return None
    owner = str(record.get("owner_skill") or "").strip()
    event_type = _memory_type_from_telemetry(record)
    kind = _memory_kind_from_telemetry(record, event_type)
    outcome = _memory_outcome_from_telemetry(record)
    evidence_refs = [
        f"hook:{record.get('hook_name', '')}",
        f"event:{record.get('event_name', '')}",
    ]
    if record.get("route_manifest_detected"):
        evidence_refs.append("route_manifest_detected")
    if record.get("validation_evidence_detected"):
        evidence_refs.append("validation_evidence_detected")
    if record.get("validation_result_outcome"):
        evidence_refs.append(f"validation_result:{record.get('validation_result_outcome')}")
    if record.get("validation_result_fresh_after_last_edit"):
        evidence_refs.append(f"fresh_after_last_edit:{record.get('validation_result_fresh_after_last_edit')}")
    if record.get("validation_result_negative_reason"):
        evidence_refs.append(f"negative_reason:{record.get('validation_result_negative_reason')}")
    if record.get("validation_broker_closure_outcome"):
        evidence_refs.append(f"validation_broker:{record.get('validation_broker_closure_outcome')}")
    for item in _memory_capped_items(record.get("validation_broker_negative_evidence", []) or [])[:5]:
        evidence_refs.append(f"validation_negative:{item}")
    if record.get("implementation_preflight_blocked"):
        evidence_refs.append("implementation_preflight_blocked")
    return {
        "repo_hash": record.get("repo_hash") or _repo_hash(repo),
        "timestamp": record.get("timestamp_utc") or datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "bounded_paths": paths,
        "summary": _memory_summary_from_event(kind, paths, outcome),
        "privacy_class": "safe_bounded",
        "retention_policy": _memory_default_retention_policy(kind),
        "source": "telemetry",
        "task_fingerprint": _memory_task_fingerprint(paths, owner, ""),
        "type": event_type,
        "paths": paths,
        "symbols": [],
        "owner_skill": owner,
        "reviewer_skill": record.get("reviewer_skill", ""),
        "route_manifest_hash": _memory_route_manifest_hash(record),
        "outcome": outcome,
        "evidence_refs": evidence_refs,
        "confidence": "medium",
        "promotion_status": "raw",
        "created_at": record.get("timestamp_utc") or datetime.now(timezone.utc).isoformat(),
    }


def _memory_type_from_telemetry(record: dict[str, Any]) -> str:
    hook_name = str(record.get("hook_name", ""))
    if hook_name == "stop_closure_gate":
        return "validation_result"
    if hook_name == "pre_edit_structure_gate":
        return "implementation_attempt"
    if record.get("validation_command_detected"):
        return "validated_command"
    findings = record.get("hook_findings")
    if isinstance(findings, dict) and findings.get("review_findings"):
        return "review_finding"
    return "implementation_attempt"


def _memory_kind_from_telemetry(record: dict[str, Any], event_type: str) -> str:
    findings = record.get("hook_findings")
    if isinstance(findings, dict):
        if findings.get("review_findings") or findings.get("repair_findings"):
            return "review_finding_pattern"
        if findings.get("structure_findings"):
            return "module_convention"
    if record.get("validation_command_detected") or event_type in {"validation_result", "validated_command"}:
        return "validation_pattern"
    if event_type == "hook_false_positive":
        return "false_positive_hook"
    if event_type == "hook_false_negative":
        return "false_negative_hook"
    return MEMORY_KIND_BY_TYPE.get(event_type, "module_convention")


def _memory_outcome_from_telemetry(record: dict[str, Any]) -> str:
    if record.get("implementation_preflight_blocked"):
        return "blocked"
    broker_outcome = record.get("validation_broker_closure_outcome")
    if broker_outcome == "blocked":
        return "blocked"
    if broker_outcome in {"needs_validation", "degraded_ready"}:
        return "partial"
    if broker_outcome == "ready" and record.get("validation_evidence_detected"):
        return "success"
    if record.get("validation_result_negative_reason") in {"stale", "failed"}:
        return "failed"
    if record.get("validation_result_outcome") == "fail":
        return "failed"
    if record.get("validation_result_outcome") == "not_run":
        return "partial"
    if record.get("validation_evidence_detected") and record.get("residual_risk_detected"):
        return "success"
    if record.get("completion_language_detected") and not record.get("validation_evidence_detected"):
        return "failed"
    if record.get("changed_paths") and not record.get("validation_evidence_detected"):
        return "partial"
    return "unknown"


def _memory_route_manifest_hash(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "manifest_selected_skills",
        "manifest_selected_capabilities",
        "manifest_selected_domain_extensions",
        "manifest_required_references",
        "manifest_required_quality_gates",
    ):
        parts.extend(_capped_items(record.get(key, [])))
    if not parts:
        return ""
    return _hash_text("|".join(parts))


def _read_memory_events(repo: Path, *, max_events: int = 500) -> list[dict[str, Any]]:
    events_dir = memory_root(repo) / "events"
    if not events_dir.is_dir():
        return []
    events: list[dict[str, Any]] = []
    for path in sorted(events_dir.glob("*.jsonl"), reverse=True):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
            if len(events) >= max_events:
                return events
    return events


def _memory_fragile_paths(events: list[dict[str, Any]], paths: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for event in events:
        if not _memory_fragile_signal(event):
            continue
        for path in _memory_event_paths(event):
            item = str(path)
            counts[item] = counts.get(item, 0) + 1
    return [path for path in paths if counts.get(path, 0) >= 2][:MAX_TELEMETRY_ITEMS]


def _memory_fragile_signal(event: dict[str, Any]) -> bool:
    kind = _memory_event_kind(event)
    event_type = str(event.get("type") or "")
    if kind in {"fragile_file", "review_finding_pattern"}:
        return True
    if event_type in {"review_finding", "repair_attempt", "fragile_file"}:
        return True
    return event_type == "validation_result" and event.get("outcome") in {"failed", "blocked"}


def _memory_repeat_failure(
    events: list[dict[str, Any]],
    *,
    repo_hash: str,
    task: str,
    paths: list[str],
    owner: str,
) -> dict[str, Any]:
    exact = _memory_matching_failures(
        events,
        repo_hash=repo_hash,
        task=task,
        paths=paths,
        owner=owner,
        require_task=True,
    )
    failures = exact if len(exact) >= 2 else _memory_matching_failures(
        events,
        repo_hash=repo_hash,
        task=task,
        paths=paths,
        owner=owner,
        require_task=False,
    )
    failures.sort(key=lambda event: str(event.get("created_at", "")), reverse=True)
    repeated = len(failures) >= 2
    return {
        "repeated": repeated,
        "failure_count": min(len(failures), 2),
        "matched_paths": _unique(path for event in failures[:2] for path in _memory_event_paths(event)),
        "required_next_gate": "failure-diagnosis",
        "allowed_to_continue": not repeated,
    }


def _memory_matching_failures(
    events: list[dict[str, Any]],
    *,
    repo_hash: str,
    task: str,
    paths: list[str],
    owner: str,
    require_task: bool,
) -> list[dict[str, Any]]:
    path_set = set(paths)
    failures: list[dict[str, Any]] = []
    for event in events:
        if event.get("repo_hash") != repo_hash:
            continue
        if require_task and event.get("task_fingerprint") != task:
            continue
        if owner and event.get("owner_skill") != owner:
            continue
        if not _memory_paths_overlap(path_set, set(_memory_event_paths(event))):
            continue
        if event.get("outcome") not in {"failed", "blocked"}:
            continue
        failures.append(event)
    return failures


def _memory_event_id(event: dict[str, Any]) -> str:
    return _memory_clean_scalar(event.get("event_id")) or "unknown"


def _memory_event_paths(event: dict[str, Any]) -> list[str]:
    values = event.get("bounded_paths")
    if not isinstance(values, list):
        values = event.get("paths")
    if not isinstance(values, list):
        return []
    return _memory_capped_items(values)


def _memory_event_kind(event: dict[str, Any]) -> str:
    kind = str(event.get("kind") or "").strip()
    if kind:
        return kind
    return MEMORY_KIND_BY_TYPE.get(str(event.get("type") or "").strip(), "module_convention")


def _memory_paths_overlap(left_paths: set[str], right_paths: set[str]) -> bool:
    if left_paths & right_paths:
        return True
    for left in left_paths:
        for right in right_paths:
            if left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                return True
    return False


def _memory_projection_key(
    changed_paths: list[str],
    included: list[dict[str, Any]],
    excluded: list[str],
) -> str:
    payload = {
        "changed_paths": sorted(changed_paths),
        "included": sorted(_memory_event_id(event) for event in included),
        "excluded": sorted(excluded),
        "determinism_version": 1,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def _memory_pre_edit_evidence(state: dict, assistant_text: str) -> dict[str, bool]:
    lowered = assistant_text.casefold()
    return {
        "read_file_evidence": bool(
            state.get("read_evidence_seen")
            or state.get("read_paths")
            or "read_evidence" in lowered
        ),
        "owner_source_of_truth_check": bool(
            "source of truth" in lowered
            or "owner source" in lowered
            or state.get("repository_context_seen")
        ),
        "same_pattern_scan": bool(
            state.get("searched_patterns")
            or "same-pattern" in lowered
            or "same pattern" in lowered
        ),
        "validator_mapping": bool(
            state.get("validation_command_seen")
            or "validator mapping" in lowered
            or "validation broker" in lowered
        ),
        "nearby_test_evidence": bool(
            state.get("validation_command_seen")
            or "test_plan" in lowered
            or "nearby test" in lowered
        ),
        "memory_summary_evidence": bool(
            "project_memory_summary" in lowered
            or "memory summary" in lowered
            or "project memory summary" in lowered
        ),
        "implementation_preflight": bool(
            state.get("implementation_preflight_seen")
            or "changeforge_implementation_preflight" in lowered
        ),
        "failure_diagnosis_route": bool(
            state.get("repair_evidence_seen")
            or "failure-diagnosis" in lowered
            or "failure diagnosis" in lowered
            or "route repair" in lowered
            or "quality-test-gate" in lowered
            or "quality test gate" in lowered
        ),
    }


def _memory_clean_paths(repo: Path, values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for raw in values:
        text = str(raw).replace("\\", "/").strip()
        if not text or text.startswith("~"):
            continue
        if Path(text).is_absolute():
            try:
                text = Path(text).resolve().relative_to(repo.resolve()).as_posix()
            except (OSError, ValueError):
                continue
        else:
            if text.startswith("../") or "/../" in text or text == "..":
                continue
            text = text.lstrip("./")
        if text.startswith("../") or "/../" in text or text == "..":
            continue
        out.append(text[:MAX_TELEMETRY_VALUE_LEN])
        if len(out) >= MAX_TELEMETRY_ITEMS:
            break
    return _unique(out)


def _memory_task_fingerprint(paths: Iterable[str], owner: object, task_hint: object) -> str:
    parts = [str(owner or "").strip(), str(task_hint or "").strip()]
    parts.extend(sorted(str(path).strip() for path in paths if str(path).strip())[:10])
    return _hash_text("|".join(part for part in parts if part) or "unknown-task")


def _memory_confidence(value: object) -> str:
    text = str(value or "").strip()
    return text if text in {"low", "medium", "high"} else "medium"


def _memory_promotion_status(value: object) -> str:
    text = str(value or "").strip()
    return text if text in {"raw", "candidate", "approved", "rejected"} else "raw"


def _memory_summary_from_event(kind: str, paths: list[str], outcome: str) -> str:
    path_text = ", ".join(paths[:3]) if paths else "no bounded path"
    return f"{kind} memory signal for {path_text}; outcome={outcome}"


def _memory_default_retention_policy(kind: str) -> str:
    if kind in {"false_positive_hook", "false_negative_hook"}:
        return "retain_until_human_review"
    if kind in {"fragile_file", "repeat_failure"}:
        return "retain_90_days_or_until_superseded"
    return "retain_30_days_or_until_superseded"


def _memory_contains_forbidden_key(data: Any) -> bool:
    if isinstance(data, dict):
        for key, value in data.items():
            key_text = str(key).casefold()
            if any(token in key_text for token in MEMORY_FORBIDDEN_KEY_TOKENS):
                return True
            if _memory_contains_forbidden_key(value):
                return True
    elif isinstance(data, list):
        return any(_memory_contains_forbidden_key(item) for item in data)
    return False


def _memory_contains_sensitive_value(data: Any) -> bool:
    if isinstance(data, dict):
        return any(_memory_contains_sensitive_value(value) for value in data.values())
    if isinstance(data, list):
        return any(_memory_contains_sensitive_value(item) for item in data)
    if isinstance(data, str):
        return bool(MEMORY_SECRET_VALUE_RE.search(data))
    return False


def _memory_deterministic_event_id(
    repo_hash: str,
    timestamp: str,
    kind: str,
    paths: list[str],
    summary: str,
    source: dict[str, Any],
) -> str:
    payload = {
        "repo_hash": repo_hash,
        "timestamp": timestamp,
        "kind": kind,
        "paths": sorted(paths),
        "summary": summary,
        "source": _memory_clean_scalar(source.get("source")),
        "evidence_refs": _memory_capped_items(source.get("evidence_refs", [])),
    }
    return "mem_" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


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
        "runtime_adapter": {},
        "normalized_events": [],
        "changed_paths": [],
        "deleted_paths": [],
        "generated_paths": [],
        "read_paths": [],
        "read_tools": [],
        "searched_patterns": [],
        "external_file_changes": [],
        "config_changes": [],
        "structure_findings": [],
        "file_naming_findings": [],
        "reuse_findings": [],
        "extension_reuse_findings": [],
        "advanced_refactor_findings": [],
        "comment_findings": [],
        "structure_quality_findings": [],
        "post_edit_structure_findings": [],
        "review_targets": [],
        "review_findings": [],
        "repair_findings": [],
        "repair_events": [],
        "rereview_events": [],
        "validation_results": [],
        "risk_surfaces": [],
        "changed_path_risk_surfaces": [],
        "command_risk_surfaces": [],
        "command_risks": [],
        "closure_risk_surfaces": [],
        "professional_injections": [],
        "professional_injection_digests": [],
        "professional_injection_digest": "",
        "last_professional_injection_event": "",
        "permission_decisions": [],
        "rollback_points": [],
        "reference_loads": [],
        "subagent_contracts": [],
        "compaction_snapshots": [],
        "prompt_signals": [],
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_domain_extensions": [],
        "suggested_gates": [],
        "context_control_records": [],
        "tool_output_boundaries": [],
        "artifact_references": [],
        "branch_route_repair_summaries": [],
        "route_repair_forbidden_retries": [],
        "context_budget_findings": [],
        "skipped_references": [],
        "implementation_preflights": [],
        "senior_programming_judgments": [],
        "pre_edit_structure_findings": [],
        "choice_ids": [],
        "choice_triggers": [],
        "choice_status": [],
        "material_choice_surfaces": [],
        "blocked_tool_category": [],
        "bounded_paths": [],
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
        "repository_context_seen": False,
        "workflow_state_seen": False,
        "tool_permission_sandbox_seen": False,
        "skill_efficacy_benchmark_seen": False,
        "plan_execution_consistency_seen": False,
        "validation_freshness_seen": False,
        "implementation_preflight_seen": False,
        "implementation_preflight_complete": False,
        "implementation_preflight_required": False,
        "implementation_preflight_blocked": False,
        "senior_programming_judgment_seen": False,
        "senior_programming_judgment_complete": False,
        "senior_programming_judgment_required": False,
        "senior_programming_judgment_blocked": False,
        "choice_gate_seen": False,
        "choice_gate_blocked": False,
        "choice_resolution_evidence_seen": False,
        "pre_edit_missing_read_evidence": False,
        "pre_edit_missing_reuse_decision": False,
        "pre_edit_missing_placement_decision": False,
        "pre_edit_missing_test_plan": False,
        "pre_edit_missing_senior_programming_judgment": False,
        "edit_without_preflight_seen": False,
        "post_edit_confirmed_preflight_gap": False,
        "validation_command_seen": False,
        "validation_seen": False,
        "route_preflight_emitted": False,
        "event_index": 0,
        "last_material_edit_index": 0,
        "last_validation_command_index": 0,
        "turn_id": "",
        "updated_at": "",
    }


def _is_follow_up_prompt(event: dict) -> bool:
    for key in ("prompt", "message", "userPrompt", "user_prompt"):
        value = event.get(key)
        if isinstance(value, str) and FOLLOW_UP_PROMPT_RE.search(value[:1000]):
            return True
    return False


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


def _capped_compaction_snapshots(values: Iterable[object]) -> list[dict[str, Any]]:
    """Preserve the latest bounded compaction checkpoints without string truncation."""
    return preserve_required_snapshots(list(values), (), limit=5)


def _capped_context_control_records(values: Iterable[object]) -> list[dict[str, Any]]:
    """Preserve bounded context-control records without raw prompt/output fields."""
    forbidden = {
        "prompt",
        "prompt_text",
        "raw_prompt",
        "raw_output",
        "raw_command_output",
        "full_output",
        "full_diff",
        "full_file",
        "file_contents",
        "environment",
        "env",
        "secret",
        "secrets",
        "credential",
        "credentials",
    }
    out: list[dict[str, Any]] = []
    for raw in values:
        if not isinstance(raw, dict):
            continue
        cleaned = _clean_state_mapping(_strip_forbidden_context_record(raw, forbidden))
        if cleaned:
            out.append(cleaned)
        if len(out) >= 10:
            break
    return out


def _capped_tool_output_boundaries(values: Iterable[object]) -> list[dict[str, Any]]:
    """Preserve bounded tool-output records without raw output or prompt fields."""
    forbidden = {
        "stdout",
        "stderr",
        "command_output",
        "raw_output",
        "full_output",
        "full_diff",
        "file_contents",
        "raw_prompt",
        "prompt",
        "environment",
        "env",
        "secret",
        "secrets",
        "credential",
        "credentials",
        "password",
        "api_key",
        "apikey",
        "token",
    }
    out: list[dict[str, Any]] = []
    for raw in values:
        if not isinstance(raw, dict):
            continue
        cleaned = _clean_tool_output_boundary_record(raw, forbidden)
        if cleaned:
            out.append(cleaned)
        if len(out) >= 10:
            break
    return out


def _capped_artifact_references(values: Iterable[str]) -> list[str]:
    """Keep artifact references repo-relative or cache-scoped."""
    return _capped_state_items(
        ref for ref in (_sanitize_artifact_reference(value) for value in values) if ref
    )


def _capped_branch_route_repair_summaries(values: Iterable[object]) -> list[dict[str, Any]]:
    """Preserve bounded route-repair summaries without raw prompt/output fields."""
    forbidden = {
        "prompt",
        "raw_prompt",
        "raw_output",
        "full_output",
        "command_output",
        "stdout",
        "stderr",
        "full_diff",
        "file_contents",
        "environment",
        "env",
        "secret",
        "secrets",
        "credential",
        "credentials",
        "password",
        "api_key",
        "apikey",
        "token",
    }
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, dict):
            continue
        privacy_failed = _state_summary_privacy_failed(raw, forbidden)
        stripped = _strip_forbidden_context_record(raw, forbidden)
        route = stripped.get("abandoned_or_repaired_route")
        route = route if isinstance(route, dict) else {}
        new_route = stripped.get("new_route")
        new_route = new_route if isinstance(new_route, dict) else {}
        source_findings = _state_summary_items(stripped.get("source_privacy_findings", []))
        if privacy_failed and "forbidden_raw_field" not in source_findings:
            source_findings.append("forbidden_raw_field")
        retained_findings = _state_summary_items(stripped.get("retained_summary_privacy_findings", []))
        retained_status = (
            "fail"
            if retained_findings or str(stripped.get("retained_summary_privacy_status") or "").strip() == "fail"
            else "pass"
        )
        record = {
            "schema_version": 1,
            "summary_id": _state_summary_text(stripped.get("summary_id")),
            "trigger": _state_summary_text(stripped.get("trigger") or "route_repair"),
            "abandoned_or_repaired_route": {
                "owner_skill": _state_summary_text(route.get("owner_skill")),
                "reviewer_skill": _state_summary_text(route.get("reviewer_skill")),
                "hypothesis": _state_summary_text(route.get("hypothesis")),
                "files_touched": _state_summary_items(route.get("files_touched", [])),
                "validation_result": _state_summary_text(route.get("validation_result")),
                "failure_reason": _state_summary_text(route.get("failure_reason")),
            },
            "reusable_findings": _state_summary_items(stripped.get("reusable_findings", [])),
            "forbidden_retries": _state_summary_items(stripped.get("forbidden_retries", [])),
            "new_route": {
                "owner_skill": _state_summary_text(new_route.get("owner_skill")),
                "selected_capabilities": _state_summary_items(new_route.get("selected_capabilities", [])),
                "validation_plan": _state_summary_items(new_route.get("validation_plan", [])),
            },
            "residual_risk": _state_summary_items(stripped.get("residual_risk", [])),
            "source_privacy_findings": source_findings,
            "source_privacy_status": "fail"
            if source_findings or str(stripped.get("source_privacy_status") or "").strip() == "fail"
            else "pass",
            "retained_summary_privacy_findings": retained_findings,
            "retained_summary_privacy_status": retained_status,
            "privacy_redaction_status": "pass" if retained_status == "pass" else "fail",
            "privacy_status": retained_status,
        }
        if not record["summary_id"]:
            record["summary_id"] = _hash_text(json.dumps(record, sort_keys=True))
        if record["summary_id"] in seen:
            continue
        seen.add(record["summary_id"])
        out.append(record)
        if len(out) >= 10:
            break
    return out


def _state_summary_text(value: object) -> str:
    text = str(value or "").replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    if not text:
        return ""
    text = STATE_SECRET_RE.sub("<redacted-secret>", text)
    text = STATE_LOCAL_PATH_RE.sub("<local-path>", text)
    return text[:MAX_STATE_VALUE_LEN]


def _state_summary_items(values: object) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return _capped_state_items(_state_summary_text(value) for value in values)


def _state_summary_privacy_failed(value: object, forbidden: set[str]) -> bool:
    if _state_record_has_forbidden_key(value, forbidden):
        return True
    try:
        text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    except TypeError:
        text = str(value)
    return bool(STATE_SECRET_RE.search(text) or STATE_LOCAL_PATH_RE.search(text))


def _state_record_has_forbidden_key(value: object, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).casefold()
            if lowered in forbidden or any(token in lowered for token in forbidden):
                return True
            if _state_record_has_forbidden_key(child, forbidden):
                return True
    if isinstance(value, (list, tuple, set)):
        return any(_state_record_has_forbidden_key(item, forbidden) for item in value)
    return False


def _sanitize_artifact_reference(value: object) -> str:
    text = str(value or "").strip().strip("'\"").replace("\\", "/")
    if not text or "\n" in text or "\0" in text or "://" in text:
        return ""
    if text.startswith("./"):
        text = text[2:]
    if not text.startswith(("/", "~")) and not re.match(r"^[A-Za-z]:/", text):
        if text.startswith("../") or "/../" in text or text == "..":
            return ""
        return text[:MAX_STATE_VALUE_LEN]
    for marker in ("/.cache/changeforge/", "/Library/Caches/changeforge/"):
        if marker in text:
            return ("${CACHE}/changeforge/" + text.split(marker, 1)[1].lstrip("/"))[
                :MAX_STATE_VALUE_LEN
            ]
    return "<local-artifact-path-redacted>"


def _clean_tool_output_boundary_record(raw: dict[str, Any], forbidden: set[str]) -> dict[str, Any]:
    allowed = {
        "schema_version",
        "tool_name",
        "event_name",
        "output_size_class",
        "output_bytes",
        "output_lines",
        "artifact_path",
        "artifact_path_source",
        "digest",
        "bounded_summary",
        "truncation_advice",
        "llm_context_policy",
        "privacy_status",
        "unsupported_reason",
    }
    stripped = _strip_forbidden_context_record(raw, forbidden)
    cleaned: dict[str, Any] = {}
    for key, value in stripped.items():
        name = str(key).strip()[:80]
        if name not in allowed:
            continue
        if name in {"schema_version", "output_bytes", "output_lines"}:
            try:
                cleaned[name] = max(0, int(value)) if value is not None else None
            except (TypeError, ValueError):
                cleaned[name] = None
        elif name == "bounded_summary":
            cleaned[name] = _capped_state_items(str(item) for item in value) if isinstance(value, (list, tuple)) else []
        elif name == "artifact_path":
            cleaned[name] = _sanitize_artifact_reference(value)
        else:
            cleaned[name] = str(value or "").strip()[:MAX_STATE_VALUE_LEN]
    if not cleaned.get("artifact_path"):
        cleaned["artifact_path"] = ""
        cleaned["artifact_path_source"] = "not_available"
    return cleaned


def _strip_forbidden_context_record(value: Any, forbidden: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for key, raw in value.items():
        name = str(key).strip()
        lowered = name.casefold()
        if not name or lowered in forbidden or any(token in lowered for token in forbidden):
            continue
        if isinstance(raw, dict):
            cleaned[name] = _strip_forbidden_context_record(raw, forbidden)
        elif isinstance(raw, (list, tuple)):
            cleaned[name] = [
                _strip_forbidden_context_record(item, forbidden) if isinstance(item, dict) else item
                for item in raw
            ]
        else:
            cleaned[name] = raw
    return cleaned


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
