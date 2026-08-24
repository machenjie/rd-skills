#!/usr/bin/env python3
"""Versioned deterministic Capsule contract for evaluation fixtures only.

This module is test infrastructure. It is not copied by ``scripts/build.py``, is
not installed as a Skill or Agent Profile, and does not compile runtime task
state. Both deterministic trajectory evaluators use it so the checked-in
structured fixture is the sole source for the exact Capsule text being measured.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import unicodedata
from collections import Counter
from pathlib import PurePosixPath
from typing import Any

from validation_utils import (
    COMPLETION_STATE_MODEL,
    EVIDENCE_LEDGER_MODEL,
    EXECUTION_LEVEL_MODEL,
    REVIEW_DISCIPLINE_MODEL,
    TASK_CONTRACT_MODEL,
    ExecutionLevelError,
    compute_execution_level,
    execution_level_integrity_fallback,
)


CONTRACT_VERSION = "changeforge.fixture-capsule.v2"
PLACEHOLDERS = {"x", "xx", "n/a", "none", "placeholder", "tbd", "todo", "unknown"}
PLACEHOLDER_ROOTS = {"none", "placeholder", "tbd", "todo", "unknown"}
STRICT_PLACEHOLDER_ROOTS = {"placeholder", "tbd", "todo"}
KNOWN_COMMANDS = {
    "bash",
    "bun",
    "bundle",
    "cargo",
    "cmake",
    "composer",
    "deno",
    "dotnet",
    "git",
    "go",
    "gradle",
    "gradlew",
    "java",
    "javac",
    "make",
    "mvn",
    "mypy",
    "ninja",
    "node",
    "npm",
    "npx",
    "php",
    "pnpm",
    "pytest",
    "python",
    "python3",
    "rake",
    "rg",
    "ruby",
    "ruff",
    "sh",
    "swift",
    "tox",
    "unittest",
    "uv",
    "yarn",
    "zsh",
}
MIN_PROSE_UNIQUE_TOKENS = 2
MIN_LONG_PROSE_DIVERSITY = 0.15
MAX_LONG_PROSE_TOKEN_SHARE = 0.90
_LEXICAL_RE = re.compile(r"[A-Za-z0-9]+|[\u3400-\u9fff]")
_PATH_PART_RE = re.compile(r"[A-Za-z0-9_.?*+@,\[\]{}-]+")
_TECHNICAL_IDENTIFIER_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9_+~-]*|[A-Za-z0-9]+(?:[._:~+/-][A-Za-z0-9*+_-]+)+"
)
_PLACEHOLDER_VALUE_RE = re.compile(
    r"(?:x+|n[\\/]?a|none|unknown|placeholder(?:[_-]?\d+)?|tbd(?:[_-]?\d+)?|todo(?:[_-]?\d+)?)[.!?…]*",
    re.IGNORECASE,
)
_STRICT_PLACEHOLDER_AFFIX_RE = re.compile(
    r"(?:(?:placeholder|tbd)(?:[_:-].+|[A-Za-z0-9]+)|.+(?:[_:-](?:placeholder|tbd)|(?:placeholder|tbd)))",
    re.IGNORECASE,
)
_REPEATED_PLACEHOLDER_RE = re.compile(
    r"(?:(?:placeholder|tbd|todo)){2,}\d*",
    re.IGNORECASE,
)
_SHELL_METACHAR_RE = re.compile(r"[;&|<>`$()]")
_LAYER3_OWNER_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_LAYER3_REFERENCE_NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]*\.md\Z")
_LAYER3_REFERENCE_FORBIDDEN_CHARS = frozenset("?#*[]{}")
_LAYER3_REFERENCE_FORBIDDEN_NAMES = frozenset({"index.md", "catalog.md"})
UTILITY_MODES = {"diff-export/no-edit", "validation-only/no-edit"}
NO_EDIT_ENFORCEMENTS = {"supported"}
CHANGE_SET_RE = re.compile(r"(?:tracked|staged|untracked):(none|present|changed)")
TYPE_TO_ROLE = {
    "analysis": "analysis-agent",
    "task": "task-agent",
    "review": "review-agent",
    "utility": "task-agent",
}
ANALYSIS_MODE_TEMPLATES = {
    "implementation-preparation": "engineering-brief",
    "diagnosis-only": "diagnosis",
    "source-backed-answer": "source-backed-answer",
}
TEMPLATES = {
    "analysis": set(ANALYSIS_MODE_TEMPLATES.values()),
    "task": {"direct-task", "implementation-task", "repair-task", "integration-task"},
    "review": {"review-handoff"},
    "utility": {"utility-capsule"},
}
COMMON_FIELDS = ("contract_version", "contract_type", "template")


def _fixture_field_name(contract_field: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", contract_field.casefold()).strip("_")


TASK_PAYLOAD_FIELDS = tuple(
    _fixture_field_name(field) for field in TASK_CONTRACT_MODEL["fields"]
)
EXECUTION_LEVEL_EXTENSION_FIELD = "execution_level_extension"
EXECUTION_LEVEL_PAYLOAD_FIELDS = tuple(
    _fixture_field_name(field)
    for field in TASK_CONTRACT_MODEL["execution_level_extension"]["fields"]
)
TYPE_FIELDS = {
    "analysis": (
        *COMMON_FIELDS,
        "goal",
        "scope",
        "evidence",
        "validation",
        "stop_conditions",
        "output",
        "canonical_sha256",
    ),
    "task": (
        *COMMON_FIELDS,
        *TASK_PAYLOAD_FIELDS,
        "canonical_sha256",
    ),
    "review": (
        *COMMON_FIELDS,
        "goal",
        "scope",
        "inputs",
        "acceptance",
        "validation",
        "stop_conditions",
        "output",
        "canonical_sha256",
    ),
    "utility": (
        *COMMON_FIELDS,
        "canonical_sha256",
    ),
}
EXTENDED_TYPE_FIELDS = {
    "task": (
        *COMMON_FIELDS,
        TASK_PAYLOAD_FIELDS[0],
        EXECUTION_LEVEL_EXTENSION_FIELD,
        *TASK_PAYLOAD_FIELDS[1:],
        "canonical_sha256",
    ),
    "review": (
        *COMMON_FIELDS,
        "task_id",
        EXECUTION_LEVEL_EXTENSION_FIELD,
        "goal",
        "scope",
        "inputs",
        "acceptance",
        "validation",
        "stop_conditions",
        "output",
        "canonical_sha256",
    ),
}
UTILITY_ASSIGNMENT_FIELDS = (
    "task_id",
    "status",
    "owner",
    "mode",
    "no_edit_enforcement",
    "goal",
    "allowed_scope",
    "inputs",
    "workspace_baseline",
    "commands_allowed",
    "expected_evidence",
    "stop_conditions",
    "evidence_ledger",
)
UTILITY_FIELDS = UTILITY_ASSIGNMENT_FIELDS
UTILITY_RETURN_FIELDS = (
    "task_id",
    "status",
    "owner",
    "mode",
    "no_edit_enforcement",
    "artifact_or_check_outcomes",
    "commands_run",
    "workspace_diff_check",
    "evidence_ledger",
    "unverified_scope",
    "residual_risk",
)
UTILITY_ASSIGNMENT_REQUIRED_CLAIMS = ("workspace baseline captured",)
UTILITY_RETURN_REQUIRED_CLAIMS = ("workspace unchanged", "utility result delivered")
UTILITY_CAPABILITY_OPERATIONS = {
    "workspace-state-observation",
    "change-evidence-export",
    "non-mutating-validation",
}
COMPLETION_CLAIM_FIELDS = (
    "request_kind",
    "status",
    "task_id",
    "owner",
    "requested_result_fully_delivered",
    "required_claims",
    "required_freshness_marker",
    "latest_material_edit_marker",
    "validation",
    "high_risk_review",
    "blocking_findings",
    "changed_scope_reviewed",
    "proof_limits_stated",
    "evidence_ledger",
)
COMPLETION_REVIEW_BINDING_FIELD = "review_requirement_binding"
EXTENDED_COMPLETION_CLAIM_FIELDS = (
    *COMPLETION_CLAIM_FIELDS[:-1],
    COMPLETION_REVIEW_BINDING_FIELD,
    COMPLETION_CLAIM_FIELDS[-1],
)
COMPLETION_REQUEST_KINDS = {"implementation", "diagnosis", "answer"}
COMPLETION_VALIDATION_RESULTS = {"passed", "failed", "unavailable", "not-required"}
COMPLETION_REVIEW_RESULTS = {"passed", "missing", "not-required"}
COMPLETION_FINDING_RESULTS = {"none", "resolved", "unresolved"}
COMBINED_REVIEW_BOUNDARY_MODEL = REVIEW_DISCIPLINE_MODEL[
    "review_boundary_contract"
]


class FixtureCapsuleError(ValueError):
    """Raised when a fixture Capsule is incomplete, stale, or non-canonical."""


def execution_level_migration_errors(
    payload: object,
    *,
    lifecycle_status: str,
    next_action: str,
    step: dict[str, Any] | None = None,
) -> list[str]:
    """Gate legacy v2 work, exempting only completed read-only access."""

    if not isinstance(payload, dict):
        return ["legacy migration requires a fixture_capsule mapping"]
    if lifecycle_status not in {"in_progress", "blocked", "partial", "completed"}:
        return ["legacy migration lifecycle status is not Core-approved"]
    if next_action not in {"read", "edit", "validation", "review"}:
        return ["legacy migration next action is not classified"]
    if EXECUTION_LEVEL_EXTENSION_FIELD in payload:
        if not isinstance(step, dict):
            return [
                "execution-level migration needs the dispatch step to validate full payload shape"
            ]
        try:
            allow_legacy_read = lifecycle_status == "completed" and next_action == "read"
            _active_execution_decision(
                payload[EXECUTION_LEVEL_EXTENSION_FIELD],
                EXECUTION_LEVEL_MODEL,
                allow_legacy_read=allow_legacy_read,
            )
            _validate_payload_shape(
                step,
                payload,
                allow_legacy_execution_read=allow_legacy_read,
            )
        except FixtureCapsuleError as exc:
            return [f"execution-level migration extension is invalid: {exc}"]
        return []
    if lifecycle_status == "completed" and next_action == "read":
        return []
    return [
        "legacy v2 Capsule is exempt only for completed/read; reissue with the execution level extension before active or resumed work, edit, validation, or review"
    ]


_TRACE_EXECUTION_ACTIONS = {
    "edit": "edit",
    "repair": "edit",
    "validate": "validation",
    "validation": "validation",
    "finding": "review",
    "review": "review",
    "re-review": "review",
}


def trace_execution_level_migration_errors(
    steps: object,
    dispatch_index: int,
    *,
    lifecycle_status: str | None = None,
) -> list[str]:
    """Classify one trace dispatch and apply the additive legacy migration gate."""

    if (
        not isinstance(steps, list)
        or not isinstance(dispatch_index, int)
        or isinstance(dispatch_index, bool)
        or not 0 <= dispatch_index < len(steps)
    ):
        return ["trace migration classifier requires a valid dispatch index"]
    step = steps[dispatch_index]
    if not isinstance(step, dict) or step.get("action") != "dispatch":
        return ["trace migration classifier requires a dispatch step"]
    payload = step.get("fixture_capsule")
    if not isinstance(payload, dict):
        return ["legacy migration requires a fixture_capsule mapping"]
    if payload.get("contract_type") not in {"task", "review"}:
        return []

    status = lifecycle_status
    if status is None:
        raw_status = payload.get("status")
        status = raw_status if isinstance(raw_status, str) else "in_progress"

    read_seen = False
    next_action: str | None = None
    parallel_batch = step.get("parallel_batch")
    for candidate in steps[dispatch_index + 1 :]:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("action") == "dispatch":
            if (
                parallel_batch is not None
                and candidate.get("parallel_batch") == parallel_batch
            ):
                continue
            break
        action = candidate.get("action")
        if action == "read":
            read_seen = True
            continue
        classified = _TRACE_EXECUTION_ACTIONS.get(action)
        if classified is not None:
            next_action = classified
            break
    if next_action is None and read_seen:
        next_action = "read"
    if next_action is None:
        mode = step.get("mode")
        if mode == "repair":
            next_action = "edit"
        elif isinstance(mode, str) and "review" in mode:
            next_action = "review"
        else:
            return ["trace migration classifier could not determine the next action"]
    errors = execution_level_migration_errors(
        payload,
        lifecycle_status=status,
        next_action=next_action,
        step=step,
    )
    return [f"classified next action {next_action}: {error}" for error in errors]


def _fixture_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def completion_transition_errors(
    from_status: object,
    to_status: object,
    *,
    same_task_id: bool = True,
) -> list[str]:
    """Validate one explicit completion transition without runtime state."""

    statuses = set(COMPLETION_STATE_MODEL["statuses"])
    errors: list[str] = []
    if from_status not in statuses:
        errors.append(f"unknown source completion status {from_status!r}")
    if to_status not in statuses:
        errors.append(f"unknown target completion status {to_status!r}")
    if not isinstance(same_task_id, bool):
        errors.append("same_task_id must be boolean")
    if errors:
        return errors

    assert isinstance(from_status, str) and isinstance(to_status, str)
    if from_status == to_status:
        return [f"completion status must change; self-transition {from_status!r} is invalid"]

    terminals = set(COMPLETION_STATE_MODEL["terminal_statuses"])
    if from_status in terminals:
        new_work = COMPLETION_STATE_MODEL["new_work_after_completion"]
        if same_task_id:
            return [
                f"terminal completion status {from_status!r} cannot transition on the same Task ID"
            ]
        if to_status != new_work["initial_status"]:
            return [
                "new work after completion must start with a new Task ID at "
                f"{new_work['initial_status']!r}"
            ]
        return []

    if not same_task_id:
        return ["an unfinished Task Contract must keep the same Task ID"]
    allowed = COMPLETION_STATE_MODEL["allowed_transitions"][from_status]
    if to_status not in allowed:
        return [
            f"completion transition {from_status!r} -> {to_status!r} is not allowed"
        ]
    return []


def evidence_ledger_errors(
    ledger: object,
    *,
    task_id: str,
    owner: str,
    additional_owners: tuple[str, ...] = (),
    required_claims: list[str],
    required_freshness_marker: int,
    latest_material_edit_marker: int | None,
    completion_status: str,
) -> list[str]:
    """Validate a fixture-only visible ledger without storing runtime state."""

    if not isinstance(ledger, list):
        return ["Evidence Ledger must be a list"]
    fields = tuple(EVIDENCE_LEDGER_MODEL["fields"])
    states = set(EVIDENCE_LEDGER_MODEL["states"])
    errors: list[str] = []
    visible_rows: list[dict[str, Any]] = []
    allowed_owners = {owner, *additional_owners}

    for index, row in enumerate(ledger):
        context = f"Evidence Ledger row {index}"
        visible = _visible_evidence_row(row)
        if visible is None or tuple(visible) != fields:
            errors.append(f"{context} must use exact ordered fields {list(fields)}")
            continue
        visible_rows.append(visible)
        for field in (
            "Owner",
            "Claim",
            "Artifact",
            "Command",
            "Result",
            "Scope",
            "Proof Limit",
        ):
            if not _fixture_nonempty_text(visible[field]):
                errors.append(f"{context} {field} must be non-empty text")
        if visible["Owner"] not in allowed_owners:
            if len(allowed_owners) == 1:
                errors.append(f"{context} Owner must equal {owner!r}")
            else:
                errors.append(
                    f"{context} Owner must be one of {sorted(allowed_owners)!r}"
                )
        marker = visible["Freshness"]
        if not isinstance(marker, int) or isinstance(marker, bool) or marker < 0:
            errors.append(f"{context} Freshness must be a non-negative integer")
        elif visible["State"] == "current" and marker < required_freshness_marker:
            errors.append(
                f"stale current Evidence Ledger row {index}: marker {marker} "
                f"is older than required marker {required_freshness_marker}"
            )
        if visible["State"] not in states:
            errors.append(
                f"invalid Evidence Ledger state {visible['State']!r}"
            )

    if completion_status == "completed":
        current_claims = {
            row["Claim"]
            for row in visible_rows
            if row["State"] == "current"
            and isinstance(row["Freshness"], int)
            and not isinstance(row["Freshness"], bool)
            and row["Freshness"] >= required_freshness_marker
            and row["Owner"] == owner
        }
        for required_claim in required_claims:
            if required_claim in current_claims:
                continue
            noncurrent = any(
                row["Claim"] == required_claim
                and row["State"] != "current"
                for row in visible_rows
            )
            if noncurrent:
                errors.append(
                    f"required claim {required_claim!r} is supported only by "
                    "superseded or invalid evidence"
                )
            else:
                errors.append(
                    f"completed missing current evidence for required claim "
                    f"{required_claim!r}"
                )
    return errors


_LEGACY_FIXTURE_EVIDENCE_FIELDS = (
    "Evidence ID",
    "Task ID",
    "Owner",
    "Claim",
    "Action",
    "Artifact",
    "Command",
    "Result",
    "Freshness Marker",
    "Scope",
    "Proof Limit",
    "Evidence State",
    "Supersedes",
)


def _visible_evidence_row(value: object) -> dict[str, Any] | None:
    """Project fixture source data to the active nine-field visible Ledger.

    The legacy input shape is accepted only as non-runtime fixture migration
    input. It is never emitted into an active capsule.
    """

    if not isinstance(value, dict):
        return None
    fields = tuple(EVIDENCE_LEDGER_MODEL["fields"])
    if tuple(value) == fields:
        return dict(value)
    if tuple(value) != _LEGACY_FIXTURE_EVIDENCE_FIELDS:
        return None
    return {
        "Claim": value["Claim"],
        "Owner": value["Owner"],
        "Artifact": value["Artifact"],
        "Command": value["Command"],
        "Result": value["Result"],
        "Freshness": value["Freshness Marker"],
        "Scope": value["Scope"],
        "Proof Limit": value["Proof Limit"],
        "State": value["Evidence State"],
    }


def _completion_review_authority_errors(
    binding: object,
    *,
    task_id: str,
    review_authority: object,
) -> tuple[list[str], bool]:
    """Bind a digest-only claim to authoritative task and review dispatches."""

    requirement = EVIDENCE_LEDGER_MODEL["completion_proof"]["implementation"][
        "high_risk_review_requirement"
    ]
    fields = tuple(requirement["binding_fields"])
    if not isinstance(binding, dict) or tuple(binding) != fields:
        return (
            [
                "review requirement binding must be digest-only and use exact "
                "ordered fields "
                f"{list(fields)}"
            ],
            True,
        )

    errors: list[str] = []
    digest = binding["capsule_canonical_sha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        errors.append("review requirement binding capsule digest is invalid")

    authority_fields = tuple(requirement["authority_fields"])
    if (
        not isinstance(review_authority, dict)
        or tuple(review_authority) != authority_fields
    ):
        errors.append(
            "review requirement authority is missing or invalid; reissue with "
            "authoritative task and review dispatches"
        )
        return errors, True

    task_dispatch = review_authority["task_dispatch"]
    review_assignment = review_authority["review_assignment"]
    actor = requirement["authority_actor"]
    task_profile = requirement["authority_task_profile"]
    review_profile = requirement["authority_review_profile"]
    if (
        not isinstance(task_dispatch, dict)
        or task_dispatch.get("actor") != actor
        or task_dispatch.get("action") != "dispatch"
        or task_dispatch.get("profile") != task_profile
    ):
        errors.append("review requirement task dispatch authority is invalid")
        return errors, True
    task_capsule = task_dispatch.get("fixture_capsule")
    if (
        not isinstance(task_capsule, dict)
        or task_capsule.get("contract_type") != "task"
        or task_capsule.get("contract_version")
        != requirement["capsule_contract_version"]
        or task_capsule.get("task_id") != task_id
    ):
        errors.append(
            "review requirement task Capsule authority does not match completion task"
        )
        return errors, True
    try:
        actual_digest = canonical_capsule_sha256(task_dispatch, task_capsule)
    except FixtureCapsuleError as exc:
        errors.append(f"review requirement task Capsule authority is invalid: {exc}")
        return errors, True
    if task_capsule.get("canonical_sha256") != actual_digest:
        errors.append(
            "review requirement task Capsule canonical digest does not match "
            "the deterministic render"
        )
    if digest != actual_digest:
        errors.append(
            "review requirement binding capsule digest does not match "
            "the authoritative task Capsule"
        )

    if (
        not isinstance(review_assignment, dict)
        or review_assignment.get("actor") != actor
        or review_assignment.get("action") != "dispatch"
        or review_assignment.get("profile") != review_profile
    ):
        errors.append("review requirement Review assignment authority is invalid")
        return errors, True
    review_capsule = review_assignment.get("fixture_capsule")
    if (
        not isinstance(review_capsule, dict)
        or review_capsule.get("contract_type") != "review"
        or review_capsule.get("contract_version")
        != requirement["capsule_contract_version"]
        or review_capsule.get("task_id") != task_id
    ):
        errors.append(
            "review requirement Review assignment does not cover the completion task"
        )
        return errors, True
    try:
        review_digest = canonical_capsule_sha256(review_assignment, review_capsule)
    except FixtureCapsuleError as exc:
        errors.append(f"review requirement Review assignment is invalid: {exc}")
        return errors, True
    if review_capsule.get("canonical_sha256") != review_digest:
        errors.append(
            "review requirement Review assignment canonical digest does not match "
            "the deterministic render"
        )

    ranks = _closed_execution_level_ranks(EXECUTION_LEVEL_MODEL)
    high_risk_floor = requirement["high_risk_floor"]
    extension = task_capsule.get(EXECUTION_LEVEL_EXTENSION_FIELD)
    if not isinstance(extension, dict):
        errors.append(
            "review requirement task Capsule lacks authoritative execution level"
        )
        return errors, True
    level_fields = (
        "effective_level",
        "historical_max_floor",
        "historical_max_effective",
    )
    for field in level_fields:
        if extension.get(field) not in ranks:
            errors.append(
                f"review requirement task Capsule {field} is invalid"
            )

    registry = EXECUTION_LEVEL_MODEL["trigger_registry"]
    basis = extension.get("level_basis")
    trigger_rows = (
        basis.get("trigger_evaluations") if isinstance(basis, dict) else None
    )
    trigger_evaluations: dict[str, dict[str, Any]] = {}
    if not isinstance(trigger_rows, list) or len(trigger_rows) != len(registry):
        errors.append(
            "review requirement task Capsule must cover the trigger registry"
        )
    else:
        for index, (row, contract_row) in enumerate(zip(trigger_rows, registry)):
            if not isinstance(row, dict):
                errors.append(
                    f"review requirement task Capsule trigger row {index} is invalid"
                )
                continue
            if row["id"] != contract_row["id"]:
                errors.append(
                    "review requirement task Capsule trigger rows are out of order"
                )
                continue
            material_candidate = (
                contract_row["floor"] == "L4"
                and contract_row["id"]
                not in {"formal-release-declared", "unknown-critical-boundary"}
            )
            allowed_statuses = (
                set(EXECUTION_LEVEL_MODEL["material_candidate_statuses"])
                if material_candidate
                else {"matched", "not_matched", "unknown"}
            )
            if row["status"] not in allowed_statuses:
                errors.append(
                    "review requirement task Capsule trigger "
                    f"{row['id']!r} status is invalid"
                )
                continue
            trigger_evaluations[row["id"]] = row

    low_risk_strategy = requirement["low_risk_review_strategy"]
    high_risk_strategies = set(requirement["high_risk_review_strategies"])
    strategy = (
        low_risk_strategy
        if review_assignment.get("mode") == requirement["low_risk_review_mode"]
        else "independent-high-risk-review"
    )

    high_risk_required = bool(errors)
    if not high_risk_required:
        high_risk_required = any(
            ranks[extension[field]] >= ranks[high_risk_floor]
            for field in level_fields
        )
        critical_statuses = set(requirement["critical_trigger_statuses"])
        high_risk_required = high_risk_required or any(
            ranks[row["floor"]] >= ranks[high_risk_floor]
            and trigger_evaluations.get(row["id"], {}).get("status")
            in critical_statuses
            for row in registry
        )
        provisional = requirement["provisional_critical_trigger"]
        provisional_row = trigger_evaluations.get(provisional["id"], {})
        high_risk_required = high_risk_required or (
            provisional_row.get("status") == provisional["status"]
            and provisional_row.get(provisional["flag"]) is True
        )
        high_risk_required = high_risk_required or strategy in high_risk_strategies
    return errors, high_risk_required


def completion_claim_errors(
    claim: object,
    *,
    review_authority: object = None,
) -> list[str]:
    """Evaluate one fixture-only completion claim against static contracts."""

    if not isinstance(claim, dict):
        return ["completion claim must be a mapping"]
    if tuple(claim) not in {
        COMPLETION_CLAIM_FIELDS,
        EXTENDED_COMPLETION_CLAIM_FIELDS,
    }:
        return [
            "completion claim must use exact ordered fields "
            f"{list(COMPLETION_CLAIM_FIELDS)} or "
            f"{list(EXTENDED_COMPLETION_CLAIM_FIELDS)}"
        ]

    errors: list[str] = []
    request_kind = claim["request_kind"]
    status = claim["status"]
    validation = claim["validation"]
    review = claim["high_risk_review"]
    findings = claim["blocking_findings"]
    task_id = claim["task_id"]
    owner = claim["owner"]
    implementation_proof = EVIDENCE_LEDGER_MODEL["completion_proof"][
        "implementation"
    ]
    required_claims = claim["required_claims"]
    required_marker = claim["required_freshness_marker"]
    latest_edit = claim["latest_material_edit_marker"]
    review_binding = claim.get(COMPLETION_REVIEW_BINDING_FIELD)
    if request_kind not in COMPLETION_REQUEST_KINDS:
        errors.append(f"unknown request_kind {request_kind!r}")
    if status not in COMPLETION_STATE_MODEL["statuses"]:
        errors.append(f"unknown completion status {status!r}")
    if validation not in COMPLETION_VALIDATION_RESULTS:
        errors.append(f"unknown validation result {validation!r}")
    if review not in COMPLETION_REVIEW_RESULTS:
        errors.append(f"unknown high-risk review result {review!r}")
    if findings not in COMPLETION_FINDING_RESULTS:
        errors.append(f"unknown blocking finding result {findings!r}")
    if not _fixture_nonempty_text(task_id) or not _fixture_nonempty_text(owner):
        errors.append("task_id and owner must be non-empty text")
    if request_kind == "implementation" and owner != implementation_proof[
        "implementation_owner_role"
    ]:
        errors.append(
            "implementation completion claim owner must equal "
            f"{implementation_proof['implementation_owner_role']!r}"
        )
    if not isinstance(required_claims, list) or not required_claims or any(
        not _fixture_nonempty_text(item) for item in required_claims
    ):
        errors.append("required_claims must be a non-empty string list")
    elif len(required_claims) != len(set(required_claims)):
        errors.append("required_claims must not contain duplicates")
    if not isinstance(required_marker, int) or isinstance(required_marker, bool) or required_marker < 0:
        errors.append("required_freshness_marker must be a non-negative integer")
    if latest_edit is not None and (
        not isinstance(latest_edit, int) or isinstance(latest_edit, bool) or latest_edit < 0
    ):
        errors.append("latest_material_edit_marker must be null or a non-negative integer")
    if request_kind == "implementation" and status == "completed":
        if latest_edit is None:
            errors.append(
                "completed implementation requires latest_material_edit_marker"
            )
        elif (
            isinstance(required_marker, int)
            and not isinstance(required_marker, bool)
            and required_marker != latest_edit
        ):
            errors.append(
                "completed implementation requires required_freshness_marker "
                "to equal latest_material_edit_marker"
            )
    for field in (
        "requested_result_fully_delivered",
        "changed_scope_reviewed",
        "proof_limits_stated",
    ):
        if not isinstance(claim[field], bool):
            errors.append(f"{field} must be boolean")
    if errors:
        return errors

    if (
        request_kind == "implementation"
        and status == "completed"
        and review == "not-required"
    ):
        if review_binding is None:
            requirement = implementation_proof["high_risk_review_requirement"]
            errors.append(
                "high-risk review not-required requires a current review requirement "
                "binding; reissue the completion claim with "
                f"{requirement['legacy_not_required']}"
            )
        else:
            binding_errors, high_risk_required = _completion_review_authority_errors(
                review_binding,
                task_id=task_id,
                review_authority=review_authority,
            )
            errors.extend(binding_errors)
            if high_risk_required:
                errors.append(
                    "high-risk review is required by the current task Capsule binding"
                )
    elif review_binding is not None:
        binding_errors, _high_risk_required = _completion_review_authority_errors(
            review_binding,
            task_id=task_id,
            review_authority=review_authority,
        )
        errors.extend(binding_errors)
    if errors:
        return errors

    review_owner = implementation_proof["independent_review_owner"]
    ledger_required_claims = list(required_claims)
    if request_kind == "implementation" and status == "completed":
        ledger_required_claims.append(
            implementation_proof["latest_material_edit_claim"]
        )
        ledger_required_claims.append(implementation_proof["validation_claim"])
    ledger_errors = evidence_ledger_errors(
        claim["evidence_ledger"],
        task_id=task_id,
        owner=owner,
        additional_owners=(review_owner,) if request_kind == "implementation" else (),
        required_claims=ledger_required_claims,
        required_freshness_marker=required_marker,
        latest_material_edit_marker=latest_edit,
        completion_status=status,
    )
    errors.extend(ledger_errors)

    active_rules: list[str] = []
    if validation == "failed":
        active_rules.append("validation-failed")
    elif validation == "unavailable":
        active_rules.append("validation-unavailable")
    if review == "missing":
        active_rules.append("high-risk-review-missing")
    if findings == "unresolved":
        active_rules.append("blocking-finding-unresolved")
    if not claim["changed_scope_reviewed"]:
        active_rules.append("changed-scope-unreviewed")
    if any("stale current Evidence Ledger row" in error for error in ledger_errors):
        active_rules.append("evidence-stale-after-edit")

    fail_closed_rules = COMPLETION_STATE_MODEL["fail_closed_rules"]
    for rule in active_rules:
        allowed = fail_closed_rules[rule]
        if status not in allowed:
            errors.append(f"{rule}: status {status!r} must be one of {allowed}")

    if status == "completed":
        if not claim["requested_result_fully_delivered"]:
            errors.append("completed requires the requested result to be fully delivered")
        if not claim["proof_limits_stated"]:
            errors.append("completed requires explicit proof limits")
        if request_kind == "implementation":
            if validation != "passed":
                errors.append(
                    "completed implementation requires validation='passed'"
                )
            latest_edit_claim = implementation_proof["latest_material_edit_claim"]
            visible_rows = [
                visible
                for row in claim["evidence_ledger"]
                if (visible := _visible_evidence_row(row)) is not None
            ]
            current_latest_edit_markers = {
                row["Freshness"]
                for row in visible_rows
                if row["Owner"] == owner
                and row["Claim"] == latest_edit_claim
                and row["State"] == "current"
                and isinstance(row["Freshness"], int)
                and not isinstance(row["Freshness"], bool)
            }
            if latest_edit is not None and current_latest_edit_markers != {latest_edit}:
                errors.append(
                    "completed implementation requires one current task-owner "
                    f"{latest_edit_claim!r} evidence marker equal to {latest_edit}"
                )
            required_review_claims: list[str] = []
            for field, claim_by_value in implementation_proof[
                "required_review_claims"
            ].items():
                raw_value = claim[field]
                value_key = (
                    str(raw_value).casefold()
                    if isinstance(raw_value, bool)
                    else str(raw_value)
                )
                required_review_claim = claim_by_value.get(value_key)
                if required_review_claim is not None:
                    required_review_claims.append(required_review_claim)
            review_marker = max(required_marker, latest_edit or 0)
            review_claims = {
                row["Claim"]
                for row in visible_rows
                if row["Owner"] == review_owner
                and row["State"] == "current"
                and isinstance(row["Freshness"], int)
                and not isinstance(row["Freshness"], bool)
                and row["Freshness"] >= review_marker
            }
            for required_review_claim in required_review_claims:
                if required_review_claim not in review_claims:
                    errors.append(
                        "completed missing current independent review evidence for "
                        f"claim {required_review_claim!r}"
                    )
    return errors


def combined_review_artifact_sha256(artifact: object) -> str:
    """Hash the fixture-only combined artifact without its digest field."""

    if not isinstance(artifact, dict):
        raise FixtureCapsuleError("combined review artifact must be a mapping")
    material = {
        field: artifact.get(field)
        for field in COMBINED_REVIEW_BOUNDARY_MODEL["artifact_fields"]
        if field != "artifact_digest"
    }
    canonical = json.dumps(
        material,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def combined_review_completion_errors(case: object) -> list[str]:
    """Validate assignment-aware combined review fixture completion semantics."""

    if not isinstance(case, dict):
        return ["combined review case must be a mapping"]
    tasks = case.get("tasks")
    boundary = case.get("review_boundary")
    events = case.get("events")
    if not isinstance(tasks, list) or not tasks or not isinstance(boundary, dict):
        return ["combined review case requires tasks and a Review Boundary"]
    if not isinstance(events, list) or not events:
        return ["combined review case requires ordered events"]

    errors: list[str] = []

    def reject(code: str, message: str) -> None:
        errors.append(f"[{code}] {message}")

    task_ids: list[str] = []
    dependencies: dict[str, set[str]] = {}
    implementation_layer3: set[str] = set()
    required_skills: set[str] = set()
    required_specialists: set[str] = set()
    required_risks: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            reject("combined-task-shape", "each covered Task must be a mapping")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id or task_id in task_ids:
            reject("combined-task-shape", "covered Task IDs must be unique text")
            continue
        task_ids.append(task_id)
        raw_dependencies = task.get("dependencies", [])
        if not isinstance(raw_dependencies, list) or any(
            not isinstance(item, str) or not item for item in raw_dependencies
        ):
            reject("combined-task-dependencies", "Task dependencies must be text")
            raw_dependencies = []
        dependencies[task_id] = set(raw_dependencies)
        raw_layer3 = task.get("implementation_layer3", [])
        if (
            not isinstance(raw_layer3, list)
            or len(raw_layer3) > 3
            or len(raw_layer3) != len(set(raw_layer3))
            or any(not isinstance(item, str) or not item for item in raw_layer3)
        ):
            reject(
                "task-layer3-routing",
                "each Task must select zero to three unique implementation Layer 3 Skills",
            )
            raw_layer3 = []
        implementation_layer3.update(raw_layer3)
        requirements = task.get("review_requirements")
        requirement_fields = tuple(
            re.sub(r"[^a-z0-9]+", "_", field.casefold()).strip("_")
            for field in COMBINED_REVIEW_BOUNDARY_MODEL[
                "task_node_requirement_fields"
            ]
        )
        if not isinstance(requirements, dict) or tuple(requirements) != requirement_fields:
            reject(
                "task-review-requirements",
                "Task nodes may retain only the three ordered review requirement fields",
            )
            continue
        for field, target in (
            ("required_review_skills", required_skills),
            ("specialist_obligations", required_specialists),
            ("professional_risk_dimensions", required_risks),
        ):
            values = requirements[field]
            if not isinstance(values, list) or any(
                not isinstance(item, str) or not item for item in values
            ) or len(values) != len(set(values)):
                reject("task-review-requirements", f"{field} must be unique text")
            else:
                target.update(values)
        forbidden = COMBINED_REVIEW_BOUNDARY_MODEL[
            "task_node_forbidden_scheduling_fields"
        ]
        for field in forbidden:
            fixture_field = re.sub(
                r"[^a-z0-9]+", "_", field.casefold()
            ).strip("_")
            if fixture_field in task:
                reject(
                    "task-review-scheduling",
                    f"Task node must not carry global Review scheduling field {field!r}",
                )

    for task_id, task_dependencies in dependencies.items():
        if not task_dependencies <= set(task_ids) or task_id in task_dependencies:
            reject("combined-task-dependencies", "Task dependencies must name other covered Tasks")

    expected_boundary_fields = tuple(
        re.sub(r"[^a-z0-9]+", "_", field.casefold()).strip("_")
        for field in COMBINED_REVIEW_BOUNDARY_MODEL["boundary_fields"]
    )
    if tuple(boundary) != expected_boundary_fields:
        reject(
            "review-boundary-shape",
            "Review Boundary fields or order do not match the combined Core contract",
        )
        return list(dict.fromkeys(errors))
    boundary_id = boundary["review_boundary_id"]
    round_id = boundary["review_round_id"]
    if not _fixture_nonempty_text(boundary_id) or not _fixture_nonempty_text(round_id):
        reject("review-boundary-identity", "boundary and round IDs must be non-empty")
    strategy = boundary["review_strategy"]
    allowed_final = {"combined-final", "L5-preimplementation", "L5-final"}
    trigger_prefix = "risk-triggered-intermediate:"
    if strategy not in allowed_final and not (
        isinstance(strategy, str) and strategy.startswith(trigger_prefix)
    ):
        reject(
            "review-boundary-frequency",
            "Review strategy must be combined final, L5-required, or name a Core intermediate trigger",
        )
    if isinstance(strategy, str) and strategy.startswith(trigger_prefix):
        trigger = strategy.removeprefix(trigger_prefix)
        allowed = set(
            REVIEW_DISCIPLINE_MODEL["review_frequency_policy"][
                "intermediate_review_triggers"
            ]
        )
        if trigger not in allowed:
            reject(
                "review-boundary-frequency",
                "intermediate Review Boundary requires a declared Core trigger",
            )
    if boundary["covered_task_ids"] != task_ids:
        reject("review-boundary-coverage", "Review Boundary must cover every ordered Task")
    if set(boundary["required_review_skills"]) != required_skills:
        reject("review-skill-preservation", "boundary Review Skills must equal Task requirements")
    if set(boundary["specialist_obligations"]) != required_specialists:
        reject("review-obligation-coverage", "boundary Specialist obligations must equal Task requirements")
    if set(boundary["professional_risk_dimensions"]) != required_risks:
        reject("review-obligation-coverage", "boundary risk dimensions must equal Task requirements")
    required_scope = boundary["required_changed_scope"]
    evidence_binding = boundary["required_validation_evidence_binding"]
    if not isinstance(required_scope, list) or not required_scope or len(required_scope) != len(set(required_scope)):
        reject("review-boundary-scope", "required changed scope must be non-empty and unique")
    if evidence_binding != REVIEW_DISCIPLINE_MODEL["obligation_subsumption"][
        "required_validation_evidence_binding"
    ]:
        reject("review-boundary-validation-binding", "boundary requires current covered-Task validation")

    assignments = boundary["review_assignments"]
    assignment_fields = tuple(COMBINED_REVIEW_BOUNDARY_MODEL["assignment_fields"])
    if not isinstance(assignments, list) or not assignments:
        reject("review-assignment-shape", "Review Boundary requires assignments")
        assignments = []
    assignment_ids: list[str] = []
    assignment_by_id: dict[str, dict[str, Any]] = {}
    review_layer3: set[str] = set()
    for assignment in assignments:
        if not isinstance(assignment, dict) or tuple(assignment) != assignment_fields:
            reject("review-assignment-shape", "assignment fields or order are invalid")
            continue
        assignment_id = assignment["assignment_id"]
        if not _fixture_nonempty_text(assignment_id) or assignment_id in assignment_ids:
            reject("review-assignment-identity", "assignment IDs must be unique text")
            continue
        assignment_ids.append(assignment_id)
        assignment_by_id[assignment_id] = assignment
        if assignment["role"] not in COMBINED_REVIEW_BOUNDARY_MODEL["assignment_roles"]:
            reject("review-assignment-role", "assignment role is invalid")
        if assignment["profile"] != COMBINED_REVIEW_BOUNDARY_MODEL["assignment_profile"]:
            reject("review-assignment-profile", "every assignment must use review-agent")
        if not _fixture_nonempty_text(assignment["review_skill"]):
            reject("review-assignment-skill", "each assignment requires exactly one Review Skill")
        layer3 = assignment["layer3_skills"]
        if (
            not isinstance(layer3, list)
            or len(layer3) > COMBINED_REVIEW_BOUNDARY_MODEL[
                "maximum_layer3_skills_per_assignment"
            ]
            or len(layer3) != len(set(layer3))
            or any(not isinstance(item, str) or not item for item in layer3)
        ):
            reject("review-layer3-routing", "each assignment allows zero to three unique review Layer 3 Skills")
            layer3 = []
        review_layer3.update(layer3)
        if assignment["layer3_selection_basis"] != COMBINED_REVIEW_BOUNDARY_MODEL[
            "layer3_selection_basis"
        ]:
            reject("review-layer3-selection", "review Layer 3 must be selected from review risk")
        scope = assignment["scope"]
        if not isinstance(scope, list) or not scope or not set(scope) <= set(required_scope):
            reject("review-assignment-scope", "assignment scope must be a bounded subset of required changed scope")
    primary_ids = [
        assignment["assignment_id"]
        for assignment in assignments
        if isinstance(assignment, dict) and assignment.get("role") == "primary"
    ]
    specialist_ids = [
        assignment["assignment_id"]
        for assignment in assignments
        if isinstance(assignment, dict) and assignment.get("role") == "specialist"
    ]
    if len(primary_ids) != 1:
        reject("review-assignment-primary", "Review Boundary requires exactly one primary assignment")
    realized_review_skills = {
        skill
        for assignment in assignments
        if isinstance(assignment, dict)
        and isinstance((skill := assignment.get("review_skill")), str)
    }
    if realized_review_skills != required_skills:
        reject("review-skill-preservation", "assignments must realize every and only required Review Skill")
    if implementation_layer3 and review_layer3 == implementation_layer3:
        reject("review-layer3-task-union", "review Layer 3 must not equal the covered Tasks' implementation Layer 3 union")
    expected_close_order = {
        "required_specialist_assignment_ids": specialist_ids,
        "primary_assignment_id": primary_ids[0] if len(primary_ids) == 1 else None,
        "specialists_before_primary": True,
        "primary_close_count": 1,
    }
    if boundary["primary_close_ordering"] != expected_close_order:
        reject("review-primary-ordering", "primary close ordering must name every specialist before the sole primary close")

    latest_generation: dict[str, int] = {}
    current_validation: set[str] = set()
    result_by_assignment: dict[str, dict[str, Any]] = {}
    result_order: dict[str, int] = {}
    artifact: dict[str, Any] | None = None
    projections: list[dict[str, Any]] = []
    completed = False
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            reject("combined-review-event", "events must be mappings")
            continue
        action = event.get("action")
        if action == "edit":
            task_id = event.get("task_id")
            generation = event.get("generation")
            if task_id not in task_ids or not isinstance(generation, int) or generation <= latest_generation.get(str(task_id), 0):
                reject("material-edit-invalidation", "edit requires an increasing covered-Task generation")
                continue
            latest_generation[str(task_id)] = generation
            dependents = {str(task_id)}
            changed = True
            while changed:
                before = set(dependents)
                dependents.update(
                    candidate
                    for candidate, candidate_dependencies in dependencies.items()
                    if candidate_dependencies & dependents
                )
                changed = dependents != before
            invalidated = event.get("invalidated_evidence_task_ids")
            retained = event.get("retained_evidence_task_ids")
            if set(invalidated or []) != dependents or set(retained or []) != set(task_ids) - dependents:
                reject("material-edit-invalidation", "edit must invalidate exactly intersecting and transitive dependent evidence and retain unaffected evidence")
            current_validation.difference_update(dependents)
            result_by_assignment.clear()
            result_order.clear()
            artifact = None
            projections.clear()
        elif action == "validate":
            task_id = event.get("task_id")
            if task_id not in task_ids or event.get("generation") != latest_generation.get(str(task_id)):
                reject("combined-review-validation", "validation must bind the Task's current generation")
            else:
                current_validation.add(str(task_id))
        elif action == "assignment-result":
            assignment_id = event.get("assignment_id")
            if assignment_id not in assignment_by_id or assignment_id in result_by_assignment:
                reject("review-assignment-result", "assignment result must name one unresolved assignment")
                continue
            if event.get("review_round_id") != round_id:
                reject("review-round-identity", "all assignment results must share the boundary Review Round ID")
            if event.get("task_generations") != latest_generation:
                reject("review-artifact-generation", "assignment result must bind every current Task generation")
            if not set(event.get("evidence_scope", [])) >= set(assignment_by_id[assignment_id]["scope"]):
                reject("review-artifact-scope", "assignment result evidence must cover its assignment scope")
            result_by_assignment[assignment_id] = event
            result_order[assignment_id] = index
        elif action == "combined-artifact":
            candidate = event.get("artifact")
            artifact_fields = tuple(COMBINED_REVIEW_BOUNDARY_MODEL["artifact_fields"])
            if not isinstance(candidate, dict) or tuple(candidate) != artifact_fields:
                reject("review-artifact-shape", "combined artifact fields or order are invalid")
                continue
            artifact = candidate
            if set(result_by_assignment) != set(assignment_ids):
                reject("review-specialist-result", "combined artifact requires every assignment result")
            if primary_ids and any(
                result_order.get(specialist, index + 1) > result_order.get(primary_ids[0], -1)
                for specialist in specialist_ids
            ):
                reject("review-primary-ordering", "primary assignment cannot close before specialist results")
            expected_artifact = {
                "review_boundary_id": boundary_id,
                "review_round_id": round_id,
                "covered_task_ids": task_ids,
                "required_changed_scope": required_scope,
                "task_generations": latest_generation,
                "assignment_result_ids": [
                    result_by_assignment.get(assignment_id, {}).get("result_id")
                    for assignment_id in assignment_ids
                ],
                "primary_assignment_id": primary_ids[0] if primary_ids else None,
            }
            for field, expected in expected_artifact.items():
                if candidate.get(field) != expected:
                    reject("review-artifact-binding", f"combined artifact {field} does not match its boundary")
            if not set(candidate.get("evidence_scope", [])) >= set(required_scope):
                reject("review-artifact-scope", "combined artifact evidence scope is incomplete")
            try:
                expected_digest = combined_review_artifact_sha256(candidate)
            except FixtureCapsuleError as exc:
                reject("review-artifact-digest", str(exc))
            else:
                if candidate.get("artifact_digest") != expected_digest:
                    reject("review-artifact-digest", "combined artifact digest is not canonical")
        elif action == "task-projection":
            projection = event.get("projection")
            projection_fields = tuple(
                COMBINED_REVIEW_BOUNDARY_MODEL["task_completion_projection_fields"]
            )
            if not isinstance(projection, dict) or tuple(projection) != projection_fields:
                reject("task-review-projection", "Task completion projection fields or order are invalid")
            else:
                projections.append(projection)
        elif action == "complete":
            completed = True
            if artifact is None:
                reject("review-artifact-missing", "completion requires the combined artifact")
                continue
            if current_validation != set(task_ids):
                reject("completion-current-evidence", "completion requires current validation for every covered Task")
            if event.get("review_round_count") != 1 or event.get("primary_close_count") != 1:
                reject("review-round-count", "specialists share one round and only the primary closes")
            if len(projections) != len(task_ids) or {row.get("task_id") for row in projections} != set(task_ids):
                reject("task-review-projection", "completion requires exactly one projection for every covered Task")
            for projection in projections:
                task_id = projection.get("task_id")
                expected_projection = {
                    "task_id": task_id,
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_digest": artifact.get("artifact_digest"),
                    "review_boundary_id": boundary_id,
                    "review_round_id": round_id,
                    "generation": latest_generation.get(str(task_id)),
                }
                if projection != expected_projection:
                    reject("task-review-projection", "Task projection must reference the exact current combined artifact")
        else:
            reject("combined-review-event", f"unsupported combined review action {action!r}")
    if not completed:
        reject("combined-review-terminal", "combined review trajectory must complete")
    return list(dict.fromkeys(errors))


def _lexical_tokens(value: str) -> list[str]:
    return [item.casefold() for item in _LEXICAL_RE.findall(value)]


def _is_placeholder_token(value: str) -> bool:
    return value in {"x", "xx", "na", *PLACEHOLDER_ROOTS}


def _normalize_text(value: object, label: str, *, minimum: int = 1) -> str:
    if not isinstance(value, str):
        raise FixtureCapsuleError(f"{label} must be text")
    canonical = unicodedata.normalize("NFKC", value)
    if any(
        unicodedata.category(char) in {"Cc", "Cf"} and not char.isspace()
        for char in canonical
    ):
        raise FixtureCapsuleError(f"{label} must not contain control characters")
    normalized = " ".join(canonical.split())
    if len(normalized) < minimum:
        raise FixtureCapsuleError(f"{label} must be meaningful fixture evidence")
    return normalized


def _reject_placeholder_value(value: str, label: str) -> None:
    if (
        _PLACEHOLDER_VALUE_RE.fullmatch(value)
        or _STRICT_PLACEHOLDER_AFFIX_RE.fullmatch(value)
        or _REPEATED_PLACEHOLDER_RE.fullmatch(value)
    ):
        raise FixtureCapsuleError(f"{label} must not be placeholder content")


def _prose(value: object, label: str, *, minimum: int = 3) -> str:
    normalized = _normalize_text(value, label, minimum=minimum)
    _reject_placeholder_value(normalized, label)
    tokens = [
        item
        for item in _lexical_tokens(normalized)
        if (
            (len(item) >= 2 or any("\u3400" <= char <= "\u9fff" for char in item))
            and not item.isdigit()
            and not _is_placeholder_token(item)
        )
    ]
    counts = Counter(tokens)
    if len(counts) < MIN_PROSE_UNIQUE_TOKENS:
        raise FixtureCapsuleError(
            f"{label} must contain at least two distinct meaningful lexical tokens"
        )
    if len(tokens) >= 6:
        diversity = len(counts) / len(tokens)
        dominant_share = max(counts.values()) / len(tokens)
        if (
            diversity < MIN_LONG_PROSE_DIVERSITY
            or dominant_share > MAX_LONG_PROSE_TOKEN_SHARE
        ):
            raise FixtureCapsuleError(f"{label} has insufficient lexical diversity")
    return normalized


def _is_repo_path_or_glob(value: str) -> bool:
    if value == ".":
        return True
    if any(char.isspace() for char in value):
        return False
    if (
        value.startswith(("/", "~", "-"))
        or "://" in value
        or "\\" in value
        or _SHELL_METACHAR_RE.search(value)
    ):
        return False
    candidate = value[2:] if value.startswith("./") else value
    parts = candidate.split("/")
    if any(not item or item in {".", ".."} for item in parts):
        return False
    if any(_PATH_PART_RE.fullmatch(item) is None for item in parts):
        return False
    return any(char.isalnum() for char in candidate)


def _is_technical_identifier(value: str) -> bool:
    if any(char.isspace() for char in value):
        return False
    return _TECHNICAL_IDENTIFIER_RE.fullmatch(value) is not None


def _is_command(value: str) -> bool:
    if _SHELL_METACHAR_RE.search(value):
        return False
    try:
        parts = shlex.split(value, posix=True)
    except ValueError:
        return False
    if not parts:
        return False
    executable = parts[0]
    name = executable.rsplit("/", 1)[-1]
    if name in {"bash", "sh", "zsh"} and "-c" in parts[1:]:
        return False
    if name in KNOWN_COMMANDS:
        return True
    return executable.startswith("./") or executable.endswith(".sh")


def _path_or_prose(value: object, label: str) -> str:
    normalized = _normalize_text(value, label)
    _reject_placeholder_value(normalized, label)
    if _is_repo_path_or_glob(normalized):
        return normalized
    return _prose(normalized, label)


def _repo_path(value: object, label: str) -> str:
    normalized = _normalize_text(value, label)
    _reject_placeholder_value(normalized, label)
    if not _is_repo_path_or_glob(normalized):
        raise FixtureCapsuleError(f"{label} must be a relative repository path or glob")
    return normalized


def _command(value: object, label: str) -> str:
    if isinstance(value, str) and any(char in value for char in "\r\n"):
        raise FixtureCapsuleError(f"{label} must not contain command line breaks")
    normalized = _normalize_text(value, label)
    _reject_placeholder_value(normalized, label)
    tokens = _lexical_tokens(normalized)
    if len(tokens) > 1 and len(set(tokens)) == 1:
        raise FixtureCapsuleError(f"{label} must not repeat one command token")
    if normalized in UTILITY_CAPABILITY_OPERATIONS:
        return normalized
    if not _is_command(normalized):
        raise FixtureCapsuleError(f"{label} must be a recognizable non-empty command")
    return normalized


def _technical_or_prose(value: object, label: str) -> str:
    normalized = _normalize_text(value, label)
    _reject_placeholder_value(normalized, label)
    if (
        _is_repo_path_or_glob(normalized)
        or _is_technical_identifier(normalized)
        or _is_command(normalized)
    ):
        return normalized
    return _prose(normalized, label)


def _technical_target(value: object, label: str) -> str:
    normalized = _normalize_text(value, label)
    _reject_placeholder_value(normalized, label)
    if (
        _is_repo_path_or_glob(normalized)
        or _is_technical_identifier(normalized)
        or _is_command(normalized)
    ):
        return normalized
    raise FixtureCapsuleError(
        f"{label} must be a repository path, command, or technical identifier"
    )


def _metadata_identifier(value: object, label: str) -> str:
    normalized = _normalize_text(value, label)
    _reject_placeholder_value(normalized, label)
    if (
        _is_repo_path_or_glob(normalized)
        or _is_technical_identifier(normalized)
    ):
        return normalized
    raise FixtureCapsuleError(f"{label} must be a technical metadata identifier")


def _output_prose(value: object, label: str) -> str:
    return _prose(value, label, minimum=10)


def _change_set_atom(value: object, label: str) -> str:
    normalized = _normalize_text(value, label)
    if CHANGE_SET_RE.fullmatch(normalized) is None:
        raise FixtureCapsuleError(
            f"{label} must be tracked, staged, or untracked state evidence"
        )
    return normalized


def _validated_list(
    value: object,
    label: str,
    validator: Any,
) -> list[str]:
    if not isinstance(value, list) or not value:
        raise FixtureCapsuleError(f"{label} must be a non-empty string list")
    result = [
        validator(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(result) != len(set(result)):
        raise FixtureCapsuleError(f"{label} must not contain duplicates")
    return result


def _prose_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _prose)


def _output_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _output_prose)


def _path_or_prose_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _path_or_prose)


def _command_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _command)


def _technical_or_prose_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _technical_or_prose)


def _technical_target_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _technical_target)


def _change_set_list(value: object, label: str) -> list[str]:
    return _validated_list(value, label, _change_set_atom)


def _optional_metadata_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise FixtureCapsuleError(f"{label} must be a string list")
    result = [
        _metadata_identifier(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(result) != len(set(result)):
        raise FixtureCapsuleError(f"{label} must not contain duplicates")
    return result


def parse_layer3_reference_id(
    value: object,
    label: str = "layer3_reference",
) -> tuple[str, str]:
    """Parse one safe ``owner/references/file.md`` fixture logical ID."""

    normalized = _normalize_text(value, label)
    if (
        any(char.isspace() for char in normalized)
        or "\\" in normalized
        or any(char in normalized for char in _LAYER3_REFERENCE_FORBIDDEN_CHARS)
    ):
        raise FixtureCapsuleError(
            f"{label} must be a normalized POSIX Layer 3 Reference logical ID"
        )
    parsed = PurePosixPath(normalized)
    if (
        parsed.is_absolute()
        or len(parsed.parts) != 3
        or any(part in {"", ".", ".."} for part in parsed.parts)
        or parsed.parts[1] != "references"
        or _LAYER3_OWNER_RE.fullmatch(parsed.parts[0]) is None
        or _LAYER3_REFERENCE_NAME_RE.fullmatch(parsed.parts[2]) is None
        or parsed.parts[2].casefold() in _LAYER3_REFERENCE_FORBIDDEN_NAMES
    ):
        raise FixtureCapsuleError(
            f"{label} must match owner/references/file.md without index or catalog files"
        )
    return parsed.parts[0], "/".join(parsed.parts[1:])


def _optional_layer3_reference_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise FixtureCapsuleError(f"{label} must be a string list")
    result: list[str] = []
    for index, item in enumerate(value):
        owner, relative = parse_layer3_reference_id(item, f"{label}[{index}]")
        result.append(f"{owner}/{relative}")
    if len(result) != len(set(result)):
        raise FixtureCapsuleError(f"{label} must not contain duplicates")
    return result


def _render_list(heading: str, values: list[str]) -> list[str]:
    return [f"## {heading}", "", *[f"- {item}" for item in values], ""]


def _optional_prose_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise FixtureCapsuleError(f"{label} must be a string list")
    if not value:
        return []
    return _prose_list(value, label)


def _render_scalar(heading: str, value: str) -> list[str]:
    return [f"## {heading}", "", value, ""]


def _public_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _public_integrity_fallback(
    value: object = None,
    *,
    execution_contract: dict[str, Any] | None = None,
) -> dict[str, object]:
    execution_contract = (
        EXECUTION_LEVEL_MODEL if execution_contract is None else execution_contract
    )
    requested = "unspecified"
    prior_floor: str | None = None
    prior_effective: str | None = None
    if isinstance(value, dict):
        candidate = value.get("requested_level")
        if candidate in execution_contract["requested_values"]:
            requested = candidate
        candidate = value.get("prior_historical_max_floor")
        if candidate in {row["id"] for row in execution_contract["levels"]}:
            prior_floor = candidate
        candidate = value.get("prior_historical_max_effective")
        if candidate in {row["id"] for row in execution_contract["levels"]}:
            prior_effective = candidate
        # A syntactically validated public Level line is trusted only for its
        # conservative L5 signal. Lower visible levels never relax the fixed
        # L4 integrity floor.
        if value.get("effective_level") == "L5":
            prior_effective = "L5"
    try:
        return execution_level_integrity_fallback(
            requested=requested,
            prior_historical_max_floor=prior_floor,
            prior_historical_max_effective=prior_effective,
            contract=execution_contract,
        )
    except (ExecutionLevelError, KeyError, TypeError):
        return execution_level_integrity_fallback(
            requested="unspecified",
            contract=EXECUTION_LEVEL_MODEL,
        )


def _active_public_schema(execution_contract: dict[str, Any]) -> dict[str, Any]:
    try:
        public = execution_contract["projection"]["public_task_extension"]
    except (KeyError, TypeError) as exc:
        raise FixtureCapsuleError("public task extension schema is missing") from exc
    expected = {
        "version": "execution-level/v2",
        "ordered_labels": ["Level", "Basis", "L5 Evidence"],
        "line_fields": {
            "Level": [
                "requested",
                "automatic",
                "minimum",
                "default",
                "effective",
                "edit",
            ],
            "Basis": [
                "source",
                "triggers",
                "l1",
                "l2",
                "l5",
                "confirmation",
                "unresolved",
            ],
            "L5 Evidence": ["when", "requires"],
        },
    }
    if public != expected:
        raise FixtureCapsuleError("public task extension decision schema is invalid")
    return public


def _closed_execution_level_ranks(
    execution_contract: dict[str, Any],
) -> dict[str, int]:
    expected = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
    try:
        ranks = {
            row["id"]: row["rank"] for row in execution_contract["levels"]
        }
    except (KeyError, TypeError) as exc:
        raise FixtureCapsuleError("execution level ranks are invalid") from exc
    if ranks != expected:
        raise FixtureCapsuleError("execution level ranks must be the closed L1-L5 order")
    return expected


def _active_execution_decision(
    value: object,
    execution_contract: dict[str, Any],
    *,
    allow_legacy_read: bool = False,
) -> dict[str, Any]:
    """Validate v2 for active work, with an explicit completed/read v1 exception."""

    if not isinstance(value, dict):
        raise FixtureCapsuleError("execution_level_extension must be a mapping")
    required = {"requested_level", "automatic_level", "effective_level", "level_basis"}
    if not required <= set(value):
        raise FixtureCapsuleError(
            "execution_level_extension is missing active decision fields"
        )
    basis = value["level_basis"]
    basis_required = {
        "trigger_evaluations",
        "l2_eligibility",
        "unresolved",
        "edit_status",
    }
    if not isinstance(basis, dict) or not basis_required <= set(basis):
        raise FixtureCapsuleError("execution Level Basis is missing decision fields")

    trigger_base_fields = (
        "id",
        "status",
        "evidence_kind",
        "source_anchor",
        "plausible_critical",
    )
    trigger_ids = [row["id"] for row in execution_contract["trigger_registry"]]
    trigger_rows = basis["trigger_evaluations"]
    if not isinstance(trigger_rows, list) or len(trigger_rows) != len(trigger_ids):
        raise FixtureCapsuleError("execution Level Basis must cover the trigger registry")
    trigger_evaluations: dict[str, dict[str, object]] = {}
    for index, row in enumerate(trigger_rows):
        if not isinstance(row, dict) or tuple(row)[: len(trigger_base_fields)] != trigger_base_fields:
            raise FixtureCapsuleError(
                f"execution trigger row {index} fields are invalid"
            )
        if set(row) - {*trigger_base_fields, "material_assessment", "critical_unknown"}:
            raise FixtureCapsuleError(
                f"execution trigger row {index} conditional fields are invalid"
            )
        if row["id"] != trigger_ids[index]:
            raise FixtureCapsuleError("execution trigger rows are out of order")
        trigger_evaluations[row["id"]] = {
            field: row[field] for field in row if field != "id"
        }

    l2_fields = ("id", "status", "evidence_kind", "source_anchor")
    l2_ids = [row["id"] for row in execution_contract["l2_eligibility"]]
    l2_rows = basis["l2_eligibility"]
    if not isinstance(l2_rows, list) or len(l2_rows) != len(l2_ids):
        raise FixtureCapsuleError("execution Level Basis must cover L2 eligibility")
    l2_evaluations: dict[str, dict[str, object]] = {}
    for index, row in enumerate(l2_rows):
        if not isinstance(row, dict) or tuple(row) != l2_fields:
            raise FixtureCapsuleError(f"execution L2 row {index} fields are invalid")
        if row["id"] != l2_ids[index]:
            raise FixtureCapsuleError("execution L2 rows are out of order")
        l2_evaluations[row["id"]] = {
            field: row[field] for field in l2_fields if field != "id"
        }

    def eligibility_rows(
        basis_field: str, contract_field: str
    ) -> dict[str, dict[str, object]] | None:
        if basis_field not in basis:
            return None
        registry_ids = [row["id"] for row in execution_contract[contract_field]]
        rows = basis[basis_field]
        if not isinstance(rows, list) or len(rows) != len(registry_ids):
            raise FixtureCapsuleError(
                f"execution Level Basis must cover {basis_field}"
            )
        evaluations: dict[str, dict[str, object]] = {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or tuple(row) != l2_fields:
                raise FixtureCapsuleError(
                    f"execution {basis_field} row {index} fields are invalid"
                )
            if row["id"] != registry_ids[index]:
                raise FixtureCapsuleError(
                    f"execution {basis_field} rows are out of order"
                )
            evaluations[row["id"]] = {
                field: row[field] for field in l2_fields if field != "id"
            }
        return evaluations

    l1_evaluations = eligibility_rows("l1_eligibility", "l1_eligibility")
    l5_evaluations = eligibility_rows(
        "l5_assurance_eligibility", "l5_assurance_eligibility"
    )
    v2_markers = (
        l1_evaluations is not None,
        l5_evaluations is not None,
        "minimum_eligible_level" in value,
        "l5_confirmation" in value,
        "l5_confirmation" in basis,
    )
    if any(v2_markers) and not all(v2_markers):
        raise FixtureCapsuleError(
            "execution-level/v2 evidence is incomplete; reissue without fabricating fields"
        )
    legacy_v1 = not any(v2_markers)
    if legacy_v1 and not allow_legacy_read:
        raise FixtureCapsuleError(
            "execution-level/v1 requires v2 reissue before active or resumed edit, validation, review, or routing"
        )
    confirmation = value.get(
        "l5_confirmation", basis.get("l5_confirmation", "not-required")
    )

    try:
        result = compute_execution_level(
            requested=value["requested_level"],
            trigger_evaluations=trigger_evaluations,
            l1_evaluations=l1_evaluations,
            l2_evaluations=l2_evaluations,
            l5_assurance_evaluations=l5_evaluations,
            l5_confirmation=confirmation,
            prior_historical_max_floor=value.get("prior_historical_max_floor"),
            prior_historical_max_effective=value.get("prior_historical_max_effective"),
            contract=execution_contract,
        )
    except ExecutionLevelError as exc:
        raise FixtureCapsuleError(f"execution Level Basis is invalid: {exc}") from exc
    if value["automatic_level"] != result["automatic_level"]:
        raise FixtureCapsuleError("execution automatic_level is not canonical")
    if (
        "minimum_eligible_level" in value
        and value["minimum_eligible_level"] != result["minimum_eligible_level"]
    ):
        raise FixtureCapsuleError("execution minimum_eligible_level is not canonical")
    if basis["unresolved"] != result["level_basis"]["unresolved"]:
        raise FixtureCapsuleError("execution unresolved Basis is not canonical")
    if basis["edit_status"] != result["level_basis"]["edit_status"]:
        raise FixtureCapsuleError("execution edit status is not canonical")
    ranks = _closed_execution_level_ranks(execution_contract)
    effective = value["effective_level"]
    if effective not in ranks:
        raise FixtureCapsuleError("execution effective_level is invalid")
    floor_candidates = [value["automatic_level"], result["mandatory_floor"]]
    if not legacy_v1:
        floor_candidates.append(result["minimum_eligible_level"])
    if value["requested_level"] != "unspecified":
        floor_candidates.append(value["requested_level"])
    for field in (
        "mandatory_floor",
        "prior_historical_max_floor",
        "prior_historical_max_effective",
    ):
        if field not in value:
            continue
        candidate = value[field]
        if candidate not in ranks:
            raise FixtureCapsuleError(f"execution {field} is invalid")
        floor_candidates.append(candidate)
    decision_floor = max(floor_candidates, key=ranks.__getitem__)
    if ranks[effective] < ranks[decision_floor]:
        raise FixtureCapsuleError("execution effective_level is below its decision floor")
    if not legacy_v1 and effective != result["effective_level"]:
        raise FixtureCapsuleError("execution effective_level is not canonical")
    if legacy_v1:
        return value
    normalized = dict(value)
    normalized["minimum_eligible_level"] = result["minimum_eligible_level"]
    normalized["l5_confirmation"] = result["l5_confirmation"]
    normalized["level_basis"] = result["level_basis"]
    return normalized


def _active_public_fields(payload: str, fields: tuple[str, ...]) -> dict[str, str]:
    parts = payload.split("; ")
    if len(parts) != len(fields):
        raise FixtureCapsuleError("public execution subfield count is invalid")
    values: dict[str, str] = {}
    for field, part in zip(fields, parts):
        prefix = field + "="
        if not part.startswith(prefix):
            raise FixtureCapsuleError(
                "public execution subfields/order are invalid"
            )
        values[field] = part[len(prefix) :]
    return values


def _trusted_active_public_level(
    text: object,
    execution_contract: dict[str, Any],
) -> dict[str, str] | None:
    """Parse only a complete, closed Level line for fail-closed L5 retention."""

    if not isinstance(text, str) or "\r" in text:
        return None
    lines = text.splitlines()
    if not lines or not lines[0].startswith("Level: "):
        return None
    payload = lines[0][len("Level: ") :]
    has_requested = payload.startswith("requested=")
    has_minimum = "; minimum=" in payload
    fields = (
        (("requested",) if has_requested else ())
        + ("automatic",)
        + (("minimum",) if has_minimum else ())
        + ("effective", "edit")
    )
    try:
        level = _active_public_fields(payload, fields)
    except FixtureCapsuleError:
        return None
    requested = level.get("requested", "unspecified")
    levels = {row["id"] for row in execution_contract["levels"]}
    if (
        requested not in execution_contract["requested_values"]
        or level["automatic"] not in execution_contract["dynamic_levels"]
        or level["effective"] not in levels
        or level["edit"] not in {"allowed", "blocked"}
    ):
        return None
    return {
        "requested_level": requested,
        "effective_level": level["effective"],
    }


def _active_public_bound_id(row: dict[str, Any]) -> str:
    evidence_aliases = {"user_fact": "u", "analysis_handoff": "a"}
    return (
        f"{row['id']}@{evidence_aliases[row['evidence_kind']]}:"
        f"{row['source_anchor']}"
    )


def _parse_active_public_bound_ids(
    value: str,
    *,
    label: str,
    registry_ids: list[str],
    execution_contract: dict[str, Any],
) -> tuple[list[str], list[str]]:
    items = json.loads(value)
    if (
        not isinstance(items, list)
        or any(not _fixture_nonempty_text(item) for item in items)
        or len(items) != len(set(items))
    ):
        raise FixtureCapsuleError(f"public {label} must be unique source-bound IDs")
    identifiers: list[str] = []
    sources: list[str] = []
    evidence_aliases = {"u": "user_fact", "a": "analysis_handoff"}
    if set(evidence_aliases.values()) != set(
        execution_contract["main_evidence_kinds"]
    ):
        raise FixtureCapsuleError("public evidence-kind aliases are invalid")
    for item in items:
        identifier, separator, source = item.partition("@")
        alias, source_separator, anchor = source.partition(":")
        if (
            not separator
            or not source_separator
            or alias not in evidence_aliases
            or not anchor.strip()
        ):
            raise FixtureCapsuleError(
                f"public {label} item is not source-bound"
            )
        identifiers.append(identifier)
        sources.append(f"{evidence_aliases[alias]}:{anchor}")
    if identifiers != [item for item in registry_ids if item in identifiers]:
        raise FixtureCapsuleError(f"public {label} IDs are unknown or out of order")
    return identifiers, sources


def _active_l5_requirements(execution_contract: dict[str, Any]) -> list[str]:
    required = {
        "independent pre-implementation review",
        "strong safety and applicability proof",
        "declared-scope comprehensive negative and failure proof",
        "exhaustive final review",
    }
    l5 = next(
        level for level in execution_contract["levels"] if level["id"] == "L5"
    )
    return [item for item in l5["obligations"] if item in required]


def encode_public_task_extension(
    value: object,
    *,
    execution_contract: dict[str, Any] | None = None,
) -> str:
    """Encode the active lightweight public execution decision projection."""

    execution_contract = (
        EXECUTION_LEVEL_MODEL if execution_contract is None else execution_contract
    )
    _active_public_schema(execution_contract)
    extension = _active_execution_decision(value, execution_contract)
    basis = extension["level_basis"]
    trigger_rows = basis["trigger_evaluations"]
    if "l1_eligibility" not in basis:
        l2_rows = basis["l2_eligibility"]
        decision_trigger_rows = [
            row for row in trigger_rows if row["status"] in {"matched", "unknown"}
        ]
        decision_l2_rows = [
            row for row in l2_rows if row["status"] in {"false", "unknown"}
        ]
        effective = extension["effective_level"]
        level_fields: list[str] = []
        if extension["requested_level"] != "unspecified":
            level_fields.append(f"requested={extension['requested_level']}")
        level_fields.extend(
            (
                f"automatic={extension['automatic_level']}",
                f"effective={effective}",
                f"edit={basis['edit_status']}",
            )
        )
        lines = [
            "Level: " + "; ".join(level_fields),
            "Basis: "
            + "; ".join(
                (
                    "t="
                    + _public_json(
                        [
                            _active_public_bound_id(row)
                            for row in decision_trigger_rows
                        ]
                    ),
                    "l="
                    + _public_json(
                        [_active_public_bound_id(row) for row in decision_l2_rows]
                    ),
                    "u=" + _public_json(basis["unresolved"]),
                )
            ),
        ]
        if effective == "L5" or extension["requested_level"] == "L5":
            lines.append(
                "L5 Evidence: requires="
                + _public_json(_active_l5_requirements(execution_contract))
            )
        return "\n".join(lines)
    l1_rows = basis["l1_eligibility"]
    l2_rows = basis["l2_eligibility"]
    l5_rows = basis["l5_assurance_eligibility"]
    decision_trigger_rows = [
        row
        for row in trigger_rows
        if row["status"] in {"matched", "unknown"}
    ]
    decision_l2_rows = [
        row for row in l2_rows if row["status"] in {"false", "unknown"}
    ]
    decision_l1_rows = [
        row for row in l1_rows if row["status"] in {"false", "unknown"}
    ]
    decision_l5_rows = [
        row for row in l5_rows if row["status"] in {"false", "unknown"}
    ]
    effective = extension["effective_level"]
    level_fields: list[str] = []
    if extension["requested_level"] != "unspecified":
        level_fields.append(f"requested={extension['requested_level']}")
    level_fields.extend(
        (
            f"automatic={extension['automatic_level']}",
            f"minimum={extension['minimum_eligible_level']}",
            f"effective={effective}",
            f"edit={basis['edit_status']}",
        )
    )
    lines = [
        "Level: " + "; ".join(level_fields),
        "Basis: "
        + "; ".join(
            (
                "t="
                + _public_json(
                    [_active_public_bound_id(row) for row in decision_trigger_rows]
                ),
                "i="
                + _public_json(
                    [_active_public_bound_id(row) for row in decision_l1_rows]
                ),
                "l="
                + _public_json(
                    [_active_public_bound_id(row) for row in decision_l2_rows]
                ),
                "a="
                + _public_json(
                    [_active_public_bound_id(row) for row in decision_l5_rows]
                ),
                "c=" + str(extension["l5_confirmation"]),
                "u=" + _public_json(basis["unresolved"]),
            )
        ),
    ]
    if effective == "L5" or extension["requested_level"] == "L5":
        lines.append(
            "L5 Evidence: requires="
            + _public_json(_active_l5_requirements(execution_contract))
        )
    return "\n".join(lines)


def decode_public_task_extension(
    text: object,
    *,
    execution_contract: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Decode the active decision projection or return the fail-closed fallback."""

    execution_contract = (
        EXECUTION_LEVEL_MODEL if execution_contract is None else execution_contract
    )
    fallback_value: dict[str, object] | None = None
    try:
        public = _active_public_schema(execution_contract)
        fallback_value = _trusted_active_public_level(text, execution_contract)
        if not isinstance(text, str) or "\r" in text:
            raise FixtureCapsuleError("public task extension text is malformed")
        lines = text.splitlines()
        if len(lines) not in {2, 3}:
            raise FixtureCapsuleError("public task extension line count is invalid")
        labels = public["ordered_labels"][: len(lines)]
        payloads: dict[str, str] = {}
        for label, line in zip(labels, lines):
            prefix = label + ": "
            if not line.startswith(prefix):
                raise FixtureCapsuleError("public task extension labels/order are invalid")
            payloads[label] = line[len(prefix) :]

        level_payload = payloads["Level"]
        has_requested = level_payload.startswith("requested=")
        is_v2 = "; minimum=" in level_payload
        level_fields = (
            (("requested",) if has_requested else ())
            + ("automatic",)
            + (("minimum",) if is_v2 else ())
            + ("effective", "edit")
        )
        level = _active_public_fields(level_payload, level_fields)
        requested = level.get("requested", "unspecified")
        fallback_value = {
            "requested_level": requested,
            "effective_level": level["effective"],
        }
        basis = _active_public_fields(
            payloads["Basis"],
            ("t", "i", "l", "a", "c", "u") if is_v2 else ("t", "l", "u"),
        )
        trigger_ids = [row["id"] for row in execution_contract["trigger_registry"]]
        l1_ids = [row["id"] for row in execution_contract["l1_eligibility"]]
        l2_ids = [row["id"] for row in execution_contract["l2_eligibility"]]
        l5_ids = [
            row["id"] for row in execution_contract["l5_assurance_eligibility"]
        ]
        triggers, trigger_sources = _parse_active_public_bound_ids(
            basis["t"],
            label="triggers",
            registry_ids=trigger_ids,
            execution_contract=execution_contract,
        )
        l2, l2_sources = _parse_active_public_bound_ids(
            basis["l"],
            label="L2 exceptions",
            registry_ids=l2_ids,
            execution_contract=execution_contract,
        )
        l1: list[str] = []
        l1_sources: list[str] = []
        l5: list[str] = []
        l5_sources: list[str] = []
        confirmation = "not-required"
        if is_v2:
            l1, l1_sources = _parse_active_public_bound_ids(
                basis["i"],
                label="L1 exceptions",
                registry_ids=l1_ids,
                execution_contract=execution_contract,
            )
            l5, l5_sources = _parse_active_public_bound_ids(
                basis["a"],
                label="L5 exceptions",
                registry_ids=l5_ids,
                execution_contract=execution_contract,
            )
            confirmation = basis["c"]
            if confirmation not in execution_contract["l5_confirmation"]["states"]:
                raise FixtureCapsuleError("public L5 confirmation is invalid")
        sources = list(
            dict.fromkeys(
                (*trigger_sources, *l1_sources, *l2_sources, *l5_sources)
            )
        )
        unresolved = json.loads(basis["u"])
        unresolved_ids = [*trigger_ids, *l1_ids, *l2_ids, *l5_ids]
        decision_ids = {*triggers, *l1, *l2, *l5}
        if (
            not isinstance(unresolved, list)
            or any(not _fixture_nonempty_text(item) for item in unresolved)
            or len(unresolved) != len(set(unresolved))
            or unresolved
            != [item for item in unresolved_ids if item in unresolved]
            or any(item not in decision_ids for item in unresolved)
        ):
            raise FixtureCapsuleError("public unresolved IDs are invalid")

        automatic = level["automatic"]
        minimum = level.get("minimum")
        effective = level["effective"]
        edit = level["edit"]
        levels = [row["id"] for row in execution_contract["levels"]]
        if requested not in execution_contract["requested_values"]:
            raise FixtureCapsuleError("public requested level is invalid")
        if automatic not in execution_contract["dynamic_levels"]:
            raise FixtureCapsuleError("public automatic level is invalid")
        if effective not in levels or edit not in {"allowed", "blocked"}:
            raise FixtureCapsuleError("public effective level or edit status is invalid")

        trigger_floors = {
            row["id"]: row["floor"] for row in execution_contract["trigger_registry"]
        }
        ranks = _closed_execution_level_ranks(execution_contract)
        matched_triggers = [item for item in triggers if item not in unresolved]
        critical_id = "unknown-critical-boundary"
        critical = critical_id in unresolved
        expected_minimum = "L2"
        if is_v2 and not l1 and not l2:
            expected_minimum = "L1"
        elif l2 or any(
            trigger_floors[item] == "L3" for item in matched_triggers
        ):
            expected_minimum = "L3"
        if critical or any(
            trigger_floors[item] == "L4" for item in matched_triggers
        ):
            expected_minimum = "L4"
        if is_v2 and minimum != expected_minimum:
            raise FixtureCapsuleError("public minimum level contradicts its Basis")
        expected_automatic = expected_minimum
        material_l4 = any(
            trigger_floors[item] == "L4"
            and item not in {"formal-release-declared", "unknown-critical-boundary"}
            for item in matched_triggers
        )
        l5_requirement = execution_contract["formula"]["l5_requirement"]
        l5_exceptions = set(l5)
        l5_eligible = (
            is_v2
            and material_l4
            and not (set(l5_requirement["required_all"]) & l5_exceptions)
            and bool(set(l5_requirement["required_any"]) - l5_exceptions)
        )
        if l5_eligible and confirmation == "confirmed":
            expected_automatic = "L5"
        elif l5_eligible:
            expected_automatic = "L4"
        if automatic != expected_automatic:
            raise FixtureCapsuleError("public automatic level contradicts its Basis")
        minimum_candidates = [automatic, expected_minimum]
        if requested != "unspecified":
            minimum_candidates.append(requested)
        minimum_effective = max(minimum_candidates, key=ranks.__getitem__)
        if ranks[effective] < ranks[minimum_effective]:
            raise FixtureCapsuleError("public effective level is below its decision floor")
        confirmation_pending = l5_eligible and confirmation == "pending"
        if critical and (ranks[effective] < ranks["L4"] or edit != "blocked"):
            raise FixtureCapsuleError("public critical unknown must fail closed")
        if confirmation_pending and edit != "blocked":
            raise FixtureCapsuleError("public pending L5 confirmation must block editing")
        if not critical and not confirmation_pending and edit != "allowed":
            raise FixtureCapsuleError("public edit status is unsupported")

        l5_required = effective == "L5" or requested == "L5"
        if (len(lines) == 3) != l5_required:
            raise FixtureCapsuleError("public L5 Evidence presence is not conditional")
        requirements: list[str] = []
        if l5_required:
            l5 = _active_public_fields(
                payloads["L5 Evidence"], ("requires",)
            )
            requirements = json.loads(l5["requires"])
            if requirements != _active_l5_requirements(execution_contract):
                raise FixtureCapsuleError("public L5 Evidence requirements are not exact")
        decoded: dict[str, object] = {
            "version": "execution-level/v2" if is_v2 else "execution-level/v1",
            "requested_level": requested,
            "automatic_level": automatic,
            "minimum_eligible_level": expected_minimum,
            "effective_level": effective,
            "l5_confirmation": confirmation,
            "level": {
                "requested": requested,
                "automatic": automatic,
                "minimum": expected_minimum,
                "effective": effective,
                "edit": edit,
            },
            "basis": {
                "source": sources,
                "triggers": triggers,
                "l1": l1,
                "l2": l2,
                "l5": l5,
                "confirmation": confirmation,
                "unresolved": unresolved,
            },
        }
        if l5_required:
            decoded["l5_evidence"] = {"requires": requirements}
        return decoded
    except (
        FixtureCapsuleError,
        ExecutionLevelError,
        KeyError,
        StopIteration,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return _public_integrity_fallback(
            fallback_value,
            execution_contract=execution_contract,
        )


def engineering_brief_protected_fields() -> tuple[str, ...]:
    """Return the source-owned Brief decision fields used by public projections."""

    authority = TASK_CONTRACT_MODEL.get("analyzed_work_authority")
    ownership = (
        authority.get("decision_ownership")
        if isinstance(authority, dict)
        else None
    )
    fields = (
        ownership.get("engineering_brief")
        if isinstance(ownership, dict)
        else None
    )
    if not isinstance(fields, list) or not fields:
        raise FixtureCapsuleError(
            "Core Engineering Brief decision ownership is unavailable"
        )
    projected: list[str] = []
    for field in fields:
        if not isinstance(field, str) or not field.strip():
            raise FixtureCapsuleError(
                "Core Engineering Brief decision ownership is malformed"
            )
        normalized = _fixture_field_name(field)
        if normalized == "layer3":
            projected.extend(("implementation_layer3", "domain"))
        else:
            projected.append(normalized)
    if len(projected) != len(set(projected)):
        raise FixtureCapsuleError(
            "Core Engineering Brief decision ownership is not unique"
        )
    return tuple(projected)


def project_engineering_brief_task_execution(
    brief_semantics: object,
    execution_result: object,
) -> dict[str, object]:
    """Project one accepted Brief plus Main execution through canonical owners."""

    protected_fields = engineering_brief_protected_fields()
    if (
        not isinstance(brief_semantics, dict)
        or tuple(brief_semantics) != protected_fields
    ):
        raise FixtureCapsuleError(
            "accepted Engineering Brief must contain the exact source-owned "
            "decision fields"
        )
    if not isinstance(execution_result, dict):
        raise FixtureCapsuleError("Main execution result must be an object")
    required_execution_fields = {
        "requested",
        "automatic_level",
        "minimum_eligible_level",
        "effective_level",
        "l5_confirmation",
        "level_basis",
    }
    if not required_execution_fields <= set(execution_result):
        raise FixtureCapsuleError(
            "Main execution result lacks the public execution projection"
        )
    try:
        canonical_values = json.loads(
            json.dumps(
                brief_semantics,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
            )
        )
    except (TypeError, ValueError) as exc:
        raise FixtureCapsuleError(
            f"accepted Engineering Brief must be canonical JSON: {exc}"
        ) from exc
    canonical_semantics = {
        field: canonical_values[field] for field in protected_fields
    }
    extension = {
        "requested_level": execution_result["requested"],
        "automatic_level": execution_result["automatic_level"],
        "minimum_eligible_level": execution_result["minimum_eligible_level"],
        "effective_level": execution_result["effective_level"],
        "l5_confirmation": execution_result["l5_confirmation"],
        "level_basis": execution_result["level_basis"],
    }
    return {
        "contract": "changeforge.engineering-brief-task-projection/v1",
        "source_authority": "task_contract.analyzed_work_authority",
        "brief_semantics": canonical_semantics,
        "execution_level_extension": decode_public_task_extension(
            encode_public_task_extension(extension)
        ),
    }


def engineering_brief_execution_transition_errors(
    before: object,
    after: object,
) -> list[str]:
    """Reject protected Brief drift across an execution-only transition."""

    expected_fields = {
        "contract",
        "source_authority",
        "brief_semantics",
        "execution_level_extension",
    }
    errors: list[str] = []
    for label, projection in (("before", before), ("after", after)):
        if not isinstance(projection, dict) or set(projection) != expected_fields:
            errors.append(
                f"{label} Engineering Brief projection fields are not exact"
            )
            continue
        if (
            projection.get("contract")
            != "changeforge.engineering-brief-task-projection/v1"
            or projection.get("source_authority")
            != "task_contract.analyzed_work_authority"
        ):
            errors.append(
                f"{label} Engineering Brief projection authority is invalid"
            )
        semantics = projection.get("brief_semantics")
        if (
            not isinstance(semantics, dict)
            or tuple(semantics) != engineering_brief_protected_fields()
        ):
            errors.append(
                f"{label} Engineering Brief protected fields are not exact"
            )
        extension = projection.get("execution_level_extension")
        if (
            not isinstance(extension, dict)
            or extension.get("version") != "execution-level/v2"
        ):
            errors.append(
                f"{label} Engineering Brief execution extension is not v2"
            )
    if errors or not isinstance(before, dict) or not isinstance(after, dict):
        return errors
    before_semantics = before["brief_semantics"]
    after_semantics = after["brief_semantics"]
    assert isinstance(before_semantics, dict)
    assert isinstance(after_semantics, dict)
    for field in engineering_brief_protected_fields():
        if before_semantics[field] != after_semantics[field]:
            errors.append(
                f"protected Engineering Brief field changed: {field}"
            )
    return errors


def _render_execution_level_extension(value: object) -> list[str]:
    extension = _active_execution_decision(value, EXECUTION_LEVEL_MODEL)
    return [
        "## Execution Level",
        "",
        *encode_public_task_extension(extension).splitlines(),
        "",
    ]


def _render_evidence_ledger(ledger: list[dict[str, Any]]) -> list[str]:
    fields = EVIDENCE_LEDGER_MODEL["fields"]
    lines = [
        "## Evidence Ledger",
        "",
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _field in fields) + " |",
    ]
    for raw_row in ledger:
        row = _visible_evidence_row(raw_row)
        if row is None:
            raise FixtureCapsuleError(
                "Evidence Ledger row cannot project to the active visible schema"
            )
        cells: list[str] = []
        for field in fields:
            value = row[field]
            if isinstance(value, list):
                rendered = ", ".join(str(item) for item in value) or "—"
            else:
                rendered = str(value)
            cells.append(rendered.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def render_direct_discovery_extension(payload: object) -> str:
    """Render the public Direct inspection boundary without routing authority."""

    if not isinstance(payload, dict):
        raise FixtureCapsuleError("Direct discovery extension must be an object")
    expected = {"inspection_boundary", "inspection_stop_conditions"}
    supplied = expected & set(payload)
    if supplied != expected:
        raise FixtureCapsuleError(
            "Direct discovery extension requires inspection_boundary and "
            "inspection_stop_conditions together"
        )
    boundary = _technical_or_prose_list(
        payload["inspection_boundary"], "inspection_boundary"
    )
    stops = _technical_or_prose_list(
        payload["inspection_stop_conditions"], "inspection_stop_conditions"
    )
    lines = [
        *_render_list("Inspection Boundary", boundary),
        *_render_list("Inspection Stop Conditions", stops),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _render_task(step: dict[str, Any], payload: dict[str, Any]) -> str:
    task_id = _metadata_identifier(payload.get("task_id"), "task_id")
    status = _metadata_identifier(payload.get("status"), "status")
    if status != TASK_CONTRACT_MODEL["assignment_initial_status"]:
        raise FixtureCapsuleError("task assignment Status must be in_progress")
    owner = _prose(payload.get("owner"), "owner")
    goal = _prose(payload.get("goal"), "goal", minimum=20)
    values: dict[str, str | list[str]] = {
        "Task ID": task_id,
        "Status": status,
        "Goal": goal,
        "Owner": owner,
        "Inputs": _technical_or_prose_list(payload.get("inputs"), "inputs"),
        "Allowed Read Scope": _path_or_prose_list(
            payload.get("allowed_read_scope"), "allowed_read_scope"
        ),
        "Allowed Write Scope": _path_or_prose_list(
            payload.get("allowed_write_scope"), "allowed_write_scope"
        ),
        "Non-goals": _prose_list(payload.get("non_goals"), "non_goals"),
        "Dependencies": _optional_prose_list(
            payload.get("dependencies"), "dependencies"
        ),
        "Expected Output": _output_list(
            payload.get("expected_output"), "expected_output"
        ),
        "Acceptance": _prose_list(payload.get("acceptance"), "acceptance"),
        "Verification": _prose_list(
            payload.get("verification"), "verification"
        ),
        "Evidence Requirements": _prose_list(
            payload.get("evidence_requirements"), "evidence_requirements"
        ),
        "Parallel Safety": _prose(payload.get("parallel_safety"), "parallel_safety"),
        "Workspace Requirement": _prose(
            payload.get("workspace_requirement"), "workspace_requirement"
        ),
        "Integration Owner": _prose(
            payload.get("integration_owner"), "integration_owner"
        ),
        "Review Owner": _prose(payload.get("review_owner"), "review_owner"),
        "Stop Conditions": _prose_list(
            payload.get("stop_conditions"), "stop_conditions"
        ),
    }
    if payload.get("template") != "direct-task" and not values["Dependencies"]:
        raise FixtureCapsuleError(
            "non-direct task fixtures require at least one dependency"
        )
    lines = ["# Task Capsule", ""]
    for contract_field in TASK_CONTRACT_MODEL["fields"]:
        value = values[contract_field]
        if contract_field in TASK_CONTRACT_MODEL["optional_for_direct_task"] and not value:
            continue
        if isinstance(value, list):
            lines.extend(_render_list(contract_field, value))
        else:
            lines.extend(_render_scalar(contract_field, value))
        if (
            contract_field == "Allowed Write Scope"
            and payload.get("template") == "direct-task"
            and (
                "inspection_boundary" in payload
                or "inspection_stop_conditions" in payload
            )
        ):
            lines.extend(
                render_direct_discovery_extension(payload).rstrip().splitlines()
            )
            lines.append("")
        if contract_field == "Status" and EXECUTION_LEVEL_EXTENSION_FIELD in payload:
            lines.extend(
                _render_execution_level_extension(
                    payload[EXECUTION_LEVEL_EXTENSION_FIELD]
                )
            )
    lines.extend(_render_skill_selection(step))
    return "\n".join(lines).rstrip() + "\n"


def _render_skill_selection(step: dict[str, Any]) -> list[str]:
    primary = step.get("primary_skill")
    references = _optional_metadata_list(
        step.get("professional_references"),
        "professional_references",
    )
    layer3 = _optional_metadata_list(step.get("layer3_skills", []), "layer3_skills")
    layer3_references = _optional_layer3_reference_list(
        step.get("layer3_references"),
        "layer3_references",
    )
    if len(layer3_references) > 3:
        raise FixtureCapsuleError("layer3_references must contain at most three files")
    selected_layer3 = set(layer3)
    for logical_id in layer3_references:
        owner, _relative = parse_layer3_reference_id(logical_id)
        if owner not in selected_layer3:
            raise FixtureCapsuleError(
                f"Layer 3 Reference owner {owner!r} must be selected in layer3_skills"
            )
    if not isinstance(primary, str) or not primary.strip():
        raise FixtureCapsuleError("non-utility dispatch requires primary_skill")
    _metadata_identifier(primary, "primary_skill")
    lines = [
        "## Professional Skill",
        "",
        f"Primary: {primary.strip()}",
        "References:",
        *([f"- {item}" for item in references] or ["- none"]),
        "Layer 3:",
        *([f"- {item}" for item in layer3] or ["- none"]),
        "Layer 3 References:",
        *([f"- {item}" for item in layer3_references] or ["- none"]),
        "",
    ]
    return lines


def _validate_payload_shape(
    step: dict[str, Any],
    payload: dict[str, Any],
    *,
    allow_legacy_execution_read: bool = False,
) -> str:
    if "dispatch_capsule" in step:
        raise FixtureCapsuleError(
            "dispatch_capsule free text is forbidden; use fixture_capsule fields"
        )
    contract_type = payload.get("contract_type")
    if contract_type not in TYPE_FIELDS:
        raise FixtureCapsuleError(f"unsupported contract_type {contract_type!r}")
    if (
        contract_type == "analysis"
        and EXECUTION_LEVEL_EXTENSION_FIELD in payload
    ):
        raise FixtureCapsuleError(
            "analysis fixture_capsule must not carry execution_level_extension"
        )
    allowed_shapes = [TYPE_FIELDS[contract_type]]
    if contract_type in EXTENDED_TYPE_FIELDS:
        allowed_shapes.append(EXTENDED_TYPE_FIELDS[contract_type])
    if tuple(payload) not in allowed_shapes:
        raise FixtureCapsuleError(
            f"{contract_type} fixture_capsule must use exact ordered fields "
            + " or ".join(str(list(fields)) for fields in allowed_shapes)
        )
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise FixtureCapsuleError(
            f"contract_version must be exactly {CONTRACT_VERSION!r}"
        )
    template = payload.get("template")
    if template not in TEMPLATES[contract_type]:
        raise FixtureCapsuleError(
            f"{contract_type} fixture_capsule has unsupported template {template!r}"
        )
    expected_role = TYPE_TO_ROLE[contract_type]
    if step.get("profile") != expected_role:
        raise FixtureCapsuleError(
            f"{contract_type} fixture_capsule requires profile {expected_role!r}"
        )
    mode = _metadata_identifier(step.get("mode"), "mode")
    if contract_type == "analysis":
        expected_template = ANALYSIS_MODE_TEMPLATES.get(mode)
        if expected_template is None:
            raise FixtureCapsuleError(
                f"analysis fixture_capsule has unsupported mode {mode!r}"
            )
        if template != expected_template:
            raise FixtureCapsuleError(
                f"analysis mode {mode!r} requires template {expected_template!r}"
            )
    if EXECUTION_LEVEL_EXTENSION_FIELD in payload:
        _active_execution_decision(
            payload[EXECUTION_LEVEL_EXTENSION_FIELD],
            EXECUTION_LEVEL_MODEL,
            allow_legacy_read=allow_legacy_execution_read,
        )
    if contract_type == "utility":
        if any(
            field in step
            for field in ("primary_skill", "layer3_skills", "layer3_references")
        ):
            raise FixtureCapsuleError(
                "utility dispatch must not select primary_skill, layer3, or layer3_references"
            )
        if step.get("professional_references") != []:
            raise FixtureCapsuleError("utility dispatch must use empty professional_references")
    else:
        _render_skill_selection(step)
    return contract_type


def _render_normal(step: dict[str, Any], payload: dict[str, Any], contract_type: str) -> str:
    if contract_type == "task":
        return _render_task(step, payload)
    title = {
        "analysis": "Analysis Assignment",
        "review": "Review Assignment",
    }[contract_type]
    goal = _prose(payload.get("goal"), "goal", minimum=20)
    scope = _path_or_prose_list(payload.get("scope"), "scope")
    validation = _prose_list(payload.get("validation"), "validation")
    stop_conditions = _prose_list(payload.get("stop_conditions"), "stop_conditions")
    output = _output_list(payload.get("output"), "output")
    lines = [
        f"# {title}",
        "",
        "## Mode",
        "",
        str(step["mode"]),
        "",
        "## Assigned Role",
        "",
        str(step["profile"]),
        "",
    ]
    if contract_type == "review" and EXECUTION_LEVEL_EXTENSION_FIELD in payload:
        task_id = _metadata_identifier(payload.get("task_id"), "task_id")
        lines.extend(_render_scalar("Task ID", task_id))
        lines.extend(
            _render_execution_level_extension(
                payload[EXECUTION_LEVEL_EXTENSION_FIELD]
            )
        )
    lines.extend(
        [
            "## Goal",
            "",
            goal,
            "",
            *_render_list(
                "Allowed Scope" if contract_type != "review" else "Reviewed Scope",
                scope,
            ),
            *_render_skill_selection(step),
        ]
    )
    if contract_type == "analysis":
        lines.extend(
            _render_list(
                "Required Evidence",
                _prose_list(payload.get("evidence"), "evidence"),
            )
        )
    else:
        lines.extend(
            _render_list(
                "Inputs",
                _technical_or_prose_list(payload.get("inputs"), "inputs"),
            )
        )
        lines.extend(
            _render_list(
                "Acceptance" if contract_type == "task" else "Review Criteria",
                _prose_list(payload.get("acceptance"), "acceptance"),
            )
        )
    lines.extend(_render_list("Validation", validation))
    lines.extend(_render_list("Stop Conditions", stop_conditions))
    lines.extend(_render_list("Output", output))
    return "\n".join(lines).rstrip() + "\n"


def _render_mapping(heading: str, value: object) -> list[str]:
    if not isinstance(value, dict) or not value:
        raise FixtureCapsuleError(f"{heading} must be a non-empty mapping")
    return [
        f"## {heading}",
        "",
        *[
            f"- {key}: {json.dumps(value[key], ensure_ascii=False, sort_keys=True)}"
            for key in sorted(value)
        ],
        "",
    ]


def _validate_utility_inputs(mode: str, value: object) -> None:
    if not isinstance(value, dict):
        raise FixtureCapsuleError("utility Inputs must be a mapping")
    if mode == "diff-export/no-edit":
        expected = ("base", "head", "artifact_delivery")
        if tuple(value) != expected:
            raise FixtureCapsuleError(
                f"diff-export Inputs must use exact ordered fields {list(expected)}"
            )
        base = _metadata_identifier(value.get("base"), "Inputs.base")
        head = _metadata_identifier(value.get("head"), "Inputs.head")
        if base == head:
            raise FixtureCapsuleError("diff-export base and head must differ")
        if value.get("artifact_delivery") != "supplied-content":
            raise FixtureCapsuleError(
                "diff-export artifact_delivery must be 'supplied-content'"
            )
        return
    expected = ("validation_targets",)
    if tuple(value) != expected:
        raise FixtureCapsuleError(
            f"validation-only Inputs must use exact ordered fields {list(expected)}"
        )
    _technical_target_list(value.get("validation_targets"), "Inputs.validation_targets")


def utility_assignment_return_errors(
    assignment: object,
    result: object,
) -> list[str]:
    """Validate one fixture-only Utility Assignment/Return visible contract pair."""

    errors: list[str] = []
    if not isinstance(assignment, dict) or tuple(assignment) != UTILITY_ASSIGNMENT_FIELDS:
        return [
            "Utility Assignment must use exact ordered fields "
            f"{list(UTILITY_ASSIGNMENT_FIELDS)}"
        ]
    if not isinstance(result, dict) or tuple(result) != UTILITY_RETURN_FIELDS:
        return [
            "Utility Return must use exact ordered fields "
            f"{list(UTILITY_RETURN_FIELDS)}"
        ]
    task_id = assignment["task_id"]
    owner = assignment["owner"]
    if not _fixture_nonempty_text(task_id) or not _fixture_nonempty_text(owner):
        errors.append("Utility Assignment Task ID and Owner must be non-empty")
        return errors
    assignment_statuses = TASK_CONTRACT_MODEL["template_schemas"][
        "utility-capsule-template.md"
    ]["status_sections"][0]["allowed"]
    return_statuses = TASK_CONTRACT_MODEL["template_schemas"][
        "utility-capsule-template.md"
    ]["status_sections"][1]["allowed"]
    if assignment["status"] not in assignment_statuses:
        errors.append(
            f"Utility Assignment Status must be one of {assignment_statuses}"
        )
    if result["status"] not in return_statuses:
        errors.append(f"Utility Return Status must be one of {return_statuses}")
    if result["task_id"] != task_id:
        errors.append("Utility Return Task ID must match Utility Assignment")
    if result["owner"] != owner:
        errors.append("Utility Return Owner must match Utility Assignment")
    if result["mode"] != assignment["mode"]:
        errors.append("Utility Return mode must match Utility Assignment")
    if result["no_edit_enforcement"] != assignment["no_edit_enforcement"]:
        errors.append(
            "Utility Return no-edit enforcement must match Utility Assignment"
        )
    errors.extend(
        completion_transition_errors(
            assignment["status"], result["status"], same_task_id=True
        )
    )

    assignment_ledger = assignment["evidence_ledger"]
    errors.extend(
        evidence_ledger_errors(
            assignment_ledger,
            task_id=task_id,
            owner=owner,
            required_claims=UTILITY_ASSIGNMENT_REQUIRED_CLAIMS,
            required_freshness_marker=0,
            latest_material_edit_marker=None,
            completion_status=assignment["status"],
        )
    )
    if isinstance(assignment_ledger, list):
        current_assignment_claims = {
            row.get("Claim")
            for row in assignment_ledger
            if isinstance(row, dict) and row.get("State") == "current"
        }
        for claim in UTILITY_ASSIGNMENT_REQUIRED_CLAIMS:
            if claim not in current_assignment_claims:
                errors.append(
                    f"Utility Assignment missing current evidence for {claim!r}"
                )

    return_ledger = result["evidence_ledger"]
    errors.extend(
        evidence_ledger_errors(
            return_ledger,
            task_id=task_id,
            owner=owner,
            required_claims=UTILITY_RETURN_REQUIRED_CLAIMS,
            required_freshness_marker=0,
            latest_material_edit_marker=None,
            completion_status=result["status"],
        )
    )
    if isinstance(assignment_ledger, list) and isinstance(return_ledger, list):
        returned_by_id = {
            row.get("Evidence ID"): row
            for row in return_ledger
            if isinstance(row, dict)
        }
        for assignment_row in assignment_ledger:
            if not isinstance(assignment_row, dict):
                continue
            evidence_id = assignment_row.get("Evidence ID")
            if returned_by_id.get(evidence_id) != assignment_row:
                errors.append(
                    f"Utility Return must preserve assignment Evidence ID {evidence_id!r}"
                )
    workspace_check = result["workspace_diff_check"]
    workspace_status = (
        workspace_check.get("status") if isinstance(workspace_check, dict) else None
    )
    if result["status"] == "completed" and workspace_status != "unchanged":
        errors.append(
            "Utility Return completed requires an unchanged workspace diff check"
        )
    return errors


def _render_utility(step: dict[str, Any]) -> str:
    utility = step.get("utility_capsule")
    if not isinstance(utility, dict) or tuple(utility) != UTILITY_FIELDS:
        raise FixtureCapsuleError(
            f"utility_capsule must use exact ordered fields {list(UTILITY_FIELDS)}"
        )
    task_id = _metadata_identifier(utility.get("task_id"), "utility_capsule.task_id")
    status = _metadata_identifier(utility.get("status"), "utility_capsule.status")
    assignment_statuses = TASK_CONTRACT_MODEL["template_schemas"][
        "utility-capsule-template.md"
    ]["status_sections"][0]["allowed"]
    if status not in assignment_statuses:
        raise FixtureCapsuleError(
            f"utility assignment Status must be one of {assignment_statuses}"
        )
    owner = _prose(utility.get("owner"), "utility_capsule.owner")
    mode = _metadata_identifier(utility.get("mode"), "utility_capsule.mode")
    if mode not in UTILITY_MODES:
        raise FixtureCapsuleError(f"unsupported utility mode {mode!r}")
    if mode != step.get("mode"):
        raise FixtureCapsuleError("utility mode must match dispatch mode")
    enforcement = _metadata_identifier(
        utility.get("no_edit_enforcement"),
        "utility_capsule.no_edit_enforcement",
    )
    if enforcement not in NO_EDIT_ENFORCEMENTS:
        raise FixtureCapsuleError(
            f"unsupported no-edit enforcement {enforcement!r}"
        )
    goal = _prose(utility.get("goal"), "utility_capsule.goal", minimum=20)
    scope = utility.get("allowed_scope")
    if not isinstance(scope, dict) or set(scope) != {"workspace_root", "paths"}:
        raise FixtureCapsuleError("utility allowed_scope must name workspace_root and paths")
    workspace_root = _repo_path(scope.get("workspace_root"), "workspace_root")
    paths = _path_or_prose_list(scope.get("paths"), "allowed_scope.paths")
    _validate_utility_inputs(mode, utility.get("inputs"))
    baseline = utility.get("workspace_baseline")
    if not isinstance(baseline, dict) or set(baseline) != {"check_commands", "change_set"}:
        raise FixtureCapsuleError(
            "utility workspace_baseline must name check_commands and change_set"
        )
    check_commands = _command_list(baseline.get("check_commands"), "check_commands")
    change_set = _change_set_list(baseline.get("change_set"), "change_set")
    commands = _command_list(utility.get("commands_allowed"), "commands_allowed")
    expected = _prose_list(utility.get("expected_evidence"), "expected_evidence")
    stops = _prose_list(utility.get("stop_conditions"), "stop_conditions")
    ledger = utility.get("evidence_ledger")
    ledger_errors = evidence_ledger_errors(
        ledger,
        task_id=task_id,
        owner=owner,
        required_claims=UTILITY_ASSIGNMENT_REQUIRED_CLAIMS,
        required_freshness_marker=0,
        latest_material_edit_marker=None,
        completion_status=status,
    )
    if ledger_errors:
        raise FixtureCapsuleError(
            "utility assignment Evidence Ledger is invalid: " + "; ".join(ledger_errors)
        )
    assert isinstance(ledger, list)
    current_claims = {
        row.get("Claim")
        for row in ledger
        if isinstance(row, dict) and row.get("State") == "current"
    }
    missing_claims = set(UTILITY_ASSIGNMENT_REQUIRED_CLAIMS) - current_claims
    if missing_claims:
        raise FixtureCapsuleError(
            "utility assignment Evidence Ledger is missing current claims "
            f"{sorted(missing_claims)}"
        )
    lines = [
        "# Utility Assignment",
        "",
        "## Task ID",
        "",
        task_id,
        "",
        "## Status",
        "",
        status,
        "",
        "## Owner",
        "",
        owner,
        "",
        "## Mode",
        "",
        mode,
        "",
        "## No-edit Enforcement",
        "",
        enforcement,
        "",
        "## Assigned Role",
        "",
        str(step["profile"]),
        "",
        "## Goal",
        "",
        goal,
        "",
        "## Allowed Scope",
        "",
        f"Workspace Root: {workspace_root}",
        *[f"- {item}" for item in paths],
        "",
        *_render_mapping("Inputs", utility.get("inputs")),
        "## Workspace Baseline",
        "",
        "Checks:",
        *[f"- {item}" for item in check_commands],
        "Change Set:",
        *[f"- {item}" for item in change_set],
        "",
        *_render_list("Commands Allowed", commands),
        *_render_list("Expected Evidence", expected),
        *_render_list("Stop Conditions", stops),
        *_render_evidence_ledger(ledger),
        *_render_list(
            "Output",
            [
                "Utility Return with Task ID, four-state Status, Owner, visible Evidence Ledger, outcomes, commands, workspace diff check, unverified scope, and residual risk"
            ],
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_fixture_capsule_payload(
    step: dict[str, Any],
    payload: dict[str, Any],
) -> str:
    """Validate a structured payload and render the canonical measured Capsule."""

    contract_type = _validate_payload_shape(step, payload)
    if contract_type == "utility":
        return _render_utility(step)
    return _render_normal(step, payload, contract_type)


def canonical_capsule_sha256(step: dict[str, Any], payload: dict[str, Any]) -> str:
    text = render_fixture_capsule_payload(step, payload)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_and_render_fixture_capsule(step: dict[str, Any]) -> str:
    payload = step.get("fixture_capsule")
    if not isinstance(payload, dict):
        raise FixtureCapsuleError("dispatch requires a fixture_capsule mapping")
    rendered = render_fixture_capsule_payload(step, payload)
    expected = payload.get("canonical_sha256")
    actual = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if not isinstance(expected, str) or expected != actual:
        raise FixtureCapsuleError(
            "fixture_capsule canonical_sha256 does not match the deterministic render"
        )
    return rendered
