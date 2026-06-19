"""Canonical executor adapter protocol for ChangeForge runtimes."""

from __future__ import annotations

import hashlib
import re
import shlex
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..events import EventKind, NormalizedEvent
from ..gates import GateResult
from ..privacy import cap_list, normalize_relative_path, redact_sensitive_value, sanitize_command_kind


CANONICAL_EVENTS = (
    "SessionStart",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "PostToolBatch",
    "Stop",
    "StopFailure",
    "SessionEnd",
    "SubagentStart",
    "SubagentStop",
    "TaskCreated",
    "TaskCompleted",
    "FileChanged",
    "ConfigChanged",
    "WorktreeCreate",
    "WorktreeRemove",
    "PreCompact",
    "PostCompact",
    "Compact",
    "Unknown",
)

EVENT_SUPPORT_FIELDS = {
    "SessionStart": "supports_session_start",
    "UserPromptSubmit": "supports_user_prompt_submit",
    "UserPromptExpansion": "supports_user_prompt_submit",
    "PreToolUse": "supports_pre_tool_use",
    "PostToolUse": "supports_post_tool_use",
    "PostToolUseFailure": "supports_post_tool_failure",
    "PostToolBatch": "supports_tool_batch",
    "Stop": "supports_stop",
    "StopFailure": "supports_stop",
    "SessionEnd": "supports_session_end",
    "SubagentStart": "supports_subagent_start",
    "SubagentStop": "supports_subagent_stop",
    "PermissionRequest": "supports_permission_decision",
    "TaskCreated": "supports_task_lifecycle",
    "TaskCompleted": "supports_task_lifecycle",
    "FileChanged": "supports_file_changed_event",
    "ConfigChanged": "supports_config_changed_event",
    "WorktreeCreate": "supports_worktree_lifecycle",
    "WorktreeRemove": "supports_worktree_lifecycle",
    "PreCompact": "supports_pre_compact",
    "PostCompact": "supports_post_compact",
    "Compact": "supports_context_injection",
}

EVENT_KIND_BY_CANONICAL = {
    "SessionStart": EventKind.SESSION_START.value,
    "UserPromptSubmit": EventKind.USER_PROMPT_SUBMIT.value,
    "UserPromptExpansion": EventKind.USER_PROMPT_EXPANSION.value,
    "PreToolUse": EventKind.PRE_TOOL_USE.value,
    "PermissionRequest": EventKind.PERMISSION_REQUEST.value,
    "PostToolUse": EventKind.POST_TOOL_USE.value,
    "PostToolUseFailure": EventKind.POST_TOOL_USE_FAILURE.value,
    "PostToolBatch": EventKind.POST_TOOL_BATCH.value,
    "Stop": EventKind.STOP.value,
    "StopFailure": EventKind.STOP_FAILURE.value,
    "SessionEnd": EventKind.SESSION_END.value,
    "SubagentStart": EventKind.SUBAGENT_START.value,
    "SubagentStop": EventKind.SUBAGENT_STOP.value,
    "TaskCreated": EventKind.TASK_CREATED.value,
    "TaskCompleted": EventKind.TASK_COMPLETED.value,
    "FileChanged": EventKind.FILE_CHANGED.value,
    "ConfigChanged": EventKind.CONFIG_CHANGED.value,
    "WorktreeCreate": EventKind.WORKTREE_CREATE.value,
    "WorktreeRemove": EventKind.WORKTREE_REMOVE.value,
    "PreCompact": EventKind.PRE_COMPACT.value,
    "PostCompact": EventKind.POST_COMPACT.value,
    "Compact": EventKind.COMPACT.value,
    "Unknown": EventKind.UNKNOWN.value,
}

CONTEXT_EVENTS_BY_RUNTIME = {
    "codex": {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "SubagentStart",
        "SubagentStop",
        "Compact",
    },
    "claude": {
        "SessionStart",
        "UserPromptSubmit",
        "UserPromptExpansion",
        "PreToolUse",
        "PostToolUse",
        "PostToolBatch",
        "SubagentStart",
        "SubagentStop",
        "Compact",
    },
    "copilot": {"SessionStart", "PostToolUse", "SubagentStart"},
    "generic": {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse"},
    "cline": set(),
    "roo": set(),
    "openhands": set(),
}

SUPPORTED_RUNTIMES = ("codex", "claude", "copilot", "generic", "cline", "roo", "openhands")
PLACEHOLDER_RUNTIMES = ("gemini-cli", "goose")
COPILOT_UNSUPPORTED_ADVISORY_EVENTS = ("UserPromptSubmit", "PreToolUse", "SubagentStop")

_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File:\s+(.+?)\s*$")
_DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)\s*$")
_DIFF_FILE_RE = re.compile(r"^(?:\+\+\+|---)\s+(?:a/|b/)?(.+?)\s*$")
_READ_TOOLS = {
    "read",
    "readfile",
    "grep",
    "glob",
    "ls",
    "list",
    "listdirectory",
    "view",
    "open",
    "search",
    "searchcode",
    "fetch",
    "fetchfile",
    "fetchprpatch",
    "getprdiff",
    "cat",
    "sed",
    "rg",
    "mcpfilesystemreadfile",
    "mcpfilesystemlistdirectory",
    "mcpgithubgetfilecontents",
    "mcpgithubpullrequestread",
    "mcpgithubsearchcode",
}
_EDIT_TOOLS = {
    "edit",
    "write",
    "multiedit",
    "applypatch",
    "apply_patch",
    "replace_string_in_file",
    "createfile",
    "create_file",
    "insert_edit_into_file",
}
_MCP_TOOLS = {
    "mcp",
    "mcpfilesystemreadfile",
    "mcpfilesystemlistdirectory",
    "mcpgithubgetfilecontents",
    "mcpgithubpullrequestread",
    "mcpgithubsearchcode",
}
_READ_COMMANDS = {"cat", "sed", "rg", "grep", "find", "ls", "pwd", "head", "tail", "wc"}
_NETWORK_COMMANDS = {"curl", "wget", "ssh", "scp", "rsync"}
_TEST_COMMANDS = {"pytest", "unittest", "tox", "nox", "jest", "vitest"}
_TEST_COMMAND_TOKENS = (
    "pytest",
    "unittest",
    "go test",
    "cargo test",
    "npm test",
    "pnpm test",
    "yarn test",
    " validate",
)

DEFAULT_SUPPORTED_CHECKS = (
    "route_manifest",
    "changed_files",
    "validation_broker",
    "validation_freshness",
    "residual_risk",
    "stop_decision",
)
RICH_SUPPORTED_CHECKS = (
    *DEFAULT_SUPPORTED_CHECKS,
    "pre_tool_advisory_context",
    "post_tool_context",
    "user_prompt_advisory_context",
    "subagent_start_context",
    "subagent_stop_context",
    "permission_signal",
    "permission_decision",
    "post_tool_failure_context",
    "tool_batch_context",
    "file_change_event",
    "config_change_event",
    "worktree_lifecycle",
    "compact_direction",
    "session_end",
    "task_lifecycle",
    "checkpoint_or_rollback",
    "plan_act_mode",
    "codebase_index",
    "mode_or_role_switch",
)
CODEX_SUPPORTED_CHECKS = (
    *DEFAULT_SUPPORTED_CHECKS,
    "pre_tool_advisory_context",
    "post_tool_context",
    "user_prompt_advisory_context",
    "subagent_start_context",
    "subagent_stop_context",
    "permission_signal",
    "permission_decision",
    "pre_tool_block",
    "compact_direction",
)
CLAUDE_SUPPORTED_CHECKS = (
    *CODEX_SUPPORTED_CHECKS,
    "post_tool_failure_context",
    "tool_batch_context",
    "file_change_event",
    "config_change_event",
    "session_end",
    "task_lifecycle",
)
CLAUDE_UNSUPPORTED_CHECKS = (
    "worktree_lifecycle",
    "checkpoint_or_rollback",
    "plan_act_mode",
    "codebase_index",
    "mode_or_role_switch",
)
RICH_UNSUPPORTED_CHECKS = (
    "post_tool_failure_context",
    "file_change_event",
    "config_change_event",
    "worktree_lifecycle",
    "session_end",
    "task_lifecycle",
    "checkpoint_or_rollback",
    "plan_act_mode",
    "codebase_index",
    "mode_or_role_switch",
)
COPILOT_SUPPORTED_CHECKS = (
    *DEFAULT_SUPPORTED_CHECKS,
    "post_tool_context",
    "subagent_start_context",
)
COPILOT_UNSUPPORTED_CHECKS = (
    "pre_tool_advisory_context",
    "user_prompt_advisory_context",
    "subagent_stop_context",
    "permission_signal",
    "permission_decision",
    "pre_tool_block",
    "tool_batch_context",
    "post_tool_failure_context",
)
GENERIC_UNSUPPORTED_CHECKS = (
    "stop_block",
    "subagent_start_context",
    "subagent_stop_context",
    "permission_signal",
    "permission_decision",
    "command_outcome",
    "tool_batch_context",
    "post_tool_failure_context",
    "file_change_event",
    "config_change_event",
    "worktree_lifecycle",
    "compact_direction",
    "session_end",
    "task_lifecycle",
    "checkpoint_or_rollback",
    "plan_act_mode",
    "codebase_index",
    "mode_or_role_switch",
)
PLACEHOLDER_UNSUPPORTED_CHECKS = (
    "route_manifest",
    "changed_files",
    "validation_broker",
    "validation_freshness",
    "residual_risk",
    "stop_decision",
    "pre_tool_advisory_context",
    "post_tool_context",
    "subagent_start_context",
    "subagent_stop_context",
    "permission_signal",
    "permission_decision",
    "pre_tool_block",
    "tool_batch_context",
    "post_tool_failure_context",
    "file_change_event",
    "config_change_event",
    "worktree_lifecycle",
    "compact_direction",
    "session_end",
    "task_lifecycle",
    "checkpoint_or_rollback",
    "plan_act_mode",
    "codebase_index",
    "mode_or_role_switch",
    "command_outcome",
    "path_observation",
)
CLINE_SUPPORTED_CHECKS = ("plan_act_mode", "mode_or_role_switch")
CLINE_UNSUPPORTED_CHECKS = tuple(
    check for check in PLACEHOLDER_UNSUPPORTED_CHECKS if check not in set(CLINE_SUPPORTED_CHECKS)
)
ROO_SUPPORTED_CHECKS = ("mode_or_role_switch", "tool_permission_boundary")
ROO_UNSUPPORTED_CHECKS = tuple(
    check for check in PLACEHOLDER_UNSUPPORTED_CHECKS if check != "mode_or_role_switch"
)
OPENHANDS_SUPPORTED_CHECKS = (
    "changed_files",
    "validation_broker",
    "validation_freshness",
    "residual_risk",
    "post_tool_context",
    "post_tool_failure_context",
    "file_change_event",
    "session_end",
    "task_lifecycle",
    "checkpoint_or_rollback",
    "command_outcome",
    "path_observation",
)
OPENHANDS_UNSUPPORTED_CHECKS = tuple(
    check for check in PLACEHOLDER_UNSUPPORTED_CHECKS if check not in set(OPENHANDS_SUPPORTED_CHECKS)
)


@dataclass(frozen=True)
class AdapterCapabilities:
    """Bounded runtime capability facts consumed by downstream policies."""

    adapter_name: str
    supported_events: tuple[str, ...]
    unsupported_events: tuple[str, ...]
    observable_payload_fields: tuple[str, ...]
    advisory_context_events: tuple[str, ...]
    advisory_context_supported: bool
    stop_block_supported: bool
    pre_tool_supported: bool
    post_tool_supported: bool
    subagent_supported: bool
    command_outcome_observable: str
    path_observable: bool
    permission_signal_observable: bool
    degradation_policy: str
    default_gate_modes: tuple[tuple[str, str], ...]
    supported_checks: tuple[str, ...]
    supports_context_injection: bool = False
    supports_pre_tool_block: bool = False
    supports_permission_decision: bool = False
    supports_post_tool_success: bool = False
    supports_post_tool_failure: bool = False
    supports_tool_batch: bool = False
    supports_file_changed_event: bool = False
    supports_config_changed_event: bool = False
    supports_worktree_lifecycle: bool = False
    supports_pre_compact: bool = False
    supports_post_compact: bool = False
    supports_session_end: bool = False
    supports_task_lifecycle: bool = False
    supports_checkpoint_or_rollback: bool = False
    supports_plan_act_mode: bool = False
    supports_codebase_index: bool = False
    supports_mode_or_role_switch: bool = False
    command_output_visibility: str = "none"
    changed_path_visibility: str = "none"
    validation_output_visibility: str = "none"
    unsupported_checks: tuple[str, ...] = field(default_factory=tuple)
    default_failure_mode: str = "fail_open"
    placeholder: bool = False

    @property
    def runtime(self) -> str:
        return self.adapter_name

    @property
    def supports_session_start(self) -> bool:
        return self.supports_event("SessionStart")

    @property
    def supports_user_prompt_submit(self) -> bool:
        return self.supports_event("UserPromptSubmit")

    @property
    def supports_pre_tool_use(self) -> bool:
        return self.supports_event("PreToolUse")

    @property
    def supports_post_tool_use(self) -> bool:
        return self.supports_event("PostToolUse")

    @property
    def supports_stop(self) -> bool:
        return self.supports_event("Stop")

    @property
    def supports_subagent_start(self) -> bool:
        return self.supports_event("SubagentStart")

    @property
    def supports_subagent_stop(self) -> bool:
        return self.supports_event("SubagentStop")

    @property
    def supports_blocking(self) -> bool:
        return self.stop_block_supported

    @property
    def supports_tool_result_inspection(self) -> bool:
        return self.command_output_visibility in {"partial", "full"}

    def supports_event(self, event_name: str) -> bool:
        return _canonical_event_name(event_name) in set(self.supported_events)

    def supports_context_event(self, event_name: str) -> bool:
        if not self.advisory_context_supported:
            return False
        return _canonical_event_name(event_name) in set(self.advisory_context_events)

    def default_gate_mode(self, gate: str) -> str:
        modes = dict(self.default_gate_modes)
        return modes.get(gate, modes.get("default", "warn"))

    def degradation_for_event(self, event_name: str) -> str:
        canonical = _canonical_event_name(event_name)
        if canonical == "Unknown":
            return f"{self.adapter_name}_unknown_event"
        return f"{self.adapter_name}_{_degradation_token(canonical)}_unsupported"

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter_name": self.adapter_name,
            "runtime": self.runtime,
            "supported_events": list(self.supported_events),
            "unsupported_events": list(self.unsupported_events),
            "observable_payload_fields": list(self.observable_payload_fields),
            "advisory_context_events": list(self.advisory_context_events),
            "advisory_context_supported": self.advisory_context_supported,
            "stop_block_supported": self.stop_block_supported,
            "pre_tool_supported": self.pre_tool_supported,
            "post_tool_supported": self.post_tool_supported,
            "subagent_supported": self.subagent_supported,
            "command_outcome_observable": self.command_outcome_observable,
            "path_observable": self.path_observable,
            "permission_signal_observable": self.permission_signal_observable,
            "degradation_policy": self.degradation_policy,
            "default_gate_modes": dict(self.default_gate_modes),
            "supported_checks": list(self.supported_checks),
            "unsupported_checks": list(self.unsupported_checks),
            "default_failure_mode": self.default_failure_mode,
            "placeholder": self.placeholder,
            "supports_context_injection": self.supports_context_injection,
            "supports_pre_tool_block": self.supports_pre_tool_block,
            "supports_permission_decision": self.supports_permission_decision,
            "supports_post_tool_success": self.supports_post_tool_success,
            "supports_post_tool_failure": self.supports_post_tool_failure,
            "supports_tool_batch": self.supports_tool_batch,
            "supports_file_changed_event": self.supports_file_changed_event,
            "supports_config_changed_event": self.supports_config_changed_event,
            "supports_worktree_lifecycle": self.supports_worktree_lifecycle,
            "supports_pre_compact": self.supports_pre_compact,
            "supports_post_compact": self.supports_post_compact,
            "supports_session_end": self.supports_session_end,
            "supports_task_lifecycle": self.supports_task_lifecycle,
            "supports_checkpoint_or_rollback": self.supports_checkpoint_or_rollback,
            "supports_plan_act_mode": self.supports_plan_act_mode,
            "supports_codebase_index": self.supports_codebase_index,
            "supports_mode_or_role_switch": self.supports_mode_or_role_switch,
            "command_output_visibility": self.command_output_visibility,
            "changed_path_visibility": self.changed_path_visibility,
            "validation_output_visibility": self.validation_output_visibility,
            "supports_session_start": self.supports_session_start,
            "supports_user_prompt_submit": self.supports_user_prompt_submit,
            "supports_pre_tool_use": self.supports_pre_tool_use,
            "supports_post_tool_use": self.supports_post_tool_use,
            "supports_stop": self.supports_stop,
            "supports_subagent_start": self.supports_subagent_start,
            "supports_subagent_stop": self.supports_subagent_stop,
            "supports_blocking": self.supports_blocking,
            "supports_tool_result_inspection": self.supports_tool_result_inspection,
        }


@dataclass(frozen=True)
class AdapterEventResult:
    """Normalized event plus the adapter support gate result."""

    normalized_event: NormalizedEvent
    gate_result: GateResult
    capabilities: AdapterCapabilities

    def to_dict(self) -> dict[str, object]:
        return {
            "normalized_event": self.normalized_event.to_json_dict(),
            "gate_result": self.gate_result.to_json_dict(),
            "adapter_capabilities": self.capabilities.to_dict(),
        }


class BaseRuntimeAdapter:
    """Normalize one runtime payload into bounded governance facts."""

    capabilities: AdapterCapabilities

    def __init__(self, capabilities: AdapterCapabilities):
        self.capabilities = capabilities

    def normalize_event(
        self,
        payload: Mapping[str, Any] | None,
        *,
        base_path: str | None = None,
    ) -> AdapterEventResult:
        source = payload if isinstance(payload, Mapping) else {}
        canonical = self.canonical_event_name(source)
        event_id = _event_id(source, canonical, self.capabilities.adapter_name)
        command_kind = self.extract_command_kind(source)
        path_groups = self.extract_path_groups(source, base_path=base_path)
        bounded_paths = self.extract_paths(source, base_path=base_path)
        if not bounded_paths:
            bounded_paths = _aggregate_path_groups(path_groups, base_path=base_path)
        degradation = self.build_degradation(canonical, source)
        validation_signal = self.extract_validation_signal(source)
        checkpoint_signal = self.extract_checkpoint(source)
        stage_signal = self.extract_stage_signal(source, canonical)
        normalized = NormalizedEvent.from_telemetry_fact(
            {
                "event_id": event_id,
                "adapter": self.capabilities.adapter_name,
                "event_name": canonical,
                "tool_name": self.extract_tool_name(source),
                "tool_category": self.classify_tool_category(source),
                "stage_signal": stage_signal,
                "bounded_paths": bounded_paths,
                "read_paths": path_groups.get("read_paths", []),
                "changed_paths": path_groups.get("changed_paths", []),
                "deleted_paths": path_groups.get("deleted_paths", []),
                "generated_paths": path_groups.get("generated_paths", []),
                "command_kind": command_kind,
                "command_risk": self.classify_command_risk(command_kind, source),
                "command_outcome": self.extract_command_outcome(source),
                "timestamp": _first_text(source, "timestamp_utc", "timestamp", "created_at"),
                "source": _event_source(source, canonical),
                "capability_degradation": cap_list(degradation),
                "exit_code": self.extract_exit_code(source),
                "permission_decision": self.extract_permission_decision(source),
                "permission_reason": self.extract_permission_reason(source),
                "privacy_redaction": self.extract_privacy_redaction(source),
                **validation_signal,
                **checkpoint_signal,
            },
            base_path=base_path,
        )
        if normalized.capability_degradation:
            result = GateResult.degraded(
                "executor_adapter",
                f"unsupported runtime event for {self.capabilities.adapter_name}: {canonical}",
                evidence_refs=[normalized.event_id],
                residual_risk=normalized.capability_degradation,
            )
        else:
            result = GateResult.pass_result("executor_adapter", evidence_refs=[normalized.event_id])
        return AdapterEventResult(normalized, result, self.capabilities)

    def advisory_context_for(self, event_name: str, text: str) -> str | None:
        if not text.strip() or not self.capabilities.supports_context_event(event_name):
            return None
        return text.strip()

    def stop_block_allowed(self, *, configured_block: bool) -> bool:
        return bool(configured_block and self.capabilities.stop_block_supported)

    def canonical_event_name(self, payload: Mapping[str, Any]) -> str:
        return _canonical_event_name(_event_name(payload))

    def extract_tool_name(self, payload: Mapping[str, Any]) -> str:
        return _tool_name(payload)

    def classify_tool_category(self, payload: Mapping[str, Any]) -> str | None:
        return _tool_category_from_payload(payload, self.extract_command_kind(payload))

    def extract_paths(
        self,
        payload: Mapping[str, Any],
        *,
        base_path: str | None = None,
    ) -> list[str]:
        return _paths_from_payload(payload, base_path=base_path)

    def extract_path_groups(
        self,
        payload: Mapping[str, Any],
        *,
        base_path: str | None = None,
    ) -> dict[str, list[str]]:
        return {
            "read_paths": [],
            "changed_paths": [],
            "deleted_paths": [],
            "generated_paths": [],
        }

    def extract_command_kind(self, payload: Mapping[str, Any]) -> str | None:
        return _command_kind_from_payload(payload)

    def classify_command_risk(
        self,
        command_kind: str | None,
        payload: Mapping[str, Any],
    ) -> str | None:
        return _classify_command_risk(_raw_command_from_payload(payload), command_kind)

    def extract_command_outcome(self, payload: Mapping[str, Any]) -> str | None:
        return _command_outcome_from_payload(payload, self.extract_exit_code(payload))

    def extract_exit_code(self, payload: Mapping[str, Any]) -> int | None:
        return _exit_code_from_payload(payload)

    def extract_permission_decision(self, payload: Mapping[str, Any]) -> str | None:
        return _permission_decision_from_payload(payload)

    def extract_permission_reason(self, payload: Mapping[str, Any]) -> str | None:
        return _permission_reason_from_payload(payload)

    def extract_checkpoint(self, payload: Mapping[str, Any]) -> dict[str, object]:
        return _checkpoint_from_payload(payload)

    def extract_validation_signal(self, payload: Mapping[str, Any]) -> dict[str, object]:
        return _validation_signal_from_payload(payload)

    def extract_stage_signal(self, payload: Mapping[str, Any], canonical_event: str) -> str | None:
        return "compaction" if _is_compact_session(payload, canonical_event) else None

    def extract_privacy_redaction(self, payload: Mapping[str, Any]) -> list[str]:
        markers: list[str] = []
        for field_name in (
            "prompt",
            "prompt_text",
            "user_prompt",
            "full_command",
            "command_output",
            "stdout",
            "stderr",
        ):
            if _payload_contains_key(payload, field_name):
                markers.append(f"{field_name}:ignored")
        if _raw_command_from_payload(payload):
            markers.append("command:kind_only")
        return cap_list(markers)

    def build_degradation(self, canonical_event: str, payload: Mapping[str, Any]) -> list[str]:
        degradation: list[str] = []
        if canonical_event == "Unknown" or not self.capabilities.supports_event(canonical_event):
            degradation.append(self.capabilities.degradation_for_event(canonical_event))
        if canonical_event in set(self.capabilities.unsupported_events):
            degradation.append(self.capabilities.degradation_for_event(canonical_event))
        return cap_list(degradation)


def adapter_capabilities_for(runtime: str) -> AdapterCapabilities:
    """Return hook-compatible capabilities, with generic fallback."""
    name = _runtime_key(runtime)
    if name in CAPABILITIES_BY_RUNTIME:
        return CAPABILITIES_BY_RUNTIME[name]
    if name in PLACEHOLDER_CAPABILITIES_BY_RUNTIME:
        return PLACEHOLDER_CAPABILITIES_BY_RUNTIME[name]
    return CAPABILITIES_BY_RUNTIME["generic"]


def strict_adapter_capabilities_for(runtime: str) -> AdapterCapabilities:
    """Return explicit capabilities; unknown runtimes degrade instead of generic pass."""
    name = _runtime_key(runtime)
    if name in CAPABILITIES_BY_RUNTIME:
        return CAPABILITIES_BY_RUNTIME[name]
    if name in PLACEHOLDER_CAPABILITIES_BY_RUNTIME:
        return PLACEHOLDER_CAPABILITIES_BY_RUNTIME[name]
    return _placeholder_capabilities(name or "unknown")


def runtime_adapter_for(runtime: str) -> BaseRuntimeAdapter:
    """Return the concrete translator for a runtime, with generic fallback."""
    name = _runtime_key(runtime)
    if name == "codex":
        from .codex import CodexAdapter

        return CodexAdapter()
    if name == "claude":
        from .claude import ClaudeAdapter

        return ClaudeAdapter()
    if name == "copilot":
        from .copilot import CopilotAdapter

        return CopilotAdapter()
    if name == "cline":
        from .cline import ClineAdapter

        return ClineAdapter()
    if name == "roo":
        from .roo import RooAdapter

        return RooAdapter()
    if name == "openhands":
        from .openhands import OpenHandsAdapter

        return OpenHandsAdapter()
    return BaseRuntimeAdapter(adapter_capabilities_for(name))


def unsupported_events_for(runtime: str) -> tuple[str, ...]:
    return adapter_capabilities_for(runtime).unsupported_events


def coverage_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for runtime in (*SUPPORTED_RUNTIMES, *PLACEHOLDER_RUNTIMES):
        capabilities = (
            CAPABILITIES_BY_RUNTIME.get(runtime)
            or PLACEHOLDER_CAPABILITIES_BY_RUNTIME[runtime]
        )
        rows.append(
            {
                "adapter": capabilities.adapter_name,
                "supported_events": list(capabilities.supported_events),
                "unsupported_events": list(capabilities.unsupported_events),
                "advisory_context_supported": capabilities.advisory_context_supported,
                "stop_block_supported": capabilities.stop_block_supported,
                "pre_tool_supported": capabilities.pre_tool_supported,
                "post_tool_supported": capabilities.post_tool_supported,
                "subagent_supported": capabilities.subagent_supported,
                "command_outcome_observable": capabilities.command_outcome_observable,
                "path_observable": capabilities.path_observable,
                "permission_signal_observable": capabilities.permission_signal_observable,
                "degradation_policy": capabilities.degradation_policy,
                "default_gate_modes": dict(capabilities.default_gate_modes),
                "supported_checks": list(capabilities.supported_checks),
                "unsupported_checks": list(capabilities.unsupported_checks),
                "placeholder": capabilities.placeholder,
                "supports_context_injection": capabilities.supports_context_injection,
                "supports_pre_tool_block": capabilities.supports_pre_tool_block,
                "supports_permission_decision": capabilities.supports_permission_decision,
                "supports_post_tool_success": capabilities.supports_post_tool_success,
                "supports_post_tool_failure": capabilities.supports_post_tool_failure,
                "supports_tool_batch": capabilities.supports_tool_batch,
                "supports_file_changed_event": capabilities.supports_file_changed_event,
                "supports_config_changed_event": capabilities.supports_config_changed_event,
                "supports_worktree_lifecycle": capabilities.supports_worktree_lifecycle,
                "supports_pre_compact": capabilities.supports_pre_compact,
                "supports_post_compact": capabilities.supports_post_compact,
                "supports_session_end": capabilities.supports_session_end,
                "supports_task_lifecycle": capabilities.supports_task_lifecycle,
                "supports_checkpoint_or_rollback": capabilities.supports_checkpoint_or_rollback,
                "supports_plan_act_mode": capabilities.supports_plan_act_mode,
                "supports_codebase_index": capabilities.supports_codebase_index,
                "supports_mode_or_role_switch": capabilities.supports_mode_or_role_switch,
                "command_output_visibility": capabilities.command_output_visibility,
                "changed_path_visibility": capabilities.changed_path_visibility,
                "validation_output_visibility": capabilities.validation_output_visibility,
            }
        )
    return rows


def format_coverage_matrix() -> str:
    headers = (
        "adapter",
        "events",
        "unsupported",
        "advisory",
        "stop_block",
        "command_outcome",
        "visibility",
        "default_modes",
        "unsupported_checks",
    )
    lines = ["runtime coverage matrix:", " | ".join(headers)]
    lines.append(" | ".join("---" for _ in headers))
    for row in coverage_matrix():
        modes = row["default_gate_modes"]
        mode_text = ",".join(f"{key}={value}" for key, value in sorted(modes.items()))
        lines.append(
            " | ".join(
                [
                    str(row["adapter"]),
                    ",".join(str(item) for item in row["supported_events"]) or "none",
                    ",".join(str(item) for item in row["unsupported_events"]) or "none",
                    "yes" if row["advisory_context_supported"] else "no",
                    "yes" if row["stop_block_supported"] else "no",
                    str(row["command_outcome_observable"]),
                    (
                        f"command={row['command_output_visibility']},"
                        f"paths={row['changed_path_visibility']},"
                        f"validation={row['validation_output_visibility']}"
                    ),
                    mode_text,
                    ",".join(str(item) for item in row["unsupported_checks"]) or "none",
                ]
            )
        )
    return "\n".join(lines)


def _canonical_event_name(name: object) -> str:
    compact = "".join(ch for ch in str(name or "").strip().casefold() if ch.isalnum())
    aliases = {
        "sessionstart": "SessionStart",
        "userpromptsubmit": "UserPromptSubmit",
        "userpromptexpansion": "UserPromptExpansion",
        "pretooluse": "PreToolUse",
        "permissionrequest": "PermissionRequest",
        "posttooluse": "PostToolUse",
        "posttoolusefailure": "PostToolUseFailure",
        "posttoolbatch": "PostToolBatch",
        "stop": "Stop",
        "stopfailure": "StopFailure",
        "sessionend": "SessionEnd",
        "subagentstart": "SubagentStart",
        "subagentstop": "SubagentStop",
        "taskcreated": "TaskCreated",
        "taskcompleted": "TaskCompleted",
        "filechanged": "FileChanged",
        "configchanged": "ConfigChanged",
        "worktreecreate": "WorktreeCreate",
        "worktreeremove": "WorktreeRemove",
        "precompact": "PreCompact",
        "postcompact": "PostCompact",
        "compact": "Compact",
        "compaction": "Compact",
        "contextcompact": "Compact",
    }
    return aliases.get(compact, "Unknown")


def _visibility(value: object) -> str:
    text = str(value or "").strip().casefold()
    if text in {"none", "partial", "full"}:
        return text
    if text in {"true", "yes", "observable"}:
        return "partial"
    return "none"


def _capabilities(
    adapter_name: str,
    *,
    supported_events: Iterable[str],
    unsupported_events: Iterable[str] = (),
    advisory_context_events: Iterable[str],
    observable_payload_fields: Iterable[str],
    stop_block_supported: bool,
    command_outcome_observable: str,
    path_observable: bool,
    permission_signal_observable: bool,
    default_gate_modes: Mapping[str, str],
    supported_checks: Iterable[str],
    unsupported_checks: Iterable[str] = (),
    placeholder: bool = False,
    supports_checkpoint_or_rollback: bool = False,
    supports_plan_act_mode: bool = False,
    supports_codebase_index: bool = False,
    supports_mode_or_role_switch: bool = False,
    command_output_visibility: str | None = None,
    changed_path_visibility: str | None = None,
    validation_output_visibility: str | None = None,
) -> AdapterCapabilities:
    supported = tuple(
        event
        for event in (_canonical_event_name(item) for item in supported_events)
        if event != "Unknown"
    )
    advisory_events = tuple(
        event
        for event in (_canonical_event_name(item) for item in advisory_context_events)
        if event in set(supported)
    )
    unsupported = tuple(
        cap_list(
            [
                *(
                    event
                    for event in (_canonical_event_name(item) for item in unsupported_events)
                    if event != "Unknown"
                ),
                *(event for event in CANONICAL_EVENTS[:-1] if event not in supported),
            ],
            max_items=len(CANONICAL_EVENTS),
        )
    )
    output_visibility = _visibility(command_output_visibility or command_outcome_observable)
    path_visibility = _visibility(changed_path_visibility or ("partial" if path_observable else "none"))
    validation_visibility = _visibility(validation_output_visibility or output_visibility)
    return AdapterCapabilities(
        adapter_name=adapter_name,
        supported_events=supported,
        unsupported_events=unsupported,
        observable_payload_fields=tuple(observable_payload_fields),
        advisory_context_events=advisory_events,
        advisory_context_supported=bool(advisory_events),
        stop_block_supported=stop_block_supported,
        pre_tool_supported="PreToolUse" in supported,
        post_tool_supported="PostToolUse" in supported or "PostToolBatch" in supported,
        subagent_supported="SubagentStart" in supported or "SubagentStop" in supported,
        command_outcome_observable=command_outcome_observable,
        path_observable=path_observable,
        permission_signal_observable=permission_signal_observable,
        degradation_policy="unsupported_event_or_check_degrades_fail_open",
        default_gate_modes=tuple(sorted(default_gate_modes.items())),
        supported_checks=tuple(supported_checks),
        supports_context_injection=bool(advisory_events),
        supports_pre_tool_block=stop_block_supported
        and bool({"PreToolUse", "PermissionRequest"} & set(supported)),
        supports_permission_decision=permission_signal_observable and "PermissionRequest" in supported,
        supports_post_tool_success="PostToolUse" in supported,
        supports_post_tool_failure="PostToolUseFailure" in supported,
        supports_tool_batch="PostToolBatch" in supported,
        supports_file_changed_event="FileChanged" in supported,
        supports_config_changed_event="ConfigChanged" in supported,
        supports_worktree_lifecycle=bool({"WorktreeCreate", "WorktreeRemove"} & set(supported)),
        supports_pre_compact="PreCompact" in supported,
        supports_post_compact="PostCompact" in supported,
        supports_session_end="SessionEnd" in supported,
        supports_task_lifecycle=bool({"TaskCreated", "TaskCompleted"} & set(supported)),
        supports_checkpoint_or_rollback=supports_checkpoint_or_rollback,
        supports_plan_act_mode=supports_plan_act_mode,
        supports_codebase_index=supports_codebase_index,
        supports_mode_or_role_switch=supports_mode_or_role_switch,
        command_output_visibility=output_visibility,
        changed_path_visibility=path_visibility,
        validation_output_visibility=validation_visibility,
        unsupported_checks=tuple(unsupported_checks),
        placeholder=placeholder,
    )


CAPABILITIES_BY_RUNTIME = {
    "codex": _capabilities(
        "codex",
        supported_events=(
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PermissionRequest",
            "PostToolUse",
            "Stop",
            "SubagentStart",
            "SubagentStop",
            "Compact",
        ),
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["codex"],
        observable_payload_fields=(
            "hook_event_name",
            "tool_name",
            "tool_input",
            "cwd",
            "session_id",
            "source",
        ),
        stop_block_supported=True,
        command_outcome_observable="partial",
        path_observable=True,
        permission_signal_observable=True,
        command_output_visibility="partial",
        changed_path_visibility="partial",
        validation_output_visibility="partial",
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=CODEX_SUPPORTED_CHECKS,
        unsupported_checks=RICH_UNSUPPORTED_CHECKS,
    ),
    "claude": _capabilities(
        "claude",
        supported_events=(
            "SessionStart",
            "UserPromptSubmit",
            "UserPromptExpansion",
            "PreToolUse",
            "PermissionRequest",
            "PostToolUse",
            "PostToolUseFailure",
            "PostToolBatch",
            "Stop",
            "StopFailure",
            "SessionEnd",
            "SubagentStart",
            "SubagentStop",
            "TaskCreated",
            "TaskCompleted",
            "FileChanged",
            "ConfigChanged",
            "PreCompact",
            "PostCompact",
            "Compact",
        ),
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["claude"],
        observable_payload_fields=(
            "hookEventName",
            "hook_event_name",
            "toolName",
            "tool_name",
            "toolInput",
            "tool_input",
            "cwd",
            "sessionId",
            "source",
        ),
        stop_block_supported=True,
        command_outcome_observable="partial",
        path_observable=True,
        permission_signal_observable=True,
        command_output_visibility="partial",
        changed_path_visibility="partial",
        validation_output_visibility="partial",
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=CLAUDE_SUPPORTED_CHECKS,
        unsupported_checks=CLAUDE_UNSUPPORTED_CHECKS,
    ),
    "copilot": _capabilities(
        "copilot",
        supported_events=("SessionStart", "PostToolUse", "Stop", "SubagentStart"),
        unsupported_events=COPILOT_UNSUPPORTED_ADVISORY_EVENTS,
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["copilot"],
        observable_payload_fields=(
            "hook_event_name",
            "eventName",
            "tool_name",
            "toolName",
            "tool_input",
            "toolInput",
            "cwd",
            "transcript_path",
            "transcriptPath",
        ),
        stop_block_supported=True,
        command_outcome_observable="partial",
        path_observable=True,
        permission_signal_observable=False,
        command_output_visibility="partial",
        changed_path_visibility="partial",
        validation_output_visibility="partial",
        default_gate_modes={"default": "warn", "stop": "block"},
        supported_checks=COPILOT_SUPPORTED_CHECKS,
        unsupported_checks=COPILOT_UNSUPPORTED_CHECKS,
    ),
    "cline": _capabilities(
        "cline",
        supported_events=(),
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["cline"],
        observable_payload_fields=(
            "mode",
            "cline_mode",
            "stage",
            "changeforge_stage",
            "task_type",
            "tool_name",
            "tool_input",
        ),
        stop_block_supported=False,
        command_outcome_observable="none",
        path_observable=False,
        permission_signal_observable=False,
        command_output_visibility="none",
        changed_path_visibility="none",
        validation_output_visibility="none",
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=CLINE_SUPPORTED_CHECKS,
        unsupported_checks=CLINE_UNSUPPORTED_CHECKS,
        supports_plan_act_mode=True,
        supports_mode_or_role_switch=True,
    ),
    "roo": _capabilities(
        "roo",
        supported_events=(),
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["roo"],
        observable_payload_fields=(
            "mode",
            "roo_mode",
            "role",
            "stage",
            "task_type",
            "tool_name",
            "tool_input",
        ),
        stop_block_supported=False,
        command_outcome_observable="none",
        path_observable=False,
        permission_signal_observable=False,
        command_output_visibility="none",
        changed_path_visibility="none",
        validation_output_visibility="none",
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=ROO_SUPPORTED_CHECKS,
        unsupported_checks=ROO_UNSUPPORTED_CHECKS,
        supports_mode_or_role_switch=True,
    ),
    "openhands": _capabilities(
        "openhands",
        supported_events=(
            "SessionStart",
            "SessionEnd",
            "TaskCreated",
            "TaskCompleted",
            "PostToolUse",
            "PostToolUseFailure",
            "FileChanged",
            "Stop",
        ),
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["openhands"],
        observable_payload_fields=(
            "event_type",
            "event_name",
            "tool_name",
            "tool_input",
            "action",
            "path",
            "paths",
            "changed_paths",
            "deleted_paths",
            "generated_paths",
            "command",
            "exit_code",
            "outcome",
            "validation_outcome",
            "checkpoint_id",
            "rollback_available",
        ),
        stop_block_supported=False,
        command_outcome_observable="partial",
        path_observable=True,
        permission_signal_observable=False,
        command_output_visibility="partial",
        changed_path_visibility="full",
        validation_output_visibility="partial",
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=OPENHANDS_SUPPORTED_CHECKS,
        unsupported_checks=OPENHANDS_UNSUPPORTED_CHECKS,
        supports_checkpoint_or_rollback=True,
    ),
    "generic": _capabilities(
        "generic",
        supported_events=("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"),
        advisory_context_events=CONTEXT_EVENTS_BY_RUNTIME["generic"],
        observable_payload_fields=("event_name", "tool_name", "tool_input", "cwd"),
        stop_block_supported=False,
        command_outcome_observable="none",
        path_observable=True,
        permission_signal_observable=False,
        command_output_visibility="none",
        changed_path_visibility="partial",
        validation_output_visibility="none",
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=("route_manifest", "changed_files", "validation_broker", "residual_risk"),
        unsupported_checks=GENERIC_UNSUPPORTED_CHECKS,
    ),
}


def _placeholder_capabilities(runtime: str) -> AdapterCapabilities:
    return _capabilities(
        _runtime_key(runtime) or "unknown",
        supported_events=(),
        unsupported_events=CANONICAL_EVENTS[:-1],
        advisory_context_events=(),
        observable_payload_fields=(),
        stop_block_supported=False,
        command_outcome_observable="none",
        path_observable=False,
        permission_signal_observable=False,
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=(),
        unsupported_checks=PLACEHOLDER_UNSUPPORTED_CHECKS,
        placeholder=True,
    )


def _runtime_key(runtime: object) -> str:
    return str(runtime or "").strip().casefold().replace("_", "-")


PLACEHOLDER_CAPABILITIES_BY_RUNTIME = {
    runtime: _placeholder_capabilities(runtime) for runtime in PLACEHOLDER_RUNTIMES
}


def _event_name(payload: Mapping[str, Any]) -> str:
    for key in ("hook_event_name", "hookEventName", "event_name", "eventName", "event"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _event_source(payload: Mapping[str, Any], canonical: str) -> str | None:
    for key in ("source", "reason", "matcher"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return redact_sensitive_value(value)[:120]
    return "compact" if canonical == "Compact" else None


def _is_compact_session(payload: Mapping[str, Any], canonical: str) -> bool:
    if canonical == "Compact":
        return True
    if canonical != "SessionStart":
        return False
    source = " ".join(
        str(payload.get(key) or "") for key in ("source", "reason", "matcher")
    ).casefold()
    return "compact" in source


def _tool_name(payload: Mapping[str, Any]) -> str:
    for key in ("tool_name", "toolName", "name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:120]
    tool = payload.get("tool")
    if isinstance(tool, Mapping):
        value = tool.get("name")
        if isinstance(value, str) and value.strip():
            return value.strip()[:120]
    return ""


def _command_kind_from_payload(payload: Mapping[str, Any]) -> str:
    return sanitize_command_kind(_raw_command_from_payload(payload)) or ""


def _exit_code_from_payload(payload: Mapping[str, Any]) -> int | None:
    for container in _candidate_mappings(payload):
        for key in ("exit_code", "exitCode", "returncode", "return_code", "status_code"):
            value = container.get(key)
            if isinstance(value, bool) or value is None:
                continue
            if isinstance(value, int):
                return value
            try:
                return int(str(value).strip())
            except ValueError:
                continue
    return None


def _permission_decision_from_payload(payload: Mapping[str, Any]) -> str | None:
    aliases = {
        "allow": "allow",
        "allowed": "allow",
        "approve": "allow",
        "approved": "allow",
        "deny": "deny",
        "denied": "deny",
        "reject": "deny",
        "rejected": "deny",
        "block": "deny",
        "blocked": "deny",
        "ask": "ask",
        "prompt": "ask",
    }
    for container in _candidate_mappings(payload):
        for key in ("permission_decision", "permissionDecision", "decision"):
            value = container.get(key)
            text = str(value or "").strip().casefold()
            if text in aliases:
                return aliases[text]
    return None


def _permission_reason_from_payload(payload: Mapping[str, Any]) -> str | None:
    for container in _candidate_mappings(payload):
        for key in (
            "permission_reason",
            "permissionReason",
            "denial_reason",
            "denialReason",
            "reason",
            "message",
        ):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                reason = redact_sensitive_value(value)
                return reason if reason else None
    return None


def _tool_category_from_payload(
    payload: Mapping[str, Any],
    command_kind: str | None,
) -> str:
    tool = _compact_token(_tool_name(payload))
    command = str(command_kind or "").casefold()
    if tool in _READ_TOOLS or command in _READ_COMMANDS:
        return "read"
    if tool in _EDIT_TOOLS:
        return "edit"
    if tool in _MCP_TOOLS:
        return "mcp"
    if command == "git":
        return "git"
    if command in _NETWORK_COMMANDS:
        return "network"
    if is_validation_command(_raw_command_from_payload(payload), command_kind):
        return "test"
    if tool in {"bash", "shell", "terminal", "runterminalcommand"} or command:
        return "bash"
    return "unknown"


def is_validation_command(raw_command: object, command_kind: str | None = None) -> bool:
    """Return whether a shell command is validation evidence without storing raw output."""
    command = str(raw_command or "").strip()
    tokens = _command_tokens(command)
    program = _program_token(command_kind or (tokens[0] if tokens else "") or sanitize_command_kind(command))
    if not command and not program:
        return False
    if program in _TEST_COMMANDS:
        return True
    if program in {"python", "python3", "py"} and len(tokens) >= 3:
        module = _program_token(tokens[2])
        if tokens[1] == "-m" and module in {"unittest", "pytest"}:
            return True
    if program == "go" and len(tokens) >= 2 and tokens[1] == "test":
        return True
    if program == "cargo" and len(tokens) >= 2 and tokens[1] == "test":
        return True
    if program in {"npm", "pnpm", "yarn"} and any(token == "test" for token in tokens[1:4]):
        return True
    if _looks_like_validation_script(program):
        return True
    if any(_looks_like_validation_script(token) for token in tokens):
        return True
    raw = f" {command.casefold()} "
    return any(token in raw for token in _TEST_COMMAND_TOKENS)


def _raw_command_from_payload(payload: Mapping[str, Any]) -> str:
    for container in _candidate_mappings(payload):
        for key in ("command", "cmd", "bash", "script"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _classify_command_risk(command: str, command_kind: str | None) -> str | None:
    text = f" {command.strip().casefold()} "
    program = str(command_kind or sanitize_command_kind(command) or "").casefold()
    tokens = _command_tokens(command)
    if not text.strip() and not program:
        return None
    if _is_destructive_command(program, tokens, text):
        return "destructive"
    if _is_release_command(program, tokens, text):
        return "release"
    if _is_migration_command(program, tokens, text):
        return "migration"
    if _is_dependency_mutation(program, tokens, text):
        return "dependency"
    if program in _NETWORK_COMMANDS:
        return "network"
    if _is_mutation_command(program, tokens, text):
        return "mutation"
    if _is_safe_read_command(program, tokens):
        return "safe"
    return "safe" if program else None


def _command_outcome_from_payload(
    payload: Mapping[str, Any],
    exit_code: int | None,
) -> str | None:
    aliases = {
        "pass": "pass",
        "passed": "pass",
        "success": "pass",
        "succeeded": "pass",
        "ok": "pass",
        "complete": "pass",
        "completed": "pass",
        "fail": "fail",
        "failed": "fail",
        "failure": "fail",
        "error": "fail",
        "errored": "fail",
        "timeout": "timeout",
        "timedout": "timeout",
        "timed_out": "timeout",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "unknown": "unknown",
        "notobservable": "not_observable",
        "not_observable": "not_observable",
    }
    for container in _candidate_mappings(payload):
        for key in ("command_outcome", "commandOutcome", "outcome", "status", "state", "result"):
            value = container.get(key)
            if isinstance(value, bool):
                return "pass" if value else "fail"
            text = str(value or "").strip().casefold().replace("-", "_")
            compact = text.replace("_", "")
            if text in aliases:
                return aliases[text]
            if compact in aliases:
                return aliases[compact]
        for key in ("success", "succeeded", "ok", "is_success", "isSuccess"):
            if key in container:
                return "pass" if _truthy(container.get(key)) else "fail"
        for key in ("is_error", "isError", "error"):
            if key in container and _truthy(container.get(key)):
                return "fail"
    if exit_code is None:
        return None
    return "pass" if exit_code == 0 else "fail"


def _checkpoint_from_payload(payload: Mapping[str, Any]) -> dict[str, object]:
    data: dict[str, object] = {}
    for container in _candidate_mappings(payload):
        for key in ("checkpoint_id", "checkpointId", "checkpoint"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                data["checkpoint_id"] = redact_sensitive_value(value)
                break
        rollback = _first_present(container, "rollback_available", "rollbackAvailable")
        if rollback is not None:
            data["rollback_available"] = _truthy(rollback)
    return data


def _validation_signal_from_payload(payload: Mapping[str, Any]) -> dict[str, object]:
    data: dict[str, object] = {}
    for container in _candidate_mappings(payload):
        candidate = _first_present(container, "validation_candidate", "validationCandidate")
        if candidate is not None:
            data["validation_candidate"] = _truthy(candidate)
        outcome = _normalize_validation_outcome(
            _first_present(container, "validation_outcome", "validationOutcome", "validation_result")
        )
        if outcome:
            data["validation_outcome"] = outcome
        freshness = _normalize_validation_freshness(
            _first_present(container, "validation_freshness", "validationFreshness")
        )
        if freshness:
            data["validation_freshness"] = freshness
        fresh_after_edit = _first_present(
            container,
            "validation_result_fresh_after_last_edit",
            "validationResultFreshAfterLastEdit",
        )
        if fresh_after_edit is not None and "validation_freshness" not in data:
            data["validation_freshness"] = "current" if _truthy(fresh_after_edit) else "stale"
    return data


def _payload_contains_key(payload: Mapping[str, Any], field_name: str) -> bool:
    for key, value in payload.items():
        if str(key) == field_name:
            return True
        if isinstance(value, Mapping) and _payload_contains_key(value, field_name):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and _payload_contains_key(item, field_name):
                    return True
    return False


def _aggregate_path_groups(
    path_groups: Mapping[str, Iterable[object]],
    *,
    base_path: str | None,
) -> list[str]:
    paths: list[object] = []
    for key in ("read_paths", "changed_paths", "deleted_paths", "generated_paths"):
        paths.extend(path_groups.get(key, []))
    return cap_list(paths, item_sanitizer=lambda item: normalize_relative_path(item, base=base_path))


def _paths_from_payload(payload: Mapping[str, Any], *, base_path: str | None) -> list[str]:
    paths: list[object] = []
    path_keys = {
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
    excluded = {"cwd", "root", "repo", "repository", "project", "transcript_path", "transcriptPath"}

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                child_name = str(child_key)
                if child_name in excluded:
                    continue
                if child_name in path_keys:
                    collect(child)
                else:
                    visit(child, child_name)
            return
        if isinstance(value, list):
            for item in value:
                visit(item, key)
            return
        if isinstance(value, str) and ("*** Begin Patch" in value or "diff --git" in value):
            paths.extend(_extract_paths_from_patch_text(value))

    def collect(value: Any) -> None:
        if isinstance(value, str):
            paths.append(value)
            return
        if isinstance(value, list):
            for item in value:
                collect(item)
            return
        if isinstance(value, Mapping):
            visit(value)

    visit(payload)
    return cap_list(paths, item_sanitizer=lambda item: normalize_relative_path(item, base=base_path))


def _candidate_mappings(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    mappings: list[Mapping[str, Any]] = [payload]
    for key in (
        "tool_input",
        "toolInput",
        "input",
        "arguments",
        "parameters",
        "params",
        "result",
        "tool_result",
        "toolResult",
        "output",
    ):
        value = payload.get(key)
        if isinstance(value, Mapping):
            mappings.append(value)
    return mappings


def _extract_paths_from_patch_text(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        patch_match = _PATCH_FILE_RE.match(line.strip())
        if patch_match:
            paths.append(patch_match.group(1).strip())
            continue
        diff_match = _DIFF_GIT_RE.match(line.strip())
        if diff_match:
            paths.append(diff_match.group(2).strip())
            continue
        file_match = _DIFF_FILE_RE.match(line.strip())
        if file_match:
            path = file_match.group(1).strip()
            if path != "/dev/null":
                paths.append(path)
    return paths


def _first_present(payload: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload.get(key)
    return None


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().casefold()
    return text in {"1", "true", "yes", "y", "allow", "allowed", "approved", "pass", "passed", "success", "ok"}


def _normalize_validation_outcome(value: object) -> str | None:
    text = str(value or "").strip().casefold().replace("-", "_")
    aliases = {
        "pass": "pass",
        "passed": "pass",
        "success": "pass",
        "succeeded": "pass",
        "fail": "fail",
        "failed": "fail",
        "failure": "fail",
        "notrun": "not_run",
        "not_run": "not_run",
        "notverified": "not_verified",
        "not_verified": "not_verified",
        "stale": "stale",
        "partial": "partial",
        "unknown": "unknown",
    }
    return aliases.get(text.replace("_", "")) or aliases.get(text)


def _normalize_validation_freshness(value: object) -> str | None:
    text = str(value or "").strip().casefold().replace("-", "_")
    aliases = {
        "fresh": "current",
        "current": "current",
        "stale": "stale",
        "unknown": "unknown",
        "notapplicable": "not_applicable",
        "not_applicable": "not_applicable",
    }
    return aliases.get(text.replace("_", "")) or aliases.get(text)


def _command_tokens(command: str) -> list[str]:
    if not command.strip():
        return []
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    cleaned: list[str] = []
    for token in tokens:
        stripped = token.strip().casefold()
        if not stripped or "=" in stripped and re.match(r"^[a-z_][a-z0-9_]*=", stripped):
            continue
        cleaned.append(stripped)
    return cleaned


def _program_token(value: object) -> str:
    token = str(value or "").strip().casefold()
    while token.startswith("./"):
        token = token[2:]
    return token.rsplit("/", 1)[-1]


def _looks_like_validation_script(value: object) -> bool:
    token = str(value or "").strip().casefold()
    while token.startswith("./"):
        token = token[2:]
    basename = token.rsplit("/", 1)[-1]
    return basename.startswith("validate-") or basename.startswith("eval-")


def _is_safe_read_command(program: str, tokens: list[str]) -> bool:
    if program in {"cat", "rg", "grep", "find", "ls", "pwd", "head", "tail", "wc"}:
        return True
    if program == "sed":
        return len(tokens) > 1 and tokens[1].startswith("-n")
    if program == "git" and len(tokens) > 1 and tokens[1] in {"diff", "status", "show", "log"}:
        return True
    return program in _TEST_COMMANDS


def _is_destructive_command(program: str, tokens: list[str], text: str) -> bool:
    if program in {"rm", "rmdir"}:
        return True
    if program == "git" and len(tokens) > 1:
        if tokens[1] in {"reset", "clean", "checkout", "rebase"}:
            return True
        if tokens[1] == "push" and any(token in {"--force", "-f", "--force-with-lease"} for token in tokens):
            return True
    return any(token in text for token in (" reset --hard ", " clean -fd", " --force ", " delete "))


def _is_release_command(program: str, tokens: list[str], text: str) -> bool:
    if program in {"kubectl", "helm"}:
        return True
    if program == "terraform" and "apply" in tokens[1:3]:
        return True
    if any("deploy" in token or "release" in token for token in tokens[1:]):
        return True
    return any(token in text for token in (" deploy", " release", " publish", " upload", " rollout "))


def _is_migration_command(program: str, tokens: list[str], text: str) -> bool:
    if program in {"alembic", "liquibase", "flyway"}:
        return True
    if program in {"psql", "mysql"} and "migration" in text:
        return True
    return any(token in text for token in (" migrate", " migration", " migrations/", " db/migrate"))


def _is_dependency_mutation(program: str, tokens: list[str], text: str) -> bool:
    if program in {"npm", "pnpm", "yarn"} and any(token in tokens[1:3] for token in {"install", "add", "update", "upgrade", "remove"}):
        return True
    if program in {"pip", "pip3"} and any(token in tokens[1:3] for token in {"install", "uninstall"}):
        return True
    if program in {"poetry", "uv", "cargo", "go", "bundle", "gem"} and any(
        token in tokens[1:4] for token in {"add", "install", "update", "remove", "get"}
    ):
        return True
    return any(token in text for token in (" package-lock.json", " pnpm-lock.yaml", " yarn.lock"))


def _is_mutation_command(program: str, tokens: list[str], text: str) -> bool:
    if program in {"mv", "cp", "chmod", "chown", "touch", "mkdir", "python", "python3", "node"} and any(
        token in text for token in (" write", " edit", " generate", " format", " lint --fix", " apply_patch")
    ):
        return True
    if program in {"apply_patch", "patch"}:
        return True
    if program == "git" and len(tokens) > 1 and tokens[1] in {"add", "commit", "stash", "merge", "cherry-pick"}:
        return True
    return any(token in text for token in (" apply_patch", " write ", " edit ", " format ", " lint --fix"))


def _compact_token(value: object) -> str:
    return "".join(ch for ch in str(value or "").strip().casefold() if ch.isalnum() or ch == "_")


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _event_id(payload: Mapping[str, Any], canonical: str, adapter: str) -> str:
    explicit = _first_text(payload, "event_id", "eventId")
    if explicit:
        return explicit[:120]
    parts = [
        adapter,
        canonical,
        _first_text(payload, "session_id", "sessionId", "turn_id", "turnId"),
        _first_text(payload, "timestamp_utc", "timestamp", "created_at"),
        ",".join(_paths_from_payload(payload, base_path=None)[:5]),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"adapter-event-{digest}"


def _degradation_token(event_name: str) -> str:
    chars: list[str] = []
    for char in event_name:
        if char.isupper() and chars:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars).replace("__", "_")


__all__ = [
    "AdapterCapabilities",
    "AdapterEventResult",
    "BaseRuntimeAdapter",
    "CAPABILITIES_BY_RUNTIME",
    "CANONICAL_EVENTS",
    "CONTEXT_EVENTS_BY_RUNTIME",
    "COPILOT_UNSUPPORTED_ADVISORY_EVENTS",
    "EVENT_SUPPORT_FIELDS",
    "PLACEHOLDER_CAPABILITIES_BY_RUNTIME",
    "PLACEHOLDER_RUNTIMES",
    "SUPPORTED_RUNTIMES",
    "adapter_capabilities_for",
    "coverage_matrix",
    "format_coverage_matrix",
    "is_validation_command",
    "runtime_adapter_for",
    "strict_adapter_capabilities_for",
    "unsupported_events_for",
]
