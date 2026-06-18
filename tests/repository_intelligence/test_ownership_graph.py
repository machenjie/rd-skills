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


class OwnershipGraphTests(unittest.TestCase):
    def test_records_owner_modules_siblings_and_rejected_dumping_ground(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/repository_intelligence/graph").mkdir(parents=True)
            (root / "src/repository_intelligence/graph/alpha.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
            (root / "src/repository_intelligence/graph/beta.py").write_text("def beta():\n    return 2\n", encoding="utf-8")
            (root / "src/common/helpers").mkdir(parents=True)
            (root / "src/common/helpers/ownerless.py").write_text("def helper():\n    return 3\n", encoding="utf-8")

            graph = build_repository_graph(root)["repository_graph"]

        ownership = {item["path"]: item for item in graph["ownership"]}
        self.assertEqual(ownership["src/repository_intelligence/graph/alpha.py"]["owner_module"], "repository_intelligence")
        self.assertIn("beta.py", ownership["src/repository_intelligence/graph/alpha.py"]["sibling_conventions"])
        rejected = ownership["src/common/helpers/ownerless.py"]["rejected_dumping_ground_candidates"]
        self.assertTrue(rejected)
        modules = {item["owner_module"] for item in graph["module_boundaries"]}
        self.assertIn("repository_intelligence", modules)


if __name__ == "__main__":
    unittest.main()
