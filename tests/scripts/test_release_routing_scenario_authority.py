from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RELEASE_ROUTING = _load(
    "release_routing_validator_test", "scripts/validate-skill-routing.py"
)
CODEGEN = _load(
    "release_routing_codegen_test", "scripts/validate-codegen-benchmarks.py"
)


class ReleaseRoutingScenarioAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenarios = RELEASE_ROUTING.load_release_routing_scenarios(
            RELEASE_ROUTING.RELEASE_ROUTING_SCENARIOS
        )
        self.router_text = RELEASE_ROUTING.ROUTER.read_text()

    def _release_projection_errors(self, *, mutate_light=None):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as raw:
            root = Path(raw)
            light = root / "light.json"
            light.write_text(RELEASE_ROUTING.LIGHT.read_text())
            if mutate_light:
                payload = json.loads(light.read_text())
                mutate_light(payload)
                light.write_text(json.dumps(payload))
            with patch.object(RELEASE_ROUTING, "LIGHT", light):
                return RELEASE_ROUTING._release_routing_projection_errors(
                    self.scenarios, self.router_text
                )

    def test_lightweight_release_projection_drift_fails(self) -> None:
        errors = self._release_projection_errors(
            mutate_light=lambda payload: payload["cases"][0]["steps"][1].update(
                {"primary_skill": "frontend-change-builder"}
            )
        )
        self.assertTrue(any("lightweight dispatch projection" in error for error in errors))

    def test_only_named_context_fixtures_are_exempt_from_release_projection(self) -> None:
        self.assertEqual(
            {
                "source-backed-payment-retry-proof",
                "module-boundary-benchmark-review",
            },
            RELEASE_ROUTING.CONTEXT_ONLY_LIGHT_CASE_IDS,
        )
        errors = self._release_projection_errors(
            mutate_light=lambda payload: payload["cases"].append(
                {"id": "unexpected-context-fixture", "steps": []}
            )
        )
        self.assertTrue(
            any("trajectory ids differ" in error for error in errors),
            errors,
        )

    def test_codegen_release_contract_projection_drift_fails(self) -> None:
        source = ROOT / "evals/codegen/data-api/backward-compatible-api-field/expected-qualities.yaml"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as raw:
            target = Path(raw) / "expected-qualities.yaml"
            target.write_text(
                source.read_text().replace(
                    "task_skill: data-api-contract-changer",
                    "task_skill: backend-change-builder",
                    1,
                )
            )
            errors: list[str] = []
            CODEGEN._validate_expected_qualities(
                target,
                "data-api",
                "backward-compatible-api-field",
                CODEGEN._load_registry_entries(),
                CODEGEN._load_release_routing_projections(errors),
                errors,
            )
            self.assertTrue(
                any("release_contract disagrees" in error for error in errors),
                errors,
            )

    def test_release_scenario_internal_drift_fails(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios[1]["router"]["expected"]["primary"] = "frontend-change-builder"
        errors = RELEASE_ROUTING.release_routing_scenario_errors(scenarios)
        self.assertTrue(any("must match the first phase" in error for error in errors), errors)

    def test_parallel_release_scenario_starts_from_reviewed_authoritative_dag(
        self,
    ) -> None:
        parallel = next(item for item in self.scenarios if item["id"] == "parallel")
        self.assertEqual("direct", parallel["control_path"])
        self.assertIsNone(parallel["analysis"])
        self.assertEqual(
            {
                "profile": "task-agent",
                "primary": "integration-change-builder",
                "layer3": ["contract-testing"],
                "review": "ai-code-review-refactor",
            },
            parallel["router"]["expected"],
        )
        self.assertEqual(3, len(parallel["tasks"]))
        self.assertTrue(
            all(
                task["primary"] == "integration-change-builder"
                and task["layer3"] == ["contract-testing"]
                and task["review"] == "ai-code-review-refactor"
                for task in parallel["tasks"]
            )
        )
        self.assertEqual(
            {"primary": "ai-code-review-refactor", "layer3": []},
            parallel["review"],
        )

    def test_codegen_case_ids_must_be_non_empty_strings(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios[0]["codegen_case_id"] = []
        errors = RELEASE_ROUTING.release_routing_scenario_errors(scenarios)
        self.assertTrue(any("must be a non-empty string" in error for error in errors), errors)

    def test_codegen_case_ids_must_be_unique(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios[1]["codegen_case_id"] = scenarios[0]["codegen_case_id"]
        errors = RELEASE_ROUTING.release_routing_scenario_errors(scenarios)
        self.assertTrue(any("codegen_case_id values must be unique" in error for error in errors), errors)

    def test_codegen_case_ids_must_exist_in_benchmark_manifest(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios[0]["codegen_case_id"] = "missing/not-in-manifest"
        errors = RELEASE_ROUTING.release_routing_scenario_errors(scenarios)
        self.assertTrue(any("not listed in EXPECTED_BENCHMARKS" in error for error in errors), errors)

    def test_codegen_projection_defends_against_duplicate_keys(self) -> None:
        scenarios = copy.deepcopy(self.scenarios[:2])
        duplicate_case_id = scenarios[0]["codegen_case_id"]
        scenarios[1]["codegen_case_id"] = duplicate_case_id
        errors: list[str] = []
        with patch.object(
            CODEGEN,
            "load_release_routing_scenarios",
            return_value=scenarios,
        ):
            projections = CODEGEN._load_release_routing_projections(errors)

        self.assertTrue(any("duplicate codegen_case_id" in error for error in errors), errors)
        self.assertEqual(
            CODEGEN.project_release_contract(scenarios[0]),
            projections[duplicate_case_id]["release_contract"],
        )

    def test_codegen_projection_uses_authoritative_decision_hints(self) -> None:
        expected = {
            "structure/object-method-encapsulation-placement": [
                "domain-object-identification",
                "implementation-structure-design",
            ],
            "structure/complexity-delete-list-review": [
                "minimal-correct-implementation",
            ],
        }
        actual = {
            scenario["codegen_case_id"]: CODEGEN.project_release_route_hints(
                scenario
            )["layer3_skills"]
            for scenario in self.scenarios
            if scenario["codegen_case_id"] in expected
        }
        self.assertEqual(expected, actual)

    def test_required_quality_text_cannot_substitute_for_empty_route_hints(self) -> None:
        source = (
            ROOT
            / "evals/codegen/structure/object-method-encapsulation-placement"
            / "expected-qualities.yaml"
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as raw:
            target = Path(raw) / "expected-qualities.yaml"
            text = source.read_text()
            text = text.replace(
                "  layer3_skills:\n"
                "    - domain-object-identification\n"
                "    - implementation-structure-design\n",
                "  layer3_skills: []\n",
                1,
            )
            text = text.replace(
                "required_qualities:\n",
                "required_qualities:\n"
                "  - Requires `domain-object-identification` and "
                "`implementation-structure-design` decision evidence.\n",
                1,
            )
            target.write_text(text)
            errors: list[str] = []
            CODEGEN._validate_expected_qualities(
                target,
                "structure",
                "object-method-encapsulation-placement",
                CODEGEN._load_registry_entries(),
                CODEGEN._load_release_routing_projections(errors),
                errors,
            )
            self.assertTrue(any("route_hints disagree" in error for error in errors), errors)

    def test_specialized_high_risk_release_routes_require_professional_layer3(self) -> None:
        for scenario_id, phase, missing_skill in (
            ("security-ssrf-boundary", "analysis", "threat-modeling"),
            ("security-ssrf-boundary", "task", "threat-modeling"),
            ("security-ssrf-boundary", "task", "web-security"),
            ("cache-stampede-reliability", "analysis", "concurrency-control"),
            ("cache-stampede-reliability", "task", "concurrency-control"),
        ):
            with self.subTest(
                scenario_id=scenario_id,
                phase=phase,
                missing_skill=missing_skill,
            ):
                scenarios = copy.deepcopy(self.scenarios)
                scenario = next(item for item in scenarios if item["id"] == scenario_id)
                if phase == "analysis":
                    scenario["router"]["expected"]["layer3"].remove(missing_skill)
                    scenario["analysis"]["layer3"].remove(missing_skill)
                else:
                    for task in scenario["tasks"]:
                        task["layer3"].remove(missing_skill)
                errors = RELEASE_ROUTING.release_routing_scenario_errors(scenarios)
                self.assertTrue(
                    any(
                        "requires Layer 3" in error and missing_skill in error
                        for error in errors
                    ),
                    errors,
                )

    def test_release_scenario_kind_drift_fails(self) -> None:
        source = RELEASE_ROUTING.RELEASE_ROUTING_SCENARIOS
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as raw:
            target = Path(raw) / source.name
            target.write_text(
                source.read_text().replace(
                    "changeforge.release_routing_scenarios",
                    "changeforge.routing_scenarios",
                    1,
                )
            )
            with self.assertRaisesRegex(
                RELEASE_ROUTING.ValidationProblem,
                "changeforge.release_routing_scenarios",
            ):
                RELEASE_ROUTING.load_release_routing_scenarios(target)

    def test_expected_qualities_release_projection_drift_fails(self) -> None:
        source = ROOT / "evals/codegen/data-api/backward-compatible-api-field/expected-qualities.yaml"
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as raw:
            target = Path(raw) / "expected-qualities.yaml"
            target.write_text(
                source.read_text().replace(
                    "primary_skill: data-api-contract-changer",
                    "primary_skill: backend-change-builder",
                    1,
                )
            )
            errors: list[str] = []
            CODEGEN._validate_expected_qualities(
                target,
                "data-api",
                "backward-compatible-api-field",
                CODEGEN._load_registry_entries(),
                CODEGEN._load_release_routing_projections(errors),
                errors,
            )
            self.assertTrue(any("route_hints disagree" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
