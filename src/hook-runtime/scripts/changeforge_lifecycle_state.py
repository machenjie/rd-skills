#!/usr/bin/env python3
"""Lifecycle state wrapper for ChangeForge hook reducer output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LifecycleState:
    turn_stage: str = ""
    owner_skill: str = ""
    reviewer_skill: str = ""
    read_evidence_seen: bool = False
    repository_context_seen: bool = False
    workflow_state_seen: bool = False
    implementation_preflight_seen: bool = False
    implementation_preflight_complete: bool = False
    edit_without_preflight_seen: bool = False
    review_evidence_seen: bool = False
    repair_evidence_seen: bool = False
    validation_freshness_seen: bool = False
    runtime_adapter: dict[str, object] = field(default_factory=dict)
    normalized_events: list[str] = field(default_factory=list)
    changed_paths: list[str] = field(default_factory=list)
    deleted_paths: list[str] = field(default_factory=list)
    generated_paths: list[str] = field(default_factory=list)
    read_paths: list[str] = field(default_factory=list)
    searched_patterns: list[str] = field(default_factory=list)
    validation_results: list[str] = field(default_factory=list)
    review_findings: list[str] = field(default_factory=list)
    repair_events: list[str] = field(default_factory=list)
    rereview_events: list[str] = field(default_factory=list)
    command_risks: list[str] = field(default_factory=list)
    permission_decisions: list[str] = field(default_factory=list)
    rollback_points: list[str] = field(default_factory=list)
    risk_surfaces: list[str] = field(default_factory=list)

    @classmethod
    def from_state(cls, state: dict | None) -> "LifecycleState":
        state = state if isinstance(state, dict) else {}
        return cls(
            turn_stage=_text(state.get("turn_stage")),
            owner_skill=_text(state.get("owner_skill")),
            reviewer_skill=_text(state.get("reviewer_skill")),
            read_evidence_seen=bool(state.get("read_evidence_seen")),
            repository_context_seen=bool(state.get("repository_context_seen")),
            workflow_state_seen=bool(state.get("workflow_state_seen")),
            implementation_preflight_seen=bool(state.get("implementation_preflight_seen")),
            implementation_preflight_complete=bool(
                state.get("implementation_preflight_complete")
            ),
            edit_without_preflight_seen=bool(state.get("edit_without_preflight_seen")),
            review_evidence_seen=bool(state.get("review_evidence_seen")),
            repair_evidence_seen=bool(state.get("repair_evidence_seen")),
            validation_freshness_seen=bool(state.get("validation_freshness_seen")),
            runtime_adapter=_clean_mapping(state.get("runtime_adapter")),
            normalized_events=_string_list(state.get("normalized_events")),
            changed_paths=_string_list(state.get("changed_paths")),
            deleted_paths=_string_list(state.get("deleted_paths")),
            generated_paths=_string_list(state.get("generated_paths")),
            read_paths=_string_list(state.get("read_paths")),
            searched_patterns=_string_list(state.get("searched_patterns")),
            validation_results=_string_list(state.get("validation_results")),
            review_findings=_string_list(state.get("review_findings")),
            repair_events=_string_list(state.get("repair_events")),
            rereview_events=_string_list(state.get("rereview_events")),
            command_risks=_string_list(state.get("command_risks")),
            permission_decisions=_string_list(state.get("permission_decisions")),
            rollback_points=_string_list(state.get("rollback_points")),
            risk_surfaces=_string_list(state.get("risk_surfaces")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "turn_stage": self.turn_stage,
            "owner_skill": self.owner_skill,
            "reviewer_skill": self.reviewer_skill,
            "read_evidence_seen": self.read_evidence_seen,
            "repository_context_seen": self.repository_context_seen,
            "workflow_state_seen": self.workflow_state_seen,
            "implementation_preflight_seen": self.implementation_preflight_seen,
            "implementation_preflight_complete": self.implementation_preflight_complete,
            "edit_without_preflight_seen": self.edit_without_preflight_seen,
            "review_evidence_seen": self.review_evidence_seen,
            "repair_evidence_seen": self.repair_evidence_seen,
            "validation_freshness_seen": self.validation_freshness_seen,
            "runtime_adapter": dict(self.runtime_adapter),
            "normalized_events": list(self.normalized_events),
            "changed_paths": list(self.changed_paths),
            "deleted_paths": list(self.deleted_paths),
            "generated_paths": list(self.generated_paths),
            "read_paths": list(self.read_paths),
            "searched_patterns": list(self.searched_patterns),
            "validation_results": list(self.validation_results),
            "review_findings": list(self.review_findings),
            "repair_events": list(self.repair_events),
            "rereview_events": list(self.rereview_events),
            "command_risks": list(self.command_risks),
            "permission_decisions": list(self.permission_decisions),
            "rollback_points": list(self.rollback_points),
            "risk_surfaces": list(self.risk_surfaces),
        }


def _text(value: object) -> str:
    return str(value or "").strip()[:300]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    result: list[str] = []
    for item in value:
        text = str(item).strip()[:300]
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _clean_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, object] = {}
    for key, raw in value.items():
        name = str(key).strip()[:80]
        if not name:
            continue
        if isinstance(raw, list):
            cleaned[name] = _string_list(raw)
        else:
            cleaned[name] = _text(raw)
    return cleaned


__all__ = ["LifecycleState"]
