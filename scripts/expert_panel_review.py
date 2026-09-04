#!/usr/bin/env python3
"""Prepare, validate, and aggregate independent content-review ballots."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Callable, Iterable

try:
    from validation_utils import (
        SKILL_EXPERTISE_TAGS,
        ValidationProblem,
        load_yaml_file,
        reference_contracts,
    )
except ModuleNotFoundError:  # Support direct importlib loading in isolated tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validation_utils import (
        SKILL_EXPERTISE_TAGS,
        ValidationProblem,
        load_yaml_file,
        reference_contracts,
    )

try:
    import professional_completeness_carry_forward as professional_carry
except ModuleNotFoundError:  # Support direct importlib loading in isolated tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import professional_completeness_carry_forward as professional_carry

try:
    import expert_panel_contracts as panel_contracts
except ModuleNotFoundError:  # Support direct importlib loading in isolated tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import expert_panel_contracts as panel_contracts

try:
    import expert_panel_manifest as reviewer_manifest
except ModuleNotFoundError:  # Support direct importlib loading in isolated tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import expert_panel_manifest as reviewer_manifest

try:
    import expert_panel_attestation as panel_attestation
except ModuleNotFoundError:  # Support direct importlib loading in isolated tests.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import expert_panel_attestation as panel_attestation


ROOT = Path(__file__).resolve().parents[1]
PANEL_SIZE = 3
VALIDATION_MODE_CURRENT = "current"
VALIDATION_MODE_HISTORICAL = "historical"
VALIDATION_MODES = {
    VALIDATION_MODE_CURRENT,
    VALIDATION_MODE_HISTORICAL,
}
DECISION_METHOD = "three-independent-experts-majority"
PROFESSIONAL_COMPLETENESS_DECISION_METHOD = (
    panel_contracts.PROFESSIONAL_DECISION_METHOD
)
PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD = (
    panel_contracts.PROFESSIONAL_INCREMENTAL_DECISION_METHOD
)
PACKET_KIND = "changeforge.expert-panel-packet"
BALLOT_KIND = "changeforge.expert-panel-ballot"
DECISION_KIND = "changeforge.expert-panel-decision"
PROFESSIONAL_COMPLETENESS_PACKET_KIND = panel_contracts.PROFESSIONAL_PACKET_KIND
PROFESSIONAL_COMPLETENESS_BALLOT_KIND = panel_contracts.PROFESSIONAL_BALLOT_KIND
PROFESSIONAL_COMPLETENESS_DECISION_KIND = panel_contracts.PROFESSIONAL_DECISION_KIND
PROFESSIONAL_COMPLETENESS_CAPSULE_KIND = (
    panel_contracts.PROFESSIONAL_REVIEW_CAPSULE_KIND
)
PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND = (
    panel_contracts.PROFESSIONAL_DISCOVERY_CAPSULE_KIND
)
PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND = (
    panel_contracts.PROFESSIONAL_CANDIDATE_REQUEST_KIND
)
SEMANTIC_DISPOSITION_PACKET_KIND = "changeforge.semantic-disposition-panel-packet"
SEMANTIC_DISPOSITION_BALLOT_KIND = "changeforge.semantic-disposition-panel-ballot"
SEMANTIC_DISPOSITION_DECISION_KIND = "changeforge.semantic-disposition-panel-decision"
SEMANTIC_DISPOSITION_APPLICATION_KIND = (
    "changeforge.semantic-disposition-application"
)
SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION = 1
READABILITY_PANEL_KIND = "readability"
PROFESSIONAL_COMPLETENESS_PANEL_KIND = "professional-completeness"
PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS = "professional-completeness"
SEMANTIC_DISPOSITION_PANEL_KIND = "semantic-disposition"
PANEL_KINDS = {
    READABILITY_PANEL_KIND,
    PROFESSIONAL_COMPLETENESS_PANEL_KIND,
    SEMANTIC_DISPOSITION_PANEL_KIND,
}
SCHEMA_VERSION = 1
READABILITY_SCHEMA_VERSION = 2
SEMANTIC_DISPOSITION_SCHEMA_VERSION = 2
PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION = 2
PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION = (
    panel_contracts.PROFESSIONAL_SCHEMA3_SCHEMA_VERSION
)
PROFESSIONAL_COMPLETENESS_MAX_PLAN_LINEAGE_DEPTH = (
    panel_contracts.PROFESSIONAL_MAXIMUM_PLAN_LINEAGE_DEPTH
)
PROFESSIONAL_PACKAGE_COUNT = 188
PROFESSIONAL_LEGACY_PACKAGE_COUNT = 162
PROFESSIONAL_CURRENT_LAYER_COUNTS = {
    "professional": 25,
    "foundation": 150,
    "domain": 13,
}
PROFESSIONAL_LEGACY_LAYER_COUNTS = {
    "professional": 22,
    "foundation": 133,
    "domain": 7,
}
PROFESSIONAL_ADJACENCY_TOP_K = panel_contracts.PROFESSIONAL_ADJACENCY_TOP_K
PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K = (
    panel_contracts.PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K
)
PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET = (
    panel_contracts.PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
)
PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID = (
    "professional-completeness-panel-2026-07-24-r11"
)
PROFESSIONAL_HISTORICAL_CAP50_PACKET_SHA256 = (
    "400181898429b8ee7740dc5168fb9b4cdc58922907e260fd99c9c0f4c03d2de0"
)
PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT = (
    "88a60c74fa8c47f9b9e5eed6a9caaf9381073057ee806b2dc2d0836709dccdde"
)
PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT = 162
PROFESSIONAL_HISTORICAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET = 50
PROFESSIONAL_HISTORICAL_CAP50_BASELINE_REVIEW_ID = (
    "professional-completeness-panel-2026-07-18-r9"
)
PROFESSIONAL_HISTORICAL_CAP50_BASELINE_DECISION_SHA256 = (
    "8b7b98f9a7101bc98fc7b16dcd7569e607fe0b433c0261926a9bba42aa34ab50"
)
PROFESSIONAL_HISTORICAL_CAP50_BASELINE_PACKET_SHA256 = (
    "3651698e0191d212f5ff7cd453bad68945cd2f975fe50cee0acad53007e0b169"
)
PROFESSIONAL_HISTORICAL_V1_REVIEW_ID = (
    "professional-completeness-panel-2026-08-02-r14"
)
PROFESSIONAL_HISTORICAL_V1_PACKET_SHA256 = (
    "8c64ee3b1056cebd8a9e5ff99468858c204960e427f8a94050d141f46bb2b219"
)
PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT = (
    "8b5b6a00e4f707e87f436b724cabead4a5426862a27b85adc8f1d7f597374a0a"
)
PROFESSIONAL_HISTORICAL_V2_REVIEW_CONTRACT_FINGERPRINT = (
    "725d3f2ca9f413b27a015c9aa36f4ae8099325266923555526b4d059c4d9f405"
)
PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT = (
    panel_contracts.PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT
)
PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL = (
    panel_contracts.PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL
)
PROFESSIONAL_ADJACENCY_SELECTION_VERSION = (
    panel_contracts.PROFESSIONAL_ADJACENCY_SELECTION_VERSION
)
PROFESSIONAL_SOURCE_DECLARED_SELECTION_VERSION = (
    panel_contracts.PROFESSIONAL_SOURCE_DECLARED_SELECTION_VERSION
)
PROFESSIONAL_ADJACENCY_ALGORITHM = (
    panel_contracts.PROFESSIONAL_ADJACENCY_ALGORITHM
)
PROFESSIONAL_ADJACENCY_MAX_DOCUMENT_FREQUENCY_PERCENT = (
    panel_contracts.PROFESSIONAL_ADJACENCY_MAX_DOCUMENT_FREQUENCY_PERCENT
)
PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS = dict(
    panel_contracts.PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS
)
PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS = (
    panel_contracts.PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS
)
PROFESSIONAL_ADJACENCY_REVIEW_ORIGINS = {
    "packet-required",
    "reviewer-added",
}
PROFESSIONAL_NEGATIVE_ROUTE_MATCH_VERSION = (
    panel_contracts.PROFESSIONAL_NEGATIVE_ROUTE_MATCH_VERSION
)
PROFESSIONAL_NEGATIVE_ROUTE_MIN_OVERLAP_TOKENS = (
    panel_contracts.PROFESSIONAL_NEGATIVE_ROUTE_MIN_OVERLAP_TOKENS
)
PROFESSIONAL_NEGATIVE_ROUTE_GENERIC_TOKENS = (
    panel_contracts.PROFESSIONAL_NEGATIVE_ROUTE_GENERIC_TOKENS
)
PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG = (
    panel_contracts.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
)
VOTER_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
EXPERTISE_TAG_PATTERN = VOTER_ID_PATTERN
CONTENT_DECISIONS = {
    "accepted-current-density",
    "tracked-tightening",
}
READABILITY_DECISIONS = {
    "accepted-current-readability",
    "tracked-tightening",
}
ACTIONABILITY_DECISIONS = {
    "accepted-current-actionability",
    "detector-false-positive",
    "rewrite-required",
}
PROFESSIONAL_COMPLETENESS_DECISIONS = set(panel_contracts.PROFESSIONAL_DECISIONS)
PROFESSIONAL_COMPLETENESS_CRITERIA = dict(panel_contracts.PROFESSIONAL_CRITERIA)
PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA = set(
    panel_contracts.PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
)
PROFESSIONAL_ORDINARY_CRITERIA = set(
    panel_contracts.PROFESSIONAL_ORDINARY_CRITERIA
)
PROFESSIONAL_CRITERION_VALUES = set(
    panel_contracts.PROFESSIONAL_CRITERION_VALUES
)
PROFESSIONAL_UNRESOLVED_DISPOSITION = (
    panel_contracts.PROFESSIONAL_UNRESOLVED_DISPOSITION
)
PROFESSIONAL_FINAL_DISPOSITIONS = set(
    panel_contracts.PROFESSIONAL_FINAL_DISPOSITIONS
)
PROFESSIONAL_REVIEW_OUTCOMES = set(
    panel_contracts.PROFESSIONAL_REVIEW_OUTCOMES
)
PROFESSIONAL_ADJACENCY_DISPOSITIONS = set(
    panel_contracts.PROFESSIONAL_ADJACENCY_DISPOSITIONS
)
SEMANTIC_DISPOSITIONS = {
    "rewrite",
    "valid-contextual-rule",
    "false-positive",
    "time-bounded-exception",
}
SEMANTIC_AXES = {"root", "reference"}
SEMANTIC_SOURCE_FINGERPRINT_KEYS = set(
    panel_contracts.SEMANTIC_DISPOSITION_SOURCE_FINGERPRINT_KEYS
)
SEMANTIC_LEGACY_SOURCE_FINGERPRINT_KEYS = set(
    panel_contracts.SEMANTIC_DISPOSITION_LEGACY_SOURCE_FINGERPRINT_KEYS
)
REASON_CODES = {
    "accepted-current-density": {
        "bounded-density-preserves-professional-coverage",
        "split-would-fragment-one-decision-model",
    },
    "accepted-current-readability": {
        "bounded-enumeration-improves-precision",
        "domain-terms-require-co-location",
        "single-indivisible-decision",
        "split-would-fragment-invariant",
    },
    "tracked-tightening": {
        "cross-boundary-decisions-conflated",
        "enumeration-obscures-primary-action",
        "multiple-independent-actions",
        "policy-exception-verification-conflated",
    },
}
ACTIONABILITY_REASON_CODES = {
    "accepted-current-actionability": {
        "bounded-skill-needs-fewer-generic-signals",
        "explicit-domain-actions-are-front-loaded",
        "short-root-is-actionable-as-a-whole",
    },
    "detector-false-positive": {
        "equivalent-action-verb-not-recognized",
        "equivalent-heading-not-recognized",
        "front-window-structure-misclassified",
    },
    "rewrite-required": {
        "generic-context-obscures-first-move",
        "primary-action-not-front-loaded",
        "stop-or-escalation-not-front-loaded",
        "verification-not-front-loaded",
    },
}
READABILITY_V2_REASON_CODES = {**REASON_CODES, **ACTIONABILITY_REASON_CODES}
PROFESSIONAL_REASON_CODES = panel_attestation.PROFESSIONAL_REASON_CODES
ALL_REASON_CODES = {
    **READABILITY_V2_REASON_CODES,
    **PROFESSIONAL_REASON_CODES,
}
LEGACY_READABILITY_PACKET_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "source_fingerprints",
    "panel_contract",
    "rubric",
    "content_targets",
    "readability_targets",
    "limitations",
}
READABILITY_PACKET_FIELDS = {
    *LEGACY_READABILITY_PACKET_FIELDS,
    "actionability_targets",
}
CONTENT_SOURCE_BINDING_CONTRACT = "root-body-document-context-v1"
LEGACY_CONTENT_TARGET_FIELDS = {
    "path",
    "classification",
    "review_state",
    "review_reasons",
}
CONTENT_TARGET_FIELDS = {
    *LEGACY_CONTENT_TARGET_FIELDS,
    "document_id",
    "owner",
    "document_part",
    "source_selector",
    "content_fingerprint",
    "document_context",
}
LEGACY_READABILITY_BALLOT_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "source_fingerprints",
    "voter",
    "content_votes",
    "readability_votes",
    "limitations",
}
READABILITY_BALLOT_FIELDS = {
    *LEGACY_READABILITY_BALLOT_FIELDS,
    "actionability_votes",
}
VOTER_FIELDS = {
    "voter_id",
    "agent_id",
    "role",
    "expertise",
    "independent_review",
}
PROFESSIONAL_V2_VOTER_FIELDS = {
    *VOTER_FIELDS,
    "expertise_tags",
    "qualification_claims",
}
CONTENT_VOTE_FIELDS = {
    "path",
    "classification",
    "decision",
    "reason_code",
    "rationale",
}
READABILITY_VOTE_FIELDS = {
    "document_id",
    "highest_band",
    "decision",
    "reason_code",
    "rationale",
}
READABILITY_V2_VOTE_FIELDS = {
    "document_id",
    "highest_band",
    "finding_reviews",
}
READABILITY_FINDING_REVIEW_FIELDS = {
    "finding_id",
    "sentence_fingerprint",
    "decision",
    "reason_code",
    "rationale",
}
READABILITY_V2_TARGET_FIELDS = {
    "document_id",
    "path",
    "surface",
    "document_part",
    "owner",
    "source_selector",
    "content_fingerprint",
    "document_context",
    "highest_band",
    "findings",
}
READABILITY_DOCUMENT_CONTEXT_FIELDS = {
    "line_count",
    "text",
    "lines",
    "sha256",
}
READABILITY_SOURCE_SELECTOR_FIELDS_BY_KIND = {
    "whole-file": {"kind", "path"},
    "yaml-body": {"kind", "path"},
    "yaml-description": {"kind", "path", "field"},
    "json-profile-field": {
        "kind",
        "path",
        "profile_name",
        "field",
    },
}
READABILITY_SOURCE_SPAN_FIELDS = {
    "start_offset",
    "end_offset",
    "start_line",
    "end_line",
    "start_column",
    "end_column",
    "lines",
    "sha256",
}
READABILITY_CONTEXT_LINE_FIELDS = {"line", "text"}
READABILITY_V2_FINDING_FIELDS = {
    "finding_id",
    "line",
    "band",
    "words",
    "kind",
    "sentence",
    "sentence_fingerprint",
    "source_span",
}
ACTIONABILITY_VOTE_FIELDS = {
    "target_id",
    "decision",
    "reason_code",
    "evidence",
    "rationale",
}
ACTIONABILITY_EVIDENCE_FIELDS = {
    "line",
    "source_line",
    "claim",
}
ACTIONABILITY_TARGET_FIELDS = {
    "target_id",
    "skill_id",
    "path",
    "kind",
    "actionability_model",
    "review_state",
    "front_loaded_action_score",
    "front_window",
    "content_fingerprint",
}
ACTIONABILITY_FRONT_WINDOW_FIELDS = {
    "start_line",
    "end_line",
    "line_count",
    "lines",
    "sha256",
}
ACTIONABILITY_FRONT_WINDOW_LINE_FIELDS = {"line", "text"}
PROFESSIONAL_PACKET_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "source_fingerprints",
    "panel_contract",
    "rubric",
    "professional_targets",
    "limitations",
}
PROFESSIONAL_V3_PACKET_FIELDS = {
    *(PROFESSIONAL_PACKET_FIELDS - {"source_fingerprints"}),
    "review_contract_fingerprint",
    "review_plan",
}
PROFESSIONAL_HISTORICAL_V3_PACKET_FIELDS = {
    *PROFESSIONAL_V3_PACKET_FIELDS,
    "source_fingerprints",
}
PROFESSIONAL_V3_PACKET_TARGET_FIELDS = {
    "skill_id",
    "layer",
    "root",
    "indexed_references",
    "registry",
    "registry_authority",
    "reference_authority",
    "required_expertise_tags",
    "routing_adjacency",
    "review_binding",
}
PROFESSIONAL_BALLOT_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "source_fingerprints",
    "voter",
    "professional_votes",
    "limitations",
}
PROFESSIONAL_V3_BALLOT_FIELDS = {
    *(PROFESSIONAL_BALLOT_FIELDS - {"source_fingerprints"}),
    "review_contract_fingerprint",
    "capsule",
}
PROFESSIONAL_V3_CAPSULE_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "review_contract_fingerprint",
    "voter_id",
    "discovery_capsule",
    "candidate_request",
    "review_projection",
    "limitations",
}
PROFESSIONAL_V3_DISCOVERY_CAPSULE_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "review_contract_fingerprint",
    "voter_id",
    "discovery_projection",
    "limitations",
}
PROFESSIONAL_V3_CANDIDATE_REQUEST_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "review_contract_fingerprint",
    "voter_id",
    "discovery_capsule",
    "assigned_fresh_target_ids",
    "reviewer_added_requests",
    "limitations",
}
PROFESSIONAL_V3_CANDIDATE_REQUEST_ROW_FIELDS = {
    "target_skill_id",
    "skill_id",
    "discovery_reason",
    "ranking_evidence",
    "material_fingerprint",
}
PROFESSIONAL_V3_DECISION_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "decided_on",
    "decision_method",
    "review_contract_fingerprint",
    "panel_contract",
    "packet",
    "voters",
    "professional_decisions",
    "summary",
    "limitations",
}
PROFESSIONAL_HISTORICAL_V3_DECISION_FIELDS = {
    *PROFESSIONAL_V3_DECISION_FIELDS,
    "source_fingerprints",
}
PROFESSIONAL_V3_DECISION_VOTER_FIELDS = {
    *PROFESSIONAL_V2_VOTER_FIELDS,
    "assigned_skill_ids",
    "ballot",
    "capsule",
    "capsule_canonical_json_bytes_proxy",
    "capsule_input_blocks_proxy",
}
PROFESSIONAL_V3_PROVENANCE_EVIDENCE_FIELDS = {
    "voter_id",
    "ballot",
    "capsule",
}
PROFESSIONAL_V3_INPUT_BLOCK_FIELDS = {
    "sha256",
    "canonical_json_bytes_proxy",
}
PROFESSIONAL_V3_TARGET_DECISION_FIELDS = {
    "skill_id",
    "review_unit_binding",
    "qualification_coverage",
    "criterion_vote_counts",
    "domain_critical_defects",
    "ordinary_criterion_defects",
    "ordinary_criterion_disposition",
    "reviewer_added_adjacency_reviews",
    "winning_disposition",
    "winning_votes",
    "vote_counts",
    "supporting_voters",
    "dissenting_voters",
    "winning_rationales",
    "final_disposition",
    "review_dependencies",
    "evidence_metrics",
    "provenance",
    "target_decision_fingerprint",
}
PROFESSIONAL_V3_EVIDENCE_METRIC_FIELDS = {
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
PROFESSIONAL_VOTE_FIELDS = {
    "skill_id",
    "decision",
    "reason_code",
    "criteria",
    "rationale",
}
PROFESSIONAL_V2_VOTE_FIELDS = {
    "skill_id",
    "decision",
    "reason_code",
    "evidence_anchors",
    "criteria",
    "examined_failure_modes",
    "examined_omission_candidates",
    "examined_adjacent_candidates",
    "proof_limits",
    "rationale",
}
PROFESSIONAL_EVIDENCE_ANCHOR_FIELDS = {
    "anchor_id",
    "skill_id",
    "path",
    "start_line",
    "end_line",
}
PROFESSIONAL_CRITERION_RESULT_FIELDS = {
    "status",
    "evidence_assertions",
}
PROFESSIONAL_EVIDENCE_ASSERTION_FIELDS = {
    "claim",
    "evidence_anchor_ids",
    "source_excerpt_sha256",
}
PROFESSIONAL_FAILURE_MODE_FIELDS = {
    "failure_mode",
    "outcome",
    "evidence_anchor_ids",
    "rationale",
}
PROFESSIONAL_OMISSION_CANDIDATE_FIELDS = {
    "omission_candidate",
    "outcome",
    "evidence_anchor_ids",
    "rationale",
}
PROFESSIONAL_ADJACENCY_REVIEW_FIELDS = {
    "skill_id",
    "review_origin",
    "discovery_reason",
    "disposition",
    "target_anchor_ids",
    "candidate_anchor_ids",
    "rationale",
}
PROFESSIONAL_ADJACENCY_CANDIDATE_FIELDS = {
    "skill_id",
    "rank",
    "total_score",
    "signals",
    "declared",
    "selection_reasons",
}
PROFESSIONAL_ADJACENCY_RANKING_FIELDS = (
    PROFESSIONAL_ADJACENCY_CANDIDATE_FIELDS
    - {"declared", "selection_reasons"}
)
PROFESSIONAL_ADJACENCY_SIGNAL_FIELDS = {
    "matched_tokens",
    "count",
    "weight",
}
PROFESSIONAL_QUALIFICATION_CLAIM_FIELDS = {
    "expertise_tag",
    "qualification_basis",
    "proof_limit",
}
SEMANTIC_PACKET_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "source_fingerprints",
    "panel_contract",
    "rubric",
    "candidate_provenance",
    "semantic_targets",
    "limitations",
}
SEMANTIC_BALLOT_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "source_fingerprints",
    "voter",
    "semantic_votes",
    "limitations",
}
SEMANTIC_VOTE_FIELDS = {
    "target_id",
    "axis",
    "candidate_id",
    "disposition",
    "rationale",
    "authority_or_condition",
    "decision_owner",
    "mitigation",
    "review_after",
}
SEMANTIC_TARGET_FIELDS = {
    "target_id",
    "axis",
    "carry_forward_mismatches",
    "candidate_binding_fingerprint",
    "candidate",
}
SEMANTIC_PROVENANCE_FIELDS = {
    "raw_candidate_count",
    "eligible_candidate_count",
    "detector_downgraded_count",
    "configured_entry_count",
    "exact_carry_forward_count",
    "exact_carry_forward_candidate_ids",
    "review_target_count",
    "review_target_candidate_ids",
    "same_id_stale_evidence_candidate_ids",
    "stale_old_count",
    "stale_old_candidate_ids",
}
LEGACY_SEMANTIC_APPLICATION_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "decision_kind",
    "decision",
}
REGISTRY_SOURCES = (
    ("professional", "src/registry/professional-skills.yaml", "professional_skills"),
    ("foundation", "src/registry/foundation-skills.yaml", "foundation_skills"),
    ("domain", "src/registry/domain-skills.yaml", "domain_skills"),
)
PROFESSIONAL_ADJACENCY_STOP_WORDS = (
    panel_contracts.PROFESSIONAL_ADJACENCY_STOP_WORDS
)
PROFESSIONAL_EVIDENCE_STOP_WORDS = (
    panel_contracts.PROFESSIONAL_EVIDENCE_STOP_WORDS
)
PROFESSIONAL_V3_GROUNDING_STOP_WORDS = (
    panel_contracts.PROFESSIONAL_GROUNDING_STOP_WORDS
)


class PanelReviewError(ValueError):
    """Raised when a panel artifact violates the closed voting contract."""


class ProfessionalReviewerAddedRequiredPromotionDrift(PanelReviewError):
    """A trusted reviewer-added candidate became required by current authority."""

    def __init__(
        self,
        skill_id: str,
        candidate_ids: Iterable[str],
        *,
        overlaps: dict[str, Iterable[str]] | None = None,
    ) -> None:
        self.skill_id = skill_id
        self.candidate_ids = tuple(sorted(candidate_ids))
        normalized_overlaps = overlaps or {skill_id: self.candidate_ids}
        self.overlaps = tuple(
            (
                overlap_skill_id,
                tuple(sorted(overlap_candidate_ids)),
            )
            for overlap_skill_id, overlap_candidate_ids in sorted(
                normalized_overlaps.items()
            )
        )
        super().__init__(
            "Professional reviewer-added candidates became current required "
            "candidates: "
            + "; ".join(
                f"{overlap_skill_id}={','.join(overlap_candidate_ids)}"
                for overlap_skill_id, overlap_candidate_ids in self.overlaps
            )
        )


def _closed_validation_mode(value: object) -> str:
    if value not in VALIDATION_MODES:
        raise PanelReviewError(
            "validation mode must be exactly current or historical"
        )
    return str(value)


def _professional_adjacency_max_required_candidates_total(
    target_count: object,
) -> int:
    """Scale the catalog budget from its locked baseline using floor rounding."""

    if type(target_count) is not int or target_count < 0:
        raise PanelReviewError(
            "professional adjacency target count must be a non-negative integer"
        )
    return (
        PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL
        * target_count
        // PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT
    )


PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_TOTAL = (
    _professional_adjacency_max_required_candidates_total(
        PROFESSIONAL_PACKAGE_COUNT
    )
)


def _json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PanelReviewError(f"{label} is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PanelReviewError(f"{label} must be a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PanelReviewError(f"cannot hash panel artifact: {path}") from exc


def _write_json(
    path: Path,
    value: dict[str, Any],
    *,
    compact: bool = False,
    create_only: bool = False,
    validation_root: Path | None = None,
) -> None:
    if compact:
        rendered = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    else:
        rendered = json.dumps(value, indent=2, ensure_ascii=False)
    if not create_only:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
        return
    if validation_root is None:
        raise PanelReviewError(
            "immutable panel artifact write requires validation_root"
        )
    root = validation_root.resolve()
    absolute_path = path.absolute()
    try:
        relative = absolute_path.relative_to(validation_root.absolute())
    except ValueError:
        try:
            relative = path.resolve().relative_to(root)
        except ValueError as exc:
            raise PanelReviewError(
                "immutable panel artifact escapes validation_root"
            ) from exc
    relative_name = relative.as_posix()
    if not relative.parts:
        raise PanelReviewError(
            "immutable panel artifact must name a file below validation_root"
        )
    _canonical_artifact_path(
        relative_name,
        validation_root=validation_root,
        label="immutable panel artifact output",
        must_exist=False,
    )
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    file_flags |= getattr(os, "O_NOFOLLOW", 0)
    file_flags |= getattr(os, "O_CLOEXEC", 0)
    directory_fd: int | None = None
    file_fd: int | None = None
    created = False
    created_identity: tuple[int, int] | None = None

    def unlink_created_if_still_owned() -> None:
        if (
            not created
            or directory_fd is None
            or created_identity is None
        ):
            return
        try:
            current = os.stat(
                relative.parts[-1],
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (current.st_dev, current.st_ino) == created_identity:
                os.unlink(relative.parts[-1], dir_fd=directory_fd)
        except OSError:
            pass

    try:
        directory_fd = os.open(root, directory_flags)
        for part in relative.parts[:-1]:
            try:
                next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=directory_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(
            relative.parts[-1],
            file_flags,
            0o644,
            dir_fd=directory_fd,
        )
        created = True
        initial_descriptor = os.fstat(file_fd)
        if not stat.S_ISREG(initial_descriptor.st_mode):
            raise PanelReviewError(
                "immutable panel artifact descriptor is not a regular file"
            )
        created_identity = (
            initial_descriptor.st_dev,
            initial_descriptor.st_ino,
        )
        stream = os.fdopen(file_fd, "w", encoding="utf-8")
        file_fd = None
        with stream:
            stream.write(rendered + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            descriptor = os.fstat(stream.fileno())
        os.fsync(directory_fd)
        stored_path = _canonical_artifact_path(
            relative_name,
            validation_root=validation_root,
            label="immutable panel artifact output",
        )
        pathname = stored_path.stat()
        if (descriptor.st_dev, descriptor.st_ino) != (
            pathname.st_dev,
            pathname.st_ino,
        ):
            raise PanelReviewError(
                "immutable panel artifact path changed during create-only write"
            )
    except FileExistsError as exc:
        raise PanelReviewError(
            f"immutable panel artifact already exists: {path}"
        ) from exc
    except PanelReviewError:
        unlink_created_if_still_owned()
        raise
    except OSError as exc:
        unlink_created_if_still_owned()
        raise PanelReviewError(
            f"cannot create immutable panel artifact: {path}: {exc}"
        ) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _path_record(path: Path, *, root: Path, label: str) -> dict[str, str]:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise PanelReviewError(f"{label} escapes the repository") from exc
    if not resolved.is_file():
        raise PanelReviewError(f"{label} is missing: {relative}")
    return {"path": relative, "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest()}


def _review_material_record(
    path: Path, *, root: Path, label: str
) -> dict[str, Any]:
    """Bind complete UTF-8 review material while retaining a stable file digest."""

    record = _path_record(path, root=root, label=label)
    try:
        content = path.resolve().read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PanelReviewError(f"{label} is not readable UTF-8") from exc
    if hashlib.sha256(content.encode("utf-8")).hexdigest() != record["sha256"]:
        raise PanelReviewError(f"{label} UTF-8 content does not match its byte digest")
    return {
        **record,
        "line_count": len(content.splitlines()),
        "content": content,
    }


def _string_list(value: object, *, label: str, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        suffix = "non-empty " if not allow_empty else ""
        raise PanelReviewError(f"{label} must be a {suffix}string array")
    return list(value)


def _expertise_tags(
    value: object,
    *,
    label: str,
    allow_architecture: bool,
    allow_historical: bool = False,
) -> list[str]:
    tags = _string_list(value, label=label, allow_empty=False)
    if tags != sorted(set(tags)):
        raise PanelReviewError(f"{label} must be sorted and unique")
    for tag in tags:
        if EXPERTISE_TAG_PATTERN.fullmatch(tag) is None:
            raise PanelReviewError(f"{label} must contain canonical expertise-tag slugs")
        if not allow_historical and tag not in SKILL_EXPERTISE_TAGS and not (
            allow_architecture
            and tag == PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
        ):
            raise PanelReviewError(f"{label} contains unknown expertise tag {tag!r}")
    return tags


def _adjacency_tokens(values: object) -> set[str]:
    if isinstance(values, str):
        texts = [values]
    elif isinstance(values, list):
        texts = [item for item in values if isinstance(item, str)]
    else:
        texts = []
    tokens = {
        token
        for text_value in texts
        for token in re.findall(r"[a-z0-9]+", text_value.casefold())
        if len(token) >= 3 and token not in PROFESSIONAL_ADJACENCY_STOP_WORDS
    }
    return tokens


def _negative_route_phrases(values: object) -> tuple[tuple[str, ...], ...]:
    """Preserve registry phrase boundaries for high-confidence route conflicts."""

    if not isinstance(values, list):
        return ()
    phrases = {
        tuple(
            sorted(
                _adjacency_tokens(value)
                - PROFESSIONAL_NEGATIVE_ROUTE_GENERIC_TOKENS
            )
        )
        for value in values
        if isinstance(value, str)
    }
    phrases.discard(())
    return tuple(sorted(phrases))


def _evidence_tokens(value: object) -> set[str]:
    if not isinstance(value, str):
        return set()
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) >= 3 and token not in PROFESSIONAL_EVIDENCE_STOP_WORDS
    }


def _professional_v3_grounding_contract() -> dict[str, Any]:
    """Return the closed schema-3-only semantic source-grounding contract."""

    return panel_contracts.professional_semantic_grounding_contract()


def _professional_v3_token_sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    return tuple(
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) >= 3 and token not in PROFESSIONAL_EVIDENCE_STOP_WORDS
    )


def _professional_v3_grounding_token_sequences(
    value: object,
) -> list[tuple[str, ...]]:
    """Keep only non-generic runs without joining across lexical gaps or lines."""

    if not isinstance(value, str):
        return []
    sequences: list[tuple[str, ...]] = []
    for line in value.splitlines() or [value]:
        run: list[str] = []
        for token in re.findall(r"[a-z0-9]+", line.casefold()):
            if (
                len(token) >= 3
                and any(character.isalpha() for character in token)
                and token not in PROFESSIONAL_V3_GROUNDING_STOP_WORDS
            ):
                run.append(token)
                continue
            if run:
                sequences.append(tuple(run))
                run = []
        if run:
            sequences.append(tuple(run))
    return sequences


def _professional_v3_ngrams(
    tokens: tuple[str, ...], size: int
) -> set[tuple[str, ...]]:
    if len(tokens) < size:
        return set()
    return {
        tuple(tokens[index : index + size])
        for index in range(len(tokens) - size + 1)
    }


def _markdown_frontmatter_lines(content: str) -> set[int]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return set(range(1, index + 1))
    return set()


@lru_cache(maxsize=1)
def _load_skill_content_auditor() -> ModuleType:
    """Load the canonical fenced-Markdown parser used by the Skill detector."""

    module_name = f"{__name__}_skill_content_auditor"
    existing = sys.modules.get(module_name)
    if isinstance(existing, ModuleType):
        return existing
    source = Path(__file__).resolve().with_name("audit-skill-content.py")
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise PanelReviewError(f"cannot load Skill detector parser: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1024)
def _detector_unfenced_line_numbers(content: str) -> frozenset[int]:
    """Return lines the canonical actionability detector treats as prose."""

    auditor = _load_skill_content_auditor()
    return frozenset(
        index + 1
        for index, _line, in_fence in auditor._strip_fenced(content.splitlines())
        if not in_fence
    )


def _is_substantive_markdown_line(content: str, line_number: int) -> bool:
    lines = content.splitlines()
    if line_number < 1 or line_number > len(lines):
        return False
    if (
        line_number in _markdown_frontmatter_lines(content)
        or line_number not in _detector_unfenced_line_numbers(content)
    ):
        return False
    line = lines[line_number - 1].strip()
    if not line:
        return False
    if re.fullmatch(r"#{1,6}(?:\s+.*)?", line):
        return False
    return True


def _substantive_excerpt(
    content: str, *, start_line: int, end_line: int
) -> str:
    lines = content.splitlines()
    substantive: list[str] = []
    for line_number in range(start_line, end_line + 1):
        if not _is_substantive_markdown_line(content, line_number):
            continue
        substantive.append(lines[line_number - 1])
    return "\n".join(substantive)


def _markdown_topic_headings(content: str) -> list[str]:
    headings: list[str] = []
    in_fence = False
    frontmatter_lines = _markdown_frontmatter_lines(content)
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        stripped = raw_line.strip()
        if re.fullmatch(r"(?:`{3,}|~{3,}).*", stripped):
            in_fence = not in_fence
            continue
        if in_fence or line_number in frontmatter_lines:
            continue
        match = re.match(r"^#{1,3}\s+(.+?)\s*#*\s*$", stripped)
        if match:
            headings.append(match.group(1))
    return headings


PROFESSIONAL_SOURCE_DECLARED_SKILL_ID_PATTERN = re.compile(
    r"(?<!`)`([a-z0-9]+(?:-[a-z0-9]+)*)`(?!`)"
)
PROFESSIONAL_SOURCE_DECLARED_EXCLUDED_SECTIONS = frozenset(
    {"background", "example", "examples", "history", "layer 3 delivery"}
)


def _markdown_source_declared_excluded_lines(content: str) -> set[int]:
    """Exclude tutorial/history and generated Layer 3 sections from routing facts."""

    excluded: set[int] = set()
    excluded_level: int | None = None
    unfenced_lines = _detector_unfenced_line_numbers(content)
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        if line_number not in unfenced_lines:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", raw_line.strip())
        if match is not None:
            level = len(match.group(1))
            heading = match.group(2).strip().casefold()
            if excluded_level is not None and level <= excluded_level:
                excluded_level = None
            if heading in PROFESSIONAL_SOURCE_DECLARED_EXCLUDED_SECTIONS:
                excluded_level = level
        if excluded_level is not None:
            excluded.add(line_number)
    return excluded


def _markdown_table_cells(raw_line: str) -> list[str] | None:
    """Return one simple Markdown table row without interpreting cell content."""

    if "|" not in raw_line:
        return None
    cells = [cell.strip() for cell in raw_line.strip().split("|")]
    if cells and cells[0] == "":
        cells.pop(0)
    if cells and cells[-1] == "":
        cells.pop()
    return cells if len(cells) >= 2 else None


def _markdown_table_separator(cells: list[str] | None) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
    )


def _source_declared_table_header(header: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", header.casefold()).strip()
    tokens = set(normalized.split())
    return bool(
        tokens & {"route", "routing"}
        or "owner" in tokens
        or "verification" in tokens
        or "handoff" in tokens
        or {"risk", "gate"} <= tokens
    )


def _source_declared_narrative_fragments(raw_line: str) -> list[str]:
    """Select imperative decision sentences, not ordinary mentions or history."""

    fragments: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", raw_line.strip()):
        sentence = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", sentence).strip()
        if re.match(r"^route\b.*\bto\b", sentence, flags=re.IGNORECASE):
            fragments.append(sentence)
            continue
        if re.match(r"^handoff\b.*\bto\b", sentence, flags=re.IGNORECASE):
            fragments.append(sentence)
            continue
        if re.match(
            r"^(?:routing owner|risk[- ]gate|verification owner|handoff owner)"
            r"\s*(?:is|are|:|=)",
            sentence,
            flags=re.IGNORECASE,
        ):
            fragments.append(sentence)
    return fragments


def _professional_source_declared_skill_ids(
    target: dict[str, Any],
    *,
    known_skill_ids: set[str],
) -> list[str]:
    """Project directional target-to-candidate facts from bound package material."""

    target_id = _non_blank(target.get("skill_id"), label="source-declared target")
    materials = [target.get("root"), *target.get("indexed_references", [])]
    declared: set[str] = set()

    def add_spans(value: str, *, material_path: str) -> None:
        for candidate_id in PROFESSIONAL_SOURCE_DECLARED_SKILL_ID_PATTERN.findall(
            value
        ):
            if candidate_id not in known_skill_ids:
                raise PanelReviewError(
                    "source-declared adjacency names unknown Skill package: "
                    f"{target_id} -> {candidate_id} ({material_path})"
                )
            if candidate_id == target_id:
                raise PanelReviewError(
                    "source-declared adjacency cannot self-reference: "
                    f"{target_id} ({material_path})"
                )
            declared.add(candidate_id)

    for material in materials:
        if not isinstance(material, dict):
            raise PanelReviewError(
                f"source-declared adjacency material is invalid: {target_id}"
            )
        content = material.get("content")
        material_path = material.get("path")
        if not isinstance(content, str) or not isinstance(material_path, str):
            raise PanelReviewError(
                f"source-declared adjacency material is incomplete: {target_id}"
            )
        eligible = set(_detector_unfenced_line_numbers(content))
        eligible -= _markdown_frontmatter_lines(content)
        eligible -= _markdown_source_declared_excluded_lines(content)
        lines = content.splitlines()
        table_lines: set[int] = set()
        line_index = 0
        while line_index + 1 < len(lines):
            header_line = line_index + 1
            separator_line = line_index + 2
            header_cells = _markdown_table_cells(lines[line_index])
            separator_cells = _markdown_table_cells(lines[line_index + 1])
            if (
                header_line not in eligible
                or separator_line not in eligible
                or header_cells is None
                or not _markdown_table_separator(separator_cells)
                or len(header_cells) != len(separator_cells or [])
            ):
                line_index += 1
                continue
            decision_columns = [
                index
                for index, header in enumerate(header_cells)
                if _source_declared_table_header(header)
            ]
            row_index = line_index + 2
            while row_index < len(lines):
                row_line = row_index + 1
                row_cells = _markdown_table_cells(lines[row_index])
                if row_line not in eligible or row_cells is None:
                    break
                table_lines.add(row_line)
                if decision_columns and len(row_cells) == len(header_cells):
                    for column in decision_columns:
                        add_spans(
                            row_cells[column],
                            material_path=material_path,
                        )
                row_index += 1
            table_lines.update({header_line, separator_line})
            line_index = max(line_index + 1, row_index)

        for line_number in sorted(eligible - table_lines):
            raw_line = lines[line_number - 1]
            for fragment in _source_declared_narrative_fragments(raw_line):
                add_spans(fragment, material_path=material_path)
    return sorted(declared)


def _professional_raw_adjacency_basis(
    target: dict[str, Any],
) -> dict[str, Any]:
    """Build relationship-independent features from embedded catalog content."""

    responsibility = target["registry"]["responsibility_contract"]
    reference_topics: list[str] = []
    for reference in target["indexed_references"]:
        reference_topics.append(reference["path"])
        reference_topics.extend(_markdown_topic_headings(reference["content"]))
    return {
        "triggers": _adjacency_tokens(responsibility["trigger_signals"]),
        "anti_triggers": _adjacency_tokens(
            responsibility["anti_trigger_signals"]
        ),
        "trigger_phrases": _negative_route_phrases(
            responsibility["trigger_signals"]
        ),
        "anti_trigger_phrases": _negative_route_phrases(
            responsibility["anti_trigger_signals"]
        ),
        "outputs": _adjacency_tokens(responsibility["output_contract"]),
        "responsibility": _adjacency_tokens(
            [
                target["skill_id"],
                *responsibility["required_inputs"],
                *responsibility["escalation_signals"],
                *responsibility["boundary_signals"],
            ]
        ),
        "reference_topics": _adjacency_tokens(reference_topics),
    }


def _professional_catalog_adjacency_features(
    targets: list[dict[str, Any]],
    *,
    include_historical_alias: bool = False,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    raw_bases = {
        target["skill_id"]: _professional_raw_adjacency_basis(target)
        for target in targets
    }
    document_frequencies: dict[str, dict[str, int]] = {}
    phrase_fields = {"trigger_phrases", "anti_trigger_phrases"}
    filterable_fields = sorted(set(next(iter(raw_bases.values()))) - phrase_fields)
    for field in filterable_fields:
        counts: dict[str, int] = {}
        for basis in raw_bases.values():
            for token in basis[field]:
                counts[token] = counts.get(token, 0) + 1
        document_frequencies[field] = dict(sorted(counts.items()))
    maximum = max(
        2,
        len(targets)
        * PROFESSIONAL_ADJACENCY_MAX_DOCUMENT_FREQUENCY_PERCENT
        // 100,
    )
    filtered = {
        skill_id: {
            field: {
                token
                for token in tokens
                if document_frequencies[field][token] <= maximum
            }
            for field, tokens in basis.items()
            if field in filterable_fields
        }
        for skill_id, basis in raw_bases.items()
    }
    for skill_id, basis in raw_bases.items():
        # A high-frequency routing token can still encode a material ownership
        # conflict. Keep negative-route comparison independent from the
        # overlap-noise filter so every such conflict remains review-required.
        filtered[skill_id]["negative_route_trigger_phrases"] = basis[
            "trigger_phrases"
        ]
        filtered[skill_id]["negative_route_anti_trigger_phrases"] = basis[
            "anti_trigger_phrases"
        ]
    contract = {
        "catalog_size": len(targets),
        "maximum_document_frequency": maximum,
        "negative_route_conflict_filtering": "phrase-aware-df-bypass",
        "negative_route_contract": {
            "version": PROFESSIONAL_NEGATIVE_ROUTE_MATCH_VERSION,
            "generic_tokens": sorted(PROFESSIONAL_NEGATIVE_ROUTE_GENERIC_TOKENS),
            "minimum_overlap_tokens": (
                PROFESSIONAL_NEGATIVE_ROUTE_MIN_OVERLAP_TOKENS
            ),
            "exact_single_token_phrase_match": True,
        },
    }
    if include_historical_alias:
        contract["document_frequencies_fingerprint"] = (
            _canonical_json_sha256(document_frequencies)
        )
    return filtered, contract


def _professional_negative_route_conflicts(
    source: dict[str, Any],
    candidate: dict[str, Any],
) -> list[str]:
    """Return phrase-aware, rank-independent ownership conflicts."""

    matches: set[str] = set()

    def compare(
        trigger_phrases: tuple[tuple[str, ...], ...],
        anti_trigger_phrases: tuple[tuple[str, ...], ...],
        *,
        prefix: str,
    ) -> None:
        for trigger_phrase in trigger_phrases:
            trigger_tokens = set(trigger_phrase)
            for anti_trigger_phrase in anti_trigger_phrases:
                anti_trigger_tokens = set(anti_trigger_phrase)
                overlap = sorted(trigger_tokens & anti_trigger_tokens)
                exact_single = (
                    len(trigger_tokens) == 1
                    and trigger_tokens == anti_trigger_tokens
                )
                if (
                    len(overlap)
                    < PROFESSIONAL_NEGATIVE_ROUTE_MIN_OVERLAP_TOKENS
                    and not exact_single
                ):
                    continue
                matches.add(prefix + "+".join(overlap))

    compare(
        source["negative_route_trigger_phrases"],
        candidate["negative_route_anti_trigger_phrases"],
        prefix="target-trigger/candidate-anti:",
    )
    compare(
        candidate["negative_route_trigger_phrases"],
        source["negative_route_anti_trigger_phrases"],
        prefix="candidate-trigger/target-anti:",
    )
    return sorted(matches)


def _professional_catalog_ranking(
    skill_id: str,
    *,
    bases: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    source = bases[skill_id]
    ranking: list[dict[str, Any]] = []
    for candidate_id, candidate in bases.items():
        if candidate_id == skill_id:
            continue
        matched_tokens = {
            "trigger-overlap": sorted(
                source["triggers"] & candidate["triggers"]
            ),
            "output-overlap": sorted(source["outputs"] & candidate["outputs"]),
            "responsibility-overlap": sorted(
                source["responsibility"] & candidate["responsibility"]
            ),
            "reference-topic-overlap": sorted(
                source["reference_topics"] & candidate["reference_topics"]
            ),
            "negative-route-conflict": _professional_negative_route_conflicts(
                source,
                candidate,
            ),
        }
        signals = {
            name: {
                "matched_tokens": matched_tokens[name],
                "count": len(matched_tokens[name]),
                "weight": PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS[name],
            }
            for name in sorted(PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS)
        }
        total_score = sum(
            signal["count"] * signal["weight"] for signal in signals.values()
        )
        ranking.append(
            {
                "skill_id": candidate_id,
                "total_score": total_score,
                "signals": signals,
            }
        )
    ranking.sort(key=lambda item: (-item["total_score"], item["skill_id"]))
    return [{**item, "rank": index} for index, item in enumerate(ranking, start=1)]


def _professional_catalog_rankings(
    *, bases: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Build every target-specific ordering in one catalog projection pass."""

    return {
        skill_id: _professional_catalog_ranking(skill_id, bases=bases)
        for skill_id in sorted(bases)
    }


def _professional_adjacency_selection_contract(
    *,
    target_count: int | None = None,
    include_derivation: bool = True,
) -> dict[str, Any]:
    """Return the closed, fingerprinted required-candidate selection contract."""

    if target_count is None:
        target_count = PROFESSIONAL_PACKAGE_COUNT
    derived_maximum = _professional_adjacency_max_required_candidates_total(
        target_count
    )
    contract = {
        "version": PROFESSIONAL_ADJACENCY_SELECTION_VERSION,
        "overall_top_k": PROFESSIONAL_ADJACENCY_TOP_K,
        "per_signal_top_k": PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K,
        "layered_signals": list(PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS),
        "per_signal_order": [
            "signal-count-desc",
            "total-score-desc",
            "skill-id-asc",
        ],
        "require_all_registry_declared": True,
        "require_all_source_declared": True,
        "source_declared_contract": {
            "version": PROFESSIONAL_SOURCE_DECLARED_SELECTION_VERSION,
            "direction": "target-to-candidate",
            "materials": ["root", "indexed-references"],
            "identity": "exact-inline-code-span-skill-id",
            "contexts": list(
                panel_contracts.PROFESSIONAL_SOURCE_DECLARED_CONTEXTS
            ),
            "excluded": list(
                panel_contracts.PROFESSIONAL_SOURCE_DECLARED_EXCLUDED_SURFACES
            ),
            "unknown_or_self": "fail-closed",
        },
        "require_all_negative_route_conflicts": True,
        "maximum_required_candidates_per_target": (
            PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
        ),
        "maximum_required_candidates_total": derived_maximum,
    }
    if include_derivation:
        contract["maximum_required_candidates_total_derivation"] = {
            "rounding": "floor",
            "baseline_target_count": (
                PROFESSIONAL_ADJACENCY_BASELINE_TARGET_COUNT
            ),
            "baseline_maximum_required_candidates_total": (
                PROFESSIONAL_ADJACENCY_BASELINE_MAX_REQUIRED_CANDIDATES_TOTAL
            ),
            "current_target_count": target_count,
            "derived_maximum_required_candidates_total": derived_maximum,
        }
    return contract


def _professional_adjacency_selection_contract_v1(
    *,
    target_count: int,
    include_derivation: bool,
    maximum_required_candidates_per_target: int,
) -> dict[str, Any]:
    """Reconstruct the exact predecessor contract for bound historical packets."""

    contract = _professional_adjacency_selection_contract(
        target_count=target_count,
        include_derivation=include_derivation,
    )
    contract["version"] = "layered-required-candidates-v1"
    contract["require_all_declared"] = contract.pop(
        "require_all_registry_declared"
    )
    contract.pop("require_all_source_declared")
    contract.pop("source_declared_contract")
    contract["maximum_required_candidates_per_target"] = (
        maximum_required_candidates_per_target
    )
    return contract


def _professional_completeness_panel_contract(
    *,
    target_count: int | None = None,
    include_selection_derivation: bool = True,
) -> dict[str, Any]:
    """Return the closed schema-2 reviewer-pool and decision contract."""

    if target_count is None:
        target_count = PROFESSIONAL_PACKAGE_COUNT
    return {
        "decision_method": PROFESSIONAL_COMPLETENESS_DECISION_METHOD,
        "per_target_panel_size": PANEL_SIZE,
        "abstentions_allowed": False,
        "minimum_winning_votes": panel_contracts.PROFESSIONAL_MINIMUM_WINNING_VOTES,
        "independent_ballots": True,
        "required_target_count": target_count,
        "criteria_required_per_target": sorted(
            PROFESSIONAL_COMPLETENESS_CRITERIA
        ),
        "reviewer_pool_contract": {
            "minimum_reviewer_count": PANEL_SIZE,
            "assignments_non_empty": True,
            "unique_voter_id_per_round": True,
            "unique_agent_id_per_round": True,
            "fixed_pool_size": False,
        },
        "qualification_contract": {
            "required_domain_experts_per_target": (
                panel_contracts.PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS
            ),
            "required_architecture_experts_per_target": (
                panel_contracts.PROFESSIONAL_REQUIRED_ARCHITECTURE_EXPERTS
            ),
            "architecture_expertise_tag": (
                PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
            ),
        },
        "domain_critical_contract": {
            "criteria": sorted(PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA),
            "qualified_domain_defect_disposition": (
                PROFESSIONAL_UNRESOLVED_DISPOSITION
            ),
            "arbitration_supported": False,
        },
        "ordinary_criterion_contract": {
            "criteria": sorted(PROFESSIONAL_ORDINARY_CRITERIA),
            "defect_votes_required": (
                panel_contracts.PROFESSIONAL_MINIMUM_WINNING_VOTES
            ),
            "correction_disposition": "requires-professional-correction",
            "overall_ballot_majority_usage": "audit-only",
        },
        "evidence_contract": {
            "criterion_source_anchors_required": True,
            "minimum_failure_modes_per_target": (
                panel_contracts.PROFESSIONAL_MINIMUM_EXAMINED_ITEMS
            ),
            "minimum_omission_candidates_per_target": (
                panel_contracts.PROFESSIONAL_MINIMUM_EXAMINED_ITEMS
            ),
            "adjacency_candidate_coverage_required": True,
            "proof_limits_required": True,
        },
        "adjacency_contract": {
            "algorithm": PROFESSIONAL_ADJACENCY_ALGORITHM,
            "required_candidate_selection": (
                _professional_adjacency_selection_contract(
                    target_count=target_count,
                    include_derivation=include_selection_derivation,
                )
            ),
            "full_catalog_count": target_count,
            "full_ranking_embedded": True,
            "maximum_document_frequency_percent": (
                PROFESSIONAL_ADJACENCY_MAX_DOCUMENT_FREQUENCY_PERCENT
            ),
            "reviewer_added_candidates": {
                "allowed": True,
                "source": "full_catalog_ranking",
                "discovery_reason_required": True,
            },
        },
    }


def _professional_required_adjacency_candidates(
    ranking: list[dict[str, Any]],
    *,
    registry_declared_skills: list[str],
    source_declared_skills: list[str],
    overall_top_k: int | None = None,
    per_signal_top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Select a bounded layered review surface without hiding route conflicts."""

    if overall_top_k is None:
        overall_top_k = PROFESSIONAL_ADJACENCY_TOP_K
    if per_signal_top_k is None:
        per_signal_top_k = PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K
    if (
        type(overall_top_k) is not int
        or overall_top_k < 0
        or type(per_signal_top_k) is not int
        or per_signal_top_k < 0
    ):
        raise PanelReviewError(
            "professional adjacency selection thresholds are invalid"
        )

    ranking_by_id = {row["skill_id"]: row for row in ranking}
    reasons: dict[str, set[str]] = {}

    def require(skill_id: str, reason: str) -> None:
        if skill_id not in ranking_by_id:
            raise PanelReviewError(
                f"required adjacency candidate is absent from catalog ranking: {skill_id}"
            )
        reasons.setdefault(skill_id, set()).add(reason)

    for skill_id in registry_declared_skills:
        require(skill_id, "registry-declared")
    for skill_id in source_declared_skills:
        require(skill_id, "source-declared")
    for row in ranking:
        if row["rank"] <= overall_top_k:
            require(row["skill_id"], "overall-top-k")
        if row["signals"]["negative-route-conflict"]["count"] > 0:
            require(row["skill_id"], "negative-route-conflict")
    for signal_name in PROFESSIONAL_ADJACENCY_LAYERED_SIGNALS:
        positive = [
            row
            for row in ranking
            if row["signals"][signal_name]["count"] > 0
        ]
        positive.sort(
            key=lambda row: (
                -row["signals"][signal_name]["count"],
                -row["total_score"],
                row["skill_id"],
            )
        )
        for row in positive[:per_signal_top_k]:
            require(row["skill_id"], f"signal-top-k:{signal_name}")

    declared = set(registry_declared_skills) | set(source_declared_skills)
    return [
        {
            **ranking_by_id[skill_id],
            "declared": skill_id in declared,
            "selection_reasons": sorted(reasons[skill_id]),
        }
        for skill_id in sorted(reasons)
    ]


def _enforce_professional_adjacency_candidate_budget(
    targets: list[dict[str, Any]],
) -> None:
    counts = [
        len(target["routing_adjacency"]["required_candidates"])
        for target in targets
    ]
    if counts and max(counts) > (
        PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
    ):
        raise PanelReviewError(
            "professional adjacency required-candidate per-target budget exceeded"
        )
    if sum(counts) > PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_TOTAL:
        raise PanelReviewError(
            "professional adjacency required-candidate catalog budget exceeded"
        )


def _professional_package_targets(
    *,
    root: Path = ROOT,
    historical_schema2: bool = False,
) -> list[dict[str, Any]]:
    """Build the canonical current-package completeness review surface."""

    registry_rows: list[tuple[str, str, dict[str, Any]]] = []
    seen_names: set[str] = set()
    for layer, relative, collection_key in REGISTRY_SOURCES:
        registry_path = root / relative
        try:
            registry = load_yaml_file(registry_path)
        except (OSError, ValidationProblem) as exc:
            raise PanelReviewError(f"cannot load completeness registry: {relative}") from exc
        rows = registry.get(collection_key) if isinstance(registry, dict) else None
        if not isinstance(rows, list):
            raise PanelReviewError(f"{relative}: {collection_key} must be an array")
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise PanelReviewError(f"{relative}: {collection_key}[{index}] is invalid")
            name = _non_blank(
                row.get("name"), label=f"{relative}: {collection_key}[{index}].name"
            )
            if name in seen_names:
                raise PanelReviewError(f"duplicate professional package name: {name}")
            seen_names.add(name)
            registry_rows.append((layer, relative, row))
    if len(registry_rows) != PROFESSIONAL_PACKAGE_COUNT:
        raise PanelReviewError(
            "professional completeness panel requires exactly "
            f"{PROFESSIONAL_PACKAGE_COUNT} non-Control Skill packages; "
            f"found {len(registry_rows)}"
        )

    direct_relationships: dict[str, set[str]] = {
        str(row["name"]): set() for _layer, _relative, row in registry_rows
    }
    for layer, _relative, row in registry_rows:
        name = str(row["name"])
        for field in ("layer3_candidates", "used_by"):
            values = row.get(field, [])
            for adjacent in _string_list(values, label=f"{name}.{field}"):
                if adjacent not in seen_names:
                    raise PanelReviewError(
                        f"{name}.{field} names unknown professional package: {adjacent}"
                    )
                direct_relationships[name].add(adjacent)
                direct_relationships[adjacent].add(name)

    targets: list[dict[str, Any]] = []
    for layer, registry_relative, row in registry_rows:
        name = str(row["name"])
        skill_directory = _non_blank(row.get("path"), label=f"{name}.path")
        root_record = _review_material_record(
            root / skill_directory / "SKILL.md",
            root=root,
            label=f"{name} root Skill",
        )
        try:
            reference_authority = reference_contracts(
                row.get("reference_index", []),
                f"{registry_relative}:{name}.reference_index",
                owner=name,
            )
        except ValidationProblem as exc:
            raise PanelReviewError(
                f"{name}.reference_index is not valid Reference authority"
            ) from exc
        references: list[dict[str, Any]] = []
        reference_paths: set[str] = set()
        for index, reference in enumerate(reference_authority):
            reference_relative = _non_blank(
                reference.get("path"), label=f"{name}.reference_index[{index}].path"
            )
            record = _review_material_record(
                root / skill_directory / reference_relative,
                root=root,
                label=f"{name} indexed Reference",
            )
            if record["path"] in reference_paths:
                raise PanelReviewError(f"{name} has a duplicate indexed Reference")
            reference_paths.add(record["path"])
            references.append(record)
        references.sort(key=lambda item: item["path"])

        responsibility_contract = {
            "role_support": _string_list(
                row.get("role_support", []), label=f"{name}.role_support", allow_empty=False
            ),
            "trigger_signals": _string_list(
                row.get("trigger_signals", []),
                label=f"{name}.trigger_signals",
                allow_empty=False,
            ),
            "anti_trigger_signals": _string_list(
                row.get("anti_trigger_signals", []),
                label=f"{name}.anti_trigger_signals",
                allow_empty=False,
            ),
            "required_inputs": _string_list(
                row.get("required_inputs", []),
                label=f"{name}.required_inputs",
                allow_empty=False,
            ),
            "output_contract": _string_list(
                row.get("output_contract", []),
                label=f"{name}.output_contract",
                allow_empty=False,
            ),
            "escalation_signals": _string_list(
                row.get("escalation_signals", []),
                label=f"{name}.escalation_signals",
                allow_empty=False,
            ),
            "layer3_candidates": _string_list(
                row.get("layer3_candidates", []), label=f"{name}.layer3_candidates"
            ),
            "used_by": _string_list(row.get("used_by", []), label=f"{name}.used_by"),
            "boundary_signals": _string_list(
                row.get("boundary_signals", []), label=f"{name}.boundary_signals"
            ),
            "group": row.get("group"),
            "content_class": row.get("content_class"),
            "delivery_scope": row.get("delivery_scope"),
            "task_routable": row.get("task_routable"),
        }
        required_expertise_tags = _expertise_tags(
            row.get("required_expertise_tags"),
            label=f"{name}.required_expertise_tags",
            allow_architecture=False,
        )
        target: dict[str, Any] = {
            "skill_id": name,
            "layer": layer,
            "required_expertise_tags": required_expertise_tags,
            "root": root_record,
            "indexed_references": references,
            "registry": {
                "path": registry_relative,
                "responsibility_contract": responsibility_contract,
            },
        }
        if historical_schema2:
            target["registry"]["entry_fingerprint"] = (
                _canonical_json_sha256(row)
            )
        else:
            registry_authority = copy.deepcopy(row)
            registry_authority["reference_index"] = copy.deepcopy(
                reference_authority
            )
            target["registry_authority"] = registry_authority
            target["reference_authority"] = copy.deepcopy(
                reference_authority
            )
            try:
                professional_carry.professional_registry_authority_binding(
                    target
                )
            except professional_carry.ProfessionalCarryForwardError as exc:
                raise PanelReviewError(
                    f"{name} Registry/Reference authority does not cover its "
                    "indexed material exactly once"
                ) from exc
        targets.append(target)
    targets.sort(key=lambda item: item["skill_id"])
    adjacency_bases, document_frequency_filter = (
        _professional_catalog_adjacency_features(
            targets,
            include_historical_alias=historical_schema2,
        )
    )
    catalog_rankings = _professional_catalog_rankings(bases=adjacency_bases)
    for target in targets:
        name = target["skill_id"]
        registry_declared_skills = sorted(direct_relationships[name])
        source_declared_skills = _professional_source_declared_skill_ids(
            target,
            known_skill_ids=seen_names,
        )
        ranking = catalog_rankings[name]
        required_candidates = _professional_required_adjacency_candidates(
            ranking,
            registry_declared_skills=registry_declared_skills,
            source_declared_skills=source_declared_skills,
        )
        target["routing_adjacency"] = {
            "algorithm": PROFESSIONAL_ADJACENCY_ALGORITHM,
            "document_frequency_filter": document_frequency_filter,
            "declared_skills": sorted(
                set(registry_declared_skills) | set(source_declared_skills)
            ),
            "registry_declared_skills": registry_declared_skills,
            "source_declared_skills": source_declared_skills,
            "required_candidate_selection": (
                _professional_adjacency_selection_contract()
            ),
            "required_candidates": required_candidates,
            "full_catalog_count": len(ranking),
            "full_catalog_ranking": ranking,
        }
        if historical_schema2:
            target["routing_adjacency"]["required_candidates_fingerprint"] = (
                _canonical_json_sha256(required_candidates)
            )
            target["routing_adjacency"]["full_catalog_ranking_fingerprint"] = (
                _canonical_json_sha256(ranking)
            )
            target["package_fingerprint"] = _canonical_json_sha256(target)
    _enforce_professional_adjacency_candidate_budget(targets)
    return targets


def prepare_professional_completeness_packet(
    *,
    review_id: str,
    created_on: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Build the immutable professional-completeness reviewer-pool packet."""

    _non_blank(review_id, label="review_id")
    _iso_date(created_on, label="created_on")
    targets = _professional_package_targets(
        root=root,
        historical_schema2=True,
    )
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "review_id": review_id,
        "created_on": created_on,
        "source_fingerprints": {
            "professional_packages": _canonical_json_sha256(targets),
        },
        "panel_contract": _professional_completeness_panel_contract(),
        "rubric": {
            "accept": (
                "Accept only when every criterion is satisfied for the complete Skill "
                "package and its responsibility boundary."
            ),
            "correct": (
                "Require professional correction when any criterion exposes an error, "
                "material omission, responsibility gap, or unverifiable output."
            ),
            "criteria": dict(sorted(PROFESSIONAL_COMPLETENESS_CRITERIA.items())),
            "reason_codes": {
                decision: sorted(PROFESSIONAL_REASON_CODES[decision])
                for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
            },
        },
        "professional_targets": targets,
        "limitations": [
            "The packet binds complete UTF-8 Skill and indexed Reference content plus registry and independent catalog-adjacency evidence.",
            "Each reviewer receives a non-empty assigned Skill subset, binds every assigned criterion assertion to substantive source lines, and must not read another ballot.",
            "Every Skill is decided by exactly two qualified domain reviewers and one skill-reference-architecture reviewer drawn from the round-wide reviewer pool.",
            "Any qualified domain-reviewer defect on a domain-critical criterion remains an unresolved professional disagreement; schema 2 supports no arbitration or override.",
            "Static professional review does not prove real-host or production behavior.",
        ],
    }


def _semantic_hash(value: object) -> str:
    """Return one canonical evidence hash for a semantic packet projection."""

    return _canonical_json_sha256(value)


def _semantic_sha(value: object, *, label: str) -> str:
    if isinstance(value, dict):
        value = value.get("value")
    return _lowercase_sha256(value, label=label)


def _semantic_audit_sections(
    audit: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    root_content = audit.get("root_content")
    reference_content = audit.get("reference_content")
    if not isinstance(root_content, dict) or not isinstance(reference_content, dict):
        raise PanelReviewError(
            "semantic disposition packet requires Root and Reference audit content"
        )
    root_semantic = root_content.get("semantic_advisories")
    reference_semantic = reference_content.get("semantic_advisories")
    if not isinstance(root_semantic, dict) or not isinstance(reference_semantic, dict):
        raise PanelReviewError(
            "semantic disposition packet requires Root and Reference semantic advisories"
        )
    return root_semantic, reference_semantic


def _semantic_candidate_evidence(candidate: dict[str, Any]) -> dict[str, Any]:
    """Remove prior governance results while retaining complete detector evidence."""

    excluded = {
        "disposition",
        "disposition_record",
        "governance_status",
        "resolved",
        "unresolved",
    }
    return {
        key: copy.deepcopy(value)
        for key, value in candidate.items()
        if key not in excluded
    }


def _semantic_candidate_review_evidence(
    *, axis: str, candidate: dict[str, Any]
) -> dict[str, Any]:
    """Project one candidate onto evidence that a disposition cannot change."""

    evidence = _semantic_candidate_evidence(candidate)
    if axis == "reference":
        # Reference priority is selected by the disposition entry. It is not
        # detector evidence and can legitimately change when a panel decision
        # is applied without changing the reviewed candidate.
        evidence.pop("priority", None)
    return evidence


def _semantic_candidate_current_binding(
    *, axis: str, candidate: dict[str, Any]
) -> dict[str, Any]:
    """Return only semantic identity and local evidence used for currentness."""

    identity_fields = (
        "candidate_id",
        "finding",
        "path",
        "owner",
        "skill_owner",
        "source_selector",
    )
    identity = {
        field: copy.deepcopy(candidate.get(field)) for field in identity_fields
    }
    evidence = {"fingerprint": candidate.get("fingerprint")}
    if axis == "root":
        identity["document_part"] = candidate.get("document_part")
        evidence.update(
            {
                "occurrence_fingerprint": candidate.get("occurrence_fingerprint"),
                "context_fingerprint": candidate.get("context_fingerprint"),
            }
        )
    else:
        evidence.update(
            {
                "evidence_fingerprint": candidate.get("evidence_fingerprint"),
                "content_fingerprint": candidate.get("content_fingerprint"),
            }
        )
        if candidate.get("path") == "group":
            evidence["group_members"] = sorted(
                {
                    (occurrence.get("path"), occurrence.get("owner"))
                    for occurrence in candidate.get("occurrences", [])
                    if isinstance(occurrence, dict)
                }
            )
    return {"stable_identity": identity, "current_evidence": evidence}


def _semantic_entry_mismatches(
    *,
    axis: str,
    candidate: dict[str, Any],
    entry: dict[str, Any] | None,
) -> list[str]:
    """Return every stable field that prevents an exact disposition carry-forward."""

    if entry is None:
        return ["prior-entry-missing"]
    fields = ["candidate_id", "finding", "path", "source_selector", "skill_owner"]
    if axis == "root":
        fields.extend(["document_part", "priority"])
    mismatches = [field for field in fields if entry.get(field) != candidate.get(field)]
    if entry.get("skill_owner") != candidate.get("owner"):
        mismatches.append("owner")
    evidence = entry.get("evidence")
    if not isinstance(evidence, dict):
        return sorted([*mismatches, "evidence"])
    if axis == "root":
        evidence_fields = (
            ("occurrence_fingerprint", "occurrence_fingerprint"),
            ("context_fingerprint", "context_fingerprint"),
        )
    else:
        # Reference priority is an expert disposition choice. The canonical
        # collector deliberately does not compare it with a detector default.
        evidence_fields = (
            ("fingerprint", "evidence_fingerprint"),
            ("content_fingerprint", "content_fingerprint"),
        )
    mismatches.extend(
        f"evidence.{entry_field}"
        for entry_field, candidate_field in evidence_fields
        if evidence.get(entry_field) != candidate.get(candidate_field)
    )
    try:
        expected_record_fingerprint = (
            panel_contracts.semantic_disposition_record_fingerprint(axis, entry)
        )
    except ValueError:
        expected_record_fingerprint = None
    if entry.get("record_fingerprint") != expected_record_fingerprint:
        mismatches.append("record_fingerprint")
    return sorted(set(mismatches))


def _semantic_eligible_candidates(
    *, axis: str, semantic: dict[str, Any]
) -> list[dict[str, Any]]:
    """Select review-visible candidates, including configured detector drift."""

    candidates = semantic.get("candidates")
    contract = semantic.get("disposition_contract")
    entries = contract.get("entries") if isinstance(contract, dict) else None
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, dict) for candidate in candidates
    ):
        raise PanelReviewError(f"semantic audit {axis} candidates must be an array")
    if not isinstance(entries, list) or not all(
        isinstance(entry, dict) for entry in entries
    ):
        raise PanelReviewError(
            f"semantic audit {axis} disposition entries must be an array"
        )
    configured_ids = {
        str(entry.get("candidate_id"))
        for entry in entries
        if isinstance(entry.get("candidate_id"), str)
    }
    return [
        candidate
        for candidate in candidates
        if (
            axis == "root"
            or candidate.get("detector_status") == "candidate"
            or str(candidate.get("candidate_id")) in configured_ids
        )
    ]


def _semantic_axis_diff(
    *,
    axis: str,
    semantic: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates = semantic.get("candidates")
    contract = semantic.get("disposition_contract")
    entries = contract.get("entries") if isinstance(contract, dict) else None
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, dict) for candidate in candidates
    ):
        raise PanelReviewError(f"semantic audit {axis} candidates must be an array")
    if not isinstance(entries, list) or not all(
        isinstance(entry, dict) for entry in entries
    ):
        raise PanelReviewError(
            f"semantic audit {axis} disposition entries must be an array"
        )
    eligible = _semantic_eligible_candidates(axis=axis, semantic=semantic)
    candidate_ids = [candidate.get("candidate_id") for candidate in eligible]
    entry_ids = [entry.get("candidate_id") for entry in entries]
    for label, values in (("candidate", candidate_ids), ("entry", entry_ids)):
        if not all(
            isinstance(value, str)
            and len(value) == 64
            and not set(value) - set("0123456789abcdef")
            for value in values
        ):
            raise PanelReviewError(
                f"semantic audit {axis} {label} IDs must be lowercase sha256"
            )
        if len(values) != len(set(values)):
            raise PanelReviewError(f"semantic audit {axis} has duplicate {label} IDs")
    entries_by_id = {str(entry["candidate_id"]): entry for entry in entries}
    exact_ids: list[str] = []
    stale_evidence_ids: list[str] = []
    targets: list[dict[str, Any]] = []
    for candidate in sorted(eligible, key=lambda item: str(item["candidate_id"])):
        candidate_id = str(candidate["candidate_id"])
        mismatches = _semantic_entry_mismatches(
            axis=axis,
            candidate=candidate,
            entry=entries_by_id.get(candidate_id),
        )
        if not mismatches:
            exact_ids.append(candidate_id)
            continue
        if candidate_id in entries_by_id:
            stale_evidence_ids.append(candidate_id)
        evidence = _semantic_candidate_review_evidence(
            axis=axis, candidate=candidate
        )
        targets.append(
            {
                "target_id": f"{axis}:{candidate_id}",
                "axis": axis,
                "carry_forward_mismatches": mismatches,
                "candidate_binding_fingerprint": _semantic_hash(
                    {
                        "review_evidence": evidence,
                        "local_semantic_context": (
                            _semantic_candidate_current_binding(
                                axis=axis,
                                candidate=candidate,
                            )
                        ),
                    }
                ),
                "candidate": evidence,
            }
        )
    current_ids = set(str(value) for value in candidate_ids)
    stale_old_ids = sorted(str(value) for value in entry_ids if value not in current_ids)
    target_ids = [target["candidate"]["candidate_id"] for target in targets]
    provenance = {
        "raw_candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible),
        "detector_downgraded_count": len(candidates) - len(eligible),
        "configured_entry_count": len(entries),
        "exact_carry_forward_count": len(exact_ids),
        "exact_carry_forward_candidate_ids": sorted(exact_ids),
        "review_target_count": len(targets),
        "review_target_candidate_ids": target_ids,
        "same_id_stale_evidence_candidate_ids": sorted(stale_evidence_ids),
        "stale_old_count": len(stale_old_ids),
        "stale_old_candidate_ids": stale_old_ids,
    }
    return provenance, targets


def _semantic_source_fingerprints(
    audit: dict[str, Any],
    *,
    root_semantic: dict[str, Any],
    reference_semantic: dict[str, Any],
) -> dict[str, str]:
    detector_contracts = {
        "root": root_semantic.get("detector_contract"),
        "reference": reference_semantic.get("detector_contract"),
    }
    expected_versions = {
        "root": "root-semantic-detector-contract-v1",
        "reference": "reference-semantic-detector-contract-v1",
    }
    for axis, contract in detector_contracts.items():
        if not isinstance(contract, dict) or set(contract) != {
            "contract_version",
            "algorithm",
            "value",
        }:
            raise PanelReviewError(
                f"semantic disposition packet requires closed {axis} detector evidence"
            )
        if (
            contract.get("contract_version") != expected_versions[axis]
            or contract.get("algorithm") != "sha256-canonical-json-v1"
        ):
            raise PanelReviewError(
                f"semantic disposition packet {axis} detector contract is invalid"
            )
    root_candidates = root_semantic.get("candidates")
    reference_candidates = reference_semantic.get("candidates")
    if not isinstance(root_candidates, list) or not isinstance(
        reference_candidates, list
    ):
        raise PanelReviewError("semantic disposition candidates are unavailable")
    manifests: dict[str, list[dict[str, Any]]] = {}
    for axis, candidates, semantic in (
        ("root", root_candidates, root_semantic),
        ("reference", reference_candidates, reference_semantic),
    ):
        eligible = _semantic_eligible_candidates(axis=axis, semantic=semantic)
        rows = []
        for candidate in eligible:
            candidate_id = _lowercase_sha256(
                candidate.get("candidate_id"),
                label=f"semantic {axis} candidate_id",
            )
            rows.append(
                {
                    "target_id": f"{axis}:{candidate_id}",
                    "current_binding": _semantic_candidate_current_binding(
                        axis=axis, candidate=candidate
                    ),
                }
            )
        target_ids = [row["target_id"] for row in rows]
        if len(target_ids) != len(set(target_ids)):
            raise PanelReviewError(
                f"semantic audit {axis} candidate IDs are duplicated"
            )
        manifests[axis] = sorted(rows, key=lambda row: row["target_id"])
    result = {
        "root_candidate_manifest": _semantic_hash(manifests["root"]),
        "root_detector_contract": _semantic_sha(
            detector_contracts["root"].get("value"),
            label="root detector fingerprint",
        ),
        "reference_candidate_manifest": _semantic_hash(
            manifests["reference"]
        ),
        "reference_detector_contract": _semantic_sha(
            detector_contracts["reference"].get("value"),
            label="reference detector fingerprint",
        ),
    }
    return dict(sorted(result.items()))


def _semantic_source_fingerprint_selector_mode(
    *,
    selector_fingerprints: object,
    current_fingerprints: object,
    review_id: str,
    review_contract_fingerprint: str,
    target_count: int,
    axis_counts: dict[str, int],
) -> str | None:
    """Prefer direct v1 evidence; otherwise admit one exact source-only bridge."""

    expected_keys = set(
        panel_contracts.SEMANTIC_DISPOSITION_SOURCE_FINGERPRINT_KEYS
    )
    detector_keys = {
        "root_detector_contract", "reference_detector_contract"
    }
    if (
        isinstance(selector_fingerprints, dict)
        and set(selector_fingerprints) == detector_keys
        and isinstance(current_fingerprints, dict)
        and set(current_fingerprints) == expected_keys
        and all(
            selector_fingerprints[key] == current_fingerprints[key]
            for key in detector_keys
        )
    ):
        return "compact-v2"
    if (
        not isinstance(selector_fingerprints, dict)
        or set(selector_fingerprints) != expected_keys
        or not isinstance(current_fingerprints, dict)
        or set(current_fingerprints) != expected_keys
    ):
        return None
    if selector_fingerprints == current_fingerprints:
        return "direct-v1"
    rows = panel_contracts.semantic_detector_compatibility_rows()
    if len(rows) != 1:
        raise PanelReviewError(
            "semantic detector compatibility contract must contain exactly one row"
        )
    row = rows[0]
    if (
        review_id == row.get("review_id")
        and review_contract_fingerprint
        == row.get("review_contract_fingerprint")
        and target_count == row.get("target_count")
        and axis_counts == row.get("axis_counts")
        and selector_fingerprints == row.get("legacy_source_fingerprints")
        and current_fingerprints == row.get("current_source_fingerprints")
    ):
        return "compatibility"
    return None


def _semantic_panel_contract(
    *, root_target_count: int, reference_target_count: int
) -> dict[str, Any]:
    """Return the dynamic panel counts plus the closed Semantic contract."""

    target_count = root_target_count + reference_target_count
    return {
        "decision_method": DECISION_METHOD,
        "required_voters": PANEL_SIZE,
        "abstentions_allowed": False,
        "minimum_winning_votes": 2,
        "independent_ballots": True,
        "required_target_count": target_count,
        "required_axis_target_counts": {
            "root": root_target_count,
            "reference": reference_target_count,
        },
        "allowed_dispositions": sorted(SEMANTIC_DISPOSITIONS),
        "semantic_contract": (
            panel_contracts.semantic_disposition_contract_projection()
        ),
    }


def prepare_semantic_disposition_packet(
    *,
    audit: dict[str, Any],
    review_id: str,
    created_on: str,
) -> dict[str, Any]:
    """Select only current candidates that cannot be carried forward exactly."""

    _non_blank(review_id, label="review_id")
    _iso_date(created_on, label="created_on")
    root_semantic, reference_semantic = _semantic_audit_sections(audit)
    root_provenance, root_targets = _semantic_axis_diff(
        axis="root", semantic=root_semantic
    )
    reference_provenance, reference_targets = _semantic_axis_diff(
        axis="reference", semantic=reference_semantic
    )
    targets = sorted(
        [*root_targets, *reference_targets], key=lambda item: item["target_id"]
    )
    return {
        "schema_version": SEMANTIC_DISPOSITION_SCHEMA_VERSION,
        "kind": SEMANTIC_DISPOSITION_PACKET_KIND,
        "review_id": review_id,
        "created_on": created_on,
        "source_fingerprints": _semantic_source_fingerprints(
            audit,
            root_semantic=root_semantic,
            reference_semantic=reference_semantic,
        ),
        "panel_contract": _semantic_panel_contract(
            root_target_count=len(root_targets),
            reference_target_count=len(reference_targets),
        ),
        "rubric": {
            "exact_carry_forward": (
                "Do not vote when the current stable candidate identity and all "
                "axis-specific occurrence, context, membership, and content evidence "
                "equal the prior disposition entry."
            ),
            "rewrite": "Select rewrite when the current source rule must change.",
            "valid_contextual_rule": (
                "Select valid-contextual-rule only when current authority and conditions "
                "make the detected rule professionally valid."
            ),
            "false_positive": (
                "Select false-positive only when the detector family does not apply to "
                "the current complete context."
            ),
            "time_bounded_exception": (
                "Select time-bounded-exception only with an accountable owner, current "
                "mitigation, and future expiry."
            ),
        },
        "candidate_provenance": {
            "root": root_provenance,
            "reference": reference_provenance,
        },
        "semantic_targets": targets,
        "limitations": [
            "This panel is authoring lifecycle evidence for semantic dispositions only.",
            "It cannot satisfy or replace readability or professional-completeness formal attestations.",
            "A majority rewrite remains a decision record and does not create a single-source-of-truth disposition entry.",
            "Static semantic review does not prove real-host or production behavior.",
        ],
    }


def _semantic_audit_for_axis_rereview(
    audit: dict[str, Any], axes: list[str]
) -> dict[str, Any]:
    """Return a review-only view with selected-axis carry proofs invalidated.

    This reuses the ordinary semantic packet contract after a detector change:
    current candidates and configured stable IDs remain unchanged, while exact
    prior dispositions on the affected axis become explicit review targets
    again. The canonical audit and its single-source-of-truth entries are never
    modified.
    """

    selected = sorted(set(axes))
    if any(axis not in SEMANTIC_AXES for axis in selected):
        raise PanelReviewError("semantic re-review axis is invalid")
    result = copy.deepcopy(audit)
    for axis in selected:
        content = result.get(f"{axis}_content")
        semantic = (
            content.get("semantic_advisories")
            if isinstance(content, dict)
            else None
        )
        contract = (
            semantic.get("disposition_contract")
            if isinstance(semantic, dict)
            else None
        )
        if not isinstance(contract, dict) or not isinstance(
            contract.get("entries"), list
        ):
            raise PanelReviewError(
                f"semantic re-review requires {axis} disposition entries"
            )
        for entry in contract["entries"]:
            if not isinstance(entry, dict):
                raise PanelReviewError(
                    f"semantic re-review requires valid {axis} disposition entries"
                )
            entry["record_fingerprint"] = None
    return result


def _semantic_forced_prepare_packet(
    *,
    audit: dict[str, Any],
    axes: list[str],
    review_id: str,
    created_on: str,
) -> dict[str, Any]:
    """Build one full-fresh Semantic packet without mutating its audit authority."""

    if sorted(axes) != sorted(SEMANTIC_AXES) or len(axes) != len(
        SEMANTIC_AXES
    ):
        raise PanelReviewError(
            "Semantic prepare must force both root and reference exactly once"
        )
    review_view = _semantic_audit_for_axis_rereview(audit, axes)
    packet = prepare_semantic_disposition_packet(
        audit=review_view,
        review_id=review_id,
        created_on=created_on,
    )
    packet["limitations"].append(
        "Full-fresh review was forced for semantic axes: root, reference."
    )
    # The packet candidates and detector bindings must remain current to the
    # untouched clean-HEAD audit. Only its in-memory disposition entries were
    # withheld to select all targets for review.
    validate_semantic_packet_current(packet, audit)
    return packet


def prepare_semantic_ballot_template(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    agent_id: str,
    role: str,
    expertise: list[str],
    created_on: str,
) -> dict[str, Any]:
    """Create a deliberately unfilled semantic ballot with complete coverage rows."""

    _validate_semantic_disposition_packet(packet)
    _lowercase_sha256(packet_sha256, label="packet_sha256")
    return {
        "schema_version": SEMANTIC_DISPOSITION_SCHEMA_VERSION,
        "kind": SEMANTIC_DISPOSITION_BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": _iso_date(created_on, label="created_on"),
        "packet_sha256": packet_sha256,
        "source_fingerprints": packet["source_fingerprints"],
        "voter": {
            "voter_id": _non_blank(voter_id, label="voter_id"),
            "agent_id": _non_blank(agent_id, label="agent_id"),
            "role": _non_blank(role, label="role"),
            "expertise": _string_list(
                expertise, label="expertise", allow_empty=False
            ),
            "independent_review": True,
        },
        "semantic_votes": [
            {
                "target_id": target["target_id"],
                "axis": target["axis"],
                "candidate_id": target["candidate"]["candidate_id"],
                "disposition": None,
                "rationale": "",
                "authority_or_condition": "",
                "decision_owner": "",
                "mitigation": "",
                "review_after": None,
            }
            for target in packet["semantic_targets"]
        ],
        "limitations": [
            "Unfilled template: every decision and rationale must be completed independently before validation."
        ],
    }


def prepare_readability_ballot_template(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    agent_id: str,
    role: str,
    expertise: list[str],
    created_on: str,
) -> dict[str, Any]:
    """Create an unfilled readability ballot with every packet target."""

    validate_packet(packet)
    _lowercase_sha256(packet_sha256, label="packet_sha256")
    ballot = {
        "schema_version": packet["schema_version"],
        "kind": BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": _iso_date(created_on, label="created_on"),
        "packet_sha256": packet_sha256,
        "source_fingerprints": packet["source_fingerprints"],
        "voter": {
            "voter_id": _non_blank(voter_id, label="voter_id"),
            "agent_id": _non_blank(agent_id, label="agent_id"),
            "role": _non_blank(role, label="role"),
            "expertise": _string_list(
                expertise, label="expertise", allow_empty=False
            ),
            "independent_review": True,
        },
        "content_votes": [
            {
                "path": target["path"],
                "classification": target["classification"],
                "decision": None,
                "reason_code": None,
                "rationale": "",
            }
            for target in packet["content_targets"]
        ],
        "readability_votes": [
            (
                {
                    "document_id": target["document_id"],
                    "highest_band": target["highest_band"],
                    "finding_reviews": [
                        {
                            "finding_id": finding["finding_id"],
                            "sentence_fingerprint": finding[
                                "sentence_fingerprint"
                            ],
                            "decision": None,
                            "reason_code": None,
                            "rationale": "",
                        }
                        for finding in target["findings"]
                    ],
                }
                if packet["schema_version"] == READABILITY_SCHEMA_VERSION
                else {
                    "document_id": target["document_id"],
                    "highest_band": target["highest_band"],
                    "decision": None,
                    "reason_code": None,
                    "rationale": "",
                }
            )
            for target in packet["readability_targets"]
        ],
        "limitations": [
            "Unfilled template: every decision, reason code, and rationale must be completed independently before validation."
        ],
    }
    if packet["schema_version"] == READABILITY_SCHEMA_VERSION:
        ballot["actionability_votes"] = [
            {
                "target_id": target["target_id"],
                "decision": None,
                "reason_code": None,
                "evidence": [],
                "rationale": "",
            }
            for target in packet["actionability_targets"]
        ]
    return ballot


def _professional_assigned_targets(
    packet: dict[str, Any], skill_ids: list[str] | None
) -> list[dict[str, Any]]:
    """Resolve one non-empty, unique schema-2 assignment deterministically."""

    if not isinstance(skill_ids, list) or not skill_ids:
        raise PanelReviewError(
            "professional completeness schema-2 ballot requires a non-empty Skill assignment"
        )
    normalized: list[str] = []
    for index, skill_id in enumerate(skill_ids):
        normalized.append(
            _non_blank(skill_id, label=f"assigned_skill_ids[{index}]")
        )
    if len(normalized) != len(set(normalized)):
        raise PanelReviewError(
            "professional completeness Skill assignment must be unique"
        )
    targets = {
        target["skill_id"]: target for target in packet["professional_targets"]
    }
    unknown = sorted(set(normalized) - set(targets))
    if unknown:
        raise PanelReviewError(
            "professional completeness Skill assignment names unknown packages: "
            + ", ".join(unknown)
        )
    return [targets[skill_id] for skill_id in sorted(normalized)]


def prepare_professional_completeness_ballot_template(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    agent_id: str,
    role: str,
    expertise: list[str],
    expertise_tags: list[str] | None,
    skill_ids: list[str] | None,
    created_on: str,
    capsule_path: Path | None = None,
    validation_root: Path = ROOT,
) -> dict[str, Any]:
    """Create an unfilled completeness ballot for one assigned Skill subset."""

    if (
        packet.get("schema_version")
        == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    ):
        if capsule_path is None:
            raise PanelReviewError(
                "professional completeness schema-3 ballot requires a capsule"
            )
        return prepare_professional_completeness_ballot_template_v3(
            packet=packet,
            packet_sha256=packet_sha256,
            capsule_path=capsule_path,
            voter_id=voter_id,
            agent_id=agent_id,
            role=role,
            expertise=expertise,
            expertise_tags=expertise_tags,
            skill_ids=skill_ids,
            created_on=created_on,
            validation_root=validation_root,
        )
    _validate_professional_completeness_packet(packet)
    if capsule_path is not None:
        raise PanelReviewError(
            "review capsules require a professional completeness schema-3 packet"
        )
    _lowercase_sha256(packet_sha256, label="packet_sha256")
    voter = {
        "voter_id": _non_blank(voter_id, label="voter_id"),
        "agent_id": _non_blank(agent_id, label="agent_id"),
        "role": _non_blank(role, label="role"),
        "expertise": _string_list(
            expertise, label="expertise", allow_empty=False
        ),
        "independent_review": True,
    }
    if packet["schema_version"] == SCHEMA_VERSION:
        if skill_ids:
            raise PanelReviewError(
                "professional completeness schema-1 ballots do not support Skill assignments"
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
            "review_id": packet["review_id"],
            "created_on": _iso_date(created_on, label="created_on"),
            "packet_sha256": packet_sha256,
            "source_fingerprints": packet["source_fingerprints"],
            "voter": voter,
            "professional_votes": [
                {
                    "skill_id": target["skill_id"],
                    "decision": None,
                    "reason_code": None,
                    "criteria": {
                        criterion: None
                        for criterion in sorted(
                            PROFESSIONAL_COMPLETENESS_CRITERIA
                        )
                    },
                    "rationale": "",
                }
                for target in packet["professional_targets"]
            ],
            "limitations": [
                "Unfilled template: every criterion, decision, reason code, and rationale must be completed independently before validation."
            ],
        }

    assigned_targets = _professional_assigned_targets(packet, skill_ids)
    voter["expertise_tags"] = _expertise_tags(
        expertise_tags,
        label="expertise_tags",
        allow_architecture=True,
    )
    voter_kind = _professional_voter_kind(voter)
    for target in assigned_targets:
        _validate_professional_target_qualification(
            voter,
            target,
            voter_kind=voter_kind,
        )
    voter["qualification_claims"] = [
        {
            "expertise_tag": tag,
            "qualification_basis": "",
            "proof_limit": "",
        }
        for tag in voter["expertise_tags"]
    ]
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": _iso_date(created_on, label="created_on"),
        "packet_sha256": packet_sha256,
        "source_fingerprints": packet["source_fingerprints"],
        "voter": voter,
        "professional_votes": [
            {
                "skill_id": target["skill_id"],
                "decision": None,
                "reason_code": None,
                "evidence_anchors": [],
                "criteria": {
                    criterion: {
                        "status": None,
                        "evidence_assertions": [],
                    }
                    for criterion in sorted(PROFESSIONAL_COMPLETENESS_CRITERIA)
                },
                "examined_failure_modes": [],
                "examined_omission_candidates": [],
                "examined_adjacent_candidates": [
                    {
                        "skill_id": candidate["skill_id"],
                        "review_origin": "packet-required",
                        "discovery_reason": None,
                        "disposition": None,
                        "target_anchor_ids": [],
                        "candidate_anchor_ids": [],
                        "rationale": "",
                    }
                    for candidate in target["routing_adjacency"][
                        "required_candidates"
                    ]
                ],
                "proof_limits": [],
                "rationale": "",
            }
            for target in assigned_targets
        ],
        "limitations": [
            "Unfilled template: every assigned source anchor, criterion assertion, failure mode, omission candidate, required adjacent candidate, optional reviewer-added adjacent candidate, qualification claim, proof limit, decision, reason code, and rationale must be completed independently before validation."
        ],
    }


def build_ballot_template(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    agent_id: str,
    role: str,
    expertise: list[str],
    created_on: str,
    expertise_tags: list[str] | None = None,
    skill_ids: list[str] | None = None,
    capsule_path: Path | None = None,
    validation_root: Path = ROOT,
) -> dict[str, Any]:
    """Dispatch one immutable packet to its kind-specific empty ballot schema."""

    if skill_ids and packet.get("kind") != PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        raise PanelReviewError(
            "Skill assignments require a professional-completeness packet"
        )
    arguments = {
        "packet": packet,
        "packet_sha256": packet_sha256,
        "voter_id": voter_id,
        "agent_id": agent_id,
        "role": role,
        "expertise": expertise,
        "created_on": created_on,
    }
    if packet.get("kind") == PACKET_KIND:
        ballot = prepare_readability_ballot_template(**arguments)
    elif packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        ballot = prepare_professional_completeness_ballot_template(
            **arguments,
            expertise_tags=expertise_tags,
            skill_ids=skill_ids,
            capsule_path=capsule_path,
            validation_root=validation_root,
        )
    elif packet.get("kind") == SEMANTIC_DISPOSITION_PACKET_KIND:
        ballot = prepare_semantic_ballot_template(**arguments)
    else:
        raise PanelReviewError("template packet kind is invalid")
    if VOTER_ID_PATTERN.fullmatch(ballot["voter"]["voter_id"]) is None:
        raise PanelReviewError(
            "ballot.voter.voter_id must be a lowercase filename-safe slug"
        )
    return ballot


def validate_ballot_template(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
) -> dict[str, Any]:
    """Validate canonical full coverage while requiring every vote to stay empty."""

    voter = ballot.get("voter")
    expected_voter_fields = VOTER_FIELDS
    if (
        packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND
        and packet.get("schema_version")
        in {
            PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
            PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
        }
    ):
        expected_voter_fields = PROFESSIONAL_V2_VOTER_FIELDS
    if not isinstance(voter, dict) or set(voter) != expected_voter_fields:
        raise PanelReviewError("ballot template voter fields are invalid")
    expected = build_ballot_template(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter.get("voter_id"),
        agent_id=voter.get("agent_id"),
        role=voter.get("role"),
        expertise=voter.get("expertise"),
        expertise_tags=voter.get("expertise_tags"),
        capsule_path=(
            _validated_artifact_reference(
                ballot.get("capsule"),
                validation_root=validation_root,
                label="schema-3 ballot template capsule",
                require_review_id=True,
                expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                expected_review_id=packet.get("review_id"),
            )[0]
            if packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND
            and packet.get("schema_version")
            == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            else None
        ),
        validation_root=validation_root,
        skill_ids=(
            [row.get("skill_id") for row in ballot.get("professional_votes", [])]
            if packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND
            and packet.get("schema_version")
            in {
                PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
            }
            else None
        ),
        created_on=ballot.get("created_on"),
    )
    if ballot != expected:
        raise PanelReviewError(
            "ballot template must match canonical coverage and contain only unfilled votes"
        )
    return ballot


def _iso_date(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise PanelReviewError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise PanelReviewError(f"{label} must be an ISO date") from exc
    return parsed.isoformat()


def _non_blank(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PanelReviewError(f"{label} must be a non-blank string")
    return value


def _fingerprints(
    value: object,
    *,
    label: str,
    required: set[str] | None = None,
) -> dict[str, str]:
    required = required or {"reference_content", "root_content", "ai_readability"}
    if not isinstance(value, dict) or set(value) != required:
        raise PanelReviewError(f"{label} must contain exactly {sorted(required)}")
    result: dict[str, str] = {}
    for key in sorted(required):
        fingerprint = value.get(key)
        if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(
            char not in "0123456789abcdef" for char in fingerprint
        ):
            raise PanelReviewError(f"{label}.{key} must be lowercase sha256")
        result[key] = fingerprint
    return result


def _canonical_relative_path(value: str, *, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or candidate.as_posix() != value or ".." in candidate.parts:
        raise PanelReviewError(f"{label} must be a canonical repository-relative path")
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PanelReviewError(f"{label} escapes the repository") from exc
    return resolved


def _canonical_artifact_path(
    value: object,
    *,
    validation_root: Path,
    label: str,
    must_exist: bool = True,
    forbidden_paths: set[Path] | None = None,
) -> Path:
    """Resolve one canonical artifact path without following path aliases."""

    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or PurePosixPath(value).is_absolute()
        or PurePosixPath(value).as_posix() != value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise PanelReviewError(
            f"{label} must be a canonical repository-relative POSIX path"
        )
    root = validation_root.resolve()
    lexical = validation_root.joinpath(*value.split("/"))
    current = validation_root
    for part in value.split("/"):
        current = current / part
        if current.is_symlink():
            raise PanelReviewError(f"{label} must not traverse a symlink")
    resolved = lexical.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PanelReviewError(f"{label} escapes validation root") from exc
    if must_exist and not resolved.is_file():
        raise PanelReviewError(f"{label} is missing: {value}")
    forbidden = {path.resolve() for path in (forbidden_paths or set())}
    if resolved in forbidden:
        raise PanelReviewError(f"{label} creates a self-reference or cycle")
    return resolved


def _artifact_reference(
    path: Path,
    *,
    validation_root: Path,
    kind: str | None = None,
    axis: str | None = None,
    review_id: str | None = None,
) -> dict[str, str]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(validation_root.resolve()).as_posix()
    except ValueError as exc:
        raise PanelReviewError("artifact path escapes validation root") from exc
    reference = {"path": relative, "sha256": _sha256(resolved)}
    if kind is not None:
        reference["kind"] = kind
    if axis is not None:
        reference["axis"] = axis
    if review_id is not None:
        reference["review_id"] = review_id
    return reference


def _validated_artifact_reference(
    value: object,
    *,
    validation_root: Path,
    label: str,
    require_review_id: bool,
    expected_kind: str | None = None,
    expected_axis: str | None = None,
    expected_review_id: str | None = None,
    forbidden_paths: set[Path] | None = None,
) -> tuple[Path, dict[str, str]]:
    fields = {"path", "sha256"}
    if require_review_id:
        fields.add("review_id")
    if expected_kind is not None:
        fields.add("kind")
    if expected_axis is not None:
        fields.add("axis")
    if not isinstance(value, dict) or set(value) != fields:
        raise PanelReviewError(f"{label} fields are invalid")
    path = _canonical_artifact_path(
        value.get("path"),
        validation_root=validation_root,
        label=f"{label}.path",
        forbidden_paths=forbidden_paths,
    )
    digest = _lowercase_sha256(value.get("sha256"), label=f"{label}.sha256")
    if _sha256(path) != digest:
        raise PanelReviewError(f"{label}.sha256 is stale")
    normalized = {"path": str(value["path"]), "sha256": digest}
    if expected_kind is not None:
        if value.get("kind") != expected_kind:
            raise PanelReviewError(f"{label}.kind is invalid")
        normalized["kind"] = expected_kind
    if expected_axis is not None:
        if value.get("axis") != expected_axis:
            raise PanelReviewError(f"{label}.axis is invalid")
        normalized["axis"] = expected_axis
    if require_review_id:
        normalized["review_id"] = _non_blank(
            value.get("review_id"), label=f"{label}.review_id"
        )
        if (
            expected_review_id is not None
            and normalized["review_id"] != expected_review_id
        ):
            raise PanelReviewError(f"{label}.review_id is stale")
    if (
        expected_kind is not None
        and expected_axis == PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS
    ):
        _validate_professional_artifact_layout(
            normalized,
            expected_kind=expected_kind,
            label=label,
            validation_root=validation_root,
        )
    return path, normalized


def _professional_artifact_reference(
    path: Path,
    *,
    validation_root: Path,
    kind: str,
    review_id: str,
) -> dict[str, str]:
    return _artifact_reference(
        path,
        validation_root=validation_root,
        kind=kind,
        axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        review_id=review_id,
    )


def _read_validated_json_artifact_reference(
    value: object,
    *,
    validation_root: Path,
    label: str,
    expected_kind: str,
    expected_axis: str,
    expected_review_id: str | None = None,
    forbidden_paths: set[Path] | None = None,
) -> tuple[Path, dict[str, str], dict[str, Any]]:
    """Bind schema-3 hash validation and JSON parsing to one byte read."""

    shaped = _artifact_reference_shape(
        value,
        label=label,
        require_review_id=True,
        expected_kind=expected_kind,
        expected_axis=expected_axis,
    )
    if (
        expected_review_id is not None
        and shaped["review_id"] != expected_review_id
    ):
        raise PanelReviewError(f"{label}.review_id is stale")
    _validate_professional_artifact_layout(
        shaped,
        expected_kind=expected_kind,
        label=label,
        validation_root=validation_root,
    )
    path = _canonical_artifact_path(
        shaped["path"],
        validation_root=validation_root,
        label=f"{label}.path",
        forbidden_paths=forbidden_paths,
    )
    try:
        with path.open("rb") as handle:
            descriptor_before = os.fstat(handle.fileno())
            payload = handle.read()
            descriptor_after = os.fstat(handle.fileno())
            path_after = _canonical_artifact_path(
                shaped["path"],
                validation_root=validation_root,
                label=f"{label}.path",
                forbidden_paths=forbidden_paths,
            )
            pathname_stat = path_after.stat()
    except OSError as exc:
        raise PanelReviewError(f"cannot read {label}: {exc}") from exc
    descriptor_identity = (
        descriptor_before.st_dev,
        descriptor_before.st_ino,
        descriptor_before.st_size,
        descriptor_before.st_mtime_ns,
        descriptor_before.st_ctime_ns,
    )
    if descriptor_identity != (
        descriptor_after.st_dev,
        descriptor_after.st_ino,
        descriptor_after.st_size,
        descriptor_after.st_mtime_ns,
        descriptor_after.st_ctime_ns,
    ) or (
        pathname_stat.st_dev,
        pathname_stat.st_ino,
        pathname_stat.st_size,
        pathname_stat.st_mtime_ns,
        pathname_stat.st_ctime_ns,
    ) != (
        descriptor_after.st_dev,
        descriptor_after.st_ino,
        descriptor_after.st_size,
        descriptor_after.st_mtime_ns,
        descriptor_after.st_ctime_ns,
    ):
        raise PanelReviewError(f"{label} changed during its bound read")
    if hashlib.sha256(payload).hexdigest() != shaped["sha256"]:
        raise PanelReviewError(f"{label}.sha256 is stale")
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PanelReviewError(f"{label} is not one UTF-8 JSON object") from exc
    if not isinstance(parsed, dict):
        raise PanelReviewError(f"{label} must contain one JSON object")
    return path_after, shaped, parsed


def _professional_v3_invocation_cache() -> dict[str, Any]:
    return {
        "artifacts": {},
        "artifacts_by_path": {},
        "path_artifacts": {},
        "baselines": {},
        "canonical_sizes": {},
        "origin_rounds": {},
        "origin_targets": {},
        "packet_states": {},
        "ballot_votes": {},
        "validated_ballots": set(),
    }


def _professional_v3_cached_json_artifact(
    value: object,
    *,
    cache: dict[str, Any],
    validation_root: Path,
    label: str,
    expected_kind: str,
    expected_axis: str,
    expected_review_id: str | None = None,
    forbidden_paths: set[Path] | None = None,
) -> tuple[Path, dict[str, str], dict[str, Any]]:
    shaped = _artifact_reference_shape(
        value,
        label=label,
        require_review_id=True,
        expected_kind=expected_kind,
        expected_axis=expected_axis,
    )
    key = (
        validation_root.resolve().as_posix(),
        expected_kind,
        shaped["path"],
        shaped["sha256"],
        shaped["review_id"],
    )
    cached = cache["artifacts"].get(key)
    if cached is not None:
        path, normalized, parsed = cached
        if path.resolve() in {
            item.resolve() for item in (forbidden_paths or set())
        }:
            raise PanelReviewError(f"{label} creates a cached cycle")
        if (
            expected_review_id is not None
            and normalized["review_id"] != expected_review_id
        ):
            raise PanelReviewError(f"{label}.review_id is stale")
        return path, normalized, parsed
    artifact_path_key = (
        validation_root.resolve().as_posix(),
        expected_kind,
        shaped["path"],
    )
    existing = cache["artifacts_by_path"].get(artifact_path_key)
    if existing is not None and (
        existing[1]["sha256"] != shaped["sha256"]
        or existing[1]["review_id"] != shaped["review_id"]
    ):
        raise PanelReviewError(f"{label} conflicts with a cached artifact path")
    result = _read_validated_json_artifact_reference(
        shaped,
        validation_root=validation_root,
        label=label,
        expected_kind=expected_kind,
        expected_axis=expected_axis,
        expected_review_id=expected_review_id,
        forbidden_paths=forbidden_paths,
    )
    cache["artifacts"][key] = result
    cache["artifacts_by_path"][artifact_path_key] = result
    return result


def _professional_v3_bind_json_artifact_path(
    path: Path,
    *,
    cache: dict[str, Any],
    validation_root: Path,
    label: str,
    expected_kind: str,
    expected_review_id: str,
    forbidden_paths: set[Path] | None = None,
) -> tuple[Path, dict[str, str], dict[str, Any]]:
    """Bind a canonical CLI/library path with one byte read and derived SHA."""

    lexical_root = validation_root.absolute()
    canonical_root = validation_root.resolve()
    lexical = path if path.is_absolute() else validation_root / path
    absolute_path = lexical.absolute()
    try:
        relative = absolute_path.relative_to(lexical_root).as_posix()
    except ValueError:
        try:
            relative = absolute_path.relative_to(canonical_root).as_posix()
        except ValueError as exc:
            raise PanelReviewError(
                f"{label} escapes validation root"
            ) from exc
    seed = {
        "path": relative,
        "sha256": "0" * 64,
        "kind": expected_kind,
        "axis": PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": expected_review_id,
    }
    _validate_professional_artifact_layout(
        seed,
        expected_kind=expected_kind,
        label=label,
        validation_root=validation_root,
    )
    canonical = _canonical_artifact_path(
        relative,
        validation_root=validation_root,
        label=f"{label}.path",
        forbidden_paths=forbidden_paths,
    )
    path_key = (
        validation_root.resolve().as_posix(),
        expected_kind,
        relative,
        expected_review_id,
    )
    artifact_path_key = (
        validation_root.resolve().as_posix(),
        expected_kind,
        relative,
    )
    cached = cache["path_artifacts"].get(path_key)
    if cached is not None:
        cached_path, _reference, _value = cached
        if cached_path.resolve() in {
            item.resolve() for item in (forbidden_paths or set())
        }:
            raise PanelReviewError(f"{label} creates a cached cycle")
        return cached
    artifact_match = cache["artifacts_by_path"].get(artifact_path_key)
    if artifact_match is not None:
        cached_path, _reference, _value = artifact_match
        if cached_path.resolve() in {
            item.resolve() for item in (forbidden_paths or set())
        }:
            raise PanelReviewError(f"{label} creates a cached cycle")
        cache["path_artifacts"][path_key] = artifact_match
        return artifact_match
    try:
        with canonical.open("rb") as handle:
            descriptor_before = os.fstat(handle.fileno())
            payload = handle.read()
            descriptor_after = os.fstat(handle.fileno())
            canonical_after = _canonical_artifact_path(
                relative,
                validation_root=validation_root,
                label=f"{label}.path",
                forbidden_paths=forbidden_paths,
            )
            pathname_stat = canonical_after.stat()
    except OSError as exc:
        raise PanelReviewError(f"cannot read {label}: {exc}") from exc
    descriptor_identity = (
        descriptor_before.st_dev,
        descriptor_before.st_ino,
        descriptor_before.st_size,
        descriptor_before.st_mtime_ns,
        descriptor_before.st_ctime_ns,
    )
    if descriptor_identity != (
        descriptor_after.st_dev,
        descriptor_after.st_ino,
        descriptor_after.st_size,
        descriptor_after.st_mtime_ns,
        descriptor_after.st_ctime_ns,
    ) or (
        pathname_stat.st_dev,
        pathname_stat.st_ino,
        pathname_stat.st_size,
        pathname_stat.st_mtime_ns,
        pathname_stat.st_ctime_ns,
    ) != (
        descriptor_after.st_dev,
        descriptor_after.st_ino,
        descriptor_after.st_size,
        descriptor_after.st_mtime_ns,
        descriptor_after.st_ctime_ns,
    ):
        raise PanelReviewError(f"{label} changed during its bound read")
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PanelReviewError(f"{label} is not one UTF-8 JSON object") from exc
    if not isinstance(parsed, dict):
        raise PanelReviewError(f"{label} must contain one JSON object")
    reference = {
        **seed,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    result = (canonical_after, reference, parsed)
    cache["path_artifacts"][path_key] = result
    artifact_key = (
        validation_root.resolve().as_posix(),
        expected_kind,
        reference["path"],
        reference["sha256"],
        reference["review_id"],
    )
    cache["artifacts"][artifact_key] = result
    cache["artifacts_by_path"][artifact_path_key] = result
    return result


def _professional_v3_cached_canonical_size(
    reference: dict[str, str],
    value: dict[str, Any],
    *,
    cache: dict[str, Any],
) -> int:
    """Measure each immutable artifact at most once per top-level invocation."""

    key = (reference["path"], reference["sha256"])
    cached = cache["canonical_sizes"].get(key)
    if cached is None:
        cached = len(
            professional_carry.canonical_json_bytes(
                _professional_v3_capsule_input_projection(value)
            )
        )
        cache["canonical_sizes"][key] = cached
    return cached


def _source_line(path: str, line: int) -> str:
    source = _canonical_relative_path(path, label="finding path")
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PanelReviewError(f"cannot read finding source: {path}") from exc
    if line < 1 or line > len(lines):
        raise PanelReviewError(f"finding line is outside source: {path}:{line}")
    return lines[line - 1]


def _readability_finding_id(
    *,
    document_id: str,
    kind: str,
    sentence: str,
    occurrence: int,
) -> str:
    """Return a stable identity independent of raw source coordinates."""

    try:
        return panel_contracts.readability_stable_finding_id(
            document_id=document_id,
            kind=kind,
            sentence=sentence,
            occurrence=occurrence,
        )
    except ValueError as exc:
        raise PanelReviewError(str(exc)) from exc


def _readability_targets_from_evidence(
    readability: dict[str, Any],
) -> list[dict[str, Any]]:
    """Project exact schema-2 document contexts and detector findings."""

    documents = readability.get("documents")
    findings = readability.get("findings")
    if not isinstance(documents, list) or not isinstance(findings, list):
        raise PanelReviewError("AI-readability documents and findings are required")
    findings_by_document: dict[str, list[dict[str, Any]]] = {}
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise PanelReviewError(f"readability finding {index} must be an object")
        document_id = _non_blank(
            finding.get("document_id"),
            label=f"readability finding {index}.document_id",
        )
        findings_by_document.setdefault(document_id, []).append(
            {
                "finding_id": finding.get("finding_id"),
                "line": finding.get("line"),
                "band": finding.get("band"),
                "words": finding.get("words"),
                "kind": finding.get("kind"),
                "sentence": finding.get("sentence"),
                "sentence_fingerprint": finding.get("sentence_fingerprint"),
                "source_span": copy.deepcopy(finding.get("source_span")),
            }
        )

    targets: list[dict[str, Any]] = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise PanelReviewError(f"readability document {index} must be an object")
        highest_band = document.get("highest_advisory_band")
        if highest_band is None:
            continue
        document_id = _non_blank(
            document.get("document_id"),
            label=f"readability document {index}.document_id",
        )
        document_findings = findings_by_document.get(document_id, [])
        if not document_findings:
            raise PanelReviewError(
                f"advisory document has no findings: {document_id}"
            )
        document_context = copy.deepcopy(document.get("document_context"))
        if isinstance(document_context, dict):
            document_context.pop("line_offset", None)
        targets.append(
            {
                "document_id": document_id,
                "path": document.get("path"),
                "surface": document.get("surface"),
                "document_part": document.get("document_part"),
                "owner": document.get("owner"),
                "source_selector": copy.deepcopy(
                    document.get("source_selector")
                ),
                "content_fingerprint": document.get("content_fingerprint"),
                "document_context": document_context,
                "highest_band": highest_band,
                "findings": sorted(
                    document_findings,
                    key=lambda row: (
                        int(row["source_span"]["start_offset"]),
                        int(row["source_span"]["end_offset"]),
                        str(row["kind"]),
                        str(row["finding_id"]),
                    ),
                ),
            }
        )
    targets.sort(key=lambda row: row["document_id"])
    expected_advisories = readability.get("summary", {}).get(
        "advisory_documents"
    )
    if expected_advisories != len(targets):
        raise PanelReviewError(
            "advisory document count does not match packet targets"
        )
    return targets


def _content_targets_from_evidence(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind each density target to its complete Root body document context."""

    skills = audit.get("skills")
    readability = audit.get("ai_readability")
    documents = (
        readability.get("documents") if isinstance(readability, dict) else None
    )
    if not isinstance(skills, list) or not isinstance(documents, list):
        raise PanelReviewError(
            "audit skills and AI-readability documents are required"
        )
    body_documents: dict[str, dict[str, Any]] = {}
    for index, document in enumerate(documents):
        if not isinstance(document, dict) or document.get("document_part") != "body":
            continue
        path = _non_blank(
            document.get("path"),
            label=f"ai_readability.documents[{index}].path",
        )
        if path in body_documents:
            raise PanelReviewError(f"duplicate AI-readability Root body: {path}")
        body_documents[path] = document

    targets: list[dict[str, Any]] = []
    for index, row in enumerate(skills):
        if not isinstance(row, dict) or row.get("classification") not in {
            "REVIEW_DENSITY",
            "TIGHTEN_BODY",
        }:
            continue
        path = _non_blank(row.get("path"), label=f"audit.skills[{index}].path")
        document = body_documents.get(path)
        if document is None:
            raise PanelReviewError(
                f"content target lacks AI-readability Root body: {path}"
            )
        document_id = _non_blank(
            document.get("document_id"),
            label=f"content target {path}.document_id",
        )
        if document_id != f"{path}#body":
            raise PanelReviewError(
                f"content target Root body document_id is invalid: {path}"
            )
        owner = _non_blank(
            document.get("owner"), label=f"content target {path}.owner"
        )
        document_part = _non_blank(
            document.get("document_part"),
            label=f"content target {path}.document_part",
        )
        if document_part != "body":
            raise PanelReviewError(
                f"content target Root document part is invalid: {path}"
            )
        selector = copy.deepcopy(document.get("source_selector"))
        if selector != {"kind": "yaml-body", "path": path}:
            raise PanelReviewError(
                f"content target Root body selector is invalid: {path}"
            )
        context = copy.deepcopy(document.get("document_context"))
        if isinstance(context, dict):
            context.pop("line_offset", None)
        context = _validate_readability_context(
            context,
            label=f"content target {path}.document_context",
        )
        fingerprint = _lowercase_sha256(
            document.get("content_fingerprint"),
            label=f"content target {path}.content_fingerprint",
        )
        if fingerprint != context["sha256"]:
            raise PanelReviewError(
                f"content target Root body fingerprint is stale: {path}"
            )
        targets.append(
            {
                "path": path,
                "classification": row.get("classification"),
                "review_state": row.get("review_state"),
                "review_reasons": copy.deepcopy(row.get("review_reasons")),
                "document_id": document_id,
                "owner": owner,
                "document_part": document_part,
                "source_selector": selector,
                "content_fingerprint": fingerprint,
                "document_context": context,
            }
        )
    targets.sort(key=lambda row: row["path"])
    return targets


def _current_readability_target_projection() -> tuple[
    dict[str, str],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Rebuild the complete current R target and detector projection."""

    auditor = _load_skill_content_auditor()
    source_documents = auditor._ai_readability_documents()
    current = auditor._collect_ai_readability(source_documents)
    audit = _json_object(
        ROOT / "reports/skill-content-audit.json",
        label="current skill content audit",
    )
    audit["ai_readability"] = current
    packet = prepare_packet(
        audit=audit,
        review_id="current-readability-projection",
        created_on="2000-01-01",
    )
    return (
        packet["source_fingerprints"],
        packet["content_targets"],
        packet["readability_targets"],
        packet["actionability_targets"],
    )


def _validate_readability_context(
    value: object, *, label: str
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != READABILITY_DOCUMENT_CONTEXT_FIELDS:
        raise PanelReviewError(f"{label} fields are invalid")
    text = value.get("text")
    lines = value.get("lines")
    line_count = value.get("line_count")
    if (
        not isinstance(text, str)
        or type(line_count) is not int
        or line_count < 1
        or not isinstance(lines, list)
        or len(lines) != line_count
        or text.splitlines()
        != [row.get("text") if isinstance(row, dict) else None for row in lines]
    ):
        raise PanelReviewError(f"{label} canonical text and lines disagree")
    for index, row in enumerate(lines):
        if (
            not isinstance(row, dict)
            or set(row) != READABILITY_CONTEXT_LINE_FIELDS
            or row.get("line") != index + 1
            or not isinstance(row.get("text"), str)
        ):
            raise PanelReviewError(f"{label}.lines[{index}] is invalid")
    if _lowercase_sha256(value.get("sha256"), label=f"{label}.sha256") != (
        hashlib.sha256(text.encode("utf-8")).hexdigest()
    ):
        raise PanelReviewError(f"{label}.sha256 is stale")
    return value


def _validate_readability_source_span(
    value: object,
    *,
    context: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != READABILITY_SOURCE_SPAN_FIELDS:
        raise PanelReviewError(f"{label} fields are invalid")
    start = value.get("start_line")
    end = value.get("end_line")
    start_offset = value.get("start_offset")
    end_offset = value.get("end_offset")
    start_column = value.get("start_column")
    end_column = value.get("end_column")
    lines = value.get("lines")
    if (
        type(start_offset) is not int
        or type(end_offset) is not int
        or not 0 <= start_offset < end_offset <= len(context["text"])
        or type(start) is not int
        or type(end) is not int
        or end < start
        or type(start_column) is not int
        or type(end_column) is not int
        or start_column < 1
        or end_column < 1
        or not isinstance(lines, list)
        or len(lines) != end - start + 1
    ):
        raise PanelReviewError(f"{label} coordinates are invalid")
    starts: list[int] = []
    cursor = 0
    for raw_line in context["text"].splitlines(keepends=True):
        starts.append(cursor)
        cursor += len(raw_line)
    start_index = max(
        index for index, offset in enumerate(starts) if offset <= start_offset
    )
    end_character = end_offset - 1
    end_index = max(
        index for index, offset in enumerate(starts) if offset <= end_character
    )
    if (
        start != start_index + 1
        or end != end_index + 1
        or start_column != start_offset - starts[start_index] + 1
        or end_column != end_offset - starts[end_index] + 1
    ):
        raise PanelReviewError(f"{label} line/column projection is stale")
    context_by_line = {row["line"]: row["text"] for row in context["lines"]}
    for index, row in enumerate(lines):
        line = start + index
        if (
            not isinstance(row, dict)
            or set(row) != READABILITY_CONTEXT_LINE_FIELDS
            or row.get("line") != line
            or row.get("text") != context_by_line.get(line)
        ):
            raise PanelReviewError(f"{label}.lines[{index}] is stale")
    if _lowercase_sha256(value.get("sha256"), label=f"{label}.sha256") != (
        hashlib.sha256(
            context["text"][start_offset:end_offset].encode("utf-8")
        ).hexdigest()
    ):
        raise PanelReviewError(f"{label}.sha256 is stale")
    return value


def _actionability_target_id(path: str) -> str:
    digest = hashlib.sha256(
        f"weak-front-loaded-action-v1\0{path}".encode("utf-8")
    ).hexdigest()
    return f"weak-front-loaded-action:{digest}"


def _actionability_front_window(path: str, *, limit: int) -> dict[str, Any]:
    if type(limit) is not int or limit < 1:
        raise PanelReviewError("actionability front-window limit is invalid")
    source = _canonical_relative_path(path, label="actionability target path")
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise PanelReviewError(f"cannot read actionability source: {path}") from exc
    if not lines or lines[0].strip() != "---":
        raise PanelReviewError(f"actionability source lacks YAML frontmatter: {path}")
    end_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        ),
        None,
    )
    if end_index is None:
        raise PanelReviewError(
            f"actionability source has unterminated YAML frontmatter: {path}"
        )
    body_lines = lines[end_index + 1 :]
    try:
        logical_units = panel_contracts.readability_normalized_logical_units(
            "\n".join(body_lines),
            exclude_fenced=True,
            strip_frontmatter=False,
        )
    except ValueError as exc:
        raise PanelReviewError(
            f"actionability source body is invalid: {path}"
        ) from exc
    selected_units = logical_units[:limit]
    if not selected_units:
        raise PanelReviewError(
            f"actionability source body has no governed logical units: {path}"
        )
    window_lines = body_lines[: int(selected_units[-1]["end_line"])]
    start_line = end_index + 2
    numbered_lines = [
        {"line": start_line + index, "text": text}
        for index, text in enumerate(window_lines)
    ]
    return {
        "start_line": start_line,
        "end_line": start_line + len(window_lines) - 1,
        "line_count": len(window_lines),
        "lines": numbered_lines,
        "sha256": hashlib.sha256(
            "\n".join(window_lines).encode("utf-8")
        ).hexdigest(),
    }


def _validate_actionability_front_window(
    value: object,
    *,
    label: str,
    limit: int,
) -> dict[str, Any]:
    """Validate an immutable detector window without consulting live source."""

    if not isinstance(value, dict) or set(value) != ACTIONABILITY_FRONT_WINDOW_FIELDS:
        raise PanelReviewError(f"{label} is invalid")
    start_line = value.get("start_line")
    end_line = value.get("end_line")
    line_count = value.get("line_count")
    if (
        type(start_line) is not int
        or start_line < 1
        or type(end_line) is not int
        or type(line_count) is not int
        or line_count < 1
        or end_line != start_line + line_count - 1
    ):
        raise PanelReviewError(f"{label} coordinates are invalid")
    lines = value.get("lines")
    if not isinstance(lines, list) or len(lines) != line_count:
        raise PanelReviewError(f"{label}.lines do not match line_count")
    for index, row in enumerate(lines):
        row_label = f"{label}.lines[{index}]"
        if not isinstance(row, dict) or set(row) != ACTIONABILITY_FRONT_WINDOW_LINE_FIELDS:
            raise PanelReviewError(f"{row_label} fields are invalid")
        if row.get("line") != start_line + index or not isinstance(
            row.get("text"), str
        ):
            raise PanelReviewError(f"{row_label} is invalid")
    fingerprint = _lowercase_sha256(value.get("sha256"), label=f"{label}.sha256")
    expected_fingerprint = hashlib.sha256(
        "\n".join(row["text"] for row in lines).encode("utf-8")
    ).hexdigest()
    if fingerprint != expected_fingerprint:
        raise PanelReviewError(f"{label}.sha256 does not match embedded lines")
    try:
        logical_units = panel_contracts.readability_normalized_logical_units(
            "\n".join(row["text"] for row in lines),
            exclude_fenced=True,
            strip_frontmatter=False,
        )
    except ValueError as exc:
        raise PanelReviewError(f"{label} logical units are invalid") from exc
    if not 1 <= len(logical_units) <= limit:
        raise PanelReviewError(
            f"{label} normalized logical-unit count is outside the limit"
        )
    return value


def _actionability_window_line_is_substantive(
    window: dict[str, Any], line: int
) -> bool:
    """Apply detector-equivalent prose semantics to an embedded body window."""

    relative_line = line - int(window["start_line"]) + 1
    content = "\n".join(row["text"] for row in window["lines"])
    try:
        logical_units = panel_contracts.readability_normalized_logical_units(
            content,
            exclude_fenced=True,
            strip_frontmatter=False,
        )
    except ValueError:
        return False
    return any(
        unit["kind"] not in {"heading", "fenced"}
        and relative_line in unit["source_lines"]
        for unit in logical_units
    )


def _root_body_fingerprints(audit: dict[str, Any]) -> dict[str, str]:
    root_content = audit.get("root_content")
    documents = root_content.get("documents") if isinstance(root_content, dict) else None
    if not isinstance(documents, list):
        raise PanelReviewError("audit.root_content.documents must be an array")
    result: dict[str, str] = {}
    for index, document in enumerate(documents):
        if not isinstance(document, dict) or document.get("document_part") != "body":
            continue
        path = _non_blank(
            document.get("path"), label=f"root_content.documents[{index}].path"
        )
        fingerprint = _lowercase_sha256(
            document.get("content_fingerprint"),
            label=f"root_content.documents[{index}].content_fingerprint",
        )
        if path in result:
            raise PanelReviewError(f"duplicate Root body document: {path}")
        result[path] = fingerprint
    return result


def _readability_panel_contract(
    *,
    required_actionability_target_count: int,
    actionability_score_threshold: int,
    actionability_front_window_lines: int,
) -> dict[str, Any]:
    return {
        "decision_method": DECISION_METHOD,
        "required_voters": PANEL_SIZE,
        "abstentions_allowed": False,
        "minimum_winning_votes": 2,
        "independent_ballots": True,
        "required_actionability_target_count": (
            required_actionability_target_count
        ),
        "actionability_score_threshold": actionability_score_threshold,
        "actionability_front_window_lines": actionability_front_window_lines,
        "allowed_actionability_dispositions": sorted(
            ACTIONABILITY_DECISIONS
        ),
        "readability_document_decision_method": (
            "finding-grounded-document-majority-v1"
        ),
        "readability_reviewer_derivation": "any-nested-tightening",
        "content_source_binding_contract": CONTENT_SOURCE_BINDING_CONTRACT,
        "readability_currentness_contract": (
            panel_contracts.readability_currentness_contract_projection()
        ),
    }


def readability_review_contract_fingerprint(
    *,
    required_actionability_target_count: int,
    actionability_score_threshold: int,
    actionability_front_window_lines: int,
) -> str:
    """Bind a compact Readability attestation to the current panel contract."""

    return _canonical_json_sha256(
        _readability_panel_contract(
            required_actionability_target_count=(
                required_actionability_target_count
            ),
            actionability_score_threshold=actionability_score_threshold,
            actionability_front_window_lines=actionability_front_window_lines,
        )
    )


def _readability_target_manifest_projection(
    *,
    content_targets: list[dict[str, Any]],
    readability_targets: list[dict[str, Any]],
    actionability_targets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return complete compact current bindings for every Readability target."""

    bindings = _readability_target_authorities(
        {
            "content_targets": content_targets,
            "readability_targets": readability_targets,
            "actionability_targets": actionability_targets,
        }
    )
    try:
        return panel_attestation.readability_target_manifest_projection(
            bindings
        )
    except panel_attestation.AttestationError as exc:
        raise PanelReviewError(
            "readability target authority manifest is invalid"
        ) from exc


def _readability_source_fingerprints(
    *,
    readability_contract: dict[str, Any],
    content_targets: list[dict[str, Any]],
    readability_targets: list[dict[str, Any]],
    actionability_targets: list[dict[str, Any]],
    actionability_score_threshold: int,
    actionability_front_window_lines: int,
) -> dict[str, str]:
    """Hash only complete R target authority and the two detector contracts."""

    try:
        readability_detector = (
            panel_contracts.readability_detector_contract_projection(
                readability_contract
            )
        )
        actionability_detector = (
            panel_contracts.actionability_detector_contract_projection(
                score_threshold=actionability_score_threshold,
                front_window_lines=actionability_front_window_lines,
            )
        )
    except ValueError as exc:
        raise PanelReviewError(str(exc)) from exc
    return _fingerprints(
        {
            "readability_target_manifest": (
                panel_attestation.readability_target_manifest_fingerprint(
                    _readability_target_authorities(
                        {
                            "content_targets": content_targets,
                            "readability_targets": readability_targets,
                            "actionability_targets": actionability_targets,
                        }
                    )
                )
            ),
            "readability_detector_contract": _canonical_json_sha256(
                readability_detector
            ),
            "actionability_detector_contract": _canonical_json_sha256(
                actionability_detector
            ),
        },
        label="source_fingerprints",
        required=set(panel_contracts.READABILITY_SOURCE_FINGERPRINT_KEYS),
    )


def prepare_packet(
    *,
    audit: dict[str, Any],
    review_id: str,
    created_on: str,
) -> dict[str, Any]:
    """Build the immutable task packet seen independently by every voter."""

    _non_blank(review_id, label="review_id")
    _iso_date(created_on, label="created_on")
    try:
        actionability_authority = (
            _load_professional_regression_validator()
            ._readability_packet_actionability_projection(audit)
        )
    except ValueError as exc:
        raise PanelReviewError(
            f"current audit actionability projection is invalid: {exc}"
        ) from exc
    readability = audit.get("ai_readability")
    if not isinstance(readability, dict):
        raise PanelReviewError("audit.ai_readability must be an object")

    skills = audit.get("skills")
    if not isinstance(skills, list):
        raise PanelReviewError("audit.skills must be an array")
    content_targets = _content_targets_from_evidence(audit)
    for index, target in enumerate(content_targets):
        _non_blank(target["path"], label=f"content_targets[{index}].path")
        if target["classification"] not in {"REVIEW_DENSITY", "TIGHTEN_BODY"}:
            raise PanelReviewError(
                f"content_targets[{index}].classification is invalid"
            )

    thresholds = audit.get("thresholds")
    if not isinstance(thresholds, dict):
        raise PanelReviewError("audit.thresholds must be an object")
    actionability_threshold = thresholds.get("weak_front_loaded_action")
    front_window_lines = thresholds.get("front_window_lines")
    if type(actionability_threshold) is not int or actionability_threshold < 1:
        raise PanelReviewError("audit weak front-loaded action threshold is invalid")
    if type(front_window_lines) is not int or front_window_lines < 1:
        raise PanelReviewError("audit front-window line count is invalid")
    root_body_fingerprints = _root_body_fingerprints(audit)
    actionability_targets: list[dict[str, Any]] = []
    for index, row in enumerate(skills):
        if not isinstance(row, dict):
            raise PanelReviewError(f"audit.skills[{index}] must be an object")
        score = row.get("front_loaded_action_score")
        reasons = row.get("review_reasons")
        actionability_model = row.get("actionability_model")
        actionability_applicable = row.get("actionability_applicable")
        if type(score) is not int or not 0 <= score <= 100:
            raise PanelReviewError(
                f"audit.skills[{index}].front_loaded_action_score is invalid"
            )
        if not isinstance(reasons, list) or not all(
            isinstance(reason, str) and reason for reason in reasons
        ):
            raise PanelReviewError(f"audit.skills[{index}].review_reasons is invalid")
        if not isinstance(actionability_model, str) or not actionability_model:
            raise PanelReviewError(
                f"audit.skills[{index}].actionability_model is invalid"
            )
        if type(actionability_applicable) is not bool:
            raise PanelReviewError(
                f"audit.skills[{index}].actionability_applicable is invalid"
            )
        reason_is_weak = "weak_front_loaded_action" in reasons
        if actionability_applicable != reason_is_weak:
            raise PanelReviewError(
                f"audit.skills[{index}] actionability applicability disagrees with review reason"
            )
        if not actionability_applicable:
            continue
        path = _non_blank(row.get("path"), label=f"audit.skills[{index}].path")
        _canonical_relative_path(path, label=f"audit.skills[{index}].path")
        if path not in root_body_fingerprints:
            raise PanelReviewError(
                f"weak actionability Skill lacks Root body fingerprint: {path}"
            )
        actionability_targets.append(
            {
                "target_id": _actionability_target_id(path),
                "skill_id": _non_blank(
                    row.get("name"), label=f"audit.skills[{index}].name"
                ),
                "path": path,
                "kind": _non_blank(
                    row.get("kind"), label=f"audit.skills[{index}].kind"
                ),
                "actionability_model": actionability_model,
                "review_state": _non_blank(
                    row.get("review_state"),
                    label=f"audit.skills[{index}].review_state",
                ),
                "front_loaded_action_score": score,
                "front_window": _actionability_front_window(
                    path, limit=front_window_lines
                ),
                "content_fingerprint": root_body_fingerprints[path],
            }
        )
    actionability_targets.sort(key=lambda row: row["target_id"])
    target_ids = [row["target_id"] for row in actionability_targets]
    if target_ids != sorted(set(target_ids)):
        raise PanelReviewError("actionability target IDs must be sorted and unique")
    expected_weak_count = audit.get("summary", {}).get(
        "actionability_applicable_items"
    )
    if expected_weak_count != len(actionability_targets):
        raise PanelReviewError(
            "weak front-loaded action summary does not match packet targets"
        )
    projected_actionability = [
        {
            field: row[field]
            for field in (
                "target_id",
                "skill_id",
                "path",
                "front_loaded_action_score",
            )
        }
        for row in actionability_targets
    ]
    if (
        projected_actionability != actionability_authority["required_targets"]
        or len(actionability_targets)
        != actionability_authority["weak_front_loaded_skills"]
    ):
        raise PanelReviewError(
            "actionability targets do not match the current audit projection"
        )

    readability_targets = _readability_targets_from_evidence(readability)
    readability_contract = readability.get("contract")
    if not isinstance(readability_contract, dict):
        raise PanelReviewError("audit AI-readability detector contract is invalid")
    fingerprints = _readability_source_fingerprints(
        readability_contract=readability_contract,
        content_targets=content_targets,
        readability_targets=readability_targets,
        actionability_targets=actionability_targets,
        actionability_score_threshold=actionability_threshold,
        actionability_front_window_lines=front_window_lines,
    )

    return {
        "schema_version": READABILITY_SCHEMA_VERSION,
        "kind": PACKET_KIND,
        "review_id": review_id,
        "created_on": created_on,
        "source_fingerprints": fingerprints,
        "panel_contract": _readability_panel_contract(
            required_actionability_target_count=len(actionability_targets),
            actionability_score_threshold=actionability_threshold,
            actionability_front_window_lines=front_window_lines,
        ),
        "rubric": {
            "accept": (
                "Accept only when the flagged text expresses one coherent decision, "
                "invariant, or bounded enumeration whose split would reduce precision."
            ),
            "tighten": (
                "Tighten when independent actions, boundaries, exceptions, or proof "
                "obligations can be separated without losing professional meaning."
            ),
            "reason_codes": {
                decision: sorted(values)
                for decision, values in sorted(
                    READABILITY_V2_REASON_CODES.items()
                )
            },
        },
        "content_targets": content_targets,
        "readability_targets": readability_targets,
        "actionability_targets": actionability_targets,
        "limitations": [
            "The packet contains static source and detector evidence only.",
            "Each voter must inspect source context and must not read another ballot.",
        ],
    }


def _validate_readability_packet(
    packet: dict[str, Any],
    *,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> None:
    validation_mode = _closed_validation_mode(validation_mode)
    schema_version = packet.get("schema_version")
    if schema_version not in {SCHEMA_VERSION, READABILITY_SCHEMA_VERSION}:
        raise PanelReviewError("readability packet schema version is unsupported")
    expected_fields = (
        LEGACY_READABILITY_PACKET_FIELDS
        if schema_version == SCHEMA_VERSION
        else READABILITY_PACKET_FIELDS
    )
    if set(packet) != expected_fields:
        raise PanelReviewError(
            f"packet fields do not match schema {schema_version}"
        )
    if packet.get("kind") != PACKET_KIND:
        raise PanelReviewError("packet schema or kind is invalid")
    _non_blank(packet.get("review_id"), label="packet.review_id")
    _iso_date(packet.get("created_on"), label="packet.created_on")
    fingerprint_fields = {"reference_content", "root_content", "ai_readability"}
    readability_source_shape = None
    if schema_version == READABILITY_SCHEMA_VERSION:
        try:
            readability_source_shape = (
                panel_attestation.readability_source_fingerprint_shape(
                    packet.get("source_fingerprints")
                )
            )
        except panel_attestation.AttestationError as exc:
            raise PanelReviewError(str(exc)) from exc
        if (
            validation_mode == VALIDATION_MODE_CURRENT
            and readability_source_shape != "current"
        ):
            raise PanelReviewError(
                "schema-2 readability packet uses legacy source fingerprints; "
                "migration is required"
            )
        fingerprint_fields = set(packet["source_fingerprints"])
    _fingerprints(
        packet.get("source_fingerprints"),
        label="packet.source_fingerprints",
        required=fingerprint_fields,
    )
    contract = packet.get("panel_contract")
    expected_contract = {
        "decision_method": DECISION_METHOD,
        "required_voters": PANEL_SIZE,
        "abstentions_allowed": False,
        "minimum_winning_votes": 2,
        "independent_ballots": True,
    }
    if schema_version == READABILITY_SCHEMA_VERSION:
        if not isinstance(contract, dict):
            raise PanelReviewError("packet panel_contract is invalid")
        binding_contract = contract.get("content_source_binding_contract")
        legacy_thin_content = (
            validation_mode == VALIDATION_MODE_HISTORICAL
            and binding_contract is None
        )
        legacy_currentness_contract = (
            validation_mode == VALIDATION_MODE_HISTORICAL
            and readability_source_shape == "legacy"
            and contract.get("readability_currentness_contract") is None
        )
        if (
            validation_mode == VALIDATION_MODE_CURRENT
            and binding_contract != CONTENT_SOURCE_BINDING_CONTRACT
        ):
            raise PanelReviewError(
                "schema-2 content source binding contract is missing or stale"
            )
        required_target_count = contract.get("required_actionability_target_count")
        score_threshold = contract.get("actionability_score_threshold")
        front_window_lines = contract.get("actionability_front_window_lines")
        if (
            type(required_target_count) is not int
            or required_target_count < 0
            or type(score_threshold) is not int
            or score_threshold < 1
            or type(front_window_lines) is not int
            or front_window_lines < 1
        ):
            raise PanelReviewError("packet actionability contract counts are invalid")
        expected_contract.update(
            {
                "required_actionability_target_count": required_target_count,
                "actionability_score_threshold": score_threshold,
                "actionability_front_window_lines": front_window_lines,
                "allowed_actionability_dispositions": sorted(
                    ACTIONABILITY_DECISIONS
                ),
                "readability_document_decision_method": (
                    "finding-grounded-document-majority-v1"
                ),
                "readability_reviewer_derivation": (
                    "any-nested-tightening"
                ),
            }
        )
        if not legacy_thin_content:
            expected_contract["content_source_binding_contract"] = (
                CONTENT_SOURCE_BINDING_CONTRACT
            )
        if not legacy_currentness_contract:
            expected_contract["readability_currentness_contract"] = (
                panel_contracts.readability_currentness_contract_projection()
            )
    else:
        legacy_thin_content = True
    if contract != expected_contract:
        raise PanelReviewError("packet panel_contract is invalid")
    rubric = packet.get("rubric")
    reason_codes = (
        REASON_CODES
        if schema_version == SCHEMA_VERSION
        else READABILITY_V2_REASON_CODES
    )
    expected_reason_codes = {
        decision: sorted(values) for decision, values in sorted(reason_codes.items())
    }
    if (
        not isinstance(rubric, dict)
        or set(rubric) != {"accept", "tighten", "reason_codes"}
        or not isinstance(rubric.get("accept"), str)
        or not rubric["accept"].strip()
        or not isinstance(rubric.get("tighten"), str)
        or not rubric["tighten"].strip()
        or rubric.get("reason_codes") != expected_reason_codes
    ):
        raise PanelReviewError("packet rubric is invalid")

    content_targets = packet.get("content_targets")
    if not isinstance(content_targets, list):
        raise PanelReviewError("packet.content_targets must be an array")
    content_paths: list[str] = []
    for index, target in enumerate(content_targets):
        target_fields = (
            LEGACY_CONTENT_TARGET_FIELDS
            if legacy_thin_content
            else CONTENT_TARGET_FIELDS
        )
        if not isinstance(target, dict) or set(target) != target_fields:
            raise PanelReviewError(f"packet content target {index} is invalid")
        path = _non_blank(target.get("path"), label=f"content target {index}.path")
        _canonical_relative_path(path, label=f"content target {index}.path")
        if target.get("classification") not in {"REVIEW_DENSITY", "TIGHTEN_BODY"}:
            raise PanelReviewError(f"packet content target {index} class is invalid")
        _non_blank(
            target.get("review_state"), label=f"content target {index}.review_state"
        )
        reasons = target.get("review_reasons")
        if not isinstance(reasons, list) or not reasons or not all(
            isinstance(item, str) and item.strip() for item in reasons
        ):
            raise PanelReviewError(
                f"packet content target {index}.review_reasons is invalid"
            )
        if not legacy_thin_content:
            if target.get("document_id") != f"{path}#body":
                raise PanelReviewError(
                    f"packet content target {index} document_id is invalid"
                )
            _non_blank(
                target.get("owner"), label=f"content target {index}.owner"
            )
            if target.get("document_part") != "body":
                raise PanelReviewError(
                    f"packet content target {index} document_part is invalid"
                )
            selector = target.get("source_selector")
            if selector != {"kind": "yaml-body", "path": path}:
                raise PanelReviewError(
                    f"packet content target {index} source_selector is invalid"
                )
            context = _validate_readability_context(
                target.get("document_context"),
                label=f"content target {index}.document_context",
            )
            fingerprint = _lowercase_sha256(
                target.get("content_fingerprint"),
                label=f"content target {index}.content_fingerprint",
            )
            if fingerprint != context["sha256"]:
                raise PanelReviewError(
                    f"packet content target {index} content fingerprint is stale"
                )
        content_paths.append(path)
    if content_paths != sorted(set(content_paths)):
        raise PanelReviewError("packet content targets must be path-sorted and unique")

    readability_targets = packet.get("readability_targets")
    if not isinstance(readability_targets, list):
        raise PanelReviewError("packet.readability_targets must be an array")
    document_ids: list[str] = []
    for index, target in enumerate(readability_targets):
        target_fields = (
            {
                "document_id",
                "path",
                "surface",
                "document_part",
                "content_fingerprint",
                "highest_band",
                "findings",
            }
            if schema_version == SCHEMA_VERSION
            else READABILITY_V2_TARGET_FIELDS
        )
        if not isinstance(target, dict) or set(target) != target_fields:
            raise PanelReviewError(f"packet readability target {index} is invalid")
        document_id = _non_blank(
            target.get("document_id"),
            label=f"readability target {index}.document_id",
        )
        path = _non_blank(target.get("path"), label=f"readability target {index}.path")
        _canonical_relative_path(path, label=f"readability target {index}.path")
        document_part = _non_blank(
            target.get("document_part"),
            label=f"readability target {index}.document_part",
        )
        _non_blank(
            target.get("surface"), label=f"readability target {index}.surface"
        )
        if schema_version == SCHEMA_VERSION and document_id != f"{path}#{document_part}":
            raise PanelReviewError(
                f"packet readability target {index} identity is inconsistent"
            )
        if schema_version == READABILITY_SCHEMA_VERSION:
            owner = _non_blank(
                target.get("owner"), label=f"readability target {index}.owner"
            )
            selector = target.get("source_selector")
            selector_kind = (
                selector.get("kind") if isinstance(selector, dict) else None
            )
            selector_fields = READABILITY_SOURCE_SELECTOR_FIELDS_BY_KIND.get(
                selector_kind
            )
            if (
                not isinstance(selector, dict)
                or selector_fields is None
                or set(selector) != selector_fields
                or selector.get("path") != path
            ):
                raise PanelReviewError(
                    f"packet readability target {index} source_selector is invalid"
                )
            if selector_kind == "json-profile-field":
                if (
                    selector.get("profile_name") != owner
                    or selector.get("field") != document_part
                    or document_id != f"{path}#{owner}#{document_part}"
                ):
                    raise PanelReviewError(
                        f"packet readability target {index} profile identity is inconsistent"
                    )
            elif document_id != f"{path}#{document_part}":
                raise PanelReviewError(
                    f"packet readability target {index} identity is inconsistent"
                )
            if selector_kind == "yaml-description" and selector.get("field") != (
                document_part
            ):
                raise PanelReviewError(
                    f"packet readability target {index} description selector is stale"
                )
        fingerprint = target.get("content_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(
            char not in "0123456789abcdef" for char in fingerprint
        ):
            raise PanelReviewError(
                f"packet readability target {index} fingerprint is invalid"
            )
        context: dict[str, Any] | None = None
        if schema_version == READABILITY_SCHEMA_VERSION:
            context = _validate_readability_context(
                target.get("document_context"),
                label=f"readability target {index}.document_context",
            )
            if fingerprint != context["sha256"]:
                raise PanelReviewError(
                    f"packet readability target {index} content fingerprint is stale"
                )
        if target.get("highest_band") not in {"review-as-complex", "tighten"}:
            raise PanelReviewError(
                f"packet readability target {index} advisory band is invalid"
            )
        findings = target.get("findings")
        if not isinstance(findings, list) or not findings:
            raise PanelReviewError(
                f"packet readability target {index} findings are required"
            )
        finding_order: list[tuple[Any, ...]] = []
        finding_identity_occurrences: dict[tuple[str, str], int] = {}
        for finding_index, finding in enumerate(findings):
            finding_fields = (
                {
                    "line",
                    "band",
                    "words",
                    "kind",
                    "sentence_fingerprint",
                    "source_line",
                }
                if schema_version == SCHEMA_VERSION
                else READABILITY_V2_FINDING_FIELDS
            )
            if not isinstance(finding, dict) or set(finding) != finding_fields:
                raise PanelReviewError(
                    f"packet readability target {index} finding {finding_index} is invalid"
                )
            line = finding.get("line")
            words = finding.get("words")
            if type(line) is not int or line < 1 or type(words) is not int or words < 1:
                raise PanelReviewError(
                    f"packet readability target {index} finding coordinates are invalid"
                )
            if finding.get("band") not in {"review-as-complex", "tighten"}:
                raise PanelReviewError(
                    f"packet readability target {index} finding band is invalid"
                )
            _non_blank(
                finding.get("kind"),
                label=f"readability target {index} finding {finding_index}.kind",
            )
            if schema_version == SCHEMA_VERSION and not isinstance(
                finding.get("source_line"), str
            ):
                raise PanelReviewError(
                    f"packet readability target {index} finding source_line must be a string"
                )
            sentence_fingerprint = finding.get("sentence_fingerprint")
            if (
                not isinstance(sentence_fingerprint, str)
                or len(sentence_fingerprint) != 64
                or any(
                    char not in "0123456789abcdef" for char in sentence_fingerprint
                )
            ):
                raise PanelReviewError(
                    f"packet readability target {index} finding fingerprint is invalid"
                )
            if schema_version == READABILITY_SCHEMA_VERSION:
                sentence = _non_blank(
                    finding.get("sentence"),
                    label=(
                        f"readability target {index} finding {finding_index}.sentence"
                    ),
                )
                expected_sentence_fingerprint = hashlib.sha256(
                    ("ai-readability-sentence-v1\0" + sentence).encode("utf-8")
                ).hexdigest()
                if sentence_fingerprint != expected_sentence_fingerprint:
                    raise PanelReviewError(
                        f"packet readability target {index} finding sentence fingerprint is stale"
                    )
                assert context is not None
                source_span = _validate_readability_source_span(
                    finding.get("source_span"),
                    context=context,
                    label=(
                        f"readability target {index} finding {finding_index}.source_span"
                    ),
                )
                if line != source_span["start_line"]:
                    raise PanelReviewError(
                        f"packet readability target {index} finding line is stale"
                    )
                finding_id = _lowercase_sha256(
                    finding.get("finding_id"),
                    label=(
                        f"readability target {index} finding {finding_index}.finding_id"
                    ),
                )
                normalized_sentence = (
                    panel_contracts.readability_normalized_visible_text(
                        sentence
                    )
                )
                occurrence_key = (
                    str(finding["kind"]), normalized_sentence
                )
                finding_identity_occurrences[occurrence_key] = (
                    finding_identity_occurrences.get(occurrence_key, 0) + 1
                )
                expected_finding_id = _readability_finding_id(
                    document_id=document_id,
                    kind=str(finding["kind"]),
                    sentence=sentence,
                    occurrence=finding_identity_occurrences[occurrence_key],
                )
                if finding_id != expected_finding_id:
                    raise PanelReviewError(
                        f"packet readability target {index} finding_id is stale"
                    )
                finding_order.append(
                    (
                        source_span["start_offset"],
                        source_span["end_offset"],
                        str(finding["kind"]),
                        finding_id,
                    )
                )
            else:
                finding_order.append((line, sentence_fingerprint))
        if finding_order != sorted(set(finding_order)):
            raise PanelReviewError(
                f"packet readability target {index} findings must be sorted and unique"
            )
        document_ids.append(document_id)
    if document_ids != sorted(set(document_ids)):
        raise PanelReviewError(
            "packet readability targets must be document-sorted and unique"
        )

    if (
        schema_version == READABILITY_SCHEMA_VERSION
        and validation_mode == VALIDATION_MODE_CURRENT
    ):
        (
            current_fingerprints,
            current_content_targets,
            current_targets,
            current_actionability_targets,
        ) = (
            _current_readability_target_projection()
        )
        if packet["source_fingerprints"] != current_fingerprints:
            raise PanelReviewError(
                "schema-2 readability packet target or detector authority is stale"
            )
        packet_manifest = _readability_target_manifest_projection(
            content_targets=content_targets,
            readability_targets=readability_targets,
            actionability_targets=packet.get("actionability_targets", []),
        )
        current_manifest = _readability_target_manifest_projection(
            content_targets=current_content_targets,
            readability_targets=current_targets,
            actionability_targets=current_actionability_targets,
        )
        if packet_manifest != current_manifest:
            raise PanelReviewError(
                "schema-2 readability normalized target bindings are stale"
            )
        if packet["source_fingerprints"]["readability_target_manifest"] != (
            _canonical_json_sha256(packet_manifest)
        ):
            raise PanelReviewError(
                "schema-2 readability target manifest is internally stale"
            )

    if schema_version == READABILITY_SCHEMA_VERSION:
        actionability_targets = packet.get("actionability_targets")
        if not isinstance(actionability_targets, list):
            raise PanelReviewError("packet.actionability_targets must be an array")
        actionability_ids: list[str] = []
        threshold = contract["actionability_score_threshold"]
        window_limit = contract["actionability_front_window_lines"]
        for index, target in enumerate(actionability_targets):
            label = f"actionability target {index}"
            if not isinstance(target, dict) or set(target) != ACTIONABILITY_TARGET_FIELDS:
                raise PanelReviewError(f"packet {label} fields are invalid")
            path = _non_blank(target.get("path"), label=f"{label}.path")
            _canonical_relative_path(path, label=f"{label}.path")
            target_id = _non_blank(
                target.get("target_id"), label=f"{label}.target_id"
            )
            if target_id != _actionability_target_id(path):
                raise PanelReviewError(f"packet {label} target_id is invalid")
            _non_blank(target.get("skill_id"), label=f"{label}.skill_id")
            _non_blank(target.get("kind"), label=f"{label}.kind")
            _non_blank(
                target.get("actionability_model"),
                label=f"{label}.actionability_model",
            )
            _non_blank(target.get("review_state"), label=f"{label}.review_state")
            score = target.get("front_loaded_action_score")
            if type(score) is not int or not 0 <= score <= 100:
                raise PanelReviewError(f"packet {label} score is invalid")
            _lowercase_sha256(
                target.get("content_fingerprint"),
                label=f"{label}.content_fingerprint",
            )
            _validate_actionability_front_window(
                target.get("front_window"),
                label=f"packet {label} front_window",
                limit=window_limit,
            )
            actionability_ids.append(target_id)
        if actionability_ids != sorted(set(actionability_ids)):
            raise PanelReviewError(
                "packet actionability targets must be target-sorted and unique"
            )
        if contract["required_actionability_target_count"] != len(
            actionability_targets
        ):
            raise PanelReviewError(
                "packet actionability target count does not match panel contract"
            )

    limitations = packet.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError("packet.limitations must be a non-empty string array")


def _lowercase_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise PanelReviewError(f"{label} must be lowercase sha256")
    return value


def _validate_file_record(value: object, *, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise PanelReviewError(f"{label} must contain path and sha256")
    path = _non_blank(value.get("path"), label=f"{label}.path")
    _canonical_relative_path(path, label=f"{label}.path")
    _lowercase_sha256(value.get("sha256"), label=f"{label}.sha256")
    return value


def _validate_professional_completeness_packet_v1(packet: dict[str, Any]) -> None:
    if set(packet) != PROFESSIONAL_PACKET_FIELDS:
        raise PanelReviewError(
            "professional completeness packet fields do not match schema 1"
        )
    if (
        packet.get("schema_version") != SCHEMA_VERSION
        or packet.get("kind") != PROFESSIONAL_COMPLETENESS_PACKET_KIND
    ):
        raise PanelReviewError(
            "professional completeness packet schema or kind is invalid"
        )
    _non_blank(packet.get("review_id"), label="packet.review_id")
    _iso_date(packet.get("created_on"), label="packet.created_on")
    contract = packet.get("panel_contract")
    target_count = (
        contract.get("required_target_count")
        if isinstance(contract, dict)
        else None
    )
    if type(target_count) is not int or target_count not in {
        PROFESSIONAL_LEGACY_PACKAGE_COUNT,
        PROFESSIONAL_PACKAGE_COUNT,
    }:
        raise PanelReviewError(
            "professional completeness packet panel_contract is invalid"
        )
    expected_contract = {
        "decision_method": DECISION_METHOD,
        "required_voters": PANEL_SIZE,
        "abstentions_allowed": False,
        "minimum_winning_votes": 2,
        "independent_ballots": True,
        "required_target_count": target_count,
        "criteria_required_per_target": sorted(PROFESSIONAL_COMPLETENESS_CRITERIA),
    }
    if contract != expected_contract:
        raise PanelReviewError(
            "professional completeness packet panel_contract is invalid"
        )
    rubric = packet.get("rubric")
    expected_reason_codes = {
        decision: sorted(PROFESSIONAL_REASON_CODES[decision])
        for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
    }
    if (
        not isinstance(rubric, dict)
        or set(rubric) != {"accept", "correct", "criteria", "reason_codes"}
        or not isinstance(rubric.get("accept"), str)
        or not rubric["accept"].strip()
        or not isinstance(rubric.get("correct"), str)
        or not rubric["correct"].strip()
        or rubric.get("criteria")
        != dict(sorted(PROFESSIONAL_COMPLETENESS_CRITERIA.items()))
        or rubric.get("reason_codes") != expected_reason_codes
    ):
        raise PanelReviewError("professional completeness packet rubric is invalid")

    targets = packet.get("professional_targets")
    if not isinstance(targets, list) or len(targets) != target_count:
        raise PanelReviewError(
            "professional completeness packet must cover exactly "
            f"{target_count} packages"
        )
    skill_ids: list[str] = []
    layer_counts = {"professional": 0, "foundation": 0, "domain": 0}
    responsibility_fields = {
        "role_support",
        "trigger_signals",
        "anti_trigger_signals",
        "required_inputs",
        "output_contract",
        "escalation_signals",
        "layer3_candidates",
        "used_by",
        "boundary_signals",
        "group",
        "content_class",
        "delivery_scope",
        "task_routable",
    }
    for index, target in enumerate(targets):
        label = f"professional_targets[{index}]"
        if not isinstance(target, dict) or set(target) != {
            "skill_id",
            "layer",
            "root",
            "indexed_references",
            "registry",
            "routing_adjacency",
            "package_fingerprint",
        }:
            raise PanelReviewError(f"{label} fields are invalid")
        skill_id = _non_blank(target.get("skill_id"), label=f"{label}.skill_id")
        layer = target.get("layer")
        if layer not in layer_counts:
            raise PanelReviewError(f"{label}.layer is invalid")
        layer_counts[layer] += 1
        _validate_file_record(target.get("root"), label=f"{label}.root")
        references = target.get("indexed_references")
        if not isinstance(references, list):
            raise PanelReviewError(f"{label}.indexed_references must be an array")
        reference_paths: list[str] = []
        for reference_index, reference in enumerate(references):
            normalized = _validate_file_record(
                reference,
                label=f"{label}.indexed_references[{reference_index}]",
            )
            reference_paths.append(normalized["path"])
        if reference_paths != sorted(set(reference_paths)):
            raise PanelReviewError(
                f"{label}.indexed_references must be path-sorted and unique"
            )
        registry = target.get("registry")
        if not isinstance(registry, dict) or set(registry) not in (
            {"path", "responsibility_contract"},
            {"path", "entry_fingerprint", "responsibility_contract"},
        ):
            raise PanelReviewError(f"{label}.registry fields are invalid")
        registry_path = _non_blank(
            registry.get("path"), label=f"{label}.registry.path"
        )
        _canonical_relative_path(registry_path, label=f"{label}.registry.path")
        responsibility = registry.get("responsibility_contract")
        if not isinstance(responsibility, dict) or set(responsibility) != responsibility_fields:
            raise PanelReviewError(f"{label}.registry.responsibility_contract is invalid")
        for field in (
            "role_support",
            "trigger_signals",
            "anti_trigger_signals",
            "required_inputs",
            "output_contract",
            "escalation_signals",
        ):
            _string_list(
                responsibility.get(field),
                label=f"{label}.registry.responsibility_contract.{field}",
                allow_empty=False,
            )
        for field in ("layer3_candidates", "used_by", "boundary_signals"):
            _string_list(
                responsibility.get(field),
                label=f"{label}.registry.responsibility_contract.{field}",
            )
        adjacency = target.get("routing_adjacency")
        if not isinstance(adjacency, dict) or set(adjacency) != {"skills", "fingerprint"}:
            raise PanelReviewError(f"{label}.routing_adjacency fields are invalid")
        adjacent_skills = _string_list(
            adjacency.get("skills"), label=f"{label}.routing_adjacency.skills"
        )
        if adjacent_skills != sorted(set(adjacent_skills)) or skill_id in adjacent_skills:
            raise PanelReviewError(
                f"{label}.routing_adjacency.skills must be sorted, unique, and exclude self"
            )
        routing_basis = {
            "skill_id": skill_id,
            "layer": layer,
            "role_support": responsibility["role_support"],
            "trigger_signals": responsibility["trigger_signals"],
            "anti_trigger_signals": responsibility["anti_trigger_signals"],
            "output_contract": responsibility["output_contract"],
            "adjacent_skills": adjacent_skills,
        }
        if adjacency.get("fingerprint") != _canonical_json_sha256(routing_basis):
            raise PanelReviewError(f"{label}.routing_adjacency fingerprint is stale")
        fingerprint = _lowercase_sha256(
            target.get("package_fingerprint"), label=f"{label}.package_fingerprint"
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        if fingerprint != _canonical_json_sha256(without_fingerprint):
            raise PanelReviewError(f"{label}.package_fingerprint is stale")
        skill_ids.append(skill_id)
    if skill_ids != sorted(set(skill_ids)):
        raise PanelReviewError(
            "professional completeness targets must be skill-sorted and unique"
        )
    expected_layer_counts = (
        PROFESSIONAL_LEGACY_LAYER_COUNTS
        if target_count == PROFESSIONAL_LEGACY_PACKAGE_COUNT
        else PROFESSIONAL_CURRENT_LAYER_COUNTS
    )
    if (
        any(type(value) is not int for value in layer_counts.values())
        or any(
            type(value) is not int
            for value in expected_layer_counts.values()
        )
        or layer_counts != expected_layer_counts
    ):
        raise PanelReviewError(
            "professional completeness target layers do not match "
            f"the {target_count}-package schema-1 inventory"
        )
    target_names = set(skill_ids)
    for index, target in enumerate(targets):
        unknown = set(target["routing_adjacency"]["skills"]) - target_names
        if unknown:
            raise PanelReviewError(
                f"professional_targets[{index}] names unknown adjacent Skills: "
                + ", ".join(sorted(unknown))
            )
    fingerprints = packet.get("source_fingerprints")
    expected_fingerprints = {
        "professional_packages": _canonical_json_sha256(targets)
    }
    if fingerprints != expected_fingerprints:
        raise PanelReviewError(
            "professional completeness source fingerprint is stale"
        )
    limitations = packet.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError(
            "professional completeness limitations must be a non-empty string array"
        )


def _validate_review_material_record(
    value: object, *, label: str
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "path",
        "sha256",
        "line_count",
        "content",
    }:
        raise PanelReviewError(
            f"{label} must contain path, sha256, line_count, and content"
        )
    path = _non_blank(value.get("path"), label=f"{label}.path")
    _canonical_relative_path(path, label=f"{label}.path")
    digest = _lowercase_sha256(value.get("sha256"), label=f"{label}.sha256")
    content = value.get("content")
    if not isinstance(content, str):
        raise PanelReviewError(f"{label}.content must be UTF-8 text")
    try:
        encoded = content.encode("utf-8")
    except UnicodeError as exc:
        raise PanelReviewError(f"{label}.content must be UTF-8 text") from exc
    if hashlib.sha256(encoded).hexdigest() != digest:
        raise PanelReviewError(f"{label}.content does not match sha256")
    line_count = value.get("line_count")
    if type(line_count) is not int or line_count < 1:
        raise PanelReviewError(f"{label}.line_count must be a positive integer")
    if line_count != len(content.splitlines()):
        raise PanelReviewError(f"{label}.line_count does not match content")
    return value


def _professional_package_profile(
    target_count: int,
    *,
    validation_mode: str,
) -> tuple[dict[str, int], bool]:
    validation_mode = _closed_validation_mode(validation_mode)
    if target_count == PROFESSIONAL_PACKAGE_COUNT:
        return PROFESSIONAL_CURRENT_LAYER_COUNTS, False
    if (
        validation_mode == VALIDATION_MODE_HISTORICAL
        and target_count == PROFESSIONAL_LEGACY_PACKAGE_COUNT
    ):
        return PROFESSIONAL_LEGACY_LAYER_COUNTS, True
    if validation_mode == VALIDATION_MODE_CURRENT:
        raise PanelReviewError(
            "professional completeness packet must cover exactly "
            f"{PROFESSIONAL_PACKAGE_COUNT} packages"
        )
    raise PanelReviewError(
        "professional completeness packet target count is not supported "
        f"for {validation_mode} validation"
    )


def _validate_professional_completeness_packet_v2(
    packet: dict[str, Any],
    *,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> None:
    validation_mode = _closed_validation_mode(validation_mode)
    if set(packet) != PROFESSIONAL_PACKET_FIELDS:
        raise PanelReviewError(
            "professional completeness packet fields do not match schema 2"
        )
    if (
        packet.get("schema_version") != PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION
        or packet.get("kind") != PROFESSIONAL_COMPLETENESS_PACKET_KIND
    ):
        raise PanelReviewError(
            "professional completeness packet schema or kind is invalid"
        )
    _non_blank(packet.get("review_id"), label="packet.review_id")
    _iso_date(packet.get("created_on"), label="packet.created_on")
    targets = packet.get("professional_targets")
    target_count = len(targets) if isinstance(targets, list) else -1
    expected_layer_counts, legacy_selection = _professional_package_profile(
        target_count,
        validation_mode=validation_mode,
    )
    expected_contract = _professional_completeness_panel_contract(
        target_count=target_count,
        include_selection_derivation=not legacy_selection,
    )
    packet_selection = (
        packet.get("panel_contract", {})
        .get("adjacency_contract", {})
        .get("required_candidate_selection")
    )
    if isinstance(packet_selection, _ProfessionalSchema3RegisteredSelection):
        expected_contract["adjacency_contract"][
            "required_candidate_selection"
        ] = copy.deepcopy(packet_selection)
    if packet.get("panel_contract") != expected_contract:
        raise PanelReviewError(
            "professional completeness packet panel_contract is invalid"
        )
    rubric = packet.get("rubric")
    expected_reason_codes = {
        decision: sorted(PROFESSIONAL_REASON_CODES[decision])
        for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
    }
    if (
        not isinstance(rubric, dict)
        or set(rubric) != {"accept", "correct", "criteria", "reason_codes"}
        or not isinstance(rubric.get("accept"), str)
        or not rubric["accept"].strip()
        or not isinstance(rubric.get("correct"), str)
        or not rubric["correct"].strip()
        or rubric.get("criteria")
        != dict(sorted(PROFESSIONAL_COMPLETENESS_CRITERIA.items()))
        or rubric.get("reason_codes") != expected_reason_codes
    ):
        raise PanelReviewError("professional completeness packet rubric is invalid")

    if not isinstance(targets, list):
        raise PanelReviewError(
            "professional completeness packet targets must be an array"
        )
    skill_ids: list[str] = []
    layer_counts = {"professional": 0, "foundation": 0, "domain": 0}
    responsibility_fields = {
        "role_support",
        "trigger_signals",
        "anti_trigger_signals",
        "required_inputs",
        "output_contract",
        "escalation_signals",
        "layer3_candidates",
        "used_by",
        "boundary_signals",
        "group",
        "content_class",
        "delivery_scope",
        "task_routable",
    }
    historical_target_fields = {
        "skill_id",
        "layer",
        "required_expertise_tags",
        "root",
        "indexed_references",
        "registry",
        "routing_adjacency",
        "package_fingerprint",
    }
    current_target_fields = {
        *historical_target_fields,
        "registry_authority",
        "reference_authority",
    }
    for index, target in enumerate(targets):
        label = f"professional_targets[{index}]"
        if not isinstance(target, dict) or set(target) not in {
            frozenset(historical_target_fields),
            frozenset(current_target_fields),
        }:
            raise PanelReviewError(f"{label} fields are invalid")
        has_current_authority = set(target) == current_target_fields
        skill_id = _non_blank(target.get("skill_id"), label=f"{label}.skill_id")
        layer = target.get("layer")
        if layer not in layer_counts:
            raise PanelReviewError(f"{label}.layer is invalid")
        layer_counts[layer] += 1
        _expertise_tags(
            target.get("required_expertise_tags"),
            label=f"{label}.required_expertise_tags",
            allow_architecture=False,
            allow_historical=(
                validation_mode == VALIDATION_MODE_HISTORICAL
            ),
        )
        _validate_review_material_record(target.get("root"), label=f"{label}.root")
        references = target.get("indexed_references")
        if not isinstance(references, list):
            raise PanelReviewError(f"{label}.indexed_references must be an array")
        reference_paths: list[str] = []
        for reference_index, reference in enumerate(references):
            normalized = _validate_review_material_record(
                reference,
                label=f"{label}.indexed_references[{reference_index}]",
            )
            reference_paths.append(normalized["path"])
        if reference_paths != sorted(set(reference_paths)):
            raise PanelReviewError(
                f"{label}.indexed_references must be path-sorted and unique"
            )
        registry = target.get("registry")
        if not isinstance(registry, dict) or set(registry) not in (
            {"path", "responsibility_contract"},
            {"path", "entry_fingerprint", "responsibility_contract"},
        ):
            raise PanelReviewError(f"{label}.registry fields are invalid")
        registry_path = _non_blank(
            registry.get("path"), label=f"{label}.registry.path"
        )
        _canonical_relative_path(registry_path, label=f"{label}.registry.path")
        responsibility = registry.get("responsibility_contract")
        if (
            not isinstance(responsibility, dict)
            or set(responsibility) != responsibility_fields
        ):
            raise PanelReviewError(
                f"{label}.registry.responsibility_contract is invalid"
            )
        for field in (
            "role_support",
            "trigger_signals",
            "anti_trigger_signals",
            "required_inputs",
            "output_contract",
            "escalation_signals",
        ):
            _string_list(
                responsibility.get(field),
                label=f"{label}.registry.responsibility_contract.{field}",
                allow_empty=False,
            )
        for field in ("layer3_candidates", "used_by", "boundary_signals"):
            _string_list(
                responsibility.get(field),
                label=f"{label}.registry.responsibility_contract.{field}",
            )
        if has_current_authority:
            try:
                professional_carry.professional_registry_authority_binding(
                    target
                )
                professional_carry.professional_reference_authority_binding(
                    target
                )
            except professional_carry.ProfessionalCarryForwardError as exc:
                raise PanelReviewError(
                    f"{label} current Registry or Reference authority is invalid"
                ) from exc
        fingerprint = _lowercase_sha256(
            target.get("package_fingerprint"),
            label=f"{label}.package_fingerprint",
        )
        expected_fingerprint = (
            _canonical_json_sha256(
                professional_carry.professional_candidate_material_binding(
                    target
                )
            )
            if "entry_fingerprint" not in registry
            else _canonical_json_sha256(
                {
                    key: value
                    for key, value in target.items()
                    if key != "package_fingerprint"
                }
            )
        )
        if fingerprint != expected_fingerprint:
            raise PanelReviewError(f"{label}.package_fingerprint is stale")
        skill_ids.append(skill_id)
    if skill_ids != sorted(set(skill_ids)):
        raise PanelReviewError(
            "professional completeness targets must be skill-sorted and unique"
        )
    if layer_counts != expected_layer_counts:
        raise PanelReviewError(
            "professional completeness target layers do not match its "
            "supported package profile"
        )

    target_names = set(skill_ids)
    historical_aliases = all(
        "entry_fingerprint" in target["registry"] for target in targets
    ) and all(
        "required_candidates_fingerprint" in target["routing_adjacency"]
        for target in targets
    )
    bases, document_frequency_filter = (
        _professional_catalog_adjacency_features(
            targets,
            include_historical_alias=historical_aliases,
        )
    )
    for index, target in enumerate(targets):
        label = f"professional_targets[{index}].routing_adjacency"
        adjacency = target.get("routing_adjacency")
        historical_v1_selection = (
            isinstance(adjacency, dict)
            and isinstance(
                adjacency.get("required_candidate_selection"),
                _ProfessionalHistoricalV1Selection,
            )
        )
        expected_fields = {
            "algorithm",
            "document_frequency_filter",
            "declared_skills",
            "registry_declared_skills",
            "source_declared_skills",
            "required_candidate_selection",
            "required_candidates",
            "full_catalog_count",
            "full_catalog_ranking",
        }
        if historical_aliases:
            expected_fields.update(
                {
                    "required_candidates_fingerprint",
                    "full_catalog_ranking_fingerprint",
                }
            )
        if historical_v1_selection:
            expected_fields.remove("registry_declared_skills")
            expected_fields.remove("source_declared_skills")
        if not isinstance(adjacency, dict) or set(adjacency) != expected_fields:
            raise PanelReviewError(f"{label} fields are invalid")
        if adjacency.get("algorithm") != PROFESSIONAL_ADJACENCY_ALGORITHM:
            raise PanelReviewError(f"{label}.algorithm is invalid")
        if adjacency.get("document_frequency_filter") != document_frequency_filter:
            raise PanelReviewError(
                f"{label}.document_frequency_filter is stale"
            )
        registry_declared = _string_list(
            adjacency.get(
                "declared_skills"
                if historical_v1_selection
                else "registry_declared_skills"
            ),
            label=(
                f"{label}.declared_skills"
                if historical_v1_selection
                else f"{label}.registry_declared_skills"
            ),
        )
        source_declared = (
            []
            if historical_v1_selection
            else _string_list(
                adjacency.get("source_declared_skills"),
                label=f"{label}.source_declared_skills",
            )
        )
        if (
            registry_declared != sorted(set(registry_declared))
            or source_declared != sorted(set(source_declared))
            or target["skill_id"] in registry_declared
            or target["skill_id"] in source_declared
        ):
            raise PanelReviewError(
                f"{label} declarations must be sorted, unique, and exclude self"
            )
        declared_union = sorted(
            set(registry_declared) | set(source_declared)
        )
        if adjacency.get("declared_skills") != declared_union:
            raise PanelReviewError(f"{label}.declared_skills is stale")
        unknown = (set(registry_declared) | set(source_declared)) - target_names
        if unknown:
            raise PanelReviewError(
                f"{label} declarations name unknown packages: "
                + ", ".join(sorted(unknown))
            )
        if not historical_v1_selection:
            expected_source_declared = _professional_source_declared_skill_ids(
                target,
                known_skill_ids=target_names,
            )
            if source_declared != expected_source_declared:
                raise PanelReviewError(
                    f"{label}.source_declared_skills is stale"
                )
        ranking = _professional_catalog_ranking(target["skill_id"], bases=bases)
        if adjacency.get("full_catalog_count") != len(ranking):
            raise PanelReviewError(f"{label}.full_catalog_count is invalid")
        embedded_ranking = adjacency.get("full_catalog_ranking")
        if embedded_ranking != ranking:
            raise PanelReviewError(
                f"{label}.full_catalog_ranking is stale"
            )
        if historical_aliases and adjacency.get(
            "full_catalog_ranking_fingerprint"
        ) != _canonical_json_sha256(embedded_ranking):
            raise PanelReviewError(
                f"{label}.full_catalog_ranking_fingerprint is stale"
            )
        selection_contract = expected_contract["adjacency_contract"][
            "required_candidate_selection"
        ]
        if adjacency.get("required_candidate_selection") != selection_contract:
            raise PanelReviewError(
                f"{label}.required_candidate_selection is stale"
            )
        expected_candidates = _professional_required_adjacency_candidates(
            ranking,
            registry_declared_skills=registry_declared,
            source_declared_skills=source_declared,
            overall_top_k=selection_contract.get("overall_top_k"),
            per_signal_top_k=selection_contract.get("per_signal_top_k"),
        )
        candidates = adjacency.get("required_candidates")
        if candidates != expected_candidates:
            raise PanelReviewError(
                f"{label}.required_candidates do not match canonical layered selection"
            )
        if historical_aliases and adjacency.get(
            "required_candidates_fingerprint"
        ) != _canonical_json_sha256(candidates):
            raise PanelReviewError(
                f"{label}.required_candidates_fingerprint is stale"
            )
        for candidate_index, candidate in enumerate(candidates):
            if (
                not isinstance(candidate, dict)
                or set(candidate) != PROFESSIONAL_ADJACENCY_CANDIDATE_FIELDS
            ):
                raise PanelReviewError(
                    f"{label}.required_candidates[{candidate_index}] fields are invalid"
                )
        for ranking_index, ranking_item in enumerate(embedded_ranking):
            ranking_label = f"{label}.full_catalog_ranking[{ranking_index}]"
            if (
                not isinstance(ranking_item, dict)
                or set(ranking_item) != PROFESSIONAL_ADJACENCY_RANKING_FIELDS
            ):
                raise PanelReviewError(f"{ranking_label} fields are invalid")
            signals = ranking_item.get("signals")
            if (
                not isinstance(signals, dict)
                or set(signals) != set(PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS)
            ):
                raise PanelReviewError(f"{ranking_label}.signals are invalid")
            for signal_name, signal in signals.items():
                if (
                    not isinstance(signal, dict)
                    or set(signal) != PROFESSIONAL_ADJACENCY_SIGNAL_FIELDS
                    or signal.get("weight")
                    != PROFESSIONAL_ADJACENCY_SIGNAL_WEIGHTS[signal_name]
                    or type(signal.get("count")) is not int
                    or signal["count"] < 0
                    or not isinstance(signal.get("matched_tokens"), list)
                    or signal["matched_tokens"]
                    != sorted(set(signal["matched_tokens"]))
                    or signal["count"] != len(signal["matched_tokens"])
                ):
                    raise PanelReviewError(
                        f"{ranking_label}.signals.{signal_name} is invalid"
                    )

    _enforce_professional_adjacency_candidate_budget(targets)
    historical_budget = expected_contract["adjacency_contract"][
        "required_candidate_selection"
    ]["maximum_required_candidates_total"]
    if sum(
        len(target["routing_adjacency"]["required_candidates"])
        for target in targets
    ) > historical_budget:
        raise PanelReviewError(
            "professional completeness required candidates exceed the "
            "packet contract budget"
        )
    fingerprints = packet.get("source_fingerprints")
    if fingerprints != {
        "professional_packages": _canonical_json_sha256(targets)
    }:
        raise PanelReviewError(
            "professional completeness source fingerprint is stale"
        )
    limitations = packet.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError(
            "professional completeness limitations must be a non-empty string array"
        )


def _validate_professional_completeness_packet(
    packet: dict[str, Any],
    *,
    validation_root: Path = ROOT,
    artifact_path: Path | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> None:
    validation_mode = _closed_validation_mode(validation_mode)
    schema_version = packet.get("schema_version")
    if schema_version == SCHEMA_VERSION:
        _validate_professional_completeness_packet_v1(packet)
        return
    if schema_version == PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION:
        _validate_professional_completeness_packet_v2(
            packet,
            validation_mode=validation_mode,
        )
        return
    if schema_version == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION:
        _validate_professional_completeness_packet_v3(
            packet,
            validation_root=validation_root,
            artifact_path=artifact_path,
            validation_mode=validation_mode,
        )
        return
    raise PanelReviewError(
        "professional completeness packet schema version is unsupported"
    )


def _validate_semantic_disposition_packet(packet: dict[str, Any]) -> None:
    if set(packet) != SEMANTIC_PACKET_FIELDS:
        raise PanelReviewError("semantic disposition packet fields do not match schema 2")
    if (
        packet.get("schema_version") != SEMANTIC_DISPOSITION_SCHEMA_VERSION
        or packet.get("kind") != SEMANTIC_DISPOSITION_PACKET_KIND
    ):
        raise PanelReviewError("semantic disposition packet schema or kind is invalid")
    _non_blank(packet.get("review_id"), label="packet.review_id")
    _iso_date(packet.get("created_on"), label="packet.created_on")
    fingerprints = packet.get("source_fingerprints")
    if not isinstance(fingerprints, dict) or set(fingerprints) != (
        SEMANTIC_SOURCE_FINGERPRINT_KEYS
    ):
        raise PanelReviewError(
            "semantic disposition source_fingerprints do not cover every evidence axis"
        )
    for key, value in fingerprints.items():
        _lowercase_sha256(value, label=f"packet.source_fingerprints.{key}")

    provenance = packet.get("candidate_provenance")
    if not isinstance(provenance, dict) or set(provenance) != SEMANTIC_AXES:
        raise PanelReviewError(
            "semantic disposition candidate_provenance must cover Root and Reference"
        )
    normalized_provenance: dict[str, dict[str, Any]] = {}
    for axis in sorted(SEMANTIC_AXES):
        value = provenance.get(axis)
        if not isinstance(value, dict) or set(value) != SEMANTIC_PROVENANCE_FIELDS:
            raise PanelReviewError(
                f"semantic disposition {axis} provenance fields are invalid"
            )
        count_fields = {
            "raw_candidate_count",
            "eligible_candidate_count",
            "detector_downgraded_count",
            "configured_entry_count",
            "exact_carry_forward_count",
            "review_target_count",
            "stale_old_count",
        }
        for field in count_fields:
            count = value.get(field)
            if type(count) is not int or count < 0:
                raise PanelReviewError(
                    f"semantic disposition {axis} provenance {field} is invalid"
                )
        list_fields = {
            "exact_carry_forward_candidate_ids",
            "review_target_candidate_ids",
            "same_id_stale_evidence_candidate_ids",
            "stale_old_candidate_ids",
        }
        for field in list_fields:
            identifiers = value.get(field)
            if not isinstance(identifiers, list) or identifiers != sorted(
                set(identifiers)
            ):
                raise PanelReviewError(
                    f"semantic disposition {axis} provenance {field} must be sorted and unique"
                )
            for identifier in identifiers:
                _lowercase_sha256(
                    identifier,
                    label=f"semantic disposition {axis} provenance {field}",
                )
        if value["raw_candidate_count"] != (
            value["eligible_candidate_count"] + value["detector_downgraded_count"]
        ):
            raise PanelReviewError(
                f"semantic disposition {axis} raw candidate accounting is invalid"
            )
        if value["eligible_candidate_count"] != (
            value["exact_carry_forward_count"] + value["review_target_count"]
        ):
            raise PanelReviewError(
                f"semantic disposition {axis} eligible candidate accounting is invalid"
            )
        if value["exact_carry_forward_count"] != len(
            value["exact_carry_forward_candidate_ids"]
        ) or value["review_target_count"] != len(
            value["review_target_candidate_ids"]
        ):
            raise PanelReviewError(
                f"semantic disposition {axis} carry-forward counts are invalid"
            )
        if value["stale_old_count"] != len(value["stale_old_candidate_ids"]):
            raise PanelReviewError(
                f"semantic disposition {axis} stale-old count is invalid"
            )
        if value["configured_entry_count"] != (
            value["exact_carry_forward_count"]
            + len(value["same_id_stale_evidence_candidate_ids"])
            + value["stale_old_count"]
        ):
            raise PanelReviewError(
                f"semantic disposition {axis} configured entry accounting is invalid"
            )
        exact = set(value["exact_carry_forward_candidate_ids"])
        review = set(value["review_target_candidate_ids"])
        same_id_stale = set(value["same_id_stale_evidence_candidate_ids"])
        stale_old = set(value["stale_old_candidate_ids"])
        if exact & review or exact & stale_old or review & stale_old:
            raise PanelReviewError(
                f"semantic disposition {axis} provenance ID sets overlap"
            )
        if not same_id_stale <= review:
            raise PanelReviewError(
                f"semantic disposition {axis} stale-evidence IDs must be review targets"
            )
        normalized_provenance[axis] = value

    targets = packet.get("semantic_targets")
    if not isinstance(targets, list):
        raise PanelReviewError("packet.semantic_targets must be an array")
    target_ids: list[str] = []
    axis_candidate_ids: dict[str, list[str]] = {axis: [] for axis in SEMANTIC_AXES}
    for index, target in enumerate(targets):
        label = f"semantic_targets[{index}]"
        if not isinstance(target, dict) or set(target) != SEMANTIC_TARGET_FIELDS:
            raise PanelReviewError(f"{label} fields are invalid")
        axis = target.get("axis")
        if axis not in SEMANTIC_AXES:
            raise PanelReviewError(f"{label}.axis is invalid")
        candidate = target.get("candidate")
        if not isinstance(candidate, dict):
            raise PanelReviewError(f"{label}.candidate must be an object")
        candidate_id = _lowercase_sha256(
            candidate.get("candidate_id"), label=f"{label}.candidate.candidate_id"
        )
        target_id = _non_blank(target.get("target_id"), label=f"{label}.target_id")
        if target_id != f"{axis}:{candidate_id}":
            raise PanelReviewError(f"{label}.target_id is inconsistent")
        mismatches = target.get("carry_forward_mismatches")
        if not isinstance(mismatches, list) or not mismatches or mismatches != sorted(
            set(mismatches)
        ) or not all(isinstance(item, str) and item.strip() for item in mismatches):
            raise PanelReviewError(
                f"{label}.carry_forward_mismatches must be non-empty, sorted, and unique"
            )
        if candidate.get("finding") is None or candidate.get("path") is None:
            raise PanelReviewError(f"{label}.candidate identity evidence is incomplete")
        occurrences = candidate.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            raise PanelReviewError(f"{label}.candidate occurrences are required")
        for occurrence_index, occurrence in enumerate(occurrences):
            if not isinstance(occurrence, dict):
                raise PanelReviewError(
                    f"{label}.candidate.occurrences[{occurrence_index}] is invalid"
                )
            path = _non_blank(
                occurrence.get("path"),
                label=f"{label}.candidate.occurrences[{occurrence_index}].path",
            )
            _canonical_relative_path(
                path,
                label=f"{label}.candidate.occurrences[{occurrence_index}].path",
            )
            lines = occurrence.get("lines")
            if (
                not isinstance(lines, dict)
                or set(lines) != {"start", "end"}
                or type(lines.get("start")) is not int
                or type(lines.get("end")) is not int
                or lines["start"] < 1
                or lines["end"] < lines["start"]
            ):
                raise PanelReviewError(
                    f"{label}.candidate.occurrences[{occurrence_index}].lines is invalid"
                )
            _non_blank(
                occurrence.get("preview"),
                label=f"{label}.candidate.occurrences[{occurrence_index}].preview",
            )
        if axis == "root":
            _lowercase_sha256(
                candidate.get("occurrence_fingerprint"),
                label=f"{label}.candidate.occurrence_fingerprint",
            )
            _lowercase_sha256(
                candidate.get("context_fingerprint"),
                label=f"{label}.candidate.context_fingerprint",
            )
            for occurrence_index, occurrence in enumerate(occurrences):
                _lowercase_sha256(
                    occurrence.get("context_fingerprint"),
                    label=(
                        f"{label}.candidate.occurrences[{occurrence_index}]"
                        ".context_fingerprint"
                    ),
                )
        elif candidate.get("path") == "group":
            _lowercase_sha256(
                candidate.get("evidence_fingerprint"),
                label=f"{label}.candidate.evidence_fingerprint",
            )
            _lowercase_sha256(
                candidate.get("content_fingerprint"),
                label=f"{label}.candidate.content_fingerprint",
            )
            member_paths = [str(occurrence["path"]) for occurrence in occurrences]
            if len(member_paths) < 2 or len(set(member_paths)) < 2:
                raise PanelReviewError(
                    f"{label}.candidate group requires complete multi-path membership"
                )
        expected_candidate_binding = _semantic_hash(
            {
                "review_evidence": candidate,
                "local_semantic_context": (
                    _semantic_candidate_current_binding(
                        axis=str(target["axis"]),
                        candidate=candidate,
                    )
                ),
            }
        )
        if target.get("candidate_binding_fingerprint") != expected_candidate_binding:
            raise PanelReviewError(f"{label}.candidate_binding_fingerprint is stale")
        target_ids.append(target_id)
        axis_candidate_ids[str(axis)].append(candidate_id)
    if target_ids != sorted(set(target_ids)):
        raise PanelReviewError("semantic disposition targets must be sorted and unique")
    for axis, identifiers in axis_candidate_ids.items():
        if identifiers != normalized_provenance[axis]["review_target_candidate_ids"]:
            raise PanelReviewError(
                f"semantic disposition {axis} targets do not match provenance"
            )

    contract = packet.get("panel_contract")
    expected_contract = _semantic_panel_contract(
        root_target_count=len(axis_candidate_ids["root"]),
        reference_target_count=len(axis_candidate_ids["reference"]),
    )
    if contract != expected_contract:
        raise PanelReviewError("semantic disposition packet panel_contract is invalid")
    rubric = packet.get("rubric")
    rubric_fields = {
        "exact_carry_forward",
        "rewrite",
        "valid_contextual_rule",
        "false_positive",
        "time_bounded_exception",
    }
    if not isinstance(rubric, dict) or set(rubric) != rubric_fields or not all(
        isinstance(value, str) and value.strip() for value in rubric.values()
    ):
        raise PanelReviewError("semantic disposition packet rubric is invalid")
    limitations = packet.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError(
            "semantic disposition packet limitations must be a non-empty string array"
        )


def _validate_semantic_packet_current(
    packet: dict[str, Any],
    audit: dict[str, Any],
    *,
    allowed_missing_target_ids: frozenset[str],
) -> dict[str, Any]:
    """Validate current evidence, with one explicit post-rewrite allowance.

    The ordinary packet contract passes an empty allowance. Decision application
    may allow only reviewed rewrite targets to disappear after their source rule
    has been changed. No new eligible candidate or other evidence drift is
    accepted.
    """

    _validate_semantic_disposition_packet(packet)
    root_semantic, reference_semantic = _semantic_audit_sections(audit)
    current_fingerprints = _semantic_source_fingerprints(
        audit,
        root_semantic=root_semantic,
        reference_semantic=reference_semantic,
    )
    if packet["source_fingerprints"] != current_fingerprints:
        raise PanelReviewError(
            "semantic disposition packet is stale against the current audit"
        )

    targets_by_axis: dict[str, dict[str, dict[str, Any]]] = {
        axis: {} for axis in SEMANTIC_AXES
    }
    for target in packet["semantic_targets"]:
        targets_by_axis[target["axis"]][target["candidate"]["candidate_id"]] = (
            target
        )
    all_target_ids = {
        target["target_id"] for target in packet["semantic_targets"]
    }
    if not allowed_missing_target_ids <= all_target_ids:
        raise PanelReviewError(
            "post-rewrite allowance names an unreviewed semantic target"
        )

    for axis, semantic in (
        ("root", root_semantic),
        ("reference", reference_semantic),
    ):
        candidates = semantic.get("candidates")
        contract = semantic.get("disposition_contract")
        entries = contract.get("entries") if isinstance(contract, dict) else None
        if not isinstance(candidates, list) or not all(
            isinstance(candidate, dict) for candidate in candidates
        ):
            raise PanelReviewError(
                f"semantic audit {axis} candidates must be an array"
            )
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise PanelReviewError(
                f"semantic audit {axis} disposition entries must be an array"
            )
        eligible = _semantic_eligible_candidates(axis=axis, semantic=semantic)
        current_by_id = {
            str(candidate.get("candidate_id")): candidate for candidate in eligible
        }
        if len(current_by_id) != len(eligible):
            raise PanelReviewError(
                f"semantic audit {axis} candidate IDs are missing or duplicated"
            )
        provenance = packet["candidate_provenance"][axis]
        reviewed_ids = sorted(
            [
                *provenance["exact_carry_forward_candidate_ids"],
                *provenance["review_target_candidate_ids"],
            ]
        )
        allowed_axis_ids = {
            target_id.split(":", 1)[1]
            for target_id in allowed_missing_target_ids
            if target_id.startswith(f"{axis}:")
        }
        missing_allowed_ids = allowed_axis_ids - set(current_by_id)
        expected_current_ids = sorted(set(reviewed_ids) - missing_allowed_ids)
        if expected_current_ids != sorted(current_by_id):
            raise PanelReviewError(
                "semantic disposition packet is stale against the current audit"
            )

        for candidate_id, target in targets_by_axis[axis].items():
            current = current_by_id.get(candidate_id)
            if current is None:
                if target["target_id"] in allowed_missing_target_ids:
                    continue
                raise PanelReviewError(
                    "semantic disposition packet is stale against the current audit"
                )
            packet_evidence = _semantic_candidate_current_binding(
                axis=axis, candidate=target["candidate"]
            )
            current_evidence = _semantic_candidate_current_binding(
                axis=axis, candidate=current
            )
            if packet_evidence != current_evidence:
                raise PanelReviewError(
                    "semantic disposition packet is stale against the current audit"
                )

        entries_by_id = {
            str(entry.get("candidate_id")): entry for entry in entries
        }
        for candidate_id in provenance["exact_carry_forward_candidate_ids"]:
            if _semantic_entry_mismatches(
                axis=axis,
                candidate=current_by_id[candidate_id],
                entry=entries_by_id.get(candidate_id),
            ):
                raise PanelReviewError(
                    "semantic disposition packet is stale against the current audit"
                )
    return packet


def validate_semantic_packet_current(
    packet: dict[str, Any], audit: dict[str, Any]
) -> dict[str, Any]:
    """Fail when reviewed semantic evidence no longer matches a fresh audit."""

    return _validate_semantic_packet_current(
        packet,
        audit,
        allowed_missing_target_ids=frozenset(),
    )


def validate_packet(
    packet: dict[str, Any],
    *,
    validation_root: Path = ROOT,
    artifact_path: Path | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> None:
    validation_mode = _closed_validation_mode(validation_mode)
    kind = packet.get("kind")
    if kind == PACKET_KIND:
        _validate_readability_packet(
            packet,
            validation_mode=validation_mode,
        )
        return
    if kind == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        _validate_professional_completeness_packet(
            packet,
            validation_root=validation_root,
            artifact_path=artifact_path,
            validation_mode=validation_mode,
        )
        return
    if kind == SEMANTIC_DISPOSITION_PACKET_KIND:
        if validation_mode == VALIDATION_MODE_HISTORICAL:
            raise PanelReviewError(
                "historical validation is limited to readability and "
                "professional-completeness artifacts"
            )
        _validate_semantic_disposition_packet(packet)
        return
    raise PanelReviewError("packet kind is invalid")


def _validate_rationale(value: object, *, label: str) -> str:
    rationale = _non_blank(value, label=label)
    if len(rationale.split()) < 6:
        raise PanelReviewError(f"{label} must contain at least six words")
    return rationale


def _validate_vote(
    vote: object,
    *,
    fields: set[str],
    decisions: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(vote, dict) or set(vote) != fields:
        raise PanelReviewError(f"{label} fields are invalid")
    decision = vote.get("decision")
    if decision not in decisions:
        raise PanelReviewError(f"{label}.decision is invalid; abstention is forbidden")
    reason_code = vote.get("reason_code")
    if reason_code not in ALL_REASON_CODES[decision]:
        raise PanelReviewError(f"{label}.reason_code does not match its decision")
    _validate_rationale(vote.get("rationale"), label=f"{label}.rationale")
    return vote


def _validate_readability_ballot(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Validate one independent, full-coverage, no-abstention ballot."""

    validate_packet(packet, validation_mode=validation_mode)
    schema_version = ballot.get("schema_version")
    if schema_version != packet.get("schema_version") or schema_version not in {
        SCHEMA_VERSION,
        READABILITY_SCHEMA_VERSION,
    }:
        raise PanelReviewError("readability ballot schema does not match packet")
    expected_fields = (
        LEGACY_READABILITY_BALLOT_FIELDS
        if schema_version == SCHEMA_VERSION
        else READABILITY_BALLOT_FIELDS
    )
    if set(ballot) != expected_fields:
        raise PanelReviewError(
            f"ballot fields do not match schema {schema_version}"
        )
    if ballot.get("kind") != BALLOT_KIND:
        raise PanelReviewError("ballot schema or kind is invalid")
    if ballot.get("review_id") != packet["review_id"]:
        raise PanelReviewError("ballot review_id does not match packet")
    _iso_date(ballot.get("created_on"), label="ballot.created_on")
    if ballot.get("packet_sha256") != packet_sha256:
        raise PanelReviewError("ballot packet_sha256 is stale")
    if ballot.get("source_fingerprints") != packet["source_fingerprints"]:
        raise PanelReviewError("ballot source_fingerprints are stale")
    voter = ballot.get("voter")
    if not isinstance(voter, dict) or set(voter) != VOTER_FIELDS:
        raise PanelReviewError("ballot.voter fields are invalid")
    for key in ("voter_id", "agent_id", "role"):
        _non_blank(voter.get(key), label=f"ballot.voter.{key}")
    if VOTER_ID_PATTERN.fullmatch(voter["voter_id"]) is None:
        raise PanelReviewError(
            "ballot.voter.voter_id must be a lowercase filename-safe slug"
        )
    expertise = voter.get("expertise")
    if not isinstance(expertise, list) or not expertise or not all(
        isinstance(item, str) and item.strip() for item in expertise
    ):
        raise PanelReviewError("ballot.voter.expertise must be a non-empty string array")
    if voter.get("independent_review") is not True:
        raise PanelReviewError("ballot voter must assert independent_review=true")
    if not isinstance(ballot.get("limitations"), list) or not ballot["limitations"] or not all(
        isinstance(item, str) and item.strip() for item in ballot["limitations"]
    ):
        raise PanelReviewError("ballot.limitations must be a non-empty string array")

    expected_content = {
        row["path"]: row["classification"] for row in packet["content_targets"]
    }
    actual_content: dict[str, str] = {}
    content_votes = ballot.get("content_votes")
    if not isinstance(content_votes, list):
        raise PanelReviewError("ballot.content_votes must be an array")
    for index, vote in enumerate(content_votes):
        row = _validate_vote(
            vote,
            fields=CONTENT_VOTE_FIELDS,
            decisions=CONTENT_DECISIONS,
            label=f"content_votes[{index}]",
        )
        path = _non_blank(row.get("path"), label=f"content_votes[{index}].path")
        if path in actual_content:
            raise PanelReviewError(f"duplicate content vote: {path}")
        actual_content[path] = row.get("classification")
    if actual_content != expected_content:
        raise PanelReviewError("content ballot coverage does not match packet")
    if [row["path"] for row in content_votes] != sorted(actual_content):
        raise PanelReviewError("content votes must be path-sorted")

    expected_readability = {
        row["document_id"]: row for row in packet["readability_targets"]
    }
    actual_readability: dict[str, str] = {}
    readability_votes = ballot.get("readability_votes")
    if not isinstance(readability_votes, list):
        raise PanelReviewError("ballot.readability_votes must be an array")
    for index, vote in enumerate(readability_votes):
        label = f"readability_votes[{index}]"
        if schema_version == SCHEMA_VERSION:
            row = _validate_vote(
                vote,
                fields=READABILITY_VOTE_FIELDS,
                decisions=READABILITY_DECISIONS,
                label=label,
            )
        else:
            if not isinstance(vote, dict) or set(vote) != READABILITY_V2_VOTE_FIELDS:
                raise PanelReviewError(f"{label} fields are invalid")
            row = vote
        document_id = _non_blank(
            row.get("document_id"),
            label=f"{label}.document_id",
        )
        if document_id in actual_readability:
            raise PanelReviewError(f"duplicate readability vote: {document_id}")
        target = expected_readability.get(document_id)
        if target is None or row.get("highest_band") != target["highest_band"]:
            raise PanelReviewError(
                f"{label} does not match its packet document target"
            )
        if schema_version == READABILITY_SCHEMA_VERSION:
            finding_reviews = row.get("finding_reviews")
            if not isinstance(finding_reviews, list):
                raise PanelReviewError(f"{label}.finding_reviews must be an array")
            expected_findings = [
                (finding["finding_id"], finding["sentence_fingerprint"])
                for finding in target["findings"]
            ]
            actual_findings: list[tuple[str, str]] = []
            for finding_index, finding_review in enumerate(finding_reviews):
                finding_label = f"{label}.finding_reviews[{finding_index}]"
                finding_row = _validate_vote(
                    finding_review,
                    fields=READABILITY_FINDING_REVIEW_FIELDS,
                    decisions=READABILITY_DECISIONS,
                    label=finding_label,
                )
                actual_findings.append(
                    (
                        _lowercase_sha256(
                            finding_row.get("finding_id"),
                            label=f"{finding_label}.finding_id",
                        ),
                        _lowercase_sha256(
                            finding_row.get("sentence_fingerprint"),
                            label=f"{finding_label}.sentence_fingerprint",
                        ),
                    )
                )
            if actual_findings != expected_findings:
                raise PanelReviewError(
                    f"{label}.finding_reviews must exactly cover packet findings in canonical order"
                )
        actual_readability[document_id] = row.get("highest_band")
    expected_bands = {
        document_id: target["highest_band"]
        for document_id, target in expected_readability.items()
    }
    if actual_readability != expected_bands:
        raise PanelReviewError("readability ballot coverage does not match packet")
    if [row["document_id"] for row in readability_votes] != sorted(actual_readability):
        raise PanelReviewError("readability votes must be document-sorted")

    if schema_version == READABILITY_SCHEMA_VERSION:
        targets = {
            row["target_id"]: row for row in packet["actionability_targets"]
        }
        actual_actionability: set[str] = set()
        actionability_votes = ballot.get("actionability_votes")
        if not isinstance(actionability_votes, list):
            raise PanelReviewError("ballot.actionability_votes must be an array")
        for index, vote in enumerate(actionability_votes):
            label = f"actionability_votes[{index}]"
            row = _validate_vote(
                vote,
                fields=ACTIONABILITY_VOTE_FIELDS,
                decisions=ACTIONABILITY_DECISIONS,
                label=label,
            )
            target_id = _non_blank(
                row.get("target_id"), label=f"{label}.target_id"
            )
            if target_id not in targets:
                raise PanelReviewError(f"{label}.target_id is not in the packet")
            if target_id in actual_actionability:
                raise PanelReviewError(
                    f"duplicate actionability vote: {target_id}"
                )
            evidence = row.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise PanelReviewError(f"{label}.evidence must be non-empty")
            window = targets[target_id]["front_window"]
            window_lines = {
                item["line"]: item["text"] for item in window["lines"]
            }
            evidence_order: list[int] = []
            for evidence_index, item in enumerate(evidence):
                evidence_label = f"{label}.evidence[{evidence_index}]"
                if (
                    not isinstance(item, dict)
                    or set(item) != ACTIONABILITY_EVIDENCE_FIELDS
                ):
                    raise PanelReviewError(f"{evidence_label} fields are invalid")
                line = item.get("line")
                if (
                    type(line) is not int
                    or line < window["start_line"]
                    or line > window["end_line"]
                ):
                    raise PanelReviewError(
                        f"{evidence_label}.line is outside the detector front window"
                    )
                source_line = item.get("source_line")
                expected_source_line = window_lines.get(line)
                if source_line != expected_source_line:
                    raise PanelReviewError(
                        f"{evidence_label}.source_line is stale"
                    )
                if not _actionability_window_line_is_substantive(window, line):
                    raise PanelReviewError(
                        f"{evidence_label}.source_line must be substantive body text"
                    )
                claim = _validate_rationale(
                    item.get("claim"), label=f"{evidence_label}.claim"
                )
                if not (_evidence_tokens(claim) & _evidence_tokens(source_line)):
                    raise PanelReviewError(
                        f"{evidence_label}.claim must overlap its source_line"
                    )
                evidence_order.append(line)
            if evidence_order != sorted(set(evidence_order)):
                raise PanelReviewError(
                    f"{label}.evidence must be line-sorted and unique"
                )
            actual_actionability.add(target_id)
        if actual_actionability != set(targets):
            missing = sorted(set(targets) - actual_actionability)
            extra = sorted(actual_actionability - set(targets))
            raise PanelReviewError(
                "actionability ballot coverage does not match packet; "
                f"missing={missing}; extra={extra}"
            )
        if [row["target_id"] for row in actionability_votes] != sorted(
            actual_actionability
        ):
            raise PanelReviewError("actionability votes must be target-sorted")
    return ballot


def _validate_professional_completeness_ballot_v1(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
) -> dict[str, Any]:
    _validate_professional_completeness_packet(packet)
    if set(ballot) != PROFESSIONAL_BALLOT_FIELDS:
        raise PanelReviewError(
            "professional completeness ballot fields do not match schema 1"
        )
    if (
        ballot.get("schema_version") != SCHEMA_VERSION
        or ballot.get("kind") != PROFESSIONAL_COMPLETENESS_BALLOT_KIND
    ):
        raise PanelReviewError(
            "professional completeness ballot schema or kind is invalid"
        )
    if ballot.get("review_id") != packet["review_id"]:
        raise PanelReviewError("professional completeness ballot review_id is stale")
    _iso_date(ballot.get("created_on"), label="ballot.created_on")
    if ballot.get("packet_sha256") != packet_sha256:
        raise PanelReviewError("professional completeness ballot packet_sha256 is stale")
    if ballot.get("source_fingerprints") != packet["source_fingerprints"]:
        raise PanelReviewError(
            "professional completeness ballot source_fingerprints are stale"
        )
    voter = ballot.get("voter")
    if not isinstance(voter, dict) or set(voter) != VOTER_FIELDS:
        raise PanelReviewError("ballot.voter fields are invalid")
    for key in ("voter_id", "agent_id", "role"):
        _non_blank(voter.get(key), label=f"ballot.voter.{key}")
    if VOTER_ID_PATTERN.fullmatch(voter["voter_id"]) is None:
        raise PanelReviewError(
            "ballot.voter.voter_id must be a lowercase filename-safe slug"
        )
    expertise = voter.get("expertise")
    if not isinstance(expertise, list) or not expertise or not all(
        isinstance(item, str) and item.strip() for item in expertise
    ):
        raise PanelReviewError("ballot.voter.expertise must be a non-empty string array")
    if voter.get("independent_review") is not True:
        raise PanelReviewError("ballot voter must assert independent_review=true")
    limitations = ballot.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError("ballot.limitations must be a non-empty string array")

    expected = {row["skill_id"] for row in packet["professional_targets"]}
    actual: set[str] = set()
    votes = ballot.get("professional_votes")
    if not isinstance(votes, list):
        raise PanelReviewError("ballot.professional_votes must be an array")
    for index, vote in enumerate(votes):
        label = f"professional_votes[{index}]"
        row = _validate_vote(
            vote,
            fields=PROFESSIONAL_VOTE_FIELDS,
            decisions=PROFESSIONAL_COMPLETENESS_DECISIONS,
            label=label,
        )
        skill_id = _non_blank(row.get("skill_id"), label=f"{label}.skill_id")
        if skill_id in actual:
            raise PanelReviewError(f"duplicate professional completeness vote: {skill_id}")
        actual.add(skill_id)
        criteria = row.get("criteria")
        if not isinstance(criteria, dict) or set(criteria) != set(
            PROFESSIONAL_COMPLETENESS_CRITERIA
        ):
            raise PanelReviewError(
                f"{label}.criteria must cover every professional criterion"
            )
        invalid_values = {
            key: value
            for key, value in criteria.items()
            if value not in PROFESSIONAL_CRITERION_VALUES
        }
        if invalid_values:
            raise PanelReviewError(f"{label}.criteria contains an invalid result")
        defect_found = any(value == "defect-found" for value in criteria.values())
        accepted = row["decision"] == "accepted-current-professional-completeness"
        if accepted == defect_found:
            raise PanelReviewError(
                f"{label}.decision conflicts with its complete criteria"
            )
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise PanelReviewError(
            "professional completeness ballot coverage does not match packet; "
            f"missing={missing}; extra={extra}"
        )
    if [row["skill_id"] for row in votes] != sorted(actual):
        raise PanelReviewError("professional completeness votes must be skill-sorted")
    return ballot


def _validate_anchor_ids(
    value: object,
    *,
    label: str,
    known_anchor_ids: set[str],
) -> list[str]:
    anchor_ids = _string_list(value, label=label, allow_empty=False)
    if anchor_ids != sorted(set(anchor_ids)):
        raise PanelReviewError(f"{label} must be sorted and unique")
    unknown = set(anchor_ids) - known_anchor_ids
    if unknown:
        raise PanelReviewError(
            f"{label} contains unknown evidence anchors: "
            + ", ".join(sorted(unknown))
        )
    return anchor_ids


def _professional_materials_by_skill(
    packet: dict[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Reuse the canonical material index without changing packet artifacts."""

    return professional_carry.professional_materials_by_skill(
        packet["professional_targets"]
    )


def _professional_review_bindings(
    targets: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Project current bindings or the audit-only schema-2 compatibility view."""

    if all(
        isinstance(target, dict)
        and "registry_authority" not in target
        and "reference_authority" not in target
        for target in targets
    ):
        return professional_carry.professional_historical_content_review_bindings(
            targets
        )
    return professional_carry.professional_review_bindings(targets)


PROFESSIONAL_EVIDENCE_REVIEW_SOURCE_PATHS = (
    "scripts/audit-skill-content.py",
    "scripts/expert_panel_attestation.py",
    "scripts/expert_panel_review.py",
    "scripts/professional_completeness_carry_forward.py",
    "scripts/validation_utils.py",
)


def _professional_evidence_review_contract_manifest() -> dict[str, object]:
    """Return the legacy source manifest for diagnostic comparison only."""

    return professional_carry.versioned_explicit_source_manifest(
        contract_version="professional-evidence-review-and-carry-v3",
        source_paths=PROFESSIONAL_EVIDENCE_REVIEW_SOURCE_PATHS,
        repository_root=ROOT,
    )


@lru_cache(maxsize=1)
def _professional_evidence_review_contract_fingerprint() -> str:
    """Return the canonical explicit Professional semantic contract digest."""

    return panel_contracts.professional_review_contract_fingerprint()


def _professional_assertion_excerpt_sha256(
    anchor_ids: list[str],
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
) -> str:
    excerpts = []
    for anchor_id in anchor_ids:
        anchor = anchors_by_id[anchor_id]
        material = materials_by_skill[anchor["skill_id"]][anchor["path"]]
        lines = material["content"].splitlines()
        excerpt = "\n".join(
            lines[anchor["start_line"] - 1 : anchor["end_line"]]
        )
        excerpts.append(
            {
                "anchor_id": anchor_id,
                "skill_id": anchor["skill_id"],
                "path": anchor["path"],
                "start_line": anchor["start_line"],
                "end_line": anchor["end_line"],
                "excerpt": excerpt,
            }
        )
    return _canonical_json_sha256(excerpts)


def _professional_anchor_text(
    anchor_ids: list[str],
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
) -> str:
    excerpts: list[str] = []
    for anchor_id in anchor_ids:
        anchor = anchors_by_id[anchor_id]
        material = materials_by_skill[anchor["skill_id"]][anchor["path"]]
        excerpts.append(
            _substantive_excerpt(
                material["content"],
                start_line=anchor["start_line"],
                end_line=anchor["end_line"],
            )
        )
    return "\n".join(excerpts)


def _require_anchor_skills(
    anchor_ids: list[str],
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    allowed_skill_ids: set[str],
    label: str,
) -> None:
    wrong = sorted(
        {
            anchors_by_id[anchor_id]["skill_id"]
            for anchor_id in anchor_ids
        }
        - allowed_skill_ids
    )
    if wrong:
        raise PanelReviewError(
            f"{label} references evidence from the wrong Skill package: "
            + ", ".join(wrong)
        )


def _require_evidence_token_overlap(
    claim: str,
    anchor_ids: list[str],
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
    minimum: int,
    label: str,
) -> None:
    source_tokens = _evidence_tokens(
        _professional_anchor_text(
            anchor_ids,
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        )
    )
    overlap = _evidence_tokens(claim) & source_tokens
    if len(overlap) < minimum:
        raise PanelReviewError(
            f"{label} must overlap substantive source evidence by at least "
            f"{minimum} non-generic tokens"
        )


def _professional_v3_anchor_token_sequences(
    anchor_id: str,
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
) -> list[tuple[str, ...]]:
    """Tokenize each cited source line independently; phrases never cross lines."""

    anchor = anchors_by_id[anchor_id]
    material = materials_by_skill[anchor["skill_id"]][anchor["path"]]
    lines = material["content"].splitlines()[
        anchor["start_line"] - 1 : anchor["end_line"]
    ]
    return [
        sequence
        for line in lines
        for sequence in _professional_v3_grounding_token_sequences(line)
    ]


def _professional_v3_grounding_counts(
    text: str,
    anchor_ids: list[str],
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
) -> tuple[int, int]:
    """Count exact grounded unigrams and bigrams without joining anchors."""

    claim_sequences = _professional_v3_grounding_token_sequences(text)
    claim_unigrams = {
        token for sequence in claim_sequences for token in sequence
    }
    claim_bigrams: set[tuple[str, ...]] = set()
    for sequence in claim_sequences:
        claim_bigrams.update(_professional_v3_ngrams(sequence, 2))
    source_unigrams: set[str] = set()
    source_bigrams: set[tuple[str, ...]] = set()
    for anchor_id in anchor_ids:
        for sequence in _professional_v3_anchor_token_sequences(
            anchor_id,
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        ):
            source_unigrams.update(sequence)
            source_bigrams.update(_professional_v3_ngrams(sequence, 2))
    return (
        len(claim_unigrams & source_unigrams),
        len(claim_bigrams & source_bigrams),
    )


def _professional_v3_require_each_anchor_grounded(
    text: str,
    anchor_ids: list[str],
    *,
    defect: bool,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
    label: str,
) -> None:
    for anchor_id in anchor_ids:
        unigram_count, bigram_count = _professional_v3_grounding_counts(
            text,
            [anchor_id],
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        )
        grounded = bigram_count >= 1 or (
            defect and unigram_count >= 3
        )
        if not grounded:
            requirement = (
                "one exact non-generic source bigram or three distinct grounded unigrams"
                if defect
                else "one exact non-generic source bigram"
            )
            raise PanelReviewError(
                f"{label} must ground anchor {anchor_id!r} with {requirement}"
            )


def _professional_v3_validate_uniform_template_guard(
    records: list[dict[str, Any]], *, label: str
) -> None:
    """Reject an extreme shared template when its common text is source-free."""

    contract = _professional_v3_grounding_contract()["uniform_template_guard"]
    clusters: dict[
        tuple[str, int, tuple[str, ...]], list[dict[str, Any]]
    ] = {}
    for member_index, record in enumerate(records):
        tokens = _professional_v3_token_sequence(record["text"])
        ordinary = _professional_v3_ngrams(
            tokens, contract["ordinary_ngram_size"]
        )
        for ngram in ordinary:
            clusters.setdefault(
                ("ordinary", contract["ordinary_ngram_size"], ngram), []
            ).append(
                {**record, "member_index": member_index}
            )
        if len(tokens) <= contract["short_claim_max_tokens"]:
            short = _professional_v3_ngrams(
                tokens, contract["short_claim_ngram_size"]
            )
            for ngram in short:
                clusters.setdefault(
                    ("short", contract["short_claim_ngram_size"], ngram), []
                ).append(
                    {**record, "member_index": member_index}
                )
    minimum_share = contract["minimum_uniform_share_percent"]
    for (category, size, ngram), members in sorted(clusters.items()):
        if len(members) < contract["minimum_uniform_claims"] or (
            len(members) * 100 < len(records) * minimum_share
        ):
            continue
        common_bigrams = {
            bigram
            for bigram in _professional_v3_ngrams(ngram, 2)
        }
        for row in members:
            if row["grounded_bigram_count"] > contract[
                "maximum_grounded_bigrams_for_low_grounding"
            ]:
                continue
            if not common_bigrams & row["source_bigrams"]:
                raise PanelReviewError(
                    f"{label} member {row['member_index']} reuses one "
                    f"source-free {size}-gram {category} template on a "
                    "low-grounding ballot surface"
                )


def _professional_v3_source_bigrams(
    anchor_ids: list[str],
    *,
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
) -> set[tuple[str, ...]]:
    result: set[tuple[str, ...]] = set()
    for anchor_id in anchor_ids:
        for sequence in _professional_v3_anchor_token_sequences(
            anchor_id,
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        ):
            result.update(_professional_v3_ngrams(sequence, 2))
    return result


def _validate_professional_v3_semantic_grounding(
    vote: dict[str, Any],
    *,
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
    label: str,
) -> None:
    """Apply stronger semantic grounding only to formal schema-3 ballots."""

    anchors_by_id = {
        anchor["anchor_id"]: anchor for anchor in vote["evidence_anchors"]
    }
    template_records: list[dict[str, Any]] = []

    def bind_record(text: str, anchor_ids: list[str]) -> dict[str, Any]:
        _unigrams, grounded_bigrams = _professional_v3_grounding_counts(
            text,
            anchor_ids,
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        )
        return {
            "text": text,
            "grounded_bigram_count": grounded_bigrams,
            "source_bigrams": _professional_v3_source_bigrams(
                anchor_ids,
                anchors_by_id=anchors_by_id,
                materials_by_skill=materials_by_skill,
            ),
        }

    for criterion, result in vote["criteria"].items():
        defect = result["status"] == "defect-found"
        for assertion_index, assertion in enumerate(result["evidence_assertions"]):
            assertion_label = (
                f"{label}.criteria.{criterion}.evidence_assertions[{assertion_index}].claim"
            )
            anchor_ids = assertion["evidence_anchor_ids"]
            claim = assertion["claim"]
            _professional_v3_require_each_anchor_grounded(
                claim,
                anchor_ids,
                defect=defect,
                anchors_by_id=anchors_by_id,
                materials_by_skill=materials_by_skill,
                label=assertion_label,
            )
            template_records.append(bind_record(claim, anchor_ids))

    for collection, item_name in (
        ("examined_failure_modes", "failure_mode"),
        ("examined_omission_candidates", "omission_candidate"),
    ):
        for item_index, item in enumerate(vote[collection]):
            item_label = f"{label}.{collection}[{item_index}]"
            text = f"{item[item_name]} {item['rationale']}"
            anchor_ids = item["evidence_anchor_ids"]
            _professional_v3_require_each_anchor_grounded(
                text,
                anchor_ids,
                defect=item["outcome"] == "defect-found",
                anchors_by_id=anchors_by_id,
                materials_by_skill=materials_by_skill,
                label=item_label,
            )

    for candidate_index, candidate in enumerate(
        vote["examined_adjacent_candidates"]
    ):
        candidate_label = (
            f"{label}.examined_adjacent_candidates[{candidate_index}].rationale"
        )
        rationale = candidate["rationale"]
        target_counts = _professional_v3_grounding_counts(
            rationale,
            candidate["target_anchor_ids"],
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        )
        candidate_counts = _professional_v3_grounding_counts(
            rationale,
            candidate["candidate_anchor_ids"],
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
        )
        exact_bigrams = target_counts[1] >= 1 and candidate_counts[1] >= 1
        if candidate["disposition"] == "gap-or-overlap-defect":
            relaxed = (
                target_counts[0] >= 1
                and candidate_counts[0] >= 1
                and target_counts[0] + candidate_counts[0] >= 6
            )
            grounded = exact_bigrams or relaxed
        else:
            grounded = exact_bigrams
        if not grounded:
            raise PanelReviewError(
                f"{candidate_label} must separately ground target and candidate source evidence"
            )

    _professional_v3_validate_uniform_template_guard(
        template_records, label=f"{label}.criteria"
    )


def _professional_voter_kind(voter: dict[str, Any]) -> str:
    """Classify one schema-2 reviewer without allowing mixed axis expertise."""

    tags = voter.get("expertise_tags")
    if not isinstance(tags, list):
        raise PanelReviewError("ballot.voter.expertise_tags must be an array")
    if PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG in tags:
        if tags != [PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG]:
            raise PanelReviewError(
                "architecture ballot expertise_tags must contain only "
                "skill-reference-architecture"
            )
        return "architecture"
    return "domain"


def _validate_professional_target_qualification(
    voter: dict[str, Any],
    target: dict[str, Any],
    *,
    voter_kind: str,
) -> None:
    """Require every domain assignment to carry the target's complete tag set."""

    if voter_kind == "architecture":
        return
    missing = set(target["required_expertise_tags"]) - set(
        voter["expertise_tags"]
    )
    if missing:
        raise PanelReviewError(
            f"domain voter {voter['voter_id']} lacks required expertise for "
            f"{target['skill_id']}: " + ", ".join(sorted(missing))
        )


def _validate_professional_qualification_claims(voter: dict[str, Any]) -> None:
    claims = voter.get("qualification_claims")
    if not isinstance(claims, list):
        raise PanelReviewError("ballot.voter.qualification_claims must be an array")
    expertise_tags = voter["expertise_tags"]
    claimed_tags: list[str] = []
    for index, claim in enumerate(claims):
        label = f"ballot.voter.qualification_claims[{index}]"
        if (
            not isinstance(claim, dict)
            or set(claim) != PROFESSIONAL_QUALIFICATION_CLAIM_FIELDS
        ):
            raise PanelReviewError(f"{label} fields are invalid")
        tag = _non_blank(claim.get("expertise_tag"), label=f"{label}.expertise_tag")
        _validate_rationale(
            claim.get("qualification_basis"),
            label=f"{label}.qualification_basis",
        )
        _validate_rationale(
            claim.get("proof_limit"), label=f"{label}.proof_limit"
        )
        claimed_tags.append(tag)
    if claimed_tags != expertise_tags:
        raise PanelReviewError(
            "ballot.voter.qualification_claims must exactly cover expertise_tags"
        )


def _validate_professional_examined_items(
    value: object,
    *,
    label: str,
    item_field: str,
    fields: set[str],
    current_skill_id: str,
    known_anchor_ids: set[str],
    anchors_by_id: dict[str, dict[str, Any]],
    materials_by_skill: dict[str, dict[str, dict[str, Any]]],
) -> tuple[bool, set[str]]:
    if (
        not isinstance(value, list)
        or len(value) < panel_contracts.PROFESSIONAL_MINIMUM_EXAMINED_ITEMS
    ):
        raise PanelReviewError(f"{label} must contain at least two items")
    names: list[str] = []
    defect_found = False
    referenced_anchor_ids: set[str] = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict) or set(item) != fields:
            raise PanelReviewError(f"{item_label} fields are invalid")
        name = _non_blank(item.get(item_field), label=f"{item_label}.{item_field}")
        outcome = item.get("outcome")
        if outcome not in PROFESSIONAL_REVIEW_OUTCOMES:
            raise PanelReviewError(f"{item_label}.outcome is invalid")
        anchor_ids = _validate_anchor_ids(
            item.get("evidence_anchor_ids"),
            label=f"{item_label}.evidence_anchor_ids",
            known_anchor_ids=known_anchor_ids,
        )
        _require_anchor_skills(
            anchor_ids,
            anchors_by_id=anchors_by_id,
            allowed_skill_ids={current_skill_id},
            label=f"{item_label}.evidence_anchor_ids",
        )
        rationale = _validate_rationale(
            item.get("rationale"), label=f"{item_label}.rationale"
        )
        _require_evidence_token_overlap(
            f"{name} {rationale}",
            anchor_ids,
            anchors_by_id=anchors_by_id,
            materials_by_skill=materials_by_skill,
            minimum=(
                panel_contracts.PROFESSIONAL_MINIMUM_EXAMINED_ITEM_OVERLAP_TOKENS
            ),
            label=item_label,
        )
        names.append(name)
        referenced_anchor_ids.update(anchor_ids)
        defect_found = defect_found or outcome == "defect-found"
    if names != sorted(set(names)):
        raise PanelReviewError(f"{label} must be name-sorted and unique")
    return defect_found, referenced_anchor_ids


def _validate_professional_completeness_ballot_v2(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
    materials_by_target: (
        dict[str, dict[str, dict[str, dict[str, Any]]]] | None
    ) = None,
    expected_adjacency_by_target: dict[str, list[str]] | None = None,
    validate_packet_contract: bool = True,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    if validate_packet_contract:
        _validate_professional_completeness_packet_v2(
            packet,
            validation_mode=validation_mode,
        )
    if set(ballot) != PROFESSIONAL_BALLOT_FIELDS:
        raise PanelReviewError(
            "professional completeness ballot fields do not match schema 2"
        )
    if (
        ballot.get("schema_version") != PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION
        or ballot.get("kind") != PROFESSIONAL_COMPLETENESS_BALLOT_KIND
    ):
        raise PanelReviewError(
            "professional completeness ballot schema or kind is invalid"
        )
    if ballot.get("review_id") != packet["review_id"]:
        raise PanelReviewError("professional completeness ballot review_id is stale")
    _iso_date(ballot.get("created_on"), label="ballot.created_on")
    if ballot.get("packet_sha256") != packet_sha256:
        raise PanelReviewError(
            "professional completeness ballot packet_sha256 is stale"
        )
    if ballot.get("source_fingerprints") != packet["source_fingerprints"]:
        raise PanelReviewError(
            "professional completeness ballot source_fingerprints are stale"
        )
    voter = ballot.get("voter")
    if not isinstance(voter, dict) or set(voter) != PROFESSIONAL_V2_VOTER_FIELDS:
        raise PanelReviewError("ballot.voter fields are invalid")
    for key in ("voter_id", "agent_id", "role"):
        _non_blank(voter.get(key), label=f"ballot.voter.{key}")
    if VOTER_ID_PATTERN.fullmatch(voter["voter_id"]) is None:
        raise PanelReviewError(
            "ballot.voter.voter_id must be a lowercase filename-safe slug"
        )
    _string_list(
        voter.get("expertise"),
        label="ballot.voter.expertise",
        allow_empty=False,
    )
    _expertise_tags(
        voter.get("expertise_tags"),
        label="ballot.voter.expertise_tags",
        allow_architecture=True,
        allow_historical=(
            validation_mode == VALIDATION_MODE_HISTORICAL
        ),
    )
    voter_kind = _professional_voter_kind(voter)
    _validate_professional_qualification_claims(voter)
    if voter.get("independent_review") is not True:
        raise PanelReviewError("ballot voter must assert independent_review=true")
    limitations = ballot.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError("ballot.limitations must be a non-empty string array")

    targets = {row["skill_id"]: row for row in packet["professional_targets"]}
    materials_by_skill = (
        {}
        if materials_by_target is not None
        else _professional_materials_by_skill(packet)
    )
    votes = ballot.get("professional_votes")
    if not isinstance(votes, list):
        raise PanelReviewError("ballot.professional_votes must be an array")
    actual: set[str] = set()
    for index, vote in enumerate(votes):
        label = f"professional_votes[{index}]"
        row = _validate_vote(
            vote,
            fields=PROFESSIONAL_V2_VOTE_FIELDS,
            decisions=PROFESSIONAL_COMPLETENESS_DECISIONS,
            label=label,
        )
        skill_id = _non_blank(row.get("skill_id"), label=f"{label}.skill_id")
        if skill_id in actual:
            raise PanelReviewError(
                f"duplicate professional completeness vote: {skill_id}"
            )
        target = targets.get(skill_id)
        if target is None:
            raise PanelReviewError(f"{label}.skill_id is not present in packet")
        actual.add(skill_id)
        vote_materials_by_skill = (
            materials_by_target.get(skill_id)
            if materials_by_target is not None
            else materials_by_skill
        )
        if vote_materials_by_skill is None:
            raise PanelReviewError(
                f"{label}.skill_id is absent from its closed material projection"
            )
        _validate_professional_target_qualification(
            voter,
            target,
            voter_kind=voter_kind,
        )

        anchors = row.get("evidence_anchors")
        if not isinstance(anchors, list) or not anchors:
            raise PanelReviewError(f"{label}.evidence_anchors must be non-empty")
        anchor_ids: list[str] = []
        anchor_paths: dict[str, str] = {}
        anchors_by_id: dict[str, dict[str, Any]] = {}
        for anchor_index, anchor in enumerate(anchors):
            anchor_label = f"{label}.evidence_anchors[{anchor_index}]"
            if (
                not isinstance(anchor, dict)
                or set(anchor) != PROFESSIONAL_EVIDENCE_ANCHOR_FIELDS
            ):
                raise PanelReviewError(f"{anchor_label} fields are invalid")
            anchor_id = _non_blank(
                anchor.get("anchor_id"), label=f"{anchor_label}.anchor_id"
            )
            if VOTER_ID_PATTERN.fullmatch(anchor_id) is None:
                raise PanelReviewError(
                    f"{anchor_label}.anchor_id must be a canonical slug"
                )
            anchor_skill_id = _non_blank(
                anchor.get("skill_id"), label=f"{anchor_label}.skill_id"
            )
            skill_materials = vote_materials_by_skill.get(anchor_skill_id)
            if skill_materials is None:
                raise PanelReviewError(
                    f"{anchor_label}.skill_id is not present in packet"
                )
            path = _non_blank(anchor.get("path"), label=f"{anchor_label}.path")
            material = skill_materials.get(path)
            if material is None:
                raise PanelReviewError(
                    f"{anchor_label}.path is not bound to anchor skill_id"
                )
            start_line = anchor.get("start_line")
            end_line = anchor.get("end_line")
            if (
                type(start_line) is not int
                or type(end_line) is not int
                or start_line < 1
                or end_line < start_line
                or end_line > material["line_count"]
            ):
                raise PanelReviewError(
                    f"{anchor_label} line range is outside bound source content"
                )
            if not _substantive_excerpt(
                material["content"],
                start_line=start_line,
                end_line=end_line,
            ):
                raise PanelReviewError(
                    f"{anchor_label} must cite substantive body text"
                )
            anchor_ids.append(anchor_id)
            anchor_paths[anchor_id] = path
            anchors_by_id[anchor_id] = anchor
        if anchor_ids != sorted(set(anchor_ids)):
            raise PanelReviewError(
                f"{label}.evidence_anchors must be anchor-id-sorted and unique"
            )
        known_anchor_ids = set(anchor_ids)

        criteria = row.get("criteria")
        if not isinstance(criteria, dict) or set(criteria) != set(
            PROFESSIONAL_COMPLETENESS_CRITERIA
        ):
            raise PanelReviewError(
                f"{label}.criteria must cover every professional criterion"
            )
        criterion_statuses: dict[str, str] = {}
        referenced_anchor_ids: set[str] = set()
        criterion_claims: list[str] = []
        criterion_anchor_signatures: list[tuple[str, ...]] = []
        for criterion, result in criteria.items():
            criterion_label = f"{label}.criteria.{criterion}"
            if (
                not isinstance(result, dict)
                or set(result) != PROFESSIONAL_CRITERION_RESULT_FIELDS
            ):
                raise PanelReviewError(f"{criterion_label} fields are invalid")
            status = result.get("status")
            if status not in PROFESSIONAL_CRITERION_VALUES:
                raise PanelReviewError(f"{criterion_label}.status is invalid")
            assertions = result.get("evidence_assertions")
            if not isinstance(assertions, list) or not assertions:
                raise PanelReviewError(
                    f"{criterion_label}.evidence_assertions must be non-empty"
                )
            criterion_anchor_ids: set[str] = set()
            for assertion_index, assertion in enumerate(assertions):
                assertion_label = (
                    f"{criterion_label}.evidence_assertions[{assertion_index}]"
                )
                if (
                    not isinstance(assertion, dict)
                    or set(assertion) != PROFESSIONAL_EVIDENCE_ASSERTION_FIELDS
                ):
                    raise PanelReviewError(f"{assertion_label} fields are invalid")
                claim = _validate_rationale(
                    assertion.get("claim"), label=f"{assertion_label}.claim"
                )
                assertion_anchor_ids = _validate_anchor_ids(
                    assertion.get("evidence_anchor_ids"),
                    label=f"{assertion_label}.evidence_anchor_ids",
                    known_anchor_ids=known_anchor_ids,
                )
                _require_anchor_skills(
                    assertion_anchor_ids,
                    anchors_by_id=anchors_by_id,
                    allowed_skill_ids={skill_id},
                    label=f"{assertion_label}.evidence_anchor_ids",
                )
                source_excerpt_sha256 = _lowercase_sha256(
                    assertion.get("source_excerpt_sha256"),
                    label=f"{assertion_label}.source_excerpt_sha256",
                )
                expected_excerpt_sha256 = (
                    _professional_assertion_excerpt_sha256(
                        assertion_anchor_ids,
                        anchors_by_id=anchors_by_id,
                        materials_by_skill=vote_materials_by_skill,
                    )
                )
                if source_excerpt_sha256 != expected_excerpt_sha256:
                    raise PanelReviewError(
                        f"{assertion_label}.source_excerpt_sha256 is stale"
                    )
                _require_evidence_token_overlap(
                    claim,
                    assertion_anchor_ids,
                    anchors_by_id=anchors_by_id,
                    materials_by_skill=vote_materials_by_skill,
                    minimum=(
                        panel_contracts.PROFESSIONAL_MINIMUM_ASSERTION_OVERLAP_TOKENS
                    ),
                    label=f"{assertion_label}.claim",
                )
                criterion_claims.append(claim.casefold())
                criterion_anchor_ids.update(assertion_anchor_ids)
                referenced_anchor_ids.update(assertion_anchor_ids)
            criterion_anchor_signatures.append(tuple(sorted(criterion_anchor_ids)))
            criterion_statuses[criterion] = status
        if len(criterion_claims) != len(set(criterion_claims)):
            raise PanelReviewError(
                f"{label}.criteria must use a unique claim for every evidence assertion"
            )
        if len(set(criterion_anchor_signatures)) == 1:
            raise PanelReviewError(
                f"{label}.criteria cannot reuse one generic anchor set for every criterion"
            )
        if target["indexed_references"]:
            reference_paths = {
                reference["path"] for reference in target["indexed_references"]
            }
            high_risk_ids = {
                anchor_id
                for assertion in criteria["reference-high-risk-coverage"][
                    "evidence_assertions"
                ]
                for anchor_id in assertion["evidence_anchor_ids"]
            }
            if not any(
                anchor_paths[anchor_id] in reference_paths
                for anchor_id in high_risk_ids
            ):
                raise PanelReviewError(
                    f"{label}.criteria.reference-high-risk-coverage must cite an indexed Reference"
                )

        failure_defect, failure_anchor_ids = (
            _validate_professional_examined_items(
                row.get("examined_failure_modes"),
                label=f"{label}.examined_failure_modes",
                item_field="failure_mode",
                fields=PROFESSIONAL_FAILURE_MODE_FIELDS,
                current_skill_id=skill_id,
                known_anchor_ids=known_anchor_ids,
                anchors_by_id=anchors_by_id,
                materials_by_skill=vote_materials_by_skill,
            )
        )
        referenced_anchor_ids.update(failure_anchor_ids)
        if failure_defect != (
            criterion_statuses["failure-modes"] == "defect-found"
        ):
            raise PanelReviewError(
                f"{label}.examined_failure_modes conflict with failure-modes criterion"
            )
        omission_defect, omission_anchor_ids = (
            _validate_professional_examined_items(
                row.get("examined_omission_candidates"),
                label=f"{label}.examined_omission_candidates",
                item_field="omission_candidate",
                fields=PROFESSIONAL_OMISSION_CANDIDATE_FIELDS,
                current_skill_id=skill_id,
                known_anchor_ids=known_anchor_ids,
                anchors_by_id=anchors_by_id,
                materials_by_skill=vote_materials_by_skill,
            )
        )
        referenced_anchor_ids.update(omission_anchor_ids)
        if omission_defect != (
            criterion_statuses["material-omissions"] == "defect-found"
        ):
            raise PanelReviewError(
                f"{label}.examined_omission_candidates conflict with material-omissions criterion"
            )

        adjacency_reviews = row.get("examined_adjacent_candidates")
        required_candidates = [
            candidate["skill_id"]
            for candidate in target["routing_adjacency"]["required_candidates"]
        ]
        full_catalog_candidates = {
            candidate["skill_id"]
            for candidate in target["routing_adjacency"]["full_catalog_ranking"]
        }
        if not isinstance(adjacency_reviews, list):
            raise PanelReviewError(
                f"{label}.examined_adjacent_candidates must be an array"
            )
        reviewed_candidates: list[str] = []
        adjacency_defect = False
        for candidate_index, candidate_review in enumerate(adjacency_reviews):
            candidate_label = (
                f"{label}.examined_adjacent_candidates[{candidate_index}]"
            )
            if (
                not isinstance(candidate_review, dict)
                or set(candidate_review) != PROFESSIONAL_ADJACENCY_REVIEW_FIELDS
            ):
                raise PanelReviewError(f"{candidate_label} fields are invalid")
            candidate_id = _non_blank(
                candidate_review.get("skill_id"),
                label=f"{candidate_label}.skill_id",
            )
            if candidate_id not in full_catalog_candidates:
                raise PanelReviewError(
                    f"{candidate_label}.skill_id must come from packet full_catalog_ranking"
                )
            review_origin = candidate_review.get("review_origin")
            if review_origin not in PROFESSIONAL_ADJACENCY_REVIEW_ORIGINS:
                raise PanelReviewError(
                    f"{candidate_label}.review_origin is invalid"
                )
            required_by_packet = candidate_id in required_candidates
            expected_origin = (
                "packet-required" if required_by_packet else "reviewer-added"
            )
            if review_origin != expected_origin:
                raise PanelReviewError(
                    f"{candidate_label}.review_origin must be {expected_origin}"
                )
            discovery_reason = candidate_review.get("discovery_reason")
            if required_by_packet:
                if discovery_reason is not None:
                    raise PanelReviewError(
                        f"{candidate_label}.discovery_reason must be null for packet-required candidates"
                    )
            else:
                _validate_rationale(
                    discovery_reason,
                    label=f"{candidate_label}.discovery_reason",
                )
            disposition = candidate_review.get("disposition")
            if disposition not in PROFESSIONAL_ADJACENCY_DISPOSITIONS:
                raise PanelReviewError(f"{candidate_label}.disposition is invalid")
            target_anchor_ids = _validate_anchor_ids(
                candidate_review.get("target_anchor_ids"),
                label=f"{candidate_label}.target_anchor_ids",
                known_anchor_ids=known_anchor_ids,
            )
            _require_anchor_skills(
                target_anchor_ids,
                anchors_by_id=anchors_by_id,
                allowed_skill_ids={skill_id},
                label=f"{candidate_label}.target_anchor_ids",
            )
            candidate_anchor_ids = _validate_anchor_ids(
                candidate_review.get("candidate_anchor_ids"),
                label=f"{candidate_label}.candidate_anchor_ids",
                known_anchor_ids=known_anchor_ids,
            )
            _require_anchor_skills(
                candidate_anchor_ids,
                anchors_by_id=anchors_by_id,
                allowed_skill_ids={candidate_id},
                label=f"{candidate_label}.candidate_anchor_ids",
            )
            rationale = _validate_rationale(
                candidate_review.get("rationale"),
                label=f"{candidate_label}.rationale",
            )
            _require_evidence_token_overlap(
                rationale,
                target_anchor_ids,
                anchors_by_id=anchors_by_id,
                materials_by_skill=vote_materials_by_skill,
                minimum=(
                    panel_contracts.PROFESSIONAL_MINIMUM_ADJACENCY_SIDE_OVERLAP_TOKENS
                ),
                label=f"{candidate_label}.rationale target evidence",
            )
            _require_evidence_token_overlap(
                rationale,
                candidate_anchor_ids,
                anchors_by_id=anchors_by_id,
                materials_by_skill=vote_materials_by_skill,
                minimum=(
                    panel_contracts.PROFESSIONAL_MINIMUM_ADJACENCY_SIDE_OVERLAP_TOKENS
                ),
                label=f"{candidate_label}.rationale candidate evidence",
            )
            referenced_anchor_ids.update(target_anchor_ids)
            referenced_anchor_ids.update(candidate_anchor_ids)
            reviewed_candidates.append(candidate_id)
            adjacency_defect = adjacency_defect or (
                disposition == "gap-or-overlap-defect"
            )
        if reviewed_candidates != sorted(set(reviewed_candidates)):
            raise PanelReviewError(
                f"{label}.examined_adjacent_candidates must be skill-sorted and unique"
            )
        missing_required = sorted(set(required_candidates) - set(reviewed_candidates))
        if missing_required:
            raise PanelReviewError(
                f"{label}.examined_adjacent_candidates must cover every required packet candidate; missing="
                + ", ".join(missing_required)
            )
        if expected_adjacency_by_target is not None:
            expected_adjacency = expected_adjacency_by_target.get(skill_id)
            if expected_adjacency is None:
                raise PanelReviewError(
                    f"{label}.skill_id is absent from its closed adjacency projection"
                )
            if reviewed_candidates != expected_adjacency:
                raise PanelReviewError(
                    f"{label}.examined_adjacent_candidates must exactly match "
                    "the target-scoped capsule manifest"
                )
        if adjacency_defect != (
            criterion_statuses["adjacent-overlap-or-gap"] == "defect-found"
        ):
            raise PanelReviewError(
                f"{label}.examined_adjacent_candidates conflict with adjacency criterion"
            )

        proof_limits = _string_list(
            row.get("proof_limits"),
            label=f"{label}.proof_limits",
            allow_empty=False,
        )
        if proof_limits != sorted(set(proof_limits)):
            raise PanelReviewError(f"{label}.proof_limits must be sorted and unique")
        for proof_index, proof_limit in enumerate(proof_limits):
            _validate_rationale(
                proof_limit, label=f"{label}.proof_limits[{proof_index}]"
            )
        if referenced_anchor_ids != known_anchor_ids:
            raise PanelReviewError(
                f"{label}.evidence_anchors contains anchors not used by criteria, failure modes, omission candidates, or adjacency reviews"
            )
        defect_found = any(
            status == "defect-found" for status in criterion_statuses.values()
        )
        accepted = row["decision"] == "accepted-current-professional-completeness"
        if accepted == defect_found:
            raise PanelReviewError(
                f"{label}.decision conflicts with its complete criteria"
            )
    if not actual:
        raise PanelReviewError(
            "professional completeness ballot assignment must be non-empty"
        )
    if [row["skill_id"] for row in votes] != sorted(actual):
        raise PanelReviewError("professional completeness votes must be skill-sorted")
    return ballot


def _validate_professional_completeness_ballot(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
    artifact_path: Path | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    schema_version = ballot.get("schema_version")
    if schema_version == SCHEMA_VERSION:
        if packet.get("schema_version") != SCHEMA_VERSION:
            raise PanelReviewError(
                "professional completeness ballot schema does not match packet"
            )
        return _validate_professional_completeness_ballot_v1(
            packet, ballot, packet_sha256=packet_sha256
        )
    if schema_version == PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION:
        if packet.get("schema_version") != PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION:
            raise PanelReviewError(
                "professional completeness ballot schema does not match packet"
            )
        return _validate_professional_completeness_ballot_v2(
            packet,
            ballot,
            packet_sha256=packet_sha256,
            validation_mode=validation_mode,
        )
    if schema_version == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION:
        if (
            packet.get("schema_version")
            != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        ):
            raise PanelReviewError(
                "professional completeness ballot schema does not match packet"
            )
        return _validate_professional_completeness_ballot_v3(
            packet,
            ballot,
            packet_sha256=packet_sha256,
            validation_root=validation_root,
            artifact_path=artifact_path,
            validation_mode=validation_mode,
        )
    raise PanelReviewError(
        "professional completeness ballot schema version is unsupported"
    )


def _validate_semantic_disposition_ballot(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
) -> dict[str, Any]:
    _validate_semantic_disposition_packet(packet)
    if set(ballot) != SEMANTIC_BALLOT_FIELDS:
        raise PanelReviewError(
            "semantic disposition ballot fields do not match schema 2"
        )
    if (
        ballot.get("schema_version") != SEMANTIC_DISPOSITION_SCHEMA_VERSION
        or ballot.get("kind") != SEMANTIC_DISPOSITION_BALLOT_KIND
    ):
        raise PanelReviewError("semantic disposition ballot schema or kind is invalid")
    if ballot.get("review_id") != packet["review_id"]:
        raise PanelReviewError("semantic disposition ballot review_id is stale")
    created_on = date.fromisoformat(
        _iso_date(ballot.get("created_on"), label="ballot.created_on")
    )
    if ballot.get("packet_sha256") != packet_sha256:
        raise PanelReviewError("semantic disposition ballot packet_sha256 is stale")
    if ballot.get("source_fingerprints") != packet["source_fingerprints"]:
        raise PanelReviewError(
            "semantic disposition ballot source_fingerprints are stale"
        )
    voter = ballot.get("voter")
    if not isinstance(voter, dict) or set(voter) != VOTER_FIELDS:
        raise PanelReviewError("semantic disposition ballot voter fields are invalid")
    for key in ("voter_id", "agent_id", "role"):
        _non_blank(voter.get(key), label=f"ballot.voter.{key}")
    if VOTER_ID_PATTERN.fullmatch(voter["voter_id"]) is None:
        raise PanelReviewError(
            "ballot.voter.voter_id must be a lowercase filename-safe slug"
        )
    _string_list(
        voter.get("expertise"),
        label="ballot.voter.expertise",
        allow_empty=False,
    )
    if voter.get("independent_review") is not True:
        raise PanelReviewError("semantic disposition voter must be independent")
    limitations = ballot.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise PanelReviewError(
            "semantic disposition ballot limitations must be a non-empty string array"
        )

    expected = {
        target["target_id"]: (
            target["axis"],
            target["candidate"]["candidate_id"],
        )
        for target in packet["semantic_targets"]
    }
    votes = ballot.get("semantic_votes")
    if not isinstance(votes, list):
        raise PanelReviewError("ballot.semantic_votes must be an array")
    actual: dict[str, tuple[str, str]] = {}
    for index, vote in enumerate(votes):
        label = f"semantic_votes[{index}]"
        if not isinstance(vote, dict) or set(vote) != SEMANTIC_VOTE_FIELDS:
            raise PanelReviewError(f"{label} fields are invalid")
        target_id = _non_blank(vote.get("target_id"), label=f"{label}.target_id")
        axis = vote.get("axis")
        if axis not in SEMANTIC_AXES:
            raise PanelReviewError(f"{label}.axis is invalid")
        candidate_id = _lowercase_sha256(
            vote.get("candidate_id"), label=f"{label}.candidate_id"
        )
        if target_id in actual:
            raise PanelReviewError(f"duplicate semantic disposition vote: {target_id}")
        actual[target_id] = (str(axis), candidate_id)
        decision = vote.get("disposition")
        if decision not in SEMANTIC_DISPOSITIONS:
            raise PanelReviewError(
                f"{label}.disposition is invalid; abstention is forbidden"
            )
        _validate_rationale(vote.get("rationale"), label=f"{label}.rationale")
        _non_blank(
            vote.get("authority_or_condition"),
            label=f"{label}.authority_or_condition",
        )
        owner = _non_blank(
            vote.get("decision_owner"), label=f"{label}.decision_owner"
        )
        if len(owner.split()) < 2 and VOTER_ID_PATTERN.fullmatch(owner) is None:
            raise PanelReviewError(
                f"{label}.decision_owner must name an accountable owner"
            )
        _non_blank(vote.get("mitigation"), label=f"{label}.mitigation")
        review_after = vote.get("review_after")
        if decision == "time-bounded-exception":
            try:
                expiry = date.fromisoformat(str(review_after))
                if expiry.isoformat() != review_after:
                    raise ValueError
            except (TypeError, ValueError):
                raise PanelReviewError(
                    f"{label}.review_after must be an ISO date for a time-bounded exception"
                ) from None
            if expiry <= max(created_on, date.today()):
                raise PanelReviewError(
                    f"{label}.review_after must be a future expiry"
                )
        elif review_after is not None:
            raise PanelReviewError(
                f"{label}.review_after must be null unless time-bounded-exception"
            )
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise PanelReviewError(
            "semantic disposition ballot coverage does not match packet; "
            f"missing={missing}; extra={extra}"
        )
    if [vote["target_id"] for vote in votes] != sorted(actual):
        raise PanelReviewError("semantic disposition votes must be target-sorted")
    return ballot


def validate_ballot(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
    artifact_path: Path | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    validation_mode = _closed_validation_mode(validation_mode)
    if packet.get("kind") == PACKET_KIND:
        return _validate_readability_ballot(
            packet,
            ballot,
            packet_sha256=packet_sha256,
            validation_mode=validation_mode,
        )
    if packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        return _validate_professional_completeness_ballot(
            packet,
            ballot,
            packet_sha256=packet_sha256,
            validation_root=validation_root,
            artifact_path=artifact_path,
            validation_mode=validation_mode,
        )
    if packet.get("kind") == SEMANTIC_DISPOSITION_PACKET_KIND:
        if validation_mode == VALIDATION_MODE_HISTORICAL:
            raise PanelReviewError(
                "historical validation is limited to readability and "
                "professional-completeness artifacts"
            )
        return _validate_semantic_disposition_ballot(
            packet, ballot, packet_sha256=packet_sha256
        )
    raise PanelReviewError("ballot packet kind is invalid")


def _majority_decision(
    rows: list[dict[str, Any]],
    *,
    voter_ids: list[str],
    include_evidence: bool = False,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["decision"]] = counts.get(row["decision"], 0) + 1
    winner, winning_votes = max(counts.items(), key=lambda item: (item[1], item[0]))
    if winning_votes < 2:
        raise PanelReviewError("three-voter ballot produced no majority")
    supporting = [
        voter_id
        for voter_id, row in zip(voter_ids, rows, strict=True)
        if row["decision"] == winner
    ]
    dissenting = [
        voter_id
        for voter_id, row in zip(voter_ids, rows, strict=True)
        if row["decision"] != winner
    ]
    return {
        "winning_disposition": winner,
        "winning_votes": winning_votes,
        "vote_counts": {key: counts[key] for key in sorted(counts)},
        "supporting_voters": supporting,
        "dissenting_voters": dissenting,
        "winning_rationales": [
            {
                "voter_id": voter_id,
                "reason_code": row["reason_code"],
                "rationale": row["rationale"],
                **(
                    {"evidence": row["evidence"]}
                    if include_evidence
                    else {}
                ),
            }
            for voter_id, row in zip(voter_ids, rows, strict=True)
            if row["decision"] == winner
        ],
    }


def _readability_document_vote_from_findings(
    vote: dict[str, Any],
) -> dict[str, Any]:
    """Derive one reviewer document disposition without a self-filled override."""

    reviews = vote["finding_reviews"]
    decision = (
        "tracked-tightening"
        if any(row["decision"] == "tracked-tightening" for row in reviews)
        else "accepted-current-readability"
    )
    decisive = next(row for row in reviews if row["decision"] == decision)
    return {
        "decision": decision,
        "reason_code": decisive["reason_code"],
        "rationale": decisive["rationale"],
    }


def _aggregate_readability_ballots(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Derive every disposition from exactly three independent ballots."""

    validate_packet(packet, validation_mode=validation_mode)
    _iso_date(decided_on, label="decided_on")
    if len(ballot_values) != PANEL_SIZE:
        raise PanelReviewError(f"panel requires exactly {PANEL_SIZE} ballots")
    packet_sha256 = _sha256(packet_path)
    validated = [
        (
            path,
            validate_ballot(
                packet,
                value,
                packet_sha256=packet_sha256,
                validation_mode=validation_mode,
            ),
        )
        for path, value in ballot_values
    ]
    validated.sort(key=lambda item: item[1]["voter"]["voter_id"])
    voter_ids = [value["voter"]["voter_id"] for _path, value in validated]
    agent_ids = [value["voter"]["agent_id"] for _path, value in validated]
    roles = [value["voter"]["role"] for _path, value in validated]
    for label, values in (
        ("voter_id", voter_ids),
        ("agent_id", agent_ids),
        ("role", roles),
    ):
        if len(values) != len(set(values)):
            raise PanelReviewError(f"panel requires three unique {label} values")

    content_by_voter = [
        {row["path"]: row for row in value["content_votes"]}
        for _path, value in validated
    ]
    readability_by_voter = [
        {row["document_id"]: row for row in value["readability_votes"]}
        for _path, value in validated
    ]
    actionability_by_voter = (
        [
            {row["target_id"]: row for row in value["actionability_votes"]}
            for _path, value in validated
        ]
        if packet["schema_version"] == READABILITY_SCHEMA_VERSION
        else []
    )
    content_decisions = []
    for target in packet["content_targets"]:
        path = target["path"]
        content_decisions.append(
            {
                "path": path,
                "classification": target["classification"],
                **_majority_decision(
                    [rows[path] for rows in content_by_voter],
                    voter_ids=voter_ids,
                ),
            }
        )
    readability_decisions = []
    for target in packet["readability_targets"]:
        document_id = target["document_id"]
        voter_rows = [rows[document_id] for rows in readability_by_voter]
        if packet["schema_version"] == READABILITY_SCHEMA_VERSION:
            reviews_by_voter = [
                {
                    row["finding_id"]: row
                    for row in voter_row["finding_reviews"]
                }
                for voter_row in voter_rows
            ]
            finding_decisions = [
                {
                    "finding_id": finding["finding_id"],
                    "sentence_fingerprint": finding["sentence_fingerprint"],
                    **_majority_decision(
                        [
                            rows[finding["finding_id"]]
                            for rows in reviews_by_voter
                        ],
                        voter_ids=voter_ids,
                    ),
                }
                for finding in target["findings"]
            ]
            document_rows = [
                _readability_document_vote_from_findings(row)
                for row in voter_rows
            ]
        else:
            finding_decisions = []
            document_rows = voter_rows
        readability_decisions.append(
            {
                "document_id": document_id,
                "highest_band": target["highest_band"],
                "finding_fingerprints": [
                    row["sentence_fingerprint"] for row in target["findings"]
                ],
                **(
                    {"finding_decisions": finding_decisions}
                    if packet["schema_version"] == READABILITY_SCHEMA_VERSION
                    else {}
                ),
                **_majority_decision(
                    document_rows,
                    voter_ids=voter_ids,
                ),
            }
        )
    actionability_decisions: list[dict[str, Any]] = []
    if packet["schema_version"] == READABILITY_SCHEMA_VERSION:
        for target in packet["actionability_targets"]:
            target_id = target["target_id"]
            actionability_decisions.append(
                {
                    **target,
                    **_majority_decision(
                        [rows[target_id] for rows in actionability_by_voter],
                        voter_ids=voter_ids,
                        include_evidence=True,
                    ),
                }
            )
    summaries = {
        "content": {
            decision: sum(
                row["winning_disposition"] == decision for row in content_decisions
            )
            for decision in sorted(CONTENT_DECISIONS)
        },
        "readability": {
            decision: sum(
                row["winning_disposition"] == decision
                for row in readability_decisions
            )
            for decision in sorted(READABILITY_DECISIONS)
        },
    }
    if packet["schema_version"] == READABILITY_SCHEMA_VERSION:
        summaries["actionability"] = {
            decision: sum(
                row["winning_disposition"] == decision
                for row in actionability_decisions
            )
            for decision in sorted(ACTIONABILITY_DECISIONS)
        }
    record = {
        "schema_version": packet["schema_version"],
        "kind": DECISION_KIND,
        "review_id": packet["review_id"],
        "decided_on": decided_on,
        "decision_method": DECISION_METHOD,
        "source_fingerprints": packet["source_fingerprints"],
        "panel_contract": packet["panel_contract"],
        "packet": {
            "path": packet_path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": packet_sha256,
        },
        "voters": [
            {
                **value["voter"],
                "ballot_path": path.name,
                "ballot_sha256": _sha256(path),
            }
            for path, value in validated
        ],
        "content_decisions": content_decisions,
        "readability_decisions": readability_decisions,
        "summary": summaries,
        "limitations": [
            "The majority decision is based on three independent static reviews.",
            "Agent votes do not prove real-host behavior or production outcomes.",
        ],
    }
    if packet["schema_version"] == READABILITY_SCHEMA_VERSION:
        record["actionability_decisions"] = actionability_decisions
    return record


def _aggregate_professional_completeness_ballots_v1(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
) -> dict[str, Any]:
    _validate_professional_completeness_packet(packet)
    _iso_date(decided_on, label="decided_on")
    if len(ballot_values) != PANEL_SIZE:
        raise PanelReviewError(f"panel requires exactly {PANEL_SIZE} ballots")
    packet_sha256 = _sha256(packet_path)
    validated = [
        (path, validate_ballot(packet, value, packet_sha256=packet_sha256))
        for path, value in ballot_values
    ]
    voter_ids = [value["voter"]["voter_id"] for _path, value in validated]
    agent_ids = [value["voter"]["agent_id"] for _path, value in validated]
    roles = [value["voter"]["role"] for _path, value in validated]
    for label, values in (
        ("voter_id", voter_ids),
        ("agent_id", agent_ids),
        ("role", roles),
    ):
        if len(values) != len(set(values)):
            raise PanelReviewError(f"panel requires three unique {label} values")
    decisions_by_voter = [
        {row["skill_id"]: row for row in value["professional_votes"]}
        for _path, value in validated
    ]
    professional_decisions: list[dict[str, Any]] = []
    for target in packet["professional_targets"]:
        skill_id = target["skill_id"]
        rows = [votes[skill_id] for votes in decisions_by_voter]
        criterion_vote_counts = {
            criterion: {
                value: sum(row["criteria"][criterion] == value for row in rows)
                for value in sorted(PROFESSIONAL_CRITERION_VALUES)
            }
            for criterion in sorted(PROFESSIONAL_COMPLETENESS_CRITERIA)
        }
        professional_decisions.append(
            {
                "skill_id": skill_id,
                "package_fingerprint": target["package_fingerprint"],
                "criterion_vote_counts": criterion_vote_counts,
                **_majority_decision(rows, voter_ids=voter_ids),
            }
        )
    summary = {
        decision: sum(
            row["winning_disposition"] == decision
            for row in professional_decisions
        )
        for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        "review_id": packet["review_id"],
        "decided_on": decided_on,
        "decision_method": DECISION_METHOD,
        "source_fingerprints": packet["source_fingerprints"],
        "panel_contract": packet["panel_contract"],
        "packet": {
            "path": packet_path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": packet_sha256,
        },
        "voters": [
            {
                **value["voter"],
                "ballot_path": path.name,
                "ballot_sha256": _sha256(path),
            }
            for path, value in validated
        ],
        "professional_decisions": professional_decisions,
        "summary": {"professional_completeness": summary},
        "limitations": [
            "The majority decision is based on three independent static professional reviews.",
            "Static professional review does not prove real-host or production outcomes.",
        ],
    }


def _aggregate_professional_completeness_ballots_v2(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
) -> dict[str, Any]:
    _validate_professional_completeness_packet_v2(packet)
    _iso_date(decided_on, label="decided_on")
    if len(ballot_values) < PANEL_SIZE:
        raise PanelReviewError(
            "professional completeness reviewer pool requires at least "
            f"{PANEL_SIZE} ballots"
        )
    packet_sha256 = _sha256(packet_path)
    validated = [
        (path, validate_ballot(packet, value, packet_sha256=packet_sha256))
        for path, value in ballot_values
    ]
    validated.sort(key=lambda item: item[1]["voter"]["voter_id"])
    voter_ids = [value["voter"]["voter_id"] for _path, value in validated]
    agent_ids = [value["voter"]["agent_id"] for _path, value in validated]
    for label, values in (
        ("voter_id", voter_ids),
        ("agent_id", agent_ids),
    ):
        if len(values) != len(set(values)):
            raise PanelReviewError(
                f"professional completeness reviewer pool requires round-wide "
                f"unique {label} values"
            )

    reviewer_kinds = {
        value["voter"]["voter_id"]: _professional_voter_kind(value["voter"])
        for _path, value in validated
    }
    assignments: dict[str, list[tuple[str, str, dict[str, Any]]]] = {
        target["skill_id"]: [] for target in packet["professional_targets"]
    }
    for _path, ballot in validated:
        voter_id = ballot["voter"]["voter_id"]
        voter_kind = reviewer_kinds[voter_id]
        for vote in ballot["professional_votes"]:
            assignments[vote["skill_id"]].append((voter_id, voter_kind, vote))

    professional_decisions: list[dict[str, Any]] = []
    for target in packet["professional_targets"]:
        skill_id = target["skill_id"]
        assigned = sorted(assignments[skill_id], key=lambda item: item[0])
        if len(assigned) != PANEL_SIZE:
            raise PanelReviewError(
                f"professional completeness target {skill_id} requires exactly "
                f"{PANEL_SIZE} assigned ballots; actual={len(assigned)}"
            )
        domain_assignments = [item for item in assigned if item[1] == "domain"]
        architecture_assignments = [
            item for item in assigned if item[1] == "architecture"
        ]
        if len(domain_assignments) != 2 or len(architecture_assignments) != 1:
            raise PanelReviewError(
                f"professional completeness target {skill_id} requires exactly "
                "two qualified domain ballots and one architecture ballot"
            )
        rows = [item[2] for item in assigned]
        target_voter_ids = [item[0] for item in assigned]
        domain_voter_ids = [item[0] for item in domain_assignments]
        architecture_voter = architecture_assignments[0][0]
        criterion_vote_counts = {
            criterion: {
                value: sum(
                    row["criteria"][criterion]["status"] == value for row in rows
                )
                for value in sorted(PROFESSIONAL_CRITERION_VALUES)
            }
            for criterion in sorted(PROFESSIONAL_COMPLETENESS_CRITERIA)
        }
        majority = _majority_decision(rows, voter_ids=target_voter_ids)
        domain_critical_defects = sorted(
            (
                {
                    "criterion": criterion,
                    "voter_id": voter_id,
                }
                for voter_id, _kind, row in domain_assignments
                for criterion in PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
                if row["criteria"][criterion]["status"] == "defect-found"
            ),
            key=lambda item: (item["criterion"], item["voter_id"]),
        )
        ordinary_criterion_defects = [
            criterion
            for criterion in sorted(PROFESSIONAL_ORDINARY_CRITERIA)
            if criterion_vote_counts[criterion]["defect-found"] >= 2
        ]
        ordinary_criterion_disposition = (
            "requires-professional-correction"
            if ordinary_criterion_defects
            else "accepted-current-professional-completeness"
        )
        final_disposition = (
            PROFESSIONAL_UNRESOLVED_DISPOSITION
            if domain_critical_defects
            else ordinary_criterion_disposition
        )
        professional_decisions.append(
            {
                "skill_id": skill_id,
                "package_fingerprint": target["package_fingerprint"],
                "qualification_coverage": {
                    "required_expertise_tags": target["required_expertise_tags"],
                    "domain_voters": domain_voter_ids,
                    "architecture_voter": architecture_voter,
                },
                "criterion_vote_counts": criterion_vote_counts,
                "domain_critical_defects": domain_critical_defects,
                "ordinary_criterion_defects": ordinary_criterion_defects,
                "ordinary_criterion_disposition": (
                    ordinary_criterion_disposition
                ),
                "reviewer_added_adjacency_reviews": [
                    {
                        "voter_id": voter_id,
                        "candidates": [
                            candidate
                            for candidate in row["examined_adjacent_candidates"]
                            if candidate["review_origin"] == "reviewer-added"
                        ],
                    }
                    for voter_id, row in zip(
                        target_voter_ids, rows, strict=True
                    )
                    if any(
                        candidate["review_origin"] == "reviewer-added"
                        for candidate in row["examined_adjacent_candidates"]
                    )
                ],
                **majority,
                "final_disposition": final_disposition,
            }
        )
    professional_summary = {
        decision: sum(
            row["final_disposition"] == decision
            for row in professional_decisions
        )
        for decision in sorted(PROFESSIONAL_FINAL_DISPOSITIONS)
    }
    ordinary_criterion_summary = {
        decision: sum(
            row["ordinary_criterion_disposition"] == decision
            for row in professional_decisions
        )
        for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
    }
    overall_ballot_majority_audit = {
        decision: sum(
            row["winning_disposition"] == decision
            for row in professional_decisions
        )
        for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
    }
    ballots = [value for _path, value in validated]
    evidence_summary = {
        "required_adjacency_candidate_count": sum(
            len(target["routing_adjacency"]["required_candidates"])
            for target in packet["professional_targets"]
        ),
        "criterion_result_count": sum(
            len(vote["criteria"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
        ),
        "criterion_anchor_binding_count": sum(
            len(assertion["evidence_anchor_ids"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
            for result in vote["criteria"].values()
            for assertion in result["evidence_assertions"]
        ),
        "criterion_assertion_count": sum(
            len(result["evidence_assertions"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
            for result in vote["criteria"].values()
        ),
        "evidence_anchor_count": sum(
            len(vote["evidence_anchors"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
        ),
        "examined_failure_mode_count": sum(
            len(vote["examined_failure_modes"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
        ),
        "examined_omission_candidate_count": sum(
            len(vote["examined_omission_candidates"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
        ),
        "examined_adjacency_count": sum(
            len(vote["examined_adjacent_candidates"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
        ),
        "examined_required_adjacency_count": sum(
            candidate["review_origin"] == "packet-required"
            for ballot in ballots
            for vote in ballot["professional_votes"]
            for candidate in vote["examined_adjacent_candidates"]
        ),
        "reviewer_added_adjacency_count": sum(
            candidate["review_origin"] == "reviewer-added"
            for ballot in ballots
            for vote in ballot["professional_votes"]
            for candidate in vote["examined_adjacent_candidates"]
        ),
        "proof_limit_count": sum(
            len(vote["proof_limits"])
            for ballot in ballots
            for vote in ballot["professional_votes"]
        ),
        "qualification_claim_count": sum(
            len(ballot["voter"]["qualification_claims"])
            for ballot in ballots
        ),
    }
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        "review_id": packet["review_id"],
        "decided_on": decided_on,
        "decision_method": PROFESSIONAL_COMPLETENESS_DECISION_METHOD,
        "source_fingerprints": packet["source_fingerprints"],
        "panel_contract": packet["panel_contract"],
        "packet": {
            "path": packet_path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": packet_sha256,
        },
        "voters": [
            {
                **value["voter"],
                "ballot_path": path.name,
                "ballot_sha256": _sha256(path),
            }
            for path, value in validated
        ],
        "professional_decisions": professional_decisions,
        "summary": {
            "professional_completeness": professional_summary,
            "ordinary_criterion_majority": ordinary_criterion_summary,
            "overall_ballot_majority_audit": overall_ballot_majority_audit,
            "qualification": {
                "covered_target_count": len(professional_decisions),
                "required_domain_experts_per_target": 2,
                "required_architecture_experts_per_target": 1,
                "per_target_panel_size": PANEL_SIZE,
                "reviewer_pool_size": len(validated),
                "domain_reviewer_count": sum(
                    kind == "domain" for kind in reviewer_kinds.values()
                ),
                "architecture_reviewer_count": sum(
                    kind == "architecture" for kind in reviewer_kinds.values()
                ),
            },
            "evidence": evidence_summary,
        },
        "limitations": [
            "Each ordinary criterion is decided independently by a two-of-three criterion majority from exactly two qualified domain reviewers and one architecture reviewer drawn from the round-wide reviewer pool.",
            "The overall ballot majority, its rationales, and its dissent remain audit evidence only and do not determine the schema-2 final disposition.",
            "A qualified domain-reviewer defect on any domain-critical criterion is fail-closed as an unresolved professional disagreement; this schema supports no arbitration or override.",
            "Qualification claims are static reviewer declarations and do not prove real reviewer identity, credentials, or domain experience.",
            "Static professional review does not prove real-host or production outcomes.",
        ],
    }


def _aggregate_professional_completeness_ballots(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
    validation_root: Path = ROOT,
    forbidden_paths: set[Path] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    if packet.get("schema_version") == SCHEMA_VERSION:
        return _aggregate_professional_completeness_ballots_v1(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=decided_on,
        )
    if packet.get("schema_version") == PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION:
        return _aggregate_professional_completeness_ballots_v2(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=decided_on,
        )
    if (
        packet.get("schema_version")
        == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    ):
        return _aggregate_professional_completeness_ballots_v3(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=decided_on,
            validation_root=validation_root,
            forbidden_paths=forbidden_paths,
            validation_mode=validation_mode,
        )
    raise PanelReviewError(
        "professional completeness packet schema version is unsupported"
    )


def _semantic_majority_decision(
    rows: list[dict[str, Any]], *, voter_ids: list[str]
) -> dict[str, Any]:
    counts = {
        disposition: sum(row["disposition"] == disposition for row in rows)
        for disposition in sorted(SEMANTIC_DISPOSITIONS)
    }
    winner, winning_votes = max(counts.items(), key=lambda item: (item[1], item[0]))
    if winning_votes < 2:
        raise PanelReviewError("three-voter semantic ballot produced no majority")
    return {
        "winning_disposition": winner,
        "winning_votes": winning_votes,
        "vote_counts": counts,
        "supporting_voters": [
            voter_id
            for voter_id, row in zip(voter_ids, rows, strict=True)
            if row["disposition"] == winner
        ],
        "dissenting_voters": [
            voter_id
            for voter_id, row in zip(voter_ids, rows, strict=True)
            if row["disposition"] != winner
        ],
        "ballot_rationales": [
            {
                "voter_id": voter_id,
                "disposition": row["disposition"],
                "rationale": row["rationale"],
                "authority_or_condition": row["authority_or_condition"],
                "decision_owner": row["decision_owner"],
                "mitigation": row["mitigation"],
                "review_after": row["review_after"],
            }
            for voter_id, row in zip(voter_ids, rows, strict=True)
        ],
    }


def _aggregate_semantic_disposition_ballots(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
) -> dict[str, Any]:
    """Derive semantic dispositions without creating governance entries."""

    _validate_semantic_disposition_packet(packet)
    _iso_date(decided_on, label="decided_on")
    if len(ballot_values) != PANEL_SIZE:
        raise PanelReviewError(f"panel requires exactly {PANEL_SIZE} ballots")
    packet_sha256 = _sha256(packet_path)
    validated = [
        (path, validate_ballot(packet, value, packet_sha256=packet_sha256))
        for path, value in ballot_values
    ]
    validated.sort(key=lambda item: item[1]["voter"]["voter_id"])
    voter_ids = [value["voter"]["voter_id"] for _path, value in validated]
    agent_ids = [value["voter"]["agent_id"] for _path, value in validated]
    roles = [value["voter"]["role"] for _path, value in validated]
    for label, values in (
        ("voter_id", voter_ids),
        ("agent_id", agent_ids),
        ("role", roles),
    ):
        if len(values) != len(set(values)):
            raise PanelReviewError(f"panel requires three unique {label} values")
    votes_by_voter = [
        {row["target_id"]: row for row in value["semantic_votes"]}
        for _path, value in validated
    ]
    decisions: list[dict[str, Any]] = []
    for target in packet["semantic_targets"]:
        target_id = target["target_id"]
        decisions.append(
            {
                "target_id": target_id,
                "axis": target["axis"],
                "candidate_id": target["candidate"]["candidate_id"],
                "candidate_binding_fingerprint": target[
                    "candidate_binding_fingerprint"
                ],
                **_semantic_majority_decision(
                    [votes[target_id] for votes in votes_by_voter],
                    voter_ids=voter_ids,
                ),
            }
        )
    summary = {
        disposition: sum(
            decision["winning_disposition"] == disposition
            for decision in decisions
        )
        for disposition in sorted(SEMANTIC_DISPOSITIONS)
    }
    return {
        "schema_version": SEMANTIC_DISPOSITION_SCHEMA_VERSION,
        "kind": SEMANTIC_DISPOSITION_DECISION_KIND,
        "review_id": packet["review_id"],
        "decided_on": decided_on,
        "decision_method": DECISION_METHOD,
        "source_fingerprints": packet["source_fingerprints"],
        "panel_contract": packet["panel_contract"],
        "packet": {
            "path": packet_path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": packet_sha256,
        },
        "voters": [
            {
                **value["voter"],
                "ballot_path": path.name,
                "ballot_sha256": _sha256(path),
            }
            for path, value in validated
        ],
        "semantic_decisions": decisions,
        "summary": {"semantic_dispositions": summary},
        "limitations": [
            "This majority is authoring lifecycle evidence only.",
            "It cannot satisfy readability or professional-completeness formal attestations.",
            "The record contains no generated single-source-of-truth disposition entries.",
            "A rewrite majority requires a source edit before any resolved governance entry can exist.",
        ],
    }


def aggregate_ballots(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
    validation_root: Path = ROOT,
    forbidden_paths: set[Path] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    validation_mode = _closed_validation_mode(validation_mode)
    if packet.get("kind") == PACKET_KIND:
        return _aggregate_readability_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=decided_on,
            validation_mode=validation_mode,
        )
    if packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        return _aggregate_professional_completeness_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=decided_on,
            validation_root=validation_root,
            forbidden_paths=forbidden_paths,
            validation_mode=validation_mode,
        )
    if packet.get("kind") == SEMANTIC_DISPOSITION_PACKET_KIND:
        if validation_mode == VALIDATION_MODE_HISTORICAL:
            raise PanelReviewError(
                "historical validation is limited to readability and "
                "professional-completeness artifacts"
            )
        return _aggregate_semantic_disposition_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballot_values,
            decided_on=decided_on,
        )
    raise PanelReviewError("aggregate packet kind is invalid")


def _validate_readability_decision_record(
    record: dict[str, Any],
    *,
    record_path: Path,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Recompute a stored decision from its packet and three stored ballots."""

    schema_version = record.get("schema_version")
    if schema_version not in {SCHEMA_VERSION, READABILITY_SCHEMA_VERSION}:
        raise PanelReviewError("decision record schema is invalid")
    expected_fields = {
        "schema_version",
        "kind",
        "review_id",
        "decided_on",
        "decision_method",
        "source_fingerprints",
        "panel_contract",
        "packet",
        "voters",
        "content_decisions",
        "readability_decisions",
        "summary",
        "limitations",
    }
    if schema_version == READABILITY_SCHEMA_VERSION:
        expected_fields.add("actionability_decisions")
    if set(record) != expected_fields:
        raise PanelReviewError(
            f"decision record fields do not match schema {schema_version}"
        )
    if record.get("kind") != DECISION_KIND:
        raise PanelReviewError("decision record kind is invalid")
    packet_ref = record.get("packet")
    if not isinstance(packet_ref, dict) or set(packet_ref) != {"path", "sha256"}:
        raise PanelReviewError("decision packet reference is invalid")
    packet_value = _non_blank(
        packet_ref.get("path"), label="decision packet path"
    )
    packet_sha256 = packet_ref.get("sha256")
    if not isinstance(packet_sha256, str) or len(packet_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in packet_sha256
    ):
        raise PanelReviewError("decision packet sha256 is invalid")
    packet_path = _canonical_relative_path(packet_value, label="decision packet path")
    if _sha256(packet_path) != packet_sha256:
        raise PanelReviewError("decision packet sha256 is stale")
    packet = _json_object(packet_path, label="panel packet")
    voters = record.get("voters")
    if not isinstance(voters, list) or len(voters) != PANEL_SIZE:
        raise PanelReviewError("decision record must reference exactly three voters")
    ballot_values: list[tuple[Path, dict[str, Any]]] = []
    for index, voter in enumerate(voters):
        if not isinstance(voter, dict):
            raise PanelReviewError(f"decision voter {index} must be an object")
        ballot_name = voter.get("ballot_path")
        ballot_name = _non_blank(
            ballot_name, label=f"decision voter {index}.ballot_path"
        )
        ballot_relative = Path(ballot_name)
        if (
            ballot_relative.is_absolute()
            or ballot_relative.name != ballot_name
            or ".." in ballot_relative.parts
        ):
            raise PanelReviewError("decision ballot path must be one canonical filename")
        ballot_path = record_path.parent / ballot_relative
        if ballot_path.parent.resolve() != record_path.parent.resolve():
            raise PanelReviewError("decision ballot path must stay beside the decision")
        if _sha256(ballot_path) != voter.get("ballot_sha256"):
            raise PanelReviewError(f"decision ballot sha256 is stale: {ballot_name}")
        ballot_values.append(
            (ballot_path, _json_object(ballot_path, label="panel ballot"))
        )
    recomputed = aggregate_ballots(
        packet=packet,
        packet_path=packet_path,
        ballot_values=ballot_values,
        decided_on=record["decided_on"],
        validation_mode=validation_mode,
    )
    if recomputed != record:
        raise PanelReviewError("decision record does not match recomputed majority")
    return record


def _validate_professional_completeness_decision_record_for_schema(
    record: dict[str, Any],
    *,
    record_path: Path,
    schema_version: int,
) -> dict[str, Any]:
    expected_fields = {
        "schema_version",
        "kind",
        "review_id",
        "decided_on",
        "decision_method",
        "source_fingerprints",
        "panel_contract",
        "packet",
        "voters",
        "professional_decisions",
        "summary",
        "limitations",
    }
    if set(record) != expected_fields:
        raise PanelReviewError(
            "professional completeness decision fields do not match schema "
            f"{schema_version}"
        )
    if (
        record.get("schema_version") != schema_version
        or record.get("kind") != PROFESSIONAL_COMPLETENESS_DECISION_KIND
    ):
        raise PanelReviewError(
            "professional completeness decision schema or kind is invalid"
        )
    packet_ref = record.get("packet")
    if not isinstance(packet_ref, dict) or set(packet_ref) != {"path", "sha256"}:
        raise PanelReviewError("decision packet reference is invalid")
    packet_value = _non_blank(packet_ref.get("path"), label="decision packet path")
    packet_sha256 = _lowercase_sha256(
        packet_ref.get("sha256"), label="decision packet sha256"
    )
    packet_path = _canonical_relative_path(packet_value, label="decision packet path")
    if _sha256(packet_path) != packet_sha256:
        raise PanelReviewError("decision packet sha256 is stale")
    packet = _json_object(packet_path, label="professional completeness packet")
    if (
        packet.get("kind") != PROFESSIONAL_COMPLETENESS_PACKET_KIND
        or packet.get("schema_version") != schema_version
    ):
        raise PanelReviewError(
            "professional completeness decision packet kind or schema is invalid"
        )
    voters = record.get("voters")
    valid_voter_count = (
        isinstance(voters, list)
        and (
            len(voters) == PANEL_SIZE
            if schema_version == SCHEMA_VERSION
            else len(voters) >= PANEL_SIZE
        )
    )
    if not valid_voter_count:
        if schema_version == SCHEMA_VERSION:
            raise PanelReviewError(
                "schema-1 decision record must reference exactly three voters"
            )
        raise PanelReviewError(
            "schema-2 professional decision must reference a reviewer pool of at least three voters"
        )
    ballot_values: list[tuple[Path, dict[str, Any]]] = []
    for index, voter in enumerate(voters):
        if not isinstance(voter, dict):
            raise PanelReviewError(f"decision voter {index} must be an object")
        ballot_name = _non_blank(
            voter.get("ballot_path"), label=f"decision voter {index}.ballot_path"
        )
        ballot_relative = Path(ballot_name)
        if (
            ballot_relative.is_absolute()
            or ballot_relative.name != ballot_name
            or ".." in ballot_relative.parts
        ):
            raise PanelReviewError("decision ballot path must be one canonical filename")
        ballot_path = record_path.parent / ballot_relative
        if ballot_path.parent.resolve() != record_path.parent.resolve():
            raise PanelReviewError("decision ballot path must stay beside the decision")
        if _sha256(ballot_path) != voter.get("ballot_sha256"):
            raise PanelReviewError(f"decision ballot sha256 is stale: {ballot_name}")
        ballot_values.append(
            (ballot_path, _json_object(ballot_path, label="professional completeness ballot"))
        )
    recomputed = aggregate_ballots(
        packet=packet,
        packet_path=packet_path,
        ballot_values=ballot_values,
        decided_on=record["decided_on"],
    )
    if recomputed != record:
        raise PanelReviewError(
            "professional completeness decision does not match recomputed majority"
        )
    return record


class _ProfessionalHistoricalV1Selection(dict):
    """Compare one exact immutable v1 selection against its live v2 projection."""

    def __init__(
        self,
        value: dict[str, Any],
        *,
        expected_current: dict[str, Any],
    ) -> None:
        dict.__init__(self, value)
        self.expected_current = expected_current

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _ProfessionalHistoricalV1Selection):
            return (
                dict(self) == dict(other)
                and self.expected_current == other.expected_current
            )
        return isinstance(other, dict) and dict(other) == self.expected_current

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __deepcopy__(self, memo: dict[int, object]) -> object:
        return type(self)(
            copy.deepcopy(dict(self), memo),
            expected_current=copy.deepcopy(self.expected_current, memo),
        )


class _ProfessionalSchema3RegisteredSelection(dict):
    """Mark a selector admitted only by the validated schema-3 bridge."""


def _professional_v3_historical_cap50_packet(
    record: dict[str, Any],
    packet_ref: dict[str, str],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Return an invocation-local view for the exact immutable r11 packet."""

    expected_ref = {
        "path": (
            "evals/expert-panel/"
            f"{PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID}/packet.json"
        ),
        "sha256": PROFESSIONAL_HISTORICAL_CAP50_PACKET_SHA256,
        "kind": PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "axis": PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID,
    }
    if (
        record.get("review_id") != PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID
        or record.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT
        or packet_ref != expected_ref
        or packet.get("review_id") != PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID
        or packet.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT
        or packet.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET != 57
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 compatibility binding is stale"
        )
    return _professional_v3_historical_cap50_view(
        packet,
        expected_review_id=PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID,
    )


def _professional_v3_historical_cap50_view(
    packet: dict[str, Any],
    *,
    expected_review_id: str,
) -> dict[str, Any]:
    """Preserve legacy bytes while comparing only the bound cap as current."""

    if (
        packet.get("review_id") != expected_review_id
        or packet.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT
        or packet.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET != 57
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 packet binding is stale"
        )
    targets = packet.get("professional_targets")
    if (
        not isinstance(targets, list)
        or len(targets) != PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 target binding is stale"
        )
    adapted = copy.deepcopy(packet)
    expected_historical_selection = _professional_adjacency_selection_contract_v1(
        target_count=PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT,
        include_derivation=False,
        maximum_required_candidates_per_target=(
            PROFESSIONAL_HISTORICAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
        ),
    )
    expected_current_selection = _professional_adjacency_selection_contract(
        target_count=PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT,
        include_derivation=False,
    )
    selections = [
        adapted.get("panel_contract", {})
        .get("adjacency_contract", {})
        .get("required_candidate_selection")
    ]
    selections.extend(
        target.get("routing_adjacency", {}).get(
            "required_candidate_selection"
        )
        if isinstance(target, dict)
        else None
        for target in adapted["professional_targets"]
    )
    if any(
        not isinstance(selection, dict)
        or selection != expected_historical_selection
        for selection in selections
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 selection binding is stale"
        )
    adapted["panel_contract"]["adjacency_contract"][
        "required_candidate_selection"
    ] = _ProfessionalHistoricalV1Selection(
        selections[0],
        expected_current=expected_current_selection,
    )
    for target, selection in zip(
        adapted["professional_targets"], selections[1:], strict=True
    ):
        target["routing_adjacency"]["required_candidate_selection"] = (
            _ProfessionalHistoricalV1Selection(
                selection,
                expected_current=expected_current_selection,
            )
        )
    return adapted


def _professional_v3_historical_v1_packet(
    record: dict[str, Any],
    packet_ref: dict[str, str],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Return an invocation-local view for the exact immutable r14 packet."""

    expected_ref = {
        "path": (
            "evals/expert-panel/"
            f"{PROFESSIONAL_HISTORICAL_V1_REVIEW_ID}/packet.json"
        ),
        "sha256": PROFESSIONAL_HISTORICAL_V1_PACKET_SHA256,
        "kind": PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "axis": PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": PROFESSIONAL_HISTORICAL_V1_REVIEW_ID,
    }
    if (
        record.get("review_id") != PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
        or record.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT
        or packet_ref != expected_ref
        or packet.get("review_id") != PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
        or packet.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT
        or packet.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET != 57
    ):
        raise PanelReviewError(
            "historical schema-3 v1 compatibility binding is stale"
        )
    return _professional_v3_historical_v1_view(packet)


def _professional_v3_historical_v1_view(
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Preserve exact r14 bytes while comparing its v1 selector as v2."""

    if (
        packet.get("review_id") != PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
        or packet.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT
        or packet.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET != 57
    ):
        raise PanelReviewError(
            "historical schema-3 v1 packet binding is stale"
        )
    targets = packet.get("professional_targets")
    if not isinstance(targets, list) or len(targets) != PROFESSIONAL_PACKAGE_COUNT:
        raise PanelReviewError(
            "historical schema-3 v1 target binding is stale"
        )
    adapted = copy.deepcopy(packet)
    expected_historical_selection = _professional_adjacency_selection_contract_v1(
        target_count=PROFESSIONAL_PACKAGE_COUNT,
        include_derivation=True,
        maximum_required_candidates_per_target=52,
    )
    expected_current_selection = _professional_adjacency_selection_contract(
        target_count=PROFESSIONAL_PACKAGE_COUNT,
        include_derivation=True,
    )
    selections = [
        adapted.get("panel_contract", {})
        .get("adjacency_contract", {})
        .get("required_candidate_selection")
    ]
    selections.extend(
        target.get("routing_adjacency", {}).get(
            "required_candidate_selection"
        )
        if isinstance(target, dict)
        else None
        for target in adapted["professional_targets"]
    )
    if any(
        not isinstance(selection, dict)
        or selection != expected_historical_selection
        for selection in selections
    ):
        raise PanelReviewError(
            "historical schema-3 v1 selection binding is stale"
        )
    adapted["panel_contract"]["adjacency_contract"][
        "required_candidate_selection"
    ] = _ProfessionalHistoricalV1Selection(
        selections[0],
        expected_current=expected_current_selection,
    )
    for target, selection in zip(
        adapted["professional_targets"], selections[1:], strict=True
    ):
        target["routing_adjacency"]["required_candidate_selection"] = (
            _ProfessionalHistoricalV1Selection(
                selection,
                expected_current=expected_current_selection,
            )
        )
    return adapted


def _replace_professional_v3_cached_packet(
    *,
    cache: dict[str, Any],
    validation_root: Path,
    packet_path: Path,
    packet_ref: dict[str, str],
    packet: dict[str, Any],
    adapted: dict[str, Any],
) -> None:
    """Replace one invocation-local parsed value without changing bound bytes."""

    result = (packet_path, packet_ref, adapted)
    root_key = validation_root.resolve().as_posix()
    artifact_key = (
        root_key,
        PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        packet_ref["path"],
        packet_ref["sha256"],
        packet_ref["review_id"],
    )
    path_key = (
        root_key,
        PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        packet_ref["path"],
    )
    if (
        cache["artifacts"].get(artifact_key)
        != (packet_path, packet_ref, packet)
        or cache["artifacts_by_path"].get(path_key)
        != (packet_path, packet_ref, packet)
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 cache binding is stale"
        )
    cache["artifacts"][artifact_key] = result
    cache["artifacts_by_path"][path_key] = result


def _seed_professional_v3_historical_cap50_packet(
    record: dict[str, Any],
    *,
    cache: dict[str, Any],
    validation_root: Path,
) -> None:
    packet_path, packet_ref, packet = _professional_v3_cached_json_artifact(
        record.get("packet"),
        cache=cache,
        validation_root=validation_root,
        label="schema-3 historical cap-50 packet",
        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        expected_review_id=record["review_id"],
    )
    adapted = _professional_v3_historical_cap50_packet(
        record,
        packet_ref,
        packet,
    )
    _replace_professional_v3_cached_packet(
        cache=cache,
        validation_root=validation_root,
        packet_path=packet_path,
        packet_ref=packet_ref,
        packet=packet,
        adapted=adapted,
    )
    baseline = packet.get("review_plan", {}).get("baseline")
    if not isinstance(baseline, dict) or set(baseline) != {
        "decision",
        "packet",
    }:
        raise PanelReviewError(
            "historical schema-3 cap-50 baseline binding is stale"
        )
    baseline_review_id = PROFESSIONAL_HISTORICAL_CAP50_BASELINE_REVIEW_ID
    expected_baseline_decision_ref = {
        "path": (
            "evals/expert-panel/"
            f"{baseline_review_id}/panel/decision.json"
        ),
        "sha256": PROFESSIONAL_HISTORICAL_CAP50_BASELINE_DECISION_SHA256,
        "kind": PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        "axis": PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": baseline_review_id,
    }
    expected_baseline_packet_ref = {
        "path": f"evals/expert-panel/{baseline_review_id}/packet.json",
        "sha256": PROFESSIONAL_HISTORICAL_CAP50_BASELINE_PACKET_SHA256,
        "kind": PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "axis": PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": baseline_review_id,
    }
    if (
        baseline.get("decision") != expected_baseline_decision_ref
        or baseline.get("packet") != expected_baseline_packet_ref
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 baseline allowlist is stale"
        )
    _baseline_path, baseline_decision_ref, baseline_record = (
        _professional_v3_cached_json_artifact(
            baseline["decision"],
            cache=cache,
            validation_root=validation_root,
            label="schema-3 historical cap-50 baseline decision",
            expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=baseline["decision"]["review_id"],
        )
    )
    if (
        baseline_decision_ref != baseline["decision"]
        or baseline_record.get("packet") != baseline["packet"]
        or baseline_record.get("review_id") != baseline_review_id
        or baseline_record.get("review_contract_fingerprint")
        != PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 baseline decision is stale"
        )
    baseline_packet_path, baseline_packet_ref, baseline_packet = (
        _professional_v3_cached_json_artifact(
            baseline["packet"],
            cache=cache,
            validation_root=validation_root,
            label="schema-3 historical cap-50 baseline packet",
            expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=baseline["packet"]["review_id"],
        )
    )
    if baseline_packet_ref != baseline["packet"]:
        raise PanelReviewError(
            "historical schema-3 cap-50 baseline packet is stale"
        )
    baseline_plan = baseline_packet.get("review_plan")
    baseline_rows = baseline_record.get("professional_decisions")
    if (
        not isinstance(baseline_plan, dict)
        or baseline_plan.get("baseline") is not None
        or baseline_plan.get("carried_targets") != []
        or baseline_plan.get("summary")
        != {
            "total_target_count": PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT,
            "fresh_target_count": PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT,
            "carried_target_count": 0,
        }
        or not isinstance(baseline_rows, list)
        or len(baseline_rows) != PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT
        or any(
            not isinstance(row, dict)
            or not isinstance(row.get("provenance"), dict)
            or row["provenance"].get("mode") != "fresh"
            or row["provenance"].get("origin_depth") != 0
            for row in baseline_rows
        )
    ):
        raise PanelReviewError(
            "historical schema-3 cap-50 baseline is not a direct fresh origin"
        )
    adapted_baseline = _professional_v3_historical_cap50_view(
        baseline_packet,
        expected_review_id=baseline_packet_ref["review_id"],
    )
    _replace_professional_v3_cached_packet(
        cache=cache,
        validation_root=validation_root,
        packet_path=baseline_packet_path,
        packet_ref=baseline_packet_ref,
        packet=baseline_packet,
        adapted=adapted_baseline,
    )


def _seed_professional_v3_historical_v1_packet(
    record: dict[str, Any],
    *,
    cache: dict[str, Any],
    validation_root: Path,
) -> None:
    """Seed exact r14 plus its exact r11/r9 baseline chain for audit."""

    packet_path, packet_ref, packet = _professional_v3_cached_json_artifact(
        record.get("packet"),
        cache=cache,
        validation_root=validation_root,
        label="schema-3 historical v1 packet",
        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        expected_review_id=record["review_id"],
    )
    adapted = _professional_v3_historical_v1_packet(
        record,
        packet_ref,
        packet,
    )
    _replace_professional_v3_cached_packet(
        cache=cache,
        validation_root=validation_root,
        packet_path=packet_path,
        packet_ref=packet_ref,
        packet=packet,
        adapted=adapted,
    )
    baseline = packet.get("review_plan", {}).get("baseline")
    baseline_decision = (
        baseline.get("decision") if isinstance(baseline, dict) else None
    )
    if not isinstance(baseline_decision, dict):
        raise PanelReviewError(
            "historical schema-3 v1 baseline binding is stale"
        )
    _baseline_path, _baseline_ref, baseline_record = (
        _professional_v3_cached_json_artifact(
            baseline_decision,
            cache=cache,
            validation_root=validation_root,
            label="schema-3 historical v1 baseline decision",
            expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID,
        )
    )
    _seed_professional_v3_historical_cap50_packet(
        baseline_record,
        cache=cache,
        validation_root=validation_root,
    )


def _validate_professional_completeness_decision_record(
    record: dict[str, Any],
    *,
    record_path: Path,
    validation_root: Path = ROOT,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    schema_version = record.get("schema_version")
    if (
        schema_version
        == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    ):
        _professional_v3_decision_shape(
            record,
            validation_mode=validation_mode,
        )
        cache = _professional_v3_invocation_cache()
        canonical_record_path, _decision_ref, record_from_artifact = (
            _professional_v3_bind_json_artifact_path(
                record_path,
                cache=cache,
                validation_root=validation_root,
                label="schema-3 public decision record",
                expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                expected_review_id=record["review_id"],
            )
        )
        if record_from_artifact != record:
            raise PanelReviewError(
                "schema-3 decision value does not match its artifact"
            )
        if (
            validation_mode == VALIDATION_MODE_HISTORICAL
            and record["review_id"]
            == PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID
        ):
            _seed_professional_v3_historical_cap50_packet(
                record,
                cache=cache,
                validation_root=validation_root,
            )
        elif (
            validation_mode == VALIDATION_MODE_HISTORICAL
            and record["review_id"]
            == PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
        ):
            _seed_professional_v3_historical_v1_packet(
                record,
                cache=cache,
                validation_root=validation_root,
            )
        packet_path, _packet_ref, packet, packet_state = (
            _professional_v3_load_packet_for_decision(
                record,
                validation_root=validation_root,
                forbidden_paths={canonical_record_path},
                validate_baseline=True,
                invocation_cache=cache,
                validation_mode=validation_mode,
            )
        )
        canonical_packet_state = _professional_v3_canonical_packet_state(
            packet,
            supplied_state=packet_state,
            validation_root=validation_root,
            artifact_path=packet_path,
            validate_baseline=True,
            forbidden_paths={canonical_record_path},
            invocation_cache=cache,
            validation_mode=validation_mode,
        )
        return _validate_professional_completeness_decision_record_v3(
            record,
            record_path=record_path,
            validation_root=validation_root,
            validate_packet_baseline=False,
            canonical_packet_state=canonical_packet_state,
            invocation_cache=cache,
            validation_mode=validation_mode,
        )
    if schema_version not in {
        SCHEMA_VERSION,
        PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
    }:
        raise PanelReviewError(
            "professional completeness decision schema version is unsupported"
        )
    return _validate_professional_completeness_decision_record_for_schema(
        record,
        record_path=record_path,
        schema_version=schema_version,
    )


def _validate_semantic_disposition_decision_record(
    record: dict[str, Any],
    *,
    record_path: Path,
) -> dict[str, Any]:
    expected_fields = {
        "schema_version",
        "kind",
        "review_id",
        "decided_on",
        "decision_method",
        "source_fingerprints",
        "panel_contract",
        "packet",
        "voters",
        "semantic_decisions",
        "summary",
        "limitations",
    }
    if set(record) != expected_fields:
        raise PanelReviewError(
            "semantic disposition decision fields do not match schema 2"
        )
    if (
        record.get("schema_version") != SEMANTIC_DISPOSITION_SCHEMA_VERSION
        or record.get("kind") != SEMANTIC_DISPOSITION_DECISION_KIND
    ):
        raise PanelReviewError("semantic disposition decision schema or kind is invalid")
    packet_ref = record.get("packet")
    if not isinstance(packet_ref, dict) or set(packet_ref) != {"path", "sha256"}:
        raise PanelReviewError("semantic disposition decision packet reference is invalid")
    packet_value = _non_blank(
        packet_ref.get("path"), label="semantic disposition decision packet path"
    )
    packet_sha256 = _lowercase_sha256(
        packet_ref.get("sha256"),
        label="semantic disposition decision packet sha256",
    )
    packet_path = _canonical_relative_path(
        packet_value, label="semantic disposition decision packet path"
    )
    if _sha256(packet_path) != packet_sha256:
        raise PanelReviewError("semantic disposition decision packet sha256 is stale")
    packet = _json_object(packet_path, label="semantic disposition packet")
    if packet.get("kind") != SEMANTIC_DISPOSITION_PACKET_KIND:
        raise PanelReviewError(
            "semantic disposition decision cannot use another panel kind"
        )
    voters = record.get("voters")
    if not isinstance(voters, list) or len(voters) != PANEL_SIZE:
        raise PanelReviewError(
            "semantic disposition decision must reference exactly three voters"
        )
    ballot_values: list[tuple[Path, dict[str, Any]]] = []
    for index, voter in enumerate(voters):
        if not isinstance(voter, dict):
            raise PanelReviewError(f"semantic disposition decision voter {index} is invalid")
        ballot_name = _non_blank(
            voter.get("ballot_path"),
            label=f"semantic disposition decision voter {index}.ballot_path",
        )
        ballot_relative = Path(ballot_name)
        if (
            ballot_relative.is_absolute()
            or ballot_relative.name != ballot_name
            or ".." in ballot_relative.parts
        ):
            raise PanelReviewError(
                "semantic disposition decision ballot path must be one canonical filename"
            )
        ballot_path = record_path.parent / ballot_relative
        if ballot_path.parent.resolve() != record_path.parent.resolve():
            raise PanelReviewError(
                "semantic disposition decision ballot must stay beside the decision"
            )
        if _sha256(ballot_path) != voter.get("ballot_sha256"):
            raise PanelReviewError(
                f"semantic disposition decision ballot sha256 is stale: {ballot_name}"
            )
        ballot_values.append(
            (ballot_path, _json_object(ballot_path, label="semantic disposition ballot"))
        )
    recomputed = aggregate_ballots(
        packet=packet,
        packet_path=packet_path,
        ballot_values=ballot_values,
        decided_on=record["decided_on"],
    )
    if recomputed != record:
        raise PanelReviewError(
            "semantic disposition decision does not match recomputed majority"
        )
    return record


def validate_decision_record(
    record: dict[str, Any],
    *,
    record_path: Path,
    validation_root: Path = ROOT,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    validation_mode = _closed_validation_mode(validation_mode)
    if record.get("kind") == DECISION_KIND:
        return _validate_readability_decision_record(
            record,
            record_path=record_path,
            validation_mode=validation_mode,
        )
    if record.get("kind") == PROFESSIONAL_COMPLETENESS_DECISION_KIND:
        return _validate_professional_completeness_decision_record(
            record,
            record_path=record_path,
            validation_root=validation_root,
            validation_mode=validation_mode,
        )
    if record.get("kind") == SEMANTIC_DISPOSITION_DECISION_KIND:
        if validation_mode == VALIDATION_MODE_HISTORICAL:
            raise PanelReviewError(
                "historical validation is limited to readability and "
                "professional-completeness artifacts"
            )
        return _validate_semantic_disposition_decision_record(
            record, record_path=record_path
        )
    raise PanelReviewError("decision record kind is invalid")


def _validate_legacy_semantic_decision_application(
    application: object,
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Validate one pre-fixed-storage application selector during migration."""

    if not isinstance(application, dict) or set(application) != LEGACY_SEMANTIC_APPLICATION_FIELDS:
        raise PanelReviewError(
            "semantic disposition application fields do not match schema 1"
        )
    if (
        application.get("schema_version")
        != SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION
        or application.get("kind") != SEMANTIC_DISPOSITION_APPLICATION_KIND
    ):
        raise PanelReviewError(
            "semantic disposition application schema or kind is invalid"
        )
    review_id = _non_blank(
        application.get("review_id"), label="semantic application review_id"
    )
    if not VOTER_ID_PATTERN.fullmatch(review_id):
        raise PanelReviewError(
            "semantic application review_id must be one canonical identifier"
        )
    decision_ref = application.get("decision")
    if not isinstance(decision_ref, dict) or set(decision_ref) != {"path", "sha256"}:
        raise PanelReviewError(
            "semantic application decision must contain path and sha256"
        )
    decision_value = _non_blank(
        decision_ref.get("path"), label="semantic application decision path"
    )
    decision_path = _canonical_relative_path(
        decision_value, label="semantic application decision path"
    )
    if decision_value == panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH:
        if application.get("decision_kind") != (
            panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND
        ):
            raise PanelReviewError(
                "semantic application fixed decision_kind is invalid"
            )
        try:
            bound = reviewer_manifest.read_bound_regular_file(
                ROOT / Path(decision_value),
                max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
                label="semantic application fixed attestation",
            )
            expected_sha256 = _lowercase_sha256(
                decision_ref.get("sha256"),
                label="semantic application decision sha256",
            )
            if bound.sha256 != expected_sha256:
                raise PanelReviewError(
                    "semantic application fixed attestation sha256 is stale"
                )
            root_semantic, reference_semantic = _semantic_audit_sections(audit)
            semantics = {"root": root_semantic, "reference": reference_semantic}
            current_bindings = {}
            for axis, semantic in semantics.items():
                candidates = semantic.get("candidates")
                if not isinstance(candidates, list) or not all(
                    isinstance(candidate, dict) for candidate in candidates
                ):
                    raise PanelReviewError(
                        f"semantic application current {axis} candidates must be an array"
                    )
                eligible = _semantic_eligible_candidates(
                    axis=axis, semantic=semantic
                )
                for candidate in eligible:
                    target_id = f"{axis}:{candidate.get('candidate_id')}"
                    if target_id in current_bindings:
                        raise PanelReviewError(
                            f"semantic application current {axis} IDs are duplicated"
                        )
                    current_bindings[target_id] = (
                        panel_attestation.semantic_candidate_authority(
                            axis=axis, candidate=candidate
                        )
                    )
            compact = panel_attestation.parse_attestation_bytes(
                bound.raw,
                expected_path=decision_value,
                expected_semantic_current_bindings=current_bindings,
            )
        except (
            reviewer_manifest.ManifestError,
            panel_attestation.AttestationError,
        ) as exc:
            raise PanelReviewError(
                f"semantic application fixed attestation is invalid: {exc}"
            ) from exc
        if compact["review_id"] != review_id:
            raise PanelReviewError(
                "semantic application fixed review_id is stale"
            )
        axis_counts = {
            axis: sum(
                finding["axis"] == axis for finding in compact["findings"]
            )
            for axis in sorted(SEMANTIC_AXES)
        }
        expected_contract = {
            "decision_method": DECISION_METHOD,
            "required_voters": PANEL_SIZE,
            "abstentions_allowed": False,
            "minimum_winning_votes": 2,
            "independent_ballots": True,
            "required_target_count": len(compact["findings"]),
            "required_axis_target_counts": axis_counts,
            "allowed_dispositions": sorted(SEMANTIC_DISPOSITIONS),
        }
        if compact["review_contract_fingerprint"] != _canonical_json_sha256(
            expected_contract
        ):
            raise PanelReviewError(
                "semantic application fixed review contract is stale"
            )
        current_fingerprints = _semantic_source_fingerprints(
            audit,
            root_semantic=root_semantic,
            reference_semantic=reference_semantic,
        )
        # Governance application changes the aggregate audit digest. Match the
        # legacy currentness contract: detectors remain digest-bound while all
        # other aggregate provenance is replaced by complete, per-candidate
        # authoritative current bindings below.
        if any(
            compact["source_fingerprints"][key] != current_fingerprints[key]
            for key in ("root_detector", "reference_detector")
        ):
            raise PanelReviewError(
                "semantic fixed attestation is stale against the current audit"
            )
        applied_count = 0
        completed_rewrite_count = 0
        findings_by_axis = {
            axis: {
                finding["target_id"].split(":", 1)[1]: finding
                for finding in compact["findings"]
                if finding["axis"] == axis
            }
            for axis in sorted(SEMANTIC_AXES)
        }
        for axis in sorted(SEMANTIC_AXES):
            semantic = semantics[axis]
            candidates = semantic.get("candidates")
            entries = semantic.get("disposition_contract", {}).get("entries")
            if not isinstance(candidates, list) or not all(
                isinstance(candidate, dict) for candidate in candidates
            ):
                raise PanelReviewError(
                    f"semantic application current {axis} candidates must be an array"
                )
            if not isinstance(entries, list) or not all(
                isinstance(entry, dict) for entry in entries
            ):
                raise PanelReviewError(
                    f"semantic application current {axis} entries must be an array"
                )
            eligible = _semantic_eligible_candidates(
                axis=axis, semantic=semantic
            )
            candidates_by_id = {
                str(candidate.get("candidate_id")): candidate
                for candidate in eligible
            }
            entries_by_id = {
                str(entry.get("candidate_id")): entry for entry in entries
            }
            if (
                len(candidates_by_id) != len(eligible)
                or len(entries_by_id) != len(entries)
            ):
                raise PanelReviewError(
                    f"semantic application current {axis} IDs are missing or duplicated"
                )
            findings = findings_by_axis[axis]
            rewrite_ids = {
                candidate_id
                for candidate_id, finding in findings.items()
                if finding["result"]["winning_disposition"] == "rewrite"
            }
            if set(findings) != set(candidates_by_id) | rewrite_ids:
                raise PanelReviewError(
                    "semantic fixed attestation coverage is incomplete"
                )
            if set(entries_by_id) != set(candidates_by_id):
                raise PanelReviewError(
                    "semantic fixed attestation application entries are incomplete"
                )
            for candidate_id, finding in findings.items():
                winner = finding["result"]["winning_disposition"]
                candidate = candidates_by_id.get(candidate_id)
                entry = entries_by_id.get(candidate_id)
                if winner == "rewrite":
                    if candidate is not None or entry is not None:
                        raise PanelReviewError(
                            "semantic fixed rewrite target remains current"
                        )
                    completed_rewrite_count += 1
                    continue
                if candidate is None or entry is None:
                    raise PanelReviewError(
                        "semantic fixed attestation application entry is missing"
                    )
                authority = current_bindings.get(f"{axis}:{candidate_id}")
                if authority is None or finding[
                    "candidate_binding_fingerprint"
                ] != authority["candidate_binding_fingerprint"]:
                    raise PanelReviewError(
                        "semantic fixed attestation is stale against the current audit"
                    )
                if _semantic_entry_mismatches(
                    axis=axis, candidate=candidate, entry=entry
                ):
                    raise PanelReviewError(
                        "semantic fixed attestation application entry is stale"
                    )
                if entry.get("disposition") != winner:
                    raise PanelReviewError(
                        "semantic fixed attestation disposition mismatch"
                    )
                applied_count += 1
        return {
            "schema_version": SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION,
            "kind": SEMANTIC_DISPOSITION_APPLICATION_KIND,
            "review_id": review_id,
            "decision_kind": application["decision_kind"],
            "decision": dict(decision_ref),
            "status": "current",
            "target_count": len(compact["findings"]),
            "applied_count": applied_count,
            "completed_rewrite_count": completed_rewrite_count,
        }
    if application.get("decision_kind") != SEMANTIC_DISPOSITION_DECISION_KIND:
        raise PanelReviewError("semantic application decision_kind is invalid")
    expected_path = f"evals/expert-panel/{review_id}/panel/decision.json"
    if decision_value != expected_path or decision_path.suffix != ".json":
        raise PanelReviewError(
            "semantic application decision path must name its canonical panel decision JSON"
        )
    expected_sha256 = _lowercase_sha256(
        decision_ref.get("sha256"), label="semantic application decision sha256"
    )
    if _sha256(decision_path) != expected_sha256:
        raise PanelReviewError("semantic application decision sha256 is stale")
    record = _json_object(decision_path, label="semantic disposition decision")
    if (
        record.get("kind") != application["decision_kind"]
        or record.get("review_id") != review_id
    ):
        raise PanelReviewError(
            "semantic application does not bind the named decision round and kind"
        )
    validate_decision_record(record, record_path=decision_path)

    packet_ref = record["packet"]
    packet_path = _canonical_relative_path(
        packet_ref["path"], label="semantic application packet path"
    )
    packet = _json_object(packet_path, label="semantic disposition packet")
    rewrite_target_ids = frozenset(
        decision["target_id"]
        for decision in record["semantic_decisions"]
        if decision["winning_disposition"] == "rewrite"
    )
    _validate_semantic_packet_current(
        packet,
        audit,
        allowed_missing_target_ids=rewrite_target_ids,
    )

    root_semantic, reference_semantic = _semantic_audit_sections(audit)
    semantics = {"root": root_semantic, "reference": reference_semantic}
    applied_count = 0
    completed_rewrite_count = 0
    for axis in sorted(SEMANTIC_AXES):
        semantic = semantics[axis]
        candidates = semantic.get("candidates")
        contract = semantic.get("disposition_contract")
        entries = contract.get("entries") if isinstance(contract, dict) else None
        if not isinstance(candidates, list) or not all(
            isinstance(candidate, dict) for candidate in candidates
        ):
            raise PanelReviewError(
                f"semantic application current {axis} candidates must be an array"
            )
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise PanelReviewError(
                f"semantic application current {axis} entries must be an array"
            )
        candidates_by_id = {
            str(candidate.get("candidate_id")): candidate for candidate in candidates
        }
        entries_by_id = {str(entry.get("candidate_id")): entry for entry in entries}
        if len(candidates_by_id) != len(candidates) or len(entries_by_id) != len(entries):
            raise PanelReviewError(
                f"semantic application current {axis} IDs are missing or duplicated"
            )
        for decision in record["semantic_decisions"]:
            if decision["axis"] != axis:
                continue
            candidate_id = decision["candidate_id"]
            winner = decision["winning_disposition"]
            candidate = candidates_by_id.get(candidate_id)
            entry = entries_by_id.get(candidate_id)
            if winner == "rewrite":
                if candidate is not None:
                    raise PanelReviewError(
                        f"semantic rewrite target remains current: {axis}:{candidate_id}"
                    )
                if entry is not None:
                    raise PanelReviewError(
                        f"semantic rewrite target retains a disposition entry: {axis}:{candidate_id}"
                    )
                completed_rewrite_count += 1
                continue
            if candidate is None or entry is None:
                raise PanelReviewError(
                    f"semantic decision application entry is missing: {axis}:{candidate_id}"
                )
            if _semantic_entry_mismatches(
                axis=axis,
                candidate=candidate,
                entry=entry,
            ):
                raise PanelReviewError(
                    f"semantic decision application entry is stale: {axis}:{candidate_id}"
                )
            if entry.get("disposition") != winner:
                raise PanelReviewError(
                    "semantic decision application disposition mismatch: "
                    f"{axis}:{candidate_id}; expected={winner}; "
                    f"actual={entry.get('disposition')}"
                )
            applied_count += 1
    return {
        "schema_version": SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION,
        "kind": SEMANTIC_DISPOSITION_APPLICATION_KIND,
        "review_id": review_id,
        "decision_kind": SEMANTIC_DISPOSITION_DECISION_KIND,
        "decision": dict(decision_ref),
        "status": "current",
        "target_count": len(record["semantic_decisions"]),
        "applied_count": applied_count,
        "completed_rewrite_count": completed_rewrite_count,
    }


def validate_semantic_decision_application(
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Validate the canonical fixed Semantic attestation against current policy."""

    fixed_relative = panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH
    fixed_path = ROOT / fixed_relative
    try:
        bound = reviewer_manifest.read_bound_regular_file(
            fixed_path,
            max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
            label="semantic application fixed attestation",
        )
        selector = panel_attestation.parse_attestation_storage_selector_bytes(
            bound.raw
        )
        review_id = _non_blank(
            selector.get("review_id"),
            label="semantic application fixed review_id",
        )
        decided_on = _iso_date(
            selector.get("decided_on"),
            label="semantic application fixed decided_on",
        )
        current_bindings, contract_fingerprint = (
            _semantic_fixed_current_validation(
                audit=audit,
                attestation_selector=selector,
            )
        )
        compact = panel_attestation.parse_attestation_bytes(
            bound.raw,
            expected_path=fixed_relative,
            expected_review_contract_fingerprint=contract_fingerprint,
            expected_semantic_current_bindings=current_bindings,
        )
    except (
        reviewer_manifest.ManifestError,
        panel_attestation.AttestationError,
    ) as exc:
        raise PanelReviewError(
            f"semantic application fixed attestation is invalid: {exc}"
        ) from exc

    root_semantic, reference_semantic = _semantic_audit_sections(audit)
    semantics = {"root": root_semantic, "reference": reference_semantic}
    applied_count = 0
    completed_rewrite_count = 0
    for axis in sorted(SEMANTIC_AXES):
        semantic = semantics[axis]
        candidates = semantic.get("candidates")
        contract = semantic.get("disposition_contract")
        entries = contract.get("entries") if isinstance(contract, dict) else None
        if not isinstance(candidates, list) or not all(
            isinstance(candidate, dict) for candidate in candidates
        ):
            raise PanelReviewError(
                f"semantic application current {axis} candidates must be an array"
            )
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise PanelReviewError(
                f"semantic application current {axis} entries must be an array"
            )
        eligible = _semantic_eligible_candidates(axis=axis, semantic=semantic)
        candidates_by_id = {
            str(candidate.get("candidate_id")): candidate
            for candidate in eligible
        }
        entries_by_id = {
            str(entry.get("candidate_id")): entry for entry in entries
        }
        if (
            len(candidates_by_id) != len(eligible)
            or len(entries_by_id) != len(entries)
        ):
            raise PanelReviewError(
                f"semantic application current {axis} IDs are missing or duplicated"
            )
        for finding in compact["findings"]:
            if finding["axis"] != axis:
                continue
            candidate_id = finding["target_id"].split(":", 1)[1]
            winner = finding["result"]["winning_disposition"]
            candidate = candidates_by_id.get(candidate_id)
            entry = entries_by_id.get(candidate_id)
            if winner == "rewrite":
                if candidate is not None or entry is not None:
                    raise PanelReviewError(
                        "semantic fixed rewrite target remains current"
                    )
                completed_rewrite_count += 1
                continue
            if candidate is None or entry is None:
                raise PanelReviewError(
                    "semantic fixed attestation application entry is missing"
                )
            if _semantic_entry_mismatches(
                axis=axis,
                candidate=candidate,
                entry=entry,
            ):
                raise PanelReviewError(
                    "semantic fixed attestation application entry is stale"
                )
            if entry.get("disposition") != winner:
                raise PanelReviewError(
                    "semantic fixed attestation disposition mismatch"
                )
            applied_count += 1

    return {
        "schema_version": SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION,
        "kind": SEMANTIC_DISPOSITION_APPLICATION_KIND,
        "review_id": compact["review_id"],
        "decision_kind": panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND,
        "decision": {
            "path": fixed_relative,
            "sha256": bound.sha256,
        },
        "status": "current",
        "target_count": len(compact["findings"]),
        "applied_count": applied_count,
        "completed_rewrite_count": completed_rewrite_count,
    }


def _professional_v3_panel_contract(
    *,
    target_count: int | None = None,
    include_selection_derivation: bool = True,
) -> dict[str, Any]:
    """Return the schema-3 exact-carry extension of the schema-2 contract."""

    if target_count is None:
        target_count = PROFESSIONAL_PACKAGE_COUNT
    contract = copy.deepcopy(
        _professional_completeness_panel_contract(
            target_count=target_count,
            include_selection_derivation=include_selection_derivation,
        )
    )
    contract["decision_method"] = (
        PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
    )
    contract["reviewer_pool_contract"] = {
        "minimum_current_reviewer_count_when_fresh_targets_present": (
            PANEL_SIZE
        ),
        "current_reviewer_count_when_no_fresh_targets": 0,
        "assignments_non_empty_for_current_ballots": True,
        "unique_voter_id_per_round": True,
        "unique_agent_id_per_round": True,
        "fixed_pool_size": False,
    }
    contract["incremental_review_contract"] = {
        "algorithm": "exact-package-carry-forward-v1",
        "bootstrap_requires_all_fresh": True,
        "legacy_baseline_allowed": False,
        "carry_unit": "whole-professional-package",
        "dependency_depth": "one-hop-factual-material",
        "origin_mode": "direct-last-fresh-decision",
        "maximum_origin_depth": 1,
        "maximum_plan_lineage_depth": (
            PROFESSIONAL_COMPLETENESS_MAX_PLAN_LINEAGE_DEPTH
        ),
        "lineage_limit_disposition": "full-fresh-checkpoint",
        "stale_contract_baseline_policy": (
            "audit-envelope-only-force-full-fresh-v1"
        ),
        "carried_target_votes_allowed": False,
        "carried_target_effective_qualification_source": (
            "validated-direct-fresh-origin"
        ),
        "maintainer_partition_override_allowed": False,
        "discovery_capsule_kind": (
            PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND
        ),
        "candidate_request_kind": (
            PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND
        ),
        "capsule_kind": PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
        "capsule_chain": (
            "discovery-capsule-to-immutable-candidate-request-to-final-review-capsule"
        ),
    }
    contract["semantic_grounding_contract"] = (
        _professional_v3_grounding_contract()
    )
    return contract


def _professional_v3_base_targets(
    targets: object,
) -> list[dict[str, Any]]:
    if not isinstance(targets, list):
        raise PanelReviewError("schema-3 professional_targets must be an array")
    base_targets: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        if not isinstance(target, dict) or "review_binding" not in target:
            raise PanelReviewError(
                f"schema-3 professional_targets[{index}] lacks review_binding"
            )
        base = copy.deepcopy(target)
        base.pop("review_binding")
        base.pop("package_fingerprint", None)
        base_targets.append(base)
    return base_targets


def _professional_v3_rubric() -> dict[str, Any]:
    return {
        "accept": (
            "Accept only when every criterion is satisfied for the complete Skill "
            "package and its responsibility boundary."
        ),
        "correct": (
            "Require professional correction when any criterion exposes an error, "
            "material omission, responsibility gap, or unverifiable output."
        ),
        "criteria": dict(sorted(PROFESSIONAL_COMPLETENESS_CRITERIA.items())),
        "reason_codes": {
            decision: sorted(PROFESSIONAL_REASON_CODES[decision])
            for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
        },
        "source_grounding": _professional_v3_grounding_contract(),
    }


def _professional_v2_projection_from_v3(
    packet: dict[str, Any],
    *,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    base_targets = _professional_v3_base_targets(
        packet.get("professional_targets")
    )
    _layer_counts, legacy_selection = _professional_package_profile(
        len(base_targets),
        validation_mode=validation_mode,
    )
    panel_contract = _professional_completeness_panel_contract(
        target_count=len(base_targets),
        include_selection_derivation=not legacy_selection,
    )
    if validation_mode == VALIDATION_MODE_HISTORICAL:
        historical_selection = (
            packet.get("panel_contract", {})
            .get("adjacency_contract", {})
            .get("required_candidate_selection")
        )
        if not isinstance(historical_selection, dict):
            raise PanelReviewError(
                "historical schema-3 selection contract is invalid"
            )
        panel_contract["adjacency_contract"][
            "required_candidate_selection"
        ] = copy.deepcopy(historical_selection)
    projected_targets = []
    for target in base_targets:
        projected = copy.deepcopy(target)
        projected["package_fingerprint"] = (
            _canonical_json_sha256(
                professional_carry.professional_candidate_material_binding(
                    projected
                )
            )
            if "entry_fingerprint" not in projected["registry"]
            else _canonical_json_sha256(projected)
        )
        projected_targets.append(projected)
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "review_id": packet.get("review_id"),
        "created_on": packet.get("created_on"),
        "source_fingerprints": {
            "professional_packages": _canonical_json_sha256(projected_targets)
        },
        "panel_contract": panel_contract,
        "rubric": {
            key: value
            for key, value in _professional_v3_rubric().items()
            if key != "source_grounding"
        },
        "professional_targets": projected_targets,
        "limitations": ["Schema-3 compatibility projection."],
    }


def _professional_v3_binding_state(
    base_targets: list[dict[str, Any]],
    *,
    review_contract_fingerprint: str,
    historical_content_binding: bool = False,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    bindings = (
        professional_carry.professional_historical_content_review_bindings(
            base_targets
        )
        if historical_content_binding
        else professional_carry.professional_review_bindings(base_targets)
    )
    snapshot = professional_carry.professional_carry_snapshot(
        bindings,
        review_contract_fingerprint=review_contract_fingerprint,
    )
    return bindings, snapshot


def _artifact_reference_shape(
    value: object,
    *,
    label: str,
    require_review_id: bool,
    expected_kind: str | None = None,
    expected_axis: str | None = None,
) -> dict[str, str]:
    fields = {"path", "sha256"}
    if require_review_id:
        fields.add("review_id")
    if expected_kind is not None:
        fields.add("kind")
    if expected_axis is not None:
        fields.add("axis")
    if not isinstance(value, dict) or set(value) != fields:
        raise PanelReviewError(f"{label} fields are invalid")
    path = value.get("path")
    if (
        not isinstance(path, str)
        or not path
        or "\\" in path
        or PurePosixPath(path).is_absolute()
        or PurePosixPath(path).as_posix() != path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        raise PanelReviewError(f"{label}.path is not canonical")
    normalized = {
        "path": path,
        "sha256": _lowercase_sha256(
            value.get("sha256"), label=f"{label}.sha256"
        ),
    }
    if expected_kind is not None:
        if value.get("kind") != expected_kind:
            raise PanelReviewError(f"{label}.kind is invalid")
        normalized["kind"] = expected_kind
    if expected_axis is not None:
        if value.get("axis") != expected_axis:
            raise PanelReviewError(f"{label}.axis is invalid")
        normalized["axis"] = expected_axis
    if require_review_id:
        normalized["review_id"] = _non_blank(
            value.get("review_id"), label=f"{label}.review_id"
        )
    if (
        expected_kind is not None
        and expected_axis == PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS
    ):
        _validate_professional_artifact_layout(
            normalized, expected_kind=expected_kind, label=label
        )
    return normalized


def _professional_attestation_reference_shape(
    value: object, *, label: str
) -> dict[str, str]:
    expected_fields = {"path", "sha256", "kind", "axis", "review_id"}
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise PanelReviewError(f"{label} fields are invalid")
    if (
        value.get("path")
        != panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
        or value.get("kind")
        != panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND
        or value.get("axis") != PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS
    ):
        raise PanelReviewError(f"{label} path, kind, or axis is invalid")
    review_id = _non_blank(value.get("review_id"), label=f"{label}.review_id")
    if VOTER_ID_PATTERN.fullmatch(review_id) is None:
        raise PanelReviewError(f"{label}.review_id is invalid")
    return {
        "path": value["path"],
        "sha256": _lowercase_sha256(
            value.get("sha256"), label=f"{label}.sha256"
        ),
        "kind": value["kind"],
        "axis": value["axis"],
        "review_id": review_id,
    }


def _validate_professional_artifact_layout(
    reference: dict[str, str],
    *,
    expected_kind: str,
    label: str,
    validation_root: Path | None = None,
) -> None:
    """Validate the fixed schema-3 round layout and optional exact root."""

    review_id = reference.get("review_id")
    path = reference["path"]
    if not isinstance(review_id, str) or not review_id:
        raise PanelReviewError(f"{label}.review_id is invalid")
    parts = path.split("/")
    filename = parts[-1]
    if expected_kind == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        expected_suffix = [review_id, "packet.json"]
    elif expected_kind == PROFESSIONAL_COMPLETENESS_DECISION_KIND:
        expected_suffix = [review_id, "panel", "decision.json"]
    elif expected_kind == PROFESSIONAL_COMPLETENESS_BALLOT_KIND:
        if (
            not filename.endswith(".json")
            or VOTER_ID_PATTERN.fullmatch(filename[:-5]) is None
            or filename == "decision.json"
        ):
            raise PanelReviewError(f"{label}.path ballot filename is invalid")
        expected_suffix = [review_id, "panel", filename]
    elif expected_kind == PROFESSIONAL_COMPLETENESS_CAPSULE_KIND:
        if (
            not filename.endswith(".json")
            or VOTER_ID_PATTERN.fullmatch(filename[:-5]) is None
        ):
            raise PanelReviewError(f"{label}.path capsule filename is invalid")
        expected_suffix = [review_id, "capsules", filename]
    elif expected_kind == PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND:
        if (
            not filename.endswith(".json")
            or VOTER_ID_PATTERN.fullmatch(filename[:-5]) is None
        ):
            raise PanelReviewError(
                f"{label}.path discovery capsule filename is invalid"
            )
        expected_suffix = [review_id, "discovery-capsules", filename]
    elif expected_kind == PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND:
        if (
            not filename.endswith(".json")
            or VOTER_ID_PATTERN.fullmatch(filename[:-5]) is None
        ):
            raise PanelReviewError(
                f"{label}.path candidate request filename is invalid"
            )
        expected_suffix = [review_id, "candidate-requests", filename]
    else:
        raise PanelReviewError(f"{label}.kind has no schema-3 layout")
    if validation_root is None:
        layout_matches = parts[-len(expected_suffix) :] == expected_suffix
    else:
        if validation_root.resolve() == ROOT.resolve():
            layout_matches = any(
                parts == [*prefix, *expected_suffix]
                for prefix in (
                    ["evals", "expert-panel"],
                    [".rd-skills", "expert-panel"],
                )
            )
        else:
            layout_matches = parts == expected_suffix
    if not layout_matches:
        raise PanelReviewError(
            f"{label}.path does not match its canonical review round layout"
        )


def _validate_professional_v3_review_plan_shape(
    value: object,
    *,
    target_ids: list[str],
    review_contract_fingerprint: str,
) -> dict[str, Any]:
    fields = {
        "algorithm",
        "review_contract_fingerprint",
        "plan_lineage_depth",
        "baseline",
        "fresh_targets",
        "carried_targets",
        "summary",
        "plan_fingerprint",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise PanelReviewError("schema-3 review_plan fields are invalid")
    if value.get("algorithm") != "exact-package-carry-forward-v1":
        raise PanelReviewError("schema-3 review_plan algorithm is invalid")
    if value.get("review_contract_fingerprint") != review_contract_fingerprint:
        raise PanelReviewError("schema-3 review_plan contract fingerprint is stale")
    lineage_depth = value.get("plan_lineage_depth")
    if (
        type(lineage_depth) is not int
        or lineage_depth < 0
        or lineage_depth > PROFESSIONAL_COMPLETENESS_MAX_PLAN_LINEAGE_DEPTH
    ):
        raise PanelReviewError(
            "schema-3 review_plan lineage depth is outside 0..8"
        )
    baseline = value.get("baseline")
    if baseline is not None:
        if not isinstance(baseline, dict) or set(baseline) not in (
            {"decision", "packet"},
            {"attestation"},
        ):
            raise PanelReviewError("schema-3 review_plan baseline fields are invalid")
        if "attestation" in baseline:
            _professional_attestation_reference_shape(
                baseline["attestation"],
                label="schema-3 review_plan baseline attestation",
            )
        else:
            _artifact_reference_shape(
                baseline.get("decision"),
                label="schema-3 review_plan baseline decision",
                require_review_id=True,
                expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            )
            _artifact_reference_shape(
                baseline.get("packet"),
                label="schema-3 review_plan baseline packet",
                require_review_id=True,
                expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            )
    fresh = value.get("fresh_targets")
    carried = value.get("carried_targets")
    if not isinstance(fresh, list) or not isinstance(carried, list):
        raise PanelReviewError(
            "schema-3 review_plan partitions must be arrays"
        )
    fresh_ids: list[str] = []
    for index, row in enumerate(fresh):
        if not isinstance(row, dict) or set(row) != {
            "skill_id",
            "reason_codes",
        }:
            raise PanelReviewError(
                f"schema-3 review_plan fresh_targets[{index}] fields are invalid"
            )
        skill_id = _non_blank(
            row.get("skill_id"),
            label=f"schema-3 review_plan fresh_targets[{index}].skill_id",
        )
        reasons = _string_list(
            row.get("reason_codes"),
            label=f"schema-3 review_plan fresh_targets[{index}].reason_codes",
            allow_empty=False,
        )
        if reasons != sorted(set(reasons)):
            raise PanelReviewError(
                "schema-3 fresh target reason codes must be sorted and unique"
            )
        fresh_ids.append(skill_id)
    carried_ids: list[str] = []
    for index, row in enumerate(carried):
        legacy_origin = isinstance(row, dict) and set(row) == {
            "skill_id",
            "review_unit_binding",
            "origin_decision",
            "origin_target_decision_fingerprint",
        }
        attested_origin = isinstance(row, dict) and set(row) == {
            "skill_id",
            "review_unit_binding",
            "origin_attestation",
            "origin_verdict_digest",
        }
        if not legacy_origin and not attested_origin:
            raise PanelReviewError(
                f"schema-3 review_plan carried_targets[{index}] fields are invalid"
            )
        skill_id = _non_blank(
            row.get("skill_id"),
            label=f"schema-3 review_plan carried_targets[{index}].skill_id",
        )
        _lowercase_sha256(
            row.get("review_unit_binding"),
            label=f"schema-3 carried target {skill_id} review binding",
        )
        if legacy_origin:
            _artifact_reference_shape(
                row.get("origin_decision"),
                label=f"schema-3 carried target {skill_id} origin decision",
                require_review_id=True,
                expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            )
            origin_digest = row.get("origin_target_decision_fingerprint")
        else:
            _professional_attestation_reference_shape(
                row.get("origin_attestation"),
                label=f"schema-3 carried target {skill_id} origin attestation",
            )
            origin_digest = row.get("origin_verdict_digest")
        _lowercase_sha256(
            origin_digest,
            label=f"schema-3 carried target {skill_id} origin fingerprint",
        )
        carried_ids.append(skill_id)
    if fresh_ids != sorted(set(fresh_ids)):
        raise PanelReviewError("schema-3 fresh targets must be sorted and unique")
    if carried_ids != sorted(set(carried_ids)):
        raise PanelReviewError("schema-3 carried targets must be sorted and unique")
    if set(fresh_ids) & set(carried_ids) or sorted(
        set(fresh_ids) | set(carried_ids)
    ) != target_ids:
        raise PanelReviewError(
            "schema-3 review_plan must partition every target exactly once"
        )
    summary = value.get("summary")
    expected_summary = {
        "total_target_count": len(target_ids),
        "fresh_target_count": len(fresh_ids),
        "carried_target_count": len(carried_ids),
    }
    if summary != expected_summary:
        raise PanelReviewError("schema-3 review_plan summary is stale")
    without_fingerprint = dict(value)
    plan_fingerprint = without_fingerprint.pop("plan_fingerprint")
    if plan_fingerprint != _canonical_json_sha256(without_fingerprint):
        raise PanelReviewError("schema-3 review_plan fingerprint is stale")
    if baseline is None and carried_ids:
        raise PanelReviewError(
            "schema-3 bootstrap review_plan cannot carry targets"
        )
    if carried_ids and lineage_depth == 0:
        raise PanelReviewError(
            "schema-3 carried review_plan must have positive lineage depth"
        )
    if not carried_ids and lineage_depth != 0:
        raise PanelReviewError(
            "schema-3 full-fresh checkpoint must reset lineage depth to zero"
        )
    return value


def _professional_v3_review_plan(
    *,
    current_bindings: dict[str, dict[str, Any]],
    review_contract_fingerprint: str,
    baseline_state: dict[str, Any] | None,
) -> dict[str, Any]:
    prior_snapshot = (
        baseline_state["snapshot"] if baseline_state is not None else None
    )
    prior_dependencies = (
        baseline_state["dependencies"] if baseline_state is not None else None
    )
    carry_plan = professional_carry.plan_exact_professional_carry_forward(
        current_bindings=current_bindings,
        prior_snapshot=prior_snapshot,
        prior_decision_dependencies=prior_dependencies,
        review_contract_fingerprint=review_contract_fingerprint,
    )
    baseline_depth = (
        baseline_state["plan_lineage_depth"]
        if baseline_state is not None
        else 0
    )
    if (
        carry_plan["carry_target_ids"]
        and baseline_depth
        >= PROFESSIONAL_COMPLETENESS_MAX_PLAN_LINEAGE_DEPTH
    ):
        carry_plan = {
            **carry_plan,
            "fresh_target_ids": sorted(current_bindings),
            "carry_target_ids": [],
            "reasons_by_target": {
                skill_id: sorted(
                    {
                        *carry_plan["reasons_by_target"][skill_id],
                        "lineage-depth-limit",
                    }
                )
                for skill_id in sorted(current_bindings)
            },
        }
    baseline = None
    if baseline_state is not None:
        if "attestation_ref" in baseline_state:
            baseline = {"attestation": baseline_state["attestation_ref"]}
        else:
            baseline = {
                "decision": baseline_state["decision_ref"],
                "packet": baseline_state["packet_ref"],
            }
    fresh_targets = [
        {
            "skill_id": skill_id,
            "reason_codes": carry_plan["reasons_by_target"][skill_id],
        }
        for skill_id in carry_plan["fresh_target_ids"]
    ]
    carried_targets = []
    for skill_id in carry_plan["carry_target_ids"]:
        if baseline_state is None:
            raise PanelReviewError("carry plan lacks a validated baseline")
        origin = baseline_state["origins"][skill_id]
        if "attestation_ref" in baseline_state:
            carried_targets.append(
                {
                    "skill_id": skill_id,
                    "review_unit_binding": current_bindings[skill_id][
                        "review_unit_binding"
                    ],
                    "origin_attestation": origin["attestation_ref"],
                    "origin_verdict_digest": origin[
                        "origin_verdict_digest"
                    ],
                }
            )
        else:
            carried_targets.append(
                {
                    "skill_id": skill_id,
                    "review_unit_binding": current_bindings[skill_id][
                        "review_unit_binding"
                    ],
                    "origin_decision": origin["decision_ref"],
                    "origin_target_decision_fingerprint": origin[
                        "target_decision_fingerprint"
                    ],
                }
            )
    plan: dict[str, Any] = {
        "algorithm": "exact-package-carry-forward-v1",
        "review_contract_fingerprint": review_contract_fingerprint,
        "plan_lineage_depth": (
            baseline_depth + 1 if carried_targets else 0
        ),
        "baseline": baseline,
        "fresh_targets": fresh_targets,
        "carried_targets": carried_targets,
        "summary": {
            "total_target_count": len(current_bindings),
            "fresh_target_count": len(fresh_targets),
            "carried_target_count": len(carried_targets),
        },
    }
    plan["plan_fingerprint"] = _canonical_json_sha256(plan)
    return plan


def _professional_v3_packet_limitations() -> list[str]:
    return [
        "Schema 3 carries only whole accepted packages through a bounded, recursively validated canonical plan lineage and direct last-fresh origin.",
        "Carry eligibility is authoritative on the conservative deterministic Professional currentness projection through canonical package_material_binding, review_unit_binding, complete Registry and ordered Reference authority, and direct one-hop dependency material bindings; raw content and SHA records remain provenance and artifact-integrity evidence only; unsupported or ambiguous material changes require affected-package fresh review.",
        "A full-fresh checkpoint resets plan lineage depth after recomputing its immediate predecessor effective evidence and reset trigger; superseded history is not recursively re-proved.",
        "Review capsules and deterministic byte proxies do not prove actual host tokens, latency, reviewer identity, credentials, behavior, production accuracy, or installed user experience.",
        "This packet does not by itself satisfy any formal release gate, and a static artifact tree cannot prove that historical rounds were not deleted.",
    ]


def _professional_v3_full_rereview_input_projection(
    packet: dict[str, Any],
    *,
    bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the same deduplicated capsule input used by a full rereview."""

    return {
        "review_contract_fingerprint": packet[
            "review_contract_fingerprint"
        ],
        "review_projection": _professional_v3_capsule_projection_from_packet(
            packet=packet,
            assigned_skill_ids=sorted(
                target["skill_id"]
                for target in packet["professional_targets"]
            ),
            reviewer_added_requests_by_target=None,
            bindings=bindings,
        ),
    }


def _professional_v3_capsule_input_projection(
    capsule: dict[str, Any],
) -> dict[str, Any]:
    """Exclude reviewer/date/limitation administration from cost evidence."""

    return {
        "review_contract_fingerprint": capsule[
            "review_contract_fingerprint"
        ],
        "review_projection": capsule["review_projection"],
    }


def _professional_v3_input_block(value: dict[str, Any]) -> dict[str, Any]:
    payload = professional_carry.canonical_json_bytes(value)
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "canonical_json_bytes_proxy": len(payload),
    }


def _professional_v3_effective_input_blocks(
    *,
    review_contract_fingerprint: str,
    discovery_projection: dict[str, Any],
    assigned_skill_ids: list[str],
    reviewer_added_requests: list[dict[str, Any]],
    final_projection: dict[str, Any],
) -> list[dict[str, Any]]:
    """Canonicalize assignment-neutral material blocks for cost evidence.

    Each target receives exactly three votes, so the summary later caps an
    identical block at three semantic copies even when a larger reviewer pool
    partitions those votes across more physical capsules.
    """

    values: list[dict[str, Any]] = [
        {
            "block_kind": "review-binding",
            "review_contract_fingerprint": review_contract_fingerprint,
        }
    ]
    for row in discovery_projection["material_catalog"]:
        values.append({"block_kind": "source-material", "value": row})
    for row in final_projection["material_catalog"]:
        values.append({"block_kind": "source-material", "value": row})
    for row in discovery_projection["boundary_catalog"]:
        values.append({"block_kind": "candidate-boundary", "value": row})
    for row in discovery_projection["targets"]:
        values.append({"block_kind": "discovery-target", "value": row})
    for row in final_projection["targets"]:
        values.append({"block_kind": "final-review-target", "value": row})
    for skill_id in assigned_skill_ids:
        values.append(
            {
                "block_kind": "candidate-request-closure",
                "target_skill_id": skill_id,
            }
        )
    for row in reviewer_added_requests:
        values.append({"block_kind": "reviewer-added-request", "value": row})
    blocks_by_digest: dict[str, dict[str, Any]] = {}
    for value in values:
        block = _professional_v3_input_block(value)
        existing = blocks_by_digest.get(block["sha256"])
        if existing is not None and existing != block:
            raise PanelReviewError(
                "schema-3 input block digest has conflicting canonical size"
            )
        blocks_by_digest[block["sha256"]] = block
    return [blocks_by_digest[digest] for digest in sorted(blocks_by_digest)]


def _professional_v3_effective_capsule_input_blocks(
    *,
    discovery_capsule: dict[str, Any],
    candidate_request: dict[str, Any],
    capsule: dict[str, Any],
) -> list[dict[str, Any]]:
    return _professional_v3_effective_input_blocks(
        review_contract_fingerprint=capsule[
            "review_contract_fingerprint"
        ],
        discovery_projection=discovery_capsule["discovery_projection"],
        assigned_skill_ids=candidate_request["assigned_fresh_target_ids"],
        reviewer_added_requests=candidate_request["reviewer_added_requests"],
        final_projection=capsule["review_projection"],
    )


def _professional_v3_full_rereview_input_blocks(
    packet: dict[str, Any],
    *,
    bindings: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    effective_bindings = bindings or professional_carry.professional_review_bindings(
        packet["professional_targets"]
    )
    assigned = sorted(effective_bindings)
    discovery = _professional_v3_discovery_projection_from_packet(
        packet=packet,
        assigned_skill_ids=assigned,
        bindings=effective_bindings,
    )
    final = _professional_v3_capsule_projection_from_packet(
        packet=packet,
        assigned_skill_ids=assigned,
        reviewer_added_requests_by_target=None,
        bindings=effective_bindings,
    )
    return _professional_v3_effective_input_blocks(
        review_contract_fingerprint=packet["review_contract_fingerprint"],
        discovery_projection=discovery,
        assigned_skill_ids=assigned,
        reviewer_added_requests=[],
        final_projection=final,
    )


def _load_professional_attestation_baseline(
    path: Path,
    *,
    current_bindings: dict[str, dict[str, Any]],
    current_snapshot: dict[str, Any],
    review_contract_fingerprint: str,
    expected_attestation_sha256: str | None = None,
) -> dict[str, Any]:
    expected_path = (
        ROOT / panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
    ).absolute()
    if path.absolute() != expected_path:
        raise PanelReviewError(
            "Professional baseline attestation must use its canonical fixed path"
        )
    bound = reviewer_manifest.read_bound_regular_file(
        path,
        max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
        label="Professional baseline attestation",
    )
    authenticated_sha256 = expected_attestation_sha256
    if authenticated_sha256 is None:
        head_blob = _git_output(
            "show",
            f"HEAD:{panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH}",
        ).stdout
        authenticated_sha256 = hashlib.sha256(head_blob).hexdigest()
        if head_blob != bound.raw:
            raise PanelReviewError(
                "Professional baseline attestation differs from its HEAD authority"
            )
    if bound.sha256 != _lowercase_sha256(
        authenticated_sha256,
        label="Professional baseline authenticated sha256",
    ):
        raise PanelReviewError(
            "Professional baseline attestation selector is stale"
        )
    try:
        preliminary = (
            panel_attestation.parse_attestation_storage_selector_bytes(
                bound.raw
            )
        )
    except panel_attestation.AttestationError as exc:
        raise PanelReviewError(
            "Professional baseline attestation selector is invalid"
        ) from exc
    raw_findings = preliminary.get("findings")
    if not isinstance(raw_findings, list):
        raise PanelReviewError(
            "Professional baseline attestation findings are invalid"
        )
    authenticated_claims = _professional_authenticated_claims_from_findings(
        raw_findings
    )
    attestation, eligible_ids = (
        panel_attestation.parse_professional_baseline_bytes(
            bound.raw,
            expected_path=(
                panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            ),
            expected_professional_current_bindings=(
                _professional_attestation_bindings_from_state(
                    current_bindings=current_bindings,
                    authenticated_claims=authenticated_claims,
                )
            ),
        )
    )
    reference = {
        "path": panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
        "sha256": bound.sha256,
        "kind": panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND,
        "axis": PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": attestation["review_id"],
    }
    findings = {row["skill_id"]: row for row in attestation["findings"]}
    if (
        set(findings) != set(current_bindings)
    ):
        raise PanelReviewError(
            "Professional baseline attestation target coverage is stale"
        )
    eligible_rows = {
        skill_id: findings[skill_id] for skill_id in sorted(eligible_ids)
    }

    prior_targets: dict[str, dict[str, Any]] = {}
    dependencies: dict[str, dict[str, Any]] = {}
    origins: dict[str, dict[str, Any]] = {}
    for skill_id, row in eligible_rows.items():
        prior_targets[skill_id] = copy.deepcopy(
            current_snapshot["targets"][skill_id]
        )
        dependencies[skill_id] = copy.deepcopy(
            row["result"]["review_dependencies"]
        )
        origins[skill_id] = {
            "attestation_ref": reference,
            "origin_verdict_digest": row["provenance"]["origin"][
                "origin_verdict_digest"
            ],
            "finding": copy.deepcopy(row),
        }
    return {
        "attestation_ref": reference,
        "snapshot": {
            "review_contract_fingerprint": attestation[
                "review_contract_fingerprint"
            ],
            "targets": prior_targets,
        },
        "dependencies": dependencies,
        "origins": origins,
        "plan_lineage_depth": attestation["summary"]["review_cost"][
            "plan_lineage_depth"
        ],
        "attestation": attestation,
    }


def prepare_professional_completeness_packet_v3(
    *,
    review_id: str,
    created_on: str,
    baseline_decision_path: Path | None = None,
    baseline_attestation_path: Path | None = None,
    baseline_attestation_sha256: str | None = None,
    root: Path = ROOT,
    validation_root: Path = ROOT,
) -> dict[str, Any]:
    """Build one schema-3 packet; no maintainer-supplied partition is accepted."""

    _non_blank(review_id, label="review_id")
    if VOTER_ID_PATTERN.fullmatch(review_id) is None:
        raise PanelReviewError("schema-3 packet review_id is not canonical")
    _iso_date(created_on, label="created_on")
    base_targets = _professional_package_targets(root=root)
    review_contract_fingerprint = (
        _professional_evidence_review_contract_fingerprint()
    )
    bindings, snapshot = _professional_v3_binding_state(
        base_targets,
        review_contract_fingerprint=review_contract_fingerprint,
    )
    invocation_cache = _professional_v3_invocation_cache()
    baseline_state = None
    if baseline_decision_path is not None and baseline_attestation_path is not None:
        raise PanelReviewError(
            "schema-3 baseline decision and attestation are mutually exclusive"
        )
    if baseline_attestation_path is not None:
        baseline_state = _load_professional_attestation_baseline(
            baseline_attestation_path,
            current_bindings=bindings,
            current_snapshot=snapshot,
            review_contract_fingerprint=review_contract_fingerprint,
            expected_attestation_sha256=baseline_attestation_sha256,
        )
    if baseline_decision_path is not None:
        baseline_ref = _artifact_reference(
            baseline_decision_path,
            validation_root=validation_root,
            kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        )
        baseline_path = _canonical_artifact_path(
            baseline_ref["path"],
            validation_root=validation_root,
            label="schema-3 baseline decision path",
        )
        baseline_state = _load_professional_v3_baseline(
            baseline_path,
            validation_root=validation_root,
            forbidden_paths=set(),
            invocation_cache=invocation_cache,
            allow_stale_contract_checkpoint=True,
        )
    targets = [
        {
            **copy.deepcopy(target),
            "review_binding": copy.deepcopy(snapshot["targets"][target["skill_id"]]),
        }
        for target in base_targets
    ]
    packet = {
        "schema_version": PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "review_id": review_id,
        "created_on": created_on,
        "review_contract_fingerprint": review_contract_fingerprint,
        "panel_contract": _professional_v3_panel_contract(),
        "rubric": _professional_v3_rubric(),
        "professional_targets": targets,
        "review_plan": _professional_v3_review_plan(
            current_bindings=bindings,
            review_contract_fingerprint=review_contract_fingerprint,
            baseline_state=baseline_state,
        ),
        "limitations": _professional_v3_packet_limitations(),
    }
    _professional_v3_packet_state(
        packet,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=True,
        invocation_cache=invocation_cache,
    )
    return packet


def _professional_v3_packet_state(
    packet: dict[str, Any],
    *,
    validation_root: Path,
    artifact_path: Path | None,
    validate_baseline: bool,
    forbidden_paths: set[Path] | None = None,
    invocation_cache: dict[str, Any] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    validation_mode = _closed_validation_mode(validation_mode)
    cache = invocation_cache or _professional_v3_invocation_cache()
    packet_contract_hint = packet.get("review_contract_fingerprint")
    historical_source_contracts = {
        PROFESSIONAL_HISTORICAL_V2_REVIEW_CONTRACT_FINGERPRINT,
        PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT,
        PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT,
    }
    expected_packet_fields = (
        PROFESSIONAL_HISTORICAL_V3_PACKET_FIELDS
        if validation_mode == VALIDATION_MODE_HISTORICAL
        and packet_contract_hint in historical_source_contracts
        else PROFESSIONAL_V3_PACKET_FIELDS
    )
    if set(packet) != expected_packet_fields:
        raise PanelReviewError(
            "professional completeness packet fields do not match schema 3"
        )
    if (
        packet.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or packet.get("kind") != PROFESSIONAL_COMPLETENESS_PACKET_KIND
    ):
        raise PanelReviewError(
            "professional completeness schema-3 packet kind is invalid"
        )
    packet_review_id = _non_blank(
        packet.get("review_id"), label="packet.review_id"
    )
    if VOTER_ID_PATTERN.fullmatch(packet_review_id) is None:
        raise PanelReviewError("schema-3 packet review_id is not canonical")
    _iso_date(packet.get("created_on"), label="packet.created_on")
    packet_contract_fingerprint = _lowercase_sha256(
        packet.get("review_contract_fingerprint"),
        label="professional completeness schema-3 review contract",
    )
    expected_contract_fingerprint = (
        _professional_evidence_review_contract_fingerprint()
        if validation_mode == VALIDATION_MODE_CURRENT
        else packet_contract_fingerprint
    )
    if packet_contract_fingerprint != expected_contract_fingerprint:
        raise PanelReviewError(
            "professional completeness schema-3 review contract is stale"
        )
    raw_targets = packet.get("professional_targets")
    target_count = len(raw_targets) if isinstance(raw_targets, list) else -1
    _layer_counts, legacy_selection = _professional_package_profile(
        target_count,
        validation_mode=validation_mode,
    )
    registered_schema3_selection = False
    if validation_mode == VALIDATION_MODE_CURRENT:
        if not isinstance(raw_targets, list) or any(
            not isinstance(target, dict)
            or set(target) != PROFESSIONAL_V3_PACKET_TARGET_FIELDS
            for target in raw_targets
        ):
            raise PanelReviewError(
                "professional completeness schema-3 packet target fields are invalid"
            )
        if packet.get("panel_contract") != _professional_v3_panel_contract(
            target_count=target_count,
            include_selection_derivation=not legacy_selection,
        ):
            raise PanelReviewError(
                "professional completeness schema-3 panel contract is invalid"
            )
    else:
        current_registered_contract = (
            panel_contracts.professional_review_contract_fingerprint()
        )
        registered_contracts = {
            current_registered_contract,
            PROFESSIONAL_HISTORICAL_V2_REVIEW_CONTRACT_FINGERPRINT,
            PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT,
            PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT,
        }
        historical_panel_contract = packet.get("panel_contract")
        if (
            packet_contract_fingerprint not in registered_contracts
            or not isinstance(historical_panel_contract, dict)
            or historical_panel_contract.get("decision_method")
            != PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
            or historical_panel_contract.get("required_target_count")
            != target_count
        ):
            raise PanelReviewError(
                "professional completeness historical panel contract is invalid"
            )
        historical_selection = historical_panel_contract.get(
            "adjacency_contract", {}
        ).get("required_candidate_selection")
        if packet_contract_fingerprint in {
            current_registered_contract,
            PROFESSIONAL_HISTORICAL_V2_REVIEW_CONTRACT_FINGERPRINT,
        }:
            registered_schema3_selection = True
            expected_historical_selection = (
                _professional_adjacency_selection_contract(
                    target_count=target_count,
                    include_derivation=not legacy_selection,
                )
            )
            if historical_selection != expected_historical_selection:
                raise PanelReviewError(
                    "professional completeness historical selection contract is invalid"
                )
        elif not isinstance(
            historical_selection, _ProfessionalHistoricalV1Selection
        ):
            raise PanelReviewError(
                "professional completeness exact legacy contract is not bound"
            )
    projected = _professional_v2_projection_from_v3(
        packet,
        validation_mode=validation_mode,
    )
    if registered_schema3_selection:
        projected_selection = projected["panel_contract"][
            "adjacency_contract"
        ]["required_candidate_selection"]
        projected["panel_contract"]["adjacency_contract"][
            "required_candidate_selection"
        ] = _ProfessionalSchema3RegisteredSelection(projected_selection)
    _validate_professional_completeness_packet_v2(
        projected,
        validation_mode=validation_mode,
    )
    base_targets = _professional_v3_base_targets(raw_targets)
    bindings, snapshot = _professional_v3_binding_state(
        base_targets,
        review_contract_fingerprint=expected_contract_fingerprint,
        historical_content_binding=(
            validation_mode == VALIDATION_MODE_HISTORICAL
            and packet_contract_fingerprint
            != panel_contracts.professional_review_contract_fingerprint()
        ),
    )
    embedded_targets = packet["professional_targets"]
    for target in embedded_targets:
        skill_id = target["skill_id"]
        if target.get("review_binding") != snapshot["targets"][skill_id]:
            raise PanelReviewError(
                f"professional completeness schema-3 review binding is stale: {skill_id}"
            )
    if packet.get("rubric") != _professional_v3_rubric():
        raise PanelReviewError("professional completeness schema-3 rubric is invalid")
    if packet.get("limitations") != _professional_v3_packet_limitations():
        raise PanelReviewError(
            "professional completeness schema-3 limitations are not canonical"
        )
    target_ids = sorted(bindings)
    plan = _validate_professional_v3_review_plan_shape(
        packet.get("review_plan"),
        target_ids=target_ids,
        review_contract_fingerprint=expected_contract_fingerprint,
    )
    baseline_state = None
    if validate_baseline:
        baseline = plan["baseline"]
        has_carries = bool(plan["carried_targets"])
        if baseline is not None:
            if "attestation" in baseline:
                reference = _professional_attestation_reference_shape(
                    baseline["attestation"],
                    label="schema-3 review_plan baseline attestation",
                )
                baseline_state = _load_professional_attestation_baseline(
                    validation_root / reference["path"],
                    current_bindings=bindings,
                    current_snapshot=snapshot,
                    review_contract_fingerprint=(
                        expected_contract_fingerprint
                    ),
                    expected_attestation_sha256=reference["sha256"],
                )
                if baseline_state["attestation_ref"] != reference:
                    raise PanelReviewError(
                        "schema-3 review_plan baseline attestation reference is stale"
                    )
            else:
                normalized = _artifact_reference_shape(
                    baseline["decision"],
                    label="schema-3 review_plan baseline decision",
                    require_review_id=True,
                    expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                    expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                )
                _validate_professional_artifact_layout(
                    normalized,
                    expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                    label="schema-3 review_plan baseline decision",
                    validation_root=validation_root,
                )
                baseline_path = _canonical_artifact_path(
                    normalized["path"],
                    validation_root=validation_root,
                    label="schema-3 review_plan baseline decision.path",
                    forbidden_paths={
                        *(forbidden_paths or set()),
                        *(
                            {artifact_path}
                            if artifact_path is not None
                            else set()
                        ),
                    },
                )
                baseline_forbidden = {
                    *(forbidden_paths or set()),
                    *({artifact_path} if artifact_path is not None else set()),
                }
                _baseline_path, normalized, baseline_record = (
                    _professional_v3_cached_json_artifact(
                        normalized,
                        cache=cache,
                        validation_root=validation_root,
                        label="schema-3 review_plan immediate baseline decision",
                        expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                        expected_review_id=normalized["review_id"],
                        forbidden_paths=baseline_forbidden,
                    )
                )
                _professional_v3_decision_envelope(baseline_record)
                if baseline_record["packet"] != baseline["packet"]:
                    raise PanelReviewError(
                        "schema-3 review_plan immediate baseline packet is stale"
                    )
                baseline_state = _load_professional_v3_baseline(
                    baseline_path,
                    validation_root=validation_root,
                    forbidden_paths=baseline_forbidden,
                    invocation_cache=cache,
                    decision_reference=normalized,
                    validate_evidence=has_carries,
                    allow_stale_contract_checkpoint=not has_carries,
                    validation_mode=validation_mode,
                    expected_review_contract_fingerprint=(
                        expected_contract_fingerprint
                    ),
                )
                if baseline_state["decision_ref"] != baseline["decision"]:
                    raise PanelReviewError(
                        "schema-3 review_plan baseline decision reference is stale"
                    )
                if baseline_state["packet_ref"] != baseline["packet"]:
                    raise PanelReviewError(
                        "schema-3 review_plan baseline packet reference is stale"
                    )
        expected_plan = _professional_v3_review_plan(
            current_bindings=bindings,
            review_contract_fingerprint=expected_contract_fingerprint,
            baseline_state=baseline_state,
        )
        if plan != expected_plan:
            raise PanelReviewError(
                "schema-3 review_plan does not match exact carry recomputation"
            )
    return {
        "base_targets": base_targets,
        "bindings": bindings,
        "snapshot": snapshot,
        "plan": plan,
        "baseline_state": baseline_state,
        "review_bindings": {
            target["skill_id"]: copy.deepcopy(target["review_binding"])
            for target in embedded_targets
        },
    }


class _ProfessionalV3FrozenDict(dict):
    """Read-compatible recursively frozen dictionary."""

    @staticmethod
    def _immutable(*_args: object, **_kwargs: object) -> None:
        raise TypeError("schema-3 canonical packet state is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    __ior__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable

    def __deepcopy__(self, memo: dict[int, Any]) -> dict[Any, Any]:
        return {
            copy.deepcopy(key, memo): copy.deepcopy(value, memo)
            for key, value in self.items()
        }


class _ProfessionalV3FrozenList(list):
    """Read-compatible recursively frozen list."""

    @staticmethod
    def _immutable(*_args: object, **_kwargs: object) -> None:
        raise TypeError("schema-3 canonical packet state is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable

    def __deepcopy__(self, memo: dict[int, Any]) -> list[Any]:
        return [copy.deepcopy(value, memo) for value in self]


def _professional_v3_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        frozen = _ProfessionalV3FrozenDict()
        dict.__init__(
            frozen,
            (
                (key, _professional_v3_freeze(item))
                for key, item in value.items()
            ),
        )
        return frozen
    if isinstance(value, list):
        frozen_list = _ProfessionalV3FrozenList()
        list.__init__(
            frozen_list,
            (_professional_v3_freeze(item) for item in value),
        )
        return frozen_list
    return value


def _professional_v3_state_binding_projection(
    state: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: state[field]
        for field in (
            "base_targets",
            "bindings",
            "snapshot",
            "plan",
            "review_bindings",
        )
    }


def _professional_v3_packet_state_boundary() -> tuple[type, Any]:
    """Create the only issuer and verifier for immutable state handles."""

    seal = object()

    class _ProfessionalV3CanonicalPacketState:
        __slots__ = (
            "__packet",
            "__state",
            "__packet_digest",
            "__state_digest",
            "__packet_identity",
            "__state_identity",
            "__baseline_validated",
            "__seal",
        )

        def __new__(cls, *args: object, **kwargs: object) -> object:
            del cls, args, kwargs
            raise PanelReviewError(
                "schema-3 canonical packet state cannot be constructed directly"
            )

        @property
        def packet(self) -> dict[str, Any]:
            return self.__packet

        @property
        def state(self) -> dict[str, Any]:
            return self.__state

        def _validate_binding(
            self, packet: dict[str, Any], *, require_baseline: bool
        ) -> None:
            try:
                verified = (
                    self.__seal is seal
                    and id(self.__packet) == self.__packet_identity
                    and id(self.__state) == self.__state_identity
                    and isinstance(self.__packet, _ProfessionalV3FrozenDict)
                    and isinstance(self.__state, _ProfessionalV3FrozenDict)
                )
            except AttributeError:
                verified = False
            if not verified:
                raise PanelReviewError(
                    "schema-3 canonical packet state seal is invalid"
                )
            if require_baseline and not self.__baseline_validated:
                raise PanelReviewError(
                    "schema-3 canonical packet state lacks baseline validation"
                )
            if packet is self.__packet:
                return
            if _canonical_json_sha256(packet) != self.__packet_digest:
                raise PanelReviewError(
                    "schema-3 canonical packet state belongs to another packet"
                )
            if _canonical_json_sha256(
                _professional_v3_state_binding_projection(self.__state)
            ) != self.__state_digest:
                raise PanelReviewError(
                    "schema-3 canonical packet state digest is stale"
                )

    def canonical_packet_state(
        packet: dict[str, Any],
        *,
        supplied_state: (
            dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
        ),
        validation_root: Path,
        artifact_path: Path | None,
        validate_baseline: bool,
        forbidden_paths: set[Path] | None = None,
        invocation_cache: dict[str, Any] | None = None,
        validation_mode: str = VALIDATION_MODE_CURRENT,
    ) -> _ProfessionalV3CanonicalPacketState:
        """Return only packet-derived state, rejecting inconsistent input."""

        if isinstance(supplied_state, _ProfessionalV3CanonicalPacketState):
            supplied_state._validate_binding(
                packet, require_baseline=validate_baseline
            )
            return supplied_state

        authoritative = _professional_v3_packet_state(
            packet,
            validation_root=validation_root,
            artifact_path=artifact_path,
            validate_baseline=validate_baseline,
            forbidden_paths=forbidden_paths,
            invocation_cache=invocation_cache,
            validation_mode=validation_mode,
        )
        if supplied_state is not None:
            if (
                not isinstance(supplied_state, dict)
                or supplied_state != authoritative
            ):
                raise PanelReviewError(
                    "schema-3 supplied packet state does not match the "
                    "authoritative packet-derived state"
                )
        sealed_packet = _professional_v3_freeze(packet)
        sealed_state = _professional_v3_freeze(authoritative)
        handle = object.__new__(_ProfessionalV3CanonicalPacketState)
        values = {
            "packet": sealed_packet,
            "state": sealed_state,
            "packet_digest": _canonical_json_sha256(packet),
            "state_digest": _canonical_json_sha256(
                _professional_v3_state_binding_projection(authoritative)
            ),
            "packet_identity": id(sealed_packet),
            "state_identity": id(sealed_state),
            "baseline_validated": validate_baseline,
            "seal": seal,
        }
        for name, value in values.items():
            object.__setattr__(
                handle,
                f"_ProfessionalV3CanonicalPacketState__{name}",
                value,
            )
        return handle

    return _ProfessionalV3CanonicalPacketState, canonical_packet_state


(
    _ProfessionalV3CanonicalPacketState,
    _professional_v3_canonical_packet_state,
) = _professional_v3_packet_state_boundary()


def _validate_professional_completeness_packet_v3(
    packet: dict[str, Any],
    *,
    validation_root: Path = ROOT,
    artifact_path: Path | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> None:
    _professional_v3_packet_state(
        packet,
        validation_root=validation_root,
        artifact_path=artifact_path,
        validate_baseline=True,
        validation_mode=validation_mode,
    )


def _professional_v3_fresh_target_ids(packet: dict[str, Any]) -> list[str]:
    return [
        row["skill_id"] for row in packet["review_plan"]["fresh_targets"]
    ]


def _professional_v3_capsule_projection_from_packet(
    *,
    packet: dict[str, Any],
    assigned_skill_ids: list[str],
    reviewer_added_requests_by_target: (
        dict[str, list[dict[str, Any]]] | None
    ),
    bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Delegate the sole capsule projection algorithm to the carry helper."""

    try:
        effective_bindings = bindings or (
            professional_carry.professional_review_bindings(
                packet["professional_targets"]
            )
        )
        return professional_carry.project_professional_review_capsule(
            bindings=effective_bindings,
            review_targets=packet["professional_targets"],
            assigned_fresh_target_ids=assigned_skill_ids,
            reviewer_added_requests_by_target=(
                reviewer_added_requests_by_target
            ),
        )
    except professional_carry.ProfessionalCarryForwardError as exc:
        raise PanelReviewError(
            f"schema-3 capsule projection is invalid: {exc}"
        ) from exc


def _professional_v3_discovery_projection_from_packet(
    *,
    packet: dict[str, Any],
    assigned_skill_ids: list[str],
    bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        effective_bindings = bindings or (
            professional_carry.professional_review_bindings(
                packet["professional_targets"]
            )
        )
        return professional_carry.project_professional_discovery_capsule(
            bindings=effective_bindings,
            review_targets=packet["professional_targets"],
            assigned_fresh_target_ids=assigned_skill_ids,
        )
    except professional_carry.ProfessionalCarryForwardError as exc:
        raise PanelReviewError(
            f"schema-3 discovery capsule projection is invalid: {exc}"
        ) from exc


def _professional_v3_normalized_assignment(
    *,
    packet: dict[str, Any],
    assigned_skill_ids: object,
    label: str,
) -> list[str]:
    if not isinstance(assigned_skill_ids, list) or not assigned_skill_ids:
        raise PanelReviewError(f"{label} requires a non-empty fresh Skill assignment")
    normalized = [
        _non_blank(value, label=f"{label}.assigned_skill_ids[{index}]")
        for index, value in enumerate(assigned_skill_ids)
    ]
    if normalized != sorted(set(normalized)):
        raise PanelReviewError(
            f"{label} assigned Skill IDs must be sorted and unique"
        )
    outside = sorted(
        set(normalized) - set(_professional_v3_fresh_target_ids(packet))
    )
    if outside:
        raise PanelReviewError(
            f"{label} may contain only current fresh targets: "
            + ", ".join(outside)
        )
    return normalized


def _professional_v3_validate_artifact_envelope(
    *,
    packet: dict[str, Any],
    value: dict[str, Any],
    fields: set[str],
    kind: str,
    packet_sha256: str,
    label: str,
) -> str:
    if set(value) != fields:
        raise PanelReviewError(f"schema-3 {label} fields are not closed")
    if (
        value.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or value.get("kind") != kind
    ):
        raise PanelReviewError(f"schema-3 {label} kind or schema is invalid")
    if value.get("review_id") != packet.get("review_id"):
        raise PanelReviewError(f"schema-3 {label} review_id is stale")
    _iso_date(value.get("created_on"), label=f"{label}.created_on")
    if value.get("packet_sha256") != packet_sha256:
        raise PanelReviewError(f"schema-3 {label} packet_sha256 is stale")
    if value.get("review_contract_fingerprint") != packet.get(
        "review_contract_fingerprint"
    ):
        raise PanelReviewError(f"schema-3 {label} review contract is stale")
    voter_id = _non_blank(value.get("voter_id"), label=f"{label}.voter_id")
    if VOTER_ID_PATTERN.fullmatch(voter_id) is None:
        raise PanelReviewError(
            f"schema-3 {label}.voter_id must be a lowercase filename-safe slug"
        )
    return voter_id


def prepare_professional_discovery_capsule_v3(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    assigned_skill_ids: list[str],
    created_on: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> dict[str, Any]:
    """Build the immutable discovery input before reviewer candidate selection."""

    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=packet_state,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=validate_packet_plan,
    )
    packet = canonical_state.packet
    state = canonical_state.state
    _lowercase_sha256(packet_sha256, label="discovery_capsule.packet_sha256")
    voter_id = _non_blank(voter_id, label="discovery_capsule.voter_id")
    if VOTER_ID_PATTERN.fullmatch(voter_id) is None:
        raise PanelReviewError(
            "discovery_capsule.voter_id must be a lowercase filename-safe slug"
        )
    _iso_date(created_on, label="discovery_capsule.created_on")
    normalized_ids = sorted(
        _non_blank(value, label="discovery_capsule.assigned_skill_id")
        for value in assigned_skill_ids
    ) if isinstance(assigned_skill_ids, list) else assigned_skill_ids
    normalized_ids = _professional_v3_normalized_assignment(
        packet=packet,
        assigned_skill_ids=normalized_ids,
        label="schema-3 discovery capsule",
    )
    projection = _professional_v3_discovery_projection_from_packet(
        packet=packet,
        assigned_skill_ids=normalized_ids,
        bindings=state["bindings"],
    )
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
        "review_id": packet["review_id"],
        "created_on": created_on,
        "packet_sha256": packet_sha256,
        "review_contract_fingerprint": packet[
            "review_contract_fingerprint"
        ],
        "voter_id": voter_id,
        "discovery_projection": projection,
        "limitations": [
            "The discovery capsule contains assigned target and required-candidate source material plus a complete lightweight boundary catalog; it is not a final review capsule or panel decision.",
            "Canonical byte and optional token counts are input-size proxies, not actual host tokens, latency, reviewer behavior, identity, credentials, or production evidence.",
        ],
    }


def validate_professional_discovery_capsule_v3(
    packet: dict[str, Any],
    capsule: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> dict[str, Any]:
    voter_id = _professional_v3_validate_artifact_envelope(
        packet=packet,
        value=capsule,
        fields=PROFESSIONAL_V3_DISCOVERY_CAPSULE_FIELDS,
        kind=PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
        packet_sha256=packet_sha256,
        label="discovery capsule",
    )
    projection = capsule.get("discovery_projection")
    if not isinstance(projection, dict):
        raise PanelReviewError(
            "schema-3 discovery capsule projection is invalid"
        )
    assigned_ids = projection.get("assigned_fresh_target_ids")
    _professional_v3_normalized_assignment(
        packet=packet,
        assigned_skill_ids=assigned_ids,
        label="schema-3 discovery capsule",
    )
    expected = prepare_professional_discovery_capsule_v3(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        assigned_skill_ids=assigned_ids,
        created_on=capsule.get("created_on"),
        validation_root=validation_root,
        validate_packet_plan=validate_packet_plan,
        packet_state=packet_state,
    )
    if capsule != expected:
        raise PanelReviewError(
            "schema-3 discovery capsule is extra, missing, duplicate, or stale"
        )
    return capsule


def _load_professional_v3_discovery_capsule_reference(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    reference: object,
    validation_root: Path,
    expected_voter_id: str,
    forbidden_paths: set[Path] | None = None,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> tuple[Path, dict[str, str], dict[str, Any]]:
    path, normalized, capsule = _read_validated_json_artifact_reference(
        reference,
        validation_root=validation_root,
        label="schema-3 discovery capsule",
        expected_kind=PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        expected_review_id=packet.get("review_id"),
        forbidden_paths=forbidden_paths,
    )
    validate_professional_discovery_capsule_v3(
        packet,
        capsule,
        packet_sha256=packet_sha256,
        validation_root=validation_root,
        validate_packet_plan=validate_packet_plan,
        packet_state=packet_state,
    )
    if capsule["voter_id"] != expected_voter_id or path.name != f"{expected_voter_id}.json":
        raise PanelReviewError(
            "schema-3 discovery capsule does not belong to its voter"
        )
    return path, normalized, capsule


def _professional_v3_candidate_request_rows(
    *,
    discovery_capsule: dict[str, Any],
    reviewer_added_requests_by_target: dict[str, list[dict[str, str]]] | None,
) -> list[dict[str, Any]]:
    projection = discovery_capsule["discovery_projection"]
    assigned = projection["assigned_fresh_target_ids"]
    supplied = reviewer_added_requests_by_target or {}
    if not isinstance(supplied, dict):
        raise PanelReviewError("schema-3 candidate requests must be an object")
    extra_targets = sorted(set(supplied) - set(assigned))
    if extra_targets:
        raise PanelReviewError(
            "schema-3 candidate request contains unassigned targets: "
            + ", ".join(extra_targets)
        )
    targets = {row["skill_id"]: row for row in projection["targets"]}
    boundaries = {
        row["skill_id"]: row for row in projection["boundary_catalog"]
    }
    rows: list[dict[str, Any]] = []
    for target_id in assigned:
        values = supplied.get(target_id, [])
        if not isinstance(values, list):
            raise PanelReviewError(
                f"schema-3 candidate requests for {target_id} must be an array"
            )
        ranking = {
            row["skill_id"]: row
            for row in targets[target_id]["adjacency"]["full_catalog_ranking"]
        }
        required = {
            row["skill_id"]
            for row in targets[target_id]["adjacency"]["required_candidates"]
        }
        candidate_ids: list[str] = []
        for index, item in enumerate(values):
            if not isinstance(item, dict) or set(item) != {
                "skill_id",
                "discovery_reason",
            }:
                raise PanelReviewError(
                    f"schema-3 candidate request {target_id}[{index}] input fields are invalid"
                )
            candidate_id = _non_blank(
                item.get("skill_id"),
                label=f"candidate request {target_id}[{index}].skill_id",
            )
            reason = _validate_rationale(
                item.get("discovery_reason"),
                label=f"candidate request {target_id}[{index}].discovery_reason",
            )
            if candidate_id not in ranking:
                raise PanelReviewError(
                    f"schema-3 candidate request is outside full ranking: {target_id}->{candidate_id}"
                )
            if candidate_id in required:
                raise PanelReviewError(
                    f"schema-3 candidate request is already packet-required: {target_id}->{candidate_id}"
                )
            candidate_ids.append(candidate_id)
            rows.append(
                {
                    "target_skill_id": target_id,
                    "skill_id": candidate_id,
                    "discovery_reason": reason,
                    "ranking_evidence": copy.deepcopy(ranking[candidate_id]),
                    "material_fingerprint": boundaries[candidate_id][
                        "material_fingerprint"
                    ],
                }
            )
        if candidate_ids != sorted(set(candidate_ids)):
            raise PanelReviewError(
                f"schema-3 candidate requests for {target_id} must be Skill-sorted and unique"
            )
    return rows


def _professional_v3_candidate_request_value(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    discovery_ref: dict[str, str],
    discovery_capsule: dict[str, Any],
    reviewer_added_requests_by_target: dict[str, list[dict[str, str]]] | None,
    created_on: str,
) -> dict[str, Any]:
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND,
        "review_id": packet["review_id"],
        "created_on": created_on,
        "packet_sha256": packet_sha256,
        "review_contract_fingerprint": packet["review_contract_fingerprint"],
        "voter_id": voter_id,
        "discovery_capsule": discovery_ref,
        "assigned_fresh_target_ids": discovery_capsule[
            "discovery_projection"
        ]["assigned_fresh_target_ids"],
        "reviewer_added_requests": _professional_v3_candidate_request_rows(
            discovery_capsule=discovery_capsule,
            reviewer_added_requests_by_target=reviewer_added_requests_by_target,
        ),
        "limitations": [
            "This create-only request is an explicit closure over the discovery assignment; an empty reviewer_added_requests array means no reviewer-added candidates were found.",
            "Ranking evidence and candidate material fingerprints are copied exactly from the bound discovery capsule and do not replace final source review.",
        ],
    }


def prepare_professional_candidate_request_v3(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    discovery_capsule_path: Path,
    voter_id: str,
    reviewer_added_requests_by_target: dict[str, list[dict[str, str]]] | None,
    created_on: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> dict[str, Any]:
    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=packet_state,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=validate_packet_plan,
    )
    packet = canonical_state.packet
    _lowercase_sha256(packet_sha256, label="candidate_request.packet_sha256")
    voter_id = _non_blank(voter_id, label="candidate_request.voter_id")
    if VOTER_ID_PATTERN.fullmatch(voter_id) is None:
        raise PanelReviewError("candidate_request.voter_id is not canonical")
    _iso_date(created_on, label="candidate_request.created_on")
    discovery_ref = _professional_artifact_reference(
        discovery_capsule_path,
        validation_root=validation_root,
        kind=PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
        review_id=packet["review_id"],
    )
    _path, discovery_ref, discovery = (
        _load_professional_v3_discovery_capsule_reference(
            packet=packet,
            packet_sha256=packet_sha256,
            reference=discovery_ref,
            validation_root=validation_root,
            expected_voter_id=voter_id,
            validate_packet_plan=validate_packet_plan,
            packet_state=canonical_state,
        )
    )
    return _professional_v3_candidate_request_value(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        discovery_ref=discovery_ref,
        discovery_capsule=discovery,
        reviewer_added_requests_by_target=reviewer_added_requests_by_target,
        created_on=created_on,
    )


def _candidate_request_inputs(
    request: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    assigned = request.get("assigned_fresh_target_ids")
    rows = request.get("reviewer_added_requests")
    if not isinstance(assigned, list) or not isinstance(rows, list):
        raise PanelReviewError("schema-3 candidate request closure is invalid")
    result: dict[str, list[dict[str, str]]] = {
        skill_id: [] for skill_id in assigned
    }
    keys: list[tuple[str, str]] = []
    for index, row in enumerate(rows):
        if (
            not isinstance(row, dict)
            or set(row) != PROFESSIONAL_V3_CANDIDATE_REQUEST_ROW_FIELDS
        ):
            raise PanelReviewError(
                f"schema-3 candidate request row[{index}] fields are invalid"
            )
        target_id = _non_blank(
            row.get("target_skill_id"),
            label=f"candidate request row[{index}].target_skill_id",
        )
        candidate_id = _non_blank(
            row.get("skill_id"),
            label=f"candidate request row[{index}].skill_id",
        )
        if target_id not in result:
            raise PanelReviewError(
                f"schema-3 candidate request row targets an unassigned Skill: {target_id}"
            )
        result[target_id].append(
            {
                "skill_id": candidate_id,
                "discovery_reason": row.get("discovery_reason"),
            }
        )
        keys.append((target_id, candidate_id))
    if keys != sorted(set(keys)):
        raise PanelReviewError(
            "schema-3 candidate request rows must be target/Skill-sorted and unique"
        )
    return result


def validate_professional_candidate_request_v3(
    packet: dict[str, Any],
    request: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
    forbidden_paths: set[Path] | None = None,
) -> tuple[dict[str, Any], tuple[Path, dict[str, str], dict[str, Any]]]:
    voter_id = _professional_v3_validate_artifact_envelope(
        packet=packet,
        value=request,
        fields=PROFESSIONAL_V3_CANDIDATE_REQUEST_FIELDS,
        kind=PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND,
        packet_sha256=packet_sha256,
        label="candidate request",
    )
    discovery_bound = _load_professional_v3_discovery_capsule_reference(
        packet=packet,
        packet_sha256=packet_sha256,
        reference=request.get("discovery_capsule"),
        validation_root=validation_root,
        expected_voter_id=voter_id,
        forbidden_paths=forbidden_paths,
        validate_packet_plan=validate_packet_plan,
        packet_state=packet_state,
    )
    _path, discovery_ref, discovery = discovery_bound
    assigned = _professional_v3_normalized_assignment(
        packet=packet,
        assigned_skill_ids=request.get("assigned_fresh_target_ids"),
        label="schema-3 candidate request",
    )
    if assigned != discovery["discovery_projection"]["assigned_fresh_target_ids"]:
        raise PanelReviewError("schema-3 candidate request assignment is stale")
    inputs = _candidate_request_inputs(request)
    expected = _professional_v3_candidate_request_value(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        discovery_ref=discovery_ref,
        discovery_capsule=discovery,
        reviewer_added_requests_by_target=inputs,
        created_on=request.get("created_on"),
    )
    if request != expected:
        raise PanelReviewError(
            "schema-3 candidate request is extra, missing, duplicate, or stale"
        )
    return request, discovery_bound


def _load_professional_v3_candidate_request_reference(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    reference: object,
    validation_root: Path,
    expected_voter_id: str,
    forbidden_paths: set[Path] | None = None,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> tuple[
    Path,
    dict[str, str],
    dict[str, Any],
    tuple[Path, dict[str, str], dict[str, Any]],
]:
    path, normalized, request = _read_validated_json_artifact_reference(
        reference,
        validation_root=validation_root,
        label="schema-3 candidate request",
        expected_kind=PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        expected_review_id=packet.get("review_id"),
        forbidden_paths=forbidden_paths,
    )
    _validated, discovery_bound = validate_professional_candidate_request_v3(
        packet,
        request,
        packet_sha256=packet_sha256,
        validation_root=validation_root,
        validate_packet_plan=validate_packet_plan,
        packet_state=packet_state,
        forbidden_paths={*(forbidden_paths or set()), path},
    )
    if request["voter_id"] != expected_voter_id or path.name != f"{expected_voter_id}.json":
        raise PanelReviewError(
            "schema-3 candidate request does not belong to its voter"
        )
    return path, normalized, request, discovery_bound


def _professional_v3_final_capsule_value(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    voter_id: str,
    discovery_ref: dict[str, str],
    request_ref: dict[str, str],
    request: dict[str, Any],
    bindings: dict[str, dict[str, Any]],
    created_on: str,
) -> dict[str, Any]:
    request_inputs = _candidate_request_inputs(request)
    request_rows_by_target: dict[str, list[dict[str, Any]]] = {
        skill_id: [] for skill_id in request["assigned_fresh_target_ids"]
    }
    for row in request["reviewer_added_requests"]:
        request_rows_by_target[row["target_skill_id"]].append(
            {
                field: copy.deepcopy(row[field])
                for field in (
                    "skill_id",
                    "discovery_reason",
                    "ranking_evidence",
                    "material_fingerprint",
                )
            }
        )
    if {
        key: [
            {"skill_id": row["skill_id"], "discovery_reason": row["discovery_reason"]}
            for row in value
        ]
        for key, value in request_rows_by_target.items()
    } != request_inputs:
        raise PanelReviewError("schema-3 candidate request projection is stale")
    projection = _professional_v3_capsule_projection_from_packet(
        packet=packet,
        assigned_skill_ids=request["assigned_fresh_target_ids"],
        reviewer_added_requests_by_target=request_rows_by_target,
        bindings=bindings,
    )
    return {
        "schema_version": PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
        "review_id": packet["review_id"],
        "created_on": created_on,
        "packet_sha256": packet_sha256,
        "review_contract_fingerprint": packet["review_contract_fingerprint"],
        "voter_id": voter_id,
        "discovery_capsule": discovery_ref,
        "candidate_request": request_ref,
        "review_projection": projection,
        "limitations": [
            "This final review capsule is derived only from its immutable discovery capsule, immutable candidate request, and authoritative packet state.",
            "The capsule is an exact fresh-target and candidate-material projection; it is not a complete panel decision.",
            "Canonical material-block byte counts are structural input proxies, not actual host tokens, latency, reviewer behavior, identity, credentials, or production evidence.",
        ],
    }


def prepare_professional_review_capsule_v3(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    discovery_capsule_path: Path,
    candidate_request_path: Path,
    voter_id: str,
    created_on: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> dict[str, Any]:
    """Build a final capsule only from the two immutable predecessor artifacts."""

    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=packet_state,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=validate_packet_plan,
    )
    packet = canonical_state.packet
    state = canonical_state.state
    _lowercase_sha256(packet_sha256, label="capsule.packet_sha256")
    voter_id = _non_blank(voter_id, label="capsule.voter_id")
    if VOTER_ID_PATTERN.fullmatch(voter_id) is None:
        raise PanelReviewError("capsule.voter_id is not canonical")
    _iso_date(created_on, label="capsule.created_on")
    discovery_ref = _professional_artifact_reference(
        discovery_capsule_path,
        validation_root=validation_root,
        kind=PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND,
        review_id=packet["review_id"],
    )
    request_ref = _professional_artifact_reference(
        candidate_request_path,
        validation_root=validation_root,
        kind=PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND,
        review_id=packet["review_id"],
    )
    _request_path, request_ref, request, discovery_bound = (
        _load_professional_v3_candidate_request_reference(
            packet=packet,
            packet_sha256=packet_sha256,
            reference=request_ref,
            validation_root=validation_root,
            expected_voter_id=voter_id,
            validate_packet_plan=validate_packet_plan,
            packet_state=canonical_state,
        )
    )
    _discovery_path, bound_discovery_ref, _discovery = discovery_bound
    if discovery_ref != bound_discovery_ref:
        raise PanelReviewError(
            "schema-3 final capsule discovery predecessor is stale"
        )
    return _professional_v3_final_capsule_value(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        discovery_ref=discovery_ref,
        request_ref=request_ref,
        request=request,
        bindings=state["bindings"],
        created_on=created_on,
    )


def validate_professional_review_capsule_v3(
    packet: dict[str, Any],
    capsule: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
    forbidden_paths: set[Path] | None = None,
) -> dict[str, Any]:
    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=packet_state,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=validate_packet_plan,
        forbidden_paths=forbidden_paths,
    )
    packet = canonical_state.packet
    state = canonical_state.state
    voter_id = _professional_v3_validate_artifact_envelope(
        packet=packet,
        value=capsule,
        fields=PROFESSIONAL_V3_CAPSULE_FIELDS,
        kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
        packet_sha256=packet_sha256,
        label="final review capsule",
    )
    request_bound = _load_professional_v3_candidate_request_reference(
        packet=packet,
        packet_sha256=packet_sha256,
        reference=capsule.get("candidate_request"),
        validation_root=validation_root,
        expected_voter_id=voter_id,
        forbidden_paths=forbidden_paths,
        validate_packet_plan=validate_packet_plan,
        packet_state=canonical_state,
    )
    _request_path, request_ref, request, discovery_bound = request_bound
    _discovery_path, discovery_ref, _discovery = discovery_bound
    if capsule.get("discovery_capsule") != discovery_ref:
        raise PanelReviewError(
            "schema-3 final capsule discovery predecessor is stale"
        )
    expected = _professional_v3_final_capsule_value(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        discovery_ref=discovery_ref,
        request_ref=request_ref,
        request=request,
        bindings=state["bindings"],
        created_on=capsule.get("created_on"),
    )
    if capsule != expected:
        raise PanelReviewError(
            "schema-3 final capsule is extra, missing, duplicate, or stale"
        )
    return capsule


def _professional_v3_capsule_materials(
    capsule: dict[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    materials: dict[str, dict[str, dict[str, Any]]] = {}

    def add_material(skill_id: str, material: dict[str, Any]) -> None:
        own = material["own_material"]
        records = [own["root"], *own["indexed_references"]]
        skill_materials = materials.setdefault(skill_id, {})
        for record in records:
            path = record["path"]
            existing = skill_materials.get(path)
            if existing is not None and existing != record:
                raise PanelReviewError(
                    f"schema-3 capsule binds conflicting material: {skill_id}:{path}"
                )
            skill_materials[path] = record

    projection = capsule["review_projection"]
    for material in projection["material_catalog"]:
        add_material(material["skill_id"], material)
    return materials


def _load_professional_v3_capsule_reference(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    reference: object,
    validation_root: Path,
    expected_voter_id: str,
    forbidden_paths: set[Path] | None = None,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
) -> tuple[Path, dict[str, str], dict[str, Any]]:
    path, normalized, capsule = _read_validated_json_artifact_reference(
        reference,
        validation_root=validation_root,
        label="schema-3 ballot capsule",
        expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        expected_review_id=packet.get("review_id"),
        forbidden_paths=forbidden_paths,
    )
    validate_professional_review_capsule_v3(
        packet,
        capsule,
        packet_sha256=packet_sha256,
        validation_root=validation_root,
        validate_packet_plan=validate_packet_plan,
        packet_state=packet_state,
        forbidden_paths={*(forbidden_paths or set()), path},
    )
    if capsule["voter_id"] != expected_voter_id:
        raise PanelReviewError(
            "schema-3 ballot voter does not own its referenced capsule"
        )
    if path.name != f"{capsule['voter_id']}.json":
        raise PanelReviewError(
            "schema-3 capsule filename must equal its voter_id"
        )
    return path, normalized, capsule


def _professional_v3_capsule_chain_input_blocks(
    *,
    capsule: dict[str, Any],
    cache: dict[str, Any],
    validation_root: Path,
    forbidden_paths: set[Path] | None = None,
) -> list[dict[str, Any]]:
    request_path, _request_ref, request = (
        _professional_v3_cached_json_artifact(
            capsule["candidate_request"],
            cache=cache,
            validation_root=validation_root,
            label="schema-3 cost candidate request",
            expected_kind=(
                PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND
            ),
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=capsule["review_id"],
            forbidden_paths=forbidden_paths,
        )
    )
    _discovery_path, discovery_ref, discovery = (
        _professional_v3_cached_json_artifact(
            request["discovery_capsule"],
            cache=cache,
            validation_root=validation_root,
            label="schema-3 cost discovery capsule",
            expected_kind=(
                PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND
            ),
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=capsule["review_id"],
            forbidden_paths={*(forbidden_paths or set()), request_path},
        )
    )
    if capsule["discovery_capsule"] != discovery_ref:
        raise PanelReviewError(
            "schema-3 cost chain discovery reference is stale"
        )
    return _professional_v3_effective_capsule_input_blocks(
        discovery_capsule=discovery,
        candidate_request=request,
        capsule=capsule,
    )


def _professional_v3_target_scoped_capsule_materials(
    capsule: dict[str, Any],
) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    """Index only material authorized for each assigned target.

    A capsule may cover several targets.  Candidate material projected for one
    target is deliberately not available to a different target unless that
    target's own manifest also names the candidate.
    """

    scoped: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}

    def material_records(material: dict[str, Any]) -> dict[str, dict[str, Any]]:
        own = material["own_material"]
        records = [own["root"], *own["indexed_references"]]
        return {record["path"]: record for record in records}

    projection = capsule["review_projection"]
    catalog_rows = projection["material_catalog"]
    catalog_ids = [row["skill_id"] for row in catalog_rows]
    if catalog_ids != sorted(set(catalog_ids)):
        raise PanelReviewError(
            "schema-3 capsule material catalog is not canonical"
        )
    catalog = {row["skill_id"]: row for row in catalog_rows}
    used_ids: set[str] = set()
    for target in projection["targets"]:
        skill_id = target["skill_id"]
        manifest_ids = [
            row["skill_id"] for row in target["candidate_material_manifest"]
        ]
        allowed_ids = [skill_id, *manifest_ids]
        missing_ids = sorted(set(allowed_ids) - set(catalog))
        if missing_ids:
            raise PanelReviewError(
                "schema-3 capsule material catalog is missing target-scoped "
                f"material for {skill_id}: {', '.join(missing_ids)}"
            )
        allowed = {
            allowed_id: material_records(catalog[allowed_id])
            for allowed_id in allowed_ids
        }
        used_ids.update(allowed_ids)
        scoped[skill_id] = allowed
    unused_ids = sorted(set(catalog) - used_ids)
    if unused_ids:
        raise PanelReviewError(
            "schema-3 capsule material catalog contains unused material: "
            + ", ".join(unused_ids)
        )
    return scoped


def _professional_v3_capsule_adjacency(
    capsule: dict[str, Any],
) -> dict[str, list[str]]:
    return {
        target["skill_id"]: [
            row["skill_id"]
            for row in target["candidate_material_manifest"]
        ]
        for target in capsule["review_projection"]["targets"]
    }


def _professional_v3_capsule_candidate_contract(
    capsule: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    return {
        target["skill_id"]: [
            {
                "skill_id": row["skill_id"],
                "review_origin": row["review_origin"],
                "discovery_reason": row["discovery_reason"],
            }
            for row in target["candidate_material_manifest"]
        ]
        for target in capsule["review_projection"]["targets"]
    }


def _professional_v3_ballot_scope_contract(
    *,
    packet: dict[str, Any],
    capsule: dict[str, Any],
    vote_ids: list[str],
) -> tuple[
    dict[str, dict[str, dict[str, dict[str, Any]]]],
    dict[str, list[str]],
]:
    assigned_ids = capsule["review_projection"]["assigned_fresh_target_ids"]
    if vote_ids != assigned_ids:
        raise PanelReviewError(
            "schema-3 ballot votes must exactly match its fresh capsule assignment"
        )
    if not set(vote_ids) <= set(_professional_v3_fresh_target_ids(packet)):
        raise PanelReviewError("schema-3 ballots cannot vote on carried targets")
    return (
        _professional_v3_target_scoped_capsule_materials(capsule),
        _professional_v3_capsule_adjacency(capsule),
    )


def _professional_v3_ballot_v2_projection(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    projected_packet = _professional_v2_projection_from_v3(
        packet,
        validation_mode=validation_mode,
    )
    return projected_packet, _professional_v3_ballot_value_v2_projection(
        projected_packet, ballot
    )


def _professional_v3_ballot_value_v2_projection(
    projected_packet: dict[str, Any],
    ballot: dict[str, Any],
) -> dict[str, Any]:
    projected_ballot = copy.deepcopy(ballot)
    projected_ballot.pop("review_contract_fingerprint", None)
    projected_ballot.pop("capsule", None)
    projected_ballot["schema_version"] = (
        PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION
    )
    projected_ballot["source_fingerprints"] = projected_packet[
        "source_fingerprints"
    ]
    return projected_ballot


def prepare_professional_completeness_ballot_template_v3(
    *,
    packet: dict[str, Any],
    packet_sha256: str,
    capsule_path: Path,
    voter_id: str,
    agent_id: str,
    role: str,
    expertise: list[str],
    expertise_tags: list[str] | None,
    skill_ids: list[str] | None,
    created_on: str,
    validation_root: Path = ROOT,
) -> dict[str, Any]:
    """Create one schema-3 fresh-only template from a validated capsule."""

    _professional_v3_packet_state(
        packet,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=True,
    )
    capsule_ref = _artifact_reference(
        capsule_path,
        validation_root=validation_root,
        kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
        axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        review_id=packet["review_id"],
    )
    _capsule_path, capsule_ref, capsule = (
        _load_professional_v3_capsule_reference(
            packet=packet,
            packet_sha256=packet_sha256,
            reference=capsule_ref,
            validation_root=validation_root,
            expected_voter_id=voter_id,
        )
    )
    assigned_ids = capsule["review_projection"]["assigned_fresh_target_ids"]
    if skill_ids is not None and sorted(skill_ids) != assigned_ids:
        raise PanelReviewError(
            "schema-3 ballot assignment must exactly match its capsule"
        )
    projected_packet = _professional_v2_projection_from_v3(packet)
    template = prepare_professional_completeness_ballot_template(
        packet=projected_packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        agent_id=agent_id,
        role=role,
        expertise=expertise,
        expertise_tags=expertise_tags,
        skill_ids=assigned_ids,
        created_on=created_on,
    )
    manifest_by_target = {
        target["skill_id"]: target["candidate_material_manifest"]
        for target in capsule["review_projection"]["targets"]
    }
    for vote in template["professional_votes"]:
        vote["examined_adjacent_candidates"] = [
            {
                "skill_id": candidate["skill_id"],
                "review_origin": candidate["review_origin"],
                "discovery_reason": (
                    None
                    if candidate["review_origin"] == "packet-required"
                    else candidate["discovery_reason"]
                ),
                "disposition": None,
                "target_anchor_ids": [],
                "candidate_anchor_ids": [],
                "rationale": "",
            }
            for candidate in manifest_by_target[vote["skill_id"]]
        ]
    template["schema_version"] = (
        PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    )
    template.pop("source_fingerprints")
    template["review_contract_fingerprint"] = packet[
        "review_contract_fingerprint"
    ]
    template["capsule"] = capsule_ref
    template["limitations"] = [
        "Unfilled schema-3 template: every vote is fresh, capsule-scoped, and must be completed independently before validation."
    ]
    return template


def _validate_professional_completeness_ballot_v3(
    packet: dict[str, Any],
    ballot: dict[str, Any],
    *,
    packet_sha256: str,
    validation_root: Path = ROOT,
    artifact_path: Path | None = None,
    validate_packet_plan: bool = True,
    forbidden_paths: set[Path] | None = None,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
    projected_packet: dict[str, Any] | None = None,
    bound_capsule: tuple[Path, dict[str, str], dict[str, Any]] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Validate one fresh schema-3 ballot against only its capsule material."""

    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=packet_state,
        validation_root=validation_root,
        artifact_path=None,
        validate_baseline=validate_packet_plan,
        forbidden_paths=(
            {
                *(forbidden_paths or set()),
                *({artifact_path} if artifact_path is not None else set()),
            }
        ),
        validation_mode=validation_mode,
    )
    packet = canonical_state.packet
    state = canonical_state.state
    if set(ballot) != PROFESSIONAL_V3_BALLOT_FIELDS:
        raise PanelReviewError(
            "professional completeness ballot fields do not match schema 3"
        )
    if (
        ballot.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or ballot.get("kind") != PROFESSIONAL_COMPLETENESS_BALLOT_KIND
    ):
        raise PanelReviewError(
            "professional completeness schema-3 ballot kind is invalid"
        )
    if ballot.get("review_id") != packet.get("review_id"):
        raise PanelReviewError(
            "professional completeness schema-3 ballot review_id is stale"
        )
    if ballot.get("packet_sha256") != packet_sha256:
        raise PanelReviewError(
            "professional completeness schema-3 ballot packet_sha256 is stale"
        )
    if ballot.get("review_contract_fingerprint") != packet.get(
        "review_contract_fingerprint"
    ):
        raise PanelReviewError(
            "professional completeness schema-3 ballot review contract is stale"
        )
    voter = ballot.get("voter")
    if not isinstance(voter, dict):
        raise PanelReviewError("schema-3 ballot voter is invalid")
    voter_id = _non_blank(
        voter.get("voter_id"), label="schema-3 ballot voter_id"
    )
    if (
        artifact_path is not None
        and artifact_path.name != f"{voter_id}.json"
    ):
        raise PanelReviewError(
            "schema-3 ballot filename must equal its voter_id"
        )
    if bound_capsule is None:
        _capsule_path, _capsule_ref, capsule = (
            _load_professional_v3_capsule_reference(
                packet=packet,
                packet_sha256=packet_sha256,
                reference=ballot.get("capsule"),
                validation_root=validation_root,
                expected_voter_id=voter_id,
                forbidden_paths=(
                    {
                        *(forbidden_paths or set()),
                        *(
                            {artifact_path}
                            if artifact_path is not None
                            else set()
                        ),
                    }
                ),
                validate_packet_plan=validate_packet_plan,
                packet_state=canonical_state,
            )
        )
    else:
        _capsule_path, _capsule_ref, capsule = bound_capsule
        if ballot.get("capsule") != _capsule_ref:
            raise PanelReviewError("schema-3 bound capsule reference is stale")
        validate_professional_review_capsule_v3(
            packet,
            capsule,
            packet_sha256=packet_sha256,
            validation_root=validation_root,
            validate_packet_plan=validate_packet_plan,
            packet_state=canonical_state,
        )
        if (
            capsule.get("voter_id") != voter_id
            or _capsule_path.name != f"{voter_id}.json"
        ):
            raise PanelReviewError(
                "schema-3 bound capsule does not belong to ballot voter"
            )
    vote_ids = [
        row.get("skill_id")
        for row in ballot.get("professional_votes", [])
        if isinstance(row, dict)
    ]
    materials_by_target, adjacency_by_target = (
        _professional_v3_ballot_scope_contract(
            packet=packet,
            capsule=capsule,
            vote_ids=vote_ids,
        )
    )
    packet_projection_was_supplied = projected_packet is not None
    if projected_packet is None:
        projected_packet, projected_ballot = (
            _professional_v3_ballot_v2_projection(
                packet,
                ballot,
                validation_mode=validation_mode,
            )
        )
    else:
        projected_ballot = (
            _professional_v3_ballot_value_v2_projection(
                projected_packet, ballot
            )
        )
    _validate_professional_completeness_ballot_v2(
        projected_packet,
        projected_ballot,
        packet_sha256=packet_sha256,
        materials_by_target=materials_by_target,
        expected_adjacency_by_target=adjacency_by_target,
        validate_packet_contract=not packet_projection_was_supplied,
        validation_mode=validation_mode,
    )
    candidate_contract = _professional_v3_capsule_candidate_contract(capsule)
    for vote_index, vote in enumerate(ballot["professional_votes"]):
        _validate_professional_v3_semantic_grounding(
            vote,
            materials_by_skill=materials_by_target[vote["skill_id"]],
            label=f"professional_votes[{vote_index}]",
        )
        actual = [
            {
                "skill_id": row["skill_id"],
                "review_origin": row["review_origin"],
                "discovery_reason": row["discovery_reason"],
            }
            for row in vote["examined_adjacent_candidates"]
        ]
        if actual != candidate_contract[vote["skill_id"]]:
            raise PanelReviewError(
                "schema-3 ballot candidate origin, discovery reason, or set "
                f"does not match its immutable request: {vote['skill_id']}"
            )
    return ballot


def _professional_v3_target_evidence_metrics(
    *,
    target: dict[str, Any],
    assignments: list[dict[str, Any]],
) -> dict[str, int]:
    votes = [assignment["vote"] for assignment in assignments]
    return {
        "target_vote_count": len(votes),
        "required_adjacency_candidate_count": len(
            target["routing_adjacency"]["required_candidates"]
        ),
        "criterion_result_count": sum(len(vote["criteria"]) for vote in votes),
        "criterion_anchor_binding_count": sum(
            len(assertion["evidence_anchor_ids"])
            for vote in votes
            for result in vote["criteria"].values()
            for assertion in result["evidence_assertions"]
        ),
        "criterion_assertion_count": sum(
            len(result["evidence_assertions"])
            for vote in votes
            for result in vote["criteria"].values()
        ),
        "evidence_anchor_count": sum(
            len(vote["evidence_anchors"]) for vote in votes
        ),
        "examined_failure_mode_count": sum(
            len(vote["examined_failure_modes"]) for vote in votes
        ),
        "examined_omission_candidate_count": sum(
            len(vote["examined_omission_candidates"]) for vote in votes
        ),
        "examined_adjacency_count": sum(
            len(vote["examined_adjacent_candidates"]) for vote in votes
        ),
        "examined_required_adjacency_count": sum(
            candidate["review_origin"] == "packet-required"
            for vote in votes
            for candidate in vote["examined_adjacent_candidates"]
        ),
        "reviewer_added_adjacency_count": sum(
            candidate["review_origin"] == "reviewer-added"
            for vote in votes
            for candidate in vote["examined_adjacent_candidates"]
        ),
        "proof_limit_count": sum(
            len(vote["proof_limits"]) for vote in votes
        ),
        "qualification_claim_count": sum(
            len(assignment["voter"]["qualification_claims"])
            for assignment in assignments
        ),
    }


def _professional_v3_fresh_target_decision(
    *,
    target: dict[str, Any],
    assignments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive one fresh target solely from its three validated evidence rows."""

    skill_id = target["skill_id"]
    if len(assignments) != PANEL_SIZE:
        raise PanelReviewError(
            f"professional completeness target {skill_id} requires exactly "
            f"{PANEL_SIZE} fresh ballots; actual={len(assignments)}"
        )
    assigned = sorted(
        assignments, key=lambda item: item["voter"]["voter_id"]
    )
    voter_ids = [item["voter"]["voter_id"] for item in assigned]
    agent_ids = [item["voter"]["agent_id"] for item in assigned]
    if len(voter_ids) != len(set(voter_ids)) or len(agent_ids) != len(
        set(agent_ids)
    ):
        raise PanelReviewError(
            f"professional completeness target {skill_id} requires unique fresh reviewers"
        )
    domain = [
        item
        for item in assigned
        if _professional_voter_kind(item["voter"]) == "domain"
    ]
    architecture = [
        item
        for item in assigned
        if _professional_voter_kind(item["voter"]) == "architecture"
    ]
    if len(domain) != 2 or len(architecture) != 1:
        raise PanelReviewError(
            f"professional completeness target {skill_id} requires exactly "
            "two qualified domain ballots and one architecture ballot"
        )
    rows = [item["vote"] for item in assigned]
    criterion_vote_counts = {
        criterion: {
            value: sum(
                row["criteria"][criterion]["status"] == value
                for row in rows
            )
            for value in sorted(PROFESSIONAL_CRITERION_VALUES)
        }
        for criterion in sorted(PROFESSIONAL_COMPLETENESS_CRITERIA)
    }
    majority = _majority_decision(rows, voter_ids=voter_ids)
    domain_critical_defects = sorted(
        (
            {
                "criterion": criterion,
                "voter_id": item["voter"]["voter_id"],
            }
            for item in domain
            for criterion in PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
            if item["vote"]["criteria"][criterion]["status"]
            == "defect-found"
        ),
        key=lambda item: (item["criterion"], item["voter_id"]),
    )
    ordinary_criterion_defects = [
        criterion
        for criterion in sorted(PROFESSIONAL_ORDINARY_CRITERIA)
        if criterion_vote_counts[criterion]["defect-found"] >= 2
    ]
    ordinary_disposition = (
        "requires-professional-correction"
        if ordinary_criterion_defects
        else "accepted-current-professional-completeness"
    )
    final_disposition = (
        PROFESSIONAL_UNRESOLVED_DISPOSITION
        if domain_critical_defects
        else ordinary_disposition
    )
    required_candidate_ids = [
        row["skill_id"]
        for row in target["routing_adjacency"]["required_candidates"]
    ]
    reviewer_added = sorted(
        {
            candidate["skill_id"]
            for row in rows
            for candidate in row["examined_adjacent_candidates"]
            if candidate["review_origin"] == "reviewer-added"
        }
    )
    dependencies = {
        "skill_id": skill_id,
        "final_disposition": final_disposition,
        "evidence_complete": True,
        "prior_target_vote_count": PANEL_SIZE,
        "required_candidate_ids": required_candidate_ids,
        "reviewer_added_candidate_ids_union": reviewer_added,
        "dependency_candidate_ids": sorted(
            set(required_candidate_ids) | set(reviewer_added)
        ),
    }
    evidence = [
        {
            "voter_id": item["voter"]["voter_id"],
            "ballot": copy.deepcopy(item["ballot_ref"]),
            "capsule": copy.deepcopy(item["capsule_ref"]),
        }
        for item in assigned
    ]
    row: dict[str, Any] = {
        "skill_id": skill_id,
        "review_unit_binding": target["review_binding"][
            "review_unit_binding"
        ],
        "qualification_coverage": {
            "required_expertise_tags": target["required_expertise_tags"],
            "domain_voters": [
                item["voter"]["voter_id"] for item in domain
            ],
            "architecture_voter": architecture[0]["voter"]["voter_id"],
        },
        "criterion_vote_counts": criterion_vote_counts,
        "domain_critical_defects": domain_critical_defects,
        "ordinary_criterion_defects": ordinary_criterion_defects,
        "ordinary_criterion_disposition": ordinary_disposition,
        "reviewer_added_adjacency_reviews": [
            {
                "voter_id": item["voter"]["voter_id"],
                "candidates": [
                    candidate
                    for candidate in item["vote"][
                        "examined_adjacent_candidates"
                    ]
                    if candidate["review_origin"] == "reviewer-added"
                ],
            }
            for item in assigned
            if any(
                candidate["review_origin"] == "reviewer-added"
                for candidate in item["vote"]["examined_adjacent_candidates"]
            )
        ],
        **majority,
        "final_disposition": final_disposition,
        "review_dependencies": dependencies,
        "evidence_metrics": _professional_v3_target_evidence_metrics(
            target=target,
            assignments=assigned,
        ),
        "provenance": {
            "mode": "fresh",
            "origin_depth": 0,
            "evidence": evidence,
        },
    }
    row["target_decision_fingerprint"] = _canonical_json_sha256(row)
    return row


def _professional_v3_carried_target_decision(
    *,
    target: dict[str, Any],
    origin_row: dict[str, Any],
    origin_decision_ref: dict[str, str],
    current_bindings: dict[str, dict[str, Any]],
    origin_candidate_material_bindings: dict[str, str],
) -> dict[str, Any]:
    if origin_row.get("skill_id") != target["skill_id"]:
        raise PanelReviewError("schema-3 carry origin Skill is stale")
    if origin_row.get("review_unit_binding") != target[
        "review_binding"
    ]["review_unit_binding"]:
        raise PanelReviewError(
            f"schema-3 carry origin review binding is stale: {target['skill_id']}"
        )
    if origin_row["final_disposition"] != (
        "accepted-current-professional-completeness"
    ):
        raise PanelReviewError(
            f"schema-3 carry origin is not accepted: {target['skill_id']}"
        )
    dependency = origin_row.get("review_dependencies")
    reviewer_added_ids = (
        dependency.get("reviewer_added_candidate_ids_union")
        if isinstance(dependency, dict)
        else None
    )
    if not isinstance(reviewer_added_ids, list):
        raise PanelReviewError(
            f"schema-3 carry origin dependencies are invalid: {target['skill_id']}"
        )
    for candidate_id in reviewer_added_ids:
        current_candidate = current_bindings.get(candidate_id)
        if (
            current_candidate is None
            or origin_candidate_material_bindings.get(candidate_id)
            != current_candidate.get("package_material_binding")
        ):
            raise PanelReviewError(
                "schema-3 reviewer-added candidate material changed: "
                f"{target['skill_id']} -> {candidate_id}"
            )
    row = {
        key: copy.deepcopy(value)
        for key, value in origin_row.items()
        if key not in {
            "review_unit_binding",
            "provenance",
            "target_decision_fingerprint",
        }
    }
    row["review_unit_binding"] = target["review_binding"][
        "review_unit_binding"
    ]
    row["provenance"] = {
        "mode": "carried-forward",
        "origin_depth": 1,
        "origin_decision": copy.deepcopy(origin_decision_ref),
        "origin_target_decision_fingerprint": origin_row[
            "target_decision_fingerprint"
        ],
        "carry_basis": "review-visible-binding-unchanged",
    }
    row["target_decision_fingerprint"] = _canonical_json_sha256(row)
    return row


def _professional_attestation_origin_row(
    finding: dict[str, Any]
) -> dict[str, Any]:
    """Project one authenticated compact finding into carry decision shape."""

    origin = finding["provenance"]["origin"]
    votes = finding["votes"]
    majority = _majority_decision(
        votes,
        voter_ids=[vote["reviewer"] for vote in votes],
    )
    majority["vote_counts"] = {
        decision: majority["vote_counts"].get(decision, 0)
        for decision in sorted(PROFESSIONAL_COMPLETENESS_DECISIONS)
    }
    result = finding["result"]
    majority_summary_fields = (
        "winning_disposition",
        "winning_votes",
        "vote_counts",
        "supporting_voters",
        "dissenting_voters",
    )
    if any(
        result.get(field) != majority[field]
        for field in majority_summary_fields
    ):
        raise PanelReviewError(
            "compact professional majority is stale: "
            f"{finding['skill_id']}"
        )
    projected_result = copy.deepcopy(result)
    projected_result.update(majority)
    reviewer_added_reviews = [
        {
            "voter_id": vote["reviewer"],
            "candidates": [
                {
                    "skill_id": candidate_id,
                    "review_origin": "reviewer-added",
                }
                for candidate_id in vote["examined_adjacent_candidates"][
                    "reviewer_added_candidate_ids"
                ]
            ],
        }
        for vote in finding["votes"]
        if vote["examined_adjacent_candidates"][
            "reviewer_added_candidate_ids"
        ]
    ]
    return {
        "skill_id": finding["skill_id"],
        "review_unit_binding": finding["review_unit_binding"],
        "reviewer_added_adjacency_reviews": reviewer_added_reviews,
        **projected_result,
        "provenance": {"mode": "fresh", "origin_depth": 0, "evidence": []},
        "target_decision_fingerprint": origin["origin_verdict_digest"],
    }


def _professional_v3_decision_envelope(record: dict[str, Any]) -> str:
    """Validate the stable schema-3 envelope without applying current rules."""

    historical_source_contracts = {
        PROFESSIONAL_HISTORICAL_V2_REVIEW_CONTRACT_FINGERPRINT,
        PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT,
        PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT,
    }
    expected_fields = (
        PROFESSIONAL_HISTORICAL_V3_DECISION_FIELDS
        if record.get("review_contract_fingerprint")
        in historical_source_contracts
        else PROFESSIONAL_V3_DECISION_FIELDS
    )
    if set(record) != expected_fields:
        raise PanelReviewError(
            "professional completeness decision fields do not match schema 3"
        )
    if (
        record.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        or record.get("kind") != PROFESSIONAL_COMPLETENESS_DECISION_KIND
    ):
        if record.get("schema_version") in {
            SCHEMA_VERSION,
            PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
        }:
            raise PanelReviewError(
                "legacy professional decisions cannot be schema-3 carry baselines"
            )
        raise PanelReviewError(
            "professional completeness decision schema or kind is invalid"
        )
    review_id = _non_blank(
        record.get("review_id"), label="decision.review_id"
    )
    if VOTER_ID_PATTERN.fullmatch(review_id) is None:
        raise PanelReviewError("schema-3 decision review_id is not canonical")
    _iso_date(record.get("decided_on"), label="decision.decided_on")
    contract_fingerprint = _lowercase_sha256(
        record.get("review_contract_fingerprint"),
        label="schema-3 decision review contract",
    )
    packet_ref = _artifact_reference_shape(
        record.get("packet"),
        label="schema-3 decision packet",
        require_review_id=True,
        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
    )
    if packet_ref["review_id"] != review_id:
        raise PanelReviewError(
            "schema-3 decision packet review_id is stale"
        )
    return contract_fingerprint


def _professional_v3_decision_shape(
    record: dict[str, Any],
    *,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> None:
    validation_mode = _closed_validation_mode(validation_mode)
    contract_fingerprint = _professional_v3_decision_envelope(record)
    if record.get("decision_method") != (
        PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
    ):
        raise PanelReviewError("schema-3 decision method is invalid")
    if (
        validation_mode == VALIDATION_MODE_CURRENT
        and contract_fingerprint
        != _professional_evidence_review_contract_fingerprint()
    ):
        raise PanelReviewError("schema-3 decision review contract is stale")
    if (
        validation_mode == VALIDATION_MODE_CURRENT
        and record.get("panel_contract") != _professional_v3_panel_contract()
    ):
        raise PanelReviewError("schema-3 decision panel contract is invalid")


def _professional_v3_load_packet_for_decision(
    record: dict[str, Any],
    *,
    validation_root: Path,
    forbidden_paths: set[Path],
    validate_baseline: bool,
    invocation_cache: dict[str, Any] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> tuple[Path, dict[str, str], dict[str, Any], dict[str, Any]]:
    cache = invocation_cache or _professional_v3_invocation_cache()
    packet_path, packet_ref, packet = (
        _professional_v3_cached_json_artifact(
            record.get("packet"),
            cache=cache,
            validation_root=validation_root,
            label="schema-3 decision packet",
        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        expected_review_id=record["review_id"],
        forbidden_paths=forbidden_paths,
        )
    )
    state_key = (
        validation_root.resolve().as_posix(),
        packet_ref["path"],
        packet_ref["sha256"],
        validate_baseline,
        validation_mode,
        tuple(sorted(path.resolve().as_posix() for path in forbidden_paths)),
    )
    state = cache["packet_states"].get(state_key)
    if state is None:
        state = _professional_v3_packet_state(
            packet,
            validation_root=validation_root,
            artifact_path=packet_path,
            validate_baseline=validate_baseline,
            forbidden_paths=forbidden_paths,
            invocation_cache=cache,
            validation_mode=validation_mode,
        )
        cache["packet_states"][state_key] = state
    if packet["review_id"] != record["review_id"]:
        raise PanelReviewError("schema-3 decision packet review_id is stale")
    if record.get("review_contract_fingerprint") != packet[
        "review_contract_fingerprint"
    ]:
        raise PanelReviewError("schema-3 decision packet contract is stale")
    return packet_path, packet_ref, packet, state


def _professional_v3_decision_row(
    record: dict[str, Any], skill_id: str
) -> dict[str, Any]:
    rows = record.get("professional_decisions")
    if not isinstance(rows, list):
        raise PanelReviewError("schema-3 professional_decisions must be an array")
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("skill_id") == skill_id
    ]
    if len(matches) != 1:
        raise PanelReviewError(
            f"schema-3 decision must contain exactly one target row: {skill_id}"
        )
    return matches[0]


def _professional_v3_validate_decision_projection(
    *,
    record: dict[str, Any],
    packet: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Cheap whole-record validation before any target-scoped origin load."""

    targets = {
        target["skill_id"]: target
        for target in packet["professional_targets"]
    }
    rows = record.get("professional_decisions")
    if not isinstance(rows, list) or [
        row.get("skill_id") if isinstance(row, dict) else None for row in rows
    ] != sorted(targets):
        raise PanelReviewError(
            "schema-3 decision must contain "
            f"{PROFESSIONAL_PACKAGE_COUNT} Skill-sorted target rows"
        )
    plan_fresh = {
        row["skill_id"] for row in state["plan"]["fresh_targets"]
    }
    plan_carried = {
        row["skill_id"] for row in state["plan"]["carried_targets"]
    }
    evidence_by_voter: dict[str, dict[str, Any]] = {}
    assignment_from_evidence: dict[str, list[str]] = {}
    for row in rows:
        skill_id = row["skill_id"]
        if set(row) != PROFESSIONAL_V3_TARGET_DECISION_FIELDS:
            raise PanelReviewError(
                f"schema-3 decision target fields are invalid: {skill_id}"
            )
        fingerprint = _lowercase_sha256(
            row.get("target_decision_fingerprint"),
            label=f"schema-3 decision target {skill_id} fingerprint",
        )
        without_fingerprint = dict(row)
        without_fingerprint.pop("target_decision_fingerprint")
        if fingerprint != _canonical_json_sha256(without_fingerprint):
            raise PanelReviewError(
                f"schema-3 decision target fingerprint is stale: {skill_id}"
            )
        target = targets[skill_id]
        if row.get("review_unit_binding") != target[
            "review_binding"
        ]["review_unit_binding"]:
            raise PanelReviewError(
                f"schema-3 decision target binding is stale: {skill_id}"
            )
        if row.get("final_disposition") not in PROFESSIONAL_FINAL_DISPOSITIONS:
            raise PanelReviewError(
                f"schema-3 decision target disposition is invalid: {skill_id}"
            )
        metrics = row.get("evidence_metrics")
        if (
            not isinstance(metrics, dict)
            or set(metrics) != PROFESSIONAL_V3_EVIDENCE_METRIC_FIELDS
            or any(type(value) is not int or value < 0 for value in metrics.values())
            or metrics["target_vote_count"] != PANEL_SIZE
            or metrics["criterion_result_count"]
            != PANEL_SIZE * len(PROFESSIONAL_COMPLETENESS_CRITERIA)
        ):
            raise PanelReviewError(
                f"schema-3 decision target evidence metrics are invalid: {skill_id}"
            )
        dependency = row.get("review_dependencies")
        dependency_fields = {
            "skill_id",
            "final_disposition",
            "evidence_complete",
            "prior_target_vote_count",
            "required_candidate_ids",
            "reviewer_added_candidate_ids_union",
            "dependency_candidate_ids",
        }
        if (
            not isinstance(dependency, dict)
            or set(dependency) != dependency_fields
            or dependency.get("skill_id") != skill_id
            or dependency.get("final_disposition") != row["final_disposition"]
            or dependency.get("evidence_complete") is not True
            or dependency.get("prior_target_vote_count") != PANEL_SIZE
        ):
            raise PanelReviewError(
                f"schema-3 decision target dependency is invalid: {skill_id}"
            )
        required_ids = [
            candidate["skill_id"]
            for candidate in target["routing_adjacency"]["required_candidates"]
        ]
        added_ids = dependency.get("reviewer_added_candidate_ids_union")
        if (
            dependency.get("required_candidate_ids") != required_ids
            or not isinstance(added_ids, list)
            or added_ids != sorted(set(added_ids))
            or dependency.get("dependency_candidate_ids")
            != sorted(set(required_ids) | set(added_ids))
        ):
            raise PanelReviewError(
                f"schema-3 decision target dependency union is stale: {skill_id}"
            )
        provenance = row.get("provenance")
        if not isinstance(provenance, dict):
            raise PanelReviewError(
                f"schema-3 decision target provenance is invalid: {skill_id}"
            )
        if provenance.get("mode") == "fresh":
            if set(provenance) != {"mode", "origin_depth", "evidence"} or (
                provenance.get("origin_depth") != 0 or skill_id not in plan_fresh
            ):
                raise PanelReviewError(
                    f"schema-3 fresh target provenance is stale: {skill_id}"
                )
            evidence = provenance.get("evidence")
            if not isinstance(evidence, list) or len(evidence) != PANEL_SIZE:
                raise PanelReviewError(
                    f"schema-3 fresh target evidence is incomplete: {skill_id}"
                )
            evidence_voters: list[str] = []
            for item in evidence:
                if (
                    not isinstance(item, dict)
                    or set(item) != PROFESSIONAL_V3_PROVENANCE_EVIDENCE_FIELDS
                ):
                    raise PanelReviewError(
                        f"schema-3 fresh evidence fields are invalid: {skill_id}"
                    )
                voter_id = _non_blank(
                    item.get("voter_id"),
                    label=f"schema-3 fresh evidence voter {skill_id}",
                )
                ballot_ref = _artifact_reference_shape(
                    item.get("ballot"),
                    label=f"schema-3 fresh evidence ballot {skill_id}",
                    require_review_id=True,
                    expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                    expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                )
                capsule_ref = _artifact_reference_shape(
                    item.get("capsule"),
                    label=f"schema-3 fresh evidence capsule {skill_id}",
                    require_review_id=True,
                    expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                    expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                )
                if (
                    ballot_ref["review_id"] != record["review_id"]
                    or capsule_ref["review_id"] != record["review_id"]
                    or Path(ballot_ref["path"]).stem != voter_id
                    or Path(capsule_ref["path"]).stem != voter_id
                ):
                    raise PanelReviewError(
                        f"schema-3 fresh evidence round or filename is stale: {skill_id}"
                    )
                projected = {
                    "ballot": ballot_ref,
                    "capsule": capsule_ref,
                }
                existing = evidence_by_voter.get(voter_id)
                if existing is not None and existing != projected:
                    raise PanelReviewError(
                        f"schema-3 voter evidence refs conflict: {voter_id}"
                    )
                evidence_by_voter[voter_id] = projected
                assignment_from_evidence.setdefault(voter_id, []).append(skill_id)
                evidence_voters.append(voter_id)
            if evidence_voters != sorted(set(evidence_voters)):
                raise PanelReviewError(
                    f"schema-3 fresh evidence voters are not canonical: {skill_id}"
                )
        elif provenance.get("mode") == "carried-forward":
            if set(provenance) != {
                "mode",
                "origin_depth",
                "origin_decision",
                "origin_target_decision_fingerprint",
                "carry_basis",
            } or provenance.get("origin_depth") != 1 or skill_id not in plan_carried:
                raise PanelReviewError(
                    f"schema-3 carried target provenance is stale: {skill_id}"
                )
            origin_reference = provenance.get("origin_decision")
            if (
                isinstance(origin_reference, dict)
                and origin_reference.get("kind")
                == panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND
            ):
                _professional_attestation_reference_shape(
                    origin_reference,
                    label=f"schema-3 carried target origin {skill_id}",
                )
            else:
                _artifact_reference_shape(
                    origin_reference,
                    label=f"schema-3 carried target origin {skill_id}",
                    require_review_id=True,
                    expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                    expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                )
            _lowercase_sha256(
                provenance.get("origin_target_decision_fingerprint"),
                label=f"schema-3 carried target origin fingerprint {skill_id}",
            )
            if provenance.get("carry_basis") != (
                "review-visible-binding-unchanged"
            ):
                raise PanelReviewError(
                    f"schema-3 carried target basis is invalid: {skill_id}"
                )
        else:
            raise PanelReviewError(
                f"schema-3 decision target provenance mode is invalid: {skill_id}"
            )
    if {
        row["skill_id"]
        for row in rows
        if row["provenance"]["mode"] == "fresh"
    } != plan_fresh or {
        row["skill_id"]
        for row in rows
        if row["provenance"]["mode"] == "carried-forward"
    } != plan_carried:
        raise PanelReviewError("schema-3 decision provenance partition is stale")
    voters = record.get("voters")
    if not isinstance(voters, list):
        raise PanelReviewError("schema-3 decision voters must be an array")
    voter_ids: list[str] = []
    agent_ids: list[str] = []
    for voter in voters:
        if (
            not isinstance(voter, dict)
            or set(voter) != PROFESSIONAL_V3_DECISION_VOTER_FIELDS
        ):
            raise PanelReviewError("schema-3 decision voter fields are invalid")
        voter_id = _non_blank(
            voter.get("voter_id"), label="schema-3 decision voter_id"
        )
        agent_ids.append(
            _non_blank(voter.get("agent_id"), label="schema-3 decision agent_id")
        )
        ballot_ref = _artifact_reference_shape(
            voter.get("ballot"),
            label=f"schema-3 decision voter ballot {voter_id}",
            require_review_id=True,
            expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        )
        capsule_ref = _artifact_reference_shape(
            voter.get("capsule"),
            label=f"schema-3 decision voter capsule {voter_id}",
            require_review_id=True,
            expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        )
        if evidence_by_voter.get(voter_id) != {
            "ballot": ballot_ref,
            "capsule": capsule_ref,
        }:
            raise PanelReviewError(
                f"schema-3 decision voter is not bound by fresh evidence: {voter_id}"
            )
        assigned = voter.get("assigned_skill_ids")
        if assigned != sorted(assignment_from_evidence.get(voter_id, [])):
            raise PanelReviewError(
                f"schema-3 decision voter assignment is stale: {voter_id}"
            )
        voter_ids.append(voter_id)
    if voter_ids != sorted(set(voter_ids)) or len(agent_ids) != len(
        set(agent_ids)
    ) or set(voter_ids) != set(evidence_by_voter):
        raise PanelReviewError("schema-3 decision reviewer pool is stale")
    expected_summary = _professional_v3_summary_from_rows(
        decisions=rows,
        packet=packet,
        decision_voters=voters,
    )
    if record.get("summary") != expected_summary:
        raise PanelReviewError("schema-3 decision summary is stale")


def _load_professional_v3_fresh_origin_target(
    *,
    origin_reference: object,
    skill_id: str,
    expected_target_decision_fingerprint: str,
    validation_root: Path,
    forbidden_paths: set[Path],
    invocation_cache: dict[str, Any] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Recompute one direct fresh origin from its actual ballots and capsules."""

    cache = invocation_cache or _professional_v3_invocation_cache()
    origin_path, origin_ref, record = (
        _professional_v3_cached_json_artifact(
        origin_reference,
        cache=cache,
        validation_root=validation_root,
        label=f"schema-3 carry origin decision for {skill_id}",
        expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        forbidden_paths=forbidden_paths,
        )
    )
    round_key = (
        validation_root.resolve().as_posix(),
        origin_ref["path"],
        origin_ref["sha256"],
        origin_ref["review_id"],
        validation_mode,
        tuple(
            sorted(path.resolve().as_posix() for path in forbidden_paths)
        ),
    )
    context = cache["origin_rounds"].get(round_key)
    if context is None:
        _professional_v3_decision_shape(
            record,
            validation_mode=validation_mode,
        )
        if origin_ref["review_id"] != record["review_id"]:
            raise PanelReviewError("schema-3 carry origin review_id is stale")
        packet_path, packet_ref, packet = (
            _professional_v3_cached_json_artifact(
                record.get("packet"),
                cache=cache,
                validation_root=validation_root,
                label="schema-3 carry origin packet",
                expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                expected_review_id=record["review_id"],
                forbidden_paths={*forbidden_paths, origin_path},
            )
        )
        canonical_state = _professional_v3_canonical_packet_state(
            packet,
            supplied_state=None,
            validation_root=validation_root,
            artifact_path=packet_path,
            validate_baseline=False,
            forbidden_paths={*forbidden_paths, origin_path},
            invocation_cache=cache,
            validation_mode=validation_mode,
        )
        packet = canonical_state.packet
        state = canonical_state.state
        _professional_v3_validate_decision_projection(
            record=record,
            packet=packet,
            state=state,
        )
        context = {
            "origin_path": origin_path,
            "origin_ref": origin_ref,
            "record": record,
            "packet_path": packet_path,
            "packet_ref": packet_ref,
            "packet": packet,
            "state": state,
            "canonical_state": canonical_state,
            "projected_packet": _professional_v2_projection_from_v3(
                packet,
                validation_mode=validation_mode,
            ),
            "targets": {
                row["skill_id"]: row
                for row in packet["professional_targets"]
            },
        }
        cache["origin_rounds"][round_key] = context
    origin_path = context["origin_path"]
    origin_ref = context["origin_ref"]
    record = context["record"]
    packet_path = context["packet_path"]
    packet_ref = context["packet_ref"]
    packet = context["packet"]
    state = context["state"]
    target_cache_key = (*round_key, skill_id, expected_target_decision_fingerprint)
    cached_target = cache["origin_targets"].get(target_cache_key)
    if cached_target is not None:
        return cached_target
    fresh_ids = {
        row["skill_id"] for row in state["plan"]["fresh_targets"]
    }
    if skill_id not in fresh_ids:
        raise PanelReviewError(
            f"schema-3 carry origin is not a direct fresh decision: {skill_id}"
        )
    target = context["targets"].get(skill_id)
    if target is None:
        raise PanelReviewError(
            f"schema-3 carry origin packet lacks target: {skill_id}"
        )
    stored = _professional_v3_decision_row(record, skill_id)
    if stored.get("target_decision_fingerprint") != (
        expected_target_decision_fingerprint
    ):
        raise PanelReviewError(
            f"schema-3 carry origin target fingerprint is stale: {skill_id}"
        )
    provenance = stored.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {
        "mode",
        "origin_depth",
        "evidence",
    }:
        raise PanelReviewError(
            f"schema-3 carry origin provenance is not fresh: {skill_id}"
        )
    if provenance.get("mode") != "fresh" or provenance.get(
        "origin_depth"
    ) != 0:
        raise PanelReviewError(
            f"schema-3 carry origin must have depth-zero fresh provenance: {skill_id}"
        )
    evidence = provenance.get("evidence")
    if not isinstance(evidence, list) or len(evidence) != PANEL_SIZE:
        raise PanelReviewError(
            f"schema-3 fresh origin must bind exactly three evidence rows: {skill_id}"
        )
    assignments: list[dict[str, Any]] = []
    for index, evidence_row in enumerate(evidence):
        label = f"schema-3 origin {skill_id} evidence[{index}]"
        if (
            not isinstance(evidence_row, dict)
            or set(evidence_row) != PROFESSIONAL_V3_PROVENANCE_EVIDENCE_FIELDS
        ):
            raise PanelReviewError(f"{label} fields are invalid")
        voter_id = _non_blank(
            evidence_row.get("voter_id"), label=f"{label}.voter_id"
        )
        ballot_path, ballot_ref, ballot = (
            _professional_v3_cached_json_artifact(
            evidence_row.get("ballot"),
            cache=cache,
            validation_root=validation_root,
            label=f"{label}.ballot",
            expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=record["review_id"],
            forbidden_paths={*forbidden_paths, origin_path, packet_path},
            )
        )
        _capsule_path, capsule_ref, _capsule = (
            _professional_v3_cached_json_artifact(
            evidence_row.get("capsule"),
            cache=cache,
            validation_root=validation_root,
            label=f"{label}.capsule",
            expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=record["review_id"],
            forbidden_paths={*forbidden_paths, origin_path, packet_path},
            )
        )
        ballot_key = (
            validation_root.resolve().as_posix(),
            ballot_ref["path"],
            ballot_ref["sha256"],
            validation_mode,
        )
        if ballot_key not in cache["validated_ballots"]:
            _validate_professional_completeness_ballot_v3(
                packet,
                ballot,
                packet_sha256=packet_ref["sha256"],
                validation_root=validation_root,
                artifact_path=ballot_path,
                validate_packet_plan=False,
                forbidden_paths={*forbidden_paths, origin_path},
                packet_state=context["canonical_state"],
                projected_packet=context["projected_packet"],
                bound_capsule=(_capsule_path, capsule_ref, _capsule),
                validation_mode=validation_mode,
            )
            cache["validated_ballots"].add(ballot_key)
        vote_index = cache["ballot_votes"].get(ballot_key)
        if vote_index is None:
            vote_index = {
                vote["skill_id"]: vote
                for vote in ballot["professional_votes"]
            }
            if len(vote_index) != len(ballot["professional_votes"]):
                raise PanelReviewError(
                    f"{label} contains duplicate target votes"
                )
            cache["ballot_votes"][ballot_key] = vote_index
        if ballot["voter"]["voter_id"] != voter_id:
            raise PanelReviewError(f"{label} voter is stale")
        if ballot["capsule"] != capsule_ref:
            raise PanelReviewError(f"{label} capsule reference is stale")
        vote = vote_index.get(skill_id)
        if vote is None:
            raise PanelReviewError(
                f"{label} must contain exactly one target vote"
            )
        assignments.append(
            {
                "voter": ballot["voter"],
                "vote": vote,
                "capsule": _capsule,
                "ballot_ref": ballot_ref,
                "capsule_ref": capsule_ref,
                "capsule_bytes_proxy": _professional_v3_cached_canonical_size(
                    capsule_ref,
                    _capsule,
                    cache=cache,
                ),
                "capsule_input_blocks_proxy": (
                    _professional_v3_capsule_chain_input_blocks(
                        capsule=_capsule,
                        cache=cache,
                        validation_root=validation_root,
                        forbidden_paths={
                            *forbidden_paths,
                            origin_path,
                            packet_path,
                            ballot_path,
                        },
                    )
                ),
            }
        )
    recomputed = _professional_v3_fresh_target_decision(
        target=target,
        assignments=assignments,
    )
    if recomputed != stored:
        raise PanelReviewError(
            f"schema-3 carry origin target does not match actual evidence: {skill_id}"
        )
    if recomputed["final_disposition"] != (
        "accepted-current-professional-completeness"
    ):
        raise PanelReviewError(
            f"schema-3 carry origin target is not accepted: {skill_id}"
        )
    result = {
        "decision_ref": origin_ref,
        "decision": record,
        "packet": packet,
        "target": target,
        "assignments": assignments,
        "target_row": recomputed,
        "target_decision_fingerprint": recomputed[
            "target_decision_fingerprint"
        ],
        "reviewer_added_candidate_material_bindings": {
            candidate_id: state["bindings"][candidate_id][
                "package_material_binding"
            ]
            for candidate_id in recomputed["review_dependencies"][
                "reviewer_added_candidate_ids_union"
            ]
        },
    }
    cache["origin_targets"][target_cache_key] = result
    return result


def _professional_v3_sum_metrics(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    keys = sorted(
        {
            key
            for row in rows
            for key in row.get("evidence_metrics", {})
        }
    )
    return {
        key: sum(row["evidence_metrics"].get(key, 0) for row in rows)
        for key in keys
    }


def _professional_v3_disposition_summary(
    rows: list[dict[str, Any]], *, field: str, values: set[str]
) -> dict[str, int]:
    return {
        value: sum(row[field] == value for row in rows)
        for value in sorted(values)
    }


def _professional_v3_summary_from_rows(
    *,
    decisions: list[dict[str, Any]],
    packet: dict[str, Any],
    decision_voters: list[dict[str, Any]],
) -> dict[str, Any]:
    fresh_rows = [
        row for row in decisions if row["provenance"].get("mode") == "fresh"
    ]
    carried_rows = [
        row
        for row in decisions
        if row["provenance"].get("mode") == "carried-forward"
    ]
    if len(fresh_rows) + len(carried_rows) != len(decisions):
        raise PanelReviewError("schema-3 decision provenance modes are invalid")
    capsule_chains: dict[
        tuple[str, str], tuple[int, tuple[tuple[str, int], ...]]
    ] = {}
    for voter_index, voter in enumerate(decision_voters):
        if (
            not isinstance(voter, dict)
            or set(voter) != PROFESSIONAL_V3_DECISION_VOTER_FIELDS
        ):
            raise PanelReviewError(
                "schema-3 summary decision voter fields are invalid"
            )
        capsule = _artifact_reference_shape(
            voter.get("capsule"),
            label=f"schema-3 summary capsule voter[{voter_index}]",
            require_review_id=True,
            expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        )
        size = voter.get("capsule_canonical_json_bytes_proxy")
        if type(size) is not int or size <= 0:
            raise PanelReviewError(
                "schema-3 capsule canonical byte proxy must be positive"
            )
        blocks = voter.get("capsule_input_blocks_proxy")
        if not isinstance(blocks, list) or not blocks:
            raise PanelReviewError(
                "schema-3 capsule input block proxy must be non-empty"
            )
        normalized_blocks: list[tuple[str, int]] = []
        for block_index, block in enumerate(blocks):
            if (
                not isinstance(block, dict)
                or set(block) != PROFESSIONAL_V3_INPUT_BLOCK_FIELDS
            ):
                raise PanelReviewError(
                    "schema-3 capsule input block fields are invalid"
                )
            digest = _lowercase_sha256(
                block.get("sha256"),
                label=(
                    "schema-3 capsule input block "
                    f"voter[{voter_index}][{block_index}].sha256"
                ),
            )
            block_size = block.get("canonical_json_bytes_proxy")
            if type(block_size) is not int or block_size <= 0:
                raise PanelReviewError(
                    "schema-3 capsule input block byte proxy must be positive"
                )
            normalized_blocks.append((digest, block_size))
        if normalized_blocks != sorted(set(normalized_blocks)):
            raise PanelReviewError(
                "schema-3 capsule input blocks must be digest-sorted and unique"
            )
        key = (capsule["path"], capsule["sha256"])
        chain = (size, tuple(normalized_blocks))
        existing = capsule_chains.get(key)
        if existing is not None and existing != chain:
            raise PanelReviewError(
                "schema-3 capsule input chain conflicts across voters"
            )
        capsule_chains[key] = chain
    fresh_evidence_rows = 0
    for row in fresh_rows:
        evidence = row["provenance"].get("evidence")
        if not isinstance(evidence, list) or len(evidence) != PANEL_SIZE:
            raise PanelReviewError(
                f"schema-3 fresh decision evidence is incomplete: {row['skill_id']}"
            )
        fresh_evidence_rows += len(evidence)
        for item in evidence:
            if (
                not isinstance(item, dict)
                or set(item) != PROFESSIONAL_V3_PROVENANCE_EVIDENCE_FIELDS
            ):
                raise PanelReviewError(
                    f"schema-3 fresh decision evidence fields are invalid: {row['skill_id']}"
                )
    fresh_criterion_results = sum(
        row["evidence_metrics"]["criterion_result_count"]
        for row in fresh_rows
    )
    carried_criterion_results = sum(
        row["evidence_metrics"]["criterion_result_count"]
        for row in carried_rows
    )
    effective_criterion_results = (
        fresh_criterion_results + carried_criterion_results
    )
    expected_target_count = len(packet["professional_targets"])
    expected_effective_criteria = (
        expected_target_count
        * PANEL_SIZE
        * len(PROFESSIONAL_COMPLETENESS_CRITERIA)
    )
    if len(decisions) != expected_target_count:
        raise PanelReviewError(
            "schema-3 summary target count does not match its packet"
        )
    if fresh_evidence_rows != PANEL_SIZE * len(fresh_rows):
        raise PanelReviewError("schema-3 fresh vote count is stale")
    if effective_criterion_results != expected_effective_criteria:
        raise PanelReviewError(
            "schema-3 effective criterion evidence count is stale"
        )
    block_occurrences: dict[str, int] = {}
    block_sizes: dict[str, int] = {}
    for _capsule_size, blocks in capsule_chains.values():
        for digest, block_size in blocks:
            existing_size = block_sizes.get(digest)
            if existing_size is not None and existing_size != block_size:
                raise PanelReviewError(
                    "schema-3 input block size conflicts across capsules"
                )
            block_sizes[digest] = block_size
            block_occurrences[digest] = block_occurrences.get(digest, 0) + 1
    capsule_bytes = sum(
        block_sizes[digest] * min(count, PANEL_SIZE)
        for digest, count in block_occurrences.items()
    )
    full_blocks = _professional_v3_full_rereview_input_blocks(packet)
    full_rereview_bytes = PANEL_SIZE * sum(
        block["canonical_json_bytes_proxy"] for block in full_blocks
    )
    input_ratio_ppm = (
        capsule_bytes * 1_000_000 // full_rereview_bytes
        if full_rereview_bytes
        else 0
    )

    def dispositions(
        rows: list[dict[str, Any]], *, field: str, values: set[str]
    ) -> dict[str, int]:
        return _professional_v3_disposition_summary(
            rows, field=field, values=values
        )

    return {
        "partition": {
            "fresh_target_count": len(fresh_rows),
            "carried_target_count": len(carried_rows),
            "effective_target_count": len(decisions),
        },
        "professional_completeness": {
            "fresh": dispositions(
                fresh_rows,
                field="final_disposition",
                values=PROFESSIONAL_FINAL_DISPOSITIONS,
            ),
            "carried": dispositions(
                carried_rows,
                field="final_disposition",
                values=PROFESSIONAL_FINAL_DISPOSITIONS,
            ),
            "effective": dispositions(
                decisions,
                field="final_disposition",
                values=PROFESSIONAL_FINAL_DISPOSITIONS,
            ),
        },
        "ordinary_criterion_majority": {
            "fresh": dispositions(
                fresh_rows,
                field="ordinary_criterion_disposition",
                values=PROFESSIONAL_COMPLETENESS_DECISIONS,
            ),
            "carried": dispositions(
                carried_rows,
                field="ordinary_criterion_disposition",
                values=PROFESSIONAL_COMPLETENESS_DECISIONS,
            ),
            "effective": dispositions(
                decisions,
                field="ordinary_criterion_disposition",
                values=PROFESSIONAL_COMPLETENESS_DECISIONS,
            ),
        },
        "overall_ballot_majority_audit": {
            "fresh": dispositions(
                fresh_rows,
                field="winning_disposition",
                values=PROFESSIONAL_COMPLETENESS_DECISIONS,
            ),
            "carried": dispositions(
                carried_rows,
                field="winning_disposition",
                values=PROFESSIONAL_COMPLETENESS_DECISIONS,
            ),
            "effective": dispositions(
                decisions,
                field="winning_disposition",
                values=PROFESSIONAL_COMPLETENESS_DECISIONS,
            ),
        },
        "qualification": {
            "fresh_target_count": len(fresh_rows),
            "carried_target_count": len(carried_rows),
            "effective_covered_target_count": len(decisions),
            "required_domain_experts_per_fresh_target": 2,
            "required_architecture_experts_per_fresh_target": 1,
            "fresh_reviewer_pool_size": len(decision_voters),
        },
        "evidence": {
            "fresh": _professional_v3_sum_metrics(fresh_rows),
            "carried": _professional_v3_sum_metrics(carried_rows),
            "effective": _professional_v3_sum_metrics(decisions),
        },
        "review_cost": {
            "fresh_vote_count": PANEL_SIZE * len(fresh_rows),
            "avoided_vote_count": PANEL_SIZE * len(carried_rows),
            "fresh_criterion_result_count": fresh_criterion_results,
            "carried_criterion_result_count": carried_criterion_results,
            "effective_criterion_result_count": effective_criterion_results,
            "avoided_criterion_result_count": (
                PANEL_SIZE
                * len(PROFESSIONAL_COMPLETENESS_CRITERIA)
                * len(carried_rows)
            ),
            "canonical_capsule_input_bytes_proxy": capsule_bytes,
            "full_rereview_deduplicated_capsule_input_bytes_proxy": (
                full_rereview_bytes
            ),
            "input_ratio_ppm": input_ratio_ppm,
            "maximum_origin_depth": max(
                (row["provenance"]["origin_depth"] for row in decisions),
                default=0,
            ),
        },
    }


def _professional_v3_decision_record(
    *,
    packet: dict[str, Any],
    packet_ref: dict[str, str],
    decided_on: str,
    decision_voters: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    record = {
        "schema_version": PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
        "kind": PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        "review_id": packet["review_id"],
        "decided_on": decided_on,
        "decision_method": (
            PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
        ),
        "review_contract_fingerprint": packet[
            "review_contract_fingerprint"
        ],
        "panel_contract": packet["panel_contract"],
        "packet": packet_ref,
        "voters": decision_voters,
        "professional_decisions": decisions,
        "summary": _professional_v3_summary_from_rows(
            decisions=decisions,
            packet=packet,
            decision_voters=decision_voters,
        ),
        "limitations": [
            "Fresh evidence is derived only from validated target-scoped capsules; carried rows contain no new votes and point directly to a validated depth-zero fresh origin.",
            "Carried authority records the conservative deterministic Professional currentness projection through canonical package_material_binding, review_unit_binding, complete Registry and ordered Reference authority, and direct one-hop dependency material bindings; raw content and SHA records remain provenance and artifact-integrity evidence only; unsupported or ambiguous material changes require affected-package fresh review.",
            "Canonical JSON byte and optional ratio values are deterministic input-size proxies, not actual tokens, reviewer effort, latency, identity, credentials, behavior, or production outcomes.",
            "Static professional review and simulated carry validation do not prove real-host startup, wall-clock performance, production accuracy, or installed user experience.",
        ],
    }
    _professional_v3_decision_shape(
        record,
        validation_mode=validation_mode,
    )
    return record


def _aggregate_professional_completeness_ballots_v3(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_values: list[tuple[Path, dict[str, Any]]],
    decided_on: str,
    validation_root: Path = ROOT,
    validate_packet_plan: bool = True,
    forbidden_paths: set[Path] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Aggregate fresh evidence and exact direct-origin carries for schema 3."""

    cache = _professional_v3_invocation_cache()
    for index, (ballot_path, ballot_value) in enumerate(ballot_values):
        _path, _reference, bound_value = (
            _professional_v3_bind_json_artifact_path(
                ballot_path,
                cache=cache,
                validation_root=validation_root,
                label=f"schema-3 aggregate ballot[{index}]",
                expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                expected_review_id=packet["review_id"],
                forbidden_paths=forbidden_paths,
            )
        )
        if bound_value != ballot_value:
            raise PanelReviewError(
                f"schema-3 aggregate ballot[{index}] value is stale"
            )
    return aggregate_professional_completeness_ballot_paths_v3(
        packet=packet,
        packet_path=packet_path,
        ballot_paths=[path for path, _value in ballot_values],
        decided_on=decided_on,
        validation_root=validation_root,
        forbidden_paths=forbidden_paths,
        invocation_cache=cache,
        validation_mode=validation_mode,
    )

def aggregate_professional_completeness_ballot_paths_v3(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    ballot_paths: list[Path],
    decided_on: str,
    validation_root: Path = ROOT,
    forbidden_paths: set[Path] | None = None,
    invocation_cache: dict[str, Any] | None = None,
    validate_packet_plan: bool = True,
    packet_state: (
        dict[str, Any] | _ProfessionalV3CanonicalPacketState | None
    ) = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Bounded-memory schema-3 aggregation from canonical ballot paths."""

    _iso_date(decided_on, label="decided_on")
    forbidden = {path.resolve() for path in (forbidden_paths or set())}
    cache = invocation_cache or _professional_v3_invocation_cache()
    canonical_packet_path, packet_ref, bound_packet = (
        _professional_v3_bind_json_artifact_path(
            packet_path,
            cache=cache,
            validation_root=validation_root,
            label="schema-3 streaming aggregate packet",
            expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
            expected_review_id=packet["review_id"],
            forbidden_paths=forbidden,
        )
    )
    if bound_packet != packet:
        raise PanelReviewError(
            "schema-3 streaming aggregate packet value is stale"
        )
    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=packet_state,
        validation_root=validation_root,
        artifact_path=canonical_packet_path,
        validate_baseline=validate_packet_plan,
        forbidden_paths=forbidden,
        invocation_cache=cache,
        validation_mode=validation_mode,
    )
    packet = canonical_state.packet
    state = canonical_state.state
    projected_packet = _professional_v2_projection_from_v3(
        packet,
        validation_mode=validation_mode,
    )
    fresh_ids = _professional_v3_fresh_target_ids(packet)
    ballot_index: dict[str, list[dict[str, Any]]] = {
        skill_id: [] for skill_id in fresh_ids
    }
    voter_rows: list[dict[str, Any]] = []
    voter_ids: list[str] = []
    agent_ids: list[str] = []
    for raw_path in ballot_paths:
        ballot_path, ballot_ref, ballot = (
            _professional_v3_bind_json_artifact_path(
                raw_path,
                cache=cache,
                validation_root=validation_root,
                label="schema-3 streaming aggregate ballot",
                expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                expected_review_id=packet["review_id"],
                forbidden_paths={*forbidden, canonical_packet_path},
            )
        )
        capsule_path, capsule_ref, capsule = (
            _professional_v3_cached_json_artifact(
                ballot["capsule"],
                cache=cache,
                validation_root=validation_root,
                label="schema-3 streaming aggregate capsule",
                expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                expected_review_id=packet["review_id"],
                forbidden_paths={*forbidden, canonical_packet_path},
            )
        )
        _validate_professional_completeness_ballot_v3(
            packet,
            ballot,
            packet_sha256=packet_ref["sha256"],
            validation_root=validation_root,
            artifact_path=ballot_path,
            validate_packet_plan=validate_packet_plan,
            forbidden_paths=forbidden,
            packet_state=canonical_state,
            projected_packet=projected_packet,
            bound_capsule=(capsule_path, capsule_ref, capsule),
            validation_mode=validation_mode,
        )
        voter = copy.deepcopy(ballot["voter"])
        voter_id = voter["voter_id"]
        assigned_ids = [
            vote["skill_id"] for vote in ballot["professional_votes"]
        ]
        metadata = {
            "ballot_path": ballot_path,
            "ballot_ref": ballot_ref,
            "capsule_ref": capsule_ref,
            "capsule_bytes_proxy": _professional_v3_cached_canonical_size(
                capsule_ref,
                capsule,
                cache=cache,
            ),
            "capsule_input_blocks_proxy": (
                _professional_v3_capsule_chain_input_blocks(
                    capsule=capsule,
                    cache=cache,
                    validation_root=validation_root,
                    forbidden_paths={
                        *forbidden,
                        canonical_packet_path,
                        ballot_path,
                        capsule_path,
                    },
                )
            ),
            "voter": voter,
        }
        for vote in ballot["professional_votes"]:
            ballot_index[vote["skill_id"]].append(
                {
                    **metadata,
                    "vote": copy.deepcopy(vote),
                }
            )
        voter_rows.append(
            {
                **voter,
                "assigned_skill_ids": assigned_ids,
                "ballot": ballot_ref,
                "capsule": capsule_ref,
                "capsule_canonical_json_bytes_proxy": metadata[
                    "capsule_bytes_proxy"
                ],
                "capsule_input_blocks_proxy": copy.deepcopy(
                    metadata["capsule_input_blocks_proxy"]
                ),
            }
        )
        voter_ids.append(voter_id)
        agent_ids.append(voter["agent_id"])
        del ballot, capsule, capsule_path
    ordered = sorted(range(len(voter_rows)), key=lambda index: voter_ids[index])
    voter_rows = [voter_rows[index] for index in ordered]
    sorted_voter_ids = [voter_ids[index] for index in ordered]
    if sorted_voter_ids != sorted(set(sorted_voter_ids)):
        raise PanelReviewError(
            "schema-3 streaming reviewer voter identities must be unique"
        )
    if len(agent_ids) != len(set(agent_ids)):
        raise PanelReviewError(
            "schema-3 streaming reviewer agent identities must be unique"
        )
    targets = {
        target["skill_id"]: target
        for target in packet["professional_targets"]
    }
    fresh_rows: list[dict[str, Any]] = []
    for skill_id in fresh_ids:
        metadata_rows = ballot_index[skill_id]
        if len(metadata_rows) != PANEL_SIZE:
            raise PanelReviewError(
                f"schema-3 fresh target {skill_id} requires exactly three ballot paths"
            )
        assignments: list[dict[str, Any]] = [
                {
                    "voter": metadata["voter"],
                    "vote": metadata["vote"],
                    "ballot_ref": metadata["ballot_ref"],
                    "capsule_ref": metadata["capsule_ref"],
                    "capsule_bytes_proxy": metadata[
                        "capsule_bytes_proxy"
                    ],
                    "capsule_input_blocks_proxy": metadata[
                        "capsule_input_blocks_proxy"
                    ],
                }
            for metadata in metadata_rows
        ]
        fresh_rows.append(
            _professional_v3_fresh_target_decision(
                target=targets[skill_id], assignments=assignments
            )
        )
        del assignments
    carried_rows: list[dict[str, Any]] = []
    for plan_row in state["plan"]["carried_targets"]:
        skill_id = plan_row["skill_id"]
        if "origin_attestation" in plan_row:
            baseline_state = state.get("baseline_state")
            if (
                not isinstance(baseline_state, dict)
                or "attestation_ref" not in baseline_state
            ):
                raise PanelReviewError(
                    "schema-3 carried attestation origin is unavailable"
                )
            origin_state = baseline_state["origins"].get(skill_id)
            if (
                not isinstance(origin_state, dict)
                or origin_state.get("attestation_ref")
                != plan_row["origin_attestation"]
                or origin_state.get("origin_verdict_digest")
                != plan_row["origin_verdict_digest"]
            ):
                raise PanelReviewError(
                    f"schema-3 carried attestation origin is stale: {skill_id}"
                )
            finding = origin_state["finding"]
            origin = {
                "target_row": _professional_attestation_origin_row(finding),
                "decision_ref": plan_row["origin_attestation"],
                "reviewer_added_candidate_material_bindings": {
                    candidate_id: baseline_state["attestation"][
                        "dependency_material_catalog"
                    ][candidate_id]
                    for candidate_id in finding["dependency_ids"]
                    if candidate_id
                    in finding["result"]["review_dependencies"][
                        "reviewer_added_candidate_ids_union"
                    ]
                },
            }
        else:
            origin = _load_professional_v3_fresh_origin_target(
                origin_reference=plan_row["origin_decision"],
                skill_id=skill_id,
                expected_target_decision_fingerprint=plan_row[
                    "origin_target_decision_fingerprint"
                ],
                validation_root=validation_root,
                forbidden_paths={*forbidden, canonical_packet_path},
                invocation_cache=cache,
                validation_mode=validation_mode,
            )
        carried_rows.append(
            _professional_v3_carried_target_decision(
                target=targets[skill_id],
                origin_row=origin["target_row"],
                origin_decision_ref=origin["decision_ref"],
                current_bindings=state["bindings"],
                origin_candidate_material_bindings=origin[
                    "reviewer_added_candidate_material_bindings"
                ],
            )
        )
    decisions = sorted(
        [*fresh_rows, *carried_rows], key=lambda row: row["skill_id"]
    )
    return _professional_v3_decision_record(
        packet=packet,
        packet_ref=packet_ref,
        decided_on=decided_on,
        decision_voters=voter_rows,
        decisions=decisions,
        validation_mode=validation_mode,
    )


def _validate_professional_completeness_decision_record_v3(
    record: dict[str, Any],
    *,
    record_path: Path,
    validation_root: Path = ROOT,
    forbidden_paths: set[Path] | None = None,
    validate_packet_baseline: bool = True,
    canonical_packet_state: (
        _ProfessionalV3CanonicalPacketState | None
    ) = None,
    invocation_cache: dict[str, Any] | None = None,
    validation_mode: str = VALIDATION_MODE_CURRENT,
) -> dict[str, Any]:
    """Recompute a complete schema-3 decision from artifact evidence."""

    _professional_v3_decision_shape(
        record,
        validation_mode=validation_mode,
    )
    forbidden = {path.resolve() for path in (forbidden_paths or set())}
    cache = invocation_cache or _professional_v3_invocation_cache()
    canonical_record_path, decision_ref, record_from_artifact = (
        _professional_v3_bind_json_artifact_path(
            record_path,
            cache=cache,
            validation_root=validation_root,
        label="schema-3 decision record",
        expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            expected_review_id=record["review_id"],
        forbidden_paths=forbidden,
        )
    )
    if record_from_artifact != record:
        raise PanelReviewError(
            "schema-3 decision value does not match its artifact"
        )
    if canonical_packet_state is None:
        packet_path, packet_ref, packet, supplied_state = (
            _professional_v3_load_packet_for_decision(
                record,
                validation_root=validation_root,
                forbidden_paths={*forbidden, canonical_record_path},
                validate_baseline=validate_packet_baseline,
                invocation_cache=cache,
                validation_mode=validation_mode,
            )
        )
    else:
        if not isinstance(
            canonical_packet_state,
            _ProfessionalV3CanonicalPacketState,
        ):
            raise PanelReviewError(
                "schema-3 decision packet state must be a sealed canonical handle"
            )
        packet_path, packet_ref, bound_packet = (
            _professional_v3_cached_json_artifact(
                record.get("packet"),
                cache=cache,
                validation_root=validation_root,
                label="schema-3 decision packet",
                expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                expected_review_id=record["review_id"],
                forbidden_paths={*forbidden, canonical_record_path},
            )
        )
        packet = canonical_packet_state.packet
        if bound_packet != packet:
            raise PanelReviewError(
                "schema-3 decision packet value does not match canonical state"
            )
        if packet["review_id"] != record["review_id"]:
            raise PanelReviewError(
                "schema-3 decision packet review_id is stale"
            )
        if record.get("review_contract_fingerprint") != packet[
            "review_contract_fingerprint"
        ]:
            raise PanelReviewError(
                "schema-3 decision packet contract is stale"
            )
        supplied_state = canonical_packet_state
    canonical_state = _professional_v3_canonical_packet_state(
        packet,
        supplied_state=supplied_state,
        validation_root=validation_root,
        artifact_path=packet_path,
        validate_baseline=validate_packet_baseline,
        forbidden_paths={*forbidden, canonical_record_path},
        invocation_cache=cache,
        validation_mode=validation_mode,
    )
    packet = canonical_state.packet
    _state = canonical_state.state
    _professional_v3_validate_decision_projection(
        record=record,
        packet=packet,
        state=_state,
    )
    if packet_ref != record["packet"]:
        raise PanelReviewError("schema-3 decision packet reference is stale")
    voters = record.get("voters")
    if not isinstance(voters, list):
        raise PanelReviewError("schema-3 decision voters must be an array")
    ballot_paths = [
        _canonical_artifact_path(
            voter["ballot"]["path"],
            validation_root=validation_root,
            label=f"schema-3 decision voter {voter['voter_id']} ballot",
            forbidden_paths={*forbidden, canonical_record_path, packet_path},
        )
        for voter in voters
    ]
    recomputed_stream = aggregate_professional_completeness_ballot_paths_v3(
        packet=packet,
        packet_path=packet_path,
        ballot_paths=ballot_paths,
        decided_on=record["decided_on"],
        validation_root=validation_root,
        forbidden_paths={*forbidden, canonical_record_path},
        invocation_cache=cache,
        validate_packet_plan=False,
        packet_state=canonical_state,
        validation_mode=validation_mode,
    )
    if recomputed_stream != record:
        raise PanelReviewError(
            "professional completeness schema-3 decision does not match recomputed evidence"
        )
    return record

def _load_professional_v3_baseline(
    decision_path: Path,
    *,
    validation_root: Path,
    forbidden_paths: set[Path],
    invocation_cache: dict[str, Any] | None = None,
    decision_reference: dict[str, str] | None = None,
    validate_evidence: bool = True,
    allow_stale_contract_checkpoint: bool = False,
    validation_mode: str = VALIDATION_MODE_CURRENT,
    expected_review_contract_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Validate one bounded canonical carry lineage and its effective evidence."""

    cache = invocation_cache or _professional_v3_invocation_cache()

    lexical_decision_path = (
        decision_path
        if decision_path.is_absolute()
        else validation_root / decision_path
    )
    absolute_decision_path = lexical_decision_path.absolute()
    try:
        relative = absolute_decision_path.relative_to(
            validation_root.absolute()
        ).as_posix()
    except ValueError:
        try:
            relative = absolute_decision_path.relative_to(
                validation_root.resolve()
            ).as_posix()
        except ValueError as exc:
            raise PanelReviewError(
                "schema-3 baseline decision escapes validation root"
            ) from exc
    canonical_path = _canonical_artifact_path(
        relative,
        validation_root=validation_root,
        label="schema-3 baseline decision",
        forbidden_paths=forbidden_paths,
    )
    prebound: tuple[Path, dict[str, str], dict[str, Any]] | None = None
    if decision_reference is None:
        prebound = _professional_v3_bind_json_artifact_path(
            canonical_path,
            cache=cache,
            validation_root=validation_root,
            label="schema-3 baseline decision",
            expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
            expected_review_id=canonical_path.parents[1].name,
            forbidden_paths=forbidden_paths,
        )
        baseline_ref = prebound[1]
    else:
        baseline_ref = decision_reference
    shaped_baseline_ref = _artifact_reference_shape(
        baseline_ref,
        label="schema-3 baseline decision",
        require_review_id=True,
        expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
        expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
    )
    if shaped_baseline_ref["path"] != relative:
        raise PanelReviewError("schema-3 baseline decision path is stale")
    forbidden_scope = tuple(
        sorted(path.resolve().as_posix() for path in forbidden_paths)
    )
    baseline_key = (
        validation_root.resolve().as_posix(),
        shaped_baseline_ref["path"],
        shaped_baseline_ref["sha256"],
        forbidden_scope,
        validate_evidence,
        allow_stale_contract_checkpoint,
        validation_mode,
        expected_review_contract_fingerprint,
    )
    cached_baseline = cache["baselines"].get(baseline_key)
    if cached_baseline is not None:
        return cached_baseline
    if prebound is None:
        canonical_path, _baseline_ref, record = (
            _professional_v3_cached_json_artifact(
                shaped_baseline_ref,
                cache=cache,
                validation_root=validation_root,
                label="schema-3 baseline decision",
                expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                expected_review_id=canonical_path.parents[1].name,
                forbidden_paths=forbidden_paths,
            )
        )
    else:
        canonical_path, _baseline_ref, record = prebound
    baseline_contract = _professional_v3_decision_envelope(record)
    current_contract = (
        _professional_evidence_review_contract_fingerprint()
        if expected_review_contract_fingerprint is None
        else _lowercase_sha256(
            expected_review_contract_fingerprint,
            label="schema-3 expected baseline review contract",
        )
    )
    if baseline_contract != current_contract:
        if not allow_stale_contract_checkpoint:
            raise PanelReviewError(
                "schema-3 stale-contract baseline cannot authorize carry"
            )
        packet_path, packet_ref, packet = (
            _professional_v3_cached_json_artifact(
                record.get("packet"),
                cache=cache,
                validation_root=validation_root,
                label="schema-3 stale-contract baseline packet",
                expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                expected_review_id=record["review_id"],
                forbidden_paths={*forbidden_paths, canonical_path},
            )
        )
        expected_stale_packet_fields = (
            PROFESSIONAL_HISTORICAL_V3_PACKET_FIELDS
            if baseline_contract
            in {
                PROFESSIONAL_HISTORICAL_V2_REVIEW_CONTRACT_FINGERPRINT,
                PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT,
                PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT,
            }
            else PROFESSIONAL_V3_PACKET_FIELDS
        )
        if set(packet) != expected_stale_packet_fields:
            raise PanelReviewError(
                "schema-3 stale-contract baseline packet fields are invalid"
            )
        if (
            packet.get("schema_version")
            != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            or packet.get("kind")
            != PROFESSIONAL_COMPLETENESS_PACKET_KIND
            or packet.get("review_id") != record["review_id"]
        ):
            raise PanelReviewError(
                "schema-3 stale-contract baseline packet envelope is invalid"
            )
        _iso_date(
            packet.get("created_on"),
            label="schema-3 stale-contract baseline packet.created_on",
        )
        packet_contract = _lowercase_sha256(
            packet.get("review_contract_fingerprint"),
            label="schema-3 stale-contract baseline packet contract",
        )
        if packet_contract == current_contract:
            raise PanelReviewError(
                "schema-3 stale-contract baseline packet is not stale"
            )
        if packet_contract != baseline_contract:
            raise PanelReviewError(
                "schema-3 stale-contract decision and packet contracts differ"
            )
        if record.get("packet") != packet_ref:
            raise PanelReviewError(
                "schema-3 stale-contract decision packet reference is stale"
            )
        packet_plan = packet.get("review_plan")
        if (
            not isinstance(packet_plan, dict)
            or packet_plan.get("review_contract_fingerprint")
            != baseline_contract
        ):
            raise PanelReviewError(
                "schema-3 stale-contract packet plan contract is stale"
            )
        result = {
            "decision_ref": _baseline_ref,
            "packet_ref": packet_ref,
            "snapshot": {
                "review_contract_fingerprint": baseline_contract,
                "targets": {},
            },
            "dependencies": {},
            "origins": {},
            "record": record,
            "packet": packet,
            "packet_path": packet_path,
            "plan_lineage_depth": 0,
            "contract_mismatch_checkpoint": True,
        }
        cache["baselines"][baseline_key] = result
        return result
    _professional_v3_decision_shape(
        record,
        validation_mode=validation_mode,
    )
    _validate_professional_completeness_decision_record_v3(
        record,
        record_path=canonical_path,
        validation_root=validation_root,
        forbidden_paths=forbidden_paths,
        validate_packet_baseline=validate_evidence,
        invocation_cache=cache,
        validation_mode=validation_mode,
    )
    packet_path, packet_ref, packet, state = (
        _professional_v3_load_packet_for_decision(
            record,
            validation_root=validation_root,
            forbidden_paths={*forbidden_paths, canonical_path},
        validate_baseline=False,
        invocation_cache=cache,
        validation_mode=validation_mode,
    )
    )
    decision_ref = _baseline_ref
    rows = record["professional_decisions"]
    if [row.get("skill_id") for row in rows] != sorted(
        state["bindings"]
    ):
        raise PanelReviewError(
            "schema-3 baseline decision target coverage is stale"
        )
    dependencies: dict[str, dict[str, Any]] = {}
    origins: dict[str, dict[str, Any]] = {}
    for row in rows:
        skill_id = row["skill_id"]
        dependency = row.get("review_dependencies")
        if not isinstance(dependency, dict):
            raise PanelReviewError(
                f"schema-3 baseline dependency is missing: {skill_id}"
            )
        dependencies[skill_id] = copy.deepcopy(dependency)
        provenance = row.get("provenance")
        if not isinstance(provenance, dict):
            raise PanelReviewError(
                f"schema-3 baseline provenance is invalid: {skill_id}"
            )
        if provenance.get("mode") == "fresh":
            if provenance.get("origin_depth") != 0:
                raise PanelReviewError(
                    f"schema-3 fresh baseline origin depth is stale: {skill_id}"
                )
            origins[skill_id] = {
                "decision_ref": decision_ref,
                "target_decision_fingerprint": row[
                    "target_decision_fingerprint"
                ],
            }
        elif provenance.get("mode") == "carried-forward":
            if provenance.get("origin_depth") != 1:
                raise PanelReviewError(
                    f"schema-3 carried baseline origin depth is stale: {skill_id}"
                )
            origin_ref = _artifact_reference_shape(
                provenance.get("origin_decision"),
                label=f"schema-3 baseline origin {skill_id}",
                require_review_id=True,
                expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            )
            if origin_ref == decision_ref:
                raise PanelReviewError(
                    f"schema-3 baseline origin cannot self-reference: {skill_id}"
                )
            origins[skill_id] = {
                "decision_ref": origin_ref,
                "target_decision_fingerprint": _lowercase_sha256(
                    provenance.get("origin_target_decision_fingerprint"),
                    label=f"schema-3 baseline origin {skill_id} fingerprint",
                ),
            }
        else:
            raise PanelReviewError(
                f"schema-3 baseline provenance mode is invalid: {skill_id}"
            )
    result = {
        "decision_ref": decision_ref,
        "packet_ref": packet_ref,
        "snapshot": state["snapshot"],
        "dependencies": dependencies,
        "origins": origins,
        "record": record,
        "packet": packet,
        "packet_path": packet_path,
        "plan_lineage_depth": state["plan"]["plan_lineage_depth"],
    }
    cache["baselines"][baseline_key] = result
    return result


def _cli_path(value: str) -> Path:
    candidate = Path(value)
    return (candidate if candidate.is_absolute() else ROOT / candidate).absolute()


def _ephemeral_review_path(review_id: str, *parts: str) -> Path:
    """Return one canonical transient path below the named review run."""

    relative = panel_attestation.ephemeral_run_path(
        review_id, "/".join(parts)
    )
    return (ROOT / relative).absolute()


def _semantic_runtime_layout(
    review_id: str, *, voter_id: str | None = None
) -> dict[str, Path]:
    """Return the one canonical transient Semantic runtime layout."""

    packet = _ephemeral_review_path(review_id, "packet.json")
    run = packet.parent
    layout = {
        "run": run,
        "packet": packet,
        "audit": _ephemeral_review_path(
            review_id, "inputs", "skill-content-audit.json"
        ),
        "ballots": _ephemeral_review_path(review_id, "ballots"),
    }
    if voter_id is not None:
        if VOTER_ID_PATTERN.fullmatch(voter_id) is None:
            raise PanelReviewError("Semantic runtime voter_id is invalid")
        layout["template"] = _ephemeral_review_path(
            review_id, "ballots", f"{voter_id}.template.json"
        )
        layout["ballot"] = _ephemeral_review_path(
            review_id, "ballots", f"{voter_id}.json"
        )
    return layout


def _semantic_prepare_reviewer_specs(
    value: object,
) -> list[tuple[str, str, str, str]]:
    if not isinstance(value, list) or len(value) != PANEL_SIZE:
        raise PanelReviewError(
            "Semantic prepare requires exactly three --reviewer declarations"
        )
    reviewers: list[tuple[str, str, str, str]] = []
    for index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 4:
            raise PanelReviewError(
                f"Semantic prepare reviewer[{index}] is invalid"
            )
        voter_id, agent_id, role, expertise = row
        if not isinstance(voter_id, str) or VOTER_ID_PATTERN.fullmatch(
            voter_id
        ) is None:
            raise PanelReviewError(
                f"Semantic prepare reviewer[{index}] voter_id is invalid"
            )
        reviewers.append(
            (
                voter_id,
                _non_blank(agent_id, label=f"reviewer[{index}].agent_id"),
                _non_blank(role, label=f"reviewer[{index}].role"),
                _non_blank(expertise, label=f"reviewer[{index}].expertise"),
            )
        )
    for field_index, label in (
        (0, "voter"),
        (1, "agent"),
        (2, "role"),
        (3, "expertise"),
    ):
        values = [row[field_index] for row in reviewers]
        if len(set(values)) != PANEL_SIZE:
            raise PanelReviewError(
                f"Semantic prepare reviewer {label} identities must be distinct"
            )
    return reviewers


def _semantic_prepare_audit_authority(
    audit_argument: str,
) -> tuple[bytes, dict[str, Any]]:
    """Bind the canonical tracked audit to clean HEAD before any run write."""

    relative = "reports/skill-content-audit.json"
    expected = (ROOT / relative).absolute()
    _require_exact_materialization_path_argument(
        audit_argument,
        expected,
        label="Semantic prepare audit",
    )
    status = _git_output(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).stdout
    if status:
        raise PanelReviewError("Semantic prepare requires a clean tracked tree")
    tracked = _git_output(
        "ls-files", "--error-unmatch", "--", relative, check=False
    )
    if tracked.returncode != 0:
        raise PanelReviewError("Semantic prepare audit must be tracked")
    head_raw = _git_output("show", f"HEAD:{relative}").stdout
    bound = reviewer_manifest.read_bound_regular_file(
        expected,
        max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
        label="Semantic prepare audit",
    )
    if bound.raw != head_raw:
        raise PanelReviewError(
            "Semantic prepare audit must be byte-equal to clean HEAD"
        )
    audit = reviewer_manifest.parse_json_object_bytes(
        bound.raw,
        label="Semantic prepare audit",
    )
    return bound.raw, audit


def _open_or_create_semantic_panel_directory() -> int:
    """Open the trusted ignored panel root without following any component."""

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    root = ROOT.resolve()
    descriptor: int | None = None
    try:
        descriptor = os.open(root, flags)
        for part in (".rd-skills", "expert-panel"):
            try:
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                    os.fsync(descriptor)
                except FileExistsError:
                    pass
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise PanelReviewError(
            "Semantic prepare panel root must not traverse a symlink"
        ) from exc


def _create_semantic_runtime(
    *,
    review_id: str,
    audit_raw: bytes,
    packet: dict[str, Any],
    templates: list[dict[str, Any]],
) -> dict[str, Path]:
    """Create one complete Semantic run or remove every owned partial artifact."""

    layout = _semantic_runtime_layout(review_id)
    panel_fd: int | None = None
    run_fd: int | None = None
    child_fds: dict[str, int] = {}
    run_identity: tuple[int, int] | None = None
    child_identities: dict[str, tuple[int, int]] = {}
    created_files: list[tuple[int, str, tuple[int, int]]] = []

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    file_flags |= getattr(os, "O_NOFOLLOW", 0)
    file_flags |= getattr(os, "O_CLOEXEC", 0)

    def create_file(
        directory_fd: int, name: str, raw: bytes, *, label: str
    ) -> None:
        descriptor: int | None = None
        try:
            descriptor = os.open(
                name,
                file_flags,
                0o644,
                dir_fd=directory_fd,
            )
            initial = os.fstat(descriptor)
            identity = (initial.st_dev, initial.st_ino)
            if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1:
                raise PanelReviewError(f"{label} is not a single-link regular file")
            created_files.append((directory_fd, name, identity))
            os.fchmod(descriptor, 0o644)
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:  # pragma: no cover - os.write raises.
                    raise OSError("short write")
                offset += written
            os.fsync(descriptor)
            final = os.fstat(descriptor)
            if (
                (final.st_dev, final.st_ino) != identity
                or final.st_size != len(raw)
                or final.st_nlink != 1
            ):
                raise PanelReviewError(f"{label} changed during durable write")
            os.fsync(directory_fd)
        except FileExistsError as exc:
            raise PanelReviewError(f"{label} already exists") from exc
        except PanelReviewError:
            raise
        except OSError as exc:
            raise PanelReviewError(f"cannot write {label}: {exc}") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def remove_owned_file(
        directory_fd: int, name: str, identity: tuple[int, int]
    ) -> None:
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != identity:
            raise PanelReviewError(
                "Semantic prepare cleanup ownership changed"
            )
        os.unlink(name, dir_fd=directory_fd)
        os.fsync(directory_fd)

    def remove_owned_directory(
        parent_fd: int, name: str, identity: tuple[int, int]
    ) -> None:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != identity:
            raise PanelReviewError(
                "Semantic prepare cleanup directory ownership changed"
            )
        os.rmdir(name, dir_fd=parent_fd)
        os.fsync(parent_fd)

    try:
        panel_fd = _open_or_create_semantic_panel_directory()
        try:
            os.mkdir(review_id, mode=0o755, dir_fd=panel_fd)
        except FileExistsError as exc:
            raise PanelReviewError(
                "Semantic prepare canonical run already exists"
            ) from exc
        run_stat = os.stat(review_id, dir_fd=panel_fd, follow_symlinks=False)
        run_identity = (run_stat.st_dev, run_stat.st_ino)
        os.fsync(panel_fd)
        run_fd = os.open(review_id, directory_flags, dir_fd=panel_fd)
        if (os.fstat(run_fd).st_dev, os.fstat(run_fd).st_ino) != run_identity:
            raise PanelReviewError("Semantic prepare run identity changed")

        for name in ("inputs", "ballots"):
            os.mkdir(name, mode=0o755, dir_fd=run_fd)
            child_stat = os.stat(name, dir_fd=run_fd, follow_symlinks=False)
            child_identities[name] = (child_stat.st_dev, child_stat.st_ino)
            os.fsync(run_fd)
            child_fds[name] = os.open(name, directory_flags, dir_fd=run_fd)

        create_file(
            child_fds["inputs"],
            "skill-content-audit.json",
            audit_raw,
            label="Semantic prepare audit snapshot",
        )
        packet_raw = reviewer_manifest.canonical_ballot_bytes(
            packet, compact=False
        )
        create_file(
            run_fd,
            "packet.json",
            packet_raw,
            label="Semantic prepare packet",
        )
        for template in templates:
            voter_id = template["voter"]["voter_id"]
            create_file(
                child_fds["ballots"],
                f"{voter_id}.template.json",
                reviewer_manifest.canonical_ballot_bytes(
                    template, compact=False
                ),
                label=f"Semantic prepare template {voter_id}",
            )

        stored_audit = reviewer_manifest.read_bound_regular_file(
            layout["audit"],
            max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
            label="prepared Semantic audit",
        )
        stored_packet = reviewer_manifest.read_bound_regular_file(
            layout["packet"],
            max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
            label="prepared Semantic packet",
        )
        if stored_audit.raw != audit_raw or stored_packet.raw != packet_raw:
            raise PanelReviewError("Semantic prepare stored bytes are stale")
        audit = reviewer_manifest.parse_json_object_bytes(
            stored_audit.raw, label="prepared Semantic audit"
        )
        stored_packet_value = reviewer_manifest.parse_json_object_bytes(
            stored_packet.raw, label="prepared Semantic packet"
        )
        validate_semantic_packet_current(stored_packet_value, audit)
        for template in templates:
            voter_id = template["voter"]["voter_id"]
            template_path = _semantic_runtime_layout(
                review_id, voter_id=voter_id
            )["template"]
            bound_template = reviewer_manifest.read_bound_regular_file(
                template_path,
                max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
                label=f"prepared Semantic template {voter_id}",
            )
            stored_template = reviewer_manifest.parse_json_object_bytes(
                bound_template.raw,
                label=f"prepared Semantic template {voter_id}",
            )
            validate_ballot_template(
                stored_packet_value,
                stored_template,
                packet_sha256=stored_packet.sha256,
            )
        os.fsync(child_fds["inputs"])
        os.fsync(child_fds["ballots"])
        os.fsync(run_fd)
        os.fsync(panel_fd)
        return layout
    except Exception as exc:
        cleanup_errors: list[str] = []
        for directory_fd, name, identity in reversed(created_files):
            try:
                remove_owned_file(directory_fd, name, identity)
            except (OSError, PanelReviewError) as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        if run_fd is not None:
            for name in ("ballots", "inputs"):
                identity = child_identities.get(name)
                if identity is None:
                    continue
                try:
                    remove_owned_directory(run_fd, name, identity)
                except (OSError, PanelReviewError) as cleanup_exc:
                    cleanup_errors.append(str(cleanup_exc))
        if panel_fd is not None and run_identity is not None:
            try:
                remove_owned_directory(panel_fd, review_id, run_identity)
            except (OSError, PanelReviewError) as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        if cleanup_errors:
            raise PanelReviewError(
                f"{exc}; Semantic prepare rollback failed: "
                + "; ".join(cleanup_errors)
            ) from exc
        if isinstance(exc, PanelReviewError):
            raise
        raise PanelReviewError(f"Semantic prepare failed: {exc}") from exc
    finally:
        for descriptor in child_fds.values():
            os.close(descriptor)
        if run_fd is not None:
            os.close(run_fd)
        if panel_fd is not None:
            os.close(panel_fd)


def _is_round_packet_path(path: Path) -> bool:
    """Recognize current transient and immutable legacy packet layouts."""

    if path.name != "packet.json":
        return False
    parent = path.parent.parent.absolute()
    return parent in {
        (ROOT / ".rd-skills" / "expert-panel").absolute(),
        (ROOT / "evals" / "expert-panel").absolute(),
    }


def _is_ephemeral_round_path(path: Path) -> bool:
    try:
        relative = path.absolute().relative_to(ROOT.absolute()).as_posix()
        panel_attestation.validate_ephemeral_run_path(relative)
    except (ValueError, panel_attestation.AttestationError):
        return False
    return True


def _require_same_ephemeral_run_path(
    path: Path, *, review_id: str, label: str
) -> Path:
    """Reject writable paths outside the exact transient review run."""

    try:
        relative = path.absolute().relative_to(ROOT.absolute()).as_posix()
        panel_attestation.validate_ephemeral_run_path(
            relative, review_id=review_id
        )
    except (ValueError, panel_attestation.AttestationError) as exc:
        raise PanelReviewError(
            f"{label} must stay inside the canonical transient review run"
        ) from exc
    return _canonical_artifact_path(
        relative,
        validation_root=ROOT,
        label=label,
        must_exist=False,
    )


def _display_cli_path(path: Path) -> Path:
    try:
        return path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return path


def _require_schema3_cli_artifact_path(
    path: Path,
    *,
    review_id: str,
    kind: str,
    voter_id: str | None = None,
) -> Path:
    if kind == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
        expected = _ephemeral_review_path(review_id, "packet.json")
    elif kind == PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND:
        expected = (
            _ephemeral_review_path(
                review_id, "discovery-capsules", f"{voter_id}.json"
            )
        )
    elif kind == PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND:
        expected = (
            _ephemeral_review_path(
                review_id, "candidate-requests", f"{voter_id}.json"
            )
        )
    elif kind == PROFESSIONAL_COMPLETENESS_CAPSULE_KIND:
        expected = (
            _ephemeral_review_path(
                review_id, "capsules", f"{voter_id}.json"
            )
        )
    elif kind == PROFESSIONAL_COMPLETENESS_BALLOT_KIND:
        expected = (
            _ephemeral_review_path(
                review_id, "panel", f"{voter_id}.json"
            )
        )
    elif kind == PROFESSIONAL_COMPLETENESS_DECISION_KIND:
        expected = (
            _ephemeral_review_path(review_id, "panel", "decision.json")
        )
    else:
        raise PanelReviewError("schema-3 CLI artifact kind is invalid")
    if path.absolute() != expected.absolute():
        raise PanelReviewError(
            f"schema-3 output must use canonical path: {expected.relative_to(ROOT)}"
        )
    return _canonical_artifact_path(
        expected.relative_to(ROOT).as_posix(),
        validation_root=ROOT,
        label="schema-3 output path",
        must_exist=False,
    )


def _require_readability_schema2_cli_packet_path(
    path: Path,
    *,
    review_id: str,
) -> Path:
    """Require the one immutable repository layout for a schema-2 packet."""

    if VOTER_ID_PATTERN.fullmatch(review_id) is None:
        raise PanelReviewError(
            "readability schema-2 packet review_id is not canonical"
        )
    expected = _ephemeral_review_path(review_id, "packet.json")
    if path.absolute() != expected.absolute():
        raise PanelReviewError(
            "readability schema-2 output must use canonical path: "
            f"{expected.relative_to(ROOT)}"
        )
    return _canonical_artifact_path(
        expected.relative_to(ROOT).as_posix(),
        validation_root=ROOT,
        label="readability schema-2 output path",
        must_exist=False,
    )


def _parse_reviewer_added_requests(
    values: list[str], *, assigned_skill_ids: list[str]
) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {
        skill_id: [] for skill_id in sorted(set(assigned_skill_ids))
    }
    for index, value in enumerate(values):
        if value.count("=") < 2:
            raise PanelReviewError(
                f"reviewer-added-request[{index}] must be TARGET=SKILL=DISCOVERY_REASON"
            )
        target_id, candidate_id, reason = value.split("=", 2)
        target_id = _non_blank(
            target_id,
            label=f"reviewer-added-request[{index}].target",
        )
        candidate_id = _non_blank(
            candidate_id,
            label=f"reviewer-added-request[{index}].candidate",
        )
        reason = _validate_rationale(
            reason,
            label=f"reviewer-added-request[{index}].discovery_reason",
        )
        if target_id not in result:
            raise PanelReviewError(
                f"reviewer-added request target is not assigned: {target_id}"
            )
        result[target_id].append(
            {"skill_id": candidate_id, "discovery_reason": reason}
        )
    for target_id, rows in result.items():
        candidate_ids = [row["skill_id"] for row in rows]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise PanelReviewError(
                f"reviewer-added requests contain duplicates: {target_id}"
            )
        result[target_id] = sorted(rows, key=lambda row: row["skill_id"])
    return result


def _materialization_json_object(raw: bytes, *, label: str) -> dict[str, Any]:
    return reviewer_manifest.parse_json_object_bytes(raw, label=label)


def _require_materialization_argument_bounds(args: argparse.Namespace) -> None:
    for name in (
        "packet",
        "audit",
        "template",
        "template_sha256",
        "manifest",
        "manifest_sha256",
        "stdin_framing",
        "out",
    ):
        value = getattr(args, name)
        if len(str(value).encode("utf-8")) > 4_096:
            raise PanelReviewError(
                f"materialize-ballot --{name.replace('_', '-')} exceeds 4096 bytes"
            )


def _require_exact_materialization_path_argument(
    value: str,
    expected: Path,
    *,
    label: str,
) -> None:
    allowed = {expected.as_posix()}
    try:
        allowed.add(expected.relative_to(ROOT).as_posix())
    except ValueError:  # pragma: no cover - Semantic paths are repository-owned.
        pass
    if value not in allowed:
        raise PanelReviewError(f"{label} must use its canonical path")


def _canonical_materialization_template(
    packet: dict[str, Any],
    template: dict[str, Any],
    *,
    packet_sha256: str,
) -> dict[str, Any]:
    """Rebuild the validated template to recover builder-owned key ordering."""

    voter = template["voter"]
    professional_schema3 = (
        packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND
        and packet.get("schema_version")
        == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    )
    capsule_path = None
    skill_ids = None
    if professional_schema3:
        capsule_path = _validated_artifact_reference(
            template.get("capsule"),
            validation_root=ROOT,
            label="schema-3 ballot template capsule",
            require_review_id=True,
            expected_kind=PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
            expected_axis=PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
            expected_review_id=packet.get("review_id"),
        )[0]
        skill_ids = [
            row.get("skill_id")
            for row in template.get("professional_votes", [])
        ]
    return build_ballot_template(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter.get("voter_id"),
        agent_id=voter.get("agent_id"),
        role=voter.get("role"),
        expertise=voter.get("expertise"),
        expertise_tags=voter.get("expertise_tags"),
        capsule_path=capsule_path,
        validation_root=ROOT,
        skill_ids=skill_ids,
        created_on=template.get("created_on"),
    )


def _materialize_ballot(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    """Materialize one transient reviewer manifest through existing validators."""

    _require_materialization_argument_bounds(args)
    packet_path = _cli_path(args.packet)
    schema3_layout = _is_round_packet_path(packet_path)
    packet_ref: dict[str, str] | None = None
    if schema3_layout:
        cache = _professional_v3_invocation_cache()
        packet_path, packet_ref, packet = _professional_v3_bind_json_artifact_path(
            packet_path,
            cache=cache,
            validation_root=ROOT,
            label="schema-3 materialize-ballot packet",
            expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
            expected_review_id=packet_path.parent.name,
        )
    else:
        packet = _json_object(packet_path, label="materialize-ballot packet")

    readability_schema2 = (
        packet.get("kind") == PACKET_KIND
        and packet.get("schema_version") == READABILITY_SCHEMA_VERSION
    )
    professional_schema3 = (
        packet.get("kind") == PROFESSIONAL_COMPLETENESS_PACKET_KIND
        and packet.get("schema_version")
        == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    )
    semantic_schema2 = (
        packet.get("kind") == SEMANTIC_DISPOSITION_PACKET_KIND
        and packet.get("schema_version") == SEMANTIC_DISPOSITION_SCHEMA_VERSION
    )
    if not readability_schema2 and not professional_schema3 and not semantic_schema2:
        raise PanelReviewError(
            "materialize-ballot accepts only Readability schema 2, Professional Completeness schema 3, or Semantic Disposition schema 2"
        )
    if professional_schema3 and not schema3_layout:
        raise PanelReviewError(
            "schema-3 materialize-ballot requires the canonical packet layout"
    )
    if semantic_schema2:
        if not schema3_layout:
            raise PanelReviewError(
                "Semantic materialize-ballot requires the canonical transient packet layout"
            )
        semantic_layout = _semantic_runtime_layout(packet["review_id"])
        expected_packet = semantic_layout["packet"]
        _require_exact_materialization_path_argument(
            args.packet,
            expected_packet,
            label="Semantic packet",
        )
        bound_packet = reviewer_manifest.read_bound_regular_file(
            expected_packet,
            max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
            label="Semantic packet",
        )
        packet = _materialization_json_object(
            bound_packet.raw,
            label="Semantic packet",
        )
        packet_ref = {"sha256": bound_packet.sha256}
        if args.audit is None:
            raise PanelReviewError(
                "Semantic materialize-ballot requires --audit"
            )
        expected_audit = semantic_layout["audit"]
        _require_exact_materialization_path_argument(
            args.audit,
            expected_audit,
            label="Semantic audit",
        )
        bound_audit = reviewer_manifest.read_bound_regular_file(
            expected_audit,
            max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
            label="Semantic audit",
        )
        audit = _materialization_json_object(
            bound_audit.raw,
            label="Semantic audit",
        )
        validate_semantic_packet_current(packet, audit)
    elif args.audit is not None:
        raise PanelReviewError(
            "materialize-ballot --audit is accepted only for Semantic Disposition"
        )

    template_path = _cli_path(args.template)
    output_path = _cli_path(args.out)
    if semantic_schema2:
        suffix = ".template.json"
        if not template_path.name.endswith(suffix):
            raise PanelReviewError(
                "Semantic template filename must end with .template.json"
            )
        filename_voter_id = template_path.name[: -len(suffix)]
        if VOTER_ID_PATTERN.fullmatch(filename_voter_id) is None:
            raise PanelReviewError("Semantic template voter filename is invalid")
        reviewer_layout = _semantic_runtime_layout(
            packet["review_id"], voter_id=filename_voter_id
        )
        expected_template = reviewer_layout["template"]
        expected_output = reviewer_layout["ballot"]
        _require_exact_materialization_path_argument(
            args.template,
            expected_template,
            label="Semantic template",
        )
        _require_exact_materialization_path_argument(
            args.out,
            expected_output,
            label="Semantic output",
        )
        template_path = expected_template
        output_path = expected_output
    bound_template = reviewer_manifest.bind_regular_file(
        template_path,
        expected_sha256=args.template_sha256,
        max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
        outside_root=(
            ROOT
            if readability_schema2 and not _is_ephemeral_round_path(packet_path)
            else None
        ),
        label="ballot template",
    )
    template = _materialization_json_object(
        bound_template.raw,
        label="ballot template",
    )
    voter = template.get("voter")
    voter_id = voter.get("voter_id") if isinstance(voter, dict) else None
    if not isinstance(voter_id, str) or VOTER_ID_PATTERN.fullmatch(voter_id) is None:
        raise PanelReviewError("ballot template voter_id is invalid")

    if readability_schema2:
        expected_template_name = f"{voter_id}.template.json"
        expected_output_name = f"{voter_id}.json"
        if template_path.name != expected_template_name:
            raise PanelReviewError(
                f"schema-2 template must be named {expected_template_name}"
            )
        if (
            output_path.parent.absolute() != template_path.parent.absolute()
            or output_path.name != expected_output_name
            or output_path == template_path
        ):
            raise PanelReviewError(
                f"schema-2 output must be the distinct sibling {expected_output_name}"
            )
        if _is_ephemeral_round_path(packet_path):
            _require_same_ephemeral_run_path(
                template_path,
                review_id=packet["review_id"],
                label="schema-2 ballot template",
            )
            output_path = _require_same_ephemeral_run_path(
                output_path,
                review_id=packet["review_id"],
                label="schema-2 ballot output",
            )
        else:
            try:
                output_path.resolve(strict=False).relative_to(ROOT.resolve())
            except ValueError:
                pass
            else:
                raise PanelReviewError(
                    "legacy schema-2 output must stay outside the repository"
                )
        packet_sha256 = _sha256(packet_path)
    elif professional_schema3:
        if template_path.absolute() != output_path.absolute():
            raise PanelReviewError("schema-3 template and output paths must be identical")
        output_path = _require_schema3_cli_artifact_path(
            output_path,
            review_id=packet["review_id"],
            kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
            voter_id=voter_id,
        )
        if output_path.absolute() != bound_template.path.absolute():
            raise PanelReviewError("schema-3 bound template path is not canonical")
        if packet_ref is None:  # pragma: no cover - guarded by schema3_layout.
            raise PanelReviewError("schema-3 packet binding is missing")
        packet_sha256 = packet_ref["sha256"]
    else:
        if voter_id != filename_voter_id:
            raise PanelReviewError(
                "Semantic template filename must equal voter_id"
            )
        if packet_ref is None:  # pragma: no cover - established above.
            raise PanelReviewError("Semantic packet binding is missing")
        packet_sha256 = packet_ref["sha256"]

    validate_ballot_template(
        packet,
        template,
        packet_sha256=packet_sha256,
        validation_root=ROOT,
    )
    canonical_template = _canonical_materialization_template(
        packet,
        template,
        packet_sha256=packet_sha256,
    )
    canonical_template_raw = reviewer_manifest.canonical_ballot_bytes(
        canonical_template,
        compact=False,
    )
    if bound_template.raw != canonical_template_raw:
        raise PanelReviewError(
            "ballot template bytes are not the canonical pretty JSON serialization"
        )

    if args.manifest == "-":
        if args.stdin_framing == "raw":
            manifest_raw = reviewer_manifest.read_raw_manifest_stream(
                sys.stdin.buffer,
                expected_size=args.manifest_size,
                expected_sha256=args.manifest_sha256,
            )
        else:
            manifest_raw = reviewer_manifest.read_framed_manifest_stream(
                sys.stdin.buffer,
                expected_size=args.manifest_size,
                expected_sha256=args.manifest_sha256,
            )
    else:
        if args.stdin_framing != "raw":
            raise PanelReviewError(
                "framed manifest transport is accepted only with --manifest -"
            )
        manifest_raw = reviewer_manifest.read_manifest_file(
            Path(args.manifest),
            expected_size=args.manifest_size,
            expected_sha256=args.manifest_sha256,
            repository_root=ROOT,
        )
    records = reviewer_manifest.parse_manifest_bytes(manifest_raw)
    if records[0].get("template_sha256") != bound_template.sha256:
        raise PanelReviewError(
            "reviewer manifest template_sha256 does not bind the exact template bytes"
        )
    candidate = reviewer_manifest.materialize_manifest(template, records)

    def validate_candidate(value: dict[str, Any]) -> object:
        return validate_ballot(
            packet,
            value,
            packet_sha256=packet_sha256,
            validation_root=ROOT,
            artifact_path=(output_path if professional_schema3 else None),
        )

    validate_candidate(candidate)
    final_bytes = reviewer_manifest.canonical_ballot_bytes(
        candidate,
        compact=professional_schema3,
    )
    if readability_schema2 or semantic_schema2:
        reviewer_manifest.create_ballot_once(
            bound_template,
            output_path,
            final_bytes,
            validate_final=validate_candidate,
        )
    else:
        reviewer_manifest.replace_bound_ballot_once(
            bound_template,
            final_bytes,
            validate_final=validate_candidate,
        )
    return output_path, candidate


def _bound_json_object(path: Path, *, label: str, max_bytes: int) -> tuple[
    reviewer_manifest.BoundFile, dict[str, Any]
]:
    bound = reviewer_manifest.read_bound_regular_file(
        path, max_bytes=max_bytes, label=label
    )
    try:
        value = json.loads(bound.raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PanelReviewError(f"{label} is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PanelReviewError(f"{label} must be a JSON object: {path}")
    return bound, value


def _attestation_reviewers(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            key: copy.deepcopy(voter[key])
            for key in (
                "voter_id",
                "agent_id",
                "role",
                "expertise",
                "independent_review",
            )
        }
        for voter in record["voters"]
    ]


def _decision_packet_and_ballots(
    record: dict[str, Any], *, decision_path: Path
) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    packet_ref = record.get("packet")
    if not isinstance(packet_ref, dict) or set(packet_ref) < {"path", "sha256"}:
        raise PanelReviewError("attestation decision packet reference is invalid")
    packet_path = _canonical_artifact_path(
        packet_ref["path"],
        validation_root=ROOT,
        label="attestation packet",
    )
    bound_packet, packet = _bound_json_object(
        packet_path,
        label="attestation packet",
        max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
    )
    if bound_packet.sha256 != packet_ref["sha256"]:
        raise PanelReviewError("attestation packet digest is stale")
    ballots: list[dict[str, Any]] = []
    for voter in record.get("voters", []):
        if "ballot" in voter:
            ballot_reference = voter.get("ballot")
            if not isinstance(ballot_reference, dict):
                raise PanelReviewError("attestation ballot reference is invalid")
            ballot_path = _canonical_artifact_path(
                ballot_reference.get("path"),
                validation_root=ROOT,
                label="attestation ballot",
            )
            expected_ballot_sha = ballot_reference.get("sha256")
        else:
            ballot_name = voter.get("ballot_path")
            if (
                not isinstance(ballot_name, str)
                or Path(ballot_name).name != ballot_name
            ):
                raise PanelReviewError("attestation ballot filename is invalid")
            ballot_path = decision_path.parent / ballot_name
            expected_ballot_sha = voter.get("ballot_sha256")
        bound_ballot, ballot = _bound_json_object(
            ballot_path,
            label="attestation ballot",
            max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
        )
        if bound_ballot.sha256 != expected_ballot_sha:
            raise PanelReviewError("attestation ballot digest is stale")
        ballots.append(ballot)
    return packet_path, packet, ballots


def _readability_attestation_from_decision(
    record: dict[str, Any],
    *,
    decision_path: Path,
    audit: dict[str, Any],
) -> dict[str, Any]:
    validate_decision_record(record, record_path=decision_path)
    packet_path, packet, ballots = _decision_packet_and_ballots(
        record, decision_path=decision_path
    )
    current = prepare_packet(
        audit=audit,
        review_id=packet["review_id"],
        created_on=packet["created_on"],
    )
    for field in ("source_fingerprints", "panel_contract"):
        if packet.get(field) != current.get(field):
            raise PanelReviewError(
                f"readability decision {field} is incomplete or stale"
            )
    if _readability_target_manifest_projection(
        content_targets=packet["content_targets"],
        readability_targets=packet["readability_targets"],
        actionability_targets=packet["actionability_targets"],
    ) != _readability_target_manifest_projection(
        content_targets=current["content_targets"],
        readability_targets=current["readability_targets"],
        actionability_targets=current["actionability_targets"],
    ):
        raise PanelReviewError(
            "readability decision normalized target bindings are incomplete or stale"
        )
    voter_ids = [reviewer["voter_id"] for reviewer in record["voters"]]
    ballot_by_voter = {
        ballot["voter"]["voter_id"]: ballot for ballot in ballots
    }
    if set(ballot_by_voter) != set(voter_ids):
        raise PanelReviewError("readability ballot coverage is stale")
    current_bindings = _readability_target_authorities(packet)
    content_votes = {
        voter_id: {
            row["path"]: row
            for row in ballot_by_voter[voter_id]["content_votes"]
        }
        for voter_id in voter_ids
    }
    finding_votes = {
        voter_id: {
            (document["document_id"], row["finding_id"]): row
            for document in ballot_by_voter[voter_id]["readability_votes"]
            for row in document["finding_reviews"]
        }
        for voter_id in voter_ids
    }
    action_votes = {
        voter_id: {
            row["target_id"]: row
            for row in ballot_by_voter[voter_id]["actionability_votes"]
        }
        for voter_id in voter_ids
    }
    findings: list[dict[str, Any]] = []
    for target in packet["content_targets"]:
        authority = current_bindings["content"][target["path"]]
        findings.append(
            {
                "category": "content",
                "target_id": target["path"],
                "source_fingerprint": authority["source_fingerprint"],
                "review_binding_fingerprint": authority[
                    "review_binding_fingerprint"
                ],
                "votes": [
                    {
                        "voter_id": voter_id,
                        "disposition": content_votes[voter_id][target["path"]][
                            "decision"
                        ],
                        "reason_code": content_votes[voter_id][target["path"]][
                            "reason_code"
                        ],
                        "rationale": content_votes[voter_id][target["path"]][
                            "rationale"
                        ],
                    }
                    for voter_id in voter_ids
                ],
                "result": {},
            }
        )
    for target in packet["readability_targets"]:
        authority = current_bindings["readability"][target["document_id"]]
        findings.append(
            {
                "category": "readability",
                "target_id": target["document_id"],
                "source_fingerprint": authority["source_fingerprint"],
                "review_binding_fingerprint": authority[
                    "review_binding_fingerprint"
                ],
                "finding_reviews": [
                    {
                        "finding_id": finding["finding_id"],
                        "source_fingerprint": authority["findings"][
                            finding["finding_id"]
                        ]["source_fingerprint"],
                        "review_binding_fingerprint": authority["findings"][
                            finding["finding_id"]
                        ]["review_binding_fingerprint"],
                        "votes": [
                            {
                                "voter_id": voter_id,
                                "disposition": finding_votes[voter_id][
                                    (target["document_id"], finding["finding_id"])
                                ]["decision"],
                                "reason_code": finding_votes[voter_id][
                                    (target["document_id"], finding["finding_id"])
                                ]["reason_code"],
                                "rationale": finding_votes[voter_id][
                                    (target["document_id"], finding["finding_id"])
                                ]["rationale"],
                            }
                            for voter_id in voter_ids
                        ],
                        "result": {},
                    }
                    for finding in sorted(
                        target["findings"], key=lambda row: row["finding_id"]
                    )
                ],
                "result": {},
            }
        )
    for target in packet["actionability_targets"]:
        authority = current_bindings["actionability"][target["target_id"]]
        findings.append(
            {
                "category": "actionability",
                "target_id": target["target_id"],
                "source_fingerprint": authority["source_fingerprint"],
                "review_binding_fingerprint": authority[
                    "review_binding_fingerprint"
                ],
                "votes": [
                    {
                        "voter_id": voter_id,
                        "disposition": action_votes[voter_id][target["target_id"]][
                            "decision"
                        ],
                        "reason_code": action_votes[voter_id][target["target_id"]][
                            "reason_code"
                        ],
                        "rationale": action_votes[voter_id][target["target_id"]][
                            "rationale"
                        ],
                    }
                    for voter_id in voter_ids
                ],
                "result": {},
            }
        )
    value = {
        "schema_version": panel_attestation.ATTESTATION_SCHEMA_VERSION,
        "kind": panel_attestation.READABILITY_ATTESTATION_KIND,
        "axis": panel_attestation.READABILITY_AXIS,
        "review_id": record["review_id"],
        "decided_on": record["decided_on"],
        "source_fingerprints": copy.deepcopy(record["source_fingerprints"]),
        "review_contract_fingerprint": _canonical_json_sha256(
            packet["panel_contract"]
        ),
        "review_artifacts": {
            "decision": {"sha256": _sha256(decision_path)},
            "packet": {"sha256": record["packet"]["sha256"]},
            "ballots": [
                {
                    "voter_id": voter["voter_id"],
                    "sha256": voter["ballot_sha256"],
                }
                for voter in sorted(
                    record["voters"], key=lambda row: row["voter_id"]
                )
            ],
        },
        "reviewers": _attestation_reviewers(record),
        "findings": findings,
        "summary": {},
        "verdict": "",
        "rationale": [
            "Every current target received three independent decisions and a derived majority."
        ],
    }
    finalized = panel_attestation.finalize_attestation(
        value,
        expected_path=panel_attestation.READABILITY_ATTESTATION_PATH,
        expected_readability_current_bindings=current_bindings,
    )
    if finalized["verdict"] != "accepted-current-readability":
        raise PanelReviewError("readability attestation is not release-complete")
    return finalized


def _readability_target_authorities(
    packet: dict[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Bind compact Readability rows to the complete current schema-2 packet."""

    result: dict[str, dict[str, dict[str, Any]]] = {
        "content": {}, "readability": {}, "actionability": {},
    }
    for category, field in (
        ("content", "content_targets"),
        ("readability", "readability_targets"),
        ("actionability", "actionability_targets"),
    ):
        targets = packet.get(field)
        if not isinstance(targets, list):
            raise PanelReviewError(
                f"readability authority packet {field} is invalid"
            )
        for target in targets:
            try:
                authority = panel_attestation.readability_target_authority(
                    category=category, target=target
                )
            except panel_attestation.AttestationError as exc:
                raise PanelReviewError(
                    f"readability authority packet {field} is invalid"
                ) from exc
            target_id = authority["target_id"]
            if target_id in result[category]:
                raise PanelReviewError(
                    f"readability authority packet {field} is duplicated"
                )
            result[category][target_id] = authority
    return result


def _semantic_candidate_authorities(
    packet: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        target["target_id"]: panel_attestation.semantic_candidate_authority(
            axis=target["axis"], candidate=target["candidate"]
        )
        for target in packet["semantic_targets"]
    }


def _semantic_attestation_from_decision(
    record: dict[str, Any],
    *,
    decision_path: Path,
    audit: dict[str, Any],
) -> dict[str, Any]:
    validate_decision_record(record, record_path=decision_path)
    _packet_path, packet, _ballots = _decision_packet_and_ballots(
        record, decision_path=decision_path
    )
    validate_semantic_packet_current(packet, audit)
    target_by_id = {row["target_id"]: row for row in packet["semantic_targets"]}
    if set(target_by_id) != {
        row["target_id"] for row in record["semantic_decisions"]
    }:
        raise PanelReviewError("semantic decision coverage is incomplete")
    current_bindings = _semantic_candidate_authorities(packet)
    findings = []
    for decision in record["semantic_decisions"]:
        target = target_by_id[decision["target_id"]]
        authority = current_bindings[target["target_id"]]
        if decision["candidate_binding_fingerprint"] != authority[
            "candidate_binding_fingerprint"
        ]:
            raise PanelReviewError("semantic decision candidate binding is stale")
        findings.append(
            {
                "target_id": target["target_id"],
                "axis": target["axis"],
                "candidate_binding_fingerprint": decision[
                    "candidate_binding_fingerprint"
                ],
                "votes": copy.deepcopy(decision["ballot_rationales"]),
                "result": {},
            }
        )
    findings.sort(key=lambda row: row["target_id"])
    value = {
        "schema_version": panel_attestation.ATTESTATION_SCHEMA_VERSION,
        "kind": panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND,
        "axis": panel_attestation.SEMANTIC_DISPOSITION_AXIS,
        "review_id": record["review_id"],
        "decided_on": record["decided_on"],
        "source_fingerprints": copy.deepcopy(record["source_fingerprints"]),
        "review_contract_fingerprint": _canonical_json_sha256(
            packet["panel_contract"]
        ),
        "reviewers": _attestation_reviewers(record),
        "findings": findings,
        "summary": {},
        "verdict": "",
        "rationale": [
            "Every current semantic candidate received three independent decisions and a majority."
        ],
    }
    return panel_attestation.finalize_attestation(
        value,
        expected_path=panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH,
        expected_semantic_current_bindings=current_bindings,
    )


@lru_cache(maxsize=1)
def _load_professional_regression_validator() -> ModuleType:
    module_name = f"{__name__}_professional_regression_validator"
    existing = sys.modules.get(module_name)
    if isinstance(existing, ModuleType):
        return existing
    source = Path(__file__).resolve().with_name(
        "validate-professionalism-regression.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise PanelReviewError(
            f"cannot load Professional regression validator: {source}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _compact_professional_reviewer(voter: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(voter[key])
        for key in (
            "voter_id",
            "agent_id",
            "role",
            "expertise",
            "independent_review",
            "expertise_tags",
            "qualification_claims",
        )
    }


def _compact_professional_vote_v2(
    assignment: dict[str, Any], *, skill_id: str
) -> dict[str, Any]:
    """Project a fully validated schema-3 vote without source context."""

    full_vote = copy.deepcopy(assignment["vote"])
    if full_vote.get("skill_id") != skill_id:
        raise PanelReviewError("professional compact vote target is stale")
    scoped = _professional_v3_target_scoped_capsule_materials(
        assignment["capsule"]
    )
    materials = scoped.get(skill_id)
    if materials is None:
        raise PanelReviewError("professional compact capsule target is stale")
    _validate_professional_v3_semantic_grounding(
        full_vote,
        materials_by_skill=materials,
        label=f"Professional compact projection {skill_id}",
    )
    voter = assignment["voter"]
    voter_id = voter["voter_id"]
    is_architecture = voter["expertise_tags"] == [
        PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
    ]
    failures = full_vote["examined_failure_modes"]
    omissions = full_vote["examined_omission_candidates"]
    adjacency = full_vote["examined_adjacent_candidates"]
    proof_limits = full_vote["proof_limits"]
    compact = {
        "reviewer": voter_id,
        "decision": full_vote["decision"],
        "reason_code": full_vote["reason_code"],
        "review_evidence_fingerprint": (
            panel_attestation.professional_compact_vote_fingerprint(
                {"voter": voter, "vote": full_vote}
            )
        ),
        "criteria": {
            "ordinary": {
                criterion: full_vote["criteria"][criterion]["status"]
                for criterion in sorted(PROFESSIONAL_ORDINARY_CRITERIA)
            },
            "domain_critical_defects": (
                []
                if is_architecture
                else sorted(
                    criterion
                    for criterion in PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
                    if full_vote["criteria"][criterion]["status"]
                    == "defect-found"
                )
            ),
        },
        "examined_failure_modes": {
            "count": len(failures),
            "defect_count": sum(
                item["outcome"] == "defect-found" for item in failures
            ),
            "digest": _canonical_json_sha256(failures),
        },
        "examined_omission_candidates": {
            "count": len(omissions),
            "defect_count": sum(
                item["outcome"] == "defect-found" for item in omissions
            ),
            "digest": _canonical_json_sha256(omissions),
        },
        "examined_adjacent_candidates": {
            "count": len(adjacency),
            "required_count": sum(
                item["review_origin"] == "packet-required"
                for item in adjacency
            ),
            "reviewer_added_candidate_ids": sorted(
                item["skill_id"]
                for item in adjacency
                if item["review_origin"] == "reviewer-added"
            ),
            "defect_count": sum(
                item["disposition"] == "gap-or-overlap-defect"
                for item in adjacency
            ),
            "digest": _canonical_json_sha256(adjacency),
        },
        "proof_limits": {
            "count": len(proof_limits),
            "digest": _canonical_json_sha256(proof_limits),
            "bounded": [
                item[
                    : panel_contracts.PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_MAXIMUM
                ].rstrip()
                for item in proof_limits[
                    : panel_contracts.PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_COUNT
                ]
            ],
        },
        "rationale": full_vote["rationale"][
            : panel_contracts.PROFESSIONAL_COMPACT_RATIONALE_MAXIMUM
        ].rstrip(),
    }
    return compact


def _professional_authenticated_claims_from_findings(
    findings: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Extract claims only after the caller authenticates their owning input."""

    if not isinstance(findings, list) or not findings:
        raise PanelReviewError("Professional authenticated findings are invalid")
    claims: dict[str, dict[str, Any]] = {}
    for row in findings:
        if not isinstance(row, dict) or not isinstance(row.get("skill_id"), str):
            raise PanelReviewError("Professional authenticated finding is invalid")
        votes = row.get("votes")
        result = row.get("result")
        provenance = row.get("provenance")
        if (
            not isinstance(votes, list)
            or len(votes) != panel_contracts.PROFESSIONAL_PANEL_SIZE
            or any(
                not isinstance(vote, dict)
                or not isinstance(vote.get("reviewer"), str)
                for vote in votes
            )
            or not isinstance(result, dict)
            or not isinstance(result.get("qualification_coverage"), dict)
            or not isinstance(result.get("evidence_metrics"), dict)
            or not isinstance(result.get("review_dependencies"), dict)
            or not isinstance(
                result["review_dependencies"].get(
                    "reviewer_added_candidate_ids_union"
                ),
                list,
            )
            or not isinstance(provenance, dict)
            or not isinstance(provenance.get("origin"), dict)
        ):
            raise PanelReviewError(
                "Professional authenticated compact claims are invalid"
            )
        voter_ids = [vote["reviewer"] for vote in votes]
        if voter_ids != sorted(set(voter_ids)):
            raise PanelReviewError(
                "Professional authenticated compact voters are invalid"
            )
        skill_id = row["skill_id"]
        if skill_id in claims:
            raise PanelReviewError(
                "Professional authenticated finding identities are duplicated"
            )
        claims[skill_id] = {
            "vote_authorities": {
                vote["reviewer"]: copy.deepcopy(vote)
                for vote in votes
            },
            "reviewer_partition": {
                "domain_voters": copy.deepcopy(
                    row["result"]["qualification_coverage"]["domain_voters"]
                ),
                "architecture_voter": row["result"][
                    "qualification_coverage"
                ]["architecture_voter"],
            },
            "evidence_metrics": copy.deepcopy(
                row["result"]["evidence_metrics"]
            ),
            "reviewer_added_candidate_ids_union": copy.deepcopy(
                row["result"]["review_dependencies"][
                    "reviewer_added_candidate_ids_union"
                ]
            ),
            "origin": copy.deepcopy(row["provenance"]["origin"]),
        }
    return claims


def _professional_attestation_bindings_from_state(
    *,
    current_bindings: dict[str, dict[str, Any]],
    authenticated_claims: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    try:
        return professional_carry.professional_current_authority(
            current_bindings,
            authenticated_claims=authenticated_claims,
        )
    except (
        professional_carry
        .ProfessionalReviewerAddedRequiredRelationshipDrift
    ) as exc:
        skill_id, candidate_ids = exc.overlaps[0]
        raise ProfessionalReviewerAddedRequiredPromotionDrift(
            skill_id,
            candidate_ids,
            overlaps=dict(exc.overlaps),
        ) from exc
    except professional_carry.ProfessionalCarryForwardError as exc:
        raise PanelReviewError(
            "Professional current authority is invalid"
        ) from exc


def _professional_attestation_current_bindings(
    current_packet: dict[str, Any],
    *,
    authenticated_claims: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    bindings = professional_carry.professional_review_bindings(
        current_packet["professional_targets"]
    )
    return _professional_attestation_bindings_from_state(
        current_bindings=bindings,
        authenticated_claims=authenticated_claims,
    )


def validate_professional_attestation_current(
    value: dict[str, Any], *, current_packet: dict[str, Any],
    authenticated_claims: dict[str, dict[str, Any]],
    validation_root: Path | None = None,
    expected_skill_ids: set[str] | None = None,
) -> None:
    """Rebind compact Professional conclusions to complete current authority."""

    authorities = _professional_attestation_current_bindings(
        current_packet, authenticated_claims=authenticated_claims
    )
    expected = set(authorities) if expected_skill_ids is None else expected_skill_ids
    if not expected <= set(authorities):
        raise PanelReviewError(
            "Professional attestation target coverage is stale"
        )
    scoped_authorities = {
        skill_id: authorities[skill_id] for skill_id in sorted(expected)
    }

    try:
        panel_attestation.validate_attestation(
            value,
            expected_professional_current_bindings=scoped_authorities,
            expected_review_contract_fingerprint=current_packet.get(
                "review_contract_fingerprint",
                value["review_contract_fingerprint"],
            ),
        )
    except panel_attestation.AttestationError as exc:
        raise PanelReviewError(
            "Professional attestation exact current binding is stale"
        ) from exc

    targets = {
        target["skill_id"]: target
        for target in current_packet["professional_targets"]
    }
    findings = {row["skill_id"]: row for row in value["findings"]}
    if (
        not expected <= set(targets)
        or len(findings) != len(value["findings"])
        or set(findings) != expected
    ):
        raise PanelReviewError(
            "Professional attestation target coverage is stale"
        )


def _professional_attestation_projection_from_decision(
    record: dict[str, Any], *, decision_path: Path
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    cache = _professional_v3_invocation_cache()
    validate_decision_record(
        record,
        record_path=decision_path,
        validation_root=ROOT,
    )
    packet_path, packet, _ballots = _decision_packet_and_ballots(
        record, decision_path=decision_path
    )
    if (
        record.get("kind") != PROFESSIONAL_COMPLETENESS_DECISION_KIND
        or record.get("schema_version")
        != PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
    ):
        raise PanelReviewError(
            "professional attestation requires a schema-3 decision"
        )
    state = _professional_v3_packet_state(
        packet,
        validation_root=ROOT,
        artifact_path=packet_path,
        validate_baseline=True,
        invocation_cache=cache,
    )
    head_commit = _git_output("rev-parse", "--verify", "HEAD").stdout.decode(
        "ascii"
    ).strip()
    if re.fullmatch(r"[0-9a-f]{40}", head_commit) is None:
        raise PanelReviewError("professional attestation origin commit is invalid")
    targets = {
        row["skill_id"]: row for row in packet["professional_targets"]
    }
    findings = []
    dependency_material_catalog: dict[str, str] = {}
    authenticated_claims: dict[str, dict[str, Any]] = {}
    for row in record["professional_decisions"]:
        skill_id = row["skill_id"]
        provenance = row["provenance"]
        origin_reference = (
            _professional_artifact_reference(
                decision_path,
                validation_root=ROOT,
                kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                review_id=record["review_id"],
            )
            if provenance["mode"] == "fresh"
            else provenance["origin_decision"]
        )
        expected_fingerprint = (
            row["target_decision_fingerprint"]
            if provenance["mode"] == "fresh"
            else provenance["origin_target_decision_fingerprint"]
        )
        if (
            provenance["mode"] != "fresh"
            and isinstance(origin_reference, dict)
            and origin_reference.get("kind")
            == panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND
        ):
            baseline_state = state.get("baseline_state")
            origin_state = (
                baseline_state.get("origins", {}).get(skill_id)
                if isinstance(baseline_state, dict)
                else None
            )
            if (
                not isinstance(origin_state, dict)
                or origin_state.get("origin_verdict_digest")
                != expected_fingerprint
            ):
                raise PanelReviewError(
                    f"professional attested origin is stale: {skill_id}"
                )
            origin_finding = origin_state["finding"]
            carried = copy.deepcopy(origin_finding)
            carried["provenance"]["mode"] = "carried"
            authenticated_claims[skill_id] = (
                _professional_authenticated_claims_from_findings(
                    [origin_finding]
                )[skill_id]
            )
            carried["result"] = {}
            for dependency_id in carried["dependency_ids"]:
                material_binding = state["bindings"][dependency_id][
                    "package_material_binding"
                ]
                existing = dependency_material_catalog.get(dependency_id)
                if existing is not None and existing != material_binding:
                    raise PanelReviewError(
                        "professional dependency catalog is inconsistent"
                    )
                dependency_material_catalog[dependency_id] = material_binding
            findings.append(carried)
            continue
        origin = _load_professional_v3_fresh_origin_target(
            origin_reference=origin_reference,
            skill_id=skill_id,
            expected_target_decision_fingerprint=expected_fingerprint,
            validation_root=ROOT,
            forbidden_paths=set(),
            invocation_cache=cache,
        )
        origin_row = origin["target_row"]
        origin_target = origin["target"]
        current_binding = state["bindings"][skill_id]
        target_material_fingerprint = current_binding[
            "package_material_binding"
        ]
        dependency_ids = origin_row["review_dependencies"][
            "dependency_candidate_ids"
        ]
        dependency_materials = {
            candidate_id: state["bindings"][candidate_id][
                "package_material_binding"
            ]
            for candidate_id in dependency_ids
        }
        compact_origin = {
            "origin_review_id": origin["decision"]["review_id"],
            "origin_commit": head_commit,
            "origin_verdict_digest": expected_fingerprint,
        }
        compact_votes = [
            _compact_professional_vote_v2(
                assignment, skill_id=skill_id
            )
            for assignment in origin["assignments"]
        ]
        domain_voters = sorted(
            assignment["voter"]["voter_id"]
            for assignment in origin["assignments"]
            if assignment["voter"]["expertise_tags"]
            != [PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG]
        )
        architecture_voters = [
            assignment["voter"]["voter_id"]
            for assignment in origin["assignments"]
            if assignment["voter"]["expertise_tags"]
            == [PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG]
        ]
        if (
            len(domain_voters)
            != panel_contracts.PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS
            or len(architecture_voters)
            != panel_contracts.PROFESSIONAL_REQUIRED_ARCHITECTURE_EXPERTS
        ):
            raise PanelReviewError(
                f"professional compact reviewer partition is stale: {skill_id}"
            )
        authenticated_claims[skill_id] = {
            "vote_authorities": {
                vote["reviewer"]: copy.deepcopy(vote)
                for vote in compact_votes
            },
            "reviewer_partition": {
                "domain_voters": domain_voters,
                "architecture_voter": architecture_voters[0],
            },
            "evidence_metrics": copy.deepcopy(
                origin_row["evidence_metrics"]
            ),
            "reviewer_added_candidate_ids_union": copy.deepcopy(
                origin_row["review_dependencies"][
                    "reviewer_added_candidate_ids_union"
                ]
            ),
            "origin": copy.deepcopy(compact_origin),
        }
        for candidate_id, material_binding in dependency_materials.items():
            existing = dependency_material_catalog.get(candidate_id)
            if existing is not None and existing != material_binding:
                raise PanelReviewError(
                    "professional dependency catalog is inconsistent"
                )
            dependency_material_catalog[candidate_id] = material_binding
        findings.append(
            {
                "skill_id": skill_id,
                "package_material_binding": target_material_fingerprint,
                "review_unit_binding": row["review_unit_binding"],
                "dependency_ids": sorted(dependency_materials),
                "required_expertise_tags": copy.deepcopy(
                    origin_target["required_expertise_tags"]
                ),
                "provenance": {
                    "mode": (
                        "fresh" if provenance["mode"] == "fresh" else "carried"
                    ),
                    "origin": compact_origin,
                },
                "votes": compact_votes,
                "result": {},
            }
        )
    try:
        cost = _load_professional_regression_validator()._professional_schema3_review_cost(
            record,
            packet=packet,
        )
    except ValueError as exc:
        raise PanelReviewError(
            f"professional attestation review cost is invalid: {exc}"
        ) from exc
    cost_input = {
        key: copy.deepcopy(cost[key])
        for key in panel_attestation.PROFESSIONAL_REVIEW_COST_INPUT_FIELDS
    }
    value = {
        "schema_version": panel_attestation.ATTESTATION_SCHEMA_VERSION,
        "kind": panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND,
        "axis": panel_attestation.PROFESSIONAL_COMPLETENESS_AXIS,
        "review_id": record["review_id"],
        "decided_on": record["decided_on"],
        "review_contract_fingerprint": record[
            "review_contract_fingerprint"
        ],
        "dependency_material_catalog": dict(
            sorted(dependency_material_catalog.items())
        ),
        "reviewers": [
            _compact_professional_reviewer(voter)
            for voter in record["voters"]
        ],
        "findings": findings,
        "review_cost_input": cost_input,
        "summary": {},
        "verdict": "",
        "rationale": [
            "Every current package has complete effective evidence and a derived formal disposition."
        ],
    }
    finalized = panel_attestation.finalize_attestation(
        value,
        expected_path=(
            panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
        ),
        expected_professional_current_bindings=(
            _professional_attestation_current_bindings(
                packet, authenticated_claims=authenticated_claims
            )
        ),
    )
    if finalized["verdict"] != (
        "accepted-current-professional-completeness"
    ):
        raise PanelReviewError(
            "professional attestation is not release-complete"
        )
    return finalized, authenticated_claims


def _professional_attestation_from_decision(
    record: dict[str, Any], *, decision_path: Path
) -> dict[str, Any]:
    """Return the compact projection while keeping authority out-of-band."""

    return _professional_attestation_projection_from_decision(
        record, decision_path=decision_path
    )[0]


def _attest(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    decision_path = _require_same_ephemeral_run_path(
        _cli_path(args.decision),
        review_id=args.review_id,
        label="attestation decision",
    )
    expected_decision = _ephemeral_review_path(
        args.review_id, "panel", "decision.json"
    )
    if decision_path.absolute() != expected_decision.resolve(strict=False):
        raise PanelReviewError(
            "attestation decision must use the canonical transient panel path"
        )
    _bound_decision, record = _bound_json_object(
        decision_path,
        label="attestation decision",
        max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
    )
    if record.get("review_id") != args.review_id:
        raise PanelReviewError("attestation decision review_id is stale")
    readability_current_bindings = None
    semantic_current_bindings = None
    professional_current_bindings = None
    professional_projection_head = None
    if args.panel_kind == READABILITY_PANEL_KIND:
        if not args.audit:
            raise PanelReviewError("readability attestation requires --audit")
        value = _readability_attestation_from_decision(
            record,
            decision_path=decision_path,
            audit=_json_object(_cli_path(args.audit), label="content audit"),
        )
        _packet_path, readability_packet, _ballots = (
            _decision_packet_and_ballots(record, decision_path=decision_path)
        )
        readability_current_bindings = _readability_target_authorities(
            readability_packet
        )
    elif args.panel_kind == SEMANTIC_DISPOSITION_PANEL_KIND:
        if not args.audit:
            raise PanelReviewError("semantic attestation requires --audit")
        value = _semantic_attestation_from_decision(
            record,
            decision_path=decision_path,
            audit=_json_object(_cli_path(args.audit), label="content audit"),
        )
        _packet_path, semantic_packet, _ballots = _decision_packet_and_ballots(
            record, decision_path=decision_path
        )
        semantic_current_bindings = _semantic_candidate_authorities(
            semantic_packet
        )
    else:
        if args.audit:
            raise PanelReviewError("professional attestation rejects --audit")
        professional_projection_head = (
            _professional_attestation_clean_stable_head()
        )
        value, professional_claims = (
            _professional_attestation_projection_from_decision(
            record, decision_path=decision_path
            )
        )
        _packet_path, professional_packet, _ballots = (
            _decision_packet_and_ballots(record, decision_path=decision_path)
        )
        professional_current_bindings = (
            _professional_attestation_current_bindings(
                professional_packet,
                authenticated_claims=professional_claims,
            )
        )
    output = _require_same_ephemeral_run_path(
        _cli_path(args.out),
        review_id=args.review_id,
        label="attestation output",
    )
    expected_output = _ephemeral_review_path(args.review_id, "attestation.json")
    if output.absolute() != expected_output.resolve(strict=False):
        raise PanelReviewError(
            "attestation output must use the canonical transient run path"
        )
    payload = panel_attestation.canonical_attestation_bytes(
        value,
        expected_path=panel_attestation.ATTESTATION_PATHS[args.panel_kind],
        expected_readability_current_bindings=readability_current_bindings,
        expected_semantic_current_bindings=semantic_current_bindings,
        expected_professional_current_bindings=professional_current_bindings,
    )
    if professional_projection_head is not None:
        confirmed_head = _professional_attestation_clean_stable_head()
        if confirmed_head != professional_projection_head:
            raise PanelReviewError(
                "professional attestation HEAD changed after projection"
            )
        fresh_origin_commits = {
            row["provenance"]["origin"]["origin_commit"]
            for row in value["findings"]
            if row["provenance"]["mode"] == "fresh"
        }
        if fresh_origin_commits and fresh_origin_commits != {
            professional_projection_head
        }:
            raise PanelReviewError(
                "professional attestation fresh origin commit is stale"
            )
    _write_json(
        output,
        json.loads(payload),
        compact=True,
        create_only=True,
        validation_root=ROOT,
    )
    bound_output = reviewer_manifest.read_bound_regular_file(
        output,
        expected_size=len(payload),
        max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
        label="attestation output",
    )
    if bound_output.raw != payload:
        raise PanelReviewError("attestation output bytes are not canonical")
    return output, value


def _validate_semantic_attestation_current(
    value: dict[str, Any], *, current_packet: dict[str, Any]
) -> None:
    expected = _semantic_candidate_authorities(current_packet)
    try:
        panel_attestation.validate_attestation(
            value,
            expected_semantic_current_bindings=expected,
        )
    except panel_attestation.AttestationError as exc:
        raise PanelReviewError(
            "semantic attestation exact current candidate coverage is stale"
        ) from exc
    for row in value["findings"]:
        if (
            len(row["votes"]) != PANEL_SIZE
            or len(row["result"]["supporting_voters"]) < 2
            or sum(row["result"]["vote_counts"].values()) != PANEL_SIZE
        ):
            raise PanelReviewError(
                "semantic attestation majority evidence is incomplete"
            )


def _semantic_attestation_selector_target_coverage(
    attestation_selector: dict[str, Any],
) -> frozenset[tuple[str, str]]:
    """Return only the untrusted target identities used to select authority."""

    findings = attestation_selector.get("findings")
    if not isinstance(findings, list) or not all(
        isinstance(finding, dict) for finding in findings
    ):
        raise PanelReviewError(
            "semantic attestation selector finding coverage is invalid"
        )
    identities: list[tuple[str, str]] = []
    for finding in findings:
        axis = finding.get("axis")
        target_id = finding.get("target_id")
        if (
            axis not in SEMANTIC_AXES
            or not isinstance(target_id, str)
            or re.fullmatch(rf"{axis}:[0-9a-f]{{64}}", target_id) is None
        ):
            raise PanelReviewError(
                "semantic attestation selector target identity is invalid"
            )
        identities.append((axis, target_id))
    coverage = frozenset(identities)
    if len(coverage) != len(identities):
        raise PanelReviewError(
            "semantic attestation selector target identities are duplicated"
        )
    return coverage


def _semantic_current_packet_for_attestation_selector(
    *,
    audit: dict[str, Any],
    review_id: str,
    decided_on: str,
    attestation_selector: dict[str, Any],
) -> dict[str, Any]:
    """Select one canonical ordinary or forced-axis Semantic authority."""

    if not isinstance(attestation_selector, dict):
        raise PanelReviewError("semantic attestation selector must be an object")
    selector_coverage = _semantic_attestation_selector_target_coverage(
        attestation_selector
    )
    matches: list[dict[str, Any]] = []
    for axes in ((), ("root",), ("reference",), ("root", "reference")):
        candidate_audit = _semantic_audit_for_axis_rereview(audit, list(axes))
        packet = prepare_semantic_disposition_packet(
            audit=candidate_audit,
            review_id=review_id,
            created_on=decided_on,
        )
        validate_semantic_packet_current(packet, audit)
        packet_coverage = frozenset(
            (target["axis"], target["target_id"])
            for target in packet["semantic_targets"]
        )
        review_contract_fingerprint = _canonical_json_sha256(
            packet["panel_contract"]
        )
        axis_counts = {
            axis: packet["panel_contract"]["required_axis_target_counts"][axis]
            for axis in sorted(SEMANTIC_AXES)
        }
        source_mode = _semantic_source_fingerprint_selector_mode(
            selector_fingerprints=(
                attestation_selector.get("detector_contract_fingerprints")
                if attestation_selector.get("schema_version")
                == panel_attestation.ATTESTATION_SCHEMA_VERSION
                else attestation_selector.get("source_fingerprints")
            ),
            current_fingerprints=packet["source_fingerprints"],
            review_id=review_id,
            review_contract_fingerprint=review_contract_fingerprint,
            target_count=packet["panel_contract"]["required_target_count"],
            axis_counts=axis_counts,
        )
        if (
            source_mode is not None
            and attestation_selector.get("review_contract_fingerprint")
            == review_contract_fingerprint
            and selector_coverage == packet_coverage
        ):
            selected_packet = copy.deepcopy(packet)
            if source_mode == "compatibility":
                selected_packet["source_fingerprints"] = copy.deepcopy(
                    attestation_selector["source_fingerprints"]
                )
            matches.append(selected_packet)
    if len(matches) != 1:
        raise PanelReviewError(
            "semantic attestation selector must match exactly one current authority"
        )
    return matches[0]


def _semantic_fixed_current_validation(
    *,
    audit: dict[str, Any],
    attestation_selector: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], str]:
    """Resolve compact current authority, including reviewed removals.

    A removed rewrite target has no current source object to recompute. Its sole
    surviving authority is the candidate binding authenticated by the compact
    attestation's immutable majority evidence. Every current non-rewrite target
    still binds complete collector evidence, and exact coverage rejects any new
    or unrelated missing candidate.
    """

    if (
        not isinstance(attestation_selector, dict)
        or attestation_selector.get("schema_version")
        != panel_attestation.ATTESTATION_SCHEMA_VERSION
        or attestation_selector.get("axis")
        != SEMANTIC_DISPOSITION_PANEL_KIND
    ):
        raise PanelReviewError(
            "semantic fixed attestation selector is not compact schema 2"
        )
    findings = attestation_selector.get("findings")
    if not isinstance(findings, list) or not findings:
        raise PanelReviewError(
            "semantic fixed attestation findings are invalid"
        )
    root_semantic, reference_semantic = _semantic_audit_sections(audit)
    current_fingerprints = _semantic_source_fingerprints(
        audit,
        root_semantic=root_semantic,
        reference_semantic=reference_semantic,
    )
    detectors = attestation_selector.get("detector_contract_fingerprints")
    detector_keys = {
        "root_detector_contract", "reference_detector_contract"
    }
    if (
        not isinstance(detectors, dict)
        or set(detectors) != detector_keys
        or any(
            detectors[key] != current_fingerprints[key]
            for key in detector_keys
        )
    ):
        raise PanelReviewError(
            "semantic fixed detector contract is stale"
        )

    current_authorities: dict[str, dict[str, Any]] = {}
    current_candidates: dict[str, dict[str, Any]] = {}
    disposition_entries: dict[str, dict[str, Any]] = {}
    for axis, semantic in (
        ("root", root_semantic),
        ("reference", reference_semantic),
    ):
        candidates = semantic.get("candidates")
        if not isinstance(candidates, list):
            raise PanelReviewError(
                f"semantic current {axis} candidates are invalid"
            )
        for candidate in _semantic_eligible_candidates(
            axis=axis, semantic=semantic
        ):
            candidate_id = candidate.get("candidate_id")
            target_id = f"{axis}:{candidate_id}"
            if target_id in current_authorities:
                raise PanelReviewError(
                    "semantic current candidate identities are duplicated"
                )
            current_authorities[target_id] = (
                panel_attestation.semantic_candidate_authority(
                    axis=axis,
                    candidate=candidate,
                )
            )
            current_candidates[target_id] = candidate
        contract = semantic.get("disposition_contract")
        entries = contract.get("entries") if isinstance(contract, dict) else None
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise PanelReviewError(
                f"semantic current {axis} disposition entries are invalid"
            )
        for entry in entries:
            candidate_id = entry.get("candidate_id")
            target_id = f"{axis}:{candidate_id}"
            if target_id in disposition_entries:
                raise PanelReviewError(
                    "semantic current disposition entries are duplicated"
                )
            disposition_entries[target_id] = entry

    finding_ids: list[str] = []
    finding_axes = {axis: 0 for axis in SEMANTIC_AXES}
    missing_rewrite_authorities: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise PanelReviewError(
                f"semantic fixed finding[{index}] is invalid"
            )
        target_id = finding.get("target_id")
        axis = finding.get("axis")
        if (
            axis not in SEMANTIC_AXES
            or not isinstance(target_id, str)
            or re.fullmatch(rf"{axis}:[0-9a-f]{{64}}", target_id) is None
        ):
            raise PanelReviewError(
                "semantic fixed target identity is invalid"
            )
        finding_ids.append(target_id)
        finding_axes[axis] += 1
        votes = finding.get("votes")
        vote_counts: dict[str, int] = {}
        if isinstance(votes, list):
            for vote in votes:
                if isinstance(vote, dict) and isinstance(
                    vote.get("disposition"), str
                ):
                    disposition = vote["disposition"]
                    vote_counts[disposition] = vote_counts.get(disposition, 0) + 1
        winners = [
            disposition
            for disposition, count in vote_counts.items()
            if count >= 2
        ]
        if len(winners) != 1:
            raise PanelReviewError(
                "semantic fixed finding lacks one majority disposition"
            )
        winner = winners[0]
        if target_id in current_authorities:
            entry = disposition_entries.get(target_id)
            if winner == "rewrite":
                raise PanelReviewError(
                    "semantic fixed rewrite target remains current"
                )
            if entry is None or _semantic_entry_mismatches(
                axis=axis,
                candidate=current_candidates[target_id],
                entry=entry,
            ):
                raise PanelReviewError(
                    "semantic attestation application entries are stale"
                )
            if entry.get("disposition") != winner:
                raise PanelReviewError(
                    "semantic fixed attestation disposition mismatch"
                )
            continue
        binding = finding.get("candidate_binding_fingerprint")
        if winner != "rewrite" or not isinstance(binding, str):
            raise PanelReviewError(
                "semantic fixed missing target lacks a rewrite majority"
            )
        if target_id in disposition_entries:
            raise PanelReviewError(
                "semantic fixed rewrite target remains current"
            )
        missing_rewrite_authorities[target_id] = {
            "candidate_binding_fingerprint": binding,
            "reviewed_rewrite": True,
        }
    if finding_ids != sorted(set(finding_ids)):
        raise PanelReviewError(
            "semantic fixed target identities are not canonical"
        )
    if set(current_authorities) - set(finding_ids):
        raise PanelReviewError(
            "semantic fixed attestation omits a current candidate"
        )
    if set(disposition_entries) != set(current_authorities):
        raise PanelReviewError(
            "semantic attestation application entries are stale"
        )
    authorities = {**current_authorities, **missing_rewrite_authorities}
    if set(authorities) != set(finding_ids):
        raise PanelReviewError(
            "semantic fixed attestation coverage is incomplete"
        )
    contract_fingerprint = _canonical_json_sha256(
        _semantic_panel_contract(
            root_target_count=finding_axes["root"],
            reference_target_count=finding_axes["reference"],
        )
    )
    if attestation_selector.get(
        "review_contract_fingerprint"
    ) != contract_fingerprint:
        raise PanelReviewError(
            "semantic fixed review contract is stale"
        )
    return authorities, contract_fingerprint


def _current_attestation_validation(
    panel_kind: str,
    *,
    review_id: str,
    decided_on: str,
    attestation_selector: dict[str, Any],
    promotion_decision_path: Path | None = None,
    promotion_source_bytes: bytes | None = None,
) -> tuple[
    str,
    dict[str, Any],
    Callable[[dict[str, Any]], None],
]:
    if panel_kind == PROFESSIONAL_COMPLETENESS_PANEL_KIND:
        if promotion_decision_path is not None:
            if not isinstance(promotion_source_bytes, bytes):
                raise PanelReviewError(
                    "Professional promotion source bytes are required"
                )
            transient_decision = _ephemeral_review_path(
                review_id, "panel", "decision.json"
            )
            supplied_decision = (
                promotion_decision_path
                if promotion_decision_path.is_absolute()
                else ROOT / promotion_decision_path
            ).absolute()
            if supplied_decision != transient_decision.resolve(strict=False):
                raise PanelReviewError(
                    "Professional promotion decision authority is not canonical"
                )
            _bound_decision, decision_record = _bound_json_object(
                transient_decision,
                label="Professional promotion decision authority",
                max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
            )
            if decision_record.get("review_id") != review_id:
                raise PanelReviewError(
                    "Professional promotion decision review_id is stale"
                )
            generated, authenticated_claims = (
                _professional_attestation_projection_from_decision(
                decision_record, decision_path=transient_decision
                )
            )
        else:
            authenticated_claims = (
                _professional_authenticated_claims_from_findings(
                    attestation_selector.get("findings")
                )
            )
        targets = _professional_package_targets(root=ROOT)
        bindings, snapshot = _professional_v3_binding_state(
            targets,
            review_contract_fingerprint=(
                _professional_evidence_review_contract_fingerprint()
            ),
        )
        current_packet = {
            "review_id": review_id,
            "created_on": decided_on,
            "professional_targets": [
                {
                    **target,
                    "review_binding": snapshot["targets"][target["skill_id"]],
                }
                for target in targets
            ],
        }
        current_authority = _professional_attestation_bindings_from_state(
            current_bindings=bindings,
            authenticated_claims=authenticated_claims,
        )
        if promotion_decision_path is not None:
            generated_bytes = panel_attestation.canonical_attestation_bytes(
                generated,
                expected_path=(
                    panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
                ),
                expected_review_contract_fingerprint=(
                    _professional_evidence_review_contract_fingerprint()
                ),
                expected_professional_current_bindings=current_authority,
            )
            if generated_bytes != promotion_source_bytes:
                raise PanelReviewError(
                    "Professional promotion attestation does not match its decision projection"
                )

        return panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH, {
            "expected_review_contract_fingerprint": (
                _professional_evidence_review_contract_fingerprint()
            ),
            "expected_professional_current_bindings": current_authority,
        }, lambda _value: None
    audit = _json_object(
        ROOT / "reports" / "skill-content-audit.json",
        label="current content audit",
    )
    if panel_kind == SEMANTIC_DISPOSITION_PANEL_KIND:
        authorities, contract_fingerprint = (
            _semantic_fixed_current_validation(
                audit=audit,
                attestation_selector=attestation_selector,
            )
        )
        return panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_PATH, {
            "expected_review_contract_fingerprint": contract_fingerprint,
            "expected_semantic_current_bindings": authorities,
        }, lambda value: None
    generated_readability: dict[str, Any] | None = None
    if promotion_decision_path is not None:
        transient_decision = _ephemeral_review_path(
            review_id, "panel", "decision.json"
        )
        supplied_decision = (
            promotion_decision_path
            if promotion_decision_path.is_absolute()
            else ROOT / promotion_decision_path
        ).absolute()
        if supplied_decision != transient_decision.resolve(strict=False):
            raise PanelReviewError(
                "Readability promotion decision authority is not canonical"
            )
        _bound_decision, decision_record = _bound_json_object(
            transient_decision,
            label="Readability promotion decision authority",
            max_bytes=reviewer_manifest.MAX_MANIFEST_BYTES,
        )
        if decision_record.get("review_id") != review_id:
            raise PanelReviewError(
                "Readability promotion decision review_id is stale"
            )
        generated_readability = _readability_attestation_from_decision(
            decision_record,
            decision_path=transient_decision,
            audit=audit,
        )
    packet = prepare_packet(
        audit=audit,
        review_id=review_id,
        created_on=decided_on,
    )
    readability_bindings = _readability_target_authorities(packet)
    if generated_readability is not None:
        generated_compact = json.loads(
            panel_attestation.canonical_attestation_bytes(
                generated_readability,
                expected_path=(
                    panel_attestation.READABILITY_ATTESTATION_PATH
                ),
                expected_source_fingerprints=packet[
                    "source_fingerprints"
                ],
                expected_review_contract_fingerprint=(
                    _canonical_json_sha256(packet["panel_contract"])
                ),
                expected_readability_current_bindings=(
                    readability_bindings
                ),
            )
        )
        if generated_compact != attestation_selector:
            raise PanelReviewError(
                "Readability promotion attestation does not match its decision projection"
            )
    return panel_attestation.READABILITY_ATTESTATION_PATH, {
        "expected_source_fingerprints": packet["source_fingerprints"],
        "expected_review_contract_fingerprint": _canonical_json_sha256(
            packet["panel_contract"]
        ),
        "expected_readability_current_bindings": readability_bindings,
    }, lambda _value: None


def _git_output(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), *arguments],
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PanelReviewError("cannot establish Git promotion preconditions") from exc


def _professional_attestation_clean_stable_head() -> str:
    """Bind one Professional projection pass to one clean repository HEAD."""

    before = _git_output("rev-parse", "--verify", "HEAD").stdout.decode(
        "ascii"
    ).strip()
    if re.fullmatch(r"[0-9a-f]{40}", before) is None:
        raise PanelReviewError("professional attestation HEAD is invalid")
    status = _git_output(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).stdout
    if status:
        raise PanelReviewError("professional attestation requires a clean tree")
    after = _git_output("rev-parse", "--verify", "HEAD").stdout.decode(
        "ascii"
    ).strip()
    if after != before:
        raise PanelReviewError(
            "professional attestation HEAD changed during validation"
        )
    return before


def _require_clean_promotion_tree() -> None:
    status = _git_output(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).stdout
    if status:
        raise PanelReviewError(
            "attestation promotion requires a clean tree outside its destination"
        )


def _promote_attestation(args: argparse.Namespace) -> Path:
    source = _require_same_ephemeral_run_path(
        _cli_path(args.source),
        review_id=args.review_id,
        label="attestation promotion source",
    )
    expected_source = _ephemeral_review_path(args.review_id, "attestation.json")
    if source.absolute() != expected_source.resolve(strict=False):
        raise PanelReviewError(
            "attestation promotion source must use the canonical transient path"
        )
    bound_source = reviewer_manifest.read_bound_regular_file(
        source,
        max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
        label="attestation promotion source",
    )
    try:
        preliminary = (
            panel_attestation.parse_attestation_storage_selector_bytes(
                bound_source.raw
            )
        )
    except panel_attestation.AttestationError as exc:
        raise PanelReviewError(
            "attestation promotion selector is invalid"
        ) from exc
    if preliminary["review_id"] != args.review_id:
        raise PanelReviewError("attestation promotion review_id is stale")
    fixed_relative, validation, _validate_current = _current_attestation_validation(
        args.panel_kind,
        review_id=args.review_id,
        decided_on=preliminary["decided_on"],
        attestation_selector=preliminary,
        promotion_decision_path=(
            _ephemeral_review_path(args.review_id, "panel", "decision.json")
            if args.panel_kind
            in {
                READABILITY_PANEL_KIND,
                PROFESSIONAL_COMPLETENESS_PANEL_KIND,
            }
            else None
        ),
        promotion_source_bytes=bound_source.raw,
    )
    if preliminary["axis"] != args.panel_kind:
        raise PanelReviewError("attestation promotion panel kind is stale")

    def validate_final(raw: bytes) -> object:
        try:
            value = panel_attestation.parse_attestation_bytes(
                raw,
                expected_path=fixed_relative,
                **validation,
            )
        except panel_attestation.AttestationError as exc:
            raise PanelReviewError(
                "attestation promotion source is invalid or stale"
            ) from exc
        return value

    validate_final(bound_source.raw)
    destination = (ROOT / fixed_relative).absolute()
    expected_existing = args.expected_existing_sha256
    bound_existing: reviewer_manifest.BoundFile | None
    if expected_existing == "absent":
        try:
            destination.lstat()
        except FileNotFoundError:
            pass
        else:
            raise PanelReviewError(
                "attestation destination must be absent for creation CAS"
            )
        tracked = _git_output(
            "ls-files", "--error-unmatch", "--", fixed_relative, check=False
        )
        if tracked.returncode == 0:
            raise PanelReviewError(
                "absent attestation destination is unexpectedly tracked"
            )
        bound_existing = None
    else:
        if re.fullmatch(r"[0-9a-f]{64}", expected_existing) is None:
            raise PanelReviewError(
                "expected-existing-sha256 must be absent or a lowercase SHA-256"
            )
        tracked = _git_output(
            "ls-files", "--error-unmatch", "--", fixed_relative, check=False
        )
        if tracked.returncode != 0:
            raise PanelReviewError(
                "replacement attestation destination must be tracked"
            )
        bound_existing = reviewer_manifest.bind_regular_file(
            destination,
            expected_sha256=expected_existing,
            max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
            label="existing attestation destination",
        )
        head_raw = _git_output("show", f"HEAD:{fixed_relative}").stdout
        if (
            hashlib.sha256(head_raw).hexdigest() != expected_existing
            or head_raw != bound_existing.raw
        ):
            raise PanelReviewError(
                "replacement attestation destination must be HEAD-identical"
            )
    _require_clean_promotion_tree()
    reviewer_manifest.promote_bound_file_atomically(
        bound_source,
        destination,
        bound_existing=bound_existing,
        max_bytes=panel_attestation.MAX_ATTESTATION_BYTES,
        validate_final=validate_final,
    )
    return destination


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("prepare", "build-packet"):
        prepare = subparsers.add_parser(command)
        prepare.add_argument(
            "--panel-kind",
            choices=sorted(PANEL_KINDS),
            default=READABILITY_PANEL_KIND,
        )
        prepare.add_argument("--audit", default="reports/skill-content-audit.json")
        prepare.add_argument("--review-id", required=True)
        prepare.add_argument("--created-on", required=True)
        prepare.add_argument("--out", required=True)
        prepare.add_argument(
            "--schema-version",
            type=int,
            choices=(
                PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION,
            ),
            default=PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
            help="Professional Completeness packet schema; other panel kinds reject this option.",
        )
        baseline = prepare.add_mutually_exclusive_group()
        baseline.add_argument(
            "--baseline-decision",
            help="Canonical schema-3 decision used for machine-derived carry planning.",
        )
        baseline.add_argument(
            "--baseline-attestation",
            help="Canonical fixed Professional attestation used for self-contained carry planning.",
        )
        prepare.add_argument(
            "--semantic-re-review-axis",
            action="append",
            choices=sorted(SEMANTIC_AXES),
            default=[],
            help=(
                "Force every current disposition on one affected semantic axis "
                "back into review without modifying the canonical audit."
            ),
        )
        if command == "prepare":
            prepare.add_argument(
                "--reviewer",
                action="append",
                nargs=4,
                default=[],
                metavar=("VOTER_ID", "AGENT_ID", "ROLE", "EXPERTISE"),
                help=(
                    "Declare one canonical Semantic reviewer template; exactly "
                    "three distinct declarations are required for Semantic prepare."
                ),
            )

    template = subparsers.add_parser("template")
    template.add_argument("--packet", required=True)
    template.add_argument("--voter-id", required=True)
    template.add_argument("--agent-id", required=True)
    template.add_argument("--role", required=True)
    template.add_argument("--expertise", action="append", required=True)
    template.add_argument("--expertise-tag", action="append")
    template.add_argument(
        "--skill-id",
        action="append",
        help=(
            "Assign one Professional Completeness schema-2 Skill to this ballot; "
            "repeat for a non-empty subset. Schema 3 derives assignments from "
            "--capsule instead."
        ),
    )
    template.add_argument("--created-on", required=True)
    template.add_argument(
        "--capsule",
        help="Canonical schema-3 review capsule owned by this voter.",
    )
    template.add_argument("--out", required=True)

    discovery = subparsers.add_parser("discovery-capsule")
    discovery.add_argument("--packet", required=True)
    discovery.add_argument("--voter-id", required=True)
    discovery.add_argument("--skill-id", action="append", required=True)
    discovery.add_argument("--created-on", required=True)
    discovery.add_argument("--out", required=True)

    request = subparsers.add_parser("candidate-request")
    request.add_argument("--packet", required=True)
    request.add_argument("--discovery-capsule", required=True)
    request.add_argument("--voter-id", required=True)
    request.add_argument(
        "--reviewer-added-request",
        action="append",
        default=[],
        metavar="TARGET=SKILL=DISCOVERY_REASON",
    )
    request.add_argument("--created-on", required=True)
    request.add_argument("--out", required=True)

    capsule = subparsers.add_parser("capsule")
    capsule.add_argument("--packet", required=True)
    capsule.add_argument("--discovery-capsule", required=True)
    capsule.add_argument("--candidate-request", required=True)
    capsule.add_argument("--voter-id", required=True)
    capsule.add_argument("--created-on", required=True)
    capsule.add_argument("--out", required=True)

    ballot = subparsers.add_parser("validate-ballot")
    ballot.add_argument("--packet", required=True)
    ballot.add_argument("--ballot", required=True)

    materialize = subparsers.add_parser("materialize-ballot")
    materialize.add_argument("--packet", required=True)
    materialize.add_argument("--audit")
    materialize.add_argument("--template", required=True)
    materialize.add_argument("--template-sha256", required=True)
    materialize.add_argument("--manifest", required=True, metavar="PATH|-")
    materialize.add_argument("--manifest-size", required=True, type=int)
    materialize.add_argument("--manifest-sha256", required=True)
    materialize.add_argument(
        "--stdin-framing",
        required=True,
        choices=("raw", "changeforge-base64-chunks-v1"),
    )
    materialize.add_argument("--out", required=True)

    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--packet", required=True)
    aggregate.add_argument("--ballot", action="append", default=[])
    aggregate.add_argument("--decided-on", required=True)
    aggregate.add_argument("--record-dir")
    aggregate.add_argument(
        "--audit",
        help="Fresh canonical audit required for semantic-disposition aggregation.",
    )

    validate = subparsers.add_parser("validate")
    validate.add_argument("--packet", required=True)
    validate.add_argument("--audit")
    artifact = validate.add_mutually_exclusive_group()
    artifact.add_argument("--ballot")
    artifact.add_argument("--ballot-template")
    artifact.add_argument("--decision")

    decision = subparsers.add_parser("validate-decision")
    decision.add_argument("--decision", required=True)

    attest = subparsers.add_parser("attest")
    attest.add_argument("--panel-kind", choices=sorted(PANEL_KINDS), required=True)
    attest.add_argument("--review-id", required=True)
    attest.add_argument("--decision", required=True)
    attest.add_argument("--out", required=True)
    attest.add_argument("--audit")

    promote = subparsers.add_parser("promote-attestation")
    promote.add_argument("--panel-kind", choices=sorted(PANEL_KINDS), required=True)
    promote.add_argument("--review-id", required=True)
    promote.add_argument("--source", required=True)
    promote.add_argument("--expected-existing-sha256", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "attest":
            output, value = _attest(args)
            print(
                "expert-panel-review: attestation="
                f"{_display_cli_path(output)}; verdict={value['verdict']}"
            )
            return 0
        if args.command == "promote-attestation":
            output = _promote_attestation(args)
            print(
                "expert-panel-review: attestation-promoted="
                f"{_display_cli_path(output)}"
            )
            return 0
        if args.command == "materialize-ballot":
            output, ballot = _materialize_ballot(args)
            print(
                "expert-panel-review: ballot-materialized="
                f"{_display_cli_path(output)}; voter="
                f"{ballot['voter']['voter_id']}"
            )
            return 0
        if args.command in {"prepare", "build-packet"}:
            if args.panel_kind == PROFESSIONAL_COMPLETENESS_PANEL_KIND:
                if getattr(args, "reviewer", []):
                    raise PanelReviewError(
                        "--reviewer requires Semantic Disposition prepare"
                    )
                if (
                    args.schema_version
                    == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                ):
                    packet = prepare_professional_completeness_packet_v3(
                        review_id=args.review_id,
                        created_on=args.created_on,
                        baseline_decision_path=(
                            _cli_path(args.baseline_decision)
                            if args.baseline_decision
                            else None
                        ),
                        baseline_attestation_path=(
                            _cli_path(args.baseline_attestation)
                            if args.baseline_attestation
                            else None
                        ),
                    )
                else:
                    if args.baseline_decision or args.baseline_attestation:
                        raise PanelReviewError(
                            "--baseline-decision requires professional schema 3"
                        )
                    packet = prepare_professional_completeness_packet(
                        review_id=args.review_id,
                        created_on=args.created_on,
                    )
            elif args.panel_kind == SEMANTIC_DISPOSITION_PANEL_KIND:
                if (
                    args.baseline_decision
                    or args.baseline_attestation
                    or args.schema_version
                    != PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION
                ):
                    raise PanelReviewError(
                        "--baseline-decision requires professional-completeness"
                    )
                if args.command == "prepare":
                    semantic_layout = _semantic_runtime_layout(args.review_id)
                    _require_exact_materialization_path_argument(
                        args.out,
                        semantic_layout["packet"],
                        label="Semantic prepare packet",
                    )
                    reviewers = _semantic_prepare_reviewer_specs(args.reviewer)
                    audit_raw, audit = _semantic_prepare_audit_authority(
                        args.audit
                    )
                    packet = _semantic_forced_prepare_packet(
                        audit=audit,
                        axes=args.semantic_re_review_axis,
                        review_id=args.review_id,
                        created_on=args.created_on,
                    )
                else:
                    audit = _json_object(
                        Path(args.audit).resolve(), label="content audit"
                    )
                    audit = _semantic_audit_for_axis_rereview(
                        audit, args.semantic_re_review_axis
                    )
                    packet = prepare_semantic_disposition_packet(
                        audit=audit,
                        review_id=args.review_id,
                        created_on=args.created_on,
                    )
                    if args.semantic_re_review_axis:
                        packet["limitations"].append(
                            "Detector-change re-review was forced for semantic axes: "
                            + ", ".join(
                                sorted(set(args.semantic_re_review_axis))
                            )
                            + "."
                        )
                if args.command == "prepare":
                    packet_raw = reviewer_manifest.canonical_ballot_bytes(
                        packet, compact=False
                    )
                    packet_sha256 = hashlib.sha256(packet_raw).hexdigest()
                    templates = [
                        prepare_semantic_ballot_template(
                            packet=packet,
                            packet_sha256=packet_sha256,
                            voter_id=voter_id,
                            agent_id=agent_id,
                            role=role,
                            expertise=[expertise],
                            created_on=args.created_on,
                        )
                        for voter_id, agent_id, role, expertise in reviewers
                    ]
                    _create_semantic_runtime(
                        review_id=args.review_id,
                        audit_raw=audit_raw,
                        packet=packet,
                        templates=templates,
                    )
                    print(
                        "expert-panel-review: prepared="
                        f"{_display_cli_path(semantic_layout['run'])}; "
                        f"semantic={len(packet['semantic_targets'])}; "
                        f"templates={len(templates)}"
                    )
                    return 0
            else:
                if getattr(args, "reviewer", []):
                    raise PanelReviewError(
                        "--reviewer requires Semantic Disposition prepare"
                    )
                if (
                    args.semantic_re_review_axis
                    or args.baseline_decision
                    or args.baseline_attestation
                    or args.schema_version
                    != PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION
                ):
                    raise PanelReviewError(
                        "semantic re-review/baseline options require their matching panel kind"
                    )
                packet = prepare_packet(
                    audit=_json_object(ROOT / args.audit, label="content audit"),
                    review_id=args.review_id,
                    created_on=args.created_on,
                )
            output = _cli_path(args.out)
            create_only = True
            if (
                packet.get("schema_version")
                == PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ):
                output = _require_schema3_cli_artifact_path(
                    output,
                    review_id=packet["review_id"],
                    kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                )
                if output.exists():
                    raise PanelReviewError(
                        "schema-3 canonical packet already exists"
                    )
                create_only = True
            elif (
                packet.get("kind") == PACKET_KIND
                and packet.get("schema_version") == READABILITY_SCHEMA_VERSION
            ):
                output = _require_readability_schema2_cli_packet_path(
                    output,
                    review_id=packet["review_id"],
                )
                if output.exists():
                    raise PanelReviewError(
                        "readability schema-2 canonical packet already exists"
                    )
                create_only = True
            else:
                expected_output = _ephemeral_review_path(
                    packet["review_id"], "packet.json"
                )
                if output.absolute() != expected_output.absolute():
                    raise PanelReviewError(
                        "panel packet output must use its canonical transient run path"
                    )
                output = _require_same_ephemeral_run_path(
                    output,
                    review_id=packet["review_id"],
                    label="panel packet output",
                )
                if output.exists():
                    raise PanelReviewError("canonical transient packet already exists")
            _write_json(
                output,
                packet,
                compact=(
                    packet["kind"] == PROFESSIONAL_COMPLETENESS_PACKET_KIND
                ),
                create_only=create_only,
                validation_root=ROOT,
            )
            display_output = (
                output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
            )
            if packet["kind"] == PROFESSIONAL_COMPLETENESS_PACKET_KIND:
                detail = f"professional={len(packet['professional_targets'])}"
            elif packet["kind"] == SEMANTIC_DISPOSITION_PACKET_KIND:
                detail = (
                    f"semantic={len(packet['semantic_targets'])}; "
                    "root="
                    f"{packet['panel_contract']['required_axis_target_counts']['root']}; "
                    "reference="
                    f"{packet['panel_contract']['required_axis_target_counts']['reference']}"
                )
            else:
                detail = (
                    f"content={len(packet['content_targets'])}; "
                    f"readability={len(packet['readability_targets'])}; "
                    f"actionability={len(packet.get('actionability_targets', []))}"
                )
            print(f"expert-panel-review: packet={display_output}; {detail}")
            return 0
        if args.command in {
            "discovery-capsule",
            "candidate-request",
            "capsule",
        }:
            packet_path = _cli_path(args.packet)
            review_id = packet_path.parent.name
            cache = _professional_v3_invocation_cache()
            packet_path, packet_ref, packet = (
                _professional_v3_bind_json_artifact_path(
                    packet_path,
                    cache=cache,
                    validation_root=ROOT,
                    label=f"schema-3 {args.command} packet",
                    expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                    expected_review_id=review_id,
                )
            )
            if packet.get("schema_version") != (
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ):
                raise PanelReviewError(
                    f"{args.command} requires a schema-3 packet"
                )
            if args.command == "discovery-capsule":
                artifact_value = prepare_professional_discovery_capsule_v3(
                    packet=packet,
                    packet_sha256=packet_ref["sha256"],
                    voter_id=args.voter_id,
                    assigned_skill_ids=sorted(args.skill_id),
                    created_on=args.created_on,
                    validation_root=ROOT,
                )
                artifact_kind = (
                    PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND
                )
                output_label = "discovery-capsule"
                target_count = len(
                    artifact_value["discovery_projection"]["targets"]
                )
            elif args.command == "candidate-request":
                discovery_path = _cli_path(args.discovery_capsule)
                _bound_path, _bound_ref, discovery_value = (
                    _professional_v3_bind_json_artifact_path(
                        discovery_path,
                        cache=cache,
                        validation_root=ROOT,
                        label="schema-3 candidate-request discovery capsule",
                        expected_kind=(
                            PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND
                        ),
                        expected_review_id=packet["review_id"],
                    )
                )
                projection = discovery_value.get("discovery_projection")
                assigned = (
                    projection.get("assigned_fresh_target_ids")
                    if isinstance(projection, dict)
                    else None
                )
                if not isinstance(assigned, list):
                    raise PanelReviewError(
                        "candidate-request discovery assignment is invalid"
                    )
                additions = _parse_reviewer_added_requests(
                    args.reviewer_added_request,
                    assigned_skill_ids=assigned,
                )
                artifact_value = prepare_professional_candidate_request_v3(
                    packet=packet,
                    packet_sha256=packet_ref["sha256"],
                    discovery_capsule_path=discovery_path,
                    voter_id=args.voter_id,
                    reviewer_added_requests_by_target=additions,
                    created_on=args.created_on,
                    validation_root=ROOT,
                )
                artifact_kind = (
                    PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND
                )
                output_label = "candidate-request"
                target_count = len(
                    artifact_value["assigned_fresh_target_ids"]
                )
            else:
                artifact_value = prepare_professional_review_capsule_v3(
                    packet=packet,
                    packet_sha256=packet_ref["sha256"],
                    discovery_capsule_path=_cli_path(
                        args.discovery_capsule
                    ),
                    candidate_request_path=_cli_path(
                        args.candidate_request
                    ),
                    voter_id=args.voter_id,
                    created_on=args.created_on,
                    validation_root=ROOT,
                )
                artifact_kind = PROFESSIONAL_COMPLETENESS_CAPSULE_KIND
                output_label = "capsule"
                target_count = len(
                    artifact_value["review_projection"]["targets"]
                )
            output = _require_schema3_cli_artifact_path(
                _cli_path(args.out),
                review_id=packet["review_id"],
                kind=artifact_kind,
                voter_id=args.voter_id,
            )
            if output.exists():
                raise PanelReviewError(
                    f"schema-3 canonical {output_label} already exists"
                )
            _write_json(
                output,
                artifact_value,
                compact=True,
                create_only=True,
                validation_root=ROOT,
            )
            print(
                f"expert-panel-review: {output_label}="
                f"{_display_cli_path(output)}; targets="
                f"{target_count}"
            )
            return 0
        if args.command == "template":
            packet_path = _cli_path(args.packet)
            cache = _professional_v3_invocation_cache()
            canonical_schema3_packet = _is_round_packet_path(packet_path)
            if canonical_schema3_packet:
                packet_path, packet_ref, packet = (
                    _professional_v3_bind_json_artifact_path(
                        packet_path,
                        cache=cache,
                        validation_root=ROOT,
                        label="schema-3 template packet",
                        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                        expected_review_id=packet_path.parent.name,
                    )
                )
                packet_sha256 = packet_ref["sha256"]
            else:
                packet = _json_object(packet_path, label="panel packet")
                packet_sha256 = _sha256(packet_path)
            if packet.get("schema_version") == (
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ) and not canonical_schema3_packet:
                raise PanelReviewError(
                    "schema-3 template requires the canonical packet layout"
                )
            ballot = build_ballot_template(
                packet=packet,
                packet_sha256=packet_sha256,
                voter_id=args.voter_id,
                agent_id=args.agent_id,
                role=args.role,
                expertise=args.expertise,
                created_on=args.created_on,
                expertise_tags=args.expertise_tag,
                skill_ids=args.skill_id,
                capsule_path=(
                    _cli_path(args.capsule) if args.capsule else None
                ),
                validation_root=ROOT,
            )
            output = _cli_path(args.out)
            if packet.get("schema_version") == (
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ):
                output = _require_schema3_cli_artifact_path(
                    output,
                    review_id=packet["review_id"],
                    kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                    voter_id=args.voter_id,
                )
                if output.exists():
                    raise PanelReviewError(
                        "schema-3 canonical ballot/template already exists"
                    )
            else:
                output = _require_same_ephemeral_run_path(
                    output,
                    review_id=packet["review_id"],
                    label="ballot template output",
                )
                if output.exists():
                    raise PanelReviewError("ballot template output already exists")
            _write_json(
                output,
                ballot,
                create_only=True,
                validation_root=ROOT,
            )
            display_output = (
                output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
            )
            print(
                "expert-panel-review: template="
                f"{display_output}; votes="
                f"{len(ballot.get('content_votes', [])) + len(ballot.get('readability_votes', [])) + len(ballot.get('actionability_votes', [])) + len(ballot.get('professional_votes', [])) + len(ballot.get('semantic_votes', []))}"
            )
            return 0
        if args.command == "validate-ballot":
            packet_path = _cli_path(args.packet)
            ballot_path = _cli_path(args.ballot)
            cache = _professional_v3_invocation_cache()
            if _is_round_packet_path(packet_path):
                packet_path, packet_ref, packet = (
                    _professional_v3_bind_json_artifact_path(
                        packet_path,
                        cache=cache,
                        validation_root=ROOT,
                        label="schema-3 validate-ballot packet",
                        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                        expected_review_id=packet_path.parent.name,
                    )
                )
                if packet.get("schema_version") == (
                    PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                ):
                    ballot_path, _ballot_ref, ballot = (
                        _professional_v3_bind_json_artifact_path(
                            ballot_path,
                            cache=cache,
                            validation_root=ROOT,
                            label="schema-3 validate ballot",
                            expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                            expected_review_id=packet["review_id"],
                        )
                    )
                    validate_ballot(
                        packet,
                        ballot,
                        packet_sha256=packet_ref["sha256"],
                        validation_root=ROOT,
                        artifact_path=ballot_path,
                    )
                else:
                    ballot = _json_object(ballot_path, label="panel ballot")
                    validate_ballot(
                        packet,
                        ballot,
                        packet_sha256=packet_ref["sha256"],
                    )
            else:
                packet = _json_object(packet_path, label="panel packet")
                ballot = _json_object(ballot_path, label="panel ballot")
                if packet.get("schema_version") == (
                    PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                ):
                    raise PanelReviewError(
                        "schema-3 validate-ballot requires canonical artifact layouts"
                    )
                validate_ballot(
                    packet,
                    ballot,
                    packet_sha256=_sha256(packet_path),
                )
            vote_count = (
                len(ballot["professional_votes"])
                if packet["kind"] == PROFESSIONAL_COMPLETENESS_PACKET_KIND
                else (
                    len(ballot["semantic_votes"])
                    if packet["kind"] == SEMANTIC_DISPOSITION_PACKET_KIND
                    else len(ballot["content_votes"])
                    + len(ballot["readability_votes"])
                    + len(ballot.get("actionability_votes", []))
                )
            )
            print(
                "expert-panel-review: ballot-valid="
                f"{ballot['voter']['voter_id']}; votes={vote_count}"
            )
            return 0
        if args.command == "validate":
            packet_path = _cli_path(args.packet)
            schema3_layout = _is_round_packet_path(packet_path)
            schema3_cache = _professional_v3_invocation_cache()
            if schema3_layout:
                packet_path, schema3_packet_ref, packet = (
                    _professional_v3_bind_json_artifact_path(
                        packet_path,
                        cache=schema3_cache,
                        validation_root=ROOT,
                        label="schema-3 validate packet",
                        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                        expected_review_id=packet_path.parent.name,
                    )
                )
            else:
                packet = _json_object(packet_path, label="panel packet")
            if packet.get("schema_version") == (
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ):
                if not schema3_layout:
                    raise PanelReviewError(
                        "schema-3 validate requires the canonical packet layout"
                    )
                validate_packet(
                    packet,
                    validation_root=ROOT,
                    artifact_path=packet_path,
                )
                if not args.ballot and not args.ballot_template and not args.decision:
                    print(f"expert-panel-review: packet-valid={packet_path}")
                    return 0
                if args.ballot or args.ballot_template:
                    artifact_value = args.ballot or args.ballot_template
                    ballot_path, _ballot_ref, ballot_value = (
                        _professional_v3_bind_json_artifact_path(
                            _cli_path(artifact_value),
                            cache=schema3_cache,
                            validation_root=ROOT,
                            label="schema-3 validate ballot artifact",
                            expected_kind=PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
                            expected_review_id=packet["review_id"],
                        )
                    )
                    if args.ballot_template:
                        template_voter = ballot_value.get("voter")
                        if (
                            not isinstance(template_voter, dict)
                            or ballot_path.stem
                            != template_voter.get("voter_id")
                        ):
                            raise PanelReviewError(
                                "schema-3 ballot template filename must equal voter_id"
                            )
                        validate_ballot_template(
                            packet,
                            ballot_value,
                            packet_sha256=schema3_packet_ref["sha256"],
                            validation_root=ROOT,
                        )
                        print(
                            "expert-panel-review: template-valid="
                            f"{ballot_value['voter']['voter_id']}"
                        )
                    else:
                        validate_ballot(
                            packet,
                            ballot_value,
                            packet_sha256=schema3_packet_ref["sha256"],
                            validation_root=ROOT,
                            artifact_path=ballot_path,
                        )
                        print(
                            "expert-panel-review: ballot-valid="
                            f"{ballot_value['voter']['voter_id']}"
                        )
                    return 0
                decision_path = _cli_path(args.decision)
                decision_path, _decision_ref, record = (
                    _professional_v3_bind_json_artifact_path(
                        decision_path,
                        cache=schema3_cache,
                        validation_root=ROOT,
                        label="schema-3 validate decision",
                        expected_kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                        expected_review_id=packet["review_id"],
                    )
                )
                if record.get("packet") != schema3_packet_ref:
                    raise PanelReviewError(
                        "schema-3 decision does not bind the supplied packet"
                    )
                validate_decision_record(
                    record,
                    record_path=decision_path,
                    validation_root=ROOT,
                )
                print(f"expert-panel-review: decision-valid={decision_path}")
                return 0
            if packet.get("kind") == SEMANTIC_DISPOSITION_PACKET_KIND:
                if not args.audit:
                    raise PanelReviewError(
                        "semantic disposition validation requires --audit"
                    )
                validate_semantic_packet_current(
                    packet,
                    _json_object(Path(args.audit).resolve(), label="content audit"),
                )
            else:
                validate_packet(packet)
            if not args.ballot and not args.ballot_template and not args.decision:
                print(f"expert-panel-review: packet-valid={packet_path}")
                return 0
            if args.ballot_template:
                template_path = Path(args.ballot_template).resolve()
                template = _json_object(template_path, label="panel ballot template")
                validate_ballot_template(
                    packet,
                    template,
                    packet_sha256=_sha256(packet_path),
                )
                print(
                    "expert-panel-review: template-valid="
                    f"{template['voter']['voter_id']}"
                )
                return 0
            if args.ballot:
                ballot_path = Path(args.ballot).resolve()
                ballot = _json_object(ballot_path, label="panel ballot")
                validate_ballot(
                    packet, ballot, packet_sha256=_sha256(packet_path)
                )
                print(
                    "expert-panel-review: ballot-valid="
                    f"{ballot['voter']['voter_id']}"
                )
                return 0
            decision_path = Path(args.decision).resolve()
            record = _json_object(decision_path, label="panel decision")
            expected_decision_kind = {
                PACKET_KIND: DECISION_KIND,
                PROFESSIONAL_COMPLETENESS_PACKET_KIND: (
                    PROFESSIONAL_COMPLETENESS_DECISION_KIND
                ),
                SEMANTIC_DISPOSITION_PACKET_KIND: SEMANTIC_DISPOSITION_DECISION_KIND,
            }.get(packet.get("kind"))
            if record.get("kind") != expected_decision_kind:
                raise PanelReviewError(
                    "panel decision kind cannot substitute for the supplied packet kind"
                )
            expected_packet_ref = {
                "path": packet_path.relative_to(ROOT.resolve()).as_posix(),
                "sha256": _sha256(packet_path),
            }
            if record.get("packet") != expected_packet_ref:
                raise PanelReviewError(
                    "panel decision does not bind the supplied current packet"
                )
            validate_decision_record(record, record_path=decision_path)
            print(f"expert-panel-review: decision-valid={decision_path}")
            return 0
        if args.command == "aggregate":
            packet_path = _cli_path(args.packet)
            schema3_layout = _is_round_packet_path(packet_path)
            schema3_cache = _professional_v3_invocation_cache()
            if schema3_layout:
                packet_path, schema3_packet_ref, packet = (
                    _professional_v3_bind_json_artifact_path(
                        packet_path,
                        cache=schema3_cache,
                        validation_root=ROOT,
                        label="schema-3 aggregate packet",
                        expected_kind=PROFESSIONAL_COMPLETENESS_PACKET_KIND,
                        expected_review_id=packet_path.parent.name,
                    )
                )
            else:
                packet = _json_object(packet_path, label="panel packet")
            if packet.get("kind") == SEMANTIC_DISPOSITION_PACKET_KIND:
                if not args.audit:
                    raise PanelReviewError(
                        "semantic disposition aggregation requires --audit"
                    )
                validate_semantic_packet_current(
                    packet,
                    _json_object(Path(args.audit).resolve(), label="content audit"),
                )
            raw_ballots = [_cli_path(value) for value in args.ballot]
            if packet.get("schema_version") == (
                PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ):
                if not schema3_layout:
                    raise PanelReviewError(
                        "schema-3 aggregate requires the canonical packet layout"
                    )
                panel_dir = packet_path.parent / "panel"
                if args.record_dir is not None and _cli_path(
                    args.record_dir
                ).absolute() != panel_dir.absolute():
                    raise PanelReviewError(
                        "schema-3 --record-dir, when supplied, must be its canonical panel directory"
                    )
                decision_path = _require_schema3_cli_artifact_path(
                    panel_dir / "decision.json",
                    review_id=packet["review_id"],
                    kind=PROFESSIONAL_COMPLETENESS_DECISION_KIND,
                )
                if decision_path.exists():
                    raise PanelReviewError(
                        "schema-3 canonical decision already exists"
                    )
                record = aggregate_professional_completeness_ballot_paths_v3(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_paths=raw_ballots,
                    decided_on=args.decided_on,
                    validation_root=ROOT,
                    invocation_cache=schema3_cache,
                )
                _write_json(
                    decision_path,
                    record,
                    compact=True,
                    create_only=True,
                    validation_root=ROOT,
                )
                validate_decision_record(
                    record,
                    record_path=decision_path,
                    validation_root=ROOT,
                )
                print(
                    "expert-panel-review: decision="
                    f"{_display_cli_path(decision_path)}; professional="
                    f"{record['summary']['professional_completeness']}"
                )
                return 0
            if args.record_dir is None:
                raise PanelReviewError(
                    "--record-dir is required for schema-1/schema-2 aggregation"
                )
            if not raw_ballots:
                raise PanelReviewError(
                    "schema-1/schema-2 aggregation requires at least one --ballot"
                )
            ballot_values = [
                (path, _json_object(path, label="panel ballot"))
                for path in raw_ballots
            ]
            aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=ballot_values,
                decided_on=args.decided_on,
            )
            record_dir = _require_same_ephemeral_run_path(
                _cli_path(args.record_dir),
                review_id=packet["review_id"],
                label="record-dir",
            )
            if record_dir.exists():
                if not record_dir.is_dir() or record_dir.is_symlink():
                    raise PanelReviewError("record-dir must be a real directory")
                if any(record_dir.iterdir()):
                    raise PanelReviewError("record-dir must not contain artifacts")
            stored_ballots: list[tuple[Path, dict[str, Any]]] = []
            for source, ballot_value in ballot_values:
                destination = record_dir / f"{ballot_value['voter']['voter_id']}.json"
                _write_json(
                    destination,
                    ballot_value,
                    create_only=True,
                    validation_root=ROOT,
                )
                stored_ballots.append((destination, ballot_value))
            record = aggregate_ballots(
                packet=packet,
                packet_path=packet_path,
                ballot_values=stored_ballots,
                decided_on=args.decided_on,
            )
            decision_path = record_dir / "decision.json"
            _write_json(
                decision_path,
                record,
                create_only=True,
                validation_root=ROOT,
            )
            validate_decision_record(record, record_path=decision_path)
            if record["kind"] == PROFESSIONAL_COMPLETENESS_DECISION_KIND:
                detail = (
                    "professional="
                    f"{record['summary']['professional_completeness']}"
                )
            elif record["kind"] == SEMANTIC_DISPOSITION_DECISION_KIND:
                detail = f"semantic={record['summary']['semantic_dispositions']}"
            else:
                detail = (
                    f"content={record['summary']['content']}; "
                    f"readability={record['summary']['readability']}; "
                    f"actionability={record['summary'].get('actionability', {})}"
                )
            print(
                "expert-panel-review: decision="
                f"{decision_path.relative_to(ROOT)}; {detail}"
            )
            return 0
        decision_path = (ROOT / args.decision).resolve()
        validate_decision_record(
            _json_object(decision_path, label="panel decision"),
            record_path=decision_path,
        )
        print(f"expert-panel-review: decision-valid={decision_path.relative_to(ROOT)}")
        return 0
    except (
        OSError,
        PanelReviewError,
        reviewer_manifest.ManifestError,
        panel_attestation.AttestationError,
        professional_carry.ProfessionalCarryForwardError,
    ) as exc:
        print(f"expert-panel-review: error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
