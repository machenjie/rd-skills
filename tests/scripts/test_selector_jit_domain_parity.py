from __future__ import annotations

import ast
import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import deterministic_route_oracle as ORACLE
import validation_utils as VALIDATION


FOUNDATION = VALIDATION.load_yaml_file(
    ROOT / "src/registry/foundation-skills.yaml"
)
PROFESSIONAL = VALIDATION.load_yaml_file(
    ROOT / "src/registry/professional-skills.yaml"
)
DOMAIN = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")


class SelectorJitDomainParityTests(unittest.TestCase):
    def _authority(
        self,
        *,
        foundation: object | None = None,
        professional: object | None = None,
        domain: object | None = None,
    ) -> dict[str, object]:
        return VALIDATION.layer3_selector_authority(
            copy.deepcopy(FOUNDATION if foundation is None else foundation),
            copy.deepcopy(PROFESSIONAL if professional is None else professional),
            copy.deepcopy(DOMAIN if domain is None else domain),
            context="focused selector parity",
        )

    def test_shared_authority_is_complete_and_oracle_consumes_it(self) -> None:
        authority = self._authority()
        self.assertEqual("changeforge.layer3-selector-authority/v1", authority["contract"])
        self.assertEqual(62, len(authority["selectors"]))
        self.assertEqual(
            69,
            len(
                {
                    skill
                    for record in authority["selectors"]
                    for skill in record["selectable_layer3"]
                }
            ),
        )
        self.assertEqual(
            180,
            sum(len(record["owner_bindings"]) for record in authority["selectors"]),
        )
        oracle = ORACLE.oracle_admission_authority(
            foundation_registry=copy.deepcopy(FOUNDATION),
            professional_registry=copy.deepcopy(PROFESSIONAL),
        )
        expected = [
            {
                "selector_id": record.selector_id,
                "selectable_layer3": list(record.foundations),
                "source": {
                    "kind": record.source.kind,
                    "symbol": record.source.symbol,
                },
                "positive_evidence": list(record.evidence_ids),
                "owner_bindings": [
                    {
                        "primary_skill": binding.primary_skill,
                        "review_skill": binding.review_skill,
                    }
                    for binding in record.owner_bindings
                ],
            }
            for record in oracle.foundation_selectors
        ]
        actual = [
            {
                "selector_id": record["selector_id"],
                "selectable_layer3": record["selectable_layer3"],
                "source": record["source"],
                "positive_evidence": record["positive_evidence"],
                "owner_bindings": [
                    {
                        "primary_skill": binding["primary_skill"],
                        "review_skill": binding["review_skill"],
                    }
                    for binding in record["owner_bindings"]
                ],
            }
            for record in authority["selectors"]
        ]
        self.assertEqual(expected, actual)

    def test_selector_records_bind_role_negative_and_domain_authority(self) -> None:
        authority = self._authority()
        for record in authority["selectors"]:
            self.assertTrue(record["role_support"])
            self.assertTrue(record["nearest_negative"])
            for binding in record["owner_bindings"]:
                self.assertTrue(binding["role_support"])
                self.assertIsInstance(binding["domain_authorization"], list)

    def test_runtime_projection_is_professional_local_and_exact_fixed_skips(self) -> None:
        authority = self._authority()
        selected = VALIDATION.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-api-contract-changer",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        self.assertEqual("main-control-agent", selected["selection_owner"])
        self.assertEqual("professional-risk", selected["selection_basis"])
        self.assertTrue(selected["selectors"])
        self.assertNotIn("_route_impl", json.dumps(selected, sort_keys=True))
        self.assertNotIn("dynamic-helper:", json.dumps(selected, sort_keys=True))
        authorized = set(selected["authorized_layer3"])
        for record in selected["selectors"]:
            self.assertEqual(
                {
                    "selector_id",
                    "selector_kind",
                    "selectable_layer3",
                    "positive_signal_groups",
                    "nearest_negative_signals",
                },
                set(record),
            )
            self.assertTrue(set(record["selectable_layer3"]) <= authorized)
            self.assertTrue(record["positive_signal_groups"])
            self.assertTrue(record["nearest_negative_signals"])
        fixed = VALIDATION.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-api-contract-changer",
            profile="task-agent",
            selection_owner="engineering-brief",
            exact_layer3=["api-contract-design"],
        )
        self.assertFalse(fixed["selector_loaded"])
        self.assertEqual([], fixed["selectors"])
        self.assertEqual(["api-contract-design"], fixed["exact_layer3"])

    def test_exact_layer3_requires_itemwise_professional_role_and_domain_authorization(
        self,
    ) -> None:
        authority = self._authority()
        invalid = (
            (
                "direct-task-invented",
                "data-api-contract-changer",
                "task-agent",
                "main-control-agent",
                ["invented-layer3"],
            ),
            (
                "initial-analysis-sibling",
                "engineering-change-analysis",
                "analysis-agent",
                "main-control-agent",
                ["cryptography-key-lifecycle"],
            ),
            (
                "analyzed-task-consumer-impact",
                "backend-change-builder",
                "task-agent",
                "engineering-brief",
                ["consumer-impact-analysis"],
            ),
            (
                "direct-review-cryptography",
                "logging-design-gate",
                "review-agent",
                "main-control-agent",
                ["cryptography-key-lifecycle"],
            ),
            (
                "analyzed-review-release-rollback",
                "ai-code-review-refactor",
                "review-agent",
                "engineering-brief",
                ["release-rollback"],
            ),
            (
                "data-api-release-rollback",
                "data-api-contract-changer",
                "task-agent",
                "main-control-agent",
                ["release-rollback"],
            ),
            (
                "backend-tenant-isolation",
                "backend-change-builder",
                "task-agent",
                "main-control-agent",
                ["tenant-isolation"],
            ),
            (
                "data-api-unauthorized-domain",
                "data-api-contract-changer",
                "task-agent",
                "main-control-agent",
                ["web3-product-extension"],
            ),
            (
                "unsupported-profile-role",
                "data-api-contract-changer",
                "review-agent",
                "main-control-agent",
                ["api-contract-design"],
            ),
        )
        for label, professional, profile, owner, exact in invalid:
            with self.subTest(label=label):
                with self.assertRaises(VALIDATION.ValidationProblem):
                    VALIDATION.layer3_selector_runtime_projection(
                        authority,
                        professional_skill=professional,
                        profile=profile,
                        selection_owner=owner,
                        exact_layer3=exact,
                    )

        for professional, domain in (
            ("ai-code-review-refactor", "web3-product-extension"),
            ("ai-code-review-refactor", "low-level-systems-extension"),
            ("quality-test-gate", "bigdata-product-extension"),
        ):
            fixed = VALIDATION.layer3_selector_runtime_projection(
                authority,
                professional_skill=professional,
                profile="review-agent",
                selection_owner="main-control-agent",
                exact_layer3=[domain],
            )
            self.assertEqual([domain], fixed["exact_layer3"])
            self.assertFalse(fixed["selector_loaded"])

    def test_task_and_review_projection_filters_are_itemwise_and_independent(self) -> None:
        authority = self._authority()
        surfaces = {
            "logging-review": (
                "logging-design-gate",
                "review-agent",
                "main-control-agent",
            ),
            "data-api-task": (
                "data-api-contract-changer",
                "task-agent",
                "main-control-agent",
            ),
            "backend-task": (
                "backend-change-builder",
                "task-agent",
                "engineering-brief",
            ),
        }
        projected = {}
        for label, (professional, profile, owner) in surfaces.items():
            projection = VALIDATION.layer3_selector_runtime_projection(
                authority,
                professional_skill=professional,
                profile=profile,
                selection_owner=owner,
                exact_layer3=None,
            )
            projected[label] = {
                record["selector_id"]: record["selectable_layer3"]
                for record in projection["selectors"]
            }
            self.assertTrue(
                all(
                    set(record["selectable_layer3"])
                    <= set(projection["authorized_layer3"])
                    for record in projection["selectors"]
                )
            )

        self.assertEqual(
            ["secret-configuration-security"],
            projected["logging-review"]["cryptography-key-lifecycle"],
        )
        self.assertEqual(
            ["version-compatibility"],
            projected["data-api-task"]["production-release-decision"],
        )
        self.assertEqual(
            ["failure-contract-design"],
            projected["backend-task"]["external-integration-analysis"],
        )
        self.assertEqual(
            ["permission-boundary-modeling"],
            projected["backend-task"]["tenant-isolation-security"],
        )

    def test_control_projection_is_owner_reachable_without_professional_root_or_catalog(
        self,
    ) -> None:
        authority = self._authority()
        projections = VALIDATION.layer3_selector_control_projections(authority)
        self.assertIn("data-api-contract-changer.json", projections)
        self.assertNotIn("index.json", projections)
        payload = projections["data-api-contract-changer.json"]
        self.assertEqual("data-api-contract-changer", payload["professional_skill"])
        self.assertTrue(payload["selection_surfaces"])
        rendered = json.dumps(payload, sort_keys=True)
        for forbidden in (
            "_route_impl",
            "_review_risk_layer3",
            "dynamic-helper:",
            "deterministic_route_oracle",
            "primary_skill",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)
        router = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/professional-skill-router.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "engineering-control-plane/references/selectors/"
            "<professional-skill>.json",
            router,
        )

    def test_review_domain_consumer_uses_fixed_review_skill_and_review_risk(self) -> None:
        authority = self._authority()
        cases = (
            (
                "ai-code-review-refactor",
                "web3-product-extension",
                ["changed-surface", "blockchain", "finality"],
                "hash or signature terminology without chain or custody behavior",
            ),
            (
                "ai-code-review-refactor",
                "low-level-systems-extension",
                ["changed-surface", "ABI", "ownership"],
                "C++ or Rust usage without a native ABI, OS, or resource boundary",
            ),
            (
                "quality-test-gate",
                "bigdata-product-extension",
                ["changed-surface", "stream", "checkpoint"],
                "single-database large-table work without a distributed pipeline, replay, or downstream consumer boundary",
            ),
        )
        for professional, domain, positive, nearest_negative in cases:
            projection = VALIDATION.layer3_selector_runtime_projection(
                authority,
                professional_skill=professional,
                profile="review-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
            )
            self.assertEqual("review-risk", projection["selection_basis"])
            self.assertEqual(professional, projection["professional_skill"])
            with self.subTest(professional=professional, outcome="positive"):
                selected = VALIDATION.layer3_selector_runtime_selection(
                    projection,
                    evidence_signals=positive,
                )
                self.assertEqual([domain], selected)
            with self.subTest(professional=professional, outcome="nearest-negative"):
                selected = VALIDATION.layer3_selector_runtime_selection(
                    projection,
                    evidence_signals=[*positive, nearest_negative],
                )
                self.assertEqual([], selected)
            with self.subTest(professional=professional, outcome="background"):
                selected = VALIDATION.layer3_selector_runtime_selection(
                    projection,
                    evidence_signals=positive[1:],
                )
                self.assertEqual([], selected)

    def test_cardinality_fails_closed_without_truncation(self) -> None:
        authority = self._authority()
        with self.assertRaises(VALIDATION.ValidationProblem):
            VALIDATION.layer3_selector_runtime_projection(
                authority,
                professional_skill="engineering-change-analysis",
                profile="analysis-agent",
                selection_owner="main-control-agent",
                exact_layer3=["a", "b", "c", "d"],
            )
        duplicate = copy.deepcopy(FOUNDATION)
        duplicate["selector_authority"]["selectors"][0]["selectable_layer3"] *= 2
        with self.assertRaises(VALIDATION.ValidationProblem):
            self._authority(foundation=duplicate)

    def test_three_domain_edges_are_reciprocal_and_total_is_47(self) -> None:
        authority = VALIDATION.domain_modifier_routing_authority(
            copy.deepcopy(DOMAIN),
            copy.deepcopy(PROFESSIONAL),
        )
        self.assertEqual(47, authority["edge_count"])
        expected = {
            ("ai-code-review-refactor", "web3-product-extension"),
            ("ai-code-review-refactor", "low-level-systems-extension"),
            ("quality-test-gate", "bigdata-product-extension"),
        }
        observed = {
            (professional, domain)
            for professional, domains in authority["domains_by_professional"].items()
            for domain in domains
        }
        self.assertTrue(expected <= observed)

        selector_authority = self._authority()
        authorized = {
            binding["primary_skill"]: set(binding["domain_authorization"])
            for record in selector_authority["selectors"]
            for binding in record["owner_bindings"]
            if binding["primary_skill"] in {
                "ai-code-review-refactor",
                "quality-test-gate",
            }
        }
        self.assertTrue(
            {
                "web3-product-extension",
                "low-level-systems-extension",
            }
            <= authorized["ai-code-review-refactor"]
        )
        self.assertIn(
            "bigdata-product-extension",
            authorized["quality-test-gate"],
        )

    def test_domain_positive_and_nearest_negative_boundaries_are_exact(self) -> None:
        cases = {
            "web3-product-extension": (
                "Review blockchain chain custody finality and recovery.",
                "Review payment-only hash terminology without chain or custody behavior.",
            ),
            "bigdata-product-extension": (
                "Review a distributed stream pipeline replay checkpoint and downstream consumer.",
                "Review an ordinary database large table without a distributed pipeline replay boundary.",
            ),
            "low-level-systems-extension": (
                "Review a Rust ABI FFI native ownership and resource boundary.",
                "Review language-only C++ and Rust without a native ABI OS or resource boundary.",
            ),
        }
        for domain, (positive, negative) in cases.items():
            with self.subTest(domain=domain):
                positive_result = {
                    row["skill"]: row
                    for row in ORACLE.classify_domain_modifiers(positive)
                }
                negative_result = {
                    row["skill"]: row
                    for row in ORACLE.classify_domain_modifiers(negative)
                }
                self.assertTrue(positive_result[domain]["eligible"])
                self.assertFalse(negative_result[domain]["eligible"])
                self.assertIn(
                    "unchanged-or-anti-trigger",
                    negative_result[domain]["rejection_reasons"],
                )

    def test_core_selection_ownership_and_review_independence_are_closed(self) -> None:
        contract = VALIDATION.CORE_CONTRACTS["layer3_selector_contract"]
        self.assertEqual(
            {
                "direct-task": "main-control-agent",
                "direct-review": "main-control-agent",
                "initial-analysis": "main-control-agent",
                "analyzed-task": "engineering-brief",
                "analyzed-review": "engineering-brief",
            },
            contract["selection_owners"],
        )
        self.assertEqual("independent-review-risk", contract["review_selection"])
        self.assertEqual("fail-closed", contract["over_maximum"])

    def test_build_has_no_oracle_import_or_task_matcher(self) -> None:
        source = (ROOT / "scripts/build.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("deterministic_route_oracle", imports)
        forbidden_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(term in node.name for term in ("match_task", "route_task"))
        }
        self.assertEqual(set(), forbidden_names)
        self.assertIn(
            '_write_control_layer3_selector_projections(destination)',
            source,
        )
        self.assertIn(
            'destination / "references" / "selectors"',
            source,
        )
        self.assertNotIn("_write_layer3_selector_authority", source)
        self.assertNotIn("references/layer3/selector-authority.json", source)


if __name__ == "__main__":
    unittest.main()
