from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT


def load_install_helper():
    name = "changeforge_install_safety_tests"
    spec = importlib.util.spec_from_file_location(
        name,
        ROOT / "installers" / "changeforge_install.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_cli(helper, script: str):
    name = f"changeforge_{script}_cli_safety_tests"
    spec = importlib.util.spec_from_file_location(
        name,
        ROOT / "installers" / f"{script}.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"changeforge_install": helper}):
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


class HooklessInstallerSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._original_dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        cls.addClassCleanup(
            setattr,
            sys,
            "dont_write_bytecode",
            cls._original_dont_write_bytecode,
        )
        cls.helper = load_install_helper()
        cls.install_cli = load_cli(cls.helper, "install")
        cls.upgrade_cli = load_cli(cls.helper, "upgrade")
        cls.doctor_cli = load_cli(cls.helper, "doctor")
        cls.uninstall_cli = load_cli(cls.helper, "uninstall")
        cls._source_skill_relatives = {
            key: path.relative_to(cls.helper.ROOT)
            for key, path in cls.helper.SOURCE_SKILL_ROOTS.items()
        }
        cls._source_profile_relatives = {
            key: path.relative_to(cls.helper.ROOT)
            for key, path in cls.helper.SOURCE_PROFILE_ROOTS.items()
        }
        cls._runtime_build = cls._temporary_recommended_build()
        cls.runtime_root = cls._runtime_build.__enter__()
        cls.addClassCleanup(cls._runtime_build.__exit__, None, None, None)

    def test_installer_has_one_runtime_and_bounded_legacy_input_counts(self) -> None:
        self.assertEqual("recommended", self.helper.RUNTIME_PROFILE)
        self.assertEqual(26, self.helper.RUNTIME_SKILL_COUNT)
        self.assertEqual(
            {"recommended": 26, "full": 39, "dev": 189},
            self.helper.LEGACY_PROFILE_COUNTS,
        )
        self.assertFalse(hasattr(self.helper, "PROFILES"))

    def test_public_installer_help_and_obsolete_profile_rejection_are_profile_free(self) -> None:
        for script in ("install", "upgrade", "doctor"):
            with self.subTest(script=script):
                help_result = subprocess.run(
                    [sys.executable, str(ROOT / "installers" / f"{script}.py"), "--help"],
                    cwd=ROOT,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, help_result.returncode, help_result.stderr)
                self.assertNotIn("--profile", help_result.stdout)
                with tempfile.TemporaryDirectory() as raw:
                    project = Path(raw) / "project"
                    before = self._tree_snapshot(Path(raw))
                    obsolete = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "installers" / f"{script}.py"),
                            "--agent",
                            "codex",
                            "--scope",
                            "project",
                            "--target",
                            str(project),
                            "--profile",
                            "full",
                        ],
                        cwd=ROOT,
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(2, obsolete.returncode)
                    self.assertIn("unrecognized arguments: --profile full", obsolete.stderr)
                    self.assertEqual(before, self._tree_snapshot(Path(raw)))

    @staticmethod
    def _authoritative_layer_names() -> dict[str, set[str]]:
        from tests.scripts.test_build_safety import BUILD

        registries = BUILD._load_registries()
        return {
            layer: {str(entry["name"]) for entry in entries}
            for layer, entries in registries.items()
        }

    def _install_current_project(self, project: Path) -> tuple[Path, Path]:
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "install.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
                ],
            ),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(0, self.install_cli.main())
        return project / ".agents/skills", project / ".codex/agents"

    def _make_legacy_install(self, project: Path, profile: str) -> tuple[Path, Path, dict]:
        skills, profiles = self._install_current_project(project)
        layers = self._authoritative_layer_names()
        expected = {
            "recommended": layers["control"] | layers["professional"],
            "full": layers["control"] | layers["professional"] | layers["domain"],
            "dev": set().union(*layers.values()),
        }[profile]
        for name in sorted(expected):
            skill = skills / name
            if not skill.exists():
                skill.mkdir()
                (skill / "SKILL.md").write_text(f"# legacy {name}\n", encoding="utf-8")
        manifest_path = skills / self.helper.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(
            {
                "profile": profile,
                "installed_skills": sorted(expected),
                "installed_control_skills": sorted(layers["control"]),
                "installed_professional_skills": sorted(layers["professional"]),
                "installed_foundation_skills": (
                    sorted(layers["foundation"]) if profile == "dev" else []
                ),
                "installed_domain_skills": (
                    sorted(layers["domain"]) if profile in {"full", "dev"} else []
                ),
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return skills, profiles, manifest

    def test_full_and_dev_upgrade_migrate_with_backup_preservation_and_idempotence(self) -> None:
        layers = self._authoritative_layer_names()
        runtime = layers["control"] | layers["professional"]
        for profile in ("full", "dev"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                skills, profiles, legacy_manifest = self._make_legacy_install(project, profile)
                retired = set(legacy_manifest["installed_skills"]) - runtime
                self.assertTrue(retired)
                mixed_name = sorted(retired)[0]
                mixed_bytes = b"user-owned bytes inside managed legacy Skill\n"
                (skills / mixed_name / "user-note.bin").write_bytes(mixed_bytes)
                root_bytes = b"unmanaged root file\n"
                (skills / "USER-NOTES.txt").write_bytes(root_bytes)
                sibling_bytes = b"# user Skill\n"
                user_skill = skills / "user-owned-skill"
                user_skill.mkdir()
                (user_skill / "SKILL.md").write_bytes(sibling_bytes)
                profile_bytes = b'user owned = true\n'
                (profiles / "user-owned.toml").write_bytes(profile_bytes)

                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "upgrade.py",
                            "--agent",
                            "codex",
                            "--scope",
                            "project",
                            "--target",
                            str(project),
                        ],
                    ),
                    mock.patch.object(
                        self.helper,
                        "utc_stamp",
                        side_effect=("first", "second"),
                    ),
                    redirect_stdout(io.StringIO()),
                    redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(0, self.upgrade_cli.main())
                    installed = json.loads(
                        (skills / self.helper.MANIFEST_NAME).read_text(encoding="utf-8")
                    )
                    self.assertEqual("recommended", installed["profile"])
                    self.assertEqual(runtime, set(installed["installed_skills"]))
                    self.assertEqual(26, len(installed["installed_skills"]))
                    self.assertEqual(4, len(installed["installed_agent_profiles"]))
                    backup = Path(installed["backup_path"])
                    self.assertEqual(
                        mixed_bytes,
                        (backup / "skills" / mixed_name / "user-note.bin").read_bytes(),
                    )
                    self.assertTrue(all(not (skills / name).exists() for name in retired))
                    self.assertEqual(root_bytes, (skills / "USER-NOTES.txt").read_bytes())
                    self.assertEqual(sibling_bytes, (user_skill / "SKILL.md").read_bytes())
                    self.assertEqual(profile_bytes, (profiles / "user-owned.toml").read_bytes())

                    self.assertEqual(0, self.upgrade_cli.main())
                    second = json.loads(
                        (skills / self.helper.MANIFEST_NAME).read_text(encoding="utf-8")
                    )
                    self.assertEqual(runtime, set(second["installed_skills"]))
                    self.assertEqual(root_bytes, (skills / "USER-NOTES.txt").read_bytes())
                    self.assertEqual(sibling_bytes, (user_skill / "SKILL.md").read_bytes())
                    self.assertEqual(profile_bytes, (profiles / "user-owned.toml").read_bytes())

    def test_safe_but_forged_or_duplicate_legacy_inventory_fails_before_mutation_even_with_force(self) -> None:
        for scenario in ("safe-forged", "duplicate"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                skills, _profiles, _manifest = self._make_legacy_install(project, "full")
                manifest_path = skills / self.helper.MANIFEST_NAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if scenario == "safe-forged":
                    removed = manifest["installed_skills"].pop()
                    manifest["installed_skills"].append("safe-forged-skill")
                    forged = skills / "safe-forged-skill"
                    forged.mkdir()
                    (forged / "SKILL.md").write_text("# forged\n", encoding="utf-8")
                    self.assertTrue((skills / removed).is_dir())
                else:
                    manifest["installed_skills"].append(manifest["installed_skills"][0])
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                before = self._tree_snapshot(project)
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "upgrade.py",
                            "--agent",
                            "codex",
                            "--scope",
                            "project",
                            "--target",
                            str(project),
                            "--force",
                        ],
                    ),
                    redirect_stdout(io.StringIO()),
                    redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(1, self.upgrade_cli.main())
                self.assertEqual(before, self._tree_snapshot(project))

    def test_doctor_reports_valid_retired_install_as_migration_required_without_build_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            self._make_legacy_install(project, "dev")
            output = io.StringIO()
            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "doctor.py",
                        "--agent",
                        "codex",
                        "--scope",
                        "project",
                        "--target",
                        str(project),
                    ],
                ),
                mock.patch.object(
                    self.doctor_cli,
                    "validated_built_core_model",
                    side_effect=AssertionError("retired build lookup is forbidden"),
                ) as resolve_source,
                redirect_stdout(output),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, self.doctor_cli.main())
            resolve_source.assert_not_called()
            self.assertIn("migration required", output.getvalue().lower())

    def test_legacy_dry_run_is_zero_mutation_and_uninstall_accepts_exact_legacy_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            skills, profiles, legacy = self._make_legacy_install(project, "full")
            root_file = skills / "USER-NOTES.txt"
            root_file.write_bytes(b"preserve root\n")
            user_skill = skills / "user-owned-skill"
            user_skill.mkdir()
            (user_skill / "SKILL.md").write_bytes(b"# preserve Skill\n")
            user_profile = profiles / "user-owned.toml"
            user_profile.write_bytes(b"preserve = true\n")
            before = self._tree_snapshot(project)

            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "upgrade.py",
                        "--agent",
                        "codex",
                        "--scope",
                        "project",
                        "--target",
                        str(project),
                        "--dry-run",
                    ],
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, self.upgrade_cli.main())
            self.assertEqual(before, self._tree_snapshot(project))

            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "uninstall.py",
                        "--agent",
                        "codex",
                        "--scope",
                        "project",
                        "--target",
                        str(project),
                    ],
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, self.uninstall_cli.main())
            self.assertFalse((skills / self.helper.MANIFEST_NAME).exists())
            self.assertTrue(
                all(not (skills / name).exists() for name in legacy["installed_skills"])
            )
            self.assertEqual(b"preserve root\n", root_file.read_bytes())
            self.assertEqual(b"# preserve Skill\n", (user_skill / "SKILL.md").read_bytes())
            self.assertEqual(b"preserve = true\n", user_profile.read_bytes())

    def test_legacy_manifest_identity_and_nested_symlink_fail_before_mutation_even_with_force(self) -> None:
        for scenario in ("architecture", "agent", "scope", "target", "nested-symlink"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                skills, _profiles, legacy = self._make_legacy_install(project, "dev")
                manifest_path = skills / self.helper.MANIFEST_NAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                outside = Path(raw) / "outside.bin"
                outside.write_bytes(b"outside must remain\n")
                if scenario == "architecture":
                    manifest["architecture"] = "safe-but-unknown-architecture"
                elif scenario == "agent":
                    manifest["agent"] = "claude"
                elif scenario == "scope":
                    manifest["scope"] = "user"
                elif scenario == "target":
                    manifest["target_path"] = str(Path(raw) / "safe-other-target")
                else:
                    runtime = self._authoritative_layer_names()["control"] | self._authoritative_layer_names()["professional"]
                    retired = sorted(set(legacy["installed_skills"]) - runtime)[0]
                    (skills / retired / "outside-link").symlink_to(outside)
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                before = self._tree_snapshot(project)
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "upgrade.py",
                            "--agent",
                            "codex",
                            "--scope",
                            "project",
                            "--target",
                            str(project),
                            "--force",
                        ],
                    ),
                    redirect_stdout(io.StringIO()),
                    redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(1, self.upgrade_cli.main())
                self.assertEqual(before, self._tree_snapshot(project))
                self.assertEqual(b"outside must remain\n", outside.read_bytes())

    def test_upgrade_backup_failure_and_unmanaged_conflict_are_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            self._make_legacy_install(project, "full")
            before = self._tree_snapshot(project)
            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "upgrade.py",
                        "--agent",
                        "codex",
                        "--scope",
                        "project",
                        "--target",
                        str(project),
                    ],
                ),
                mock.patch.object(
                    self.helper.shutil,
                    "copytree",
                    side_effect=OSError("synthetic backup failure"),
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, self.upgrade_cli.main())
            self.assertEqual(before, self._tree_snapshot(project))

        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            conflict = project / ".agents/skills/engineering-control-plane"
            conflict.mkdir(parents=True)
            (conflict / "SKILL.md").write_bytes(b"# user conflict\n")
            before = self._tree_snapshot(project)
            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "install.py",
                        "--agent",
                        "codex",
                        "--scope",
                        "project",
                        "--target",
                        str(project),
                    ],
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, self.install_cli.main())
            self.assertEqual(before, self._tree_snapshot(project))

    def test_cline_runtime_manifest_has_26_skills_and_no_agent_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "install.py",
                        "--agent",
                        "cline",
                        "--scope",
                        "project",
                        "--target",
                        str(project),
                    ],
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, self.install_cli.main())
            manifest = json.loads(
                (
                    project
                    / ".cline/skills"
                    / self.helper.MANIFEST_NAME
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("recommended", manifest["profile"])
            self.assertEqual(26, len(manifest["installed_skills"]))
            self.assertEqual([], manifest["installed_agent_profiles"])
            self.assertEqual([], manifest["installed_agent_profile_files"])

    def test_capability_fact_projection_reuses_canonical_build_renderer(self) -> None:
        from tests.scripts.test_build_safety import BUILD as build

        enforcement = self.helper.host_enforcement_for_agent("codex")
        expected = build._render_decision_capability_facts(
            build._normalized_decision_capabilities(enforcement)
        )
        self.assertEqual(
            expected,
            self.helper.canonical_profile_capability_facts(enforcement),
        )

    def test_install_and_upgrade_preflight_rejects_overlap_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            host_project = root / "dist" / "codex" / "project"
            source = host_project / ".agents" / "skills" / "recommended"
            source_profiles = host_project / ".codex" / "agents"
            source.mkdir(parents=True)
            source_profiles.mkdir(parents=True)
            (source / "source-marker.txt").write_text("source\n", encoding="utf-8")
            (source_profiles / "profile-marker.toml").write_text(
                "profile\n",
                encoding="utf-8",
            )

            safe_skill_target = root / "installed" / "skills"
            safe_profile_target = root / "installed" / "profiles"
            scenarios = {
                "project target is dist host project": self.helper.InstallTargets(
                    skills=host_project / ".agents" / "skills",
                    profiles=source_profiles,
                ),
                "user target is built Skill source": self.helper.InstallTargets(
                    skills=source,
                    profiles=safe_profile_target,
                ),
                "Profile source equals Profile target": self.helper.InstallTargets(
                    skills=safe_skill_target,
                    profiles=source_profiles,
                ),
            }

            for operation, cli in (
                ("install", self.install_cli),
                ("upgrade", self.upgrade_cli),
            ):
                for label, targets in scenarios.items():
                    with self.subTest(operation=operation, label=label):
                        self._assert_cli_overlap_is_non_mutating(
                            cli,
                            operation,
                            root,
                            host_project,
                            source,
                            source_profiles,
                            targets,
                        )

    def _assert_cli_overlap_is_non_mutating(
        self,
        cli,
        operation: str,
        root: Path,
        host_project: Path,
        source: Path,
        source_profiles: Path,
        targets,
    ) -> None:
        before = self._tree_snapshot(root)
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    f"{operation}.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--target",
                    str(host_project),
                ],
            ),
            mock.patch.object(
                cli,
                "resolve_source_profile_dir",
                return_value=source,
            ),
            mock.patch.object(
                cli,
                "resolve_source_profiles",
                return_value=source_profiles,
            ),
            mock.patch.object(
                cli,
                "resolve_targets",
                return_value=targets,
            ),
            mock.patch.object(cli, "validate_built_source") as built,
            mock.patch.object(cli, "read_manifest") as read_manifest,
            mock.patch.object(cli, "backup_existing") as backup,
            mock.patch.object(cli, "cleanup_legacy_residue") as cleanup,
            mock.patch.object(cli, "replace_skills") as replace_skills,
            mock.patch.object(cli, "replace_profiles") as replace_profiles,
            mock.patch.object(cli, "write_json") as write_json,
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(1, cli.main())

        built.assert_not_called()
        read_manifest.assert_not_called()
        backup.assert_not_called()
        cleanup.assert_not_called()
        replace_skills.assert_not_called()
        replace_profiles.assert_not_called()
        write_json.assert_not_called()
        self.assertEqual(before, self._tree_snapshot(root))

    def test_install_preflight_checks_symlink_resolved_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "dist" / "skills" / "recommended"
            source.mkdir(parents=True)
            target_alias = root / "target-alias"
            target_alias.symlink_to(source, target_is_directory=True)
            before = self._tree_snapshot(root)

            with self.assertRaises(self.helper.InstallError):
                self.helper.validate_install_path_separation(
                    source,
                    None,
                    self.helper.InstallTargets(skills=target_alias, profiles=None),
                )

            self.assertEqual(before, self._tree_snapshot(root))

    @staticmethod
    def _tree_snapshot(root: Path) -> tuple[tuple[str, str, bytes | str], ...]:
        entries: list[tuple[str, str, bytes | str]] = []
        for path in sorted([root, *root.rglob("*")]):
            relative = str(path.relative_to(root)) or "."
            if path.is_symlink():
                entries.append((relative, "symlink", str(path.readlink())))
            elif path.is_dir():
                entries.append((relative, "directory", ""))
            else:
                entries.append((relative, "file", path.read_bytes()))
        return tuple(entries)

    @classmethod
    @contextmanager
    def _temporary_recommended_build(cls):
        from tests.scripts.test_build_safety import BUILD, BuildSafetyTests

        case = BuildSafetyTests()
        with tempfile.TemporaryDirectory(
            prefix="changeforge-hookless-installer-safety-"
        ) as raw:
            root = (Path(raw) / "repo").resolve()
            if root.is_relative_to(SOURCE_ROOT.resolve()):
                raise AssertionError(
                    "temporary Runtime fixture must be outside the source tree"
                )
            case._copy_source(root)
            ignored = shutil.ignore_patterns("__pycache__", "*.pyc")
            shutil.copytree(
                SOURCE_ROOT / "scripts",
                root / "scripts",
                dirs_exist_ok=True,
                ignore=ignored,
            )
            for name in ("tests", "evals"):
                shutil.copytree(
                    SOURCE_ROOT / name,
                    root / name,
                    ignore=ignored,
                )
            with case._layout(root):
                result = BUILD.build_profile("recommended")
            if result != {
                "profile": "recommended",
                "top_level_count": 26,
                "compiled_layer3_reference_count": 154,
                "agent_profile_count": 4,
                "zip_count": 26,
            }:
                raise AssertionError(
                    f"unexpected canonical Runtime build result: {result}"
                )
            with (
                mock.patch.multiple(
                    cls.helper,
                    ROOT=root,
                    HOST_ENFORCEMENT_SOURCE=(
                        root / "src/agent-profiles/host-enforcement.json"
                    ),
                    CORE_CONTRACTS_SOURCE=(
                        root / "src/control-model/core-contracts.json"
                    ),
                    SOURCE_SKILL_ROOTS={
                        key: root / relative
                        for key, relative in cls._source_skill_relatives.items()
                    },
                    SOURCE_PROFILE_ROOTS={
                        key: root / relative
                        for key, relative in cls._source_profile_relatives.items()
                    },
                ),
                mock.patch.object(
                    cls.doctor_cli,
                    "HOST_ENFORCEMENT_SOURCE",
                    root / "src/agent-profiles/host-enforcement.json",
                ),
            ):
                yield root

    def _assert_cli_freshness_failure_before_mutation(
        self,
        cli,
        operation: str,
        root: Path,
        scenario: str,
    ) -> None:
        source = root / "dist/codex/project/.agents/skills/recommended"
        source_profiles = root / "dist/codex/project/.codex/agents"
        project = root / f"{scenario}-{operation}-target"
        project.mkdir()
        sentinel = project / "sentinel.txt"
        sentinel.write_text("unchanged\n", encoding="utf-8")
        targets = self.helper.InstallTargets(
            skills=project / ".agents/skills",
            profiles=project / ".codex/agents",
        )
        before = self._tree_snapshot(project)
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    f"{operation}.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--target",
                    str(project),
                ],
            ),
            mock.patch.object(cli, "resolve_source_profile_dir", return_value=source),
            mock.patch.object(cli, "resolve_source_profiles", return_value=source_profiles),
            mock.patch.object(cli, "resolve_targets", return_value=targets),
            mock.patch.object(cli, "read_manifest", return_value={}) as read_manifest,
            mock.patch.object(cli, "backup_existing") as backup,
            mock.patch.object(cli, "cleanup_legacy_residue", return_value=[]) as cleanup,
            mock.patch.object(cli, "replace_skills") as replace_skills,
            mock.patch.object(cli, "replace_profiles") as replace_profiles,
            mock.patch.object(cli, "write_json") as write_json,
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(1, cli.main())

        read_manifest.assert_not_called()
        backup.assert_not_called()
        cleanup.assert_not_called()
        replace_skills.assert_not_called()
        replace_profiles.assert_not_called()
        write_json.assert_not_called()
        self.assertEqual(before, self._tree_snapshot(project))

    def test_install_and_upgrade_reject_unfresh_build_before_target_mutation(self) -> None:
        with self._temporary_recommended_build() as root:
            manifest_path = (
                root
                / "dist/codex/project/.agents/skills/recommended"
                / self.helper.BUILD_MANIFEST_NAME
            )
            original_manifest = manifest_path.read_bytes()
            source_path = root / "src/registry/control-skills.yaml"
            original_source = source_path.read_bytes()
            for scenario in ("stale", "missing", "malformed"):
                manifest_path.write_bytes(original_manifest)
                source_path.write_bytes(original_source)
                if scenario == "stale":
                    source_path.write_bytes(original_source + b"\n# stale\n")
                else:
                    manifest = json.loads(original_manifest)
                    if scenario == "missing":
                        manifest.pop("authoritative_build_inputs")
                    else:
                        manifest["authoritative_build_inputs"] = "malformed"
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                for operation, cli in (
                    ("install", self.install_cli),
                    ("upgrade", self.upgrade_cli),
                ):
                    with self.subTest(scenario=scenario, operation=operation):
                        self._assert_cli_freshness_failure_before_mutation(
                            cli,
                            operation,
                            root,
                            scenario,
                        )

    def test_openai_rejects_unfresh_build_manifest_without_bundle_mutation(self) -> None:
        with self._temporary_recommended_build() as root:
            bundles = root / "dist/openai-api/zips/recommended"
            manifest_path = (
                root
                / "dist/universal/skills/recommended"
                / self.helper.BUILD_MANIFEST_NAME
            )
            original_manifest = manifest_path.read_bytes()
            source_path = root / "src/registry/control-skills.yaml"
            original_source = source_path.read_bytes()
            before = self._tree_snapshot(bundles)
            for scenario in ("stale", "missing", "malformed"):
                manifest_path.write_bytes(original_manifest)
                source_path.write_bytes(original_source)
                if scenario == "stale":
                    source_path.write_bytes(original_source + b"\n# stale\n")
                else:
                    manifest = json.loads(original_manifest)
                    if scenario == "missing":
                        manifest.pop("authoritative_build_inputs")
                    else:
                        manifest["authoritative_build_inputs"] = "malformed"
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.subTest(scenario=scenario), self.assertRaisesRegex(
                    self.helper.InstallError,
                    "authoritative build input",
                ):
                    self.helper.validate_openai_bundles(bundles)
                self.assertEqual(before, self._tree_snapshot(bundles))

    def test_profile_replacement_unlinks_live_and_dangling_symlinks(self) -> None:
        for live in (False, True):
            with self.subTest(live=live), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                source = root / "source"
                target = root / "target"
                source.mkdir()
                target.mkdir()
                name = "analysis-agent.toml"
                (source / name).write_text("new profile\n", encoding="utf-8")
                outside = root / "outside.toml"
                if live:
                    outside.write_text("preserve\n", encoding="utf-8")
                profile = target / name
                profile.symlink_to(outside)

                self.assertEqual(
                    [name],
                    self.helper.find_unmanaged_conflicts(target, {name}, set()),
                )
                self.helper.replace_profiles(source, target, {name}, False)

                self.assertFalse(profile.is_symlink())
                self.assertEqual("new profile\n", profile.read_text(encoding="utf-8"))
                if live:
                    self.assertEqual("preserve\n", outside.read_text(encoding="utf-8"))
                else:
                    self.assertFalse(outside.exists())

    def test_project_profile_root_symlinks_cannot_escape_project(self) -> None:
        for live in (False, True):
            with self.subTest(live=live), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                config = project / ".codex"
                config.mkdir(parents=True)
                outside = Path(raw) / "outside-agents"
                if live:
                    outside.mkdir()
                (config / "agents").symlink_to(outside, target_is_directory=True)

                with self.assertRaises(self.helper.InstallError):
                    self.helper.resolve_targets("codex", "project", project)

                self.assertTrue((config / "agents").is_symlink())
                if not live:
                    self.assertFalse(outside.exists())

    def test_current_profile_symlinks_are_reported_as_residue(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            skills = project / ".agents" / "skills"
            agents = project / ".codex" / "agents"
            skills.mkdir(parents=True)
            agents.mkdir(parents=True)
            outside = Path(raw) / "outside.toml"
            profile = agents / "analysis-agent.toml"
            profile.symlink_to(outside)

            residue = self.helper.legacy_residue_paths(
                "codex",
                "project",
                project,
                skills,
            )

            self.assertIn("analysis-agent.toml", {path.name for path in residue})
            self.assertTrue(profile.is_symlink())
            self.assertFalse(outside.exists())

    def test_manifest_symlinks_are_rejected_without_external_write(self) -> None:
        for live in (False, True):
            with self.subTest(live=live), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                skills = root / "skills"
                skills.mkdir()
                outside = root / "outside.json"
                original = '{"preserve": true}\n'
                if live:
                    outside.write_text(original, encoding="utf-8")
                manifest = skills / self.helper.MANIFEST_NAME
                manifest.symlink_to(outside)

                with self.assertRaises(self.helper.InstallError):
                    self.helper.read_manifest(skills)
                with self.assertRaises(self.helper.InstallError):
                    self.helper.write_json(manifest, {"unsafe": True})

                if live:
                    self.assertEqual(original, outside.read_text(encoding="utf-8"))
                else:
                    self.assertFalse(outside.exists())

    def test_build_manifest_requires_ai_consumption_layer3_format(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "recommended"
            source.mkdir()
            manifest_path = source / self.helper.BUILD_MANIFEST_NAME
            valid = {
                "architecture": "hookless-control-plane-v1",
                "compiled_layer3_format": self.helper.COMPILED_LAYER3_FORMAT,
            }
            manifest_path.write_text(json.dumps(valid), encoding="utf-8")
            self.assertEqual(valid, self.helper.read_build_manifest(source))

            for value in (None, "authoring-root-v1"):
                with self.subTest(value=value):
                    invalid = dict(valid)
                    if value is None:
                        invalid.pop("compiled_layer3_format")
                    else:
                        invalid["compiled_layer3_format"] = value
                    manifest_path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaisesRegex(
                        self.helper.InstallError,
                        "compiled_layer3_format must equal",
                    ):
                        self.helper.read_build_manifest(source)

    def test_backup_root_and_action_symlinks_are_rejected(self) -> None:
        for location in ("root", "action"):
            for live in (False, True):
                with (
                    self.subTest(location=location, live=live),
                    tempfile.TemporaryDirectory() as raw,
                ):
                    root = Path(raw)
                    skills = root / "skills"
                    managed = skills / "engineering-control-plane"
                    managed.mkdir(parents=True)
                    (managed / "SKILL.md").write_text("managed\n", encoding="utf-8")
                    outside = root / "outside"
                    if live:
                        outside.mkdir()
                    backup_root = skills / self.helper.BACKUP_DIR_NAME
                    if location == "root":
                        backup_root.symlink_to(outside, target_is_directory=True)
                    else:
                        backup_root.mkdir()
                        (backup_root / "install-fixed").symlink_to(
                            outside,
                            target_is_directory=True,
                        )
                    targets = self.helper.InstallTargets(skills=skills, profiles=None)

                    with (
                        mock.patch.object(self.helper, "utc_stamp", return_value="fixed"),
                        self.assertRaises(self.helper.InstallError),
                    ):
                        self.helper.backup_existing(
                            targets,
                            {"engineering-control-plane"},
                            set(),
                            "install",
                            False,
                        )

                    self.assertFalse((outside / "skills").exists())
                    if not live:
                        self.assertFalse(outside.exists())

    def test_legacy_leaf_symlinks_are_unlinked_without_following(self) -> None:
        for live in (False, True):
            with self.subTest(live=live), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                skills = project / ".agents" / "skills"
                hooks = project / ".codex" / "hooks"
                skills.mkdir(parents=True)
                hooks.mkdir(parents=True)
                outside = Path(raw) / "outside.py"
                if live:
                    outside.write_text("preserve\n", encoding="utf-8")
                legacy = hooks / "changeforge_hook.py"
                legacy.symlink_to(outside)

                removed = self.helper.cleanup_legacy_residue(
                    "codex",
                    "project",
                    project,
                    skills,
                    False,
                )

                self.assertIn("changeforge_hook.py", {path.name for path in removed})
                self.assertFalse(legacy.is_symlink())
                if live:
                    self.assertEqual("preserve\n", outside.read_text(encoding="utf-8"))
                else:
                    self.assertFalse(outside.exists())

    def test_legacy_ancestor_symlinks_cannot_escape_project(self) -> None:
        for live in (False, True):
            with self.subTest(live=live), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                skills = project / ".agents" / "skills"
                config = project / ".codex"
                skills.mkdir(parents=True)
                config.mkdir(parents=True)
                outside = Path(raw) / "outside-hooks"
                if live:
                    outside.mkdir()
                    (outside / "changeforge_hook.py").write_text(
                        "preserve\n",
                        encoding="utf-8",
                    )
                (config / "hooks").symlink_to(outside, target_is_directory=True)

                with self.assertRaises(self.helper.InstallError):
                    self.helper.cleanup_legacy_residue(
                        "codex",
                        "project",
                        project,
                        skills,
                        False,
                    )

                self.assertTrue((config / "hooks").is_symlink())
                if live:
                    self.assertEqual(
                        "preserve\n",
                        (outside / "changeforge_hook.py").read_text(encoding="utf-8"),
                    )
                else:
                    self.assertFalse(outside.exists())

    def test_unmarked_copilot_plain_md_profiles_are_preserved(self) -> None:
        for live in (False, True):
            with self.subTest(live=live), tempfile.TemporaryDirectory() as raw:
                project = Path(raw) / "project"
                skills = project / ".github" / "skills"
                agents = project / ".github" / "agents"
                skills.mkdir(parents=True)
                agents.mkdir(parents=True)
                outside = Path(raw) / "outside-profile.md"
                if live:
                    outside.write_text("preserve\n", encoding="utf-8")
                legacy = agents / "analysis-agent.md"
                legacy.symlink_to(outside)

                removed = self.helper.cleanup_legacy_residue(
                    "copilot",
                    "project",
                    project,
                    skills,
                    False,
                )

                self.assertNotIn("analysis-agent.md", {path.name for path in removed})
                self.assertTrue(legacy.is_symlink())
                if live:
                    self.assertEqual("preserve\n", outside.read_text(encoding="utf-8"))
                else:
                    self.assertFalse(outside.exists())

    def test_marked_legacy_copilot_plain_md_profile_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            skills = project / ".github" / "skills"
            agents = project / ".github" / "agents"
            skills.mkdir(parents=True)
            agents.mkdir(parents=True)
            legacy = agents / "task-agent.md"
            legacy.write_text(
                "# ChangeForge legacy profile\nDeclared tool boundary: edit\n",
                encoding="utf-8",
            )

            removed = self.helper.cleanup_legacy_residue(
                "copilot",
                "project",
                project,
                skills,
                False,
            )

            self.assertIn("task-agent.md", {path.name for path in removed})
            self.assertFalse(legacy.exists())

    def test_unmarked_legacy_named_profile_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            skills = project / ".agents" / "skills"
            agents = project / ".codex" / "agents"
            skills.mkdir(parents=True)
            agents.mkdir(parents=True)
            user_profile = agents / "analysis-worker.toml"
            user_profile.write_text(
                'name = "analysis-worker"\n# User-owned unrelated profile\n',
                encoding="utf-8",
            )

            removed = self.helper.cleanup_legacy_residue(
                "codex",
                "project",
                project,
                skills,
                False,
            )

            self.assertNotIn("analysis-worker.toml", {path.name for path in removed})
            self.assertTrue(user_profile.is_file())

    def test_built_skill_source_rejects_nested_symlinks(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=self.runtime_root / "dist",
            prefix="nested-symlink-source-",
        ) as raw, tempfile.TemporaryDirectory() as outside_raw:
            source = Path(raw)
            outside = Path(outside_raw) / "external-skill"
            outside.mkdir()
            (outside / "SKILL.md").write_text("# external\n", encoding="utf-8")
            (outside / "secret.txt").write_text("must not copy\n", encoding="utf-8")
            (source / "external-skill").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(self.helper.InstallError):
                self.helper.validate_built_source(
                    "cline",
                    source,
                    None,
                )

    def test_symlinked_shared_hook_config_aborts_before_legacy_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "project"
            skills = project / ".agents" / "skills"
            hooks = project / ".codex" / "hooks"
            skills.mkdir(parents=True)
            hooks.mkdir(parents=True)
            legacy = hooks / "changeforge_hook.py"
            legacy.write_text("preserve until preflight passes\n", encoding="utf-8")
            outside = Path(raw) / "outside-hooks.json"
            original = json.dumps(
                {
                    "hooks": {
                        "Before": [
                            {"hooks": [{"command": "python changeforge_hook.py"}]}
                        ]
                    }
                }
            )
            outside.write_text(original, encoding="utf-8")
            (project / ".codex" / "hooks.json").symlink_to(outside)

            with self.assertRaises(self.helper.InstallError):
                self.helper.cleanup_legacy_residue(
                    "codex",
                    "project",
                    project,
                    skills,
                    False,
                )

            self.assertTrue(legacy.is_file())
            self.assertEqual(original, outside.read_text(encoding="utf-8"))

    def test_openai_bundle_rejects_unsafe_paths_and_bad_crc(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            valid = root / "valid" / "skill.zip"
            valid.parent.mkdir()
            with zipfile.ZipFile(valid, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("skill/SKILL.md", "valid\n")
            self.helper._validate_openai_bundle(valid)

            for index, unsafe in enumerate(
                ("skill/../outside.txt", "skill/..\\outside.txt"),
                start=1,
            ):
                with self.subTest(unsafe=unsafe):
                    path = root / f"unsafe-{index}" / "skill.zip"
                    path.parent.mkdir()
                    with zipfile.ZipFile(path, "w") as archive:
                        archive.writestr("skill/SKILL.md", "valid\n")
                        archive.writestr(unsafe, "escape\n")
                    with self.assertRaises(self.helper.InstallError):
                        self.helper._validate_openai_bundle(path)

            corrupt = root / "corrupt" / "skill.zip"
            corrupt.parent.mkdir()
            payload = b"UNIQUE_CRC_PAYLOAD_12345"
            with zipfile.ZipFile(corrupt, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("skill/SKILL.md", payload)
            data = bytearray(corrupt.read_bytes())
            offset = data.find(payload)
            self.assertGreaterEqual(offset, 0)
            data[offset] ^= 0x01
            corrupt.write_bytes(data)
            with self.assertRaises(self.helper.InstallError):
                self.helper._validate_openai_bundle(corrupt)


if __name__ == "__main__":
    unittest.main()
