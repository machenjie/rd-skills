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
            "residual_risk": ledger.residual_risk,
            "adapter_degradation": ledger.adapter_degradation,
        }

        for name, entry in entries.items():
            if entry.strength != EvidenceStrength.NONE.value:
                freshness[name] = entry.freshness
            if entry.strength == EvidenceStrength.NEGATIVE.value:
                negative.append(name)
                if entry.summary:
                    residual.append(f"{name}: {entry.summary}")
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

        if unsupported:
            residual.append("unsupported runtime checks remain")
        verdict = _verdict(required, missing, negative, unsupported)
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
            verdict=verdict,
            residual_risk=cap_list(residual),
            next_owner=redact_sensitive_value(next_owner) or "agent",
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
            verdict=_closure_verdict(data.get("verdict")),
            residual_risk=cap_list(data.get("residual_risk") or []),
            next_owner=redact_sensitive_value(data.get("next_owner")) or "agent",
        )

    @classmethod
    def from_json(cls, text: str) -> "ClosureContract":
        return cls.from_json_dict(json_loads(text))


def _verdict(required: list[str], missing: list[str], negative: list[str], unsupported: list[str]) -> str:
    if negative:
        if "repair" in negative:
            return ClosureVerdict.NEEDS_REPAIR.value
        return ClosureVerdict.BLOCKED.value
    if "validation" in missing:
        return ClosureVerdict.NEEDS_VALIDATION.value
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
