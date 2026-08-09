from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from . import test_expert_panel_review as panel_fixtures
from . import test_professional_completeness_schema3 as schema3_fixtures


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PANEL = _load("professionalism_panel_fixture", "scripts/expert_panel_review.py")
REGRESSION = _load(
    "professionalism_panel_regression_fixture",
    "scripts/validate-professionalism-regression.py",
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
        return panel_fixtures._professional_ballot(
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


class ProfessionalismExpertPanelTests(unittest.TestCase):
    def test_shared_fixture_uses_current_unittest_package(self) -> None:
        expected_module = f"{__package__}.test_expert_panel_review"
        self.assertEqual(expected_module, panel_fixtures.__name__)
        self.assertIs(panel_fixtures, sys.modules[expected_module])
        self.assertIs(
            panel_fixtures.PANEL,
            sys.modules[panel_fixtures.PANEL.__name__],
        )

    def test_regression_loader_preserves_current_readability(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config = REGRESSION.load_yaml_file(config_path)
        attestation = config["readability_review_attestation"]
        record, _path, evidence = REGRESSION._load_dual_panel_record(
            config_path,
            attestation["panel_record"],
            field_name="readability_review_attestation",
            expected_kind=PANEL.DECISION_KIND,
        )
        self.assertEqual(2, record["schema_version"])
        self.assertEqual(5, len(evidence))

    def test_regression_loader_preserves_current_professional(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config = REGRESSION.load_yaml_file(config_path)
        attestation = config["professional_completeness_review_attestation"]
        record, _path, evidence = REGRESSION._load_dual_panel_record(
            config_path,
            attestation["panel_record"],
            field_name="professional_completeness_review_attestation",
            expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        )
        self.assertEqual(3, record["schema_version"])
        self.assertGreater(len(evidence), len(record["voters"]))

    def test_current_schema3_review_cost_is_artifact_relative(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config = REGRESSION.load_yaml_file(config_path)
        attestation = config["professional_completeness_review_attestation"]
        record, _path, _evidence = REGRESSION._load_dual_panel_record(
            config_path,
            attestation["panel_record"],
            field_name="professional_completeness_review_attestation",
            expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        )
        _packet_path, packet = REGRESSION._read_professional_artifact_reference(
            record["packet"],
            label="tracked schema-3 Professional packet",
        )

        cost = REGRESSION._professional_schema3_review_cost(
            record,
            packet=packet,
        )

        target_count = len(packet["professional_targets"])
        expected_vote_count = PANEL.PANEL_SIZE * target_count
        expected_criterion_result_count = (
            expected_vote_count * len(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA)
        )
        self.assertEqual(PANEL.PROFESSIONAL_PACKAGE_COUNT, target_count)
        self.assertEqual(3, len(record["voters"]))
        self.assertEqual(expected_vote_count, cost["fresh_vote_count"])
        self.assertEqual(0, cost["carried_forward_vote_count"])
        self.assertEqual(expected_vote_count, cost["effective_vote_count"])
        self.assertEqual(
            expected_criterion_result_count,
            cost["fresh_criterion_result_count"],
        )
        self.assertEqual(
            0,
            cost["carried_forward_criterion_result_count"],
        )
        self.assertEqual(
            expected_criterion_result_count,
            cost["effective_criterion_result_count"],
        )
        self.assertGreater(cost["canonical_capsule_input_bytes_proxy"], 0)
        self.assertEqual(1_000_000, cost["input_ratio_ppm"])
        self.assertEqual(1_000_000, cost["required_only_input_ratio_ppm"])
        self.assertEqual(1_000_000, cost["source_material_coverage_ratio_ppm"])
        self.assertEqual("contract-change-full-review", cost["policy_status"])
        self.assertTrue(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=target_count,
                carried_forward_target_count=0,
            )
        )
        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                cost,
                fresh_target_count=86,
                carried_forward_target_count=103,
            )
        )

        forged_incremental = copy.deepcopy(cost)
        forged_incremental["policy_status"] = "incremental-reduced-input"
        self.assertFalse(
            REGRESSION._professional_review_cost_policy_satisfied(
                forged_incremental,
                fresh_target_count=0,
                carried_forward_target_count=target_count,
            )
        )

        malformed_partition = copy.deepcopy(record)
        malformed_partition["professional_decisions"].pop()
        with self.assertRaisesRegex(ValueError, "target partition"):
            REGRESSION._professional_schema3_review_cost(
                malformed_partition,
                packet=packet,
            )

        malformed_voters = copy.deepcopy(record)
        malformed_voters["voters"].append(
            copy.deepcopy(record["voters"][0])
        )
        malformed_voters["voters"][-1]["capsule_input_blocks_proxy"][0][
            "sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(ValueError, "conflicts across voters"):
            REGRESSION._professional_schema3_review_cost(
                malformed_voters,
                packet=packet,
            )

        malformed_input = copy.deepcopy(record)
        malformed_input["summary"]["review_cost"][
            "canonical_capsule_input_bytes_proxy"
        ] = 1
        with self.assertRaisesRegex(
            ValueError,
            "core review_cost does not match raw evidence",
        ):
            REGRESSION._professional_schema3_review_cost(
                malformed_input,
                packet=packet,
            )

        malformed_core_cost = copy.deepcopy(record)
        malformed_core_cost["summary"]["review_cost"][
            "effective_criterion_result_count"
        ] += 1
        with self.assertRaisesRegex(
            ValueError,
            "core review_cost does not match raw evidence",
        ):
            REGRESSION._professional_schema3_review_cost(
                malformed_core_cost,
                packet=packet,
            )

    def test_current_schema3_axis_is_current_and_accepted(self) -> None:
        config_path = ROOT / "config/professionalism-release-review.yaml"
        config_bytes = config_path.read_bytes()
        config = REGRESSION.load_yaml_file(config_path)
        evaluation_date = date.fromisoformat(config["reviewed_at"])
        self.assertEqual(date(2026, 8, 9), evaluation_date)
        attestation = config["professional_completeness_review_attestation"]
        record, _record_path, _evidence = REGRESSION._load_dual_panel_record(
            config_path,
            attestation["panel_record"],
            field_name="professional_completeness_review_attestation",
            expected_kind=PANEL.PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        )
        self.assertEqual("2026-08-09", record["decided_on"])
        result = REGRESSION._professional_completeness_review_axis(
            config_path,
            config_bytes=config_bytes,
            config_fingerprint=hashlib.sha256(config_bytes).hexdigest(),
            attestation=attestation,
            current_packet=REGRESSION._current_professional_completeness_packet(),
            evaluation_date=evaluation_date,
        )

        target_count = PANEL.PROFESSIONAL_PACKAGE_COUNT
        expected_vote_count = PANEL.PANEL_SIZE * target_count
        expected_criterion_result_count = (
            expected_vote_count * len(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA)
        )
        self.assertEqual(record["decided_on"], result["attested_on"])
        self.assertLessEqual(
            date.fromisoformat(result["attested_on"]),
            evaluation_date,
        )
        with self.assertRaisesRegex(ValueError, "non-future ISO date"):
            REGRESSION._validated_iso_date(
                "not-a-date",
                label="test malformed decision date",
                evaluation_date=evaluation_date,
            )
        with self.assertRaisesRegex(ValueError, "non-future ISO date"):
            REGRESSION._validated_iso_date(
                "2026-08-10",
                label="test future decision date",
                evaluation_date=evaluation_date,
            )
        self.assertEqual(target_count, result["required_target_count"])
        self.assertEqual(target_count, result["applied_target_count"])
        self.assertEqual(target_count, result["fresh_target_count"])
        self.assertEqual(0, result["carried_forward_target_count"])
        self.assertEqual(3, result["reviewer_pool_size"])
        self.assertEqual(
            3,
            result["qualification_summary"]["fresh_reviewer_pool_size"],
        )
        self.assertEqual(
            2 * target_count,
            result["qualification_summary"]["effective_domain_vote_count"],
        )
        self.assertEqual(
            target_count,
            result["qualification_summary"][
                "effective_architecture_vote_count"
            ],
        )
        self.assertEqual(
            expected_vote_count,
            result["review_cost"]["fresh_vote_count"],
        )
        self.assertEqual(0, result["review_cost"]["carried_forward_vote_count"])
        self.assertEqual(
            expected_vote_count,
            result["review_cost"]["effective_vote_count"],
        )
        self.assertEqual(
            expected_criterion_result_count,
            result["review_cost"]["fresh_criterion_result_count"],
        )
        self.assertEqual(
            0,
            result["review_cost"]["carried_forward_criterion_result_count"],
        )
        self.assertEqual(
            expected_criterion_result_count,
            result["review_cost"]["effective_criterion_result_count"],
        )
        self.assertEqual(
            "contract-change-full-review",
            result["review_cost"]["policy_status"],
        )
        self.assertTrue(result["source_current"])
        self.assertTrue(result["review_contract_current"])
        self.assertTrue(result["review_plan_current"])
        self.assertTrue(result["review_binding_current"])
        self.assertTrue(result["provenance_current"])
        self.assertTrue(result["round_lifecycle_current"])
        self.assertTrue(result["evidence_contract_satisfied"])
        self.assertEqual(
            "panel-majority-pending-checkin", result["attestation_status"]
        )
        self.assertFalse(result["storage_current"])
        self.assertFalse(result["review_cost_current"])
        self.assertFalse(result["accepted_for_formal"])

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

    def _dual_config(
        self,
        *,
        readability_record: Path | None,
        readability_fingerprints: dict[str, str | None],
        completeness_record: Path | None = None,
    ) -> dict:
        readability_ref = (
            None
            if readability_record is None
            else {
                "path": readability_record.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(readability_record.read_bytes()).hexdigest(),
            }
        )
        completeness_ref = (
            None
            if completeness_record is None
            else {
                "path": completeness_record.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(completeness_record.read_bytes()).hexdigest(),
            }
        )
        return {
            "schema_version": 5,
            "review_owner": "changeforge-expert-panel-governance",
            "reviewed_at": "2026-07-16",
            "decisions": [],
            "readability_review_attestation": {
                "schema_version": 5,
                "panel_kind": PANEL.READABILITY_PANEL_KIND,
                "scope": "ai-readability-and-density",
                "decision_method": PANEL.DECISION_METHOD,
                "source_fingerprints": readability_fingerprints,
                "panel_record": readability_ref,
                "limitations": ["Static readability fixture."],
            },
            "professional_completeness_review_attestation": {
                "schema_version": 5,
                "panel_kind": PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                "scope": "professional-skill-packages",
                "decision_method": PANEL.DECISION_METHOD,
                "source_fingerprints": {
                    "professional_packages": (
                        "a" * 64 if completeness_record is not None else None
                    )
                },
                "panel_record": completeness_ref,
                "limitations": ["No completeness evidence in this fixture."],
            },
        }

    def test_dual_parser_preserves_stale_readability_and_blocks_missing_completeness(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            _config_path, record_path, _ballots, packet = self._fixture(Path(raw))
            data = self._dual_config(
                readability_record=record_path,
                readability_fingerprints=packet["source_fingerprints"],
            )
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
                    "summary": {"advisory_documents": 1, "blocker_findings": 0},
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
                    "source_fingerprints": {"professional_packages": "6" * 64},
                    "professional_targets": [
                        {"skill_id": f"skill-{index}", "package_fingerprint": "5" * 64}
                        for index in range(PANEL.PROFESSIONAL_PACKAGE_COUNT)
                    ],
                },
                evaluation_date=date(2026, 7, 16),
            )

            self.assertTrue(result["readability"]["decision_complete"])
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

    def test_dual_parser_rejects_cross_axis_decision_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            _config_path, record_path, _ballots, _packet = self._fixture(Path(raw))
            data = self._dual_config(
                readability_record=None,
                readability_fingerprints={
                    "reference_content": None,
                    "root_content": None,
                    "ai_readability": None,
                },
                completeness_record=record_path,
            )
            with self.assertRaisesRegex(ValueError, "wrong review axis"):
                REGRESSION._dual_expert_reviews_from_data(
                    Path(raw) / "dual-review.yaml",
                    data=data,
                    config_bytes=b"dual-fixture\n",
                    reference_fingerprint="9" * 64,
                    root_fingerprint="8" * 64,
                    ai_readability_fingerprint="7" * 64,
                    content_skills=[],
                    readability_content={
                        "summary": {"advisory_documents": 0, "blocker_findings": 0},
                        "documents": [],
                    },
                    current_completeness_packet={
                        "source_fingerprints": {"professional_packages": "6" * 64},
                        "professional_targets": [
                            {
                                "skill_id": f"skill-{index}",
                                "package_fingerprint": "5" * 64,
                            }
                            for index in range(PANEL.PROFESSIONAL_PACKAGE_COUNT)
                        ],
                    },
                    evaluation_date=date(2026, 7, 16),
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

    def test_release_gate_accepts_only_two_clean_axes_and_current_root(self) -> None:
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            self._formal_reviews(),
            {"semantic_lifecycle_formal_release_ready": True},
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_PASS, gate)
        self.assertEqual([], blockers)

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
        producer_panel = schema3_fixtures.PANEL
        packet = schema3_fixtures._bootstrap_packet()
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
                panel_fixtures._write_json(discovery_path, discovery)
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
                panel_fixtures._write_json(request_path, request)
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
                panel_fixtures._write_json(capsule_path, capsule)
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
            {"semantic_lifecycle_formal_release_ready": True},
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
            {"semantic_lifecycle_formal_release_ready": True},
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
            {"semantic_lifecycle_formal_release_ready": True},
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
            {"semantic_lifecycle_formal_release_ready": True},
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
            {"semantic_lifecycle_formal_release_ready": True},
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
            {"semantic_lifecycle_formal_release_ready": True},
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
            {"semantic_lifecycle_formal_release_ready": True},
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            {
                "readability-review-release-gate",
                "professional-completeness-review-release-gate",
            },
            {item.category for item in blockers},
        )

    def test_release_gate_blocks_root_bootstrap_after_two_clean_axes(self) -> None:
        gate, blockers = REGRESSION._release_gate(
            REGRESSION.AUTHORING_GATE_PASS,
            [],
            self._formal_reviews(),
            {
                "semantic_lifecycle_formal_release_ready": False,
                "semantic_lifecycle_status": "bootstrap-current",
                "semantic_lifecycle_comparison": {
                    "unclassified_count": None,
                },
            },
        )
        self.assertEqual(REGRESSION.RELEASE_GATE_FAIL, gate)
        self.assertEqual(
            ["root-disposition-lifecycle-release-record-required"],
            [item.category for item in blockers],
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
            attestation = {
                "schema_version": 5,
                "panel_kind": PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                "scope": "professional-skill-packages",
                "decision_method": PANEL.PROFESSIONAL_COMPLETENESS_DECISION_METHOD,
                "source_fingerprints": packet["source_fingerprints"],
                "panel_record": {
                    "path": decision_path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(decision_path.read_bytes()).hexdigest(),
                },
                "limitations": ["Temporary parser integration fixture."],
            }
            with mock.patch.object(
                REGRESSION,
                "_dual_storage_status",
                return_value=(True, None),
            ):
                result = REGRESSION._professional_completeness_review_axis(
                    root / "review.yaml",
                    config_bytes=b"fixture\n",
                    config_fingerprint="f" * 64,
                    attestation=attestation,
                    current_packet=packet,
                    evaluation_date=date(2026, 7, 16),
                )

        self.assertFalse(result["accepted_for_formal"])
        self.assertFalse(result["source_current"])
        self.assertEqual("panel-legacy-nonformal", result["attestation_status"])
        self.assertEqual(PANEL.PROFESSIONAL_PACKAGE_COUNT, result["applied_target_count"])
        self.assertEqual(0, result["correction_count"])
        self.assertEqual(
            ["all-professional-criteria-satisfied"],
            result["professional_dispositions"][0]["reason_codes"],
        )
        self.assertEqual(
            "accepted-current-professional-completeness",
            result["professional_dispositions"][0][
                "ordinary_criterion_disposition"
            ],
        )
        self.assertEqual(
            [],
            result["professional_dispositions"][0][
                "ordinary_criterion_defects"
            ],
        )

    def test_panel_decision_is_applied_but_pending_until_checked_in(self) -> None:
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
