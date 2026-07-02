from __future__ import annotations

import sys
import unittest
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import ClosureContract, ClosureVerdict, EvidenceLedger, Freshness  # noqa: E402


SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_hook_closure_contract():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(
        "changeforge_closure_contract_for_phase_tests",
        SCRIPT_DIR / "changeforge_closure_contract.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


class HookClosurePhaseContractTests(unittest.TestCase):
    def _contract(self, state: dict) -> object:
        module = load_hook_closure_contract()
        return module.ClosureContract.from_state(
            state,
            route_manifest_complete=True,
            stage_route_present=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            review_evidence_present=True,
            residual_risk_present=True,
            runtime="codex",
        )

    def _state(self, **overrides: object) -> dict:
        state: dict[str, object] = {
            "runtime": "codex",
            "turn_stage": "repair",
            "changed_paths": ["src/runtime_governance/process_phase.py"],
            "validation_freshness_seen": True,
            "phase_review_findings": [
                {
                    "finding_id": "sdd-001",
                    "phase": "sdd",
                    "severity": "high",
                    "evidence": "material choice missing",
                    "required_fix": "add choice evidence",
                    "blocks_next_stage": True,
                }
            ],
        }
        state.update(overrides)
        return state

    def test_phase_review_finding_without_repair_blocks_closure(self) -> None:
        contract = self._contract(self._state())
        self.assertEqual(contract.verdict, "needs_repair")
        self.assertIn("phase_repair", contract.missing_items)

    def test_phase_repair_without_rereview_blocks_closure(self) -> None:
        contract = self._contract(
            self._state(phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}])
        )
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("phase_rereview", contract.missing_items)

    def test_phase_rereview_fail_blocks_closure(self) -> None:
        contract = self._contract(
            self._state(
                phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
                phase_rereview_events=[{"finding_id": "sdd-001", "verdict": "fail"}],
            )
        )
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("phase_rereview", contract.missing_items)

    def test_phase_rereview_pass_allows_closure(self) -> None:
        contract = self._contract(
            self._state(
                phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
                phase_rereview_events=[{"finding_id": "sdd-001", "verdict": "pass"}],
            )
        )
        self.assertNotIn("phase_repair", contract.missing_items)
        self.assertNotIn("phase_rereview", contract.missing_items)

    def test_unrelated_phase_repair_does_not_close_finding(self) -> None:
        contract = self._contract(
            self._state(phase_repair_events=[{"finding_id": "ddd-002", "repair_summary": "unrelated"}])
        )
        self.assertEqual(contract.verdict, "needs_repair")
        self.assertIn("phase_repair", contract.missing_items)

    def test_stale_validation_after_phase_repair_blocks_closure(self) -> None:
        contract = self._contract(
            self._state(
                validation_freshness_seen=False,
                phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
                phase_rereview_events=[{"finding_id": "sdd-001", "verdict": "pass"}],
            )
        )
        self.assertEqual(contract.verdict, "needs_validation")
        self.assertIn("validation_fresh_after_final_edit", contract.missing_items)


if __name__ == "__main__":
    unittest.main()
