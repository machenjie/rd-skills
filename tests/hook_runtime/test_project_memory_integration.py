from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.privacy import sanitize_memory_event


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_memory_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_pre_edit_gate():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "changeforge_pre_edit_for_memory_test",
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


def read_memory_records(cache: Path) -> list[dict]:
    records: list[dict] = []
    for path in cache.glob("changeforge/memory/*/events/*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


class ProjectMemoryIntegrationTests(unittest.TestCase):
    def test_telemetry_writer_mirrors_bounded_memory_event(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                common.write_telemetry_event(
                    cwd,
                    runtime="codex",
                    hook_name="stop_closure_gate",
                    event_name="Stop",
                    mode="warn",
                    changed_paths=["src/app.py"],
                    validation_evidence_detected=True,
                    residual_risk_detected=True,
                )
                records = read_memory_records(cache)
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["type"], "validation_result")
        self.assertEqual(records[0]["paths"], ["src/app.py"])
        self.assertEqual(records[0]["outcome"], "success")

    def test_pre_edit_warns_for_fragile_file_without_memory_summary(self) -> None:
        common = load_common()
        gate = load_pre_edit_gate()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                for event_id in ("fragile-1", "fragile-2"):
                    common.write_memory_event(
                        cwd,
                        {
                            "event_id": event_id,
                            "task_fingerprint": "task",
                            "type": "review_finding",
                            "paths": ["src/services/order_service.py"],
                            "outcome": "unknown",
                        },
                    )
                result = gate.evaluate_pre_edit(
                    _patch_event(_complete_preflight()),
                    {"read_evidence_seen": True},
                    cwd,
                )
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
        self.assertIn("memory_summary_evidence", result["missing"])
        self.assertIn("fragile file memory gate", " ".join(result["findings"]))

    def test_direct_memory_write_drops_external_absolute_paths(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            (cwd / "src").mkdir()
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                common.write_memory_event(
                    cwd,
                    {
                        "event_id": "privacy-path",
                        "task_fingerprint": "task",
                        "type": "implementation_attempt",
                        "paths": [str(cwd / "src" / "app.py"), "/Users/example/private.py", "../escape.py"],
                        "outcome": "failed",
                    },
                )
                records = read_memory_records(cache)
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
        self.assertEqual(records[0]["paths"], ["src/app.py"])

    def test_repeat_failure_blocks_third_same_path_edit_without_diagnosis(self) -> None:
        common = load_common()
        gate = load_pre_edit_gate()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            previous_mode = os.environ.get("CHANGEFORGE_PRE_EDIT_MODE")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            os.environ["CHANGEFORGE_PRE_EDIT_MODE"] = "block"
            try:
                _seed_repeat_failures(common, cwd)
                result = gate.evaluate_pre_edit(
                    _patch_event(_complete_preflight()),
                    {"read_evidence_seen": True},
                    cwd,
                )
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
                if previous_mode is None:
                    os.environ.pop("CHANGEFORGE_PRE_EDIT_MODE", None)
                else:
                    os.environ["CHANGEFORGE_PRE_EDIT_MODE"] = previous_mode
        self.assertIn("failure_diagnosis_route", result["missing"])
        self.assertTrue(result["block"])

    def test_repeat_failure_blocks_when_prior_failures_have_different_stages(self) -> None:
        common = load_common()
        gate = load_pre_edit_gate()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            previous_mode = os.environ.get("CHANGEFORGE_PRE_EDIT_MODE")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            os.environ["CHANGEFORGE_PRE_EDIT_MODE"] = "block"
            try:
                _seed_stage_specific_repeat_failures(common, cwd)
                result = gate.evaluate_pre_edit(
                    _patch_event(_complete_preflight()),
                    {"read_evidence_seen": True, "turn_stage": "plan"},
                    cwd,
                )
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
                if previous_mode is None:
                    os.environ.pop("CHANGEFORGE_PRE_EDIT_MODE", None)
                else:
                    os.environ["CHANGEFORGE_PRE_EDIT_MODE"] = previous_mode
        self.assertIn("failure_diagnosis_route", result["missing"])
        self.assertTrue(result["block"])

    def test_repeat_failure_allows_edit_with_diagnosis_route_evidence(self) -> None:
        common = load_common()
        gate = load_pre_edit_gate()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                _seed_repeat_failures(common, cwd)
                result = gate.evaluate_pre_edit(
                    _patch_event(_complete_preflight() + "\nfailure-diagnosis completed\n"),
                    {"read_evidence_seen": True},
                    cwd,
                )
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
        self.assertNotIn("failure_diagnosis_route", result["missing"])
        self.assertFalse(result["block"])

    def test_hook_and_project_memory_sanitizers_share_privacy_contract(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd_s:
            cwd = Path(cwd_s)
            (cwd / "src").mkdir()
            raw = {
                "event_id": "privacy-equivalence",
                "task_fingerprint": "task",
                "type": "implementation_attempt",
                "paths": [str(cwd / "src" / "app.py"), "/Users/example/private.py", "../escape.py"],
                "symbols": ["OrderService", "token=SHOULD_DROP"],
                "prompt": "raw prompt",
                "raw_prompt": "raw prompt",
                "env": {"API_KEY": "secret"},
                "stdout": "full stdout",
                "stderr": "full stderr",
                "secret": "secret",
                "api_key": "secret",
                "evidence_refs": ["cmd:pytest -q", "Bearer abcdefghijklmnop", "token=SECRET123"],
                "outcome": "failed",
            }
            hook_record = common._sanitize_memory_event(cwd, raw)
            project_record = sanitize_memory_event(raw, repo=cwd)
        self.assertEqual(hook_record["paths"], ["src/app.py"])
        self.assertEqual(project_record["paths"], ["src/app.py"])
        self.assertEqual(hook_record["evidence_refs"], ["cmd:pytest -q"])
        self.assertEqual(project_record["evidence_refs"], ["cmd:pytest -q"])
        self.assertEqual(set(hook_record), set(project_record))
        text = json.dumps({"hook": hook_record, "project": project_record})
        for forbidden in ("raw prompt", "API_KEY", "full stdout", "full stderr", "/Users/example", "Bearer", "token=SECRET"):
            self.assertNotIn(forbidden, text)

    def test_memory_disabled_by_policy_is_not_degraded(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd_s:
            cwd = Path(cwd_s)
            previous = os.environ.get("CHANGEFORGE_MEMORY")
            os.environ["CHANGEFORGE_MEMORY"] = "off"
            try:
                advice = common.memory_closure_advice(cwd, {"changed_paths": ["src/app.py"]})
            finally:
                if previous is None:
                    os.environ.pop("CHANGEFORGE_MEMORY", None)
                else:
                    os.environ["CHANGEFORGE_MEMORY"] = previous
        self.assertFalse(advice["available"])
        self.assertEqual(advice["status"], "disabled_by_policy")
        self.assertEqual(advice["stale_context_gate"], "not_applicable")
        self.assertEqual(advice["residual_risk"], [])


def _patch_event(message: str) -> dict:
    return {
        "runtime": "codex",
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {
            "patch": (
                "*** Begin Patch\n"
                "*** Update File: src/services/order_service.py\n"
                "@@\n"
                "+class OrderService:\n"
                "+    pass\n"
                "*** End Patch\n"
            )
        },
        "last_assistant_message": message,
    }


def _seed_repeat_failures(common, cwd: Path) -> None:
    task = common._memory_task_fingerprint(["src/services/order_service.py"], "", "")
    for event_id in ("failed-1", "failed-2"):
        common.write_memory_event(
            cwd,
            {
                "event_id": event_id,
                "task_fingerprint": task,
                "type": "validation_result",
                "paths": ["src/services/order_service.py"],
                "outcome": "failed",
            },
        )


def _seed_stage_specific_repeat_failures(common, cwd: Path) -> None:
    for event_id, stage in (("failed-1", "edit"), ("failed-2", "repair")):
        common.write_memory_event(
            cwd,
            {
                "event_id": event_id,
                "task_fingerprint": common._memory_task_fingerprint(
                    ["src/services/order_service.py"], "", stage
                ),
                "type": "validation_result",
                "paths": ["src/services/order_service.py"],
                "outcome": "failed",
            },
        )


def _complete_preflight() -> str:
    return (
        "```yaml\n"
        "changeforge_implementation_preflight:\n"
        "  read_evidence:\n"
        "    target_files:\n"
        "      - src/services/order_service.py\n"
        "  placement_decision:\n"
        "    target_file: src/services/order_service.py\n"
        "    reason: existing service module owns order orchestration\n"
        "  reuse_decision:\n"
        "    direct_reuse:\n"
        "      - symbol_or_path: src/services/base.py\n"
        "  object_boundary:\n"
        "    artifact_type: class\n"
        "    owner: src/services/order_service.py\n"
        "    state_or_invariant: service owns order orchestration boundary\n"
        "  test_plan:\n"
        "    validation_commands:\n"
        "      - pytest tests/test_order_service.py\n"
        "  risk:\n"
        "    rollback_or_revert_path: revert patch\n"
        "```\n"
    )


if __name__ == "__main__":
    unittest.main()
