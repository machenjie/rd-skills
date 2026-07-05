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


class ContextPackValidationCandidateTests(unittest.TestCase):
    def test_changed_path_maps_to_related_test_and_broker_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/repository_intelligence/cache").mkdir(parents=True)
            (root / "src/repository_intelligence/cache/repo_hash.py").write_text("def hash_repo():\n    return 'x'\n", encoding="utf-8")
            (root / "tests/repository_intelligence").mkdir(parents=True)
            (root / "tests/repository_intelligence/test_repo_hash.py").write_text("def test_hash_repo():\n    pass\n", encoding="utf-8")
            graph = build_repository_graph(root)
            pack = build_context_pack(
                graph,
                "repository intelligence validation",
                ["src/repository_intelligence/cache/repo_hash.py"],
                root,
                graph_path="/tmp/graph.json",
                context_pack_path="/tmp/pack.json",
            )["task_context_pack"]

        commands = {item["command"] for item in pack["validation_candidates"]}
        self.assertIn("python3 -m unittest discover -s tests/repository_intelligence", commands)
        self.assertIn("python3 scripts/validate-context-pack.py --context-pack /tmp/pack.json", commands)
        self.assertIn("tests/repository_intelligence/test_repo_hash.py", {item["path"] for item in pack["related_tests"]})

    def test_unknown_changed_path_keeps_residual_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            graph = build_repository_graph(root)
            pack = build_context_pack(graph, "unknown path", ["unknown/file.bin"], root)["task_context_pack"]

        self.assertIn("unknown_validation_mapping", {item["kind"] for item in pack["residual_risk"]})


if __name__ == "__main__":
    unittest.main()
