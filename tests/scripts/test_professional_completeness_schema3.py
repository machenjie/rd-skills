from __future__ import annotations

import copy
import functools
import hashlib
import json
import linecache
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_completeness_test_support as professional_support


PANEL = source_support.PANEL
_bootstrap_packet = professional_support._bootstrap_packet
_materialize_empty_capsule_chain = (
    professional_support._materialize_empty_capsule_chain
)
_ground_schema3_vote = professional_support._ground_schema3_vote
_professional_ballot = professional_support._professional_ballot
_anchor_phrase = professional_support._anchor_phrase
_write_json = source_support.write_json
R11_REVIEW_CONTRACT_FINGERPRINT = (
    "88a60c74fa8c47f9b9e5eed6a9caaf9381073057ee806b2dc2d0836709dccdde"
)


class ProfessionalSchema3ClosedFieldMigrationContractTests(unittest.TestCase):
    def test_current_contract_and_packet_target_shape_are_v3_only(self) -> None:
        packet = _bootstrap_packet()
        target = packet["professional_targets"][0]
        self.assertNotIn("source_fingerprints", packet)
        self.assertEqual(
            "professional-completeness-schema3-review-carry-v3",
            PANEL.panel_contracts.PROFESSIONAL_SCHEMA3_CONTRACT_VERSION,
        )
        self.assertEqual(
            {
                "skill_id",
                "layer",
                "root",
                "indexed_references",
                "registry",
                "required_expertise_tags",
                "routing_adjacency",
                "review_binding",
            },
            set(target),
        )
        self.assertEqual(
            {
                "skill_id",
                "layer",
                "package_material_binding",
                "dependency_material_bindings",
                "review_unit_binding",
            },
            set(target["review_binding"]),
        )
        forged = copy.deepcopy(packet)
        forged["source_fingerprints"] = {}
        with self.assertRaises(PANEL.PanelReviewError):
            PANEL._professional_v3_packet_state(
                forged,
                validation_root=PANEL.ROOT,
                artifact_path=None,
                validate_baseline=False,
            )

    def test_current_packet_limitations_name_only_material_authority(
        self,
    ) -> None:
        packet = _bootstrap_packet()
        limitations = " ".join(packet["limitations"]).lower()
        self.assertNotIn("package fingerprint", limitations)
        self.assertNotIn("origin/current provenance", limitations)
        for authority in (
            "package_material_binding",
            "review_unit_binding",
            "direct dependency material bindings",
            "origin_review_id",
            "origin_commit",
            "origin_verdict_digest",
        ):
            self.assertIn(authority, limitations)
        validated = PANEL._professional_v3_packet_state(
            copy.deepcopy(packet),
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        self.assertEqual(
            PANEL._professional_v2_projection_from_v3(packet),
            PANEL._professional_v2_projection_from_v3(copy.deepcopy(packet)),
        )
        self.assertEqual(
            sorted(
                target["skill_id"]
                for target in packet["professional_targets"]
            ),
            sorted(validated["bindings"]),
        )

    def test_current_decision_limitations_name_only_material_authority(
        self,
    ) -> None:
        packet = {
            "review_id": "schema3-decision-limitations",
            "review_contract_fingerprint": "0" * 64,
            "panel_contract": {},
        }
        with mock.patch.object(
            PANEL,
            "_professional_v3_summary_from_rows",
            return_value={},
        ), mock.patch.object(PANEL, "_professional_v3_decision_shape"):
            decision = PANEL._professional_v3_decision_record(
                packet=packet,
                packet_ref={},
                decided_on="2026-08-14",
                decision_voters=[],
                decisions=[],
            )
        limitations = " ".join(decision["limitations"]).lower()
        self.assertNotIn("package fingerprint", limitations)
        self.assertNotIn("raw package", limitations)
        for authority in (
            "package_material_binding",
            "review_unit_binding",
            "direct dependency material bindings",
            "origin_review_id",
            "origin_commit",
            "origin_verdict_digest",
        ):
            self.assertIn(authority, limitations)

    def test_current_decision_target_has_no_package_or_review_aliases(self) -> None:
        with professional_support._synthetic_schema3_professional_decision() as fixture:
            decision = fixture["decision"]
            row = decision["professional_decisions"][0]
            state = PANEL._professional_v3_packet_state(
                fixture["packet"],
                validation_root=fixture["validation_root"],
                artifact_path=fixture["packet_path"],
                validate_baseline=False,
            )
            def object_keys(value: object) -> set[str]:
                if isinstance(value, dict):
                    return set(value) | {
                        key
                        for child in value.values()
                        for key in object_keys(child)
                    }
                if isinstance(value, list):
                    return {
                        key for child in value for key in object_keys(child)
                    }
                return set()

            self.assertNotIn("origin_commit", object_keys(fixture["packet"]))
            self.assertNotIn("origin_commit", object_keys(decision))
        self.assertIn("review_unit_binding", row)
        self.assertNotIn("package_fingerprint", row)
        self.assertNotIn("review_binding_fingerprint", row)
        forged = copy.deepcopy(decision)
        forged["source_fingerprints"] = {}
        with self.assertRaises(PANEL.PanelReviewError):
            PANEL._professional_v3_decision_shape(forged)
        for alias in ("package_fingerprint", "review_binding_fingerprint"):
            with self.subTest(alias=alias):
                forged = copy.deepcopy(decision)
                forged["professional_decisions"][0][alias] = "0" * 64
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL._professional_v3_validate_decision_projection(
                        record=forged,
                        packet=fixture["packet"],
                        state=state,
                    )


def _baseline_state(packet: dict, *, depth: int) -> dict:
    state = PANEL._professional_v3_packet_state(
        packet,
        validation_root=PANEL.ROOT,
        artifact_path=None,
        validate_baseline=False,
    )
    review_id = "schema3-baseline"
    decision_ref = {
        "path": f"{review_id}/panel/decision.json",
        "sha256": "a" * 64,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": review_id,
    }
    packet_ref = {
        "path": f"{review_id}/packet.json",
        "sha256": "b" * 64,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": review_id,
    }
    dependencies = {}
    origins = {}
    for skill_id, binding in state["bindings"].items():
        required = list(binding["dependency_material_bindings"])
        dependencies[skill_id] = {
            "skill_id": skill_id,
            "final_disposition": "accepted-current-professional-completeness",
            "evidence_complete": True,
            "prior_target_vote_count": 3,
            "required_candidate_ids": required,
            "reviewer_added_candidate_ids_union": [],
            "dependency_candidate_ids": required,
        }
        origins[skill_id] = {
            "decision_ref": decision_ref,
            "target_decision_fingerprint": hashlib.sha256(
                skill_id.encode("utf-8")
            ).hexdigest(),
        }
    return {
        "decision_ref": decision_ref,
        "packet_ref": packet_ref,
        "snapshot": state["snapshot"],
        "dependencies": dependencies,
        "origins": origins,
        "plan_lineage_depth": depth,
    }






def _anchor_unigrams(
    anchor_id: str,
    *,
    vote: dict,
    materials_by_skill: dict,
) -> list[str]:
    anchors = {row["anchor_id"]: row for row in vote["evidence_anchors"]}
    return list(
        dict.fromkeys(
            token
            for sequence in PANEL._professional_v3_anchor_token_sequences(
                anchor_id,
                anchors_by_id=anchors,
                materials_by_skill=materials_by_skill,
            )
            for token in sequence
        )
    )


def _separated_unigrams(tokens: list[str]) -> str:
    separators = ("xylophone", "quasar", "nebula", "zephyr", "platypus", "orchid")
    return " ".join(
        value
        for index, token in enumerate(tokens)
        for value in (token, separators[index % len(separators)])
    )


def _assertion_source_bigrams(
    assertion: dict,
    *,
    vote: dict,
    materials_by_skill: dict,
) -> list[tuple[str, str]]:
    anchors = {row["anchor_id"]: row for row in vote["evidence_anchors"]}
    return sorted(
        {
            bigram
            for anchor_id in assertion["evidence_anchor_ids"]
            for sequence in PANEL._professional_v3_anchor_token_sequences(
                anchor_id,
                anchors_by_id=anchors,
                materials_by_skill=materials_by_skill,
            )
            for bigram in PANEL._professional_v3_ngrams(sequence, 2)
        }
    )




def _repository_source_replacement(
    path: Path, module_name: str, function, body: str
):
    name = function.__name__
    source = f"def {name}(*args, **kwargs):\n    {body}\n"
    path.write_text(source, encoding="utf-8")
    linecache.clearcache()
    module = types.ModuleType(module_name)
    module.__file__ = path.as_posix()
    sys.modules[module_name] = module
    exec(compile(source, path.as_posix(), "exec"), module.__dict__)
    replacement = module.__dict__[name]
    replacement.__qualname__ = function.__qualname__
    return replacement


def _stale_contract_baseline_artifacts(
    validation_root: Path,
    *,
    contract_fingerprint: str | None = None,
) -> tuple[Path, dict, dict]:
    review_id = "stale-contract-round"
    old_contract = contract_fingerprint or hashlib.sha256(
        b"old-review-contract"
    ).hexdigest()
    source_fingerprints = {
        "professional_packages": "1" * 64,
        "professional_review_bindings": "2" * 64,
        "professional_review_contract": old_contract,
    }
    packet = {
        "schema_version": 3,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "review_id": review_id,
        "created_on": "2026-07-16",
        "review_contract_fingerprint": old_contract,
        "panel_contract": {},
        "rubric": {},
        "professional_targets": [],
        "review_plan": {"review_contract_fingerprint": old_contract},
        "limitations": [],
    }
    if old_contract == R11_REVIEW_CONTRACT_FINGERPRINT:
        packet["source_fingerprints"] = source_fingerprints
    packet_path = validation_root / review_id / "packet.json"
    PANEL._write_json(packet_path, packet, compact=True)
    packet_ref = PANEL._professional_artifact_reference(
        packet_path,
        validation_root=validation_root,
        kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        review_id=review_id,
    )
    decision = {
        "schema_version": 3,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        "review_id": review_id,
        "decided_on": "2026-07-16",
        "decision_method": "superseded-contract-method",
        "review_contract_fingerprint": old_contract,
        "panel_contract": {},
        "packet": packet_ref,
        "voters": [],
        "professional_decisions": [],
        "summary": {},
        "limitations": [],
    }
    if old_contract == R11_REVIEW_CONTRACT_FINGERPRINT:
        decision["source_fingerprints"] = source_fingerprints
    decision_path = validation_root / review_id / "panel" / "decision.json"
    PANEL._write_json(decision_path, decision, compact=True)
    return decision_path, packet, decision


class ProfessionalCompletenessSchema3CliTests(unittest.TestCase):
    @staticmethod
    def _compact_attestation_finding(
        decisions: list[str],
    ) -> dict:
        accepted = "accepted-current-professional-completeness"
        vote_rows = [
            {
                "reviewer": f"professional-expert-{index}",
                "decision": decision,
                "reason_code": (
                    "all-professional-criteria-satisfied"
                    if decision == accepted
                    else "professional-correction-required"
                ),
                "rationale": f"Reviewer {index} rationale for {decision}.",
                "examined_adjacent_candidates": {
                    "reviewer_added_candidate_ids": [],
                },
            }
            for index, decision in enumerate(decisions, start=1)
        ]
        majority = PANEL._majority_decision(
            vote_rows,
            voter_ids=[row["reviewer"] for row in vote_rows],
        )
        majority["vote_counts"] = {
            decision: majority["vote_counts"].get(decision, 0)
            for decision in sorted(
                PANEL.PROFESSIONAL_COMPLETENESS_DECISIONS
            )
        }
        return {
            "skill_id": "sample-skill",
            "review_unit_binding": "a" * 64,
            "provenance": {
                "origin": {"origin_verdict_digest": "b" * 64},
            },
            "votes": vote_rows,
            "result": {
                key: copy.deepcopy(majority[key])
                for key in (
                    "winning_disposition",
                    "winning_votes",
                    "vote_counts",
                    "supporting_voters",
                    "dissenting_voters",
                )
            },
        }

    def test_compact_attestation_origin_derives_two_of_three_rationales(
        self,
    ) -> None:
        accepted = "accepted-current-professional-completeness"
        finding = self._compact_attestation_finding(
            [accepted, "requires-professional-correction", accepted]
        )

        projected = PANEL._professional_attestation_origin_row(finding)

        self.assertEqual(
            ["professional-expert-1", "professional-expert-3"],
            projected["supporting_voters"],
        )
        self.assertEqual(2, projected["winning_votes"])
        self.assertEqual(
            [
                {
                    "voter_id": vote["reviewer"],
                    "reason_code": vote["reason_code"],
                    "rationale": vote["rationale"],
                }
                for vote in (finding["votes"][0], finding["votes"][2])
            ],
            projected["winning_rationales"],
        )

    def test_compact_attestation_origin_derives_three_of_three_rationales(
        self,
    ) -> None:
        accepted = "accepted-current-professional-completeness"
        finding = self._compact_attestation_finding([accepted] * 3)

        projected = PANEL._professional_attestation_origin_row(finding)

        self.assertEqual(3, projected["winning_votes"])
        self.assertEqual(
            [row["reviewer"] for row in finding["votes"]],
            [row["voter_id"] for row in projected["winning_rationales"]],
        )

    def test_compact_attestation_origin_rejects_stored_majority_mismatch(
        self,
    ) -> None:
        accepted = "accepted-current-professional-completeness"
        original = self._compact_attestation_finding([accepted] * 3)
        mismatches = {
            "winning_disposition": "requires-professional-correction",
            "winning_votes": 2,
            "vote_counts": {accepted: 2},
            "supporting_voters": [
                "professional-expert-1",
                "professional-expert-2",
            ],
            "dissenting_voters": ["professional-expert-3"],
        }

        for field, value in mismatches.items():
            finding = copy.deepcopy(original)
            finding["result"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "compact professional majority is stale",
            ):
                PANEL._professional_attestation_origin_row(finding)

    def test_shared_fixture_uses_current_unittest_package(self) -> None:
        isolated_name = f"{__name__}.isolated_expert_panel_review"
        self.assertIs(PANEL, source_support.load_panel())
        self.assertIs(PANEL, sys.modules[PANEL.__name__])
        with source_support.isolated_source_module(
            "scripts/expert_panel_review.py", isolated_name
        ) as isolated:
            self.assertIsNot(PANEL, isolated)
            self.assertIs(isolated, sys.modules[isolated_name])
        self.assertNotIn(isolated_name, sys.modules)

    def _semantic_grounding_fixture(self) -> tuple[dict, dict]:
        packet = _bootstrap_packet()
        projected = PANEL._professional_v2_projection_from_v3(packet)
        skill_id = projected["professional_targets"][0]["skill_id"]
        ballot = _professional_ballot(
            projected,
            "a" * 64,
            voter=1,
            skill_ids=[skill_id],
        )
        vote = ballot["professional_votes"][0]
        materials = PANEL._professional_materials_by_skill(projected)
        _ground_schema3_vote(vote, materials)
        return vote, materials

    def _clustered_uniform_vote(
        self,
        *,
        shared_count: int,
        template: str,
        short_category: bool = False,
    ) -> tuple[dict, dict]:
        vote, materials = self._semantic_grounding_fixture()
        assertions = [
            result["evidence_assertions"][0]
            for result in vote["criteria"].values()
        ]
        self.assertEqual(10, len(assertions))
        for index, assertion in enumerate(assertions):
            source_phrase = " ".join(
                _assertion_source_bigrams(
                    assertion,
                    vote=vote,
                    materials_by_skill=materials,
                )[0]
            )
            if index < shared_count:
                separator = f" unique{index}" if short_category else ""
                assertion["claim"] = f"{source_phrase}{separator} {template}"
            else:
                assertion["claim"] = (
                    f"{source_phrase} distinct{index} alternate{index} "
                    f"wording{index} boundary{index}"
                )
        return vote, materials

    def test_fresh_attestation_origin_reference_includes_review_id(self) -> None:
        review_id = "professional-fresh-attestation"

        class OriginReferenceObserved(Exception):
            pass

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            decision_path = (
                validation_root / review_id / "panel" / "decision.json"
            )
            decision_path.parent.mkdir(parents=True)
            decision_path.write_text("{}\n", encoding="utf-8")
            packet_path = validation_root / review_id / "packet.json"
            packet = {
                "professional_targets": [{"skill_id": "sample-skill"}],
            }
            record = {
                "schema_version": (
                    PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                ),
                "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                "review_id": review_id,
                "professional_decisions": [
                    {
                        "skill_id": "sample-skill",
                        "provenance": {"mode": "fresh"},
                        "target_decision_fingerprint": "f" * 64,
                    }
                ],
            }

            def observe_origin_reference(**kwargs: object) -> None:
                self.assertEqual(
                    {
                        "path": (
                            f"{review_id}/panel/decision.json"
                        ),
                        "sha256": hashlib.sha256(
                            decision_path.read_bytes()
                        ).hexdigest(),
                        "kind": (
                            PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND
                        ),
                        "axis": (
                            PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS
                        ),
                        "review_id": review_id,
                    },
                    kwargs["origin_reference"],
                )
                raise OriginReferenceObserved

            with mock.patch.object(
                PANEL, "ROOT", validation_root
            ), mock.patch.object(
                PANEL, "validate_decision_record", return_value=None
            ), mock.patch.object(
                PANEL,
                "_decision_packet_and_ballots",
                return_value=(packet_path, packet, []),
            ), mock.patch.object(
                PANEL, "_professional_v3_packet_state", return_value={}
            ), mock.patch.object(
                PANEL,
                "_git_output",
                return_value=types.SimpleNamespace(stdout=b"0" * 40),
            ), mock.patch.object(
                PANEL,
                "_load_professional_v3_fresh_origin_target",
                side_effect=observe_origin_reference,
            ), self.assertRaises(OriginReferenceObserved):
                PANEL._professional_attestation_from_decision(
                    record,
                    decision_path=decision_path,
                )

    def test_fresh_origin_reference_review_id_is_fail_closed(self) -> None:
        review_id = "professional-origin-reference"
        skill_id = "sample-skill"
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            decision_path = (
                validation_root / review_id / "panel" / "decision.json"
            )
            decision_path.parent.mkdir(parents=True)
            decision_path.write_text("{}\n", encoding="utf-8")
            decision_ref = PANEL._professional_artifact_reference(
                decision_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                review_id=review_id,
            )

            missing_review_id = copy.deepcopy(decision_ref)
            missing_review_id.pop("review_id")
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "schema-3 carry origin decision .* fields are invalid",
            ):
                PANEL._load_professional_v3_fresh_origin_target(
                    origin_reference=missing_review_id,
                    skill_id=skill_id,
                    expected_target_decision_fingerprint="f" * 64,
                    validation_root=validation_root,
                    forbidden_paths=set(),
                )

            wrong_review_id = {
                **decision_ref,
                "review_id": f"{review_id}-wrong",
            }
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "does not match its canonical review round layout",
            ):
                PANEL._load_professional_v3_fresh_origin_target(
                    origin_reference=wrong_review_id,
                    skill_id=skill_id,
                    expected_target_decision_fingerprint="f" * 64,
                    validation_root=validation_root,
                    forbidden_paths=set(),
                )

    def test_compact_fixed_baseline_aggregates_exact_mixed_carry_plan(
        self,
    ) -> None:
        """Aggregate one real binding delta across authenticated dependencies."""

        packet = _bootstrap_packet()
        base_targets = []
        for embedded_target in packet["professional_targets"]:
            target = copy.deepcopy(embedded_target)
            target.pop("review_binding")
            base_targets.append(target)
        review_contract = packet["review_contract_fingerprint"]
        base_bindings, base_snapshot = PANEL._professional_v3_binding_state(
            base_targets,
            review_contract_fingerprint=review_contract,
        )
        pristine_attestation_bytes = (
            professional_support._current_compact_professional_fixture_bytes(
                base_targets,
                review_contract_fingerprint=review_contract,
            )
        )
        bindings, snapshot = base_bindings, base_snapshot
        packet["review_id"] = "schema3-mixed-aggregate"
        packet["professional_targets"] = [
            {
                **copy.deepcopy(target),
                "review_binding": copy.deepcopy(
                    snapshot["targets"][target["skill_id"]]
                ),
            }
            for target in base_targets
        ]

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            fixed = (
                validation_root
                / PANEL.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            )
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(pristine_attestation_bytes)
            with mock.patch.object(PANEL, "ROOT", validation_root):
                unchanged_baseline = (
                    PANEL._load_professional_attestation_baseline(
                        fixed,
                        current_bindings=base_bindings,
                        current_snapshot=base_snapshot,
                        review_contract_fingerprint=review_contract,
                        expected_attestation_sha256=hashlib.sha256(
                            pristine_attestation_bytes
                        ).hexdigest(),
                    )
                )
                all_ids = sorted(base_bindings)
                self.assertEqual(
                    all_ids,
                    sorted(unchanged_baseline["snapshot"]["targets"]),
                )
                self.assertEqual(
                    all_ids,
                    sorted(unchanged_baseline["dependencies"]),
                )
                unchanged_plan = PANEL._professional_v3_review_plan(
                    current_bindings=base_bindings,
                    review_contract_fingerprint=review_contract,
                    baseline_state=unchanged_baseline,
                )
                self.assertEqual([], unchanged_plan["fresh_targets"])
                self.assertEqual(
                    all_ids,
                    [
                        row["skill_id"]
                        for row in unchanged_plan["carried_targets"]
                    ],
                )
                self.assertEqual(
                    {
                        "total_target_count": len(all_ids),
                        "fresh_target_count": 0,
                        "carried_target_count": len(all_ids),
                    },
                    unchanged_plan["summary"],
                )

                reviewer_added_free_ids = sorted(
                    skill_id
                    for skill_id, dependency in unchanged_baseline[
                        "dependencies"
                    ].items()
                    if not dependency[
                        "reviewer_added_candidate_ids_union"
                    ]
                )
                self.assertGreaterEqual(len(reviewer_added_free_ids), 56)
                expected_carried_ids = set(reviewer_added_free_ids[:56])
                expected_fresh_ids = set(all_ids) - expected_carried_ids
                historical_storage = (
                    PANEL.panel_attestation.parse_attestation_storage_selector_bytes(
                        pristine_attestation_bytes
                    )
                )
                historical_claims = (
                    PANEL._professional_authenticated_claims_from_findings(
                        historical_storage["findings"]
                    )
                )
                base_authorities = (
                    PANEL._professional_attestation_bindings_from_state(
                        current_bindings=base_bindings,
                        authenticated_claims=historical_claims,
                    )
                )
                historical, _eligible = (
                    PANEL.panel_attestation.parse_professional_baseline_bytes(
                        pristine_attestation_bytes,
                        expected_professional_current_bindings=(
                            base_authorities
                        ),
                    )
                )
                stale_review_unit_bindings = {}
                for finding in historical["findings"]:
                    if finding["skill_id"] not in expected_fresh_ids:
                        continue
                    stale_binding = hashlib.sha256(
                        (
                            "stale-review-unit:"
                            f"{finding['skill_id']}"
                        ).encode("utf-8")
                    ).hexdigest()
                    finding["review_unit_binding"] = stale_binding
                    stale_review_unit_bindings[
                        finding["skill_id"]
                    ] = stale_binding
                historical_authorities = (
                    PANEL._professional_attestation_bindings_from_state(
                        current_bindings=base_bindings,
                        authenticated_claims=historical_claims,
                    )
                )
                for skill_id, stale_binding in (
                    stale_review_unit_bindings.items()
                ):
                    historical_authorities[skill_id][
                        "review_unit_binding"
                    ] = stale_binding
                historical = PANEL.panel_attestation.finalize_attestation(
                    historical,
                    expected_professional_current_bindings=(
                        historical_authorities
                    ),
                )
                fixed_attestation_bytes = (
                    PANEL.panel_attestation.canonical_attestation_bytes(
                        historical,
                        expected_professional_current_bindings=(
                            historical_authorities
                        ),
                    )
                )
                fixed.write_bytes(fixed_attestation_bytes)
                self.assertEqual(133, len(expected_fresh_ids))
                self.assertEqual(56, len(expected_carried_ids))
                expected_reasons = {skill_id: [] for skill_id in all_ids}
                for skill_id in expected_fresh_ids:
                    expected_reasons[skill_id] = [
                        "prior-evidence-missing",
                        "target-not-in-prior-snapshot",
                    ]

                baseline = PANEL._load_professional_attestation_baseline(
                    fixed,
                    current_bindings=bindings,
                    current_snapshot=snapshot,
                    review_contract_fingerprint=review_contract,
                    expected_attestation_sha256=hashlib.sha256(
                        fixed_attestation_bytes
                    ).hexdigest(),
                )
                packet["review_plan"] = PANEL._professional_v3_review_plan(
                    current_bindings=bindings,
                    review_contract_fingerprint=review_contract,
                    baseline_state=baseline,
                )
                actual_fresh_ids = {
                    row["skill_id"]
                    for row in packet["review_plan"]["fresh_targets"]
                }
                actual_carried_ids = {
                    row["skill_id"]
                    for row in packet["review_plan"]["carried_targets"]
                }
                self.assertEqual(
                    expected_fresh_ids,
                    actual_fresh_ids,
                )
                self.assertEqual(
                    expected_carried_ids,
                    actual_carried_ids,
                )
                fresh_ids = sorted(actual_fresh_ids)
                self.assertEqual(
                    {
                        "total_target_count": len(all_ids),
                        "fresh_target_count": len(expected_fresh_ids),
                        "carried_target_count": len(expected_carried_ids),
                    },
                    packet["review_plan"]["summary"],
                )
                actual_reasons = {
                    skill_id: [] for skill_id in actual_carried_ids
                }
                actual_reasons.update(
                    {
                        row["skill_id"]: row["reason_codes"]
                        for row in packet["review_plan"]["fresh_targets"]
                    }
                )
                self.assertEqual(expected_reasons, actual_reasons)
                PANEL._professional_v3_packet_state(
                    packet,
                    validation_root=validation_root,
                    artifact_path=None,
                    validate_baseline=True,
                )
                state = PANEL._professional_v3_packet_state(
                    packet,
                    validation_root=validation_root,
                    artifact_path=None,
                    validate_baseline=False,
                )
                round_root = (
                    validation_root
                    / ".rd-skills"
                    / "expert-panel"
                    / packet["review_id"]
                )
                packet_path = round_root / "packet.json"
                packet_path.parent.mkdir(parents=True)
                _write_json(packet_path, packet)
                packet_sha256 = hashlib.sha256(
                    packet_path.read_bytes()
                ).hexdigest()
                projected = PANEL._professional_v2_projection_from_v3(packet)
                ballots = []
                for voter in range(1, 4):
                    voter_id = f"professional-expert-{voter}"
                    (
                        _discovery,
                        _discovery_path,
                        _request,
                        _request_path,
                        capsule,
                        capsule_path,
                    ) = _materialize_empty_capsule_chain(
                        validation_root=validation_root,
                        packet=packet,
                        packet_sha256=packet_sha256,
                        state=state,
                        voter_id=voter_id,
                        skill_ids=fresh_ids,
                    )
                    capsule_ref = PANEL._artifact_reference(
                        capsule_path,
                        validation_root=validation_root,
                        kind=PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                        axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                        review_id=packet["review_id"],
                    )
                    ballot = _professional_ballot(
                        projected,
                        packet_sha256,
                        voter=voter,
                        skill_ids=fresh_ids,
                    )
                    ballot["schema_version"] = (
                        PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                    )
                    ballot.pop("source_fingerprints")
                    ballot["review_contract_fingerprint"] = review_contract
                    ballot["capsule"] = capsule_ref
                    scoped_materials = (
                        PANEL._professional_v3_target_scoped_capsule_materials(
                            capsule
                        )
                    )
                    for vote in ballot["professional_votes"]:
                        _ground_schema3_vote(
                            vote,
                            scoped_materials[vote["skill_id"]],
                        )
                    ballot_path = round_root / "panel" / f"{voter_id}.json"
                    ballot_path.parent.mkdir(parents=True, exist_ok=True)
                    _write_json(ballot_path, ballot)
                    ballots.append((ballot_path, ballot))

                decision = PANEL.aggregate_ballots(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_values=ballots,
                    decided_on="2026-07-17",
                    validation_root=validation_root,
                )
                decision_path = round_root / "panel" / "decision.json"
                _write_json(decision_path, decision)
                self.assertEqual(
                    decision,
                    PANEL.validate_decision_record(
                        decision,
                        record_path=decision_path,
                        validation_root=validation_root,
                    ),
                )
                rows = decision["professional_decisions"]
                self.assertEqual(len(all_ids), len(rows))
                self.assertEqual(
                    {
                        "fresh": len(expected_fresh_ids),
                        "carried-forward": len(expected_carried_ids),
                    },
                    {
                        mode: sum(
                            row["provenance"]["mode"] == mode for row in rows
                        )
                        for mode in ("fresh", "carried-forward")
                    },
                )
                plan_carries = {
                    row["skill_id"]: row
                    for row in packet["review_plan"]["carried_targets"]
                }
                carried = [
                    row
                    for row in rows
                    if row["provenance"]["mode"] == "carried-forward"
                ]
                for row in carried:
                    self.assertEqual(
                        PANEL.PROFESSIONAL_V3_TARGET_DECISION_FIELDS,
                        set(row),
                    )
                    row_without_fingerprint = copy.deepcopy(row)
                    row_without_fingerprint.pop("target_decision_fingerprint")
                    self.assertEqual(
                        PANEL._canonical_json_sha256(row_without_fingerprint),
                        row["target_decision_fingerprint"],
                    )
                    authority = plan_carries[row["skill_id"]]
                    provenance = row["provenance"]
                    self.assertEqual(1, provenance["origin_depth"])
                    self.assertEqual(
                        authority["origin_attestation"],
                        provenance["origin_decision"],
                    )
                    self.assertEqual(
                        authority["origin_verdict_digest"],
                        provenance["origin_target_decision_fingerprint"],
                    )
                    self.assertEqual(
                        "review-visible-binding-unchanged",
                        provenance["carry_basis"],
                    )
                    self.assertEqual(
                        authority["review_unit_binding"],
                        row["review_unit_binding"],
                    )

                tampered_origin = PANEL._professional_attestation_origin_row(
                    baseline["origins"][carried[0]["skill_id"]]["finding"]
                )
                tampered_origin["review_unit_binding"] = "0" * 64
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "review binding",
                ):
                    PANEL._professional_v3_carried_target_decision(
                        target=next(
                            target
                            for target in packet["professional_targets"]
                            if target["skill_id"] == carried[0]["skill_id"]
                        ),
                        origin_row=tampered_origin,
                        origin_decision_ref=baseline["attestation_ref"],
                        current_bindings=bindings,
                        origin_candidate_material_bindings={},
                    )

    def test_schema3_semantic_grounding_positive_control(self) -> None:
        vote, materials = self._semantic_grounding_fixture()
        PANEL._validate_professional_v3_semantic_grounding(
            vote,
            materials_by_skill=materials,
            label="professional_votes[0]",
        )

    def test_grounding_phrase_never_bridges_generic_tokens_lines_or_anchors(
        self,
    ) -> None:
        materials = {
            "target": {
                "source.md": {
                    "content": "alpha for beta\ngamma\ndelta\nepsilon zeta\n"
                }
            }
        }
        anchors = {
            "generic-gap": {
                "skill_id": "target",
                "path": "source.md",
                "start_line": 1,
                "end_line": 1,
            },
            "line-gap": {
                "skill_id": "target",
                "path": "source.md",
                "start_line": 2,
                "end_line": 3,
            },
            "left-anchor": {
                "skill_id": "target",
                "path": "source.md",
                "start_line": 2,
                "end_line": 2,
            },
            "right-anchor": {
                "skill_id": "target",
                "path": "source.md",
                "start_line": 3,
                "end_line": 3,
            },
            "positive": {
                "skill_id": "target",
                "path": "source.md",
                "start_line": 4,
                "end_line": 4,
            },
        }
        for claim, anchor_ids in (
            ("alpha beta", ["generic-gap"]),
            ("gamma delta", ["line-gap"]),
            ("gamma delta", ["left-anchor", "right-anchor"]),
        ):
            with self.subTest(anchor_ids=anchor_ids):
                self.assertEqual(
                    0,
                    PANEL._professional_v3_grounding_counts(
                        claim,
                        anchor_ids,
                        anchors_by_id=anchors,
                        materials_by_skill=materials,
                    )[1],
                )
        self.assertEqual(
            1,
            PANEL._professional_v3_grounding_counts(
                "epsilon zeta",
                ["positive"],
                anchors_by_id=anchors,
                materials_by_skill=materials,
            )[1],
        )

    def test_r6_token_salad_criterion_and_examined_items_fail_closed(self) -> None:
        for surface in ("criterion", "failure-mode", "omission-candidate"):
            vote, materials = self._semantic_grounding_fixture()
            if surface == "criterion":
                item = next(iter(vote["criteria"].values()))[
                    "evidence_assertions"
                ][0]
                anchor_ids = item["evidence_anchor_ids"]
                field = "claim"
            elif surface == "failure-mode":
                item = vote["examined_failure_modes"][0]
                anchor_ids = item["evidence_anchor_ids"]
                field = "rationale"
            else:
                item = vote["examined_omission_candidates"][0]
                anchor_ids = item["evidence_anchor_ids"]
                field = "rationale"
            first, second = _anchor_phrase(
                anchor_ids[0], vote=vote, materials_by_skill=materials
            )
            if surface != "criterion":
                item[
                    "failure_mode"
                    if surface == "failure-mode"
                    else "omission_candidate"
                ] = f"token-salad-{surface}"
            item[field] = (
                f"{first} xylophone quasar nebula separates {second} while "
                "retaining two source words as a token salad."
            )
            with self.subTest(surface=surface), self.assertRaisesRegex(
                PANEL.PanelReviewError, "exact non-generic source bigram"
            ):
                PANEL._validate_professional_v3_semantic_grounding(
                    vote,
                    materials_by_skill=materials,
                    label="professional_votes[0]",
                )

    def test_defect_fallback_requires_three_grounded_unigrams_per_anchor(
        self,
    ) -> None:
        for surface in ("criterion", "failure-mode", "omission-candidate"):
            for count, should_pass in ((3, True), (2, False)):
                vote, materials = self._semantic_grounding_fixture()
                if surface == "criterion":
                    result = next(iter(vote["criteria"].values()))
                    result["status"] = "defect-found"
                    item = result["evidence_assertions"][0]
                    anchor_ids = item["evidence_anchor_ids"]
                    field = "claim"
                elif surface == "failure-mode":
                    item = vote["examined_failure_modes"][0]
                    item["outcome"] = "defect-found"
                    item["failure_mode"] = "synthetic failure"
                    anchor_ids = item["evidence_anchor_ids"]
                    field = "rationale"
                else:
                    item = vote["examined_omission_candidates"][0]
                    item["outcome"] = "defect-found"
                    item["omission_candidate"] = "synthetic omission"
                    anchor_ids = item["evidence_anchor_ids"]
                    field = "rationale"
                anchor = next(
                    row
                    for row in vote["evidence_anchors"]
                    if row["anchor_id"] == anchor_ids[0]
                )
                line_count = len(
                    materials[anchor["skill_id"]][anchor["path"]][
                        "content"
                    ].splitlines()
                )
                while len(
                    _anchor_unigrams(
                        anchor_ids[0],
                        vote=vote,
                        materials_by_skill=materials,
                    )
                ) < 3:
                    if anchor["end_line"] < line_count:
                        anchor["end_line"] += 1
                    elif anchor["start_line"] > 1:
                        anchor["start_line"] -= 1
                    else:
                        self.fail("fixture anchor cannot expose three unigrams")
                unigrams = _anchor_unigrams(
                    anchor_ids[0],
                    vote=vote,
                    materials_by_skill=materials,
                )
                self.assertGreaterEqual(len(unigrams), 3)
                item[field] = _separated_unigrams(unigrams[:count])
                with self.subTest(surface=surface, grounded_unigrams=count):
                    if should_pass:
                        PANEL._validate_professional_v3_semantic_grounding(
                            vote,
                            materials_by_skill=materials,
                            label="professional_votes[0]",
                        )
                    else:
                        with self.assertRaisesRegex(
                            PANEL.PanelReviewError,
                            "three distinct grounded unigrams",
                        ):
                            PANEL._validate_professional_v3_semantic_grounding(
                                vote,
                                materials_by_skill=materials,
                                label="professional_votes[0]",
                            )

    def test_r6_bag_of_words_adjacency_fails_both_side_grounding(self) -> None:
        vote, materials = self._semantic_grounding_fixture()
        candidate = vote["examined_adjacent_candidates"][0]
        target_first, _target_second = _anchor_phrase(
            candidate["target_anchor_ids"][0],
            vote=vote,
            materials_by_skill=materials,
        )
        candidate_first, _candidate_second = _anchor_phrase(
            candidate["candidate_anchor_ids"][0],
            vote=vote,
            materials_by_skill=materials,
        )
        candidate["rationale"] = (
            f"{target_first} xylophone separates target evidence while "
            f"{candidate_first} quasar separates candidate evidence in this comparison."
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "separately ground target and candidate"
        ):
            PANEL._validate_professional_v3_semantic_grounding(
                vote,
                materials_by_skill=materials,
                label="professional_votes[0]",
            )

    def test_adjacency_defect_relaxation_requires_both_sides_and_six_total(
        self,
    ) -> None:
        vote, materials = self._semantic_grounding_fixture()
        candidate = vote["examined_adjacent_candidates"][0]
        candidate["disposition"] = "gap-or-overlap-defect"
        target_tokens = _anchor_unigrams(
            candidate["target_anchor_ids"][0],
            vote=vote,
            materials_by_skill=materials,
        )
        adjacent_tokens = _anchor_unigrams(
            candidate["candidate_anchor_ids"][0],
            vote=vote,
            materials_by_skill=materials,
        )
        self.assertGreaterEqual(len(target_tokens), 3)
        self.assertGreaterEqual(len(adjacent_tokens), 3)

        candidate["rationale"] = _separated_unigrams(
            target_tokens[:3] + adjacent_tokens[:3]
        )
        PANEL._validate_professional_v3_semantic_grounding(
            vote,
            materials_by_skill=materials,
            label="professional_votes[0]",
        )

        for label, tokens in (
            ("missing-candidate-side", target_tokens[:3]),
            ("total-under-six", target_tokens[:2] + adjacent_tokens[:2]),
        ):
            changed = copy.deepcopy(vote)
            changed["examined_adjacent_candidates"][0]["rationale"] = (
                _separated_unigrams(tokens)
            )
            with self.subTest(label=label), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "separately ground target and candidate",
            ):
                PANEL._validate_professional_v3_semantic_grounding(
                    changed,
                    materials_by_skill=materials,
                    label="professional_votes[0]",
                )

    def test_r6_uniform_fivegram_low_grounding_template_fails_closed(self) -> None:
        vote, materials = self._semantic_grounding_fixture()
        for criterion, result in vote["criteria"].items():
            assertion = result["evidence_assertions"][0]
            phrase = _anchor_phrase(
                assertion["evidence_anchor_ids"][0],
                vote=vote,
                materials_by_skill=materials,
            )
            assertion["claim"] = (
                f"{' '.join(phrase)} uniform xylophone quasar nebula zephyr "
                f"template supports {criterion}."
            )
        with self.assertRaisesRegex(PANEL.PanelReviewError, "source-free 5-gram"):
            PANEL._validate_professional_v3_semantic_grounding(
                vote,
                materials_by_skill=materials,
                label="professional_votes[0]",
            )

    def test_eight_of_ten_shared_fivegram_forms_a_rejecting_cluster(self) -> None:
        vote, materials = self._clustered_uniform_vote(
            shared_count=8,
            template="uniform xylophone quasar nebula zephyr",
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "source-free 5-gram ordinary template"
        ):
            PANEL._validate_professional_v3_semantic_grounding(
                vote,
                materials_by_skill=materials,
                label="professional_votes[0]",
            )

    def test_seven_of_ten_shared_fivegram_stays_below_uniform_threshold(
        self,
    ) -> None:
        vote, materials = self._clustered_uniform_vote(
            shared_count=7,
            template="uniform xylophone quasar nebula zephyr",
        )
        PANEL._validate_professional_v3_semantic_grounding(
            vote,
            materials_by_skill=materials,
            label="professional_votes[0]",
        )

    def test_eight_of_ten_short_shared_fourgram_forms_a_rejecting_cluster(
        self,
    ) -> None:
        vote, materials = self._clustered_uniform_vote(
            shared_count=8,
            template="xylophone quasar nebula zephyr",
            short_category=True,
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "source-free 4-gram short template"
        ):
            PANEL._validate_professional_v3_semantic_grounding(
                vote,
                materials_by_skill=materials,
                label="professional_votes[0]",
            )

    def test_uniform_template_outlier_cannot_exempt_low_grounding_members(
        self,
    ) -> None:
        vote, materials = self._semantic_grounding_fixture()
        anchors = {
            anchor["anchor_id"]: anchor for anchor in vote["evidence_anchors"]
        }
        assertions = [
            result["evidence_assertions"][0]
            for result in vote["criteria"].values()
        ]
        outlier_index = next(
            index
            for index, assertion in enumerate(assertions)
            if len(
                {
                    bigram
                    for anchor_id in assertion["evidence_anchor_ids"]
                    for sequence in PANEL._professional_v3_anchor_token_sequences(
                        anchor_id,
                        anchors_by_id=anchors,
                        materials_by_skill=materials,
                    )
                    for bigram in PANEL._professional_v3_ngrams(sequence, 2)
                }
            )
            >= 2
        )
        for index, assertion in enumerate(assertions):
            source_bigrams = sorted(
                {
                    bigram
                    for anchor_id in assertion["evidence_anchor_ids"]
                    for sequence in PANEL._professional_v3_anchor_token_sequences(
                        anchor_id,
                        anchors_by_id=anchors,
                        materials_by_skill=materials,
                    )
                    for bigram in PANEL._professional_v3_ngrams(sequence, 2)
                }
            )
            selected = source_bigrams[: 2 if index == outlier_index else 1]
            assertion["claim"] = (
                " and ".join(" ".join(bigram) for bigram in selected)
                + " uniform xylophone quasar nebula zephyr additional bounded "
                "wording remains here"
            )
        with self.assertRaisesRegex(PANEL.PanelReviewError, "source-free 5-gram"):
            PANEL._validate_professional_v3_semantic_grounding(
                vote,
                materials_by_skill=materials,
                label="professional_votes[0]",
            )

    def test_full_schema3_validator_accepts_grounded_positive_fixture(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        skill_id = sorted(state["bindings"])[0]
        voter_id = "professional-expert-1"
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            (
                _discovery,
                _discovery_path,
                _request,
                _request_path,
                capsule,
                capsule_path,
            ) = _materialize_empty_capsule_chain(
                validation_root=validation_root,
                packet=packet,
                packet_sha256="a" * 64,
                state=state,
                voter_id=voter_id,
                skill_ids=[skill_id],
            )
            capsule_ref = PANEL._artifact_reference(
                capsule_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                review_id=packet["review_id"],
            )
            projected = PANEL._professional_v2_projection_from_v3(packet)
            ballot = _professional_ballot(
                projected,
                "a" * 64,
                voter=1,
                skill_ids=[skill_id],
            )
            ballot["schema_version"] = (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            )
            ballot.pop("source_fingerprints")
            ballot["review_contract_fingerprint"] = packet[
                "review_contract_fingerprint"
            ]
            ballot["capsule"] = capsule_ref
            scoped = PANEL._professional_v3_target_scoped_capsule_materials(
                capsule
            )[skill_id]
            _ground_schema3_vote(ballot["professional_votes"][0], scoped)
            PANEL._validate_professional_completeness_ballot_v3(
                packet,
                ballot,
                packet_sha256="a" * 64,
                validation_root=validation_root,
                validate_packet_plan=False,
                packet_state=state,
                bound_capsule=(capsule_path, capsule_ref, capsule),
            )
            weak = copy.deepcopy(ballot)
            weak_vote = weak["professional_votes"][0]
            assertion = next(iter(weak_vote["criteria"].values()))[
                "evidence_assertions"
            ][0]
            first, second = _anchor_phrase(
                assertion["evidence_anchor_ids"][0],
                vote=weak_vote,
                materials_by_skill=scoped,
            )
            assertion["claim"] = (
                f"{first} xylophone quasar nebula separates {second} in a "
                "schema-three token-salad integration fixture."
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "exact non-generic source bigram"
            ):
                PANEL._validate_professional_completeness_ballot_v3(
                    packet,
                    weak,
                    packet_sha256="a" * 64,
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=state,
                    bound_capsule=(capsule_path, capsule_ref, capsule),
                )

    def test_create_only_json_write_rejects_race_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "round" / "packet.json"
            target.parent.mkdir(parents=True)
            self.assertFalse(target.exists())

            # Simulate another process winning after the caller's existence
            # check but before the immutable schema-3 write.
            target.write_text("racer-won\n", encoding="utf-8")
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "already exists"
            ):
                PANEL._write_json(
                    target,
                    {"winner": "must-not-overwrite"},
                    create_only=True,
                    validation_root=Path(raw),
                )
            self.assertEqual(
                "racer-won\n", target.read_text(encoding="utf-8")
            )

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            target = validation_root / "round" / "packet.json"
            barrier = threading.Barrier(2)
            outcomes: list[str] = []
            outcome_lock = threading.Lock()

            def writer(name: str) -> None:
                barrier.wait()
                try:
                    PANEL._write_json(
                        target,
                        {"winner": name},
                        compact=True,
                        create_only=True,
                        validation_root=validation_root,
                    )
                except PANEL.PanelReviewError:
                    outcome = "rejected"
                else:
                    outcome = name
                with outcome_lock:
                    outcomes.append(outcome)

            threads = [
                threading.Thread(target=writer, args=(name,))
                for name in ("one", "two")
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(1, outcomes.count("rejected"))
            winner = json.loads(target.read_text(encoding="utf-8"))["winner"]
            self.assertIn(winner, {"one", "two"})
            self.assertIn(winner, outcomes)

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            actual = validation_root / "actual"
            actual.mkdir()
            (validation_root / "round").symlink_to(
                actual, target_is_directory=True
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "symlink"
            ):
                PANEL._write_json(
                    validation_root / "round" / "packet.json",
                    {"must": "not-follow"},
                    create_only=True,
                    validation_root=validation_root,
                )
            self.assertFalse((actual / "packet.json").exists())

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            target = validation_root / "round" / "packet.json"
            target.parent.mkdir(parents=True)
            displaced = target.with_name("created-by-us.json")
            original_canonical = PANEL._canonical_artifact_path
            calls = 0

            def replace_after_write(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    target.rename(displaced)
                    target.write_text("competitor-won\n", encoding="utf-8")
                return original_canonical(*args, **kwargs)

            with mock.patch.object(
                PANEL,
                "_canonical_artifact_path",
                side_effect=replace_after_write,
            ), self.assertRaisesRegex(
                PANEL.PanelReviewError, "path changed"
            ):
                PANEL._write_json(
                    target,
                    {"created": "by-us"},
                    compact=True,
                    create_only=True,
                    validation_root=validation_root,
                )
            self.assertEqual(
                "competitor-won\n", target.read_text(encoding="utf-8")
            )
            self.assertTrue(displaced.is_file())

    def test_schema3_packet_review_id_must_be_canonical_slug(self) -> None:
        with self.assertRaisesRegex(PANEL.PanelReviewError, "canonical"):
            PANEL.prepare_professional_completeness_packet_v3(
                review_id="Not A Slug",
                created_on="2026-07-17",
            )
        packet = _bootstrap_packet()
        packet["review_id"] = "Not A Slug"
        with self.assertRaisesRegex(PANEL.PanelReviewError, "canonical"):
            PANEL._professional_v3_packet_state(
                packet,
                validation_root=PANEL.ROOT,
                artifact_path=None,
                validate_baseline=False,
            )

    def test_stale_contract_baseline_is_audit_only_full_fresh_checkpoint(self) -> None:
        current_packet = _bootstrap_packet()
        current_state = PANEL._professional_v3_packet_state(
            current_packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            decision_path, _old_packet, _old_decision = (
                _stale_contract_baseline_artifacts(
                    validation_root,
                    contract_fingerprint=R11_REVIEW_CONTRACT_FINGERPRINT,
                )
            )
            self.assertNotEqual(
                R11_REVIEW_CONTRACT_FINGERPRINT,
                current_packet["review_contract_fingerprint"],
            )
            baseline = PANEL._load_professional_v3_baseline(
                decision_path,
                validation_root=validation_root,
                forbidden_paths=set(),
                allow_stale_contract_checkpoint=True,
            )
            self.assertTrue(baseline["contract_mismatch_checkpoint"])
            self.assertEqual({}, baseline["snapshot"]["targets"])
            self.assertEqual({}, baseline["dependencies"])
            self.assertEqual({}, baseline["origins"])

            plan = PANEL._professional_v3_review_plan(
                current_bindings=current_state["bindings"],
                review_contract_fingerprint=current_packet[
                    "review_contract_fingerprint"
                ],
                baseline_state=baseline,
            )
            self.assertEqual(0, plan["plan_lineage_depth"])
            self.assertEqual([], plan["carried_targets"])
            self.assertEqual(189, len(plan["fresh_targets"]))
            self.assertTrue(
                all(
                    row["reason_codes"] == ["review-contract-changed"]
                    for row in plan["fresh_targets"]
                )
            )
            self.assertEqual(
                baseline["decision_ref"], plan["baseline"]["decision"]
            )
            self.assertEqual(
                baseline["packet_ref"], plan["baseline"]["packet"]
            )

            rebound_packet = copy.deepcopy(current_packet)
            rebound_packet["review_plan"] = plan
            PANEL._professional_v3_packet_state(
                rebound_packet,
                validation_root=validation_root,
                artifact_path=None,
                validate_baseline=True,
            )

            forged = copy.deepcopy(rebound_packet)
            forged["review_plan"]["fresh_targets"][0]["reason_codes"] = [
                "no-prior-baseline"
            ]
            without_fingerprint = copy.deepcopy(forged["review_plan"])
            without_fingerprint.pop("plan_fingerprint")
            forged["review_plan"]["plan_fingerprint"] = (
                PANEL._canonical_json_sha256(without_fingerprint)
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "exact carry recomputation"
            ):
                PANEL._professional_v3_packet_state(
                    forged,
                    validation_root=validation_root,
                    artifact_path=None,
                    validate_baseline=True,
                )

            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "cannot authorize carry"
            ):
                PANEL._load_professional_v3_baseline(
                    decision_path,
                    validation_root=validation_root,
                    forbidden_paths=set(),
                    allow_stale_contract_checkpoint=False,
                )

            forged_carry = copy.deepcopy(rebound_packet)
            moved = forged_carry["review_plan"]["fresh_targets"].pop(0)
            forged_carry["review_plan"]["carried_targets"] = [
                {
                    "skill_id": moved["skill_id"],
                    "review_unit_binding": current_state["bindings"][
                        moved["skill_id"]
                    ]["review_unit_binding"],
                    "origin_decision": baseline["decision_ref"],
                    "origin_target_decision_fingerprint": "f" * 64,
                }
            ]
            forged_carry["review_plan"]["plan_lineage_depth"] = 1
            forged_carry["review_plan"]["summary"] = {
                "total_target_count": 189,
                "fresh_target_count": 188,
                "carried_target_count": 1,
            }
            without_fingerprint = copy.deepcopy(forged_carry["review_plan"])
            without_fingerprint.pop("plan_fingerprint")
            forged_carry["review_plan"]["plan_fingerprint"] = (
                PANEL._canonical_json_sha256(without_fingerprint)
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "cannot authorize carry"
            ):
                PANEL._professional_v3_packet_state(
                    forged_carry,
                    validation_root=validation_root,
                    artifact_path=None,
                    validate_baseline=True,
                )

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            decision_path, _packet, _decision = (
                _stale_contract_baseline_artifacts(
                    validation_root,
                    contract_fingerprint=current_packet[
                        "review_contract_fingerprint"
                    ],
                )
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "decision method"
            ):
                PANEL._load_professional_v3_baseline(
                    decision_path,
                    validation_root=validation_root,
                    forbidden_paths=set(),
                    allow_stale_contract_checkpoint=True,
                )

    def test_fresh_target_rejects_fewer_than_three_ballots(self) -> None:
        target = _bootstrap_packet()["professional_targets"][0]
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "requires exactly 3 fresh ballots"
        ):
            PANEL._professional_v3_fresh_target_decision(
                target=target,
                assignments=[{"voter": {}}, {"voter": {}}],
            )

    def test_cli_bootstrap_capsule_template_and_validate(self) -> None:
        # Cache the code-aware contract against the repository before the
        # temporary validation root is installed.
        contract_fingerprint = (
            PANEL._professional_evidence_review_contract_fingerprint()
        )
        review_id = "schema3-cli-smoke"
        voter_id = "domain-one"
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            packet_relative = (
                f".rd-skills/expert-panel/{review_id}/packet.json"
            )
            discovery_relative = (
                f".rd-skills/expert-panel/{review_id}/discovery-capsules/{voter_id}.json"
            )
            request_relative = (
                f".rd-skills/expert-panel/{review_id}/candidate-requests/{voter_id}.json"
            )
            capsule_relative = (
                f".rd-skills/expert-panel/{review_id}/capsules/{voter_id}.json"
            )
            ballot_relative = (
                f".rd-skills/expert-panel/{review_id}/panel/{voter_id}.json"
            )
            with mock.patch.object(PANEL, "ROOT", validation_root), mock.patch.object(
                PANEL,
                "_professional_evidence_review_contract_fingerprint",
                return_value=contract_fingerprint,
            ):
                self.assertEqual(
                    0,
                    PANEL.main(
                        [
                            "prepare",
                            "--panel-kind",
                            PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                            "--schema-version",
                            "3",
                            "--review-id",
                            review_id,
                            "--created-on",
                            "2026-07-17",
                            "--out",
                            packet_relative,
                        ]
                    ),
                )
                packet_path = validation_root / packet_relative
                packet = json.loads(packet_path.read_text(encoding="utf-8"))
                skill_id = packet["review_plan"]["fresh_targets"][0]["skill_id"]
                target = next(
                    row
                    for row in packet["professional_targets"]
                    if row["skill_id"] == skill_id
                )
                self.assertEqual(
                    0,
                    PANEL.main(
                        [
                            "discovery-capsule",
                            "--packet",
                            packet_relative,
                            "--voter-id",
                            voter_id,
                            "--skill-id",
                            skill_id,
                            "--created-on",
                            "2026-07-17",
                            "--out",
                            discovery_relative,
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    PANEL.main(
                        [
                            "candidate-request",
                            "--packet",
                            packet_relative,
                            "--discovery-capsule",
                            discovery_relative,
                            "--voter-id",
                            voter_id,
                            "--created-on",
                            "2026-07-17",
                            "--out",
                            request_relative,
                        ]
                    ),
                )
                request_value = json.loads(
                    (validation_root / request_relative).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual([], request_value["reviewer_added_requests"])
                self.assertEqual(
                    [skill_id], request_value["assigned_fresh_target_ids"]
                )
                self.assertEqual(
                    0,
                    PANEL.main(
                        [
                            "capsule",
                            "--packet",
                            packet_relative,
                            "--discovery-capsule",
                            discovery_relative,
                            "--candidate-request",
                            request_relative,
                            "--voter-id",
                            voter_id,
                            "--created-on",
                            "2026-07-17",
                            "--out",
                            capsule_relative,
                        ]
                    ),
                )
                arguments = [
                    "template",
                    "--packet",
                    packet_relative,
                    "--capsule",
                    capsule_relative,
                    "--voter-id",
                    voter_id,
                    "--agent-id",
                    "agent-domain-one",
                    "--role",
                    "domain-reviewer",
                    "--expertise",
                    "Independent domain review.",
                    "--skill-id",
                    skill_id,
                    "--created-on",
                    "2026-07-17",
                    "--out",
                    ballot_relative,
                ]
                for tag in target["required_expertise_tags"]:
                    arguments.extend(["--expertise-tag", tag])
                self.assertEqual(0, PANEL.main(arguments))
                self.assertEqual(
                    0,
                    PANEL.main(
                        [
                            "validate",
                            "--packet",
                            packet_relative,
                            "--ballot-template",
                            ballot_relative,
                        ]
                    ),
                )
                template_path = validation_root / ballot_relative
                template_bytes = template_path.read_bytes()
                template_value = json.loads(template_bytes.decode("utf-8"))
                packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
                capsule_path = validation_root / capsule_relative
                capsule_value = json.loads(capsule_path.read_text(encoding="utf-8"))
                projected = PANEL._professional_v2_projection_from_v3(packet)
                completed = _professional_ballot(
                    projected,
                    packet_sha256,
                    voter=1,
                    skill_ids=[skill_id],
                )
                completed["schema_version"] = (
                    PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                )
                completed.pop("source_fingerprints")
                completed["created_on"] = template_value["created_on"]
                completed["review_contract_fingerprint"] = packet[
                    "review_contract_fingerprint"
                ]
                completed["capsule"] = template_value["capsule"]
                completed["voter"] = copy.deepcopy(template_value["voter"])
                for claim in completed["voter"]["qualification_claims"]:
                    tag = claim["expertise_tag"]
                    claim["qualification_basis"] = (
                        f"Reviewer declares bounded prior work in {tag} professional decision reviews."
                    )
                    claim["proof_limit"] = (
                        f"This static {tag} declaration cannot verify external identity credentials or experience."
                    )
                scoped = PANEL._professional_v3_target_scoped_capsule_materials(
                    capsule_value
                )[skill_id]
                _ground_schema3_vote(completed["professional_votes"][0], scoped)
                manifest_records = PANEL.reviewer_manifest.project_ballot_to_manifest(
                    completed,
                    template_sha256=hashlib.sha256(template_bytes).hexdigest(),
                )
                manifest_bytes = PANEL.reviewer_manifest.encode_manifest_records(
                    manifest_records
                )
                with tempfile.TemporaryDirectory() as manifest_raw:
                    manifest_path = Path(manifest_raw) / "reviewer-manifest.jsonl"
                    manifest_path.write_bytes(manifest_bytes)
                    materialize_arguments = [
                        "materialize-ballot",
                        "--packet",
                        packet_relative,
                        "--template",
                        ballot_relative,
                        "--template-sha256",
                        hashlib.sha256(template_bytes).hexdigest(),
                        "--manifest",
                        str(manifest_path),
                        "--manifest-size",
                        str(len(manifest_bytes)),
                        "--manifest-sha256",
                        hashlib.sha256(manifest_bytes).hexdigest(),
                        "--stdin-framing",
                        "raw",
                        "--out",
                        ballot_relative,
                    ]
                    self.assertEqual(0, PANEL.main(materialize_arguments))
                    self.assertEqual(1, PANEL.main(materialize_arguments))
                self.assertEqual(completed, json.loads(template_path.read_text("utf-8")))
                self.assertFalse(
                    (template_path.parent / f".{voter_id}.json.materialize.lock").exists()
                )
                self.assertEqual(
                    [],
                    list(template_path.parent.glob(f".{voter_id}.json.materialize-*.tmp")),
                )

    def test_capsule_projection_malformed_shape_is_panel_error(self) -> None:
        packet = _bootstrap_packet()
        capsule = {
            "schema_version": 3,
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
            "review_id": packet["review_id"],
            "created_on": "2026-07-17",
            "packet_sha256": "a" * 64,
            "review_contract_fingerprint": packet[
                "review_contract_fingerprint"
            ],
            "voter_id": "domain-one",
            "review_projection": {"assigned_fresh_target_ids": []},
            "limitations": ["malformed fixture"],
        }
        with self.assertRaises(PANEL.PanelReviewError):
            PANEL.validate_professional_review_capsule_v3(
                packet,
                capsule,
                packet_sha256="a" * 64,
            )

    def test_reviewer_added_candidate_chain_rejects_forged_or_stale_requests(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        target = next(
            row
            for row in packet["professional_targets"]
            if row["routing_adjacency"]["required_candidates"]
            and len(row["routing_adjacency"]["full_catalog_ranking"])
            > len(row["routing_adjacency"]["required_candidates"])
        )
        target_id = target["skill_id"]
        required_id = target["routing_adjacency"]["required_candidates"][0][
            "skill_id"
        ]
        required_ids = {
            row["skill_id"]
            for row in target["routing_adjacency"]["required_candidates"]
        }
        candidate_id = next(
            row["skill_id"]
            for row in target["routing_adjacency"]["full_catalog_ranking"]
            if row["skill_id"] not in required_ids
        )
        reason = (
            "Reviewer independently found a plausible responsibility boundary "
            "outside the machine-required candidate set."
        )
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            round_root = validation_root / packet["review_id"]
            discovery = PANEL.prepare_professional_discovery_capsule_v3(
                packet=packet,
                packet_sha256="a" * 64,
                voter_id="domain-one",
                assigned_skill_ids=[target_id],
                created_on="2026-07-17",
                validation_root=validation_root,
                validate_packet_plan=False,
                packet_state=state,
            )
            discovery_path = (
                round_root / "discovery-capsules" / "domain-one.json"
            )
            discovery_path.parent.mkdir(parents=True)
            _write_json(discovery_path, discovery)
            request = PANEL.prepare_professional_candidate_request_v3(
                packet=packet,
                packet_sha256="a" * 64,
                discovery_capsule_path=discovery_path,
                voter_id="domain-one",
                reviewer_added_requests_by_target={
                    target_id: [
                        {
                            "skill_id": candidate_id,
                            "discovery_reason": reason,
                        }
                    ]
                },
                created_on="2026-07-17",
                validation_root=validation_root,
                validate_packet_plan=False,
                packet_state=state,
            )
            self.assertEqual(
                reason, request["reviewer_added_requests"][0]["discovery_reason"]
            )
            self.assertEqual(
                candidate_id,
                request["reviewer_added_requests"][0]["ranking_evidence"][
                    "skill_id"
                ],
            )
            self.assertEqual(
                request,
                PANEL.validate_professional_candidate_request_v3(
                    packet,
                    request,
                    packet_sha256="a" * 64,
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=state,
                )[0],
            )
            request_path = round_root / "candidate-requests" / "domain-one.json"
            request_path.parent.mkdir(parents=True)
            _write_json(request_path, request)
            capsule = PANEL.prepare_professional_review_capsule_v3(
                packet=packet,
                packet_sha256="a" * 64,
                discovery_capsule_path=discovery_path,
                candidate_request_path=request_path,
                voter_id="domain-one",
                created_on="2026-07-17",
                validation_root=validation_root,
                validate_packet_plan=False,
                packet_state=state,
            )
            added_manifest = next(
                row
                for row in capsule["review_projection"]["targets"][0][
                    "candidate_material_manifest"
                ]
                if row["review_origin"] == "reviewer-added"
            )
            self.assertEqual(reason, added_manifest["discovery_reason"])

            mutations = []
            stale_ranking = copy.deepcopy(request)
            stale_ranking["reviewer_added_requests"][0]["ranking_evidence"][
                "rank"
            ] += 1
            mutations.append(stale_ranking)
            stale_material = copy.deepcopy(request)
            stale_material["reviewer_added_requests"][0][
                "material_fingerprint"
            ] = "f" * 64
            mutations.append(stale_material)
            duplicate = copy.deepcopy(request)
            duplicate["reviewer_added_requests"].append(
                copy.deepcopy(duplicate["reviewer_added_requests"][0])
            )
            mutations.append(duplicate)
            required = copy.deepcopy(request)
            required["reviewer_added_requests"][0]["skill_id"] = required_id
            mutations.append(required)
            outside = copy.deepcopy(request)
            outside["reviewer_added_requests"][0]["skill_id"] = (
                "outside-catalog"
            )
            mutations.append(outside)
            cross_voter = copy.deepcopy(request)
            cross_voter["voter_id"] = "domain-two"
            mutations.append(cross_voter)
            stale_packet = copy.deepcopy(request)
            stale_packet["packet_sha256"] = "b" * 64
            mutations.append(stale_packet)
            forged_predecessor = copy.deepcopy(request)
            forged_predecessor["discovery_capsule"]["sha256"] = "c" * 64
            mutations.append(forged_predecessor)
            for index, value in enumerate(mutations):
                with self.subTest(mutation=index), self.assertRaises(
                    PANEL.PanelReviewError
                ):
                    PANEL.validate_professional_candidate_request_v3(
                        packet,
                        value,
                        packet_sha256="a" * 64,
                        validation_root=validation_root,
                        validate_packet_plan=False,
                        packet_state=state,
                    )

            stale_final = copy.deepcopy(capsule)
            stale_final["candidate_request"]["sha256"] = "d" * 64
            with self.assertRaises(PANEL.PanelReviewError):
                PANEL.validate_professional_review_capsule_v3(
                    packet,
                    stale_final,
                    packet_sha256="a" * 64,
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=state,
                )

        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            PANEL._parse_args(
                [
                    "capsule",
                    "--packet",
                    "packet.json",
                    "--discovery-capsule",
                    "discovery.json",
                    "--candidate-request",
                    "request.json",
                    "--voter-id",
                    "domain-one",
                    "--reviewer-added-candidate",
                    f"{target_id}={candidate_id}",
                    "--created-on",
                    "2026-07-17",
                    "--out",
                    "capsule.json",
                ]
            )

    def test_cost_projections_exclude_administrative_padding(self) -> None:
        packet = _bootstrap_packet()
        projection = PANEL._professional_v3_full_rereview_input_projection(
            packet
        )
        padded = copy.deepcopy(packet)
        padded["review_id"] = "x" * 50_000
        padded["limitations"] = ["x" * 50_000]
        self.assertEqual(
            projection,
            PANEL._professional_v3_full_rereview_input_projection(padded),
        )
        with self.assertRaisesRegex(PANEL.PanelReviewError, "canonical"):
            PANEL._professional_v3_packet_state(
                padded,
                validation_root=PANEL.ROOT,
                artifact_path=None,
                validate_baseline=False,
            )

    def test_deduplicated_full_capsule_matches_full_rereview_proxy(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        all_skill_ids = sorted(state["bindings"])
        full_projection = PANEL._professional_v3_capsule_projection_from_packet(
            packet=packet,
            assigned_skill_ids=all_skill_ids,
            reviewer_added_requests_by_target=None,
            bindings=state["bindings"],
        )
        capsule = {
            "review_contract_fingerprint": packet[
                "review_contract_fingerprint"
            ],
            "review_projection": full_projection,
        }
        capsule_projection = PANEL._professional_v3_capsule_input_projection(
            capsule
        )
        full_input_projection = PANEL._professional_v3_full_rereview_input_projection(
            packet,
            bindings=state["bindings"],
        )
        capsule_bytes = len(
            PANEL.professional_carry.canonical_json_bytes(capsule_projection)
        )
        full_bytes = len(
            PANEL.professional_carry.canonical_json_bytes(full_input_projection)
        )
        self.assertLessEqual(capsule_bytes / full_bytes, 1.05)
        self.assertEqual(full_input_projection, capsule_projection)
        self.assertEqual(
            189,
            len(capsule["review_projection"]["material_catalog"]),
        )

        local_projection = PANEL._professional_v3_capsule_projection_from_packet(
            packet=packet,
            assigned_skill_ids=all_skill_ids[:1],
            reviewer_added_requests_by_target=None,
            bindings=state["bindings"],
        )
        local_capsule = {
            "review_contract_fingerprint": packet[
                "review_contract_fingerprint"
            ],
            "review_projection": local_projection,
        }
        local_bytes = len(
            PANEL.professional_carry.canonical_json_bytes(
                PANEL._professional_v3_capsule_input_projection(local_capsule)
            )
        )
        self.assertLess(local_bytes, capsule_bytes)

        full_blocks = PANEL._professional_v3_full_rereview_input_blocks(
            packet, bindings=state["bindings"]
        )
        full_block_bytes = sum(
            block["canonical_json_bytes_proxy"] for block in full_blocks
        )
        local_discovery = PANEL._professional_v3_discovery_projection_from_packet(
            packet=packet,
            assigned_skill_ids=all_skill_ids[:1],
            bindings=state["bindings"],
        )
        local_blocks = PANEL._professional_v3_effective_input_blocks(
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
            discovery_projection=local_discovery,
            assigned_skill_ids=all_skill_ids[:1],
            reviewer_added_requests=[],
            final_projection=local_projection,
        )
        local_block_bytes = sum(
            block["canonical_json_bytes_proxy"] for block in local_blocks
        )

        def decision_row(
            row_skill_id: str,
            *,
            mode: str,
            per_reviewer_bytes: int,
            blocks: list[dict] | None = None,
            voter_ids: tuple[str, ...] = (
                "architecture-one",
                "domain-one",
                "domain-two",
            ),
        ) -> dict:
            provenance = {"mode": mode, "origin_depth": 0 if mode == "fresh" else 1}
            if mode == "fresh":
                provenance["evidence"] = [
                    {
                        "voter_id": voter_id,
                        "ballot": {
                            "path": (
                                f"{packet['review_id']}/panel/{voter_id}.json"
                            ),
                            "sha256": hashlib.sha256(
                                f"ballot:{voter_id}".encode("utf-8")
                            ).hexdigest(),
                            "kind": PANEL.PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                            "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                            "review_id": packet["review_id"],
                        },
                        "capsule": {
                            "path": (
                                f"{packet['review_id']}/capsules/{voter_id}.json"
                            ),
                            "sha256": hashlib.sha256(
                                f"capsule:{voter_id}".encode("utf-8")
                            ).hexdigest(),
                            "kind": PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                            "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                            "review_id": packet["review_id"],
                        },
                    }
                    for voter_id in voter_ids
                ]
            return {
                "skill_id": row_skill_id,
                "final_disposition": "accepted-current-professional-completeness",
                "ordinary_criterion_disposition": (
                    "accepted-current-professional-completeness"
                ),
                "winning_disposition": (
                    "accepted-current-professional-completeness"
                ),
                "evidence_metrics": {"criterion_result_count": 30},
                "provenance": provenance,
            }

        def decision_voter(
            voter_id: str,
            *,
            assigned_skill_ids: list[str],
            per_reviewer_bytes: int,
            blocks: list[dict],
        ) -> dict:
            evidence = decision_row(
                assigned_skill_ids[0],
                mode="fresh",
                per_reviewer_bytes=per_reviewer_bytes,
                blocks=blocks,
                voter_ids=(voter_id,),
            )["provenance"]["evidence"][0]
            return {
                "voter_id": voter_id,
                "agent_id": f"agent-{voter_id}",
                "role": f"role-{voter_id}",
                "expertise": f"expertise-{voter_id}",
                "independent_review": True,
                "expertise_tags": ["skill-reference-architecture"],
                "qualification_claims": ["fixture qualification claim"],
                "assigned_skill_ids": assigned_skill_ids,
                "ballot": evidence["ballot"],
                "capsule": evidence["capsule"],
                "capsule_canonical_json_bytes_proxy": per_reviewer_bytes,
                "capsule_input_blocks_proxy": copy.deepcopy(blocks),
            }

        full_rows = [
            decision_row(
                row_skill_id,
                mode="fresh",
                per_reviewer_bytes=capsule_bytes,
                blocks=full_blocks,
            )
            for row_skill_id in all_skill_ids
        ]
        full_summary = PANEL._professional_v3_summary_from_rows(
            decisions=full_rows,
            packet=packet,
            decision_voters=[
                decision_voter(
                    voter_id,
                    assigned_skill_ids=all_skill_ids,
                    per_reviewer_bytes=capsule_bytes,
                    blocks=full_blocks,
                )
                for voter_id in (
                    "architecture-one",
                    "domain-one",
                    "domain-two",
                )
            ],
        )["review_cost"]
        self.assertEqual(
            3 * full_block_bytes,
            full_summary["canonical_capsule_input_bytes_proxy"],
        )
        self.assertEqual(
            3 * full_block_bytes,
            full_summary[
                "full_rereview_deduplicated_capsule_input_bytes_proxy"
            ],
        )
        self.assertEqual(1_000_000, full_summary["input_ratio_ppm"])

        local_rows = [
            decision_row(
                row_skill_id,
                mode="fresh" if index == 0 else "carried-forward",
                per_reviewer_bytes=local_bytes,
                blocks=local_blocks,
            )
            for index, row_skill_id in enumerate(all_skill_ids)
        ]
        local_summary = PANEL._professional_v3_summary_from_rows(
            decisions=local_rows,
            packet=packet,
            decision_voters=[
                decision_voter(
                    voter_id,
                    assigned_skill_ids=all_skill_ids[:1],
                    per_reviewer_bytes=local_bytes,
                    blocks=local_blocks,
                )
                for voter_id in (
                    "architecture-one",
                    "domain-one",
                    "domain-two",
                )
            ],
        )["review_cost"]
        self.assertEqual(
            3 * local_block_bytes,
            local_summary["canonical_capsule_input_bytes_proxy"],
        )
        self.assertEqual(
            local_block_bytes * 1_000_000 // full_block_bytes,
            local_summary["input_ratio_ppm"],
        )

        voter_ids = tuple(f"reviewer-{index}" for index in range(5))
        assignments_by_voter = {voter_id: [] for voter_id in voter_ids}
        voters_by_skill: dict[str, tuple[str, ...]] = {}
        for index, skill_id in enumerate(all_skill_ids):
            assigned_voters = tuple(
                voter_ids[(index + offset) % len(voter_ids)]
                for offset in range(3)
            )
            voters_by_skill[skill_id] = assigned_voters
            for voter_id in assigned_voters:
                assignments_by_voter[voter_id].append(skill_id)
        blocks_by_voter = {}
        sizes_by_voter = {}
        for voter_id, assigned in assignments_by_voter.items():
            discovery = PANEL._professional_v3_discovery_projection_from_packet(
                packet=packet,
                assigned_skill_ids=assigned,
                bindings=state["bindings"],
            )
            final = PANEL._professional_v3_capsule_projection_from_packet(
                packet=packet,
                assigned_skill_ids=assigned,
                reviewer_added_requests_by_target=None,
                bindings=state["bindings"],
            )
            blocks_by_voter[voter_id] = PANEL._professional_v3_effective_input_blocks(
                review_contract_fingerprint=packet[
                    "review_contract_fingerprint"
                ],
                discovery_projection=discovery,
                assigned_skill_ids=assigned,
                reviewer_added_requests=[],
                final_projection=final,
            )
            sizes_by_voter[voter_id] = len(
                PANEL.professional_carry.canonical_json_bytes(final)
            )

        five_pool_rows = []
        for skill_id in all_skill_ids:
            assigned_voters = voters_by_skill[skill_id]
            row = decision_row(
                skill_id,
                mode="fresh",
                per_reviewer_bytes=1,
                voter_ids=assigned_voters,
            )
            five_pool_rows.append(row)
        five_pool_voters = [
            decision_voter(
                voter_id,
                assigned_skill_ids=assignments_by_voter[voter_id],
                per_reviewer_bytes=sizes_by_voter[voter_id],
                blocks=blocks_by_voter[voter_id],
            )
            for voter_id in voter_ids
        ]
        five_pool_summary = PANEL._professional_v3_summary_from_rows(
            decisions=five_pool_rows,
            packet=packet,
            decision_voters=five_pool_voters,
        )["review_cost"]
        self.assertEqual(
            five_pool_summary[
                "full_rereview_deduplicated_capsule_input_bytes_proxy"
            ],
            five_pool_summary["canonical_capsule_input_bytes_proxy"],
        )
        self.assertEqual(1_000_000, five_pool_summary["input_ratio_ppm"])
        self.assertTrue(
            all(
                set(evidence)
                == PANEL.PROFESSIONAL_V3_PROVENANCE_EVIDENCE_FIELDS
                for row in five_pool_rows
                for evidence in row["provenance"]["evidence"]
            )
        )
        top_level_manifest_bytes = sum(
            len(
                PANEL.professional_carry.canonical_json_bytes(
                    voter["capsule_input_blocks_proxy"]
                )
            )
            for voter in five_pool_voters
        )
        repeated_target_manifest_bytes = sum(
            len(
                PANEL.professional_carry.canonical_json_bytes(
                    blocks_by_voter[evidence["voter_id"]]
                )
            )
            for row in five_pool_rows
            for evidence in row["provenance"]["evidence"]
        )
        self.assertLess(top_level_manifest_bytes, repeated_target_manifest_bytes)

    def test_capsule_catalog_rejects_missing_duplicate_and_unused_material(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        skill_id = sorted(state["bindings"])[0]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        validation_root = Path(temporary.name)
        _discovery, _discovery_path, _request, _request_path, capsule, _capsule_path = (
            _materialize_empty_capsule_chain(
                validation_root=validation_root,
                packet=packet,
                packet_sha256="a" * 64,
                state=state,
                voter_id="domain-one",
                skill_ids=[skill_id],
            )
        )
        self.assertIs(
            capsule,
            PANEL.validate_professional_review_capsule_v3(
                packet,
                capsule,
                packet_sha256="a" * 64,
                validation_root=validation_root,
                validate_packet_plan=False,
                packet_state=state,
            ),
        )
        catalog = capsule["review_projection"]["material_catalog"]

        missing = copy.deepcopy(capsule)
        missing["review_projection"]["material_catalog"] = [
            row for row in catalog if row["skill_id"] != skill_id
        ]
        duplicate = copy.deepcopy(capsule)
        duplicate["review_projection"]["material_catalog"].append(
            copy.deepcopy(catalog[0])
        )
        unused = copy.deepcopy(capsule)
        full_catalog = PANEL._professional_v3_full_rereview_input_projection(
            packet,
            bindings=state["bindings"],
        )["review_projection"]["material_catalog"]
        local_ids = {row["skill_id"] for row in catalog}
        unused_material = next(
            row for row in full_catalog if row["skill_id"] not in local_ids
        )
        unused["review_projection"]["material_catalog"].append(
            copy.deepcopy(unused_material)
        )
        unused["review_projection"]["material_catalog"].sort(
            key=lambda row: row["skill_id"]
        )

        for label, value, message in (
            ("missing", missing, "missing target-scoped material"),
            ("duplicate", duplicate, "not canonical"),
            ("unused", unused, "unused material"),
        ):
            with self.subTest(label=label), self.assertRaisesRegex(
                PANEL.PanelReviewError, message
            ):
                PANEL._professional_v3_target_scoped_capsule_materials(value)
            with self.subTest(label=f"validator-{label}"), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL.validate_professional_review_capsule_v3(
                    packet,
                    value,
                    packet_sha256="a" * 64,
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=state,
                )

    def test_supplied_packet_state_cannot_replace_packet_materials(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        skill_id = sorted(state["bindings"])[0]
        capsule = PANEL.prepare_professional_discovery_capsule_v3(
            packet=packet,
            packet_sha256="a" * 64,
            voter_id="domain-one",
            assigned_skill_ids=[skill_id],
            created_on="2026-07-17",
            validate_packet_plan=False,
            packet_state=state,
        )

        forged_state = copy.deepcopy(state)
        material = forged_state["base_targets"][0]["root"]
        material["content"] += "\nforged review material\n"
        material["line_count"] = len(material["content"].splitlines())
        material["sha256"] = hashlib.sha256(
            material["content"].encode("utf-8")
        ).hexdigest()
        bindings, snapshot = PANEL._professional_v3_binding_state(
            forged_state["base_targets"],
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
        )
        forged_state["bindings"] = bindings
        forged_state["snapshot"] = snapshot
        self.assertEqual(state["plan"], forged_state["plan"])
        self.assertNotEqual(state["bindings"], forged_state["bindings"])

        with self.subTest(entry="prepare"), self.assertRaisesRegex(
            PANEL.PanelReviewError, "authoritative packet-derived state"
        ):
            PANEL.prepare_professional_discovery_capsule_v3(
                packet=packet,
                packet_sha256="a" * 64,
                voter_id="domain-one",
                assigned_skill_ids=[skill_id],
                created_on="2026-07-17",
                validate_packet_plan=False,
                packet_state=forged_state,
            )

        with self.subTest(entry="validate"), self.assertRaisesRegex(
            PANEL.PanelReviewError, "authoritative packet-derived state"
        ):
            PANEL.validate_professional_discovery_capsule_v3(
                packet,
                capsule,
                packet_sha256="a" * 64,
                validate_packet_plan=False,
                packet_state=forged_state,
            )

        with self.subTest(entry="ballot-validator"), self.assertRaisesRegex(
            PANEL.PanelReviewError, "authoritative packet-derived state"
        ):
            PANEL._validate_professional_completeness_ballot_v3(
                packet,
                {},
                packet_sha256="a" * 64,
                validate_packet_plan=False,
                packet_state=forged_state,
            )

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            packet_path = validation_root / packet["review_id"] / "packet.json"
            packet_path.parent.mkdir(parents=True)
            _write_json(packet_path, packet)
            with self.subTest(entry="streaming-aggregate"), self.assertRaisesRegex(
                PANEL.PanelReviewError, "authoritative packet-derived state"
            ):
                PANEL.aggregate_professional_completeness_ballot_paths_v3(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_paths=[],
                    decided_on="2026-07-17",
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=forged_state,
                )

    def test_canonical_packet_state_handle_is_immutable_and_packet_bound(self) -> None:
        packet = _bootstrap_packet()
        raw_state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        handle = PANEL._professional_v3_canonical_packet_state(
            packet,
            supplied_state=raw_state,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        skill_id = sorted(raw_state["bindings"])[0]
        capsule = PANEL.prepare_professional_discovery_capsule_v3(
            packet=packet,
            packet_sha256="a" * 64,
            voter_id="domain-one",
            assigned_skill_ids=[skill_id],
            created_on="2026-07-17",
            validate_packet_plan=False,
            packet_state=handle,
        )

        for attribute, value in (
            ("state", copy.deepcopy(raw_state)),
            ("packet", copy.deepcopy(packet)),
        ):
            with self.subTest(attribute=attribute), self.assertRaises(
                AttributeError
            ):
                object.__setattr__(handle, attribute, value)
        with self.assertRaises(TypeError):
            handle.state["bindings"] = {}
        with self.assertRaises(TypeError):
            handle.packet["professional_targets"] = []

        changed_packet = copy.deepcopy(packet)
        changed_packet["professional_targets"][0]["root"]["content"] += (
            "\npost-issuance packet mutation\n"
        )
        entry_calls = {
            "prepare": lambda: PANEL.prepare_professional_discovery_capsule_v3(
                packet=changed_packet,
                packet_sha256="a" * 64,
                voter_id="domain-one",
                assigned_skill_ids=[skill_id],
                created_on="2026-07-17",
                validate_packet_plan=False,
                packet_state=handle,
            ),
            "validate": lambda: PANEL.validate_professional_discovery_capsule_v3(
                changed_packet,
                capsule,
                packet_sha256="a" * 64,
                validate_packet_plan=False,
                packet_state=handle,
            ),
            "ballot": lambda: PANEL._validate_professional_completeness_ballot_v3(
                changed_packet,
                {},
                packet_sha256="a" * 64,
                validate_packet_plan=False,
                packet_state=handle,
            ),
        }
        for entry, call in entry_calls.items():
            with self.subTest(entry=entry), self.assertRaisesRegex(
                PANEL.PanelReviewError, "belongs to another packet"
            ):
                call()

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            packet_path = (
                validation_root / packet["review_id"] / "packet.json"
            )
            packet_path.parent.mkdir(parents=True)
            _write_json(packet_path, changed_packet)
            with self.subTest(entry="streaming-aggregate"), self.assertRaisesRegex(
                PANEL.PanelReviewError, "belongs to another packet"
            ):
                PANEL.aggregate_professional_completeness_ballot_paths_v3(
                    packet=changed_packet,
                    packet_path=packet_path,
                    ballot_paths=[],
                    decided_on="2026-07-17",
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=handle,
                )

    def test_public_decision_validator_separates_plan_and_evidence_state(
        self,
    ) -> None:
        packet = _bootstrap_packet()
        packet_ref = {
            "path": f"{packet['review_id']}/packet.json",
            "sha256": "a" * 64,
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
            "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            "review_id": packet["review_id"],
        }
        record = {
            "schema_version": (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ),
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            "review_id": packet["review_id"],
            "decided_on": "2026-07-17",
            "decision_method": (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
            ),
            "review_contract_fingerprint": packet[
                "review_contract_fingerprint"
            ],
            "panel_contract": packet["panel_contract"],
            "packet": packet_ref,
            "voters": [],
            "professional_decisions": [],
            "summary": {},
            "limitations": ["Packet-state handoff regression fixture."],
        }
        strong_state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=True,
        )
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            packet_path = validation_root / packet_ref["path"]
            decision_path = (
                validation_root
                / packet["review_id"]
                / "panel"
                / "decision.json"
            )
            with (
                mock.patch.object(
                    PANEL,
                    "_professional_v3_bind_json_artifact_path",
                    return_value=(decision_path, {"sha256": "b" * 64}, record),
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_v3_load_packet_for_decision",
                    side_effect=[
                        (packet_path, packet_ref, packet, strong_state),
                        (packet_path, packet_ref, packet, strong_state),
                    ],
                ) as load_packet,
                mock.patch.object(
                    PANEL,
                    "_professional_v3_cached_json_artifact",
                    return_value=(packet_path, packet_ref, packet),
                ) as bind_packet,
                mock.patch.object(
                    PANEL,
                    "_professional_v3_canonical_packet_state",
                    wraps=PANEL._professional_v3_canonical_packet_state,
                ) as seal_state,
                mock.patch.object(
                    PANEL,
                    "_professional_v3_validate_decision_projection",
                ),
                mock.patch.object(
                    PANEL,
                    "aggregate_professional_completeness_ballot_paths_v3",
                    return_value=record,
                ) as aggregate,
            ):
                self.assertIs(
                    record,
                    PANEL._validate_professional_completeness_decision_record(
                        record,
                        record_path=decision_path,
                        validation_root=validation_root,
                    ),
                )
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "must be a sealed canonical handle",
                ):
                    PANEL._validate_professional_completeness_decision_record_v3(
                        record,
                        record_path=decision_path,
                        validation_root=validation_root,
                        validate_packet_baseline=False,
                        canonical_packet_state=strong_state,
                    )

        aggregate_handle = aggregate.call_args.kwargs["packet_state"]
        self.assertIsInstance(
            aggregate_handle,
            PANEL._ProfessionalV3CanonicalPacketState,
        )
        self.assertIs(
            aggregate.call_args.kwargs["packet"],
            aggregate_handle.packet,
        )
        try:
            aggregate_handle._validate_binding(
                aggregate_handle.packet,
                require_baseline=True,
            )
        except PANEL.PanelReviewError as exc:
            self.fail(f"public validator weakened baseline provenance: {exc}")

        load_packet.assert_called_once()
        self.assertTrue(
            load_packet.call_args.kwargs["validate_baseline"]
        )
        bind_packet.assert_called_once()
        self.assertEqual(2, seal_state.call_count)
        issue_call, adopt_call = seal_state.call_args_list
        self.assertTrue(issue_call.kwargs["validate_baseline"])
        self.assertFalse(
            adopt_call.kwargs["validate_baseline"]
        )
        self.assertIs(
            adopt_call.kwargs["supplied_state"],
            aggregate_handle,
        )
        self.assertFalse(aggregate.call_args.kwargs["validate_packet_plan"])
        self.assertIs(
            load_packet.call_args.kwargs["invocation_cache"],
            aggregate.call_args.kwargs["invocation_cache"],
        )

    def test_decision_validator_reuses_strong_packet_state_for_weak_aggregate(
        self,
    ) -> None:
        packet = _bootstrap_packet()
        packet_ref = {
            "path": f"{packet['review_id']}/packet.json",
            "sha256": "a" * 64,
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
            "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            "review_id": packet["review_id"],
        }
        record = {
            "schema_version": (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ),
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            "review_id": packet["review_id"],
            "decided_on": "2026-07-17",
            "decision_method": (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
            ),
            "review_contract_fingerprint": packet[
                "review_contract_fingerprint"
            ],
            "panel_contract": packet["panel_contract"],
            "packet": packet_ref,
            "voters": [],
            "professional_decisions": [],
            "summary": {},
            "limitations": ["Strong-to-weak packet-state handoff fixture."],
        }
        strong_state = {"validation_strength": "baseline-validated"}
        sealed_packet = copy.deepcopy(packet)
        sealed_state = {"validation_strength": "sealed"}
        sealed_handle = types.SimpleNamespace(
            packet=sealed_packet,
            state=sealed_state,
        )
        cache = PANEL._professional_v3_invocation_cache()

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            packet_path = validation_root / packet_ref["path"]
            decision_path = (
                validation_root
                / packet["review_id"]
                / "panel"
                / "decision.json"
            )
            decision_path.parent.mkdir(parents=True)
            with (
                mock.patch.object(
                    PANEL,
                    "_professional_v3_bind_json_artifact_path",
                    return_value=(
                        decision_path,
                        {"sha256": "b" * 64},
                        record,
                    ),
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_v3_load_packet_for_decision",
                    return_value=(
                        packet_path,
                        packet_ref,
                        packet,
                        strong_state,
                    ),
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_v3_canonical_packet_state",
                    return_value=sealed_handle,
                ) as seal_state,
                mock.patch.object(
                    PANEL,
                    "_professional_v3_validate_decision_projection",
                ) as validate_projection,
                mock.patch.object(
                    PANEL,
                    "aggregate_professional_completeness_ballot_paths_v3",
                    return_value=record,
                ) as aggregate,
            ):
                self.assertIs(
                    record,
                    PANEL._validate_professional_completeness_decision_record_v3(
                        record,
                        record_path=decision_path,
                        validation_root=validation_root,
                        validate_packet_baseline=True,
                        invocation_cache=cache,
                    ),
                )

        seal_state.assert_called_once_with(
            packet,
            supplied_state=strong_state,
            validation_root=validation_root,
            artifact_path=packet_path,
            validate_baseline=True,
            forbidden_paths={decision_path},
            invocation_cache=cache,
            validation_mode=PANEL.VALIDATION_MODE_CURRENT,
        )
        validate_projection.assert_called_once_with(
            record=record,
            packet=sealed_packet,
            state=sealed_state,
        )
        aggregate.assert_called_once()
        self.assertIs(aggregate.call_args.kwargs["packet"], sealed_packet)
        self.assertFalse(aggregate.call_args.kwargs["validate_packet_plan"])
        self.assertIs(
            aggregate.call_args.kwargs["packet_state"], sealed_handle
        )
        self.assertIs(aggregate.call_args.kwargs["invocation_cache"], cache)

    def test_all_carry_origin_cache_miss_recomputes_fresh_evidence(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        skill_id = sorted(state["bindings"])[0]
        target = next(
            row
            for row in packet["professional_targets"]
            if row["skill_id"] == skill_id
        )
        projected_packet = PANEL._professional_v2_projection_from_v3(packet)

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            round_root = validation_root / packet["review_id"]
            packet_path = round_root / "packet.json"
            packet_path.parent.mkdir(parents=True)
            _write_json(packet_path, packet)
            packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            packet_ref = PANEL._artifact_reference(
                packet_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                review_id=packet["review_id"],
            )

            assignments = []
            decision_voters = []
            ballot_artifacts = []
            for voter in range(1, 4):
                voter_id = f"professional-expert-{voter}"
                (
                    _discovery,
                    _discovery_path,
                    _request,
                    _request_path,
                    capsule,
                    capsule_path,
                ) = _materialize_empty_capsule_chain(
                    validation_root=validation_root,
                    packet=packet,
                    packet_sha256=packet_sha256,
                    state=state,
                    voter_id=voter_id,
                    skill_ids=[skill_id],
                )
                capsule_ref = PANEL._artifact_reference(
                    capsule_path,
                    validation_root=validation_root,
                    kind=PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                    axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                    review_id=packet["review_id"],
                )

                ballot = _professional_ballot(
                    projected_packet,
                    packet_sha256,
                    voter=voter,
                    skill_ids=[skill_id],
                )
                ballot["schema_version"] = (
                    PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                )
                ballot.pop("source_fingerprints")
                ballot["review_contract_fingerprint"] = packet[
                    "review_contract_fingerprint"
                ]
                ballot["capsule"] = capsule_ref
                scoped = PANEL._professional_v3_target_scoped_capsule_materials(
                    capsule
                )[skill_id]
                _ground_schema3_vote(ballot["professional_votes"][0], scoped)
                ballot_path = round_root / "panel" / f"{voter_id}.json"
                ballot_path.parent.mkdir(parents=True, exist_ok=True)
                _write_json(ballot_path, ballot)
                ballot_ref = PANEL._artifact_reference(
                    ballot_path,
                    validation_root=validation_root,
                    kind=PANEL.PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                    axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                    review_id=packet["review_id"],
                )
                assignments.append(
                    {
                        "voter": ballot["voter"],
                        "vote": ballot["professional_votes"][0],
                        "ballot_ref": ballot_ref,
                        "capsule_ref": capsule_ref,
                        "capsule_bytes_proxy": len(
                            PANEL.professional_carry.canonical_json_bytes(
                                PANEL._professional_v3_capsule_input_projection(
                                    capsule
                                )
                            )
                        ),
                        "capsule_input_blocks_proxy": (
                            PANEL._professional_v3_effective_capsule_input_blocks(
                                discovery_capsule=_discovery,
                                candidate_request=_request,
                                capsule=capsule,
                            )
                        ),
                    }
                )
                decision_voters.append(
                    {
                        **ballot["voter"],
                        "assigned_skill_ids": [skill_id],
                        "ballot": ballot_ref,
                        "capsule": capsule_ref,
                        "capsule_canonical_json_bytes_proxy": assignments[-1][
                            "capsule_bytes_proxy"
                        ],
                        "capsule_input_blocks_proxy": copy.deepcopy(
                            assignments[-1]["capsule_input_blocks_proxy"]
                        ),
                    }
                )
                ballot_artifacts.append((ballot_path, ballot, scoped))

            stored = PANEL._professional_v3_fresh_target_decision(
                target=target,
                assignments=assignments,
            )
            record = {
                "schema_version": (
                    PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                ),
                "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                "review_id": packet["review_id"],
                "decided_on": "2026-07-17",
                "decision_method": (
                    PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
                ),
                "review_contract_fingerprint": packet[
                    "review_contract_fingerprint"
                ],
                "panel_contract": packet["panel_contract"],
                "packet": packet_ref,
                "voters": decision_voters,
                "professional_decisions": [stored],
                "summary": {},
                "limitations": ["Target-scoped origin cache-miss fixture."],
            }
            decision_path = round_root / "panel" / "decision.json"
            _write_json(decision_path, record)
            decision_ref = PANEL._artifact_reference(
                decision_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                review_id=packet["review_id"],
            )
            cache = PANEL._professional_v3_invocation_cache()
            with mock.patch.object(
                PANEL,
                "_professional_v3_validate_decision_projection",
                return_value=None,
            ):
                result = PANEL._load_professional_v3_fresh_origin_target(
                    origin_reference=decision_ref,
                    skill_id=skill_id,
                    expected_target_decision_fingerprint=stored[
                        "target_decision_fingerprint"
                    ],
                    validation_root=validation_root,
                    forbidden_paths=set(),
                    invocation_cache=cache,
                )
            self.assertEqual(stored, result["target_row"])
            self.assertEqual(1, len(cache["origin_rounds"]))
            context = next(iter(cache["origin_rounds"].values()))
            self.assertIsInstance(
                context["canonical_state"],
                PANEL._ProfessionalV3CanonicalPacketState,
            )
            self.assertEqual(state["plan"], context["state"]["plan"])

            weak_path, original_ballot, weak_materials = ballot_artifacts[0]
            weak_ballot = copy.deepcopy(original_ballot)
            weak_vote = weak_ballot["professional_votes"][0]
            weak_assertion = next(iter(weak_vote["criteria"].values()))[
                "evidence_assertions"
            ][0]
            first, second = _anchor_phrase(
                weak_assertion["evidence_anchor_ids"][0],
                vote=weak_vote,
                materials_by_skill=weak_materials,
            )
            weak_assertion["claim"] = (
                f"{first} xylophone quasar nebula separates {second} while "
                "retaining a current-fingerprint token salad."
            )
            _write_json(weak_path, weak_ballot)
            weak_ballot_ref = PANEL._artifact_reference(
                weak_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                review_id=packet["review_id"],
            )
            weak_assignments = copy.deepcopy(assignments)
            weak_assignments[0]["vote"] = weak_vote
            weak_assignments[0]["ballot_ref"] = weak_ballot_ref
            weak_voters = copy.deepcopy(decision_voters)
            weak_voters[0]["ballot"] = weak_ballot_ref
            weak_stored = PANEL._professional_v3_fresh_target_decision(
                target=target,
                assignments=weak_assignments,
            )
            weak_record = {
                **record,
                "voters": weak_voters,
                "professional_decisions": [weak_stored],
            }
            _write_json(decision_path, weak_record)
            weak_decision_ref = PANEL._artifact_reference(
                decision_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                review_id=packet["review_id"],
            )
            with mock.patch.object(
                PANEL,
                "_professional_v3_validate_decision_projection",
                return_value=None,
            ), self.assertRaisesRegex(
                PANEL.PanelReviewError, "exact non-generic source bigram"
            ):
                PANEL._load_professional_v3_fresh_origin_target(
                    origin_reference=weak_decision_ref,
                    skill_id=skill_id,
                    expected_target_decision_fingerprint=weak_stored[
                        "target_decision_fingerprint"
                    ],
                    validation_root=validation_root,
                    forbidden_paths=set(),
                    invocation_cache=PANEL._professional_v3_invocation_cache(),
                )

    def test_canonical_packet_state_handle_cannot_be_forged(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )

        with self.subTest(entry="direct-constructor"), self.assertRaisesRegex(
            PANEL.PanelReviewError, "cannot be constructed directly"
        ):
            PANEL._ProfessionalV3CanonicalPacketState(
                packet=packet,
                state=state,
                baseline_validated=True,
            )

        unsealed = object.__new__(PANEL._ProfessionalV3CanonicalPacketState)
        with self.subTest(entry="unsealed-allocation"), self.assertRaisesRegex(
            PANEL.PanelReviewError, "seal is invalid"
        ):
            PANEL.prepare_professional_discovery_capsule_v3(
                packet=packet,
                packet_sha256="a" * 64,
                voter_id="domain-one",
                assigned_skill_ids=[sorted(state["bindings"])[0]],
                created_on="2026-07-17",
                validate_packet_plan=False,
                packet_state=unsealed,
            )

    def test_depth_eight_forces_full_fresh_checkpoint(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        plan = PANEL._professional_v3_review_plan(
            current_bindings=state["bindings"],
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
            baseline_state=_baseline_state(packet, depth=8),
        )
        self.assertEqual(0, plan["plan_lineage_depth"])
        self.assertEqual(189, len(plan["fresh_targets"]))
        self.assertEqual([], plan["carried_targets"])
        self.assertTrue(
            all(
                "lineage-depth-limit" in row["reason_codes"]
                for row in plan["fresh_targets"]
            )
        )

    def test_depth_seven_carries_and_reaches_depth_eight(self) -> None:
        packet = _bootstrap_packet()
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=PANEL.ROOT,
            artifact_path=None,
            validate_baseline=False,
        )
        plan = PANEL._professional_v3_review_plan(
            current_bindings=state["bindings"],
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
            baseline_state=_baseline_state(packet, depth=7),
        )
        self.assertEqual(8, plan["plan_lineage_depth"])
        self.assertEqual([], plan["fresh_targets"])
        self.assertEqual(189, len(plan["carried_targets"]))

    def test_raw_package_intermediate_change_does_not_override_binding(self) -> None:
        packet = _bootstrap_packet()
        target = packet["professional_targets"][0]
        origin_row = {
            "skill_id": target["skill_id"],
            "review_unit_binding": target["review_binding"][
                "review_unit_binding"
            ],
            "final_disposition": "accepted-current-professional-completeness",
            "review_dependencies": {
                "reviewer_added_candidate_ids_union": []
            },
            "target_decision_fingerprint": "b" * 64,
        }
        origin_ref = {
            "path": "origin/panel/decision.json",
            "sha256": "c" * 64,
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            "review_id": "origin",
        }
        carried = PANEL._professional_v3_carried_target_decision(
            target=target,
            origin_row=origin_row,
            origin_decision_ref=origin_ref,
            current_bindings={},
            origin_candidate_material_bindings={},
        )
        self.assertEqual(
            target["review_binding"]["review_unit_binding"],
            carried["review_unit_binding"],
        )
        self.assertNotIn("package_fingerprint", carried)
        self.assertEqual(
            "review-visible-binding-unchanged",
            carried["provenance"]["carry_basis"],
        )
        changed = copy.deepcopy(target)
        changed["review_binding"]["review_unit_binding"] = "d" * 64
        with self.assertRaisesRegex(PANEL.PanelReviewError, "review binding"):
            PANEL._professional_v3_carried_target_decision(
                target=changed,
                origin_row=origin_row,
                origin_decision_ref=origin_ref,
                current_bindings={},
                origin_candidate_material_bindings={},
            )

    def test_bound_path_cache_reads_once_and_rechecks_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "round" / "packet.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}\n", encoding="utf-8")
            cache = PANEL._professional_v3_invocation_cache()
            original_open = Path.open
            reads = 0

            def counted_open(self, *args, **kwargs):
                nonlocal reads
                if self.resolve() == path.resolve():
                    reads += 1
                return original_open(self, *args, **kwargs)

            with mock.patch.object(Path, "open", counted_open):
                first = PANEL._professional_v3_bind_json_artifact_path(
                    path,
                    cache=cache,
                    validation_root=root,
                    label="packet",
                    expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                    expected_review_id="round",
                )
                second = PANEL._professional_v3_bind_json_artifact_path(
                    path,
                    cache=cache,
                    validation_root=root,
                    label="packet",
                    expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                    expected_review_id="round",
                )
                self.assertEqual(first, second)
                self.assertEqual(1, reads)
                with self.assertRaisesRegex(PANEL.PanelReviewError, "cycle"):
                    PANEL._professional_v3_bind_json_artifact_path(
                        path,
                        cache=cache,
                        validation_root=root,
                        label="packet",
                        expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                        expected_review_id="round",
                        forbidden_paths={path},
                    )

    def test_cached_reference_rejects_same_path_with_second_sha(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "round" / "packet.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}\n", encoding="utf-8")
            cache = PANEL._professional_v3_invocation_cache()
            _path, reference, _value = (
                PANEL._professional_v3_bind_json_artifact_path(
                    path,
                    cache=cache,
                    validation_root=root,
                    label="packet",
                    expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                    expected_review_id="round",
                )
            )
            conflicting = {**reference, "sha256": "f" * 64}
            with self.assertRaisesRegex(PANEL.PanelReviewError, "conflicts"):
                PANEL._professional_v3_cached_json_artifact(
                    conflicting,
                    cache=cache,
                    validation_root=root,
                    label="packet-conflict",
                    expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                    expected_axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                    expected_review_id="round",
                )

    def test_bound_read_detects_same_inode_metadata_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "round" / "packet.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}\n", encoding="utf-8")
            original_open = Path.open
            original_stat = Path.stat
            read_finished = False
            target_paths = {path.absolute(), path.resolve().absolute()}

            class HandleProxy:
                def __init__(self, handle):
                    self.handle = handle

                def __enter__(self):
                    self.handle.__enter__()
                    return self

                def __exit__(self, *args):
                    return self.handle.__exit__(*args)

                def fileno(self):
                    return self.handle.fileno()

                def read(self, *args, **kwargs):
                    nonlocal read_finished
                    value = self.handle.read(*args, **kwargs)
                    read_finished = True
                    return value

            class StatProxy:
                def __init__(self, value):
                    self._value = value

                def __getattr__(self, name):
                    if name in {"st_mtime_ns", "st_ctime_ns"}:
                        return getattr(self._value, name) + 1
                    return getattr(self._value, name)

            def changed_open(self, *args, **kwargs):
                handle = original_open(self, *args, **kwargs)
                if self.absolute() in target_paths:
                    return HandleProxy(handle)
                return handle

            def changed_stat(self, *args, **kwargs):
                value = original_stat(self, *args, **kwargs)
                if read_finished and self.absolute() in target_paths:
                    return StatProxy(value)
                return value

            with mock.patch.object(Path, "open", changed_open), mock.patch.object(
                Path, "stat", changed_stat
            ), self.assertRaisesRegex(PANEL.PanelReviewError, "changed"):
                PANEL._professional_v3_bind_json_artifact_path(
                    path,
                    cache=PANEL._professional_v3_invocation_cache(),
                    validation_root=root,
                    label="packet",
                    expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                    expected_review_id="round",
                )

    def test_review_contract_uses_repository_source_bytes_not_runtime_patches(self) -> None:
        def fingerprints_for_bodies(
            *, attribute: str, first_body: str, second_body: str
        ) -> tuple[str, str]:
            original = getattr(PANEL, attribute)
            with tempfile.TemporaryDirectory(dir=PANEL.ROOT / "tests") as raw:
                path = Path(raw) / "contract_replacement.py"
                first = _repository_source_replacement(
                    path,
                    f"schema3_contract_{attribute}_first",
                    original,
                    first_body,
                )
                with mock.patch.object(PANEL, attribute, first):
                    fingerprint = (
                        PANEL._professional_evidence_review_contract_fingerprint
                    )
                    fingerprint.cache_clear()
                    left = fingerprint()
                second = _repository_source_replacement(
                    path,
                    f"schema3_contract_{attribute}_second",
                    original,
                    second_body,
                )
                with mock.patch.object(PANEL, attribute, second):
                    fingerprint = (
                        PANEL._professional_evidence_review_contract_fingerprint
                    )
                    fingerprint.cache_clear()
                    right = fingerprint()
            PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
            return left, right

        validator_fingerprints = fingerprints_for_bodies(
            attribute="_validate_professional_completeness_ballot_v3",
            first_body="return kwargs.get('ballot')",
            second_body="return {'changed': True}",
        )
        self.assertEqual(*validator_fingerprints)

        cache_fingerprints = fingerprints_for_bodies(
            attribute="_professional_v3_cached_json_artifact",
            first_body="raise RuntimeError('opaque first')",
            second_body="raise RuntimeError('opaque second')",
        )
        self.assertEqual(*cache_fingerprints)

        lineage_fingerprints = fingerprints_for_bodies(
            attribute="_load_professional_v3_baseline",
            first_body="return None",
            second_body="return {'changed': True}",
        )
        self.assertEqual(*lineage_fingerprints)


if __name__ == "__main__":
    unittest.main()
