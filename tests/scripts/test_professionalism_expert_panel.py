from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_completeness_test_support as professional_support
from . import readability_review_test_support as readability_support


ROOT = Path(__file__).resolve().parents[2]




PANEL = source_support.PANEL
REGRESSION = source_support.REGRESSION


def _formal_release_manifest_fixture() -> dict:
    head_commit = "1" * 40
    observations = [
        {
            "axis": axis,
            "path": path,
            "external_sha256": format(index + 1, "x") * 64,
            "size_bytes": 100 + index,
            "review_id": f"fixture-{axis}",
            "verdict": verdict,
            "head_byte_equal": True,
            "clean": True,
        }
        for index, (axis, path, verdict) in enumerate(
            REGRESSION.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
        )
    ]
    return REGRESSION._derive_expert_panel_release_manifest(
        formal=True,
        storage_statuses={
            axis: "current"
            for axis, _path, _verdict in (
                REGRESSION.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
            )
        },
        current_head_commit=head_commit,
        manifest_head_commit=head_commit,
        artifact_observations=observations,
    )


def _full_fresh_review_cost() -> dict:
    _policy, fingerprint = REGRESSION._professional_review_formal_round_policy()
    return {
        "fresh_vote_count": 567,
        "carried_forward_vote_count": 0,
        "effective_vote_count": 567,
        "fresh_criterion_result_count": 5670,
        "carried_forward_criterion_result_count": 0,
        "effective_criterion_result_count": 5670,
        "canonical_capsule_input_bytes_proxy": 1010,
        "full_rereview_deduplicated_capsule_input_bytes_proxy": 1000,
        "input_ratio_ppm": 1_010_000,
        "required_only_capsule_input_bytes_proxy": 1000,
        "required_only_input_ratio_ppm": 1_000_000,
        "required_only_source_material_input_bytes_proxy": 200,
        "source_material_input_bytes_proxy": 200,
        "full_rereview_source_material_input_bytes_proxy": 200,
        "source_material_coverage_ratio_ppm": 1_000_000,
        "reviewer_added_source_material_input_bytes_proxy": 0,
        "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": 10,
        "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 12_500,
        "reviewer_added_request_count": 3,
        "reviewer_added_unique_relationship_count": 1,
        "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 500_000,
        "formal_round_policy_fingerprint": fingerprint,
        "maximum_origin_depth": 0,
        "plan_lineage_depth": 0,
        "policy_status": "bootstrap-full-review",
        "limitations": list(REGRESSION.PROFESSIONAL_REVIEW_COST_LIMITATIONS),
    }


def _all_carry_review_cost() -> dict:
    cost = _full_fresh_review_cost()
    cost.update(
        {
            "fresh_vote_count": 0,
            "carried_forward_vote_count": 567,
            "fresh_criterion_result_count": 0,
            "carried_forward_criterion_result_count": 5670,
            "canonical_capsule_input_bytes_proxy": 0,
            "input_ratio_ppm": 0,
            "required_only_capsule_input_bytes_proxy": 0,
            "required_only_input_ratio_ppm": 0,
            "required_only_source_material_input_bytes_proxy": 0,
            "source_material_input_bytes_proxy": 0,
            "source_material_coverage_ratio_ppm": 0,
            "reviewer_added_source_material_input_bytes_proxy": 0,
            "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": 0,
            "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 0,
            "reviewer_added_request_count": 0,
            "reviewer_added_unique_relationship_count": 0,
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 0,
            "maximum_origin_depth": 1,
            "plan_lineage_depth": 1,
            "policy_status": "all-carry-zero-input",
        }
    )
    return cost


def _recompose_review_cost(
    cost: dict,
    *,
    denominator: int,
    full_source: int,
    required_source: int,
    actual_source: int,
    required_metadata: int,
    metadata_overhead: int,
) -> dict:
    required = required_source + required_metadata
    actual = actual_source + required_metadata + metadata_overhead
    cost.update(
        {
            "canonical_capsule_input_bytes_proxy": actual,
            "full_rereview_deduplicated_capsule_input_bytes_proxy": denominator,
            "input_ratio_ppm": actual * 1_000_000 // denominator,
            "required_only_capsule_input_bytes_proxy": required,
            "required_only_input_ratio_ppm": required * 1_000_000 // denominator,
            "required_only_source_material_input_bytes_proxy": required_source,
            "source_material_input_bytes_proxy": actual_source,
            "full_rereview_source_material_input_bytes_proxy": full_source,
            "source_material_coverage_ratio_ppm": (
                actual_source * 1_000_000 // full_source
            ),
            "reviewer_added_source_material_input_bytes_proxy": (
                actual_source - required_source
            ),
            "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": (
                metadata_overhead
            ),
            "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": (
                metadata_overhead * 1_000_000 // required_metadata
                if required_metadata
                else 0
            ),
        }
    )
    return cost


def _incremental_review_cost() -> dict:
    cost = _full_fresh_review_cost()
    cost.update(
        {
            "fresh_vote_count": 3,
            "carried_forward_vote_count": 564,
            "fresh_criterion_result_count": 30,
            "carried_forward_criterion_result_count": 5640,
            "reviewer_added_request_count": 3,
            "reviewer_added_unique_relationship_count": 1,
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 1_000_000,
            "maximum_origin_depth": 1,
            "plan_lineage_depth": 8,
            "policy_status": "incremental-reduced-input",
        }
    )
    return _recompose_review_cost(
        cost,
        denominator=2_000_400,
        full_source=400,
        required_source=200,
        actual_source=200,
        required_metadata=1_000_000,
        metadata_overhead=50_000,
    )


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _packet() -> dict:
    return {
        "schema_version": 1,
        "kind": PANEL.PACKET_KIND,
        "review_id": "fixture-panel",
        "created_on": "2026-07-16",
        "source_fingerprints": {
            "reference_content": "a" * 64,
            "root_content": "b" * 64,
            "ai_readability": "c" * 64,
        },
        "panel_contract": {
            "decision_method": PANEL.DECISION_METHOD,
            "required_voters": 3,
            "abstentions_allowed": False,
            "minimum_winning_votes": 2,
            "independent_ballots": True,
        },
        "rubric": {
            "accept": "Accept one coherent bounded decision.",
            "tighten": "Tighten separable independent actions.",
            "reason_codes": {
                decision: sorted(values)
                for decision, values in sorted(PANEL.REASON_CODES.items())
            },
        },
        "content_targets": [
            {
                "path": "src/foundation/capabilities/a/SKILL.md",
                "classification": "REVIEW_DENSITY",
                "review_state": "REVIEW_READABILITY",
                "review_reasons": ["classification_review_density"],
            }
        ],
        "readability_targets": [
            {
                "document_id": "src/foundation/capabilities/a/SKILL.md#body",
                "path": "src/foundation/capabilities/a/SKILL.md",
                "surface": "foundation-root",
                "document_part": "body",
                "content_fingerprint": "e" * 64,
                "highest_band": "review-as-complex",
                "findings": [
                    {
                        "line": 1,
                        "band": "review-as-complex",
                        "words": 24,
                        "kind": "sentence-length",
                        "sentence_fingerprint": "d" * 64,
                        "source_line": "One coherent fixture sentence remains reviewable.",
                    }
                ],
            }
        ],
        "limitations": ["Static fixture."],
    }


def _ballot(packet: dict, packet_sha: str, voter: int) -> dict:
    return {
        "schema_version": 1,
        "kind": PANEL.BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": "2026-07-16",
        "packet_sha256": packet_sha,
        "source_fingerprints": packet["source_fingerprints"],
        "voter": {
            "voter_id": f"expert-{voter}",
            "agent_id": f"agent-{voter}",
            "role": f"senior-role-{voter}",
            "expertise": ["professional content review"],
            "independent_review": True,
        },
        "content_votes": [
            {
                "path": packet["content_targets"][0]["path"],
                "classification": "REVIEW_DENSITY",
                "decision": "accepted-current-density",
                "reason_code": "bounded-density-preserves-professional-coverage",
                "rationale": "This bounded density preserves one complete professional decision model.",
            }
        ],
        "readability_votes": [
            {
                "document_id": packet["readability_targets"][0]["document_id"],
                "highest_band": "review-as-complex",
                "decision": "accepted-current-readability",
                "reason_code": "single-indivisible-decision",
                "rationale": "This sentence keeps one coherent decision readable and precise.",
            }
        ],
        "limitations": ["Static fixture vote."],
    }


def _professional_ballot(packet: dict, packet_sha: str, voter: int) -> dict:
    if packet.get("schema_version") == PANEL.PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION:
        return professional_support._professional_ballot(
            packet,
            packet_sha,
            voter=voter,
        )
    votes = []
    for target in packet["professional_targets"]:
        votes.append(
            {
                "skill_id": target["skill_id"],
                "decision": "accepted-current-professional-completeness",
                "reason_code": "all-professional-criteria-satisfied",
                "criteria": {
                    criterion: "satisfied"
                    for criterion in PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA
                },
                "rationale": (
                    "Every required professional completeness criterion is "
                    "satisfied for this package."
                ),
            }
        )
    return {
        "schema_version": 1,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": "2026-07-16",
        "packet_sha256": packet_sha,
        "source_fingerprints": packet["source_fingerprints"],
        "voter": {
            "voter_id": f"professional-expert-{voter}",
            "agent_id": f"professional-agent-{voter}",
            "role": f"senior-professional-role-{voter}",
            "expertise": ["professional completeness review"],
            "independent_review": True,
        },
        "professional_votes": votes,
        "limitations": ["Temporary parser integration fixture."],
    }


def _current_semantic_attestation(
    axes: tuple[str, ...],
    *,
    winner_overrides: dict[str, str] | None = None,
) -> tuple[dict, dict, dict, bytes]:
    producer = REGRESSION.expert_panel
    audit = source_support.live_semantic_audit()
    review_id = "semantic-current-selector-" + ("-".join(axes) or "ordinary")
    packet = producer.prepare_semantic_disposition_packet(
        audit=producer._semantic_audit_for_axis_rereview(audit, list(axes)),
        review_id=review_id,
        created_on="2026-08-11",
    )
    producer.validate_semantic_packet_current(packet, audit)
    authorities = producer._semantic_candidate_authorities(packet)
    reviewers = [
        {
            "voter_id": f"semantic-current-voter-{index}",
            "agent_id": f"semantic-current-agent-{index}",
            "role": f"semantic-current-role-{index}",
            "expertise": ["semantic disposition governance"],
            "independent_review": True,
        }
        for index in range(1, producer.PANEL_SIZE + 1)
    ]
    winner_overrides = winner_overrides or {}
    current_dispositions = {
        f"{axis}:{entry['candidate_id']}": entry["disposition"]
        for axis in PANEL.SEMANTIC_AXES
        for entry in audit[f"{axis}_content"]["semantic_advisories"][
            "disposition_contract"
        ]["entries"]
    }

    def votes_for(target_id: str) -> list[dict]:
        winner = winner_overrides.get(
            target_id,
            current_dispositions[target_id],
        )
        return [
            {
                "voter_id": reviewer["voter_id"],
                "disposition": winner,
                "rationale": (
                    "The current candidate received the independently reviewed "
                    "bounded disposition."
                ),
                "authority_or_condition": (
                    "The current source owner retains authority."
                ),
                "decision_owner": "current-source-owner",
                "mitigation": (
                    "Repeat review when source or detector evidence changes."
                ),
                "review_after": None,
            }
            for reviewer in reviewers
        ]
    value = {
        "schema_version": producer.panel_attestation.ATTESTATION_SCHEMA_VERSION,
        "kind": producer.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND,
        "axis": producer.panel_attestation.SEMANTIC_DISPOSITION_AXIS,
        "review_id": review_id,
        "decided_on": "2026-08-11",
        "source_fingerprints": copy.deepcopy(packet["source_fingerprints"]),
        "review_contract_fingerprint": producer._canonical_json_sha256(
            packet["panel_contract"]
        ),
        "reviewers": reviewers,
        "findings": [
            {
                "target_id": target["target_id"],
                "axis": target["axis"],
                "candidate_binding_fingerprint": authorities[target["target_id"]][
                    "candidate_binding_fingerprint"
                ],
                "votes": votes_for(target["target_id"]),
                "result": {},
            }
            for target in packet["semantic_targets"]
        ],
        "summary": {},
        "verdict": "",
        "rationale": [
            "Every selected current semantic candidate received a complete majority."
        ],
    }
    finalized = producer.panel_attestation.finalize_attestation(
        value,
        expected_path=(
            producer.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
        ),
        expected_semantic_current_bindings=authorities,
    )
    raw = producer.panel_attestation.canonical_attestation_bytes(
        finalized,
        expected_path=(
            producer.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
        ),
        expected_semantic_current_bindings=authorities,
    )
    selector = json.loads(raw)
    return audit, packet, selector, raw


class ProfessionalismExpertPanelTests(unittest.TestCase):
    CURRENT_PATHS = (
        "evals/expert-panel/professional-completeness.json",
        "evals/expert-panel/readability.json",
        "evals/expert-panel/semantic-disposition.json",
    )

    def _git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _storage_repo(
        self,
        root: Path,
        *,
        tracked: dict[str, bytes] | None = None,
        untracked: dict[str, bytes] | None = None,
    ) -> None:
        self._git(root, "init", "-q")
        self._git(root, "config", "user.name", "Storage Contract Test")
        self._git(root, "config", "user.email", "storage@example.invalid")
        (root / ".anchor").write_text("tracked\n", encoding="utf-8")
        for relative, payload in (tracked or {}).items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        self._git(root, "add", ".anchor", *(tracked or {}))
        self._git(root, "commit", "-qm", "fixture")
        for relative, payload in (untracked or {}).items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    def _validate_storage(
        self,
        root: Path,
        *,
        formal: bool,
        currentness_error: Exception | None = None,
        parse_error: Exception | None = None,
    ) -> dict[str, str]:

        def current_validation(
            panel_kind, *, review_id, decided_on, attestation_selector
        ):
            self.assertEqual("storage-fixture", review_id)
            self.assertEqual("2026-08-10", decided_on)
            self.assertEqual(
                {
                    "schema_version": 2,
                    "review_id": "storage-fixture",
                    "decided_on": "2026-08-10",
                },
                attestation_selector,
            )
            path = REGRESSION.expert_panel.panel_attestation.ATTESTATION_PATHS[
                panel_kind
            ]
            def validate_current(_value):
                if currentness_error is not None:
                    raise currentness_error

            return path, {}, validate_current

        def parse_attestation(_raw, *, expected_path, **_kwargs):
            if parse_error is not None:
                raise parse_error
            if currentness_error is not None:
                raise currentness_error
            return {"path": expected_path}

        with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
            REGRESSION.expert_panel.panel_attestation,
            "parse_attestation_storage_selector_bytes",
            return_value={
                "schema_version": 2,
                "review_id": "storage-fixture",
                "decided_on": "2026-08-10",
            },
        ), mock.patch.object(
            REGRESSION.expert_panel,
            "_current_attestation_validation",
            side_effect=current_validation,
        ), mock.patch.object(
            REGRESSION.expert_panel.panel_attestation,
            "parse_attestation_bytes",
            side_effect=parse_attestation,
        ):
            return REGRESSION._validate_current_expert_panel_storage(
                formal=formal
            )

    def test_current_attestation_storage_authoring_subset_and_formal_exact_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root)
            self.assertEqual(
                {
                    panel_kind: "missing"
                    for panel_kind in REGRESSION.expert_panel.panel_attestation.ATTESTATION_PATHS
                },
                self._validate_storage(root, formal=False),
            )
            with self.assertRaisesRegex(ValueError, "formal.*missing"):
                self._validate_storage(root, formal=True)

        for missing in self.CURRENT_PATHS:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                tracked = {
                    path: b"{}\n" for path in self.CURRENT_PATHS if path != missing
                }
                self._storage_repo(root, tracked=tracked)
                expected = {
                    panel_kind: (
                        "missing"
                        if path == missing
                        else "current"
                    )
                    for panel_kind, path in (
                        REGRESSION.expert_panel.panel_attestation.ATTESTATION_PATHS.items()
                    )
                }
                self.assertEqual(expected, self._validate_storage(root, formal=False))
                with self.assertRaisesRegex(ValueError, "formal.*missing"):
                    self._validate_storage(root, formal=True)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = {path: b"{}\n" for path in self.CURRENT_PATHS}
            self._storage_repo(root, tracked=tracked)
            self.assertEqual(
                {
                    panel_kind: "current"
                    for panel_kind in REGRESSION.expert_panel.panel_attestation.ATTESTATION_PATHS
                },
                self._validate_storage(root, formal=True),
            )

    def test_professional_storage_validates_current_authority_once_per_parse(
        self,
    ) -> None:
        panel_kind = (
            REGRESSION.expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND
        )
        current = (
            REGRESSION.expert_panel.panel_attestation.ATTESTATION_PATHS[
                panel_kind
            ]
        )
        authority = {"fixture-skill": {"fixture": "current-authority"}}

        def current_validation(
            actual_panel_kind,
            *,
            review_id,
            decided_on,
            attestation_selector,
        ):
            self.assertEqual(panel_kind, actual_panel_kind)
            self.assertEqual("storage-fixture", review_id)
            self.assertEqual("2026-08-10", decided_on)
            self.assertEqual(2, attestation_selector["schema_version"])

            def duplicate_post_parse(value):
                REGRESSION.expert_panel.panel_attestation.validate_attestation(
                    value,
                    expected_professional_current_bindings=authority,
                )

            return current, {
                "expected_professional_current_bindings": authority,
            }, duplicate_post_parse

        def parse_attestation(_raw, *, expected_path, **validation):
            self.assertEqual(current, expected_path)
            return REGRESSION.expert_panel.panel_attestation.validate_attestation(
                {"parsed": True},
                **validation,
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            with mock.patch.object(
                REGRESSION, "ROOT", root
            ), mock.patch.object(
                REGRESSION.expert_panel.panel_attestation,
                "parse_attestation_storage_selector_bytes",
                return_value={
                    "schema_version": 2,
                    "review_id": "storage-fixture",
                    "decided_on": "2026-08-10",
                },
            ) as selector, mock.patch.object(
                REGRESSION.expert_panel,
                "_current_attestation_validation",
                side_effect=current_validation,
            ), mock.patch.object(
                REGRESSION.expert_panel.panel_attestation,
                "parse_attestation_bytes",
                side_effect=parse_attestation,
            ) as parse, mock.patch.object(
                REGRESSION.expert_panel.panel_attestation,
                "validate_attestation",
                return_value={"parsed": True},
            ) as validate:
                statuses = REGRESSION._validate_current_expert_panel_storage(
                    formal=False
                )

        self.assertEqual("current", statuses[panel_kind])
        self.assertEqual(1, selector.call_count)
        self.assertEqual(1, parse.call_count)
        self.assertEqual(parse.call_count, validate.call_count)

    def test_current_attestation_storage_softens_only_currentness_drift(self) -> None:
        current = self.CURRENT_PATHS[1]
        panel_kind = REGRESSION.expert_panel.panel_attestation.attestation_axis_for_path(
            current
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            statuses = self._validate_storage(
                root,
                formal=False,
                currentness_error=REGRESSION.expert_panel.PanelReviewError(
                    "readability attestation exact current coverage or contract is stale"
                ),
            )
            self.assertEqual("stale", statuses[panel_kind])
            with self.assertRaisesRegex(ValueError, "formal.*stale"):
                self._validate_storage(
                    root,
                    formal=True,
                    currentness_error=REGRESSION.expert_panel.PanelReviewError(
                        "readability attestation exact current coverage or contract is stale"
                    ),
                )

        drift = (
            REGRESSION.expert_panel.panel_attestation.AttestationCurrentnessError(
                "Readability target manifest binding is stale"
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            statuses = self._validate_storage(
                root,
                formal=False,
                parse_error=drift,
            )
            self.assertEqual("stale", statuses[panel_kind])
            with self.assertRaisesRegex(ValueError, "formal.*stale"):
                self._validate_storage(
                    root,
                    formal=True,
                    parse_error=drift,
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            (root / current).write_bytes(b'{"changed":true}\n')
            with self.assertRaises(
                REGRESSION.expert_panel.panel_attestation.AttestationCurrentnessError
            ):
                self._validate_storage(
                    root,
                    formal=False,
                    parse_error=drift,
                )

    def test_semantic_target_set_drift_is_stale_only_for_trusted_fixed_bytes(
        self,
    ) -> None:
        current = self.CURRENT_PATHS[2]
        panel_kind = (
            REGRESSION.expert_panel.panel_attestation.attestation_axis_for_path(
                current
            )
        )
        messages = (
            "semantic fixed missing target lacks a rewrite majority",
            "semantic fixed attestation omits a current candidate",
        )
        for message in messages:
            drift = REGRESSION.expert_panel.PanelReviewError(message)
            with self.subTest(message=message, state="clean"), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._storage_repo(root, tracked={current: b"{}\n"})
                statuses = self._validate_storage(
                    root,
                    formal=False,
                    currentness_error=drift,
                )
                self.assertEqual("stale", statuses[panel_kind])
                with self.assertRaisesRegex(ValueError, "formal.*stale"):
                    self._validate_storage(
                        root,
                        formal=True,
                        currentness_error=drift,
                    )

            with self.subTest(message=message, state="dirty"), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._storage_repo(root, tracked={current: b"{}\n"})
                (root / current).write_bytes(b'{"changed":true}\n')
                with self.assertRaisesRegex(
                    REGRESSION.expert_panel.PanelReviewError,
                    message,
                ):
                    self._validate_storage(
                        root,
                        formal=False,
                        currentness_error=drift,
                    )

        generic_drifts = (
            REGRESSION.expert_panel.panel_attestation.AttestationError(
                "attestation review contract fingerprint is stale"
            ),
            REGRESSION.expert_panel.panel_attestation.AttestationError(
                "attestation source fingerprints are stale"
            ),
        )
        for generic_drift in generic_drifts:
            with self.subTest(
                drift=str(generic_drift)
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._storage_repo(root, tracked={current: b"{}\n"})
                (root / current).write_bytes(b'{"changed":true}\n')
                with self.assertRaises(type(generic_drift)):
                    self._validate_storage(
                        root,
                        formal=False,
                        parse_error=generic_drift,
                    )

        semantic_binding_drift = (
            REGRESSION.expert_panel.panel_attestation.AttestationError(
                "Semantic candidate binding is stale"
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            self.assertEqual(
                "stale",
                self._validate_storage(
                    root,
                    formal=False,
                    parse_error=semantic_binding_drift,
                )[panel_kind],
            )
            with self.assertRaisesRegex(ValueError, "formal.*stale"):
                self._validate_storage(
                    root,
                    formal=True,
                    parse_error=semantic_binding_drift,
                )
            (root / current).write_bytes(b'{"changed":true}\n')
            with self.assertRaises(
                REGRESSION.expert_panel.panel_attestation.AttestationError
            ):
                self._validate_storage(
                    root,
                    formal=False,
                    parse_error=semantic_binding_drift,
                )

        panel_drift = REGRESSION.expert_panel.PanelReviewError(
            "readability attestation exact current coverage or contract is stale"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            (root / current).write_bytes(b'{"changed":true}\n')
            with self.assertRaises(REGRESSION.expert_panel.PanelReviewError):
                self._validate_storage(
                    root,
                    formal=False,
                    currentness_error=panel_drift,
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            (root / current).write_bytes(b'{"changed":true}\n')
            self.assertEqual(
                "pending",
                self._validate_storage(root, formal=False)[panel_kind],
            )
            with self.assertRaisesRegex(ValueError, "formal.*pending"):
                self._validate_storage(root, formal=True)

    def test_current_attestation_storage_keeps_malformed_and_tampered_hard(self) -> None:
        current = self.CURRENT_PATHS[1]
        for formal in (False, True):
            with self.subTest(kind="malformed", formal=formal), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._storage_repo(root, tracked={current: b"{\n"})
                with mock.patch.object(REGRESSION, "ROOT", root), self.assertRaisesRegex(
                    ValueError,
                    "invalid JSON",
                ):
                    REGRESSION._validate_current_expert_panel_storage(
                        formal=formal
                    )
            with self.subTest(kind="tampered", formal=formal), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._storage_repo(root, tracked={current: b"{}\n"})
                with self.assertRaisesRegex(
                    ValueError,
                    "derived results or summary",
                ):
                    self._validate_storage(
                        root,
                        formal=formal,
                        parse_error=(
                            REGRESSION.expert_panel.panel_attestation.AttestationError(
                                "attestation derived results or summary are stale"
                            )
                        ),
                    )

    def test_semantic_current_validation_selects_ordinary_root_and_both_authority(
        self,
    ) -> None:
        expected_counts = {
            ("root", "reference"): 208,
        }
        for axes, expected_count in expected_counts.items():
            with self.subTest(axes=axes):
                audit, packet, selector, raw = _current_semantic_attestation(axes)
                with mock.patch.object(
                    REGRESSION.expert_panel, "_json_object", return_value=audit
                ):
                    relative, validation, validate_current = (
                        REGRESSION.expert_panel._current_attestation_validation(
                            REGRESSION.expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND,
                            review_id=selector["review_id"],
                            decided_on=selector["decided_on"],
                            attestation_selector=selector,
                        )
                    )
                self.assertEqual(
                    REGRESSION.expert_panel.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH,
                    relative,
                )
                self.assertEqual(
                    expected_count,
                    len(validation["expected_semantic_current_bindings"]),
                )
                self.assertNotIn("expected_source_fingerprints", validation)
                parsed = REGRESSION.expert_panel.panel_attestation.parse_attestation_bytes(
                    raw,
                    expected_path=relative,
                    **validation,
                )
                validate_current(parsed)

    def test_semantic_current_validation_rejects_no_match_ambiguous_and_tampered_evidence(
        self,
    ) -> None:
        audit, _packet, selector, raw = _current_semantic_attestation(
            ("root", "reference")
        )
        for field in (
            "detector_contract_fingerprints",
            "review_contract_fingerprint",
            "findings",
        ):
            with self.subTest(field=field):
                tampered_selector = copy.deepcopy(selector)
                if field == "detector_contract_fingerprints":
                    tampered_selector[field][
                        "root_detector_contract"
                    ] = "0" * 64
                elif field == "review_contract_fingerprint":
                    tampered_selector[field] = "0" * 64
                else:
                    tampered_selector[field][0]["target_id"] = (
                        tampered_selector[field][0]["axis"] + ":" + "0" * 64
                    )
                with mock.patch.object(
                    REGRESSION.expert_panel, "_json_object", return_value=audit
                ), self.assertRaisesRegex(
                    REGRESSION.expert_panel.PanelReviewError,
                    "stale|identity|rewrite majority",
                ):
                    REGRESSION.expert_panel._current_attestation_validation(
                        REGRESSION.expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND,
                        review_id=tampered_selector["review_id"],
                        decided_on=tampered_selector["decided_on"],
                        attestation_selector=tampered_selector,
                    )

        with mock.patch.object(
            REGRESSION.expert_panel, "_json_object", return_value=audit
        ), mock.patch.object(
            REGRESSION.expert_panel,
            "_semantic_audit_for_axis_rereview",
            return_value=audit,
        ), self.assertRaisesRegex(
            REGRESSION.expert_panel.PanelReviewError,
            "findings are invalid",
        ):
            ordinary = _current_semantic_attestation(())[2]
            REGRESSION.expert_panel._current_attestation_validation(
                REGRESSION.expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND,
                review_id=ordinary["review_id"],
                decided_on=ordinary["decided_on"],
                attestation_selector=ordinary,
            )

        evidence_tamper = json.loads(raw)
        evidence_tamper["findings"][0]["candidate_binding_fingerprint"] = "0" * 64
        tampered_raw = (
            json.dumps(
                evidence_tamper,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        with mock.patch.object(
            REGRESSION.expert_panel, "_json_object", return_value=audit
        ):
            relative, validation, _validate_current = (
                REGRESSION.expert_panel._current_attestation_validation(
                    REGRESSION.expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND,
                    review_id=selector["review_id"],
                    decided_on=selector["decided_on"],
                    attestation_selector=evidence_tamper,
                )
            )
        with self.assertRaises(
            REGRESSION.expert_panel.panel_attestation.AttestationError
        ):
            REGRESSION.expert_panel.panel_attestation.parse_attestation_bytes(
                tampered_raw,
                expected_path=relative,
                **validation,
            )

    def test_fixed_semantic_storage_is_current_without_runtime_authority(self) -> None:
        for axes, expected_count in ((("root", "reference"), 208),):
            with self.subTest(axes=axes), tempfile.TemporaryDirectory() as directory:
                audit, _packet, _selector, raw = _current_semantic_attestation(axes)
                audit_raw = (
                    json.dumps(
                        audit,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                root = Path(directory)
                self._storage_repo(
                    root,
                    tracked={
                        "reports/skill-content-audit.json": audit_raw,
                        REGRESSION.expert_panel.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH: raw,
                    },
                )
                self.assertFalse((root / ".rd-skills").exists())
                with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                    REGRESSION.expert_panel, "ROOT", root
                ):
                    REGRESSION._validate_current_expert_panel_storage(formal=False)
                value = json.loads(raw)
                self.assertEqual(expected_count, len(value["findings"]))

    def test_fixed_semantic_storage_rejects_retained_rewrite_entry_in_all_modes(
        self,
    ) -> None:
        audit = source_support.live_semantic_audit()
        first_candidate = audit["root_content"]["semantic_advisories"][
            "candidates"
        ][0]
        candidate_id = first_candidate["candidate_id"]
        target_id = f"root:{candidate_id}"
        audit, _packet, _selector, raw = _current_semantic_attestation(
            ("root", "reference"),
            winner_overrides={target_id: "rewrite"},
        )
        semantic = audit["root_content"]["semantic_advisories"]
        semantic["candidates"] = [
            candidate
            for candidate in semantic["candidates"]
            if candidate.get("candidate_id") != candidate_id
        ]
        self.assertTrue(
            any(
                entry.get("candidate_id") == candidate_id
                for entry in semantic["disposition_contract"]["entries"]
            )
        )
        audit_raw = (
            json.dumps(
                audit,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            semantic_path = (
                REGRESSION.expert_panel.panel_attestation
                .SEMANTIC_DISPOSITION_ATTESTATION_PATH
            )
            self._storage_repo(
                root,
                tracked={
                    "reports/skill-content-audit.json": audit_raw,
                    semantic_path: raw,
                },
            )
            with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                REGRESSION.expert_panel, "ROOT", root
            ):
                self.assertEqual(
                    "stale",
                    REGRESSION._validate_current_expert_panel_storage(
                        formal=False
                    )[REGRESSION.expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND],
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "semantic-disposition=stale",
                ):
                    REGRESSION._validate_current_expert_panel_storage(
                        formal=True
                    )

    def test_fixed_semantic_storage_rejects_duplicate_missing_and_mismatched_entries(
        self,
    ) -> None:
        for mutation in ("duplicate", "missing", "mismatch"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                audit, _packet, _selector, raw = _current_semantic_attestation(
                    ("root", "reference")
                )
                entries = audit["root_content"]["semantic_advisories"][
                    "disposition_contract"
                ]["entries"]
                if mutation == "duplicate":
                    entries.append(copy.deepcopy(entries[0]))
                elif mutation == "missing":
                    entries.pop(0)
                else:
                    entries[0]["disposition"] = "false-positive"
                audit_raw = (
                    json.dumps(
                        audit,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                root = Path(directory)
                semantic_path = (
                    REGRESSION.expert_panel.panel_attestation
                    .SEMANTIC_DISPOSITION_ATTESTATION_PATH
                )
                self._storage_repo(
                    root,
                    tracked={
                        "reports/skill-content-audit.json": audit_raw,
                        semantic_path: raw,
                    },
                )
                with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                    REGRESSION.expert_panel, "ROOT", root
                ):
                    if mutation == "duplicate":
                        for formal in (False, True):
                            with self.assertRaisesRegex(
                                REGRESSION.expert_panel.PanelReviewError,
                                "disposition entries are duplicated",
                            ):
                                REGRESSION._validate_current_expert_panel_storage(
                                    formal=formal
                                )
                    else:
                        self.assertEqual(
                            "stale",
                            REGRESSION._validate_current_expert_panel_storage(
                                formal=False
                            )[
                                REGRESSION.expert_panel
                                .SEMANTIC_DISPOSITION_PANEL_KIND
                            ],
                        )
                        with self.assertRaisesRegex(
                            ValueError,
                            "semantic-disposition=stale",
                        ):
                            REGRESSION._validate_current_expert_panel_storage(
                                formal=True
                            )

    def test_semantic_promotion_selects_ordinary_and_forced_authority(self) -> None:
        for axes, expected_count in ((("root", "reference"), 208),):
            with self.subTest(axes=axes), tempfile.TemporaryDirectory() as directory:
                audit, _packet, selector, raw = _current_semantic_attestation(axes)
                audit_raw = (
                    json.dumps(
                        audit,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                root = Path(directory)
                self._storage_repo(
                    root,
                    tracked={
                        ".gitignore": b".rd-skills/\n",
                        "evals/expert-panel/.gitkeep": b"",
                        "reports/skill-content-audit.json": audit_raw,
                    },
                )
                source = (
                    root
                    / REGRESSION.expert_panel.panel_attestation.EPHEMERAL_RUN_ROOT
                    / selector["review_id"]
                    / "attestation.json"
                )
                source.parent.mkdir(parents=True)
                source.write_bytes(raw)
                args = argparse.Namespace(
                    panel_kind=(
                        REGRESSION.expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND
                    ),
                    review_id=selector["review_id"],
                    source=source.relative_to(root).as_posix(),
                    expected_existing_sha256="absent",
                )
                with mock.patch.object(REGRESSION.expert_panel, "ROOT", root):
                    destination = REGRESSION.expert_panel._promote_attestation(args)
                self.assertEqual(raw, destination.read_bytes())
                self.assertEqual(
                    expected_count,
                    len(json.loads(destination.read_text(encoding="utf-8"))["findings"]),
                )

    def test_current_attestation_storage_rejects_every_unexpected_tracked_path(self) -> None:
        unexpected = (
            "evals/expert-panel/semantic-disposition-panel-2026-08-10-r28/packet.json",
            "evals/expert-panel/run-r1/ballots/reviewer.json",
            "evals/expert-panel/run-r1/capsules/reviewer.json",
            "evals/expert-panel/run-r1/reviewer.template.json",
            "evals/expert-panel/run-r1/reviewer.manifest.jsonl",
            "evals/expert-panel/run-r1/panel/decision.json",
            "evals/expert-panel/run-r1/temporary.json",
            "evals/expert-panel/fourth.json",
        )
        for relative in unexpected:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._storage_repo(root, tracked={relative: b"{}\n"})
                with self.assertRaisesRegex(ValueError, "unexpected tracked"):
                    self._validate_storage(root, formal=False)
        actual = REGRESSION._validate_current_expert_panel_storage(formal=False)
        self.assertEqual(
            set(REGRESSION.expert_panel.panel_attestation.ATTESTATION_PATHS),
            set(actual),
        )
        self.assertLessEqual(
            set(actual.values()),
            {"current", "missing", "stale", "pending"},
        )

    def test_current_attestation_storage_marks_untracked_pending_and_rejects_duplicate_inventory(self) -> None:
        current = self.CURRENT_PATHS[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, untracked={current: b"{}\n"})
            panel_kind = (
                REGRESSION.expert_panel.panel_attestation.attestation_axis_for_path(
                    current
                )
            )
            self.assertEqual(
                "pending",
                self._validate_storage(root, formal=False)[panel_kind],
            )
            with self.assertRaisesRegex(ValueError, "formal.*pending"):
                self._validate_storage(root, formal=True)
        with mock.patch.object(
            REGRESSION,
            "_git_tracked_expert_panel_paths",
            return_value=[current, current],
        ), self.assertRaisesRegex(ValueError, "duplicate tracked"):
            REGRESSION._validate_current_expert_panel_storage(formal=False)

    def test_current_attestation_storage_rejects_oversize_symlink_and_nonregular(self) -> None:
        current = self.CURRENT_PATHS[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / current
            path.parent.mkdir(parents=True)
            path.write_bytes(
                b"x" * (REGRESSION.expert_panel.panel_attestation.MAX_ATTESTATION_BYTES + 1)
            )
            with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                REGRESSION,
                "_git_tracked_expert_panel_paths",
                return_value=[current],
            ), self.assertRaisesRegex(ValueError, "exceeds 4194304 bytes"):
                REGRESSION._validate_current_expert_panel_storage(formal=False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("{}\n", encoding="utf-8")
            path = root / current
            path.parent.mkdir(parents=True)
            path.symlink_to(target)
            with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                REGRESSION,
                "_git_tracked_expert_panel_paths",
                return_value=[current],
            ), self.assertRaisesRegex(ValueError, "symbolic links"):
                REGRESSION._validate_current_expert_panel_storage(formal=False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / current).mkdir(parents=True)
            with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                REGRESSION,
                "_git_tracked_expert_panel_paths",
                return_value=[current],
            ), self.assertRaisesRegex(ValueError, "regular file"):
                REGRESSION._validate_current_expert_panel_storage(formal=False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("{}\n", encoding="utf-8")
            path = root / current
            path.parent.mkdir(parents=True)
            os.link(target, path)
            with mock.patch.object(REGRESSION, "ROOT", root), mock.patch.object(
                REGRESSION,
                "_git_tracked_expert_panel_paths",
                return_value=[current],
            ), self.assertRaisesRegex(ValueError, "exactly one hard link"):
                REGRESSION._validate_current_expert_panel_storage(formal=False)

    def test_current_attestation_storage_marks_head_mismatch_and_dirty_mode_pending(self) -> None:
        current = self.CURRENT_PATHS[1]
        panel_kind = REGRESSION.expert_panel.panel_attestation.attestation_axis_for_path(
            current
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            (root / current).write_bytes(b'{"changed":true}\n')
            self.assertEqual(
                "pending",
                self._validate_storage(root, formal=False)[panel_kind],
            )
            with self.assertRaisesRegex(ValueError, "formal.*pending"):
                self._validate_storage(root, formal=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._storage_repo(root, tracked={current: b"{}\n"})
            os.chmod(root / current, 0o755)
            self.assertEqual(
                "pending",
                self._validate_storage(root, formal=False)[panel_kind],
            )
            with self.assertRaisesRegex(ValueError, "formal.*pending"):
                self._validate_storage(root, formal=True)

    def test_formal_producer_invokes_storage_validation_once(self) -> None:
        for formal, arguments in (
            (False, []),
            (True, ["--strict", "--require-expert-content-review"]),
        ):
            with self.subTest(formal=formal), tempfile.TemporaryDirectory() as directory:
                with mock.patch.object(
                    REGRESSION, "_validate_current_expert_panel_storage"
                ) as validate_storage, mock.patch.object(
                    REGRESSION, "_reports", side_effect=ValueError("stop after storage")
                ):
                    self.assertEqual(
                        1,
                        REGRESSION.main(
                            ["--reports-dir", directory, *arguments]
                        ),
                    )
                validate_storage.assert_called_once_with(formal=formal)

    def test_affected_producer_bypasses_noncurrent_storage_precheck(self) -> None:
        context = {"fixture": "affected"}
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ,
            {REGRESSION.AFFECTED_CONTEXT_ENV: "{}"},
        ), mock.patch.object(
            REGRESSION,
            "_validate_current_expert_panel_storage",
            side_effect=AssertionError(
                "affected archive must not inspect Git storage"
            ),
        ) as validate_storage, mock.patch.object(
            REGRESSION,
            "_affected_package_ids",
            return_value=[],
        ), mock.patch.object(
            REGRESSION,
            "parse_affected_professionalism_context",
            return_value=context,
        ), mock.patch.object(
            REGRESSION,
            "_affected_main",
            return_value=0,
        ) as affected_main:
            self.assertEqual(
                0,
                REGRESSION.main(["--reports-dir", directory]),
            )
        validate_storage.assert_not_called()
        affected_main.assert_called_once()

    def test_shared_fixture_uses_current_unittest_package(self) -> None:
        self.assertIs(PANEL, source_support.load_panel())
        self.assertIs(PANEL, sys.modules[PANEL.__name__])
        self.assertIs(REGRESSION, source_support.REGRESSION)

    def test_regression_loader_preserves_current_readability(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config_bytes = config_path.read_bytes()
        config = REGRESSION.load_yaml_file(config_path)
        readability_config = config["readability_review_attestation"]
        self.assertNotIn("panel_record", readability_config)
        self.assertNotIn("source_fingerprints", readability_config)
        public_limitations = " ".join(readability_config["limitations"])
        for stale_claim in (
            "readability-current-",
            "readability-fpl001-",
            "43 density targets",
            "360 readability documents",
            "983 nested findings",
        ):
            self.assertNotIn(stale_claim, public_limitations)
        for dynamic_contract in (
            "canonical fixed Readability attestation",
            "sole evidence authority",
            "validated review ID",
            "target and finding counts",
            "derived dynamically",
            "selector-free configuration",
        ):
            self.assertIn(dynamic_contract, public_limitations)
        audit = readability_support.current_audit()
        packet = readability_support.current_packet()
        fixture = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(fixture.cleanup)
        fixture_root = Path(fixture.name)
        packet_path = fixture_root / "packet.json"
        _write(packet_path, packet)
        packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        ballot_values = []
        for voter in range(1, PANEL.PANEL_SIZE + 1):
            ballot = readability_support.ballot(packet, packet_sha256, voter)
            ballot_path = fixture_root / f"readability-voter-{voter}.json"
            _write(ballot_path, ballot)
            ballot_values.append((ballot_path, ballot))
        decision = PANEL.aggregate_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=packet["created_on"],
        )
        decision_path = fixture_root / "decision.json"
        _write(decision_path, decision)
        attestation = PANEL._readability_attestation_from_decision(
            decision,
            decision_path=decision_path,
            audit=audit,
        )
        current_bindings = PANEL._readability_target_authorities(packet)
        fixed_bytes = PANEL.panel_attestation.canonical_attestation_bytes(
            attestation,
            expected_path=PANEL.panel_attestation.READABILITY_ATTESTATION_PATH,
            expected_readability_current_bindings=current_bindings,
        )
        storage_root = fixture_root / "storage"
        fixed = storage_root / PANEL.panel_attestation.READABILITY_ATTESTATION_PATH
        fixed.parent.mkdir(parents=True)
        fixed.write_bytes(fixed_bytes)
        fixed_bytes = fixed.read_bytes()
        fixed_sha256 = hashlib.sha256(fixed_bytes).hexdigest()
        value = json.loads(fixed_bytes)
        self.assertEqual(
            {
                "axis",
                "decided_on",
                "detector_contract_fingerprints",
                "findings",
                "kind",
                "rationale",
                "review_artifacts",
                "review_contract_fingerprint",
                "review_id",
                "reviewers",
                "schema_version",
                "target_manifest_binding",
                "verdict",
            },
            set(value),
        )
        self.assertEqual(
            {
                "axis": PANEL.READABILITY_PANEL_KIND,
                "kind": PANEL.panel_attestation.READABILITY_ATTESTATION_KIND,
                "review_contract_fingerprint": PANEL._canonical_json_sha256(
                    packet["panel_contract"]
                ),
                "schema_version": 2,
                "target_manifest_binding": packet["source_fingerprints"][
                    "readability_target_manifest"
                ],
                "verdict": "accepted-current-readability",
            },
            {
                field: value[field]
                for field in (
                    "axis",
                    "kind",
                    "review_contract_fingerprint",
                    "schema_version",
                    "target_manifest_binding",
                    "verdict",
                )
            },
        )
        self.assertIsInstance(value["review_id"], str)
        self.assertTrue(value["review_id"].strip())

        artifacts = value["review_artifacts"]
        self.assertEqual({"ballots", "decision", "packet"}, set(artifacts))
        self.assertEqual({"sha256"}, set(artifacts["packet"]))
        self.assertEqual({"sha256"}, set(artifacts["decision"]))
        ballots = artifacts["ballots"]
        self.assertEqual(3, len(ballots))
        self.assertTrue(
            all(set(ballot) == {"sha256", "voter_id"} for ballot in ballots)
        )
        self.assertEqual(
            sorted({ballot["voter_id"] for ballot in ballots}),
            [ballot["voter_id"] for ballot in ballots],
        )
        for digest in (
            artifacts["packet"]["sha256"],
            artifacts["decision"]["sha256"],
            *(ballot["sha256"] for ballot in ballots),
        ):
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

        by_category = {
            category: [
                row for row in value["findings"]
                if row["category"] == category
            ]
            for category in ("content", "readability", "actionability")
        }
        self.assertEqual(
            {"actionability": 0, "content": 43, "readability": 367},
            {category: len(rows) for category, rows in by_category.items()},
        )
        self.assertTrue(
            all(
                set(row)
                == {"category", "review_unit_binding", "target_id", "votes"}
                for row in by_category["content"]
            )
        )
        self.assertTrue(
            all(
                set(row) == {"category", "finding_reviews", "target_id"}
                for row in by_category["readability"]
            )
        )
        unit_bindings = [
            row["review_unit_binding"] for row in by_category["content"]
        ] + [
            finding["review_unit_binding"]
            for row in by_category["readability"]
            for finding in row["finding_reviews"]
        ]
        self.assertEqual(
            len(packet["content_targets"])
            + sum(
                len(target["findings"])
                for target in packet["readability_targets"]
            ),
            len(unit_bindings),
        )
        self.assertTrue(
            all(
                set(finding) == {"finding_id", "review_unit_binding", "votes"}
                for row in by_category["readability"]
                for finding in row["finding_reviews"]
            )
        )
        for binding in unit_bindings:
            self.assertRegex(binding, r"^[0-9a-f]{64}$")

        def nested_keys(item: object) -> set[str]:
            if isinstance(item, dict):
                return set(item) | set().union(
                    *(nested_keys(child) for child in item.values())
                )
            if isinstance(item, list):
                return set().union(*(nested_keys(child) for child in item))
            return set()

        self.assertTrue(
            {
                "source_fingerprint",
                "source_fingerprints",
                "review_binding_fingerprint",
            }.isdisjoint(nested_keys(value))
        )

        with mock.patch.object(REGRESSION, "ROOT", storage_root), mock.patch.object(
            REGRESSION, "_validate_expert_evidence"
        ) as evidence:
            application = REGRESSION._readability_review_axis(
                config_path,
                config_bytes=config_bytes,
                config_fingerprint=hashlib.sha256(config_bytes).hexdigest(),
                attestation=readability_config,
                content_skills=audit["skills"],
                readability_content=audit["ai_readability"],
                content_audit=audit,
                evaluation_date=date.fromisoformat(config["reviewed_at"]),
                storage_status="current",
            )

        evidence.assert_called_once_with(
            {
                "path": PANEL.panel_attestation.READABILITY_ATTESTATION_PATH,
                "sha256": fixed_sha256,
            }
        )
        self.assertEqual(value["review_id"], application["panel_review_id"])
        self.assertEqual(
            {
                "accepted_for_formal": True,
                "applied_actionability_disposition_count": 0,
                "applied_density_disposition_count": 43,
                "applied_readability_disposition_count": 367,
                "attestation_status": "panel-majority-current",
                "detector_false_positive_count": 0,
                "rewrite_required_count": 0,
                "source_current": True,
                "storage_current": True,
                "tracked_tightening_count": 0,
            },
            {
                field: application[field]
                for field in (
                    "accepted_for_formal",
                    "applied_actionability_disposition_count",
                    "applied_density_disposition_count",
                    "applied_readability_disposition_count",
                    "attestation_status",
                    "detector_false_positive_count",
                    "rewrite_required_count",
                    "source_current",
                    "storage_current",
                    "tracked_tightening_count",
                )
            },
        )
        self.assertEqual(
            value["target_manifest_binding"],
            application["source_fingerprints"]["readability_target_manifest"],
        )
        self.assertEqual(
            [
                {
                    "path": PANEL.panel_attestation.READABILITY_ATTESTATION_PATH,
                    "sha256": fixed_sha256,
                }
            ],
            application["evidence"],
        )
        self.assertEqual(
            {"accepted-current-density"},
            {row["disposition"] for row in application["density_dispositions"]},
        )
        self.assertEqual(
            {"accepted-current-readability"},
            {
                row["disposition"]
                for row in application["readability_dispositions"]
            },
        )

    def test_readability_config_is_selector_free_and_closed(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config = REGRESSION.load_yaml_file(config_path)
        readability = config["readability_review_attestation"]
        REGRESSION._validated_readability_config(config_path, readability)

        for field, value in (
            ("source_fingerprints", {"readability_target_manifest": "0" * 64}),
            (
                "panel_record",
                {
                    "path": PANEL.panel_attestation.READABILITY_ATTESTATION_PATH,
                    "sha256": "0" * 64,
                },
            ),
            ("review_id", "configured-review-id"),
        ):
            changed = copy.deepcopy(readability)
            changed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                ValueError, "selector-free schema 5 contract"
            ):
                REGRESSION._validated_readability_config(
                    config_path, changed
                )

    def test_regression_loader_preserves_current_semantic(self) -> None:
        config_path = ROOT / "config/skill-content-exceptions.yaml"
        config = REGRESSION.load_yaml_file(config_path)
        fixed = (
            ROOT
            / PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
        )
        fixed_bytes = fixed.read_bytes()
        self.assertEqual(
            "2a5a19fca3465a4409f3624564c600cdb62fb467f3b3348c3a0b3973c4adc774",
            hashlib.sha256(fixed_bytes).hexdigest(),
        )
        value = json.loads(fixed_bytes)
        self.assertEqual(
            {
                "axis",
                "decided_on",
                "detector_contract_fingerprints",
                "findings",
                "kind",
                "rationale",
                "review_contract_fingerprint",
                "review_id",
                "reviewers",
                "schema_version",
                "verdict",
            },
            set(value),
        )
        self.assertEqual(2, value["schema_version"])
        self.assertEqual(
            PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND,
            value["kind"],
        )
        self.assertEqual(PANEL.SEMANTIC_DISPOSITION_PANEL_KIND, value["axis"])
        self.assertEqual(
            "accepted-current-semantic-disposition", value["verdict"]
        )
        self.assertEqual("semantic-refresh-20260816-r1", value["review_id"])
        self.assertEqual(206, len(value["findings"]))
        self.assertEqual(
            PANEL._canonical_json_sha256(
                PANEL._semantic_panel_contract(
                    root_target_count=81,
                    reference_target_count=125,
                )
            ),
            value["review_contract_fingerprint"],
        )

        live_audit = copy.deepcopy(source_support.live_semantic_audit())
        root_semantic, reference_semantic = PANEL._semantic_audit_sections(
            live_audit
        )
        current_fingerprints = PANEL._semantic_source_fingerprints(
            live_audit,
            root_semantic=root_semantic,
            reference_semantic=reference_semantic,
        )
        detector_keys = {
            "reference_detector_contract",
            "root_detector_contract",
        }
        self.assertEqual(
            detector_keys, set(value["detector_contract_fingerprints"])
        )
        self.assertEqual(
            {
                key: current_fingerprints[key]
                for key in sorted(detector_keys)
            },
            value["detector_contract_fingerprints"],
        )

        configured = {
            f"{axis}:{entry['candidate_id']}": entry["disposition"]
            for axis, key in (
                ("root", "root_semantic_dispositions"),
                ("reference", "reference_semantic_dispositions"),
            )
            for entry in config[key]["entries"]
        }
        winners = {}
        for finding in value["findings"]:
            self.assertEqual(
                {
                    "axis",
                    "candidate_binding_fingerprint",
                    "target_id",
                    "votes",
                },
                set(finding),
            )
            axis = finding["axis"]
            target_id = finding["target_id"]
            self.assertIn(axis, PANEL.SEMANTIC_AXES)
            self.assertRegex(target_id, rf"^{axis}:[0-9a-f]{{64}}$")
            self.assertRegex(
                finding["candidate_binding_fingerprint"], r"^[0-9a-f]{64}$"
            )
            votes = finding["votes"]
            self.assertEqual(PANEL.PANEL_SIZE, len(votes))
            voter_ids = [vote["voter_id"] for vote in votes]
            self.assertEqual(sorted(set(voter_ids)), voter_ids)
            vote_counts = {
                disposition: sum(
                    vote["disposition"] == disposition for vote in votes
                )
                for disposition in sorted(PANEL.SEMANTIC_DISPOSITIONS)
            }
            majority = [
                disposition
                for disposition, count in vote_counts.items()
                if count >= 2
            ]
            self.assertEqual(1, len(majority))
            winners[target_id] = majority[0]

        self.assertEqual(
            {"reference": 125, "root": 81},
            {
                axis: sum(target_id.startswith(f"{axis}:") for target_id in winners)
                for axis in ("reference", "root")
            },
        )
        self.assertEqual(208, len(configured))
        self.assertNotEqual(set(configured), set(winners))

        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "semantic fixed missing target lacks a rewrite majority",
        ):
            PANEL.validate_semantic_decision_application(live_audit)

    def test_regression_loader_preserves_current_professional(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config_bytes = config_path.read_bytes()
        config = REGRESSION.load_yaml_file(config_path)
        professional_config = config[
            "professional_completeness_review_attestation"
        ]
        self.assertNotIn("panel_record", professional_config)
        self.assertNotIn("source_fingerprints", professional_config)
        current_packet = REGRESSION._current_professional_completeness_packet()
        current_targets = []
        for embedded_target in current_packet["professional_targets"]:
            target = copy.deepcopy(embedded_target)
            target.pop("review_binding")
            current_targets.append(target)
        fixed_bytes = (
            professional_support._current_compact_professional_fixture_bytes(
                current_targets,
                review_contract_fingerprint=current_packet[
                    "review_contract_fingerprint"
                ],
            )
        )
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        validation_root = Path(fixture.name)
        fixed = (
            validation_root
            / PANEL.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
        )
        fixed.parent.mkdir(parents=True)
        fixed.write_bytes(fixed_bytes)
        fixed_bytes = fixed.read_bytes()
        fixed_sha256 = hashlib.sha256(fixed_bytes).hexdigest()
        value = json.loads(fixed_bytes)
        self.assertEqual(
            {
                "axis",
                "decided_on",
                "dependency_material_catalog",
                "findings",
                "kind",
                "rationale",
                "review_contract_fingerprint",
                "review_cost_input",
                "review_id",
                "reviewers",
                "schema_version",
                "storage_encoding",
                "string_catalog",
                "verdict",
            },
            set(value),
        )
        self.assertEqual(2, value["schema_version"])
        self.assertEqual(
            PANEL.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND,
            value["kind"],
        )
        self.assertEqual(
            PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
            value["axis"],
        )
        self.assertEqual("professional-refresh-20260816-r1", value["review_id"])
        self.assertEqual(
            current_packet["review_contract_fingerprint"],
            value["review_contract_fingerprint"],
        )
        self.assertEqual(
            PANEL.panel_attestation.PROFESSIONAL_STORAGE_ENCODING,
            value["storage_encoding"],
        )
        catalog = value["string_catalog"]
        self.assertTrue(catalog)
        self.assertEqual(sorted(set(catalog)), catalog)
        for field in (
            "source_fingerprints",
            "source_fingerprint",
            "package_fingerprint",
            "review_binding_fingerprint",
        ):
            self.assertNotIn(field, value)

        self.assertEqual(
            value["review_contract_fingerprint"],
            current_packet["review_contract_fingerprint"],
        )
        with mock.patch.object(
            REGRESSION, "ROOT", validation_root
        ), mock.patch.object(
            REGRESSION, "_validate_expert_evidence"
        ) as evidence:
            application = REGRESSION._professional_completeness_review_axis(
                config_path,
                config_bytes=config_bytes,
                config_fingerprint=hashlib.sha256(config_bytes).hexdigest(),
                attestation=professional_config,
                current_packet=current_packet,
                evaluation_date=date.fromisoformat(config["reviewed_at"]),
                storage_status="current",
            )

        evidence.assert_called_once_with(
            {
                "path": (
                    PANEL.panel_attestation
                    .PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
                ),
                "sha256": fixed_sha256,
            }
        )
        self.assertEqual("panel-majority-current", application["attestation_status"])
        self.assertTrue(application["storage_current"])
        self.assertTrue(application["source_current"])
        self.assertTrue(application["accepted_for_formal"])
        self.assertEqual(value["review_id"], application["panel_review_id"])
        self.assertEqual(
            value["review_contract_fingerprint"],
            application["review_contract_fingerprint"],
        )
        self.assertEqual(
            PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
            application["panel_artifact_schema_version"],
        )
        self.assertEqual(189, application["applied_target_count"])
        self.assertEqual(189, application["accepted_current_count"])
        self.assertEqual(0, application["correction_count"])
        self.assertEqual(
            0,
            application["unresolved_professional_disagreement_count"],
        )
        self.assertEqual(
            [
                {
                    "path": (
                        PANEL.panel_attestation
                        .PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
                    ),
                    "sha256": fixed_sha256,
                }
            ],
            application["evidence"],
        )
        dispositions = application["professional_dispositions"]
        self.assertEqual(
            {
                "accepted-current-professional-completeness": 189,
                "requires-professional-correction": 0,
                PANEL.PROFESSIONAL_UNRESOLVED_DISPOSITION: 0,
            },
            {
                disposition: sum(
                    row["disposition"] == disposition
                    for row in dispositions
                )
                for disposition in (
                    "accepted-current-professional-completeness",
                    "requires-professional-correction",
                    PANEL.PROFESSIONAL_UNRESOLVED_DISPOSITION,
                )
            },
        )
        self.assertEqual(
            {"carried": 56, "fresh": 133},
            {
                mode: sum(
                    row["provenance"]["mode"] == mode
                    for row in dispositions
                )
                for mode in ("carried", "fresh")
            },
        )
        self.assertEqual(
            {
                "carried": {
                    (
                        "professional-fpl001-fresh-20260814-r4",
                        "a31ea263084894ccc4358696d3860e49857d3af2",
                    )
                },
                "fresh": {
                    (
                        "professional-refresh-20260816-r1",
                        "d6534d06d1537ca29da16832b37e078f903f58ee",
                    )
                },
            },
            {
                mode: {
                    (
                        row["provenance"]["origin"]["origin_review_id"],
                        row["provenance"]["origin"]["origin_commit"],
                    )
                    for row in dispositions
                    if row["provenance"]["mode"] == mode
                }
                for mode in ("carried", "fresh")
            },
        )

        cost = application["review_cost"]
        target_count = application["applied_target_count"]
        self.assertEqual(PANEL.PROFESSIONAL_PACKAGE_COUNT, target_count)
        self.assertEqual(3, application["reviewer_pool_size"])
        self.assertEqual(
            {
                "carried_forward_target_count": 56,
                "fresh_target_count": 133,
            },
            {
                field: application[field]
                for field in (
                    "carried_forward_target_count",
                    "fresh_target_count",
                )
            },
        )
        self.assertEqual(
            {
                "carried_forward_vote_count": 168,
                "effective_vote_count": 567,
                "fresh_vote_count": 399,
            },
            {
                field: cost[field]
                for field in (
                    "carried_forward_vote_count",
                    "effective_vote_count",
                    "fresh_vote_count",
                )
            },
        )
        self.assertEqual(
            {
                "carried_forward_criterion_result_count": 1680,
                "effective_criterion_result_count": 5670,
                "fresh_criterion_result_count": 3990,
            },
            {
                field: cost[field]
                for field in (
                    "carried_forward_criterion_result_count",
                    "effective_criterion_result_count",
                    "fresh_criterion_result_count",
                )
            },
        )
        self.assertGreater(cost["canonical_capsule_input_bytes_proxy"], 0)
        self.assertEqual(
            (
                cost["canonical_capsule_input_bytes_proxy"]
                * 1_000_000
                // cost[
                    "full_rereview_deduplicated_capsule_input_bytes_proxy"
                ]
            ),
            cost["input_ratio_ppm"],
        )
        self.assertEqual(
            {
                "input_ratio_ppm": 729116,
                "required_only_input_ratio_ppm": 727995,
                "source_material_coverage_ratio_ppm": 1_000_000,
            },
            {
                field: cost[field]
                for field in (
                    "input_ratio_ppm",
                    "required_only_input_ratio_ppm",
                    "source_material_coverage_ratio_ppm",
                )
            },
        )
        self.assertEqual(
            (
                cost["reviewer_added_source_material_input_bytes_proxy"]
                + cost[
                    "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy"
                ]
            ),
            (
                cost["canonical_capsule_input_bytes_proxy"]
                - cost["required_only_capsule_input_bytes_proxy"]
            ),
        )
        self.assertEqual("incremental-reduced-input", cost["policy_status"])
        self.assertTrue(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=133,
                carried_forward_target_count=56,
            )
        )
        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=86,
                carried_forward_target_count=103,
            )
        )

        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=0,
                carried_forward_target_count=target_count,
            )
        )

    def test_professional_config_is_selector_free_and_closed(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config = REGRESSION.load_yaml_file(config_path)
        professional = config["professional_completeness_review_attestation"]
        REGRESSION._validated_professional_config(config_path, professional)

        for field, value in (
            (
                "source_fingerprints",
                {"professional_packages": "0" * 64},
            ),
            (
                "panel_record",
                {
                    "path": PANEL.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
                    "sha256": "0" * 64,
                },
            ),
            ("review_id", "configured-review-id"),
            ("review_contract_fingerprint", "0" * 64),
        ):
            changed = copy.deepcopy(professional)
            changed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                ValueError, "selector-free schema 5 contract"
            ):
                REGRESSION._validated_professional_config(
                    config_path, changed
                )

    def test_canonical_schema3_axis_preserves_currentness_classification(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config_bytes = config_path.read_bytes()
        config = REGRESSION.load_yaml_file(config_path)
        evaluation_date = date.fromisoformat(config["reviewed_at"])
        current_packet = REGRESSION._current_professional_completeness_packet()
        result = REGRESSION._professional_completeness_review_axis(
            config_path,
            config_bytes=config_bytes,
            config_fingerprint=hashlib.sha256(config_bytes).hexdigest(),
            attestation=config["professional_completeness_review_attestation"],
            current_packet=current_packet,
            evaluation_date=evaluation_date,
            storage_status="stale",
        )

        self.assertEqual("panel-majority-stale", result["attestation_status"])
        self.assertFalse(result["decision_complete"])
        self.assertFalse(result["storage_current"])
        self.assertFalse(result["source_current"])
        self.assertFalse(result["accepted_for_formal"])
        self.assertEqual(
            {},
            result["current_source_fingerprints"],
        )
        self.assertIsNone(result["attested_on"])

        stale = REGRESSION._professional_completeness_review_axis(
            config_path,
            config_bytes=config_bytes,
            config_fingerprint=hashlib.sha256(config_bytes).hexdigest(),
            attestation=config["professional_completeness_review_attestation"],
            current_packet=current_packet,
            evaluation_date=evaluation_date,
            storage_status="stale",
        )
        self.assertEqual("panel-majority-stale", stale["attestation_status"])
        self.assertFalse(stale["decision_complete"])
        self.assertFalse(stale["storage_current"])
        self.assertFalse(stale["source_current"])
        self.assertFalse(stale["accepted_for_formal"])
        self.assertIsNone(stale["attested_on"])

    def test_legacy_review_normalizes_to_two_non_authoritative_axes(self) -> None:
        legacy = {
            "expert_content_review_complete": True,
            "panel_decision_complete": True,
            "storage_current": True,
            "decision_method": PANEL.DECISION_METHOD,
            "panel_review_id": "historical-readability-panel",
            "panel_size": 3,
            "attestation_source": "fixture#expert_content_review_attestation",
            "attestation_schema_version": 5,
            "attestation_config_fingerprint": "a" * 64,
            "source_fingerprints": {
                "reference_content": "b" * 64,
                "root_content": "c" * 64,
                "ai_readability": "d" * 64,
            },
            "attested_by": "expert-panel:historical-readability-panel",
            "attested_on": "2026-07-16",
            "evidence": [],
            "content_dispositions": [
                {
                    "path": "src/foundation/capabilities/a/SKILL.md",
                    "classification": "REVIEW_DENSITY",
                    "disposition": "accepted-current-density",
                    "rationale": "A historical density rationale remains available here.",
                }
            ],
            "readability_dispositions": [
                {
                    "document_id": "fixture#body",
                    "highest_band": "review-as-complex",
                    "disposition": "tracked-tightening",
                    "rationale": "A historical tightening rationale remains available here.",
                }
            ],
            "required_content_disposition_count": 1,
            "applied_content_disposition_count": 1,
            "content_blocker_count": 0,
            "required_readability_disposition_count": 1,
            "applied_readability_disposition_count": 1,
            "readability_blocker_count": 0,
            "limitations": ["Historical fixture."],
        }

        result = REGRESSION._normalized_expert_reviews(legacy)

        self.assertTrue(result["deprecated_legacy_attestation"])
        self.assertFalse(result["readability"]["accepted_for_formal"])
        self.assertEqual(1, result["readability"]["tracked_tightening_count"])
        self.assertFalse(
            result["professional_completeness"]["decision_complete"]
        )
        self.assertIsNone(
            result["professional_completeness"]["correction_count"]
        )
        self.assertFalse(
            result["professional_completeness"]["accepted_for_formal"]
        )

    def _fixture(self, root: Path) -> tuple[Path, Path, list[Path], dict]:
        packet = _packet()
        packet_path = root / "packet.json"
        _write(packet_path, packet)
        packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        ballots: list[Path] = []
        ballot_values = []
        for voter in range(1, 4):
            path = root / f"expert-{voter}.json"
            value = _ballot(packet, packet_sha, voter)
            _write(path, value)
            ballots.append(path)
            ballot_values.append((path, value))
        record = PANEL.aggregate_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on="2026-07-16",
        )
        record_path = root / "decision.json"
        _write(record_path, record)
        config = {
            "schema_version": 5,
            "review_owner": "changeforge-expert-panel-governance",
            "reviewed_at": "2026-07-16",
            "decisions": [],
            "expert_content_review_attestation": {
                "schema_version": 5,
                "scope": "agent-facing-content",
                "decision_method": PANEL.DECISION_METHOD,
                "source_fingerprints": packet["source_fingerprints"],
                "panel_record": {
                    "path": record_path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
                },
                "limitations": ["Static panel evidence does not prove host behavior."],
            },
        }
        config_path = root / "review.json"
        _write(config_path, config)
        return config_path, record_path, ballots, packet

    def _dual_config(self) -> dict:
        config = copy.deepcopy(
            REGRESSION.load_yaml_file(
                ROOT / "config/professionalism-release-review.yaml"
            )
        )
        config["reviewed_at"] = "2026-07-16"
        config["decisions"] = []
        return config

    def test_dual_parser_preserves_stale_readability_and_blocks_missing_completeness(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            data = self._dual_config()
            readability_sources = {
                "readability_target_manifest": "1" * 64,
                "readability_detector_contract": "2" * 64,
                "actionability_detector_contract": "3" * 64,
            }
            with mock.patch.object(
                REGRESSION.expert_panel,
                "prepare_packet",
                return_value={
                    "source_fingerprints": readability_sources,
                    "panel_contract": {},
                },
            ), mock.patch.object(
                REGRESSION.expert_panel,
                "_readability_target_authorities",
                return_value={"actionability": {}},
            ):
                result = REGRESSION._dual_expert_reviews_from_data(
                    Path(raw) / "dual-review.yaml",
                    data=data,
                    config_bytes=b"dual-fixture\n",
                    reference_fingerprint="9" * 64,
                    root_fingerprint="8" * 64,
                    ai_readability_fingerprint="7" * 64,
                    content_skills=[
                        {
                            "path": "src/foundation/capabilities/a/SKILL.md",
                            "classification": "REVIEW_DENSITY",
                        }
                    ],
                    readability_content={
                        "summary": {
                            "advisory_documents": 1,
                            "blocker_findings": 0,
                        },
                        "documents": [
                            {
                                "document_id": (
                                    "src/foundation/capabilities/a/SKILL.md#body"
                                ),
                                "highest_advisory_band": "review-as-complex",
                            }
                        ],
                    },
                    current_completeness_packet={
                        "source_fingerprints": {
                            "professional_packages": "6" * 64
                        },
                        "professional_targets": [
                            {
                                "skill_id": f"skill-{index}",
                                "package_fingerprint": "5" * 64,
                            }
                            for index in range(PANEL.PROFESSIONAL_PACKAGE_COUNT)
                        ],
                    },
                    evaluation_date=date(2026, 7, 16),
                    content_audit={},
                    storage_statuses={
                        PANEL.READABILITY_PANEL_KIND: "stale",
                        PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND: "missing",
                    },
                )

            self.assertFalse(result["readability"]["decision_complete"])
            self.assertFalse(result["readability"]["source_current"])
            self.assertEqual(
                "panel-majority-stale",
                result["readability"]["attestation_status"],
            )
            self.assertFalse(result["readability"]["accepted_for_formal"])
            completeness = result["professional_completeness"]
            self.assertEqual("missing-evidence", completeness["attestation_status"])
            self.assertEqual(
                PANEL.PROFESSIONAL_PACKAGE_COUNT,
                completeness["required_target_count"],
            )
            self.assertIsNone(completeness["correction_count"])

    def test_fixed_axes_reuse_noncurrent_storage_status_without_formal_authority(
        self,
    ) -> None:
        readability_sources = {
            "reference_content": "1" * 64,
            "root_content": "2" * 64,
            "ai_readability": "3" * 64,
            "skill_detector": "4" * 64,
        }
        with mock.patch.object(
            REGRESSION,
            "_validated_readability_config",
            return_value=({}, []),
        ), mock.patch.object(
            REGRESSION.expert_panel,
            "prepare_packet",
            return_value={
                "source_fingerprints": readability_sources,
                "panel_contract": {},
            },
        ), mock.patch.object(
            REGRESSION.expert_panel,
            "_readability_target_authorities",
            return_value={"actionability": {}},
        ), mock.patch.object(
            REGRESSION,
            "_apply_fixed_readability_attestation",
            side_effect=AssertionError("stale fixed evidence must not be applied"),
        ):
            readability = REGRESSION._readability_review_axis(
                Path("config/professionalism-release-review.yaml"),
                config_bytes=b"fixture\n",
                config_fingerprint="6" * 64,
                attestation={},
                content_skills=[],
                readability_content={
                    "summary": {
                        "advisory_documents": 0,
                        "blocker_findings": 0,
                    },
                    "documents": [],
                },
                content_audit={},
                evaluation_date=date(2026, 8, 11),
                storage_status="stale",
            )
        self.assertEqual("panel-majority-stale", readability["attestation_status"])
        self.assertFalse(readability["storage_current"])
        self.assertFalse(readability["source_current"])
        self.assertFalse(readability["accepted_for_formal"])

        current_packet = {
            "source_fingerprints": {
                "professional_packages": "7" * 64,
                "professional_review_contract": "8" * 64,
            },
            "professional_targets": [],
        }
        with mock.patch.object(
            REGRESSION,
            "_validated_professional_config",
            return_value=({}, []),
        ), mock.patch.object(
            REGRESSION,
            "_apply_fixed_professional_attestation",
            side_effect=AssertionError("pending fixed evidence must not be applied"),
        ):
            professional = REGRESSION._professional_completeness_review_axis(
                Path("config/professionalism-release-review.yaml"),
                config_bytes=b"fixture\n",
                config_fingerprint="a" * 64,
                attestation={},
                current_packet=current_packet,
                evaluation_date=date(2026, 8, 11),
                storage_status="pending",
            )
        self.assertEqual(
            "panel-majority-pending-checkin",
            professional["attestation_status"],
        )
        self.assertFalse(professional["storage_current"])
        self.assertFalse(professional["source_current"])
        self.assertFalse(professional["accepted_for_formal"])

    def test_dual_parser_rejects_cross_axis_decision_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            data = self._dual_config()
            readability_sources = {
                "readability_target_manifest": "1" * 64,
                "readability_detector_contract": "2" * 64,
                "actionability_detector_contract": "3" * 64,
            }
            with mock.patch.object(
                REGRESSION.expert_panel,
                "prepare_packet",
                return_value={
                    "source_fingerprints": readability_sources,
                    "panel_contract": {},
                },
            ), mock.patch.object(
                REGRESSION.expert_panel,
                "_readability_target_authorities",
                return_value={"actionability": {}},
            ), mock.patch.object(
                REGRESSION,
                "_load_fixed_compact_attestation",
                side_effect=ValueError("wrong review axis"),
            ), self.assertRaisesRegex(ValueError, "wrong review axis"):
                REGRESSION._dual_expert_reviews_from_data(
                    Path(raw) / "dual-review.yaml",
                    data=data,
                    config_bytes=b"dual-fixture\n",
                    reference_fingerprint="9" * 64,
                    root_fingerprint="8" * 64,
                    ai_readability_fingerprint="7" * 64,
                    content_skills=[],
                    readability_content={
                        "summary": {
                            "advisory_documents": 0,
                            "blocker_findings": 0,
                        },
                        "documents": [],
                    },
                    current_completeness_packet={
                        "source_fingerprints": {
                            "professional_packages": "6" * 64
                        },
                        "professional_targets": [],
                    },
                    evaluation_date=date(2026, 7, 16),
                    content_audit={},
                )

    def _formal_reviews(self) -> dict:
        return {
            "deprecated_expert_content_review_complete": False,
            "readability": {
                "panel_kind": PANEL.READABILITY_PANEL_KIND,
                "scope": "ai-readability-and-density",
                "decision_complete": True,
                "storage_current": True,
                "source_current": True,
                "accepted_for_formal": True,
                "decision_method": PANEL.DECISION_METHOD,
                "panel_size": PANEL.PANEL_SIZE,
                "panel_artifact_schema_version": 2,
                "attestation_schema_version": 5,
                "attestation_status": "panel-majority-current",
                "attestation_source": "fixture#readability_review_attestation",
                "tracked_tightening_count": 0,
                "detector_false_positive_count": 0,
                "rewrite_required_count": 0,
                "blocker_count": 0,
                "required_density_disposition_count": 2,
                "applied_density_disposition_count": 2,
                "required_readability_disposition_count": 3,
                "applied_readability_disposition_count": 3,
                "required_actionability_disposition_count": 120,
                "applied_actionability_disposition_count": 120,
            },
            "professional_completeness": {
                "panel_kind": PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                "scope": "professional-skill-packages",
                "decision_complete": True,
                "storage_current": True,
                "source_current": True,
                "accepted_for_formal": True,
                "decision_method": (
                    PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
                ),
                "panel_size": PANEL.PANEL_SIZE,
                "reviewer_pool_size": PANEL.PANEL_SIZE,
                "panel_artifact_schema_version": 3,
                "attestation_schema_version": 5,
                "attestation_status": "panel-majority-current",
                "attestation_source": (
                    "fixture#professional_completeness_review_attestation"
                ),
                "required_target_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
                "fresh_target_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
                "carried_forward_target_count": 0,
                "applied_target_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
                "accepted_current_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
                "correction_count": 0,
                "unresolved_professional_disagreement_count": 0,
                "evidence_contract_satisfied": True,
                "qualification_summary": {
                    "covered_target_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
                    "required_domain_experts_per_target": 2,
                    "required_architecture_experts_per_target": 1,
                    "per_target_panel_size": 3,
                    "fresh_reviewer_pool_size": 3,
                    "effective_domain_vote_count": 378,
                    "effective_architecture_vote_count": 189,
                },
                "evidence_summary": {
                    "target_vote_count": 567,
                    "required_adjacency_candidate_count": 905,
                    "criterion_result_count": 5670,
                    "criterion_anchor_binding_count": 5670,
                    "criterion_assertion_count": 5670,
                    "evidence_anchor_count": 1134,
                    "examined_failure_mode_count": 1134,
                    "examined_omission_candidate_count": 1134,
                    "examined_adjacency_count": 2715,
                    "examined_required_adjacency_count": 2715,
                    "reviewer_added_adjacency_count": 0,
                    "proof_limit_count": 567,
                    "qualification_claim_count": 567,
                },
                "review_contract_current": True,
                "review_plan_current": True,
                "review_binding_current": True,
                "provenance_current": True,
                "round_lifecycle_current": True,
                "review_cost_current": True,
                "review_cost": _full_fresh_review_cost(),
            },
        }

    def test_release_gate_accepts_two_clean_axes_and_current_manifest(self) -> None:
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            self._formal_reviews(),
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_PASS, gate)
        self.assertEqual([], blockers)

    def test_content_readiness_aggregate_uses_complete_axis_contracts(self) -> None:
        summaries = {
            "source_fingerprint": "a" * 64,
            "strict_ready_basis": "fixture",
            "structural_strict_ready": True,
            "semantic_triage_complete": True,
            "strict_ready": True,
        }
        reviews = self._formal_reviews()
        readiness = REGRESSION._content_readiness(
            summaries,
            summaries,
            reviews,
        )
        self.assertTrue(readiness["aggregate"]["readability_review_current"])
        self.assertTrue(
            readiness["aggregate"]["professional_completeness_review_current"]
        )

        readability_flips = {
            "decision_complete": False,
            "storage_current": False,
            "source_current": False,
            "accepted_for_formal": False,
            "attestation_status": "panel-majority-stale",
            "applied_density_disposition_count": 1,
            "applied_readability_disposition_count": 2,
            "applied_actionability_disposition_count": 119,
        }
        for field, changed_value in readability_flips.items():
            with self.subTest(axis="readability", field=field):
                changed = copy.deepcopy(reviews)
                changed["readability"][field] = changed_value
                actual = REGRESSION._content_readiness(
                    summaries,
                    summaries,
                    changed,
                )
                self.assertFalse(
                    actual["aggregate"]["readability_review_current"]
                )

        professional_flips = {
            "decision_complete": False,
            "storage_current": False,
            "source_current": False,
            "accepted_for_formal": False,
            "attestation_status": "panel-majority-stale",
            "required_target_count": 188,
            "applied_target_count": 188,
            "accepted_current_count": 188,
        }
        for field, changed_value in professional_flips.items():
            with self.subTest(axis="professional_completeness", field=field):
                changed = copy.deepcopy(reviews)
                changed["professional_completeness"][field] = changed_value
                actual = REGRESSION._content_readiness(
                    summaries,
                    summaries,
                    changed,
                )
                self.assertFalse(
                    actual["aggregate"][
                        "professional_completeness_review_current"
                    ]
                )

    def test_all_carry_zero_input_requires_zero_fresh_reviewer_pool(self) -> None:
        reviews = self._formal_reviews()
        completeness = reviews["professional_completeness"]
        completeness.update(
            {
                "fresh_target_count": 0,
                "carried_forward_target_count": 189,
                "reviewer_pool_size": 0,
                "review_cost": _all_carry_review_cost(),
            }
        )
        completeness["qualification_summary"]["fresh_reviewer_pool_size"] = 0
        self.assertTrue(
            REGRESSION._professional_completeness_review_formal_ready(
                completeness
            )
        )
        completeness["reviewer_pool_size"] = 3
        self.assertFalse(
            REGRESSION._professional_completeness_review_formal_ready(
                completeness
            )
        )
        completeness["reviewer_pool_size"] = 0
        completeness["review_cost"]["canonical_capsule_input_bytes_proxy"] = 1
        self.assertFalse(
            REGRESSION._professional_completeness_review_formal_ready(
                completeness
            )
        )

    def test_forged_review_cost_current_boolean_cannot_bypass_raw_policy(self) -> None:
        completeness = self._formal_reviews()["professional_completeness"]
        completeness["review_cost"] = {"policy_status": "bootstrap-full-review"}
        self.assertFalse(
            REGRESSION._professional_completeness_review_formal_ready(
                completeness
            )
        )

    def test_split_review_cost_policy_accepts_raw_metadata_overhead(self) -> None:
        cost = _full_fresh_review_cost()
        self.assertGreater(cost["input_ratio_ppm"], 1_000_000)
        self.assertTrue(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=189,
                carried_forward_target_count=0,
            )
        )

    def test_metadata_overhead_uses_exact_cross_multiplication(self) -> None:
        boundary = _recompose_review_cost(
            _full_fresh_review_cost(),
            denominator=1_000_200,
            full_source=200,
            required_source=200,
            actual_source=200,
            required_metadata=1_000_000,
            metadata_overhead=50_000,
        )
        self.assertTrue(
            REGRESSION._professional_review_cost_policy_satisfied(
                boundary,
                fresh_target_count=189,
                carried_forward_target_count=0,
            )
        )

        plus_one = _recompose_review_cost(
            copy.deepcopy(boundary),
            denominator=1_000_200,
            full_source=200,
            required_source=200,
            actual_source=200,
            required_metadata=1_000_000,
            metadata_overhead=50_001,
        )
        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                plus_one,
                fresh_target_count=189,
                carried_forward_target_count=0,
            )
        )

        floor_collision = _recompose_review_cost(
            _full_fresh_review_cost(),
            denominator=1_000_201,
            full_source=200,
            required_source=200,
            actual_source=200,
            required_metadata=1_000_001,
            metadata_overhead=50_001,
        )
        self.assertEqual(
            50_000,
            floor_collision[
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ],
        )
        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                floor_collision,
                fresh_target_count=189,
                carried_forward_target_count=0,
            )
        )

    def test_incremental_split_cost_positive_and_boundaries(self) -> None:
        valid = _incremental_review_cost()
        self.assertTrue(
            REGRESSION._professional_review_cost_policy_satisfied(
                valid,
                fresh_target_count=1,
                carried_forward_target_count=188,
            )
        )

        mutations = {
            "required-not-reduced": lambda cost: cost.update(
                {
                    "full_rereview_deduplicated_capsule_input_bytes_proxy": cost[
                        "required_only_capsule_input_bytes_proxy"
                    ],
                    "input_ratio_ppm": cost[
                        "canonical_capsule_input_bytes_proxy"
                    ]
                    * 1_000_000
                    // cost["required_only_capsule_input_bytes_proxy"],
                    "required_only_input_ratio_ppm": 1_000_000,
                }
            ),
            "actual-source-below-required": lambda cost: cost.update(
                {
                    "source_material_input_bytes_proxy": 199,
                    "source_material_coverage_ratio_ppm": 497_500,
                }
            ),
            "lineage-over-boundary": lambda cost: cost.__setitem__(
                "plan_lineage_depth", 9
            ),
            "metadata-one-byte-over": lambda cost: _recompose_review_cost(
                cost,
                denominator=2_000_400,
                full_source=400,
                required_source=200,
                actual_source=200,
                required_metadata=1_000_000,
                metadata_overhead=50_001,
            ),
            "union-one-ppm-over": lambda cost: cost.__setitem__(
                "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
                1_000_001,
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                cost = copy.deepcopy(valid)
                mutate(cost)
                self.assertFalse(
                    REGRESSION._professional_review_cost_policy_satisfied(
                        cost,
                        fresh_target_count=1,
                        carried_forward_target_count=188,
                    )
                )

        zero_metadata = copy.deepcopy(valid)
        zero_metadata.update(
            {
                "reviewer_added_request_count": 0,
                "reviewer_added_unique_relationship_count": 0,
                "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 0,
            }
        )
        _recompose_review_cost(
            zero_metadata,
            denominator=400,
            full_source=400,
            required_source=200,
            actual_source=200,
            required_metadata=0,
            metadata_overhead=0,
        )
        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                zero_metadata,
                fresh_target_count=1,
                carried_forward_target_count=188,
            )
        )

    def test_schema3_cost_producer_recomputes_canonical_chain_and_exact_owner_boundaries(
        self,
    ) -> None:
        producer_panel = PANEL
        packet = professional_support._bootstrap_packet()
        state = producer_panel._professional_v3_packet_state(
            packet,
            validation_root=producer_panel.ROOT,
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
        required_ids = {
            row["skill_id"]
            for row in target["routing_adjacency"]["required_candidates"]
        }
        candidate_id = next(
            row["skill_id"]
            for row in target["routing_adjacency"]["full_catalog_ranking"]
            if row["skill_id"] not in required_ids
        )
        all_skill_ids = sorted(state["bindings"])
        fresh_ids = [target_id] + [
            skill_id
            for skill_id in all_skill_ids
            if skill_id != target_id
        ][:39]
        fresh_set = set(fresh_ids)
        reason = (
            "Reviewer independently found a plausible responsibility boundary "
            "outside the machine-required candidate set."
        )

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            round_root = validation_root / packet["review_id"]
            voters = []
            block_sizes: dict[str, int] = {}
            block_occurrences: dict[str, int] = {}
            for voter_id in ("architecture-one", "domain-one", "domain-two"):
                discovery = producer_panel.prepare_professional_discovery_capsule_v3(
                    packet=packet,
                    packet_sha256="a" * 64,
                    voter_id=voter_id,
                    assigned_skill_ids=fresh_ids,
                    created_on="2026-07-17",
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=state,
                )
                discovery_path = (
                    round_root / "discovery-capsules" / f"{voter_id}.json"
                )
                discovery_path.parent.mkdir(parents=True, exist_ok=True)
                source_support.write_json(discovery_path, discovery)
                request = producer_panel.prepare_professional_candidate_request_v3(
                    packet=packet,
                    packet_sha256="a" * 64,
                    discovery_capsule_path=discovery_path,
                    voter_id=voter_id,
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
                request_path = (
                    round_root / "candidate-requests" / f"{voter_id}.json"
                )
                request_path.parent.mkdir(parents=True, exist_ok=True)
                source_support.write_json(request_path, request)
                capsule = producer_panel.prepare_professional_review_capsule_v3(
                    packet=packet,
                    packet_sha256="a" * 64,
                    discovery_capsule_path=discovery_path,
                    candidate_request_path=request_path,
                    voter_id=voter_id,
                    created_on="2026-07-17",
                    validation_root=validation_root,
                    validate_packet_plan=False,
                    packet_state=state,
                )
                capsule_path = round_root / "capsules" / f"{voter_id}.json"
                capsule_path.parent.mkdir(parents=True, exist_ok=True)
                source_support.write_json(capsule_path, capsule)
                blocks = (
                    REGRESSION.expert_panel._professional_v3_effective_capsule_input_blocks(
                        discovery_capsule=discovery,
                        candidate_request=request,
                        capsule=capsule,
                    )
                )
                REGRESSION._professional_review_cost_add_blocks(
                    blocks,
                    sizes=block_sizes,
                    occurrences=block_occurrences,
                    label="synthetic canonical capsule input blocks",
                )
                voters.append(
                    {
                        "capsule": {
                            "path": capsule_path.relative_to(
                                validation_root
                            ).as_posix(),
                            "sha256": hashlib.sha256(
                                capsule_path.read_bytes()
                            ).hexdigest(),
                            "kind": producer_panel.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                            "axis": producer_panel.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                            "review_id": packet["review_id"],
                        },
                        "capsule_input_blocks_proxy": blocks,
                    }
                )

            actual_bytes = REGRESSION._professional_review_charged_bytes(
                sizes=block_sizes,
                occurrences=block_occurrences,
            )
            full_bytes = producer_panel.PANEL_SIZE * sum(
                block["canonical_json_bytes_proxy"]
                for block in producer_panel._professional_v3_full_rereview_input_blocks(
                    packet
                )
            )
            rows = [
                {
                    "skill_id": skill_id,
                    "provenance": {
                        "mode": "fresh" if skill_id in fresh_set else "carried-forward",
                        "origin_depth": 0 if skill_id in fresh_set else 1,
                    },
                }
                for skill_id in all_skill_ids
            ]
            packet["review_plan"]["plan_lineage_depth"] = 8
            record = {
                "voters": voters,
                "professional_decisions": rows,
                "summary": {
                    "review_cost": {
                        "fresh_vote_count": 3 * len(fresh_ids),
                        "avoided_vote_count": 3 * (189 - len(fresh_ids)),
                        "fresh_criterion_result_count": 30 * len(fresh_ids),
                        "carried_criterion_result_count": 30
                        * (189 - len(fresh_ids)),
                        "effective_criterion_result_count": 5670,
                        "avoided_criterion_result_count": 30
                        * (189 - len(fresh_ids)),
                        "canonical_capsule_input_bytes_proxy": actual_bytes,
                        "full_rereview_deduplicated_capsule_input_bytes_proxy": full_bytes,
                        "input_ratio_ppm": actual_bytes * 1_000_000 // full_bytes,
                        "maximum_origin_depth": 1,
                    }
                },
            }
            with mock.patch.object(REGRESSION, "ROOT", validation_root):
                cost = REGRESSION._professional_schema3_review_cost(
                    record,
                    packet=packet,
                )

            formal_policy, _fingerprint = (
                REGRESSION._professional_review_formal_round_policy()
            )
            metadata_ratio_limit = formal_policy[
                "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ]
            required_source_bytes = 100
            actual_source_bytes = 100
            boundary_required_metadata_bytes = 1_000_000
            self.assertEqual(
                0,
                boundary_required_metadata_bytes
                * metadata_ratio_limit
                % 1_000_000,
            )
            boundary_overhead_bytes = (
                boundary_required_metadata_bytes
                * metadata_ratio_limit
                // 1_000_000
            )
            floor_collision_required_metadata_bytes = (
                boundary_required_metadata_bytes + 1
            )
            floor_collision_overhead_bytes = boundary_overhead_bytes + 1
            boundary_cases = (
                (
                    "exact-boundary",
                    boundary_required_metadata_bytes,
                    boundary_overhead_bytes,
                    "incremental-reduced-input",
                ),
                (
                    "one-byte-over",
                    boundary_required_metadata_bytes,
                    boundary_overhead_bytes + 1,
                    "reviewer-added-metadata-overhead-exceeded",
                ),
                (
                    "floor-collision",
                    floor_collision_required_metadata_bytes,
                    floor_collision_overhead_bytes,
                    "reviewer-added-metadata-overhead-exceeded",
                ),
            )
            self.assertGreater(
                full_bytes,
                actual_source_bytes
                + floor_collision_required_metadata_bytes
                + floor_collision_overhead_bytes,
            )
            producer_boundary_costs = {}
            for (
                label,
                required_metadata_bytes,
                metadata_overhead_bytes,
                expected_status,
            ) in boundary_cases:
                required_bytes = required_source_bytes + required_metadata_bytes
                controlled_actual_bytes = (
                    actual_source_bytes
                    + required_metadata_bytes
                    + metadata_overhead_bytes
                )
                controlled_record = copy.deepcopy(record)
                controlled_core_cost = controlled_record["summary"]["review_cost"]
                controlled_core_cost[
                    "canonical_capsule_input_bytes_proxy"
                ] = controlled_actual_bytes
                controlled_core_cost["input_ratio_ppm"] = (
                    controlled_actual_bytes * 1_000_000 // full_bytes
                )

                # The canonical chain and block manifests above remain real. Patch
                # only the producer's four aggregate byte totals, in call order,
                # so each exact byte boundary is deterministic across JSON changes.
                with (
                    mock.patch.object(REGRESSION, "ROOT", validation_root),
                    mock.patch.object(
                        REGRESSION,
                        "_professional_review_charged_bytes",
                        side_effect=(
                            controlled_actual_bytes,
                            required_bytes,
                            actual_source_bytes,
                            required_source_bytes,
                        ),
                    ) as charged_bytes,
                ):
                    boundary_cost = REGRESSION._professional_schema3_review_cost(
                        controlled_record,
                        packet=packet,
                    )
                self.assertEqual(4, charged_bytes.call_count, label)
                self.assertTrue(
                    all(
                        call.kwargs["sizes"] and call.kwargs["occurrences"]
                        for call in charged_bytes.call_args_list
                    ),
                    label,
                )
                self.assertEqual(expected_status, boundary_cost["policy_status"], label)
                self.assertEqual(
                    metadata_overhead_bytes,
                    boundary_cost[
                        "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy"
                    ],
                    label,
                )
                producer_boundary_costs[label] = boundary_cost

        self.assertEqual("incremental-reduced-input", cost["policy_status"])
        self.assertEqual(8, cost["plan_lineage_depth"])
        self.assertEqual(3, cost["reviewer_added_request_count"])
        self.assertEqual(1, cost["reviewer_added_unique_relationship_count"])
        self.assertLess(
            cost["required_only_capsule_input_bytes_proxy"],
            cost["full_rereview_deduplicated_capsule_input_bytes_proxy"],
        )
        self.assertGreaterEqual(
            cost["source_material_input_bytes_proxy"],
            cost["required_only_source_material_input_bytes_proxy"],
        )
        self.assertTrue(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=len(fresh_ids),
                carried_forward_target_count=189 - len(fresh_ids),
            )
        )
        self.assertEqual(
            metadata_ratio_limit,
            producer_boundary_costs["exact-boundary"][
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ],
        )
        self.assertEqual(
            metadata_ratio_limit,
            producer_boundary_costs["floor-collision"][
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ],
        )
        self.assertGreater(
            floor_collision_overhead_bytes * 1_000_000,
            metadata_ratio_limit * floor_collision_required_metadata_bytes,
        )

    def test_split_review_cost_policy_rejects_forged_or_over_budget_claims(
        self,
    ) -> None:
        def incomplete_source(cost: dict) -> None:
            cost["required_only_source_material_input_bytes_proxy"] = 199
            cost["source_material_input_bytes_proxy"] = 199
            cost["source_material_coverage_ratio_ppm"] = 995_000
            cost[
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ] = 10 * 1_000_000 // 801

        def metadata_over_budget(cost: dict) -> None:
            cost["canonical_capsule_input_bytes_proxy"] = 1041
            cost["input_ratio_ppm"] = 1_041_000
            cost[
                "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy"
            ] = 41
            cost[
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ] = 51_250

        mutations = {
            "forged-raw-ratio": lambda cost: cost.__setitem__(
                "input_ratio_ppm", 1_000_000
            ),
            "forged-required-ratio": lambda cost: cost.__setitem__(
                "required_only_input_ratio_ppm", 999_999
            ),
            "incomplete-source-coverage": incomplete_source,
            "forged-metadata-overhead": lambda cost: cost.__setitem__(
                "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy",
                9,
            ),
            "metadata-over-budget": metadata_over_budget,
            "reviewer-added-union-over-budget": lambda cost: cost.__setitem__(
                "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
                1_000_001,
            ),
            "request-multiplicity-over-budget": lambda cost: cost.__setitem__(
                "reviewer_added_request_count", 4
            ),
            "wrong-policy-fingerprint": lambda cost: cost.__setitem__(
                "formal_round_policy_fingerprint", "0" * 64
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                cost = _full_fresh_review_cost()
                mutate(cost)
                self.assertFalse(
                    REGRESSION._professional_review_cost_policy_satisfied(
                        cost,
                        fresh_target_count=189,
                        carried_forward_target_count=0,
                    )
                )

    def test_schema3_round_topology_blocks_fork_orphan_cycle_and_old_selection(self) -> None:
        root_round = "evals/expert-panel/r1/panel/decision.json"
        head_round = "evals/expert-panel/r2/panel/decision.json"
        third_round = "evals/expert-panel/r3/panel/decision.json"
        valid = REGRESSION._professional_schema3_round_topology(
            round_paths={root_round, head_round},
            baseline_by_child={root_round: None, head_round: root_round},
            current_relative=head_round,
        )
        self.assertEqual("schema3-head-current", valid["status"])
        old = REGRESSION._professional_schema3_round_topology(
            round_paths={root_round, head_round},
            baseline_by_child={root_round: None, head_round: root_round},
            current_relative=root_round,
        )
        self.assertEqual("schema3-head-not-selected", old["status"])
        self.assertFalse(old["current_decision_is_head"])

        cases = {
            "missing predecessor": (
                {head_round},
                {head_round: root_round},
                "missing predecessor",
            ),
            "fork": (
                {root_round, head_round, third_round},
                {
                    root_round: None,
                    head_round: root_round,
                    third_round: root_round,
                },
                "forks at",
            ),
            "orphan": (
                {root_round, head_round},
                {root_round: None, head_round: None},
                "exactly one current head",
            ),
            "cycle": (
                {root_round, head_round},
                {root_round: head_round, head_round: root_round},
                "contains a cycle",
            ),
        }
        for label, (rounds, baselines, marker) in cases.items():
            with self.subTest(label=label):
                result = REGRESSION._professional_schema3_round_topology(
                    round_paths=rounds,
                    baseline_by_child=baselines,
                    current_relative=head_round,
                )
                self.assertEqual(
                    "schema3-round-lifecycle-invalid", result["status"]
                )
                self.assertTrue(
                    any(marker in error for error in result["errors"]),
                    result,
                )

    def test_schema3_storage_closure_checks_current_and_direct_origin_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            directory = Path(raw)

            def artifact(
                name: str, value: dict | None = None
            ) -> dict[str, str]:
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                _write(path, value or {})
                return {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }

            current_discovery = artifact(
                "current/discovery.json",
                {
                    "kind": PANEL.PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
                    "voter_id": "current-voter",
                },
            )
            current_request = artifact(
                "current/request.json",
                {
                    "kind": PANEL.PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND,
                    "voter_id": "current-voter",
                    "discovery_capsule": current_discovery,
                },
            )
            current_capsule = artifact(
                "current/capsule.json",
                {
                    "kind": PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                    "voter_id": "current-voter",
                    "candidate_request": current_request,
                    "discovery_capsule": current_discovery,
                },
            )
            current_evidence = [
                artifact("current/decision.json"),
                artifact("current/packet.json"),
                artifact("current/ballot.json"),
                current_capsule,
                current_request,
                current_discovery,
            ]
            origin_packet = artifact("origin/packet.json")
            origin_rows = []
            origin_ballots = []
            origin_capsules = []
            origin_requests = []
            origin_discoveries = []
            for voter in range(3):
                ballot = artifact(f"origin/ballot-{voter}.json")
                voter_id = f"voter-{voter}"
                discovery = artifact(
                    f"origin/discovery-{voter}.json",
                    {
                        "kind": PANEL.PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
                        "voter_id": voter_id,
                    },
                )
                request = artifact(
                    f"origin/request-{voter}.json",
                    {
                        "kind": PANEL.PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND,
                        "voter_id": voter_id,
                        "discovery_capsule": discovery,
                    },
                )
                capsule = artifact(
                    f"origin/capsule-{voter}.json",
                    {
                        "kind": PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                        "voter_id": voter_id,
                        "candidate_request": request,
                        "discovery_capsule": discovery,
                    },
                )
                origin_ballots.append(ballot)
                origin_capsules.append(capsule)
                origin_requests.append(request)
                origin_discoveries.append(discovery)
                origin_rows.append(
                    {
                        "voter_id": voter_id,
                        "ballot": ballot,
                        "capsule": capsule,
                    }
                )
            origin_decision_path = directory / "origin/decision.json"
            origin_decision = {
                "packet": origin_packet,
                "professional_decisions": [
                    {
                        "skill_id": "fixture-skill",
                        "provenance": {
                            "mode": "fresh",
                            "origin_depth": 0,
                            "evidence": origin_rows,
                        },
                    }
                ],
            }
            _write(origin_decision_path, origin_decision)
            origin_decision_ref = {
                "path": origin_decision_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(
                    origin_decision_path.read_bytes()
                ).hexdigest(),
            }
            record = {
                "professional_decisions": [
                    {
                        "skill_id": "fixture-skill",
                        "provenance": {
                            "mode": "carried-forward",
                            "origin_decision": origin_decision_ref,
                        },
                    }
                ]
            }
            evidence = REGRESSION._professional_schema3_storage_evidence(
                record, evidence=current_evidence
            )
            paths = {item["path"] for item in evidence}
            expected_paths = {
                item["path"]
                for item in [
                    *current_evidence,
                    origin_decision_ref,
                    origin_packet,
                    *origin_ballots,
                    *origin_capsules,
                    *origin_requests,
                    *origin_discoveries,
                ]
            }
            self.assertEqual(expected_paths, paths)

            legacy_capsule = artifact(
                "legacy/capsule.json",
                {
                    "kind": PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                    "voter_id": "legacy-voter",
                },
            )
            with self.assertRaisesRegex(
                ValueError, "regenerate a full-fresh round"
            ):
                REGRESSION._professional_schema3_capsule_chain_evidence(
                    legacy_capsule,
                    label="legacy schema-3 fixture",
                )

            representative_targets = [
                current_evidence[-1]["path"],
                origin_decision_ref["path"],
                origin_packet["path"],
                origin_ballots[0]["path"],
                origin_capsules[0]["path"],
                origin_requests[0]["path"],
                origin_discoveries[0]["path"],
            ]
            for target in representative_targets:
                with self.subTest(target=target):
                    def validate(item: dict[str, str]) -> None:
                        if item["path"] == target:
                            raise ValueError("fixture evidence is not checked in")

                    with mock.patch.object(
                        REGRESSION, "_require_default_release_review_config"
                    ), mock.patch.object(
                        REGRESSION,
                        "_validate_expert_evidence",
                        side_effect=validate,
                    ):
                        current, error = REGRESSION._dual_storage_status(
                            REGRESSION.DEFAULT_RELEASE_REVIEW_CONFIG,
                            config_bytes=b"fixture\n",
                            evidence=evidence,
                        )
                    self.assertFalse(current)
                    self.assertIn("not checked in", error)

    def test_release_gate_blocks_readability_tracked_tightening(self) -> None:
        reviews = self._formal_reviews()
        reviews["readability"].update(
            {
                "accepted_for_formal": False,
                "attestation_status": "panel-majority-tracked-tightening",
                "tracked_tightening_count": 1,
            }
        )
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["readability-review-release-gate"],
            [item.category for item in blockers],
        )

    def test_release_gate_blocks_unresolved_actionability_detector_false_positive(
        self,
    ) -> None:
        reviews = self._formal_reviews()
        reviews["readability"].update(
            {
                "accepted_for_formal": False,
                "attestation_status": "panel-majority-detector-update-required",
                "detector_false_positive_count": 1,
            }
        )
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["readability-review-release-gate"],
            [item.category for item in blockers],
        )
        self.assertIn("detector_false_positive_count=1", blockers[0].message)

    def test_release_gate_blocks_professional_correction(self) -> None:
        reviews = self._formal_reviews()
        reviews["professional_completeness"].update(
            {
                "accepted_for_formal": False,
                "attestation_status": "panel-majority-corrections-required",
                "accepted_current_count": PANEL.PROFESSIONAL_PACKAGE_COUNT - 1,
                "correction_count": 1,
            }
        )
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["professional-completeness-review-release-gate"],
            [item.category for item in blockers],
        )

    def test_release_gate_blocks_unresolved_domain_critical_disagreement(self) -> None:
        reviews = self._formal_reviews()
        reviews["professional_completeness"].update(
            {
                "accepted_for_formal": False,
                "attestation_status": "panel-domain-disagreement-unresolved",
                "accepted_current_count": PANEL.PROFESSIONAL_PACKAGE_COUNT - 1,
                "unresolved_professional_disagreement_count": 1,
            }
        )
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["professional-completeness-review-release-gate"],
            [item.category for item in blockers],
        )
        self.assertIn(
            "unresolved_professional_disagreement_count=1",
            blockers[0].message,
        )

    def test_legacy_professional_majority_method_cannot_satisfy_formal(self) -> None:
        reviews = self._formal_reviews()
        reviews["professional_completeness"]["decision_method"] = (
            PANEL.DECISION_METHOD
        )
        reviews["professional_completeness"]["panel_artifact_schema_version"] = 1
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["professional-completeness-review-release-gate"],
            [item.category for item in blockers],
        )

    def test_release_gate_rejects_noncanonical_required_adjacency_count(
        self,
    ) -> None:
        reviews = self._formal_reviews()
        evidence = reviews["professional_completeness"]["evidence_summary"]
        evidence["examined_required_adjacency_count"] -= 1
        evidence["examined_adjacency_count"] -= 1

        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )

        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["professional-completeness-review-release-gate"],
            [item.category for item in blockers],
        )

    def test_release_gate_rejects_cross_axis_substitution(self) -> None:
        reviews = self._formal_reviews()
        reviews["readability"], reviews["professional_completeness"] = (
            reviews["professional_completeness"],
            reviews["readability"],
        )
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            reviews,
            {},
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            {
                "readability-review-release-gate",
                "professional-completeness-review-release-gate",
            },
            {item.category for item in blockers},
        )

    def test_schema_two_professional_decision_is_auditable_but_nonformal(self) -> None:
        packet = PANEL.prepare_professional_completeness_packet(
            review_id="professional-parser-fixture",
            created_on="2026-07-16",
            root=ROOT,
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write(packet_path, packet)
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter in range(1, 4):
                ballot_path = root / f"professional-expert-{voter}.json"
                ballot = _professional_ballot(packet, packet_sha, voter)
                _write(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            decision = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )
            decision_path = root / "decision.json"
            _write(decision_path, decision)
            selector_free = self._dual_config()[
                "professional_completeness_review_attestation"
            ]
            REGRESSION._validated_professional_config(
                root / "review.yaml", selector_free
            )
            result = PANEL.validate_decision_record(
                decision,
                record_path=decision_path,
                validation_mode=PANEL.VALIDATION_MODE_HISTORICAL,
            )

        self.assertEqual(2, result["schema_version"])
        self.assertEqual(
            PANEL.PROFESSIONAL_PACKAGE_COUNT,
            len(result["professional_decisions"]),
        )
        self.assertEqual(
            0,
            result["summary"]["professional_completeness"][
                "requires-professional-correction"
            ],
        )
        self.assertEqual(
            ["all-professional-criteria-satisfied"],
            sorted(
                {
                    row["reason_code"]
                    for row in result["professional_decisions"][0][
                        "winning_rationales"
                    ]
                }
            ),
        )
        self.assertEqual(
            "accepted-current-professional-completeness",
            result["professional_decisions"][0][
                "ordinary_criterion_disposition"
            ],
        )
        self.assertEqual(
            [],
            result["professional_decisions"][0][
                "ordinary_criterion_defects"
            ],
        )
        self.assertFalse(
            REGRESSION._professional_completeness_review_formal_ready(
                {
                    "panel_artifact_schema_version": result["schema_version"],
                    "accepted_for_formal": False,
                }
            )
        )

    def test_panel_decision_is_applied_but_pending_until_checked_in(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            config_path, _record_path, _ballots, packet = self._fixture(Path(raw))
            with mock.patch.object(
                REGRESSION,
                "load_yaml_file",
                return_value=json.loads(config_path.read_text(encoding="utf-8")),
            ):
                result = REGRESSION._expert_content_review(
                    config_path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    content_skills=[
                        {
                            "path": "src/foundation/capabilities/a/SKILL.md",
                            "classification": "REVIEW_DENSITY",
                        }
                    ],
                    readability_content={
                        "summary": {
                            "advisory_documents": 1,
                            "blocker_findings": 0,
                        },
                        "documents": [
                            {
                                "document_id": (
                                    "src/foundation/capabilities/a/SKILL.md#body"
                                ),
                                "highest_advisory_band": "review-as-complex",
                            }
                        ],
                    },
                    evaluation_date=date(2026, 7, 16),
                )
            self.assertTrue(result["panel_decision_complete"])
            self.assertFalse(result["expert_content_review_complete"])
            self.assertFalse(result["storage_current"])
            self.assertEqual("panel-majority-pending-checkin", result["attestation_status"])
            self.assertEqual(1, result["applied_readability_disposition_count"])

    def test_checked_in_panel_becomes_formal_authority_without_maintainer_vote(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            config_path, _record_path, _ballots, packet = self._fixture(Path(raw))
            with mock.patch.object(
                REGRESSION.expert_panel,
                "prepare_packet",
                return_value=packet,
            ), mock.patch.object(
                REGRESSION,
                "load_yaml_file",
                return_value=json.loads(config_path.read_text(encoding="utf-8")),
            ), mock.patch.object(
                REGRESSION, "_require_default_release_review_config"
            ), mock.patch.object(REGRESSION, "_validate_expert_evidence"):
                result = REGRESSION._expert_content_review(
                    config_path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    content_skills=[
                        {
                            "path": "src/foundation/capabilities/a/SKILL.md",
                            "classification": "REVIEW_DENSITY",
                        }
                    ],
                    readability_content={
                        "summary": {
                            "advisory_documents": 1,
                            "blocker_findings": 0,
                        },
                        "documents": [
                            {
                                "document_id": (
                                    "src/foundation/capabilities/a/SKILL.md#body"
                                ),
                                "highest_advisory_band": "review-as-complex",
                            }
                        ],
                    },
                    evaluation_date=date(2026, 7, 16),
                )
            self.assertTrue(result["expert_content_review_complete"])
            self.assertTrue(result["storage_current"])
            self.assertEqual("panel-majority-current", result["attestation_status"])
            self.assertEqual("expert-panel:fixture-panel", result["attested_by"])

    def test_ballot_tamper_breaks_panel_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            config_path, _record_path, ballots, packet = self._fixture(Path(raw))
            ballots[0].write_text("{}\n", encoding="utf-8")
            with mock.patch.object(
                REGRESSION.expert_panel,
                "prepare_packet",
                return_value=packet,
            ), mock.patch.object(
                REGRESSION,
                "load_yaml_file",
                return_value=json.loads(config_path.read_text(encoding="utf-8")),
            ), self.assertRaisesRegex(ValueError, "ballot sha256 is stale"):
                REGRESSION._expert_content_review(
                    config_path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    content_skills=[
                        {
                            "path": "src/foundation/capabilities/a/SKILL.md",
                            "classification": "REVIEW_DENSITY",
                        }
                    ],
                    readability_content={
                        "summary": {
                            "advisory_documents": 1,
                            "blocker_findings": 0,
                        },
                        "documents": [
                            {
                                "document_id": (
                                    "src/foundation/capabilities/a/SKILL.md#body"
                                ),
                                "highest_advisory_band": "review-as-complex",
                            }
                        ],
                    },
                    evaluation_date=date(2026, 7, 16),
                )


if __name__ == "__main__":
    unittest.main()
