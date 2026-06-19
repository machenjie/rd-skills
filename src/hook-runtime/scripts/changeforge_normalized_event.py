#!/usr/bin/env python3
"""Normalized hook event object for ChangeForge executor adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from changeforge_common import (
    detect_runtime,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    normalize_path,
    summarize_command_program,
    tool_name,
)
from changeforge_adapter_capabilities import runtime_adapter_for


EVENT_NAME_MAP = {
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


@dataclass(frozen=True)
class NormalizedEvent:
    runtime: str = "unknown"
    event_name: str = "unknown"
    event_kind: str = "unknown"
    stage: str = "unknown"
    tool_name: str = ""
    command_program: str = ""
    bounded_paths: list[str] = field(default_factory=list)
    changed_paths: list[str] = field(default_factory=list)
    read_paths: list[str] = field(default_factory=list)
    deleted_paths: list[str] = field(default_factory=list)
    generated_paths: list[str] = field(default_factory=list)
    searched_patterns: list[str] = field(default_factory=list)
    product_surfaces: list[str] = field(default_factory=list)
    language_surfaces: list[str] = field(default_factory=list)
    risk_surfaces: list[str] = field(default_factory=list)
    domain_extensions: list[str] = field(default_factory=list)
    prompt_signals: list[str] = field(default_factory=list)
    should_inject: bool = False
    lifecycle_cadence: str | None = None
    executor_event_name: str | None = None
    executor_event_phase: str | None = None
    tool_category: str | None = None
    command_risk: str | None = None
    command_outcome: str | None = None
    exit_code: int | None = None
    validation_candidate: bool | None = None
    validation_outcome: str | None = None
    validation_freshness: str | None = None
    permission_decision: str | None = None
    permission_reason: str | None = None
    checkpoint_id: str | None = None
    rollback_available: bool | None = None
    capability_degradation: list[str] = field(default_factory=list)
    privacy_redaction: list[str] = field(default_factory=list)

    @classmethod
    def from_event(
        cls,
        event: dict[str, Any],
        *,
        classification: dict[str, Any] | None = None,
        read_evidence: dict[str, list[str]] | None = None,
    ) -> "NormalizedEvent":
        event = event if isinstance(event, dict) else {}
        classification = classification if isinstance(classification, dict) else {}
        read_evidence = read_evidence if isinstance(read_evidence, dict) else {}
        runtime = _normalized_runtime(detect_runtime(event))
        canonical = _canonical_normalized_event(event, runtime)
        canonical_data = canonical.to_json_dict() if canonical is not None else {}
        raw_event_name = str(
            canonical_data.get("executor_event_name") or _canonical_event_name(event_name(event))
        )
        stage = str(classification.get("stage") or "unknown").strip() or "unknown"
        command = extract_bash_command(event)
        command_program = str(
            classification.get("command_program") or summarize_command_program(command)
        ).strip()
        tool = str(classification.get("tool") or tool_name(event)).strip()
        paths = _string_list(classification.get("paths"))
        if not paths:
            paths = [normalize_path(path) for path in extract_changed_paths(event)]
        changed_paths = paths if stage in {"edit", "repair", "refactor", "release", "skill_authoring"} else []
        read_paths = _string_list(read_evidence.get("paths"))
        if stage in {"read", "review"} and not read_paths:
            read_paths = paths
        return cls(
            runtime=runtime,
            event_name=raw_event_name,
            event_kind=str(canonical_data.get("event_kind") or "unknown"),
            stage=stage,
            tool_name=tool,
            command_program=command_program,
            bounded_paths=_unique(_string_list(canonical_data.get("bounded_paths")) or paths),
            changed_paths=_unique(changed_paths),
            read_paths=_unique(read_paths),
            deleted_paths=_unique(_string_list(canonical_data.get("deleted_paths"))),
            generated_paths=_unique(_string_list(canonical_data.get("generated_paths"))),
            searched_patterns=_unique(_string_list(read_evidence.get("patterns"))),
            product_surfaces=_unique(_string_list(classification.get("product_surfaces") or classification.get("surfaces"))),
            language_surfaces=_unique(_string_list(classification.get("language_surfaces"))),
            risk_surfaces=_unique(_string_list(classification.get("risk_surfaces"))),
            domain_extensions=_unique(_string_list(classification.get("domain_extensions"))),
            prompt_signals=_unique(_string_list(classification.get("prompt_signals"))),
            should_inject=bool(classification.get("should_inject")),
            lifecycle_cadence=_optional_text(canonical_data.get("lifecycle_cadence")),
            executor_event_name=_optional_text(canonical_data.get("executor_event_name")),
            executor_event_phase=_optional_text(canonical_data.get("executor_event_phase")),
            tool_category=_optional_text(canonical_data.get("tool_category")),
            command_risk=_optional_text(canonical_data.get("command_risk")),
            command_outcome=_optional_text(canonical_data.get("command_outcome")),
            exit_code=_optional_int(canonical_data.get("exit_code")),
            validation_candidate=_optional_bool(canonical_data.get("validation_candidate")),
            validation_outcome=_optional_text(canonical_data.get("validation_outcome")),
            validation_freshness=_optional_text(canonical_data.get("validation_freshness")),
            permission_decision=_optional_text(canonical_data.get("permission_decision")),
            permission_reason=_optional_text(canonical_data.get("permission_reason")),
            checkpoint_id=_optional_text(canonical_data.get("checkpoint_id")),
            rollback_available=_optional_bool(canonical_data.get("rollback_available")),
            capability_degradation=_unique(
                _string_list(canonical_data.get("capability_degradation"))
            ),
            privacy_redaction=_unique(_string_list(canonical_data.get("privacy_redaction"))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime": self.runtime,
            "event_name": self.event_name,
            "event_kind": self.event_kind,
            "stage": self.stage,
            "tool_name": self.tool_name,
            "command_program": self.command_program,
            "bounded_paths": list(self.bounded_paths),
            "changed_paths": list(self.changed_paths),
            "read_paths": list(self.read_paths),
            "deleted_paths": list(self.deleted_paths),
            "generated_paths": list(self.generated_paths),
            "searched_patterns": list(self.searched_patterns),
            "product_surfaces": list(self.product_surfaces),
            "language_surfaces": list(self.language_surfaces),
            "risk_surfaces": list(self.risk_surfaces),
            "domain_extensions": list(self.domain_extensions),
            "prompt_signals": list(self.prompt_signals),
            "should_inject": self.should_inject,
            "lifecycle_cadence": self.lifecycle_cadence,
            "executor_event_name": self.executor_event_name,
            "executor_event_phase": self.executor_event_phase,
            "tool_category": self.tool_category,
            "command_risk": self.command_risk,
            "command_outcome": self.command_outcome,
            "exit_code": self.exit_code,
            "validation_candidate": self.validation_candidate,
            "validation_outcome": self.validation_outcome,
            "validation_freshness": self.validation_freshness,
            "permission_decision": self.permission_decision,
            "permission_reason": self.permission_reason,
            "checkpoint_id": self.checkpoint_id,
            "rollback_available": self.rollback_available,
            "capability_degradation": list(self.capability_degradation),
            "privacy_redaction": list(self.privacy_redaction),
        }

    def to_classifier_dict(self) -> dict[str, object]:
        paths = self.changed_paths or self.read_paths
        return {
            "stage": self.stage,
            "surfaces": list(self.product_surfaces),
            "product_surfaces": list(self.product_surfaces),
            "language_surfaces": list(self.language_surfaces),
            "risk_surfaces": list(self.risk_surfaces),
            "domain_extensions": list(self.domain_extensions),
            "prompt_signals": list(self.prompt_signals),
            "paths": list(paths),
            "tool": self.tool_name,
            "command_program": self.command_program,
            "should_inject": self.should_inject,
        }


def _canonical_event_name(name: str) -> str:
    compact = "".join(ch for ch in str(name or "").strip().casefold() if ch.isalnum())
    return EVENT_NAME_MAP.get(compact, "Unknown")


def _canonical_normalized_event(event: dict[str, Any], runtime: str) -> Any:
    try:
        return runtime_adapter_for(runtime).normalize_event(event).normalized_event
    except Exception:
        return None


def _normalized_runtime(runtime: str) -> str:
    runtime = str(runtime or "").strip().casefold()
    supported = {"codex", "claude", "copilot", "generic", "cline", "roo", "openhands"}
    return runtime if runtime in supported else "unknown"


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().casefold()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()[:300]
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


__all__ = ["NormalizedEvent"]
