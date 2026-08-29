#!/usr/bin/env python3
"""Validate hookless product documentation, reports, and release assets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import expert_panel_contracts as panel_contracts
from validation_utils import (
    PROFESSIONAL_REVIEW_COST_FIELDS,
    PROFESSIONAL_REVIEW_COST_LIMITATIONS,
    PROFESSIONAL_REVIEW_COST_TEXT_FIELDS,
    PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS,
    PROFESSIONAL_REVIEW_FIXTURE_LIMITATIONS,
    validate_expert_panel_release_manifest,
    validate_core_contracts,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "docs/HOOKLESS_ARCHITECTURE.md",
    "docs/AI_CONTROL_BOUNDARIES.md",
    "docs/MIGRATING_TO_HOOKLESS.md",
    "docs/INSTALLATION.md",
    "docs/VALIDATION.md",
    "docs/BENCHMARKS.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "reports/hookless-control-plane-eval.json",
    "reports/rendered-context-budget.json",
    "reports/context-control-plane-eval.json",
    "reports/routing-eval.json",
    "reports/skill-professionalism-eval.json",
    "reports/professionalism-regression-report.json",
    "reports/installation-validation.json",
    "schemas/marketplace-index.schema.json",
    "src/control-model/core-contracts.json",
    "scripts/build.py",
    "scripts/eval-core-principles.py",
    "scripts/expert_panel_review.py",
    "scripts/professional_completeness_carry_forward.py",
    "scripts/fixture_capsule_contract.py",
    "scripts/quickstart.py",
    "scripts/export-marketplace-index.py",
    "scripts/generate-marketplace-catalog.py",
    "scripts/validate-marketplace-index.py",
    "scripts/validate-docs-consistency.py",
)
FORBIDDEN = (
    "src/toolbox",
    "registry/toolbox.yaml",
    "src/hook-runtime",
    "src/runtime_governance",
    "src/project_memory",
    "src/repository_intelligence",
    "src/validation_broker",
    "src/trajectory",
)
STATIC_REPORT_CONTRACTS = {
    "reports/hookless-control-plane-eval.json": ("status", "pass"),
    "reports/rendered-context-budget.json": ("status", "pass"),
    "reports/context-control-plane-eval.json": ("status", "pass"),
    "reports/routing-eval.json": ("status", "pass"),
    "reports/professionalism-regression-report.json": ("status", "current-contract-pass"),
    "reports/installation-validation.json": ("status", "pass"),
}
STATIC_REPORT_EVIDENCE_SCOPES = {
    "reports/rendered-context-budget.json": "deterministic-rendered-artifacts",
}
CONTENT_READINESS_REPORTS = {
    "reports/professionalism-regression-report.json",
}
AUTHORING_GATE_PASS = "current-contract-pass"
AUTHORING_GATE_FAIL = "current-contract-fail"
RELEASE_GATE_PASS = "release-ready"
RELEASE_GATE_FAIL = "release-not-ready"
READABILITY_RELEASE_BLOCKER_CATEGORY = "readability-review-release-gate"
PROFESSIONAL_COMPLETENESS_RELEASE_BLOCKER_CATEGORY = (
    "professional-completeness-review-release-gate"
)
CORE_PRINCIPLES_CONTRACT_SOURCE = "src/control-model/core-contracts.json"
PROFESSIONALISM_REPORT_FIELDS = {
    "reports/professionalism-regression-report.json": {
        "schema_version",
        "status",
        "mode",
        "strict",
        "authoring_gate",
        "release_gate",
        "baseline_comparison",
        "evidence_scope",
        "content_audit_summary",
        "ai_readability_summary",
        "reference_content_summary",
        "root_content_summary",
        "content_readiness",
        "coverage_gate_summary",
        "professional_review_cost_fixtures",
        "limitations",
        "blockers",
        "release_blockers",
        "advisories",
        "summary",
    }
}
PROFESSIONALISM_REPORT_SCHEMA_VERSION = 4
LEGACY_PROFESSIONALISM_REPORT_SCHEMA_VERSION = 3
SKILL_REVIEW_STATES = {
    "BLOCK",
    "TIGHTEN_BODY",
    "REVIEW_READABILITY",
    "REVIEW_CONTEXT",
    "KEEP_WITH_ADVISORY",
    "KEEP",
}
SKILL_REVIEW_REASONS = {
    "classification_block",
    "ai_readability_hard_fail",
    "ai_readability_compound_bullet",
    "classification_tighten_body",
    "ai_readability_tighten",
    "ai_readability_review_as_complex",
    "classification_review_density",
    "professional_governed_lines_over_80",
    "professional_projection_pushes_physical_lines_over_80",
    "weak_front_loaded_action",
    "control_boilerplate_risk",
    "actionable_duplicate_content",
    "description_authoring_advisory",
    "split_candidate",
}
REFERENCE_READINESS_FIELDS = {
    "scope",
    "source_fingerprint",
    "strict_ready_basis",
    "structural_strict_ready",
    "semantic_triage_complete",
    "strict_ready",
}
ROOT_READINESS_FIELDS = set(REFERENCE_READINESS_FIELDS)
EXPERT_READINESS_FIELDS = {
    "readability",
    "professional_completeness",
    "deprecated_expert_content_review_complete",
}
READABILITY_REVIEW_FIELDS = {
    "scope",
    "panel_kind",
    "decision_complete",
    "storage_current",
    "source_current",
    "accepted_for_formal",
    "decision_method",
    "panel_review_id",
    "panel_size",
    "attestation_status",
    "attestation_source",
    "attestation_schema_version",
    "panel_artifact_schema_version",
    "attestation_config_fingerprint",
    "source_fingerprints",
    "current_source_fingerprints",
    "attested_by",
    "attested_on",
    "evidence",
    "density_dispositions",
    "readability_dispositions",
    "actionability_dispositions",
    "required_density_disposition_count",
    "applied_density_disposition_count",
    "required_readability_disposition_count",
    "applied_readability_disposition_count",
    "required_actionability_disposition_count",
    "applied_actionability_disposition_count",
    "accepted_current_actionability_count",
    "detector_false_positive_count",
    "rewrite_required_count",
    "tracked_tightening_count",
    "blocker_count",
    "limitations",
}
PROFESSIONAL_COMPLETENESS_REVIEW_FIELDS = {
    "scope",
    "panel_kind",
    "decision_complete",
    "storage_current",
    "source_current",
    "accepted_for_formal",
    "decision_method",
    "panel_review_id",
    "panel_size",
    "reviewer_pool_size",
    "attestation_status",
    "attestation_source",
    "attestation_schema_version",
    "attestation_config_fingerprint",
    "source_fingerprints",
    "current_source_fingerprints",
    "attested_by",
    "attested_on",
    "evidence",
    "panel_artifact_schema_version",
    "evidence_contract_satisfied",
    "qualification_summary",
    "evidence_summary",
    "review_contract_fingerprint",
    "current_review_contract_fingerprint",
    "review_contract_current",
    "review_plan_fingerprint",
    "current_review_plan_fingerprint",
    "review_plan_current",
    "review_binding_current",
    "provenance_current",
    "round_lifecycle_current",
    "round_lifecycle",
    "review_cost_current",
    "review_cost",
    "professional_dispositions",
    "required_target_count",
    "fresh_target_count",
    "carried_forward_target_count",
    "applied_target_count",
    "accepted_current_count",
    "correction_count",
    "unresolved_professional_disagreement_count",
    "limitations",
}
AGGREGATE_READINESS_FIELDS = {
    "structural_strict_ready",
    "semantic_triage_complete",
    "readability_review_current",
    "professional_completeness_review_current",
}
EXPERT_DECISION_METHOD = "three-independent-experts-majority"
PROFESSIONAL_COMPLETENESS_DECISION_METHOD = (
    "per-skill-qualified-reviewer-pool-domain-critical-fail-closed"
)
PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD = (
    "exact-package-carry-forward-qualified-reviewer-pool-domain-critical-fail-closed"
)
READABILITY_PANEL_KIND = "readability"
PROFESSIONAL_COMPLETENESS_PANEL_KIND = "professional-completeness"
PROFESSIONAL_PACKAGE_COUNT = 189
PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA = {
    "professional-correctness",
    "erroneous-rules",
    "material-omissions",
    "failure-modes",
    "boundary-conditions",
    "verification-methods",
}
PROFESSIONAL_ORDINARY_CRITERIA = {
    "adjacent-overlap-or-gap",
    "generic-knowledge-pollution",
    "reference-high-risk-coverage",
    "output-verifiability",
}
PROFESSIONAL_UNRESOLVED_DISPOSITION = "unresolved-professional-disagreement"
PROFESSIONAL_SCHEMA3_DISPOSITION_FIELDS = {
    "skill_id",
    "package_material_binding",
    "review_unit_binding",
    "disposition",
    "majority_disposition",
    "domain_critical_defects",
    "ordinary_criterion_disposition",
    "ordinary_criterion_defects",
    "reason_codes",
    "rationales",
    "review_dependencies",
    "evidence_metrics",
    "provenance",
    "target_decision_fingerprint",
}
PROFESSIONAL_COMPACT_ORIGIN_FIELDS = {
    "origin_review_id",
    "origin_commit",
    "origin_verdict_digest",
}
PROFESSIONAL_IDENTIFIER_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,126}[a-z0-9])?$"
)
READABILITY_FINGERPRINT_FIELDS = set(
    panel_contracts.READABILITY_SOURCE_FINGERPRINT_KEYS
)
LEGACY_READABILITY_FINGERPRINT_FIELDS = {
    "reference_content",
    "root_content",
    "ai_readability",
}
PROFESSIONAL_COMPLETENESS_FINGERPRINT_FIELDS = {"professional_packages"}
PROFESSIONAL_COMPLETENESS_V3_FINGERPRINT_FIELDS: set[str] = set()
READABILITY_STATUSES = {
    "missing-evidence",
    "panel-majority-stale",
    "panel-majority-incomplete-coverage",
    "panel-majority-pending-checkin",
    "panel-majority-tracked-tightening",
    "panel-majority-actionability-rewrite-required",
    "panel-majority-detector-update-required",
    "panel-majority-blocked",
    "panel-majority-current",
    "deprecated-combined-attestation",
}
PROFESSIONAL_COMPLETENESS_STATUSES = {
    "missing-evidence",
    "panel-majority-stale",
    "panel-majority-incomplete-coverage",
    "panel-majority-pending-checkin",
    "panel-majority-corrections-required",
    "panel-domain-disagreement-unresolved",
    "panel-majority-evidence-insufficient",
    "panel-majority-invalid-lineage",
    "panel-review-cost-policy-not-satisfied",
    "panel-legacy-nonformal",
    "panel-majority-current",
}


def _is_sha256(value: str) -> bool:
    return bool(len(value) == 64 and all(char in "0123456789abcdef" for char in value))


def _non_negative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _axis_common_errors(
    relative: str,
    *,
    label: str,
    axis: object,
    expected_scope: str,
    expected_kind: str,
    fingerprint_fields: set[str],
    current_fingerprint_fields: set[str] | None = None,
    allowed_statuses: set[str],
    allowed_decision_methods: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(axis, dict):
        return [f"static report {relative} {label} must be a mapping"]
    if axis.get("scope") != expected_scope or axis.get("panel_kind") != expected_kind:
        errors.append(f"static report {relative} {label} belongs to the wrong review axis")
    for field in (
        "decision_complete",
        "storage_current",
        "source_current",
        "accepted_for_formal",
    ):
        if type(axis.get(field)) is not bool:
            errors.append(f"static report {relative} {label}.{field} must be a boolean")
    decision_methods = allowed_decision_methods or {EXPERT_DECISION_METHOD}
    if axis.get("decision_method") not in decision_methods:
        errors.append(f"static report {relative} {label} decision_method is invalid")
    if axis.get("attestation_schema_version") != 5:
        errors.append(
            f"static report {relative} {label}.attestation_schema_version must equal 5"
        )
    if not _non_negative_int(axis.get("panel_size")):
        errors.append(
            f"static report {relative} {label}.panel_size must be a non-negative integer"
        )
    status = axis.get("attestation_status")
    if status not in allowed_statuses:
        errors.append(f"static report {relative} {label}.attestation_status is invalid")
    if not isinstance(axis.get("attestation_source"), str) or not axis[
        "attestation_source"
    ].strip():
        errors.append(
            f"static report {relative} {label}.attestation_source must be non-blank"
        )
    config_fingerprint = axis.get("attestation_config_fingerprint")
    if not isinstance(config_fingerprint, str) or not _is_sha256(config_fingerprint):
        errors.append(
            f"static report {relative} {label}.attestation_config_fingerprint "
            "must be lowercase sha256"
        )
    fingerprints = axis.get("source_fingerprints")
    current_fingerprints = axis.get("current_source_fingerprints")
    expected_current_fields = (
        fingerprint_fields
        if current_fingerprint_fields is None
        else current_fingerprint_fields
    )
    if not isinstance(fingerprints, dict) or set(fingerprints) != fingerprint_fields:
        errors.append(
            f"static report {relative} {label}.source_fingerprints are malformed"
        )
        fingerprints = {}
    if not isinstance(current_fingerprints, dict) or set(
        current_fingerprints
    ) != expected_current_fields or any(
        not isinstance(value, str) or not _is_sha256(value)
        for value in current_fingerprints.values()
    ):
        errors.append(
            f"static report {relative} {label}.current_source_fingerprints "
            "must contain current lowercase sha256 values"
        )
        current_fingerprints = {}
    decision_complete = axis.get("decision_complete") is True
    if decision_complete:
        if any(
            not isinstance(value, str) or not _is_sha256(value)
            for value in fingerprints.values()
        ):
            errors.append(
                f"static report {relative} {label} decision fingerprints are malformed"
            )
        if axis.get("panel_size") != 3:
            errors.append(f"static report {relative} {label}.panel_size must equal 3")
        for field in ("panel_review_id", "attested_by", "attested_on"):
            if not isinstance(axis.get(field), str) or not axis[field].strip():
                errors.append(
                    f"static report {relative} {label}.{field} must be non-blank "
                    "for a completed decision"
                )
    else:
        if axis.get("panel_size") != 0:
            errors.append(
                f"static report {relative} {label}.panel_size must be zero without evidence"
            )
        if any(axis.get(field) is not None for field in ("panel_review_id", "attested_by", "attested_on")):
            errors.append(
                f"static report {relative} {label} missing evidence carries panel identity"
            )
        if fingerprints and any(value is not None for value in fingerprints.values()):
            errors.append(
                f"static report {relative} {label} missing evidence carries source claims"
            )
    evidence = axis.get("evidence")
    if not isinstance(evidence, list) or not all(
        isinstance(item, dict)
        and set(item) == {"path", "sha256"}
        and isinstance(item.get("path"), str)
        and bool(item["path"].strip())
        and isinstance(item.get("sha256"), str)
        and _is_sha256(item["sha256"])
        for item in evidence
    ):
        errors.append(
            f"static report {relative} {label}.evidence must contain path and sha256 mappings"
        )
        evidence = []
    elif [item["path"] for item in evidence] != sorted(
        {item["path"] for item in evidence}
    ):
        errors.append(
            f"static report {relative} {label}.evidence paths must be sorted and unique"
        )
    if decision_complete is not bool(evidence):
        errors.append(
            f"static report {relative} {label} decision completeness disagrees with evidence"
        )
    limitations = axis.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        errors.append(
            f"static report {relative} {label}.limitations must be a non-empty string list"
        )
    source_current = bool(
        decision_complete and fingerprints == current_fingerprints
    )
    if axis.get("source_current") is not source_current:
        errors.append(
            f"static report {relative} {label}.source_current disagrees with fingerprints"
        )
    if axis.get("storage_current") is True and not decision_complete:
        errors.append(
            f"static report {relative} {label}.storage_current requires a completed decision"
        )
    if axis.get("accepted_for_formal") is True and (
        not decision_complete
        or axis.get("storage_current") is not True
        or axis.get("source_current") is not True
        or status != "panel-majority-current"
    ):
        errors.append(
            f"static report {relative} {label} accepted_for_formal is not current"
        )
    fixed_storage_noncurrent = bool(
        not decision_complete
        and axis.get("panel_artifact_schema_version") is None
        and axis.get("panel_size") == 0
        and all(
            axis.get(field) is None
            for field in ("panel_review_id", "attested_by", "attested_on")
        )
        and all(value is None for value in fingerprints.values())
        and evidence == []
        and axis.get("storage_current") is False
        and axis.get("source_current") is False
        and axis.get("accepted_for_formal") is False
    )
    if status == "missing-evidence" and (
        decision_complete
        or axis.get("storage_current") is not False
        or axis.get("source_current") is not False
        or axis.get("accepted_for_formal") is not False
    ):
        errors.append(
            f"static report {relative} {label} missing-evidence state is contradictory"
        )
    if status == "panel-majority-stale" and (
        not fixed_storage_noncurrent
        and (
            not decision_complete
            or axis.get("source_current") is not False
            or axis.get("accepted_for_formal") is not False
        )
    ):
        errors.append(f"static report {relative} {label} stale state is contradictory")
    if status == "panel-majority-pending-checkin" and (
        not fixed_storage_noncurrent
        and (
            not decision_complete
            or axis.get("source_current") is not True
            or axis.get("storage_current") is not False
            or axis.get("accepted_for_formal") is not False
        )
    ):
        errors.append(
            f"static report {relative} {label} pending-checkin state is contradictory"
        )
    if status == "panel-majority-incomplete-coverage" and (
        not decision_complete
        or axis.get("source_current") is not True
        or axis.get("accepted_for_formal") is not False
    ):
        errors.append(
            f"static report {relative} {label} incomplete-coverage state is contradictory"
        )
    return errors


def _readability_formal_ready(axis: object) -> bool:
    return bool(
        isinstance(axis, dict)
        and axis.get("panel_kind") == READABILITY_PANEL_KIND
        and axis.get("scope") == "ai-readability-and-density"
        and axis.get("decision_complete") is True
        and axis.get("storage_current") is True
        and axis.get("source_current") is True
        and axis.get("accepted_for_formal") is True
        and axis.get("decision_method") == EXPERT_DECISION_METHOD
        and axis.get("panel_size") == 3
        and axis.get("attestation_schema_version") == 5
        and axis.get("panel_artifact_schema_version") == 2
        and axis.get("attestation_status") == "panel-majority-current"
        and axis.get("tracked_tightening_count") == 0
        and axis.get("detector_false_positive_count") == 0
        and axis.get("rewrite_required_count") == 0
        and axis.get("blocker_count") == 0
        and axis.get("required_density_disposition_count")
        == axis.get("applied_density_disposition_count")
        and axis.get("required_readability_disposition_count")
        == axis.get("applied_readability_disposition_count")
        and axis.get("required_actionability_disposition_count")
        == axis.get("applied_actionability_disposition_count")
    )


def _professional_v2_evidence_ready(axis: object) -> bool:
    if not isinstance(axis, dict) or axis.get("panel_artifact_schema_version") != 2:
        return False
    qualification = axis.get("qualification_summary")
    evidence = axis.get("evidence_summary")
    qualification_fields = {
        "covered_target_count",
        "required_domain_experts_per_target",
        "required_architecture_experts_per_target",
        "per_target_panel_size",
        "reviewer_pool_size",
        "domain_reviewer_count",
        "architecture_reviewer_count",
    }
    if not isinstance(qualification, dict) or set(qualification) != qualification_fields:
        return False
    reviewer_pool_size = qualification.get("reviewer_pool_size")
    domain_reviewer_count = qualification.get("domain_reviewer_count")
    architecture_reviewer_count = qualification.get("architecture_reviewer_count")
    if (
        qualification.get("covered_target_count") != PROFESSIONAL_PACKAGE_COUNT
        or qualification.get("required_domain_experts_per_target") != 2
        or qualification.get("required_architecture_experts_per_target") != 1
        or qualification.get("per_target_panel_size") != 3
        or type(reviewer_pool_size) is not int
        or reviewer_pool_size < 3
        or reviewer_pool_size != axis.get("reviewer_pool_size")
        or type(domain_reviewer_count) is not int
        or domain_reviewer_count < 2
        or type(architecture_reviewer_count) is not int
        or architecture_reviewer_count < 1
        or domain_reviewer_count + architecture_reviewer_count
        != reviewer_pool_size
    ):
        return False
    evidence_fields = {
        "required_adjacency_candidate_count",
        "criterion_result_count",
        "criterion_anchor_binding_count",
        "criterion_assertion_count",
        "evidence_anchor_count",
        "examined_failure_mode_count",
        "examined_omission_candidate_count",
        "examined_adjacency_count",
        "examined_required_adjacency_count",
        "reviewer_added_adjacency_count",
        "proof_limit_count",
        "qualification_claim_count",
    }
    if not isinstance(evidence, dict) or set(evidence) != evidence_fields:
        return False
    if not all(type(evidence.get(field)) is int for field in evidence_fields):
        return False
    reviewed_votes = PROFESSIONAL_PACKAGE_COUNT * 3
    criterion_results = reviewed_votes * 10
    required_adjacency_candidate_count = evidence.get(
        "required_adjacency_candidate_count"
    )
    if not _non_negative_int(required_adjacency_candidate_count):
        return False
    required_adjacency_reviews = required_adjacency_candidate_count * 3
    return bool(
        evidence["criterion_result_count"] == criterion_results
        and evidence["criterion_assertion_count"] >= criterion_results
        and evidence["criterion_anchor_binding_count"]
        >= evidence["criterion_assertion_count"]
        and evidence["evidence_anchor_count"] >= reviewed_votes * 2
        and evidence["examined_failure_mode_count"] >= reviewed_votes * 2
        and evidence["examined_omission_candidate_count"] >= reviewed_votes * 2
        and evidence["examined_required_adjacency_count"]
        == required_adjacency_reviews
        and evidence["reviewer_added_adjacency_count"] >= 0
        and evidence["examined_adjacency_count"]
        == evidence["examined_required_adjacency_count"]
        + evidence["reviewer_added_adjacency_count"]
        and evidence["proof_limit_count"] >= reviewed_votes
        and evidence["qualification_claim_count"] >= reviewer_pool_size
    )


def _professional_v3_evidence_ready(axis: object) -> bool:
    if not isinstance(axis, dict) or axis.get("panel_artifact_schema_version") != 3:
        return False
    qualification = axis.get("qualification_summary")
    evidence = axis.get("evidence_summary")
    if not isinstance(qualification, dict) or set(qualification) != {
        "covered_target_count",
        "required_domain_experts_per_target",
        "required_architecture_experts_per_target",
        "per_target_panel_size",
        "fresh_reviewer_pool_size",
        "effective_domain_vote_count",
        "effective_architecture_vote_count",
    }:
        return False
    if (
        qualification["covered_target_count"] != 189
        or qualification["required_domain_experts_per_target"] != 2
        or qualification["required_architecture_experts_per_target"] != 1
        or qualification["per_target_panel_size"] != 3
        or not _non_negative_int(qualification["fresh_reviewer_pool_size"])
        or qualification["fresh_reviewer_pool_size"]
        != axis.get("reviewer_pool_size")
        or qualification["effective_domain_vote_count"] != 378
        or qualification["effective_architecture_vote_count"] != 189
    ):
        return False
    evidence_fields = {
        "target_vote_count",
        "required_adjacency_candidate_count",
        "criterion_result_count",
        "criterion_anchor_binding_count",
        "criterion_assertion_count",
        "evidence_anchor_count",
        "examined_failure_mode_count",
        "examined_omission_candidate_count",
        "examined_adjacency_count",
        "examined_required_adjacency_count",
        "reviewer_added_adjacency_count",
        "proof_limit_count",
        "qualification_claim_count",
    }
    if (
        not isinstance(evidence, dict)
        or set(evidence) != evidence_fields
        or any(not _non_negative_int(value) for value in evidence.values())
    ):
        return False
    return bool(
        evidence["target_vote_count"] == 567
        and evidence["criterion_result_count"] == 5670
        and evidence["criterion_assertion_count"] >= 5670
        and evidence["criterion_anchor_binding_count"]
        >= evidence["criterion_assertion_count"]
        and evidence["evidence_anchor_count"] >= 1134
        and evidence["examined_failure_mode_count"] >= 1134
        and evidence["examined_omission_candidate_count"] >= 1134
        and evidence["examined_required_adjacency_count"]
        == 3 * evidence["required_adjacency_candidate_count"]
        and evidence["examined_adjacency_count"]
        == evidence["examined_required_adjacency_count"]
        + evidence["reviewer_added_adjacency_count"]
        and evidence["proof_limit_count"] >= 567
        and evidence["qualification_claim_count"] >= 567
    )


def _professional_review_formal_round_policy(
    *, root: Path = ROOT
) -> tuple[dict[str, int], str] | None:
    try:
        contracts = json.loads(
            (root / CORE_PRINCIPLES_CONTRACT_SOURCE).read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError):
        return None
    if validate_core_contracts(contracts):
        return None
    try:
        policy = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["formal_round_policy"]
    except (KeyError, TypeError):
        return None
    if (
        not isinstance(policy, dict)
        or set(policy) != PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS
        or policy.get("schema_version") != 1
        or any(
            type(policy.get(field)) is not int or policy[field] < 0
            for field in PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS
            - {"schema_version"}
        )
    ):
        return None
    normalized = dict(policy)
    fingerprint = hashlib.sha256(
        json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return normalized, fingerprint


def _professional_review_cost_ready(axis: object) -> bool:
    if not isinstance(axis, dict):
        return False
    cost = axis.get("review_cost")
    fresh = axis.get("fresh_target_count")
    carried = axis.get("carried_forward_target_count")
    if (
        not isinstance(cost, dict)
        or set(cost) != PROFESSIONAL_REVIEW_COST_FIELDS
        or not _non_negative_int(fresh)
        or not _non_negative_int(carried)
        or fresh + carried != 189
        or cost.get("limitations") != PROFESSIONAL_REVIEW_COST_LIMITATIONS
    ):
        return False
    integer_fields = (
        PROFESSIONAL_REVIEW_COST_FIELDS - PROFESSIONAL_REVIEW_COST_TEXT_FIELDS
    )
    if any(not _non_negative_int(cost.get(field)) for field in integer_fields):
        return False
    policy_result = _professional_review_formal_round_policy()
    if policy_result is None:
        return False
    formal_policy, formal_policy_fingerprint = policy_result
    fingerprint = cost.get("formal_round_policy_fingerprint")
    if (
        not isinstance(fingerprint, str)
        or not _is_sha256(fingerprint)
        or fingerprint != formal_policy_fingerprint
    ):
        return False
    denominator = cost["full_rereview_deduplicated_capsule_input_bytes_proxy"]
    full_source = cost[
        "full_rereview_source_material_input_bytes_proxy"
    ]
    actual = cost["canonical_capsule_input_bytes_proxy"]
    required = cost["required_only_capsule_input_bytes_proxy"]
    actual_source = cost["source_material_input_bytes_proxy"]
    required_source = cost[
        "required_only_source_material_input_bytes_proxy"
    ]
    if (
        denominator <= 0
        or full_source <= 0
        or required > actual
        or required_source > actual_source
        or actual_source > full_source
        or actual < actual_source
        or required < required_source
    ):
        return False
    actual_metadata = actual - actual_source
    required_metadata = required - required_source
    if actual_metadata < required_metadata:
        return False
    metadata_overhead = actual_metadata - required_metadata
    expected_metadata_overhead_ratio = (
        metadata_overhead * 1_000_000 // required_metadata
        if required_metadata
        else 0
    )
    if (
        cost["fresh_vote_count"] != 3 * fresh
        or cost["carried_forward_vote_count"] != 3 * carried
        or cost["effective_vote_count"] != 567
        or cost["fresh_criterion_result_count"] != 30 * fresh
        or cost["carried_forward_criterion_result_count"] != 30 * carried
        or cost["effective_criterion_result_count"] != 5670
        or cost["input_ratio_ppm"]
        != actual * 1_000_000 // denominator
        or cost["required_only_input_ratio_ppm"]
        != required * 1_000_000 // denominator
        or cost["source_material_coverage_ratio_ppm"]
        != actual_source * 1_000_000 // full_source
        or cost[
            "reviewer_added_source_material_input_bytes_proxy"
        ]
        != actual_source - required_source
        or cost[
            "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy"
        ]
        != metadata_overhead
        or cost[
            "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ]
        != expected_metadata_overhead_ratio
        or metadata_overhead * 1_000_000
        > formal_policy[
            "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ]
        * required_metadata
        or cost[
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ]
        > formal_policy[
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ]
        or cost["reviewer_added_unique_relationship_count"]
        > cost["reviewer_added_request_count"]
        or cost["reviewer_added_request_count"]
        > 3 * cost["reviewer_added_unique_relationship_count"]
        or cost["maximum_origin_depth"] > 1
        or cost["plan_lineage_depth"] > 8
    ):
        return False
    status = cost.get("policy_status")
    if fresh == 0:
        return bool(
            axis.get("reviewer_pool_size") == 0
            and all(
                cost[field] == 0
                for field in {
                    "canonical_capsule_input_bytes_proxy",
                    "required_only_capsule_input_bytes_proxy",
                    "required_only_source_material_input_bytes_proxy",
                    "source_material_input_bytes_proxy",
                    "source_material_coverage_ratio_ppm",
                    "reviewer_added_source_material_input_bytes_proxy",
                    "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy",
                    "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm",
                    "reviewer_added_request_count",
                    "reviewer_added_unique_relationship_count",
                    "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
                    "input_ratio_ppm",
                    "required_only_input_ratio_ppm",
                }
            )
            and status == "all-carry-zero-input"
        )
    if axis.get("reviewer_pool_size", 0) < 3:
        return False
    if fresh < 189:
        return bool(
            0 < required < denominator
            and 0 < required_source <= actual_source <= full_source
            and 0 < cost["required_only_input_ratio_ppm"] < 1_000_000
            and required_metadata > 0
            and status == "incremental-reduced-input"
        )
    return bool(
        required == denominator
        and cost["required_only_input_ratio_ppm"] == 1_000_000
        and required_source == full_source
        and cost["source_material_coverage_ratio_ppm"]
        == formal_policy[
            "full_fresh_source_material_coverage_ratio_ppm"
        ]
        and required_metadata > 0
        and status
        in {
            "bootstrap-full-review",
            "contract-change-full-review",
            "lineage-checkpoint-full-review",
            "full-fresh-review",
        }
    )


PROFESSIONAL_REVIEW_COST_SENSITIVITY_FIELDS = {
    "case_count",
    "full_rereview_deduplicated_capsule_input_bytes_proxy",
    "fresh_target_count",
    "input_ratio_ppm",
    "named_isolated_case",
}
LEGACY_PROFESSIONAL_REVIEW_COST_DIGEST_FIELDS = {
    "professional_packages_fingerprint",
    "catalog_fingerprint",
    "material_catalog_fingerprint",
    "full_projection_fingerprint",
    "review_contract_fingerprint",
    "cases_fingerprint",
}


def _normalized_professional_review_cost_sensitivity(
    value: object,
) -> tuple[dict | None, list[str]]:
    if not isinstance(value, dict):
        return None, ["routing-neutral sensitivity must be a mapping"]
    fields = set(value)
    if fields == PROFESSIONAL_REVIEW_COST_SENSITIVITY_FIELDS:
        return copy.deepcopy(value), []
    if fields != (
        PROFESSIONAL_REVIEW_COST_SENSITIVITY_FIELDS
        | LEGACY_PROFESSIONAL_REVIEW_COST_DIGEST_FIELDS
    ):
        return None, ["routing-neutral sensitivity fields are invalid"]
    errors = []
    for field in sorted(LEGACY_PROFESSIONAL_REVIEW_COST_DIGEST_FIELDS):
        digest = value.get(field)
        if not isinstance(digest, str) or not _is_sha256(digest):
            errors.append(f"legacy {field} must be lowercase sha256")
    return (
        {field: copy.deepcopy(value[field]) for field in PROFESSIONAL_REVIEW_COST_SENSITIVITY_FIELDS},
        errors,
    )


def _professional_review_cost_fixture_errors(
    relative: str, fixture: object, *, root: Path = ROOT
) -> list[str]:
    label = "professional_review_cost_fixtures"
    errors = _professional_review_cost_fixture_envelope_errors(relative, fixture)
    if errors or not isinstance(fixture, dict):
        return errors
    if fixture.get("status") != "pass":
        errors.append(
            f"static report {relative} {label} must be a passing schema-1 fixture"
        )
    if fixture.get("unchanged") != {
        "fresh_target_count": 0,
        "carried_forward_target_count": 189,
        "input_ratio_ppm": 0,
    }:
        errors.append(
            f"static report {relative} {label}.unchanged is not exact-carry"
        )
    try:
        contracts = json.loads(
            (root / CORE_PRINCIPLES_CONTRACT_SOURCE).read_text(encoding="utf-8")
        )
        contract_errors = validate_core_contracts(contracts)
        if contract_errors:
            raise ValueError("; ".join(contract_errors))
        authority_thresholds = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["thresholds"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return [
            f"static report {relative} cannot load Final Goal review-cost "
            f"authority: {exc}"
        ]

    sensitivity, sensitivity_errors = _normalized_professional_review_cost_sensitivity(
        fixture.get("routing_neutral_isolated_material_binding_sensitivity")
    )
    errors.extend(
        f"static report {relative} {label} {error}"
        for error in sensitivity_errors
    )
    if sensitivity is not None:
        case_count = sensitivity.get("case_count")
        full_bytes = sensitivity.get(
            "full_rereview_deduplicated_capsule_input_bytes_proxy"
        )
        fresh = sensitivity.get("fresh_target_count")
        ratio = sensitivity.get("input_ratio_ppm")
        named = sensitivity.get("named_isolated_case")
        valid = bool(
            type(case_count) is int
            and case_count == 189
            and type(full_bytes) is int
            and full_bytes > 0
            and isinstance(fresh, dict)
            and set(fresh) == {"min", "sum", "mean_milli", "p95", "max"}
            and all(type(item) is int and item >= 0 for item in fresh.values())
            and fresh["mean_milli"] == fresh["sum"] * 1000 // case_count
            and fresh["min"] <= fresh["p95"] <= fresh["max"]
            and fresh["max"] <= authority_thresholds["maximum_fresh_target_count"]
            and fresh["sum"]
            <= authority_thresholds["maximum_mean_fresh_target_count"] * case_count
            and isinstance(ratio, dict)
            and set(ratio) == {"min", "sum", "mean", "p95", "max"}
            and all(type(item) is int and item >= 0 for item in ratio.values())
            and ratio["mean"] == ratio["sum"] // case_count
            and ratio["min"] <= ratio["p95"] <= ratio["max"]
            and ratio["max"] <= authority_thresholds["maximum_input_ratio_ppm"]
            and ratio["sum"]
            <= authority_thresholds["maximum_mean_input_ratio_ppm"] * case_count
            and isinstance(named, dict)
            and set(named)
            == {
                "skill_id",
                "fresh_target_count",
                "carried_forward_target_count",
                "canonical_capsule_input_bytes_proxy",
                "input_ratio_ppm",
            }
            and named["skill_id"] == "acceptance-criteria-builder"
            and all(
                type(named[field]) is int and named[field] >= 0
                for field in (
                    "fresh_target_count",
                    "carried_forward_target_count",
                    "canonical_capsule_input_bytes_proxy",
                    "input_ratio_ppm",
                )
            )
            and named["fresh_target_count"] + named["carried_forward_target_count"]
            == case_count
            and named["canonical_capsule_input_bytes_proxy"] > 0
            and named["input_ratio_ppm"]
            == named["canonical_capsule_input_bytes_proxy"] * 1_000_000 // full_bytes
        )
        if not valid:
            errors.append(
                f"static report {relative} {label} measured sensitivity "
                "arithmetic, inventory, or thresholds are invalid"
            )
    if fixture.get("representative_routing_adjacency_mutation") != {
        "skill_id": "acceptance-criteria-builder",
        "fresh_target_ids": ["acceptance-criteria-builder"],
        "carried_forward_target_count": 188,
        "reason_codes": ["adjacency-review-binding-changed"],
        "cost_threshold_applied": False,
    }:
        errors.append(
            f"static report {relative} {label} representative routing/adjacency "
            "mutation is stale"
        )
    if fixture.get("review_contract_change") != {
        "fresh_target_count": 189,
        "carried_forward_target_count": 0,
        "input_ratio_ppm": 1_000_000,
    }:
        errors.append(
            f"static report {relative} {label}.review_contract_change must force "
            "a full rereview"
        )
    if fixture.get("thresholds") != authority_thresholds:
        errors.append(
            f"static report {relative} {label}.thresholds disagree with Final Goal"
        )
    if fixture.get("limitations") != PROFESSIONAL_REVIEW_FIXTURE_LIMITATIONS:
        errors.append(
            f"static report {relative} {label}.limitations are incomplete"
        )
    return errors


def _professional_review_cost_fixture_envelope_errors(
    relative: str, fixture: object
) -> list[str]:
    label = "professional_review_cost_fixtures"
    expected_fields = {
        "schema_version",
        "status",
        "unchanged",
        "routing_neutral_isolated_material_binding_sensitivity",
        "representative_routing_adjacency_mutation",
        "review_contract_change",
        "thresholds",
        "limitations",
    }
    if not isinstance(fixture, dict) or set(fixture) != expected_fields:
        return [
            f"static report {relative} {label} fields do not match schema 1"
        ]
    errors: list[str] = []
    if fixture.get("schema_version") != 1:
        errors.append(
            f"static report {relative} {label}.schema_version must equal 1"
        )
    if fixture.get("status") not in {"pass", "formal-non-current"}:
        errors.append(
            f"static report {relative} {label}.status must be pass or "
            "formal-non-current"
        )
    _normalized, sensitivity_errors = _normalized_professional_review_cost_sensitivity(
        fixture.get("routing_neutral_isolated_material_binding_sensitivity")
    )
    errors.extend(
        f"static report {relative} {label} {error}"
        for error in sensitivity_errors
    )
    limitations = fixture.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        errors.append(
            f"static report {relative} {label}.limitations must be a non-empty list"
        )
    return errors


def _expert_axis_envelope_errors(
    relative: str,
    *,
    label: str,
    axis: object,
    expected_fields: set[str],
    expected_scope: str,
    expected_kind: str,
    allowed_statuses: set[str],
) -> list[str]:
    if not isinstance(axis, dict) or set(axis) != expected_fields:
        return [
            f"static report {relative} {label} fields do not match schema 10"
        ]
    errors: list[str] = []
    if axis.get("scope") != expected_scope:
        errors.append(f"static report {relative} {label}.scope is invalid")
    if axis.get("panel_kind") != expected_kind:
        errors.append(f"static report {relative} {label}.panel_kind is invalid")
    for field in (
        "decision_complete",
        "storage_current",
        "source_current",
        "accepted_for_formal",
    ):
        if type(axis.get(field)) is not bool:
            errors.append(
                f"static report {relative} {label}.{field} must be a boolean"
            )
    status = axis.get("attestation_status")
    if status not in allowed_statuses:
        errors.append(
            f"static report {relative} {label}.attestation_status is invalid"
        )
    if type(axis.get("attestation_schema_version")) is not int:
        errors.append(
            f"static report {relative} {label}.attestation_schema_version "
            "must be an integer"
        )
    if axis.get("accepted_for_formal") is True and not _expert_axis_current(axis):
        errors.append(
            f"static report {relative} {label}.accepted_for_formal contradicts "
            "its currentness booleans or attestation status"
        )
    return errors


def _expert_axis_current(axis: object) -> bool:
    return bool(
        isinstance(axis, dict)
        and axis.get("decision_complete") is True
        and axis.get("storage_current") is True
        and axis.get("source_current") is True
        and axis.get("accepted_for_formal") is True
        and axis.get("attestation_status") == "panel-majority-current"
    )


def _professional_fixed_attestation_lifecycle_valid(axis: object) -> bool:
    if not isinstance(axis, dict):
        return False
    lifecycle = axis.get("round_lifecycle")
    review_cost = axis.get("review_cost")
    return bool(
        isinstance(lifecycle, dict)
        and set(lifecycle)
        == {
            "status",
            "round_count",
            "chain_depth",
            "head_decision",
            "current_decision_is_head",
            "errors",
            "limitations",
        }
        and lifecycle.get("status") == "fixed-attestation-current"
        and lifecycle.get("round_count") == 1
        and isinstance(review_cost, dict)
        and lifecycle.get("chain_depth")
        == review_cost.get("plan_lineage_depth")
        and lifecycle.get("head_decision") is None
        and lifecycle.get("current_decision_is_head") is True
        and lifecycle.get("errors") == []
        and lifecycle.get("limitations")
        == [PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]]
    )


def _professional_completeness_formal_ready(axis: object) -> bool:
    return bool(
        isinstance(axis, dict)
        and axis.get("panel_kind") == PROFESSIONAL_COMPLETENESS_PANEL_KIND
        and axis.get("scope") == "professional-skill-packages"
        and axis.get("decision_complete") is True
        and axis.get("storage_current") is True
        and axis.get("source_current") is True
        and axis.get("accepted_for_formal") is True
        and axis.get("decision_method")
        == PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
        and axis.get("panel_size") == 3
        and _non_negative_int(axis.get("reviewer_pool_size"))
        and axis.get("attestation_schema_version") == 5
        and axis.get("panel_artifact_schema_version") == 3
        and axis.get("attestation_status") == "panel-majority-current"
        and axis.get("evidence_contract_satisfied") is True
        and _professional_v3_evidence_ready(axis)
        and axis.get("review_contract_current") is True
        and axis.get("review_plan_current") is True
        and axis.get("review_plan_fingerprint") is None
        and axis.get("current_review_plan_fingerprint") is None
        and axis.get("review_binding_current") is True
        and axis.get("provenance_current") is True
        and _professional_schema3_compact_authority_valid(axis)
        and axis.get("round_lifecycle_current") is True
        and _professional_fixed_attestation_lifecycle_valid(axis)
        and axis.get("review_cost_current") is True
        and _professional_review_cost_ready(axis)
        and axis.get("required_target_count") == PROFESSIONAL_PACKAGE_COUNT
        and _non_negative_int(axis.get("fresh_target_count"))
        and _non_negative_int(axis.get("carried_forward_target_count"))
        and axis.get("fresh_target_count")
        + axis.get("carried_forward_target_count")
        == PROFESSIONAL_PACKAGE_COUNT
        and axis.get("applied_target_count") == PROFESSIONAL_PACKAGE_COUNT
        and axis.get("accepted_current_count") == PROFESSIONAL_PACKAGE_COUNT
        and axis.get("correction_count") == 0
        and axis.get("unresolved_professional_disagreement_count") == 0
    )


def _professional_compact_provenance_valid(
    item: dict, *, panel_review_id: object
) -> bool:
    provenance = item.get("provenance")
    if (
        not isinstance(provenance, dict)
        or set(provenance) != {"mode", "origin"}
        or provenance.get("mode") not in {"fresh", "carried"}
    ):
        return False
    origin = provenance.get("origin")
    return bool(
        isinstance(origin, dict)
        and set(origin) == PROFESSIONAL_COMPACT_ORIGIN_FIELDS
        and isinstance(origin.get("origin_review_id"), str)
        and isinstance(panel_review_id, str)
        and PROFESSIONAL_IDENTIFIER_PATTERN.fullmatch(
            origin["origin_review_id"]
        )
        is not None
        and PROFESSIONAL_IDENTIFIER_PATTERN.fullmatch(panel_review_id)
        is not None
        and isinstance(origin.get("origin_commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", origin["origin_commit"])
        is not None
        and isinstance(origin.get("origin_verdict_digest"), str)
        and _is_sha256(origin["origin_verdict_digest"])
        and origin["origin_verdict_digest"]
        == item.get("target_decision_fingerprint")
        and (
            (
                provenance["mode"] == "fresh"
                and origin["origin_review_id"] == panel_review_id
            )
            or (
                provenance["mode"] == "carried"
                and origin["origin_review_id"] != panel_review_id
                and item.get("disposition")
                == "accepted-current-professional-completeness"
            )
        )
    )


def _professional_schema3_disposition_evidence_valid(
    item: dict, *, panel_review_id: object
) -> bool:
    metrics = item.get("evidence_metrics")
    if (
        not isinstance(metrics, dict)
        or set(metrics) != {
            "target_vote_count",
            "required_adjacency_candidate_count",
            "criterion_result_count",
            "criterion_anchor_binding_count",
            "criterion_assertion_count",
            "evidence_anchor_count",
            "examined_failure_mode_count",
            "examined_omission_candidate_count",
            "examined_adjacency_count",
            "examined_required_adjacency_count",
            "reviewer_added_adjacency_count",
            "proof_limit_count",
            "qualification_claim_count",
        }
        or any(not _non_negative_int(value) for value in metrics.values())
        or metrics["target_vote_count"] != 3
        or metrics["criterion_result_count"] != 30
        or metrics["criterion_assertion_count"] < 30
        or metrics["criterion_anchor_binding_count"]
        < metrics["criterion_assertion_count"]
        or metrics["evidence_anchor_count"] < 6
        or metrics["examined_failure_mode_count"] < 6
        or metrics["examined_omission_candidate_count"] < 6
        or metrics["examined_required_adjacency_count"]
        != 3 * metrics["required_adjacency_candidate_count"]
        or metrics["examined_adjacency_count"]
        != metrics["examined_required_adjacency_count"]
        + metrics["reviewer_added_adjacency_count"]
        or metrics["proof_limit_count"] < 3
        or metrics["qualification_claim_count"] < 3
    ):
        return False
    dependency = item.get("review_dependencies")
    if not isinstance(dependency, dict) or set(dependency) != {
        "skill_id",
        "final_disposition",
        "evidence_complete",
        "prior_target_vote_count",
        "required_candidate_ids",
        "reviewer_added_candidate_ids_union",
        "dependency_candidate_ids",
    }:
        return False
    required_ids = dependency.get("required_candidate_ids")
    added_ids = dependency.get("reviewer_added_candidate_ids_union")
    if (
        dependency.get("skill_id") != item.get("skill_id")
        or dependency.get("final_disposition") != item.get("disposition")
        or dependency.get("evidence_complete") is not True
        or dependency.get("prior_target_vote_count") != 3
        or not isinstance(required_ids, list)
        or not all(
            isinstance(candidate_id, str) and candidate_id.strip()
            for candidate_id in required_ids
        )
        or required_ids != sorted(set(required_ids))
        or not isinstance(added_ids, list)
        or not all(
            isinstance(candidate_id, str) and candidate_id.strip()
            for candidate_id in added_ids
        )
        or added_ids != sorted(set(added_ids))
        or dependency.get("dependency_candidate_ids")
        != sorted(set(required_ids) | set(added_ids))
        or metrics["required_adjacency_candidate_count"] != len(required_ids)
    ):
        return False
    return _professional_compact_provenance_valid(
        item, panel_review_id=panel_review_id
    )


def _professional_schema3_compact_authority_valid(axis: object) -> bool:
    if not isinstance(axis, dict):
        return False
    dispositions = axis.get("professional_dispositions")
    panel_review_id = axis.get("panel_review_id")
    fresh = axis.get("fresh_target_count")
    carried = axis.get("carried_forward_target_count")
    if (
        not isinstance(dispositions, list)
        or len(dispositions) != PROFESSIONAL_PACKAGE_COUNT
        or not _non_negative_int(fresh)
        or not _non_negative_int(carried)
        or fresh + carried != PROFESSIONAL_PACKAGE_COUNT
        or not all(
            isinstance(item, dict)
            and set(item) == PROFESSIONAL_SCHEMA3_DISPOSITION_FIELDS
            and isinstance(item.get("package_material_binding"), str)
            and _is_sha256(item["package_material_binding"])
            and isinstance(item.get("review_unit_binding"), str)
            and _is_sha256(item["review_unit_binding"])
            and isinstance(item.get("target_decision_fingerprint"), str)
            and _is_sha256(item["target_decision_fingerprint"])
            and _professional_schema3_disposition_evidence_valid(
                item, panel_review_id=panel_review_id
            )
            for item in dispositions
        )
    ):
        return False
    fresh_rows = [
        item for item in dispositions if item["provenance"]["mode"] == "fresh"
    ]
    carried_rows = [
        item for item in dispositions if item["provenance"]["mode"] == "carried"
    ]
    fresh_origin_commits = {
        item["provenance"]["origin"]["origin_commit"] for item in fresh_rows
    }
    review_cost = axis.get("review_cost")
    return bool(
        len(fresh_rows) == fresh
        and len(carried_rows) == carried
        and len(fresh_origin_commits) == (1 if fresh_rows else 0)
        and isinstance(review_cost, dict)
        and review_cost.get("maximum_origin_depth")
        == (1 if carried_rows else 0)
    )


def _readability_axis_errors(relative: str, axis: object) -> list[str]:
    label = "content_readiness.expert.readability"
    shape_errors: list[str] = []
    if isinstance(axis, dict) and set(axis) != READABILITY_REVIEW_FIELDS:
        shape_errors.append(
            f"static report {relative} {label} fields do not match schema 7"
        )
    fingerprint_fields = READABILITY_FINGERPRINT_FIELDS
    if (
        isinstance(axis, dict)
        and axis.get("decision_complete") is True
        and axis.get("panel_artifact_schema_version") == 1
    ):
        fingerprint_fields = LEGACY_READABILITY_FINGERPRINT_FIELDS
    errors = _axis_common_errors(
        relative,
        label=label,
        axis=axis,
        expected_scope="ai-readability-and-density",
        expected_kind=READABILITY_PANEL_KIND,
        fingerprint_fields=fingerprint_fields,
        current_fingerprint_fields=READABILITY_FINGERPRINT_FIELDS,
        allowed_statuses=READABILITY_STATUSES,
    )
    errors[:0] = shape_errors
    if not isinstance(axis, dict):
        return errors
    density = axis.get("density_dispositions")
    if not isinstance(density, list) or not all(
        isinstance(item, dict)
        and set(item) == {"path", "classification", "disposition", "rationale"}
        and isinstance(item.get("path"), str)
        and bool(item["path"].strip())
        and item.get("classification") in {"REVIEW_DENSITY", "TIGHTEN_BODY"}
        and item.get("disposition")
        in {"accepted-current-density", "tracked-tightening"}
        and isinstance(item.get("rationale"), str)
        and bool(item["rationale"].strip())
        for item in density
    ):
        errors.append(f"static report {relative} {label}.density_dispositions are malformed")
        density = []
    elif [item["path"] for item in density] != sorted(
        {item["path"] for item in density}
    ):
        errors.append(
            f"static report {relative} {label}.density_dispositions must be sorted and unique"
        )
    readability = axis.get("readability_dispositions")
    if not isinstance(readability, list) or not all(
        isinstance(item, dict)
        and set(item) == {"document_id", "highest_band", "disposition", "rationale"}
        and isinstance(item.get("document_id"), str)
        and bool(item["document_id"].strip())
        and item.get("highest_band") in {"review-as-complex", "tighten"}
        and item.get("disposition")
        in {"accepted-current-readability", "tracked-tightening"}
        and isinstance(item.get("rationale"), str)
        and bool(item["rationale"].strip())
        for item in readability
    ):
        errors.append(
            f"static report {relative} {label}.readability_dispositions are malformed"
        )
        readability = []
    elif [item["document_id"] for item in readability] != sorted(
        {item["document_id"] for item in readability}
    ):
        errors.append(
            f"static report {relative} {label}.readability_dispositions must be sorted and unique"
        )
    actionability = axis.get("actionability_dispositions")
    actionability_decisions = {
        "accepted-current-actionability",
        "detector-false-positive",
        "rewrite-required",
    }
    if not isinstance(actionability, list) or not all(
        isinstance(item, dict)
        and set(item)
        == {
            "target_id",
            "skill_id",
            "path",
            "front_loaded_action_score",
            "disposition",
            "reason_codes",
            "rationale",
            "evidence",
        }
        and all(
            isinstance(item.get(field), str) and bool(item[field].strip())
            for field in ("target_id", "skill_id", "path", "rationale")
        )
        and _non_negative_int(item.get("front_loaded_action_score"))
        and item.get("disposition") in actionability_decisions
        and isinstance(item.get("reason_codes"), list)
        and bool(item["reason_codes"])
        and item["reason_codes"] == sorted(set(item["reason_codes"]))
        and isinstance(item.get("evidence"), list)
        and bool(item["evidence"])
        and all(
            isinstance(evidence, dict)
            and set(evidence) == {"line", "source_line", "claim"}
            and type(evidence.get("line")) is int
            and evidence["line"] > 0
            and isinstance(evidence.get("source_line"), str)
            and isinstance(evidence.get("claim"), str)
            and bool(evidence["claim"].strip())
            for evidence in item["evidence"]
        )
        for item in actionability
    ):
        errors.append(
            f"static report {relative} {label}.actionability_dispositions are malformed"
        )
        actionability = []
    elif [item["target_id"] for item in actionability] != sorted(
        {item["target_id"] for item in actionability}
    ):
        errors.append(
            f"static report {relative} {label}.actionability_dispositions "
            "must be sorted and unique"
        )
    for field in (
        "required_density_disposition_count",
        "applied_density_disposition_count",
        "required_readability_disposition_count",
        "applied_readability_disposition_count",
        "required_actionability_disposition_count",
        "applied_actionability_disposition_count",
        "blocker_count",
    ):
        if not _non_negative_int(axis.get(field)):
            errors.append(
                f"static report {relative} {label}.{field} must be a non-negative integer"
            )
    tracked = axis.get("tracked_tightening_count")
    rewrite_required = axis.get("rewrite_required_count")
    accepted_actionability = axis.get("accepted_current_actionability_count")
    false_positive_actionability = axis.get("detector_false_positive_count")
    decision_complete = axis.get("decision_complete") is True
    if decision_complete:
        if not _non_negative_int(tracked):
            errors.append(
                f"static report {relative} {label}.tracked_tightening_count "
                "must be a non-negative integer for a completed decision"
            )
        else:
            actual_tracked = sum(
                item.get("disposition") == "tracked-tightening"
                for item in (*density, *readability)
            )
            if tracked != actual_tracked:
                errors.append(
                    f"static report {relative} {label}.tracked_tightening_count "
                    "does not match dispositions"
                )
        for field, value in (
            ("accepted_current_actionability_count", accepted_actionability),
            ("detector_false_positive_count", false_positive_actionability),
            ("rewrite_required_count", rewrite_required),
        ):
            if not _non_negative_int(value):
                errors.append(
                    f"static report {relative} {label}.{field} must be a "
                    "non-negative integer for a completed decision"
                )
        if all(
            _non_negative_int(value)
            for value in (
                accepted_actionability,
                false_positive_actionability,
                rewrite_required,
            )
        ):
            expected_counts = {
                "accepted-current-actionability": accepted_actionability,
                "detector-false-positive": false_positive_actionability,
                "rewrite-required": rewrite_required,
            }
            actual_counts = {
                disposition: sum(
                    item.get("disposition") == disposition
                    for item in actionability
                )
                for disposition in actionability_decisions
            }
            if actual_counts != expected_counts:
                errors.append(
                    f"static report {relative} {label} actionability counts "
                    "do not match dispositions"
                )
    elif tracked is not None:
        errors.append(
            f"static report {relative} {label}.tracked_tightening_count must be null "
            "without evidence"
        )
    if not decision_complete and any(
        value is not None
        for value in (
            accepted_actionability,
            false_positive_actionability,
            rewrite_required,
        )
    ):
        errors.append(
            f"static report {relative} {label} actionability counts must be null "
            "without evidence"
        )
    applied_density = axis.get("applied_density_disposition_count")
    applied_readability = axis.get("applied_readability_disposition_count")
    applied_actionability = axis.get("applied_actionability_disposition_count")
    if applied_density != len(density):
        errors.append(
            f"static report {relative} {label} applied density count does not match dispositions"
        )
    if applied_readability != len(readability):
        errors.append(
            f"static report {relative} {label} applied readability count does not match dispositions"
        )
    if applied_actionability != len(actionability):
        errors.append(
            f"static report {relative} {label} applied actionability count does "
            "not match dispositions"
        )
    if not decision_complete and (
        density
        or readability
        or actionability
        or applied_density
        or applied_readability
        or applied_actionability
    ):
        errors.append(
            f"static report {relative} {label} missing evidence carries dispositions"
        )
    if axis.get("source_current") is True and axis.get(
        "attestation_status"
    ) != "panel-majority-incomplete-coverage":
        if axis.get("required_density_disposition_count") != applied_density or axis.get(
            "required_readability_disposition_count"
        ) != applied_readability or axis.get(
            "required_actionability_disposition_count"
        ) != applied_actionability:
            errors.append(
                f"static report {relative} {label} current panel coverage is incomplete"
            )
    if axis.get("accepted_for_formal") is True and not _readability_formal_ready(axis):
        errors.append(
            f"static report {relative} {label}.accepted_for_formal disagrees with "
            "the zero-tightening/actionability formal contract"
        )
    status = axis.get("attestation_status")
    if status == "panel-majority-current" and not _readability_formal_ready(axis):
        errors.append(
            f"static report {relative} {label} current status does not satisfy "
            "the zero-tightening/actionability formal contract"
        )
    if status == "panel-majority-tracked-tightening" and (
        not _non_negative_int(tracked)
        or tracked == 0
        or axis.get("decision_complete") is not True
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
    ):
        errors.append(
            f"static report {relative} {label} tracked-tightening status requires findings"
        )
    if status == "panel-majority-actionability-rewrite-required" and (
        not _non_negative_int(rewrite_required)
        or rewrite_required == 0
        or axis.get("decision_complete") is not True
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
        or tracked != 0
    ):
        errors.append(
            f"static report {relative} {label} actionability rewrite status "
            "requires rewrite findings"
        )
    if status == "panel-majority-detector-update-required" and (
        not _non_negative_int(false_positive_actionability)
        or false_positive_actionability == 0
        or axis.get("decision_complete") is not True
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
        or tracked != 0
        or rewrite_required != 0
    ):
        errors.append(
            f"static report {relative} {label} detector-update status requires "
            "unresolved detector false positives"
        )
    if status == "panel-majority-blocked" and (
        axis.get("blocker_count") == 0
        or axis.get("decision_complete") is not True
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
        or tracked != 0
    ):
        errors.append(
            f"static report {relative} {label} blocked status requires blockers"
        )
    return errors


def _professional_completeness_axis_errors(relative: str, axis: object) -> list[str]:
    label = "content_readiness.expert.professional_completeness"
    shape_errors: list[str] = []
    if isinstance(axis, dict) and set(axis) != PROFESSIONAL_COMPLETENESS_REVIEW_FIELDS:
        shape_errors.append(
            f"static report {relative} {label} fields do not match schema 10"
        )
    artifact_schema = (
        axis.get("panel_artifact_schema_version")
        if isinstance(axis, dict)
        else None
    )
    errors = _axis_common_errors(
        relative,
        label=label,
        axis=axis,
        expected_scope="professional-skill-packages",
        expected_kind=PROFESSIONAL_COMPLETENESS_PANEL_KIND,
        fingerprint_fields=(
            PROFESSIONAL_COMPLETENESS_FINGERPRINT_FIELDS
            if artifact_schema in {1, 2}
            else PROFESSIONAL_COMPLETENESS_V3_FINGERPRINT_FIELDS
        ),
        current_fingerprint_fields=(
            PROFESSIONAL_COMPLETENESS_V3_FINGERPRINT_FIELDS
        ),
        allowed_statuses=PROFESSIONAL_COMPLETENESS_STATUSES,
        allowed_decision_methods={
            EXPERT_DECISION_METHOD,
            PROFESSIONAL_COMPLETENESS_DECISION_METHOD,
            PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD,
        },
    )
    errors[:0] = shape_errors
    if not isinstance(axis, dict):
        return errors
    decision_complete = axis.get("decision_complete") is True
    if decision_complete and artifact_schema not in {1, 2, 3}:
        errors.append(
            f"static report {relative} {label}.panel_artifact_schema_version "
            "must identify a supported decision schema"
        )
    if not decision_complete and artifact_schema is not None:
        errors.append(
            f"static report {relative} {label} missing evidence carries an artifact schema"
        )
    if artifact_schema == 1 and axis.get("decision_method") != EXPERT_DECISION_METHOD:
        errors.append(
            f"static report {relative} {label} schema-1 decision method is invalid"
        )
    if (
        artifact_schema == 2
        and axis.get("decision_method")
        != PROFESSIONAL_COMPLETENESS_DECISION_METHOD
    ):
        errors.append(
            f"static report {relative} {label} schema-2 decision method is invalid"
        )
    if (
        artifact_schema == 3
        and axis.get("decision_method")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
    ):
        errors.append(
            f"static report {relative} {label} schema-3 decision method is invalid"
        )
    if artifact_schema in {1, 2} and (
        axis.get("attestation_status") != "panel-legacy-nonformal"
        or axis.get("accepted_for_formal") is not False
        or axis.get("source_current") is not False
    ):
        errors.append(
            f"static report {relative} {label} schema-1/schema-2 evidence must "
            "remain panel-legacy-nonformal"
        )
    reviewer_pool_size = axis.get("reviewer_pool_size")
    if not _non_negative_int(reviewer_pool_size):
        errors.append(
            f"static report {relative} {label}.reviewer_pool_size must be non-negative"
        )
    elif artifact_schema == 2 and reviewer_pool_size < 3:
        errors.append(
            f"static report {relative} {label}.reviewer_pool_size must be at least three"
        )
    if artifact_schema == 2 and not _professional_v2_evidence_ready(axis):
        errors.append(
            f"static report {relative} {label} schema-2 qualification or evidence "
            "summary is insufficient"
        )
    if artifact_schema == 3 and not _professional_v3_evidence_ready(axis):
        errors.append(
            f"static report {relative} {label} schema-3 effective qualification "
            "or evidence summary is insufficient"
        )
    expected_evidence_contract = (
        _professional_v3_evidence_ready(axis)
        if artifact_schema == 3
        else _professional_v2_evidence_ready(axis)
    )
    if axis.get("evidence_contract_satisfied") is not expected_evidence_contract:
        errors.append(
            f"static report {relative} {label}.evidence_contract_satisfied "
            "disagrees with its artifact-schema summaries"
        )
    if artifact_schema not in {2, 3} and (
        axis.get("qualification_summary") is not None
        or axis.get("evidence_summary") is not None
    ):
        errors.append(
            f"static report {relative} {label} legacy or missing evidence carries "
            "schema-2/schema-3 summaries"
        )
    lifecycle = axis.get("round_lifecycle")
    fixed_attestation = _professional_fixed_attestation_lifecycle_valid(axis)
    dispositions = axis.get("professional_dispositions")
    if not isinstance(dispositions, list) or not all(
        isinstance(item, dict)
        and set(item)
        == (
            {
                *PROFESSIONAL_SCHEMA3_DISPOSITION_FIELDS,
            }
            if artifact_schema == 3
            else {
                "skill_id",
                "package_fingerprint",
                "review_binding_fingerprint",
                "disposition",
                "majority_disposition",
                "domain_critical_defects",
                "ordinary_criterion_disposition",
                "ordinary_criterion_defects",
                "reason_codes",
                "rationales",
                "review_dependencies",
                "evidence_metrics",
                "provenance",
                "target_decision_fingerprint",
            }
        )
        and isinstance(item.get("skill_id"), str)
        and bool(item["skill_id"].strip())
        and (
            (
                artifact_schema == 3
                and isinstance(item.get("package_material_binding"), str)
                and _is_sha256(item["package_material_binding"])
                and isinstance(item.get("review_unit_binding"), str)
                and _is_sha256(item["review_unit_binding"])
            )
            or (
                artifact_schema in {1, 2}
                and isinstance(item.get("package_fingerprint"), str)
                and _is_sha256(item["package_fingerprint"])
            )
        )
        and item.get("disposition")
        in {
            "accepted-current-professional-completeness",
            "requires-professional-correction",
            PROFESSIONAL_UNRESOLVED_DISPOSITION,
        }
        and item.get("majority_disposition")
        in {
            "accepted-current-professional-completeness",
            "requires-professional-correction",
        }
        and item.get("ordinary_criterion_disposition")
        in {
            "accepted-current-professional-completeness",
            "requires-professional-correction",
        }
        and isinstance(item.get("ordinary_criterion_defects"), list)
        and item["ordinary_criterion_defects"]
        == sorted(set(item["ordinary_criterion_defects"]))
        and set(item["ordinary_criterion_defects"])
        <= PROFESSIONAL_ORDINARY_CRITERIA
        and isinstance(item.get("domain_critical_defects"), list)
        and all(
            isinstance(defect, dict)
            and set(defect) == {"criterion", "voter_id"}
            and defect.get("criterion") in PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
            and isinstance(defect.get("voter_id"), str)
            and bool(defect["voter_id"].strip())
            for defect in item["domain_critical_defects"]
        )
        and item["domain_critical_defects"]
        == sorted(
            item["domain_critical_defects"],
            key=lambda defect: (defect["criterion"], defect["voter_id"]),
        )
        and len(
            {
                (defect["criterion"], defect["voter_id"])
                for defect in item["domain_critical_defects"]
            }
        )
        == len(item["domain_critical_defects"])
        and (
            item["disposition"] == PROFESSIONAL_UNRESOLVED_DISPOSITION
        )
        == bool(item["domain_critical_defects"])
        and (
            (
                artifact_schema in {2, 3}
                and (
                    item["ordinary_criterion_disposition"]
                    == "requires-professional-correction"
                )
                == bool(item["ordinary_criterion_defects"])
                and (
                    bool(item["domain_critical_defects"])
                    or item["disposition"]
                    == item["ordinary_criterion_disposition"]
                )
            )
            or (
                artifact_schema == 1
                and not item["domain_critical_defects"]
                and not item["ordinary_criterion_defects"]
                and item["ordinary_criterion_disposition"]
                == item["majority_disposition"]
                and item["disposition"] == item["majority_disposition"]
            )
        )
        and isinstance(item.get("reason_codes"), list)
        and bool(item["reason_codes"])
        and all(isinstance(code, str) and code.strip() for code in item["reason_codes"])
        and isinstance(item.get("rationales"), list)
        and len(item["rationales"]) >= 2
        and all(
            isinstance(row, dict)
            and set(row) == {"voter_id", "reason_code", "rationale"}
            and all(isinstance(row.get(field), str) and row[field].strip() for field in row)
            for row in item["rationales"]
        )
        and (
            (
                artifact_schema == 3
                and _professional_schema3_disposition_evidence_valid(
                    item, panel_review_id=axis.get("panel_review_id")
                )
                and isinstance(item.get("target_decision_fingerprint"), str)
                and _is_sha256(item["target_decision_fingerprint"])
            )
            or (
                artifact_schema in {1, 2}
                and item.get("review_binding_fingerprint") is None
                and item.get("review_dependencies") is None
                and item.get("evidence_metrics") is None
                and item.get("provenance") is None
                and item.get("target_decision_fingerprint") is None
            )
        )
        for item in dispositions
    ):
        errors.append(
            f"static report {relative} {label}.professional_dispositions are malformed"
        )
        dispositions = []
    elif [item["skill_id"] for item in dispositions] != sorted(
        {item["skill_id"] for item in dispositions}
    ):
        errors.append(
            f"static report {relative} {label}.professional_dispositions must be sorted and unique"
        )
    if artifact_schema == 3 and dispositions:
        if not _professional_schema3_compact_authority_valid(axis):
            errors.append(
                f"static report {relative} {label} compact origin authority "
                "is malformed or unstable"
            )
        fresh_rows = [
            item
            for item in dispositions
            if item["provenance"]["mode"] == "fresh"
        ]
        carried_rows = [
            item
            for item in dispositions
            if item["provenance"]["mode"] == "carried"
        ]
        if len(fresh_rows) != axis.get("fresh_target_count") or len(
            carried_rows
        ) != axis.get("carried_forward_target_count"):
            errors.append(
                f"static report {relative} {label} disposition provenance "
                "partition disagrees with fresh/carried counts"
            )
        metric_fields = set(next(iter(dispositions))["evidence_metrics"])
        effective_metrics = {
            field: sum(item["evidence_metrics"][field] for item in dispositions)
            for field in metric_fields
        }
        if effective_metrics != axis.get("evidence_summary"):
            errors.append(
                f"static report {relative} {label}.evidence_summary does not "
                "equal the disposition evidence-metric sum"
            )
        review_cost = axis.get("review_cost")
        expected_maximum_origin_depth = 1 if carried_rows else 0
        if isinstance(review_cost, dict) and review_cost.get(
            "maximum_origin_depth"
        ) != expected_maximum_origin_depth:
            errors.append(
                f"static report {relative} {label} maximum origin depth is stale"
            )
    required = axis.get("required_target_count")
    fresh = axis.get("fresh_target_count")
    carried = axis.get("carried_forward_target_count")
    applied = axis.get("applied_target_count")
    accepted = axis.get("accepted_current_count")
    corrections = axis.get("correction_count")
    unresolved = axis.get("unresolved_professional_disagreement_count")
    if not _non_negative_int(required):
        errors.append(
            f"static report {relative} {label}.required_target_count must be non-negative"
        )
    if not _non_negative_int(applied):
        errors.append(
            f"static report {relative} {label}.applied_target_count must be non-negative"
        )
    if not _non_negative_int(fresh) or not _non_negative_int(carried):
        errors.append(
            f"static report {relative} {label} fresh/carried target counts must "
            "be non-negative"
        )
    elif artifact_schema == 3:
        if fresh + carried != PROFESSIONAL_PACKAGE_COUNT:
            errors.append(
                f"static report {relative} {label} schema-3 fresh/carried partition "
                "must contain 189 targets"
            )
        if (fresh == 0 and reviewer_pool_size != 0) or (
            fresh > 0 and reviewer_pool_size < 3
        ):
            errors.append(
                f"static report {relative} {label} schema-3 reviewer pool does not "
                "match the fresh target partition"
            )
    elif fresh != 0 or carried != 0:
        errors.append(
            f"static report {relative} {label} legacy or missing evidence cannot "
            "claim schema-3 carry partition counts"
        )
    if decision_complete:
        for field, value in (
            ("accepted_current_count", accepted),
            ("correction_count", corrections),
            ("unresolved_professional_disagreement_count", unresolved),
        ):
            if not _non_negative_int(value):
                errors.append(
                    f"static report {relative} {label}.{field} must be non-negative "
                    "for a completed decision"
                )
        if (
            _non_negative_int(accepted)
            and _non_negative_int(corrections)
            and _non_negative_int(unresolved)
        ):
            if accepted + corrections + unresolved != applied:
                errors.append(
                    f"static report {relative} {label} disposition counts do not sum to applied targets"
                )
            actual_corrections = sum(
                item.get("disposition") == "requires-professional-correction"
                for item in dispositions
            )
            if corrections != actual_corrections:
                errors.append(
                    f"static report {relative} {label}.correction_count does not match dispositions"
                )
            actual_unresolved = sum(
                item.get("disposition") == PROFESSIONAL_UNRESOLVED_DISPOSITION
                for item in dispositions
            )
            if unresolved != actual_unresolved:
                errors.append(
                    f"static report {relative} {label}.unresolved_professional_disagreement_count does not match dispositions"
                )
    elif accepted is not None or corrections is not None or unresolved is not None:
        errors.append(
            f"static report {relative} {label} missing evidence carries decision counts"
        )
    if applied != len(dispositions):
        errors.append(
            f"static report {relative} {label}.applied_target_count does not match dispositions"
        )
    if not decision_complete and (dispositions or applied):
        errors.append(
            f"static report {relative} {label} missing evidence carries dispositions"
        )

    current_fingerprints = axis.get("current_source_fingerprints")
    actual_contract = axis.get("review_contract_fingerprint")
    current_contract = axis.get("current_review_contract_fingerprint")
    actual_plan = axis.get("review_plan_fingerprint")
    current_plan = axis.get("current_review_plan_fingerprint")
    current_flags = (
        "review_contract_current",
        "review_plan_current",
        "review_binding_current",
        "provenance_current",
        "round_lifecycle_current",
        "review_cost_current",
    )
    for field in current_flags:
        if type(axis.get(field)) is not bool:
            errors.append(
                f"static report {relative} {label}.{field} must be a boolean"
            )
    if not isinstance(current_contract, str) or not _is_sha256(current_contract):
        errors.append(
            f"static report {relative} {label}.current_review_contract_fingerprint "
            "must be lowercase sha256"
        )
    if artifact_schema == 3:
        if not isinstance(actual_contract, str) or not _is_sha256(actual_contract):
            errors.append(
                f"static report {relative} {label}.review_contract_fingerprint "
                "must be lowercase sha256 for schema 3"
            )
        if axis.get("review_contract_current") is not (
            actual_contract == current_contract
        ):
            errors.append(
                f"static report {relative} {label}.review_contract_current "
                "disagrees with fingerprints"
            )
        if actual_plan is not None or current_plan is not None:
            errors.append(
                f"static report {relative} {label} current schema 3 requires "
                "paired-null review plan fingerprints"
            )
        expected_plan_current = bool(
            fixed_attestation and actual_plan is None and current_plan is None
        )
        if axis.get("review_plan_current") is not expected_plan_current:
            errors.append(
                f"static report {relative} {label}.review_plan_current "
                "disagrees with fixed attestation plan identity"
            )

        expected_binding_current = bool(
            fixed_attestation
            and axis.get("source_current") is True
            and axis.get("storage_current") is True
            and axis.get("review_contract_current") is True
            and len(dispositions) == PROFESSIONAL_PACKAGE_COUNT
            and all(
                isinstance(item.get("package_material_binding"), str)
                and _is_sha256(item["package_material_binding"])
                and isinstance(item.get("review_unit_binding"), str)
                and _is_sha256(item["review_unit_binding"])
                for item in dispositions
            )
        )
        if axis.get("review_binding_current") is not expected_binding_current:
            errors.append(
                f"static report {relative} {label}.review_binding_current "
                "disagrees with compact material and review-unit bindings"
            )
        expected_provenance_current = bool(
            expected_binding_current
            and _professional_schema3_compact_authority_valid(axis)
            and sum(
                item["provenance"]["mode"] == "fresh"
                for item in dispositions
            )
            == fresh
            and sum(
                item["provenance"]["mode"] == "carried"
                for item in dispositions
            )
            == carried
        )
        if axis.get("provenance_current") is not expected_provenance_current:
            errors.append(
                f"static report {relative} {label}.provenance_current "
                "disagrees with compact origins and partition"
            )
    elif (
        actual_contract is not None
        or actual_plan is not None
        or current_plan is not None
        or any(axis.get(field) is not False for field in current_flags)
        or axis.get("review_cost") is not None
    ):
        errors.append(
            f"static report {relative} {label} legacy or missing evidence carries "
            "schema-3 currentness or review-cost claims"
        )

    lifecycle_fields = {
        "status",
        "round_count",
        "chain_depth",
        "head_decision",
        "current_decision_is_head",
        "errors",
        "limitations",
    }
    if not isinstance(lifecycle, dict) or set(lifecycle) != lifecycle_fields:
        errors.append(
            f"static report {relative} {label}.round_lifecycle fields are malformed"
        )
    else:
        historical_lifecycle_statuses = {
            "no-schema3-rounds",
            "no-schema3-current-decision",
            "schema3-head-current",
            "schema3-head-not-selected",
            "schema3-round-lifecycle-invalid",
        }
        lifecycle_statuses = {
            "fixed-attestation-current",
        } if artifact_schema == 3 else historical_lifecycle_statuses | {
            "fixed-attestation-current"
        }
        lifecycle_shape_valid = not (
            lifecycle.get("status") not in lifecycle_statuses
            or not _non_negative_int(lifecycle.get("round_count"))
            or not _non_negative_int(lifecycle.get("chain_depth"))
            or (
                lifecycle.get("head_decision") is not None
                and (
                    not isinstance(lifecycle.get("head_decision"), str)
                    or not lifecycle["head_decision"].strip()
                )
            )
            or type(lifecycle.get("current_decision_is_head")) is not bool
            or not isinstance(lifecycle.get("errors"), list)
            or not all(
                isinstance(error, str) and error.strip()
                for error in lifecycle.get("errors", [])
            )
            or lifecycle.get("limitations")
            != [PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]]
        )
        fixed_lifecycle_valid = bool(
            lifecycle_shape_valid
            and _professional_fixed_attestation_lifecycle_valid(axis)
        )
        if not lifecycle_shape_valid or (
            artifact_schema == 3 and not fixed_lifecycle_valid
        ) or (
            artifact_schema != 3
            and lifecycle.get("status") == "fixed-attestation-current"
            and not fixed_lifecycle_valid
        ):
            errors.append(
                f"static report {relative} {label}.round_lifecycle is invalid"
            )
        expected_lifecycle_current = bool(
            artifact_schema == 3 and fixed_lifecycle_valid
        )
        if axis.get("round_lifecycle_current") is not expected_lifecycle_current:
            errors.append(
                f"static report {relative} {label}.round_lifecycle_current "
                "disagrees with lifecycle topology"
            )

    cost_ready = _professional_review_cost_ready(axis)
    expected_cost_current = bool(
        artifact_schema == 3
        and cost_ready
        and axis.get("source_current") is True
        and axis.get("storage_current") is True
        and axis.get("review_contract_current") is True
        and axis.get("review_plan_current") is True
        and axis.get("review_binding_current") is True
        and axis.get("provenance_current") is True
        and axis.get("round_lifecycle_current") is True
    )
    if axis.get("review_cost_current") is not expected_cost_current:
        errors.append(
            f"static report {relative} {label}.review_cost_current disagrees "
            "with raw cost, lineage, currentness, or storage"
        )
    if artifact_schema == 3 and not isinstance(axis.get("review_cost"), dict):
        errors.append(
            f"static report {relative} {label}.review_cost must be present for schema 3"
        )
    if axis.get("source_current") is True and axis.get(
        "attestation_status"
    ) != "panel-majority-incomplete-coverage" and required != applied:
        errors.append(
            f"static report {relative} {label} current panel coverage is incomplete"
        )
    if axis.get("accepted_for_formal") is True and not _professional_completeness_formal_ready(
        axis
    ):
        errors.append(
            f"static report {relative} {label}.accepted_for_formal disagrees with "
            "the 189-package zero-correction formal contract"
        )
    status = axis.get("attestation_status")
    if status == "panel-majority-current" and not _professional_completeness_formal_ready(
        axis
    ):
        errors.append(
            f"static report {relative} {label} current status does not satisfy "
            "the 189-package zero-correction formal contract"
        )
    if status == "panel-domain-disagreement-unresolved" and (
        not _non_negative_int(unresolved)
        or unresolved == 0
        or axis.get("decision_complete") is not True
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
    ):
        errors.append(
            f"static report {relative} {label} unresolved status needs a domain-critical disagreement"
        )
    if status == "panel-majority-corrections-required" and (
        not _non_negative_int(corrections)
        or corrections == 0
        or axis.get("decision_complete") is not True
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
        or unresolved != 0
    ):
        errors.append(
            f"static report {relative} {label} corrections-required status needs corrections"
        )
    if status == "panel-majority-evidence-insufficient" and (
        not decision_complete
        or axis.get("source_current") is not True
        or axis.get("storage_current") is not True
        or axis.get("accepted_for_formal") is not False
        or corrections != 0
        or unresolved != 0
        or expected_evidence_contract
    ):
        errors.append(
            f"static report {relative} {label} evidence-insufficient status is contradictory"
        )
    if status == "panel-majority-invalid-lineage" and (
        artifact_schema != 3
        or not decision_complete
        or axis.get("source_current") is not True
        or axis.get("accepted_for_formal") is not False
        or (
            axis.get("provenance_current") is True
            and axis.get("round_lifecycle_current") is True
        )
    ):
        errors.append(
            f"static report {relative} {label} invalid-lineage status is contradictory"
        )
    if status == "panel-review-cost-policy-not-satisfied" and (
        artifact_schema != 3
        or not decision_complete
        or axis.get("source_current") is not True
        or axis.get("accepted_for_formal") is not False
        or axis.get("review_cost_current") is not False
    ):
        errors.append(
            f"static report {relative} {label} review-cost status is contradictory"
        )
    return errors


def _docs_errors(root: Path) -> list[str]:
    path = root / "scripts/validate-docs-consistency.py"
    spec = importlib.util.spec_from_file_location("hookless_docs_validator", path)
    if spec is None or spec.loader is None:
        return ["cannot load documentation validator"]
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return [f"docs: {error}" for error in module.validate_docs_consistency(root)]


def _content_readiness_errors(
    relative: str, report: dict, *, root: Path = ROOT
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_version") not in {
        LEGACY_PROFESSIONALISM_REPORT_SCHEMA_VERSION,
        PROFESSIONALISM_REPORT_SCHEMA_VERSION,
    }:
        errors.append(
            f"static report {relative} must use report schema_version 3 or 4"
        )
    reference_summary = report.get("reference_content_summary")
    root_summary = report.get("root_content_summary")
    readability_summary = report.get("ai_readability_summary")
    content_audit_summary = report.get("content_audit_summary")
    readiness = report.get("content_readiness")
    if not isinstance(reference_summary, dict):
        errors.append(f"static report {relative} must contain reference_content_summary")
    if not isinstance(root_summary, dict):
        errors.append(f"static report {relative} must contain root_content_summary")
    if not isinstance(content_audit_summary, dict):
        errors.append(f"static report {relative} must contain content_audit_summary")
    else:
        review_states = content_audit_summary.get("review_states")
        if (
            not isinstance(review_states, dict)
            or not set(review_states) <= SKILL_REVIEW_STATES
            or any(type(value) is not int or value < 0 for value in review_states.values())
        ):
            errors.append(
                f"static report {relative} content_audit_summary.review_states "
                "must be a closed non-negative count mapping"
            )
        review_reasons = content_audit_summary.get("review_reasons")
        if (
            not isinstance(review_reasons, dict)
            or set(review_reasons) != SKILL_REVIEW_REASONS
            or any(type(value) is not int or value < 0 for value in review_reasons.values())
        ):
            errors.append(
                f"static report {relative} content_audit_summary.review_reasons "
                "must be the complete closed non-negative count mapping"
            )
    if not isinstance(readiness, dict):
        errors.append(f"static report {relative} must contain content_readiness")
        return errors
    if readiness.get("schema_version") != 10:
        errors.append(f"static report {relative} content_readiness.schema_version must equal 10")
    expected_sections = {"schema_version", "reference", "root", "expert", "aggregate"}
    if set(readiness) != expected_sections:
        errors.append(
            f"static report {relative} content_readiness must contain exactly "
            "schema_version, reference, root, expert, and aggregate"
        )

    sections = {
        "reference": (readiness.get("reference"), REFERENCE_READINESS_FIELDS),
        "root": (readiness.get("root"), ROOT_READINESS_FIELDS),
        "expert": (readiness.get("expert"), EXPERT_READINESS_FIELDS),
        "aggregate": (readiness.get("aggregate"), AGGREGATE_READINESS_FIELDS),
    }
    for name, (value, fields) in sections.items():
        if not isinstance(value, dict):
            errors.append(
                f"static report {relative} content_readiness.{name} must be a mapping"
            )
            continue
        if set(value) != fields:
            errors.append(
                f"static report {relative} content_readiness.{name} fields do not "
                "match schema 10"
            )

    errors.extend(
        _professional_review_cost_fixture_envelope_errors(
            relative, report.get("professional_review_cost_fixtures")
        )
    )

    reference = readiness.get("reference")
    root = readiness.get("root")
    expert = readiness.get("expert")
    aggregate = readiness.get("aggregate")
    for label, value, fields in (
        (
            "reference_content_summary",
            reference_summary,
            ("structural_strict_ready", "semantic_triage_complete", "strict_ready"),
        ),
        (
            "root_content_summary",
            root_summary,
            ("structural_strict_ready", "semantic_triage_complete", "strict_ready"),
        ),
        (
            "content_readiness.reference",
            reference,
            ("structural_strict_ready", "semantic_triage_complete", "strict_ready"),
        ),
        (
            "content_readiness.root",
            root,
            ("structural_strict_ready", "semantic_triage_complete", "strict_ready"),
        ),
        (
            "content_readiness.aggregate",
            aggregate,
            tuple(sorted(AGGREGATE_READINESS_FIELDS)),
        ),
    ):
        if not isinstance(value, dict):
            continue
        for field in fields:
            if type(value.get(field)) is not bool:
                errors.append(
                    f"static report {relative} {label}.{field} must be a boolean"
                )

    if isinstance(reference_summary, dict) and isinstance(reference, dict):
        for field in ("readiness_scope", "source_fingerprint", "strict_ready_basis"):
            if not isinstance(reference_summary.get(field), str) or not reference_summary[
                field
            ].strip():
                errors.append(
                    f"static report {relative} reference_content_summary.{field} "
                    "must be a non-blank string"
                )
        for field in ("structural_strict_ready", "semantic_triage_complete", "strict_ready"):
            if reference_summary.get(field) != reference.get(field):
                errors.append(
                    f"static report {relative} Reference readiness mismatch for {field}"
                )
        if reference_summary.get("strict_ready_basis") != "reference-strict-v4":
            errors.append(
                f"static report {relative} must preserve reference-strict-v4 compatibility"
            )
        if reference.get("scope") != "reference-content":
            errors.append(
                f"static report {relative} content_readiness.reference scope is invalid"
            )
        if reference.get("strict_ready_basis") != "reference-strict-v4":
            errors.append(
                f"static report {relative} content_readiness.reference basis is invalid"
            )
        if reference.get("source_fingerprint") != reference_summary.get(
            "source_fingerprint"
        ):
            errors.append(
                f"static report {relative} Reference source fingerprint mismatch"
            )
    if isinstance(root_summary, dict) and isinstance(root, dict):
        for field in ("readiness_scope", "source_fingerprint", "strict_ready_basis"):
            if not isinstance(root_summary.get(field), str) or not root_summary[field].strip():
                errors.append(
                    f"static report {relative} root_content_summary.{field} must be "
                    "a non-blank string"
                )
        for field in ("structural_strict_ready", "semantic_triage_complete", "strict_ready"):
            if root_summary.get(field) != root.get(field):
                errors.append(f"static report {relative} Root readiness mismatch for {field}")
        if root_summary.get("strict_ready_basis") != "root-strict-v5":
            errors.append(f"static report {relative} must use root-strict-v5")
        if root.get("scope") != "agent-facing-root-content":
            errors.append(f"static report {relative} content_readiness.root scope is invalid")
        if root.get("strict_ready_basis") != "root-strict-v5":
            errors.append(f"static report {relative} content_readiness.root basis is invalid")
        if root.get("source_fingerprint") != root_summary.get("source_fingerprint"):
            errors.append(f"static report {relative} Root source fingerprint mismatch")
    readability_axis = expert.get("readability") if isinstance(expert, dict) else None
    completeness_axis = (
        expert.get("professional_completeness") if isinstance(expert, dict) else None
    )
    if isinstance(expert, dict):
        if type(expert.get("deprecated_expert_content_review_complete")) is not bool:
            errors.append(
                f"static report {relative} deprecated expert compatibility flag "
                "must be a boolean"
            )
        elif expert["deprecated_expert_content_review_complete"] is not False:
            errors.append(
                f"static report {relative} deprecated expert compatibility flag "
                "cannot satisfy formal release"
            )
    errors.extend(
        _expert_axis_envelope_errors(
            relative,
            label="content_readiness.expert.readability",
            axis=readability_axis,
            expected_fields=READABILITY_REVIEW_FIELDS,
            expected_scope="ai-readability-and-density",
            expected_kind=READABILITY_PANEL_KIND,
            allowed_statuses=READABILITY_STATUSES,
        )
    )
    errors.extend(
        _expert_axis_envelope_errors(
            relative,
            label="content_readiness.expert.professional_completeness",
            axis=completeness_axis,
            expected_fields=PROFESSIONAL_COMPLETENESS_REVIEW_FIELDS,
            expected_scope="professional-skill-packages",
            expected_kind=PROFESSIONAL_COMPLETENESS_PANEL_KIND,
            allowed_statuses=PROFESSIONAL_COMPLETENESS_STATUSES,
        )
    )
    errors.extend(_readability_axis_errors(relative, readability_axis))
    errors.extend(
        _professional_completeness_axis_errors(relative, completeness_axis)
    )
    if isinstance(completeness_axis, dict) and type(
        completeness_axis.get("review_cost_current")
    ) is not bool:
        errors.append(
            f"static report {relative} content_readiness.expert."
            "professional_completeness.review_cost_current must be a boolean"
        )
    if isinstance(readability_axis, dict) and isinstance(completeness_axis, dict):
        if readability_axis.get("attestation_config_fingerprint") != completeness_axis.get(
            "attestation_config_fingerprint"
        ):
            errors.append(
                f"static report {relative} expert axes disagree on the release-review config"
            )
    if (
        isinstance(reference, dict)
        and isinstance(root, dict)
        and isinstance(expert, dict)
        and isinstance(aggregate, dict)
    ):
        expected_aggregate = {
            "structural_strict_ready": (
                reference.get("structural_strict_ready") is True
                and root.get("structural_strict_ready") is True
            ),
            "semantic_triage_complete": (
                reference.get("semantic_triage_complete") is True
                and root.get("semantic_triage_complete") is True
            ),
            "readability_review_current": _readability_formal_ready(
                readability_axis
            ),
            "professional_completeness_review_current": (
                _professional_completeness_formal_ready(completeness_axis)
            ),
        }
        if aggregate != expected_aggregate:
            errors.append(
                f"static report {relative} content_readiness.aggregate does not "
                "match its scoped readiness axes"
            )

    status_field = "authoring_gate" if "authoring_gate" in report else "status"
    if report.get(status_field) == "current-contract-pass":
        for label, value in (("Reference", reference), ("Root", root)):
            if not isinstance(value, dict):
                continue
            for field in (
                "structural_strict_ready",
                "semantic_triage_complete",
                "strict_ready",
            ):
                if value.get(field) is not True:
                    errors.append(
                        f"static report {relative} cannot pass while {label} {field}=false"
                    )
    return errors


def _blocker_list_errors(
    relative: str,
    field: str,
    blockers: object,
) -> tuple[list[str], int]:
    errors: list[str] = []
    if not isinstance(blockers, list):
        errors.append(f"static report {relative} must contain a {field} list")
        return errors, 0
    error_blockers = 0
    required_fields = {"category", "target", "message", "severity"}
    for index, blocker in enumerate(blockers):
        label = f"static report {relative} {field}[{index}]"
        if not isinstance(blocker, dict) or set(blocker) != required_fields:
            errors.append(f"{label} fields do not match the Finding contract")
            continue
        for required_field in required_fields:
            if not isinstance(blocker.get(required_field), str) or not blocker[
                required_field
            ].strip():
                errors.append(
                    f"{label}.{required_field} must be a non-blank string"
                )
        if blocker.get("severity") == "error":
            error_blockers += 1
        else:
            errors.append(f"{label}.severity must equal error")
    return errors, error_blockers


def _status_blocker_errors(relative: str, report: dict) -> list[str]:
    errors: list[str] = []
    authoring_gate = report.get("authoring_gate")
    if authoring_gate not in {AUTHORING_GATE_PASS, AUTHORING_GATE_FAIL}:
        errors.append(
            f"static report {relative} authoring_gate must be a current contract status"
        )
    if "status" in report and report.get("status") != authoring_gate:
        errors.append(
            f"static report {relative} status must match authoring_gate"
        )
    blockers = report.get("blockers")
    blocker_errors, error_blockers = _blocker_list_errors(
        relative, "blockers", blockers
    )
    errors.extend(blocker_errors)
    if authoring_gate == AUTHORING_GATE_PASS and error_blockers:
        errors.append(
            f"static report {relative} cannot pass with error blockers"
        )
    if authoring_gate == AUTHORING_GATE_FAIL and not error_blockers:
        errors.append(
            f"static report {relative} cannot fail without an error blocker"
        )
    if relative == "reports/professionalism-regression-report.json":
        summary = report.get("summary")
        if not isinstance(summary, dict):
            errors.append(f"static report {relative} must contain a summary mapping")
        elif summary.get("blocker_count") != (
            len(blockers) if isinstance(blockers, list) else 0
        ):
            errors.append(
                f"static report {relative} summary.blocker_count does not match blockers"
            )
    return errors


def _professionalism_report_envelope_errors(
    relative: str, report: dict
) -> list[str]:
    expected_fields = PROFESSIONALISM_REPORT_FIELDS.get(relative)
    if expected_fields is None:
        return []
    schema_version = report.get("schema_version")
    if schema_version == PROFESSIONALISM_REPORT_SCHEMA_VERSION:
        expected_fields = {*expected_fields, "expert_panel_release_manifest"}
    elif schema_version != LEGACY_PROFESSIONALISM_REPORT_SCHEMA_VERSION:
        return [
            f"static report {relative} schema_version must be 3 or 4"
        ]
    if set(report) != expected_fields:
        return [
            f"static report {relative} fields do not match the closed "
            "professionalism report envelope"
        ]
    errors: list[str] = []
    advisories = report.get("advisories")
    if not isinstance(advisories, list):
        errors.append(f"static report {relative} advisories must be a list")
    if relative == "reports/professionalism-regression-report.json":
        if not isinstance(report.get("mode"), str) or not report["mode"].strip():
            errors.append(f"static report {relative} mode must be a non-blank string")
        if type(report.get("strict")) is not bool:
            errors.append(f"static report {relative} strict must be a boolean")
        if not isinstance(report.get("summary"), dict):
            errors.append(f"static report {relative} summary must be a mapping")
        if schema_version == PROFESSIONALISM_REPORT_SCHEMA_VERSION:
            errors.extend(
                f"static report {relative} {error}"
                for error in validate_expert_panel_release_manifest(
                    report.get("expert_panel_release_manifest"),
                    require_current=(report.get("release_gate") == RELEASE_GATE_PASS),
                )
            )
        elif report.get("release_gate") == RELEASE_GATE_PASS:
            errors.append(
                f"static report {relative} legacy schema 3 cannot claim formal release"
            )
    else:
        release_claim = report.get("release_claim")
        if not isinstance(release_claim, str) or not release_claim.strip():
            errors.append(
                f"static report {relative} release_claim must be a non-blank string"
            )
    return errors


def _release_gate_errors(relative: str, report: dict) -> list[str]:
    errors: list[str] = []
    release_gate = report.get("release_gate")
    if release_gate not in {RELEASE_GATE_PASS, RELEASE_GATE_FAIL}:
        errors.append(
            f"static report {relative} release_gate must be release-ready or "
            "release-not-ready"
        )
    release_blockers = report.get("release_blockers")
    blocker_errors, error_blocker_count = _blocker_list_errors(
        relative, "release_blockers", release_blockers
    )
    errors.extend(blocker_errors)
    if not isinstance(release_blockers, list):
        release_blockers = []

    authoring_blockers = report.get("blockers")
    if isinstance(authoring_blockers, list) and any(
        blocker not in release_blockers for blocker in authoring_blockers
    ):
        errors.append(
            f"static report {relative} release_blockers must include every "
            "authoring blocker"
        )

    readiness = report.get("content_readiness")
    expert = readiness.get("expert") if isinstance(readiness, dict) else None
    readability = expert.get("readability") if isinstance(expert, dict) else None
    professional_completeness = (
        expert.get("professional_completeness")
        if isinstance(expert, dict)
        else None
    )
    aggregate = readiness.get("aggregate") if isinstance(readiness, dict) else None
    readability_ready = bool(
        isinstance(aggregate, dict)
        and aggregate.get("readability_review_current") is True
        and _readability_formal_ready(readability)
    )
    professional_completeness_ready = bool(
        isinstance(aggregate, dict)
        and aggregate.get("professional_completeness_review_current") is True
        and _professional_completeness_formal_ready(professional_completeness)
        and isinstance(professional_completeness, dict)
        and professional_completeness.get("review_cost_current") is True
        and isinstance(report.get("professional_review_cost_fixtures"), dict)
        and report["professional_review_cost_fixtures"].get("status") == "pass"
    )
    manifest_ready = bool(
        report.get("schema_version") == PROFESSIONALISM_REPORT_SCHEMA_VERSION
        and not validate_expert_panel_release_manifest(
            report.get("expert_panel_release_manifest"),
            require_current=True,
        )
    )
    root_summary = report.get("root_content_summary")
    expected_gate = (
        RELEASE_GATE_PASS
        if report.get("authoring_gate") == AUTHORING_GATE_PASS
        and readability_ready
        and professional_completeness_ready
        and manifest_ready
        and error_blocker_count == 0
        else RELEASE_GATE_FAIL
    )
    if release_gate != expected_gate:
        errors.append(
            f"static report {relative} release_gate does not match authoring, "
            "readability review, Professional Completeness review, and "
            "current Semantic application readiness"
        )
    if release_gate == RELEASE_GATE_PASS and error_blocker_count:
        errors.append(
            f"static report {relative} cannot be release-ready with release blockers"
        )
    if release_gate == RELEASE_GATE_FAIL and not error_blocker_count:
        errors.append(
            f"static report {relative} cannot be release-not-ready without a "
            "release blocker"
        )

    readability_release_blockers = [
        blocker
        for blocker in release_blockers
        if isinstance(blocker, dict)
        and blocker.get("category") == READABILITY_RELEASE_BLOCKER_CATEGORY
    ]
    expected_readability_blockers = 0 if readability_ready else 1
    if len(readability_release_blockers) != expected_readability_blockers:
        errors.append(
            f"static report {relative} readability release blocker count must equal "
            f"{expected_readability_blockers}"
        )
    completeness_release_blockers = [
        blocker
        for blocker in release_blockers
        if isinstance(blocker, dict)
        and blocker.get("category")
        == PROFESSIONAL_COMPLETENESS_RELEASE_BLOCKER_CATEGORY
    ]
    expected_completeness_blockers = 0 if professional_completeness_ready else 1
    if len(completeness_release_blockers) != expected_completeness_blockers:
        errors.append(
            f"static report {relative} professional-completeness release blocker "
            f"count must equal {expected_completeness_blockers}"
        )
    if relative == "reports/professionalism-regression-report.json":
        summary = report.get("summary")
        if isinstance(summary, dict) and summary.get("release_blocker_count") != len(
            release_blockers
        ):
            errors.append(
                f"static report {relative} summary.release_blocker_count does "
                "not match release_blockers"
            )
    return errors


def _static_report_errors(root: Path) -> list[str]:
    """Validate checked-in JSON semantics without re-executing any producer."""
    errors: list[str] = []
    loaded_reports: dict[str, dict] = {}
    for relative, (status_field, expected_status) in STATIC_REPORT_CONTRACTS.items():
        path = root / relative
        if not path.is_file():
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"static report is unreadable: {relative}: {exc}")
            continue
        if not isinstance(report, dict):
            errors.append(f"static report must contain an object: {relative}")
            continue
        loaded_reports[relative] = report
        if report.get(status_field) != expected_status:
            errors.append(
                f"static report {relative} must set {status_field}={expected_status!r}"
            )
        expected_scope = STATIC_REPORT_EVIDENCE_SCOPES.get(
            relative,
            "deterministic-fixtures",
        )
        if report.get("evidence_scope") != expected_scope:
            errors.append(
                f"static report {relative} must use evidence_scope={expected_scope!r}"
            )
        limitations = report.get("limitations")
        if not isinstance(limitations, list) or not limitations:
            errors.append(f"static report {relative} must declare non-empty limitations")
            continue
        folded = " ".join(str(item) for item in limitations).casefold()
        required_limits = {
            "wall-clock performance": "wall-clock performance",
            "real-host accuracy": "real-host accuracy",
            "installed user experience": "installed user experience",
        }
        for label, token in required_limits.items():
            if token not in folded:
                errors.append(f"static report {relative} lacks {label} limitation")
        if relative in CONTENT_READINESS_REPORTS:
            errors.extend(_professionalism_report_envelope_errors(relative, report))
            errors.extend(_content_readiness_errors(relative, report, root=root))
            errors.extend(_status_blocker_errors(relative, report))
            errors.extend(_release_gate_errors(relative, report))
    return errors


def validate_productization_assets(root: Path = ROOT) -> list[str]:
    errors = [f"missing required product asset: {path}" for path in REQUIRED if not (root / path).is_file()]
    errors.extend(f"forbidden product path remains: {path}" for path in FORBIDDEN if (root / path).exists())
    errors.extend(_docs_errors(root))
    errors.extend(_static_report_errors(root))

    schema_path = root / "schemas/marketplace-index.schema.json"
    if schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if schema.get("properties", {}).get("schema_version", {}).get("const") != 3:
            errors.append("Marketplace schema must require schema_version 3")
        if schema.get("properties", {}).get("profile") != {
            "const": "recommended"
        }:
            errors.append(
                "Marketplace schema must expose one fixed recommended Runtime projection"
            )

    installation_report_path = root / "reports/installation-validation.json"
    if installation_report_path.is_file():
        report = json.loads(installation_report_path.read_text(encoding="utf-8"))
        summary = report.get("summary", {})
        if report.get("schema_version") != 2:
            errors.append("installation report must use Hookless schema_version 2")
        if report.get("architecture") != "hookless-control-plane-v1":
            errors.append("installation report must name the Hookless architecture")
        if report.get("status") != "pass":
            errors.append("installation report must contain a current passing validation")
        if summary.get("obsolete_runtime_artifacts") != 0:
            errors.append("installation report contains obsolete runtime artifacts")
        for obsolete in ("required_hook_runtime_files", "runtime_roots"):
            if obsolete in summary:
                errors.append(f"installation report retains obsolete field: {obsolete}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    errors = validate_productization_assets(Path(args.root))
    if errors:
        for error in errors:
            print(f"validate-productization-assets: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-productization-assets: hookless docs, reports, Marketplace, and boundaries are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
