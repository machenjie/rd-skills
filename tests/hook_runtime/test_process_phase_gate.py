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
    mode: str | None = None,
) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = agent
    if mode is None:
        env.pop("CHANGEFORGE_PROCESS_PHASE_MODE", None)
        env.pop("CHANGEFORGE_PROCESS_PHASE_STOP_MODE", None)
    else:
        env["CHANGEFORGE_PROCESS_PHASE_MODE"] = mode
        env["CHANGEFORGE_PROCESS_PHASE_STOP_MODE"] = mode
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def run_gate_strict(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    agent: str = "codex",
) -> subprocess.CompletedProcess[str]:
    return run_gate(event, cwd, cache, agent=agent, mode="block")


def seed_state(cwd: Path, cache: Path, *, runtime: str = "codex", **fields: object) -> None:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        state: dict[str, object] = {"runtime": runtime}
        if "process_phase_ledgers" in fields and "phase_review_results" not in fields:
            fields["phase_review_results"] = phase_reviews_for_ledgers(fields.get("process_phase_ledgers"))
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
        "review_source": "subagent_review_gate",
        "capsule_id": f"{phase}-capsule-1",
        "expected_artifact_digest": digest,
        "review_context_strength": "strong",
        "reviewer_boundary": "subagent",
    }


def phase_reviews_for_ledgers(ledgers: object) -> list[dict]:
    reviews: list[dict] = []
    if not isinstance(ledgers, list):
        return reviews
    for ledger in ledgers:
        if not isinstance(ledger, dict):
            continue
        artifact_digests = ledger.get("artifact_digests") if isinstance(ledger.get("artifact_digests"), dict) else {}
        phase_status = ledger.get("phase_status") if isinstance(ledger.get("phase_status"), dict) else {}
        for phase, digest in artifact_digests.items():
            if phase_status.get(phase) == "reviewed" and isinstance(digest, str):
                reviews.append(phase_review_result(str(phase), digest))
    return reviews


def assert_strict_blocked(test_case: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> str:
    test_case.assertEqual(result.returncode, 0, result.stderr)
    payload = json.loads(result.stdout)
    hook_output = payload.get("hookSpecificOutput", {})
    test_case.assertEqual(hook_output.get("hookEventName"), "PreToolUse", result.stdout)
    test_case.assertEqual(hook_output.get("permissionDecision"), "deny", result.stdout)
    reason = str(hook_output.get("permissionDecisionReason", ""))
    test_case.assertIn("Engineering expert note:", reason)
    test_case.assertNotIn("ChangeForge Process Phase Gate", reason)
    test_case.assertNotIn("BLOCKED", reason)
    test_case.assertNotIn("required_action", reason)
    test_case.assertNotIn("phase_review_result", reason)
    return reason


class ProcessPhaseGateTests(unittest.TestCase):
    def test_default_daily_pretool_records_evidence_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            result = run_gate(edit_event(), cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            state = load_state(cwd, Path(cache))
        self.assertTrue(state["process_phase_blocked"])
        self.assertIn("process_phase_ledger is missing", state["process_phase_blocked_reason"])

    def test_edit_without_phase_ledger_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("process planning evidence is missing", reason)

    def test_python_heredoc_write_without_phase_ledger_blocks(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "python3 - <<'PY'\nfrom pathlib import Path\nPath('x.go').write_text('package x')\nPY"
            },
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
            self.assertIn("process planning evidence is missing", reason)

    def test_perl_and_sed_in_place_without_phase_ledger_block(self) -> None:
        commands = ["perl -pi -e 's/a/b/' x.go", "sed -i '' 's/a/b/' x.go"]
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            for command in commands:
                with self.subTest(command=command):
                    event = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}
                    reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
                    self.assertIn("process planning evidence is missing", reason)

    def test_read_only_python_validation_commands_without_phase_ledger_do_not_block(self) -> None:
        commands = [
            "python3 -m unittest tests.hook_runtime.test_process_phase_gate",
            "python3 -m py_compile x.py",
            "python3 scripts/audit-skill-content.py",
        ]
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            for command in commands:
                with self.subTest(command=command):
                    event = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}
                    result = run_gate(event, Path(tmp), Path(cache))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), "")

    def test_hook_state_write_in_normal_task_is_flagged_as_internal_state_access(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python3 - <<'PY'\\nfrom pathlib import Path\\nPath('/tmp/changeforge/hooks/current-turn.json').write_text('{}')\\nPY"},
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
            self.assertIn("rd_skills_internal_state_access", reason)

    def test_hook_state_maintenance_mode_records_report_without_blocking(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python3 - <<'PY'\\nfrom pathlib import Path\\nPath('/tmp/changeforge/hooks/current-turn.json').write_text('{}')\\nPY"},
        }
        previous = os.environ.get("CHANGEFORGE_MAINTENANCE_MODE")
        os.environ["CHANGEFORGE_MAINTENANCE_MODE"] = "1"
        try:
            with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
                result = run_gate(event, Path(tmp), Path(cache))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "")
                state = load_state(Path(tmp), Path(cache))
                self.assertFalse(state["process_phase_blocked"])
                self.assertIn("hook_state_maintenance_report", state["process_phase_blocked_reason"])
        finally:
            if previous is None:
                os.environ.pop("CHANGEFORGE_MAINTENANCE_MODE", None)
            else:
                os.environ["CHANGEFORGE_MAINTENANCE_MODE"] = previous

    def test_edit_with_pdd_only_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd")])
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("DDD is not independently checked", reason)

    def test_edit_with_pdd_and_ddd_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd", "ddd")])
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("SDD is not independently checked", reason)

    def test_pretool_missing_sdd_review_outputs_expert_note_without_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd", "ddd")])
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
        self.assertIn("SDD is not independently checked", reason)
        self.assertIn("Natural next step:", reason)
        self.assertNotIn("review_" "required" "_action:", reason)
        self.assertNotIn("expected_event_chain:", reason)
        self.assertNotIn("SubagentStart", reason)
        self.assertNotIn("SubagentStop", reason)
        self.assertNotIn("phase_" "review_result", reason)
    def test_pretool_missing_pdd_review_does_not_suggest_final_handoff_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
        self.assertIn("Natural next step:", reason)
        self.assertNotIn("Do not add phase_reviews in final handoff", reason)
        self.assertNotIn("final handoff phase_reviews are enough", reason.casefold())
        self.assertNotIn("final handoff phase_reviews are enough", reason.casefold())

    def test_edit_with_sdd_but_no_tdd_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[reviewed_ledger("pdd", "ddd", "sdd")])
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("TDD is not independently checked", reason)

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
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
            self.assertIn("SDD reviewed requires unresolved design choices=0", reason)

    def test_tdd_review_does_not_require_validation_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(
                Path(tmp),
                Path(cache),
                process_phase_ledgers=[reviewed_ledger("pdd", "ddd", "sdd", "tdd", validation=False)],
            )
            result = run_gate(edit_event(), Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["tdd_reviewed"])

    def test_copilot_pretool_blocks_with_permission_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate_strict(edit_event(), Path(tmp), Path(cache), agent="copilot")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("permissionDecision"), "deny")
            self.assertIn("Engineering expert note:", payload.get("permissionDecisionReason", ""))
            self.assertNotIn("ChangeForge Process Phase Gate", payload.get("permissionDecisionReason", ""))
            state = load_state(Path(tmp), Path(cache))
            self.assertTrue(state["process_phase_blocked"])
            self.assertNotIn("lacks PreToolUse", state["process_phase_blocked_reason"])

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


    def test_missing_process_phase_ledger_outputs_expert_note_without_artifact_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
        self.assertIn("process planning evidence is missing", reason)
        self.assertIn("Natural next step:", reason)
        self.assertNotIn("phase_artifact_" "required" "_action:", reason)
        self.assertNotIn("next_action: create_process_phase_artifact", reason)
        self.assertNotIn("artifact_" "digest", reason)

    def test_missing_artifact_digest_outputs_expert_note_without_protocol_actions(self) -> None:
        ledger = reviewed_ledger("pdd", "ddd")
        ledger["artifact_digests"].pop("sdd", None)
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[ledger])
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
        self.assertIn("SDD is not independently checked", reason)
        self.assertNotIn("phase_artifact_" "required" "_action:", reason)
        self.assertNotIn("review_" "required" "_action:", reason)
        self.assertNotIn("phase: sdd", reason)

    def test_review_gap_with_artifact_digest_does_not_emit_internal_protocol(self) -> None:
        ledger = reviewed_ledger("pdd", "ddd")
        ledger["artifact_digests"]["sdd"] = "sha256:" + ("c" * 64)
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(Path(tmp), Path(cache), process_phase_ledgers=[ledger])
            reason = assert_strict_blocked(self, run_gate_strict(edit_event(), Path(tmp), Path(cache)))
        self.assertNotIn("phase_artifact_" "required" "_action:", reason)
        self.assertNotIn("review_" "required" "_action:", reason)
        self.assertNotIn("artifact_" "digest: sha256:" + ("c" * 64), reason)
        self.assertIn("SDD is not independently checked", reason)

    def test_business_prompt_internal_state_token_records_risk(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Please describe current-turn.json for meeting notes.",
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache), mode="monitor")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            state = load_state(Path(tmp), Path(cache))
            self.assertIn("rd_skills_internal_state_access", state["risk_surfaces"])
            self.assertIn(
                "rd_skills_internal_state_access",
                state["closure_risk_surfaces"],
            )
            self.assertFalse(state["process_phase_ledger_seen"])

    def test_stop_outputs_quality_report_without_internal_protocol(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "response": "Done.",
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            seed_state(
                Path(tmp),
                Path(cache),
                changed_paths=["src/app.py"],
                process_phase_ledgers=[reviewed_ledger("pdd")],
            )
            result = run_gate(event, Path(tmp), Path(cache), mode="warn")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            message = payload.get("systemMessage", "")
        self.assertIn("engineering_quality_report:", message)
        self.assertIn("status: degraded_ready", message)
        self.assertNotIn("phase_" "review_result", message)
        self.assertNotIn("implementation_" "review_result", message)
        self.assertNotIn("review_" "required" "_action", message)


if __name__ == "__main__":
    unittest.main()
