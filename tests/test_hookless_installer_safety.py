from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager, redirect_stderr
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


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
        cls.helper = load_install_helper()
        cls.install_cli = load_cli(cls.helper, "install")
        cls.upgrade_cli = load_cli(cls.helper, "upgrade")

    def test_installer_profile_counts_match_current_delivery_contract(self) -> None:
        self.assertEqual(
            {"recommended": 27, "full": 40, "dev": 190},
            self.helper.EXPECTED_PROFILE_COUNTS,
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

    @contextmanager
    def _temporary_recommended_build(self):
        from tests.scripts.test_build_safety import BUILD, BuildSafetyTests

        case = BuildSafetyTests()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve() / "repo"
            case._copy_source(root)
            with case._layout(root):
                BUILD.build_profile("recommended")
            with mock.patch.multiple(
                self.helper,
                ROOT=root,
                HOST_ENFORCEMENT_SOURCE=(
                    root / "src/agent-profiles/host-enforcement.json"
                ),
                CORE_CONTRACTS_SOURCE=(
                    root / "src/control-model/core-contracts.json"
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
                    "--profile",
                    "recommended",
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
                    self.helper.validate_openai_bundles("recommended", bundles)
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
        (ROOT / "dist").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "dist") as raw, tempfile.TemporaryDirectory() as outside_raw:
            source = Path(raw)
            outside = Path(outside_raw) / "external-skill"
            outside.mkdir()
            (outside / "SKILL.md").write_text("# external\n", encoding="utf-8")
            (outside / "secret.txt").write_text("must not copy\n", encoding="utf-8")
            (source / "external-skill").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(self.helper.InstallError):
                self.helper.validate_built_source(
                    "cline",
                    "recommended",
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
