from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
for path in (SRC, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

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


def complete_contract(state: dict, *, runtime: str = "codex") -> ClosureContract:
    return ClosureContract.from_state(
        {**_complete_phase_state(), **state},
        route_manifest_complete=True,
        repository_context_present=True,
        implementation_preflight_complete=True,
        validation_evidence_present=True,
        residual_risk_present=True,
        stage_route_present=True,
        capabilities=adapter_capabilities_for(runtime),
        runtime=runtime,
        validation_broker_outcome="ready",
    )


class DegradedClosureContractTests(unittest.TestCase):
    def test_degraded_closure_cannot_be_plain_ready(self) -> None:
        contract = complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/app.py"],
                "runtime_adapter": {
                    "adapter": "codex",
                    "active_degradation": ["codex_post_tool_batch_unsupported"],
                },
            }
        )

        self.assertEqual(contract.verdict, "degraded_ready")
        self.assertIn("runtime_adapter_degradation", contract.unsupported_checks)
        self.assertIn("codex_post_tool_batch_unsupported", contract.degraded_capabilities)
        self.assertIn("adapter fail_open policy active for degraded capabilities", contract.residual_risk)
        self.assertIn("adapter fail_open policy active for degraded capabilities", contract.changeforge_closure["residual_risk"])

    def test_fail_open_policy_is_residual_risk_for_visibility_limits(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/app.py"],
                "validation_results": ["unknown:unknown:pytest"],
                "validation_command_seen": True,
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("generic"),
            runtime="generic",
            validation_broker_outcome="ready",
        )

        self.assertNotEqual(contract.verdict, "ready")
        self.assertIn("generic_validation_outcome_visibility_none", contract.degraded_capabilities)
        self.assertIn("adapter fail_open policy active for degraded capabilities", contract.residual_risk)

    def test_fail_closed_requires_configured_closure_check(self) -> None:
        capabilities = replace(adapter_capabilities_for("codex"), fail_closed_allowed_checks=())
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=False,
            validation_evidence_present=False,
            residual_risk_present=False,
            capabilities=capabilities,
            block_mode=True,
        )

        self.assertTrue(contract.adapter_supports_blocking)
        self.assertEqual(contract.closure_status, "warn")

    def test_fail_closed_allowed_stop_closure_stays_advisory(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "coding", "changed_paths": ["src/app.py"]},
            route_manifest_complete=False,
            validation_evidence_present=False,
            residual_risk_present=False,
            capabilities=adapter_capabilities_for("codex"),
            block_mode=True,
        )

        self.assertEqual(contract.closure_status, "warn")


if __name__ == "__main__":
    unittest.main()
