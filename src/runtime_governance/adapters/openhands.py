"""OpenHands executor backend event adapter."""

from __future__ import annotations

from typing import Any, Mapping

from ..privacy import cap_list, normalize_relative_path
from .base import (
    BaseRuntimeAdapter,
    adapter_capabilities_for,
    _aggregate_path_groups,
    _canonical_event_name,
    _classify_command_risk,
    _compact_token,
    _paths_from_payload,
)


_OPENHANDS_EVENT_ALIASES = {
    "sandboxsessionstart": "SessionStart",
    "sessionstart": "SessionStart",
    "sessionstarted": "SessionStart",
    "taskcreated": "TaskCreated",
    "taskstarted": "TaskCreated",
    "taskcompleted": "TaskCompleted",
    "taskfinished": "TaskCompleted",
    "filechanged": "FileChanged",
    "filechange": "FileChanged",
    "filewrite": "FileChanged",
    "filewritten": "FileChanged",
    "filedelete": "FileChanged",
    "filedeleted": "FileChanged",
    "shellcommand": "PostToolUse",
    "command": "PostToolUse",
    "testcommand": "PostToolUse",
    "browseraction": "PostToolUse",
    "networkrequest": "PostToolUse",
    "shellcommandfailed": "PostToolUseFailure",
    "testcommandfailed": "PostToolUseFailure",
    "sandboxsessionend": "SessionEnd",
    "sessionend": "SessionEnd",
    "stop": "Stop",
}


class OpenHandsAdapter(BaseRuntimeAdapter):
    """Normalize OpenHands backend protocol events into bounded facts."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("openhands"))

    def canonical_event_name(self, payload: Mapping[str, Any]) -> str:
        raw = _first_text(payload, "event_type", "event_name", "eventName", "event", "type", "action")
        compact = _alias_token(raw)
        canonical = _OPENHANDS_EVENT_ALIASES.get(compact, _canonical_event_name(raw))
        if canonical == "PostToolUse" and self.extract_command_outcome(payload) == "fail":
            return "PostToolUseFailure"
        return canonical

    def classify_tool_category(self, payload: Mapping[str, Any]) -> str | None:
        action = _alias_token(_first_text(payload, "action", "event_type", "event_name", "type"))
        if action in {"fileread", "readfile"}:
            return "read"
        if action in {"filewrite", "filewritten", "filechange", "filechanged", "filedelete", "filedeleted"}:
            return "edit"
        if action in {"testcommand", "testcommandfailed", "validationcommand"}:
            return "test"
        if action in {"browseraction", "networkrequest"}:
            return "network"
        if action in {"shellcommand", "shellcommandfailed", "command"}:
            command_kind = self.extract_command_kind(payload)
            return "test" if command_kind in {"pytest", "unittest", "tox", "nox"} else "bash"
        return super().classify_tool_category(payload)

    def extract_paths(
        self,
        payload: Mapping[str, Any],
        *,
        base_path: str | None = None,
    ) -> list[str]:
        groups = self.extract_path_groups(payload, base_path=base_path)
        return _aggregate_path_groups(groups, base_path=base_path) or _paths_from_payload(
            payload,
            base_path=base_path,
        )

    def extract_path_groups(
        self,
        payload: Mapping[str, Any],
        *,
        base_path: str | None = None,
    ) -> dict[str, list[str]]:
        action = _alias_token(_first_text(payload, "action", "event_type", "event_name", "type"))
        generic_paths = _paths_from_payload(payload, base_path=base_path)
        read_paths: list[object] = []
        changed_paths: list[object] = []
        deleted_paths: list[object] = []
        generated_paths: list[object] = []
        read_paths.extend(_path_values(payload, "read_paths", "readPaths"))
        changed_paths.extend(_path_values(payload, "changed_paths", "changedPaths", "modified_paths"))
        deleted_paths.extend(_path_values(payload, "deleted_paths", "deletedPaths", "removed_paths"))
        generated_paths.extend(_path_values(payload, "generated_paths", "generatedPaths", "output_paths"))
        if action in {"fileread", "readfile"}:
            read_paths.extend(generic_paths)
        elif action in {"filedelete", "filedeleted"}:
            deleted_paths.extend(generic_paths)
        elif action in {"filewrite", "filewritten", "filechange", "filechanged"}:
            changed_paths.extend(generic_paths)
        elif action in {"shellcommand", "testcommand", "browseraction", "networkrequest"}:
            generated_paths.extend(_path_values(payload, "output_path", "outputPath"))
        return {
            "read_paths": _bounded_paths(read_paths, base_path),
            "changed_paths": _bounded_paths(changed_paths, base_path),
            "deleted_paths": _bounded_paths(deleted_paths, base_path),
            "generated_paths": _bounded_paths(generated_paths, base_path),
        }

    def classify_command_risk(
        self,
        command_kind: str | None,
        payload: Mapping[str, Any],
    ) -> str | None:
        category = self.classify_tool_category(payload)
        if category == "network":
            return "network"
        if category == "edit" and not command_kind:
            return "mutation"
        return _classify_command_risk(_raw_command(payload), command_kind)

    def extract_command_outcome(self, payload: Mapping[str, Any]) -> str | None:
        canonical = _OPENHANDS_EVENT_ALIASES.get(
            _alias_token(_first_text(payload, "event_type", "event_name", "type", "action"))
        )
        if canonical == "PostToolUseFailure":
            return "fail"
        return super().extract_command_outcome(payload)

    def extract_validation_signal(self, payload: Mapping[str, Any]) -> dict[str, object]:
        data = super().extract_validation_signal(payload)
        if self.classify_tool_category(payload) == "test":
            data.setdefault("validation_candidate", True)
            outcome = self.extract_command_outcome(payload)
            if outcome in {"pass", "fail", "timeout", "cancelled", "unknown"}:
                data.setdefault("validation_outcome", outcome)
            data.setdefault("validation_freshness", "current")
        return data


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _path_values(payload: Mapping[str, Any], *keys: str) -> list[object]:
    values: list[object] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            values.extend(value)
        elif value:
            values.append(value)
    return values


def _raw_command(payload: Mapping[str, Any]) -> str:
    for key in ("command", "cmd", "bash", "script"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _bounded_paths(paths: list[object], base_path: str | None) -> list[str]:
    return cap_list(paths, item_sanitizer=lambda item: normalize_relative_path(item, base=base_path))


def _alias_token(value: object) -> str:
    return _compact_token(value).replace("_", "")


__all__ = ["OpenHandsAdapter"]
