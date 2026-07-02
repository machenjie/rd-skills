from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_adapter_capabilities import adapter_capabilities_for  # noqa: E402
from changeforge_closure_contract import ClosureContract  # noqa: E402


def _complete_phase_state() -> dict[str, object]:
    digest = "sha256:" + ("a" * 64)
    phases = ("pdd", "ddd", "sdd", "tdd")
    return {
        "process_phase_ledger_seen": True,
        "process_phase_ledgers": [
            {
                "route_id": "active-runtime-route",
                "current_phase": "implementation",
                "required_phases": list(phases),
                "phase_status": {phase: "reviewed" for phase in phases},
                "artifact_digests": {phase: digest for phase in phases},
                "review_ids": {phase: f"{phase}-review-1" for phase in phases},
                "validation_signal_present": True,
            }
        ],
        "pdd_reviewed": True,
        "ddd_reviewed": True,
        "sdd_reviewed": True,
        "tdd_reviewed": True,
    }


class ClosureContractTests(unittest.TestCase):
    def test_engineering_contract_flags_missing_route_validation_and_risk(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=False,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=False,
            residual_risk_present=False,
            capabilities=adapter_capabilities_for("codex"),
            block_mode=False,
        )
        self.assertEqual(contract.closure_status, "warn")
        self.assertIn("route_manifest", contract.missing_items)
        self.assertIn("validation", contract.missing_items)
        self.assertIn("risk", contract.missing_items)

    def test_block_mode_stays_advisory_for_closure_evidence(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=False,
            repository_context_present=False,
            implementation_preflight_complete=False,
            validation_evidence_present=False,
            residual_risk_present=False,
            capabilities=adapter_capabilities_for("copilot"),
            block_mode=True,
        )
        self.assertTrue(contract.adapter_supports_blocking)
        self.assertEqual(contract.closure_status, "warn")
        self.assertIn("route_manifest", contract.missing_items)

    def test_read_review_profile_does_not_require_engineering_route(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "read", "read_evidence_seen": True},
            route_manifest_complete=False,
            validation_evidence_present=False,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("claude"),
        )
        self.assertFalse(contract.requires_route_manifest)
        self.assertNotIn("route_manifest", contract.missing_items)

    def test_ordinary_codex_closure_is_ready_despite_catalog_unsupported_checks(self) -> None:
        contract = ClosureContract.from_state(
            {
                **_complete_phase_state(),
                "turn_stage": "coding",
                "changed_paths": ["src/app.py"],
                "runtime_adapter": {
                    "adapter": "codex",
                    "unsupported_checks": ["file_change_event", "session_end"],
                },
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            stage_route_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )
        self.assertEqual(contract.verdict, "ready")
        self.assertEqual(contract.unsupported_checks, [])
        self.assertEqual(contract.degraded_capabilities, [])

    def test_structured_changeforge_closure_reports_review_repair_state(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "repair",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "review_findings": ["P1: repair requires re-review"],
                "repair_evidence_seen": True,
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            review_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
        )
        self.assertEqual(contract.verdict, "needs_review")
        closure = contract.changeforge_closure
        self.assertEqual(closure["verdict"], "needs_review")
        self.assertEqual(
            closure["changed_files"],
            {"changed": ["src/runtime_governance/closure.py"], "deleted": [], "generated": []},
        )
        self.assertEqual(
            closure["review"],
            {
                "review_outcome": "finding",
                "repair_present": True,
                "rereview_present": False,
            },
        )

    def test_route_repair_without_branch_summary_is_not_ready(self) -> None:
        contract = ClosureContract.from_state(
            {
                **_complete_phase_state(),
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "stage_route_present": True,
                "route_repair_forbidden_retries": ["same-path retry"],
                "prompt_signals": ["route_repair"],
            },
            route_manifest_complete=True,
            stage_route_present=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertEqual(contract.verdict, "needs_repair")
        self.assertIn("branch_route_repair_summary", contract.missing_items)
        self.assertIn(
            "route repair happened without a bounded branch/route-repair summary",
            contract.residual_risk,
        )

    def test_route_repair_with_branch_summary_can_close_ready(self) -> None:
        contract = ClosureContract.from_state(
            {
                **_complete_phase_state(),
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "stage_route_present": True,
                "route_repair_forbidden_retries": ["same-path retry"],
                "prompt_signals": ["route_repair"],
                "branch_route_repair_summaries": [
                    {
                        "schema_version": 1,
                        "summary_id": "route-repair-1",
                        "trigger": "repeated_same_path_retry",
                        "abandoned_or_repaired_route": {
                            "owner_skill": "quality-test-gate",
                            "reviewer_skill": "ai-code-review-refactor",
                            "hypothesis": "same path retry",
                            "files_touched": ["src/runtime_governance/closure.py"],
                            "validation_result": "fail:old route",
                            "failure_reason": "same-path retry",
                        },
                        "reusable_findings": ["do not retry same path"],
                        "forbidden_retries": ["same-path retry"],
                        "new_route": {
                            "owner_skill": "quality-test-gate",
                            "selected_capabilities": ["context-control-plane"],
                            "validation_plan": ["rerun closure tests"],
                        },
                        "residual_risk": ["none known"],
                        "privacy_status": "pass",
                    }
                ],
            },
            route_manifest_complete=True,
            stage_route_present=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertEqual(contract.verdict, "ready")
        self.assertNotIn("branch_route_repair_summary", contract.missing_items)


if __name__ == "__main__":
    unittest.main()
