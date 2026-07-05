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


class GeneratedArtifactTests(unittest.TestCase):
    def test_generated_dist_path_traces_source_of_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/foundation/capabilities/sample").mkdir(parents=True)
            (root / "src/foundation/capabilities/sample/SKILL.md").write_text("# Sample\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts/build.py").write_text("print('build')\n", encoding="utf-8")
            graph = build_repository_graph(root)
            pack = build_context_pack(
                graph,
                "generated artifact boundary",
                ["dist/sample/SKILL.md"],
                root,
            )["task_context_pack"]

        self.assertTrue(pack["generated_artifacts"])
        self.assertFalse(any(item["path"].startswith("dist/") for item in pack["source_of_truth"]))
        self.assertIn("generated_artifact_changed", {item["kind"] for item in pack["residual_risk"]})


if __name__ == "__main__":
    unittest.main()
