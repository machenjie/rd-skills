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
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_gate(event: dict, cwd: Path, cache: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = "codex"
    env["CHANGEFORGE_HOOK_MODE"] = "warn"
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "changeforge_tool_output_boundary_gate.py")],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def load_cache_state(cache: Path) -> dict:
    matches = list(cache.glob("changeforge/hooks/*/current-turn.json"))
    if len(matches) != 1:
        raise AssertionError(f"expected one hook state file, found {matches}")
    return json.loads(matches[0].read_text(encoding="utf-8"))


class ToolOutputBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = load_module("changeforge_tool_output_boundary")

    def test_large_stdout_is_summarized_without_raw_retention(self) -> None:
        payload = "\n".join(f"line-{index}" for index in range(500))
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_response": {"stdout": payload},
        }
        record = self.boundary.tool_output_boundary_from_event(event)
        rendered = json.dumps(record, sort_keys=True)
        self.assertEqual(record["output_size_class"], "large")
        self.assertEqual(record["privacy_status"], "pass")
        self.assertEqual(record["llm_context_policy"], "rerun_with_redirect")
        self.assertTrue(record["digest"].startswith("sha256:"))
        self.assertNotIn("line-499", rendered)
        self.assertNotIn("stdout", rendered)

    def test_explicit_artifact_path_and_metadata_are_preserved(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_result": {
                "artifact_path": "artifacts/validation/pytest.log",
                "output_bytes": 64000,
                "output_lines": 900,
                "digest": "a" * 64,
            },
        }
        record = self.boundary.tool_output_boundary_from_event(event)
        self.assertEqual(record["output_size_class"], "large")
        self.assertEqual(record["artifact_path"], "artifacts/validation/pytest.log")
        self.assertEqual(record["artifact_path_source"], "explicit_tool_result")
        self.assertEqual(record["digest"], f"sha256:{'a' * 64}")
        self.assertEqual(record["llm_context_policy"], "artifact_reference_only")

    def test_runtime_without_output_metadata_records_unsupported(self) -> None:
        event = {"hook_event_name": "PostToolUse", "tool_name": "Bash"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(event, Path(cwd_s), Path(cache_s))
            state = load_cache_state(Path(cache_s))
        self.assertEqual(result.returncode, 0, result.stderr)
        record = state["tool_output_boundaries"][0]
        self.assertEqual(record["output_size_class"], "unsupported")
        self.assertEqual(record["llm_context_policy"], "unsupported_runtime")
        self.assertIn("output metadata not available", record["unsupported_reason"])
        self.assertIn("unsupported_runtime", result.stdout)
        self.assertFalse(state["validation_seen"])

    def test_small_inline_output_does_not_emit_advisory(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_result": {"stdout": "ok"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(event, Path(cwd_s), Path(cache_s))
            state = load_cache_state(Path(cache_s))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        record = state["tool_output_boundaries"][0]
        self.assertEqual(record["output_size_class"], "small")
        self.assertEqual(record["privacy_status"], "pass")
        self.assertEqual(record["llm_context_policy"], "inline_bounded")

    def test_unknown_output_emits_advisory_without_validation_success(self) -> None:
        gate = load_module("changeforge_tool_output_boundary_gate")
        self.assertTrue(
            gate._should_emit(
                {
                    "output_size_class": "unknown",
                    "llm_context_policy": "inline_bounded",
                    "privacy_status": "pass",
                }
            )
        )

    def test_secret_like_output_fails_privacy_without_raw_retention(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_result": {"stdout": "OPENAI_API_KEY=sk-ABCDEFGHIJK123456789"},
        }
        record = self.boundary.tool_output_boundary_from_event(event)
        rendered = json.dumps(record, sort_keys=True)
        self.assertEqual(record["privacy_status"], "fail")
        self.assertNotIn("ABCDEFGHIJK", rendered)
        self.assertNotIn("stdout", rendered)

    def test_large_output_with_artifact_emits_artifact_reference_advisory(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_result": {
                "artifact_path": "artifacts/validation/pytest.log",
                "output_bytes": 64000,
            },
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(event, Path(cwd_s), Path(cache_s))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("artifact_reference_only", result.stdout)
        self.assertIn("artifacts/validation/pytest.log", result.stdout)

    def test_large_output_without_artifact_emits_redirect_advisory(self) -> None:
        payload = "\n".join(f"line-{index}" for index in range(500))
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_result": {"stdout": payload},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(event, Path(cwd_s), Path(cache_s))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rerun_with_redirect", result.stdout)
        self.assertNotIn("line-499", result.stdout)

    def test_compaction_snapshot_keeps_safe_boundary_only(self) -> None:
        compaction = load_module("changeforge_compaction_contract")
        state = {
            "tool_output_boundaries": [
                {
                    "schema_version": 1,
                    "tool_name": "Bash",
                    "event_name": "PostToolUse",
                    "output_size_class": "large",
                    "stdout": "must not persist",
                    "artifact_path": "/Users/example/project/logs/full-output.txt",
                    "privacy_status": "pass",
                }
            ],
            "artifact_references": ["/Users/example/project/logs/full-output.txt"],
        }
        snapshot = compaction.snapshot_from_state(state, {"hook_event_name": "PreCompact"})
        rendered = json.dumps(snapshot, sort_keys=True)
        self.assertIn("tool_output_boundaries", snapshot)
        self.assertNotIn("must not persist", rendered)
        self.assertNotIn("/Users/example", rendered)
        self.assertNotIn("stdout", rendered)


if __name__ == "__main__":
    unittest.main()
