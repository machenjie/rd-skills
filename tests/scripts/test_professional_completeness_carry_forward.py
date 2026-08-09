from __future__ import annotations

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

    def test_review_contract_uses_versioned_explicit_source_manifest(self) -> None:
        manifest = PANEL._professional_evidence_review_contract_manifest()
        self.assertEqual(
            "professional-evidence-review-and-carry-v2",
            manifest["contract_version"],
        )
        self.assertRegex(manifest["aggregate_source_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            [
                "scripts/audit-skill-content.py",
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
        self.assertEqual(
            manifest["aggregate_source_digest"],
            PANEL._professional_evidence_review_contract_fingerprint(),
        )

    def test_contract_version_and_explicit_source_bytes_change_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            first = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v1",
                source_paths=("source.py",),
                repository_root=root,
            )
            version_changed = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v2",
                source_paths=("source.py",),
                repository_root=root,
            )
            source.write_text("VALUE = 2\n", encoding="utf-8")
            source_changed = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v1",
                source_paths=("source.py",),
                repository_root=root,
            )
        self.assertNotEqual(
            first["aggregate_source_digest"],
            version_changed["aggregate_source_digest"],
        )
        self.assertNotEqual(
            first["aggregate_source_digest"],
            source_changed["aggregate_source_digest"],
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
