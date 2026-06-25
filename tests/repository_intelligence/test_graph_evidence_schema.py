from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.repo_indexer import build_repository_graph


class GraphEvidenceSchemaTests(unittest.TestCase):
    def test_python_symbols_have_current_high_confidence_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/app.py").write_text(
                "class Worker:\n    def run(self):\n        return 1\n\ndef build():\n    return Worker()\n",
                encoding="utf-8",
            )
            graph = build_repository_graph(root)["repository_graph"]

        file_node = next(item for item in graph["files"] if item["path"] == "src/pkg/app.py")
        self.assertEqual(file_node["freshness"], "current")
        self.assertEqual(file_node["confidence"], "high")
        self.assertEqual(file_node["extractor"], "python_symbol_extractor")
        self.assertTrue(file_node["source_hash"])
        symbol = next(item for item in graph["symbols"] if item["name"] == "build")
        self.assertEqual(symbol["freshness"], "current")
        self.assertEqual(symbol["confidence"], "high")
        self.assertEqual(symbol["evidence"]["node_type"], "function")
        json.dumps(graph)

    def test_unsupported_language_uses_low_confidence_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/view.ts").write_text("export const view = 1;\n", encoding="utf-8")
            graph = build_repository_graph(root)["repository_graph"]

        file_node = next(item for item in graph["files"] if item["path"] == "src/pkg/view.ts")
        self.assertEqual(file_node["confidence"], "low")
        self.assertEqual(file_node["freshness"], "current")
        self.assertEqual(file_node["unknown_reason"], "unsupported_language_uses_file_heuristic")
        symbol = next(item for item in graph["symbols"] if item["path"] == "src/pkg/view.ts")
        self.assertEqual(symbol["confidence"], "low")
        self.assertEqual(symbol["freshness"], "current")


if __name__ == "__main__":
    unittest.main()
