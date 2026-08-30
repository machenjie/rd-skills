from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_utils import (
    CORE_CONTRACTS,
    decision_eval_authority,
    load_yaml_file,
    validate_core_contracts,
)
import fixture_capsule_contract as FIXTURE_CAPSULE
import validation_utils as VALIDATION_UTILS


DECISION_CASES = ROOT / "evals" / "routing" / "decision-cases.yaml"
BOUNDARY_RELATIONS = ROOT / "evals" / "routing" / "boundary-relations.yaml"


def _load_eval_routing():
    path = ROOT / "scripts" / "eval-routing.py"
    spec = importlib.util.spec_from_file_location("decision_eval_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVAL_ROUTING = _load_eval_routing()


class RoutingBoundaryRelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = getattr(
            EVAL_ROUTING, "evaluate_boundary_relations", None
        )
        cls.route_report = (
            EVAL_ROUTING.evaluate_routes()
            if callable(cls.validator)
            else None
        )

    def _validate(self, document, results=None):
        self.assertTrue(
            callable(self.validator),
            "eval-routing.py must own the boundary relation validator",
        )
        assert self.route_report is not None
        selected_results = (
            self.route_report["results"] if results is None else results
        )
        return type(self).validator(document, selected_results)

    def test_eight_relations_use_fresh_route_decisions_and_winner_traces(
        self,
    ) -> None:
        document = load_yaml_file(BOUNDARY_RELATIONS)
        report = self._validate(document)
        self.assertEqual("pass", report["status"], report["errors"])
        self.assertEqual(8, report["relation_count"])
        self.assertEqual(8, report["passed_count"])
        self.assertEqual(32, report["role_count"])
        self.assertEqual("proven", report["route_once"])
        self.assertEqual("full", report["candidate_coverage"])
        self.assertTrue(
            all(item["passed"] for item in report["results"])
        )

    def test_relation_schema_rejects_missing_role_duplicate_and_unknown_ids(
        self,
    ) -> None:
        document = load_yaml_file(BOUNDARY_RELATIONS)

        missing_role = copy.deepcopy(document)
        del missing_role["relations"][0]["cases"]["distractor"]
        report = self._validate(missing_role)
        self.assertTrue(
            any("exactly canonical, paraphrase, distractor, transition" in error
                for error in report["errors"]),
            report["errors"],
        )

        duplicate_case = copy.deepcopy(document)
        duplicate_case["relations"][0]["cases"]["distractor"] = (
            duplicate_case["relations"][0]["cases"]["canonical"]
        )
        report = self._validate(duplicate_case)
        self.assertTrue(
            any("case ids must be globally unique" in error
                for error in report["errors"]),
            report["errors"],
        )

        unknown_case = copy.deepcopy(document)
        unknown_case["relations"][0]["cases"]["canonical"] = "unknown-case"
        report = self._validate(unknown_case)
        self.assertTrue(
            any("unknown routing case" in error for error in report["errors"]),
            report["errors"],
        )

        duplicate_relation = copy.deepcopy(document)
        duplicate_relation["relations"][1]["id"] = (
            duplicate_relation["relations"][0]["id"]
        )
        report = self._validate(duplicate_relation)
        self.assertTrue(
            any("relation ids must be unique" in error
                for error in report["errors"]),
            report["errors"],
        )

    def test_relation_controls_reject_competitor_winner_and_stable_drift(
        self,
    ) -> None:
        document = load_yaml_file(BOUNDARY_RELATIONS)
        assert self.route_report is not None
        by_id = {
            item["id"]: copy.deepcopy(item)
            for item in self.route_report["results"]
        }
        relation = document["relations"][0]
        distractor_id = relation["cases"]["distractor"]
        transition_id = relation["cases"]["transition"]
        competitor = copy.deepcopy(by_id[transition_id])
        competitor["id"] = distractor_id
        by_id[distractor_id] = competitor
        report = self._validate(document, list(by_id.values()))
        self.assertTrue(
            any("distractor selected competing Skill" in error
                for error in report["errors"]),
            report["errors"],
        )

        by_id = {
            item["id"]: copy.deepcopy(item)
            for item in self.route_report["results"]
        }
        paraphrase_id = relation["cases"]["paraphrase"]
        by_id[paraphrase_id]["route_decision"]["route_result"][
            "primary_skill"
        ] = "quality-test-gate"
        by_id[paraphrase_id]["winner_trace"]["selected_candidate"][
            "primary_skill"
        ] = "quality-test-gate"
        matching = by_id[paraphrase_id]["winner_trace"]["selected_candidate"][
            "candidate_id"
        ]
        for candidate in by_id[paraphrase_id]["winner_trace"][
            "raw_candidates"
        ]:
            if candidate["candidate_id"] == matching:
                candidate["primary_skill"] = "quality-test-gate"
        report = self._validate(document, list(by_id.values()))
        self.assertTrue(
            any("stable dimensions drifted" in error
                for error in report["errors"]),
            report["errors"],
        )

    def test_relation_controls_reject_ineffective_and_extra_transition(
        self,
    ) -> None:
        document = load_yaml_file(BOUNDARY_RELATIONS)
        assert self.route_report is not None
        relation = document["relations"][7]
        canonical_id = relation["cases"]["canonical"]
        transition_id = relation["cases"]["transition"]

        by_id = {
            item["id"]: copy.deepcopy(item)
            for item in self.route_report["results"]
        }
        ineffective = copy.deepcopy(by_id[canonical_id])
        ineffective["id"] = transition_id
        by_id[transition_id] = ineffective
        report = self._validate(document, list(by_id.values()))
        self.assertTrue(
            any("transition dimensions differ" in error
                for error in report["errors"]),
            report["errors"],
        )

        by_id = {
            item["id"]: copy.deepcopy(item)
            for item in self.route_report["results"]
        }
        by_id[transition_id]["route_decision"]["route_result"][
            "review_skill"
        ] = "quality-test-gate"
        by_id[transition_id]["winner_trace"]["selected_candidate"][
            "review_skill"
        ] = "quality-test-gate"
        matching = by_id[transition_id]["winner_trace"]["selected_candidate"][
            "candidate_id"
        ]
        for candidate in by_id[transition_id]["winner_trace"][
            "raw_candidates"
        ]:
            if candidate["candidate_id"] == matching:
                candidate["review_skill"] = "quality-test-gate"
        report = self._validate(document, list(by_id.values()))
        self.assertTrue(
            any("transition dimensions differ" in error
                for error in report["errors"]),
            report["errors"],
        )

    def test_relation_controls_require_route_once_full_coverage_and_one_winner(
        self,
    ) -> None:
        document = load_yaml_file(BOUNDARY_RELATIONS)
        assert self.route_report is not None
        first_case = document["relations"][0]["cases"]["canonical"]
        mutations = {
            "route_once": lambda row: row["route_decision"].__setitem__(
                "route_once", False
            ),
            "coverage": lambda row: row["winner_trace"].__setitem__(
                "candidate_coverage", "partial"
            ),
            "winner": lambda row: row["winner_trace"].__setitem__(
                "selected_candidate", None
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                by_id = {
                    item["id"]: copy.deepcopy(item)
                    for item in self.route_report["results"]
                }
                mutate(by_id[first_case])
                report = self._validate(document, list(by_id.values()))
                self.assertEqual("fail", report["status"])
                self.assertTrue(report["errors"])


class DecisionEvalTests(unittest.TestCase):
    def test_authority_projects_exact_axes_mutants_and_compatibility_baseline(
        self,
    ) -> None:
        authority = decision_eval_authority(CORE_CONTRACTS)
        self.assertEqual(
            [
                "path-decision",
                "gap-ownership",
                "discovery-decision",
                "professional-layer3-decision",
                "execution-level",
                "action-authority",
                "review-decision",
            ],
            authority["decision_axes"],
        )
        self.assertEqual(
            {"routing_cases": 233, "capability_cases": 62},
            authority["compatibility_baseline"],
        )
        self.assertEqual(9, len(authority["invariant_bindings"]))
        self.assertEqual(
            set(authority["decision_axes"]),
            {binding["axis"] for binding in authority["invariant_bindings"]},
        )
        self.assertEqual(
            "evals/routing/decision-cases.yaml", authority["fixture_path"]
        )
        self.assertFalse(authority["runtime_dependency"])

    def test_authority_schema_rejects_axis_and_failure_binding_drift(self) -> None:
        missing_axis = copy.deepcopy(CORE_CONTRACTS)
        missing_axis["decision_eval_contract"]["decision_axes"].pop()
        self.assertTrue(
            any(
                "exact seven axes" in error
                for error in validate_core_contracts(missing_axis)
            )
        )

        changed_failure = copy.deepcopy(CORE_CONTRACTS)
        changed_failure["decision_eval_contract"]["invariant_bindings"][0][
            "failure_id"
        ] = "unstable-failure-id"
        self.assertTrue(
            any(
                "exact nine controlled mutants" in error
                for error in validate_core_contracts(changed_failure)
            )
        )

    def test_nine_controlled_mutants_fail_only_their_bound_invariant(self) -> None:
        report = EVAL_ROUTING.evaluate_decision_cases()
        self.assertEqual("pass", report["status"])
        self.assertEqual(7, report["axis_count"])
        self.assertEqual(9, report["case_count"])
        self.assertEqual(6, report["level_invariance_count"])
        self.assertEqual(9, report["passed_count"])
        self.assertEqual([], report["errors"])
        for result in report["results"]:
            with self.subTest(mutant=result["id"]):
                self.assertEqual([], result["baseline_failure_ids"])
                self.assertEqual(
                    [result["expected_failure_id"]],
                    result["mutant_failure_ids"],
                )
                self.assertTrue(result["mutant_evaluated"])
                self.assertTrue(result["passed"])

    def test_requested_levels_preserve_fixed_expertise_route_fields(self) -> None:
        document = load_yaml_file(DECISION_CASES)
        report = EVAL_ROUTING.evaluate_decision_document(
            document, decision_eval_authority(CORE_CONTRACTS)
        )
        self.assertEqual("pass", report["status"])
        self.assertEqual(6, report["level_invariance_count"])
        evidence = report["mechanism_evidence"]["level_invariance"]
        self.assertEqual(6, evidence["canonical_route_invocation_count"])
        self.assertEqual(
            ["unspecified", "L1", "L2", "L3", "L4", "L5"],
            evidence["requested_levels"],
        )
        self.assertTrue(evidence["fixed_route_equal"])
        self.assertEqual(
            1,
            len(
                {
                    EVAL_ROUTING.json.dumps(
                        projection["fixed_route"], sort_keys=True
                    )
                    for projection in evidence["projections"]
                }
            ),
        )
        self.assertIn("semantic_route", document["level_invariance"])
        self.assertNotIn("projections", document["level_invariance"])

    def test_every_baseline_is_canonical_before_its_mutant(self) -> None:
        document = load_yaml_file(DECISION_CASES)
        for case in document["cases"]:
            with self.subTest(case=case["id"]):
                baseline = EVAL_ROUTING.decision_case_baseline(document, case)
                self.assertEqual(
                    [],
                    EVAL_ROUTING.decision_baseline_failure_ids(baseline),
                )

        baseline = EVAL_ROUTING.decision_case_baseline(
            document, document["cases"][0]
        )
        invalid = []

        requested = copy.deepcopy(baseline)
        requested["execution_level"]["requested_level"] = "automatic"
        invalid.append(("decision-baseline-requested-level-invalid", requested))

        primary = copy.deepcopy(baseline)
        primary["professional_layer3_decision"].update(
            {
                "primary_skill": "ai-code-review-refactor",
                "implementation_layer3": ["test-strategy"],
                "domain": [],
                "required_layer3": ["test-strategy"],
            }
        )
        invalid.append(("decision-baseline-primary-role-invalid", primary))

        review_skill = copy.deepcopy(baseline)
        review_skill["review_decision"]["review_skill"] = (
            "data-api-contract-changer"
        )
        invalid.append(("decision-baseline-review-role-invalid", review_skill))

        review_layer3 = copy.deepcopy(baseline)
        review_layer3["review_decision"]["review_layer3"] = ["test-strategy"]
        invalid.append(
            ("decision-baseline-review-layer3-unauthorized", review_layer3)
        )

        domain = copy.deepcopy(baseline)
        domain["professional_layer3_decision"]["domain"] = [
            "web3-product-extension"
        ]
        invalid.append(("decision-baseline-domain-nonreciprocal", domain))

        authority = copy.deepcopy(baseline)
        authority["action_authority"]["outcome"] = "ask"
        invalid.append(("decision-baseline-action-authority-invalid", authority))

        for expected, candidate in invalid:
            with self.subTest(expected=expected):
                self.assertIn(
                    expected,
                    EVAL_ROUTING.decision_baseline_failure_ids(candidate),
                )

        invalid_document = copy.deepcopy(document)
        invalid_document["defaults"]["execution_level"][
            "requested_level"
        ] = "automatic"
        report = EVAL_ROUTING.evaluate_decision_document(
            invalid_document, decision_eval_authority(CORE_CONTRACTS)
        )
        first = report["results"][0]
        self.assertFalse(first["mutant_evaluated"])
        self.assertEqual([], first["mutant_failure_ids"])

    def test_real_confirmation_review_context_and_domain_consumers_are_bound(self) -> None:
        report = EVAL_ROUTING.evaluate_decision_cases()
        evidence = report["mechanism_evidence"]

        confirmation = evidence["l5_confirmation"]
        self.assertEqual("ask-once", confirmation["pending_action"])
        self.assertEqual("L5", confirmation["confirmed_effective"])
        self.assertEqual("L4", confirmation["rejected_effective"])
        self.assertTrue(confirmation["route_preserved"])
        self.assertTrue(confirmation["selector_preserved"])
        self.assertTrue(confirmation["brief_semantics_preserved"])

        review_copy = evidence["review_copy"]
        self.assertEqual(
            ["regression-testing"], review_copy["baseline_review_layer3"]
        )
        self.assertEqual(
            ["regression-testing"], review_copy["mutant_review_layer3"]
        )
        self.assertEqual([], review_copy["baseline_receipt_errors"])
        self.assertTrue(review_copy["mutant_receipt_errors"])
        self.assertTrue(review_copy["receipts_distinct"])
        self.assertFalse(review_copy["fixture_labels_consulted"])
        self.assertTrue(review_copy["mutant_evaluated"])
        self.assertEqual(
            ["decision-review-layer3-independent"],
            review_copy["mutant_failure_ids"],
        )

        pressure = evidence["token_pressure"]
        self.assertTrue(pressure["overflow_observed"])
        self.assertEqual("fail-closed", pressure["outcome"])
        self.assertTrue(pressure["route_obligations_preserved"])

        domains = evidence["review_domain_consumers"]
        self.assertEqual(3, domains["case_count"])
        self.assertEqual(9, domains["passed_outcome_count"])
        self.assertEqual([], domains["errors"])

    def test_decision_fixture_schema_rejects_unbound_and_duplicate_mutants(self) -> None:
        document = load_yaml_file(DECISION_CASES)
        unbound = copy.deepcopy(document)
        unbound["cases"][0]["id"] = "not-authorized"
        report = EVAL_ROUTING.evaluate_decision_document(
            unbound, decision_eval_authority(CORE_CONTRACTS)
        )
        self.assertEqual("fail", report["status"])
        self.assertTrue(
            any("controlled mutant ids" in error for error in report["errors"]),
            report["errors"],
        )

        duplicate = copy.deepcopy(document)
        duplicate["cases"].append(copy.deepcopy(duplicate["cases"][0]))
        report = EVAL_ROUTING.evaluate_decision_document(
            duplicate, decision_eval_authority(CORE_CONTRACTS)
        )
        self.assertEqual("fail", report["status"])
        self.assertTrue(
            any("must be unique" in error for error in report["errors"]),
            report["errors"],
        )

    def test_layer3_cardinality_is_unique_zero_to_three_and_never_truncated(
        self,
    ) -> None:
        document = load_yaml_file(DECISION_CASES)
        baseline = EVAL_ROUTING.decision_case_baseline(document, document["cases"][0])
        for skills in ([], ["one"], ["one", "two", "three"]):
            with self.subTest(skills=skills):
                candidate = copy.deepcopy(baseline)
                candidate["professional_layer3_decision"][
                    "implementation_layer3"
                ] = list(skills)
                candidate["professional_layer3_decision"]["required_layer3"] = list(
                    skills
                )
                self.assertNotIn(
                    "decision-layer3-cardinality-invalid",
                    EVAL_ROUTING.decision_state_failure_ids(candidate),
                )

        overflow = copy.deepcopy(baseline)
        supplied = ["one", "two", "three", "four"]
        overflow["professional_layer3_decision"][
            "implementation_layer3"
        ] = supplied
        failures = EVAL_ROUTING.decision_state_failure_ids(overflow)
        self.assertIn("decision-layer3-cardinality-invalid", failures)
        self.assertEqual(["one", "two", "three", "four"], supplied)

        duplicate = copy.deepcopy(baseline)
        duplicate["professional_layer3_decision"][
            "implementation_layer3"
        ] = ["one", "one"]
        self.assertIn(
            "decision-layer3-cardinality-invalid",
            EVAL_ROUTING.decision_state_failure_ids(duplicate),
        )

    def test_existing_route_vectors_remain_frozen_and_route_once(self) -> None:
        report = EVAL_ROUTING.evaluate_routes()
        self.assertEqual("pass", report["status"], report["errors"])
        self.assertEqual(233, report["case_count"])
        self.assertEqual(62, report["compatibility_baseline"]["capability_cases"])
        self.assertEqual("proven", report["route_once"])
        self.assertLessEqual(report["max_layer3_per_case"], 3)
        self.assertEqual(9, report["decision_eval"]["passed_count"])

    def test_l5_confirmation_changes_only_public_execution_extension(self) -> None:
        evidence = EVAL_ROUTING.evaluate_decision_cases()["mechanism_evidence"][
            "l5_confirmation"
        ]
        self.assertEqual(
            "fixture_capsule_contract:engineering-brief-task-projection/v1",
            evidence["consumer"],
        )
        self.assertEqual(
            [
                "goal",
                "acceptance",
                "non_goals",
                "owner",
                "invariants",
                "scope",
                "professional_skill",
                "implementation_layer3",
                "domain",
                "review_requirements",
            ],
            evidence["protected_fields"],
        )
        self.assertEqual(3, evidence["public_projection_count"])
        self.assertEqual(
            {
                "pending-to-confirmed": ["execution_level_extension"],
                "pending-to-rejected": ["execution_level_extension"],
            },
            evidence["changed_fields_by_transition"],
        )
        self.assertTrue(evidence["all_protected_fields_preserved"])

    def test_l5_confirmation_uses_source_owned_brief_projection_and_rejects_drift(
        self,
    ) -> None:
        projector = getattr(
            FIXTURE_CAPSULE,
            "project_engineering_brief_task_execution",
            None,
        )
        transition_errors = getattr(
            FIXTURE_CAPSULE,
            "engineering_brief_execution_transition_errors",
            None,
        )
        self.assertTrue(callable(projector))
        self.assertTrue(callable(transition_errors))
        document = load_yaml_file(DECISION_CASES)
        semantics = document["level_invariance"]["semantic_route"][
            "brief_semantics"
        ]
        level = EVAL_ROUTING._compute_decision_level(
            "unspecified",
            evidence_profile="material-l5",
            confirmation="pending",
            prior_historical_max_floor="L4",
            prior_historical_max_effective="L4",
        )
        projection = projector(semantics, level)
        self.assertEqual(
            "task_contract.analyzed_work_authority",
            projection["source_authority"],
        )

        missing = copy.deepcopy(semantics)
        del missing["invariants"]
        with self.assertRaises(FIXTURE_CAPSULE.FixtureCapsuleError):
            projector(missing, level)

        changed = copy.deepcopy(projection)
        changed["brief_semantics"]["scope"] = "changed scope"
        self.assertTrue(
            any(
                "protected Engineering Brief field changed: scope" in error
                for error in transition_errors(projection, changed)
            )
        )
        eval_source = inspect.getsource(EVAL_ROUTING)
        self.assertNotIn("def _brief_task_public_projection", eval_source)
        self.assertNotIn("**protected", eval_source)

    def test_equal_review_layer3_is_derived_by_independent_review_risk_call(
        self,
    ) -> None:
        review = EVAL_ROUTING.evaluate_decision_cases()["mechanism_evidence"][
            "review_copy"
        ]
        self.assertEqual(
            review["baseline_review_layer3"],
            review["implementation_layer3"],
        )
        self.assertEqual(2, review["selection_call_count"])
        implementation = review["implementation_selection_receipt"]
        selected_review = review["review_selection_receipt"]
        self.assertEqual("task-agent", implementation["profile"])
        self.assertEqual(
            "quality-test-gate", implementation["professional_skill"]
        )
        self.assertEqual("implementation-risk", implementation["selection_kind"])
        self.assertEqual("review-agent", selected_review["profile"])
        self.assertEqual(
            "ai-code-review-refactor", selected_review["professional_skill"]
        )
        self.assertEqual("review-risk", selected_review["selection_kind"])
        for receipt in (implementation, selected_review):
            self.assertEqual(
                ["dynamic-foundation:regression-testing"],
                receipt["selector_ids"],
            )
            self.assertEqual(["regression-testing"], receipt["selected_layer3"])
            self.assertTrue(receipt["receipt_sha256"])
        self.assertNotEqual(
            implementation["receipt_sha256"],
            selected_review["receipt_sha256"],
        )
        self.assertEqual([], review["baseline_receipt_errors"])
        self.assertTrue(
            any(
                "profile differs" in error
                or "professional_skill differs" in error
                or "selection_kind differs" in error
                for error in review["mutant_receipt_errors"]
            )
        )

    def test_selection_consumer_generates_deterministic_owner_bound_receipt(
        self,
    ) -> None:
        receipt_consumer = getattr(
            VALIDATION_UTILS,
            "layer3_selector_runtime_selection_receipt",
            None,
        )
        receipt_errors = getattr(
            VALIDATION_UTILS,
            "layer3_selector_runtime_selection_receipt_errors",
            None,
        )
        self.assertTrue(callable(receipt_consumer))
        self.assertTrue(callable(receipt_errors))
        authority = EVAL_ROUTING._decision_selector_authority()
        projection = VALIDATION_UTILS.layer3_selector_runtime_projection(
            authority,
            professional_skill="quality-test-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        selector = next(
            row
            for row in projection["selectors"]
            if row["selector_id"] == "dynamic-foundation:regression-testing"
        )
        signals = [group[0] for group in selector["positive_signal_groups"]]
        first = receipt_consumer(projection, evidence_signals=signals)
        second = receipt_consumer(projection, evidence_signals=signals)
        self.assertEqual(first, second)
        normalized_variant = receipt_consumer(
            projection,
            evidence_signals=[f"  {signal.upper()}  " for signal in signals],
        )
        self.assertEqual(first, normalized_variant)
        self.assertEqual(
            [],
            receipt_errors(
                first,
                expected_owner="main-control-agent",
                expected_profile="task-agent",
                expected_professional="quality-test-gate",
                expected_selection_kind="implementation-risk",
                expected_selected_layer3=["regression-testing"],
            ),
        )
        self.assertTrue(
            receipt_errors(
                first,
                expected_owner="main-control-agent",
                expected_profile="review-agent",
                expected_professional="ai-code-review-refactor",
                expected_selection_kind="review-risk",
                expected_selected_layer3=["regression-testing"],
            )
        )
        invalid_expectations = (
            {
                "expected_owner": "forged-owner",
                "expected_profile": "task-agent",
                "expected_professional": "quality-test-gate",
                "expected_selection_kind": "implementation-risk",
            },
            {
                "expected_owner": "main-control-agent",
                "expected_profile": "forged-profile",
                "expected_professional": "quality-test-gate",
                "expected_selection_kind": "implementation-risk",
            },
            {
                "expected_owner": "main-control-agent",
                "expected_profile": "task-agent",
                "expected_professional": "forged-professional",
                "expected_selection_kind": "implementation-risk",
            },
            {
                "expected_owner": "main-control-agent",
                "expected_profile": "task-agent",
                "expected_professional": "quality-test-gate",
                "expected_selection_kind": "review-risk",
            },
        )
        for binding in invalid_expectations:
            with self.subTest(binding=binding):
                self.assertTrue(
                    receipt_errors(
                        first,
                        **binding,
                        expected_selected_layer3=["regression-testing"],
                    )
                )

    def test_receipt_validation_replays_canonical_selector_authority(
        self,
    ) -> None:
        evidence = EVAL_ROUTING.evaluate_decision_cases()["mechanism_evidence"][
            "review_copy"
        ]
        review_receipt = evidence["review_selection_receipt"]

        def rehash(receipt: dict[str, object]) -> None:
            payload = {
                key: value
                for key, value in receipt.items()
                if key != "receipt_sha256"
            }
            receipt["receipt_sha256"] = hashlib.sha256(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()

        mutations = {
            "authority_contract": "changeforge.forged-selector-authority/v1",
            "selection_basis": "professional-risk",
            "selector_ids": ["dynamic-foundation:forged-selector"],
            "evidence_signals": ["forged review-risk evidence"],
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                forged = copy.deepcopy(review_receipt)
                forged[field] = value
                rehash(forged)
                self.assertTrue(
                    VALIDATION_UTILS.layer3_selector_runtime_selection_receipt_errors(
                        forged,
                        expected_owner="main-control-agent",
                        expected_profile="review-agent",
                        expected_professional="ai-code-review-refactor",
                        expected_selection_kind="review-risk",
                        expected_selected_layer3=["regression-testing"],
                    )
                )

        locally_forged = {
            "contract": "changeforge.layer3-selector-selection-receipt/v1",
            "authority_contract": "changeforge.layer3-selector-authority/v1",
            "selection_owner": "main-control-agent",
            "profile": "review-agent",
            "professional_skill": "ai-code-review-refactor",
            "selection_kind": "review-risk",
            "selection_basis": "review-risk",
            "selector_ids": ["dynamic-foundation:regression-testing"],
            "evidence_signals": ["locally invented signal"],
            "selected_layer3": ["regression-testing"],
            "receipt_sha256": "",
        }
        rehash(locally_forged)
        self.assertTrue(
            VALIDATION_UTILS.layer3_selector_runtime_selection_receipt_errors(
                locally_forged,
                expected_owner="main-control-agent",
                expected_profile="review-agent",
                expected_professional="ai-code-review-refactor",
                expected_selection_kind="review-risk",
                expected_selected_layer3=["regression-testing"],
            )
        )

    def test_level_baseline_uses_canonical_compute_and_rejects_missing_basis(
        self,
    ) -> None:
        document = load_yaml_file(DECISION_CASES)
        report = EVAL_ROUTING.evaluate_decision_document(
            document, decision_eval_authority(CORE_CONTRACTS)
        )
        level = report["mechanism_evidence"]["level_derivation"]
        self.assertEqual("validation_utils:compute_execution_level", level["consumer"])
        self.assertGreaterEqual(level["call_count"], 9)
        self.assertEqual([], level["errors"])
        for row in level["rows"]:
            with self.subTest(case=row["case_id"]):
                self.assertEqual(
                    row["declared_projection"], row["computed_projection"]
                )

        baseline = EVAL_ROUTING.decision_case_baseline(
            document, document["cases"][0]
        )
        missing_basis = copy.deepcopy(baseline)
        missing_basis["execution_level"]["effective_level"] = "L4"
        missing_basis["execution_level"]["computation_basis"] = None
        self.assertIn(
            "decision-baseline-execution-basis-invalid",
            EVAL_ROUTING.decision_baseline_failure_ids(missing_basis),
        )

        explicit_higher = copy.deepcopy(baseline)
        explicit_higher["execution_level"].update(
            {
                "requested_level": "L4",
                "requested_or_automatic": "L4",
                "effective_level": "L4",
            }
        )
        self.assertEqual(
            [], EVAL_ROUTING.decision_baseline_failure_ids(explicit_higher)
        )

    def test_review_independence_ignores_fixture_provenance_labels(self) -> None:
        document = load_yaml_file(DECISION_CASES)
        baseline = EVAL_ROUTING.decision_case_baseline(
            document,
            next(
                case
                for case in document["cases"]
                if case["id"] == "review-copies-implementation-layer3"
            ),
        )
        self.assertEqual(
            baseline["professional_layer3_decision"]["implementation_layer3"],
            baseline["review_decision"]["review_layer3"],
        )
        self.assertEqual(
            "review-risk-selector",
            baseline["review_decision"]["selection_provenance"],
        )
        self.assertNotIn(
            "decision-review-layer3-independent",
            EVAL_ROUTING.decision_state_failure_ids(baseline),
        )

        copied = copy.deepcopy(baseline)
        copied["review_decision"]["selection_provenance"] = (
            "implementation-layer3-copy"
        )
        self.assertEqual(
            [],
            EVAL_ROUTING.decision_state_failure_ids(copied),
        )
        review_case = next(
            case
            for case in document["cases"]
            if case["id"] == "review-copies-implementation-layer3"
        )
        self.assertEqual(
            "review-risk-selector", review_case["mutation"]["value"]
        )
        evidence, errors = EVAL_ROUTING._evaluate_review_copy(document)
        self.assertEqual([], errors)
        self.assertEqual(
            ["decision-review-layer3-independent"],
            evidence["mutant_failure_ids"],
        )
        self.assertTrue(evidence["mutant_receipt_errors"])

    def test_token_pressure_uses_obligation_aware_context_boundary(self) -> None:
        pressure = EVAL_ROUTING.evaluate_decision_cases()["mechanism_evidence"][
            "token_pressure"
        ]
        self.assertEqual(
            "eval-rendered-context-budget:evaluate_route_obligation_context",
            pressure["consumer"],
        )
        self.assertEqual("context-token-budget-overflow", pressure["failure_id"])
        self.assertFalse(pressure["continue_allowed"])
        self.assertTrue(pressure["route_obligations_preserved"])
        self.assertEqual(
            pressure["required_route_obligations"],
            pressure["observed_route_obligations"],
        )

    def test_decision_eval_fixture_and_test_have_affected_graph_binding(self) -> None:
        rules = CORE_CONTRACTS["impact_graph_contract"]["rules"]
        owner = next(rule for rule in rules if rule["id"] == "routing-fixtures-and-helpers")
        self.assertIn("evals/routing/**", owner["path_patterns"])
        self.assertIn(
            "tests/scripts/test_decision_eval.py", owner["test_modules"]
        )


if __name__ == "__main__":
    unittest.main()
