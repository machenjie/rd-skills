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


class ContextPackBudgetTests(unittest.TestCase):
    def test_context_pack_is_bounded_and_reports_omitted_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            for index in range(12):
                (root / f"src/pkg/file_{index}.py").write_text(
                    f"VALUE_{index} = {index}\ndef function_{index}():\n    return VALUE_{index}\n",
                    encoding="utf-8",
                )
            graph = build_repository_graph(root)
            pack = build_context_pack(
                graph,
                "bounded context",
                ["src/pkg/file_0.py"],
                root,
                max_files=3,
                max_symbols=2,
            )["task_context_pack"]

        self.assertLessEqual(len(pack["selected_files"]), 3)
        self.assertLessEqual(len(pack["selected_symbols"]), 2)
        self.assertGreater(pack["anti_bloat_decision"]["omitted_node_count"], 0)
        self.assertTrue(pack["omitted_nodes"])

    def test_stale_graph_is_residual_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            source = root / "src/app.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            graph = build_repository_graph(root)
            source.write_text("VALUE = 2\n", encoding="utf-8")
            pack = build_context_pack(graph, "stale graph", ["src/app.py"], root)["task_context_pack"]

        self.assertEqual(pack["freshness"]["status"], "stale")
        self.assertIn("stale_graph", {item["kind"] for item in pack["residual_risk"]})


if __name__ == "__main__":
    unittest.main()
