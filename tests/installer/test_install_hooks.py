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
            self.assertEqual(len(scripts), 4)
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

    def test_with_hooks_rejected_for_user_scope(self) -> None:
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
                "--dry-run",
            ],
            text=True,
            capture_output=True,
            cwd=str(ROOT),
            env=os.environ.copy(),
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("only supported for codex and claude project", result.stderr)


if __name__ == "__main__":
    unittest.main()
