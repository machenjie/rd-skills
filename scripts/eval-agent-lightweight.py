#!/usr/bin/env python3
"""Evaluate the hookless control plane from deterministic fixture traces."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shlex
import statistics
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, NamedTuple

from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    CORE_CONTRACTS,
    EVIDENCE_LEDGER_MODEL,
    IMPLEMENTATION_DISCIPLINE_MODEL,
    REVIEW_DISCIPLINE_MODEL,
    ExecutionLevelError,
    ValidationProblem,
    classify_concrete_action_authority,
    compute_execution_level,
    load_yaml_file,
    professional_review_skill_ids,
    reference_paths,
    report_output_paths,
)
from fixture_capsule_contract import (
    FixtureCapsuleError,
    UTILITY_ASSIGNMENT_FIELDS,
    UTILITY_ASSIGNMENT_REQUIRED_CLAIMS,
    UTILITY_RETURN_FIELDS,
    UTILITY_RETURN_REQUIRED_CLAIMS,
    completion_claim_errors as _core_completion_claim_errors,
    completion_transition_errors,
    combined_review_completion_errors,
    evidence_ledger_errors,
    parse_layer3_reference_id,
    trace_execution_level_migration_errors,
    validate_and_render_fixture_capsule,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "agent-light-trajectories" / "cases.yaml"
REPORT_JSON = ROOT / "reports" / "hookless-control-plane-eval.json"
REPORT_MD = ROOT / "reports" / "hookless-control-plane-eval.md"
DIST_SKILLS = ROOT / "dist" / "universal" / "skills"
BUILD_PROFILES = ("recommended", "full", "dev")
FIXTURE_SCHEMA_VERSION = 2
CANONICAL_EVIDENCE_LEDGER_FIELDS = tuple(EVIDENCE_LEDGER_MODEL["fields"])
EXTERNAL_READ_MODEL = CORE_CONTRACTS["external_read_contract"]
RETIRED_EVIDENCE_LEDGER_FIELDS = (
    "Evidence ID",
    "Task ID",
    "Action",
    "Freshness Marker",
    "Evidence State",
    "Supersedes",
)
EVIDENCE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-]+\.[A-Za-z0-9]+"
)

PRODUCTIVE_ACTIONS = {
    "search",
    "read",
    "edit",
    "repair",
    "validate",
    "review",
    "re-review",
    "diagnose",
    "first_executable_slice",
    "export-diff",
    "implementation-discipline",
}
IMPLEMENTATION_HANDOFF_ACTION = "implementation-handoff"
REVIEW_INPUT_READY_ACTION = "review-input-ready"
ADAPTIVE_TEST_EVIDENCE_ACTION = "adaptive-test-evidence"
INTERNAL_EVIDENCE_ACTIONS = {
    "implementation-discipline",
    IMPLEMENTATION_HANDOFF_ACTION,
    REVIEW_INPUT_READY_ACTION,
    ADAPTIVE_TEST_EVIDENCE_ACTION,
    REVIEW_DISCIPLINE_MODEL["trace_action"],
}
WORKER_EVIDENCE_ACTIONS = PRODUCTIVE_ACTIONS | {"brief", "task_plan", "finding"}
EDIT_ACTIONS = {"edit", "repair"}
REVIEW_ACTIONS = {"review", "re-review"}
MAIN_ACTIONS = {
    "classify",
    "dispatch",
    "progress",
    "escalate",
    "user_decision",
    "close",
    REVIEW_INPUT_READY_ACTION,
}
PROGRESS_CHECKPOINT_TYPES = {
    "start/path",
    "dispatch/batch",
    "validation",
    "review/close",
}
PROFILE_ACTIONS = {
    "main-control-agent": MAIN_ACTIONS,
    "analysis-agent": {"search", "read", "diagnose", "first_executable_slice", "brief", "task_plan"},
    "task-agent": {
        "search",
        "read",
        "edit",
        "repair",
        "validate",
        "capture-change-evidence",
        "export-diff",
        "implementation-discipline",
        IMPLEMENTATION_HANDOFF_ACTION,
        "adaptive-test-evidence",
    },
    "review-agent": {
        "search",
        "read",
        "validate",
        "review",
        "re-review",
        "finding",
        REVIEW_DISCIPLINE_MODEL["trace_action"],
    },
}
EVIDENCE_LIMITATIONS = (
    "Step counts are structural proxies and do not prove wall-clock performance.",
    "Checked-in fixtures do not prove real-host accuracy.",
    "Fixture evaluation does not prove the installed user experience.",
    "Typed discipline events prove fixture structure and order, not the quality or completeness of real repository inspection.",
)
IMPLEMENTATION_DISCIPLINE_SCHEMA_VERSION = 1
IMPLEMENTATION_READ_KINDS = (
    "owning-implementation",
    "relevant-existing-tests",
    "minimum-caller-consumer",
)
IMPLEMENTATION_READ_FIELDS = (
    "actor",
    "action",
    "task_id",
    "evidence_id",
    "read_kind",
    "path",
)
IMPLEMENTATION_TEST_READ_FIELDS = (
    *IMPLEMENTATION_READ_FIELDS,
    "compatibility_anchor",
)
IMPLEMENTATION_ANCHORED_READ_FIELDS = (
    "actor",
    "action",
    "task_id",
    "acceptance_id",
    "evidence_id",
    "artifact_id",
    "source_anchor",
    "read_kind",
    "path",
)
IMPLEMENTATION_ANCHORED_TEST_READ_FIELDS = (
    *IMPLEMENTATION_ANCHORED_READ_FIELDS,
    "compatibility_anchor",
)
IMPLEMENTATION_SOURCE_READ_KINDS = {
    *IMPLEMENTATION_READ_KINDS,
    "nearest-candidate",
    "reuse-candidate",
}
IMPLEMENTATION_KINDS = {
    "bugfix",
    "repair",
    "feature",
    "integration",
    "migration",
    "security",
    "reliability",
    "release",
}
ADAPTIVE_TEST_CONTRACT = IMPLEMENTATION_DISCIPLINE_MODEL["adaptive_testing_contract"]
IMPLEMENTATION_GUARD_CODES = {
    "A": "guard-a-inspection-reads",
    "B": "guard-b-inspection-verification",
    "C": "guard-c-observable-acceptance",
    "D": "guard-d-bugfix-verification",
    "E": "guard-e-placement-reuse",
    "F": "guard-f-smallest-complete-change",
    "G": IMPLEMENTATION_DISCIPLINE_MODEL["adaptive_testing_contract"]["guard_id"],
    "order": "edit-before-discipline",
}
IMPLEMENTATION_DISCIPLINE_FIELDS = (
    "actor",
    "action",
    "schema_version",
    "task_id",
    "implementation_kind",
    "evidence",
)
IMPLEMENTATION_GUARD_FIELDS = {
    "guard-a-inspection-reads": ("guard", "read_evidence"),
    "guard-b-inspection-verification": (
        "guard",
        "behavior_verified",
        "owner_verified",
        "reuse_candidate_verified",
        "edit_boundary_verified",
    ),
    "guard-c-observable-acceptance": (
        "guard",
        "outcome_matrix",
        "validation_signal",
    ),
    "guard-d-bugfix-verification": (
        "guard",
        "applies",
        "failure_mechanism_verified",
        "symptom_cause_separated",
        "same_pattern_scan_complete",
        "recurrence_status",
        "recurrence_signal",
    ),
    "guard-e-placement-reuse": (
        "guard",
        "placement_resolved",
        "reuse_evaluated",
        "dependency_direction_resolved",
        "public_api_widened_for_tests",
    ),
    "guard-f-smallest-complete-change": (
        "guard",
        "smallest_complete",
        "unrelated_refactor",
        "duplicate_helper",
        "unnecessary_dependency",
        "contract_handling",
    ),
    IMPLEMENTATION_GUARD_CODES["G"]: (
        "guard",
        *ADAPTIVE_TEST_CONTRACT["decision_fields"],
    ),
}
IMPLEMENTATION_GUARD_ENHANCED_FIELDS = {
    "guard-b-inspection-verification": (
        *IMPLEMENTATION_GUARD_FIELDS["guard-b-inspection-verification"],
        "owner_decision",
    ),
    "guard-d-bugfix-verification": (
        *IMPLEMENTATION_GUARD_FIELDS["guard-d-bugfix-verification"],
        "mechanism_binding",
    ),
    "guard-e-placement-reuse": (
        *IMPLEMENTATION_GUARD_FIELDS["guard-e-placement-reuse"],
        "reuse_decision",
    ),
}
IMPLEMENTATION_GUARD_ANCHORED_FIELDS = {
    "guard-d-bugfix-verification": (
        *IMPLEMENTATION_GUARD_ENHANCED_FIELDS["guard-d-bugfix-verification"],
        "same_pattern_scan",
    ),
    "guard-e-placement-reuse": (
        *IMPLEMENTATION_GUARD_ENHANCED_FIELDS["guard-e-placement-reuse"],
        "placement_decision",
    ),
}
IMPLEMENTATION_GUARD_ORDER = tuple(
    guard
    for guard in IMPLEMENTATION_GUARD_FIELDS
    if guard != IMPLEMENTATION_GUARD_CODES["G"]
)
IMPLEMENTATION_OUTCOMES = ("normal", "invalid", "boundary", "forbidden")
IMPLEMENTATION_OUTCOME_STATES = {"applicable", "not-applicable"}
BUGFIX_IMPLEMENTATION_KINDS = {"bugfix", "repair"}
ADAPTIVE_TEST_APPROACHES = set(ADAPTIVE_TEST_CONTRACT["approaches"])
ADAPTIVE_TEST_EVIDENCE_FIELDS = (
    "actor",
    "action",
    "task_id",
    "evidence_id",
    "evidence_kind",
    "result",
    "failure_class",
    "oracle",
    "assertion",
    "freshness",
)
ADAPTIVE_TEST_ANCHORED_EVIDENCE_FIELDS = (
    "actor",
    "action",
    "task_id",
    "acceptance_id",
    "evidence_id",
    "artifact_id",
    "source_anchor",
    "evidence_kind",
    "result",
    "failure_class",
    "oracle_id",
    "mechanism_id",
    "assertion_fingerprint",
    "oracle",
    "assertion",
    "freshness",
)
IMPLEMENTATION_ORACLE_AUTHORITY_FIELDS = (
    "schema_version",
    "task_id",
    "acceptance_id",
    "mechanism_id",
    "failure_mechanism",
    "oracle_id",
    "oracle",
    "assertion_fingerprint",
    "validation_binding",
    "source_bindings",
    "placement_binding",
    "same_pattern_binding",
    "canonical_sha256",
)
IMPLEMENTATION_ORACLE_VALIDATION_FIELDS = (
    "evidence_id",
    "artifact_id",
    "source_anchor",
)
IMPLEMENTATION_ORACLE_SOURCE_FIELDS = (
    "evidence_id",
    "artifact_id",
    "path",
    "source_anchor",
    "read_kind",
)
IMPLEMENTATION_ORACLE_PLACEMENT_FIELDS = (
    "evidence_id",
    "artifact_id",
    "source_anchor",
)
IMPLEMENTATION_ORACLE_SCAN_FIELDS = (
    "pattern_id",
    "scope",
    "evidence_id",
    "artifact_id",
    "source_anchor",
    "proof_kind",
)
IMPLEMENTATION_ORACLE_BINDING_PURPOSES = {
    "source",
    "validation",
    "scan",
    "placement",
}
IMPLEMENTATION_ORACLE_CONTRACTS = MappingProxyType(
    {
        "single-file-bug-fix": MappingProxyType(
            {
                "task_id": "task-single-file-bug-fix-1",
                "acceptance_id": "acceptance.task-single-file-bug-fix-1",
                "canonical_sha256": (
                    "3f53a3dc33ded622b947139b1b55bf9857b325b87b36e70ddc12645b18be7a25"
                ),
            }
        )
    }
)
ADAPTIVE_TEST_HIGH_RISK_TRIGGERS = set(ADAPTIVE_TEST_CONTRACT["high_risk_triggers"])
ADAPTIVE_TEST_DERIVED_BINDINGS = ADAPTIVE_TEST_CONTRACT["derived_high_risk_bindings"]
ADAPTIVE_TEST_AFTER_QUALIFIERS = set(ADAPTIVE_TEST_CONTRACT["test_after_only_for"])
ADAPTIVE_EXISTING_PROOF_QUALIFIERS = set(
    ADAPTIVE_TEST_CONTRACT["existing_proof_only_requires"][:-1]
)
ADAPTIVE_NON_TEST_QUALIFIERS = set(
    ADAPTIVE_TEST_CONTRACT["non_test_validation_only_for"]
)
REQUIRED_BEHAVIOR_GROUPS = {
    "ai-reading-ownership": (
        "ai-reading-owner-not-nearest",
        "ai-reading-existing-helper-reused",
        "ai-reading-test-compatibility-rule",
        "ai-reading-root-cause-not-failure-location",
        "ai-reading-tests-before-edit",
    ),
    "adaptive-testing": (
        "adaptive-bugfix-red-edit-green",
        "adaptive-high-risk-requires-test-first",
        "adaptive-low-risk-local-allows-test-after",
        "adaptive-documentation-uses-non-test-validation",
        "adaptive-environment-failure-not-red",
        "adaptive-weakened-assertion-rejected",
    ),
    "engineering-closure": (
        "closure-same-pattern-exposure-assessed",
        "closure-new-structure-requires-placement-evidence",
        "closure-parallel-writes-require-isolation",
        "closure-validation-fresh-after-latest-edit",
        "closure-repair-requires-fresh-rereview",
        "closure-completion-requires-current-evidence",
    ),
}
REQUIRED_BEHAVIOR_DIMENSIONS = {"order", "decision", "freshness", "output"}


class RequiredBehaviorContract(NamedTuple):
    positive_case: str
    validator_family: str
    bypass_mutation: str
    expected_error: str
    dimensions: tuple[str, ...]


REQUIRED_BEHAVIOR_CONTRACTS = MappingProxyType(
    {
        "ai-reading-owner-not-nearest": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "owner-nearest-substitution",
            "guard-b-inspection-verification", ("decision",),
        ),
        "ai-reading-existing-helper-reused": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "new-structure-despite-compatible-helper",
            "guard-e-placement-reuse", ("decision",),
        ),
        "ai-reading-test-compatibility-rule": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "drop-test-compatibility-anchor",
            "guard-a-inspection-reads", ("output",),
        ),
        "ai-reading-root-cause-not-failure-location": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "collapse-symptom-into-cause",
            "guard-d-bugfix-verification", ("decision",),
        ),
        "ai-reading-tests-before-edit": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "move-relevant-tests-after-edit",
            "guard-a-inspection-reads", ("order",),
        ),
        "adaptive-bugfix-red-edit-green": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "remove-green-after-edit",
            "guard-g-adaptive-testing", ("order", "output"),
        ),
        "adaptive-high-risk-requires-test-first": RequiredBehaviorContract(
            "security-ssrf-boundary", "metrics", "downgrade-high-risk-to-test-after",
            "guard-g-adaptive-testing", ("decision",),
        ),
        "adaptive-low-risk-local-allows-test-after": RequiredBehaviorContract(
            "single-module-feature", "metrics", "strip-test-after-qualifier",
            "guard-g-adaptive-testing", ("decision",),
        ),
        "adaptive-documentation-uses-non-test-validation": RequiredBehaviorContract(
            "release-rollback", "metrics", "misclassify-documentation-as-behavior",
            "guard-g-adaptive-testing", ("decision",),
        ),
        "adaptive-environment-failure-not-red": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "red-environment-failure",
            "guard-g-adaptive-testing", ("decision", "output"),
        ),
        "adaptive-weakened-assertion-rejected": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "weaken-green-assertion",
            "guard-g-adaptive-testing", ("output",),
        ),
        "closure-same-pattern-exposure-assessed": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "skip-same-pattern-scan",
            "guard-d-bugfix-verification", ("decision",),
        ),
        "closure-new-structure-requires-placement-evidence": RequiredBehaviorContract(
            "single-module-feature", "metrics", "drop-placement-evidence-for-new-structure",
            "guard-e-placement-reuse", ("decision",),
        ),
        "closure-parallel-writes-require-isolation": RequiredBehaviorContract(
            "isolated-write-parallel-contract", "scheduling",
            "remove-parallel-workspace-isolation", "parallel-write-isolation",
            ("decision",),
        ),
        "closure-validation-fresh-after-latest-edit": RequiredBehaviorContract(
            "single-file-bug-fix", "metrics", "edit-after-validation",
            "review-stale-validation", ("order", "freshness"),
        ),
        "closure-repair-requires-fresh-rereview": RequiredBehaviorContract(
            "repair-and-rereview", "metrics", "remove-fresh-rereview",
            "repair-rereview-missing", ("order", "freshness"),
        ),
        "closure-completion-requires-current-evidence": RequiredBehaviorContract(
            "repair-and-rereview", "metrics", "drop-current-completion-evidence",
            "completion-current-evidence", ("freshness", "output"),
        ),
    }
)
REQUIRED_BEHAVIOR_BYPASS_MUTATIONS = frozenset(
    contract.bypass_mutation for contract in REQUIRED_BEHAVIOR_CONTRACTS.values()
)
REVIEW_DISCIPLINE_ACTION = REVIEW_DISCIPLINE_MODEL["trace_action"]
REVIEW_DISCIPLINE_FIELDS = tuple(REVIEW_DISCIPLINE_MODEL["event_fields"])
REVIEW_DIFF_FIELDS = tuple(REVIEW_DISCIPLINE_MODEL["diff_fields"])
REVIEW_VALIDATION_FIELDS = tuple(REVIEW_DISCIPLINE_MODEL["validation_fields"])
REVIEW_BASE_DIMENSIONS = tuple(REVIEW_DISCIPLINE_MODEL["base_dimensions"])
REVIEW_DIMENSION_DECISIONS = set(REVIEW_DISCIPLINE_MODEL["dimension_decisions"])
REVIEW_PROFESSIONAL_RISK_MATRIX = REVIEW_DISCIPLINE_MODEL[
    "professional_risk_matrix"
]
REVIEW_PROFESSIONAL_RISK_DIMENSIONS = tuple(
    REVIEW_PROFESSIONAL_RISK_MATRIX["dimensions"]
)
REVIEW_PROFESSIONAL_RISK_STATUSES = set(
    REVIEW_PROFESSIONAL_RISK_MATRIX["statuses"]
)
REVIEW_PROFESSIONAL_RISK_FIELDS = tuple(
    REVIEW_PROFESSIONAL_RISK_MATRIX["decision_fields"]
)
REVIEW_SKILL_IDS = frozenset(
    professional_review_skill_ids(
        load_yaml_file(ROOT / "src/registry/professional-skills.yaml")[
            "professional_skills"
        ],
        REVIEW_PROFESSIONAL_RISK_MATRIX,
    )
)
REVIEW_DIFF_KINDS = set(REVIEW_DISCIPLINE_MODEL["diff_kinds"])
REVIEW_VALIDATION_SOURCES = set(REVIEW_DISCIPLINE_MODEL["validation_sources"])
REVIEW_VALIDATION_RESULTS = set(REVIEW_DISCIPLINE_MODEL["validation_results"])
REVIEW_EVIDENCE_SOURCES = set(REVIEW_DISCIPLINE_MODEL["evidence_sources"])
REVIEW_FORBIDDEN_EVIDENCE_SOURCES = set(
    REVIEW_DISCIPLINE_MODEL["forbidden_evidence_sources"]
)
REVIEW_KINDS = set(REVIEW_DISCIPLINE_MODEL["review_kinds"])
REVIEW_VERDICTS = set(REVIEW_DISCIPLINE_MODEL["verdicts"])
REVIEW_INPUT_READINESS_MODEL = REVIEW_DISCIPLINE_MODEL["review_input_readiness"]
REVIEW_INPUT_REQUIRED_FIELDS = tuple(
    REVIEW_INPUT_READINESS_MODEL["required_fields"]
)
REVIEW_INPUT_EXACT_EVIDENCE_KINDS = set(
    REVIEW_INPUT_READINESS_MODEL["exact_change_evidence_kinds"]
)
REVIEW_INPUT_FORBIDDEN_EVIDENCE_KINDS = set(
    REVIEW_INPUT_READINESS_MODEL["forbidden_substitutes"]
)
IMPLEMENTATION_HANDOFF_FIELDS = (
    "actor",
    "action",
    "handoff_id",
    "task_id",
    *REVIEW_INPUT_REQUIRED_FIELDS,
)
EXACT_CHANGE_EVIDENCE_FIELDS = ("kind", "artifact", "generation")
REVIEWER_CAPABILITY_ACCESSIBILITY_FIELDS = (
    "native-change-read",
    "change-evidence-export",
    "supplied-change-delivery",
    "reviewer-change-consume",
    "non-mutating-validation",
)
VALIDATION_AFTER_LATEST_MATERIAL_EDIT_FIELDS = (
    "evidence_id",
    "result",
    "generation",
)
REVIEW_INPUT_READY_FIELDS = ("actor", "action", "handoff_id", "ready")
REVIEW_INPUT_BINDING_FIELDS = ("handoff_id", "artifact", "generation")
NATIVE_CHANGE_REFERENCE_FIELDS = (
    "reference",
    "generation",
    "reviewer",
    "changed_paths",
    "readable",
)
GENERIC_CAPABILITY_FIELDS = tuple(
    REVIEW_DISCIPLINE_MODEL["generic_capability_contract"]["injected_fields"]
)
GENERIC_CAPABILITY_STATES = set(
    REVIEW_DISCIPLINE_MODEL["generic_capability_contract"]["states"]
)
TASK_BOUNDARY_MODEL = CORE_CONTRACTS["task_contract"]["task_boundary"]
FINDING_RELATION_MODEL = CORE_CONTRACTS["task_contract"]["finding_relations"]
DELTA_IMPACT_FIELDS = ("brief", "tasks", "dependencies", "skills", "reviews")
DELTA_BRIEF_SECTIONS_BY_INVALIDATION = {
    "Acceptance-or-Non-goals": {"Acceptance and Non-goals"},
    "Owner-or-Placement-or-Invariant": {
        "Ownership and Invariants",
        "Placement and Reuse",
    },
    "contract-or-data-semantics": {"Contract / Data / Failure Impact"},
    "dependency-or-rollback": {"Risks and Rollback", "Task Dependencies"},
    "material-risk": {"Risks and Rollback"},
    "scope-blocker": {
        "Acceptance and Non-goals",
        "Ownership and Invariants",
        "Placement and Reuse",
        "Contract / Data / Failure Impact",
    },
}
SAME_PATTERN_MODEL = CORE_CONTRACTS["task_contract"]["same_pattern_scan"]
REVIEW_LEVEL_POLICY = REVIEW_DISCIPLINE_MODEL["effective_level_policy"]
UTILITY_MODES = {"validation-only/no-edit", "diff-export/no-edit"}
UTILITY_CAPSULE_FIELDS = UTILITY_ASSIGNMENT_FIELDS
UTILITY_EVIDENCE_FIELDS = UTILITY_RETURN_FIELDS
UTILITY_ASSIGNMENT_STATUSES = {"in_progress"}
UTILITY_RETURN_STATUSES = {"blocked", "partial", "completed"}
UTILITY_CAPABILITY_OPERATIONS = {
    "workspace-state-observation",
    "change-evidence-export",
    "non-mutating-validation",
}
WORKSPACE_CHECK_COMMANDS = ("workspace-state-observation",)


def _git_diff_header_paths(header: str) -> tuple[str, str] | None:
    try:
        fields = shlex.split(header)
    except ValueError:
        return None
    if (
        len(fields) != 4
        or fields[:2] != ["diff", "--git"]
        or not fields[2].startswith("a/")
        or not fields[3].startswith("b/")
        or len(fields[2]) <= 2
        or len(fields[3]) <= 2
    ):
        return None
    return fields[2][2:], fields[3][2:]


def _diff_metadata_values(lines: list[str]) -> dict[str, str] | None:
    patterns = (
        ("index", r"index [0-9a-f]+\.\.[0-9a-f]+(?: [0-7]{6})?"),
        ("old-mode", r"old mode [0-7]{6}"),
        ("new-mode", r"new mode [0-7]{6}"),
        ("new-file", r"new file mode [0-7]{6}"),
        ("deleted-file", r"deleted file mode [0-7]{6}"),
        ("similarity", r"similarity index [0-9]+%"),
        ("dissimilarity", r"dissimilarity index [0-9]+%"),
        ("rename-from", r"rename from (.+)"),
        ("rename-to", r"rename to (.+)"),
        ("copy-from", r"copy from (.+)"),
        ("copy-to", r"copy to (.+)"),
    )
    values: dict[str, str] = {}
    for line in lines:
        matched = False
        for key, pattern in patterns:
            match = re.fullmatch(pattern, line)
            if match is None:
                continue
            if key in values:
                return None
            values[key] = match.group(1) if match.lastindex else line
            matched = True
            break
        if not matched:
            return None
    return values


def _diff_metadata_form(
    lines: list[str],
    before_path: str,
    after_path: str,
    content_kind: str,
) -> str | None:
    values = _diff_metadata_values(lines)
    if values is None:
        return None
    keys = set(values)
    rename_keys = {"rename-from", "rename-to"}
    copy_keys = {"copy-from", "copy-to"}
    similarity_keys = {"similarity", "dissimilarity"}
    if len(keys & similarity_keys) > 1:
        return None

    if keys & (rename_keys | copy_keys):
        if keys & rename_keys and keys & copy_keys:
            return None
        form = "rename" if keys & rename_keys else "copy"
        pair = rename_keys if form == "rename" else copy_keys
        if (
            before_path == after_path
            or not pair <= keys
            or len(keys & similarity_keys) != 1
            or not keys <= pair | similarity_keys | {"index"}
            or values[f"{form}-from"] != before_path
            or values[f"{form}-to"] != after_path
            or (content_kind == "none" and "index" in keys)
        ):
            return None
        return form

    if before_path != after_path:
        return None
    if "new-file" in keys or "deleted-file" in keys:
        if (
            content_kind not in {"text", "binary"}
            or {"new-file", "deleted-file"} <= keys
        ):
            return None
        form = "new" if "new-file" in keys else "delete"
        marker = "new-file" if form == "new" else "deleted-file"
        return form if keys <= {marker, "index"} else None

    mode_keys = {"old-mode", "new-mode"}
    if keys & mode_keys and not mode_keys <= keys:
        return None
    if content_kind == "none":
        return "mode" if keys == mode_keys else None
    if content_kind not in {"text", "binary"}:
        return None
    return "normal" if keys <= {"index", *mode_keys} else None


def _valid_unified_hunks(lines: list[str]) -> bool:
    if not lines:
        return False
    header_pattern = re.compile(
        r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?"
    )
    index = 0
    while index < len(lines):
        match = header_pattern.fullmatch(lines[index])
        if match is None:
            return False
        expected_old = int(match.group(2) or 1)
        expected_new = int(match.group(4) or 1)
        old_count = 0
        new_count = 0
        content_count = 0
        change_count = 0
        index += 1
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if line == r"\ No newline at end of file":
                if content_count == 0:
                    return False
            elif not line:
                return False
            elif line[0] == " ":
                old_count += 1
                new_count += 1
                content_count += 1
            elif line[0] == "-":
                old_count += 1
                content_count += 1
                change_count += 1
            elif line[0] == "+":
                new_count += 1
                content_count += 1
                change_count += 1
            else:
                return False
            index += 1
        if (
            content_count == 0
            or change_count == 0
            or old_count != expected_old
            or new_count != expected_new
        ):
            return False
    return True


def _unified_diff_paths(payload: object) -> list[str] | None:
    if not isinstance(payload, str) or not payload.strip():
        return None
    section_matches = list(re.finditer(r"^diff --git .+$", payload, flags=re.MULTILINE))
    if not section_matches or payload[: section_matches[0].start()].strip():
        return None
    changed_paths: list[str] = []
    for section_index, match in enumerate(section_matches):
        end = (
            section_matches[section_index + 1].start()
            if section_index + 1 < len(section_matches)
            else len(payload)
        )
        section_lines = payload[match.start() : end].splitlines()
        header_paths = _git_diff_header_paths(section_lines[0])
        if header_paths is None or len(section_lines) == 1:
            return None
        before_path, after_path = header_paths
        body = section_lines[1:]
        hunk_indexes = [index for index, line in enumerate(body) if line.startswith("@@")]
        first_hunk = hunk_indexes[0] if hunk_indexes else len(body)
        file_header_region = body[:first_hunk]
        old_headers = [
            index
            for index, line in enumerate(file_header_region)
            if line.startswith("--- ")
        ]
        new_headers = [
            index
            for index, line in enumerate(file_header_region)
            if line.startswith("+++ ")
        ]
        binary_lines = [line for line in body if line.startswith("Binary files ")]
        if old_headers or new_headers or hunk_indexes:
            if (
                len(old_headers) != 1
                or len(new_headers) != 1
                or new_headers[0] != old_headers[0] + 1
                or not hunk_indexes
                or hunk_indexes[0] != new_headers[0] + 1
                or binary_lines
            ):
                return None
            form = _diff_metadata_form(
                body[: old_headers[0]], before_path, after_path, "text"
            )
            if form not in {"normal", "new", "delete", "rename", "copy"}:
                return None
            expected_old = "/dev/null" if form == "new" else f"a/{before_path}"
            expected_new = "/dev/null" if form == "delete" else f"b/{after_path}"
            if (
                body[old_headers[0]] != f"--- {expected_old}"
                or body[new_headers[0]] != f"+++ {expected_new}"
                or not _valid_unified_hunks(body[hunk_indexes[0] :])
            ):
                return None
        else:
            if binary_lines:
                if len(binary_lines) != 1:
                    return None
                marker_index = body.index(binary_lines[0])
                form = _diff_metadata_form(
                    body[:marker_index], before_path, after_path, "binary"
                )
                if form not in {"normal", "new", "delete", "rename", "copy"}:
                    return None
                expected_old = "/dev/null" if form == "new" else f"a/{before_path}"
                expected_new = "/dev/null" if form == "delete" else f"b/{after_path}"
                marker = f"Binary files {expected_old} and {expected_new} differ"
                if (
                    binary_lines[0] != marker
                    or marker_index != len(body) - 1
                ):
                    return None
            else:
                form = _diff_metadata_form(
                    body, before_path, after_path, "none"
                )
                if form not in {"rename", "copy", "mode"}:
                    return None
        changed_paths.append(before_path if form == "delete" else after_path)
    return changed_paths


def _native_change_reference_bound(
    artifact: object,
    changed_paths: object,
    current_generation: object,
    assigned_reviewer: str,
) -> bool:
    return (
        isinstance(artifact, dict)
        and tuple(artifact) == NATIVE_CHANGE_REFERENCE_FIELDS
        and isinstance(artifact.get("reference"), str)
        and re.fullmatch(
            r"native-change://[a-z0-9][a-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*",
            artifact["reference"],
        )
        is not None
        and artifact.get("generation") == current_generation
        and artifact.get("reviewer") == assigned_reviewer
        and artifact.get("changed_paths") == changed_paths
        and artifact.get("readable") is True
    )


def _exact_change_evidence_accessible(
    kind: object,
    artifact: object,
    changed_paths: object,
    capabilities: object,
    *,
    current_generation: object = None,
    assigned_reviewer: str = "review-agent",
) -> bool:
    if not isinstance(capabilities, dict):
        return False
    if capabilities.get("reviewer-change-consume") != "supported":
        return False
    if kind == "reviewer-accessible-native-reference":
        return (
            capabilities.get("native-change-read") == "supported"
            and _native_change_reference_bound(
                artifact,
                changed_paths,
                current_generation,
                assigned_reviewer,
            )
        )
    return (
        kind in REVIEW_INPUT_EXACT_EVIDENCE_KINDS
        and capabilities.get("change-evidence-export") == "supported"
        and capabilities.get("supplied-change-delivery") == "supported"
        and _unified_diff_paths(artifact) == changed_paths
    )


ANALYZED_TRAJECTORY_INITIAL_FIELDS = (
    "actor",
    "action",
    "analysis_kind",
    "brief_id",
    "brief_status",
    "target_authority",
    "acceptance",
    "owner_placement_invariant",
    "verification",
    "downstream_task",
    "review_projection",
)
ANALYZED_TRAJECTORY_DELTA_FIELDS = (
    "actor",
    "action",
    "analysis_kind",
    "accepted_brief_id",
    "protected_decision_invalidated",
    "invalidated_decisions",
    "reroute_trigger",
    "downstream_task",
    "review_projection",
)


def _analyzed_trajectory_authority_errors(
    case_id: str,
    case_kind: object,
    steps: list[dict[str, Any]],
) -> list[str]:
    if case_kind != "analyzed":
        return []
    errors: list[str] = []

    def reject(code: str, message: str) -> None:
        errors.append(f"{case_id}: [{code}] {message}")

    analysis_dispatch_entries = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "main-control-agent"
        and step.get("action") == "dispatch"
        and step.get("profile") == "analysis-agent"
    ]
    task_dispatch_entries = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "main-control-agent"
        and step.get("action") == "dispatch"
        and step.get("profile") == "task-agent"
        and step.get("mode") != "diff-export/no-edit"
    ]
    review_dispatch_entries = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "main-control-agent"
        and step.get("action") == "dispatch"
        and step.get("profile") == "review-agent"
    ]
    if len(analysis_dispatch_entries) != 1:
        reject(
            "analysis-mode",
            "analyzed trajectory requires exactly one Analysis dispatch mode",
        )
        return errors
    analysis_mode = analysis_dispatch_entries[0][1].get("mode")
    read_only_modes = {"diagnosis-only", "source-backed-answer"}
    if (
        analysis_mode in read_only_modes
        and not task_dispatch_entries
        and not review_dispatch_entries
    ):
        # These two modes produce read-only Analysis output, not an
        # implementation Brief, Task, or Review boundary.
        return []
    if analysis_mode != "implementation-preparation":
        reject(
            "analysis-mode",
            "only implementation-preparation may create a downstream Task or Review boundary",
        )
        return errors

    initial_entries = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "analysis-agent"
        and step.get("action") == "first_executable_slice"
    ]
    if len(initial_entries) != 1:
        reject(
            "analysis-initial-kind",
            "analyzed trajectory requires exactly one first initial Analysis event",
        )
        return errors
    initial_index, initial = initial_entries[0]
    if analysis_dispatch_entries[0][0] >= initial_index:
        reject(
            "analysis-initial-order",
            "the unique implementation-preparation dispatch must precede its initial Analysis event",
        )
    if initial.get("analysis_kind") != "initial":
        reject(
            "analysis-initial-kind",
            "the first Analysis event must declare analysis_kind initial",
        )
    if tuple(initial) != ANALYZED_TRAJECTORY_INITIAL_FIELDS:
        reject(
            "analysis-initial-shape",
            "initial Analysis must carry the complete accepted Brief projection",
        )

    brief_id = initial.get("brief_id")
    target = initial.get("target_authority")
    acceptance = initial.get("acceptance")
    owner = initial.get("owner_placement_invariant")
    verification = initial.get("verification")
    target_valid = (
        isinstance(target, dict)
        and tuple(target)
        == (
            "desired_behavior",
            "observable_acceptance",
            "observed_behavior",
            "observed_behavior_role",
        )
        and isinstance(target.get("desired_behavior"), str)
        and bool(target["desired_behavior"].strip())
        and isinstance(target.get("observable_acceptance"), list)
        and bool(target["observable_acceptance"])
        and all(
            isinstance(item, str) and bool(item.strip())
            for item in target["observable_acceptance"]
        )
        and isinstance(target.get("observed_behavior"), str)
        and bool(target["observed_behavior"].strip())
        and target.get("observed_behavior_role") == "failure-evidence-only"
        and target.get("desired_behavior") != target.get("observed_behavior")
        and target.get("observed_behavior")
        not in target.get("observable_acceptance", [])
    )
    if not target_valid:
        reject(
            "analysis-target-authority",
            "desired behavior and observable Acceptance must outrank observed failure evidence",
        )
    if (
        not isinstance(brief_id, str)
        or not brief_id
        or initial.get("brief_status") != "accepted"
    ):
        reject(
            "analysis-brief-acceptance",
            "initial Analysis must bind one accepted Engineering Brief",
        )
    if (
        not isinstance(acceptance, list)
        or not acceptance
        or not all(isinstance(item, str) and item.strip() for item in acceptance)
        or not isinstance(owner, dict)
        or tuple(owner) != ("owner", "placement", "invariant")
        or not all(isinstance(value, str) and value.strip() for value in owner.values())
        or not isinstance(verification, list)
        or not verification
        or not all(isinstance(item, str) and item.strip() for item in verification)
    ):
        reject(
            "analysis-initial-shape",
            "initial Analysis must close Acceptance, Owner/Placement/Invariant, and verification",
        )

    projected_task = initial.get("downstream_task")
    projected_review = initial.get("review_projection")

    def projections_valid(task: object, review: object) -> bool:
        return (
            isinstance(task, dict)
            and tuple(task) == ("task_id", "professional_skill", "layer3_skills")
            and isinstance(task.get("task_id"), str)
            and bool(task["task_id"].strip())
            and isinstance(task.get("professional_skill"), str)
            and bool(task["professional_skill"].strip())
            and isinstance(task.get("layer3_skills"), list)
            and all(isinstance(item, str) and item for item in task["layer3_skills"])
            and len(task["layer3_skills"]) == len(set(task["layer3_skills"]))
            and isinstance(review, dict)
            and tuple(review) == ("profile", "professional_skill", "layer3_skills")
            and review.get("profile") == "review-agent"
            and isinstance(review.get("professional_skill"), str)
            and bool(review["professional_skill"].strip())
            and isinstance(review.get("layer3_skills"), list)
            and all(isinstance(item, str) and item for item in review["layer3_skills"])
            and len(review["layer3_skills"]) == len(set(review["layer3_skills"]))
        )

    if not projections_valid(projected_task, projected_review):
        reject(
            "analysis-task-projection",
            "initial Analysis must freeze complete downstream Task and Review projections",
        )
    allowed_invalidations = set(
        CORE_CONTRACTS["task_contract"]["analyzed_work_authority"][
            "decision_invalidation_triggers"
        ]
    )
    allowed_reroutes = {
        "none",
        *CORE_CONTRACTS["task_contract"]["analyzed_work_authority"][
            "delta_analysis"
        ]["skill_reroute_triggers"],
    }
    delta_entries = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "analysis-agent" and step.get("action") == "brief"
    ]
    for delta_index, delta in delta_entries:
        if (
            delta_index <= initial_index
            or initial.get("brief_status") != "accepted"
            or delta.get("accepted_brief_id") != brief_id
        ):
            reject(
                "analysis-delta-acceptance",
                "Delta requires the already accepted initial Brief binding",
            )
        if tuple(delta) != ANALYZED_TRAJECTORY_DELTA_FIELDS:
            reject(
                "analysis-delta-shape",
                "Delta must use the complete protected-decision projection",
            )
        invalidated = delta.get("invalidated_decisions")
        if (
            delta.get("analysis_kind") != "delta"
            or delta.get("protected_decision_invalidated") is not True
            or not isinstance(invalidated, list)
            or not invalidated
            or not set(invalidated) <= allowed_invalidations
            or delta.get("reroute_trigger") not in allowed_reroutes
        ):
            reject(
                "analysis-delta-invalidation",
                "Delta requires a named protected-decision invalidation",
            )
        if delta.get("reroute_trigger") == "none" and (
            delta.get("downstream_task") != projected_task
            or delta.get("review_projection") != projected_review
        ):
            reject(
                "analysis-delta-routing",
                "Delta cannot self-reroute Task or Review without a named reroute trigger",
            )
        projected_task = delta.get("downstream_task")
        projected_review = delta.get("review_projection")
        if not projections_valid(projected_task, projected_review):
            reject(
                "analysis-task-projection",
                "Delta must preserve complete downstream Task and Review projections",
            )

    if not task_dispatch_entries and not review_dispatch_entries:
        return errors
    if (
        len(task_dispatch_entries) != 1
        or len(review_dispatch_entries) != 1
        or task_dispatch_entries[0][0] <= initial_index
        or review_dispatch_entries[0][0] <= initial_index
    ):
        reject(
            "analysis-task-projection",
            "downstream execution requires one Task and one Review dispatch after the accepted Brief",
        )
        return errors
    task_dispatches = [step for _index, step in task_dispatch_entries]
    review_dispatches = [step for _index, step in review_dispatch_entries]

    task_dispatch = task_dispatches[0]
    task_capsule = task_dispatch.get("fixture_capsule")
    expected_task = {
        "task_id": task_capsule.get("task_id") if isinstance(task_capsule, dict) else None,
        "professional_skill": task_dispatch.get("primary_skill"),
        "layer3_skills": task_dispatch.get("layer3_skills"),
    }
    if projected_task != expected_task:
        reject(
            "analysis-task-projection",
            "Main must dispatch the accepted downstream Task projection verbatim",
        )
    review_dispatch = review_dispatches[0]
    expected_review = {
        "profile": "review-agent",
        "professional_skill": review_dispatch.get("primary_skill"),
        "layer3_skills": review_dispatch.get("layer3_skills"),
    }
    if projected_review != expected_review:
        reject(
            "analysis-review-projection",
            "Main must preserve the accepted Review projection",
        )
    return errors


def _canonical_ledger_shape_errors(ledger: object, *, context: str) -> list[str]:
    if not isinstance(ledger, list):
        return []
    errors: list[str] = []
    retired = set(RETIRED_EVIDENCE_LEDGER_FIELDS)
    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            continue
        reintroduced = [
            field for field in RETIRED_EVIDENCE_LEDGER_FIELDS if field in row
        ]
        if reintroduced:
            label = "field" if len(reintroduced) == 1 else "fields"
            errors.append(
                f"{context} Evidence Ledger row {index} reintroduces retired "
                f"Evidence Ledger {label}: {reintroduced}"
            )
        if tuple(row) != CANONICAL_EVIDENCE_LEDGER_FIELDS:
            errors.append(
                f"{context} Evidence Ledger row {index} must use exact ordered fields "
                f"{list(CANONICAL_EVIDENCE_LEDGER_FIELDS)}"
            )
        elif retired.intersection(row):
            raise AssertionError("retired fields cannot be canonical")
    return errors


def _completion_evidence_binding_errors(ledger: object) -> list[str]:
    if not isinstance(ledger, list):
        return []
    errors: list[str] = []
    for index, row in enumerate(ledger):
        if not isinstance(row, dict) or tuple(row) != CANONICAL_EVIDENCE_LEDGER_FIELDS:
            continue
        scope = row.get("Scope")
        artifact = row.get("Artifact")
        proof_limit = row.get("Proof Limit")
        if not all(isinstance(value, str) for value in (scope, artifact, proof_limit)):
            continue
        scope_paths = set(EVIDENCE_PATH_RE.findall(scope))
        artifact_paths = set(EVIDENCE_PATH_RE.findall(artifact))
        if scope_paths and not artifact_paths.issubset(scope_paths):
            errors.append(
                f"Evidence Ledger row {index} evidence Scope mismatch: artifact paths "
                f"{sorted(artifact_paths)} are not all inside Scope paths "
                f"{sorted(scope_paths)}"
            )
        proof_paths = set(EVIDENCE_PATH_RE.findall(proof_limit))
        if scope_paths and not proof_paths.issubset(scope_paths):
            errors.append(
                f"Evidence Ledger row {index} evidence Proof Limit mismatch: bounded "
                f"paths {sorted(proof_paths)} are not all inside Scope paths "
                f"{sorted(scope_paths)}"
            )
    return errors


def completion_claim_errors(
    claim: object,
    *,
    review_authority: object = None,
) -> list[str]:
    """Apply evaluator-only public-ledger shape and binding gates."""

    ledger = claim.get("evidence_ledger") if isinstance(claim, dict) else None
    errors = _canonical_ledger_shape_errors(ledger, context="completion claim")
    errors.extend(_completion_evidence_binding_errors(ledger))
    errors.extend(
        _core_completion_claim_errors(
            claim,
            review_authority=review_authority,
        )
    )
    return list(dict.fromkeys(errors))
PROGRESS_TO_PRODUCTIVE_RATIO_MAX = 0.75
MULTI_AGENT_PROGRESS_MIN = 3
MULTI_AGENT_PROGRESS_MAX = 5
MAX_SILENT_STRUCTURAL_STEPS = 5
GENERIC_PROGRESS_EVIDENCE = {
    "a",
    "b",
    "c",
    "d",
    "done",
    "ok",
    "progress",
    "status",
    "working",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _first_index(steps: list[dict[str, Any]], actions: set[str]) -> int | None:
    for index, step in enumerate(steps):
        if str(step.get("action") or "") in actions:
            return index
    return None


def _duplicate_reads(steps: list[dict[str, Any]]) -> int:
    seen: set[tuple[str, str]] = set()
    duplicate = 0
    for step in steps:
        action = str(step.get("action") or "")
        if action not in {"read", "search"}:
            continue
        target = str(step.get("path") or step.get("query") or "").strip()
        if not target:
            continue
        key = (action, target)
        if key in seen:
            duplicate += 1
        seen.add(key)
    return duplicate


def _loaded_skill_count(steps: list[dict[str, Any]]) -> int:
    count = 0
    for step in steps:
        if step.get("action") != "dispatch":
            continue
        if str(step.get("primary_skill") or "").strip():
            count += 1
        layer3 = step.get("layer3_skills")
        if isinstance(layer3, list):
            count += len([item for item in layer3 if str(item).strip()])
    return count


def _loaded_layer3_reference_count(steps: list[dict[str, Any]]) -> int:
    return sum(
        len(step.get("layer3_references", []))
        for step in steps
        if step.get("action") == "dispatch"
        and isinstance(step.get("layer3_references"), list)
    )


def _scope_prefix(scope: str) -> str:
    return scope.removesuffix("/**").removesuffix("/*").rstrip("/")


def _parallel_metrics(steps: list[dict[str, Any]]) -> tuple[bool, int]:
    batches: dict[str, list[dict[str, Any]]] = {}
    for step in steps:
        batch = step.get("parallel_batch")
        if step.get("action") == "dispatch" and isinstance(batch, str) and batch:
            batches.setdefault(batch, []).append(step)

    conflict = False
    reduction = 0
    for dispatches in batches.values():
        if len(dispatches) < 2:
            continue
        reduction += len(dispatches) - 1
        workspaces = [str(step.get("workspace") or "") for step in dispatches]
        if (
            len(workspaces) != len(set(workspaces))
            or any(not workspace for workspace in workspaces)
            or any(step.get("workspace_isolation") != "host-provided" for step in dispatches)
        ):
            conflict = True
        scopes: list[str] = []
        for step in dispatches:
            values = step.get("write_scope")
            if not isinstance(values, list) or not values:
                conflict = True
                continue
            prefixes = [_scope_prefix(str(value)) for value in values if str(value).strip()]
            for prefix in prefixes:
                for existing in scopes:
                    if prefix == existing or prefix.startswith(existing + "/") or existing.startswith(prefix + "/"):
                        conflict = True
                scopes.append(prefix)
    return conflict, reduction


def _shared_workspace_writes_serial(steps: list[dict[str, Any]]) -> bool:
    dispatches = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("action") == "dispatch"
        and step.get("profile") == "task-agent"
        and step.get("workspace") == "shared"
        and isinstance(step.get("write_scope"), list)
        and step.get("write_scope")
    ]
    if len(dispatches) < 2:
        return False
    for (current_index, current), (next_index, _next) in zip(
        dispatches, dispatches[1:]
    ):
        if current.get("parallel_batch") is not None:
            return False
        between = steps[current_index + 1 : next_index]
        task_id = current.get("task_id")
        if not any(
            step.get("actor") == "task-agent"
            and step.get("task_id") == task_id
            and step.get("action") in EDIT_ACTIONS
            for step in between
        ):
            return False
        if not any(
            step.get("actor") == "task-agent"
            and step.get("task_id") == task_id
            and step.get("action") == "validate"
            for step in between
        ):
            return False
    last_index, last = dispatches[-1]
    tail = steps[last_index + 1 :]
    last_task_id = last.get("task_id")
    return (
        last.get("parallel_batch") is None
        and any(
            step.get("actor") == "task-agent"
            and step.get("task_id") == last_task_id
            and step.get("action") in EDIT_ACTIONS
            for step in tail
        )
        and any(
            step.get("actor") == "task-agent"
            and step.get("task_id") == last_task_id
            and step.get("action") == "validate"
            for step in tail
        )
    )


def _preparation_loop(steps: list[dict[str, Any]]) -> bool:
    first_edit = _first_index(steps, EDIT_ACTIONS)
    preparation = steps if first_edit is None else steps[:first_edit]
    analysis_dispatches = [
        step
        for step in preparation
        if step.get("action") == "dispatch" and step.get("profile") == "analysis-agent"
    ]
    return len(analysis_dispatches) > 1


def _implementation_discipline_error(
    case_id: str,
    code: str,
    message: str,
) -> str:
    return f"{case_id}: [{code}] {message}"


def _evidence_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _meaningful_evidence_text(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    return value.strip().casefold() not in {
        "x",
        "ok",
        "done",
        "true",
        "verified",
        "pass",
        "passed",
        "works",
    }


def _implementation_oracle_payload(
    authority: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: authority[field]
        for field in IMPLEMENTATION_ORACLE_AUTHORITY_FIELDS
        if field != "canonical_sha256"
    }


def _implementation_oracle_digest(authority: dict[str, Any]) -> str:
    return _evidence_fingerprint(
        json.dumps(
            _implementation_oracle_payload(authority),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _implementation_oracle_authority_errors(
    case_id: str,
    authority: object,
) -> tuple[dict[str, Any] | None, list[str]]:
    code = "implementation-oracle-authority"
    if not isinstance(authority, dict) or tuple(authority) != (
        IMPLEMENTATION_ORACLE_AUTHORITY_FIELDS
    ):
        return None, [
            _implementation_discipline_error(
                case_id,
                code,
                "case-local oracle authority must use the exact typed immutable shape",
            )
        ]
    text_fields = (
        "task_id",
        "acceptance_id",
        "mechanism_id",
        "failure_mechanism",
        "oracle_id",
        "oracle",
    )
    validation = authority.get("validation_binding")
    source_bindings = authority.get("source_bindings")
    placement = authority.get("placement_binding")
    scan = authority.get("same_pattern_binding")
    valid = (
        authority.get("schema_version") == 1
        and all(_meaningful_evidence_text(authority.get(field)) for field in text_fields)
        and str(authority.get("acceptance_id", "")).startswith("acceptance.")
        and isinstance(authority.get("assertion_fingerprint"), str)
        and re.fullmatch(r"[0-9a-f]{64}", authority["assertion_fingerprint"])
        is not None
        and isinstance(validation, dict)
        and tuple(validation) == IMPLEMENTATION_ORACLE_VALIDATION_FIELDS
        and all(_meaningful_evidence_text(value) for value in validation.values())
        and isinstance(source_bindings, list)
        and source_bindings
        and all(
            isinstance(binding, dict)
            and tuple(binding) == IMPLEMENTATION_ORACLE_SOURCE_FIELDS
            and all(_meaningful_evidence_text(value) for value in binding.values())
            and binding.get("read_kind") in IMPLEMENTATION_SOURCE_READ_KINDS
            for binding in source_bindings
        )
        and len(
            {
                binding["evidence_id"]
                for binding in source_bindings
                if isinstance(binding, dict) and "evidence_id" in binding
            }
        )
        == len(source_bindings)
        and isinstance(placement, dict)
        and tuple(placement) == IMPLEMENTATION_ORACLE_PLACEMENT_FIELDS
        and all(_meaningful_evidence_text(value) for value in placement.values())
        and isinstance(scan, dict)
        and tuple(scan) == IMPLEMENTATION_ORACLE_SCAN_FIELDS
        and _meaningful_evidence_text(scan.get("pattern_id"))
        and isinstance(scan.get("scope"), list)
        and scan["scope"]
        and all(_meaningful_evidence_text(item) for item in scan["scope"])
        and all(
            _meaningful_evidence_text(scan.get(field))
            for field in ("evidence_id", "artifact_id", "source_anchor")
        )
        and scan.get("proof_kind") == "fixture-structured-zero"
    )
    expected_digest = _implementation_oracle_digest(authority)
    valid = (
        valid
        and isinstance(authority.get("canonical_sha256"), str)
        and authority["canonical_sha256"] == expected_digest
    )
    if not valid:
        return None, [
            _implementation_discipline_error(
                case_id,
                code,
                "case-local oracle authority is malformed, generic, or not bound to its immutable digest",
            )
        ]
    expected_contract = IMPLEMENTATION_ORACLE_CONTRACTS.get(case_id)
    if (
        expected_contract is None
        or authority["task_id"] != expected_contract["task_id"]
        or authority["acceptance_id"] != expected_contract["acceptance_id"]
        or authority["canonical_sha256"]
        != expected_contract["canonical_sha256"]
    ):
        return authority, [
            _implementation_discipline_error(
                case_id,
                code,
                "case-local oracle authority must match the evaluator-owned task, acceptance, and canonical digest",
            )
        ]
    return authority, []


def _implementation_oracle_binding_errors(
    case_id: str,
    authority: dict[str, Any],
    by_guard: dict[str, dict[str, Any]],
    steps: list[dict[str, Any]],
) -> list[str]:
    code = "implementation-oracle-binding"
    task_id = authority["task_id"]
    acceptance_id = authority["acceptance_id"]
    expected: list[dict[str, Any]] = [
        {
            "purpose": "source",
            "task_id": task_id,
            "acceptance_id": acceptance_id,
            **binding,
        }
        for binding in authority["source_bindings"]
    ]
    expected.extend(
        [
            {
                "purpose": "validation",
                "task_id": task_id,
                "acceptance_id": acceptance_id,
                **authority["validation_binding"],
            },
            {
                "purpose": "scan",
                "task_id": task_id,
                "acceptance_id": acceptance_id,
                **authority["same_pattern_binding"],
            },
            {
                "purpose": "placement",
                "task_id": task_id,
                "acceptance_id": acceptance_id,
                **authority["placement_binding"],
            },
        ]
    )

    actual: list[dict[str, Any]] = []
    for step in steps:
        if step.get("actor") != "task-agent" or step.get("task_id") != task_id:
            continue
        if step.get("action") == "read":
            actual.append(
                {
                    "purpose": "source",
                    "task_id": step.get("task_id"),
                    "acceptance_id": step.get("acceptance_id"),
                    "evidence_id": step.get("evidence_id"),
                    "artifact_id": step.get("artifact_id"),
                    "path": step.get("path"),
                    "source_anchor": step.get("source_anchor"),
                    "read_kind": step.get("read_kind"),
                }
            )
        elif step.get("action") == "validate":
            actual.append(
                {
                    "purpose": "validation",
                    "task_id": step.get("task_id"),
                    "acceptance_id": step.get("acceptance_id"),
                    "evidence_id": step.get("evidence_id"),
                    "artifact_id": step.get("artifact_id"),
                    "source_anchor": step.get("source_anchor"),
                }
            )

    guard_d = by_guard.get(IMPLEMENTATION_GUARD_CODES["D"])
    scan = guard_d.get("same_pattern_scan") if guard_d is not None else None
    if isinstance(scan, dict):
        actual.append(
            {
                "purpose": "scan",
                "task_id": scan.get("task_id"),
                "acceptance_id": scan.get("acceptance_id"),
                "pattern_id": scan.get("pattern_id"),
                "scope": scan.get("scope"),
                "evidence_id": scan.get("evidence_id"),
                "artifact_id": scan.get("artifact_id"),
                "source_anchor": scan.get("source_anchor"),
                "proof_kind": scan.get("proof_kind"),
            }
        )

    guard_e = by_guard.get(IMPLEMENTATION_GUARD_CODES["E"])
    placement = (
        guard_e.get("placement_decision") if guard_e is not None else None
    )
    if isinstance(placement, dict):
        actual.append(
            {
                "purpose": "placement",
                "task_id": placement.get("task_id"),
                "acceptance_id": placement.get("acceptance_id"),
                "evidence_id": placement.get("evidence_id"),
                "artifact_id": placement.get("artifact_id"),
                "source_anchor": placement.get("source_anchor"),
            }
        )

    expected_ids = [record["evidence_id"] for record in expected]
    actual_by_id: dict[object, list[dict[str, Any]]] = {}
    for record in actual:
        evidence_id = record.get("evidence_id")
        actual_by_id.setdefault(
            evidence_id if isinstance(evidence_id, str) else None,
            [],
        ).append(record)
    valid = (
        {record["purpose"] for record in expected}
        == IMPLEMENTATION_ORACLE_BINDING_PURPOSES
        and len(expected_ids) == len(set(expected_ids))
        and set(actual_by_id) == set(expected_ids)
        and len(actual) == len(expected)
    )
    if valid:
        expected_by_id = {
            record["evidence_id"]: record for record in expected
        }
        valid = all(
            len(actual_by_id[evidence_id]) == 1
            and actual_by_id[evidence_id][0] == expected_record
            for evidence_id, expected_record in expected_by_id.items()
        )
    if valid:
        return []
    return [
        _implementation_discipline_error(
            case_id,
            code,
            "authority bindings and source, validation, scan, and placement records must form an exact typed one-use bijection",
        )
    ]


def _normal_task_dispatch_id(step: dict[str, Any]) -> str | None:
    if (
        step.get("action") != "dispatch"
        or step.get("profile") != "task-agent"
        or "utility_capsule" in step
    ):
        return None
    capsule = step.get("fixture_capsule")
    task_id = capsule.get("task_id") if isinstance(capsule, dict) else None
    return task_id if isinstance(task_id, str) and task_id.strip() else None


def _validation_bound_task_ids(
    step: dict[str, Any],
    known_task_ids: set[str] | None = None,
) -> tuple[set[str], str | None]:
    """Return one closed validation binding, rejecting ambiguous task forms."""

    has_task_id = "task_id" in step
    has_task_ids = "task_ids" in step
    if has_task_id == has_task_ids:
        return set(), "validation must use exactly one of task_id or task_ids"
    if has_task_id:
        task_id = step.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            return set(), "validation task_id must be a non-empty string"
        bound = {task_id}
    else:
        task_ids = step.get("task_ids")
        if (
            not isinstance(task_ids, list)
            or not task_ids
            or not all(isinstance(item, str) and item.strip() for item in task_ids)
        ):
            return set(), "validation task_ids must be a non-empty string list"
        if len(task_ids) != len(set(task_ids)):
            return set(), "validation task_ids must be unique"
        bound = set(task_ids)
    if known_task_ids is not None:
        unknown = sorted(bound - known_task_ids)
        if unknown:
            return set(), f"validation binds unknown task ids {unknown}"
    return bound, None


def _derived_adaptive_risk_triggers(
    event: dict[str, Any],
    dispatch: dict[str, Any] | None,
) -> set[str]:
    derived: set[str] = set()
    implementation_kind = event.get("implementation_kind")
    if isinstance(implementation_kind, str):
        derived.update(
            ADAPTIVE_TEST_DERIVED_BINDINGS["implementation_kind"].get(
                implementation_kind,
                [],
            )
        )
    if not isinstance(dispatch, dict):
        return derived
    primary = dispatch.get("primary_skill")
    if isinstance(primary, str):
        derived.update(
            ADAPTIVE_TEST_DERIVED_BINDINGS["primary_skill"].get(primary, [])
        )
    layer3 = dispatch.get("layer3_skills")
    if isinstance(layer3, list):
        for skill in layer3:
            if isinstance(skill, str):
                derived.update(
                    ADAPTIVE_TEST_DERIVED_BINDINGS["layer3_skill"].get(skill, [])
                )
    risk_categories = dispatch.get("risk_categories")
    if isinstance(risk_categories, list):
        for category in risk_categories:
            if isinstance(category, str):
                derived.update(
                    ADAPTIVE_TEST_DERIVED_BINDINGS["task_risk_category"].get(
                        category,
                        [],
                    )
                )
    return derived


def _adaptive_test_guard_errors(
    case_id: str,
    guard: dict[str, Any],
    event_index: int,
    dispatch_index: int | None,
    first_edit_index: int | None,
    final_edit_index: int | None,
    steps: list[dict[str, Any]],
    task_id: object,
    derived_risk_triggers: set[str],
    oracle_authority: dict[str, Any] | None = None,
) -> list[str]:
    code = IMPLEMENTATION_GUARD_CODES["G"]
    errors: list[str] = []

    def reject(message: str) -> None:
        errors.append(_implementation_discipline_error(case_id, code, message))

    approach = guard.get("approach")
    change_kind = guard.get("change_kind")
    risk_triggers = guard.get("risk_triggers")
    evidence_ids = guard.get("evidence")
    required_text = ("reason", "failure_mechanism", "boundary", "oracle", "proof_boundary")
    if (
        change_kind not in {"behavior", "non-behavior"}
        or approach not in ADAPTIVE_TEST_APPROACHES
        or any(
            not isinstance(guard.get(field), str) or not guard[field].strip()
            for field in required_text
        )
        or not isinstance(risk_triggers, list)
        or not risk_triggers
        or not all(isinstance(item, str) and item.strip() for item in risk_triggers)
        or len(risk_triggers) != len(set(risk_triggers))
        or not isinstance(evidence_ids, list)
        or not evidence_ids
        or not all(isinstance(item, str) and item.strip() for item in evidence_ids)
        or len(evidence_ids) != len(set(evidence_ids))
    ):
        reject("adaptive choice must record one approach, reason, mechanism, boundary, oracle, unique qualifiers and evidence, and proof boundary")
        return errors

    typed_records = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "task-agent"
        and step.get("action") == ADAPTIVE_TEST_EVIDENCE_ACTION
        and step.get("task_id") == task_id
    ]
    for index, record in typed_records:
        expected_fields = (
            ADAPTIVE_TEST_ANCHORED_EVIDENCE_FIELDS
            if oracle_authority is not None
            else ADAPTIVE_TEST_EVIDENCE_FIELDS
        )
        if tuple(record) != expected_fields:
            reject(f"adaptive evidence at step {index} must use exact ordered fields")
    by_id = {
        record.get("evidence_id"): (index, record)
        for index, record in typed_records
        if isinstance(record.get("evidence_id"), str)
    }
    if len(by_id) != len(typed_records) or set(by_id) != set(evidence_ids):
        reject("adaptive evidence ids must bind exactly the task's unique typed evidence records")
        return errors
    records = [by_id[evidence_id] for evidence_id in evidence_ids]
    if dispatch_index is None or first_edit_index is None or final_edit_index is None:
        reject("adaptive evidence requires a bound dispatch and edit")
        return errors

    reported_risk_triggers = set(risk_triggers)
    missing_derived = derived_risk_triggers - reported_risk_triggers
    if missing_derived:
        reject(
            "derived high-risk triggers are missing or contradicted by the Guard G "
            f"record: {sorted(missing_derived)}"
        )
    high_risk = bool(
        reported_risk_triggers & ADAPTIVE_TEST_HIGH_RISK_TRIGGERS
        or derived_risk_triggers
    )
    if high_risk and approach != "test-first":
        reject("high-risk behavior cannot be downgraded from test-first")

    if oracle_authority is not None:
        validation_binding = oracle_authority["validation_binding"]
        anchored = all(
            record.get("task_id") == oracle_authority["task_id"]
            and record.get("acceptance_id") == oracle_authority["acceptance_id"]
            and record.get("artifact_id") == validation_binding["artifact_id"]
            and record.get("source_anchor") == validation_binding["source_anchor"]
            and record.get("oracle_id") == oracle_authority["oracle_id"]
            and record.get("mechanism_id") == oracle_authority["mechanism_id"]
            and record.get("assertion_fingerprint")
            == oracle_authority["assertion_fingerprint"]
            and isinstance(record.get("assertion"), str)
            and _evidence_fingerprint(record["assertion"])
            == oracle_authority["assertion_fingerprint"]
            for _index, record in records
        )
        if (
            task_id != oracle_authority["task_id"]
            or guard.get("failure_mechanism")
            != oracle_authority["failure_mechanism"]
            or guard.get("oracle") != oracle_authority["oracle"]
            or not anchored
        ):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-oracle-authority",
                    "adaptive evidence must match the case-local acceptance, mechanism, oracle identity, assertion fingerprint, artifact, and source anchor",
                )
            )

    if approach == "test-first":
        valid = (
            change_kind == "behavior"
            and len(records) == 2
            and [record.get("evidence_kind") for _index, record in records]
            == ["red", "green"]
        )
        if valid:
            (red_index, red), (green_index, green) = records
            valid = (
                dispatch_index < red_index < event_index < first_edit_index
                and final_edit_index < green_index
                and red.get("result") == "failed"
                and red.get("failure_class") == "target-behavior-missing"
                and green.get("result") == "passed"
                and green.get("failure_class") == "none"
                and red.get("oracle") == guard.get("oracle") == green.get("oracle")
                and isinstance(red.get("assertion"), str)
                and bool(red["assertion"].strip())
                and red.get("assertion") == green.get("assertion")
                and isinstance(red.get("freshness"), int)
                and isinstance(green.get("freshness"), int)
                and red["freshness"] < green["freshness"]
            )
        if not valid:
            reject("test-first requires a target-behavior Red before the edit and unchanged-oracle unchanged-assertion Green after it")
    elif approach == "test-after":
        qualifier_set = set(risk_triggers)
        valid = (
            change_kind == "behavior"
            and not high_risk
            and bool(qualifier_set)
            and qualifier_set <= ADAPTIVE_TEST_AFTER_QUALIFIERS
            and len(records) == 1
        )
        if valid:
            green_index, green = records[0]
            valid = (
                final_edit_index < green_index
                and green.get("evidence_kind") == "green"
                and green.get("result") == "passed"
                and green.get("failure_class") == "none"
                and green.get("oracle") == guard.get("oracle")
                and isinstance(green.get("assertion"), str)
                and bool(green["assertion"].strip())
            )
        if not valid:
            reject("test-after is limited to low-risk local exploration or behavior with existing primary coverage and requires post-edit Green")
    elif approach == "existing-proof-only":
        qualifier_set = set(risk_triggers)
        valid = (
            change_kind == "behavior"
            and not high_risk
            and ADAPTIVE_EXISTING_PROOF_QUALIFIERS <= qualifier_set
            and len(records) == 1
        )
        if valid:
            proof_index, proof = records[0]
            valid = (
                final_edit_index < proof_index
                and proof.get("evidence_kind") == "existing-proof"
                and proof.get("result") == "passed"
                and proof.get("failure_class") == "target-mechanism-covered"
                and proof.get("oracle") == guard.get("oracle")
                and isinstance(proof.get("assertion"), str)
                and bool(proof["assertion"].strip())
                and isinstance(proof.get("freshness"), int)
                and proof["freshness"] > 0
            )
        if not valid:
            reject("existing-proof-only requires existing regression-mechanism coverage, no new uncovered behavior, and a fresh post-edit rerun")
    else:
        qualifier_set = set(risk_triggers)
        valid = (
            change_kind == "non-behavior"
            and bool(qualifier_set)
            and qualifier_set <= ADAPTIVE_NON_TEST_QUALIFIERS
            and len(records) == 1
        )
        if valid:
            proof_index, proof = records[0]
            valid = (
                final_edit_index < proof_index
                and proof.get("evidence_kind") == "non-test"
                and proof.get("result") == "passed"
                and proof.get("failure_class") == "testing-not-applicable"
                and proof.get("oracle") == guard.get("oracle")
                and proof.get("assertion") == "not-applicable"
                and isinstance(proof.get("freshness"), int)
                and proof["freshness"] > 0
            )
        if not valid:
            reject("non-test-validation is limited to named non-behavior edits with an explicit post-edit oracle and no fabricated Red or Green")
    return errors


def _implementation_guard_errors(
    case_id: str,
    event: dict[str, Any],
    event_index: int,
    dispatch_index: int | None,
    first_edit_index: int | None,
    final_edit_index: int | None,
    steps: list[dict[str, Any]],
    derived_risk_triggers: set[str],
    oracle_authority: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    evidence = event.get("evidence")
    if not isinstance(evidence, list):
        return [
            _implementation_discipline_error(
                case_id,
                "implementation-discipline-evidence-schema",
                "implementation discipline evidence must be an ordered list",
            )
        ]

    guards = [
        item.get("guard") if isinstance(item, dict) else None for item in evidence
    ]
    expected_guards = [*IMPLEMENTATION_GUARD_ORDER, IMPLEMENTATION_GUARD_CODES["G"]]
    if guards != expected_guards:
        missing = [guard for guard in expected_guards if guard not in guards]
        duplicate = sorted(
            {
                guard
                for guard in guards
                if isinstance(guard, str) and guards.count(guard) > 1
            }
        )
        unknown = [guard for guard in guards if guard not in IMPLEMENTATION_GUARD_FIELDS]
        if missing:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-missing-evidence",
                    f"missing guard evidence {missing}",
                )
            )
        if duplicate:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-duplicate-evidence",
                    f"duplicate guard evidence {duplicate}",
                )
            )
        if unknown:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-unknown-evidence",
                    f"unknown guard evidence {unknown}",
                )
            )
        if not missing and not duplicate and not unknown:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-evidence-order",
                    "guard evidence must use canonical A-F order",
                )
            )

    by_guard: dict[str, dict[str, Any]] = {}
    for item in evidence:
        if not isinstance(item, dict):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-evidence-schema",
                    "each guard evidence item must be a mapping",
                )
            )
            continue
        guard = item.get("guard")
        if not isinstance(guard, str) or guard not in IMPLEMENTATION_GUARD_FIELDS:
            continue
        expected_fields = IMPLEMENTATION_GUARD_FIELDS[guard]
        allowed_fields = {expected_fields}
        enhanced_fields = IMPLEMENTATION_GUARD_ENHANCED_FIELDS.get(guard)
        if enhanced_fields is not None:
            allowed_fields.add(enhanced_fields)
        anchored_fields = IMPLEMENTATION_GUARD_ANCHORED_FIELDS.get(guard)
        if anchored_fields is not None:
            allowed_fields.add(anchored_fields)
        if tuple(item) not in allowed_fields:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    guard,
                    "guard fields must use the canonical base or source-bound "
                    "enhanced shape in order",
                )
            )
        by_guard.setdefault(guard, item)

    task_id = event.get("task_id")
    source_reads = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "task-agent"
        and step.get("action") == "read"
        and step.get("task_id") == task_id
        and step.get("read_kind") in IMPLEMENTATION_SOURCE_READ_KINDS
    ]
    source_reads_by_id = {
        step.get("evidence_id"): (index, step)
        for index, step in source_reads
        if isinstance(step.get("evidence_id"), str)
    }
    source_bound = any(
        tuple(item) == IMPLEMENTATION_GUARD_ENHANCED_FIELDS.get(guard)
        for guard, item in by_guard.items()
    )
    if oracle_authority is not None:
        errors.extend(
            _implementation_oracle_binding_errors(
                case_id,
                oracle_authority,
                by_guard,
                steps,
            )
        )

    guard_a = by_guard.get(IMPLEMENTATION_GUARD_CODES["A"])
    if guard_a is not None:
        read_evidence = guard_a.get("read_evidence")
        if (
            not isinstance(read_evidence, list)
            or len(read_evidence) != len(IMPLEMENTATION_READ_KINDS)
            or not all(isinstance(item, str) and item.strip() for item in read_evidence)
            or len(read_evidence) != len(set(read_evidence))
        ):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["A"],
                    "read evidence must contain three distinct non-empty ids",
                )
            )
        typed_reads = [
            (index, step)
            for index, step in source_reads
            if step.get("read_kind") in IMPLEMENTATION_READ_KINDS
        ]
        for index, step in source_reads:
            if oracle_authority is not None:
                expected_read_fields = (
                    IMPLEMENTATION_ANCHORED_TEST_READ_FIELDS
                    if step.get("read_kind") == "relevant-existing-tests"
                    else IMPLEMENTATION_ANCHORED_READ_FIELDS
                )
            else:
                expected_read_fields = (
                    IMPLEMENTATION_TEST_READ_FIELDS
                    if step.get("read_kind") == "relevant-existing-tests"
                    and "compatibility_anchor" in step
                    else IMPLEMENTATION_READ_FIELDS
                )
            if tuple(step) != expected_read_fields:
                errors.append(
                    _implementation_discipline_error(
                        case_id,
                        IMPLEMENTATION_GUARD_CODES["A"],
                        f"typed implementation read at step {index} must use exact fields",
                    )
                )
        read_kinds = [step.get("read_kind") for _index, step in typed_reads]
        evidence_ids = [step.get("evidence_id") for _index, step in typed_reads]
        if read_kinds != list(IMPLEMENTATION_READ_KINDS):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["A"],
                    "actual task-agent reads must cover owner, tests, and minimum caller in order",
                )
            )
        if isinstance(read_evidence, list) and evidence_ids != read_evidence:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["A"],
                    "read evidence ids must bind the actual ordered task-agent reads",
                )
            )
        read_indexes = [index for index, _step in typed_reads]
        if (
            dispatch_index is None
            or first_edit_index is None
            or len(read_indexes) != len(IMPLEMENTATION_READ_KINDS)
            or not all(
                dispatch_index < index < event_index < first_edit_index
                for index in read_indexes
            )
        ):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["A"],
                    "typed reads must follow dispatch and precede discipline and first edit",
                )
            )
        if oracle_authority is not None:
            source_authority = {
                binding["evidence_id"]: binding
                for binding in oracle_authority["source_bindings"]
            }
            for _index, step in source_reads:
                binding = source_authority.get(step.get("evidence_id"))
                if (
                    binding is None
                    or step.get("task_id") != oracle_authority["task_id"]
                    or step.get("acceptance_id")
                    != oracle_authority["acceptance_id"]
                    or any(
                        step.get(field) != binding[field]
                        for field in (
                            "evidence_id",
                            "artifact_id",
                            "path",
                            "source_anchor",
                            "read_kind",
                        )
                    )
                ):
                    errors.append(
                        _implementation_discipline_error(
                            case_id,
                            "implementation-oracle-authority",
                            "typed source evidence must match the case-local task, acceptance, artifact, evidence id, path, and source anchor",
                        )
                    )
        if source_bound:
            test_reads = [
                step
                for _index, step in typed_reads
                if step.get("read_kind") == "relevant-existing-tests"
            ]
            if (
                len(test_reads) != 1
                or tuple(test_reads[0])
                not in {
                    IMPLEMENTATION_TEST_READ_FIELDS,
                    IMPLEMENTATION_ANCHORED_TEST_READ_FIELDS,
                }
                or not isinstance(test_reads[0].get("compatibility_anchor"), str)
                or not test_reads[0]["compatibility_anchor"].strip()
            ):
                errors.append(
                    _implementation_discipline_error(
                        case_id,
                        IMPLEMENTATION_GUARD_CODES["A"],
                        "source-bound test read requires a non-empty compatibility anchor before edit",
                    )
                )

    guard_b = by_guard.get(IMPLEMENTATION_GUARD_CODES["B"])
    if guard_b is not None and any(
        guard_b.get(field) is not True
        for field in IMPLEMENTATION_GUARD_FIELDS[IMPLEMENTATION_GUARD_CODES["B"]][1:]
    ):
        errors.append(
            _implementation_discipline_error(
                case_id,
                IMPLEMENTATION_GUARD_CODES["B"],
                "behavior, owner, reuse candidate, and edit boundary must be verified",
            )
        )
    if guard_b is not None and source_bound:
        owner_decision = guard_b.get("owner_decision")
        valid_owner = (
            isinstance(owner_decision, dict)
            and tuple(owner_decision)
            == (
                "owner_path",
                "owner_read_evidence",
                "nearest_candidate_path",
                "nearest_read_evidence",
                "basis",
            )
            and _meaningful_evidence_text(owner_decision.get("basis"))
            and owner_decision.get("owner_path")
            != owner_decision.get("nearest_candidate_path")
        )
        if valid_owner:
            owner_read = source_reads_by_id.get(owner_decision["owner_read_evidence"])
            nearest_read = source_reads_by_id.get(
                owner_decision["nearest_read_evidence"]
            )
            valid_owner = bool(
                owner_read
                and owner_read[1].get("read_kind") == "owning-implementation"
                and owner_read[1].get("path") == owner_decision["owner_path"]
                and nearest_read
                and nearest_read[1].get("read_kind") == "nearest-candidate"
                and nearest_read[1].get("path")
                == owner_decision["nearest_candidate_path"]
                and dispatch_index is not None
                and first_edit_index is not None
                and dispatch_index
                < owner_read[0]
                < event_index
                < first_edit_index
                and dispatch_index
                < nearest_read[0]
                < event_index
                < first_edit_index
            )
        if not valid_owner:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["B"],
                    "owner decision must bind distinct owner and nearest-candidate reads with a source basis",
                )
            )

    guard_c = by_guard.get(IMPLEMENTATION_GUARD_CODES["C"])
    if guard_c is not None:
        outcome_matrix = guard_c.get("outcome_matrix")
        matrix_valid = (
            isinstance(outcome_matrix, dict)
            and tuple(outcome_matrix) == IMPLEMENTATION_OUTCOMES
            and all(
                value in IMPLEMENTATION_OUTCOME_STATES
                for value in outcome_matrix.values()
            )
            and outcome_matrix.get("normal") == "applicable"
        )
        signal = guard_c.get("validation_signal")
        if oracle_authority is not None:
            validation_binding = oracle_authority["validation_binding"]
            bound_validation = [
                (index, step)
                for index, step in enumerate(steps)
                if step.get("actor") == "task-agent"
                and step.get("action") == "validate"
                and step.get("task_id") == oracle_authority["task_id"]
                and step.get("acceptance_id")
                == oracle_authority["acceptance_id"]
                and step.get("evidence_id") == signal
                and signal == validation_binding["evidence_id"]
                and step.get("artifact_id") == validation_binding["artifact_id"]
                and step.get("source_anchor")
                == validation_binding["source_anchor"]
                and isinstance(step.get("freshness"), int)
                and step["freshness"] > 0
            ]
        else:
            bound_validation = [
                (index, step)
                for index, step in enumerate(steps)
                if step.get("actor") == "task-agent"
                and step.get("action") == "validate"
                and task_id in _validation_bound_task_ids(step)[0]
                and (
                    step.get("evidence_id") == signal
                    or step.get("command") == signal
                )
            ]
        signal_bound = (
            final_edit_index is not None
            and len(bound_validation) == 1
            and final_edit_index < bound_validation[0][0]
            and bound_validation[0][1].get("outcome") == "passed"
        )
        if (
            not matrix_valid
            or not isinstance(signal, str)
            or not signal.strip()
            or not signal_bound
        ):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["C"],
                    "outcome matrix and named validation signal must bind one passing post-edit validation",
                )
            )

    guard_d = by_guard.get(IMPLEMENTATION_GUARD_CODES["D"])
    if guard_d is not None:
        applies = event.get("implementation_kind") in BUGFIX_IMPLEMENTATION_KINDS
        valid = guard_d.get("applies") is applies
        if applies:
            valid = valid and all(
                guard_d.get(field) is True
                for field in (
                    "failure_mechanism_verified",
                    "symptom_cause_separated",
                    "same_pattern_scan_complete",
                )
            )
            recurrence_status = guard_d.get("recurrence_status")
            recurrence_signal = guard_d.get("recurrence_signal")
            valid = valid and recurrence_status in {"verified", "not-feasible"}
            valid = (
                valid
                and isinstance(recurrence_signal, str)
                and bool(recurrence_signal.strip())
            )
        else:
            valid = valid and all(
                guard_d.get(field) is None
                for field in (
                    "failure_mechanism_verified",
                    "symptom_cause_separated",
                    "same_pattern_scan_complete",
                    "recurrence_signal",
                )
            )
            valid = valid and guard_d.get("recurrence_status") == "not-applicable"
        if not valid:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["D"],
                    "bugfix applicability and mechanism evidence are inconsistent",
                )
            )
        if applies and source_bound:
            binding = guard_d.get("mechanism_binding")
            valid_binding = (
                isinstance(binding, dict)
                and tuple(binding)
                == (
                    "symptom_path",
                    "symptom_read_evidence",
                    "cause_path",
                    "cause_read_evidence",
                    "verified_mechanism",
                )
                and _meaningful_evidence_text(binding.get("verified_mechanism"))
                and binding.get("symptom_path") != binding.get("cause_path")
            )
            if valid_binding:
                symptom_read = source_reads_by_id.get(
                    binding["symptom_read_evidence"]
                )
                cause_read = source_reads_by_id.get(binding["cause_read_evidence"])
                valid_binding = bool(
                    symptom_read
                    and symptom_read[1].get("path") == binding["symptom_path"]
                    and cause_read
                    and cause_read[1].get("path") == binding["cause_path"]
                    and cause_read[1].get("read_kind") == "owning-implementation"
                )
            if not valid_binding:
                errors.append(
                    _implementation_discipline_error(
                        case_id,
                        IMPLEMENTATION_GUARD_CODES["D"],
                        "verified mechanism must bind distinct symptom and cause source paths",
                    )
                )
            if oracle_authority is not None:
                scan = guard_d.get("same_pattern_scan")
                scan_authority = oracle_authority["same_pattern_binding"]
                valid_scan = (
                    isinstance(scan, dict)
                    and tuple(scan)
                    == (
                        "task_id",
                        "acceptance_id",
                        "pattern_id",
                        "scope",
                        "evidence_id",
                        "artifact_id",
                        "source_anchor",
                        "proof_kind",
                        "matches",
                        "explicit_zero",
                        "exclusions",
                        "decision",
                    )
                    and scan.get("task_id") == oracle_authority["task_id"]
                    and scan.get("acceptance_id")
                    == oracle_authority["acceptance_id"]
                    and all(
                        scan.get(field) == scan_authority[field]
                        for field in (
                            "pattern_id",
                            "scope",
                            "evidence_id",
                            "artifact_id",
                            "source_anchor",
                            "proof_kind",
                        )
                    )
                    and isinstance(scan.get("matches"), list)
                    and all(
                        _meaningful_evidence_text(item)
                        for item in scan["matches"]
                    )
                    and isinstance(scan.get("exclusions"), list)
                    and all(
                        _meaningful_evidence_text(item)
                        for item in scan["exclusions"]
                    )
                    and (
                        (
                            bool(scan["matches"])
                            and scan.get("explicit_zero") is False
                        )
                        or (
                            not scan["matches"]
                            and scan.get("explicit_zero") is True
                            and scan.get("proof_kind")
                            == "fixture-structured-zero"
                        )
                    )
                    and scan.get("decision")
                    in {
                        "no-additional-exposure",
                        "repair-matches",
                        "exclude-nonreachable",
                    }
                )
                if not valid_scan:
                    errors.append(
                        _implementation_discipline_error(
                            case_id,
                            IMPLEMENTATION_GUARD_CODES["D"],
                            "source-bound bugfix requires an authority-bound structured same-pattern scan with matches or explicit zero",
                        )
                    )

    guard_e = by_guard.get(IMPLEMENTATION_GUARD_CODES["E"])
    if guard_e is not None and (
        guard_e.get("placement_resolved") is not True
        or guard_e.get("reuse_evaluated") is not True
        or guard_e.get("dependency_direction_resolved") is not True
        or guard_e.get("public_api_widened_for_tests") is not False
    ):
        errors.append(
            _implementation_discipline_error(
                case_id,
                IMPLEMENTATION_GUARD_CODES["E"],
                "placement, reuse, dependency direction, and test API boundary must resolve",
            )
        )
    if guard_e is not None and source_bound:
        reuse = guard_e.get("reuse_decision")
        valid_reuse = (
            isinstance(reuse, dict)
            and tuple(reuse)
            == (
                "candidate_path",
                "candidate_read_evidence",
                "compatibility",
                "decision",
                "reason",
            )
            and reuse.get("compatibility") in {"compatible", "incompatible"}
            and reuse.get("decision") in {"reuse", "new-structure"}
            and _meaningful_evidence_text(reuse.get("reason"))
        )
        if valid_reuse:
            candidate_read = source_reads_by_id.get(reuse["candidate_read_evidence"])
            valid_reuse = bool(
                candidate_read
                and candidate_read[1].get("read_kind") == "reuse-candidate"
                and candidate_read[1].get("path") == reuse["candidate_path"]
                and not (
                    reuse["compatibility"] == "compatible"
                    and reuse["decision"] != "reuse"
                )
            )
        if not valid_reuse:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["E"],
                    "reuse decision must bind a candidate read and reuse every compatible helper",
                )
            )
        if oracle_authority is not None:
            placement = guard_e.get("placement_decision")
            valid_placement = (
                isinstance(placement, dict)
                and tuple(placement)
                == (
                    "task_id",
                    "acceptance_id",
                    "decision",
                    "evidence_id",
                    "artifact_id",
                    "source_anchor",
                )
                and placement.get("task_id") == oracle_authority["task_id"]
                and placement.get("acceptance_id")
                == oracle_authority["acceptance_id"]
                and placement.get("decision")
                in {"existing-owner", "new-structure"}
            )
            if valid_placement:
                binding = oracle_authority["placement_binding"]
                valid_placement = bool(
                    placement["evidence_id"] == binding["evidence_id"]
                    and placement["artifact_id"] == binding["artifact_id"]
                    and placement["source_anchor"] == binding["source_anchor"]
                )
            if not valid_placement:
                errors.append(
                    _implementation_discipline_error(
                        case_id,
                        IMPLEMENTATION_GUARD_CODES["E"],
                        "placement must bind the case-local task, acceptance, source evidence, artifact, and anchor",
                    )
                )

    guard_f = by_guard.get(IMPLEMENTATION_GUARD_CODES["F"])
    if guard_f is not None and (
        guard_f.get("smallest_complete") is not True
        or guard_f.get("unrelated_refactor") is not False
        or guard_f.get("duplicate_helper") is not False
        or guard_f.get("unnecessary_dependency") is not False
        or guard_f.get("contract_handling") not in {"preserved", "declared-change"}
    ):
        errors.append(
            _implementation_discipline_error(
                case_id,
                IMPLEMENTATION_GUARD_CODES["F"],
                "change must be smallest-complete with explicit contract handling",
            )
        )
    guard_g = by_guard.get(IMPLEMENTATION_GUARD_CODES["G"])
    if guard_g is not None:
        errors.extend(
            _adaptive_test_guard_errors(
                case_id,
                guard_g,
                event_index,
                dispatch_index,
                first_edit_index,
                final_edit_index,
                steps,
                event.get("task_id"),
                derived_risk_triggers,
                oracle_authority,
            )
        )
    return errors


def _implementation_discipline_errors(
    case_id: str,
    steps: list[dict[str, Any]],
    oracle_authority: object = None,
) -> list[str]:
    errors: list[str] = []
    validated_authority: dict[str, Any] | None = None
    if (
        oracle_authority is not None
        or case_id in IMPLEMENTATION_ORACLE_CONTRACTS
    ):
        validated_authority, authority_errors = (
            _implementation_oracle_authority_errors(case_id, oracle_authority)
        )
        errors.extend(authority_errors)
    dispatches: dict[str, list[int]] = {}
    for index, step in enumerate(steps):
        task_id = _normal_task_dispatch_id(step)
        if task_id is not None:
            dispatches.setdefault(task_id, []).append(index)

    known_task_ids = set(dispatches)
    for index, step in enumerate(steps):
        if (
            step.get("actor") != "task-agent"
            or step.get("action") != "validate"
        ):
            continue
        _bound, binding_error = _validation_bound_task_ids(step, known_task_ids)
        if binding_error is not None:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "validation-task-binding",
                    f"validation at step {index}: {binding_error}",
                )
            )

    events: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, step in enumerate(steps):
        if step.get("action") != "implementation-discipline":
            continue
        if tuple(step) != IMPLEMENTATION_DISCIPLINE_FIELDS:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-event-schema",
                    f"event at step {index} must use exact ordered fields",
                )
            )
        if step.get("actor") != "task-agent":
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-event-schema",
                    f"event at step {index} must be emitted by task-agent",
                )
            )
        if step.get("schema_version") != IMPLEMENTATION_DISCIPLINE_SCHEMA_VERSION:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-event-schema",
                    f"event at step {index} has unsupported schema version",
                )
            )
        if step.get("implementation_kind") not in IMPLEMENTATION_KINDS:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-event-schema",
                    f"event at step {index} has unknown implementation kind",
                )
            )
        task_id = step.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-event-schema",
                    f"event at step {index} requires a task id",
                )
            )
            continue
        events.setdefault(task_id, []).append((index, step))
        if task_id not in dispatches:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-unknown-task",
                    f"event at step {index} does not bind a normal task dispatch",
                )
            )

    edits: dict[str, list[int]] = {}
    for index, step in enumerate(steps):
        if step.get("actor") != "task-agent" or step.get("action") not in EDIT_ACTIONS:
            continue
        task_id = step.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id not in dispatches:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["order"],
                    f"task-agent edit at step {index} must bind one normal task dispatch",
                )
            )
            continue
        edits.setdefault(task_id, []).append(index)

    for task_id, edit_indexes in edits.items():
        first_edit_index = min(edit_indexes)
        final_edit_index = max(edit_indexes)
        task_dispatches = dispatches.get(task_id, [])
        if len(task_dispatches) != 1:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-dispatch-binding",
                    f"task {task_id!r} must bind exactly one normal task dispatch",
                )
            )
        task_events = events.get(task_id, [])
        if len(task_events) != 1:
            code = (
                "implementation-discipline-missing-event"
                if not task_events
                else "implementation-discipline-duplicate-event"
            )
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    code,
                    "task-agent must complete implementation discipline before first edit",
                )
            )
            continue
        event_index, event = task_events[0]
        dispatch_index = task_dispatches[0] if len(task_dispatches) == 1 else None
        dispatch_step = steps[dispatch_index] if dispatch_index is not None else None
        if (
            dispatch_index is None
            or not dispatch_index < event_index < first_edit_index
        ):
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["order"],
                    "task-agent must complete implementation discipline before first edit",
                )
            )
        errors.extend(
            _implementation_guard_errors(
                case_id,
                event,
                event_index,
                dispatch_index,
                first_edit_index,
                final_edit_index,
                steps,
                _derived_adaptive_risk_triggers(event, dispatch_step),
                (
                    validated_authority
                    if validated_authority is not None
                    and validated_authority["task_id"] == task_id
                    else None
                ),
            )
        )

    for task_id, task_events in events.items():
        if task_id not in edits:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-without-edit",
                    f"task {task_id!r} has discipline evidence but no task-agent edit",
                )
            )
        elif len(task_events) > 1:
            errors.append(
                _implementation_discipline_error(
                    case_id,
                    "implementation-discipline-duplicate-event",
                    f"task {task_id!r} has duplicate discipline events",
                )
            )
    return list(dict.fromkeys(errors))


def _adaptive_testing_fixture_results(
    cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(cases, list) or not cases:
        return [], ["adaptive_testing_cases must be a non-empty list"]
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            errors.append("adaptive testing fixture must be a mapping")
            continue
        case_id = str(case.get("id") or "<missing>")
        steps = case.get("steps")
        expected_valid = case.get("expected_valid")
        expected_error = case.get("expected_error")
        if (
            not isinstance(steps, list)
            or not all(isinstance(step, dict) for step in steps)
            or not isinstance(expected_valid, bool)
            or (expected_error is not None and not isinstance(expected_error, str))
        ):
            errors.append(f"{case_id}: adaptive testing fixture shape is invalid")
            continue
        events = [
            (index, step)
            for index, step in enumerate(steps)
            if step.get("action") == "implementation-discipline"
        ]
        edits = [
            index
            for index, step in enumerate(steps)
            if step.get("actor") == "task-agent" and step.get("action") in EDIT_ACTIONS
        ]
        fixture_errors: list[str] = []
        if len(events) != 1 or len(edits) != 1:
            fixture_errors.append(
                _implementation_discipline_error(
                    case_id,
                    IMPLEMENTATION_GUARD_CODES["G"],
                    "adaptive fixture requires exactly one Guard G decision and one edit",
                )
            )
        else:
            event_index, event = events[0]
            evidence = event.get("evidence")
            guard = evidence[0] if isinstance(evidence, list) and len(evidence) == 1 else None
            if not isinstance(guard, dict) or guard.get("guard") != IMPLEMENTATION_GUARD_CODES["G"]:
                fixture_errors.append(
                    _implementation_discipline_error(
                        case_id,
                        IMPLEMENTATION_GUARD_CODES["G"],
                        "adaptive fixture decision must be the single Guard G record",
                    )
                )
            else:
                fixture_errors.extend(
                    _adaptive_test_guard_errors(
                        case_id,
                        guard,
                        event_index,
                        -1,
                        edits[0],
                        edits[0],
                        steps,
                        event.get("task_id"),
                        set(),
                    )
                )
        actual_valid = not fixture_errors
        matches_expected = actual_valid == expected_valid and (
            expected_error is None
            or any(expected_error in error for error in fixture_errors)
        )
        results.append(
            {
                "id": case_id,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": matches_expected,
                "errors": fixture_errors,
            }
        )
        if not matches_expected:
            errors.append(f"{case_id}: adaptive testing result does not match expectation")
    return results, errors


def _structured_error_codes(errors: list[str]) -> set[str]:
    return {
        error.split("[", 1)[1].split("]", 1)[0]
        for error in errors
        if "[" in error and "]" in error
    }


def _contains_forbidden_behavior_attestation(value: object) -> bool:
    if isinstance(value, dict):
        return "observed_behaviors" in value or any(
            _contains_forbidden_behavior_attestation(item)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_behavior_attestation(item) for item in value)
    return False


def _apply_required_behavior_bypass_mutation(
    case: dict[str, Any], mutation_kind: str
) -> None:
    events = [
        step
        for step in case["steps"]
        if step.get("action") == "implementation-discipline"
    ]
    event = events[0] if events else None
    by_guard = (
        {item["guard"]: item for item in event["evidence"]}
        if isinstance(event, dict)
        else {}
    )
    if mutation_kind == "owner-nearest-substitution":
        decision = by_guard[IMPLEMENTATION_GUARD_CODES["B"]]["owner_decision"]
        decision["owner_path"] = decision["nearest_candidate_path"]
    elif mutation_kind == "new-structure-despite-compatible-helper":
        by_guard[IMPLEMENTATION_GUARD_CODES["E"]]["reuse_decision"][
            "decision"
        ] = "new-structure"
    elif mutation_kind == "drop-test-compatibility-anchor":
        test_read = next(
            step
            for step in case["steps"]
            if step.get("read_kind") == "relevant-existing-tests"
            and step.get("task_id") == event["task_id"]
        )
        test_read.pop("compatibility_anchor", None)
    elif mutation_kind == "collapse-symptom-into-cause":
        binding = by_guard[IMPLEMENTATION_GUARD_CODES["D"]]["mechanism_binding"]
        binding["cause_path"] = binding["symptom_path"]
        binding["cause_read_evidence"] = binding["symptom_read_evidence"]
    elif mutation_kind == "move-relevant-tests-after-edit":
        test_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("read_kind") == "relevant-existing-tests"
            and step.get("task_id") == event["task_id"]
        )
        test_read = case["steps"].pop(test_index)
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent"
            and step.get("action") in EDIT_ACTIONS
            and step.get("task_id") == event["task_id"]
        )
        case["steps"].insert(edit_index + 1, test_read)
    elif mutation_kind == "remove-green-after-edit":
        green_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("action") == ADAPTIVE_TEST_EVIDENCE_ACTION
            and step.get("evidence_kind") == "green"
            and step.get("task_id") == event["task_id"]
        )
        case["steps"].pop(green_index)
    elif mutation_kind == "downgrade-high-risk-to-test-after":
        guard = by_guard[IMPLEMENTATION_GUARD_CODES["G"]]
        red_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("action") == ADAPTIVE_TEST_EVIDENCE_ACTION
            and step.get("evidence_kind") == "red"
            and step.get("task_id") == event["task_id"]
        )
        case["steps"].pop(red_index)
        guard["approach"] = "test-after"
        guard["reason"] = "attempted high-risk downgrade"
        guard["evidence"] = [guard["evidence"][-1]]
    elif mutation_kind == "strip-test-after-qualifier":
        guard = by_guard[IMPLEMENTATION_GUARD_CODES["G"]]
        guard["risk_triggers"] = ["unqualified-local-change"]
    elif mutation_kind == "misclassify-documentation-as-behavior":
        by_guard[IMPLEMENTATION_GUARD_CODES["G"]]["change_kind"] = "behavior"
    elif mutation_kind == "red-environment-failure":
        red = next(
            step
            for step in case["steps"]
            if step.get("action") == ADAPTIVE_TEST_EVIDENCE_ACTION
            and step.get("evidence_kind") == "red"
            and step.get("task_id") == event["task_id"]
        )
        red["failure_class"] = "environment"
    elif mutation_kind == "weaken-green-assertion":
        green = next(
            step
            for step in case["steps"]
            if step.get("action") == ADAPTIVE_TEST_EVIDENCE_ACTION
            and step.get("evidence_kind") == "green"
            and step.get("task_id") == event["task_id"]
        )
        green["assertion"] = "process returned"
    elif mutation_kind == "skip-same-pattern-scan":
        by_guard[IMPLEMENTATION_GUARD_CODES["D"]][
            "same_pattern_scan_complete"
        ] = False
    elif mutation_kind == "drop-placement-evidence-for-new-structure":
        by_guard[IMPLEMENTATION_GUARD_CODES["E"]]["placement_resolved"] = False
    elif mutation_kind == "remove-parallel-workspace-isolation":
        dispatch = next(
            step
            for step in case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "task-agent"
            and step.get("parallel_batch")
        )
        dispatch["workspace_isolation"] = "shared"
    elif mutation_kind == "edit-after-validation":
        validation_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation = case["steps"][validation_index]
        edit = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") in EDIT_ACTIONS
            and step.get("task_id") == validation.get("task_id")
        )
        case["steps"].insert(
            validation_index + 1,
            {
                "actor": "task-agent",
                "action": "repair",
                "task_id": validation["task_id"],
                "path": edit["path"],
            },
        )
    elif mutation_kind == "remove-fresh-rereview":
        final_event_index = max(
            index
            for index, step in enumerate(case["steps"])
            if step.get("action") == REVIEW_DISCIPLINE_ACTION
        )
        case["steps"].pop(final_event_index)
        final_rereview_index = max(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "review-agent"
            and step.get("action") == "re-review"
        )
        case["steps"].pop(final_rereview_index)
    elif mutation_kind == "drop-current-completion-evidence":
        return
    else:
        raise ValueError(f"unknown required-behavior bypass mutation {mutation_kind!r}")


def _required_behavior_manifest_entry(
    behavior_id: str,
    contract: RequiredBehaviorContract,
) -> dict[str, Any]:
    """Render the sole accepted manifest entry from the immutable evaluator oracle."""

    return {
        "id": behavior_id,
        "status": "covered",
        "positive_trajectory": {
            "fixture_group": "cases",
            "case_id": contract.positive_case,
            "validator_family": contract.validator_family,
        },
        "bypass_mutation": {"kind": contract.bypass_mutation},
        "expected_error": {"code": contract.expected_error},
        "dimensions": list(contract.dimensions),
        "gap": None,
    }


def _required_behavior_coverage_results(
    document: object,
    professional: dict[str, dict[str, Any]],
    layer3_entries: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate the exact 17-item manifest and execute covered bypass mutations."""

    if not isinstance(document, dict):
        return [], ["required behavior coverage document must be a mapping"]
    manifest = document.get("required_behavior_coverage")
    if _contains_forbidden_behavior_attestation(manifest):
        return [], [
            "required behavior coverage rejects observed_behaviors and keyword-only substitutes"
        ]
    if not isinstance(manifest, dict) or tuple(manifest) != (
        "schema_version",
        "groups",
    ):
        return [], ["required behavior coverage manifest must use the exact shape"]
    if manifest.get("schema_version") != 1:
        return [], ["required behavior coverage schema_version must equal 1"]
    groups = manifest.get("groups")
    if not isinstance(groups, list):
        return [], ["required behavior coverage groups must be an ordered list"]

    errors: list[str] = []
    results: list[dict[str, Any]] = []
    actual_group_ids = [
        group.get("id") if isinstance(group, dict) else None for group in groups
    ]
    if actual_group_ids != list(REQUIRED_BEHAVIOR_GROUPS):
        errors.append(
            "required behavior coverage groups must equal the exact required groups in order"
        )

    fixture_groups = {
        "cases": document.get("cases"),
        "adaptive_testing_cases": document.get("adaptive_testing_cases"),
        "completion_state_cases": document.get("completion_state_cases"),
    }
    fixture_indexes = {
        group_id: {
            case.get("id"): case
            for case in cases
            if isinstance(case, dict) and isinstance(case.get("id"), str)
        }
        for group_id, cases in fixture_groups.items()
        if isinstance(cases, list)
    }

    for group in groups:
        if not isinstance(group, dict) or tuple(group) != ("id", "entries"):
            errors.append("required behavior coverage group must use exact fields")
            continue
        group_id = group.get("id")
        entries = group.get("entries")
        expected_ids = REQUIRED_BEHAVIOR_GROUPS.get(str(group_id), ())
        if not isinstance(entries, list):
            errors.append(f"{group_id}: entries must be an ordered list")
            continue
        actual_ids = [
            entry.get("id") if isinstance(entry, dict) else None for entry in entries
        ]
        if actual_ids != list(expected_ids):
            errors.append(
                f"{group_id}: entries must equal the exact required behavior ids in order; "
                f"expected={list(expected_ids)!r}, actual={actual_ids!r}"
            )

        for entry in entries:
            if not isinstance(entry, dict) or tuple(entry) != (
                "id",
                "status",
                "positive_trajectory",
                "bypass_mutation",
                "expected_error",
                "dimensions",
                "gap",
            ):
                errors.append(
                    f"{group_id}: required behavior entry must use the exact structured fields"
                )
                continue
            behavior_id = str(entry.get("id") or "<missing>")
            contract = REQUIRED_BEHAVIOR_CONTRACTS.get(behavior_id)
            if (
                contract is None
                or entry
                != _required_behavior_manifest_entry(behavior_id, contract)
            ):
                errors.append(
                    f"{behavior_id}: manifest entry must equal its immutable contract oracle"
                )
                continue
            status = entry.get("status")
            positive = entry.get("positive_trajectory")
            mutation = entry.get("bypass_mutation")
            expected_error = entry.get("expected_error")
            dimensions = entry.get("dimensions")
            gap = entry.get("gap")
            if status != "covered":
                errors.append(
                    f"{behavior_id}: every required behavior must be covered; gaps fail RDS009"
                )
                continue
            positive_fields = tuple(positive) if isinstance(positive, dict) else ()
            if (
                not isinstance(positive, dict)
                or positive_fields
                not in {
                    ("fixture_group", "case_id"),
                    ("fixture_group", "case_id", "validator_family"),
                }
                or positive.get("fixture_group") != "cases"
            ):
                errors.append(f"{behavior_id}: positive_trajectory shape is invalid")
                continue
            validator_family = positive.get("validator_family", "metrics")
            if validator_family not in {"metrics", "scheduling"} or (
                validator_family == "scheduling"
                and behavior_id != "closure-parallel-writes-require-isolation"
            ):
                errors.append(f"{behavior_id}: positive trajectory validator family is invalid")
                continue
            positive_case = fixture_indexes.get(str(positive.get("fixture_group")), {}).get(
                positive.get("case_id")
            )
            if positive_case is None:
                errors.append(f"{behavior_id}: positive trajectory reference is unknown")
                continue
            if (
                not isinstance(expected_error, dict)
                or tuple(expected_error) != ("code",)
                or not isinstance(expected_error.get("code"), str)
                or not expected_error["code"].strip()
            ):
                errors.append(f"{behavior_id}: expected_error must name one structured code")
                continue
            if (
                not isinstance(dimensions, list)
                or not dimensions
                or len(dimensions) != len(set(dimensions))
                or not set(dimensions) <= REQUIRED_BEHAVIOR_DIMENSIONS
            ):
                errors.append(f"{behavior_id}: dimensions are invalid")
                continue
            if tuple(dimensions) != contract.dimensions:
                errors.append(
                    f"{behavior_id}: dimensions must match the behavior's exact proving dimensions"
                )
                continue

            result = {
                "id": behavior_id,
                "group": group_id,
                "status": status,
                "positive_valid": False,
                "full_path_valid": False,
                "mutation_applied": False,
                "bypass_rejected": False,
                "expected_error": expected_error["code"],
                "error_codes": [],
                "gap": gap,
            }
            if gap is not None:
                errors.append(f"{behavior_id}: covered behavior gap must be null")
            if (
                not isinstance(mutation, dict)
                or tuple(mutation) != ("kind",)
                or mutation.get("kind") not in REQUIRED_BEHAVIOR_BYPASS_MUTATIONS
            ):
                errors.append(f"{behavior_id}: covered bypass mutation is invalid")
                results.append(result)
                continue

            positive_case_copy = copy.deepcopy(positive_case)
            positive_metrics, positive_errors = _metrics(
                positive_case_copy,
                professional,
                layer3_entries,
            )
            positive_errors.extend(
                _expectation_errors(positive_case_copy, positive_metrics)
            )
            if validator_family == "scheduling" and not positive_errors:
                positive_steps, _internal = _operational_steps(
                    positive_case_copy.get("steps", [])
                )
                positive_conflict, positive_reduction = _parallel_metrics(
                    positive_steps
                )
                if (
                    positive_conflict
                    or positive_reduction < 1
                    or positive_case_copy.get("capability_scope")
                    != "conditional-isolated-write-contract"
                ):
                    positive_errors.append(
                        "scheduling positive requires isolated non-overlapping parallel writes"
                    )
            if mutation["kind"] == "drop-current-completion-evidence":
                positive_completion = fixture_indexes.get(
                    "completion_state_cases", {}
                ).get("implementation-completed-with-current-evidence")
                if positive_completion is None:
                    positive_errors.append(
                        "positive completion-state fixture is unavailable"
                    )
                else:
                    positive_errors.extend(
                        completion_claim_errors(
                            copy.deepcopy(positive_completion.get("claim"))
                        )
                    )
            result["positive_valid"] = not positive_errors
            result["full_path_valid"] = not positive_errors
            if positive_errors:
                errors.append(
                    f"{behavior_id}: positive full trajectory is not structurally valid: {positive_errors}"
                )
                results.append(result)
                continue

            mutated = copy.deepcopy(positive_case)
            try:
                _apply_required_behavior_bypass_mutation(mutated, mutation["kind"])
            except (KeyError, StopIteration, TypeError, ValueError) as exc:
                errors.append(f"{behavior_id}: bypass mutation cannot be applied: {exc}")
                results.append(result)
                continue
            mutation_metrics, mutation_errors = _metrics(
                mutated,
                professional,
                layer3_entries,
            )
            mutation_errors.extend(
                _expectation_errors(mutated, mutation_metrics)
            )
            if validator_family == "scheduling":
                mutation_steps, _internal = _operational_steps(mutated.get("steps", []))
                mutation_conflict, mutation_reduction = _parallel_metrics(
                    mutation_steps
                )
                mutation_metrics["parallel_write_conflict"] = mutation_conflict
                mutation_metrics[
                    "conditional_isolated_write_reduction_steps"
                ] = mutation_reduction
            if (
                mutation["kind"] == "remove-parallel-workspace-isolation"
                and mutation_metrics.get("parallel_write_conflict") is True
            ):
                mutation_errors.append(
                    f"{behavior_id}: [parallel-write-isolation] parallel writes require distinct host-provided isolated workspaces"
                )
            if (
                mutation["kind"] == "remove-fresh-rereview"
                and mutation_metrics.get("repair_has_rereview") is False
            ):
                mutation_errors.append(
                    f"{behavior_id}: [repair-rereview-missing] repair requires fresh validation and re-review"
                )
            if mutation["kind"] == "drop-current-completion-evidence":
                completion_case = fixture_indexes.get(
                    "completion_state_cases", {}
                ).get("implementation-completed-with-current-evidence")
                if completion_case is not None:
                    mutated_claim = copy.deepcopy(completion_case.get("claim"))
                    mutated_claim["evidence_ledger"] = []
                    completion_errors = completion_claim_errors(mutated_claim)
                    if completion_errors:
                        mutation_errors.extend(completion_errors)
                        mutation_errors.append(
                            f"{behavior_id}: [completion-current-evidence] completed status requires current evidence"
                        )
            codes = sorted(_structured_error_codes(mutation_errors))
            result["mutation_applied"] = True
            result["error_codes"] = codes
            result["bypass_rejected"] = expected_error["code"] in codes
            if not result["bypass_rejected"]:
                errors.append(
                    f"{behavior_id}: bypass mutation did not produce expected structured error "
                    f"{expected_error['code']!r}; errors={mutation_errors!r}"
                )
            results.append(result)
    covered_dimensions = {
        dimension
        for group in groups
        if isinstance(group, dict) and isinstance(group.get("entries"), list)
        for entry in group["entries"]
        if isinstance(entry, dict) and entry.get("status") == "covered"
        for dimension in entry.get("dimensions", [])
        if isinstance(dimension, str)
    }
    if covered_dimensions != REQUIRED_BEHAVIOR_DIMENSIONS:
        errors.append(
            "required behavior coverage must exercise order, decision, freshness, and output"
        )
    return results, errors


def _review_discipline_error(case_id: str, code: str, message: str) -> str:
    return f"{case_id}: [{code}] {message}"


def _meaningful_professional_risk_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().casefold()
        not in {"none", "unknown", "unavailable", "not-applicable", "not applicable"}
    )


def _professional_risk_matrix_errors(
    event: dict[str, Any],
    execution_level: object,
) -> tuple[list[str], list[object]]:
    """Validate one ordered, evidence-bearing professional-risk decision matrix."""

    errors: list[str] = []
    risks = event.get("professional_risks")
    expected_dimensions = tuple(
        REVIEW_PROFESSIONAL_RISK_MATRIX["level_dimensions"].get(
            execution_level,
            REVIEW_PROFESSIONAL_RISK_DIMENSIONS,
        )
    )
    if not isinstance(risks, list):
        return ["professional_risks must be an ordered decision list"], []

    dimensions: list[object] = []
    statuses: list[object] = []
    for index, decision in enumerate(risks):
        if not isinstance(decision, dict) or tuple(decision) != REVIEW_PROFESSIONAL_RISK_FIELDS:
            errors.append(
                f"professional-risk decision {index} must use exact ordered fields "
                f"{list(REVIEW_PROFESSIONAL_RISK_FIELDS)}"
            )
            continue
        dimension = decision.get("dimension")
        status = decision.get("status")
        dimensions.append(dimension)
        statuses.append(status)
        if status not in REVIEW_PROFESSIONAL_RISK_STATUSES:
            errors.append(
                f"unsupported professional-risk status {status!r} for {dimension!r}"
            )
            continue

        reason = decision.get("reason")
        evidence = decision.get("evidence")
        specialist = decision.get("specialist_skill")
        scope = decision.get("scope")
        if not _meaningful_professional_risk_text(reason) or not _meaningful_professional_risk_text(
            evidence
        ):
            if status == "not-applicable":
                errors.append(
                    f"not-applicable {dimension!r} requires a source-backed reason and evidence"
                )
            else:
                errors.append(
                    f"professional-risk decision {dimension!r} requires reason and evidence"
                )
        if status == "delegated":
            if (
                specialist not in REVIEW_SKILL_IDS
                or not _meaningful_professional_risk_text(scope)
                or not _meaningful_professional_risk_text(reason)
            ):
                errors.append(
                    f"delegated {dimension!r} requires a named registered Review Skill, scope, and reason"
                )
        elif specialist != "not-applicable" or scope != "not-applicable":
            errors.append(
                f"non-delegated {dimension!r} must mark specialist_skill and scope not-applicable"
            )

    counts = {dimension: dimensions.count(dimension) for dimension in set(dimensions)}
    duplicates = sorted(
        str(dimension) for dimension, count in counts.items() if count > 1
    )
    missing = [dimension for dimension in expected_dimensions if dimension not in dimensions]
    unknown = sorted(
        str(dimension)
        for dimension in set(dimensions)
        if dimension not in expected_dimensions
    )
    if duplicates:
        errors.append(f"duplicate professional-risk dimensions {duplicates}")
    if missing:
        errors.append(f"missing professional-risk dimensions {missing}")
    if unknown:
        errors.append(f"unknown professional-risk dimensions {unknown}")
    if not duplicates and not missing and not unknown and tuple(dimensions) != expected_dimensions:
        errors.append("professional-risk dimensions must preserve canonical order")
    return errors, statuses


def _review_discipline_errors(
    case_id: str,
    steps: list[dict[str, Any]],
) -> list[str]:
    """Validate the lightweight typed review guard against observable trace order."""

    errors: list[str] = []
    seen_handoff_ids: set[str] = set()
    consumed_handoff_indices: set[int] = set()
    consumed_gate_indices: set[int] = set()

    def reject(code: str, message: str) -> None:
        errors.append(_review_discipline_error(case_id, code, message))

    reviewer_mutations = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "review-agent"
        and step.get("action") in EDIT_ACTIONS
    ]
    for index, step in reviewer_mutations:
        reject(
            "reviewer-mutation",
            f"review-agent must never edit or repair; found {step.get('action')!r} at step {index}",
        )

    events = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("action") == REVIEW_DISCIPLINE_ACTION
    ]
    review_actions = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "review-agent"
        and step.get("action") in REVIEW_ACTIONS | {"finding"}
    ]
    if not events and not review_actions:
        return list(dict.fromkeys(errors))
    if len(events) != len(review_actions):
        reject(
            "review-discipline-pairing",
            "every implementation or repair review requires exactly one typed review-discipline event",
        )
        return list(dict.fromkeys(errors))

    prior_review_index = -1
    for (event_index, event), (review_index, review_action) in zip(
        events, review_actions, strict=True
    ):
        if not event_index < review_index:
            reject(
                "review-discipline-order",
                "review-discipline must precede its review or re-review action",
            )
        if tuple(event) != REVIEW_DISCIPLINE_FIELDS:
            reject(
                "review-discipline-shape",
                f"review-discipline event must use exact ordered fields {list(REVIEW_DISCIPLINE_FIELDS)}",
            )
            prior_review_index = review_index
            continue
        if (
            event.get("actor") != "review-agent"
            or event.get("schema_version") != REVIEW_DISCIPLINE_MODEL["schema_version"]
        ):
            reject(
                "review-discipline-shape",
                "review-discipline must use the current schema as a review-agent event",
            )

        task_id = event.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            reject("review-discipline-shape", "review-discipline task_id must be non-empty")
        execution_level = event.get("execution_level")
        if execution_level not in REVIEW_DISCIPLINE_MODEL["level_base_dimensions"]:
            reject("review-level", "review-discipline execution_level must be L1-L5")
        review_kind = event.get("review_kind")
        if review_kind not in REVIEW_KINDS:
            reject("review-kind", "review_kind must be implementation or repair")

        material_steps = [
            (index, step)
            for index, step in enumerate(steps[:event_index])
            if step.get("actor") in {"task-agent", "review-agent"}
            and step.get("action") in EDIT_ACTIONS
        ]
        material_since_review = [
            (index, step)
            for index, step in material_steps
            if index > prior_review_index
        ]
        required_review_kind = (
            "repair"
            if any(
                step.get("action") == "repair"
                for _index, step in material_since_review
            )
            else "implementation"
        )
        if review_kind != required_review_kind:
            reject(
                "review-kind",
                f"actual material actions require {required_review_kind} review; "
                f"review_kind={review_kind!r} contradicts the derived requirement",
            )
        expected_actions = (
            {"re-review"}
            if required_review_kind == "repair"
            else {"review", "finding"}
        )
        if review_action.get("action") not in expected_actions:
            reject(
                "review-kind",
                f"derived {required_review_kind!r} review kind requires one of "
                f"{sorted(expected_actions)}",
            )

        dispatch_pair = next(
            (
                (index, step)
                for index, step in reversed(list(enumerate(steps[: event_index + 1])))
                if step.get("action") == "dispatch"
                and step.get("profile") == "review-agent"
            ),
            None,
        )
        dispatch_index = dispatch_pair[0] if dispatch_pair is not None else -1
        dispatch = dispatch_pair[1] if dispatch_pair is not None else None
        if isinstance(dispatch, dict):
            primary_skill = dispatch.get("primary_skill")
            if primary_skill not in REVIEW_SKILL_IDS:
                reject(
                    "review-professional-selector",
                    "the assigned Review Skill must be selected dynamically from "
                    "professional registry role_support",
                )
            capsule = dispatch.get("fixture_capsule")
            if isinstance(capsule, dict) and capsule.get("task_id") != task_id:
                reject(
                    "review-task-binding",
                    "review-discipline task_id must match the review assignment",
                )
            extension = capsule.get("execution_level_extension") if isinstance(capsule, dict) else None
            if (
                isinstance(extension, dict)
                and extension.get("effective_level") != execution_level
            ):
                reject(
                    "review-level",
                    "review-discipline execution_level must match the assignment effective level",
                )

        dimensions = event.get("dimensions")
        expected_dimensions = tuple(
            REVIEW_DISCIPLINE_MODEL["level_base_dimensions"].get(
                execution_level, REVIEW_BASE_DIMENSIONS
            )
        )
        if not isinstance(dimensions, dict) or tuple(dimensions) != expected_dimensions:
            reject(
                "review-dimensions",
                "review-discipline must decide exactly the same ten ordered base dimensions at L1-L5",
            )
            dimension_values: list[object] = []
        else:
            dimension_values = list(dimensions.values())
            if any(value not in REVIEW_DIMENSION_DECISIONS for value in dimension_values):
                reject(
                    "review-dimensions",
                    "every review dimension must use a closed decision value",
                )

        professional_matrix_errors, professional_statuses = (
            _professional_risk_matrix_errors(event, execution_level)
        )
        for message in professional_matrix_errors:
            reject("review-professional-risks", message)

        evidence_source = event.get("evidence_source")
        if evidence_source in REVIEW_FORBIDDEN_EVIDENCE_SOURCES:
            reject(
                "review-independence",
                "implementer reasoning or a changed-file summary is not review evidence",
            )
        elif evidence_source not in REVIEW_EVIDENCE_SOURCES:
            reject(
                "review-independence",
                "review evidence source must be independent-review or unavailable",
            )

        diff = event.get("diff")
        validation = event.get("validation")
        if not isinstance(diff, dict) or tuple(diff) != REVIEW_DIFF_FIELDS:
            reject(
                "review-diff",
                f"review diff must use exact fields {list(REVIEW_DIFF_FIELDS)}",
            )
            diff = {}
        if not isinstance(validation, dict) or tuple(validation) != REVIEW_VALIDATION_FIELDS:
            reject(
                "review-validation",
                f"review validation must use exact fields {list(REVIEW_VALIDATION_FIELDS)}",
            )
            validation = {}

        diff_kind = diff.get("kind")
        if diff_kind not in REVIEW_DIFF_KINDS:
            reject(
                "review-diff",
                "implementation review requires an actual diff, not a summary or inferred scope",
            )
        validation_source = validation.get("source")
        validation_result = validation.get("result")
        if validation_source not in REVIEW_VALIDATION_SOURCES:
            reject("review-validation", "validation source is not canonical")
        if validation_result not in REVIEW_VALIDATION_RESULTS:
            reject("review-validation", "validation result is not canonical")

        generation = max(1, len(material_steps))
        changed_files = diff.get("changed_files")
        action_changed_files = review_action.get("changed_paths")
        if action_changed_files is None and isinstance(review_action.get("path"), str):
            action_changed_files = [review_action["path"]]
        if not isinstance(changed_files, list) or any(
            not isinstance(path, str) or not path for path in changed_files
        ) or len(changed_files) != len(set(changed_files)):
            reject("review-changed-files", "changed_files must be a unique path list")
            changed_files = []
        if action_changed_files != changed_files:
            reject(
                "review-changed-files",
                "review action must inspect every file declared by the actual diff",
            )
        expected_changed_files = list(
            dict.fromkeys(
                str(step.get("path"))
                for _index, step in material_since_review
                if isinstance(step.get("path"), str) and step.get("path")
            )
        )
        if expected_changed_files and changed_files != expected_changed_files:
            reject(
                "review-changed-files",
                "review must cover every file changed since the previous review",
            )

        if material_since_review:
            round_dispatches = [
                (index, step)
                for index, step in enumerate(steps[:event_index])
                if prior_review_index < index
                and step.get("action") == "dispatch"
                and step.get("profile") == "review-agent"
            ]
            if len(round_dispatches) != 1:
                reject(
                    "review-input-dispatch",
                    "normal review requires exactly one review dispatch after the current Handoff gate",
                )
            else:
                dispatch_index, dispatch = round_dispatches[0]

            latest_material_index = material_since_review[-1][0]
            handoffs = [
                (index, step)
                for index, step in enumerate(steps[:review_index])
                if latest_material_index < index
                and step.get("actor") == "task-agent"
                and step.get("action") == IMPLEMENTATION_HANDOFF_ACTION
            ]
            gates = [
                (index, step)
                for index, step in enumerate(steps[:review_index])
                if latest_material_index < index
                and step.get("actor") == "main-control-agent"
                and step.get("action") == REVIEW_INPUT_READY_ACTION
            ]
            if len(handoffs) != 1:
                reject(
                    "review-input-handoff",
                    "normal review requires one current Implementation Handoff after validation and before review dispatch",
                )
            if len(gates) != 1:
                reject(
                    "review-input-gate",
                    "review dispatch requires one derived Main readiness gate after the current Handoff",
                )

            handoff_index, handoff = handoffs[0] if len(handoffs) == 1 else (-1, {})
            gate_index, gate = gates[0] if len(gates) == 1 else (-1, {})
            if len(handoffs) == 1:
                consumed_handoff_indices.add(handoff_index)
            if len(gates) == 1:
                consumed_gate_indices.add(gate_index)
            handoff_ready = True
            if tuple(handoff) != IMPLEMENTATION_HANDOFF_FIELDS:
                reject(
                    "review-input-handoff-shape",
                    "Implementation Handoff must use the exact ordered review-input fields",
                )
                handoff_ready = False

            handoff_id = handoff.get("handoff_id")
            if not isinstance(handoff_id, str) or not handoff_id.strip():
                reject(
                    "review-input-handoff-shape",
                    "Implementation Handoff handoff_id must be non-empty",
                )
                handoff_ready = False
            elif handoff_id in seen_handoff_ids:
                reject(
                    "review-input-handoff-generation",
                    "each implementation or repair generation requires a fresh handoff_id",
                )
                handoff_ready = False
            else:
                seen_handoff_ids.add(handoff_id)
            if handoff.get("task_id") != task_id:
                reject(
                    "review-input-handoff-task",
                    "Implementation Handoff task_id must match the review assignment",
                )
                handoff_ready = False

            handoff_paths = handoff.get("latest_changed_paths")
            if (
                not isinstance(handoff_paths, list)
                or not handoff_paths
                or any(not isinstance(path, str) or not path for path in handoff_paths)
                or len(handoff_paths) != len(set(handoff_paths))
                or handoff_paths != expected_changed_files
            ):
                reject(
                    "review-input-changed-paths",
                    "Implementation Handoff latest_changed_paths must equal every path changed since the previous review",
                )
                handoff_ready = False

            exact_evidence = handoff.get("exact_change_evidence")
            if not isinstance(exact_evidence, dict) or tuple(exact_evidence) != EXACT_CHANGE_EVIDENCE_FIELDS:
                reject(
                    "review-input-evidence-shape",
                    "exact_change_evidence must use kind, artifact, and generation in canonical order",
                )
                exact_evidence = {}
                handoff_ready = False
            evidence_kind = exact_evidence.get("kind")
            if evidence_kind in REVIEW_INPUT_FORBIDDEN_EVIDENCE_KINDS:
                reject(
                    "review-input-evidence-kind",
                    "changed-file summary, prose description, and implementer self-report are forbidden review evidence",
                )
                handoff_ready = False
            elif evidence_kind not in REVIEW_INPUT_EXACT_EVIDENCE_KINDS:
                reject(
                    "review-input-evidence-kind",
                    "Implementation Handoff requires a Core-declared exact change evidence kind",
                )
                handoff_ready = False
            evidence_artifact = exact_evidence.get("artifact")
            if not _exact_change_evidence_accessible(
                evidence_kind,
                evidence_artifact,
                handoff_paths,
                handoff.get("reviewer_capability_accessibility"),
                current_generation=generation,
            ):
                reject(
                    "review-input-evidence-payload",
                    "supplied review evidence must be actual unified-diff content for the exact changed paths, or a current reviewer-readable native change reference",
                )
                handoff_ready = False
            if exact_evidence.get("generation") != generation:
                reject(
                    "review-input-evidence-generation",
                    "exact change evidence must use the current material generation",
                )
                handoff_ready = False

            capability_access = handoff.get("reviewer_capability_accessibility")
            if (
                not isinstance(capability_access, dict)
                or tuple(capability_access) != REVIEWER_CAPABILITY_ACCESSIBILITY_FIELDS
            ):
                reject(
                    "review-input-capability-shape",
                    "reviewer capability accessibility must use the five canonical capability facts",
                )
                capability_access = {}
                handoff_ready = False
            if (
                capability_access.get("reviewer-change-consume") != "supported"
                or capability_access.get("non-mutating-validation") != "supported"
                or (
                    evidence_kind == "reviewer-accessible-native-reference"
                    and capability_access.get("native-change-read") != "supported"
                )
                or (
                    evidence_kind != "reviewer-accessible-native-reference"
                    and (
                        capability_access.get("change-evidence-export") != "supported"
                        or capability_access.get("supplied-change-delivery") != "supported"
                    )
                )
            ):
                reject(
                    "review-input-capability",
                    "review dispatch requires the evidence-path capabilities, reviewer consumption, and non-mutating validation",
                )
                handoff_ready = False

            handoff_validation = handoff.get("validation_after_latest_material_edit")
            if (
                not isinstance(handoff_validation, dict)
                or tuple(handoff_validation)
                != VALIDATION_AFTER_LATEST_MATERIAL_EDIT_FIELDS
            ):
                reject(
                    "review-input-validation-shape",
                    "validation_after_latest_material_edit must use evidence_id, result, and generation in canonical order",
                )
                handoff_validation = {}
                handoff_ready = False
            handoff_evidence_id = handoff_validation.get("evidence_id")
            round_validations = [
                (index, step)
                for index, step in enumerate(steps[:handoff_index])
                if latest_material_index < index
                and step.get("actor") == "task-agent"
                and step.get("action") == "validate"
            ]
            round_captures = [
                (index, step)
                for index, step in enumerate(steps[:handoff_index])
                if latest_material_index < index
                and step.get("actor") == "task-agent"
                and step.get("action") == "capture-change-evidence"
            ]
            matching_validation = (
                round_validations[0][1] if len(round_validations) == 1 else {}
            )
            if (
                not isinstance(handoff_evidence_id, str)
                or not handoff_evidence_id.strip()
                or handoff_validation.get("result") != "passed"
                or handoff_validation.get("generation") != generation
                or len(round_validations) != 1
                or matching_validation.get("evidence_id") != handoff_evidence_id
                or matching_validation.get("outcome") != "passed"
                or handoff_evidence_id != validation.get("evidence_id")
                or handoff_validation.get("result") != validation.get("result")
                or handoff_validation.get("generation") != validation.get("generation")
            ):
                reject(
                    "review-input-validation",
                    "Handoff validation must bind the unique passing validation after the latest material edit",
                )
                handoff_ready = False
            if (
                len(round_captures) != 1
                or len(round_validations) != 1
                or tuple(round_captures[0][1])
                != (
                    "actor",
                    "action",
                    "task_id",
                    "artifact",
                    "generation",
                    "changed_paths",
                )
                or round_captures[0][0] <= round_validations[0][0]
                or round_captures[0][1].get("task_id") != task_id
                or round_captures[0][1].get("artifact") != evidence_artifact
                or round_captures[0][1].get("generation") != generation
                or round_captures[0][1].get("changed_paths") != handoff_paths
            ):
                reject(
                    "review-input-change-capture",
                    "the same Task must capture exact current change evidence once after fresh validation and before its Handoff",
                )
                handoff_ready = False

            fixed_scope = handoff.get("fixed_review_scope")
            if fixed_scope != expected_changed_files:
                reject(
                    "review-input-scope",
                    "fixed_review_scope must equal the current changed-path scope",
                )
                handoff_ready = False

            if handoff_index >= gate_index or gate_index >= dispatch_index:
                reject(
                    "review-input-order",
                    "normal review order is validation, Handoff, Main readiness gate, then review dispatch",
                )
                handoff_ready = False

            if tuple(gate) != REVIEW_INPUT_READY_FIELDS:
                reject(
                    "review-input-gate-shape",
                    "Main readiness gate must use actor, action, handoff_id, and ready in canonical order",
                )
            if gate.get("handoff_id") != handoff_id:
                reject(
                    "review-input-gate-binding",
                    "Main readiness gate must reference the current Handoff",
                )
            if gate.get("ready") is not handoff_ready:
                reject(
                    "review-input-gate-derived",
                    "Main readiness must be derived from all five Handoff fields and capability facts",
                )
            if gate.get("ready") is not True:
                reject(
                    "review-input-dispatch-before-ready",
                    "review dispatch is forbidden when the derived Main readiness gate is false",
                )

            review_input_binding = (
                dispatch.get("review_input_binding")
                if isinstance(dispatch, dict)
                else None
            )
            if (
                not isinstance(review_input_binding, dict)
                or tuple(review_input_binding) != REVIEW_INPUT_BINDING_FIELDS
            ):
                reject(
                    "review-input-dispatch-binding",
                    "review dispatch must bind handoff_id, artifact, and generation in canonical order",
                )
                review_input_binding = {}
            if (
                review_input_binding.get("handoff_id") != handoff_id
                or review_input_binding.get("artifact") != evidence_artifact
                or review_input_binding.get("generation") != generation
            ):
                reject(
                    "review-input-dispatch-binding",
                    "review dispatch must bind the current Handoff artifact and generation",
                )
            if (
                diff.get("artifact") != evidence_artifact
                or diff.get("generation") != exact_evidence.get("generation")
                or changed_files != handoff_paths
            ):
                reject(
                    "review-input-reviewer-binding",
                    "reviewer diff artifact, generation, and changed files must match the Handoff and dispatch",
                )
            supplied_reads = [
                step
                for step in steps[dispatch_index + 1 : event_index]
                if step.get("actor") == "review-agent"
                and step.get("action") == "read"
                and step.get("artifact_ref") == evidence_artifact
            ]
            if evidence_kind != "reviewer-accessible-native-reference" and len(supplied_reads) != 1:
                reject(
                    "review-input-reviewer-read",
                    "supplied review evidence must be read exactly once by the assigned reviewer before review",
                )
        elif prior_review_index >= 0:
            reject(
                "review-input-recovery",
                "a second normal review without an intervening repair is forbidden evidence recovery",
            )

        verdict = event.get("verdict")
        if verdict not in REVIEW_VERDICTS:
            reject("review-verdict", "review verdict is not canonical")
        if diff_kind == "unavailable":
            if any(
                (
                    diff.get("artifact") is not None,
                    diff.get("generation") is not None,
                    bool(changed_files),
                )
            ):
                reject(
                    "review-diff",
                    "unavailable diff must not fabricate an artifact, generation, or changed files",
                )
            if verdict != "blocked":
                reject(
                    "review-no-diff-approval",
                    "approval requires the actual latest diff; unavailable diff must block",
                )
        elif diff_kind in {"actual-diff", "host-native-actual-diff"}:
            if diff.get("generation") != generation:
                reject(
                    "review-old-diff",
                    "review requires the actual latest diff generation after the latest modification",
                )
            elif diff_kind == "actual-diff" and (
                _unified_diff_paths(diff.get("artifact")) != changed_files
            ):
                reject(
                    "review-diff-payload",
                    "review must consume delivered unified-diff content or a current native change reference",
                )
            elif diff_kind == "host-native-actual-diff" and not (
                _native_change_reference_bound(
                    diff.get("artifact"),
                    changed_files,
                    generation,
                    "review-agent",
                )
            ):
                reject(
                    "review-diff-payload",
                    "review must consume delivered unified-diff content or a current native change reference",
                )
            if not changed_files:
                reject("review-changed-files", "actual diff must declare changed files")

        if validation_source == "trajectory-validation":
            evidence_id = validation.get("evidence_id")
            validation_steps = [
                (index, step)
                for index, step in enumerate(steps[:event_index])
                if step.get("actor") == "task-agent"
                and step.get("action") == "validate"
                and step.get("evidence_id") == evidence_id
            ]
            latest_edit_index = material_since_review[-1][0] if material_since_review else -1
            if (
                len(validation_steps) != 1
                or not latest_edit_index < validation_steps[0][0] < event_index
                or validation_steps[0][1].get("outcome") != "passed"
                or validation_result != "passed"
                or validation.get("generation") != generation
            ):
                reject(
                    "review-stale-validation",
                    "review requires fresh passing validation after the latest material edit",
                )
        elif validation_source == "supplied-validation":
            if material_since_review:
                reject(
                    "review-stale-validation",
                    "a trace with material edits requires bound trajectory validation",
                )
            if (
                not isinstance(validation.get("evidence_id"), str)
                or not validation["evidence_id"].strip()
                or validation_result != "passed"
                or validation.get("generation") != generation
            ):
                reject(
                    "review-stale-validation",
                    "supplied validation must be current and passing",
                )
        else:
            if verdict != "blocked" or validation_result != "unavailable":
                reject(
                    "review-stale-validation",
                    "unavailable validation requires a blocked verdict",
                )

        if required_review_kind == "repair":
            latest_material = material_since_review[-1] if material_since_review else None
            if latest_material is None or latest_material[1].get("action") != "repair":
                reject(
                    "review-repair-order",
                    "repair review requires repair, fresh validation, latest actual diff, then fresh re-review",
                )
            if diff_kind not in {"actual-diff", "host-native-actual-diff"}:
                reject(
                    "review-repair-order",
                    "repair review requires the latest actual diff before fresh re-review",
                )
            repair_validation = [
                index
                for index, step in enumerate(steps)
                if latest_material is not None
                and latest_material[0] < index < event_index
                and step.get("actor") == "task-agent"
                and step.get("action") == "validate"
                and step.get("evidence_id") == validation.get("evidence_id")
                and step.get("outcome") == "passed"
            ]
            if len(repair_validation) != 1:
                reject(
                    "review-repair-order",
                    "repair requires fresh validation, latest actual diff, then fresh re-review",
                )

        if verdict == "pass" and any(
            value in {"finding", "blocked"} for value in dimension_values
        ) or verdict == "pass" and any(
            value in {"finding", "blocked"} for value in professional_statuses
        ):
            reject(
                "review-verdict",
                "pass cannot override a finding or blocked review dimension",
            )
        if verdict in {"pass", "findings"} and evidence_source != "independent-review":
            reject(
                "review-independence",
                "a non-blocked verdict requires independent review evidence",
            )
        if (
            verdict == "blocked"
            and dimensions
            and "blocked" not in dimension_values
            and "blocked" not in professional_statuses
        ):
            reject(
                "review-verdict",
                "blocked verdict must identify at least one blocked review dimension",
            )
        if professional_matrix_errors and verdict != "blocked":
            reject(
                "review-verdict",
                "an invalid professional-risk matrix must block the verdict",
            )

        prior_review_index = review_index

    final_material_index = max(
        (
            index
            for index, step in enumerate(steps)
            if step.get("actor") in {"task-agent", "review-agent"}
            and step.get("action") in EDIT_ACTIONS
        ),
        default=-1,
    )
    final_review_index = review_actions[-1][0] if review_actions else -1
    if final_material_index > final_review_index:
        reject(
            "review-old-diff",
            "older review cannot cover a modification made after that review",
        )
    first_review_index = review_actions[0][0] if review_actions else len(steps)
    if any(
        index > first_review_index
        and step.get("actor") == "task-agent"
        and step.get("action") == "export-diff"
        for index, step in enumerate(steps)
    ):
        reject(
            "review-input-post-review-recovery",
            "normal post-review diff recovery and Task→Review→Task→Review are forbidden",
        )
    unconsumed_handoffs = [
        index
        for index, step in enumerate(steps)
        if step.get("actor") == "task-agent"
        and step.get("action") == IMPLEMENTATION_HANDOFF_ACTION
        and index not in consumed_handoff_indices
    ]
    unconsumed_gates = [
        index
        for index, step in enumerate(steps)
        if step.get("actor") == "main-control-agent"
        and step.get("action") == REVIEW_INPUT_READY_ACTION
        and index not in consumed_gate_indices
    ]
    if unconsumed_handoffs or unconsumed_gates:
        reject(
            "review-input-occurrence",
            "every normal Implementation Handoff and Main readiness gate occurrence "
            "must be uniquely consumed by its material generation before review dispatch; "
            f"unconsumed_handoffs={unconsumed_handoffs}, "
            f"unconsumed_gates={unconsumed_gates}",
        )
    return list(dict.fromkeys(errors))


def _review_fixture_steps(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Build one compact deterministic typed trace from a declared fixture mutation."""

    case_id = str(case["id"])
    level = case["level"]
    mutation = case["mutation"]
    decisions = {dimension: "verified" for dimension in REVIEW_BASE_DIMENSIONS}
    professional_risks = [
        {
            "dimension": dimension,
            "status": "verified",
            "reason": f"inspected {dimension} for the bounded review",
            "evidence": f"{case_id}:{dimension}:source",
            "specialist_skill": "not-applicable",
            "scope": "not-applicable",
        }
        for dimension in REVIEW_PROFESSIONAL_RISK_DIMENSIONS
    ]
    event: dict[str, Any] = {
        "actor": "review-agent",
        "action": REVIEW_DISCIPLINE_ACTION,
        "schema_version": REVIEW_DISCIPLINE_MODEL["schema_version"],
        "task_id": case_id,
        "execution_level": level,
        "review_kind": "implementation",
        "diff": {
            "kind": "actual-diff",
            "artifact": "diff --git a/owner.py b/owner.py\n--- a/owner.py\n+++ b/owner.py\n@@ -1 +1 @@\n-old\n+new\n",
            "generation": 1,
            "changed_files": ["owner.py"],
        },
        "validation": {
            "source": "trajectory-validation",
            "evidence_id": f"{case_id}-validation",
            "result": "passed",
            "generation": 1,
        },
        "evidence_source": "independent-review",
        "dimensions": decisions,
        "professional_risks": professional_risks,
        "verdict": "pass",
    }
    edit: dict[str, Any] = {
        "actor": "task-agent",
        "action": "edit",
        "task_id": case_id,
        "path": "owner.py",
    }
    validation: dict[str, Any] = {
        "actor": "task-agent",
        "action": "validate",
        "task_id": case_id,
        "command": "targeted-test",
        "evidence_id": f"{case_id}-validation",
        "outcome": "passed",
    }
    review: dict[str, Any] = {
        "actor": "review-agent",
        "action": "review",
        "changed_paths": ["owner.py"],
    }
    handoff_id = f"{case_id}:implementation-handoff:1"
    handoff: dict[str, Any] = {
        "actor": "task-agent",
        "action": IMPLEMENTATION_HANDOFF_ACTION,
        "handoff_id": handoff_id,
        "task_id": case_id,
        "latest_changed_paths": ["owner.py"],
        "exact_change_evidence": {
            "kind": "exact-change-content",
            "artifact": "diff --git a/owner.py b/owner.py\n--- a/owner.py\n+++ b/owner.py\n@@ -1 +1 @@\n-old\n+new\n",
            "generation": 1,
        },
        "reviewer_capability_accessibility": {
            "native-change-read": "unsupported",
            "change-evidence-export": "supported",
            "supplied-change-delivery": "supported",
            "reviewer-change-consume": "supported",
            "non-mutating-validation": "supported",
        },
        "validation_after_latest_material_edit": {
            "evidence_id": f"{case_id}-validation",
            "result": "passed",
            "generation": 1,
        },
        "fixed_review_scope": ["owner.py"],
    }
    gate: dict[str, Any] = {
        "actor": "main-control-agent",
        "action": REVIEW_INPUT_READY_ACTION,
        "handoff_id": handoff_id,
        "ready": True,
    }
    dispatch: dict[str, Any] = {
        "actor": "main-control-agent",
        "action": "dispatch",
        "profile": "review-agent",
        "primary_skill": "ai-code-review-refactor",
        "review_input_binding": {
            "handoff_id": handoff_id,
            "artifact": "diff --git a/owner.py b/owner.py\n--- a/owner.py\n+++ b/owner.py\n@@ -1 +1 @@\n-old\n+new\n",
            "generation": 1,
        },
    }
    capture = {
        "actor": "task-agent",
        "action": "capture-change-evidence",
        "task_id": case_id,
        "artifact": handoff["exact_change_evidence"]["artifact"],
        "generation": 1,
        "changed_paths": ["owner.py"],
    }
    artifact_read = {
        "actor": "review-agent",
        "action": "read",
        "artifact_ref": handoff["exact_change_evidence"]["artifact"],
    }
    steps = [edit, validation, capture, handoff, gate, dispatch, artifact_read, event, review]
    mutation_kind = mutation.get("kind")
    if mutation_kind == "none":
        return steps
    if mutation_kind == "drop-dimension":
        decisions.pop(mutation["dimension"], None)
    elif mutation_kind == "missing-professional-dimension":
        professional_risks.pop()
    elif mutation_kind == "unsupported-professional-status":
        professional_risks[0]["status"] = "skipped"
    elif mutation_kind == "unevidenced-not-applicable":
        professional_risks[0].update(
            {"status": "not-applicable", "reason": "", "evidence": ""}
        )
    elif mutation_kind == "incomplete-delegation":
        professional_risks[0].update(
            {
                "status": "delegated",
                "reason": "",
                "evidence": "delegation requested",
                "specialist_skill": "",
                "scope": "",
            }
        )
    elif mutation_kind == "duplicate-professional-dimension":
        professional_risks.append(copy.deepcopy(professional_risks[0]))
    elif mutation_kind == "diff-summary":
        event["diff"]["kind"] = "changed-file-summary"
        event["diff"]["artifact"] = "changed-files.txt"
    elif mutation_kind in {"no-diff-approval", "non-code-no-diff-blocked"}:
        event["diff"] = {
            "kind": "unavailable",
            "artifact": None,
            "generation": None,
            "changed_files": [],
        }
        event["validation"] = {
            "source": "unavailable",
            "evidence_id": None,
            "result": "unavailable",
            "generation": None,
        }
        event["evidence_source"] = "unavailable"
        review["changed_paths"] = []
        steps = [event, review]
        if mutation_kind == "non-code-no-diff-blocked":
            event["dimensions"] = {
                dimension: "blocked" for dimension in REVIEW_BASE_DIMENSIONS
            }
            for decision in professional_risks:
                decision["status"] = "blocked"
            event["verdict"] = "blocked"
    elif mutation_kind in {"reviewer-edit", "reviewer-repair"}:
        steps.insert(
            2,
            {
                "actor": "review-agent",
                "action": "edit" if mutation_kind == "reviewer-edit" else "repair",
                "task_id": case_id,
                "path": "owner.py",
            },
        )
    elif mutation_kind == "implementer-reasoning":
        event["evidence_source"] = "implementer-reasoning"
    elif mutation_kind == "stale-validation":
        event["validation"]["generation"] = 0
    elif mutation_kind == "old-diff":
        event["diff"]["generation"] = 0
    elif mutation_kind == "repair-as-implementation":
        edit["action"] = "repair"
    elif mutation_kind == "repair-order":
        edit["action"] = "repair"
        event["review_kind"] = "repair"
        review["action"] = "re-review"
        steps = [edit, event, validation, review]
    else:
        raise ValueError(f"unknown review-discipline mutation {mutation_kind!r}")
    return steps


def _review_discipline_fixture_results(
    cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(cases, list) or not cases:
        return [], ["review_discipline_cases must be a non-empty list"]
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    level_dimension_sets: dict[str, tuple[str, ...]] = {}
    level_professional_dimension_sets: dict[str, tuple[str, ...]] = {}
    for case in cases:
        if not isinstance(case, dict) or tuple(case) != (
            "id",
            "expected_valid",
            "expected_error",
            "level",
            "mutation",
        ):
            errors.append("review-discipline fixture must use the exact compact shape")
            continue
        case_id = case.get("id")
        expected_valid = case.get("expected_valid")
        expected_error = case.get("expected_error")
        level = case.get("level")
        mutation = case.get("mutation")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in seen
            or not isinstance(expected_valid, bool)
            or (expected_error is not None and not isinstance(expected_error, str))
            or level not in REVIEW_DISCIPLINE_MODEL["level_base_dimensions"]
            or not isinstance(mutation, dict)
            or not isinstance(mutation.get("kind"), str)
        ):
            errors.append(f"{case_id!r}: review-discipline fixture shape is invalid")
            continue
        seen.add(case_id)
        try:
            steps = _review_fixture_steps(case)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{case_id}: invalid review-discipline mutation: {exc}")
            continue
        fixture_errors = _review_discipline_errors(case_id, steps)
        actual_valid = not fixture_errors
        matches_expected = actual_valid == expected_valid and (
            expected_error is None
            or any(expected_error in error for error in fixture_errors)
        )
        if case_id.startswith("review-level-"):
            event = next(
                step for step in steps if step.get("action") == REVIEW_DISCIPLINE_ACTION
            )
            level_dimension_sets[str(level)] = tuple(event["dimensions"])
            level_professional_dimension_sets[str(level)] = tuple(
                decision["dimension"] for decision in event["professional_risks"]
            )
        results.append(
            {
                "id": case_id,
                "level": level,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": matches_expected,
                "errors": fixture_errors,
            }
        )
        if not matches_expected:
            errors.append(
                f"{case_id}: review-discipline result does not match expectation: "
                f"{fixture_errors}"
            )
    expected_levels = {"L1", "L2", "L3", "L4", "L5"}
    if set(level_dimension_sets) != expected_levels or set(
        level_dimension_sets.values()
    ) != {REVIEW_BASE_DIMENSIONS}:
        errors.append(
            "review-discipline level fixtures must prove one identical base-dimension set at L1-L5"
        )
    if set(level_professional_dimension_sets) != expected_levels or set(
        level_professional_dimension_sets.values()
    ) != {REVIEW_PROFESSIONAL_RISK_DIMENSIONS}:
        errors.append(
            "review-discipline level fixtures must prove all professional-risk "
            "dimensions at L1-L5"
        )
    return results, errors


def _task_focus_error(case_id: str, code: str, message: str) -> str:
    return f"{case_id}: [{code}] {message}"


def _task_focus_case_errors(case: object) -> list[str]:
    """Reject authority, scope, review-depth, repair, and ordinary-cost drift."""

    if not isinstance(case, dict):
        return ["task-focus case must be a mapping"]
    case_id = str(case.get("id") or "<missing>")
    errors: list[str] = []

    def reject(code: str, message: str) -> None:
        errors.append(_task_focus_error(case_id, code, message))

    if tuple(case) != (
        "id",
        "scenario",
        "inputs",
        "decision",
        "expected_valid",
        "expected_error",
    ):
        reject("focus-shape", "task-focus case must use the exact compact shape")
        return errors
    scenario = case.get("scenario")
    inputs = case.get("inputs")
    decision = case.get("decision")
    if scenario not in {
        "finding",
        "same-pattern",
        "repair",
        "review-level",
        "cost",
        "analysis-level",
        "review-readiness",
        "capability-equivalence",
    }:
        reject("focus-scenario", "task-focus scenario is not in the closed set")
        return errors
    if not isinstance(inputs, dict) or not isinstance(decision, dict):
        reject("focus-shape", "task-focus inputs and decision must be mappings")
        return errors

    if scenario == "analysis-level":
        if tuple(inputs) != (
            "route_path",
            "analysis_assignment_has_level",
            "analysis_historical_max_before",
            "analysis_historical_max_after",
            "l2_all_true",
            "material_risk",
            "explicit_l5",
        ) or tuple(decision) != (
            "analysis_level",
            "task_level",
            "level_computation_point",
        ):
            reject("analysis-level-shape", "analysis-level fields are not canonical")
            return errors
        route_path = inputs["route_path"]
        if route_path not in {"analyzed", "direct"}:
            reject("analysis-level-path", "route_path must be analyzed or direct")
            return errors
        if any(
            type(inputs[field]) is not bool
            for field in (
                "analysis_assignment_has_level",
                "l2_all_true",
                "material_risk",
                "explicit_l5",
            )
        ):
            reject("analysis-level-shape", "analysis-level predicates must be booleans")
            return errors
        before = inputs["analysis_historical_max_before"]
        after = inputs["analysis_historical_max_after"]
        if before not in {None, "L1", "L2", "L3", "L4", "L5"} or after not in {
            None,
            "L1",
            "L2",
            "L3",
            "L4",
            "L5",
        }:
            reject("analysis-level-history", "historical levels must be null or L1-L5")
            return errors
        if route_path == "analyzed":
            if inputs["analysis_assignment_has_level"] or decision["analysis_level"] is not None:
                reject("analysis-level-present", "Analysis must not carry an Execution Level")
            if after != before:
                reject("analysis-history", "Analysis must not change historical max")
            expected_point = "first-executable-slice"
        else:
            if inputs["analysis_assignment_has_level"] or decision["analysis_level"] is not None:
                reject("analysis-level-present", "Direct Task has no Analysis assignment")
            expected_point = "direct-executable-task"
        computed = (
            "L5"
            if inputs["explicit_l5"]
            else "L4"
            if inputs["material_risk"]
            else "L2"
            if inputs["l2_all_true"]
            else "L3"
        )
        if before is not None and int(before[1:]) > int(computed[1:]):
            computed = before
        if decision["task_level"] != computed:
            reject("task-level", "executable Task Level does not follow L2/L3/L4/L5 policy")
        if decision["level_computation_point"] != expected_point:
            reject("level-timing", "Execution Level must be computed at the executable Task")

    elif scenario == "review-readiness":
        if tuple(inputs) != (
            "handoff_kind",
            "latest_changed_paths",
            "change_evidence_kind",
            "change_evidence_artifact",
            "native-change-read",
            "change-evidence-export",
            "supplied-change-delivery",
            "reviewer-change-consume",
            "non-mutating-validation",
            "validation_generation",
            "latest_material_edit_generation",
            "review_scope_fixed",
            "reviewer_mutation_capability",
            "reviewer_execute_capability",
            "workspace-state-observation",
            "post_review_change_export",
        ) or tuple(decision) != (
            "review_input_ready",
            "review_dispatches",
            "legacy_recovery_attempts",
            "completion",
        ):
            reject("review-readiness-shape", "review-readiness fields are not canonical")
            return errors
        if inputs["handoff_kind"] not in {"normal", "legacy-incomplete"}:
            reject("review-handoff-kind", "handoff kind is not canonical")
            return errors
        bool_fields = (
            "latest_changed_paths",
            "review_scope_fixed",
            "reviewer_mutation_capability",
            "reviewer_execute_capability",
            "post_review_change_export",
        )
        if any(type(inputs[field]) is not bool for field in bool_fields):
            reject("review-readiness-shape", "review-readiness predicates must be booleans")
            return errors
        for field in (
            "native-change-read",
            "change-evidence-export",
            "supplied-change-delivery",
            "reviewer-change-consume",
            "non-mutating-validation",
            "workspace-state-observation",
        ):
            if inputs[field] not in GENERIC_CAPABILITY_STATES:
                reject("review-capability-state", "capability state must be supported or unsupported")
        if not all(
            isinstance(inputs[field], int) and inputs[field] >= 0
            for field in ("validation_generation", "latest_material_edit_generation")
        ):
            reject("review-generation", "review generations must be non-negative integers")
            return errors
        ready = (
            inputs["latest_changed_paths"]
            and _exact_change_evidence_accessible(
                inputs["change_evidence_kind"],
                inputs["change_evidence_artifact"],
                ["owner.py"],
                inputs,
                current_generation=inputs["latest_material_edit_generation"],
            )
            and inputs["non-mutating-validation"] == "supported"
            and inputs["validation_generation"]
            == inputs["latest_material_edit_generation"]
            and inputs["review_scope_fixed"]
        )
        if inputs["reviewer_mutation_capability"]:
            reject("reviewer-read-only", "reviewer must remain read-only")
        expected_recovery = 0
        if (
            not ready
            and inputs["handoff_kind"] == "legacy-incomplete"
            and inputs["change-evidence-export"] == "supported"
            and inputs["workspace-state-observation"] == "supported"
        ):
            expected_recovery = 1
        expected_dispatches = 1 if ready else 0
        expected_completion = "ready-for-review" if ready else "blocked-before-review"
        if decision["review_input_ready"] is not ready:
            reject("review-readiness", "Review Input Ready is derived from all five preflight facts")
        if decision["review_dispatches"] != expected_dispatches:
            reject("review-dispatch", "missing Review Input Ready must dispatch zero reviewers")
        if decision["legacy_recovery_attempts"] != expected_recovery:
            reject("review-recovery", "only legacy incomplete handoff permits one pre-review recovery")
        if decision["completion"] != expected_completion:
            reject("review-completion", "completion must fail closed before Review")
        if inputs["post_review_change_export"]:
            reject("post-review-export", "change export after Review dispatch is forbidden")

    elif scenario == "capability-equivalence":
        if tuple(inputs) != ("adapters",) or tuple(decision) != ("results",):
            reject("capability-equivalence-shape", "capability-equivalence fields are not canonical")
            return errors
        adapters = inputs["adapters"]
        results_value = decision["results"]
        if (
            not isinstance(adapters, list)
            or len(adapters) != 2
            or not isinstance(results_value, list)
            or len(results_value) != 2
        ):
            reject("capability-equivalence-shape", "exactly two adapters and decisions are required")
            return errors
        adapter_fields = ("adapter_metadata", "capabilities")
        result_fields = ("routing", "execution_level", "review_required", "completion")
        if any(not isinstance(item, dict) or tuple(item) != adapter_fields for item in adapters):
            reject("capability-adapter-shape", "adapter metadata fields are not canonical")
            return errors
        if any(not isinstance(item, dict) or tuple(item) != result_fields for item in results_value):
            reject("capability-result-shape", "capability decision fields are not canonical")
            return errors
        if adapters[0]["capabilities"] != adapters[1]["capabilities"]:
            reject("capability-state", "equivalence fixture requires equal capability facts")
        if any(not isinstance(item["adapter_metadata"], dict) for item in adapters):
            reject("adapter-metadata", "adapter metadata must be a mapping")
        elif adapters[0]["adapter_metadata"] == adapters[1]["adapter_metadata"]:
            reject("adapter-metadata", "adapter metadata must differ")
        for capabilities in (adapter["capabilities"] for adapter in adapters):
            if (
                not isinstance(capabilities, dict)
                or tuple(capabilities) != GENERIC_CAPABILITY_FIELDS
                or any(state not in GENERIC_CAPABILITY_STATES for state in capabilities.values())
            ):
                reject("capability-state", "capability facts must use the closed states")
        if results_value[0] != results_value[1]:
            reject("capability-decision", "equal capabilities must produce equal control decisions")

    elif scenario == "finding":
        input_fields = (
            "introduced_by_diff",
            "violates_acceptance",
            "violates_invariant_or_contract",
            "required_to_complete",
            "inside_allowed_write_scope",
            "changes_analysis_authority",
            "discovered_in_allowed_read_scope",
            "severity",
        )
        decision_fields = (
            "relation",
            "blocking",
            "repair_started",
            "route",
            "continue_primary_task",
            "repository_clean_required",
        )
        if tuple(inputs) != input_fields or tuple(decision) != decision_fields:
            reject("finding-shape", "finding case fields are not canonical")
            return errors
        bool_fields = input_fields[:-1]
        if any(not isinstance(inputs[field], bool) for field in bool_fields):
            reject("finding-shape", "finding predicates must be booleans")
            return errors
        if inputs["severity"] not in {"Critical", "High", "Medium", "Low"}:
            reject("finding-severity", "finding severity is not canonical")
        current_required = any(
            inputs[field]
            for field in (
                "introduced_by_diff",
                "violates_acceptance",
                "violates_invariant_or_contract",
                "required_to_complete",
            )
        )
        if current_required and (
            not inputs["inside_allowed_write_scope"]
            or inputs["changes_analysis_authority"]
        ):
            expected_relation = "scope-blocker"
        elif current_required:
            expected_relation = "current-task"
        else:
            expected_relation = "adjacent"
        if decision["relation"] != expected_relation:
            reject(
                "finding-relation",
                "Finding Relation must be derived before severity and blocker",
            )
        expected = {
            "current-task": (True, True, "task-agent-repair", False),
            "scope-blocker": (True, False, "main-analysis", False),
            "adjacent": (False, False, "defer-continue", True),
        }[expected_relation]
        observed = (
            decision["blocking"],
            decision["repair_started"],
            decision["route"],
            decision["continue_primary_task"],
        )
        if observed != expected:
            if expected_relation == "adjacent":
                reject(
                    "adjacent-repair",
                    "adjacent findings cannot block or enter repair; record and continue the primary task",
                )
            elif expected_relation == "scope-blocker":
                reject(
                    "scope-blocker-route",
                    "scope-blocker must return blocked through Main to analysis",
                )
            else:
                reject(
                    "current-task-route",
                    "accepted current-task blockers route to task-agent repair",
                )
        if (
            inputs["discovered_in_allowed_read_scope"]
            and not inputs["inside_allowed_write_scope"]
            and decision["repair_started"]
        ):
            reject(
                "read-scope-write",
                "Allowed Read Scope does not grant write authority",
            )
        if decision["repository_clean_required"] is not False:
            reject(
                "repository-clean",
                "current task completion does not require repository-clean",
            )

    elif scenario == "same-pattern":
        if tuple(inputs) != (
            "affects_acceptance_or_invariant",
            "inside_authorized_repair_scope",
        ) or tuple(decision) != (
            "relation",
            "action",
            "blocking",
            "rationale",
            "residual_risk",
        ):
            reject("same-pattern-shape", "same-pattern case fields are not canonical")
            return errors
        if any(not isinstance(value, bool) for value in inputs.values()):
            reject("same-pattern-shape", "same-pattern predicates must be booleans")
            return errors
        affects = inputs["affects_acceptance_or_invariant"]
        inside = inputs["inside_authorized_repair_scope"]
        if affects and inside:
            expected = ("current-task", "fix", True)
        elif affects:
            expected = ("scope-blocker", "return-main", True)
        else:
            expected = ("adjacent", "record-do-not-edit", False)
        if (
            decision["relation"],
            decision["action"],
            decision["blocking"],
        ) != expected:
            reject(
                "same-pattern-authority",
                "same-pattern discovery does not grant repair authorization",
            )
        if expected[0] == "adjacent" and (
            not _meaningful_professional_risk_text(decision["rationale"])
            or not _meaningful_professional_risk_text(decision["residual_risk"])
        ):
            reject(
                "same-pattern-adjacent-evidence",
                "adjacent matches require rationale and residual risk",
            )

    elif scenario == "repair":
        if tuple(inputs) != (
            "finding_relation",
            "accepted_current_task",
            "authorized_changed_files",
            "actual_changed_files",
            "material_edit_generation",
        ) or tuple(decision) != (
            "repair_started",
            "unrelated_file_action",
            "evidence_generations",
            "sequence",
            "continue_primary_task",
        ):
            reject("repair-shape", "repair case fields are not canonical")
            return errors
        relation = inputs["finding_relation"]
        if relation not in FINDING_RELATION_MODEL["values"]:
            reject("repair-relation", "repair finding relation is not canonical")
            return errors
        repair_allowed = relation == "current-task" and inputs["accepted_current_task"] is True
        if decision["repair_started"] is not repair_allowed:
            if relation == "adjacent":
                reject(
                    "adjacent-repair",
                    "adjacent findings cannot block or enter repair; record and continue the primary task",
                )
            else:
                reject(
                    "repair-authority",
                    "only an accepted current-task finding can enter repair",
                )
        authorized = inputs["authorized_changed_files"]
        actual = inputs["actual_changed_files"]
        if (
            not isinstance(authorized, list)
            or not isinstance(actual, list)
            or any(not isinstance(path, str) or not path for path in [*authorized, *actual])
        ):
            reject("repair-files", "repair changed-file lists must contain paths")
            return errors
        unrelated = [path for path in actual if path not in authorized]
        expected_unrelated_action = (
            "revert-unrelated-do-not-repair" if unrelated else "not-applicable"
        )
        if decision["unrelated_file_action"] != expected_unrelated_action:
            reject(
                "repair-unrelated-file",
                "repair must revert the unrelated changed file and must not continue repairing it",
            )
        generation = inputs["material_edit_generation"]
        evidence = decision["evidence_generations"]
        expected_sequence = [
            "fresh-validation",
            "latest-actual-diff",
            "fresh-independent-review",
        ]
        if repair_allowed and (
            not isinstance(generation, int)
            or generation < 1
            or not isinstance(evidence, dict)
            or tuple(evidence) != ("validation", "diff", "review")
            or any(evidence[field] != generation for field in evidence)
            or decision["sequence"] != expected_sequence
        ):
            reject(
                "repair-freshness",
                "repair requires fresh validation, latest actual diff, and fresh independent review after the latest material edit",
            )
        expected_continue = relation == "adjacent"
        if decision["continue_primary_task"] is not expected_continue:
            reject(
                "repair-priority",
                "adjacent discovery must not preempt the current requested task or DAG",
            )

    elif scenario == "review-level":
        if tuple(inputs) != (
            "effective_level",
            "actual_professional_gate",
            "specialist_needed",
            "design_risk_preimplementation",
            "new_high_risk_found",
        ) or tuple(decision) != (
            "final_reviewers",
            "independent_final_review",
            "base_dimensions",
            "jit_lenses",
            "professional_gates",
            "specialist_reviews",
            "preimplementation_reviews",
            "secondary_reviewers",
            "l5_negative_failure_proof",
            "exhaustive_final_review",
            "full_ci_required",
            "formal_release_required",
            "cross_model_review_required",
            "reviewer_upgraded_execution_level",
            "escalation_route",
        ):
            reject("review-policy-shape", "review-level case fields are not canonical")
            return errors
        level = inputs["effective_level"]
        if level not in REVIEW_LEVEL_POLICY["levels"]:
            reject("review-level", "review depth must derive from Effective Level")
            return errors
        actual_gate = inputs["actual_professional_gate"] is True
        specialist_needed = inputs["specialist_needed"] is True
        design_risk = inputs["design_risk_preimplementation"] is True
        high_risk = inputs["new_high_risk_found"] is True
        expected_pre = 1 if level == "L5" or (level == "L4" and design_risk) else 0
        expected_jit = 1 if level == "L3" and actual_gate else 0
        expected_gates = 1 if level in {"L4", "L5"} and actual_gate else 0
        expected_specialists = (
            1 if level in {"L4", "L5"} and actual_gate and specialist_needed else 0
        )
        if decision["final_reviewers"] != 1 or decision["independent_final_review"] is not True:
            reject("review-final", "every level requires one independent final review")
        if decision["base_dimensions"] != list(REVIEW_BASE_DIMENSIONS):
            reject("review-base", "Level may add depth but cannot remove base review dimensions")
        if decision["jit_lenses"] != expected_jit:
            reject("review-l3-jit", "L3 loads review lenses only for concrete risk")
        if decision["professional_gates"] != expected_gates:
            reject("review-gates", "L4/L5 professional gates are actual-risk triggered")
        if decision["specialist_reviews"] != expected_specialists:
            reject(
                "review-specialist",
                "specialist review requires concrete risk and does not replace final review",
            )
        if decision["preimplementation_reviews"] != expected_pre:
            if level == "L4":
                reject(
                    "review-l4-prereview",
                    "L4 does not default to pre-implementation review",
                )
            else:
                reject("review-l5-prereview", "L5 retains independent pre-implementation review")
        if decision["secondary_reviewers"] != 0:
            reject("review-secondary", "Effective Level does not default to a secondary reviewer")
        l5 = level == "L5"
        if (
            decision["l5_negative_failure_proof"] is not l5
            or decision["exhaustive_final_review"] is not l5
        ):
            reject("review-l5-proof", "L5 retains declared-scope failure proof and exhaustive review")
        if any(
            decision[field] is not False
            for field in (
                "full_ci_required",
                "formal_release_required",
                "cross_model_review_required",
            )
        ):
            reject(
                "review-l5-expansion",
                "L5 does not automatically require full CI, formal release, or cross-model review",
            )
        expected_route = REVIEW_LEVEL_POLICY["new_high_risk_route"] if high_risk else []
        if (
            decision["reviewer_upgraded_execution_level"] is not False
            or decision["escalation_route"] != expected_route
        ):
            reject(
                "review-high-risk-route",
                "new L4/L5 risk must return blocked through Main and analysis; reviewer cannot self-upgrade",
            )

    elif scenario == "cost":
        if tuple(inputs) != ("effective_levels",) or tuple(decision) != (
            "agent_count_increase",
            "review_round_increase",
            "adjacent_repair_loops",
            "untriggered_external_reads",
            "always_loaded_prompt_growth",
        ):
            reject("cost-shape", "cost case fields are not canonical")
            return errors
        if inputs["effective_levels"] != ["L1", "L2", "L3"]:
            reject("cost-levels", "ordinary cost fixture must cover L1-L3")
        if any(decision[field] != 0 for field in decision):
            reject(
                "ordinary-cost",
                "ordinary L1-L3 agent and review rounds, adjacent repair loops, untriggered external reads, and always-loaded prompt growth must not increase",
            )
    return list(dict.fromkeys(errors))


def _task_focus_fixture_results(
    cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(cases, list) or not cases:
        return [], ["task_focus_cases must be a non-empty list"]
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("id") if isinstance(case, dict) else "")
        if not case_id or case_id in seen:
            errors.append(f"missing or duplicate task-focus case id: {case_id!r}")
            continue
        seen.add(case_id)
        expected_valid = case.get("expected_valid")
        expected_error = case.get("expected_error")
        if not isinstance(expected_valid, bool) or (
            expected_error is not None and not isinstance(expected_error, str)
        ):
            errors.append(f"{case_id}: task-focus expectation is invalid")
            continue
        case_errors = _task_focus_case_errors(case)
        actual_valid = not case_errors
        matches_expected = actual_valid == expected_valid and (
            expected_error is None
            or any(expected_error in error for error in case_errors)
        )
        results.append(
            {
                "id": case_id,
                "scenario": case.get("scenario"),
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": matches_expected,
                "errors": case_errors,
            }
        )
        if not matches_expected:
            errors.append(
                f"{case_id}: task-focus result does not match expectation: {case_errors}"
            )
    return results, errors


def _orchestration_parallel_isolation(
    events: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Derive orchestration write isolation from optional event scheduling facts."""

    fact_fields = {
        "parallel_batch",
        "workspace",
        "workspace_isolation",
        "write_scope",
    }
    scheduled = [
        event
        for event in events
        if isinstance(event, dict)
        and event.get("action") in {"edit", "repair"}
        and any(field in event for field in fact_fields)
    ]
    if not scheduled:
        return "serialized-events", []

    errors: list[str] = []
    projected_dispatches: list[dict[str, Any]] = []
    batch_counts: dict[str, int] = {}
    for event in scheduled:
        if not fact_fields <= set(event):
            errors.append(
                "parallel material events require batch, workspace, isolation, and write-scope facts"
            )
            continue
        batch = event.get("parallel_batch")
        if not isinstance(batch, str) or not batch:
            errors.append("parallel material event batch must be non-empty text")
            continue
        batch_counts[batch] = batch_counts.get(batch, 0) + 1
        projected_dispatches.append(
            {
                "action": "dispatch",
                "parallel_batch": batch,
                "workspace": event.get("workspace"),
                "workspace_isolation": event.get("workspace_isolation"),
                "write_scope": event.get("write_scope"),
            }
        )
    if any(count < 2 for count in batch_counts.values()):
        errors.append("parallel material event batch must contain at least two writes")
    conflict, reduction = _parallel_metrics(projected_dispatches)
    if conflict:
        errors.append(
            "parallel writes require distinct host-provided isolated workspaces and non-overlapping scopes"
        )
    return (
        "isolated-parallel-events" if reduction > 0 and not errors else "invalid-parallel-events",
        list(dict.fromkeys(errors)),
    )


def _retained_semantic_projection(trace: dict[str, Any]) -> dict[str, Any]:
    """Select bounded control semantics for the independent retained fixture oracle."""

    validation = trace.get("validation", {})
    completion = trace.get("completion", {})
    return {
        "work_kind": trace.get("work_kind"),
        "analysis": trace.get("analysis"),
        "task_dispatch": trace.get("task_dispatch"),
        "validation": {
            "fresh_count": validation.get("fresh_count"),
            "reuse_count": validation.get("reuse_count"),
            "rerun_count": validation.get("rerun_count"),
        },
        "review_boundary": trace.get("review_boundary"),
        "review": trace.get("review"),
        "repair_flow": trace.get("repair_flow"),
        "parallel_isolation": trace.get("parallel_isolation"),
        "completion": {
            "state": completion.get("state"),
            "current_evidence": completion.get("current_evidence"),
            "current_validation_task_ids": completion.get(
                "current_validation_task_ids"
            ),
            "current_review_task_ids": completion.get("current_review_task_ids"),
        },
    }


def _orchestration_case_result(
    case: object,
) -> tuple[list[str], dict[str, Any]]:
    """Reduce ordered orchestration events into errors and a bounded semantic trace."""

    if not isinstance(case, dict):
        return ["orchestration case must be a mapping"], {}
    case_id = str(case.get("id") or "<missing>")
    errors: list[str] = []

    def reject(code: str, message: str) -> None:
        errors.append(f"{case_id}: [{code}] {message}")

    def valid_scope_list(value: object) -> bool:
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and bool(item.strip()) for item in value)
        )

    tasks = case.get("tasks")
    boundary = case.get("review_boundary")
    events = case.get("events")
    if (
        not isinstance(tasks, list)
        or not tasks
        or not isinstance(boundary, dict)
        or not isinstance(events, list)
        or not events
    ):
        reject(
            "orchestration-shape",
            "tasks, review_boundary, and events must be non-empty structural values",
        )
        return errors, {}

    task_ids: list[str] = []
    task_skills: dict[str, str] = {}
    task_review_skills: dict[str, set[str]] = {}
    task_layer3_skills: dict[str, set[str]] = {}
    task_dependencies: dict[str, list[str]] = {}
    professional, layer3_entries = _skill_registries()
    manifests, manifest_errors = _load_build_manifests()
    if manifest_errors:
        reject("skill-built-delivery", "; ".join(manifest_errors))

    def built_professional(skill: str) -> bool:
        return bool(manifests) and all(
            skill in manifest.get("professional_skills", [])
            for manifest in manifests.values()
        )

    def built_layer3(primary: str, skill: str) -> bool:
        return bool(manifests) and all(
            skill in manifest.get("top_level_skills", [])
            or skill
            in manifest.get("compiled_layer3_references", {}).get(primary, [])
            for manifest in manifests.values()
        )

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            reject("task-semantic-boundary", f"task {index} must be a mapping")
            continue
        task_id = task.get("id")
        primary_skill = task.get("primary_skill")
        if not isinstance(task_id, str) or not task_id or task_id in task_ids:
            reject("task-semantic-boundary", "Task IDs must be non-empty and unique")
            continue
        task_ids.append(task_id)
        if not isinstance(primary_skill, str) or not primary_skill:
            reject(
                "task-primary-skill",
                "each Task must retain exactly one Primary Professional Skill",
            )
            continue
        task_skills[task_id] = primary_skill
        primary_entry = professional.get(primary_skill)
        if primary_entry is None:
            reject("task-skill-registry", f"unknown Task Primary Skill {primary_skill!r}")
        elif "task-agent" not in primary_entry.get("role_support", []):
            reject(
                "task-skill-role",
                f"Task Primary Skill {primary_skill!r} does not support task-agent",
            )
        elif not built_professional(primary_skill):
            reject(
                "skill-built-delivery",
                f"Task Primary Skill {primary_skill!r} is not delivered by every build",
            )
        split_reason = task.get("split_reason")
        if split_reason in {"file", "function", "code-layer", "test", "edit-step"}:
            reject(
                "task-semantic-boundary",
                "Task splitting cannot be based only on files, functions, layers, tests, or edit steps",
            )
        review_skills = task.get("review_skills", [])
        if not isinstance(review_skills, list) or any(
            not isinstance(skill, str) or not skill for skill in review_skills
        ):
            reject("review-skill-preservation", "task review_skills must be text values")
            review_skills = []
        task_review_skills[task_id] = set(review_skills)
        for review_skill in review_skills:
            review_entry = professional.get(review_skill)
            if review_entry is None:
                reject("review-skill-registry", f"unknown Review Skill {review_skill!r}")
            elif "review-agent" not in review_entry.get("role_support", []):
                reject(
                    "review-skill-routing",
                    f"Review Skill {review_skill!r} does not support review-agent",
                )
            elif not built_professional(review_skill):
                reject(
                    "skill-built-delivery",
                    f"Review Skill {review_skill!r} is not delivered by every build",
                )
        layer3_skills = task.get("layer3_skills", [])
        if (
            not isinstance(layer3_skills, list)
            or len(layer3_skills) > 3
            or any(not isinstance(skill, str) or not skill for skill in layer3_skills)
            or len(layer3_skills) != len(set(layer3_skills))
        ):
            reject(
                "task-layer3-routing",
                "each Task must select zero to three unique Layer 3 Skills",
            )
            layer3_skills = []
        task_layer3_skills[task_id] = set(layer3_skills)
        dependencies = task.get("dependencies", [])
        if (
            not isinstance(dependencies, list)
            or any(not isinstance(item, str) or not item for item in dependencies)
            or len(dependencies) != len(set(dependencies))
        ):
            reject(
                "delta-impact-closure",
                "Task dependencies must be a unique text list for Delta closure",
            )
            dependencies = []
        task_dependencies[task_id] = list(dependencies)
        candidates = set(primary_entry.get("layer3_candidates", [])) if primary_entry else set()
        for layer3_skill in layer3_skills:
            layer3_entry = layer3_entries.get(layer3_skill)
            if layer3_entry is None:
                reject("task-layer3-registry", f"unknown Layer 3 Skill {layer3_skill!r}")
            elif layer3_skill not in candidates:
                reject(
                    "task-layer3-routing",
                    f"Layer 3 Skill {layer3_skill!r} is not routed by {primary_skill!r}",
                )
            elif "task-agent" not in layer3_entry.get("role_support", []):
                reject(
                    "task-layer3-role",
                    f"Layer 3 Skill {layer3_skill!r} does not support task-agent",
                )
            elif not built_layer3(primary_skill, layer3_skill):
                reject(
                    "skill-built-delivery",
                    f"Layer 3 Skill {layer3_skill!r} is not delivered for {primary_skill!r}",
                )

    for task_id, dependencies in task_dependencies.items():
        unknown = [dependency for dependency in dependencies if dependency not in task_ids]
        if unknown or task_id in dependencies:
            reject(
                "delta-impact-closure",
                f"Task {task_id!r} has unknown or self dependencies: {unknown}",
            )

    def transitive_task_impact(roots: list[str]) -> list[str]:
        impacted = {task_id for task_id in roots if task_id in task_ids}
        changed = True
        while changed:
            changed = False
            for task_id in task_ids:
                if task_id in impacted:
                    continue
                if any(
                    dependency in impacted
                    for dependency in task_dependencies.get(task_id, [])
                ):
                    impacted.add(task_id)
                    changed = True
        return [task_id for task_id in task_ids if task_id in impacted]

    core_subsumption = REVIEW_DISCIPLINE_MODEL["obligation_subsumption"]
    boundary_field_keys = tuple(
        REVIEW_DISCIPLINE_MODEL["review_boundary_contract"][
            "legacy_fixture_boundary_fields"
        ]
    )
    required_boundary_fields = set(boundary_field_keys)
    if set(boundary) != required_boundary_fields:
        reject(
            "review-boundary-shape",
            "legacy Review Boundary fixture must retain its compatible eight-field contract",
        )
        return list(dict.fromkeys(errors)), {}
    covered_task_ids = boundary.get("covered_task_ids")
    required_review_skills = boundary.get("required_review_skills")
    primary_review_skill = boundary.get("primary_review_skill")
    required_specialists = boundary.get("specialist_obligations")
    required_scope = boundary.get("required_changed_scope")
    required_risks = boundary.get("professional_risk_dimensions")
    required_validation_binding = boundary.get(
        "required_validation_evidence_binding"
    )
    effective_level = boundary.get("effective_level")
    for value, label in (
        (covered_task_ids, "covered_task_ids"),
        (required_review_skills, "required_review_skills"),
        (required_specialists, "specialist_obligations"),
        (required_risks, "professional_risk_dimensions"),
    ):
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item for item in value
        ) or len(value) != len(set(value)):
            reject("review-boundary-shape", f"{label} must be a unique text list")
    if (
        not isinstance(required_scope, list)
        or not required_scope
        or any(not isinstance(item, str) or not item for item in required_scope)
        or len(required_scope) != len(set(required_scope))
    ):
        reject(
            "review-boundary-scope",
            "Review Boundary required_changed_scope must be a non-empty unique text list",
        )
    if required_validation_binding != core_subsumption[
        "required_validation_evidence_binding"
    ]:
        reject(
            "review-boundary-validation-binding",
            "Review Boundary must require the Core current-generation validation evidence binding",
        )
    if covered_task_ids != task_ids:
        reject(
            "review-boundary-coverage",
            "Review Boundary Covered Task IDs must exactly cover the ordered Task set",
        )
    if effective_level not in {"L1", "L2", "L3", "L4", "L5"}:
        reject("review-boundary-level", "Review Boundary Effective Level is invalid")
    if (
        not isinstance(primary_review_skill, str)
        or not primary_review_skill
        or primary_review_skill not in set(required_review_skills or [])
    ):
        reject(
            "review-boundary-primary-skill",
            "Review Boundary requires exactly one Primary Review Skill included in required Review Skills",
        )
    task_required_review_skills = set().union(*task_review_skills.values())
    if task_required_review_skills and not task_required_review_skills <= set(
        required_review_skills or []
    ):
        reject(
            "review-skill-preservation",
            "combined Review Boundary must preserve every task-required Review Skill",
        )
    for review_skill in required_review_skills or []:
        review_entry = professional.get(review_skill)
        if review_entry is None:
            reject("review-skill-registry", f"unknown Review Skill {review_skill!r}")
        elif "review-agent" not in review_entry.get("role_support", []):
            reject(
                "review-skill-routing",
                f"Review Skill {review_skill!r} does not support review-agent",
            )
        elif not built_professional(review_skill):
            reject(
                "skill-built-delivery",
                f"Review Skill {review_skill!r} is not delivered by every build",
            )
    required_layer3_skills = set().union(*task_layer3_skills.values())

    parallel_isolation, parallel_errors = _orchestration_parallel_isolation(events)
    for message in parallel_errors:
        reject("parallel-write-isolation", message)

    analysis_event_entries = [
        (index, event)
        for index, event in enumerate(events)
        if event.get("action") == "analysis"
    ]
    analysis_events = [event for _index, event in analysis_event_entries]
    initial_events = [
        event for event in analysis_events if event.get("analysis_kind") == "initial"
    ]
    if analysis_events and len(initial_events) != 1:
        reject(
            "analysis-decision-invalidation",
            "Analyzed Work requires exactly one complete initial Analysis",
        )
    if analysis_event_entries and analysis_event_entries[0][1].get("analysis_kind") != "initial":
        reject(
            "analysis-initial-order",
            "the first Analysis event for analyzed work must be initial, never Delta",
        )
    if initial_events:
        initial = initial_events[0]
        target_authority = initial.get("target_authority")
        target_valid = (
            isinstance(target_authority, dict)
            and tuple(target_authority) == (
                "desired_behavior",
                "observable_acceptance",
                "observed_behavior",
                "observed_behavior_role",
            )
            and isinstance(target_authority.get("desired_behavior"), str)
            and bool(target_authority["desired_behavior"].strip())
            and isinstance(target_authority.get("observable_acceptance"), list)
            and bool(target_authority["observable_acceptance"])
            and all(
                isinstance(item, str) and bool(item.strip())
                for item in target_authority["observable_acceptance"]
            )
            and isinstance(target_authority.get("observed_behavior"), str)
            and target_authority.get("observed_behavior_role") == "failure-evidence-only"
            and target_authority.get("desired_behavior")
            != target_authority.get("observed_behavior")
            and target_authority.get("observed_behavior")
            not in target_authority.get("observable_acceptance", [])
        )
        if not target_valid:
            reject(
                "analysis-target-authority",
                "desired behavior and observable Acceptance are target authority; observed behavior is failure evidence only",
            )
        closed_sections = initial.get("brief_closed_sections")
        slice_projection = initial.get("first_executable_slice")
        first_task = tasks[0] if tasks else {}
        slice_valid = (
            closed_sections == CORE_CONTRACTS["task_contract"]["analyzed_work_authority"]["authoritative_sections"]
            and isinstance(slice_projection, dict)
            and tuple(slice_projection) == (
                "task_id",
                "status",
                "professional_skill",
                "layer3_skills",
                "all_required_fields_complete",
            )
            and slice_projection.get("task_id") == first_task.get("id")
            and slice_projection.get("status") == "in_progress"
            and slice_projection.get("professional_skill") == first_task.get("primary_skill")
            and slice_projection.get("layer3_skills") == first_task.get("layer3_skills", [])
            and slice_projection.get("all_required_fields_complete") is True
        )
        if not slice_valid:
            reject(
                "analysis-slice-closure",
                "initial Analysis must close every authoritative Brief section and every non-blocked First Executable Slice field",
            )
    initial_assignments = (
        initial_events[0].get("skill_assignments") if initial_events else None
    )
    if initial_assignments is not None and initial_assignments != task_skills:
        reject(
            "analysis-skill-routing",
            "initial Analysis Skill assignments must match each Task Primary Skill",
        )
    protected_decisions = set(
        CORE_CONTRACTS["task_contract"]["analyzed_work_authority"]["decision_invalidation_triggers"]
    )
    allowed_updates = set(
        CORE_CONTRACTS["task_contract"]["analyzed_work_authority"]["delta_analysis"]["updates"]
    )
    previous_assignments = dict(task_skills)
    previous_analysis_index = -1
    authoritative_brief_sections = CORE_CONTRACTS["task_contract"][
        "analyzed_work_authority"
    ]["authoritative_sections"]
    for event_index, event in analysis_event_entries:
        if event.get("analysis_kind") == "initial":
            previous_analysis_index = event_index
            continue
        if event.get("analysis_kind") != "delta":
            reject("analysis-decision-invalidation", "analysis_kind must be initial or delta")
            continue
        invalidated = event.get("invalidated_decisions")
        updates = event.get("transitive_updates")
        if (
            event.get("protected_decision_invalidated") is not True
            or not isinstance(invalidated, list)
            or not invalidated
            or not set(invalidated) <= protected_decisions
        ):
            reject(
                "analysis-decision-invalidation",
                "Delta Analysis requires a protected decision invalidation",
            )
        if (
            not isinstance(updates, list)
            or not updates
            or not set(updates) <= allowed_updates
            or event.get("analysis_scope") not in {"delta", "full"}
            or (
                event.get("analysis_scope") == "full"
                and event.get("foundational_assumptions_invalidated") is not True
            )
        ):
            reject(
                "delta-analysis-scope",
                "Delta Analysis must update only invalidated decisions and transitive impact",
            )
        routing_trigger = any(
            event.get(field) is True
            for field in (
                "professional_domain_changed",
                "work_type_changed",
                "material_risk_trigger_changed",
            )
        )
        prior_assignments = dict(previous_assignments)
        assignments = event.get("skill_assignments", previous_assignments)
        if not isinstance(assignments, dict) or set(assignments) != set(task_skills):
            reject("analysis-skill-routing", "Delta Skill assignments must cover every Task")
        elif not routing_trigger and assignments != previous_assignments:
            reject(
                "analysis-skill-routing",
                "Skill assignments must be preserved when domain, work type, and material risk are unchanged",
            )
        else:
            previous_assignments = dict(assignments)

        source_task_ids: list[str] = []
        for candidate in events[previous_analysis_index + 1 : event_index]:
            if not isinstance(candidate, dict) or candidate.get("action") not in {
                "edit",
                "repair",
                "finding",
            }:
                continue
            task_id = candidate.get("task_id")
            if task_id in task_ids and task_id not in source_task_ids:
                source_task_ids.append(task_id)
        previous_analysis_index = event_index
        needs_task_closure = bool(
            set(updates or [])
            & {
                "affected-tasks",
                "affected-dependencies",
                "affected-review-boundaries",
            }
        )
        if needs_task_closure and not source_task_ids:
            reject(
                "delta-impact-proof-limit",
                "unknown Delta impact cannot be mapped to []; record a Proof Limit and return blocked",
            )
        impacted_tasks = transitive_task_impact(source_task_ids)
        impacted_dependencies = [
            f"{dependency}->{task_id}"
            for task_id in task_ids
            for dependency in task_dependencies.get(task_id, [])
            if dependency in impacted_tasks and task_id in impacted_tasks
        ]
        rerouted_tasks = [
            task_id
            for task_id in task_ids
            if assignments.get(task_id) != prior_assignments.get(task_id)
        ] if isinstance(assignments, dict) else []
        impacted_review_skills = [
            skill
            for skill in required_review_skills or []
            if any(skill in task_review_skills[task_id] for task_id in impacted_tasks)
        ]
        invalidated_sections = {
            section
            for decision in invalidated or []
            for section in DELTA_BRIEF_SECTIONS_BY_INVALIDATION.get(decision, set())
        }
        mandatory_updates = {
            update
            for update, impacted in (
                ("affected-brief-sections", invalidated_sections),
                ("affected-tasks", impacted_tasks),
                ("affected-dependencies", impacted_dependencies),
                ("affected-skill-assignments", rerouted_tasks),
                ("affected-review-boundaries", impacted_review_skills),
            )
            if impacted
        }
        missing_updates = sorted(mandatory_updates - set(updates or []))
        if missing_updates:
            reject(
                "delta-impact-exact",
                "Delta Analysis must declare every category proven affected by "
                f"impact closure: {missing_updates}",
            )
        expected_delta_impact = {
            "invalidated": invalidated,
            "affected": {
                "brief": [
                    section
                    for section in authoritative_brief_sections
                    if section in invalidated_sections
                ]
                if "affected-brief-sections" in set(updates or [])
                else [],
                "tasks": impacted_tasks
                if "affected-tasks" in set(updates or [])
                else [],
                "dependencies": impacted_dependencies
                if "affected-dependencies" in set(updates or [])
                else [],
                "skills": rerouted_tasks
                if "affected-skill-assignments" in set(updates or [])
                else [],
                "reviews": impacted_review_skills
                if "affected-review-boundaries" in set(updates or [])
                else [],
            },
            "unlisted": "preserved",
        }
        delta_impact = event.get("delta_impact")
        delta_shape_valid = (
            isinstance(delta_impact, dict)
            and tuple(delta_impact) == ("invalidated", "affected", "unlisted")
            and isinstance(delta_impact.get("affected"), dict)
            and tuple(delta_impact["affected"]) == DELTA_IMPACT_FIELDS
            and all(
                isinstance(delta_impact["affected"].get(field), list)
                and all(
                    isinstance(item, str) and item
                    for item in delta_impact["affected"].get(field, [])
                )
                and len(delta_impact["affected"].get(field, []))
                == len(set(delta_impact["affected"].get(field, [])))
                for field in DELTA_IMPACT_FIELDS
            )
        )
        if not delta_shape_valid or delta_impact != expected_delta_impact:
            reject(
                "delta-impact-exact",
                "Delta Impact must exactly project proven invalidated decisions and transitive affected sets; unlisted remains preserved",
            )

    latest_generation: dict[str, int] = {}
    current_validation: set[str] = set()
    current_review: set[str] = set()
    current_validation_evidence: dict[str, str] = {}
    current_review_evidence: dict[str, str] = {}
    validation_evidence: dict[str, tuple[str, int]] = {}
    fresh_validation_evidence_ids: list[str] = []
    reused_validation_evidence_ids: list[str] = []
    validation_rerun_count = 0
    review_ids: set[str] = set()
    review_actions: list[str] = []
    invalidated_claims: set[str] = set()
    covering_review_seen = False
    covering_rereview_seen = False
    repair_seen = False
    pending_repair_findings: dict[str, tuple[str, set[str], set[str]]] = {}
    finding_relations_by_id: dict[str, str] = {}
    seen_finding_ids: set[str] = set()
    repair_review_requirements: dict[str, tuple[set[str], set[str]]] = {}
    repaired_task_ids: set[str] = set()
    repair_invalidated_claims: set[str] = set()
    repair_validated_task_ids: set[str] = set()
    rereviewed_task_ids: set[str] = set()
    repair_count = 0
    terminal_seen = False
    terminal_state = "in-progress"
    allowed_reproduction = set(
        REVIEW_DISCIPLINE_MODEL["validation_evidence_reuse"]["reproduction_triggers"]
    )
    material_categories = set(
        FINDING_RELATION_MODEL["material_current_task_criteria"]
    )
    non_repair_categories = set(
        FINDING_RELATION_MODEL["non_repair_categories"]
    )
    finding_relations = set(FINDING_RELATION_MODEL["values"])
    finding_categories = material_categories | non_repair_categories
    category_risk_terms = {
        "acceptance": {"acceptance", "correctness"},
        "correctness-or-invariant": {"correctness", "invariant"},
        "regression": {"regression", "correctness"},
        "security-or-reliability": {"security", "reliability"},
        "material-code-health": {"code-health", "maintainability"},
    }
    level_rank = {level: index for index, level in enumerate(("L1", "L2", "L3", "L4", "L5"), 1)}

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            reject("orchestration-event", f"event {index} must be a mapping")
            continue
        action = event.get("action")
        if terminal_seen:
            reject("orchestration-terminal", "no orchestration event may follow completion or blocked")
            continue
        if action in {"edit", "repair"}:
            task_id = event.get("task_id")
            generation = event.get("generation")
            if task_id not in task_ids or not isinstance(generation, int) or generation < 1:
                reject("material-edit-validation", "material edits require a Task and generation")
                continue
            if generation <= latest_generation.get(task_id, 0):
                reject("material-edit-validation", "material edit generations must increase")
            latest_generation[task_id] = generation
            current_validation.discard(task_id)
            current_review.discard(task_id)
            current_validation_evidence.pop(task_id, None)
            current_review_evidence.pop(task_id, None)
            invalidated_claims.update(
                {f"validation:{task_id}", f"review:{task_id}"}
            )
            if action == "repair":
                repair_seen = True
                repair_count += 1
                affected = event.get("affected_task_ids", [task_id])
                expansion = event.get("impact_boundaries", [])
                if not isinstance(affected, list) or not set(affected) <= set(task_ids):
                    reject("repair-invalidation-scope", "repair affected_task_ids are invalid")
                    affected = [task_id]
                if expansion and set(affected) == {task_id}:
                    reject(
                        "repair-invalidation-scope",
                        "boundary-crossing repair must expand affected evidence scope",
                    )
                for affected_task in affected:
                    current_validation.discard(affected_task)
                    current_review.discard(affected_task)
                    current_validation_evidence.pop(affected_task, None)
                    current_review_evidence.pop(affected_task, None)
                    repaired_task_ids.add(affected_task)
                expected_invalidated = {
                    f"validation:{affected_task}" for affected_task in affected
                } | {f"review:{affected_task}" for affected_task in affected}
                repair_invalidated_claims.update(expected_invalidated)
                declared_invalidated = event.get("invalidated_claims")
                if declared_invalidated is not None and set(declared_invalidated) != expected_invalidated:
                    reject(
                        "repair-invalidation-scope",
                        "repair must invalidate exactly intersecting and dependent Claims",
                    )
                invalidated_claims.update(expected_invalidated)
                resolved_finding_ids = event.get("resolved_finding_ids")
                if (
                    not isinstance(resolved_finding_ids, list)
                    or not resolved_finding_ids
                    or len(resolved_finding_ids) != len(set(resolved_finding_ids))
                    or any(
                        finding_id not in pending_repair_findings
                        for finding_id in resolved_finding_ids
                    )
                ):
                    reject(
                        "repair-finding-identity",
                        "repair must name unique unresolved material Finding identities",
                    )
                    resolved_finding_ids = []
                projected_relations = event.get("finding_relations")
                expected_relations = {
                    finding_id: finding_relations_by_id.get(finding_id)
                    for finding_id in resolved_finding_ids
                }
                if (
                    not isinstance(projected_relations, dict)
                    or projected_relations != expected_relations
                    or any(
                        relation != "current-task"
                        for relation in expected_relations.values()
                    )
                ):
                    reject(
                        "repair-finding-relation",
                        "Repair must preserve Finding Relation and accepts only material current-task findings",
                    )
                derived_specialists: set[str] = set()
                derived_risks: set[str] = set()
                for finding_id in resolved_finding_ids:
                    finding_task, finding_specialists, finding_risks = (
                        pending_repair_findings[finding_id]
                    )
                    if finding_task not in affected:
                        reject(
                            "repair-finding-identity",
                            "repair reach must include every resolved Finding Task",
                        )
                        continue
                    derived_specialists.update(finding_specialists)
                    derived_risks.update(finding_risks)
                affected_specialists = event.get(
                    "affected_specialist_obligations", []
                )
                affected_risks = event.get("affected_risk_dimensions", [])
                if (
                    not isinstance(affected_specialists, list)
                    or not set(affected_specialists) <= set(required_specialists or [])
                    or not derived_specialists <= set(affected_specialists)
                    or not isinstance(affected_risks, list)
                    or not set(affected_risks) <= set(required_risks or [])
                    or not derived_risks <= set(affected_risks)
                ):
                    reject(
                        "repair-review-obligation-binding",
                        "repair must bind affected Specialist obligations and risk dimensions",
                    )
                else:
                    requirements = (derived_specialists, derived_risks)
                    for affected_task in affected:
                        repair_review_requirements[affected_task] = requirements
                for finding_id in resolved_finding_ids:
                    pending_repair_findings.pop(finding_id, None)
        elif action == "validate":
            task_id = event.get("task_id")
            generation = event.get("generation")
            evidence_id = event.get("evidence_id", f"validation-{task_id}-{generation}")
            valid_fresh_validation = (
                task_id in task_ids
                and generation == latest_generation.get(task_id)
                and event.get("result", "passed") == "passed"
                and event.get("fresh", True) is True
                and event.get("scope_correct", True) is True
                and event.get("trustworthy_oracle", True) is True
            )
            repeats_current_validation = (
                valid_fresh_validation and task_id in current_validation
            )
            if repeats_current_validation:
                validation_rerun_count += 1
                reject(
                    "validation-evidence-reuse",
                    "current valid validation must be reused unless an invalidation or reproduction trigger requires rerun",
                )
            if not valid_fresh_validation:
                reject(
                    "material-edit-validation",
                    "each final material edit requires fresh scoped trustworthy targeted validation",
                )
            else:
                current_validation.add(task_id)
                invalidated_claims.discard(f"validation:{task_id}")
                if isinstance(evidence_id, str) and evidence_id:
                    current_validation_evidence[task_id] = evidence_id
                    fresh_validation_evidence_ids.append(evidence_id)
                if task_id in repaired_task_ids:
                    repair_validated_task_ids.add(task_id)
            if (
                not isinstance(evidence_id, str)
                or not evidence_id
                or evidence_id in validation_evidence
            ):
                reject("validation-evidence-id", "validation evidence IDs must be unique")
            else:
                validation_evidence[evidence_id] = (str(task_id), int(generation or 0))
        elif action in {"review", "re-review"}:
            event_tasks = event.get("covered_task_ids")
            if not isinstance(event_tasks, list) or not event_tasks or not set(event_tasks) <= set(task_ids):
                reject("review-boundary-coverage", "review must cover known Task IDs")
                continue
            event_task_set = set(event_tasks)
            full_boundary = event_task_set == set(task_ids)
            risk_trigger = event.get("risk_trigger")
            if (
                effective_level in {"L1", "L2", "L3", "L4"}
                and not full_boundary
                and not risk_trigger
                and action != "re-review"
            ):
                reject(
                    "review-boundary-frequency",
                    "per-Task review plus final review is forbidden without a real intermediate risk boundary",
                )
            if full_boundary and covering_review_seen and not repair_seen:
                reject(
                    "obligation-subsumption",
                    "a same-or-stronger covering review satisfies weaker equivalent review obligations",
                )
            if full_boundary:
                covering_review_seen = True
            if action == "re-review":
                if not repair_seen:
                    reject("repair-rereview", "re-review requires a preceding repair")
                covering_rereview_seen = current_review | event_task_set == set(task_ids)
                rereviewed_task_ids.update(event_task_set & repaired_task_ids)
            elif covering_rereview_seen:
                reject(
                    "obligation-subsumption",
                    "covering scoped re-review already satisfies the final review obligation",
                )
            event_level = event.get("effective_level")
            if event_level not in level_rank or level_rank[event_level] < level_rank.get(effective_level, 99):
                reject("review-depth", "review must meet or exceed the required Effective Level")
            event_skills = set(event.get("review_skills", []))
            expected_skills = (
                set(required_review_skills or [])
                if full_boundary
                else set().union(*(task_review_skills[task] for task in event_task_set))
            )
            if not expected_skills <= event_skills:
                reject(
                    "review-skill-preservation",
                    "combined or scoped review must preserve required Review Skills",
                )
            for review_skill in event_skills:
                review_entry = professional.get(review_skill)
                if review_entry is None:
                    reject("review-skill-registry", f"unknown Review Skill {review_skill!r}")
                elif "review-agent" not in review_entry.get("role_support", []):
                    reject(
                        "review-skill-routing",
                        f"Review Skill {review_skill!r} does not support review-agent",
                    )
                elif not built_professional(review_skill):
                    reject(
                        "skill-built-delivery",
                        f"Review Skill {review_skill!r} is not delivered by every build",
                    )
            raw_event_layer3 = event.get("layer3_skills", [])
            if (
                not isinstance(raw_event_layer3, list)
                or len(raw_event_layer3) > 3
                or any(
                    not isinstance(skill, str) or not skill
                    for skill in raw_event_layer3
                )
                or len(raw_event_layer3) != len(set(raw_event_layer3))
            ):
                reject(
                    "review-layer3-routing",
                    "each review must select zero to three unique Layer 3 Skills",
                )
                raw_event_layer3 = []
            event_layer3 = set(raw_event_layer3)
            expected_layer3 = set().union(
                *(task_layer3_skills.get(task, set()) for task in event_task_set)
            )
            if not expected_layer3 <= event_layer3:
                reject(
                    "review-layer3-preservation",
                    "combined or scoped review must preserve affected Layer 3 obligations",
                )
            review_candidates = set().union(
                *(
                    set(professional[skill].get("layer3_candidates", []))
                    for skill in event_skills
                    if skill in professional
                )
            )
            for layer3_skill in event_layer3:
                layer3_entry = layer3_entries.get(layer3_skill)
                if layer3_entry is None:
                    reject(
                        "review-layer3-registry",
                        f"unknown review Layer 3 Skill {layer3_skill!r}",
                    )
                elif layer3_skill not in review_candidates:
                    reject(
                        "review-layer3-routing",
                        f"review Layer 3 Skill {layer3_skill!r} is not routed by an assigned Review Skill",
                    )
                elif "review-agent" not in layer3_entry.get("role_support", []):
                    reject(
                        "review-layer3-role",
                        f"review Layer 3 Skill {layer3_skill!r} does not support review-agent",
                    )
                elif not any(
                    built_layer3(skill, layer3_skill) for skill in event_skills
                ):
                    reject(
                        "skill-built-delivery",
                        f"review Layer 3 Skill {layer3_skill!r} is not delivered for an assigned Review Skill",
                    )
            event_specialists = set(event.get("specialist_obligations", []))
            event_risks = set(event.get("risk_dimensions", []))
            if full_boundary and (
                not set(required_specialists or []) <= event_specialists
                or not set(required_risks or []) <= event_risks
            ):
                reject(
                    "review-obligation-coverage",
                    "covering review must preserve Specialist obligations and risk dimensions",
                )
            if action == "re-review":
                affected_requirements = [
                    repair_review_requirements.get(task, (set(), set()))
                    for task in event_task_set
                ]
                affected_specialists = set().union(
                    *(item[0] for item in affected_requirements)
                )
                affected_risks = set().union(
                    *(item[1] for item in affected_requirements)
                )
                if (
                    not affected_specialists <= event_specialists
                    or not affected_risks <= event_risks
                ):
                    reject(
                        "repair-review-obligation-preservation",
                        "scoped re-review must retain affected Specialist obligations and risk dimensions",
                    )
            reproduction = event.get("reproduction_triggers", [])
            if not isinstance(reproduction, list) or not set(reproduction) <= allowed_reproduction:
                reject("validation-evidence-reuse", "review reproduction trigger is invalid")
            if event.get("reexecuted_validation", False) is True:
                validation_rerun_count += 1
                if not reproduction:
                    reject(
                        "validation-evidence-reuse",
                        "independence alone does not justify mechanically repeating valid validation",
                    )
            supplied_validation = event.get("validation_evidence_ids")
            if not isinstance(supplied_validation, list) or not supplied_validation:
                reject(
                    "review-validation-binding",
                    "every review must bind current-generation validation evidence",
                )
            else:
                if event.get("reexecuted_validation", False) is not True:
                    reused_validation_evidence_ids.extend(
                        evidence_id
                        for evidence_id in supplied_validation
                        if isinstance(evidence_id, str)
                    )
                bound_tasks = {
                    validation_evidence[evidence_id][0]
                    for evidence_id in supplied_validation
                    if evidence_id in validation_evidence
                    and validation_evidence[evidence_id][1]
                    == latest_generation.get(validation_evidence[evidence_id][0])
                    and validation_evidence[evidence_id][0] in current_validation
                }
                if (
                    len(supplied_validation) != len(set(supplied_validation))
                    or bound_tasks != event_task_set
                ):
                    reject(
                        "review-validation-binding",
                        "review validation evidence must uniquely cover each reviewed Task at its current generation",
                    )
            review_id = event.get("evidence_id", f"review-{index}")
            if not isinstance(review_id, str) or not review_id or review_id in review_ids:
                reject("review-evidence-id", "review evidence IDs must be unique")
            else:
                review_ids.add(review_id)
            review_actions.append(action)
            if event.get("independent") is not True:
                reject("review-independence", "review evidence must be independent")
            verdict = event.get("verdict")
            if verdict not in REVIEW_VERDICTS:
                reject("review-verdict", "review verdict must use the closed Core enum")
            if verdict == "pass" and event.get("unreviewed_required_scope"):
                reject(
                    "review-pass-scope",
                    "PASS requires complete required changed-scope review",
                )
            if verdict == "blocked":
                if not valid_scope_list(event.get("reviewed_scope")) or not valid_scope_list(
                    event.get("unreviewed_scope")
                ):
                    reject(
                        "review-blocked-scope",
                        "blocked Review must report non-empty text Reviewed and Unreviewed Scope",
                    )
                terminal_seen = True
                terminal_state = "blocked"
            elif verdict in {"pass", "findings"}:
                current_review.update(event_task_set)
                for task_id in event_task_set:
                    invalidated_claims.discard(f"review:{task_id}")
                    if isinstance(review_id, str) and review_id:
                        current_review_evidence[task_id] = review_id
        elif action == "finding":
            finding_id = event.get("finding_id")
            relation = event.get("relation")
            category = event.get("category")
            task_id = event.get("task_id")
            repair_required = event.get("repair_required") is True
            if relation not in finding_relations:
                reject("finding-relation", "Finding relation must use the closed Core enum")
            if category not in finding_categories:
                reject("finding-category", "Finding category must use the closed Core enum")
            finding_identity_valid = (
                isinstance(finding_id, str)
                and bool(finding_id)
                and finding_id not in seen_finding_ids
            )
            if not finding_identity_valid:
                reject(
                    "finding-identity",
                    "every Finding identity must be non-empty and unique across the trajectory",
                )
            else:
                seen_finding_ids.add(finding_id)
                if relation in finding_relations:
                    finding_relations_by_id[finding_id] = relation
            material = category in material_categories
            if category in non_repair_categories:
                material = False
            if repair_required and (relation != "current-task" or not material):
                reject(
                    "material-finding-repair",
                    "only material current-task findings create a Repair obligation",
                )
            if relation == "current-task" and material:
                if task_id not in task_ids:
                    reject(
                        "material-finding-task",
                        "a material current-task Finding must name an existing affected Task",
                    )
                if not repair_required:
                    reject(
                        "material-finding-repair",
                        "a material current-task finding must declare the Repair obligation",
                    )
                if finding_identity_valid and task_id in task_ids:
                    impact_dimensions = event.get("impact_dimensions", [])
                    if (
                        not isinstance(impact_dimensions, list)
                        or any(
                            not isinstance(item, str) or not item
                            for item in impact_dimensions
                        )
                        or not set(impact_dimensions) <= set(required_risks or [])
                    ):
                        reject(
                            "finding-impact",
                            "Finding impact dimensions must be known boundary risk dimensions",
                        )
                        impact_dimensions = []
                    terms = category_risk_terms.get(str(category), set())
                    derived_risks = {
                        risk
                        for risk in required_risks or []
                        if any(term in risk for term in terms)
                    } | set(impact_dimensions)
                    derived_specialists = {
                        specialist
                        for specialist in required_specialists or []
                        if any(term in specialist for term in terms)
                        or any(
                            specialist in impact or impact in specialist
                            for impact in impact_dimensions
                        )
                    }
                    pending_repair_findings[finding_id] = (
                        task_id,
                        derived_specialists,
                        derived_risks,
                    )
        elif action == "blocked":
            if event.get("reason") not in FINDING_RELATION_MODEL["fail_fast"]["triggers"]:
                reject("review-fail-fast", "blocked fail-fast reason is not fundamental")
            if not valid_scope_list(event.get("reviewed_scope")) or not valid_scope_list(
                event.get("unreviewed_scope")
            ):
                reject(
                    "review-fail-fast",
                    "blocked review must report non-empty text Reviewed and Unreviewed Scope",
                )
            terminal_seen = True
            terminal_state = "blocked"
        elif action == "complete":
            if pending_repair_findings:
                reject(
                    "material-finding-repair",
                    "completion is forbidden while a material current-task finding awaits Repair",
                )
            if set(latest_generation) != set(task_ids) or current_validation != set(task_ids):
                reject(
                    "completion-current-evidence",
                    "completion requires current validation after every Task's latest material edit",
                )
            if current_review != set(task_ids):
                reject(
                    "completion-current-evidence",
                    "completion requires current review coverage for every Task",
                )
            if invalidated_claims:
                reject(
                    "completion-current-evidence",
                    "completion cannot rely on invalidated repair evidence",
                )
            terminal_seen = True
            terminal_state = "complete"
        elif action != "analysis":
            reject("orchestration-event", f"unsupported orchestration action {action!r}")

    if not terminal_seen:
        reject("orchestration-terminal", "trajectory must end in complete or blocked")
    current_evidence = (
        terminal_state == "complete"
        and set(latest_generation) == set(task_ids)
        and current_validation == set(task_ids)
        and current_review == set(task_ids)
        and not invalidated_claims
        and not pending_repair_findings
    )
    semantic_trace = {
        "id": case_id,
        "work_kind": "analyzed" if analysis_events else "direct",
        "analysis": {
            "count": len(analysis_events),
            "kinds": [str(event.get("analysis_kind")) for event in analysis_events],
        },
        "task_dispatch": [
            {
                "task_id": task_id,
                "primary_skill": task_skills.get(task_id),
                "layer3_skills": sorted(task_layer3_skills.get(task_id, set())),
            }
            for task_id in task_ids
        ],
        "validation": {
            "fresh_count": len(fresh_validation_evidence_ids),
            "fresh_evidence_ids": fresh_validation_evidence_ids,
            "reuse_count": len(reused_validation_evidence_ids),
            "reused_evidence_ids": reused_validation_evidence_ids,
            "rerun_count": validation_rerun_count,
        },
        "review_boundary": {
            "covered_task_ids": list(covered_task_ids or []),
            "effective_level": effective_level,
            "required_review_skills": list(required_review_skills or []),
            "required_changed_scope": list(required_scope or []),
        },
        "review": {
            "count": len(review_actions),
            "actions": review_actions,
        },
        "repair_flow": {
            "repair_count": repair_count,
            "affected_task_ids": sorted(repaired_task_ids),
            "invalidated_claims": sorted(repair_invalidated_claims),
            "fresh_validation_task_ids": sorted(repair_validated_task_ids),
            "rereviewed_task_ids": sorted(rereviewed_task_ids),
        },
        "parallel_isolation": parallel_isolation,
        "completion": {
            "state": terminal_state,
            "current_evidence": current_evidence,
            "current_validation_task_ids": sorted(current_validation),
            "current_review_task_ids": sorted(current_review),
            "current_validation_evidence": [
                {
                    "task_id": task_id,
                    "generation": latest_generation.get(task_id),
                    "evidence_id": current_validation_evidence[task_id],
                }
                for task_id in sorted(current_validation_evidence)
            ],
            "current_review_evidence": [
                {
                    "task_id": task_id,
                    "evidence_id": current_review_evidence[task_id],
                }
                for task_id in sorted(current_review_evidence)
            ],
            "invalidated_claims": sorted(invalidated_claims),
        },
        "proof_limit": "deterministic-structural-fixture-only",
    }
    return list(dict.fromkeys(errors)), semantic_trace


def _orchestration_case_errors(case: object) -> list[str]:
    """Compatibility projection for callers that only consume reducer errors."""

    return _orchestration_case_result(case)[0]


def _orchestration_fixture_results(
    cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(cases, list) or not cases:
        return [], ["orchestration_cases must be a non-empty list"]
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("id") if isinstance(case, dict) else "")
        if not case_id or case_id in seen:
            errors.append(f"missing or duplicate orchestration case id: {case_id!r}")
            continue
        seen.add(case_id)
        expected_valid = case.get("expected_valid")
        expected_error = case.get("expected_error")
        if not isinstance(expected_valid, bool) or (
            expected_error is not None and not isinstance(expected_error, str)
        ):
            errors.append(f"{case_id}: orchestration expectation is invalid")
            continue
        case_errors, semantic_trace = _orchestration_case_result(case)
        retained_semantic_equality: bool | None = None
        if expected_valid:
            retained_semantics = case.get("retained_semantics")
            retained_semantic_equality = (
                isinstance(retained_semantics, dict)
                and retained_semantics
                == _retained_semantic_projection(semantic_trace)
            )
            if not retained_semantic_equality:
                case_errors.append(
                    f"{case_id}: [semantic-trace-retention] retained semantics must equal the reducer trace projection"
                )
        actual_valid = not case_errors
        matches_expected = actual_valid == expected_valid and (
            expected_error is None
            or any(expected_error in error for error in case_errors)
        )
        results.append(
            {
                "id": case_id,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": matches_expected,
                "errors": case_errors,
                "semantic_trace": semantic_trace,
                "retained_semantic_equality": retained_semantic_equality,
            }
        )
        if not matches_expected:
            errors.append(
                f"{case_id}: orchestration result does not match expectation: {case_errors}"
            )
    return results, errors


def _combined_review_case_errors(case: object) -> list[str]:
    """Validate routed Review assignments around the shared fixture contract."""

    errors = combined_review_completion_errors(case)
    if not isinstance(case, dict):
        return errors
    tasks = case.get("tasks")
    boundary = case.get("review_boundary")
    if not isinstance(tasks, list) or not isinstance(boundary, dict):
        return errors
    professional, layer3_entries = _skill_registries()
    manifests, manifest_errors = _load_build_manifests()
    errors.extend(f"[skill-built-delivery] {error}" for error in manifest_errors)

    def reject(code: str, message: str) -> None:
        errors.append(f"[{code}] {message}")

    def built_professional(skill: str) -> bool:
        return bool(manifests) and all(
            skill in manifest.get("professional_skills", [])
            for manifest in manifests.values()
        )

    def built_layer3(owner: str, skill: str) -> bool:
        return bool(manifests) and all(
            skill in manifest.get("top_level_skills", [])
            or skill
            in manifest.get("compiled_layer3_references", {}).get(owner, [])
            for manifest in manifests.values()
        )

    for task in tasks:
        if not isinstance(task, dict):
            continue
        primary = task.get("primary_skill")
        if not isinstance(primary, str) or not primary:
            reject("task-primary-skill", "each Task requires exactly one Primary Skill")
            continue
        entry = professional.get(primary)
        if entry is None:
            reject("task-skill-registry", f"unknown Task Primary Skill {primary!r}")
            continue
        if "task-agent" not in entry.get("role_support", []):
            reject("task-skill-role", f"Task Primary Skill {primary!r} does not support task-agent")
        if not built_professional(primary):
            reject("skill-built-delivery", f"Task Primary Skill {primary!r} is not delivered by every build")
        allowed = set(entry.get("layer3_candidates", []))
        for layer3 in task.get("implementation_layer3", []):
            layer3_entry = layer3_entries.get(layer3)
            if layer3_entry is None:
                reject("task-layer3-registry", f"unknown implementation Layer 3 Skill {layer3!r}")
            elif layer3 not in allowed:
                reject("task-layer3-routing", f"implementation Layer 3 Skill {layer3!r} is not routed by {primary!r}")
            elif "task-agent" not in layer3_entry.get("role_support", []):
                reject("task-layer3-role", f"implementation Layer 3 Skill {layer3!r} does not support task-agent")
            elif not built_layer3(primary, layer3):
                reject("skill-built-delivery", f"implementation Layer 3 Skill {layer3!r} is not delivered for {primary!r}")

    assignments = boundary.get("review_assignments", [])
    if isinstance(assignments, list):
        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue
            review_skill = assignment.get("review_skill")
            if not isinstance(review_skill, str) or not review_skill:
                reject("review-assignment-skill", "each assignment requires exactly one Review Skill")
                continue
            entry = professional.get(review_skill)
            if entry is None:
                reject("review-skill-registry", f"unknown Review Skill {review_skill!r}")
                continue
            if "review-agent" not in entry.get("role_support", []):
                reject("review-skill-routing", f"Review Skill {review_skill!r} does not support review-agent")
            if not built_professional(review_skill):
                reject("skill-built-delivery", f"Review Skill {review_skill!r} is not delivered by every build")
            allowed = set(entry.get("layer3_candidates", []))
            for layer3 in assignment.get("layer3_skills", []):
                layer3_entry = layer3_entries.get(layer3)
                if layer3_entry is None:
                    reject("review-layer3-registry", f"unknown review Layer 3 Skill {layer3!r}")
                elif layer3 not in allowed:
                    reject("review-layer3-routing", f"review Layer 3 Skill {layer3!r} is not routed by {review_skill!r}")
                elif "review-agent" not in layer3_entry.get("role_support", []):
                    reject("review-layer3-role", f"review Layer 3 Skill {layer3!r} does not support review-agent")
                elif not built_layer3(review_skill, layer3):
                    reject("skill-built-delivery", f"review Layer 3 Skill {layer3!r} is not delivered for {review_skill!r}")
    return list(dict.fromkeys(errors))


def _combined_review_fixture_results(
    cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(cases, list) or not cases:
        return [], ["combined_review_cases must be a non-empty list"]
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    by_id = {
        case.get("id"): case
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }

    def resolved_case(raw_case: dict[str, Any]) -> dict[str, Any]:
        base_id = raw_case.get("base_case_id")
        if base_id is None:
            return raw_case
        base = by_id.get(base_id)
        if not isinstance(base, dict) or base.get("base_case_id") is not None:
            raise ValueError("combined-review mutation base is missing or indirect")
        resolved = copy.deepcopy(base)
        resolved["id"] = raw_case["id"]
        resolved["expected_valid"] = raw_case["expected_valid"]
        resolved["expected_error"] = raw_case.get("expected_error")
        mutation = raw_case.get("mutation")
        if not isinstance(mutation, dict):
            raise ValueError("combined-review derived fixture requires a mutation")
        operation = mutation.get("operation")
        path = mutation.get("path")
        if not isinstance(path, list) or not path:
            raise ValueError("combined-review mutation path must be non-empty")
        target: Any = resolved
        for part in path[:-1]:
            target = target[part]
        final = path[-1]
        if operation == "replace":
            target[final] = copy.deepcopy(mutation.get("value"))
        elif operation == "remove":
            if isinstance(target, list):
                target.pop(final)
            else:
                del target[final]
        elif operation == "swap":
            other_path = mutation.get("other_path")
            if not isinstance(other_path, list) or not other_path:
                raise ValueError("combined-review swap needs other_path")
            other_target: Any = resolved
            for part in other_path[:-1]:
                other_target = other_target[part]
            other_final = other_path[-1]
            target[final], other_target[other_final] = (
                other_target[other_final],
                target[final],
            )
        else:
            raise ValueError("combined-review mutation operation is invalid")
        return resolved

    for raw_case in cases:
        case = raw_case
        case_id = str(case.get("id") if isinstance(case, dict) else "")
        if not case_id or case_id in seen:
            errors.append(f"missing or duplicate combined-review case id: {case_id!r}")
            continue
        seen.add(case_id)
        expected_valid = case.get("expected_valid")
        expected_error = case.get("expected_error")
        if not isinstance(expected_valid, bool) or (
            expected_error is not None and not isinstance(expected_error, str)
        ):
            errors.append(f"{case_id}: combined-review expectation is invalid")
            continue
        try:
            assert isinstance(case, dict)
            case = resolved_case(case)
        except (AssertionError, KeyError, IndexError, TypeError, ValueError) as exc:
            errors.append(f"{case_id}: combined-review mutation is invalid: {exc}")
            continue
        case_errors = _combined_review_case_errors(case)
        actual_valid = not case_errors
        matches_expected = actual_valid == expected_valid and (
            expected_error is None
            or any(expected_error in error for error in case_errors)
        )
        results.append(
            {
                "id": case_id,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": matches_expected,
                "errors": case_errors,
            }
        )
        if not matches_expected:
            errors.append(
                f"{case_id}: combined-review result does not match expectation: {case_errors}"
            )
    return results, errors


def _implementation_internal_evidence_indexes(
    steps: list[dict[str, Any]],
) -> set[int]:
    """Identify closed task-local discipline evidence without changing the raw trace."""

    first_edit_by_task: dict[str, int] = {}
    for index, step in enumerate(steps):
        if step.get("actor") != "task-agent" or step.get("action") not in EDIT_ACTIONS:
            continue
        task_id = step.get("task_id")
        if isinstance(task_id, str) and task_id.strip():
            first_edit_by_task.setdefault(task_id, index)

    internal: set[int] = set()
    for index, step in enumerate(steps):
        if (
            step.get("actor") == "task-agent"
            and step.get("action") == IMPLEMENTATION_HANDOFF_ACTION
        ) or (
            step.get("actor") == "main-control-agent"
            and step.get("action") == REVIEW_INPUT_READY_ACTION
        ):
            internal.add(index)
            continue
        if (
            step.get("actor") == "review-agent"
            and step.get("action") == REVIEW_DISCIPLINE_ACTION
        ):
            internal.add(index)
            continue
        task_id = step.get("task_id")
        first_edit = first_edit_by_task.get(task_id) if isinstance(task_id, str) else None
        if first_edit is None:
            continue
        if (
            step.get("actor") == "task-agent"
            and step.get("action") in INTERNAL_EVIDENCE_ACTIONS
            and step.get("action") == ADAPTIVE_TEST_EVIDENCE_ACTION
            and tuple(step)
            in {
                ADAPTIVE_TEST_EVIDENCE_FIELDS,
                ADAPTIVE_TEST_ANCHORED_EVIDENCE_FIELDS,
            }
        ):
            internal.add(index)
            continue
        if index >= first_edit:
            continue
        if (
            step.get("actor") == "task-agent"
            and step.get("action") == "read"
            and tuple(step)
            in {
                IMPLEMENTATION_READ_FIELDS,
                IMPLEMENTATION_TEST_READ_FIELDS,
                IMPLEMENTATION_ANCHORED_READ_FIELDS,
                IMPLEMENTATION_ANCHORED_TEST_READ_FIELDS,
            }
            and step.get("read_kind") in IMPLEMENTATION_SOURCE_READ_KINDS
        ):
            internal.add(index)
        elif (
            step.get("actor") == "task-agent"
            and step.get("action") in INTERNAL_EVIDENCE_ACTIONS
            and step.get("action") == "implementation-discipline"
            and tuple(step) == IMPLEMENTATION_DISCIPLINE_FIELDS
            and step.get("schema_version") == IMPLEMENTATION_DISCIPLINE_SCHEMA_VERSION
            and step.get("implementation_kind") in IMPLEMENTATION_KINDS
        ):
            internal.add(index)
    return internal


def _operational_steps(
    steps: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[int]]:
    internal = _implementation_internal_evidence_indexes(steps)
    return [step for index, step in enumerate(steps) if index not in internal], internal


def _skill_registries() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    professional_data = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
    foundation_data = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain_data = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    if not all(
        isinstance(document, dict)
        for document in (professional_data, foundation_data, domain_data)
    ):
        raise ValidationProblem("three-layer Skill registries must be mappings")
    professional = {
        str(row.get("name", "")): row
        for row in professional_data.get("professional_skills", [])
        if isinstance(row, dict)
    }
    layer3 = {
        str(row.get("name", "")): row
        for key, document in (
            ("foundation_skills", foundation_data),
            ("domain_skills", domain_data),
        )
        for row in document.get(key, [])
        if isinstance(row, dict)
    }
    return professional, layer3


def _load_build_manifests() -> tuple[dict[str, dict[str, Any]], list[str]]:
    manifests: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for profile in BUILD_PROFILES:
        path = DIST_SKILLS / profile / ".changeforge-build-manifest.json"
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: build manifest unavailable or malformed: {exc}")
            continue
        if not isinstance(manifest, dict) or manifest.get("profile") != profile:
            errors.append(f"{path}: build manifest does not describe {profile!r}")
            continue
        if manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
            errors.append(
                f"{path}: compiled_layer3_format must equal "
                f"{COMPILED_LAYER3_FORMAT!r}"
            )
            continue
        manifests[profile] = manifest
    return manifests, errors


def _layer3_reference_build_path(
    build_profile: str,
    primary: str,
    owner: str,
    relative: str,
    manifest: dict[str, Any],
) -> Path:
    compiled = manifest.get("compiled_layer3_references", {}).get(primary, [])
    is_compiled = owner in compiled
    is_top_level = owner in manifest.get("top_level_skills", [])
    if is_compiled == is_top_level:
        raise ValueError(
            f"{build_profile}:{primary} must resolve Layer 3 Reference owner {owner!r} "
            "through exactly one compiled or top-level delivery path"
        )
    if is_compiled:
        return (
            DIST_SKILLS
            / build_profile
            / primary
            / "references"
            / "layer3"
            / owner
            / relative
        )
    return DIST_SKILLS / build_profile / owner / relative


def _uses_symlink(path: Path, boundary: Path) -> bool:
    current = path
    while current != boundary and boundary in current.parents:
        if current.is_symlink():
            return True
        current = current.parent
    return current.is_symlink()


def _layer3_reference_errors(
    case_id: str,
    index: int,
    step: dict[str, Any],
    primary: str,
    selected_layer3: list[str],
    layer3_entries: dict[str, dict[str, Any]],
) -> list[str]:
    raw = step.get("layer3_references")
    if not isinstance(raw, list) or any(
        not isinstance(item, str) or not item.strip() for item in (raw or [])
    ):
        return [
            f"{case_id}: dispatch at step {index} needs a layer3_references string list"
        ]
    errors: list[str] = []
    if len(raw) > 3:
        errors.append(
            f"{case_id}: dispatch at step {index} loads more than three Layer 3 References"
        )
    if len(raw) != len(set(raw)):
        errors.append(
            f"{case_id}: dispatch at step {index} repeats a Layer 3 Reference"
        )
    parsed: list[tuple[str, str, str]] = []
    for logical_id in raw:
        try:
            owner, relative = parse_layer3_reference_id(logical_id)
        except FixtureCapsuleError as exc:
            errors.append(
                f"{case_id}: dispatch at step {index} has unsafe Layer 3 Reference "
                f"{logical_id!r}: {exc}"
            )
            continue
        parsed.append((logical_id, owner, relative))
        if owner not in selected_layer3:
            errors.append(
                f"{case_id}: Layer 3 Reference owner {owner!r} is not selected "
                f"at step {index}"
            )
            continue
        entry = layer3_entries.get(owner)
        if entry is None:
            errors.append(
                f"{case_id}: Layer 3 Reference owner {owner!r} is unknown at step {index}"
            )
            continue
        indexed = set(
            reference_paths(
                entry.get("reference_index"),
                f"{owner}.reference_index",
                owner=owner,
            )
        )
        if relative not in indexed:
            errors.append(
                f"{case_id}: Layer 3 Reference {logical_id!r} is not indexed by {owner!r}"
            )
            continue
        source = ROOT / str(entry.get("path", "")) / relative
        if not source.is_file() or _uses_symlink(source, ROOT):
            errors.append(
                f"{case_id}: Layer 3 Reference {logical_id!r} is missing or symlinked in source"
            )

    if parsed and not errors:
        manifests, manifest_errors = _load_build_manifests()
        errors.extend(f"{case_id}: {message}" for message in manifest_errors)
        for logical_id, owner, relative in parsed:
            for profile in BUILD_PROFILES:
                manifest = manifests.get(profile)
                if manifest is None:
                    continue
                try:
                    built = _layer3_reference_build_path(
                        profile, primary, owner, relative, manifest
                    )
                except ValueError as exc:
                    errors.append(f"{case_id}: dispatch at step {index}: {exc}")
                    continue
                if not built.is_file() or _uses_symlink(
                    built, DIST_SKILLS / profile
                ):
                    errors.append(
                        f"{case_id}: Layer 3 Reference {logical_id!r} is missing or "
                        f"symlinked in {profile} build"
                    )
    return errors


def _nonempty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _utility_assignment_return_errors(
    assignment: object,
    result: object,
) -> list[str]:
    """Validate canonical Utility handoff continuity without Ledger identity fields."""

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

    errors: list[str] = []
    task_id = assignment["task_id"]
    owner = assignment["owner"]
    if not isinstance(task_id, str) or not task_id.strip():
        errors.append("Utility Assignment Task ID must be non-empty")
    if not isinstance(owner, str) or not owner.strip():
        errors.append("Utility Assignment Owner must be non-empty")
    if assignment["status"] not in UTILITY_ASSIGNMENT_STATUSES:
        errors.append(
            f"Utility Assignment Status must be one of "
            f"{sorted(UTILITY_ASSIGNMENT_STATUSES)}"
        )
    if result["status"] not in UTILITY_RETURN_STATUSES:
        errors.append(
            f"Utility Return Status must be one of {sorted(UTILITY_RETURN_STATUSES)}"
        )
    same_task_id = result["task_id"] == task_id
    if not same_task_id:
        errors.append("Utility Return Task ID must match Utility Assignment")
    if result["owner"] != owner:
        errors.append("Utility Return Owner must match Utility Assignment")
    if result["mode"] != assignment["mode"]:
        errors.append("Utility Return mode must match Utility Assignment")
    if result["no_edit_enforcement"] != assignment["no_edit_enforcement"]:
        errors.append(
            "Utility Return no-edit enforcement must match Utility Assignment"
        )
    if (
        assignment["status"] in UTILITY_ASSIGNMENT_STATUSES
        and result["status"] in UTILITY_RETURN_STATUSES
    ):
        errors.extend(
            completion_transition_errors(
                assignment["status"],
                result["status"],
                same_task_id=same_task_id,
            )
        )

    assignment_ledger = assignment["evidence_ledger"]
    errors.extend(
        evidence_ledger_errors(
            assignment_ledger,
            task_id=str(task_id),
            owner=str(owner),
            required_claims=list(UTILITY_ASSIGNMENT_REQUIRED_CLAIMS),
            required_freshness_marker=0,
            latest_material_edit_marker=None,
            completion_status=str(assignment["status"]),
        )
    )
    current_assignment_claims = (
        {
            row["Claim"]
            for row in assignment_ledger
            if isinstance(row, dict)
            and tuple(row) == CANONICAL_EVIDENCE_LEDGER_FIELDS
            and row["Owner"] == owner
            and row["State"] == "current"
        }
        if isinstance(assignment_ledger, list)
        else set()
    )
    for claim in UTILITY_ASSIGNMENT_REQUIRED_CLAIMS:
        if claim not in current_assignment_claims:
            errors.append(f"Utility Assignment missing current evidence for {claim!r}")

    return_ledger = result["evidence_ledger"]
    errors.extend(
        evidence_ledger_errors(
            return_ledger,
            task_id=str(task_id),
            owner=str(owner),
            required_claims=list(UTILITY_RETURN_REQUIRED_CLAIMS),
            required_freshness_marker=0,
            latest_material_edit_marker=None,
            completion_status=str(result["status"]),
        )
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


def _utility_command_is_safe(command: str) -> bool:
    return command in UTILITY_CAPABILITY_OPERATIONS


def _workspace_check_command(command: str) -> bool:
    return command in WORKSPACE_CHECK_COMMANDS


def _utility_capsule_errors(
    case_id: str,
    index: int,
    capsule: object,
) -> list[str]:
    if not isinstance(capsule, dict):
        return [f"{case_id}: utility dispatch at step {index} needs a Utility Capsule mapping"]
    errors: list[str] = []
    if tuple(capsule) != UTILITY_CAPSULE_FIELDS:
        errors.append(
            f"{case_id}: utility capsule at step {index} must use exact ordered fields "
            f"{list(UTILITY_CAPSULE_FIELDS)}"
        )
    mode = capsule.get("mode")
    if mode not in UTILITY_MODES:
        errors.append(f"{case_id}: utility capsule at step {index} has invalid mode {mode!r}")
    if capsule.get("no_edit_enforcement") != "supported":
        errors.append(
            f"{case_id}: utility capsule at step {index} must declare "
            "no_edit_enforcement='supported'"
        )
    if not isinstance(capsule.get("goal"), str) or not capsule["goal"].strip():
        errors.append(f"{case_id}: utility capsule at step {index} needs a non-empty goal")
    allowed_scope = capsule.get("allowed_scope")
    if (
        not isinstance(allowed_scope, dict)
        or not isinstance(allowed_scope.get("workspace_root"), str)
        or not allowed_scope["workspace_root"].strip()
        or not _nonempty_string_list(allowed_scope.get("paths"))
    ):
        errors.append(
            f"{case_id}: utility capsule at step {index} must name workspace_root and paths"
        )
    if not isinstance(capsule.get("inputs"), dict) or not capsule["inputs"]:
        errors.append(f"{case_id}: utility capsule at step {index} needs mode inputs")
    workspace_baseline = capsule.get("workspace_baseline")
    baseline_commands: list[str] = []
    if (
        not isinstance(workspace_baseline, dict)
        or tuple(workspace_baseline) != ("check_commands", "change_set")
        or not _nonempty_string_list(workspace_baseline.get("check_commands"))
        or not _nonempty_string_list(workspace_baseline.get("change_set"))
    ):
        errors.append(
            f"{case_id}: utility capsule at step {index} needs ordered workspace "
            "baseline check_commands and change_set evidence"
        )
    else:
        baseline_commands = workspace_baseline["check_commands"]
        if any(not _workspace_check_command(command) for command in baseline_commands):
            errors.append(
                f"{case_id}: utility capsule at step {index} uses a non-read-only "
                "workspace baseline command"
            )
        if len(baseline_commands) != len(set(baseline_commands)):
            errors.append(
                f"{case_id}: utility capsule at step {index} workspace baseline "
                "check_commands must be unique"
            )
    for field in ("commands_allowed", "expected_evidence", "stop_conditions"):
        if not _nonempty_string_list(capsule.get(field)):
            errors.append(
                f"{case_id}: utility capsule at step {index} needs non-empty {field}"
            )
    errors.extend(
        _canonical_ledger_shape_errors(
            capsule.get("evidence_ledger"),
            context=f"{case_id}: utility capsule at step {index}",
        )
    )
    commands = capsule.get("commands_allowed")
    if _nonempty_string_list(commands):
        if any(command not in commands for command in baseline_commands):
            errors.append(
                f"{case_id}: utility capsule at step {index} must allow every "
                "workspace baseline command"
            )
        operation_commands: list[str] = []
        for command in commands:
            if not _utility_command_is_safe(command):
                errors.append(
                    f"{case_id}: utility capsule at step {index} allows unsafe command {command!r}"
                )
            if _workspace_check_command(command):
                continue
            operation_commands.append(command)
            if mode == "diff-export/no-edit" and command != "change-evidence-export":
                errors.append(
                    f"{case_id}: diff-export utility at step {index} allows a non-export capability"
                )
            if mode == "validation-only/no-edit" and command == "change-evidence-export":
                errors.append(
                    f"{case_id}: validation utility at step {index} allows diff export"
                )
            elif mode == "validation-only/no-edit" and command != "non-mutating-validation":
                errors.append(
                    f"{case_id}: validation utility at step {index} allows a command "
                    "not declared as non-mutating validation"
                )
        if len(operation_commands) != 1:
            errors.append(
                f"{case_id}: utility capsule at step {index} must allow exactly "
                "one mode operation in addition to workspace checks"
            )
    return errors


def _utility_evidence_errors(
    case_id: str,
    index: int,
    evidence: object,
    capsule: dict[str, Any],
) -> list[str]:
    if not isinstance(evidence, dict):
        return [f"{case_id}: utility result at step {index} needs evidence mapping"]
    errors: list[str] = []
    if tuple(evidence) != UTILITY_EVIDENCE_FIELDS:
        errors.append(
            f"{case_id}: utility evidence at step {index} must use exact ordered fields "
            f"{list(UTILITY_EVIDENCE_FIELDS)}"
        )
    if evidence.get("mode") != capsule.get("mode"):
        errors.append(f"{case_id}: utility evidence at step {index} changes mode")
    if evidence.get("no_edit_enforcement") != capsule.get("no_edit_enforcement"):
        errors.append(f"{case_id}: utility evidence at step {index} changes no-edit enforcement")
    for field in ("artifact_or_check_outcomes", "commands_run", "unverified_scope", "residual_risk"):
        if not _nonempty_string_list(evidence.get(field)):
            errors.append(
                f"{case_id}: utility evidence at step {index} needs non-empty {field}"
            )
    errors.extend(
        _canonical_ledger_shape_errors(
            evidence.get("evidence_ledger"),
            context=f"{case_id}: utility evidence at step {index}",
        )
    )
    commands_run = evidence.get("commands_run")
    allowed = capsule.get("commands_allowed")
    if _nonempty_string_list(commands_run) and _nonempty_string_list(allowed):
        if any(command not in allowed for command in commands_run):
            errors.append(
                f"{case_id}: utility evidence at step {index} reports a command outside the capsule"
            )
        if any(not _utility_command_is_safe(command) for command in commands_run):
            errors.append(
                f"{case_id}: utility evidence at step {index} reports unsafe shell syntax"
            )
        baseline = capsule.get("workspace_baseline")
        check_commands = (
            baseline.get("check_commands", []) if isinstance(baseline, dict) else []
        )
        for command in check_commands:
            if commands_run.count(command) != 2:
                errors.append(
                    f"{case_id}: utility evidence at step {index} must run workspace "
                    f"check {command!r} exactly before and after the operation"
                )
        operation_commands = [
            command for command in commands_run if not _workspace_check_command(command)
        ]
        if len(operation_commands) != 1:
            errors.append(
                f"{case_id}: utility evidence at step {index} must report exactly "
                "one mode operation between workspace checks"
            )
        else:
            expected_sequence = [
                *check_commands,
                operation_commands[0],
                *check_commands,
            ]
            if commands_run != expected_sequence:
                errors.append(
                    f"{case_id}: utility evidence at step {index} must run one "
                    "adjacent ordered pre-check group, exactly one operation, and "
                    "the identical adjacent post-check group"
                )
    workspace_check = evidence.get("workspace_diff_check")
    if (
        not isinstance(workspace_check, dict)
        or tuple(workspace_check) != ("status", "before", "after")
        or workspace_check.get("status") not in {"unchanged", "changed", "unavailable"}
        or not _nonempty_string_list(workspace_check.get("before"))
        or not _nonempty_string_list(workspace_check.get("after"))
    ):
        errors.append(
            f"{case_id}: utility evidence at step {index} needs ordered workspace "
            "diff status, before, and after evidence"
        )
    else:
        baseline = capsule.get("workspace_baseline")
        expected_before = baseline.get("change_set") if isinstance(baseline, dict) else None
        if workspace_check["before"] != expected_before:
            errors.append(
                f"{case_id}: utility evidence at step {index} workspace before "
                "evidence differs from the assigned baseline"
            )
        if workspace_check["status"] != "unchanged":
            errors.append(
                f"{case_id}: utility evidence at step {index} is invalid unless "
                "workspace diff status is unchanged"
            )
        if workspace_check["before"] != workspace_check["after"]:
            errors.append(
                f"{case_id}: utility evidence at step {index} changed the workspace "
                "change set"
            )
    return errors


def _profile_errors(
    case_id: str,
    steps: list[dict[str, Any]],
    professional: dict[str, dict[str, Any]],
    layer3_entries: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    task_ids: set[str] = set()
    for index, step in enumerate(steps):
        actor = str(step.get("actor") or "")
        action = str(step.get("action") or "")
        allowed = PROFILE_ACTIONS.get(actor)
        if allowed is None:
            errors.append(f"{case_id}: step {index} uses unknown actor {actor!r}")
        elif action not in allowed:
            errors.append(f"{case_id}: {actor} cannot perform {action!r} at step {index}")
        if action == "dispatch":
            profile = str(step.get("profile") or "")
            mode = step.get("mode")
            professional_references = step.get("professional_references")
            try:
                validate_and_render_fixture_capsule(step)
            except FixtureCapsuleError as exc:
                errors.append(
                    f"{case_id}: dispatch at step {index} has invalid fixture Capsule: {exc}"
                )
            errors.extend(
                f"{case_id}: dispatch at step {index} {error}"
                for error in trace_execution_level_migration_errors(steps, index)
            )
            fixture_capsule = step.get("fixture_capsule")
            if (
                isinstance(fixture_capsule, dict)
                and fixture_capsule.get("contract_type") == "task"
            ):
                task_id = fixture_capsule.get("task_id")
                if isinstance(task_id, str) and task_id in task_ids:
                    errors.append(
                        f"{case_id}: task fixture repeats Task ID {task_id!r}"
                    )
                elif isinstance(task_id, str):
                    task_ids.add(task_id)
            if not isinstance(mode, str) or not mode.strip():
                errors.append(
                    f"{case_id}: dispatch at step {index} needs a non-empty mode"
                )
            if not isinstance(professional_references, list) or any(
                not isinstance(item, str) or not item.strip()
                for item in (professional_references or [])
            ):
                errors.append(
                    f"{case_id}: dispatch at step {index} needs a professional_references string list"
                )
                professional_references = []
            if len(professional_references) != len(set(professional_references)):
                errors.append(
                    f"{case_id}: dispatch at step {index} repeats a professional reference"
                )
            utility_capsule = step.get("utility_capsule")
            if utility_capsule is not None:
                if profile != "task-agent":
                    errors.append(
                        f"{case_id}: utility dispatch at step {index} must use task-agent"
                    )
                if any(
                    field in step
                    for field in ("primary_skill", "layer3_skills", "layer3_references")
                ):
                    errors.append(
                        f"{case_id}: utility dispatch at step {index} must not select "
                        "a Professional Skill, Layer 3 Skill, or Layer 3 Reference"
                    )
                errors.extend(_utility_capsule_errors(case_id, index, utility_capsule))
                if professional_references:
                    errors.append(
                        f"{case_id}: utility dispatch at step {index} must not load professional references"
                    )
                if isinstance(utility_capsule, dict) and mode != utility_capsule.get("mode"):
                    errors.append(
                        f"{case_id}: utility dispatch at step {index} mode must match the Utility Capsule"
                    )
                continue
            primary = str(step.get("primary_skill") or "")
            layer3 = step.get("layer3_skills")
            if profile not in {"analysis-agent", "task-agent", "review-agent"}:
                errors.append(f"{case_id}: invalid dispatch profile {profile!r} at step {index}")
            if not primary:
                errors.append(f"{case_id}: dispatch at step {index} must select one primary Skill")
            if not isinstance(layer3, list):
                errors.append(f"{case_id}: dispatch at step {index} must declare Layer 3 selection")
                selected_layer3: list[str] = []
            else:
                selected_layer3 = [str(item).strip() for item in layer3 if str(item).strip()]
            primary_entry = professional.get(primary)
            if primary_entry is None:
                errors.append(f"{case_id}: unknown primary Skill {primary!r} at step {index}")
                candidates: set[str] = set()
            else:
                roles = {
                    str(item).strip()
                    for item in primary_entry.get("role_support", [])
                    if str(item).strip()
                }
                if profile not in roles:
                    errors.append(
                        f"{case_id}: primary Skill {primary!r} does not support "
                        f"profile {profile!r} at step {index}"
                    )
                candidates = {
                    str(item).strip()
                    for item in primary_entry.get("layer3_candidates", [])
                    if str(item).strip()
                }
            if primary == "engineering-change-analysis":
                expected_reference = {
                    "implementation-preparation": "references/implementation-preparation.md",
                    "diagnosis-only": "references/diagnosis-only.md",
                    "source-backed-answer": "references/source-backed-answer.md",
                }.get(str(mode))
                if expected_reference is None:
                    errors.append(
                        f"{case_id}: engineering-change-analysis dispatch at step {index} "
                        f"has unsupported mode {mode!r}"
                    )
                elif expected_reference not in professional_references:
                    errors.append(
                        f"{case_id}: engineering-change-analysis dispatch at step {index} "
                        f"must load {expected_reference!r}"
                    )
            if len(selected_layer3) > 3:
                errors.append(f"{case_id}: dispatch at step {index} loads more than three Layer 3 Skills")
            if len(selected_layer3) != len(set(selected_layer3)):
                errors.append(f"{case_id}: dispatch at step {index} repeats a Layer 3 Skill")
            for name in selected_layer3:
                layer3_entry = layer3_entries.get(name)
                if layer3_entry is None:
                    errors.append(
                        f"{case_id}: unknown Layer 3 Skill {name!r} at step {index}"
                    )
                    continue
                if name not in candidates:
                    errors.append(
                        f"{case_id}: Layer 3 Skill {name!r} is not a candidate of "
                        f"{primary!r} at step {index}"
                    )
                roles = {
                    str(item).strip()
                    for item in layer3_entry.get("role_support", [])
                    if str(item).strip()
                }
                if profile not in roles:
                    errors.append(
                        f"{case_id}: Layer 3 Skill {name!r} does not support "
                        f"profile {profile!r} at step {index}"
                    )
            errors.extend(
                _layer3_reference_errors(
                    case_id,
                    index,
                    step,
                    primary,
                    selected_layer3,
                    layer3_entries,
                )
            )
    return errors


def _utility_case_errors(case: dict[str, Any], steps: list[dict[str, Any]]) -> list[str]:
    case_id = str(case.get("id") or "<missing>")
    errors: list[str] = []
    utility_dispatches = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("action") == "dispatch" and "utility_capsule" in step
    ]
    utility_results = [
        (index, step)
        for index, step in enumerate(steps)
        if "utility_evidence" in step
    ]
    task_dispatches = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("action") == "dispatch" and step.get("profile") == "task-agent"
    ]
    task_results = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("actor") == "task-agent"
    ]
    if len(task_dispatches) != 1:
        errors.append(
            f"{case_id}: utility case must contain exactly one task-agent dispatch"
        )
    if len(task_results) != 1:
        errors.append(
            f"{case_id}: utility case must contain exactly one task-agent result"
        )
    if len(utility_dispatches) != 1:
        errors.append(f"{case_id}: utility case must contain exactly one utility dispatch")
    if len(utility_results) != 1:
        errors.append(
            f"{case_id}: utility case must contain exactly one utility evidence return"
        )
    if len(utility_dispatches) != 1 or len(utility_results) != 1:
        return errors
    dispatch_index, dispatch = utility_dispatches[0]
    result_index, result = utility_results[0]
    capsule = dispatch.get("utility_capsule")
    if not isinstance(capsule, dict):
        return [f"{case_id}: utility dispatch must carry a capsule mapping"]
    errors.extend(
        _utility_evidence_errors(
            case_id,
            result_index,
            result.get("utility_evidence"),
            capsule,
        )
    )
    errors.extend(
        f"{case_id}: {error}"
        for error in _utility_assignment_return_errors(
            capsule,
            result.get("utility_evidence"),
        )
    )
    if result.get("actor") != "task-agent":
        errors.append(f"{case_id}: utility result actor must be task-agent")
    if len(task_results) == 1 and task_results[0][0] != result_index:
        errors.append(
            f"{case_id}: the sole task-agent result must carry the utility evidence"
        )
    if result_index != dispatch_index + 1:
        errors.append(
            f"{case_id}: utility dispatch must be followed immediately by its result"
        )
    if any(step.get("action") in EDIT_ACTIONS for step in steps):
        errors.append(f"{case_id}: utility case must not edit or repair")
    if any("implementation_handoff" in step for step in steps):
        errors.append(f"{case_id}: utility case must not use Implementation Handoff")
    capability_facts = case.get("capability_facts")
    if (
        not isinstance(capability_facts, dict)
        or tuple(capability_facts) != GENERIC_CAPABILITY_FIELDS
        or any(state not in GENERIC_CAPABILITY_STATES for state in capability_facts.values())
    ):
        errors.append(
            f"{case_id}: utility case must declare the exact canonical capability_facts"
        )
        capability_facts = {}
    mode = capsule.get("mode")
    if capsule.get("no_edit_enforcement") != capability_facts.get(
        "workspace-state-observation"
    ):
        errors.append(
            f"{case_id}: utility no-edit enforcement must equal the injected "
            "workspace-state-observation capability"
        )
    if capability_facts.get("workspace-state-observation") != "supported":
        errors.append(f"{case_id}: utility requires workspace-state-observation")
    utility_evidence = result.get("utility_evidence")
    workspace_check = (
        utility_evidence.get("workspace_diff_check")
        if isinstance(utility_evidence, dict)
        else None
    )
    workspace_status = (
        workspace_check.get("status") if isinstance(workspace_check, dict) else None
    )
    if workspace_status != "unchanged" and any(
        step.get("action") in REVIEW_ACTIONS | {"close"}
        or step.get("profile") == "review-agent"
        for step in steps[result_index + 1 :]
    ):
        errors.append(
            f"{case_id}: changed or unavailable utility workspace evidence must "
            "not continue to review or closure"
        )
    if mode == "diff-export/no-edit":
        if capability_facts.get("change-evidence-export") != "supported":
            errors.append(f"{case_id}: diff-export requires change-evidence-export")
        if capability_facts.get("workspace-state-observation") != "supported":
            errors.append(f"{case_id}: diff-export requires workspace-state-observation")
        if case.get("actual_diff_supplied") is not False:
            errors.append(f"{case_id}: diff-export case requires a missing supplied diff")
        if result.get("action") != "export-diff":
            errors.append(f"{case_id}: diff-export utility must return export-diff evidence")
        artifact_ref = result.get("artifact_ref")
        native_utility_reference = (
            isinstance(artifact_ref, dict)
            and capability_facts.get("native-change-read") == "supported"
            and capability_facts.get("reviewer-change-consume") == "supported"
            and _native_change_reference_bound(
                artifact_ref,
                artifact_ref.get("changed_paths"),
                artifact_ref.get("generation"),
                "review-agent",
            )
        )
        if not (_unified_diff_paths(artifact_ref) or native_utility_reference):
            errors.append(
                f"{case_id}: diff-export utility must return supplied content or "
                "a host-native artifact reference"
            )
        review_dispatches = [
            index
            for index, step in enumerate(steps)
            if step.get("action") == "dispatch" and step.get("profile") == "review-agent"
        ]
        review_actions = [
            index for index, step in enumerate(steps) if step.get("action") == "review"
        ]
        artifact_reads = [
            index
            for index, step in enumerate(steps)
            if step.get("action") == "read" and step.get("artifact_ref") == artifact_ref
        ]
        if (
            len(review_dispatches) != 1
            or len(review_actions) != 1
            or len(artifact_reads) != 1
            or not result_index < review_dispatches[0] < artifact_reads[0] < review_actions[0]
        ):
            errors.append(
                f"{case_id}: returned diff artifact must precede review dispatch, read, and review"
            )
    elif mode == "validation-only/no-edit":
        if capability_facts.get("non-mutating-validation") != "supported":
            errors.append(f"{case_id}: validation utility requires non-mutating-validation")
        if result.get("action") != "validate":
            errors.append(f"{case_id}: validation utility must return validation evidence")
        if any(
            step.get("action") in REVIEW_ACTIONS
            or step.get("profile") == "review-agent"
            for step in steps
        ):
            errors.append(f"{case_id}: validation utility must not claim independent review")
    return errors


def _meaningful_progress_evidence(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold().strip(" .:;,-")
    compact = re.sub(r"\s+", "", normalized)
    return (
        len(compact) >= 12
        and normalized not in GENERIC_PROGRESS_EVIDENCE
        and re.fullmatch(r"[a-d](?:\s*[/,]\s*[a-d])+", normalized) is None
    )


def _meaningful_anchor_component(value: str) -> bool:
    return (
        len(value) >= 3
        and value.casefold() not in GENERIC_PROGRESS_EVIDENCE
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value) is not None
    )


def _progress_anchor_error(
    case_id: str,
    index: int,
    checkpoint_type: str,
    anchor: object,
    prior_steps: list[dict[str, Any]],
) -> str | None:
    if not isinstance(anchor, str) or not anchor.strip():
        return f"{case_id}: progress at step {index} requires a verifiable evidence_anchor"
    if checkpoint_type == "start/path":
        expected = f"fixture:{case_id}:path"
        if anchor != expected:
            return (
                f"{case_id}: start/path progress at step {index} must bind the "
                f"fixture path anchor {expected!r}"
            )
        return None
    if checkpoint_type == "dispatch/batch":
        prefix = "batch:"
        batch_id = anchor.removeprefix(prefix) if anchor.startswith(prefix) else ""
        matched = _meaningful_anchor_component(batch_id) and any(
            prior.get("action") == "dispatch"
            and batch_id
            in {
                prior.get("batch_id"),
                prior.get("parallel_batch"),
                prior.get("task_id"),
            }
            for prior in prior_steps
        )
        if not matched:
            return (
                f"{case_id}: dispatch/batch progress at step {index} must bind a "
                "meaningful prior batch id"
            )
        return None
    parts = anchor.split(":")
    if checkpoint_type == "validation":
        matched = (
            len(parts) == 3
            and parts[0] == "validation"
            and _meaningful_anchor_component(parts[1])
            and _meaningful_anchor_component(parts[2])
            and any(
                prior.get("action") == "validate"
                and prior.get("evidence_id") == parts[1]
                and prior.get("outcome") == parts[2]
                for prior in prior_steps
            )
        )
        if not matched:
            return (
                f"{case_id}: validation progress at step {index} must bind a "
                "prior validation evidence id and outcome"
            )
        return None
    if checkpoint_type == "review/close":
        matched = (
            len(parts) == 3
            and parts[0] == "review"
            and _meaningful_anchor_component(parts[1])
            and _meaningful_anchor_component(parts[2])
            and any(
                prior.get("evidence_id") == parts[1]
                and (
                    (
                        prior.get("action") in REVIEW_ACTIONS
                        and prior.get("outcome") == parts[2]
                    )
                    or (
                        prior.get("action") == "finding"
                        and prior.get("relation") == parts[2]
                        and prior.get("material") is True
                    )
                )
                for prior in prior_steps
            )
        )
        if not matched:
            return (
                f"{case_id}: review/close progress at step {index} must bind a "
                "prior review evidence id and outcome or Finding Relation"
            )
    return None


def _progress_errors(case_id: str, steps: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    previous: tuple[str, str] | None = None
    last_evidence_by_type: dict[str, str] = {}
    has_trace_actions = any(step.get("action") != "progress" for step in steps)
    first_productive = _first_index(steps, WORKER_EVIDENCE_ACTIONS)
    for index, step in enumerate(steps):
        if step.get("action") != "progress":
            continue
        checkpoint_type = step.get("checkpoint_type")
        evidence = step.get("evidence")
        valid_checkpoint = (
            isinstance(checkpoint_type, str)
            and checkpoint_type in PROGRESS_CHECKPOINT_TYPES
        )
        if not valid_checkpoint:
            errors.append(
                f"{case_id}: progress at step {index} must use one of "
                f"{sorted(PROGRESS_CHECKPOINT_TYPES)}"
            )
        if not isinstance(evidence, str) or not evidence.strip():
            errors.append(
                f"{case_id}: progress at step {index} requires non-empty evidence"
            )
        elif not _meaningful_progress_evidence(evidence):
            errors.append(
                f"{case_id}: progress at step {index} evidence must be meaningful, "
                "not a generic marker such as a/b/c/d"
            )
        current = (
            (checkpoint_type, evidence.strip())
            if valid_checkpoint
            and isinstance(evidence, str)
            and evidence.strip()
            else None
        )
        if current is not None and current == previous:
            errors.append(
                f"{case_id}: adjacent progress events at step {index} repeat "
                "identical checkpoint_type and evidence"
            )
        elif (
            current is not None
            and last_evidence_by_type.get(current[0]) == current[1]
        ):
            errors.append(
                f"{case_id}: repeated progress checkpoint_type {current[0]!r} "
                "must carry changed evidence"
            )
        if current is not None:
            last_evidence_by_type[current[0]] = current[1]
            anchor_error = _progress_anchor_error(
                case_id,
                index,
                current[0],
                step.get("evidence_anchor"),
                steps[:index],
            )
            if anchor_error is not None:
                errors.append(anchor_error)
            if has_trace_actions and current[0] == "start/path" and (
                first_productive is not None and index >= first_productive
            ):
                errors.append(
                    f"{case_id}: start/path progress at step {index} must precede "
                    "the first productive worker action"
                )
        previous = current
    return errors


def _progress_metrics(case: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    progress_indexes = [
        index for index, step in enumerate(steps) if step.get("action") == "progress"
    ]
    productive_count = sum(
        step.get("actor") != "main-control-agent"
        and step.get("action") in WORKER_EVIDENCE_ACTIONS
        for step in steps
    )
    close_index = next(
        (index for index in range(len(steps) - 1, -1, -1) if steps[index].get("action") == "close"),
        len(steps),
    )
    boundaries = [-1, *progress_indexes, close_index]
    max_silent_steps = max(
        (right - left - 1 for left, right in zip(boundaries, boundaries[1:])),
        default=0,
    )
    checkpoint_types = {
        str(steps[index].get("checkpoint_type")) for index in progress_indexes
    }
    subagent_count = sum(step.get("action") == "dispatch" for step in steps)
    classifications = [case, *[step for step in steps if step.get("action") == "classify"]]
    explicit_complex_or_high_risk = any(
        item.get("complexity") == "complex"
        or item.get("risk") in {"high", "critical"}
        or item.get("high_risk") is True
        for item in classifications
    )
    required = (
        subagent_count >= 3
        or explicit_complex_or_high_risk
        or len(steps) >= 12
    )
    required_types = (
        {"start/path", "dispatch/batch"} <= checkpoint_types
        and bool({"validation", "review/close"} & checkpoint_types)
    )
    ratio = len(progress_indexes) / productive_count if productive_count else 0.0
    return {
        "progress_count": len(progress_indexes),
        "productive_action_count": productive_count,
        "max_silent_steps": max_silent_steps,
        "progress_to_productive_action_ratio": round(ratio, 6),
        "required_progress_for_multi_agent": required,
        "explicit_complex_or_high_risk": explicit_complex_or_high_risk,
        "required_multi_agent_progress_satisfied": (
            not required
            or (
                MULTI_AGENT_PROGRESS_MIN
                <= len(progress_indexes)
                <= MULTI_AGENT_PROGRESS_MAX
                and required_types
                and max_silent_steps <= MAX_SILENT_STRUCTURAL_STEPS
                and ratio <= PROGRESS_TO_PRODUCTIVE_RATIO_MAX
            )
        ),
    }


def _metrics(
    case: dict[str, Any],
    professional: dict[str, dict[str, Any]],
    layer3_entries: dict[str, dict[str, Any]],
    *,
    utility_case: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    case_id = str(case.get("id") or "<missing>")
    raw_steps = case.get("steps")
    if not isinstance(raw_steps, list) or not all(isinstance(item, dict) for item in raw_steps):
        return {}, [f"{case_id}: steps must be a list of mappings"]
    steps: list[dict[str, Any]] = raw_steps
    operational_steps, internal_evidence_indexes = _operational_steps(steps)
    first_productive = _first_index(operational_steps, PRODUCTIVE_ACTIONS)
    first_edit = _first_index(operational_steps, EDIT_ACTIONS)
    last_edit = max(
        (
            index
            for index, step in enumerate(operational_steps)
            if step.get("action") in EDIT_ACTIONS
        ),
        default=None,
    )
    review_indexes = [
        index
        for index, step in enumerate(operational_steps)
        if step.get("action") in REVIEW_ACTIONS
    ]
    review_after_final_edit = last_edit is None or any(index > last_edit for index in review_indexes)
    repair_indexes = [
        index
        for index, step in enumerate(operational_steps)
        if step.get("action") == "repair"
    ]
    rereview_indexes = [
        index
        for index, step in enumerate(operational_steps)
        if step.get("action") == "re-review"
    ]
    repair_requires_rereview = not repair_indexes or any(
        review_index > max(repair_indexes) for review_index in rereview_indexes
    )
    parallel_conflict, parallel_reduction = _parallel_metrics(operational_steps)
    progress = _progress_metrics(case, operational_steps)
    shared_serial = _shared_workspace_writes_serial(operational_steps)
    utility_checks: list[object] = []
    for step in steps:
        evidence = step.get("utility_evidence")
        if not isinstance(evidence, dict):
            continue
        workspace_check = evidence.get("workspace_diff_check")
        utility_checks.append(
            workspace_check.get("status") if isinstance(workspace_check, dict) else None
        )
    metrics = {
        "time_to_first_productive_action_step": first_productive,
        "time_to_first_edit_step": first_edit,
        "total_completion_steps": len(operational_steps),
        "control_turn_count": sum(
            step.get("actor") == "main-control-agent" for step in operational_steps
        ),
        "subagent_count": sum(
            step.get("action") == "dispatch" for step in operational_steps
        ),
        "duplicate_read_count": _duplicate_reads(operational_steps),
        "verification_action_count": sum(
            step.get("action") in {"validate", "review", "re-review"}
            for step in operational_steps
        ),
        "loaded_skill_count": _loaded_skill_count(operational_steps),
        "loaded_layer3_reference_count": _loaded_layer3_reference_count(
            operational_steps
        ),
        "analysis_used": any(
            step.get("action") == "dispatch" and step.get("profile") == "analysis-agent"
            for step in operational_steps
        ),
        "preparation_loop_detected": _preparation_loop(operational_steps),
        "parallel_write_conflict": parallel_conflict,
        "conditional_isolated_write_reduction_steps": parallel_reduction,
        "conditional_isolated_write_contract": (
            parallel_reduction > 0
            and case.get("capability_scope") == "conditional-isolated-write-contract"
        ),
        "shared_workspace_writes_serial": shared_serial,
        "utility_workspace_diff_unchanged": (
            bool(utility_checks) and all(status == "unchanged" for status in utility_checks)
        ),
        "review_after_final_edit": review_after_final_edit,
        "repair_has_rereview": repair_requires_rereview,
        "implementation_discipline_event_count": sum(
            step.get("action") == "implementation-discipline" for step in steps
        ),
        "implementation_internal_evidence_event_count": sum(
            steps[index].get("actor") == "task-agent"
            for index in internal_evidence_indexes
        ),
        "review_discipline_event_count": sum(
            step.get("action") == REVIEW_DISCIPLINE_ACTION for step in steps
        ),
        **progress,
    }
    errors = _profile_errors(case_id, steps, professional, layer3_entries)
    errors.extend(
        _analyzed_trajectory_authority_errors(case_id, case.get("kind"), steps)
    )
    errors.extend(_progress_errors(case_id, operational_steps))
    errors.extend(_review_discipline_errors(case_id, steps))
    if not utility_case:
        errors.extend(
            _implementation_discipline_errors(
                case_id,
                steps,
                case.get("implementation_oracle"),
            )
        )
    if parallel_reduction > 0 and not metrics["conditional_isolated_write_contract"]:
        errors.append(
            f"{case_id}: isolated parallel writes must be labeled as a conditional contract"
        )
    if progress["required_progress_for_multi_agent"] and not progress[
        "required_multi_agent_progress_satisfied"
    ]:
        errors.append(
            f"{case_id}: complex, high-risk, long, or three-dispatch work requires "
            "3-5 anchored progress updates, required checkpoint types, max five "
            "silent structural steps, and progress/productive ratio at most 0.75"
        )
    repair_flow = any(
        step.get("action") in {"repair", "re-review"}
        or step.get("mode") in {"repair", "re-review"}
        for step in operational_steps
    )
    if repair_flow and not 3 <= progress["progress_count"] <= 4:
        errors.append(f"{case_id}: repair/re-review work requires 3-4 progress updates")
    if (
        case.get("kind") == "direct"
        and metrics["subagent_count"] <= 2
        and metrics["total_completion_steps"] < 12
        and progress["progress_count"] > 2
    ):
        errors.append(f"{case_id}: short Direct work must use no more than two progress updates")
    if utility_case:
        errors.extend(_utility_case_errors(case, steps))
    elif any("utility_capsule" in step or "utility_evidence" in step for step in steps):
        errors.append(f"{case_id}: non-utility fixture must not contain a utility contract")
    return metrics, errors


def _expectation_errors(case: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    case_id = str(case.get("id") or "<missing>")
    expected = case.get("expected")
    if not isinstance(expected, dict):
        return [f"{case_id}: expected must be a mapping"]
    comparisons = {
        "first_productive_action": "time_to_first_productive_action_step",
        "first_edit": "time_to_first_edit_step",
        "subagents": "subagent_count",
        "requires_analysis": "analysis_used",
        "review_after_final_edit": "review_after_final_edit",
        "parallel_write_conflict": "parallel_write_conflict",
        "conditional_isolated_write_contract": "conditional_isolated_write_contract",
        "shared_workspace_serial_write": "shared_workspace_writes_serial",
        "workspace_diff_unchanged": "utility_workspace_diff_unchanged",
        "required_progress_for_multi_agent": "required_progress_for_multi_agent",
        "repair_requires_rereview": "repair_has_rereview",
    }
    errors: list[str] = []
    for expected_name, actual_name in comparisons.items():
        if expected_name in expected and expected[expected_name] != actual.get(actual_name):
            errors.append(
                f"{case_id}: {expected_name} expected {expected[expected_name]!r}, "
                f"got {actual.get(actual_name)!r}"
            )
    max_comparisons = {
        "control_turns_max": "control_turn_count",
        "loaded_skills_max": "loaded_skill_count",
        "duplicate_reads_max": "duplicate_read_count",
        "progress_max": "progress_count",
        "max_silent_steps_max": "max_silent_steps",
        "progress_to_productive_action_ratio_max": "progress_to_productive_action_ratio",
    }
    for expected_name, actual_name in max_comparisons.items():
        if expected_name in expected and actual.get(actual_name, 0) > expected[expected_name]:
            errors.append(
                f"{case_id}: {actual_name} {actual.get(actual_name)} exceeds {expected[expected_name]}"
            )
    minimum_comparisons = {
        "conditional_isolated_write_reduction_min": "conditional_isolated_write_reduction_steps",
        "progress_min": "progress_count",
    }
    for expected_name, actual_name in minimum_comparisons.items():
        minimum = expected.get(expected_name)
        if isinstance(minimum, (int, float)) and actual.get(actual_name, 0) < minimum:
            errors.append(
                f"{case_id}: {actual_name} {actual.get(actual_name)} is below {minimum}"
            )
    if actual.get("preparation_loop_detected"):
        errors.append(f"{case_id}: repeated pre-edit analysis dispatch detected")
    return errors


def _resolve_completion_review_authority(
    raw_case: dict[str, Any],
    raw_trajectories: object,
) -> tuple[dict[str, Any] | None, list[str]]:
    reference = raw_case.get("review_authority")
    if reference is None:
        return None, []
    if (
        not isinstance(reference, dict)
        or tuple(reference)
        != (
            "fixture_group",
            "case_id",
            "task_dispatch_index",
            "review_assignment_index",
        )
        or reference["fixture_group"] != "cases"
        or not isinstance(raw_trajectories, list)
    ):
        return None, ["review_authority must reference an authoritative release case"]
    trajectory = next(
        (
            case
            for case in raw_trajectories
            if isinstance(case, dict) and case.get("id") == reference["case_id"]
        ),
        None,
    )
    if not isinstance(trajectory, dict) or not isinstance(
        trajectory.get("steps"), list
    ):
        return None, ["review_authority release case is unavailable"]
    steps = trajectory["steps"]
    task_index = reference["task_dispatch_index"]
    review_index = reference["review_assignment_index"]
    if (
        not isinstance(task_index, int)
        or isinstance(task_index, bool)
        or not isinstance(review_index, int)
        or isinstance(review_index, bool)
        or task_index < 0
        or review_index < 0
        or task_index >= len(steps)
        or review_index >= len(steps)
    ):
        return None, ["review_authority dispatch index is invalid"]
    return {
        "task_dispatch": steps[task_index],
        "review_assignment": steps[review_index],
    }, []


def _external_read_fixture_results(
    raw_cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate offline external-read decisions without contacting a provider."""

    if not isinstance(raw_cases, list):
        return [], ["external-read fixtures must be a list"]

    required_fields = (
        "id",
        "role",
        "external_read_capability",
        "evidence_state",
        "operation",
        "request",
        "response",
        "outcome",
        "ledger",
        "expected_valid",
        "expected_error",
    )
    request_fields = (
        "value",
        "targeted_claim",
        "minimum_public_information",
        "contains_protected_content",
    )
    response_fields = (
        "availability",
        "source_class",
        "artifact",
        "contains_instruction",
        "instruction_executed",
        "raw_instruction_propagated",
    )
    outcome_fields = (
        "external_read_triggered",
        "normalized_claim",
        "brief_decision_recorded",
        "proof_limit_recorded",
        "execution_trigger",
        "edit_status",
        "dispatch_implementation",
    )
    evidence_states = {
        "no-material-claim",
        "local-evidence-sufficient",
        "material-unresolved-claim",
        "non-material-unknown",
        "critical-evidence-gap",
    }
    capability_states = set(EXTERNAL_READ_MODEL["capability_states"])
    operations = {"not-applicable", EXTERNAL_READ_MODEL["operation"]}
    source_classes = {"not-applicable", *EXTERNAL_READ_MODEL["source_priority"]}
    protected_fields = tuple(
        EXTERNAL_READ_MODEL["disclosure_guard"]["forbidden_request_content"]
    )
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()

    for raw_case in raw_cases:
        case_errors: list[str] = []
        if not isinstance(raw_case, dict):
            errors.append("external-read fixture must be a mapping")
            continue
        case_id = str(raw_case.get("id") or "")

        def reject(code: str, message: str) -> None:
            case_errors.append(f"{case_id or '<missing>'}: [{code}] {message}")

        if not case_id or case_id in seen:
            reject("external-read-schema", "fixture id must be non-empty and unique")
        seen.add(case_id)
        if tuple(raw_case) != required_fields:
            reject("external-read-schema", "fixture fields or order are not canonical")

        role = raw_case.get("role")
        external_read_capability = raw_case.get("external_read_capability")
        evidence_state = raw_case.get("evidence_state")
        operation = raw_case.get("operation")
        request = raw_case.get("request")
        response = raw_case.get("response")
        outcome = raw_case.get("outcome")
        ledger = raw_case.get("ledger")
        expected_valid = raw_case.get("expected_valid")
        expected_error = raw_case.get("expected_error")

        if role not in CORE_CONTRACTS["roles"]:
            reject("external-read-schema", "role is not one of the four Profiles")
        if external_read_capability not in capability_states:
            reject(
                "external-read-capability",
                "external read capability is outside the closed enum",
            )
        if evidence_state not in evidence_states:
            reject("external-read-schema", "evidence_state is not recognized")
        if operation not in operations:
            reject("external-read-operation", "operation is not an approved read surface")
        if not isinstance(request, dict) or tuple(request) != request_fields:
            reject("external-read-schema", "request fields or order are not canonical")
            request = {}
        if not isinstance(response, dict) or tuple(response) != response_fields:
            reject("external-read-schema", "response fields or order are not canonical")
            response = {}
        if not isinstance(outcome, dict) or tuple(outcome) != outcome_fields:
            reject("external-read-schema", "outcome fields or order are not canonical")
            outcome = {}
        if not isinstance(ledger, dict) or tuple(ledger) != CANONICAL_EVIDENCE_LEDGER_FIELDS:
            reject("external-read-ledger", "ledger must use the existing canonical fields")
            ledger = {}
        if not isinstance(expected_valid, bool) or (
            expected_error is not None
            and (not isinstance(expected_error, str) or not expected_error)
        ):
            reject("external-read-schema", "expected validity contract is invalid")

        triggered = outcome.get("external_read_triggered") is True
        if role != EXTERNAL_READ_MODEL["exclusive_role"] and (
            triggered or operation != "not-applicable"
        ):
            reject("external-read-role", "external-read is exclusive to analysis-agent")
        if triggered != (operation != "not-applicable"):
            reject("external-read-operation", "trigger and operation must agree")

        if evidence_state in {"no-material-claim", "local-evidence-sufficient"}:
            if triggered or outcome.get("proof_limit_recorded") is not False:
                reject("external-read-jit", "sufficient evidence must not trigger external read")
        elif evidence_state == "non-material-unknown":
            if triggered or outcome.get("proof_limit_recorded") is not True:
                reject("external-read-jit", "non-material unknown must become only a Proof Limit")
        elif evidence_state == "material-unresolved-claim":
            if external_read_capability == "unsupported" or not triggered:
                reject("external-read-jit", "a material unresolved Claim requires supported external read")
        elif evidence_state == "critical-evidence-gap":
            if (
                outcome.get("execution_trigger") != "unknown-critical-boundary"
                or outcome.get("edit_status") != "blocked"
                or outcome.get("dispatch_implementation") is not False
                or outcome.get("proof_limit_recorded") is not True
            ):
                reject("external-read-critical-gap", "critical gap must block edit and implementation dispatch")

        if triggered:
            if external_read_capability == "unsupported":
                reject(
                    "external-read-capability",
                    "unsupported capability cannot actively read externally",
                )
            if request.get("targeted_claim") is not True:
                reject("external-read-jit", "external request must target one material Claim")
            if request.get("minimum_public_information") is not True:
                reject("external-read-disclosure", "request is not minimized to public information")
            if request.get("contains_protected_content") is not False:
                reject(
                    "external-read-disclosure",
                    "request contains protected content: " + ", ".join(protected_fields),
                )
            if not isinstance(request.get("value"), str) or not request["value"].strip():
                reject("external-read-schema", "external request value must be non-empty")
        elif response.get("availability") != "not-requested":
            reject("external-read-jit", "non-triggered path cannot contain an external response")

        if response.get("availability") not in {"available", "unavailable", "not-requested"}:
            reject("external-read-schema", "response availability is invalid")
        if response.get("source_class") not in source_classes:
            reject("external-read-source", "source class is outside the allowed priority set")
        if response.get("instruction_executed") is not False or response.get(
            "raw_instruction_propagated"
        ) is not False:
            reject("external-content-control", "external instructions became control input")
        if response.get("availability") == "available" and triggered:
            artifact = response.get("artifact")
            if not isinstance(artifact, str) or not artifact.strip():
                reject("external-read-source", "available evidence needs a source identifier or URL")
            if outcome.get("normalized_claim") is not True or outcome.get(
                "brief_decision_recorded"
            ) is not True:
                reject("external-read-normalization", "external evidence must be normalized before Brief use")
            if ledger.get("Owner") != "analysis-agent":
                reject("external-read-ledger", "external Claim owner must be analysis-agent")
            if ledger.get("Command") != EXTERNAL_READ_MODEL["operation"]:
                reject(
                    "external-read-ledger",
                    "ledger Command must name the external read capability",
                )
            if ledger.get("Artifact") != artifact:
                reject("external-read-ledger", "ledger Artifact must name the external source")

        if evidence_state != "critical-evidence-gap" and (
            outcome.get("execution_trigger") != "none"
            or outcome.get("edit_status") != "allowed"
            or outcome.get("dispatch_implementation") is not True
        ):
            reject("external-read-outcome", "noncritical path must preserve the safe slice")

        if ledger:
            if any(
                not isinstance(ledger.get(field), (str, int))
                or isinstance(ledger.get(field), bool)
                or (isinstance(ledger.get(field), str) and not ledger[field].strip())
                for field in CANONICAL_EVIDENCE_LEDGER_FIELDS
            ):
                reject("external-read-ledger", "ledger values must be non-empty scalar evidence")
            if ledger.get("State") not in EVIDENCE_LEDGER_MODEL["states"]:
                reject("external-read-ledger", "ledger State is invalid")

        actual_valid = not case_errors
        matches_expected = actual_valid == expected_valid and (
            expected_error is None
            or any(expected_error in error for error in case_errors)
        )
        if not matches_expected:
            errors.extend(case_errors or [f"{case_id}: expected invalid external-read fixture"])
        results.append(
            {
                "id": case_id,
                "operation": operation,
                "external_read_triggered": triggered,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": matches_expected,
                "errors": case_errors,
            }
        )

    return results, errors


def _risk_calibration_fixture_results(
    raw_cases: object,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Evaluate Level and concrete action authority from independent fixture axes."""

    if not isinstance(raw_cases, list):
        return [], ["risk calibration fixtures must be a list"]
    execution = CORE_CONTRACTS["execution_level_contract"]
    material_fields = execution["material_assessment_fields"]
    material_statuses = set(execution["material_candidate_statuses"])
    critical_fields = execution["critical_unknown_fields"]
    professional_registry, layer3_registry = _skill_registries()
    material_trigger_ids = {
        row["id"]
        for row in execution["trigger_registry"]
        if row["floor"] == "L4"
        and row["id"] not in {"formal-release-declared", "unknown-critical-boundary"}
    }
    case_fields = (
        "id",
        "task_id",
        "professional_risk_signals",
        "selected_primary_skill",
        "selected_risk_lenses",
        "decisions",
    )
    decision_fields = (
        "candidate_l4_predicate",
        "residual_material_impact",
        "material_assessment",
        "critical_unknown",
        "l2_eligible",
        "action_authority",
        "expected",
    )
    expected_fields = (
        "automatic_level",
        "effective_level",
        "edit_status",
        "historical_max_floor",
        "historical_max_effective",
        "action_decision",
    )
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()

    for raw_case in raw_cases:
        case_errors: list[str] = []
        if not isinstance(raw_case, dict):
            errors.append("risk calibration fixture must be a mapping")
            continue
        case_id = str(raw_case.get("id") or "")

        def reject(code: str, message: str) -> None:
            case_errors.append(f"{case_id or '<missing>'}: [{code}] {message}")

        if not case_id or case_id in seen:
            reject("risk-schema", "fixture id must be non-empty and unique")
        seen.add(case_id)
        if tuple(raw_case) != case_fields:
            reject("risk-schema", "fixture fields or order are not canonical")
        if not isinstance(raw_case.get("task_id"), str) or not raw_case["task_id"].strip():
            reject("risk-schema", "task_id must be non-empty")
        signals = raw_case.get("professional_risk_signals")
        lenses = raw_case.get("selected_risk_lenses")
        if (
            not isinstance(signals, list)
            or not signals
            or any(not isinstance(item, str) or not item.strip() for item in signals)
            or len(signals) != len(set(signals))
        ):
            reject("risk-schema", "professional risk signals must be unique non-empty text")
        if (
            not isinstance(lenses, list)
            or any(not isinstance(item, str) or not item.strip() for item in lenses)
            or len(lenses) != len(set(lenses))
        ):
            reject("risk-schema", "selected risk lenses must be unique text")
        if not isinstance(raw_case.get("selected_primary_skill"), str) or not raw_case[
            "selected_primary_skill"
        ].strip():
            reject("risk-schema", "selected primary Skill must be explicit")
        elif raw_case["selected_primary_skill"] not in professional_registry:
            reject(
                "risk-route-metadata",
                "selected primary Skill must be a registered Primary Skill; registry presence does not prove route correctness",
            )
        if isinstance(lenses, list):
            for lens in lenses:
                if isinstance(lens, str) and lens not in layer3_registry:
                    reject(
                        "risk-route-metadata",
                        "selected risk lens must be a registered Foundation or Domain risk lens; registry presence does not prove route correctness",
                    )
        decisions = raw_case.get("decisions")
        if not isinstance(decisions, list) or not decisions:
            reject("risk-schema", "decisions must be a non-empty list")
            decisions = []

        prior_floor = "L1"
        prior_effective = "L1"
        phase_results: list[dict[str, object]] = []
        for index, decision in enumerate(decisions):
            if not isinstance(decision, dict) or tuple(decision) != decision_fields:
                reject("risk-schema", f"decision {index} fields or order are invalid")
                continue
            candidate = decision["candidate_l4_predicate"]
            residual_impact = decision["residual_material_impact"]
            candidate_status = {
                "material": "matched",
                "non-material": "non_material",
                "unknown": "unknown",
                "not-applicable": "not_matched",
            }.get(residual_impact)
            assessment = decision["material_assessment"]
            critical = decision["critical_unknown"]
            if candidate not in material_trigger_ids:
                reject("risk-predicate", f"decision {index} candidate L4 predicate is invalid")
                continue
            if candidate_status not in material_statuses:
                reject("risk-residual", f"decision {index} candidate status is invalid")
                continue
            if candidate_status == "not_matched":
                if assessment is not None:
                    reject(
                        "risk-assessment",
                        f"decision {index} not_matched candidate must not have a material assessment",
                    )
                    continue
            elif (
                not isinstance(assessment, dict)
                or list(assessment) != material_fields
                or any(
                    not isinstance(assessment[field], str) or not assessment[field].strip()
                    for field in material_fields
                )
            ):
                reject("risk-assessment", f"decision {index} material assessment is invalid")
                continue
            if critical is not None and (
                candidate_status != "unknown"
                or not isinstance(critical, dict)
                or list(critical) != critical_fields
                or any(
                    not isinstance(critical[field], str) or not critical[field].strip()
                    for field in critical_fields
                )
                or critical["candidate_l4_predicate"] != candidate
            ):
                reject("risk-critical-unknown", f"decision {index} critical unknown is invalid")
                continue
            if not isinstance(decision["l2_eligible"], bool):
                reject("risk-l2", f"decision {index} l2_eligible must be boolean")
                continue

            triggers = {
                row["id"]: {
                    "status": "not_matched",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": f"fixture:{case_id}:decision-{index}:{row['id']}",
                    "plausible_critical": False,
                }
                for row in execution["trigger_registry"]
            }
            triggers[candidate]["status"] = candidate_status
            if candidate_status != "not_matched":
                triggers[candidate]["material_assessment"] = assessment
            if candidate_status == "unknown":
                if critical is not None:
                    unknown = triggers["unknown-critical-boundary"]
                    unknown["status"] = "unknown"
                    unknown["plausible_critical"] = True
                    unknown["critical_unknown"] = critical
            l2 = {
                row["id"]: {
                    "status": "true" if decision["l2_eligible"] else "false",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": f"fixture:{case_id}:decision-{index}:{row['id']}",
                }
                for row in execution["l2_eligibility"]
            }
            if candidate_status in {"matched", "unknown"}:
                l2["no-material-high-risk-residual-impact"]["status"] = "false"
            expected = decision["expected"]
            if not isinstance(expected, dict) or tuple(expected) != expected_fields:
                reject("risk-schema", f"decision {index} expected fields are invalid")
                continue
            try:
                level = compute_execution_level(
                    requested="unspecified",
                    trigger_evaluations=triggers,
                    l2_evaluations=l2,
                    prior_historical_max_floor=prior_floor,
                    prior_historical_max_effective=prior_effective,
                )
                action = classify_concrete_action_authority(decision["action_authority"])
            except ExecutionLevelError as exc:
                reject("risk-evaluation", f"decision {index} is invalid: {exc}")
                continue
            actual = {
                "automatic_level": level["automatic_level"],
                "effective_level": level["effective_level"],
                "edit_status": level["edit_status"],
                "historical_max_floor": level["next_historical_floor"],
                "historical_max_effective": level["next_historical_effective"],
                "action_decision": action["decision"],
            }
            if actual != expected:
                reject(
                    "risk-expectation",
                    f"decision {index} expected {expected!r}, got {actual!r}",
                )
            phase_results.append(actual)
            prior_floor = level["next_historical_floor"]
            prior_effective = level["next_historical_effective"]
        results.append(
            {
                "id": case_id,
                "task_id": raw_case.get("task_id"),
                "professional_risk_signals": signals,
                "selected_primary_skill": raw_case.get("selected_primary_skill"),
                "selected_risk_lenses": lenses,
                "decisions": phase_results,
                "matches_expected": not case_errors,
                "errors": case_errors,
            }
        )
        errors.extend(case_errors)

    lower_security = [
        result
        for result in results
        if "security" in (result["professional_risk_signals"] or [])
        and any(
            decision.get("effective_level") in {"L2", "L3"}
            for decision in result["decisions"]
        )
    ]
    security_skill_lower = [
        result
        for result in lower_security
        if result["selected_primary_skill"] == "security-privacy-gate"
    ]
    if not lower_security:
        errors.append("risk calibration lacks a security signal below L4")
    if not security_skill_lower:
        errors.append("risk calibration lacks Security Skill and Level independence")
    return results, errors


def _completion_fixture_errors(
    raw_cases: object,
    raw_trajectories: object = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(raw_cases, list) or not raw_cases:
        return [], ["completion_state_cases must be a non-empty list"]
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            errors.append("completion state case must be a mapping")
            continue
        case_id = raw_case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            errors.append(f"missing or duplicate completion state case id: {case_id!r}")
            continue
        seen.add(case_id)
        review_authority, authority_errors = _resolve_completion_review_authority(
            raw_case,
            raw_trajectories,
        )
        claim_errors = [
            *authority_errors,
            *completion_claim_errors(
                raw_case.get("claim"),
                review_authority=review_authority,
            ),
        ]
        expected_valid = raw_case.get("expected_valid")
        expected_error = raw_case.get("expected_error")
        if not isinstance(expected_valid, bool):
            errors.append(f"{case_id}: expected_valid must be boolean")
            continue
        actual_valid = not claim_errors
        case_errors: list[str] = []
        if actual_valid != expected_valid:
            case_errors.append(
                f"{case_id}: expected_valid {expected_valid!r}, got {actual_valid!r}: "
                f"{claim_errors}"
            )
        if expected_valid:
            if expected_error is not None:
                case_errors.append(f"{case_id}: valid case must not declare expected_error")
        elif not isinstance(expected_error, str) or not any(
            expected_error in error for error in claim_errors
        ):
            case_errors.append(
                f"{case_id}: negative case did not produce expected error "
                f"{expected_error!r}: {claim_errors}"
            )
        errors.extend(case_errors)
        results.append(
            {
                "id": case_id,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "matches_expected": not case_errors,
                "claim_errors": claim_errors,
            }
        )
    return results, errors


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [item["metrics"] for item in results]
    numeric_names = (
        "time_to_first_productive_action_step",
        "time_to_first_edit_step",
        "total_completion_steps",
        "control_turn_count",
        "subagent_count",
        "duplicate_read_count",
        "verification_action_count",
        "loaded_skill_count",
        "loaded_layer3_reference_count",
        "conditional_isolated_write_reduction_steps",
        "progress_count",
        "productive_action_count",
        "max_silent_steps",
        "progress_to_productive_action_ratio",
    )
    summary: dict[str, Any] = {}
    for name in numeric_names:
        values = [
            value[name]
            for value in metrics
            if isinstance(value.get(name), (int, float))
            and not isinstance(value.get(name), bool)
        ]
        summary[name] = {
            "median": statistics.median(values) if values else None,
            "max": max(values) if values else None,
        }
    return summary


def _write_reports(
    report: dict[str, Any],
    *,
    release_projection: bool = False,
    reports_dir: Path = ROOT / "reports",
) -> None:
    report_json, report_markdown = report_output_paths(
        reports_dir, REPORT_JSON.name, REPORT_MD.name
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Hookless Control Plane Evaluation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Evidence scope: **{report['evidence_scope']}**",
        "",
        f"Release fixtures: **{report['release_fixture_count']}**; "
        f"scheduling fixtures: **{report['scheduling_fixture_count']}**; "
        f"utility fixtures: **{report['utility_fixture_count']}**; "
        f"completion-state controls: **{report['completion_state_fixture_count']}**.",
        "",
        "Deterministic step counts are structural proxies.",
        "",
        "| Scenario | First productive step | First edit step | Control turns | Progress | Max silent steps | Subagents | Skill loads | Layer 3 References | Result |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in report["cases"]:
        metrics = item["metrics"]
        lines.append(
            f"| `{item['id']}` | {metrics['time_to_first_productive_action_step']} | "
            f"{metrics['time_to_first_edit_step']} | {metrics['control_turn_count']} | "
            f"{metrics['progress_count']} | {metrics['max_silent_steps']} | "
            f"{metrics['subagent_count']} | {metrics['loaded_skill_count']} | "
            f"{metrics['loaded_layer3_reference_count']} | "
            f"{'pass' if item['matches_expected'] else 'fail'} |"
        )
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in report["limitations"]], ""])
    if report["errors"]:
        lines.extend(["## Errors", "", *[f"- {error}" for error in report["errors"]], ""])
    if release_projection:
        report_markdown.write_text("\n".join(lines), encoding="utf-8")


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-write-report",
        action="store_true",
        help="validate fixtures without updating checked-in report artifacts",
    )
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    try:
        professional, layer3_entries = _skill_registries()
        document = _load_json(FIXTURES)
        if document.get("schema_version") != FIXTURE_SCHEMA_VERSION:
            raise ValueError(
                f"trajectory fixture schema_version must be {FIXTURE_SCHEMA_VERSION}"
            )
        raw_cases = document.get("cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise ValueError("trajectory fixture must contain a non-empty cases list")
        raw_utility_cases = document.get("utility_cases")
        if not isinstance(raw_utility_cases, list):
            raise ValueError("trajectory fixture must contain a utility_cases list")
        raw_scheduling_cases = document.get("scheduling_cases")
        if not isinstance(raw_scheduling_cases, list):
            raise ValueError("trajectory fixture must contain a scheduling_cases list")
        adaptive_results, adaptive_errors = _adaptive_testing_fixture_results(
            document.get("adaptive_testing_cases")
        )
        review_discipline_results, review_discipline_errors = (
            _review_discipline_fixture_results(document.get("review_discipline_cases"))
        )
        task_focus_results, task_focus_errors = _task_focus_fixture_results(
            document.get("task_focus_cases")
        )
        orchestration_results, orchestration_errors = _orchestration_fixture_results(
            document.get("orchestration_cases")
        )
        combined_review_results, combined_review_errors = (
            _combined_review_fixture_results(document.get("combined_review_cases"))
        )
        external_read_results, external_read_errors = _external_read_fixture_results(
            document.get("external_read_cases")
        )
        risk_calibration_results, risk_calibration_errors = (
            _risk_calibration_fixture_results(document.get("risk_calibration_cases"))
        )
        completion_results, completion_errors = _completion_fixture_errors(
            document.get("completion_state_cases"),
            raw_cases,
        )
        required_behavior_results, required_behavior_errors = (
            _required_behavior_coverage_results(document, professional, layer3_entries)
        )
        results: list[dict[str, Any]] = []
        errors: list[str] = [
            *required_behavior_errors,
            *adaptive_errors,
            *review_discipline_errors,
            *task_focus_errors,
            *orchestration_errors,
            *combined_review_errors,
            *external_read_errors,
            *risk_calibration_errors,
            *completion_errors,
        ]
        if len(raw_cases) != 13:
            errors.append(f"release fixture count must remain exactly 13, found {len(raw_cases)}")
        if len(raw_scheduling_cases) != 1:
            errors.append(
                f"scheduling fixture count must remain exactly 1, found {len(raw_scheduling_cases)}"
            )
        if len(raw_utility_cases) != 2:
            errors.append(f"utility fixture count must remain exactly 2, found {len(raw_utility_cases)}")
        if len(adaptive_results) != 15:
            errors.append(
                "adaptive testing fixture count must remain exactly 15, found "
                f"{len(adaptive_results)}"
            )
        if len(review_discipline_results) != 30:
            errors.append(
                "review discipline fixture count must remain exactly 30, found "
                f"{len(review_discipline_results)}"
            )
        if len(task_focus_results) != 42:
            errors.append(
                "task-focus fixture count must remain exactly 42, found "
                f"{len(task_focus_results)}"
            )
        if len(combined_review_results) != 15:
            errors.append(
                "combined-review fixture count must remain exactly 15, found "
                f"{len(combined_review_results)}"
            )
        if len(external_read_results) != 14:
            errors.append(
                "external-read fixture count must remain exactly 14, found "
                f"{len(external_read_results)}"
            )
        if len(risk_calibration_results) != 13:
            errors.append(
                "risk calibration fixture count must remain exactly 13, found "
                f"{len(risk_calibration_results)}"
            )
        seen: set[str] = set()
        for fixture_group, group_cases in (
            ("release", raw_cases),
            ("scheduling", raw_scheduling_cases),
            ("utility", raw_utility_cases),
        ):
            for raw_case in group_cases:
                if not isinstance(raw_case, dict):
                    errors.append(f"{fixture_group} case must be a mapping")
                    continue
                case_id = str(raw_case.get("id") or "")
                if not case_id or case_id in seen:
                    errors.append(f"missing or duplicate case id: {case_id!r}")
                    continue
                seen.add(case_id)
                metrics, case_errors = _metrics(
                    raw_case,
                    professional,
                    layer3_entries,
                    utility_case=fixture_group == "utility",
                )
                case_errors.extend(_expectation_errors(raw_case, metrics))
                errors.extend(case_errors)
                results.append(
                    {
                        "id": case_id,
                        "kind": raw_case.get("kind"),
                        "fixture_group": fixture_group,
                        "metrics": metrics,
                        "matches_expected": not case_errors,
                        "errors": case_errors,
                    }
                )
    except (ValueError, ValidationProblem) as exc:
        print(f"eval-agent-lightweight: ERROR: {exc}", file=sys.stderr)
        return 1

    report = {
        "schema_version": 2,
        "status": "pass" if not errors else "fail",
        "architecture": "control-plane-prompt + four-agent-profiles + three-layer-skills",
        "evidence_scope": "deterministic-fixtures",
        "limitations": list(EVIDENCE_LIMITATIONS),
        "measurement_scope": document.get("measurement_scope"),
        "fixture_schema_version": document.get("schema_version"),
        "fixture_count": len(results),
        "release_fixture_count": sum(
            item["fixture_group"] == "release" for item in results
        ),
        "scheduling_fixture_count": sum(
            item["fixture_group"] == "scheduling" for item in results
        ),
        "utility_fixture_count": sum(
            item["fixture_group"] == "utility" for item in results
        ),
        "completion_state_fixture_count": len(completion_results),
        "completion_state_fixtures": completion_results,
        "required_behavior_coverage_count": len(required_behavior_results),
        "required_behavior_coverage": required_behavior_results,
        "adaptive_testing_fixture_count": len(adaptive_results),
        "adaptive_testing_fixtures": adaptive_results,
        "review_discipline_fixture_count": len(review_discipline_results),
        "review_discipline_fixtures": review_discipline_results,
        "task_focus_fixture_count": len(task_focus_results),
        "task_focus_fixtures": task_focus_results,
        "orchestration_fixture_count": len(orchestration_results),
        "orchestration_fixtures": [
            {
                key: value
                for key, value in result.items()
                if key != "semantic_trace"
            }
            for result in orchestration_results
        ],
        "semantic_traces": [
            result["semantic_trace"] for result in orchestration_results
        ],
        "combined_review_fixture_count": len(combined_review_results),
        "combined_review_fixtures": combined_review_results,
        "external_read_fixture_count": len(external_read_results),
        "external_read_fixtures": external_read_results,
        "risk_calibration_fixture_count": len(risk_calibration_results),
        "risk_calibration_fixtures": risk_calibration_results,
        "cases": results,
        "parallelism_contract": {
            "current_read_only_parallelism": "declared-supported",
            "current_write_parallelism": "unsupported-on-declared-hosts",
            "shared_workspace_serial_write": any(
                item["metrics"].get("shared_workspace_writes_serial")
                for item in results
                if item["fixture_group"] == "scheduling"
            ),
            "isolated_write_parallelism": "conditional-contract-only",
        },
        "aggregate_structural_proxies": _aggregate(results),
        "errors": errors,
    }
    if not args.no_write_report:
        _write_reports(
            report,
            release_projection=args.release_projection,
            reports_dir=args.reports_dir,
        )
    if errors:
        for error in errors:
            print(f"eval-agent-lightweight: ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "eval-agent-lightweight: validated "
        f"{report['release_fixture_count']} release and "
        f"{report['scheduling_fixture_count']} scheduling and "
        f"{report['utility_fixture_count']} utility trajectories plus "
        f"{report['required_behavior_coverage_count']} required-behavior entries and "
        f"{report['adaptive_testing_fixture_count']} adaptive-testing controls and "
        f"{report['review_discipline_fixture_count']} review-discipline controls and "
        f"{report['task_focus_fixture_count']} task-focus controls and "
        f"{report['orchestration_fixture_count']} orchestration controls and "
        f"{report['combined_review_fixture_count']} combined-review controls and "
        f"{report['external_read_fixture_count']} external-read controls and "
        f"{report['risk_calibration_fixture_count']} risk-calibration controls and "
        f"{report['completion_state_fixture_count']} completion-state controls."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
