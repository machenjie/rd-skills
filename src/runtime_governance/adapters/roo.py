"""Roo staged adapter target."""

from __future__ import annotations

from typing import Any, Mapping

from ..privacy import cap_list
from .base import BaseRuntimeAdapter, adapter_capabilities_for, _canonical_event_name, _compact_token


ROO_MODE_TOOL_POLICIES = {
    "architect": frozenset({"read", "mcp"}),
    "code": frozenset({"read", "edit", "bash", "test"}),
    "debug": frozenset({"read", "bash", "test"}),
    "review": frozenset({"read", "mcp"}),
    "test": frozenset({"read", "bash", "test"}),
    "release": frozenset({"read", "bash", "test", "git"}),
    "security": frozenset({"read", "mcp", "test"}),
}
ROO_MODE_STAGE = {
    "architect": "architecture-design",
    "code": "coding",
    "debug": "debugging-diagnosis",
    "review": "code-review",
    "test": "testing",
    "release": "release-delivery",
    "security": "code-review",
}
_ROO_EVENT_ALIASES = {
    "modechange": "UserPromptSubmit",
    "modeswitch": "UserPromptSubmit",
    "taskstarted": "TaskCreated",
    "taskcreated": "TaskCreated",
    "taskcompleted": "TaskCompleted",
    "tooluse": "PostToolUse",
    "toolresult": "PostToolUse",
    "filechanged": "FileChanged",
}


class RooAdapter(BaseRuntimeAdapter):
    """Normalize Roo mode payloads and expose unsupported runtime gaps."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("roo"))

    def canonical_event_name(self, payload: Mapping[str, Any]) -> str:
        raw = _first_text(payload, "event_name", "eventName", "event", "type")
        compact = _alias_token(raw)
        return _ROO_EVENT_ALIASES.get(compact, _canonical_event_name(raw))

    def extract_stage_signal(self, payload: Mapping[str, Any], canonical_event: str) -> str | None:
        mode = _mode_token(payload)
        return ROO_MODE_STAGE.get(mode)

    def build_degradation(self, canonical_event: str, payload: Mapping[str, Any]) -> list[str]:
        degradation = super().build_degradation(canonical_event, payload)
        mode = _mode_token(payload)
        category = self.classify_tool_category(payload)
        allowed = ROO_MODE_TOOL_POLICIES.get(mode)
        if allowed is not None and category not in {None, "unknown"} and category not in allowed:
            degradation.append(f"roo_{mode}_mode_{category}_tools_unsupported")
        if _truthy(_first_text(payload, "repository_context_indexed", "repositoryContextIndexed")):
            degradation.append("roo_repository_context_indexing_unverified")
        if _truthy(_first_text(payload, "orchestrator_task", "subtask", "subagent_task")):
            degradation.append("roo_orchestrator_subtask_mapping_unverified")
        return cap_list(degradation)


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, bool):
            return "true" if value else "false"
    return ""


def _mode_token(payload: Mapping[str, Any]) -> str:
    mode = _alias_token(_first_text(payload, "mode", "roo_mode", "rooMode", "role"))
    if mode == "ask":
        return "architect"
    if mode == "orchestrator":
        return "code"
    return mode


def _truthy(value: object) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "y", "enabled"}


def _alias_token(value: object) -> str:
    return _compact_token(value).replace("_", "")


__all__ = ["ROO_MODE_STAGE", "ROO_MODE_TOOL_POLICIES", "RooAdapter"]
