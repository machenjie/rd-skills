from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


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
        self.assertIn("route preflight", payload["additionalContext"].casefold())
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


if __name__ == "__main__":
    unittest.main()
