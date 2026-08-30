from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/quickstart.py"
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))


def _load_quickstart():
    spec = importlib.util.spec_from_file_location("quickstart_unit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class QuickstartPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quickstart = _load_quickstart()

    def test_codex_plan_uses_one_profile_free_runtime_build(self) -> None:
        plan = self.quickstart.build_plan(
            argparse.Namespace(
                agent="codex",
                scope="project",
                target=Path("/tmp/project"),
                dry_run=True,
                no_doctor=False,
            )
        )

        self.assertFalse(hasattr(plan, "selected_profile"))
        self.assertEqual(
            1,
            sum(command[:2] == ("python3", "scripts/build.py") for command in plan.commands),
        )
        self.assertEqual(26, plan.expected_skill_count)
        command_text = " ".join(" ".join(command) for command in plan.commands)
        self.assertNotIn("--profile", command_text)

    def test_openai_api_plan_has_no_installed_agent_profiles(self) -> None:
        plan = self.quickstart.build_plan(
            argparse.Namespace(
                agent="openai-api",
                scope=None,
                target=None,
                dry_run=True,
                no_doctor=False,
            )
        )

        self.assertEqual((), plan.agent_profiles)

    def test_public_help_and_parser_reject_obsolete_profile_before_execution(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertNotIn("--profile", help_result.stdout)

        obsolete = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--agent",
                "codex",
                "--scope",
                "project",
                "--target",
                "/tmp/profile-must-not-run",
                "--profile",
                "full",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, obsolete.returncode)
        self.assertIn("unrecognized arguments: --profile full", obsolete.stderr)


if __name__ == "__main__":
    unittest.main()
