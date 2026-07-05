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
UNINSTALL_SCRIPT = ROOT / "installers" / "uninstall.py"
DOCTOR_SCRIPT = ROOT / "installers" / "doctor.py"
DIST_CODEX_SKILLS = ROOT / "dist" / "codex" / "project" / ".agents" / "skills" / "recommended"
DIST_CODEX_HOOKS = ROOT / "dist" / "codex" / "project" / ".codex"


def _build_recommended() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build.py"), "--profile", "recommended"],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def _ensure_recommended_dist() -> None:
    if not (DIST_CODEX_SKILLS / ".changeforge-build-manifest.json").is_file() or not (
        DIST_CODEX_HOOKS / ".changeforge-hook-manifest.json"
    ).is_file():
        _build_recommended()


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


def _run_uninstall(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(UNINSTALL_SCRIPT),
            "--agent",
            "codex",
            "--scope",
            "project",
            "--target",
            str(project),
            *extra,
        ],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=os.environ.copy(),
        check=False,
    )


def _run_doctor(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(DOCTOR_SCRIPT),
            "--agent",
            "codex",
            "--scope",
            "project",
            "--target",
            str(project),
            *extra,
        ],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=os.environ.copy(),
        check=False,
    )


def _write_user_codex_hook(project: Path) -> None:
    codex_dir = project / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    (codex_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Shell",
                            "hooks": [{"type": "command", "command": "echo user-hook"}],
                        }
                    ]
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class UninstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_recommended_dist()

    def test_uninstall_removes_managed_skills_and_hooks_preserving_user_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            _write_user_codex_hook(project)
            install = _run_install(project)
            self.assertEqual(install.returncode, 0, install.stderr)

            target_dir = project / ".agents" / "skills"
            manifest = json.loads(
                (target_dir / ".changeforge-install-manifest.json").read_text(encoding="utf-8")
            )
            self.assertIn("change-forge-router", manifest["installed_skills"])
            self.assertTrue((project / ".codex" / "hooks" / "changeforge_session_bootstrap.py").is_file())

            uninstall = _run_uninstall(project)
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertIn("removed 22 ChangeForge-managed skill", uninstall.stdout)
            self.assertIn("hooks: removed ChangeForge-managed hook artifacts", uninstall.stdout)

            self.assertFalse((target_dir / ".changeforge-install-manifest.json").exists())
            self.assertFalse((target_dir / "change-forge-router").exists())
            self.assertFalse((project / ".codex" / ".changeforge-hook-manifest.json").exists())
            hooks_dir = project / ".codex" / "hooks"
            self.assertFalse(any(hooks_dir.glob("changeforge_*.py")) if hooks_dir.exists() else False)
            self.assertFalse((hooks_dir / "validation_broker").exists())

            hooks_json = project / ".codex" / "hooks.json"
            self.assertTrue(hooks_json.is_file())
            rendered = hooks_json.read_text(encoding="utf-8")
            self.assertIn("echo user-hook", rendered)
            self.assertNotIn("changeforge_", rendered)

            doctor = _run_doctor(project, "--check-hooks")
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("doctor: no installation issues detected", doctor.stdout)

    def test_uninstall_dry_run_does_not_remove_managed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            install = _run_install(project)
            self.assertEqual(install.returncode, 0, install.stderr)

            uninstall = _run_uninstall(project, "--dry-run")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertIn("would remove 22 managed skill", uninstall.stdout)
            self.assertIn("hooks: remove file", uninstall.stdout)

            self.assertTrue((project / ".agents" / "skills" / "change-forge-router").is_dir())
            self.assertTrue((project / ".codex" / ".changeforge-hook-manifest.json").is_file())
            self.assertTrue((project / ".codex" / "hooks" / "changeforge_session_bootstrap.py").is_file())

    def test_keep_hooks_removes_skills_but_leaves_hook_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            install = _run_install(project)
            self.assertEqual(install.returncode, 0, install.stderr)

            uninstall = _run_uninstall(project, "--keep-hooks")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertIn("hooks: kept because --keep-hooks", uninstall.stdout)

            self.assertFalse((project / ".agents" / "skills" / "change-forge-router").exists())
            self.assertTrue((project / ".codex" / ".changeforge-hook-manifest.json").is_file())
            self.assertTrue((project / ".codex" / "hooks" / "changeforge_session_bootstrap.py").is_file())

    def test_uninstall_removes_standalone_bootstrap_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            install = _run_install(project, "--with-bootstrap", "--without-hooks")
            self.assertEqual(install.returncode, 0, install.stderr)
            fragment = project / ".changeforge" / "changeforge-route-preflight.md"
            self.assertTrue(fragment.is_file())

            uninstall = _run_uninstall(project)
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertIn("bootstrap: removed standalone ChangeForge bootstrap fragments", uninstall.stdout)
            self.assertFalse(fragment.exists())
            self.assertFalse((project / ".changeforge").exists())


if __name__ == "__main__":
    unittest.main()
