from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


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
    def test_external_built_source_packages_without_repository_relative_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            skill = root / "source" / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: sample-skill\n---\n\n# Sample\n", encoding="utf-8")
            output = root / "zips"

            self.assertEqual(PACKAGE.package_profile(root / "source", output), 1)
            self.assertTrue((output / "sample-skill.zip").is_file())

    def test_symlinked_skill_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            skill = root / "source" / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            outside = root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (skill / "references").mkdir()
            (skill / "references" / "escape.md").symlink_to(outside)

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(root / "source", root / "zips")

    def test_symlinked_source_and_output_roots_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "source"
            skill = source / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            source_link = root / "source-link"
            source_link.symlink_to(source, target_is_directory=True)

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(source_link, root / "zips")

            output = root / "real-zips"
            output.mkdir()
            output_link = root / "zips-link"
            output_link.symlink_to(output, target_is_directory=True)
            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(source, output_link)

    def test_symlinked_ancestor_is_rejected_before_external_output_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "source"
            skill = source / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Sample\n", encoding="utf-8")

            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "sentinel.zip"
            sentinel.write_bytes(b"unchanged")
            ancestor = root / "redirect"
            ancestor.symlink_to(outside, target_is_directory=True)

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(source, ancestor / "managed-zips")
            self.assertEqual(b"unchanged", sentinel.read_bytes())
            self.assertFalse((outside / "managed-zips").exists())

            source_parent = root / "source-redirect"
            source_parent.symlink_to(root, target_is_directory=True)
            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(source_parent / "source", root / "zips")

    def test_source_output_overlap_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "source"
            skill = source / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            sentinel = source / "sentinel.zip"
            sentinel.write_bytes(b"unchanged")

            for output in (source, skill / "zips"):
                with self.subTest(output=output):
                    with self.assertRaises(PACKAGE.PackageError):
                        PACKAGE.package_profile(source, output)
                    self.assertEqual(b"unchanged", sentinel.read_bytes())

    def test_invalid_skill_name_preserves_existing_managed_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            skill = root / "source" / "unsafe_name"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            output = root / "zips"
            output.mkdir()
            existing = output / "unsafe_name.zip"
            existing.write_bytes(b"unchanged")

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(root / "source", output)
            self.assertEqual(b"unchanged", existing.read_bytes())

    def test_backslash_archive_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            archive_path = output / "sample-skill.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("sample-skill\\SKILL.md", "# Sample\n")

            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE._validate_written_zips(output)

    def test_missing_source_and_unrelated_zip_are_never_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            output = root / "zips"
            output.mkdir()
            unrelated = output / "user-backup.zip"
            unrelated.write_bytes(b"preserve")

            self.assertEqual(PACKAGE.package_profile(root / "missing", output), 0)
            self.assertEqual(b"preserve", unrelated.read_bytes())

            skill = root / "source" / "sample-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Sample\n", encoding="utf-8")
            with self.assertRaises(PACKAGE.PackageError):
                PACKAGE.package_profile(root / "source", output)
            self.assertEqual(b"preserve", unrelated.read_bytes())


if __name__ == "__main__":
    unittest.main()
