from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import (  # noqa: E402
    ClosureContract,
    ClosureVerdict,
    EventKind,
    EvidenceLedger,
    EvidenceStrength,
    Freshness,
    GateOutcome,
    GateResult,
    NormalizedEvent,
)


def _event(
    event_id: str,
    kind: str,
    *,
    tool_category: str | None = None,
    changed_paths: list[str] | None = None,
    read_paths: list[str] | None = None,
    command_outcome: str | None = None,
    validation_candidate: bool = False,
    validation_outcome: str | None = None,
    validation_freshness: str | None = None,
    permission_decision: str | None = None,
    permission_reason: str | None = None,
    capability_degradation: list[str] | None = None,
) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=event_id,
        adapter="codex",
        event_kind=kind,
        tool_category=tool_category,
        changed_paths=changed_paths or [],
        read_paths=read_paths or [],
        command_outcome=command_outcome,
        validation_candidate=validation_candidate,
        validation_outcome=validation_outcome,
        validation_freshness=validation_freshness,
        permission_decision=permission_decision,
        permission_reason=permission_reason,
        capability_degradation=capability_degradation or [],
    )


def _contract(
    ledger: EvidenceLedger,
    required: list[str] | None = None,
) -> ClosureContract:
    return ClosureContract.from_ledger(
        ledger,
        required_evidence=["validation"] if required is None else required,
    )


class EvidenceLedgerSequenceTests(unittest.TestCase):
    def test_read_edit_validation_pass_closes_ready_without_required_preflight(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            _event(
                "read-1",
                EventKind.PRE_TOOL_USE.value,
                tool_category="read",
                read_paths=["src/runtime_governance/evidence.py"],
            )
        )
        ledger.add_normalized_event(
            _event(
                "edit-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="edit",
                changed_paths=["src/runtime_governance/evidence.py"],
            )
        )
        ledger.add_normalized_event(
            _event(
                "validate-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="test",
                command_outcome="pass",
                validation_candidate=True,
            )
        )

        contract = _contract(ledger, ["read_evidence", "validation"])

        self.assertEqual(ledger.read_evidence.strength, EvidenceStrength.STRONG.value)
        self.assertEqual(ledger.validation.strength, EvidenceStrength.STRONG.value)
        self.assertEqual(ledger.validation.freshness, Freshness.CURRENT.value)
        self.assertEqual(contract.verdict, ClosureVerdict.READY.value)
        self.assertNotIn("implementation_preflight", contract.missing_evidence)

    def test_validation_before_later_edit_is_stale_and_needs_validation(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            _event(
                "validate-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="test",
                command_outcome="pass",
                validation_candidate=True,
            )
        )
        ledger.add_normalized_event(
            _event(
                "edit-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="edit",
                changed_paths=["src/runtime_governance/closure.py"],
            )
        )

        contract = _contract(ledger)

        self.assertEqual(ledger.validation.strength, EvidenceStrength.NEGATIVE.value)
        self.assertEqual(ledger.validation.freshness, Freshness.STALE.value)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)
        self.assertIn("validation", contract.missing_evidence)

    def test_review_finding_without_repair_needs_repair_owner(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "review_findings": ["P1: stale closure evidence"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                }
            ]
        )

        contract = _contract(ledger)

        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_REPAIR.value)
        self.assertIn("repair", contract.missing_evidence)
        self.assertEqual(contract.next_owner, "repair")

    def test_repair_without_rereview_needs_review_owner(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "review_findings": ["P1: stale closure evidence"],
                    "repair_evidence_seen": True,
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                }
            ]
        )

        contract = _contract(ledger)

        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_REVIEW.value)
        self.assertIn("review", contract.missing_evidence)
        self.assertEqual(contract.next_owner, "reviewer")

    def test_repair_then_rereview_then_validation_can_close_ready(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "review_findings": ["P1: stale closure evidence"],
                    "repair_evidence_seen": True,
                    "review_after_repair_seen": True,
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                }
            ]
        )

        contract = _contract(ledger)

        self.assertEqual(contract.verdict, ClosureVerdict.READY.value)
        self.assertNotIn("repair", contract.missing_evidence)
        self.assertNotIn("review", contract.missing_evidence)

    def test_incomplete_route_manifest_is_partial_with_specific_missing_fields(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                }
            ]
        )

        contract = _contract(ledger, ["route_manifest"])

        self.assertEqual(ledger.route_manifest.strength, EvidenceStrength.PARTIAL.value)
        self.assertIn("selected_capabilities", ledger.route_manifest.summary)
        self.assertIn("required_references", ledger.route_manifest.summary)
        self.assertIn("required_quality_gates", ledger.route_manifest.summary)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)
        self.assertIn("route_manifest", contract.missing_evidence)

    def test_unsupported_runtime_event_degrades_not_passes(self) -> None:
        unsupported_event = _event(
            "unsupported-1",
            EventKind.UNKNOWN.value,
            capability_degradation=["unsupported_event:UnknownFutureEvent"],
        )
        gate = GateResult.from_event_support(
            "executor_adapter",
            unsupported_event,
            supported_events=["PostToolUse"],
        )
        ledger = EvidenceLedger()
        ledger.add_normalized_event(unsupported_event)

        contract = _contract(ledger, [])

        self.assertEqual(gate.outcome, GateOutcome.DEGRADED.value)
        self.assertEqual(contract.verdict, ClosureVerdict.DEGRADED_READY.value)
        self.assertIn("runtime_adapter_degradation", contract.unsupported_checks)
        self.assertIn("unsupported runtime checks remain", contract.residual_risk)

    def test_command_only_validation_is_weak_and_cannot_close_ready(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            _event(
                "validate-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="test",
                validation_candidate=True,
            )
        )

        contract = _contract(ledger)

        self.assertEqual(ledger.validation.strength, EvidenceStrength.WEAK.value)
        self.assertEqual(ledger.validation.outcome, "no_outcome")
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)

    def test_config_change_after_validation_stales_prior_pass(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            _event(
                "validate-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="test",
                command_outcome="pass",
                validation_candidate=True,
            )
        )
        ledger.add_normalized_event(
            _event(
                "config-1",
                EventKind.CONFIG_CHANGED.value,
                changed_paths=["pyproject.toml"],
            )
        )

        contract = _contract(ledger)

        self.assertEqual(ledger.validation.freshness, Freshness.STALE.value)
        self.assertEqual(ledger.validation.outcome, "stale")
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)

    def test_permission_denial_is_not_overwritten_by_later_validation_pass(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            _event(
                "permission-1",
                EventKind.PERMISSION_REQUEST.value,
                permission_decision="deny",
                permission_reason="permission denied by user",
            )
        )
        ledger.add_normalized_event(
            _event(
                "validate-1",
                EventKind.POST_TOOL_USE.value,
                tool_category="test",
                command_outcome="pass",
                validation_candidate=True,
            )
        )

        contract = _contract(ledger)

        self.assertEqual(ledger.permission.strength, EvidenceStrength.NEGATIVE.value)
        self.assertEqual(ledger.permission.outcome, "deny")
        self.assertEqual(contract.verdict, ClosureVerdict.BLOCKED.value)
        self.assertIn("permission", contract.negative_evidence)
        self.assertIn("permission: permission denied by user", contract.residual_risk)


if __name__ == "__main__":
    unittest.main()
