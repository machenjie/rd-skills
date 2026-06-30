from __future__ import annotations

import importlib.util
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


VALIDATOR_PATH = ROOT / "scripts" / "validate-repository-graph.py"
_SPEC = importlib.util.spec_from_file_location("validate_repository_graph_under_test", VALIDATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(VALIDATOR)


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

    def test_invalid_node_freshness_fails(self) -> None:
        graph = _valid_graph()
        graph["repository_graph"]["files"][0]["freshness"] = "fresh"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(any("files[0].freshness must be one of" in error for error in errors), errors)

    def test_invalid_node_confidence_fails(self) -> None:
        graph = _valid_graph()
        graph["repository_graph"]["files"][0]["confidence"] = "certain"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(any("files[0].confidence must be one of" in error for error in errors), errors)

    def test_invalid_edge_type_fails(self) -> None:
        graph = _valid_graph()
        graph["repository_graph"]["edges"][0]["edge_type"] = "links"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(any("edges[0].edge_type must be one of" in error for error in errors), errors)

    def test_business_semantic_edge_type_is_allowed(self) -> None:
        graph = _valid_graph()
        edge = graph["repository_graph"]["edges"][0]
        edge["edge_type"] = "rule_enforced_by"
        edge["extractor"] = "business_semantic_graph"
        edge["evidence"]["edge_type"] = "rule_enforced_by"
        edge["evidence"]["extractor"] = "business_semantic_graph"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertFalse(errors, errors)

    def test_business_semantic_graph_edge_is_selector_not_fact(self) -> None:
        graph = _valid_graph()
        edge = graph["repository_graph"]["edges"][0]
        edge["edge_type"] = "rule_enforced_by"
        edge["extractor"] = "business_semantic_graph"
        edge["evidence"]["edge_type"] = "rule_enforced_by"
        edge["evidence"]["extractor"] = "business_semantic_graph"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertFalse(errors, errors)
        self.assertEqual(edge["extractor"], "business_semantic_graph")
        self.assertNotEqual(edge["evidence"].get("evidence_class"), "FACT")

    def test_unknown_edge_type_requires_unknown_reason(self) -> None:
        graph = _valid_graph()
        edge = graph["repository_graph"]["edges"][0]
        edge["edge_type"] = "unknown"
        edge["evidence"]["edge_type"] = "unknown"
        edge.pop("unknown_reason", None)
        edge["evidence"].pop("unknown_reason", None)

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(
            any("edges[0].unknown_reason is required when edge_type is unknown" in error for error in errors),
            errors,
        )

    def test_generated_artifact_without_source_of_truth_requires_low_confidence(self) -> None:
        graph = _valid_graph()
        item = graph["repository_graph"]["generated_artifacts"][0]
        item["source_of_truth"] = []
        item["source_path"] = ""
        item["confidence"] = "medium"
        item.pop("unknown_reason", None)

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(any("confidence must be low/unknown" in error for error in errors), errors)
        self.assertTrue(any("unknown_reason is required" in error for error in errors), errors)

    def test_generated_artifact_with_edit_source_policy_requires_source_of_truth(self) -> None:
        graph = _valid_graph()
        item = graph["repository_graph"]["generated_artifacts"][0]
        item["source_of_truth"] = []
        item["source_path"] = ""
        item["confidence"] = "low"
        item["unknown_reason"] = "generated_source_of_truth_unknown"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(
            any("source_of_truth is required when edit_policy is edit source / do not edit generated" in error for error in errors),
            errors,
        )

    def test_evidence_top_level_mismatch_fails(self) -> None:
        graph = _valid_graph()
        graph["repository_graph"]["files"][0]["evidence"]["freshness"] = "stale"

        errors = VALIDATOR.validate_repository_graph(graph)

        self.assertTrue(any("files[0].freshness must match evidence.freshness" in error for error in errors), errors)


def _valid_graph() -> dict[str, object]:
    file_evidence = {
        "node_id": "src/app.py",
        "path": "src/app.py",
        "node_type": "file",
        "language": "python",
        "extractor": "python_symbol_extractor",
        "source_hash": "a" * 64,
        "freshness": "current",
        "confidence": "high",
        "generated_artifact": False,
        "last_indexed_at": "2026-06-25T00:00:00Z",
    }
    return {
        "repository_graph": {
            "schema_version": 2,
            "repo_hash": "repo",
            "indexed_at": "2026-06-25T00:00:00Z",
            "created_at": "2026-06-25T00:00:00Z",
            "commit_sha": None,
            "freshness": {"repo_hash": "repo", "created_at": "2026-06-25T00:00:00Z"},
            "files": [
                {
                    "path": "src/app.py",
                    "kind": "python",
                    "role": "source",
                    "symbols": [],
                    "references": [],
                    **file_evidence,
                    "evidence": dict(file_evidence),
                }
            ],
            "edges": [
                {
                    "from": "src/app.py",
                    "to": "tests/test_app.py",
                    "type": "test_reference",
                    "edge_type": "tests",
                    "confidence": "medium",
                    "freshness": "unknown",
                    "extractor": "test_graph",
                    "evidence": {
                        "edge_type": "tests",
                        "from_node": "src/app.py",
                        "to_node": "tests/test_app.py",
                        "confidence": "medium",
                        "freshness": "unknown",
                        "extractor": "test_graph",
                    },
                }
            ],
            "symbols": [
                {
                    "name": "build",
                    "kind": "function",
                    "path": "src/app.py",
                    "line": 1,
                    "visibility": "public",
                    "language": "python",
                    "confidence": "high",
                    "evidence": {
                        **file_evidence,
                        "node_id": "src/app.py::build",
                        "symbol": "build",
                        "node_type": "function",
                    },
                    "source_hash": "a" * 64,
                    "freshness": "current",
                    "extractor": "python_symbol_extractor",
                }
            ],
            "module_boundaries": [],
            "ownership": [],
            "generated_artifacts": [
                {
                    "generated_path": "reports/",
                    "source_path": "scripts/eval-routing.py",
                    "source_of_truth": ["scripts/eval-routing.py"],
                    "edit_policy": "edit source / do not edit generated",
                    "confidence": "medium",
                    "freshness": "not_applicable",
                    "extractor": "generated_artifact_graph",
                }
            ],
            "validation_candidates": [{"command": "python3 -m unittest discover -s tests", "scope": "module"}],
        }
    }


if __name__ == "__main__":
    unittest.main()
