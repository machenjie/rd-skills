from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOK_ROOT = ROOT / "src" / "hook-runtime"


class HookTemplateTests(unittest.TestCase):
    def test_codex_hooks_json_parses(self) -> None:
        data = json.loads((HOOK_ROOT / "templates" / "codex" / "hooks.json").read_text())
        self.assertIn("PostToolUse", data["hooks"])
        self.assertIn("Stop", data["hooks"])
        commands = []

        def collect(value: object) -> None:
            if isinstance(value, dict):
                command = value.get("command")
                if isinstance(command, str):
                    commands.append(command)
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(data["hooks"])
        self.assertTrue(commands)
        for command in commands:
            self.assertIn("CHANGEFORGE_AGENT=codex", command)
            self.assertIn("/usr/bin/env python3", command)

    def test_claude_settings_fragment_parses(self) -> None:
        data = json.loads(
            (
                HOOK_ROOT
                / "templates"
                / "claude"
                / "settings.changeforge-hooks.fragment.json"
            ).read_text()
        )
        self.assertIn("PostToolUse", data["hooks"])
        self.assertIn("Stop", data["hooks"])
        self.assertIn("SessionStart", data["hooks"])
        session_commands = json.dumps(data["hooks"]["SessionStart"])
        self.assertIn("changeforge_session_bootstrap", session_commands)

    def test_codex_wires_session_start_and_new_events(self) -> None:
        # Codex now exposes SessionStart and several other events; the template
        # must wire each one to its dedicated ChangeForge hook script.
        data = json.loads((HOOK_ROOT / "templates" / "codex" / "hooks.json").read_text())
        hooks = data["hooks"]
        for event, script in (
            ("SessionStart", "changeforge_session_bootstrap"),
            ("UserPromptSubmit", "changeforge_user_prompt_route_reminder"),
            ("PreToolUse", "changeforge_pre_tool_risk_preview"),
            ("SubagentStart", "changeforge_session_bootstrap"),
            ("SubagentStop", "changeforge_subagent_stop_reminder"),
        ):
            self.assertIn(event, hooks)
            self.assertIn(script, json.dumps(hooks[event]))
        # SessionStart matcher covers the post-compaction compact source.
        self.assertIn("compact", json.dumps(hooks["SessionStart"]))

    def test_codex_user_template_resolves_from_codex_home(self) -> None:
        # The user template mirrors the project events but resolves its command
        # path from CODEX_HOME (with a $HOME/.codex fallback), never the git root.
        data = json.loads((HOOK_ROOT / "templates" / "codex-user" / "hooks.json").read_text())
        hooks = data["hooks"]
        for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"):
            self.assertIn(event, hooks)
        commands = json.dumps(hooks)
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/hooks/", commands)
        self.assertIn("CHANGEFORGE_AGENT=codex", commands)
        self.assertNotIn("git rev-parse", commands)

    def test_claude_user_fragment_resolves_from_config_dir(self) -> None:
        data = json.loads(
            (
                HOOK_ROOT
                / "templates"
                / "claude-user"
                / "settings.changeforge-hooks.fragment.json"
            ).read_text()
        )
        hooks = data["hooks"]
        self.assertIn("SessionStart", hooks)
        self.assertIn("PostToolUse", hooks)
        self.assertIn("Stop", hooks)
        commands = json.dumps(hooks)
        self.assertIn("${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/", commands)
        self.assertNotIn("CLAUDE_PROJECT_DIR", commands)

    def test_copilot_template_is_flat_and_wires_events(self) -> None:
        # VS Code Copilot uses the flat (matcher-less) format: each event maps
        # directly to a list of command entries, no matcher groups.
        data = json.loads(
            (HOOK_ROOT / "templates" / "copilot" / "changeforge-hooks.json").read_text()
        )
        hooks = data["hooks"]
        for event, script in (
            ("SessionStart", "changeforge_session_bootstrap"),
            ("UserPromptSubmit", "changeforge_user_prompt_route_reminder"),
            ("PreToolUse", "changeforge_pre_tool_risk_preview"),
            ("PostToolUse", "changeforge_post_edit_structure_gate"),
            ("SubagentStart", "changeforge_session_bootstrap"),
            ("SubagentStop", "changeforge_subagent_stop_reminder"),
            ("Stop", "changeforge_stop_closure_gate"),
        ):
            self.assertIn(event, hooks)
            entries = hooks[event]
            # Flat format: entries carry "command" directly, not nested "hooks".
            self.assertTrue(all("command" in entry for entry in entries))
            self.assertNotIn("matcher", json.dumps(entries))
            self.assertIn(script, json.dumps(entries))
        commands = json.dumps(hooks)
        self.assertIn("CHANGEFORGE_AGENT=copilot", commands)
        self.assertIn("/.github/hooks/changeforge/", commands)

    def test_copilot_user_template_resolves_from_home(self) -> None:
        data = json.loads(
            (HOOK_ROOT / "templates" / "copilot-user" / "changeforge-hooks.json").read_text()
        )
        commands = json.dumps(data["hooks"])
        self.assertIn("${HOME}/.copilot/hooks/changeforge/", commands)
        self.assertIn("CHANGEFORGE_AGENT=copilot", commands)
        self.assertNotIn("git rev-parse", commands)

    def test_bootstrap_fragment_exists_and_points_to_router(self) -> None:
        fragment = (
            HOOK_ROOT / "templates" / "bootstrap" / "changeforge-route-preflight.md"
        ).read_text(encoding="utf-8")
        self.assertIn("change-forge-router", fragment)
        self.assertIn("implementation-structure-design", fragment)
        self.assertIn("agent-execution-discipline", fragment)


if __name__ == "__main__":
    unittest.main()
