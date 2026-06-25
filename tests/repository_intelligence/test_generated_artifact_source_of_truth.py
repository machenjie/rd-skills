from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.generated_artifact_graph import generated_edit_policy
from repository_intelligence.graph.repo_indexer import build_repository_graph
from repository_intelligence.packaging.context_pack_builder import build_context_pack


class GeneratedArtifactSourceOfTruthTests(unittest.TestCase):
    def test_known_generated_dist_source_has_edit_source_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/foundation/capabilities/sample").mkdir(parents=True)
            (root / "src/foundation/capabilities/sample/SKILL.md").write_text("# Sample\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts/build.py").write_text("print('build')\n", encoding="utf-8")
            graph = build_repository_graph(root)["repository_graph"]

        dist_item = next(item for item in graph["generated_artifacts"] if item["generated_path"] == "dist/")
        self.assertIn("src/foundation/capabilities", dist_item["source_of_truth"])
        self.assertEqual(dist_item["edit_policy"], "edit source / do not edit generated")
        self.assertEqual(dist_item["confidence"], "medium")

    def test_unknown_generated_source_forbids_direct_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports/score.md").write_text("generated\n", encoding="utf-8")
            graph = build_repository_graph(root)
            pack = build_context_pack(graph, "generated report", ["reports/score.md"], root)["task_context_pack"]
            files_by_path = {item["path"]: item for item in graph["repository_graph"]["files"]}

        report_item = next(item for item in pack["generated_artifacts"] if item["generated_path"] == "reports/")
        self.assertEqual(report_item["edit_policy"], "unknown requires inspection")
        self.assertEqual(report_item["confidence"], "low")
        self.assertEqual(generated_edit_policy("reports/score.md", files_by_path), "unknown requires inspection")


if __name__ == "__main__":
    unittest.main()
