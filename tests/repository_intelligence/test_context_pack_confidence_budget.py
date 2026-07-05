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
from validation_broker.command_resolver import resolve_validation_plan


class ContextPackConfidenceBudgetTests(unittest.TestCase):
    def test_budget_prioritizes_current_high_confidence_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/app.py").write_text("def app():\n    return 1\n", encoding="utf-8")
            (root / "src/pkg/view.ts").write_text("export const view = 1;\n", encoding="utf-8")
            graph = build_repository_graph(root)
            pack = build_context_pack(
                graph,
                "app view change",
                ["src/pkg/view.ts"],
                root,
                max_files=2,
                budget_mode="minimal",
            )["task_context_pack"]

        self.assertEqual(pack["anti_bloat_decision"]["budget_mode"], "minimal")
        selected = {item["path"]: item for item in pack["selected_files"]}
        self.assertEqual(selected["src/pkg/app.py"]["confidence"], "high")
        self.assertEqual(selected["src/pkg/view.ts"]["confidence"], "low")
        skipped = {item["path"] for item in pack["skipped_graph_nodes"]}
        self.assertIn("src/pkg/view.ts", skipped)
        closure_paths = {item["path"] for item in pack["closure_evidence"]}
        self.assertNotIn("src/pkg/view.ts", closure_paths)

    def test_current_affected_test_mapping_is_strong_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/app.py").write_text("def app():\n    return 1\n", encoding="utf-8")
            (root / "tests/pkg").mkdir(parents=True)
            (root / "tests/pkg/test_app.py").write_text("def test_app():\n    pass\n", encoding="utf-8")
            graph = build_repository_graph(root)
            pack = build_context_pack(graph, "app tests", ["src/pkg/app.py"], root)["task_context_pack"]

        candidate = next(item for item in pack["graph_validation_candidates"] if item["changed_path"] == "src/pkg/app.py")
        self.assertEqual(candidate["candidate_tests"], ["tests/pkg/test_app.py"])
        self.assertEqual(candidate["freshness"], "current")
        self.assertEqual(candidate["strength"], "strong")

    def test_stale_or_unknown_affected_test_mapping_is_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            source = root / "src/pkg/app.py"
            source.write_text("def app():\n    return 1\n", encoding="utf-8")
            (root / "tests/pkg").mkdir(parents=True)
            (root / "tests/pkg/test_app.py").write_text("def test_app():\n    pass\n", encoding="utf-8")
            graph = build_repository_graph(root)
            source.write_text("def app():\n    return 2\n", encoding="utf-8")
            stale_pack = build_context_pack(graph, "app tests", ["src/pkg/app.py"], root)["task_context_pack"]
            unknown_pack = build_context_pack(graph, "unknown tests", ["unknown/file.bin"], root)["task_context_pack"]

        stale_candidate = next(
            item for item in stale_pack["graph_validation_candidates"] if item["changed_path"] == "src/pkg/app.py"
        )
        self.assertEqual(stale_candidate["freshness"], "stale")
        self.assertEqual(stale_candidate["strength"], "conservative")
        unknown_candidate = next(
            item for item in unknown_pack["graph_validation_candidates"] if item["changed_path"] == "unknown/file.bin"
        )
        self.assertEqual(unknown_candidate["strength"], "conservative")
        self.assertEqual(unknown_candidate["candidate_tests"], [])

    def test_validation_broker_consumes_only_strong_graph_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            source = root / "src/pkg/app.py"
            source.write_text("def app():\n    return 1\n", encoding="utf-8")
            (root / "tests/pkg").mkdir(parents=True)
            (root / "tests/pkg/test_app.py").write_text("def test_app():\n    pass\n", encoding="utf-8")
            graph = build_repository_graph(root)
            current_pack = build_context_pack(graph, "app tests", ["src/pkg/app.py"], root)
            source.write_text("def app():\n    return 2\n", encoding="utf-8")
            stale_pack = build_context_pack(graph, "app tests", ["src/pkg/app.py"], root)

        current_plan = resolve_validation_plan(["src/pkg/app.py"], repo_context=current_pack)
        stale_plan = resolve_validation_plan(["src/pkg/app.py"], repo_context=stale_pack)
        current_commands = {item["command"] for item in current_plan["recommended_commands"]}
        stale_commands = {item["command"] for item in stale_plan["recommended_commands"]}
        self.assertIn("python3 -m unittest discover -s tests/pkg", current_commands)
        self.assertNotIn("python3 -m unittest discover -s tests/pkg", stale_commands)


if __name__ == "__main__":
    unittest.main()
