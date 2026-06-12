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
