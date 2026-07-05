from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_adapter_capabilities import adapter_capabilities_for  # noqa: E402
from changeforge_closure_contract import ClosureContract  # noqa: E402
from changeforge_common import extract_diagnosis_closure_fields  # noqa: E402


def _phase_review_result(phase: str, digest: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "review_id": f"{phase}-review-1",
        "phase": phase,
        "reviewer_skill": "ai-code-review-refactor",
        "owner_skill": "development-process-orchestrator",
        "reviewed_artifact_digest": digest,
        "verdict": "pass",
        "score": 5,
        "findings": [],
        "approved_scope": {"files": ["src/app.py"], "behaviors": [], "facts": []},
        "not_reviewed": [],
        "required_next_action": ["proceed"],
        "residual_risk": [],
        "review_source": "subagent_review_gate",
        "capsule_id": f"{phase}-capsule-1",
        "expected_artifact_digest": digest,
        "review_context_strength": "strong",
        "reviewer_boundary": "subagent",
    }


def _implementation_review() -> dict[str, object]:
    return {
        "schema_version": 1,
        "review_id": "implementation-review-1",
        "review_source": "implementation_review_gate",
        "review_context_strength": "strong",
        "reviewed_diff_digest": "sha256:" + ("b" * 64),
        "reviewed_files": [
            "src/app.py",
            "src/runtime_governance/closure.py",
            "src/hook-runtime/scripts/changeforge_common.py",
            "src/hook-runtime/scripts/changeforge_stop_closure_gate.py",
            "docs/USAGE.md",
        ],
        "changed_files_count": 5,
        "reviewer_skill": "ai-code-review-refactor",
        "owner_skill": "development-process-orchestrator",
        "verdict": "pass",
        "score": 5,
        "findings": [],
        "validation_map": [],
        "residual_risk": [],
    }


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
        "phase_review_results": [_phase_review_result(phase, digest) for phase in phases],
        "pdd_reviewed": True,
        "ddd_reviewed": True,
        "sdd_reviewed": True,
        "tdd_reviewed": True,
        "implementation_review_required": True,
        "implementation_review_seen": True,
        "implementation_review_passed": True,
        "implementation_review_results": [_implementation_review()],
    }


def _complete_diagnosis_state() -> dict[str, object]:
    return {
        "turn_stage": "debugging-diagnosis",
        "diagnosis_closure_present": True,
        "diagnosis_closure_complete": True,
        "diagnosis_closure_status": "complete",
        "diagnosis_closure_missing": [],
        "diagnosis_independent_review_status": "strong",
        "diagnosis_selected_skills_only_review": False,
        "validation_results": ["pass:bounded-readonly-diagnosis-fixture"],
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


    def _ready_contract_for_state(self, state: dict[str, object]) -> ClosureContract:
        return ClosureContract.from_state(
            state,
            route_manifest_complete=True,
            stage_route_present=True,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
            validation_result_outcome="pass",
        )

    def _phase_review_contract(self, *, mutate_first_review=None) -> ClosureContract:
        state = {
            **_complete_phase_state(),
            "turn_stage": "coding",
            "changed_paths": ["src/app.py"],
            "validation_results": ["pass:python -m unittest"],
        }
        reviews = [dict(review) for review in state["phase_review_results"]]
        if mutate_first_review is not None:
            mutate_first_review(reviews[0])
        state["phase_review_results"] = reviews
        return self._ready_contract_for_state(state)

    def test_closure_rejects_strong_source_review_with_low_score(self) -> None:
        contract = self._phase_review_contract(mutate_first_review=lambda review: review.update(score=3))
        self.assertNotEqual(contract.phase_review_status, "pass")
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("phase_reviews", contract.missing_items)

    def test_closure_rejects_strong_source_review_with_same_owner_reviewer(self) -> None:
        def mutate(review: dict[str, object]) -> None:
            review["reviewer_skill"] = review["owner_skill"]

        contract = self._phase_review_contract(mutate_first_review=mutate)
        self.assertNotEqual(contract.phase_review_status, "pass")
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("phase_reviews", contract.missing_items)

    def test_closure_rejects_strong_source_review_with_blocking_findings(self) -> None:
        def mutate(review: dict[str, object]) -> None:
            review["findings"] = [
                {
                    "finding_id": "pdd-blocker-1",
                    "severity": "high",
                    "blocks_next_stage": True,
                    "required_fix": "repair the phase artifact",
                }
            ]

        contract = self._phase_review_contract(mutate_first_review=mutate)
        self.assertNotEqual(contract.phase_review_status, "pass")
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("phase_reviews", contract.missing_items)

    def test_closure_rejects_strong_source_review_missing_expected_digest(self) -> None:
        def mutate(review: dict[str, object]) -> None:
            review.pop("expected_artifact_digest", None)

        contract = self._phase_review_contract(mutate_first_review=mutate)
        self.assertNotEqual(contract.phase_review_status, "pass")
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("phase_reviews", contract.missing_items)

    def test_closure_accepts_only_phase_review_passes_result(self) -> None:
        contract = self._phase_review_contract()
        self.assertEqual(contract.phase_review_status, "pass")
        self.assertNotIn("phase_reviews", contract.missing_items)

    def test_missing_implementation_review_emits_required_action(self) -> None:
        state = {
            **_complete_phase_state(),
            "turn_stage": "coding",
            "changed_paths": ["src/app.py"],
            "implementation_review_results": [],
            "implementation_review_seen": False,
            "implementation_review_passed": False,
        }
        contract = self._ready_contract_for_state(state)
        self.assertEqual(contract.verdict, "degraded_ready")
        self.assertEqual(contract.implementation_review_status, "missing")
        self.assertIn("implementation_review_required_action", contract.changeforge_closure)
        self.assertIn("implementation review not run", contract.review_residual_risk)

    def test_weak_implementation_review_emits_required_action(self) -> None:
        weak_review = _implementation_review()
        weak_review["reviewed_files"] = ["docs/USAGE.md"]
        state = {
            **_complete_phase_state(),
            "turn_stage": "coding",
            "changed_paths": ["src/app.py"],
            "implementation_review_results": [weak_review],
        }
        contract = self._ready_contract_for_state(state)
        self.assertEqual(contract.verdict, "needs_review")
        self.assertEqual(contract.implementation_review_status, "weak")
        self.assertIn("implementation_review_required_action", contract.changeforge_closure)

    def test_implementation_review_required_action_lists_actual_changed_files(self) -> None:
        state = {
            **_complete_phase_state(),
            "turn_stage": "coding",
            "changed_paths": ["src/app.py"],
            "generated_paths": ["docs/generated.md"],
            "implementation_review_results": [],
        }
        contract = self._ready_contract_for_state(state)
        action = contract.changeforge_closure["implementation_review_required_action"]
        self.assertEqual(action["changed_files"], ["src/app.py", "docs/generated.md"])
        self.assertEqual(action["changed_files_count"], 2)

    def test_implementation_review_required_action_requires_reviewed_diff_digest(self) -> None:
        state = {
            **_complete_phase_state(),
            "turn_stage": "coding",
            "changed_paths": ["src/app.py"],
            "implementation_review_results": [],
        }
        contract = self._ready_contract_for_state(state)
        action = contract.changeforge_closure["implementation_review_required_action"]
        self.assertTrue(action["reviewed_diff_digest_required"])
        required = action["expected_output"]["required_fields"]
        self.assertIn("reviewed_diff_digest", required)

    def test_debugging_diagnosis_missing_diagnosis_closure_fails_handoff(self) -> None:
        contract = self._ready_contract_for_state({"turn_stage": "debugging-diagnosis"})

        self.assertEqual(contract.verdict, "needs_review")
        self.assertTrue(contract.requires_stage_route)
        self.assertIn("diagnosis_closure", contract.missing_items)
        self.assertIn("diagnosis_closure", contract.changeforge_closure)

    def test_debugging_diagnosis_missing_hypothesis_elimination_fails_handoff(self) -> None:
        state = {
            **_complete_diagnosis_state(),
            "diagnosis_closure_complete": False,
            "diagnosis_closure_status": "partial",
            "diagnosis_closure_missing": ["hypothesis_elimination"],
        }
        contract = self._ready_contract_for_state(state)

        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("hypothesis_elimination", contract.missing_items)
        self.assertIn(
            "diagnosis closure is partial without eliminated hypotheses",
            contract.residual_risk,
        )

    def test_debugging_diagnosis_missing_independent_reviews_fails_handoff(self) -> None:
        state = {
            **_complete_diagnosis_state(),
            "diagnosis_closure_complete": False,
            "diagnosis_closure_status": "partial",
            "diagnosis_closure_missing": ["independent_reviews"],
            "diagnosis_independent_review_status": "missing",
        }
        contract = self._ready_contract_for_state(state)

        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("independent_reviews", contract.missing_items)
        self.assertIn(
            "diagnosis closure is partial without independent review results",
            contract.residual_risk,
        )

    def test_debugging_diagnosis_missing_stage_route_fails_handoff(self) -> None:
        contract = ClosureContract.from_state(
            _complete_diagnosis_state(),
            route_manifest_complete=True,
            stage_route_present=False,
            repository_context_present=True,
            implementation_preflight_complete=True,
            validation_evidence_present=True,
            residual_risk_present=True,
            capabilities=adapter_capabilities_for("codex"),
            validation_broker_outcome="ready",
            validation_result_outcome="pass",
        )

        self.assertNotEqual(contract.verdict, "ready")
        self.assertTrue(contract.requires_stage_route)
        self.assertIn("stage_route", contract.missing_items)

    def test_diagnosis_review_with_only_selected_skills_fails_handoff(self) -> None:
        # Regression guard: listing reviewer skills is not a structured review result.
        final_text = """
```yaml
diagnosis_closure:
  stage: debugging-diagnosis
  symptom: gmgn skipped token intel events
  direct_cause: missing chain mapping
  upstream_cause: upstream payload omitted chain context
  owner_surface: crypto diagnosis
  evidence_inventory:
    - bounded production log query, redacted summary only
  hypothesis_elimination:
    - missing chain confirmed; deployment mutation refuted
  validation_results:
    - bounded readonly query matched expected skip reason
  independent_reviews:
    selected_skills:
      - reliability-observability-gate
      - security-privacy-gate
  proves: bounded logs support diagnosis
  does_not_prove: no code fix or production mutation was validated
  residual_risk: readonly logs may include sensitive content
  next_gate: bug-fix
```
"""
        parsed = extract_diagnosis_closure_fields(final_text)
        state = {
            "turn_stage": "debugging-diagnosis",
            "diagnosis_closure_present": parsed["present"],
            "diagnosis_closure_complete": parsed["complete"],
            "diagnosis_closure_status": parsed["status"],
            "diagnosis_closure_missing": parsed["missing"],
            "diagnosis_independent_review_status": parsed["review_status"],
            "diagnosis_selected_skills_only_review": parsed["selected_skills_only_review"],
        }
        contract = self._ready_contract_for_state(state)

        self.assertEqual(parsed["review_status"], "selected_skills_only")
        self.assertEqual(contract.verdict, "needs_review")
        self.assertIn("diagnosis_independent_review_result", contract.missing_items)


if __name__ == "__main__":
    unittest.main()
