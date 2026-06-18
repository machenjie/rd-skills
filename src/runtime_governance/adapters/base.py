"""Canonical executor adapter protocol for ChangeForge runtimes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..events import EventKind, NormalizedEvent
from ..gates import GateResult
from ..privacy import cap_list, normalize_relative_path, sanitize_command_kind


CANONICAL_EVENTS = (
    "SessionStart",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolBatch",
    "Stop",
    "SubagentStart",
    "SubagentStop",
    "Compact",
    "Unknown",
)

EVENT_SUPPORT_FIELDS = {
    "SessionStart": "supports_session_start",
    "UserPromptSubmit": "supports_user_prompt_submit",
    "UserPromptExpansion": "supports_user_prompt_submit",
    "PreToolUse": "supports_pre_tool_use",
    "PostToolUse": "supports_post_tool_use",
    "PostToolBatch": "supports_post_tool_use",
    "Stop": "supports_stop",
    "SubagentStart": "supports_subagent_start",
    "SubagentStop": "supports_subagent_stop",
    "PermissionRequest": "supports_permission_decision",
    "Compact": "supports_session_start",
}

EVENT_KIND_BY_CANONICAL = {
    "SessionStart": EventKind.SESSION_START.value,
    "UserPromptSubmit": EventKind.USER_PROMPT_SUBMIT.value,
    "UserPromptExpansion": EventKind.USER_PROMPT_SUBMIT.value,
    "PreToolUse": EventKind.PRE_TOOL_USE.value,
    "PermissionRequest": EventKind.PRE_TOOL_USE.value,
    "PostToolUse": EventKind.POST_TOOL_USE.value,
    "PostToolBatch": EventKind.POST_TOOL_USE.value,
    "Stop": EventKind.STOP.value,
    "SubagentStart": EventKind.SUBAGENT_START.value,
    "SubagentStop": EventKind.SUBAGENT_STOP.value,
    "Compact": EventKind.COMPACT.value,
    "Unknown": EventKind.UNKNOWN.value,
}

CONTEXT_EVENTS_BY_RUNTIME = {
    "codex": {
        "SessionStart",
        "UserPromptSubmit",
        "UserPromptExpansion",
        "PreToolUse",
        "PostToolUse",
        "PostToolBatch",
        "SubagentStart",
        "SubagentStop",
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
    },
    "copilot": {"SessionStart", "PostToolUse", "SubagentStart", "Notification"},
    "generic": {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse"},
}

SUPPORTED_RUNTIMES = ("codex", "claude", "copilot", "generic")
PLACEHOLDER_RUNTIMES = ("cline", "openhands", "gemini-cli", "goose")
COPILOT_UNSUPPORTED_ADVISORY_EVENTS = ("UserPromptSubmit", "PreToolUse", "SubagentStop")

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
)
GENERIC_UNSUPPORTED_CHECKS = (
    "stop_block",
    "subagent_start_context",
    "subagent_stop_context",
    "permission_signal",
    "command_outcome",
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
    def supports_permission_decision(self) -> bool:
        return self.permission_signal_observable and self.supports_event("PermissionRequest")

    @property
    def supports_blocking(self) -> bool:
        return self.stop_block_supported

    @property
    def supports_context_injection(self) -> bool:
        return self.advisory_context_supported

    @property
    def supports_tool_result_inspection(self) -> bool:
        return self.command_outcome_observable in {"partial", "full"}

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
            "supports_session_start": self.supports_session_start,
            "supports_user_prompt_submit": self.supports_user_prompt_submit,
            "supports_pre_tool_use": self.supports_pre_tool_use,
            "supports_post_tool_use": self.supports_post_tool_use,
            "supports_stop": self.supports_stop,
            "supports_subagent_start": self.supports_subagent_start,
            "supports_subagent_stop": self.supports_subagent_stop,
            "supports_permission_decision": self.supports_permission_decision,
            "supports_blocking": self.supports_blocking,
            "supports_context_injection": self.supports_context_injection,
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
        canonical = _canonical_event_name(_event_name(source))
        event_kind = EVENT_KIND_BY_CANONICAL.get(canonical, EventKind.UNKNOWN.value)
        event_id = _event_id(source, canonical, self.capabilities.adapter_name)
        command_kind = _command_kind_from_payload(source)
        bounded_paths = _paths_from_payload(source, base_path=base_path)
        degradation: list[str] = []
        if canonical == "Unknown" or not self.capabilities.supports_event(canonical):
            degradation.append(self.capabilities.degradation_for_event(canonical))
        if canonical in set(self.capabilities.unsupported_events):
            degradation.append(self.capabilities.degradation_for_event(canonical))
        stage_signal = "compaction" if _is_compact_session(source, canonical) else None
        normalized = NormalizedEvent(
            event_id=event_id,
            adapter=self.capabilities.adapter_name,
            event_kind=event_kind,
            action_type=_tool_name(source) or None,
            stage_signal=stage_signal,
            bounded_paths=bounded_paths,
            command_kind=command_kind or None,
            timestamp=_first_text(source, "timestamp_utc", "timestamp", "created_at") or None,
            source=_event_source(source, canonical),
            capability_degradation=cap_list(degradation),
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
                    mode_text,
                    ",".join(str(item) for item in row["unsupported_checks"]) or "none",
                ]
            )
        )
    return "\n".join(lines)


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
) -> AdapterCapabilities:
    supported = tuple(supported_events)
    return AdapterCapabilities(
        adapter_name=adapter_name,
        supported_events=supported,
        unsupported_events=tuple(unsupported_events),
        observable_payload_fields=tuple(observable_payload_fields),
        advisory_context_events=tuple(advisory_context_events),
        advisory_context_supported=bool(tuple(advisory_context_events)),
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
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=RICH_SUPPORTED_CHECKS,
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
            "PostToolBatch",
            "Stop",
            "SubagentStart",
            "SubagentStop",
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
        default_gate_modes={"default": "warn", "stop": "warn"},
        supported_checks=RICH_SUPPORTED_CHECKS,
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
        default_gate_modes={"default": "warn", "stop": "block"},
        supported_checks=COPILOT_SUPPORTED_CHECKS,
        unsupported_checks=COPILOT_UNSUPPORTED_CHECKS,
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
        unsupported_checks=(
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
            "command_outcome",
            "path_observation",
        ),
        placeholder=True,
    )


def _canonical_event_name(name: object) -> str:
    compact = "".join(ch for ch in str(name or "").strip().casefold() if ch.isalnum())
    aliases = {
        "sessionstart": "SessionStart",
        "userpromptsubmit": "UserPromptSubmit",
        "userpromptexpansion": "UserPromptExpansion",
        "pretooluse": "PreToolUse",
        "permissionrequest": "PermissionRequest",
        "posttooluse": "PostToolUse",
        "posttoolbatch": "PostToolBatch",
        "stop": "Stop",
        "subagentstart": "SubagentStart",
        "subagentstop": "SubagentStop",
        "compact": "Compact",
        "compaction": "Compact",
        "contextcompact": "Compact",
        "notification": "Notification",
    }
    return aliases.get(compact, "Unknown")


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
            return value.strip()[:120]
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
    for container in _candidate_mappings(payload):
        for key in ("command", "cmd", "bash", "script"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return sanitize_command_kind(value)
    return ""


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
    for key in ("tool_input", "toolInput", "input", "arguments", "parameters", "params"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            mappings.append(value)
    return mappings


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
    "strict_adapter_capabilities_for",
    "unsupported_events_for",
]
