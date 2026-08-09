from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/quickstart.py"


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

    def test_codex_auto_plan_selects_one_recommended_build(self) -> None:
        plan = self.quickstart.build_plan(
            argparse.Namespace(
                agent="codex",
                scope="project",
                target=Path("/tmp/project"),
                profile="auto",
                dry_run=True,
                no_doctor=False,
            )
        )

        self.assertEqual("recommended", plan.selected_profile)
        self.assertEqual(
            1,
            sum(command[:2] == ("python3", "scripts/build.py") for command in plan.commands),
        )
        self.assertEqual(27, plan.expected_skill_count)

    def test_openai_api_plan_has_no_installed_agent_profiles(self) -> None:
        plan = self.quickstart.build_plan(
            argparse.Namespace(
                agent="openai-api",
                scope=None,
                target=None,
                profile="auto",
                dry_run=True,
                no_doctor=False,
            )
        )

        self.assertEqual((), plan.agent_profiles)


if __name__ == "__main__":
    unittest.main()
