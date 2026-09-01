from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = str(ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from validation_utils import extract_section_body, heading_entries  # noqa: E402


SCRIPT = ROOT / "scripts" / "validate-productization-assets.py"
PROFESSIONAL_REVIEW_COST_AUTHORITY_TITLE = "Professional Review Cost Authority"
PROFESSIONAL_REVIEW_COST_NUMERIC_PATTERNS = (
    r"min/sum/mean-milli/p95/max\s+`[0-9/]+`",
    r"input-ratio-ppm\s+`[0-9/]+`",
    r"case is\s+`\d+` fresh",
)


def _professional_review_cost_numeric_duplicates(section: str) -> list[str]:
    return [
        pattern
        for pattern in PROFESSIONAL_REVIEW_COST_NUMERIC_PATTERNS
        if re.search(pattern, section)
    ]


def _formal_round_policy_fingerprint() -> str:
    policy = json.loads(
        (ROOT / "src/control-model/core-contracts.json").read_text(
            encoding="utf-8"
        )
    )["final_goal_contract"]["professional_review_cost_fixtures"][
        "formal_round_policy"
    ]
    import hashlib

    return hashlib.sha256(
        json.dumps(
            policy,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


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


def _incremental_review_cost(cost: dict) -> dict:
    cost.update(
        {
            "fresh_vote_count": 3,
            "carried_forward_vote_count": 561,
            "fresh_criterion_result_count": 30,
            "carried_forward_criterion_result_count": 5610,
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


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_productization_assets", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _gif_fixture(*, frame_count: int) -> bytes:
    """Return a minimal structurally valid 1x1 GIF test fixture."""
    header = (
        b"GIF89a"
        b"\x01\x00\x01\x00"
        b"\x80\x00\x00"
        b"\x00\x00\x00\xff\xff\xff"
    )
    frame = (
        b"\x21\xf9\x04\x00\x01\x00\x00\x00"
        b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00"
        b"\x02\x02\x44\x01\x00"
    )
    return header + frame * frame_count + b"\x3b"


def _content_readiness_payload() -> dict:
    cost_authority = json.loads(
        (ROOT / "src/control-model/core-contracts.json").read_text(encoding="utf-8")
    )["final_goal_contract"]["professional_review_cost_fixtures"]
    readability_release_blocker = {
        "category": "readability-review-release-gate",
        "target": (
            "config/professionalism-release-review.yaml"
            "#readability_review_attestation"
        ),
        "message": "Formal release requires current readability review.",
        "severity": "error",
    }
    completeness_release_blocker = {
        "category": "professional-completeness-review-release-gate",
        "target": (
            "config/professionalism-release-review.yaml"
            "#professional_completeness_review_attestation"
        ),
        "message": "Formal release requires current professional completeness review.",
        "severity": "error",
    }
    reference_summary = {
        "readiness_scope": "reference-content",
        "source_fingerprint": "a" * 64,
        "strict_ready_basis": "reference-strict-v4",
        "structural_strict_ready": True,
        "semantic_triage_complete": True,
        "strict_ready": True,
    }
    root_summary = {
        "readiness_scope": "agent-facing-root-content",
        "source_fingerprint": "b" * 64,
        "strict_ready_basis": "root-strict-v5",
        "structural_strict_ready": True,
        "semantic_triage_complete": True,
        "strict_ready": True,
        "semantic_disposition_configured": 1,
    }
    reference = {
        "scope": "reference-content",
        "source_fingerprint": "a" * 64,
        "strict_ready_basis": "reference-strict-v4",
        "structural_strict_ready": True,
        "semantic_triage_complete": True,
        "strict_ready": True,
    }
    root = {
        "scope": "agent-facing-root-content",
        "source_fingerprint": "b" * 64,
        "strict_ready_basis": "root-strict-v5",
        "structural_strict_ready": True,
        "semantic_triage_complete": True,
        "strict_ready": True,
    }
    expert = {
        "readability": {
            "scope": "ai-readability-and-density",
            "panel_kind": "readability",
            "decision_complete": False,
            "storage_current": False,
            "source_current": False,
            "accepted_for_formal": False,
            "decision_method": "three-independent-experts-majority",
            "panel_review_id": None,
            "panel_size": 0,
            "attestation_status": "missing-evidence",
            "attestation_source": (
                "config/professionalism-release-review.yaml"
                "#readability_review_attestation"
            ),
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": None,
            "attestation_config_fingerprint": "c" * 64,
            "source_fingerprints": {
                "readability_target_manifest": None,
                "readability_detector_contract": None,
                "actionability_detector_contract": None,
            },
            "current_source_fingerprints": {
                "readability_target_manifest": "a" * 64,
                "readability_detector_contract": "b" * 64,
                "actionability_detector_contract": "f" * 64,
            },
            "attested_by": None,
            "attested_on": None,
            "evidence": [],
            "density_dispositions": [],
            "readability_dispositions": [],
            "actionability_dispositions": [],
            "required_density_disposition_count": 0,
            "applied_density_disposition_count": 0,
            "required_readability_disposition_count": 0,
            "applied_readability_disposition_count": 0,
            "required_actionability_disposition_count": 0,
            "applied_actionability_disposition_count": 0,
            "accepted_current_actionability_count": None,
            "detector_false_positive_count": None,
            "rewrite_required_count": None,
            "tracked_tightening_count": None,
            "blocker_count": 0,
            "limitations": ["No readability panel evidence is configured."],
        },
        "professional_completeness": {
            "scope": "professional-skill-packages",
            "panel_kind": "professional-completeness",
            "decision_complete": False,
            "storage_current": False,
            "source_current": False,
            "accepted_for_formal": False,
            "decision_method": "per-skill-qualified-reviewer-pool-domain-critical-fail-closed",
            "panel_review_id": None,
            "panel_size": 0,
            "reviewer_pool_size": 0,
            "attestation_status": "missing-evidence",
            "attestation_source": (
                "config/professionalism-release-review.yaml"
                "#professional_completeness_review_attestation"
            ),
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": None,
            "attestation_config_fingerprint": "c" * 64,
            "source_fingerprints": {},
            "current_source_fingerprints": {},
            "attested_by": None,
            "attested_on": None,
            "evidence": [],
            "professional_dispositions": [],
            "evidence_contract_satisfied": False,
            "qualification_summary": None,
            "evidence_summary": None,
            "review_contract_fingerprint": None,
            "current_review_contract_fingerprint": "7" * 64,
            "review_contract_current": False,
            "review_plan_fingerprint": None,
            "current_review_plan_fingerprint": None,
            "review_plan_current": False,
            "review_binding_current": False,
            "provenance_current": False,
            "round_lifecycle_current": False,
            "round_lifecycle": {
                "status": "no-schema3-current-decision",
                "round_count": 0,
                "chain_depth": 0,
                "head_decision": None,
                "current_decision_is_head": False,
                "errors": [],
                "limitations": [
                    "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted."
                ],
            },
            "review_cost_current": False,
            "review_cost": None,
            "required_target_count": 188,
            "fresh_target_count": 0,
            "carried_forward_target_count": 0,
            "applied_target_count": 0,
            "accepted_current_count": None,
            "correction_count": None,
            "unresolved_professional_disagreement_count": None,
            "limitations": [
                "No professional-completeness panel evidence is configured."
            ],
        },
        "deprecated_expert_content_review_complete": False,
    }
    return {
        "schema_version": 3,
        "authoring_gate": "current-contract-pass",
        "release_gate": "release-not-ready",
        "baseline_comparison": "not-numerically-comparable",
        "content_audit_summary": {
            "skill_detector_fingerprint": "7" * 64,
            "review_states": {"KEEP": 188},
            "review_reasons": {
                "classification_block": 0,
                "ai_readability_hard_fail": 0,
                "ai_readability_compound_bullet": 0,
                "classification_tighten_body": 0,
                "ai_readability_tighten": 0,
                "ai_readability_review_as_complex": 0,
                "classification_review_density": 0,
                "professional_governed_lines_over_80": 0,
                "professional_projection_pushes_physical_lines_over_80": 0,
                "weak_front_loaded_action": 0,
                "control_boilerplate_risk": 0,
                "actionable_duplicate_content": 0,
                "description_authoring_advisory": 0,
                "split_candidate": 0,
            },
        },
        "ai_readability_summary": {
            "source_fingerprint": "f" * 64,
            "hard_gate_ready": True,
        },
        "reference_content_summary": reference_summary,
        "root_content_summary": root_summary,
        "content_readiness": {
            "schema_version": 10,
            "reference": reference,
            "root": root,
            "expert": expert,
            "aggregate": {
                "structural_strict_ready": True,
                "semantic_triage_complete": True,
                "readability_review_current": False,
                "professional_completeness_review_current": False,
            },
        },
        "coverage_gate_summary": {
            "source": "professional-coverage-matrix.json",
            "policy": {
                "source": "config/professionalism-release-review.yaml",
                "decision_id": "release-critical-professional-coverage",
                "decision_schema_version": 1,
                "fingerprint": {"algorithm": "sha256", "value": "d" * 64},
                "required_skill_count": 11,
            },
            "required_skill_count": 11,
            "pass_count": 11,
            "fail_count": 0,
            "not_required_count": 152,
            "failing_skills": [],
            "status": "pass",
        },
        "professional_review_cost_fixtures": {
            "schema_version": 1,
            "status": "pass",
            "unchanged": {
                "fresh_target_count": 0,
                "carried_forward_target_count": 188,
                "input_ratio_ppm": 0,
            },
            "routing_neutral_isolated_material_binding_sensitivity": {
                "case_count": 188,
                "full_rereview_deduplicated_capsule_input_bytes_proxy": 100_000_000,
                "fresh_target_count": {
                    "min": 3,
                    "sum": 3240,
                    "mean_milli": 17234,
                    "p95": 35,
                    "max": cost_authority["thresholds"][
                        "maximum_fresh_target_count"
                    ],
                },
                "input_ratio_ppm": {
                    "min": 1000,
                    "sum": 18_900_000,
                    "mean": 100_531,
                    "p95": 150_000,
                    "max": 200_000,
                },
                "named_isolated_case": {
                    "skill_id": "acceptance-criteria-builder",
                    "fresh_target_count": 8,
                    "carried_forward_target_count": 180,
                    "canonical_capsule_input_bytes_proxy": 10_000_000,
                    "input_ratio_ppm": 100_000,
                },
            },
            "representative_routing_adjacency_mutation": {
                "skill_id": "acceptance-criteria-builder",
                "fresh_target_ids": ["acceptance-criteria-builder"],
                "carried_forward_target_count": 187,
                "reason_codes": ["adjacency-review-binding-changed"],
                "cost_threshold_applied": False,
            },
            "review_contract_change": {
                "fresh_target_count": 188,
                "carried_forward_target_count": 0,
                "input_ratio_ppm": 1_000_000,
            },
            "thresholds": copy.deepcopy(cost_authority["thresholds"]),
            "limitations": [
                "Canonical effective discovery/request/final input-block bytes are a structural proxy; identical blocks are counted at most three times, while formal policy separately recomputes required-only source coverage and reviewer-added relationship/evidence metadata overhead; neither measure proves actual tokens, wall-clock time, subagent count, monetary cost, or reviewer behavior.",
                "Static qualification claims do not prove reviewer identity, credentials, or domain experience.",
                "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted.",
                "Routing-neutral isolated material-binding sensitivity keeps Registry, expertise, Reference paths and headings, adjacency ranking and selection unchanged and assumes an empty reviewer-added candidate union; real history-added dependencies or governance changes can require more review.",
            ],
        },
        "blockers": [],
        "release_blockers": [
            readability_release_blocker,
            completeness_release_blocker,
        ],
        "advisories": [],
    }


def _formal_expert_panel_release_manifest() -> dict:
    return {
        "schema_version": 1,
        "status": "current",
        "head_commit": "a" * 40,
        "artifacts": [
            {
                "axis": axis,
                "path": path,
                "external_sha256": digest * 64,
                "size_bytes": index,
                "review_id": f"{axis}-fixture",
                "verdict": verdict,
            }
            for index, (axis, path, verdict, digest) in enumerate(
                (
                    (
                        "readability",
                        "evals/expert-panel/readability.json",
                        "accepted-current-readability",
                        "a",
                    ),
                    (
                        "semantic-disposition",
                        "evals/expert-panel/semantic-disposition.json",
                        "accepted-current-semantic-disposition",
                        "b",
                    ),
                    (
                        "professional-completeness",
                        "evals/expert-panel/professional-completeness.json",
                        "accepted-current-professional-completeness",
                        "c",
                    ),
                ),
                start=1,
            )
        ],
        "verification_toolchain": {
            "head_commit_matches_current": True,
            "artifact_count": 3,
            "accepted_artifact_count": 3,
            "head_byte_equal_count": 3,
            "clean_artifact_count": 3,
        },
    }


def _set_readability_decision(report: dict, *, tracked: bool = False) -> None:
    axis = report["content_readiness"]["expert"]["readability"]
    dispositions = (
        [
            {
                "path": "src/foundation/capabilities/a/SKILL.md",
                "classification": "REVIEW_DENSITY",
                "disposition": "tracked-tightening",
                "rationale": "Majority requires this density to be tightened before release.",
            }
        ]
        if tracked
        else []
    )
    axis.update(
        {
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": not tracked,
            "panel_artifact_schema_version": 2,
            "panel_review_id": "readability-fixture",
            "panel_size": 3,
            "attestation_status": (
                "panel-majority-tracked-tightening"
                if tracked
                else "panel-majority-current"
            ),
            "source_fingerprints": dict(axis["current_source_fingerprints"]),
            "attested_by": "expert-panel:readability-fixture",
            "attested_on": "2026-07-16",
            "evidence": [{"path": "evals/readability.json", "sha256": "d" * 64}],
            "density_dispositions": dispositions,
            "actionability_dispositions": [],
            "required_density_disposition_count": len(dispositions),
            "applied_density_disposition_count": len(dispositions),
            "required_actionability_disposition_count": 0,
            "applied_actionability_disposition_count": 0,
            "accepted_current_actionability_count": 0,
            "detector_false_positive_count": 0,
            "rewrite_required_count": 0,
            "tracked_tightening_count": len(dispositions),
        }
    )
    report["content_readiness"]["aggregate"]["readability_review_current"] = not tracked


def _set_completeness_decision(
    report: dict,
    *,
    corrections: int = 0,
    applied: int = 188,
    status: str | None = None,
) -> None:
    axis = report["content_readiness"]["expert"]["professional_completeness"]
    dispositions = []
    for index in range(applied):
        correction = index < corrections
        reason = (
            "generic-knowledge-pollution"
            if correction
            else "all-professional-criteria-satisfied"
        )
        dispositions.append(
            {
                "skill_id": f"skill-{index:03d}",
                "package_material_binding": f"{index:064x}"[-64:],
                "review_unit_binding": f"{index + 200:064x}"[-64:],
                "disposition": (
                    "requires-professional-correction"
                    if correction
                    else "accepted-current-professional-completeness"
                ),
                "majority_disposition": (
                    "requires-professional-correction"
                    if correction
                    else "accepted-current-professional-completeness"
                ),
                "domain_critical_defects": [],
                "ordinary_criterion_disposition": (
                    "requires-professional-correction"
                    if correction
                    else "accepted-current-professional-completeness"
                ),
                "ordinary_criterion_defects": (
                    ["generic-knowledge-pollution"] if correction else []
                ),
                "reason_codes": [reason],
                "rationales": [
                    {
                        "voter_id": "expert-1",
                        "reason_code": reason,
                        "rationale": "The reviewer applied every required professional criterion.",
                    },
                    {
                        "voter_id": "expert-2",
                        "reason_code": reason,
                        "rationale": "The independent review reached the same package decision.",
                    },
                ],
                "review_dependencies": {
                    "skill_id": f"skill-{index:03d}",
                    "final_disposition": (
                        "requires-professional-correction"
                        if correction
                        else "accepted-current-professional-completeness"
                    ),
                    "evidence_complete": True,
                    "prior_target_vote_count": 3,
                    "required_candidate_ids": [
                        f"candidate-{candidate}" for candidate in range(5)
                    ],
                    "reviewer_added_candidate_ids_union": [],
                    "dependency_candidate_ids": [
                        f"candidate-{candidate}" for candidate in range(5)
                    ],
                },
                "evidence_metrics": {
                    "target_vote_count": 3,
                    "required_adjacency_candidate_count": 5,
                    "criterion_result_count": 30,
                    "criterion_anchor_binding_count": 30,
                    "criterion_assertion_count": 30,
                    "evidence_anchor_count": 6,
                    "examined_failure_mode_count": 6,
                    "examined_omission_candidate_count": 6,
                    "examined_adjacency_count": 15,
                    "examined_required_adjacency_count": 15,
                    "reviewer_added_adjacency_count": 0,
                    "proof_limit_count": 3,
                    "qualification_claim_count": 3,
                },
                "provenance": {
                    "mode": "fresh",
                    "origin": {
                        "origin_review_id": "completeness-fixture",
                        "origin_commit": "a" * 40,
                        "origin_verdict_digest": f"{index + 400:064x}"[-64:],
                    },
                },
                "target_decision_fingerprint": f"{index + 400:064x}"[-64:],
            }
        )
    formal = corrections == 0 and applied == 188 and status in {
        None,
        "panel-majority-current",
    }
    axis.update(
        {
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": formal,
            "panel_review_id": "completeness-fixture",
            "panel_size": 3,
            "reviewer_pool_size": 3,
            "decision_method": "exact-package-carry-forward-qualified-reviewer-pool-domain-critical-fail-closed",
            "attestation_status": status
            or (
                "panel-majority-corrections-required"
                if corrections
                else "panel-majority-current"
            ),
            "source_fingerprints": dict(axis["current_source_fingerprints"]),
            "attested_by": "expert-panel:completeness-fixture",
            "attested_on": "2026-07-16",
            "evidence": [{"path": "evals/completeness.json", "sha256": "e" * 64}],
            "professional_dispositions": dispositions,
            "panel_artifact_schema_version": 3,
            "evidence_contract_satisfied": True,
            "qualification_summary": {
                "covered_target_count": 188,
                "required_domain_experts_per_target": 2,
                "required_architecture_experts_per_target": 1,
                "per_target_panel_size": 3,
                "fresh_reviewer_pool_size": 3,
                "effective_domain_vote_count": 376,
                "effective_architecture_vote_count": 188,
            },
            "evidence_summary": {
                "target_vote_count": 564,
                "required_adjacency_candidate_count": 940,
                "criterion_result_count": 5640,
                "criterion_anchor_binding_count": 5640,
                "criterion_assertion_count": 5640,
                "evidence_anchor_count": 1128,
                "examined_failure_mode_count": 1128,
                "examined_omission_candidate_count": 1128,
                "examined_adjacency_count": 2820,
                "examined_required_adjacency_count": 2820,
                "reviewer_added_adjacency_count": 0,
                "proof_limit_count": 564,
                "qualification_claim_count": 564,
            },
            "review_contract_fingerprint": "7" * 64,
            "current_review_contract_fingerprint": "7" * 64,
            "review_contract_current": True,
            "review_plan_fingerprint": None,
            "current_review_plan_fingerprint": None,
            "review_plan_current": True,
            "review_binding_current": True,
            "provenance_current": True,
            "round_lifecycle_current": True,
            "round_lifecycle": {
                "status": "fixed-attestation-current",
                "round_count": 1,
                "chain_depth": 0,
                "head_decision": None,
                "current_decision_is_head": True,
                "errors": [],
                "limitations": [
                    "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted."
                ],
            },
            "review_cost_current": True,
            "review_cost": {
                "fresh_vote_count": 564,
                "carried_forward_vote_count": 0,
                "effective_vote_count": 564,
                "fresh_criterion_result_count": 5640,
                "carried_forward_criterion_result_count": 0,
                "effective_criterion_result_count": 5640,
                "canonical_capsule_input_bytes_proxy": 303,
                "full_rereview_deduplicated_capsule_input_bytes_proxy": 300,
                "input_ratio_ppm": 1_010_000,
                "required_only_capsule_input_bytes_proxy": 300,
                "required_only_input_ratio_ppm": 1_000_000,
                "required_only_source_material_input_bytes_proxy": 100,
                "source_material_input_bytes_proxy": 100,
                "full_rereview_source_material_input_bytes_proxy": 100,
                "source_material_coverage_ratio_ppm": 1_000_000,
                "reviewer_added_source_material_input_bytes_proxy": 0,
                "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": 3,
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 15_000,
                "reviewer_added_request_count": 3,
                "reviewer_added_unique_relationship_count": 1,
                "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 200_000,
                "formal_round_policy_fingerprint": _formal_round_policy_fingerprint(),
                "maximum_origin_depth": 0,
                "plan_lineage_depth": 0,
                "policy_status": "bootstrap-full-review",
                "limitations": [
                    "Canonical effective discovery/request/final input-block bytes are a structural proxy; identical blocks are counted at most three times, while formal policy separately recomputes required-only source coverage and reviewer-added relationship/evidence metadata overhead; neither measure proves actual tokens, wall-clock time, subagent count, monetary cost, or reviewer behavior.",
                    "Static qualification claims do not prove reviewer identity, credentials, or domain experience.",
                    "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted.",
                ],
            },
            "fresh_target_count": 188,
            "carried_forward_target_count": 0,
            "applied_target_count": applied,
            "accepted_current_count": applied - corrections,
            "correction_count": corrections,
            "unresolved_professional_disagreement_count": 0,
        }
    )
    report["content_readiness"]["aggregate"][
        "professional_completeness_review_current"
    ] = formal


def _set_compact_completeness_decision(
    report: dict, *, carried: bool = False
) -> None:
    _set_completeness_decision(report)
    axis = report["content_readiness"]["expert"]["professional_completeness"]
    for index, disposition in enumerate(axis["professional_dispositions"]):
        disposition["provenance"] = {
            "mode": "carried" if carried else "fresh",
            "origin": {
                "origin_review_id": (
                    "professional-completeness-origin"
                    if carried
                    else axis["panel_review_id"]
                ),
                "origin_commit": "a" * 40,
                "origin_verdict_digest": disposition[
                    "target_decision_fingerprint"
                ],
            },
        }
    axis.update(
        {
            "review_plan_fingerprint": None,
            "current_review_plan_fingerprint": None,
            "round_lifecycle": {
                "status": "fixed-attestation-current",
                "round_count": 1,
                "chain_depth": 1 if carried else 0,
                "head_decision": None,
                "current_decision_is_head": True,
                "errors": [],
                "limitations": [
                    "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted."
                ],
            },
        }
    )
    if carried:
        axis["reviewer_pool_size"] = 0
        axis["qualification_summary"]["fresh_reviewer_pool_size"] = 0
        axis["fresh_target_count"] = 0
        axis["carried_forward_target_count"] = 188
        axis["review_cost"].update(
            {
                "fresh_vote_count": 0,
                "carried_forward_vote_count": 564,
                "fresh_criterion_result_count": 0,
                "carried_forward_criterion_result_count": 5640,
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


class StaticProductizationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _professional_review_cost_authority_section(
        self, markdown: str
    ) -> str:
        matches = [
            entry
            for entry in heading_entries(markdown)
            if entry[2].casefold()
            == PROFESSIONAL_REVIEW_COST_AUTHORITY_TITLE.casefold()
        ]
        self.assertEqual(1, len(matches), matches)
        section = extract_section_body(
            markdown,
            PROFESSIONAL_REVIEW_COST_AUTHORITY_TITLE,
        )
        if section is None:
            self.fail("professional review cost authority section is missing")
        return section

    def _write_reports(self, root: Path) -> None:
        contract_target = root / "src/control-model/core-contracts.json"
        contract_target.parent.mkdir(parents=True, exist_ok=True)
        contract_target.write_bytes(
            (ROOT / "src/control-model/core-contracts.json").read_bytes()
        )
        limits = [
            "Fixtures do not prove wall-clock performance, real-host accuracy, "
            "or the installed user experience."
        ]
        for relative, (field, value) in self.module.STATIC_REPORT_CONTRACTS.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                field: value,
                "evidence_scope": self.module.STATIC_REPORT_EVIDENCE_SCOPES.get(
                    relative,
                    "deterministic-fixtures",
                ),
                "limitations": limits,
            }
            if relative in self.module.CONTENT_READINESS_REPORTS:
                payload.update(_content_readiness_payload())
                if relative == "reports/professionalism-regression-report.json":
                    payload["mode"] = "strict"
                    payload["strict"] = True
                    payload["summary"] = {
                        "blocker_count": 0,
                        "release_blocker_count": 2,
                    }
                else:
                    payload["release_claim"] = (
                        "deterministic source and captured-fixture contracts only"
                    )
            path.write_text(json.dumps(payload), encoding="utf-8")

    def _read_professionalism_reports(self, root: Path) -> dict[str, dict]:
        return {
            relative: json.loads((root / relative).read_text(encoding="utf-8"))
            for relative in self.module.CONTENT_READINESS_REPORTS
        }

    def _current_professionalism_artifacts(self) -> dict[str, bytes]:
        return {
            relative: (ROOT / relative).read_bytes()
            for relative in self.module.CONTENT_READINESS_REPORTS
        }

    def _write_current_professionalism_artifacts(self, root: Path) -> None:
        contract_target = root / "src/control-model/core-contracts.json"
        contract_target.parent.mkdir(parents=True, exist_ok=True)
        contract_target.write_bytes(
            (ROOT / "src/control-model/core-contracts.json").read_bytes()
        )
        for relative, content in self._current_professionalism_artifacts().items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def test_internally_consistent_current_contract_fail_static_report_is_valid(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_current_professionalism_artifacts(root)

            self.assertEqual([], self.module._static_report_errors(root))

    def test_current_contract_fail_static_report_remains_fail_closed(self) -> None:
        mutations = {
            "no-error-blocker": lambda report: (
                report.__setitem__("blockers", []),
                report["summary"].__setitem__("blocker_count", 0),
            ),
            "status-mismatch": lambda report: report.__setitem__(
                "status", "current-contract-pass"
            ),
            "release-ready": lambda report: report.__setitem__(
                "release_gate", "release-ready"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._write_current_professionalism_artifacts(root)
                path = root / "reports/professionalism-regression-report.json"
                report = json.loads(path.read_text(encoding="utf-8"))
                mutate(report)
                path.write_text(json.dumps(report), encoding="utf-8")

                self.assertTrue(self.module._static_report_errors(root), label)

    def test_stale_professional_axis_cannot_claim_current_evidence(self) -> None:
        def set_schema_three(axis: dict) -> None:
            axis["panel_artifact_schema_version"] = 3

        def set_qualification(axis: dict) -> None:
            axis["qualification_summary"] = {
                "covered_target_count": 188,
                "required_domain_experts_per_target": 2,
                "required_architecture_experts_per_target": 1,
                "per_target_panel_size": 3,
                "fresh_reviewer_pool_size": 0,
                "effective_domain_vote_count": 376,
                "effective_architecture_vote_count": 188,
            }

        def set_evidence(axis: dict) -> None:
            axis["evidence_summary"] = {
                "target_vote_count": 564,
                "required_adjacency_candidate_count": 0,
                "criterion_result_count": 5640,
                "criterion_anchor_binding_count": 5640,
                "criterion_assertion_count": 5640,
                "evidence_anchor_count": 1128,
                "examined_failure_mode_count": 1128,
                "examined_omission_candidate_count": 1128,
                "examined_adjacency_count": 0,
                "examined_required_adjacency_count": 0,
                "reviewer_added_adjacency_count": 0,
                "proof_limit_count": 564,
                "qualification_claim_count": 564,
            }

        mutations = {
            "current": lambda axis: axis.__setitem__("source_current", True),
            "schema-three": set_schema_three,
            "qualification": set_qualification,
            "evidence-564-5640": set_evidence,
            "applied-evidence": lambda axis: axis.__setitem__(
                "applied_target_count", 188
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._write_current_professionalism_artifacts(root)
                path = root / "reports/professionalism-regression-report.json"
                report = json.loads(path.read_text(encoding="utf-8"))
                axis = report["content_readiness"]["expert"][
                    "professional_completeness"
                ]
                mutate(axis)
                path.write_text(json.dumps(report), encoding="utf-8")

                self.assertTrue(self.module._static_report_errors(root), label)

    def test_static_reports_require_deterministic_scope_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            self.assertIn("reports/routing-eval.json", self.module.STATIC_REPORT_CONTRACTS)
            self.assertIn(
                "reports/installation-validation.json",
                self.module.STATIC_REPORT_CONTRACTS,
            )
            self.assertEqual(
                [], self.module._static_report_errors(root)
            )

            path = root / "reports/hookless-control-plane-eval.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["evidence_scope"] = "host-performance"
            report["limitations"] = []
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)
            self.assertTrue(any("evidence_scope" in error for error in errors), errors)
            self.assertTrue(any("non-empty limitations" in error for error in errors), errors)

    def test_routing_and_installation_reports_cannot_omit_limitations(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            for relative in (
                "reports/routing-eval.json",
                "reports/installation-validation.json",
            ):
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                report.pop("limitations")
                path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)
            self.assertTrue(any("routing-eval.json" in error for error in errors), errors)
            self.assertTrue(
                any("installation-validation.json" in error for error in errors), errors
            )

    def test_professionalism_reports_require_self_contained_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report.pop("root_content_summary")
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any("must contain root_content_summary" in error for error in errors),
                errors,
            )

    def test_professionalism_reports_require_closed_top_level_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["unexpected"] = True
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

            self.assertTrue(
                any("closed professionalism report envelope" in error for error in errors),
                errors,
            )

    def test_professionalism_reports_require_closed_skill_review_counts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_audit_summary"]["review_reasons"].pop(
                "weak_front_loaded_action"
            )
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

            self.assertTrue(
                any("review_reasons must be the complete closed" in error for error in errors),
                errors,
            )

    def test_professionalism_reports_reject_non_boolean_or_contradictory_axes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["semantic_triage_complete"] = "true"
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(any("must be a boolean" in error for error in errors), errors)

            self._write_reports(root)
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["structural_strict_ready"] = False
            report["content_readiness"]["root"]["structural_strict_ready"] = False
            report["content_readiness"]["aggregate"]["structural_strict_ready"] = False
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any("cannot pass while Root structural_strict_ready=false" in error for error in errors),
                errors,
            )

    def test_expert_false_is_required_but_does_not_block_authoring_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            self.assertEqual(
                [], self.module._static_report_errors(root)
            )
            readiness = json.loads(
                (
                    root / "reports/professionalism-regression-report.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("current-contract-pass", readiness["authoring_gate"])
            self.assertEqual("release-not-ready", readiness["release_gate"])

    def test_current_noncurrent_report_requires_no_professional_cost_evidence(
        self,
    ) -> None:
        reports = self._read_professionalism_reports(ROOT)
        self.assertEqual(
            {"reports/professionalism-regression-report.json"}, set(reports)
        )
        for report in reports.values():
            completeness = report["content_readiness"]["expert"][
                "professional_completeness"
            ]
            self.assertEqual("current-contract-fail", report["authoring_gate"])
            self.assertEqual("release-not-ready", report["release_gate"])
            self.assertTrue(report["blockers"])
            self.assertTrue(report["release_blockers"])
            self.assertEqual(
                [],
                self.module._content_readiness_errors(
                    "reports/professionalism-regression-report.json",
                    report,
                ),
            )
            applied_target_count = completeness["applied_target_count"]
            required_target_count = completeness["required_target_count"]
            self.assertEqual(
                self.module.PROFESSIONAL_PACKAGE_COUNT,
                required_target_count,
            )
            self.assertEqual(0, applied_target_count)
            self.assertEqual(0, completeness["fresh_target_count"])
            self.assertEqual(0, completeness["carried_forward_target_count"])
            self.assertEqual([], completeness["professional_dispositions"])
            self.assertIsNone(completeness["qualification_summary"])
            self.assertIsNone(completeness["evidence_summary"])
            self.assertIsNone(completeness["review_cost"])
            self.assertFalse(completeness["review_cost_current"])
            self.assertFalse(
                report["content_readiness"]["aggregate"][
                    "professional_completeness_review_current"
                ]
            )
            self.assertFalse(
                self.module._professional_completeness_formal_ready(
                    completeness
                )
            )

            fixture = report["professional_review_cost_fixtures"]
            sensitivity = fixture[
                "routing_neutral_isolated_material_binding_sensitivity"
            ]
            case_count = sensitivity["case_count"]
            self.assertEqual("formal-non-current", fixture["status"])
            self.assertEqual(required_target_count, case_count)

    def test_professional_report_semantic_envelope_rejects_tampers(
        self,
    ) -> None:
        mutations = {
            "unexpected-field": lambda axis: axis.__setitem__("unexpected", 1),
            "wrong-scope": lambda axis: axis.__setitem__("scope", "readability"),
            "wrong-kind": lambda axis: axis.__setitem__("panel_kind", "readability"),
            "non-boolean-currentness": lambda axis: axis.__setitem__(
                "source_current", "true"
            ),
            "invalid-status": lambda axis: axis.__setitem__(
                "attestation_status", "current"
            ),
            "invalid-schema-version": lambda axis: axis.__setitem__(
                "attestation_schema_version", "5"
            ),
            "contradictory-formal-acceptance": lambda axis: axis.update(
                {
                    "accepted_for_formal": True,
                    "source_current": False,
                }
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._write_current_professionalism_artifacts(root)
                for relative in self.module.CONTENT_READINESS_REPORTS:
                    path = root / relative
                    report = json.loads(path.read_text(encoding="utf-8"))
                    completeness = report["content_readiness"]["expert"][
                        "professional_completeness"
                    ]
                    before = (
                        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
                    ).encode("utf-8")
                    mutate(completeness)
                    after = (
                        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
                    ).encode("utf-8")
                    self.assertTrue(
                        before != after,
                        f"{label} must change the report bytes",
                    )
                    path.write_bytes(after)
                errors = self.module._static_report_errors(root)
                self.assertTrue(errors)

    def test_current_cost_status_cannot_be_rewritten_as_non_current(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_current_professionalism_artifacts(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                report["professional_review_cost_fixtures"][
                    "status"
                ] = "invalid"
                path.write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any(
                    "professional_review_cost_fixtures.status" in error
                    for error in errors
                ),
                errors,
            )

    def test_release_ready_claims_require_honest_blockers_and_current_state(
        self,
    ) -> None:
        readability_blocker = {
            "category": "readability-review-release-gate",
            "target": (
                "config/professionalism-release-review.yaml"
                "#readability_review_attestation"
            ),
            "message": "Formal release requires current readability review.",
            "severity": "error",
        }

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_current_professionalism_artifacts(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = copy.deepcopy(
                    json.loads(path.read_text(encoding="utf-8"))
                )
                readability = report["content_readiness"]["expert"][
                    "readability"
                ]
                readability["source_current"] = False
                readability["accepted_for_formal"] = False
                readability["attestation_status"] = "panel-majority-stale"
                report["content_readiness"]["aggregate"][
                    "readability_review_current"
                ] = False
                report["release_blockers"] = [readability_blocker]
                report["release_gate"] = "release-ready"
                if relative.endswith("professionalism-regression-report.json"):
                    report["summary"]["release_blocker_count"] = 1
                path.write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any("cannot be release-ready with release blockers" in error for error in errors),
                errors,
            )

            self._write_current_professionalism_artifacts(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = copy.deepcopy(
                    json.loads(path.read_text(encoding="utf-8"))
                )
                readability = report["content_readiness"]["expert"][
                    "readability"
                ]
                readability["source_current"] = False
                readability["accepted_for_formal"] = False
                readability["attestation_status"] = "panel-majority-stale"
                report["content_readiness"]["aggregate"][
                    "readability_review_current"
                ] = False
                report["release_gate"] = "release-ready"
                report["release_blockers"] = []
                if relative.endswith("professionalism-regression-report.json"):
                    report["summary"]["release_blocker_count"] = 0
                path.write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any(
                    "release_gate does not match authoring, readability review, "
                    "Professional Completeness review, and "
                    "current Semantic application readiness"
                    in error
                    for error in errors
                ),
                errors,
            )

    def test_release_gate_must_match_authoring_and_expert_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            release = root / "reports/professionalism-regression-report.json"
            report = json.loads(release.read_text(encoding="utf-8"))
            report["release_gate"] = "release-ready"
            report["release_blockers"] = []
            release.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

            self.assertTrue(
                any(
                    "release_gate does not match authoring, readability review, "
                    "Professional Completeness review, and "
                    "current Semantic application readiness"
                    in error
                    for error in errors
                ),
                errors,
            )
            self.assertTrue(
                any("readability release blocker count" in error for error in errors),
                errors,
            )

    def test_expert_attestation_status_and_schema_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_readiness"]["expert"]["readability"][
                "attestation_schema_version"
            ] = None
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

            self.assertTrue(
                any("attestation_schema_version" in error for error in errors),
                errors,
            )

    def test_schema_five_pending_readability_is_complete_but_not_formally_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                readability = report["content_readiness"]["expert"]["readability"]
                readability.update(
                    {
                        "decision_complete": True,
                        "storage_current": False,
                        "source_current": True,
                        "accepted_for_formal": False,
                        "panel_artifact_schema_version": 2,
                        "panel_review_id": "fixture-panel",
                        "panel_size": 3,
                        "attestation_status": "panel-majority-pending-checkin",
                        "source_fingerprints": {
                            "readability_target_manifest": "a" * 64,
                            "readability_detector_contract": "b" * 64,
                            "actionability_detector_contract": "f" * 64,
                        },
                        "attested_by": "expert-panel:fixture-panel",
                        "attested_on": "2026-07-16",
                        "evidence": [{"path": "evals/panel.json", "sha256": "e" * 64}],
                        "density_dispositions": [],
                        "readability_dispositions": [],
                        "actionability_dispositions": [],
                        "required_actionability_disposition_count": 0,
                        "applied_actionability_disposition_count": 0,
                        "accepted_current_actionability_count": 0,
                        "detector_false_positive_count": 0,
                        "rewrite_required_count": 0,
                        "tracked_tightening_count": 0,
                    }
                )
                path.write_text(json.dumps(report), encoding="utf-8")

            self.assertEqual(
                [], self.module._static_report_errors(root)
            )

    def test_fixed_storage_stale_and_pending_axes_are_fail_closed_nonformal(
        self,
    ) -> None:
        statuses = (
            "panel-majority-stale",
            "panel-majority-pending-checkin",
        )
        for status in statuses:
            with self.subTest(status=status):
                report = _content_readiness_payload()
                expert = report["content_readiness"]["expert"]
                for axis_name in ("readability", "professional_completeness"):
                    axis = expert[axis_name]
                    axis["attestation_status"] = status
                    self.assertFalse(axis["decision_complete"])
                    self.assertFalse(axis["storage_current"])
                    self.assertFalse(axis["source_current"])
                    self.assertFalse(axis["accepted_for_formal"])
                self.assertEqual(
                    [],
                    self.module._content_readiness_errors(
                        "fixture.json", report
                    ),
                )
                self.assertFalse(
                    report["content_readiness"]["aggregate"][
                        "readability_review_current"
                    ]
                )
                self.assertFalse(
                    report["content_readiness"]["aggregate"][
                        "professional_completeness_review_current"
                    ]
                )
                self.assertEqual("release-not-ready", report["release_gate"])

                mutations = {
                    "missing-axis-field": lambda axis: axis.pop("panel_size"),
                    "forged-current": lambda axis: axis.__setitem__(
                        "source_current", True
                    ),
                    "incomplete-current": lambda axis: axis.__setitem__(
                        "storage_current", True
                    ),
                    "false-formal-ready": lambda axis: axis.__setitem__(
                        "accepted_for_formal", True
                    ),
                }
                for mutation_name, mutate in mutations.items():
                    with self.subTest(
                        status=status,
                        mutation=mutation_name,
                    ):
                        changed = copy.deepcopy(report)
                        mutate(
                            changed["content_readiness"]["expert"][
                                "readability"
                            ]
                        )
                        self.assertTrue(
                            self.module._content_readiness_errors(
                                "fixture.json", changed
                            ),
                            mutation_name,
                        )

    def test_schema_one_readability_remains_auditable_with_legacy_fingerprints(self) -> None:
        report = _content_readiness_payload()
        readability = report["content_readiness"]["expert"]["readability"]
        readability.update(
            {
                "decision_complete": True,
                "storage_current": True,
                "source_current": False,
                "accepted_for_formal": False,
                "panel_artifact_schema_version": 1,
                "panel_review_id": "historical-readability-panel",
                "panel_size": 3,
                "attestation_status": "panel-majority-stale",
                "source_fingerprints": {
                    "reference_content": "a" * 64,
                    "root_content": "b" * 64,
                    "ai_readability": "f" * 64,
                },
                "attested_by": "expert-panel:historical-readability-panel",
                "attested_on": "2026-07-16",
                "evidence": [
                    {"path": "evals/historical-panel.json", "sha256": "e" * 64}
                ],
                "required_actionability_disposition_count": 123,
                "accepted_current_actionability_count": 0,
                "detector_false_positive_count": 0,
                "rewrite_required_count": 0,
                "tracked_tightening_count": 0,
            }
        )

        self.assertEqual(
            [], self.module._readability_axis_errors("fixture.json", readability)
        )

    def test_schema_one_professional_correction_remains_auditable_but_nonformal(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report, corrections=1)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis.update(
            {
                "accepted_for_formal": False,
                "decision_method": "three-independent-experts-majority",
                "panel_artifact_schema_version": 1,
                "evidence_contract_satisfied": False,
                "qualification_summary": None,
                "evidence_summary": None,
                "attestation_status": "panel-legacy-nonformal",
                "source_current": False,
                "source_fingerprints": {"professional_packages": "9" * 64},
                "review_contract_fingerprint": None,
                "review_contract_current": False,
                "review_plan_fingerprint": None,
                "current_review_plan_fingerprint": None,
                "review_plan_current": False,
                "review_binding_current": False,
                "provenance_current": False,
                "round_lifecycle_current": False,
                "review_cost_current": False,
                "review_cost": None,
                "fresh_target_count": 0,
                "carried_forward_target_count": 0,
                "round_lifecycle": {
                    "status": "no-schema3-current-decision",
                    "round_count": 0,
                    "chain_depth": 0,
                    "head_decision": None,
                    "current_decision_is_head": False,
                    "errors": [],
                    "limitations": [
                        "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted."
                    ],
                },
            }
        )
        for disposition in axis["professional_dispositions"]:
            disposition["package_fingerprint"] = disposition.pop(
                "package_material_binding"
            )
            disposition["review_binding_fingerprint"] = None
            disposition.pop("review_unit_binding")
            disposition["ordinary_criterion_disposition"] = disposition[
                "majority_disposition"
            ]
            disposition["ordinary_criterion_defects"] = []
            disposition["review_dependencies"] = None
            disposition["evidence_metrics"] = None
            disposition["provenance"] = None
            disposition["target_decision_fingerprint"] = None

        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "fixture.json", axis
            ),
        )
        self.assertEqual(1, axis["correction_count"])
        self.assertFalse(self.module._professional_completeness_formal_ready(axis))

    def test_schema_two_remains_auditable_but_rejects_current_field_aliases(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis.update(
            {
                "accepted_for_formal": False,
                "source_current": False,
                "source_fingerprints": {"professional_packages": "9" * 64},
                "current_source_fingerprints": {},
                "attestation_status": "panel-legacy-nonformal",
                "panel_artifact_schema_version": 2,
                "decision_method": (
                    "per-skill-qualified-reviewer-pool-domain-critical-fail-closed"
                ),
                "qualification_summary": {
                    "covered_target_count": 188,
                    "required_domain_experts_per_target": 2,
                    "required_architecture_experts_per_target": 1,
                    "per_target_panel_size": 3,
                    "reviewer_pool_size": 3,
                    "domain_reviewer_count": 2,
                    "architecture_reviewer_count": 1,
                },
                "evidence_summary": {
                    key: value
                    for key, value in axis["evidence_summary"].items()
                    if key != "target_vote_count"
                },
                "evidence_contract_satisfied": True,
                "review_contract_fingerprint": None,
                "review_contract_current": False,
                "review_plan_fingerprint": None,
                "current_review_plan_fingerprint": None,
                "review_plan_current": False,
                "review_binding_current": False,
                "provenance_current": False,
                "round_lifecycle_current": False,
                "review_cost_current": False,
                "review_cost": None,
                "fresh_target_count": 0,
                "carried_forward_target_count": 0,
                "round_lifecycle": {
                    "status": "no-schema3-current-decision",
                    "round_count": 0,
                    "chain_depth": 0,
                    "head_decision": None,
                    "current_decision_is_head": False,
                    "errors": [],
                    "limitations": [
                        "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted."
                    ],
                },
            }
        )
        for disposition in axis["professional_dispositions"]:
            disposition["package_fingerprint"] = disposition.pop(
                "package_material_binding"
            )
            disposition["review_binding_fingerprint"] = None
            disposition.pop("review_unit_binding")
            disposition["review_dependencies"] = None
            disposition["evidence_metrics"] = None
            disposition["provenance"] = None
            disposition["target_decision_fingerprint"] = None

        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "fixture.json", axis
            ),
        )
        self.assertFalse(self.module._professional_completeness_formal_ready(axis))

        for alias in ("package_material_binding", "review_unit_binding"):
            with self.subTest(alias=alias):
                injected = copy.deepcopy(axis)
                injected["professional_dispositions"][0][alias] = "f" * 64
                self.assertTrue(
                    self.module._professional_completeness_axis_errors(
                        "fixture.json", injected
                    )
                )

    def test_schema_three_exact_inventory_vote_and_criterion_counts_fail_closed(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        valid = report["content_readiness"]["expert"]["professional_completeness"]
        self.assertTrue(self.module._professional_v3_evidence_ready(valid))
        cases = (
            ("qualification_summary", "covered_target_count", (187, 189)),
            (
                "qualification_summary",
                "effective_domain_vote_count",
                (375, 377),
            ),
            (
                "qualification_summary",
                "effective_architecture_vote_count",
                (187, 189),
            ),
            ("evidence_summary", "target_vote_count", (563, 565)),
            ("evidence_summary", "criterion_result_count", (5639, 5641)),
        )
        for section, field, neighbors in cases:
            for value in neighbors:
                with self.subTest(section=section, field=field, value=value):
                    axis = copy.deepcopy(valid)
                    axis[section][field] = value
                    self.assertFalse(
                        self.module._professional_v3_evidence_ready(axis)
                    )

    def test_all_carry_zero_input_recomputes_provenance_and_cost(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        for disposition in axis["professional_dispositions"]:
            disposition["provenance"] = {
                "mode": "carried",
                "origin": {
                    "origin_review_id": "professional-completeness-origin",
                    "origin_commit": "a" * 40,
                    "origin_verdict_digest": disposition[
                        "target_decision_fingerprint"
                    ],
                },
            }
        axis.update(
            {
                "reviewer_pool_size": 0,
                "fresh_target_count": 0,
                "carried_forward_target_count": 188,
                "review_cost": {
                    "fresh_vote_count": 0,
                    "carried_forward_vote_count": 564,
                    "effective_vote_count": 564,
                    "fresh_criterion_result_count": 0,
                    "carried_forward_criterion_result_count": 5640,
                    "effective_criterion_result_count": 5640,
                    "canonical_capsule_input_bytes_proxy": 0,
                    "full_rereview_deduplicated_capsule_input_bytes_proxy": 300,
                    "input_ratio_ppm": 0,
                    "required_only_capsule_input_bytes_proxy": 0,
                    "required_only_input_ratio_ppm": 0,
                    "required_only_source_material_input_bytes_proxy": 0,
                    "source_material_input_bytes_proxy": 0,
                    "full_rereview_source_material_input_bytes_proxy": 100,
                    "source_material_coverage_ratio_ppm": 0,
                    "reviewer_added_source_material_input_bytes_proxy": 0,
                    "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": 0,
                    "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 0,
                    "reviewer_added_request_count": 0,
                    "reviewer_added_unique_relationship_count": 0,
                    "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 0,
                    "formal_round_policy_fingerprint": _formal_round_policy_fingerprint(),
                    "maximum_origin_depth": 1,
                    "plan_lineage_depth": 1,
                    "policy_status": "all-carry-zero-input",
                    "limitations": [
                        "Canonical effective discovery/request/final input-block bytes are a structural proxy; identical blocks are counted at most three times, while formal policy separately recomputes required-only source coverage and reviewer-added relationship/evidence metadata overhead; neither measure proves actual tokens, wall-clock time, subagent count, monetary cost, or reviewer behavior.",
                        "Static qualification claims do not prove reviewer identity, credentials, or domain experience.",
                        "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted.",
                    ],
                },
            }
        )
        axis["round_lifecycle"]["chain_depth"] = 1
        axis["qualification_summary"]["fresh_reviewer_pool_size"] = 0
        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "fixture.json", axis
            ),
        )
        self.assertTrue(self.module._professional_completeness_formal_ready(axis))
        axis["reviewer_pool_size"] = 3
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(any("reviewer pool" in error for error in errors), errors)
        self.assertFalse(self.module._professional_completeness_formal_ready(axis))

    def test_review_cost_metadata_boundary_uses_exact_cross_multiplication(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        boundary = _recompose_review_cost(
            axis["review_cost"],
            denominator=1_000_200,
            full_source=200,
            required_source=200,
            actual_source=200,
            required_metadata=1_000_000,
            metadata_overhead=50_000,
        )
        self.assertTrue(self.module._professional_review_cost_ready(axis))

        plus_one = _recompose_review_cost(
            copy.deepcopy(boundary),
            denominator=1_000_200,
            full_source=200,
            required_source=200,
            actual_source=200,
            required_metadata=1_000_000,
            metadata_overhead=50_001,
        )
        axis["review_cost"] = plus_one
        self.assertFalse(self.module._professional_review_cost_ready(axis))

        floor_collision = _recompose_review_cost(
            copy.deepcopy(boundary),
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
        axis["review_cost"] = floor_collision
        self.assertFalse(self.module._professional_review_cost_ready(axis))

    def test_incremental_review_cost_positive_and_boundaries(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["fresh_target_count"] = 1
        axis["carried_forward_target_count"] = 187
        valid = _incremental_review_cost(axis["review_cost"])
        self.assertTrue(self.module._professional_review_cost_ready(axis))

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
                axis["review_cost"] = copy.deepcopy(valid)
                mutate(axis["review_cost"])
                self.assertFalse(
                    self.module._professional_review_cost_ready(axis)
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
        axis["review_cost"] = zero_metadata
        self.assertFalse(self.module._professional_review_cost_ready(axis))

    def test_forged_all_carry_partition_and_redistributed_metrics_fail(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["fresh_target_count"] = 0
        axis["carried_forward_target_count"] = 188
        axis["reviewer_pool_size"] = 0
        axis["qualification_summary"]["fresh_reviewer_pool_size"] = 0
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(any("provenance partition" in error for error in errors), errors)

        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        first, second = axis["professional_dispositions"][:2]
        first["evidence_metrics"]["evidence_anchor_count"] = 5
        second["evidence_metrics"]["evidence_anchor_count"] = 7
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(any("professional_dispositions are malformed" in error for error in errors), errors)

        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["professional_dispositions"][0]["evidence_metrics"][
            "evidence_anchor_count"
        ] = 7
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(
            any("evidence_summary does not equal" in error for error in errors),
            errors,
        )

    def test_malformed_dependency_ids_return_errors_without_raising(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["professional_dispositions"][0]["review_dependencies"][
            "required_candidate_ids"
        ] = [{"not": "hashable"}]
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(any("professional_dispositions are malformed" in error for error in errors), errors)

    def test_review_cost_fixture_follows_validated_core_authority(self) -> None:
        fixture = _content_readiness_payload()["professional_review_cost_fixtures"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "src/control-model/core-contracts.json"
            target.parent.mkdir(parents=True)
            contracts = json.loads(
                (ROOT / "src/control-model/core-contracts.json").read_text(
                    encoding="utf-8"
                )
            )
            thresholds = contracts["final_goal_contract"][
                "professional_review_cost_fixtures"
            ]["thresholds"]
            target.write_text(json.dumps(contracts), encoding="utf-8")
            self.assertEqual(
                [],
                self.module._professional_review_cost_fixture_errors(
                    "fixture.json", fixture, root=root
                ),
            )
            fixture_max = fixture[
                "routing_neutral_isolated_material_binding_sensitivity"
            ]["fresh_target_count"]["max"]
            thresholds["maximum_fresh_target_count"] = fixture_max - 1
            target.write_text(json.dumps(contracts), encoding="utf-8")
            errors = self.module._professional_review_cost_fixture_errors(
                "fixture.json", fixture, root=root
            )
            self.assertTrue(
                any("arithmetic, inventory, or thresholds" in error for error in errors),
                errors,
            )

        legacy = copy.deepcopy(fixture)
        legacy_sensitivity = legacy[
            "routing_neutral_isolated_material_binding_sensitivity"
        ]
        for index, field in enumerate(
            sorted(self.module.LEGACY_PROFESSIONAL_REVIEW_COST_DIGEST_FIELDS),
            start=1,
        ):
            legacy_sensitivity[field] = f"{index:x}" * 64
        self.assertEqual(
            [],
            self.module._professional_review_cost_fixture_errors(
                "fixture.json", legacy
            ),
        )

        governance = (ROOT / "docs/SKILL_CONTENT_GOVERNANCE.md").read_text(
            encoding="utf-8"
        )
        cost_section = self._professional_review_cost_authority_section(
            governance
        )
        for authority in (
            "src/control-model/core-contracts.json",
            "final_goal_contract.professional_review_cost_fixtures",
            "reports/professionalism-regression-report.json",
            "reports/professionalism-regression-report.json",
        ):
            with self.subTest(authority=authority):
                self.assertIn(authority, cost_section)
        self.assertEqual(
            [],
            _professional_review_cost_numeric_duplicates(cost_section),
        )

    def test_review_cost_authority_section_uses_structural_boundaries(self) -> None:
        markdown = """# Governance

### Professional Review Cost Authority

The contract owns the policy and thresholds.

Derived reports remain evidence only.

#### Nested Cost Notes

Nested subsection content remains part of the authority section.

```markdown
### Next Section
```

input-ratio-ppm `1/2/3/4/5`

### Next Section

case is `9` fresh
"""
        cost_section = self._professional_review_cost_authority_section(
            markdown
        )
        self.assertIn("Derived reports remain evidence only.", cost_section)
        self.assertIn("#### Nested Cost Notes", cost_section)
        self.assertIn("Nested subsection content", cost_section)
        self.assertIn("```markdown\n### Next Section\n```", cost_section)
        self.assertIn("input-ratio-ppm `1/2/3/4/5`", cost_section)
        self.assertNotIn("case is `9` fresh", cost_section)
        self.assertEqual(
            [PROFESSIONAL_REVIEW_COST_NUMERIC_PATTERNS[1]],
            _professional_review_cost_numeric_duplicates(cost_section),
        )

    def test_deprecated_combined_attestation_cannot_be_formal_review(self) -> None:
        report = _content_readiness_payload()
        expert = report["content_readiness"]["expert"]
        expert["deprecated_expert_content_review_complete"] = True

        errors = self.module._content_readiness_errors("fixture.json", report)

        self.assertTrue(
            any("deprecated expert compatibility flag" in error for error in errors),
            errors,
        )

    def test_content_readiness_schema_eight_is_rejected_as_stale(self) -> None:
        report = _content_readiness_payload()
        report["content_readiness"]["schema_version"] = 8

        errors = self.module._content_readiness_errors("fixture.json", report)

        self.assertTrue(
            any(
                "content_readiness.schema_version must equal 10" in error
                for error in errors
            ),
            errors,
        )

    def test_dual_axis_nested_schema_and_identity_fail_closed(self) -> None:
        report = _content_readiness_payload()
        readability = report["content_readiness"]["expert"]["readability"]
        readability["unknown_contract_field"] = True
        errors = self.module._content_readiness_errors("fixture.json", report)
        self.assertTrue(any("fields do not match schema 10" in item for item in errors), errors)

        report = _content_readiness_payload()
        report["content_readiness"]["expert"]["professional_completeness"][
            "panel_kind"
        ] = "readability"
        errors = self.module._content_readiness_errors("fixture.json", report)
        self.assertTrue(any("panel_kind is invalid" in item for item in errors), errors)

        report = _content_readiness_payload()
        report["content_readiness"]["expert"].pop("readability")
        errors = self.module._content_readiness_errors("fixture.json", report)
        self.assertTrue(any("content_readiness.expert fields" in item for item in errors), errors)

    def test_tracked_tightening_cannot_be_forged_as_formal(self) -> None:
        report = _content_readiness_payload()
        _set_readability_decision(report, tracked=True)
        axis = report["content_readiness"]["expert"]["readability"]
        axis["accepted_for_formal"] = True
        axis["attestation_status"] = "panel-majority-current"
        report["content_readiness"]["aggregate"]["readability_review_current"] = True

        errors = self.module._readability_axis_errors("fixture.json", axis)

        self.assertTrue(any("zero-tightening/actionability formal contract" in item for item in errors), errors)
        self.assertFalse(self.module._readability_formal_ready(axis))

    def test_actionability_rewrite_cannot_be_forged_as_formal(self) -> None:
        report = _content_readiness_payload()
        _set_readability_decision(report)
        axis = report["content_readiness"]["expert"]["readability"]
        axis["actionability_dispositions"] = [
            {
                "target_id": "weak-front-loaded-action:" + "a" * 64,
                "skill_id": "fixture-skill",
                "path": "src/foundation/capabilities/fixture-skill/SKILL.md",
                "front_loaded_action_score": 20,
                "disposition": "rewrite-required",
                "reason_codes": ["primary-action-not-front-loaded"],
                "rationale": "Majority review requires a concrete first action before release.",
                "evidence": [
                    {
                        "line": 8,
                        "source_line": "The current opening only supplies context.",
                        "claim": "The opening supplies context without a concrete first action.",
                    }
                ],
            }
        ]
        axis.update(
            {
                "accepted_for_formal": True,
                "attestation_status": "panel-majority-current",
                "required_actionability_disposition_count": 1,
                "applied_actionability_disposition_count": 1,
                "accepted_current_actionability_count": 0,
                "detector_false_positive_count": 0,
                "rewrite_required_count": 1,
            }
        )
        report["content_readiness"]["aggregate"]["readability_review_current"] = True

        errors = self.module._readability_axis_errors("fixture.json", axis)

        self.assertTrue(
            any("zero-tightening/actionability formal contract" in item for item in errors),
            errors,
        )
        self.assertFalse(self.module._readability_formal_ready(axis))

    def test_actionability_detector_false_positive_requires_detector_update(self) -> None:
        report = _content_readiness_payload()
        _set_readability_decision(report)
        axis = report["content_readiness"]["expert"]["readability"]
        axis["actionability_dispositions"] = [
            {
                "target_id": "weak-front-loaded-action:" + "b" * 64,
                "skill_id": "fixture-skill",
                "path": "src/foundation/capabilities/fixture-skill/SKILL.md",
                "front_loaded_action_score": 20,
                "disposition": "detector-false-positive",
                "reason_codes": ["equivalent-action-verb-not-recognized"],
                "rationale": "The detector missed the explicit domain action in the opening.",
                "evidence": [
                    {
                        "line": 8,
                        "source_line": "Reconcile the current authority record first.",
                        "claim": "Reconcile is the concrete first action missed by the detector.",
                    }
                ],
            }
        ]
        axis.update(
            {
                "accepted_for_formal": False,
                "attestation_status": "panel-majority-detector-update-required",
                "required_actionability_disposition_count": 1,
                "applied_actionability_disposition_count": 1,
                "accepted_current_actionability_count": 0,
                "detector_false_positive_count": 1,
                "rewrite_required_count": 0,
            }
        )

        errors = self.module._readability_axis_errors("fixture.json", axis)

        self.assertEqual([], errors)
        self.assertFalse(self.module._readability_formal_ready(axis))

    def test_current_compact_professional_projection_passes_axis_and_static_entry(
        self,
    ) -> None:
        current = json.loads(
            (ROOT / "reports/professionalism-regression-report.json").read_text(
                encoding="utf-8"
            )
        )
        axis = current["content_readiness"]["expert"][
            "professional_completeness"
        ]
        self.assertEqual("release-not-ready", current["release_gate"])
        self.assertEqual(
            [],
            self.module._release_gate_errors(
                "reports/professionalism-regression-report.json", current
            ),
        )
        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "reports/professionalism-regression-report.json", axis
            ),
        )

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            path.write_text(json.dumps(current), encoding="utf-8")
            self.assertEqual([], self.module._static_report_errors(root))

    def test_current_professional_report_rejects_runtime_or_hybrid_authority(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_compact_completeness_decision(report)
        valid = report["content_readiness"]["expert"][
            "professional_completeness"
        ]
        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "reports/professionalism-regression-report.json", valid
            ),
        )
        self.assertTrue(self.module._professional_completeness_formal_ready(valid))

        cases = {
            "runtime-plan-and-lifecycle": ("6" * 64, "6" * 64),
            "runtime-lifecycle-without-plan": (None, None),
            "mixed-plan": (None, "6" * 64),
        }
        for label, (actual_plan, current_plan) in cases.items():
            with self.subTest(label=label):
                axis = copy.deepcopy(valid)
                axis["review_plan_fingerprint"] = actual_plan
                axis["current_review_plan_fingerprint"] = current_plan
                axis["round_lifecycle"].update(
                    {
                        "status": "schema3-head-current",
                        "round_count": 1,
                        "chain_depth": 0,
                        "head_decision": None,
                        "current_decision_is_head": True,
                        "errors": [],
                    }
                )
                errors = self.module._professional_completeness_axis_errors(
                    "reports/professionalism-regression-report.json", axis
                )
                self.assertTrue(errors)
                self.assertFalse(
                    self.module._professional_completeness_formal_ready(axis)
                )

    def test_current_professional_report_rejects_origin_semantic_forgery(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_compact_completeness_decision(report)
        valid = report["content_readiness"]["expert"][
            "professional_completeness"
        ]

        def canonical_carried_with_stale_counts(axis: dict) -> None:
            provenance = axis["professional_dispositions"][0]["provenance"]
            provenance["mode"] = "carried"
            provenance["origin"]["origin_review_id"] = "prior-valid-origin"

        cases = {
            "fresh-origin-review": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"]["origin"].__setitem__(
                "origin_review_id", "forged-valid-origin"
            ),
            "split-fresh-origin-commit": lambda axis: axis[
                "professional_dispositions"
            ][1]["provenance"]["origin"].__setitem__(
                "origin_commit", "b" * 40
            ),
            "fresh-carried-mode": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"].__setitem__("mode", "carried"),
            "canonical-carried-stale-counts": canonical_carried_with_stale_counts,
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                axis = copy.deepcopy(valid)
                mutate(axis)
                errors = self.module._professional_completeness_axis_errors(
                    "reports/professionalism-regression-report.json", axis
                )
                self.assertTrue(errors)
                self.assertFalse(
                    self.module._professional_completeness_formal_ready(axis)
                )

    def test_compact_professional_authority_is_closed_and_origin_bound(self) -> None:
        report = _content_readiness_payload()
        _set_compact_completeness_decision(report)
        valid = report["content_readiness"]["expert"][
            "professional_completeness"
        ]
        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "fixture.json", valid
            ),
        )

        mutations = {
            "extra-origin-field": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"]["origin"].__setitem__("origin_depth", 0),
            "invalid-mode": lambda axis: axis["professional_dispositions"][0][
                "provenance"
            ].__setitem__("mode", "carried-forward"),
            "invalid-review-id": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"]["origin"].__setitem__(
                "origin_review_id", "Not Canonical"
            ),
            "invalid-commit": lambda axis: axis["professional_dispositions"][0][
                "provenance"
            ]["origin"].__setitem__("origin_commit", "a" * 39),
            "invalid-digest": lambda axis: axis["professional_dispositions"][0][
                "provenance"
            ]["origin"].__setitem__("origin_verdict_digest", "z" * 64),
            "legacy-origin-source-alias": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"]["origin"].__setitem__(
                "source_fingerprint", "f" * 64
            ),
            "legacy-package-alias": lambda axis: axis[
                "professional_dispositions"
            ][0].__setitem__("package_fingerprint", "f" * 64),
            "legacy-review-alias": lambda axis: axis[
                "professional_dispositions"
            ][0].__setitem__("review_binding_fingerprint", "f" * 64),
            "missing-package-material-binding": lambda axis: axis[
                "professional_dispositions"
            ][0].pop("package_material_binding"),
            "missing-review-unit-binding": lambda axis: axis[
                "professional_dispositions"
            ][0].pop("review_unit_binding"),
            "verdict-digest-mismatch": lambda axis: axis[
                "professional_dispositions"
            ][0].__setitem__("target_decision_fingerprint", "f" * 64),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                axis = copy.deepcopy(valid)
                mutate(axis)
                errors = self.module._professional_completeness_axis_errors(
                    "fixture.json", axis
                )
                self.assertTrue(
                    any("professional_dispositions are malformed" in error for error in errors),
                    errors,
                )

    def test_compact_professional_partitions_counts_and_cost_fail_closed(self) -> None:
        report = _content_readiness_payload()
        _set_compact_completeness_decision(report, carried=True)
        valid = report["content_readiness"]["expert"][
            "professional_completeness"
        ]
        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "fixture.json", valid
            ),
        )

        mutations = {
            "partition": lambda axis: axis.__setitem__(
                "carried_forward_target_count", 189
            ),
            "origin-current-review": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"]["origin"].__setitem__(
                "origin_review_id", axis["panel_review_id"]
            ),
            "reviewer-pool": lambda axis: axis.__setitem__(
                "reviewer_pool_size", 3
            ),
            "cost": lambda axis: axis["review_cost"].__setitem__(
                "carried_forward_vote_count", 565
            ),
            "cost-currentness": lambda axis: axis.__setitem__(
                "review_cost_current", False
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                axis = copy.deepcopy(valid)
                mutate(axis)
                self.assertTrue(
                    self.module._professional_completeness_axis_errors(
                        "fixture.json", axis
                    )
                )

    def test_null_professional_plans_require_authenticated_fixed_lifecycle(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_compact_completeness_decision(report)
        valid = report["content_readiness"]["expert"][
            "professional_completeness"
        ]
        self.assertEqual(
            [],
            self.module._professional_completeness_axis_errors(
                "fixture.json", valid
            ),
        )

        mutations = {
            "partial-null": lambda axis: axis.__setitem__(
                "current_review_plan_fingerprint", "6" * 64
            ),
            "runtime-lifecycle": lambda axis: axis["round_lifecycle"].update(
                {
                    "status": "schema3-head-current",
                    "head_decision": "evals/expert-panel/runtime/panel/decision.json",
                }
            ),
            "fixed-head": lambda axis: axis["round_lifecycle"].__setitem__(
                "head_decision", "evals/expert-panel/runtime/panel/decision.json"
            ),
            "fixed-errors": lambda axis: axis["round_lifecycle"].__setitem__(
                "errors", ["forged fixed lifecycle"]
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                axis = copy.deepcopy(valid)
                mutate(axis)
                self.assertTrue(
                    self.module._professional_completeness_axis_errors(
                        "fixture.json", axis
                    )
                )

    def test_professional_correction_and_short_coverage_cannot_be_formal(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report, corrections=1)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["accepted_for_formal"] = True
        axis["attestation_status"] = "panel-majority-current"
        report["content_readiness"]["aggregate"][
            "professional_completeness_review_current"
        ] = True
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(any("zero-correction formal contract" in item for item in errors), errors)
        self.assertFalse(self.module._professional_completeness_formal_ready(axis))

        report = _content_readiness_payload()
        _set_completeness_decision(
            report,
            applied=187,
            status="panel-majority-incomplete-coverage",
        )
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["accepted_for_formal"] = True
        axis["attestation_status"] = "panel-majority-current"
        report["content_readiness"]["aggregate"][
            "professional_completeness_review_current"
        ] = True
        errors = self.module._professional_completeness_axis_errors(
            "fixture.json", axis
        )
        self.assertTrue(any("188-package zero-correction" in item for item in errors), errors)
        self.assertFalse(self.module._professional_completeness_formal_ready(axis))

    def test_dual_axis_aggregate_and_release_blockers_are_independent(self) -> None:
        report = _content_readiness_payload()
        report["content_readiness"]["aggregate"]["readability_review_current"] = True
        errors = self.module._content_readiness_errors("fixture.json", report)
        self.assertTrue(any("aggregate does not match" in item for item in errors), errors)

        report = _content_readiness_payload()
        _set_readability_decision(report)
        report["release_blockers"] = [
            item
            for item in report["release_blockers"]
            if item["category"] != "readability-review-release-gate"
        ]
        self.assertEqual([], self.module._release_gate_errors("fixture.json", report))

        _set_completeness_decision(report)
        report["release_blockers"] = [
            item
            for item in report["release_blockers"]
            if item["category"] != "professional-completeness-review-release-gate"
        ]
        report["schema_version"] = 4
        report["expert_panel_release_manifest"] = (
            _formal_expert_panel_release_manifest()
        )
        report["release_gate"] = "release-ready"
        self.assertEqual([], self.module._release_gate_errors("fixture.json", report))

    def test_root_and_reference_summary_drift_does_not_rebind_readability(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["source_fingerprint"] = "e" * 64
            report["content_readiness"]["root"]["source_fingerprint"] = "e" * 64
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

            self.assertFalse(
                any("readability fingerprint" in error for error in errors), errors
            )

    def test_current_readability_fingerprints_are_closed_exact_three(self) -> None:
        report = _content_readiness_payload()
        _set_readability_decision(report)
        axis = report["content_readiness"]["expert"]["readability"]
        expected_keys = set(
            self.module.panel_contracts.READABILITY_SOURCE_FINGERPRINT_KEYS
        )
        self.assertEqual(expected_keys, set(axis["source_fingerprints"]))
        self.assertEqual(
            [], self.module._readability_axis_errors("fixture.json", axis)
        )

        mutations = {
            "missing": lambda value: value["current_source_fingerprints"].pop(
                "readability_target_manifest"
            ),
            "extra": lambda value: value["current_source_fingerprints"].__setitem__(
                "extra", "d" * 64
            ),
            "non-sha": lambda value: value["current_source_fingerprints"].__setitem__(
                "readability_detector_contract", "not-a-sha"
            ),
            "mismatch": lambda value: value["source_fingerprints"].__setitem__(
                "actionability_detector_contract", "e" * 64
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                changed = copy.deepcopy(axis)
                mutate(changed)
                errors = self.module._readability_axis_errors(
                    "fixture.json", changed
                )
                self.assertTrue(errors, name)

    def test_aggregate_rejects_each_incomplete_current_axis_field(self) -> None:
        report = _content_readiness_payload()
        _set_readability_decision(report)
        _set_completeness_decision(report)
        self.assertEqual(
            [], self.module._content_readiness_errors("fixture.json", report)
        )

        flips = {
            "readability": {
                "decision_complete": False,
                "storage_current": False,
                "source_current": False,
                "accepted_for_formal": False,
                "attestation_status": "panel-majority-stale",
                "applied_density_disposition_count": 1,
                "applied_readability_disposition_count": 1,
                "applied_actionability_disposition_count": 1,
            },
            "professional_completeness": {
                "decision_complete": False,
                "storage_current": False,
                "source_current": False,
                "accepted_for_formal": False,
                "attestation_status": "panel-majority-stale",
                "required_target_count": 187,
                "applied_target_count": 187,
                "accepted_current_count": 187,
            },
        }
        for axis_name, axis_flips in flips.items():
            for field, changed_value in axis_flips.items():
                with self.subTest(axis=axis_name, field=field):
                    changed = copy.deepcopy(report)
                    changed["content_readiness"]["expert"][axis_name][
                        field
                    ] = changed_value
                    errors = self.module._content_readiness_errors(
                        "fixture.json", changed
                    )
                    self.assertTrue(
                        any("aggregate does not match" in error for error in errors),
                        errors,
                    )

    def test_ordinary_noncurrent_readability_is_soft_and_not_aggregate_current(
        self,
    ) -> None:
        report = _content_readiness_payload()
        self.assertEqual(
            [], self.module._content_readiness_errors("fixture.json", report)
        )
        self.assertFalse(
            report["content_readiness"]["aggregate"][
                "readability_review_current"
            ]
        )

        _set_readability_decision(report)
        axis = report["content_readiness"]["expert"]["readability"]
        axis["source_fingerprints"]["readability_target_manifest"] = "d" * 64
        axis["source_current"] = False
        axis["accepted_for_formal"] = False
        axis["attestation_status"] = "panel-majority-stale"
        report["content_readiness"]["aggregate"][
            "readability_review_current"
        ] = False
        self.assertEqual(
            [], self.module._content_readiness_errors("fixture.json", report)
        )

    def test_content_readiness_entry_runs_complete_axis_validators(self) -> None:
        report = _content_readiness_payload()
        _set_readability_decision(report)
        _set_completeness_decision(report)
        self.assertEqual(
            [], self.module._content_readiness_errors("fixture.json", report)
        )

        mutations = {
            "readability-exact-fingerprint-keys": (
                "readability",
                lambda axis: axis["current_source_fingerprints"].__setitem__(
                    "forged", "a" * 64
                ),
                "current_source_fingerprints",
            ),
            "readability-missing-evidence": (
                "readability",
                lambda axis: axis.__setitem__("evidence", []),
                "evidence",
            ),
            "professional-exact-fingerprint-keys": (
                "professional_completeness",
                lambda axis: axis["current_source_fingerprints"].__setitem__(
                    "forged", "b" * 64
                ),
                "current_source_fingerprints",
            ),
            "professional-missing-evidence": (
                "professional_completeness",
                lambda axis: axis.__setitem__("evidence", []),
                "evidence",
            ),
            "professional-invalid-artifact-schema": (
                "professional_completeness",
                lambda axis: axis.__setitem__(
                    "panel_artifact_schema_version", 4
                ),
                "supported decision schema",
            ),
            "professional-count-mismatch": (
                "professional_completeness",
                lambda axis: axis.__setitem__("accepted_current_count", 187),
                "do not sum",
            ),
        }
        for name, (axis_name, mutate, expected) in mutations.items():
            with self.subTest(name=name):
                changed = copy.deepcopy(report)
                mutate(changed["content_readiness"]["expert"][axis_name])
                errors = self.module._content_readiness_errors(
                    "fixture.json", changed
                )
                self.assertTrue(
                    any(expected in error for error in errors),
                    errors,
                )

    def test_static_report_entry_rejects_deep_expert_axis_forgery(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_readiness"]["expert"]["readability"][
                "current_source_fingerprints"
            ]["forged"] = "f" * 64
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

        self.assertTrue(
            any("current_source_fingerprints" in error for error in errors),
            errors,
        )

    def test_status_and_blocker_contract_rejects_missing_or_contradictory_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blocker = {
                "category": "synthetic-error",
                "target": "fixture",
                "message": "Synthetic blocking evidence.",
                "severity": "error",
            }
            self._write_reports(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                report["blockers"] = [blocker]
                if relative.endswith("regression-report.json"):
                    report["summary"]["blocker_count"] = 1
                path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(any("cannot pass with error blockers" in item for item in errors), errors)

            self._write_reports(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                if relative.endswith("regression-report.json"):
                    report["status"] = "current-contract-fail"
                else:
                    report["authoring_gate"] = "current-contract-fail"
                path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(any("status must match authoring_gate" in item for item in errors), errors)

            self._write_reports(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                report.pop("blockers")
                path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(any("must contain a blockers list" in item for item in errors), errors)

    def test_semantic_validation_rejects_invalid_source_fingerprint_shape(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["source_fingerprint"] = "not-a-sha256"
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)

            self.assertTrue(
                any("Root source fingerprint mismatch" in item for item in errors),
                errors,
            )

    def test_semantic_validation_rejects_forged_expert_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_readiness"]["expert"][
                "deprecated_expert_content_review_complete"
            ] = True
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any("deprecated expert compatibility flag" in item for item in errors),
                errors,
            )

    def test_core_principles_global_report_is_not_a_productization_asset(self) -> None:
        self.assertTrue(
            {
                "scripts/eval-core-principles.py",
                "src/control-model/core-contracts.json",
            }.issubset(set(self.module.REQUIRED))
        )
        self.assertNotIn("reports/core-principles-outcomes.json", self.module.REQUIRED)
        self.assertNotIn("reports/core-principles-outcomes.md", self.module.REQUIRED)

    def test_productization_ignores_stale_or_missing_core_global_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            report_path = root / "reports/core-principles-outcomes.json"
            self.assertEqual([], self.module._static_report_errors(root))
            report_path.write_text("not-json\n", encoding="utf-8")
            self.assertEqual([], self.module._static_report_errors(root))
            report_path.unlink()
            self.assertEqual([], self.module._static_report_errors(root))

            owned_path = root / "reports/professionalism-regression-report.json"
            owned = json.loads(owned_path.read_text(encoding="utf-8"))
            owned["unexpected"] = True
            owned_path.write_text(json.dumps(owned), encoding="utf-8")
            errors = self.module._static_report_errors(root)
            self.assertTrue(
                any("closed professionalism report envelope" in item for item in errors),
                errors,
            )

    def test_missing_core_principles_evaluator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with mock.patch.object(
                self.module, "_docs_errors", return_value=[]
            ), mock.patch.object(
                self.module, "_static_report_errors", return_value=[]
            ):
                errors = self.module.validate_productization_assets(root)
            self.assertTrue(
                any(
                    "missing required product asset: scripts/eval-core-principles.py"
                    in error
                    for error in errors
                ),
                errors,
            )

    def test_productization_validates_professional_json_without_rerunning_producer(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            self.assertFalse(
                hasattr(self.module, "_canonical_professionalism_artifacts")
            )
            with mock.patch.object(
                self.module.importlib.util,
                "spec_from_file_location",
                side_effect=AssertionError("producer must not load"),
            ):
                self.module._static_report_errors(root)

    def test_productization_rejects_multi_profile_marketplace_schema(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            schema_path = root / "schemas/marketplace-index.schema.json"
            schema_path.parent.mkdir(parents=True)
            schema_path.write_text(
                json.dumps(
                    {
                        "properties": {
                            "schema_version": {"const": 3},
                            "profile": {"enum": ["recommended", "full", "dev"]},
                        }
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(self.module, "REQUIRED", ()), mock.patch.object(
                self.module, "FORBIDDEN", ()
            ), mock.patch.object(
                self.module, "_docs_errors", return_value=[]
            ), mock.patch.object(
                self.module, "_static_report_errors", return_value=[]
            ):
                errors = self.module.validate_productization_assets(root)

        self.assertTrue(
            any(
                "fixed recommended Runtime projection" in error
                for error in errors
            ),
            errors,
        )

    def test_demo_gif_is_required_and_linked_from_readme(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# rd-skills\n", encoding="utf-8")

            errors = self.module._demo_gif_errors(root)

        self.assertIn("missing demo GIF: docs/assets/rd-skills-demo.gif", errors)

    def test_demo_gif_rejects_invalid_and_static_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            readme = root / "README.md"
            asset = root / "docs/assets/rd-skills-demo.gif"
            asset.parent.mkdir(parents=True)
            readme.write_text(
                "![rd-skills demo](docs/assets/rd-skills-demo.gif)\n",
                encoding="utf-8",
            )

            asset.write_bytes(b"not-a-gif")
            self.assertIn(
                "demo GIF is not a valid GIF animation",
                self.module._demo_gif_errors(root),
            )

            asset.write_bytes(_gif_fixture(frame_count=1))
            self.assertIn(
                "demo GIF must be animated (found 1 frame)",
                self.module._demo_gif_errors(root),
            )

    def test_demo_gif_rejects_unlinked_asset_and_accepts_animated_asset(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            readme = root / "README.md"
            asset = root / "docs/assets/rd-skills-demo.gif"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(_gif_fixture(frame_count=2))
            readme.write_text("# rd-skills\n", encoding="utf-8")

            self.assertIn(
                "README.md must embed docs/assets/rd-skills-demo.gif",
                self.module._demo_gif_errors(root),
            )

            readme.write_text(
                "![rd-skills demo](docs/assets/rd-skills-demo.gif)\n",
                encoding="utf-8",
            )
            self.assertEqual([], self.module._demo_gif_errors(root))

            asset.write_bytes(_gif_fixture(frame_count=2).replace(b"GIF89a", b"GIF87a", 1))
            self.assertEqual([], self.module._demo_gif_errors(root))

    def test_authoring_assets_exclude_release_only_markdown_and_duplicate_json(
        self,
    ) -> None:
        self.assertIn(
            "reports/professionalism-regression-report.json", self.module.REQUIRED
        )
        self.assertFalse(
            any(path.endswith(".md") and path.startswith("reports/") for path in self.module.REQUIRED)
        )
        self.assertEqual(
            {"reports/professionalism-regression-report.json"},
            self.module.CONTENT_READINESS_REPORTS,
        )


if __name__ == "__main__":
    unittest.main()
