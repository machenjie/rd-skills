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
    deleted_files: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    changed_files_by_status: dict[str, list[str]] = field(default_factory=dict)
    validation: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("validation"))
    review: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("review"))
    repair: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("repair"))
    rereview: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("rereview"))
    residual_risk: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("residual_risk"))
    external_file_change: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("external_file_change"))
    config_change: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("config_change"))
    permission: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("permission"))
    command_risk: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("command_risk"))
    rollback: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("rollback"))
    adapter_degradation: EvidenceEntry = field(default_factory=lambda: EvidenceEntry("adapter_degradation"))
    event_count: int = 0
    last_material_change_event: int = 0
    last_validation_event: int = 0

    @classmethod
    def from_telemetry_facts(cls, facts: Iterable[Mapping[str, Any]]) -> "EvidenceLedger":
        ledger = cls()
        for fact in facts:
            ledger.add_fact(fact)
        return ledger

    def add_fact(self, fact: Mapping[str, Any]) -> None:
        event = NormalizedEvent.from_telemetry_fact(fact)
        self.add_normalized_event(event)
        ref = event.event_id
        timestamp = event.timestamp
        self._record_paths(fact)
        self._record_route(fact, ref, timestamp)
        self._record_read(fact, ref, timestamp)
        self._record_repository_context(fact, ref, timestamp)
        self._record_preflight(fact, ref, timestamp)
        self._record_validation(fact, ref, timestamp)
        self._record_review_repair_risk(fact, ref, timestamp)
        self._record_external_config_from_fact(fact, ref, timestamp)
        self._sync_changed_file_sets()

    def add_normalized_event(self, event: NormalizedEvent) -> None:
        """Record canonical runtime event evidence without storing raw payloads."""
        self.event_count += 1
        event_order = self.event_count
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

        if event.read_paths:
            self.read_evidence.merge(
                EvidenceEntry(
                    "read_evidence",
                    EvidenceStrength.STRONG.value,
                    Freshness.CURRENT.value,
                    [ref],
                    timestamp=timestamp,
                )
            )
        elif event.tool_category == "read":
            self.read_evidence.merge(
                EvidenceEntry(
                    "read_evidence",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="read tool observed without bounded read paths",
                    timestamp=timestamp,
                )
            )

        changed = cap_list(event.changed_paths, item_sanitizer=normalize_relative_path)
        deleted = cap_list(event.deleted_paths, item_sanitizer=normalize_relative_path)
        generated = cap_list(event.generated_paths, item_sanitizer=normalize_relative_path)
        if changed or deleted or generated:
            self._record_path_sets(changed=changed, deleted=deleted, generated=generated)

        material_change = bool(changed or deleted or generated)
        if event.event_kind in {EventKind.FILE_CHANGED.value, EventKind.CONFIG_CHANGED.value}:
            material_change = True
        if event.tool_category in {"edit", "write"}:
            material_change = True
            self.implementation_preflight.merge(
                EvidenceEntry(
                    "implementation_preflight",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="material edit requires implementation preflight evidence",
                    timestamp=timestamp,
                )
            )
        if material_change:
            self.last_material_change_event = event_order
            if event.event_kind == EventKind.CONFIG_CHANGED.value:
                self.config_change.merge(
                    EvidenceEntry(
                        "config_change",
                        EvidenceStrength.PARTIAL.value,
                        Freshness.CURRENT.value,
                        [ref],
                        summary="configuration changed after prior evidence",
                        timestamp=timestamp,
                    )
                )
            elif event.event_kind == EventKind.FILE_CHANGED.value and event.tool_category not in {
                "edit",
                "write",
            }:
                self.external_file_change.merge(
                    EvidenceEntry(
                        "external_file_change",
                        EvidenceStrength.PARTIAL.value,
                        Freshness.CURRENT.value,
                        [ref],
                        summary="file changed outside a tracked edit/write event",
                        timestamp=timestamp,
                    )
                )
            if self.last_validation_event and self.last_validation_event < event_order:
                self._mark_validation_stale(ref, timestamp, "material change after validation")

        if event.validation_candidate or event.tool_category == "test":
            self._record_validation_event(event, event_order)

        if event.event_kind == EventKind.POST_TOOL_USE_FAILURE.value:
            self._record_post_tool_failure(event)

        if event.permission_decision:
            outcome = event.permission_decision
            self.permission.merge(
                EvidenceEntry(
                    "permission",
                    EvidenceStrength.NEGATIVE.value if outcome == "deny" else EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary=redact_sensitive_value(event.permission_reason),
                    outcome=outcome,
                    timestamp=timestamp,
                )
            )

        if event.command_risk and event.command_risk != "unknown":
            self.command_risk.merge(
                EvidenceEntry(
                    "command_risk",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="bounded command risk classification",
                    outcome=event.command_risk,
                    timestamp=timestamp,
                )
            )

        if event.rollback_available is not None or event.checkpoint_id:
            available = bool(event.rollback_available)
            self.rollback.merge(
                EvidenceEntry(
                    "rollback",
                    EvidenceStrength.STRONG.value if available else EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="rollback checkpoint observed" if event.checkpoint_id else "",
                    outcome="available" if available else "unknown",
                    timestamp=timestamp,
                )
            )

        self._sync_changed_file_sets()

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
            deleted_files=cap_list(
                data.get("deleted_files") or [],
                item_sanitizer=normalize_relative_path,
            ),
            generated_files=cap_list(
                data.get("generated_files") or [],
                item_sanitizer=normalize_relative_path,
            ),
            changed_files_by_status=_changed_files_by_status(data),
            validation=EvidenceEntry.from_json_dict(data.get("validation") or {}, kind="validation"),
            review=EvidenceEntry.from_json_dict(data.get("review") or {}, kind="review"),
            repair=EvidenceEntry.from_json_dict(data.get("repair") or {}, kind="repair"),
            rereview=EvidenceEntry.from_json_dict(data.get("rereview") or {}, kind="rereview"),
            residual_risk=EvidenceEntry.from_json_dict(data.get("residual_risk") or {}, kind="residual_risk"),
            external_file_change=EvidenceEntry.from_json_dict(
                data.get("external_file_change") or {},
                kind="external_file_change",
            ),
            config_change=EvidenceEntry.from_json_dict(data.get("config_change") or {}, kind="config_change"),
            permission=EvidenceEntry.from_json_dict(data.get("permission") or {}, kind="permission"),
            command_risk=EvidenceEntry.from_json_dict(data.get("command_risk") or {}, kind="command_risk"),
            rollback=EvidenceEntry.from_json_dict(data.get("rollback") or {}, kind="rollback"),
            adapter_degradation=EvidenceEntry.from_json_dict(
                data.get("adapter_degradation") or {},
                kind="adapter_degradation",
            ),
            event_count=_optional_int(data.get("event_count")),
            last_material_change_event=_optional_int(data.get("last_material_change_event")),
            last_validation_event=_optional_int(data.get("last_validation_event")),
        )

    @classmethod
    def from_json(cls, text: str) -> "EvidenceLedger":
        return cls.from_json_dict(json_loads(text))

    def _record_paths(self, fact: Mapping[str, Any]) -> None:
        self._record_path_sets(
            changed=[
                *_object_list(fact.get("changed_paths")),
                *_object_list(fact.get("added_paths")),
                *_object_list(fact.get("modified_paths")),
                *_object_list(fact.get("created_paths")),
            ],
            deleted=[
                *_object_list(fact.get("deleted_paths")),
                *_object_list(fact.get("removed_paths")),
            ],
            generated=[
                *_object_list(fact.get("generated_paths")),
                *_object_list(fact.get("output_paths")),
            ],
        )

    def _record_path_sets(
        self,
        *,
        changed: Iterable[object] = (),
        deleted: Iterable[object] = (),
        generated: Iterable[object] = (),
    ) -> None:
        self.changed_files = cap_list(
            [*self.changed_files, *changed],
            item_sanitizer=normalize_relative_path,
        )
        self.deleted_files = cap_list(
            [*self.deleted_files, *deleted],
            item_sanitizer=normalize_relative_path,
        )
        self.generated_files = cap_list(
            [*self.generated_files, *generated],
            item_sanitizer=normalize_relative_path,
        )
        self._sync_changed_file_sets()

    def _sync_changed_file_sets(self) -> None:
        self.changed_files_by_status = {
            "changed": cap_list(self.changed_files, item_sanitizer=normalize_relative_path),
            "deleted": cap_list(self.deleted_files, item_sanitizer=normalize_relative_path),
            "generated": cap_list(self.generated_files, item_sanitizer=normalize_relative_path),
        }

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
            missing_fields = []
            if not selected:
                missing_fields.append("selected_skills")
            if not capabilities:
                missing_fields.append("selected_capabilities")
            if not references:
                missing_fields.append("required_references")
            if not gates:
                missing_fields.append("required_quality_gates")
            missing_text = ", ".join(missing_fields) if missing_fields else "unknown"
            self.route_manifest.merge(
                EvidenceEntry(
                    "route_manifest",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary=(
                        "route manifest detected but required closure fields were incomplete: "
                        f"{missing_text}"
                    ),
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
        review_findings = _list_field(fact, "review_findings")
        if fact.get("review_finding_seen"):
            review_findings = cap_list([*review_findings, "finding"])
        if review_findings:
            self.review.merge(
                EvidenceEntry(
                    "review",
                    EvidenceStrength.STRONG.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="review finding requires repair evidence",
                    outcome="finding",
                    timestamp=timestamp,
                )
            )
        elif fact.get("review_evidence_seen") or _list_field(fact, "review_targets"):
            self.review.merge(
                EvidenceEntry("review", EvidenceStrength.STRONG.value, Freshness.CURRENT.value, [ref], timestamp=timestamp)
            )
        if fact.get("repair_evidence_seen") or _list_field(fact, "repair_findings"):
            self.repair.merge(
                EvidenceEntry("repair", EvidenceStrength.PARTIAL.value, Freshness.CURRENT.value, [ref], timestamp=timestamp)
            )
        if (
            fact.get("review_after_repair_seen")
            or fact.get("re_review_evidence_seen")
            or fact.get("rereview_evidence_seen")
        ):
            self.rereview.merge(
                EvidenceEntry(
                    "rereview",
                    EvidenceStrength.STRONG.value,
                    Freshness.CURRENT.value,
                    [ref],
                    timestamp=timestamp,
                )
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

    def _record_external_config_from_fact(
        self,
        fact: Mapping[str, Any],
        ref: str,
        timestamp: str | None,
    ) -> None:
        external_paths = [
            *_object_list(fact.get("external_changed_paths")),
            *_object_list(fact.get("external_file_changes")),
        ]
        config_paths = [
            *_object_list(fact.get("config_changed_paths")),
            *_object_list(fact.get("config_changes")),
        ]
        if fact.get("external_file_change_seen") or external_paths:
            self.external_file_change.merge(
                EvidenceEntry(
                    "external_file_change",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="external file change invalidates prior validation freshness",
                    timestamp=timestamp,
                )
            )
            self._record_path_sets(changed=external_paths)
            if self.last_validation_event:
                self._mark_validation_stale(ref, timestamp, "external file change after validation")
        if fact.get("config_change_seen") or config_paths:
            self.config_change.merge(
                EvidenceEntry(
                    "config_change",
                    EvidenceStrength.PARTIAL.value,
                    Freshness.CURRENT.value,
                    [ref],
                    summary="configuration change invalidates prior validation freshness",
                    timestamp=timestamp,
                )
            )
            self._record_path_sets(changed=config_paths)
            if self.last_validation_event:
                self._mark_validation_stale(ref, timestamp, "configuration change after validation")

    def _record_validation_event(self, event: NormalizedEvent, event_order: int) -> None:
        outcome = event.validation_outcome
        if outcome is None:
            if event.command_outcome == "pass":
                outcome = "pass"
            elif event.command_outcome in {"fail", "timeout", "cancelled"}:
                outcome = "fail"
            elif event.command_outcome == "not_observable":
                outcome = "unknown"
        freshness = event.validation_freshness or Freshness.CURRENT.value
        if self.last_material_change_event and event_order < self.last_material_change_event:
            freshness = Freshness.STALE.value

        if outcome == "pass":
            strength = EvidenceStrength.STRONG.value
        elif outcome == "fail":
            strength = EvidenceStrength.NEGATIVE.value
        elif outcome in {"not_run", "not_verified"}:
            strength = EvidenceStrength.WEAK.value
        else:
            strength = EvidenceStrength.WEAK.value
            outcome = "no_outcome"

        summary = ""
        if freshness == Freshness.STALE.value and strength == EvidenceStrength.STRONG.value:
            strength = EvidenceStrength.NEGATIVE.value
            outcome = "stale"
            summary = "stale"

        self.validation.merge(
            EvidenceEntry(
                "validation",
                strength,
                freshness,
                [event.event_id],
                summary=summary,
                outcome=outcome,
                timestamp=event.timestamp,
            )
        )
        self.last_validation_event = event_order

    def _record_post_tool_failure(self, event: NormalizedEvent) -> None:
        if event.validation_candidate or event.tool_category == "test":
            self.validation.merge(
                EvidenceEntry(
                    "validation",
                    EvidenceStrength.NEGATIVE.value,
                    Freshness.CURRENT.value,
                    [event.event_id],
                    summary="validation tool failed",
                    outcome="fail",
                    timestamp=event.timestamp,
                )
            )
            return
        self.adapter_degradation.merge(
            EvidenceEntry(
                "adapter_degradation",
                EvidenceStrength.PARTIAL.value,
                Freshness.CURRENT.value,
                [event.event_id],
                summary="post-tool failure limited runtime evidence",
                timestamp=event.timestamp,
            )
        )

    def _mark_validation_stale(self, ref: str, timestamp: str | None, reason: str) -> None:
        if self.validation.strength == EvidenceStrength.NONE.value:
            return
        if self.validation.freshness == Freshness.STALE.value:
            return
        self.validation.strength = EvidenceStrength.NEGATIVE.value
        self.validation.freshness = Freshness.STALE.value
        self.validation.outcome = "stale"
        self.validation.summary = reason
        self.validation.timestamp = timestamp or self.validation.timestamp
        self.validation.refs = cap_list([*self.validation.refs, ref])


def _list_field(fact: Mapping[str, Any], key: str) -> list[str]:
    return cap_list(fact.get(key) or [])


def _object_list(value: object) -> list[object]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if value:
        return [value]
    return []


def _changed_files_by_status(data: Mapping[str, Any]) -> dict[str, list[str]]:
    raw = data.get("changed_files_by_status")
    if not isinstance(raw, Mapping):
        return {
            "changed": cap_list(data.get("changed_files") or [], item_sanitizer=normalize_relative_path),
            "deleted": cap_list(data.get("deleted_files") or [], item_sanitizer=normalize_relative_path),
            "generated": cap_list(data.get("generated_files") or [], item_sanitizer=normalize_relative_path),
        }
    return {
        "changed": cap_list(raw.get("changed") or [], item_sanitizer=normalize_relative_path),
        "deleted": cap_list(raw.get("deleted") or [], item_sanitizer=normalize_relative_path),
        "generated": cap_list(raw.get("generated") or [], item_sanitizer=normalize_relative_path),
    }


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


def _optional_int(value: object) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0
