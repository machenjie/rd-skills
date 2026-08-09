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
    lifecycle_release_blocker = {
        "category": "root-disposition-lifecycle-release-record-required",
        "target": (
            "config/skill-content-exceptions.yaml"
            "#root_semantic_dispositions.lifecycle"
        ),
        "message": "Formal release requires a recorded Root lifecycle release.",
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
        "semantic_lifecycle_status": "bootstrap-current",
        "semantic_lifecycle_detector_fingerprint": "e" * 64,
        "semantic_lifecycle_snapshot_current": True,
        "semantic_lifecycle_formal_release_ready": False,
        "semantic_lifecycle_bootstrap_refresh_chain_valid": True,
        "semantic_lifecycle_bootstrap_refresh_count": 0,
        "semantic_lifecycle_bootstrap_refresh_latest_delta": None,
        "semantic_lifecycle_comparison": {
            "comparison_scope": "bootstrap-no-prior-release",
            "added_count": None,
            "removed_count": None,
            "new_disposition_count": None,
            "disposition_change_count": None,
            "source_rewrite_count": None,
            "source_replacement_count": None,
            "detector_change_removal_count": None,
            "detector_improvement_count": None,
            "unclassified_count": None,
            "added": [],
            "removed": [],
            "disposition_changes": [],
            "disposition_change_details": [],
            "source_rewrites": [],
            "detector_change_removals": [],
            "detector_improvements": [],
            "unclassified": [],
        },
        "semantic_lifecycle_age": {
            "known_age_count": 0,
            "unknown_age_count": 1,
            "max_age_days": None,
        },
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
                "reference_content": None,
                "root_content": None,
                "ai_readability": None,
                "skill_detector": None,
            },
            "current_source_fingerprints": {
                "reference_content": "a" * 64,
                "root_content": "b" * 64,
                "ai_readability": "f" * 64,
                "skill_detector": "7" * 64,
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
            "source_fingerprints": {
                "professional_packages": None,
                "professional_review_bindings": None,
                "professional_review_contract": None,
            },
            "current_source_fingerprints": {
                "professional_packages": "9" * 64,
                "professional_review_bindings": "8" * 64,
                "professional_review_contract": "7" * 64,
            },
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
            "required_target_count": 189,
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
            "review_states": {"KEEP": 189},
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
            "schema_version": 9,
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
                "carried_forward_target_count": 189,
                "input_ratio_ppm": 0,
            },
            "routing_neutral_isolated_material_binding_sensitivity": copy.deepcopy(
                cost_authority["locked_current_catalog"]
            ),
            "representative_routing_adjacency_mutation": {
                "skill_id": "acceptance-criteria-builder",
                "fresh_target_ids": ["acceptance-criteria-builder"],
                "carried_forward_target_count": 188,
                "reason_codes": ["adjacency-review-binding-changed"],
                "cost_threshold_applied": False,
            },
            "review_contract_change": {
                "fresh_target_count": 189,
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
            lifecycle_release_blocker,
        ],
        "advisories": [],
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
    applied: int = 189,
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
                "package_fingerprint": f"{index:064x}"[-64:],
                "review_binding_fingerprint": f"{index + 200:064x}"[-64:],
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
                    "origin_depth": 0,
                    "evidence": [
                        {
                            "voter_id": f"expert-{voter}",
                            "ballot": {
                                "path": f"evals/completeness-fixture/panel/expert-{voter}.json",
                                "sha256": f"{voter:064x}",
                                "kind": "changeforge.professional-completeness-panel-ballot",
                                "axis": "professional-completeness",
                                "review_id": "completeness-fixture",
                            },
                            "capsule": {
                                "path": f"evals/completeness-fixture/capsules/expert-{voter}.json",
                                "sha256": f"{voter + 10:064x}",
                                "kind": "changeforge.professional-completeness-review-capsule",
                                "axis": "professional-completeness",
                                "review_id": "completeness-fixture",
                            },
                            "capsule_canonical_json_bytes_proxy": 100,
                        }
                        for voter in range(1, 4)
                    ],
                },
                "target_decision_fingerprint": f"{index + 400:064x}"[-64:],
            }
        )
    formal = corrections == 0 and applied == 189 and status in {
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
                "covered_target_count": 189,
                "required_domain_experts_per_target": 2,
                "required_architecture_experts_per_target": 1,
                "per_target_panel_size": 3,
                "fresh_reviewer_pool_size": 3,
                "effective_domain_vote_count": 378,
                "effective_architecture_vote_count": 189,
            },
            "evidence_summary": {
                "target_vote_count": 567,
                "required_adjacency_candidate_count": 945,
                "criterion_result_count": 5670,
                "criterion_anchor_binding_count": 5670,
                "criterion_assertion_count": 5670,
                "evidence_anchor_count": 1134,
                "examined_failure_mode_count": 1134,
                "examined_omission_candidate_count": 1134,
                "examined_adjacency_count": 2835,
                "examined_required_adjacency_count": 2835,
                "reviewer_added_adjacency_count": 0,
                "proof_limit_count": 567,
                "qualification_claim_count": 567,
            },
            "review_contract_fingerprint": "7" * 64,
            "current_review_contract_fingerprint": "7" * 64,
            "review_contract_current": True,
            "review_plan_fingerprint": "6" * 64,
            "current_review_plan_fingerprint": "6" * 64,
            "review_plan_current": True,
            "review_binding_current": True,
            "provenance_current": True,
            "round_lifecycle_current": True,
            "round_lifecycle": {
                "status": "schema3-head-current",
                "round_count": 1,
                "chain_depth": 1,
                "head_decision": "evals/expert-panel/completeness-fixture/panel/decision.json",
                "current_decision_is_head": True,
                "errors": [],
                "limitations": [
                    "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted."
                ],
            },
            "review_cost_current": True,
            "review_cost": {
                "fresh_vote_count": 567,
                "carried_forward_vote_count": 0,
                "effective_vote_count": 567,
                "fresh_criterion_result_count": 5670,
                "carried_forward_criterion_result_count": 0,
                "effective_criterion_result_count": 5670,
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
            "fresh_target_count": 189,
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
                        "release_blocker_count": 3,
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
            for relative in self.module.PROFESSIONALISM_CANONICAL_ARTIFACTS
        }

    def _write_current_professionalism_artifacts(self, root: Path) -> None:
        for relative, content in self._current_professionalism_artifacts().items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

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
                [], self.module._static_report_errors(root, enforce_fresh=False)
            )

            path = root / "reports/hookless-control-plane-eval.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["evidence_scope"] = "host-performance"
            report["limitations"] = []
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root, enforce_fresh=False)
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

            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(any("routing-eval.json" in error for error in errors), errors)
            self.assertTrue(
                any("installation-validation.json" in error for error in errors), errors
            )

    def test_professionalism_reports_require_self_contained_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report.pop("root_content_summary")
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any("must contain root_content_summary" in error for error in errors),
                errors,
            )

    def test_professionalism_reports_require_closed_top_level_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["unexpected"] = True
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root, enforce_fresh=False)

            self.assertTrue(
                any("closed professionalism report envelope" in error for error in errors),
                errors,
            )

    def test_professionalism_reports_require_closed_skill_review_counts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_audit_summary"]["review_reasons"].pop(
                "weak_front_loaded_action"
            )
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root, enforce_fresh=False)

            self.assertTrue(
                any("review_reasons must be the complete closed" in error for error in errors),
                errors,
            )

    def test_professionalism_reports_reject_non_boolean_or_contradictory_axes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["semantic_triage_complete"] = "true"
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(any("must be a boolean" in error for error in errors), errors)

            self._write_reports(root)
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["structural_strict_ready"] = False
            report["content_readiness"]["root"]["structural_strict_ready"] = False
            report["content_readiness"]["aggregate"]["structural_strict_ready"] = False
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any("cannot pass while Root structural_strict_ready=false" in error for error in errors),
                errors,
            )

    def test_expert_false_is_required_but_does_not_block_authoring_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            self.assertEqual(
                [], self.module._static_report_errors(root, enforce_fresh=False)
            )
            readiness = json.loads(
                (
                    root / "reports/professionalism-release-readiness.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("current-contract-pass", readiness["authoring_gate"])
            self.assertEqual("release-not-ready", readiness["release_gate"])

    def test_current_cost_reports_are_consistent_while_release_is_not_ready(
        self,
    ) -> None:
        reports = self._read_professionalism_reports(ROOT)
        expected_release_blocker = {
            "category": "root-disposition-lifecycle-release-record-required",
            "target": (
                "config/skill-content-exceptions.yaml"
                "#root_semantic_dispositions.lifecycle"
            ),
            "message": (
                "formal release requires a recorded, current, classified Root "
                "disposition release snapshot; status=pending-changes; unclassified=0"
            ),
            "severity": "error",
        }
        for report in reports.values():
            completeness = report["content_readiness"]["expert"][
                "professional_completeness"
            ]
            self.assertEqual("current-contract-pass", report["authoring_gate"])
            self.assertEqual("release-not-ready", report["release_gate"])
            self.assertEqual([], report["blockers"])
            self.assertEqual(
                [expected_release_blocker],
                report["release_blockers"],
            )
            root_summary = report["root_content_summary"]
            self.assertEqual(
                "pending-changes",
                root_summary["semantic_lifecycle_status"],
            )
            self.assertEqual(
                0,
                root_summary["semantic_lifecycle_comparison"][
                    "unclassified_count"
                ],
            )
            self.assertEqual(
                "pass",
                report["professional_review_cost_fixtures"]["status"],
            )
            applied_target_count = completeness["applied_target_count"]
            required_target_count = completeness["required_target_count"]
            qualification = completeness["qualification_summary"]
            evidence = completeness["evidence_summary"]
            panel_size = qualification["per_target_panel_size"]
            criterion_count = len(
                self.module.PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
                | self.module.PROFESSIONAL_ORDINARY_CRITERIA
            )
            self.assertEqual(3, panel_size)
            self.assertEqual(
                2,
                qualification["required_domain_experts_per_target"],
            )
            self.assertEqual(
                1,
                qualification["required_architecture_experts_per_target"],
            )
            self.assertEqual(
                self.module.PROFESSIONAL_PACKAGE_COUNT,
                required_target_count,
            )
            self.assertEqual(
                applied_target_count,
                completeness["fresh_target_count"]
                + completeness["carried_forward_target_count"],
            )
            self.assertLessEqual(applied_target_count, required_target_count)
            if completeness["source_current"]:
                self.assertEqual(required_target_count, applied_target_count)
            else:
                self.assertLess(applied_target_count, required_target_count)
            self.assertEqual(
                applied_target_count,
                qualification["covered_target_count"],
            )
            self.assertEqual(
                2 * applied_target_count,
                qualification["effective_domain_vote_count"],
            )
            self.assertEqual(
                applied_target_count,
                qualification["effective_architecture_vote_count"],
            )
            self.assertEqual(
                panel_size * applied_target_count,
                evidence["target_vote_count"],
            )
            self.assertEqual(
                criterion_count * panel_size * applied_target_count,
                evidence["criterion_result_count"],
            )
            self.assertEqual(
                56,
                report["professional_review_cost_fixtures"][
                    "routing_neutral_isolated_material_binding_sensitivity"
                ]["fresh_target_count"]["max"],
            )

        canonical = self._current_professionalism_artifacts()
        with mock.patch.object(
            self.module,
            "_canonical_professionalism_artifacts",
            return_value=canonical,
        ):
            self.assertEqual([], self.module._static_report_errors(ROOT))

    def test_nested_formal_tampers_fail_at_the_canonical_artifact_boundary(
        self,
    ) -> None:
        mutations = {
            "nested-shape": lambda axis: axis["qualification_summary"].__setitem__(
                "unexpected", 1
            ),
            "nested-sha": lambda axis: axis["professional_dispositions"][0].__setitem__(
                "package_fingerprint", "0" * 64
            ),
            "provenance-partition": lambda axis: axis[
                "professional_dispositions"
            ][0]["provenance"].__setitem__("mode", "fresh"),
            "disposition-evidence-sum": lambda axis: axis[
                "professional_dispositions"
            ][0]["evidence_metrics"].__setitem__("criterion_result_count", 31),
            "effective-domain-votes": lambda axis: axis[
                "qualification_summary"
            ].__setitem__("effective_domain_vote_count", 325),
            "effective-criteria": lambda axis: axis["evidence_summary"].__setitem__(
                "criterion_result_count", 4861
            ),
            "review-cost-ratio": lambda axis: axis["review_cost"].__setitem__(
                "input_ratio_ppm", 1011968
            ),
        }
        canonical = self._current_professionalism_artifacts()
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
                    if label == "provenance-partition":
                        self.assertEqual(
                            "carried-forward",
                            completeness["professional_dispositions"][0][
                                "provenance"
                            ]["mode"],
                        )
                    before = (
                        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
                    ).encode("utf-8")
                    mutate(completeness)
                    after = (
                        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
                    ).encode("utf-8")
                    self.assertNotEqual(before, after)
                    path.write_bytes(after)
                with mock.patch.object(
                    self.module,
                    "_canonical_professionalism_artifacts",
                    return_value=canonical,
                ):
                    errors = self.module._static_report_errors(root)
                self.assertTrue(
                    any(
                        "differs from fresh canonical producer bytes" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_current_cost_status_cannot_be_rewritten_as_non_current(self) -> None:
        canonical = self._current_professionalism_artifacts()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_current_professionalism_artifacts(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                report["professional_review_cost_fixtures"][
                    "status"
                ] = "formal-non-current"
                path.write_text(
                    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            with mock.patch.object(
                self.module,
                "_canonical_professionalism_artifacts",
                return_value=canonical,
            ):
                errors = self.module._static_report_errors(root)
            self.assertTrue(
                any(
                    "differs from fresh canonical producer bytes" in error
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
            errors = self.module._static_report_errors(root, enforce_fresh=False)
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
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any(
                    "release_gate does not match authoring, readability review, "
                    "professional-completeness review, and Root lifecycle"
                    in error
                    for error in errors
                ),
                errors,
            )

    def test_bootstrap_lifecycle_rejects_forged_delta(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"]["semantic_lifecycle_comparison"][
                "added_count"
            ] = 0
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any("bootstrap lifecycle must preserve null deltas" in item for item in errors),
                errors,
            )

            path = root / "reports/professionalism-regression-report.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_readiness"]["expert"].pop("readability")
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any("content_readiness.expert fields" in error for error in errors),
                errors,
            )

    def test_bootstrap_refresh_report_fields_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"].pop(
                "semantic_lifecycle_bootstrap_refresh_chain_valid"
            )
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any("bootstrap_refresh_chain_valid must be a boolean" in item for item in errors),
                errors,
            )

            self._write_reports(root)
            report = json.loads(path.read_text(encoding="utf-8"))
            report["root_content_summary"][
                "semantic_lifecycle_bootstrap_refresh_count"
            ] = 1
            path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(
                any("latest delta must match its closed schema" in item for item in errors),
                errors,
            )

    def test_release_gate_must_match_authoring_and_expert_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            release = root / "reports/professionalism-release-readiness.json"
            report = json.loads(release.read_text(encoding="utf-8"))
            report["release_gate"] = "release-ready"
            report["release_blockers"] = []
            release.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root, enforce_fresh=False)

            self.assertTrue(
                any(
                    "release_gate does not match authoring, readability review, "
                    "professional-completeness review, and Root lifecycle"
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
            path = root / "reports/professionalism-release-readiness.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["content_readiness"]["expert"]["readability"][
                "attestation_schema_version"
            ] = None
            path.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root, enforce_fresh=False)

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
                            "reference_content": "a" * 64,
                            "root_content": "b" * 64,
                            "ai_readability": "f" * 64,
                            "skill_detector": "7" * 64,
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
                [], self.module._static_report_errors(root, enforce_fresh=False)
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
            }
        )
        for disposition in axis["professional_dispositions"]:
            disposition["ordinary_criterion_disposition"] = disposition[
                "majority_disposition"
            ]
            disposition["ordinary_criterion_defects"] = []
            disposition["review_binding_fingerprint"] = None
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

    def test_schema_two_current_booleans_cannot_satisfy_formal(self) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        axis = report["content_readiness"]["expert"]["professional_completeness"]
        axis["panel_artifact_schema_version"] = 2
        axis["decision_method"] = (
            "per-skill-qualified-reviewer-pool-domain-critical-fail-closed"
        )
        self.assertFalse(self.module._professional_completeness_formal_ready(axis))

    def test_schema_three_exact_inventory_vote_and_criterion_counts_fail_closed(
        self,
    ) -> None:
        report = _content_readiness_payload()
        _set_completeness_decision(report)
        valid = report["content_readiness"]["expert"]["professional_completeness"]
        self.assertTrue(self.module._professional_v3_evidence_ready(valid))
        cases = (
            ("qualification_summary", "covered_target_count", (188, 190)),
            (
                "qualification_summary",
                "effective_domain_vote_count",
                (377, 379),
            ),
            (
                "qualification_summary",
                "effective_architecture_vote_count",
                (188, 190),
            ),
            ("evidence_summary", "target_vote_count", (566, 568)),
            ("evidence_summary", "criterion_result_count", (5669, 5671)),
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
                "mode": "carried-forward",
                "origin_depth": 1,
                "origin_decision": {
                    "path": "evals/expert-panel/origin/panel/decision.json",
                    "sha256": "a" * 64,
                    "kind": "changeforge.professional-completeness-panel-decision",
                    "axis": "professional-completeness",
                    "review_id": "origin",
                },
                "origin_target_decision_fingerprint": "b" * 64,
                "origin_package_fingerprint": "c" * 64,
                "current_package_fingerprint": disposition[
                    "package_fingerprint"
                ],
                "carry_basis": "review-visible-binding-unchanged",
            }
        axis.update(
            {
                "reviewer_pool_size": 0,
                "fresh_target_count": 0,
                "carried_forward_target_count": 189,
                "review_cost": {
                    "fresh_vote_count": 0,
                    "carried_forward_vote_count": 567,
                    "effective_vote_count": 567,
                    "fresh_criterion_result_count": 0,
                    "carried_forward_criterion_result_count": 5670,
                    "effective_criterion_result_count": 5670,
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
        axis["carried_forward_target_count"] = 188
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
        axis["carried_forward_target_count"] = 189
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
            locked = contracts["final_goal_contract"][
                "professional_review_cost_fixtures"
            ]["locked_current_catalog"]
            locked["cases_fingerprint"] = "f" * 64
            fixture[
                "routing_neutral_isolated_material_binding_sensitivity"
            ]["cases_fingerprint"] = "f" * 64
            target.write_text(json.dumps(contracts), encoding="utf-8")
            self.assertEqual(
                [],
                self.module._professional_review_cost_fixture_errors(
                    "fixture.json", fixture, root=root
                ),
            )

        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            locked["professional_packages_fingerprint"],
            source,
        )
        self.assertNotIn("47475069", source)

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
            "reports/professionalism-release-readiness.json",
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
                "content_readiness.schema_version must equal 9" in error
                for error in errors
            ),
            errors,
        )

    def test_dual_axis_nested_schema_and_identity_fail_closed(self) -> None:
        report = _content_readiness_payload()
        readability = report["content_readiness"]["expert"]["readability"]
        readability["unknown_contract_field"] = True
        errors = self.module._content_readiness_errors("fixture.json", report)
        self.assertTrue(any("fields do not match schema 9" in item for item in errors), errors)

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
            applied=188,
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
        self.assertTrue(any("189-package zero-correction" in item for item in errors), errors)
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
        self.assertEqual([], self.module._release_gate_errors("fixture.json", report))

        report["root_content_summary"]["semantic_lifecycle_formal_release_ready"] = True
        report["release_blockers"] = []
        report["release_gate"] = "release-ready"
        self.assertEqual([], self.module._release_gate_errors("fixture.json", report))

    def test_professionalism_reports_must_match_each_other_completely(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            release = root / "reports/professionalism-release-readiness.json"
            report = json.loads(release.read_text(encoding="utf-8"))
            report["root_content_summary"]["source_fingerprint"] = "e" * 64
            report["content_readiness"]["root"]["source_fingerprint"] = "e" * 64
            report["coverage_gate_summary"]["pass_count"] = 3
            release.write_text(json.dumps(report), encoding="utf-8")

            errors = self.module._static_report_errors(root, enforce_fresh=False)

            self.assertTrue(
                any("complete root_content_summary" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("complete coverage_gate_summary" in error for error in errors),
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
            errors = self.module._static_report_errors(root, enforce_fresh=False)
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
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(any("cannot fail without an error blocker" in item for item in errors), errors)

            self._write_reports(root)
            for relative in self.module.CONTENT_READINESS_REPORTS:
                path = root / relative
                report = json.loads(path.read_text(encoding="utf-8"))
                report.pop("blockers")
                path.write_text(json.dumps(report), encoding="utf-8")
            errors = self.module._static_report_errors(root, enforce_fresh=False)
            self.assertTrue(any("must contain a blockers list" in item for item in errors), errors)

    def test_freshness_rejects_consistent_stale_source_and_same_fingerprint_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            canonical = self._read_professionalism_reports(root)
            reports = copy.deepcopy(canonical)
            for report in reports.values():
                report["root_content_summary"]["agent_facing_root_documents"] = 999
            self.assertEqual(
                {
                    report["root_content_summary"]["source_fingerprint"]
                    for report in reports.values()
                },
                {"b" * 64},
            )

            errors = self.module._professionalism_freshness_errors(
                reports, canonical
            )

            self.assertTrue(
                any("non-canonical root_content_summary" in item for item in errors),
                errors,
            )

    def test_freshness_rejects_consistent_forged_expert_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_reports(root)
            canonical = self._read_professionalism_reports(root)
            reports = copy.deepcopy(canonical)
            for report in reports.values():
                expert = report["content_readiness"]["expert"]
                expert["deprecated_expert_content_review_complete"] = True
                report["content_readiness"]["aggregate"][
                    "readability_review_current"
                ] = True

            self.assertEqual([], self.module._professionalism_cross_report_errors(reports))
            errors = self.module._professionalism_freshness_errors(
                reports, canonical
            )
            self.assertTrue(
                any("non-canonical content_readiness" in item for item in errors),
                errors,
            )

    def test_all_four_professionalism_artifacts_are_byte_canonical(self) -> None:
        markdown = {
            "reports/professionalism-regression-report.md",
            "reports/professionalism-release-readiness.md",
        }
        self.assertTrue(markdown.issubset(set(self.module.REQUIRED)))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            expected = {
                relative: f"canonical:{relative}\n".encode("utf-8")
                for relative in self.module.PROFESSIONALISM_CANONICAL_ARTIFACTS
            }
            for relative, content in expected.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            self.assertEqual(
                [],
                self.module._professionalism_artifact_freshness_errors(
                    root, expected
                ),
            )

            for relative in sorted(markdown):
                path = root / relative
                with self.subTest(relative=relative, mutation="deleted"):
                    path.unlink()
                    errors = self.module._professionalism_artifact_freshness_errors(
                        root, expected
                    )
                    self.assertTrue(
                        any(
                            f"missing canonical professionalism artifact: {relative}"
                            in item
                            for item in errors
                        ),
                        errors,
                    )
                    path.write_bytes(expected[relative])
                with self.subTest(relative=relative, mutation="tampered"):
                    path.write_bytes(expected[relative] + b"tampered\n")
                    errors = self.module._professionalism_artifact_freshness_errors(
                        root, expected
                    )
                    self.assertTrue(
                        any(
                            f"professionalism artifact {relative} differs" in item
                            and "current_sha256=" in item
                            and "canonical_sha256=" in item
                            for item in errors
                        ),
                        errors,
                    )
                    path.write_bytes(expected[relative])

            json_relative = "reports/professionalism-release-readiness.json"
            (root / json_relative).write_bytes(expected[json_relative] + b" \n")
            errors = self.module._professionalism_artifact_freshness_errors(
                root, expected
            )
            self.assertTrue(
                any(
                    f"professionalism artifact {json_relative} differs" in item
                    for item in errors
                ),
                errors,
            )

    def test_core_principles_outcome_reports_are_required_assets(self) -> None:
        self.assertTrue(
            {
                "reports/core-principles-outcomes.json",
                "reports/core-principles-outcomes.md",
                "scripts/eval-core-principles.py",
                "src/control-model/core-contracts.json",
            }.issubset(set(self.module.REQUIRED))
        )

    def test_core_principles_report_rejects_alternate_contract_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "scripts").mkdir()
            (root / "reports").mkdir()
            (root / "scripts/eval-core-principles.py").write_text(
                "def validate_saved_report(root, report):\n    return []\n\n"
                "def render_markdown(report):\n    return '# projection\\n'\n",
                encoding="utf-8",
            )
            (root / "reports/core-principles-outcomes.json").write_text(
                json.dumps(
                    {
                        "contract_source": "src/control-model/alternate.json"
                    }
                ),
                encoding="utf-8",
            )
            (root / "reports/core-principles-outcomes.md").write_text(
                "# projection\n", encoding="utf-8"
            )

            errors = self.module._core_principles_report_errors(root)

            self.assertTrue(
                any("contract_source must equal the canonical" in error for error in errors),
                errors,
            )

    def test_core_principles_productization_accepts_canonical_stub_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "scripts").mkdir()
            (root / "reports").mkdir()
            (root / "scripts/eval-core-principles.py").write_text(
                "def validate_saved_report(root, report):\n    return []\n\n"
                "def render_markdown(report):\n    return '# projection\\n'\n",
                encoding="utf-8",
            )
            (root / "reports/core-principles-outcomes.json").write_text(
                json.dumps(
                    {
                        "contract_source": self.module.CORE_PRINCIPLES_CONTRACT_SOURCE
                    }
                ),
                encoding="utf-8",
            )
            (root / "reports/core-principles-outcomes.md").write_text(
                "# projection\n", encoding="utf-8"
            )

            self.assertEqual(
                [], self.module._core_principles_report_errors(root)
            )

    def test_core_principles_productization_bounds_malformed_report_errors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "scripts").mkdir()
            (root / "reports").mkdir()
            script = root / "scripts/eval-core-principles.py"
            report_path = root / "reports/core-principles-outcomes.json"
            markdown_path = root / "reports/core-principles-outcomes.md"
            markdown_path.write_text("# projection\n", encoding="utf-8")

            script.write_text(
                "def validate_saved_report(root, report):\n"
                "    return ['closed schema rejection']\n\n"
                "def render_markdown(report):\n    raise AssertionError('must not run')\n",
                encoding="utf-8",
            )
            report_path.write_text("[]\n", encoding="utf-8")
            errors = self.module._core_principles_report_errors(root)
            self.assertTrue(
                any("contract_source must equal the canonical" in item for item in errors),
                errors,
            )
            self.assertTrue(
                any("closed schema rejection" in item for item in errors), errors
            )

            script.write_text(
                "def validate_saved_report(root, report):\n"
                "    raise TypeError('PRIVATE_SCHEMA_DETAIL')\n\n"
                "def render_markdown(report):\n    return '# projection\\n'\n",
                encoding="utf-8",
            )
            report_path.write_text(
                json.dumps(
                    {
                        "contract_source": self.module.CORE_PRINCIPLES_CONTRACT_SOURCE
                    }
                ),
                encoding="utf-8",
            )
            errors = self.module._core_principles_report_errors(root)
            self.assertTrue(
                any("validation raised TypeError" in item for item in errors), errors
            )
            self.assertNotIn("PRIVATE_SCHEMA_DETAIL", json.dumps(errors))

            script.write_text(
                "def validate_saved_report(root, report):\n"
                "    raise SystemExit(7)\n\n"
                "def render_markdown(report):\n    return '# projection\\n'\n",
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit) as raised:
                self.module._core_principles_report_errors(root)
            self.assertEqual(7, raised.exception.code)

            script.write_text(
                "def validate_saved_report(root, report):\n"
                "    raise KeyboardInterrupt()\n\n"
                "def render_markdown(report):\n    return '# projection\\n'\n",
                encoding="utf-8",
            )
            with self.assertRaises(KeyboardInterrupt):
                self.module._core_principles_report_errors(root)

    def test_missing_core_principles_evaluator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with mock.patch.object(
                self.module, "_docs_errors", return_value=[]
            ), mock.patch.object(
                self.module, "_static_report_errors", return_value=[]
            ), mock.patch.object(
                self.module, "_core_principles_report_errors", return_value=[]
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


if __name__ == "__main__":
    unittest.main()
