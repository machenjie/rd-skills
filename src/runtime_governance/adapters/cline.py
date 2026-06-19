"""Cline staged adapter target."""

from __future__ import annotations

from typing import Any, Mapping

from ..privacy import cap_list
from .base import (
    BaseRuntimeAdapter,
    adapter_capabilities_for,
    _canonical_event_name,
    _compact_token,
    _paths_from_payload,
)


PLAN_STAGE_BY_TOKEN = {
    "requirement": "requirement-intake",
    "requirements": "requirement-intake",
    "requirementintake": "requirement-intake",
    "intake": "requirement-intake",
    "architecture": "architecture-design",
    "architecturedesign": "architecture-design",
    "design": "architecture-design",
    "plan": "implementation-planning",
    "planning": "implementation-planning",
    "implementationplanning": "implementation-planning",
    "debug": "debugging-diagnosis",
    "debugging": "debugging-diagnosis",
    "diagnosis": "debugging-diagnosis",
    "debuggingdiagnosis": "debugging-diagnosis",
    "review": "code-review",
    "codereview": "code-review",
}
ACT_STAGE_BY_TOKEN = {
    "act": "coding",
    "code": "coding",
    "coding": "coding",
    "implement": "coding",
    "implementation": "coding",
    "fix": "bug-fix",
    "bugfix": "bug-fix",
    "bug": "bug-fix",
    "refactor": "refactoring",
    "refactoring": "refactoring",
    "test": "testing",
    "testing": "testing",
    "release": "release-delivery",
    "delivery": "release-delivery",
    "releasedelivery": "release-delivery",
}
PLAN_MODE_TOKENS = {"plan", "planning"}
ACT_MODE_TOKENS = {"act", "acting"}
_CLINE_EVENT_ALIASES = {
    "modechange": "UserPromptSubmit",
    "modeswitch": "UserPromptSubmit",
    "plan": "UserPromptSubmit",
    "act": "PostToolUse",
    "taskstarted": "TaskCreated",
    "taskcreated": "TaskCreated",
    "taskcompleted": "TaskCompleted",
    "filechanged": "FileChanged",
    "tooluse": "PostToolUse",
    "toolresult": "PostToolUse",
}


class ClineAdapter(BaseRuntimeAdapter):
    """Normalize Cline mode payloads without claiming hook lifecycle support."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("cline"))

    def canonical_event_name(self, payload: Mapping[str, Any]) -> str:
        raw = _first_text(payload, "event_name", "eventName", "event", "type")
        compact = _alias_token(raw)
        return _CLINE_EVENT_ALIASES.get(compact, _canonical_event_name(raw))

    def extract_stage_signal(self, payload: Mapping[str, Any], canonical_event: str) -> str | None:
        mode = _mode_token(payload)
        stage = _stage_token(payload)
        if mode in PLAN_MODE_TOKENS:
            return PLAN_STAGE_BY_TOKEN.get(stage)
        if mode in ACT_MODE_TOKENS:
            return ACT_STAGE_BY_TOKEN.get(stage)
        return PLAN_STAGE_BY_TOKEN.get(stage) or ACT_STAGE_BY_TOKEN.get(stage)

    def build_degradation(self, canonical_event: str, payload: Mapping[str, Any]) -> list[str]:
        degradation = super().build_degradation(canonical_event, payload)
        mode = _mode_token(payload)
        if mode in PLAN_MODE_TOKENS and _looks_like_mutation(payload, self.classify_tool_category(payload)):
            degradation.append("cline_plan_mode_edit_evidence_unsupported")
        if mode in ACT_MODE_TOKENS and _stage_token(payload) in set(PLAN_STAGE_BY_TOKEN):
            degradation.append("cline_act_mode_planning_stage_degraded")
        return cap_list(degradation)


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _mode_token(payload: Mapping[str, Any]) -> str:
    return _alias_token(_first_text(payload, "mode", "cline_mode", "clineMode", "plan_act_mode"))


def _stage_token(payload: Mapping[str, Any]) -> str:
    return _alias_token(
        _first_text(payload, "stage", "changeforge_stage", "changeforgeStage", "task_type", "taskType")
    )


def _looks_like_mutation(payload: Mapping[str, Any], category: str | None) -> bool:
    if category in {"edit", "write", "bash", "test", "git", "network"}:
        return True
    return bool(_paths_from_payload(payload, base_path=None))


def _alias_token(value: object) -> str:
    return _compact_token(value).replace("_", "")


__all__ = ["ACT_STAGE_BY_TOKEN", "PLAN_STAGE_BY_TOKEN", "ClineAdapter"]
