from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
COLLECTOR = SCRIPT_DIR / "changeforge_post_tool_collector.py"


def run_collector(event: dict, *, agent: str = "codex", mode: str = "warn") -> tuple[subprocess.CompletedProcess[str], dict]:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache_tmp:
        cwd = Path(tmp)
        cache = Path(cache_tmp)
        event = {**event, "cwd": str(cwd)}
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = str(cache)
        env["CHANGEFORGE_AGENT"] = agent
        env["CHANGEFORGE_HOOK_MODE"] = mode
        result = subprocess.run(
            [sys.executable, str(COLLECTOR)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=str(cwd),
            env=env,
            check=False,
        )
        return result, load_state(cache)


def load_state(cache: Path) -> dict:
    matches = list(cache.glob("changeforge/hooks/*/current-turn.json"))
    if not matches:
        return {}
    if len(matches) != 1:
        raise AssertionError(f"expected one hook state file, found {matches}")
    return json.loads(matches[0].read_text(encoding="utf-8"))


class PostToolCollectorTests(unittest.TestCase):
    def test_read_tool_records_evidence_without_advisory_output(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "src/app.py"},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("src/app.py", state["read_paths"])
        self.assertTrue(state["read_evidence_seen"])

    def test_edit_tool_records_structure_and_risk_evidence(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Add File: src/services/order_service.py\n"
            "+class OrderService:\n"
            "+    pass\n"
            "*** End Patch\n"
        )
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Design risk detected", result.stdout)
        self.assertIn("src/services/order_service.py", state["changed_paths"])
        self.assertTrue(state["post_edit_structure_findings"])

    def test_bash_validation_records_result_without_advisory_output(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "python3 -m unittest discover -s tests"},
                "tool_result": {"exit_code": 0},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(state["validation_results"])
        self.assertTrue(state["validation_command_seen"])

    def test_review_diff_records_review_evidence_without_noise(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "get_pr_diff",
                "tool_input": {"pull_request": "12"},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(state["review_evidence_seen"])
        self.assertTrue(state["review_artifact_seen"])

    def test_write_input_content_without_tool_result_does_not_emit_boundary(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "docs/notes.md",
                    "content": "implementation note, not tool output",
                },
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Tool Output Boundary", result.stdout)
        self.assertEqual(state.get("tool_output_boundaries", []), [])
        self.assertEqual(state.get("context_budget_findings", []), [])

    def test_edit_input_replacement_content_without_tool_result_does_not_emit_boundary(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "docs/notes.md",
                    "old_string": "before",
                    "new_string": "after",
                    "content": "replacement body, not tool output",
                },
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Tool Output Boundary", result.stdout)
        self.assertEqual(state.get("tool_output_boundaries", []), [])
        self.assertEqual(state.get("context_budget_findings", []), [])

    def test_failure_event_uses_tool_output_boundary(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUseFailure",
                "tool_name": "Bash",
            },
            agent="copilot",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(state["tool_output_boundaries"][0]["llm_context_policy"], "unsupported_runtime")

    def test_large_tool_result_output_emits_boundary_and_omits_raw_output(self) -> None:
        payload = "\n".join(f"line-{index}" for index in range(500))
        for output_key in ("stdout", "content"):
            with self.subTest(output_key=output_key):
                result, state = run_collector(
                    {
                        "hook_event_name": "PostToolUse",
                        "tool_name": "Bash",
                        "tool_result": {output_key: payload},
                    }
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("rerun_with_redirect", result.stdout)
                self.assertNotIn("line-499", result.stdout)
                self.assertEqual(state["tool_output_boundaries"][0]["output_size_class"], "large")

    def test_large_string_output_container_emits_boundary(self) -> None:
        payload = "\n".join(f"line-{index}" for index in range(500))
        for output_key in ("result", "toolResult", "response"):
            with self.subTest(output_key=output_key):
                result, state = run_collector(
                    {
                        "hook_event_name": "PostToolUse",
                        "tool_name": "Bash",
                        output_key: payload,
                    }
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("rerun_with_redirect", result.stdout)
                self.assertNotIn("line-499", result.stdout)
                self.assertEqual(state["tool_output_boundaries"][0]["output_size_class"], "large")

    def test_tool_input_result_and_content_do_not_emit_boundary(self) -> None:
        payload = "\n".join(f"line-{index}" for index in range(500))
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {
                    "result": payload,
                    "content": payload,
                },
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Tool Output Boundary", result.stdout)
        self.assertEqual(state.get("tool_output_boundaries", []), [])
        self.assertEqual(state.get("context_budget_findings", []), [])

    def test_small_output_without_evidence_is_noop(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_result": {"stdout": "ok"},
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(state, {})

    def test_unsupported_event_without_evidence_is_noop(self) -> None:
        result, state = run_collector(
            {
                "hook_event_name": "Notification",
                "message": "hello",
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(state, {})


if __name__ == "__main__":
    unittest.main()
