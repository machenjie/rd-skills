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
    ValidationProblem,
    load_yaml_file,
    professional_review_skill_ids,
    reference_paths,
)
from fixture_capsule_contract import (
    FixtureCapsuleError,
    UTILITY_ASSIGNMENT_FIELDS,
    UTILITY_ASSIGNMENT_REQUIRED_CLAIMS,
    UTILITY_RETURN_FIELDS,
    UTILITY_RETURN_REQUIRED_CLAIMS,
    completion_claim_errors as _core_completion_claim_errors,
    completion_transition_errors,
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
ADAPTIVE_TEST_EVIDENCE_ACTION = "adaptive-test-evidence"
INTERNAL_EVIDENCE_ACTIONS = {
    "implementation-discipline",
    ADAPTIVE_TEST_EVIDENCE_ACTION,
    REVIEW_DISCIPLINE_MODEL["trace_action"],
}
WORKER_EVIDENCE_ACTIONS = PRODUCTIVE_ACTIONS | {"brief", "task_plan", "finding"}
EDIT_ACTIONS = {"edit", "repair"}
REVIEW_ACTIONS = {"review", "re-review"}
MAIN_ACTIONS = {"classify", "dispatch", "progress", "escalate", "user_decision", "close"}
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
        "export-diff",
        "implementation-discipline",
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
TASK_BOUNDARY_MODEL = CORE_CONTRACTS["task_contract"]["task_boundary"]
FINDING_RELATION_MODEL = CORE_CONTRACTS["task_contract"]["finding_relations"]
SAME_PATTERN_MODEL = CORE_CONTRACTS["task_contract"]["same_pattern_scan"]
REVIEW_LEVEL_POLICY = REVIEW_DISCIPLINE_MODEL["effective_level_policy"]
UTILITY_MODES = {"validation-only/no-edit", "diff-export/no-edit"}
UTILITY_CAPSULE_FIELDS = UTILITY_ASSIGNMENT_FIELDS
UTILITY_EVIDENCE_FIELDS = UTILITY_RETURN_FIELDS
UTILITY_ASSIGNMENT_STATUSES = {"in_progress"}
UTILITY_RETURN_STATUSES = {"blocked", "partial", "completed"}
FORBIDDEN_UTILITY_COMMAND_FRAGMENTS = (
    "curl ",
    "wget ",
    "http://",
    "https://",
    "ssh ",
    "git fetch",
    "git pull",
    "git push",
    "git clone",
    "git checkout",
    "git switch",
    "git reset",
    "git clean",
    "git add",
    "git commit",
    "rm ",
    " >",
)
VALIDATION_COMMAND_PREFIXES = (
    "python3 -m unittest ",
    "python -m unittest ",
    "pytest ",
    "npm test",
    "pnpm test",
    "yarn test",
    "go test ",
    "cargo test",
    "mvn test",
    "gradle test",
    "./gradlew test",
    "make test",
    "equivalent-non-modifying-check ",
)
WORKSPACE_CHECK_COMMANDS = (
    "git status --porcelain=v1 --untracked-files=all",
    "git --no-pager diff --no-ext-diff --no-textconv --binary HEAD",
    "git --no-pager diff --no-ext-diff --no-textconv --cached --binary HEAD",
)


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
UTILITY_NO_EDIT_ENFORCEMENT = "prompt-enforced"
PROGRESS_TO_PRODUCTIVE_RATIO_MAX = 0.75
MULTI_AGENT_PROGRESS_MIN = 3
MULTI_AGENT_PROGRESS_MAX = 5
MAX_SILENT_STRUCTURAL_STEPS = 5
FORBIDDEN_UTILITY_SHELL_SYNTAX_RE = re.compile(r"[\r\n;|&<>\x60$(){}]")
GIT_DIFF_SHOW_ALLOWED_OPTIONS = {
    "--binary",
    "--cached",
    "--check",
    "--full-index",
    "--name-only",
    "--name-status",
    "--no-color",
    "--no-ext-diff",
    "--no-textconv",
    "--numstat",
    "--patch",
    "--shortstat",
    "--staged",
    "--stat",
    "--summary",
    "-p",
}
GIT_DIFF_SHOW_ALLOWED_OPTION_PATTERNS = (
    re.compile(r"--abbrev=\d+\Z"),
    re.compile(r"--color=never\Z"),
    re.compile(r"--unified=\d+\Z"),
    re.compile(r"-U\d+\Z"),
)
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

        dispatch = next(
            (
                step
                for step in reversed(steps[: event_index + 1])
                if step.get("action") == "dispatch"
                and step.get("profile") == "review-agent"
            ),
            None,
        )
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
            if (
                not isinstance(diff.get("artifact"), str)
                or not diff["artifact"].strip()
                or diff.get("generation") != generation
            ):
                reject(
                    "review-old-diff",
                    "review requires the actual latest diff generation after the latest modification",
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
            "artifact": "actual.diff",
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
    steps = [edit, validation, event, review]
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
    if scenario not in {"finding", "same-pattern", "repair", "review-level", "cost"}:
        reject("focus-scenario", "task-focus scenario is not in the closed set")
        return errors
    if not isinstance(inputs, dict) or not isinstance(decision, dict):
        reject("focus-shape", "task-focus inputs and decision must be mappings")
        return errors

    if scenario == "finding":
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

    else:
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


def _git_diff_show_options_are_safe(command: str) -> bool:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False
    if len(tokens) < 3 or tokens[:3] not in (
        ["git", "--no-pager", "diff"],
        ["git", "--no-pager", "show"],
    ):
        return False
    required_safety_options = {"--no-ext-diff", "--no-textconv"}
    seen_options: set[str] = set()
    after_path_separator = False
    for token in tokens[3:]:
        if after_path_separator:
            continue
        if token == "--":
            after_path_separator = True
            continue
        if not token.startswith("-"):
            continue
        if token in GIT_DIFF_SHOW_ALLOWED_OPTIONS:
            seen_options.add(token)
            continue
        if any(pattern.fullmatch(token) for pattern in GIT_DIFF_SHOW_ALLOWED_OPTION_PATTERNS):
            continue
        return False
    return required_safety_options <= seen_options


def _utility_command_is_safe(command: str) -> bool:
    folded = command.casefold()
    shell_safe = (
        FORBIDDEN_UTILITY_SHELL_SYNTAX_RE.search(command) is None
        and not any(fragment in folded for fragment in FORBIDDEN_UTILITY_COMMAND_FRAGMENTS)
    )
    if not shell_safe:
        return False
    if folded.startswith(("git --no-pager diff ", "git --no-pager show ")):
        return _git_diff_show_options_are_safe(command)
    if folded.startswith("git ") and command not in WORKSPACE_CHECK_COMMANDS:
        return False
    return True


def _workspace_check_command(command: str) -> bool:
    return command in WORKSPACE_CHECK_COMMANDS or command.startswith(
        "equivalent-read-only-workspace-change-set "
    )


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
    if capsule.get("no_edit_enforcement") != UTILITY_NO_EDIT_ENFORCEMENT:
        errors.append(
            f"{case_id}: utility capsule at step {index} must declare "
            f"no_edit_enforcement={UTILITY_NO_EDIT_ENFORCEMENT!r}"
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
            if mode == "diff-export/no-edit" and not command.startswith(
                (
                    "git --no-pager diff ",
                    "git --no-pager show ",
                    "equivalent-read-only-diff ",
                )
            ):
                errors.append(
                    f"{case_id}: diff-export utility at step {index} allows non-diff command"
                )
            if mode == "validation-only/no-edit" and command.startswith(
                (
                    "git --no-pager diff ",
                    "git --no-pager show ",
                    "equivalent-read-only-diff ",
                )
            ):
                errors.append(
                    f"{case_id}: validation utility at step {index} allows diff export"
                )
            elif mode == "validation-only/no-edit" and not command.startswith(
                VALIDATION_COMMAND_PREFIXES
            ):
                errors.append(
                    f"{case_id}: validation utility at step {index} allows a command "
                    "not declared as a non-modifying check"
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
    host_modes = case.get("host_modes")
    if not isinstance(host_modes, dict):
        errors.append(f"{case_id}: utility case must declare host_modes")
        host_modes = {}
    mode = capsule.get("mode")
    if host_modes.get("utility_no_edit") != UTILITY_NO_EDIT_ENFORCEMENT:
        errors.append(
            f"{case_id}: utility case requires utility_no_edit="
            f"{UTILITY_NO_EDIT_ENFORCEMENT}"
        )
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
        if host_modes.get("diff_input_mode") != "supplied-artifact":
            errors.append(f"{case_id}: diff-export case requires supplied-artifact mode")
        if case.get("actual_diff_supplied") is not False:
            errors.append(f"{case_id}: diff-export case requires a missing supplied diff")
        if result.get("action") != "export-diff":
            errors.append(f"{case_id}: diff-export utility must return export-diff evidence")
        artifact_ref = result.get("artifact_ref")
        if not isinstance(artifact_ref, str) or not artifact_ref.startswith(
            ("utility-return:", "host-native:")
        ):
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
        if host_modes.get("validation_mode") != "task-no-edit":
            errors.append(f"{case_id}: validation utility requires task-no-edit mode")
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
                prior.get("action") in REVIEW_ACTIONS | {"finding"}
                and prior.get("evidence_id") == parts[1]
                and prior.get("outcome") == parts[2]
                for prior in prior_steps
            )
        )
        if not matched:
            return (
                f"{case_id}: review/close progress at step {index} must bind a "
                "prior review evidence id and outcome"
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
        "host_mode",
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
        "read_only_capability_proven",
        "connector_authorized",
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
    modes = set(EXTERNAL_READ_MODEL["capability_modes"])
    operations = {"not-applicable", *EXTERNAL_READ_MODEL["supported_operations"]}
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
        mode = raw_case.get("host_mode")
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
        if mode not in modes:
            reject("external-read-host-mode", "host mode is outside the closed enum")
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
            if mode == "unsupported" or not triggered:
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
            if mode == "unsupported":
                reject("external-read-host-mode", "unsupported host cannot actively read externally")
            if request.get("targeted_claim") is not True:
                reject("external-read-jit", "external request must target one material Claim")
            if request.get("minimum_public_information") is not True:
                reject("external-read-disclosure", "request is not minimized to public information")
            if request.get("contains_protected_content") is not False:
                reject(
                    "external-read-disclosure",
                    "request contains protected content: " + ", ".join(protected_fields),
                )
            if request.get("read_only_capability_proven") is not True:
                reject("external-read-host-mode", "read-only capability is not proven")
            if not isinstance(request.get("value"), str) or not request["value"].strip():
                reject("external-read-schema", "external request value must be non-empty")
            if operation == "ConnectorRead" and request.get("connector_authorized") is not True:
                reject("external-read-operation", "ConnectorRead must be authorized and proven read-only")
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
            if ledger.get("Command") != operation:
                reject("external-read-ledger", "ledger Command must name the external read operation")
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


def _write_reports(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-write-report",
        action="store_true",
        help="validate fixtures without updating checked-in report artifacts",
    )
    args = parser.parse_args()
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
        external_read_results, external_read_errors = _external_read_fixture_results(
            document.get("external_read_cases")
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
            *external_read_errors,
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
        if len(task_focus_results) != 25:
            errors.append(
                "task-focus fixture count must remain exactly 25, found "
                f"{len(task_focus_results)}"
            )
        if len(external_read_results) != 14:
            errors.append(
                "external-read fixture count must remain exactly 14, found "
                f"{len(external_read_results)}"
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
        "external_read_fixture_count": len(external_read_results),
        "external_read_fixtures": external_read_results,
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
        _write_reports(report)
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
        f"{report['external_read_fixture_count']} external-read controls and "
        f"{report['completion_state_fixture_count']} completion-state controls."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
