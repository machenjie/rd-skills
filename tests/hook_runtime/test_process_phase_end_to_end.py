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
PROCESS_GATE = SCRIPT_DIR / "changeforge_process_phase_gate.py"
SUBAGENT_GATE = SCRIPT_DIR / "changeforge_subagent_review_gate.py"
STOP_GATE = SCRIPT_DIR / "changeforge_stop_closure_gate.py"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_process_phase_e2e_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_script(script: Path, event: dict, cwd: Path, cache: Path, *, agent: str = "codex") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = agent
    env["CHANGEFORGE_PROCESS_PHASE_MODE"] = "block"
    env["CHANGEFORGE_SUBAGENT_REVIEW_MODE"] = "block"
    env["CHANGEFORGE_STOP_MODE"] = "block"
    return subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps({**event, "cwd": str(cwd)}),
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
        state: dict[str, object] = {"runtime": fields.pop("runtime", "codex")}
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


def digest(phase: str) -> str:
    marker = {"pdd": "a", "ddd": "b", "sdd": "c", "tdd": "d"}.get(phase, "e")
    return "sha256:" + marker * 64


def review_result(phase: str, *, artifact_digest: str | None = None, verdict: str = "pass", score: int = 5) -> dict:
    return {
        "schema_version": 1,
        "review_id": f"{phase}-review-1",
        "phase": phase,
        "reviewer_skill": "ai-code-review-refactor",
        "owner_skill": "development-process-orchestrator",
        "reviewed_artifact_digest": artifact_digest or digest(phase),
        "verdict": verdict,
        "score": score,
        "findings": [],
        "approved_scope": {"files": ["src/runtime_governance/process_phase.py"], "behaviors": [], "facts": []},
        "not_reviewed": [],
        "required_next_action": ["proceed"],
        "residual_risk": [],
    }


def edit_event() -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "src/runtime_governance/process_phase.py",
            "new_string": "def changed():\n    return True\n",
        },
    }


def phase_state(**overrides: object) -> dict:
    state: dict[str, object] = {
        "changed_paths": ["src/runtime_governance/process_phase.py"],
        "process_phase_ledger_seen": True,
        "pdd_reviewed": True,
        "ddd_reviewed": True,
        "sdd_reviewed": True,
        "tdd_reviewed": True,
        "validation_freshness_seen": True,
    }
    state.update(overrides)
    return state


COMPLETE_RESPONSE = (
    "I used the ChangeForge skill path. Changed files are listed. "
    "Validation: ran python3 -m unittest tests/hook_runtime/test_process_phase_end_to_end.py, passed, exit 0. "
    "Residual risk is none. Repository context: owning surface and caller/callee flow inspected. "
    "Workflow state: current stage testing, allowed transition review, owner/reviewer split recorded. "
    "Plan-execution consistency: accepted plan vs actual changed files and validation commands reconciled. "
    "Skill efficacy benchmark: hook runtime behavior covered by focused fixture. "
    "Validation freshness: latest edit covered by the hook validator. Next steps: none.\n\n"
    "```yaml\nrepository_context:\n  source_of_truth:\n    - src/hook-runtime/scripts/changeforge_stop_closure_gate.py\n"
    "  reuse_candidates:\n    - ClosureContract\n  validation_candidates:\n    - python3 -m unittest tests/hook_runtime/test_process_phase_end_to_end.py\n"
    "  graph_freshness: current\n  residual_risk:\n    - none\n```\n"
    "```yaml\nchangeforge_implementation_preflight:\n  read_evidence:\n    target_files:\n      - src/hook-runtime/scripts/changeforge_stop_closure_gate.py\n"
    "  placement_decision:\n    target_file: src/hook-runtime/scripts/changeforge_stop_closure_gate.py\n    reason: existing owner\n"
    "  reuse_decision:\n    direct_reuse:\n      - ClosureContract\n  test_plan:\n    validation_commands:\n      - python3 -m unittest tests/hook_runtime/test_process_phase_end_to_end.py\n"
    "  risk:\n    rollback_or_revert_path: revert patch\n```\n"
    "```yaml\nsenior_programming_judgment:\n  skip_reason: trivial-local-edit\n```\n"
    "```yaml\nchangeforge_stage_route:\n  current_stage: testing\n  selected_capabilities: []\n  next_stage: handoff\n```\n"
    "```yaml\nchangeforge_route:\n  selected_skills:\n    - development-process-orchestrator\n"
    "  selected_capabilities:\n    - agent-workflow-state-machine\n  required_references:\n    - references/routing-rules.md\n"
    "  required_quality_gates:\n    - quality-test-gate\n```\n"
)


class ProcessPhaseEndToEndTests(unittest.TestCase):
    def test_full_phase_lifecycle_allows_edit_and_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd, cache_path = Path(tmp), Path(cache)
            prompt = {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "Please fix the runtime phase FSM closure behavior and add tests.",
            }
            self.assertEqual(run_script(PROCESS_GATE, prompt, cwd, cache_path).returncode, 0)
            for phase in ("pdd", "ddd", "sdd", "tdd"):
                start = {
                    "hook_event_name": "SubagentStart",
                    "review_type": phase,
                    "capsule_id": f"{phase}-capsule-1",
                    "artifact_digest": digest(phase),
                }
                self.assertEqual(run_script(SUBAGENT_GATE, start, cwd, cache_path).returncode, 0)
                stop = {
                    "hook_event_name": "SubagentStop",
                    "capsule_id": f"{phase}-capsule-1",
                    "phase_review_result": review_result(phase),
                }
                self.assertEqual(run_script(SUBAGENT_GATE, stop, cwd, cache_path).returncode, 0)
            state = load_state(cwd, cache_path)
            state["process_phase_ledgers"][0]["validation_signal_present"] = True
            seed_state(cwd, cache_path, **state)
            edit = run_script(PROCESS_GATE, edit_event(), cwd, cache_path)
            self.assertEqual(edit.returncode, 0, edit.stderr)
            self.assertEqual(edit.stdout.strip(), "")
            state = load_state(cwd, cache_path)
            self.assertTrue(state["pdd_reviewed"])
            self.assertTrue(state["ddd_reviewed"])
            self.assertTrue(state["sdd_reviewed"])
            self.assertTrue(state["tdd_reviewed"])
            latest = state["process_phase_ledgers"][0]
            self.assertEqual(set(latest["artifact_digests"]), {"pdd", "ddd", "sdd", "tdd"})
            stop = run_script(STOP_GATE, {"hook_event_name": "Stop", "response": COMPLETE_RESPONSE}, cwd, cache_path)
            self.assertEqual(stop.returncode, 0, stop.stderr)
            if stop.stdout.strip():
                payload = json.loads(stop.stdout)
                self.assertNotEqual(payload.get("decision"), "block")


    def test_stop_accepts_bounded_phase_handoff_manifest(self) -> None:
        response = (
            "```yaml\n"
            "process_phase_ledger:\n"
            "  pdd: reviewed\n"
            "  ddd: reviewed\n"
            "  sdd: reviewed\n"
            "  tdd: reviewed\n"
            "  validation_signal_present: true\n"
            "phase_reviews:\n"
            "  count: 4\n"
            "  verdict: pass\n"
            "phase_repair:\n"
            "  repair_event: final handoff phase repair evidence\n"
            "  rereview: pass\n"
            "validation:\n"
            "  - cmd: python3 -m unittest discover -s tests/hook_runtime\n"
            "    outcome: exit 0\n"
            "```\n"
        )
        state = phase_state(
            process_phase_ledgers=[],
            process_phase_ledger_seen=False,
            phase_review_findings=[
                {
                    "finding_id": "process-phase-1",
                    "phase": "sdd",
                    "severity": "high",
                    "evidence": "missing phase handoff",
                    "required_fix": "repair",
                    "blocks_next_stage": True,
                }
            ],
        )
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd, cache_path = Path(tmp), Path(cache)
            seed_state(cwd, cache_path, **state)
            result = run_script(PROCESS_GATE, {"hook_event_name": "Stop", "response": response}, cwd, cache_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_pdd_pass_but_ddd_missing_blocks_pretool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            ledger = {
                "route_id": "active-runtime-route",
                "current_phase": "implementation",
                "phase_status": {"pdd": "reviewed", "ddd": "pending", "sdd": "pending", "tdd": "pending"},
                "artifact_digests": {"pdd": digest("pdd")},
                "review_ids": {"pdd": "pdd-review-1"},
                "validation_signal_present": True,
            }
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[ledger])
            result = run_script(PROCESS_GATE, edit_event(), Path(tmp), Path(cache))
            self.assertEqual(json.loads(result.stdout)["decision"], "block")
            self.assertIn("DDD is not independently reviewed", result.stdout)

    def test_sdd_digest_mismatch_blocks_pretool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            ledger = {
                "route_id": "active-runtime-route",
                "current_phase": "implementation",
                "phase_status": {"pdd": "reviewed", "ddd": "reviewed", "sdd": "review_pending", "tdd": "pending"},
                "artifact_digests": {"pdd": digest("pdd"), "ddd": digest("ddd"), "sdd": digest("sdd")},
                "review_ids": {"pdd": "pdd-review-1", "ddd": "ddd-review-1"},
                "validation_signal_present": True,
            }
            seed_state(
                Path(tmp),
                Path(cache),
                process_phase_ledgers=[ledger],
                phase_review_results=[review_result("sdd", artifact_digest=digest("tdd"))],
            )
            result = run_script(PROCESS_GATE, edit_event(), Path(tmp), Path(cache))
            self.assertEqual(json.loads(result.stdout)["decision"], "block")
            self.assertIn("SDD is not independently reviewed", result.stdout)

    def test_review_finding_without_repair_blocks_stop(self) -> None:
        self._assert_stop_blocks_with_state(
            phase_state(
                phase_review_findings=[
                    {
                        "finding_id": "sdd-001",
                        "phase": "sdd",
                        "severity": "high",
                        "evidence": "missing choice",
                        "required_fix": "repair",
                        "blocks_next_stage": True,
                    }
                ]
            ),
            "phase_repair",
        )

    def test_repair_without_rereview_blocks_stop(self) -> None:
        self._assert_stop_blocks_with_state(
            phase_state(
                phase_review_findings=[
                    {
                        "finding_id": "sdd-001",
                        "phase": "sdd",
                        "severity": "high",
                        "evidence": "missing choice",
                        "required_fix": "repair",
                        "blocks_next_stage": True,
                    }
                ],
                phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
            ),
            "phase_rereview",
        )

    def test_rereview_pass_but_validation_freshness_false_blocks_stop(self) -> None:
        self._assert_stop_blocks_with_state(
            phase_state(
                validation_freshness_seen=False,
                phase_review_findings=[
                    {
                        "finding_id": "sdd-001",
                        "phase": "sdd",
                        "severity": "high",
                        "evidence": "missing choice",
                        "required_fix": "repair",
                        "blocks_next_stage": True,
                    }
                ],
                phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
                phase_rereview_events=[{"finding_id": "sdd-001", "verdict": "pass"}],
            ),
            "validation_fresh_after_final_edit",
        )

    def _assert_stop_blocks_with_state(self, state: dict, expected: str) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), **state)
            result = run_script(STOP_GATE, {"hook_event_name": "Stop", "response": COMPLETE_RESPONSE}, Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("decision"), "block")
            self.assertIn(expected, payload["reason"])


if __name__ == "__main__":
    unittest.main()
