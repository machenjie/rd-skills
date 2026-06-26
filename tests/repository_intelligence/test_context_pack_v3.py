from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.repo_indexer import build_repository_graph
from repository_intelligence.packaging.context_pack_builder import build_context_pack
from repository_intelligence.packaging.context_pack_renderer import render_context_pack_markdown


def _validate_context_pack(document: dict[str, Any]) -> list[str]:
    spec = importlib.util.spec_from_file_location(
        "validate_context_pack_script",
        ROOT / "scripts" / "validate-context-pack.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_context_pack(document)


class ContextPackV3Tests(unittest.TestCase):
    def test_v3_runtime_pack_adds_context_control_jit_reads_and_artifact_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/pkg").mkdir(parents=True)
            (root / "src/pkg/app.py").write_text("def app():\n    return 1\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/guide.md").write_text("# Guide\nUse `src/pkg/app.py`.\n", encoding="utf-8")
            graph = build_repository_graph(root)
            document = build_context_pack(
                graph,
                "runtime context control app guide",
                ["src/pkg/app.py", "docs/guide.md"],
                root,
                max_files=99,
                max_symbols=99,
                context_budget_tokens=9999,
                budget_mode="single-stage",
                budget_profile="runtime",
                graph_path="/tmp/graph.json",
                context_pack_path="/tmp/pack.json",
            )

        pack = document["task_context_pack"]
        self.assertEqual(pack["schema_version"], 3)
        self.assertEqual(pack["context_control"]["budget_mode"], "single-stage")
        self.assertEqual(pack["context_control"]["budget_profile"], "runtime")
        self.assertEqual(pack["context_control"]["max_file_count"], 16)
        self.assertEqual(pack["context_control"]["max_symbol_count"], 48)
        self.assertEqual(pack["context_control"]["context_budget_tokens"], 900)
        targeted = {item["path"]: item for item in pack["jit_retrieval_plan"]["targeted_reads"]}
        self.assertEqual(targeted["src/pkg/app.py"]["line_hint"], "1-2")
        self.assertEqual(targeted["src/pkg/app.py"]["read_policy"], "read_slice")
        self.assertEqual(targeted["docs/guide.md"]["line_hint"], "line 1")
        self.assertEqual(targeted["docs/guide.md"]["read_policy"], "read_heading_only")
        self.assertIn("dist/", {item["path"] for item in pack["jit_retrieval_plan"]["forbidden_reads"]})
        self.assertEqual(pack["artifact_policy"]["full_graph_dump"], "forbidden")
        self.assertEqual(_validate_context_pack(document), [])

        markdown = render_context_pack_markdown(document)
        self.assertIn("## Context Control", markdown)
        self.assertIn("## JIT Retrieval Plan", markdown)
        self.assertIn("## Artifact Policy", markdown)
        self.assertIn("## Omitted Nodes", markdown)

    def test_validator_keeps_v2_compatibility_without_v3_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            document = build_context_pack(build_repository_graph(root), "legacy pack", ["src/app.py"], root)

        legacy = copy.deepcopy(document)
        legacy_pack = legacy["task_context_pack"]
        legacy_pack["schema_version"] = 2
        legacy_pack.pop("context_control", None)
        legacy_pack.pop("jit_retrieval_plan", None)
        legacy_pack.pop("artifact_policy", None)
        self.assertEqual(_validate_context_pack(legacy), [])

    def test_validator_rejects_unsafe_or_over_budget_v3_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            document = build_context_pack(build_repository_graph(root), "validator rejects", ["src/app.py"], root)

        over_budget = copy.deepcopy(document)
        over_budget_pack = over_budget["task_context_pack"]
        over_budget_pack["context_control"]["selected_file_count"] = (
            over_budget_pack["context_control"]["max_file_count"] + 1
        )
        self.assertTrue(
            any("selected_file_count must not exceed selected budget" in error for error in _validate_context_pack(over_budget))
        )

        absolute_path = copy.deepcopy(document)
        absolute_path["task_context_pack"]["jit_retrieval_plan"]["targeted_reads"][0]["path"] = "/Users/example/src/app.py"
        self.assertTrue(any("must be repository-relative" in error for error in _validate_context_pack(absolute_path)))

        graph_dump = copy.deepcopy(document)
        graph_dump["task_context_pack"]["artifact_policy"]["full_graph_dump"] = "allowed"
        self.assertTrue(any("artifact_policy.full_graph_dump must be forbidden" in error for error in _validate_context_pack(graph_dump)))

    def test_validator_requires_generated_artifact_forbidden_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/foundation/capabilities/sample").mkdir(parents=True)
            (root / "src/foundation/capabilities/sample/SKILL.md").write_text("# Sample\n", encoding="utf-8")
            document = build_context_pack(
                build_repository_graph(root),
                "generated output boundary",
                ["dist/sample/SKILL.md"],
                root,
            )

        missing_forbidden = copy.deepcopy(document)
        missing_forbidden["task_context_pack"]["jit_retrieval_plan"]["forbidden_reads"] = []
        self.assertTrue(
            any(
                "forbidden_reads must include dist/ or generated-output handling" in error
                for error in _validate_context_pack(missing_forbidden)
            )
        )


if __name__ == "__main__":
    unittest.main()
