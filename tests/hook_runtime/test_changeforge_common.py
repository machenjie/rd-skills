from __future__ import annotations

import contextlib
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
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_hook(script_name: str, stdin: str, cwd: Path, cache: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env.pop("CHANGEFORGE_HOOK_MODE", None)
    env.pop("CHANGEFORGE_AGENT", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        input=stdin,
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


NEW_FINDING_FIELDS = (
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
    "structure_quality_findings",
)
CONTEXT_CONTROL_FIELDS = (
    "context_control_records",
    "tool_output_boundaries",
    "artifact_references",
    "branch_route_repair_summaries",
    "route_repair_forbidden_retries",
    "context_budget_findings",
    "skipped_references",
)


@contextlib.contextmanager
def cache_env(cache: Path):
    previous = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous


class ChangeForgeCommonTests(unittest.TestCase):
    def test_invalid_json_stdin_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            result = run_hook(
                "changeforge_post_edit_structure_gate.py",
                "not json",
                Path(cwd),
                Path(cache),
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_runtime_and_tool_normalization(self) -> None:
        common = load_common()
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "apply_patch",
            "toolInput": {"file_path": "src/services/order_service.py"},
        }
        self.assertEqual(common.detect_runtime(event), "codex")
        self.assertEqual(common.event_name(event), "PostToolUse")
        self.assertEqual(common.tool_name(event), "apply_patch")

    def test_runtime_detection_prefers_env_override_and_codex_snake_case(self) -> None:
        common = load_common()
        previous_agent = os.environ.get("CHANGEFORGE_AGENT")
        os.environ["CHANGEFORGE_AGENT"] = "codex"
        try:
            self.assertEqual(common.detect_runtime({"hookEventName": "Stop"}), "codex")
        finally:
            if previous_agent is None:
                os.environ.pop("CHANGEFORGE_AGENT", None)
            else:
                os.environ["CHANGEFORGE_AGENT"] = previous_agent

        self.assertEqual(common.detect_runtime({"hook_event_name": "PostToolUse"}), "codex")
        self.assertEqual(common.detect_runtime({"hookEventName": "PostToolUse"}), "claude")

    def test_runtime_detection_uses_claude_env_override_for_snake_case(self) -> None:
        common = load_common()
        previous_agent = os.environ.get("CHANGEFORGE_AGENT")
        os.environ["CHANGEFORGE_AGENT"] = "claude"
        try:
            self.assertEqual(
                common.detect_runtime({"hook_event_name": "PostToolUse"}),
                "claude",
            )
        finally:
            if previous_agent is None:
                os.environ.pop("CHANGEFORGE_AGENT", None)
            else:
                os.environ["CHANGEFORGE_AGENT"] = previous_agent

    def test_extract_changed_paths_from_apply_patch(self) -> None:
        common = load_common()
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_apply_patch.json").read_text())
        self.assertEqual(common.extract_changed_paths(event), ["src/services/order_service.py"])

    def test_extract_bash_command(self) -> None:
        common = load_common()
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_bash_kubectl.json").read_text())
        self.assertEqual(
            common.extract_bash_command(event),
            "kubectl apply -f deploy/helm/values.yaml",
        )

    def test_debug_log_writes_to_cache_when_enabled(self) -> None:
        common = load_common()
        previous_cache = os.environ.get("XDG_CACHE_HOME")
        previous_debug = os.environ.get("CHANGEFORGE_HOOK_DEBUG")
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ["CHANGEFORGE_HOOK_DEBUG"] = "1"
            try:
                common.debug_log(Path(cwd), "structure gate runtime=codex")
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
                if previous_debug is None:
                    os.environ.pop("CHANGEFORGE_HOOK_DEBUG", None)
                else:
                    os.environ["CHANGEFORGE_HOOK_DEBUG"] = previous_debug

            debug_logs = list(Path(cache).glob("changeforge/hooks/*/debug.log"))
            self.assertEqual(len(debug_logs), 1)
            self.assertIn("structure gate runtime=codex", debug_logs[0].read_text())

    def test_new_state_fields_initialized(self) -> None:
        common = load_common()
        state = common._empty_state()
        for field in (*NEW_FINDING_FIELDS, *CONTEXT_CONTROL_FIELDS):
            self.assertEqual(state[field], [])
        self.assertTrue(
            all(field in common.STATE_LIST_FIELDS for field in (*NEW_FINDING_FIELDS, *CONTEXT_CONTROL_FIELDS))
        )

    def test_new_state_fields_round_trip(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                common.save_state(
                    Path(cwd),
                    {
                        "runtime": "codex",
                        "file_naming_findings": ["a.go: mismatch"],
                        "comment_findings": ["a.go: uncommented"],
                        "structure_quality_findings": ["a.go: weak signature"],
                        "context_control_records": [
                            {
                                "route_id": "route-a",
                                "budget_mode": "single-stage",
                                "raw_prompt": "must not persist",
                                "overhead_evidence": {
                                    "selected_references": 3,
                                    "environment": "must not persist",
                                },
                            }
                        ],
                        "tool_output_boundaries": [
                            {
                                "schema_version": 1,
                                "tool_name": "Bash",
                                "event_name": "PostToolUse",
                                "output_size_class": "large",
                                "output_bytes": 64000,
                                "output_lines": 700,
                                "artifact_path": "artifacts/validation/pytest.log",
                                "artifact_path_source": "explicit_tool_result",
                                "digest": "sha256:" + "a" * 24,
                                "bounded_summary": ["size=large"],
                                "truncation_advice": "use artifact",
                                "llm_context_policy": "artifact_reference_only",
                                "privacy_status": "pass",
                                "stdout": "must not persist",
                            }
                        ],
                        "artifact_references": ["artifacts/validation/pytest.log"],
                        "branch_route_repair_summaries": [
                            {
                                "schema_version": 1,
                                "summary_id": "route-repair-common",
                                "trigger": "repeated_same_path_retry",
                                "abandoned_or_repaired_route": {
                                    "owner_skill": "quality-test-gate",
                                    "reviewer_skill": "ai-code-review-refactor",
                                    "hypothesis": "same-path retry",
                                    "files_touched": ["a.go"],
                                    "validation_result": "fail:pytest",
                                    "failure_reason": "same-path retry",
                                },
                                "reusable_findings": ["P1 unresolved"],
                                "forbidden_retries": ["same-path retry"],
                                "new_route": {
                                    "owner_skill": "quality-test-gate",
                                    "selected_capabilities": ["context-control-plane"],
                                    "validation_plan": ["rerun tests"],
                                },
                                "residual_risk": ["none"],
                                "privacy_status": "pass",
                                "stdout": "must not persist",
                            }
                        ],
                        "route_repair_forbidden_retries": ["same-path retry"],
                        "context_budget_findings": ["skipped_references 1 require JIT retrieval rationale"],
                        "skipped_references": [
                            "references/capabilities/105-code-clarity-maintainability.md: omitted by budget"
                        ],
                    },
                )
                loaded = common.load_state(Path(cwd))
        self.assertEqual(loaded["file_naming_findings"], ["a.go: mismatch"])
        self.assertEqual(loaded["comment_findings"], ["a.go: uncommented"])
        self.assertEqual(loaded["structure_quality_findings"], ["a.go: weak signature"])
        self.assertEqual(loaded["context_control_records"][0]["budget_mode"], "single-stage")
        self.assertNotIn("raw_prompt", loaded["context_control_records"][0])
        self.assertNotIn("environment", loaded["context_control_records"][0]["overhead_evidence"])
        self.assertEqual(loaded["tool_output_boundaries"][0]["output_bytes"], 64000)
        self.assertNotIn("stdout", loaded["tool_output_boundaries"][0])
        self.assertEqual(loaded["artifact_references"], ["artifacts/validation/pytest.log"])
        self.assertEqual(loaded["branch_route_repair_summaries"][0]["summary_id"], "route-repair-common")
        self.assertNotIn("stdout", loaded["branch_route_repair_summaries"][0])
        self.assertEqual(loaded["route_repair_forbidden_retries"], ["same-path retry"])
        self.assertEqual(
            loaded["context_budget_findings"],
            ["skipped_references 1 require JIT retrieval rationale"],
        )
        self.assertEqual(
            loaded["skipped_references"],
            ["references/capabilities/105-code-clarity-maintainability.md: omitted by budget"],
        )

    def test_merge_state_supports_finding_fields(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                common.merge_state(
                    Path(cwd),
                    "codex",
                    file_naming_findings=["x"],
                    reuse_findings=["y"],
                    extension_reuse_findings=["z"],
                    advanced_refactor_findings=["w"],
                    comment_findings=["c"],
                    structure_quality_findings=["q"],
                    context_control_records=[
                        {
                            "route_id": "active-runtime-route",
                            "current_stage": "coding",
                            "budget_mode": "minimal",
                            "full_output": "must not persist",
                        }
                    ],
                    tool_output_boundaries=[
                        {
                            "schema_version": 1,
                            "tool_name": "Bash",
                            "event_name": "PostToolUse",
                            "output_size_class": "large",
                            "artifact_path": "/Users/example/private.log",
                            "artifact_path_source": "explicit_tool_result",
                            "llm_context_policy": "rerun_with_redirect",
                            "privacy_status": "pass",
                            "stderr": "must not persist",
                        }
                    ],
                    artifact_references=["/Users/example/private.log"],
                    branch_route_repair_summaries=[
                        {
                            "schema_version": 1,
                            "summary_id": "route-repair-merge",
                            "trigger": "repeated_same_path_retry",
                            "abandoned_or_repaired_route": {
                                "files_touched": ["/Users/example/private/a.go"],
                                "failure_reason": "same-path retry",
                            },
                            "forbidden_retries": ["same-path retry"],
                            "new_route": {},
                            "privacy_status": "pass",
                            "raw_output": "must not persist",
                        }
                    ],
                    route_repair_forbidden_retries=["same-path retry"],
                    context_budget_findings=["selected_capabilities 9/8 over budget"],
                    skipped_references=["references/capabilities/122-plan-execution-consistency.md: omitted"],
                )
                state = common.load_state(Path(cwd))
        self.assertEqual(state["file_naming_findings"], ["x"])
        self.assertEqual(state["reuse_findings"], ["y"])
        self.assertEqual(state["extension_reuse_findings"], ["z"])
        self.assertEqual(state["advanced_refactor_findings"], ["w"])
        self.assertEqual(state["comment_findings"], ["c"])
        self.assertEqual(state["structure_quality_findings"], ["q"])
        self.assertEqual(state["context_control_records"][0]["budget_mode"], "minimal")
        self.assertNotIn("full_output", state["context_control_records"][0])
        self.assertNotIn("stderr", state["tool_output_boundaries"][0])
        self.assertEqual(state["tool_output_boundaries"][0]["artifact_path"], "<local-artifact-path-redacted>")
        self.assertEqual(state["artifact_references"], ["<local-artifact-path-redacted>"])
        self.assertEqual(state["branch_route_repair_summaries"][0]["summary_id"], "route-repair-merge")
        self.assertNotIn("raw_output", state["branch_route_repair_summaries"][0])
        self.assertEqual(
            state["branch_route_repair_summaries"][0]["abandoned_or_repaired_route"]["files_touched"],
            ["<local-path>"],
        )
        self.assertEqual(state["branch_route_repair_summaries"][0]["source_privacy_status"], "fail")
        self.assertEqual(state["branch_route_repair_summaries"][0]["retained_summary_privacy_status"], "pass")
        self.assertEqual(state["branch_route_repair_summaries"][0]["privacy_status"], "pass")
        self.assertEqual(state["route_repair_forbidden_retries"], ["same-path retry"])
        self.assertEqual(state["context_budget_findings"], ["selected_capabilities 9/8 over budget"])
        self.assertEqual(
            state["skipped_references"],
            ["references/capabilities/122-plan-execution-consistency.md: omitted"],
        )

    def test_legacy_state_file_missing_fields_is_compatible(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                path = common._state_path(Path(cwd))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps({"runtime": "codex", "changed_paths": ["a.py"]}),
                    encoding="utf-8",
                )
                loaded = common.load_state(Path(cwd))
        self.assertEqual(loaded["changed_paths"], ["a.py"])
        for field in (*NEW_FINDING_FIELDS, *CONTEXT_CONTROL_FIELDS):
            self.assertEqual(loaded[field], [])

    def test_state_written_to_cache_not_project_source(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                common.merge_state(Path(cwd), "codex", changed_paths=["a.py"])
            cache_state = list(Path(cache).glob("changeforge/hooks/*/current-turn.json"))
            project_state = list(Path(cwd).rglob("current-turn.json"))
        self.assertEqual(len(cache_state), 1)
        self.assertEqual(project_state, [])


if __name__ == "__main__":
    unittest.main()
