from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_utils import (  # noqa: E402
    FOUNDATION_CONTENT_BUDGETS,
    EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS,
    REGISTRY_SCHEMA_VERSIONS,
    foundation_content_class_errors,
    foundation_ownership_errors,
    foundation_registry_field_errors,
    load_yaml_file,
    required_expertise_tag_errors,
)
import validation_utils as VALIDATION  # noqa: E402


def _load_audit_skill_content():
    path = ROOT / "scripts" / "audit-skill-content.py"
    spec = importlib.util.spec_from_file_location(
        "audit_skill_content_registry_tests",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AUDIT_SKILL_CONTENT = _load_audit_skill_content()


def _entry(entries: list[dict], name: str) -> dict:
    return next(entry for entry in entries if entry["name"] == name)


class FoundationOwnershipRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.foundation = load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )["foundation_skills"]
        cls.professional = load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )["professional_skills"]

    def _copies(self) -> tuple[list[dict], list[dict]]:
        return copy.deepcopy(self.foundation), copy.deepcopy(self.professional)

    def test_current_scope_counts_and_reciprocity_pass(self) -> None:
        self.assertEqual(
            Counter(entry["delivery_scope"] for entry in self.foundation),
            EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS,
        )
        self.assertEqual(
            foundation_ownership_errors(self.foundation, self.professional),
            [],
        )
        self.assertEqual(
            Counter(entry["content_class"] for entry in self.foundation),
            {"compact": 128, "complex": 22},
        )
        self.assertEqual(
            [
                error
                for entry in self.foundation
                for error in foundation_content_class_errors(
                    entry, f"foundation-skills.yaml:{entry['name']}"
                )
            ],
            [],
        )
        self.assertEqual(
            FOUNDATION_CONTENT_BUDGETS,
            {
                "compact": {"target_words": 400, "hard_words": 500},
                "complex": {"target_words": 500, "hard_words": 600},
            },
        )

    def test_structure_roots_meet_current_budget_semantic_and_trigger_contracts(
        self,
    ) -> None:
        collected = AUDIT_SKILL_CONTENT._collect_root_content()
        rows = {
            row["path"]: row
            for row in collected["documents"]
            if row["document_part"] == "body"
        }
        structure_path = (
            "src/foundation/capabilities/"
            "implementation-structure-design/SKILL.md"
        )
        structure = rows[structure_path]
        self.assertLessEqual(
            structure["word_count"],
            structure["content_hard_words"],
        )
        self.assertLessEqual(
            structure["high_value_rule_count"],
            8,
        )
        self.assertGreaterEqual(
            structure["high_value_rule_count"],
            3,
        )
        self.assertEqual(
            0,
            structure["high_value_rules_over_sentence_limit"],
        )
        self.assertEqual(
            0,
            structure["high_value_rules_without_decision_semantics"],
        )

        refactoring_path = (
            "src/foundation/capabilities/refactoring/SKILL.md"
        )
        unresolved_refactoring_p1 = [
            candidate
            for candidate in collected["semantic_advisories"]["candidates"]
            if candidate["path"] == refactoring_path
            and candidate["priority"] == "P1"
            and candidate["unresolved"]
        ]
        self.assertEqual([], unresolved_refactoring_p1)

        architecture = _entry(
            self.professional,
            "architecture-impact-reviewer",
        )
        owner_internal_trigger = next(
            signal
            for signal in architecture["trigger_signals"]
            if signal.startswith("owner-internal ")
        )
        architecture_root = (
            ROOT
            / architecture["path"]
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn(owner_internal_trigger, architecture_root)

    def test_review_skill_selector_is_dynamic_and_covers_current_registry(self) -> None:
        selector = getattr(VALIDATION, "professional_review_skill_ids", None)
        self.assertTrue(callable(selector), "dynamic Review Skill selector is missing")
        matrix = VALIDATION.CORE_CONTRACTS["review_discipline_contract"][
            "professional_risk_matrix"
        ]
        expected = {
            entry["name"]
            for entry in self.professional
            if "review-agent" in entry["role_support"]
        }
        self.assertEqual(10, len(expected))
        self.assertEqual(expected, set(selector(self.professional, matrix)))

        future = copy.deepcopy(self.professional)
        candidate = copy.deepcopy(future[0])
        candidate["name"] = "future-review-skill"
        candidate["role_support"] = ["review-agent"]
        future.append(candidate)
        self.assertEqual(
            expected | {"future-review-skill"},
            set(selector(future, matrix)),
        )

    def test_content_class_rationale_contract_fails_closed(self) -> None:
        compact = {"content_class": "compact", "content_class_rationale": "unused"}
        self.assertTrue(
            any(
                "compact content_class forbids" in error
                for error in foundation_content_class_errors(compact, "compact")
            )
        )

        missing = {"content_class": "complex"}
        self.assertTrue(
            any(
                "requires a non-empty" in error
                for error in foundation_content_class_errors(missing, "complex")
            )
        )

        generic = {
            "content_class": "complex",
            "content_class_rationale": "Complex content",
        }
        self.assertTrue(
            any(
                "concrete coupled decisions" in error
                for error in foundation_content_class_errors(generic, "generic")
            )
        )

        unknown = copy.deepcopy(self.foundation[0])
        unknown["content_budget_override"] = 999
        self.assertTrue(
            any(
                "unknown Foundation field" in error
                for error in foundation_registry_field_errors(unknown, "unknown")
            )
        )

    def test_registry_schema_versions_are_layer_specific(self) -> None:
        specs = {
            "control": "control-skills.yaml",
            "professional": "professional-skills.yaml",
            "foundation": "foundation-skills.yaml",
            "domain": "domain-skills.yaml",
        }
        for layer, filename in specs.items():
            with self.subTest(layer=layer):
                registry = load_yaml_file(ROOT / "src/registry" / filename)
                self.assertEqual(
                    REGISTRY_SCHEMA_VERSIONS[layer], registry["schema_version"]
                )

    def test_expertise_taxonomy_is_closed_and_layer_bound(self) -> None:
        foundation = _entry(self.foundation, "transaction-consistency")
        self.assertEqual(
            [],
            required_expertise_tag_errors(
                foundation["required_expertise_tags"],
                "transaction-consistency",
                layer="foundation",
                skill_name=foundation["name"],
                foundation_group=foundation["group"],
            ),
        )
        self.assertTrue(
            any(
                "unknown Skill expertise tag" in error
                for error in required_expertise_tag_errors(
                    ["foundation-data-middleware", "specialty-made-up"],
                    "unknown",
                )
            )
        )
        self.assertTrue(
            any(
                "must include group tag" in error
                for error in required_expertise_tag_errors(
                    ["specialty-transaction-consistency"],
                    "missing-group-tag",
                    layer="foundation",
                    skill_name="transaction-consistency",
                    foundation_group="data-middleware",
                )
            )
        )
        self.assertTrue(
            any(
                "must include Skill tag" in error
                for error in required_expertise_tag_errors(
                    ["foundation-security-privacy"],
                    "missing-domain-tag",
                    layer="domain",
                    skill_name="ai-product-extension",
                )
            )
        )

    def test_unknown_delivery_scope_fails_closed(self) -> None:
        foundation, professional = self._copies()
        _entry(foundation, "unit-testing")["delivery_scope"] = "normal"
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("delivery_scope must be one of" in error for error in errors))

    def test_product_foundation_requires_an_owner(self) -> None:
        foundation, professional = self._copies()
        skill = _entry(foundation, "user-role-identification")
        skill["used_by"] = []
        owner = _entry(professional, "change-intake-compiler")
        owner["layer3_candidates"].remove("user-role-identification")
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("must have at least one Professional owner" in error for error in errors))

    def test_used_by_must_match_professional_candidates_in_both_directions(self) -> None:
        foundation, professional = self._copies()
        _entry(foundation, "unit-testing")["used_by"] = []
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("must exactly match" in error for error in errors))

        foundation, professional = self._copies()
        owner = _entry(professional, "quality-test-gate")
        owner["layer3_candidates"].remove("unit-testing")
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("must exactly match" in error for error in errors))

    def test_used_by_cannot_name_a_layer3_skill(self) -> None:
        foundation, professional = self._copies()
        _entry(foundation, "unit-testing")["used_by"].append(
            "transaction-consistency"
        )
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("must reference a Professional Skill" in error for error in errors))

    def test_non_product_foundation_cannot_be_a_candidate(self) -> None:
        foundation, professional = self._copies()
        skill = _entry(foundation, "skill-authoring-expert")
        skill["used_by"] = ["ai-code-review-refactor"]
        owner = _entry(professional, "ai-code-review-refactor")
        owner["layer3_candidates"].append("skill-authoring-expert")
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("must have no Professional owner" in error for error in errors))

    def test_product_owner_requires_role_intersection(self) -> None:
        foundation, professional = self._copies()
        skill = _entry(foundation, "architecture-tradeoff-analysis")
        skill["used_by"].append("high-risk-design-review")
        owner = _entry(professional, "high-risk-design-review")
        owner["layer3_candidates"].append("architecture-tradeoff-analysis")
        errors = foundation_ownership_errors(foundation, professional)
        self.assertTrue(any("has no role_support intersection" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
