from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-professional-routing-coverage.py"
ROUTE_SCRIPT = ROOT / "scripts/eval-routing.py"


def _l4_main_execution_yaml(task_id: str) -> str:
    return (
        "    main_execution:\n"
        "      producer: main-control-agent\n"
        f"      task_id: {task_id}\n"
        "      execution_level: L4\n"
        "      level_basis:\n"
        "        trigger_evaluations:\n"
        "          - id: public-api-event-schema-compatibility\n"
        "            status: matched\n"
        "            evidence_kind: analysis_handoff\n"
        f"            source_anchor: task:{task_id}:routing-api\n"
        "            plausible_critical: false\n"
        "        l2_eligibility: []\n"
        "        obligations: [high-risk pre-implementation evidence]\n"
        "        unresolved: []\n"
        "        edit_status: allowed\n"
    )


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "validate_professional_routing_coverage_contract",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_route_module():
    spec = importlib.util.spec_from_file_location(
        "eval_routing_negative_contract",
        ROUTE_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProfessionalRoutingNegativeCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.route_module = _load_route_module()
        cls.professional = {
            "primary-skill": {
                "task_routable": True,
                "role_support": ["task-agent"],
                "layer3_candidates": [],
            },
            "review-skill": {
                "task_routable": True,
                "role_support": ["review-agent"],
                "layer3_candidates": [],
            },
            "excluded-skill": {
                "task_routable": True,
                "role_support": ["task-agent", "review-agent"],
                "layer3_candidates": [],
            },
        }

    def _raw(self, excluded: list[str]) -> dict:
        return {
            "id": "negative-route",
            "excluded_skills": excluded,
            "actual": {
                "profile": "task-agent",
                "path": "direct",
                "primary_skill": "primary-skill",
                "layer3_skills": [],
                "review_skill": "review-skill",
            },
            "passed": True,
            "errors": [],
            "domain_family": None,
            "domain_anti": None,
        }

    def test_valid_negative_route_is_preserved(self) -> None:
        result = self.module._case(
            self._raw(["excluded-skill"]),
            self.professional,
            {},
        )
        self.assertEqual([], result.errors)
        self.assertEqual(["excluded-skill"], result.excluded_skills)

    def test_domain_positive_and_negative_fixture_counts_are_required(self) -> None:
        domains = set(self.module._canonical_domain_specs())
        positive = {name: 1 for name in domains}
        negative = {name: 1 for name in domains}
        positive["web3-product-extension"] = 0
        negative["ai-product-extension"] = 0
        errors = self.module._domain_coverage_errors(
            domains,
            positive,
            negative,
        )
        self.assertEqual(
            [
                "Domain Skill 'ai-product-extension' has no negative anti-route fixture",
                "Domain Skill 'web3-product-extension' has no positive Layer 3 routing fixture",
            ],
            errors,
        )
        self.assertEqual(
            [],
            self.module._domain_coverage_errors(
                domains,
                {name: 1 for name in domains},
                {name: 1 for name in domains},
            ),
        )

    def test_combined_family_transition_contract_is_narrow_and_evidence_bound(
        self,
    ) -> None:
        prompt = (
            "Analyze and migrate a cloud control plane source change where "
            "cloud account authority controls IAM."
        )
        family_evidence = "family:cloud-account-authority:canonical"
        transition_evidence = "transition:cloud-account-authority"
        base = {
            "domain_family": {
                "domain": "cloud-platform-extension",
                "family": "cloud-account-authority",
                "variant": "canonical",
                "evidence_id": family_evidence,
            },
            "domain_transition": {
                "domain": "cloud-platform-extension",
                "family": "cloud-account-authority",
                "evidence_id": transition_evidence,
            },
        }

        def errors_for(
            case: dict[str, object],
            *,
            excluded: list[str] | None = None,
        ) -> list[str]:
            errors: list[str] = []
            self.route_module._domain_metadata(
                case,
                "combined-domain-contract",
                prompt,
                {
                    "layer3_skills": [
                        "cloud-platform-extension",
                        "macos-platform-extension",
                    ]
                },
                set(),
                [] if excluded is None else excluded,
                errors,
            )
            return errors

        self.assertEqual([], errors_for(base))

        cross_domain = {
            **base,
            "domain_transition": {
                "domain": "macos-platform-extension",
                "family": "platform-lifecycle-authority",
                "evidence_id": transition_evidence,
            },
        }
        self.assertTrue(
            any("same Domain and family" in error for error in errors_for(cross_domain))
        )

        mismatched_family = {
            "domain_family": {
                "domain": "windows-platform-extension",
                "family": "service-lifecycle-authority",
                "variant": "canonical",
                "evidence_id": "family:windows-service:canonical",
            },
            "domain_transition": {
                "domain": "windows-platform-extension",
                "family": "application-identity-authority",
                "evidence_id": "transition:windows-application-identity",
            },
        }
        self.assertTrue(
            any(
                "same Domain and family" in error
                for error in errors_for(mismatched_family)
            )
        )

        duplicate_evidence = {
            **base,
            "domain_transition": {
                **base["domain_transition"],
                "evidence_id": family_evidence,
            },
        }
        self.assertTrue(
            any(
                "distinct evidence_id" in error
                for error in errors_for(duplicate_evidence)
            )
        )

        contradiction = {
            **base,
            "domain_anti": "cloud-platform-extension",
            "domain_anti_variant": "unchanged-paraphrase",
        }
        self.assertTrue(
            any(
                "cannot combine material positive and unchanged evidence" in error
                for error in errors_for(
                    contradiction,
                    excluded=["cloud-platform-extension"],
                )
            )
        )

    def test_family_coverage_requires_actual_canonical_and_paraphrase_routes(self) -> None:
        professional, layer3, domains = self.module._registries()
        routing = self.route_module.evaluate_routes()
        results = [
            self.module._case(row, professional, layer3)
            for row in routing["results"]
        ]
        family_coverage = self.module._domain_family_coverage(results, domains)
        self.assertEqual(21, len(family_coverage))
        expected_family_case_ids = {
            ("ai-product-extension", "agent-model-authority"): {
                "canonical": ["ai-agent-tool-authority"],
                "paraphrase": ["ai-model-decision-paraphrase"],
            },
            ("ai-product-extension", "retrieval-data"): {
                "canonical": ["ai-rag-tool-authority"],
                "paraphrase": [
                    "ai-rag-http-contrast-clause",
                    "ai-retrieval-permission-paraphrase",
                ],
            },
            ("android-platform-extension", "accessibility-platform-authority"): {
                "canonical": ["android-accessibility-platform-authority"],
                "paraphrase": [
                    "android-accessibility-compose-focus-paraphrase"
                ],
            },
            ("bigdata-product-extension", "distributed-batch-schema"): {
                "canonical": ["bigdata-distributed-backfill-schema"],
                "paraphrase": ["bigdata-lake-reprocessing-paraphrase"],
            },
            ("bigdata-product-extension", "stream-cdc-replay"): {
                "canonical": ["bigdata-cdc-stream-replay"],
                "paraphrase": ["bigdata-stream-checkpoint-paraphrase"],
            },
            ("android-platform-extension", "platform-lifecycle-authority"): {
                "canonical": ["mobile-native-lifecycle-permission"],
                "paraphrase": ["mobile-android-permission-paraphrase"],
            },
            ("cloud-platform-extension", "cloud-account-authority"): {
                "canonical": ["structure-owner-internal-backend-placement"],
                "paraphrase": ["structure-real-pattern-force"],
            },
            ("cross-platform-client-extension", "shared-target-ownership"): {
                "canonical": ["unknown-owner"],
                "paraphrase": ["source-backed-question"],
            },
            ("ios-ipados-platform-extension", "platform-lifecycle-authority"): {
                "canonical": ["mobile-offline-deeplink"],
                "paraphrase": ["mobile-store-upgrade-paraphrase"],
            },
            ("iot-embedded-extension", "device-physical-runtime"): {
                "canonical": ["iot-device-physical-runtime"],
                "paraphrase": ["iot-edge-provisioning-paraphrase"],
            },
            ("iot-embedded-extension", "firmware-update-recovery"): {
                "canonical": ["iot-firmware-actuator-rollout"],
                "paraphrase": ["iot-firmware-brownout-paraphrase"],
            },
            ("low-level-systems-extension", "abi-ffi-memory"): {
                "canonical": ["low-level-ffi-ownership"],
                "paraphrase": ["low-level-native-memory-paraphrase"],
            },
            ("low-level-systems-extension", "kernel-realtime-concurrency"): {
                "canonical": ["low-level-kernel-driver"],
                "paraphrase": ["low-level-realtime-paraphrase"],
            },
            ("linux-desktop-platform-extension", "desktop-session-authority"): {
                "canonical": ["multi-task-plan"],
                "paraphrase": ["structure-unresolved-placement-is-not-refactoring"],
            },
            ("macos-platform-extension", "platform-lifecycle-authority"): {
                "canonical": ["structure-generated-authority-unknown"],
                "paraphrase": ["structure-fixed-placement-refactor-analysis"],
            },
            ("payment-trading-extension", "money-ledger-settlement"): {
                "canonical": ["payment-security"],
                "paraphrase": [
                    "payment-ledger-settlement-paraphrase",
                    "payment-wallet-custody-accounting-conflict",
                ],
            },
            ("payment-trading-extension", "trading-order-execution"): {
                "canonical": ["payment-trading-execution"],
                "paraphrase": ["payment-venue-order-paraphrase"],
            },
            ("web3-product-extension", "chain-custody-finality"): {
                "canonical": ["web3-chain-custody-finality"],
                "paraphrase": ["web3-wallet-signing-paraphrase"],
            },
            ("web3-product-extension", "contract-cross-chain"): {
                "canonical": ["web3-chain-contract-finality"],
                "paraphrase": ["web3-bridge-proof-paraphrase"],
            },
            ("windows-platform-extension", "application-identity-authority"): {
                "canonical": ["structure-minimal-backend"],
                "paraphrase": ["structure-object-classification-method-placement"],
            },
            ("windows-platform-extension", "service-lifecycle-authority"): {
                "canonical": ["structure-ef-mapping-domain-facts-unchanged"],
                "paraphrase": [
                    "structure-deliberate-separate-owner-implementations"
                ],
            },
        }
        self.assertEqual(
            expected_family_case_ids,
            {
                (row["domain"], row["family"]): row["case_ids_by_variant"]
                for row in family_coverage
            },
        )
        for row in family_coverage:
            with self.subTest(domain=row["domain"], family=row["family"]):
                self.assertGreaterEqual(row["passing_case_count"], 2)
                self.assertEqual(
                    row["passing_case_count"],
                    sum(
                        len(case_ids)
                        for case_ids in row["case_ids_by_variant"].values()
                    ),
                )

        transition = {
            name: [
                row.case_id
                for row in results
                if row.passed
                and not row.errors
                and row.domain_transition is not None
                and row.domain_transition["domain"] == name
                and name in row.layer3_skills
            ]
            for name in domains
        }
        unchanged = {
            name: [
                row.case_id
                for row in results
                if row.passed
                and not row.errors
                and row.domain_anti == name
                and row.domain_anti_variant == "unchanged-paraphrase"
                and name in row.excluded_skills
            ]
            for name in domains
        }
        expected_transition_case_ids = {
            "ai-product-extension": "ai-transition-search-to-prompt-context",
            "android-platform-extension": "mobile-transition-pwa-to-native-lifecycle",
            "bigdata-product-extension": "bigdata-transition-table-to-distributed-batch",
            "cloud-platform-extension": "structure-owner-internal-backend-placement",
            "cross-platform-client-extension": "unknown-owner",
            "ios-ipados-platform-extension": "mobile-offline-deeplink",
            "iot-embedded-extension": "iot-transition-cloud-api-to-device-protocol",
            "linux-desktop-platform-extension": "multi-task-plan",
            "low-level-systems-extension": "low-level-transition-rust-to-os-resource",
            "macos-platform-extension": "structure-generated-authority-unknown",
            "payment-trading-extension": "payment-transition-price-display-to-wallet-ledger",
            "web3-product-extension": "web3-transition-api-signature-to-chain-custody",
            "windows-platform-extension": (
                "structure-object-classification-method-placement"
            ),
        }
        for domain, case_id in expected_transition_case_ids.items():
            with self.subTest(transition_domain=domain):
                self.assertIn(case_id, transition[domain])
                self.assertGreaterEqual(len(transition[domain]), 1)
        expected_unchanged_case_ids = {
            "ai-product-extension": "ai-anti-unchanged-rag-documentation",
            "android-platform-extension": "mobile-anti-responsive-pwa",
            "bigdata-product-extension": "bigdata-anti-unchanged-pipeline-documentation",
            "cloud-platform-extension": "platform-infrastructure-direct",
            "cross-platform-client-extension": "frontend-direct",
            "ios-ipados-platform-extension": "mobile-anti-unchanged-permission-help",
            "iot-embedded-extension": "iot-anti-unchanged-protocol-documentation",
            "linux-desktop-platform-extension": "documentation",
            "low-level-systems-extension": "low-level-anti-unchanged-ffi-documentation",
            "macos-platform-extension": "logging",
            "payment-trading-extension": "payment-anti-unchanged-wallet-copy",
            "web3-product-extension": "web3-anti-unchanged-wallet-documentation",
            "windows-platform-extension": "validation",
        }
        for domain, case_id in expected_unchanged_case_ids.items():
            with self.subTest(unchanged_domain=domain):
                self.assertIn(case_id, unchanged[domain])
                self.assertGreaterEqual(len(unchanged[domain]), 1)
        transition_with_extra = {
            domain: list(case_ids) for domain, case_ids in transition.items()
        }
        transition_with_extra["ai-product-extension"].append(
            "ai-transition-additional-proof"
        )
        self.assertEqual(
            [],
            self.module._domain_coverage_errors(
                domains,
                {name: 1 for name in domains},
                {name: 1 for name in domains},
                family_coverage,
                transition_with_extra,
                unchanged,
            ),
        )
        transition["ai-product-extension"] = []
        self.assertIn(
            "Domain Skill 'ai-product-extension' has no passing actual transition route fixture",
            self.module._domain_coverage_errors(
                domains,
                {name: 1 for name in domains},
                {name: 1 for name in domains},
                family_coverage,
                transition,
                unchanged,
            ),
        )

    def test_replacing_route_oracle_breaks_actual_domain_coverage(self) -> None:
        original = self.route_module.route_with_trace

        def replacement(prompt: str, **kwargs: object) -> dict[str, object]:
            observed = copy.deepcopy(original(prompt, **kwargs))
            observed["route_decision"]["path"] = "analyzed"
            observed["route_decision"]["route_result"].update(
                {
                    "start_profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": ["repository-context-map"],
                    "review_skill": "architecture-impact-reviewer",
                }
            )
            return observed

        self.route_module.route_with_trace = replacement
        try:
            routing = self.route_module.evaluate_routes()
        finally:
            self.route_module.route_with_trace = original
        professional, layer3, domains = self.module._registries()
        results = [
            self.module._case(row, professional, layer3)
            for row in routing["results"]
        ]
        positive = {
            name: sum(
                name in row.layer3_skills
                for row in results
                if row.passed and not row.errors
            )
            for name in domains
        }
        negative = {
            name: sum(
                name in row.excluded_skills
                for row in results
                if row.passed and not row.errors
            )
            for name in domains
        }
        errors = self.module._domain_coverage_errors(
            domains,
            positive,
            negative,
            self.module._domain_family_coverage(results, domains),
        )
        self.assertEqual("fail", routing["status"])
        self.assertTrue(
            any("no positive Layer 3 routing fixture" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("no passing actual canonical route fixture" in error for error in errors),
            errors,
        )

    def test_selected_unknown_and_duplicate_exclusions_fail(self) -> None:
        for excluded, phrase in (
            (["primary-skill"], "selected route"),
            (["unknown-skill"], "unknown Skill"),
            (["excluded-skill", "excluded-skill"], "must be unique"),
        ):
            with self.subTest(excluded=excluded):
                result = self.module._case(
                    self._raw(excluded),
                    self.professional,
                    {},
                )
                self.assertTrue(any(phrase in item for item in result.errors), result.errors)

    def test_actual_route_cannot_select_explicit_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "cases.yaml"
            path.write_text(
                "cases:\n"
                "  - id: selected-exclusion\n"
                "    prompt: Implement a local backend service behavior fix with a targeted test.\n"
                f"{_l4_main_execution_yaml('selected-exclusion')}"
                "    excluded_skills: [backend-change-builder]\n"
                "    expected: {path: direct, profile: task-agent, primary_skill: backend-change-builder, layer3_skills: [], review_skill: ai-code-review-refactor}\n",
                encoding="utf-8",
            )
            report = self.route_module.evaluate_routes(path)
        self.assertEqual("fail", report["status"])
        self.assertFalse(report["results"][0]["negative_passed"])
        self.assertTrue(
            any(
                "actual route selected explicitly excluded" in item
                for item in report["errors"]
            )
        )

    def test_repeat_failure_requires_repeated_or_contradicted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "cases.yaml"
            path.write_text(
                "cases:\n"
                "  - id: first-fragile-owner-failure\n"
                "    prompt: Review the actual diff after its first failure in a fragile owner file; still perform the ordinary same-pattern scan.\n"
                f"{_l4_main_execution_yaml('first-fragile-owner-failure')}"
                "    excluded_skills: [repeat-failure-analysis]\n"
                "    expected: {path: direct, profile: review-agent, primary_skill: ai-code-review-refactor, layer3_skills: [code-review], review_skill: ai-code-review-refactor}\n"
                "  - id: same-repair-path-failed-twice\n"
                "    prompt: Review the actual diff after the same repair path failed twice and require a new hypothesis.\n"
                f"{_l4_main_execution_yaml('same-repair-path-failed-twice')}"
                "    expected: {path: direct, profile: review-agent, primary_skill: ai-code-review-refactor, layer3_skills: [repeat-failure-analysis], review_skill: ai-code-review-refactor}\n"
                "  - id: same-cause-failed-twice\n"
                "    prompt: Review the actual diff after the same cause failed twice and require a different proof path.\n"
                f"{_l4_main_execution_yaml('same-cause-failed-twice')}"
                "    expected: {path: direct, profile: review-agent, primary_skill: ai-code-review-refactor, layer3_skills: [repeat-failure-analysis], review_skill: ai-code-review-refactor}\n"
                "  - id: same-patch-and-validator-failed-twice\n"
                "    prompt: Review the actual diff after the same patch shape and same validator failed twice and require a new hypothesis.\n"
                f"{_l4_main_execution_yaml('same-patch-and-validator-failed-twice')}"
                "    expected: {path: direct, profile: review-agent, primary_skill: ai-code-review-refactor, layer3_skills: [repeat-failure-analysis], review_skill: ai-code-review-refactor}\n"
                "  - id: contradicted-repair-repeats\n"
                "    prompt: Review the actual diff because the repair repeats an approach contradicted by current evidence.\n"
                f"{_l4_main_execution_yaml('contradicted-repair-repeats')}"
                "    expected: {path: direct, profile: review-agent, primary_skill: ai-code-review-refactor, layer3_skills: [repeat-failure-analysis], review_skill: ai-code-review-refactor}\n"
                "  - id: first-verified-failure-different-action\n"
                "    prompt: Review the actual diff after the first failure has a verified cause and a materially different next action.\n"
                f"{_l4_main_execution_yaml('first-verified-failure-different-action')}"
                "    excluded_skills: [repeat-failure-analysis]\n"
                "    expected: {path: direct, profile: review-agent, primary_skill: ai-code-review-refactor, layer3_skills: [code-review], review_skill: ai-code-review-refactor}\n",
                encoding="utf-8",
            )
            report = self.route_module.evaluate_routes(path)
        self.assertEqual("pass", report["status"])
        self.assertEqual([], report["errors"])
        self.assertTrue(all(row["passed"] for row in report["results"]))
        self.assertEqual(
            [False, True, True, True, True, False],
            [
                "repeat-failure-analysis" in row["actual"]["layer3_skills"]
                for row in report["results"]
            ],
        )

    def test_domain_subtype_metadata_requires_prompt_semantics(self) -> None:
        expected = {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": [
                "ai-product-extension",
                "permission-boundary-modeling",
            ],
            "review_skill": "security-privacy-gate",
        }
        errors: list[str] = []
        self.route_module._domain_metadata(
            {
                "domain_transition": {
                    "domain": "ai-product-extension",
                    "family": "retrieval-data",
                }
            },
            "relabel-transition",
            "Analyze RAG retrieval with tenant permission in model context.",
            expected,
            set(expected["layer3_skills"]),
            [],
            errors,
        )
        self.assertTrue(
            any("lacks a same-clause migration marker" in error for error in errors),
            errors,
        )

        errors = []
        self.route_module._domain_metadata(
            {
                "domain_anti": "ai-product-extension",
                "domain_anti_variant": "unchanged-paraphrase",
            },
            "relabel-unchanged",
            "Review ordinary static search behavior.",
            {**expected, "layer3_skills": []},
            set(expected["layer3_skills"]),
            ["ai-product-extension"],
            errors,
        )
        self.assertTrue(
            any("lacks related anti-route evidence" in error for error in errors),
            errors,
        )
    def test_case_schema_error_cannot_remain_passed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "cases.yaml"
            path.write_text(
                "cases:\n"
                "  - id: unknown-exclusion\n"
                "    prompt: Implement a local backend service behavior fix with a targeted test.\n"
                f"{_l4_main_execution_yaml('unknown-exclusion')}"
                "    excluded_skills: [not-a-skill]\n"
                "    expected: {path: direct, profile: task-agent, primary_skill: backend-change-builder, layer3_skills: [], review_skill: ai-code-review-refactor}\n",
                encoding="utf-8",
            )
            report = self.route_module.evaluate_routes(path)
        row = report["results"][0]
        self.assertTrue(row["positive_passed"])
        self.assertTrue(row["negative_passed"])
        self.assertFalse(row["passed"])
        self.assertTrue(any("unknown Skill" in item for item in row["errors"]))

    def test_duplicate_case_ids_fail_every_duplicate_row(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "cases.yaml"
            case = (
                "  - id: duplicate-route\n"
                "    prompt: Implement a local backend service behavior fix with a targeted test.\n"
                f"{_l4_main_execution_yaml('duplicate-route')}"
                "    expected: {path: direct, profile: task-agent, primary_skill: backend-change-builder, layer3_skills: [], review_skill: ai-code-review-refactor}\n"
            )
            path.write_text("cases:\n" + case + case, encoding="utf-8")
            report = self.route_module.evaluate_routes(path)
        self.assertEqual("fail", report["status"])
        self.assertTrue(all(not row["passed"] for row in report["results"]))
        self.assertTrue(
            all(any("id must be unique" in item for item in row["errors"]) for row in report["results"])
        )


if __name__ == "__main__":
    unittest.main()
