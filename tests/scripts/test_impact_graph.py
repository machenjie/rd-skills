from __future__ import annotations

import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import impact_graph  # noqa: E402
from validation_utils import (  # noqa: E402
    CORE_CONTRACTS,
    validate_impact_graph_contract,
)


BASE = "a" * 40
HEAD = "b" * 40
REPORT_DIRECTORY_REGRESSION_TEST = (
    "tests/scripts/test_report_directory_cli.py"
)


PACKAGE_CATALOG = {
    "repository-tooling-change-builder": {
        "skill_id": "repository-tooling-change-builder",
        "layer": "professional",
        "path": "src/professional-skills/repository-tooling-change-builder",
        "registry_path": "src/registry/professional-skills.yaml",
        "registry_entry": {
            "name": "repository-tooling-change-builder",
            "layer3_candidates": [],
        },
    },
    "one": {
        "skill_id": "one",
        "layer": "professional",
        "path": "src/professional-skills/one",
        "registry_path": "src/registry/professional-skills.yaml",
        "registry_entry": {
            "name": "one",
            "layer3_candidates": ["foundation-example", "domain-example"],
        },
    },
    "two": {
        "skill_id": "two",
        "layer": "professional",
        "path": "src/professional-skills/two",
        "registry_path": "src/registry/professional-skills.yaml",
        "registry_entry": {"name": "two", "layer3_candidates": []},
    },
    "foundation-example": {
        "skill_id": "foundation-example",
        "layer": "foundation",
        "path": "src/foundation/capabilities/foundation-example",
        "registry_path": "src/registry/foundation-skills.yaml",
        "registry_entry": {
            "name": "foundation-example",
            "delivery_scope": "product",
        },
    },
    "foundation-dev-only": {
        "skill_id": "foundation-dev-only",
        "layer": "foundation",
        "path": "src/foundation/capabilities/foundation-dev-only",
        "registry_path": "src/registry/foundation-skills.yaml",
        "registry_entry": {
            "name": "foundation-dev-only",
            "delivery_scope": "dev-only",
        },
    },
    "domain-example": {
        "skill_id": "domain-example",
        "layer": "domain",
        "path": "src/domain-extensions/domain-example",
        "registry_path": "src/registry/domain-skills.yaml",
        "registry_entry": {"name": "domain-example"},
    },
    "domain-unreferenced": {
        "skill_id": "domain-unreferenced",
        "layer": "domain",
        "path": "src/domain-extensions/domain-unreferenced",
        "registry_path": "src/registry/domain-skills.yaml",
        "registry_entry": {"name": "domain-unreferenced"},
    },
}


IMPACT_004_SCRIPT_CASES = {
    "installers/doctor.py": {
        "rule_id": "installer-tooling",
        "direct_producer_ids": ["validate-installation"],
        "test_modules": [
            "tests/test_hookless_build_install.py",
            "tests/test_hookless_installer_safety.py",
        ],
    },
    "scripts/eval-context-control-plane.py": {
        "rule_id": "context-control-evaluator",
        "direct_producer_ids": ["eval-context-control"],
        "test_modules": [
            "tests/scripts/test_eval_context_control_plane.py",
            REPORT_DIRECTORY_REGRESSION_TEST,
            "tests/test_hookless_evaluations.py",
        ],
    },
    "scripts/eval-professional-agent-samples.py": {
        "rule_id": "professional-sample-evaluator",
        "direct_producer_ids": ["eval-professional-samples"],
        "test_modules": ["tests/scripts/test_deterministic_report_contracts.py"],
    },
    "scripts/eval-professional-benchmarks.py": {
        "rule_id": "professional-benchmark-evaluator",
        "direct_producer_ids": ["eval-professional-benchmarks"],
        "test_modules": [
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_eval_professional_benchmarks.py",
        ],
    },
    "scripts/eval-rendered-context-budget.py": {
        "rule_id": "rendered-context-evaluator",
        "direct_producer_ids": ["eval-rendered-context"],
        "test_modules": [
            "tests/scripts/test_eval_rendered_context_budget.py",
            REPORT_DIRECTORY_REGRESSION_TEST,
            "tests/test_hookless_evaluations.py",
        ],
    },
    "scripts/eval-routing.py": {
        "rule_id": "routing-evaluator",
        "direct_producer_ids": ["eval-routing"],
        "test_modules": [
            "tests/scripts/test_capability_coverage_red.py",
            "tests/scripts/test_decision_eval.py",
            "tests/scripts/test_evidence_direct_authority.py",
            REPORT_DIRECTORY_REGRESSION_TEST,
            "tests/scripts/test_route_implementation_owner_candidates.py",
            "tests/scripts/test_route_oracle_instrumentation.py",
            "tests/scripts/test_validate_professional_routing_coverage.py",
            "tests/test_hookless_evaluations.py",
        ],
    },
    "scripts/eval-skill-professionalism.py": {
        "rule_id": "skill-professionalism-evaluator",
        "direct_producer_ids": ["eval-skill-professionalism"],
        "test_modules": [
            "tests/scripts/test_affected_professionalism.py",
            "tests/scripts/test_capability_coverage_red.py",
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_eval_skill_professionalism.py",
            "tests/test_hookless_evaluations.py",
        ],
    },
    "scripts/expert_panel_review.py": {
        "rule_id": "professional-review-lifecycle-tooling",
        "direct_producer_ids": ["validate-professionalism-regression"],
        "test_modules": [
            "tests/scripts/test_affected_professionalism.py",
            "tests/scripts/test_capability_coverage_red.py",
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_eval_core_principles.py",
            "tests/scripts/test_expert_panel_actionability.py",
            "tests/scripts/test_expert_panel_attestation.py",
            "tests/scripts/test_expert_panel_manifest.py",
            "tests/scripts/test_expert_panel_review.py",
            "tests/scripts/test_professional_completeness_carry_forward.py",
            "tests/scripts/test_professional_completeness_schema3.py",
            "tests/scripts/test_professional_review_cost_fixture.py",
            "tests/scripts/test_professionalism_expert_panel.py",
        ],
    },
    "scripts/professional_completeness_carry_forward.py": {
        "rule_id": "professional-review-lifecycle-tooling",
        "direct_producer_ids": ["validate-professionalism-regression"],
        "test_modules": [
            "tests/scripts/test_affected_professionalism.py",
            "tests/scripts/test_capability_coverage_red.py",
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_eval_core_principles.py",
            "tests/scripts/test_expert_panel_actionability.py",
            "tests/scripts/test_expert_panel_attestation.py",
            "tests/scripts/test_expert_panel_manifest.py",
            "tests/scripts/test_expert_panel_review.py",
            "tests/scripts/test_professional_completeness_carry_forward.py",
            "tests/scripts/test_professional_completeness_schema3.py",
            "tests/scripts/test_professional_review_cost_fixture.py",
            "tests/scripts/test_professionalism_expert_panel.py",
        ],
    },
    "scripts/validate-installation.py": {
        "rule_id": "installation-validator",
        "direct_producer_ids": ["validate-installation"],
        "test_modules": [
            "tests/scripts/test_build_input_freshness.py",
            "tests/scripts/test_deterministic_report_contracts.py",
            REPORT_DIRECTORY_REGRESSION_TEST,
        ],
    },
    "scripts/validate-productization-assets.py": {
        "rule_id": "productization-assets-validator",
        "direct_producer_ids": [],
        "test_modules": ["tests/scripts/test_validate_productization_assets.py"],
    },
    "scripts/validate-professional-routing-coverage.py": {
        "rule_id": "professional-routing-validator",
        "direct_producer_ids": ["validate-professional-routing"],
        "test_modules": [
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_validate_professional_routing_coverage.py",
        ],
    },
    "scripts/validate-professionalism-regression.py": {
        "rule_id": "professional-review-lifecycle-tooling",
        "direct_producer_ids": ["validate-professionalism-regression"],
        "test_modules": [
            "tests/scripts/test_affected_professionalism.py",
            "tests/scripts/test_capability_coverage_red.py",
            "tests/scripts/test_deterministic_report_contracts.py",
            "tests/scripts/test_eval_core_principles.py",
            "tests/scripts/test_expert_panel_actionability.py",
            "tests/scripts/test_expert_panel_attestation.py",
            "tests/scripts/test_expert_panel_manifest.py",
            "tests/scripts/test_expert_panel_review.py",
            "tests/scripts/test_professional_completeness_carry_forward.py",
            "tests/scripts/test_professional_completeness_schema3.py",
            "tests/scripts/test_professional_review_cost_fixture.py",
            "tests/scripts/test_professionalism_expert_panel.py",
        ],
    },
}
IMPACT_004_SCRIPT_CASES["scripts/expert_panel_attestation.py"] = copy.deepcopy(
    IMPACT_004_SCRIPT_CASES["scripts/expert_panel_review.py"]
)
IMPACT_004_SCRIPT_CASES.update(
    {
        "scripts/expert_panel_attestation.py": {
            "rule_id": "expert-panel-attestation-tooling",
            "direct_producer_ids": [],
            "test_modules": [
                "tests/scripts/test_expert_panel_actionability.py",
                "tests/scripts/test_expert_panel_attestation.py",
            ],
        },
        "scripts/expert_panel_contracts.py": {
            "rule_id": "expert-panel-contract-projections",
            "direct_producer_ids": [],
            "test_modules": [
                "tests/scripts/test_expert_panel_actionability.py",
                "tests/scripts/test_expert_panel_attestation.py",
                "tests/scripts/test_expert_panel_review.py",
                "tests/scripts/test_professional_completeness_carry_forward.py",
                "tests/scripts/test_professional_completeness_schema3.py",
            ],
        },
        "scripts/expert_panel_manifest.py": {
            "rule_id": "expert-panel-manifest-tooling",
            "direct_producer_ids": [],
            "test_modules": [
                "tests/scripts/test_expert_panel_manifest.py",
                "tests/scripts/test_expert_panel_release_manifest.py",
            ],
        },
        "scripts/expert_panel_review.py": {
            "rule_id": "expert-panel-review-tooling",
            "direct_producer_ids": [],
            "test_modules": [
                "tests/scripts/test_expert_panel_actionability.py",
                "tests/scripts/test_expert_panel_attestation.py",
                "tests/scripts/test_expert_panel_review.py",
                "tests/scripts/test_professional_completeness_schema3.py",
            ],
        },
        "scripts/professional_completeness_carry_forward.py": {
            "rule_id": "professional-completeness-carry-tooling",
            "direct_producer_ids": [],
            "test_modules": [
                "tests/scripts/test_professional_completeness_carry_forward.py",
                "tests/scripts/test_professional_completeness_schema3.py",
                "tests/scripts/test_professional_review_cost_fixture.py",
            ],
        },
        "scripts/validate-professionalism-regression.py": {
            "rule_id": "professionalism-regression-tooling",
            "direct_producer_ids": [],
            "test_modules": [
                "tests/scripts/test_deterministic_report_contracts.py",
                "tests/scripts/test_eval_core_principles.py",
                "tests/scripts/test_expert_panel_actionability.py",
                "tests/scripts/test_professional_review_cost_fixture.py",
            ],
        },
    }
)


class ImpactGraphContractTests(unittest.TestCase):
    def test_expert_panel_fixture_support_has_one_way_dependencies(self) -> None:
        test_paths = [
            ROOT / "tests/scripts/test_expert_panel_actionability.py",
            ROOT / "tests/scripts/test_expert_panel_attestation.py",
            ROOT / "tests/scripts/test_expert_panel_manifest.py",
            ROOT / "tests/scripts/test_expert_panel_review.py",
            ROOT / "tests/scripts/test_professional_completeness_carry_forward.py",
            ROOT / "tests/scripts/test_professional_completeness_schema3.py",
            ROOT / "tests/scripts/test_professional_review_cost_fixture.py",
            ROOT / "tests/scripts/test_professionalism_expert_panel.py",
        ]
        support_paths = [
            ROOT / "tests/scripts/expert_panel_source_test_support.py",
            ROOT / "tests/scripts/readability_review_test_support.py",
            ROOT / "tests/scripts/professional_completeness_test_support.py",
            ROOT / "tests/scripts/professional_review_cost_test_support.py",
        ]

        test_module_names = {path.stem for path in test_paths}
        support_module_names = {path.stem for path in support_paths}

        def imported_modules(path: Path) -> set[str]:
            tree = ast.parse(path.read_text(encoding="utf-8"), path.as_posix())
            modules: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name.split(".")[-1] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        modules.add(node.module.split(".")[-1])
                    modules.update(alias.name.split(".")[-1] for alias in node.names)
                elif (
                    isinstance(node, ast.Call)
                    and (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "import_module"
                        or isinstance(node.func, ast.Name)
                        and node.func.id == "_import_sibling_test_module"
                    )
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    modules.add(node.args[0].value.lstrip(".").split(".")[-1])
            return modules

        for path in test_paths:
            with self.subTest(path=path.name):
                self.assertFalse(imported_modules(path) & test_module_names)

        for path in support_paths:
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"), path.as_posix())
                self.assertFalse(imported_modules(path) & test_module_names)
                self.assertFalse(
                    any(
                        isinstance(node, ast.ClassDef)
                        and any(
                            isinstance(base, ast.Attribute)
                            and base.attr == "TestCase"
                            or isinstance(base, ast.Name)
                            and base.id == "TestCase"
                            for base in node.bases
                        )
                        for node in tree.body
                    )
                )
                self.assertFalse(
                    any(
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name.startswith("test_")
                        for node in tree.body
                    )
                )

        expected_support_graph = {
            "expert_panel_source_test_support": set(),
            "readability_review_test_support": {
                "expert_panel_source_test_support"
            },
            "professional_completeness_test_support": {
                "expert_panel_source_test_support"
            },
            "professional_review_cost_test_support": {
                "expert_panel_source_test_support",
                "professional_completeness_test_support",
            },
        }
        actual_support_graph = {
            path.stem: imported_modules(path) & support_module_names
            for path in support_paths
        }
        self.assertEqual(expected_support_graph, actual_support_graph)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module: str) -> None:
            if module in visiting:
                self.fail(f"Expert Panel test support dependency cycle at {module}")
            if module in visited:
                return
            visiting.add(module)
            for dependency in sorted(actual_support_graph[module]):
                visit(dependency)
            visiting.remove(module)
            visited.add(module)

        for module in sorted(actual_support_graph):
            visit(module)
        self.assertEqual(set(actual_support_graph), visited)

        expected_owners = {
            "expert-panel-source-test-support": [
                path.relative_to(ROOT).as_posix() for path in test_paths
            ],
            "readability-review-test-support": [
                "tests/scripts/test_expert_panel_actionability.py",
                "tests/scripts/test_expert_panel_review.py",
            ],
            "professional-completeness-test-support": [
                "tests/scripts/test_expert_panel_manifest.py",
                "tests/scripts/test_expert_panel_review.py",
                "tests/scripts/test_professional_completeness_carry_forward.py",
                "tests/scripts/test_professional_completeness_schema3.py",
                "tests/scripts/test_professional_review_cost_fixture.py",
                "tests/scripts/test_professionalism_expert_panel.py",
            ],
            "professional-review-cost-test-support": [
                "tests/scripts/test_professional_review_cost_fixture.py"
            ],
        }
        rules = {
            row["id"]: row
            for row in CORE_CONTRACTS["impact_graph_contract"]["rules"]
        }
        for rule_id, expected_modules in expected_owners.items():
            with self.subTest(rule=rule_id):
                self.assertEqual([], rules[rule_id]["producer_ids"])
                self.assertEqual(expected_modules, rules[rule_id]["test_modules"])

    def test_contract_is_single_validated_authority_over_canonical_producers(self) -> None:
        graph = CORE_CONTRACTS["impact_graph_contract"]
        self.assertEqual("scripts/impact_graph.py", graph["resolver"])
        self.assertEqual(
            "/principle_acceptance_contract/producers", graph["producer_source"]
        )
        authorities = CORE_CONTRACTS["principle_acceptance_contract"]["authorities"]
        self.assertEqual(
            ["impact-graph-authority"],
            [row["id"] for row in authorities if row["pointer"] == "/impact_graph_contract"],
        )
        authority = next(
            row for row in authorities if row["id"] == "impact-graph-authority"
        )
        self.assertEqual(
            "Affected producer and unit-test selection, dependency closure, "
            "fail-closed classification, isolated producer execution, and "
            "deterministic unsharded unique test execution.",
            authority["scope"],
        )
        self.assertEqual([], validate_impact_graph_contract(CORE_CONTRACTS, ROOT))

    def test_contract_owns_exactly_five_layers_and_affected_forbids_release(self) -> None:
        graph = CORE_CONTRACTS["impact_graph_contract"]
        layers = graph["test_selection"]
        self.assertEqual(
            ["unit", "integration", "contract", "governance", "release"],
            layers["order"],
        )
        self.assertEqual("unit", layers["default_layer"])
        policy = graph["stages"]["affected"]["test_policy"]
        self.assertEqual(["unit", "contract"], policy["always_layers"])
        self.assertEqual(
            ["integration", "governance"], policy["direct_only_layers"]
        )
        self.assertEqual(["release"], policy["forbidden_layers"])
        self.assertNotIn(
            "shard_count", graph["stages"]["ci-tests"]
        )

    def test_invalid_graph_rejects_unknown_and_stage_ineligible_producers(self) -> None:
        for label, expected in (
            ("unknown", "unknown producer"),
            ("ineligible", "stage-ineligible"),
        ):
            with self.subTest(label=label):
                mutated = copy.deepcopy(CORE_CONTRACTS)
                producer_id = "missing-producer"
                if label == "ineligible":
                    eligible = mutated["impact_graph_contract"]["stages"][
                        "affected"
                    ]["eligible_producer_ids"]
                    producer_id = eligible.pop(0)
                mutated["impact_graph_contract"]["rules"][0]["producer_ids"] = [
                    producer_id
                ]
                errors = validate_impact_graph_contract(mutated, ROOT)
                self.assertTrue(any(expected in item for item in errors), errors)

    def test_build_profile_projection_is_closed_and_package_rules_do_not_duplicate_it(self) -> None:
        graph = CORE_CONTRACTS["impact_graph_contract"]
        projection = graph["stages"]["affected"]["build_profile_projection"]
        self.assertEqual(["recommended", "full", "dev"], projection["profiles"])
        self.assertEqual("all-profiles", projection["unknown_package_policy"])
        package_rules = {
            rule["id"]: rule
            for rule in graph["rules"]
            if rule["id"] in {
                "foundation-skills",
                "professional-skills",
                "domain-skills",
            }
        }
        self.assertEqual(
            {"foundation-skills", "professional-skills", "domain-skills"},
            set(package_rules),
        )
        for rule in package_rules.values():
            self.assertFalse(
                any(producer.startswith("build-") for producer in rule["producer_ids"])
            )

        mutated = copy.deepcopy(CORE_CONTRACTS)
        mutated["impact_graph_contract"]["stages"]["affected"][
            "build_profile_projection"
        ]["unknown_package_policy"] = "none"
        errors = validate_impact_graph_contract(mutated, ROOT)
        self.assertTrue(any("build_profile_projection" in error for error in errors), errors)


class ImpactGraphResolutionTests(unittest.TestCase):
    @staticmethod
    def _write_registry_catalog(root: Path, *, include_example: bool) -> None:
        registry = root / "src/registry"
        registry.mkdir(parents=True, exist_ok=True)
        values = {
            "professional-skills.yaml": (
                "schema_version: 1\nprofessional_skills:\n"
                "  - name: example\n"
                "    path: src/professional-skills/example\n"
                if include_example
                else "schema_version: 1\nprofessional_skills: []\n"
            ),
            "foundation-skills.yaml": (
                "schema_version: 1\nfoundation_skills: []\n"
            ),
            "domain-skills.yaml": "schema_version: 1\ndomain_skills: []\n",
        }
        for name, value in values.items():
            (registry / name).write_text(value, encoding="utf-8")

    def _resolve(self, entries: list[tuple[str, str]]) -> dict:
        return impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            entries,
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
        )

    def test_non_control_skill_layers_select_exact_direct_packages(self) -> None:
        cases = {
            "src/professional-skills/repository-tooling-change-builder/SKILL.md": (
                "repository-tooling-change-builder"
            ),
            "src/foundation/capabilities/foundation-example/SKILL.md": (
                "foundation-example"
            ),
            "src/domain-extensions/domain-example/references/checklist.md": (
                "domain-example"
            ),
        }
        for path, skill_id in cases.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertEqual("packages", result["professionalism"]["scope"])
                self.assertEqual(
                    [skill_id], result["professionalism"]["direct_package_ids"]
                )
                self.assertIn("eval-skill-professionalism", result["selected_producer_ids"])

    def test_deleted_reference_in_surviving_package_remains_package_scoped(self) -> None:
        result = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [
                (
                    "D",
                    "src/professional-skills/repository-tooling-change-builder/"
                    "references/harness-validity-contracts.md",
                )
            ],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
        )
        self.assertEqual("packages", result["professionalism"]["scope"])
        self.assertEqual(
            ["repository-tooling-change-builder"],
            result["professionalism"]["direct_package_ids"],
        )

    def test_deleted_package_topology_forces_full_head_scope_without_old_id(self) -> None:
        head_catalog = copy.deepcopy(PACKAGE_CATALOG)
        del head_catalog["foundation-dev-only"]
        result = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("D", "src/foundation/capabilities/foundation-dev-only/SKILL.md")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=head_catalog,
        )
        self.assertEqual("full", result["professionalism"]["scope"])
        self.assertEqual([], result["professionalism"]["direct_package_ids"])
        self.assertEqual(["dev"], result["selected_build_profiles"])
        self.assertIn(
            [
                "package:foundation-dev-only",
                "professionalism:package-removed",
                "scope:full",
            ],
            result["professionalism"]["reason_chains"],
        )

    def test_registry_entry_diff_is_package_scoped_but_envelope_diff_is_full(self) -> None:
        head_catalog = copy.deepcopy(PACKAGE_CATALOG)
        head_catalog["one"]["registry_entry"] = {"name": "one", "trigger": "changed"}
        scoped = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("M", "src/registry/professional-skills.yaml")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=head_catalog,
            registry_envelopes_equal=True,
        )
        self.assertEqual("packages", scoped["professionalism"]["scope"])
        self.assertEqual(["one"], scoped["professionalism"]["direct_package_ids"])

        full = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("M", "src/registry/professional-skills.yaml")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=head_catalog,
            registry_envelopes_equal=False,
        )
        self.assertEqual("full", full["professionalism"]["scope"])
        self.assertEqual([], full["professionalism"]["direct_package_ids"])

    def test_panel_tooling_config_attestations_and_docs_do_not_select_full_professionalism(self) -> None:
        cases = {
            "scripts/expert_panel_attestation.py": "soft-stale",
            "scripts/expert_panel_manifest.py": "soft-stale",
            "scripts/expert_panel_review.py": "soft-stale",
            "scripts/professional_completeness_carry_forward.py": "soft-stale",
            "scripts/validate-professionalism-regression.py": "soft-stale",
            "scripts/validation_utils.py": "soft-stale",
            "src/control-model/core-contracts.json": "soft-stale",
            "config/professionalism-release-review.yaml": "soft-stale",
            "evals/expert-panel/readability.json": "soft-stale",
            "evals/expert-panel/semantic-disposition.json": "soft-stale",
            "evals/expert-panel/professional-completeness.json": "soft-stale",
            "docs/VALIDATION.md": "unchanged",
        }
        forbidden = {
            "eval-skill-professionalism",
            "validate-professionalism-regression",
        }
        for path, evidence_status in cases.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertEqual("none", result["professionalism"]["scope"])
                self.assertEqual([], result["professionalism"]["direct_package_ids"])
                self.assertTrue(
                    forbidden.isdisjoint(result["selected_producer_ids"]), result
                )
                self.assertEqual(
                    evidence_status, result["expert_panel_evidence"]["status"]
                )
                self.assertEqual(
                    [], result["selected_test_modules_by_layer"]["release"]
                )

    def test_professional_semantic_contract_selects_full_static_validation_and_soft_stale_evidence(self) -> None:
        result = self._resolve([("M", "scripts/expert_panel_contracts.py")])
        self.assertEqual("full", result["professionalism"]["scope"])
        self.assertEqual([], result["professionalism"]["direct_package_ids"])
        self.assertIn("eval-skill-professionalism", result["selected_producer_ids"])
        self.assertNotIn(
            "validate-professionalism-regression", result["selected_producer_ids"]
        )
        self.assertEqual("soft-stale", result["expert_panel_evidence"]["status"])
        self.assertEqual(
            ["readability", "semantic-disposition", "professional-completeness"],
            result["expert_panel_evidence"]["affected_axes"],
        )
        self.assertIn(
            "tests/scripts/test_professional_completeness_carry_forward.py",
            result["selected_test_modules"],
        )

    def test_readability_and_semantic_detector_change_selects_focused_axis_validators(self) -> None:
        result = self._resolve([("M", "scripts/audit-skill-content.py")])
        self.assertEqual("none", result["professionalism"]["scope"])
        self.assertNotIn("eval-skill-professionalism", result["selected_producer_ids"])
        self.assertEqual(
            ["readability", "semantic-disposition"],
            result["expert_panel_evidence"]["affected_axes"],
        )
        self.assertIn(
            "tests/scripts/test_expert_panel_actionability.py",
            result["selected_test_modules"],
        )
        self.assertIn(
            "tests/scripts/test_expert_panel_attestation.py",
            result["selected_test_modules"],
        )

    def test_canonical_producer_dependency_cannot_receive_none_scope(self) -> None:
        result = self._resolve(
            [("M", "scripts/validate-professional-routing-coverage.py")]
        )
        self.assertIn("eval-skill-professionalism", result["selected_producer_ids"])
        self.assertEqual("full", result["professionalism"]["scope"])
        self.assertEqual(
            [
                [
                    "producer:eval-skill-professionalism",
                    "professionalism:canonical-producer-closure",
                    "scope:full",
                ]
            ],
            result["professionalism"]["reason_chains"],
        )

    def test_affected_professionalism_tests_follow_every_exact_source_owner(self) -> None:
        test_module = "tests/scripts/test_affected_professionalism.py"
        for path in (
            "scripts/eval-core-principles.py",
            "scripts/eval-skill-professionalism.py",
        ):
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertIn(test_module, result["selected_test_modules"])

    def test_skill_and_reference_are_strict_subsets_without_full_professionalism(self) -> None:
        total = len(CORE_CONTRACTS["principle_acceptance_contract"]["producers"])
        paths = (
            "src/professional-skills/repository-tooling-change-builder/SKILL.md",
            "src/professional-skills/repository-tooling-change-builder/"
            "references/harness-validity-contracts.md",
        )
        for path in paths:
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                selected = result["selected_producer_ids"]
                self.assertLess(len(selected), total)
                self.assertNotIn("validate-professionalism-regression", selected)
                self.assertIn("audit-skill-content", selected)
                self.assertIn("validate-reference-content", selected)
                self.assertTrue(result["producer_explanations"])

    def test_one_package_selection_keeps_exact_canonical_producer_closure(self) -> None:
        result = self._resolve(
            [("M", "src/professional-skills/repository-tooling-change-builder/SKILL.md")]
        )
        self.assertEqual(
            ["repository-tooling-change-builder"],
            result["professionalism"]["direct_package_ids"],
        )
        self.assertEqual(
            [
                "validate-skills",
                "validate-registry",
                "validate-skill-routing",
                "validate-skill-body-links",
                "validate-skill-content-size",
                "audit-skill-content",
                "validate-reference-content",
                "validate-root-content",
                "build-recommended",
                "build-full",
                "build-dev",
                "eval-skill-professionalism",
                "eval-agent-lightweight",
                "eval-rendered-context",
                "eval-context-control",
            ],
            result["selected_producer_ids"],
        )

    def test_deletion_has_same_authority_and_targets_as_modification(self) -> None:
        path = (
            "src/professional-skills/repository-tooling-change-builder/"
            "references/harness-validity-contracts.md"
        )
        modified = self._resolve([("M", path)])
        deleted = self._resolve([("D", path)])
        for key in ("selected_producer_ids", "selected_test_modules"):
            self.assertEqual(modified[key], deleted[key])
        self.assertEqual(
            modified["changed_paths"][0]["rule_id"],
            deleted["changed_paths"][0]["rule_id"],
        )

    def test_rename_preserves_old_and_new_path_authority(self) -> None:
        payload = (
            b"R100\0src/professional-skills/old/SKILL.md\0"
            b"src/professional-skills/new/SKILL.md\0"
        )
        entries = impact_graph._parse_name_status_z(payload)
        self.assertEqual(
            [
                ("D", "src/professional-skills/old/SKILL.md"),
                ("A", "src/professional-skills/new/SKILL.md"),
            ],
            entries,
        )
        result = self._resolve(entries)
        self.assertEqual(2, len(result["changed_paths"]))

    def test_deleted_and_renamed_tests_select_only_existing_targets(self) -> None:
        deleted = self._resolve([("D", "tests/scripts/test_old.py")])
        self.assertEqual([], deleted["selected_test_modules"])
        self.assertEqual("test-self", deleted["changed_paths"][0]["classification"])
        self.assertEqual([], deleted["changed_paths"][0]["test_modules"])

        renamed = self._resolve(
            [
                ("D", "tests/scripts/test_old.py"),
                ("A", "tests/scripts/test_new.py"),
            ]
        )
        self.assertEqual(
            ["tests/scripts/test_new.py"], renamed["selected_test_modules"]
        )
        self.assertEqual(
            [[], ["tests/scripts/test_new.py"]],
            [row["test_modules"] for row in renamed["changed_paths"]],
        )

    def test_docs_and_known_no_impact_never_expand_to_full_fallback(self) -> None:
        expected_docs_closure = [
            "build-recommended",
            "build-full",
            "build-dev",
            "eval-agent-lightweight",
            "eval-rendered-context",
            "validate-docs-consistency",
        ]
        docs = self._resolve([("M", "docs/VALIDATION.md")])
        self.assertEqual(expected_docs_closure, docs["selected_producer_ids"])
        self.assertNotIn("eval-context-control", docs["selected_producer_ids"])
        self.assertEqual([], docs["selected_test_modules_by_layer"]["release"])
        self.assertEqual("affected-targets", docs["reason"])
        docs_producer = next(
            producer
            for producer in CORE_CONTRACTS["principle_acceptance_contract"]["producers"]
            if producer["id"] == "validate-docs-consistency"
        )
        self.assertEqual(["eval-rendered-context"], docs_producer["depends_on"])

        without_report_edge = copy.deepcopy(CORE_CONTRACTS)
        mutated_docs_producer = next(
            producer
            for producer in without_report_edge["principle_acceptance_contract"][
                "producers"
            ]
            if producer["id"] == "validate-docs-consistency"
        )
        mutated_docs_producer["depends_on"] = []
        collapsed = impact_graph.resolve_entries(
            without_report_edge,
            [("M", "docs/VALIDATION.md")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
        )
        self.assertEqual(
            ["validate-docs-consistency"], collapsed["selected_producer_ids"]
        )

        no_impact = self._resolve([("M", "LICENSE")])
        self.assertEqual([], no_impact["selected_producer_ids"])
        self.assertEqual([], no_impact["selected_test_modules"])
        self.assertEqual("known-no-impact", no_impact["reason"])
        self.assertEqual("unchanged", no_impact["expert_panel_evidence"]["status"])
        self.assertEqual([], no_impact["expert_panel_evidence"]["affected_axes"])
        self.assertNotIn("fallback", no_impact)

        benchmark = self._resolve(
            [("M", "tests/scripts/expert_panel_storage_benchmark.py")]
        )
        self.assertEqual([], benchmark["selected_producer_ids"])
        self.assertEqual([], benchmark["selected_test_modules"])
        self.assertEqual("known-no-impact", benchmark["reason"])
        self.assertEqual("unchanged", benchmark["expert_panel_evidence"]["status"])
        self.assertEqual([], benchmark["expert_panel_evidence"]["affected_axes"])
        self.assertNotIn("fallback", benchmark)

    def test_repository_authority_docs_have_one_docs_owner_and_minimal_contract_test(self) -> None:
        paths = (
            ".github/pull_request_template.md",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
        )
        for path in paths:
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                decision = result["changed_paths"][0]
                self.assertEqual("rule", decision["classification"])
                self.assertEqual("repository-authority-docs", decision["rule_id"])
                self.assertEqual(
                    ["validate-docs-consistency"],
                    decision["direct_producer_ids"],
                )
                self.assertEqual(
                    ["tests/scripts/test_validate_docs_consistency.py"],
                    decision["test_modules"],
                )
                self.assertEqual([], result["selected_test_modules_by_layer"]["release"])
                self.assertNotIn("fallback", result)

    def test_retired_workflow_paths_select_the_same_docs_guard(self) -> None:
        for relative in (
            ".github/workflows/ci.yml",
            ".github/workflows/formal-release.yml",
        ):
            with self.subTest(relative=relative):
                result = self._resolve([("M", relative)])
                decision = result["changed_paths"][0]
                self.assertEqual("rule", decision["classification"])
                self.assertEqual("retired-workflow-guard", decision["rule_id"])
                self.assertEqual(
                    ["validate-docs-consistency"],
                    decision["direct_producer_ids"],
                )
                self.assertEqual(
                    ["tests/scripts/test_validate_docs_consistency.py"],
                    decision["test_modules"],
                )
                self.assertEqual(
                    [], result["selected_test_modules_by_layer"]["release"]
                )
                self.assertNotIn("fallback", result)

    def test_all_repository_control_paths_resolve_without_ambiguity_or_release_tests(self) -> None:
        paths = (
            ".github/pull_request_template.md",
            ".github/workflows/ci.yml",
            ".github/workflows/formal-release.yml",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
        )
        result = self._resolve([("M", path) for path in paths])
        self.assertEqual(paths, tuple(row["path"] for row in result["changed_paths"]))
        self.assertTrue(
            all(row["classification"] == "rule" for row in result["changed_paths"])
        )
        self.assertEqual(
            {"repository-authority-docs", "retired-workflow-guard"},
            {row["rule_id"] for row in result["changed_paths"]},
        )
        self.assertEqual(
            [
                "build-recommended",
                "build-full",
                "build-dev",
                "eval-agent-lightweight",
                "eval-rendered-context",
                "validate-docs-consistency",
            ],
            result["selected_producer_ids"],
        )
        self.assertNotIn("eval-context-control", result["selected_producer_ids"])
        self.assertEqual([], result["selected_test_modules_by_layer"]["release"])
        self.assertNotIn("fallback", result)

    def test_canonical_producer_script_ownership_is_derived_from_core_argv(self) -> None:
        result = self._resolve([("M", "scripts/validate-skills.py")])
        decision = result["changed_paths"][0]
        self.assertEqual("canonical-producer-script:validate-skills", decision["rule_id"])
        self.assertEqual(["validate-skills"], decision["direct_producer_ids"])
        self.assertIn("tests/scripts/test_validate_skills.py", decision["test_modules"])
        self.assertEqual([], result["selected_test_modules_by_layer"]["release"])
        self.assertNotIn("fallback", result)

    def test_material_fixture_categories_select_their_canonical_owner(self) -> None:
        cases = {
            "evals/professional-benchmarks/backend/example/expected.yaml": (
                "professional-benchmark-evaluator",
                ["eval-professional-benchmarks"],
            ),
            "evals/pressure/hookless/example.yaml": (
                "pressure-behavior-evaluator",
                ["eval-pressure-behavior"],
            ),
            "evals/agent-behavior/professional-samples/backend/example.yaml": (
                "agent-behavior-evaluator",
                ["eval-agent-behavior"],
            ),
            "evals/capability-coverage/admission-cases.yaml": (
                "routing-fixtures-and-helpers",
                ["eval-routing"],
            ),
        }
        for path, (rule_id, producer_ids) in cases.items():
            with self.subTest(path=path):
                modified = self._resolve([("M", path)])
                deleted = self._resolve([("D", path)])
                for result in (modified, deleted):
                    decision = result["changed_paths"][0]
                    self.assertEqual(rule_id, decision["rule_id"])
                    self.assertEqual(producer_ids, decision["direct_producer_ids"])
                    self.assertEqual(
                        [], result["selected_test_modules_by_layer"]["release"]
                    )
                    self.assertNotIn("fallback", result)
                self.assertEqual(
                    modified["selected_producer_ids"], deleted["selected_producer_ids"]
                )

    def test_selected_tests_are_grouped_by_layer_and_flat_projection_is_compatible(self) -> None:
        result = self._resolve([("M", "scripts/impact_graph.py")])
        grouped = result["selected_test_modules_by_layer"]
        self.assertEqual(
            ["unit", "integration", "contract", "governance", "release"],
            list(grouped),
        )
        flattened = sorted(
            module for modules in grouped.values() for module in modules
        )
        self.assertEqual(flattened, result["selected_test_modules"])
        self.assertEqual([], grouped["release"])
        self.assertIn("tests/scripts/test_impact_graph_git.py", grouped["integration"])

    def test_affected_policy_triggers_governance_directly_but_never_release(self) -> None:
        result = self._resolve([("M", "scripts/expert_panel_review.py")])
        direct = result["changed_paths"][0]["test_modules"]
        self.assertIn("tests/scripts/test_expert_panel_review.py", direct)
        self.assertIn(
            "tests/scripts/test_expert_panel_review.py",
            result["selected_test_modules"],
        )
        self.assertEqual([], result["selected_test_modules_by_layer"]["integration"])
        self.assertEqual([], result["selected_test_modules_by_layer"]["release"])

    def test_skill_and_reference_never_select_integration_or_governance(self) -> None:
        for path in (
            "src/professional-skills/one/SKILL.md",
            "src/professional-skills/one/references/checklist.md",
        ):
            with self.subTest(path=path):
                grouped = self._resolve([("M", path)])["selected_test_modules_by_layer"]
                self.assertEqual([], grouped["integration"])
                self.assertEqual([], grouped["governance"])

    def test_integration_is_selected_only_by_direct_build_or_codegen_impact(self) -> None:
        for path in (
            "scripts/build.py",
            "evals/codegen/validation/case/prompt.md",
        ):
            with self.subTest(path=path):
                grouped = self._resolve([("M", path)])["selected_test_modules_by_layer"]
                self.assertTrue(grouped["integration"], grouped)
        docs = self._resolve([("M", "docs/VALIDATION.md")])
        self.assertEqual([], docs["selected_test_modules_by_layer"]["integration"])

        quickstart = self._resolve([("M", "scripts/quickstart.py")])
        self.assertEqual([], quickstart["selected_test_modules_by_layer"]["integration"])
        self.assertEqual(
            ["tests/scripts/test_quickstart.py"], quickstart["selected_test_modules"]
        )

    def test_eval_core_source_selects_contract_and_real_integration_tests(self) -> None:
        grouped = self._resolve(
            [("M", "scripts/eval-core-principles.py")]
        )["selected_test_modules_by_layer"]
        self.assertIn("tests/scripts/test_eval_core_principles.py", grouped["contract"])
        self.assertIn("tests/scripts/test_eval_core_affected.py", grouped["integration"])
        self.assertNotIn("tests/scripts/test_impact_graph_git.py", grouped["integration"])

    def test_impact_control_owners_are_split_into_minimal_exact_test_sets(self) -> None:
        cases = {
            "scripts/impact_graph.py": (
                "impact-graph-resolver",
                [],
                [
                    "tests/scripts/test_impact_graph.py",
                    "tests/scripts/test_impact_graph_git.py",
                ],
            ),
            "scripts/run-ci-tests.py": (
                "affected-test-runner",
                [],
                ["tests/scripts/test_run_ci_tests.py"],
            ),
            "scripts/eval-core-principles.py": (
                "core-evaluator",
                [],
                [
                    "tests/scripts/test_affected_professionalism.py",
                    "tests/scripts/test_eval_core_affected.py",
                    "tests/scripts/test_eval_core_principles.py",
                ],
            ),
            "scripts/validation_utils.py": (
                "core-schema-and-validation",
                [
                    "eval-agent-lightweight",
                    "eval-context-control",
                    "eval-pressure-behavior",
                    "eval-rendered-context",
                    "eval-routing",
                    "validate-task-contracts",
                ],
                [
                    "tests/scripts/test_decision_eval.py",
                    "tests/scripts/test_evidence_direct_authority.py",
                    "tests/scripts/test_impact_graph.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/scripts/test_validate_task_contracts.py",
                    "tests/scripts/test_validation_utils.py",
                ],
            ),
            "src/control-model/core-contracts.json": (
                "core-schema-and-validation",
                [
                    "eval-agent-lightweight",
                    "eval-context-control",
                    "eval-pressure-behavior",
                    "eval-rendered-context",
                    "eval-routing",
                    "validate-task-contracts",
                ],
                [
                    "tests/scripts/test_decision_eval.py",
                    "tests/scripts/test_evidence_direct_authority.py",
                    "tests/scripts/test_impact_graph.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/scripts/test_validate_task_contracts.py",
                    "tests/scripts/test_validation_utils.py",
                ],
            ),
            ".github/workflows/ci.yml": (
                "retired-workflow-guard",
                ["validate-docs-consistency"],
                ["tests/scripts/test_validate_docs_consistency.py"],
            ),
            ".github/workflows/formal-release.yml": (
                "retired-workflow-guard",
                ["validate-docs-consistency"],
                ["tests/scripts/test_validate_docs_consistency.py"],
            ),
        }
        legacy_broad_test_count = 8
        for path, (rule_id, producer_ids, test_modules) in cases.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                decision = result["changed_paths"][0]
                self.assertEqual(rule_id, decision["rule_id"])
                self.assertEqual(producer_ids, decision["direct_producer_ids"])
                self.assertEqual(test_modules, decision["test_modules"])
                self.assertLess(len(test_modules), legacy_broad_test_count)
                self.assertEqual([], result["selected_test_modules_by_layer"]["release"])
        self.assertEqual(2, len(cases["scripts/impact_graph.py"][2]))
        self.assertNotIn(
            "tests/scripts/test_validate_task_contracts.py",
            cases["scripts/impact_graph.py"][2],
        )

    def test_report_directory_regression_follows_every_exact_source_owner(
        self,
    ) -> None:
        cases = {
            "scripts/validation_utils.py": (
                "core-schema-and-validation",
                [
                    "tests/scripts/test_decision_eval.py",
                    "tests/scripts/test_evidence_direct_authority.py",
                    "tests/scripts/test_impact_graph.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/scripts/test_validate_task_contracts.py",
                    "tests/scripts/test_validation_utils.py",
                ],
            ),
            "scripts/audit-skill-content.py": (
                "skill-content-collector",
                [
                    "tests/scripts/test_audit_skill_content.py",
                    "tests/scripts/test_evidence_direct_authority.py",
                    "tests/scripts/test_expert_panel_actionability.py",
                    "tests/scripts/test_expert_panel_attestation.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/scripts/test_validate_root_content.py",
                ],
            ),
            "scripts/validate-installation.py": (
                "installation-validator",
                [
                    "tests/scripts/test_build_input_freshness.py",
                    "tests/scripts/test_deterministic_report_contracts.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                ],
            ),
            "scripts/eval-routing.py": (
                "routing-evaluator",
                [
                    "tests/scripts/test_capability_coverage_red.py",
                    "tests/scripts/test_decision_eval.py",
                    "tests/scripts/test_evidence_direct_authority.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/scripts/test_route_implementation_owner_candidates.py",
                    "tests/scripts/test_route_oracle_instrumentation.py",
                    "tests/scripts/test_validate_professional_routing_coverage.py",
                    "tests/test_hookless_evaluations.py",
                ],
            ),
            "scripts/eval-agent-lightweight.py": (
                "agent-lightweight-fixtures",
                [
                    "tests/scripts/test_eval_agent_lightweight_layer3_references.py",
                    "tests/scripts/test_eval_agent_lightweight_utility.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                ],
            ),
            "scripts/eval-rendered-context-budget.py": (
                "rendered-context-evaluator",
                [
                    "tests/scripts/test_eval_rendered_context_budget.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/test_hookless_evaluations.py",
                ],
            ),
            "scripts/eval-context-control-plane.py": (
                "context-control-evaluator",
                [
                    "tests/scripts/test_eval_context_control_plane.py",
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/test_hookless_evaluations.py",
                ],
            ),
            "scripts/validate-docs-consistency.py": (
                "docs-consistency-producer",
                [
                    REPORT_DIRECTORY_REGRESSION_TEST,
                    "tests/scripts/test_validate_docs_consistency.py",
                ],
            ),
        }
        for path, (rule_id, test_modules) in cases.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                decision = result["changed_paths"][0]
                self.assertEqual("rule", decision["classification"])
                self.assertEqual(rule_id, decision["rule_id"])
                self.assertEqual(test_modules, decision["test_modules"])
                self.assertEqual(
                    sorted(test_modules), result["selected_test_modules"]
                )
                self.assertEqual(
                    [], result["selected_test_modules_by_layer"]["release"]
                )
                self.assertNotIn("fallback", result)

    def test_duplicate_rule_targets_are_deduplicated_after_layer_selection(self) -> None:
        result = self._resolve(
            [
                ("M", "scripts/impact_graph.py"),
                ("M", "scripts/run-ci-tests.py"),
            ]
        )
        selected = result["selected_test_modules"]
        self.assertEqual(len(selected), len(set(selected)))
        grouped = result["selected_test_modules_by_layer"]
        self.assertEqual(
            len(selected), sum(len(modules) for modules in grouped.values())
        )

    def test_affected_test_support_selects_exact_declared_consumers_only(self) -> None:
        result = self._resolve(
            [("M", "tests/scripts/affected_test_support.py")]
        )
        decision = result["changed_paths"][0]
        self.assertEqual("affected-test-support", decision["rule_id"])
        self.assertEqual([], decision["direct_producer_ids"])
        self.assertEqual(
            [
                "tests/scripts/test_affected_professionalism.py",
                "tests/scripts/test_eval_core_affected.py",
                "tests/scripts/test_impact_graph_git.py",
            ],
            decision["test_modules"],
        )
        self.assertEqual(
            {
                "unit": [],
                "integration": [
                    "tests/scripts/test_eval_core_affected.py",
                    "tests/scripts/test_impact_graph_git.py",
                ],
                "contract": [],
                "governance": [
                    "tests/scripts/test_affected_professionalism.py"
                ],
                "release": [],
            },
            result["selected_test_modules_by_layer"],
        )
        self.assertEqual(
            sorted(decision["test_modules"]), result["selected_test_modules"]
        )

    def test_impact_004_change_surface_has_closed_affected_targets(self) -> None:
        result = self._resolve(
            [("M", path) for path in IMPACT_004_SCRIPT_CASES]
        )
        decisions = {row["path"]: row for row in result["changed_paths"]}
        self.assertEqual(set(IMPACT_004_SCRIPT_CASES), set(decisions))
        for path, expected in IMPACT_004_SCRIPT_CASES.items():
            with self.subTest(path=path):
                decision = decisions[path]
                self.assertEqual("rule", decision["classification"])
                self.assertEqual(expected["rule_id"], decision["rule_id"])
                self.assertEqual(
                    expected["direct_producer_ids"],
                    decision["direct_producer_ids"],
                )
                self.assertEqual(expected["test_modules"], decision["test_modules"])

        self.assertEqual(
            {
                "build-dev",
                "build-full",
                "build-recommended",
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-professional-benchmarks",
                "eval-professional-samples",
                "eval-rendered-context",
                "eval-routing",
                "eval-skill-professionalism",
                "validate-agent-profiles",
                "validate-built-links",
                "validate-installation",
                "validate-professional-routing",
            },
            set(result["selected_producer_ids"]),
        )
        self.assertEqual(
            {
                module
                for expected in IMPACT_004_SCRIPT_CASES.values()
                for module in expected["test_modules"]
                if module
                not in {
                    "tests/scripts/test_professionalism_expert_panel.py",
                }
            },
            set(result["selected_test_modules"]),
        )
        self.assertEqual("resolved", result["status"])
        self.assertEqual("affected-targets", result["reason"])
        self.assertNotIn("fallback", result)

    def test_profile_build_quickstart_and_codegen_select_declared_targets_only(self) -> None:
        cases = {
            "src/agent-profiles/role-agents.json": {
                "build-recommended",
                "build-full",
                "build-dev",
                "validate-agent-profiles",
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
            },
            "scripts/build.py": set(),
            "scripts/quickstart.py": set(),
            "evals/codegen/validation/case/prompt.md": set(),
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertEqual(expected, set(result["selected_producer_ids"]))

    def test_build_tooling_uses_one_direct_owner_without_build_producer_duplication(self) -> None:
        result = self._resolve([("M", "scripts/build.py")])
        self.assertEqual([], result["selected_build_profiles"])
        self.assertFalse(
            any(
                producer.startswith("build-")
                for producer in result["selected_producer_ids"]
            )
        )
        self.assertEqual(
            ["tests/scripts/test_build_safety.py"], result["selected_test_modules"]
        )

    def test_package_build_profiles_follow_the_real_build_graph(self) -> None:
        cases = {
            "src/professional-skills/one/SKILL.md": {
                "recommended", "full", "dev"
            },
            "src/foundation/capabilities/foundation-example/SKILL.md": {
                "recommended", "full", "dev"
            },
            "src/foundation/capabilities/foundation-dev-only/SKILL.md": {"dev"},
            "src/domain-extensions/domain-example/SKILL.md": {
                "recommended", "full", "dev"
            },
            "src/domain-extensions/domain-unreferenced/SKILL.md": {"full", "dev"},
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertEqual(expected, set(result["selected_build_profiles"]))
                self.assertEqual(
                    {f"build-{profile}" for profile in expected},
                    {
                        producer
                        for producer in result["selected_producer_ids"]
                        if producer.startswith("build-")
                    },
                )

    def test_unknown_package_projection_fails_closed_to_all_profiles(self) -> None:
        result = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("M", "src/foundation/capabilities/unknown/SKILL.md")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog={},
            head_package_catalog={},
        )
        self.assertEqual(
            ["recommended", "full", "dev"], result["selected_build_profiles"]
        )

    def test_added_and_deleted_packages_use_the_matching_revision_graph(self) -> None:
        head_without_deleted = copy.deepcopy(PACKAGE_CATALOG)
        del head_without_deleted["foundation-dev-only"]
        deleted = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("D", "src/foundation/capabilities/foundation-dev-only/SKILL.md")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
            head_package_catalog=head_without_deleted,
        )
        self.assertEqual(["dev"], deleted["selected_build_profiles"])

        base_without_added = copy.deepcopy(PACKAGE_CATALOG)
        del base_without_added["domain-unreferenced"]
        added = impact_graph.resolve_entries(
            copy.deepcopy(CORE_CONTRACTS),
            [("A", "src/domain-extensions/domain-unreferenced/SKILL.md")],
            base_sha=BASE,
            head_sha=HEAD,
            base_package_catalog=base_without_added,
            head_package_catalog=copy.deepcopy(PACKAGE_CATALOG),
        )
        self.assertEqual(["full", "dev"], added["selected_build_profiles"])

    def test_multiple_paths_deduplicate_producers_and_retain_each_reason(self) -> None:
        result = self._resolve(
            [
                ("M", "src/professional-skills/one/SKILL.md"),
                ("M", "src/professional-skills/two/SKILL.md"),
            ]
        )
        selected = result["selected_producer_ids"]
        self.assertEqual(len(selected), len(set(selected)))
        audit = next(
            row for row in result["producer_explanations"]
            if row["id"] == "audit-skill-content"
        )
        explained_paths = {
            chain[0] for chain in audit["chains"] if chain
        }
        self.assertEqual(
            {
                "path:src/professional-skills/one/SKILL.md",
                "path:src/professional-skills/two/SKILL.md",
            },
            explained_paths,
        )
        json.loads(json.dumps(result, sort_keys=True))

    def test_behavior_control_sources_select_existing_regression_evaluators(self) -> None:
        behavior_producers = {
            "eval-routing",
            "eval-agent-lightweight",
            "eval-context-control",
            "eval-rendered-context",
            "eval-pressure-behavior",
        }
        expected = {
            "src/control-model/core-contracts.json": {
                "eval-routing",
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
                "eval-pressure-behavior",
            },
            "src/control-prompts/main-control-agent.md": {
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
            },
            "src/agent-profiles/role-agents.json": {
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
            },
            "src/control-skills/engineering-control-plane/references/engineering-brief-template.md": {
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
            },
            "src/professional-skills/backend-change-builder/SKILL.md": {
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
            },
            "src/registry/professional-skills.yaml": {
                "eval-routing",
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
                "eval-pressure-behavior",
            },
            "src/registry/foundation-skills.yaml": {
                "eval-routing",
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
                "eval-pressure-behavior",
            },
            "src/registry/domain-skills.yaml": {
                "eval-routing",
                "eval-agent-lightweight",
                "eval-context-control",
                "eval-rendered-context",
                "eval-pressure-behavior",
            },
        }
        for path, required in expected.items():
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertEqual(
                    required,
                    behavior_producers & set(result["selected_producer_ids"]),
                )
                self.assertNotIn(
                    "validate-professionalism-regression",
                    result["selected_producer_ids"],
                )

        for path in (
            "src/registry/control-skills.yaml",
            "src/registry/release-routing-scenarios.yaml",
        ):
            with self.subTest(path=path):
                result = self._resolve([("M", path)])
                self.assertNotIn(
                    "eval-pressure-behavior", result["selected_producer_ids"]
                )

    def test_known_no_impact_change_selects_no_behavior_or_full_regression(self) -> None:
        result = self._resolve([("M", "LICENSE")])
        self.assertEqual([], result["selected_producer_ids"])
        self.assertEqual([], result["selected_test_modules"])
        self.assertEqual("known-no-impact", result["reason"])
        self.assertEqual(
            "known-no-impact", result["changed_paths"][0]["classification"]
        )

    def test_ambiguous_and_unmatched_paths_fail_closed(self) -> None:
        ambiguous = copy.deepcopy(CORE_CONTRACTS)
        duplicate = copy.deepcopy(ambiguous["impact_graph_contract"]["rules"][-1])
        duplicate["id"] = "overlapping-rule"
        duplicate["path_patterns"] = ["src/professional-skills/**"]
        ambiguous["impact_graph_contract"]["rules"].append(duplicate)
        with self.assertRaisesRegex(
            impact_graph.ImpactGraphError, "multiple impact classifications"
        ) as raised:
            impact_graph.resolve_entries(
                ambiguous,
                [("M", "src/professional-skills/one/SKILL.md")],
                base_sha=BASE,
                head_sha=HEAD,
            )
        self.assertEqual("ambiguous-classification", raised.exception.reason)
        with self.assertRaises(impact_graph.ImpactGraphError) as unmatched:
            self._resolve([("M", "unknown/path.txt")])
        self.assertEqual("unmatched-path", unmatched.exception.reason)

    def test_missing_malformed_and_nonexistent_revisions_fail_closed(self) -> None:
        for base, head, reason in (
            (None, HEAD, "missing-revision"),
            (BASE, None, "missing-revision"),
            ("short", HEAD, "malformed-revision"),
            ("0" * 40, HEAD, "malformed-revision"),
        ):
            with self.subTest(reason=reason), self.assertRaises(
                impact_graph.ImpactGraphError
            ) as raised:
                impact_graph.select(ROOT, CORE_CONTRACTS, base, head)
            self.assertEqual(reason, raised.exception.reason)

        missing = subprocess.CompletedProcess(
            ["git", "cat-file"], 1, stdout=b"", stderr=b"missing"
        )
        with mock.patch.object(impact_graph, "_run_git", return_value=missing), self.assertRaises(
            impact_graph.ImpactGraphError
        ) as raised:
            impact_graph.select(ROOT, CORE_CONTRACTS, BASE, HEAD)
        self.assertEqual("missing-revision", raised.exception.reason)

if __name__ == "__main__":
    unittest.main()
