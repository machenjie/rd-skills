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


class RepoIndexerSymbolTests(unittest.TestCase):
    def test_indexes_python_markdown_yaml_and_low_confidence_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/helper.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
            (root / "src/pkg/app.py").write_text(
                "\n".join(
                    [
                        "from helper import helper",
                        "VALUE = 1",
                        "class Worker:",
                        "    def run(self):",
                        "        return helper()",
                        "def build():",
                        "    return Worker()",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "src/pkg/broken.py").write_text("def broken(:\n", encoding="utf-8")
            (root / "src/pkg/view.ts").write_text("export const view = 1;\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/guide.md").write_text("---\nname: guide\n---\n# Guide\n", encoding="utf-8")
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

            graph = build_repository_graph(root)["repository_graph"]

        self.assertEqual(graph["schema_version"], 2)
        symbols = {(item["name"], item["kind"], item["path"]) for item in graph["symbols"]}
        self.assertIn(("Worker", "class", "src/pkg/app.py"), symbols)
        self.assertIn(("Worker.run", "method", "src/pkg/app.py"), symbols)
        self.assertIn(("build", "function", "src/pkg/app.py"), symbols)
        self.assertIn(("VALUE", "constant", "src/pkg/app.py"), symbols)
        self.assertIn(("Guide", "heading", "docs/guide.md"), symbols)
        self.assertIn(("sample", "config_key", "src/registry/capabilities.yaml"), symbols)
        low_confidence = [
            item for item in graph["symbols"] if item["path"] == "src/pkg/view.ts" and item["confidence"] == "low"
        ]
        self.assertTrue(low_confidence)
        self.assertTrue(
            any(
                ref.get("kind") == "index_error"
                for file_node in graph["files"]
                if file_node["path"] == "src/pkg/broken.py"
                for ref in file_node["references"]
            )
        )
        edges = {(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]}
        self.assertIn(("src/pkg/app.py", "src/pkg/helper.py", "import"), edges)


if __name__ == "__main__":
    unittest.main()
