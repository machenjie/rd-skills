from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
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


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import professional_completeness_carry_forward as CARRY


def _load_panel(module_name: str = "carry_forward_panel_tests"):
    path = SCRIPTS / "expert_panel_review.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PANEL = _load_panel()
SKILL_IDS = ("a", "b", "c", "d")
CONTRACT_FINGERPRINT = "a" * 64


def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _load_contract_fixture(path: Path, module_name: str, source: str):
    path.write_text(source, encoding="utf-8")
    linecache.clearcache()
    module = types.ModuleType(module_name)
    module.__file__ = path.as_posix()
    sys.modules[module_name] = module
    exec(compile(source, path.as_posix(), "exec"), module.__dict__)
    return module


def _material(skill_id: str, part: str, content: str) -> dict:
    return {
        "path": f"src/{skill_id}/{part}.md",
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "line_count": len(content.splitlines()),
        "content": content,
    }


def _catalog(
    *,
    roots: dict[str, str] | None = None,
    references: dict[str, str] | None = None,
    registry_markers: dict[str, str] | None = None,
    expertise: dict[str, list[str]] | None = None,
    layers: dict[str, str] | None = None,
    required: dict[str, list[str]] | None = None,
    rankings: dict[str, list[str]] | None = None,
    document_filter_marker: str = "baseline-filter",
) -> list[dict]:
    roots = roots or {}
    references = references or {}
    registry_markers = registry_markers or {}
    expertise = expertise or {}
    layers = layers or {}
    required = required or {"b": ["d"], "c": ["a"]}
    rankings = rankings or {}
    targets = []
    for skill_id in SKILL_IDS:
        root_content = roots.get(
            skill_id, f"# {skill_id}\n\nReview {skill_id} root behavior.\n"
        )
        reference_content = references.get(
            skill_id,
            f"# {skill_id} Reference\n\nVerify {skill_id} failure evidence.\n",
        )
        ranking_ids = rankings.get(
            skill_id, sorted(set(SKILL_IDS) - {skill_id})
        )
        ranking = [
            {
                "skill_id": candidate_id,
                "rank": rank,
                "total_score": 0,
                "signals": {},
            }
            for rank, candidate_id in enumerate(ranking_ids, start=1)
        ]
        ranking_by_id = {row["skill_id"]: row for row in ranking}
        required_ids = sorted(required.get(skill_id, []))
        required_candidates = [
            {
                **ranking_by_id[candidate_id],
                "declared": False,
                "selection_reasons": ["fixture-required"],
            }
            for candidate_id in required_ids
        ]
        responsibility = {
            "marker": registry_markers.get(skill_id, "baseline-registry"),
            "trigger_signals": [f"trigger {skill_id}"],
            "output_contract": [f"output {skill_id}"],
        }
        registry_row = {
            "name": skill_id,
            "responsibility_contract": responsibility,
        }
        adjacency = {
            "algorithm": "fixture-ranking-v1",
            "document_frequency_filter": {
                "catalog_wide_intermediate": document_filter_marker
            },
            "declared_skills": [],
            "required_candidate_selection": {
                "version": "fixture-selection-v1"
            },
            "required_candidates": required_candidates,
            "required_candidates_fingerprint": _sha(required_candidates),
            "full_catalog_count": len(ranking),
            "full_catalog_ranking": ranking,
            "full_catalog_ranking_fingerprint": _sha(ranking),
        }
        target = {
            "skill_id": skill_id,
            "layer": layers.get(skill_id, "foundation"),
            "required_expertise_tags": expertise.get(skill_id, ["domain"]),
            "root": _material(skill_id, "SKILL", root_content),
            "indexed_references": [
                _material(skill_id, "reference", reference_content)
            ],
            "registry": {
                "path": "src/registry.yaml",
                "entry_fingerprint": _sha(registry_row),
                "responsibility_contract": responsibility,
            },
            "routing_adjacency": adjacency,
        }
        target["package_fingerprint"] = _sha(target)
        targets.append(target)
    return targets


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


@lru_cache(maxsize=1)
def _live_packet() -> dict:
    return PANEL.prepare_professional_completeness_packet(
        review_id="carry-baseline",
        created_on="2026-07-17",
    )


@lru_cache(maxsize=1)
def _legacy_schema1_packet() -> dict:
    current = _live_packet()
    targets = []
    for current_target in current["professional_targets"]:
        responsibility = copy.deepcopy(
            current_target["registry"]["responsibility_contract"]
        )
        adjacent_skills = copy.deepcopy(
            current_target["routing_adjacency"]["declared_skills"]
        )
        routing_basis = {
            "skill_id": current_target["skill_id"],
            "layer": current_target["layer"],
            "role_support": responsibility["role_support"],
            "trigger_signals": responsibility["trigger_signals"],
            "anti_trigger_signals": responsibility["anti_trigger_signals"],
            "output_contract": responsibility["output_contract"],
            "adjacent_skills": adjacent_skills,
        }
        target = {
            "skill_id": current_target["skill_id"],
            "layer": current_target["layer"],
            "root": {
                "path": current_target["root"]["path"],
                "sha256": current_target["root"]["sha256"],
            },
            "indexed_references": [
                {"path": row["path"], "sha256": row["sha256"]}
                for row in current_target["indexed_references"]
            ],
            "registry": {
                "path": current_target["registry"]["path"],
                "entry_fingerprint": current_target["registry"][
                    "entry_fingerprint"
                ],
                "responsibility_contract": responsibility,
            },
            "routing_adjacency": {
                "skills": adjacent_skills,
                "fingerprint": _sha(routing_basis),
            },
        }
        target["package_fingerprint"] = _sha(target)
        targets.append(target)
    return {
        "schema_version": PANEL.SCHEMA_VERSION,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "review_id": "legacy-carry-baseline",
        "created_on": "2026-07-17",
        "source_fingerprints": {"professional_packages": _sha(targets)},
        "panel_contract": {
            "decision_method": PANEL.DECISION_METHOD,
            "required_voters": PANEL.PANEL_SIZE,
            "abstentions_allowed": False,
            "minimum_winning_votes": 2,
            "independent_ballots": True,
            "required_target_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
            "criteria_required_per_target": sorted(
                PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA
            ),
        },
        "rubric": {
            "accept": "Accept the complete legacy package.",
            "correct": "Correct any legacy professional defect.",
            "criteria": dict(
                sorted(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA.items())
            ),
            "reason_codes": {
                decision: sorted(PANEL.PROFESSIONAL_REASON_CODES[decision])
                for decision in sorted(
                    PANEL.PROFESSIONAL_COMPLETENESS_DECISIONS
                )
            },
        },
        "professional_targets": targets,
        "limitations": ["Legacy static fixture."],
    }


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
        ranking = next(
            (
                row
                for row in self.bindings[target_id]["adjacency"][
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
            "candidate_material_fingerprint", "f" * 64
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

    def test_root_and_reference_changes_expand_to_required_candidate_once(self) -> None:
        root_plan = self._plan(
            _catalog(roots={"d": "# d\n\nChanged d root evidence.\n"})
        )
        reference_plan = self._plan(
            _catalog(
                references={
                    "d": "# d Reference\n\nChanged d failure evidence.\n"
                }
            )
        )
        for plan in (root_plan, reference_plan):
            self.assertEqual(["b", "d"], plan["fresh_target_ids"])
            self.assertIn(
                "required-candidate-material-changed",
                plan["reasons_by_target"]["b"],
            )
            self.assertEqual([], plan["reasons_by_target"]["a"])

    def test_registry_expertise_and_layer_changes_are_exact(self) -> None:
        cases = (
            (
                _catalog(registry_markers={"d": "changed-registry"}),
                "registry-responsibility-changed",
            ),
            (
                _catalog(expertise={"d": ["domain", "security"]}),
                "required-expertise-changed",
            ),
            (
                _catalog(layers={"d": "domain"}),
                "target-placement-changed",
            ),
        )
        for targets, own_reason in cases:
            with self.subTest(reason=own_reason):
                plan = self._plan(targets)
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertIn(own_reason, plan["reasons_by_target"]["d"])
                self.assertIn(
                    "required-candidate-material-changed",
                    plan["reasons_by_target"]["b"],
                )

    def test_rank_or_required_list_change_does_not_recursively_spread(self) -> None:
        rank_plan = self._plan(
            _catalog(rankings={"d": ["c", "b", "a"]})
        )
        required_plan = self._plan(
            _catalog(required={"b": ["d"], "c": ["a"], "d": ["a"]})
        )
        for plan in (rank_plan, required_plan):
            self.assertEqual(["d"], plan["fresh_target_ids"])
            self.assertEqual(
                ["adjacency-review-binding-changed"],
                plan["reasons_by_target"]["d"],
            )
            self.assertEqual([], plan["reasons_by_target"]["b"])

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
            _catalog(roots={"b": "# b\n\nChanged b source material.\n"})
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
            assigned_fresh_target_ids=["a"],
            reviewer_added_requests_by_target={"a": [request]},
        )
        validated = CARRY.validate_professional_review_capsule(
            capsule,
            bindings=self.bindings,
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
            assigned_fresh_target_ids=["b"],
        )
        self.assertIs(
            discovery,
            CARRY.validate_professional_discovery_capsule(
                discovery,
                bindings=self.bindings,
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

    def test_capsule_reviewer_added_ids_must_be_unique_ranked_and_not_required(self) -> None:
        for added in ([self._request("a", "a")], [self._request("a", "b")] * 2):
            with self.subTest(added=added), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.project_professional_review_capsule(
                    bindings=self.bindings,
                    assigned_fresh_target_ids=["a"],
                    reviewer_added_requests_by_target={"a": added},
                )
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "already packet-required"
        ):
            CARRY.project_professional_review_capsule(
                bindings=self.bindings,
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

    def test_relevant_callable_and_contract_constant_change_fingerprint(self) -> None:
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
        baseline = PANEL._professional_evidence_review_contract_fingerprint()
        with mock.patch.object(
            PANEL,
            "_substantive_excerpt",
            lambda content, *, start_line, end_line: "changed",
        ):
            PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
            callable_changed = (
                PANEL._professional_evidence_review_contract_fingerprint()
            )
        with mock.patch.object(
            PANEL,
            "PROFESSIONAL_CRITERION_VALUES",
            {"satisfied", "defect-found", "fixture-new-value"},
        ):
            PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
            constant_changed = (
                PANEL._professional_evidence_review_contract_fingerprint()
            )
        with mock.patch.object(
            PANEL.professional_carry,
            "professional_materials_by_skill",
            lambda targets: {},
        ):
            PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
            material_resolution_changed = (
                PANEL._professional_evidence_review_contract_fingerprint()
            )
        self.assertNotEqual(baseline, callable_changed)
        self.assertNotEqual(baseline, constant_changed)
        self.assertNotEqual(baseline, material_resolution_changed)

    def test_cross_version_portable_golden(self) -> None:
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
        self.assertEqual(
            "f80ffe96349a5cf35fc5c02ea698ede77e01c892a24fa35b1baecc1d9ec48fa1",
            PANEL._professional_evidence_review_contract_fingerprint(),
        )

    def test_production_packet_seal_identity_boundary_is_explicit(self) -> None:
        class_identity = CARRY._callable_identity(
            PANEL._ProfessionalV3CanonicalPacketState,
            repository_root=ROOT,
        )
        issuer_identity = CARRY._callable_identity(
            PANEL._professional_v3_canonical_packet_state,
            repository_root=ROOT,
        )
        self.assertEqual(
            {
                "scripts/expert_panel_review.py:_professional_v3_packet_state_boundary.<locals>._ProfessionalV3CanonicalPacketState",
                "scripts/expert_panel_review.py:_professional_v3_packet_state_boundary.<locals>.canonical_packet_state",
            },
            {class_identity, issuer_identity},
        )
        self.assertTrue(
            {class_identity, issuer_identity}
            <= CARRY._PROCESS_LOCAL_IDENTITY_BOUNDARIES
        )
        self.assertEqual(
            {class_identity, issuer_identity},
            CARRY._OPAQUE_IDENTITY_CLOSURE_BOUNDARIES,
        )
        class_seal = CARRY._callable_closure_values(
            PANEL._ProfessionalV3CanonicalPacketState
        )["_validate_binding:seal"]
        issuer_seal = CARRY._callable_closure_values(
            PANEL._professional_v3_canonical_packet_state
        )["callable:seal"]
        self.assertIs(class_seal, issuer_seal)
        projector = CARRY._ContractValueProjector(repository_root=ROOT)
        class_reference = projector.project(
            class_seal,
            allow_opaque_object=True,
            value_label="packet seal",
        )
        issuer_reference = projector.project(
            issuer_seal,
            allow_opaque_object=True,
            value_label="packet seal",
        )
        self.assertEqual(class_reference, issuer_reference)
        self.assertRegex(
            PANEL._professional_evidence_review_contract_fingerprint(),
            r"^[0-9a-f]{64}$",
        )

    def test_packet_seal_opaque_usage_is_closed(self) -> None:
        seal = object()
        allowed = (
            (
                CARRY._PACKET_STATE_CLASS_IDENTITY,
                "def check(self):\n    return self.__seal is seal\n",
            ),
            (
                CARRY._PACKET_STATE_ISSUER_IDENTITY,
                'def issue():\n    values = {"seal": seal}\n    return values\n',
            ),
        )
        for identity, source in allowed:
            with self.subTest(allowed_identity=identity):
                CARRY._identity_observation_names(
                    ast.parse(source),
                    callable_identity=identity,
                    resolved_names={"seal": seal},
                )

        rejected = (
            "def leak():\n    return repr(seal)\n",
            "def leak():\n    return str(seal)\n",
            "def leak():\n    return hash(seal)\n",
            "def leak(helper):\n    return helper(seal)\n",
            "def leak():\n    return seal\n",
        )
        for source in rejected:
            with self.subTest(rejected_source=source), self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "opaque identity closure has unsupported use",
            ):
                CARRY._identity_observation_names(
                    ast.parse(source),
                    callable_identity=CARRY._PACKET_STATE_ISSUER_IDENTITY,
                    resolved_names={
                        "hash": hash,
                        "repr": repr,
                        "seal": seal,
                        "str": str,
                    },
                )

    def test_decorated_detector_body_is_bound(self) -> None:
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
        baseline = PANEL._professional_evidence_review_contract_fingerprint()

        @lru_cache(maxsize=1024)
        def changed_detector(content: str) -> frozenset[int]:
            return frozenset({len(content)})

        with mock.patch.object(
            PANEL, "_detector_unfenced_line_numbers", changed_detector
        ):
            PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
            changed = PANEL._professional_evidence_review_contract_fingerprint()
        self.assertNotEqual(baseline, changed)

    def test_fingerprint_is_stable_across_import_module_names(self) -> None:
        alias = _load_panel("carry_forward_panel_alias_tests")
        self.assertEqual(
            PANEL._professional_evidence_review_contract_fingerprint(),
            alias._professional_evidence_review_contract_fingerprint(),
        )

    def test_unrelated_cli_callable_change_does_not_change_fingerprint(self) -> None:
        baseline = PANEL._professional_evidence_review_contract_fingerprint()
        with mock.patch.object(PANEL, "main", lambda: "unrelated CLI wording"):
            changed = PANEL._professional_evidence_review_contract_fingerprint()
        self.assertEqual(baseline, changed)

    def test_source_ast_ignores_formatting_comments_and_literal_spelling(self) -> None:
        first = '''\
CONTRACT_VALUE = {"mode": "strict"}

def dependency(value):
    # An explanatory comment is not executable contract behavior.
    return value + 1

def root(value=2, *, flag=True):
    return dependency(value) if flag else CONTRACT_VALUE["mode"]
'''
        second = '''\
CONTRACT_VALUE={'mode': 'strict'}

def dependency( value ):
    return (value + 0x1)  # Different formatting and literal spelling.

def root(
    value = 0x2,
    *,
    flag = True,
):
    return (dependency(value) if flag else CONTRACT_VALUE['mode'])
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            left = _load_contract_fixture(path, "contract_ast_left", first)
            left_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(left.root,),
                constants={},
                repository_root=ROOT,
            )
            right = _load_contract_fixture(path, "contract_ast_right", second)
            right_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(right.root,),
                constants={},
                repository_root=ROOT,
            )
        self.assertEqual(left_fingerprint, right_fingerprint)

    def test_source_ast_tracks_behavior_defaults_and_referenced_constants(self) -> None:
        source = '''\
LIMIT = 3

def dependency(value):
    return value + 1

def root(value=2, *, enabled=True):
    def nested():
        return LIMIT
    return dependency(value) + nested() if enabled else value
'''
        changed_dependency = source.replace("value + 1", "value - 1")
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            baseline_module = _load_contract_fixture(
                path, "contract_behavior_baseline", source
            )

            def fingerprint(module):
                return CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={},
                    repository_root=ROOT,
                )

            baseline = fingerprint(baseline_module)
            baseline_module.LIMIT = 4
            self.assertNotEqual(baseline, fingerprint(baseline_module))
            baseline_module.LIMIT = 3
            baseline_module.root.__defaults__ = (5,)
            self.assertNotEqual(baseline, fingerprint(baseline_module))
            baseline_module.root.__defaults__ = (2,)
            baseline_module.root.__kwdefaults__ = {"enabled": False}
            self.assertNotEqual(baseline, fingerprint(baseline_module))
            changed_module = _load_contract_fixture(
                path, "contract_behavior_changed", changed_dependency
            )
            self.assertNotEqual(baseline, fingerprint(changed_module))

    def test_definition_time_dependencies_are_bound(self) -> None:
        decorator_source = '''\
def contract_decorator(function):
    function.contract_marker = "left"
    return function

@contract_decorator
def root():
    return 1
'''
        default_source = '''\
def make_default():
    return 1

def root(value=make_default()):
    return value
'''
        annotation_source = '''\
class Marker:
    def contract_value(self):
        return "left"

def root(value: Marker) -> Marker:
    return value
'''
        class_source = '''\
class ContractMeta(type):
    def contract_value(cls):
        return "meta-left"

class ContractBase:
    def contract_value(self):
        return "base-left"

class Root(ContractBase, metaclass=ContractMeta):
    pass
'''
        cases = (
            (
                "decorator",
                decorator_source,
                decorator_source.replace('"left"', '"right"'),
                "root",
            ),
            (
                "default",
                default_source,
                default_source.replace("return 1\n\n", 'return int("1")\n\n'),
                "root",
            ),
            (
                "annotation",
                annotation_source,
                annotation_source.replace('"left"', '"right"'),
                "root",
            ),
            (
                "base",
                class_source,
                class_source.replace('"base-left"', '"base-right"'),
                "Root",
            ),
            (
                "metaclass",
                class_source,
                class_source.replace('"meta-left"', '"meta-right"'),
                "Root",
            ),
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for label, baseline_source, changed_source, root_name in cases:
                with self.subTest(dependency=label):
                    baseline_module = _load_contract_fixture(
                        path, f"contract_definition_{label}_baseline", baseline_source
                    )
                    baseline = CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(getattr(baseline_module, root_name),),
                        constants={},
                        repository_root=ROOT,
                    )
                    changed_module = _load_contract_fixture(
                        path, f"contract_definition_{label}_changed", changed_source
                    )
                    changed = CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(getattr(changed_module, root_name),),
                        constants={},
                        repository_root=ROOT,
                    )
                    self.assertNotEqual(baseline, changed)

    def test_closure_partial_bound_method_and_lowercase_global_state_are_bound(
        self,
    ) -> None:
        closure_source = '''\
def make_root(marker):
    def root():
        return marker
    return root

root = make_root("left")
'''
        partial_source = '''\
from functools import partial

def add(left, right):
    return left + right

adjust = partial(add, 2)

def root(value):
    return adjust(value)
'''
        bound_method_source = '''\
separator = ",".join

def root(values):
    return separator(values)
'''
        lowercase_source = '''\
settings = {"mode": "left"}

def root():
    return settings["mode"]
'''
        typing_source = '''\
import typing

alias = typing.List[str]

def root():
    return alias
'''
        cases = (
            ("closure", closure_source, closure_source.replace('"left"', '"right"')),
            ("partial", partial_source, partial_source.replace("partial(add, 2)", "partial(add, 3)")),
            ("bound-method", bound_method_source, bound_method_source.replace('",".join', '"|".join')),
            ("lowercase-global", lowercase_source, lowercase_source.replace('"left"', '"right"')),
            (
                "typing-parameter",
                typing_source,
                typing_source.replace("typing.List[str]", "typing.List[int]"),
            ),
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for label, baseline_source, changed_source in cases:
                with self.subTest(state=label):
                    baseline_module = _load_contract_fixture(
                        path, f"contract_state_{label}_baseline", baseline_source
                    )
                    baseline = CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(baseline_module.root,),
                        constants={},
                        repository_root=ROOT,
                    )
                    changed_module = _load_contract_fixture(
                        path, f"contract_state_{label}_changed", changed_source
                    )
                    changed = CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(changed_module.root,),
                        constants={},
                        repository_root=ROOT,
                    )
                    self.assertNotEqual(baseline, changed)

    def test_mutated_object_default_state_is_bound(self) -> None:
        source = '''\
class Config:
    def __init__(self):
        self.value = 1

def root(config=Config()):
    return config.value
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_object_default", source
            )
            baseline = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(module.root,),
                constants={},
                repository_root=ROOT,
            )
            module.root.__defaults__[0].value = 2
            changed = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(module.root,),
                constants={},
                repository_root=ROOT,
            )
        self.assertNotEqual(baseline, changed)

    def test_mapping_key_types_do_not_collapse(self) -> None:
        integer_source = '''\
settings = {1: "value"}

def root():
    return settings
'''
        string_source = integer_source.replace("{1:", '{"1":')
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            integer_module = _load_contract_fixture(
                path, "contract_mapping_integer", integer_source
            )
            integer_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(integer_module.root,),
                constants={},
                repository_root=ROOT,
            )
            string_module = _load_contract_fixture(
                path, "contract_mapping_string", string_source
            )
            string_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(string_module.root,),
                constants={},
                repository_root=ROOT,
            )
        self.assertNotEqual(integer_fingerprint, string_fingerprint)

    def test_runtime_and_explicit_container_types_do_not_collapse(self) -> None:
        source = '''\
state = None

def root():
    return state
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_runtime_shapes", source
            )

            def runtime_fingerprint(value):
                module.state = value
                return CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={},
                    repository_root=ROOT,
                )

            self.assertNotEqual(
                runtime_fingerprint([1, 2]),
                runtime_fingerprint((1, 2)),
            )
            self.assertNotEqual(
                runtime_fingerprint({1, 2}),
                runtime_fingerprint(frozenset({1, 2})),
            )
            self.assertNotEqual(
                runtime_fingerprint(Path("contract-shape")),
                runtime_fingerprint("contract-shape"),
            )

            self.assertNotEqual(
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={"value": [1, 2]},
                    repository_root=ROOT,
                ),
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={"value": (1, 2)},
                    repository_root=ROOT,
                ),
            )

    def test_mapping_order_is_contract_behavior(self) -> None:
        source = '''\
state = None

def root():
    return tuple(state.items())
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_mapping_order", source
            )

            def runtime_fingerprint(value):
                module.state = value
                return CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={},
                    repository_root=ROOT,
                )

            forward = {"first": 1, "second": 2}
            reverse = {"second": 2, "first": 1}
            self.assertEqual(forward, reverse)
            self.assertNotEqual(
                runtime_fingerprint(forward),
                runtime_fingerprint(reverse),
            )
            self.assertNotEqual(
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={"value": forward},
                    repository_root=ROOT,
                ),
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={"value": reverse},
                    repository_root=ROOT,
                ),
            )

    def test_value_graph_tracks_aliases_and_cycles_stably(self) -> None:
        source = '''\
state = None

def root():
    return state
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_value_topology", source
            )

            def fingerprint(value):
                module.state = value
                return CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(module.root,),
                    constants={},
                    repository_root=ROOT,
                )

            shared_child: list[object] = []
            shared = fingerprint([shared_child, shared_child])
            distinct = fingerprint([[], []])
            self.assertNotEqual(shared, distinct)

            first_cycle: list[object] = []
            first_cycle.append(first_cycle)
            second_cycle: list[object] = []
            second_cycle.append(second_cycle)
            self.assertEqual(
                fingerprint(first_cycle), fingerprint(second_cycle)
            )

    def test_generic_opaque_sentinel_closures_fail_closed(self) -> None:
        shared_source = '''\
def make_root(first, second):
    def root():
        return first is second
    return root

sentinel = object()
root = make_root(sentinel, sentinel)
'''
        distinct_source = shared_source.replace(
            "sentinel = object()\nroot = make_root(sentinel, sentinel)",
            "root = make_root(object(), object())",
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            first_shared = _load_contract_fixture(
                path, "contract_opaque_shared_first", shared_source
            )
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "builtins.object",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(first_shared.root,),
                    constants={},
                    repository_root=ROOT,
                )
            distinct = _load_contract_fixture(
                path, "contract_opaque_distinct", distinct_source
            )
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "builtins.object",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(distinct.root,),
                    constants={},
                    repository_root=ROOT,
                )

    def test_callable_and_module_identity_aliases_fail_closed(self) -> None:
        source = '''\
def make_root(first, second):
    def root():
        return first is second
    return root
'''

        def external_callable() -> object:
            namespace = {"__name__": "external_identity_fixture"}
            exec(
                compile(
                    "def sentinel():\n    return None\n",
                    "<external-identity-fixture>",
                    "exec",
                ),
                namespace,
            )
            return namespace["sentinel"]

        first_callable = external_callable()
        second_callable = external_callable()
        self.assertIsNot(first_callable, second_callable)
        self.assertEqual(
            CARRY._external_callable_contract(
                first_callable, repository_root=ROOT
            ),
            CARRY._external_callable_contract(
                second_callable, repository_root=ROOT
            ),
        )
        first_module = types.ModuleType("external_identity_module")
        second_module = types.ModuleType("external_identity_module")
        self.assertIsNot(first_module, second_module)

        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_callable_module_identity", source
            )
            for kind, first, second in (
                ("callable-shared", first_callable, first_callable),
                ("callable-distinct", first_callable, second_callable),
                ("module-shared", first_module, first_module),
                ("module-distinct", first_module, second_module),
            ):
                root = module.make_root(first, second)
                with self.subTest(identity_topology=kind), self.assertRaisesRegex(
                    CARRY.ProfessionalCarryForwardError,
                    "unsupported non-singleton identity comparison",
                ):
                    CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(root,),
                        constants={},
                        repository_root=ROOT,
                    )

    def test_callable_and_module_alias_topology_is_bound(self) -> None:
        def external_callable() -> object:
            namespace = {"__name__": "external_alias_topology_fixture"}
            exec(
                compile(
                    "def sentinel():\n    return None\n",
                    "<external-alias-topology-fixture>",
                    "exec",
                ),
                namespace,
            )
            return namespace["sentinel"]

        first_callable = external_callable()
        second_callable = external_callable()
        self.assertIsNot(first_callable, second_callable)
        self.assertEqual(
            CARRY._external_callable_contract(
                first_callable, repository_root=ROOT
            ),
            CARRY._external_callable_contract(
                second_callable, repository_root=ROOT
            ),
        )
        first_module = types.ModuleType("external_alias_topology_module")
        second_module = types.ModuleType("external_alias_topology_module")
        self.assertIsNot(first_module, second_module)
        observers = {
            "hash": "return hash(first) == hash(second)",
            "repr": "return repr(first) == repr(second)",
            "equality": "return first == second",
            "container": "return len({first, second})",
        }

        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for observer, statement in observers.items():
                source = f'''\
def make_root(first, second):
    def root():
        {statement}
    return root
'''
                module = _load_contract_fixture(
                    path, f"contract_alias_topology_{observer}", source
                )
                for value_kind, first, second in (
                    ("callable", first_callable, second_callable),
                    ("module", first_module, second_module),
                ):
                    shared_root = module.make_root(first, first)
                    distinct_root = module.make_root(first, second)
                    if value_kind == "callable" or observer != "repr":
                        self.assertNotEqual(shared_root(), distinct_root())
                    with self.subTest(
                        observer=observer, value_kind=value_kind
                    ):
                        shared_fingerprint = (
                            CARRY.code_aware_contract_fingerprint(
                                contract_name="fixture",
                                root_callables=(shared_root,),
                                constants={},
                                repository_root=ROOT,
                            )
                        )
                        distinct_fingerprint = (
                            CARRY.code_aware_contract_fingerprint(
                                contract_name="fixture",
                                root_callables=(distinct_root,),
                                constants={},
                                repository_root=ROOT,
                            )
                        )
                        self.assertNotEqual(
                            shared_fingerprint, distinct_fingerprint
                        )

    def test_identity_primitive_aliases_defaults_and_modules_fail_closed(
        self,
    ) -> None:
        sources = {
            "global_id_alias": '''\
observe_id = id

def root(value):
    return observe_id(value)
''',
            "default_id_alias": '''\
def root(value, identity=id):
    return identity(value)
''',
            "builtins_id": '''\
import builtins

def root(value):
    return builtins.id(value)
''',
            "literal_getattr_id": '''\
import builtins

def root(value):
    return getattr(builtins, "id")(value)
''',
            "local_builtins_id": '''\
import builtins

def root(value):
    observe_id = builtins.id
    return observe_id(value)
''',
            "dynamic_getattr_id": '''\
import builtins

def root(value):
    member = "id"
    return getattr(builtins, member)(value)
''',
            "operator_alias": '''\
from operator import is_ as same

def root(left, right):
    return same(left, right)
''',
            "operator_is_not_alias": '''\
from operator import is_not as different

def root(left, right):
    return different(left, right)
''',
            "local_operator_alias": '''\
import operator

def root(left, right):
    same = operator.is_
    return same(left, right)
''',
            "partial_id": '''\
from functools import partial

observe_id = partial(id)

def root(value):
    return observe_id(value)
''',
            "partial_operator": '''\
from functools import partial
from operator import is_ as same

compare = partial(same)

def root(left, right):
    return compare(left, right)
''',
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for label, source in sources.items():
                module = _load_contract_fixture(
                    path, f"contract_identity_primitive_{label}", source
                )
                with self.subTest(identity_primitive=label), self.assertRaisesRegex(
                    CARRY.ProfessionalCarryForwardError,
                    "process-local identity primitive|process-local id|identity-sensitive module",
                ):
                    CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(module.root,),
                        constants={},
                        repository_root=ROOT,
                    )

    def test_callable_local_imports_fail_closed(self) -> None:
        sources = {
            "repository_module": '''\
def root():
    import temp_repo_helper as helper
    return helper.validate()
''',
            "repository_member": '''\
def root():
    from temp_repo_helper import validate
    return validate()
''',
            "builtins_module": '''\
def root(value):
    import builtins as local_builtins
    return local_builtins.id(value)
''',
            "builtins_member": '''\
def root(value):
    from builtins import id as identity
    return identity(value)
''',
            "operator_module": '''\
def root(left, right):
    import operator as local_operator
    return local_operator.is_(left, right)
''',
            "operator_member": '''\
def root(left, right):
    from operator import is_ as same
    return same(left, right)
''',
            "dynamic_getattr": '''\
def root(value, member="id"):
    import builtins as local_builtins
    return getattr(local_builtins, member)(value)
''',
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for label, source in sources.items():
                module = _load_contract_fixture(
                    path, f"contract_local_import_{label}", source
                )
                with self.subTest(local_import=label), self.assertRaisesRegex(
                    CARRY.ProfessionalCarryForwardError,
                    "callable-local imports are unsupported",
                ):
                    CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(module.root,),
                        constants={},
                        repository_root=ROOT,
                    )

    def test_dynamic_code_and_import_primitive_aliases_fail_closed(self) -> None:
        sources = {
            "global_eval_alias": '''\
runner = eval

def root(source):
    return runner(source)
''',
            "default_exec_alias": '''\
def root(source, runner=exec):
    return runner(source)
''',
            "builtins_compile": '''\
import builtins

def root(source):
    return builtins.compile(source, "<contract>", "exec")
''',
            "local_builtins_eval": '''\
import builtins

def root(source):
    runner = builtins.eval
    return runner(source)
''',
            "literal_getattr_import": '''\
import builtins

def root(name):
    return getattr(builtins, "__import__")(name)
''',
            "global_import_alias": '''\
load_module = __import__

def root(name):
    return load_module(name)
''',
            "partial_compile": '''\
from functools import partial

compile_source = partial(compile)

def root(source):
    return compile_source(source, "<contract>", "exec")
''',
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for label, source in sources.items():
                module = _load_contract_fixture(
                    path, f"contract_dynamic_primitive_{label}", source
                )
                with self.subTest(dynamic_primitive=label), self.assertRaisesRegex(
                    CARRY.ProfessionalCarryForwardError,
                    "dynamic code or import primitive|identity-sensitive module",
                ):
                    CARRY.code_aware_contract_fingerprint(
                        contract_name="fixture",
                        root_callables=(module.root,),
                        constants={},
                        repository_root=ROOT,
                    )

    def test_scalar_identity_observation_fails_closed(self) -> None:
        comparison_source = '''\
left = None
right = None

def root():
    return left is right
'''
        id_source = '''\
value = None

def root():
    return id(value)
'''
        scalar_pairs = (
            (b"contract-token", bytes(bytearray(b"contract-token"))),
            (
                "contract-identity-token",
                "".join(("contract-identity-", "token")),
            ),
            (10**40 + 123, int(str(10**40 + 123))),
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_scalar_identity", comparison_source
            )
            for shared_value, distinct_value in scalar_pairs:
                self.assertEqual(shared_value, distinct_value)
                self.assertIsNot(shared_value, distinct_value)
                for label, left, right in (
                    ("shared", shared_value, shared_value),
                    ("distinct", shared_value, distinct_value),
                ):
                    with self.subTest(
                        scalar_type=type(shared_value).__name__, topology=label
                    ):
                        module.left = left
                        module.right = right
                        with self.assertRaisesRegex(
                            CARRY.ProfessionalCarryForwardError,
                            "identity comparison observes scalar contract state",
                        ):
                            CARRY.code_aware_contract_fingerprint(
                                contract_name="fixture",
                                root_callables=(module.root,),
                                constants={},
                                repository_root=ROOT,
                            )

            id_module = _load_contract_fixture(
                path, "contract_process_id", id_source
            )
            id_module.value = []
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                r"process-local id\(\) observes contract state",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(id_module.root,),
                    constants={},
                    repository_root=ROOT,
                )

    def test_cross_function_scalar_identity_observation_fails_closed(
        self,
    ) -> None:
        comparison_source = '''\
left = None
right = None

def same(first, second):
    return first is second

def root():
    return same(left, right)
'''
        id_source = '''\
value = None

def observe(candidate):
    return id(candidate)

def root():
    return observe(value)
'''
        scalar_pairs = (
            (b"contract-token", bytes(bytearray(b"contract-token"))),
            (
                "contract-identity-token",
                "".join(("contract-identity-", "token")),
            ),
            (10**40 + 123, int(str(10**40 + 123))),
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            module = _load_contract_fixture(
                path, "contract_cross_function_identity", comparison_source
            )
            for shared_value, distinct_value in scalar_pairs:
                for label, left, right in (
                    ("shared", shared_value, shared_value),
                    ("distinct", shared_value, distinct_value),
                ):
                    module.left = left
                    module.right = right
                    with self.subTest(
                        scalar_type=type(shared_value).__name__, topology=label
                    ), self.assertRaisesRegex(
                        CARRY.ProfessionalCarryForwardError,
                        "unsupported non-singleton identity comparison",
                    ):
                        CARRY.code_aware_contract_fingerprint(
                            contract_name="fixture",
                            root_callables=(module.root,),
                            constants={},
                            repository_root=ROOT,
                        )

            id_module = _load_contract_fixture(
                path, "contract_cross_function_process_id", id_source
            )
            id_module.value = []
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                r"process-local id\(\) observes contract state",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(id_module.root,),
                    constants={},
                    repository_root=ROOT,
                )

    def test_unsupported_value_subclasses_and_explicit_values_fail_closed(
        self,
    ) -> None:
        class IntegerChoice(IntEnum):
            ONE = 1

        class CustomList(list):
            pass

        Pair = namedtuple("Pair", ("left", "right"))
        strict_values = (
            IntegerChoice.ONE,
            OrderedDict((("value", 1),)),
            defaultdict(int, {"value": 1}),
            CustomList((1, 2)),
            Pair(1, 2),
        )
        for value in strict_values:
            with self.subTest(strict_type=type(value).__qualname__):
                with self.assertRaisesRegex(
                    CARRY.ProfessionalCarryForwardError,
                    "cannot be represented safely",
                ):
                    CARRY._strict_contract_value(
                        value, repository_root=ROOT
                    )

        explicit_values = (Decimal("1"), range(1), bytearray(b"a"))
        for value in explicit_values:
            with self.subTest(explicit_type=type(value).__qualname__):
                with self.assertRaisesRegex(
                    CARRY.ProfessionalCarryForwardError,
                    "explicit contract value cannot be represented safely",
                ):
                    CARRY._contract_value(value, repository_root=ROOT)

        self.assertNotEqual(
            CARRY.canonical_json_bytes(
                CARRY._strict_contract_value(True, repository_root=ROOT)
            ),
            CARRY.canonical_json_bytes(
                CARRY._strict_contract_value(1, repository_root=ROOT)
            ),
        )
        self.assertNotEqual(
            CARRY.canonical_json_bytes(
                CARRY._contract_value(1, repository_root=ROOT)
            ),
            CARRY.canonical_json_bytes(
                CARRY._contract_value(1.0, repository_root=ROOT)
            ),
        )

    def test_custom_wrapped_callable_state_fails_closed(self) -> None:
        source = '''\
import functools

def base():
    return 1

def decorate(token):
    def wrapper():
        return token + base()
    return functools.wraps(base)(wrapper)

root = decorate(1)
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for token in (1, 2):
                with self.subTest(token=token):
                    module = _load_contract_fixture(
                        path,
                        f"contract_wrapper_{token}",
                        source.replace("decorate(1)", f"decorate({token})"),
                    )
                    with self.assertRaisesRegex(
                        CARRY.ProfessionalCarryForwardError,
                        "wrapper has unsupported runtime state",
                    ):
                        CARRY.code_aware_contract_fingerprint(
                            contract_name="fixture",
                            root_callables=(module.root,),
                            constants={},
                            repository_root=ROOT,
                        )

    def test_direct_class_body_free_state_fails_closed(self) -> None:
        source = '''\
def make_root(value):
    class Root:
        observed = value
    return Root

root = make_root(1)
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            for value in (1, 2):
                with self.subTest(value=value):
                    module = _load_contract_fixture(
                        path,
                        f"contract_class_free_{value}",
                        source.replace("make_root(1)", f"make_root({value})"),
                    )
                    with self.assertRaisesRegex(
                        CARRY.ProfessionalCarryForwardError,
                        "class body captures unsupported runtime state",
                    ):
                        CARRY.code_aware_contract_fingerprint(
                            contract_name="fixture",
                            root_callables=(module.root,),
                            constants={},
                            repository_root=ROOT,
                        )

    def test_repository_module_attribute_chain_binds_only_selected_member(self) -> None:
        helper_source = '''\
def validate(value):
    return value + 1

def unrelated():
    return "unused-left"
'''
        root_source = '''\
import contract_attr_helper as helper

def root(value):
    return helper.validate(value)
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            directory_path = Path(directory)
            helper_path = directory_path / "contract_attr_helper.py"
            root_path = directory_path / "contract_attr_root.py"

            _load_contract_fixture(
                helper_path, "contract_attr_helper", helper_source
            )
            baseline_module = _load_contract_fixture(
                root_path, "contract_attr_root_baseline", root_source
            )
            baseline = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(baseline_module.root,),
                constants={},
                repository_root=ROOT,
            )

            _load_contract_fixture(
                helper_path,
                "contract_attr_helper",
                helper_source.replace('"unused-left"', '"unused-right"'),
            )
            unrelated_module = _load_contract_fixture(
                root_path, "contract_attr_root_unrelated", root_source
            )
            unrelated = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(unrelated_module.root,),
                constants={},
                repository_root=ROOT,
            )

            _load_contract_fixture(
                helper_path,
                "contract_attr_helper",
                helper_source.replace("value + 1", "value - 1"),
            )
            relevant_module = _load_contract_fixture(
                root_path, "contract_attr_root_relevant", root_source
            )
            relevant = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(relevant_module.root,),
                constants={},
                repository_root=ROOT,
            )

        self.assertEqual(baseline, unrelated)
        self.assertNotEqual(baseline, relevant)

    def test_repository_module_literal_getattr_is_bound_and_other_use_fails(
        self,
    ) -> None:
        helper_source = '''\
def validate(value):
    return value + 1

def unrelated():
    return "unused-left"
'''
        literal_source = '''\
import contract_dynamic_helper as helper

def root(value):
    return getattr(helper, "validate")(value)
'''
        dynamic_source = literal_source.replace('"validate"', "value")
        bare_source = '''\
import contract_dynamic_helper as helper

def consume(value):
    return value

def root():
    return consume(helper)
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            directory_path = Path(directory)
            helper_path = directory_path / "contract_dynamic_helper.py"
            root_path = directory_path / "contract_dynamic_root.py"

            _load_contract_fixture(
                helper_path, "contract_dynamic_helper", helper_source
            )
            baseline_module = _load_contract_fixture(
                root_path, "contract_dynamic_root_baseline", literal_source
            )
            baseline = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(baseline_module.root,),
                constants={},
                repository_root=ROOT,
            )

            _load_contract_fixture(
                helper_path,
                "contract_dynamic_helper",
                helper_source.replace('"unused-left"', '"unused-right"'),
            )
            unrelated_module = _load_contract_fixture(
                root_path, "contract_dynamic_root_unrelated", literal_source
            )
            unrelated = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(unrelated_module.root,),
                constants={},
                repository_root=ROOT,
            )

            _load_contract_fixture(
                helper_path,
                "contract_dynamic_helper",
                helper_source.replace("value + 1", "value - 1"),
            )
            relevant_module = _load_contract_fixture(
                root_path, "contract_dynamic_root_relevant", literal_source
            )
            relevant = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(relevant_module.root,),
                constants={},
                repository_root=ROOT,
            )
            self.assertEqual(baseline, unrelated)
            self.assertNotEqual(baseline, relevant)

            for label, source, error in (
                (
                    "dynamic",
                    dynamic_source,
                    "getattr requires a constant public member",
                ),
                ("bare", bare_source, "unsupported dynamic or bare use"),
            ):
                with self.subTest(module_use=label):
                    rejected_module = _load_contract_fixture(
                        root_path, f"contract_dynamic_root_{label}", source
                    )
                    with self.assertRaisesRegex(
                        CARRY.ProfessionalCarryForwardError, error
                    ):
                        CARRY.code_aware_contract_fingerprint(
                            contract_name="fixture",
                            root_callables=(rejected_module.root,),
                            constants={},
                            repository_root=ROOT,
                        )

    def test_production_snapshot_module_attribute_is_in_contract_graph(self) -> None:
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
        baseline = PANEL._professional_evidence_review_contract_fingerprint()

        def changed_snapshot(*, bindings, review_contract_fingerprint):
            return {
                "bindings": bindings,
                "review_contract_fingerprint": review_contract_fingerprint,
                "changed": True,
            }

        with mock.patch.object(
            PANEL.professional_carry,
            "professional_carry_snapshot",
            changed_snapshot,
        ):
            PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
            changed = PANEL._professional_evidence_review_contract_fingerprint()
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()
        self.assertNotEqual(baseline, changed)

    def test_multiline_string_indentation_is_runtime_behavior(self) -> None:
        baseline_source = '''\
def root():
    return """first
    nested
last"""
'''
        changed_source = baseline_source.replace("    nested", "        nested")
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            baseline_module = _load_contract_fixture(
                path, "contract_multiline_baseline", baseline_source
            )
            baseline = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(baseline_module.root,),
                constants={},
                repository_root=ROOT,
            )
            changed_module = _load_contract_fixture(
                path, "contract_multiline_changed", changed_source
            )
            changed = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(changed_module.root,),
                constants={},
                repository_root=ROOT,
            )
        self.assertNotEqual(baseline, changed)

    def test_duplicate_repository_identity_fails_closed(self) -> None:
        source = '''\
def root():
    return 1
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            left = _load_contract_fixture(path, "contract_identity_left", source)
            right = _load_contract_fixture(path, "contract_identity_right", source)
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "duplicate repository identity",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(left.root, right.root),
                    constants={},
                    repository_root=ROOT,
                )

    def test_opaque_repository_identity_collision_fails_closed(self) -> None:
        helper_source = '''\
def helper():
    return 1
'''
        root_source = '''\
def make_root(helper):
    def root():
        return helper()
    return root
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            directory_path = Path(directory)
            helper_path = directory_path / "contract_helper.py"
            root_path = directory_path / "contract_root.py"
            left = _load_contract_fixture(
                helper_path, "opaque_identity_left", helper_source
            )
            right = _load_contract_fixture(
                helper_path, "opaque_identity_right", helper_source
            )
            root_module = _load_contract_fixture(
                root_path, "opaque_identity_root", root_source
            )
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "repository callable identity collision",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(root_module.make_root(right.helper),),
                    constants={},
                    repository_root=ROOT,
                    opaque_repository_callables=(left.helper,),
                )

    def test_dependency_discovery_respects_lexical_scope_and_attributes(self) -> None:
        first = '''\
SHADOWED = "first"

def helper():
    return "first"

def root(SHADOWED, target):
    return SHADOWED + target.helper()
'''
        second = first.replace('SHADOWED = "first"', 'SHADOWED = "second"').replace(
            'return "first"', 'return "second"'
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            left = _load_contract_fixture(path, "contract_scope_left", first)
            left_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(left.root,),
                constants={},
                repository_root=ROOT,
            )
            right = _load_contract_fixture(path, "contract_scope_right", second)
            right_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(right.root,),
                constants={},
                repository_root=ROOT,
            )
        self.assertEqual(left_fingerprint, right_fingerprint)

    def test_repository_class_behavior_is_reachable(self) -> None:
        first = '''\
class Helper:
    def value(self):
        return 1

def root():
    return Helper().value()
'''
        second = first.replace("return 1", "return 2")
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            left = _load_contract_fixture(path, "contract_class_left", first)
            left_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(left.root,),
                constants={},
                repository_root=ROOT,
            )
            right = _load_contract_fixture(path, "contract_class_right", second)
            right_fingerprint = CARRY.code_aware_contract_fingerprint(
                contract_name="fixture",
                root_callables=(right.root,),
                constants={},
                repository_root=ROOT,
            )
        self.assertNotEqual(left_fingerprint, right_fingerprint)

    def test_external_callable_contract_excludes_stdlib_source_and_path(self) -> None:
        contract = CARRY._external_callable_contract(
            Path, repository_root=ROOT
        )
        self.assertEqual("pathlib:Path", contract["identity"])
        self.assertEqual("class", contract["kind"])
        self.assertEqual({"identity", "kind"}, set(contract))

    def test_repository_callable_without_matching_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "contract_fixture.py"
            path.write_text("VALUE = 1\n", encoding="utf-8")
            namespace = {"__name__": "contract_missing_source"}
            exec(
                compile("def root():\n    return 1\n", path.as_posix(), "exec"),
                namespace,
            )
            linecache.clearcache()
            with self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                "source is unavailable|does not uniquely match",
            ):
                CARRY.code_aware_contract_fingerprint(
                    contract_name="fixture",
                    root_callables=(namespace["root"],),
                    constants={},
                    repository_root=ROOT,
                )

    def test_code_object_contract_value_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "code objects"
        ):
            CARRY._contract_value(
                self.test_code_object_contract_value_fails_closed.__code__,
                repository_root=ROOT,
            )


class ProfessionalPacketCompatibilityTests(unittest.TestCase):
    def test_schema1_inventory_count_is_a_strict_closed_integer_set(self) -> None:
        historical_path = (
            ROOT
            / "evals/expert-panel/professional-completeness-panel-2026-07-16-r5/packet.json"
        )
        historical = json.loads(historical_path.read_text(encoding="utf-8"))
        current = copy.deepcopy(_legacy_schema1_packet())
        PANEL._validate_professional_completeness_packet_v1(historical)
        PANEL._validate_professional_completeness_packet_v1(current)
        self.assertEqual(
            {"professional": 22, "foundation": 133, "domain": 7},
            PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS,
        )
        self.assertEqual(
            {"professional": 26, "foundation": 150, "domain": 13},
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
            (current, 188),
            (current, 190),
            (historical, 162.0),
            (current, 189.0),
            (current, True),
            (current, False),
            (current, "189"),
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
        self.assertEqual(189, len(bindings))
        self.assertEqual(before, after)
        self.assertEqual(
            "d024412e5f5ece5dd5c21abdac8269564e81fca91b4e1bfab6fec860ccfeaa9c",
            hashlib.sha256(after).hexdigest(),
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

    def test_historical_cap50_adapter_is_exact_and_hash_preserving(self) -> None:
        decision_path = (
            ROOT
            / "evals/expert-panel/"
            / "professional-completeness-panel-2026-07-24-r11"
            / "panel/decision.json"
        )
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        packet = json.loads(
            (ROOT / decision["packet"]["path"]).read_text(encoding="utf-8")
        )
        adapted = PANEL._professional_v3_historical_cap50_packet(
            decision,
            decision["packet"],
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
            packet_ref = copy.deepcopy(decision["packet"])
            packet_value = copy.deepcopy(packet)
            mutate(record_value, packet_ref, packet_value)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._professional_v3_historical_cap50_packet(
                    record_value,
                    packet_ref,
                    packet_value,
                )
        with mock.patch.object(
            PANEL,
            "PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET",
            53,
        ), self.assertRaises(PANEL.PanelReviewError):
            PANEL._professional_v3_historical_cap50_packet(
                decision,
                decision["packet"],
                packet,
            )

    def test_historical_r14_v1_adapter_is_exact_and_hash_preserving(self) -> None:
        decision_path = (
            ROOT
            / "evals/expert-panel/"
            / PANEL.PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
            / "panel/decision.json"
        )
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        packet = json.loads(
            (ROOT / decision["packet"]["path"]).read_text(encoding="utf-8")
        )
        adapted = PANEL._professional_v3_historical_v1_packet(
            decision,
            decision["packet"],
            packet,
        )
        self.assertEqual(_sha(packet), _sha(adapted))
        self.assertEqual(
            PANEL._professional_v3_panel_contract(target_count=189),
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
            packet_ref = copy.deepcopy(decision["packet"])
            packet_value = copy.deepcopy(packet)
            mutate(record_value, packet_ref, packet_value)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._professional_v3_historical_v1_packet(
                    record_value,
                    packet_ref,
                    packet_value,
                )

    def test_historical_r14_v1_decision_remains_auditable(self) -> None:
        decision_path = (
            ROOT
            / "evals/expert-panel/"
            / PANEL.PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
            / "panel/decision.json"
        )
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        self.assertEqual(
            decision,
            PANEL._validate_professional_completeness_decision_record(
                decision,
                record_path=decision_path,
                validation_root=ROOT,
                validation_mode=PANEL.VALIDATION_MODE_HISTORICAL,
            ),
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
            "e184b31a1c060d48a2247c934b304ef260e38ef3d1c0c606aa6342915f02881e",
            hashlib.sha256(before).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
