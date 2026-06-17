from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOOK_SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(HOOK_SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from changeforge_action_classifier import classify_event  # noqa: E402
from changeforge_runtime_route_resolver import build_active_skill_context  # noqa: E402
from validation_utils import load_yaml_file  # noqa: E402


ALIGNMENT_CASES: dict[str, dict[str, set[str] | bool]] = {
    "docs-only-no-implementation-builder": {
        "context_skill_extras": {"change-forge-router"},
        "context_capability_extras": {"agent-execution-discipline"},
    },
    "skill-authoring-no-product-coding": {
        "context_capability_extras": {"documentation-generation", "agent-execution-discipline"},
    },
    "skill-output-contract-update": {
        "fixture_skill_extras": {"ai-code-review-refactor", "change-documentation-gate"},
        "fixture_quality_gate_extras": {"AI review gate"},
    },
    "stage-model-registry-drift": {
        "fixture_skill_extras": {"change-documentation-gate"},
    },
    "redis-cache-no-kafka-bigdata": {
        "context_skill_extras": {"ai-code-review-refactor"},
        "fixture_skill_extras": {"quality-test-gate"},
        "context_capability_extras": {
            "module-boundary-design",
            "code-clarity-maintainability",
            "language-idiom-enforcement",
            "observability",
        },
        "fixture_quality_gate_extras": {"test gate"},
    },
    "kubernetes-helm-no-backend-builder": {
        "fixture_surface_may_be_secondary": True,
        "context_capability_extras": {
            "containerization",
            "observability",
            "backup-recovery",
            "secret-configuration-security",
        },
    },
    "test-only-no-release-security": {
        "context_skill_extras": {"ai-code-review-refactor"},
        "context_capability_extras": {"test-data-management"},
    },
    "sql-migration-no-frontend": {
        "context_skill_extras": {"ai-code-review-refactor"},
        "fixture_skill_extras": {"data-middleware-change-builder"},
        "context_capability_extras": {"test-data-management"},
        "fixture_capability_extras": {"version-compatibility"},
    },
    "large-table-migration": {
        "fixture_skill_extras": {
            "change-intake-compiler",
            "change-impact-analyzer",
            "task-dag-planner",
            "data-middleware-change-builder",
            "backend-change-builder",
            "reliability-observability-gate",
            "change-documentation-gate",
        },
        "context_capability_extras": {"ci-cd", "containerization", "kubernetes-gateway"},
        "fixture_capability_extras": {
            "implementation-structure-design",
            "relational-database",
            "indexing-query-optimization",
            "integration-testing",
        },
        "fixture_quality_gate_extras": {
            "requirement gate",
            "impact gate",
            "implementation gate",
            "reliability gate",
            "documentation gate",
        },
    },
}


class RuntimeRouteFixtureAlignmentTests(unittest.TestCase):
    def test_selected_fixture_outputs_align_with_runtime_resolver(self) -> None:
        for case_id, rules in ALIGNMENT_CASES.items():
            with self.subTest(case_id=case_id):
                case_data = _load_case(case_id)
                actual = _load_actual(case_id)
                context = _context_for_prompt(str(case_data["prompt"]))
                stage_manifest = _dict(actual.get("stage_route_manifest"))

                self.assertEqual(context["current_stage"], stage_manifest["current_stage"])
                self.assertEqual(context["primary_language_surface"], stage_manifest["language_surface"])
                if rules.get("fixture_surface_may_be_secondary"):
                    self.assertIn(stage_manifest["product_surface"], context["product_surfaces"])
                else:
                    self.assertEqual(context["primary_product_surface"], stage_manifest["product_surface"])

                self.assertEqual(
                    set(context["selected_domain_extensions"]),
                    set(_strings(actual.get("domain_extensions"))),
                )
                self._assert_aligned_set(
                    case_id,
                    "selected_skills",
                    context["selected_skills"],
                    actual.get("skills"),
                    rules,
                    "skill",
                )
                self._assert_aligned_set(
                    case_id,
                    "selected_capabilities",
                    context["selected_capabilities"],
                    actual.get("capabilities"),
                    rules,
                    "capability",
                )
                self._assert_aligned_set(
                    case_id,
                    "required_quality_gates",
                    context["required_quality_gates"],
                    actual.get("quality_gates"),
                    rules,
                    "quality_gate",
                )
                self._assert_forbidden_absent(case_id, context, case_data)

    def _assert_aligned_set(
        self,
        case_id: str,
        field: str,
        context_values: object,
        fixture_values: object,
        rules: dict[str, set[str] | bool],
        rule_prefix: str,
    ) -> None:
        context_set = set(_strings(context_values))
        fixture_set = set(_strings(fixture_values))
        context_allowed = set(_strings(rules.get(f"context_{rule_prefix}_extras")))
        fixture_allowed = set(_strings(rules.get(f"fixture_{rule_prefix}_extras")))
        unexpected_context = sorted(context_set - fixture_set - context_allowed)
        unexpected_fixture = sorted(fixture_set - context_set - fixture_allowed)
        self.assertEqual(
            unexpected_context,
            [],
            f"{case_id}: runtime {field} had undeclared extras",
        )
        self.assertEqual(
            unexpected_fixture,
            [],
            f"{case_id}: fixture {field} had undeclared extras",
        )

    def _assert_forbidden_absent(self, case_id: str, context: dict[str, Any], case_data: dict[str, Any]) -> None:
        forbidden = _dict(case_data.get("forbidden"))
        field_map = {
            "skills": "selected_skills",
            "capabilities": "selected_capabilities",
            "domain_extensions": "selected_domain_extensions",
            "quality_gates": "required_quality_gates",
        }
        for fixture_field, context_field in field_map.items():
            present = sorted(
                set(_strings(forbidden.get(fixture_field))) & set(_strings(context.get(context_field)))
            )
            self.assertEqual(present, [], f"{case_id}: runtime context selected forbidden {fixture_field}")


def _context_for_prompt(prompt: str) -> dict[str, Any]:
    classification = classify_event({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
    return build_active_skill_context(
        runtime="codex",
        stage=classification["stage"],
        surfaces=classification["surfaces"],
        event_name="UserPromptSubmit",
        classification=classification,
    )


def _load_case(case_id: str) -> dict[str, Any]:
    return _dict(load_yaml_file(ROOT / "evals" / "routing" / f"{case_id}.yaml"))


def _load_actual(case_id: str) -> dict[str, Any]:
    data = _dict(load_yaml_file(ROOT / "evals" / "routing-outputs" / f"{case_id}.actual.yaml"))
    return _dict(data.get("actual"))


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strings(value: object) -> list[str]:
    if isinstance(value, (list, set, tuple)):
        return [item for item in value if isinstance(item, str)]
    return []


if __name__ == "__main__":
    unittest.main()
