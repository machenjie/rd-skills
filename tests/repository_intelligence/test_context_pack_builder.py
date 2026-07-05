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


class ContextPackBuilderTests(unittest.TestCase):
    def test_builds_bounded_pack_with_source_tests_validation_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/hook-runtime/scripts").mkdir(parents=True)
            (root / "src/hook-runtime/scripts/changeforge_runtime_adapters.py").write_text(
                "def adapt_event(event):\n    return event\n", encoding="utf-8"
            )
            (root / "scripts").mkdir()
            (root / "scripts/build.py").write_text("print('build')\n", encoding="utf-8")
            (root / "scripts/validate-hooks.py").write_text("print('hooks')\n", encoding="utf-8")
            (root / "tests/hook_runtime").mkdir(parents=True)
            (root / "tests/hook_runtime/test_changeforge_runtime_adapters.py").write_text(
                "def test_adapt_event():\n    pass\n", encoding="utf-8"
            )
            graph = build_repository_graph(root)
            context_pack = build_context_pack(
                graph,
                "hook runtime adapter refactor",
                ["src/hook-runtime/scripts/changeforge_runtime_adapters.py"],
                root,
                max_files=8,
                graph_path="/tmp/graph.json",
                context_pack_path="/tmp/pack.json",
            )["task_context_pack"]

        self.assertEqual(context_pack["source_of_truth"][0]["path"], "src/hook-runtime/scripts/changeforge_runtime_adapters.py")
        self.assertLessEqual(len(context_pack["relevant_files"]), 8)
        commands = {candidate["command"] for candidate in context_pack["validation_candidates"]}
        self.assertIn("python3 scripts/validate-hooks.py", commands)
        self.assertIn("python3 scripts/build.py --profile recommended", commands)
        self.assertIn("python3 scripts/validate-repository-graph.py --graph /tmp/graph.json", commands)
        self.assertIn("python3 scripts/validate-context-pack.py --context-pack /tmp/pack.json", commands)
        self.assertTrue(context_pack["freshness_markers"]["repo_hash"])
        self.assertTrue(context_pack["freshness_markers"]["artifact_hash"])
        self.assertTrue(any(item["path"] == "dist/" for item in context_pack["excluded_context"]))

    def test_missing_graph_and_output_paths_use_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            graph = build_repository_graph(root)
            context_pack = build_context_pack(graph, "source change", ["src/app.py"], root)["task_context_pack"]

        commands = {candidate["command"] for candidate in context_pack["validation_candidates"]}
        self.assertIn(
            "python3 scripts/validate-repository-graph.py --graph <repository_graph_json>",
            commands,
        )
        self.assertIn(
            "python3 scripts/validate-context-pack.py --context-pack <task_context_pack_json>",
            commands,
        )


if __name__ == "__main__":
    unittest.main()
