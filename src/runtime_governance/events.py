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
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    STOP = "stop"
    SUBAGENT_START = "subagent_start"
    SUBAGENT_STOP = "subagent_stop"
    COMPACT = "compact"
    UNKNOWN = "unknown"


_EVENT_KIND_ALIASES = {
    "sessionstart": EventKind.SESSION_START,
    "session_start": EventKind.SESSION_START,
    "userpromptsubmit": EventKind.USER_PROMPT_SUBMIT,
    "user_prompt_submit": EventKind.USER_PROMPT_SUBMIT,
    "pretooluse": EventKind.PRE_TOOL_USE,
    "pre_tool_use": EventKind.PRE_TOOL_USE,
    "permissionrequest": EventKind.PRE_TOOL_USE,
    "permission_request": EventKind.PRE_TOOL_USE,
    "posttooluse": EventKind.POST_TOOL_USE,
    "post_tool_use": EventKind.POST_TOOL_USE,
    "stop": EventKind.STOP,
    "subagentstart": EventKind.SUBAGENT_START,
    "subagent_start": EventKind.SUBAGENT_START,
    "subagentstop": EventKind.SUBAGENT_STOP,
    "subagent_stop": EventKind.SUBAGENT_STOP,
    "compact": EventKind.COMPACT,
}


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

    @classmethod
    def from_telemetry_fact(cls, fact: Mapping[str, Any], *, base_path: str | None = None) -> "NormalizedEvent":
        """Build a normalized event from existing hook telemetry fields."""
        raw_event = _first_text(fact, "event_kind", "event_name", "hook_event_name", "event_type")
        event_kind = _event_kind(raw_event)
        degradation = cap_list(fact.get("capability_degradation") or fact.get("adapter_degradation") or [])
        if event_kind == EventKind.UNKNOWN.value:
            detail = f"unsupported_event:{redact_sensitive_value(raw_event) or 'missing'}"
            degradation = cap_list([*degradation, detail])

        paths: list[object] = []
        for field_name in (
            "bounded_paths",
            "changed_paths",
            "added_paths",
            "read_paths",
            "validation_result_covered_paths",
        ):
            value = fact.get(field_name)
            if isinstance(value, (list, tuple, set)):
                paths.extend(value)
            elif value:
                paths.append(value)

        command = (
            fact.get("command_kind")
            or fact.get("command_program")
            or fact.get("command")
            or fact.get("tool_command")
        )
        return cls(
            event_id=redact_sensitive_value(fact.get("event_id")) or _event_id(fact),
            adapter=redact_sensitive_value(fact.get("adapter") or fact.get("runtime") or "unknown"),
            event_kind=event_kind,
            action_type=_optional_fact(fact.get("action_type") or fact.get("hook_name") or fact.get("tool_name")),
            stage_signal=_optional_fact(
                fact.get("stage_signal") or fact.get("turn_stage") or fact.get("manifest_current_stage")
            ),
            bounded_paths=cap_list(
                paths,
                item_sanitizer=lambda value: normalize_relative_path(value, base=base_path),
            ),
            command_kind=sanitize_command_kind(command),
            timestamp=_optional_fact(fact.get("timestamp") or fact.get("timestamp_utc")),
            source=_optional_fact(fact.get("source") or fact.get("hook_name") or fact.get("_source")),
            capability_degradation=degradation,
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


def _optional_fact(value: object) -> str | None:
    text = redact_sensitive_value(value)
    return text or None


def _maybe_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _event_id(fact: Mapping[str, Any]) -> str:
    parts = [
        str(fact.get("session_id") or ""),
        str(fact.get("timestamp_utc") or fact.get("timestamp") or ""),
        str(fact.get("event_name") or fact.get("event_kind") or fact.get("hook_name") or ""),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"event-{digest}"
