"""Copilot executor adapter."""

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


_COPILOT_EVENT_ALIASES = {
    "sessionstart": "SessionStart",
    "posttooluse": "PostToolUse",
    "stop": "Stop",
    "agentstop": "Stop",
    "subagentstart": "SubagentStart",
    "userpromptsubmit": "UserPromptSubmit",
    "userpromptsubmitted": "UserPromptSubmit",
    "pretooluse": "PreToolUse",
    "subagentstop": "SubagentStop",
}


class CopilotAdapter(BaseRuntimeAdapter):
    """Normalize Copilot hook payloads into governance facts."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("copilot"))

    def canonical_event_name(self, payload: Mapping[str, Any]) -> str:
        raw = _first_text(
            payload,
            "eventName",
            "event_name",
            "hook_event_name",
            "hookEventName",
            "event",
            "type",
        )
        compact = _compact_token(raw)
        return _COPILOT_EVENT_ALIASES.get(compact, _canonical_event_name(raw))

    def classify_tool_category(self, payload: Mapping[str, Any]) -> str | None:
        if self.canonical_event_name(payload) != "PostToolUse":
            return super().classify_tool_category(payload)
        tool = _compact_token(self.extract_tool_name(payload))
        if tool in {"read_file", "readfile", "grep_search", "grep", "search", "list_dir", "listdirectory"}:
            return "read"
        if tool in {
            "replace_string_in_file",
            "createfile",
            "create_file",
            "insert_edit_into_file",
            "edit",
            "write",
        }:
            return "edit"
        if tool in {"runterminalcommand", "terminal", "bash", "shell"}:
            command_kind = self.extract_command_kind(payload)
            if command_kind in {"pytest", "unittest", "tox", "nox"}:
                return "test"
            return "bash"
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
        if self.canonical_event_name(payload) != "PostToolUse":
            return super().extract_path_groups(payload, base_path=base_path)
        category = self.classify_tool_category(payload)
        generic_paths = _paths_from_payload(payload, base_path=base_path)
        read_paths: list[object] = []
        changed_paths: list[object] = []
        generated_paths: list[object] = []
        if category == "read":
            read_paths.extend(generic_paths)
        elif category == "edit":
            changed_paths.extend(generic_paths)
        else:
            generated_paths.extend(_explicit_output_paths(payload))
        return {
            "read_paths": _bounded_paths(read_paths, base_path),
            "changed_paths": _bounded_paths(changed_paths, base_path),
            "deleted_paths": [],
            "generated_paths": _bounded_paths(generated_paths, base_path),
        }

    def classify_command_risk(
        self,
        command_kind: str | None,
        payload: Mapping[str, Any],
    ) -> str | None:
        if self.canonical_event_name(payload) != "PostToolUse":
            return super().classify_command_risk(command_kind, payload)
        category = self.classify_tool_category(payload)
        if category == "edit" and not command_kind:
            return "mutation"
        return _classify_command_risk(_raw_command(payload), command_kind)


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _candidate_mappings(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates: list[Mapping[str, Any]] = [payload]
    for key in ("tool_input", "toolInput", "input", "arguments", "parameters", "params", "result"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            candidates.append(value)
    return candidates


def _raw_command(payload: Mapping[str, Any]) -> str:
    for container in _candidate_mappings(payload):
        for key in ("command", "cmd", "bash", "script"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _explicit_output_paths(payload: Mapping[str, Any]) -> list[object]:
    paths: list[object] = []
    for container in _candidate_mappings(payload):
        for key in ("output_path", "outputPath", "output_paths", "outputPaths", "generated_paths"):
            value = container.get(key)
            if isinstance(value, list):
                paths.extend(value)
            elif value:
                paths.append(value)
    return paths


def _bounded_paths(paths: list[object], base_path: str | None) -> list[str]:
    return cap_list(paths, item_sanitizer=lambda item: normalize_relative_path(item, base=base_path))


__all__ = ["CopilotAdapter"]
