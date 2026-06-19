from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "quickstart.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("quickstart", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _args(**overrides):
    values = {
        "agent": "codex",
        "scope": "user",
        "target": None,
        "profile": "auto",
        "dry_run": False,
        "with_hooks": False,
        "with_bootstrap": False,
        "no_doctor": False,
        "yes": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class QuickstartTests(unittest.TestCase):
    def test_auto_profile_resolution(self) -> None:
        module = _load_module()
        self.assertEqual(module.resolve_profile("codex", "user", "auto"), "recommended")
        self.assertEqual(module.resolve_profile("claude", "project", "auto"), "full")
        self.assertEqual(module.resolve_profile("cline", "project", "auto"), "full")
        self.assertEqual(module.resolve_profile("openai-api", None, "auto"), "recommended")
        self.assertEqual(module.resolve_profile("codex", "user", "dev"), "dev")

    def test_codex_user_command_plan(self) -> None:
        module = _load_module()
        plan = module.build_plan(_args(agent="codex", scope="user"))
        self.assertEqual(plan.selected_profile, "recommended")
        self.assertEqual(plan.expected_skill_count, 19)
        self.assertEqual(
            plan.commands,
            [
                ["python3", "scripts/build.py", "--profile", "recommended"],
                [
                    "python3",
                    "installers/install.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "user",
                    "--profile",
                    "recommended",
                ],
                [
                    "python3",
                    "installers/doctor.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "user",
                    "--profile",
                    "recommended",
                ],
            ],
        )

    def test_claude_project_requires_target(self) -> None:
        module = _load_module()
        with self.assertRaisesRegex(ValueError, "--target is required"):
            module.build_plan(_args(agent="claude", scope="project"))

    def test_project_scope_defaults_to_full(self) -> None:
        module = _load_module()
        plan = module.build_plan(
            _args(agent="copilot", scope="project", target=Path("/tmp/changeforge-project"))
        )
        self.assertEqual(plan.selected_profile, "full")
        self.assertEqual(plan.expected_skill_count, 26)
        self.assertIn("--target", plan.commands[1])

    def test_cline_project_command_plan(self) -> None:
        module = _load_module()
        target = Path("/tmp/changeforge-cline")
        plan = module.build_plan(_args(agent="cline", scope="project", target=target))
        self.assertEqual(plan.selected_profile, "full")
        self.assertEqual(plan.commands[1][:8], [
            "python3",
            "installers/install.py",
            "--agent",
            "cline",
            "--scope",
            "project",
            "--profile",
            "full",
        ])
        self.assertIn(str(target), plan.commands[1])
        self.assertEqual(plan.commands[2][2:6], ["--agent", "cline", "--scope", "project"])

    def test_user_scope_defaults_to_recommended(self) -> None:
        module = _load_module()
        plan = module.build_plan(_args(agent="claude", scope="user"))
        self.assertEqual(plan.selected_profile, "recommended")

    def test_dev_profile_must_be_explicit(self) -> None:
        module = _load_module()
        auto_plan = module.build_plan(_args(agent="codex", scope="user"))
        explicit_plan = module.build_plan(_args(agent="codex", scope="user", profile="dev"))
        self.assertNotEqual(auto_plan.selected_profile, "dev")
        self.assertEqual(explicit_plan.selected_profile, "dev")

    def test_dry_run_does_not_execute_commands(self) -> None:
        module = _load_module()
        executed: list[list[str]] = []
        plan = module.build_plan(_args(agent="codex", scope="user", dry_run=True))
        result = module.run_plan(plan, dry_run=True, runner=lambda command: executed.append(list(command)))
        self.assertEqual(result, 0)
        self.assertEqual(executed, [])

    def test_command_failure_propagates_non_zero(self) -> None:
        module = _load_module()

        def failing_runner(command):
            raise subprocess.CalledProcessError(7, command)

        plan = module.build_plan(_args(agent="codex", scope="user"))
        self.assertEqual(module.run_plan(plan, dry_run=False, runner=failing_runner), 7)

    def test_openai_api_uses_zip_dry_run_and_skips_doctor(self) -> None:
        module = _load_module()
        plan = module.build_plan(_args(agent="openai-api", scope=None))
        self.assertEqual(plan.selected_profile, "recommended")
        self.assertFalse(plan.doctor_expected)
        self.assertEqual(
            plan.commands,
            [
                ["python3", "scripts/build.py", "--profile", "recommended"],
                [
                    "python3",
                    "installers/install.py",
                    "--agent",
                    "openai-api",
                    "--profile",
                    "recommended",
                    "--dry-run",
                ],
            ],
        )


if __name__ == "__main__":
    unittest.main()
