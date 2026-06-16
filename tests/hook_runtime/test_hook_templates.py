from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOK_ROOT = ROOT / "src" / "hook-runtime"


class HookTemplateTests(unittest.TestCase):
    def collect_commands(self, value: object) -> list[str]:
        commands: list[str] = []

        def collect(child: object) -> None:
            if isinstance(child, dict):
                command = child.get("command")
                if isinstance(command, str):
                    commands.append(command)
                for nested in child.values():
                    collect(nested)
            elif isinstance(child, list):
                for nested in child:
                    collect(nested)

        collect(value)
        return commands

    def collect_timeouts(self, value: object) -> list[int]:
        timeouts: list[int] = []

        def collect(child: object) -> None:
            if isinstance(child, dict):
                timeout = child.get("timeout")
                if isinstance(timeout, int):
                    timeouts.append(timeout)
                for nested in child.values():
                    collect(nested)
            elif isinstance(child, list):
                for nested in child:
                    collect(nested)

        collect(value)
        return timeouts

    def command_script_names(self, value: object) -> list[str]:
        names: list[str] = []
        for command in self.collect_commands(value):
            names.append(command.split("/")[-1].split(".py")[0].strip('"'))
        return names

    def test_codex_hooks_json_parses(self) -> None:
        data = json.loads((HOOK_ROOT / "templates" / "codex" / "hooks.json").read_text())
        self.assertIn("PostToolUse", data["hooks"])
        self.assertIn("Stop", data["hooks"])
        commands = self.collect_commands(data["hooks"])
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
        for event in (
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "SubagentStart",
            "SubagentStop",
            "Stop",
        ):
            self.assertIn(event, data["hooks"])
        session_commands = json.dumps(data["hooks"]["SessionStart"])
        self.assertIn("changeforge_session_bootstrap", session_commands)
        commands = self.collect_commands(data["hooks"])
        self.assertTrue(commands)
        for command in commands:
            self.assertIn("CHANGEFORGE_AGENT=claude", command)
            self.assertIn("/usr/bin/env python3", command)
            self.assertIn("${CLAUDE_PROJECT_DIR}/.claude/hooks/", command)
        self.assertTrue(self.collect_timeouts(data["hooks"]))
        self.assertTrue(all(timeout <= 10 for timeout in self.collect_timeouts(data["hooks"])))

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
        for event in (
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "SubagentStart",
            "SubagentStop",
            "Stop",
        ):
            self.assertIn(event, hooks)
        commands = json.dumps(hooks)
        self.assertIn("${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/", commands)
        self.assertIn("CHANGEFORGE_AGENT=claude", commands)
        self.assertIn("/usr/bin/env python3", commands)
        self.assertNotIn("CLAUDE_PROJECT_DIR", commands)
        self.assertTrue(self.collect_timeouts(hooks))
        self.assertTrue(all(timeout <= 10 for timeout in self.collect_timeouts(hooks)))

    def test_copilot_template_is_flat_and_wires_events(self) -> None:
        # VS Code Copilot uses the flat (matcher-less) format: each event maps
        # directly to a list of command entries, no matcher groups.
        data = json.loads(
            (HOOK_ROOT / "templates" / "copilot" / "changeforge-hooks.json").read_text()
        )
        self.assertEqual(data["version"], 1)
        hooks = data["hooks"]
        for event, script in (
            ("SessionStart", "changeforge_session_bootstrap"),
            ("PostToolUse", "changeforge_post_edit_structure_gate"),
            ("SubagentStart", "changeforge_session_bootstrap"),
            ("Stop", "changeforge_stop_closure_gate"),
        ):
            self.assertIn(event, hooks)
            entries = hooks[event]
            # Flat format: entries carry "command" directly, not nested "hooks".
            self.assertTrue(all("command" in entry for entry in entries))
            self.assertTrue(all("timeoutSec" in entry for entry in entries))
            self.assertFalse(any("timeout" in entry for entry in entries))
            self.assertNotIn("matcher", json.dumps(entries))
            self.assertIn(script, json.dumps(entries))
        self.assertNotIn("UserPromptSubmit", hooks)
        self.assertNotIn("PreToolUse", hooks)
        self.assertNotIn("SubagentStop", hooks)
        commands = json.dumps(hooks)
        self.assertIn("CHANGEFORGE_AGENT=copilot", commands)
        self.assertIn("/.github/hooks/changeforge/", commands)
        self.assertIn("CHANGEFORGE_HOOK_MODE=block", json.dumps(hooks["Stop"]))
        for event in ("SessionStart", "PostToolUse", "SubagentStart"):
            self.assertNotIn("CHANGEFORGE_HOOK_MODE=block", json.dumps(hooks[event]))

    def test_copilot_user_template_resolves_from_home(self) -> None:
        data = json.loads(
            (HOOK_ROOT / "templates" / "copilot-user" / "changeforge-hooks.json").read_text()
        )
        self.assertEqual(data["version"], 1)
        commands = json.dumps(data["hooks"])
        self.assertNotIn("UserPromptSubmit", data["hooks"])
        self.assertNotIn("PreToolUse", data["hooks"])
        self.assertNotIn("SubagentStop", data["hooks"])
        self.assertIn("${HOME}/.copilot/hooks/changeforge/", commands)
        self.assertIn("CHANGEFORGE_AGENT=copilot", commands)
        self.assertIn("CHANGEFORGE_HOOK_MODE=block", json.dumps(data["hooks"]["Stop"]))
        self.assertNotIn("git rev-parse", commands)

    def test_claude_post_tool_batch_invokes_read_context_gate(self) -> None:
        for template in (
            HOOK_ROOT / "templates" / "claude" / "settings.changeforge-hooks.fragment.json",
            HOOK_ROOT / "templates" / "claude-user" / "settings.changeforge-hooks.fragment.json",
        ):
            data = json.loads(template.read_text())
            batch_commands = json.dumps(data["hooks"]["PostToolBatch"])
            self.assertIn("changeforge_professional_injector", batch_commands)
            self.assertIn("changeforge_read_context_gate", batch_commands)
            self.assertIn("changeforge_review_gate", batch_commands)

    def test_post_tool_use_matchers_include_lowercase_mcp_read_tools(self) -> None:
        # Regression: real MCP tool names are lowercase and may be matched case-sensitively.
        required_tokens = (
            "mcp__filesystem__read_file",
            "mcp__filesystem__list_directory",
            "mcp__github__get_file_contents",
            "mcp__github__pull_request_read",
            "mcp__github__search_code",
            "mcpfilesystemreadfile",
            "mcpfilesystemlistdirectory",
            "mcpgithubgetfilecontents",
            "mcpgithubpullrequestread",
            "mcpgithubsearchcode",
        )
        for template in (
            HOOK_ROOT / "templates" / "codex" / "hooks.json",
            HOOK_ROOT / "templates" / "codex-user" / "hooks.json",
            HOOK_ROOT / "templates" / "claude" / "settings.changeforge-hooks.fragment.json",
            HOOK_ROOT / "templates" / "claude-user" / "settings.changeforge-hooks.fragment.json",
        ):
            data = json.loads(template.read_text())
            post_tool_use = json.dumps(data["hooks"]["PostToolUse"])
            for token in required_tokens:
                self.assertIn(token, post_tool_use, template.name)

    def test_compaction_snapshot_runs_before_reinject_without_overwriting_active_context(self) -> None:
        templates = (
            HOOK_ROOT / "templates" / "codex" / "hooks.json",
            HOOK_ROOT / "templates" / "codex-user" / "hooks.json",
            HOOK_ROOT / "templates" / "claude" / "settings.changeforge-hooks.fragment.json",
            HOOK_ROOT / "templates" / "claude-user" / "settings.changeforge-hooks.fragment.json",
            HOOK_ROOT / "templates" / "copilot" / "changeforge-hooks.json",
            HOOK_ROOT / "templates" / "copilot-user" / "changeforge-hooks.json",
        )
        expected = [
            "changeforge_compaction_snapshot",
            "changeforge_session_bootstrap",
            "changeforge_compaction_reinject",
            "changeforge_professional_injector",
        ]
        for template in templates:
            data = json.loads(template.read_text())
            names = self.command_script_names(data["hooks"]["SessionStart"])
            self.assertEqual(names[:4], expected)

    def test_copilot_no_unsupported_advisory_events(self) -> None:
        for template in (
            HOOK_ROOT / "templates" / "copilot" / "changeforge-hooks.json",
            HOOK_ROOT / "templates" / "copilot-user" / "changeforge-hooks.json",
        ):
            data = json.loads(template.read_text())
            for event in ("UserPromptSubmit", "PreToolUse", "SubagentStop", "PostToolBatch"):
                self.assertNotIn(event, data["hooks"])

    def test_bootstrap_fragment_exists_and_points_to_router(self) -> None:
        fragment = (
            HOOK_ROOT / "templates" / "bootstrap" / "changeforge-route-preflight.md"
        ).read_text(encoding="utf-8")
        self.assertIn("change-forge-router", fragment)
        self.assertIn("implementation-structure-design", fragment)
        self.assertIn("agent-execution-discipline", fragment)


if __name__ == "__main__":
    unittest.main()
