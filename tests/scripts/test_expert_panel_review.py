from __future__ import annotations

import copy
import functools
import hashlib
import json
import re
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_completeness_test_support as professional_support
from . import readability_review_test_support as readability_support

ROOT = Path(__file__).resolve().parents[2]
PANEL = source_support.PANEL
AUDIT = source_support.AUDIT
_load_module = source_support.load_panel
_live_semantic_audit = source_support.live_semantic_audit
_semantic_audit_with_synthetic_delta = (
    source_support.semantic_audit_with_synthetic_delta
)
_write_json = source_support.write_json
_synthetic_schema1_professional_decision = (
    professional_support._synthetic_schema1_professional_decision
)
_current_schema2_readability_packet_fixture = readability_support.current_packet
_synthetic_historical_schema2_readability_decision = (
    readability_support.historical_decision
)
_synthetic_schema3_professional_decision = (
    professional_support._synthetic_schema3_professional_decision
)
_professional_packet = professional_support._professional_packet
_professional_ballot = professional_support._professional_ballot
_fixture_evidence_lines = professional_support._fixture_evidence_lines
_fixture_anchor = professional_support._fixture_anchor
_fixture_anchor_tokens = professional_support._fixture_anchor_tokens


















def _packet() -> dict:
    return {
        "schema_version": 1,
        "kind": PANEL.PACKET_KIND,
        "review_id": "review-1",
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




def _ballot(
    packet: dict,
    packet_sha256: str,
    *,
    voter: int,
    readability_decision: str = "accepted-current-readability",
) -> dict:
    readability_reason = (
        "single-indivisible-decision"
        if readability_decision == "accepted-current-readability"
        else "multiple-independent-actions"
    )
    return {
        "schema_version": 1,
        "kind": PANEL.BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": "2026-07-16",
        "packet_sha256": packet_sha256,
        "source_fingerprints": packet["source_fingerprints"],
        "voter": {
            "voter_id": f"expert-{voter}",
            "agent_id": f"agent-{voter}",
            "role": f"role-{voter}",
            "expertise": ["skill review"],
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
                "decision": readability_decision,
                "reason_code": readability_reason,
                "rationale": "This expert independently selected one mandatory disposition for review.",
            }
        ],
        "limitations": ["Static fixture vote."],
    }














@functools.lru_cache(maxsize=1)
def _phase1_professional_targets_cached() -> list[dict]:
    return PANEL._professional_package_targets(root=ROOT)


def _phase1_professional_targets() -> list[dict]:
    return copy.deepcopy(_phase1_professional_targets_cached())


def _professional_domain_expertise_tags(packet: dict) -> list[str]:
    return sorted(
        {
            tag
            for target in packet["professional_targets"]
            for tag in target["required_expertise_tags"]
        }
    )










def _add_reviewer_added_candidate(
    packet: dict,
    ballot: dict,
    *,
    vote_index: int | None = None,
) -> tuple[int, str]:
    """Add one source-bound full-catalog candidate outside the required set."""

    targets_by_id = {
        target["skill_id"]: target for target in packet["professional_targets"]
    }
    candidate_vote_indexes = (
        [vote_index]
        if vote_index is not None
        else list(range(len(ballot["professional_votes"])))
    )
    selected: tuple[int, dict, dict] | None = None
    for index in candidate_vote_indexes:
        vote = ballot["professional_votes"][index]
        target = targets_by_id[vote["skill_id"]]
        reviewed = {
            row["skill_id"] for row in vote["examined_adjacent_candidates"]
        }
        ranking_item = next(
            (
                row
                for row in target["routing_adjacency"]["full_catalog_ranking"]
                if row["skill_id"] not in reviewed
            ),
            None,
        )
        if ranking_item is not None:
            selected = (index, target, ranking_item)
            break
    if selected is None:
        raise AssertionError("fixture needs one non-required full-catalog candidate")

    index, target, ranking_item = selected
    vote = ballot["professional_votes"][index]
    candidate_id = ranking_item["skill_id"]
    candidate_target = targets_by_id[candidate_id]
    candidate_line, _tokens = _fixture_evidence_lines(candidate_target["root"], 1)[0]
    candidate_anchor_id = "reviewer-added-000"
    if any(
        anchor["anchor_id"] == candidate_anchor_id
        for anchor in vote["evidence_anchors"]
    ):
        raise AssertionError("reviewer-added fixture anchor already exists")
    candidate_anchor = _fixture_anchor(
        skill_id=candidate_id,
        material=candidate_target["root"],
        anchor_id=candidate_anchor_id,
        line_number=candidate_line,
    )
    vote["evidence_anchors"].append(candidate_anchor)
    vote["evidence_anchors"].sort(key=lambda row: row["anchor_id"])
    anchors_by_id = {
        anchor["anchor_id"]: anchor for anchor in vote["evidence_anchors"]
    }
    target_anchor_id = vote["criteria"]["adjacent-overlap-or-gap"][
        "evidence_assertions"
    ][0]["evidence_anchor_ids"][0]
    materials_by_skill = PANEL._professional_materials_by_skill(packet)
    target_tokens = _fixture_anchor_tokens(
        anchors_by_id[target_anchor_id], materials_by_skill
    )
    candidate_tokens = _fixture_anchor_tokens(
        anchors_by_id[candidate_anchor_id], materials_by_skill
    )
    vote["examined_adjacent_candidates"].append(
        {
            "skill_id": candidate_id,
            "review_origin": "reviewer-added",
            "discovery_reason": (
                "Reviewer independently discovered a plausible boundary relationship "
                "outside the required selection."
            ),
            "disposition": "not-adjacent",
            "target_anchor_ids": [target_anchor_id],
            "candidate_anchor_ids": [candidate_anchor_id],
            "rationale": (
                f"The {target_tokens[0]} target boundary and "
                f"{candidate_tokens[0]} candidate boundary were compared after "
                "independent catalog discovery."
            ),
        }
    )
    vote["examined_adjacent_candidates"].sort(key=lambda row: row["skill_id"])
    return index, candidate_id


def _semantic_packet() -> dict:
    return PANEL.prepare_semantic_disposition_packet(
        audit=_semantic_audit_with_synthetic_delta(),
        review_id="semantic-review-1",
        created_on="2026-07-16",
    )


def _historical_schema1_semantic_selector() -> dict:
    """Return the immutable historical selector admitted by the v1 bridge."""

    return {
        "schema_version": 1,
        "kind": PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND,
        "axis": PANEL.SEMANTIC_DISPOSITION_PANEL_KIND,
        "review_id": "semantic-015be10a-final-prep",
        "decided_on": "2026-08-11",
        "source_fingerprints": {
            "reference_candidate_manifest": (
                "dd03e7b80fe661d9db293db3d725706cd44a43ef7820de90452e22120e67638b"
            ),
            "reference_detector_contract": (
                "bb6182108495b202f41d3ca0d73cabe8e62f7433b54fe233d61fc4dcb7d4c06e"
            ),
            "root_candidate_manifest": (
                "8af1bbe28abcec952f7e52704f377324778002e2343a108fa3e2d0533ec7c919"
            ),
            "root_detector_contract": (
                "1ed220a953b74fd6d4e4594660999b53064177c885841ca744ca1dd06caf146d"
            ),
        },
        "review_contract_fingerprint": (
            "6f9618afabdc84a4e39a6cfe30b24b4b7b22f431f4d77a6337923af82f43069e"
        ),
        "target_count": 197,
        "axis_counts": {"reference": 121, "root": 76},
    }


@contextmanager
def _current_semantic_application_fixture(
    audit: dict,
    *,
    winner_overrides: dict[str, str] | None = None,
):
    """Create one real, current semantic application in an isolated review root."""

    review_id = "semantic-current-application-fixture"
    overrides = winner_overrides or {}
    for axis in sorted(PANEL.SEMANTIC_AXES):
        semantic = audit[f"{axis}_content"]["semantic_advisories"]
        candidates_by_id = {
            candidate["candidate_id"]: candidate
            for candidate in semantic["candidates"]
        }
        exact_entries = [
            entry
            for entry in semantic["disposition_contract"]["entries"]
            if entry["candidate_id"] in candidates_by_id
            and not PANEL._semantic_entry_mismatches(
                axis=axis,
                candidate=candidates_by_id[entry["candidate_id"]],
                entry=entry,
            )
        ]
        semantic["disposition_contract"]["entries"] = exact_entries
        covered_ids = {
            entry["candidate_id"] for entry in exact_entries
        }
        semantic["candidates"] = [
            candidate
            for candidate in semantic["candidates"]
            if candidate["candidate_id"] in covered_ids
        ]
    review_audit = PANEL._semantic_audit_for_axis_rereview(
        copy.deepcopy(audit), sorted(PANEL.SEMANTIC_AXES)
    )
    packet = PANEL.prepare_semantic_disposition_packet(
        audit=review_audit,
        review_id=review_id,
        created_on="2026-07-23",
    )
    entries_by_axis = {}
    for axis in sorted(PANEL.SEMANTIC_AXES):
        semantic = audit[f"{axis}_content"]["semantic_advisories"]
        entries_by_axis[axis] = {
            entry["candidate_id"]: entry
            for entry in semantic["disposition_contract"]["entries"]
        }
    winners = {}
    for target in packet["semantic_targets"]:
        target_id = target["target_id"]
        candidate_id = target["candidate"]["candidate_id"]
        entry = entries_by_axis[target["axis"]].get(candidate_id)
        if entry is None:
            raise AssertionError(f"current semantic entry is missing: {target_id}")
        winners[target_id] = overrides.get(target_id, entry["disposition"])
        if winners[target_id] not in PANEL.SEMANTIC_DISPOSITIONS:
            raise AssertionError(
                f"semantic fixture winner is invalid: {target_id}={winners[target_id]}"
            )

    with tempfile.TemporaryDirectory() as raw:
        validation_root = Path(raw)
        review_root = validation_root / "evals" / "expert-panel" / review_id
        panel_root = review_root / "panel"
        panel_root.mkdir(parents=True)
        packet_path = review_root / "packet.json"
        _write_json(packet_path, packet)
        packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()

        ballot_values = []
        for voter in range(1, PANEL.PANEL_SIZE + 1):
            ballot = PANEL.prepare_semantic_ballot_template(
                packet=packet,
                packet_sha256=packet_sha256,
                voter_id=f"semantic-fixture-voter-{voter}",
                agent_id=f"semantic-fixture-agent-{voter}",
                role=f"semantic-fixture-role-{voter}",
                expertise=["semantic disposition governance"],
                created_on="2026-07-23",
            )
            for vote in ballot["semantic_votes"]:
                winner = winners[vote["target_id"]]
                vote.update(
                    {
                        "disposition": winner,
                        "rationale": (
                            f"Reviewer {voter} independently evaluated the complete "
                            f"current evidence for {vote['target_id']}."
                        ),
                        "authority_or_condition": (
                            "The current bounded candidate evidence and authority apply."
                        ),
                        "decision_owner": f"semantic-fixture-owner-{voter}",
                        "mitigation": (
                            "Repeat the review when detector or source evidence changes."
                        ),
                        "review_after": (
                            "2099-12-31"
                            if winner == "time-bounded-exception"
                            else None
                        ),
                    }
                )
            ballot_path = panel_root / f"ballot-{voter}.json"
            _write_json(ballot_path, ballot)
            ballot_values.append((ballot_path, ballot))

        with mock.patch.object(PANEL, "ROOT", validation_root), mock.patch.dict(
            sys.modules, {"expert_panel_review": PANEL}
        ):
            decision = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-23",
            )
            decision_path = panel_root / "decision.json"
            _write_json(decision_path, decision)
            compact = PANEL._semantic_attestation_from_decision(
                decision,
                decision_path=decision_path,
                audit=audit,
            )
            fixed = (
                validation_root
                / PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
            )
            fixed.parent.mkdir(parents=True, exist_ok=True)
            fixed.write_bytes(
                PANEL.panel_attestation.canonical_attestation_bytes(
                    compact,
                    expected_path=(
                        PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
                    ),
                    expected_review_contract_fingerprint=(
                        PANEL._canonical_json_sha256(packet["panel_contract"])
                    ),
                    expected_semantic_current_bindings=(
                        PANEL._semantic_candidate_authorities(packet)
                    ),
                )
            )
            yield {
                "attestation": compact,
                "decision": decision,
                "packet": packet,
                "root": validation_root,
            }


def _semantic_ballot(
    packet: dict,
    packet_sha256: str,
    *,
    voter: int,
    disposition: str = "valid-contextual-rule",
) -> dict:
    ballot = PANEL.prepare_semantic_ballot_template(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=f"semantic-expert-{voter}",
        agent_id=f"semantic-agent-{voter}",
        role=f"senior-semantic-role-{voter}",
        expertise=["semantic disposition governance"],
        created_on="2026-07-16",
    )
    for index, vote in enumerate(ballot["semantic_votes"]):
        vote.update(
            {
                "disposition": disposition,
                "rationale": (
                    f"Reviewer {voter} independently evaluated complete current evidence "
                    f"for semantic target {index}."
                ),
                "authority_or_condition": (
                    "The current bounded candidate context and authority are in scope."
                ),
                "decision_owner": f"semantic-owner-{voter}",
                "mitigation": (
                    "Re-evaluate when bound source or detector evidence changes."
                ),
                "review_after": None,
            }
        )
    return ballot


class ExpertPanelReviewTests(unittest.TestCase):
    def test_professional_attest_requires_one_clean_stable_projection_head(
        self,
    ) -> None:
        review_id = "professional-origin-projection-head"
        decision_path = PANEL._ephemeral_review_path(
            review_id, "panel", "decision.json"
        )
        output_path = PANEL._ephemeral_review_path(
            review_id, "attestation.json"
        )
        args = mock.Mock(
            decision=str(decision_path),
            review_id=review_id,
            panel_kind=PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
            audit=None,
            out=str(output_path),
        )
        head_b = "b" * 40
        head_c = "c" * 40

        def projection(origin_commit: str = head_b) -> dict:
            return {
                "findings": [
                    {
                        "provenance": {
                            "mode": "fresh",
                            "origin": {"origin_commit": origin_commit},
                        }
                    }
                ]
            }

        def git_result(stdout: bytes) -> mock.Mock:
            return mock.Mock(stdout=stdout, returncode=0)

        def invoke(
            git_outputs: list[bytes],
            *,
            projected_origin: str = head_b,
            writer: mock.Mock | None = None,
        ) -> mock.Mock:
            payload = b"{}\n"
            writer = mock.Mock() if writer is None else writer
            with mock.patch.object(
                PANEL,
                "_require_same_ephemeral_run_path",
                side_effect=[decision_path, output_path],
            ), mock.patch.object(
                PANEL,
                "_bound_json_object",
                return_value=(mock.sentinel.bound, {"review_id": review_id}),
            ), mock.patch.object(
                PANEL,
                "_professional_attestation_projection_from_decision",
                return_value=(projection(projected_origin), {}),
            ), mock.patch.object(
                PANEL,
                "_decision_packet_and_ballots",
                return_value=(mock.sentinel.packet_path, {}, []),
            ), mock.patch.object(
                PANEL,
                "_professional_attestation_current_bindings",
                return_value={},
            ), mock.patch.object(
                PANEL.panel_attestation,
                "canonical_attestation_bytes",
                return_value=payload,
            ), mock.patch.object(
                PANEL, "_git_output", side_effect=[git_result(row) for row in git_outputs]
            ), mock.patch.object(
                PANEL, "_write_json", writer
            ), mock.patch.object(
                PANEL.reviewer_manifest,
                "read_bound_regular_file",
                return_value=mock.Mock(raw=payload),
            ):
                PANEL._attest(args)
            return writer

        clean_b = [
            head_b.encode("ascii"),
            b"",
            head_b.encode("ascii"),
        ]
        writer = invoke(clean_b + clean_b)
        writer.assert_called_once()

        invalid_cases = (
            (
                "dirty before projection",
                [head_b.encode("ascii"), b" M src/example.py\x00"],
                head_b,
                "clean tree",
            ),
            (
                "dirty after projection",
                clean_b
                + [head_b.encode("ascii"), b"?? unexpected.txt\x00"],
                head_b,
                "clean tree",
            ),
            (
                "head changes while captured",
                [
                    head_b.encode("ascii"),
                    b"",
                    head_c.encode("ascii"),
                ],
                head_b,
                "HEAD changed",
            ),
            (
                "head changes after projection",
                clean_b
                + [
                    head_c.encode("ascii"),
                    b"",
                    head_c.encode("ascii"),
                ],
                head_b,
                "HEAD changed",
            ),
            (
                "fresh origin differs from projection head",
                clean_b + clean_b,
                head_c,
                "origin commit",
            ),
        )
        for label, outputs, projected_origin, error in invalid_cases:
            writer = mock.Mock()
            with self.subTest(label=label), self.assertRaisesRegex(
                PANEL.PanelReviewError, error
            ):
                invoke(
                    outputs,
                    projected_origin=projected_origin,
                    writer=writer,
                )
            writer.assert_not_called()

    def test_current_artifact_version_domains_are_independent(self) -> None:
        self.assertEqual(2, PANEL.READABILITY_SCHEMA_VERSION)
        self.assertEqual(
            3, PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        )
        self.assertEqual(2, PANEL.SEMANTIC_DISPOSITION_SCHEMA_VERSION)

    def test_professional_adjacency_catalog_budget_is_derived_and_fingerprinted(
        self,
    ) -> None:
        self.assertEqual(162, PANEL.PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT)
        self.assertEqual(
            3500,
            PANEL.PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL,
        )
        self.assertEqual(188, PANEL.PROFESSIONAL_PACKAGE_COUNT)
        for target_count, expected in ((188, 4061), (189, 4083), (190, 4104)):
            with self.subTest(target_count=target_count):
                self.assertEqual(
                    expected,
                    PANEL._professional_adjacency_max_required_candidates_total(
                        target_count
                    ),
                )
        for invalid in (-1, True, False, 189.0, "189", None):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "non-negative integer",
                ):
                    PANEL._professional_adjacency_max_required_candidates_total(
                        invalid
                    )

        contract = PANEL._professional_adjacency_selection_contract()
        self.assertEqual(
            {
                "rounding": "floor",
                "baseline_target_count": 162,
                "baseline_maximum_required_candidates_total": 3500,
                "current_target_count": 188,
                "derived_maximum_required_candidates_total": 4061,
            },
            contract["maximum_required_candidates_total_derivation"],
        )
        self.assertEqual(4061, contract["maximum_required_candidates_total"])
        current_fingerprint = PANEL._canonical_json_sha256(
            PANEL._professional_completeness_panel_contract()
        )
        with mock.patch.object(PANEL, "PROFESSIONAL_PACKAGE_COUNT", 180):
            reduced_contract = PANEL._professional_adjacency_selection_contract()
            reduced_fingerprint = PANEL._canonical_json_sha256(
                PANEL._professional_completeness_panel_contract()
            )
        self.assertEqual(3888, reduced_contract["maximum_required_candidates_total"])
        self.assertNotEqual(current_fingerprint, reduced_fingerprint)

        def synthetic_targets(counts: list[int]) -> list[dict]:
            return [
                {
                    "routing_adjacency": {
                        "required_candidates": [{} for _index in range(count)]
                    }
                }
                for count in counts
            ]

        actual_budget = [21] * 101 + [20] * 88
        self.assertEqual(3881, sum(actual_budget))
        PANEL._enforce_professional_adjacency_candidate_budget(
            synthetic_targets(actual_budget)
        )
        PANEL._enforce_professional_adjacency_candidate_budget(
            synthetic_targets([57] + [0] * 188)
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "catalog budget exceeded",
        ):
            PANEL._enforce_professional_adjacency_candidate_budget(
                synthetic_targets([22] * 115 + [21] * 74)
            )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "per-target budget exceeded",
        ):
            PANEL._enforce_professional_adjacency_candidate_budget(
                synthetic_targets([58] + [0] * 188)
            )

    def test_professional_declared_adjacency_is_exact_registry_field_graph(
        self,
    ) -> None:
        with mock.patch.object(
            PANEL,
            "_enforce_professional_adjacency_candidate_budget",
        ) as enforce_budget:
            targets = PANEL._professional_package_targets(root=ROOT)
        enforce_budget.assert_called_once_with(targets)

        targets_by_id = {
            target["skill_id"]: target for target in targets
        }
        provenance: dict[str, dict[str, set[tuple[str, str, str]]]] = {
            skill_id: {} for skill_id in targets_by_id
        }
        groups: dict[str, object] = {}
        domain_declarations: set[tuple[str, str]] = set()
        registry_skill_ids: set[str] = set()
        for layer, relative, collection_key in PANEL.REGISTRY_SOURCES:
            registry = PANEL.load_yaml_file(ROOT / relative)
            for row in registry[collection_key]:
                source_id = row["name"]
                registry_skill_ids.add(source_id)
                groups[source_id] = row.get("group")
                for field in ("layer3_candidates", "used_by"):
                    for adjacent_id in row.get(field, []):
                        source = (source_id, field, adjacent_id)
                        provenance[source_id].setdefault(
                            adjacent_id, set()
                        ).add(source)
                        provenance[adjacent_id].setdefault(
                            source_id, set()
                        ).add(source)
                        if layer == "domain":
                            domain_declarations.add(
                                (source_id, adjacent_id)
                            )
        self.assertEqual(set(targets_by_id), registry_skill_ids)

        actual_graph = {
            target["skill_id"]: set(
                target["routing_adjacency"]["registry_declared_skills"]
            )
            for target in targets
        }
        expected_graph = {
            skill_id: set(neighbors)
            for skill_id, neighbors in provenance.items()
        }
        self.assertEqual(expected_graph, actual_graph)
        self.assertEqual(
            [],
            sorted(
                (source_id, adjacent_id)
                for source_id, neighbors in actual_graph.items()
                for adjacent_id in neighbors
                if not provenance[source_id].get(adjacent_id)
            ),
        )
        self.assertEqual(
            set(),
            {
                (source_id, adjacent_id)
                for source_id, neighbors in actual_graph.items()
                for adjacent_id in neighbors
                if groups[source_id]
                and groups[source_id] == groups[adjacent_id]
                and not provenance[source_id].get(adjacent_id)
            },
        )
        self.assertEqual(
            {
                "ai-code-review-refactor",
                "architecture-impact-reviewer",
                "backend-change-builder",
                "repository-tooling-change-builder",
            },
            actual_graph["implementation-structure-design"],
        )
        self.assertEqual(47, len(domain_declarations))
        self.assertEqual(
            47,
            sum(
                source_id in actual_graph[adjacent_id]
                for source_id, adjacent_id in domain_declarations
            ),
        )

    def test_professional_source_declared_adjacency_covers_reviewed_directional_gaps(
        self,
    ) -> None:
        known_relationships = {
            ("requirement-structuring", "acceptance-standard-definition"),
            ("requirement-structuring", "data-api-contract-changer"),
            ("requirement-structuring", "integration-change-builder"),
            ("requirement-structuring", "performance-budgeting"),
            ("requirement-structuring", "permission-boundary-modeling"),
            ("requirement-structuring", "quality-test-gate"),
            ("requirement-structuring", "reliability-observability-gate"),
            ("requirement-structuring", "repository-impact-inspection"),
            ("requirement-structuring", "scenario-decomposition"),
            ("requirement-structuring", "security-privacy-gate"),
            ("requirement-structuring", "version-compatibility"),
            ("scenario-decomposition", "acceptance-standard-definition"),
            ("scenario-decomposition", "change-documentation-gate"),
            ("scenario-decomposition", "delivery-release-gate"),
            ("scenario-decomposition", "failure-diagnosis"),
            ("scenario-decomposition", "idempotency-retry-design"),
            ("scenario-decomposition", "quality-test-gate"),
            ("scenario-decomposition", "reliability-observability-gate"),
            ("scenario-decomposition", "requirement-clarification"),
            ("scenario-decomposition", "security-privacy-gate"),
            ("scenario-decomposition", "state-machine-modeling"),
            ("scenario-decomposition", "threat-modeling"),
            ("scenario-decomposition", "transaction-consistency"),
            ("scenario-decomposition", "user-flow-modeling"),
            ("state-machine-modeling", "async-job-design"),
            ("state-machine-modeling", "business-rule-extraction"),
            ("state-machine-modeling", "data-migration-design"),
            ("state-machine-modeling", "data-side-effect-flow-tracing"),
            ("state-machine-modeling", "domain-event-modeling"),
            ("state-machine-modeling", "permission-boundary-modeling"),
            ("state-machine-modeling", "quality-test-gate"),
            ("state-machine-modeling", "test-strategy"),
            ("state-machine-modeling", "transaction-consistency"),
        }
        self.assertEqual(33, len(known_relationships))

        targets = PANEL._professional_package_targets(root=ROOT)
        actual_relationships = {
            (target["skill_id"], candidate["skill_id"])
            for target in targets
            for candidate in target["routing_adjacency"]["required_candidates"]
            if "source-declared" in candidate["selection_reasons"]
        }
        self.assertEqual(
            set(),
            known_relationships - actual_relationships,
        )

    def test_professional_source_declared_grammar_is_closed_directional_and_fail_closed(
        self,
    ) -> None:
        known = {
            "source-skill",
            "candidate-a",
            "candidate-b",
            "candidate-c",
            "candidate-d",
            "ordinary-example",
            "history-skill",
            "fenced-skill",
            "frontmatter-skill",
            "layer3-skill",
        }
        content = """---
description: "Route to `frontmatter-skill`."
---

# Source

The package mentions `ordinary-example` without assigning a decision.
Previously routed to `history-skill` in an obsolete release.
Route invalid outcomes to `candidate-a` or `candidate-b detail`.
Handoff recovery decisions to `candidate-b`.

| Decision | Routing owner | Risk gate | Example |
| --- | --- | --- | --- |
| current | `candidate-c` | `candidate-d` | `ordinary-example` |

```text
Route fenced material to `fenced-skill`.
```

## Examples

Route sample work to `ordinary-example`.

## Current decisions

The exact span `candidate-c extra` is not a Skill ID.

## Layer 3 Delivery

Route generated delivery to `layer3-skill`.
"""
        target = {
            "skill_id": "source-skill",
            "root": {"path": "source/SKILL.md", "content": content},
            "indexed_references": [],
        }
        self.assertEqual(
            ["candidate-a", "candidate-b", "candidate-c", "candidate-d"],
            PANEL._professional_source_declared_skill_ids(
                target,
                known_skill_ids=known,
            ),
        )

        reverse = {
            "skill_id": "candidate-a",
            "root": {
                "path": "candidate-a/SKILL.md",
                "content": "# Candidate A\n\nNo directional handoff is declared.\n",
            },
            "indexed_references": [],
        }
        self.assertEqual(
            [],
            PANEL._professional_source_declared_skill_ids(
                reverse,
                known_skill_ids=known,
            ),
        )

        for label, candidate_id, marker in (
            ("unknown", "unknown-skill", "unknown Skill package"),
            ("self", "source-skill", "cannot self-reference"),
        ):
            invalid = copy.deepcopy(target)
            invalid["root"]["content"] = (
                f"# Invalid\n\nRoute the decision to `{candidate_id}`.\n"
            )
            with self.subTest(label=label), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                marker,
            ):
                PANEL._professional_source_declared_skill_ids(
                    invalid,
                    known_skill_ids=known,
                )

    def test_professional_source_declared_ignores_excluded_heading_inside_fence(
        self,
    ) -> None:
        target = {
            "skill_id": "source-skill",
            "root": {
                "path": "source/SKILL.md",
                "content": """# Source

```text
## Examples
Route fenced material to `candidate-a`.
```

Route current work to `candidate-a`.
""",
            },
            "indexed_references": [],
        }

        self.assertEqual(
            ["candidate-a"],
            PANEL._professional_source_declared_skill_ids(
                target,
                known_skill_ids={"source-skill", "candidate-a"},
            ),
        )

    def test_professional_declared_edge_projection_preserves_contracts_and_budget_blocker(
        self,
    ) -> None:
        self.assertEqual(
            "catalog-semantic-overlap-v3",
            PANEL.PROFESSIONAL_ADJACENCY_ALGORITHM,
        )
        self.assertEqual(
            "layered-required-candidates-v2",
            PANEL.PROFESSIONAL_ADJACENCY_SELECTION_VERSION,
        )
        self.assertEqual(5, PANEL.PROFESSIONAL_ADJACENCY_TOP_K)
        self.assertEqual(2, PANEL.PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K)
        self.assertEqual(
            57,
            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET,
        )
        self.assertEqual(
            "a24d605c00e5477f0ea09b4b2eb2aefc32426389980c93efa397fd1c1b41bd4a",
            PANEL._canonical_json_sha256(
                PANEL._professional_adjacency_selection_contract()
            ),
        )
        self.assertEqual(
            "47a7df83b5fa63559c82a52e94a9e374507bbf72a5bff520b1f3e53f193fdd9c",
            PANEL._canonical_json_sha256(
                PANEL._professional_completeness_panel_contract()
            ),
        )

        with mock.patch.object(
            PANEL,
            "_enforce_professional_adjacency_candidate_budget",
        ) as enforce_budget:
            targets = PANEL._professional_package_targets(root=ROOT)
        enforce_budget.assert_called_once_with(targets)
        required_counts = {
            target["skill_id"]: len(
                target["routing_adjacency"]["required_candidates"]
            )
            for target in targets
        }
        targets_by_id = {
            target["skill_id"]: target for target in targets
        }
        eca_adjacency = targets_by_id["engineering-change-analysis"][
            "routing_adjacency"
        ]
        scenario_adjacency = targets_by_id["scenario-decomposition"][
            "routing_adjacency"
        ]
        self.assertNotIn(
            "scenario-decomposition",
            eca_adjacency["registry_declared_skills"],
        )
        allowed_reasons = {
            "registry-declared",
            "source-declared",
            "overall-top-k",
            "negative-route-conflict",
            *{
                f"signal-top-k:{signal_name}"
                for signal_name in PANEL.PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS
            },
        }
        for target in targets:
            adjacency = target["routing_adjacency"]
            ranking = adjacency["full_catalog_ranking"]
            required_by_id = {
                candidate["skill_id"]: candidate
                for candidate in adjacency["required_candidates"]
            }
            declared_by_reason = {
                "registry-declared": set(adjacency["registry_declared_skills"]),
                "source-declared": set(adjacency["source_declared_skills"]),
            }
            for reason, declared_ids in declared_by_reason.items():
                self.assertLessEqual(declared_ids, set(required_by_id))
                for candidate_id in declared_ids:
                    self.assertIn(
                        reason,
                        required_by_id[candidate_id]["selection_reasons"],
                    )
            for candidate_id, candidate in required_by_id.items():
                reasons = candidate["selection_reasons"]
                self.assertTrue(reasons)
                self.assertEqual(sorted(set(reasons)), reasons)
                self.assertLessEqual(set(reasons), allowed_reasons)
                self.assertEqual(
                    candidate_id
                    in (
                        declared_by_reason["registry-declared"]
                        | declared_by_reason["source-declared"]
                    ),
                    candidate["declared"],
                )
            self.assertEqual(187, adjacency["full_catalog_count"])
            self.assertEqual(
                list(range(1, 188)),
                [candidate["rank"] for candidate in ranking],
            )
            self.assertEqual(
                187,
                len({candidate["skill_id"] for candidate in ranking}),
            )
            self.assertNotIn("full_catalog_ranking_fingerprint", adjacency)
        self.assertLessEqual(
            max(required_counts.values()),
            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET,
        )

        PANEL._professional_package_targets(root=ROOT)

    def test_client_lifecycle_split_stays_closed_after_structure_signal_narrowing(
        self,
    ) -> None:
        client_id = "client-lifecycle-state-restoration"
        implementation_id = "implementation-structure-design"
        expected_phrases = [
            "no lifecycle or restoration decision",
            "only offline-sync policy",
            "one platform API without a shared state rule",
        ]
        old_combined = (
            "no lifecycle or restoration decision or only offline-sync policy "
            "or one platform API without a shared state rule"
        )

        def with_phrases(
            targets: list[dict],
            phrases: list[str],
        ) -> list[dict]:
            projected = copy.deepcopy(targets)
            target = next(
                row for row in projected if row["skill_id"] == client_id
            )
            target["registry"]["responsibility_contract"][
                "anti_trigger_signals"
            ] = phrases
            return projected

        def projection(targets: list[dict]) -> dict:
            bases, _contract = PANEL._professional_catalog_adjacency_features(
                targets
            )
            signals: dict[tuple[str, str], dict[str, tuple[str, ...]]] = {}
            required: dict[str, set[str]] = {}
            reasons: dict[str, dict[str, tuple[str, ...]]] = {}
            for target in targets:
                source_id = target["skill_id"]
                ranking = PANEL._professional_catalog_ranking(
                    source_id,
                    bases=bases,
                )
                selected = PANEL._professional_required_adjacency_candidates(
                    ranking,
                    registry_declared_skills=target["routing_adjacency"][
                        "registry_declared_skills"
                    ],
                    source_declared_skills=target["routing_adjacency"][
                        "source_declared_skills"
                    ],
                )
                required[source_id] = {
                    row["skill_id"] for row in selected
                }
                reasons[source_id] = {
                    row["skill_id"]: tuple(row["selection_reasons"])
                    for row in selected
                }
                for row in ranking:
                    signals[(source_id, row["skill_id"])] = {
                        name: tuple(signal["matched_tokens"])
                        for name, signal in row["signals"].items()
                    }
            reverse = {
                target["skill_id"]: {target["skill_id"]}
                for target in targets
            }
            for source_id, candidate_ids in required.items():
                for candidate_id in candidate_ids:
                    reverse[candidate_id].add(source_id)
            return {
                "signals": signals,
                "required": required,
                "reasons": reasons,
                "reverse": reverse,
            }

        current_targets = _phase1_professional_targets()
        current_client = next(
            row for row in current_targets if row["skill_id"] == client_id
        )
        self.assertEqual(
            expected_phrases,
            current_client["registry"]["responsibility_contract"][
                "anti_trigger_signals"
            ],
        )
        current_implementation = next(
            row for row in current_targets if row["skill_id"] == implementation_id
        )
        self.assertFalse(
            any(
                "lifecycle" in signal or "state" in signal
                for signal in current_implementation["registry"][
                    "responsibility_contract"
                ]["trigger_signals"]
            )
        )
        before = projection(with_phrases(current_targets, [old_combined]))
        after = projection(current_targets)

        signal_changes = {
            (source_id, candidate_id, signal_name): (
                before["signals"][(source_id, candidate_id)][signal_name],
                after["signals"][(source_id, candidate_id)][signal_name],
            )
            for source_id, candidate_id in before["signals"]
            for signal_name in before["signals"][(source_id, candidate_id)]
            if before["signals"][(source_id, candidate_id)][signal_name]
            != after["signals"][(source_id, candidate_id)][signal_name]
        }
        self.assertEqual({}, signal_changes)

        required_changes = {
            source_id: {
                "removed": before["required"][source_id]
                - after["required"][source_id],
                "added": after["required"][source_id]
                - before["required"][source_id],
            }
            for source_id in before["required"]
            if before["required"][source_id] != after["required"][source_id]
        }
        self.assertEqual({}, required_changes)
        self.assertEqual(
            len(before["reverse"][implementation_id]),
            len(after["reverse"][implementation_id]),
        )
        self.assertEqual(
            set(),
            before["reverse"][implementation_id]
            - after["reverse"][implementation_id],
        )
        self.assertEqual(
            max(map(len, before["reverse"].values())),
            max(map(len, after["reverse"].values())),
        )
        for owner_id in (
            "installed-client-change-builder",
            "platform-infrastructure-change-builder",
        ):
            for source_id, candidate_id in (
                (client_id, owner_id),
                (owner_id, client_id),
            ):
                with self.subTest(
                    source_id=source_id,
                    candidate_id=candidate_id,
                ):
                    self.assertEqual(
                        before["signals"][(source_id, candidate_id)],
                        after["signals"][(source_id, candidate_id)],
                    )
                    self.assertTrue(
                        any(
                            values
                            for name, values in after["signals"][
                                (source_id, candidate_id)
                            ].items()
                            if name != "negative-route-conflict"
                        )
                    )
                    self.assertEqual(
                        before["reasons"][source_id].get(candidate_id),
                        after["reasons"][source_id].get(candidate_id),
                    )

        rejected = projection(
            with_phrases(
                current_targets,
                [
                    *expected_phrases[:2],
                    "one platform callback without a shared lifecycle state rule",
                ],
            )
        )
        rejected_signal_changes = {
            edge
            for edge in before["signals"]
            if before["signals"][edge] != rejected["signals"][edge]
        }
        self.assertNotEqual(
            {
                (client_id, implementation_id),
                (implementation_id, client_id),
            },
            rejected_signal_changes,
        )

    def test_empty_templates_bind_kind_hash_and_assigned_target_coverage(self) -> None:
        readability_packet = _packet()
        readability_sha = "a" * 64
        readability = PANEL.build_ballot_template(
            packet=readability_packet,
            packet_sha256=readability_sha,
            voter_id="reviewer-a",
            agent_id="readability-agent-a",
            role="senior-readability-reviewer",
            expertise=["AI instruction readability"],
            created_on="2026-07-16",
        )
        self.assertEqual(PANEL.BALLOT_KIND, readability["kind"])
        self.assertEqual(readability_sha, readability["packet_sha256"])
        self.assertEqual(
            [row["path"] for row in readability_packet["content_targets"]],
            [row["path"] for row in readability["content_votes"]],
        )
        self.assertEqual(
            [row["document_id"] for row in readability_packet["readability_targets"]],
            [row["document_id"] for row in readability["readability_votes"]],
        )
        PANEL.validate_ballot_template(
            readability_packet,
            readability,
            packet_sha256=readability_sha,
        )
        with self.assertRaisesRegex(PANEL.PanelReviewError, "decision is invalid"):
            PANEL.validate_ballot(
                readability_packet,
                readability,
                packet_sha256=readability_sha,
            )

        professional_packet = _professional_packet()
        professional_sha = "b" * 64
        professional = PANEL.build_ballot_template(
            packet=professional_packet,
            packet_sha256=professional_sha,
            voter_id="reviewer-a",
            agent_id="professional-agent-a",
            role="senior-professional-reviewer",
            expertise=["professional completeness"],
            created_on="2026-07-16",
            expertise_tags=[PANEL.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG],
            skill_ids=[professional_packet["professional_targets"][0]["skill_id"]],
        )
        self.assertEqual(
            PANEL.PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
            professional["kind"],
        )
        self.assertEqual(professional_sha, professional["packet_sha256"])
        self.assertEqual(
            [professional_packet["professional_targets"][0]["skill_id"]],
            [row["skill_id"] for row in professional["professional_votes"]],
        )
        for row in professional["professional_votes"]:
            self.assertEqual(
                set(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA),
                set(row["criteria"]),
            )
            self.assertTrue(
                all(
                    value["status"] is None
                    and value["evidence_assertions"] == []
                    for value in row["criteria"].values()
                )
            )
            self.assertEqual([], row["evidence_anchors"])
            self.assertEqual([], row["examined_failure_modes"])
            self.assertEqual([], row["examined_omission_candidates"])
            self.assertEqual([], row["proof_limits"])
        PANEL.validate_ballot_template(
            professional_packet,
            professional,
            packet_sha256=professional_sha,
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "decision is invalid|qualification_basis"
        ):
            PANEL.validate_ballot(
                professional_packet,
                professional,
                packet_sha256=professional_sha,
            )

        readability["readability_votes"][0]["decision"] = (
            "accepted-current-readability"
        )
        with self.assertRaisesRegex(PANEL.PanelReviewError, "only unfilled votes"):
            PANEL.validate_ballot_template(
                readability_packet,
                readability,
                packet_sha256=readability_sha,
            )

    def test_template_ballots_cannot_cross_panel_axes(self) -> None:
        readability_packet = _packet()
        professional_packet = _professional_packet()
        readability = PANEL.build_ballot_template(
            packet=readability_packet,
            packet_sha256="a" * 64,
            voter_id="reviewer-a",
            agent_id="readability-agent-a",
            role="senior-readability-reviewer",
            expertise=["AI instruction readability"],
            created_on="2026-07-16",
        )
        professional = PANEL.build_ballot_template(
            packet=professional_packet,
            packet_sha256="b" * 64,
            voter_id="reviewer-a",
            agent_id="professional-agent-a",
            role="senior-professional-reviewer",
            expertise=["professional completeness"],
            created_on="2026-07-16",
            expertise_tags=[PANEL.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG],
            skill_ids=[professional_packet["professional_targets"][0]["skill_id"]],
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "fields do not match|schema does not match"
        ):
            PANEL.validate_ballot(
                readability_packet,
                professional,
                packet_sha256="a" * 64,
            )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "fields do not match|schema does not match"
        ):
            PANEL.validate_ballot(
                professional_packet,
                readability,
                packet_sha256="b" * 64,
            )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "only unfilled votes|voter fields are invalid"
        ):
            PANEL.validate_ballot_template(
                readability_packet,
                professional,
                packet_sha256="a" * 64,
            )

    def test_professional_template_assignment_is_non_empty_unique_known_and_sorted(self) -> None:
        packet = _professional_packet()
        skill_ids = [target["skill_id"] for target in packet["professional_targets"]]

        def build(assigned: list[str] | None) -> dict:
            return PANEL.build_ballot_template(
                packet=packet,
                packet_sha256="c" * 64,
                voter_id="architecture-reviewer",
                agent_id="architecture-agent",
                role="skill-reference-architecture-reviewer",
                expertise=["Skill Reference architecture"],
                created_on="2026-07-16",
                expertise_tags=[PANEL.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG],
                skill_ids=assigned,
            )

        for assigned in (None, []):
            with self.subTest(assigned=assigned):
                with self.assertRaisesRegex(PANEL.PanelReviewError, "non-empty"):
                    build(assigned)
        with self.assertRaisesRegex(PANEL.PanelReviewError, "unique"):
            build([skill_ids[0], skill_ids[0]])
        with self.assertRaisesRegex(PANEL.PanelReviewError, "unknown packages"):
            build(["unknown-skill"])
        ballot = build([skill_ids[1], skill_ids[0]])
        self.assertEqual(
            sorted(skill_ids[:2]),
            [vote["skill_id"] for vote in ballot["professional_votes"]],
        )

    def test_ballot_requires_full_coverage_and_forbids_abstention(self) -> None:
        packet = _packet()
        with tempfile.TemporaryDirectory() as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _ballot(packet, digest, voter=1)
            PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot["readability_votes"] = []
            with self.assertRaisesRegex(PANEL.PanelReviewError, "coverage"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot = _ballot(packet, digest, voter=1)
            ballot["readability_votes"][0]["decision"] = "abstain"
            with self.assertRaisesRegex(PANEL.PanelReviewError, "abstention"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

    def test_ballot_rejects_stale_packet_and_non_independent_voter(self) -> None:
        packet = _packet()
        ballot = _ballot(packet, "a" * 64, voter=1)
        with self.assertRaisesRegex(PANEL.PanelReviewError, "stale"):
            PANEL.validate_ballot(packet, ballot, packet_sha256="b" * 64)
        ballot["packet_sha256"] = "b" * 64
        ballot["voter"]["independent_review"] = False
        with self.assertRaisesRegex(PANEL.PanelReviewError, "independent"):
            PANEL.validate_ballot(packet, ballot, packet_sha256="b" * 64)

    def test_three_unique_experts_produce_a_deterministic_majority(self) -> None:
        packet = _packet()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet_path = ROOT / "tests/fixtures/nonexistent-panel-packet.json"
            local_packet = root / "packet.json"
            _write_json(local_packet, packet)
            digest = hashlib.sha256(local_packet.read_bytes()).hexdigest()
            ballot_values = []
            for voter, decision in enumerate(
                (
                    "accepted-current-readability",
                    "tracked-tightening",
                    "tracked-tightening",
                ),
                start=1,
            ):
                path = root / f"expert-{voter}.json"
                value = _ballot(
                    packet,
                    digest,
                    voter=voter,
                    readability_decision=decision,
                )
                _write_json(path, value)
                ballot_values.append((path, value))
            with mock.patch.object(PANEL, "_sha256") as sha256:
                sha256.side_effect = lambda path: (
                    digest
                    if path == packet_path
                    else hashlib.sha256(path.read_bytes()).hexdigest()
                )
                record = PANEL.aggregate_ballots(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_values=ballot_values,
                    decided_on="2026-07-16",
                )
        decision = record["readability_decisions"][0]
        self.assertEqual("tracked-tightening", decision["winning_disposition"])
        self.assertEqual(2, decision["winning_votes"])
        self.assertEqual(["expert-2", "expert-3"], decision["supporting_voters"])

    def test_readability_aggregate_is_ballot_permutation_invariant(self) -> None:
        packet = _packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter, decision in enumerate(
                (
                    "accepted-current-readability",
                    "tracked-tightening",
                    "tracked-tightening",
                ),
                start=1,
            ):
                path = root / f"expert-{voter}.json"
                value = _ballot(
                    packet,
                    digest,
                    voter=voter,
                    readability_decision=decision,
                )
                _write_json(path, value)
                ballot_values.append((path, value))

            ordered = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )
            permuted = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=[
                    ballot_values[2],
                    ballot_values[0],
                    ballot_values[1],
                ],
                decided_on="2026-07-16",
            )

        self.assertEqual(
            json.dumps(ordered, sort_keys=True, separators=(",", ":")),
            json.dumps(permuted, sort_keys=True, separators=(",", ":")),
        )
        self.assertEqual(
            sorted(voter["voter_id"] for voter in permuted["voters"]),
            [voter["voter_id"] for voter in permuted["voters"]],
        )
        for field in ("content_decisions", "readability_decisions"):
            for decision in permuted[field]:
                self.assertEqual(
                    sorted(decision["supporting_voters"]),
                    decision["supporting_voters"],
                )
                self.assertEqual(
                    sorted(decision["dissenting_voters"]),
                    decision["dissenting_voters"],
                )
                self.assertEqual(
                    sorted(
                        row["voter_id"]
                        for row in decision["winning_rationales"]
                    ),
                    [
                        row["voter_id"]
                        for row in decision["winning_rationales"]
                    ],
                )

    def test_panel_rejects_duplicate_agent_or_role(self) -> None:
        packet = _packet()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet_path = ROOT / "tests/fixtures/nonexistent-panel-packet.json"
            local_packet = root / "packet.json"
            _write_json(local_packet, packet)
            digest = hashlib.sha256(local_packet.read_bytes()).hexdigest()
            ballot_values = []
            for voter in range(1, 4):
                path = root / f"expert-{voter}.json"
                value = _ballot(packet, digest, voter=voter)
                value["voter"]["agent_id"] = "same-agent"
                _write_json(path, value)
                ballot_values.append((path, value))
            with mock.patch.object(PANEL, "_sha256", return_value=digest):
                with self.assertRaisesRegex(PANEL.PanelReviewError, "unique agent_id"):
                    PANEL.aggregate_ballots(
                        packet=packet,
                        packet_path=packet_path,
                        ballot_values=ballot_values,
                        decided_on="2026-07-16",
                    )

    def test_voter_id_must_be_filename_safe(self) -> None:
        packet = _packet()
        with tempfile.TemporaryDirectory() as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _ballot(packet, digest, voter=1)
            ballot["voter"]["voter_id"] = "../escape"

            with self.assertRaisesRegex(PANEL.PanelReviewError, "filename-safe"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

    def test_invalid_ballot_does_not_create_a_partial_record_directory(self) -> None:
        packet = _packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_paths = []
            for voter in range(1, 4):
                ballot_path = root / f"expert-{voter}.json"
                ballot = _ballot(packet, digest, voter=voter)
                if voter == 1:
                    ballot["voter"]["voter_id"] = "../escape"
                _write_json(ballot_path, ballot)
                ballot_paths.append(ballot_path)
            record_dir = root / "panel"
            arguments = [
                "aggregate",
                "--packet",
                packet_path.relative_to(ROOT).as_posix(),
                "--decided-on",
                "2026-07-16",
                "--record-dir",
                record_dir.relative_to(ROOT).as_posix(),
            ]
            for ballot_path in ballot_paths:
                arguments.extend(["--ballot", str(ballot_path)])

            self.assertEqual(1, PANEL.main(arguments))
            self.assertFalse(record_dir.exists())

    def test_packet_rubric_is_closed_and_canonical(self) -> None:
        packet = _packet()
        PANEL.validate_packet(packet)
        packet["rubric"]["reason_codes"]["tracked-tightening"] = []

        with self.assertRaisesRegex(PANEL.PanelReviewError, "rubric"):
            PANEL.validate_packet(packet)

    def test_professional_packet_covers_every_non_control_package_and_reference(self) -> None:
        packet = _professional_packet()
        PANEL.validate_packet(packet)
        self.assertEqual(PANEL.PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION, packet["schema_version"])
        self.assertEqual(188, len(packet["professional_targets"]))
        self.assertTrue(
            all(
                [row["path"] for row in target["indexed_references"]]
                == sorted(
                    {row["path"] for row in target["indexed_references"]}
                )
                for target in packet["professional_targets"]
            )
        )
        self.assertEqual(
            {"professional": 25, "foundation": 150, "domain": 13},
            {
                layer: sum(
                    target["layer"] == layer
                    for target in packet["professional_targets"]
                )
                for layer in ("professional", "foundation", "domain")
            },
        )
        for target in packet["professional_targets"]:
            self.assertTrue(target["required_expertise_tags"])
            self.assertEqual(
                target["root"]["line_count"],
                len(target["root"]["content"].splitlines()),
            )
            adjacency = target["routing_adjacency"]
            self.assertEqual(
                PANEL.PROFESSIONAL_ADJACENCY_ALGORITHM,
                adjacency["algorithm"],
            )
            candidates = {
                row["skill_id"]: row
                for row in adjacency["required_candidates"]
            }
            self.assertTrue(set(adjacency["declared_skills"]) <= set(candidates))
            self.assertEqual(
                PANEL._professional_adjacency_selection_contract(),
                adjacency["required_candidate_selection"],
            )
            self.assertEqual(
                PANEL._canonical_json_sha256(adjacency["required_candidates"]),
                adjacency["required_candidates_fingerprint"],
            )
            self.assertEqual(187, len(adjacency["full_catalog_ranking"]))
            self.assertEqual(
                PANEL._canonical_json_sha256(adjacency["full_catalog_ranking"]),
                adjacency["full_catalog_ranking_fingerprint"],
            )
            for ranking_item in adjacency["full_catalog_ranking"]:
                self.assertEqual(
                    set(PANEL.PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS),
                    set(ranking_item["signals"]),
                )
                for signal in ranking_item["signals"].values():
                    self.assertEqual(signal["count"], len(signal["matched_tokens"]))
            self.assertTrue(
                {
                    row["skill_id"]
                    for row in adjacency["full_catalog_ranking"]
                    if row["rank"] <= PANEL.PROFESSIONAL_ADJACENCY_TOP_K
                }
                <= set(candidates)
            )
            self.assertTrue(
                {
                    row["skill_id"]
                    for row in adjacency["full_catalog_ranking"]
                    if row["signals"]["negative-route-conflict"]["count"] > 0
                }
                <= set(candidates)
            )
            self.assertTrue(
                all(row["selection_reasons"] for row in candidates.values())
            )
            self.assertEqual(64, len(adjacency["full_catalog_ranking_fingerprint"]))

        required_candidate_counts = [
            len(target["routing_adjacency"]["required_candidates"])
            for target in packet["professional_targets"]
        ]
        self.assertLessEqual(
            sum(required_candidate_counts),
            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_TOTAL,
        )
        self.assertLessEqual(
            max(required_candidate_counts),
            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET,
        )

        reference_target = next(
            target for target in packet["professional_targets"]
            if target["indexed_references"]
        )
        raw_basis = PANEL._professional_raw_adjacency_basis(reference_target)
        reference = reference_target["indexed_references"][0]
        heading_tokens = PANEL._adjacency_tokens(
            PANEL._markdown_topic_headings(reference["content"])
        )
        self.assertTrue(heading_tokens & raw_basis["reference_topics"])
        self.assertTrue(
            PANEL._adjacency_tokens(reference["path"])
            & raw_basis["reference_topics"]
        )

        filtered_bases, filter_contract = (
            PANEL._professional_catalog_adjacency_features(
                packet["professional_targets"]
            )
        )
        raw_bases = {
            target["skill_id"]: PANEL._professional_raw_adjacency_basis(target)
            for target in packet["professional_targets"]
        }
        self.assertEqual(
            "phrase-aware-df-bypass",
            filter_contract["negative_route_conflict_filtering"],
        )
        for skill_id, raw_basis in raw_bases.items():
            self.assertEqual(
                raw_basis["trigger_phrases"],
                filtered_bases[skill_id]["negative_route_trigger_phrases"],
            )
            self.assertEqual(
                raw_basis["anti_trigger_phrases"],
                filtered_bases[skill_id][
                    "negative_route_anti_trigger_phrases"
                ],
            )
        high_frequency = []
        for field in (
            "triggers",
            "anti_triggers",
            "outputs",
            "responsibility",
            "reference_topics",
        ):
            tokens = {
                token
                for basis in raw_bases.values()
                for token in basis[field]
            }
            for token in tokens:
                count = sum(token in basis[field] for basis in raw_bases.values())
                if count > filter_contract["maximum_document_frequency"]:
                    high_frequency.append((field, token))
        self.assertTrue(high_frequency)
        for field, token in high_frequency:
            self.assertTrue(
                all(token not in basis[field] for basis in filtered_bases.values())
            )

    def test_professional_current_targets_bind_complete_registry_and_reference_authority(
        self,
    ) -> None:
        targets = _phase1_professional_targets()
        registry_rows = {}
        for _layer, relative, collection_key in PANEL.REGISTRY_SOURCES:
            registry = PANEL.load_yaml_file(ROOT / relative)
            registry_rows.update(
                (row["name"], (relative, row))
                for row in registry[collection_key]
            )

        self.assertEqual(set(registry_rows), {row["skill_id"] for row in targets})
        for target in targets:
            skill_id = target["skill_id"]
            relative, registry_row = registry_rows[skill_id]
            reference_authority = PANEL.reference_contracts(
                registry_row["reference_index"],
                f"{relative}:{skill_id}.reference_index",
                owner=skill_id,
            )
            self.assertEqual(registry_row, target["registry_authority"])
            self.assertEqual(reference_authority, target["reference_authority"])
            self.assertEqual(
                sorted(
                    (
                        PurePosixPath(registry_row["path"])
                        / reference["path"]
                    ).as_posix()
                    for reference in reference_authority
                ),
                [reference["path"] for reference in target["indexed_references"]],
            )

    def test_professional_current_packet_requires_and_recomputes_authority_binding(
        self,
    ) -> None:
        packet = professional_support._bootstrap_packet()
        self.assertTrue(
            all(
                set(target) == PANEL.PROFESSIONAL_V3_PACKET_TARGET_FIELDS
                for target in packet["professional_targets"]
            )
        )

        for label, mutate in (
            (
                "missing",
                lambda target: target.pop("registry_authority"),
            ),
            (
                "extra",
                lambda target: target.update({"derived_semantics": {}}),
            ),
        ):
            changed = copy.deepcopy(packet)
            mutate(changed["professional_targets"][0])
            with self.subTest(label=label), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "packet target fields are invalid",
            ):
                PANEL._professional_v3_packet_state(
                    changed,
                    validation_root=ROOT,
                    artifact_path=None,
                    validate_baseline=False,
                )

        changed = copy.deepcopy(packet)
        target = changed["professional_targets"][0]
        target["registry_authority"]["activation"] = "changed activation"
        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "review binding is stale",
        ):
            PANEL._professional_v3_packet_state(
                changed,
                validation_root=ROOT,
                artifact_path=None,
                validate_baseline=False,
            )

        mismatched = copy.deepcopy(packet)
        reference_target = next(
            target
            for target in mismatched["professional_targets"]
            if target["reference_authority"]
        )
        reference_target["reference_authority"] = []
        with self.assertRaisesRegex(ValueError, "reference_index.*drift"):
            PANEL._professional_v3_packet_state(
                mismatched,
                validation_root=ROOT,
                artifact_path=None,
                validate_baseline=False,
            )

    def test_professional_authority_changes_refresh_exact_one_hop_review_surface(
        self,
    ) -> None:
        carry = PANEL.professional_carry
        targets = professional_support._catalog()
        bindings = carry.professional_review_bindings(targets)
        review_contract = "a" * 64
        snapshot = carry.professional_carry_snapshot(
            bindings,
            review_contract_fingerprint=review_contract,
        )
        dependencies = {}
        for skill_id, binding in bindings.items():
            required = binding["adjacency"]["required_candidate_ids"]
            reviewer_added = ["d"] if skill_id == "a" else []
            dependencies[skill_id] = {
                "skill_id": skill_id,
                "final_disposition": carry.ACCEPTED_PROFESSIONAL_DISPOSITION,
                "evidence_complete": True,
                "prior_target_vote_count": PANEL.PANEL_SIZE,
                "required_candidate_ids": copy.deepcopy(required),
                "reviewer_added_candidate_ids_union": reviewer_added,
                "dependency_candidate_ids": sorted(
                    set(required) | set(reviewer_added)
                ),
            }

        responsibility_fields = {
            "trigger_signals",
            "anti_trigger_signals",
            "required_inputs",
            "output_contract",
            "escalation_signals",
            "boundary_signals",
            "layer3_candidates",
            "used_by",
            "task_routable",
            "role_support",
        }
        registry_cases = (
            ("trigger", "trigger_signals", ["changed trigger"]),
            ("anti-trigger", "anti_trigger_signals", ["changed anti-trigger"]),
            ("required-input", "required_inputs", ["changed input"]),
            ("required-output", "output_contract", ["changed output"]),
            ("escalation", "escalation_signals", ["changed escalation"]),
            ("boundary", "boundary_signals", ["changed boundary"]),
            ("routing-mode", "routing_mode", "direct"),
            ("routing-family", "routing_family", "repository-tooling"),
            ("task-routable", "task_routable", False),
            (
                "role-input",
                "required_inputs_by_role",
                {"task-agent": ["changed role input"]},
            ),
            (
                "role-output",
                "output_contract_by_role",
                {"task-agent": ["changed role output"]},
            ),
            (
                "context-admissibility",
                "context_admissibility",
                {"contract": "fixture/v2", "references": {}},
            ),
            ("activation", "activation", "explicit"),
            ("layer3", "layer3_candidates", ["a"]),
            ("used-by", "used_by", ["a"]),
            ("role-support", "role_support", ["analysis-agent"]),
        )

        def assert_exact_fresh(changed_targets: list[dict], label: str) -> None:
            plan = carry.plan_exact_professional_carry_forward(
                current_bindings=carry.professional_review_bindings(
                    changed_targets
                ),
                prior_snapshot=snapshot,
                prior_decision_dependencies=dependencies,
                review_contract_fingerprint=review_contract,
            )
            self.assertEqual(["a", "b", "d"], plan["fresh_target_ids"], label)
            self.assertIn(
                "target-material-changed",
                plan["reasons_by_target"]["d"],
                label,
            )
            self.assertIn(
                "required-candidate-material-changed",
                plan["reasons_by_target"]["b"],
                label,
            )
            self.assertIn(
                "reviewer-added-candidate-material-changed",
                plan["reasons_by_target"]["a"],
                label,
            )
            self.assertEqual([], plan["reasons_by_target"]["c"], label)

        for label, field, value in registry_cases:
            changed = copy.deepcopy(targets)
            target = changed[3]
            target["registry_authority"][field] = copy.deepcopy(value)
            if field in responsibility_fields:
                target["registry"]["responsibility_contract"][field] = (
                    copy.deepcopy(value)
                )
            with self.subTest(authority=label):
                assert_exact_fresh(changed, label)

        changed = copy.deepcopy(targets)
        changed[3]["required_expertise_tags"] = ["domain", "security"]
        changed[3]["registry_authority"]["required_expertise_tags"] = [
            "domain",
            "security",
        ]
        assert_exact_fresh(changed, "required-expertise")

        changed = copy.deepcopy(targets)
        target = changed[3]
        target["registry_authority"]["path"] = "src/d-renamed"
        target["root"]["path"] = "src/d-renamed/SKILL.md"
        target["indexed_references"][0]["path"] = (
            "src/d-renamed/reference.md"
        )
        assert_exact_fresh(changed, "package-path")

        reference_cases = (
            ("path", "renamed-reference.md"),
            ("type", "decision-checklist"),
            ("load_when", "Reviewing d recovery evidence for this bounded task"),
            (
                "do_not_load_when",
                "The d recovery boundary is already fully evidenced",
            ),
            ("required_by", ["analysis-agent"]),
            ("required_output", ["decision-record"]),
        )
        for field, value in reference_cases:
            changed = copy.deepcopy(targets)
            target = changed[3]
            reference = copy.deepcopy(target["reference_authority"][0])
            reference[field] = copy.deepcopy(value)
            target["reference_authority"] = [reference]
            target["registry_authority"]["reference_index"] = [
                copy.deepcopy(reference)
            ]
            if field == "path":
                target["indexed_references"][0]["path"] = (
                    "src/d/renamed-reference.md"
                )
            with self.subTest(reference_field=field):
                assert_exact_fresh(changed, f"reference-{field}")

        wrong_owner = copy.deepcopy(targets)
        wrong_owner[3]["registry_authority"]["name"] = "other-owner"
        with self.assertRaisesRegex(ValueError, "name must match"):
            carry.professional_review_bindings(wrong_owner)

        missing_path = copy.deepcopy(targets)
        missing_path[3]["indexed_references"] = []
        with self.assertRaisesRegex(ValueError, "coverage drift"):
            carry.professional_review_bindings(missing_path)

        mismatched_path = copy.deepcopy(targets)
        reference = copy.deepcopy(
            mismatched_path[3]["reference_authority"][0]
        )
        reference["path"] = "renamed-reference.md"
        mismatched_path[3]["reference_authority"] = [reference]
        mismatched_path[3]["registry_authority"]["reference_index"] = [
            copy.deepcopy(reference)
        ]
        with self.assertRaisesRegex(ValueError, "coverage drift"):
            carry.professional_review_bindings(mismatched_path)

        extra_path = copy.deepcopy(targets)
        extra_path[3]["indexed_references"].append(
            copy.deepcopy(extra_path[3]["indexed_references"][0])
        )
        extra_path[3]["indexed_references"][1]["path"] = "src/d/extra.md"
        with self.assertRaisesRegex(ValueError, "path-sorted|coverage drift"):
            carry.professional_review_bindings(extra_path)

    def test_negative_route_conflicts_are_phrase_aware_and_ignore_generic_noise(
        self,
    ) -> None:
        def route_basis(*, triggers: list[str], anti_triggers: list[str]) -> dict:
            return {
                "negative_route_trigger_phrases": (
                    PANEL._negative_route_phrases(triggers)
                ),
                "negative_route_anti_trigger_phrases": (
                    PANEL._negative_route_phrases(anti_triggers)
                ),
            }

        source = route_basis(
            triggers=["implementation diff ready"],
            anti_triggers=["design task-local decision required"],
        )
        candidate = route_basis(
            triggers=["ordinary task-local decision required"],
            anti_triggers=["no actual diff"],
        )
        self.assertEqual(
            ["target-trigger/candidate-anti:diff"],
            PANEL._professional_negative_route_conflicts(source, candidate),
        )

        generic_source = route_basis(
            triggers=["design task-local decision required"],
            anti_triggers=["ordinary task-local decision required"],
        )
        generic_candidate = route_basis(
            triggers=["select task-local decision required"],
            anti_triggers=["no task-local decision is required"],
        )
        self.assertEqual(
            [],
            PANEL._professional_negative_route_conflicts(
                generic_source, generic_candidate
            ),
        )

    def test_professional_required_candidate_budgets_fail_closed(self) -> None:
        per_target_over_budget = [
            {
                "routing_adjacency": {
                    "required_candidates": [
                        {}
                        for _index in range(
                            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
                            + 1
                        )
                    ]
                }
            }
        ]
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "per-target budget exceeded"
        ):
            PANEL._enforce_professional_adjacency_candidate_budget(
                per_target_over_budget
            )

        full_targets, remainder = divmod(
            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_TOTAL + 1,
            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET,
        )
        catalog_over_budget = [
            {
                "routing_adjacency": {
                    "required_candidates": [
                        {}
                        for _index in range(
                            PANEL.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
                        )
                    ]
                }
            }
            for _target_index in range(full_targets)
        ]
        if remainder:
            catalog_over_budget.append(
                {
                    "routing_adjacency": {
                        "required_candidates": [
                            {} for _index in range(remainder)
                        ]
                    }
                }
            )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "catalog budget exceeded"
        ):
            PANEL._enforce_professional_adjacency_candidate_budget(
                catalog_over_budget
            )

    def test_professional_packet_rejects_missing_duplicate_and_stale_targets(self) -> None:
        for label, mutate, marker in (
            (
                "missing",
                lambda packet: packet["professional_targets"].pop(),
                "exactly 188",
            ),
            (
                "duplicate",
                lambda packet: packet["professional_targets"].__setitem__(
                    1, packet["professional_targets"][0]
                ),
                "skill-sorted and unique",
            ),
            (
                "fingerprint",
                lambda packet: packet["professional_targets"][0]["root"].__setitem__(
                    "sha256", "0" * 64
                ),
                "content does not match sha256",
            ),
        ):
            with self.subTest(label=label):
                packet = _professional_packet()
                mutate(packet)
                with self.assertRaisesRegex(PANEL.PanelReviewError, marker):
                    PANEL.validate_packet(packet)

    def test_professional_ballot_accepts_subset_and_requires_non_empty_complete_votes(self) -> None:
        packet = _professional_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _professional_ballot(packet, digest, voter=1)
            PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot["professional_votes"].pop()
            PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot["professional_votes"] = []
            with self.assertRaisesRegex(PANEL.PanelReviewError, "non-empty"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot = _professional_ballot(packet, digest, voter=1)
            ballot["professional_votes"][1] = ballot["professional_votes"][0]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "duplicate"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot = _professional_ballot(packet, digest, voter=1)
            ballot["professional_votes"][0]["criteria"].pop("failure-modes")
            with self.assertRaisesRegex(PANEL.PanelReviewError, "every professional criterion"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

    def test_professional_ballot_rejects_unbound_evidence_and_incomplete_review(self) -> None:
        packet = _professional_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()

            ballot = _professional_ballot(packet, digest, voter=1)
            ballot["professional_votes"][0]["evidence_anchors"][0][
                "end_line"
            ] = 999999
            with self.assertRaisesRegex(PANEL.PanelReviewError, "line range"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            reference_index = next(
                index
                for index, target in enumerate(packet["professional_targets"])
                if target["indexed_references"]
            )
            ballot = _professional_ballot(packet, digest, voter=1)
            vote = ballot["professional_votes"][reference_index]
            assertion = vote["criteria"][
                "reference-high-risk-coverage"
            ]["evidence_assertions"][0]
            root_anchor_id = next(
                anchor["anchor_id"]
                for anchor in vote["evidence_anchors"]
                if anchor["skill_id"] == vote["skill_id"]
                and anchor["path"].endswith("SKILL.md")
            )
            root_anchor = next(
                anchor
                for anchor in vote["evidence_anchors"]
                if anchor["anchor_id"] == root_anchor_id
            )
            root_tokens = _fixture_anchor_tokens(
                root_anchor, PANEL._professional_materials_by_skill(packet)
            )
            assertion["claim"] = (
                f"Reference coverage instead cites {root_tokens[0]} and "
                f"{root_tokens[1]} from current root evidence."
            )
            assertion["evidence_anchor_ids"] = [root_anchor_id]
            assertion["source_excerpt_sha256"] = (
                PANEL._professional_assertion_excerpt_sha256(
                    [root_anchor_id],
                    anchors_by_id={
                        anchor["anchor_id"]: anchor
                        for anchor in vote["evidence_anchors"]
                    },
                    materials_by_skill=PANEL._professional_materials_by_skill(packet),
                )
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "indexed Reference"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot = _professional_ballot(packet, digest, voter=1)
            ballot["professional_votes"][0]["examined_adjacent_candidates"].pop()
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "every required packet candidate"
            ):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            ballot = _professional_ballot(packet, digest, voter=1)
            ballot["professional_votes"][0]["examined_failure_modes"][0]["outcome"] = (
                "defect-found"
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "failure-modes criterion"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

    def test_professional_ballot_accepts_and_constrains_reviewer_added_candidates(
        self,
    ) -> None:
        packet = _professional_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _professional_ballot(packet, digest, voter=1)
            vote_index, candidate_id = _add_reviewer_added_candidate(
                packet, ballot
            )

            PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            missing_discovery = copy.deepcopy(ballot)
            added = next(
                row
                for row in missing_discovery["professional_votes"][vote_index][
                    "examined_adjacent_candidates"
                ]
                if row["skill_id"] == candidate_id
            )
            added["discovery_reason"] = None
            with self.assertRaisesRegex(PANEL.PanelReviewError, "discovery_reason"):
                PANEL.validate_ballot(
                    packet, missing_discovery, packet_sha256=digest
                )

            duplicate = copy.deepcopy(ballot)
            reviews = duplicate["professional_votes"][vote_index][
                "examined_adjacent_candidates"
            ]
            reviews.append(copy.deepcopy(next(
                row for row in reviews if row["skill_id"] == candidate_id
            )))
            reviews.sort(key=lambda row: row["skill_id"])
            with self.assertRaisesRegex(PANEL.PanelReviewError, "sorted and unique"):
                PANEL.validate_ballot(packet, duplicate, packet_sha256=digest)

            outside_catalog = copy.deepcopy(ballot)
            added = next(
                row
                for row in outside_catalog["professional_votes"][vote_index][
                    "examined_adjacent_candidates"
                ]
                if row["skill_id"] == candidate_id
            )
            added["skill_id"] = outside_catalog["professional_votes"][vote_index][
                "skill_id"
            ]
            outside_catalog["professional_votes"][vote_index][
                "examined_adjacent_candidates"
            ].sort(key=lambda row: row["skill_id"])
            with self.assertRaisesRegex(PANEL.PanelReviewError, "full_catalog_ranking"):
                PANEL.validate_ballot(
                    packet, outside_catalog, packet_sha256=digest
                )

    def test_professional_ballot_rejects_template_and_cross_package_evidence(self) -> None:
        packet = _professional_packet()
        materials = PANEL._professional_materials_by_skill(packet)
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            base = _professional_ballot(packet, digest, voter=1)

            frontmatter = copy.deepcopy(base)
            vote = frontmatter["professional_votes"][0]
            criterion = sorted(vote["criteria"])[0]
            assertion = vote["criteria"][criterion]["evidence_assertions"][0]
            anchor_id = assertion["evidence_anchor_ids"][0]
            anchor = next(
                item for item in vote["evidence_anchors"]
                if item["anchor_id"] == anchor_id
            )
            anchor["start_line"] = 1
            anchor["end_line"] = 1
            with self.assertRaisesRegex(PANEL.PanelReviewError, "substantive body text"):
                PANEL.validate_ballot(packet, frontmatter, packet_sha256=digest)

            no_overlap = copy.deepcopy(base)
            assertion = no_overlap["professional_votes"][0]["criteria"][criterion][
                "evidence_assertions"
            ][0]
            assertion["claim"] = (
                "Zygote quasar nebula validates unrelated platypus assertions today."
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "non-generic tokens"):
                PANEL.validate_ballot(packet, no_overlap, packet_sha256=digest)

            generic = copy.deepcopy(base)
            vote = generic["professional_votes"][0]
            first_assertion = vote["criteria"][criterion]["evidence_assertions"][0]
            anchor_id = first_assertion["evidence_anchor_ids"][0]
            anchors_by_id = {
                item["anchor_id"]: item for item in vote["evidence_anchors"]
            }
            tokens = _fixture_anchor_tokens(anchors_by_id[anchor_id], materials)
            repeated_claim = (
                f"Repeated {tokens[0]} and {tokens[1]} evidence covers every "
                "professional criterion identically."
            )
            excerpt_sha = PANEL._professional_assertion_excerpt_sha256(
                [anchor_id],
                anchors_by_id=anchors_by_id,
                materials_by_skill=materials,
            )
            for result in vote["criteria"].values():
                result["evidence_assertions"] = [
                    {
                        "claim": repeated_claim,
                        "evidence_anchor_ids": [anchor_id],
                        "source_excerpt_sha256": excerpt_sha,
                    }
                ]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "unique claim"):
                PANEL.validate_ballot(packet, generic, packet_sha256=digest)

            cross_package = copy.deepcopy(base)
            vote = cross_package["professional_votes"][0]
            candidate_anchor = next(
                item
                for item in vote["evidence_anchors"]
                if item["skill_id"] != vote["skill_id"]
            )
            assertion = vote["criteria"][criterion]["evidence_assertions"][0]
            assertion["evidence_anchor_ids"] = [candidate_anchor["anchor_id"]]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "wrong Skill package"):
                PANEL.validate_ballot(packet, cross_package, packet_sha256=digest)

            too_few_failures = copy.deepcopy(base)
            too_few_failures["professional_votes"][0][
                "examined_failure_modes"
            ].pop()
            with self.assertRaisesRegex(PANEL.PanelReviewError, "at least two"):
                PANEL.validate_ballot(packet, too_few_failures, packet_sha256=digest)

            generic_failure = copy.deepcopy(base)
            failure = generic_failure["professional_votes"][0][
                "examined_failure_modes"
            ][0]
            failure["failure_mode"] = "quasar-nebula-platypus"
            failure["rationale"] = (
                "Quasar nebula platypus words provide no grounded source semantics."
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "non-generic tokens"):
                PANEL.validate_ballot(packet, generic_failure, packet_sha256=digest)

            omission_defect = copy.deepcopy(base)
            omission_defect["professional_votes"][0][
                "examined_omission_candidates"
            ][0]["outcome"] = "defect-found"
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "material-omissions criterion"
            ):
                PANEL.validate_ballot(packet, omission_defect, packet_sha256=digest)

            wrong_candidate_anchor = copy.deepcopy(base)
            adjacency = wrong_candidate_anchor["professional_votes"][0][
                "examined_adjacent_candidates"
            ][0]
            adjacency["candidate_anchor_ids"] = adjacency["target_anchor_ids"]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "wrong Skill package"):
                PANEL.validate_ballot(
                    packet, wrong_candidate_anchor, packet_sha256=digest
                )

            missing_qualification = copy.deepcopy(base)
            missing_qualification["voter"]["qualification_claims"].pop()
            with self.assertRaisesRegex(PANEL.PanelReviewError, "exactly cover"):
                PANEL.validate_ballot(
                    packet, missing_qualification, packet_sha256=digest
                )

    def test_professional_packet_recomputes_independent_adjacency_ranking(self) -> None:
        packet = _professional_packet()
        target = packet["professional_targets"][0]
        adjacency = target["routing_adjacency"]
        old_top_five_ids = set(adjacency["declared_skills"]) | {
            row["skill_id"]
            for row in adjacency["full_catalog_ranking"]
            if row["rank"] <= PANEL.PROFESSIONAL_ADJACENCY_TOP_K
        }
        old_top_five = [
            row
            for row in adjacency["required_candidates"]
            if row["skill_id"] in old_top_five_ids
        ]
        self.assertLess(len(old_top_five), len(adjacency["required_candidates"]))
        adjacency["required_candidates"] = old_top_five
        adjacency["required_candidates_fingerprint"] = (
            PANEL._canonical_json_sha256(old_top_five)
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        target["package_fingerprint"] = PANEL._canonical_json_sha256(
            without_fingerprint
        )
        packet["source_fingerprints"]["professional_packages"] = (
            PANEL._canonical_json_sha256(packet["professional_targets"])
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "canonical layered selection"
        ):
            PANEL.validate_packet(packet)

        packet = _professional_packet()
        target = packet["professional_targets"][0]
        target["routing_adjacency"]["required_candidates"][0][
            "total_score"
        ] += 1
        target["routing_adjacency"]["required_candidates_fingerprint"] = (
            PANEL._canonical_json_sha256(
                target["routing_adjacency"]["required_candidates"]
            )
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        target["package_fingerprint"] = PANEL._canonical_json_sha256(
            without_fingerprint
        )
        packet["source_fingerprints"]["professional_packages"] = (
            PANEL._canonical_json_sha256(packet["professional_targets"])
        )
        with self.assertRaisesRegex(
            PANEL.PanelReviewError, "canonical layered selection"
        ):
            PANEL.validate_packet(packet)

        packet = _professional_packet()
        target = packet["professional_targets"][0]
        target["routing_adjacency"]["full_catalog_ranking"][0][
            "total_score"
        ] += 1
        target["routing_adjacency"]["full_catalog_ranking_fingerprint"] = (
            PANEL._canonical_json_sha256(
                target["routing_adjacency"]["full_catalog_ranking"]
            )
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        target["package_fingerprint"] = PANEL._canonical_json_sha256(
            without_fingerprint
        )
        packet["source_fingerprints"]["professional_packages"] = (
            PANEL._canonical_json_sha256(packet["professional_targets"])
        )
        with self.assertRaisesRegex(PANEL.PanelReviewError, "full_catalog_ranking is stale"):
            PANEL.validate_packet(packet)

    def test_rank_six_negative_route_conflict_is_required_and_cannot_be_omitted(
        self,
    ) -> None:
        packet = _professional_packet()
        target = packet["professional_targets"][0]
        adjacency = target["routing_adjacency"]
        declared = set(adjacency["declared_skills"])
        ranked_ids = [
            row["skill_id"]
            for row in adjacency["full_catalog_ranking"]
            if row["skill_id"] not in declared
        ]
        self.assertGreaterEqual(len(ranked_ids), 6)
        leaders = ranked_ids[:6]

        def synthetic_row(
            skill_id: str,
            *,
            rank: int,
            trigger_count: int = 0,
            negative_count: int = 0,
        ) -> dict:
            signals = {
                signal_name: {
                    "matched_tokens": [],
                    "count": 0,
                    "weight": weight,
                }
                for signal_name, weight in sorted(
                    PANEL.PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS.items()
                )
            }
            if trigger_count:
                tokens = [f"synthetic-trigger-{index:02d}" for index in range(trigger_count)]
                signals["trigger-overlap"].update(
                    {"matched_tokens": tokens, "count": trigger_count}
                )
            if negative_count:
                tokens = [
                    f"target-trigger/candidate-anti:synthetic-route-{index:02d}"
                    for index in range(negative_count)
                ]
                signals["negative-route-conflict"].update(
                    {"matched_tokens": tokens, "count": negative_count}
                )
            return {
                "skill_id": skill_id,
                "total_score": sum(
                    signal["count"] * signal["weight"]
                    for signal in signals.values()
                ),
                "signals": signals,
                "rank": rank,
            }

        synthetic_ranking = [
            synthetic_row(
                skill_id,
                rank=index,
                trigger_count=6 - index,
            )
            for index, skill_id in enumerate(leaders[:5], start=1)
        ]
        synthetic_ranking.append(
            synthetic_row(leaders[5], rank=6, negative_count=1)
        )
        remaining = sorted(
            set(row["skill_id"] for row in adjacency["full_catalog_ranking"])
            - set(leaders)
        )
        synthetic_ranking.extend(
            synthetic_row(skill_id, rank=index)
            for index, skill_id in enumerate(remaining, start=7)
        )
        self.assertTrue(
            all(
                row["signals"]["negative-route-conflict"]["count"] == 0
                for row in synthetic_ranking[:5]
            )
        )
        rank_six_id = synthetic_ranking[5]["skill_id"]
        required = PANEL._professional_required_adjacency_candidates(
            synthetic_ranking,
            registry_declared_skills=adjacency[
                "registry_declared_skills"
            ],
            source_declared_skills=adjacency["source_declared_skills"],
        )
        rank_six = next(
            row for row in required if row["skill_id"] == rank_six_id
        )
        self.assertIn("negative-route-conflict", rank_six["selection_reasons"])

        adjacency["required_candidate_selection"] = (
            PANEL._professional_adjacency_selection_contract()
        )
        adjacency["required_candidates"] = required
        adjacency["required_candidates_fingerprint"] = (
            PANEL._canonical_json_sha256(required)
        )
        adjacency["full_catalog_count"] = len(synthetic_ranking)
        adjacency["full_catalog_ranking"] = synthetic_ranking
        adjacency["full_catalog_ranking_fingerprint"] = (
            PANEL._canonical_json_sha256(synthetic_ranking)
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        target["package_fingerprint"] = PANEL._canonical_json_sha256(
            without_fingerprint
        )
        packet["source_fingerprints"]["professional_packages"] = (
            PANEL._canonical_json_sha256(packet["professional_targets"])
        )

        original_ranking = PANEL._professional_catalog_ranking

        def patched_ranking(skill_id: str, *, bases: dict) -> list[dict]:
            if skill_id == target["skill_id"]:
                return synthetic_ranking
            return original_ranking(skill_id, bases=bases)

        with mock.patch.object(
            PANEL,
            "_professional_catalog_ranking",
            side_effect=patched_ranking,
        ), tempfile.TemporaryDirectory(dir=ROOT) as raw:
            PANEL.validate_packet(packet)
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _professional_ballot(packet, digest, voter=1)
            vote = ballot["professional_votes"][0]
            vote["examined_adjacent_candidates"] = [
                row
                for row in vote["examined_adjacent_candidates"]
                if row["skill_id"] != rank_six_id
            ]
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "every required packet candidate"
            ):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

    def test_historical_professional_schema_one_artifacts_remain_readable(self) -> None:
        with _synthetic_schema1_professional_decision() as fixture:
            packet, packet_path, ballots, decision, decision_path = fixture
            PANEL.validate_packet(packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            for _path, ballot in ballots:
                PANEL.validate_ballot(
                    packet,
                    ballot,
                    packet_sha256=digest,
                )
            self.assertEqual(
                decision,
                PANEL.validate_decision_record(
                    decision, record_path=decision_path
                ),
            )

    def test_historical_mode_preserves_source_stale_schema_two_readability(self) -> None:
        with _synthetic_historical_schema2_readability_decision() as fixture:
            decision, decision_path = fixture
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "schema-2 content source binding contract is missing or stale",
            ):
                PANEL.validate_decision_record(decision, record_path=decision_path)

            self.assertEqual(
                decision,
                PANEL.validate_decision_record(
                    decision,
                    record_path=decision_path,
                    validation_mode="historical",
                ),
            )
            for field, mutate in (
                (
                    "packet",
                    lambda value: value["packet"].update({"sha256": "0" * 64}),
                ),
                (
                    "ballot",
                    lambda value: value["voters"][0].update(
                        {"ballot_sha256": "0" * 64}
                    ),
                ),
                (
                    "majority",
                    lambda value: value["summary"]["readability"].update(
                        {"accepted-current-readability": 0}
                    ),
                ),
            ):
                tampered = copy.deepcopy(decision)
                mutate(tampered)
                with self.subTest(field=field), self.assertRaises(
                    PANEL.PanelReviewError
                ):
                    PANEL.validate_decision_record(
                        tampered,
                        record_path=decision_path,
                        validation_mode="historical",
                    )

    def test_historical_mode_preserves_source_stale_schema_three_professional(
        self,
    ) -> None:
        with _synthetic_schema3_professional_decision() as fixture:
            decision = fixture["decision"]
            decision_path = fixture["decision_path"]
            validation_root = fixture["validation_root"]
            stale_contract = "0" * 64
            self.assertNotEqual(
                stale_contract,
                decision["review_contract_fingerprint"],
            )
            with mock.patch.object(
                PANEL,
                "_professional_evidence_review_contract_fingerprint",
                return_value=stale_contract,
            ):
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "review contract is stale",
                ):
                    PANEL.validate_decision_record(
                        decision,
                        record_path=decision_path,
                        validation_root=validation_root,
                    )
                self.assertEqual(
                    decision,
                    PANEL.validate_decision_record(
                        decision,
                        record_path=decision_path,
                        validation_root=validation_root,
                        validation_mode="historical",
                    ),
                )

            tampered_depth = copy.deepcopy(decision)
            target = tampered_depth["professional_decisions"][0]
            target["provenance"]["origin_depth"] = 1
            without_fingerprint = dict(target)
            without_fingerprint.pop("target_decision_fingerprint")
            target["target_decision_fingerprint"] = (
                PANEL._canonical_json_sha256(without_fingerprint)
            )
            _write_json(decision_path, tampered_depth)
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "fresh target provenance is stale",
            ):
                PANEL.validate_decision_record(
                    tampered_depth,
                    record_path=decision_path,
                    validation_root=validation_root,
                    validation_mode="historical",
                )

            _write_json(decision_path, decision)
            ballot_path, ballot = fixture["ballots"][0]
            tampered_ballot = copy.deepcopy(ballot)
            tampered_ballot["limitations"].append("Post-decision tamper.")
            _write_json(ballot_path, tampered_ballot)
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "decision does not match recomputed evidence",
            ):
                PANEL.validate_decision_record(
                    decision,
                    record_path=decision_path,
                    validation_root=validation_root,
                    validation_mode="historical",
                )

    def test_historical_current_registered_schema3_rejects_k_mutation_end_to_end(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "historical selection contract is invalid",
        ):
            with _synthetic_schema3_professional_decision(
                mutate_registered_selection=True
            ):
                self.fail("mutated registered selector reached canonical packet state")

    def test_historical_mode_is_closed_and_axis_specific(self) -> None:
        decision_path = ROOT / ".rd-skills/expert-panel/synthetic/decision.json"
        decision = {"kind": PANEL.DECISION_KIND}
        with self.assertRaisesRegex(PANEL.PanelReviewError, "validation mode"):
            PANEL.validate_decision_record(
                decision,
                record_path=decision_path,
                validation_mode="anything",
            )

        with self.assertRaisesRegex(PANEL.PanelReviewError, "historical"):
            PANEL.validate_decision_record(
                {"kind": PANEL.SEMANTIC_DISPOSITION_DECISION_KIND},
                record_path=decision_path,
                validation_mode="historical",
            )

    def test_panel_axes_cannot_substitute_for_each_other(self) -> None:
        readability_packet = _packet()
        professional_packet = _professional_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            readability_path = root / "readability.json"
            professional_path = root / "professional.json"
            _write_json(readability_path, readability_packet)
            _write_json(professional_path, professional_packet)
            readability_digest = hashlib.sha256(readability_path.read_bytes()).hexdigest()
            professional_digest = hashlib.sha256(professional_path.read_bytes()).hexdigest()
            readability_ballot = _ballot(
                readability_packet, readability_digest, voter=1
            )
            professional_ballot = _professional_ballot(
                professional_packet, professional_digest, voter=1
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "fields|schema does not match"
            ):
                PANEL.validate_ballot(
                    readability_packet,
                    professional_ballot,
                    packet_sha256=readability_digest,
                )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "fields|schema does not match"
            ):
                PANEL.validate_ballot(
                    professional_packet,
                    readability_ballot,
                    packet_sha256=professional_digest,
                )

    def test_professional_reviewer_pool_uses_distinct_domain_pairs_by_skill(self) -> None:
        packet = _professional_packet()
        skill_ids = [target["skill_id"] for target in packet["professional_targets"]]
        midpoint = len(skill_ids) // 2
        first, second = skill_ids[:midpoint], skill_ids[midpoint:]
        assignments = [
            (1, "domain", first),
            (2, "domain", first),
            (3, "architecture", first),
            (4, "domain", second),
            (5, "domain", second),
            (6, "architecture", second),
        ]
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter, reviewer_kind, assigned_skill_ids in assignments:
                ballot = _professional_ballot(
                    packet,
                    digest,
                    voter=voter,
                    reviewer_kind=reviewer_kind,
                    skill_ids=assigned_skill_ids,
                )
                ballot_path = root / f"professional-expert-{voter}.json"
                _write_json(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=list(reversed(ballot_values)),
                decided_on="2026-07-16",
            )
            ordered_record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )

        self.assertEqual(ordered_record, record)
        self.assertEqual(
            PANEL.PROFESSIONAL_COMPLETENESS_DECISION_METHOD,
            record["decision_method"],
        )
        self.assertEqual(3, record["summary"]["qualification"]["per_target_panel_size"])
        self.assertEqual(6, record["summary"]["qualification"]["reviewer_pool_size"])
        self.assertEqual(
            ["professional-expert-1", "professional-expert-2"],
            record["professional_decisions"][0]["qualification_coverage"][
                "domain_voters"
            ],
        )
        self.assertEqual(
            ["professional-expert-4", "professional-expert-5"],
            record["professional_decisions"][-1]["qualification_coverage"][
                "domain_voters"
            ],
        )
        self.assertEqual(
            188 * 3 * len(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA),
            record["summary"]["evidence"]["criterion_result_count"],
        )
        self.assertEqual(
            sorted(voter["voter_id"] for voter in record["voters"]),
            [voter["voter_id"] for voter in record["voters"]],
        )

    def test_one_domain_critical_defect_is_unresolved_despite_accept_majority(self) -> None:
        packet = _professional_packet()
        correction_skill = packet["professional_targets"][0]["skill_id"]
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            added_review: tuple[int, str] | None = None
            for voter in range(1, 4):
                ballot_path = root / f"professional-expert-{voter}.json"
                ballot = _professional_ballot(
                    packet,
                    digest,
                    voter=voter,
                    correction_skill=correction_skill if voter == 1 else None,
                )
                if voter == 1:
                    added_review = _add_reviewer_added_candidate(packet, ballot)
                _write_json(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )
        self.assertEqual(
            0,
            record["summary"]["professional_completeness"][
                "requires-professional-correction"
            ],
        )
        self.assertEqual(
            1,
            record["summary"]["professional_completeness"][
                PANEL.PROFESSIONAL_UNRESOLVED_DISPOSITION
            ],
        )
        self.assertEqual(
            "accepted-current-professional-completeness",
            record["professional_decisions"][0]["winning_disposition"],
        )
        self.assertEqual(
            PANEL.PROFESSIONAL_UNRESOLVED_DISPOSITION,
            record["professional_decisions"][0]["final_disposition"],
        )
        self.assertEqual(
            [{"criterion": "professional-correctness", "voter_id": "professional-expert-1"}],
            record["professional_decisions"][0]["domain_critical_defects"],
        )
        self.assertEqual(
            188,
            record["summary"]["qualification"]["covered_target_count"],
        )
        self.assertEqual(
            188 * 3 * len(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA),
            record["summary"]["evidence"]["criterion_result_count"],
        )
        self.assertEqual(
            ["professional-expert-1", "professional-expert-2"],
            record["professional_decisions"][0]["qualification_coverage"][
                "domain_voters"
            ],
        )
        self.assertTrue(record["voters"][0]["qualification_claims"])
        self.assertIsNotNone(added_review)
        assert added_review is not None
        added_vote_index, added_candidate_id = added_review
        added_skill_id = packet["professional_targets"][added_vote_index]["skill_id"]
        added_decision = next(
            row
            for row in record["professional_decisions"]
            if row["skill_id"] == added_skill_id
        )
        self.assertEqual(
            added_candidate_id,
            added_decision["reviewer_added_adjacency_reviews"][0][
                "candidates"
            ][0]["skill_id"],
        )
        self.assertEqual(
            1,
            record["summary"]["evidence"][
                "reviewer_added_adjacency_count"
            ],
        )
        required_candidate_count = sum(
            len(target["routing_adjacency"]["required_candidates"])
            for target in packet["professional_targets"]
        )
        self.assertEqual(
            required_candidate_count,
            record["summary"]["evidence"][
                "required_adjacency_candidate_count"
            ],
        )
        self.assertEqual(
            required_candidate_count * PANEL.PANEL_SIZE,
            record["summary"]["evidence"][
                "examined_required_adjacency_count"
            ],
        )
        self.assertEqual(
            record["summary"]["evidence"]["examined_adjacency_count"],
            record["summary"]["evidence"][
                "examined_required_adjacency_count"
            ]
            + 1,
        )
        self.assertIn(
            "do not prove real reviewer identity",
            " ".join(record["limitations"]),
        )

    def test_professional_per_skill_panel_rejects_wrong_role_counts_and_vote_count(self) -> None:
        packet = _professional_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            domain_one = _professional_ballot(
                packet, digest, voter=1, reviewer_kind="domain"
            )
            domain_two = _professional_ballot(
                packet, digest, voter=2, reviewer_kind="domain"
            )
            domain_three = _professional_ballot(
                packet, digest, voter=4, reviewer_kind="domain"
            )
            architecture_one = _professional_ballot(
                packet, digest, voter=3, reviewer_kind="architecture"
            )
            architecture_two = _professional_ballot(
                packet, digest, voter=5, reviewer_kind="architecture"
            )

            def aggregate(ballots: list[dict]) -> None:
                values = []
                for index, ballot in enumerate(ballots):
                    path = root / f"role-count-{index}.json"
                    _write_json(path, ballot)
                    values.append((path, ballot))
                PANEL.aggregate_ballots(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_values=values,
                    decided_on="2026-07-16",
                )

            with self.assertRaisesRegex(PANEL.PanelReviewError, "two qualified domain"):
                aggregate([domain_one, domain_two, domain_three])
            with self.assertRaisesRegex(PANEL.PanelReviewError, "two qualified domain"):
                aggregate([domain_one, architecture_one, architecture_two])
            with self.assertRaisesRegex(PANEL.PanelReviewError, "exactly 3 assigned"):
                aggregate(
                    [domain_one, domain_two, architecture_one, architecture_two]
                )
            missing_assignment = copy.deepcopy(domain_one)
            missing_assignment["professional_votes"].pop()
            with self.assertRaisesRegex(PANEL.PanelReviewError, "exactly 3 assigned"):
                aggregate([missing_assignment, domain_two, architecture_one])
            duplicate_agent = copy.deepcopy(architecture_one)
            duplicate_agent["voter"]["agent_id"] = domain_one["voter"]["agent_id"]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "unique agent_id"):
                aggregate([domain_one, domain_two, duplicate_agent])
            duplicate_voter = copy.deepcopy(architecture_one)
            duplicate_voter["voter"]["voter_id"] = domain_one["voter"]["voter_id"]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "unique voter_id"):
                aggregate([domain_one, domain_two, duplicate_voter])

    def test_each_domain_critical_criterion_is_fail_closed(self) -> None:
        packet = _professional_packet()
        correction_skill = packet["professional_targets"][0]["skill_id"]
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            accepting_domain = _professional_ballot(packet, digest, voter=2)
            accepting_architecture = _professional_ballot(packet, digest, voter=3)
            for criterion in sorted(PANEL.PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA):
                with self.subTest(criterion=criterion):
                    defect_domain = _professional_ballot(
                        packet,
                        digest,
                        voter=1,
                        correction_skill=correction_skill,
                        correction_criterion=criterion,
                    )
                    ballots = [defect_domain, accepting_domain, accepting_architecture]
                    ballot_values = []
                    for index, ballot in enumerate(ballots, start=1):
                        path = root / f"critical-{index}.json"
                        _write_json(path, ballot)
                        ballot_values.append((path, ballot))
                    record = PANEL.aggregate_ballots(
                        packet=packet,
                        packet_path=packet_path,
                        ballot_values=ballot_values,
                        decided_on="2026-07-16",
                    )
                    decision = record["professional_decisions"][0]
                    self.assertEqual(
                        "accepted-current-professional-completeness",
                        decision["winning_disposition"],
                    )
                    self.assertEqual(
                        PANEL.PROFESSIONAL_UNRESOLVED_DISPOSITION,
                        decision["final_disposition"],
                    )
                    self.assertEqual(
                        [{"criterion": criterion, "voter_id": "professional-expert-1"}],
                        decision["domain_critical_defects"],
                    )

    def test_architecture_only_critical_defect_does_not_trigger_domain_blocker(self) -> None:
        packet = _professional_packet()
        correction_skill = packet["professional_targets"][0]["skill_id"]
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballots = [
                _professional_ballot(packet, digest, voter=1),
                _professional_ballot(packet, digest, voter=2),
                _professional_ballot(
                    packet,
                    digest,
                    voter=3,
                    correction_skill=correction_skill,
                    correction_criterion="professional-correctness",
                ),
            ]
            ballot_values = []
            for index, ballot in enumerate(ballots, start=1):
                path = root / f"architecture-defect-{index}.json"
                _write_json(path, ballot)
                ballot_values.append((path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )
        decision = record["professional_decisions"][0]
        self.assertEqual([], decision["domain_critical_defects"])
        self.assertEqual(
            "accepted-current-professional-completeness",
            decision["final_disposition"],
        )

    def test_noncritical_criteria_keep_ordinary_two_of_three_majority(self) -> None:
        packet = _professional_packet()
        correction_skill = packet["professional_targets"][0]["skill_id"]
        noncritical = sorted(
            set(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA)
            - PANEL.PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
        )
        self.assertEqual(4, len(noncritical))
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            accepting_architecture = _professional_ballot(packet, digest, voter=3)
            for criterion in noncritical:
                with self.subTest(criterion=criterion):
                    ballots = [
                        _professional_ballot(
                            packet,
                            digest,
                            voter=voter,
                            correction_skill=correction_skill,
                            correction_criterion=criterion,
                        )
                        for voter in (1, 2)
                    ]
                    ballots.append(accepting_architecture)
                    ballot_values = []
                    for index, ballot in enumerate(ballots, start=1):
                        path = root / f"ordinary-{index}.json"
                        _write_json(path, ballot)
                        ballot_values.append((path, ballot))
                    record = PANEL.aggregate_ballots(
                        packet=packet,
                        packet_path=packet_path,
                        ballot_values=ballot_values,
                        decided_on="2026-07-16",
                    )
                    decision = record["professional_decisions"][0]
                    self.assertEqual([], decision["domain_critical_defects"])
                    self.assertEqual(
                        "requires-professional-correction",
                        decision["winning_disposition"],
                    )
                    self.assertEqual(
                        "requires-professional-correction",
                        decision["final_disposition"],
                    )
                    self.assertEqual(
                        [criterion], decision["ordinary_criterion_defects"]
                    )
                    self.assertEqual(
                        "requires-professional-correction",
                        decision["ordinary_criterion_disposition"],
                    )

    def test_distributed_ordinary_defects_do_not_create_a_false_correction(self) -> None:
        packet = _professional_packet()
        correction_skill = packet["professional_targets"][0]["skill_id"]
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballots = [
                _professional_ballot(
                    packet,
                    digest,
                    voter=1,
                    correction_skill=correction_skill,
                    correction_criterion="generic-knowledge-pollution",
                ),
                _professional_ballot(
                    packet,
                    digest,
                    voter=2,
                    correction_skill=correction_skill,
                    correction_criterion="output-verifiability",
                ),
                _professional_ballot(packet, digest, voter=3),
            ]
            ballot_values = []
            for index, ballot in enumerate(ballots, start=1):
                path = root / f"distributed-ordinary-{index}.json"
                _write_json(path, ballot)
                ballot_values.append((path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )

        decision = record["professional_decisions"][0]
        self.assertEqual([], decision["domain_critical_defects"])
        self.assertEqual([], decision["ordinary_criterion_defects"])
        self.assertEqual(
            "accepted-current-professional-completeness",
            decision["ordinary_criterion_disposition"],
        )
        self.assertEqual(
            "requires-professional-correction",
            decision["winning_disposition"],
        )
        self.assertEqual(
            "accepted-current-professional-completeness",
            decision["final_disposition"],
        )
        self.assertEqual(
            1,
            decision["criterion_vote_counts"]["generic-knowledge-pollution"][
                "defect-found"
            ],
        )
        self.assertEqual(
            1,
            decision["criterion_vote_counts"]["output-verifiability"][
                "defect-found"
            ],
        )
        self.assertEqual(
            1,
            record["summary"]["overall_ballot_majority_audit"][
                "requires-professional-correction"
            ],
        )
        self.assertEqual(
            PANEL.PROFESSIONAL_PACKAGE_COUNT,
            record["summary"]["ordinary_criterion_majority"][
                "accepted-current-professional-completeness"
            ],
        )

    def test_professional_ballot_rejects_unknown_arbitration_field(self) -> None:
        packet = _professional_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _professional_ballot(packet, digest, voter=1)
            ballot["professional_votes"][0]["arbitration"] = {
                "disposition": "override"
            }
            with self.assertRaisesRegex(PANEL.PanelReviewError, "fields are invalid"):
                PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

    def test_professional_panel_requires_exact_expertise_coverage(self) -> None:
        packet = _professional_packet()
        required_tag = packet["professional_targets"][0][
            "required_expertise_tags"
        ][0]
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()

            def aggregate(ballots: list[dict]) -> dict:
                values = []
                for voter, ballot in enumerate(ballots, start=1):
                    ballot_path = root / f"qualification-{voter}.json"
                    _write_json(ballot_path, ballot)
                    values.append((ballot_path, ballot))
                return PANEL.aggregate_ballots(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_values=values,
                    decided_on="2026-07-16",
                )

            ballots = [
                _professional_ballot(packet, digest, voter=voter)
                for voter in range(1, 4)
            ]
            ballots[0]["voter"]["expertise_tags"] = [
                tag
                for tag in ballots[0]["voter"]["expertise_tags"]
                if tag != required_tag
            ]
            ballots[0]["voter"]["qualification_claims"] = [
                claim
                for claim in ballots[0]["voter"]["qualification_claims"]
                if claim["expertise_tag"] != required_tag
            ]
            with self.assertRaisesRegex(PANEL.PanelReviewError, "lacks required expertise"):
                aggregate(ballots)

            ballots = [
                _professional_ballot(packet, digest, voter=voter)
                for voter in range(1, 4)
            ]
            ballots[1]["voter"]["expertise_tags"].append(
                PANEL.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
            )
            ballots[1]["voter"]["expertise_tags"].sort()
            ballots[1]["voter"]["qualification_claims"].append(
                {
                    "expertise_tag": PANEL.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG,
                    "qualification_basis": (
                        "Reviewer declares prior work in Skill Reference architecture reviews."
                    ),
                    "proof_limit": (
                        "This static architecture declaration cannot verify external credentials."
                    ),
                }
            )
            ballots[1]["voter"]["qualification_claims"].sort(
                key=lambda claim: claim["expertise_tag"]
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "architecture ballot"):
                aggregate(ballots)

    def test_semantic_packet_targets_are_the_synthetic_non_carry_forward_difference(self) -> None:
        audit = _semantic_audit_with_synthetic_delta()
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=audit,
            review_id="semantic-live-diff",
            created_on="2026-07-16",
        )
        PANEL.validate_semantic_packet_current(packet, audit)

        expected_total = 0
        for axis, content_key in (
            ("root", "root_content"),
            ("reference", "reference_content"),
        ):
            semantic = audit[content_key]["semantic_advisories"]
            candidates = PANEL._semantic_eligible_candidates(
                axis=axis, semantic=semantic
            )
            entries = semantic["disposition_contract"]["entries"]
            entries_by_id = {entry["candidate_id"]: entry for entry in entries}
            target_ids = []
            exact_ids = []
            for candidate in candidates:
                entry = entries_by_id.get(candidate["candidate_id"])
                exact = not PANEL._semantic_entry_mismatches(
                    axis=axis,
                    candidate=candidate,
                    entry=entry,
                )
                (exact_ids if exact else target_ids).append(candidate["candidate_id"])
            stale_old = sorted(
                set(entries_by_id) - {candidate["candidate_id"] for candidate in candidates}
            )
            provenance = packet["candidate_provenance"][axis]
            self.assertEqual(sorted(exact_ids), provenance["exact_carry_forward_candidate_ids"])
            self.assertEqual(sorted(target_ids), provenance["review_target_candidate_ids"])
            self.assertEqual(stale_old, provenance["stale_old_candidate_ids"])
            self.assertEqual(
                len(candidates) - len(exact_ids), provenance["review_target_count"]
            )
            expected_total += len(target_ids)
        self.assertEqual(expected_total, len(packet["semantic_targets"]))
        for target in packet["semantic_targets"]:
            self.assertTrue(target["candidate"]["occurrences"])
            self.assertTrue(
                all(row["path"] for row in target["candidate"]["occurrences"])
            )

    def test_semantic_packet_rejects_missing_duplicate_and_stale_evidence(self) -> None:
        for label, mutate, marker in (
            (
                "missing",
                lambda packet: packet["semantic_targets"].pop(),
                "targets do not match provenance|panel_contract",
            ),
            (
                "duplicate",
                lambda packet: packet["semantic_targets"].append(
                    copy.deepcopy(packet["semantic_targets"][-1])
                ),
                "sorted and unique|targets do not match provenance",
            ),
            (
                "candidate-evidence",
                lambda packet: packet["semantic_targets"][0]["candidate"].__setitem__(
                    "preview", "stale altered candidate evidence"
                ),
                "candidate_binding_fingerprint is stale",
            ),
        ):
            with self.subTest(label=label):
                packet = _semantic_packet()
                mutate(packet)
                with self.assertRaisesRegex(PANEL.PanelReviewError, marker):
                    PANEL.validate_packet(packet)

        audit = _semantic_audit_with_synthetic_delta()
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=audit,
            review_id="semantic-stale-audit",
            created_on="2026-07-16",
        )
        changed = copy.deepcopy(audit)
        changed["root_content"]["semantic_advisories"]["candidates"][0][
            "context_fingerprint"
        ] = "0" * 64
        with self.assertRaisesRegex(PANEL.PanelReviewError, "stale"):
            PANEL.validate_semantic_packet_current(packet, changed)

    def test_semantic_source_fingerprints_are_closed_candidate_manifests_and_detector_contracts(
        self,
    ) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        audit["semantic_disposition_application"] = {
            "schema_version": 1,
            "kind": PANEL.SEMANTIC_DISPOSITION_APPLICATION_KIND,
            "review_id": "semantic-current-first",
            "decision_kind": (
                PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND
            ),
            "decision": {
                "path": PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH,
                "sha256": "1" * 64,
            },
            "status": "current",
            "target_count": 0,
            "applied_count": 0,
            "completed_rewrite_count": 0,
        }

        def fingerprints(value: dict) -> dict[str, str]:
            root_semantic, reference_semantic = PANEL._semantic_audit_sections(value)
            return PANEL._semantic_source_fingerprints(
                value,
                root_semantic=root_semantic,
                reference_semantic=reference_semantic,
            )

        original = copy.deepcopy(audit)
        baseline = fingerprints(audit)
        self.assertEqual(original, audit)
        self.assertEqual(
            {
                "reference_candidate_manifest",
                "reference_detector_contract",
                "root_candidate_manifest",
                "root_detector_contract",
            },
            set(baseline),
        )
        selector_changed = copy.deepcopy(audit)
        selector_changed["semantic_disposition_application"].update(
            {
                "kind": "changeforge.semantic-disposition-application-replacement",
                "review_id": "semantic-current-second",
                "decision_kind": "changeforge.semantic-disposition-attestation-replacement",
                "status": "invalid",
                "target_count": 3,
                "applied_count": 2,
                "completed_rewrite_count": 1,
                "error": {
                    "id": "selector-derived-error",
                    "message": "Selector-derived application status changed.",
                },
            }
        )
        selector_changed["semantic_disposition_application"]["decision"] = {
            "path": "evals/expert-panel/semantic-disposition-replacement.json",
            "sha256": "2" * 64,
        }
        self.assertEqual(baseline, fingerprints(selector_changed))

        config_changed = copy.deepcopy(audit)
        config_changed["root_content"]["semantic_advisories"][
            "disposition_contract"
        ]["entries"][0]["reason"] += " Substantive authority changed."
        config_changed["reference_content"]["semantic_advisories"][
            "disposition_contract"
        ]["entries"][0]["disposition"] = "false-positive"
        config_changed["root_content"]["source_fingerprint"] = "6" * 64
        config_changed["reference_content"]["preface_contract"][
            "source_fingerprint"
        ] = "7" * 64
        config_changed["review_id"] = "untrusted-audit-report-selector"
        config_changed["created_on"] = "2099-12-31"
        self.assertEqual(baseline, fingerprints(config_changed))

        root_candidate_changed = copy.deepcopy(audit)
        root_candidate_changed["root_content"]["semantic_advisories"]["candidates"][0][
            "fingerprint"
        ] = "3" * 64
        changed = fingerprints(root_candidate_changed)
        self.assertNotEqual(
            baseline["root_candidate_manifest"],
            changed["root_candidate_manifest"],
        )
        self.assertEqual(
            baseline["reference_candidate_manifest"],
            changed["reference_candidate_manifest"],
        )

        reference_candidate_changed = copy.deepcopy(audit)
        group = next(
            candidate
            for candidate in reference_candidate_changed["reference_content"][
                "semantic_advisories"
            ]["candidates"]
            if candidate["path"] == "group"
        )
        group["content_fingerprint"] = "5" * 64
        changed = fingerprints(reference_candidate_changed)
        self.assertNotEqual(
            baseline["reference_candidate_manifest"],
            changed["reference_candidate_manifest"],
        )

        root_detector_changed = copy.deepcopy(audit)
        root_detector_changed["root_content"]["semantic_advisories"][
            "detector_contract"
        ]["value"] = "4" * 64
        changed = fingerprints(root_detector_changed)
        self.assertNotEqual(
            baseline["root_detector_contract"],
            changed["root_detector_contract"],
        )

        reference_detector_changed = copy.deepcopy(audit)
        reference_detector_changed["reference_content"]["semantic_advisories"][
            "detector_contract"
        ]["value"] = "5" * 64
        changed = fingerprints(reference_detector_changed)
        self.assertNotEqual(
            baseline["reference_detector_contract"],
            changed["reference_detector_contract"],
        )

        unrelated_threshold_changed = copy.deepcopy(audit)
        unrelated_threshold_changed["thresholds"] = {
            **unrelated_threshold_changed["thresholds"],
            "semantic-fixture-threshold": 1,
        }
        self.assertEqual(baseline, fingerprints(unrelated_threshold_changed))

    def test_semantic_forced_both_selector_resolves_all_current_targets_without_runtime_artifacts(
        self,
    ) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        forced = PANEL._semantic_audit_for_axis_rereview(
            audit, ["root", "reference"]
        )
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=forced,
            review_id="semantic-forced-both-current",
            created_on="2026-08-11",
        )
        selector = {
            "source_fingerprints": copy.deepcopy(packet["source_fingerprints"]),
            "review_contract_fingerprint": PANEL._canonical_json_sha256(
                packet["panel_contract"]
            ),
            "findings": [
                {
                    "axis": target["axis"],
                    "target_id": target["target_id"],
                }
                for target in packet["semantic_targets"]
            ],
        }

        selected = PANEL._semantic_current_packet_for_attestation_selector(
            audit=audit,
            review_id="semantic-forced-both-current",
            decided_on="2026-08-11",
            attestation_selector=selector,
        )

        expected_axis_counts = {
            axis: len(
                PANEL._semantic_eligible_candidates(
                    axis=axis,
                    semantic=audit[f"{axis}_content"]["semantic_advisories"],
                )
            )
            for axis in ("root", "reference")
        }
        self.assertEqual(
            sum(expected_axis_counts.values()),
            len(selected["semantic_targets"]),
        )
        self.assertEqual(
            expected_axis_counts,
            selected["panel_contract"]["required_axis_target_counts"],
        )

    def test_semantic_secure_prepare_forces_both_axes_against_original_audit(
        self,
    ) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        original = copy.deepcopy(audit)
        packet = PANEL._semantic_forced_prepare_packet(
            audit=audit,
            axes=["root", "reference"],
            review_id="semantic-secure-forced-both",
            created_on="2026-08-13",
        )

        self.assertEqual(original, audit)
        expected_axis_counts = {
            axis: len(
                PANEL._semantic_eligible_candidates(
                    axis=axis,
                    semantic=original[f"{axis}_content"][
                        "semantic_advisories"
                    ],
                )
            )
            for axis in ("root", "reference")
        }
        self.assertEqual(
            expected_axis_counts,
            packet["panel_contract"]["required_axis_target_counts"],
        )
        PANEL.validate_semantic_packet_current(packet, original)

        for axes in ([], ["root"], ["reference"], ["root", "root"]):
            with self.subTest(axes=axes), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "both root and reference",
            ):
                PANEL._semantic_forced_prepare_packet(
                    audit=audit,
                    axes=axes,
                    review_id="semantic-incomplete-force",
                    created_on="2026-08-13",
                )

    def test_semantic_prepare_reviewer_specs_require_four_distinct_fields(
        self,
    ) -> None:
        rows = [
            [f"voter-{index}", f"agent-{index}", f"role-{index}", f"lens-{index}"]
            for index in range(1, 4)
        ]
        self.assertEqual(3, len(PANEL._semantic_prepare_reviewer_specs(rows)))
        for field_index in range(4):
            duplicate = copy.deepcopy(rows)
            duplicate[1][field_index] = duplicate[0][field_index]
            with self.subTest(field_index=field_index), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "distinct",
            ):
                PANEL._semantic_prepare_reviewer_specs(duplicate)

    def test_semantic_prepare_audit_authority_rejects_wrong_path_and_dirty_tree(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "canonical path",
        ):
            PANEL._semantic_prepare_audit_authority("audit.json")

        completed = mock.Mock(stdout=b" M src/example\x00", returncode=0)
        with mock.patch.object(PANEL, "_git_output", return_value=completed):
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "clean tracked tree",
            ):
                PANEL._semantic_prepare_audit_authority(
                    "reports/skill-content-audit.json"
                )

        clean = mock.Mock(stdout=b"", returncode=0)
        untracked = mock.Mock(stdout=b"", returncode=1)
        with mock.patch.object(
            PANEL, "_git_output", side_effect=[clean, untracked]
        ):
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "must be tracked",
            ):
                PANEL._semantic_prepare_audit_authority(
                    "reports/skill-content-audit.json"
                )

        tracked = mock.Mock(stdout=b"", returncode=0)
        head = mock.Mock(stdout=b'{"schema_version": 10}\n', returncode=0)
        bound = mock.Mock(raw=b'{"schema_version": 9}\n')
        with mock.patch.object(
            PANEL, "_git_output", side_effect=[clean, tracked, head]
        ), mock.patch.object(
            PANEL.reviewer_manifest,
            "read_bound_regular_file",
            return_value=bound,
        ):
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "byte-equal to clean HEAD",
            ):
                PANEL._semantic_prepare_audit_authority(
                    "reports/skill-content-audit.json"
                )

    def test_semantic_runtime_is_atomic_create_once_with_three_templates(
        self,
    ) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        packet = PANEL._semantic_forced_prepare_packet(
            audit=audit,
            axes=["root", "reference"],
            review_id="semantic-atomic-create-once",
            created_on="2026-08-13",
        )
        packet_raw = PANEL.reviewer_manifest.canonical_ballot_bytes(
            packet, compact=False
        )
        packet_sha256 = hashlib.sha256(packet_raw).hexdigest()
        templates = [
            PANEL.prepare_semantic_ballot_template(
                packet=packet,
                packet_sha256=packet_sha256,
                voter_id=f"semantic-voter-{index}",
                agent_id=f"semantic-agent-{index}",
                role=f"semantic-role-{index}",
                expertise=[f"semantic-expertise-{index}"],
                created_on="2026-08-13",
            )
            for index in range(1, 4)
        ]
        audit_raw = json.dumps(
            audit, indent=2, ensure_ascii=False, sort_keys=True
        ).encode("utf-8") + b"\n"
        with tempfile.TemporaryDirectory(dir=ROOT) as raw, mock.patch.object(
            PANEL, "ROOT", Path(raw)
        ):
            layout = PANEL._create_semantic_runtime(
                review_id=packet["review_id"],
                audit_raw=audit_raw,
                packet=packet,
                templates=templates,
            )
            self.assertEqual(audit_raw, layout["audit"].read_bytes())
            self.assertEqual(3, len(list(layout["ballots"].glob("*.template.json"))))
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "canonical run already exists",
            ):
                PANEL._create_semantic_runtime(
                    review_id=packet["review_id"],
                    audit_raw=audit_raw,
                    packet=packet,
                    templates=templates,
                )

    def test_semantic_currentness_ignores_applied_governance_only(self) -> None:
        packet = _semantic_packet()
        current = copy.deepcopy(_live_semantic_audit())
        PANEL.validate_semantic_packet_current(packet, current)

        changed = copy.deepcopy(current)
        root_target = next(
            target for target in packet["semantic_targets"] if target["axis"] == "root"
        )
        root_candidate = next(
            candidate
            for candidate in changed["root_content"]["semantic_advisories"]["candidates"]
            if candidate["candidate_id"] == root_target["candidate"]["candidate_id"]
        )
        root_candidate["disposition"] = "false-positive"
        root_candidate["governance_status"] = "resolved-by-current-entry"
        root_candidate["resolved"] = True
        root_candidate["unresolved"] = False
        reference_target = next(
            target
            for target in packet["semantic_targets"]
            if target["axis"] == "reference"
        )
        reference_candidate = next(
            candidate
            for candidate in changed["reference_content"]["semantic_advisories"]["candidates"]
            if candidate["candidate_id"]
            == reference_target["candidate"]["candidate_id"]
        )
        reference_candidate["priority"] = (
            "P1" if reference_candidate.get("priority") != "P1" else "P2"
        )
        reference_candidate["disposition"] = "valid-contextual-rule"
        changed["reference_content"]["semantic_advisories"][
            "disposition_contract"
        ]["entries"][0]["rationale"] = "Governance-only rationale update."
        changed["root_content"]["source_fingerprint"] = "0" * 64
        changed["reference_content"]["preface_contract"][
            "source_fingerprint"
        ] = "1" * 64
        changed["ai_readability"] = {
            "source_fingerprint": {"value": "2" * 64}
        }
        layout_target = next(
            target
            for target in packet["semantic_targets"]
            if target["axis"] == "reference" and target["candidate"]["path"] != "group"
        )
        layout_candidate = next(
            candidate
            for candidate in changed["reference_content"]["semantic_advisories"]["candidates"]
            if candidate["candidate_id"]
            == layout_target["candidate"]["candidate_id"]
        )
        for occurrence in layout_candidate["occurrences"]:
            occurrence["lines"] = {
                "start": occurrence["lines"]["start"] + 1,
                "end": occurrence["lines"]["end"] + 1,
            }
        PANEL.validate_semantic_packet_current(packet, changed)

    def test_semantic_currentness_rejects_stable_identity_evidence_changes(self) -> None:
        packet = _semantic_packet()
        current = copy.deepcopy(_live_semantic_audit())

        def change_detector(audit: dict) -> None:
            audit["root_content"]["semantic_advisories"]["detector_contract"][
                "value"
            ] = "0" * 64

        def change_candidate_set(audit: dict) -> None:
            audit["root_content"]["semantic_advisories"]["candidates"].pop()

        def change_candidate_text(audit: dict) -> None:
            target = next(
                target
                for target in packet["semantic_targets"]
                if target["axis"] == "root"
            )
            candidate = next(
                candidate
                for candidate in audit["root_content"]["semantic_advisories"]["candidates"]
                if candidate["candidate_id"] == target["candidate"]["candidate_id"]
            )
            candidate["fingerprint"] = "0" * 64

        def change_context(audit: dict) -> None:
            audit["root_content"]["semantic_advisories"]["candidates"][0][
                "context_fingerprint"
            ] = "0" * 64

        def change_group(audit: dict) -> None:
            candidates = audit["reference_content"]["semantic_advisories"][
                "candidates"
            ]
            group = next(candidate for candidate in candidates if candidate["path"] == "group")
            group["content_fingerprint"] = "0" * 64

        for label, mutate in (
            ("detector", change_detector),
            ("candidate-set", change_candidate_set),
            ("candidate-text", change_candidate_text),
            ("context", change_context),
            ("group", change_group),
        ):
            with self.subTest(label=label):
                changed = copy.deepcopy(current)
                mutate(changed)
                with self.assertRaisesRegex(PANEL.PanelReviewError, "stale"):
                    PANEL.validate_semantic_packet_current(packet, changed)

    def test_semantic_currentness_ignores_downgraded_only_candidate_churn(self) -> None:
        packet = _semantic_packet()
        current = copy.deepcopy(_live_semantic_audit())
        candidates = current["reference_content"]["semantic_advisories"][
            "candidates"
        ]
        downgraded_index = next(
            index
            for index, candidate in enumerate(candidates)
            if candidate.get("detector_status") != "candidate"
        )

        removed = copy.deepcopy(current)
        removed["reference_content"]["semantic_advisories"]["candidates"].pop(
            downgraded_index
        )
        PANEL.validate_semantic_packet_current(packet, removed)

        added = copy.deepcopy(current)
        synthetic = copy.deepcopy(candidates[downgraded_index])
        synthetic["candidate_id"] = "3" * 64
        added["reference_content"]["semantic_advisories"]["candidates"].append(
            synthetic
        )
        PANEL.validate_semantic_packet_current(packet, added)

    def test_semantic_axis_rereview_reopens_only_the_selected_current_axis(self) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        original = copy.deepcopy(audit)
        original_packet = PANEL.prepare_semantic_disposition_packet(
            audit=original,
            review_id="semantic-current-backlog",
            created_on="2026-07-17",
        )
        review_audit = PANEL._semantic_audit_for_axis_rereview(audit, ["root"])
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=review_audit,
            review_id="semantic-root-detector-rereview",
            created_on="2026-07-17",
        )

        self.assertEqual(original, audit)
        self.assertGreater(
            packet["panel_contract"]["required_axis_target_counts"]["root"], 0
        )
        self.assertEqual(
            original_packet["panel_contract"]["required_axis_target_counts"][
                "reference"
            ],
            packet["panel_contract"]["required_axis_target_counts"]["reference"],
        )
        PANEL.validate_semantic_packet_current(packet, audit)

    def test_semantic_application_binds_exact_majority_to_current_entries(self) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        with _current_semantic_application_fixture(audit) as fixture:
            result = PANEL.validate_semantic_decision_application(audit)
            self.assertEqual("current", result["status"])
            self.assertEqual(
                len(fixture["decision"]["semantic_decisions"]),
                result["target_count"],
            )
            self.assertEqual(result["target_count"], result["applied_count"])
            self.assertEqual(0, result["completed_rewrite_count"])

            target = fixture["decision"]["semantic_decisions"][0]
            semantic = audit[f"{target['axis']}_content"]["semantic_advisories"]
            entry = next(
                row
                for row in semantic["disposition_contract"]["entries"]
                if row["candidate_id"] == target["candidate_id"]
            )
            entry["disposition"] = next(
                disposition
                for disposition in sorted(PANEL.SEMANTIC_DISPOSITIONS)
                if disposition != target["winning_disposition"]
            )
            entry["record_fingerprint"] = (
                PANEL.panel_contracts.semantic_disposition_record_fingerprint(
                    target["axis"], entry
                )
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError, "disposition mismatch"
            ):
                PANEL.validate_semantic_decision_application(audit)

    def test_historical_schema1_semantic_attestation_cannot_authorize_currentness(self) -> None:
        config = AUDIT.load_yaml_file(
            ROOT / "config/skill-content-exceptions.yaml"
        )
        self.assertNotIn("semantic_disposition_application", config)

        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            fixed = (
                validation_root
                / PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
            )
            fixed.parent.mkdir(parents=True)
            _write_json(fixed, _historical_schema1_semantic_selector())
            with mock.patch.object(PANEL, "ROOT", validation_root), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "compact schema 2",
            ):
                PANEL.validate_semantic_decision_application(
                    copy.deepcopy(_live_semantic_audit())
                )

    def test_semantic_detector_v1_compatibility_is_one_exact_row(self) -> None:
        historical = _historical_schema1_semantic_selector()
        fixed = json.loads(
            (
                ROOT
                / PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
            ).read_text(encoding="utf-8")
        )
        rows = PANEL.panel_contracts.semantic_detector_compatibility_rows()
        self.assertEqual(1, len(rows))
        row = rows[0]
        expected_row = {
            "compatibility_id": "semantic-015be10a-detector-contract-v1",
            "review_id": "semantic-015be10a-final-prep",
            "legacy_source_fingerprints": {
                "reference_candidate_manifest": (
                    "dd03e7b80fe661d9db293db3d725706cd44a43ef7820de90452e22120e67638b"
                ),
                "reference_detector_contract": (
                    "bb6182108495b202f41d3ca0d73cabe8e62f7433b54fe233d61fc4dcb7d4c06e"
                ),
                "root_candidate_manifest": (
                    "8af1bbe28abcec952f7e52704f377324778002e2343a108fa3e2d0533ec7c919"
                ),
                "root_detector_contract": (
                    "1ed220a953b74fd6d4e4594660999b53064177c885841ca744ca1dd06caf146d"
                ),
            },
            "current_source_fingerprints": {
                "reference_candidate_manifest": (
                    "dd03e7b80fe661d9db293db3d725706cd44a43ef7820de90452e22120e67638b"
                ),
                "reference_detector_contract": (
                    "b30afbeafb68bb21ade261d0ada1698865ccef20327dac0fe8edca4138ed1fcb"
                ),
                "root_candidate_manifest": (
                    "8af1bbe28abcec952f7e52704f377324778002e2343a108fa3e2d0533ec7c919"
                ),
                "root_detector_contract": (
                    "1553aac6b6640674967a676ff192ea933bd788a27b197dd8d8f0619f895564f0"
                ),
            },
            "legacy_detector_contracts": {
                "root_detector_contract": (
                    "1ed220a953b74fd6d4e4594660999b53064177c885841ca744ca1dd06caf146d"
                ),
                "reference_detector_contract": (
                    "bb6182108495b202f41d3ca0d73cabe8e62f7433b54fe233d61fc4dcb7d4c06e"
                ),
            },
            "current_detector_contracts": {
                "root_detector_contract": (
                    "1553aac6b6640674967a676ff192ea933bd788a27b197dd8d8f0619f895564f0"
                ),
                "reference_detector_contract": (
                    "b30afbeafb68bb21ade261d0ada1698865ccef20327dac0fe8edca4138ed1fcb"
                ),
            },
            "review_contract_fingerprint": (
                "6f9618afabdc84a4e39a6cfe30b24b4b7b22f431f4d77a6337923af82f43069e"
            ),
            "target_count": 197,
            "axis_counts": {"reference": 121, "root": 76},
        }
        self.assertEqual(expected_row, row)
        current = copy.deepcopy(expected_row["current_source_fingerprints"])
        mode = PANEL._semantic_source_fingerprint_selector_mode(
            selector_fingerprints=historical["source_fingerprints"],
            current_fingerprints=current,
            review_id=historical["review_id"],
            review_contract_fingerprint=historical[
                "review_contract_fingerprint"
            ],
            target_count=historical["target_count"],
            axis_counts=historical["axis_counts"],
        )
        self.assertEqual("compatibility", mode)

        self.assertEqual(2, fixed["schema_version"])
        self.assertEqual(
            {"reference_detector_contract", "root_detector_contract"},
            set(fixed["detector_contract_fingerprints"]),
        )
        detector_keys = {
            "reference_detector_contract",
            "root_detector_contract",
        }
        self.assertTrue(
            all(
                re.fullmatch(r"[0-9a-f]{64}", digest)
                for digest in fixed["detector_contract_fingerprints"].values()
            )
        )
        live_audit = copy.deepcopy(_live_semantic_audit())
        root_semantic, reference_semantic = PANEL._semantic_audit_sections(
            live_audit
        )
        live_fingerprints = PANEL._semantic_source_fingerprints(
            live_audit,
            root_semantic=root_semantic,
            reference_semantic=reference_semantic,
        )
        self.assertNotEqual(
            fixed["detector_contract_fingerprints"],
            {key: live_fingerprints[key] for key in sorted(detector_keys)},
        )
        current_mode = PANEL._semantic_source_fingerprint_selector_mode(
            selector_fingerprints=fixed["detector_contract_fingerprints"],
            current_fingerprints=live_fingerprints,
            review_id=fixed["review_id"],
            review_contract_fingerprint=fixed[
                "review_contract_fingerprint"
            ],
            target_count=len(fixed["findings"]),
            axis_counts={
                axis: sum(item["axis"] == axis for item in fixed["findings"])
                for axis in sorted(PANEL.SEMANTIC_AXES)
            },
        )
        self.assertIsNone(current_mode)

        direct = PANEL._semantic_source_fingerprint_selector_mode(
            selector_fingerprints=current,
            current_fingerprints=current,
            review_id="future-direct-v1",
            review_contract_fingerprint="0" * 64,
            target_count=197,
            axis_counts={"reference": 121, "root": 76},
        )
        self.assertEqual("direct-v1", direct)

        mutations = []
        arbitrary = copy.deepcopy(historical["source_fingerprints"])
        arbitrary["root_detector_contract"] = "a" * 64
        mutations.append(arbitrary)
        mixed = copy.deepcopy(historical["source_fingerprints"])
        mixed["root_detector_contract"] = current["root_detector_contract"]
        mutations.append(mixed)
        nibble = copy.deepcopy(historical["source_fingerprints"])
        nibble["reference_detector_contract"] = (
            nibble["reference_detector_contract"][:-1] + "0"
        )
        mutations.append(nibble)
        legacy9 = {
            key: "a" * 64
            for key in PANEL.panel_contracts.SEMANTIC_DISPOSITION_LEGACY_SOURCE_FINGERPRINT_KEYS
        }
        mutations.append(legacy9)
        for selector in mutations:
            self.assertIsNone(
                PANEL._semantic_source_fingerprint_selector_mode(
                    selector_fingerprints=selector,
                    current_fingerprints=current,
                    review_id=historical["review_id"],
                    review_contract_fingerprint=historical[
                        "review_contract_fingerprint"
                    ],
                    target_count=historical["target_count"],
                    axis_counts=historical["axis_counts"],
                )
            )

        candidate_mismatch = copy.deepcopy(current)
        candidate_mismatch["root_candidate_manifest"] = "f" * 64
        self.assertIsNone(
            PANEL._semantic_source_fingerprint_selector_mode(
                selector_fingerprints=historical["source_fingerprints"],
                current_fingerprints=candidate_mismatch,
                review_id=historical["review_id"],
                review_contract_fingerprint=historical[
                    "review_contract_fingerprint"
                ],
                target_count=historical["target_count"],
                axis_counts=historical["axis_counts"],
            )
        )

        future = copy.deepcopy(current)
        future["root_detector_contract"] = "f" * 64
        self.assertIsNone(
            PANEL._semantic_source_fingerprint_selector_mode(
                selector_fingerprints=historical["source_fingerprints"],
                current_fingerprints=future,
                review_id=historical["review_id"],
                review_contract_fingerprint=historical[
                    "review_contract_fingerprint"
                ],
                target_count=historical["target_count"],
                axis_counts=historical["axis_counts"],
            )
        )

    def test_semantic_application_uses_only_the_safe_canonical_fixed_path(self) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        with tempfile.TemporaryDirectory() as raw:
            validation_root = Path(raw)
            with mock.patch.object(PANEL, "ROOT", validation_root):
                with self.assertRaisesRegex(PANEL.PanelReviewError, "invalid"):
                    PANEL.validate_semantic_decision_application(audit)

            fixed = (
                validation_root
                / PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
            )
            fixed.parent.mkdir(parents=True)
            fixed.symlink_to(validation_root / "outside.json")
            with mock.patch.object(PANEL, "ROOT", validation_root):
                with self.assertRaisesRegex(PANEL.PanelReviewError, "invalid"):
                    PANEL.validate_semantic_decision_application(audit)

    def test_auditor_projects_one_stable_application_error_to_formal_gate_only(
        self,
    ) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        with _current_semantic_application_fixture(audit) as fixture:
            current = PANEL.validate_semantic_decision_application(audit)
            self.assertEqual("current", current["status"])
            self.assertEqual(
                len(fixture["decision"]["semantic_decisions"]),
                current["target_count"],
            )

            fixed = (
                fixture["root"]
                / PANEL.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
            )
            fixed.unlink()
            root, reference, report = (
                AUDIT._collect_semantic_content_with_application()
            )
            self.assertEqual("invalid", report["status"])
            self.assertEqual(
                AUDIT.SEMANTIC_DISPOSITION_APPLICATION_ERROR_ID,
                report["error"]["id"],
            )
            for content in (root, reference):
                self.assertNotIn(
                    AUDIT.SEMANTIC_DISPOSITION_APPLICATION_ERROR_ID,
                    content["semantic_advisories"]["disposition_contract"][
                        "errors"
                    ],
                )
            gate_status = AUDIT._audit_gate_status(
                {
                    "ai_readability": {
                        "summary": {"hard_gate_ready": True}
                    },
                    "root_content": root,
                    "reference_content": reference,
                    "semantic_disposition_application": report,
                },
                {"content_blockers": 0},
                selected_gate="formal-release",
            )
            self.assertNotIn(
                report["error"], gate_status["authoring"]["blockers"]
            )
            self.assertEqual(
                "blocked", gate_status["formal_release"]["status"]
            )
            self.assertIn(
                report["error"],
                gate_status["formal_release"]["blockers"],
            )

    def test_reviewed_rewrite_removal_is_self_contained_but_entry_retention_fails(self) -> None:
        audit = copy.deepcopy(_live_semantic_audit())
        root_semantic = audit["root_content"]["semantic_advisories"]
        candidates_by_id = {
            candidate["candidate_id"]: candidate
            for candidate in root_semantic["candidates"]
        }
        candidate_id = next(
            entry["candidate_id"]
            for entry in root_semantic["disposition_contract"]["entries"]
            if entry["candidate_id"] in candidates_by_id
            and not PANEL._semantic_entry_mismatches(
                axis="root",
                candidate=candidates_by_id[entry["candidate_id"]],
                entry=entry,
            )
        )
        target_id = f"root:{candidate_id}"
        with _current_semantic_application_fixture(
            audit, winner_overrides={target_id: "rewrite"}
        ) as fixture:
            target = next(
                row
                for row in fixture["decision"]["semantic_decisions"]
                if row["target_id"] == target_id
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "remains current"):
                PANEL.validate_semantic_decision_application(audit)

            semantic = audit[f"{target['axis']}_content"]["semantic_advisories"]
            original_entry = next(
                copy.deepcopy(row)
                for row in semantic["disposition_contract"]["entries"]
                if row["candidate_id"] == target["candidate_id"]
            )
            semantic["candidates"] = [
                row
                for row in semantic["candidates"]
                if row["candidate_id"] != target["candidate_id"]
            ]
            semantic["disposition_contract"]["entries"] = [
                row
                for row in semantic["disposition_contract"]["entries"]
                if row["candidate_id"] != target["candidate_id"]
            ]
            PANEL.validate_semantic_decision_application(audit)

            semantic["disposition_contract"]["entries"].append(original_entry)
            semantic["disposition_contract"]["entries"].sort(
                key=lambda row: row["candidate_id"]
            )
            with self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "rewrite target remains current",
            ):
                PANEL.validate_semantic_decision_application(audit)

    def test_semantic_ballot_is_full_coverage_no_abstention_and_kind_specific(self) -> None:
        packet = _semantic_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _semantic_ballot(packet, digest, voter=1)
            PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            missing = copy.deepcopy(ballot)
            missing["semantic_votes"].pop()
            with self.assertRaisesRegex(PANEL.PanelReviewError, "coverage"):
                PANEL.validate_ballot(packet, missing, packet_sha256=digest)

            duplicate = copy.deepcopy(ballot)
            duplicate["semantic_votes"][1] = copy.deepcopy(
                duplicate["semantic_votes"][0]
            )
            with self.assertRaisesRegex(PANEL.PanelReviewError, "duplicate"):
                PANEL.validate_ballot(packet, duplicate, packet_sha256=digest)

            abstain = copy.deepcopy(ballot)
            abstain["semantic_votes"][0]["disposition"] = "abstain"
            with self.assertRaisesRegex(PANEL.PanelReviewError, "abstention"):
                PANEL.validate_ballot(packet, abstain, packet_sha256=digest)

            stale = copy.deepcopy(ballot)
            stale["source_fingerprints"]["root_candidate_manifest"] = "0" * 64
            with self.assertRaisesRegex(PANEL.PanelReviewError, "stale"):
                PANEL.validate_ballot(packet, stale, packet_sha256=digest)

            readability_ballot = _ballot(_packet(), digest, voter=1)
            with self.assertRaisesRegex(PANEL.PanelReviewError, "fields"):
                PANEL.validate_ballot(
                    packet, readability_ballot, packet_sha256=digest
                )

    def test_semantic_time_bounded_exception_requires_owner_and_future_expiry(self) -> None:
        packet = _semantic_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            packet_path = Path(raw) / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot = _semantic_ballot(packet, digest, voter=1)
            vote = ballot["semantic_votes"][0]
            vote["disposition"] = "time-bounded-exception"
            vote["review_after"] = "2099-01-01"
            PANEL.validate_ballot(packet, ballot, packet_sha256=digest)

            missing_owner = copy.deepcopy(ballot)
            missing_owner["semantic_votes"][0]["decision_owner"] = ""
            with self.assertRaisesRegex(PANEL.PanelReviewError, "decision_owner"):
                PANEL.validate_ballot(
                    packet, missing_owner, packet_sha256=digest
                )

            expired = copy.deepcopy(ballot)
            expired["semantic_votes"][0]["review_after"] = "2026-07-16"
            with self.assertRaisesRegex(PANEL.PanelReviewError, "future expiry"):
                PANEL.validate_ballot(packet, expired, packet_sha256=digest)

            invalid_other = _semantic_ballot(packet, digest, voter=1)
            invalid_other["semantic_votes"][0]["review_after"] = "2099-01-01"
            with self.assertRaisesRegex(PANEL.PanelReviewError, "unless"):
                PANEL.validate_ballot(
                    packet, invalid_other, packet_sha256=digest
                )

    def test_semantic_rewrite_majority_preserves_all_rationales_without_ssot_entry(self) -> None:
        packet = _semantic_packet()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter, disposition in enumerate(
                ("rewrite", "rewrite", "valid-contextual-rule"), start=1
            ):
                ballot_path = root / f"semantic-expert-{voter}.json"
                ballot = _semantic_ballot(
                    packet,
                    digest,
                    voter=voter,
                    disposition=disposition,
                )
                _write_json(ballot_path, ballot)
                ballot_values.append((ballot_path, ballot))
            record = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )
            decision_path = root / "decision.json"
            _write_json(decision_path, record)
            PANEL.validate_decision_record(record, record_path=decision_path)

        first = record["semantic_decisions"][0]
        self.assertEqual("rewrite", first["winning_disposition"])
        self.assertEqual(3, len(first["ballot_rationales"]))
        self.assertEqual(
            3, len({row["rationale"] for row in first["ballot_rationales"]})
        )
        self.assertNotIn("ssot_entries", record)
        self.assertNotIn("disposition_entries", record)
        self.assertEqual(
            len(packet["semantic_targets"]),
            record["summary"]["semantic_dispositions"]["rewrite"],
        )

    def test_semantic_aggregate_is_permutation_invariant_and_attestable(self) -> None:
        audit = _semantic_audit_with_synthetic_delta()
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=audit,
            review_id="semantic-permutation-review",
            created_on="2026-07-16",
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            _write_json(packet_path, packet)
            digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            for voter, disposition in enumerate(
                (
                    "false-positive",
                    "valid-contextual-rule",
                    "valid-contextual-rule",
                ),
                start=1,
            ):
                path = root / f"semantic-expert-{voter}.json"
                value = _semantic_ballot(
                    packet,
                    digest,
                    voter=voter,
                    disposition=disposition,
                )
                _write_json(path, value)
                ballot_values.append((path, value))

            ordered = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on="2026-07-16",
            )
            permuted = PANEL.aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=[
                    ballot_values[2],
                    ballot_values[0],
                    ballot_values[1],
                ],
                decided_on="2026-07-16",
            )
            self.assertEqual(
                json.dumps(ordered, sort_keys=True, separators=(",", ":")),
                json.dumps(permuted, sort_keys=True, separators=(",", ":")),
            )
            decision_path = root / "decision.json"
            _write_json(decision_path, permuted)
            PANEL.validate_decision_record(
                permuted, record_path=decision_path
            )
            compact = PANEL._semantic_attestation_from_decision(
                permuted,
                decision_path=decision_path,
                audit=audit,
            )

        self.assertEqual(
            sorted(voter["voter_id"] for voter in permuted["voters"]),
            [voter["voter_id"] for voter in permuted["voters"]],
        )
        for decision in permuted["semantic_decisions"]:
            for field in ("supporting_voters", "dissenting_voters"):
                self.assertEqual(sorted(decision[field]), decision[field])
            self.assertEqual(
                sorted(
                    row["voter_id"]
                    for row in decision["ballot_rationales"]
                ),
                [
                    row["voter_id"]
                    for row in decision["ballot_rationales"]
                ],
            )
        self.assertEqual(
            sorted(reviewer["voter_id"] for reviewer in compact["reviewers"]),
            [reviewer["voter_id"] for reviewer in compact["reviewers"]],
        )
        for finding in compact["findings"]:
            self.assertEqual(
                sorted(vote["voter_id"] for vote in finding["votes"]),
                [vote["voter_id"] for vote in finding["votes"]],
            )


if __name__ == "__main__":
    unittest.main()
