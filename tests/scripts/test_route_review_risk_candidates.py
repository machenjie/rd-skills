from __future__ import annotations

import copy
import unittest
from unittest import mock

from tests.scripts import test_route_candidate_cohorts as COHORTS


ORACLE = COHORTS.ORACLE
CASES_PATH = COHORTS.CASES_PATH

FULL_CONVERT_RULE_IDS = {"review-default-code"}
SPLIT_RETAINED_RULE_IDS = {
    "review-repeat-failure",
    "review-ambiguous-structure-repository-first",
    "review-minimality-change",
    "review-domain-pattern-structure",
    "review-refactoring-change",
    "review-readability-change",
    "tenant-isolation-security",
    "generic-security-risk",
    "production-release-decision",
    "reliability-signal-analysis",
}
KEEP_RULE_IDS = {
    "production-rollout-fallback",
    "ssrf-url-fetch-analysis",
    "privacy-or-token-security",
    "secret-rotation",
    "audit-integrity-change",
    "security-credential-session-lifecycle",
    "engineering-artifact-review",
}
CANONICAL_CANDIDATE_RULE_IDS = frozenset(
    {
        "acceptance-definition",
        "accepted-brief-task-dag",
        "ambiguous-intake",
        "api-compatibility-artifact",
        "audit-integrity-change",
        "backend-effects-ambiguous",
        "backend-idempotency-analysis",
        "backend-layer-budget",
        "cache-stampede-reliability-controls",
        "concurrency-control-analysis",
        "cryptography-key-lifecycle",
        "cryptography-specialist-boundary",
        "data-consistency-artifact",
        "database-migration-analysis",
        "database-migration-coexistence-rollback",
        "dependent-task-analysis-early",
        "dependent-task-analysis-fallback",
        "design-pattern-analysis",
        "distributed-effect-ambiguous",
        "distributed-workflow-analysis",
        "distributed-workflow-consistency-analysis",
        "documentation-only-change",
        "domain-object-analysis",
        "dto-model-boundary-analysis",
        "engineering-artifact-review",
        "experience-design-system-analysis",
        "experience-interaction-analysis",
        "explicit-architecture-tradeoff",
        "explicit-authentication-authorization-analysis",
        "explicit-test-data-analysis",
        "external-integration-analysis",
        "external-integration-consumer-impact-analysis",
        "external-integration-failure-contract-analysis",
        "failure-diagnosis-analysis",
        "generic-security-risk",
        "high-risk-architecture-plan",
        "high-risk-module-boundary-review",
        "high-risk-technology-stack-review",
        "incident-response-coordination",
        "incident-response-coordination-observability",
        "installed-filesystem-ambiguous",
        "integration-handoff-artifact",
        "legal-record-admissibility",
        "migration-documentation",
        "minimality-analysis",
        "module-boundary-analysis",
        "owner-blast-radius-analysis",
        "owner-internal-structure-analysis",
        "package-dependency-analysis",
        "package-supply-chain-analysis",
        "personal-data-lifecycle",
        "privacy-or-token-security",
        "production-release-decision",
        "production-rollout-fallback",
        "public-api-analysis",
        "refactor-fixed-destination",
        "reliability-signal-analysis",
        "repository-first-default",
        "repository-tooling-ambiguous",
        "repository-tooling-layer-budget",
        "retry-lease-terminal-resolution-analysis",
        "review-ambiguous-structure-repository-first",
        "review-domain-pattern-structure",
        "review-minimality-change",
        "review-readability-change",
        "review-refactoring-change",
        "review-repeat-failure",
        "sdk-contract-analysis",
        "secret-rotation",
        "security-anti-input-shape",
        "security-anti-reliability-only",
        "security-anti-scanner-report",
        "security-credential-session-lifecycle",
        "source-backed-repository-question",
        "ssrf-threat-professional-precedence",
        "ssrf-url-fetch-analysis",
        "technology-stack-commitment",
        "tenant-isolation-security",
        "test-strategy-professional-precedence",
        "user-flow-analysis",
    }
)
DIRECT_RISK_CASE_TO_CANDIDATE = {
    "t2c-review-security-tenant-auth-diff": "review-security-risk",
    "t2c-review-release-production-rollout": "review-release-risk",
    "t2c-review-logging-secret-redaction": "review-logging-risk",
    "t2c-review-reliability-slo-recovery": "review-reliability-risk",
    "t2c-review-regression-security-risk": "review-security-risk",
}
GENERIC_REVIEW_CASE_IDS = {
    "t2c-review-security-auth-unchanged",
    "t2c-review-security-background-context",
    "t2c-review-release-out-of-scope",
    "t2c-review-logging-unchanged",
    "t2c-review-reliability-slo-unchanged",
    "t2c-review-generic-refactor-diff",
    "t2c-review-regression-ordinary",
}
PREPARATION_CASE_TO_RISK = {
    "t2c-preparation-security-risk": "review-security-risk",
    "t2c-preparation-release-risk": "review-release-risk",
    "t2c-preparation-logging-risk": "review-logging-risk",
    "t2c-preparation-reliability-risk": "review-reliability-risk",
}
FAMILY_SCOPED_CASE_TO_RISK = {
    "t2c-repair-security-material-logging-none": "review-security-risk",
    "t2c-repair-logging-material-security-unchanged": (
        "review-logging-risk"
    ),
    "t2c-repair-security-material-release-out-of-scope": (
        "review-security-risk"
    ),
    "t2c-repair-release-material-security-background": (
        "review-release-risk"
    ),
    "t2c-repair-release-material-reliability-unchanged": (
        "review-release-risk"
    ),
    "t2c-repair-reliability-material-release-out-of-scope": (
        "review-reliability-risk"
    ),
    "t2c-repair-logging-material-reliability-none": (
        "review-logging-risk"
    ),
    "t2c-repair-reliability-material-logging-background": (
        "review-reliability-risk"
    ),
}
OWNER_CONFLICT_CASE_TO_RISKS = {
    "t2c-repair-conflict-security-release": {
        "review-security-risk",
        "review-release-risk",
    },
    "t2c-repair-conflict-release-security": {
        "review-security-risk",
        "review-release-risk",
    },
    "t2c-repair-conflict-logging-reliability": {
        "review-logging-risk",
        "review-reliability-risk",
    },
    "t2c-repair-conflict-reliability-logging": {
        "review-logging-risk",
        "review-reliability-risk",
    },
}
FAMILY_LOCAL_CONNECTORS = ("and", "although", "even though", "yet")
FAMILY_LOCAL_MATRIX = (
    (
        "security-logging",
        (
            "tenant authorization permission bypass may cross "
            "a trust boundary"
        ),
        "logging redaction is unchanged",
        "review-security-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": [
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            "review_skill": "security-privacy-gate",
        },
    ),
    (
        "security-release",
        (
            "tenant authorization permission bypass may cross "
            "a trust boundary"
        ),
        "the production rollout decision is out of scope",
        "review-security-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": [
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            "review_skill": "security-privacy-gate",
        },
    ),
    (
        "release-reliability",
        "the production rollout may require release rollback",
        "SLO recovery is background context only",
        "review-release-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "delivery-release-gate",
            "layer3_skills": [
                "release-rollback",
                "version-compatibility",
            ],
            "review_skill": "delivery-release-gate",
        },
    ),
    (
        "logging-reliability",
        "logging may expose a secret and requires redaction",
        "SLO recovery behavior does not change",
        "review-logging-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "logging-design-gate",
            "layer3_skills": [
                "logging-error-handling",
                "secret-configuration-security",
                "observability",
            ],
            "review_skill": "logging-design-gate",
        },
    ),
)
PLURAL_COMPOUND_MATRIX = (
    (
        "reliability-nonmaterial",
        "logging may expose a secret and requires redaction",
        "SLO and recovery appear only as unchanged background context",
        "review-logging-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "logging-design-gate",
            "layer3_skills": [
                "logging-error-handling",
                "secret-configuration-security",
                "observability",
            ],
            "review_skill": "logging-design-gate",
        },
    ),
    (
        "logging-nonmaterial",
        (
            "tenant authorization permission bypass may cross "
            "a trust boundary"
        ),
        "logging and redaction appear only as unchanged background context",
        "review-security-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": [
                "permission-boundary-modeling",
                "threat-modeling",
            ],
            "review_skill": "security-privacy-gate",
        },
    ),
    (
        "security-nonmaterial",
        "the production rollout may require release rollback",
        (
            "tenant authorization and permission boundary appear only "
            "as unchanged background context"
        ),
        "review-release-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "delivery-release-gate",
            "layer3_skills": [
                "release-rollback",
                "version-compatibility",
            ],
            "review_skill": "delivery-release-gate",
        },
    ),
    (
        "release-nonmaterial",
        "outage degradation and recovery may occur",
        (
            "production rollout and release rollback appear only as "
            "unchanged background context"
        ),
        "review-reliability-risk",
        {
            "path": "direct",
            "profile": "review-agent",
            "primary_skill": "reliability-observability-gate",
            "layer3_skills": [
                "degradation-circuit-breaking",
                "observability",
                "backup-recovery",
            ],
            "review_skill": "reliability-observability-gate",
        },
    ),
)
EXPECTED_DEFERRED_LAYER3 = {
    "t2c-preparation-security-risk": ["tenant-isolation"],
    "t2c-preparation-release-risk": [],
    "t2c-preparation-logging-risk": [
        "logging-error-handling",
        "secret-configuration-security",
    ],
    "t2c-preparation-reliability-risk": ["backup-recovery"],
}
T2C_CASE_IDS = (
    set(DIRECT_RISK_CASE_TO_CANDIDATE)
    | GENERIC_REVIEW_CASE_IDS
    | set(PREPARATION_CASE_TO_RISK)
    | set(FAMILY_SCOPED_CASE_TO_RISK)
    | set(OWNER_CONFLICT_CASE_TO_RISKS)
)


def _t2c_cases() -> dict[str, dict[str, object]]:
    cases = COHORTS.load_yaml_file(CASES_PATH)["cases"]
    return {
        str(case["id"]): case
        for case in cases
        if isinstance(case, dict) and case.get("id") in T2C_CASE_IDS
    }


class RouteReviewRiskCandidateTests(unittest.TestCase):
    def test_review_candidate_inventory_has_exact_delta_and_retained_controls(
        self,
    ) -> None:
        direct_rule_ids = COHORTS._direct_rule_ids()
        candidate_rule_ids = COHORTS._candidate_rule_ids()
        self.assertEqual([], direct_rule_ids)
        self.assertEqual(
            CANONICAL_CANDIDATE_RULE_IDS,
            set(candidate_rule_ids),
        )
        self.assertEqual(len(candidate_rule_ids), len(set(candidate_rule_ids)))
        self.assertTrue(FULL_CONVERT_RULE_IDS.isdisjoint(direct_rule_ids))
        self.assertTrue(
            (SPLIT_RETAINED_RULE_IDS | KEEP_RULE_IDS).issubset(
                candidate_rule_ids
            )
        )
        self.assertEqual(3, ORACLE.ROUTE_COHORT_PRECEDENCE["review-generic"])

    def test_authoritative_t2c_routes_match_expected_contracts(self) -> None:
        cases = _t2c_cases()
        self.assertEqual(T2C_CASE_IDS, set(cases))
        for case_id, case in cases.items():
            with self.subTest(case_id=case_id):
                observed = COHORTS._observed(case)
                self.assertEqual(case["expected"], COHORTS._projected_route(observed))
                self.assertEqual(
                    {
                        "path",
                        "profile",
                        "primary_skill",
                        "layer3_skills",
                        "review_skill",
                    },
                    set(COHORTS._projected_route(observed)),
                )

    def test_direct_review_risk_candidates_beat_generic_review(self) -> None:
        cases = _t2c_cases()
        for case_id, risk_candidate_id in (
            DIRECT_RISK_CASE_TO_CANDIDATE.items()
        ):
            with self.subTest(case_id=case_id):
                trace = COHORTS._observed(cases[case_id])["winner_trace"]
                raw_ids = [
                    item["candidate_id"]
                    for item in trace["raw_candidates"]
                ]
                self.assertEqual(
                    [risk_candidate_id, "review-generic"],
                    [
                        candidate_id
                        for candidate_id in raw_ids
                        if candidate_id
                        in {risk_candidate_id, "review-generic"}
                    ],
                )
                self.assertEqual(
                    risk_candidate_id,
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertEqual(
                    ["review-generic"],
                    [
                        item["candidate_id"]
                        for item in trace["excluded_candidates"]
                        if item["candidate_id"] == "review-generic"
                    ],
                )
                self.assertEqual(
                    [f"lower-precedence-than-{risk_candidate_id}"],
                    [
                        item["reason"]
                        for item in trace["excluded_candidates"]
                        if item["candidate_id"] == "review-generic"
                    ],
                )
                self.assertNotEqual(
                    "legacy-downstream",
                    trace["selected_candidate"]["candidate_type"],
                )
                self.assertEqual("full", trace["candidate_coverage"])
                self.assertEqual("proven", trace["route_once"])

    def test_negated_and_generic_review_select_only_generic_candidate(
        self,
    ) -> None:
        cases = _t2c_cases()
        for case_id in sorted(GENERIC_REVIEW_CASE_IDS):
            with self.subTest(case_id=case_id):
                trace = COHORTS._observed(cases[case_id])["winner_trace"]
                self.assertEqual(
                    ["review-generic"],
                    [
                        item["candidate_id"]
                        for item in trace["raw_candidates"]
                        if item["candidate_type"] == "converted-cohort"
                    ],
                )
                self.assertEqual(
                    "review-generic",
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertEqual(
                    [],
                    [
                        item
                        for item in trace["excluded_candidates"]
                        if item["candidate_type"] == "converted-cohort"
                    ],
                )
                self.assertNotEqual(
                    "legacy-downstream",
                    trace["selected_candidate"]["candidate_type"],
                )

    def test_generic_review_post_filter_fallback_requires_authority(
        self,
    ) -> None:
        primary_skill = "ai-code-review-refactor"
        fallback_skill = "code-review"
        canonical_authority = ORACLE.professional_routing_authority()[
            "layer3_candidates_by_primary"
        ]
        self.assertIn(fallback_skill, canonical_authority[primary_skill])

        original_enrich = ORACLE._enrich_route_candidates
        mutated_authorities: list[dict[str, list[str]]] = []

        def enrich_without_fallback_authority(
            *args: object,
            **kwargs: object,
        ) -> object:
            layer3_authority = copy.deepcopy(
                kwargs["layer3_authority_by_primary"]
            )
            self.assertIn(fallback_skill, layer3_authority[primary_skill])
            layer3_authority[primary_skill].remove(fallback_skill)
            mutated_authorities.append(layer3_authority)
            kwargs["layer3_authority_by_primary"] = layer3_authority
            return original_enrich(*args, **kwargs)

        with mock.patch.object(
            ORACLE,
            "_enrich_route_candidates",
            side_effect=enrich_without_fallback_authority,
        ):
            with self.assertRaises(ORACLE.RoutingIntegrityError):
                ORACLE.route_with_trace(
                    (
                        "Review the actual diff for a cryptographic "
                        "construction and key lifecycle nonce policy change."
                    ),
                    main_execution=COHORTS._test_main_execution(
                        "route-global-171-s1-authority-removal"
                    ),
                )

        self.assertEqual(1, len(mutated_authorities))
        self.assertNotIn(
            fallback_skill,
            mutated_authorities[0][primary_skill],
        )
        self.assertIn(
            fallback_skill,
            ORACLE.professional_routing_authority()[
                "layer3_candidates_by_primary"
            ][primary_skill],
        )

    def test_preparation_keeps_eca_and_defers_unauthorized_risk_layers(
        self,
    ) -> None:
        cases = _t2c_cases()
        for case_id, risk_candidate_id in (
            PREPARATION_CASE_TO_RISK.items()
        ):
            with self.subTest(case_id=case_id):
                case = cases[case_id]
                observed = COHORTS._observed(case)
                trace = observed["winner_trace"]
                self.assertEqual(
                    ["implementation-preparation", risk_candidate_id],
                    [
                        item["candidate_id"]
                        for item in trace["raw_candidates"]
                        if item["candidate_id"]
                        in {
                            "implementation-preparation",
                            risk_candidate_id,
                        }
                    ],
                )
                self.assertEqual(
                    "implementation-preparation",
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertEqual(
                    [risk_candidate_id],
                    [
                        item["candidate_id"]
                        for item in trace["excluded_candidates"]
                        if item["candidate_id"] == risk_candidate_id
                    ],
                )
                self.assertEqual(
                    [
                        "lower-precedence-than-implementation-preparation"
                    ],
                    [
                        item["reason"]
                        for item in trace["excluded_candidates"]
                        if item["candidate_id"] == risk_candidate_id
                    ],
                )
                self.assertNotEqual(
                    "legacy-downstream",
                    trace["selected_candidate"]["candidate_type"],
                )
                decision = observed["route_decision"]
                self.assertEqual(
                    {"producer", "task_id"},
                    set(case["main_execution"]),
                )
                self.assertEqual("analyzed", decision["path"])
                self.assertIsNone(
                    decision["route_result"]["execution_level"]
                )
                self.assertIsNone(
                    decision["route_result"]["level_basis"]
                )
                self.assertIsNone(decision["main_execution_provenance"])
                handoff = trace["deferred_handoff"]
                self.assertEqual("unresolved", handoff["status"])
                self.assertEqual(
                    COHORTS._projected_route(observed)["layer3_skills"],
                    handoff["retained_layer3"],
                )
                self.assertEqual(
                    EXPECTED_DEFERRED_LAYER3[case_id],
                    handoff["deferred_layer3"],
                )
                self.assertEqual(
                    "candidate-layer3-not-authorized-by-"
                    "engineering-change-analysis",
                    handoff["reason"],
                )

    def test_review_risk_precedence_is_independent_of_candidate_source_order(
        self,
    ) -> None:
        selector = ORACLE._select_route_cohort_candidate
        for risk_candidate_id in sorted(
            set(DIRECT_RISK_CASE_TO_CANDIDATE.values())
        ):
            with self.subTest(candidate_id=risk_candidate_id):
                self.assertIn(
                    risk_candidate_id,
                    ORACLE.ROUTE_COHORT_PRECEDENCE,
                )
                self.assertIn(
                    "review-generic",
                    ORACLE.ROUTE_COHORT_PRECEDENCE,
                )
                raw = [
                    {
                        "candidate_id": "review-generic",
                        "evidence": ["explicit-review-task"],
                    },
                    {
                        "candidate_id": risk_candidate_id,
                        "evidence": [f"material-{risk_candidate_id}"],
                    },
                ]
                forward = selector(raw)
                reverse = selector(list(reversed(raw)))
                self.assertEqual(forward, reverse)
                self.assertEqual(
                    risk_candidate_id,
                    forward["selected_candidate"]["candidate_id"],
                )

    def test_nonmaterial_binding_is_scoped_to_each_matched_risk_family(
        self,
    ) -> None:
        cases = _t2c_cases()
        for case_id, risk_candidate_id in (
            FAMILY_SCOPED_CASE_TO_RISK.items()
        ):
            with self.subTest(case_id=case_id):
                observed = COHORTS._observed(cases[case_id])
                self.assertEqual(
                    cases[case_id]["expected"],
                    COHORTS._projected_route(observed),
                )
                trace = observed["winner_trace"]
                self.assertEqual(
                    [risk_candidate_id, "review-generic"],
                    [
                        item["candidate_id"]
                        for item in trace["raw_candidates"]
                        if item["candidate_id"]
                        in {risk_candidate_id, "review-generic"}
                    ],
                )
                self.assertEqual(
                    risk_candidate_id,
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertNotEqual(
                    "review-risk-owner-conflict",
                    trace["selected_candidate"]["candidate_id"],
                )
                self.assertNotEqual(
                    "legacy-downstream",
                    trace["selected_candidate"]["candidate_type"],
                )

    def test_distinct_review_owner_ties_select_explicit_conflict(
        self,
    ) -> None:
        cases = _t2c_cases()
        for case_id, risk_candidate_ids in (
            OWNER_CONFLICT_CASE_TO_RISKS.items()
        ):
            with self.subTest(case_id=case_id):
                case = cases[case_id]
                observed = COHORTS._observed(case)
                self.assertEqual(case["expected"], COHORTS._projected_route(observed))
                trace = observed["winner_trace"]
                ordered_risks = sorted(risk_candidate_ids)
                self.assertEqual(
                    [*ordered_risks, "review-generic"],
                    [
                        item["candidate_id"]
                        for item in trace["raw_candidates"]
                        if item["candidate_id"]
                        in {*ordered_risks, "review-generic"}
                    ],
                )
                selected = trace["selected_candidate"]
                self.assertEqual(
                    "review-risk-owner-conflict",
                    selected["candidate_id"],
                )
                self.assertEqual(
                    "equal-semantic-precedence-owner-conflict",
                    selected["reason"],
                )
                self.assertEqual(
                    "derived-conflict",
                    selected["candidate_type"],
                )
                self.assertEqual(
                    [*ordered_risks, "review-generic"],
                    [
                        item["candidate_id"]
                        for item in trace["excluded_candidates"]
                        if item["candidate_id"]
                        in {*ordered_risks, "review-generic"}
                    ],
                )
                self.assertEqual(
                    [
                        "ambiguous-review-owner",
                        "ambiguous-review-owner",
                        (
                            "lower-precedence-than-"
                            "review-risk-owner-conflict"
                        ),
                    ],
                    [
                        item["reason"]
                        for item in trace["excluded_candidates"]
                        if item["candidate_id"]
                        in {*ordered_risks, "review-generic"}
                    ],
                )
                self.assertNotEqual(
                    "legacy-downstream",
                    selected["candidate_type"],
                )
                decision = observed["route_decision"]
                self.assertEqual(
                    {"producer", "task_id"},
                    set(case["main_execution"]),
                )
                self.assertEqual("analyzed", decision["path"])
                self.assertIsNone(
                    decision["route_result"]["execution_level"]
                )
                self.assertIsNone(
                    decision["route_result"]["level_basis"]
                )
                self.assertIsNone(decision["main_execution_provenance"])
                self.assertEqual("full", trace["candidate_coverage"])
                self.assertEqual("proven", trace["route_once"])

    def test_review_owner_conflict_is_independent_of_source_order(
        self,
    ) -> None:
        cases = _t2c_cases()
        paired_case_ids = (
            (
                "t2c-repair-conflict-security-release",
                "t2c-repair-conflict-release-security",
            ),
            (
                "t2c-repair-conflict-logging-reliability",
                "t2c-repair-conflict-reliability-logging",
            ),
        )
        for left_case_id, right_case_id in paired_case_ids:
            with self.subTest(
                left_case_id=left_case_id,
                right_case_id=right_case_id,
            ):
                left = COHORTS._observed(cases[left_case_id])[
                    "winner_trace"
                ]
                right = COHORTS._observed(cases[right_case_id])[
                    "winner_trace"
                ]
                self.assertEqual(
                    left["raw_candidates"][:-1],
                    right["raw_candidates"][:-1],
                )
                self.assertEqual(
                    left["selected_candidate"],
                    right["selected_candidate"],
                )
                self.assertEqual(
                    left["excluded_candidates"][:-1],
                    right["excluded_candidates"][:-1],
                )

    def test_family_local_nonmaterial_binding_is_connector_independent(
        self,
    ) -> None:
        for (
            pair_id,
            material,
            nonmaterial,
            risk_candidate_id,
            expected_route,
        ) in FAMILY_LOCAL_MATRIX:
            for connector in FAMILY_LOCAL_CONNECTORS:
                for order, propositions in (
                    ("material-first", (material, nonmaterial)),
                    ("nonmaterial-first", (nonmaterial, material)),
                ):
                    with self.subTest(
                        pair_id=pair_id,
                        connector=connector,
                        order=order,
                    ):
                        prompt = (
                            "Review the actual diff where "
                            f"{propositions[0]} {connector} "
                            f"{propositions[1]}."
                        )
                        observed = ORACLE.route_with_trace(
                            prompt,
                            main_execution=COHORTS._test_main_execution(
                                f"t2g-family-{pair_id}-{order}"
                            ),
                        )
                        self.assertEqual(
                            expected_route,
                            COHORTS._projected_route(observed),
                        )
                        trace = observed["winner_trace"]
                        self.assertEqual(
                            [risk_candidate_id, "review-generic"],
                            [
                                item["candidate_id"]
                                for item in trace["raw_candidates"]
                                if item["candidate_id"]
                                in {risk_candidate_id, "review-generic"}
                            ],
                        )
                        self.assertEqual(
                            risk_candidate_id,
                            trace["selected_candidate"]["candidate_id"],
                        )

    def test_one_material_family_survives_two_nonmaterial_families(
        self,
    ) -> None:
        prompt = (
            "Review the actual diff where tenant authorization permission "
            "bypass may cross a trust boundary although no logging secret "
            "exposure exists and the production rollout decision is out "
            "of scope."
        )
        observed = ORACLE.route_with_trace(
            prompt,
            main_execution=COHORTS._test_main_execution(
                "t2g-one-material-family"
            ),
        )
        trace = observed["winner_trace"]
        self.assertEqual(
            {
                "path": "direct",
                "profile": "review-agent",
                "primary_skill": "security-privacy-gate",
                "layer3_skills": [
                    "permission-boundary-modeling",
                    "threat-modeling",
                ],
                "review_skill": "security-privacy-gate",
            },
            COHORTS._projected_route(observed),
        )
        self.assertEqual(
            [
                "review-security-risk",
                "review-generic",
            ],
            [
                item["candidate_id"]
                for item in trace["raw_candidates"]
                if item["candidate_id"]
                in {"review-security-risk", "review-generic"}
            ],
        )
        self.assertEqual(
            "review-security-risk",
            trace["selected_candidate"]["candidate_id"],
        )
        self.assertEqual(
            "security-privacy-gate",
            COHORTS._projected_route(observed)["primary_skill"],
        )

    def test_same_owner_compound_material_evidence_is_not_a_conflict(
        self,
    ) -> None:
        prompt = (
            "Review the actual diff where tenant authorization may change "
            "and permission bypass may cross a trust boundary."
        )
        observed = ORACLE.route_with_trace(
            prompt,
            main_execution=COHORTS._test_main_execution(
                "t2g-same-owner-compound"
            ),
        )
        trace = observed["winner_trace"]
        self.assertEqual(
            {
                "path": "direct",
                "profile": "review-agent",
                "primary_skill": "security-privacy-gate",
                "layer3_skills": [
                    "permission-boundary-modeling",
                    "threat-modeling",
                ],
                "review_skill": "security-privacy-gate",
            },
            COHORTS._projected_route(observed),
        )
        self.assertEqual(
            ["review-security-risk", "review-generic"],
            [
                item["candidate_id"]
                for item in trace["raw_candidates"][:-1]
            ],
        )
        self.assertEqual(
            "review-security-risk",
            trace["selected_candidate"]["candidate_id"],
        )
        self.assertNotEqual(
            "review-risk-owner-conflict",
            trace["selected_candidate"]["candidate_id"],
        )

    def test_family_local_nonmaterial_ranges_do_not_cross_propositions(
        self,
    ) -> None:
        value = (
            "tenant authorization permission bypass may occur although "
            "logging redaction is unchanged. the production rollout "
            "decision is out of scope yet outage recovery may occur"
        )
        ranges = ORACLE._review_risk_nonmaterial_ranges
        self.assertEqual([], ranges("review-security-risk", value))
        self.assertEqual(
            ["logging redaction is unchanged"],
            [
                value[start:end]
                for start, end in ranges("review-logging-risk", value)
            ],
        )
        self.assertEqual(
            ["production rollout decision is out of scope"],
            [
                value[start:end]
                for start, end in ranges("review-release-risk", value)
            ],
        )
        self.assertEqual([], ranges("review-reliability-risk", value))

    def test_plural_compound_background_subjects_are_family_local(
        self,
    ) -> None:
        for (
            case_id,
            material,
            nonmaterial,
            risk_candidate_id,
            expected_route,
        ) in PLURAL_COMPOUND_MATRIX:
            for order, propositions in (
                ("material-first", (material, nonmaterial)),
                ("nonmaterial-first", (nonmaterial, material)),
            ):
                with self.subTest(case_id=case_id, order=order):
                    prompt = (
                        "Review the actual diff where "
                        f"{propositions[0]} while {propositions[1]}."
                    )
                    observed = ORACLE.route_with_trace(
                        prompt,
                        main_execution=COHORTS._test_main_execution(
                            f"t2g-plural-{case_id}-{order}"
                        ),
                    )
                    self.assertEqual(expected_route, COHORTS._projected_route(observed))
                    trace = observed["winner_trace"]
                    self.assertEqual(
                        [risk_candidate_id, "review-generic"],
                        [
                            item["candidate_id"]
                            for item in trace["raw_candidates"]
                            if item["candidate_id"]
                            in {risk_candidate_id, "review-generic"}
                        ],
                    )
                    self.assertEqual(
                        risk_candidate_id,
                        trace["selected_candidate"]["candidate_id"],
                    )
                    self.assertNotEqual(
                        "review-risk-owner-conflict",
                        trace["selected_candidate"]["candidate_id"],
                    )


if __name__ == "__main__":
    unittest.main()
