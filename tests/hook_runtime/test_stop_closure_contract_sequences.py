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

from changeforge_adapter_capabilities import adapter_capabilities_for  # noqa: E402
from changeforge_closure_contract import ClosureContract  # noqa: E402


def _complete_contract(state: dict, *, runtime: str = "codex") -> ClosureContract:
    return ClosureContract.from_state(
        state,
        route_manifest_complete=True,
        stage_route_present=bool(state.get("stage_route_present", True)),
        repository_context_present=True,
        implementation_preflight_complete=True,
        validation_evidence_present=True,
        residual_risk_present=True,
        capabilities=adapter_capabilities_for(runtime),
        runtime=runtime,
        validation_broker_outcome="ready",
    )


class StopClosureContractSequenceTests(unittest.TestCase):
    def test_non_trivial_engineering_without_stage_route_cannot_close_ready(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertNotEqual(contract.verdict, "ready")
        self.assertIn("stage_route", contract.missing_items)
        self.assertTrue(contract.requires_stage_route)
        self.assertIn(
            "stage route evidence missing for non-trivial engineering task",
            contract.residual_risk,
        )

    def test_engineering_with_stage_route_can_close_ready(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "stage_route_present": True,
            }
        )

        self.assertEqual(contract.verdict, "ready")
        self.assertNotIn("stage_route", contract.missing_items)
        self.assertTrue(contract.requires_stage_route)

    def test_non_trivial_engineering_task_string_true_does_not_skip_stage_route(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "non_trivial_engineering_task": "true",
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertTrue(contract.requires_stage_route)
        self.assertIn("stage_route", contract.missing_items)
        self.assertNotEqual(contract.verdict, "ready")

    def test_trivial_engineering_task_string_true_does_not_skip_stage_route_without_reason(
        self,
    ) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["docs/USAGE.md"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "trivial_engineering_task": "true",
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertTrue(contract.requires_stage_route)
        self.assertIn("stage_route", contract.missing_items)
        self.assertNotEqual(contract.verdict, "ready")

    def test_trivial_engineering_task_boolean_true_still_needs_skip_reason(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["docs/USAGE.md"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "trivial_engineering_task": True,
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertTrue(contract.requires_stage_route)
        self.assertIn("stage_route", contract.missing_items)
        self.assertNotEqual(contract.verdict, "ready")

    def test_question_stage_does_not_require_stage_route(self) -> None:
        contract = ClosureContract.from_state(
            {"turn_stage": "question"},
            route_manifest_complete=True,
            repository_context_present=False,
            implementation_preflight_complete=False,
            validation_evidence_present=False,
            residual_risk_present=False,
            capabilities=adapter_capabilities_for("codex"),
        )

        self.assertFalse(contract.requires_stage_route)
        self.assertNotIn("stage_route", contract.missing_items)

    def test_explicit_stage_route_skip_reason_allows_trivial_docs_change(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["docs/USAGE.md"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "trivial_engineering_task": True,
                "stage_route_present": False,
                "stage_route_skip_reason": "single trivial documentation wording correction",
            }
        )

        self.assertFalse(contract.requires_stage_route)
        self.assertNotIn("stage_route", contract.missing_items)
        self.assertEqual(contract.verdict, "ready")

    def test_trivial_engineering_with_explicit_skip_reason_does_not_require_stage_route(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["docs/USAGE.md"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "stage_route_present": False,
                "stage_route_skip_reason": "single trivial docs correction",
            }
        )

        self.assertEqual(contract.verdict, "ready")
        self.assertFalse(contract.requires_stage_route)
        self.assertNotIn("stage_route", contract.missing_items)

    def test_empty_stage_route_skip_reason_still_requires_stage_route(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "stage_route_skip_reason": "",
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertTrue(contract.requires_stage_route)
        self.assertIn("stage_route", contract.missing_items)

    def test_boolean_stage_route_skip_placeholder_still_requires_stage_route(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
                "trivial_engineering_task": True,
                "non_trivial_engineering_task": False,
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
        )

        self.assertTrue(contract.requires_stage_route)
        self.assertIn("stage_route", contract.missing_items)
        self.assertNotEqual(contract.verdict, "ready")

    def test_edit_then_validation_pass_can_close_ready(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/evidence.py"],
                "validation_results": ["pass:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            }
        )

        self.assertEqual(contract.verdict, "ready")
        self.assertEqual(contract.missing_items, [])
        self.assertEqual(contract.changeforge_closure["validation"]["freshness"], "current")

    def test_config_change_after_validation_cannot_close_ready(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/evidence.py"],
                "validation_results": ["pass:python -m unittest"],
                "config_changes": ["pyproject.toml"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            }
        )

        self.assertEqual(contract.verdict, "needs_validation")
        self.assertIn("validation", contract.missing_items)
        self.assertIn("validation", contract.changeforge_closure["negative_evidence"])
        self.assertEqual(contract.changeforge_closure["validation"]["freshness"], "stale")

    def test_review_finding_without_repair_routes_to_repair(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "repair",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "review_findings": ["P1: repair required"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            }
        )

        self.assertEqual(contract.verdict, "needs_repair")
        self.assertIn("repair", contract.missing_items)
        self.assertEqual(contract.changeforge_closure["next_owner"], "repair")

    def test_repair_without_rereview_routes_to_review(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "repair",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "review_findings": ["P1: repair required"],
                "repair_evidence_seen": True,
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            }
        )

        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("review_evidence", contract.missing_items)
        self.assertEqual(contract.changeforge_closure["next_owner"], "reviewer")

    def test_repair_rereview_and_validation_can_close_ready(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "repair",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "review_findings": ["P1: repair required"],
                "repair_evidence_seen": True,
                "review_after_repair_seen": True,
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            }
        )

        self.assertEqual(contract.verdict, "ready")
        self.assertNotIn("repair", contract.missing_items)
        self.assertNotIn("review", contract.missing_items)

    def test_command_only_validation_remains_weak(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["candidate:python -m unittest"],
                "implementation_preflight_required": True,
            },
            route_manifest_complete=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="needs_validation",
        )

        self.assertEqual(contract.verdict, "needs_validation")
        self.assertIn("validation", contract.missing_items)
        self.assertEqual(contract.changeforge_closure["validation"]["outcome"], "unknown")

    def test_permission_denial_survives_later_safe_validation_pass(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/runtime_governance/closure.py"],
                "validation_results": ["pass:python -m unittest"],
                "permission_decisions": ["deny: user declined write"],
                "command_risks": ["safe:python -m unittest"],
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            }
        )

        self.assertEqual(contract.verdict, "blocked")
        self.assertIn("permission", contract.changeforge_closure["negative_evidence"])
        self.assertIn("permission: permission denied by runtime", contract.residual_risk)

    def test_active_unsupported_runtime_check_is_degraded_ready(self) -> None:
        contract = _complete_contract(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/hook-runtime/scripts/changeforge_stop_closure_gate.py"],
                "validation_results": ["pass:python -m unittest"],
                "runtime_adapter": {
                    "adapter": "copilot",
                    "active_unsupported_checks": ["pre_tool_advisory_context"],
                },
                "implementation_preflight_required": True,
                "implementation_preflight_complete": True,
            },
            runtime="copilot",
        )

        self.assertEqual(contract.verdict, "degraded_ready")
        self.assertIn("pre_tool_advisory_context", contract.unsupported_checks)
        self.assertIn("unsupported runtime checks remain", contract.residual_risk)


if __name__ == "__main__":
    unittest.main()
