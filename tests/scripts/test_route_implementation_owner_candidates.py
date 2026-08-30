from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import importlib.util
import inspect
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import deterministic_route_oracle as ORACLE
import validation_utils as VALIDATION
from validation_utils import load_yaml_file


REGISTRY_PATH = ROOT / "src" / "registry" / "professional-skills.yaml"
ORACLE_PATH = ROOT / "scripts" / "deterministic_route_oracle.py"
ROUTER_PATH = (
    ROOT
    / "src"
    / "control-skills"
    / "engineering-control-plane"
    / "references"
    / "professional-skill-router.md"
)
EVAL_ROUTING_SPEC = importlib.util.spec_from_file_location(
    "eval_routing",
    ROOT / "scripts" / "eval-routing.py",
)
if EVAL_ROUTING_SPEC is None or EVAL_ROUTING_SPEC.loader is None:
    raise RuntimeError("unable to load eval-routing.py")
EVAL_ROUTING = importlib.util.module_from_spec(EVAL_ROUTING_SPEC)
EVAL_ROUTING_SPEC.loader.exec_module(EVAL_ROUTING)

AUTOMATIC_FAMILIES = {
    "backend",
    "frontend",
    "installed-client",
    "data-middleware",
    "integration",
    "repository-tooling",
    "platform-infrastructure",
    "test-validation",
    "logging",
}
AUTOMATIC_NAMES = {
    "backend-change-builder",
    "frontend-change-builder",
    "installed-client-change-builder",
    "data-middleware-change-builder",
    "integration-change-builder",
    "repository-tooling-change-builder",
    "platform-infrastructure-change-builder",
    "quality-test-gate",
    "logging-design-gate",
}
EXPECTED_POLICY = {
    "implementation_owner": {
        "accepted": {
            "path": "direct",
            "profile": "task-agent",
            "layer3": {
                "source": "task-evidence",
                "default": [],
                "max": 3,
            },
            "review": {
                "source": "selected-one-T2C-risk-or-default",
                "default": "ai-code-review-refactor",
            },
        },
        "conflict": {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "reason": "implementation-owner-conflict",
        },
    }
}
T2E_ECA_DOMAIN_ADDITIONS = {
    "ai-product-extension",
    "android-platform-extension",
    "bigdata-product-extension",
    "cloud-platform-extension",
    "cross-platform-client-extension",
    "ios-ipados-platform-extension",
    "iot-embedded-extension",
    "linux-desktop-platform-extension",
    "low-level-systems-extension",
    "macos-platform-extension",
    "web3-product-extension",
    "windows-platform-extension",
}
POLICY_SHA256 = (
    "81efd6d39cefc37df743253378fa0783117c5ea3b221987981d1de95f685f293"
)
FULL13 = {
    "repository-tooling-direct",
    "backend-direct",
    "filesystem-implementation-direct",
    "backend-fallback",
    "regression-test-route",
    "regression-tests-fallback",
    "browser-frontend-route",
    "frontend-native-unchanged",
    "frontend-display-copy",
    "frontend-fallback",
    "infrastructure-direct",
    "installed-client-direct",
    "structured-redacted-logging",
}
RETAINED63_CONTROLS = {
    "repository-tooling-ambiguous",
    "repository-tooling-layer-budget",
    "backend-effects-ambiguous",
    "backend-layer-budget",
    "installed-filesystem-ambiguous",
    "audit-integrity-change",
    "backend-idempotency-analysis",
    "distributed-workflow-analysis",
    "data-consistency-artifact",
    "integration-handoff-artifact",
    "external-integration-analysis",
    "production-release-decision",
    "production-rollout-fallback",
}

LOCKED_ROUTING_FIXTURES = {
    "repository-tooling-direct": {
        "prompt": "Implement an accepted repository-owned generator source change.",
        "excluded_skills": ["incident-response-coordinator"],
        "expected": {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "repository-tooling-change-builder",
            "layer3_skills": [
                "build-tool-professional-usage",
                "targeted-validation-selection",
            ],
            "review_skill": "ai-code-review-refactor",
        },
    },
    "wave1a-dependency-package-mechanics-negative": {
        "prompt": (
            "Analyze whether to install a new package for a capability gap using "
            "only provenance metadata and version-pinning mechanics; no "
            "reachability, remediation, accepted-risk, incompatible-license, "
            "provenance-trust, signature-failure, malicious-package, install-hook, "
            "or SBOM-exception decision exists."
        ),
        "excluded_skills": [
            "technology-stack-selection",
            "dependency-vulnerability-scanning",
        ],
        "expected": {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["package-dependency-management"],
            "review_skill": "architecture-impact-reviewer",
        },
    },
    "wave1a-dependency-lockfile-negative": {
        "prompt": (
            "Implement an accepted repository tooling lockfile version refresh "
            "only; no vulnerability, license, provenance, malicious-package, "
            "install-time, SBOM exception, or package-risk acceptance changes."
        ),
        "excluded_skills": ["dependency-vulnerability-scanning"],
        "expected": {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "repository-tooling-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        },
    },
    "wave1a-dependency-advisory-keyword-negative": {
        "prompt": (
            "Explain a vulnerability advisory keyword without inspecting a "
            "dependency graph, changing a package, or accepting dependency risk."
        ),
        "excluded_skills": ["dependency-vulnerability-scanning"],
        "expected": {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        },
    },
    "wave1a-sandbox-dev-only-negative": {
        "prompt": (
            "Analyze whether to run a local command whose target and mutation "
            "surface are unresolved; this product route must not inject the "
            "dev-only agent tool permission sandbox companion."
        ),
        "excluded_skills": ["agent-tool-permission-sandbox"],
        "expected": {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        },
    },
}


def _registry() -> dict[str, object]:
    value = load_yaml_file(REGISTRY_PATH)
    if not isinstance(value, dict):
        raise AssertionError("Professional registry must be an object")
    return value


def _direct_rule_ids() -> set[str]:
    tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
    route_impl = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_route_impl"
    )
    ids: set[str] = set()
    for node in ast.walk(route_impl):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "result":
            continue
        for keyword in node.keywords:
            if (
                keyword.arg == "rule_id"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                ids.add(keyword.value.value)
    return ids


def _route(prompt: str, registry: object | None = None) -> dict[str, object]:
    parameters = inspect.signature(ORACLE.route_with_trace).parameters
    if "professional_registry" not in parameters:
        raise AssertionError(
            "route_with_trace must accept injected Professional registry authority"
        )
    return ORACLE.route_with_trace(
        prompt,
        main_execution=_test_main_execution(prompt),
        professional_registry=registry,
    )


def _test_task_id(prompt: str) -> str:
    return "test-route-" + hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def _test_main_execution(prompt: str) -> dict[str, object]:
    task_id = _test_task_id(prompt)
    contract = VALIDATION.CORE_CONTRACTS["execution_level_contract"]
    trigger_evaluations = {
        row["id"]: {
            "status": "not_matched",
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"task:{task_id}:trigger:{row['id']}",
            "plausible_critical": False,
        }
        for row in contract["trigger_registry"]
    }
    l2_evaluations = {
        row["id"]: {
            "status": "false",
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"task:{task_id}:l2:{row['id']}",
        }
        for row in contract["l2_eligibility"]
    }
    computed = VALIDATION.compute_execution_level(
        requested="unspecified",
        trigger_evaluations=trigger_evaluations,
        l2_evaluations=l2_evaluations,
    )
    return {
        "producer": "main-control-agent",
        "task_id": task_id,
        "execution_level": computed["effective_level"],
        "level_basis": computed["level_basis"],
    }


def _terminal_action_ambiguity_main(prompt: str) -> dict[str, object]:
    task_id = _test_task_id(prompt)
    return {
        "producer": "main-control-agent",
        "task_id": task_id,
    }


def _projected_route(observed: dict[str, object]) -> dict[str, object]:
    decision = observed["route_decision"]
    result = decision["route_result"]
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }


class ProfessionalRegistryRoutingContractTests(unittest.TestCase):
    def test_schema_v5_modes_families_policy_and_protected_rows(self) -> None:
        data = _registry()
        self.assertEqual(5, data["schema_version"])
        self.assertEqual(EXPECTED_POLICY, data["automatic_routing_policy"])
        rows = data["professional_skills"]
        self.assertEqual(25, len(rows))
        modes = [row.get("routing_mode") for row in rows]
        self.assertEqual(9, modes.count("automatic"))
        self.assertEqual(16, modes.count("evidence-only"))
        self.assertEqual(0, modes.count("not-automatic"))
        automatic = {
            row["name"]: row["routing_family"]
            for row in rows
            if row.get("routing_mode") == "automatic"
        }
        self.assertEqual(AUTOMATIC_NAMES, set(automatic))
        self.assertEqual(AUTOMATIC_FAMILIES, set(automatic.values()))
        for row in rows:
            mode = row["routing_mode"]
            self.assertEqual(mode != "not-automatic", row["task_routable"])
            self.assertEqual(
                mode == "automatic",
                "routing_family" in row,
                row["name"],
            )
        authority = VALIDATION.professional_automatic_routing_authority(data)
        self.assertEqual(EXPECTED_POLICY, authority["policy"])
        self.assertEqual(
            {
                row["routing_family"]: {
                    "name": row["name"],
                    "layer3_candidates": list(row["layer3_candidates"]),
                }
                for row in rows
                if row["routing_mode"] == "automatic"
            },
            authority["owners_by_family"],
        )

    def test_strict_authority_rejects_malformed_mode_family_and_policy(self) -> None:
        builder = getattr(
            VALIDATION,
            "professional_automatic_routing_authority",
            None,
        )
        self.assertTrue(
            callable(builder),
            "typed Professional automatic-routing authority is missing",
        )
        data = _registry()
        malformed: list[dict[str, object]] = []
        for mutate in (
            lambda item: item.update(schema_version=4),
            lambda item: item["professional_skills"][11].update(
                routing_mode="mystery"
            ),
            lambda item: item["professional_skills"][12].update(
                routing_family="unknown"
            ),
            lambda item: item["automatic_routing_policy"][
                "implementation_owner"
            ]["accepted"]["layer3"].update(max=4),
        ):
            candidate = copy.deepcopy(data)
            mutate(candidate)
            malformed.append(candidate)
        for index, candidate in enumerate(malformed):
            with self.subTest(index=index):
                with self.assertRaises(VALIDATION.ValidationProblem):
                    builder(candidate, context=f"injected[{index}]")

    def test_one_sided_registry_rename_fails_domain_reciprocity(self) -> None:
        data = copy.deepcopy(_registry())
        backend = next(
            row
            for row in data["professional_skills"]
            if row.get("routing_family") == "backend"
        ) if any(
            row.get("routing_family") == "backend"
            for row in data["professional_skills"]
        ) else None
        if backend is None:
            self.fail(
                "backend automatic-routing family is missing from the registry"
            )
        backend["name"] = "renamed-backend-owner"
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            _route(
                "Implement an accepted backend service behavior change.",
                data,
            )

    def test_trigger_and_anti_prose_do_not_change_machine_owner(self) -> None:
        data = copy.deepcopy(_registry())
        backend = next(
            row
            for row in data["professional_skills"]
            if row.get("routing_family") == "backend"
        )
        backend["trigger_signals"] = ["human-only trigger prose changed"]
        backend["anti_trigger_signals"] = ["human-only anti prose changed"]
        observed = _route(
            "Implement an accepted backend service behavior change.",
            data,
        )
        self.assertEqual(
            "backend-change-builder",
            _projected_route(observed)["primary_skill"],
        )


class ImplementationFamilyClassifierTests(unittest.TestCase):
    def test_classifier_has_nine_positive_unchanged_and_anti_contracts(self) -> None:
        classify = getattr(ORACLE, "classify_professional_families", None)
        self.assertTrue(
            callable(classify),
            "semantic Professional family classifier is missing",
        )
        positives = {
            "backend": "Implement an accepted backend service behavior change.",
            "frontend": (
                "Implement an accepted browser frontend component state change."
            ),
            "installed-client": (
                "Implement an accepted Android installed application lifecycle change."
            ),
            "data-middleware": (
                "Implement an accepted queue middleware consistency change."
            ),
            "integration": (
                "Implement an accepted external integration contract change."
            ),
            "repository-tooling": (
                "Implement an accepted repository code generator source change."
            ),
            "platform-infrastructure": (
                "Implement an accepted Terraform module source change."
            ),
            "test-validation": (
                "Implement regression tests proving the changed behavior."
            ),
            "logging": (
                "Implement a structured redacted logging schema change."
            ),
        }
        negatives = {
            "backend": "Inspect backend service source only; behavior is unchanged.",
            "frontend": (
                "Explore frontend component design without implementation."
            ),
            "installed-client": (
                "Implement a browser or PWA-only frontend component change."
            ),
            "data-middleware": (
                "Inspect queue terminology; there is no middleware impact."
            ),
            "integration": (
                "Implement an isolated change with no integration edge."
            ),
            "repository-tooling": (
                "Implement backend product business logic; repository tooling is unchanged."
            ),
            "platform-infrastructure": (
                "Approve a production Terraform apply, deployment, and rollback."
            ),
            "test-validation": (
                "Validation is already fresh and complete; there is no material change."
            ),
            "logging": (
                "Implement backend behavior with no logging impact."
            ),
        }
        for family, prompt in positives.items():
            with self.subTest(family=family, polarity="changed"):
                observed = classify(prompt)
                self.assertIn(family, {item["routing_family"] for item in observed})
                for item in observed:
                    self.assertEqual(
                        sorted(set(item["match_evidence"])),
                        item["match_evidence"],
                    )
        for family, prompt in negatives.items():
            with self.subTest(family=family, polarity="unchanged-or-anti"):
                observed = classify(prompt)
                self.assertNotIn(
                    family,
                    {item["routing_family"] for item in observed},
                )

    def test_test_only_task_type_precedes_product_surface_owners(
        self,
    ) -> None:
        document = load_yaml_file(
            ROOT
            / "evals"
            / "capability-coverage"
            / "admission-cases.yaml"
        )
        self.assertIsInstance(document, dict)
        rows = {
            row["id"]: row
            for row in document["cases"]
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        authority_id = (
            "capcov-admission-foundation-client-testing-decision"
        )
        self.assertIn(authority_id, rows)
        authority = rows[authority_id]
        self.assertEqual("foundation", authority["layer"])
        self.assertEqual("client-application-testing", authority["skill"])
        self.assertEqual("selected", authority["case_kind"])
        self.assertEqual(
            {
                "selected": True,
                "primary_skill": "quality-test-gate",
            },
            authority["expected"],
        )

        direct_test_route = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "quality-test-gate",
        }
        authority_route = {
            **direct_test_route,
            "review_skill": "ai-code-review-refactor",
        }
        conflict_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
        }
        critical_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        proof = {
            "decision_route_once": True,
            "trace_route_once": "proven",
            "candidate_coverage": "full",
        }
        quality_owner = "implementation-owner:quality-test-gate"
        cases = {
            "authority:client-testing-decision": {
                "prompt": authority["prompt"],
                "main_execution": authority["main_execution"],
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": authority_route,
                "layer3_contract": {
                    "scope": "selected-exact",
                    "expected": [
                        "regression-testing",
                        "client-application-testing",
                    ],
                },
                "selected_domains": [],
            },
            "test-only:server-side-behavior": {
                "prompt": (
                    "Implement regression tests proving server-side behavior."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:command-line-service-behavior": {
                "prompt": (
                    "Update command-line service regression test coverage."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:installed-client-screen-behavior": {
                "prompt": (
                    "Update regression test coverage for installed-client "
                    "screen behavior."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:android-screen-behavior": {
                "prompt": "Add regression tests for Android screen behavior.",
                "classifier_only": True,
                "families": ["test-validation"],
                "domains": [
                    (
                        "android-platform-extension",
                        "platform-lifecycle-authority",
                    )
                ],
            },
            "test-only:without-changing-server-side-source": {
                "prompt": (
                    "Add regression tests without changing server-side source."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:action-like-backend-change-referent": {
                "prompt": (
                    "Add regression tests for the accepted backend revision."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:action-like-migration-plan-referent": {
                "prompt": "Add regression tests for the migration proposal.",
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:referent-caller-implement-action": {
                "prompt": (
                    "Add regression tests proving callers can implement an "
                    "accepted backend behavior revision."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "test-only:negated-later-product-action": {
                "prompt": (
                    "Add regression tests, then do not implement an accepted "
                    "backend behavior revision."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "review87:for-referent-then-backend-product-action": {
                "prompt": (
                    "Add regression tests for process death then implement an "
                    "accepted backend service behavior change."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "review87:proving-subordinate-then-backend-product-action": {
                "prompt": (
                    "Add regression tests proving callers can implement an "
                    "accepted backend behavior change then implement an "
                    "accepted backend service behavior change."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "review87:noun-before-test-order-guard": {
                "prompt": (
                    "Add the accepted backend revision regression tests."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "review91:for-referent-need-to-create-backend-product": {
                "prompt": (
                    "Add regression tests for process death then we need to "
                    "create an accepted backend service."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "review91:proving-referent-need-to-create-backend-product": {
                "prompt": (
                    "Add regression tests proving caller behavior then we "
                    "need to create an accepted backend service."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "review95:proving-api-callers-multitoken-subordinate": {
                "prompt": (
                    "Add regression tests proving API callers can implement "
                    "an accepted backend behavior revision."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "review95:for-api-callers-multitoken-subordinate": {
                "prompt": (
                    "Add regression tests for API callers to implement an "
                    "accepted backend behavior revision."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "selected": quality_owner,
                "route": direct_test_route,
                "layer3_contract": {
                    "scope": "quality-owner-membership",
                    "expected": "regression-testing",
                },
                "selected_domains": [],
            },
            "critical-ambiguity:backend-change-referent": {
                "prompt": (
                    "Add regression tests for the accepted backend change."
                ),
                "main_execution": _terminal_action_ambiguity_main(
                    "Add regression tests for the accepted backend change."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "ordinary_candidates": ["ordinary-ambiguity"],
                "selected": "ordinary-ambiguity",
                "route": critical_route,
                "proof_limit_main": True,
                "selected_domains": [],
            },
            "critical-ambiguity:migration-plan-referent": {
                "prompt": "Add regression tests for the migration plan.",
                "main_execution": _terminal_action_ambiguity_main(
                    "Add regression tests for the migration plan."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "ordinary_candidates": ["ordinary-ambiguity"],
                "selected": "ordinary-ambiguity",
                "route": critical_route,
                "proof_limit_main": True,
                "selected_domains": [],
            },
            "critical-ambiguity:noun-before-test-order": {
                "prompt": "Add the accepted backend change regression tests.",
                "main_execution": _terminal_action_ambiguity_main(
                    "Add the accepted backend change regression tests."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "ordinary_candidates": ["ordinary-ambiguity"],
                "selected": "ordinary-ambiguity",
                "route": critical_route,
                "proof_limit_main": True,
                "selected_domains": [],
            },
            "critical-ambiguity:terminal-for": {
                "prompt": "Add regression tests for API callers implement.",
                "main_execution": _terminal_action_ambiguity_main(
                    "Add regression tests for API callers implement."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "ordinary_candidates": ["ordinary-ambiguity"],
                "selected": "ordinary-ambiguity",
                "route": critical_route,
                "proof_limit_main": True,
                "selected_domains": [],
            },
            "critical-ambiguity:terminal-for-article": {
                "prompt": (
                    "Add regression tests for the API callers implement."
                ),
                "main_execution": _terminal_action_ambiguity_main(
                    "Add regression tests for the API callers implement."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "ordinary_candidates": ["ordinary-ambiguity"],
                "selected": "ordinary-ambiguity",
                "route": critical_route,
                "proof_limit_main": True,
                "selected_domains": [],
            },
            "critical-ambiguity:terminal-proving": {
                "prompt": "Add regression tests proving API callers implement.",
                "main_execution": _terminal_action_ambiguity_main(
                    "Add regression tests proving API callers implement."
                ),
                "families": ["test-validation"],
                "domains": [],
                "owners": [quality_owner],
                "ordinary_candidates": ["ordinary-ambiguity"],
                "selected": "ordinary-ambiguity",
                "route": critical_route,
                "proof_limit_main": True,
                "selected_domains": [],
            },
            "product-plus-tests:backend": {
                "prompt": (
                    "Add regression tests and implement an accepted backend "
                    "service behavior change."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "product-plus-tests:installed-client": {
                "prompt": (
                    "Implement an accepted installed-client screen behavior "
                    "change and add regression tests."
                ),
                "families": ["installed-client", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:installed-client-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "multiaction:backend-product-first-then-add-tests": {
                "prompt": (
                    "Implement an accepted backend service behavior change "
                    "then add regression tests."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "multiaction:backend-test-first-then-implement-product": {
                "prompt": (
                    "Add regression tests then implement an accepted backend "
                    "service behavior change."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
            "multiaction:backend-product-first-to-add-tests": {
                "prompt": (
                    "Implement an accepted backend service behavior change "
                    "to add regression tests."
                ),
                "families": ["backend", "test-validation"],
                "domains": [],
                "owners": [
                    "implementation-owner:backend-change-builder",
                    quality_owner,
                ],
                "selected": "implementation-owner-conflict",
                "route": conflict_route,
                "selected_domains": [],
            },
        }

        mismatches: list[str] = []
        executed: list[str] = []
        for label, case in cases.items():
            executed.append(label)
            prompt = case["prompt"]
            actual_families = [
                item["routing_family"]
                for item in ORACLE.classify_professional_families(prompt)
            ]
            actual_domains = ORACLE.domain_route_families(prompt)
            if case.get("classifier_only") is True:
                actual = {
                    "families": actual_families,
                    "domains": actual_domains,
                }
                expected = {
                    "families": case["families"],
                    "domains": case["domains"],
                }
                if actual != expected:
                    mismatches.append(
                        f"[{label}] mismatch=test-only-precedence; "
                        f"expected={expected!r}; actual={actual!r}"
                    )
                continue

            observed = (
                ORACLE.route_with_trace(
                    prompt,
                    main_execution=copy.deepcopy(case["main_execution"]),
                )
                if "main_execution" in case
                else _route(prompt)
            )
            trace = observed["winner_trace"]
            route = _projected_route(observed)
            raw_candidates = trace["raw_candidates"]
            actual = {
                "families": actual_families,
                "domains": actual_domains,
                "owners": [
                    item["candidate_id"]
                    for item in raw_candidates
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ],
                "selected": trace["selected_candidate"]["candidate_id"],
                "route": {
                    key: route[key]
                    for key in case["route"]
                },
                "proof": {
                    "decision_route_once": observed["route_decision"].get(
                        "route_once"
                    ),
                    "trace_route_once": trace.get("route_once"),
                    "candidate_coverage": trace.get("candidate_coverage"),
                },
            }
            expected = {
                "families": case["families"],
                "domains": case["domains"],
                "owners": case["owners"],
                "selected": case["selected"],
                "route": case["route"],
                "proof": proof,
            }
            if case.get("proof_limit_main") is True:
                supplied_main = case["main_execution"]
                decision = observed["route_decision"]
                route_result = decision["route_result"]
                actual["ordinary_candidates"] = [
                    item["candidate_id"]
                    for item in raw_candidates
                    if item["candidate_id"] == "ordinary-ambiguity"
                ]
                expected["ordinary_candidates"] = case[
                    "ordinary_candidates"
                ]
                actual["proof_limit_source"] = (
                    "proof-limit:terminal-task-action-ambiguity"
                    in trace["selected_candidate"].get("evidence", [])
                )
                expected["proof_limit_source"] = True
                actual["analysis_assignment_keys"] = set(supplied_main)
                expected["analysis_assignment_keys"] = {
                    "producer",
                    "task_id",
                }
                actual["main_provenance"] = decision[
                    "main_execution_provenance"
                ]
                expected["main_provenance"] = None
                actual["execution_level"] = route_result["execution_level"]
                expected["execution_level"] = None
                actual["level_basis"] = route_result["level_basis"]
                expected["level_basis"] = None
            layer3_contract = case.get("layer3_contract")
            if isinstance(layer3_contract, dict):
                if layer3_contract["scope"] == "selected-exact":
                    actual["layer3"] = route["layer3_skills"]
                    expected["layer3"] = layer3_contract["expected"]
                else:
                    quality_candidates = [
                        item
                        for item in raw_candidates
                        if item["candidate_id"] == quality_owner
                    ]
                    expected_layer3 = layer3_contract["expected"]
                    actual["risk_layer3_present"] = (
                        len(quality_candidates) == 1
                        and expected_layer3
                        in quality_candidates[0].get("layer3_skills", [])
                    )
                    expected["risk_layer3_present"] = True
            if "selected_domains" in case:
                actual["selected_domains"] = sorted(
                    set(route["layer3_skills"])
                    & T2E_ECA_DOMAIN_ADDITIONS
                )
                expected["selected_domains"] = case["selected_domains"]
            if actual != expected:
                mismatches.append(
                    f"[{label}] mismatch=test-only-precedence; "
                    f"expected={expected!r}; actual={actual!r}"
                )

        expected_labels = list(cases)
        if executed != expected_labels:
            mismatches.append(
                "[test-only-precedence] mismatch=case-execution; "
                f"expected={expected_labels!r}; actual={executed!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_terminal_action_ambiguity_main_provenance_is_closed(
        self,
    ) -> None:
        prompt = "Add regression tests for the accepted backend change."
        assignment = _terminal_action_ambiguity_main(prompt)
        self.assertEqual({"producer", "task_id"}, set(assignment))
        legacy_fabricated_level = _test_main_execution(prompt)
        expected_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for label, main_execution in (
            ("analysis-assignment", assignment),
            ("legacy-fabricated-level", legacy_fabricated_level),
        ):
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=copy.deepcopy(main_execution),
                )
                decision = observed["route_decision"]
                result = decision["route_result"]
                self.assertEqual(expected_route, _projected_route(observed))
                self.assertEqual(
                    "ordinary-ambiguity",
                    observed["winner_trace"]["selected_candidate"][
                        "candidate_id"
                    ],
                )
                self.assertIsNone(decision["main_execution_provenance"])
                self.assertIsNone(result["execution_level"])
                self.assertIsNone(result["level_basis"])

    def test_typed_task_action_parser_contract_and_fail_closed_issues(
        self,
    ) -> None:
        parser = getattr(
            ORACLE,
            "_parse_normalized_task_request",
            None,
        )
        self.assertTrue(
            callable(parser),
            "typed normalized task parser is missing",
        )

        critical_prompt = (
            "Add regression tests for the accepted backend change."
        )
        with patch.object(
            ORACLE,
            "_parse_normalized_task_request",
            wraps=parser,
        ) as parser_spy:
            ORACLE.route_with_trace(
                critical_prompt,
                main_execution=_terminal_action_ambiguity_main(
                    critical_prompt
                ),
            )
        self.assertEqual(1, parser_spy.call_count)

        direct_prompt = (
            "Add regression tests for the accepted backend revision."
        )
        with patch.object(
            ORACLE,
            "_parse_normalized_task_request",
            wraps=parser,
        ) as parser_spy:
            ORACLE.classify_professional_families(direct_prompt)
        self.assertEqual(1, parser_spy.call_count)

        expected_fields = {
            "_ParsedTaskRequest": ("value", "task_actions"),
            "_TaskSpan": ("normalized", "source"),
            "_TaskActionParse": (
                "source_text",
                "normalized_text",
                "actions",
                "objects",
                "lexemes",
                "issues",
                "blocking_terminal_spans",
            ),
            "_TaskActionNode": (
                "action_id",
                "statement_id",
                "clause_id",
                "role",
                "verb",
                "polarity",
                "prefix_kind",
                "parent_action_id",
                "clause_span",
                "verb_span",
                "prefix_span",
                "subject_span",
                "object_span",
                "referent_marker_span",
                "coordinator_span",
            ),
            "_TaskObjectNode": (
                "object_id",
                "parent_action_id",
                "parent_object_id",
                "role",
                "span",
                "complete",
            ),
            "_TaskLexeme": (
                "lexeme",
                "raw_match_span",
                "legacy_recognized",
                "disposition",
                "action_id",
                "issue_code",
            ),
            "_TaskActionIssue": ("code", "span", "action_id"),
        }

        def assert_frozen_shape(
            value: object,
            type_name: str,
        ) -> None:
            self.assertTrue(dataclasses.is_dataclass(value), type_name)
            self.assertTrue(
                type(value).__dataclass_params__.frozen,
                type_name,
            )
            self.assertEqual(
                expected_fields[type_name],
                tuple(field.name for field in dataclasses.fields(value)),
                type_name,
            )

        def span_text(value: str, span: object) -> str:
            assert_frozen_shape(span, "_TaskSpan")
            self.assertEqual(span.normalized, span.source)
            start, end = span.normalized
            self.assertIsInstance(start, int)
            self.assertIsInstance(end, int)
            self.assertLess(start, end)
            self.assertEqual(
                value[start:end],
                value[span.source[0] : span.source[1]],
            )
            return value[start:end]

        def parsed_task(prompt: str) -> tuple[object, object]:
            normalized = " ".join(prompt.casefold().split())
            parsed = parser(normalized)
            assert_frozen_shape(parsed, "_ParsedTaskRequest")
            self.assertEqual(normalized, parsed.value)
            task = parsed.task_actions
            assert_frozen_shape(task, "_TaskActionParse")
            self.assertEqual(normalized, task.source_text)
            self.assertEqual(normalized, task.normalized_text)
            action_ids = [action.action_id for action in task.actions]
            self.assertEqual(len(action_ids), len(set(action_ids)))
            self.assertEqual(
                sorted(
                    action_ids,
                    key=lambda identifier: next(
                        action.verb_span.normalized[0]
                        for action in task.actions
                        if action.action_id == identifier
                    ),
                ),
                action_ids,
            )
            for action in task.actions:
                assert_frozen_shape(action, "_TaskActionNode")
                self.assertIn(
                    action.role,
                    {
                        "direct",
                        "coordinated",
                        "referent-complement",
                        "ambiguous",
                    },
                )
                self.assertIn(
                    action.polarity,
                    {"changed", "unchanged", "ambiguous"},
                )
                self.assertIn(
                    action.prefix_kind,
                    {
                        "none",
                        "directive",
                        "modal",
                        "infinitive",
                        "negative",
                    },
                )
                span_text(normalized, action.clause_span)
                self.assertEqual(
                    action.verb,
                    span_text(normalized, action.verb_span),
                )
                if action.parent_action_id is not None:
                    self.assertIn(action.parent_action_id, action_ids)
                for name in (
                    "prefix_span",
                    "subject_span",
                    "object_span",
                    "referent_marker_span",
                    "coordinator_span",
                ):
                    span = getattr(action, name)
                    if span is not None:
                        span_text(normalized, span)
            for item in task.objects:
                assert_frozen_shape(item, "_TaskObjectNode")
                self.assertIn(
                    item.role,
                    {
                        "test-object",
                        "ordinary-object",
                        "nominal-referent",
                    },
                )
                self.assertIn(item.parent_action_id, action_ids)
                span_text(normalized, item.span)
            lexeme_spans = []
            for item in task.lexemes:
                assert_frozen_shape(item, "_TaskLexeme")
                self.assertIn(
                    item.disposition,
                    {
                        "action-node",
                        "non-action-object-lexeme",
                        "blocking-ambiguous",
                        "blocking-unconsumed",
                    },
                )
                span_text(normalized, item.raw_match_span)
                lexeme_spans.append(item.raw_match_span.normalized)
            self.assertEqual(len(lexeme_spans), len(set(lexeme_spans)))
            for item in task.issues:
                assert_frozen_shape(item, "_TaskActionIssue")
                span_text(normalized, item.span)
            for span in task.blocking_terminal_spans:
                span_text(normalized, span)
            return parsed, task

        referent_cases = (
            (
                "Add regression tests proving API callers can implement an "
                "accepted backend behavior revision.",
                "proving",
                "can",
                "api callers",
                "an accepted backend behavior revision",
            ),
            (
                "Add regression tests for API callers to implement an "
                "accepted backend behavior revision.",
                "for",
                "to",
                "api callers",
                "an accepted backend behavior revision",
            ),
        )
        for prompt, marker, prefix, subject, object_text in referent_cases:
            with self.subTest(contract="referent-complement", prompt=prompt):
                _, task = parsed_task(prompt)
                add = next(action for action in task.actions if action.verb == "add")
                implement = next(
                    action
                    for action in task.actions
                    if action.verb == "implement"
                )
                self.assertEqual(("direct", "changed"), (add.role, add.polarity))
                self.assertEqual(
                    ("referent-complement", "changed", add.action_id),
                    (
                        implement.role,
                        implement.polarity,
                        implement.parent_action_id,
                    ),
                )
                self.assertEqual(
                    marker,
                    span_text(task.normalized_text, implement.referent_marker_span),
                )
                self.assertEqual(
                    prefix,
                    span_text(task.normalized_text, implement.prefix_span),
                )
                self.assertEqual(
                    subject,
                    span_text(task.normalized_text, implement.subject_span),
                )
                self.assertEqual(
                    object_text,
                    span_text(task.normalized_text, implement.object_span),
                )

        coordinated_cases = (
            (
                "Add regression tests and then create an accepted backend service.",
                "create",
                "changed",
                "and then",
            ),
            (
                "Add regression tests, then create an accepted backend service.",
                "create",
                "changed",
                "then",
            ),
            (
                "Add regression tests, then we need to create an accepted "
                "backend service.",
                "create",
                "changed",
                "then",
            ),
            (
                "Add regression tests, then do not implement an accepted "
                "backend behavior revision.",
                "implement",
                "unchanged",
                "then",
            ),
        )
        for prompt, verb, polarity, coordinator in coordinated_cases:
            with self.subTest(contract="coordinated", prompt=prompt):
                _, task = parsed_task(prompt)
                action = next(
                    item for item in task.actions if item.verb == verb
                )
                self.assertEqual("coordinated", action.role)
                self.assertEqual(polarity, action.polarity)
                self.assertEqual(
                    coordinator,
                    span_text(task.normalized_text, action.coordinator_span),
                )
                if polarity == "unchanged":
                    self.assertEqual("negative", action.prefix_kind)
                    self.assertEqual(
                        "do not",
                        span_text(task.normalized_text, action.prefix_span),
                    )

        terminal_cases = (
            (
                "Add regression tests for the accepted backend change.",
                "change",
            ),
            ("Add regression tests for the migration plan.", "plan"),
            (
                "Add the accepted backend change regression tests.",
                "change",
            ),
            ("Add regression tests for API callers implement.", "implement"),
            (
                "Add regression tests for the API callers implement.",
                "implement",
            ),
            (
                "Add regression tests proving API callers implement.",
                "implement",
            ),
        )
        for prompt, lexeme_text in terminal_cases:
            with self.subTest(contract="terminal-ambiguity", prompt=prompt):
                _, task = parsed_task(prompt)
                lexemes = [
                    item
                    for item in task.lexemes
                    if item.lexeme == lexeme_text
                    and item.disposition == "blocking-ambiguous"
                ]
                self.assertEqual(1, len(lexemes))
                self.assertFalse(lexemes[0].legacy_recognized)
                self.assertIn(
                    lexemes[0].raw_match_span,
                    task.blocking_terminal_spans,
                )

        issue_cases = (
            ("missing-object", "Add."),
            (
                "missing-referent-subject",
                "Add regression tests proving can implement backend behavior.",
            ),
            (
                "ambiguous-weak-coordination",
                "Add regression tests proving callers can implement or create "
                "an accepted backend service.",
            ),
            (
                "multiple-action-prefixes",
                "Add regression tests proving callers can need to implement "
                "backend behavior.",
            ),
            (
                "unsupported-referent-nesting",
                "Add regression tests proving callers can implement checks "
                "proving clients can create services.",
            ),
            (
                "unbalanced-delimiter",
                'Add regression tests proving "callers can implement backend behavior.',
            ),
            (
                "unconsumed-action-lexeme",
                "Background implement an accepted backend service.",
            ),
            (
                "unconsumed-action-lexeme",
                "Add regression tests background implement an accepted "
                "backend service.",
            ),
            (
                "unconsumed-action-lexeme",
                "Add regression tests background implement.",
            ),
        )
        for issue_code, prompt in issue_cases:
            with self.subTest(contract="issue", prompt=prompt):
                _, task = parsed_task(prompt)
                self.assertIn(
                    issue_code,
                    [item.code for item in task.issues],
                )
                self.assertNotIn(
                    "test-validation",
                    {
                        item["routing_family"]
                        for item in ORACLE.classify_professional_families(prompt)
                    },
                )

    def test_terminal_action_ambiguity_is_structural_not_lexical(
        self,
    ) -> None:
        canonical_prompt = (
            "Select regression tests for a unit test or local performance "
            "revision with no runtime objective."
        )
        old_canonical_prompt = (
            "Select regression tests for a unit test or local performance "
            "change with no runtime objective."
        )
        direct_quality_route = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "quality-test-gate",
            "layer3_skills": ["regression-testing"],
            "review_skill": "ai-code-review-refactor",
        }
        ambiguity_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        direct_backend_route = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "backend-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        }
        quality_owner = "implementation-owner:quality-test-gate"
        proof_limit_source = "proof-limit:terminal-task-action-ambiguity"
        mismatches: list[str] = []
        parser = getattr(
            ORACLE,
            "_parse_normalized_task_request",
            None,
        )

        if "_TASK_TERMINAL_HOMOGRAPHS" in vars(ORACLE):
            mismatches.append(
                "[authority] forbidden named terminal-homograph "
                "authority remains present"
            )
        if not callable(parser):
            mismatches.append(
                "[typed-parser] typed normalized parser is missing"
            )

        document = load_yaml_file(ROOT / "evals" / "routing" / "cases.yaml")
        canonical_rows = [
            row
            for row in document["cases"]
            if row.get("id") == "reliability-anti-unit-local-performance"
        ]
        wave1a_rows = [
            row
            for row in document["cases"]
            if str(row.get("id", "")).startswith("wave1a-")
        ]
        if len(wave1a_rows) != 30:
            mismatches.append(
                "[canonical-fixture] Wave1A fixture-count drift; "
                f"expected=30; actual={len(wave1a_rows)}"
            )
        if len(document["cases"]) != 233:
            mismatches.append(
                "[canonical-fixture] total case-count drift; "
                f"expected=233; actual={len(document['cases'])}"
            )
        if len(document["cases"]) - len(wave1a_rows) != 203:
            mismatches.append(
                "[canonical-fixture] predecessor case-count drift; "
                "expected=203; actual="
                f"{len(document['cases']) - len(wave1a_rows)}"
            )
        if len(canonical_rows) != 1:
            mismatches.append(
                "[canonical-fixture] stable row must occur exactly once; "
                f"actual={len(canonical_rows)}"
            )
        else:
            canonical = canonical_rows[0]
            if canonical["prompt"] != canonical_prompt:
                mismatches.append(
                    "[canonical-fixture] prompt mismatch; "
                    f"expected={canonical_prompt!r}; "
                    f"actual={canonical['prompt']!r}"
                )
            if canonical["excluded_skills"] != [
                "reliability-observability-gate"
            ]:
                mismatches.append(
                    "[canonical-fixture] excluded skill drift; "
                    f"actual={canonical['excluded_skills']!r}"
                )
            if canonical["expected"] != direct_quality_route:
                mismatches.append(
                    "[canonical-fixture] expected route drift; "
                    f"expected={direct_quality_route!r}; "
                    f"actual={canonical['expected']!r}"
                )
            observed = ORACLE.route_with_trace(
                canonical_prompt,
                main_execution=copy.deepcopy(canonical["main_execution"]),
            )
            actual_route = _projected_route(observed)
            if actual_route != direct_quality_route:
                mismatches.append(
                    "[canonical-fixture] replacement route mismatch; "
                    f"expected={direct_quality_route!r}; "
                    f"actual={actual_route!r}"
                )
            if callable(parser):
                parsed = parser(
                    " ".join(canonical_prompt.casefold().split())
                )
                task = parsed.task_actions
                raw_candidates = observed["winner_trace"][
                    "raw_candidates"
                ]
                actual_typed = {
                    "actions": [
                        (
                            item.action_id,
                            item.verb,
                            item.role,
                            item.parent_action_id,
                        )
                        for item in task.actions
                    ],
                    "objects": [
                        (
                            item.parent_action_id,
                            item.role,
                            item.complete,
                        )
                        for item in task.objects
                    ],
                    "lexemes": [
                        (
                            item.lexeme,
                            item.disposition,
                            item.action_id,
                        )
                        for item in task.lexemes
                    ],
                    "blocking_spans": list(
                        task.blocking_terminal_spans
                    ),
                    "families": [
                        item["routing_family"]
                        for item in ORACLE.classify_professional_families(
                            canonical_prompt
                        )
                    ],
                    "quality_owner_present": quality_owner
                    in {
                        item["candidate_id"]
                        for item in raw_candidates
                    },
                    "reliability_candidates": [
                        item["candidate_id"]
                        for item in raw_candidates
                        if item.get("primary_skill")
                        == "reliability-observability-gate"
                    ],
                }
                expected_typed = {
                    "actions": [
                        ("action-1", "select", "direct", None),
                    ],
                    "objects": [
                        ("action-1", "test-object", True),
                    ],
                    "lexemes": [
                        ("select", "action-node", "action-1"),
                    ],
                    "blocking_spans": [],
                    "families": ["test-validation"],
                    "quality_owner_present": True,
                    "reliability_candidates": [],
                }
                if actual_typed != expected_typed:
                    mismatches.append(
                        "[canonical-fixture] replacement typed structure "
                        "mismatch; "
                        f"expected={expected_typed!r}; "
                        f"actual={actual_typed!r}"
                    )

        critical_cases = {
            "old-canonical": old_canonical_prompt,
            "generic-fix": (
                "Select regression tests for API callers fix with no "
                "runtime objective."
            ),
            "g3": (
                "Select regression tests for API callers change with no "
                "runtime objective."
            ),
            "g4": (
                "Select regression tests for a unit test or API callers "
                "change with no runtime objective."
            ),
            "g5": (
                "Select regression tests for a unit test or the API callers "
                "change with no runtime objective."
            ),
            "g6": (
                "Select regression tests for an API caller or the API "
                "callers change with no runtime objective."
            ),
        }
        for label, prompt in critical_cases.items():
            supplied_main = _terminal_action_ambiguity_main(prompt)
            observed = ORACLE.route_with_trace(
                prompt,
                main_execution=supplied_main,
            )
            trace = observed["winner_trace"]
            raw_ids = [
                item["candidate_id"]
                for item in trace["raw_candidates"]
            ]
            actual = {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(prompt)
                ],
                "quality_owner_present": quality_owner in raw_ids,
                "critical_present": "critical-unknown" in raw_ids,
                "ordinary_present": "ordinary-ambiguity" in raw_ids,
                "selected": trace["selected_candidate"]["candidate_id"],
                "proof_limit_source": proof_limit_source
                in trace["selected_candidate"].get("evidence", []),
                "route": _projected_route(observed),
            }
            expected = {
                "families": ["test-validation"],
                "quality_owner_present": True,
                "critical_present": False,
                "ordinary_present": True,
                "selected": "ordinary-ambiguity",
                "proof_limit_source": True,
                "route": ambiguity_route,
            }
            if label == "old-canonical":
                decision = observed["route_decision"]
                route_result = decision["route_result"]
                actual["main_provenance_bytes"] = json.dumps(
                    decision["main_execution_provenance"],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected["main_provenance_bytes"] = b"null"
                actual["execution_level_bytes"] = json.dumps(
                    route_result["execution_level"],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected["execution_level_bytes"] = b"null"
                actual["level_basis_bytes"] = json.dumps(
                    route_result["level_basis"],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected["level_basis_bytes"] = b"null"
            if actual != expected:
                mismatches.append(
                    f"[critical:{label}] structural ambiguity mismatch; "
                    f"expected={expected!r}; actual={actual!r}"
                )

        direct_cases = {
            "recognized-can": (
                "Select regression tests proving API callers can fix an "
                "accepted backend behavior revision with no runtime objective."
            ),
            "recognized-to": (
                "Select regression tests for API callers to fix an accepted "
                "backend behavior revision with no runtime objective."
            ),
        }
        for label, prompt in direct_cases.items():
            observed = _route(prompt)
            typed = {
                "select_nodes": None,
                "fix_nodes": None,
                "fix_lexemes": None,
            }
            if callable(parser):
                task = parser(
                    " ".join(prompt.casefold().split())
                ).task_actions
                typed = {
                    "select_nodes": [
                        (item.action_id, item.role)
                        for item in task.actions
                        if item.verb == "select"
                    ],
                    "fix_nodes": [
                        (
                            item.action_id,
                            item.role,
                            item.parent_action_id,
                        )
                        for item in task.actions
                        if item.verb == "fix"
                    ],
                    "fix_lexemes": [
                        (
                            item.disposition,
                            item.action_id,
                        )
                        for item in task.lexemes
                        if item.lexeme == "fix"
                    ],
                }
            actual = {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(prompt)
                ],
                "selected": observed["winner_trace"]["selected_candidate"][
                    "candidate_id"
                ],
                "route": _projected_route(observed),
                **typed,
            }
            expected = {
                "families": ["test-validation"],
                "selected": quality_owner,
                "route": direct_quality_route,
                "select_nodes": [("action-1", "direct")],
                "fix_nodes": [
                    (
                        "action-2",
                        "referent-complement",
                        "action-1",
                    ),
                ],
                "fix_lexemes": [("action-node", "action-2")],
            }
            if actual != expected:
                mismatches.append(
                    f"[direct:{label}] referent route mismatch; "
                    f"expected={expected!r}; actual={actual!r}"
                )

        backend_prompt = "Implement an accepted backend fix."
        backend = _route(backend_prompt)
        backend_typed = {
            "objects": None,
            "fix_lexemes": None,
        }
        if callable(parser):
            task = parser(
                " ".join(backend_prompt.casefold().split())
            ).task_actions
            backend_typed = {
                "objects": [
                    (
                        item.parent_action_id,
                        item.role,
                        item.complete,
                    )
                    for item in task.objects
                ],
                "fix_lexemes": [
                    (
                        item.disposition,
                        item.action_id,
                    )
                    for item in task.lexemes
                    if item.lexeme == "fix"
                ],
            }
        actual_backend = {
            "families": [
                item["routing_family"]
                for item in ORACLE.classify_professional_families(
                    backend_prompt
                )
            ],
            "selected": backend["winner_trace"]["selected_candidate"][
                "candidate_id"
            ],
            "route": _projected_route(backend),
            **backend_typed,
        }
        expected_backend = {
            "families": ["backend"],
            "selected": "implementation-owner:backend-change-builder",
            "route": direct_backend_route,
            "objects": [
                ("action-1", "ordinary-object", True),
            ],
            "fix_lexemes": [
                ("non-action-object-lexeme", "action-1"),
            ],
        }
        if actual_backend != expected_backend:
            mismatches.append(
                "[direct:ordinary-backend-fix] route mismatch; "
                f"expected={expected_backend!r}; actual={actual_backend!r}"
            )

        if mismatches:
            self.fail("\n".join(mismatches))

    def test_repository_owner_filter_conserves_independent_changed_actions(
        self,
    ) -> None:
        cases = (
            (
                "Implement an accepted repository CLI path registration for "
                "the same user. Implement a separate backend service behavior "
                "change.",
                "Implement a separate backend service behavior change. Implement "
                "an accepted repository CLI path registration for the same user.",
            ),
            (
                "Update accepted repository CLI help text only. Write a separate "
                "backend file for runtime service behavior.",
                "Write a separate backend file for runtime service behavior. "
                "Update accepted repository CLI help text only.",
            ),
        )
        for pair_index, prompts in enumerate(cases):
            observed = []
            for source_order, prompt in enumerate(prompts):
                with self.subTest(
                    pair=pair_index,
                    source_order=source_order,
                ):
                    result = _route(prompt)
                    projected = _projected_route(result)
                    observed.append(projected)
                    self.assertEqual("analyzed", projected["path"])
                    self.assertEqual(
                        "engineering-change-analysis",
                        projected["primary_skill"],
                    )
                    self.assertEqual(
                        "implementation-owner-conflict",
                        result["winner_trace"]["selected_candidate"][
                            "candidate_id"
                        ],
                    )
                    self.assertEqual(
                        {
                            "backend:backend-change-builder",
                            "repository-tooling:repository-tooling-change-builder",
                        },
                        set(
                            result["winner_trace"]["selected_candidate"][
                                "evidence"
                            ]
                        ),
                    )
            self.assertEqual(observed[0], observed[1])

    def test_nominal_add_dir_modifiers_remain_action_local(self) -> None:
        prompt = (
            "Implement repository CLI registration of ~/.copilot/skills as the "
            "--add-dir path for the same OS user; the bounded local resource is "
            "non-sensitive and unprivileged, authority remains unchanged."
        )
        normalized = " ".join(prompt.casefold().split())
        typed = ORACLE._routing_boundary_fact_snapshots(
            normalized,
            parsed=ORACLE._parse_normalized_task_request(normalized),
        )
        self.assertEqual(1, len(typed))
        facts = typed[0]
        self.assertTrue(facts.repository_owner)
        self.assertEqual("register", facts.path_mutation)
        self.assertEqual("changed", facts.filesystem_behavior)
        self.assertEqual("same_principal", facts.writer_identity)
        self.assertEqual("same_trust", facts.writer_trust)
        self.assertEqual("absent", facts.sensitive_asset)
        self.assertEqual("absent", facts.privileged_consumption)
        self.assertEqual("unchanged", facts.authority_delta)

        observed = _projected_route(_route(prompt))
        self.assertEqual(
            "repository-tooling-change-builder",
            observed["primary_skill"],
        )
        self.assertIn(
            "filesystem-process-safety",
            observed["layer3_skills"],
        )
        self.assertNotEqual("security-privacy-gate", observed["review_skill"])

        cross_clause = (
            "Implement repository CLI registration. "
            "A separate note names ~/.copilot/skills as an --add-dir path for a "
            "non-sensitive unprivileged resource with unchanged authority."
        )
        cross_normalized = " ".join(cross_clause.casefold().split())
        cross_typed = ORACLE._routing_boundary_fact_snapshots(
            cross_normalized,
            parsed=ORACLE._parse_normalized_task_request(cross_normalized),
        )
        self.assertEqual(1, len(cross_typed))
        self.assertTrue(cross_typed[0].repository_owner)
        self.assertEqual("none", cross_typed[0].path_mutation)
        self.assertNotEqual("same_principal", cross_typed[0].writer_identity)
        self.assertNotEqual("absent", cross_typed[0].sensitive_asset)

    def test_clause_local_coordinated_negation_denies_each_security_sink(
        self,
    ) -> None:
        prompt = (
            "Analyze a proved reachable repository path controlled by a "
            "less-trusted writer where no sensitive data or privileged "
            "consumption is involved."
        )
        normalized = " ".join(prompt.casefold().split())
        typed = ORACLE._routing_boundary_fact_snapshots(
            normalized,
            parsed=ORACLE._parse_normalized_task_request(normalized),
        )
        self.assertEqual(1, len(typed))
        self.assertEqual("less_trusted", typed[0].writer_trust)
        self.assertEqual("proved", typed[0].reachable_path)
        self.assertEqual("absent", typed[0].sensitive_asset)
        self.assertEqual("absent", typed[0].privileged_consumption)

        observed = _projected_route(_route(prompt))
        self.assertEqual("analyzed", observed["path"])
        self.assertEqual("engineering-change-analysis", observed["primary_skill"])
        self.assertNotEqual("security-privacy-gate", observed["review_skill"])

        positive = prompt.replace(
            "where no sensitive data or privileged consumption is involved",
            "where a privileged consumer is involved",
        )
        self.assertEqual(
            "security-privacy-gate",
            _projected_route(_route(positive))["primary_skill"],
        )

        cross_sentence = (
            "Analyze a proved reachable repository path controlled by a "
            "less-trusted writer that reaches a privileged service. No sensitive "
            "data or privileged consumption is involved in a separate "
            "documentation action."
        )
        cross_observed = _projected_route(_route(cross_sentence))
        self.assertEqual(
            "security-privacy-gate",
            cross_observed["primary_skill"],
        )

    def test_filesystem_selector_has_exact_security_review_bindings(self) -> None:
        selector_id = "dynamic-foundation:filesystem-process-safety"
        owners = {
            "backend": "backend-change-builder",
            "repository-tooling": "repository-tooling-change-builder",
            "installed-client": "installed-client-change-builder",
        }
        expected_bindings = {
            (
                f"implementation-owner:{primary}",
                None,
                family,
                primary,
                review,
            )
            for family, primary in owners.items()
            for review in (
                "ai-code-review-refactor",
                "security-privacy-gate",
            )
        }
        self.assertEqual(
            expected_bindings,
            set(ORACLE._DYNAMIC_FOUNDATION_OWNER_BINDINGS[selector_id]),
        )

        prompts = {
            "backend": (
                "Implement an accepted backend service behavior to atomically "
                "replace a local settings file controlled by a less-trusted "
                "writer before a privileged service consumes it through a proved "
                "reachable permission boundary."
            ),
            "repository-tooling": (
                "Implement an accepted repository CLI behavior to atomically "
                "replace a local settings file controlled by a less-trusted "
                "writer before a privileged service consumes it through a proved "
                "reachable permission boundary."
            ),
            "installed-client": (
                "Implement an accepted Android installed-client behavior to "
                "atomically replace a local settings file controlled by a "
                "less-trusted writer before a privileged service consumes it "
                "through a proved reachable permission boundary."
            ),
        }
        for family, prompt in prompts.items():
            with self.subTest(family=family):
                normalized = " ".join(prompt.casefold().split())
                facts = ORACLE._routing_boundary_fact_snapshots(
                    normalized,
                    parsed=ORACLE._parse_normalized_task_request(normalized),
                )
                self.assertEqual(1, len(facts))
                self.assertEqual("changed", facts[0].filesystem_behavior)
                self.assertTrue(ORACLE._security_boundary_is_proved(facts[0]))

                result = _route(prompt)
                projected = _projected_route(result)
                self.assertEqual(owners[family], projected["primary_skill"])
                self.assertEqual(
                    ["filesystem-process-safety"],
                    projected["layer3_skills"],
                )
                self.assertEqual(
                    "security-privacy-gate",
                    projected["review_skill"],
                )
                source_rows = result["winner_trace"]["selected_candidate"][
                    "source_foundation_candidates"
                ]
                self.assertEqual(
                    None,
                    result["winner_trace"]["selected_candidate"]["rule_id"],
                )
                self.assertEqual(1, len(source_rows))
                self.assertEqual(selector_id, source_rows[0]["candidate_id"])
                self.assertEqual(
                    {
                        "primary_skill": owners[family],
                        "review_skill": "security-privacy-gate",
                    },
                    source_rows[0]["owner_binding"],
                )

        safe = _projected_route(
            _route(
                "Implement the accepted maintenance utility to atomically swap "
                "its bounded local settings file for the same user; rollback is "
                "available, no sensitive data or elevated consumer is involved, "
                "and authority stays unchanged."
            )
        )
        self.assertEqual(
            "repository-tooling-change-builder",
            safe["primary_skill"],
        )
        self.assertEqual("ai-code-review-refactor", safe["review_skill"])

        boundary_without_filesystem = _projected_route(
            _route(
                "Implement an accepted repository CLI change that restricts an "
                "existing proved reachable permission boundary for a less-trusted "
                "writer before privileged consumption; authority is reduced."
            )
        )
        self.assertEqual(
            "security-privacy-gate",
            boundary_without_filesystem["review_skill"],
        )
        self.assertNotIn(
            "filesystem-process-safety",
            boundary_without_filesystem["layer3_skills"],
        )

        disconnected = _projected_route(
            _route(
                "Implement an accepted backend service behavior consumed by a "
                "privileged service. A separate local settings file has a "
                "less-trusted writer and a proved reachable path."
            )
        )
        self.assertEqual("backend-change-builder", disconnected["primary_skill"])
        self.assertEqual("ai-code-review-refactor", disconnected["review_skill"])

        authority = ORACLE.oracle_admission_authority()
        filesystem_record = next(
            record
            for record in authority.foundation_selectors
            if record.selector_id == selector_id
        )
        undeclared = {
            "candidate_id": "implementation-owner:frontend-change-builder",
            "rule_id": None,
            "routing_family": "frontend",
            "primary_skill": "frontend-change-builder",
            "review_skill": "security-privacy-gate",
            "evidence": ["browser-component-surface"],
        }
        self.assertFalse(
            ORACLE._foundation_route_binding_declared(
                undeclared,
                [filesystem_record],
            )
        )

        mutated_registry = copy.deepcopy(
            load_yaml_file(ROOT / "src" / "registry" / "foundation-skills.yaml")
        )
        mutated_selector = next(
            row
            for row in mutated_registry["selector_authority"]["selectors"]
            if row["selector_id"] == selector_id
        )
        mutated_selector["owner_bindings"].append(
            {
                "primary_skill": "frontend-change-builder",
                "review_skill": "security-privacy-gate",
            }
        )
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            ORACLE.oracle_admission_authority(
                foundation_registry=mutated_registry,
            )

    def test_repository_path_permission_priority_and_security_anti_trigger(self) -> None:
        repository_cases = {
            "same-principal-add-dir-paraphrase-a": (
                "Implement the accepted repository CLI so --add-dir registers a "
                "user-owned non-sensitive skills directory for the current OS "
                "account; no lower-trust writer or privilege elevation exists and "
                "authority remains unchanged.",
                "register",
                "changed",
                True,
            ),
            "same-principal-add-dir-paraphrase-b": (
                "Change the internal CLI to add a bounded local plugin directory "
                "owned by this same user; it is non-sensitive, unprivileged, "
                "reversible, and cannot be written by a less-trusted principal.",
                "register",
                "changed",
                True,
            ),
            "atomic-local-replacement-paraphrase": (
                "Implement the accepted maintenance utility to atomically swap its "
                "bounded local settings file for the same user; rollback is "
                "available, no sensitive data or elevated consumer is involved, "
                "and authority stays unchanged.",
                "replace",
                "changed",
                True,
            ),
            "permission-help-copy-only": (
                "Update accepted repository CLI help text describing a permission "
                "flag; no path, filesystem, authority, security, or privacy "
                "behavior changes.",
                "none",
                "unchanged",
                False,
            ),
        }
        snapshots = getattr(
            ORACLE,
            "_routing_boundary_fact_snapshots",
            None,
        )
        self.assertTrue(
            callable(snapshots),
            "clause-local typed routing boundary snapshots are missing",
        )
        for label, (
            prompt,
            expected_mutation,
            expected_filesystem,
            expect_filesystem_lens,
        ) in repository_cases.items():
            with self.subTest(label=label):
                observed = _projected_route(_route(prompt))
                self.assertEqual(
                    "repository-tooling-change-builder",
                    observed["primary_skill"],
                )
                self.assertEqual(
                    expect_filesystem_lens,
                    "filesystem-process-safety" in observed["layer3_skills"],
                )
                self.assertNotEqual("security-privacy-gate", observed["primary_skill"])
                self.assertNotEqual("security-privacy-gate", observed["review_skill"])
                typed = snapshots(
                    " ".join(prompt.casefold().split()),
                    parsed=ORACLE._parse_normalized_task_request(
                        " ".join(prompt.casefold().split())
                    ),
                )
                self.assertEqual(
                    len(typed),
                    len({item.action_id for item in typed}),
                )
                for item in typed:
                    self.assertTrue(dataclasses.is_dataclass(item))
                    self.assertTrue(type(item).__dataclass_params__.frozen)
                    self.assertEqual(
                        (
                            "action_id",
                            "clause_id",
                            "repository_owner",
                            "filesystem_behavior",
                            "path_mutation",
                            "writer_identity",
                            "writer_trust",
                            "sensitive_asset",
                            "privileged_consumption",
                            "authority_delta",
                            "reachable_path",
                            "evidence_ids",
                        ),
                        tuple(
                            field.name
                            for field in dataclasses.fields(item)
                        ),
                    )
                    self.assertIn(
                        item.filesystem_behavior,
                        {"changed", "unchanged", "adjacent", "ambiguous"},
                    )
                    self.assertIn(
                        item.path_mutation,
                        {
                            "create",
                            "register",
                            "replace",
                            "resolve",
                            "contain",
                            "protect",
                            "cleanup",
                            "none",
                            "unknown",
                        },
                    )
                    self.assertEqual(
                        len(item.evidence_ids),
                        len(set(item.evidence_ids)),
                    )
                matching = [
                    item
                    for item in typed
                    if item.repository_owner
                    and item.path_mutation == expected_mutation
                ]
                self.assertEqual(1, len(matching))
                self.assertEqual(
                    expected_filesystem,
                    matching[0].filesystem_behavior,
                )
                if label == "atomic-local-replacement-paraphrase":
                    self.assertEqual(
                        "absent",
                        matching[0].privileged_consumption,
                    )

        generic_non_boundary = _projected_route(
            _route(
                "Analyze repository security and privacy permission terminology; "
                "controls prove no reachable trust, privilege, credential, secret, "
                "or data-recipient boundary changes."
            )
        )
        self.assertEqual(
            "engineering-change-analysis",
            generic_non_boundary["primary_skill"],
        )
        self.assertNotEqual(
            "security-privacy-gate",
            generic_non_boundary["review_skill"],
        )

        cross_clause = _projected_route(
            _route(
                "Implement an accepted repository CLI path registration for the "
                "same user with no sensitive data or privilege elevation. A "
                "separate cache has a less-trusted writer."
            )
        )
        self.assertEqual(
            "repository-tooling-change-builder",
            cross_clause["primary_skill"],
        )
        self.assertNotEqual("security-privacy-gate", cross_clause["review_skill"])

        unknown = _projected_route(
            _route(
                "Analyze a repository CLI path-registration proposal where writer "
                "identity is unknown and no concrete privileged or sensitive "
                "consumption path is identified."
            )
        )
        self.assertEqual("analyzed", unknown["path"])
        self.assertEqual("engineering-change-analysis", unknown["primary_skill"])
        self.assertEqual(["repository-context-map"], unknown["layer3_skills"])

        material = _projected_route(
            _route(
                "Analyze a repository path where a proven less-trusted writer can "
                "replace content that a privileged service consumes, creating a "
                "reachable authorization boundary."
            )
        )
        self.assertEqual("security-privacy-gate", material["primary_skill"])

        hardening_prompt = (
            "Implement an accepted repository CLI change that restricts an existing "
            "reachable permission boundary for a less-trusted writer before "
            "privileged consumption; authority is reduced."
        )
        hardening_main = _test_main_execution(hardening_prompt)
        hardening = _projected_route(
            ORACLE.route_with_trace(
                hardening_prompt,
                main_execution=hardening_main,
            )
        )
        self.assertEqual("L3", hardening_main["execution_level"])
        self.assertEqual(
            "repository-tooling-change-builder",
            hardening["primary_skill"],
        )
        self.assertEqual("security-privacy-gate", hardening["review_skill"])

        positive = (
            "Analyze a proven less-trusted writer reaching a privileged service."
        )
        self.assertEqual(
            "security-privacy-gate",
            _projected_route(_route(positive))["primary_skill"],
        )
        positive_mutations = (
            positive.replace("less-trusted", "same-trust"),
            positive.replace("privileged", "unprivileged"),
            positive.replace("reaching", "denied from reaching"),
        )
        for prompt in positive_mutations:
            with self.subTest(mutation=prompt):
                observed = _projected_route(_route(prompt))
                self.assertNotEqual(
                    "security-privacy-gate",
                    observed["primary_skill"],
                )
                self.assertNotEqual(
                    "security-privacy-gate",
                    observed["review_skill"],
                )

        payment_prompt = (
            "Analyze payment ledger settlement where reconciliation proves "
            "accounting conservation."
        )
        payment_main = _test_main_execution(payment_prompt)
        payment = _projected_route(
            ORACLE.route_with_trace(payment_prompt, main_execution=payment_main)
        )
        self.assertEqual("L3", payment_main["execution_level"])
        self.assertEqual("engineering-change-analysis", payment["primary_skill"])
        self.assertEqual(
            ["payment-trading-extension", "repository-context-map"],
            payment["layer3_skills"],
        )

    def test_router_registry_oracle_and_fixture_identity_are_locked(self) -> None:
        router_rows = []
        for line in ROUTER_PATH.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or line.startswith("|---"):
                continue
            cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
            if len(cells) == 4 and cells[0] != "Task signal":
                router_rows.append(cells)

        security_rows = [
            row
            for row in router_rows
            if row[2] == "security-privacy-gate"
            and "proved reachable" in row[0]
        ]
        payment_rows = [
            row
            for row in router_rows
            if row[0].startswith("payment, ledger, balance")
        ]
        self.assertEqual(1, len(security_rows))
        self.assertEqual(1, len(payment_rows))
        self.assertEqual(
            (
                "analysis-agent",
                "engineering-change-analysis",
                "architecture-impact-reviewer",
            ),
            payment_rows[0][1:],
        )

        security_registry = next(
            row
            for row in _registry()["professional_skills"]
            if row["name"] == "security-privacy-gate"
        )
        proved_trigger = " ".join(security_registry["trigger_signals"])
        self.assertIn("proved", proved_trigger)
        self.assertIn("reachable", proved_trigger)

        document = load_yaml_file(ROOT / "evals" / "routing" / "cases.yaml")
        self.assertEqual(233, len(document["cases"]))
        fixtures = {row["id"]: row for row in document["cases"]}
        for case_id, locked in LOCKED_ROUTING_FIXTURES.items():
            with self.subTest(fixture=case_id):
                actual = fixtures[case_id]
                self.assertEqual(case_id, actual["main_execution"]["task_id"])
                self.assertEqual(locked["prompt"], actual["prompt"])
                self.assertEqual(
                    locked["excluded_skills"],
                    actual["excluded_skills"],
                )
                self.assertEqual(locked["expected"], actual["expected"])
                self.assertEqual(
                    locked["expected"],
                    _projected_route(
                        ORACLE.route_with_trace(
                            actual["prompt"],
                            main_execution=copy.deepcopy(
                                actual["main_execution"]
                            ),
                        )
                    ),
                )

        payment_fixture = fixtures["payment-security"]
        self.assertEqual(
            payment_rows[0][2],
            payment_fixture["expected"]["primary_skill"],
        )
        self.assertEqual(
            payment_rows[0][3],
            payment_fixture["expected"]["review_skill"],
        )
        self.assertEqual(
            payment_fixture["expected"],
            _projected_route(
                ORACLE.route_with_trace(
                    payment_fixture["prompt"],
                    main_execution=copy.deepcopy(
                        payment_fixture["main_execution"]
                    ),
                )
            ),
        )

        router_mutation = list(payment_rows[0])
        router_mutation[2] = "security-privacy-gate"
        self.assertNotEqual(tuple(router_mutation), payment_rows[0])
        registry_mutation = copy.deepcopy(security_registry)
        registry_mutation["trigger_signals"] = [
            trigger.replace("reachable", "possible")
            for trigger in registry_mutation["trigger_signals"]
        ]
        self.assertNotIn(
            "reachable",
            " ".join(registry_mutation["trigger_signals"]),
        )

        positive = (
            "Analyze a proved reachable permission boundary where a less-trusted "
            "writer controls content consumed by a privileged service."
        )
        self.assertEqual(
            "security-privacy-gate",
            _projected_route(_route(positive))["primary_skill"],
        )
        predicate = getattr(ORACLE, "_security_boundary_is_proved", None)
        self.assertTrue(callable(predicate))
        with patch.object(
            ORACLE,
            "_security_boundary_is_proved",
            return_value=False,
        ):
            mutated = _projected_route(_route(positive))
        self.assertNotEqual("security-privacy-gate", mutated["primary_skill"])

    def test_unchanged_adjacent_surface_is_clause_local_for_all_families(self) -> None:
        cases = {
            "backend": (
                "Implement an accepted backend service behavior change",
                "frontend component behavior is unchanged",
            ),
            "frontend": (
                "Implement an accepted frontend component state change",
                "database behavior is unchanged",
            ),
            "installed-client": (
                "Implement an accepted Android installed application lifecycle change",
                "backend service behavior is unchanged",
            ),
            "data-middleware": (
                "Implement an accepted queue middleware consistency change",
                "frontend component behavior is unchanged",
            ),
            "integration": (
                "Implement an accepted external integration contract change",
                "backend service behavior is unchanged",
            ),
            "repository-tooling": (
                "Implement an accepted repository code generator source change",
                "Terraform source behavior is unchanged",
            ),
            "platform-infrastructure": (
                "Implement an accepted Terraform module source change",
                "repository code generator behavior is unchanged",
            ),
            "test-validation": (
                "Implement regression tests proving the changed behavior",
                "structured logging behavior is unchanged",
            ),
            "logging": (
                "Implement a structured redacted logging schema change",
                "external integration contract is unchanged",
            ),
        }
        expected_owners = {
            "backend": "backend-change-builder",
            "frontend": "frontend-change-builder",
            "installed-client": "installed-client-change-builder",
            "data-middleware": "data-middleware-change-builder",
            "integration": "integration-change-builder",
            "repository-tooling": "repository-tooling-change-builder",
            "platform-infrastructure": "platform-infrastructure-change-builder",
            "test-validation": "quality-test-gate",
            "logging": "logging-design-gate",
        }
        expected_anti_routes = {
            "backend": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "backend-change-builder",
                "layer3_skills": [],
                "review_skill": "ai-code-review-refactor",
            },
            "frontend": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "frontend-change-builder",
                "layer3_skills": ["state-management-design"],
                "review_skill": "ai-code-review-refactor",
            },
            "installed-client": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "installed-client-change-builder",
                "layer3_skills": [],
                "review_skill": "ai-code-review-refactor",
            },
            "data-middleware": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "data-middleware-change-builder",
                "layer3_skills": [
                    "transaction-consistency",
                    "idempotency-retry-design",
                ],
                "review_skill": "ai-code-review-refactor",
            },
            "integration": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "integration-change-builder",
                "layer3_skills": ["contract-testing"],
                "review_skill": "ai-code-review-refactor",
            },
            "repository-tooling": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "repository-tooling-change-builder",
                "layer3_skills": [
                    "build-tool-professional-usage",
                    "targeted-validation-selection",
                ],
                "review_skill": "ai-code-review-refactor",
            },
            "platform-infrastructure": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "platform-infrastructure-change-builder",
                "layer3_skills": ["infrastructure-as-code-safety"],
                "review_skill": "ai-code-review-refactor",
            },
            "test-validation": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "quality-test-gate",
                "layer3_skills": ["regression-testing"],
                "review_skill": "ai-code-review-refactor",
            },
            "logging": {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "logging-design-gate",
                "layer3_skills": ["logging-error-handling"],
                "review_skill": "logging-design-gate",
            },
        }
        for family, (changed, unchanged) in cases.items():
            for prompt in (
                f"{changed}; {unchanged}.",
                f"{unchanged}; {changed}.",
            ):
                with self.subTest(family=family, prompt=prompt):
                    observed = ORACLE.classify_professional_families(prompt)
                    self.assertEqual(
                        [family],
                        [item["routing_family"] for item in observed],
                    )
                    route = _projected_route(_route(prompt))
                    self.assertEqual("direct", route["path"])
                    self.assertEqual(
                        expected_owners[family],
                        route["primary_skill"],
                    )
        self.assertEqual(
            [],
            ORACLE.classify_professional_families(
                "Update backend service documentation only; behavior is unchanged."
            ),
        )
        anti_cases: list[tuple[str, str, str]] = []
        for family, (changed, _unchanged) in cases.items():
            platform = "iOS" if family == "installed-client" else "Windows"
            anti_cases.extend(
                [
                    (
                        f"{family}:tail",
                        family,
                        f"{changed} with no {platform} behavior.",
                    ),
                    (
                        f"{family}:inline",
                        family,
                        changed.replace(
                            "Implement ",
                            f"Implement with no {platform} behavior ",
                            1,
                        )
                        + ".",
                    ),
                ]
            )
        frontend_copy_fixture = (
            "Implement a frontend component authorization copy update for an "
            "ordinary payment confirmation; no funds, ledger, settlement, or "
            "execution state changes."
        )
        anti_cases.extend(
            [
                (
                    "frontend-copy:tail",
                    "frontend",
                    frontend_copy_fixture.replace(
                        "; no funds",
                        " with no Windows behavior; no funds",
                        1,
                    ),
                ),
                (
                    "frontend-copy:inline",
                    "frontend",
                    frontend_copy_fixture.replace(
                        "Implement ",
                        "Implement with no Windows behavior ",
                        1,
                    ),
                ),
            ]
        )

        mismatches: list[str] = []
        executed: list[str] = []
        for label, family, prompt in anti_cases:
            executed.append(label)
            actual_families = [
                item["routing_family"]
                for item in ORACLE.classify_professional_families(prompt)
            ]
            if actual_families != [family]:
                mismatches.append(
                    f"[{label}] mismatch=professional-family; "
                    f"expected={[family]!r}; actual={actual_families!r}"
                )
            if family != "installed-client":
                actual_domains = ORACLE.domain_route_families(prompt)
                if actual_domains:
                    mismatches.append(
                        f"[{label}] mismatch=unexpected-domain; "
                        f"expected=[]; actual={actual_domains!r}"
                    )
            try:
                observed = _route(prompt)
            except ORACLE.RoutingIntegrityError as exc:
                mismatches.append(
                    f"[{label}] mismatch=route-integrity; "
                    f"error={type(exc).__name__}: {exc}"
                )
                continue
            owner_ids = [
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith("implementation-owner:")
            ]
            expected_owner_ids = [
                f"implementation-owner:{expected_owners[family]}"
            ]
            if owner_ids != expected_owner_ids:
                mismatches.append(
                    f"[{label}] mismatch=raw-owner; "
                    f"expected={expected_owner_ids!r}; "
                    f"actual={owner_ids!r}"
                )
            actual_route = _projected_route(observed)
            expected_route = expected_anti_routes[family]
            route_keys = ("path", "profile", "primary_skill")
            if not label.startswith("frontend-copy:"):
                actual_route = {
                    key: actual_route[key]
                    for key in route_keys
                }
                expected_route = {
                    key: expected_route[key]
                    for key in route_keys
                }
            if actual_route != expected_route:
                mismatches.append(
                    f"[{label}] mismatch=route-envelope; "
                    f"expected={expected_route!r}; "
                    f"actual={actual_route!r}"
                )
            trace = observed["winner_trace"]
            if (
                observed["route_decision"].get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{label}] mismatch=route-proof; "
                    f"route_once="
                    f"{observed['route_decision'].get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )
        expected_labels = [
            f"{family}:{placement}"
            for family in cases
            for placement in ("tail", "inline")
        ] + ["frontend-copy:tail", "frontend-copy:inline"]
        if executed != expected_labels:
            mismatches.append(
                "[professional-effect-anti] mismatch=case-execution; "
                f"expected={expected_labels!r}; actual={executed!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_filesystem_fallback_preserves_backend_family_evidence(
        self,
    ) -> None:
        prompts = (
            "Implement a backend service child process contract change and no "
            "local filesystem mutation or path authority change.",
            "Implement path-containment behavior change while child-process "
            "behavior remains unchanged.",
            "Implement filesystem durability behavior change without "
            "child-process work.",
            "Implement subprocess timeout behavior change without local file "
            "changes.",
        )
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                observed = _route(prompt)
                route = _projected_route(observed)
                self.assertEqual("direct", route["path"])
                self.assertEqual(
                    "backend-change-builder",
                    route["primary_skill"],
                )
                self.assertIn(
                    "filesystem-process-safety",
                    route["layer3_skills"],
                )
                self.assertIn(
                    "backend-surface",
                    observed["winner_trace"]["selected_candidate"][
                        "evidence"
                    ],
                )

    def test_external_contradiction_fails_closed(self) -> None:
        prompt = (
            "Analyze an external integration downstream consumer "
            "compatibility change; downstream consumer compatibility "
            "remains unchanged."
        )
        observed = _route(prompt)
        selected = observed["winner_trace"]["selected_candidate"]
        self.assertEqual("critical-unknown", selected["candidate_id"])
        self.assertIn(
            "critical-source:external-integration-consumer-"
            "effect-contradiction",
            selected["evidence"],
        )

    def test_external_action_relation_and_polarity_are_parser_owned(
        self,
    ) -> None:
        cases = (
            (
                "Implement an external integration downstream consumer "
                "compatibility change.",
                "changed",
            ),
            (
                "Do not implement an external integration downstream "
                "consumer compatibility change.",
                "unchanged",
            ),
        )
        for prompt, polarity in cases:
            with self.subTest(prompt=prompt):
                bindings = (
                    ORACLE._build_external_effect_scope_bindings(prompt)
                )
                self.assertEqual(1, len(bindings))
                binding = bindings[0]
                self.assertEqual("direct", binding.action_relation)
                self.assertEqual(polarity, binding.action_polarity)
                self.assertEqual(
                    "explicit-external",
                    binding.continuation_owner,
                )

    def test_independent_action_does_not_inherit_external_session(
        self,
    ) -> None:
        prompt = (
            "external integration contract is unchanged; "
            "Implement a database schema change."
        )
        bindings = ORACLE._build_external_effect_scope_bindings(prompt)
        records = ORACLE._build_external_concern_effect_records(prompt)
        self.assertFalse(
            any(
                binding.continuation_owner == "inherited-external"
                for binding in bindings
            )
        )
        self.assertFalse(
            any(record.clause_id > 0 for record in records)
        )
        route = _projected_route(_route(prompt))
        self.assertEqual("direct", route["path"])
        self.assertEqual(
            "data-middleware-change-builder",
            route["primary_skill"],
        )

    def test_tail_adjacent_negative_preserves_changed_owner_surface(self) -> None:
        fixture_paths = {
            "routing": ROOT / "evals" / "routing" / "cases.yaml",
            "admission": (
                ROOT
                / "evals"
                / "capability-coverage"
                / "admission-cases.yaml"
            ),
        }
        fixture_rows = {}
        for source, path in fixture_paths.items():
            document = load_yaml_file(path)
            self.assertIsInstance(document, dict)
            fixture_rows[source] = {
                row["id"]: row for row in document["cases"]
            }

        cases = [
            {
                "id": "reliability-anti-logging-field",
                "source": "routing",
                "family": "logging",
                "owner": "logging-design-gate",
                "target": "reliability-observability-gate",
                "tail": " with no reliability decision.",
                "replacements": (),
            },
            {
                "id": (
                    "capcov-admission-domain-cloud-platform-language-negative"
                ),
                "source": "admission",
                "family": "backend",
                "owner": "backend-change-builder",
                "target": "cloud-platform-extension",
                "tail": " with no cloud control-plane decision.",
                "replacements": (),
            },
            {
                "id": (
                    "capcov-admission-foundation-client-lifecycle-"
                    "simple-negative"
                ),
                "source": "admission",
                "family": "installed-client",
                "owner": "installed-client-change-builder",
                "target": "client-lifecycle-state-restoration",
                "tail": " with no lifecycle state change.",
                "replacements": (
                    ("screen copy", "screen behavior"),
                    ("lifecycle or state", "lifecycle state"),
                ),
            },
            {
                "id": (
                    "capcov-admission-foundation-offline-sync-"
                    "simple-negative"
                ),
                "source": "admission",
                "family": "installed-client",
                "owner": "installed-client-change-builder",
                "target": "offline-sync-conflict-resolution",
                "tail": " with no offline state or synchronization.",
                "replacements": (
                    ("online-only client copy", "installed client behavior"),
                ),
            },
            {
                "id": (
                    "capcov-admission-foundation-client-testing-"
                    "domain-owned-negative"
                ),
                "source": "admission",
                "family": "installed-client",
                "owner": "installed-client-change-builder",
                "target": "client-application-testing",
                "tail": " with no test decision.",
                "replacements": (),
            },
            {
                "id": (
                    "capcov-admission-foundation-swift-domain-owned-negative"
                ),
                "source": "admission",
                "family": "installed-client",
                "owner": "installed-client-change-builder",
                "target": "swift-professional-usage",
                "tail": " with no Swift code decision.",
                "replacements": (),
            },
        ]
        whole_scope_controls = [
            "Do not change structured redacted logging behavior.",
            "Android installed application lifecycle remains unchanged.",
        ]

        mismatches: list[str] = []
        executed: list[str] = []
        counterfactuals: list[str] = []

        def observe(prompt: str, row: dict[str, object]) -> dict[str, object]:
            return ORACLE.route_with_trace(
                prompt,
                main_execution=copy.deepcopy(row["main_execution"]),
            )

        for case in cases:
            case_id = case["id"]
            executed.append(case_id)
            rows = fixture_rows[case["source"]]
            self.assertIn(case_id, rows)
            row = rows[case_id]
            prompt = row["prompt"]
            for old, new in case["replacements"]:
                self.assertEqual(
                    1,
                    prompt.count(old),
                    msg=f"[{case_id}] fixture replacement anchor={old!r}",
                )
                prompt = prompt.replace(old, new, 1)
            tail = case["tail"]
            self.assertTrue(
                prompt.endswith(tail),
                msg=f"[{case_id}] prompt does not end with {tail!r}",
            )
            counterfactual_prompt = prompt[: -len(tail)] + "."
            counterfactuals.append(case_id)

            counterfactual_families = [
                item["routing_family"]
                for item in ORACLE.classify_professional_families(
                    counterfactual_prompt
                )
            ]
            if counterfactual_families != [case["family"]]:
                mismatches.append(
                    f"[{case_id}:counterfactual] "
                    "mismatch=professional-family; "
                    f"expected={[case['family']]!r}; "
                    f"actual={counterfactual_families!r}"
                )
            counterfactual = observe(counterfactual_prompt, row)
            counterfactual_owner_ids = [
                item["candidate_id"]
                for item in counterfactual["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith("implementation-owner:")
            ]
            expected_owner_ids = [
                f"implementation-owner:{case['owner']}"
            ]
            if counterfactual_owner_ids != expected_owner_ids:
                mismatches.append(
                    f"[{case_id}:counterfactual] mismatch=raw-owner; "
                    f"expected={expected_owner_ids!r}; "
                    f"actual={counterfactual_owner_ids!r}"
                )
            counterfactual_selected = counterfactual["winner_trace"][
                "selected_candidate"
            ]["candidate_id"]
            if counterfactual_selected != expected_owner_ids[0]:
                mismatches.append(
                    f"[{case_id}:counterfactual] mismatch=selected-owner; "
                    f"expected={expected_owner_ids[0]!r}; "
                    f"actual={counterfactual_selected!r}"
                )
            counterfactual_route = _projected_route(counterfactual)
            counterfactual_core = {
                key: counterfactual_route[key]
                for key in ("path", "profile", "primary_skill")
            }
            expected_core = {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": case["owner"],
            }
            if counterfactual_core != expected_core:
                mismatches.append(
                    f"[{case_id}:counterfactual] mismatch=route-envelope; "
                    f"expected={expected_core!r}; "
                    f"actual={counterfactual_core!r}"
                )
            counterfactual_trace = counterfactual["winner_trace"]
            if (
                counterfactual["route_decision"].get("route_once") is not True
                or counterfactual_trace.get("route_once") != "proven"
                or counterfactual_trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{case_id}:counterfactual] mismatch=route-proof; "
                    "route_once="
                    f"{counterfactual['route_decision'].get('route_once')!r}; "
                    "trace_route_once="
                    f"{counterfactual_trace.get('route_once')!r}; "
                    "coverage="
                    f"{counterfactual_trace.get('candidate_coverage')!r}"
                )

            actual_families = [
                item["routing_family"]
                for item in ORACLE.classify_professional_families(prompt)
            ]
            if actual_families != [case["family"]]:
                mismatches.append(
                    f"[{case_id}] mismatch=professional-family; "
                    f"expected={[case['family']]!r}; "
                    f"actual={actual_families!r}"
                )
            actual_domains = ORACLE.domain_route_families(prompt)
            if actual_domains:
                mismatches.append(
                    f"[{case_id}] mismatch=unexpected-domain; "
                    f"expected=[]; actual={actual_domains!r}"
                )
            observed = observe(prompt, row)
            owner_ids = [
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith("implementation-owner:")
            ]
            if owner_ids != expected_owner_ids:
                mismatches.append(
                    f"[{case_id}] mismatch=raw-owner; "
                    f"expected={expected_owner_ids!r}; "
                    f"actual={owner_ids!r}"
                )
            selected = observed["winner_trace"]["selected_candidate"][
                "candidate_id"
            ]
            if selected != expected_owner_ids[0]:
                mismatches.append(
                    f"[{case_id}] mismatch=selected-owner; "
                    f"expected={expected_owner_ids[0]!r}; "
                    f"actual={selected!r}; "
                    "forbidden='repository-first-default'"
                )
            actual_route = _projected_route(observed)
            selected_skills = {
                actual_route["primary_skill"],
                actual_route["review_skill"],
                *actual_route["layer3_skills"],
            }
            if case["source"] == "routing":
                expected_route = row["expected"]
            else:
                actual_route = {
                    key: actual_route[key]
                    for key in ("path", "profile", "primary_skill")
                }
                expected_route = expected_core
            if actual_route != expected_route:
                mismatches.append(
                    f"[{case_id}] mismatch=route-envelope; "
                    f"expected={expected_route!r}; "
                    f"actual={actual_route!r}"
                )
            if case["target"] in selected_skills:
                mismatches.append(
                    f"[{case_id}] mismatch=forbidden-target-selected; "
                    f"target={case['target']!r}; "
                    f"actual={sorted(selected_skills)!r}"
                )
            trace = observed["winner_trace"]
            if (
                observed["route_decision"].get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{case_id}] mismatch=route-proof; "
                    f"route_once="
                    f"{observed['route_decision'].get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )

        for prompt in whole_scope_controls:
            control_id = f"whole-scope:{prompt}"
            if ORACLE.classify_professional_families(prompt):
                mismatches.append(
                    f"[{control_id}] mismatch=professional-family; "
                    "expected=[]"
                )
            if ORACLE.domain_route_families(prompt):
                mismatches.append(
                    f"[{control_id}] mismatch=unexpected-domain; expected=[]"
                )
            observed = _route(prompt)
            owner_ids = [
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith("implementation-owner:")
            ]
            if owner_ids:
                mismatches.append(
                    f"[{control_id}] mismatch=raw-owner; "
                    f"expected=[]; actual={owner_ids!r}"
                )
            selected = observed["winner_trace"]["selected_candidate"][
                "candidate_id"
            ]
            if selected != "repository-first-default":
                mismatches.append(
                    f"[{control_id}] mismatch=selected-owner; "
                    "expected='repository-first-default'; "
                    f"actual={selected!r}"
                )
            trace = observed["winner_trace"]
            if (
                observed["route_decision"].get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{control_id}] mismatch=route-proof; "
                    f"route_once="
                    f"{observed['route_decision'].get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )

        expected_case_ids = [case["id"] for case in cases]
        if executed != expected_case_ids:
            mismatches.append(
                "[tail-adjacent-negative] mismatch=case-execution; "
                f"expected={expected_case_ids!r}; actual={executed!r}"
            )
        if counterfactuals != expected_case_ids:
            mismatches.append(
                "[tail-adjacent-negative] mismatch=counterfactual-execution; "
                f"expected={expected_case_ids!r}; "
                f"actual={counterfactuals!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_tail_projection_requires_explicit_action_subject(self) -> None:
        direct_route = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "backend-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        }
        fallback_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        cases = {
            "one-word-subject:tail": {
                "prompt": "Implement backend with no Windows behavior.",
                "families": ["backend"],
                "owners": ["implementation-owner:backend-change-builder"],
                "selected": "implementation-owner:backend-change-builder",
                "route": direct_route,
            },
            "one-word-subject:inline": {
                "prompt": "Implement with no Windows behavior backend.",
                "families": ["backend"],
                "owners": ["implementation-owner:backend-change-builder"],
                "selected": "implementation-owner:backend-change-builder",
                "route": direct_route,
            },
            "accepted-plan:tail": {
                "prompt": (
                    "Plan an accepted backend change with no Windows behavior."
                ),
                "families": ["backend"],
                "owners": ["implementation-owner:backend-change-builder"],
                "selected": "implementation-owner:backend-change-builder",
                "route": direct_route,
            },
            "bare-action:inline": {
                "prompt": "Implement with no Windows behavior.",
                "families": [],
                "owners": [],
                "selected": "repository-first-default",
                "route": fallback_route,
            },
            "whole-scope:unchanged": {
                "prompt": "Do not change backend behavior.",
                "families": [],
                "owners": [],
                "selected": "repository-first-default",
                "route": fallback_route,
            },
        }

        mismatches: list[str] = []
        executed: list[str] = []
        for label, case in cases.items():
            executed.append(label)
            prompt = case["prompt"]
            observed = _route(prompt)
            trace = observed["winner_trace"]
            actual = {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(prompt)
                ],
                "domains": ORACLE.domain_route_families(prompt),
                "owners": [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ],
                "selected": trace["selected_candidate"]["candidate_id"],
                "route": _projected_route(observed),
                "proof": {
                    "decision_route_once": observed["route_decision"].get(
                        "route_once"
                    ),
                    "trace_route_once": trace.get("route_once"),
                    "candidate_coverage": trace.get("candidate_coverage"),
                },
            }
            expected = {
                "families": case["families"],
                "domains": [],
                "owners": case["owners"],
                "selected": case["selected"],
                "route": case["route"],
                "proof": {
                    "decision_route_once": True,
                    "trace_route_once": "proven",
                    "candidate_coverage": "full",
                },
            }
            if actual != expected:
                mismatches.append(
                    f"[{label}] mismatch=subject-guard-contract; "
                    f"expected={expected!r}; actual={actual!r}"
                )

        expected_labels = list(cases)
        if executed != expected_labels:
            mismatches.append(
                "[tail-projection-subject-guard] mismatch=case-execution; "
                f"expected={expected_labels!r}; actual={executed!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_declared_signal_pairs_normalize_scope_and_signal_with_boundaries(
        self,
    ) -> None:
        document = load_yaml_file(
            ROOT
            / "evals"
            / "capability-coverage"
            / "admission-cases.yaml"
        )
        self.assertIsInstance(document, dict)
        source_rows = [
            row
            for row in document["cases"]
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        ]
        source_ids = [row["id"] for row in source_rows]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        rows = {row["id"]: row for row in source_rows}

        offline_adjacent_id = (
            "capcov-admission-foundation-offline-sync-adjacent-negative"
        )
        online_simple_id = (
            "capcov-admission-foundation-offline-sync-simple-negative"
        )
        swift_linux_id = (
            "capcov-admission-domain-macos-language-negative"
        )
        android_installed_id = (
            "capcov-admission-prof-installed-client-positive"
        )
        dotnet_service_id = (
            "capcov-admission-foundation-csharp-dotnet-decision"
        )
        dotnet_maui_id = (
            "capcov-admission-domain-windows-release-framework-mismatch"
        )
        fixture_expectations = {
            offline_adjacent_id: {
                "selected": False,
                "primary_skill": "installed-client-change-builder",
            },
            online_simple_id: {
                "selected": False,
                "primary_skill": "installed-client-change-builder",
            },
            swift_linux_id: {
                "selected": False,
                "primary_skill": "backend-change-builder",
            },
            android_installed_id: {
                "selected": True,
                "primary_skill": "installed-client-change-builder",
            },
            dotnet_service_id: {
                "selected": True,
                "primary_skill": "backend-change-builder",
            },
            dotnet_maui_id: {
                "selected": True,
                "primary_skill": "installed-client-change-builder",
            },
        }
        for case_id, expected in fixture_expectations.items():
            self.assertIn(case_id, rows)
            self.assertEqual(expected, rows[case_id]["expected"])

        backend_route = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "backend-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        }
        installed_route = {
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "installed-client-change-builder",
            "layer3_skills": [],
            "review_skill": "ai-code-review-refactor",
        }
        fallback_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }

        def direct_contract(
            family: str,
            owner: str,
            *,
            layer3_skills: list[str],
            domains: list[tuple[str, str]],
        ) -> dict[str, object]:
            return {
                "families": [family],
                "domains": domains,
                "owners": [f"implementation-owner:{owner}"],
                "selected": f"implementation-owner:{owner}",
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": owner,
                    "layer3_skills": layer3_skills,
                    "review_skill": "ai-code-review-refactor",
                },
                "proof": {
                    "decision_route_once": True,
                    "trace_route_once": "proven",
                    "candidate_coverage": "full",
                },
            }

        def observe(
            prompt: str,
            *,
            main_execution: dict[str, object] | None = None,
        ) -> dict[str, object]:
            observed = ORACLE.route_with_trace(
                prompt,
                main_execution=copy.deepcopy(
                    main_execution
                    if main_execution is not None
                    else _test_main_execution(prompt)
                ),
            )
            trace = observed["winner_trace"]
            return {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(prompt)
                ],
                "domains": ORACLE.domain_route_families(prompt),
                "owners": [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ],
                "selected": trace["selected_candidate"]["candidate_id"],
                "route": _projected_route(observed),
                "proof": {
                    "decision_route_once": observed["route_decision"].get(
                        "route_once"
                    ),
                    "trace_route_once": trace.get("route_once"),
                    "candidate_coverage": trace.get("candidate_coverage"),
                },
            }

        process_prompt = rows[offline_adjacent_id]["prompt"]
        self.assertEqual(1, process_prompt.count("process-death"))
        process_space_prompt = process_prompt.replace(
            "process-death",
            "process death",
            1,
        )
        online_prompt = rows[online_simple_id]["prompt"]
        self.assertEqual(1, online_prompt.count("online-only"))
        online_space_prompt = online_prompt.replace(
            "online-only",
            "online only",
            1,
        )
        android_prompt = rows[android_installed_id]["prompt"]
        self.assertEqual(
            1,
            android_prompt.count("installed-client screen"),
        )
        back_stack_prompt = android_prompt.replace(
            "installed-client screen",
            "back-stack",
            1,
        )
        back_stack_space_prompt = back_stack_prompt.replace(
            "back-stack",
            "back stack",
            1,
        )

        pair_cases = {
            "server-side": {
                "signal_pair": ("server-side", "server side"),
                "prompts": (
                    "Implement accepted server-side behavior.",
                    "Implement accepted server side behavior.",
                ),
                "main_execution": None,
                "expected": direct_contract(
                    "backend",
                    "backend-change-builder",
                    layer3_skills=[],
                    domains=[],
                ),
            },
            "command-line": {
                "signal_pair": ("command-line", "command line"),
                "prompts": (
                    "Implement accepted command-line service behavior.",
                    "Implement accepted command line service behavior.",
                ),
                "main_execution": None,
                "expected": direct_contract(
                    "backend",
                    "backend-change-builder",
                    layer3_skills=[],
                    domains=[],
                ),
            },
            "installed-client": {
                "signal_pair": ("installed-client", "installed client"),
                "prompts": (
                    "Implement accepted installed-client screen behavior.",
                    "Implement accepted installed client screen behavior.",
                ),
                "main_execution": None,
                "expected": direct_contract(
                    "installed-client",
                    "installed-client-change-builder",
                    layer3_skills=[],
                    domains=[],
                ),
            },
            "process-death": {
                "signal_pair": ("process-death", "process death"),
                "prompts": (process_prompt, process_space_prompt),
                "main_execution": rows[offline_adjacent_id][
                    "main_execution"
                ],
                "expected": direct_contract(
                    "installed-client",
                    "installed-client-change-builder",
                    layer3_skills=[
                        "client-lifecycle-state-restoration",
                    ],
                    domains=[],
                ),
            },
            "online-only": {
                "signal_pair": ("online-only", "online only"),
                "prompts": (online_prompt, online_space_prompt),
                "main_execution": rows[online_simple_id]["main_execution"],
                "expected": direct_contract(
                    "installed-client",
                    "installed-client-change-builder",
                    layer3_skills=[],
                    domains=[],
                ),
            },
            "back-stack": {
                "signal_pair": ("back-stack", "back stack"),
                "prompts": (
                    back_stack_prompt,
                    back_stack_space_prompt,
                ),
                "main_execution": rows[android_installed_id][
                    "main_execution"
                ],
                "expected": direct_contract(
                    "installed-client",
                    "installed-client-change-builder",
                    layer3_skills=[],
                    domains=[],
                ),
            },
        }

        mismatches: list[str] = []
        executed_pairs: list[str] = []
        for label, case in pair_cases.items():
            hyphen_signal, spaced_signal = case["signal_pair"]
            hyphen_prompt, spaced_prompt = case["prompts"]
            self.assertEqual(1, hyphen_prompt.count(hyphen_signal))
            self.assertEqual(
                spaced_prompt,
                hyphen_prompt.replace(
                    hyphen_signal,
                    spaced_signal,
                    1,
                ),
            )
            for variant, prompt in (
                ("hyphen", hyphen_prompt),
                ("space", spaced_prompt),
            ):
                executed_pairs.append(f"{label}:{variant}")
                actual = observe(
                    prompt,
                    main_execution=case["main_execution"],
                )
                if actual != case["expected"]:
                    mismatches.append(
                        f"[pair:{label}:{variant}] "
                        "mismatch=public-route-contract; "
                        f"expected={case['expected']!r}; "
                        f"actual={actual!r}"
                    )

        expected_pairs = [
            f"{label}:{variant}"
            for label in pair_cases
            for variant in ("hyphen", "space")
        ]
        if executed_pairs != expected_pairs:
            mismatches.append(
                "[pair-inventory] mismatch=execution; "
                f"expected={expected_pairs!r}; "
                f"actual={executed_pairs!r}"
            )

        source_controls = {
            swift_linux_id: direct_contract(
                "backend",
                "backend-change-builder",
                layer3_skills=[],
                domains=[],
            ),
            android_installed_id: direct_contract(
                "installed-client",
                "installed-client-change-builder",
                layer3_skills=["android-platform-extension"],
                domains=[
                    (
                        "android-platform-extension",
                        "platform-lifecycle-authority",
                    ),
                ],
            ),
            dotnet_service_id: direct_contract(
                "backend",
                "backend-change-builder",
                layer3_skills=["csharp-dotnet-professional-usage"],
                domains=[],
            ),
            dotnet_maui_id: direct_contract(
                "installed-client",
                "installed-client-change-builder",
                layer3_skills=[
                    "cross-platform-client-extension",
                    "windows-platform-extension",
                ],
                domains=[],
            ),
        }
        for case_id, expected in source_controls.items():
            actual = observe(
                rows[case_id]["prompt"],
                main_execution=rows[case_id]["main_execution"],
            )
            if actual != expected:
                mismatches.append(
                    f"[source:{case_id}] mismatch=retained-control; "
                    f"expected={expected!r}; actual={actual!r}"
                )

        boundary_negatives = {
            "subnet-service": "Implement a subnet service policy.",
            "planet-maui": "Implement a planet Maui client screen.",
        }
        boundary_expected = {
            "families": [],
            "domains": [],
            "owners": [],
            "selected": "repository-first-default",
            "route": fallback_route,
            "proof": {
                "decision_route_once": True,
                "trace_route_once": "proven",
                "candidate_coverage": "full",
            },
        }
        for label, prompt in boundary_negatives.items():
            actual = observe(prompt)
            if actual != boundary_expected:
                mismatches.append(
                    f"[boundary:{label}] mismatch=substring-guard; "
                    f"expected={boundary_expected!r}; actual={actual!r}"
                )

        self.assertEqual(
            backend_route,
            pair_cases["server-side"]["expected"]["route"],
        )
        self.assertEqual(
            installed_route,
            pair_cases["installed-client"]["expected"]["route"],
        )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_dotnet_normalized_effect_signals_preserve_owner_and_layers(
        self,
    ) -> None:
        document = load_yaml_file(
            ROOT
            / "evals"
            / "capability-coverage"
            / "admission-cases.yaml"
        )
        self.assertIsInstance(document, dict)
        rows = {
            row["id"]: row
            for row in document["cases"]
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        cases = {
            "capcov-admission-domain-windows-release-framework-mismatch": {
                "fixture": {
                    "layer": "domain",
                    "skill": "windows-platform-extension",
                    "selected": True,
                    "owner": "installed-client-change-builder",
                },
                "family": "installed-client",
                "domains": [],
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "installed-client-change-builder",
                    "layer3_skills": [
                        "cross-platform-client-extension",
                        "windows-platform-extension",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
                "forbidden": {
                    "delivery-release-gate",
                    "android-platform-extension",
                    "ios-ipados-platform-extension",
                    "linux-desktop-platform-extension",
                    "macos-platform-extension",
                },
                "replacement": (
                    ".NET MAUI client whose release target is Windows",
                    (
                        "Windows packaged desktop application "
                        "protocol-handler change"
                    ),
                ),
                "owner_only_neighbor": {
                    "proof_scope": "owner-only",
                    "semantic_equivalence": False,
                    "family": "installed-client",
                    "domains": [
                        (
                            "windows-platform-extension",
                            "application-identity-authority",
                        )
                    ],
                    "route": {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "installed-client-change-builder",
                        "layer3_skills": ["windows-platform-extension"],
                        "review_skill": "ai-code-review-refactor",
                    },
                },
            },
            "capcov-admission-foundation-csharp-dotnet-decision": {
                "fixture": {
                    "layer": "foundation",
                    "skill": "csharp-dotnet-professional-usage",
                    "selected": True,
                    "owner": "backend-change-builder",
                },
                "family": "backend",
                "domains": [],
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                    "layer3_skills": [
                        "csharp-dotnet-professional-usage",
                    ],
                    "review_skill": "ai-code-review-refactor",
                },
                "forbidden": {
                    "installed-client-change-builder",
                    "cross-platform-client-extension",
                    "windows-platform-extension",
                },
                "replacement": (
                    ".NET service",
                    (
                        "Windows service whose service lifecycle changes "
                        "shutdown behavior"
                    ),
                ),
                "owner_only_neighbor": {
                    "proof_scope": "owner-only",
                    "semantic_equivalence": False,
                    "family": "backend",
                    "domains": [
                        (
                            "windows-platform-extension",
                            "service-lifecycle-authority",
                        )
                    ],
                    "route": {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "backend-change-builder",
                        "layer3_skills": [
                            "windows-platform-extension",
                            "csharp-dotnet-professional-usage",
                        ],
                        "review_skill": "ai-code-review-refactor",
                    },
                },
            },
        }

        mismatches: list[str] = []
        executed: list[str] = []
        owner_only_neighbors: list[str] = []
        for case_id, case in cases.items():
            executed.append(case_id)
            self.assertIn(case_id, rows)
            row = rows[case_id]
            fixture = case["fixture"]
            self.assertEqual(fixture["layer"], row["layer"])
            self.assertEqual(fixture["skill"], row["skill"])
            self.assertEqual(
                {
                    "selected": fixture["selected"],
                    "primary_skill": fixture["owner"],
                },
                row["expected"],
            )
            prompt = row["prompt"]
            old, new = case["replacement"]
            self.assertEqual(
                1,
                prompt.count(old),
                msg=f"[{case_id}] .NET replacement anchor={old!r}",
            )

            observed = ORACLE.route_with_trace(
                prompt,
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            trace = observed["winner_trace"]
            actual_route = _projected_route(observed)
            actual_skills = {
                actual_route["primary_skill"],
                actual_route["review_skill"],
                *actual_route["layer3_skills"],
            }
            actual = {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(prompt)
                ],
                "domains": ORACLE.domain_route_families(prompt),
                "owners": [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ],
                "selected": trace["selected_candidate"]["candidate_id"],
                "route": actual_route,
                "forbidden_selected": sorted(
                    actual_skills & case["forbidden"]
                ),
                "proof": {
                    "decision_route_once": observed["route_decision"].get(
                        "route_once"
                    ),
                    "trace_route_once": trace.get("route_once"),
                    "candidate_coverage": trace.get("candidate_coverage"),
                },
            }
            expected = {
                "families": [case["family"]],
                "domains": case["domains"],
                "owners": [
                    f"implementation-owner:{fixture['owner']}"
                ],
                "selected": f"implementation-owner:{fixture['owner']}",
                "route": case["route"],
                "forbidden_selected": [],
                "proof": {
                    "decision_route_once": True,
                    "trace_route_once": "proven",
                    "candidate_coverage": "full",
                },
            }
            if actual != expected:
                mismatches.append(
                    f"[{case_id}] mismatch=dotnet-root-contract; "
                    f"expected={expected!r}; actual={actual!r}"
                )

            owner_only_neighbor_prompt = prompt.replace(old, new, 1)
            self.assertNotIn(
                ".NET",
                owner_only_neighbor_prompt,
                msg=(
                    f"[{case_id}] owner-only neighbor retains .NET spelling"
                ),
            )
            owner_only_neighbors.append(case_id)
            owner_only_neighbor = ORACLE.route_with_trace(
                owner_only_neighbor_prompt,
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            owner_only_neighbor_trace = owner_only_neighbor["winner_trace"]
            owner_only_neighbor_route = _projected_route(
                owner_only_neighbor
            )
            owner_only_neighbor_expected = case["owner_only_neighbor"]
            if owner_only_neighbor_expected["proof_scope"] != "owner-only":
                mismatches.append(
                    f"[{case_id}:owner_only_neighbor] "
                    "mismatch=proof-scope; expected='owner-only'; "
                    f"actual={owner_only_neighbor_expected['proof_scope']!r}"
                )
            if (
                owner_only_neighbor_expected["semantic_equivalence"]
                is not False
            ):
                mismatches.append(
                    f"[{case_id}:owner_only_neighbor] "
                    "mismatch=semantic-equivalence-declaration; "
                    "expected=False; actual="
                    f"{owner_only_neighbor_expected['semantic_equivalence']!r}"
                )
            owner_only_neighbor_actual = {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(
                        owner_only_neighbor_prompt
                    )
                ],
                "domains": ORACLE.domain_route_families(
                    owner_only_neighbor_prompt
                ),
                "owners": [
                    item["candidate_id"]
                    for item in owner_only_neighbor_trace["raw_candidates"]
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ],
                "selected": owner_only_neighbor_trace[
                    "selected_candidate"
                ]["candidate_id"],
                "route": owner_only_neighbor_route,
                "proof": {
                    "decision_route_once": owner_only_neighbor[
                        "route_decision"
                    ].get("route_once"),
                    "trace_route_once": owner_only_neighbor_trace.get(
                        "route_once"
                    ),
                    "candidate_coverage": owner_only_neighbor_trace.get(
                        "candidate_coverage"
                    ),
                },
            }
            owner_only_neighbor_owner = owner_only_neighbor_expected["route"][
                "primary_skill"
            ]
            owner_only_neighbor_contract = {
                "families": [owner_only_neighbor_expected["family"]],
                "domains": owner_only_neighbor_expected["domains"],
                "owners": [
                    f"implementation-owner:{owner_only_neighbor_owner}"
                ],
                "selected": (
                    f"implementation-owner:{owner_only_neighbor_owner}"
                ),
                "route": owner_only_neighbor_expected["route"],
                "proof": {
                    "decision_route_once": True,
                    "trace_route_once": "proven",
                    "candidate_coverage": "full",
                },
            }
            if (
                owner_only_neighbor_route["primary_skill"]
                != fixture["owner"]
            ):
                mismatches.append(
                    f"[{case_id}:owner_only_neighbor] "
                    "mismatch=owner-only-scope; "
                    f"expected={fixture['owner']!r}; "
                    f"actual="
                    f"{owner_only_neighbor_route['primary_skill']!r}"
                )
            if (
                owner_only_neighbor_actual["domains"]
                == case["domains"]
            ):
                mismatches.append(
                    f"[{case_id}:owner_only_neighbor] "
                    "mismatch=semantic-equivalence-domain; "
                    "expected neighbor Domain to differ from root; "
                    f"root={case['domains']!r}; "
                    "neighbor="
                    f"{owner_only_neighbor_actual['domains']!r}"
                )
            if (
                owner_only_neighbor_route["layer3_skills"]
                == case["route"]["layer3_skills"]
            ):
                mismatches.append(
                    f"[{case_id}:owner_only_neighbor] "
                    "mismatch=semantic-equivalence-layer3; "
                    "expected neighbor Layer3 to differ from root; "
                    f"root={case['route']['layer3_skills']!r}; "
                    "neighbor="
                    f"{owner_only_neighbor_route['layer3_skills']!r}"
                )
            if (
                owner_only_neighbor_actual
                != owner_only_neighbor_contract
            ):
                mismatches.append(
                    f"[{case_id}:owner_only_neighbor] "
                    "mismatch=neighbor-route-contract; "
                    f"expected={owner_only_neighbor_contract!r}; "
                    f"actual={owner_only_neighbor_actual!r}"
                )

        fallback_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        boundary_negative_cases = {
            "substring-negative:subnet-service-policy": (
                "Implement a subnet service policy."
            ),
            "substring-negative:planet-maui-client-screen": (
                "Implement a planet Maui client screen."
            ),
        }
        forbidden_dotnet_layers = {
            "csharp-dotnet-professional-usage",
            "cross-platform-client-extension",
            "windows-platform-extension",
        }
        executed_boundary_negatives: list[str] = []
        for label, prompt in boundary_negative_cases.items():
            executed_boundary_negatives.append(label)
            observed = _route(prompt)
            trace = observed["winner_trace"]
            actual_route = _projected_route(observed)
            actual = {
                "families": [
                    item["routing_family"]
                    for item in ORACLE.classify_professional_families(prompt)
                ],
                "domains": ORACLE.domain_route_families(prompt),
                "owners": [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                    if item["candidate_id"].startswith(
                        "implementation-owner:"
                    )
                ],
                "selected": trace["selected_candidate"]["candidate_id"],
                "route": actual_route,
                "forbidden_layer3": sorted(
                    forbidden_dotnet_layers
                    & set(actual_route["layer3_skills"])
                ),
                "proof": {
                    "decision_route_once": observed["route_decision"].get(
                        "route_once"
                    ),
                    "trace_route_once": trace.get("route_once"),
                    "candidate_coverage": trace.get("candidate_coverage"),
                },
            }
            expected = {
                "families": [],
                "domains": [],
                "owners": [],
                "selected": "repository-first-default",
                "route": fallback_route,
                "forbidden_layer3": [],
                "proof": {
                    "decision_route_once": True,
                    "trace_route_once": "proven",
                    "candidate_coverage": "full",
                },
            }
            if actual != expected:
                mismatches.append(
                    f"[{label}] "
                    "mismatch=normalized-signal-boundary; "
                    f"expected={expected!r}; actual={actual!r}"
                )

        expected_case_ids = list(cases)
        if executed != expected_case_ids:
            mismatches.append(
                "[dotnet-normalized-effect-signals] "
                "mismatch=case-execution; "
                f"expected={expected_case_ids!r}; actual={executed!r}"
            )
        if owner_only_neighbors != expected_case_ids:
            mismatches.append(
                "[dotnet-normalized-effect-signals] "
                "mismatch=owner-only-neighbor-execution; "
                f"expected={expected_case_ids!r}; "
                f"actual={owner_only_neighbors!r}"
            )
        expected_boundary_labels = list(boundary_negative_cases)
        if executed_boundary_negatives != expected_boundary_labels:
            mismatches.append(
                "[dotnet-normalized-effect-signals] "
                "mismatch=boundary-negative-execution; "
                f"expected={expected_boundary_labels!r}; "
                f"actual={executed_boundary_negatives!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_classifier_source_contains_no_professional_or_layer3_ids_or_prose(self) -> None:
        classify = getattr(ORACLE, "classify_professional_families", None)
        self.assertTrue(callable(classify))
        source = inspect.getsource(classify)
        registry = _registry()
        forbidden = {
            row["name"] for row in registry["professional_skills"]
        } | {
            layer3
            for row in registry["professional_skills"]
            for layer3 in row["layer3_candidates"]
        } | {
            signal
            for row in registry["professional_skills"]
            for field in ("trigger_signals", "anti_trigger_signals")
            for signal in row[field]
        }
        self.assertEqual(
            [],
            sorted(item for item in forbidden if item and item in source),
        )


class ImplementationOwnerRouteTests(unittest.TestCase):
    def test_android_accessibility_uses_one_specialist_contract(self) -> None:
        expected_routes = {
            "android-compose-semantics": (
                "Implement an accepted Android app Compose semantics behavior "
                "change.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "android-dpad-navigation": (
                "Implement an accepted Android app D-pad navigation behavior "
                "change.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "android-dpad-input": (
                "Implement an accepted Android app D-pad input behavior change.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "android-keyboard-navigation": (
                "Implement an accepted Android app keyboard navigation behavior "
                "change.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "android-interaction-alternative": (
                "Implement an accepted Android app interaction alternative "
                "behavior change.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "android-pointer-alternative": (
                "Implement an accepted Android app pointer alternative behavior "
                "change.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "native-android": (
                "Implement an accepted Android installed application screen "
                "accessibility behavior change for TalkBack and Switch Access.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "flutter-android": (
                "Implement an accepted Flutter application change targeting "
                "Android for TalkBack accessibility behavior and keyboard focus.",
                [
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "react-native-android": (
                "Implement an accepted React Native application change targeting "
                "Android for TalkBack accessibility behavior and Switch Access.",
                [
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
        }
        for label, (prompt, layer3) in expected_routes.items():
            with self.subTest(label=label):
                observed = _route(prompt)
                self.assertEqual(
                    {
                        "path": "direct",
                        "profile": "task-agent",
                        "primary_skill": "installed-client-change-builder",
                        "layer3_skills": layer3,
                        "review_skill": "ai-code-review-refactor",
                    },
                    _projected_route(observed),
                )

        helper = getattr(ORACLE, "_accessibility_behavior_requested", None)
        self.assertTrue(callable(helper))
        self.assertEqual(
            "_accessibility_behavior_requested",
            ORACLE._DYNAMIC_FOUNDATION_SOURCES[
                "accessibility-inclusive-design"
            ],
        )

    def test_android_accessibility_layer3_overflow_preserves_handoff(
        self,
    ) -> None:
        prompt = (
            "Implement an accepted Flutter application change targeting "
            "Android and iOS for accessibility behavior affecting TalkBack "
            "and VoiceOver."
        )
        observed = _route(prompt)
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            _projected_route(observed),
        )
        trace = observed["winner_trace"]
        self.assertEqual(
            "foundation-layer3-overflow",
            trace["selected_candidate"]["candidate_id"],
        )
        self.assertEqual(
            [
                "cross-platform-client-extension",
                "android-platform-extension",
                "ios-ipados-platform-extension",
                "accessibility-inclusive-design",
            ],
            trace["deferred_handoff"]["deferred_layer3"],
        )

    def test_accessibility_negatives_do_not_over_route(self) -> None:
        prompts = {
            "platform-api-name-only": (
                "Inspect Android TalkBack API names only; no Android behavior "
                "changes and no implementation is requested."
            ),
            "talkback-api-constant-rename": (
                "Rename the Android TalkBack API constant used by the app; no "
                "runtime behavior changes."
            ),
            "talkback-symbol-rename": (
                "Rename an Android TalkBack symbol in the application; runtime "
                "behavior remains unchanged."
            ),
            "backend-json-dynamic-type": (
                "Implement an accepted backend application change to JSON-decoder "
                "dynamic type handling."
            ),
            "backend-json-dynamic-type-variant": (
                "Change the backend application JSON decoder's dynamic type "
                "handling."
            ),
            "backend-kotlin": (
                "Implement accepted backend Kotlin code for a field named "
                "accessibility; no user interface behavior changes."
            ),
            "backend-diff-field": (
                "Review the actual diff for a backend field named accessibility; "
                "no user interface behavior changes."
            ),
            "ios-only-lifecycle": (
                "Implement an accepted iOS application lifecycle change with no "
                "Android behavior and no accessibility behavior."
            ),
            "documentation-only": (
                "Update Android accessibility API documentation only without "
                "changing application behavior."
            ),
            "unknown-cross-platform-target": (
                "Prepare an implementation for a Flutter accessibility behavior "
                "change whose target platforms are not yet known."
            ),
        }
        helper = getattr(ORACLE, "_accessibility_behavior_requested", None)
        self.assertTrue(callable(helper))
        for label, prompt in prompts.items():
            with self.subTest(label=label):
                if label != "unknown-cross-platform-target":
                    self.assertFalse(helper(prompt))
                observed = _route(prompt)
                route = _projected_route(observed)
                self.assertNotIn(
                    "accessibility-inclusive-design",
                    route["layer3_skills"],
                )
                if label != "ios-only-lifecycle":
                    self.assertNotIn(
                        "android-platform-extension",
                        route["layer3_skills"],
                    )

    def test_nine_owners_route_direct_with_registry_derived_primary(self) -> None:
        cases = {
            "backend-change-builder": (
                "Implement an accepted backend service behavior change."
            ),
            "frontend-change-builder": (
                "Implement an accepted browser frontend component state change."
            ),
            "installed-client-change-builder": (
                "Implement an accepted Android installed application lifecycle change."
            ),
            "data-middleware-change-builder": (
                "Implement an accepted queue middleware consistency change."
            ),
            "integration-change-builder": (
                "Implement an accepted external integration contract change."
            ),
            "repository-tooling-change-builder": (
                "Implement an accepted repository code generator source change."
            ),
            "platform-infrastructure-change-builder": (
                "Implement an accepted Terraform module source change."
            ),
            "quality-test-gate": (
                "Implement regression tests proving the changed behavior."
            ),
            "logging-design-gate": (
                "Implement a structured redacted logging schema change."
            ),
        }
        for primary, prompt in cases.items():
            with self.subTest(primary=primary):
                observed = _route(prompt)
                route = _projected_route(observed)
                self.assertEqual("direct", route["path"])
                self.assertEqual("task-agent", route["profile"])
                self.assertEqual(primary, route["primary_skill"])
                self.assertEqual(
                    (
                        "logging-design-gate"
                        if primary == "logging-design-gate"
                        else "ai-code-review-refactor"
                    ),
                    route["review_skill"],
                )
                self.assertLessEqual(len(route["layer3_skills"]), 3)

    def test_same_family_coalesces_and_conflicts_are_order_invariant(self) -> None:
        same = _route(
            "Implement accepted backend service and worker behavior changes."
        )
        same_candidates = [
            item
            for item in same["winner_trace"]["raw_candidates"]
            if item["candidate_id"].startswith("implementation-owner:")
        ]
        self.assertEqual(1, len(same_candidates))
        repository_backend = (
            "repository code generator source",
            "backend service behavior",
        )
        first = _route(
            f"Implement accepted {repository_backend[0]} and "
            f"{repository_backend[1]} changes."
        )
        second = _route(
            f"Implement accepted {repository_backend[1]} and "
            f"{repository_backend[0]} changes."
        )
        for observed in (first, second):
            route = _projected_route(observed)
            self.assertEqual("analyzed", route["path"])
            self.assertEqual(
                "engineering-change-analysis",
                route["primary_skill"],
            )
            self.assertEqual(
                "implementation-owner-conflict",
                observed["winner_trace"]["selected_candidate"]["reason"],
            )
        self.assertEqual(_projected_route(first), _projected_route(second))

        mismatches: list[str] = []
        scope_boundary_controls = {
            "backend:semicolon-context": {
                "prompt": (
                    "Implement accepted backend service behavior; Android "
                    "installed application lifecycle is background context "
                    "only."
                ),
                "family": "backend",
            },
            "frontend:semicolon-context": {
                "prompt": (
                    "Implement accepted browser frontend component state; "
                    "Android installed application lifecycle is background "
                    "context only."
                ),
                "family": "frontend",
            },
        }
        for label, control in scope_boundary_controls.items():
            actual_families = [
                row["routing_family"]
                for row in ORACLE.classify_professional_families(
                    control["prompt"]
                )
            ]
            expected_families = [control["family"]]
            if actual_families != expected_families:
                mismatches.append(
                    f"[{label}] mismatch=scope-boundary-family-classifier; "
                    f"expected={expected_families!r}; "
                    f"actual={actual_families!r}"
                )

        expected_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        shared_action_cases = {
            "backend:family-first": {
                "prompt": (
                    "Implement accepted backend service behavior and Android "
                    "installed application lifecycle changes."
                ),
                "family": "backend",
                "owner": "backend-change-builder",
            },
            "backend:client-first": {
                "prompt": (
                    "Implement accepted Android installed application "
                    "lifecycle and backend service behavior changes."
                ),
                "family": "backend",
                "owner": "backend-change-builder",
            },
            "frontend:family-first": {
                "prompt": (
                    "Implement accepted browser frontend component state and "
                    "Android installed application lifecycle changes."
                ),
                "family": "frontend",
                "owner": "frontend-change-builder",
            },
            "frontend:client-first": {
                "prompt": (
                    "Implement accepted Android installed application "
                    "lifecycle and browser frontend component state changes."
                ),
                "family": "frontend",
                "owner": "frontend-change-builder",
            },
        }
        routes_by_family: dict[str, list[dict[str, object]]] = {
            "backend": [],
            "frontend": [],
        }
        for label, case in shared_action_cases.items():
            prompt = case["prompt"]
            family = case["family"]
            owner = case["owner"]
            expected_families = sorted([family, "installed-client"])
            actual_families = sorted(
                row["routing_family"]
                for row in ORACLE.classify_professional_families(prompt)
            )
            if actual_families != expected_families:
                mismatches.append(
                    f"[{label}] mismatch=shared-action-family-classifier; "
                    f"expected={expected_families!r}; "
                    f"actual={actual_families!r}"
                )
            actual_domains = ORACLE.domain_route_families(prompt)
            expected_domains = [
                (
                    "android-platform-extension",
                    "platform-lifecycle-authority",
                )
            ]
            if actual_domains != expected_domains:
                mismatches.append(
                    f"[{label}] mismatch=domain-classifier; "
                    f"expected={expected_domains!r}; "
                    f"actual={actual_domains!r}"
                )
            try:
                observed = _route(prompt)
            except ORACLE.RoutingIntegrityError as exc:
                mismatches.append(
                    f"[{label}] mismatch=public-route-integrity; "
                    f"error={type(exc).__name__}: {exc}"
                )
                continue
            owner_ids = sorted(
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith(
                    "implementation-owner:"
                )
            )
            expected_owner_ids = sorted(
                [
                    f"implementation-owner:{owner}",
                    (
                        "implementation-owner:"
                        "installed-client-change-builder"
                    ),
                ]
            )
            if owner_ids != expected_owner_ids:
                mismatches.append(
                    f"[{label}] mismatch=raw-owner-multiset; "
                    f"expected={expected_owner_ids!r}; actual={owner_ids!r}"
                )
            selected = observed["winner_trace"]["selected_candidate"]
            if (
                selected.get("candidate_id")
                != "implementation-owner-conflict"
                or selected.get("candidate_type") != "derived-conflict"
                or selected.get("reason")
                != "implementation-owner-conflict"
            ):
                mismatches.append(
                    f"[{label}] mismatch=typed-conflict; "
                    f"actual={selected!r}"
                )
            actual_route = _projected_route(observed)
            if actual_route != expected_route:
                mismatches.append(
                    f"[{label}] mismatch=final-route; "
                    f"expected={expected_route!r}; actual={actual_route!r}"
                )
            trace = observed["winner_trace"]
            if (
                observed["route_decision"].get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{label}] mismatch=route-once-or-coverage; "
                    f"route_once={observed['route_decision'].get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )
            routes_by_family[family].append(actual_route)
        for family, routes in routes_by_family.items():
            if len(routes) == 2 and routes[0] != routes[1]:
                mismatches.append(
                    f"[{family}] mismatch=source-order-invariance; "
                    f"routes={routes!r}"
                )

        scope_local_anti_cases = {
            "backend:do-not-change:family-first": {
                "prompt": (
                    "Implement accepted backend service behavior and do not "
                    "change Android installed application lifecycle."
                ),
                "family": "backend",
                "owner": "backend-change-builder",
            },
            "backend:do-not-change:anti-first": {
                "prompt": (
                    "Do not change Android installed application lifecycle "
                    "and implement accepted backend service behavior."
                ),
                "family": "backend",
                "owner": "backend-change-builder",
            },
            "backend:background-context:family-first": {
                "prompt": (
                    "Implement accepted backend service behavior and Android "
                    "installed application lifecycle is background context "
                    "only."
                ),
                "family": "backend",
                "owner": "backend-change-builder",
            },
            "backend:background-context:anti-first": {
                "prompt": (
                    "Android installed application lifecycle is background "
                    "context only and implement accepted backend service "
                    "behavior."
                ),
                "family": "backend",
                "owner": "backend-change-builder",
            },
            "frontend:do-not-change:family-first": {
                "prompt": (
                    "Implement accepted browser frontend component state and "
                    "do not change Android installed application lifecycle."
                ),
                "family": "frontend",
                "owner": "frontend-change-builder",
            },
            "frontend:do-not-change:anti-first": {
                "prompt": (
                    "Do not change Android installed application lifecycle "
                    "and implement accepted browser frontend component state."
                ),
                "family": "frontend",
                "owner": "frontend-change-builder",
            },
            "frontend:background-context:family-first": {
                "prompt": (
                    "Implement accepted browser frontend component state and "
                    "Android installed application lifecycle is background "
                    "context only."
                ),
                "family": "frontend",
                "owner": "frontend-change-builder",
            },
            "frontend:background-context:anti-first": {
                "prompt": (
                    "Android installed application lifecycle is background "
                    "context only and implement accepted browser frontend "
                    "component state."
                ),
                "family": "frontend",
                "owner": "frontend-change-builder",
            },
        }
        executed_scope_local_anti: list[str] = []
        for label, case in scope_local_anti_cases.items():
            executed_scope_local_anti.append(label)
            prompt = case["prompt"]
            family = case["family"]
            owner = case["owner"]
            expected_families = [family]
            actual_families = [
                row["routing_family"]
                for row in ORACLE.classify_professional_families(prompt)
            ]
            if actual_families != expected_families:
                mismatches.append(
                    f"[{label}] mismatch=scope-local-anti-owner-deleted; "
                    f"expected={expected_families!r}; "
                    f"actual={actual_families!r}"
                )
            actual_domains = ORACLE.domain_route_families(prompt)
            if actual_domains:
                mismatches.append(
                    f"[{label}] mismatch=scope-local-anti-extra-domain; "
                    f"expected=[]; actual={actual_domains!r}"
                )
            try:
                observed = _route(prompt)
            except ORACLE.RoutingIntegrityError as exc:
                mismatches.append(
                    f"[{label}] mismatch=scope-local-anti-route-error; "
                    f"error={type(exc).__name__}: {exc}"
                )
                continue
            owner_ids = sorted(
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith(
                    "implementation-owner:"
                )
            )
            expected_owner_ids = [f"implementation-owner:{owner}"]
            if owner_ids != expected_owner_ids:
                mismatches.append(
                    f"[{label}] mismatch=scope-local-anti-raw-owner; "
                    f"expected={expected_owner_ids!r}; "
                    f"actual={owner_ids!r}"
                )
            expected_direct_route = {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": owner,
                "layer3_skills": [],
                "review_skill": "ai-code-review-refactor",
            }
            actual_route = _projected_route(observed)
            if actual_route != expected_direct_route:
                mismatches.append(
                    f"[{label}] mismatch=scope-local-anti-route-error; "
                    f"expected={expected_direct_route!r}; "
                    f"actual={actual_route!r}"
                )
            trace = observed["winner_trace"]
            if (
                observed["route_decision"].get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{label}] mismatch=scope-local-anti-route-proof; "
                    f"route_once={observed['route_decision'].get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )
        if executed_scope_local_anti != list(scope_local_anti_cases):
            mismatches.append(
                "[scope-local-anti] mismatch=case-execution; "
                f"expected={list(scope_local_anti_cases)!r}; "
                f"actual={executed_scope_local_anti!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_duplicate_classifier_rows_union_evidence_before_owner_resolution(
        self,
    ) -> None:
        duplicate_backend = [
            {
                "routing_family": "backend",
                "match_evidence": ["a"],
            },
            {
                "routing_family": "backend",
                "match_evidence": ["b"],
            },
        ]
        with patch.object(
            ORACLE,
            "classify_professional_families",
            return_value=duplicate_backend,
        ):
            observed = _route(
                "Implement an accepted backend service behavior change."
            )
        owner_candidates = [
            item
            for item in observed["winner_trace"]["raw_candidates"]
            if item["candidate_id"] == "implementation-owner:backend-change-builder"
        ]
        self.assertEqual(1, len(owner_candidates))
        self.assertEqual(["a", "b"], owner_candidates[0]["evidence"])
        self.assertEqual(
            "backend-change-builder",
            _projected_route(observed)["primary_skill"],
        )

    def test_direct_owner_preserves_one_review_risk_and_conflicts_on_two(
        self,
    ) -> None:
        one_risk = _route(
            "Implement an accepted backend service change across a proved reachable "
            "authorization boundary where a less-trusted tenant writer feeds a "
            "privileged service."
        )
        self.assertEqual(
            "backend-change-builder",
            _projected_route(one_risk)["primary_skill"],
        )
        self.assertEqual(
            "security-privacy-gate",
            _projected_route(one_risk)["review_skill"],
        )
        two_risks = _route(
            "Implement an accepted backend service change across a proved reachable "
            "authorization boundary where a less-trusted tenant writer feeds a "
            "privileged service with a material production rollout decision."
        )
        self.assertEqual("analyzed", _projected_route(two_risks)["path"])
        self.assertEqual(
            "review-risk-owner-conflict",
            two_risks["winner_trace"]["selected_candidate"]["candidate_id"],
        )

    def test_zero_family_falls_through_and_preparation_precedes_owner(self) -> None:
        zero = _route("Explain repository terminology without editing anything.")
        self.assertEqual(
            "repository-first-default",
            zero["winner_trace"]["rule_id"],
        )
        prepared = _route(
            "Prepare an accepted backend service implementation before editing."
        )
        self.assertEqual("analyzed", _projected_route(prepared)["path"])
        self.assertEqual(
            "implementation-preparation",
            prepared["winner_trace"]["selected_candidate"]["candidate_id"],
        )
        self.assertTrue(
            any(
                item["candidate_id"].startswith("implementation-owner:")
                for item in prepared["winner_trace"]["raw_candidates"]
            )
        )

    def test_delivery_is_not_an_automatic_owner(self) -> None:
        observed = _route(
            "Approve a production apply, deployment, release, and rollback."
        )
        self.assertFalse(
            any(
                item["candidate_id"]
                == "implementation-owner:delivery-release-gate"
                for item in observed["winner_trace"]["raw_candidates"]
            )
        )
        self.assertEqual(
            "delivery-release-gate",
            _projected_route(observed)["primary_skill"],
        )

    def test_wave1a_runtime_config_and_dependency_owner_matrix_red(
        self,
    ) -> None:
        rows = {
            row["id"]: row
            for row in load_yaml_file(
                ROOT / "evals" / "routing" / "cases.yaml"
            )["cases"]
        }
        config_target_ids = (
            "wave1a-config-frontend",
            "wave1a-config-installed-client",
            "wave1a-config-backend",
            "wave1a-config-data-middleware",
            "wave1a-config-platform-infrastructure",
            "wave1a-config-integration",
            "wave1a-config-repository-tooling",
        )
        failures: list[str] = []
        for case_id in config_target_ids:
            row = rows[case_id]
            observed = ORACLE.route_with_trace(
                row["prompt"],
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            actual = _projected_route(observed)
            expected = row["expected"]
            owner_ids = sorted(
                candidate["candidate_id"]
                for candidate in observed["winner_trace"]["raw_candidates"]
                if candidate["candidate_id"].startswith(
                    "implementation-owner:"
                )
            )
            expected_owner_ids = [
                f"implementation-owner:{expected['primary_skill']}"
            ]
            if owner_ids != expected_owner_ids:
                failures.append(
                    f"{case_id}: owner-candidates expected="
                    f"{expected_owner_ids!r}; actual={owner_ids!r}"
                )
            if "configuration-runtime-policy" not in actual["layer3_skills"]:
                failures.append(
                    f"{case_id}: missing-selector:"
                    "configuration-runtime-policy"
                )
            if actual != expected:
                failures.append(
                    f"{case_id}: route-mismatch expected={expected!r}; "
                    f"actual={actual!r}"
                )
            if len(expected["layer3_skills"]) > 3:
                failures.append(
                    f"{case_id}: invalid-expected-layer3-budget"
                )
        dependency_target_ids = (
            "wave1a-dependency-frontend",
            "wave1a-dependency-installed-client",
            "wave1a-dependency-backend",
            "wave1a-dependency-data-middleware",
            "wave1a-dependency-platform-infrastructure",
            "wave1a-dependency-integration",
            "wave1a-dependency-repository-tooling",
        )
        for case_id in dependency_target_ids:
            row = rows[case_id]
            observed = ORACLE.route_with_trace(
                row["prompt"],
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            actual = _projected_route(observed)
            expected = row["expected"]
            owner_ids = sorted(
                candidate["candidate_id"]
                for candidate in observed["winner_trace"]["raw_candidates"]
                if candidate["candidate_id"].startswith(
                    "implementation-owner:"
                )
            )
            expected_owner_ids = [
                f"implementation-owner:{expected['primary_skill']}"
            ]
            if owner_ids != expected_owner_ids:
                failures.append(
                    f"{case_id}: owner-candidates expected="
                    f"{expected_owner_ids!r}; actual={owner_ids!r}"
                )
            if (
                "dependency-vulnerability-scanning"
                not in actual["layer3_skills"]
            ):
                failures.append(
                    f"{case_id}: missing-selector:"
                    "dependency-vulnerability-scanning"
                )
            if actual["review_skill"] != "security-privacy-gate":
                failures.append(
                    f"{case_id}: missing-review-consumer:"
                    "security-privacy-gate"
                )
            if actual != expected:
                failures.append(
                    f"{case_id}: route-mismatch expected={expected!r}; "
                    f"actual={actual!r}"
                )
            if len(expected["layer3_skills"]) > 3:
                failures.append(
                    f"{case_id}: invalid-expected-layer3-budget"
                )
        self.assertEqual([], failures)

    def test_wave1a_config_dependency_and_sandbox_negatives_stay_green(
        self,
    ) -> None:
        rows = {
            row["id"]: row
            for row in load_yaml_file(
                ROOT / "evals" / "routing" / "cases.yaml"
            )["cases"]
        }
        target_ids = (
            "wave1a-config-generic-negative",
            "wave1a-config-build-only-negative",
            "wave1a-config-secret-only-negative",
            "wave1a-dependency-package-mechanics-negative",
            "wave1a-dependency-lockfile-negative",
            "wave1a-dependency-advisory-keyword-negative",
            "wave1a-sandbox-dev-only-negative",
        )
        failures: list[str] = []
        for case_id in target_ids:
            row = rows[case_id]
            observed = ORACLE.route_with_trace(
                row["prompt"],
                main_execution=copy.deepcopy(row["main_execution"]),
            )
            actual = _projected_route(observed)
            if actual != row["expected"]:
                failures.append(
                    f"{case_id}: expected={row['expected']!r}; "
                    f"actual={actual!r}"
                )
            selected = {
                actual["primary_skill"],
                actual["review_skill"],
                *actual["layer3_skills"],
            }
            leaked = sorted(
                selected.intersection(row["excluded_skills"])
            )
            if leaked:
                failures.append(f"{case_id}: leaked={leaked!r}")
            if len(actual["layer3_skills"]) > 3:
                failures.append(
                    f"{case_id}: layer3-overflow="
                    f"{actual['layer3_skills']!r}"
                )
        self.assertEqual([], failures)


class RoutingIntegrityTests(unittest.TestCase):
    def test_malformed_injected_authority_fails_closed_with_one_error_type(self) -> None:
        error_type = getattr(ORACLE, "RoutingIntegrityError", None)
        self.assertTrue(
            isinstance(error_type, type),
            "production RoutingIntegrityError is missing",
        )
        malformed = copy.deepcopy(_registry())
        malformed["professional_skills"][11]["routing_family"] = "unknown"
        with self.assertRaises(error_type) as caught:
            _route("Implement an accepted browser frontend component change.", malformed)
        self.assertEqual("routing-integrity-failure", caught.exception.code)

        semantically_different = copy.deepcopy(_registry())
        backend = next(
            row
            for row in semantically_different["professional_skills"]
            if row.get("routing_family") == "backend"
        )
        frontend = next(
            row
            for row in semantically_different["professional_skills"]
            if row.get("routing_family") == "frontend"
        )
        backend["routing_family"], frontend["routing_family"] = (
            frontend["routing_family"],
            backend["routing_family"],
        )
        stage_names = (
            "_normalize_route_prompt",
            "_build_route_candidates",
            "_select_route_cohort_candidate",
            "compose_domain_extensions",
            "_project_route_selection",
            "validate_route_decision",
        )
        patches = [
            patch.object(
                ORACLE,
                name,
                wraps=getattr(ORACLE, name),
            )
            for name in stage_names
        ]
        spies = [item.start() for item in patches]
        try:
            with self.assertRaises(error_type) as caught:
                _route(
                    "Implement an accepted browser frontend component change.",
                    semantically_different,
                )
        finally:
            for item in reversed(patches):
                item.stop()
        self.assertEqual("routing-integrity-failure", caught.exception.code)
        self.assertIn(
            "Professional automatic-owner authority differs",
            str(caught.exception),
        )
        self.assertEqual(
            {name: 0 for name in stage_names},
            {
                name: spy.call_count
                for name, spy in zip(stage_names, spies, strict=True)
            },
        )

        reordered = copy.deepcopy(_registry())
        reordered["professional_skills"] = [
            dict(reversed(tuple(row.items())))
            for row in reversed(reordered["professional_skills"])
        ]
        automatic = next(
            row
            for row in reordered["professional_skills"]
            if row.get("routing_family") == "backend"
        )
        automatic["layer3_candidates"] = list(
            reversed(automatic["layer3_candidates"])
        )
        observed = _route(
            "Implement an accepted backend service behavior change.",
            reordered,
        )
        self.assertEqual(
            "backend-change-builder",
            _projected_route(observed)["primary_skill"],
        )

    def test_derived_layer3_accepts_three_and_fails_closed_for_invalid_sets(
        self,
    ) -> None:
        error_type = getattr(ORACLE, "RoutingIntegrityError", None)
        self.assertTrue(isinstance(error_type, type))
        prompt = "Implement an accepted backend service behavior change."
        accepted = [
            "domain-object-identification",
            "implementation-structure-design",
            "regression-testing",
        ]
        with patch.object(
            ORACLE,
            "_implementation_owner_layer3",
            return_value=accepted,
        ):
            observed = _route(prompt)
        self.assertEqual(accepted, _projected_route(observed)["layer3_skills"])

        overflow = [
            "domain-object-identification",
            "implementation-structure-design",
            "minimal-correct-implementation",
            "regression-testing",
        ]
        with patch.object(
            ORACLE,
            "_implementation_owner_layer3",
            return_value=overflow,
        ):
            observed = _route(prompt)
        self.assertEqual(
            "foundation-layer3-overflow",
            observed["winner_trace"]["selected_candidate"]["candidate_id"],
        )
        self.assertEqual(
            sorted(overflow),
            observed["winner_trace"]["selected_candidate"][
                "eligible_layer3_skills"
            ],
        )
        self.assertEqual(
            ["repository-context-map"],
            _projected_route(observed)["layer3_skills"],
        )

        invalid_sets = (
            ["regression-testing", "regression-testing"],
            ["unknown-layer3"],
        )
        for index, value in enumerate(invalid_sets):
            with self.subTest(index=index):
                with patch.object(
                    ORACLE,
                    "_implementation_owner_layer3",
                    return_value=value,
                ), self.assertRaises(error_type) as caught:
                    _route(prompt)
                self.assertEqual(
                    "routing-integrity-failure",
                    caught.exception.code,
                )

    def test_evaluator_records_derived_layer3_integrity_failure(self) -> None:
        invalid = [
            "domain-object-identification",
            "implementation-structure-design",
            "minimal-correct-implementation",
            "regression-testing",
        ]
        with patch.object(
            ORACLE,
            "_implementation_owner_layer3",
            return_value=invalid,
        ), patch.object(
            EVAL_ROUTING,
            "route_with_trace",
            ORACLE.route_with_trace,
        ):
            report = EVAL_ROUTING.evaluate_routes(
                _validate_capability_matrix=False,
            )
        failed = [
            item
            for item in report["results"]
            if any(
                "routing-integrity-failure" in error
                for error in item["errors"]
            )
        ]
        self.assertTrue(failed)
        self.assertTrue(all(item["actual"] is None for item in failed))


class InventoryAndEvaluatorTests(unittest.TestCase):
    def test_full13_and_domain_routes_removed_with_63_returns_retained(self) -> None:
        direct = _direct_rule_ids()
        self.assertEqual(0, len(direct))
        self.assertTrue(FULL13.isdisjoint(direct))
        source = ORACLE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        route_impl = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_route_impl"
        )
        direct_candidate_ids = {
            keyword.value.value
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_candidate"
            for keyword in node.keywords
            if keyword.arg == "rule_id"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        }
        selector_ids_by_symbol = {
            target.id: node.value.args[0].value
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance((target := node.targets[0]), ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "_FoundationSelectorSpec"
            and node.value.args
            and isinstance(node.value.args[0], ast.Constant)
            and isinstance(node.value.args[0].value, str)
        }
        wired_selector_symbols = [
            node.args[0].id
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_foundation_selector"
            and node.args
            and isinstance(node.args[0], ast.Name)
        ]
        self.assertTrue(
            all(
                symbol in selector_ids_by_symbol
                for symbol in wired_selector_symbols
            ),
            "every live selector call must resolve to its local typed spec",
        )
        wired_selector_ids = {
            selector_ids_by_symbol[symbol]
            for symbol in wired_selector_symbols
        }
        direct_retained = RETAINED63_CONTROLS & direct_candidate_ids
        selector_retained = RETAINED63_CONTROLS & wired_selector_ids
        self.assertEqual(7, len(direct_retained))
        self.assertEqual(6, len(selector_retained))
        candidate_ids = direct_candidate_ids | wired_selector_ids
        self.assertTrue(RETAINED63_CONTROLS.issubset(candidate_ids))
        self.assertNotIn("return result(", source)

    def test_evaluator_exposes_stable_policy_fingerprint(self) -> None:
        report = EVAL_ROUTING.evaluate_routes(
            _validate_capability_matrix=False,
        )
        helper = getattr(
            VALIDATION,
            "professional_automatic_routing_policy_fingerprint",
            None,
        )
        self.assertTrue(callable(helper))
        expected = helper(_registry())
        self.assertEqual(POLICY_SHA256, expected)
        self.assertEqual(
            expected,
            report["automatic_routing_policy_fingerprint"],
        )
        legacy_field = "_".join(
            ("implementation", "owner", "policy", "fingerprint")
        )
        self.assertNotIn(legacy_field, report)
        self.assertRegex(expected, r"^[0-9a-f]{64}$")

    def test_evaluator_records_integrity_error_without_public_route(self) -> None:
        malformed = copy.deepcopy(_registry())
        malformed["professional_skills"][11][
            "routing_family"
        ] = "unknown"
        report = EVAL_ROUTING.evaluate_routes(
            _validate_capability_matrix=False,
            professional_registry=malformed,
        )
        self.assertEqual("fail", report["status"])
        self.assertEqual("unavailable", report[
            "automatic_routing_policy_fingerprint"
        ])
        self.assertTrue(report["results"])
        self.assertTrue(
            all(item["actual"] is None for item in report["results"])
        )
        self.assertTrue(
            all(item["route_decision"] is None for item in report["results"])
        )
        self.assertTrue(
            all(
                item["winner_trace"]["candidate_coverage"] == "unavailable"
                and item["winner_trace"]["route_once"] == "unavailable"
                for item in report["results"]
            )
        )
        self.assertTrue(
            all(
                any(
                    "routing-integrity-failure" in error
                    for error in item["errors"]
                )
                for item in report["results"]
            )
        )


if __name__ == "__main__":
    unittest.main()
