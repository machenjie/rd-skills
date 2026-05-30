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
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def run_structure(event: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event["cwd"] = cwd
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env.pop("CHANGEFORGE_HOOK_MODE", None)
        env.pop("CHANGEFORGE_AGENT", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "changeforge_post_edit_structure_gate.py")],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=cwd,
            env=env,
            check=False,
        )


class PostEditStructureGateTests(unittest.TestCase):
    def test_readme_edit_does_not_warn(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "README.md"},
        }
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Structure Gate triggered", result.stdout)

    def test_new_service_file_warns(self) -> None:
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_apply_patch.json").read_text())
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Structure Gate triggered", result.stdout)
        self.assertIn("implementation-structure-design", result.stdout)

    def test_utils_common_shared_edit_warns(self) -> None:
        event = {
            "runtime": "claude",
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/shared/utils/date_helpers.py"},
        }
        result = run_structure(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Structure Gate triggered", result.stdout)


if __name__ == "__main__":
    unittest.main()
