from __future__ import annotations

import importlib.util
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
from runtime_governance import process_phase  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def strong_review(phase: str, digest: str) -> dict:
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
        "approved_scope": {"files": ["src/app.py"]},
        "review_source": "subagent_review_gate",
        "capsule_id": f"{phase}-capsule-1",
        "expected_artifact_digest": digest,
        "review_context_strength": "strong",
        "reviewer_boundary": "subagent",
    }


class RealLogReviewExecutionRegressionTests(unittest.TestCase):
    def test_final_text_phase_review_result_with_non_sha_digest_is_weak_disclosure(self) -> None:
        review = strong_review("sdd", "notify_1h_price_change_trace_v1")
        review["review_source"] = "final_handoff_disclosure"
        review["review_context_strength"] = "weak"
        self.assertFalse(process_phase.phase_review_passes(review, artifact_digest="sha256:" + ("a" * 64)))

    def test_manual_state_merge_empty_lists_does_not_clear_review_evidence(self) -> None:
        reducer = load_module("state_reducer_for_real_log_test", SCRIPT_DIR / "changeforge_state_reducer.py")
        state = {"phase_review_results": [strong_review("sdd", "sha256:" + ("a" * 64))]}
        reduced = reducer.reduce_state_update(state, {"phase_review_results": []})
        self.assertEqual(reduced["phase_review_results"][0]["review_id"], "sdd-review-1")

    def test_review_target_must_cover_actual_changed_files(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/app.py"],
                "implementation_review_results": [
                    {
                        "schema_version": 1,
                        "review_id": "implementation-review-1",
                        "review_source": "implementation_review_gate",
                        "review_context_strength": "strong",
                        "reviewed_diff_digest": "sha256:" + ("b" * 64),
                        "reviewed_files": ["docs/README.md"],
                        "changed_files_count": 1,
                        "reviewer_skill": "ai-code-review-refactor",
                        "owner_skill": "development-process-orchestrator",
                        "verdict": "pass",
                        "score": 5,
                        "findings": [],
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
        self.assertEqual(contract.implementation_review_status, "weak")

    def test_pretool_review_gap_renders_expert_note_not_internal_protocol(self) -> None:
        gate = load_module("process_phase_gate_for_real_log_test", SCRIPT_DIR / "changeforge_process_phase_gate.py")
        result = gate._evaluate_state_for_implementation(
            {"process_phase_ledger_seen": True, "process_phase_ledgers": []},
            runtime="codex",
        )
        message = gate.render_pre_tool_message(result)
        self.assertIn("Engineering expert note:", message)
        self.assertIn("Natural next step:", message)
        self.assertNotIn("review_" "required" "_action", message)
        self.assertNotIn("phase_" "review_result", message)
        self.assertNotIn("Do not add phase_reviews in final handoff", message)

    def test_repeated_stop_missing_review_degrades_but_does_not_resolve_review(self) -> None:
        contract = ClosureContract.from_state(
            {
                "turn_stage": "coding",
                "changed_paths": ["src/app.py"],
                "process_phase_ledger_seen": True,
                "process_phase_ledgers": [],
                "same_stop_missing_count": 2,
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
        self.assertIn("phase_ledger", contract.missing_items)
        self.assertNotEqual(contract.phase_review_status, "pass")


if __name__ == "__main__":
    unittest.main()
