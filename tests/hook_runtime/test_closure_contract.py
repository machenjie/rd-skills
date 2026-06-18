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


if __name__ == "__main__":
    unittest.main()
