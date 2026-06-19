from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import ClosureContract, ClosureVerdict, EvidenceLedger, Freshness  # noqa: E402


class ClosureContractTests(unittest.TestCase):
    def test_ready_when_required_evidence_is_strong_and_current(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.READY.value)
        self.assertEqual(contract.missing_evidence, [])

    def test_unsupported_runtime_can_be_degraded_ready(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "residual_risk_detected": True,
                    "capability_degradation": ["copilot_stop_unsupported"],
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.DEGRADED_READY.value)
        self.assertIn("runtime_adapter_degradation", contract.unsupported_checks)

    def test_validation_command_without_outcome_needs_validation(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)
        self.assertIn("validation", contract.missing_evidence)
        self.assertIn("validation command was observed without outcome", contract.residual_risk)

    def test_stale_validation_needs_fresh_validation(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "false",
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)
        self.assertIn("validation", contract.negative_evidence)
        self.assertEqual(contract.freshness["validation"], Freshness.STALE.value)

    def test_changed_code_without_validation_needs_validation(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "changed_paths": ["src/runtime_governance/closure.py"],
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)
        self.assertIn("validation", contract.missing_evidence)

    def test_failed_validation_blocks_closure(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "fail",
                    "validation_result_evidence_strength": "negative",
                    "validation_result_fresh_after_last_edit": "true",
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.BLOCKED.value)
        self.assertIn("validation", contract.negative_evidence)

    def test_review_finding_without_repair_needs_repair(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "review_findings": ["P1: stale closure evidence"],
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_REPAIR.value)
        self.assertIn("repair", contract.missing_evidence)

    def test_repair_without_rereview_needs_review(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "repair_evidence_seen": True,
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_REVIEW.value)
        self.assertIn("review", contract.missing_evidence)

    def test_targeted_validator_reported_as_full_needs_validation(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_broker_closure_outcome": "needs_validation",
                    "validation_broker_negative_evidence": [
                        "targeted_check_reported_as_full"
                    ],
                    "validation_broker_command_ledger": [
                        {"outcome": "partial", "evidence_strength": "partial"}
                    ],
                    "residual_risk_detected": True,
                }
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.NEEDS_VALIDATION.value)
        self.assertIn("validation", contract.missing_evidence)

    def test_permission_denied_destructive_command_blocks_without_raw_command(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "residual_risk_detected": True,
                },
                {
                    "event_name": "PermissionRequest",
                    "permission_decision": "deny",
                    "permission_reason": "rm -rf /tmp/x --token=SECRET",
                    "command": "rm -rf /tmp/x --token=SECRET",
                },
            ]
        )
        contract = ClosureContract.from_ledger(ledger)
        self.assertEqual(contract.verdict, ClosureVerdict.BLOCKED.value)
        self.assertIn("permission", contract.negative_evidence)
        self.assertNotIn("SECRET", contract.to_json())

    def test_json_round_trip(self) -> None:
        contract = ClosureContract(
            supported_checks=["validation"],
            required_evidence=["validation"],
            missing_evidence=["validation"],
            verdict=ClosureVerdict.NEEDS_VALIDATION.value,
        )
        self.assertEqual(ClosureContract.from_json(contract.to_json()), contract)


if __name__ == "__main__":
    unittest.main()
