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
    changed_paths: list[str] = field(default_factory=list)
    read_paths: list[str] = field(default_factory=list)
    searched_patterns: list[str] = field(default_factory=list)
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
            changed_paths=_string_list(state.get("changed_paths")),
            read_paths=_string_list(state.get("read_paths")),
            searched_patterns=_string_list(state.get("searched_patterns")),
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
            "changed_paths": list(self.changed_paths),
            "read_paths": list(self.read_paths),
            "searched_patterns": list(self.searched_patterns),
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


__all__ = ["LifecycleState"]
