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


def load_stop_gate():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "changeforge_stop_closure_gate_for_test",
            SCRIPT_DIR / "changeforge_stop_closure_gate.py",
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


def read_telemetry(cache: Path) -> list[dict]:
    import glob

    records: list[dict] = []
    pattern = str(cache / "changeforge" / "telemetry" / "*" / "sessions" / "*.jsonl")
    for file_path in glob.glob(pattern):
        for line in Path(file_path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


PREFLIGHT_MANIFEST = (
    "```yaml\n"
    "changeforge_implementation_preflight:\n"
    "  read_evidence:\n"
    "    target_files:\n"
    "      - a.go\n"
    "    sibling_files:\n"
    "      - b.go\n"
    "  placement_decision:\n"
    "    target_file: a.go\n"
    "    reason: existing package owns the changed behavior\n"
    "  reuse_decision:\n"
    "    direct_reuse:\n"
    "      - symbol_or_path: b.go\n"
    "  object_boundary:\n"
    "    artifact_type: module\n"
    "    owner: a.go\n"
    "    state_or_invariant: module owns the changed behavior boundary\n"
    "  test_plan:\n"
    "    validation_commands:\n"
    "      - go test ./...\n"
    "  risk:\n"
    "    rollback_or_revert_path: revert patch\n"
    "```\n"
)

REPOSITORY_CONTEXT_MANIFEST = (
    "```yaml\n"
    "repository_context:\n"
    "  source_of_truth:\n"
    "    - src/hook-runtime/scripts/changeforge_stop_closure_gate.py\n"
    "  reuse_candidates:\n"
    "    - runtime_governance.closure.ClosureContract\n"
    "  validation_candidates:\n"
    "    - python3 -m unittest tests/hook_runtime/test_stop_closure_gate.py\n"
    "  graph_freshness: current\n"
    "  residual_risk:\n"
    "    - none\n"
    "```\n"
)


class StopClosureGateTests(unittest.TestCase):
    def test_empty_state_is_silent(self) -> None:
        event = json.loads((FIXTURE_DIR / "codex_stop_with_changes.json").read_text())
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            result = run_stop(event, Path(cwd), Path(cache))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_stop_gate_ignores_professional_injection_for_question_stage(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "Here is the answer."}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                turn_stage="question",
                professional_injections=["UserPromptSubmit:question"],
            )
            result = run_stop(event, cwd, cache)
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
        payload = json.loads(result.stdout)
        self.assertIn("ChangeForge Closure Gate reminder", payload["systemMessage"])
        self.assertIn("changed files", payload["systemMessage"])

    def test_changed_paths_without_implementation_preflight_warns(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "Changed files. Risk noted."}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.go"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("implementation preflight evidence is incomplete", result.stdout)
        self.assertIn("implementation_preflight", result.stdout)

    def test_edit_without_preflight_seen_requests_preflight_evidence(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "Changed files. Risk noted."}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, edit_without_preflight_seen=True, changed_paths=["a.go"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("changeforge_implementation_preflight", result.stdout)

    def test_read_review_profile_no_changed_paths_does_not_require_preflight(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "response": "Reviewed a.go. Finding: none. Risk: none.",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, turn_stage="review", review_targets=["a.go"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("implementation_preflight", result.stdout)

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

    def test_structure_quality_findings_request_clarity_evidence(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, structure_quality_findings=["x.ts: boolean parameter"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("code clarity evidence", result.stdout)

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
                structure_quality_findings=["a.py: weak signature"],
            )
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("missing closure signals", result.stdout)
        self.assertIn("naming", result.stdout)
        self.assertIn("reuse", result.stdout)
        self.assertIn("comments", result.stdout)
        self.assertIn("clarity", result.stdout)

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

    def test_claude_block_mode_outputs_block_decision(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "stop_hook_active": False,
            "last_assistant_message": "done",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, runtime="claude", comment_findings=["a.py: uncommented"])
            result = run_stop(event, cwd, cache, mode="block", agent="claude")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("comment", payload["reason"])

    def test_state_cleared_after_stop(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"], comment_findings=["a.py: uncommented"])
            run_stop(event, cwd, cache)
            state = load_state(cwd, cache)
        self.assertEqual(state["changed_paths"], [])
        self.assertEqual(state["comment_findings"], [])

    def test_block_mode_does_not_block_when_evidence_complete(self) -> None:
        # Response covers all five base closure groups; state has no conditional
        # findings.  Block mode must emit a non-blocking reminder, not "block".
        event = {
            "hook_event_name": "Stop",
            "runtime": "codex",
            "stop_hook_active": False,
            "last_assistant_message": (
                "I used the ChangeForge skill path. Changed files are listed. "
                "Validation: ran python3 scripts/validate-hooks.py, passed, exit 0. Residual risk is none. "
                "Repository context: owning surface and caller/callee flow inspected. "
                "Workflow state: current stage testing, allowed transition handoff, owner/reviewer split recorded. "
                "Plan-execution consistency: accepted plan vs actual changed files and validation commands reconciled. "
                "Skill efficacy benchmark: hook runtime behavior only; existing hook validator covers the changed closure behavior. "
                "Validation freshness: latest edit covered by the hook validator. Next steps: deploy.\n\n"
                f"{REPOSITORY_CONTEXT_MANIFEST}\n"
                f"{PREFLIGHT_MANIFEST}\n"
                "```yaml\n"
                "changeforge_route:\n"
                "  selected_skills:\n"
                "    - backend-change-builder\n"
                "  selected_capabilities:\n"
                "    - implementation-structure-design\n"
                "  required_references:\n"
                "    - references/routing-rules.md\n"
                "  required_quality_gates:\n"
                "    - implementation gate\n"
                "```\n"
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                runtime="codex",
                changed_paths=["src/hook-runtime/scripts/changeforge_common.py"],
            )
            result = run_stop(event, cwd, cache, mode="block", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertNotEqual(payload.get("decision"), "block")
        self.assertIn("systemMessage", payload)

    def test_complete_preflight_validation_and_route_does_not_block(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "codex",
            "stop_hook_active": False,
            "last_assistant_message": (
                "I used the ChangeForge skill path. Changed files are listed. "
                "Validation: ran python3 scripts/validate-hooks.py, exit 0. Residual risk is none. "
                "Repository context: owning surface and caller/callee flow inspected. "
                "Workflow state: current stage testing, allowed transition review, owner/reviewer split recorded. "
                "Plan-execution consistency: accepted plan vs actual changed files and validation commands reconciled. "
                "Skill efficacy benchmark: hook runtime behavior only; existing hook validator covers the changed closure behavior. "
                "Validation freshness: latest edit covered by the hook validator. Next steps: review.\n\n"
                f"{REPOSITORY_CONTEXT_MANIFEST}\n"
                f"{PREFLIGHT_MANIFEST}\n"
                "```yaml\n"
                "changeforge_route:\n"
                "  selected_skills:\n"
                "    - backend-change-builder\n"
                "  selected_capabilities:\n"
                "    - implementation-structure-design\n"
                "  required_references:\n"
                "    - references/routing-rules.md\n"
                "  required_quality_gates:\n"
                "    - quality-test-gate\n"
                "```\n"
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                runtime="codex",
                changed_paths=["src/hook-runtime/scripts/changeforge_common.py"],
                implementation_preflight_required=True,
                implementation_preflight_seen=True,
                implementation_preflight_complete=True,
            )
            result = run_stop(event, cwd, cache, mode="block", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertNotEqual(payload.get("decision"), "block")

    def test_repository_context_keywords_only_do_not_satisfy_closure(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "codex",
            "stop_hook_active": False,
            "last_assistant_message": (
                "I used the ChangeForge skill path. Changed files are listed. "
                "Validation: ran python3 scripts/validate-hooks.py, exit 0. Residual risk is none. "
                "Repository context was not checked; owning surface and caller/callee are still unknown. "
                "Workflow state: current stage testing, allowed transition review, owner/reviewer split recorded. "
                "Plan-execution consistency: accepted plan vs actual changed files and validation commands reconciled. "
                "Skill efficacy benchmark: hook runtime behavior only; existing hook validator covers the changed closure behavior. "
                "Validation freshness: latest edit covered by the hook validator. Next steps: review.\n\n"
                f"{PREFLIGHT_MANIFEST}\n"
                "```yaml\n"
                "changeforge_route:\n"
                "  selected_skills:\n"
                "    - backend-change-builder\n"
                "  selected_capabilities:\n"
                "    - implementation-structure-design\n"
                "  required_references:\n"
                "    - references/routing-rules.md\n"
                "  required_quality_gates:\n"
                "    - quality-test-gate\n"
                "```\n"
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                runtime="codex",
                changed_paths=["src/hook-runtime/scripts/changeforge_common.py"],
                implementation_preflight_required=True,
                implementation_preflight_seen=True,
                implementation_preflight_complete=True,
            )
            result = run_stop(event, cwd, cache, mode="block", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("repository_context", payload["reason"])

    def test_block_mode_blocks_when_route_manifest_missing_despite_keywords(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "codex",
            "stop_hook_active": False,
            "last_assistant_message": (
                "I used the ChangeForge skill path. Changed files are listed. "
                "Validation: ran pytest -q, 12 passed, exit 0. Residual risk is none. "
                "Next steps: deploy. The string changeforge_route appears in prose."
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, runtime="codex", changed_paths=["a.go"])
            result = run_stop(event, cwd, cache, mode="block", agent="codex")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("route_manifest", payload["reason"])

    def test_block_mode_preserves_state_when_blocking(self) -> None:
        # When block mode fires (evidence missing), state must NOT be cleared so
        # the agent can satisfy requirements on the next stop event.
        event = {
            "hook_event_name": "Stop",
            "runtime": "codex",
            "stop_hook_active": False,
            "last_assistant_message": "done",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, runtime="codex", comment_findings=["a.go: uncommented"])
            run_stop(event, cwd, cache, mode="block", agent="codex")
            state = load_state(cwd, cache)
        self.assertNotEqual(state["comment_findings"], [])

    def test_route_and_stage_manifest_recorded_in_telemetry(self) -> None:
        manifest_text = (
            "Routing done.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "  selected_capabilities:\n"
            "    - implementation-structure-design\n"
            "    - authentication-authorization\n"
            "  required_references:\n"
            "    - references/routing-rules.md\n"
            "  required_quality_gates:\n"
            "    - security gate\n"
            "  skipped_quality_gates:\n"
            "    - gate: delivery gate\n"
            "      reason: no deploy\n"
            "```\n\n"
            "```yaml\n"
            "changeforge_stage_route:\n"
            "  current_stage: coding\n"
            "  selected_capabilities: []\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": manifest_text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["src/services/order_service.py"])
            run_stop(event, cwd, cache, mode="monitor")
            records = read_telemetry(cache)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertTrue(record["route_manifest_detected"])
        self.assertTrue(record["stage_manifest_detected"])
        self.assertEqual(record["manifest_current_stage"], "coding")
        self.assertIn(
            "implementation-structure-design", record["manifest_selected_capabilities"]
        )
        self.assertIn(
            "authentication-authorization", record["manifest_selected_capabilities"]
        )
        self.assertEqual(record["manifest_skipped_quality_gates"], ["delivery gate"])

    def test_closure_reminder_requests_route_and_stage_manifest(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("changeforge_route", result.stdout)
        self.assertIn("changeforge_stage_route", result.stdout)
        self.assertIn("required references", result.stdout)

    def test_closure_reminder_flags_missing_route_manifest(self) -> None:
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": "done"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("MISSING", result.stdout)
        self.assertIn("no complete changeforge_route manifest", result.stdout)

    def test_stop_review_requires_reviewed_files_and_findings(self) -> None:
        response = (
            "Review handoff. Changed files are unchanged. "
            "Validation: ran pytest -q, 1 passed, exit 0. Residual risk: none. "
            "Next steps: no deploy.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - ai-code-review-refactor\n"
            "  selected_capabilities:\n"
            "    - implementation-structure-design\n"
            "  required_references:\n"
            "    - references/routing-rules.md\n"
            "  required_quality_gates:\n"
            "    - quality-test-gate\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": response}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, turn_stage="review", review_intent_seen=True)
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("review_artifact", result.stdout)
        self.assertIn("review_findings", result.stdout)

    def test_stop_read_no_change_profile_is_silent_when_evidence_complete(self) -> None:
        # Regression: read-only turns should not require edit-style route or changed-file closure.
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "response": (
                "Inspected src/hook-runtime/scripts/changeforge_action_classifier.py. "
                "Found the classifier order. Residual risk: none. Next action: none."
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                turn_stage="read",
                read_evidence_seen=True,
                read_paths=["src/hook-runtime/scripts/changeforge_action_classifier.py"],
            )
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_read_only_command_risk_surface_is_not_engineering_closure_surface(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "response": "Inspected schema telemetry. Residual risk: none. Next action: none.",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(
                cwd,
                cache,
                command_risk_surfaces=["data-api"],
                closure_risk_surfaces=[],
                risk_surfaces=[],
            )
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_stop_review_no_change_profile_omits_edit_closure_groups(self) -> None:
        # Regression: review-only turns need findings/risk, not changed files or validation proof.
        event = {
            "hook_event_name": "Stop",
            "runtime": "claude",
            "response": "Reviewed src/app.py.",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, turn_stage="review", review_targets=["src/app.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("review_findings", result.stdout)
        self.assertIn("risk", result.stdout)
        self.assertNotIn("route_manifest", result.stdout)
        self.assertNotIn("changeforge_route", result.stdout)
        self.assertNotIn("changed files", result.stdout)
        self.assertNotIn("validation commands", result.stdout)

    def test_closure_reminder_omits_missing_flag_when_manifest_present(self) -> None:
        manifest_text = (
            "Change prepared. Tests run: pytest -q passed.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "  selected_capabilities:\n"
            "    - implementation-structure-design\n"
            "  required_references:\n"
            "    - references/routing-rules.md\n"
            "  required_quality_gates:\n"
            "    - implementation gate\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": manifest_text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("no changeforge_route manifest", result.stdout)
        self.assertNotIn("completion language but shows no validation", result.stdout)

    def test_copilot_stop_reads_final_text_from_transcript_path(self) -> None:
        manifest_text = (
            "Change prepared. Changed files listed. "
            "Validation: ran pytest -q, 12 passed, exit 0. Residual risk: none. "
            "Next steps: review.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - quality-test-gate\n"
            "  selected_capabilities:\n"
            "    - regression-testing\n"
            "  required_references:\n"
            "    - references/routing-rules.md\n"
            "  required_quality_gates:\n"
            "    - regression gate\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            transcript = cwd / "copilot-transcript.jsonl"
            transcript.write_text(
                json.dumps({"role": "user", "content": "fix hook"}) + "\n"
                + json.dumps({"role": "assistant", "content": manifest_text}) + "\n",
                encoding="utf-8",
            )
            seed_state(cwd, cache, runtime="copilot", changed_paths=["a.py"])
            event = {
                "hook_event_name": "Stop",
                "runtime": "copilot",
                "transcript_path": str(transcript),
            }
            result = run_stop(event, cwd, cache, agent="copilot")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("no complete changeforge_route manifest", result.stdout)

    def test_closure_reminder_flags_incomplete_route_manifest(self) -> None:
        manifest_text = (
            "Change prepared. Changed files and risk are noted. "
            "Validation: ran pytest -q, 12 passed. Next steps listed.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": manifest_text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("no complete changeforge_route manifest", result.stdout)
        self.assertIn("route_manifest", result.stdout)

    def test_completion_language_without_validation_is_flagged(self) -> None:
        # "Done." with a route manifest but no validation evidence is an
        # unverified completion claim; the gate must ask for evidence.
        text = (
            "Done. Fixed the bug.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("completion language but shows no validation", result.stdout)
        self.assertIn("completion_evidence", result.stdout)

    def test_completion_language_with_validation_is_not_flagged(self) -> None:
        text = (
            "Done. Ran python3 scripts/validate-hooks.py, passed, exit 0.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["src/hook-runtime/scripts/changeforge_common.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("completion language but shows no validation", result.stdout)

    def test_completion_language_with_negative_validation_is_flagged(self) -> None:
        text = (
            "Done. Validation not run.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "```\n"
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertIn("completion language but shows no validation", result.stdout)
        self.assertIn("not-verified disclosure", result.stdout)

    def test_not_verified_disclosure_is_not_completion_claim(self) -> None:
        text = (
            "Changes prepared, not verified because tests are unavailable; "
            "run pytest -q."
        )
        event = {"hook_event_name": "Stop", "runtime": "claude", "response": text}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            seed_state(cwd, cache, changed_paths=["a.py"])
            result = run_stop(event, cwd, cache)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("completion language but shows no validation", result.stdout)
        self.assertNotIn("completion_evidence", result.stdout)

    def test_fail_closed_blocks_on_unhandled_exception(self) -> None:
        gate = load_stop_gate()
        output = StringIO()
        with patch.dict(
            os.environ,
            {
                "CHANGEFORGE_AGENT": "codex",
                "CHANGEFORGE_STOP_CLOSURE_FAILURE_MODE": "fail_closed",
            },
            clear=True,
        ), patch.object(gate, "_main", side_effect=RuntimeError("boom")), redirect_stdout(output):
            self.assertEqual(gate.main(), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["decision"], "block")
        self.assertIn("failed closed", payload["reason"])


if __name__ == "__main__":
    unittest.main()
