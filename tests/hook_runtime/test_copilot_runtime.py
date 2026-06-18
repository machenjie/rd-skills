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


def _load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_copilot_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _seed_state(cwd: Path, cache: Path, **fields: object) -> None:
    common = _load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        state: dict[str, object] = {"runtime": "copilot"}
        state.update(fields)
        common.save_state(cwd, state)
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


def _load_state(cwd: Path, cache: Path) -> dict:
    common = _load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        return common.load_state(cwd)
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


def _run(script: str, event: dict, *, mode: str | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event = dict(event)
        event.setdefault("cwd", cwd)
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env["CHANGEFORGE_AGENT"] = "copilot"
        if mode is None:
            env.pop("CHANGEFORGE_HOOK_MODE", None)
        else:
            env["CHANGEFORGE_HOOK_MODE"] = mode
        return subprocess.run(
            [sys.executable, str(SCRIPT_DIR / script)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=cwd,
            env=env,
            check=False,
        )


class CopilotRuntimeTests(unittest.TestCase):
    def test_session_start_emits_additional_context(self) -> None:
        event = {"hook_event_name": "SessionStart", "source": "new"}
        result = _run("changeforge_session_bootstrap.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["additionalContext"]
        self.assertIn("route preflight", context.casefold())
        self.assertIn("ChangeForge Copilot Skill Summary", context)
        self.assertIn("change-impact-analyzer", context)
        self.assertIn("security-privacy-gate", context)
        self.assertNotIn("hookSpecificOutput", payload)

    def test_subagent_start_emits_skill_summary_context(self) -> None:
        event = {"hook_event_name": "SubagentStart"}
        result = _run("changeforge_session_bootstrap.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["additionalContext"]
        self.assertIn("ChangeForge Copilot Skill Summary", context)
        self.assertIn("quality-test-gate", context)
        self.assertNotIn("hookSpecificOutput", payload)

    def test_risk_gate_matches_vscode_replace_string_tool(self) -> None:
        # VS Code Copilot uses replace_string_in_file with a camelCase filePath;
        # the risk gate must still recognize the auth surface and emit JSON.
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "replace_string_in_file",
            "tool_input": {"filePath": "src/auth/session_token.py"},
        }
        result = _run("changeforge_risk_surface_gate.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["additionalContext"]
        self.assertIn("security", context)
        self.assertNotIn("decision", payload)

    def test_risk_gate_matches_vscode_run_terminal_command(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "runTerminalCommand",
            "tool_input": {"command": "psql -f db/migrations/004_add_column.sql"},
        }
        result = _run("changeforge_risk_surface_gate.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("data-api", payload["additionalContext"])
        self.assertNotIn("decision", payload)

    def test_structure_gate_matches_vscode_create_file(self) -> None:
        # create_file with a service path should trigger the structure gate.
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "create_file",
            "tool_input": {"filePath": "src/services/payment_service.py"},
        }
        result = _run("changeforge_post_edit_structure_gate.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        # A structural path produces a JSON additionalContext reminder.
        payload = json.loads(result.stdout)
        self.assertIn("ChangeForge Structure Gate triggered", payload["additionalContext"])
        self.assertNotIn("hookSpecificOutput", payload)
        self.assertNotIn("decision", payload)

    def test_pre_tool_preview_does_not_emit_unsupported_context(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "create_file",
            "tool_input": {"filePath": "src/auth/login.py"},
        }
        result = _run("changeforge_pre_tool_risk_preview.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Copilot PreToolUse supports permission decisions, not additionalContext.
        self.assertEqual(result.stdout.strip(), "")
        self.assertNotIn("permissionDecision", result.stdout)
        self.assertNotIn("\"decision\"", result.stdout)

    def test_non_risk_vscode_edit_is_silent(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "replace_string_in_file",
            "tool_input": {"filePath": "docs/notes.md"},
        }
        result = _run("changeforge_risk_surface_gate.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_user_prompt_reminder_does_not_emit_unsupported_context(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "add redis cache"}
        result = _run("changeforge_user_prompt_route_reminder.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Copilot userPromptSubmitted output is not processed, so avoid a fake
        # context injection signal.
        self.assertEqual(result.stdout.strip(), "")

    def test_subagent_stop_reminder_does_not_emit_unsupported_system_message(self) -> None:
        event = {"hook_event_name": "SubagentStop"}
        result = _run("changeforge_subagent_stop_reminder.py", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_stop_block_mode_emits_top_level_decision(self) -> None:
        # Regression: Copilot agentStop consumes top-level decision/reason, not Codex hookSpecificOutput.
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = cache
            env["CHANGEFORGE_AGENT"] = "copilot"
            env["CHANGEFORGE_HOOK_MODE"] = "block"

            seed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import importlib.util, pathlib, os; "
                        f"p=pathlib.Path({str(SCRIPT_DIR / 'changeforge_common.py')!r}); "
                        "s=importlib.util.spec_from_file_location('cf', p); "
                        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                        f"m.save_state(pathlib.Path({cwd!r}), {{'runtime':'copilot','changed_paths':['a.py']}})"
                    ),
                ],
                text=True,
                capture_output=True,
                cwd=cwd,
                env=env,
                check=False,
            )
            self.assertEqual(seed.returncode, 0, seed.stderr)

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "changeforge_stop_closure_gate.py")],
                input=json.dumps(
                    {
                        "hook_event_name": "Stop",
                        "cwd": cwd,
                        "stop_hook_active": False,
                        "response": "done",
                    }
                ),
                text=True,
                capture_output=True,
                cwd=cwd,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("changeforge_route", payload["reason"])
            self.assertNotIn("hookSpecificOutput", payload)

    def test_stop_block_mode_does_not_block_when_closure_evidence_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            _seed_state(cwd, cache, changed_paths=["src/hook-runtime/scripts/example.py"])
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = str(cache)
            env["CHANGEFORGE_AGENT"] = "copilot"
            env["CHANGEFORGE_HOOK_MODE"] = "block"
            response = (
                "I used the ChangeForge skill path. Changed files: example.py. "
                "Validation: ran python3 -m unittest discover -s tests/hook_runtime, "
                "1 passed, exit 0. Residual risk: none. Next steps: review.\n\n"
                "```yaml\n"
                "changeforge_implementation_preflight:\n"
                "  read_evidence:\n"
                "    target_files:\n"
                "      - src/hook-runtime/scripts/example.py\n"
                "    sibling_files:\n"
                "      - src/hook-runtime/scripts/changeforge_common.py\n"
                "  placement_decision:\n"
                "    target_file: src/hook-runtime/scripts/example.py\n"
                "    reason: hook runtime script directory owns hook behavior\n"
                "  reuse_decision:\n"
                "    direct_reuse:\n"
                "      - symbol_or_path: src/hook-runtime/scripts/changeforge_common.py\n"
                "  object_boundary:\n"
                "    artifact_type: module\n"
                "    owner: src/hook-runtime/scripts/example.py\n"
                "    state_or_invariant: hook script owns its runtime behavior boundary\n"
                "  test_plan:\n"
                "    validation_commands:\n"
                "      - python3 -m unittest discover -s tests/hook_runtime\n"
                "  risk:\n"
                "    rollback_or_revert_path: revert patch\n"
                "```\n\n"
                "```yaml\n"
                "repository_context:\n"
                "  source_of_truth:\n"
                "    - src/hook-runtime/scripts/example.py\n"
                "  reuse_candidates:\n"
                "    - src/hook-runtime/scripts/changeforge_stop_closure_gate.py\n"
                "  validation_candidates:\n"
                "    - python3 -m unittest discover -s tests/hook_runtime\n"
                "  graph_freshness: current\n"
                "  residual_risk:\n"
                "    - none\n"
                "```\n\n"
                "Repository context map: inspected src/hook-runtime/scripts/example.py, sibling "
                "hook scripts, tests/hook_runtime, and hook config before editing.\n"
                "Workflow state: implementation-planning moved to coding, then testing after "
                "the validation command was selected.\n"
                "Tool permission/sandbox: filesystem edit only; no external command or "
                "destructive operation used.\n"
                "Plan-execution consistency: planned path src/hook-runtime/scripts/example.py "
                "matches the actual changed path with no unplanned behavior.\n"
                "Skill efficacy benchmark: no capability behavior claim changed; existing "
                "hook runtime regression fixture covers the changed closure behavior.\n"
                "Validation freshness: python3 -m unittest discover -s tests/hook_runtime "
                "ran after the final material edit.\n\n"
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
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "changeforge_stop_closure_gate.py")],
                input=json.dumps(
                    {
                        "hook_event_name": "Stop",
                        "cwd": str(cwd),
                        "stop_hook_active": False,
                        "response": response,
                    }
                ),
                text=True,
                capture_output=True,
                cwd=str(cwd),
                env=env,
                check=False,
            )
            state = _load_state(cwd, cache)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertEqual(state["changed_paths"], [])


if __name__ == "__main__":
    unittest.main()
