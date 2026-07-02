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
GATE_SCRIPT = SCRIPT_DIR / "changeforge_subagent_review_gate.py"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_subagent_review_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_gate(event: dict, cwd: Path, cache: Path, *, agent: str = "codex") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = agent
    env["CHANGEFORGE_SUBAGENT_REVIEW_MODE"] = "block"
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        input=json.dumps({**event, "cwd": str(cwd)}),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def seed_state(cwd: Path, cache: Path, *, runtime: str = "codex", **fields: object) -> None:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        state: dict[str, object] = {"runtime": runtime}
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


def review_result(verdict: str = "pass", score: int = 5) -> dict:
    return {
        "schema_version": 1,
        "review_id": "sdd-review-1",
        "phase": "sdd",
        "reviewer_skill": "ai-code-review-refactor",
        "owner_skill": "development-process-orchestrator",
        "reviewed_artifact_digest": "sha256:" + ("b" * 64),
        "verdict": verdict,
        "score": score,
        "findings": []
        if verdict == "pass"
        else [
            {
                "finding_id": "sdd-001",
                "severity": "high",
                "evidence": "material choice not resolved",
                "required_fix": "add design decision resolution evidence",
                "blocks_next_stage": True,
            }
        ],
        "approved_scope": {"files": ["src/runtime_governance/process_phase.py"], "behaviors": [], "facts": []},
        "not_reviewed": [],
        "required_next_action": ["proceed"] if verdict == "pass" else ["repair"],
        "residual_risk": [],
    }


class SubagentReviewCapsuleTests(unittest.TestCase):
    def test_valid_subagent_review_result_updates_phase_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(
                {"hook_event_name": "SubagentStop", "phase_review_result": review_result()},
                Path(tmp),
                Path(cache),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["phase_review_seen"])
            self.assertTrue(state["sdd_reviewed"])
            self.assertEqual(state["phase_review_results"][0]["verdict"], "pass")

    def test_fail_review_blocks_next_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(
                {"hook_event_name": "SubagentStop", "phase_review_result": review_result("fail", 2)},
                Path(tmp),
                Path(cache),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["process_phase_blocked"])
            self.assertTrue(state["phase_repair_required"])
            self.assertEqual(state["phase_review_findings"][0]["finding_id"], "sdd-001")

    def test_needs_user_choice_blocks_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(
                {"hook_event_name": "SubagentStop", "phase_review_result": review_result("needs_user_choice", 3)},
                Path(tmp),
                Path(cache),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["process_phase_blocked"])
            self.assertIn("review verdict needs_user_choice", state["process_phase_blocked_reason"])

    def test_raw_prompt_secret_in_capsule_is_not_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), read_paths=["src/runtime_governance/process_phase.py"])
            result = run_gate(
                {
                    "hook_event_name": "SubagentStart",
                    "review_type": "sdd",
                    "raw_prompt": "must not persist",
                    "secret_token": "must not persist",
                },
                Path(tmp),
                Path(cache),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            capsule = load_state(Path(tmp), Path(cache))["review_capsules"][0]
            rendered = json.dumps(capsule)
            self.assertNotIn("raw_prompt", rendered)
            self.assertNotIn("secret_token", rendered)

    def test_copilot_unsupported_subagent_stop_records_degraded_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(
                {"hook_event_name": "SubagentStop", "phase_review_result": review_result()},
                Path(tmp),
                Path(cache),
                agent="copilot",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["process_phase_blocked"])
            self.assertIn("copilot lacks SubagentStop support", state["process_phase_blocked_reason"])


if __name__ == "__main__":
    unittest.main()
