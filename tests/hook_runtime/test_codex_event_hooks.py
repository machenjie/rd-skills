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


def _run(
    script: str,
    event: dict,
    *,
    mode: str | None = None,
    agent: str = "codex",
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event = dict(event)
        event.setdefault("cwd", cwd)
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env["CHANGEFORGE_AGENT"] = agent
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


class UserPromptRouteReminderTests(unittest.TestCase):
    SCRIPT = "changeforge_user_prompt_route_reminder.py"

    def test_user_prompt_submit_emits_route_reminder(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "add a redis cache to lookups"}
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("change-forge-router", context)
        self.assertIn("changeforge_route", context)

    def test_prompt_text_is_never_echoed(self) -> None:
        # Privacy: the reminder is fixed and must never include prompt content.
        secret = "SECRET_TOKEN_abc123_should_not_appear"
        event = {"hook_event_name": "UserPromptSubmit", "prompt": f"deploy with {secret}"}
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(secret, result.stdout)

    def test_off_mode_is_silent(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "x"}
        result = _run(self.SCRIPT, event, mode="off")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_monitor_mode_is_silent(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "x"}
        result = _run(self.SCRIPT, event, mode="monitor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_non_user_prompt_event_is_ignored(self) -> None:
        event = {"hook_event_name": "Stop"}
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


class PreToolRiskPreviewTests(unittest.TestCase):
    SCRIPT = "changeforge_pre_tool_risk_preview.py"

    def test_pre_edit_auth_path_emits_advisory(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/auth/session_token.py"},
        }
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("security", context)
        self.assertIn("change-forge-router", context)
        # Advisory only: never deny or block.
        self.assertNotIn("permissionDecision", result.stdout)
        self.assertNotIn("\"decision\"", result.stdout)

    def test_pre_edit_non_risk_path_is_silent(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "docs/notes.md"},
        }
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_bash_migration_command_emits_advisory(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "psql -f db/migrations/004_add_column.sql"},
        }
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("data-api", payload["hookSpecificOutput"]["additionalContext"])

    def test_script_name_marker_previews_high_risk_tool_permission(self) -> None:
        # Regression: preview must share PostToolUse marker boundaries for script paths.
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python scripts/run_migration.py"},
        }
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("tool-permission-sandbox", context)
        self.assertIn("agent-tool-permission-sandbox", context)
        self.assertIn("delivery gate", context)
        self.assertIn("reliability gate", context)
        self.assertIn("high-risk command", context)

    def test_destructive_commands_emit_tool_permission_advisory(self) -> None:
        commands = ["rm -rf tmp/generated", "git clean -fd"]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                }
                result = _run(self.SCRIPT, event)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                context = payload["hookSpecificOutput"]["additionalContext"]
                self.assertIn("tool-permission-sandbox", context)
                self.assertIn("agent-tool-permission-sandbox", context)
                self.assertIn("high-risk command", context)

    def test_read_only_bash_command_is_silent(self) -> None:
        commands = ['bash -lc "rg data-api src | head"', "cat README.md", "git diff README.md"]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                }
                result = _run(self.SCRIPT, event)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "")

    def test_validation_command_is_silent(self) -> None:
        commands = [
            "python3 scripts/eval-skill-professionalism.py",
            "pytest tests/hook_runtime/test_codex_event_hooks.py",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                }
                result = _run(self.SCRIPT, event)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "")

    def test_off_mode_is_silent(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/auth/session_token.py"},
        }
        result = _run(self.SCRIPT, event, mode="off")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_post_tool_use_event_is_ignored(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/auth/session_token.py"},
        }
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


class SubagentStopReminderTests(unittest.TestCase):
    SCRIPT = "changeforge_subagent_stop_reminder.py"

    def test_subagent_stop_emits_system_message(self) -> None:
        event = {"hook_event_name": "SubagentStop", "agent_type": "explore"}
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("systemMessage", payload)
        self.assertIn("changeforge_route", payload["systemMessage"])
        # Advisory only: never force continuation.
        self.assertNotIn("decision", payload)
        self.assertNotIn("continue", payload)

    def test_off_mode_is_silent(self) -> None:
        event = {"hook_event_name": "SubagentStop", "agent_type": "explore"}
        result = _run(self.SCRIPT, event, mode="off")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_non_subagent_stop_event_is_ignored(self) -> None:
        event = {"hook_event_name": "Stop"}
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


class SessionBootstrapSubagentStartTests(unittest.TestCase):
    SCRIPT = "changeforge_session_bootstrap.py"

    def test_subagent_start_emits_preflight_for_subagent(self) -> None:
        event = {"hook_event_name": "SubagentStart", "agent_type": "explore"}
        result = _run(self.SCRIPT, event)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SubagentStart")
        self.assertIn(
            "route preflight",
            payload["hookSpecificOutput"]["additionalContext"].casefold(),
        )
        # Advisory only: the subagent start must not be blocked.
        self.assertNotIn("\"decision\"", result.stdout)


class ClaudeLifecycleHookTests(unittest.TestCase):
    def test_user_prompt_submit_emits_claude_additional_context(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "change hook templates"}
        result = _run(
            "changeforge_user_prompt_route_reminder.py",
            event,
            agent="claude",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("changeforge_route", payload["hookSpecificOutput"]["additionalContext"])

    def test_pre_tool_use_emits_claude_advisory_without_permission_decision(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/auth/session_token.py"},
        }
        result = _run("changeforge_pre_tool_risk_preview.py", event, agent="claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("security", payload["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("permissionDecision", payload["hookSpecificOutput"])
        self.assertNotIn("decision", payload)

    def test_subagent_start_emits_claude_preflight_context(self) -> None:
        event = {"hook_event_name": "SubagentStart", "agent_type": "Explore"}
        result = _run("changeforge_session_bootstrap.py", event, agent="claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SubagentStart")
        self.assertIn("route preflight", payload["hookSpecificOutput"]["additionalContext"].casefold())

    def test_subagent_stop_emits_claude_system_message_without_continuation(self) -> None:
        event = {"hook_event_name": "SubagentStop", "agent_type": "Explore"}
        result = _run("changeforge_subagent_stop_reminder.py", event, agent="claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("systemMessage", payload)
        self.assertIn("changeforge_route", payload["systemMessage"])
        self.assertNotIn("decision", payload)
        self.assertNotIn("continue", payload)


if __name__ == "__main__":
    unittest.main()
