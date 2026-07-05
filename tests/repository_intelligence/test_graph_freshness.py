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
from repository_intelligence.packaging.context_pack_builder import build_context_pack


class GraphFreshnessTests(unittest.TestCase):
    def test_yaml_reference_node_has_current_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/registry").mkdir(parents=True)
            (root / "src/registry/capabilities.yaml").write_text(
                """---
schema_version: 1
kind: changeforge.capabilities
capabilities:
  - id: "01"
    name: sample
    path: src/foundation/capabilities/sample
""",
                encoding="utf-8",
            )
            graph = build_repository_graph(root)["repository_graph"]

        node = next(item for item in graph["files"] if item["path"] == "src/registry/capabilities.yaml")
        self.assertEqual(node["freshness"], "current")
        self.assertEqual(node["confidence"], "high")
        self.assertTrue(node["source_hash"])

    def test_file_change_makes_old_graph_node_stale_in_context_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            source = root / "src/app.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            graph = build_repository_graph(root)
            source.write_text("VALUE = 2\n", encoding="utf-8")
            pack = build_context_pack(graph, "freshness", ["src/app.py"], root)["task_context_pack"]

        self.assertEqual(pack["freshness"]["status"], "stale")
        self.assertFalse(pack["closure_evidence"])
        self.assertTrue(any(item["path"] == "src/app.py" for item in pack["skipped_graph_nodes"]))
        self.assertIn("stale_graph", {item["kind"] for item in pack["residual_risk"]})


if __name__ == "__main__":
    unittest.main()
