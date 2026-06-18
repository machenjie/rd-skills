#!/usr/bin/env python3
"""Evidence ledger objects for ChangeForge hook closure checks."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from changeforge_lifecycle_state import LifecycleState
from changeforge_normalized_event import NormalizedEvent

try:
    from runtime_governance.evidence import EvidenceLedger as GovernanceEvidenceLedger
except ModuleNotFoundError:  # Source tree layout: hook scripts live under src/hook-runtime.
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from runtime_governance.evidence import EvidenceLedger as GovernanceEvidenceLedger


UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReadEvidence:
    paths: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"paths": list(self.paths), "patterns": list(self.patterns)}


@dataclass(frozen=True)
class EditEvidence:
    changed_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"changed_paths": list(self.changed_paths)}


@dataclass(frozen=True)
class ValidationEvidence:
    commands: list[str] = field(default_factory=list)
    outcome_seen: bool = False
    fresh_after_last_edit: bool | str = UNKNOWN

    def to_dict(self) -> dict[str, object]:
        return {
            "commands": list(self.commands),
            "outcome_seen": self.outcome_seen,
            "fresh_after_last_edit": self.fresh_after_last_edit,
        }


@dataclass(frozen=True)
class ReviewEvidence:
    reviewer_skill: str = ""
    reviewed_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "reviewer_skill": self.reviewer_skill,
            "reviewed_paths": list(self.reviewed_paths),
        }


@dataclass(frozen=True)
class RepairEvidence:
    repaired_paths: list[str] = field(default_factory=list)
    re_review_seen: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "repaired_paths": list(self.repaired_paths),
            "re_review_seen": self.re_review_seen,
        }


@dataclass(frozen=True)
class ClosureEvidence:
    route_manifest_complete: bool = False
    changed_files_present: bool = False
    validation_present: bool = False
    residual_risk_present: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "route_manifest_complete": self.route_manifest_complete,
            "changed_files_present": self.changed_files_present,
            "validation_present": self.validation_present,
            "residual_risk_present": self.residual_risk_present,
        }


@dataclass(frozen=True)
class EvidenceLedger:
    read_evidence: ReadEvidence = field(default_factory=ReadEvidence)
    edit_evidence: EditEvidence = field(default_factory=EditEvidence)
    validation_evidence: ValidationEvidence = field(default_factory=ValidationEvidence)
    review_evidence: ReviewEvidence = field(default_factory=ReviewEvidence)
    repair_evidence: RepairEvidence = field(default_factory=RepairEvidence)
    closure_evidence: ClosureEvidence = field(default_factory=ClosureEvidence)
    governance_ledger: GovernanceEvidenceLedger | None = field(default=None, repr=False, compare=False)

    @classmethod
    def from_state(
        cls,
        state: dict | None,
        *,
        normalized_event: NormalizedEvent | None = None,
        route_manifest_complete: bool = False,
        residual_risk_present: bool = False,
    ) -> "EvidenceLedger":
        state = state if isinstance(state, dict) else {}
        lifecycle = LifecycleState.from_state(state)
        event = normalized_event
        validation_commands: list[str] = []
        if event and event.stage == "test" and event.command_program:
            validation_commands.append(event.command_program)
        validation_present = bool(state.get("validation_command_seen") or state.get("validation_seen"))
        read_paths = _unique([*lifecycle.read_paths, *((event.read_paths if event else []))])
        changed_paths = _unique([*lifecycle.changed_paths, *((event.changed_paths if event else []))])
        governance = GovernanceEvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": event.event_name if event else "Stop",
                    "runtime": event.runtime if event else "generic",
                    "route_manifest_detected": route_manifest_complete,
                    "manifest_selected_skills": ["change-forge-router"] if route_manifest_complete else [],
                    "manifest_selected_capabilities": ["implementation-structure-design"]
                    if route_manifest_complete
                    else [],
                    "manifest_required_references": ["hook-compat"] if route_manifest_complete else [],
                    "manifest_required_quality_gates": ["quality-test-gate"]
                    if route_manifest_complete
                    else [],
                    "read_evidence_seen": bool(read_paths),
                    "read_paths": read_paths,
                    "repository_context_seen": bool(lifecycle.repository_context_seen),
                    "implementation_preflight_complete": bool(
                        state.get("implementation_preflight_complete")
                    ),
                    "changed_paths": changed_paths,
                    "validation_command_detected": validation_present,
                    "validation_evidence_detected": validation_present,
                    "validation_result_outcome": "pass" if validation_present else "",
                    "validation_result_evidence_strength": "strong" if validation_present else "",
                    "validation_result_fresh_after_last_edit": "true"
                    if lifecycle.validation_freshness_seen
                    else "",
                    "review_evidence_seen": bool(state.get("review_evidence_seen")),
                    "repair_evidence_seen": bool(state.get("repair_evidence_seen")),
                    "residual_risk_detected": residual_risk_present
                    or bool(state.get("closure_risk_surfaces") or lifecycle.risk_surfaces),
                }
            ]
        )
        return cls(
            read_evidence=ReadEvidence(
                paths=read_paths,
                patterns=_unique(
                    [*lifecycle.searched_patterns, *((event.searched_patterns if event else []))]
                ),
            ),
            edit_evidence=EditEvidence(
                changed_paths=changed_paths
            ),
            validation_evidence=ValidationEvidence(
                commands=_unique(validation_commands),
                outcome_seen=validation_present,
                fresh_after_last_edit=True
                if lifecycle.validation_freshness_seen
                else UNKNOWN,
            ),
            review_evidence=ReviewEvidence(
                reviewer_skill=lifecycle.reviewer_skill,
                reviewed_paths=_unique(_string_list(state.get("review_targets"))),
            ),
            repair_evidence=RepairEvidence(
                repaired_paths=_unique(_string_list(state.get("repair_findings"))),
                re_review_seen=bool(state.get("review_evidence_seen") and state.get("repair_evidence_seen")),
            ),
            closure_evidence=ClosureEvidence(
                route_manifest_complete=route_manifest_complete,
                changed_files_present=bool(changed_paths),
                validation_present=validation_present,
                residual_risk_present=residual_risk_present
                or bool(state.get("closure_risk_surfaces") or lifecycle.risk_surfaces),
            ),
            governance_ledger=governance,
        )

    def to_governance_ledger(self) -> GovernanceEvidenceLedger:
        return self.governance_ledger or GovernanceEvidenceLedger()

    def to_dict(self) -> dict[str, object]:
        return {
            "read_evidence": self.read_evidence.to_dict(),
            "edit_evidence": self.edit_evidence.to_dict(),
            "validation_evidence": self.validation_evidence.to_dict(),
            "review_evidence": self.review_evidence.to_dict(),
            "repair_evidence": self.repair_evidence.to_dict(),
            "closure_evidence": self.closure_evidence.to_dict(),
        }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()[:300]
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


__all__ = [
    "ClosureEvidence",
    "EditEvidence",
    "EvidenceLedger",
    "ReadEvidence",
    "RepairEvidence",
    "ReviewEvidence",
    "UNKNOWN",
    "ValidationEvidence",
]
