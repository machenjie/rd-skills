from __future__ import annotations

import copy
import json
import linecache
import sys
import tempfile
import types
import unittest
from collections import OrderedDict, defaultdict, namedtuple
from decimal import Decimal
from enum import IntEnum
from functools import lru_cache
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_completeness_test_support as professional_support

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import expert_panel_contracts as CONTRACTS
import professional_completeness_carry_forward as CARRY






PANEL = source_support.PANEL
_sha = professional_support._sha
_material = professional_support._material
_catalog = professional_support._catalog
_live_packet = professional_support._live_packet
_legacy_schema1_packet = professional_support._legacy_schema1_packet
SKILL_IDS = ("a", "b", "c", "d")
CONTRACT_FINGERPRINT = "a" * 64




def _load_contract_fixture(path: Path, module_name: str, source: str):
    path.write_text(source, encoding="utf-8")
    linecache.clearcache()
    module = types.ModuleType(module_name)
    module.__file__ = path.as_posix()
    sys.modules[module_name] = module
    exec(compile(source, path.as_posix(), "exec"), module.__dict__)
    return module






def _prior_artifacts(
    targets: list[dict],
    *,
    final_dispositions: dict[str, str] | None = None,
) -> tuple[dict, list[dict], dict]:
    final_dispositions = final_dispositions or {}
    source_fingerprints = {"professional_packages": _sha(targets)}
    packet = {
        "review_id": "prior-review",
        "source_fingerprints": source_fingerprints,
        "professional_targets": copy.deepcopy(targets),
    }
    voters = [
        ("domain-one", "agent-domain-one", ["domain"]),
        ("domain-two", "agent-domain-two", ["domain"]),
        (
            "architecture-one",
            "agent-architecture-one",
            ["skill-reference-architecture"],
        ),
    ]
    ballots = []
    for voter_index, (voter_id, agent_id, tags) in enumerate(voters):
        votes = []
        for target in targets:
            reviews = [
                {
                    "skill_id": candidate["skill_id"],
                    "review_origin": "packet-required",
                }
                for candidate in target["routing_adjacency"][
                    "required_candidates"
                ]
            ]
            # Only one of three ballots adds b while reviewing a.  The union
            # must retain this minority/dissent dependency.
            if voter_index == 0 and target["skill_id"] == "a":
                reviews.append(
                    {"skill_id": "b", "review_origin": "reviewer-added"}
                )
            reviews.sort(key=lambda row: row["skill_id"])
            votes.append(
                {
                    "skill_id": target["skill_id"],
                    "examined_adjacent_candidates": reviews,
                }
            )
        ballots.append(
            {
                "review_id": packet["review_id"],
                "source_fingerprints": source_fingerprints,
                "voter": {
                    "voter_id": voter_id,
                    "agent_id": agent_id,
                    "expertise_tags": tags,
                    "qualification_claims": [
                        {
                            "expertise_tag": tag,
                            "qualification_basis": "fixture qualification",
                            "proof_limit": "fixture proof limit",
                        }
                        for tag in tags
                    ],
                    "independent_review": True,
                },
                "professional_votes": votes,
            }
        )
    decisions = []
    for target in targets:
        reviewer_added = []
        if target["skill_id"] == "a":
            reviewer_added = [
                {
                    "voter_id": "domain-one",
                    "candidates": [
                        {
                            "skill_id": "b",
                            "review_origin": "reviewer-added",
                        }
                    ],
                }
            ]
        decisions.append(
            {
                "skill_id": target["skill_id"],
                "package_fingerprint": target["package_fingerprint"],
                "qualification_coverage": {
                    "required_expertise_tags": target[
                        "required_expertise_tags"
                    ],
                    "domain_voters": ["domain-one", "domain-two"],
                    "architecture_voter": "architecture-one",
                },
                "reviewer_added_adjacency_reviews": reviewer_added,
                "final_disposition": final_dispositions.get(
                    target["skill_id"],
                    CARRY.ACCEPTED_PROFESSIONAL_DISPOSITION,
                ),
            }
        )
    decision = {
        "review_id": packet["review_id"],
        "source_fingerprints": source_fingerprints,
        "voters": [
            {"voter_id": voter_id, "agent_id": agent_id}
            for voter_id, agent_id, _tags in voters
        ],
        "professional_decisions": decisions,
    }
    return packet, ballots, decision






def _historical_schema1_packet() -> dict:
    packet = copy.deepcopy(_legacy_schema1_packet())
    remaining = copy.deepcopy(PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS)
    targets = []
    for target in packet["professional_targets"]:
        layer = target["layer"]
        if remaining[layer] > 0:
            targets.append(target)
            remaining[layer] -= 1
    if remaining != {"professional": 0, "foundation": 0, "domain": 0}:
        raise AssertionError(f"legacy fixture inventory is incomplete: {remaining}")
    packet["review_id"] = "synthetic-legacy-schema-one"
    packet["professional_targets"] = sorted(
        targets, key=lambda target: target["skill_id"]
    )
    selected_ids = {
        target["skill_id"] for target in packet["professional_targets"]
    }
    for target in packet["professional_targets"]:
        adjacency = target["routing_adjacency"]
        adjacency["skills"] = [
            skill_id
            for skill_id in adjacency["skills"]
            if skill_id in selected_ids
        ]
        responsibility = target["registry"]["responsibility_contract"]
        adjacency["fingerprint"] = _sha(
            {
                "skill_id": target["skill_id"],
                "layer": target["layer"],
                "role_support": responsibility["role_support"],
                "trigger_signals": responsibility["trigger_signals"],
                "anti_trigger_signals": responsibility["anti_trigger_signals"],
                "output_contract": responsibility["output_contract"],
                "adjacent_skills": adjacency["skills"],
            }
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        target["package_fingerprint"] = _sha(without_fingerprint)
    packet["source_fingerprints"]["professional_packages"] = _sha(
        packet["professional_targets"]
    )
    packet["panel_contract"]["required_target_count"] = len(targets)
    return packet


def _historical_schema3_adapter_fixture(*, cap50: bool) -> tuple[dict, dict, dict]:
    packet = professional_support._bootstrap_packet()
    if cap50:
        review_id = PANEL.PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID
        review_contract = (
            PANEL.PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT
        )
        packet_sha = PANEL.PROFESSIONAL_HISTORICAL_CAP50_PACKET_SHA256
        target_count = PANEL.PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT
        include_derivation = False
        maximum = (
            PANEL.PROFESSIONAL_HISTORICAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
        )
        remaining = copy.deepcopy(PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS)
        targets = []
        for target in packet["professional_targets"]:
            layer = target["layer"]
            if remaining[layer] > 0:
                targets.append(target)
                remaining[layer] -= 1
    else:
        review_id = PANEL.PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
        review_contract = PANEL.PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT
        packet_sha = PANEL.PROFESSIONAL_HISTORICAL_V1_PACKET_SHA256
        target_count = PANEL.PROFESSIONAL_PACKAGE_COUNT
        include_derivation = True
        maximum = 52
        targets = packet["professional_targets"]
    if len(targets) != target_count:
        raise AssertionError("historical adapter fixture target count is stale")
    historical_selection = PANEL._professional_adjacency_selection_contract_v1(
        target_count=target_count,
        include_derivation=include_derivation,
        maximum_required_candidates_per_target=maximum,
    )
    packet["review_id"] = review_id
    packet["review_contract_fingerprint"] = review_contract
    packet["professional_targets"] = copy.deepcopy(targets)
    packet["panel_contract"] = PANEL._professional_v3_panel_contract(
        target_count=target_count,
        include_selection_derivation=include_derivation,
    )
    packet["panel_contract"]["adjacency_contract"][
        "required_candidate_selection"
    ] = copy.deepcopy(historical_selection)
    for target in packet["professional_targets"]:
        target["routing_adjacency"]["required_candidate_selection"] = copy.deepcopy(
            historical_selection
        )
    packet_ref = {
        "path": f"evals/expert-panel/{review_id}/packet.json",
        "sha256": packet_sha,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": review_id,
    }
    decision = {
        "review_id": review_id,
        "review_contract_fingerprint": review_contract,
    }
    return decision, packet_ref, packet


class ProfessionalCarryForwardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.targets = _catalog()
        self.bindings = CARRY.professional_review_bindings(self.targets)
        self.snapshot = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        packet, ballots, decision = _prior_artifacts(self.targets)
        self.dependencies = CARRY.professional_prior_decision_dependencies(
            prior_packet=packet,
            prior_ballots=ballots,
            prior_decision=decision,
        )

    def _plan(self, current_targets: list[dict], **overrides) -> dict:
        arguments = {
            "current_bindings": CARRY.professional_review_bindings(
                current_targets
            ),
            "prior_snapshot": self.snapshot,
            "prior_decision_dependencies": self.dependencies,
            "review_contract_fingerprint": CONTRACT_FINGERPRINT,
        }
        arguments.update(overrides)
        return CARRY.plan_exact_professional_carry_forward(**arguments)

    def _request(self, target_id: str, candidate_id: str) -> dict:
        target = next(
            row for row in self.targets if row["skill_id"] == target_id
        )
        ranking = next(
            (
                row
                for row in target["routing_adjacency"][
                    "full_catalog_ranking"
                ]
                if row["skill_id"] == candidate_id
            ),
            {
                "skill_id": candidate_id,
                "rank": 999,
                "total_score": 0,
                "signals": {},
            },
        )
        fingerprint = self.bindings.get(candidate_id, {}).get(
            "content_fingerprint", "f" * 64
        )
        return {
            "skill_id": candidate_id,
            "discovery_reason": "The boundary summary exposes a distinct overlapping responsibility.",
            "ranking_evidence": copy.deepcopy(ranking),
            "material_fingerprint": fingerprint,
        }

    def test_unchanged_exact_baseline_carries_every_package(self) -> None:
        plan = self._plan(self.targets)
        self.assertEqual([], plan["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), plan["carry_target_ids"])
        for target in self.targets:
            binding = self.bindings[target["skill_id"]]
            self.assertEqual(
                CARRY.canonical_json_sha256(
                    CARRY.professional_candidate_material_binding(target)
                ),
                binding["content_fingerprint"],
            )
            self.assertEqual(
                CARRY.canonical_json_sha256(
                    CARRY.professional_candidate_semantic_review_binding(
                        target
                    )
                ),
                binding["package_material_binding"],
            )

    def test_no_baseline_and_contract_change_make_every_target_fresh(self) -> None:
        without_baseline = self._plan(
            self.targets,
            prior_snapshot=None,
            prior_decision_dependencies=None,
        )
        contract_changed = self._plan(
            self.targets,
            review_contract_fingerprint="b" * 64,
        )
        self.assertEqual(list(SKILL_IDS), without_baseline["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), contract_changed["fresh_target_ids"])
        self.assertEqual(
            ["no-prior-baseline"], without_baseline["reasons_by_target"]["a"]
        )
        self.assertEqual(
            ["review-contract-changed"],
            contract_changed["reasons_by_target"]["a"],
        )

    def test_semantic_contract_projection_is_the_only_contract_staleness_input(
        self,
    ) -> None:
        current_contract = (
            CONTRACTS.professional_review_contract_fingerprint()
        )
        current_snapshot = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=current_contract,
        )
        unchanged = CARRY.plan_exact_professional_carry_forward(
            current_bindings=self.bindings,
            prior_snapshot=current_snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=current_contract,
        )

        changed_projection = (
            CONTRACTS.professional_schema3_contract_projection()
        )
        changed_projection["evidence"]["semantic_grounding"][
            "uniform_template_guard"
        ]["minimum_uniform_share_percent"] -= 1
        changed_contract = (
            CONTRACTS.professional_review_contract_fingerprint(
                changed_projection
            )
        )
        changed = CARRY.plan_exact_professional_carry_forward(
            current_bindings=self.bindings,
            prior_snapshot=current_snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=changed_contract,
        )

        self.assertEqual([], unchanged["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), unchanged["carry_target_ids"])
        self.assertNotEqual(current_contract, changed_contract)
        self.assertEqual(list(SKILL_IDS), changed["fresh_target_ids"])
        self.assertEqual(
            ["review-contract-changed"],
            changed["reasons_by_target"]["a"],
        )

    def test_semantic_fact_contract_mutation_forces_all_fresh(self) -> None:
        current_contract = CONTRACTS.professional_review_contract_fingerprint()
        current_snapshot = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=current_contract,
        )
        changed_projection = CONTRACTS.professional_schema3_contract_projection()
        changed_projection["binding_contracts"]["semantic_fact_projection"][
            "argument_relations"
        ].append("under")
        changed_contract = CONTRACTS.professional_review_contract_fingerprint(
            changed_projection
        )
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=self.bindings,
            prior_snapshot=current_snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=changed_contract,
        )
        self.assertNotEqual(current_contract, changed_contract)
        self.assertEqual(list(SKILL_IDS), plan["fresh_target_ids"])
        self.assertEqual(
            ["review-contract-changed"], plan["reasons_by_target"]["a"]
        )

    def test_raw_content_only_changes_preserve_semantic_carry(self) -> None:
        cases = (
            _catalog(
                roots={
                    "d": (
                        "# d\n\n<!-- Corrected speling. -->\n"
                        "Review d root behavior.\n"
                    )
                }
            ),
            _catalog(roots={"d": "# d\n\n**Review** d root behavior.\n"}),
            _catalog(roots={"d": "# d\n\n\nReview   d root behavior.\n"}),
            _catalog(roots={"d": "# d\n\nReview d behavior.\n"}),
            _catalog(
                references={
                    "d": "# d Reference\n\n**Verify** d failure evidence.\n"
                }
            ),
        )
        baseline_content = self.bindings["d"]["content_fingerprint"]
        for targets in cases:
            with self.subTest(content=targets[3]["root"]["content"]):
                current = CARRY.professional_review_bindings(targets)
                self.assertNotEqual(
                    baseline_content, current["d"]["content_fingerprint"]
                )
                self.assertEqual(
                    self.bindings["d"]["package_material_binding"],
                    current["d"]["package_material_binding"],
                )
                plan = self._plan(targets)
                self.assertEqual([], plan["fresh_target_ids"])
                self.assertEqual(list(SKILL_IDS), plan["carry_target_ids"])

    def test_material_semantic_fact_projection_carries_proven_equivalent_edits(
        self,
    ) -> None:
        baseline = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- You must validate every output before release.\n"
                )
            }
        )
        equivalent = _catalog(
            roots={
                "d": (
                    "# d\n\n### Decision Rules\n\n"
                    "<!-- display-only note -->\n"
                    "* **Validte** ouputs prior to release.\n"
                    "* Verify output before release.\n"
                )
            }
        )
        expected_root_fact = {
            "source_class": "root",
            "fact_class": "professional-decision",
            "section_kind": "decision-rules",
            "unit_kind": "list-item",
            "fact_kind": "obligation",
            "predicate_ordinal": 1,
            "incoming_connector": "root",
            "subject_scope_concepts": ["actor:implicit"],
            "action_concept": "validate",
            "argument_role_bindings": [
                {
                    "argument_ordinal": 1,
                    "relation": "direct",
                    "scope_concepts": ["output"],
                    "attachment": "governing-predicate",
                    "owner_action_concept": "validate",
                    "owner_modality": "required",
                    "owner_polarity": "affirmative",
                }
            ],
            "object_scope_concepts": ["output"],
            "condition_concepts": [
                "precondition",
                "release",
            ],
            "modality": "required",
            "polarity": "affirmative",
        }
        for targets in (baseline, equivalent):
            projection = CARRY.professional_semantic_fact_projection(
                targets[3]
            )
            self.assertEqual(
                "professional-semantic-predicate-projection-v4",
                projection["contract_version"],
            )
            self.assertEqual(
                [expected_root_fact],
                [
                    fact
                    for fact in projection["facts"]
                    if fact["source_class"] == "root"
                ],
            )
            encoded = CARRY.canonical_json_bytes(projection)
            for forbidden in (
                b'"content":',
                b'"sha256":',
                b'"line_count":',
                b'"path":',
            ):
                self.assertNotIn(forbidden, encoded)

        baseline_bindings = CARRY.professional_review_bindings(baseline)
        equivalent_bindings = CARRY.professional_review_bindings(equivalent)
        snapshot = CARRY.professional_carry_snapshot(
            baseline_bindings,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=equivalent_bindings,
            prior_snapshot=snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        self.assertNotEqual(
            baseline_bindings["d"]["content_fingerprint"],
            equivalent_bindings["d"]["content_fingerprint"],
        )
        self.assertEqual([], plan["fresh_target_ids"])

    def test_predicate_projection_preserves_root_and_reference_action_object_relations(
        self,
    ) -> None:
        baseline_text = (
            "# d\n\n## Professional Decision Rules\n\n"
            "- Validate input and delete output.\n"
        )
        swapped_text = (
            "# d\n\n## Professional Decision Rules\n\n"
            "- Delete input and validate output.\n"
        )
        cosmetic_text = (
            "# d\n\n### Decision Rules\n\n"
            "<!-- presentation only -->\n"
            "* **Verify** input and remove output.\n"
        )
        expected_predicates = [
            {
                "source_class": "SOURCE",
                "fact_class": "professional-decision",
                "section_kind": "decision-rules",
                "unit_kind": "list-item",
                "fact_kind": "obligation",
                "predicate_ordinal": 2,
                "incoming_connector": "and",
                "subject_scope_concepts": ["actor:implicit"],
                "action_concept": "delete",
                "argument_role_bindings": [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": ["output"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "delete",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    }
                ],
                "object_scope_concepts": ["output"],
                "condition_concepts": [],
                "modality": "required",
                "polarity": "affirmative",
            },
            {
                "source_class": "SOURCE",
                "fact_class": "professional-decision",
                "section_kind": "decision-rules",
                "unit_kind": "list-item",
                "fact_kind": "obligation",
                "predicate_ordinal": 1,
                "incoming_connector": "root",
                "subject_scope_concepts": ["actor:implicit"],
                "action_concept": "validate",
                "argument_role_bindings": [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": ["input"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "validate",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    }
                ],
                "object_scope_concepts": ["input"],
                "condition_concepts": [],
                "modality": "required",
                "polarity": "affirmative",
            },
        ]
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            with self.subTest(source_class=source_class):
                baseline = _catalog(**{material_field: {"d": baseline_text}})
                swapped = _catalog(**{material_field: {"d": swapped_text}})
                cosmetic = _catalog(**{material_field: {"d": cosmetic_text}})
                baseline_binding = CARRY.professional_review_bindings(baseline)
                expected = [
                    {**fact, "source_class": source_class}
                    for fact in expected_predicates
                ]
                actual = [
                    fact
                    for fact in CARRY.professional_semantic_fact_projection(
                        baseline[3]
                    )["facts"]
                    if fact["source_class"] == source_class
                ]
                self.assertEqual(expected, actual)
                self.assertEqual(
                    baseline_binding["d"]["package_material_binding"],
                    CARRY.professional_review_bindings(cosmetic)["d"]
                    ["package_material_binding"],
                )
                self.assertNotEqual(
                    baseline_binding["d"]["package_material_binding"],
                    CARRY.professional_review_bindings(swapped)["d"]
                    ["package_material_binding"],
                )
                snapshot = CARRY.professional_carry_snapshot(
                    baseline_binding,
                    review_contract_fingerprint=CONTRACT_FINGERPRINT,
                )
                plan = CARRY.plan_exact_professional_carry_forward(
                    current_bindings=CARRY.professional_review_bindings(swapped),
                    prior_snapshot=snapshot,
                    prior_decision_dependencies=self.dependencies,
                    review_contract_fingerprint=CONTRACT_FINGERPRINT,
                )
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertEqual(
                    ["target-material-changed"],
                    plan["reasons_by_target"]["d"],
                )
                self.assertIn(
                    "required-candidate-material-changed",
                    plan["reasons_by_target"]["b"],
                )

    def test_directional_roles_reopen_root_and_reference_target_and_one_hop(self) -> None:
        cases = (
            (
                "Route input to destination from source.",
                "Route input to source from destination.",
                "handoff",
                [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": ["input"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "handoff",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                    {
                        "argument_ordinal": 2,
                        "relation": "to",
                        "scope_concepts": ["term:destination"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "handoff",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                    {
                        "argument_ordinal": 3,
                        "relation": "from",
                        "scope_concepts": ["provenance"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "handoff",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                ],
            ),
            (
                "Copy artifact from origin to target.",
                "Copy artifact from target to origin.",
                "build",
                [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": ["artifact"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "build",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                    {
                        "argument_ordinal": 2,
                        "relation": "from",
                        "scope_concepts": ["term:origin"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "build",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                    {
                        "argument_ordinal": 3,
                        "relation": "to",
                        "scope_concepts": ["target"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "build",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                ],
            ),
            (
                "Migrate data from legacy to current.",
                "Migrate data from current to legacy.",
                "migrate",
                [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": ["data"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "migrate",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                    {
                        "argument_ordinal": 2,
                        "relation": "from",
                        "scope_concepts": ["term:legacy"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "migrate",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                    {
                        "argument_ordinal": 3,
                        "relation": "to",
                        "scope_concepts": ["term:current"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "migrate",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    },
                ],
            ),
        )
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            for baseline_sentence, reversed_sentence, action, expected_roles in cases:
                with self.subTest(source_class=source_class, action=action):
                    baseline = _catalog(
                        **{
                            material_field: {
                                "d": (
                                    "# d\n\n## Professional Decision Rules\n\n"
                                    f"- {baseline_sentence}\n"
                                )
                            }
                        }
                    )
                    changed = _catalog(
                        **{
                            material_field: {
                                "d": (
                                    "# d\n\n## Professional Decision Rules\n\n"
                                    f"- {reversed_sentence}\n"
                                )
                            }
                        }
                    )
                    fact = next(
                        row
                        for row in CARRY.professional_semantic_fact_projection(
                            baseline[3]
                        )["facts"]
                        if row["source_class"] == source_class
                        and row["action_concept"] == action
                    )
                    self.assertEqual(expected_roles, fact["argument_role_bindings"])
                    self.assertEqual(
                        sorted(
                            {
                                concept
                                for role in expected_roles
                                for concept in role["scope_concepts"]
                            }
                        ),
                        fact["object_scope_concepts"],
                    )
                    baseline_bindings = CARRY.professional_review_bindings(baseline)
                    changed_bindings = CARRY.professional_review_bindings(changed)
                    self.assertNotEqual(
                        baseline_bindings["d"]["package_material_binding"],
                        changed_bindings["d"]["package_material_binding"],
                    )
                    plan = CARRY.plan_exact_professional_carry_forward(
                        current_bindings=changed_bindings,
                        prior_snapshot=CARRY.professional_carry_snapshot(
                            baseline_bindings,
                            review_contract_fingerprint=CONTRACT_FINGERPRINT,
                        ),
                        prior_decision_dependencies=self.dependencies,
                        review_contract_fingerprint=CONTRACT_FINGERPRINT,
                    )
                    self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                    self.assertEqual(
                        ["target-material-changed"],
                        plan["reasons_by_target"]["d"],
                    )
                    self.assertIn(
                        "required-candidate-material-changed",
                        plan["reasons_by_target"]["b"],
                    )

    def test_directional_role_cosmetic_changes_carry(self) -> None:
        baseline = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Route input to destination from source.\n"
                )
            }
        )
        cosmetic = _catalog(
            roots={
                "d": (
                    "# d\n\n### Decision Rules\n\n"
                    "<!-- presentation only -->\n"
                    "* **Route** input   to destination from source.\n"
                )
            }
        )
        baseline_bindings = CARRY.professional_review_bindings(baseline)
        cosmetic_bindings = CARRY.professional_review_bindings(cosmetic)
        self.assertNotEqual(
            baseline_bindings["d"]["content_fingerprint"],
            cosmetic_bindings["d"]["content_fingerprint"],
        )
        self.assertEqual(
            baseline_bindings["d"]["package_material_binding"],
            cosmetic_bindings["d"]["package_material_binding"],
        )

    def test_infinitive_to_is_not_a_direction_and_still_binds_semantics(self) -> None:
        baseline_sentence = (
            "When new structure or a boundary is proposed, place behavior with "
            "the owner of its reason to change and preserve the affected "
            "dependency direction."
        )
        changed_sentence = baseline_sentence.replace(
            "reason to change", "reason to preserve"
        )
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            with self.subTest(source_class=source_class):
                baseline = _catalog(
                    **{
                        material_field: {
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {baseline_sentence}\n"
                            )
                        }
                    }
                )
                changed = _catalog(
                    **{
                        material_field: {
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {changed_sentence}\n"
                            )
                        }
                    }
                )
                baseline_facts = [
                    fact
                    for fact in CARRY.professional_semantic_fact_projection(
                        baseline[3]
                    )["facts"]
                    if fact["source_class"] == source_class
                ]
                self.assertTrue(baseline_facts)
                self.assertNotIn(
                    "to",
                    {
                        role["relation"]
                        for fact in baseline_facts
                        for role in fact["argument_role_bindings"]
                    },
                )
                self.assertNotEqual(
                    CARRY.professional_review_bindings(baseline)["d"]
                    ["package_material_binding"],
                    CARRY.professional_review_bindings(changed)["d"]
                    ["package_material_binding"],
                )

    def test_nearest_structural_owner_controls_each_local_direction(self) -> None:
        cases = (
            (
                "Stop when evidence is mapped from origin while it must route "
                "to target.",
                [("from", "map"), ("to", "handoff")],
            ),
            (
                "Validate evidence by copying from origin while migrating to "
                "target.",
                [("from", "build"), ("to", "migrate")],
            ),
            (
                "Stop when evidence must distinguish a choice while validating "
                "input to output.",
                [("to", "validate")],
            ),
        )
        for sentence, expected in cases:
            with self.subTest(sentence=sentence):
                target = _catalog(
                    roots={
                        "d": (
                            "# d\n\n## Professional Decision Rules\n\n"
                            f"- {sentence}\n"
                        )
                    }
                )[3]
                fact = next(
                    row
                    for row in CARRY.professional_semantic_fact_projection(target)[
                        "facts"
                    ]
                    if row["source_class"] == "root"
                )
                self.assertEqual(
                    expected,
                    [
                        (role["relation"], role["owner_action_concept"])
                        for role in fact["argument_role_bindings"]
                        if role["relation"] in {"from", "to"}
                    ],
                )

    def test_infinitive_owner_preserves_directional_reversal(self) -> None:
        baseline_sentence = "Plan to change input from legacy to current."
        reversed_sentence = "Plan to change input from current to legacy."
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            with self.subTest(source_class=source_class):
                baseline = _catalog(
                    **{
                        material_field: {
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {baseline_sentence}\n"
                            )
                        }
                    }
                )
                reversed_target = _catalog(
                    **{
                        material_field: {
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {reversed_sentence}\n"
                            )
                        }
                    }
                )
                fact = next(
                    row
                    for row in CARRY.professional_semantic_fact_projection(
                        baseline[3]
                    )["facts"]
                    if row["source_class"] == source_class
                    and row["action_concept"] == "design"
                )
                self.assertEqual(
                    [
                        ("direct", "change", ["input"]),
                        ("from", "change", ["term:legacy"]),
                        ("to", "change", ["term:current"]),
                    ],
                    [
                        (
                            role["relation"],
                            role["owner_action_concept"],
                            role["scope_concepts"],
                        )
                        for role in fact["argument_role_bindings"]
                    ],
                )
                self.assertNotEqual(
                    CARRY.professional_review_bindings(baseline)["d"]
                    ["package_material_binding"],
                    CARRY.professional_review_bindings(reversed_target)["d"]
                    ["package_material_binding"],
                )

    def test_forced_lexical_dependent_actions_are_bounded_and_semantic(self) -> None:
        decay_sentence = (
            "A modular monolith without enforced ownership can decay into a "
            "coupled monolith."
        )
        mirror_sentence = (
            "Organization structure is evidence, not a universal command to "
            "mirror the current org chart."
        )
        frobnicate_sentence = "Plan to frobnicate the input from source."
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            with self.subTest(source_class=source_class):
                def target_for(sentence: str) -> tuple[object, ...]:
                    return _catalog(
                        **{
                            material_field: {
                                "d": (
                                    "# d\n\n## Professional Decision Rules\n\n"
                                    f"- {sentence}\n"
                                )
                            }
                        }
                    )

                decay = target_for(decay_sentence)
                decay_fact = next(
                    fact
                    for fact in CARRY.professional_semantic_fact_projection(decay[3])[
                        "facts"
                    ]
                    if fact["source_class"] == source_class
                )
                decay_role = next(
                    role
                    for role in decay_fact["argument_role_bindings"]
                    if role["relation"] == "to"
                )
                self.assertEqual(
                    ("lexical:decay", "permitted", "affirmative"),
                    (
                        decay_role["owner_action_concept"],
                        decay_role["owner_modality"],
                        decay_role["owner_polarity"],
                    ),
                )
                cosmetic = target_for(
                    decay_sentence.replace("can decay", "can   decay")
                )
                mutation = target_for(decay_sentence.replace("decay", "degrade"))
                self.assertEqual(
                    CARRY.professional_review_bindings(decay)["d"]
                    ["package_material_binding"],
                    CARRY.professional_review_bindings(cosmetic)["d"]
                    ["package_material_binding"],
                )
                self.assertNotEqual(
                    CARRY.professional_review_bindings(decay)["d"]
                    ["package_material_binding"],
                    CARRY.professional_review_bindings(mutation)["d"]
                    ["package_material_binding"],
                )

                mirror = target_for(mirror_sentence)
                mirror_facts = [
                    fact
                    for fact in CARRY.professional_semantic_fact_projection(mirror[3])[
                        "facts"
                    ]
                    if fact["source_class"] == source_class
                ]
                self.assertNotIn(
                    "to",
                    {
                        role["relation"]
                        for fact in mirror_facts
                        for role in fact["argument_role_bindings"]
                    },
                )
                self.assertNotEqual(
                    CARRY.professional_review_bindings(mirror)["d"]
                    ["package_material_binding"],
                    CARRY.professional_review_bindings(
                        target_for(mirror_sentence.replace("mirror", "frobnicate"))
                    )["d"]["package_material_binding"],
                )

                frobnicate = target_for(frobnicate_sentence)
                frobnicate_fact = next(
                    fact
                    for fact in CARRY.professional_semantic_fact_projection(
                        frobnicate[3]
                    )["facts"]
                    if fact["source_class"] == source_class
                    and fact["action_concept"] == "design"
                )
                from_role = next(
                    role
                    for role in frobnicate_fact["argument_role_bindings"]
                    if role["relation"] == "from"
                )
                self.assertEqual(
                    ("lexical:frobnicate", "dependent-complement"),
                    (
                        from_role["owner_action_concept"],
                        from_role["attachment"],
                    ),
                )

    def test_forced_lexical_classifier_preserves_closed_and_invalid_boundaries(
        self,
    ) -> None:
        directional = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Route input to frobnicate.\n"
                )
            }
        )[3]
        directional_fact = next(
            fact
            for fact in CARRY.professional_semantic_fact_projection(directional)[
                "facts"
            ]
            if fact["source_class"] == "root"
        )
        self.assertEqual(
            [("to", "handoff", ["term:frobnicate"])],
            [
                (
                    role["relation"],
                    role["owner_action_concept"],
                    role["scope_concepts"],
                )
                for role in directional_fact["argument_role_bindings"]
                if role["relation"] == "to"
            ],
        )

        for closed_form in ("validate", "validated"):
            with self.subTest(closed_form=closed_form):
                target = _catalog(
                    roots={
                        "d": (
                            "# d\n\n## Professional Decision Rules\n\n"
                            f"- Stop when evidence can {closed_form} from source.\n"
                        )
                    }
                )[3]
                fact = next(
                    row
                    for row in CARRY.professional_semantic_fact_projection(target)[
                        "facts"
                    ]
                    if row["source_class"] == "root"
                )
                owner = next(
                    role
                    for role in fact["argument_role_bindings"]
                    if role["relation"] == "from"
                )
                self.assertEqual("validate", owner["owner_action_concept"])

        for sentence, message in (
            (
                "Stop when evidence can decaying into output.",
                "structurally signaled unknown dependent owner",
            ),
            (
                "Stop when evidence can input from source.",
                "structurally signaled unknown dependent owner",
            ),
            (
                "Plan to frobnicate the.",
                "malformed lexical infinitive complement",
            ),
            (
                "Validate evidence by zorbaxing into output.",
                "structurally signaled unknown dependent owner",
            ),
        ):
            with self.subTest(sentence=sentence), self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                message,
            ):
                CARRY.professional_review_bindings(
                    _catalog(
                        roots={
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {sentence}\n"
                            )
                        }
                    )
                )

        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "material semantic clause has no predicate",
        ):
            CARRY.professional_review_bindings(
                _catalog(
                    roots={
                        "d": (
                            "# d\n\n## Professional Decision Rules\n\n"
                            "The frobnicate owner.\n"
                        )
                    }
                )
            )

    def test_exact_closed_action_is_a_locality_barrier_and_condition_owner(
        self,
    ) -> None:
        sentence = (
            "When equivalent submissions or workers can overlap, select a "
            "control from the actual overlap window, business identity, "
            "in-flight behavior, winning-effect authority, loser outcome, "
            "result reuse, effect semantics, and storage guarantees."
        )
        mutated_sentence = sentence.replace(
            "actual overlap window", "declared overlap window"
        )
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            with self.subTest(source_class=source_class):
                baseline = _catalog(
                    **{
                        material_field: {
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {sentence}\n"
                            )
                        }
                    }
                )
                mutated = _catalog(
                    **{
                        material_field: {
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {mutated_sentence}\n"
                            )
                        }
                    }
                )
                fact = next(
                    row
                    for row in CARRY.professional_semantic_fact_projection(
                        baseline[3]
                    )["facts"]
                    if row["source_class"] == source_class
                )
                from_role = next(
                    role
                    for role in fact["argument_role_bindings"]
                    if role["relation"] == "from"
                )
                self.assertEqual(
                    ("decide", "dependent-condition"),
                    (
                        from_role["owner_action_concept"],
                        from_role["attachment"],
                    ),
                )
                self.assertNotEqual(
                    CARRY.professional_review_bindings(baseline)["d"]
                    ["package_material_binding"],
                    CARRY.professional_review_bindings(mutated)["d"]
                    ["package_material_binding"],
                )

        sliced_roles = CARRY._semantic_argument_role_bindings(
            CARRY._semantic_tokenize(
                "equivalent submissions or workers can overlap select a "
                "control from the actual overlap window"
            ),
            governing_action_concept="lexical:when",
            governing_modality="required",
            governing_polarity="affirmative",
            initial_condition_scope=True,
        )
        sliced_from = next(
            role for role in sliced_roles if role["relation"] == "from"
        )
        self.assertEqual("decide", sliced_from["owner_action_concept"])
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "structurally signaled unknown dependent owner",
        ):
            CARRY._semantic_argument_role_bindings(
                CARRY._semantic_tokenize("workers can overlap from source"),
                governing_action_concept="lexical:when",
                governing_modality="required",
                governing_polarity="affirmative",
                initial_condition_scope=True,
            )

    def test_acceptance_criteria_direction_attachments_cover_root_and_reference(
        self,
    ) -> None:
        cases = (
            (
                "Support `analysis-agent` in turning ambiguous intent into "
                "observable acceptance for each affected actor, state, failure "
                "path, and preserved behavior.",
                "own",
                [
                    ("governing-predicate", "own", "direct"),
                    ("dependent-complement", "change", "direct"),
                    ("dependent-complement", "change", "to"),
                ],
                (2, "invalid-condition"),
                (3, "term:acceptance"),
            ),
            (
                "Trace every affected actor, trigger, precondition, outcome, "
                "and preserved behavior to source evidence.",
                "diagnose",
                [
                    ("governing-predicate", "diagnose", "direct"),
                    ("governing-predicate", "diagnose", "to"),
                ],
                (1, "precondition"),
                (2, "evidence"),
            ),
            (
                "Stop drafting when evidence cannot distinguish a product "
                "choice from a source fact.",
                "stop",
                [
                    ("governing-predicate", "stop", "direct"),
                    ("condition-scope", None, "direct"),
                    ("dependent-condition", "compare", "direct"),
                    ("dependent-condition", "compare", "from"),
                ],
                (3, "term:choice"),
                (4, "provenance"),
            ),
            (
                "Escalate when proposed criteria conflict with another active "
                "change to the same contract or system boundary.",
                "handoff",
                [
                    ("condition-scope", None, "direct"),
                    ("dependent-condition", "change", "to"),
                ],
                (1, "term:criteria"),
                (2, "contract"),
            ),
            (
                "Use this reference when acceptance closure depends on proving "
                "that criteria are mapped to validation evidence, stakeholder "
                "sign-off is fresh, manual or audit evidence is bounded, and "
                "residual risk is explicit.",
                "apply",
                [
                    ("governing-predicate", "apply", "direct"),
                    ("condition-scope", None, "direct"),
                    ("condition-scope", None, "direct"),
                    ("dependent-condition", "map", "to"),
                ],
                (3, "term:criteria"),
                (4, "evidence"),
            ),
        )
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            for sentence, action, expected_shape, left, right in cases:
                with self.subTest(source_class=source_class, action=action):
                    target = _catalog(
                        **{
                            material_field: {
                                "d": (
                                    "# d\n\n## Professional Decision Rules\n\n"
                                    f"- {sentence}\n"
                                )
                            }
                        }
                    )[3]
                    fact = next(
                        row
                        for row in CARRY.professional_semantic_fact_projection(
                            target
                        )["facts"]
                        if row["source_class"] == source_class
                        and row["action_concept"] == action
                    )
                    roles = fact["argument_role_bindings"]
                    self.assertEqual(
                        expected_shape,
                        [
                            (
                                role["attachment"],
                                role["owner_action_concept"],
                                role["relation"],
                            )
                            for role in roles
                        ],
                    )
                    self.assertIn(left[1], roles[left[0] - 1]["scope_concepts"])
                    self.assertIn(right[1], roles[right[0] - 1]["scope_concepts"])

    def test_directional_role_invalid_and_unsupported_markers_fail_closed(self) -> None:
        for sentence, message in (
            ("Route input to.", "incomplete directional argument segment"),
            (
                "Stop when evidence must zorbaxing input to output.",
                "structurally signaled unknown dependent owner",
            ),
            (
                "Plan to changing input from legacy.",
                "unsupported inflected infinitive",
            ),
            (
                "Stop when evidence must should resolve conflict from source.",
                "conflicting dependent owner modalities",
            ),
        ):
            with self.subTest(sentence=sentence), self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                message,
            ):
                CARRY.professional_review_bindings(
                    _catalog(
                        roots={
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"- {sentence}\n"
                            )
                        }
                    )
                )

        under = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Route input under policy.\n"
                )
            }
        )[3]
        fact = next(
            row
            for row in CARRY.professional_semantic_fact_projection(under)["facts"]
            if row["source_class"] == "root"
        )
        self.assertEqual(
            [
                {
                    "argument_ordinal": 1,
                    "relation": "direct",
                    "scope_concepts": ["input", "policy"],
                    "attachment": "governing-predicate",
                    "owner_action_concept": "handoff",
                    "owner_modality": "required",
                    "owner_polarity": "affirmative",
                }
            ],
            fact["argument_role_bindings"],
        )

        prior_to = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Validate output prior to release.\n"
                )
            }
        )[3]
        prior_fact = next(
            row
            for row in CARRY.professional_semantic_fact_projection(prior_to)["facts"]
            if row["source_class"] == "root"
        )
        self.assertEqual(
            ["direct"],
            [role["relation"] for role in prior_fact["argument_role_bindings"]],
        )
        self.assertIn("precondition", prior_fact["condition_concepts"])

        condition_word = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Trace precondition to evidence.\n"
                )
            }
        )[3]
        condition_fact = next(
            row
            for row in CARRY.professional_semantic_fact_projection(condition_word)[
                "facts"
            ]
            if row["source_class"] == "root"
        )
        self.assertEqual(
            [
                ("direct", ["precondition"]),
                ("to", ["evidence"]),
            ],
            [
                (role["relation"], role["scope_concepts"])
                for role in condition_fact["argument_role_bindings"]
            ],
        )

    def test_repeat_from_source_has_directional_owner_and_action_changes_bind(self) -> None:
        sentence = (
            "Rely on evidence whose production a reviewer cannot repeat from "
            "task-accessible sources."
        )
        repeated = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    f"- {sentence}\n"
                )
            }
        )
        fact = next(
            row
            for row in CARRY.professional_semantic_fact_projection(repeated[3])[
                "facts"
            ]
            if row["source_class"] == "root"
        )
        self.assertEqual(
            [
                ("governing-predicate", "lexical:rely", "direct"),
                ("condition-scope", None, "direct"),
                ("dependent-condition", "retry", "from"),
            ],
            [
                (
                    role["attachment"],
                    role["owner_action_concept"],
                    role["relation"],
                )
                for role in fact["argument_role_bindings"]
            ],
        )
        retry_source = fact["argument_role_bindings"][2]["scope_concepts"]
        self.assertIn("provenance", retry_source)
        self.assertIn("term:accessible", retry_source)

        bindings = []
        for action in ("repeat", "generate", "validate"):
            target = _catalog(
                roots={
                    "d": (
                        "# d\n\n## Professional Decision Rules\n\n- "
                        + sentence.replace("repeat", action)
                        + "\n"
                    )
                }
            )
            bindings.append(
                CARRY.professional_review_bindings(target)["d"]
                ["package_material_binding"]
            )
        self.assertEqual(3, len(set(bindings)))

    def test_modal_passive_owner_coalesces_with_local_metadata(self) -> None:
        cases = (
            ("cannot be resolved", "permitted", "negative"),
            ("can be resolved", "permitted", "affirmative"),
            ("must not be resolved", "required", "negative"),
        )
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            for phrase, modality, polarity in cases:
                with self.subTest(source_class=source_class, phrase=phrase):
                    sentence = (
                        f"Return contradictory when conflicts {phrase} from "
                        "the supplied evidence, and name the missing fact."
                    )
                    target = _catalog(
                        **{
                            material_field: {
                                "d": (
                                    "# d\n\n## Professional Decision Rules\n\n"
                                    f"- {sentence}\n"
                                )
                            }
                        }
                    )[3]
                    fact = next(
                        row
                        for row in CARRY.professional_semantic_fact_projection(
                            target
                        )["facts"]
                        if row["source_class"] == source_class
                        and row["action_concept"] == "emit"
                    )
                    dependent = [
                        role
                        for role in fact["argument_role_bindings"]
                        if role["attachment"] == "dependent-condition"
                    ]
                    self.assertEqual(1, len(dependent))
                    self.assertEqual("resolve", dependent[0]["owner_action_concept"])
                    self.assertEqual(modality, dependent[0]["owner_modality"])
                    self.assertEqual(polarity, dependent[0]["owner_polarity"])
                    self.assertEqual("from", dependent[0]["relation"])
                    self.assertIn("evidence", dependent[0]["scope_concepts"])
                    self.assertNotIn(
                        "copular-assert",
                        {
                            role["owner_action_concept"]
                            for role in fact["argument_role_bindings"]
                        },
                    )

    def test_active_and_passive_dependent_owners_remain_distinct(self) -> None:
        active = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Stop when reviewers cannot resolve conflict from source "
                    "evidence.\n"
                )
            }
        )
        passive = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Stop when conflict cannot be resolved from source "
                    "evidence.\n"
                )
            }
        )
        for target, expected_owner_count in ((active, 2), (passive, 1)):
            fact = next(
                row
                for row in CARRY.professional_semantic_fact_projection(target[3])[
                    "facts"
                ]
                if row["source_class"] == "root"
            )
            owners = [
                (
                    role["owner_action_concept"],
                    role["owner_modality"],
                    role["owner_polarity"],
                )
                for role in fact["argument_role_bindings"]
                if role["attachment"] == "dependent-condition"
            ]
            self.assertEqual(
                [("resolve", "permitted", "negative")] * expected_owner_count,
                owners,
            )
        self.assertNotEqual(
            CARRY.professional_review_bindings(active)["d"]
            ["package_material_binding"],
            CARRY.professional_review_bindings(passive)["d"]
            ["package_material_binding"],
        )

    def test_shared_complement_rebinds_governing_owner_only(self) -> None:
        target = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Validate and stop drafting when conflict cannot be "
                    "resolved from source evidence.\n"
                )
            }
        )[3]
        facts = [
            row
            for row in CARRY.professional_semantic_fact_projection(target)["facts"]
            if row["source_class"] == "root"
        ]
        validate_fact = next(
            fact for fact in facts if fact["action_concept"] == "validate"
        )
        stop_fact = next(fact for fact in facts if fact["action_concept"] == "stop")
        validate_governing = next(
            role
            for role in validate_fact["argument_role_bindings"]
            if role["attachment"] == "governing-predicate"
        )
        stop_governing = next(
            role
            for role in stop_fact["argument_role_bindings"]
            if role["attachment"] == "governing-predicate"
        )
        self.assertEqual("validate", validate_governing["owner_action_concept"])
        self.assertEqual("stop", stop_governing["owner_action_concept"])
        self.assertEqual(
            stop_governing["scope_concepts"],
            validate_governing["scope_concepts"],
        )
        self.assertEqual(
            ("required", "affirmative"),
            (
                validate_governing["owner_modality"],
                validate_governing["owner_polarity"],
            ),
        )
        validate_dependent = next(
            role
            for role in validate_fact["argument_role_bindings"]
            if role["attachment"] == "dependent-condition"
        )
        stop_dependent = next(
            role
            for role in stop_fact["argument_role_bindings"]
            if role["attachment"] == "dependent-condition"
        )
        self.assertEqual(stop_dependent, validate_dependent)
        self.assertEqual(
            ("resolve", "permitted", "negative", "from"),
            (
                validate_dependent["owner_action_concept"],
                validate_dependent["owner_modality"],
                validate_dependent["owner_polarity"],
                validate_dependent["relation"],
            ),
        )

    def test_fact_validation_rejects_directional_role_invariant_breaks(self) -> None:
        valid = {
            "source_class": "root",
            "fact_class": "professional-decision",
            "section_kind": "decision-rules",
            "unit_kind": "list-item",
            "fact_kind": "obligation",
            "predicate_ordinal": 1,
            "incoming_connector": "root",
            "subject_scope_concepts": ["actor:implicit"],
            "action_concept": "handoff",
            "argument_role_bindings": [
                {
                    "argument_ordinal": 1,
                    "relation": "direct",
                    "scope_concepts": ["input"],
                    "attachment": "governing-predicate",
                    "owner_action_concept": "handoff",
                    "owner_modality": "required",
                    "owner_polarity": "affirmative",
                },
                {
                    "argument_ordinal": 2,
                    "relation": "to",
                    "scope_concepts": ["output"],
                    "attachment": "governing-predicate",
                    "owner_action_concept": "handoff",
                    "owner_modality": "required",
                    "owner_polarity": "affirmative",
                },
            ],
            "object_scope_concepts": ["input", "output"],
            "condition_concepts": [],
            "modality": "required",
            "polarity": "affirmative",
        }
        CARRY._validate_semantic_fact(valid)
        variants = []
        noncontiguous = copy.deepcopy(valid)
        noncontiguous["argument_role_bindings"][1]["argument_ordinal"] = 3
        variants.append((noncontiguous, "argument ordinals must be contiguous"))
        unknown_relation = copy.deepcopy(valid)
        unknown_relation["argument_role_bindings"][1]["relation"] = "under"
        variants.append((unknown_relation, "unknown argument relation"))
        union_mismatch = copy.deepcopy(valid)
        union_mismatch["object_scope_concepts"] = ["input"]
        variants.append((union_mismatch, "object scope union mismatch"))
        for fact, message in variants:
            with self.subTest(message=message), self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                message,
            ):
                CARRY._validate_semantic_fact(fact)

    def test_predicate_projection_binds_root_and_reference_local_negation(
        self,
    ) -> None:
        baseline_text = (
            "# d\n\n## Professional Decision Rules\n\n"
            "- You must validate input and do not delete output.\n"
        )
        reversed_text = (
            "# d\n\n## Professional Decision Rules\n\n"
            "- Do not validate input and you must delete output.\n"
        )
        for source_class, material_field in (
            ("root", "roots"),
            ("indexed-reference", "references"),
        ):
            with self.subTest(source_class=source_class):
                baseline = _catalog(**{material_field: {"d": baseline_text}})
                changed = _catalog(**{material_field: {"d": reversed_text}})
                projection = CARRY.professional_semantic_fact_projection(
                    baseline[3]
                )
                actual_polarities = {
                    fact["action_concept"]: fact["polarity"]
                    for fact in projection["facts"]
                    if fact["source_class"] == source_class
                }
                self.assertEqual(
                    {"delete": "negative", "validate": "affirmative"},
                    actual_polarities,
                )
                baseline_binding = CARRY.professional_review_bindings(baseline)
                changed_binding = CARRY.professional_review_bindings(changed)
                self.assertNotEqual(
                    baseline_binding["d"]["package_material_binding"],
                    changed_binding["d"]["package_material_binding"],
                )
                plan = CARRY.plan_exact_professional_carry_forward(
                    current_bindings=changed_binding,
                    prior_snapshot=CARRY.professional_carry_snapshot(
                        baseline_binding,
                        review_contract_fingerprint=CONTRACT_FINGERPRINT,
                    ),
                    prior_decision_dependencies=self.dependencies,
                    review_contract_fingerprint=CONTRACT_FINGERPRINT,
                )
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])

    def test_confirm_and_verify_are_closed_validate_aliases(self) -> None:
        confirm = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Confirm output before release.\n"
                )
            }
        )
        verify = _catalog(
            roots={
                "d": (
                    "# d\n\n### Decision Rules\n\n"
                    "* **Verify** output prior to release.\n"
                )
            }
        )
        confirm_binding = CARRY.professional_review_bindings(confirm)
        verify_binding = CARRY.professional_review_bindings(verify)
        self.assertEqual(
            confirm_binding["d"]["package_material_binding"],
            verify_binding["d"]["package_material_binding"],
        )
        fact = next(
            row
            for row in CARRY.professional_semantic_fact_projection(confirm[3])[
                "facts"
            ]
            if row["source_class"] == "root"
        )
        self.assertEqual("validate", fact["action_concept"])

    def test_unknown_list_imperative_is_lexical_and_changes_binding(self) -> None:
        zorblate = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Zorblate output before release.\n"
                )
            }
        )
        flarnicate = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Flarnicate output before release.\n"
                )
            }
        )
        fact = next(
            row
            for row in CARRY.professional_semantic_fact_projection(zorblate[3])[
                "facts"
            ]
            if row["source_class"] == "root"
        )
        self.assertEqual("lexical:zorblate", fact["action_concept"])
        self.assertNotEqual(
            CARRY.professional_review_bindings(zorblate)["d"]
            ["package_material_binding"],
            CARRY.professional_review_bindings(flarnicate)["d"]
            ["package_material_binding"],
        )

    def test_material_paragraph_without_predicate_fails_closed(self) -> None:
        no_predicate = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "The zorbax and the quindle.\n"
                )
            }
        )
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "material semantic clause has no predicate",
        ):
            CARRY.professional_review_bindings(no_predicate)

    def test_table_row_preserves_header_cell_relation_and_object_disjunction(
        self,
    ) -> None:
        target = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "| Rule | Evidence |\n"
                    "| --- | --- |\n"
                    "| Validate input | test or benchmark |\n"
                )
            }
        )[3]
        root_facts = [
            row
            for row in CARRY.professional_semantic_fact_projection(target)[
                "facts"
            ]
            if row["source_class"] == "root"
        ]
        self.assertEqual(2, len(root_facts))
        evidence = next(
            row for row in root_facts if "evidence" in row["subject_scope_concepts"]
        )
        self.assertEqual("table-row", evidence["unit_kind"])
        self.assertEqual(2, evidence["predicate_ordinal"])
        self.assertEqual("then", evidence["incoming_connector"])
        self.assertEqual("define", evidence["action_concept"])
        self.assertEqual(
            ["term:benchmark", "test"], evidence["object_scope_concepts"]
        )

    def test_relative_modality_does_not_override_governing_predicate(self) -> None:
        target = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Validate input that may change before release.\n"
                )
            }
        )[3]
        root_facts = [
            row
            for row in CARRY.professional_semantic_fact_projection(target)[
                "facts"
            ]
            if row["source_class"] == "root"
        ]
        self.assertEqual(1, len(root_facts))
        self.assertEqual("required", root_facts[0]["modality"])
        self.assertIn(
            "modality:permitted", root_facts[0]["condition_concepts"]
        )

    def test_perform_and_execute_are_equivalent_closed_actions(self) -> None:
        perform = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "Perform one complete initial analysis.\n"
                )
            }
        )
        execute = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "Execute one complete initial analysis.\n"
                )
            }
        )
        perform_projection = CARRY.professional_semantic_fact_projection(
            perform[3]
        )
        perform_fact = next(
            row
            for row in perform_projection["facts"]
            if row["source_class"] == "root"
        )
        self.assertEqual("execute", perform_fact["action_concept"])
        self.assertEqual(
            CARRY.professional_review_bindings(perform)["d"]
            ["package_material_binding"],
            CARRY.professional_review_bindings(execute)["d"]
            ["package_material_binding"],
        )

    def test_action_like_noun_fragments_do_not_form_predicates(self) -> None:
        for fragment in (
            "The performance budget.",
            "The follow-up owner.",
            "The discard policy.",
        ):
            with self.subTest(fragment=fragment), self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "material semantic clause has no predicate",
            ):
                CARRY.professional_review_bindings(
                    _catalog(
                        roots={
                            "d": (
                                "# d\n\n## Professional Decision Rules\n\n"
                                f"{fragment}\n"
                            )
                        }
                    )
                )

    def test_closed_source_rewrites_emit_directional_predicates(self) -> None:
        source_text = (
            "# d\n\n## Professional Decision Rules\n\n"
            "Derive severity from reachable consequence and current policy.\n\n"
            "A GraphQL addition still requires schema-policy compliance "
            "and current consumer proof.\n\n"
            "At the first trusted ingress, remove untrusted client-identity "
            "headers or change those headers to the ingress-owned canonical "
            "form.\n"
        )
        baseline = _catalog(roots={"d": source_text})
        target = baseline[3]
        facts = [
            row
            for row in CARRY.professional_semantic_fact_projection(target)[
                "facts"
            ]
            if row["source_class"] == "root"
        ]
        by_action = {}
        for row in facts:
            by_action.setdefault(row["action_concept"], []).append(row)
        self.assertEqual(1, len(by_action["derive"]))
        self.assertEqual(1, len(by_action["require"]))
        self.assertEqual(1, len(by_action["delete"]))
        self.assertEqual(1, len(by_action["change"]))
        changed_header = by_action["change"][0]
        self.assertEqual("or", changed_header["incoming_connector"])
        self.assertIn("term:ingress", changed_header["subject_scope_concepts"])
        self.assertIn("term:headers", changed_header["object_scope_concepts"])

        retained = _catalog(
            roots={
                "d": source_text.replace(
                    "or change those headers", "or retain those headers"
                )
            }
        )
        self.assertNotEqual(
            CARRY.professional_review_bindings(baseline)["d"]
            ["package_material_binding"],
            CARRY.professional_review_bindings(retained)["d"]
            ["package_material_binding"],
        )

    def test_material_constraint_reversal_reopens_target_and_dependents(
        self,
    ) -> None:
        baseline = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Validate outputs before release.\n"
                )
            }
        )
        reversed_constraint = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "- Do not validate outputs before release.\n"
                )
            }
        )
        baseline_bindings = CARRY.professional_review_bindings(baseline)
        snapshot = CARRY.professional_carry_snapshot(
            baseline_bindings,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=CARRY.professional_review_bindings(
                reversed_constraint
            ),
            prior_snapshot=snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        self.assertEqual(["b", "d"], plan["fresh_target_ids"])
        self.assertIn(
            "target-material-changed", plan["reasons_by_target"]["d"]
        )
        self.assertIn(
            "required-candidate-material-changed",
            plan["reasons_by_target"]["b"],
        )

    def test_registry_fact_projection_ignores_display_spelling_but_binds_semantics(
        self,
    ) -> None:
        baseline = _catalog(
            responsibility_overrides={
                "d": {
                    "output_contract": [
                        "You must validate every output before release."
                    ]
                }
            }
        )
        equivalent = _catalog(
            responsibility_overrides={
                "d": {
                    "output_contract": [
                        "**Validte** outputs prior to release."
                    ]
                }
            }
        )
        changed = _catalog(
            responsibility_overrides={
                "d": {"output_contract": ["Delete outputs before release."]}
            }
        )
        expected_registry_fact = {
            "source_class": "registry",
            "fact_class": "required-output",
            "section_kind": "registry-output-contract",
            "unit_kind": "paragraph",
            "fact_kind": "obligation",
            "predicate_ordinal": 1,
            "incoming_connector": "root",
            "subject_scope_concepts": ["actor:implicit"],
            "action_concept": "validate",
            "argument_role_bindings": [
                {
                    "argument_ordinal": 1,
                    "relation": "direct",
                    "scope_concepts": ["output"],
                    "attachment": "governing-predicate",
                    "owner_action_concept": "validate",
                    "owner_modality": "required",
                    "owner_polarity": "affirmative",
                }
            ],
            "object_scope_concepts": ["output"],
            "condition_concepts": [
                "precondition",
                "release",
            ],
            "modality": "required",
            "polarity": "affirmative",
        }
        for targets in (baseline, equivalent):
            projection = CARRY.professional_semantic_fact_projection(
                targets[3]
            )
            self.assertIn(expected_registry_fact, projection["facts"])

        baseline_bindings = CARRY.professional_review_bindings(baseline)
        self.assertEqual(
            baseline_bindings["d"]["package_material_binding"],
            CARRY.professional_review_bindings(equivalent)["d"]
            ["package_material_binding"],
        )
        self.assertNotEqual(
            baseline_bindings["d"]["package_material_binding"],
            CARRY.professional_review_bindings(changed)["d"]
            ["package_material_binding"],
        )

    def test_ambiguous_material_fact_fails_closed_without_raw_hash_fallback(
        self,
    ) -> None:
        ambiguous = _catalog(
            roots={
                "d": (
                    "# d\n\n## Professional Decision Rules\n\n"
                    "The frobnicate and the flarn.\n"
                )
            }
        )
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "material semantic clause has no predicate",
        ):
            CARRY.professional_review_bindings(ambiguous)

    def test_professional_semantic_authority_changes_are_exact(self) -> None:
        cases = (
            (
                _catalog(registry_markers={"d": "changed-registry"}),
                [],
            ),
            (
                _catalog(
                    responsibility_overrides={
                        "d": {"output_contract": ["**Output**   d."]}
                    }
                ),
                [],
            ),
            (
                _catalog(expertise={"d": ["domain", "security"]}),
                "target-material-changed",
            ),
            (
                _catalog(layers={"d": "domain"}),
                "target-placement-changed",
            ),
            (
                _catalog(
                    responsibility_overrides={
                        "d": {"trigger_signals": ["changed routing trigger"]}
                    }
                ),
                "target-material-changed",
            ),
            (
                _catalog(
                    responsibility_overrides={
                        "d": {"output_contract": ["changed required output"]}
                    }
                ),
                "target-material-changed",
            ),
            (
                _catalog(
                    responsibility_overrides={
                        "d": {"escalation_signals": ["changed constraint"]}
                    }
                ),
                "target-material-changed",
            ),
            (
                _catalog(
                    responsibility_overrides={
                        "d": {"boundary_signals": ["changed boundary"]}
                    }
                ),
                "target-material-changed",
            ),
        )
        for targets, own_reason in cases:
            with self.subTest(reason=own_reason):
                plan = self._plan(targets)
                if own_reason == []:
                    self.assertEqual([], plan["fresh_target_ids"])
                    continue
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertIn(own_reason, plan["reasons_by_target"]["d"])
                self.assertIn(
                    "required-candidate-material-changed",
                    plan["reasons_by_target"]["b"],
                )

    def test_semantic_binding_rejects_missing_forged_and_unknown_authority(self) -> None:
        missing = _catalog()
        missing[0]["registry"]["responsibility_contract"].pop(
            "output_contract"
        )
        malformed = _catalog()
        malformed[0]["registry"]["responsibility_contract"][
            "required_inputs"
        ] = "not-a-list"
        noncanonical = _catalog()
        noncanonical[0]["required_expertise_tags"] = ["z", "a"]
        unknown_dependency = _catalog(
            required={"a": ["unknown"]},
            rankings={"a": ["b", "c", "d", "unknown"]},
        )
        for targets in (
            missing,
            malformed,
            noncanonical,
            unknown_dependency,
        ):
            with self.subTest(target=targets[0]), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.professional_review_bindings(targets)

        forged = copy.deepcopy(self.bindings)
        forged["a"]["package_material_binding"] = "0" * 64
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "package_material_binding is stale",
        ):
            CARRY.professional_carry_snapshot(
                forged,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )

    def test_unselected_ranking_churn_does_not_reopen_target(self) -> None:
        rank_plan = self._plan(
            _catalog(rankings={"d": ["c", "b", "a"]})
        )

        self.assertEqual([], rank_plan["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), rank_plan["carry_target_ids"])
        self.assertEqual([], rank_plan["reasons_by_target"]["d"])

    def test_required_list_change_reopens_only_target(self) -> None:
        required_plan = self._plan(
            _catalog(required={"b": ["d"], "c": ["a"], "d": ["a"]})
        )

        self.assertEqual(["d"], required_plan["fresh_target_ids"])
        self.assertEqual(
            ["adjacency-review-binding-changed"],
            required_plan["reasons_by_target"]["d"],
        )
        self.assertEqual([], required_plan["reasons_by_target"]["b"])

    def test_target_binding_contains_only_local_selection_authority(self) -> None:
        binding = self.bindings["b"]

        self.assertEqual(
            {
                "required_candidate_ids",
                "selection_contract_version",
            },
            set(binding["adjacency"]),
        )
        self.assertEqual(["d"], binding["adjacency"]["required_candidate_ids"])
        self.assertEqual(
            "fixture-selection-v1",
            binding["adjacency"]["selection_contract_version"],
        )
        serialized = CARRY.canonical_json_bytes(
            CARRY.professional_carry_snapshot(
                self.bindings,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )["targets"]["b"]
        )
        for forbidden in (
            b"content_fingerprint",
            b"own_material",
            b"required_candidates_fingerprint",
            b"full_catalog_ranking",
            b"full_catalog_ranking_fingerprint",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_catalog_intermediate_filter_change_does_not_stale_all_targets(self) -> None:
        changed = CARRY.professional_review_bindings(
            _catalog(document_filter_marker="changed-global-intermediate")
        )
        self.assertEqual(self.bindings, changed)
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=changed,
            prior_snapshot=self.snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        self.assertEqual([], plan["fresh_target_ids"])

    def test_minority_reviewer_added_dependency_is_union_and_one_hop(self) -> None:
        self.assertEqual(
            ["b"],
            self.dependencies["a"][
                "reviewer_added_candidate_ids_union"
            ],
        )
        # b changes. a is fresh because one prior ballot added b; c reviews a,
        # but a's fresh status is not recursively propagated to c.
        plan = self._plan(
            _catalog(
                roots={
                    "b": (
                        "# b\n\n## Professional Decision Rules\n\n"
                        "- Do not validate outputs before release.\n"
                    )
                }
            )
        )
        self.assertEqual(["a", "b"], plan["fresh_target_ids"])
        self.assertIn(
            "reviewer-added-candidate-material-changed",
            plan["reasons_by_target"]["a"],
        )
        self.assertEqual([], plan["reasons_by_target"]["c"])

    def test_duplicate_ballot_identity_cannot_form_complete_evidence(self) -> None:
        packet, ballots, decision = _prior_artifacts(self.targets)
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "duplicate voter_id"
        ):
            CARRY.professional_prior_decision_dependencies(
                prior_packet=packet,
                prior_ballots=[ballots[0], ballots[0], ballots[0]],
                prior_decision=decision,
            )

    def test_missing_evidence_and_nonaccepted_prior_are_never_carried(self) -> None:
        missing = copy.deepcopy(self.dependencies)
        missing["a"]["evidence_complete"] = False
        missing_plan = self._plan(
            self.targets, prior_decision_dependencies=missing
        )
        self.assertEqual(["a"], missing_plan["fresh_target_ids"])
        for disposition in (
            "requires-professional-correction",
            "unresolved-professional-disagreement",
        ):
            with self.subTest(disposition=disposition):
                nonaccepted = copy.deepcopy(self.dependencies)
                nonaccepted["a"]["final_disposition"] = disposition
                plan = self._plan(
                    self.targets,
                    prior_decision_dependencies=nonaccepted,
                )
                self.assertEqual(["a"], plan["fresh_target_ids"])
                self.assertIn(
                    "prior-final-not-accepted",
                    plan["reasons_by_target"]["a"],
                )

    def test_partition_and_reason_order_are_deterministic(self) -> None:
        targets = _catalog(
            roots={"b": "# b\n\nChanged deterministic evidence.\n"}
        )
        first = self._plan(targets)
        second = self._plan(copy.deepcopy(targets))
        self.assertEqual(first, second)
        self.assertEqual(
            CARRY.canonical_json_bytes(first),
            CARRY.canonical_json_bytes(second),
        )

    def test_capsule_exact_projection_and_reviewer_added_material(self) -> None:
        request = self._request("a", "b")
        capsule = CARRY.project_professional_review_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["a"],
            reviewer_added_requests_by_target={"a": [request]},
        )
        validated = CARRY.validate_professional_review_capsule(
            capsule,
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["a"],
            reviewer_added_requests_by_target={"a": [request]},
        )
        self.assertIs(capsule, validated)
        target = capsule["targets"][0]
        self.assertEqual(
            ["b"],
            [row["skill_id"] for row in target["candidate_material_manifest"]],
        )
        self.assertEqual(
            ["a", "b"],
            [row["skill_id"] for row in capsule["material_catalog"]],
        )
        self.assertNotIn("adjacency", capsule["material_catalog"][1])
        self.assertNotIn("material", target)
        self.assertNotIn("candidate_materials", target)
        self.assertIn("full_catalog_ranking", target["adjacency"])
        self.assertEqual(
            request["discovery_reason"],
            target["candidate_material_manifest"][0]["discovery_reason"],
        )

    def test_discovery_capsule_has_required_material_and_complete_boundary_catalog(self) -> None:
        discovery = CARRY.project_professional_discovery_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["b"],
        )
        self.assertIs(
            discovery,
            CARRY.validate_professional_discovery_capsule(
                discovery,
                bindings=self.bindings,
                review_targets=self.targets,
                assigned_fresh_target_ids=["b"],
            ),
        )
        self.assertEqual(
            list(SKILL_IDS),
            [row["skill_id"] for row in discovery["boundary_catalog"]],
        )
        self.assertEqual(
            ["b", "d"],
            [row["skill_id"] for row in discovery["material_catalog"]],
        )

    def test_capsule_rejects_extra_missing_duplicate_and_stale_projection(self) -> None:
        expected_arguments = {
            "bindings": self.bindings,
            "review_targets": self.targets,
            "assigned_fresh_target_ids": ["a"],
            "reviewer_added_requests_by_target": {
                "a": [self._request("a", "b")]
            },
        }
        capsule = CARRY.project_professional_review_capsule(**expected_arguments)
        mutations = []
        missing_target = copy.deepcopy(capsule)
        missing_target["targets"] = []
        mutations.append(missing_target)
        duplicate_target = copy.deepcopy(capsule)
        duplicate_target["targets"].append(copy.deepcopy(duplicate_target["targets"][0]))
        mutations.append(duplicate_target)
        missing_catalog_material = copy.deepcopy(capsule)
        missing_catalog_material["material_catalog"] = [
            row
            for row in missing_catalog_material["material_catalog"]
            if row["skill_id"] != "b"
        ]
        mutations.append(missing_catalog_material)
        duplicate_catalog_material = copy.deepcopy(capsule)
        duplicate_catalog_material["material_catalog"].append(
            copy.deepcopy(duplicate_catalog_material["material_catalog"][0])
        )
        mutations.append(duplicate_catalog_material)
        duplicate_candidate = copy.deepcopy(capsule)
        duplicate_candidate["targets"][0]["candidate_material_manifest"].append(
            copy.deepcopy(
                duplicate_candidate["targets"][0]["candidate_material_manifest"][0]
            )
        )
        mutations.append(duplicate_candidate)
        stale = copy.deepcopy(capsule)
        stale["material_catalog"][0]["own_material"]["root"][
            "content"
        ] += "stale"
        mutations.append(stale)
        extra_top_level_field = copy.deepcopy(capsule)
        extra_top_level_field["unexpected"] = True
        mutations.append(extra_top_level_field)
        extra_target_field = copy.deepcopy(capsule)
        extra_target_field["targets"][0]["unexpected"] = True
        mutations.append(extra_target_field)
        extra_nested_field = copy.deepcopy(capsule)
        extra_nested_field["targets"][0]["candidate_material_manifest"][0][
            "unexpected"
        ] = True
        mutations.append(extra_nested_field)
        extra = copy.deepcopy(capsule)
        extra_material = CARRY.project_professional_review_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["d"],
        )["material_catalog"][0]
        extra["material_catalog"].append(extra_material)
        mutations.append(extra)
        for index, value in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.validate_professional_review_capsule(
                    value, **expected_arguments
                )

    def test_raw_source_change_still_invalidates_capsule_integrity(self) -> None:
        capsule = CARRY.project_professional_review_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["b"],
        )
        changed_targets = _catalog(
            roots={"d": "# d\n\n**Review** d root behavior.\n"}
        )
        changed_bindings = CARRY.professional_review_bindings(
            changed_targets
        )
        plan = self._plan(changed_targets)
        self.assertEqual([], plan["fresh_target_ids"])
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "projection is stale|material_catalog projection is stale",
        ):
            CARRY.validate_professional_review_capsule(
                capsule,
                bindings=changed_bindings,
                review_targets=changed_targets,
                assigned_fresh_target_ids=["b"],
            )

        forged_targets = copy.deepcopy(changed_targets)
        forged_targets[3]["root"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "sha256 must bind content"
        ):
            CARRY.professional_review_bindings(forged_targets)

    def test_capsule_reviewer_added_ids_must_be_unique_ranked_and_not_required(self) -> None:
        for added in ([self._request("a", "a")], [self._request("a", "b")] * 2):
            with self.subTest(added=added), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.project_professional_review_capsule(
                    bindings=self.bindings,
                    review_targets=self.targets,
                    assigned_fresh_target_ids=["a"],
                    reviewer_added_requests_by_target={"a": added},
                )
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "already packet-required"
        ):
            CARRY.project_professional_review_capsule(
                bindings=self.bindings,
                review_targets=self.targets,
                assigned_fresh_target_ids=["b"],
                reviewer_added_requests_by_target={
                    "b": [self._request("b", "d")]
                },
            )

    def test_material_paths_must_be_canonical_repository_relative(self) -> None:
        for path in ("../escape.md", "a/../b.md", "a\\b.md", "/abs.md"):
            targets = copy.deepcopy(self.targets)
            targets[0]["root"]["path"] = path
            with self.subTest(path=path), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.professional_review_bindings(targets)

    def test_capsule_cost_proxy_uses_canonical_unicode_bytes(self) -> None:
        left = {"z": "技能", "a": {"b": 1}}
        right = {"a": {"b": 1}, "z": "技能"}
        self.assertEqual(
            CARRY.canonical_json_bytes(left), CARRY.canonical_json_bytes(right)
        )
        left_cost = CARRY.professional_review_capsule_cost_proxy(left)
        right_cost = CARRY.professional_review_capsule_cost_proxy(right)
        self.assertEqual(left_cost, right_cost)
        self.assertEqual(
            len(CARRY.canonical_json_bytes(left)),
            left_cost["canonical_json_bytes_proxy"],
        )
        self.assertTrue(all("proxy" in key or "available" in key for key in left_cost))


class ProfessionalReviewContractFingerprintTests(unittest.TestCase):
    def tearDown(self) -> None:
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()

    def test_review_contract_uses_canonical_semantic_projection(self) -> None:
        projection = CONTRACTS.professional_schema3_contract_projection()
        self.assertEqual(
            "professional-completeness-schema3-review-carry-v3",
            projection["contract_version"],
        )
        self.assertEqual(3, projection["artifact_contract"]["schema_version"])
        self.assertEqual(3, projection["panel"]["exact_votes_per_target"])
        self.assertEqual(
            CONTRACTS.canonical_json_sha256(projection),
            PANEL._professional_evidence_review_contract_fingerprint(),
        )

        encoded = CONTRACTS.canonical_json_bytes(projection)
        for forbidden in (
            b"scripts/",
            b"source_paths",
            b"created_on",
            b"review_id",
            b"selector",
            b'"report_path"',
            b"package_fingerprint",
            b"required-candidate-material-fingerprints",
            b"full-catalog-ranking-fingerprint",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_legacy_source_manifest_is_diagnostic_only(self) -> None:
        manifest = PANEL._professional_evidence_review_contract_manifest()
        self.assertEqual(
            "professional-evidence-review-and-carry-v3",
            manifest["contract_version"],
        )
        self.assertRegex(manifest["aggregate_source_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            [
                "scripts/audit-skill-content.py",
                "scripts/expert_panel_attestation.py",
                "scripts/expert_panel_review.py",
                "scripts/professional_completeness_carry_forward.py",
                "scripts/validation_utils.py",
            ],
            [row["path"] for row in manifest["source_manifest"]],
        )
        payload = {
            key: value
            for key, value in manifest.items()
            if key != "aggregate_source_digest"
        }
        self.assertEqual(
            CARRY.canonical_json_sha256(payload),
            manifest["aggregate_source_digest"],
        )
        self.assertNotEqual(
            manifest["aggregate_source_digest"],
            PANEL._professional_evidence_review_contract_fingerprint(),
        )

    def test_non_contract_source_bytes_do_not_change_semantic_digest(self) -> None:
        semantic_before = (
            CONTRACTS.professional_review_contract_fingerprint()
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            first = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v1",
                source_paths=("source.py",),
                repository_root=root,
            )
            source.write_text("VALUE = 2\n", encoding="utf-8")
            source_changed = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v1",
                source_paths=("source.py",),
                repository_root=root,
            )
        semantic_after = CONTRACTS.professional_review_contract_fingerprint()
        self.assertNotEqual(
            first["aggregate_source_digest"],
            source_changed["aggregate_source_digest"],
        )
        self.assertEqual(semantic_before, semantic_after)

    def test_contract_version_and_semantic_projection_change_digest(self) -> None:
        projection = CONTRACTS.professional_schema3_contract_projection()
        original = CONTRACTS.professional_review_contract_fingerprint(
            projection
        )
        changed_version = copy.deepcopy(projection)
        changed_version["contract_version"] = "fixture-v2"
        changed_rule = copy.deepcopy(projection)
        changed_rule["panel"]["minimum_winning_votes"] = 3

        self.assertNotEqual(
            original,
            CONTRACTS.professional_review_contract_fingerprint(
                changed_version
            ),
        )
        self.assertNotEqual(
            original,
            CONTRACTS.professional_review_contract_fingerprint(changed_rule),
        )


class ProfessionalPacketCompatibilityTests(unittest.TestCase):
    def test_schema1_inventory_count_is_a_strict_closed_integer_set(self) -> None:
        historical = _historical_schema1_packet()
        current = copy.deepcopy(_legacy_schema1_packet())
        PANEL._validate_professional_completeness_packet_v1(historical)
        PANEL._validate_professional_completeness_packet_v1(current)
        self.assertEqual(
            {"professional": 22, "foundation": 133, "domain": 7},
            PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS,
        )
        self.assertEqual(
            {"professional": 25, "foundation": 150, "domain": 13},
            PANEL.PROFESSIONAL_CURRENT_LAYER_COUNTS,
        )
        self.assertTrue(
            all(
                type(value) is int
                for counts in (
                    PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS,
                    PANEL.PROFESSIONAL_CURRENT_LAYER_COUNTS,
                )
                for value in counts.values()
            )
        )
        invalid_layer_cases = (
            (
                historical,
                "PROFESSIONAL_LEGACY_LAYER_COUNTS",
                "professional",
                22.0,
            ),
            (
                historical,
                "PROFESSIONAL_LEGACY_LAYER_COUNTS",
                "domain",
                True,
            ),
            (
                current,
                "PROFESSIONAL_CURRENT_LAYER_COUNTS",
                "professional",
                24.0,
            ),
            (
                current,
                "PROFESSIONAL_CURRENT_LAYER_COUNTS",
                "domain",
                False,
            ),
        )
        for source, constant_name, layer, invalid_count in invalid_layer_cases:
            with self.subTest(
                constant_name=constant_name,
                layer=layer,
                invalid_count=invalid_count,
            ):
                expected_counts = copy.deepcopy(
                    getattr(PANEL, constant_name)
                )
                expected_counts[layer] = invalid_count
                with mock.patch.object(
                    PANEL,
                    constant_name,
                    expected_counts,
                ), self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "target layers",
                ):
                    PANEL._validate_professional_completeness_packet_v1(
                        copy.deepcopy(source)
                    )

        invalid_cases = (
            (current, 187),
            (current, 189),
            (historical, 162.0),
            (current, 188.0),
            (current, True),
            (current, False),
            (current, "188"),
            (current, None),
        )
        for source, required_target_count in invalid_cases:
            with self.subTest(required_target_count=required_target_count):
                packet = copy.deepcopy(source)
                packet["panel_contract"][
                    "required_target_count"
                ] = required_target_count
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "panel_contract is invalid",
                ):
                    PANEL._validate_professional_completeness_packet_v1(
                        packet
                    )

    def test_schema2_packet_shape_and_canonical_bytes_remain_unchanged(self) -> None:
        packet = copy.deepcopy(_live_packet())
        before = CARRY.canonical_json_bytes(packet)
        bindings = PANEL._professional_review_bindings(
            packet["professional_targets"]
        )
        after = CARRY.canonical_json_bytes(packet)
        self.assertEqual(188, len(bindings))
        self.assertEqual(before, after)
        self.assertEqual(
            after,
            CARRY.canonical_json_bytes(json.loads(after)),
        )
        self.assertEqual(
            {
                "created_on",
                "kind",
                "limitations",
                "panel_contract",
                "professional_targets",
                "review_id",
                "rubric",
                "schema_version",
                "source_fingerprints",
            },
            set(packet),
        )
        self.assertEqual(
            {
                "indexed_references",
                "layer",
                "package_fingerprint",
                "registry",
                "required_expertise_tags",
                "root",
                "routing_adjacency",
                "skill_id",
            },
            set(packet["professional_targets"][0]),
        )

    def test_schema2_unregistered_selector_is_rejected_in_every_mode(self) -> None:
        packet = copy.deepcopy(_live_packet())
        selector = packet["panel_contract"]["adjacency_contract"][
            "required_candidate_selection"
        ]
        selector["version"] = "unregistered-selection-mutation"
        for target in packet["professional_targets"]:
            target["routing_adjacency"]["required_candidate_selection"] = (
                copy.deepcopy(selector)
            )
            without_fingerprint = copy.deepcopy(target)
            without_fingerprint.pop("package_fingerprint")
            target["package_fingerprint"] = _sha(without_fingerprint)
        packet["source_fingerprints"]["professional_packages"] = _sha(
            packet["professional_targets"]
        )

        for validation_mode in (
            PANEL.VALIDATION_MODE_CURRENT,
            PANEL.VALIDATION_MODE_HISTORICAL,
        ):
            with self.subTest(validation_mode=validation_mode), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "panel_contract",
            ):
                PANEL._validate_professional_completeness_packet_v2(
                    packet,
                    validation_mode=validation_mode,
                )

    def test_historical_cap50_adapter_is_exact_and_hash_preserving(self) -> None:
        decision, packet_ref, packet = _historical_schema3_adapter_fixture(
            cap50=True
        )
        adapted = PANEL._professional_v3_historical_cap50_packet(
            decision,
            packet_ref,
            packet,
        )
        self.assertEqual(_sha(packet), _sha(adapted))
        self.assertEqual(
            PANEL._professional_v3_panel_contract(
                target_count=162,
                include_selection_derivation=False,
            ),
            adapted["panel_contract"],
        )

        mutations = (
            (
                "packet-sha",
                lambda record, packet_ref, value: packet_ref.update(
                    {"sha256": "0" * 64}
                ),
            ),
            (
                "review-id",
                lambda record, packet_ref, value: record.update(
                    {"review_id": "professional-completeness-panel-other"}
                ),
            ),
            (
                "review-contract",
                lambda record, packet_ref, value: record.update(
                    {"review_contract_fingerprint": "0" * 64}
                ),
            ),
            (
                "target-count",
                lambda record, packet_ref, value: value[
                    "professional_targets"
                ].pop(),
            ),
            (
                "panel-cap",
                lambda record, packet_ref, value: value["panel_contract"][
                    "adjacency_contract"
                ]["required_candidate_selection"].update(
                    {"maximum_required_candidates_per_target": 49}
                ),
            ),
            (
                "target-cap",
                lambda record, packet_ref, value: value[
                    "professional_targets"
                ][0]["routing_adjacency"][
                    "required_candidate_selection"
                ].update({"maximum_required_candidates_per_target": 49}),
            ),
        )
        for label, mutate in mutations:
            record_value = copy.deepcopy(decision)
            mutated_packet_ref = copy.deepcopy(packet_ref)
            packet_value = copy.deepcopy(packet)
            mutate(record_value, mutated_packet_ref, packet_value)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._professional_v3_historical_cap50_packet(
                    record_value,
                    mutated_packet_ref,
                    packet_value,
                )
        with mock.patch.object(
            PANEL,
            "PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET",
            53,
        ), self.assertRaises(PANEL.PanelReviewError):
            PANEL._professional_v3_historical_cap50_packet(
                decision,
                packet_ref,
                packet,
            )

    def test_historical_r14_v1_adapter_is_exact_and_hash_preserving(self) -> None:
        decision, packet_ref, packet = _historical_schema3_adapter_fixture(
            cap50=False
        )
        adapted = PANEL._professional_v3_historical_v1_packet(
            decision,
            packet_ref,
            packet,
        )
        self.assertEqual(_sha(packet), _sha(adapted))
        self.assertEqual(
            PANEL._professional_v3_panel_contract(target_count=188),
            adapted["panel_contract"],
        )
        self.assertEqual(
            "declared_skills",
            next(
                key
                for key in adapted["professional_targets"][0][
                    "routing_adjacency"
                ]
                if key == "declared_skills"
            ),
        )

        mutations = (
            (
                "packet-sha",
                lambda record, packet_ref, value: packet_ref.update(
                    {"sha256": "0" * 64}
                ),
            ),
            (
                "review-id",
                lambda record, packet_ref, value: record.update(
                    {"review_id": "professional-completeness-panel-other"}
                ),
            ),
            (
                "review-contract",
                lambda record, packet_ref, value: record.update(
                    {"review_contract_fingerprint": "0" * 64}
                ),
            ),
            (
                "target-count",
                lambda record, packet_ref, value: value[
                    "professional_targets"
                ].pop(),
            ),
            (
                "selector-version",
                lambda record, packet_ref, value: value["panel_contract"][
                    "adjacency_contract"
                ]["required_candidate_selection"].update(
                    {"version": "layered-required-candidates-other"}
                ),
            ),
        )
        for label, mutate in mutations:
            record_value = copy.deepcopy(decision)
            mutated_packet_ref = copy.deepcopy(packet_ref)
            packet_value = copy.deepcopy(packet)
            mutate(record_value, mutated_packet_ref, packet_value)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._professional_v3_historical_v1_packet(
                    record_value,
                    mutated_packet_ref,
                    packet_value,
                )

    def test_historical_schema3_decision_remains_auditable_for_carry(self) -> None:
        with professional_support._synthetic_schema3_professional_decision() as fixture:
            decision = fixture["decision"]
            validation_root = fixture["validation_root"]
            with mock.patch.object(
                PANEL,
                "_professional_evidence_review_contract_fingerprint",
                return_value="0" * 64,
            ), mock.patch.object(
                PANEL, "PROFESSIONAL_ADJACENCY_TOP_K", 0
            ), mock.patch.object(
                PANEL, "PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K", 0
            ):
                self.assertEqual(
                    decision,
                    PANEL.validate_decision_record(
                        decision,
                        record_path=fixture["decision_path"],
                        validation_root=validation_root,
                        validation_mode="historical",
                    ),
                )

            dependencies = CARRY.professional_prior_decision_dependencies(
                prior_packet=fixture["packet"],
                prior_ballots=[ballot for _path, ballot in fixture["ballots"]],
                prior_decision=decision,
            )
            self.assertEqual(PANEL.PROFESSIONAL_PACKAGE_COUNT, len(dependencies))
            self.assertTrue(
                all(row["evidence_complete"] for row in dependencies.values())
            )

    def test_schema1_legacy_packet_bytes_and_validator_remain_compatible(self) -> None:
        packet = copy.deepcopy(_legacy_schema1_packet())
        before = CARRY.canonical_json_bytes(packet)
        PANEL._validate_professional_completeness_packet(packet)
        template = PANEL.prepare_professional_completeness_ballot_template(
            packet=packet,
            packet_sha256="b" * 64,
            voter_id="legacy-reviewer",
            agent_id="legacy-agent",
            role="legacy-professional-reviewer",
            expertise=["legacy completeness"],
            expertise_tags=None,
            skill_ids=None,
            created_on="2026-07-17",
        )
        PANEL.validate_ballot_template(
            packet,
            template,
            packet_sha256="b" * 64,
        )
        self.assertEqual(before, CARRY.canonical_json_bytes(packet))
        self.assertEqual(
            before,
            CARRY.canonical_json_bytes(json.loads(before)),
        )


if __name__ == "__main__":
    unittest.main()
