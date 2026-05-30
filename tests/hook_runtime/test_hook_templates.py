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


if __name__ == "__main__":
    unittest.main()
