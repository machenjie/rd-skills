"""Normalized runtime event facts for ChangeForge governance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .privacy import cap_list, normalize_relative_path, redact_sensitive_value, sanitize_command_kind
from .serialization import json_dumps, json_loads, to_json_dict


class EventKind(str, Enum):
    SESSION_START = "session_start"
    USER_PROMPT_SUBMIT = "user_prompt_submit"
    USER_PROMPT_EXPANSION = "user_prompt_expansion"
    PRE_TOOL_USE = "pre_tool_use"
    PERMISSION_REQUEST = "permission_request"
    POST_TOOL_USE = "post_tool_use"
    POST_TOOL_USE_FAILURE = "post_tool_use_failure"
    POST_TOOL_BATCH = "post_tool_batch"
    STOP = "stop"
    STOP_FAILURE = "stop_failure"
    SESSION_END = "session_end"
    SUBAGENT_START = "subagent_start"
    SUBAGENT_STOP = "subagent_stop"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    FILE_CHANGED = "file_changed"
    CONFIG_CHANGED = "config_changed"
    WORKTREE_CREATE = "worktree_create"
    WORKTREE_REMOVE = "worktree_remove"
    PRE_COMPACT = "pre_compact"
    POST_COMPACT = "post_compact"
    COMPACT = "compact"
    UNKNOWN = "unknown"


_EVENT_KIND_ALIASES = {
    "sessionstart": EventKind.SESSION_START,
    "session_start": EventKind.SESSION_START,
    "userpromptsubmit": EventKind.USER_PROMPT_SUBMIT,
    "user_prompt_submit": EventKind.USER_PROMPT_SUBMIT,
    "userpromptexpansion": EventKind.USER_PROMPT_EXPANSION,
    "user_prompt_expansion": EventKind.USER_PROMPT_EXPANSION,
    "pretooluse": EventKind.PRE_TOOL_USE,
    "pre_tool_use": EventKind.PRE_TOOL_USE,
    "permissionrequest": EventKind.PERMISSION_REQUEST,
    "permission_request": EventKind.PERMISSION_REQUEST,
    "posttooluse": EventKind.POST_TOOL_USE,
    "post_tool_use": EventKind.POST_TOOL_USE,
    "posttoolusefailure": EventKind.POST_TOOL_USE_FAILURE,
    "post_tool_use_failure": EventKind.POST_TOOL_USE_FAILURE,
    "posttoolbatch": EventKind.POST_TOOL_BATCH,
    "post_tool_batch": EventKind.POST_TOOL_BATCH,
    "stop": EventKind.STOP,
    "stopfailure": EventKind.STOP_FAILURE,
    "stop_failure": EventKind.STOP_FAILURE,
    "sessionend": EventKind.SESSION_END,
    "session_end": EventKind.SESSION_END,
    "subagentstart": EventKind.SUBAGENT_START,
    "subagent_start": EventKind.SUBAGENT_START,
    "subagentstop": EventKind.SUBAGENT_STOP,
    "subagent_stop": EventKind.SUBAGENT_STOP,
    "taskcreated": EventKind.TASK_CREATED,
    "task_created": EventKind.TASK_CREATED,
    "taskcompleted": EventKind.TASK_COMPLETED,
    "task_completed": EventKind.TASK_COMPLETED,
    "filechanged": EventKind.FILE_CHANGED,
    "file_changed": EventKind.FILE_CHANGED,
    "configchanged": EventKind.CONFIG_CHANGED,
    "config_changed": EventKind.CONFIG_CHANGED,
    "worktreecreate": EventKind.WORKTREE_CREATE,
    "worktree_create": EventKind.WORKTREE_CREATE,
    "worktreeremove": EventKind.WORKTREE_REMOVE,
    "worktree_remove": EventKind.WORKTREE_REMOVE,
    "precompact": EventKind.PRE_COMPACT,
    "pre_compact": EventKind.PRE_COMPACT,
    "postcompact": EventKind.POST_COMPACT,
    "post_compact": EventKind.POST_COMPACT,
    "compact": EventKind.COMPACT,
    "compaction": EventKind.COMPACT,
    "contextcompact": EventKind.COMPACT,
}

_EVENT_CADENCE = {
    EventKind.SESSION_START.value: "session",
    EventKind.USER_PROMPT_SUBMIT.value: "turn",
    EventKind.USER_PROMPT_EXPANSION.value: "turn",
    EventKind.PRE_TOOL_USE.value: "tool",
    EventKind.PERMISSION_REQUEST.value: "tool",
    EventKind.POST_TOOL_USE.value: "tool",
    EventKind.POST_TOOL_USE_FAILURE.value: "tool",
    EventKind.POST_TOOL_BATCH.value: "tool",
    EventKind.STOP.value: "stop",
    EventKind.STOP_FAILURE.value: "stop",
    EventKind.SESSION_END.value: "session",
    EventKind.SUBAGENT_START.value: "subagent",
    EventKind.SUBAGENT_STOP.value: "subagent",
    EventKind.TASK_CREATED.value: "task",
    EventKind.TASK_COMPLETED.value: "task",
    EventKind.FILE_CHANGED.value: "file",
    EventKind.CONFIG_CHANGED.value: "file",
    EventKind.WORKTREE_CREATE.value: "file",
    EventKind.WORKTREE_REMOVE.value: "file",
    EventKind.PRE_COMPACT.value: "compact",
    EventKind.POST_COMPACT.value: "compact",
    EventKind.COMPACT.value: "compact",
    EventKind.UNKNOWN.value: "unknown",
}

_EVENT_PHASE = {
    EventKind.SESSION_START.value: "before",
    EventKind.USER_PROMPT_SUBMIT.value: "before",
    EventKind.USER_PROMPT_EXPANSION.value: "before",
    EventKind.PRE_TOOL_USE.value: "before",
    EventKind.PERMISSION_REQUEST.value: "before",
    EventKind.POST_TOOL_USE.value: "after",
    EventKind.POST_TOOL_USE_FAILURE.value: "failure",
    EventKind.POST_TOOL_BATCH.value: "after",
    EventKind.STOP.value: "end",
    EventKind.STOP_FAILURE.value: "failure",
    EventKind.SESSION_END.value: "end",
    EventKind.SUBAGENT_START.value: "before",
    EventKind.SUBAGENT_STOP.value: "end",
    EventKind.TASK_CREATED.value: "before",
    EventKind.TASK_COMPLETED.value: "after",
    EventKind.FILE_CHANGED.value: "after",
    EventKind.CONFIG_CHANGED.value: "after",
    EventKind.WORKTREE_CREATE.value: "after",
    EventKind.WORKTREE_REMOVE.value: "after",
    EventKind.PRE_COMPACT.value: "before",
    EventKind.POST_COMPACT.value: "after",
    EventKind.COMPACT.value: "unknown",
    EventKind.UNKNOWN.value: "unknown",
}

_TOOL_CATEGORIES = {"read", "edit", "write", "bash", "test", "git", "network", "mcp", "unknown"}
_COMMAND_RISKS = {"safe", "mutation", "destructive", "release", "migration", "dependency", "network", "unknown"}
_COMMAND_OUTCOMES = {"pass", "fail", "timeout", "cancelled", "unknown", "not_observable"}
_VALIDATION_OUTCOMES = {"pass", "fail", "not_run", "not_verified", "stale", "partial", "unknown"}
_VALIDATION_FRESHNESS = {"current", "stale", "unknown", "not_applicable"}
_PERMISSION_DECISIONS = {"allow", "deny", "ask", "unknown", "not_observable"}


@dataclass
class NormalizedEvent:
    """Bounded runtime event fact shared by hooks, broker, and trajectory tools."""

    event_id: str
    adapter: str
    event_kind: str
    action_type: str | None = None
    stage_signal: str | None = None
    bounded_paths: list[str] = field(default_factory=list)
    command_kind: str | None = None
    timestamp: str | None = None
    source: str | None = None
    capability_degradation: list[str] = field(default_factory=list)
    lifecycle_cadence: str | None = None
    executor_event_name: str | None = None
    executor_event_phase: str | None = None
    tool_category: str | None = None
    command_risk: str | None = None
    command_outcome: str | None = None
    exit_code: int | None = None
    read_paths: list[str] = field(default_factory=list)
    changed_paths: list[str] = field(default_factory=list)
    deleted_paths: list[str] = field(default_factory=list)
    generated_paths: list[str] = field(default_factory=list)
    validation_candidate: bool | None = None
    validation_outcome: str | None = None
    validation_freshness: str | None = None
    permission_decision: str | None = None
    permission_reason: str | None = None
    checkpoint_id: str | None = None
    rollback_available: bool | None = None
    privacy_redaction: list[str] = field(default_factory=list)

    @classmethod
    def from_telemetry_fact(cls, fact: Mapping[str, Any], *, base_path: str | None = None) -> "NormalizedEvent":
        """Build a normalized event from existing hook telemetry fields."""
        raw_event = _first_text(fact, "event_kind", "event_name", "hook_event_name", "event_type")
        event_kind = _event_kind(raw_event)
        degradation = cap_list(fact.get("capability_degradation") or fact.get("adapter_degradation") or [])
        if event_kind == EventKind.UNKNOWN.value:
            detail = f"unsupported_event:{redact_sensitive_value(raw_event) or 'missing'}"
            degradation = cap_list([*degradation, detail])

        command = (
            fact.get("command_kind")
            or fact.get("command_program")
            or fact.get("command")
            or fact.get("tool_command")
        )
        command_kind = sanitize_command_kind(command)
        read_paths = _path_list(fact, "read_paths", "opened_paths", "input_paths", base_path=base_path)
        changed_paths = _path_list(
            fact,
            "changed_paths",
            "added_paths",
            "modified_paths",
            "created_paths",
            base_path=base_path,
        )
        deleted_paths = _path_list(fact, "deleted_paths", "removed_paths", base_path=base_path)
        generated_paths = _path_list(fact, "generated_paths", "output_paths", base_path=base_path)
        bounded_paths = cap_list(
            [
                *read_paths,
                *changed_paths,
                *deleted_paths,
                *generated_paths,
                *_path_list(fact, "bounded_paths", "validation_result_covered_paths", base_path=base_path),
            ],
            item_sanitizer=normalize_relative_path,
        )
        exit_code = _optional_int(_first_present(fact, "exit_code", "returncode", "status_code"))
        tool_category = _tool_category(fact, command_kind)
        validation_candidate = _optional_bool(fact.get("validation_candidate"))
        if validation_candidate is None:
            validation_candidate = tool_category == "test"
        return cls(
            event_id=redact_sensitive_value(fact.get("event_id")) or _event_id(fact),
            adapter=redact_sensitive_value(fact.get("adapter") or fact.get("runtime") or "unknown"),
            event_kind=event_kind,
            action_type=_optional_fact(fact.get("action_type") or fact.get("hook_name") or fact.get("tool_name")),
            stage_signal=_optional_fact(
                fact.get("stage_signal") or fact.get("turn_stage") or fact.get("manifest_current_stage")
            ),
            bounded_paths=bounded_paths,
            command_kind=command_kind,
            timestamp=_optional_fact(fact.get("timestamp") or fact.get("timestamp_utc")),
            source=_optional_fact(fact.get("source") or fact.get("hook_name") or fact.get("_source")),
            capability_degradation=degradation,
            lifecycle_cadence=_bounded_choice(
                fact.get("lifecycle_cadence"),
                set(_EVENT_CADENCE.values()),
                _EVENT_CADENCE.get(event_kind, "unknown"),
            ),
            executor_event_name=_optional_fact(raw_event),
            executor_event_phase=_bounded_choice(
                fact.get("executor_event_phase") or fact.get("event_phase"),
                {"before", "after", "failure", "end", "unknown"},
                _EVENT_PHASE.get(event_kind, "unknown"),
            ),
            tool_category=tool_category,
            command_risk=_bounded_choice(fact.get("command_risk"), _COMMAND_RISKS, None)
            or _command_risk(command, command_kind),
            command_outcome=_command_outcome(fact, exit_code),
            exit_code=exit_code,
            read_paths=read_paths,
            changed_paths=changed_paths,
            deleted_paths=deleted_paths,
            generated_paths=generated_paths,
            validation_candidate=validation_candidate,
            validation_outcome=_validation_outcome(fact),
            validation_freshness=_validation_freshness(fact),
            permission_decision=_permission_decision(fact),
            permission_reason=_optional_fact(fact.get("permission_reason") or fact.get("reason")),
            checkpoint_id=_optional_fact(fact.get("checkpoint_id") or fact.get("checkpoint")),
            rollback_available=_optional_bool(fact.get("rollback_available")),
            privacy_redaction=_privacy_redaction(fact),
        )

    def is_supported(self) -> bool:
        """Return whether the event kind was recognized by the adapter."""
        return self.event_kind != EventKind.UNKNOWN.value and not self.capability_degradation

    def to_json_dict(self) -> dict[str, Any]:
        return to_json_dict(self)

    def to_json(self) -> str:
        return json_dumps(self)

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any]) -> "NormalizedEvent":
        return cls(
            event_id=str(data.get("event_id") or ""),
            adapter=str(data.get("adapter") or "unknown"),
            event_kind=_event_kind(data.get("event_kind")),
            action_type=_maybe_str(data.get("action_type")),
            stage_signal=_maybe_str(data.get("stage_signal")),
            bounded_paths=cap_list(data.get("bounded_paths") or [], item_sanitizer=normalize_relative_path),
            command_kind=_maybe_str(data.get("command_kind")),
            timestamp=_maybe_str(data.get("timestamp")),
            source=_maybe_str(data.get("source")),
            capability_degradation=cap_list(data.get("capability_degradation") or []),
            lifecycle_cadence=_bounded_choice(data.get("lifecycle_cadence"), set(_EVENT_CADENCE.values()), None),
            executor_event_name=_maybe_str(data.get("executor_event_name")),
            executor_event_phase=_bounded_choice(
                data.get("executor_event_phase"),
                {"before", "after", "failure", "end", "unknown"},
                None,
            ),
            tool_category=_bounded_choice(data.get("tool_category"), _TOOL_CATEGORIES, None),
            command_risk=_bounded_choice(data.get("command_risk"), _COMMAND_RISKS, None),
            command_outcome=_bounded_choice(data.get("command_outcome"), _COMMAND_OUTCOMES, None),
            exit_code=_optional_int(data.get("exit_code")),
            read_paths=cap_list(data.get("read_paths") or [], item_sanitizer=normalize_relative_path),
            changed_paths=cap_list(data.get("changed_paths") or [], item_sanitizer=normalize_relative_path),
            deleted_paths=cap_list(data.get("deleted_paths") or [], item_sanitizer=normalize_relative_path),
            generated_paths=cap_list(data.get("generated_paths") or [], item_sanitizer=normalize_relative_path),
            validation_candidate=_optional_bool(data.get("validation_candidate")),
            validation_outcome=_bounded_choice(data.get("validation_outcome"), _VALIDATION_OUTCOMES, None),
            validation_freshness=_bounded_choice(data.get("validation_freshness"), _VALIDATION_FRESHNESS, None),
            permission_decision=_bounded_choice(data.get("permission_decision"), _PERMISSION_DECISIONS, None),
            permission_reason=_maybe_str(data.get("permission_reason")),
            checkpoint_id=_maybe_str(data.get("checkpoint_id")),
            rollback_available=_optional_bool(data.get("rollback_available")),
            privacy_redaction=cap_list(data.get("privacy_redaction") or []),
        )

    @classmethod
    def from_json(cls, text: str) -> "NormalizedEvent":
        return cls.from_json_dict(json_loads(text))


def _event_kind(value: object) -> str:
    text = str(value or "").strip()
    key = text.replace("-", "_").replace(" ", "_").casefold()
    compact = key.replace("_", "")
    kind = _EVENT_KIND_ALIASES.get(key) or _EVENT_KIND_ALIASES.get(compact)
    return (kind or EventKind.UNKNOWN).value


def _first_text(fact: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = fact.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _first_present(fact: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in fact:
            return fact.get(key)
    return None


def _optional_fact(value: object) -> str | None:
    text = redact_sensitive_value(value)
    return text or None


def _maybe_str(value: object) -> str | None:
    if value is None:
        return None
    text = redact_sensitive_value(value)
    return text or None


def _bounded_choice(value: object, allowed: set[str], default: str | None) -> str | None:
    text = redact_sensitive_value(value).strip().casefold()
    if text in allowed:
        return text
    return default


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().casefold()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _path_list(fact: Mapping[str, Any], *keys: str, base_path: str | None = None) -> list[str]:
    paths: list[object] = []
    for key in keys:
        value = fact.get(key)
        if isinstance(value, (list, tuple, set)):
            paths.extend(value)
        elif value:
            paths.append(value)
    return cap_list(paths, item_sanitizer=lambda value: normalize_relative_path(value, base=base_path))


def _tool_category(fact: Mapping[str, Any], command_kind: str | None) -> str:
    explicit = _bounded_choice(fact.get("tool_category"), _TOOL_CATEGORIES, None)
    if explicit:
        return explicit
    tool = str(
        fact.get("tool_name")
        or fact.get("tool")
        or fact.get("action_type")
        or fact.get("hook_name")
        or ""
    ).strip().casefold()
    compact_tool = "".join(ch for ch in tool if ch.isalnum())
    command = str(command_kind or "").casefold()
    command_text = " ".join(
        str(fact.get(key) or "")
        for key in ("command", "tool_command", "command_program", "command_kind")
    ).casefold()
    if compact_tool in {"read", "grep", "glob", "ls", "fetch", "open", "view"} or command in {
        "cat",
        "sed",
        "rg",
        "grep",
        "find",
        "ls",
    }:
        return "read"
    if compact_tool in {"edit", "write", "multiedit", "applypatch", "apply_patch"}:
        return "edit"
    if compact_tool in {"mcp", "mcpfilesystemreadfile", "mcpgithubpullrequestread"}:
        return "mcp"
    if command in {"git"}:
        return "git"
    if (
        command in {"pytest", "unittest", "tox", "nox"}
        or "test" in command
        or "validate" in command
        or any(token in command_text for token in ("pytest", "unittest", "validate", " test"))
    ):
        return "test"
    if command in {"curl", "wget", "ssh", "scp", "rsync"}:
        return "network"
    if compact_tool in {"bash", "shell", "terminal", "runterminalcommand"} or command:
        return "bash"
    return "unknown"


def _command_risk(command: object, command_kind: str | None) -> str:
    text = str(command or "").casefold()
    program = str(command_kind or "").casefold()
    if not text and not program:
        return "unknown"
    if program in {"rm", "rmdir"} or any(token in text for token in (" reset --hard", " clean -fd", " --force", " delete ")):
        return "destructive"
    if any(token in text for token in (" deploy", " release", " publish", " push ", " upload", " terraform apply")):
        return "release"
    if any(token in text for token in (" migrate", " migration", " alembic", " liquibase", " flyway")):
        return "migration"
    if any(token in text for token in (" install", " add ", " update ", " pip ", " npm ", " pnpm ", " yarn ", " poetry ", " uv ")):
        return "dependency"
    if program in {"curl", "wget", "ssh", "scp", "rsync"}:
        return "network"
    if any(token in text for token in (" apply_patch", " write", " edit", " mv ", " cp ", " chmod", " chown")):
        return "mutation"
    return "safe"


def _command_outcome(fact: Mapping[str, Any], exit_code: int | None) -> str:
    outcome = _bounded_choice(
        fact.get("command_outcome") or fact.get("outcome") or fact.get("status"),
        _COMMAND_OUTCOMES,
        None,
    )
    if outcome:
        return outcome
    if exit_code is None:
        return "not_observable"
    return "pass" if exit_code == 0 else "fail"


def _validation_outcome(fact: Mapping[str, Any]) -> str | None:
    value = fact.get("validation_outcome") or fact.get("validation_result_outcome")
    text = str(value or "").strip().casefold()
    aliases = {"passed": "pass", "failed": "fail", "notrun": "not_run", "notverified": "not_verified"}
    text = aliases.get(text.replace("-", "_"), text.replace("-", "_"))
    return text if text in _VALIDATION_OUTCOMES else None


def _validation_freshness(fact: Mapping[str, Any]) -> str | None:
    value = fact.get("validation_freshness")
    if value is not None:
        return _bounded_choice(value, _VALIDATION_FRESHNESS, None)
    fresh = str(fact.get("validation_result_fresh_after_last_edit") or "").strip().casefold()
    if fresh == "true":
        return "current"
    if fresh == "false":
        return "stale"
    if fresh == "not_applicable":
        return "not_applicable"
    return None


def _permission_decision(fact: Mapping[str, Any]) -> str | None:
    return _bounded_choice(
        fact.get("permission_decision") or fact.get("decision"),
        _PERMISSION_DECISIONS,
        None,
    )


def _privacy_redaction(fact: Mapping[str, Any]) -> list[str]:
    redactions = cap_list(fact.get("privacy_redaction") or [])
    for field_name in (
        "prompt",
        "prompt_text",
        "user_prompt",
        "full_command",
        "command_output",
        "stdout",
        "stderr",
    ):
        if field_name in fact:
            redactions.append(f"{field_name}:ignored")
    return cap_list(redactions)


def _event_id(fact: Mapping[str, Any]) -> str:
    parts = [
        str(fact.get("session_id") or ""),
        str(fact.get("timestamp_utc") or fact.get("timestamp") or ""),
        str(fact.get("event_name") or fact.get("event_kind") or fact.get("hook_name") or ""),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"event-{digest}"
