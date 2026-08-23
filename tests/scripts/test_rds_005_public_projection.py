#!/usr/bin/env python3
"""Focused RDS-005 public execution and evidence projection contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UTILS = _load_module("rds005_validation_utils", SCRIPTS / "validation_utils.py")
TASK_VALIDATOR = _load_module(
    "rds005_validate_task_contracts", SCRIPTS / "validate-task-contracts.py"
)


class Rds005PublicProjectionTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        self.execution = self.core["execution_level_contract"]
        self.public = self.execution["projection"]["public_task_extension"]
        self.references = (
            ROOT / "src/control-skills/engineering-control-plane/references"
        )

    def test_l1_through_l5_public_projection_is_decision_only(self) -> None:
        self.assertEqual(
            {
                "version": "execution-level/v2",
                "ordered_labels": ["Level", "Basis", "L5 Evidence"],
                "line_fields": {
                    "Level": [
                        "requested",
                        "automatic",
                        "minimum",
                        "default",
                        "effective",
                        "edit",
                    ],
                    "Basis": [
                        "source",
                        "triggers",
                        "l1",
                        "l2",
                        "l5",
                        "confirmation",
                        "unresolved",
                    ],
                    "L5 Evidence": ["when", "requires"],
                },
            },
            self.public,
        )

        forbidden = (
            "Claims:",
            "Gaps:",
            "Identity:",
            "History:",
            "claim_manifest",
            "gap_manifest",
            "identity_manifest",
            "command_hash",
            "path_digest",
            "sha256-b64u:",
        )
        for surface in (
            "direct-task-template.md",
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        ):
            with self.subTest(surface=surface):
                text = (self.references / surface).read_text(encoding="utf-8")
                spans, errors = UTILS.public_execution_template_spans(
                    text, self.core, surface
                )
                self.assertEqual([], errors)
                self.assertTrue(spans)
                for start, end in spans:
                    block = text[start:end]
                    for term in forbidden:
                        self.assertNotIn(term, block)
                    self.assertIn(
                        "requested=unspecified / L1 / L2 / L3 / L4 / L5", block
                    )
                    self.assertIn("automatic=L1 / L2 / L3 / L4 / L5", block)
                    self.assertIn("minimum=L1 / L2 / L3 / L4 / L5", block)
                    self.assertIn("default=L3", block)
                    self.assertIn("effective=L1 / L2 / L3 / L4 / L5", block)
                    self.assertIn("source=user_fact:<anchor> / analysis_handoff:<anchor>", block)
                    self.assertIn(
                        'unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]',
                        block,
                    )
                    self.assertIn("when=effective L5 only", block)

    def test_legacy_validation_machinery_is_absent_from_core_and_active_source(
        self,
    ) -> None:
        retired_core_fields = {
            "legacy_internal_validation",
            "validation_identity",
            "validation_path_contract",
            "validation_loop",
        }
        self.assertTrue(retired_core_fields.isdisjoint(self.execution))
        self.assertEqual(
            {
                "same_path_failure_limit": 2,
                "retry_change_dimensions": [
                    "hypothesis",
                    "material",
                    "gap",
                    "transition",
                ],
                "unchanged_retry_after_limit": "return-to-main-or-block",
                "third_unchanged_retry": "forbidden",
            },
            self.execution["retry_policy"],
        )

        runtime = UTILS.execution_level_runtime_payload(self.core)
        self.assertEqual(self.execution["retry_policy"], runtime["retry_policy"])
        runtime_text = json.dumps(runtime, sort_keys=True)
        for term in (
            "claim_manifest",
            "gap_manifest",
            "identity_manifest",
            "adapter_registry",
            "validator_source_hashes",
            "validation_path_id",
            "completed_path",
            "failed_attempt",
            "evidence_transition",
        ):
            self.assertNotIn(term, runtime_text)

        for retired_api in (
            "canonical_claim_manifest",
            "canonical_gap_manifest",
            "canonical_evidence_transition",
            "canonical_validation_identity",
            "canonical_validation_identity_manifest_digest",
            "collect_visible_validation_identity_sources",
            "validation_identity_handoff_errors",
            "validation_attempt_errors",
            "execution_public_version_registry",
        ):
            with self.subTest(retired_api=retired_api):
                self.assertFalse(hasattr(UTILS, retired_api))

        forbidden_source_terms = (
            "legacy_internal_validation",
            "validation_path_contract",
            "validation_identity_manifest",
            "validation_claim_manifest",
            "distinct_gap_manifest",
            "canonical_validation_identity",
            "canonical_claim_manifest",
            "canonical_gap_manifest",
            "validation_attempt_errors",
        )
        for relative in (
            "scripts/validation_utils.py",
            "scripts/fixture_capsule_contract.py",
            "scripts/eval-pressure-behavior.py",
            "src/control-model/core-contracts.json",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for term in forbidden_source_terms:
                with self.subTest(relative=relative, term=term):
                    self.assertNotIn(term, text)

    def test_level_safety_retry_closure_and_l5_contracts_remain(self) -> None:
        execution = self.execution
        self.assertEqual(
            ["unspecified", "L1", "L2", "L3", "L4", "L5"],
            execution["requested_values"],
        )
        self.assertEqual(
            ["L1", "L2", "L3", "L4", "L5"], execution["dynamic_levels"]
        )
        self.assertEqual("L3", execution["default_level"])
        self.assertEqual(
            {
                "floor": "L4",
                "edit_status": "blocked",
                "provisional": True,
                "required_fields": [
                    "candidate_l4_predicate",
                    "missing_fact",
                    "plausible_impact_path",
                    "material_consequence",
                ],
                "rule": (
                    "only a concrete critical unknown with every required field "
                    "receives provisional L4 and blocks editing until resolved; "
                    "generic possibility is a Proof Limit"
                ),
            },
            execution["critical_unknown"],
        )
        fallback = execution["integrity_fallback"]
        self.assertEqual(["missing", "malformed", "duplicate"], fallback["inputs"])
        self.assertFalse(fallback["partial_computation"])
        self.assertEqual("blocked", fallback["edit_status"])

        self.assertEqual(
            ["hypothesis", "material", "gap", "transition"],
            execution["retry_policy"]["retry_change_dimensions"],
        )
        self.assertEqual(2, execution["retry_policy"]["same_path_failure_limit"])
        self.assertEqual(
            "return-to-main-or-block",
            execution["retry_policy"]["unchanged_retry_after_limit"],
        )
        self.assertEqual(
            "forbidden", execution["retry_policy"]["third_unchanged_retry"]
        )
        for control in (
            "authority and sandbox controls",
            "repository safety",
            "production and destructive authorization",
            "formal evidence when formal readiness is declared",
            "post-edit targeted validation",
            "independent implementation review",
            "current scoped completion evidence",
        ):
            self.assertIn(control, execution["non_bypassable"])

        l5 = next(level for level in execution["levels"] if level["id"] == "L5")
        for obligation in (
            "independent pre-implementation review",
            "strong safety and applicability proof",
            "declared-scope comprehensive negative and failure proof",
            "exhaustive final review",
        ):
            self.assertIn(obligation, l5["obligations"])

        completion = self.core["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]
        self.assertTrue(completion["independent_owner_required"])
        self.assertEqual("task-agent", completion["implementation_owner_role"])
        self.assertEqual("review-agent", completion["independent_review_owner"])
        self.assertEqual("latest-material-edit", completion["latest_material_edit_claim"])
        self.assertEqual("validation-passed", completion["validation_claim"])

    def test_evidence_ledger_uses_the_visible_user_core(self) -> None:
        expected = [
            "Claim",
            "Owner",
            "Artifact",
            "Command",
            "Result",
            "Freshness",
            "Scope",
            "Proof Limit",
            "State",
        ]
        self.assertEqual(expected, self.core["visible_evidence_contract"]["fields"])
        header = "| " + " | ".join(expected) + " |"
        for surface in (
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        ):
            with self.subTest(surface=surface):
                text = (self.references / surface).read_text(encoding="utf-8")
                self.assertIn(header, text)
                self.assertNotIn("| Evidence ID | Task ID |", text)

    def test_conditional_test_evidence_is_one_exact_public_projection(self) -> None:
        conditional_test_evidence = self.core["visible_evidence_contract"][
            "conditional_test_evidence"
        ]
        projection = UTILS.conditional_test_evidence_projection_text(
            conditional_test_evidence
        )
        targets = [
            "direct-task-template.md",
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        ]
        self.assertEqual(
            {
                "schema_version": 1,
                "claim_values": [
                    "test-approach-selected",
                    "red-proof",
                    "green-proof",
                ],
                "record_only_when_applicable": True,
                "separate_stage": False,
                "unavailable_proof_rule": "never-fabricate",
                "projection_targets": targets,
                "projection_text": projection,
            },
            conditional_test_evidence,
        )
        for surface in targets:
            with self.subTest(surface=surface):
                normalized = " ".join(
                    (self.references / surface).read_text(encoding="utf-8").split()
                )
                self.assertEqual(1, normalized.count(projection))

    def test_public_contract_rejects_legacy_field_reintroduction(self) -> None:
        mutated = copy.deepcopy(self.core)
        public = mutated["execution_level_contract"]["projection"][
            "public_task_extension"
        ]
        public["ordered_labels"].insert(2, "Claims")
        public["line_fields"]["Claims"] = ["ids", "digest"]
        errors = UTILS.validate_core_contracts(mutated)
        self.assertTrue(
            any("public task extension" in error for error in errors), errors
        )

        mutated = copy.deepcopy(self.core)
        mutated["visible_evidence_contract"]["fields"].insert(0, "Evidence ID")
        errors = UTILS.validate_core_contracts(mutated)
        self.assertTrue(any("Evidence Ledger fields" in error for error in errors), errors)

        self.assertEqual([], TASK_VALIDATOR.validate_contracts(self.references))


if __name__ == "__main__":
    unittest.main()
