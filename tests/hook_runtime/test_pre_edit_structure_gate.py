from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_pre_edit_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_gate():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "changeforge_pre_edit_structure_gate_for_test",
            SCRIPT_DIR / "changeforge_pre_edit_structure_gate.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(SCRIPT_DIR))
        except ValueError:
            pass


def run_gate(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str | None = None,
) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = "codex"
    if mode is None:
        env.pop("CHANGEFORGE_PRE_EDIT_MODE", None)
        env.pop("CHANGEFORGE_HOOK_MODE", None)
    else:
        env["CHANGEFORGE_PRE_EDIT_MODE"] = mode
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "changeforge_pre_edit_structure_gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def load_state(cwd: Path, cache: Path) -> dict:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        return common.load_state(cwd)
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


def seed_read_state(cwd: Path, cache: Path) -> None:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        common.merge_state(
            cwd,
            "codex",
            read_paths=["src/services/order_service.py"],
            read_evidence_seen=True,
        )
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


def patch_event(path: str = "src/services/order_service.py") -> dict:
    return {
        "runtime": "codex",
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {
            "patch": (
                "*** Begin Patch\n"
                f"*** Add File: {path}\n"
                "+class OrderService:\n"
                "+    pass\n"
                "*** End Patch\n"
            )
        },
    }


def write_event(path: str, content: str) -> dict:
    return {
        "runtime": "codex",
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": path, "content": content},
    }


def multiedit_event(path: str, replacement: str) -> dict:
    return {
        "runtime": "codex",
        "hook_event_name": "PreToolUse",
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": path,
            "edits": [{"old_string": "pass", "replacement": replacement}],
        },
    }


class PreEditStructureGateTests(unittest.TestCase):
    def test_edit_without_read_evidence_warns_and_records_state(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_gate(patch_event(), cwd, cache)
            state = load_state(cwd, cache)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ChangeForge Pre-Edit Implementation Structure Gate", result.stdout)
        self.assertIn("read_evidence", result.stdout)
        self.assertTrue(state["implementation_preflight_required"])
        self.assertTrue(state["pre_edit_missing_read_evidence"])

    def test_edit_without_read_evidence_blocks_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(patch_event(), Path(cwd_s), Path(cache_s), mode="block")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")

    def test_new_file_without_placement_warns_with_read_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_read_state(cwd, cache)
            result = run_gate(patch_event(), cwd, cache)
        self.assertIn("placement_decision", result.stdout)
        self.assertNotIn('"decision": "block"', result.stdout)

    def test_helper_like_path_without_reuse_warns(self) -> None:
        event = patch_event("src/common/utils/token_helper.py")
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_read_state(cwd, cache)
            result = run_gate(event, cwd, cache)
        self.assertIn("reuse_decision", result.stdout)

    def test_class_patch_without_object_boundary_warns(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_read_state(cwd, cache)
            result = run_gate(patch_event(), cwd, cache)
        self.assertIn("object_boundary", result.stdout)

    def test_manifest_present_records_preflight_without_warning(self) -> None:
        manifest = (
            "```yaml\n"
            "changeforge_implementation_preflight:\n"
            "  read_evidence:\n"
            "    target_files:\n"
            "      - src/services/order_service.py\n"
            "    sibling_files:\n"
            "      - src/services/user_service.py\n"
            "  placement_decision:\n"
            "    target_file: src/services/order_service.py\n"
            "    reason: service module owns order orchestration\n"
            "  reuse_decision:\n"
            "    direct_reuse:\n"
            "      - symbol_or_path: src/services/base.py\n"
            "  object_boundary:\n"
            "    artifact_type: class\n"
            "    owner: src/services/order_service.py\n"
            "    state_or_invariant: service class owns order orchestration boundary\n"
            "  test_plan:\n"
            "    validation_commands:\n"
            "      - pytest tests/test_order_service.py\n"
            "  risk:\n"
            "    rollback_or_revert_path: revert patch\n"
            "```\n"
        )
        event = {**patch_event(), "last_assistant_message": manifest}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_gate(event, cwd, cache)
            state = load_state(cwd, cache)
        self.assertEqual(result.stdout, "")
        self.assertTrue(state["implementation_preflight_seen"])
        self.assertTrue(state["implementation_preflight_complete"])
        self.assertTrue(state["implementation_preflights"])

    def test_write_plain_class_content_requires_object_boundary(self) -> None:
        event = write_event("src/domain/order.py", "class OrderService:\n    pass\n")
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_read_state(cwd, cache)
            result = run_gate(event, cwd, cache)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("object_boundary", result.stdout)

    def test_write_plain_export_function_requires_public_api_rationale(self) -> None:
        event = write_event("web/src/api/orders.ts", "export function x() {\n  return 1;\n}\n")
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_read_state(cwd, cache)
            result = run_gate(event, cwd, cache)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("object_boundary", result.stdout)

    def test_multiedit_replacement_class_requires_object_boundary(self) -> None:
        event = multiedit_event("src/domain/order.py", "class OrderService:\n    pass\n")
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_read_state(cwd, cache)
            result = run_gate(event, cwd, cache)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("object_boundary", result.stdout)

    def test_block_mode_blocks_existing_code_edit_without_read_or_preflight(self) -> None:
        event = {
            "runtime": "codex",
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "patch": (
                    "*** Begin Patch\n"
                    "*** Update File: src/domain/order.py\n"
                    "@@\n"
                    "+def calculate_total():\n"
                    "+    return 1\n"
                    "*** End Patch\n"
                )
            },
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(event, Path(cwd_s), Path(cache_s), mode="block")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")

    def test_weak_preflight_manifest_does_not_satisfy_required_fields(self) -> None:
        common = load_common()
        manifest = (
            "```yaml\n"
            "changeforge_implementation_preflight:\n"
            "  placement_decision: yes\n"
            "  reuse_decision: yes\n"
            "  object_boundary: yes\n"
            "  test_plan: yes\n"
            "  risk: yes\n"
            "```\n"
        )
        result = common.extract_implementation_preflight_fields(manifest)
        self.assertTrue(result["present"])
        self.assertFalse(result["placement_decision"])
        self.assertFalse(result["reuse_decision"])
        self.assertFalse(result["object_boundary"])
        self.assertFalse(result["test_plan"])
        self.assertFalse(result["risk"])

    def test_repository_context_parser_requires_structured_fields(self) -> None:
        common = load_common()
        negative = "repository context was not checked; owning surface and caller/callee are unknown"
        self.assertFalse(common.extract_repository_context_fields(negative)["complete"])
        structured = (
            "```yaml\n"
            "repository_context:\n"
            "  source_of_truth:\n"
            "    - src/hook-runtime/scripts/changeforge_common.py\n"
            "  no_reuse_candidate_found: true\n"
            "  test_candidates:\n"
            "    - python3 -m unittest tests/hook_runtime/test_pre_edit_structure_gate.py\n"
            "  graph_freshness: current\n"
            "  residual_risk:\n"
            "    - none\n"
            "```\n"
        )
        result = common.extract_repository_context_fields(structured)
        self.assertTrue(result["complete"])
        self.assertTrue(result["no_reuse_candidate_found"])

    def test_structural_edit_without_repository_context_or_preflight_read_warns(self) -> None:
        event = {
            **patch_event(),
            "last_assistant_message": "repository context was not checked; owning surface remains unknown",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_gate(event, Path(cwd_s), Path(cache_s))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repository_context", result.stdout)

    def test_incomplete_manifest_records_seen_but_not_complete(self) -> None:
        manifest = (
            "```yaml\n"
            "changeforge_implementation_preflight:\n"
            "  read_evidence:\n"
            "    target_files:\n"
            "      - src/services/order_service.py\n"
            "  placement_decision:\n"
            "    target_file: src/services/order_service.py\n"
            "    reason: service module owns order orchestration\n"
            "  reuse_decision:\n"
            "    new_code_justification: no compatible extension point\n"
            "  object_boundary:\n"
            "    artifact_type: class\n"
            "  test_plan:\n"
            "    validation_commands:\n"
            "      - pytest tests/test_order_service.py\n"
            "  risk:\n"
            "    rollback_or_revert_path: revert patch\n"
            "```\n"
        )
        event = {**patch_event(), "last_assistant_message": manifest}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_gate(event, cwd, cache)
            state = load_state(cwd, cache)
        self.assertIn("object_boundary", result.stdout)
        self.assertTrue(state["implementation_preflight_seen"])
        self.assertFalse(state["implementation_preflight_complete"])

    def test_fail_closed_blocks_on_unhandled_exception(self) -> None:
        gate = load_gate()
        output = StringIO()
        with patch.dict(
            os.environ,
            {
                "CHANGEFORGE_AGENT": "codex",
                "CHANGEFORGE_PRE_EDIT_STRUCTURE_FAILURE_MODE": "fail_closed",
            },
            clear=True,
        ), patch.object(gate, "_main", side_effect=RuntimeError("boom")), redirect_stdout(output):
            self.assertEqual(gate.main(), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["decision"], "block")
        self.assertIn("failed closed", payload["reason"])

    def test_transcript_tail_reads_bounded_tail(self) -> None:
        gate = load_gate()
        with tempfile.TemporaryDirectory() as cwd_s:
            transcript = Path(cwd_s) / "transcript.jsonl"
            transcript.write_text(
                ("x" * (gate.MAX_TRANSCRIPT_BYTES + 100))
                + "\n"
                + json.dumps({"role": "assistant", "content": "tail content"})
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(gate._transcript_tail(str(transcript)), "tail content")

    def test_non_edit_events_do_not_require_preflight(self) -> None:
        gate = load_gate()
        for event in (
            {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"hook_event_name": "UserPromptSubmit", "prompt": "review latest commit"},
            {"hook_event_name": "UserPromptSubmit", "prompt": "what is code review?"},
        ):
            with self.subTest(event=event):
                result = gate.evaluate_pre_edit(event, {}, ROOT)
                self.assertFalse(result["required"])


if __name__ == "__main__":
    unittest.main()
