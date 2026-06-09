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

    def test_codex_fragment_has_no_session_start(self) -> None:
        # Codex has no stable session-start hook; the bootstrap is advisory there.
        data = json.loads((HOOK_ROOT / "templates" / "codex" / "hooks.json").read_text())
        self.assertNotIn("SessionStart", data["hooks"])

    def test_bootstrap_fragment_exists_and_points_to_router(self) -> None:
        fragment = (
            HOOK_ROOT / "templates" / "bootstrap" / "changeforge-route-preflight.md"
        ).read_text(encoding="utf-8")
        self.assertIn("change-forge-router", fragment)
        self.assertIn("implementation-structure-design", fragment)
        self.assertIn("agent-execution-discipline", fragment)


if __name__ == "__main__":
    unittest.main()
