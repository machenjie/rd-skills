from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_adapter_capabilities import adapter_capabilities_for  # noqa: E402
from changeforge_closure_contract import ClosureContract  # noqa: E402


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

    def test_block_mode_uses_adapter_blocking_capability(self) -> None:
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
        self.assertEqual(contract.closure_status, "block")

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


if __name__ == "__main__":
    unittest.main()
