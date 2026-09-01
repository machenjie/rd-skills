from __future__ import annotations

import argparse
import io
import importlib.util
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


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

    def test_explicit_options_preserve_exact_command_plan(self) -> None:
        plan = self.quickstart.build_plan(
            argparse.Namespace(
                agent="codex",
                scope="project",
                target=Path("/tmp/project"),
                dry_run=True,
                no_doctor=False,
            )
        )

        self.assertEqual(
            (
                ("python3", "scripts/build.py"),
                (
                    "python3",
                    "installers/install.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--target",
                    "/tmp/project",
                    "--dry-run",
                ),
                (
                    "python3",
                    "installers/doctor.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--target",
                    "/tmp/project",
                ),
            ),
            plan.commands,
        )

        openai_plan = self.quickstart.build_plan(
            argparse.Namespace(
                agent="openai-api",
                scope=None,
                target=None,
                dry_run=False,
                no_doctor=False,
            )
        )
        self.assertEqual(
            (
                ("python3", "scripts/build.py"),
                (
                    "python3",
                    "installers/install.py",
                    "--agent",
                    "openai-api",
                    "--scope",
                    "project",
                ),
            ),
            openai_plan.commands,
        )
        self.assertFalse(openai_plan.doctor_expected)

    def test_runtime_scope_is_rejected_before_execution(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(
                sys,
                "argv",
                ["quickstart.py", "--agent", "codex"],
            ),
            mock.patch.object(self.quickstart, "run_plan") as run_plan,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            self.assertEqual(2, self.quickstart.main())

        run_plan.assert_not_called()
        self.assertEqual("", stdout.getvalue())
        self.assertIn("--scope is required for runtime installs", stderr.getvalue())

    def test_run_plan_keeps_argv_and_hides_success_diagnostics(self) -> None:
        plan = self.quickstart.QuickstartPlan(
            expected_skill_count=26,
            commands=(("python3", "scripts/build.py"),),
            doctor_expected=False,
            agent_profiles=(),
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(
                self.quickstart.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    args=["python3", "scripts/build.py"],
                    returncode=0,
                    stdout="internal build diagnostics\n",
                    stderr="",
                ),
            ) as child,
            redirect_stdout(stdout),
        ):
            self.assertEqual(
                0,
                self.quickstart.run_plan(plan, dry_run=False, verbose=False),
            )

        child.assert_called_once_with(
            ["python3", "scripts/build.py"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual("", stdout.getvalue())

    def test_run_plan_preserves_material_success_output_and_all_stderr(self) -> None:
        plan = self.quickstart.QuickstartPlan(
            expected_skill_count=26,
            commands=(("python3", "installers/install.py"),),
            doctor_expected=False,
            agent_profiles=(),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(
                self.quickstart.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    args=list(plan.commands[0]),
                    returncode=0,
                    stdout=(
                        "install: internal inventory=26\n"
                        "install: removed 2 legacy artifacts\n"
                        "- legacy hooks directory\n"
                        "install: backup written to /safe/recovery/backup\n"
                        "  restore this path before retrying\n"
                        "install: manifest digest=internal\n"
                    ),
                    stderr="warning: restart the host before continuing\n",
                ),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            self.assertEqual(
                0,
                self.quickstart.run_plan(plan, dry_run=False, verbose=False),
            )

        self.assertEqual(
            "install: removed 2 legacy artifacts\n"
            "- legacy hooks directory\n"
            "install: backup written to /safe/recovery/backup\n"
            "  restore this path before retrying\n",
            stdout.getvalue(),
        )
        self.assertEqual(
            "warning: restart the host before continuing\n",
            stderr.getvalue(),
        )

    def test_run_plan_forwards_failure_details_and_exact_exit(self) -> None:
        plan = self.quickstart.QuickstartPlan(
            expected_skill_count=26,
            commands=(
                ("python3", "installers/install.py", "--scope", "user"),
                ("python3", "installers/doctor.py", "--scope", "user"),
            ),
            doctor_expected=True,
            agent_profiles=(),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(
                self.quickstart.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    args=list(plan.commands[0]),
                    returncode=7,
                    stdout="install: specific problem\n",
                    stderr="install: actionable failure\n",
                ),
            ) as child,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            self.assertEqual(
                7,
                self.quickstart.run_plan(plan, dry_run=False, verbose=False),
            )

        child.assert_called_once_with(
            ["python3", "installers/install.py", "--scope", "user"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual("install: specific problem\n", stdout.getvalue())
        self.assertEqual("install: actionable failure\n", stderr.getvalue())

    def test_normal_output_gives_authority_derived_next_step_per_host(self) -> None:
        expected = {
            "codex": ("$engineering-control-plane", "full rd-skills workflow"),
            "claude": ("/engineering-control-plane", "full rd-skills workflow"),
            "copilot": ("/engineering-control-plane", "Copilot CLI"),
            "cline": ("artifacts are healthy", "not established"),
            "openai-api": ("packages were generated and verified", "API integration"),
        }
        for agent, required in expected.items():
            with self.subTest(agent=agent):
                stdout = io.StringIO()
                argv = ["quickstart.py", "--agent", agent]
                if agent != "openai-api":
                    argv.extend(("--scope", "user"))
                with (
                    mock.patch.object(sys, "argv", argv),
                    mock.patch.object(self.quickstart, "run_plan", return_value=0),
                    redirect_stdout(stdout),
                ):
                    self.assertEqual(0, self.quickstart.main())

                output = stdout.getvalue()
                self.assertIn("✓ rd-skills setup complete", output)
                self.assertIn("Next:", output)
                for phrase in required:
                    self.assertIn(phrase, output)
                if agent in {"cline", "openai-api"}:
                    self.assertNotIn("run the first task", output)
                self.assertNotIn("command plan", output)
                self.assertNotIn("expected standard Skills", output)
                self.assertNotIn("scripts/build.py", output)

    def test_dry_run_and_verbose_show_diagnostic_plan(self) -> None:
        for extra_args in (["--dry-run"], ["--verbose"]):
            with self.subTest(extra_args=extra_args):
                stdout = io.StringIO()
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "quickstart.py",
                            "--agent",
                            "codex",
                            "--scope",
                            "project",
                            "--target",
                            "/tmp/project",
                            *extra_args,
                        ],
                    ),
                    mock.patch.object(self.quickstart, "run_plan", return_value=0),
                    redirect_stdout(stdout),
                ):
                    self.assertEqual(0, self.quickstart.main())

                output = stdout.getvalue()
                self.assertIn("quickstart: command plan", output)
                self.assertIn("python3 scripts/build.py", output)
                self.assertIn("expected standard Skills: 26", output)

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
        self.assertIn("--verbose", help_result.stdout)

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
