#!/usr/bin/env python3
"""Closed data, bounded transport, and finalization for reviewer manifests.

The pure data layer projects, parses, and materializes transient JSONL without
filesystem access.  The bounded transport/finalization layer binds exact input
bytes and performs create-only or ordinary-POSIX atomic ballot writes.  Reviewer
manifest content never becomes part of a packet, ballot, decision, or report
schema; the existing panel module remains the final semantic authority.
"""

from __future__ import annotations

import copy
import base64
import hashlib
import json
import os
import re
import secrets
import stat
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import BinaryIO, Callable
from typing import Any


MANIFEST_KIND = "changeforge.expert-panel-reviewer-manifest"
MANIFEST_SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 262_144
MAX_MANIFEST_BYTES = 33_554_432
MAX_REVIEWER_MANIFEST_BYTES = 16_777_216
MAX_CHUNK_RAW_BYTES = 32_768
MAX_CHUNK_BASE64_CHARS = 43_692
MAX_CHUNK_ENVELOPE_BYTES = 49_152
MAX_CHUNK_COUNT = 512
CHUNK_PROTOCOL = "changeforge.reviewer-manifest-chunk"
CHUNK_PROTOCOL_VERSION = 1

_CHUNK_FIELDS = {
    "protocol",
    "version",
    "stream_id",
    "sequence",
    "chunk_count",
    "total_raw_bytes",
    "manifest_sha256",
    "chunk_raw_sha256",
    "payload_base64",
}

READABILITY_PANEL_KIND = "readability"
PROFESSIONAL_PANEL_KIND = "professional-completeness"
SEMANTIC_PANEL_KIND = "semantic-disposition"
READABILITY_BALLOT_KIND = "changeforge.expert-panel-ballot"
PROFESSIONAL_BALLOT_KIND = (
    "changeforge.professional-completeness-panel-ballot"
)
SEMANTIC_BALLOT_KIND = "changeforge.semantic-disposition-panel-ballot"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

_HEADER_FIELDS = {
    "record_type",
    "manifest_kind",
    "manifest_schema_version",
    "panel_kind",
    "ballot_kind",
    "ballot_schema_version",
    "review_id",
    "created_on",
    "voter_id",
    "packet_sha256",
    "capsule_sha256",
    "template_sha256",
    "record_count",
}
_LIMITATION_FIELDS = {"record_type", "ordinal", "text"}
_QUALIFICATION_FIELDS = {
    "record_type",
    "expertise_tag",
    "qualification_basis",
    "proof_limit",
}
_CONTENT_FIELDS = {
    "record_type",
    "path",
    "decision",
    "reason_code",
    "rationale",
}
_FINDING_FIELDS = {
    "record_type",
    "document_id",
    "finding_id",
    "decision",
    "reason_code",
    "rationale",
}
_ACTIONABILITY_FIELDS = {
    "record_type",
    "target_id",
    "decision",
    "reason_code",
    "evidence",
    "rationale",
}
_ACTIONABILITY_EVIDENCE_FIELDS = {"line", "source_line", "claim"}
_SEMANTIC_FIELDS = {
    "record_type",
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
_PROFESSIONAL_FIELDS = {
    "record_type",
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
_PROFESSIONAL_ANCHOR_FIELDS = {
    "anchor_id",
    "skill_id",
    "path",
    "start_line",
    "end_line",
}
_CRITERION_RESULT_FIELDS = {"status", "evidence_assertions"}
_EVIDENCE_ASSERTION_FIELDS = {
    "claim",
    "evidence_anchor_ids",
    "source_excerpt_sha256",
}
_FAILURE_FIELDS = {
    "failure_mode",
    "outcome",
    "evidence_anchor_ids",
    "rationale",
}
_OMISSION_FIELDS = {
    "omission_candidate",
    "outcome",
    "evidence_anchor_ids",
    "rationale",
}
_MANIFEST_ADJACENCY_FIELDS = {
    "skill_id",
    "disposition",
    "target_anchor_ids",
    "candidate_anchor_ids",
    "rationale",
}

_READABILITY_BALLOT_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "source_fingerprints",
    "voter",
    "content_votes",
    "readability_votes",
    "actionability_votes",
    "limitations",
}
_READABILITY_VOTER_FIELDS = {
    "voter_id",
    "agent_id",
    "role",
    "expertise",
    "independent_review",
}
_READABILITY_CONTENT_BALLOT_FIELDS = {
    "path",
    "classification",
    "decision",
    "reason_code",
    "rationale",
}
_READABILITY_DOCUMENT_BALLOT_FIELDS = {
    "document_id",
    "highest_band",
    "finding_reviews",
}
_READABILITY_FINDING_BALLOT_FIELDS = {
    "finding_id",
    "sentence_fingerprint",
    "decision",
    "reason_code",
    "rationale",
}
_ACTIONABILITY_BALLOT_FIELDS = {
    "target_id",
    "decision",
    "reason_code",
    "evidence",
    "rationale",
}

_SEMANTIC_BALLOT_FIELDS = {
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
_SEMANTIC_BALLOT_VOTE_FIELDS = _SEMANTIC_FIELDS - {"record_type"}

_PROFESSIONAL_BALLOT_FIELDS = {
    "schema_version",
    "kind",
    "review_id",
    "created_on",
    "packet_sha256",
    "voter",
    "professional_votes",
    "limitations",
    "review_contract_fingerprint",
    "capsule",
}
_PROFESSIONAL_VOTER_FIELDS = {
    *_READABILITY_VOTER_FIELDS,
    "expertise_tags",
    "qualification_claims",
}
_QUALIFICATION_BALLOT_FIELDS = {
    "expertise_tag",
    "qualification_basis",
    "proof_limit",
}
_PROFESSIONAL_BALLOT_VOTE_FIELDS = _PROFESSIONAL_FIELDS - {"record_type"}
_PROFESSIONAL_BALLOT_ADJACENCY_FIELDS = {
    *_MANIFEST_ADJACENCY_FIELDS,
    "review_origin",
    "discovery_reason",
}
_CAPSULE_REFERENCE_FIELDS = {"axis", "kind", "path", "review_id", "sha256"}

_CRITERIA = (
    "adjacent-overlap-or-gap",
    "boundary-conditions",
    "erroneous-rules",
    "failure-modes",
    "generic-knowledge-pollution",
    "material-omissions",
    "output-verifiability",
    "professional-correctness",
    "reference-high-risk-coverage",
    "verification-methods",
)

_CONTENT_REASON_CODES = {
    "accepted-current-density": {
        "bounded-density-preserves-professional-coverage",
        "split-would-fragment-one-decision-model",
    },
    "tracked-tightening": {
        "cross-boundary-decisions-conflated",
        "enumeration-obscures-primary-action",
        "multiple-independent-actions",
        "policy-exception-verification-conflated",
    },
}
_FINDING_REASON_CODES = {
    "accepted-current-readability": {
        "bounded-enumeration-improves-precision",
        "domain-terms-require-co-location",
        "single-indivisible-decision",
        "split-would-fragment-invariant",
    },
    "tracked-tightening": _CONTENT_REASON_CODES["tracked-tightening"],
}
_ACTIONABILITY_REASON_CODES = {
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
_PROFESSIONAL_REASON_CODES = {
    "accepted-current-professional-completeness": {
        "all-professional-criteria-satisfied",
    },
    "requires-professional-correction": {
        "adjacent-responsibility-gap",
        "boundary-condition-gap",
        "erroneous-professional-rule",
        "failure-mode-gap",
        "generic-knowledge-pollution",
        "material-professional-omission",
        "output-verification-gap",
        "professional-correctness-defect",
        "reference-high-risk-coverage-gap",
        "verification-method-gap",
    },
}
_CRITERION_STATUSES = {"satisfied", "defect-found"}
_EXAMINED_OUTCOMES = {"covered", "not-applicable", "defect-found"}
_ADJACENCY_DISPOSITIONS = {
    "adjacent-no-gap",
    "not-adjacent",
    "gap-or-overlap-defect",
}
_SEMANTIC_DISPOSITIONS = {
    "rewrite",
    "valid-contextual-rule",
    "false-positive",
    "time-bounded-exception",
}
_SEMANTIC_AXES = {"root", "reference"}


class ManifestError(ValueError):
    """Raised when a reviewer manifest violates its closed transport contract."""


def _object(value: object, fields: set[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ManifestError(f"{label} fields are invalid")
    return value


def _nonblank(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-blank string")
    _reject_surrogates(value, label=label)
    return value


def _sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ManifestError(f"{label} must be a lowercase SHA-256")
    return value


def _slug(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SLUG_RE.fullmatch(value) is None:
        raise ManifestError(f"{label} must be a canonical slug")
    return value


def _iso_date(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ManifestError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ManifestError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise ManifestError(f"{label} must be a canonical ISO date")
    return value


def _integer(value: object, *, label: str, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise ManifestError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ManifestError(f"{label} must be at least {minimum}")
    return value


def _string_array(
    value: object,
    *,
    label: str,
    nonempty: bool,
    sorted_unique: bool = False,
) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ManifestError(f"{label} must be a non-empty string array")
    result = [
        _nonblank(item, label=f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if sorted_unique and result != sorted(set(result)):
        raise ManifestError(f"{label} must be sorted and unique")
    return result


def _slug_array(value: object, *, label: str, nonempty: bool) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ManifestError(f"{label} must be a non-empty slug array")
    result = [
        _slug(item, label=f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if result != sorted(set(result)):
        raise ManifestError(f"{label} must be sorted and unique")
    return result


def _decision_reason(
    value: dict[str, Any],
    reason_codes: dict[str, set[str]],
    *,
    label: str,
) -> None:
    decision = value.get("decision")
    reason_code = value.get("reason_code")
    if decision not in reason_codes:
        raise ManifestError(f"{label}.decision is invalid")
    if reason_code not in reason_codes[decision]:
        raise ManifestError(f"{label}.reason_code does not match decision")
    _nonblank(value.get("rationale"), label=f"{label}.rationale")


def _reject_surrogates(value: str, *, label: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ManifestError(f"{label} contains an isolated surrogate")


def _validate_json_domain(value: object, *, label: str = "manifest") -> None:
    if value is None or type(value) in {bool, int}:
        return
    if isinstance(value, str):
        _reject_surrogates(value, label=label)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_domain(item, label=f"{label}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ManifestError(f"{label} contains a non-string key")
            _reject_surrogates(key, label=f"{label} key")
            _validate_json_domain(item, label=f"{label}.{key}")
        return
    raise ManifestError(f"{label} contains an unsupported JSON value")


def _canonical_record_bytes(record: dict[str, Any]) -> bytes:
    _validate_json_domain(record)
    try:
        return json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise ManifestError("manifest record is not canonical JSON") from exc


def _canonical_template_sha256(template: dict[str, Any]) -> str:
    """Reproduce the canonical pretty bytes emitted by the panel template writer."""

    _validate_json_domain(template, label="template")
    try:
        rendered = json.dumps(
            template,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise ManifestError("ballot template is not canonical JSON") from exc
    return hashlib.sha256(rendered).hexdigest()


def _validate_header(header: object, *, record_count: int) -> str:
    row = _object(header, _HEADER_FIELDS, label="header")
    if row.get("record_type") != "header":
        raise ManifestError("first manifest record must be header")
    if row.get("manifest_kind") != MANIFEST_KIND:
        raise ManifestError("header.manifest_kind is invalid")
    if type(row.get("manifest_schema_version")) is not int or row.get(
        "manifest_schema_version"
    ) != MANIFEST_SCHEMA_VERSION:
        raise ManifestError("header.manifest_schema_version is invalid")
    panel_kind = row.get("panel_kind")
    expected: tuple[str, int]
    if panel_kind == READABILITY_PANEL_KIND:
        expected = (READABILITY_BALLOT_KIND, 2)
        if row.get("capsule_sha256") is not None:
            raise ManifestError("readability header.capsule_sha256 must be null")
    elif panel_kind == PROFESSIONAL_PANEL_KIND:
        expected = (PROFESSIONAL_BALLOT_KIND, 3)
        _sha256(row.get("capsule_sha256"), label="header.capsule_sha256")
    elif panel_kind == SEMANTIC_PANEL_KIND:
        expected = (SEMANTIC_BALLOT_KIND, 2)
        if row.get("capsule_sha256") is not None:
            raise ManifestError("semantic header.capsule_sha256 must be null")
    else:
        raise ManifestError("header.panel_kind is invalid")
    if (row.get("ballot_kind"), row.get("ballot_schema_version")) != expected:
        raise ManifestError("header ballot kind or schema version is invalid")
    _slug(row.get("review_id"), label="header.review_id")
    _iso_date(row.get("created_on"), label="header.created_on")
    _slug(row.get("voter_id"), label="header.voter_id")
    _sha256(row.get("packet_sha256"), label="header.packet_sha256")
    _sha256(row.get("template_sha256"), label="header.template_sha256")
    count = _integer(row.get("record_count"), label="header.record_count", minimum=2)
    if count != record_count:
        raise ManifestError("header.record_count does not match manifest records")
    return panel_kind


def _validate_limitation(record: object, *, label: str) -> int:
    row = _object(record, _LIMITATION_FIELDS, label=label)
    if row.get("record_type") != "limitation":
        raise ManifestError(f"{label}.record_type is invalid")
    ordinal = _integer(row.get("ordinal"), label=f"{label}.ordinal", minimum=0)
    _nonblank(row.get("text"), label=f"{label}.text")
    return ordinal


def _validate_qualification(record: object, *, label: str) -> str:
    row = _object(record, _QUALIFICATION_FIELDS, label=label)
    if row.get("record_type") != "qualification_claim":
        raise ManifestError(f"{label}.record_type is invalid")
    tag = _slug(row.get("expertise_tag"), label=f"{label}.expertise_tag")
    _nonblank(row.get("qualification_basis"), label=f"{label}.qualification_basis")
    _nonblank(row.get("proof_limit"), label=f"{label}.proof_limit")
    return tag


def _validate_content(record: object, *, label: str) -> str:
    row = _object(record, _CONTENT_FIELDS, label=label)
    if row.get("record_type") != "readability_content_vote":
        raise ManifestError(f"{label}.record_type is invalid")
    path = _nonblank(row.get("path"), label=f"{label}.path")
    _decision_reason(row, _CONTENT_REASON_CODES, label=label)
    return path


def _validate_finding(record: object, *, label: str) -> tuple[str, str]:
    row = _object(record, _FINDING_FIELDS, label=label)
    if row.get("record_type") != "readability_finding":
        raise ManifestError(f"{label}.record_type is invalid")
    document_id = _nonblank(row.get("document_id"), label=f"{label}.document_id")
    finding_id = _sha256(row.get("finding_id"), label=f"{label}.finding_id")
    _decision_reason(row, _FINDING_REASON_CODES, label=label)
    return document_id, finding_id


def _validate_actionability(record: object, *, label: str) -> str:
    row = _object(record, _ACTIONABILITY_FIELDS, label=label)
    if row.get("record_type") != "actionability_vote":
        raise ManifestError(f"{label}.record_type is invalid")
    target_id = _nonblank(row.get("target_id"), label=f"{label}.target_id")
    _decision_reason(row, _ACTIONABILITY_REASON_CODES, label=label)
    evidence = row.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ManifestError(f"{label}.evidence must be non-empty")
    lines: list[int] = []
    for index, item in enumerate(evidence):
        item_label = f"{label}.evidence[{index}]"
        evidence_row = _object(item, _ACTIONABILITY_EVIDENCE_FIELDS, label=item_label)
        lines.append(
            _integer(evidence_row.get("line"), label=f"{item_label}.line", minimum=1)
        )
        _nonblank(evidence_row.get("source_line"), label=f"{item_label}.source_line")
        _nonblank(evidence_row.get("claim"), label=f"{item_label}.claim")
    if lines != sorted(set(lines)):
        raise ManifestError(f"{label}.evidence must be line-sorted and unique")
    return target_id


def _validate_semantic(record: object, *, label: str) -> tuple[str, str, str]:
    row = _object(record, _SEMANTIC_FIELDS, label=label)
    if row.get("record_type") != "semantic_vote":
        raise ManifestError(f"{label}.record_type is invalid")
    target_id = _nonblank(row.get("target_id"), label=f"{label}.target_id")
    axis = row.get("axis")
    if axis not in _SEMANTIC_AXES:
        raise ManifestError(f"{label}.axis is invalid")
    candidate_id = _sha256(
        row.get("candidate_id"), label=f"{label}.candidate_id"
    )
    if target_id != f"{axis}:{candidate_id}":
        raise ManifestError(f"{label} identity is inconsistent")
    disposition = row.get("disposition")
    if disposition not in _SEMANTIC_DISPOSITIONS:
        raise ManifestError(f"{label}.disposition is invalid")
    for field in (
        "rationale",
        "authority_or_condition",
        "decision_owner",
        "mitigation",
    ):
        _nonblank(row.get(field), label=f"{label}.{field}")
    review_after = row.get("review_after")
    if disposition == "time-bounded-exception":
        _iso_date(review_after, label=f"{label}.review_after")
    elif review_after is not None:
        raise ManifestError(
            f"{label}.review_after must be null unless time-bounded-exception"
        )
    return target_id, str(axis), candidate_id


def _validate_professional(record: object, *, label: str) -> str:
    row = _object(record, _PROFESSIONAL_FIELDS, label=label)
    if row.get("record_type") != "professional_vote":
        raise ManifestError(f"{label}.record_type is invalid")
    skill_id = _slug(row.get("skill_id"), label=f"{label}.skill_id")
    _decision_reason(row, _PROFESSIONAL_REASON_CODES, label=label)

    anchors = row.get("evidence_anchors")
    if not isinstance(anchors, list) or not anchors:
        raise ManifestError(f"{label}.evidence_anchors must be non-empty")
    anchor_ids: list[str] = []
    for index, anchor in enumerate(anchors):
        anchor_label = f"{label}.evidence_anchors[{index}]"
        anchor_row = _object(anchor, _PROFESSIONAL_ANCHOR_FIELDS, label=anchor_label)
        anchor_ids.append(
            _slug(anchor_row.get("anchor_id"), label=f"{anchor_label}.anchor_id")
        )
        _slug(anchor_row.get("skill_id"), label=f"{anchor_label}.skill_id")
        _nonblank(anchor_row.get("path"), label=f"{anchor_label}.path")
        start = _integer(
            anchor_row.get("start_line"), label=f"{anchor_label}.start_line", minimum=1
        )
        end = _integer(
            anchor_row.get("end_line"), label=f"{anchor_label}.end_line", minimum=1
        )
        if end < start:
            raise ManifestError(f"{anchor_label} line range is invalid")
    if anchor_ids != sorted(set(anchor_ids)):
        raise ManifestError(f"{label}.evidence_anchors must be anchor_id-sorted and unique")
    known_anchor_ids = set(anchor_ids)

    criteria = row.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(_CRITERIA):
        raise ManifestError(f"{label}.criteria fields are invalid")
    for criterion in _CRITERIA:
        criterion_label = f"{label}.criteria.{criterion}"
        result = _object(criteria[criterion], _CRITERION_RESULT_FIELDS, label=criterion_label)
        if result.get("status") not in _CRITERION_STATUSES:
            raise ManifestError(f"{criterion_label}.status is invalid")
        assertions = result.get("evidence_assertions")
        if not isinstance(assertions, list) or not assertions:
            raise ManifestError(f"{criterion_label}.evidence_assertions must be non-empty")
        for index, assertion in enumerate(assertions):
            assertion_label = f"{criterion_label}.evidence_assertions[{index}]"
            assertion_row = _object(
                assertion, _EVIDENCE_ASSERTION_FIELDS, label=assertion_label
            )
            _nonblank(assertion_row.get("claim"), label=f"{assertion_label}.claim")
            ids = _slug_array(
                assertion_row.get("evidence_anchor_ids"),
                label=f"{assertion_label}.evidence_anchor_ids",
                nonempty=True,
            )
            if not set(ids) <= known_anchor_ids:
                raise ManifestError(
                    f"{assertion_label}.evidence_anchor_ids name unknown anchors"
                )
            _sha256(
                assertion_row.get("source_excerpt_sha256"),
                label=f"{assertion_label}.source_excerpt_sha256",
            )

    _validate_examined_rows(
        row.get("examined_failure_modes"),
        label=f"{label}.examined_failure_modes",
        fields=_FAILURE_FIELDS,
        name_field="failure_mode",
        known_anchor_ids=known_anchor_ids,
    )
    _validate_examined_rows(
        row.get("examined_omission_candidates"),
        label=f"{label}.examined_omission_candidates",
        fields=_OMISSION_FIELDS,
        name_field="omission_candidate",
        known_anchor_ids=known_anchor_ids,
    )

    adjacency = row.get("examined_adjacent_candidates")
    if not isinstance(adjacency, list):
        raise ManifestError(f"{label}.examined_adjacent_candidates must be an array")
    candidate_ids: list[str] = []
    for index, candidate in enumerate(adjacency):
        candidate_label = f"{label}.examined_adjacent_candidates[{index}]"
        candidate_row = _object(
            candidate, _MANIFEST_ADJACENCY_FIELDS, label=candidate_label
        )
        candidate_ids.append(
            _slug(candidate_row.get("skill_id"), label=f"{candidate_label}.skill_id")
        )
        if candidate_row.get("disposition") not in _ADJACENCY_DISPOSITIONS:
            raise ManifestError(f"{candidate_label}.disposition is invalid")
        for key in ("target_anchor_ids", "candidate_anchor_ids"):
            ids = _slug_array(
                candidate_row.get(key),
                label=f"{candidate_label}.{key}",
                nonempty=True,
            )
            if not set(ids) <= known_anchor_ids:
                raise ManifestError(f"{candidate_label}.{key} names unknown anchors")
        _nonblank(candidate_row.get("rationale"), label=f"{candidate_label}.rationale")
    if candidate_ids != sorted(set(candidate_ids)):
        raise ManifestError(
            f"{label}.examined_adjacent_candidates must be skill_id-sorted and unique"
        )

    _string_array(
        row.get("proof_limits"),
        label=f"{label}.proof_limits",
        nonempty=True,
        sorted_unique=True,
    )
    return skill_id


def _validate_examined_rows(
    value: object,
    *,
    label: str,
    fields: set[str],
    name_field: str,
    known_anchor_ids: set[str],
) -> None:
    if not isinstance(value, list) or len(value) < 2:
        raise ManifestError(f"{label} must contain at least two rows")
    names: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        row = _object(item, fields, label=item_label)
        names.append(_nonblank(row.get(name_field), label=f"{item_label}.{name_field}"))
        if row.get("outcome") not in _EXAMINED_OUTCOMES:
            raise ManifestError(f"{item_label}.outcome is invalid")
        ids = _slug_array(
            row.get("evidence_anchor_ids"),
            label=f"{item_label}.evidence_anchor_ids",
            nonempty=True,
        )
        if not set(ids) <= known_anchor_ids:
            raise ManifestError(f"{item_label}.evidence_anchor_ids name unknown anchors")
        _nonblank(row.get("rationale"), label=f"{item_label}.rationale")
    if names != sorted(set(names)):
        raise ManifestError(f"{label} must be name-sorted and unique")


def _validate_records(records: object) -> str:
    if not isinstance(records, list) or len(records) < 2:
        raise ManifestError("manifest records must be an array with at least two records")
    panel_kind = _validate_header(records[0], record_count=len(records))
    if panel_kind == READABILITY_PANEL_KIND:
        allowed = {
            "limitation": 1,
            "readability_content_vote": 2,
            "readability_finding": 3,
            "actionability_vote": 4,
        }
    elif panel_kind == PROFESSIONAL_PANEL_KIND:
        allowed = {
            "limitation": 1,
            "qualification_claim": 2,
            "professional_vote": 3,
        }
    else:
        allowed = {
            "limitation": 1,
            "semantic_vote": 2,
        }
    last_rank = 0
    limitation_ordinals: list[int] = []
    qualification_tags: list[str] = []
    content_paths: list[str] = []
    finding_keys: list[tuple[str, str]] = []
    finding_documents: list[str] = []
    actionability_ids: list[str] = []
    professional_ids: list[str] = []
    semantic_ids: list[tuple[str, str, str]] = []
    for index, record in enumerate(records[1:], start=1):
        if not isinstance(record, dict):
            raise ManifestError(f"record[{index}] must be an object")
        record_type = record.get("record_type")
        rank = allowed.get(record_type)
        if rank is None:
            raise ManifestError(
                f"record[{index}].record_type is unknown or belongs to another axis"
            )
        if rank < last_rank:
            raise ManifestError("manifest records are not in canonical type order")
        last_rank = rank
        label = f"record[{index}]"
        if record_type == "limitation":
            limitation_ordinals.append(_validate_limitation(record, label=label))
        elif record_type == "qualification_claim":
            qualification_tags.append(_validate_qualification(record, label=label))
        elif record_type == "readability_content_vote":
            content_paths.append(_validate_content(record, label=label))
        elif record_type == "readability_finding":
            key = _validate_finding(record, label=label)
            finding_keys.append(key)
            finding_documents.append(key[0])
        elif record_type == "actionability_vote":
            actionability_ids.append(_validate_actionability(record, label=label))
        elif record_type == "professional_vote":
            professional_ids.append(_validate_professional(record, label=label))
        elif record_type == "semantic_vote":
            semantic_ids.append(_validate_semantic(record, label=label))
    if limitation_ordinals != list(range(len(limitation_ordinals))) or not limitation_ordinals:
        raise ManifestError("limitation ordinals must provide contiguous zero-based coverage")
    _require_sorted_unique(qualification_tags, label="qualification expertise tags")
    _require_sorted_unique(content_paths, label="content vote paths")
    if len(finding_keys) != len(set(finding_keys)):
        raise ManifestError("readability finding identities must be unique")
    if finding_documents != sorted(finding_documents):
        raise ManifestError("readability finding documents must be document-sorted")
    _require_sorted_unique(actionability_ids, label="actionability target IDs")
    _require_sorted_unique(professional_ids, label="professional skill IDs")
    if panel_kind == PROFESSIONAL_PANEL_KIND and not professional_ids:
        raise ManifestError("professional manifest must contain at least one vote")
    if semantic_ids != sorted(set(semantic_ids)):
        raise ManifestError(
            "semantic vote identities must be triple-sorted and unique"
        )
    return panel_kind


def _require_sorted_unique(values: list[str], *, label: str) -> None:
    if values != sorted(set(values)):
        raise ManifestError(f"{label} must be sorted and unique")


def _validate_encoded_bounds(records: list[dict[str, Any]]) -> list[bytes]:
    encoded: list[bytes] = []
    total = 0
    for index, record in enumerate(records):
        line = _canonical_record_bytes(record) + b"\n"
        if len(line) > MAX_RECORD_BYTES:
            raise ManifestError(
                f"record[{index}] exceeds the {MAX_RECORD_BYTES}-byte limit"
            )
        total += len(line)
        if total > MAX_REVIEWER_MANIFEST_BYTES:
            raise ManifestError(
                "manifest exceeds the "
                f"{MAX_REVIEWER_MANIFEST_BYTES}-byte limit"
            )
        encoded.append(line)
    return encoded


def _ballot_axis(ballot: object, *, template: bool) -> str:
    if not isinstance(ballot, dict):
        raise ManifestError("ballot must be an object")
    schema_version = ballot.get("schema_version")
    kind = ballot.get("kind")
    if schema_version == 2 and kind == READABILITY_BALLOT_KIND:
        _validate_readability_ballot_shape(ballot, template=template)
        return READABILITY_PANEL_KIND
    if schema_version == 3 and kind == PROFESSIONAL_BALLOT_KIND:
        _validate_professional_ballot_shape(ballot, template=template)
        return PROFESSIONAL_PANEL_KIND
    if schema_version == 2 and kind == SEMANTIC_BALLOT_KIND:
        _validate_semantic_ballot_shape(ballot, template=template)
        return SEMANTIC_PANEL_KIND
    raise ManifestError(
        "only readability schema 2, professional schema 3, and semantic schema 2 are supported"
    )


def _validate_common_ballot(ballot: dict[str, Any], *, professional: bool) -> None:
    _slug(ballot.get("review_id"), label="ballot.review_id")
    _iso_date(ballot.get("created_on"), label="ballot.created_on")
    _sha256(ballot.get("packet_sha256"), label="ballot.packet_sha256")
    if not professional and not isinstance(ballot.get("source_fingerprints"), dict):
        raise ManifestError("ballot.source_fingerprints must be an object")
    voter = ballot.get("voter")
    expected = _PROFESSIONAL_VOTER_FIELDS if professional else _READABILITY_VOTER_FIELDS
    voter = _object(voter, expected, label="ballot.voter")
    _slug(voter.get("voter_id"), label="ballot.voter.voter_id")
    _nonblank(voter.get("agent_id"), label="ballot.voter.agent_id")
    _nonblank(voter.get("role"), label="ballot.voter.role")
    _string_array(voter.get("expertise"), label="ballot.voter.expertise", nonempty=True)
    if voter.get("independent_review") is not True:
        raise ManifestError("ballot.voter.independent_review must be true")
    _string_array(ballot.get("limitations"), label="ballot.limitations", nonempty=True)


def _validate_readability_ballot_shape(ballot: dict[str, Any], *, template: bool) -> None:
    _object(ballot, _READABILITY_BALLOT_FIELDS, label="readability ballot")
    _validate_common_ballot(ballot, professional=False)
    paths: list[str] = []
    votes = ballot.get("content_votes")
    if not isinstance(votes, list):
        raise ManifestError("ballot.content_votes must be an array")
    for index, vote in enumerate(votes):
        label = f"ballot.content_votes[{index}]"
        row = _object(vote, _READABILITY_CONTENT_BALLOT_FIELDS, label=label)
        paths.append(_nonblank(row.get("path"), label=f"{label}.path"))
        _nonblank(row.get("classification"), label=f"{label}.classification")
        _validate_fill_state(row, label=label, template=template, reason_codes=_CONTENT_REASON_CODES)
    _require_sorted_unique(paths, label="ballot content vote paths")

    documents: list[str] = []
    finding_keys: set[tuple[str, str]] = set()
    readability = ballot.get("readability_votes")
    if not isinstance(readability, list):
        raise ManifestError("ballot.readability_votes must be an array")
    for index, vote in enumerate(readability):
        label = f"ballot.readability_votes[{index}]"
        row = _object(vote, _READABILITY_DOCUMENT_BALLOT_FIELDS, label=label)
        document_id = _nonblank(row.get("document_id"), label=f"{label}.document_id")
        documents.append(document_id)
        _nonblank(row.get("highest_band"), label=f"{label}.highest_band")
        findings = row.get("finding_reviews")
        if not isinstance(findings, list):
            raise ManifestError(f"{label}.finding_reviews must be an array")
        for finding_index, finding in enumerate(findings):
            finding_label = f"{label}.finding_reviews[{finding_index}]"
            finding_row = _object(
                finding, _READABILITY_FINDING_BALLOT_FIELDS, label=finding_label
            )
            key = (
                document_id,
                _sha256(finding_row.get("finding_id"), label=f"{finding_label}.finding_id"),
            )
            if key in finding_keys:
                raise ManifestError("ballot readability finding identities must be unique")
            finding_keys.add(key)
            _sha256(
                finding_row.get("sentence_fingerprint"),
                label=f"{finding_label}.sentence_fingerprint",
            )
            _validate_fill_state(
                finding_row,
                label=finding_label,
                template=template,
                reason_codes=_FINDING_REASON_CODES,
            )
    _require_sorted_unique(documents, label="ballot readability documents")

    target_ids: list[str] = []
    actionability = ballot.get("actionability_votes")
    if not isinstance(actionability, list):
        raise ManifestError("ballot.actionability_votes must be an array")
    for index, vote in enumerate(actionability):
        label = f"ballot.actionability_votes[{index}]"
        row = _object(vote, _ACTIONABILITY_BALLOT_FIELDS, label=label)
        target_ids.append(_nonblank(row.get("target_id"), label=f"{label}.target_id"))
        if template:
            _require_unfilled(row, label=label, evidence_field="evidence")
        else:
            _validate_actionability({"record_type": "actionability_vote", **row}, label=label)
    _require_sorted_unique(target_ids, label="ballot actionability target IDs")


def _validate_semantic_ballot_shape(
    ballot: dict[str, Any], *, template: bool
) -> None:
    _object(ballot, _SEMANTIC_BALLOT_FIELDS, label="semantic ballot")
    _validate_common_ballot(ballot, professional=False)
    votes = ballot.get("semantic_votes")
    if not isinstance(votes, list):
        raise ManifestError("ballot.semantic_votes must be an array")
    identities: list[tuple[str, str, str]] = []
    for index, vote in enumerate(votes):
        label = f"ballot.semantic_votes[{index}]"
        row = _object(vote, _SEMANTIC_BALLOT_VOTE_FIELDS, label=label)
        target_id = _nonblank(row.get("target_id"), label=f"{label}.target_id")
        axis = row.get("axis")
        if axis not in _SEMANTIC_AXES:
            raise ManifestError(f"{label}.axis is invalid")
        candidate_id = _sha256(
            row.get("candidate_id"), label=f"{label}.candidate_id"
        )
        if target_id != f"{axis}:{candidate_id}":
            raise ManifestError(f"{label} identity is inconsistent")
        identities.append((target_id, str(axis), candidate_id))
        if template:
            if (
                row.get("disposition") is not None
                or row.get("rationale") != ""
                or row.get("authority_or_condition") != ""
                or row.get("decision_owner") != ""
                or row.get("mitigation") != ""
                or row.get("review_after") is not None
            ):
                raise ManifestError(f"{label} is not an unfilled template vote")
        else:
            _validate_semantic(
                {"record_type": "semantic_vote", **row},
                label=label,
            )
    if identities != sorted(set(identities)):
        raise ManifestError(
            "ballot semantic vote identities must be triple-sorted and unique"
        )


def _validate_fill_state(
    row: dict[str, Any],
    *,
    label: str,
    template: bool,
    reason_codes: dict[str, set[str]],
) -> None:
    if template:
        _require_unfilled(row, label=label)
    else:
        _decision_reason(row, reason_codes, label=label)


def _require_unfilled(
    row: dict[str, Any], *, label: str, evidence_field: str | None = None
) -> None:
    if (
        row.get("decision") is not None
        or row.get("reason_code") is not None
        or row.get("rationale") != ""
    ):
        raise ManifestError(f"{label} is not an unfilled template row")
    if evidence_field is not None and row.get(evidence_field) != []:
        raise ManifestError(f"{label}.{evidence_field} is not unfilled")


def _validate_professional_ballot_shape(ballot: dict[str, Any], *, template: bool) -> None:
    _object(ballot, _PROFESSIONAL_BALLOT_FIELDS, label="professional ballot")
    _validate_common_ballot(ballot, professional=True)
    _sha256(
        ballot.get("review_contract_fingerprint"),
        label="ballot.review_contract_fingerprint",
    )
    capsule = _object(ballot.get("capsule"), _CAPSULE_REFERENCE_FIELDS, label="ballot.capsule")
    if (
        capsule.get("axis") != PROFESSIONAL_PANEL_KIND
        or capsule.get("kind")
        != "changeforge.professional-completeness-review-capsule"
        or capsule.get("review_id") != ballot.get("review_id")
    ):
        raise ManifestError("ballot.capsule binding is invalid")
    _nonblank(capsule.get("path"), label="ballot.capsule.path")
    _sha256(capsule.get("sha256"), label="ballot.capsule.sha256")

    voter = ballot["voter"]
    tags = _slug_array(voter.get("expertise_tags"), label="ballot.voter.expertise_tags", nonempty=True)
    claims = voter.get("qualification_claims")
    if not isinstance(claims, list):
        raise ManifestError("ballot.voter.qualification_claims must be an array")
    claim_tags: list[str] = []
    for index, claim in enumerate(claims):
        label = f"ballot.voter.qualification_claims[{index}]"
        row = _object(claim, _QUALIFICATION_BALLOT_FIELDS, label=label)
        claim_tags.append(_slug(row.get("expertise_tag"), label=f"{label}.expertise_tag"))
        if template:
            if row.get("qualification_basis") != "" or row.get("proof_limit") != "":
                raise ManifestError(f"{label} is not unfilled")
        else:
            _nonblank(row.get("qualification_basis"), label=f"{label}.qualification_basis")
            _nonblank(row.get("proof_limit"), label=f"{label}.proof_limit")
    if claim_tags != tags:
        raise ManifestError("ballot qualification claims must exactly cover expertise tags")

    votes = ballot.get("professional_votes")
    if not isinstance(votes, list) or not votes:
        raise ManifestError("ballot.professional_votes must be non-empty")
    skill_ids: list[str] = []
    for index, vote in enumerate(votes):
        label = f"ballot.professional_votes[{index}]"
        row = _object(vote, _PROFESSIONAL_BALLOT_VOTE_FIELDS, label=label)
        skill_ids.append(_slug(row.get("skill_id"), label=f"{label}.skill_id"))
        adjacency = row.get("examined_adjacent_candidates")
        if not isinstance(adjacency, list):
            raise ManifestError(f"{label}.examined_adjacent_candidates must be an array")
        adjacency_ids: list[str] = []
        for candidate_index, candidate in enumerate(adjacency):
            candidate_label = f"{label}.examined_adjacent_candidates[{candidate_index}]"
            candidate_row = _object(
                candidate,
                _PROFESSIONAL_BALLOT_ADJACENCY_FIELDS,
                label=candidate_label,
            )
            adjacency_ids.append(
                _slug(candidate_row.get("skill_id"), label=f"{candidate_label}.skill_id")
            )
            origin = candidate_row.get("review_origin")
            discovery_reason = candidate_row.get("discovery_reason")
            if origin == "packet-required":
                if discovery_reason is not None:
                    raise ManifestError(
                        f"{candidate_label}.discovery_reason must be null for packet-required"
                    )
            elif origin == "reviewer-added":
                _nonblank(discovery_reason, label=f"{candidate_label}.discovery_reason")
            else:
                raise ManifestError(f"{candidate_label}.review_origin is invalid")
            if template and (
                candidate_row.get("disposition") is not None
                or candidate_row.get("target_anchor_ids") != []
                or candidate_row.get("candidate_anchor_ids") != []
                or candidate_row.get("rationale") != ""
            ):
                raise ManifestError(f"{candidate_label} is not unfilled")
        _require_sorted_unique(adjacency_ids, label=f"{label} adjacency skill IDs")
        if template:
            _validate_professional_template_vote(row, label=label)
        else:
            projected = {
                **{key: copy.deepcopy(row[key]) for key in _PROFESSIONAL_FIELDS - {"record_type", "examined_adjacent_candidates"}},
                "record_type": "professional_vote",
                "examined_adjacent_candidates": [
                    {
                        key: copy.deepcopy(candidate[key])
                        for key in _MANIFEST_ADJACENCY_FIELDS
                    }
                    for candidate in adjacency
                ],
            }
            _validate_professional(projected, label=label)
    _require_sorted_unique(skill_ids, label="ballot professional skill IDs")


def _validate_professional_template_vote(row: dict[str, Any], *, label: str) -> None:
    if (
        row.get("decision") is not None
        or row.get("reason_code") is not None
        or row.get("evidence_anchors") != []
        or row.get("examined_failure_modes") != []
        or row.get("examined_omission_candidates") != []
        or row.get("proof_limits") != []
        or row.get("rationale") != ""
    ):
        raise ManifestError(f"{label} is not an unfilled template vote")
    criteria = row.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(_CRITERIA):
        raise ManifestError(f"{label}.criteria fields are invalid")
    for criterion in _CRITERIA:
        result = _object(
            criteria[criterion],
            _CRITERION_RESULT_FIELDS,
            label=f"{label}.criteria.{criterion}",
        )
        if result.get("status") is not None or result.get("evidence_assertions") != []:
            raise ManifestError(f"{label}.criteria.{criterion} is not unfilled")


def project_ballot_to_manifest(
    ballot: dict[str, Any],
    *,
    template_sha256: str,
) -> list[dict[str, Any]]:
    """Project one filled supported ballot into closed JSONL records."""

    template_digest = _sha256(template_sha256, label="template_sha256")
    panel_kind = _ballot_axis(ballot, template=False)
    voter = ballot["voter"]
    records: list[dict[str, Any]] = [
        {
            "record_type": "header",
            "manifest_kind": MANIFEST_KIND,
            "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
            "panel_kind": panel_kind,
            "ballot_kind": ballot["kind"],
            "ballot_schema_version": ballot["schema_version"],
            "review_id": ballot["review_id"],
            "created_on": ballot["created_on"],
            "voter_id": voter["voter_id"],
            "packet_sha256": ballot["packet_sha256"],
            "capsule_sha256": (
                ballot["capsule"]["sha256"]
                if panel_kind == PROFESSIONAL_PANEL_KIND
                else None
            ),
            "template_sha256": template_digest,
            "record_count": 0,
        }
    ]
    records.extend(
        {
            "record_type": "limitation",
            "ordinal": index,
            "text": text,
        }
        for index, text in enumerate(ballot["limitations"])
    )
    if panel_kind == READABILITY_PANEL_KIND:
        records.extend(
            {
                "record_type": "readability_content_vote",
                "path": vote["path"],
                "decision": vote["decision"],
                "reason_code": vote["reason_code"],
                "rationale": vote["rationale"],
            }
            for vote in ballot["content_votes"]
        )
        records.extend(
            {
                "record_type": "readability_finding",
                "document_id": vote["document_id"],
                "finding_id": finding["finding_id"],
                "decision": finding["decision"],
                "reason_code": finding["reason_code"],
                "rationale": finding["rationale"],
            }
            for vote in ballot["readability_votes"]
            for finding in vote["finding_reviews"]
        )
        records.extend(
            {
                "record_type": "actionability_vote",
                "target_id": vote["target_id"],
                "decision": vote["decision"],
                "reason_code": vote["reason_code"],
                "evidence": copy.deepcopy(vote["evidence"]),
                "rationale": vote["rationale"],
            }
            for vote in ballot["actionability_votes"]
        )
    elif panel_kind == PROFESSIONAL_PANEL_KIND:
        records.extend(
            {
                "record_type": "qualification_claim",
                "expertise_tag": claim["expertise_tag"],
                "qualification_basis": claim["qualification_basis"],
                "proof_limit": claim["proof_limit"],
            }
            for claim in voter["qualification_claims"]
        )
        records.extend(
            {
                "record_type": "professional_vote",
                "skill_id": vote["skill_id"],
                "decision": vote["decision"],
                "reason_code": vote["reason_code"],
                "evidence_anchors": copy.deepcopy(vote["evidence_anchors"]),
                "criteria": copy.deepcopy(vote["criteria"]),
                "examined_failure_modes": copy.deepcopy(
                    vote["examined_failure_modes"]
                ),
                "examined_omission_candidates": copy.deepcopy(
                    vote["examined_omission_candidates"]
                ),
                "examined_adjacent_candidates": [
                    {
                        key: copy.deepcopy(candidate[key])
                        for key in _MANIFEST_ADJACENCY_FIELDS
                    }
                    for candidate in vote["examined_adjacent_candidates"]
                ],
                "proof_limits": copy.deepcopy(vote["proof_limits"]),
                "rationale": vote["rationale"],
            }
            for vote in ballot["professional_votes"]
        )
    else:
        records.extend(
            {
                "record_type": "semantic_vote",
                "target_id": vote["target_id"],
                "axis": vote["axis"],
                "candidate_id": vote["candidate_id"],
                "disposition": vote["disposition"],
                "rationale": vote["rationale"],
                "authority_or_condition": vote["authority_or_condition"],
                "decision_owner": vote["decision_owner"],
                "mitigation": vote["mitigation"],
                "review_after": vote["review_after"],
            }
            for vote in ballot["semantic_votes"]
        )
    records[0]["record_count"] = len(records)
    _validate_records(records)
    _validate_encoded_bounds(records)
    return records


def encode_manifest_records(records: list[dict[str, Any]]) -> bytes:
    """Return canonical UTF-8 JSONL bytes, including the required final LF."""

    _validate_records(records)
    return b"".join(_validate_encoded_bounds(records))


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ManifestError(f"non-finite JSON number is forbidden: {value}")


def parse_manifest_bytes(raw: bytes) -> list[dict[str, Any]]:
    """Parse canonical bounded JSONL, rejecting ambiguity before materialization."""

    if not isinstance(raw, bytes):
        raise ManifestError("manifest input must be bytes")
    if not raw:
        raise ManifestError("manifest must not be empty")
    if len(raw) > MAX_REVIEWER_MANIFEST_BYTES:
        raise ManifestError(
            "manifest exceeds the "
            f"{MAX_REVIEWER_MANIFEST_BYTES}-byte limit"
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ManifestError("manifest must not contain a UTF-8 BOM")
    if b"\r" in raw:
        raise ManifestError("manifest must use LF line endings only")
    if not raw.endswith(b"\n"):
        raise ManifestError("manifest must end with LF")
    lines = raw[:-1].split(b"\n")
    if not lines or any(not line for line in lines):
        raise ManifestError("manifest must not contain blank records")
    records: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if len(line) + 1 > MAX_RECORD_BYTES:
            raise ManifestError(
                f"record[{index}] exceeds the {MAX_RECORD_BYTES}-byte limit"
            )
        try:
            text = line.decode("utf-8", errors="strict")
            value = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_pairs,
                parse_constant=_reject_json_constant,
            )
        except ManifestError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ManifestError(f"record[{index}] is not strict UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise ManifestError(f"record[{index}] must be a JSON object")
        canonical = _canonical_record_bytes(value)
        if line != canonical:
            raise ManifestError(f"record[{index}] is not canonical JSON")
        records.append(value)
    _validate_records(records)
    return records


def _records_of_type(
    records: list[dict[str, Any]], record_type: str
) -> list[dict[str, Any]]:
    return [record for record in records if record.get("record_type") == record_type]


def _expected_header(template: dict[str, Any], *, panel_kind: str) -> dict[str, Any]:
    return {
        "manifest_kind": MANIFEST_KIND,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "panel_kind": panel_kind,
        "ballot_kind": template["kind"],
        "ballot_schema_version": template["schema_version"],
        "review_id": template["review_id"],
        "created_on": template["created_on"],
        "voter_id": template["voter"]["voter_id"],
        "packet_sha256": template["packet_sha256"],
        "capsule_sha256": (
            template["capsule"]["sha256"]
            if panel_kind == PROFESSIONAL_PANEL_KIND
            else None
        ),
    }


def materialize_manifest(
    template: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fill reviewer-owned values into a deep copy of an unfilled template."""

    panel_kind = _validate_records(records)
    _validate_encoded_bounds(records)
    template_panel_kind = _ballot_axis(template, template=True)
    if panel_kind != template_panel_kind:
        raise ManifestError("manifest axis does not match ballot template")
    header = records[0]
    for key, expected in _expected_header(template, panel_kind=panel_kind).items():
        if header.get(key) != expected:
            raise ManifestError(f"header.{key} does not match ballot template")
    if header.get("template_sha256") != _canonical_template_sha256(template):
        raise ManifestError("header.template_sha256 does not match ballot template")

    result = copy.deepcopy(template)
    limitations = _records_of_type(records, "limitation")
    result["limitations"] = [record["text"] for record in limitations]
    if panel_kind == READABILITY_PANEL_KIND:
        _materialize_readability(result, records)
    elif panel_kind == PROFESSIONAL_PANEL_KIND:
        _materialize_professional(result, records)
    else:
        _materialize_semantic(result, records)
    # The closed records were fully validated before the template was copied,
    # and exact identity coverage above fills every reviewer-owned slot.  Do
    # not re-traverse the completed ballot here: the existing panel validator
    # remains the final semantic authority and Task B invokes it before write.
    return result


def _materialize_readability(
    result: dict[str, Any], records: list[dict[str, Any]]
) -> None:
    content = _records_of_type(records, "readability_content_vote")
    expected_paths = [vote["path"] for vote in result["content_votes"]]
    actual_paths = [record["path"] for record in content]
    if actual_paths != expected_paths:
        raise ManifestError("content manifest coverage does not match template")
    for vote, record in zip(result["content_votes"], content, strict=True):
        _fill_decision(vote, record)

    findings = _records_of_type(records, "readability_finding")
    template_findings = [
        (vote["document_id"], finding)
        for vote in result["readability_votes"]
        for finding in vote["finding_reviews"]
    ]
    expected_keys = [
        (document_id, finding["finding_id"])
        for document_id, finding in template_findings
    ]
    actual_keys = [
        (record["document_id"], record["finding_id"])
        for record in findings
    ]
    if actual_keys != expected_keys:
        raise ManifestError("readability finding coverage does not match template")
    for (_document_id, finding), record in zip(
        template_findings, findings, strict=True
    ):
        _fill_decision(finding, record)

    actionability = _records_of_type(records, "actionability_vote")
    expected_targets = [vote["target_id"] for vote in result["actionability_votes"]]
    actual_targets = [record["target_id"] for record in actionability]
    if actual_targets != expected_targets:
        raise ManifestError("actionability manifest coverage does not match template")
    for vote, record in zip(result["actionability_votes"], actionability, strict=True):
        _fill_decision(vote, record)
        vote["evidence"] = copy.deepcopy(record["evidence"])


def _fill_decision(target: dict[str, Any], record: dict[str, Any]) -> None:
    target["decision"] = record["decision"]
    target["reason_code"] = record["reason_code"]
    target["rationale"] = record["rationale"]


def _materialize_semantic(
    result: dict[str, Any], records: list[dict[str, Any]]
) -> None:
    votes = _records_of_type(records, "semantic_vote")
    identity_fields = ("target_id", "axis", "candidate_id")
    expected = [
        tuple(vote[field] for field in identity_fields)
        for vote in result["semantic_votes"]
    ]
    actual = [
        tuple(record[field] for field in identity_fields)
        for record in votes
    ]
    if actual != expected:
        raise ManifestError(
            "semantic manifest identity coverage does not match template"
        )
    reviewer_fields = (
        "disposition",
        "rationale",
        "authority_or_condition",
        "decision_owner",
        "mitigation",
        "review_after",
    )
    for vote, record in zip(result["semantic_votes"], votes, strict=True):
        for field in reviewer_fields:
            vote[field] = copy.deepcopy(record[field])


def _materialize_professional(
    result: dict[str, Any], records: list[dict[str, Any]]
) -> None:
    qualifications = _records_of_type(records, "qualification_claim")
    expected_tags = result["voter"]["expertise_tags"]
    actual_tags = [record["expertise_tag"] for record in qualifications]
    if actual_tags != expected_tags:
        raise ManifestError("qualification manifest coverage does not match template")
    for claim, record in zip(
        result["voter"]["qualification_claims"],
        qualifications,
        strict=True,
    ):
        claim["qualification_basis"] = record["qualification_basis"]
        claim["proof_limit"] = record["proof_limit"]

    votes = _records_of_type(records, "professional_vote")
    expected_skills = [vote["skill_id"] for vote in result["professional_votes"]]
    actual_skills = [record["skill_id"] for record in votes]
    if actual_skills != expected_skills:
        raise ManifestError("professional manifest coverage does not match template")
    for vote, record in zip(result["professional_votes"], votes, strict=True):
        template_adjacency = vote["examined_adjacent_candidates"]
        manifest_adjacency = record["examined_adjacent_candidates"]
        if [item["skill_id"] for item in manifest_adjacency] != [
            item["skill_id"] for item in template_adjacency
        ]:
            raise ManifestError(
                f"professional adjacency coverage does not match template: {vote['skill_id']}"
            )
        _fill_decision(vote, record)
        for key in (
            "evidence_anchors",
            "criteria",
            "examined_failure_modes",
            "examined_omission_candidates",
            "proof_limits",
        ):
            vote[key] = copy.deepcopy(record[key])
        for candidate, candidate_record in zip(
            template_adjacency, manifest_adjacency, strict=True
        ):
            for key in (
                "disposition",
                "target_anchor_ids",
                "candidate_anchor_ids",
                "rationale",
            ):
                candidate[key] = copy.deepcopy(candidate_record[key])


@dataclass(frozen=True)
class FileIdentity:
    """The ordinary-POSIX identity bound before a ballot is finalized."""

    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    mode: int


@dataclass(frozen=True)
class BoundFile:
    """One no-follow, single-link regular file and its exact bytes."""

    path: Path
    raw: bytes
    sha256: str
    identity: FileIdentity
    parent_identity: tuple[int, int]


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_lower_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ManifestError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_manifest_size(value: object) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
        or value > MAX_REVIEWER_MANIFEST_BYTES
    ):
        raise ManifestError(
            "manifest size must be between 1 and "
            f"{MAX_REVIEWER_MANIFEST_BYTES} bytes"
        )
    return value


def _file_identity(value: os.stat_result) -> FileIdentity:
    return FileIdentity(
        device=value.st_dev,
        inode=value.st_ino,
        size=value.st_size,
        mtime_ns=value.st_mtime_ns,
        ctime_ns=value.st_ctime_ns,
        mode=stat.S_IMODE(value.st_mode),
    )


def _open_directory_no_follow(path: Path) -> int:
    """Open an absolute directory one component at a time without symlinks."""

    absolute = _platform_absolute(path)
    if not absolute.is_absolute():  # pragma: no cover - Path.absolute guarantees it.
        raise ManifestError("artifact directory must be absolute")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(absolute.anchor, directory_flags)
        for part in absolute.parts[1:]:
            next_descriptor = os.open(
                part,
                directory_flags,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise ManifestError(
            f"artifact path must not traverse a symlink: {absolute}"
        ) from exc


def _open_parent_no_follow(path: Path) -> tuple[int, str]:
    absolute = _platform_absolute(path)
    if absolute.name in {"", ".", ".."}:
        raise ManifestError("artifact path must name a file")
    return _open_directory_no_follow(absolute.parent), absolute.name


def _platform_absolute(path: Path) -> Path:
    """Normalize only macOS's fixed root aliases before no-follow traversal."""

    absolute = path.absolute()
    if sys.platform == "darwin" and len(absolute.parts) > 1:
        root_alias = absolute.parts[1]
        if root_alias in {"tmp", "var"}:
            return Path("/private", *absolute.parts[1:])
    return absolute


def _read_all_descriptor(
    descriptor: int,
    *,
    expected_size: int | None,
    max_bytes: int,
    label: str,
) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(descriptor, min(65_536, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise ManifestError(f"{label} exceeds {max_bytes} bytes")
    raw = b"".join(chunks)
    if expected_size is not None and len(raw) != expected_size:
        raise ManifestError(
            f"{label} size mismatch: expected {expected_size}, got {len(raw)}"
        )
    return raw


def _read_regular_at(
    directory_fd: int,
    name: str,
    *,
    expected_size: int | None,
    max_bytes: int,
    label: str,
) -> tuple[bytes, FileIdentity]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(name, flags, dir_fd=directory_fd)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ManifestError(f"{label} must be a regular file")
        if before.st_nlink != 1:
            raise ManifestError(f"{label} must have exactly one hard link")
        if before.st_size > max_bytes:
            raise ManifestError(f"{label} exceeds {max_bytes} bytes")
        if expected_size is not None and before.st_size != expected_size:
            raise ManifestError(
                f"{label} size mismatch: expected {expected_size}, got {before.st_size}"
            )
        raw = _read_all_descriptor(
            descriptor,
            expected_size=expected_size,
            max_bytes=max_bytes,
            label=label,
        )
        after = os.fstat(descriptor)
        pathname = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except OSError as exc:
        raise ManifestError(f"cannot read {label}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    before_identity = _file_identity(before)
    if (
        before_identity != _file_identity(after)
        or before_identity != _file_identity(pathname)
        or not stat.S_ISREG(pathname.st_mode)
        or pathname.st_nlink != 1
    ):
        raise ManifestError(f"{label} changed while it was read")
    return raw, before_identity


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def bind_regular_file(
    path: Path,
    *,
    expected_sha256: str,
    expected_size: int | None = None,
    max_bytes: int = MAX_MANIFEST_BYTES,
    outside_root: Path | None = None,
    label: str,
) -> BoundFile:
    """Read and bind one no-follow regular file by bytes and POSIX identity."""

    digest = _require_lower_sha256(expected_sha256, label=f"{label} SHA-256")
    bound = read_bound_regular_file(
        path,
        expected_size=expected_size,
        max_bytes=max_bytes,
        outside_root=outside_root,
        label=label,
    )
    if bound.sha256 != digest:
        raise ManifestError(f"{label} SHA-256 mismatch")
    return bound


def read_bound_regular_file(
    path: Path,
    *,
    expected_size: int | None = None,
    max_bytes: int = MAX_MANIFEST_BYTES,
    outside_root: Path | None = None,
    label: str,
) -> BoundFile:
    """Read and bind a no-follow file when its digest is not known in advance."""

    if expected_size is not None:
        if (
            not isinstance(expected_size, int)
            or isinstance(expected_size, bool)
            or expected_size < 0
            or expected_size > max_bytes
        ):
            raise ManifestError(f"{label} size is outside its byte bound")
    absolute = _platform_absolute(path)
    if outside_root is not None:
        repository = outside_root.resolve()
        if _path_is_within(absolute, outside_root.absolute()):
            raise ManifestError(f"{label} must stay outside the repository")
        try:
            resolved = absolute.resolve(strict=True)
        except OSError as exc:
            raise ManifestError(f"cannot resolve {label}: {absolute}") from exc
        if _path_is_within(resolved, repository):
            raise ManifestError(f"{label} must stay outside the repository")
    directory_fd, name = _open_parent_no_follow(absolute)
    try:
        parent_stat = os.fstat(directory_fd)
        raw, identity = _read_regular_at(
            directory_fd,
            name,
            expected_size=expected_size,
            max_bytes=max_bytes,
            label=label,
        )
    finally:
        os.close(directory_fd)
    actual_digest = _sha256_bytes(raw)
    return BoundFile(
        path=absolute,
        raw=raw,
        sha256=actual_digest,
        identity=identity,
        parent_identity=(parent_stat.st_dev, parent_stat.st_ino),
    )


def _recheck_bound_at(
    bound: BoundFile,
    directory_fd: int,
    *,
    label: str,
) -> bytes:
    parent = os.fstat(directory_fd)
    if (parent.st_dev, parent.st_ino) != bound.parent_identity:
        raise ManifestError(f"{label} parent directory changed")
    raw, identity = _read_regular_at(
        directory_fd,
        bound.path.name,
        expected_size=bound.identity.size,
        max_bytes=max(MAX_MANIFEST_BYTES, bound.identity.size),
        label=label,
    )
    if identity != bound.identity or _sha256_bytes(raw) != bound.sha256:
        raise ManifestError(f"{label} identity or content changed")
    return raw


def recheck_bound_file(bound: BoundFile, *, label: str) -> bytes:
    directory_fd, _name = _open_parent_no_follow(bound.path)
    try:
        return _recheck_bound_at(bound, directory_fd, label=label)
    finally:
        os.close(directory_fd)


def read_manifest_file(
    path: Path,
    *,
    expected_size: int,
    expected_sha256: str,
    repository_root: Path,
) -> bytes:
    size = _require_manifest_size(expected_size)
    return bind_regular_file(
        path,
        expected_sha256=expected_sha256,
        expected_size=size,
        max_bytes=MAX_REVIEWER_MANIFEST_BYTES,
        outside_root=repository_root,
        label="reviewer manifest",
    ).raw


def _read_stream_bounded(stream: BinaryIO, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = stream.read(min(65_536, max_bytes + 1 - total))
        if not isinstance(chunk, bytes):
            raise ManifestError("reviewer manifest input must be a binary stream")
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise ManifestError(f"reviewer manifest exceeds {max_bytes} bytes")
    return b"".join(chunks)


def _verify_manifest_bytes(
    raw: bytes,
    *,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    size = _require_manifest_size(expected_size)
    digest = _require_lower_sha256(
        expected_sha256,
        label="reviewer manifest SHA-256",
    )
    if len(raw) != size:
        raise ManifestError(
            f"reviewer manifest size mismatch: expected {size}, got {len(raw)}"
        )
    if _sha256_bytes(raw) != digest:
        raise ManifestError("reviewer manifest SHA-256 mismatch")
    return raw


def read_raw_manifest_stream(
    stream: BinaryIO,
    *,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    size = _require_manifest_size(expected_size)
    raw = _read_stream_bounded(
        stream,
        max_bytes=min(MAX_REVIEWER_MANIFEST_BYTES, size) + 1,
    )
    return _verify_manifest_bytes(
        raw,
        expected_size=size,
        expected_sha256=expected_sha256,
    )


def parse_json_object_bytes(raw: bytes, *, label: str) -> dict[str, Any]:
    """Parse one strict UTF-8 JSON object, rejecting duplicate keys recursively."""

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ManifestError(f"{label} contains duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        decoded = raw.decode("utf-8")
        value = json.loads(
            decoded,
            object_pairs_hook=object_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ManifestError(f"{label} contains invalid JSON constant: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ManifestError(f"{label} is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be a JSON object")
    return value


def _framed_lines(stream: BinaryIO):
    pending = bytearray()
    while True:
        chunk = stream.read(8_192)
        if not isinstance(chunk, bytes):
            raise ManifestError("framed reviewer manifest must be a binary stream")
        if not chunk:
            break
        pending.extend(chunk)
        while True:
            newline = pending.find(b"\n")
            if newline < 0:
                break
            line = bytes(pending[:newline])
            del pending[: newline + 1]
            if len(line) + 1 > MAX_CHUNK_ENVELOPE_BYTES:
                raise ManifestError("reviewer manifest chunk envelope is too large")
            if not line:
                raise ManifestError("reviewer manifest chunk envelope is empty")
            yield line
        if len(pending) + 1 > MAX_CHUNK_ENVELOPE_BYTES:
            raise ManifestError("reviewer manifest chunk envelope is too large")
    if pending:
        raise ManifestError("framed reviewer manifest must end with a newline")


def read_framed_manifest_stream(
    stream: BinaryIO,
    *,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    size = _require_manifest_size(expected_size)
    digest = _require_lower_sha256(
        expected_sha256,
        label="reviewer manifest SHA-256",
    )
    expected_sequence = 0
    expected_count: int | None = None
    stream_id: str | None = None
    chunks: list[bytes] = []
    total = 0
    for line in _framed_lines(stream):
        envelope = parse_json_object_bytes(
            line,
            label=f"reviewer manifest chunk {expected_sequence}",
        )
        if set(envelope) != _CHUNK_FIELDS:
            raise ManifestError("reviewer manifest chunk fields are invalid")
        if envelope.get("protocol") != CHUNK_PROTOCOL:
            raise ManifestError("reviewer manifest chunk protocol is invalid")
        if (
            not isinstance(envelope.get("version"), int)
            or isinstance(envelope.get("version"), bool)
            or envelope.get("version") != CHUNK_PROTOCOL_VERSION
        ):
            raise ManifestError("reviewer manifest chunk version is invalid")
        sequence = envelope.get("sequence")
        chunk_count = envelope.get("chunk_count")
        total_raw_bytes = envelope.get("total_raw_bytes")
        if (
            not isinstance(sequence, int)
            or isinstance(sequence, bool)
            or sequence != expected_sequence
        ):
            raise ManifestError("reviewer manifest chunk sequence is not contiguous")
        if (
            not isinstance(chunk_count, int)
            or isinstance(chunk_count, bool)
            or not 1 <= chunk_count <= MAX_CHUNK_COUNT
        ):
            raise ManifestError("reviewer manifest chunk count is invalid")
        if expected_count is None:
            expected_count = chunk_count
        elif chunk_count != expected_count:
            raise ManifestError("reviewer manifest chunk count changed within stream")
        if expected_sequence >= chunk_count:
            raise ManifestError("reviewer manifest contains too many chunks")
        if (
            not isinstance(total_raw_bytes, int)
            or isinstance(total_raw_bytes, bool)
            or total_raw_bytes != size
        ):
            raise ManifestError("reviewer manifest framed size binding is stale")
        if envelope.get("manifest_sha256") != digest:
            raise ManifestError("reviewer manifest framed digest binding is stale")
        current_stream = envelope.get("stream_id")
        if not isinstance(current_stream, str) or not current_stream:
            raise ManifestError("reviewer manifest stream id is invalid")
        if stream_id is None:
            stream_id = current_stream
        elif current_stream != stream_id:
            raise ManifestError("reviewer manifest chunks mix stream ids")
        payload = envelope.get("payload_base64")
        if (
            not isinstance(payload, str)
            or len(payload) > MAX_CHUNK_BASE64_CHARS
            or not payload.isascii()
        ):
            raise ManifestError("reviewer manifest chunk base64 is invalid")
        try:
            raw_chunk = base64.b64decode(payload, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ManifestError("reviewer manifest chunk base64 is invalid") from exc
        if base64.b64encode(raw_chunk).decode("ascii") != payload:
            raise ManifestError("reviewer manifest chunk base64 is not canonical")
        if not raw_chunk or len(raw_chunk) > MAX_CHUNK_RAW_BYTES:
            raise ManifestError("reviewer manifest raw chunk size is invalid")
        chunk_digest = _require_lower_sha256(
            envelope.get("chunk_raw_sha256"),
            label="reviewer manifest chunk SHA-256",
        )
        if _sha256_bytes(raw_chunk) != chunk_digest:
            raise ManifestError("reviewer manifest chunk SHA-256 mismatch")
        total += len(raw_chunk)
        if total > size or total > MAX_REVIEWER_MANIFEST_BYTES:
            raise ManifestError("reviewer manifest framed payload exceeds its bound")
        chunks.append(raw_chunk)
        expected_sequence += 1
    if expected_count is None or expected_sequence != expected_count:
        raise ManifestError("reviewer manifest chunk stream ended before completion")
    raw = _verify_manifest_bytes(
        b"".join(chunks),
        expected_size=size,
        expected_sha256=digest,
    )
    header = parse_manifest_bytes(raw)[0]
    expected_stream_id = f"{header['review_id']}:{header['voter_id']}"
    if stream_id != expected_stream_id:
        raise ManifestError("reviewer manifest stream id does not match its header")
    return raw


def canonical_ballot_bytes(ballot: dict[str, Any], *, compact: bool) -> bytes:
    if compact:
        rendered = json.dumps(
            ballot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    else:
        rendered = json.dumps(ballot, ensure_ascii=False, indent=2)
    return (rendered + "\n").encode("utf-8")


def _write_all(descriptor: int, raw: bytes) -> None:
    offset = 0
    while offset < len(raw):
        written = os.write(descriptor, raw[offset:])
        if written <= 0:  # pragma: no cover - os.write either writes or raises.
            raise OSError("short write")
        offset += written


def _unlink_if_owned(
    directory_fd: int,
    name: str,
    identity: tuple[int, int] | None,
) -> None:
    if identity is None:
        return
    try:
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) == identity:
            os.unlink(name, dir_fd=directory_fd)
    except OSError:
        pass


def _unlink_owned_or_raise(
    directory_fd: int,
    name: str,
    identity: tuple[int, int],
    *,
    label: str,
) -> None:
    try:
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != identity:
            raise ManifestError(f"{label} ownership changed before cleanup")
        os.unlink(name, dir_fd=directory_fd)
    except ManifestError:
        raise
    except OSError as exc:
        raise ManifestError(f"cannot remove {label}: {exc}") from exc


def _create_durable_file(
    directory_fd: int,
    name: str,
    raw: bytes,
    *,
    label: str,
    mode: int = 0o644,
) -> tuple[int, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    identity: tuple[int, int] | None = None
    succeeded = False
    try:
        descriptor = os.open(name, flags, mode, dir_fd=directory_fd)
        initial = os.fstat(descriptor)
        identity = (initial.st_dev, initial.st_ino)
        if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1:
            raise ManifestError(f"{label} is not a single-link regular file")
        os.fchmod(descriptor, mode)
        _write_all(descriptor, raw)
        os.fsync(descriptor)
        final = os.fstat(descriptor)
        if (
            (final.st_dev, final.st_ino) != identity
            or final.st_size != len(raw)
            or final.st_nlink != 1
        ):
            raise ManifestError(f"{label} changed during durable write")
        succeeded = True
        return identity
    except FileExistsError as exc:
        raise ManifestError(f"{label} already exists") from exc
    except OSError as exc:
        raise ManifestError(f"cannot write {label}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if not succeeded:
            _unlink_if_owned(directory_fd, name, identity)


def create_ballot_once(
    bound_template: BoundFile,
    path: Path,
    raw: bytes,
    *,
    validate_final: Callable[[dict[str, Any]], object],
) -> None:
    """Create a schema-2 sibling output without replacing any existing path."""

    directory_fd, name = _open_parent_no_follow(path)
    created_identity: tuple[int, int] | None = None
    succeeded = False
    try:
        if name == bound_template.path.name:
            raise ManifestError("schema-2 ballot output must differ from its template")
        _recheck_bound_at(
            bound_template,
            directory_fd,
            label="schema-2 ballot template",
        )
        created_identity = _create_durable_file(
            directory_fd,
            name,
            raw,
            label="schema-2 ballot output",
        )
        os.fsync(directory_fd)
        stored, identity = _read_regular_at(
            directory_fd,
            name,
            expected_size=len(raw),
            max_bytes=max(MAX_MANIFEST_BYTES, len(raw)),
            label="schema-2 ballot output",
        )
        if (
            (identity.device, identity.inode) != created_identity
            or stored != raw
        ):
            raise ManifestError("schema-2 ballot output verification failed")
        validate_final(parse_json_object_bytes(stored, label="schema-2 ballot"))
        _recheck_bound_at(
            bound_template,
            directory_fd,
            label="schema-2 ballot template",
        )
        succeeded = True
    except ManifestError:
        raise
    except OSError as exc:
        raise ManifestError(f"cannot finalize schema-2 ballot: {exc}") from exc
    finally:
        if not succeeded:
            _unlink_if_owned(directory_fd, name, created_identity)
        os.close(directory_fd)


def replace_bound_ballot_once(
    bound_template: BoundFile,
    raw: bytes,
    *,
    validate_final: Callable[[dict[str, Any]], object],
) -> None:
    """Atomically replace one bound schema-3 template exactly once."""

    directory_fd, destination_name = _open_parent_no_follow(bound_template.path)
    lock_name = f".{destination_name}.materialize.lock"
    temp_name = f".{destination_name}.materialize-{secrets.token_hex(16)}.tmp"
    lock_identity: tuple[int, int] | None = None
    temp_identity: tuple[int, int] | None = None
    replaced = False
    succeeded = False
    try:
        lock_identity = _create_durable_file(
            directory_fd,
            lock_name,
            b"",
            label="schema-3 materialization lock",
        )
        os.fsync(directory_fd)
        _recheck_bound_at(
            bound_template,
            directory_fd,
            label="schema-3 ballot template",
        )
        temp_identity = _create_durable_file(
            directory_fd,
            temp_name,
            raw,
            label="schema-3 ballot temporary output",
        )
        stored_temp, temp_stat = _read_regular_at(
            directory_fd,
            temp_name,
            expected_size=len(raw),
            max_bytes=max(MAX_MANIFEST_BYTES, len(raw)),
            label="schema-3 ballot temporary output",
        )
        if (
            (temp_stat.device, temp_stat.inode) != temp_identity
            or stored_temp != raw
            or _sha256_bytes(stored_temp) != _sha256_bytes(raw)
        ):
            raise ManifestError("schema-3 ballot temporary output verification failed")
        _recheck_bound_at(
            bound_template,
            directory_fd,
            label="schema-3 ballot template",
        )
        current_parent_fd, _current_name = _open_parent_no_follow(
            bound_template.path
        )
        try:
            current_parent = os.fstat(current_parent_fd)
            if (current_parent.st_dev, current_parent.st_ino) != (
                os.fstat(directory_fd).st_dev,
                os.fstat(directory_fd).st_ino,
            ):
                raise ManifestError("schema-3 ballot parent directory changed")
        finally:
            os.close(current_parent_fd)
        os.replace(
            temp_name,
            destination_name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        replaced = True
        os.fsync(directory_fd)
        stored_final, final_stat = _read_regular_at(
            directory_fd,
            destination_name,
            expected_size=len(raw),
            max_bytes=max(MAX_MANIFEST_BYTES, len(raw)),
            label="schema-3 final ballot",
        )
        if (
            (final_stat.device, final_stat.inode) != temp_identity
            or stored_final != raw
            or _sha256_bytes(stored_final) != _sha256_bytes(raw)
        ):
            raise ManifestError("schema-3 final ballot identity or digest is invalid")
        final_parent_fd, _final_name = _open_parent_no_follow(bound_template.path)
        try:
            final_parent = os.fstat(final_parent_fd)
            directory = os.fstat(directory_fd)
            if (final_parent.st_dev, final_parent.st_ino) != (
                directory.st_dev,
                directory.st_ino,
            ):
                raise ManifestError("schema-3 final ballot parent directory changed")
        finally:
            os.close(final_parent_fd)
        validate_final(
            parse_json_object_bytes(stored_final, label="schema-3 final ballot")
        )
        if lock_identity is None:  # pragma: no cover - lock creation succeeded above.
            raise ManifestError("schema-3 materialization lock ownership is missing")
        _unlink_owned_or_raise(
            directory_fd,
            lock_name,
            lock_identity,
            label="schema-3 materialization lock",
        )
        lock_identity = None
        os.fsync(directory_fd)
        succeeded = True
    except ManifestError:
        raise
    except OSError as exc:
        raise ManifestError(f"cannot finalize schema-3 ballot: {exc}") from exc
    finally:
        if not replaced:
            _unlink_if_owned(directory_fd, temp_name, temp_identity)
            _unlink_if_owned(directory_fd, lock_name, lock_identity)
        elif succeeded:
            _unlink_if_owned(directory_fd, lock_name, lock_identity)
        os.close(directory_fd)


def promote_bound_file_atomically(
    bound_source: BoundFile,
    destination: Path,
    *,
    bound_existing: BoundFile | None,
    max_bytes: int,
    validate_final: Callable[[bytes], object],
) -> None:
    """CAS-promote bound bytes through a restrictive, verified sibling temp."""

    directory_fd, destination_name = _open_parent_no_follow(destination)
    temp_name = f".{destination_name}.promote-{secrets.token_hex(16)}.tmp"
    rollback_name = f".{destination_name}.rollback-{secrets.token_hex(16)}.tmp"
    temp_identity: tuple[int, int] | None = None
    rollback_identity: tuple[int, int] | None = None
    replaced = False
    final_identity: tuple[int, int] | None = None
    try:
        _recheck_destination_cas(
            directory_fd,
            destination_name,
            bound_existing=bound_existing,
            label="attestation destination",
        )
        recheck_bound_file(bound_source, label="attestation promotion source")
        validate_final(bound_source.raw)
        temp_identity = _create_durable_file(
            directory_fd,
            temp_name,
            bound_source.raw,
            label="attestation promotion temporary output",
            mode=0o600,
        )
        stored_temp, temp_stat = _read_regular_at(
            directory_fd,
            temp_name,
            expected_size=len(bound_source.raw),
            max_bytes=max_bytes,
            label="attestation promotion temporary output",
        )
        if (
            (temp_stat.device, temp_stat.inode) != temp_identity
            or stored_temp != bound_source.raw
        ):
            raise ManifestError("attestation promotion temporary output is stale")
        validate_final(stored_temp)
        if bound_existing is not None:
            rollback_identity = _create_durable_file(
                directory_fd,
                rollback_name,
                bound_existing.raw,
                label="attestation promotion rollback copy",
                mode=bound_existing.identity.mode,
            )
        recheck_bound_file(bound_source, label="attestation promotion source")
        _recheck_destination_cas(
            directory_fd,
            destination_name,
            bound_existing=bound_existing,
            label="attestation destination",
        )
        os.replace(
            temp_name,
            destination_name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        replaced = True
        final_identity = temp_identity
        temp_identity = None
        os.fsync(directory_fd)
        stored_final, final_stat = _read_regular_at(
            directory_fd,
            destination_name,
            expected_size=len(bound_source.raw),
            max_bytes=max_bytes,
            label="promoted attestation",
        )
        if (
            (final_stat.device, final_stat.inode) != final_identity
            or stored_final != bound_source.raw
        ):
            raise ManifestError("promoted attestation identity or bytes are stale")
        validate_final(stored_final)
        if rollback_identity is not None:
            _unlink_owned_or_raise(
                directory_fd,
                rollback_name,
                rollback_identity,
                label="attestation promotion rollback copy",
            )
            rollback_identity = None
        os.fsync(directory_fd)
    except Exception:
        if replaced:
            try:
                if final_identity is None:
                    raise ManifestError(
                        "failed promoted attestation ownership is missing"
                    )
                promoted, promoted_identity = _read_regular_at(
                    directory_fd,
                    destination_name,
                    expected_size=len(bound_source.raw),
                    max_bytes=max_bytes,
                    label="failed promoted attestation",
                )
                if (
                    (promoted_identity.device, promoted_identity.inode)
                    != final_identity
                    or promoted != bound_source.raw
                    or _sha256_bytes(promoted) != bound_source.sha256
                ):
                    raise ManifestError(
                        "failed promoted attestation is no longer owned by rollback"
                    )
                if bound_existing is not None and rollback_identity is not None:
                    os.replace(
                        rollback_name,
                        destination_name,
                        src_dir_fd=directory_fd,
                        dst_dir_fd=directory_fd,
                    )
                    rollback_identity = None
                    os.fsync(directory_fd)
                    restored, restored_identity = _read_regular_at(
                        directory_fd,
                        destination_name,
                        expected_size=len(bound_existing.raw),
                        max_bytes=max_bytes,
                        label="restored attestation destination",
                    )
                    if (
                        restored != bound_existing.raw
                        or restored_identity.mode
                        != bound_existing.identity.mode
                    ):
                        raise ManifestError(
                            "restored attestation destination state is stale"
                        )
                elif bound_existing is None:
                    _unlink_owned_or_raise(
                        directory_fd,
                        destination_name,
                        final_identity,
                        label="failed promoted attestation",
                    )
                    os.fsync(directory_fd)
            except Exception as rollback_exc:
                raise ManifestError(
                    "attestation promotion failed and destination rollback failed"
                ) from rollback_exc
        raise
    finally:
        _unlink_if_owned(directory_fd, temp_name, temp_identity)
        _unlink_if_owned(directory_fd, rollback_name, rollback_identity)
        os.close(directory_fd)


def _recheck_destination_cas(
    directory_fd: int,
    name: str,
    *,
    bound_existing: BoundFile | None,
    label: str,
) -> None:
    if bound_existing is None:
        try:
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ManifestError(f"cannot inspect {label}: {exc}") from exc
        raise ManifestError(f"{label} was created before commit")
    if bound_existing.path.name != name:
        raise ManifestError(f"{label} CAS path is invalid")
    _recheck_bound_at(bound_existing, directory_fd, label=label)


__all__ = [
    "BoundFile",
    "CHUNK_PROTOCOL",
    "CHUNK_PROTOCOL_VERSION",
    "FileIdentity",
    "MANIFEST_KIND",
    "MANIFEST_SCHEMA_VERSION",
    "MAX_CHUNK_BASE64_CHARS",
    "MAX_CHUNK_COUNT",
    "MAX_CHUNK_ENVELOPE_BYTES",
    "MAX_CHUNK_RAW_BYTES",
    "MAX_MANIFEST_BYTES",
    "MAX_RECORD_BYTES",
    "MAX_REVIEWER_MANIFEST_BYTES",
    "ManifestError",
    "bind_regular_file",
    "canonical_ballot_bytes",
    "create_ballot_once",
    "encode_manifest_records",
    "materialize_manifest",
    "parse_json_object_bytes",
    "parse_manifest_bytes",
    "project_ballot_to_manifest",
    "promote_bound_file_atomically",
    "read_framed_manifest_stream",
    "read_manifest_file",
    "read_raw_manifest_stream",
    "read_bound_regular_file",
    "recheck_bound_file",
    "replace_bound_ballot_once",
]
