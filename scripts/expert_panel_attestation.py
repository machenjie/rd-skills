#!/usr/bin/env python3
"""Pure, self-contained contract for compact Expert Panel attestations."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import PurePosixPath
from typing import Any

import expert_panel_contracts as panel_contracts


ATTESTATION_SCHEMA_VERSION = 2
MAX_ATTESTATION_BYTES = 4 * 1024 * 1024
READABILITY_AXIS = "readability"
PROFESSIONAL_COMPLETENESS_AXIS = "professional-completeness"
SEMANTIC_DISPOSITION_AXIS = "semantic-disposition"
READABILITY_ATTESTATION_KIND = "changeforge.readability-attestation"
PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND = (
    "changeforge.professional-completeness-attestation"
)
SEMANTIC_DISPOSITION_ATTESTATION_KIND = (
    "changeforge.semantic-disposition-attestation"
)
READABILITY_ATTESTATION_PATH = "evals/expert-panel/readability.json"
PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH = (
    "evals/expert-panel/professional-completeness.json"
)
SEMANTIC_DISPOSITION_ATTESTATION_PATH = (
    "evals/expert-panel/semantic-disposition.json"
)
ATTESTATION_PATHS = {
    READABILITY_AXIS: READABILITY_ATTESTATION_PATH,
    PROFESSIONAL_COMPLETENESS_AXIS: PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
    SEMANTIC_DISPOSITION_AXIS: SEMANTIC_DISPOSITION_ATTESTATION_PATH,
}
EPHEMERAL_RUN_ROOT = ".rd-skills/expert-panel"

_KINDS = {
    READABILITY_AXIS: READABILITY_ATTESTATION_KIND,
    PROFESSIONAL_COMPLETENESS_AXIS: PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND,
    SEMANTIC_DISPOSITION_AXIS: SEMANTIC_DISPOSITION_ATTESTATION_KIND,
}
_AXES_BY_PATH = {path: axis for axis, path in ATTESTATION_PATHS.items()}
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,126}[a-z0-9])?$")
_COMMON_FIELDS = {
    "schema_version", "kind", "axis", "review_id", "decided_on",
    "source_fingerprints", "review_contract_fingerprint", "reviewers",
    "findings", "summary", "verdict", "rationale",
}
_READABILITY_ATTESTATION_FIELDS = {*_COMMON_FIELDS, "review_artifacts"}
_PRO_ATTESTATION_FIELDS = {
    *(_COMMON_FIELDS - {"source_fingerprints"}),
    "dependency_material_catalog",
    "review_cost_input",
}
PROFESSIONAL_STORAGE_ENCODING = "professional-string-catalog-v1"
PROFESSIONAL_STORAGE_ENCODING_FIELD = "storage_encoding"
PROFESSIONAL_STRING_CATALOG_FIELD = "string_catalog"
_PROFESSIONAL_STORAGE_ROUTING_FIELDS = {
    "schema_version",
    "kind",
    "axis",
    "review_id",
    "decided_on",
    "review_contract_fingerprint",
}
_PROFESSIONAL_STORAGE_FIELDS = {
    *(_PRO_ATTESTATION_FIELDS - {"summary"}),
    PROFESSIONAL_STORAGE_ENCODING_FIELD,
    PROFESSIONAL_STRING_CATALOG_FIELD,
}
_BASIC_REVIEWER_FIELDS = {
    "voter_id", "agent_id", "role", "expertise", "independent_review",
}
_PRO_REVIEWER_FIELDS = {
    *_BASIC_REVIEWER_FIELDS, "expertise_tags", "qualification_claims",
}
_QUALIFICATION_FIELDS = {
    "expertise_tag", "qualification_basis", "proof_limit",
}
_RESULT_FIELDS = {
    "winning_disposition", "winning_votes", "vote_counts",
    "supporting_voters", "dissenting_voters",
}
_SIMPLE_VOTE_FIELDS = {
    "voter_id", "disposition", "reason_code", "rationale",
}
_CONTENT_FIELDS = {
    "category", "target_id", "source_fingerprint",
    "review_binding_fingerprint", "votes", "result",
}
_READABILITY_FIELDS = {
    "category", "target_id", "source_fingerprint",
    "review_binding_fingerprint", "finding_reviews", "result",
}
_READABILITY_FINDING_FIELDS = {
    "finding_id", "source_fingerprint", "review_binding_fingerprint",
    "votes", "result",
}
_ACTION_FIELDS = {
    "category", "target_id", "source_fingerprint",
    "review_binding_fingerprint", "votes", "result",
}
_SEMANTIC_FIELDS = {
    "target_id", "axis", "candidate_binding_fingerprint", "votes", "result",
}
_SEMANTIC_EVIDENCE_FIELDS = {
    "target_id", "axis", "candidate", "candidate_binding_fingerprint",
    "votes", "result",
}
_SEMANTIC_GOVERNANCE_FIELDS = {
    "disposition", "disposition_record", "governance_status", "resolved", "unresolved",
}
_SEMANTIC_VOTE_FIELDS = {
    "voter_id", "disposition", "rationale", "authority_or_condition",
    "decision_owner", "mitigation", "review_after",
}
_PRO_FINDING_FIELDS = {
    "skill_id", "package_fingerprint", "review_binding_fingerprint",
    "required_expertise_tags", "required_candidate_ids",
    "dependency_material_fingerprints", "provenance", "result", "rationale",
}
_PROVENANCE_FIELDS = {"mode", "origin"}
_ORIGIN_FIELDS = {
    "review_id", "decided_on", "origin_depth", "review_contract_fingerprint",
    "package_fingerprint", "review_binding_fingerprint",
    "required_expertise_tags", "required_candidate_ids",
    "dependency_material_fingerprints", "votes", "origin_fingerprint",
}
_PRO_VOTE_FIELDS = {
    "reviewer", "decision", "reason_code", "evidence_anchors", "criteria",
    "examined_failure_modes", "examined_omission_candidates",
    "examined_adjacent_candidates", "proof_limits", "rationale",
}
_ANCHOR_FIELDS = {
    "anchor_id", "skill_id", "path", "start_line", "end_line", "excerpt",
    "excerpt_sha256",
}
_CRITERION_RESULT_FIELDS = {"status", "evidence_assertions"}
_ASSERTION_FIELDS = {
    "claim", "evidence_anchor_ids", "source_excerpt_sha256",
}
_FAILURE_FIELDS = {"failure_mode", "outcome", "evidence_anchor_ids", "rationale"}
_OMISSION_FIELDS = {
    "omission_candidate", "outcome", "evidence_anchor_ids", "rationale",
}
_ADJACENCY_FIELDS = {
    "skill_id", "review_origin", "discovery_reason", "disposition",
    "target_anchor_ids", "candidate_anchor_ids", "rationale",
}
_PRO_RESULT_FIELDS = {
    "qualification_coverage", "criterion_vote_counts", "domain_critical_defects",
    "ordinary_criterion_defects", "ordinary_criterion_disposition",
    "winning_disposition", "winning_votes", "vote_counts", "supporting_voters",
    "dissenting_voters", "final_disposition", "review_dependencies",
    "evidence_metrics",
}
_COMPACT_PRO_FINDING_FIELDS = {
    "skill_id", "package_material_binding", "review_unit_binding",
    "dependency_ids", "required_expertise_tags", "votes", "result",
    "provenance",
}
_COMPACT_PRO_AUTHORITY_FIELDS = set(
    panel_contracts.PROFESSIONAL_COMPACT_AUTHORITY_FIELDS
)
_COMPACT_PRO_ORIGIN_FIELDS = {
    "origin_review_id", "origin_commit", "origin_verdict_digest",
}
_COMPACT_PRO_VOTE_FIELDS = set(
    panel_contracts.PROFESSIONAL_COMPACT_VOTE_FIELDS
)
_COMPACT_CRITERIA_FIELDS = set(
    panel_contracts.PROFESSIONAL_COMPACT_CRITERIA_FIELDS
)
_COMPACT_COLLECTION_FIELDS = set(
    panel_contracts.PROFESSIONAL_COMPACT_COLLECTION_FIELDS
) - {"digest"}
_COMPACT_ADJACENCY_FIELDS = set(
    panel_contracts.PROFESSIONAL_COMPACT_ADJACENCY_FIELDS
) - {"digest"}
_COMPACT_PROOF_LIMIT_FIELDS = set(
    panel_contracts.PROFESSIONAL_COMPACT_PROOF_LIMIT_FIELDS
) - {"digest"}
_COMPACT_REVIEWER_PARTITION_FIELDS = {
    "domain_voters", "architecture_voter",
}
_EVIDENCE_METRIC_KEYS = {
    "target_vote_count", "required_adjacency_candidate_count",
    "criterion_result_count", "criterion_anchor_binding_count",
    "criterion_assertion_count", "evidence_anchor_count",
    "examined_failure_mode_count", "examined_omission_candidate_count",
    "examined_adjacency_count", "examined_required_adjacency_count",
    "reviewer_added_adjacency_count", "proof_limit_count",
    "qualification_claim_count",
}
PROFESSIONAL_REVIEW_COST_FIELDS = {
    "fresh_vote_count", "carried_forward_vote_count", "effective_vote_count",
    "fresh_criterion_result_count", "carried_forward_criterion_result_count",
    "effective_criterion_result_count", "canonical_capsule_input_bytes_proxy",
    "full_rereview_deduplicated_capsule_input_bytes_proxy", "input_ratio_ppm",
    "required_only_capsule_input_bytes_proxy", "required_only_input_ratio_ppm",
    "required_only_source_material_input_bytes_proxy",
    "source_material_input_bytes_proxy",
    "full_rereview_source_material_input_bytes_proxy",
    "source_material_coverage_ratio_ppm",
    "reviewer_added_source_material_input_bytes_proxy",
    "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy",
    "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm",
    "reviewer_added_request_count", "reviewer_added_unique_relationship_count",
    "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
    "formal_round_policy_fingerprint", "maximum_origin_depth",
    "plan_lineage_depth", "policy_status", "limitations",
}
PROFESSIONAL_REVIEW_COST_INPUT_FIELDS = {
    "canonical_capsule_input_bytes_proxy",
    "full_rereview_deduplicated_capsule_input_bytes_proxy",
    "required_only_capsule_input_bytes_proxy",
    "required_only_source_material_input_bytes_proxy",
    "source_material_input_bytes_proxy",
    "full_rereview_source_material_input_bytes_proxy",
    "reviewer_added_request_count", "reviewer_added_unique_relationship_count",
    "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
    "formal_round_policy_fingerprint", "plan_lineage_depth", "policy_status",
}
PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY = {
    "schema_version": 1,
    "full_fresh_source_material_coverage_ratio_ppm": 1_000_000,
    "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 50_000,
    "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 1_000_000,
}
PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FINGERPRINT = (
    "2851d39a4f19abdb21d9a0516223a01598247d0897b5f5be3a4ce8a7ad156d6e"
)
PROFESSIONAL_REVIEW_COST_LIMITATIONS = [
    (
        "Canonical effective discovery/request/final input-block bytes are a "
        "structural proxy; identical blocks are counted at most three times, "
        "while formal policy separately recomputes required-only source coverage "
        "and reviewer-added relationship/evidence metadata overhead; neither "
        "measure proves actual tokens, wall-clock time, subagent count, monetary "
        "cost, or reviewer behavior."
    ),
    (
        "Static qualification claims do not prove reviewer identity, credentials, "
        "or domain experience."
    ),
    (
        "Static round-tree validation cannot prove that historical schema-3 "
        "rounds were not deleted."
    ),
]
_SOURCE_KEYS = {
    READABILITY_AXIS: set(
        panel_contracts.READABILITY_SOURCE_FINGERPRINT_KEYS
    ),
    PROFESSIONAL_COMPLETENESS_AXIS: {
        "professional_packages", "professional_review_bindings",
        "professional_review_contract",
    },
    SEMANTIC_DISPOSITION_AXIS: set(
        panel_contracts.SEMANTIC_DISPOSITION_SOURCE_FINGERPRINT_KEYS
    ),
}
_LEGACY_READABILITY_SOURCE_KEYS = set(
    panel_contracts.READABILITY_LEGACY_SOURCE_FINGERPRINT_KEYS
)
_LEGACY_SEMANTIC_SOURCE_KEYS = set(
    panel_contracts.SEMANTIC_DISPOSITION_LEGACY_SOURCE_FINGERPRINT_KEYS
)
_CONTENT_DECISIONS = {"accepted-current-density", "tracked-tightening"}
_READABILITY_DECISIONS = {"accepted-current-readability", "tracked-tightening"}
_ACTION_DECISIONS = {
    "accepted-current-actionability", "detector-false-positive", "rewrite-required",
}
_REASON_CODES = {
    "accepted-current-density": {
        "bounded-density-preserves-professional-coverage",
        "split-would-fragment-one-decision-model",
    },
    "accepted-current-readability": {
        "bounded-enumeration-improves-precision", "domain-terms-require-co-location",
        "single-indivisible-decision", "split-would-fragment-invariant",
    },
    "tracked-tightening": {
        "cross-boundary-decisions-conflated", "enumeration-obscures-primary-action",
        "multiple-independent-actions", "policy-exception-verification-conflated",
    },
    "accepted-current-actionability": {
        "bounded-skill-needs-fewer-generic-signals",
        "explicit-domain-actions-are-front-loaded",
        "short-root-is-actionable-as-a-whole",
    },
    "detector-false-positive": {
        "equivalent-action-verb-not-recognized", "equivalent-heading-not-recognized",
        "front-window-structure-misclassified",
    },
    "rewrite-required": {
        "generic-context-obscures-first-move", "primary-action-not-front-loaded",
        "stop-or-escalation-not-front-loaded", "verification-not-front-loaded",
    },
}
_SEMANTIC_DISPOSITIONS = {
    "rewrite", "valid-contextual-rule", "false-positive", "time-bounded-exception",
}
_CRITERIA = set(panel_contracts.PROFESSIONAL_CRITERIA)
_CRITICAL_CRITERIA = set(
    panel_contracts.PROFESSIONAL_DOMAIN_CRITICAL_CRITERIA
)
_ORDINARY_CRITERIA = set(panel_contracts.PROFESSIONAL_ORDINARY_CRITERIA)
_PRO_DECISIONS = set(panel_contracts.PROFESSIONAL_DECISIONS)
PROFESSIONAL_REASON_CODES = {
    disposition: set(reason_codes)
    for disposition, reason_codes in panel_contracts.PROFESSIONAL_REASON_CODES.items()
}
_FINAL_DISPOSITIONS = set(panel_contracts.PROFESSIONAL_FINAL_DISPOSITIONS)
_CRITERION_VALUES = set(panel_contracts.PROFESSIONAL_CRITERION_VALUES)
_EXAMINED_OUTCOMES = set(panel_contracts.PROFESSIONAL_REVIEW_OUTCOMES)
_ADJACENCY_DISPOSITIONS = set(
    panel_contracts.PROFESSIONAL_ADJACENCY_DISPOSITIONS
)
_ARCHITECTURE_TAG = panel_contracts.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG
_FORBIDDEN = (
    ".rd-skills", "packet.json", "ballots/", "ballots\\", "capsules/",
    "capsules\\", "predecessor decision", "evals/expert-panel/",
    "panel/decision.json",
)


class AttestationError(ValueError):
    """Raised when normalized attestation evidence is invalid or stale."""


class AttestationCurrentnessError(AttestationError):
    """Raised only when trusted evidence no longer matches current authority."""


def readability_source_fingerprint_shape(value: object) -> str:
    """Classify one closed Readability source shape without granting currentness."""

    if not isinstance(value, dict):
        raise AttestationError("source fingerprint fields are not closed")
    keys = set(value)
    if keys == _SOURCE_KEYS[READABILITY_AXIS]:
        return "current"
    if keys == _LEGACY_READABILITY_SOURCE_KEYS:
        return "legacy"
    raise AttestationError("source fingerprint fields are not closed")


def semantic_source_fingerprint_shape(value: object) -> str:
    """Classify one closed Semantic source shape without granting currentness."""

    if not isinstance(value, dict):
        raise AttestationError("source fingerprint fields are not closed")
    keys = set(value)
    if keys == _SOURCE_KEYS[SEMANTIC_DISPOSITION_AXIS]:
        return "current"
    if keys == _LEGACY_SEMANTIC_SOURCE_KEYS:
        return "legacy"
    raise AttestationError("source fingerprint fields are not closed")


def _closed(value: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise AttestationError(f"{label} fields are not closed")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AttestationError(f"{label} must be canonical non-blank text")
    return value


def _slug(value: object, label: str) -> str:
    if not isinstance(value, str) or _SLUG_RE.fullmatch(value) is None:
        raise AttestationError(f"{label} must be a canonical slug")
    return value


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise AttestationError(f"{label} must be a lowercase SHA-256")
    return value


def _iso_date(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise AttestationError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise AttestationError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise AttestationError(f"{label} must be an ISO date")
    return value


def _sorted_strings(value: object, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AttestationError(f"{label} must be a string array")
    if nonempty and not value:
        raise AttestationError(f"{label} must be non-empty")
    if value != sorted(set(value)):
        raise AttestationError(f"{label} must be sorted and unique")
    for item in value:
        _text(item, label)
    return value


def _source_path(value: object, label: str) -> str:
    if not isinstance(value, str) or "\\" in value:
        raise AttestationError(f"{label} must be a repository source path")
    path = PurePosixPath(value)
    if (
        path.is_absolute() or path.as_posix() != value or not path.parts
        or path.parts[0] != "src" or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise AttestationError(f"{label} must be a repository source path")
    return value


def _json_body(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AttestationError("value is not canonical JSON") from exc


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(_json_body(value)).hexdigest()


def semantic_candidate_review_evidence(
    *, axis: str, candidate: dict[str, Any]
) -> dict[str, Any]:
    """Match the producer's complete, governance-free candidate projection."""

    if axis not in {"root", "reference"} or not isinstance(candidate, dict):
        raise AttestationError("semantic candidate projection input is invalid")
    evidence = {
        key: copy.deepcopy(value)
        for key, value in candidate.items()
        if key not in _SEMANTIC_GOVERNANCE_FIELDS
    }
    if axis == "reference":
        evidence.pop("priority", None)
    return evidence


def semantic_candidate_current_binding(
    *, axis: str, candidate: dict[str, Any]
) -> dict[str, Any]:
    """Match the producer's stable identity and local-evidence projection."""

    if axis not in {"root", "reference"} or not isinstance(candidate, dict):
        raise AttestationError("semantic current-binding input is invalid")
    identity_fields = (
        "candidate_id", "finding", "path", "owner", "skill_owner", "source_selector",
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


def semantic_candidate_fingerprints(
    *, axis: str, candidate: dict[str, Any]
) -> dict[str, str]:
    """Return the sole complete binding for one current Semantic candidate."""

    return {
        "candidate_binding_fingerprint": canonical_json_sha256(
            {
                "review_evidence": semantic_candidate_review_evidence(
                    axis=axis, candidate=candidate
                ),
                "local_semantic_context": semantic_candidate_current_binding(
                    axis=axis, candidate=candidate
                ),
            }
        ),
    }


def semantic_candidate_authority(
    *, axis: str, candidate: dict[str, Any]
) -> dict[str, Any]:
    """Bind compact digests to complete current evidence outside the file."""

    evidence = semantic_candidate_review_evidence(axis=axis, candidate=candidate)
    return {
        "candidate": evidence,
        **semantic_candidate_fingerprints(axis=axis, candidate=evidence),
    }


def readability_target_authority(
    *, category: str, target: dict[str, Any]
) -> dict[str, Any]:
    """Bind one compact Readability row to complete current packet evidence."""

    if category not in {"content", "readability", "actionability"} or not isinstance(
        target, dict
    ):
        raise AttestationError("readability target authority input is invalid")
    identity_field = "path" if category == "content" else (
        "document_id" if category == "readability" else "target_id"
    )
    target_id = _text(
        target.get(identity_field),
        f"readability {category} target identity",
    )
    source_fingerprint = _sha(
        target.get("content_fingerprint"),
        f"readability {category} source fingerprint",
    )
    authority: dict[str, Any] = {
        "category": category,
        "target_id": target_id,
        "target": copy.deepcopy(target),
        "source_fingerprint": source_fingerprint,
    }
    finding_bindings: list[dict[str, str]] = []
    if category == "readability":
        raw_findings = target.get("findings")
        if not isinstance(raw_findings, list) or not raw_findings:
            raise AttestationError(
                "readability target authority findings must be non-empty"
            )
        findings: dict[str, dict[str, Any]] = {}
        for index, finding in enumerate(raw_findings):
            if not isinstance(finding, dict):
                raise AttestationError(
                    f"readability target authority finding {index} is invalid"
                )
            finding_id = _sha(
                finding.get("finding_id"),
                f"readability target authority finding {index} identity",
            )
            if finding_id in findings:
                raise AttestationError(
                    "readability target authority finding identities are duplicated"
                )
            finding_source_fingerprint = _sha(
                finding.get("sentence_fingerprint"),
                f"readability target authority finding {index} source fingerprint",
            )
            try:
                finding_review_authority = (
                    panel_contracts.readability_finding_review_projection(
                        finding=finding
                    )
                )
            except ValueError as exc:
                raise AttestationError(str(exc)) from exc
            finding_binding = {
                "binding_contract_id": (
                    panel_contracts.READABILITY_FINDING_BINDING_CONTRACT_ID
                ),
                "target_id": target_id,
                "review_authority": finding_review_authority,
            }
            findings[finding_id] = {
                "finding_id": finding_id,
                "finding": copy.deepcopy(finding),
                "source_fingerprint": finding_source_fingerprint,
                "review_binding_fingerprint": canonical_json_sha256(
                    finding_binding
                ),
            }
        authority["findings"] = {
            finding_id: findings[finding_id] for finding_id in sorted(findings)
        }
        finding_bindings = [
            {
                "finding_id": finding_id,
                "review_binding_fingerprint": finding[
                    "review_binding_fingerprint"
                ],
            }
            for finding_id, finding in authority["findings"].items()
        ]
    try:
        target_review_authority = (
            panel_contracts.readability_target_review_projection(
                category=category, target=target
            )
        )
    except ValueError as exc:
        raise AttestationError(str(exc)) from exc
    target_binding: dict[str, Any] = {
        "binding_contract_id": (
            panel_contracts.READABILITY_TARGET_BINDING_CONTRACT_ID
        ),
        "category": category,
        "target_id": target_id,
        "review_authority": target_review_authority,
    }
    if category == "readability":
        target_binding["finding_authorities"] = finding_bindings
    authority["review_binding_fingerprint"] = canonical_json_sha256(
        target_binding
    )
    return authority


def _readability_authority_projection(
    value: object,
) -> dict[str, dict[str, dict[str, Any]]]:
    if not isinstance(value, dict) or set(value) != {
        "content", "readability", "actionability"
    }:
        raise AttestationError(
            "expected Readability current bindings are incomplete"
        )
    projected: dict[str, dict[str, dict[str, Any]]] = {}
    for category in ("content", "readability", "actionability"):
        rows = value[category]
        if not isinstance(rows, dict):
            raise AttestationError(
                "expected Readability current binding category is invalid"
            )
        projected[category] = {}
        for target_id, raw in rows.items():
            if not isinstance(raw, dict) or "target" not in raw:
                raise AttestationError(
                    "expected Readability current binding is incomplete"
                )
            recomputed = readability_target_authority(
                category=category, target=raw["target"]
            )
            if target_id != recomputed["target_id"] or raw != recomputed:
                raise AttestationError(
                    "expected Readability current binding is stale"
                )
            projected[category][target_id] = {
                "source_fingerprint": recomputed["source_fingerprint"],
                "review_binding_fingerprint": recomputed[
                    "review_binding_fingerprint"
                ],
                **(
                    {
                        "findings": {
                            finding_id: {
                                "source_fingerprint": finding[
                                    "source_fingerprint"
                                ],
                                "review_binding_fingerprint": finding[
                                    "review_binding_fingerprint"
                                ],
                            }
                            for finding_id, finding in recomputed[
                                "findings"
                            ].items()
                        }
                    }
                    if category == "readability"
                    else {}
                ),
            }
    return projected


def readability_target_manifest_projection(
    value: object,
) -> dict[str, Any]:
    """Return the one complete Readability target-authority manifest."""

    projected = _readability_binding_projection(
        _readability_authority_projection(value)
    )
    targets: list[dict[str, Any]] = []
    for category in ("content", "readability", "actionability"):
        for target_id, authority in sorted(projected[category].items()):
            targets.append(
                {
                    "category": category,
                    "target_id": target_id,
                    **copy.deepcopy(authority),
                }
            )
    return {
        "contract_id": panel_contracts.READABILITY_TARGET_MANIFEST_CONTRACT_ID,
        "targets": targets,
    }


def readability_target_manifest_fingerprint(value: object) -> str:
    """Hash the complete Readability target-authority manifest once."""

    return canonical_json_sha256(readability_target_manifest_projection(value))


def _readability_binding_projection(
    value: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Project validated authorities without raw provenance fingerprints."""

    return {
        category: {
            target_id: {
                "review_binding_fingerprint": authority[
                    "review_binding_fingerprint"
                ],
                **(
                    {
                        "findings": {
                            finding_id: {
                                "review_binding_fingerprint": finding[
                                    "review_binding_fingerprint"
                                ]
                            }
                            for finding_id, finding in authority.get(
                                "findings", {}
                            ).items()
                        }
                    }
                    if category == "readability"
                    else {}
                ),
            }
            for target_id, authority in rows.items()
        }
        for category, rows in value.items()
    }


def _readability_local_authority(
    *,
    category: str,
    authority: dict[str, Any],
    finding_id: str | None = None,
) -> dict[str, Any]:
    target = {
        "review_binding_fingerprint": authority[
            "review_binding_fingerprint"
        ],
    }
    if finding_id is None:
        return {"target": target}
    finding = authority["findings"].get(finding_id)
    if finding is None:
        raise AttestationError(
            "Readability authoritative finding identity is unknown"
        )
    return {
        "target": target,
        "finding": {
            "review_binding_fingerprint": finding[
                "review_binding_fingerprint"
            ],
        },
    }


def readability_review_unit_binding(
    *,
    category: str,
    target_id: str,
    authority: dict[str, Any],
    finding_id: str | None = None,
) -> str:
    """Bind one compact review-unit identity to its sole manifest authority."""

    if category not in {"content", "readability", "actionability"}:
        raise AttestationError("Readability review unit category is invalid")
    if (category == "readability") != (finding_id is not None):
        raise AttestationError("Readability review unit identity is invalid")
    projection: dict[str, Any] = {
        "binding_contract_id": (
            panel_contracts.READABILITY_REVIEW_UNIT_BINDING_CONTRACT_ID
        ),
        "category": category,
        "target_id": target_id,
        "local_authority": _readability_local_authority(
            category=category,
            authority=authority,
            finding_id=finding_id,
        ),
    }
    if finding_id is not None:
        projection["finding_id"] = finding_id
    return canonical_json_sha256(projection)


def _readability_review_artifacts(
    value: object,
    *,
    reviewer_ids: list[str] | None = None,
) -> dict[str, Any]:
    row = _closed(
        value,
        {"decision", "packet", "ballots"},
        "Readability review_artifacts",
    )
    for artifact in ("decision", "packet"):
        artifact_row = _closed(
            row[artifact],
            {"sha256"},
            f"Readability review_artifacts.{artifact}",
        )
        _sha(
            artifact_row["sha256"],
            f"Readability review_artifacts.{artifact}.sha256",
        )
    ballots = row["ballots"]
    if not isinstance(ballots, list) or len(ballots) != 3:
        raise AttestationError(
            "Readability review_artifacts must contain exactly three ballots"
        )
    voter_ids: list[str] = []
    for index, raw in enumerate(ballots):
        ballot = _closed(
            raw,
            {"voter_id", "sha256"},
            f"Readability review_artifacts.ballots[{index}]",
        )
        voter_ids.append(
            _slug(
                ballot["voter_id"],
                f"Readability review_artifacts.ballots[{index}].voter_id",
            )
        )
        _sha(
            ballot["sha256"],
            f"Readability review_artifacts.ballots[{index}].sha256",
        )
    if voter_ids != sorted(set(voter_ids)):
        raise AttestationError(
            "Readability review_artifacts ballot identities are not canonical"
        )
    if reviewer_ids is not None and voter_ids != reviewer_ids:
        raise AttestationError(
            "Readability review_artifacts ballot coverage is stale"
        )
    return row


def _forbidden(value: object, label: str = "attestation") -> None:
    if isinstance(value, str):
        if any(fragment in value.lower() for fragment in _FORBIDDEN):
            raise AttestationError(f"{label} contains an external evidence reference")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _forbidden(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            _forbidden(key, f"{label}.field")
            _forbidden(item, f"{label}.{key}")


def attestation_axis_for_path(path: object) -> str:
    if not isinstance(path, str) or path not in _AXES_BY_PATH:
        raise AttestationError("attestation path is not fixed")
    return _AXES_BY_PATH[path]


def ephemeral_review_root(review_id: object) -> str:
    return f"{EPHEMERAL_RUN_ROOT}/{_slug(review_id, 'review_id')}"


def validate_ephemeral_run_path(path: object, *, review_id: str | None = None) -> str:
    if not isinstance(path, str) or not path or "\\" in path:
        raise AttestationError("ephemeral path is not canonical")
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute() or parsed.as_posix() != path or len(parsed.parts) < 3
        or parsed.parts[:2] != (".rd-skills", "expert-panel")
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise AttestationError("ephemeral path escapes its lexical base")
    actual = _slug(parsed.parts[2], "ephemeral review_id")
    if review_id is not None and actual != _slug(review_id, "review_id"):
        raise AttestationError("ephemeral path review_id is stale")
    return path


def ephemeral_run_path(review_id: object, relative_path: object) -> str:
    if not isinstance(relative_path, str) or not relative_path:
        raise AttestationError("run-relative path must be non-empty")
    return validate_ephemeral_run_path(
        f"{ephemeral_review_root(review_id)}/{relative_path}",
        review_id=str(review_id),
    )


def _validate_basic_reviewer(value: object, label: str) -> dict[str, Any]:
    row = _closed(value, _BASIC_REVIEWER_FIELDS, label)
    _slug(row["voter_id"], f"{label}.voter_id")
    _text(row["agent_id"], f"{label}.agent_id")
    _text(row["role"], f"{label}.role")
    _sorted_strings(row["expertise"], f"{label}.expertise", nonempty=True)
    if row["independent_review"] is not True:
        raise AttestationError(f"{label} must be independent")
    return row


def _validate_pro_reviewer(
    value: object, label: str, required_tags: list[str]
) -> tuple[dict[str, Any], str]:
    row = _closed(value, _PRO_REVIEWER_FIELDS, label)
    _validate_basic_reviewer(
        {key: row[key] for key in _BASIC_REVIEWER_FIELDS}, label
    )
    tags = _sorted_strings(row["expertise_tags"], f"{label}.expertise_tags", nonempty=True)
    claims = row["qualification_claims"]
    if not isinstance(claims, list):
        raise AttestationError(f"{label}.qualification_claims must be an array")
    claim_tags = []
    for index, raw in enumerate(claims):
        claim = _closed(raw, _QUALIFICATION_FIELDS, f"{label}.qualification_claims[{index}]")
        claim_tags.append(_slug(claim["expertise_tag"], f"{label}.qualification tag"))
        _text(claim["qualification_basis"], f"{label}.qualification basis")
        _text(claim["proof_limit"], f"{label}.qualification proof limit")
    if claim_tags != tags:
        raise AttestationError(f"{label} qualifications do not cover expertise tags")
    if tags == [_ARCHITECTURE_TAG]:
        return row, "architecture"
    if _ARCHITECTURE_TAG in tags or not set(required_tags).issubset(tags):
        raise AttestationError(f"{label} is not qualified for the target")
    return row, "domain"


def _validate_reviewer_pool(
    reviewers: object, *, professional: bool, allow_empty: bool = False
) -> dict[str, dict[str, Any]]:
    if not isinstance(reviewers, list) or (not allow_empty and len(reviewers) != 3):
        raise AttestationError("reviewer pool size is invalid")
    by_id: dict[str, dict[str, Any]] = {}
    agents: list[str] = []
    roles: list[str] = []
    for index, raw in enumerate(reviewers):
        row = (
            _closed(raw, _PRO_REVIEWER_FIELDS, f"reviewers[{index}]")
            if professional
            else _validate_basic_reviewer(raw, f"reviewers[{index}]")
        )
        if professional:
            _validate_pro_reviewer(row, f"reviewers[{index}]", [])
        voter_id = _slug(row["voter_id"], f"reviewers[{index}].voter_id")
        if voter_id in by_id:
            raise AttestationError("reviewer voter identities must be unique")
        by_id[voter_id] = row
        agents.append(row["agent_id"])
        roles.append(row["role"])
    if list(by_id) != sorted(by_id) or len(agents) != len(set(agents)):
        raise AttestationError("reviewer identities are not canonical")
    if not professional and len(roles) != len(set(roles)):
        raise AttestationError("readability and semantic reviewer roles must be unique")
    return by_id


def _majority(votes: list[dict[str, Any]], decisions: set[str]) -> dict[str, Any]:
    if len(votes) != 3:
        raise AttestationError("target requires exactly three votes")
    voter_ids = [vote["voter_id"] for vote in votes]
    if voter_ids != sorted(set(voter_ids)):
        raise AttestationError("target voters must be sorted and unique")
    counts = {decision: sum(vote["disposition"] == decision for vote in votes)
              for decision in sorted(decisions)}
    winner, winning_votes = max(counts.items(), key=lambda item: (item[1], item[0]))
    if winning_votes < 2:
        raise AttestationError("target votes have no majority")
    return {
        "winning_disposition": winner,
        "winning_votes": winning_votes,
        "vote_counts": counts,
        "supporting_voters": [vote["voter_id"] for vote in votes if vote["disposition"] == winner],
        "dissenting_voters": [vote["voter_id"] for vote in votes if vote["disposition"] != winner],
    }


def _simple_votes(
    value: object, *, reviewers: dict[str, dict[str, Any]], decisions: set[str], label: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise AttestationError(f"{label} must be an array")
    for index, raw in enumerate(value):
        vote = _closed(raw, _SIMPLE_VOTE_FIELDS, f"{label}[{index}]")
        voter_id = _slug(vote["voter_id"], f"{label}[{index}].voter_id")
        if voter_id not in reviewers:
            raise AttestationError(f"{label}[{index}] reviewer is unknown")
        decision = vote["disposition"]
        if decision not in decisions or vote["reason_code"] not in _REASON_CODES[decision]:
            raise AttestationError(f"{label}[{index}] decision or reason is invalid")
        _text(vote["rationale"], f"{label}[{index}].rationale")
    return value


def _derive_readability(
    attestation: dict[str, Any],
    *,
    expected_current_bindings: dict[str, dict[str, dict[str, Any]]],
) -> tuple[dict[str, Any], str]:
    reviewers = _validate_reviewer_pool(attestation["reviewers"], professional=False)
    _readability_review_artifacts(
        attestation["review_artifacts"], reviewer_ids=list(reviewers)
    )
    expected = _readability_authority_projection(expected_current_bindings)
    actual: dict[str, dict[str, dict[str, Any]]] = {
        "content": {}, "readability": {}, "actionability": {},
    }
    identities = []
    summary = {
        "content": {value: 0 for value in sorted(_CONTENT_DECISIONS)},
        "readability": {value: 0 for value in sorted(_READABILITY_DECISIONS)},
        "actionability": {value: 0 for value in sorted(_ACTION_DECISIONS)},
    }
    failure = False
    for index, raw in enumerate(attestation["findings"]):
        if not isinstance(raw, dict):
            raise AttestationError(f"findings[{index}] must be an object")
        category = raw.get("category")
        identity = (category, raw.get("target_id"))
        identities.append(identity)
        if category == "content":
            row = _closed(raw, _CONTENT_FIELDS, f"findings[{index}]")
            _text(row["target_id"], f"findings[{index}].target_id")
            votes = _simple_votes(row["votes"], reviewers=reviewers, decisions=_CONTENT_DECISIONS, label=f"findings[{index}].votes")
            result = _majority(votes, _CONTENT_DECISIONS)
        elif category == "readability":
            row = _closed(raw, _READABILITY_FIELDS, f"findings[{index}]")
            _text(row["target_id"], f"findings[{index}].target_id")
            finding_rows = row["finding_reviews"]
            if not isinstance(finding_rows, list) or not finding_rows:
                raise AttestationError("readability finding_reviews must be non-empty")
            document_votes = {voter_id: [] for voter_id in reviewers}
            finding_ids = []
            for finding_index, finding_raw in enumerate(finding_rows):
                finding = _closed(finding_raw, _READABILITY_FINDING_FIELDS, f"findings[{index}].finding_reviews[{finding_index}]")
                finding_ids.append(_sha(finding["finding_id"], "readability finding_id"))
                _sha(finding["source_fingerprint"], "readability finding source fingerprint")
                _sha(finding["review_binding_fingerprint"], "readability finding review binding fingerprint")
                votes = _simple_votes(finding["votes"], reviewers=reviewers, decisions=_READABILITY_DECISIONS, label="readability finding votes")
                finding["result"] = _majority(votes, _READABILITY_DECISIONS)
                for vote in votes:
                    document_votes[vote["voter_id"]].append(vote["disposition"])
            if finding_ids != sorted(set(finding_ids)):
                raise AttestationError("readability finding IDs are not canonical")
            derived_votes = [
                {"voter_id": voter_id,
                 "disposition": ("tracked-tightening" if "tracked-tightening" in dispositions else "accepted-current-readability")}
                for voter_id, dispositions in sorted(document_votes.items())
            ]
            result = _majority(derived_votes, _READABILITY_DECISIONS)
            actual[category][row["target_id"]] = {
                "source_fingerprint": _sha(
                    row["source_fingerprint"],
                    f"findings[{index}].source_fingerprint",
                ),
                "review_binding_fingerprint": _sha(
                    row["review_binding_fingerprint"],
                    f"findings[{index}].review_binding_fingerprint",
                ),
                "findings": {
                    finding["finding_id"]: {
                        "source_fingerprint": finding["source_fingerprint"],
                        "review_binding_fingerprint": finding[
                            "review_binding_fingerprint"
                        ],
                    }
                    for finding in finding_rows
                },
            }
        elif category == "actionability":
            row = _closed(raw, _ACTION_FIELDS, f"findings[{index}]")
            _text(row["target_id"], f"findings[{index}].target_id")
            votes = _simple_votes(row["votes"], reviewers=reviewers, decisions=_ACTION_DECISIONS, label=f"findings[{index}].votes")
            result = _majority(votes, _ACTION_DECISIONS)
        else:
            raise AttestationError(f"findings[{index}].category is invalid")
        if category != "readability":
            actual[category][row["target_id"]] = {
                "source_fingerprint": _sha(
                    row["source_fingerprint"],
                    f"findings[{index}].source_fingerprint",
                ),
                "review_binding_fingerprint": _sha(
                    row["review_binding_fingerprint"],
                    f"findings[{index}].review_binding_fingerprint",
                ),
            }
        row["result"] = result
        summary[category][result["winning_disposition"]] += 1
        failure = failure or result["winning_disposition"] in {
            "tracked-tightening", "detector-false-positive", "rewrite-required",
        }
    expected_order = {"content": 0, "readability": 1, "actionability": 2}
    if identities != sorted(set(identities), key=lambda item: (expected_order.get(item[0], 99), str(item[1]))):
        raise AttestationError("readability targets are not canonical")
    if _readability_binding_projection(
        actual
    ) != _readability_binding_projection(expected):
        raise AttestationError(
            "readability review binding coverage is stale"
        )
    return summary, ("requires-readability-correction" if failure else "accepted-current-readability")


def _validate_semantic_candidate(
    candidate: object, *, axis: str, label: str
) -> dict[str, Any]:
    if not isinstance(candidate, dict) or not candidate:
        raise AttestationError(f"{label} must be a non-empty object")
    if candidate != semantic_candidate_review_evidence(
        axis=axis, candidate=candidate
    ):
        raise AttestationError(f"{label} contains disposition-selected governance")
    candidate_id = _sha(candidate.get("candidate_id"), f"{label}.candidate_id")
    del candidate_id
    for field in ("finding", "owner", "skill_owner"):
        _text(candidate.get(field), f"{label}.{field}")
    source_selector = candidate.get("source_selector")
    if not isinstance(source_selector, dict) or not source_selector:
        raise AttestationError(f"{label}.source_selector must be a non-empty object")
    path = candidate.get("path")
    if path != "group":
        _source_path(path, f"{label}.path")
    _sha(candidate.get("fingerprint"), f"{label}.fingerprint")
    occurrences = candidate.get("occurrences")
    if not isinstance(occurrences, list) or not occurrences:
        raise AttestationError(f"{label}.occurrences must be non-empty")
    member_paths = []
    for index, occurrence in enumerate(occurrences):
        occurrence_label = f"{label}.occurrences[{index}]"
        if not isinstance(occurrence, dict):
            raise AttestationError(f"{occurrence_label} must be an object")
        member_paths.append(
            _source_path(occurrence.get("path"), f"{occurrence_label}.path")
        )
        lines = occurrence.get("lines")
        if (
            not isinstance(lines, dict) or set(lines) != {"start", "end"}
            or type(lines.get("start")) is not int
            or type(lines.get("end")) is not int
            or lines["start"] < 1 or lines["end"] < lines["start"]
        ):
            raise AttestationError(f"{occurrence_label}.lines is invalid")
        preview = occurrence.get("preview")
        if not isinstance(preview, str) or not preview.strip():
            raise AttestationError(f"{occurrence_label}.preview must be non-blank text")
    if axis == "root":
        _text(candidate.get("document_part"), f"{label}.document_part")
        _sha(
            candidate.get("occurrence_fingerprint"),
            f"{label}.occurrence_fingerprint",
        )
        _sha(candidate.get("context_fingerprint"), f"{label}.context_fingerprint")
        for index, occurrence in enumerate(occurrences):
            _sha(
                occurrence.get("context_fingerprint"),
                f"{label}.occurrences[{index}].context_fingerprint",
            )
    else:
        _sha(candidate.get("evidence_fingerprint"), f"{label}.evidence_fingerprint")
        _sha(candidate.get("content_fingerprint"), f"{label}.content_fingerprint")
    if axis == "reference" and path == "group":
        if len(member_paths) < 2 or len(set(member_paths)) < 2:
            raise AttestationError(
                f"{label} group requires complete multi-path membership"
            )
        for index, occurrence in enumerate(occurrences):
            _text(occurrence.get("owner"), f"{label}.occurrences[{index}].owner")
    return candidate


def _derive_semantic(attestation: dict[str, Any]) -> tuple[dict[str, Any], str]:
    reviewers = _validate_reviewer_pool(attestation["reviewers"], professional=False)
    counts = {value: 0 for value in sorted(_SEMANTIC_DISPOSITIONS)}
    target_ids = []
    for index, raw in enumerate(attestation["findings"]):
        row = _closed(raw, _SEMANTIC_EVIDENCE_FIELDS, f"findings[{index}]")
        if row["axis"] not in {"root", "reference"}:
            raise AttestationError("semantic target axis is invalid")
        candidate = _validate_semantic_candidate(
            row["candidate"], axis=row["axis"],
            label=f"findings[{index}].candidate",
        )
        candidate_id = _sha(candidate["candidate_id"], "semantic candidate_id")
        if row["target_id"] != f"{row['axis']}:{candidate_id}":
            raise AttestationError("semantic target identity is stale")
        expected_binding = semantic_candidate_fingerprints(
            axis=row["axis"], candidate=candidate
        )["candidate_binding_fingerprint"]
        if row["candidate_binding_fingerprint"] != expected_binding:
            raise AttestationError("semantic candidate binding is stale")
        votes = row["votes"]
        if not isinstance(votes, list):
            raise AttestationError("semantic votes must be an array")
        for vote_index, vote_raw in enumerate(votes):
            vote = _closed(vote_raw, _SEMANTIC_VOTE_FIELDS, f"semantic votes[{vote_index}]")
            if vote["voter_id"] not in reviewers or vote["disposition"] not in _SEMANTIC_DISPOSITIONS:
                raise AttestationError("semantic voter or disposition is invalid")
            for field in ("rationale", "authority_or_condition", "decision_owner", "mitigation"):
                _text(vote[field], f"semantic vote.{field}")
            if vote["disposition"] == "time-bounded-exception":
                _iso_date(vote["review_after"], "semantic vote.review_after")
            elif vote["review_after"] is not None:
                raise AttestationError("semantic review_after is invalid")
        row["result"] = _majority(votes, _SEMANTIC_DISPOSITIONS)
        counts[row["result"]["winning_disposition"]] += 1
        target_ids.append(row["target_id"])
    if target_ids != sorted(set(target_ids)):
        raise AttestationError("semantic targets are not canonical")
    return {"semantic_dispositions": counts}, "accepted-current-semantic-disposition"


def _derive_compact_semantic(
    attestation: dict[str, Any],
    *,
    expected_current_bindings: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    if not isinstance(expected_current_bindings, dict):
        raise AttestationError("expected Semantic current bindings are invalid")
    reviewers = _validate_reviewer_pool(
        attestation["reviewers"], professional=False
    )
    counts = {value: 0 for value in sorted(_SEMANTIC_DISPOSITIONS)}
    target_ids = []
    for index, raw in enumerate(attestation["findings"]):
        row = _closed(raw, _SEMANTIC_FIELDS, f"findings[{index}]")
        target_id = row["target_id"]
        if not isinstance(target_id, str):
            raise AttestationError("semantic target identity is stale")
        target_parts = target_id.split(":")
        if (
            len(target_parts) != 2
            or target_parts[0] not in {"root", "reference"}
            or row["axis"] != target_parts[0]
        ):
            raise AttestationError("semantic target identity is stale")
        _sha(target_parts[1], f"findings[{index}].target_id candidate")
        authority = expected_current_bindings.get(target_id)
        if not isinstance(authority, dict):
            raise AttestationError("semantic candidate authority is incomplete")
        binding = _sha(
            row["candidate_binding_fingerprint"],
            f"findings[{index}].candidate_binding_fingerprint",
        )
        reviewed_rewrite = set(authority) == {
            "candidate_binding_fingerprint",
            "reviewed_rewrite",
        }
        if reviewed_rewrite:
            if authority["reviewed_rewrite"] is not True or authority[
                "candidate_binding_fingerprint"
            ] != binding:
                raise AttestationError(
                    "semantic reviewed rewrite binding is stale"
                )
        else:
            if set(authority) != {
                "candidate", "candidate_binding_fingerprint",
            }:
                raise AttestationError(
                    "semantic candidate authority is incomplete"
                )
            candidate = _validate_semantic_candidate(
                authority["candidate"],
                axis=row["axis"],
                label=f"expected Semantic candidate {target_id}",
            )
            if candidate["candidate_id"] != target_parts[1]:
                raise AttestationError(
                    "semantic candidate authority identity is stale"
                )
            recomputed = semantic_candidate_fingerprints(
                axis=row["axis"], candidate=candidate
            )
            if authority != {"candidate": candidate, **recomputed}:
                raise AttestationError(
                    "semantic candidate authority digests are stale"
                )
            if binding != recomputed["candidate_binding_fingerprint"]:
                raise AttestationError("semantic candidate binding is stale")
        votes = row["votes"]
        if not isinstance(votes, list):
            raise AttestationError("semantic votes must be an array")
        for vote_index, vote_raw in enumerate(votes):
            vote = _closed(
                vote_raw,
                _SEMANTIC_VOTE_FIELDS,
                f"semantic votes[{vote_index}]",
            )
            if (
                vote["voter_id"] not in reviewers
                or vote["disposition"] not in _SEMANTIC_DISPOSITIONS
            ):
                raise AttestationError(
                    "semantic voter or disposition is invalid"
                )
            for field in (
                "rationale",
                "authority_or_condition",
                "decision_owner",
                "mitigation",
            ):
                _text(vote[field], f"semantic vote.{field}")
            if vote["disposition"] == "time-bounded-exception":
                _iso_date(vote["review_after"], "semantic vote.review_after")
            elif vote["review_after"] is not None:
                raise AttestationError("semantic review_after is invalid")
        result = _majority(votes, _SEMANTIC_DISPOSITIONS)
        if reviewed_rewrite and result["winning_disposition"] != "rewrite":
            raise AttestationError(
                "semantic reviewed rewrite authority lacks a rewrite majority"
            )
        row["result"] = result
        counts[result["winning_disposition"]] += 1
        target_ids.append(target_id)
    if set(expected_current_bindings) != set(target_ids):
        raise AttestationError("semantic candidate fingerprint coverage is stale")
    return {
        "semantic_dispositions": counts
    }, "accepted-current-semantic-disposition"


def professional_source_excerpt_fingerprint(
    anchors: list[dict[str, Any]], anchor_ids: list[str]
) -> str:
    by_id = {row["anchor_id"]: row for row in anchors}
    projection = [
        {key: by_id[anchor_id][key] for key in (
            "anchor_id", "skill_id", "path", "start_line", "end_line", "excerpt"
        )}
        for anchor_id in anchor_ids
    ]
    return canonical_json_sha256(projection)


def professional_origin_fingerprint(origin: dict[str, Any]) -> str:
    projected = copy.deepcopy(origin)
    projected.pop("origin_fingerprint", None)
    return canonical_json_sha256(projected)


def _validate_anchor_ids(
    value: object, anchors: dict[str, dict[str, Any]], label: str
) -> list[str]:
    ids = _sorted_strings(value, label, nonempty=True)
    if not set(ids).issubset(anchors):
        raise AttestationError(f"{label} contains unknown anchors")
    return ids


def _validate_professional_vote(
    raw: object, *, skill_id: str, required_tags: list[str], required_candidates: list[str],
    label: str,
) -> tuple[dict[str, Any], str]:
    vote = _closed(raw, _PRO_VOTE_FIELDS, label)
    reviewer, kind = _validate_pro_reviewer(vote["reviewer"], f"{label}.reviewer", required_tags)
    anchors_raw = vote["evidence_anchors"]
    if not isinstance(anchors_raw, list) or not anchors_raw:
        raise AttestationError(f"{label}.evidence_anchors must be non-empty")
    anchors: dict[str, dict[str, Any]] = {}
    for index, anchor_raw in enumerate(anchors_raw):
        anchor = _closed(anchor_raw, _ANCHOR_FIELDS, f"{label}.evidence_anchors[{index}]")
        anchor_id = _slug(anchor["anchor_id"], "professional anchor_id")
        if anchor_id in anchors:
            raise AttestationError("professional anchor IDs must be unique")
        _slug(anchor["skill_id"], "professional anchor skill_id")
        _source_path(anchor["path"], "professional anchor path")
        if type(anchor["start_line"]) is not int or type(anchor["end_line"]) is not int or anchor["start_line"] < 1 or anchor["end_line"] < anchor["start_line"]:
            raise AttestationError("professional anchor line range is invalid")
        excerpt = _text(anchor["excerpt"], "professional anchor excerpt")
        if len(excerpt.splitlines()) != anchor["end_line"] - anchor["start_line"] + 1:
            raise AttestationError("professional anchor excerpt line count is stale")
        if anchor["excerpt_sha256"] != hashlib.sha256(excerpt.encode("utf-8")).hexdigest():
            raise AttestationError("professional anchor excerpt digest is stale")
        anchors[anchor_id] = anchor
    if list(anchors) != sorted(anchors):
        raise AttestationError("professional anchors must be sorted")
    criteria = vote["criteria"]
    if not isinstance(criteria, dict) or set(criteria) != _CRITERIA:
        raise AttestationError("professional criteria fields are not closed")
    referenced: set[str] = set()
    statuses: dict[str, str] = {}
    for criterion in sorted(_CRITERIA):
        result = _closed(criteria[criterion], _CRITERION_RESULT_FIELDS, f"{label}.criteria.{criterion}")
        if result["status"] not in _CRITERION_VALUES:
            raise AttestationError("professional criterion status is invalid")
        assertions = result["evidence_assertions"]
        if not isinstance(assertions, list) or not assertions:
            raise AttestationError("professional criterion assertions must be non-empty")
        for assertion_index, assertion_raw in enumerate(assertions):
            assertion = _closed(assertion_raw, _ASSERTION_FIELDS, f"{label}.criteria.{criterion}[{assertion_index}]")
            _text(assertion["claim"], "professional assertion claim")
            ids = _validate_anchor_ids(assertion["evidence_anchor_ids"], anchors, "professional assertion anchors")
            if any(anchors[anchor_id]["skill_id"] != skill_id for anchor_id in ids):
                raise AttestationError("professional criterion cites another Skill")
            if assertion["source_excerpt_sha256"] != professional_source_excerpt_fingerprint(list(anchors.values()), ids):
                raise AttestationError("professional assertion excerpt digest is stale")
            referenced.update(ids)
        statuses[criterion] = result["status"]
    failure_defect = False
    failures = vote["examined_failure_modes"]
    omissions = vote["examined_omission_candidates"]
    for collection, fields, name, item_key in (
        (failures, _FAILURE_FIELDS, "failure", "failure_mode"),
        (omissions, _OMISSION_FIELDS, "omission", "omission_candidate"),
    ):
        if not isinstance(collection, list) or not collection:
            raise AttestationError(f"professional {name} evidence must be non-empty")
        names = []
        defect = False
        for index, item_raw in enumerate(collection):
            item = _closed(item_raw, fields, f"{label}.{name}[{index}]")
            names.append(_text(item[item_key], f"professional {name} name"))
            if item["outcome"] not in _EXAMINED_OUTCOMES:
                raise AttestationError(f"professional {name} outcome is invalid")
            ids = _validate_anchor_ids(item["evidence_anchor_ids"], anchors, f"professional {name} anchors")
            if any(anchors[anchor_id]["skill_id"] != skill_id for anchor_id in ids):
                raise AttestationError(f"professional {name} cites another Skill")
            referenced.update(ids)
            _text(item["rationale"], f"professional {name} rationale")
            defect = defect or item["outcome"] == "defect-found"
        if names != sorted(set(names)):
            raise AttestationError(f"professional {name} evidence is not canonical")
        if name == "failure":
            failure_defect = defect
        elif defect != (statuses["material-omissions"] == "defect-found"):
            raise AttestationError("professional omission evidence conflicts with criterion")
    if failure_defect != (statuses["failure-modes"] == "defect-found"):
        raise AttestationError("professional failure evidence conflicts with criterion")
    adjacency = vote["examined_adjacent_candidates"]
    if not isinstance(adjacency, list):
        raise AttestationError("professional adjacency evidence must be an array")
    candidate_ids = []
    adjacency_defect = False
    for index, item_raw in enumerate(adjacency):
        item = _closed(item_raw, _ADJACENCY_FIELDS, f"{label}.adjacency[{index}]")
        candidate_id = _slug(item["skill_id"], "professional candidate skill_id")
        candidate_ids.append(candidate_id)
        if item["review_origin"] not in {"packet-required", "reviewer-added"}:
            raise AttestationError("professional adjacency review_origin is invalid")
        expected_origin = "packet-required" if candidate_id in required_candidates else "reviewer-added"
        if item["review_origin"] != expected_origin:
            raise AttestationError("professional adjacency origin is stale")
        if expected_origin == "packet-required" and item["discovery_reason"] is not None:
            raise AttestationError("packet-required adjacency cannot have discovery reason")
        if expected_origin == "reviewer-added":
            _text(item["discovery_reason"], "reviewer-added discovery reason")
        if item["disposition"] not in _ADJACENCY_DISPOSITIONS:
            raise AttestationError("professional adjacency disposition is invalid")
        target_ids = _validate_anchor_ids(item["target_anchor_ids"], anchors, "professional target anchors")
        candidate_anchor_ids = _validate_anchor_ids(item["candidate_anchor_ids"], anchors, "professional candidate anchors")
        if any(anchors[anchor_id]["skill_id"] != skill_id for anchor_id in target_ids) or any(anchors[anchor_id]["skill_id"] != candidate_id for anchor_id in candidate_anchor_ids):
            raise AttestationError("professional adjacency anchor ownership is invalid")
        referenced.update(target_ids)
        referenced.update(candidate_anchor_ids)
        _text(item["rationale"], "professional adjacency rationale")
        adjacency_defect = adjacency_defect or item["disposition"] == "gap-or-overlap-defect"
    if candidate_ids != sorted(set(candidate_ids)) or not set(required_candidates).issubset(candidate_ids):
        raise AttestationError("professional adjacency coverage is incomplete")
    if adjacency_defect != (statuses["adjacent-overlap-or-gap"] == "defect-found"):
        raise AttestationError("professional adjacency evidence conflicts with criterion")
    proof_limits = _sorted_strings(vote["proof_limits"], "professional proof_limits", nonempty=True)
    if referenced != set(anchors):
        raise AttestationError("professional anchors must all be used")
    defect = "defect-found" in statuses.values()
    expected_decision = "requires-professional-correction" if defect else "accepted-current-professional-completeness"
    if vote["decision"] != expected_decision:
        raise AttestationError("professional vote decision conflicts with criteria")
    expected_reason = (
        "all-professional-criteria-satisfied" if not defect else None
    )
    if expected_reason is not None and vote["reason_code"] != expected_reason:
        raise AttestationError("professional vote reason_code is invalid")
    _text(vote["rationale"], "professional vote rationale")
    return vote, kind


def professional_compact_vote_fingerprint(vote: dict[str, Any]) -> str:
    """Fingerprint one fully validated authoritative Professional vote."""

    return canonical_json_sha256(vote)


def _bounded_text(value: object, label: str, *, maximum: int) -> str:
    text = _text(value, label)
    if len(text) > maximum:
        raise AttestationError(f"{label} exceeds {maximum} characters")
    return text


def _compact_count(value: object, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise AttestationError(f"{label} must be an integer >= {minimum}")
    return value


def _validate_compact_professional_vote(
    raw: object,
    *,
    required_candidates: list[str],
    expected_vote: dict[str, Any],
    reviewer_partition: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    """Validate conclusions retained after full schema-3 source replay."""

    if not isinstance(raw, dict):
        raise AttestationError(f"{label} must be an object")
    normalized_raw = copy.deepcopy(raw)
    for field in (
        "examined_failure_modes",
        "examined_omission_candidates",
        "examined_adjacent_candidates",
        "proof_limits",
    ):
        if isinstance(normalized_raw.get(field), dict):
            normalized_raw[field].pop("digest", None)
    vote = _closed(normalized_raw, _COMPACT_PRO_VOTE_FIELDS, label)
    voter_id = _slug(vote["reviewer"], f"{label}.reviewer")
    _sha(
        vote["review_evidence_fingerprint"],
        f"{label}.review_evidence_fingerprint",
    )
    criteria = vote["criteria"]
    criteria = _closed(criteria, _COMPACT_CRITERIA_FIELDS, f"{label}.criteria")
    ordinary = criteria["ordinary"]
    if not isinstance(ordinary, dict) or set(ordinary) != _ORDINARY_CRITERIA:
        raise AttestationError("professional compact criteria fields are not closed")
    for criterion in sorted(_ORDINARY_CRITERIA):
        if ordinary[criterion] not in _CRITERION_VALUES:
            raise AttestationError("professional compact criterion status is invalid")
    critical_defects = _sorted_strings(
        criteria["domain_critical_defects"],
        f"{label}.criteria.domain_critical_defects",
    )
    if not set(critical_defects).issubset(_CRITICAL_CRITERIA):
        raise AttestationError("professional compact critical defect set is invalid")
    if voter_id == reviewer_partition["architecture_voter"] and critical_defects:
        raise AttestationError("architecture vote cannot assert a domain critical defect")

    for field, criterion in (
        ("examined_failure_modes", "failure-modes"),
        ("examined_omission_candidates", "material-omissions"),
    ):
        summary = _closed(
            vote[field], _COMPACT_COLLECTION_FIELDS, f"{label}.{field}"
        )
        count = _compact_count(summary["count"], f"{label}.{field}.count", minimum=1)
        defects = _compact_count(
            summary["defect_count"], f"{label}.{field}.defect_count"
        )
        if defects > count:
            raise AttestationError(f"{label}.{field} defect count exceeds count")
        if voter_id in reviewer_partition["domain_voters"] and (
            (defects > 0) != (criterion in critical_defects)
        ):
            raise AttestationError(
                f"{label}.{field} defects conflict with domain critical defects"
            )

    adjacency = _closed(
        vote["examined_adjacent_candidates"],
        _COMPACT_ADJACENCY_FIELDS,
        f"{label}.examined_adjacent_candidates",
    )
    count = _compact_count(
        adjacency["count"], f"{label}.examined_adjacent_candidates.count"
    )
    required_count = _compact_count(
        adjacency["required_count"],
        f"{label}.examined_adjacent_candidates.required_count",
    )
    defect_count = _compact_count(
        adjacency["defect_count"],
        f"{label}.examined_adjacent_candidates.defect_count",
    )
    if required_count != len(required_candidates) or max(
        required_count, defect_count
    ) > count:
        raise AttestationError("professional compact adjacency counts are stale")
    added_ids = _sorted_strings(
        adjacency["reviewer_added_candidate_ids"],
        f"{label}.examined_adjacent_candidates.reviewer_added_candidate_ids",
    )
    if set(added_ids) & set(required_candidates):
        raise AttestationError("professional compact adjacency origins overlap")
    if (defect_count > 0) != (
        ordinary["adjacent-overlap-or-gap"] == "defect-found"
    ):
        raise AttestationError("professional compact adjacency conflicts with criterion")

    proof_limits = _closed(
        vote["proof_limits"],
        _COMPACT_PROOF_LIMIT_FIELDS,
        f"{label}.proof_limits",
    )
    proof_count = _compact_count(
        proof_limits["count"], f"{label}.proof_limits.count", minimum=1
    )
    bounded = proof_limits["bounded"]
    if (
        not isinstance(bounded, list)
        or not bounded
        or len(bounded)
        > panel_contracts.PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_COUNT
        or len(bounded) > proof_count
    ):
        raise AttestationError("professional compact proof limits are not bounded")
    for index, item in enumerate(bounded):
        _bounded_text(
            item,
            f"{label}.proof_limits.bounded[{index}]",
            maximum=(
                panel_contracts.PROFESSIONAL_COMPACT_PROOF_LIMIT_ITEM_MAXIMUM
            ),
        )

    if vote["decision"] not in _PRO_DECISIONS:
        raise AttestationError("professional compact vote decision is invalid")
    if vote["reason_code"] not in PROFESSIONAL_REASON_CODES[vote["decision"]]:
        raise AttestationError("professional compact vote reason_code is invalid")
    _bounded_text(
        vote["rationale"],
        f"{label}.rationale",
        maximum=panel_contracts.PROFESSIONAL_COMPACT_RATIONALE_MAXIMUM,
    )
    if not isinstance(expected_vote, dict):
        raise AttestationError("professional authenticated compact vote is stale")
    normalized_expected = copy.deepcopy(expected_vote)
    for field in (
        "examined_failure_modes",
        "examined_omission_candidates",
        "examined_adjacent_candidates",
        "proof_limits",
    ):
        if isinstance(normalized_expected.get(field), dict):
            normalized_expected[field].pop("digest", None)
    if vote != normalized_expected:
        raise AttestationError("professional authenticated compact vote is stale")
    return vote


def _derive_compact_professional_target(
    row: dict[str, Any], *, attestation: dict[str, Any],
    expected_authority: dict[str, Any],
    reviewer_pool: dict[str, dict[str, Any]],
    dependency_material_catalog: dict[str, str],
) -> tuple[dict[str, Any], set[str], str]:
    skill_id = _slug(row["skill_id"], "professional skill_id")
    _sha(
        row["package_material_binding"],
        "professional package material binding",
    )
    _sha(row["review_unit_binding"], "professional review unit binding")
    required_tags = _sorted_strings(
        row["required_expertise_tags"], "required expertise", nonempty=True
    )
    required_candidates = _sorted_strings(
        expected_authority["required_candidate_ids"], "required candidates"
    )
    dependency_ids = _sorted_strings(
        row["dependency_ids"], "dependency candidates"
    )
    if not set(dependency_ids) <= set(dependency_material_catalog):
        raise AttestationError(
            "professional dependency material catalog is incomplete"
        )

    provenance = _closed(
        row["provenance"], _PROVENANCE_FIELDS, "professional provenance"
    )
    if provenance["mode"] not in {"fresh", "carried"}:
        raise AttestationError("professional provenance mode is invalid")
    origin = _closed(
        provenance["origin"],
        _COMPACT_PRO_ORIGIN_FIELDS,
        "professional origin",
    )
    origin_review_id = _slug(
        origin["origin_review_id"], "professional origin review_id"
    )
    if not isinstance(origin["origin_commit"], str) or re.fullmatch(
        r"[0-9a-f]{40}", origin["origin_commit"]
    ) is None:
        raise AttestationError("professional origin commit is invalid")

    partition = _closed(
        expected_authority["reviewer_partition"],
        _COMPACT_REVIEWER_PARTITION_FIELDS,
        f"professional reviewer partition {skill_id}",
    )
    domain_voters = _sorted_strings(
        partition["domain_voters"],
        f"professional domain voters {skill_id}",
        nonempty=True,
    )
    architecture_voter = _slug(
        partition["architecture_voter"],
        f"professional architecture voter {skill_id}",
    )
    if (
        len(domain_voters)
        != panel_contracts.PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS
        or architecture_voter in domain_voters
    ):
        raise AttestationError("professional reviewer partition is invalid")
    authoritative_voters = {*domain_voters, architecture_voter}
    vote_authorities = expected_authority["vote_authorities"]
    if (
        not isinstance(vote_authorities, dict)
        or set(vote_authorities) != authoritative_voters
    ):
        raise AttestationError(
            "expected professional vote authority is incomplete"
        )

    votes = row["votes"]
    if (
        not isinstance(votes, list)
        or len(votes) != panel_contracts.PROFESSIONAL_PANEL_SIZE
    ):
        raise AttestationError("professional target requires exactly three votes")
    for index, raw_vote in enumerate(votes):
        voter_id = (
            raw_vote.get("reviewer") if isinstance(raw_vote, dict) else None
        )
        if not isinstance(voter_id, str) or voter_id not in vote_authorities:
            raise AttestationError("professional compact reviewer is stale")
        _validate_compact_professional_vote(
            raw_vote,
            required_candidates=required_candidates,
            expected_vote=vote_authorities[voter_id],
            reviewer_partition=partition,
            label=f"professional votes[{index}]",
        )
    voter_ids = [vote["reviewer"] for vote in votes]
    if voter_ids != sorted(authoritative_voters):
        raise AttestationError("professional effective reviewer identities are invalid")
    if origin != expected_authority["origin"]:
        raise AttestationError("professional authenticated origin is stale")
    added_ids = sorted(
        {
            item
            for vote in votes
            for item in vote["examined_adjacent_candidates"][
                "reviewer_added_candidate_ids"
            ]
        }
    )
    derived_dependency_ids = sorted(set(required_candidates) | set(added_ids))
    if dependency_ids != derived_dependency_ids:
        raise AttestationError("professional dependency fingerprint coverage is stale")

    criterion_counts = {
        criterion: {
            status: sum(
                vote["criteria"]["ordinary"][criterion] == status
                for vote in votes
            )
            for status in sorted(_CRITERION_VALUES)
        }
        for criterion in sorted(_ORDINARY_CRITERIA)
    }
    domain_defects = sorted(
        [
            {"criterion": criterion, "voter_id": vote["reviewer"]}
            for vote in votes
            if vote["reviewer"] in domain_voters
            for criterion in vote["criteria"]["domain_critical_defects"]
        ],
        key=lambda item: (item["criterion"], item["voter_id"]),
    )
    ordinary_defects = [
        criterion
        for criterion in sorted(_ORDINARY_CRITERIA)
        if criterion_counts[criterion]["defect-found"] >= 2
    ]
    ordinary_disposition = (
        "requires-professional-correction"
        if ordinary_defects
        else "accepted-current-professional-completeness"
    )
    final_disposition = (
        "unresolved-professional-disagreement"
        if domain_defects
        else ordinary_disposition
    )
    majority = _majority(
        [
            {
                "voter_id": vote["reviewer"],
                "disposition": vote["decision"],
            }
            for vote in votes
        ],
        _PRO_DECISIONS,
    )
    metrics = expected_authority["evidence_metrics"]
    if not isinstance(metrics, dict) or set(metrics) != _EVIDENCE_METRIC_KEYS:
        raise AttestationError("expected professional evidence metrics are incomplete")
    if any(type(value) is not int or value < 0 for value in metrics.values()):
        raise AttestationError("expected professional evidence metrics are invalid")
    expected_metric_subset = {
        "target_vote_count": 3,
        "required_adjacency_candidate_count": len(required_candidates),
        "criterion_result_count": len(_CRITERIA) * 3,
        "examined_failure_mode_count": sum(
            vote["examined_failure_modes"]["count"] for vote in votes
        ),
        "examined_omission_candidate_count": sum(
            vote["examined_omission_candidates"]["count"] for vote in votes
        ),
        "examined_adjacency_count": sum(
            vote["examined_adjacent_candidates"]["count"] for vote in votes
        ),
        "examined_required_adjacency_count": sum(
            vote["examined_adjacent_candidates"]["required_count"]
            for vote in votes
        ),
        "reviewer_added_adjacency_count": sum(
            len(
                vote["examined_adjacent_candidates"][
                    "reviewer_added_candidate_ids"
                ]
            )
            for vote in votes
        ),
        "proof_limit_count": sum(
            vote["proof_limits"]["count"] for vote in votes
        ),
    }
    if any(metrics[key] != value for key, value in expected_metric_subset.items()):
        raise AttestationError("expected professional evidence metrics are stale")
    result = {
        "qualification_coverage": {
            "required_expertise_tags": required_tags,
            "domain_voters": domain_voters,
            "architecture_voter": architecture_voter,
        },
        "criterion_vote_counts": criterion_counts,
        "domain_critical_defects": domain_defects,
        "ordinary_criterion_defects": ordinary_defects,
        "ordinary_criterion_disposition": ordinary_disposition,
        **majority,
        "final_disposition": final_disposition,
        "review_dependencies": {
            "skill_id": skill_id,
            "final_disposition": final_disposition,
            "evidence_complete": True,
            "prior_target_vote_count": 3,
            "required_candidate_ids": required_candidates,
            "reviewer_added_candidate_ids_union": added_ids,
            "dependency_candidate_ids": derived_dependency_ids,
        },
        "evidence_metrics": metrics,
    }
    if provenance["mode"] == "fresh":
        if origin_review_id != attestation["review_id"]:
            raise AttestationError("professional fresh origin is stale")
        for voter_id in domain_voters:
            reviewer = reviewer_pool.get(voter_id)
            if reviewer is None or _validate_pro_reviewer(
                reviewer,
                f"professional fresh reviewer {voter_id}",
                required_tags,
            )[1] != "domain":
                raise AttestationError("professional fresh domain reviewer is stale")
        architecture = reviewer_pool.get(architecture_voter)
        if architecture is None or _validate_pro_reviewer(
            architecture,
            f"professional fresh reviewer {architecture_voter}",
            required_tags,
        )[1] != "architecture":
            raise AttestationError(
                "professional fresh architecture reviewer is stale"
            )
    elif origin_review_id == attestation["review_id"]:
        raise AttestationError("professional carried origin is stale")
    if (
        provenance["mode"] == "carried"
        and final_disposition != "accepted-current-professional-completeness"
    ):
        raise AttestationError("only accepted direct origins may be carried")
    return (
        result,
        set(voter_ids) if provenance["mode"] == "fresh" else set(),
        provenance["mode"],
    )


def _derive_professional_target(
    row: dict[str, Any], *, attestation: dict[str, Any], populate: bool,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    skill_id = _slug(row["skill_id"], "professional skill_id")
    for field in ("package_fingerprint", "review_binding_fingerprint"):
        _sha(row[field], f"professional {field}")
    required_tags = _sorted_strings(row["required_expertise_tags"], "required expertise", nonempty=True)
    required_candidates = _sorted_strings(row["required_candidate_ids"], "required candidates")
    dependencies = row["dependency_material_fingerprints"]
    if not isinstance(dependencies, dict):
        raise AttestationError("dependency material fingerprints must be an object")
    for candidate_id, digest in dependencies.items():
        _slug(candidate_id, "dependency candidate")
        _sha(digest, "dependency material fingerprint")
    provenance = _closed(row["provenance"], _PROVENANCE_FIELDS, "professional provenance")
    if provenance["mode"] not in {"fresh", "carried"}:
        raise AttestationError("professional provenance mode is invalid")
    origin = _closed(provenance["origin"], _ORIGIN_FIELDS, "professional origin")
    origin_review_id = _slug(origin["review_id"], "origin review_id")
    origin_date = _iso_date(origin["decided_on"], "origin decided_on")
    if type(origin["origin_depth"]) is not int or origin["origin_depth"] != 0:
        raise AttestationError("professional origin must be depth zero")
    for field in ("review_contract_fingerprint", "package_fingerprint", "review_binding_fingerprint"):
        _sha(origin[field], f"origin {field}")
    origin_tags = _sorted_strings(origin["required_expertise_tags"], "origin required expertise", nonempty=True)
    origin_required = _sorted_strings(origin["required_candidate_ids"], "origin required candidates")
    origin_dependencies = origin["dependency_material_fingerprints"]
    if not isinstance(origin_dependencies, dict):
        raise AttestationError("origin dependency fingerprints must be an object")
    for candidate_id, digest in origin_dependencies.items():
        _slug(candidate_id, "origin dependency candidate")
        _sha(digest, "origin dependency fingerprint")
    if (
        origin["review_contract_fingerprint"] != attestation["review_contract_fingerprint"]
        or origin["package_fingerprint"] != row["package_fingerprint"]
        or origin["review_binding_fingerprint"] != row["review_binding_fingerprint"]
        or origin_tags != required_tags or origin_required != required_candidates
        or origin_dependencies != dependencies
    ):
        raise AttestationError("professional origin binding is stale")
    votes = origin["votes"]
    if (
        not isinstance(votes, list)
        or len(votes) != panel_contracts.PROFESSIONAL_PANEL_SIZE
    ):
        raise AttestationError("professional origin requires exactly three votes")
    kinds = []
    voter_ids = []
    agent_ids = []
    reviewer_rows = []
    for index, vote_raw in enumerate(votes):
        vote, kind = _validate_professional_vote(
            vote_raw, skill_id=skill_id, required_tags=required_tags,
            required_candidates=required_candidates, label=f"professional votes[{index}]",
        )
        kinds.append(kind)
        reviewer_rows.append(vote["reviewer"])
        voter_ids.append(vote["reviewer"]["voter_id"])
        agent_ids.append(vote["reviewer"]["agent_id"])
    if voter_ids != sorted(set(voter_ids)) or len(agent_ids) != len(set(agent_ids)):
        raise AttestationError("professional effective reviewer identities are invalid")
    if kinds.count("domain") != 2 or kinds.count("architecture") != 1:
        raise AttestationError("professional target requires two domain and one architecture vote")
    added_ids = sorted({
        item["skill_id"] for vote in votes
        for item in vote["examined_adjacent_candidates"]
        if item["review_origin"] == "reviewer-added"
    })
    dependency_ids = sorted(set(required_candidates) | set(added_ids))
    if set(dependencies) != set(dependency_ids):
        raise AttestationError("professional dependency fingerprint coverage is stale")
    expected_origin_fingerprint = professional_origin_fingerprint(origin)
    if populate:
        origin["origin_fingerprint"] = expected_origin_fingerprint
    elif origin["origin_fingerprint"] != expected_origin_fingerprint:
        raise AttestationError("professional origin fingerprint is stale")
    if provenance["mode"] == "fresh":
        if origin_review_id != attestation["review_id"] or origin_date != attestation["decided_on"] or origin["package_fingerprint"] != row["package_fingerprint"]:
            raise AttestationError("professional fresh origin is stale")
    elif origin_review_id == attestation["review_id"] or origin_date > attestation["decided_on"]:
        raise AttestationError("professional carried origin is stale")
    criterion_counts = {
        criterion: {value: sum(vote["criteria"][criterion]["status"] == value for vote in votes)
                    for value in sorted(_CRITERION_VALUES)}
        for criterion in sorted(_CRITERIA)
    }
    domain_votes = [vote for vote, kind in zip(votes, kinds, strict=True) if kind == "domain"]
    domain_defects = sorted(
        [
            {
                "criterion": criterion,
                "voter_id": vote["reviewer"]["voter_id"],
            }
            for vote in domain_votes
            for criterion in _CRITICAL_CRITERIA
            if vote["criteria"][criterion]["status"] == "defect-found"
        ],
        key=lambda item: (item["criterion"], item["voter_id"]),
    )
    ordinary_defects = [criterion for criterion in sorted(_ORDINARY_CRITERIA)
                        if criterion_counts[criterion]["defect-found"] >= 2]
    ordinary_disposition = (
        "requires-professional-correction" if ordinary_defects
        else "accepted-current-professional-completeness"
    )
    final_disposition = (
        "unresolved-professional-disagreement" if domain_defects else ordinary_disposition
    )
    majority = _majority([
        {"voter_id": vote["reviewer"]["voter_id"], "disposition": vote["decision"]}
        for vote in votes
    ], _PRO_DECISIONS)
    metrics = {
        "target_vote_count": 3,
        "required_adjacency_candidate_count": len(required_candidates),
        "criterion_result_count": sum(len(vote["criteria"]) for vote in votes),
        "criterion_anchor_binding_count": sum(
            len(assertion["evidence_anchor_ids"]) for vote in votes
            for result in vote["criteria"].values()
            for assertion in result["evidence_assertions"]
        ),
        "criterion_assertion_count": sum(
            len(result["evidence_assertions"]) for vote in votes
            for result in vote["criteria"].values()
        ),
        "evidence_anchor_count": sum(len(vote["evidence_anchors"]) for vote in votes),
        "examined_failure_mode_count": sum(len(vote["examined_failure_modes"]) for vote in votes),
        "examined_omission_candidate_count": sum(len(vote["examined_omission_candidates"]) for vote in votes),
        "examined_adjacency_count": sum(len(vote["examined_adjacent_candidates"]) for vote in votes),
        "examined_required_adjacency_count": sum(
            item["review_origin"] == "packet-required" for vote in votes
            for item in vote["examined_adjacent_candidates"]
        ),
        "reviewer_added_adjacency_count": sum(
            item["review_origin"] == "reviewer-added" for vote in votes
            for item in vote["examined_adjacent_candidates"]
        ),
        "proof_limit_count": sum(len(vote["proof_limits"]) for vote in votes),
        "qualification_claim_count": sum(len(vote["reviewer"]["qualification_claims"]) for vote in votes),
    }
    result = {
        "qualification_coverage": {
            "required_expertise_tags": required_tags,
            "domain_voters": sorted(vote["reviewer"]["voter_id"] for vote in domain_votes),
            "architecture_voter": next(vote["reviewer"]["voter_id"] for vote, kind in zip(votes, kinds, strict=True) if kind == "architecture"),
        },
        "criterion_vote_counts": criterion_counts,
        "domain_critical_defects": domain_defects,
        "ordinary_criterion_defects": ordinary_defects,
        "ordinary_criterion_disposition": ordinary_disposition,
        **majority,
        "final_disposition": final_disposition,
        "review_dependencies": {
            "skill_id": skill_id, "final_disposition": final_disposition,
            "evidence_complete": True, "prior_target_vote_count": 3,
            "required_candidate_ids": required_candidates,
            "reviewer_added_candidate_ids_union": added_ids,
            "dependency_candidate_ids": dependency_ids,
        },
        "evidence_metrics": metrics,
    }
    if provenance["mode"] == "carried" and final_disposition != "accepted-current-professional-completeness":
        raise AttestationError("only accepted depth-zero origins may be carried")
    _text(row["rationale"], "professional target rationale")
    return result, {reviewer["voter_id"]: reviewer for reviewer in reviewer_rows}, provenance["mode"]


def _disposition_counts(rows: list[dict[str, Any]], field: str, values: set[str]) -> dict[str, int]:
    return {value: sum(row[field] == value for row in rows) for value in sorted(values)}


def _sum_metrics(results: list[dict[str, Any]]) -> dict[str, int]:
    return {key: sum(result["evidence_metrics"][key] for result in results)
            for key in sorted(_EVIDENCE_METRIC_KEYS)}


def _derive_professional_review_cost(
    value: object, *, fresh_target_count: int, carried_target_count: int,
    maximum_origin_depth: int,
) -> dict[str, Any]:
    """Validate promotion-supplied proxies and derive the durable policy result."""

    inputs = _closed(
        value, PROFESSIONAL_REVIEW_COST_INPUT_FIELDS,
        "professional review_cost_input",
    )
    integer_fields = PROFESSIONAL_REVIEW_COST_INPUT_FIELDS - {
        "formal_round_policy_fingerprint", "policy_status",
    }
    if any(type(inputs[field]) is not int or inputs[field] < 0 for field in integer_fields):
        raise AttestationError("professional review-cost inputs must be non-negative integers")
    if (
        inputs["formal_round_policy_fingerprint"]
        != PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FINGERPRINT
    ):
        raise AttestationError("professional formal-round policy fingerprint is stale")
    _text(inputs["policy_status"], "professional review-cost policy_status")
    if inputs["plan_lineage_depth"] > 8 or maximum_origin_depth > 1:
        raise AttestationError("professional review-cost lineage bounds are stale")

    actual = inputs["canonical_capsule_input_bytes_proxy"]
    denominator = inputs[
        "full_rereview_deduplicated_capsule_input_bytes_proxy"
    ]
    required = inputs["required_only_capsule_input_bytes_proxy"]
    required_source = inputs[
        "required_only_source_material_input_bytes_proxy"
    ]
    actual_source = inputs["source_material_input_bytes_proxy"]
    full_source = inputs["full_rereview_source_material_input_bytes_proxy"]
    if (
        denominator <= 0 or full_source <= 0 or required > actual
        or required_source > actual_source or actual_source > full_source
        or actual < actual_source or required < required_source
    ):
        raise AttestationError("professional review-cost decomposition is invalid")
    actual_metadata = actual - actual_source
    required_metadata = required - required_source
    if actual_metadata < required_metadata:
        raise AttestationError("professional review-cost metadata overhead is negative")
    metadata_overhead = actual_metadata - required_metadata
    metadata_overhead_ratio = (
        metadata_overhead * 1_000_000 // required_metadata
        if required_metadata else 0
    )
    policy = PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY
    if (
        metadata_overhead * 1_000_000
        > policy[
            "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ] * required_metadata
        or inputs["maximum_reviewer_added_unique_union_to_required_ratio_ppm"]
        > policy[
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ]
    ):
        raise AttestationError("professional review-cost formal budget is exceeded")
    request_count = inputs["reviewer_added_request_count"]
    relationship_count = inputs["reviewer_added_unique_relationship_count"]
    maximum_union_ratio = inputs[
        "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
    ]
    if (
        relationship_count > request_count
        or request_count > 3 * relationship_count
        or (relationship_count == 0 and maximum_union_ratio != 0)
    ):
        raise AttestationError("professional reviewer-added accounting is invalid")

    total = fresh_target_count + carried_target_count
    status = inputs["policy_status"]
    input_ratio = actual * 1_000_000 // denominator
    required_ratio = required * 1_000_000 // denominator
    source_ratio = actual_source * 1_000_000 // full_source
    if fresh_target_count == 0:
        zero_inputs = (
            actual, required, required_source, actual_source, request_count,
            relationship_count, maximum_union_ratio, input_ratio,
            required_ratio, source_ratio, metadata_overhead,
        )
        if any(zero_inputs) or status != "all-carry-zero-input":
            raise AttestationError("professional all-carry review cost is not zero-input")
    elif fresh_target_count < total:
        if not (
            0 < required < denominator
            and 0 < required_source <= actual_source <= full_source
            and 0 < required_ratio < 1_000_000
            and required_metadata > 0
            and status == "incremental-reduced-input"
        ):
            raise AttestationError("professional incremental review-cost policy is invalid")
    elif not (
        required == denominator
        and required_ratio == 1_000_000
        and required_source == full_source
        and source_ratio
        == policy["full_fresh_source_material_coverage_ratio_ppm"]
        and required_metadata > 0
        and status in {
            "bootstrap-full-review", "contract-change-full-review",
            "lineage-checkpoint-full-review", "full-fresh-review",
        }
    ):
        raise AttestationError("professional full-fresh review-cost policy is invalid")

    return {
        "fresh_vote_count": 3 * fresh_target_count,
        "carried_forward_vote_count": 3 * carried_target_count,
        "effective_vote_count": 3 * total,
        "fresh_criterion_result_count": 3 * len(_CRITERIA) * fresh_target_count,
        "carried_forward_criterion_result_count": (
            3 * len(_CRITERIA) * carried_target_count
        ),
        "effective_criterion_result_count": 3 * len(_CRITERIA) * total,
        "canonical_capsule_input_bytes_proxy": actual,
        "full_rereview_deduplicated_capsule_input_bytes_proxy": denominator,
        "input_ratio_ppm": input_ratio,
        "required_only_capsule_input_bytes_proxy": required,
        "required_only_input_ratio_ppm": required_ratio,
        "required_only_source_material_input_bytes_proxy": required_source,
        "source_material_input_bytes_proxy": actual_source,
        "full_rereview_source_material_input_bytes_proxy": full_source,
        "source_material_coverage_ratio_ppm": source_ratio,
        "reviewer_added_source_material_input_bytes_proxy": (
            actual_source - required_source
        ),
        "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": (
            metadata_overhead
        ),
        "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": (
            metadata_overhead_ratio
        ),
        "reviewer_added_request_count": request_count,
        "reviewer_added_unique_relationship_count": relationship_count,
        "maximum_reviewer_added_unique_union_to_required_ratio_ppm": (
            maximum_union_ratio
        ),
        "formal_round_policy_fingerprint": (
            PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FINGERPRINT
        ),
        "maximum_origin_depth": maximum_origin_depth,
        "plan_lineage_depth": inputs["plan_lineage_depth"],
        "policy_status": status,
        "limitations": copy.deepcopy(PROFESSIONAL_REVIEW_COST_LIMITATIONS),
    }


def _derive_professional(
    attestation: dict[str, Any], *, populate: bool
) -> tuple[dict[str, Any], str]:
    if not isinstance(attestation["reviewers"], list):
        raise AttestationError("professional reviewers must be an array")
    findings = attestation["findings"]
    if not isinstance(findings, list) or not findings:
        raise AttestationError("professional findings must be non-empty")
    results = []
    modes = []
    fresh_reviewers: dict[str, dict[str, Any]] = {}
    skill_ids = []
    for index, raw in enumerate(findings):
        row = _closed(raw, _PRO_FINDING_FIELDS, f"findings[{index}]")
        skill_ids.append(row["skill_id"])
        result, origin_reviewers, mode = _derive_professional_target(
            row, attestation=attestation, populate=populate
        )
        row["result"] = result
        results.append(result)
        modes.append(mode)
        if mode == "fresh":
            for voter_id, reviewer in origin_reviewers.items():
                existing = fresh_reviewers.get(voter_id)
                if existing is not None and existing != reviewer:
                    raise AttestationError("fresh reviewer metadata conflicts across targets")
                fresh_reviewers[voter_id] = reviewer
    if skill_ids != sorted(set(skill_ids)):
        raise AttestationError("professional targets must be Skill-sorted and unique")
    actual_pool = _validate_reviewer_pool(
        attestation["reviewers"], professional=True, allow_empty=True
    )
    if actual_pool != fresh_reviewers:
        raise AttestationError("professional fresh reviewer pool is stale")
    fresh_results = [result for result, mode in zip(results, modes, strict=True) if mode == "fresh"]
    carried_results = [result for result, mode in zip(results, modes, strict=True) if mode == "carried"]
    disposition_group = lambda subset, field, values: _disposition_counts(subset, field, values)
    maximum_origin_depth = max(
        row["provenance"]["origin"]["origin_depth"] for row in findings
    )
    review_cost = _derive_professional_review_cost(
        attestation["review_cost_input"],
        fresh_target_count=len(fresh_results),
        carried_target_count=len(carried_results),
        maximum_origin_depth=maximum_origin_depth,
    )
    summary = {
        "partition": {
            "fresh_target_count": len(fresh_results),
            "carried_target_count": len(carried_results),
            "effective_target_count": len(results),
        },
        "professional_completeness": {
            "fresh": disposition_group(fresh_results, "final_disposition", _FINAL_DISPOSITIONS),
            "carried": disposition_group(carried_results, "final_disposition", _FINAL_DISPOSITIONS),
            "effective": disposition_group(results, "final_disposition", _FINAL_DISPOSITIONS),
        },
        "ordinary_criterion_majority": {
            "fresh": disposition_group(fresh_results, "ordinary_criterion_disposition", _PRO_DECISIONS),
            "carried": disposition_group(carried_results, "ordinary_criterion_disposition", _PRO_DECISIONS),
            "effective": disposition_group(results, "ordinary_criterion_disposition", _PRO_DECISIONS),
        },
        "overall_ballot_majority_audit": {
            "fresh": disposition_group(fresh_results, "winning_disposition", _PRO_DECISIONS),
            "carried": disposition_group(carried_results, "winning_disposition", _PRO_DECISIONS),
            "effective": disposition_group(results, "winning_disposition", _PRO_DECISIONS),
        },
        "qualification": {
            "fresh_target_count": len(fresh_results),
            "carried_target_count": len(carried_results),
            "effective_covered_target_count": len(results),
            "required_domain_experts_per_fresh_target": 2,
            "required_architecture_experts_per_fresh_target": 1,
            "fresh_reviewer_pool_size": len(actual_pool),
        },
        "evidence": {
            "fresh": _sum_metrics(fresh_results),
            "carried": _sum_metrics(carried_results),
            "effective": _sum_metrics(results),
        },
        "review_cost": review_cost,
    }
    final_dispositions = [result["final_disposition"] for result in results]
    verdict = (
        "unresolved-professional-disagreement"
        if "unresolved-professional-disagreement" in final_dispositions
        else (
            "requires-professional-correction"
            if "requires-professional-correction" in final_dispositions
            else "accepted-current-professional-completeness"
        )
    )
    return summary, verdict


def _derive_compact_professional(
    attestation: dict[str, Any],
    *,
    populate: bool,
    expected_current_bindings: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Derive Professional results from compact conclusions plus current authority."""

    if not isinstance(attestation["reviewers"], list):
        raise AttestationError("professional reviewers must be an array")
    findings = attestation["findings"]
    if not isinstance(findings, list) or not findings:
        raise AttestationError("professional findings must be non-empty")
    if not isinstance(expected_current_bindings, dict):
        raise AttestationError(
            "Professional validation requires authoritative current bindings"
        )
    dependency_catalog = attestation["dependency_material_catalog"]
    if (
        not isinstance(dependency_catalog, dict)
        or list(dependency_catalog) != sorted(dependency_catalog)
    ):
        raise AttestationError(
            "Professional dependency material catalog is invalid"
        )
    for candidate_id, digest in dependency_catalog.items():
        _slug(candidate_id, "professional dependency catalog ID")
        _sha(digest, "professional dependency catalog binding")
    finding_ids = [
        row.get("skill_id") if isinstance(row, dict) else None for row in findings
    ]
    if (
        finding_ids != sorted(set(finding_ids))
        or set(finding_ids) != set(expected_current_bindings)
    ):
        raise AttestationError(
            "Professional current binding coverage is incomplete"
        )
    normalized_bindings: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(expected_current_bindings):
        _slug(skill_id, "expected professional skill_id")
        authority = _closed(
            expected_current_bindings[skill_id],
            _COMPACT_PRO_AUTHORITY_FIELDS,
            f"expected professional binding {skill_id}",
        )
        for field in ("package_material_binding", "review_unit_binding"):
            _sha(authority[field], f"expected professional {field}")
        _sorted_strings(
            authority["required_expertise_tags"],
            f"expected professional {skill_id} expertise",
            nonempty=True,
        )
        _sorted_strings(
            authority["required_candidate_ids"],
            f"expected professional {skill_id} candidates",
        )
        selection_version = authority["selection_contract_version"]
        if not isinstance(selection_version, str) or not selection_version:
            raise AttestationError(
                "expected professional selection contract version is invalid"
            )
        required_dependencies = authority[
            "required_candidate_material_bindings"
        ]
        added_ids = _sorted_strings(
            authority["reviewer_added_candidate_ids_union"],
            f"expected professional {skill_id} reviewer-added candidates",
        )
        added_dependencies = authority[
            "reviewer_added_candidate_material_bindings"
        ]
        if (
            not isinstance(required_dependencies, dict)
            or set(required_dependencies) != set(authority["required_candidate_ids"])
            or not isinstance(added_dependencies, dict)
            or set(added_dependencies) != set(added_ids)
            or set(added_ids) & set(authority["required_candidate_ids"])
        ):
            raise AttestationError(
                "expected professional dependency bindings are invalid"
            )
        for candidate_id, digest in {
            **required_dependencies,
            **added_dependencies,
        }.items():
            _slug(candidate_id, "expected professional dependency candidate")
            _sha(digest, "expected professional dependency fingerprint")
        vote_authorities = authority["vote_authorities"]
        if not isinstance(vote_authorities, dict) or len(vote_authorities) != 3:
            raise AttestationError(
                "expected professional vote authority is incomplete"
            )
        for voter_id, vote in vote_authorities.items():
            _slug(voter_id, "expected professional evidence voter")
            if not isinstance(vote, dict) or vote.get("reviewer") != voter_id:
                raise AttestationError(
                    "expected professional vote authority is invalid"
                )
        _closed(
            authority["reviewer_partition"],
            _COMPACT_REVIEWER_PARTITION_FIELDS,
            f"expected professional reviewer partition {skill_id}",
        )
        metrics = authority["evidence_metrics"]
        if not isinstance(metrics, dict) or set(metrics) != _EVIDENCE_METRIC_KEYS:
            raise AttestationError(
                "expected professional evidence metrics are incomplete"
            )
        expected_origin = _closed(
            authority["origin"],
            _COMPACT_PRO_ORIGIN_FIELDS,
            f"expected professional origin {skill_id}",
        )
        _slug(
            expected_origin["origin_review_id"],
            "expected professional origin review_id",
        )
        if not isinstance(expected_origin["origin_commit"], str) or re.fullmatch(
            r"[0-9a-f]{40}", expected_origin["origin_commit"]
        ) is None:
            raise AttestationError(
                "expected professional origin commit is invalid"
            )
        _sha(
            expected_origin["origin_verdict_digest"],
            "expected professional origin verdict digest",
        )
        normalized_bindings[skill_id] = authority

    actual_pool = _validate_reviewer_pool(
        attestation["reviewers"], professional=True, allow_empty=True
    )
    results = []
    modes = []
    fresh_voter_ids: set[str] = set()
    for index, raw in enumerate(findings):
        row = _closed(raw, _COMPACT_PRO_FINDING_FIELDS, f"findings[{index}]")
        authority = normalized_bindings[row["skill_id"]]
        if any(
            row[field] != authority[field]
            for field in (
                "package_material_binding",
                "review_unit_binding",
                "required_expertise_tags",
            )
        ):
            raise AttestationError(
                f"Professional current binding for {row['skill_id']} is stale"
            )
        result, origin_reviewers, mode = _derive_compact_professional_target(
            row,
            attestation=attestation,
            expected_authority=authority,
            reviewer_pool=actual_pool,
            dependency_material_catalog=dependency_catalog,
        )
        expected_dependencies = {
            **authority["required_candidate_material_bindings"],
            **authority[
                "reviewer_added_candidate_material_bindings"
            ],
        }
        if (
            result["review_dependencies"]["required_candidate_ids"]
            != authority["required_candidate_ids"]
            or result["review_dependencies"][
                "reviewer_added_candidate_ids_union"
            ]
            != authority["reviewer_added_candidate_ids_union"]
            or set(expected_dependencies)
            != set(result["review_dependencies"]["dependency_candidate_ids"])
            or row["dependency_ids"] != sorted(expected_dependencies)
            or any(
                dependency_catalog[candidate_id] != digest
                for candidate_id, digest in expected_dependencies.items()
            )
        ):
            raise AttestationError(
                f"Professional dependency binding for {row['skill_id']} is stale"
            )
        row["result"] = result
        results.append(result)
        modes.append(mode)
        if mode == "fresh":
            fresh_voter_ids.update(origin_reviewers)
    if set(dependency_catalog) != {
        candidate_id
        for row in findings
        for candidate_id in row["dependency_ids"]
    }:
        raise AttestationError(
            "Professional dependency material catalog coverage is stale"
        )
    if set(actual_pool) != fresh_voter_ids:
        raise AttestationError("professional fresh reviewer pool is stale")
    fresh_results = [
        result
        for result, mode in zip(results, modes, strict=True)
        if mode == "fresh"
    ]
    carried_results = [
        result
        for result, mode in zip(results, modes, strict=True)
        if mode == "carried"
    ]
    disposition_group = lambda subset, field, values: _disposition_counts(
        subset, field, values
    )
    review_cost = _derive_professional_review_cost(
        attestation["review_cost_input"],
        fresh_target_count=len(fresh_results),
        carried_target_count=len(carried_results),
        maximum_origin_depth=1 if carried_results else 0,
    )
    summary = {
        "partition": {
            "fresh_target_count": len(fresh_results),
            "carried_target_count": len(carried_results),
            "effective_target_count": len(results),
        },
        "professional_completeness": {
            "fresh": disposition_group(
                fresh_results, "final_disposition", _FINAL_DISPOSITIONS
            ),
            "carried": disposition_group(
                carried_results, "final_disposition", _FINAL_DISPOSITIONS
            ),
            "effective": disposition_group(
                results, "final_disposition", _FINAL_DISPOSITIONS
            ),
        },
        "ordinary_criterion_majority": {
            "fresh": disposition_group(
                fresh_results, "ordinary_criterion_disposition", _PRO_DECISIONS
            ),
            "carried": disposition_group(
                carried_results, "ordinary_criterion_disposition", _PRO_DECISIONS
            ),
            "effective": disposition_group(
                results, "ordinary_criterion_disposition", _PRO_DECISIONS
            ),
        },
        "overall_ballot_majority_audit": {
            "fresh": disposition_group(
                fresh_results, "winning_disposition", _PRO_DECISIONS
            ),
            "carried": disposition_group(
                carried_results, "winning_disposition", _PRO_DECISIONS
            ),
            "effective": disposition_group(
                results, "winning_disposition", _PRO_DECISIONS
            ),
        },
        "qualification": {
            "fresh_target_count": len(fresh_results),
            "carried_target_count": len(carried_results),
            "effective_covered_target_count": len(results),
            "required_domain_experts_per_fresh_target": 2,
            "required_architecture_experts_per_fresh_target": 1,
            "fresh_reviewer_pool_size": len(actual_pool),
        },
        "evidence": {
            "fresh": _sum_metrics(fresh_results),
            "carried": _sum_metrics(carried_results),
            "effective": _sum_metrics(results),
        },
        "review_cost": review_cost,
    }
    final_dispositions = [result["final_disposition"] for result in results]
    verdict = (
        "unresolved-professional-disagreement"
        if "unresolved-professional-disagreement" in final_dispositions
        else (
            "requires-professional-correction"
            if "requires-professional-correction" in final_dispositions
            else "accepted-current-professional-completeness"
        )
    )
    return summary, verdict


def _envelope(value: object, expected_path: str | None) -> tuple[dict[str, Any], str]:
    _forbidden(value)
    fields = _COMMON_FIELDS
    if isinstance(value, dict):
        if value.get("axis") == PROFESSIONAL_COMPLETENESS_AXIS:
            fields = _PRO_ATTESTATION_FIELDS
        elif value.get("axis") == READABILITY_AXIS:
            fields = _READABILITY_ATTESTATION_FIELDS
    attestation = _closed(value, fields, "attestation")
    if (
        type(attestation["schema_version"]) is not int
        or attestation["schema_version"] != ATTESTATION_SCHEMA_VERSION
    ):
        raise AttestationError("attestation schema_version is invalid")
    axis = attestation["axis"]
    if axis not in _KINDS or attestation["kind"] != _KINDS[axis]:
        raise AttestationError("attestation axis or kind is invalid")
    if expected_path is not None and attestation_axis_for_path(expected_path) != axis:
        raise AttestationError("attestation path cannot substitute across axes")
    _slug(attestation["review_id"], "attestation.review_id")
    _iso_date(attestation["decided_on"], "attestation.decided_on")
    sources = attestation.get("source_fingerprints")
    if axis == READABILITY_AXIS:
        readability_source_fingerprint_shape(sources)
        _readability_review_artifacts(attestation["review_artifacts"])
    elif axis == SEMANTIC_DISPOSITION_AXIS:
        semantic_source_fingerprint_shape(sources)
    elif axis != PROFESSIONAL_COMPLETENESS_AXIS:
        raise AttestationError("source fingerprint fields are not closed")
    if sources is not None:
        for key, digest in sources.items():
            _sha(digest, f"source_fingerprints.{key}")
    contract = _sha(attestation["review_contract_fingerprint"], "review contract")
    _sorted_strings(attestation["rationale"], "attestation rationale", nonempty=True)
    if not isinstance(attestation["findings"], list):
        raise AttestationError("attestation findings must be an array")
    return attestation, axis


def _derive(
    value: object,
    *,
    expected_path: str | None,
    populate: bool,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
    expected_semantic_current_bindings: dict[str, dict[str, Any]] | None = None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    attestation, axis = _envelope(value, expected_path)
    if axis == READABILITY_AXIS:
        if expected_readability_current_bindings is None:
            raise AttestationError(
                "Readability validation requires authoritative current bindings"
            )
        summary, verdict = _derive_readability(
            attestation,
            expected_current_bindings=expected_readability_current_bindings,
        )
    elif axis == SEMANTIC_DISPOSITION_AXIS:
        if expected_semantic_current_bindings is None:
            raise AttestationError(
                "Semantic validation requires authoritative current fingerprints"
            )
        summary, verdict = _derive_compact_semantic(
            attestation,
            expected_current_bindings=expected_semantic_current_bindings,
        )
    else:
        if expected_professional_current_bindings is None:
            raise AttestationError(
                "Professional validation requires authoritative current bindings"
            )
        summary, verdict = _derive_compact_professional(
            attestation,
            populate=populate,
            expected_current_bindings=expected_professional_current_bindings,
        )
    attestation["summary"] = summary
    attestation["verdict"] = verdict
    if axis == READABILITY_AXIS:
        expected_manifest = readability_target_manifest_fingerprint(
            expected_readability_current_bindings
        )
        if attestation["source_fingerprints"].get(
            "readability_target_manifest"
        ) != expected_manifest:
            raise AttestationError(
                "readability target manifest binding is stale"
            )
    elif axis == SEMANTIC_DISPOSITION_AXIS:
        by_axis = {"root": {}, "reference": {}}
        for target_id, authority in expected_semantic_current_bindings.items():
            semantic_axis = target_id.split(":", 1)[0]
            by_axis[semantic_axis][target_id] = authority[
                "candidate_binding_fingerprint"
            ]
        attestation["source_fingerprints"][
            "root_candidate_manifest"
        ] = canonical_json_sha256(by_axis["root"])
        attestation["source_fingerprints"][
            "reference_candidate_manifest"
        ] = canonical_json_sha256(by_axis["reference"])
    return attestation


def finalize_attestation(
    value: object,
    *,
    expected_path: str | None = None,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
    expected_semantic_current_bindings: dict[str, dict[str, Any]] | None = None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Populate every deterministic fingerprint, result, summary, and verdict."""

    candidate = _derive(
        copy.deepcopy(value),
        expected_path=expected_path,
        populate=True,
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
        expected_semantic_current_bindings=expected_semantic_current_bindings,
        expected_professional_current_bindings=expected_professional_current_bindings,
    )
    validate_attestation(
        candidate,
        expected_path=expected_path,
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
        expected_semantic_current_bindings=expected_semantic_current_bindings,
        expected_professional_current_bindings=expected_professional_current_bindings,
    )
    return candidate


def validate_attestation(
    value: object, *, expected_path: str | None = None,
    expected_source_fingerprints: dict[str, str] | None = None,
    expected_review_contract_fingerprint: str | None = None,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
    expected_semantic_current_bindings: dict[str, dict[str, Any]] | None = None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Reject evidence whose deterministic claims cannot be recomputed."""

    if isinstance(value, dict):
        if (
            value.get("axis") == READABILITY_AXIS
            and expected_readability_current_bindings is None
        ):
            raise AttestationError(
                "Readability validation requires authoritative current bindings"
            )
        if (
            value.get("axis") == SEMANTIC_DISPOSITION_AXIS
            and expected_semantic_current_bindings is None
        ):
            raise AttestationError(
                "Semantic validation requires authoritative current fingerprints"
            )
        if (
            value.get("axis") == PROFESSIONAL_COMPLETENESS_AXIS
            and expected_professional_current_bindings is None
        ):
            raise AttestationError(
                "Professional validation requires authoritative current bindings"
            )
    original = copy.deepcopy(value)
    derived = _derive(
        copy.deepcopy(value),
        expected_path=expected_path,
        populate=False,
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
        expected_semantic_current_bindings=expected_semantic_current_bindings,
        expected_professional_current_bindings=expected_professional_current_bindings,
    )
    if original != derived:
        raise AttestationError("attestation derived results or summary are stale")
    if expected_source_fingerprints is not None:
        if derived["axis"] == PROFESSIONAL_COMPLETENESS_AXIS:
            raise AttestationError(
                "Professional source fingerprints are not current authority"
            )
        if derived["source_fingerprints"] != expected_source_fingerprints:
            raise AttestationError("attestation source fingerprints are stale")
    if expected_review_contract_fingerprint is not None and derived["review_contract_fingerprint"] != expected_review_contract_fingerprint:
        raise AttestationError("attestation review contract fingerprint is stale")
    if expected_semantic_current_bindings is not None:
        if derived["axis"] != SEMANTIC_DISPOSITION_AXIS:
            raise AttestationError("Semantic current bindings require Semantic evidence")
        if not isinstance(expected_semantic_current_bindings, dict):
            raise AttestationError("expected Semantic current bindings are invalid")
        expected_pairs = {}
        for target_id, raw in expected_semantic_current_bindings.items():
            if not isinstance(raw, dict):
                raise AttestationError(
                    "expected Semantic current bindings are incomplete"
                )
            target_parts = target_id.split(":") if isinstance(target_id, str) else []
            if len(target_parts) != 2 or target_parts[0] not in {
                "root",
                "reference",
            }:
                raise AttestationError(
                    "expected Semantic current binding target is invalid"
                )
            _sha(target_parts[1], "expected Semantic candidate_id")
            if set(raw) == {
                "candidate_binding_fingerprint",
                "reviewed_rewrite",
            }:
                if raw["reviewed_rewrite"] is not True:
                    raise AttestationError(
                        "expected Semantic reviewed rewrite is invalid"
                    )
                expected_pairs[target_id] = {
                    "candidate_binding_fingerprint": _sha(
                        raw["candidate_binding_fingerprint"],
                        "expected Semantic reviewed rewrite binding",
                    )
                }
                continue
            if set(raw) != {
                "candidate", "candidate_binding_fingerprint",
            }:
                raise AttestationError(
                    "expected Semantic current bindings are incomplete"
                )
            candidate = _validate_semantic_candidate(
                raw["candidate"],
                axis=target_parts[0],
                label=f"expected Semantic candidate {target_id}",
            )
            if candidate["candidate_id"] != target_parts[1]:
                raise AttestationError(
                    "expected Semantic candidate authority identity is stale"
                )
            recomputed = semantic_candidate_fingerprints(
                axis=target_parts[0], candidate=candidate
            )
            if recomputed != {
                "candidate_binding_fingerprint": raw[
                    "candidate_binding_fingerprint"
                ]
            }:
                raise AttestationError(
                    "expected Semantic current binding digests are stale"
                )
            expected_pairs[target_id] = recomputed
        actual_bindings = {
            row["target_id"]: {
                "candidate_binding_fingerprint": row[
                    "candidate_binding_fingerprint"
                ]
            }
            for row in derived["findings"]
        }
        if actual_bindings != expected_pairs:
            raise AttestationError("semantic candidate fingerprints are stale")
    return derived


def _bounded(payload: bytes) -> bytes:
    if len(payload) > MAX_ATTESTATION_BYTES:
        raise AttestationError(
            f"attestation exceeds 4 MiB; actual={len(payload)}"
        )
    return payload


def _professional_storage_string_counts(
    value: dict[str, Any],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    def visit(item: object) -> None:
        if isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, str):
            counts[item] = counts.get(item, 0) + 1

    try:
        for field, child in value.items():
            if field not in _PROFESSIONAL_STORAGE_ROUTING_FIELDS:
                visit(child)
    except RecursionError as exc:
        raise AttestationError(
            "Professional storage nesting exceeds the codec limit"
        ) from exc
    return counts


def _encode_professional_storage_in_place(value: dict[str, Any]) -> None:
    """Intern repeated non-routing strings in one validated compact tree."""

    counts = _professional_storage_string_counts(value)
    catalog = sorted(text for text, count in counts.items() if count >= 2)
    if any(unicodedata.normalize("NFC", text) != text for text in catalog):
        raise AttestationError(
            "Professional storage string catalog must use canonical Unicode"
        )
    references = {text: -(index + 1) for index, text in enumerate(catalog)}

    def replace(item: object) -> None:
        if isinstance(item, dict):
            for field, child in item.items():
                if isinstance(child, str) and child in references:
                    item[field] = references[child]
                else:
                    replace(child)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                if isinstance(child, str) and child in references:
                    item[index] = references[child]
                else:
                    replace(child)

    try:
        for field, child in value.items():
            if field in _PROFESSIONAL_STORAGE_ROUTING_FIELDS:
                continue
            if isinstance(child, str) and child in references:
                value[field] = references[child]
            else:
                replace(child)
    except RecursionError as exc:
        raise AttestationError(
            "Professional storage nesting exceeds the codec limit"
        ) from exc
    value[PROFESSIONAL_STORAGE_ENCODING_FIELD] = (
        PROFESSIONAL_STORAGE_ENCODING
    )
    value[PROFESSIONAL_STRING_CATALOG_FIELD] = catalog


def _decode_professional_storage_in_place(value: dict[str, Any]) -> None:
    """Expand one closed canonical Professional physical storage object."""

    _closed(
        value,
        _PROFESSIONAL_STORAGE_FIELDS,
        "Professional physical storage",
    )
    if value.get(PROFESSIONAL_STORAGE_ENCODING_FIELD) != (
        PROFESSIONAL_STORAGE_ENCODING
    ):
        raise AttestationError("Professional storage encoding is invalid")
    catalog = value.get(PROFESSIONAL_STRING_CATALOG_FIELD)
    if (
        not isinstance(catalog, list)
        or not all(isinstance(text, str) for text in catalog)
        or catalog != sorted(set(catalog))
        or any(unicodedata.normalize("NFC", text) != text for text in catalog)
    ):
        raise AttestationError(
            "Professional storage string catalog is not canonical"
        )
    value.pop(PROFESSIONAL_STORAGE_ENCODING_FIELD)
    value.pop(PROFESSIONAL_STRING_CATALOG_FIELD)
    raw_literals: set[str] = set()

    def expand(item: object) -> None:
        if isinstance(item, dict):
            for field, child in item.items():
                if type(child) is int and child < 0:
                    reference = -child - 1
                    if reference >= len(catalog):
                        raise AttestationError(
                            "Professional storage string reference is out of range"
                        )
                    item[field] = catalog[reference]
                else:
                    if isinstance(child, str):
                        raw_literals.add(child)
                    expand(child)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                if type(child) is int and child < 0:
                    reference = -child - 1
                    if reference >= len(catalog):
                        raise AttestationError(
                            "Professional storage string reference is out of range"
                        )
                    item[index] = catalog[reference]
                else:
                    if isinstance(child, str):
                        raw_literals.add(child)
                    expand(child)

    try:
        for field, child in value.items():
            if field in _PROFESSIONAL_STORAGE_ROUTING_FIELDS:
                continue
            if type(child) is int and child < 0:
                reference = -child - 1
                if reference >= len(catalog):
                    raise AttestationError(
                        "Professional storage string reference is out of range"
                    )
                value[field] = catalog[reference]
            else:
                if isinstance(child, str):
                    raw_literals.add(child)
                expand(child)
    except RecursionError as exc:
        raise AttestationError(
            "Professional storage nesting exceeds the codec limit"
        ) from exc
    counts = _professional_storage_string_counts(value)
    expected_catalog = sorted(
        text for text, count in counts.items() if count >= 2
    )
    if catalog != expected_catalog:
        raise AttestationError(
            "Professional storage string catalog is incomplete or unused"
        )
    if raw_literals & set(catalog):
        raise AttestationError(
            "Professional storage repeated string literal is not interned"
        )


def canonical_attestation_bytes(
    value: object, *, expected_path: str | None = None,
    expected_source_fingerprints: dict[str, str] | None = None,
    expected_review_contract_fingerprint: str | None = None,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
    expected_semantic_current_bindings: dict[str, dict[str, Any]] | None = None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None = None,
) -> bytes:
    validated = validate_attestation(
        value, expected_path=expected_path,
        expected_source_fingerprints=expected_source_fingerprints,
        expected_review_contract_fingerprint=expected_review_contract_fingerprint,
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
        expected_semantic_current_bindings=expected_semantic_current_bindings,
        expected_professional_current_bindings=expected_professional_current_bindings,
    )
    if (
        validated["axis"] == SEMANTIC_DISPOSITION_AXIS
        and expected_semantic_current_bindings is None
    ):
        raise AttestationError(
            "Semantic serialization requires authoritative current fingerprints"
        )
    return _bounded(
        _json_body(
            _storage_projection(
                validated,
                expected_readability_current_bindings=(
                    expected_readability_current_bindings
                ),
            )
        )
        + b"\n"
    )


def _storage_projection(
    value: dict[str, Any],
    *,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
) -> dict[str, Any]:
    """Project the validated in-memory model onto compact schema 2 storage.

    Runtime validators still derive summaries and component facts from their
    authoritative bindings.  The fixed file stores only the axis contract,
    detector contracts, one review-unit binding, and authenticated conclusions.
    """

    compact = copy.deepcopy(value)
    compact.pop("summary")
    axis = compact["axis"]
    if axis == READABILITY_AXIS:
        sources = compact.pop("source_fingerprints")
        expected = _readability_authority_projection(
            expected_readability_current_bindings
        )
        compact["detector_contract_fingerprints"] = {
            key: sources[key]
            for key in (
                "readability_detector_contract",
                "actionability_detector_contract",
            )
        }
        compact["target_manifest_binding"] = (
            readability_target_manifest_fingerprint(
                expected_readability_current_bindings
            )
        )
        for row in compact["findings"]:
            authority = expected[row["category"]][row["target_id"]]
            if row["category"] != "readability":
                row["review_unit_binding"] = readability_review_unit_binding(
                    category=row["category"],
                    target_id=row["target_id"],
                    authority=authority,
                )
            row.pop("source_fingerprint")
            row.pop("review_binding_fingerprint")
            row.pop("result")
            for finding in row.get("finding_reviews", []):
                finding["review_unit_binding"] = (
                    readability_review_unit_binding(
                        category="readability",
                        target_id=row["target_id"],
                        finding_id=finding["finding_id"],
                        authority=authority,
                    )
                )
                finding.pop("source_fingerprint")
                finding.pop("review_binding_fingerprint")
                finding.pop("result")
    elif axis == SEMANTIC_DISPOSITION_AXIS:
        sources = compact.pop("source_fingerprints")
        compact["detector_contract_fingerprints"] = {
            key: sources[key]
            for key in (
                "root_detector_contract",
                "reference_detector_contract",
            )
        }
        for row in compact["findings"]:
            row.pop("result")
    else:
        compact["review_cost_input"].pop(
            "formal_round_policy_fingerprint"
        )
        for row in compact["findings"]:
            for vote in row["votes"]:
                vote["examined_failure_modes"].pop("digest", None)
                vote["examined_omission_candidates"].pop("digest", None)
                vote["examined_adjacent_candidates"].pop("digest", None)
                vote["proof_limits"].pop("digest", None)
        _encode_professional_storage_in_place(compact)
    return compact


def _expanded_storage_projection(
    value: object,
    *,
    expected_source_fingerprints: dict[str, str] | None,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None,
    expected_semantic_current_bindings: dict[str, dict[str, Any]] | None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Rehydrate only derived, non-authoritative fields for validation."""

    if not isinstance(value, dict) or value.get("schema_version") != 2:
        raise AttestationError(
            "compact storage schema_version must equal 2"
        )
    expanded = copy.deepcopy(value)
    axis = expanded.get("axis")
    detectors = expanded.pop("detector_contract_fingerprints", None)
    sources = copy.deepcopy(expected_source_fingerprints)
    if axis == READABILITY_AXIS:
        manifest_binding = expanded.pop("target_manifest_binding", None)
        _sha(manifest_binding, "Readability target manifest binding")
        if not isinstance(detectors, dict) or set(detectors) != {
            "readability_detector_contract",
            "actionability_detector_contract",
        }:
            raise AttestationError(
                "Readability detector contract bindings are incomplete"
            )
        if expected_readability_current_bindings is None:
            raise AttestationError(
                "Readability storage requires current bindings"
            )
        if sources is None:
            raise AttestationError(
                "Readability storage requires expected source fingerprints"
            )
        if readability_source_fingerprint_shape(sources) != "current":
            raise AttestationError(
                "Readability expected source fingerprints are stale"
            )
        expected_manifest = readability_target_manifest_fingerprint(
            expected_readability_current_bindings
        )
        if any(sources.get(key) != digest for key, digest in detectors.items()):
            raise AttestationCurrentnessError(
                "Readability detector contract binding is stale"
            )
        if sources.get("readability_target_manifest") != expected_manifest:
            raise AttestationError(
                "Readability expected target manifest binding is stale"
            )
        if manifest_binding != expected_manifest:
            raise AttestationCurrentnessError(
                "Readability target manifest binding is stale"
            )
        expected = _readability_authority_projection(
            expected_readability_current_bindings
        )
        for row in expanded["findings"]:
            if not isinstance(row, dict):
                raise AttestationError(
                    "Readability compact finding must be an object"
                )
            category = row.get("category")
            target_id = row.get("target_id")
            category_bindings = expected.get(category, {})
            authority = category_bindings.get(target_id)
            if authority is None:
                raise AttestationError(
                    "Readability authoritative target identity is unknown"
                )
            if category != "readability":
                stored_unit_binding = row.pop(
                    "review_unit_binding", None
                )
                _sha(
                    stored_unit_binding,
                    "Readability review unit binding",
                )
                expected_unit_binding = readability_review_unit_binding(
                    category=category,
                    target_id=target_id,
                    authority=authority,
                )
                if stored_unit_binding != expected_unit_binding:
                    raise AttestationError(
                        "Readability review unit binding is stale"
                    )
            elif "review_unit_binding" in row:
                raise AttestationError(
                    "Readability document conclusion must be derived"
                )
            row["source_fingerprint"] = authority["source_fingerprint"]
            row["review_binding_fingerprint"] = authority[
                "review_binding_fingerprint"
            ]
            row["result"] = {}
            for finding in row.get("finding_reviews", []):
                if not isinstance(finding, dict):
                    raise AttestationError(
                        "Readability compact finding review must be an object"
                    )
                finding_authority = authority["findings"].get(
                    finding.get("finding_id")
                )
                if finding_authority is None:
                    raise AttestationError(
                        "Readability authoritative finding identity is unknown"
                    )
                stored_unit_binding = finding.pop(
                    "review_unit_binding", None
                )
                _sha(
                    stored_unit_binding,
                    "Readability review unit binding",
                )
                expected_unit_binding = readability_review_unit_binding(
                    category="readability",
                    target_id=target_id,
                    finding_id=finding["finding_id"],
                    authority=authority,
                )
                if stored_unit_binding != expected_unit_binding:
                    raise AttestationError(
                        "Readability review unit binding is stale"
                    )
                finding["source_fingerprint"] = finding_authority[
                    "source_fingerprint"
                ]
                finding["review_binding_fingerprint"] = finding_authority[
                    "review_binding_fingerprint"
                ]
                finding["result"] = {}
    elif axis == SEMANTIC_DISPOSITION_AXIS:
        if expected_semantic_current_bindings is None:
            raise AttestationError(
                "Semantic storage requires authoritative current bindings"
            )
        if not isinstance(detectors, dict) or set(detectors) != {
            "root_detector_contract",
            "reference_detector_contract",
        }:
            raise AttestationError(
                "Semantic detector contract bindings are incomplete"
            )
        if sources is None:
            if expected_semantic_current_bindings is None:
                raise AttestationError(
                    "Semantic storage requires current bindings"
                )
            by_axis = {"root": {}, "reference": {}}
            for target_id, authority in expected_semantic_current_bindings.items():
                by_axis[target_id.split(":", 1)[0]][target_id] = authority[
                    "candidate_binding_fingerprint"
                ]
            sources = {
                "root_candidate_manifest": canonical_json_sha256(by_axis["root"]),
                "reference_candidate_manifest": canonical_json_sha256(
                    by_axis["reference"]
                ),
                **detectors,
            }
        if any(sources.get(key) != digest for key, digest in detectors.items()):
            raise AttestationError(
                "Semantic detector contract binding is stale"
            )
        for row in expanded["findings"]:
            authority = expected_semantic_current_bindings.get(
                row["target_id"]
            )
            if authority is None:
                raise AttestationError(
                    "Semantic authoritative current bindings are incomplete"
                )
            if row["candidate_binding_fingerprint"] != authority[
                "candidate_binding_fingerprint"
            ]:
                raise AttestationError(
                    "Semantic candidate binding is stale"
                )
            row["result"] = {}
    elif axis == PROFESSIONAL_COMPLETENESS_AXIS:
        if detectors is not None or expected_professional_current_bindings is None:
            raise AttestationError(
                "Professional storage requires current bindings"
            )
        catalog = expanded.get("dependency_material_catalog")
        if not isinstance(catalog, dict) or list(catalog) != sorted(catalog):
            raise AttestationError(
                "Professional dependency material catalog is invalid"
            )
        for candidate_id, digest in catalog.items():
            _slug(candidate_id, "professional dependency catalog ID")
            _sha(digest, "professional dependency catalog binding")
        expanded["review_cost_input"][
            "formal_round_policy_fingerprint"
        ] = PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FINGERPRINT
        for row in expanded["findings"]:
            if not isinstance(row, dict):
                raise AttestationError(
                    "Professional compact finding must be an object"
                )
            authority = expected_professional_current_bindings.get(
                row.get("skill_id")
            )
            if authority is None:
                raise AttestationError(
                    "Professional authoritative current bindings are incomplete"
                )
            dependency_ids = row.get("dependency_ids")
            if (
                not isinstance(dependency_ids, list)
                or dependency_ids != sorted(set(dependency_ids))
            ):
                raise AttestationError(
                    "Professional dependency IDs are not canonical"
                )
            if not set(dependency_ids) <= set(catalog):
                raise AttestationError(
                    "Professional dependency material catalog is incomplete"
                )
    else:
        raise AttestationError("attestation axis or kind is invalid")
    if axis != PROFESSIONAL_COMPLETENESS_AXIS:
        expanded["source_fingerprints"] = sources
    expanded["summary"] = {}
    return expanded


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AttestationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_attestation_storage_selector_bytes(payload: object) -> dict[str, Any]:
    """Parse one raw storage object and expand only its physical codec."""

    if not isinstance(payload, bytes):
        raise AttestationError("attestation payload must be bytes")
    _bounded(payload)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AttestationError("attestation payload must be UTF-8") from exc
    if text.startswith("\ufeff"):
        raise AttestationError("attestation payload must not contain a BOM")
    try:
        value = json.loads(
            text, object_pairs_hook=_unique_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                AttestationError(f"invalid JSON constant: {token}")
            ),
        )
    except AttestationError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise AttestationError("attestation payload is invalid JSON") from exc
    if not isinstance(value, dict):
        raise AttestationError("attestation payload must be a JSON object")
    if (
        value.get("schema_version") == ATTESTATION_SCHEMA_VERSION
        and value.get("axis") == PROFESSIONAL_COMPLETENESS_AXIS
    ):
        if payload != _json_body(value) + b"\n":
            raise AttestationError("attestation payload is not canonical JSON")
        _decode_professional_storage_in_place(value)
    return value


def parse_attestation_bytes(
    payload: object, *, expected_path: str | None = None,
    expected_source_fingerprints: dict[str, str] | None = None,
    expected_review_contract_fingerprint: str | None = None,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
    expected_semantic_current_bindings: dict[str, dict[str, Any]] | None = None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    value = parse_attestation_storage_selector_bytes(payload)
    expanded = _expanded_storage_projection(
        value,
        expected_source_fingerprints=expected_source_fingerprints,
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
        expected_semantic_current_bindings=expected_semantic_current_bindings,
        expected_professional_current_bindings=(
            expected_professional_current_bindings
        ),
    )
    validated = finalize_attestation(
        expanded, expected_path=expected_path,
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
        expected_semantic_current_bindings=expected_semantic_current_bindings,
        expected_professional_current_bindings=expected_professional_current_bindings,
    )
    if (
        expected_source_fingerprints is not None
        and validated.get("source_fingerprints")
        != expected_source_fingerprints
    ):
        raise AttestationError("attestation source fingerprints are stale")
    if (
        expected_review_contract_fingerprint is not None
        and validated["review_contract_fingerprint"]
        != expected_review_contract_fingerprint
    ):
        raise AttestationError("attestation review contract fingerprint is stale")
    if payload != _json_body(
        _storage_projection(
            validated,
            expected_readability_current_bindings=(
                expected_readability_current_bindings
            ),
        )
    ) + b"\n":
        raise AttestationError("attestation payload is not canonical JSON")
    return validated


def parse_professional_baseline_bytes(
    payload: object,
    *,
    expected_professional_current_bindings: dict[str, dict[str, Any]],
    expected_path: str | None = None,
) -> tuple[dict[str, Any], set[str]]:
    """Validate one prior compact artifact and partition exact-current rows.

    This is deliberately separate from current attestation validation.  It
    requires a complete current authority map, validates the prior artifact's
    own closed conclusions and digests, and returns only rows whose complete
    authority remains byte-for-byte current as carry candidates.
    """

    value = parse_attestation_storage_selector_bytes(payload)
    if not isinstance(value, dict) or value.get("axis") != (
        PROFESSIONAL_COMPLETENESS_AXIS
    ):
        raise AttestationError("Professional baseline axis is invalid")
    if value.get("review_contract_fingerprint") != (
        panel_contracts.professional_review_contract_fingerprint()
    ):
        raise AttestationError(
            "Professional baseline review contract is not current"
        )
    value = _expanded_storage_projection(
        value,
        expected_source_fingerprints=None,
        expected_readability_current_bindings=None,
        expected_semantic_current_bindings=None,
        expected_professional_current_bindings=(
            expected_professional_current_bindings
        ),
    )
    findings = value.get("findings")
    if not isinstance(findings, list) or not findings:
        raise AttestationError("professional findings must be non-empty")
    finding_ids = [
        row.get("skill_id") if isinstance(row, dict) else None
        for row in findings
    ]
    if (
        not isinstance(expected_professional_current_bindings, dict)
        or finding_ids != sorted(set(finding_ids))
        or set(finding_ids) != set(expected_professional_current_bindings)
    ):
        raise AttestationError(
            "Professional current binding coverage is incomplete"
        )

    current: dict[str, dict[str, Any]] = {}
    for skill_id in finding_ids:
        _slug(skill_id, "expected professional skill_id")
        authority = _closed(
            expected_professional_current_bindings[skill_id],
            _COMPACT_PRO_AUTHORITY_FIELDS,
            f"expected professional binding {skill_id}",
        )
        for field in ("package_material_binding", "review_unit_binding"):
            _sha(authority[field], f"expected professional {field}")
        _sorted_strings(
            authority["required_expertise_tags"],
            f"expected professional {skill_id} expertise",
            nonempty=True,
        )
        _sorted_strings(
            authority["required_candidate_ids"],
            f"expected professional {skill_id} candidates",
        )
        selection_version = authority["selection_contract_version"]
        if not isinstance(selection_version, str) or not selection_version:
            raise AttestationError(
                "expected professional selection contract version is invalid"
            )
        required_dependencies = authority[
            "required_candidate_material_bindings"
        ]
        added_ids = _sorted_strings(
            authority["reviewer_added_candidate_ids_union"],
            f"expected professional {skill_id} reviewer-added candidates",
        )
        added_dependencies = authority[
            "reviewer_added_candidate_material_bindings"
        ]
        if (
            not isinstance(required_dependencies, dict)
            or set(required_dependencies) != set(authority["required_candidate_ids"])
            or not isinstance(added_dependencies, dict)
            or set(added_dependencies) != set(added_ids)
            or set(added_ids) & set(authority["required_candidate_ids"])
        ):
            raise AttestationError(
                "expected professional dependency bindings are invalid"
            )
        for candidate_id, digest in {
            **required_dependencies,
            **added_dependencies,
        }.items():
            _slug(candidate_id, "expected professional dependency candidate")
            _sha(digest, "expected professional dependency fingerprint")
        votes = authority["vote_authorities"]
        if (
            not isinstance(votes, dict)
            or len(votes) != panel_contracts.PROFESSIONAL_PANEL_SIZE
        ):
            raise AttestationError(
                "expected professional vote authority is incomplete"
            )
        for voter_id, vote in votes.items():
            _slug(voter_id, "expected professional evidence voter")
            if not isinstance(vote, dict) or vote.get("reviewer") != voter_id:
                raise AttestationError(
                    "expected professional vote authority is invalid"
                )
        _closed(
            authority["reviewer_partition"],
            _COMPACT_REVIEWER_PARTITION_FIELDS,
            f"expected professional reviewer partition {skill_id}",
        )
        metrics = authority["evidence_metrics"]
        if not isinstance(metrics, dict) or set(metrics) != _EVIDENCE_METRIC_KEYS:
            raise AttestationError(
                "expected professional evidence metrics are incomplete"
            )
        _closed(
            authority["origin"],
            _COMPACT_PRO_ORIGIN_FIELDS,
            f"expected professional origin {skill_id}",
        )
        current[skill_id] = authority

    historical_catalog = value["dependency_material_catalog"]
    historical = {
        row["skill_id"]: {
            "package_material_binding": row.get(
                "package_material_binding"
            ),
            "review_unit_binding": row.get("review_unit_binding"),
            "required_expertise_tags": copy.deepcopy(
                row.get("required_expertise_tags")
            ),
            "required_candidate_ids": copy.deepcopy(
                row.get("result", {})
                .get("review_dependencies", {})
                .get("required_candidate_ids")
            ),
            "selection_contract_version": current[row["skill_id"]][
                "selection_contract_version"
            ],
            "required_candidate_material_bindings": {
                candidate_id: historical_catalog[candidate_id]
                for candidate_id in row.get("result", {})
                .get("review_dependencies", {})
                .get("required_candidate_ids", [])
                if candidate_id in historical_catalog
            },
            "reviewer_added_candidate_ids_union": copy.deepcopy(
                row.get("result", {})
                .get("review_dependencies", {})
                .get("reviewer_added_candidate_ids_union")
            ),
            "reviewer_added_candidate_material_bindings": {
                candidate_id: historical_catalog[candidate_id]
                for candidate_id in row.get("result", {})
                .get("review_dependencies", {})
                .get("reviewer_added_candidate_ids_union", [])
                if candidate_id in historical_catalog
            },
            "vote_authorities": {
                vote["reviewer"]: copy.deepcopy(vote)
                for vote in row.get("votes", [])
                if isinstance(vote, dict)
                and isinstance(vote.get("reviewer"), str)
            },
            "reviewer_partition": {
                "domain_voters": copy.deepcopy(
                    row.get("result", {})
                    .get("qualification_coverage", {})
                    .get("domain_voters")
                ),
                "architecture_voter": (
                    row.get("result", {})
                    .get("qualification_coverage", {})
                    .get("architecture_voter")
                ),
            },
            "evidence_metrics": copy.deepcopy(
                row.get("result", {}).get("evidence_metrics")
            ),
            "origin": copy.deepcopy(
                row.get("provenance", {}).get("origin")
            ),
        }
        for row in findings
    }
    original = copy.deepcopy(value)
    derived = _derive(
        copy.deepcopy(value),
        expected_path=expected_path,
        populate=False,
        expected_professional_current_bindings=historical,
    )
    # Summary is intentionally not stored in compact v2.  Recompute it from
    # the authenticated rows before comparing the remaining self-contained
    # baseline claims.
    original["summary"] = copy.deepcopy(derived["summary"])
    if original != derived:
        raise AttestationError("attestation derived results or summary are stale")
    if payload != _json_body(_storage_projection(derived)) + b"\n":
        raise AttestationError("attestation payload is not canonical JSON")

    eligible: set[str] = set()
    for row in derived["findings"]:
        authority = current[row["skill_id"]]
        dependency_ids = row["result"]["review_dependencies"][
            "dependency_candidate_ids"
        ]
        expected_dependencies = {
            **authority["required_candidate_material_bindings"],
            **authority[
                "reviewer_added_candidate_material_bindings"
            ],
        }
        if (
            row["package_material_binding"]
            == authority["package_material_binding"]
            and row["review_unit_binding"]
            == authority["review_unit_binding"]
            and row["required_expertise_tags"]
            == authority["required_expertise_tags"]
            and row["result"]["review_dependencies"][
                "required_candidate_ids"
            ] == authority["required_candidate_ids"]
            and row["result"]["review_dependencies"][
                "reviewer_added_candidate_ids_union"
            ]
            == authority["reviewer_added_candidate_ids_union"]
            and set(expected_dependencies) == set(dependency_ids)
            and row["dependency_ids"] == sorted(expected_dependencies)
            and all(
                historical_catalog.get(candidate_id) == digest
                for candidate_id, digest in expected_dependencies.items()
            )
            and {
                vote["reviewer"]: vote for vote in row["votes"]
            }
            == authority["vote_authorities"]
            and row["result"]["qualification_coverage"]["domain_voters"]
            == authority["reviewer_partition"]["domain_voters"]
            and row["result"]["qualification_coverage"]["architecture_voter"]
            == authority["reviewer_partition"]["architecture_voter"]
            and row["result"]["evidence_metrics"]
            == authority["evidence_metrics"]
            and row["provenance"]["origin"] == authority["origin"]
        ):
            eligible.add(row["skill_id"])
    return derived, eligible
