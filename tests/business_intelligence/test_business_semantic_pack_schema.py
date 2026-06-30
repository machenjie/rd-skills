from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

VALIDATOR_PATH = ROOT / "scripts" / "validate-business-semantic-pack.py"
_SPEC = importlib.util.spec_from_file_location("validate_business_semantic_pack_under_test", VALIDATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = VALIDATOR
_SPEC.loader.exec_module(VALIDATOR)

SAMPLE_DIR = ROOT / "evals" / "business-semantic" / "samples"


class BusinessSemanticPackSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (VALIDATOR.SCHEMA_DIR / "business-semantic-pack.v1.schema.json").open(encoding="utf-8") as handle:
            cls.schema = json.load(handle)

    def test_valid_bsp_passes(self) -> None:
        self.assertEqual(self._errors("valid-business-semantic-pack.json"), [])

    def test_fact_from_memory_fails(self) -> None:
        self.assert_errors("invalid-fact-from-memory.json", "FACT evidence cannot rely on memory_projection")

    def test_fact_from_graph_fails(self) -> None:
        self.assert_errors("invalid-fact-from-graph.json", "FACT evidence cannot rely on repository_graph")

    def test_selected_reference_without_reason_fails(self) -> None:
        self.assert_errors("invalid-selected-reference-no-reason.json", "reason")

    def test_rule_without_owner_fails(self) -> None:
        self.assert_errors("invalid-rule-missing-owner.json", "owner")

    def test_rule_without_enforcement_path_fails(self) -> None:
        self.assert_errors("invalid-rule-missing-enforcement-path.json", "authoritative_enforcement_paths")

    def test_rule_empty_reason_codes_fails(self) -> None:
        self.assert_errors("invalid-rule-empty-reason-codes.json", "reason_codes")

    def test_rule_empty_entry_points_fails(self) -> None:
        self.assert_errors("invalid-rule-empty-entry-points.json", "entry_points")

    def test_workflow_without_forbidden_transition_fails(self) -> None:
        self.assert_errors("invalid-workflow-no-forbidden-transition.json", "forbidden")

    def assert_errors(self, sample_name: str, expected: str) -> None:
        errors = self._errors(sample_name)
        self.assertTrue(errors, f"{sample_name} unexpectedly passed")
        joined = "\n".join(errors)
        self.assertIn(expected, joined)

    def _errors(self, sample_name: str) -> list[str]:
        with (SAMPLE_DIR / sample_name).open(encoding="utf-8") as handle:
            sample = json.load(handle)
        errors = VALIDATOR._schema_errors(self.schema, sample)
        VALIDATOR._validate_bsp_semantics(sample, sample_name, errors)
        return errors


if __name__ == "__main__":
    unittest.main()
