from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validation_utils import load_yaml_file


FIXTURE = ROOT / "evals" / "skill-efficacy" / "fixtures" / "over-under-routing.yaml"


class OverUnderRoutingFixtureTests(unittest.TestCase):
    def test_fixture_contains_required_cases(self) -> None:
        data = load_yaml_file(FIXTURE)
        cases = {case["id"]: case for case in data["cases"]}
        self.assertEqual(
            set(cases),
            {
                "l1-isolated-backend-bug-fix",
                "logging-change-routes-logging-design",
                "registry-capability-edit-routes-efficacy",
                "memory-stale-context-routes-governance",
                "graph-source-truth-routes-repository-graph",
                "validation-stale-routes-broker",
                "adapter-unsupported-event-routes-protocol",
                "simple-docs-typo-no-over-routing",
            },
        )

    def test_each_case_has_budgeted_references_and_gate_reasons(self) -> None:
        data = load_yaml_file(FIXTURE)
        for case in data["cases"]:
            with self.subTest(case=case["id"]):
                expected = case["expected"]
                self.assertTrue(expected["selected_skills_include"])
                self.assertTrue(expected["selected_skills_exclude"])
                self.assertTrue(expected["selected_capabilities_include"])
                self.assertTrue(expected["capability_skill_map"])
                self.assertLessEqual(
                    len(expected["required_references"]),
                    expected["required_references_max"],
                )
                self.assertLessEqual(
                    len(expected["required_references"]),
                    expected["context_budget"]["selected_reference_count_max"],
                )
                self.assertIn(
                    expected["context_budget"]["mode"],
                    {"minimal", "single-stage", "staged-plan", "full"},
                )
                for reference in expected["required_references"]:
                    self.assertTrue((ROOT / reference).is_file(), reference)
                for item in expected["skipped_references"]:
                    self.assertTrue(item["reference"])
                    self.assertTrue(item["reason"])
                for item in expected["required_quality_gates"]:
                    self.assertTrue(item["gate"])
                    self.assertTrue(item["reason"])
                for item in expected["skipped_quality_gates"]:
                    self.assertTrue(item["gate"])
                    self.assertTrue(item["reason"])

    def test_named_routing_expectations_are_explicit(self) -> None:
        data = load_yaml_file(FIXTURE)
        cases = {case["id"]: case["expected"] for case in data["cases"]}
        self.assertIn(
            "logging-design-gate",
            cases["logging-change-routes-logging-design"]["selected_skills_include"],
        )
        self.assertIn(
            "skill-efficacy-benchmark",
            cases["registry-capability-edit-routes-efficacy"]["selected_capabilities_include"],
        )
        self.assertIn(
            "project-memory-governance",
            cases["memory-stale-context-routes-governance"]["selected_capabilities_include"],
        )
        self.assertIn(
            "repository-graph-analysis",
            cases["graph-source-truth-routes-repository-graph"]["selected_capabilities_include"],
        )
        self.assertIn(
            "validation-broker",
            cases["validation-stale-routes-broker"]["selected_capabilities_include"],
        )
        self.assertIn(
            "executor-adapter-protocol",
            cases["adapter-unsupported-event-routes-protocol"]["selected_capabilities_include"],
        )
        self.assertIn(
            "security-privacy-gate",
            cases["simple-docs-typo-no-over-routing"]["selected_skills_exclude"],
        )


if __name__ == "__main__":
    unittest.main()
