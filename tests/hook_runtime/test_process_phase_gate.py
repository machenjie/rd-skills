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
GATE_SCRIPT = SCRIPT_DIR / "changeforge_process_phase_gate.py"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_process_phase_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_gate(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    agent: str = "codex",
    mode: str | None = "block",
) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = agent
    if mode is None:
        env.pop("CHANGEFORGE_PROCESS_PHASE_MODE", None)
    else:
        env["CHANGEFORGE_PROCESS_PHASE_MODE"] = mode
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        input=json.dumps(payload),
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


def edit_event() -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "src/runtime_governance/example.py",
            "new_string": "def changed():\n    return True\n",
        },
    }


def reviewed_ledger(*reviewed: str, validation: bool = True, unresolved_choices: int = 0) -> dict:
    digest = "sha256:" + ("a" * 64)
    statuses = {phase: ("reviewed" if phase in reviewed else "pending") for phase in ("pdd", "ddd", "sdd", "tdd")}
    return {
        "schema_version": 1,
        "route_id": "active-runtime-route",
        "current_phase": "implementation",
        "required_phases": ["pdd", "ddd", "sdd", "tdd"],
        "phase_status": statuses,
        "phase_scores": {phase: (5 if phase in reviewed else 0) for phase in ("pdd", "ddd", "sdd", "tdd")},
        "artifact_digests": {phase: digest for phase in reviewed},
        "review_ids": {phase: f"{phase}-review-1" for phase in reviewed},
        "blockers": [],
        "unresolved_blocking_choices": unresolved_choices,
        "validation_signal_present": validation,
        "updated_by_hook": "changeforge_process_phase_gate",
    }


def phase_review_result(phase: str, digest: str) -> dict:
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
        "approved_scope": {"files": ["src/runtime_governance/example.py"], "behaviors": [], "facts": []},
        "not_reviewed": [],
        "required_next_action": ["proceed"],
        "residual_risk": [],
    }


def assert_blocked(test_case: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> str:
    test_case.assertEqual(result.returncode, 0, result.stderr)
    payload = json.loads(result.stdout)
    test_case.assertEqual(payload.get("decision"), "block", result.stdout)
    reason = str(payload.get("reason", ""))
    test_case.assertIn("ChangeForge Process Phase Gate: BLOCKED", reason)
    return reason


class ProcessPhaseGateTests(unittest.TestCase):
    def test_edit_without_phase_ledger_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_blocked(self, run_gate(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("process_phase_ledger is missing", reason)

    def test_edit_with_pdd_only_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd")])
            reason = assert_blocked(self, run_gate(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("DDD is not independently reviewed", reason)

    def test_edit_with_pdd_and_ddd_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd", "ddd")])
            reason = assert_blocked(self, run_gate(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("SDD is not independently reviewed", reason)

    def test_edit_with_sdd_but_no_tdd_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd", "ddd", "sdd")])
            reason = assert_blocked(self, run_gate(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("TDD is not independently reviewed", reason)

    def test_edit_with_all_reviewed_allows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd", "ddd", "sdd", "tdd")])
            result = run_gate(edit_event(), Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["pdd_reviewed"])
            self.assertTrue(state["tdd_reviewed"])

    def test_sdd_unresolved_choice_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(
                Path(tmp),
                Path(cache),
                process_phase_ledgers=[reviewed_ledger("pdd", "ddd", "sdd", "tdd", unresolved_choices=1)],
            )
            reason = assert_blocked(self, run_gate(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("SDD reviewed requires unresolved_blocking_choices=0", reason)

    def test_tdd_missing_validation_signal_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(
                Path(tmp),
                Path(cache),
                process_phase_ledgers=[reviewed_ledger("pdd", "ddd", "sdd", "tdd", validation=False)],
            )
            reason = assert_blocked(self, run_gate(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("TDD reviewed requires validation_signal_present=true", reason)

    def test_copilot_records_degraded_rather_than_claiming_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(edit_event(), Path(tmp), Path(cache), agent="copilot")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["process_phase_blocked"])
            self.assertIn("copilot lacks PreToolUse hard blocking", state["process_phase_blocked_reason"])

    def test_passing_reviews_populate_missing_digests_and_allow_edit(self) -> None:
        digests = {phase: "sha256:" + str(index) * 64 for index, phase in enumerate(("pdd", "ddd", "sdd", "tdd"), start=1)}
        ledger = reviewed_ledger(validation=True)
        ledger["artifact_digests"] = {}
        ledger["review_ids"] = {}
        ledger["phase_status"] = {phase: "pending" for phase in ("pdd", "ddd", "sdd", "tdd")}
        ledger["phase_scores"] = {phase: 0 for phase in ("pdd", "ddd", "sdd", "tdd")}
        reviews = [phase_review_result(phase, digest) for phase, digest in digests.items()]
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[ledger], phase_review_results=reviews)
            result = run_gate(edit_event(), Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["pdd_reviewed"])
            self.assertTrue(state["ddd_reviewed"])
            self.assertTrue(state["sdd_reviewed"])
            self.assertTrue(state["tdd_reviewed"])
            latest = state["process_phase_ledgers"][0]
            self.assertEqual(latest["artifact_digests"], digests)

    def test_chinese_engineering_prompt_initializes_phase_ledger(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "请修复运行时状态机闭环问题，并补充验证测试覆盖。",
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["process_phase_ledger_seen"])
            self.assertEqual(state["process_phase_ledgers"][0]["current_phase"], "pdd")

    def test_chinese_non_engineering_question_does_not_initialize_phase_ledger(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "请说明一下产品需求文档的含义和适用场景？",
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(Path(tmp), Path(cache))
            self.assertFalse(state["process_phase_ledger_seen"])
            self.assertEqual(state["process_phase_ledgers"], [])


if __name__ == "__main__":
    unittest.main()
