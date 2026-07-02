from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_reducer():
    spec = importlib.util.spec_from_file_location(
        "changeforge_state_reducer_for_test",
        SCRIPT_DIR / "changeforge_state_reducer.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StateReducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reducer = load_reducer()

    def test_list_additive_dedupe(self) -> None:
        state = {"changed_paths": ["a.py"]}
        result = self.reducer.reduce_state_update(state, {"changed_paths": ["a.py", "b.py"]})
        self.assertEqual(result["changed_paths"], ["a.py", "b.py"])

    def test_bool_or_false_does_not_overwrite_true(self) -> None:
        state = {"read_evidence_seen": True}
        result = self.reducer.reduce_state_update(state, {"read_evidence_seen": False})
        self.assertTrue(result["read_evidence_seen"])

    def test_scalar_last_non_empty(self) -> None:
        state = {"turn_stage": "read"}
        result = self.reducer.reduce_state_update(state, {"turn_stage": ""})
        self.assertEqual(result["turn_stage"], "read")
        result = self.reducer.reduce_state_update(result, {"turn_stage": "edit"})
        self.assertEqual(result["turn_stage"], "edit")

    def test_active_skill_context_mapping_replace(self) -> None:
        state = {"active_skill_context": {"stage": "read"}}
        result = self.reducer.reduce_state_update(
            state, {"active_skill_context": {"stage": "edit", "refs": ["a", "b"]}}
        )
        self.assertEqual(result["active_skill_context"]["stage"], "edit")
        self.assertEqual(result["active_skill_context"]["refs"], ["a", "b"])

    def test_runtime_adapter_mapping_replace_preserves_empty_update(self) -> None:
        state = {"runtime_adapter": {"adapter": "codex"}}
        result = self.reducer.reduce_state_update(
            state,
            {
                "runtime_adapter": {
                    "adapter": "claude",
                    "supported_checks": ["stop_closure"],
                }
            },
        )
        self.assertEqual(result["runtime_adapter"]["adapter"], "claude")
        self.assertEqual(result["runtime_adapter"]["supported_checks"], ["stop_closure"])
        result = self.reducer.reduce_state_update(result, {"runtime_adapter": {}})
        self.assertEqual(result["runtime_adapter"]["adapter"], "claude")

    def test_compaction_preserves_old_active_context_on_empty_update(self) -> None:
        state = {"active_skill_context": {"stage": "review"}}
        result = self.reducer.reduce_state_update(state, {"active_skill_context": {}})
        self.assertEqual(result["active_skill_context"], {"stage": "review"})

    def test_unknown_field_ignored(self) -> None:
        result = self.reducer.reduce_state_update({}, {"raw_prompt": "secret"})
        self.assertNotIn("raw_prompt", result)

    def test_bounded_list_length(self) -> None:
        values = [f"path-{index}" for index in range(80)]
        result = self.reducer.reduce_state_update({}, {"changed_paths": values})
        self.assertEqual(len(result["changed_paths"]), 50)

    def test_new_evidence_fields_are_bounded_lists(self) -> None:
        result = self.reducer.reduce_state_update(
            {},
            {
                "normalized_events": ["event=PostToolUse"],
                "deleted_paths": ["old.py"],
                "generated_paths": ["dist/out.py"],
                "external_file_changes": ["outside.py"],
                "config_changes": ["settings.json"],
                "validation_results": ["pass:current:pytest"],
                "repair_events": ["repair:fix-1"],
                "rereview_events": ["rereview:fix-1"],
                "command_risks": ["safe:pytest"],
                "rollback_points": ["checkpoint:abc"],
                "post_edit_structure_findings": ["file_naming:count=0"],
                "choice_ids": ["api-boundary"],
                "choice_triggers": ["public_api_or_export"],
                "choice_status": ["missing"],
                "material_choice_surfaces": ["public_api_or_export"],
                "blocked_tool_category": ["edit"],
                "bounded_paths": ["src/api/orders.ts"],
                "choice_gate_seen": True,
                "choice_gate_blocked": True,
                "choice_resolution_evidence_seen": False,
            },
        )
        self.assertEqual(result["deleted_paths"], ["old.py"])
        self.assertEqual(result["validation_results"], ["pass:current:pytest"])
        self.assertEqual(result["post_edit_structure_findings"], ["file_naming:count=0"])
        self.assertEqual(result["choice_ids"], ["api-boundary"])
        self.assertEqual(result["material_choice_surfaces"], ["public_api_or_export"])
        self.assertTrue(result["choice_gate_seen"])
        self.assertTrue(result["choice_gate_blocked"])

    def test_professional_injection_digest_fields_are_bounded_and_redacted(self) -> None:
        result = self.reducer.reduce_state_update(
            {"professional_injection_digest": "sha256:old"},
            {
                "professional_injection_digests": ["sha256:new", "sha256:new"],
                "professional_injection_digest": "sha256:new",
                "last_professional_injection_event": "UserPromptSubmit",
                "raw_prompt": "must not persist",
                "stdout": "must not persist",
            },
        )

        self.assertEqual(result["professional_injection_digests"], ["sha256:new"])
        self.assertEqual(result["professional_injection_digest"], "sha256:new")
        self.assertEqual(result["last_professional_injection_event"], "UserPromptSubmit")
        self.assertNotIn("raw_prompt", result)
        self.assertNotIn("stdout", result)

    def test_context_control_records_latest_by_route_stage_and_redacted(self) -> None:
        result = self.reducer.reduce_state_update(
            {
                "context_control_records": [
                    {
                        "route_id": "route-a",
                        "current_stage": "coding",
                        "budget_mode": "minimal",
                        "skipped_reference_count": 0,
                    }
                ]
            },
            {
                "context_control_records": [
                    {
                        "route_id": "route-a",
                        "current_stage": "coding",
                        "budget_mode": "staged-plan",
                        "skipped_reference_count": 2,
                        "raw_prompt": "must not persist",
                        "skipped_references": [
                            {
                                "reference": "references/capabilities/122-plan-execution-consistency.md",
                                "reason": "omitted by budget",
                            }
                        ],
                    }
                ],
                "context_budget_findings": ["skipped_references 2 require JIT retrieval rationale"],
                "skipped_references": ["references/capabilities/122-plan-execution-consistency.md: omitted"],
            },
        )
        records = result["context_control_records"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["budget_mode"], "staged-plan")
        self.assertEqual(records[0]["skipped_reference_count"], 2)
        self.assertNotIn("raw_prompt", records[0])
        self.assertEqual(
            result["context_budget_findings"],
            ["skipped_references 2 require JIT retrieval rationale"],
        )
        self.assertEqual(
            result["skipped_references"],
            ["references/capabilities/122-plan-execution-consistency.md: omitted"],
        )

    def test_tool_output_boundaries_are_bounded_and_redacted(self) -> None:
        result = self.reducer.reduce_state_update(
            {},
            {
                "tool_output_boundaries": [
                    {
                        "schema_version": 1,
                        "tool_name": "Bash",
                        "event_name": "PostToolUse",
                        "output_size_class": "large",
                        "output_bytes": 32000,
                        "output_lines": 500,
                        "artifact_path": "/Users/example/project/output.log",
                        "artifact_path_source": "explicit_tool_result",
                        "digest": "sha256:abcdef1234567890abcdef12",
                        "bounded_summary": ["output_size_class=large"],
                        "truncation_advice": "rerun with redirect",
                        "llm_context_policy": "rerun_with_redirect",
                        "privacy_status": "pass",
                        "stdout": "must not persist",
                    }
                ],
                "artifact_references": ["/Users/example/project/output.log"],
            },
        )
        record = result["tool_output_boundaries"][0]
        self.assertEqual(record["output_bytes"], 32000)
        self.assertEqual(record["privacy_status"], "fail")
        self.assertNotIn("stdout", record)
        self.assertEqual(record["artifact_path"], "<local-artifact-path-redacted>")
        self.assertEqual(result["artifact_references"], ["<local-artifact-path-redacted>"])

    def test_process_phase_ledgers_keep_latest_by_route(self) -> None:
        result = self.reducer.reduce_state_update(
            {
                "process_phase_ledgers": [
                    {
                        "route_id": "route-a",
                        "current_phase": "pdd",
                        "phase_status": {"pdd": "draft"},
                    }
                ]
            },
            {
                "process_phase_ledgers": [
                    {
                        "route_id": "route-a",
                        "current_phase": "implementation",
                        "phase_status": {"pdd": "reviewed"},
                        "artifact_digests": {"pdd": "sha256:abcdef1234567890"},
                        "review_ids": {"pdd": "pdd-review-1"},
                    }
                ],
                "process_phase_ledger_seen": True,
                "pdd_reviewed": True,
            },
        )

        ledgers = result["process_phase_ledgers"]
        self.assertEqual(len(ledgers), 1)
        self.assertEqual(ledgers[0]["current_phase"], "implementation")
        self.assertEqual(ledgers[0]["phase_status"]["pdd"], "reviewed")
        self.assertTrue(result["process_phase_ledger_seen"])
        self.assertTrue(result["pdd_reviewed"])

    def test_phase_review_results_keep_latest_by_phase_and_review_id(self) -> None:
        first = {
            "review_id": "sdd-review-1",
            "phase": "sdd",
            "reviewer_skill": "ai-code-review-refactor",
            "owner_skill": "architecture-impact-reviewer",
            "reviewed_artifact_digest": "sha256:abcdef1234567890",
            "verdict": "fail",
            "score": 2,
        }
        second = {**first, "verdict": "pass", "score": 5}

        result = self.reducer.reduce_state_update(
            {"phase_review_results": [first]},
            {"phase_review_results": [second], "phase_review_seen": True, "sdd_reviewed": True},
        )

        self.assertEqual(len(result["phase_review_results"]), 1)
        self.assertEqual(result["phase_review_results"][0]["verdict"], "pass")
        self.assertEqual(result["phase_review_results"][0]["score"], 5)
        self.assertTrue(result["phase_review_seen"])
        self.assertTrue(result["sdd_reviewed"])

    def test_phase_findings_prioritize_unresolved(self) -> None:
        result = self.reducer.reduce_state_update(
            {},
            {
                "phase_review_findings": [
                    {"finding_id": "sdd-002", "phase": "sdd", "evidence": "fixed", "resolved": True},
                    {
                        "finding_id": "sdd-001",
                        "phase": "sdd",
                        "severity": "high",
                        "evidence": "missing material choice",
                        "required_fix": "add resolution evidence",
                        "blocks_next_stage": True,
                    },
                ]
            },
        )

        self.assertEqual(result["phase_review_findings"][0]["finding_id"], "sdd-001")

    def test_phase_repair_and_rereview_are_latest_by_finding_id(self) -> None:
        result = self.reducer.reduce_state_update(
            {
                "phase_repair_events": [{"finding_id": "sdd-001", "repair_summary": "old"}],
                "phase_rereview_events": [{"finding_id": "sdd-001", "verdict": "fail"}],
            },
            {
                "phase_repair_events": [{"finding_id": "sdd-001", "repair_summary": "new"}],
                "phase_rereview_events": [{"finding_id": "sdd-001", "verdict": "pass"}],
                "phase_rereview_passed": True,
            },
        )

        self.assertEqual(result["phase_repair_events"], [{"finding_id": "sdd-001", "repair_summary": "new"}])
        self.assertEqual(result["phase_rereview_events"], [{"finding_id": "sdd-001", "verdict": "pass"}])
        self.assertTrue(result["phase_rereview_passed"])

    def test_review_capsules_drop_raw_prompt_like_and_secret_keys(self) -> None:
        result = self.reducer.reduce_state_update(
            {},
            {
                "review_capsules": [
                    {
                        "capsule_id": "sdd-capsule-1",
                        "review_type": "sdd",
                        "user_request_summary": "bounded summary",
                        "raw_prompt": "must not persist",
                        "secret_token": "must not persist",
                        "source_evidence": {"read_files": ["src/runtime_governance/process_phase.py"]},
                    }
                ]
            },
        )

        capsule = result["review_capsules"][0]
        self.assertEqual(capsule["capsule_id"], "sdd-capsule-1")
        self.assertNotIn("raw_prompt", capsule)
        self.assertNotIn("secret_token", capsule)

    def test_context_control_policy_strips_raw_field_variants_without_losing_overhead_metrics(self) -> None:
        policy = load_module("changeforge_context_control_policy")
        cleaned = policy._sanitize_record(
            {
                "context_budget_tokens": 1200,
                "input_token_overhead_pct": 234.06,
                "raw_output_excerpt": "must not persist",
                "stdout_text": "must not persist",
                "safe_nested": {
                    "command_output_summary": "must not persist",
                    "turn_overhead": "not_collected",
                },
            }
        )
        rendered = str(cleaned)

        self.assertEqual(cleaned["context_budget_tokens"], 1200)
        self.assertEqual(cleaned["input_token_overhead_pct"], "234.06")
        self.assertNotIn("raw_output_excerpt", rendered)
        self.assertNotIn("stdout_text", rendered)
        self.assertNotIn("command_output_summary", rendered)
        self.assertEqual(cleaned["safe_nested"], {"turn_overhead": "not_collected"})


if __name__ == "__main__":
    unittest.main()
