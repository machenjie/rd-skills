from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-skill-professionalism.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "eval_skill_professionalism_empty_sections",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SkillProfessionalismEmptySectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_empty_section_records_error_and_loses_section_points(self) -> None:
        body = """# example

## Registry Trigger

**Use when**

- example trigger

**Do not use when**

- example anti-trigger

## Skill Role

Focused Layer 3 Skill for `task-agent`.

## High-Value Rules

- Preserve the owning invariant.
- Verify the current source.

## Anti-Patterns

<!-- Placeholder text is not authored content. -->

## Targeted References

- Load none by default.
"""
        entry = {
            "name": "example",
            "path": "example",
            "role_support": ["task-agent"],
            "trigger_signals": ["example trigger"],
            "anti_trigger_signals": ["example anti-trigger"],
            "required_inputs": ["current contract"],
            "output_contract": ["decision"],
            "escalation_signals": ["unknown ownership"],
            "reference_index": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "example" / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nname: example\ndescription: Example trigger and boundary.\n---\n\n"
                + body,
                encoding="utf-8",
            )
            with mock.patch.object(self.module, "ROOT", root):
                result = self.module._evaluate("foundation", entry)

        self.assertEqual("fail", result.status)
        self.assertEqual(88, result.authoring_score)
        self.assertTrue(
            any(
                "empty Markdown sections: Anti-Patterns" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_optional_foundation_section_does_not_bleed_into_required_content(self) -> None:
        body = """# example

## Registry Trigger

Trigger text.

## Skill Role

Role text.

## Inputs

- Optional sentinel.

## High-Value Rules

- First rule.
- Second rule.

## Anti-Patterns

- Named failure.

## Targeted References

- No reference.
"""
        sections = self.module._sections(body, self.module.FOUNDATION_SECTIONS)
        self.assertEqual("Role text.", sections["Skill Role"])
        self.assertNotIn("Optional sentinel", sections["Skill Role"])
        self.assertNotIn("Optional sentinel", sections["High-Value Rules"])

    def test_coverage_matrix_separates_authoring_and_release_gate_status(self) -> None:
        matrix = self.module.build_coverage_matrix()
        self.assertEqual(3, matrix["schema_version"])
        self.assertEqual(0, matrix["gate_summary"]["fail_count"])
        uncovered = next(
            row for row in matrix["rows"] if row["name"] == "user-role-identification"
        )
        self.assertEqual("pass", uncovered["authoring_status"])
        self.assertEqual("not-required", uncovered["coverage_gate_status"])
        self.assertFalse(uncovered["coverage_states"]["behavior_covered"])
        self.assertNotIn("status", uncovered)

    def test_release_critical_targets_have_distinct_coverage_evidence(self) -> None:
        matrix = self.module.build_coverage_matrix()
        by_name = {row["name"]: row for row in matrix["rows"]}
        for name in (
            "security-privacy-gate",
            "reliability-observability-gate",
            "logging-design-gate",
            "architecture-impact-reviewer",
        ):
            with self.subTest(name=name):
                row = by_name[name]
                self.assertEqual("pass", row["coverage_gate_status"])
                self.assertTrue(row["coverage_states"]["negative_route_covered"])
                self.assertTrue(row["coverage_states"]["behavior_covered"])
                self.assertTrue(row["coverage_states"]["release_critical_covered"])
        self.assertTrue(by_name["security-privacy-gate"]["coverage_states"]["pressure_covered"])
        self.assertFalse(
            by_name["architecture-impact-reviewer"]["coverage_states"]["pressure_covered"]
        )

    def test_domain_skills_require_ordinary_routing_evidence(
        self,
    ) -> None:
        matrix = self.module.build_coverage_matrix()
        self.assertEqual(10, matrix["gate_summary"]["required_skill_count"])
        self.assertEqual(10, matrix["gate_summary"]["pass_count"])
        domain_names = {
            "ai-product-extension",
            "bigdata-product-extension",
            "iot-embedded-extension",
            "low-level-systems-extension",
            "payment-trading-extension",
            "web3-product-extension",
        }
        by_name = {row["name"]: row for row in matrix["rows"]}
        positive_case_ids: list[str] = []
        negative_case_ids: list[str] = []
        behavior_case_ids: list[str] = []
        for name in sorted(domain_names):
            with self.subTest(skill=name):
                row = by_name[name]
                self.assertEqual("domain", row["layer"])
                self.assertEqual(
                    [
                        "route_covered",
                        "negative_route_covered",
                        "behavior_covered",
                    ],
                    row["required_states"],
                )
                self.assertTrue(row["coverage_states"]["route_covered"])
                self.assertTrue(
                    row["coverage_states"]["negative_route_covered"]
                )
                self.assertTrue(row["coverage_states"]["behavior_covered"])
                self.assertEqual("pass", row["coverage_gate_status"])
                self.assertGreaterEqual(row["evidence_counts"]["positive_route"], 1)
                self.assertGreaterEqual(row["evidence_counts"]["negative_route"], 1)
                self.assertEqual(1, row["evidence_counts"]["behavior"])
                positive_case_ids.extend(
                    row["evidence_case_ids"]["positive_route"]
                )
                negative_case_ids.extend(
                    row["evidence_case_ids"]["negative_route"]
                )
                behavior_case_ids.extend(row["evidence_case_ids"]["behavior"])
        self.assertEqual(36, len(positive_case_ids))
        self.assertEqual(36, len(set(positive_case_ids)))
        added_case_ids = (
            "t2b-preparation-payment",
            "t2b-dedicated-payment-analysis",
            "t2b-preparation-ai",
            "t2b-dedicated-ai-analysis",
        )
        self.assertEqual(
            {case_id: 1 for case_id in added_case_ids},
            {
                case_id: positive_case_ids.count(case_id)
                for case_id in added_case_ids
            },
        )
        self.assertEqual(19, len(negative_case_ids))
        self.assertEqual(19, len(set(negative_case_ids)))
        self.assertEqual(6, len(behavior_case_ids))
        self.assertEqual(6, len(set(behavior_case_ids)))

    def test_security_and_reliability_negative_routes_cover_adjacent_boundaries(self) -> None:
        matrix = self.module.build_coverage_matrix()
        by_name = {row["name"]: row for row in matrix["rows"]}
        self.assertTrue(
            {
                "security-anti-credential-session-internal-refactor",
                "security-anti-reliability-only",
                "security-anti-input-shape",
                "security-anti-scanner-report",
            }.issubset(
                by_name["security-privacy-gate"]["evidence_case_ids"]["negative_route"]
            )
        )
        self.assertTrue(
            {
                "reliability-anti-unit-local-performance",
                "reliability-anti-logging-field",
                "reliability-anti-release-ordering",
                "reliability-anti-data-correctness",
            }.issubset(
                by_name["reliability-observability-gate"]["evidence_case_ids"]["negative_route"]
            )
        )

    def test_adversarial_negative_control_does_not_count_as_behavior(self) -> None:
        matrix = self.module.build_coverage_matrix()
        review = next(
            row for row in matrix["rows"] if row["name"] == "ai-code-review-refactor"
        )
        negative = set(
            review["evidence_case_ids"]["adversarial_negative_control"]
        )
        behavior = set(review["evidence_case_ids"]["behavior"])
        self.assertTrue(negative)
        self.assertTrue(negative.isdisjoint(behavior))


if __name__ == "__main__":
    unittest.main()
