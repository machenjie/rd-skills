#!/usr/bin/env python3
"""Compatibility wrapper around canonical runtime_governance closure facts."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from changeforge_adapter_capabilities import AdapterCapabilities, adapter_capabilities_for

try:
    from runtime_governance.closure import ClosureContract as GovernanceClosureContract
    from runtime_governance.evidence import (
        EvidenceEntry,
        EvidenceLedger as GovernanceEvidenceLedger,
        EvidenceStrength,
        Freshness,
    )
except ModuleNotFoundError:  # Source tree layout: hook scripts live under src/hook-runtime.
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from runtime_governance.closure import ClosureContract as GovernanceClosureContract
    from runtime_governance.evidence import (
        EvidenceEntry,
        EvidenceLedger as GovernanceEvidenceLedger,
        EvidenceStrength,
        Freshness,
    )


@dataclass(frozen=True)
class ClosureContract:
    adapter: str = "generic"
    supported_checks: list[str] = field(default_factory=list)
    unsupported_checks: list[str] = field(default_factory=list)
    degraded_capabilities: list[str] = field(default_factory=list)
    verdict: str = "needs_validation"
    residual_risk: list[str] = field(default_factory=list)
    requires_route_manifest: bool = True
    requires_stage_route: bool = False
    requires_repository_context: bool = False
    requires_implementation_preflight: bool = False
    requires_validation_evidence: bool = True
    requires_review_evidence: bool = False
    requires_residual_risk: bool = True
    adapter_supports_blocking: bool = False
    closure_status: str = "pass"
    missing_items: list[str] = field(default_factory=list)

    @classmethod
    def from_state(
        cls,
        state: dict | None,
        *,
        route_manifest_complete: bool,
        stage_route_present: bool = False,
        repository_context_present: bool = False,
        implementation_preflight_complete: bool = False,
        validation_evidence_present: bool = False,
        review_evidence_present: bool = False,
        residual_risk_present: bool = False,
        capabilities: AdapterCapabilities | None = None,
        runtime: str = "generic",
        block_mode: bool = False,
        validation_broker_outcome: str = "",
        validation_broker_residual_risk: list[str] | None = None,
    ) -> "ClosureContract":
        state = state if isinstance(state, dict) else {}
        capabilities = capabilities or adapter_capabilities_for(runtime)
        profile = _profile(state)
        supported_checks = _list(getattr(capabilities, "supported_checks", ()))
        unsupported_checks = _list(getattr(capabilities, "unsupported_checks", ()))
        degraded_capabilities = [
            f"{capabilities.runtime}_{_check_token(check)}_unsupported"
            for check in unsupported_checks
        ]
        residual = _list(validation_broker_residual_risk or [])
        if profile == "silent":
            governance = GovernanceClosureContract.from_ledger(
                GovernanceEvidenceLedger(),
                supported_checks=supported_checks,
                unsupported_checks=unsupported_checks,
                degraded_capabilities=degraded_capabilities,
                adapter=capabilities.runtime,
                required_evidence=[],
            )
            return cls(
                adapter=capabilities.runtime,
                supported_checks=supported_checks,
                unsupported_checks=unsupported_checks,
                degraded_capabilities=degraded_capabilities,
                verdict=governance.verdict,
                residual_risk=_unique([*residual, *governance.residual_risk]),
                requires_route_manifest=False,
                requires_validation_evidence=False,
                requires_residual_risk=False,
                adapter_supports_blocking=capabilities.supports_blocking,
            )

        engineering = profile == "engineering"
        requires_route = engineering
        requires_repo = engineering
        requires_preflight = engineering and bool(
            state.get("changed_paths")
            or state.get("implementation_preflight_required")
            or state.get("edit_without_preflight_seen")
            or state.get("post_edit_confirmed_preflight_gap")
        )
        requires_validation = engineering
        requires_review = str(state.get("turn_stage") or "") in {
            "review",
            "code-review",
            "repair",
            "bug-fix",
        }
        requires_risk = True
        required_evidence: list[str] = []
        if requires_route:
            required_evidence.append("route_manifest")
        if engineering and bool(state.get("stage_route_present")):
            required_evidence.append("stage_route")
        if requires_repo:
            required_evidence.append("repository_context")
        if requires_preflight:
            required_evidence.append("implementation_preflight")
        if requires_validation:
            required_evidence.append("validation")
        if requires_review:
            required_evidence.append("review")
        if requires_risk:
            required_evidence.append("residual_risk")

        ledger = _governance_ledger(
            route_manifest_complete=route_manifest_complete,
            repository_context_present=repository_context_present,
            implementation_preflight_complete=implementation_preflight_complete,
            validation_evidence_present=validation_evidence_present,
            review_evidence_present=review_evidence_present,
            residual_risk_present=residual_risk_present,
        )
        governance = GovernanceClosureContract.from_ledger(
            ledger,
            supported_checks=supported_checks,
            unsupported_checks=unsupported_checks,
            degraded_capabilities=degraded_capabilities,
            adapter=capabilities.runtime,
            required_evidence=required_evidence,
        )
        missing = _compat_missing(governance.missing_evidence)
        if "stage_route" in required_evidence and not stage_route_present:
            missing.append("stage_route")
        missing = _unique(missing)
        status = "block" if missing and block_mode and capabilities.supports_blocking else "warn" if missing else "pass"
        verdict = _compat_verdict(governance.verdict, status, validation_broker_outcome)
        return cls(
            adapter=capabilities.runtime,
            supported_checks=supported_checks,
            unsupported_checks=unsupported_checks,
            degraded_capabilities=governance.degraded_capabilities or degraded_capabilities,
            verdict=verdict,
            residual_risk=_unique([*residual, *governance.residual_risk]),
            requires_route_manifest=requires_route,
            requires_stage_route=engineering and bool(state.get("stage_route_present")),
            requires_repository_context=requires_repo,
            requires_implementation_preflight=requires_preflight,
            requires_validation_evidence=requires_validation,
            requires_review_evidence=requires_review,
            requires_residual_risk=requires_risk,
            adapter_supports_blocking=capabilities.supports_blocking,
            closure_status=status,
            missing_items=missing,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "requires_route_manifest": self.requires_route_manifest,
            "requires_stage_route": self.requires_stage_route,
            "requires_repository_context": self.requires_repository_context,
            "requires_implementation_preflight": self.requires_implementation_preflight,
            "requires_validation_evidence": self.requires_validation_evidence,
            "requires_review_evidence": self.requires_review_evidence,
            "requires_residual_risk": self.requires_residual_risk,
            "adapter": self.adapter,
            "supported_checks": list(self.supported_checks),
            "unsupported_checks": list(self.unsupported_checks),
            "degraded_capabilities": list(self.degraded_capabilities),
            "verdict": self.verdict,
            "residual_risk": list(self.residual_risk),
            "adapter_supports_blocking": self.adapter_supports_blocking,
            "closure_status": self.closure_status,
            "missing_items": list(self.missing_items),
        }


def _governance_ledger(
    *,
    route_manifest_complete: bool,
    repository_context_present: bool,
    implementation_preflight_complete: bool,
    validation_evidence_present: bool,
    review_evidence_present: bool,
    residual_risk_present: bool,
) -> GovernanceEvidenceLedger:
    ledger = GovernanceEvidenceLedger()
    _mark(ledger.route_manifest, route_manifest_complete)
    _mark(ledger.repository_context, repository_context_present)
    _mark(ledger.implementation_preflight, implementation_preflight_complete)
    _mark(ledger.validation, validation_evidence_present)
    _mark(ledger.review, review_evidence_present)
    _mark(ledger.residual_risk, residual_risk_present)
    return ledger


def _mark(entry: EvidenceEntry, present: bool) -> None:
    if present:
        entry.merge(
            EvidenceEntry(
                entry.kind,
                EvidenceStrength.STRONG.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
            )
        )


def _profile(state: dict) -> str:
    stage = str(state.get("turn_stage") or "").strip()
    if stage in {"", "question", "unknown", "no_engineering_action"}:
        return "silent"
    if stage in {"read", "review", "requirement-intake", "code-review"} and not state.get("changed_paths"):
        return "read_review"
    return "engineering"


def _compat_missing(items: list[str]) -> list[str]:
    mapping = {"review": "review_evidence", "residual_risk": "risk"}
    return [mapping.get(item, item) for item in items]


def _compat_verdict(governance_verdict: str, closure_status: str, validation_broker_outcome: str) -> str:
    broker = str(validation_broker_outcome or "").strip()
    if broker in {"blocked", "needs_validation", "degraded_ready"}:
        return broker
    if broker == "ready":
        return governance_verdict
    if closure_status == "block":
        return "blocked"
    return governance_verdict


def _check_token(value: str) -> str:
    return str(value).strip().replace("-", "_").replace(" ", "_")


def _list(values: object) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return _unique([str(item) for item in values])


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


__all__ = ["ClosureContract"]
