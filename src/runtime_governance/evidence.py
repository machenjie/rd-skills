"""Evidence ledger primitives for runtime governance closure."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from .events import EventKind, NormalizedEvent
from .privacy import cap_list, normalize_relative_path, redact_sensitive_value
from .serialization import json_dumps, json_loads, to_json_dict


class EvidenceStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    PARTIAL = "partial"
    STRONG = "strong"
    NEGATIVE = "negative"


class Freshness(str, Enum):
    UNKNOWN = "unknown"
    CURRENT = "current"
    STALE = "stale"
    NOT_APPLICABLE = "not_applicable"


_STRENGTH_ORDER = {
    EvidenceStrength.NONE.value: 0,
    EvidenceStrength.WEAK.value: 1,
    EvidenceStrength.PARTIAL.value: 2,
    EvidenceStrength.STRONG.value: 3,
    EvidenceStrength.NEGATIVE.value: 4,
}


@dataclass
class EvidenceEntry:
    kind: str
    strength: str = EvidenceStrength.NONE.value
    freshness: str = Freshness.UNKNOWN.value
    refs: list[str] = field(default_factory=list)
    summary: str = ""
    outcome: str | None = None
    timestamp: str | None = None

    def merge(self, other: "EvidenceEntry") -> None:
        if (
            self.strength == EvidenceStrength.NEGATIVE.value
            and self.freshness == Freshness.STALE.value
            and other.strength == EvidenceStrength.STRONG.value
            and other.freshness == Freshness.CURRENT.value
        ):
            should_replace = True
        elif (
            other.strength == EvidenceStrength.NEGATIVE.value
            and other.freshness == Freshness.STALE.value
            and self.is_closure_evidence
        ):
            should_replace = False
        else:
            should_replace = _STRENGTH_ORDER.get(other.strength, 0) >= _STRENGTH_ORDER.get(
                self.strength,
                0,
            )
        if should_replace:
            self.strength = other.strength
            self.freshness = other.freshness
            self.outcome = other.outcome
            self.summary = other.summary or self.summary
            self.timestamp = other.timestamp or self.timestamp
        self.refs = cap_list([*self.refs, *other.refs])

    @property
    def is_closure_evidence(self) -> bool:
        return self.strength == EvidenceStrength.STRONG.value and self.freshness in {
            Freshness.CURRENT.value,
            Freshness.NOT_APPLICABLE.value,
        }

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any], *, kind: str = "") -> "EvidenceEntry":
        return cls(
            kind=str(data.get("kind") or kind),
            strength=_strength(data.get("strength")),
            freshness=_freshness(data.get("freshness")),
            refs=cap_list(data.get("refs") or []),
            summary=redact_sensitive_value(data.get("summary")),
            outcome=_maybe_str(data.get("outcome")),
            timestamp=_maybe_str(data.get("timestamp")),
        )


@dataclass
class EvidenceLedger:
    route_manifest: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("route_manifest"))
    read_evidence: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("read_evidence"))
    repository_context: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("repository_context"))
    implementation_preflight: EvidenceEntry = field(
        default_factory=lambda: EvidenceEntry("implementation_preflight")
    )
    changed_files: list[str] = field(default_factory=list)
    validation: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("validation"))
    review: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("review"))
    repair: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("repair"))
    residual_risk: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("residual_risk"))
    adapter_degradation: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("adapter_degradation"))

    @classmethod
    def from_telemetry_facts(cls, facts: Iterable[Mapping[str, Any]]) -> "EvidenceLedger":
        ledger = cls()
        for fact in facts:
            ledger.add_fact(fact)
        return ledger

    def add_fact(self, fact: Mapping[str, Any]) -> None:
        event = NormalizedEvent.from_telemetry_fact(fact)
        ref = event.event_id
        timestamp = event.timestamp
        if event.event_kind == EventKind.UNKNOWN.value or event.capability_degradation:
            self.adapter_degradation.merge(
                EvidenceEntry(
                    "adapter_degradation",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="adapter reported unsupported or degraded runtime event",
                    timestamp=timestamp,
                )
            )

        self._record_paths(fact)
        self._record_route(fact, ref, timestamp)
        self._record_read(fact, ref, timestamp)
        self._record_repository_context(fact, ref, timestamp)
        self._record_preflight(fact, ref, timestamp)
        self._record_validation(fact, ref, timestamp)
        self._record_review_repair_risk(fact, ref, timestamp)

    def to_json_dict(self) -> dict[str, Any]:
        return to_json_dict(self)

    def to_json(self) -> str:
        return json_dumps(self)

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any]) -> "EvidenceLedger":
        return cls(
            route_manifest=EvidenceEntry.from_json_dict(data.get("route_manifest") or {}, kind="route_manifest"),
            read_evidence=EvidenceEntry.from_json_dict(data.get("read_evidence") or {}, kind="read_evidence"),
            repository_context=EvidenceEntry.from_json_dict(
                data.get("repository_context") or {},
                kind="repository_context",
            ),
            implementation_preflight=EvidenceEntry.from_json_dict(
                data.get("implementation_preflight") or {},
                kind="implementation_preflight",
            ),
            changed_files=cap_list(
                data.get("changed_files") or [],
                item_sanitizer=normalize_relative_path,
            ),
            validation=EvidenceEntry.from_json_dict(data.get("validation") or {}, kind="validation"),
            review=EvidenceEntry.from_json_dict(data.get("review") or {}, kind="review"),
            repair=EvidenceEntry.from_json_dict(data.get("repair") or {}, kind="repair"),
            residual_risk=EvidenceEntry.from_json_dict(data.get("residual_risk") or {}, kind="residual_risk"),
            adapter_degradation=EvidenceEntry.from_json_dict(
                data.get("adapter_degradation") or {},
                kind="adapter_degradation",
            ),
        )

    @classmethod
    def from_json(cls, text: str) -> "EvidenceLedger":
        return cls.from_json_dict(json_loads(text))

    def _record_paths(self, fact: Mapping[str, Any]) -> None:
        paths: list[object] = []
        for key in ("changed_paths", "added_paths"):
            value = fact.get(key)
            if isinstance(value, (list, tuple, set)):
                paths.extend(value)
            elif value:
                paths.append(value)
        self.changed_files = cap_list(
            [*self.changed_files, *paths],
            item_sanitizer=normalize_relative_path,
        )

    def _record_route(self, fact: Mapping[str, Any], ref: str, timestamp: str | None) -> None:
        selected = _list_field(fact, "manifest_selected_skills") or _list_field(fact, "selected_skills")
        capabilities = _list_field(fact, "manifest_selected_capabilities") or _list_field(
            fact,
            "selected_capabilities",
        )
        references = _list_field(fact, "manifest_required_references") or _list_field(
            fact,
            "required_references",
        )
        gates = _list_field(fact, "manifest_required_quality_gates") or _list_field(
            fact,
            "required_quality_gates",
        )
        if fact.get("route_manifest_detected") and selected and capabilities and references and gates:
            self.route_manifest.merge(
                EvidenceEntry(
                    "route_manifest",
                    EvidenceStrength.STRONG.value,
                    Freshness.CURRENT.value,
                    [ref],
                    timestamp=timestamp,
                )
            )
        elif fact.get("route_manifest_detected"):
            self.route_manifest.merge(
                EvidenceEntry(
                    "route_manifest",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="route manifest detected but required closure fields were incomplete",
                    timestamp=timestamp,
                )
            )

    def _record_read(self, fact: Mapping[str, Any], ref: str, timestamp: str | None) -> None:
        read_paths = _list_field(fact, "read_paths")
        if fact.get("read_evidence_seen") and read_paths:
            strength = EvidenceStrength.STRONG.value
        elif fact.get("read_evidence_seen") or read_paths:
            strength = EvidenceStrength.PARTIAL.value
        else:
            return
        self.read_evidence.merge(
            EvidenceEntry("read_evidence", strength, Freshness.CURRENT.value, [ref], timestamp=timestamp)
        )

    def _record_repository_context(self, fact: Mapping[str, Any], ref: str, timestamp: str | None) -> None:
        if fact.get("repository_context_seen"):
            self.repository_context.merge(
                EvidenceEntry(
                    "repository_context",
                    EvidenceStrength.STRONG.value,
                    Freshness.CURRENT.value,
                    [ref],
                    timestamp=timestamp,
                )
            )
        elif fact.get("repository_context_required"):
            self.repository_context.merge(
                EvidenceEntry(
                    "repository_context",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="repository context was required but not complete",
                    timestamp=timestamp,
                )
            )

    def _record_preflight(self, fact: Mapping[str, Any], ref: str, timestamp: str | None) -> None:
        if fact.get("implementation_preflight_complete"):
            entry = EvidenceEntry(
                "implementation_preflight",
                EvidenceStrength.STRONG.value,
                Freshness.CURRENT.value,
                [ref],
                timestamp=timestamp,
            )
        elif fact.get("edit_without_preflight_seen") or fact.get("post_edit_confirmed_preflight_gap"):
            entry = EvidenceEntry(
                "implementation_preflight",
                EvidenceStrength.NEGATIVE.value,
                Freshness.CURRENT.value,
                [ref],
                summary="material edit without complete implementation preflight",
                outcome="missing",
                timestamp=timestamp,
            )
        elif fact.get("implementation_preflight_seen") or fact.get("implementation_preflight_required"):
            entry = EvidenceEntry(
                "implementation_preflight",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                [ref],
                timestamp=timestamp,
            )
        else:
            return
        self.implementation_preflight.merge(entry)

    def _record_validation(self, fact: Mapping[str, Any], ref: str, timestamp: str | None) -> None:
        broker_entry = _validation_entry_from_broker_fact(fact, ref, timestamp)
        if broker_entry is not None:
            self.validation.merge(broker_entry)
            if _broker_has_validation_blocker(fact):
                return

        outcome = str(fact.get("validation_result_outcome") or "").strip().lower()
        strength = str(fact.get("validation_result_evidence_strength") or "").strip().lower()
        negative_reason = str(fact.get("validation_result_negative_reason") or "").strip()
        fresh = str(fact.get("validation_result_fresh_after_last_edit") or "").strip().lower()
        coverage = str(fact.get("validation_result_coverage_aligned") or "").strip().lower()
        command_seen = bool(fact.get("validation_command_detected") or fact.get("validation_command_seen"))
        evidence_seen = bool(fact.get("validation_evidence_detected") or fact.get("validation_seen"))

        freshness = Freshness.UNKNOWN.value
        if fresh == "true":
            freshness = Freshness.CURRENT.value
        elif fresh == "false":
            freshness = Freshness.STALE.value
        elif fresh == "not_applicable":
            freshness = Freshness.NOT_APPLICABLE.value

        if outcome in {"fail", "failed"} or strength == EvidenceStrength.NEGATIVE.value or negative_reason:
            entry_strength = EvidenceStrength.NEGATIVE.value
        elif outcome == "pass" and strength == EvidenceStrength.STRONG.value and evidence_seen and coverage != "false":
            entry_strength = EvidenceStrength.STRONG.value
            if freshness == Freshness.UNKNOWN.value:
                freshness = Freshness.CURRENT.value
        elif command_seen and not outcome:
            entry_strength = EvidenceStrength.WEAK.value
            outcome = "no_outcome"
        elif command_seen and outcome in {"unknown", ""}:
            entry_strength = EvidenceStrength.WEAK.value
            outcome = "no_outcome"
        elif evidence_seen:
            entry_strength = EvidenceStrength.PARTIAL.value
        else:
            return

        if freshness == Freshness.STALE.value and entry_strength == EvidenceStrength.STRONG.value:
            entry_strength = EvidenceStrength.NEGATIVE.value
            negative_reason = negative_reason or "stale"

        self.validation.merge(
            EvidenceEntry(
                "validation",
                entry_strength,
                freshness,
                [ref],
                summary=negative_reason,
                outcome=outcome or None,
                timestamp=timestamp,
            )
        )

    def _record_review_repair_risk(self, fact: Mapping[str, Any], ref: str, timestamp: str | None) -> None:
        if fact.get("review_evidence_seen") or _list_field(fact, "review_targets"):
            self.review.merge(
                EvidenceEntry("review", EvidenceStrength.STRONG.value, Freshness.CURRENT.value, [ref], timestamp=timestamp)
            )
        if fact.get("repair_evidence_seen") or _list_field(fact, "repair_findings"):
            self.repair.merge(
                EvidenceEntry("repair", EvidenceStrength.PARTIAL.value, Freshness.CURRENT.value, [ref], timestamp=timestamp)
            )
        if fact.get("residual_risk_detected") or fact.get("residual_risk_seen"):
            self.residual_risk.merge(
                EvidenceEntry(
                    "residual_risk",
                    EvidenceStrength.STRONG.value,
                    Freshness.CURRENT.value,
                    [ref],
                    timestamp=timestamp,
                )
            )


def _list_field(fact: Mapping[str, Any], key: str) -> list[str]:
    return cap_list(fact.get(key) or [])


def _validation_entry_from_broker_fact(
    fact: Mapping[str, Any],
    ref: str,
    timestamp: str | None,
) -> EvidenceEntry | None:
    broker_outcome = str(fact.get("validation_broker_closure_outcome") or "").strip().lower()
    broker_negative = _list_field(fact, "validation_broker_negative_evidence")
    ledger = fact.get("validation_broker_command_ledger")
    ledger_items = ledger if isinstance(ledger, list) else []
    if not broker_outcome and not broker_negative and not ledger_items:
        return None

    ledger_outcomes = {
        str(item.get("outcome") or "").strip().lower()
        for item in ledger_items
        if isinstance(item, Mapping)
    }
    freshness = Freshness.UNKNOWN.value
    if "stale" in ledger_outcomes or "stale_validation" in broker_negative:
        freshness = Freshness.STALE.value
    elif "passed" in ledger_outcomes or broker_outcome in {"ready", "degraded_ready"}:
        freshness = Freshness.CURRENT.value

    validation_blockers = {
        "missing_validation",
        "validation_command_without_outcome",
        "validation_not_run",
        "validation_failed",
        "stale_validation",
        "coverage_mismatch",
        "targeted_check_reported_as_full",
        "changed_path_without_validator",
    }
    negative_blockers = validation_blockers & set(broker_negative)
    if {"failed", "stale"} & ledger_outcomes or {"validation_failed", "stale_validation"} & set(
        broker_negative
    ):
        strength = EvidenceStrength.NEGATIVE.value
    elif negative_blockers:
        strength = EvidenceStrength.WEAK.value
    elif "passed" in ledger_outcomes and broker_outcome in {"ready", "degraded_ready"}:
        strength = EvidenceStrength.STRONG.value
    elif ledger_items or broker_outcome == "needs_validation":
        strength = EvidenceStrength.WEAK.value
    else:
        strength = EvidenceStrength.PARTIAL.value

    outcome = None
    if "failed" in ledger_outcomes:
        outcome = "failed"
    elif "stale" in ledger_outcomes:
        outcome = "stale"
    elif "not_verified" in ledger_outcomes or "unknown" in ledger_outcomes:
        outcome = "no_outcome"
    elif "not_run" in ledger_outcomes:
        outcome = "not_run"
    elif "passed" in ledger_outcomes:
        outcome = "pass"

    return EvidenceEntry(
        "validation",
        strength,
        freshness,
        [ref],
        summary=",".join(broker_negative[:5]),
        outcome=outcome,
        timestamp=timestamp,
    )


def _broker_has_validation_blocker(fact: Mapping[str, Any]) -> bool:
    blockers = {
        "missing_validation",
        "validation_command_without_outcome",
        "validation_not_run",
        "validation_failed",
        "stale_validation",
        "coverage_mismatch",
        "targeted_check_reported_as_full",
        "changed_path_without_validator",
    }
    return bool(blockers & set(_list_field(fact, "validation_broker_negative_evidence")))


def _strength(value: object) -> str:
    text = str(value or "").strip()
    return text if text in _STRENGTH_ORDER else EvidenceStrength.NONE.value


def _freshness(value: object) -> str:
    text = str(value or "").strip()
    allowed = {item.value for item in Freshness}
    return text if text in allowed else Freshness.UNKNOWN.value


def _maybe_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
