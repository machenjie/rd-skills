from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validation_utils as VALIDATION  # noqa: E402
import build as BUILD  # noqa: E402


def load_package_module():
    spec = importlib.util.spec_from_file_location(
        "hookless_package_tests",
        ROOT / "scripts/package.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PACKAGE = load_package_module()


class PackageSafetyTests(unittest.TestCase):
    @contextmanager
    def _runtime_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            built_root = root / "universal/skills"
            source = built_root / "recommended"
            registries = {
                layer: VALIDATION.load_yaml_file(ROOT / "src/registry" / filename)[key]
                for layer, filename, key in (
                    ("control", "control-skills.yaml", "control_skills"),
                    ("professional", "professional-skills.yaml", "professional_skills"),
                    ("foundation", "foundation-skills.yaml", "foundation_skills"),
                    ("domain", "domain-skills.yaml", "domain_skills"),
                )
            }
            names = {
                layer: [entry["name"] for entry in entries]
                for layer, entries in registries.items()
            }
            allowed_layer3 = set(names["domain"]) | {
                entry["name"]
                for entry in registries["foundation"]
                if entry.get("delivery_scope") == "product"
            }
            compiled = {
                entry["name"]: list(
                    dict.fromkeys(
                        name
                        for name in entry.get("layer3_candidates", [])
                        if name in allowed_layer3
                    )
                )
                for entry in registries["professional"]
            }
            source_snapshot = VALIDATION.authoritative_build_input_snapshot(ROOT)
            runtime_asset_bindings = {}
            build_identity = VALIDATION.runtime_asset_build_identity(
                source_snapshot["sha256"]
            )
            runtime_version = BUILD._source_version()
            for name in [*names["control"], *names["professional"]]:
                skill = source / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    "---\n"
                    f"name: {name}\n"
                    "---\n\n"
                    f"# {name}\n\n"
                    "## JIT Reference Delivery\n\n"
                    "JIT: `references/runtime/selector.json`; "
                    f"Runtime: `{runtime_version}/{build_identity}`.\n",
                    encoding="utf-8",
                )
                if name in names["professional"]:
                    selector = skill / "references/runtime/selector.json"
                    selector.parent.mkdir(parents=True)
                    selector.write_text(
                        json.dumps(
                            {"build": build_identity},
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    runtime_asset_bindings[name] = (
                        BUILD._write_and_validate_runtime_bundle_metadata(
                            skill,
                            name,
                            source_snapshot,
                        )
                    )
            manifest_path = source / ".changeforge-build-manifest.json"
            manifest = {
                "profile": "recommended",
                "source_version": BUILD._source_version(),
                "authoritative_build_inputs": source_snapshot,
                "runtime_asset_bindings": runtime_asset_bindings,
                "top_level_skills": [*names["control"], *names["professional"]],
                "control_skills": names["control"],
                "professional_skills": names["professional"],
                "foundation_skills": names["foundation"],
                "domain_skills": names["domain"],
                "compiled_layer3_references": compiled,
                "foundation_mode": "targeted-product-references",
                "domain_mode": "targeted-references",
                "agent_profiles": [
                    "main-control-agent",
                    "analysis-agent",
                    "task-agent",
                    "review-agent",
                ],
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            zip_root = root / "openai-api/zips"
            with mock.patch.multiple(
                PACKAGE,
                BUILT_SKILLS_ROOT=built_root,
                ZIP_DIR=zip_root,
            ):
                yield root, source, zip_root

    def test_packages_exact_current_runtime(self) -> None:
        with self._runtime_layout() as (_root, source, zip_root):
            self.assertEqual(26, PACKAGE.package_profile())
            output = zip_root / "recommended"
            self.assertEqual(
                {f"{path.name}.zip" for path in source.iterdir() if path.is_dir()},
                {path.name for path in output.glob("*.zip")},
            )

    def test_cli_rejects_profile_and_arbitrary_source_before_mutation(self) -> None:
        with self._runtime_layout() as (_root, _source, zip_root):
            for flag, value in (("--profile", "full"), ("--source", "/tmp/input")):
                with self.subTest(flag=flag), mock.patch.object(
                    sys,
                    "argv",
                    ["package.py", flag, value],
                ), self.assertRaises(SystemExit):
                    PACKAGE.main()
                self.assertFalse(zip_root.exists())

    def test_manifest_profile_names_and_modes_are_required_before_writing(self) -> None:
        mutations = (
            ("profile", "full", "profile"),
            ("foundation_mode", "top-level", "foundation_mode"),
            ("domain_mode", "top-level", "domain_mode"),
            ("top_level_skills", ["engineering-control-plane"], "top_level_skills"),
        )
        for field, value, error in mutations:
            with self.subTest(field=field), self._runtime_layout() as (
                _root,
                source,
                zip_root,
            ):
                manifest_path = source / ".changeforge-build-manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest[field] = value
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                sentinel = zip_root / "sentinel.bin"
                sentinel.parent.mkdir(parents=True)
                sentinel.write_bytes(b"unchanged")

                with self.assertRaisesRegex(PACKAGE.PackageError, error):
                    PACKAGE.package_profile()

                self.assertEqual(b"unchanged", sentinel.read_bytes())

    def test_source_tree_must_match_exact_manifest_names(self) -> None:
        with self._runtime_layout() as (_root, source, zip_root):
            extra = source / "unexpected-skill"
            extra.mkdir()
            (extra / "SKILL.md").write_text("# Unexpected\n", encoding="utf-8")

            with self.assertRaisesRegex(PACKAGE.PackageError, "built Skill names"):
                PACKAGE.package_profile()
            self.assertFalse(zip_root.exists())

    def test_symlinked_skill_content_is_rejected(self) -> None:
        with self._runtime_layout() as (root, source, zip_root):
            skill = next(path for path in source.iterdir() if path.is_dir())
            outside = root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (skill / "escape.md").symlink_to(outside)

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile()
            self.assertFalse(zip_root.exists())

    def test_symlinked_managed_root_is_rejected_before_external_changes(self) -> None:
        with self._runtime_layout() as (root, _source, zip_root):
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "sentinel.zip"
            sentinel.write_bytes(b"unchanged")
            zip_root.parent.mkdir(parents=True)
            zip_root.symlink_to(outside, target_is_directory=True)

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile()
            self.assertEqual(b"unchanged", sentinel.read_bytes())

    def test_retired_roots_are_preflighted_then_removed_without_touching_sentinels(self) -> None:
        with self._runtime_layout() as (_root, source, zip_root):
            for managed_root in (source.parent, zip_root):
                for retired in ("full", "dev"):
                    residue = managed_root / retired / "managed.bin"
                    residue.parent.mkdir(parents=True, exist_ok=True)
                    residue.write_bytes(b"retired")
                sentinel = managed_root / "user-sentinel.bin"
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.write_bytes(b"preserve")

            PACKAGE.package_profile()

            for managed_root in (source.parent, zip_root):
                self.assertFalse((managed_root / "full").exists())
                self.assertFalse((managed_root / "dev").exists())
                self.assertEqual(
                    b"preserve",
                    (managed_root / "user-sentinel.bin").read_bytes(),
                )

    def test_invalid_retired_root_prevents_all_cleanup_and_packaging(self) -> None:
        with self._runtime_layout() as (_root, source, zip_root):
            first = source.parent / "full/managed.bin"
            first.parent.mkdir(parents=True)
            first.write_bytes(b"preserve")
            invalid = zip_root / "dev"
            invalid.parent.mkdir(parents=True)
            invalid.write_bytes(b"not-a-directory")

            with self.assertRaisesRegex(
                PACKAGE.PackageError,
                "retired profile output.*regular directory",
            ):
                PACKAGE.package_profile()

            self.assertEqual(b"preserve", first.read_bytes())
            self.assertEqual(b"not-a-directory", invalid.read_bytes())
            self.assertFalse((zip_root / "recommended").exists())

    def test_backslash_archive_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            archive_path = output / "sample-skill.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("sample-skill\\SKILL.md", "# Sample\n")

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE._validate_written_zips(output)

    def test_unrelated_zip_is_never_deleted(self) -> None:
        with self._runtime_layout() as (_root, _source, zip_root):
            output = zip_root / "recommended"
            output.mkdir(parents=True)
            unrelated = output / "user-backup.zip"
            unrelated.write_bytes(b"preserve")

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile()
            self.assertEqual(b"preserve", unrelated.read_bytes())


if __name__ == "__main__":
    unittest.main()
