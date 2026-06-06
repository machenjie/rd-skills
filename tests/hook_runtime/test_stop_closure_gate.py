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
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_stop_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_stop(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str | None = None,
    agent: str | None = None,
) -> subprocess.CompletedProcess[str]:
    event["cwd"] = str(cwd)
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    if mode is None:
        env.pop("CHANGEFORGE_HOOK_MODE", None)
    else:
        env["CHANGEFORGE_HOOK_MODE"] = mode
    if agent is None:
        env.pop("CHANGEFORGE_AGENT", None)
    else:
        env["CHANGEFORGE_AGENT"] = agent
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "changeforge_stop_closure_gate.py")],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def seed_state(cwd: Path, cache: Path, **fields: object) -> None:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        state: dict[str, object] = {"runtime": fields.pop("runtime", "claude")}
        state.update(fields)
        common.save_state(cwd, state)
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


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


class StopClosureGateTests(unittest.TestCase):
    def test_empty_state_is_silent(self) -> None:
        event = json.loads((FIXTURE_DIR / "codex_stop_with_changes.json").read_text())
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            result = run_stop(event, Path(cwd), Path(cache))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_changed_paths_emit_closure_reminder(self) -> None:
        event = json.loads((FIXTURE_DIR / "claude_stop_with_changes.json").read_text())
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                runtime="claude",
                changed_paths=["src/services/order_service.py"],
                structure_findings=["src/services/order_service.py: new file"],
            )
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Closure Gate reminder", result.stdout)
        self.assertIn("changed files", result.stdout)

    def test_file_naming_findings_request_naming_evidence(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, file_naming_findings=["a.go: name mismatch"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("file naming convention evidence", result.stdout)

    def test_reuse_findings_request_reuse_ladder(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, reuse_findings=["utils/x.py: reuse"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("reuse ladder record", result.stdout)

    def test_extension_reuse_findings_request_extension_safety(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, extension_reuse_findings=["x.go: extended"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("extension safety record", result.stdout)

    def test_advanced_refactor_findings_request_decision(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, advanced_refactor_findings=["x.ts: class"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("advanced refactor decision", result.stdout)

    def test_comment_findings_request_comment_quality(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, comment_findings=["x.go: uncommented exported function"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment quality evidence", result.stdout)

    def test_missing_closure_signals_listed(self) -> None:
        # The final response covers the base closure groups but omits naming,
        # reuse, and comment evidence, so only those conditional groups are flagged.
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "response": (
                "I used the ChangeForge skill path, changed files, ran tests to verify, "
                "noted residual risk, and listed next actions."
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                changed_paths=["a.py"],
                file_naming_findings=["a.py: mismatch"],
                reuse_findings=["a.py: reuse"],
                comment_findings=["a.py: uncommented"],
            )
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("missing closure signals", result.stdout)
        self.assertIn("naming", result.stdout)
        self.assertIn("reuse", result.stdout)
        self.assertIn("comments", result.stdout)

    def test_missing_comment_keyword_listed(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "response": "I used the skill path, changed files, verified with tests, risk noted, next steps.",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.go"], comment_findings=["a.go: uncommented"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("missing closure signals", result.stdout)
        self.assertIn("comments", result.stdout)

    def test_monitor_mode_clears_state_without_output(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, comment_findings=["a.go: uncommented"])
            result = run_stop(event, cwd, cache, mode="monitor")
            state = load_state(cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(state["comment_findings"], [])

    def test_block_mode_outputs_block_decision(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "codex",
            "stop_hook_active": False,
            "last_assistant_message": "done",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, runtime="codex", comment_findings=["a.go: uncommented"])
            result = run_stop(event, cwd, cache, mode="block", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")

    def test_state_cleared_after_stop(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"], comment_findings=["a.py: uncommented"])
            run_stop(event, cwd, cache)
            state = load_state(cwd, cache)
        self.assertEqual(state["changed_paths"], [])
        self.assertEqual(state["comment_findings"], [])


if __name__ == "__main__":
    unittest.main()
