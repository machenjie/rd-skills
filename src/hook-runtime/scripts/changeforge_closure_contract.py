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
    changeforge_closure: dict[str, object] = field(default_factory=dict)

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
        validation_result_outcome: str = "",
        validation_result_freshness: str = "",
        validation_result_scope: str = "",
        validation_result_command_kind: str = "",
    ) -> "ClosureContract":
        state = state if isinstance(state, dict) else {}
        capabilities = capabilities or adapter_capabilities_for(runtime)
        profile = _profile(state)
        supported_checks = _list(getattr(capabilities, "supported_checks", ()))
        unsupported_catalog = _list(getattr(capabilities, "unsupported_checks", ()))
        unsupported_checks = _active_unsupported_checks(state, unsupported_catalog)
        degraded_capabilities = _active_degraded_capabilities(state, capabilities, unsupported_checks)
        degraded_capabilities = _unique(
            [
                *degraded_capabilities,
                *_visibility_degraded_capabilities(state, capabilities, profile),
            ]
        )
        if degraded_capabilities and "runtime_adapter_degradation" not in unsupported_checks:
            unsupported_checks = _unique([*unsupported_checks, "runtime_adapter_degradation"])
        residual = _list(validation_broker_residual_risk or [])
        if degraded_capabilities and getattr(capabilities, "default_failure_mode", "") == "fail_open":
            residual.append("adapter fail_open policy active for degraded capabilities")
        if profile == "silent":
            governance = GovernanceClosureContract.from_ledger(
                GovernanceEvidenceLedger(),
                supported_checks=supported_checks,
                unsupported_checks=unsupported_checks,
                degraded_capabilities=degraded_capabilities,
                adapter=capabilities.runtime,
                required_evidence=[],
            )
            final_residual = _unique([*residual, *governance.residual_risk])
            closure_payload = _changeforge_closure(
                governance,
                validation_broker_outcome=validation_broker_outcome,
                validation_result_outcome=validation_result_outcome,
                validation_result_freshness=validation_result_freshness,
                validation_result_scope=validation_result_scope,
                validation_result_command_kind=validation_result_command_kind,
                extra_residual_risk=final_residual,
            )
            return cls(
                adapter=capabilities.runtime,
                supported_checks=supported_checks,
                unsupported_checks=unsupported_checks,
                degraded_capabilities=degraded_capabilities,
                verdict=governance.verdict,
                residual_risk=final_residual,
                requires_route_manifest=False,
                requires_validation_evidence=False,
                requires_residual_risk=False,
                adapter_supports_blocking=capabilities.supports_blocking,
                changeforge_closure=closure_payload,
            )

        engineering = profile == "engineering"
        requires_stage = _requires_stage_route(state, profile)
        requires_route = engineering
        requires_repo = engineering
        requires_preflight = engineering and bool(
            state.get("changed_paths")
            or state.get("deleted_paths")
            or state.get("generated_paths")
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
        if requires_stage:
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
            state=state,
            route_manifest_complete=route_manifest_complete,
            stage_route_present=stage_route_present,
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
        missing = _unique(missing)
        fail_closed_allowed = "stop_closure" in _list(
            getattr(capabilities, "fail_closed_allowed_checks", ())
        )
        status = (
            "block"
            if missing and block_mode and capabilities.supports_blocking and fail_closed_allowed
            else "warn"
            if missing
            else "pass"
        )
        verdict = _compat_verdict(governance.verdict, status, validation_broker_outcome)
        stage_route_residual = (
            ["stage route evidence missing for non-trivial engineering task"]
            if requires_stage and not stage_route_present
            else []
        )
        final_residual = _unique([*residual, *governance.residual_risk, *stage_route_residual])
        closure_payload = _changeforge_closure(
            governance,
            validation_broker_outcome=validation_broker_outcome,
            validation_result_outcome=validation_result_outcome,
            validation_result_freshness=validation_result_freshness,
            validation_result_scope=validation_result_scope,
            validation_result_command_kind=validation_result_command_kind,
            extra_residual_risk=final_residual,
        )
        return cls(
            adapter=capabilities.runtime,
            supported_checks=supported_checks,
            unsupported_checks=unsupported_checks,
            degraded_capabilities=governance.degraded_capabilities or degraded_capabilities,
            verdict=verdict,
            residual_risk=final_residual,
            requires_route_manifest=requires_route,
            requires_stage_route=requires_stage,
            requires_repository_context=requires_repo,
            requires_implementation_preflight=requires_preflight,
            requires_validation_evidence=requires_validation,
            requires_review_evidence=requires_review,
            requires_residual_risk=requires_risk,
            adapter_supports_blocking=capabilities.supports_blocking,
            closure_status=status,
            missing_items=missing,
            changeforge_closure=closure_payload,
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
            "changeforge_closure": dict(self.changeforge_closure),
        }


def _governance_ledger(
    *,
    state: dict | None = None,
    route_manifest_complete: bool,
    stage_route_present: bool,
    repository_context_present: bool,
    implementation_preflight_complete: bool,
    validation_evidence_present: bool,
    review_evidence_present: bool,
    residual_risk_present: bool,
) -> GovernanceEvidenceLedger:
    ledger = GovernanceEvidenceLedger()
    _mark(ledger.route_manifest, route_manifest_complete)
    _mark(ledger.stage_route, stage_route_present)
    _mark(ledger.repository_context, repository_context_present)
    _mark(ledger.implementation_preflight, implementation_preflight_complete)
    _mark(ledger.review, review_evidence_present)
    _mark(ledger.residual_risk, residual_risk_present)
    state = state if isinstance(state, dict) else {}
    changed_paths = _list(state.get("changed_paths"))
    deleted_paths = _list(state.get("deleted_paths"))
    generated_paths = _list(state.get("generated_paths"))
    if changed_paths or deleted_paths or generated_paths:
        ledger.changed_files = changed_paths
        ledger.deleted_files = deleted_paths
        ledger.generated_files = generated_paths
        ledger.changed_files_by_status = {
            "changed": changed_paths,
            "deleted": deleted_paths,
            "generated": generated_paths,
        }
    validation_status = _validation_status_from_results(state.get("validation_results"))
    if validation_status == "stale":
        ledger.validation.merge(
            EvidenceEntry(
                "validation",
                EvidenceStrength.NEGATIVE.value,
                Freshness.STALE.value,
                ["hook-compat"],
                summary="validation stale after material change",
                outcome="stale",
            )
        )
    elif validation_status == "fail":
        ledger.validation.merge(
            EvidenceEntry(
                "validation",
                EvidenceStrength.NEGATIVE.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="validation command reported failure",
                outcome="fail",
            )
        )
    elif validation_status == "pass":
        ledger.validation.merge(
            EvidenceEntry(
                "validation",
                EvidenceStrength.STRONG.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="structured validation result reported pass",
                outcome="pass",
            )
        )
    elif validation_status == "unknown":
        ledger.validation.merge(
            EvidenceEntry(
                "validation",
                EvidenceStrength.PARTIAL.value,
                Freshness.UNKNOWN.value,
                ["hook-compat"],
                summary="validation command observed without outcome",
                outcome="unknown",
            )
        )
    else:
        _mark(ledger.validation, validation_evidence_present)
    review_findings = _list(state.get("review_findings"))
    if review_findings:
        ledger.review.merge(
            EvidenceEntry(
                "review",
                EvidenceStrength.STRONG.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="review finding requires repair evidence",
                outcome="finding",
            )
        )
    if state.get("repair_evidence_seen") or _list(state.get("repair_findings")):
        ledger.repair.merge(
            EvidenceEntry(
                "repair",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
            )
        )
    if state.get("review_after_repair_seen") or state.get("re_review_evidence_seen"):
        ledger.rereview.merge(
            EvidenceEntry(
                "rereview",
                EvidenceStrength.STRONG.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
            )
        )
    if _list(state.get("external_file_changes")):
        ledger.external_file_change.merge(
            EvidenceEntry(
                "external_file_change",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="external file change observed by adapter",
            )
        )
        _mark_validation_stale(
            ledger,
            "external file change after validation",
            "hook-compat",
        )
    if _list(state.get("config_changes")):
        ledger.config_change.merge(
            EvidenceEntry(
                "config_change",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="configuration change observed by adapter",
            )
        )
        _mark_validation_stale(
            ledger,
            "configuration change after validation",
            "hook-compat",
        )
    permission_decisions = _list(state.get("permission_decisions"))
    if permission_decisions:
        permission_denied = _has_permission_denial(permission_decisions)
        ledger.permission.merge(
            EvidenceEntry(
                "permission",
                EvidenceStrength.NEGATIVE.value
                if permission_denied
                else EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="permission denied by runtime"
                if permission_denied
                else "permission decision recorded",
                outcome="deny" if permission_denied else None,
            )
        )
    command_risks = _list(state.get("command_risks"))
    if command_risks:
        ledger.command_risk.merge(
            EvidenceEntry(
                "command_risk",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="command risk recorded",
                outcome=_first_risk(command_risks) or None,
            )
        )
    if _list(state.get("rollback_points")):
        ledger.rollback.merge(
            EvidenceEntry(
                "rollback",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                ["hook-compat"],
                summary="rollback point recorded",
            )
        )
    adapter = state.get("runtime_adapter")
    active_degradation = _runtime_active_degradation(state)
    if isinstance(adapter, dict) and active_degradation:
        ledger.adapter_degradation.merge(
            EvidenceEntry(
                "adapter_degradation",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                active_degradation,
                summary="runtime adapter reported degraded capabilities",
            )
        )
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


def _mark_validation_stale(
    ledger: GovernanceEvidenceLedger,
    reason: str,
    ref: str,
) -> None:
    if ledger.validation.strength == EvidenceStrength.NONE.value:
        return
    if ledger.validation.freshness == Freshness.STALE.value:
        return
    ledger.validation.strength = EvidenceStrength.NEGATIVE.value
    ledger.validation.freshness = Freshness.STALE.value
    ledger.validation.outcome = "stale"
    ledger.validation.summary = reason
    ledger.validation.refs = _unique([*ledger.validation.refs, ref])


def _changeforge_closure(
    governance: GovernanceClosureContract,
    *,
    validation_broker_outcome: str = "",
    validation_result_outcome: str = "",
    validation_result_freshness: str = "",
    validation_result_scope: str = "",
    validation_result_command_kind: str = "",
    extra_residual_risk: list[str] | None = None,
) -> dict[str, object]:
    validation = dict(governance.validation_status)
    if validation_result_outcome:
        validation["outcome"] = validation_result_outcome
    elif validation_broker_outcome and validation.get("outcome") in {"", None}:
        validation["outcome"] = validation_broker_outcome
    if validation_result_freshness:
        validation["freshness"] = validation_result_freshness
    validation["scope"] = validation_result_scope or validation.get("scope") or "unknown"
    validation["command_kind"] = (
        validation_result_command_kind or validation.get("command_kind") or "unknown"
    )
    return {
        "adapter": governance.adapter,
        "verdict": governance.verdict,
        "supported_checks": list(governance.supported_checks),
        "unsupported_checks": list(governance.unsupported_checks),
        "degraded_capabilities": list(governance.degraded_capabilities),
        "present_evidence": list(governance.present_evidence),
        "missing_evidence": list(governance.missing_evidence),
        "negative_evidence": list(governance.negative_evidence),
        "validation": validation,
        "review": dict(governance.review_status),
        "changed_files": dict(governance.changed_files),
        "residual_risk": _unique([*governance.residual_risk, *(_list(extra_residual_risk) or [])]),
        "next_owner": governance.next_owner,
    }


def _profile(state: dict) -> str:
    stage = str(state.get("turn_stage") or "").strip()
    if stage in {"question", "unknown", "no_engineering_action"}:
        return "silent"
    if stage == "" and not state.get("changed_paths"):
        return "silent"
    if stage in {"read", "review", "requirement-intake", "code-review"} and not state.get("changed_paths"):
        return "read_review"
    return "engineering"


def _requires_stage_route(state: dict, profile: str) -> bool:
    if profile != "engineering":
        return False
    if _has_stage_route_skip_reason(state):
        return False
    return bool(
        state.get("changed_paths")
        or state.get("deleted_paths")
        or state.get("generated_paths")
        or state.get("implementation_preflight_required")
        or state.get("edit_without_preflight_seen")
        or state.get("post_edit_confirmed_preflight_gap")
    )


def _has_stage_route_skip_reason(state: dict) -> bool:
    reason_keys = ("stage_route_skip_reason", "stage_route_not_required_reason")
    return any(_nonempty_string(state.get(key)) for key in reason_keys)


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


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


def _active_unsupported_checks(
    state: dict,
    unsupported_catalog: list[str],
) -> list[str]:
    requested = _active_requirement_text(state)
    adapter = state.get("runtime_adapter")
    if isinstance(adapter, dict):
        requested.extend(_list(adapter.get("active_unsupported_checks")))
        requested.extend(_list(adapter.get("required_unsupported_checks")))
    requested.extend(_list(state.get("active_unsupported_checks")))
    requested.extend(_list(state.get("required_unsupported_checks")))
    requested.extend(_list(state.get("closure_required_checks")))
    active: list[str] = []
    for check in unsupported_catalog:
        token = _check_token(check).casefold()
        if any(_check_matches(check, token, item) for item in requested):
            active.append(check)
    return _unique(active)


def _active_degraded_capabilities(
    state: dict,
    capabilities: AdapterCapabilities,
    unsupported_checks: list[str],
) -> list[str]:
    active = _runtime_active_degradation(state)
    active.extend(
        f"{capabilities.runtime}_{_check_token(check)}_unsupported"
        for check in unsupported_checks
    )
    return _unique(active)


def _runtime_active_degradation(state: dict) -> list[str]:
    values = _list(state.get("active_degradation"))
    adapter = state.get("runtime_adapter")
    if isinstance(adapter, dict):
        values.extend(_list(adapter.get("active_degradation")))
        values.extend(_list(adapter.get("degraded_capabilities")))
    return _unique(values)


def _visibility_degraded_capabilities(
    state: dict,
    capabilities: AdapterCapabilities,
    profile: str,
) -> list[str]:
    if profile == "silent":
        return []
    visibility = dict(getattr(capabilities, "visibility", {}) or {})
    adapter = state.get("runtime_adapter")
    if isinstance(adapter, dict) and isinstance(adapter.get("visibility"), dict):
        visibility.update(adapter.get("visibility") or {})
    degraded: list[str] = []
    runtime = str(getattr(capabilities, "runtime", "adapter") or "adapter")
    if visibility.get("validation_outcome") == "none" and (
        state.get("validation_command_seen") or state.get("validation_results")
    ):
        degraded.append(f"{runtime}_validation_outcome_visibility_none")
    if visibility.get("changed_paths") == "none" and (
        state.get("changed_paths")
        or state.get("deleted_paths")
        or state.get("generated_paths")
        or state.get("implementation_preflight_required")
    ):
        degraded.append(f"{runtime}_changed_paths_visibility_none")
    return _unique(degraded)


def _active_requirement_text(state: dict) -> list[str]:
    values: list[str] = []
    for field_name in (
        "suggested_capabilities",
        "suggested_gates",
        "required_gates",
        "closure_risk_surfaces",
        "command_risk_surfaces",
        "risk_surfaces",
        "prompt_signals",
        "reference_loads",
    ):
        values.extend(_list(state.get(field_name)))
    values.extend(_runtime_active_degradation(state))
    context = state.get("active_skill_context")
    if isinstance(context, dict):
        for key, value in context.items():
            values.append(str(key))
            if isinstance(value, dict):
                for child_key, child_value in value.items():
                    values.append(str(child_key))
                    values.append(str(child_value))
            elif isinstance(value, (list, tuple, set)):
                values.extend(str(item) for item in value)
            else:
                values.append(str(value))
    return _unique(values)


def _check_matches(check: str, token: str, value: object) -> bool:
    raw = str(value or "").strip().casefold()
    if not raw:
        return False
    compact = _check_token(raw).casefold()
    return raw == str(check).casefold() or compact == token or token in compact


def _check_token(value: str) -> str:
    return str(value).strip().replace("-", "_").replace(" ", "_")


def _list(values: object) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return _unique([str(item) for item in values])


def _validation_status_from_results(values: object) -> str:
    results = " ".join(_list(values)).casefold()
    if not results:
        return ""
    if "stale_after_material_change" in results or "stale" in results:
        return "stale"
    if "fail" in results or "failed" in results:
        return "fail"
    if "pass" in results or "passed" in results:
        return "pass"
    if "unknown" in results or "candidate" in results:
        return "unknown"
    return ""


def _has_permission_denial(values: list[str]) -> bool:
    return any("deny" in value.casefold() or "denied" in value.casefold() for value in values)


def _first_risk(values: list[str]) -> str:
    if not values:
        return ""
    return values[0].split(":", 1)[0].strip()


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
