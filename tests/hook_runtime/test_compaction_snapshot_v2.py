from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_module(name: str):
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_hook(script_name: str, event: dict, cwd: Path, cache: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = "codex"
    event = {**event, "cwd": str(cwd)}
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def complete_state() -> dict:
    return {
        "turn_id": "turn-a",
        "event_index": 8,
        "turn_stage": "coding",
        "active_skill_context": {
            "route_id": "context-control-phase-4",
            "selected_skills": ["change-forge-router", "quality-test-gate"],
            "selected_capabilities": ["context-control-plane", "context-packaging"],
            "required_quality_gates": ["security/privacy gate", "test/regression gate"],
            "current_stage": "coding",
            "pdd_summary": ["add v2 compaction fields"],
            "ddd_invariants": ["state stays bounded"],
            "sdd_decisions": ["extend compaction contract"],
            "tdd_validation_plan": ["python3 -m unittest discover -s tests/hook_runtime"],
            "residual_risk": ["none known"],
            "context_control": {
                "budget_mode": "staged-plan",
                "selected_reference_count": 2,
                "skipped_reference_count": 1,
                "over_budget_findings": ["one skipped reference requires JIT retrieval"],
                "jit_retrieval_required": True,
                "tool_output_boundary_required": True,
            },
        },
        "changed_paths": ["src/hook-runtime/scripts/changeforge_compaction_contract.py"],
        "read_paths": ["src/hook-runtime/scripts/changeforge_compaction_contract.py"],
        "validation_results": ["pass:python3 -m unittest discover -s tests/hook_runtime"],
        "review_findings": ["resolved:rereview passed"],
        "repair_events": ["repair:finding-1"],
        "rereview_events": ["rereview:finding-1"],
        "closure_risk_surfaces": ["none known"],
        "reference_loads": ["references/capabilities/128-context-control-plane.md"],
        "reuse_findings": ["same-pattern:changeforge_tool_output_boundary.py"],
        "skipped_references": ["references/capabilities/122-plan-execution-consistency.md: omitted by budget"],
        "tool_output_boundaries": [
            {
                "schema_version": 1,
                "tool_name": "Bash",
                "event_name": "PostToolUse",
                "output_size_class": "large",
                "artifact_path": "artifacts/validation/unittest.log",
                "artifact_path_source": "explicit_tool_result",
                "llm_context_policy": "artifact_reference_only",
                "privacy_status": "pass",
            }
        ],
        "artifact_references": ["artifacts/validation/unittest.log"],
        "branch_route_repair_summaries": [
            {
                "schema_version": 1,
                "summary_id": "route-repair-test",
                "trigger": "repeated_same_path_retry",
                "abandoned_or_repaired_route": {
                    "owner_skill": "quality-test-gate",
                    "reviewer_skill": "ai-code-review-refactor",
                    "hypothesis": "same path retry was abandoned",
                    "files_touched": ["src/hook-runtime/scripts/changeforge_compaction_contract.py"],
                    "validation_result": "fail:old route",
                    "failure_reason": "same-path retry",
                },
                "reusable_findings": ["do not retry same path without new route"],
                "forbidden_retries": ["same-path retry"],
                "new_route": {
                    "owner_skill": "quality-test-gate",
                    "selected_capabilities": ["context-control-plane"],
                    "validation_plan": ["rerun hook runtime tests"],
                },
                "residual_risk": ["none known"],
                "privacy_status": "pass",
            }
        ],
        "last_material_edit_index": 6,
        "last_validation_command_index": 7,
    }


class CompactionSnapshotV2Tests(unittest.TestCase):
    def test_v2_snapshot_includes_v1_required_fields_and_context_control_fields(self) -> None:
        compaction = load_module("changeforge_compaction_contract")
        snapshot = compaction.snapshot_from_state(
            complete_state(),
            {"hook_event_name": "PreCompact"},
        )

        self.assertEqual(snapshot["schema_version"], 2)
        for field in compaction.REQUIRED_CONTEXT_FIELDS:
            self.assertIn(field, snapshot)
        self.assertEqual(snapshot["missing_required_fields"], [])
        self.assertEqual(snapshot["snapshot_source"], "pre_compact")
        self.assertIsNone(snapshot["tokens_before"])
        self.assertIsNone(snapshot["first_kept_entry_id"])
        self.assertIn("runtime_tokens_before_not_exposed", snapshot["warnings"])
        self.assertIn("runtime_first_kept_entry_id_not_exposed", snapshot["warnings"])

        context_control = snapshot["context_control"]
        self.assertEqual(context_control["budget_mode"], "staged-plan")
        self.assertEqual(context_control["selected_reference_count"], 2)
        self.assertEqual(context_control["skipped_reference_count"], 1)
        self.assertTrue(context_control["jit_retrieval_required"])
        self.assertTrue(context_control["tool_output_boundary_required"])
        self.assertIn("selected_reference_policy", snapshot)
        self.assertIn("omitted_context", snapshot)
        self.assertIn("tool_output_boundaries", snapshot)
        self.assertIn("artifact_references", snapshot)
        self.assertIn("branch_route_repair_summaries", snapshot)

    def test_v1_snapshot_sanitizes_without_v2_fields(self) -> None:
        compaction = load_module("changeforge_compaction_contract")
        legacy = compaction.snapshot_from_state(
            complete_state(),
            {"hook_event_name": "PreCompact"},
        )
        legacy["schema_version"] = 1
        legacy.pop("selected_reference_policy", None)
        legacy.pop("omitted_context", None)
        legacy.pop("branch_route_repair_summaries", None)
        legacy.pop("tokens_before", None)
        legacy.pop("first_kept_entry_id", None)
        legacy.pop("snapshot_source", None)

        sanitized = compaction.sanitize_compaction_snapshot(legacy)

        self.assertEqual(sanitized["schema_version"], 1)
        self.assertEqual(sanitized["missing_required_fields"], [])
        self.assertNotIn("selected_reference_policy", sanitized)
        self.assertNotIn("snapshot_source", sanitized)

    def test_generic_compact_reinjects_complete_snapshot_without_overwriting_it(self) -> None:
        common = load_module("changeforge_common")
        compaction = load_module("changeforge_compaction_contract")
        snapshot = compaction.snapshot_from_state(
            complete_state(),
            {"hook_event_name": "PreCompact"},
        )

        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                common.merge_state(
                    cwd,
                    "codex",
                    turn_stage="review",
                    active_skill_context={"stage": "review"},
                    compaction_snapshots=[snapshot],
                )
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache

            result = run_hook(
                "changeforge_compaction_snapshot.py",
                {"hook_event_name": "SessionStart", "source": "compact"},
                cwd,
                cache,
            )

            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                state = common.load_state(cwd)
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(state["compaction_snapshots"]), 1)
        self.assertEqual(state["compaction_snapshots"][0]["snapshot_id"], snapshot["snapshot_id"])
        self.assertEqual(state["active_skill_context"]["route_id"], "context-control-phase-4")
        self.assertIn("compaction_degraded:session_compact", state["runtime_adapter"]["active_degradation"])


class BranchRouteSummaryTests(unittest.TestCase):
    def test_repeated_same_path_retry_summary_is_bounded_and_redacted(self) -> None:
        summary_mod = load_module("changeforge_branch_route_summary")
        state = {
            "owner_skill": "quality-test-gate",
            "reviewer_skill": "ai-code-review-refactor",
            "changed_paths": ["/Users/example/private/project/src/app.py"],
            "validation_results": ["fail:pytest"],
            "route_repair_forbidden_retries": [
                "same-path retry for /Users/example/private/project/src/app.py"
            ],
            "raw_output": "line 1\nline 2",
            "active_skill_context": {
                "selected_capabilities": ["context-control-plane"],
                "tdd_validation_plan": ["rerun focused tests"],
            },
        }

        summary = summary_mod.build_route_repair_summary(state)
        rendered = json.dumps(summary, sort_keys=True)

        self.assertEqual(summary["trigger"], "repeated_same_path_retry")
        self.assertEqual(summary["privacy_status"], "fail")
        self.assertTrue(summary["forbidden_retries"])
        self.assertNotIn("/Users/example", rendered)
        self.assertNotIn("raw_output", rendered)
        self.assertNotIn("line 1", rendered)
        self.assertIn("<local-path>", rendered)

    def test_state_reducer_keeps_latest_route_repair_summaries_and_forbidden_retries(self) -> None:
        reducer = load_module("changeforge_state_reducer")
        summary = {
            "schema_version": 1,
            "summary_id": "route-repair-1",
            "trigger": "repeated_same_path_retry",
            "abandoned_or_repaired_route": {
                "owner_skill": "quality-test-gate",
                "reviewer_skill": "ai-code-review-refactor",
                "hypothesis": "same path retry",
                "files_touched": ["src/app.py"],
                "validation_result": "fail:pytest",
                "failure_reason": "same-path retry",
            },
            "reusable_findings": ["P1 unresolved finding"],
            "forbidden_retries": ["same-path retry"],
            "new_route": {
                "owner_skill": "quality-test-gate",
                "selected_capabilities": ["context-control-plane"],
                "validation_plan": ["rerun tests"],
            },
            "residual_risk": ["none"],
            "privacy_status": "pass",
        }

        state = reducer.reduce_state_update(
            {},
            {
                "branch_route_repair_summaries": [summary, {**summary, "raw_output": "must not persist"}],
                "route_repair_forbidden_retries": ["same-path retry", "same-path retry"],
            },
        )

        self.assertEqual(len(state["branch_route_repair_summaries"]), 1)
        self.assertEqual(state["branch_route_repair_summaries"][0]["summary_id"], "route-repair-1")
        self.assertEqual(state["route_repair_forbidden_retries"], ["same-path retry"])

    def test_prompt_signals_are_safe_bounded_metadata_not_raw_prompt(self) -> None:
        summary_mod = load_module("changeforge_branch_route_summary")

        summary = summary_mod.build_route_repair_summary(
            {
                "prompt_signals": ["route_repair"],
                "route_repair_forbidden_retries": ["same-path retry"],
                "changed_paths": ["src/app.py"],
            }
        )

        self.assertEqual(summary["privacy_status"], "pass")


if __name__ == "__main__":
    unittest.main()
