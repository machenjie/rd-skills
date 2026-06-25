"""Closure contract primitives built from governance evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from .evidence import EvidenceLedger, EvidenceStrength, Freshness
from .privacy import cap_list, redact_sensitive_value
from .serialization import json_dumps, json_loads, to_json_dict


class ClosureVerdict(str, Enum):
    READY = "ready"
    NEEDS_VALIDATION = "needs_validation"
    NEEDS_REVIEW = "needs_review"
    NEEDS_REPAIR = "needs_repair"
    BLOCKED = "blocked"
    DEGRADED_READY = "degraded_ready"


@dataclass
class ClosureContract:
    adapter: str = ""
    supported_checks: list[str] = field(default_factory=list)
    unsupported_checks: list[str] = field(default_factory=list)
    degraded_capabilities: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    present_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    negative_evidence: list[str] = field(default_factory=list)
    freshness: dict[str, str] = field(default_factory=dict)
    validation_status: dict[str, str] = field(default_factory=dict)
    review_status: dict[str, Any] = field(default_factory=dict)
    changed_files: dict[str, list[str]] = field(default_factory=dict)
    verdict: str = ClosureVerdict.NEEDS_VALIDATION.value
    residual_risk: list[str] = field(default_factory=list)
    next_owner: str = "agent"

    @classmethod
    def from_ledger(
        cls,
        ledger: EvidenceLedger,
        *,
        supported_checks: Iterable[object] = (),
        unsupported_checks: Iterable[object] = (),
        degraded_capabilities: Iterable[object] = (),
        adapter: str = "",
        required_evidence: Iterable[object] = ("route_manifest", "validation", "residual_risk"),
        next_owner: str = "agent",
    ) -> "ClosureContract":
        required = cap_list(required_evidence)
        supported = cap_list(supported_checks)
        unsupported = cap_list(unsupported_checks)
        degraded = cap_list(degraded_capabilities)
        if degraded and "runtime_adapter_degradation" not in unsupported:
            unsupported = cap_list([*unsupported, "runtime_adapter_degradation"])
        if ledger.adapter_degradation.strength != EvidenceStrength.NONE.value:
            unsupported = cap_list([*unsupported, "runtime_adapter_degradation"])
            degraded = cap_list([*degraded, *ledger.adapter_degradation.refs])

        present: list[str] = []
        missing: list[str] = []
        negative: list[str] = []
        freshness: dict[str, str] = {}
        residual: list[str] = []

        entries = {
            "route_manifest": ledger.route_manifest,
            "read_evidence": ledger.read_evidence,
            "repository_context": ledger.repository_context,
            "implementation_preflight": ledger.implementation_preflight,
            "validation": ledger.validation,
            "review": ledger.review,
            "repair": ledger.repair,
            "rereview": ledger.rereview,
            "residual_risk": ledger.residual_risk,
            "external_file_change": ledger.external_file_change,
            "config_change": ledger.config_change,
            "permission": ledger.permission,
            "command_risk": ledger.command_risk,
            "rollback": ledger.rollback,
            "adapter_degradation": ledger.adapter_degradation,
        }

        for name, entry in entries.items():
            if entry.strength != EvidenceStrength.NONE.value:
                freshness[name] = entry.freshness
            if entry.strength == EvidenceStrength.NEGATIVE.value:
                negative.append(name)
                if entry.summary:
                    residual.append(f"{name}: {entry.summary}")
                if name == "validation" and entry.freshness == Freshness.STALE.value:
                    missing.append("validation")
            elif entry.is_closure_evidence:
                present.append(name)

        for name in required:
            entry = entries.get(name)
            if entry is None:
                missing.append(name)
                continue
            if entry.strength == EvidenceStrength.NEGATIVE.value:
                if name not in negative:
                    negative.append(name)
                continue
            if not entry.is_closure_evidence:
                missing.append(name)
                if entry.strength == EvidenceStrength.WEAK.value and name == "validation":
                    residual.append("validation command was observed without outcome")
                if entry.freshness == Freshness.STALE.value:
                    residual.append(f"{name} is stale")

        changed_files = _changed_files(ledger)
        has_material_change = any(changed_files.values()) or any(
            entry.strength != EvidenceStrength.NONE.value
            for entry in (ledger.external_file_change, ledger.config_change)
        )
        validation_current = ledger.validation.is_closure_evidence
        review_has_finding = ledger.review.outcome == "finding"
        repair_present = ledger.repair.strength != EvidenceStrength.NONE.value
        rereview_present = ledger.rereview.is_closure_evidence
        dangerous_permission_denied = (
            ledger.permission.outcome == "deny"
            and ledger.command_risk.outcome in {"destructive", "release", "migration"}
        )
        preflight_negative = ledger.implementation_preflight.strength == EvidenceStrength.NEGATIVE.value
        preflight_required_missing = (
            "implementation_preflight" in required
            and has_material_change
            and ledger.implementation_preflight.strength == EvidenceStrength.PARTIAL.value
            and "implementation_preflight" not in present
        )

        if has_material_change and not validation_current and "validation" not in missing:
            missing.append("validation")
            residual.append("changed files require fresh validation evidence")
        if review_has_finding and not repair_present and "repair" not in missing:
            missing.append("repair")
            residual.append("review finding requires repair evidence")
        if repair_present and not rereview_present and "review" not in missing:
            missing.append("review")
            residual.append("repair evidence requires re-review")
        if dangerous_permission_denied:
            negative.append("permission")
            residual.append("permission denied for dangerous command class")

        if unsupported:
            residual.append("unsupported runtime checks remain")
        verdict = _verdict(
            required,
            missing,
            negative,
            unsupported,
            validation_stale=ledger.validation.freshness == Freshness.STALE.value,
            validation_failed=ledger.validation.outcome in {"fail", "failed"},
            review_has_finding=review_has_finding,
            repair_present=repair_present,
            rereview_present=rereview_present,
            dangerous_permission_denied=dangerous_permission_denied,
            preflight_negative=preflight_negative,
            preflight_required_missing=preflight_required_missing,
        )
        effective_next_owner = next_owner
        if next_owner == "agent":
            if review_has_finding and not repair_present:
                effective_next_owner = "repair"
            elif repair_present and not rereview_present:
                effective_next_owner = "reviewer"
        return cls(
            adapter=redact_sensitive_value(adapter),
            supported_checks=supported,
            unsupported_checks=unsupported,
            degraded_capabilities=degraded,
            required_evidence=required,
            present_evidence=cap_list(present),
            missing_evidence=cap_list(missing),
            negative_evidence=cap_list(negative),
            freshness={key: str(value) for key, value in sorted(freshness.items())},
            validation_status={
                "strength": ledger.validation.strength,
                "freshness": ledger.validation.freshness,
                "outcome": ledger.validation.outcome or "",
            },
            review_status={
                "review_outcome": ledger.review.outcome or "",
                "repair_present": repair_present,
                "rereview_present": rereview_present,
            },
            changed_files=changed_files,
            verdict=verdict,
            residual_risk=cap_list(residual),
            next_owner=redact_sensitive_value(effective_next_owner) or "agent",
        )

    def to_json_dict(self) -> dict[str, Any]:
        return to_json_dict(self)

    def to_json(self) -> str:
        return json_dumps(self)

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any]) -> "ClosureContract":
        freshness = data.get("freshness")
        return cls(
            adapter=redact_sensitive_value(data.get("adapter")),
            supported_checks=cap_list(data.get("supported_checks") or []),
            unsupported_checks=cap_list(data.get("unsupported_checks") or []),
            degraded_capabilities=cap_list(data.get("degraded_capabilities") or []),
            required_evidence=cap_list(data.get("required_evidence") or []),
            present_evidence=cap_list(data.get("present_evidence") or []),
            missing_evidence=cap_list(data.get("missing_evidence") or []),
            negative_evidence=cap_list(data.get("negative_evidence") or []),
            freshness={
                str(key): str(value)
                for key, value in (freshness.items() if isinstance(freshness, dict) else [])
            },
            validation_status=_string_mapping(data.get("validation_status")),
            review_status=_review_mapping(data.get("review_status")),
            changed_files=_changed_files_mapping(data.get("changed_files")),
            verdict=_closure_verdict(data.get("verdict")),
            residual_risk=cap_list(data.get("residual_risk") or []),
            next_owner=redact_sensitive_value(data.get("next_owner")) or "agent",
        )

    @classmethod
    def from_json(cls, text: str) -> "ClosureContract":
        return cls.from_json_dict(json_loads(text))


def _verdict(
    required: list[str],
    missing: list[str],
    negative: list[str],
    unsupported: list[str],
    *,
    validation_stale: bool = False,
    validation_failed: bool = False,
    review_has_finding: bool = False,
    repair_present: bool = False,
    rereview_present: bool = False,
    dangerous_permission_denied: bool = False,
    preflight_negative: bool = False,
    preflight_required_missing: bool = False,
) -> str:
    if validation_failed or dangerous_permission_denied or preflight_negative:
        return ClosureVerdict.BLOCKED.value
    if validation_stale:
        return ClosureVerdict.NEEDS_VALIDATION.value
    if review_has_finding and not repair_present:
        return ClosureVerdict.NEEDS_REPAIR.value
    if repair_present and not rereview_present:
        return ClosureVerdict.NEEDS_REVIEW.value
    if negative:
        if "repair" in negative:
            return ClosureVerdict.NEEDS_REPAIR.value
        return ClosureVerdict.BLOCKED.value
    if "validation" in missing:
        return ClosureVerdict.NEEDS_VALIDATION.value
    if preflight_required_missing:
        return ClosureVerdict.NEEDS_REVIEW.value
    if "review" in missing:
        return ClosureVerdict.NEEDS_REVIEW.value
    if "repair" in required and "repair" in missing:
        return ClosureVerdict.NEEDS_REPAIR.value
    if missing:
        return ClosureVerdict.NEEDS_VALIDATION.value
    if unsupported:
        return ClosureVerdict.DEGRADED_READY.value
    return ClosureVerdict.READY.value


def _closure_verdict(value: object) -> str:
    text = str(value or "").strip()
    allowed = {item.value for item in ClosureVerdict}
    return text if text in allowed else ClosureVerdict.NEEDS_VALIDATION.value


def _changed_files(ledger: EvidenceLedger) -> dict[str, list[str]]:
    if ledger.changed_files_by_status:
        return _changed_files_mapping(ledger.changed_files_by_status)
    return {
        "changed": cap_list(ledger.changed_files),
        "deleted": cap_list(ledger.deleted_files),
        "generated": cap_list(ledger.generated_files),
    }


def _changed_files_mapping(value: object) -> dict[str, list[str]]:
    raw = value if isinstance(value, Mapping) else {}
    if not raw:
        return {}
    return {
        "changed": cap_list(raw.get("changed") or []),
        "deleted": cap_list(raw.get("deleted") or []),
        "generated": cap_list(raw.get("generated") or []),
    }


def _string_mapping(value: object) -> dict[str, str]:
    raw = value if isinstance(value, Mapping) else {}
    return {str(key): redact_sensitive_value(item) for key, item in raw.items()}


def _review_mapping(value: object) -> dict[str, Any]:
    raw = value if isinstance(value, Mapping) else {}
    if not raw:
        return {}
    return {
        "review_outcome": redact_sensitive_value(raw.get("review_outcome")),
        "repair_present": bool(raw.get("repair_present")),
        "rereview_present": bool(raw.get("rereview_present")),
    }
