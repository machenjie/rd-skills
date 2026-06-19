"""Claude executor adapter."""

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
    is_validation_command,
)


_CLAUDE_EVENT_ALIASES = {
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
    "precompact": "PreCompact",
    "postcompact": "PostCompact",
    "compact": "Compact",
    "compaction": "Compact",
}


class ClaudeAdapter(BaseRuntimeAdapter):
    """Normalize Claude hook payloads into governance facts."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("claude"))

    def canonical_event_name(self, payload: Mapping[str, Any]) -> str:
        raw = _first_text(
            payload,
            "hookEventName",
            "hook_event_name",
            "eventName",
            "event_name",
            "event",
            "type",
        )
        compact = _compact_token(raw)
        return _CLAUDE_EVENT_ALIASES.get(compact, _canonical_event_name(raw))

    def classify_tool_category(self, payload: Mapping[str, Any]) -> str | None:
        canonical = self.canonical_event_name(payload)
        if canonical in {"FileChanged", "ConfigChanged"}:
            return "edit"
        tool = _compact_token(self.extract_tool_name(payload))
        if tool in {
            "read",
            "grep",
            "glob",
            "ls",
            "search",
            "view",
            "open",
            "fetch",
            "fetchfile",
            "fetchprpatch",
            "getprdiff",
            "mcpfilesystemreadfile",
            "mcpfilesystemlistdirectory",
            "mcpgithubgetfilecontents",
            "mcpgithubpullrequestread",
            "mcpgithubsearchcode",
        }:
            return "read"
        if tool in {"edit", "write", "multiedit"}:
            return "edit"
        if tool == "bash":
            command_kind = self.extract_command_kind(payload)
            if is_validation_command(_raw_command(payload), command_kind):
                return "test"
            return "bash"
        if tool.startswith("mcp"):
            return "mcp"
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
        canonical = self.canonical_event_name(payload)
        category = self.classify_tool_category(payload)
        generic_paths = _paths_from_payload(payload, base_path=base_path)
        changed_paths: list[object] = []
        read_paths: list[object] = []
        deleted_paths: list[object] = []
        generated_paths: list[object] = []
        patch_groups = _patch_path_groups(payload)
        changed_paths.extend(patch_groups["changed_paths"])
        deleted_paths.extend(patch_groups["deleted_paths"])
        if canonical in {"FileChanged", "ConfigChanged"}:
            changed_paths.extend(generic_paths)
        elif category == "read":
            read_paths.extend(generic_paths)
        elif category == "edit":
            changed_paths.extend(generic_paths)
        else:
            generated_paths.extend(_explicit_output_paths(payload))
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
        if category == "edit" and not command_kind:
            return "mutation"
        return _classify_command_risk(_raw_command(payload), command_kind)

    def extract_command_outcome(self, payload: Mapping[str, Any]) -> str | None:
        canonical = self.canonical_event_name(payload)
        if canonical in {"PostToolUseFailure", "StopFailure"}:
            return "fail"
        return super().extract_command_outcome(payload)

    def extract_validation_signal(self, payload: Mapping[str, Any]) -> dict[str, object]:
        data = super().extract_validation_signal(payload)
        canonical = self.canonical_event_name(payload)
        if canonical in {"FileChanged", "ConfigChanged"} and _after_validation(payload):
            data.setdefault("validation_candidate", False)
            data["validation_outcome"] = "stale"
            data["validation_freshness"] = "stale"
        return data


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


def _patch_path_groups(payload: Mapping[str, Any]) -> dict[str, list[str]]:
    changed: list[str] = []
    deleted: list[str] = []
    for container in _candidate_mappings(payload):
        for value in container.values():
            if not isinstance(value, str) or "*** Begin Patch" not in value:
                continue
            for line in value.splitlines():
                stripped = line.strip()
                for prefix, target in (
                    ("*** Add File:", changed),
                    ("*** Update File:", changed),
                    ("*** Delete File:", deleted),
                ):
                    if stripped.startswith(prefix):
                        target.append(stripped.removeprefix(prefix).strip())
    return {"changed_paths": changed, "deleted_paths": deleted}


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


def _after_validation(payload: Mapping[str, Any]) -> bool:
    for container in _candidate_mappings(payload):
        for key in ("after_validation", "afterValidation", "validation_already_ran", "validationAlreadyRan"):
            value = container.get(key)
            if isinstance(value, bool):
                return value
            if str(value or "").strip().casefold() in {"true", "1", "yes"}:
                return True
    return False


def _bounded_paths(paths: list[object], base_path: str | None) -> list[str]:
    return cap_list(paths, item_sanitizer=lambda item: normalize_relative_path(item, base=base_path))


__all__ = ["ClaudeAdapter"]
