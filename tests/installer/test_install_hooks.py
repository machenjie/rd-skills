from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALL_SCRIPT = ROOT / "installers" / "install.py"
DIST_CODEX_HOOKS = ROOT / "dist" / "codex" / "project" / ".codex"
DIST_COPILOT_HOOK_SUPPORT = (
    ROOT
    / "dist"
    / "copilot"
    / "project"
    / ".github"
    / "hooks"
    / "changeforge"
    / "changeforge_copilot_skill_summary.md"
)


def _build_recommended() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build.py"), "--profile", "recommended"],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def _run_install(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(INSTALL_SCRIPT),
            "--agent",
            "codex",
            "--scope",
            "project",
            "--target",
            str(project),
            "--profile",
            "recommended",
            *extra,
        ],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=os.environ.copy(),
        check=False,
    )


class InstallHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (DIST_CODEX_HOOKS / "hooks.json").is_file():
            _build_recommended()

    def test_hooks_dry_run_writes_no_hook_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-hooks", "--hooks-dry-run")
            codex_dir = project / ".codex"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hooks: dry run", result.stdout)
            self.assertFalse((codex_dir / "hooks").exists())

    def test_with_hooks_installs_scripts_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-hooks")
            codex_dir = project / ".codex"
            scripts = sorted((codex_dir / "hooks").glob("changeforge_*.py"))
            manifest = codex_dir / ".changeforge-hook-manifest.json"
            hooks_json = codex_dir / "hooks.json"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(scripts), 8)
            self.assertTrue((codex_dir / "hooks" / "changeforge_session_bootstrap.py").is_file())
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_user_prompt_route_reminder.py").is_file()
            )
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_pre_tool_risk_preview.py").is_file()
            )
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_subagent_stop_reminder.py").is_file()
            )
            self.assertTrue((codex_dir / "changeforge-route-preflight.md").is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(hooks_json.is_file())

    def test_merge_preserves_existing_user_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            codex_dir = project / ".codex"
            codex_dir.mkdir(parents=True)
            (codex_dir / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PostToolUse": [
                                {
                                    "matcher": "Edit",
                                    "hooks": [{"type": "command", "command": "echo user-hook"}],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            result = _run_install(project, "--with-hooks")
            merged = json.loads((codex_dir / "hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = json.dumps(merged)
            self.assertIn("echo user-hook", commands)
            self.assertIn("changeforge_post_edit_structure_gate", commands)

    def test_with_hooks_user_scope_installs_to_home(self) -> None:
        # User-scope hooks install under the agent home (~/.codex), sandboxed
        # here by pointing HOME at a temp dir. --target is not required.
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env.pop("CODEX_HOME", None)
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "codex",
                    "--scope",
                    "user",
                    "--profile",
                    "recommended",
                    "--with-hooks",
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            codex_dir = Path(home) / ".codex"
            scripts = sorted((codex_dir / "hooks").glob("changeforge_*.py"))
            self.assertEqual(len(scripts), 8)
            self.assertTrue((codex_dir / "hooks.json").is_file())
            manifest = json.loads(
                (codex_dir / ".changeforge-hook-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["scope"], "user")
            self.assertEqual(manifest["agent"], "codex")


class InstallCopilotHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (DIST_CODEX_HOOKS / "hooks.json").is_file() or not DIST_COPILOT_HOOK_SUPPORT.is_file():
            _build_recommended()

    def test_copilot_project_hooks_install_to_github(self) -> None:
        # VS Code Copilot project hooks: config at .github/hooks/changeforge-hooks.json,
        # scripts nested in .github/hooks/changeforge/.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "copilot",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
                    "--profile",
                    "recommended",
                    "--with-hooks",
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            hooks_dir = project / ".github" / "hooks"
            config = hooks_dir / "changeforge-hooks.json"
            scripts_dir = hooks_dir / "changeforge"
            self.assertTrue(config.is_file())
            scripts = sorted(scripts_dir.glob("changeforge_*.py"))
            self.assertEqual(len(scripts), 8)
            self.assertTrue((scripts_dir / "changeforge_copilot_skill_summary.md").is_file())
            self.assertTrue((scripts_dir / ".changeforge-hook-manifest.json").is_file())
            manifest = json.loads(
                (scripts_dir / ".changeforge-hook-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["support_files"], ["changeforge_copilot_skill_summary.md"])
            # The manifest is nested so VS Code does not parse it as a hook config.
            self.assertFalse((hooks_dir / ".changeforge-hook-manifest.json").exists())
            payload = json.loads(config.read_text(encoding="utf-8"))
            self.assertIn("PostToolUse", payload["hooks"])

    def test_copilot_project_preserves_existing_hook_json(self) -> None:
        # Installing the managed config must not touch a user's own hook JSON in
        # the same .github/hooks folder.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            hooks_dir = project / ".github" / "hooks"
            hooks_dir.mkdir(parents=True)
            user_hook = hooks_dir / "my-format.json"
            user_hook.write_text(
                json.dumps({"hooks": {"PostToolUse": [{"type": "command", "command": "echo mine"}]}}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "copilot",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
                    "--profile",
                    "recommended",
                    "--with-hooks",
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # The user's own hook file is untouched.
            self.assertIn("echo mine", user_hook.read_text(encoding="utf-8"))
            self.assertTrue((hooks_dir / "changeforge-hooks.json").is_file())

    def test_copilot_user_hooks_install_to_home(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "copilot",
                    "--scope",
                    "user",
                    "--profile",
                    "recommended",
                    "--with-hooks",
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            hooks_dir = Path(home) / ".copilot" / "hooks"
            self.assertTrue((hooks_dir / "changeforge-hooks.json").is_file())
            scripts = sorted((hooks_dir / "changeforge").glob("changeforge_*.py"))
            self.assertEqual(len(scripts), 8)
            self.assertTrue(
                (hooks_dir / "changeforge" / "changeforge_copilot_skill_summary.md").is_file()
            )
            manifest = json.loads(
                (hooks_dir / "changeforge" / ".changeforge-hook-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["scope"], "user")
            self.assertEqual(manifest["agent"], "copilot")
            self.assertEqual(manifest["support_files"], ["changeforge_copilot_skill_summary.md"])


class InstallBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (DIST_CODEX_HOOKS / "hooks.json").is_file():
            _build_recommended()

    def test_bootstrap_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-bootstrap", "--bootstrap-dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("bootstrap: dry run", result.stdout)
            self.assertFalse((project / ".changeforge").exists())

    def test_with_bootstrap_installs_advisory_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-bootstrap")
            fragment = project / ".changeforge" / "changeforge-route-preflight.md"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(fragment.is_file())
            self.assertIn("change-forge-router", fragment.read_text(encoding="utf-8"))

    def test_with_bootstrap_does_not_install_hook_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-bootstrap")
            self.assertEqual(result.returncode, 0, result.stderr)
            # The advisory fragment must never pull in executable hook scripts.
            self.assertFalse((project / ".codex" / "hooks").exists())


if __name__ == "__main__":
    unittest.main()
