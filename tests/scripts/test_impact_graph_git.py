from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.scripts.affected_test_support import impact_fixture_owner
from tests.scripts.test_impact_graph import CORE_CONTRACTS, ROOT, impact_graph


_FIXTURES = impact_fixture_owner()


class ImpactGraphGitTests(unittest.TestCase):
    _write_registry_catalog = staticmethod(_FIXTURES._write_registry_catalog)
    _resolve = _FIXTURES._resolve

    def test_current_repository_paths_have_one_closed_classification(self) -> None:
        listed = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        paths = sorted(
            {
                raw.decode("utf-8", "surrogateescape")
                for raw in listed.split(b"\0")
                if raw
            }
        )
        result = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("M", path) for path in paths],
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_package_catalog={},
            head_package_catalog={},
        )
        self.assertEqual(len(paths), len(result["changed_paths"]))
        counts: dict[str, int] = {}
        for row in result["changed_paths"]:
            classification = row["classification"]
            counts[classification] = counts.get(classification, 0) + 1
        self.assertEqual(
            {"known-no-impact", "rule", "test-self"}, set(counts)
        )
        self.assertEqual([], result["selected_test_modules_by_layer"]["release"])
        self.assertNotIn("fallback", result)

    def test_real_git_deleted_reference_matches_modification(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        path = root / "src/professional-skills/example/references/example.md"
        path.parent.mkdir(parents=True)
        path.write_text("first\n", encoding="utf-8")
        self._write_registry_catalog(root, include_example=True)
        commands = (
            ["git", "init", "-q"],
            ["git", "add", "."],
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "base",
            ],
        )
        for command in commands:
            subprocess.run(command, cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        path.unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "delete",
            ],
            cwd=root,
            check=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        selected = impact_graph.select(root, CORE_CONTRACTS, base, head)
        expected = self._resolve(
            [("M", "src/professional-skills/example/references/example.md")]
        )
        self.assertEqual(
            expected["selected_producer_ids"], selected["selected_producer_ids"]
        )

    def test_real_git_package_deletion_is_full_but_reference_deletion_is_scoped(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        package = root / "src/professional-skills/example"
        reference = package / "references/example.md"
        reference.parent.mkdir(parents=True)
        (package / "SKILL.md").write_text("# Example\n", encoding="utf-8")
        reference.write_text("reference\n", encoding="utf-8")
        self._write_registry_catalog(root, include_example=True)
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "."],
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "base",
            ],
        ):
            subprocess.run(command, cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

        reference.unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "delete-reference",
            ],
            cwd=root,
            check=True,
        )
        reference_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        reference_selection = impact_graph.select(
            root, CORE_CONTRACTS, base, reference_head
        )
        self.assertEqual("packages", reference_selection["professionalism"]["scope"])
        self.assertEqual(
            ["example"],
            reference_selection["professionalism"]["direct_package_ids"],
        )

        (package / "SKILL.md").unlink()
        self._write_registry_catalog(root, include_example=False)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "delete-package",
            ],
            cwd=root,
            check=True,
        )
        deleted_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        deleted_selection = impact_graph.select(
            root, CORE_CONTRACTS, reference_head, deleted_head
        )
        self.assertEqual("full", deleted_selection["professionalism"]["scope"])
        self.assertEqual(
            [], deleted_selection["professionalism"]["direct_package_ids"]
        )
        self.assertEqual("recommended", deleted_selection["selected_runtime"])

    def test_real_git_test_deletion_and_rename_run_only_present_paths(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        old_path = root / "tests/scripts/test_old.py"
        old_path.parent.mkdir(parents=True)
        old_path.write_text("import unittest\n", encoding="utf-8")
        self._write_registry_catalog(root, include_example=False)
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "."],
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "base",
            ],
        ):
            subprocess.run(command, cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

        old_path.unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "delete",
            ],
            cwd=root,
            check=True,
        )
        deleted_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        deleted = impact_graph.select(root, CORE_CONTRACTS, base, deleted_head)
        self.assertEqual([], deleted["selected_test_modules"])

        old_path.write_text("import unittest\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "restore",
            ],
            cwd=root,
            check=True,
        )
        rename_base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        subprocess.run(
            ["git", "mv", "tests/scripts/test_old.py", "tests/scripts/test_new.py"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qam",
                "rename",
            ],
            cwd=root,
            check=True,
        )
        rename_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        renamed = impact_graph.select(root, CORE_CONTRACTS, rename_base, rename_head)
        self.assertEqual(
            ["tests/scripts/test_new.py"], renamed["selected_test_modules"]
        )




del _FIXTURES


if __name__ == "__main__":
    unittest.main()
