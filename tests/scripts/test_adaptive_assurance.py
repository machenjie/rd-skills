from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from fixture_capsule_contract import (  # noqa: E402
    decode_public_task_extension,
    encode_public_task_extension,
)
from validation_utils import (  # noqa: E402
    CORE_CONTRACTS,
    ExecutionLevelError,
    compute_execution_level,
    load_yaml_file,
    validate_core_contracts,
)


EXECUTION = CORE_CONTRACTS["execution_level_contract"]


def _evidence(
    *,
    source: str = "analysis_handoff",
    l1_status: str = "true",
    l2_status: str = "true",
    matched_trigger: str | None = None,
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    triggers = {
        row["id"]: {
            "status": "matched" if row["id"] == matched_trigger else "not_matched",
            "evidence_kind": source,
            "source_anchor": f"{source}:{row['id']}",
            "plausible_critical": False,
        }
        for row in EXECUTION["trigger_registry"]
    }
    if matched_trigger is not None:
        row = next(
            item for item in EXECUTION["trigger_registry"]
            if item["id"] == matched_trigger
        )
        if row["floor"] == "L4" and matched_trigger not in {
            "formal-release-declared",
            "unknown-critical-boundary",
        }:
            triggers[matched_trigger]["material_assessment"] = {
                field: f"{source}:{matched_trigger}:{field}"
                for field in EXECUTION["material_assessment_fields"]
            }
    l2 = {
        row["id"]: {
            "status": l2_status,
            "evidence_kind": source,
            "source_anchor": f"{source}:{row['id']}",
        }
        for row in EXECUTION["l2_eligibility"]
    }
    if source == "user_fact":
        for predicate in (
            "single-bounded-owner",
            "local-scope-only",
            "no-shared-contract-or-external-consumer",
            "no-unresolved-owner-placement-verification-or-rollback-gap",
        ):
            l2[predicate]["evidence_kind"] = "analysis_handoff"
            l2[predicate]["source_anchor"] = (
                f"analysis_handoff:{predicate}"
            )
    if matched_trigger is not None and next(
        item["floor"] for item in EXECUTION["trigger_registry"]
        if item["id"] == matched_trigger
    ) == "L4":
        l2["no-material-high-risk-residual-impact"]["status"] = "false"
    l1 = {
        row["id"]: {
            "status": l1_status,
            "evidence_kind": source,
            "source_anchor": f"{source}:{row['id']}",
        }
        for row in EXECUTION["l1_eligibility"]
    }
    l5 = {
        row["id"]: {
            "status": "true" if matched_trigger is not None else "false",
            "evidence_kind": source,
            "source_anchor": f"{source}:{row['id']}",
        }
        for row in EXECUTION["l5_assurance_eligibility"]
    }
    return triggers, l1, l2, l5


def _compute(
    *,
    requested: str = "unspecified",
    source: str = "analysis_handoff",
    l1_status: str = "true",
    l2_status: str = "true",
    matched_trigger: str | None = None,
    confirmation: str = "not-required",
    prior_floor: str | None = None,
    prior_effective: str | None = None,
) -> dict[str, object]:
    triggers, l1, l2, l5 = _evidence(
        source=source,
        l1_status=l1_status,
        l2_status=l2_status,
        matched_trigger=matched_trigger,
    )
    return compute_execution_level(
        requested=requested,
        trigger_evaluations=triggers,
        l1_evaluations=l1,
        l2_evaluations=l2,
        l5_assurance_evaluations=l5,
        l5_confirmation=confirmation,
        prior_historical_max_floor=prior_floor,
        prior_historical_max_effective=prior_effective,
    )


class AdaptiveAssuranceTests(unittest.TestCase):
    def test_bare_user_claims_cannot_prove_protected_repository_l2_facts(
        self,
    ) -> None:
        protected = (
            "single-bounded-owner",
            "local-scope-only",
            "no-shared-contract-or-external-consumer",
            "no-unresolved-owner-placement-verification-or-rollback-gap",
        )
        for predicate in protected:
            with self.subTest(predicate=predicate):
                triggers, l1, l2, l5 = _evidence(
                    source="analysis_handoff", l1_status="false"
                )
                l2[predicate] = {
                    "status": "true",
                    "evidence_kind": "user_fact",
                    "source_anchor": f"user_fact:owner-claim:{predicate}",
                }
                with self.assertRaisesRegex(
                    ExecutionLevelError,
                    "protected repository L2 predicate|proven task evidence",
                ):
                    compute_execution_level(
                        requested="unspecified",
                        trigger_evaluations=triggers,
                        l1_evaluations=l1,
                        l2_evaluations=l2,
                        l5_assurance_evaluations=l5,
                    )

    def test_candidate_task_evidence_cannot_prove_an_l2_predicate(self) -> None:
        triggers, l1, l2, l5 = _evidence(
            source="user_fact", l1_status="false"
        )
        l2["single-bounded-owner"]["source_anchor"] = (
            "task_evidence:owner-candidate"
        )
        with self.assertRaisesRegex(
            ExecutionLevelError,
            "candidate.*single-bounded-owner|single-bounded-owner.*candidate",
        ):
            compute_execution_level(
                requested="unspecified",
                trigger_evaluations=triggers,
                l1_evaluations=l1,
                l2_evaluations=l2,
                l5_assurance_evaluations=l5,
                task_evidence=[
                    {
                        "id": "owner-candidate",
                        "kind": "routing_candidate",
                        "task_id": "task-direct-fact-reuse",
                        "source_anchor": "src/example.py#candidate",
                    }
                ],
            )

    def test_proven_atomic_direct_facts_can_satisfy_only_their_l2_predicates(
        self,
    ) -> None:
        reuse = EXECUTION["atomic_fact_reuse"]
        mapping = reuse["proven_kind_to_l2_predicate"]
        triggers, l1, l2, l5 = _evidence(
            source="user_fact", l1_status="false"
        )
        facts = []
        for index, (kind, predicate) in enumerate(mapping.items()):
            fact_id = f"direct-fact-{index}"
            facts.append(
                {
                    "id": fact_id,
                    "kind": kind,
                    "task_id": "task-direct-fact-reuse",
                    "source_anchor": f"current-source:{predicate}",
                }
            )
            l2[predicate]["source_anchor"] = f"task_evidence:{fact_id}"

        result = compute_execution_level(
            requested="unspecified",
            trigger_evaluations=triggers,
            l1_evaluations=l1,
            l2_evaluations=l2,
            l5_assurance_evaluations=l5,
            task_evidence=facts,
        )
        self.assertEqual("L2", result["effective_level"])

        wrong = copy.deepcopy(facts)
        first_kind, first_predicate = next(iter(mapping.items()))
        wrong[0]["kind"] = next(
            kind for kind in mapping if kind != first_kind
        )
        self.assertEqual(
            f"task_evidence:{wrong[0]['id']}",
            l2[first_predicate]["source_anchor"],
        )
        with self.assertRaisesRegex(
            ExecutionLevelError,
            "cannot prove|can prove only|must use proven kind",
        ):
            compute_execution_level(
                requested="unspecified",
                trigger_evaluations=triggers,
                l1_evaluations=l1,
                l2_evaluations=l2,
                l5_assurance_evaluations=l5,
                task_evidence=wrong,
            )

    def test_material_floor_dominates_complete_proven_direct_facts(self) -> None:
        reuse = EXECUTION["atomic_fact_reuse"]
        triggers, l1, l2, l5 = _evidence(
            source="user_fact",
            l1_status="false",
            matched_trigger="public-api-event-schema-compatibility",
        )
        facts = []
        for index, (kind, predicate) in enumerate(
            reuse["proven_kind_to_l2_predicate"].items()
        ):
            fact_id = f"material-direct-fact-{index}"
            facts.append(
                {
                    "id": fact_id,
                    "kind": kind,
                    "task_id": "task-direct-material-floor",
                    "source_anchor": f"current-source:{predicate}",
                }
            )
            l2[predicate]["source_anchor"] = f"task_evidence:{fact_id}"
        l2["no-material-high-risk-residual-impact"]["status"] = "false"

        result = compute_execution_level(
            requested="unspecified",
            trigger_evaluations=triggers,
            l1_evaluations=l1,
            l2_evaluations=l2,
            l5_assurance_evaluations=l5,
            l5_confirmation="not-required",
            task_evidence=facts,
        )
        self.assertGreaterEqual(int(result["effective_level"][1:]), 4)

    def test_core_declares_closed_adaptive_assurance_contract(self) -> None:
        self.assertEqual([], validate_core_contracts(CORE_CONTRACTS))
        self.assertEqual(2, EXECUTION["schema_version"])
        self.assertEqual(
            ["unspecified", "L1", "L2", "L3", "L4", "L5"],
            EXECUTION["requested_values"],
        )
        self.assertEqual(
            [
                "no-runtime-or-product-behavior-change",
                "no-public-or-shared-contract-change",
                "no-state-data-or-invariant-change",
                "no-external-or-integration-effect",
                "deterministic-bounded-verification",
                "trivial-bounded-revert",
            ],
            [row["id"] for row in EXECUTION["l1_eligibility"]],
        )
        self.assertEqual(
            "analysis_handoff",
            EXECUTION["l5_confirmation"]["required_source"],
        )
        self.assertEqual(
            "execution-level-projection-only",
            EXECUTION["l5_confirmation"]["confirmation_effect"],
        )

    def test_strict_l1_is_an_all_true_l2_subset_and_unknown_is_not_safe(self) -> None:
        result = _compute()
        self.assertEqual("L1", result["minimum_eligible_level"])
        self.assertEqual("L1", result["automatic_level"])
        self.assertEqual("L1", result["effective_level"])
        for identifier in [row["id"] for row in EXECUTION["l1_eligibility"]]:
            triggers, l1, l2, l5 = _evidence()
            l1[identifier]["status"] = "unknown"
            result = compute_execution_level(
                requested="unspecified",
                trigger_evaluations=triggers,
                l1_evaluations=l1,
                l2_evaluations=l2,
                l5_assurance_evaluations=l5,
                l5_confirmation="not-required",
            )
            self.assertEqual("L2", result["minimum_eligible_level"], identifier)
            self.assertNotEqual("L1", result["effective_level"], identifier)

    def test_minimum_floor_requested_and_history_are_aggregated_by_max(self) -> None:
        self.assertEqual(
            "L2", _compute(l1_status="false")["minimum_eligible_level"]
        )
        self.assertEqual(
            "L3",
            _compute(l1_status="false", l2_status="false")[
                "minimum_eligible_level"
            ],
        )
        result = _compute(
            requested="L1",
            l1_status="false",
            l2_status="false",
            matched_trigger="public-api-event-schema-compatibility",
            confirmation="rejected",
            prior_effective="L4",
        )
        self.assertEqual("L4", result["minimum_eligible_level"])
        self.assertEqual("L4", result["mandatory_floor"])
        self.assertEqual("L4", result["effective_level"])
        for requested in ("L1", "L2", "L3", "L4", "L5"):
            result = _compute(requested=requested)
            self.assertGreaterEqual(
                int(str(result["effective_level"])[1:]), int(requested[1:])
            )

    def test_automatic_l5_requires_every_material_condition_and_confirmation(self) -> None:
        pending = _compute(
            l1_status="false",
            l2_status="false",
            matched_trigger="public-api-event-schema-compatibility",
            confirmation="pending",
        )
        self.assertEqual("L5", pending["assurance_recommendation"])
        self.assertEqual("L4", pending["automatic_level"])
        self.assertEqual("blocked", pending["edit_status"])
        self.assertEqual("ask-once", pending["confirmation_action"])

        confirmed = _compute(
            l1_status="false",
            l2_status="false",
            matched_trigger="public-api-event-schema-compatibility",
            confirmation="confirmed",
        )
        rejected = _compute(
            l1_status="false",
            l2_status="false",
            matched_trigger="public-api-event-schema-compatibility",
            confirmation="rejected",
        )
        self.assertEqual("L5", confirmed["effective_level"])
        self.assertEqual("L4", rejected["effective_level"])
        self.assertEqual("allowed", rejected["edit_status"])

        explicit = _compute(requested="L5", source="user_fact")
        self.assertEqual("L5", explicit["effective_level"])
        self.assertEqual("explicit", explicit["l5_confirmation"])

    def test_keyword_or_incomplete_l5_evidence_never_selects_l5(self) -> None:
        triggers, l1, l2, l5 = _evidence(
            matched_trigger="public-api-event-schema-compatibility"
        )
        l2 = copy.deepcopy(l2)
        l1 = copy.deepcopy(l1)
        for evaluation in l1.values():
            evaluation["status"] = "false"
        for evaluation in l2.values():
            evaluation["status"] = "false"
        for identifier in (
            "confirmed-material-l4",
            "critical-consequence",
            "extra-assurance-materially-reduces-uncertainty",
        ):
            mutated = copy.deepcopy(l5)
            mutated[identifier]["status"] = "false"
            result = compute_execution_level(
                requested="unspecified",
                trigger_evaluations=triggers,
                l1_evaluations=l1,
                l2_evaluations=l2,
                l5_assurance_evaluations=mutated,
                l5_confirmation="not-required",
            )
            self.assertEqual("L4", result["effective_level"], identifier)
            self.assertEqual("not-recommended", result["assurance_recommendation"])
        no_recovery = copy.deepcopy(l5)
        for identifier in ("broad-blast-radius", "irreversible", "weak-recovery"):
            no_recovery[identifier]["status"] = "false"
        result = compute_execution_level(
            requested="unspecified",
            trigger_evaluations=triggers,
            l1_evaluations=l1,
            l2_evaluations=l2,
            l5_assurance_evaluations=no_recovery,
            l5_confirmation="not-required",
        )
        self.assertEqual("not-recommended", result["assurance_recommendation"])

    def test_level_choice_and_confirmation_do_not_carry_route_fields(self) -> None:
        fixed_route = {
            "primary_professional": "data-api-contract-changer",
            "implementation_layer3": [
                "api-contract-design",
                "version-compatibility",
                "contract-testing",
            ],
            "domain": [],
            "required_review_skills": ["data-api-contract-changer"],
        }
        for requested in ("unspecified", "L1", "L2", "L3", "L4", "L5"):
            result = _compute(requested=requested)
            self.assertFalse(
                {
                    "primary_professional",
                    "implementation_layer3",
                    "domain",
                    "required_review_skills",
                }
                & set(result)
            )
            self.assertEqual(fixed_route, copy.deepcopy(fixed_route))

    def test_public_v2_round_trip_and_legacy_v1_read_compatibility(self) -> None:
        result = _compute()
        extension = {
            "requested_level": result["requested"],
            "automatic_level": result["automatic_level"],
            "minimum_eligible_level": result["minimum_eligible_level"],
            "effective_level": result["effective_level"],
            "l5_confirmation": result["l5_confirmation"],
            "level_basis": result["level_basis"],
        }
        encoded = encode_public_task_extension(extension)
        self.assertIn("minimum=L1", encoded)
        self.assertIn("c=not-required", encoded)
        self.assertEqual("execution-level/v2", decode_public_task_extension(encoded)["version"])

        legacy = "\n".join(
            [
                "Level: automatic=L2; effective=L2; edit=allowed",
                "Basis: t=[]; l=[]; u=[]",
            ]
        )
        decoded = decode_public_task_extension(legacy)
        self.assertEqual("execution-level/v1", decoded["version"])
        self.assertEqual("L2", decoded["effective_level"])

    def test_public_v2_preserves_any_recovery_path_l5_semantics(self) -> None:
        triggers, l1, l2, l5 = _evidence(
            l1_status="false",
            l2_status="false",
            matched_trigger="public-api-event-schema-compatibility",
        )
        l5["broad-blast-radius"]["status"] = "false"
        result = compute_execution_level(
            requested="unspecified",
            trigger_evaluations=triggers,
            l1_evaluations=l1,
            l2_evaluations=l2,
            l5_assurance_evaluations=l5,
            l5_confirmation="confirmed",
        )
        extension = {
            "requested_level": result["requested"],
            "automatic_level": result["automatic_level"],
            "minimum_eligible_level": result["minimum_eligible_level"],
            "effective_level": result["effective_level"],
            "l5_confirmation": result["l5_confirmation"],
            "level_basis": result["level_basis"],
        }
        decoded = decode_public_task_extension(
            encode_public_task_extension(extension)
        )
        self.assertEqual("execution-level/v2", decoded["version"])
        self.assertEqual("L5", decoded["effective_level"])

    def test_existing_decision_mutants_bind_level_failures(self) -> None:
        document = load_yaml_file(
            ROOT / "evals" / "routing" / "decision-cases.yaml"
        )
        mutants = {
            mutant["id"]: mutant["failure_id"]
            for mutant in document["cases"]
        }
        self.assertEqual(
            "decision-level-no-unsupported-downgrade",
            mutants["unsupported-l1-downgrade"],
        )
        self.assertEqual(
            "decision-level-confirmation-route-invariant",
            mutants["l5-confirmation-reroute"],
        )


if __name__ == "__main__":
    unittest.main()
