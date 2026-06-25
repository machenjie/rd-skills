from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
for path in (SRC, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from changeforge_closure_contract import ClosureContract  # noqa: E402
from runtime_governance.adapters import adapter_capabilities_for  # noqa: E402


class ClosureContractByAdapterTests(unittest.TestCase):
    def test_copilot_ready_when_unsupported_checks_are_catalog_only(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("copilot"),
            validation_broker_outcome="ready",
        )
        self.assertEqual(contract.adapter, "copilot")
        self.assertEqual(contract.unsupported_checks, [])
        self.assertEqual(contract.degraded_capabilities, [])
        self.assertEqual(contract.verdict, "ready")

    def test_copilot_degraded_ready_when_required_check_is_active(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/app.py"],
                "suggested_gates": ["pre_tool_advisory_context"],
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("copilot"),
            validation_broker_outcome="ready",
        )
        self.assertEqual(contract.adapter, "copilot")
        self.assertIn("pre_tool_advisory_context", contract.unsupported_checks)
        self.assertIn("runtime_adapter_degradation", contract.unsupported_checks)
        self.assertIn(
            "copilot_pre_tool_advisory_context_unsupported",
            contract.degraded_capabilities,
        )
        self.assertEqual(contract.verdict, "degraded_ready")

    def test_missing_validation_uses_needs_validation(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=False,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
        )
        self.assertEqual(contract.verdict, "needs_validation")

    def test_generic_runtime_cannot_block_stop(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=False,
            validation_evidence_present=False,
            residual_risk_present=False,
            capabilities=adapter_capabilities_for("generic"),
            block_mode=True,
        )
        self.assertFalse(contract.adapter_supports_blocking)
        self.assertEqual(contract.closure_status, "warn")


if __name__ == "__main__":
    unittest.main()
