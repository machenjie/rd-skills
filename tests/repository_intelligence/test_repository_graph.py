from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.repo_indexer import build_repository_graph
from repository_intelligence.cache.repo_hash import stable_artifact_hash, stable_repo_hash


class RepositoryGraphTests(unittest.TestCase):
    def test_builds_registry_import_hook_and_test_edges_without_dist_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/foundation/capabilities/sample").mkdir(parents=True)
            (root / "src/foundation/capabilities/sample/SKILL.md").write_text("# Sample\n", encoding="utf-8")
            (root / "src/registry").mkdir(parents=True)
            (root / "src/registry/capabilities.yaml").write_text(
                """---
schema_version: 1
kind: changeforge.capabilities
capabilities:
  - id: "01"
    name: sample
    path: src/foundation/capabilities/sample
    used_by: []
""",
                encoding="utf-8",
            )
            (root / "src/hook-runtime/scripts").mkdir(parents=True)
            (root / "src/hook-runtime/scripts/helper.py").write_text("def help_me():\n    return 1\n", encoding="utf-8")
            (root / "src/hook-runtime/scripts/sample.py").write_text(
                "from helper import help_me\n", encoding="utf-8"
            )
            (root / "scripts").mkdir()
            (root / "scripts/build.py").write_text("print('build')\n", encoding="utf-8")
            (root / "scripts/validate-hooks.py").write_text("print('hooks')\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests/test_sample.py").write_text("def test_sample():\n    pass\n", encoding="utf-8")
            (root / "dist").mkdir()
            (root / "dist/generated.py").write_text("generated = True\n", encoding="utf-8")

            graph = build_repository_graph(root)["repository_graph"]

        paths = {file_node["path"] for file_node in graph["files"]}
        self.assertIn("src/registry/capabilities.yaml", paths)
        self.assertNotIn("dist/generated.py", paths)
        edges = {(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]}
        self.assertIn(
            ("src/registry/capabilities.yaml", "src/foundation/capabilities/sample/SKILL.md", "registry_entry"),
            edges,
        )
        self.assertIn(("src/hook-runtime/scripts/sample.py", "src/hook-runtime/scripts/helper.py", "import"), edges)
        self.assertTrue(any(edge_type == "hook_template_reference" for _source, _target, edge_type in edges))
        self.assertTrue(any(edge_type == "generated_artifact" for _source, _target, edge_type in edges))

    def test_generated_reports_do_not_change_source_repo_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "reports").mkdir()
            (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "reports/score.md").write_text("old\n", encoding="utf-8")

            source_before = stable_repo_hash(root)
            artifact_before = stable_artifact_hash(root)
            (root / "reports/score.md").write_text("new\n", encoding="utf-8")
            source_after = stable_repo_hash(root)
            artifact_after = stable_artifact_hash(root)

        self.assertEqual(source_before, source_after)
        self.assertNotEqual(artifact_before, artifact_after)


if __name__ == "__main__":
    unittest.main()
