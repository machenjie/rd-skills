from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from installers import changeforge_install


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
SOURCE_HOOK_SCRIPTS = ROOT / "src" / "hook-runtime" / "scripts"
EXPECTED_HOOK_SCRIPT_COUNT = len(tuple(SOURCE_HOOK_SCRIPTS.glob("changeforge_*.py")))
RUNTIME_ROUTE_RESOLVER_NAME = "changeforge_runtime_route_resolver.py"
RUNTIME_ROUTE_INDEX_NAME = "changeforge_runtime_route_index.json"
EXPECTED_COMMON_SUPPORT_FILES = [
    "changeforge_professional_contract.md",
    RUNTIME_ROUTE_INDEX_NAME,
]
EXPECTED_COPILOT_SUPPORT_FILES = sorted(
    [
        *EXPECTED_COMMON_SUPPORT_FILES,
        "changeforge_copilot_professional_contract.md",
        "changeforge_copilot_skill_summary.md",
    ]
)
EXPECTED_SUPPORT_PACKAGES = [
    "validation_broker",
    "runtime_governance",
    "repository_intelligence",
    "project_memory",
]


def _build_recommended() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build.py"), "--profile", "recommended"],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def _built_manifest_has_support_packages(path: Path) -> bool:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    return manifest.get("support_packages") == EXPECTED_SUPPORT_PACKAGES


def _built_hook_scripts_complete(hooks_dir: Path) -> bool:
    return len(tuple(hooks_dir.glob("changeforge_*.py"))) == EXPECTED_HOOK_SCRIPT_COUNT


def _built_repository_intelligence_subset_complete(hooks_dir: Path) -> bool:
    return (
        hooks_dir / "repository_intelligence" / "graph" / "file_classifier.py"
    ).is_file()


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


def _assert_action_classifier_smoke(test_case: unittest.TestCase, scripts_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "changeforge_action_classifier.py")],
        text=True,
        capture_output=True,
        cwd=str(scripts_dir.parent),
        env=os.environ.copy(),
        check=False,
    )
    test_case.assertEqual(result.returncode, 0, result.stderr)


def _assert_hook_support_import_smoke(test_case: unittest.TestCase, hooks_dir: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import validation_broker;"
                "import runtime_governance;"
                "import project_memory.hook_safe.adapter;"
                "import repository_intelligence.cache.repo_hash"
            ),
        ],
        text=True,
        capture_output=True,
        cwd=str(hooks_dir),
        env=os.environ.copy(),
        check=False,
    )
    test_case.assertEqual(result.returncode, 0, result.stderr)


class InstallHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (DIST_CODEX_HOOKS / "hooks.json").is_file() or not (
            DIST_CODEX_HOOKS / "hooks" / RUNTIME_ROUTE_INDEX_NAME
        ).is_file() or not (
            DIST_CODEX_HOOKS / "hooks" / "changeforge_sdd_material_choice_gate.py"
        ).is_file() or not _built_manifest_has_support_packages(
            DIST_CODEX_HOOKS / ".changeforge-hook-manifest.json"
        ) or not _built_hook_scripts_complete(
            DIST_CODEX_HOOKS / "hooks"
        ) or not _built_repository_intelligence_subset_complete(
            DIST_CODEX_HOOKS / "hooks"
        ):
            _build_recommended()

    def test_hooks_dry_run_writes_no_hook_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-hooks", "--hooks-dry-run")
            codex_dir = project / ".codex"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hooks: decision install", result.stdout)
            self.assertIn("hooks: dry run", result.stdout)
            self.assertFalse((codex_dir / "hooks").exists())

    def test_codex_project_install_defaults_to_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project)
            codex_dir = project / ".codex"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hooks: decision install (default; professional-injection)", result.stdout)
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_sdd_material_choice_gate.py").is_file()
            )
            self.assertTrue((codex_dir / "hooks.json").is_file())

    def test_with_hooks_installs_scripts_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-hooks")
            codex_dir = project / ".codex"
            scripts = sorted((codex_dir / "hooks").glob("changeforge_*.py"))
            manifest = codex_dir / ".changeforge-hook-manifest.json"
            hooks_json = codex_dir / "hooks.json"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(scripts), EXPECTED_HOOK_SCRIPT_COUNT)
            self.assertTrue((codex_dir / "hooks" / "changeforge_session_bootstrap.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "changeforge_professional_injector.py").is_file())
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_user_prompt_route_reminder.py").is_file()
            )
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_pre_tool_risk_preview.py").is_file()
            )
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_sdd_material_choice_gate.py").is_file()
            )
            self.assertTrue((codex_dir / "hooks" / "changeforge_process_phase_gate.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "changeforge_subagent_review_gate.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "changeforge_context_control_policy.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "changeforge_compaction_contract.py").is_file())
            self.assertTrue((codex_dir / "hooks" / RUNTIME_ROUTE_RESOLVER_NAME).is_file())
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_subagent_stop_reminder.py").is_file()
            )
            self.assertTrue((codex_dir / "changeforge-route-preflight.md").is_file())
            self.assertTrue((codex_dir / "hooks" / "changeforge_professional_contract.md").is_file())
            self.assertTrue((codex_dir / "hooks" / RUNTIME_ROUTE_INDEX_NAME).is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(hooks_json.is_file())
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(set(manifest_data["hooks"]), {path.stem for path in scripts})
            _assert_action_classifier_smoke(self, codex_dir / "hooks")
            _assert_hook_support_import_smoke(self, codex_dir / "hooks")

    def test_hook_plan_discovers_new_built_script(self) -> None:
        # Regression: installer script planning must not miss hook files added after a static allowlist.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_root = tmp_path / "built" / ".codex"
            scripts_root = source_root / "hooks"
            scripts_root.mkdir(parents=True)
            for script_name in ("changeforge_existing.py", "changeforge_new_runtime_gate.py"):
                (scripts_root / script_name).write_text(
                    "#!/usr/bin/env python3\nprint('ok')\n",
                    encoding="utf-8",
                )
            (source_root / "hooks.json").write_text(json.dumps({"hooks": {}}), encoding="utf-8")
            (source_root / ".changeforge-hook-manifest.json").write_text(
                json.dumps({"support_files": [], "support_packages": []}),
                encoding="utf-8",
            )
            original_source = changeforge_install.HOOK_SOURCE_ROOTS[("codex", "project")]
            changeforge_install.HOOK_SOURCE_ROOTS[("codex", "project")] = source_root
            try:
                plan = changeforge_install.plan_hook_install(
                    "codex",
                    "project",
                    tmp_path / "project",
                )
                planned = {destination.name for _source, destination, _action in plan.script_actions}
                self.assertEqual(
                    planned,
                    {"changeforge_existing.py", "changeforge_new_runtime_gate.py"},
                )
                changeforge_install.apply_hook_install(plan, dry_run=False)
                installed = tmp_path / "project" / ".codex" / "hooks"
                self.assertTrue((installed / "changeforge_existing.py").is_file())
                self.assertTrue((installed / "changeforge_new_runtime_gate.py").is_file())
            finally:
                changeforge_install.HOOK_SOURCE_ROOTS[("codex", "project")] = original_source

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

    def test_codex_user_scope_installs_hooks_by_default(self) -> None:
        # User-scope hooks install under the agent home (~/.codex), sandboxed
        # here by pointing HOME at a temp dir. --target and --with-hooks are not required.
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
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hooks: decision install (default; professional-injection)", result.stdout)
            codex_dir = Path(home) / ".codex"
            scripts = sorted((codex_dir / "hooks").glob("changeforge_*.py"))
            self.assertEqual(len(scripts), EXPECTED_HOOK_SCRIPT_COUNT)
            self.assertTrue(
                (codex_dir / "hooks" / "changeforge_sdd_material_choice_gate.py").is_file()
            )
            self.assertTrue((codex_dir / "hooks" / RUNTIME_ROUTE_RESOLVER_NAME).is_file())
            self.assertTrue((codex_dir / "hooks.json").is_file())
            manifest = json.loads(
                (codex_dir / ".changeforge-hook-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["scope"], "user")
            self.assertEqual(manifest["agent"], "codex")
            self.assertEqual(manifest["support_files"], EXPECTED_COMMON_SUPPORT_FILES)
            self.assertEqual(manifest["support_packages"], EXPECTED_SUPPORT_PACKAGES)
            self.assertTrue((codex_dir / "hooks" / "validation_broker" / "__init__.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "runtime_governance" / "__init__.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "repository_intelligence" / "__init__.py").is_file())
            self.assertTrue((codex_dir / "hooks" / "project_memory" / "__init__.py").is_file())
            self.assertTrue(
                (codex_dir / "hooks" / "project_memory" / "hook_safe" / "adapter.py").is_file()
            )
            _assert_hook_support_import_smoke(self, codex_dir / "hooks")

    def test_without_hooks_skips_hook_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--without-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hooks: decision skip (skipped because --without-hooks was requested)", result.stdout)
            self.assertFalse((project / ".codex" / "hooks").exists())

    def test_with_hooks_and_without_hooks_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_install(Path(tmp), "--with-hooks", "--without-hooks")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot be combined", result.stderr)

    def test_professional_injection_and_without_hooks_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_install(Path(tmp), "--professional-injection", "--without-hooks")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot be combined", result.stderr)

    def test_unsupported_agent_default_skips_hooks_without_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "cline",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
                    "--profile",
                    "recommended",
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hooks unsupported for cline project", result.stdout)

    def test_unsupported_agent_explicit_hooks_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "cline",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only supported for codex, claude, and copilot", result.stderr)

    def test_unsupported_agent_explicit_professional_injection_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "cline",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
                    "--profile",
                    "recommended",
                    "--professional-injection",
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only supported for codex, claude, and copilot", result.stderr)

    def test_unsupported_scope_default_skips_hooks_without_error(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--agent",
                "codex",
                "--scope",
                "admin",
                "--profile",
                "recommended",
                "--dry-run",
            ],
            text=True,
            capture_output=True,
            cwd=str(ROOT),
            env=os.environ.copy(),
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hooks unsupported for codex admin", result.stdout)

    def test_unsupported_scope_explicit_hooks_errors(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--agent",
                "codex",
                "--scope",
                "admin",
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
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only supported for codex, claude, and copilot", result.stderr)

    def test_hook_support_package_manifest_rejects_path_like_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / ".changeforge-hook-manifest.json"
            manifest.write_text(json.dumps({"support_packages": [".."]}), encoding="utf-8")
            packages = changeforge_install._hook_support_packages_from_manifest(manifest)
        self.assertEqual(packages, tuple(EXPECTED_SUPPORT_PACKAGES))

    def test_cline_skill_install_layout_is_skills_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.assertEqual(
                changeforge_install.resolve_target_dir("cline", "project", project),
                project.resolve() / ".cline" / "skills",
            )
        self.assertEqual(changeforge_install.supported_scopes("cline"), ("project", "user"))
        self.assertFalse(changeforge_install.hooks_supported("cline", "project"))


class InstallCopilotHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        copilot_index = (
            DIST_COPILOT_HOOK_SUPPORT.parent / RUNTIME_ROUTE_INDEX_NAME
        )
        if (
            not (DIST_CODEX_HOOKS / "hooks.json").is_file()
            or not DIST_COPILOT_HOOK_SUPPORT.is_file()
            or not copilot_index.is_file()
            or not (DIST_COPILOT_HOOK_SUPPORT.parent / "changeforge_sdd_material_choice_gate.py").is_file()
            or not _built_manifest_has_support_packages(
                DIST_COPILOT_HOOK_SUPPORT.parent / ".changeforge-hook-manifest.json"
            )
            or not _built_hook_scripts_complete(DIST_COPILOT_HOOK_SUPPORT.parent)
            or not _built_repository_intelligence_subset_complete(DIST_COPILOT_HOOK_SUPPORT.parent)
        ):
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
            self.assertEqual(len(scripts), EXPECTED_HOOK_SCRIPT_COUNT)
            self.assertTrue((scripts_dir / RUNTIME_ROUTE_RESOLVER_NAME).is_file())
            self.assertTrue((scripts_dir / "changeforge_professional_contract.md").is_file())
            self.assertTrue((scripts_dir / RUNTIME_ROUTE_INDEX_NAME).is_file())
            self.assertTrue((scripts_dir / "changeforge_copilot_skill_summary.md").is_file())
            self.assertTrue(
                (scripts_dir / "changeforge_copilot_professional_contract.md").is_file()
            )
            self.assertTrue((scripts_dir / ".changeforge-hook-manifest.json").is_file())
            manifest = json.loads(
                (scripts_dir / ".changeforge-hook-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                set(manifest["hooks"]),
                {path.stem for path in scripts},
            )
            self.assertEqual(sorted(manifest["support_files"]), EXPECTED_COPILOT_SUPPORT_FILES)
            self.assertEqual(manifest["support_packages"], EXPECTED_SUPPORT_PACKAGES)
            self.assertTrue((scripts_dir / "validation_broker" / "__init__.py").is_file())
            self.assertTrue((scripts_dir / "runtime_governance" / "__init__.py").is_file())
            self.assertTrue((scripts_dir / "repository_intelligence" / "__init__.py").is_file())
            self.assertTrue((scripts_dir / "project_memory" / "__init__.py").is_file())
            self.assertTrue((scripts_dir / "project_memory" / "hook_safe" / "adapter.py").is_file())
            _assert_hook_support_import_smoke(self, scripts_dir)
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
            self.assertEqual(len(scripts), EXPECTED_HOOK_SCRIPT_COUNT)
            self.assertTrue(
                (hooks_dir / "changeforge" / RUNTIME_ROUTE_RESOLVER_NAME).is_file()
            )
            self.assertTrue(
                (hooks_dir / "changeforge" / "changeforge_professional_contract.md").is_file()
            )
            self.assertTrue((hooks_dir / "changeforge" / RUNTIME_ROUTE_INDEX_NAME).is_file())
            self.assertTrue(
                (hooks_dir / "changeforge" / "changeforge_copilot_skill_summary.md").is_file()
            )
            self.assertTrue(
                (
                    hooks_dir
                    / "changeforge"
                    / "changeforge_copilot_professional_contract.md"
                ).is_file()
            )
            manifest = json.loads(
                (hooks_dir / "changeforge" / ".changeforge-hook-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["scope"], "user")
            self.assertEqual(manifest["agent"], "copilot")
            self.assertEqual(sorted(manifest["support_files"]), EXPECTED_COPILOT_SUPPORT_FILES)
            self.assertEqual(manifest["support_packages"], EXPECTED_SUPPORT_PACKAGES)
            self.assertTrue(
                (hooks_dir / "changeforge" / "validation_broker" / "__init__.py").is_file()
            )
            self.assertTrue(
                (hooks_dir / "changeforge" / "runtime_governance" / "__init__.py").is_file()
            )
            self.assertTrue(
                (hooks_dir / "changeforge" / "repository_intelligence" / "__init__.py").is_file()
            )
            self.assertTrue(
                (hooks_dir / "changeforge" / "project_memory" / "__init__.py").is_file()
            )
            self.assertTrue(
                (hooks_dir / "changeforge" / "project_memory" / "hook_safe" / "adapter.py").is_file()
            )
            _assert_hook_support_import_smoke(self, hooks_dir / "changeforge")


class InstallClaudeHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        claude_hooks = ROOT / "dist" / "claude" / "project" / ".claude" / "hooks"
        if not (claude_hooks / RUNTIME_ROUTE_INDEX_NAME).is_file() or not (
            claude_hooks / "changeforge_sdd_material_choice_gate.py"
        ).is_file() or not (
            ROOT / "dist" / "claude" / "project" / ".claude" / ".changeforge-hook-manifest.json"
        ).is_file() or not _built_hook_scripts_complete(
            claude_hooks
        ) or not _built_repository_intelligence_subset_complete(claude_hooks):
            _build_recommended()

    def test_claude_project_hook_support_packages_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "claude",
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
            _assert_hook_support_import_smoke(self, project / ".claude" / "hooks")

    def test_claude_user_hook_support_packages_import(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_SCRIPT),
                    "--agent",
                    "claude",
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
            _assert_hook_support_import_smoke(self, Path(home) / ".claude" / "hooks")


class InstallBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (DIST_CODEX_HOOKS / "hooks.json").is_file() or not (
            DIST_CODEX_HOOKS / "hooks" / "changeforge_sdd_material_choice_gate.py"
        ).is_file():
            _build_recommended()

    def test_bootstrap_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-bootstrap", "--without-hooks", "--bootstrap-dry-run")
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
            result = _run_install(project, "--with-bootstrap", "--without-hooks")
            self.assertEqual(result.returncode, 0, result.stderr)
            # The advisory fragment must never pull in executable hook scripts.
            self.assertFalse((project / ".codex" / "hooks").exists())

    def test_with_universal_bootstrap_installs_professional_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = _run_install(project, "--with-universal-bootstrap")
            professional = project / ".changeforge" / "changeforge-professional-contract.md"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(professional.is_file())
            self.assertIn("owner skill", professional.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
