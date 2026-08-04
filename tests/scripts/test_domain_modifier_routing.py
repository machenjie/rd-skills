from __future__ import annotations

import ast
import copy
import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import capability_coverage as CAPABILITY_COVERAGE
import deterministic_route_oracle as ORACLE
import validation_utils as VALIDATION
from validation_utils import load_yaml_file

from tests.scripts import test_route_candidate_cohorts as COHORTS
from tests.scripts import test_route_review_risk_candidates as REVIEW_RISKS


DOMAIN_REGISTRY = ROOT / "src/registry/domain-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
ORACLE_PATH = ROOT / "scripts/deterministic_route_oracle.py"
CAPABILITY_ROUTE_CASES = ROOT / "evals/routing/capability-coverage-cases.yaml"
CLIENT_DOMAIN_NAMES = {
    "android-platform-extension",
    "cross-platform-client-extension",
    "ios-ipados-platform-extension",
    "linux-desktop-platform-extension",
    "macos-platform-extension",
    "windows-platform-extension",
}
NATURAL_CLIENT_DOMAIN_EXPECTATIONS = {
    "capcov-natural-android-screen-state": [
        "android-platform-extension",
    ],
    "capcov-natural-android-foreground-background": [
        "android-platform-extension",
    ],
    "capcov-natural-ios-swiftui-view-state": [
        "ios-ipados-platform-extension",
    ],
    "capcov-natural-ios-scene-background-task": [
        "ios-ipados-platform-extension",
    ],
    "capcov-natural-windows-packaged-desktop-app": [
        "windows-platform-extension",
    ],
    "capcov-natural-macos-appkit-app": [
        "macos-platform-extension",
    ],
    "capcov-natural-linux-graphical-desktop-app": [
        "linux-desktop-platform-extension",
    ],
    "capcov-natural-flutter-android-ios": [
        "android-platform-extension",
        "cross-platform-client-extension",
        "ios-ipados-platform-extension",
    ],
    "capcov-natural-electron-windows": [
        "cross-platform-client-extension",
        "windows-platform-extension",
    ],
    "capcov-natural-kotlin-backend": [],
    "capcov-natural-swift-linux-backend": [],
    "capcov-natural-csharp-linux-backend": [],
    "capcov-natural-cpp-linux-server": [],
    "capcov-natural-dart-backend": [],
    "capcov-natural-cross-target-unknown": [],
    "capcov-natural-pwa-web-only": [],
    "capcov-natural-android-store-rollout": [],
}
NEIGHBOR_CLIENT_DOMAIN_EXPECTATIONS = {
    "capcov-neighbor-android-app-state-backend-payload": [],
    "capcov-neighbor-ios-app-state-backend-payload": [],
    "capcov-neighbor-macos-swiftui-window": [
        "macos-platform-extension",
    ],
    "capcov-neighbor-android-compose-view": [
        "android-platform-extension",
    ],
    "capcov-neighbor-windows-wpf-window": [
        "windows-platform-extension",
    ],
    "capcov-neighbor-windows-winui-view": [
        "windows-platform-extension",
    ],
}
DOCUMENTATION_ORDER_CLIENT_DOMAIN_EXPECTATIONS = {
    "capcov-docs-order-android-compose": [],
    "capcov-docs-order-leading-only-android-compose-analyze": [],
    "capcov-docs-order-leading-only-android-compose-inspect": [],
    "capcov-docs-order-leading-only-android-compose-review": [],
    "capcov-docs-order-macos-swiftui": [],
    "capcov-docs-order-windows-wpf": [],
    "capcov-docs-order-windows-winui": [],
}
REMOVED_DIRECT_IDS = {
    "cross-platform-composition-unresolved",
    "installed-client-layer-budget",
    "domain-composition-conflict",
    "domain-layer-budget",
    "domain-family-route",
}
EXPECTED_RECIPROCITY = {
    "ai-product-extension": {
        "ai-code-review-refactor",
        "backend-change-builder",
        "data-middleware-change-builder",
        "engineering-change-analysis",
        "frontend-change-builder",
        "installed-client-change-builder",
        "integration-change-builder",
        "security-privacy-gate",
    },
    "android-platform-extension": {
        "ai-code-review-refactor",
        "engineering-change-analysis",
        "installed-client-change-builder",
    },
    "bigdata-product-extension": {
        "data-middleware-change-builder",
        "engineering-change-analysis",
    },
    "cloud-platform-extension": {
        "backend-change-builder",
        "engineering-change-analysis",
        "platform-infrastructure-change-builder",
        "reliability-observability-gate",
        "security-privacy-gate",
    },
    "cross-platform-client-extension": {
        "ai-code-review-refactor",
        "engineering-change-analysis",
        "installed-client-change-builder",
    },
    "ios-ipados-platform-extension": {
        "ai-code-review-refactor",
        "engineering-change-analysis",
        "installed-client-change-builder",
    },
    "iot-embedded-extension": {
        "delivery-release-gate",
        "engineering-change-analysis",
    },
    "linux-desktop-platform-extension": {
        "ai-code-review-refactor",
        "engineering-change-analysis",
        "installed-client-change-builder",
    },
    "low-level-systems-extension": {
        "backend-change-builder",
        "engineering-change-analysis",
    },
    "macos-platform-extension": {
        "ai-code-review-refactor",
        "engineering-change-analysis",
        "installed-client-change-builder",
    },
    "payment-trading-extension": {
        "backend-change-builder",
        "engineering-change-analysis",
        "security-privacy-gate",
    },
    "web3-product-extension": {
        "engineering-change-analysis",
        "integration-change-builder",
    },
    "windows-platform-extension": {
        "ai-code-review-refactor",
        "backend-change-builder",
        "domain-impact-modeler",
        "engineering-change-analysis",
        "installed-client-change-builder",
    },
}
DOMAIN_EVIDENCE_MATRIX = {
    "ai-product-extension": (
        "model decision with delegated authority",
        "model",
    ),
    "android-platform-extension": (
        "Android application lifecycle",
        "Android",
    ),
    "bigdata-product-extension": (
        "stream checkpoint",
        "stream",
    ),
    "cloud-platform-extension": (
        "cloud control plane account authority",
        "cloud control plane",
    ),
    "cross-platform-client-extension": (
        "Flutter shared installed client with concrete platform targets "
        "for Android application lifecycle",
        "Flutter shared installed client",
    ),
    "ios-ipados-platform-extension": (
        "iOS application lifecycle",
        "iOS",
    ),
    "iot-embedded-extension": (
        "firmware recovery",
        "firmware",
    ),
    "linux-desktop-platform-extension": (
        "Linux graphical desktop desktop session",
        "Linux graphical desktop",
    ),
    "low-level-systems-extension": (
        "Rust FFI ownership",
        "Rust",
    ),
    "macos-platform-extension": (
        "macOS installed application lifecycle",
        "macOS installed application",
    ),
    "payment-trading-extension": (
        "payment reconciliation",
        "payment",
    ),
    "web3-product-extension": (
        "blockchain finality",
        "blockchain",
    ),
    "windows-platform-extension": (
        "Windows service lifecycle",
        "Windows service",
    ),
}
CLASSIFIER_FIELDS = {
    "skill",
    "eligible",
    "evidence_ids",
    "rejection_reasons",
}
COMPATIBILITY_ROUTE_FIELDS = {
    "path",
    "profile",
    "primary_skill",
    "layer3_skills",
    "review_skill",
}


def _domain_registry() -> dict[str, object]:
    value = load_yaml_file(DOMAIN_REGISTRY)
    if not isinstance(value, dict):
        raise AssertionError("Domain registry must be a mapping")
    return value


def _professional_registry() -> dict[str, object]:
    value = load_yaml_file(PROFESSIONAL_REGISTRY)
    if not isinstance(value, dict):
        raise AssertionError("Professional registry must be a mapping")
    return value


def _domain_order() -> list[str]:
    return [
        row["name"]
        for row in _domain_registry()["domain_skills"]
    ]


def _eligible_skills(prompt: str) -> list[str]:
    classifier = getattr(ORACLE, "classify_domain_modifiers", None)
    if not callable(classifier):
        raise AssertionError("evidence-bound Domain modifier classifier is missing")
    return [
        item["skill"]
        for item in classifier(prompt)
        if item["eligible"] is True
    ]


class DomainModifierRegistryContractTests(unittest.TestCase):
    def test_all_domains_are_modifier_only_with_exact_reciprocal_edges(self) -> None:
        domains = _domain_registry()["domain_skills"]
        professionals = _professional_registry()["professional_skills"]
        self.assertEqual(13, len(domains))
        self.assertTrue(
            all(row.get("routing_mode") == "modifier-only" for row in domains)
        )
        actual = {
            row["name"]: set(row.get("used_by", []))
            for row in domains
        }
        self.assertEqual(EXPECTED_RECIPROCITY, actual)
        self.assertEqual(44, sum(len(owners) for owners in actual.values()))
        domain_names = set(actual)
        professional_edges = {
            (row["name"], candidate)
            for row in professionals
            for candidate in row.get("layer3_candidates", [])
            if candidate in domain_names
        }
        expected_edges = {
            (owner, domain)
            for domain, owners in EXPECTED_RECIPROCITY.items()
            for owner in owners
        }
        self.assertEqual(expected_edges, professional_edges)
        eca = next(
            row
            for row in professionals
            if row["name"] == "engineering-change-analysis"
        )
        self.assertEqual(
            domain_names,
            domain_names.intersection(eca["layer3_candidates"]),
        )

    def test_registry_authority_fails_closed_on_integrity_mutations(self) -> None:
        authority = getattr(
            VALIDATION,
            "domain_modifier_routing_authority",
            None,
        )
        self.assertTrue(callable(authority))
        if not callable(authority):
            return
        domains = _domain_registry()
        professionals = _professional_registry()
        mutations: list[tuple[dict[str, object], dict[str, object]]] = []

        stale_mode = copy.deepcopy(domains)
        stale_mode["domain_skills"][0]["routing_mode"] = "automatic"
        mutations.append((stale_mode, professionals))

        duplicate_owner = copy.deepcopy(domains)
        duplicate_owner["domain_skills"][0]["used_by"].append(
            duplicate_owner["domain_skills"][0]["used_by"][0]
        )
        mutations.append((duplicate_owner, professionals))

        missing_reciprocal = copy.deepcopy(professionals)
        eca = next(
            row
            for row in missing_reciprocal["professional_skills"]
            if row["name"] == "engineering-change-analysis"
        )
        eca["layer3_candidates"].remove("ai-product-extension")
        mutations.append((domains, missing_reciprocal))

        missing_domain_half = copy.deepcopy(domains)
        ai = next(
            row
            for row in missing_domain_half["domain_skills"]
            if row["name"] == "ai-product-extension"
        )
        ai["used_by"].remove("backend-change-builder")
        mutations.append((missing_domain_half, professionals))

        incompatible_role = copy.deepcopy(domains)
        incompatible_role["domain_skills"][0]["role_support"] = [
            "review-agent"
        ]
        mutations.append((incompatible_role, professionals))

        duplicate_domain = copy.deepcopy(domains)
        duplicate_domain["domain_skills"].append(
            copy.deepcopy(duplicate_domain["domain_skills"][0])
        )
        mutations.append((duplicate_domain, professionals))

        for index, (domain_data, professional_data) in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(VALIDATION.ValidationProblem):
                    authority(domain_data, professional_data)

        semantic_mutations: list[
            tuple[str, dict[str, object], dict[str, object]]
        ] = []
        changed_mode = copy.deepcopy(domains)
        changed_mode["domain_skills"][0]["routing_mode"] = "automatic"
        semantic_mutations.append(("modifier-mode", changed_mode, professionals))

        changed_edges = copy.deepcopy(domains)
        changed_professionals = copy.deepcopy(professionals)
        ai = next(
            row
            for row in changed_edges["domain_skills"]
            if row["name"] == "ai-product-extension"
        )
        web3 = next(
            row
            for row in changed_edges["domain_skills"]
            if row["name"] == "web3-product-extension"
        )
        ai["used_by"].remove("security-privacy-gate")
        web3["used_by"].append("security-privacy-gate")
        web3["used_by"].sort()
        security = next(
            row
            for row in changed_professionals["professional_skills"]
            if row["name"] == "security-privacy-gate"
        )
        security["layer3_candidates"].remove("ai-product-extension")
        security["layer3_candidates"].append("web3-product-extension")
        self.assertIsInstance(
            authority(changed_edges, changed_professionals),
            dict,
        )
        semantic_mutations.append(
            ("used-by-reciprocity", changed_edges, changed_professionals)
        )

        changed_roles = copy.deepcopy(domains)
        android = next(
            row
            for row in changed_roles["domain_skills"]
            if row["name"] == "android-platform-extension"
        )
        android["role_support"] = ["analysis-agent", "task-agent"]
        with self.assertRaises(VALIDATION.ValidationProblem):
            authority(changed_roles, professionals)

        stage_names = (
            "_normalize_route_prompt",
            "_build_route_candidates",
            "_select_route_cohort_candidate",
            "compose_domain_extensions",
            "_project_route_selection",
            "validate_route_decision",
        )
        for label, domain_data, professional_data in semantic_mutations:
            with self.subTest(semantic=label):
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
                    with self.assertRaises(
                        ORACLE.RoutingIntegrityError
                    ) as caught:
                        ORACLE.route(
                            "Implement an accepted backend service change.",
                            main_execution=COHORTS._test_main_execution(
                                f"t2g-domain-authority-{label}"
                            ),
                            domain_registry=domain_data,
                            professional_registry=professional_data,
                        )
                finally:
                    for item in reversed(patches):
                        item.stop()
                self.assertEqual(
                    "routing-integrity-failure",
                    caught.exception.code,
                )
                self.assertEqual(
                    {name: 0 for name in stage_names},
                    {
                        name: spy.call_count
                        for name, spy in zip(
                            stage_names,
                            spies,
                            strict=True,
                        )
                    },
                )


class DomainModifierClassifierTests(unittest.TestCase):
    def test_catalog_is_semantic_only_and_classifier_shape_is_closed(self) -> None:
        catalog = ORACLE._DOMAIN_ROUTE_SPEC_CATALOG
        professional_ids = {
            row["name"]
            for row in _professional_registry()["professional_skills"]
        }
        forbidden_fields = {
            "route",
            "modifier_only",
            "owner",
            "path",
            "profile",
            "review",
            "review_skill",
            "execution_level",
            "level_basis",
        }
        for skill, spec in catalog.items():
            with self.subTest(skill=skill):
                self.assertTrue(forbidden_fields.isdisjoint(spec))
                source = repr(spec)
                self.assertEqual(
                    [],
                    sorted(name for name in professional_ids if name in source),
                )

        classifier = getattr(ORACLE, "classify_domain_modifiers", None)
        self.assertTrue(callable(classifier))
        if not callable(classifier):
            return
        rows = classifier("Implement an accepted backend service behavior change.")
        self.assertEqual(set(DOMAIN_EVIDENCE_MATRIX), {
            row["skill"] for row in rows
        })
        self.assertTrue(all(set(row) == CLASSIFIER_FIELDS for row in rows))
        classifier_source = inspect.getsource(classifier)
        self.assertEqual(
            [],
            sorted(name for name in professional_ids if name in classifier_source),
        )
        self.assertTrue(
            {
                "owner",
                "path",
                "profile",
                "review_skill",
                "execution_level",
                "level_basis",
            }.isdisjoint(classifier_source.split())
        )

    def test_39_case_evidence_matrix_and_source_order_negatives(self) -> None:
        self.assertGreaterEqual(len(DOMAIN_EVIDENCE_MATRIX) * 3, 28)
        classifier = getattr(ORACLE, "classify_domain_modifiers", None)
        self.assertTrue(callable(classifier))
        if not callable(classifier):
            return
        base = "Implement an accepted backend service behavior change"
        for skill, (positive, trigger_only) in DOMAIN_EVIDENCE_MATRIX.items():
            with self.subTest(skill=skill, variant="positive"):
                row = next(
                    item
                    for item in classifier(f"Implement a {positive} change.")
                    if item["skill"] == skill
                )
                self.assertTrue(row["eligible"])
                self.assertTrue(row["evidence_ids"])
                self.assertEqual([], row["rejection_reasons"])
            with self.subTest(skill=skill, variant="trigger-only"):
                row = next(
                    item
                    for item in classifier(
                        f"Inspect the {trigger_only} keyword only."
                    )
                    if item["skill"] == skill
                )
                self.assertFalse(row["eligible"])
                self.assertTrue(row["rejection_reasons"])
            unchanged = f"{positive} behavior remains unchanged"
            for prompt in (
                f"{base}; {unchanged}.",
                f"{unchanged}; {base}.",
            ):
                with self.subTest(
                    skill=skill,
                    variant="unchanged-source-order",
                    prompt=prompt,
                ):
                    row = next(
                        item
                        for item in classifier(prompt)
                        if item["skill"] == skill
                    )
                    self.assertFalse(row["eligible"])
                    self.assertTrue(row["rejection_reasons"])

    def test_natural_client_compound_signals_and_negative_controls(self) -> None:
        document = load_yaml_file(CAPABILITY_ROUTE_CASES)
        self.assertEqual({"schema_version", "cases"}, set(document))
        self.assertEqual(1, document["schema_version"])
        cases = document["cases"]
        self.assertEqual(62, len(cases))
        rows = {
            row["id"]: row
            for row in cases
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        self.assertEqual(62, len(rows))
        natural_ids = {
            case_id
            for case_id in rows
            if case_id.startswith("capcov-natural-")
        }
        self.assertEqual(
            set(NATURAL_CLIENT_DOMAIN_EXPECTATIONS),
            natural_ids,
        )

        classifier = getattr(ORACLE, "classify_domain_modifiers", None)
        self.assertTrue(callable(classifier))
        if not callable(classifier):
            return
        domain_order = _domain_order()
        harness_errors: list[str] = []
        mismatches: list[str] = []
        for case_id, expected_domains in (
            NATURAL_CLIENT_DOMAIN_EXPECTATIONS.items()
        ):
            snapshot = classifier(rows[case_id]["prompt"])
            if (
                len(snapshot) != len(domain_order)
                or [item.get("skill") for item in snapshot] != domain_order
                or any(set(item) != CLASSIFIER_FIELDS for item in snapshot)
            ):
                harness_errors.append(
                    f"[{case_id}] malformed classifier snapshot={snapshot!r}"
                )
                continue
            eligible_rows = [
                item for item in snapshot if item["eligible"] is True
            ]
            if any(
                not item["evidence_ids"] or item["rejection_reasons"]
                for item in eligible_rows
            ):
                harness_errors.append(
                    f"[{case_id}] eligible rows lack closed evidence={eligible_rows!r}"
                )
            actual_domains = [
                item["skill"]
                for item in eligible_rows
                if item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if actual_domains != expected_domains:
                mismatches.append(
                    f"[{case_id}] expected client_domains={expected_domains!r}; "
                    f"actual={actual_domains!r}; "
                    f"classifier_rows={eligible_rows!r}"
                )

        keyword_only_controls = {
            "android": "Inspect the Android keyword only.",
            "ios": "Inspect the iOS keyword only.",
            "windows": "Inspect the Windows keyword only.",
            "macos": "Inspect the macOS keyword only.",
            "linux-desktop": "Inspect the Linux graphical desktop term only.",
            "cross-platform": "Inspect the Flutter framework name only.",
        }
        for label, prompt in keyword_only_controls.items():
            selected = [
                item["skill"]
                for item in classifier(prompt)
                if item["eligible"] is True
                and item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if selected:
                mismatches.append(
                    f"[keyword-only:{label}] expected client_domains=[]; "
                    f"actual={selected!r}"
                )

        if harness_errors:
            self.fail("\n".join(harness_errors))
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_neighbor_client_compound_signals_and_negative_controls(
        self,
    ) -> None:
        document = load_yaml_file(CAPABILITY_ROUTE_CASES)
        self.assertEqual({"schema_version", "cases"}, set(document))
        self.assertEqual(1, document["schema_version"])
        cases = document["cases"]
        self.assertEqual(62, len(cases))
        rows = {
            row["id"]: row
            for row in cases
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        self.assertEqual(62, len(rows))
        neighbor_ids = {
            case_id
            for case_id in rows
            if case_id.startswith("capcov-neighbor-")
        }
        self.assertEqual(
            set(NEIGHBOR_CLIENT_DOMAIN_EXPECTATIONS),
            neighbor_ids,
        )
        self.assertEqual(
            set(DOCUMENTATION_ORDER_CLIENT_DOMAIN_EXPECTATIONS),
            {
                case_id
                for case_id in rows
                if case_id.startswith("capcov-docs-order-")
            },
        )

        classifier = getattr(ORACLE, "classify_domain_modifiers", None)
        self.assertTrue(callable(classifier))
        if not callable(classifier):
            return
        documentation_only = getattr(ORACLE, "_documentation_only", None)
        self.assertTrue(callable(documentation_only))
        if not callable(documentation_only):
            return
        domain_order = _domain_order()
        harness_errors: list[str] = []
        mismatches: list[str] = []
        for case_id, expected_domains in (
            NEIGHBOR_CLIENT_DOMAIN_EXPECTATIONS.items()
        ):
            snapshot = classifier(rows[case_id]["prompt"])
            if (
                len(snapshot) != len(domain_order)
                or [item.get("skill") for item in snapshot] != domain_order
                or any(set(item) != CLASSIFIER_FIELDS for item in snapshot)
            ):
                harness_errors.append(
                    f"[{case_id}] malformed classifier snapshot={snapshot!r}"
                )
                continue
            eligible_rows = [
                item for item in snapshot if item["eligible"] is True
            ]
            if any(
                not item["evidence_ids"] or item["rejection_reasons"]
                for item in eligible_rows
            ):
                harness_errors.append(
                    f"[{case_id}] eligible rows lack closed evidence={eligible_rows!r}"
                )
            actual_domains = [
                item["skill"]
                for item in eligible_rows
                if item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if actual_domains != expected_domains:
                mismatches.append(
                    f"[{case_id}] mismatch=public-classifier; "
                    f"expected client_domains={expected_domains!r}; "
                    f"actual={actual_domains!r}; "
                    f"classifier_rows={eligible_rows!r}"
                )

        keyword_negative_controls = {
            "framework:wpf": "Inspect the WPF framework name only.",
            "framework:winui": "Inspect the WinUI framework name only.",
            "framework:swiftui": "Inspect the SwiftUI framework name only.",
            "framework:jetpack-compose": (
                "Inspect the Jetpack Compose framework name only."
            ),
            "language:kotlin": "Inspect the Kotlin language name only.",
            "language:swift": "Inspect the Swift language name only.",
            "language:csharp": "Inspect the C# language name only.",
            "language:cpp": "Inspect the C++ language name only.",
            "language:dart": "Inspect the Dart language name only.",
        }
        combined_platform_framework_negative_controls = {
            "android-jetpack-compose": (
                "Inspect the Android and Jetpack Compose documentation names "
                "only; do not implement anything and Android application "
                "behavior remains unchanged."
            ),
            "macos-swiftui": (
                "Inspect the macOS and SwiftUI documentation names only; do "
                "not implement anything and macOS application behavior "
                "remains unchanged."
            ),
            "windows-wpf": (
                "Inspect the Windows and WPF documentation names only; do not "
                "implement anything and packaged desktop application behavior "
                "remains unchanged."
            ),
            "windows-winui": (
                "Inspect the Windows and WinUI documentation names only; do "
                "not implement anything and packaged desktop application "
                "behavior remains unchanged."
            ),
        }
        for label, prompt in (
            keyword_negative_controls
            | combined_platform_framework_negative_controls
        ).items():
            selected = [
                item["skill"]
                for item in classifier(prompt)
                if item["eligible"] is True
                and item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if selected:
                mismatches.append(
                    f"[control:{label}] expected client_domains=[]; "
                    f"actual={selected!r}"
                )

        for label, prompt in (
            combined_platform_framework_negative_controls.items()
        ):
            decision = ORACLE.route(
                prompt,
                main_execution=COHORTS._test_main_execution(
                    f"t4b-neighbor-negative-control-{label}"
                ),
            )
            route_result = decision["route_result"]
            actual_route = {
                "path": decision["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            }
            if (
                actual_route["primary_skill"]
                == "installed-client-change-builder"
            ):
                mismatches.append(
                    f"[control:{label}] expected route_owner!="
                    "installed-client-change-builder; "
                    f"actual={actual_route!r}"
                )

        neutral_documentation_controls = {
            "leading-only-inspect": (
                "Only inspect ExampleUI screen documentation; behavior "
                "remains unchanged."
            ),
            "leading-only-analyze": (
                "Only analyze ExampleUI screen documentation; behavior "
                "remains unchanged."
            ),
            "leading-only-review": (
                "Only review ExampleUI screen documentation; behavior "
                "remains unchanged."
            ),
            "only-before-documentation": (
                "Inspect only ExampleUI screen documentation; behavior "
                "remains unchanged."
            ),
            "only-after-documentation": (
                "Inspect ExampleUI documentation names only; behavior "
                "remains unchanged."
            ),
        }
        for label, prompt in neutral_documentation_controls.items():
            actual = documentation_only(prompt.casefold())
            if actual is not True:
                mismatches.append(
                    f"[documentation-only:{label}] expected=True; "
                    f"actual={actual!r}"
                )

        expected_documentation_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        for case_id, expected_domains in (
            DOCUMENTATION_ORDER_CLIENT_DOMAIN_EXPECTATIONS.items()
        ):
            prompt = rows[case_id]["prompt"]
            selected = [
                item["skill"]
                for item in classifier(prompt)
                if item["eligible"] is True
                and item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if selected != expected_domains:
                mismatches.append(
                    f"[{case_id}] mismatch=public-classifier-extra-domain; "
                    f"expected client_domains={expected_domains!r}; "
                    f"actual={selected!r}"
                )
            decision = ORACLE.route(
                prompt,
                main_execution=rows[case_id]["main_execution"],
            )
            route_result = decision["route_result"]
            actual_route = {
                "path": decision["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            }
            if actual_route != expected_documentation_route:
                mismatches.append(
                    f"[{case_id}] mismatch=public-route-extra-domain; "
                    f"expected route={expected_documentation_route!r}; "
                    f"actual={actual_route!r}"
                )
            if actual_route["primary_skill"] == (
                "installed-client-change-builder"
            ):
                mismatches.append(
                    f"[{case_id}] mismatch=forbidden-installed-owner; "
                    f"actual={actual_route!r}"
                )

        material_documentation_controls = {
            "android-compose": {
                "prompt": (
                    "Analyze Android Jetpack Compose screen lifecycle "
                    "behavior and document the constraints."
                ),
                "domain": "android-platform-extension",
            },
            "android-compose-leading-only": {
                "prompt": (
                    "Only analyze Android Jetpack Compose screen lifecycle "
                    "behavior and document the constraints."
                ),
                "domain": "android-platform-extension",
            },
            "macos-swiftui": {
                "prompt": (
                    "Analyze macOS SwiftUI window lifecycle and platform "
                    "behavior, then document the constraints."
                ),
                "domain": "macos-platform-extension",
            },
            "windows-wpf": {
                "prompt": (
                    "Analyze Windows WPF window rendering and platform "
                    "behavior, then document the constraints."
                ),
                "domain": "windows-platform-extension",
            },
            "windows-winui": {
                "prompt": (
                    "Analyze Windows WinUI view rendering and platform "
                    "behavior, then document the constraints."
                ),
                "domain": "windows-platform-extension",
            },
        }
        for label, control in material_documentation_controls.items():
            expected_domain = control["domain"]
            documentation_only_result = documentation_only(
                control["prompt"].casefold()
            )
            if documentation_only_result is not False:
                mismatches.append(
                    f"[material-docs:{label}] expected "
                    "_documentation_only=False; "
                    f"actual={documentation_only_result!r}"
                )
            selected = [
                item["skill"]
                for item in classifier(control["prompt"])
                if item["eligible"] is True
                and item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if selected != [expected_domain]:
                mismatches.append(
                    f"[material-docs:{label}] expected client_domains="
                    f"{[expected_domain]!r}; actual={selected!r}"
                )
            observed = ORACLE.route_with_trace(
                control["prompt"],
                main_execution=COHORTS._test_main_execution(
                    f"t4b-material-docs-positive-{label}"
                ),
            )
            decision = observed["route_decision"]
            route_result = decision["route_result"]
            actual_route = {
                "path": decision["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            }
            expected_route = {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": [
                    expected_domain,
                    "repository-context-map",
                ],
                "review_skill": "architecture-impact-reviewer",
            }
            if actual_route != expected_route:
                mismatches.append(
                    f"[material-docs:{label}] expected route="
                    f"{expected_route!r}; actual={actual_route!r}"
                )
            if actual_route["primary_skill"] == (
                "installed-client-change-builder"
            ):
                mismatches.append(
                    f"[material-docs:{label}] forbidden installed owner; "
                    f"actual={actual_route!r}"
                )
            raw_owner_ids = [
                item["candidate_id"]
                for item in observed["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith(
                    "implementation-owner:"
                )
            ]
            if (
                "implementation-owner:installed-client-change-builder"
                in raw_owner_ids
            ):
                mismatches.append(
                    f"[material-docs:{label}] forbidden raw installed owner; "
                    f"actual={raw_owner_ids!r}"
                )
            trace = observed["winner_trace"]
            if (
                decision.get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[material-docs:{label}] expected route-once/full proof; "
                    f"route_once={decision.get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )

        positive_controls = {
            "android-client-state-payload-parser": {
                "prompt": (
                    "Implement the accepted Android installed app state "
                    "payload parser change in the client."
                ),
                "domain": "android-platform-extension",
            },
            "ios-client-state-payload-parser": {
                "prompt": (
                    "Implement the accepted iOS installed app state payload "
                    "parser change in the client."
                ),
                "domain": "ios-ipados-platform-extension",
            },
        }
        for label, control in positive_controls.items():
            expected_domain = control["domain"]
            selected = [
                item["skill"]
                for item in classifier(control["prompt"])
                if item["eligible"] is True
                and item["skill"] in CLIENT_DOMAIN_NAMES
            ]
            if selected != [expected_domain]:
                mismatches.append(
                    f"[control:{label}] expected client_domains="
                    f"{[expected_domain]!r}; actual={selected!r}"
                )
            decision = ORACLE.route(
                control["prompt"],
                main_execution=COHORTS._test_main_execution(
                    f"t4b-neighbor-positive-control-{label}"
                ),
            )
            route_result = decision["route_result"]
            actual_route = {
                "path": decision["path"],
                "profile": route_result["start_profile"],
                "primary_skill": route_result["primary_skill"],
                "layer3_skills": route_result["layer3_skills"],
                "review_skill": route_result["review_skill"],
            }
            expected_route = {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "installed-client-change-builder",
                "layer3_skills": [expected_domain],
                "review_skill": "ai-code-review-refactor",
            }
            if actual_route != expected_route:
                mismatches.append(
                    f"[control:{label}] expected route={expected_route!r}; "
                    f"actual={actual_route!r}"
                )

        if harness_errors:
            self.fail("\n".join(harness_errors))
        if mismatches:
            self.fail("\n".join(mismatches))


class DomainModifierCompositionTests(unittest.TestCase):
    def test_zero_one_and_many_composition_is_deterministic(self) -> None:
        registered = _domain_order()
        empty = ORACLE.compose_domain_extensions(
            [],
            registered_domains=registered,
        )
        self.assertEqual("selected", empty["outcome"])
        self.assertEqual([], empty["ordered_domains"])
        one = ORACLE.compose_domain_extensions(
            ["ai-product-extension"],
            registered_domains=registered,
        )
        self.assertEqual(["ai-product-extension"], one["ordered_domains"])
        expected = [
            "cross-platform-client-extension",
            "android-platform-extension",
            "ios-ipados-platform-extension",
        ]
        for candidates in (
            list(reversed(expected)),
            expected,
        ):
            with self.subTest(candidates=candidates):
                many = ORACLE.compose_domain_extensions(
                    candidates,
                    registered_domains=registered,
                )
                self.assertEqual("selected", many["outcome"])
                self.assertEqual(expected, many["ordered_domains"])

    def test_registry_order_wins_over_candidate_order_for_mixed_domains(
        self,
    ) -> None:
        registered = _domain_order()
        expected = [
            "web3-product-extension",
            "payment-trading-extension",
        ]
        for candidates in (expected, list(reversed(expected))):
            with self.subTest(candidates=candidates):
                composition = ORACLE.compose_domain_extensions(
                    candidates,
                    registered_domains=registered,
                )
                self.assertEqual(
                    expected,
                    composition["ordered_domains"],
                )

    def test_all_thirteen_domains_follow_registry_order_with_cross_exception(
        self,
    ) -> None:
        registered = _domain_order()
        expected = list(registered)
        expected.remove("cross-platform-client-extension")
        expected.insert(
            expected.index("android-platform-extension"),
            "cross-platform-client-extension",
        )
        for candidates in (registered, list(reversed(registered))):
            with self.subTest(candidates=candidates):
                composition = ORACLE.compose_domain_extensions(
                    candidates,
                    registered_domains=registered,
                    max_domains=13,
                )
                self.assertEqual(expected, composition["ordered_domains"])

    def test_invalid_compositions_fail_closed(self) -> None:
        error_type = getattr(ORACLE, "RoutingIntegrityError", None)
        self.assertTrue(isinstance(error_type, type))
        registered = _domain_order()
        invalid = (
            ["cross-platform-client-extension"],
            ["ai-product-extension", "ai-product-extension"],
            ["unknown-domain"],
            [
                "ai-product-extension",
                "bigdata-product-extension",
                "iot-embedded-extension",
                "payment-trading-extension",
            ],
        )
        for candidates in invalid:
            with self.subTest(candidates=candidates):
                with self.assertRaises(error_type):
                    ORACLE.compose_domain_extensions(
                        candidates,
                        registered_domains=registered,
                    )

    def test_unordered_registry_authority_fails_closed(self) -> None:
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            ORACLE.compose_domain_extensions(
                ["web3-product-extension"],
                registered_domains=set(_domain_order()),
            )


class DomainModifierResultValidationTests(unittest.TestCase):
    _BACKEND_PROMPT = (
        "Implement an accepted backend service behavior change with targeted tests."
    )

    def _rows(self) -> list[dict[str, object]]:
        return copy.deepcopy(
            ORACLE.classify_domain_modifiers(self._BACKEND_PROMPT)
        )

    @staticmethod
    def _eligible(
        row: dict[str, object],
        evidence_id: str,
    ) -> None:
        row["eligible"] = True
        row["evidence_ids"] = [evidence_id]
        row["rejection_reasons"] = []

    def _route_with_rows(
        self,
        rows: list[dict[str, object]],
    ) -> dict[str, object]:
        with patch.object(
            ORACLE,
            "classify_domain_modifiers",
            return_value=rows,
        ):
            decision = ORACLE.route(
                self._BACKEND_PROMPT,
                main_execution=COHORTS._test_main_execution(
                    "t2g-domain-row-routing"
                ),
            )
            return {
                "path": decision["path"],
                "profile": decision["route_result"]["start_profile"],
                "primary_skill": decision["route_result"]["primary_skill"],
                "layer3_skills": decision["route_result"]["layer3_skills"],
                "review_skill": decision["route_result"]["review_skill"],
            }

    def test_valid_rejected_rows_are_ignored_and_reversed_snapshot_is_stable(
        self,
    ) -> None:
        rows = self._rows()
        self.assertTrue(
            all(
                row["eligible"] is False
                and row["evidence_ids"] == []
                and row["rejection_reasons"]
                for row in rows
            )
        )
        forward = self._route_with_rows(rows)
        reverse = self._route_with_rows(list(reversed(rows)))
        self.assertEqual(forward, reverse)
        self.assertEqual([], forward["layer3_skills"])

    def test_malformed_or_stale_candidate_snapshots_fail_closed(self) -> None:
        mutations = []

        unknown = self._rows()
        unknown[0]["skill"] = "unknown-domain-extension"
        mutations.append(("unknown-skill", unknown))

        duplicate = self._rows()
        duplicate[-1] = copy.deepcopy(duplicate[0])
        mutations.append(("duplicate-skill", duplicate))

        missing = self._rows()
        missing.pop()
        mutations.append(("missing-skill", missing))

        forbidden = self._rows()
        forbidden[0]["owner"] = "backend-change-builder"
        mutations.append(("forbidden-field", forbidden))

        empty_evidence = self._rows()
        self._eligible(empty_evidence[4], "")
        mutations.append(("empty-evidence", empty_evidence))

        stale_evidence = self._rows()
        self._eligible(
            stale_evidence[4],
            "domain-family:retired-ledger-authority",
        )
        mutations.append(("stale-evidence", stale_evidence))

        duplicate_evidence = self._rows()
        self._eligible(
            duplicate_evidence[4],
            "domain-family:money-ledger-settlement",
        )
        duplicate_evidence[4]["evidence_ids"] = [
            "domain-family:money-ledger-settlement",
            "domain-family:money-ledger-settlement",
        ]
        mutations.append(("duplicate-evidence", duplicate_evidence))

        stale_rejection = self._rows()
        stale_rejection[0]["rejection_reasons"] = ["retired-reason"]
        mutations.append(("stale-rejection", stale_rejection))

        for label, rows in mutations:
            with self.subTest(label=label):
                with self.assertRaises(
                    ORACLE.RoutingIntegrityError
                ) as caught:
                    self._route_with_rows(rows)
                self.assertEqual(
                    "routing-integrity-failure",
                    caught.exception.code,
                )

    def test_eligible_unauthorized_owner_reciprocity_fails_closed(self) -> None:
        task_id = "t2g-domain-row-routing"
        rows = self._rows()
        ai_row = next(
            row for row in rows if row["skill"] == "ai-product-extension"
        )
        self._eligible(
            ai_row,
            "domain-family:agent-model-authority",
        )
        with patch.object(
            ORACLE,
            "classify_domain_modifiers",
            return_value=rows,
        ):
            observed = ORACLE.route_with_trace(
                "Select regression tests and validate final changed paths "
                "where a model decision has delegated authority.",
                main_execution=COHORTS._test_main_execution(task_id),
            )
        trace = observed["winner_trace"]
        provisional = next(
            candidate
            for candidate in trace["raw_candidates"]
            if candidate["candidate_id"]
            == "implementation-owner:quality-test-gate"
        )
        expected_markers = [
            "domain-layer3-incompatible:ai-product-extension:"
            "professional-layer3",
            "domain-layer3-incompatible:ai-product-extension:reciprocity",
        ]
        self.assertEqual(
            expected_markers,
            [
                evidence
                for evidence in provisional["evidence"]
                if evidence.startswith(
                    COHORTS.ACTIVATION_V2_139C_MARKER_PREFIX
                )
            ],
        )
        selected = trace["selected_candidate"]
        self.assertEqual(
            {
                "candidate_id": "route-contract-conflict",
                "candidate_type": "derived-conflict",
                "reason": COHORTS.ACTIVATION_V2_139C_CONFLICT_REASON,
                "source_candidate_ids": [
                    "implementation-owner:quality-test-gate"
                ],
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            },
            {
                field: selected[field]
                for field in (
                    "candidate_id",
                    "candidate_type",
                    "reason",
                    "source_candidate_ids",
                    *ORACLE.ROUTE_CONTRACT_FIELDS,
                )
            },
        )
        self.assertEqual(
            {
                field: provisional[field]
                for field in COHORTS.ACTIVATION_V2_139C_PRIVATE_FIELDS
            },
            {
                field: selected[field]
                for field in COHORTS.ACTIVATION_V2_139C_PRIVATE_FIELDS
            },
        )
        self.assertEqual(
            [
                {
                    "id": "route-evidence-1",
                    "kind": "routing_candidate",
                    "task_id": task_id,
                    "source_anchor": (
                        COHORTS.ACTIVATION_V2_139C_CONFLICT_REASON
                    ),
                }
            ],
            observed["route_decision"]["selection_evidence"][
                "task_evidence"
            ],
        )

    def test_eligible_role_mismatch_fails_closed(self) -> None:
        rows = self._rows()
        payment = next(
            row
            for row in rows
            if row["skill"] == "payment-trading-extension"
        )
        self._eligible(
            payment,
            "domain-family:money-ledger-settlement",
        )
        authority = VALIDATION.domain_modifier_routing_authority(
            _domain_registry(),
            _professional_registry(),
        )
        incompatible = copy.deepcopy(authority)
        incompatible["domains_by_name"]["payment-trading-extension"][
            "role_support"
        ] = ["analysis-agent"]
        with patch.object(
            ORACLE,
            "domain_modifier_routing_authority",
            return_value=incompatible,
        ):
            with self.assertRaises(ORACLE.RoutingIntegrityError):
                self._route_with_rows(rows)

    def test_cross_platform_without_concrete_target_fails_closed(self) -> None:
        rows = self._rows()
        cross = next(
            row
            for row in rows
            if row["skill"] == "cross-platform-client-extension"
        )
        self._eligible(
            cross,
            "domain-family:shared-target-ownership",
        )
        with self.assertRaises(ORACLE.RoutingIntegrityError):
            self._route_with_rows(rows)


class DomainModifierRouteTests(unittest.TestCase):
    def test_android_registry_contract_preserves_general_and_accessibility_obligations(
        self,
    ) -> None:
        android = next(
            row
            for row in _domain_registry()["domain_skills"]
            if row["name"] == "android-platform-extension"
        )
        required_inputs = android["required_inputs"]
        output_contract = android["output_contract"]
        escalation_signals = android["escalation_signals"]
        self.assertEqual(1, len(required_inputs))
        self.assertEqual(1, len(output_contract))
        self.assertEqual(1, len(escalation_signals))

        for phrase in (
            "API/SDK range",
            "variant",
            "lifecycle/component owner",
            "manifest/permission",
            "storage/package/device evidence",
            "when accessibility changes",
            "representation/input/scaling delta",
            "required accessibility evidence",
        ):
            self.assertIn(phrase, required_inputs[0])
        for phrase in (
            "platform owner",
            "API/SDK/form-factor scope",
            "normal/failure behavior",
            "accessibility delta when applicable",
            "artifact/device validation",
            "proof limits",
            "residual risk",
        ):
            self.assertIn(phrase, output_contract[0])
        for phrase in (
            "SDK/variant",
            "identity",
            "permission",
            "state owner",
            "data recovery",
            "representative device evidence",
            "for an accessibility change",
            "representation/input/scaling",
            "required accessibility evidence",
        ):
            self.assertIn(phrase, escalation_signals[0])

    def test_android_accessibility_reference_closes_lifecycle_restoration(
        self,
    ) -> None:
        reference = (
            ROOT
            / "src/domain-extensions/android-platform-extension/references/"
            "accessibility-representation-input-and-scaling.md"
        ).read_text(encoding="utf-8")
        required_phrases = (
            "Foundation focus-restoration and one-time-announcement rules",
            "configuration recreation, process-death restoration, and "
            "navigation return",
            "still-valid continuing-task target",
            "stale asynchronous completions and repeated effects",
            "pane and live-region behavior",
            "invalid prior accessibility-focus target",
            "do not emit the pane or live-region announcement twice",
        )
        self.assertEqual(
            [],
            [phrase for phrase in required_phrases if phrase not in reference],
        )

    def test_client_domain_actual_diff_review_reciprocity(self) -> None:
        cases = {
            "android-accessibility": (
                "Review the actual diff for an Android application "
                "accessibility behavior change affecting TalkBack and Switch "
                "Access.",
                [
                    "android-platform-extension",
                    "accessibility-inclusive-design",
                ],
            ),
            "android-lifecycle": (
                "Review the actual diff for an Android application lifecycle "
                "change.",
                ["android-platform-extension", "code-review"],
            ),
            "ios-lifecycle": (
                "Review the actual diff for an iOS application lifecycle change.",
                ["ios-ipados-platform-extension", "code-review"],
            ),
            "windows-identity": (
                "Review the actual diff for a Windows packaged desktop "
                "application identity change.",
                ["windows-platform-extension", "code-review"],
            ),
            "macos-window": (
                "Review the actual diff for a macOS installed application "
                "window lifecycle change.",
                ["macos-platform-extension", "code-review"],
            ),
            "linux-session": (
                "Review the actual diff for a Linux graphical desktop session "
                "window change.",
                ["linux-desktop-platform-extension", "code-review"],
            ),
            "flutter-android": (
                "Review the actual diff for a Flutter shared installed client "
                "change targeting Android.",
                [
                    "cross-platform-client-extension",
                    "android-platform-extension",
                    "code-review",
                ],
            ),
        }
        for label, (prompt, layer3) in cases.items():
            with self.subTest(label=label):
                observed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=COHORTS._test_main_execution(
                        f"android-accessibility-review-{label}"
                    ),
                )
                self.assertEqual(
                    {
                        "path": "direct",
                        "profile": "review-agent",
                        "primary_skill": "ai-code-review-refactor",
                        "layer3_skills": layer3,
                        "review_skill": "ai-code-review-refactor",
                    },
                    COHORTS._projected_route(observed),
                )
        android = ORACLE.domain_route_families(cases["android-accessibility"][0])
        self.assertIn(
            (
                "android-platform-extension",
                "accessibility-platform-authority",
            ),
            android,
        )

    def test_domain_object_analysis_candidate_uses_clause_local_action_polarity(
        self,
    ) -> None:
        analysis = (
            "Analyze a Windows MSIX protocol-handler change whose application identity "
            "controls registration; identify domain object identity and writer authority"
        )
        for clause in (
            "before implementation",
            "without implementation",
            "do not implement it",
            "implementation is out of scope",
        ):
            observed = ORACLE.route_with_trace(
                f"{analysis}; {clause}.",
                main_execution=COHORTS._test_main_execution(
                    f"t3-edge-action-polarity-{clause}"
                ),
            )
            with self.subTest(clause=clause):
                self.assertEqual(
                    "domain-object-analysis",
                    observed["winner_trace"]["selected_candidate"][
                        "candidate_id"
                    ],
                )
                self.assertFalse(
                    any(
                        item["candidate_id"].startswith(
                            "implementation-owner:"
                        )
                        for item in observed["winner_trace"]["raw_candidates"]
                    )
                )

        implementation_suffix = (
            "an accepted Windows packaged desktop application protocol-handler change "
            "whose application identity controls registration"
        )
        for prefix in (
            "Implement",
            "For the accepted task, implement",
            "We must implement",
            "Please implement",
            "The accepted task is to implement",
        ):
            implementation = f"{prefix} {implementation_suffix}"
            for prompt in (
                f"{analysis}. {implementation}.",
                f"{implementation}. {analysis}.",
            ):
                mixed = ORACLE.route_with_trace(
                    prompt,
                    main_execution=COHORTS._test_main_execution(
                        f"t3-edge-action-polarity-mixed-{prefix}"
                    ),
                )
                with self.subTest(prompt=prompt):
                    self.assertEqual(
                        "implementation-owner:installed-client-change-builder",
                        mixed["winner_trace"]["selected_candidate"][
                            "candidate_id"
                        ],
                    )

        contradictory = ORACLE.route_with_trace(
            f"{analysis}. We must implement {implementation_suffix} despite an "
            "instruction that we must not implement it.",
            main_execution=COHORTS._test_main_execution(
                "t3-edge-action-polarity-contradictory"
            ),
        )
        self.assertEqual(
            "repository-first-default",
            contradictory["winner_trace"]["selected_candidate"][
                "candidate_id"
            ],
        )

    def test_candidate_inventory_matches_canonical_with_controls_preserved(
        self,
    ) -> None:
        rule_ids = COHORTS._candidate_rule_ids()
        self.assertEqual(
            REVIEW_RISKS.CANONICAL_CANDIDATE_RULE_IDS,
            set(rule_ids),
        )
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        self.assertTrue(REMOVED_DIRECT_IDS.isdisjoint(rule_ids))
        self.assertTrue(COHORTS.SPLIT_GUARD_RULE_IDS.issubset(rule_ids))
        self.assertTrue(
            REVIEW_RISKS.SPLIT_RETAINED_RULE_IDS.issubset(rule_ids)
        )
        self.assertTrue(REVIEW_RISKS.KEEP_RULE_IDS.issubset(rule_ids))

    def test_domain_does_not_suppress_owner_and_is_source_order_invariant(
        self,
    ) -> None:
        domain_clause = "Rust FFI ownership behavior changes"
        base_clause = "Implement an accepted backend service behavior change"
        observed = [
            ORACLE.route_with_trace(
                f"{left}; {right}.",
                main_execution=COHORTS._test_main_execution(
                    f"t2g-domain-owner-{index}"
                ),
            )
            for index, (left, right) in enumerate((
                (base_clause, domain_clause),
                (domain_clause, base_clause),
            ))
        ]
        for result in observed:
            route = COHORTS._projected_route(result)
            self.assertEqual(COMPATIBILITY_ROUTE_FIELDS, set(route))
            self.assertEqual("direct", route["path"])
            self.assertEqual("task-agent", route["profile"])
            self.assertEqual("backend-change-builder", route["primary_skill"])
            self.assertEqual(
                ["low-level-systems-extension"],
                route["layer3_skills"],
            )
            self.assertEqual(
                "ai-code-review-refactor",
                route["review_skill"],
            )
        self.assertEqual(
            COHORTS._projected_route(observed[0]),
            COHORTS._projected_route(observed[1]),
        )

        android_change = (
            "Implement an accepted Android installed application lifecycle change"
        )
        windows_service_change = (
            "Implement an accepted Windows service lifecycle change in C# "
            "with async disposal and CancellationToken behavior"
        )
        cases = {
            "android:tail": {
                "prompt": f"{android_change} with no iOS behavior.",
                "families": ["installed-client"],
                "domains": [
                    (
                        "android-platform-extension",
                        "platform-lifecycle-authority",
                    )
                ],
                "owners": [
                    "implementation-owner:installed-client-change-builder"
                ],
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "installed-client-change-builder",
                    "layer3_skills": ["android-platform-extension"],
                    "review_skill": "ai-code-review-refactor",
                },
            },
            "android:inline": {
                "prompt": android_change.replace(
                    "Implement ",
                    "Implement with no iOS behavior ",
                    1,
                )
                + ".",
                "families": ["installed-client"],
                "domains": [
                    (
                        "android-platform-extension",
                        "platform-lifecycle-authority",
                    )
                ],
                "owners": [
                    "implementation-owner:installed-client-change-builder"
                ],
                "route": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "installed-client-change-builder",
                    "layer3_skills": ["android-platform-extension"],
                    "review_skill": "ai-code-review-refactor",
                },
            },
            "windows-service:tail": {
                "prompt": f"{windows_service_change} with no iOS behavior.",
                "families": ["backend"],
                "domains": [
                    (
                        "windows-platform-extension",
                        "service-lifecycle-authority",
                    )
                ],
                "owners": ["implementation-owner:backend-change-builder"],
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
            "windows-service:inline": {
                "prompt": windows_service_change.replace(
                    "Implement ",
                    "Implement with no iOS behavior ",
                    1,
                )
                + ".",
                "families": ["backend"],
                "domains": [
                    (
                        "windows-platform-extension",
                        "service-lifecycle-authority",
                    )
                ],
                "owners": ["implementation-owner:backend-change-builder"],
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
            "ordinary-backend:no-windows": {
                "prompt": (
                    "Implement an accepted backend service endpoint change "
                    "with no Windows behavior."
                ),
                "families": ["backend"],
                "domains": [],
                "owners": ["implementation-owner:backend-change-builder"],
                "route_core": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "backend-change-builder",
                },
            },
            "ordinary-frontend:no-windows": {
                "prompt": (
                    "Implement an accepted frontend component state change "
                    "with no Windows behavior."
                ),
                "families": ["frontend"],
                "domains": [],
                "owners": ["implementation-owner:frontend-change-builder"],
                "route_core": {
                    "path": "direct",
                    "profile": "task-agent",
                    "primary_skill": "frontend-change-builder",
                },
            },
            "whole-android:remains-unchanged": {
                "prompt": (
                    "Android installed application lifecycle remains unchanged."
                ),
                "families": [],
                "domains": [],
                "owners": [],
            },
            "whole-windows:do-not-change": {
                "prompt": (
                    "Do not change Windows packaged desktop app window state "
                    "behavior."
                ),
                "families": [],
                "domains": [],
                "owners": [],
            },
        }
        mismatches: list[str] = []
        executed: list[str] = []
        for label, case in cases.items():
            executed.append(label)
            prompt = case["prompt"]
            actual_families = [
                row["routing_family"]
                for row in ORACLE.classify_professional_families(prompt)
            ]
            if actual_families != case["families"]:
                mismatches.append(
                    f"[{label}] mismatch=professional-family; "
                    f"expected={case['families']!r}; "
                    f"actual={actual_families!r}"
                )
            actual_domains = ORACLE.domain_route_families(prompt)
            if actual_domains != case["domains"]:
                mismatches.append(
                    f"[{label}] mismatch=domain-family; "
                    f"expected={case['domains']!r}; "
                    f"actual={actual_domains!r}"
                )
            result = ORACLE.route_with_trace(
                prompt,
                main_execution=COHORTS._test_main_execution(
                    f"red59-{label}"
                ),
            )
            owner_ids = [
                item["candidate_id"]
                for item in result["winner_trace"]["raw_candidates"]
                if item["candidate_id"].startswith("implementation-owner:")
            ]
            if owner_ids != case["owners"]:
                mismatches.append(
                    f"[{label}] mismatch=raw-owner; "
                    f"expected={case['owners']!r}; actual={owner_ids!r}"
                )
            actual_route = COHORTS._projected_route(result)
            if "route" in case and actual_route != case["route"]:
                mismatches.append(
                    f"[{label}] mismatch=route-envelope; "
                    f"expected={case['route']!r}; actual={actual_route!r}"
                )
            if "route_core" in case:
                route_core = {
                    key: actual_route[key]
                    for key in ("path", "profile", "primary_skill")
                }
                if route_core != case["route_core"]:
                    mismatches.append(
                        f"[{label}] mismatch=route-core; "
                        f"expected={case['route_core']!r}; "
                        f"actual={route_core!r}"
                    )
            trace = result["winner_trace"]
            if (
                result["route_decision"].get("route_once") is not True
                or trace.get("route_once") != "proven"
                or trace.get("candidate_coverage") != "full"
            ):
                mismatches.append(
                    f"[{label}] mismatch=route-proof; "
                    f"route_once="
                    f"{result['route_decision'].get('route_once')!r}; "
                    f"trace_route_once={trace.get('route_once')!r}; "
                    f"coverage={trace.get('candidate_coverage')!r}"
                )
        if executed != list(cases):
            mismatches.append(
                "[platform-domain-anti] mismatch=case-execution; "
                f"expected={list(cases)!r}; actual={executed!r}"
            )
        if mismatches:
            self.fail("\n".join(mismatches))

    def test_t2c_and_t2d_precedence_is_domain_order_invariant(self) -> None:
        security = (
            "Review the actual diff where tenant authorization permission "
            "bypass may cross a trust boundary"
        )
        ai = "a model decision has delegated authority"
        reviewed = [
            COHORTS._projected_route(
                ORACLE.route_with_trace(
                    f"{left}; {right}.",
                    main_execution=COHORTS._test_main_execution(
                        f"t2g-domain-review-{index}"
                    ),
                )
            )
            for index, (left, right) in enumerate(
                ((security, ai), (ai, security))
            )
        ]
        self.assertEqual(reviewed[0], reviewed[1])
        self.assertEqual("security-privacy-gate", reviewed[0]["primary_skill"])
        self.assertEqual(
            [
                "ai-product-extension",
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            reviewed[0]["layer3_skills"],
        )

        backend = "Implement an accepted backend service behavior change"
        installed = "an accepted Android application lifecycle change"
        expected_domains = ["android-platform-extension"]
        expected_owners = [
            "backend-change-builder",
            "installed-client-change-builder",
        ]
        expected_route = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
        }
        mixed_errors: list[str] = []
        for order, left, right in (
            ("backend-first", backend, installed),
            ("installed-first", installed, backend),
        ):
            prompt = f"{left} and {right}."
            observed = ORACLE.route_with_trace(
                prompt,
                main_execution=COHORTS._test_main_execution(
                    f"t2g-domain-conflict-{order}"
                ),
            )
            actual_domains = [
                row["skill"]
                for row in ORACLE.classify_domain_modifiers(prompt)
                if row["eligible"] is True
            ]
            if actual_domains != expected_domains:
                mixed_errors.append(
                    f"[mixed-owner:{order}:domains] expected="
                    f"{expected_domains!r}; actual={actual_domains!r}"
                )
            raw_owners = sorted(
                candidate["primary_skill"]
                for candidate in observed["winner_trace"]["raw_candidates"]
                if candidate.get("candidate_type")
                == "automatic-implementation-owner"
            )
            if raw_owners != expected_owners:
                mixed_errors.append(
                    f"[mixed-owner:{order}:raw-owners] expected="
                    f"{expected_owners!r}; actual={raw_owners!r}"
                )
            selected_id = observed["winner_trace"][
                "selected_candidate"
            ]["candidate_id"]
            if selected_id != "implementation-owner-conflict":
                mixed_errors.append(
                    f"[mixed-owner:{order}:winner] expected="
                    "'implementation-owner-conflict'; "
                    f"actual={selected_id!r}"
                )
            actual_route = COHORTS._projected_route(observed)
            if actual_route != expected_route:
                mixed_errors.append(
                    f"[mixed-owner:{order}:envelope] expected="
                    f"{expected_route!r}; actual={actual_route!r}"
                )
            decision_route_once = observed["route_decision"]["route_once"]
            trace_route_once = observed["winner_trace"]["route_once"]
            candidate_coverage = observed["winner_trace"][
                "candidate_coverage"
            ]
            if (
                decision_route_once is not True
                or trace_route_once != "proven"
                or candidate_coverage != "full"
            ):
                mixed_errors.append(
                    f"[mixed-owner:{order}:route-once] expected="
                    "(decision=True, trace='proven', coverage='full'); "
                    f"actual={(decision_route_once, trace_route_once, candidate_coverage)!r}"
                )
        if mixed_errors:
            self.fail("\n".join(mixed_errors))

    def test_unknown_target_stays_t2b_analyzed_without_guessed_domain(
        self,
    ) -> None:
        observed = ORACLE.route_with_trace(
            "Prepare a Flutter installed-client implementation before editing; "
            "target platforms are unknown.",
            main_execution=COHORTS._test_main_execution(
                "t2g-domain-unknown-target"
            ),
        )
        route = COHORTS._projected_route(observed)
        self.assertEqual("analyzed", route["path"])
        self.assertEqual(
            "engineering-change-analysis",
            route["primary_skill"],
        )
        self.assertEqual(
            ["repository-context-map"],
            route["layer3_skills"],
        )
        self.assertEqual([], _eligible_skills(
            "Flutter installed-client; target platforms are unknown."
        ))

    def test_total_layer3_budget_is_fail_closed_without_truncation(self) -> None:
        error_type = getattr(ORACLE, "RoutingIntegrityError", None)
        self.assertTrue(isinstance(error_type, type))
        accepted = COHORTS._projected_route(
            ORACLE.route_with_trace(
                "Review the actual diff where tenant authorization permission "
                "bypass may cross a trust boundary; a model decision has "
                "delegated authority.",
                main_execution=COHORTS._test_main_execution(
                    "t2g-domain-budget-accepted"
                ),
            )
        )
        self.assertEqual(3, len(accepted["layer3_skills"]))
        with self.assertRaises(error_type):
            ORACLE.route_with_trace(
                "Review regression tests where tenant authorization permission "
                "bypass may cross a trust boundary; a model decision has "
                "delegated authority.",
                main_execution=COHORTS._test_main_execution(
                    "t2g-domain-budget-overflow"
                ),
            )

    def test_route_impl_has_no_domain_suppression_gate(self) -> None:
        tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
        route_impl = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_route_impl"
        )
        source = ast.get_source_segment(
            ORACLE_PATH.read_text(encoding="utf-8"),
            route_impl,
        )
        self.assertIsNotNone(source)
        self.assertNotIn(
            "if not domain_route_families",
            source,
        )
        self.assertNotIn(
            "backend_subject and not domain_route_families",
            source,
        )


class DomainModifierCorpusContractTests(unittest.TestCase):
    def test_corpus_counts_remain_exact(self) -> None:
        self.assertEqual(
            233,
            len(load_yaml_file(ROOT / "evals/routing/cases.yaml")["cases"]),
        )
        self.assertEqual(
            62,
            len(
                load_yaml_file(
                    ROOT / "evals/routing/capability-coverage-cases.yaml"
                )["cases"]
            ),
        )
        admission_cases = load_yaml_file(
            ROOT / "evals/capability-coverage/admission-cases.yaml"
        )["cases"]
        expected_domain_combinations = {
            combination
            for combination in (
                CAPABILITY_COVERAGE.EXPECTED_ADMISSION_COMBINATIONS
            )
            if combination[0] == "domain"
        }
        domain_cases = [
            case
            for case in admission_cases
            if case["layer"] == "domain"
        ]
        domain_ids = [case["id"] for case in domain_cases]
        domain_combinations = [
            (case["layer"], case["skill"], case["case_kind"])
            for case in domain_cases
        ]
        self.assertEqual(
            len(domain_ids),
            len(set(domain_ids)),
        )
        self.assertEqual(
            len(domain_combinations),
            len(set(domain_combinations)),
        )
        self.assertEqual(
            expected_domain_combinations,
            set(domain_combinations),
        )
        self.assertEqual(
            len(expected_domain_combinations),
            len(domain_cases),
        )


if __name__ == "__main__":
    unittest.main()
