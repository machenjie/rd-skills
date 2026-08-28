#!/usr/bin/env python3
"""Measure deterministic rendered instruction context with exact token budgets."""

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
import tempfile
import unicodedata
from collections import Counter, defaultdict
from contextlib import contextmanager
from itertools import combinations
from pathlib import Path, PurePosixPath
from typing import Any

from validation_utils import (
    BEHAVIOR_EVAL_MODEL,
    COMPILED_LAYER3_FORMAT,
    CONTEXT_BUDGET_MODEL,
    CORE_CONTRACTS,
    REVIEW_DISCIPLINE_MODEL,
    ValidationProblem,
    authoritative_build_input_snapshot,
    behavior_eval_authority,
    count_o200k_base_tokens,
    derived_context_budget_limits,
    layer3_selector_authority,
    layer3_selector_control_projections,
    layer3_selector_expand_runtime_projection,
    layer3_selector_resolve_control_projection,
    layer3_selector_runtime_projection,
    layer3_selector_runtime_selection_receipt,
    layer3_selector_runtime_selection_receipt_errors,
    load_yaml_file,
    parse_frontmatter,
    reference_context_admissibility_authority,
    reference_context_admissibility_decisions,
    reference_context_staged_plan,
    reference_paths,
    report_output_paths,
)
from fixture_capsule_contract import (
    CONTRACT_VERSION as FIXTURE_CAPSULE_CONTRACT_VERSION,
    FixtureCapsuleError,
    parse_layer3_reference_id,
    trace_execution_level_migration_errors,
    validate_and_render_fixture_capsule,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "agent-light-trajectories" / "cases.yaml"
DIST_SKILLS = ROOT / "dist" / "universal" / "skills"
CONTROL_PROMPT = ROOT / "src" / "control-prompts" / "main-control-agent.md"
REPORT_JSON = ROOT / "reports" / "rendered-context-budget.json"
REPORT_MD = ROOT / "reports" / "rendered-context-budget.md"
LIGHTWEIGHT_REPORT = ROOT / "reports" / "hookless-control-plane-eval.json"
IMPLEMENTATION_HANDOFF_TEMPLATE = (
    ROOT
    / "src"
    / "control-skills"
    / "engineering-control-plane"
    / "references"
    / "implementation-handoff-template.md"
)
REVIEW_HANDOFF_TEMPLATE = IMPLEMENTATION_HANDOFF_TEMPLATE.with_name(
    "review-handoff-template.md"
)
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"

BUILD_PROFILES = ("recommended", "full", "dev")
REVIEW_ROUND_COMPLETION_ACTIONS = {"review", "re-review"}
HOST_PROFILE_ROOTS = {
    "codex": ROOT / "dist" / "codex" / "project" / ".codex" / "agents",
    "claude": ROOT / "dist" / "claude" / "project" / ".claude" / "agents",
    "copilot": ROOT / "dist" / "copilot" / "project" / ".github" / "agents",
}
HOST_PROFILE_SUFFIXES = {
    "codex": ".toml",
    "claude": ".md",
    "copilot": ".agent.md",
}


@contextmanager
def _subject_configuration(
    root: Path,
    fixtures: Path,
    lightweight_report: Path,
):
    global ROOT, FIXTURES, DIST_SKILLS, CONTROL_PROMPT, LIGHTWEIGHT_REPORT
    global IMPLEMENTATION_HANDOFF_TEMPLATE, REVIEW_HANDOFF_TEMPLATE
    global PROFESSIONAL_REGISTRY, FOUNDATION_REGISTRY, DOMAIN_REGISTRY
    global HOST_PROFILE_ROOTS
    names = (
        "ROOT",
        "FIXTURES",
        "DIST_SKILLS",
        "CONTROL_PROMPT",
        "LIGHTWEIGHT_REPORT",
        "IMPLEMENTATION_HANDOFF_TEMPLATE",
        "REVIEW_HANDOFF_TEMPLATE",
        "PROFESSIONAL_REGISTRY",
        "FOUNDATION_REGISTRY",
        "DOMAIN_REGISTRY",
        "HOST_PROFILE_ROOTS",
    )
    saved = {name: globals()[name] for name in names}
    ROOT = root.resolve()
    FIXTURES = fixtures.resolve()
    DIST_SKILLS = ROOT / "dist/universal/skills"
    CONTROL_PROMPT = ROOT / "src/control-prompts/main-control-agent.md"
    LIGHTWEIGHT_REPORT = lightweight_report.resolve()
    IMPLEMENTATION_HANDOFF_TEMPLATE = ROOT / (
        "src/control-skills/engineering-control-plane/references/"
        "implementation-handoff-template.md"
    )
    REVIEW_HANDOFF_TEMPLATE = IMPLEMENTATION_HANDOFF_TEMPLATE.with_name(
        "review-handoff-template.md"
    )
    PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
    FOUNDATION_REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
    DOMAIN_REGISTRY = ROOT / "src/registry/domain-skills.yaml"
    HOST_PROFILE_ROOTS = {
        "codex": ROOT / "dist/codex/project/.codex/agents",
        "claude": ROOT / "dist/claude/project/.claude/agents",
        "copilot": ROOT / "dist/copilot/project/.github/agents",
    }
    try:
        yield
    finally:
        globals().update(saved)
CONTEXT_BUDGET_LIMITS = derived_context_budget_limits(CONTEXT_BUDGET_MODEL)
DISPATCH_COMPOSITION_CLASSES = tuple(
    CONTEXT_BUDGET_MODEL["context_taxonomy"]["dispatch_composition"]["classes"]
)
ADMISSIBLE_BUDGET_CLASSES = tuple(
    budget_class
    for budget_class in DISPATCH_COMPOSITION_CLASSES
    if budget_class != "utility"
)
ADMISSIBLE_COMPOSITION_CONTRACT = (
    "changeforge.admissible-context-composition-eval/v1"
)
CONTEXT_COMPONENT_SEPARATOR_TOKENS = count_o200k_base_tokens("\n\n")
DUPLICATE_TOKEN_RATIO_MAX = CONTEXT_BUDGET_MODEL[
    "duplicate_rule_token_ratio_max"
]
MIN_DUPLICATE_BLOCK_CHARS = 50
MIN_DUPLICATE_BLOCK_TOKENS = 12
MODE_REFERENCES = {
    "implementation-preparation": "references/implementation-preparation.md",
    "diagnosis-only": "references/diagnosis-only.md",
    "source-backed-answer": "references/source-backed-answer.md",
}
LIMITATIONS = (
    "Counts cover deterministic rendered rd-skills instructions and canonical Capsules rendered from versioned checked-in fixture data, not a host-observed model request.",
    "Counts exclude host system prompts, tool schemas, user conversation history, repository reads, diffs, command output, and other dynamic evidence.",
    "Host loaders may transform Profile or Skill files and may expose discovery metadata differently; this report does not prove real-host accuracy.",
    "Token counts do not prove wall-clock performance, production accuracy, Profile startup, or the installed user experience.",
    "Duplicate-token measurement detects exact normalized Markdown rule blocks, not semantic paraphrases.",
    "Nested Layer 3 Reference counts include only explicitly named fixture files; directories, indexes, catalogs, and recursively linked files are never loaded.",
)
FIXTURE_SCHEMA_VERSION = 2
TRANSFER_CATEGORY_ORDER = (
    "authority",
    "skill_reference",
    "task_capsule",
    "implementation_handoff",
    "evidence_ledger",
    "diff",
    "validation",
    "review_handoff",
    "repair_context",
    "duplicate_context",
    "superseded_evidence",
)
TRANSFER_CATEGORY_LABELS = {
    "authority": "Authority",
    "skill_reference": "Skill / Reference",
    "task_capsule": "Task Capsule",
    "implementation_handoff": "Implementation Handoff",
    "evidence_ledger": "Evidence Ledger",
    "diff": "Diff",
    "validation": "Validation",
    "review_handoff": "Review Handoff",
    "repair_context": "Repair Context",
    "duplicate_context": "duplicate context",
    "superseded_evidence": "superseded evidence",
}
TRANSFER_EXCLUSIVE_CATEGORIES = (
    "authority",
    "skill_reference",
    "task_capsule",
    "implementation_handoff",
    "review_handoff",
    "repair_context",
)
TRANSFER_OVERLAP_VIEWS = tuple(
    item for item in TRANSFER_CATEGORY_ORDER if item not in TRANSFER_EXCLUSIVE_CATEGORIES
)
END_TO_END_COMPONENTS = (
    "always_loaded",
    "dispatch_instructions",
    "professional",
    "layer3",
    "selector",
    "reference_partition",
    "targeted_reference",
    "cross_agent_transfer",
)
END_TO_END_STRUCTURAL_COUNTERS = (
    "selector_load_count",
    "reference_partition_load_count",
    "envelope_count",
    "reference_load_count",
    "reference_tokens",
    "handoff_count",
    "handoff_tokens",
    "same_assignment_duplicate_read_count",
    "end_to_end_context_occurrence_count",
)
END_TO_END_COVERAGE_COUNTERS = (
    "envelope_count",
    "reference_load_count",
    "handoff_count",
    "same_assignment_duplicate_read_count",
    "end_to_end_context_occurrence_count",
)
FOCUS_CURRENT_ONLY_MAP = {
    "focus-review-digest-placeholder-blocked": "focus-review-summary-is-not-evidence",
    "focus-review-command-output-placeholder-blocked": "focus-review-summary-is-not-evidence",
    "focus-review-opaque-reference-blocked": "focus-review-summary-is-not-evidence",
    "focus-review-path-only-blocked": "focus-review-summary-is-not-evidence",
    "focus-review-missing-latest-changed-paths-blocked": "focus-review-missing-change-evidence-blocked",
    "focus-review-missing-fixed-scope-blocked": "focus-review-missing-change-evidence-blocked",
    "focus-review-missing-reviewer-consumption-blocked": "focus-review-unsupported-capability-blocked",
    "l4-risk-depth-not-frequency": "focus-review-l4-actual-gates-only",
    "engineering-choice-not-user-choice": "focus-direct-task-level-unchanged",
}
FOCUS_PROTECTED_SEMANTIC_EXTENSIONS = {
    "l4-risk-depth-not-frequency": {
        "baseline_id": "focus-review-l4-actual-gates-only",
        "candidate_native_sha256": "2be6b6da02472e37028db4cbf6e73b25b93dac3a895a7ea5bf43cda76ae19d90",
        "baseline_native_sha256": "b70da853565a78b65e0864469d8127ea002ff8baa28188f8066827d7e3fb6eb4",
        "candidate_semantic_sha256": "b66435d6fe768fe2a9aae9a2bafe10bf9594e2ffd709d854be0adc2de44a6f87",
        "baseline_semantic_sha256": "4ba1d82057ea5aa29d690672171d48d607cf5a5dc39716af86e624a9bf551376",
        "candidate_actor": "review-agent",
        "baseline_actor": "review-agent",
    },
    "engineering-choice-not-user-choice": {
        "baseline_id": "focus-direct-task-level-unchanged",
        "candidate_native_sha256": "dab625f164c8aabf0f3fd2b72b88ec428bde187858a2237b11677442dc7c17cf",
        "baseline_native_sha256": "0ec86a72e58ff4ee5f1db945710db1536ee7e28a7aca51524d90e19644b9f567",
        "candidate_semantic_sha256": "7f19132183309dab8971127796678ae5f3376ac2768f2aa446598ec6f3c3abdf",
        "baseline_semantic_sha256": "a624167a69447dcff8cc5e0a9226f86a7876af5f50fbd38eb67174e36d5da4f3",
        "candidate_actor": "main-control-agent",
        "baseline_actor": "main-control-agent",
    },
}
FOCUS_SCENARIO_ACTORS = {
    "finding": "review-agent",
    "same-pattern": "task-agent",
    "repair": "task-agent",
    "review-level": "review-agent",
    "analysis-level": "main-control-agent",
    "review-readiness": "main-control-agent",
    "capability-equivalence": "main-control-agent",
    "cost": "task-agent",
    "engineering-choice": "main-control-agent",
}
FOCUS_PROFILE_HOSTS = ("codex", "claude", "copilot")
REFERENCE_SEMANTIC_EQUIVALENCE = {
    (
        "api-contract-change",
        "architecture-impact-reviewer",
        "references/architecture-output-and-gates.md",
    ): "architecture-consumer-and-data-impact",
    (
        "api-contract-change",
        "architecture-impact-reviewer",
        "references/consumer-and-data-impact.md",
    ): "architecture-consumer-and-data-impact",
    (
        "single-module-feature",
        "architecture-impact-reviewer",
        "references/architecture-output-and-gates.md",
    ): "architecture-placement-and-ownership",
    (
        "single-module-feature",
        "architecture-impact-reviewer",
        "references/placement-and-ownership.md",
    ): "architecture-placement-and-ownership",
}
TRANSFER_PROJECTION_FIELDS = {
    "task_to_implementation": (
        "task_id",
        "status",
        "changed_files",
        "actual_diff",
        "commands",
        "validation_result",
        "freshness",
        "current_evidence",
        "unverified_scope",
        "residual_risk",
    ),
    "implementation_to_review": (
        "acceptance",
        "review_boundary",
        "effective_level",
        "required_review_skills",
        "required_changed_scope",
        "latest_diff",
        "current_validation",
        "current_evidence",
        "scope",
        "freshness",
        "proof_limit",
        "unverified_scope",
    ),
    "review_to_repair": (
        "repair_batch_key",
        "blocking_findings",
        "finding_obligations",
        "affected_scope",
        "acceptance_impact",
        "latest_diff",
        "invalidated_evidence",
        "reusable_evidence",
        "required_validation",
        "required_rereview",
    ),
}
_RAW_LOG_FIELDS = frozenset({"log", "logs", "full_log", "stdout", "stderr"})
TRANSFER_PROOF_LIMITS = (
    "Transferred-context counts are deterministic projections from checked-in trace fields, canonical Capsules, and current handoff contracts; they are not host-observed requests or model responses.",
    "Skill / Reference counts cover only selectors crossing the dispatch boundary; full loaded Skill content remains measured by the existing rendered instruction contexts.",
    "Execution Delta, review input, and repair input are bounded field projections; the fixtures do not store full natural-language handoff bodies.",
    "Diff counts cover actual-diff metadata or an accessible fixture reference, not diff contents; validation is structured and excludes full command logs, which remain JIT-only.",
    "Duplicate context detects exact normalized blocks in the projected transfers, not semantic paraphrases.",
    "Current-evidence selection uses explicit fixture ordering and freshness; it does not infer unstated runtime evidence.",
)

_LIST_ITEM_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.*)$")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s+|$)")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")
_HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$")
_MARKDOWN_LINK_RE = re.compile(r"\[([^]]+)\]\([^)]+\)")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _component(kind: str, path: str, text: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": path,
        "sha256": _sha256_text(text),
        "tokens": count_o200k_base_tokens(text),
        "_text": text,
    }


def _file_component(kind: str, path: Path) -> dict[str, Any]:
    return _component(kind, _relative(path), path.read_text(encoding="utf-8"))


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :])
    return text


def _normalize_rule_block(block: str) -> str:
    value = unicodedata.normalize("NFKC", block)
    value = _MARKDOWN_LINK_RE.sub(r"\1", value)
    value = re.sub(r"[`*_~>]", "", value)
    value = " ".join(value.casefold().split())
    return value.strip()


def _markdown_rule_blocks(text: str) -> list[str]:
    """Return non-overlapping normalized prose/list blocks for exact copy checks."""

    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        if not current:
            return
        normalized = _normalize_rule_block(" ".join(current))
        current.clear()
        if len(normalized) < MIN_DUPLICATE_BLOCK_CHARS:
            return
        if count_o200k_base_tokens(normalized) < MIN_DUPLICATE_BLOCK_TOKENS:
            return
        blocks.append(normalized)

    for raw_line in _strip_frontmatter(text).splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("```", "~~~")):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            flush()
            continue
        if (
            _HEADING_RE.match(raw_line)
            or _HTML_COMMENT_RE.match(raw_line)
            or _TABLE_SEPARATOR_RE.match(raw_line)
            or (stripped.startswith("|") and stripped.endswith("|"))
        ):
            flush()
            continue
        list_match = _LIST_ITEM_RE.match(raw_line)
        if list_match:
            flush()
            current.append(list_match.group(1))
            continue
        current.append(stripped)
    flush()
    return blocks


def _duplicate_block_metrics(components: list[dict[str, Any]]) -> dict[str, Any]:
    occurrences: dict[str, list[str]] = defaultdict(list)
    for component in components:
        component_id = f"{component['kind']}:{component['path']}"
        for block in _markdown_rule_blocks(component["_text"]):
            occurrences[block].append(component_id)

    duplicate_tokens = 0
    duplicate_blocks: list[dict[str, Any]] = []
    for block, source_occurrences in occurrences.items():
        if len(source_occurrences) < 2:
            continue
        block_tokens = count_o200k_base_tokens(block)
        repeated_tokens = block_tokens * (len(source_occurrences) - 1)
        source_counts: dict[str, int] = defaultdict(int)
        for source in source_occurrences:
            source_counts[source] += 1
        duplicate_tokens += repeated_tokens
        duplicate_blocks.append(
            {
                "sha256": _sha256_text(block),
                "tokens_per_extra_copy": block_tokens,
                "occurrence_count": len(source_occurrences),
                "extra_copy_count": len(source_occurrences) - 1,
                "duplicate_tokens": repeated_tokens,
                "sources": [
                    {"component": source, "occurrences": count}
                    for source, count in sorted(source_counts.items())
                ],
                "preview": block[:160],
            }
        )
    duplicate_blocks.sort(
        key=lambda item: (-item["duplicate_tokens"], item["sha256"])
    )
    return {
        "duplicate_rule_tokens": duplicate_tokens,
        "duplicate_blocks": duplicate_blocks,
    }


def _canonical_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _long_task_ids_from_lightweight(
    report: dict[str, Any],
    expected_case_ids: set[str],
) -> set[str]:
    """Join long-task selection to the existing lightweight report metric."""

    if report.get("schema_version") != 2:
        raise ValueError("lightweight prerequisite report must use schema_version 2")
    if report.get("fixture_schema_version") != FIXTURE_SCHEMA_VERSION:
        raise ValueError("lightweight prerequisite report has stale fixture_schema_version")
    if report.get("status") != "pass":
        raise ValueError("lightweight prerequisite report must have status 'pass'")
    if report.get("evidence_scope") != "deterministic-fixtures":
        raise ValueError(
            "lightweight prerequisite report must use deterministic-fixtures evidence"
        )
    cases = report.get("cases")
    if not isinstance(cases, list) or report.get("fixture_count") != len(cases):
        raise ValueError("lightweight prerequisite report cases/count are malformed")
    actual_ids: set[str] = set()
    long_ids: set[str] = set()
    for index, item in enumerate(cases):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError(f"lightweight prerequisite case {index} needs an id")
        case_id = item["id"]
        metrics = item.get("metrics")
        if not isinstance(metrics, dict) or not isinstance(
            metrics.get("required_progress_for_multi_agent"), bool
        ):
            raise ValueError(
                f"lightweight prerequisite case {case_id!r} metric "
                "required_progress_for_multi_agent must be boolean"
            )
        if case_id in actual_ids:
            raise ValueError(f"lightweight prerequisite repeats case id {case_id!r}")
        actual_ids.add(case_id)
        if metrics["required_progress_for_multi_agent"]:
            long_ids.add(case_id)
    if actual_ids != expected_case_ids:
        raise ValueError(
            "lightweight prerequisite fixture IDs do not match the rendered fixture"
        )
    if not long_ids:
        raise ValueError("lightweight prerequisite selects no long tasks")
    _retained_semantic_equality_evidence(report)
    return long_ids


def _retained_semantic_equality_evidence(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Consume the lightweight reducer's independent equality result."""

    fixtures = report.get("orchestration_fixtures")
    traces = report.get("semantic_traces")
    declared_count = report.get("orchestration_fixture_count")
    if (
        not isinstance(fixtures, list)
        or not isinstance(traces, list)
        or declared_count != len(fixtures)
        or declared_count != len(traces)
    ):
        raise ValueError(
            "lightweight prerequisite retained semantic equality evidence is absent"
        )
    fixture_ids: list[str] = []
    trace_ids: list[str] = []
    positive_ids: list[str] = []
    for index, fixture in enumerate(fixtures):
        if not isinstance(fixture, dict) or not isinstance(fixture.get("id"), str):
            raise ValueError(
                f"lightweight prerequisite orchestration fixture {index} needs an id"
            )
        fixture_id = fixture["id"]
        fixture_ids.append(fixture_id)
        expected_valid = fixture.get("expected_valid")
        if not isinstance(expected_valid, bool):
            raise ValueError(
                f"lightweight prerequisite orchestration fixture {fixture_id!r} "
                "needs expected_valid"
            )
        if expected_valid:
            positive_ids.append(fixture_id)
            if fixture.get("retained_semantic_equality") is not True:
                raise ValueError(
                    "lightweight prerequisite retained semantic equality is not true "
                    f"for {fixture_id!r}"
                )
    for index, trace in enumerate(traces):
        if not isinstance(trace, dict) or not isinstance(trace.get("id"), str):
            raise ValueError(
                f"lightweight prerequisite semantic trace {index} needs an id"
            )
        trace_ids.append(trace["id"])
    if (
        len(fixture_ids) != len(set(fixture_ids))
        or len(trace_ids) != len(set(trace_ids))
        or set(fixture_ids) != set(trace_ids)
    ):
        raise ValueError(
            "lightweight prerequisite retained semantic equality identities are malformed"
        )
    return {
        "source": f"{_relative(LIGHTWEIGHT_REPORT)}#/orchestration_fixtures",
        "orchestration_fixture_count": declared_count,
        "positive_fixture_count": len(positive_ids),
        "positive_fixture_ids": sorted(positive_ids),
        "retained_semantic_equality": True,
        "derivation": "consumed lightweight reducer result; no second semantic reducer",
    }


def _load_lightweight_prerequisite(
    expected_case_ids: set[str],
) -> tuple[set[str], dict[str, Any]]:
    try:
        value = json.loads(LIGHTWEIGHT_REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"cannot read passing lightweight prerequisite {LIGHTWEIGHT_REPORT}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError("lightweight prerequisite report root must be an object")
    return (
        _long_task_ids_from_lightweight(value, expected_case_ids),
        _retained_semantic_equality_evidence(value),
    )


def _load_lightweight_long_task_ids(expected_case_ids: set[str]) -> set[str]:
    """Compatibility accessor for the source-bound long-task selector."""

    return _load_lightweight_prerequisite(expected_case_ids)[0]


def _manifest_input_identity(
    dist_root: Path, expected_input: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    manifests: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for profile in BUILD_PROFILES:
        path = dist_root / profile / ".changeforge-build-manifest.json"
        try:
            raw = path.read_bytes()
            manifest = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{profile} manifest unavailable or malformed: {exc}")
            continue
        if not isinstance(manifest, dict) or manifest.get("profile") != profile:
            errors.append(f"{profile} manifest profile identity mismatch")
            continue
        if manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
            errors.append(f"{profile} manifest compiled Layer 3 format mismatch")
            continue
        actual_input = manifest.get("authoritative_build_inputs")
        if actual_input != expected_input:
            errors.append(f"{profile} manifest authoritative input mismatch")
            continue
        manifests[profile] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "authoritative_build_inputs": actual_input,
        }
    if errors:
        return {}, errors
    return manifests, []


def _require_native_validator_report(
    report: dict[str, Any], *, subject: str, expected_fixture_schema: int
) -> None:
    if (
        report.get("status") != "pass"
        or report.get("errors") != []
        or report.get("fixture_schema_version") != expected_fixture_schema
        or report.get("evidence_scope") != "deterministic-fixtures"
    ):
        raise ValueError(
            f"{subject} native trajectory validation is not current and passing"
        )


def _native_dispatch_partition(
    step: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if step.get("action") != "dispatch":
        raise ValueError("native dispatch partition requires a dispatch step")
    if not isinstance(step.get("profile"), str) or not step["profile"]:
        raise ValueError("native dispatch has no profile")
    capsule_fields = [
        name
        for name in ("fixture_capsule", "utility_capsule")
        if name in step
    ]
    if not capsule_fields:
        raise ValueError("native dispatch requires capsule data")
    instructions = {
        name: copy.deepcopy(step[name]) for name in capsule_fields
    }
    if any(not isinstance(value, dict) for value in instructions.values()):
        raise ValueError("native dispatch capsules must be mappings")
    selector = {
        key: copy.deepcopy(value)
        for key, value in step.items()
        if key not in capsule_fields
    }
    return selector, instructions


def _subject_case_cost(
    case: dict[str, Any],
    transfer: dict[str, Any],
    metrics: dict[str, Any],
    route_obligations: dict[str, Any],
) -> dict[str, Any]:
    measurements = [
        item
        for item in case.get("measurements", [])
        if item.get("host") == "codex"
        and item.get("build_profile") == "recommended"
    ]
    if not measurements:
        raise ValueError(
            f"{case.get('id', '<missing>')}: a codex/recommended measurement is required"
        )
    components = {name: 0 for name in END_TO_END_COMPONENTS}
    component_kind = {
        "worker_profile": "always_loaded",
        "analysis_profile": "always_loaded",
        "task_profile": "always_loaded",
        "review_profile": "always_loaded",
        "utility_profile": "always_loaded",
        "dispatch_capsule": "dispatch_instructions",
        "primary_skill": "professional",
        "layer3": "layer3",
        "selector": "selector",
        "layer3_reference": "targeted_reference",
        "targeted_reference": "targeted_reference",
    }
    measured_total = 0
    for measurement in measurements:
        classified = 0
        for item in measurement.get("components", []):
            tokens = int(item.get("tokens", 0))
            bucket = component_kind.get(str(item.get("kind") or ""))
            if bucket is None:
                components["always_loaded"] += tokens
            else:
                components[bucket] += tokens
            classified += tokens
        dispatch_total = int(measurement.get("total_tokens", classified))
        if classified < dispatch_total:
            components["always_loaded"] += dispatch_total - classified
        measured_total += dispatch_total
    transfer_tokens = int(transfer.get("gross_tokens", 0))
    categories = transfer.get("categories", {})
    selector_tokens = int(categories.get("skill_reference", {}).get("gross_tokens", 0))
    components["selector"] += selector_tokens
    components["cross_agent_transfer"] = transfer_tokens - selector_tokens
    handoff_tokens = sum(
        int(categories.get(name, {}).get("gross_tokens", 0))
        for name in (
            "implementation_handoff",
            "review_handoff",
            "repair_context",
        )
    )
    handoff_count = int(
        metrics.get("handoff_count", len(transfer.get("boundary_rows", [])))
    )
    selector_load_count = int(metrics.get("selector_load_count", 0))
    reference_load_count = int(metrics.get("reference_load_count", 0))
    structural = {
        "selector_load_count": selector_load_count,
        "reference_partition_load_count": 0,
        "envelope_count": selector_load_count,
        "reference_load_count": reference_load_count,
        "reference_tokens": components["targeted_reference"],
        "handoff_count": handoff_count,
        "handoff_tokens": handoff_tokens,
        "same_assignment_duplicate_read_count": int(
            metrics.get("same_assignment_duplicate_read_count", 0)
        ),
        "end_to_end_context_occurrence_count": int(
            metrics.get(
                "end_to_end_context_occurrence_count",
                selector_load_count + reference_load_count + handoff_count,
            )
        ),
    }
    return {
        "id": str(case.get("id") or "<missing>"),
        "route_obligations": route_obligations,
        "component_tokens": components,
        "structural": structural,
        "total_task_tokens": measured_total + transfer_tokens,
    }


def _comparison_value(baseline: int, candidate: int) -> dict[str, int]:
    return {
        "baseline": baseline,
        "candidate": candidate,
        "delta": candidate - baseline,
    }


def _focus_semantic_obligation(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario": case.get("scenario"),
        "decision": case.get("decision"),
        "expected_valid": case.get("expected_valid"),
        "expected_error": case.get("expected_error"),
    }


def _canonical_focus_mapping(
    candidate_document: dict[str, Any],
    baseline_document: dict[str, Any],
    *,
    overrides: dict[str, str | list[str]] | None = None,
    protected_extensions: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    candidate_cases = {
        str(item.get("id")): item
        for item in candidate_document.get("task_focus_cases", [])
        if isinstance(item, dict) and item.get("id")
    }
    baseline_cases = {
        str(item.get("id")): item
        for item in baseline_document.get("task_focus_cases", [])
        if isinstance(item, dict) and item.get("id")
    }
    mapping = FOCUS_CURRENT_ONLY_MAP if overrides is None else overrides
    protections = (
        FOCUS_PROTECTED_SEMANTIC_EXTENSIONS
        if protected_extensions is None
        else protected_extensions
    )
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    protected_ids = set(FOCUS_PROTECTED_SEMANTIC_EXTENSIONS)
    if set(protections) != protected_ids:
        errors.append(
            "protected focus projection must exactly cover "
            + ", ".join(sorted(protected_ids))
        )
    for canonical_id, candidate in candidate_cases.items():
        native: str | list[str] | None = (
            canonical_id if canonical_id in baseline_cases else mapping.get(canonical_id)
        )
        if native is None:
            errors.append(f"{canonical_id}: unmapped current task-focus case")
            continue
        if isinstance(native, list):
            errors.append(f"{canonical_id}: ambiguous native mapping {native}")
            continue
        baseline = baseline_cases.get(native)
        if baseline is None:
            errors.append(f"{canonical_id}: missing-native-binding {native}")
            continue
        candidate_obligation = _focus_semantic_obligation(candidate)
        baseline_obligation = _focus_semantic_obligation(baseline)
        candidate_text = json.dumps(
            candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        baseline_text = json.dumps(
            baseline, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        candidate_native_sha256 = _sha256_text(candidate_text)
        baseline_native_sha256 = _sha256_text(baseline_text)
        candidate_semantic_sha256 = _sha256_text(
            json.dumps(
                candidate_obligation,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        baseline_semantic_sha256 = _sha256_text(
            json.dumps(
                baseline_obligation,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        protected_projection: dict[str, str] | None = None
        if candidate_obligation != baseline_obligation:
            if canonical_id not in protected_ids:
                errors.append(f"{canonical_id}: semantic-mismatch")
                continue
            protected_projection = protections.get(canonical_id)
            if protected_projection is None:
                errors.append(f"{canonical_id}: protected-projection-missing")
                continue
            required_protection_fields = {
                "baseline_id",
                "candidate_native_sha256",
                "baseline_native_sha256",
                "candidate_semantic_sha256",
                "baseline_semantic_sha256",
                "candidate_actor",
                "baseline_actor",
            }
            if set(protected_projection) != required_protection_fields:
                errors.append(f"{canonical_id}: protected-projection-schema")
                continue
            protection_checks = (
                (
                    "protected-baseline-binding",
                    protected_projection["baseline_id"] == native,
                ),
                (
                    "stale-candidate-native-hash",
                    protected_projection["candidate_native_sha256"]
                    == candidate_native_sha256,
                ),
                (
                    "stale-baseline-native-hash",
                    protected_projection["baseline_native_sha256"]
                    == baseline_native_sha256,
                ),
                (
                    "stale-candidate-semantic-hash",
                    protected_projection["candidate_semantic_sha256"]
                    == candidate_semantic_sha256,
                ),
                (
                    "stale-baseline-semantic-hash",
                    protected_projection["baseline_semantic_sha256"]
                    == baseline_semantic_sha256,
                ),
            )
            failed_checks = [
                code for code, passed in protection_checks if not passed
            ]
            if failed_checks:
                errors.extend(
                    f"{canonical_id}: {code}" for code in failed_checks
                )
                continue
            try:
                core = json.loads(
                    (ROOT / "src/control-model/core-contracts.json").read_text(
                        encoding="utf-8"
                    )
                )
                candidate_actor = _focus_case_actor_authority(candidate, core)[0]
                baseline_actor = _focus_case_actor_authority(baseline, core)[0]
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{canonical_id}: protected-actor-authority: {exc}")
                continue
            if (
                candidate_actor != baseline_actor
                or protected_projection["candidate_actor"] != candidate_actor
                or protected_projection["baseline_actor"] != baseline_actor
            ):
                errors.append(f"{canonical_id}: protected-actor-mismatch")
                continue
            state = "protected-semantic-extension"
        else:
            state = (
                "raw-route-equal"
                if canonical_id == native and candidate_text == baseline_text
                else "source-derived-semantic-equivalent"
            )
        row = {
            "canonical_id": canonical_id,
            "candidate_native_id": canonical_id,
            "baseline_native_id": native,
            "state": state,
            "semantic_obligation": candidate_obligation,
            "route_obligations": {
                "professional": [],
                "layer3": [],
                "domain": [],
                "review": [],
                "references": [],
                "not_applicable_basis": "task-focus case contains no Task dispatch",
            },
            "candidate_native_sha256": candidate_native_sha256,
            "baseline_native_sha256": baseline_native_sha256,
            "raw_physical_route_equal": state == "raw-route-equal",
        }
        if protected_projection is not None:
            row["protected_projection"] = dict(protected_projection)
        rows.append(row)
    if len(rows) != len(candidate_cases):
        errors.append(
            f"canonical focus coverage is incomplete: {len(rows)}/{len(candidate_cases)}"
        )
    digest = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return {
        "status": "pass" if not errors else "fail",
        "rows": rows,
        "mapping_digest": digest,
        "errors": errors,
    }


def _canonical_trajectory_mapping(
    candidate_document: dict[str, Any],
    baseline_document: dict[str, Any],
    *,
    candidate_root: Path,
    baseline_root: Path,
) -> dict[str, Any]:
    candidate_cases = {
        str(case.get("id") or ""): case
        for _group, case in _fixture_cases(candidate_document)
    }
    baseline_cases = {
        str(case.get("id") or ""): case
        for _group, case in _fixture_cases(baseline_document)
    }
    errors: list[str] = []
    if "" in candidate_cases or "" in baseline_cases:
        errors.append("native trajectory mapping contains a missing case id")
    if set(candidate_cases) != set(baseline_cases):
        errors.append("native trajectory case coverage differs")
    rows: list[dict[str, Any]] = []
    for case_id in sorted(set(candidate_cases) & set(baseline_cases)):
        candidate_route, candidate_raw = _route_obligations(
            candidate_cases[case_id], candidate_root
        )
        baseline_route, baseline_raw = _route_obligations(
            baseline_cases[case_id], baseline_root
        )
        if candidate_route != baseline_route:
            errors.append(f"{case_id}: native trajectory obligation-mismatch")
            continue
        candidate_text = _canonical_json_text(candidate_cases[case_id])
        baseline_text = _canonical_json_text(baseline_cases[case_id])
        raw_equal = candidate_raw == baseline_raw and candidate_text == baseline_text
        rows.append(
            {
                "canonical_id": case_id,
                "candidate_native_id": case_id,
                "baseline_native_id": case_id,
                "state": (
                    "raw-route-equal"
                    if raw_equal
                    else "source-derived-semantic-equivalent"
                ),
                "semantic_obligation": candidate_route,
                "candidate_native_sha256": _sha256_text(candidate_text),
                "baseline_native_sha256": _sha256_text(baseline_text),
                "raw_physical_route_equal": raw_equal,
                "raw_route_difference": {
                    "baseline": baseline_raw,
                    "candidate": candidate_raw,
                },
            }
        )
    if len(rows) != len(candidate_cases):
        errors.append(
            "canonical trajectory coverage is incomplete: "
            f"{len(rows)}/{len(candidate_cases)}"
        )
    digest = hashlib.sha256(
        _canonical_json_text(rows).encode("utf-8")
    ).hexdigest()
    return {
        "status": "pass" if not errors else "fail",
        "rows": rows,
        "mapping_digest": digest,
        "errors": errors,
    }


def _role_for_core_capability(core: dict[str, Any], capability_id: str) -> str:
    role_capabilities = core.get("profile_contract", {}).get(
        "role_capabilities", {}
    )
    matches = [
        role
        for role, contract in role_capabilities.items()
        if isinstance(contract, dict)
        and capability_id in contract.get("required_capability_ids", [])
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Core capability {capability_id!r} has ambiguous actor binding: {matches}"
        )
    return str(matches[0])


def _focus_case_actor_authority(
    native_case: dict[str, Any], core: dict[str, Any]
) -> tuple[str, str, Any]:
    scenario = native_case.get("scenario")
    expected_actor = FOCUS_SCENARIO_ACTORS.get(str(scenario))
    if expected_actor is None:
        raise ValueError(f"unknown task-focus consumer scenario {scenario!r}")
    implementation_capability = core.get("implementation_discipline_contract", {}).get(
        "profile_capability_id"
    )
    review_contract = core.get("review_discipline_contract", {})
    review_policy = review_contract.get("effective_level_policy", {})
    readiness = review_contract.get("review_input_readiness", {})
    authority_pointer: str
    authority_value: Any
    if scenario == "finding":
        authority_pointer = (
            "/review_discipline_contract/effective_level_policy/"
            "finding_merge_owner"
        )
        authority_value = review_policy.get("finding_merge_owner")
        actor = authority_value
    elif scenario == "review-level":
        authority_pointer = (
            "/review_discipline_contract/effective_level_policy/"
            "final_review_profile"
        )
        authority_value = review_policy.get("final_review_profile")
        actor = authority_value
    elif scenario in {"review-readiness", "capability-equivalence"}:
        authority_pointer = (
            "/review_discipline_contract/review_input_readiness/consumer"
        )
        authority_value = readiness.get("consumer")
        actor = (
            authority_value.removesuffix("-before-review-dispatch")
            if isinstance(authority_value, str)
            else None
        )
        if scenario == "capability-equivalence":
            capability_contract = review_contract.get(
                "generic_capability_contract"
            )
            if (
                not isinstance(capability_contract, dict)
                or not isinstance(capability_contract.get("fields"), list)
                or not capability_contract["fields"]
            ):
                raise ValueError(
                    "capability-equivalence lacks a closed Core capability contract"
                )
    elif scenario == "analysis-level":
        authority_pointer = (
            "/execution_level_contract/lifecycle/first_computation_point"
        )
        authority_value = core.get("execution_level_contract", {}).get(
            "lifecycle", {}
        ).get("first_computation_point")
        if authority_value != "first-executable-slice-or-direct-executable-task":
            raise ValueError("analysis-level Core computation authority is unknown")
        actor = _role_for_core_capability(core, "main-prompt-single-load")
        inputs = native_case.get("inputs", {})
        decision = native_case.get("decision", {})
        expected_points = {
            "analyzed": "first-executable-slice",
            "direct": "direct-executable-task",
        }
        route_path = inputs.get("route_path") if isinstance(inputs, dict) else None
        if (
            route_path not in expected_points
            or not isinstance(decision, dict)
            or decision.get("level_computation_point")
            != expected_points[route_path]
        ):
            raise ValueError(
                "analysis-level route path disagrees with Core computation point"
            )
    elif scenario == "engineering-choice":
        concepts = core.get("prompt_contract", {}).get("concepts", [])
        matches = [
            concept
            for concept in concepts
            if isinstance(concept, dict)
            and concept.get("id") == "evidence-resolution-authority"
        ] if isinstance(concepts, list) else []
        if len(matches) != 1:
            raise ValueError(
                "engineering-choice lacks unique Core evidence-resolution authority"
            )
        authority_pointer = (
            "/prompt_contract/concepts/evidence-resolution-authority"
        )
        authority_value = matches[0]
        required_terms = authority_value.get("required_terms")
        if (
            authority_value.get("section") != "Choose Exactly One Path"
            or not isinstance(required_terms, list)
            or not {
                "user choice -> one Main question",
                "otherwise bounded Direct discovery",
            } <= set(required_terms)
        ):
            raise ValueError(
                "engineering-choice Core evidence-resolution authority is incomplete"
            )
        actor = _role_for_core_capability(core, "main-prompt-single-load")
    else:
        authority_pointer = (
            "/implementation_discipline_contract/profile_capability_id"
        )
        authority_value = implementation_capability
        if not isinstance(authority_value, str) or not authority_value:
            raise ValueError("task-focus implementation consumer authority is missing")
        actor = _role_for_core_capability(core, authority_value)
        if scenario == "same-pattern":
            same_pattern = core.get("task_contract", {}).get(
                "same_pattern_scan", {}
            )
            if same_pattern.get("required") is not True or not same_pattern.get(
                "routes"
            ):
                raise ValueError("same-pattern Core authority is incomplete")
        elif scenario == "repair":
            if (
                core.get("task_contract", {})
                .get("repair_routing", {})
                .get("current_task_blocking")
                != "task-agent-repair"
            ):
                raise ValueError("repair Core actor authority disagrees")
        elif scenario == "cost":
            if (
                review_policy.get("ordinary_l1_l3_agent_count_increase") is not False
                or review_policy.get("ordinary_l1_l3_review_round_increase") is not False
            ):
                raise ValueError("ordinary-cost Core conservation authority disagrees")
    if actor != expected_actor:
        raise ValueError(
            f"{scenario} Core actor disagreement: expected {expected_actor}, got {actor}"
        )
    return expected_actor, authority_pointer, authority_value


def _focus_actor_profile_binding(
    native_case: dict[str, Any], subject_root: Path
) -> dict[str, Any]:
    core_path = subject_root / "src/control-model/core-contracts.json"
    profile_authority_path = subject_root / "src/agent-profiles/role-agents.json"
    try:
        core_raw = core_path.read_bytes()
        core = json.loads(core_raw)
        profile_authority_raw = profile_authority_path.read_bytes()
        profile_authority = json.loads(profile_authority_raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"task-focus subject authority is unavailable: {exc}") from exc
    if not isinstance(core, dict) or not isinstance(profile_authority, dict):
        raise ValueError("task-focus subject authority must be an object")
    actor, authority_pointer, authority_value = _focus_case_actor_authority(
        native_case, core
    )
    profiles = profile_authority.get("profiles")
    matches = [
        item
        for item in profiles if isinstance(item, dict) and item.get("name") == actor
    ] if isinstance(profiles, list) else []
    if len(matches) != 1:
        raise ValueError(
            f"task-focus actor {actor!r} has no unique source Profile binding"
        )
    host_paths = {
        "codex": subject_root
        / "dist/codex/project/.codex/agents"
        / f"{actor}.toml",
        "claude": subject_root
        / "dist/claude/project/.claude/agents"
        / f"{actor}.md",
        "copilot": subject_root
        / "dist/copilot/project/.github/agents"
        / f"{actor}.agent.md",
    }
    generated_profiles: list[dict[str, Any]] = []
    for host in FOCUS_PROFILE_HOSTS:
        generated_path = host_paths[host]
        if not generated_path.is_file() or _uses_symlink(generated_path, subject_root):
            raise ValueError(
                f"task-focus actor {actor!r} generated {host} Profile is missing "
                "or symlinked"
            )
        try:
            generated_raw = generated_path.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"task-focus actor {actor!r} generated {host} Profile is missing"
            ) from exc
        generated_profiles.append(
            {
                "host": host,
                "path": generated_path.relative_to(subject_root).as_posix(),
                "sha256": hashlib.sha256(generated_raw).hexdigest(),
                "tokens": count_o200k_base_tokens(
                    generated_raw.decode("utf-8")
                ),
                "content_scope": "complete-subject-native-profile",
            }
        )
    manifest_bindings: dict[str, dict[str, dict[str, str]]] = {}
    for build_profile in BUILD_PROFILES:
        manifest_path = subject_root / (
            "dist/universal/skills/"
            f"{build_profile}/.changeforge-build-manifest.json"
        )
        try:
            manifest_raw = manifest_path.read_bytes()
            manifest = json.loads(manifest_raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"task-focus {build_profile} manifest is unavailable"
            ) from exc
        if manifest.get("profile") != build_profile:
            raise ValueError(
                f"task-focus {build_profile} manifest identity is stale"
            )
        host_bindings: dict[str, dict[str, str]] = {}
        for generated in generated_profiles:
            host = generated["host"]
            expected_sha256 = (
                manifest.get("agent_profile_sha256", {})
                .get(host, {})
                .get(actor)
                if isinstance(manifest, dict)
                else None
            )
            if expected_sha256 != generated["sha256"]:
                raise ValueError(
                    f"task-focus {build_profile} manifest has stale "
                    f"{host}/{actor} Profile binding"
                )
            host_bindings[str(host)] = {
                "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
                "profile_sha256": str(expected_sha256),
            }
        manifest_bindings[build_profile] = host_bindings
    return {
        "actor": actor,
        "profile": actor,
        "scenario": native_case["scenario"],
        "core_authority": {
            "path": core_path.relative_to(subject_root).as_posix(),
            "sha256": hashlib.sha256(core_raw).hexdigest(),
            "pointer": authority_pointer,
            "value": authority_value,
        },
        "profile_authority": {
            "path": profile_authority_path.relative_to(subject_root).as_posix(),
            "sha256": hashlib.sha256(profile_authority_raw).hexdigest(),
            "source_profile_sha256": _sha256_text(
                _canonical_json_text(matches[0])
            ),
        },
        "host_order": list(FOCUS_PROFILE_HOSTS),
        "generated_profiles": generated_profiles,
        "manifest_bindings": manifest_bindings,
    }


def _focus_case_cost(
    row: dict[str, Any],
    native_case: dict[str, Any],
    subject_root: Path,
    *,
    subject: str,
    host: str,
) -> dict[str, Any]:
    if host not in FOCUS_PROFILE_HOSTS:
        raise ValueError(f"task-focus host binding is invalid: {host!r}")
    binding = _focus_actor_profile_binding(native_case, subject_root)
    binding = {**binding, "measured_host": host}
    native_bytes_case = copy.deepcopy(native_case)
    if native_bytes_case.get("native_case_id"):
        native_bytes_case["id"] = native_bytes_case.pop("native_case_id")
    case_text = json.dumps(
        native_bytes_case, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    components = {name: 0 for name in END_TO_END_COMPONENTS}
    generated_profile = next(
        item for item in binding["generated_profiles"] if item["host"] == host
    )
    components["always_loaded"] = generated_profile["tokens"]
    logical_case_id = str(row["canonical_id"])
    return {
        "id": f"{logical_case_id}::{host}",
        "logical_case_id": logical_case_id,
        "host": host,
        "native_case_id": str(row[f"{subject}_native_id"]),
        "mapping_state": row["state"],
        "semantic_obligation": row["semantic_obligation"],
        "route_obligations": row["route_obligations"],
        "raw_route_obligations": row["route_obligations"],
        "native_reference_bindings": [],
        "actor_profile_binding": binding,
        "component_tokens": components,
        "structural": {
            "selector_load_count": 0,
            "reference_partition_load_count": 0,
            "envelope_count": 0,
            "reference_load_count": 0,
            "reference_tokens": 0,
            "handoff_count": 0,
            "handoff_tokens": 0,
            "same_assignment_duplicate_read_count": 0,
            "end_to_end_context_occurrence_count": 1,
        },
        "total_task_tokens": components["always_loaded"],
        "native_sources": {
            "fixture_case": {
                "path": f"fixture:{row[f'{subject}_native_id']}",
                "sha256": row[f"{subject}_native_sha256"],
                "tokens": count_o200k_base_tokens(case_text),
                "content_scope": "oracle-only-not-loaded",
            },
            "core": {
                **binding["core_authority"],
                "content_scope": "authority-only-not-loaded",
            },
            "profiles": [generated_profile],
        },
    }


def _native_reference_differences(
    case_id: str,
    baseline: object,
    candidate: object,
    errors: list[str],
) -> list[dict[str, Any]]:
    baseline_rows = baseline if isinstance(baseline, list) else []
    candidate_rows = candidate if isinstance(candidate, list) else []
    required = {
        "semantic_obligation",
        "physical_path",
        "reference_type",
        "required_outputs",
        "registry_sha256",
        "source_sha256",
        "tokens",
        "content_scope",
    }
    for label, rows in (("baseline", baseline_rows), ("candidate", candidate_rows)):
        for row in rows:
            if not isinstance(row, dict) or not required <= set(row):
                errors.append(f"{case_id}: hidden physical {label} Reference difference")
            elif row.get("content_scope") != "complete-native-bytes":
                errors.append(f"{case_id}: extracted span cannot replace native bytes")

    def by_semantic(rows: list[object]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            if isinstance(row, dict) and required <= set(row):
                grouped.setdefault(str(row["semantic_obligation"]), []).append(row)
        return grouped

    baseline_by_semantic = by_semantic(baseline_rows)
    candidate_by_semantic = by_semantic(candidate_rows)
    if set(baseline_by_semantic) != set(candidate_by_semantic):
        errors.append(f"{case_id}: native Reference semantic obligations differ")
    result: list[dict[str, Any]] = []
    for semantic in sorted(set(baseline_by_semantic) & set(candidate_by_semantic)):
        before_rows = baseline_by_semantic[semantic]
        after_rows = candidate_by_semantic[semantic]
        if len(before_rows) != len(after_rows):
            errors.append(
                f"{case_id}: native Reference occurrence cardinality differs for "
                f"{semantic}: baseline={len(before_rows)} candidate={len(after_rows)}"
            )
        for occurrence, (before, after) in enumerate(zip(before_rows, after_rows)):
            result.append(
                {
                    "semantic_obligation": semantic,
                    "occurrence": occurrence,
                    "state": (
                        "raw-route-equal"
                        if before == after
                        else "source-derived-semantic-equivalent"
                    ),
                    "baseline": before,
                    "candidate": after,
                    "raw_physical_route_equal": before == after,
                }
            )
    return result


def _actor_profile_differences(
    case_id: str,
    host: str,
    baseline: object,
    candidate: object,
    before_components: dict[str, Any],
    after_components: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    if baseline is None and candidate is None:
        return []
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        errors.append(f"{case_id}: actor/Profile binding differs between subjects")
        return []
    required_binding_fields = {
        "actor",
        "profile",
        "scenario",
        "core_authority",
        "profile_authority",
        "host_order",
        "generated_profiles",
        "manifest_bindings",
        "measured_host",
    }
    for label, binding in (("baseline", baseline), ("candidate", candidate)):
        if not required_binding_fields <= set(binding):
            errors.append(f"{case_id}: {label} actor/Profile authority is incomplete")
        manifest_bindings = binding.get("manifest_bindings")
        if not isinstance(manifest_bindings, dict) or list(
            manifest_bindings
        ) != list(BUILD_PROFILES):
            errors.append(f"{case_id}: {label} actor/Profile manifests are incomplete")
        elif any(
            list(host_bindings) != list(FOCUS_PROFILE_HOSTS)
            for host_bindings in manifest_bindings.values()
            if isinstance(host_bindings, dict)
        ) or any(
            not isinstance(host_bindings, dict)
            for host_bindings in manifest_bindings.values()
        ):
            errors.append(
                f"{case_id}: {label} actor/Profile manifest host coverage is incomplete"
            )
    for field in ("actor", "profile", "scenario", "host_order", "measured_host"):
        if baseline.get(field) != candidate.get(field):
            errors.append(
                f"{case_id}: actor/Profile {field} differs between subjects"
            )
    expected_hosts = list(FOCUS_PROFILE_HOSTS)
    result: list[dict[str, Any]] = []
    selected_tokens: list[int] = []
    for label, binding in (("baseline", baseline), ("candidate", candidate)):
        if binding.get("measured_host") != host:
            errors.append(f"{case_id}: {label} actor/Profile host binding is invalid")
        if binding.get("host_order") != expected_hosts:
            errors.append(f"{case_id}: {label} actor/Profile host order is invalid")
        rows = binding.get("generated_profiles")
        if not isinstance(rows, list) or [
            item.get("host") if isinstance(item, dict) else None for item in rows
        ] != expected_hosts:
            errors.append(
                f"{case_id}: {label} actor/Profile host coverage is incomplete"
            )
            selected_tokens.append(-1)
            continue
        valid_selected = -1
        for item in rows:
            if (
                set(item)
                != {"host", "path", "sha256", "tokens", "content_scope"}
                or type(item.get("tokens")) is not int
                or item["tokens"] < 0
                or item.get("content_scope")
                != "complete-subject-native-profile"
            ):
                errors.append(
                    f"{case_id}: {label} actor/Profile host row is malformed"
                )
                valid_selected = -1
                break
            if item["host"] == host:
                valid_selected = item["tokens"]
        selected_tokens.append(valid_selected)
    if len(selected_tokens) == 2:
        if selected_tokens[0] != before_components.get("always_loaded"):
            errors.append(
                f"{case_id}: baseline actor/Profile total is not fully accounted"
            )
        if selected_tokens[1] != after_components.get("always_loaded"):
            errors.append(
                f"{case_id}: candidate actor/Profile total is not fully accounted"
            )
    baseline_rows = baseline.get("generated_profiles", [])
    candidate_rows = candidate.get("generated_profiles", [])
    if (
        isinstance(baseline_rows, list)
        and isinstance(candidate_rows, list)
        and len(baseline_rows) == len(candidate_rows) == len(expected_hosts)
    ):
        for row_host, before, after in zip(
            expected_hosts, baseline_rows, candidate_rows
        ):
            if row_host != host:
                continue
            if not isinstance(before, dict) or not isinstance(after, dict):
                continue
            result.append(
                {
                    "host": row_host,
                    "baseline_path": before.get("path"),
                    "candidate_path": after.get("path"),
                    "tokens": _comparison_value(
                        int(before.get("tokens", 0)),
                        int(after.get("tokens", 0)),
                    ),
                }
            )
    return result


def _host_complete_case_matrix(
    label: str,
    cases: object,
    identity: object,
    errors: list[str],
) -> dict[str, Any]:
    if not isinstance(cases, list):
        errors.append(f"{label} measured subject cases are not a list")
        return {"logical_case_count": 0, "host_pair_count": 0}
    grouped: dict[str, list[str]] = {}
    for case in cases:
        if not isinstance(case, dict):
            errors.append(f"{label} measured subject contains a non-object case")
            continue
        logical_case_id = case.get("logical_case_id")
        host = case.get("host")
        if not isinstance(logical_case_id, str) or not logical_case_id:
            errors.append(f"{label} measured subject case lacks logical host binding")
            continue
        if host not in FOCUS_PROFILE_HOSTS:
            errors.append(
                f"{logical_case_id}: {label} measured subject host binding is invalid"
            )
            continue
        if case.get("id") != f"{logical_case_id}::{host}":
            errors.append(
                f"{logical_case_id}: {label} measured subject cross-host id binding"
            )
        grouped.setdefault(logical_case_id, []).append(str(host))
        native_sources = case.get("native_sources")
        source_rows = (
            native_sources.get("components", [])
            if isinstance(native_sources, dict)
            else []
        )
        if not isinstance(source_rows, list):
            errors.append(f"{case['id']}: {label} native component rows are invalid")
            continue
        for source in source_rows:
            if not isinstance(source, dict):
                errors.append(f"{case['id']}: {label} native component row is invalid")
                continue
            if source.get("host") != host:
                errors.append(f"{case['id']}: {label} cross-host component binding")
            if (
                source.get("kind") == "native-selector-envelope"
                and source.get("bucket") != "cross_agent_transfer"
            ):
                errors.append(
                    f"{case['id']}: {label} selector envelope component overlap"
                )
        if source_rows:
            component_tokens = case.get("component_tokens")
            structural = case.get("structural")
            if not isinstance(component_tokens, dict) or not isinstance(structural, dict):
                errors.append(f"{case['id']}: {label} native row accounting is incomplete")
            else:
                source_totals = {name: 0 for name in END_TO_END_COMPONENTS}
                valid_sources = True
                for source in source_rows:
                    if not isinstance(source, dict):
                        valid_sources = False
                        continue
                    bucket = source.get("bucket")
                    tokens = source.get("tokens")
                    load_count = source.get("load_count")
                    if (
                        bucket not in END_TO_END_COMPONENTS
                        or type(tokens) is not int
                        or tokens < 0
                        or type(load_count) is not int
                        or load_count < 1
                    ):
                        valid_sources = False
                        continue
                    source_totals[str(bucket)] += tokens * load_count
                handoffs = native_sources.get("handoffs", [])
                if not isinstance(handoffs, list):
                    valid_sources = False
                    handoffs = []
                for handoff in handoffs:
                    if (
                        not isinstance(handoff, dict)
                        or handoff.get("host") != host
                        or type(handoff.get("tokens")) is not int
                        or handoff["tokens"] < 0
                    ):
                        valid_sources = False
                        continue
                    source_totals["cross_agent_transfer"] += handoff["tokens"]
                if not valid_sources or any(
                    component_tokens.get(bucket) != total
                    for bucket, total in source_totals.items()
                ):
                    errors.append(
                        f"{case['id']}: {label} native component rows do not reconcile"
                    )
                expected_counters = {
                    "selector_load_count": sum(
                        int(source.get("load_count", 0))
                        for source in source_rows
                        if isinstance(source, dict) and source.get("bucket") == "selector"
                    ),
                    "reference_partition_load_count": sum(
                        int(source.get("load_count", 0))
                        for source in source_rows
                        if isinstance(source, dict)
                        and source.get("bucket") == "reference_partition"
                    ),
                    "envelope_count": sum(
                        source.get("kind") == "native-selector-envelope"
                        for source in source_rows
                        if isinstance(source, dict)
                    ),
                    "reference_load_count": sum(
                        source.get("kind")
                        in {"professional-reference", "layer3-reference"}
                        for source in source_rows
                        if isinstance(source, dict)
                    ),
                    "reference_tokens": source_totals["targeted_reference"],
                    "handoff_count": len(handoffs)
                    + sum(
                        source.get("kind") == "native-selector-envelope"
                        for source in source_rows
                        if isinstance(source, dict)
                    ),
                    "handoff_tokens": sum(
                        int(item.get("tokens", 0))
                        for item in handoffs
                        if isinstance(item, dict)
                    ),
                }
                if any(
                    structural.get(field) != expected
                    for field, expected in expected_counters.items()
                ):
                    errors.append(
                        f"{case['id']}: {label} native structural rows do not reconcile"
                    )
        actor_binding = case.get("actor_profile_binding")
        if isinstance(actor_binding, dict) and actor_binding.get("measured_host") != host:
            errors.append(f"{case['id']}: {label} actor/Profile cross-host binding")
    for logical_case_id, hosts in grouped.items():
        if hosts != list(FOCUS_PROFILE_HOSTS):
            errors.append(
                f"{logical_case_id}: {label} host matrix is incomplete or unordered"
            )
    logical_case_count = len(grouped)
    host_pair_count = len(cases)
    if not isinstance(identity, dict):
        errors.append(f"{label} measured subject identity is invalid")
    else:
        expected_identity = {
            "logical_case_count": logical_case_count,
            "host_pair_count": host_pair_count,
            "host_order": list(FOCUS_PROFILE_HOSTS),
        }
        for field, expected in expected_identity.items():
            if identity.get(field) != expected:
                errors.append(f"{label} measured subject {field} identity mismatch")
    return {
        "logical_case_count": logical_case_count,
        "host_pair_count": host_pair_count,
        "host_order": list(FOCUS_PROFILE_HOSTS),
    }


def _compare_end_to_end_subjects(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    baseline_identity = baseline.get("identity", {})
    candidate_identity = candidate.get("identity", {})
    for label, identity in (
        ("baseline", baseline_identity),
        ("candidate", candidate_identity),
    ):
        if identity.get("measurement_source") != "isolated-built-subject":
            errors.append(f"{label} is not an isolated measured subject")
        for field in (
            "evaluator_sha256",
            "lightweight_evaluator_sha256",
            "canonical_corpus_digest",
            "tokenizer",
        ):
            if not identity.get(field):
                errors.append(f"{label} measured subject lacks {field}")
        if not identity.get("native_fixture_sha256"):
            errors.append(f"{label} measured subject lacks native fixture identity")
        if not isinstance(identity.get("native_schema"), dict):
            errors.append(f"{label} measured subject lacks native schema identity")
        if not identity.get("native_validator_sha256"):
            errors.append(f"{label} measured subject lacks native validator identity")
        authoritative = identity.get("authoritative_build_inputs")
        manifests = identity.get("manifests")
        if not isinstance(authoritative, dict) or not isinstance(manifests, dict):
            errors.append(f"{label} measured subject lacks manifest identity")
            continue
        if set(manifests) != set(BUILD_PROFILES):
            errors.append(f"{label} measured subject lacks all build manifests")
        for profile, manifest in manifests.items():
            if manifest.get("authoritative_build_inputs") != authoritative:
                errors.append(
                    f"{label} {profile} manifest authoritative input mismatch"
                )
    for field in (
        "evaluator_sha256",
        "lightweight_evaluator_sha256",
        "canonical_corpus_digest",
        "tokenizer",
    ):
        if baseline_identity.get(field) != candidate_identity.get(field):
            errors.append(f"subjects do not use the same {field}")

    baseline_matrix = _host_complete_case_matrix(
        "baseline", baseline.get("cases"), baseline_identity, errors
    )
    candidate_matrix = _host_complete_case_matrix(
        "candidate", candidate.get("cases"), candidate_identity, errors
    )
    if baseline_matrix != candidate_matrix:
        errors.append("measured subject host matrices differ")

    baseline_cases = {
        str(item.get("id")): item for item in baseline.get("cases", [])
    }
    candidate_cases = {
        str(item.get("id")): item for item in candidate.get("cases", [])
    }
    if set(baseline_cases) != set(candidate_cases):
        errors.append("measured subject case coverage differs")
    rows: list[dict[str, Any]] = []
    baseline_total = 0
    candidate_total = 0
    baseline_by_host = {host: 0 for host in FOCUS_PROFILE_HOSTS}
    candidate_by_host = {host: 0 for host in FOCUS_PROFILE_HOSTS}
    component_baseline = {name: 0 for name in END_TO_END_COMPONENTS}
    component_candidate = {name: 0 for name in END_TO_END_COMPONENTS}
    component_by_host = {
        host: {
            "baseline": {name: 0 for name in END_TO_END_COMPONENTS},
            "candidate": {name: 0 for name in END_TO_END_COMPONENTS},
        }
        for host in FOCUS_PROFILE_HOSTS
    }
    ordinary_route_regressions: list[dict[str, Any]] = []
    for case_id in sorted(set(baseline_cases) & set(candidate_cases)):
        before = baseline_cases[case_id]
        after = candidate_cases[case_id]
        host = before.get("host")
        if host != after.get("host") or host not in FOCUS_PROFILE_HOSTS:
            errors.append(f"{case_id}: subject host bindings differ")
        if before.get("route_obligations") != after.get("route_obligations"):
            errors.append(f"{case_id}: route obligations differ between subjects")
        before_mapping_state = before.get("mapping_state")
        after_mapping_state = after.get("mapping_state")
        if before_mapping_state != after_mapping_state:
            errors.append(f"{case_id}: mapping states differ between subjects")
        before_structural = before.get("structural", {})
        after_structural = after.get("structural", {})
        for field in END_TO_END_COVERAGE_COUNTERS:
            if before_structural.get(field) != after_structural.get(field):
                errors.append(f"{case_id}: coverage counter {field} differs")
        before_components = before.get("component_tokens", {})
        after_components = after.get("component_tokens", {})
        complete = True
        for label, components, structural, case in (
            ("baseline", before_components, before_structural, before),
            ("candidate", after_components, after_structural, after),
        ):
            if not isinstance(components, dict) or set(components) != set(
                END_TO_END_COMPONENTS
            ):
                errors.append(
                    f"{case_id}: {label} lacks the complete component breakdown"
                )
                complete = False
            elif any(type(components[name]) is not int or components[name] < 0 for name in END_TO_END_COMPONENTS):
                errors.append(
                    f"{case_id}: {label} component breakdown contains invalid tokens"
                )
                complete = False
            if not isinstance(structural, dict) or set(structural) != set(
                END_TO_END_STRUCTURAL_COUNTERS
            ):
                errors.append(
                    f"{case_id}: {label} lacks the complete structural breakdown"
                )
                complete = False
            elif any(type(structural[name]) is not int or structural[name] < 0 for name in END_TO_END_STRUCTURAL_COUNTERS):
                errors.append(
                    f"{case_id}: {label} structural breakdown contains invalid values"
                )
                complete = False
            declared_total = case.get("total_task_tokens")
            if type(declared_total) is not int or declared_total < 0:
                errors.append(f"{case_id}: {label} total task tokens are invalid")
                complete = False
            elif isinstance(components, dict) and set(components) == set(
                END_TO_END_COMPONENTS
            ) and declared_total != sum(components.values()):
                errors.append(
                    f"{case_id}: {label} total task tokens differ from component sum"
                )
                complete = False
            if (
                isinstance(components, dict)
                and isinstance(structural, dict)
                and components.get("targeted_reference")
                != structural.get("reference_tokens")
            ):
                errors.append(
                    f"{case_id}: {label} Reference token accounting differs"
                )
                complete = False
        if not complete:
            continue
        component_comparison = {
            name: _comparison_value(
                before_components[name],
                after_components[name],
            )
            for name in END_TO_END_COMPONENTS
        }
        structural_comparison = {
            name: _comparison_value(
                before_structural[name],
                after_structural[name],
            )
            for name in END_TO_END_STRUCTURAL_COUNTERS
        }
        native_reference_differences = _native_reference_differences(
            case_id,
            before.get("native_reference_bindings", []),
            after.get("native_reference_bindings", []),
            errors,
        )
        actor_profile_differences = _actor_profile_differences(
            case_id,
            str(host),
            before.get("actor_profile_binding"),
            after.get("actor_profile_binding"),
            before_components,
            after_components,
            errors,
        )
        authority_bundles: dict[str, list[dict[str, Any]]] = {}
        selection_asset_rows: dict[str, list[dict[str, Any]]] = {}
        selection_asset_reconciliation: dict[str, int] = {}
        for label, case, structural in (
            ("baseline", before, before_structural),
            ("candidate", after, after_structural),
        ):
            native_sources = case.get("native_sources")
            bundles = (
                native_sources.get("selection_authority_bundles")
                if isinstance(native_sources, dict)
                else None
            )
            if structural.get("selector_load_count", 0) > 0 and (
                not isinstance(bundles, list) or not bundles
            ):
                errors.append(
                    f"{case_id}: {label} loses measured selection authority bundles"
                )
                bundles = []
            if isinstance(bundles, list) and any(
                not isinstance(bundle, dict) or bundle.get("host") != host
                for bundle in bundles
            ):
                errors.append(
                    f"{case_id}: {label} selection authority cross-host binding"
                )
            authority_bundles[label] = copy.deepcopy(
                bundles if isinstance(bundles, list) else []
            )
            component_rows = (
                native_sources.get("components", [])
                if isinstance(native_sources, dict)
                else []
            )
            if not isinstance(component_rows, list):
                errors.append(f"{case_id}: {label} selection asset rows are invalid")
                component_rows = []
            for source in component_rows:
                if not isinstance(source, dict):
                    continue
                if source.get("host") != host:
                    errors.append(f"{case_id}: {label} cross-host component binding")
                if (
                    source.get("kind") == "native-selector-envelope"
                    and source.get("bucket") != "cross_agent_transfer"
                ):
                    errors.append(
                        f"{case_id}: {label} selector envelope component overlap"
                    )
            retained = [
                copy.deepcopy(row)
                for row in component_rows
                if isinstance(row, dict)
                and row.get("kind")
                in {
                    "main-profile",
                    "control-owner",
                    "global-professional-router",
                    "professional-selector",
                    "professional-selector-envelope",
                    "professional-selector-decision",
                    "professional-selector-complete",
                    "reference-records-partition",
                }
            ]
            seen_selection_assets: set[tuple[str, str, str, str]] = set()
            for row in retained:
                key = (
                    str(row.get("assignment_key") or ""),
                    str(row.get("host") or ""),
                    str(row.get("physical_path") or ""),
                    str(row.get("sha256") or ""),
                )
                if not all(key) or key in seen_selection_assets:
                    errors.append(
                        f"{case_id}: {label} selection asset rows contain an "
                        "unbound or duplicate assignment occurrence"
                    )
                seen_selection_assets.add(key)
            actual_selection_tokens = {
                bucket: sum(
                    int(row.get("tokens", 0)) * int(row.get("load_count", 0))
                    for row in retained
                    if row.get("bucket") == bucket
                )
                for bucket in ("always_loaded", "selector", "reference_partition")
            }
            expected_selection_tokens = (
                native_sources.get("selection_asset_component_tokens", {})
                if isinstance(native_sources, dict)
                else {}
            )
            if not isinstance(expected_selection_tokens, dict):
                expected_selection_tokens = {}
            if retained and set(expected_selection_tokens) != {
                "always_loaded",
                "selector",
                "reference_partition",
            }:
                errors.append(
                    f"{case_id}: {label} selection asset rows lack component binding"
                )
            reconciliation = sum(
                actual_selection_tokens[bucket]
                - int(expected_selection_tokens.get(bucket, 0))
                for bucket in actual_selection_tokens
            )
            if any(
                actual_selection_tokens[bucket]
                != int(expected_selection_tokens.get(bucket, 0))
                for bucket in actual_selection_tokens
            ):
                errors.append(
                    f"{case_id}: {label} selection asset rows do not reconcile"
                )
            selection_asset_rows[label] = retained
            selection_asset_reconciliation[label] = reconciliation
        before_total = before["total_task_tokens"]
        after_total = after["total_task_tokens"]
        raw_route_equal = (
            before.get("raw_route_obligations")
            == after.get("raw_route_obligations")
        )
        route_obligations = before.get("route_obligations")
        ordinary_raw_route_equal = (
            before_mapping_state == "raw-route-equal"
            and after_mapping_state == "raw-route-equal"
            and raw_route_equal
            and isinstance(route_obligations, dict)
            and "not_applicable_basis" not in route_obligations
        )
        if ordinary_raw_route_equal and after_total > before_total:
            regression = {
                "id": case_id,
                "logical_case_id": before.get("logical_case_id"),
                "host": host,
                "classification": "ordinary-raw-route-equal",
                "source_authority": "canonical-trajectory-mapping/raw-route-equal",
                "total_task_tokens": _comparison_value(before_total, after_total),
            }
            ordinary_route_regressions.append(regression)
        baseline_total += before_total
        candidate_total += after_total
        if host in FOCUS_PROFILE_HOSTS:
            baseline_by_host[str(host)] += before_total
            candidate_by_host[str(host)] += after_total
            for name in END_TO_END_COMPONENTS:
                component_baseline[name] += before_components[name]
                component_candidate[name] += after_components[name]
                component_by_host[str(host)]["baseline"][name] += before_components[name]
                component_by_host[str(host)]["candidate"][name] += after_components[name]
        rows.append(
            {
                "id": case_id,
                "logical_case_id": before.get("logical_case_id"),
                "host": host,
                "mapping_state": before_mapping_state,
                "cost_classification": (
                    "ordinary-raw-route-equal"
                    if ordinary_raw_route_equal
                    else "source-classified-non-ordinary"
                ),
                "route_obligations": before.get("route_obligations", {}),
                "raw_route_difference": {
                    "baseline": before.get("raw_route_obligations"),
                    "candidate": after.get("raw_route_obligations"),
                    "equal": before.get("raw_route_obligations")
                    == after.get("raw_route_obligations"),
                },
                "component_tokens": component_comparison,
                "structural": structural_comparison,
                "native_reference_differences": native_reference_differences,
                "actor_profile_differences": actor_profile_differences,
                "selection_authority_bundles": authority_bundles,
                "selection_asset_rows": selection_asset_rows,
                "selection_asset_reconciliation": selection_asset_reconciliation,
                "total_task_tokens": _comparison_value(before_total, after_total),
            }
        )
    comparison_blocked = bool(errors)
    reduction_ratio = None
    if not comparison_blocked:
        reduction_ratio = (
            round((baseline_total - candidate_total) / baseline_total, 6)
            if baseline_total
            else 0.0
        )
        if baseline_total <= 0:
            errors.append("baseline measured subject total must be positive")
    component_aggregate = {
        name: _comparison_value(component_baseline[name], component_candidate[name])
        for name in END_TO_END_COMPONENTS
    }
    host_aggregates = {
        host: {
            "total_task_tokens": _comparison_value(
                baseline_by_host[host], candidate_by_host[host]
            ),
            "component_tokens": {
                name: _comparison_value(
                    component_by_host[host]["baseline"][name],
                    component_by_host[host]["candidate"][name],
                )
                for name in END_TO_END_COMPONENTS
            },
        }
        for host in FOCUS_PROFILE_HOSTS
    }
    host_cost_increases = [
        host
        for host in FOCUS_PROFILE_HOSTS
        if candidate_by_host[host] > baseline_by_host[host]
    ]
    if comparison_blocked or baseline_total <= 0:
        cost_status = "not-comparable"
    elif candidate_total > baseline_total:
        cost_status = "candidate-higher-cost"
    elif ordinary_route_regressions or host_cost_increases:
        cost_status = "mixed-cost-deltas"
    elif candidate_total < baseline_total:
        cost_status = "candidate-lower-cost"
    elif candidate_total == baseline_total:
        cost_status = "candidate-equal-cost"
    else:
        cost_status = "candidate-higher-cost"
    return {
        "status": "pass" if not errors else "fail",
        "comparison_rule": "cost-observation-after-quality-gate",
        "ordinary_route_comparison_rule": (
            "source-classified-raw-route-equal-cost-observation"
        ),
        "ordinary_route_regressions": ordinary_route_regressions,
        "cost_observation": {
            "status": cost_status,
            "candidate_total_not_greater_is_correctness_acceptance": False,
            "host_cost_increases": host_cost_increases,
        },
        "subjects": {
            "baseline": baseline_identity,
            "candidate": candidate_identity,
        },
        "cases": rows,
        "host_matrix": {
            **baseline_matrix,
            "component_tokens": component_aggregate,
            "hosts": host_aggregates,
            "reconciliation": {
                "baseline": baseline_total
                - sum(item["baseline"] for item in component_aggregate.values()),
                "candidate": candidate_total
                - sum(item["candidate"] for item in component_aggregate.values()),
                "host_pair_count": len(rows) - baseline_matrix["host_pair_count"],
            },
        },
        "aggregate": {
            **(
                _comparison_value(baseline_total, candidate_total)
                if not comparison_blocked
                else {"baseline": None, "candidate": None, "delta": None}
            ),
            "reduction_ratio": reduction_ratio,
            "comparable": not comparison_blocked,
        },
        "errors": errors,
    }


def _quality_first_cost_gate(
    *,
    behavior_evidence: dict[str, Any],
    codegen_evidence: dict[str, Any],
    cost_comparison: dict[str, Any],
) -> dict[str, Any]:
    """Apply Core-owned quality precedence to evaluator-owned cost observations."""

    gate = CONTEXT_BUDGET_MODEL["quality_cost_gate"]
    current_behavior_authority = behavior_eval_authority(CORE_CONTRACTS)
    if BEHAVIOR_EVAL_MODEL != current_behavior_authority:
        raise ValueError("Behavior Eval authority is detached or malformed")
    behavior_verdicts = set(BEHAVIOR_EVAL_MODEL["verdicts"])
    behavior_classes = set(BEHAVIOR_EVAL_MODEL["evidence_classes"])
    behavior_statuses = set(BEHAVIOR_EVAL_MODEL["live_evidence_statuses"])
    preserving = set(gate["quality_preserving_verdicts"])
    regression = gate["regression_verdict"]
    missing = gate["missing_evidence_verdict"]
    closed_verdicts = behavior_verdicts
    if (
        preserving | {regression, missing} != behavior_verdicts
        or regression != BEHAVIOR_EVAL_MODEL["verdict_policy"]["quality_regression"]
        or missing != BEHAVIOR_EVAL_MODEL["verdict_policy"]["missing-live-agent-data"]
    ):
        raise ValueError("Behavior Eval authority disagrees with the quality-cost gate")

    def quality_projection(label: str, evidence: Any) -> dict[str, Any]:
        if not isinstance(evidence, dict):
            raise ValueError(f"{label} quality evidence must be an object")
        verdict = evidence.get("verdict")
        evidence_class = evidence.get("evidence_class")
        live_status = evidence.get("live_evidence_status")
        if verdict not in closed_verdicts:
            raise ValueError(f"{label} quality evidence has an unknown verdict")
        if evidence_class not in behavior_classes:
            raise ValueError(f"{label} quality evidence has an unknown evidence class")
        if live_status not in behavior_statuses:
            raise ValueError(f"{label} quality evidence has an unknown live status")
        comparable = (
            evidence_class == "live_agent"
            and live_status == "collected"
            and verdict != missing
        )
        return {
            "evaluation_kind": evidence.get("evaluation_kind"),
            "evidence_class": evidence_class,
            "live_evidence_status": live_status,
            "verdict": verdict,
            "comparable": comparable,
        }

    behavior = quality_projection("behavior", behavior_evidence)
    codegen = quality_projection("codegen", codegen_evidence)
    quality_rows = {"behavior": behavior, "codegen": codegen}
    verdicts = [row["verdict"] for row in quality_rows.values()]
    candidate_rejected = regression in verdicts
    all_comparable = all(row["comparable"] for row in quality_rows.values())
    if candidate_rejected:
        verdict = regression
    elif not all_comparable:
        verdict = missing
    elif "improved" in verdicts:
        verdict = "improved"
    elif "hardening_only" in verdicts:
        verdict = "hardening_only"
    else:
        verdict = "no_effect"
    quality_preserved = all_comparable and verdict in preserving

    aggregate = cost_comparison.get("aggregate", {})
    cost_metrics: dict[str, Any] = {
        "tokens": {
            "baseline": aggregate.get("baseline"),
            "candidate": aggregate.get("candidate"),
            "delta": aggregate.get("delta"),
        }
    }
    for metric in ("turns", "elapsed_ms"):
        values: list[Any] = []
        for side in ("old", "new"):
            side_payload = behavior_evidence.get(side, {})
            side_costs = (
                side_payload.get("cost_metrics", {})
                if isinstance(side_payload, dict)
                else {}
            )
            values.append(side_costs.get(metric) if isinstance(side_costs, dict) else None)
        if behavior["comparable"] and all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in values
        ):
            cost_metrics[metric] = {
                "baseline": values[0],
                "candidate": values[1],
                "delta": values[1] - values[0],
            }
        else:
            cost_metrics[metric] = gate["not_collected_value"]
    if cost_comparison.get("status") != "pass" or aggregate.get("comparable") is not True:
        frontier_status = "not-evaluated-invalid-cost-evidence"
        frontier_eligible = False
    elif not quality_preserved:
        frontier_status = "not-evaluated-quality-evidence"
        frontier_eligible = False
    else:
        delta = aggregate.get("delta")
        observation = cost_comparison.get("cost_observation", {}).get("status")
        if not isinstance(delta, int):
            raise ValueError("cost comparison aggregate delta must be an integer")
        frontier_eligible = True
        if observation == "mixed-cost-deltas":
            frontier_status = "eligible-mixed-cost-not-selected"
        else:
            collected_deltas = [
                value["delta"]
                for value in cost_metrics.values()
                if isinstance(value, dict)
            ]
            if any(value > 0 for value in collected_deltas):
                frontier_status = "eligible-mixed-cost-not-selected"
            elif any(value < 0 for value in collected_deltas):
                frontier_status = "selected-lower-cost"
            else:
                frontier_status = "eligible-equal-cost"
    elapsed_status = (
        "collected"
        if isinstance(cost_metrics["elapsed_ms"], dict)
        else gate["not_collected_value"]
    )
    return {
        "status": "fail" if candidate_rejected else "pass",
        "verdict": verdict,
        "claim_boundary": (
            "bounded-live-quality-comparison"
            if all_comparable
            else gate["structural_claim"]
        ),
        "quality_preserved": quality_preserved,
        "candidate_rejected": candidate_rejected,
        "quality_evidence": quality_rows,
        "cost_frontier": {
            "rule": gate["frontier_rule"],
            "eligible": frontier_eligible,
            "status": frontier_status,
            "metrics": cost_metrics,
            "token_observation": copy.deepcopy(aggregate),
        },
        "live_evidence": {
            "behavior": behavior["live_evidence_status"],
            "codegen": codegen["live_evidence_status"],
            "elapsed_ms": elapsed_status,
        },
        "proof_limits": [
            "Static token counts are cost proxies and do not prove latency.",
            "A candidate total not greater than baseline is not correctness acceptance.",
            "Missing comparable behavior or codegen evidence cannot enter the cost frontier.",
        ],
        "errors": (
            ["quality regression rejects the candidate before cost comparison"]
            if candidate_rejected
            else []
        ),
    }


AB_S1_WRITE_PATHS = frozenset(
    {
        "scripts/eval-rendered-context-budget.py",
        "scripts/eval-agent-lightweight.py",
        "evals/agent-light-trajectories/cases.yaml",
        "tests/scripts/test_eval_rendered_context_budget.py",
        "tests/scripts/test_eval_agent_lightweight_utility.py",
        "tests/scripts/test_eval_agent_lightweight_layer3_references.py",
        "reports/rendered-context-budget.json",
        "reports/hookless-control-plane-eval.json",
    }
)

AB_S2_WRITE_PATHS = frozenset(
    {
        "docs/BUILD_PROFILES.md",
        "scripts/build.py",
        "scripts/validation_utils.py",
        "scripts/validate-agent-profiles.py",
        "scripts/validate-control-plane-prompt.py",
        "scripts/validate-control-skills.py",
        "scripts/validate-skill-routing.py",
        "scripts/validate-task-contracts.py",
        "src/control-prompts/main-control-agent.md",
        "src/agent-profiles/role-agents.json",
        "src/control-skills/engineering-control-plane/references/professional-skill-router.md",
        "src/control-skills/engineering-control-plane/references/implementation-handoff-template.md",
        "src/control-skills/engineering-control-plane/references/review-handoff-template.md",
        "evals/agent-light-trajectories/cases.yaml",
        "scripts/eval-agent-lightweight.py",
        "scripts/eval-rendered-context-budget.py",
        "tests/scripts/test_eval_agent_lightweight_utility.py",
        "tests/scripts/test_eval_rendered_context_budget.py",
        "reports/hookless-control-plane-eval.json",
        "reports/rendered-context-budget.json",
        "reports/rendered-context-budget.md",
        "tests/scripts/test_build_safety.py",
        "tests/test_hookless_build_install.py",
        "tests/scripts/test_validate_agent_profiles.py",
        "tests/scripts/test_validate_control_plane_prompt.py",
        "tests/scripts/test_validate_control_skills.py",
        "tests/scripts/test_validate_docs_consistency.py",
        "tests/scripts/test_authority_delivery_repair.py",
        "tests/scripts/test_rds_005_public_projection.py",
        "tests/scripts/test_validate_task_contracts.py",
        "tests/scripts/test_rds_006_agent_execution_discipline.py",
        "tests/scripts/test_rds_006_task_handoff_context.py",
        "tests/scripts/test_skill_routing_roles.py",
        "tests/scripts/test_selector_jit_domain_parity.py",
        "tests/scripts/test_foundation_selector_authority.py",
        "tests/scripts/test_eval_agent_lightweight_layer3_references.py",
    }
)

AB_S3_WRITE_PATHS = frozenset(
    {
        "scripts/build.py",
        "scripts/validation_utils.py",
        "scripts/validate-built-skill-reference-links.py",
        "scripts/eval-rendered-context-budget.py",
        "tests/scripts/test_built_professional_root_projection.py",
        "tests/scripts/test_selector_jit_domain_parity.py",
        "tests/scripts/test_validate_built_skill_reference_links.py",
        "tests/scripts/test_eval_rendered_context_budget.py",
        "tests/test_hookless_build_install.py",
        "tests/scripts/test_context_content_relocation.py",
        "tests/scripts/test_authority_delivery_repair.py",
        "reports/rendered-context-budget.json",
        "reports/rendered-context-budget.md",
    }
)

AB_P4_INTEGRATION_WRITE_PATHS = frozenset(
    {
        "docs/VALIDATION.md",
        "docs/BENCHMARKS.md",
        "evals/agent-behavior/README.md",
        "evals/agent-behavior/comparison-fixtures/structural-agent-packet.yaml",
        "evals/agent-behavior/comparison-fixtures/structural-observations.yaml",
        "evals/agent-behavior/comparison-fixtures/structural-oracle.yaml",
        "evals/agent-behavior/comparison-fixtures/structural-reveal.yaml",
        "evals/agent-behavior/comparison-fixtures/structural-verifier-capture.yaml",
        "evals/agent-behavior/comparison-fixtures/structural.yaml",
        "scripts/eval-agent-behavior.py",
        "src/control-model/core-contracts.json",
        "src/foundation/capabilities/skill-efficacy-benchmark/SKILL.md",
        "src/foundation/capabilities/skill-efficacy-benchmark/references/benchmarks-and-patterns.md",
        "src/foundation/capabilities/skill-efficacy-benchmark/references/checklist.md",
        "src/foundation/capabilities/skill-efficacy-benchmark/references/evidence-patterns.md",
        "tests/scripts/test_eval_agent_behavior.py",
        "tests/scripts/test_impact_graph.py",
        "tests/scripts/test_validation_utils.py",
    }
)

AB_ALLOWED_WRITE_PATHS = (
    AB_S1_WRITE_PATHS
    | AB_S2_WRITE_PATHS
    | AB_S3_WRITE_PATHS
    | AB_P4_INTEGRATION_WRITE_PATHS
)


def _run_checked(
    command: list[str],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command,
        cwd=cwd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{' '.join(command)} failed: {stderr}")
    return result


def _stage_allowed_untracked_inputs(
    repository_root: Path,
    candidate_root: Path,
    untracked_paths: set[str],
) -> None:
    """Stage the closed P4 fixture/test set into the isolated candidate subject."""

    for relative in sorted(untracked_paths):
        if relative not in AB_ALLOWED_WRITE_PATHS:
            raise ValueError(f"A/B candidate contains out-of-scope path: {relative}")
        source = repository_root / relative
        try:
            source_stat = source.lstat()
        except OSError as exc:
            raise ValueError(f"A/B untracked input is unreadable: {relative}") from exc
        if stat.S_ISLNK(source_stat.st_mode) or not stat.S_ISREG(source_stat.st_mode):
            raise ValueError(f"A/B untracked input must be a regular file: {relative}")
        destination = candidate_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def _validate_candidate_changed_paths(
    candidate_root: Path,
    relative_paths: set[str],
) -> None:
    """Reject staged patch paths that could redirect candidate reads or execution."""

    root = candidate_root.resolve()
    for relative in sorted(relative_paths):
        pure = PurePosixPath(relative)
        if pure.is_absolute() or not pure.parts or ".." in pure.parts:
            raise ValueError(f"A/B candidate path is not contained: {relative}")
        candidate = candidate_root / pure
        try:
            metadata = candidate.lstat()
        except OSError as exc:
            raise ValueError(f"A/B candidate path is not a regular file: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"A/B candidate path must be a regular non-symlink file: {relative}")
        try:
            candidate.resolve(strict=True).relative_to(root)
        except (OSError, ValueError) as exc:
            raise ValueError(f"A/B candidate path escapes containment: {relative}") from exc


def _candidate_quality_evidence(
    candidate_root: Path,
    workspace: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    behavior_dir = workspace / "candidate-behavior"
    _run_checked(
        [
            "python3",
            "scripts/eval-agent-behavior.py",
            "--comparison-spec",
            "evals/agent-behavior/comparison-fixtures/structural.yaml",
            "--format",
            "json",
            "--output-dir",
            str(behavior_dir),
        ],
        cwd=candidate_root,
    )
    behavior_paths = sorted(behavior_dir.glob("*-agent-behavior-comparison.json"))
    if len(behavior_paths) != 1:
        raise ValueError("candidate behavior comparison produced an ambiguous report set")
    behavior = json.loads(behavior_paths[0].read_text(encoding="utf-8"))

    professional_dir = workspace / "candidate-professional"
    _run_checked(
        [
            "python3",
            "scripts/eval-professional-benchmarks.py",
            "--mode",
            "comparison",
            "--reports-dir",
            str(professional_dir),
        ],
        cwd=candidate_root,
    )
    professional = json.loads(
        (professional_dir / "professional-benchmarks-report.json").read_text(
            encoding="utf-8"
        )
    )
    if professional.get("errors") != []:
        raise ValueError("candidate professional benchmark evidence is invalid")
    codegen = {
        "evaluation_kind": professional.get("evaluation_kind"),
        "evidence_class": "structural_only",
        "live_evidence_status": CONTEXT_BUDGET_MODEL["quality_cost_gate"][
            "not_collected_value"
        ],
        "verdict": CONTEXT_BUDGET_MODEL["quality_cost_gate"][
            "missing_evidence_verdict"
        ],
        "claim_boundary": "captured-fixture-harness-validity-only",
        "source_report_sha256": hashlib.sha256(
            json.dumps(professional, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest(),
    }
    return behavior, codegen


def _load_current_lightweight_module(path: Path) -> Any:
    module_name = f"changeforge_native_structure_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load current lightweight evaluator {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, "_native_structural_metrics", None)):
        raise ValueError("current lightweight evaluator lacks native structural metrics")
    if not callable(getattr(module, "_minimal_dispatch_partition", None)):
        raise ValueError("current lightweight evaluator lacks minimal dispatch projection")
    if not callable(getattr(module, "_minimal_transfer_projection", None)):
        raise ValueError("current lightweight evaluator lacks minimal transfer projection")
    return module


def _git_text(root: Path, *arguments: str) -> str:
    return _run_checked(["git", *arguments], cwd=root).stdout.decode("utf-8").strip()


def _native_contract_identity(document: dict[str, Any]) -> dict[str, Any]:
    schema_version = document.get("schema_version")
    if type(schema_version) is not int:
        raise ValueError("native fixture schema_version is missing or ambiguous")
    capsule_contracts: Counter[tuple[str, str | None, str | None, str]] = Counter()
    trajectory_count = 0
    for _group, case in _fixture_cases(document):
        trajectory_count += 1
        for step in case.get("steps", []):
            if not isinstance(step, dict) or step.get("action") != "dispatch":
                continue
            _selector, capsules = _native_dispatch_partition(step)
            for capsule_field, capsule in capsules.items():
                contract_version = capsule.get("contract_version")
                contract_type = capsule.get("contract_type")
                if capsule_field == "fixture_capsule":
                    if not isinstance(contract_version, str) or not contract_version:
                        raise ValueError(
                            f"{case.get('id')}: native capsule contract_version is missing"
                        )
                    if not isinstance(contract_type, str) or not contract_type:
                        raise ValueError(
                            f"{case.get('id')}: native capsule contract_type is missing"
                        )
                    version_state = "versioned-native-envelope"
                else:
                    if contract_version is not None and (
                        not isinstance(contract_version, str) or not contract_version
                    ):
                        raise ValueError(
                            f"{case.get('id')}: native utility capsule version is malformed"
                        )
                    if contract_type is not None and (
                        not isinstance(contract_type, str) or not contract_type
                    ):
                        raise ValueError(
                            f"{case.get('id')}: native utility capsule type is malformed"
                        )
                    version_state = (
                        "versioned-native-auxiliary"
                        if contract_version
                        else "unversioned-native-auxiliary"
                    )
                capsule_contracts[
                    (capsule_field, contract_version, contract_type, version_state)
                ] += 1
    return {
        "fixture_schema_version": schema_version,
        "trajectory_case_count": trajectory_count,
        "task_focus_case_count": len(document.get("task_focus_cases", [])),
        "capsule_contracts": [
            {
                "capsule_field": capsule_field,
                "contract_version": version,
                "contract_type": contract_type,
                "version_state": version_state,
                "count": count,
            }
            for (
                capsule_field,
                version,
                contract_type,
                version_state,
            ), count in sorted(
                capsule_contracts.items(), key=lambda item: repr(item[0])
            )
        ],
    }


def _registry_documents(subject_root: Path) -> list[tuple[Path, str, dict[str, Any]]]:
    specs = (
        (subject_root / "src/registry/professional-skills.yaml", "professional_skills"),
        (subject_root / "src/registry/foundation-skills.yaml", "foundation_skills"),
        (subject_root / "src/registry/domain-skills.yaml", "domain_skills"),
    )
    return [(path, key, load_yaml_file(path)) for path, key in specs]


def _reference_native_binding(
    subject_root: Path,
    owner: str,
    relative_path: str,
    *,
    semantic_obligation: str | None = None,
) -> dict[str, Any]:
    matches: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    for registry_path, key, document in _registry_documents(subject_root):
        for row in document.get(key, []):
            if not isinstance(row, dict) or row.get("name") != owner:
                continue
            reference = next(
                (
                    item
                    for item in row.get("reference_index", [])
                    if isinstance(item, dict) and item.get("path") == relative_path
                ),
                None,
            )
            if reference is not None:
                matches.append((registry_path, row, reference))
    if len(matches) != 1:
        raise ValueError(
            f"{owner}/{relative_path}: expected one native registry binding, got {len(matches)}"
        )
    registry_path, owner_row, reference = matches[0]
    source_path = subject_root / str(owner_row["path"]) / relative_path
    source_bytes = source_path.read_bytes()
    return {
        "semantic_obligation": semantic_obligation or f"{owner}/{relative_path}",
        "owner": owner,
        "physical_path": source_path.relative_to(subject_root).as_posix(),
        "reference_type": str(reference.get("type") or ""),
        "required_outputs": [str(item) for item in reference.get("required_output", [])],
        "registry_path": registry_path.relative_to(subject_root).as_posix(),
        "registry_sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "tokens": count_o200k_base_tokens(source_bytes.decode("utf-8")),
        "content_scope": "complete-native-bytes",
    }


def _canonical_reference_obligation(
    case_id: str, owner: str, relative_path: str
) -> str:
    if (
        owner == "payment-trading-extension"
        and relative_path
        in {
            "references/checklist.md",
            "references/duplicate-financial-effect-control.md",
        }
    ):
        return "payment-duplicate-financial-effect-control"
    return REFERENCE_SEMANTIC_EQUIVALENCE.get(
        (case_id, owner, relative_path), f"{owner}/{relative_path}"
    )


def _case_native_reference_bindings(
    case: dict[str, Any], subject_root: Path
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    case_id = str(case.get("id") or "")
    for step in case.get("steps", []):
        if not isinstance(step, dict) or step.get("action") != "dispatch":
            continue
        primary = str(step.get("primary_skill") or "")
        for relative_path in step.get("professional_references", []):
            result.append(
                _reference_native_binding(
                    subject_root,
                    primary,
                    str(relative_path),
                    semantic_obligation=_canonical_reference_obligation(
                        case_id, primary, str(relative_path)
                    ),
                )
            )
        for logical_id in step.get("layer3_references", []):
            owner, relative_path = str(logical_id).split("/", 1)
            result.append(
                _reference_native_binding(
                    subject_root,
                    owner,
                    relative_path,
                    semantic_obligation=_canonical_reference_obligation(
                        case_id, owner, relative_path
                    ),
                )
            )
    return result


def _trajectory_exact_reference_selection(
    step: dict[str, Any], subject_root: Path
) -> tuple[list[str] | None, list[dict[str, Any]]]:
    """Bind the two native trajectory Reference fields or remain unresolved."""

    if not all(
        field in step for field in ("professional_references", "layer3_references")
    ):
        return None, []
    professional_references = step.get("professional_references")
    layer3_references = step.get("layer3_references")
    if (
        not isinstance(professional_references, list)
        or not isinstance(layer3_references, list)
        or any(
            not isinstance(item, str) or not item
            for item in [*professional_references, *layer3_references]
        )
        or len(professional_references) != len(set(professional_references))
        or len(layer3_references) != len(set(layer3_references))
    ):
        raise ValueError(
            "trajectory exact References require two ordered unique string lists"
        )
    primary = str(step.get("primary_skill") or "")
    selected_layer3 = step.get("layer3_skills")
    if not primary or not isinstance(selected_layer3, list):
        raise ValueError("trajectory exact References require current route authority")
    exact: list[str] = []
    bindings: list[dict[str, Any]] = []
    for relative_path in professional_references:
        native = _reference_native_binding(subject_root, primary, relative_path)
        exact.append(relative_path)
        bindings.append(
            {"owner_skill": primary, "path": relative_path, **native}
        )
    for logical_id in layer3_references:
        try:
            owner, relative_path = logical_id.split("/", 1)
        except ValueError as exc:
            raise ValueError(
                "trajectory Layer 3 Reference lacks owner/path binding"
            ) from exc
        if owner not in selected_layer3:
            raise ValueError(
                "trajectory Layer 3 Reference owner is not in ordered selected Layer 3"
            )
        native = _reference_native_binding(subject_root, owner, relative_path)
        exact.append(logical_id)
        bindings.append(
            {"owner_skill": owner, "path": relative_path, **native}
        )
    if len({(row["owner_skill"], row["path"]) for row in bindings}) != len(bindings):
        raise ValueError("trajectory exact References contain duplicate bindings")
    return exact, bindings


def _route_obligations(
    case: dict[str, Any], subject_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    domain_document = load_yaml_file(
        subject_root / "src/registry/domain-skills.yaml"
    )
    domain_names = {
        str(row.get("name") or "")
        for row in domain_document.get("domain_skills", [])
        if isinstance(row, dict)
    }
    professional: list[str] = []
    layer3: list[str] = []
    references: list[str] = []
    canonical_references: list[str] = []
    review: list[str] = []
    case_id = str(case.get("id") or "")
    for step in case.get("steps", []):
        if not isinstance(step, dict) or step.get("action") != "dispatch":
            continue
        primary = str(step.get("primary_skill") or "")
        if primary:
            professional.append(primary)
        layer3.extend(str(item) for item in step.get("layer3_skills", []))
        for item in step.get("professional_references", []):
            relative_path = str(item)
            references.append(relative_path)
            canonical_references.append(
                _canonical_reference_obligation(case_id, primary, relative_path)
            )
        for item in step.get("layer3_references", []):
            logical_id = str(item)
            references.append(logical_id)
            owner, relative_path = logical_id.split("/", 1)
            canonical_references.append(
                _canonical_reference_obligation(case_id, owner, relative_path)
            )
        if step.get("profile") == "review-agent" and primary:
            review.append(primary)
        capsule = step.get("fixture_capsule")
        if isinstance(capsule, dict):
            review.extend(
                str(item) for item in capsule.get("required_review_skills", [])
            )
    raw = {
        "professional": professional,
        "layer3": layer3,
        "domain": [item for item in layer3 if item in domain_names],
        "review": review,
        "references": references,
    }
    canonical = copy.deepcopy(raw)
    canonical["references"] = canonical_references
    return canonical, raw


def _native_transfer_measurement(
    case: dict[str, Any], lightweight_module: Any
) -> dict[str, Any]:
    case_id = case.get("id")
    steps = case.get("steps")
    if not isinstance(case_id, str) or not case_id or not isinstance(steps, list):
        raise ValueError("native transfer requires a case id and steps")
    handoff_actions = {
        "analysis-handoff",
        "implementation-handoff",
        "review-handoff",
        "repair-handoff",
    }
    rows: list[dict[str, Any]] = []
    total = 0
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not step.get("action"):
            raise ValueError(f"{case_id}: malformed native transfer step {index}")
        if step.get("action") not in handoff_actions:
            continue
        projected = lightweight_module._minimal_transfer_projection(step)
        text = _canonical_json_text(projected)
        tokens = count_o200k_base_tokens(text)
        total += tokens
        rows.append(
            {
                "step": index,
                "action": step["action"],
                "sha256": _sha256_text(text),
                "tokens": tokens,
                "content_scope": "core-derived-minimal-handoff",
            }
        )
    return {
        "gross_tokens": total,
        "handoff_tokens": total,
        "handoff_rows": rows,
    }


_COMBINED_ROUTER_HEADER = (
    "| Task signal | Start profile | Primary Professional Skill | "
    "Optional Layer 3 Skills | Review Skill |"
)
_SPLIT_ROUTER_HEADER = (
    "| Task signal | Start profile | Primary Professional Skill | Review Skill |"
)


def _professional_router_authority(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError("professional router authority is unavailable") from exc
    headers = [
        header for header in (_COMBINED_ROUTER_HEADER, _SPLIT_ROUTER_HEADER)
        if header in text.splitlines()
    ]
    if len(headers) != 1:
        raise ValueError("professional router schema header is missing or ambiguous")
    schema = (
        "combined-router/v1"
        if headers[0] == _COMBINED_ROUTER_HEADER
        else "split-professional-selector/v1"
    )
    rows: list[dict[str, Any]] = []
    expected_columns = 5 if schema == "combined-router/v1" else 4
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("|") or line.startswith("| ---") or line == headers[0]:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != expected_columns:
            continue
        layer3 = []
        if schema == "combined-router/v1" and cells[3] != "none":
            layer3 = [item.strip() for item in cells[3].split(",")]
        rows.append(
            {
                "pointer": f"#L{line_number}",
                "signal": cells[0],
                "profile": cells[1],
                "professional_skill": cells[2],
                "layer3_skills": layer3,
                "review_skill": cells[-1],
            }
        )
    if not rows:
        raise ValueError("professional router has no declared route rows")
    return {
        "schema": schema,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "header": headers[0],
        "rows": rows,
    }


def _native_combined_dispatch_binding(
    case_id: str,
    step_index: int,
    step: dict[str, Any],
    subject_root: Path,
    router_authority: dict[str, Any],
) -> dict[str, Any]:
    """Bind a historical dispatch to one source-owned combined-router trigger."""

    fixture_path = subject_root / "evals/agent-light-trajectories/cases.yaml"
    if not fixture_path.is_file():
        fixture_path = FIXTURES
    try:
        fixture_raw = fixture_path.read_bytes()
        fixture_document = json.loads(fixture_raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("combined router native fixture authority is unavailable") from exc
    native_cases = [
        case
        for _group, case in _fixture_cases(fixture_document)
        if case.get("id") == case_id
    ]
    if len(native_cases) != 1:
        raise ValueError("combined router native case authority is missing or ambiguous")
    native_steps = native_cases[0].get("steps")
    if (
        not isinstance(native_steps, list)
        or step_index >= len(native_steps)
        or native_steps[step_index] != step
    ):
        raise ValueError("combined router native dispatch authority disagrees")

    profile = str(step.get("profile") or "")
    primary = str(step.get("primary_skill") or "")
    effective = step.get("layer3_skills")
    if not profile or not primary or not isinstance(effective, list):
        raise ValueError("combined router native dispatch is malformed")
    fixture_relative = (
        fixture_path.relative_to(subject_root).as_posix()
        if fixture_path.is_relative_to(subject_root)
        else fixture_path.as_posix()
    )
    fixture_authority = {
        "path": fixture_relative,
        "sha256": hashlib.sha256(fixture_raw).hexdigest(),
        "pointer": f"#/case/{case_id}/steps/{step_index}",
        "profile": profile,
        "primary_skill": primary,
        "layer3_skills": list(effective),
    }

    scenario_path = subject_root / "src/registry/release-routing-scenarios.yaml"
    scenario_raw = b""
    scenarios: list[dict[str, Any]] = []
    if scenario_path.is_file():
        scenario_raw = scenario_path.read_bytes()
        scenario_document = load_yaml_file(scenario_path)
        scenarios = [
            row
            for row in scenario_document.get("scenarios", [])
            if isinstance(row, dict) and row.get("light_case_id") == case_id
        ]
    if len(scenarios) > 1:
        raise ValueError("combined router release scenario authority is ambiguous")

    route_expectation: dict[str, Any] | None = None
    dispatch_authority = dict(fixture_authority)
    augmentation_source = dict(fixture_authority)
    if scenarios:
        scenario = scenarios[0]
        router = scenario.get("router")
        expected = router.get("expected") if isinstance(router, dict) else None
        if (
            not isinstance(router, dict)
            or not isinstance(router.get("trigger"), str)
            or not isinstance(expected, dict)
        ):
            raise ValueError("combined router release scenario is malformed")
        route_expectation = {
            "trigger": router["trigger"],
            "profile": expected.get("profile"),
            "primary": expected.get("primary"),
            "layer3": expected.get("layer3"),
            "review": expected.get("review"),
        }
        if (
            not isinstance(route_expectation["profile"], str)
            or not isinstance(route_expectation["primary"], str)
            or not isinstance(route_expectation["review"], str)
            or not isinstance(route_expectation["layer3"], list)
        ):
            raise ValueError("combined router release scenario route is incomplete")
        scenario_sha = hashlib.sha256(scenario_raw).hexdigest()
        scenario_index = scenario_document["scenarios"].index(scenario)
        scenario_pointer = f"#/scenarios/{scenario_index}"
        scenario_dispatches: list[tuple[str, int, dict[str, Any]]] = []
        analysis = scenario.get("analysis")
        if isinstance(analysis, dict):
            scenario_dispatches.append(("analysis-agent", 0, analysis))
        scenario_dispatches.extend(
            ("task-agent", index, row)
            for index, row in enumerate(scenario.get("tasks", []))
            if isinstance(row, dict)
        )
        review = scenario.get("review")
        if isinstance(review, dict):
            scenario_dispatches.append(("review-agent", 0, review))
        matching = [
            (role, index, row)
            for role, index, row in scenario_dispatches
            if role == profile
            and row.get("primary") == primary
            and row.get("layer3", []) == effective
        ]
        if profile == route_expectation["profile"] and primary == route_expectation["primary"] and effective == route_expectation["layer3"]:
            matching.append((profile, -1, expected))
        if not matching:
            raise ValueError("combined router dispatch disagrees with release scenario")
        role_matches = [
            (index, item)
            for index, native_step in enumerate(native_steps[: step_index + 1])
            if isinstance(native_step, dict)
            and native_step.get("action") == "dispatch"
            and native_step.get("profile") == profile
            and native_step.get("primary_skill") == primary
            and native_step.get("layer3_skills") == effective
            for item in [native_step]
        ]
        occurrence = len(role_matches) - 1
        chosen = matching[min(occurrence, len(matching) - 1)]
        source_kind, source_index, source_row = chosen
        source_pointer = (
            f"{scenario_pointer}/router/expected"
            if source_index == -1
            else (
                f"{scenario_pointer}/analysis"
                if source_kind == "analysis-agent"
                else (
                    f"{scenario_pointer}/tasks/{source_index}"
                    if source_kind == "task-agent"
                    else f"{scenario_pointer}/review"
                )
            )
        )
        dispatch_review = (
            primary
            if profile == "review-agent"
            else source_row.get("review", route_expectation["review"])
        )
        dispatch_authority = {
            "path": scenario_path.relative_to(subject_root).as_posix(),
            "sha256": scenario_sha,
            "pointer": source_pointer,
            "profile": profile,
            "primary_skill": primary,
            "review_skill": dispatch_review,
            "layer3_skills": list(effective),
        }
        augmentation_source = dict(dispatch_authority)

    rows = router_authority.get("rows")
    if not isinstance(rows, list):
        raise ValueError("combined router rows are unavailable")
    if route_expectation is None:
        if _has_authoritative_task_dag_provenance(
            step,
            str(native_cases[0].get("kind") or ""),
            native_steps,
        ):
            dag_rows = [
                row
                for row in rows
                if "authoritative Task DAG downstream integration tasks"
                in str(row.get("signal") or "")
            ]
            if len(dag_rows) != 1:
                raise ValueError(
                    "combined router authoritative Task DAG trigger is missing or ambiguous"
                )
            dag_row = dag_rows[0]
            route_expectation = {
                "trigger": dag_row["signal"],
                "profile": dag_row["profile"],
                "primary": dag_row["professional_skill"],
                "layer3": dag_row["layer3_skills"],
                "review": dag_row["review_skill"],
            }
        elif profile == "review-agent":
            prior = next(
                (
                    (index, native_step)
                    for index, native_step in reversed(
                        list(enumerate(native_steps[:step_index]))
                    )
                    if isinstance(native_step, dict)
                    and native_step.get("action") == "dispatch"
                    and native_step.get("primary_skill") == primary
                ),
                None,
            )
            if prior is not None:
                prior_index, prior_step = prior
                prior_binding = _native_combined_dispatch_binding(
                    case_id,
                    prior_index,
                    prior_step,
                    subject_root,
                    router_authority,
                )
                route_expectation = {
                    "trigger": prior_binding["router_trigger"],
                    "profile": prior_binding["router_profile"],
                    "primary": prior_binding["router_primary_skill"],
                    "layer3": prior_binding["router_layer3_skills"],
                    "review": prior_binding["review_skill"],
                }
    if route_expectation is None:
        candidates = []
        for row in rows:
            row_layer3 = row.get("layer3_skills", [])
            if not isinstance(row_layer3, list):
                continue
            direct = row.get("profile") == profile and row.get("professional_skill") == primary
            professional = row.get("professional_skill") == primary
            review = profile == "review-agent" and row.get("review_skill") == primary
            if not (direct or professional or review):
                continue
            overlap = sum(item in row_layer3 for item in effective)
            candidates.append(((int(direct), overlap, int(professional), int(review)), row))
        if not candidates:
            raise ValueError("combined router native trigger authority is missing")
        maximum = max(score for score, _row in candidates)
        selected = [row for score, row in candidates if score == maximum]
        if len(selected) != 1:
            raise ValueError("combined router native trigger authority is ambiguous")
        selected_row = selected[0]
        route_expectation = {
            "trigger": selected_row["signal"],
            "profile": selected_row["profile"],
            "primary": selected_row["professional_skill"],
            "layer3": selected_row["layer3_skills"],
            "review": selected_row["review_skill"],
        }
        dispatch_authority["review_skill"] = (
            primary if profile == "review-agent" else selected_row["review_skill"]
        )
    exact_rows = [
        row
        for row in rows
        if row.get("signal") == route_expectation["trigger"]
        and row.get("profile") == route_expectation["profile"]
        and row.get("professional_skill") == route_expectation["primary"]
        and row.get("review_skill") == route_expectation["review"]
        and row.get("layer3_skills") == route_expectation["layer3"]
    ]
    if len(exact_rows) != 1:
        raise ValueError("combined router scenario trigger has no exact native row")
    base = [item for item in effective if item in route_expectation["layer3"]]
    augmentation = [item for item in effective if item not in base]
    return {
        "router_trigger": route_expectation["trigger"],
        "router_profile": route_expectation["profile"],
        "router_primary_skill": route_expectation["primary"],
        "router_layer3_skills": list(route_expectation["layer3"]),
        "review_skill": route_expectation["review"],
        "dispatch_authority": dispatch_authority,
        "handoff_augmentation_authority": (
            {
                **augmentation_source,
                "layer3_skills": augmentation,
            }
            if augmentation
            else None
        ),
    }


def _selection_authority_bundle(
    *,
    schema: str,
    router_rows: list[dict[str, Any]],
    step: dict[str, Any],
    selector: dict[str, Any] | None,
    selector_resolution: dict[str, Any] | None = None,
    reference_partitions: dict[str, dict[str, Any]] | None = None,
    exact_references: object = None,
    exact_reference_bindings: object = None,
    envelope_pointer: str,
    envelope_sha256: str,
    selection_owner: str = "main-control-agent",
) -> dict[str, Any]:
    profile = str(step.get("profile") or "")
    primary = str(step.get("primary_skill") or "")
    effective = step.get("layer3_skills")
    if (
        not profile
        or not primary
        or not isinstance(effective, list)
        or any(not isinstance(item, str) or not item for item in effective)
        or len(effective) != len(set(effective))
        or len(effective) > 3
    ):
        raise ValueError("native dispatch selection envelope is malformed")
    direct = [
        row
        for row in router_rows
        if row.get("profile") == profile
        and row.get("professional_skill") == primary
    ]
    relevant = direct or [
        row for row in router_rows if row.get("professional_skill") == primary
    ]
    if not relevant and profile == "review-agent":
        relevant = [
            row for row in router_rows if row.get("review_skill") == primary
        ]
    if schema == "split-professional-selector/v1" and not relevant:
        raise ValueError("native dispatch Professional route lacks router authority")

    if schema == "split-professional-selector/v1":
        if not isinstance(selector, dict):
            raise ValueError("split router requires Professional selector authority")
        if (
            selector.get("contract")
            != "changeforge.layer3-selector-normalized-control/v1"
            or selector.get("professional_skill") != primary
        ):
            raise ValueError("Professional selector authority mismatch")
        surfaces = selector.get("owner_surfaces")
        matches = [
            (index, surface)
            for index, surface in enumerate(surfaces if isinstance(surfaces, list) else [])
            if isinstance(surface, dict)
            and surface.get("profile") == profile
            and surface.get("selection_owner") == selection_owner
        ]
        if len(matches) != 1:
            raise ValueError("Professional selector has no unique Profile surface")
        surface_index, _surface = matches[0]
        try:
            exact_layer3 = (
                effective
                if selector_resolution is not None
                and selector_resolution.get("selection_kind") == "exact"
                else None
            )
            expanded = layer3_selector_expand_runtime_projection(
                selector,
                reference_partitions,
                profile=profile,
                selection_owner=selection_owner,
                exact_layer3=exact_layer3,
                selected_layer3=effective,
                exact_references=exact_references,
                exact_reference_bindings=exact_reference_bindings,
            )
        except ValidationProblem as exc:
            raise ValueError(
                "Professional selector expansion failed closed"
            ) from exc
        authorized = expanded.get("authorized_layer3")
        if (
            not isinstance(authorized, list)
            or any(item not in authorized for item in effective)
        ):
            raise ValueError("effective Layer 3 disagrees with Professional selector")
        receipt = None
        if exact_layer3 is not None:
            receipt = layer3_selector_runtime_selection_receipt(
                expanded,
                evidence_signals=[],
            )
            if receipt["selected_layer3"] != effective:
                raise ValueError("selector receipt disagrees with effective Layer 3")
        return {
            "schema": schema,
            "router_pointers": [row["pointer"] for row in relevant],
            "router_declared_layer3": [],
            "professional_selector_pointer": f"#/owner_surfaces/{surface_index}",
            "professional_selector_resolution": copy.deepcopy(selector_resolution),
            "professional_selector_receipt": receipt,
            "selection_owner": selection_owner,
            "professional_selector_declared_layer3": list(authorized),
            "reference_partitions_loaded": (
                [primary, *effective] if exact_references is None else []
            ),
            "reference_partition_pointers": (
                [
                    selector["reference_records_partition"]["path_template"].format(
                        owner_skill=owner
                    )
                    for owner in [primary, *effective]
                ]
                if exact_references is None
                else []
            ),
            "native_envelope": {
                "pointer": envelope_pointer,
                "sha256": envelope_sha256,
            },
            "handoff_augmentation": {
                "pointer": envelope_pointer,
                "sha256": envelope_sha256,
                "layer3_skills": [],
                "tokens_added": 0,
                "accounting": "already-counted-native-selector-envelope",
            },
            "effective_ordered_layer3": list(effective),
        }

    if schema != "combined-router/v1" or selector is not None:
        raise ValueError("selection authority schema disagrees with supplied assets")
    route_profile = str(step.get("router_profile") or profile)
    route_primary = str(step.get("router_primary_skill") or primary)
    route_trigger = str(step.get("router_trigger") or "")
    review_skill = str(step.get("review_skill") or "")
    if not route_trigger or not review_skill:
        raise ValueError("combined router dispatch lacks source route authority")
    exact_rows = [
        row
        for row in router_rows
        if row.get("signal") == route_trigger
        and row.get("profile") == route_profile
        and row.get("professional_skill") == route_primary
        and row.get("review_skill") == review_skill
    ]
    if len(exact_rows) != 1:
        raise ValueError("combined router trigger authority is missing or ambiguous")
    route_row = exact_rows[0]
    declared = route_row.get("layer3_skills")
    if not isinstance(declared, list) or any(
        not isinstance(item, str) or not item for item in declared
    ):
        raise ValueError("combined router trigger Layer 3 authority is malformed")
    base = [item for item in effective if item in declared]
    augmentation = [item for item in effective if item not in base]
    augmentation_authority = step.get("handoff_augmentation_authority")
    if augmentation:
        required = {"path", "sha256", "pointer", "layer3_skills"}
        if (
            not isinstance(augmentation_authority, dict)
            or set(augmentation_authority) < required
            or not isinstance(augmentation_authority.get("path"), str)
            or not isinstance(augmentation_authority.get("pointer"), str)
            or not isinstance(augmentation_authority.get("sha256"), str)
            or len(augmentation_authority["sha256"]) != 64
            or augmentation_authority.get("layer3_skills") != augmentation
        ):
            raise ValueError("combined router handoff augmentation authority mismatch")
    elif augmentation_authority not in (None, {}):
        if not isinstance(augmentation_authority, dict) or augmentation_authority.get(
            "layer3_skills"
        ) not in (None, []):
            raise ValueError("combined router has unexpected augmentation authority")
    dispatch_authority = step.get("dispatch_authority")
    if route_profile != profile or route_primary != primary:
        if (
            not isinstance(dispatch_authority, dict)
            or dispatch_authority.get("profile") != profile
            or dispatch_authority.get("primary_skill") != primary
            or dispatch_authority.get("layer3_skills") != effective
            or not dispatch_authority.get("path")
            or not dispatch_authority.get("sha256")
            or not dispatch_authority.get("pointer")
        ):
            raise ValueError("combined router downstream dispatch authority mismatch")
    return {
        "schema": schema,
        "router_pointers": [str(route_row["pointer"])],
        "router_trigger": route_trigger,
        "router_profile": route_profile,
        "router_primary_skill": route_primary,
        "router_review_skill": review_skill,
        "router_declared_layer3": base,
        "professional_selector_pointer": None,
        "selection_owner": "native-dispatch-envelope",
        "professional_selector_declared_layer3": [],
        "reference_partitions_loaded": [],
        "reference_partition_pointers": [],
        "native_envelope": {
            "pointer": envelope_pointer,
            "sha256": envelope_sha256,
        },
        "handoff_augmentation": {
            "pointer": (
                augmentation_authority["pointer"]
                if augmentation
                else envelope_pointer
            ),
            "sha256": (
                augmentation_authority["sha256"]
                if augmentation
                else envelope_sha256
            ),
            "authority_path": (
                augmentation_authority["path"] if augmentation else None
            ),
            "layer3_skills": augmentation,
            "tokens_added": 0,
            "accounting": "already-counted-native-selector-envelope",
        },
        "dispatch_authority": copy.deepcopy(dispatch_authority),
        "effective_ordered_layer3": list(effective),
    }


def _native_selector_decision_context(
    case_id: str,
    step: dict[str, Any],
    subject_root: Path,
    router_authority: dict[str, Any],
) -> dict[str, Any]:
    """Derive a runtime tuple from Router authority and provenance independently."""

    profile = str(step.get("profile") or "")
    professional = str(step.get("primary_skill") or "")
    mode = str(step.get("mode") or "")
    if not profile or not professional or not mode:
        raise ValueError("Professional selector dispatch lacks a runtime route tuple")
    all_router_rows = [
        row
        for row in router_authority["rows"]
        if row.get("profile") == profile
        and row.get("professional_skill") == professional
    ]
    route_rows = [
        row
        for row in all_router_rows
        if f"(`{mode}`)" in str(row.get("signal") or "")
    ]
    if len(route_rows) != 1:
        scenario_path = subject_root / "src/registry/release-routing-scenarios.yaml"
        scenario_document = load_yaml_file(scenario_path)
        scenario_rows = [
            row
            for row in scenario_document.get("scenarios", [])
            if isinstance(row, dict) and row.get("light_case_id") == case_id
        ]
        scenario_router = (
            scenario_rows[0].get("router") if len(scenario_rows) == 1 else None
        )
        scenario_expected = (
            scenario_router.get("expected")
            if isinstance(scenario_router, dict)
            else None
        )
        route_rows = [
            row
            for row in all_router_rows
            if isinstance(scenario_expected, dict)
            and row.get("signal") == scenario_router.get("trigger")
            and row.get("review_skill") == scenario_expected.get("review")
        ]
    if len(route_rows) != 1:
        raise ValueError("Professional selector Router tuple is missing or ambiguous")
    route_row = route_rows[0]
    source_router_path = (
        subject_root
        / "src/control-skills/engineering-control-plane/references/"
        "professional-skill-router.md"
    )
    try:
        source_router_raw = source_router_path.read_bytes()
        source_router_text = source_router_raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError("Professional selector source Router is unavailable") from exc
    route_pointer = (
        f"| {route_row['signal']} | {profile} | {professional} | "
        f"{route_row['review_skill']} |"
    )
    if source_router_text.count(route_pointer) != 1:
        raise ValueError("Professional selector source Router tuple is stale or ambiguous")
    runtime_key = {
        "route_source": {
            "path": source_router_path.relative_to(subject_root).as_posix(),
            "sha256": hashlib.sha256(source_router_raw).hexdigest(),
            "pointer": route_pointer,
        },
        "trigger": route_row["signal"],
        "start_profile": profile,
        "primary_professional_skill": professional,
        "review_skill": route_row["review_skill"],
        "selection_owner": "main-control-agent",
    }

    scenarios_path = subject_root / "src/registry/release-routing-scenarios.yaml"
    scenarios = load_yaml_file(scenarios_path)
    if (
        not isinstance(scenarios, dict)
        or scenarios.get("schema_version") != 2
        or scenarios.get("kind") != "changeforge.release_routing_scenarios"
        or not isinstance(scenarios.get("scenarios"), list)
    ):
        raise ValueError("Professional selector release-scenario authority is malformed")
    matches = []
    for row in scenarios["scenarios"]:
        router = row.get("router") if isinstance(row, dict) else None
        expected = router.get("expected") if isinstance(router, dict) else None
        if (
            isinstance(expected, dict)
            and router.get("trigger") == runtime_key["trigger"]
            and expected.get("profile") == runtime_key["start_profile"]
            and expected.get("primary")
            == runtime_key["primary_professional_skill"]
            and expected.get("review") == runtime_key["review_skill"]
            and expected.get("layer3") == step.get("layer3_skills")
        ):
            matches.append(row)
    if len(matches) > 1 or (mode == "diagnosis-only" and len(matches) != 1):
        raise ValueError("Professional selector release provenance is missing or ambiguous")
    scenario_raw = scenarios_path.read_bytes()
    if not matches:
        return {
            "runtime_key": runtime_key,
            "source_authorities": {
                "router": copy.deepcopy(runtime_key["route_source"]),
                "release_scenario": None,
                "selector_registry": None,
            },
            "provenance": {"scenario_id": None, "light_case_id": None},
        }
    scenario = matches[0]
    foundation_path = subject_root / "src/registry/foundation-skills.yaml"
    foundation = load_yaml_file(foundation_path)
    aliases = (
        foundation.get("selector_authority", {}).get("aliases", [])
        if isinstance(foundation, dict)
        else []
    )
    alias = [
        row
        for row in aliases
        if isinstance(row, dict)
        and row.get("candidate_id") == "failure-diagnosis-analysis"
        and row.get("primary_skill") == professional
        and row.get("review_skill") == runtime_key["review_skill"]
    ]
    if mode == "diagnosis-only" and len(alias) != 1:
        raise ValueError("Professional selector registry provenance is missing or ambiguous")
    try:
        foundation_raw = foundation_path.read_bytes()
    except OSError as exc:
        raise ValueError("Professional selector registry provenance is unavailable") from exc
    return {
        "runtime_key": runtime_key,
        "source_authorities": {
            "router": copy.deepcopy(runtime_key["route_source"]),
            "release_scenario": {
                "path": scenarios_path.relative_to(subject_root).as_posix(),
                "sha256": hashlib.sha256(scenario_raw).hexdigest(),
                "pointer": f"scenarios[id={scenario.get('id')}]",
            },
            "selector_registry": (
                {
                    "path": foundation_path.relative_to(subject_root).as_posix(),
                    "sha256": hashlib.sha256(foundation_raw).hexdigest(),
                    "pointer": (
                        "selector_authority.aliases[candidate_id="
                        "failure-diagnosis-analysis]"
                    ),
                }
                if mode == "diagnosis-only"
                else None
            ),
        },
        "provenance": {
            "scenario_id": scenario.get("id"),
            "light_case_id": scenario.get("light_case_id"),
        },
    }


def _validate_selection_asset_occurrences(rows: list[dict[str, Any]]) -> None:
    seen_paths: set[tuple[str, str]] = set()
    seen_hashes: set[tuple[str, str]] = set()
    for row in rows:
        host = str(row.get("host") or "")
        path_key = (host, str(row.get("physical_path") or ""))
        hash_key = (host, str(row.get("sha256") or ""))
        if path_key in seen_paths or hash_key in seen_hashes:
            raise ValueError("duplicate selection asset in one host assignment")
        seen_paths.add(path_key)
        seen_hashes.add(hash_key)


def _native_dispatch_selection_assets(
    case_id: str,
    step_index: int,
    step: dict[str, Any],
    subject_root: Path,
    manifests: dict[str, dict[str, Any]],
    *,
    envelope_pointer: str | None = None,
    envelope_sha256: str | None = None,
    selection_owner: str = "main-control-agent",
    loaded_assignment_keys: set[tuple[str, ...]] | None = None,
    global_router_loaded_hosts: set[str] | None = None,
) -> dict[str, Any]:
    """Measure one dispatch without reloading case or assignment authority."""

    if set(manifests) != set(BUILD_PROFILES):
        raise ValueError(f"{case_id}: dispatch {step_index} requires all three manifests")
    manifest_bindings: dict[str, dict[str, Any]] = {}
    expected_input: dict[str, Any] | None = None
    for profile in BUILD_PROFILES:
        path = (
            subject_root
            / "dist/universal/skills"
            / profile
            / ".changeforge-build-manifest.json"
        )
        try:
            raw = path.read_bytes()
            current = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{case_id}: {profile} manifest is unavailable or malformed"
            ) from exc
        if current != manifests[profile] or current.get("profile") != profile:
            raise ValueError(f"{case_id}: {profile} manifest identity mismatch")
        if current.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
            raise ValueError(f"{case_id}: {profile} manifest Layer 3 format mismatch")
        current_input = current.get("authoritative_build_inputs")
        if not isinstance(current_input, dict) or not current_input.get("sha256"):
            raise ValueError(f"{case_id}: {profile} manifest lacks build input")
        if expected_input is None:
            expected_input = current_input
        elif current_input != expected_input:
            raise ValueError(f"{case_id}: manifest authoritative inputs disagree")
        manifest_bindings[profile] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "authoritative_build_inputs": current_input,
        }
    assert expected_input is not None

    primary = str(step.get("primary_skill") or "")
    if not primary:
        raise ValueError(f"{case_id}: dispatch {step_index} lacks Professional Skill")
    hosts = ("codex", "claude", "copilot")
    host_profiles = {
        "codex": subject_root
        / "dist/codex/project/.codex/agents/main-control-agent.toml",
        "claude": subject_root
        / "dist/claude/project/.claude/agents/main-control-agent.md",
        "copilot": subject_root
        / "dist/copilot/project/.github/agents/main-control-agent.agent.md",
    }
    recommended = subject_root / "dist/universal/skills/recommended"
    router_path = recommended / (
        "engineering-control-plane/references/professional-skill-router.md"
    )
    router_authority = _professional_router_authority(router_path)
    selector_path = recommended / (
        f"engineering-control-plane/references/selectors/{primary}.json"
    )
    selector: dict[str, Any] | None = None
    selector_resolution: dict[str, Any] | None = None
    selector_asset_specs: list[tuple[str, Path, str]] = []
    reference_partitions: dict[str, dict[str, Any]] = {}
    reference_partition_paths: dict[str, Path] = {}
    exact_references, exact_reference_bindings = (
        _trajectory_exact_reference_selection(step, subject_root)
    )
    effective = step.get("layer3_skills")
    assert isinstance(effective, list)
    if router_authority["schema"] == "split-professional-selector/v1":
        try:
            selector_raw = selector_path.read_bytes()
            selector_document = json.loads(selector_raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{case_id}: dispatch {step_index} professional-selector authority is missing"
            ) from exc
        if (
            isinstance(selector_document, dict)
            and selector_document.get("contract")
            == "changeforge.layer3-selector-decision-envelope/v1"
        ):
            decision_context = _native_selector_decision_context(
                case_id,
                step,
                subject_root,
                router_authority,
            )
            exact_bindings = [
                row
                for row in selector_document.get("decisions", [])
                if isinstance(row, dict)
                and row.get("runtime_key") == decision_context["runtime_key"]
            ]
            selected_binding = (
                exact_bindings[0]
                if exact_bindings
                else selector_document.get("complete")
            )
            if (
                not isinstance(selected_binding, dict)
                or not isinstance(selected_binding.get("path"), str)
                or not selected_binding["path"]
            ):
                raise ValueError("Professional selector decision binding is malformed")
            selected_path = selector_path.parent / selected_binding["path"]
            try:
                selected_document = json.loads(
                    selected_path.read_text(encoding="utf-8")
                )
                resolved = layer3_selector_resolve_control_projection(
                    selector_document,
                    {selected_binding["path"]: selected_document},
                    runtime_key=decision_context["runtime_key"],
                )
            except (OSError, json.JSONDecodeError, ValidationProblem) as exc:
                raise ValueError(
                    "Professional selector decision resolution failed closed"
                ) from exc
            if (
                resolved["selection_kind"] == "exact"
                and resolved["selected_layer3"] != effective
            ):
                raise ValueError(
                    "Professional selector decision output disagrees with dispatch"
                )
            provenance = resolved.get("provenance")
            if resolved["selection_kind"] == "exact" and (
                not isinstance(provenance, dict)
                or provenance.get("release_scenario")
                != decision_context["source_authorities"]["release_scenario"]
                or provenance.get("selector_registry")
                != decision_context["source_authorities"]["selector_registry"]
            ):
                raise ValueError(
                    "Professional selector decision provenance disagrees with source"
                )
            selector = resolved["projection"]
            selector_resolution = {
                key: copy.deepcopy(resolved[key])
                for key in (
                    "selection_kind",
                    "decision_id",
                    "path",
                    "sha256",
                    "runtime_key",
                    "provenance",
                    "selected_layer3",
                )
            }
            selector_resolution["source_authorities"] = copy.deepcopy(
                decision_context["source_authorities"]
            )
            selector_asset_specs = [
                ("professional-selector-envelope", selector_path, "selector-envelope"),
                (
                    (
                        "professional-selector-decision"
                        if resolved["selection_kind"] == "exact"
                        else "professional-selector-complete"
                    ),
                    selected_path,
                    f"selector-{resolved['selection_kind']}",
                ),
            ]
        else:
            selector = selector_document
            selector_asset_specs = [
                ("professional-selector", selector_path, "professional-selector")
            ]
        if exact_references is None:
            owners = [primary, *effective]
            if len(owners) > 4 or len(owners) != len(set(owners)):
                raise ValueError(
                    f"{case_id}: dispatch {step_index} Reference partition owners exceed the bounded route"
                )
            for owner in owners:
                path = recommended / (
                    "engineering-control-plane/references/reference-records/"
                    f"{primary}/{owner}.json"
                )
                try:
                    reference_partitions[owner] = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"{case_id}: dispatch {step_index} Reference partition authority is missing"
                    ) from exc
                reference_partition_paths[owner] = path
    pointer = envelope_pointer or f"fixture:{case_id}:step:{step_index}:selector"
    envelope_sha = envelope_sha256 or _sha256_text(_canonical_json_text(step))
    authority_step = step
    if router_authority["schema"] == "combined-router/v1":
        authority_step = {
            **step,
            **_native_combined_dispatch_binding(
                case_id,
                step_index,
                step,
                subject_root,
                router_authority,
            ),
        }
    authority_bundle = _selection_authority_bundle(
        schema=router_authority["schema"],
        router_rows=router_authority["rows"],
        step=authority_step,
        selector=selector,
        selector_resolution=selector_resolution,
        reference_partitions=(reference_partitions or None),
        exact_references=exact_references,
        exact_reference_bindings=exact_reference_bindings,
        envelope_pointer=pointer,
        envelope_sha256=envelope_sha,
        selection_owner=selection_owner,
    )
    if loaded_assignment_keys is None:
        loaded_assignment_keys = set()
    if global_router_loaded_hosts is None:
        global_router_loaded_hosts = set()
    capsule = step.get("fixture_capsule") or step.get("utility_capsule")
    assignment = None
    if isinstance(capsule, dict):
        assignment = next(
            (
                str(capsule[field])
                for field in (
                    "task_id",
                    "review_round_id",
                    "analysis_id",
                    "canonical_sha256",
                )
                if isinstance(capsule.get(field), str) and capsule[field]
            ),
            None,
        )
    assignment = assignment or f"{case_id}:dispatch:{step_index}"
    assignment_prefix = (
        case_id,
        assignment,
        str(step.get("profile") or ""),
        primary,
        selection_owner,
    )
    components: list[dict[str, Any]] = []
    component_tokens = {
        "always_loaded": 0,
        "selector": 0,
        "reference_partition": 0,
    }
    for host in hosts:
        assets: list[tuple[str, str, Path, tuple[str, ...]]] = []
        if selection_owner == "main-control-agent" and host not in global_router_loaded_hosts:
            assets.extend(
                [
                    (
                        "main-profile",
                        "always_loaded",
                        host_profiles[host],
                        (case_id, host, "initial-main-profile"),
                    ),
                    (
                        "control-owner",
                        "always_loaded",
                        recommended / "engineering-control-plane/SKILL.md",
                        (case_id, host, "initial-control-owner"),
                    ),
                    (
                        "global-professional-router",
                        "selector",
                        router_path,
                        (case_id, host, "initial-global-router"),
                    ),
                ]
            )
            global_router_loaded_hosts.add(host)
        for selector_kind, physical_path, key_suffix in selector_asset_specs:
            selector_key = (*assignment_prefix, host, key_suffix)
            if (
                selector is not None
                and selection_owner == "main-control-agent"
                and selector_key not in loaded_assignment_keys
            ):
                assets.append(
                    (selector_kind, "selector", physical_path, selector_key)
                )
                loaded_assignment_keys.add(selector_key)
        for owner, path in reference_partition_paths.items():
            partition_key = (*assignment_prefix, host, "reference-partition", owner)
            if partition_key in loaded_assignment_keys:
                continue
            assets.append(
                ("reference-records-partition", "reference_partition", path, partition_key)
            )
            loaded_assignment_keys.add(partition_key)
        for kind, bucket, path, asset_key in assets:
            if not path.is_file() or path.is_symlink():
                raise ValueError(
                    f"{case_id}: dispatch {step_index} {host} {kind} authority is missing"
                )
            raw = path.read_bytes()
            sha256 = hashlib.sha256(raw).hexdigest()
            if kind == "main-profile":
                for profile in BUILD_PROFILES:
                    expected_sha = manifests[profile].get(
                        "agent_profile_sha256", {}
                    ).get(host, {}).get("main-control-agent")
                    if expected_sha != sha256:
                        raise ValueError(
                            f"{case_id}: {host} main-profile manifest binding mismatch"
                        )
            tokens = count_o200k_base_tokens(raw.decode("utf-8"))
            component_tokens[bucket] += tokens
            components.append(
                {
                    "host": host,
                    "kind": kind,
                    "bucket": bucket,
                    "physical_path": path.relative_to(subject_root).as_posix(),
                    "sha256": sha256,
                    "tokens": tokens,
                    "load_count": 1,
                    "content_scope": "complete-native-bytes",
                    "assignment_key": "/".join(asset_key),
                }
            )
    _validate_selection_asset_occurrences(components)
    return {
        **authority_bundle,
        "selector_resolution": (
            selector_resolution["selection_kind"]
            if selector_resolution is not None
            else "complete-legacy"
        ),
        "professional_selector_decision_path": (
            selector_resolution["path"]
            if selector_resolution is not None
            else selector_path.relative_to(subject_root).as_posix()
        ),
        "host_order": list(hosts),
        "physical_selector_kinds": sorted(
            {row["kind"] for row in components if row["bucket"] == "selector"}
        ),
        "components": components,
        "component_tokens": component_tokens,
        "selector_load_count": sum(
            row["load_count"] for row in components if row["bucket"] == "selector"
        ),
        "reference_partition_load_count": sum(
            row["load_count"]
            for row in components
            if row["bucket"] == "reference_partition"
        ),
        "manifest_bindings": manifest_bindings,
        "authoritative_build_inputs": expected_input,
        "authority": {
            "router": {
                "path": router_path.relative_to(subject_root).as_posix(),
                "sha256": router_authority["sha256"],
                "header": router_authority["header"],
            },
            "professional_selector": (
                {
                    "path": selector_path.relative_to(subject_root).as_posix(),
                    "sha256": hashlib.sha256(selector_path.read_bytes()).hexdigest(),
                    "pointer": authority_bundle["professional_selector_pointer"],
                }
                if selector is not None
                else None
            ),
            "professional_selector_assets": [
                {
                    "kind": kind,
                    "path": path.relative_to(subject_root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for kind, path, _key in selector_asset_specs
            ],
            "reference_partitions": [
                {
                    "owner_skill": owner,
                    "path": path.relative_to(subject_root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "pointer": pointer,
                }
                for owner, path, pointer in zip(
                    reference_partition_paths,
                    reference_partition_paths.values(),
                    authority_bundle["reference_partition_pointers"],
                    strict=True,
                )
            ],
        },
    }


def _native_trajectory_case_cost(
    case: dict[str, Any],
    subject_root: Path,
    manifests: dict[str, dict[str, Any]],
    lightweight_module: Any,
    *,
    native_schema: dict[str, Any],
    host: str,
) -> dict[str, Any]:
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("native trajectory case has no id")
    if host not in FOCUS_PROFILE_HOSTS:
        raise ValueError(f"{case_id}: native trajectory host binding is invalid")
    steps = case.get("steps")
    if not isinstance(steps, list):
        raise ValueError(f"{case_id}: native trajectory steps are missing")
    metrics = lightweight_module._native_structural_metrics(case)
    components = {name: 0 for name in END_TO_END_COMPONENTS}
    component_sources: list[dict[str, Any]] = []
    manifest_bindings: dict[str, Any] | None = None
    authoritative_build_inputs: dict[str, Any] | None = None
    selector_asset_load_count = 0
    reference_partition_load_count = 0
    envelope_count = 0
    selection_authority_bundles: list[dict[str, Any]] = []
    selection_asset_component_tokens = {
        "always_loaded": 0,
        "selector": 0,
        "reference_partition": 0,
    }
    loaded_assignment_keys: set[tuple[str, ...]] = set()
    global_router_loaded_hosts: set[str] = set()
    accepted_brief_seen = False

    def add_file(bucket: str, kind: str, path: Path) -> None:
        if not path.is_file() or _uses_symlink(
            path, subject_root
        ):
            raise ValueError(
                f"{case_id}: missing complete native {kind} component "
                f"{path.relative_to(subject_root)}"
            )
        raw = path.read_bytes()
        tokens = count_o200k_base_tokens(raw.decode("utf-8"))
        components[bucket] += tokens
        component_sources.append(
            {
                "host": host,
                "kind": kind,
                "bucket": bucket,
                "physical_path": path.relative_to(subject_root).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "tokens": tokens,
                "load_count": 1,
                "content_scope": "complete-native-bytes",
            }
        )

    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not step.get("action"):
            raise ValueError(f"{case_id}: malformed native step {index}")
        if (
            step.get("action") == "first_executable_slice"
            and step.get("brief_status") == "accepted"
        ):
            accepted_brief_seen = True
        if step.get("action") != "dispatch":
            continue
        selector, instructions = lightweight_module._minimal_dispatch_partition(step)
        selector_text = _canonical_json_text(selector)
        instruction_text = _canonical_json_text(instructions)
        selector_tokens = count_o200k_base_tokens(selector_text)
        components["cross_agent_transfer"] += selector_tokens
        envelope_count += 1
        components["dispatch_instructions"] += count_o200k_base_tokens(
            instruction_text
        )
        component_sources.extend(
            [
                {
                    "host": host,
                    "kind": "native-selector-envelope",
                    "bucket": "cross_agent_transfer",
                    "physical_path": f"fixture:{case_id}:step:{index}:selector",
                    "sha256": _sha256_text(selector_text),
                    "tokens": selector_tokens,
                    "load_count": 1,
                    "content_scope": "complete-native-dispatch-partition",
                },
                {
                    "host": host,
                    "kind": "native-dispatch-instructions",
                    "bucket": "dispatch_instructions",
                    "physical_path": f"fixture:{case_id}:step:{index}:capsule",
                    "sha256": _sha256_text(instruction_text),
                    "tokens": count_o200k_base_tokens(instruction_text),
                    "load_count": 1,
                    "content_scope": "complete-native-dispatch-partition",
                },
            ]
        )
        role = str(step["profile"])
        worker_path = _profile_path(host, role)
        add_file("always_loaded", "worker-profile", worker_path)
        worker_sha256 = hashlib.sha256(worker_path.read_bytes()).hexdigest()
        if any(
            manifest.get("agent_profile_sha256", {}).get(host, {}).get(role)
            != worker_sha256
            for manifest in manifests.values()
        ):
            raise ValueError(
                f"{case_id}: {host}/{role} worker Profile manifest binding mismatch"
            )
        primary = str(step.get("primary_skill") or "")
        if primary:
            assets = _native_dispatch_selection_assets(
                case_id,
                index,
                step,
                subject_root,
                manifests,
                envelope_pointer=f"fixture:{case_id}:step:{index}:selector",
                envelope_sha256=_sha256_text(selector_text),
                selection_owner=(
                    "engineering-brief"
                    if accepted_brief_seen
                    and step.get("profile") in {"task-agent", "review-agent"}
                    else "main-control-agent"
                ),
                loaded_assignment_keys=loaded_assignment_keys,
                global_router_loaded_hosts=global_router_loaded_hosts,
            )
            host_assets = [
                item for item in assets["components"] if item.get("host") == host
            ]
            for item in host_assets:
                bucket = str(item["bucket"])
                tokens = int(item["tokens"]) * int(item["load_count"])
                components[bucket] += tokens
                selection_asset_component_tokens[bucket] += tokens
            component_sources.extend(host_assets)
            selector_asset_load_count += sum(
                int(item["load_count"])
                for item in host_assets
                if item["bucket"] == "selector"
            )
            reference_partition_load_count += sum(
                int(item["load_count"])
                for item in host_assets
                if item["bucket"] == "reference_partition"
            )
            selection_authority_bundles.append(
                {
                    "host": host,
                    **{
                        key: assets[key]
                        for key in (
                            "schema",
                            "authority",
                            "router_pointers",
                            "router_declared_layer3",
                            "professional_selector_pointer",
                            "selection_owner",
                            "professional_selector_declared_layer3",
                            "reference_partitions_loaded",
                            "reference_partition_pointers",
                            "native_envelope",
                            "handoff_augmentation",
                            "effective_ordered_layer3",
                            "manifest_bindings",
                            "authoritative_build_inputs",
                        )
                    },
                    "professional_selector_resolution": copy.deepcopy(
                        assets.get("professional_selector_resolution")
                    ),
                    "professional_selector_receipt": copy.deepcopy(
                        assets.get("professional_selector_receipt")
                    ),
                }
            )
            if manifest_bindings is None:
                manifest_bindings = assets["manifest_bindings"]
                authoritative_build_inputs = assets["authoritative_build_inputs"]
            elif (
                manifest_bindings != assets["manifest_bindings"]
                or authoritative_build_inputs != assets["authoritative_build_inputs"]
            ):
                raise ValueError(f"{case_id}: dispatch asset bindings disagree")
            add_file(
                "professional",
                "professional-skill",
                DIST_SKILLS / "recommended" / primary / "SKILL.md",
            )
        for reference in step.get("professional_references", []):
            add_file(
                "targeted_reference",
                "professional-reference",
                _professional_reference_path(
                    "recommended", primary, str(reference)
                ),
            )
        for name in step.get("layer3_skills", []):
            add_file(
                "layer3",
                "layer3-skill",
                _layer3_path(
                    "recommended", primary, str(name), manifests["recommended"]
                ),
            )
        for logical_id in step.get("layer3_references", []):
            add_file(
                "targeted_reference",
                "layer3-reference",
                _layer3_reference_path(
                    "recommended", primary, str(logical_id), manifests["recommended"]
                ),
            )

    transfer = _native_transfer_measurement(case, lightweight_module)
    components["cross_agent_transfer"] += transfer["gross_tokens"]
    handoff_tokens = transfer["handoff_tokens"]
    route, raw_route = _route_obligations(case, subject_root)
    case_text = _canonical_json_text(case)
    return {
        "id": f"{case_id}::{host}",
        "logical_case_id": case_id,
        "host": host,
        "mapping_state": "raw-route-equal-pending-subject-comparison",
        "route_obligations": route,
        "raw_route_obligations": raw_route,
        "native_reference_bindings": _case_native_reference_bindings(
            case, subject_root
        ),
        "component_tokens": components,
        "structural": {
            **metrics,
            "selector_load_count": selector_asset_load_count,
            "reference_partition_load_count": reference_partition_load_count,
            "envelope_count": envelope_count,
            "reference_tokens": components["targeted_reference"],
            "handoff_tokens": handoff_tokens,
        },
        "total_task_tokens": sum(components.values()),
        "native_schema": native_schema,
        "native_sources": {
            "fixture_case_sha256": _sha256_text(case_text),
            "fixture_case_tokens": count_o200k_base_tokens(case_text),
            "content_scope": "complete-native-case",
            "components": component_sources,
            "handoffs": [
                {**item, "host": host} for item in transfer["handoff_rows"]
            ],
            "selection_asset_manifest_bindings": manifest_bindings or {},
            "selection_asset_authoritative_build_inputs": (
                authoritative_build_inputs or {}
            ),
            "selection_authority_bundles": selection_authority_bundles,
            "selection_asset_component_tokens": selection_asset_component_tokens,
        },
    }


def _build_isolated_subject(subject_root: Path) -> None:
    for profile in BUILD_PROFILES:
        _run_checked(
            ["python3", "scripts/build.py", "--profile", profile],
            cwd=subject_root,
        )


def _measure_isolated_subject(
    *,
    subject_root: Path,
    subject_fixtures: Path,
    focus_mapping: dict[str, Any],
    trajectory_mapping: dict[str, Any],
    subject: str,
    evaluator_path: Path,
    lightweight_evaluator_path: Path,
    reports_root: Path,
) -> dict[str, Any]:
    fixture_document = json.loads(subject_fixtures.read_text(encoding="utf-8"))
    if not isinstance(fixture_document, dict):
        raise ValueError(f"{subject} native fixture is not a mapping")
    native_schema = _native_contract_identity(fixture_document)
    snapshot = authoritative_build_input_snapshot(subject_root)
    manifests, manifest_errors = _manifest_input_identity(
        subject_root / "dist/universal/skills", snapshot
    )
    if manifest_errors:
        raise ValueError("; ".join(manifest_errors))
    lightweight_reports = reports_root / "native-lightweight"
    native_lightweight = subject_root / "scripts/eval-agent-lightweight.py"
    _run_checked(
        [
            "python3",
            str(native_lightweight),
            "--reports-dir",
            str(lightweight_reports),
        ],
        cwd=subject_root,
    )
    lightweight_path = lightweight_reports / "hookless-control-plane-eval.json"
    lightweight = json.loads(lightweight_path.read_text(encoding="utf-8"))
    _require_native_validator_report(
        lightweight,
        subject=subject,
        expected_fixture_schema=native_schema["fixture_schema_version"],
    )
    lightweight_module = _load_current_lightweight_module(
        lightweight_evaluator_path
    )
    fixture_cases = {
        str(case.get("id") or ""): case
        for _group, case in _fixture_cases(fixture_document)
    }
    if "" in fixture_cases:
        raise ValueError(f"{subject} native trajectory has a missing case id")
    subject_manifests = {
        profile: json.loads(
            (
                subject_root
                / "dist/universal/skills"
                / profile
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        for profile in BUILD_PROFILES
    }
    cases: list[dict[str, Any]] = []
    trajectory_rows = {
        str(row["canonical_id"]): row
        for row in trajectory_mapping.get("rows", [])
    }
    with _subject_configuration(subject_root, subject_fixtures, lightweight_path):
        for case_id in sorted(fixture_cases):
            row = trajectory_rows.get(case_id)
            if row is None:
                raise ValueError(
                    f"{subject} native trajectory {case_id} lacks canonical mapping"
                )
            for host in FOCUS_PROFILE_HOSTS:
                measured = _native_trajectory_case_cost(
                    fixture_cases[case_id],
                    subject_root,
                    subject_manifests,
                    lightweight_module,
                    native_schema=native_schema,
                    host=host,
                )
                measured["mapping_state"] = row["state"]
                measured["semantic_obligation"] = row["semantic_obligation"]
                cases.append(measured)
        rendered = evaluate() if subject == "candidate" else None
    native_focus_cases = {
        str(item.get("id")): item
        for item in fixture_document.get("task_focus_cases", [])
        if isinstance(item, dict) and item.get("id")
    }
    for row in focus_mapping.get("rows", []):
        native_id = str(row[f"{subject}_native_id"])
        if native_id not in native_focus_cases:
            raise ValueError(
                f"{subject} task-focus mapping lacks native case {native_id}"
            )
        for host in FOCUS_PROFILE_HOSTS:
            cases.append(
                _focus_case_cost(
                    row,
                    native_focus_cases[native_id],
                    subject_root,
                    subject=subject,
                    host=host,
                )
            )
            cases[-1]["native_schema"] = native_schema
    return {
        "identity": {
            "measurement_source": "isolated-built-subject",
            "evaluator_sha256": hashlib.sha256(evaluator_path.read_bytes()).hexdigest(),
            "lightweight_evaluator_sha256": hashlib.sha256(
                lightweight_evaluator_path.read_bytes()
            ).hexdigest(),
            "native_fixture_sha256": hashlib.sha256(
                subject_fixtures.read_bytes()
            ).hexdigest(),
            "native_schema": native_schema,
            "native_validator_sha256": hashlib.sha256(
                native_lightweight.read_bytes()
            ).hexdigest(),
            "canonical_corpus_digest": focus_mapping.get(
                "canonical_corpus_digest", focus_mapping["mapping_digest"]
            ),
            "tokenizer": "o200k_base",
            "source_commit": _git_text(subject_root, "rev-parse", "HEAD"),
            "authoritative_build_inputs": snapshot,
            "manifests": manifests,
            "logical_case_count": len(cases) // len(FOCUS_PROFILE_HOSTS),
            "host_pair_count": len(cases),
            "host_order": list(FOCUS_PROFILE_HOSTS),
        },
        "cases": cases,
        "lightweight_subject_status": lightweight.get("status"),
        "lightweight_subject_errors": lightweight.get("errors", []),
        "rendered_report": rendered,
    }


def evaluate_end_to_end_ab(
    *,
    baseline_ref: str,
    expected_baseline_commit: str | None = None,
) -> dict[str, Any]:
    repository_root = ROOT.resolve()
    evaluator_path = Path(__file__).resolve()
    lightweight_evaluator_path = repository_root / "scripts/eval-agent-lightweight.py"
    candidate_commit = _git_text(repository_root, "rev-parse", "HEAD")
    baseline_commit = _git_text(repository_root, "rev-parse", baseline_ref)
    if expected_baseline_commit and baseline_commit != expected_baseline_commit:
        raise ValueError(
            f"baseline ref moved: expected {expected_baseline_commit}, got {baseline_commit}"
        )
    changed_paths = {
        line
        for line in _git_text(repository_root, "diff", "--name-only", "HEAD").splitlines()
        if line
    }
    untracked = {
        line
        for line in _git_text(
            repository_root, "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        if line
    }
    unexpected = sorted((changed_paths | untracked) - AB_ALLOWED_WRITE_PATHS)
    if unexpected:
        raise ValueError(f"A/B candidate contains out-of-scope paths: {unexpected}")
    candidate_patch = _run_checked(
        ["git", "diff", "--binary", "HEAD"], cwd=repository_root
    ).stdout
    with tempfile.TemporaryDirectory(
        prefix="changeforge-token-ab-", dir="/private/tmp"
    ) as raw:
        workspace = Path(raw)
        baseline_root = workspace / "baseline"
        candidate_root = workspace / "candidate"
        added: list[Path] = []
        try:
            for root, commit in (
                (baseline_root, baseline_commit),
                (candidate_root, candidate_commit),
            ):
                _run_checked(
                    ["git", "worktree", "add", "--detach", str(root), commit],
                    cwd=repository_root,
                )
                added.append(root)
            if candidate_patch:
                _run_checked(
                    ["git", "apply", "--binary", "-"],
                    cwd=candidate_root,
                    input_bytes=candidate_patch,
                )
            _validate_candidate_changed_paths(candidate_root, changed_paths)
            _stage_allowed_untracked_inputs(
                repository_root,
                candidate_root,
                untracked,
            )
            _validate_candidate_changed_paths(
                candidate_root, changed_paths | untracked
            )
            baseline_document = json.loads(
                (baseline_root / "evals/agent-light-trajectories/cases.yaml").read_text(
                    encoding="utf-8"
                )
            )
            candidate_document = json.loads(
                (candidate_root / "evals/agent-light-trajectories/cases.yaml").read_text(
                    encoding="utf-8"
                )
            )
            focus_mapping = _canonical_focus_mapping(
                candidate_document, baseline_document
            )
            if focus_mapping["errors"]:
                raise ValueError("; ".join(focus_mapping["errors"]))
            trajectory_mapping = _canonical_trajectory_mapping(
                candidate_document,
                baseline_document,
                candidate_root=candidate_root,
                baseline_root=baseline_root,
            )
            if trajectory_mapping["errors"]:
                raise ValueError("; ".join(trajectory_mapping["errors"]))
            baseline_fixtures = (
                baseline_root / "evals/agent-light-trajectories/cases.yaml"
            )
            candidate_fixtures = (
                candidate_root / "evals/agent-light-trajectories/cases.yaml"
            )
            baseline_native_fixture_sha256 = hashlib.sha256(
                (baseline_root / "evals/agent-light-trajectories/cases.yaml").read_bytes()
            ).hexdigest()
            candidate_native_fixture_sha256 = hashlib.sha256(
                (candidate_root / "evals/agent-light-trajectories/cases.yaml").read_bytes()
            ).hexdigest()
            focus_mapping["canonical_corpus_digest"] = hashlib.sha256(
                json.dumps(
                    {
                        "focus_mapping_digest": focus_mapping["mapping_digest"],
                        "trajectory_mapping_digest": trajectory_mapping[
                            "mapping_digest"
                        ],
                        "baseline_native_fixture_sha256": baseline_native_fixture_sha256,
                        "candidate_native_fixture_sha256": candidate_native_fixture_sha256,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            _build_isolated_subject(baseline_root)
            _build_isolated_subject(candidate_root)
            baseline = _measure_isolated_subject(
                subject_root=baseline_root,
                subject_fixtures=baseline_fixtures,
                focus_mapping=focus_mapping,
                trajectory_mapping=trajectory_mapping,
                subject="baseline",
                evaluator_path=evaluator_path,
                lightweight_evaluator_path=lightweight_evaluator_path,
                reports_root=workspace / "baseline-reports",
            )
            candidate = _measure_isolated_subject(
                subject_root=candidate_root,
                subject_fixtures=candidate_fixtures,
                focus_mapping=focus_mapping,
                trajectory_mapping=trajectory_mapping,
                subject="candidate",
                evaluator_path=evaluator_path,
                lightweight_evaluator_path=lightweight_evaluator_path,
                reports_root=workspace / "candidate-reports",
            )
            comparison = _compare_end_to_end_subjects(baseline, candidate)
            behavior_evidence, codegen_evidence = _candidate_quality_evidence(
                candidate_root,
                workspace,
            )
            comparison["quality_cost_gate"] = _quality_first_cost_gate(
                behavior_evidence=behavior_evidence,
                codegen_evidence=codegen_evidence,
                cost_comparison=comparison,
            )
            comparison["fixed_baseline_ref"] = baseline_ref
            comparison["fixed_baseline_commit"] = baseline_commit
            comparison["candidate_start_commit"] = candidate_commit
            comparison["candidate_changed_paths"] = sorted(changed_paths | untracked)
            comparison["canonical_corpus"] = {
                "focus_mapping_digest": focus_mapping["mapping_digest"],
                "trajectory_mapping_digest": trajectory_mapping[
                    "mapping_digest"
                ],
                "canonical_corpus_digest": focus_mapping[
                    "canonical_corpus_digest"
                ],
                "task_focus_mapping_row_count": len(focus_mapping["rows"]),
                "task_focus_mapping_rows": focus_mapping["rows"],
                "trajectory_mapping_row_count": len(trajectory_mapping["rows"]),
                "trajectory_mapping_rows": trajectory_mapping["rows"],
                "total_case_count": (
                    len(focus_mapping["rows"]) + len(trajectory_mapping["rows"])
                ),
                "baseline_native_fixture_sha256": baseline_native_fixture_sha256,
                "candidate_native_fixture_sha256": candidate_native_fixture_sha256,
            }
            expected_logical_cases = comparison["canonical_corpus"][
                "total_case_count"
            ]
            expected_host_pairs = expected_logical_cases * len(FOCUS_PROFILE_HOSTS)
            matrix = comparison.get("host_matrix")
            if not isinstance(matrix, dict) or (
                matrix.get("logical_case_count") != expected_logical_cases
                or matrix.get("host_pair_count") != expected_host_pairs
                or matrix.get("host_order") != list(FOCUS_PROFILE_HOSTS)
            ):
                comparison["errors"].append(
                    "end-to-end host matrix does not bind every canonical case"
                )
            comparison["_candidate_rendered_report"] = candidate["rendered_report"]
            if baseline.get("lightweight_subject_errors"):
                comparison["errors"].append("baseline lightweight subject is invalid")
            if candidate.get("lightweight_subject_errors"):
                comparison["errors"].append("candidate lightweight subject is invalid")
            if comparison["quality_cost_gate"]["status"] != "pass":
                comparison["errors"].extend(
                    comparison["quality_cost_gate"]["errors"]
                )
            comparison["status"] = "pass" if not comparison["errors"] else "fail"
        finally:
            for root in reversed(added):
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(root)],
                    cwd=repository_root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
        if _git_text(repository_root, "rev-parse", baseline_ref) != baseline_commit:
            raise RuntimeError("baseline ref moved after measurement")
        return comparison


def _markdown_h2_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    name = "preamble"
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            sections.append((name, "".join(lines)))
            name = line[3:].strip()
            lines = [line]
        else:
            lines.append(line)
    sections.append((name, "".join(lines)))
    return [(section, body) for section, body in sections if body]


def _template_measurement(
    path: Path,
    compactable_sections: frozenset[str],
) -> tuple[int, int, int, str]:
    text = path.read_text(encoding="utf-8")
    sections = _markdown_h2_sections(text)
    gross = sum(count_o200k_base_tokens(body) for _name, body in sections)
    compressible = sum(
        count_o200k_base_tokens(body)
        for name, body in sections
        if name in compactable_sections
    )
    return gross, gross - compressible, compressible, text


def _empty_transfer_categories() -> dict[str, dict[str, Any]]:
    return {
        category: {
            "label": TRANSFER_CATEGORY_LABELS[category],
            "accounting_role": (
                "exclusive-denominator"
                if category in TRANSFER_EXCLUSIVE_CATEGORIES
                else "overlap-view"
            ),
            "gross_tokens": 0,
            "non_compressible_tokens": 0,
            "compressible_tokens": 0,
            "occurrence_count": 0,
            "source_selectors": set(),
        }
        for category in TRANSFER_CATEGORY_ORDER
    }


def _add_transfer_measurement(
    categories: dict[str, dict[str, Any]],
    category: str,
    *,
    gross: int,
    non_compressible: int,
    compressible: int,
    source: str,
) -> None:
    if min(gross, non_compressible, compressible) < 0:
        raise ValueError(f"negative transferred-context measurement for {category}")
    if category in TRANSFER_EXCLUSIVE_CATEGORIES and gross != (
        non_compressible + compressible
    ):
        raise ValueError(f"non-exclusive token partition for {category}")
    entry = categories[category]
    entry["gross_tokens"] += gross
    entry["non_compressible_tokens"] += non_compressible
    entry["compressible_tokens"] += compressible
    entry["occurrence_count"] += 1
    entry["source_selectors"].add(source)


def _current_blocking_review_window(
    steps: list[Any], index: int
) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    review_index = next(
        (
            candidate_index
            for candidate_index in range(index - 1, -1, -1)
            if isinstance(steps[candidate_index], dict)
            and steps[candidate_index].get("action") == "review-discipline"
        ),
        None,
    )
    if review_index is None:
        return None
    review = steps[review_index]
    if review.get("verdict") != "findings":
        return None
    dispatch = steps[index] if isinstance(steps[index], dict) else {}
    capsule = dispatch.get("fixture_capsule")
    repair_task_id = capsule.get("task_id") if isinstance(capsule, dict) else None
    closing_review = next(
        (
            step
            for step in reversed(steps[review_index + 1 : index])
            if isinstance(step, dict)
            and step.get("actor") == "review-agent"
            and step.get("action") in REVIEW_ROUND_COMPLETION_ACTIONS
        ),
        None,
    )
    review_round_id = (
        closing_review.get("review_round_id")
        if isinstance(closing_review, dict)
        else None
    )
    round_aware_findings = [
        step
        for step in steps[review_index + 1 : index]
        if isinstance(step, dict)
        and step.get("action") == "finding"
        and step.get("review_round_id") is not None
    ]
    covered_task_ids = (
        closing_review.get("covered_task_ids", [])
        if isinstance(closing_review, dict)
        else []
    )
    closes_repair_task = (
        isinstance(closing_review, dict)
        and closing_review.get("task_id") == repair_task_id
    ) or (
        isinstance(covered_task_ids, list)
        and repair_task_id in covered_task_ids
    )
    initial_completion_is_complete = (
        isinstance(closing_review, dict)
        and closing_review.get("action") == "review"
        and all(
            closing_review.get(field) is True
            for field in (
                "required_changed_scope_complete",
                "base_dimensions_complete",
                "professional_risk_dimensions_complete",
            )
        )
    )
    focused_rereview_is_complete = (
        isinstance(closing_review, dict)
        and closing_review.get("action") == "re-review"
        and closing_review.get("rereview_checks")
        == REVIEW_DISCIPLINE_MODEL["repair_invalidation_policy"]["rereview_focus"]
        and closing_review.get("rereview_scope_expanded") is False
        and closing_review.get("frozen_boundary_status")
        in {"preserved", "violation", "invalidated"}
        and closing_review.get("frozen_professional_risk_boundary_status")
        == "preserved"
    )
    if (
        not round_aware_findings
        or not isinstance(closing_review, dict)
        or not isinstance(review_round_id, str)
        or not review_round_id
        or not closes_repair_task
        or not (initial_completion_is_complete or focused_rereview_is_complete)
    ):
        return None
    blockers = [
        step
        for step in steps[review_index + 1 : index]
        if isinstance(step, dict)
        and step.get("action") == "finding"
        and step.get("relation") == "current-task"
        and step.get("material") is True
        and (
            step.get("task_id") == repair_task_id
            and step.get("review_round_id") == review_round_id
        )
    ]
    if closing_review.get("finding_ids") != [
        step.get("evidence_id")
        for step in round_aware_findings
        if step.get("review_round_id") == review_round_id
    ]:
        return None
    return (review, blockers) if blockers else None


def _is_repair_dispatch(steps: list[Any], index: int) -> bool:
    return _current_blocking_review_window(steps, index) is not None


def _contains_raw_log(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in _RAW_LOG_FIELDS or _contains_raw_log(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_raw_log(item) for item in value)
    return False


def _current_evidence_errors(value: Any, *, context: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{context}: current_evidence must be a list"]
    errors: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or item.get("state") != "current":
            errors.append(f"{context}: current_evidence[{index}] must have state=current")
        elif not item.get("claim"):
            errors.append(f"{context}: current_evidence[{index}] needs a claim")
    return errors


def _nonempty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(value) == len(set(value))
    )


def _transfer_projection_errors(boundary: str, projection: Any) -> list[str]:
    """Validate only the lossy transfer boundary, never orchestration semantics."""

    expected = TRANSFER_PROJECTION_FIELDS.get(boundary)
    if expected is None:
        return [f"unknown transfer boundary {boundary!r}"]
    if not isinstance(projection, dict):
        return [f"{boundary}: projection must be an object"]
    errors: list[str] = []
    if tuple(projection) != expected:
        errors.append(f"{boundary}: fields must be exactly {list(expected)}")
    if _contains_raw_log(projection):
        errors.append(f"{boundary}: raw command logs are JIT-only")
    if boundary == "task_to_implementation":
        diff = projection.get("actual_diff")
        if not isinstance(diff, dict) or diff.get("kind") not in {
            "actual-diff",
            "accessible-diff-reference",
        } or not diff.get("artifact"):
            errors.append(f"{boundary}: actual_diff needs an actual or accessible artifact")
        validation = projection.get("validation_result")
        if not isinstance(validation, dict) or not validation.get("result"):
            errors.append(f"{boundary}: validation_result must be structured")
        errors.extend(
            _current_evidence_errors(
                projection.get("current_evidence"), context=boundary
            )
        )
    elif boundary == "implementation_to_review":
        diff = projection.get("latest_diff")
        if not isinstance(diff, dict) or diff.get("kind") not in {
            "actual-diff",
            "accessible-diff-reference",
        } or not diff.get("artifact"):
            errors.append(f"{boundary}: latest_diff cannot be a changed-file summary")
        if not isinstance(projection.get("current_validation"), dict):
            errors.append(f"{boundary}: current_validation must be structured")
        for field in ("scope", "freshness", "proof_limit", "unverified_scope"):
            if field not in projection or projection[field] in (None, ""):
                errors.append(f"{boundary}: missing {field}")
        errors.extend(
            _current_evidence_errors(
                projection.get("current_evidence"), context=boundary
            )
        )
    else:
        batch_key = projection.get("repair_batch_key")
        if (
            not isinstance(batch_key, list)
            or len(batch_key) != 2
            or any(
                not isinstance(item, str) or not item.strip()
                for item in batch_key
            )
        ):
            errors.append(
                f"{boundary}: repair_batch_key must bind one Review Round and Task ID"
            )
            repair_task_id = None
        else:
            repair_task_id = batch_key[1]
        findings = projection.get("blocking_findings")
        if (
            not isinstance(findings, list)
            or not findings
            or any(
                not isinstance(item, dict)
                or tuple(item) != ("claim", "relation")
                or item.get("relation") != "current-task"
                for item in findings
            )
        ):
            errors.append(
                f"{boundary}: only material current-task findings may enter Repair with Finding Relation preserved"
            )
        obligations = projection.get("finding_obligations")
        obligation_fields = (
            "finding_id",
            "relation",
            "affected_scope",
            "acceptance_or_risk_impact",
            "required_validation",
            "required_covering_rereview",
        )
        if (
            not isinstance(obligations, list)
            or not obligations
            or any(
                not isinstance(item, dict)
                or tuple(item) != obligation_fields
                or item.get("relation") != "current-task"
                or not _nonempty_string_list(item.get("affected_scope"))
                or not isinstance(item.get("acceptance_or_risk_impact"), str)
                or not item["acceptance_or_risk_impact"].strip()
                or not _nonempty_string_list(item.get("required_validation"))
                or not isinstance(item.get("required_covering_rereview"), dict)
                or tuple(item["required_covering_rereview"])
                != ("covered_task_ids", "same_or_stronger")
                or item["required_covering_rereview"].get("covered_task_ids")
                != [repair_task_id]
                or item["required_covering_rereview"].get("same_or_stronger") is not True
                for item in obligations
            )
        ):
            errors.append(
                f"{boundary}: each Finding must preserve scope, impact, validation, and covering re-review obligations"
            )
        finding_claims = [
            item.get("claim") for item in findings or [] if isinstance(item, dict)
        ]
        obligation_ids = [
            item.get("finding_id")
            for item in obligations or []
            if isinstance(item, dict)
        ]
        if finding_claims != obligation_ids or len(obligation_ids) != len(
            set(obligation_ids)
        ):
            errors.append(
                f"{boundary}: one Repair must retain every same-task Finding exactly once"
            )
        diff = projection.get("latest_diff")
        if not isinstance(diff, dict) or diff.get("kind") not in {
            "actual-diff",
            "accessible-diff-reference",
        } or not diff.get("artifact"):
            errors.append(f"{boundary}: latest_diff needs an actual or accessible artifact")
        for field in ("invalidated_evidence", "reusable_evidence"):
            value = projection.get(field)
            if not isinstance(value, list):
                errors.append(f"{boundary}: {field} must be a list")
        invalidated = {
            item.get("claim")
            for item in projection.get("invalidated_evidence", [])
            if isinstance(item, dict)
        }
        reusable = {
            item.get("claim")
            for item in projection.get("reusable_evidence", [])
            if isinstance(item, dict)
        }
        if invalidated & reusable:
            errors.append(f"{boundary}: evidence cannot be both invalidated and reusable")
    return errors


def _transfer_reference_id(source: str) -> str:
    """Return the source-local identifier carried across a transfer boundary."""

    marker = "#/"
    if marker not in source:
        raise ValueError("transfer source must contain a fixture-local selector")
    reference_id = source.rsplit(marker, 1)[1]
    if not reference_id or reference_id.startswith("/") or ".." in reference_id.split("/"):
        raise ValueError("transfer source has an unsafe fixture-local selector")
    return reference_id


def _compact_transfer_projection(
    boundary: str,
    projection: dict[str, Any],
    source: str,
) -> list[str]:
    """Bind one validated full projection to its JIT-loadable source owner."""

    errors = _transfer_projection_errors(boundary, projection)
    if errors:
        raise ValueError("; ".join(errors))
    text = _canonical_json_text(projection)
    return [_transfer_reference_id(source), _sha256_text(text)]


def _expand_transfer_projection(
    boundary: str,
    compact: Any,
) -> dict[str, Any]:
    """JIT-load and verify one source-owned transfer projection."""

    if (
        not isinstance(compact, list)
        or len(compact) != 2
        or any(not isinstance(item, str) or not item for item in compact)
        or not re.fullmatch(r"[0-9a-f]{64}", compact[1])
    ):
        raise ValueError("compact transfer projection must be [source-id, sha256]")
    reference_id, expected_sha256 = compact
    document = json.loads(FIXTURES.read_text(encoding="utf-8"))
    matches: list[dict[str, Any]] = []
    for _group, case in _fixture_cases(document):
        for candidate_boundary, projection, source in _case_transfer_projection_rows(
            case
        ):
            if (
                candidate_boundary == boundary
                and _transfer_reference_id(source) == reference_id
            ):
                matches.append(projection)
    if len(matches) != 1:
        raise ValueError(
            f"compact transfer projection must resolve once, found {len(matches)}"
        )
    projection = matches[0]
    actual_sha256 = _sha256_text(_canonical_json_text(projection))
    if actual_sha256 != expected_sha256:
        raise ValueError("compact transfer projection fingerprint mismatch")
    return projection


def _step_task_ids(step: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    task_id = step.get("task_id")
    if isinstance(task_id, str) and task_id:
        result.add(task_id)
    task_ids = step.get("task_ids")
    if isinstance(task_ids, list):
        result.update(item for item in task_ids if isinstance(item, str) and item)
    return result


def _task_bound_steps(
    steps: list[Any], start: int, task_id: str
) -> list[tuple[int, dict[str, Any]]]:
    end = next(
        (
            index
            for index, step in enumerate(steps[start + 1 :], start + 1)
            if isinstance(step, dict)
            and step.get("actor") == "task-agent"
            and step.get("action") == "implementation-handoff"
            and step.get("task_id") == task_id
        ),
        len(steps) - 1,
    )
    return [
        (index, step)
        for index, step in enumerate(steps[start + 1 : end + 1], start + 1)
        if isinstance(step, dict) and task_id in _step_task_ids(step)
    ]


def _next_review_discipline(
    steps: list[Any], start: int, task_id: str
) -> dict[str, Any] | None:
    for step in steps[start + 1 :]:
        if not isinstance(step, dict):
            continue
        if step.get("action") == "review-discipline" and step.get("task_id") == task_id:
            return step
    return None


def _diff_projection(
    case_id: str,
    steps: list[Any],
    start: int,
    task_id: str,
) -> dict[str, Any]:
    review = _next_review_discipline(steps, start, task_id)
    if review and isinstance(review.get("diff"), dict):
        return dict(review["diff"])
    changed = sorted(
        {
            str(step["path"])
            for _index, step in _task_bound_steps(steps, start, task_id)
            if step.get("action") in {"edit", "repair"}
            and isinstance(step.get("path"), str)
        }
    )
    return {
        "kind": "accessible-diff-reference",
        "artifact": f"{_relative(FIXTURES)}#/{case_id}/tasks/{task_id}",
        "generation": 1,
        "changed_files": changed,
    }


def _evidence_projection(
    steps: list[Any], start: int, task_id: str
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for _index, step in _task_bound_steps(steps, start, task_id):
        if step.get("action") == "adaptive-test-evidence" and step.get("freshness", 0) > 0:
            candidates.append(
                {
                    "claim": str(step.get("evidence_id")),
                    "state": "current",
                    "scope": task_id,
                    "freshness": step.get("freshness"),
                    "proof_limit": str(step.get("oracle") or "deterministic fixture oracle"),
                }
            )
        elif step.get("action") == "validate" and step.get("outcome") == "passed":
            candidates.append(
                {
                    "claim": str(step.get("evidence_id")),
                    "state": "current",
                    "scope": task_id,
                    "freshness": "after-latest-material-edit",
                    "proof_limit": "structured fixture result; raw log JIT-only",
                }
            )
    return candidates


def _case_transfer_projection_rows(case: dict[str, Any]) -> list[tuple[str, dict[str, Any], str]]:
    case_id = str(case["id"])
    steps = case["steps"]
    rows: list[tuple[str, dict[str, Any], str]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or step.get("action") != "dispatch":
            continue
        payload = step.get("fixture_capsule")
        if not isinstance(payload, dict):
            continue
        contract_type = payload.get("contract_type")
        task_id = str(payload.get("task_id") or "")
        if contract_type == "task":
            task_steps = _task_bound_steps(steps, index, task_id)
            diff = _diff_projection(case_id, steps, index, task_id)
            validations = [
                item for _step_index, item in task_steps if item.get("action") == "validate"
            ]
            validation = validations[-1] if validations else {}
            evidence = _evidence_projection(steps, index, task_id)
            execution = {
                "task_id": task_id,
                "status": "completed" if validation.get("outcome") == "passed" else "partial",
                "changed_files": diff.get("changed_files", []),
                "actual_diff": diff,
                "commands": [str(item.get("command")) for item in validations],
                "validation_result": {
                    "evidence_id": validation.get("evidence_id"),
                    "result": validation.get("outcome", "not-run"),
                },
                "freshness": diff.get("generation", 1),
                "current_evidence": evidence,
                "unverified_scope": [],
                "residual_risk": ["deterministic fixture proof only"],
            }
            rows.append(
                (
                    "task_to_implementation",
                    execution,
                    f"{_relative(IMPLEMENTATION_HANDOFF_TEMPLATE)}; {_relative(FIXTURES)}#/{case_id}/steps/{index}/tasks/{task_id}",
                )
            )
            repair_window = _current_blocking_review_window(steps, index)
            if repair_window is not None:
                prior_review, findings = repair_window
                for finding in findings:
                    dependent_scope = finding.get("dependent_scope", [])
                    if not isinstance(dependent_scope, list) or not all(
                        isinstance(item, str) and item for item in dependent_scope
                    ):
                        raise ValueError(
                            f"{case_id}: blocking finding dependent_scope must be "
                            "a string list"
                        )
                affected = sorted(
                    {
                        scope
                        for item in findings
                        for scope in (
                            [str(item["path"])]
                            if isinstance(item.get("path"), str)
                            else []
                        )
                        + [
                            str(dependent)
                            for dependent in item.get("dependent_scope", [])
                        ]
                    }
                )
                repair_task_id = payload.get("task_id")
                if not isinstance(repair_task_id, str) or not repair_task_id:
                    raise ValueError(
                        f"{case_id}: Repair projection requires one Task ID"
                    )
                for item in findings:
                    required_covering_rereview = item.get(
                        "required_covering_rereview"
                    )
                    if (
                        not isinstance(item.get("path"), str)
                        or not item["path"].strip()
                        or not _nonempty_string_list(
                            [item["path"], *item.get("dependent_scope", [])]
                        )
                        or not isinstance(item.get("acceptance_impact"), str)
                        or not item["acceptance_impact"].strip()
                        or not _nonempty_string_list(
                            item.get("required_validation")
                        )
                        or not isinstance(required_covering_rereview, dict)
                        or tuple(required_covering_rereview)
                        != ("covered_task_ids", "same_or_stronger")
                        or required_covering_rereview.get("covered_task_ids")
                        != [repair_task_id]
                        or required_covering_rereview.get("same_or_stronger")
                        is not True
                    ):
                        raise ValueError(
                            f"{case_id}: Repair projection per-finding obligations "
                            "must be explicit, non-empty, and bound to the Repair Task ID"
                        )
                review_round_ids = {
                    item.get("review_round_id") for item in findings
                }
                if len(review_round_ids) != 1 or not next(iter(review_round_ids)):
                    raise ValueError(
                        f"{case_id}: Repair projection requires one explicit Review Round ID"
                    )
                review_round_id = next(iter(review_round_ids))
                repair = {
                    "repair_batch_key": [review_round_id, repair_task_id],
                    "blocking_findings": [
                        {
                            "claim": item.get("evidence_id"),
                            "relation": item.get("relation"),
                        }
                        for item in findings
                    ],
                    "finding_obligations": [
                        {
                            "finding_id": item.get("evidence_id"),
                            "relation": item.get("relation"),
                            "affected_scope": [
                                item["path"], *item.get("dependent_scope", [])
                            ],
                            "acceptance_or_risk_impact": item.get(
                                "acceptance_impact"
                            ),
                            "required_validation": item["required_validation"],
                            "required_covering_rereview": item[
                                "required_covering_rereview"
                            ],
                        }
                        for item in findings
                    ],
                    "affected_scope": affected,
                    "acceptance_impact": [
                        item.get("acceptance_impact") for item in findings
                    ],
                    "latest_diff": dict(prior_review.get("diff", diff)),
                    "invalidated_evidence": [
                        {"claim": prior_review.get("validation", {}).get("evidence_id"), "scope": affected},
                        {"claim": "previous-diff-review", "scope": affected},
                    ],
                    "reusable_evidence": [
                        {"claim": "owner-placement-inspection", "scope": task_id, "state": "current"}
                    ],
                    "required_validation": payload.get("verification", []),
                    "required_rereview": {"required": True, "owner": payload.get("review_owner")},
                }
                repair_errors = _transfer_projection_errors(
                    "review_to_repair", repair
                )
                if repair_errors:
                    raise ValueError("; ".join(repair_errors))
                rows.append(
                    (
                        "review_to_repair",
                        repair,
                        f"{_relative(REVIEW_HANDOFF_TEMPLATE)}; {_relative(FIXTURES)}#/{case_id}/steps/{index}",
                    )
                )
        elif contract_type == "review":
            discipline = _next_review_discipline(steps, index, task_id) or {}
            latest_diff = dict(
                discipline.get("diff")
                or {
                    "kind": "accessible-diff-reference",
                    "artifact": f"{_relative(FIXTURES)}#/{case_id}/steps/{index}",
                    "generation": 0,
                    "changed_files": payload.get("scope", []),
                }
            )
            current_validation = dict(discipline.get("validation") or {"result": "unverified"})
            evidence_id = current_validation.get("evidence_id")
            current_evidence = (
                [
                    {
                        "claim": evidence_id,
                        "state": "current",
                        "scope": payload.get("scope", []),
                        "freshness": current_validation.get("generation", "current"),
                        "proof_limit": "structured fixture result; raw log JIT-only",
                    }
                ]
                if evidence_id
                else []
            )
            review = {
                "acceptance": payload.get("acceptance", []),
                "review_boundary": {
                    "task_id": task_id,
                    "review_kind": discipline.get("review_kind", "bounded-review"),
                },
                "effective_level": payload.get("execution_level_extension", {}).get("effective_level"),
                "required_review_skills": [
                    step.get("primary_skill"), *step.get("layer3_skills", [])
                ],
                "required_changed_scope": payload.get("scope", []),
                "latest_diff": latest_diff,
                "current_validation": current_validation,
                "current_evidence": current_evidence,
                "scope": payload.get("scope", []),
                "freshness": latest_diff.get("generation", 0),
                "proof_limit": payload.get("stop_conditions", []),
                "unverified_scope": [],
            }
            rows.append(
                (
                    "implementation_to_review",
                    review,
                    f"{_relative(REVIEW_HANDOFF_TEMPLATE)}; {_relative(FIXTURES)}#/{case_id}/steps/{index}",
                )
            )
    for boundary, projection, _source in rows:
        errors = _transfer_projection_errors(boundary, projection)
        if errors:
            raise ValueError("; ".join(errors))
    return rows


def _case_transfer_projections(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for boundary, projection, _source in _case_transfer_projection_rows(case):
        result[boundary] = projection
    return result


def _case_transfer_measurement(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case["id"])
    steps = case["steps"]
    categories = _empty_transfer_categories()
    duplicate_components: list[dict[str, Any]] = []
    projection_rows = _case_transfer_projection_rows(case)

    for index, step in enumerate(steps):
        if not isinstance(step, dict) or step.get("action") != "dispatch":
            continue
        selector = {
            key: step.get(key)
            for key in (
                "primary_skill",
                "professional_references",
                "layer3_skills",
                "layer3_references",
            )
            if key in step
        }
        if any(value not in (None, [], "") for value in selector.values()):
            selector_text = _canonical_json_text(selector)
            selector_tokens = count_o200k_base_tokens(selector_text)
            selector_source = f"{_relative(FIXTURES)}#/{case_id}/steps/{index}/skill-selectors"
            _add_transfer_measurement(
                categories,
                "skill_reference",
                gross=selector_tokens,
                non_compressible=selector_tokens,
                compressible=0,
                source=selector_source,
            )
            duplicate_components.append(
                _component("skill_reference", selector_source, selector_text)
            )

        payload = step.get("fixture_capsule")
        if not isinstance(payload, dict):
            continue
        contract_type = payload.get("contract_type")
        capsule_text = validate_and_render_fixture_capsule(step)
        capsule_tokens = count_o200k_base_tokens(capsule_text)
        capsule_source = f"{_relative(FIXTURES)}#/{case_id}/steps/{index}/fixture_capsule"
        if contract_type == "analysis":
            _add_transfer_measurement(
                categories,
                "authority",
                gross=capsule_tokens,
                non_compressible=capsule_tokens,
                compressible=0,
                source=capsule_source,
            )
            duplicate_components.append(
                _component("authority", capsule_source, capsule_text)
            )
        elif contract_type == "task":
            if _is_repair_dispatch(steps, index):
                continue
            if case.get("kind") == "direct":
                compressible = 0
                category = "authority"
            else:
                compressible = 0
                category = "task_capsule"
            _add_transfer_measurement(
                categories,
                category,
                gross=capsule_tokens,
                non_compressible=capsule_tokens - compressible,
                compressible=compressible,
                source=capsule_source,
            )
            duplicate_components.append(
                _component(category, capsule_source, capsule_text)
            )


    for boundary, projection, source in projection_rows:
        compact = _compact_transfer_projection(boundary, projection, source)
        text = _canonical_json_text(compact)
        tokens = count_o200k_base_tokens(text)
        category = {
            "task_to_implementation": "implementation_handoff",
            "implementation_to_review": "review_handoff",
            "review_to_repair": "repair_context",
        }[boundary]
        _add_transfer_measurement(
            categories,
            category,
            gross=tokens,
            non_compressible=tokens,
            compressible=0,
            source=source,
        )
        duplicate_components.append(_component(boundary, source, text))

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        action = step.get("action")
        source = f"{_relative(FIXTURES)}#/{case_id}/steps/{index}"
        if action == "adaptive-test-evidence" and step.get("freshness", 0) > 0:
            tokens = count_o200k_base_tokens(_canonical_json_text(step))
            _add_transfer_measurement(
                categories,
                "evidence_ledger",
                gross=tokens,
                non_compressible=0,
                compressible=0,
                source=source,
            )
        if action in {"edit", "repair"}:
            value = {key: step.get(key) for key in ("task_id", "path") if key in step}
            tokens = count_o200k_base_tokens(_canonical_json_text(value))
            _add_transfer_measurement(
                categories,
                "diff",
                gross=tokens,
                non_compressible=0,
                compressible=0,
                source=source,
            )
        if action == "review-discipline" and isinstance(step.get("diff"), dict):
            tokens = count_o200k_base_tokens(_canonical_json_text(step["diff"]))
            _add_transfer_measurement(
                categories,
                "diff",
                gross=tokens,
                non_compressible=0,
                compressible=0,
                source=f"{source}/diff",
            )
        if action == "validate":
            tokens = count_o200k_base_tokens(_canonical_json_text(step))
            _add_transfer_measurement(
                categories,
                "validation",
                gross=tokens,
                non_compressible=0,
                compressible=0,
                source=source,
            )
        if action == "review-discipline" and isinstance(step.get("validation"), dict):
            tokens = count_o200k_base_tokens(_canonical_json_text(step["validation"]))
            _add_transfer_measurement(
                categories,
                "validation",
                gross=tokens,
                non_compressible=0,
                compressible=0,
                source=f"{source}/validation",
            )

    categories["superseded_evidence"]["source_selectors"].add(
        "current-only transfer filter; superseded fixture evidence excluded"
    )

    duplicates = _duplicate_block_metrics(duplicate_components)
    _add_transfer_measurement(
        categories,
        "duplicate_context",
        gross=duplicates["duplicate_rule_tokens"],
        non_compressible=0,
        compressible=0,
        source="exact normalized Markdown blocks across exclusive transfer projections",
    )
    categories["duplicate_context"]["source_selectors"].update(
        source["component"]
        for block in duplicates["duplicate_blocks"]
        for source in block["sources"]
    )
    for category in categories.values():
        category["source_selectors"] = sorted(category["source_selectors"])
    gross = sum(categories[item]["gross_tokens"] for item in TRANSFER_EXCLUSIVE_CATEGORIES)
    non_compressible = sum(
        categories[item]["non_compressible_tokens"]
        for item in TRANSFER_EXCLUSIVE_CATEGORIES
    )
    compressible = sum(
        categories[item]["compressible_tokens"]
        for item in TRANSFER_EXCLUSIVE_CATEGORIES
    )
    return {
        "id": case_id,
        "boundary_rows": [
            {
                "boundary": boundary,
                "task_id": projection.get("task_id"),
                "projection": projection,
                "transfer_reference": _compact_transfer_projection(
                    boundary, projection, source
                ),
                "source": source,
            }
            for boundary, projection, source in projection_rows
        ],
        "categories": categories,
        "gross_tokens": gross,
        "non_compressible_tokens": non_compressible,
        "compressible_tokens": compressible,
        "compressible_ratio": round(compressible / gross, 6) if gross else 0.0,
    }


def _aggregate_transfer_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = _empty_transfer_categories()
    for row in rows:
        for name, source in row["categories"].items():
            target = categories[name]
            for field in (
                "gross_tokens",
                "non_compressible_tokens",
                "compressible_tokens",
                "occurrence_count",
            ):
                target[field] += source[field]
            target["source_selectors"].update(source["source_selectors"])
    for category in categories.values():
        category["source_selectors"] = sorted(category["source_selectors"])
    gross = sum(categories[item]["gross_tokens"] for item in TRANSFER_EXCLUSIVE_CATEGORIES)
    non_compressible = sum(
        categories[item]["non_compressible_tokens"]
        for item in TRANSFER_EXCLUSIVE_CATEGORIES
    )
    compressible = sum(
        categories[item]["compressible_tokens"]
        for item in TRANSFER_EXCLUSIVE_CATEGORIES
    )
    return {
        "categories": categories,
        "gross_tokens": gross,
        "non_compressible_tokens": non_compressible,
        "compressible_tokens": compressible,
        "compressible_ratio": round(compressible / gross, 6) if gross else 0.0,
    }


def _measure_context(
    components: list[dict[str, Any]],
    *,
    budget_class: str,
) -> dict[str, Any]:
    limit = CONTEXT_BUDGET_LIMITS[budget_class]
    combined = "\n\n".join(component["_text"].rstrip() for component in components)
    total_tokens = count_o200k_base_tokens(combined)
    duplicates = _duplicate_block_metrics(components)
    duplicate_tokens = duplicates["duplicate_rule_tokens"]
    ratio = duplicate_tokens / total_tokens if total_tokens else 0.0
    public_components = [
        {key: value for key, value in component.items() if key != "_text"}
        for component in components
    ]
    within_soft_target = total_tokens <= limit["soft_target"]
    within_hard_ceiling = total_tokens <= limit["hard_ceiling"]
    return {
        "budget_class": budget_class,
        "soft_target": limit["soft_target"],
        "hard_ceiling": limit["hard_ceiling"],
        "calibration_status": limit["calibration_status"],
        "total_tokens": total_tokens,
        "sum_component_tokens": sum(item["tokens"] for item in public_components),
        "duplicate_rule_tokens": duplicate_tokens,
        "duplicate_rule_token_ratio": round(ratio, 6),
        "within_soft_target": within_soft_target,
        "within_hard_ceiling": within_hard_ceiling,
        "soft_margin_tokens": limit["soft_target"] - total_tokens,
        "hard_margin_tokens": limit["hard_ceiling"] - total_tokens,
        "budget_signal": (
            "hard-ceiling-exceeded"
            if not within_hard_ceiling
            else "growth-advisory"
            if not within_soft_target
            else None
        ),
        "within_duplicate_budget": ratio <= DUPLICATE_TOKEN_RATIO_MAX,
        "components": public_components,
        "duplicate_blocks": duplicates["duplicate_blocks"],
    }


def evaluate_route_obligation_context(
    components: list[dict[str, Any]],
    *,
    required_route_obligations: dict[str, Any],
    budget_class: str,
) -> dict[str, Any]:
    """Evaluate token pressure while preserving one closed route obligation input."""

    required_fields = {
        "primary_professional_skill",
        "implementation_layer3",
        "domain",
        "required_review_skills",
    }
    if (
        not isinstance(required_route_obligations, dict)
        or set(required_route_obligations) != required_fields
        or not isinstance(
            required_route_obligations["primary_professional_skill"], str
        )
        or not required_route_obligations["primary_professional_skill"]
        or any(
            not isinstance(required_route_obligations[field], list)
            or any(
                not isinstance(item, str) or not item
                for item in required_route_obligations[field]
            )
            for field in (
                "implementation_layer3",
                "domain",
                "required_review_skills",
            )
        )
    ):
        raise ValueError("route obligations must use the exact closed contract")
    obligation_components = [
        component
        for component in components
        if isinstance(component, dict)
        and component.get("kind") == "route-obligations"
    ]
    observed: object = None
    if len(obligation_components) == 1:
        try:
            observed = json.loads(obligation_components[0]["_text"])
        except (KeyError, TypeError, json.JSONDecodeError):
            observed = None
    preserved = observed == required_route_obligations
    if not preserved:
        return {
            "failure_id": "context-route-obligation-mismatch",
            "outcome": "fail-closed",
            "continue_allowed": False,
            "route_obligations_preserved": False,
            "required_route_obligations": required_route_obligations,
            "observed_route_obligations": observed,
        }
    measurement = _measure_context(
        components,
        budget_class=budget_class,
    )
    overflow = measurement["within_hard_ceiling"] is False
    return {
        **measurement,
        "failure_id": (
            "context-token-budget-overflow" if overflow else None
        ),
        "outcome": "fail-closed" if overflow else "continue",
        "continue_allowed": not overflow,
        "route_obligations_preserved": True,
        "required_route_obligations": required_route_obligations,
        "observed_route_obligations": observed,
    }


def _profile_path(host: str, role: str) -> Path:
    return HOST_PROFILE_ROOTS[host] / f"{role}{HOST_PROFILE_SUFFIXES[host]}"


def _load_manifests(errors: list[str]) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for profile in BUILD_PROFILES:
        path = DIST_SKILLS / profile / ".changeforge-build-manifest.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                f"{_relative(path)} is unavailable or malformed; run all three builds first: {exc}"
            )
            continue
        if not isinstance(value, dict) or value.get("profile") != profile:
            errors.append(f"{_relative(path)} does not describe profile {profile!r}")
            continue
        if value.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
            errors.append(
                f"{_relative(path)} compiled_layer3_format must equal "
                f"{COMPILED_LAYER3_FORMAT!r}"
            )
            continue
        manifests[profile] = value
    return manifests


def _validate_profile_digest(
    host: str,
    role: str,
    profile_path: Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    expected = (
        manifest.get("agent_profile_sha256", {})
        .get(host, {})
        .get(role)
    )
    actual = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    if expected != actual:
        errors.append(
            f"{_relative(profile_path)} digest does not match the {manifest.get('profile')} build manifest"
        )


def _layer3_path(
    build_profile: str,
    primary: str,
    name: str,
    manifest: dict[str, Any],
) -> Path:
    compiled = manifest.get("compiled_layer3_references", {}).get(primary, [])
    is_compiled = name in compiled
    is_top_level = name in manifest.get("top_level_skills", [])
    if is_compiled == is_top_level:
        raise ValueError(
            f"{build_profile}:{primary} must resolve routed Layer 3 Skill {name!r} "
            "through exactly one compiled or top-level delivery path"
        )
    if is_compiled:
        return DIST_SKILLS / build_profile / primary / "references" / "layer3" / f"{name}.md"
    return DIST_SKILLS / build_profile / name / "SKILL.md"


def _layer3_reference_path(
    build_profile: str,
    primary: str,
    logical_id: str,
    manifest: dict[str, Any],
) -> Path:
    owner, relative = parse_layer3_reference_id(logical_id)
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


def _layer3_registry_entries() -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for registry_path, key in (
        (ROOT / "src/registry/foundation-skills.yaml", "foundation_skills"),
        (ROOT / "src/registry/domain-skills.yaml", "domain_skills"),
    ):
        document = load_yaml_file(registry_path)
        rows = document.get(key) if isinstance(document, dict) else None
        if not isinstance(rows, list):
            raise ValueError(f"{_relative(registry_path)} requires a {key} list")
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("name"), str):
                entries[row["name"]] = row
    return entries


def _layer3_reference_registry_errors(
    case_id: str,
    index: int,
    step: dict[str, Any],
    entries: dict[str, dict[str, Any]],
) -> list[str]:
    if "utility_capsule" in step:
        return []
    raw = step.get("layer3_references")
    if not isinstance(raw, list):
        return [f"{case_id}: dispatch step {index} layer3_references must be a list"]
    errors: list[str] = []
    for logical_id in raw:
        try:
            owner, relative = parse_layer3_reference_id(logical_id)
        except FixtureCapsuleError as exc:
            errors.append(f"{case_id}: dispatch step {index}: {exc}")
            continue
        entry = entries.get(owner)
        indexed = (
            reference_paths(
                entry.get("reference_index"),
                f"{owner}.reference_index",
                owner=owner,
            )
            if entry
            else []
        )
        if entry is None or relative not in indexed:
            errors.append(
                f"{case_id}: dispatch step {index} Layer 3 Reference "
                f"{logical_id!r} is not registry-indexed"
            )
            continue
        source = ROOT / str(entry.get("path", "")) / relative
        if not source.is_file() or _uses_symlink(source, ROOT):
            errors.append(
                f"{case_id}: dispatch step {index} Layer 3 Reference "
                f"{logical_id!r} is missing or symlinked in source"
            )
    return errors


def _professional_reference_path(
    build_profile: str,
    primary: str,
    relative: str,
) -> Path:
    if "\\" in relative:
        raise ValueError(f"professional reference must use POSIX syntax: {relative!r}")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError(f"professional reference is not normalized: {relative!r}")
    if not parsed.parts or parsed.parts[0] != "references":
        raise ValueError(f"professional reference must remain under references/: {relative!r}")
    return DIST_SKILLS.joinpath(build_profile, primary, *parsed.parts)


def _has_authoritative_task_dag_provenance(
    step: dict[str, Any],
    case_kind: str,
    case_steps: list[Any],
) -> bool:
    if (
        case_kind != "direct"
        or step.get("profile") != "task-agent"
        or "utility_capsule" in step
    ):
        return False
    capsule = step.get("fixture_capsule")
    if not isinstance(capsule, dict) or capsule.get("contract_type") != "task":
        return False
    if capsule.get("inputs") != [
        "Accepted, artifact-reviewed authoritative Task DAG and downstream "
        "Task Capsule",
        "Current source, tests, routed Professional Skill, and named Layer 3 "
        "guidance",
    ]:
        return False
    dependencies = capsule.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) != 1:
        return False
    dependency = dependencies[0]
    template = capsule.get("template")
    if template == "implementation-task":
        if dependency not in (
            "Accepted authoritative Task DAG node and engineering-artifact-review "
            "pass.",
            "Accepted authoritative Task DAG dependency plus completed predecessor "
            "output and current evidence.",
        ):
            return False
    elif template == "integration-task":
        if dependency != (
            "Completed authoritative Task DAG predecessor outputs and their "
            "current evidence."
        ):
            return False
    else:
        return False
    if any(
        isinstance(candidate, dict)
        and candidate.get("action") == "dispatch"
        and candidate.get("profile") == "analysis-agent"
        for candidate in case_steps
    ):
        return False
    authoritative_evidence = (
        "Accepted, artifact-reviewed authoritative Task DAG selects three "
        "downstream integration tasks and final review.",
        "Accepted, artifact-reviewed authoritative Task DAG selects two "
        "serialized downstream tasks and final review.",
    )
    return any(
        isinstance(candidate, dict)
        and candidate.get("action") == "progress"
        and candidate.get("evidence") in authoritative_evidence
        for candidate in case_steps
    )


def _budget_class(
    step: dict[str, Any],
    case_kind: str,
    case_steps: list[Any],
) -> str:
    profile = step.get("profile")
    if profile == "analysis-agent":
        return "analysis"
    if profile == "review-agent":
        return "review"
    if profile == "task-agent" and "utility_capsule" in step:
        return "utility"
    if profile == "task-agent":
        if case_kind == "analyzed" or _has_authoritative_task_dag_provenance(
            step,
            case_kind,
            case_steps,
        ):
            return "analyzed_task"
        return "task"
    raise ValueError(f"unsupported dispatch profile {profile!r}")


def _fixture_cases(document: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    for group, key in (
        ("release", "cases"),
        ("scheduling", "scheduling_cases"),
        ("utility", "utility_cases"),
    ):
        raw_cases = document.get(key)
        if not isinstance(raw_cases, list):
            raise ValueError(f"fixture document requires a {key} list")
        for case in raw_cases:
            if not isinstance(case, dict):
                raise ValueError(f"{key} entries must be mappings")
            result.append((group, case))
    if not result:
        raise ValueError("fixture document must contain at least one case")
    return result


def _dispatch_metadata_errors(case_id: str, index: int, step: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        validate_and_render_fixture_capsule(step)
    except FixtureCapsuleError as exc:
        errors.append(f"{case_id}: dispatch step {index} has invalid fixture Capsule: {exc}")
    mode = step.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        errors.append(f"{case_id}: dispatch step {index} needs a non-empty mode")
    references = step.get("professional_references")
    if not isinstance(references, list) or any(
        not isinstance(item, str) or not item.strip() for item in references
    ):
        errors.append(
            f"{case_id}: dispatch step {index} needs a professional_references string list"
        )
        references = []
    if len(references) != len(set(references)):
        errors.append(f"{case_id}: dispatch step {index} repeats a professional reference")
    primary = step.get("primary_skill")
    if primary == "engineering-change-analysis":
        expected_reference = MODE_REFERENCES.get(str(mode))
        if expected_reference is None:
            errors.append(f"{case_id}: dispatch step {index} has unsupported analysis mode {mode!r}")
        elif expected_reference not in references:
            errors.append(
                f"{case_id}: dispatch step {index} must load mode reference {expected_reference!r}"
            )
    if "utility_capsule" in step:
        utility_mode = step.get("utility_capsule", {}).get("mode")
        if mode != utility_mode:
            errors.append(f"{case_id}: dispatch step {index} utility mode does not match capsule")
        if references:
            errors.append(f"{case_id}: dispatch step {index} utility must not load references")
        if "layer3_references" in step:
            errors.append(
                f"{case_id}: dispatch step {index} utility must not declare layer3_references"
            )
    return errors


def _discovery_metadata(
    build_profile: str,
    errors: list[str],
) -> dict[str, Any]:
    root = DIST_SKILLS / build_profile
    entries: list[dict[str, Any]] = []
    payloads: list[str] = []
    for skill_dir in sorted(
        path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")
    ):
        skill_file = skill_dir / "SKILL.md"
        try:
            metadata, _raw, _body = parse_frontmatter(skill_file)
        except ValidationProblem as exc:
            errors.append(str(exc).replace(str(ROOT) + "/", ""))
            continue
        name = metadata.get("name")
        description = metadata.get("description")
        if not isinstance(name, str) or not isinstance(description, str):
            errors.append(f"{_relative(skill_file)} lacks name/description discovery metadata")
            continue
        payload = f"name: {name}\ndescription: {description.strip()}"
        payloads.append(payload)
        entries.append(
            {
                "path": _relative(skill_file),
                "sha256": _sha256_text(payload),
                "tokens": count_o200k_base_tokens(payload),
            }
        )
    combined = "\n\n".join(payloads)
    return {
        "build_profile": build_profile,
        "skill_count": len(entries),
        "canonical_serialization": "name and description from each top-level SKILL.md",
        "tokens": count_o200k_base_tokens(combined),
        "sha256": _sha256_text(combined),
        "entries": entries,
        "accounting": "reported separately because host discovery injection is not observed",
    }


def _compact_component_catalog(
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate repeated host/profile/Skill component evidence in the report."""

    keys = sorted(
        {
            (
                component["kind"],
                component["path"],
                component["sha256"],
                component["tokens"],
            )
            for context in contexts
            for component in context.get("components", [])
        }
    )
    ids = {key: f"component-{index:04d}" for index, key in enumerate(keys, start=1)}
    catalog = [
        {
            "id": ids[key],
            "kind": key[0],
            "path": key[1],
            "sha256": key[2],
            "tokens": key[3],
        }
        for key in keys
    ]
    for context in contexts:
        context["component_ids"] = [
            ids[
                (
                    component["kind"],
                    component["path"],
                    component["sha256"],
                    component["tokens"],
                )
            ]
            for component in context.pop("components", [])
        ]
        context.pop("duplicate_blocks", None)
    return catalog


def _maximum_summary(
    maximum: dict[str, Any] | None,
    *,
    include_dispatch: bool,
) -> dict[str, Any] | None:
    """Expose Core-derived soft and hard margins for one maximum."""

    if maximum is None:
        return None
    observed = maximum["total_tokens"]
    result = {
        "tokens": observed,
        "soft_target": maximum["soft_target"],
        "hard_ceiling": maximum["hard_ceiling"],
        "soft_margin_tokens": maximum["soft_target"] - observed,
        "hard_margin_tokens": maximum["hard_ceiling"] - observed,
        "within_soft_target": maximum["within_soft_target"],
        "within_hard_ceiling": maximum["within_hard_ceiling"],
        "budget_signal": maximum["budget_signal"],
        "calibration_status": maximum["calibration_status"],
        "host": maximum["host"],
        "build_profile": maximum["build_profile"],
    }
    if include_dispatch:
        result.update(
            {
                "step": maximum["step"],
                "primary_skill": maximum["primary_skill"],
            }
        )
    return result


def _selector_authority() -> dict[str, Any]:
    """Load the single registry-owned selector authority projection."""

    return layer3_selector_authority(
        load_yaml_file(FOUNDATION_REGISTRY),
        load_yaml_file(PROFESSIONAL_REGISTRY),
        load_yaml_file(DOMAIN_REGISTRY),
        context="admissible context composition selector authority",
    )


def _normalized_signal(value: str) -> str:
    return " ".join(value.casefold().split())


def _activation_evidence(records: tuple[dict[str, Any], ...]) -> list[str] | None:
    """Choose one source-declared representative for a selector equivalence class."""

    negatives = {
        _normalized_signal(signal)
        for record in records
        for signal in record["nearest_negative_signals"]
    }
    evidence: list[str] = []
    normalized_evidence: set[str] = set()
    for record in records:
        for group in record["positive_signal_groups"]:
            selected = next(
                (
                    signal
                    for signal in group
                    if _normalized_signal(signal) not in negatives
                ),
                None,
            )
            if selected is None:
                return None
            normalized = _normalized_signal(selected)
            if normalized not in normalized_evidence:
                normalized_evidence.add(normalized)
                evidence.append(selected)
    return evidence


def _selection_kind(profile: str) -> str:
    return {
        "analysis-agent": "analysis-risk",
        "task-agent": "implementation-risk",
        "review-agent": "review-risk",
    }[profile]


def _admissible_selector_equivalence_classes(
    authority: dict[str, Any],
    projection: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    """Invoke the canonical selector over every legal <=3 activation class."""

    errors: list[str] = []
    selectors = projection["selectors"]
    classes_by_selected: dict[tuple[str, ...], dict[str, Any]] = {}
    positive_cases = 0
    nearest_negative_cases = 0
    nearest_negative_leaks = 0
    over_max_rejections = 0
    unauthorized_exact_rejections = 0
    duplicate_exact_rejections = 0

    empty_receipt = layer3_selector_runtime_selection_receipt(
        projection,
        evidence_signals=[],
    )
    classes_by_selected[tuple(empty_receipt["selected_layer3"])] = {
        "selected_layer3": list(empty_receipt["selected_layer3"]),
        "receipt": empty_receipt,
    }

    for record in selectors:
        evidence = _activation_evidence((record,))
        if evidence is None:
            errors.append(
                f"{projection['professional_skill']}:{projection['profile']}:"
                f"{record['selector_id']} has no positive representative outside "
                "its nearest-negative boundary"
            )
            continue
        positive_cases += 1
        receipt = layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence,
        )
        classes_by_selected.setdefault(
            tuple(receipt["selected_layer3"]),
            {
                "selected_layer3": list(receipt["selected_layer3"]),
                "receipt": receipt,
            },
        )
        negative_evidence = [*evidence, record["nearest_negative_signals"][0]]
        negative_receipt = layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=negative_evidence,
        )
        nearest_negative_cases += 1
        if set(record["selectable_layer3"]) & set(
            negative_receipt["selected_layer3"]
        ):
            nearest_negative_leaks += 1

    for size in range(2, min(3, len(selectors)) + 1):
        for selected_records in combinations(selectors, size):
            evidence = _activation_evidence(selected_records)
            if evidence is None:
                continue
            try:
                receipt = layer3_selector_runtime_selection_receipt(
                    projection,
                    evidence_signals=evidence,
                )
            except ValidationProblem as exc:
                if "more than three Layer 3" not in str(exc):
                    errors.append(str(exc))
                continue
            classes_by_selected.setdefault(
                tuple(receipt["selected_layer3"]),
                {
                    "selected_layer3": list(receipt["selected_layer3"]),
                    "receipt": receipt,
                },
            )

    for selected_class in classes_by_selected.values():
        selected = selected_class["selected_layer3"]
        try:
            fixed = layer3_selector_runtime_projection(
                authority,
                professional_skill=projection["professional_skill"],
                profile=projection["profile"],
                selection_owner=projection["selection_owner"],
                exact_layer3=selected,
            )
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        if fixed["selector_loaded"] or fixed["exact_layer3"] != selected:
            errors.append(
                f"{projection['professional_skill']}:{projection['profile']} "
                "exact Layer 3 did not skip selector loading"
            )

    replay_class = max(
        classes_by_selected.values(),
        key=lambda item: len(item["selected_layer3"]),
    )
    replay_errors = layer3_selector_runtime_selection_receipt_errors(
        replay_class["receipt"],
        expected_owner=projection["selection_owner"],
        expected_profile=projection["profile"],
        expected_professional=projection["professional_skill"],
        expected_selection_kind=_selection_kind(projection["profile"]),
        expected_selected_layer3=replay_class["selected_layer3"],
    )
    errors.extend(replay_errors)

    try:
        layer3_selector_runtime_projection(
            authority,
            professional_skill=projection["professional_skill"],
            profile=projection["profile"],
            selection_owner=projection["selection_owner"],
            exact_layer3=["admissible-context-invented-layer3"],
        )
    except ValidationProblem:
        unauthorized_exact_rejections += 1
    authorized = projection["authorized_layer3"]
    if authorized:
        try:
            layer3_selector_runtime_projection(
                authority,
                professional_skill=projection["professional_skill"],
                profile=projection["profile"],
                selection_owner=projection["selection_owner"],
                exact_layer3=[authorized[0], authorized[0]],
            )
        except ValidationProblem:
            duplicate_exact_rejections += 1

    overflow_found = False
    for size in range(2, min(4, len(selectors)) + 1):
        if overflow_found:
            break
        for selected_records in combinations(selectors, size):
            if sum(len(record["selectable_layer3"]) for record in selected_records) <= 3:
                continue
            evidence = _activation_evidence(selected_records)
            if evidence is None:
                continue
            try:
                layer3_selector_runtime_selection_receipt(
                    projection,
                    evidence_signals=evidence,
                )
            except ValidationProblem as exc:
                if "more than three Layer 3" in str(exc):
                    over_max_rejections += 1
                    overflow_found = True
                    break
                errors.append(str(exc))

    return (
        sorted(
            classes_by_selected.values(),
            key=lambda item: (len(item["selected_layer3"]), item["selected_layer3"]),
        ),
        {
            "positive_selector_case_count": positive_cases,
            "nearest_negative_case_count": nearest_negative_cases,
            "nearest_negative_leak_count": nearest_negative_leaks,
            "over_max_rejection_count": over_max_rejections,
            "unauthorized_exact_rejection_count": unauthorized_exact_rejections,
            "duplicate_exact_rejection_count": duplicate_exact_rejections,
            "receipt_replay_count": 1 if not replay_errors else 0,
        },
        errors,
    )


def _registry_rows_by_name(document: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    return {
        row["name"]: row
        for row in document[key]
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }


def _eligible_reference_entries(
    row: dict[str, Any],
    profile: str,
) -> list[dict[str, Any]]:
    return [
        entry
        for entry in row.get("reference_index", [])
        if isinstance(entry, dict)
        and profile in entry.get("required_by", [])
    ]


def _reference_envelopes(
    rows: list[tuple[str, dict[str, Any]]],
    context_authority: dict[str, object],
) -> tuple[list[list[tuple[str, dict[str, Any]]]], int, int, int, int]:
    """Return maximal legal selected unions without deciding stage residency.

    A selected union may contain independent Reference decisions.  Only the
    v3 staged planner's reciprocal must-co-trigger components authorize shared
    residency.  This conflict frontier establishes union legality; it never
    preloads a resident set.  Memoized independent-set counting avoids
    enumerating or tokenizing dominated subsets.
    """

    non_index = [
        (owner, entry)
        for owner, entry in rows
        if entry.get("type") != "index"
    ]
    forbidden_indexes = len(rows) - len(non_index)
    conflict_pairs: set[tuple[int, int]] = set()
    for left, right in combinations(range(len(non_index)), 2):
        left_owner, left_entry = non_index[left]
        right_owner, right_entry = non_index[right]
        if left_owner != right_owner:
            continue
        decision = reference_context_admissibility_decisions(
            context_authority,
            references=[
                (left_owner, left_entry["path"]),
                (right_owner, right_entry["path"]),
            ],
            path="analyzed",
        )
        if decision["failure_id"] == "context-reference-conflict":
            conflict_pairs.add((left, right))

    full_mask = (1 << len(non_index)) - 1
    neighbors = [0] * len(non_index)
    for left, right in conflict_pairs:
        neighbors[left] |= 1 << right
        neighbors[right] |= 1 << left

    independent_count_cache: dict[int, int] = {}

    def independent_count(mask: int) -> int:
        cached = independent_count_cache.get(mask)
        if cached is not None:
            return cached
        if not mask:
            return 1
        vertex_bit = mask & -mask
        vertex = vertex_bit.bit_length() - 1
        without_vertex = mask & ~vertex_bit
        count = independent_count(without_vertex) + independent_count(
            without_vertex & ~neighbors[vertex]
        )
        independent_count_cache[mask] = count
        return count

    frontier = {full_mask}
    changed = True
    while changed:
        changed = False
        next_frontier: set[int] = set()
        for mask in frontier:
            conflict = next(
                (
                    (left, right)
                    for left, right in sorted(conflict_pairs)
                    if mask & (1 << left) and mask & (1 << right)
                ),
                None,
            )
            if conflict is None:
                next_frontier.add(mask)
                continue
            changed = True
            left, right = conflict
            next_frontier.add(mask & ~(1 << left))
            next_frontier.add(mask & ~(1 << right))
        frontier = next_frontier
    maximal_masks = sorted(
        (
            mask
            for mask in frontier
            if not any(mask != other and mask & other == mask for other in frontier)
        ),
        key=lambda mask: (
            -mask.bit_count(),
            tuple(
                (non_index[index][0], non_index[index][1]["path"])
                for index in range(len(non_index))
                if mask & (1 << index)
            ),
        ),
    )
    envelopes = [
        [
            non_index[index]
            for index in range(len(non_index))
            if mask & (1 << index)
        ]
        for mask in maximal_masks
    ] or [[]]
    legal_subset_count = independent_count(full_mask)
    return (
        envelopes,
        legal_subset_count - len(envelopes),
        forbidden_indexes,
        len(conflict_pairs),
        legal_subset_count,
    )


def _capsule_envelopes(
    cases: list[tuple[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    envelopes: dict[str, dict[str, Any]] = {}
    for _fixture_group, case in cases:
        steps = case.get("steps", [])
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or step.get("action") != "dispatch":
                continue
            try:
                rendered = validate_and_render_fixture_capsule(step)
                budget_class = _budget_class(
                    step,
                    str(case.get("kind") or ""),
                    steps,
                )
            except (FixtureCapsuleError, ValueError):
                continue
            if budget_class not in ADMISSIBLE_BUDGET_CLASSES:
                continue
            component = _component(
                "dispatch_capsule",
                f"fixture:{case.get('id')}:step:{index}:canonical-capsule",
                rendered,
            )
            current = envelopes.get(budget_class)
            if current is None or component["tokens"] > current["tokens"]:
                envelopes[budget_class] = component
    return envelopes


def _component_upper_bound(components: list[dict[str, Any]]) -> int:
    """Return a memoized component-token dominance score without re-tokenizing."""

    return sum(component["tokens"] for component in components) + max(
        0, len(components) - 1
    ) * CONTEXT_COMPONENT_SEPARATOR_TOKENS


def _token_distribution(values: list[int]) -> dict[str, int | None]:
    """Return deterministic nearest-rank distribution statistics."""

    ordered = sorted(values)
    if not ordered:
        return {
            "count": 0,
            "p50": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
        }

    def nearest_rank(percentile: int) -> int:
        index = max(0, ((percentile * len(ordered) + 99) // 100) - 1)
        return ordered[index]

    return {
        "count": len(ordered),
        "p50": nearest_rank(50),
        "p90": nearest_rank(90),
        "p95": nearest_rank(95),
        "p99": nearest_rank(99),
        "max": ordered[-1],
    }


def _unavailable_growth_distribution() -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": "single-snapshot evaluation has no prior comparable valid-context population",
        "count": 0,
        "p50": None,
        "p90": None,
        "p95": None,
        "p99": None,
        "max": None,
    }


def _main_utility_selection_rows(
    main_contexts: list[dict[str, Any]],
    dispatch_measurements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project stable measured rows for classes outside the dominance mapping."""

    rows: list[dict[str, Any]] = []
    for measurement in [
        *main_contexts,
        *(
            item
            for item in dispatch_measurements
            if item.get("budget_class") == "utility"
        ),
    ]:
        budget_class = measurement.get("budget_class")
        if budget_class not in {"main", "utility"}:
            raise ValueError(
                "selection identity rows may contain only main or utility measurements"
            )
        components = measurement.get("components")
        if not isinstance(components, list) or not components:
            raise ValueError(
                f"{budget_class} selection identity requires measured components"
            )
        render_signature = [
            {
                key: component[key]
                for key in ("kind", "path", "sha256", "tokens")
            }
            for component in components
        ]
        candidate_identity = {
            "host": measurement.get("host"),
            "build_profile": measurement.get("build_profile"),
        }
        if budget_class == "utility":
            candidate_identity.update(
                {
                    "step": measurement.get("step"),
                    "role": measurement.get("role"),
                    "mode": measurement.get("mode"),
                    "primary_skill": measurement.get("primary_skill"),
                    "layer3_skills": measurement.get("layer3_skills", []),
                    "layer3_references": measurement.get(
                        "layer3_references", []
                    ),
                    "professional_references": measurement.get(
                        "professional_references", []
                    ),
                    "canonical_capsule_sha256": measurement.get(
                        "canonical_capsule_sha256"
                    ),
                }
            )
        tokens = measurement.get("total_tokens")
        if not isinstance(tokens, int) or isinstance(tokens, bool):
            raise ValueError(
                f"{budget_class} selection identity requires measured integer tokens"
            )
        rows.append(
            {
                "budget_class": budget_class,
                "candidate_identity": candidate_identity,
                "render_signature_sha256": _sha256_text(
                    _canonical_json_text(render_signature)
                ),
                "tokens": tokens,
            }
        )
    return sorted(rows, key=_canonical_json_text)


def _calibration_selection_identity(
    selected_valid_candidate_rows: Any,
    contract: dict[str, Any],
) -> str:
    """Fingerprint canonical measured valid-candidate rows without budget fields."""

    return _sha256_text(
        _canonical_json_text(
            {
                "tokenizer": contract["tokenizer"],
                "valid_candidate_measurements": selected_valid_candidate_rows,
            }
        )
    )


def _render_signature_tokens(candidate: dict[str, Any]) -> int:
    """Measure one exact rendered component signature without duplicate scanning."""

    return count_o200k_base_tokens(
        "\n\n".join(
            component["_text"].rstrip() for component in candidate["components"]
        )
    )


def _active_reference_ids(candidate: dict[str, Any]) -> list[str]:
    """Return source-owned References resident in this measured candidate stage."""

    return sorted(
        f"{owner}/{path}"
        for owner, path in candidate["stage_loaded_references"]
    )


def _frontier_member_witness(
    *,
    member: str,
    tokens: int,
    equivalence_key: tuple[Any, ...],
    render_signature: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    """Bind one member maximum to compact deterministic candidate evidence."""

    return {
        "member": member,
        "maximum_tokens": tokens,
        "canonical_reduction_key_sha256": _sha256_text(
            _canonical_json_text(equivalence_key)
        ),
        "render_signature_sha256": _sha256_text(
            _canonical_json_text(render_signature)
        ),
    }


def _dominance_frontier_consumer_boundary() -> dict[str, Any]:
    """Prove the eval projection is absent from runtime and build consumers."""

    checked_paths = (
        ROOT / "scripts" / "build.py",
        ROOT / "scripts" / "validation_utils.py",
        ROOT / "src" / "control-prompts" / "main-control-agent.md",
        ROOT
        / "src"
        / "control-skills"
        / "engineering-control-plane"
        / "references"
        / "professional-skill-router.md",
    )
    token = "dominance_frontier"
    runtime_consumers: list[str] = []
    build_consumers: list[str] = []
    checked_fingerprints: dict[str, str] = {}
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        relative = _relative(path)
        checked_fingerprints[relative] = _sha256_text(text)
        if token not in text:
            continue
        if path.name == "build.py":
            build_consumers.append(relative)
        else:
            runtime_consumers.append(relative)
    return {
        "projection_only": not runtime_consumers and not build_consumers,
        "runtime_consumers": runtime_consumers,
        "build_consumers": build_consumers,
        "checked_path_fingerprints": checked_fingerprints,
    }


def _dominance_frontier_projection(
    *,
    canonical_candidates: dict[
        str,
        dict[tuple[Any, ...], dict[str, Any]],
    ],
    authority: dict[str, Any],
    control_projections: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Project complete source-derived budget dominance without runtime matching."""

    signature_tokens: dict[tuple[tuple[str, str], ...], int] = {}
    budget_rows: dict[str, dict[str, Any]] = {}
    mapping_hasher = hashlib.sha256()
    component_fingerprints: set[tuple[str, str, str]] = set()

    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        soft_target = CONTEXT_BUDGET_LIMITS[budget_class]["soft_target"]
        candidates_by_key = canonical_candidates[budget_class]
        signatures: set[tuple[tuple[str, str], ...]] = set()
        candidate_tokens: list[int] = []
        all_members = {
            "professional": set(),
            "layer3": set(),
            "active_reference": set(),
        }
        frontier_members = {
            "professional": set(),
            "layer3": set(),
            "active_reference": set(),
        }
        member_maxima: dict[str, dict[str, tuple[int, str, dict[str, Any]]]] = {
            "professional": {},
            "layer3": {},
            "active_reference": {},
        }
        over_target_candidate_count = 0

        for equivalence_key, candidate in sorted(
            candidates_by_key.items(), key=lambda item: repr(item[0])
        ):
            render_signature = candidate["render_signature"]
            signatures.add(render_signature)
            tokens = signature_tokens.get(render_signature)
            if tokens is None:
                tokens = _render_signature_tokens(candidate)
                signature_tokens[render_signature] = tokens
            candidate_tokens.append(tokens)
            active_references = _active_reference_ids(candidate)
            members = {
                "professional": [candidate["professional_skill"]],
                "layer3": sorted(candidate["selected_layer3"]),
                "active_reference": active_references,
            }
            over_target = tokens > soft_target
            over_target_candidate_count += int(over_target)
            equivalence_key_text = _canonical_json_text(equivalence_key)
            equivalence_key_rank = _sha256_text(equivalence_key_text)
            render_signature_sha256 = _sha256_text(
                _canonical_json_text(render_signature)
            )
            mapping_hasher.update(
                (
                    _canonical_json_text(
                        {
                            "budget_class": budget_class,
                            "canonical_reduction_key": equivalence_key,
                            "render_signature_sha256": render_signature_sha256,
                            "tokens": tokens,
                        }
                    )
                    + "\n"
                ).encode("utf-8")
            )
            component_fingerprints.update(
                (component["kind"], component["path"], component["sha256"])
                for component in candidate["components"]
            )
            for member_kind, values in members.items():
                all_members[member_kind].update(values)
                if over_target:
                    frontier_members[member_kind].update(values)
                for member in values:
                    current = member_maxima[member_kind].get(member)
                    rank = (tokens, equivalence_key_rank)
                    if current is None or rank > (current[0], current[1]):
                        member_maxima[member_kind][member] = (
                            tokens,
                            equivalence_key_rank,
                            _frontier_member_witness(
                                member=member,
                                tokens=tokens,
                                equivalence_key=equivalence_key,
                                render_signature=render_signature,
                            ),
                        )

        outside_members = {
            member_kind: sorted(all_members[member_kind] - frontier_members[member_kind])
            for member_kind in all_members
        }
        budget_rows[budget_class] = {
            "soft_target": soft_target,
            "hard_ceiling": CONTEXT_BUDGET_LIMITS[budget_class]["hard_ceiling"],
            "candidate_count": len(candidates_by_key),
            "exact_render_signature_count": len(signatures),
            "token_distribution": _token_distribution(candidate_tokens),
            "growth_distribution": _unavailable_growth_distribution(),
            "over_target_candidate_count": over_target_candidate_count,
            "frontier_counts": {
                member_kind: len(frontier_members[member_kind])
                for member_kind in frontier_members
            },
            "frontier": {
                member_kind: sorted(frontier_members[member_kind])
                for member_kind in frontier_members
            },
            "frontier_witnesses": {
                member_kind: [
                    member_maxima[member_kind][member][2]
                    for member in sorted(frontier_members[member_kind])
                ]
                for member_kind in frontier_members
            },
            "outside_counts": {
                member_kind: len(outside_members[member_kind])
                for member_kind in outside_members
            },
            "outside": {
                member_kind: [
                    {
                        "member": member,
                        "maximum_tokens": member_maxima[member_kind][member][0],
                    }
                    for member in outside_members[member_kind]
                ]
                for member_kind in outside_members
            },
        }

    task_review_classes = ("task", "review")
    global_all: dict[str, set[str]] = {
        member_kind: set()
        for member_kind in ("professional", "layer3", "active_reference")
    }
    global_frontier: dict[str, set[str]] = {
        member_kind: set() for member_kind in global_all
    }
    for budget_class in task_review_classes:
        row = budget_rows[budget_class]
        for member_kind in global_all:
            global_frontier[member_kind].update(row["frontier"][member_kind])
            global_all[member_kind].update(row["frontier"][member_kind])
            global_all[member_kind].update(
                item["member"] for item in row["outside"][member_kind]
            )
    safe_complement = {
        member_kind: sorted(global_all[member_kind] - global_frontier[member_kind])
        for member_kind in global_all
    }

    component_mapping_text = "\n".join(
        _canonical_json_text(row) for row in sorted(component_fingerprints)
    )
    build_manifest_paths = {
        profile: DIST_SKILLS / profile / ".changeforge-build-manifest.json"
        for profile in BUILD_PROFILES
    }
    source_fingerprints = {
        "registries": {
            _relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                PROFESSIONAL_REGISTRY,
                FOUNDATION_REGISTRY,
                DOMAIN_REGISTRY,
            )
        },
        "capsule_source": {
            "path": _relative(FIXTURES),
            "sha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        },
        "build_manifests": {
            profile: {
                "path": _relative(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for profile, path in build_manifest_paths.items()
        },
        "selector_authority_sha256": _sha256_text(_canonical_json_text(authority)),
        "control_projection_sha256": _sha256_text(
            _canonical_json_text(control_projections)
        ),
        "render_component_inventory": {
            "count": len(component_fingerprints),
            "mapping_sha256": _sha256_text(component_mapping_text),
        },
    }
    return {
        "contract": "changeforge.context-dominance-frontier/v1",
        "projection_scope": "eval-only canonical admissible compositions",
        "budget_classes": budget_rows,
        "global_task_review_union": {
            "frontier_counts": {
                member_kind: len(global_frontier[member_kind])
                for member_kind in global_frontier
            },
            "frontier": {
                member_kind: sorted(global_frontier[member_kind])
                for member_kind in global_frontier
            },
            "safe_complement_counts": {
                member_kind: len(safe_complement[member_kind])
                for member_kind in safe_complement
            },
            "safe_complement": safe_complement,
        },
        "source_fingerprints": source_fingerprints,
        "mapping_row_count": sum(
            len(candidates) for candidates in canonical_candidates.values()
        ),
        "mapping_digest": mapping_hasher.hexdigest(),
        "consumer_boundary": _dominance_frontier_consumer_boundary(),
        "completeness": {
            "numeric_cap": None,
            "truncation": False,
            "task_matcher": False,
            "index_or_catalog_preload": False,
            "canonical_representatives_exhausted": True,
        },
    }


def _evaluate_admissible_context_compositions(
    *,
    cases: list[tuple[str, dict[str, Any]]],
    manifests: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Measure source-derived selector/reference composition equivalence classes."""

    errors: list[str] = []
    authority = _selector_authority()
    control_projections = layer3_selector_control_projections(authority)
    professional_document = load_yaml_file(PROFESSIONAL_REGISTRY)
    foundation_document = load_yaml_file(FOUNDATION_REGISTRY)
    domain_document = load_yaml_file(DOMAIN_REGISTRY)
    context_authority = reference_context_admissibility_authority(
        professional_document,
        foundation_document,
        domain_document,
        context="rendered context admissibility",
    )
    professional_rows = _registry_rows_by_name(
        professional_document,
        "professional_skills",
    )
    layer3_rows = {
        **_registry_rows_by_name(foundation_document, "foundation_skills"),
        **_registry_rows_by_name(domain_document, "domain_skills"),
    }
    domain_names = set(authority["runtime_domains"])
    capsule_envelopes = _capsule_envelopes(cases)
    component_cache: dict[tuple[str, Path], dict[str, Any]] = {}

    def file_component(kind: str, path: Path) -> dict[str, Any]:
        key = (kind, path)
        if key not in component_cache:
            component_cache[key] = _file_component(kind, path)
        return component_cache[key]

    profile_variants: dict[str, tuple[str, Path]] = {}
    for profile in ("analysis-agent", "task-agent", "review-agent"):
        profile_variants[profile] = max(
            (
                (host, _profile_path(host, profile))
                for host in HOST_PROFILE_ROOTS
            ),
            key=lambda item: (
                file_component("worker_profile", item[1])["tokens"],
                file_component("worker_profile", item[1])["sha256"],
                item[0],
            ),
        )

    inventory = {
        "professional_count": len(control_projections),
        "owner_surface_count": 0,
        "legal_selection_equivalence_class_count": 0,
        "positive_selector_case_count": 0,
        "nearest_negative_case_count": 0,
        "professional_reference_count": 0,
        "professional_reference_conflict_count": 0,
        "nested_reference_count": 0,
        "legal_nested_reference_combination_count": 0,
        "dominated_reference_subset_count": 0,
        "maximum_loaded_reference_count": 0,
        "maximum_selected_reference_count": 0,
        "four_plus_reference_measurement_count": 0,
        "stage_measurement_count": 0,
        "valid_carried_predecessor_count": 0,
        "required_output_receipt_count": 0,
        "required_output_receipt_failure_count": 0,
        "carrier_failure_count": 0,
        "dropped_reference_obligation_count": 0,
        "path_excluded_composition_count": 0,
        "path_exclusions": {},
        "layer3_cardinality_counts": {str(value): 0 for value in range(4)},
        "candidate_composition_count": 0,
        "canonical_representative_count": 0,
        "coverage_mapping_count": 0,
        "exact_measurement_count": 0,
        "upper_bound_dominated_count": 0,
        "host_variant_dominated_count": 0,
    }
    forbidden = {
        "maximum_layer3": 3,
        "overflow_failure_id": "admissible-context-layer3-overflow",
        "over_max_rejection_count": 0,
        "unauthorized_exact_rejection_count": 0,
        "duplicate_exact_rejection_count": 0,
        "nearest_negative_leak_count": 0,
        "index_or_catalog_load_count": 0,
        "index_reference_forbidden_count": 0,
        "silent_truncation_count": 0,
        "reference_conflict_leak_count": 0,
    }
    required_coverage = {
        "analysis_foundation_domain": False,
        "analyzed_task_three_layer3": False,
        "review_domain_foundation": False,
        "nested_targeted_references": False,
        "direct_main_owner": False,
        "initial_analysis_main_owner": False,
        "analyzed_brief_owner": False,
        "direct_false_worst_excluded": False,
    }
    professional_reference_ids: set[tuple[str, str, str]] = set()
    nested_reference_ids: set[tuple[str, str, str]] = set()
    maxima: dict[str, dict[str, Any] | None] = {
        budget_class: None for budget_class in ADMISSIBLE_BUDGET_CLASSES
    }
    canonical_candidates: dict[
        str,
        dict[tuple[Any, ...], dict[str, Any]],
    ] = {budget_class: {} for budget_class in ADMISSIBLE_BUDGET_CLASSES}
    receipt_replay_count = 0
    surface_count = 0

    for projection_document in control_projections.values():
        professional = projection_document["professional_skill"]
        professional_row = professional_rows[professional]
        for projection in projection_document["selection_surfaces"]:
            surface_count += 1
            profile = projection["profile"]
            owner = projection["selection_owner"]
            if profile == "analysis-agent" and owner == "main-control-agent":
                required_coverage["initial_analysis_main_owner"] = True
            if profile == "task-agent" and owner == "main-control-agent":
                required_coverage["direct_main_owner"] = True
            if owner == "engineering-brief":
                required_coverage["analyzed_brief_owner"] = True
            classes, selector_stats, selector_errors = (
                _admissible_selector_equivalence_classes(authority, projection)
            )
            errors.extend(selector_errors)
            inventory["legal_selection_equivalence_class_count"] += len(classes)
            for key in (
                "positive_selector_case_count",
                "nearest_negative_case_count",
            ):
                inventory[key] += selector_stats[key]
            for key in (
                "over_max_rejection_count",
                "unauthorized_exact_rejection_count",
                "duplicate_exact_rejection_count",
                "nearest_negative_leak_count",
            ):
                forbidden[key] += selector_stats[key]
            receipt_replay_count += selector_stats["receipt_replay_count"]

            (
                professional_envelopes,
                professional_dominated,
                forbidden_indexes,
                professional_conflicts,
                professional_subset_count,
            ) = _reference_envelopes(
                [
                    (professional, entry)
                    for entry in _eligible_reference_entries(
                        professional_row,
                        profile,
                    )
                ],
                context_authority,
            )
            forbidden["index_reference_forbidden_count"] += forbidden_indexes
            inventory["professional_reference_conflict_count"] += (
                professional_conflicts
            )
            for envelope in professional_envelopes:
                decision = reference_context_admissibility_decisions(
                    context_authority,
                    references=[
                        (reference_owner, entry["path"])
                        for reference_owner, entry in envelope
                    ],
                    path="analyzed",
                )
                if decision["failure_id"] == "context-reference-conflict":
                    forbidden["reference_conflict_leak_count"] += 1
            for envelope in professional_envelopes:
                for reference_owner, entry in envelope:
                    professional_reference_ids.add(
                        (reference_owner, profile, entry["path"])
                    )
            inventory["dominated_reference_subset_count"] += (
                professional_subset_count - len(professional_envelopes)
            )

            if profile == "analysis-agent":
                budget_class = "analysis"
            elif profile == "review-agent":
                budget_class = "review"
            elif owner == "engineering-brief":
                budget_class = "analyzed_task"
            else:
                budget_class = "task"
            capsule = capsule_envelopes.get(budget_class)
            if capsule is None:
                errors.append(
                    f"admissible composition lacks {budget_class} Capsule envelope"
                )
                continue

            for selected_class in classes:
                selected = selected_class["selected_layer3"]
                inventory["layer3_cardinality_counts"][str(len(selected))] += 1
                foundations = [item for item in selected if item not in domain_names]
                domains = [item for item in selected if item in domain_names]
                if profile == "analysis-agent" and foundations and domains:
                    required_coverage["analysis_foundation_domain"] = True
                if (
                    profile == "task-agent"
                    and owner == "engineering-brief"
                    and len(selected) == 3
                ):
                    required_coverage["analyzed_task_three_layer3"] = True
                if profile == "review-agent" and foundations and domains:
                    required_coverage["review_domain_foundation"] = True

                nested_entries: list[tuple[str, dict[str, Any]]] = []
                for layer3_name in selected:
                    row = layer3_rows[layer3_name]
                    for entry in _eligible_reference_entries(row, profile):
                        if entry.get("type") == "index":
                            forbidden["index_reference_forbidden_count"] += 1
                            continue
                        nested_entries.append((layer3_name, entry))
                        nested_reference_ids.add(
                            (layer3_name, profile, entry["path"])
                        )
                        if entry.get("type") == "targeted":
                            required_coverage["nested_targeted_references"] = True
                (
                    nested_envelopes,
                    nested_dominated,
                    nested_forbidden_indexes,
                    nested_conflicts,
                    nested_subset_count,
                ) = _reference_envelopes(nested_entries, context_authority)
                forbidden["index_reference_forbidden_count"] += (
                    nested_forbidden_indexes
                )
                inventory["legal_nested_reference_combination_count"] += (
                    nested_subset_count
                )
                inventory["dominated_reference_subset_count"] += (
                    nested_dominated
                )
                inventory["professional_reference_conflict_count"] += (
                    nested_conflicts
                )

                for build_profile, manifest in manifests.items():
                    primary_path = (
                        DIST_SKILLS / build_profile / professional / "SKILL.md"
                    )
                    if not primary_path.is_file():
                        errors.append(
                            f"missing admissible Professional {_relative(primary_path)}"
                        )
                        continue
                    layer3_components: list[dict[str, Any]] = []
                    failed = False
                    for layer3_name in selected:
                        try:
                            layer3_path = _layer3_path(
                                build_profile,
                                professional,
                                layer3_name,
                                manifest,
                            )
                        except ValueError as exc:
                            errors.append(str(exc))
                            failed = True
                            break
                        layer3_components.append(
                            file_component("layer3", layer3_path)
                        )
                    if failed:
                        continue
                    nested_component_rows: dict[
                        tuple[str, str], tuple[str, dict[str, Any]]
                    ] = {}
                    for layer3_name, entry in nested_entries:
                        logical_id = f"{layer3_name}/{entry['path']}"
                        try:
                            nested_path = _layer3_reference_path(
                                build_profile,
                                professional,
                                logical_id,
                                manifest,
                            )
                        except (FixtureCapsuleError, ValueError) as exc:
                            errors.append(str(exc))
                            failed = True
                            break
                        if nested_path.name in {"index.md", "catalog.md"}:
                            forbidden["index_or_catalog_load_count"] += 1
                        nested_component_rows[(layer3_name, entry["path"])] = (
                            logical_id,
                            file_component("layer3_reference", nested_path),
                        )
                    if failed:
                        continue
                    nested_component_envelopes = [
                        [
                            nested_component_rows[(reference_owner, entry["path"])]
                            for reference_owner, entry in envelope
                        ]
                        for envelope in nested_envelopes
                    ]

                    for host in (profile_variants[profile][0],):
                        profile_path = profile_variants[profile][1]
                        for professional_envelope in professional_envelopes:
                            for nested_envelope, nested_source_envelope in zip(
                                nested_component_envelopes,
                                nested_envelopes,
                                strict=True,
                            ):
                                selected_references = [
                                    (reference_owner, entry["path"])
                                    for reference_owner, entry in professional_envelope
                                ] + [
                                    (reference_owner, entry["path"])
                                    for reference_owner, entry in nested_source_envelope
                                ]
                                composition_path = (
                                    "direct"
                                    if budget_class == "task"
                                    or (
                                        budget_class == "review"
                                        and owner == "main-control-agent"
                                    )
                                    else "analyzed"
                                )
                                reachability = (
                                    reference_context_admissibility_decisions(
                                        context_authority,
                                        references=selected_references,
                                        path=composition_path,
                                    )
                                )
                                if not reachability["reachable"]:
                                    inventory["path_excluded_composition_count"] += 1
                                    failure_id = reachability["failure_id"]
                                    path_exclusions = inventory["path_exclusions"]
                                    path_exclusions[failure_id] = (
                                        path_exclusions.get(failure_id, 0) + 1
                                    )
                                    if (
                                        composition_path == "direct"
                                        and professional == "backend-change-builder"
                                        and {
                                            "domain-object-identification",
                                            "filesystem-process-safety",
                                        }
                                        <= set(selected)
                                    ):
                                        required_coverage[
                                            "direct_false_worst_excluded"
                                        ] = True
                                    continue
                                carrier_fields = (
                                    context_authority["carrier_fields"][profile][
                                        "engineering-brief"
                                    ]
                                    if profile in {"task-agent", "review-agent"}
                                    and owner == "engineering-brief"
                                    else []
                                )
                                staged_plan = reference_context_staged_plan(
                                    context_authority,
                                    references=selected_references,
                                    path=composition_path,
                                    profile=profile,
                                    selection_owner=owner,
                                    available_carrier_fields=carrier_fields,
                                    receipt_replayed=True,
                                    brief_current=owner == "engineering-brief",
                                    review_fresh=(
                                        profile != "review-agent"
                                        or owner == "engineering-brief"
                                    ),
                                )
                                if not staged_plan["reachable"]:
                                    inventory["carrier_failure_count"] += 1
                                    errors.append(
                                        "admissible composition rejected a current "
                                        f"carrier for {professional}:{profile}:{owner}: "
                                        f"{staged_plan['failure_id']}"
                                    )
                                    continue
                                selected_union = {
                                    tuple(reference)
                                    for reference in staged_plan["selected_union"]
                                }
                                loaded_union = {
                                    tuple(reference)
                                    for reference in staged_plan["loaded_union"]
                                }
                                carried_union = {
                                    tuple(reference)
                                    for reference in staged_plan[
                                        "carried_predecessors"
                                    ]
                                }
                                receipt_rows = staged_plan[
                                    "required_output_receipts"
                                ]
                                receipt_union = {
                                    tuple(receipt["reference"])
                                    for receipt in receipt_rows
                                }
                                receipts_complete = all(
                                    isinstance(receipt.get("required_outputs"), list)
                                    and bool(receipt["required_outputs"])
                                    for receipt in receipt_rows
                                )
                                if selected_union != loaded_union:
                                    inventory[
                                        "dropped_reference_obligation_count"
                                    ] += 1
                                    errors.append(
                                        "admissible staged composition dropped a "
                                        f"Reference obligation for {professional}:"
                                        f"{profile}:{owner}"
                                    )
                                    continue
                                if (
                                    receipt_union != selected_union
                                    or not receipts_complete
                                ):
                                    inventory[
                                        "required_output_receipt_failure_count"
                                    ] += 1
                                    errors.append(
                                        "admissible staged composition dropped a "
                                        f"required-output receipt for {professional}:"
                                        f"{profile}:{owner}"
                                    )
                                    continue
                                inventory["maximum_selected_reference_count"] = max(
                                    inventory["maximum_selected_reference_count"],
                                    len(selected_union),
                                )
                                inventory["valid_carried_predecessor_count"] += len(
                                    carried_union
                                )
                                inventory["required_output_receipt_count"] += len(
                                    receipt_rows
                                )

                                professional_component_rows: dict[
                                    tuple[str, str], dict[str, Any]
                                ] = {}
                                reference_failed = False
                                for reference_owner, entry in professional_envelope:
                                    try:
                                        reference_path = _professional_reference_path(
                                            build_profile,
                                            reference_owner,
                                            entry["path"],
                                        )
                                    except ValueError as exc:
                                        errors.append(str(exc))
                                        reference_failed = True
                                        break
                                    professional_component_rows[
                                        (reference_owner, entry["path"])
                                    ] = file_component(
                                        "targeted_reference",
                                        reference_path,
                                    )
                                if reference_failed:
                                    continue
                                for stage in staged_plan["stages"]:
                                    loaded_references = {
                                        tuple(reference)
                                        for reference in stage["loaded_references"]
                                    }
                                    carried_predecessors = {
                                        tuple(reference)
                                        for reference in stage[
                                            "carried_predecessors"
                                        ]
                                    }
                                    components = [
                                        file_component(
                                            "worker_profile",
                                            profile_path,
                                        ),
                                        file_component("primary_skill", primary_path),
                                    ]
                                    loaded_paths: list[str] = [
                                        _relative(profile_path),
                                        _relative(primary_path),
                                    ]
                                    for reference, component in (
                                        professional_component_rows.items()
                                    ):
                                        if reference not in loaded_references:
                                            continue
                                        components.append(component)
                                        loaded_paths.append(component["path"])
                                    components.extend(layer3_components)
                                    loaded_paths.extend(
                                        item["path"] for item in layer3_components
                                    )
                                    loaded_nested_logical_ids: list[str] = []
                                    for reference, (
                                        logical_id,
                                        component,
                                    ) in nested_component_rows.items():
                                        if reference not in loaded_references:
                                            continue
                                        components.append(component)
                                        loaded_paths.append(component["path"])
                                        loaded_nested_logical_ids.append(logical_id)
                                    components.append(capsule)
                                    loaded_paths.append(capsule["path"])
                                    inventory["candidate_composition_count"] += len(
                                        HOST_PROFILE_ROOTS
                                    )
                                    inventory["host_variant_dominated_count"] += (
                                        len(HOST_PROFILE_ROOTS) - 1
                                    )
                                    inventory["stage_measurement_count"] += 1
                                    component_score = sum(
                                        component["tokens"]
                                        for component in components
                                    )
                                    equivalence_key = (
                                        professional,
                                        profile,
                                        owner,
                                        len(selected),
                                        len(foundations),
                                        len(domains),
                                        tuple(sorted(selected_union)),
                                        stage["stage"],
                                        tuple(sorted(loaded_references)),
                                        tuple(sorted(carried_predecessors)),
                                    )
                                    render_signature = tuple(
                                        (component["kind"], component["sha256"])
                                        for component in components
                                    )
                                    candidate = {
                                        "component_score": component_score,
                                        "component_upper_bound": _component_upper_bound(
                                            components
                                        ),
                                        "render_signature": render_signature,
                                        "host": host,
                                        "build_profile": build_profile,
                                        "profile": profile,
                                        "selection_owner": owner,
                                        "professional_skill": professional,
                                        "selected_layer3": list(selected),
                                        "selected_layer3_references": sorted(
                                            loaded_nested_logical_ids
                                        ),
                                        "selected_reference_union": [
                                            list(reference)
                                            for reference in sorted(selected_union)
                                        ],
                                        "loaded_reference_union": [
                                            list(reference)
                                            for reference in sorted(loaded_union)
                                        ],
                                        "stage": stage["stage"],
                                        "stage_loaded_references": [
                                            list(reference)
                                            for reference in sorted(
                                                loaded_references
                                            )
                                        ],
                                        "stage_carried_predecessors": [
                                            list(reference)
                                            for reference in sorted(
                                                carried_predecessors
                                            )
                                        ],
                                        "stage_required_output_receipts": stage[
                                            "required_output_receipts"
                                        ],
                                        "carrier_validated": staged_plan[
                                            "carrier_validated"
                                        ],
                                        "foundation": foundations,
                                        "domain": domains,
                                        "loaded_paths": loaded_paths,
                                        "receipt_sha256": selected_class["receipt"][
                                            "receipt_sha256"
                                        ],
                                        "components": components,
                                    }
                                    loaded_reference_count = len(loaded_references)
                                    inventory[
                                        "maximum_loaded_reference_count"
                                    ] = max(
                                        inventory[
                                            "maximum_loaded_reference_count"
                                        ],
                                        loaded_reference_count,
                                    )
                                    if loaded_reference_count >= 4:
                                        inventory[
                                            "four_plus_reference_measurement_count"
                                        ] += 1
                                    current = canonical_candidates[
                                        budget_class
                                    ].get(equivalence_key)
                                    candidate_rank = (
                                        component_score,
                                        candidate["component_upper_bound"],
                                        render_signature,
                                    )
                                    current_rank = (
                                        (
                                            current["component_score"],
                                            current["component_upper_bound"],
                                            current["render_signature"],
                                        )
                                        if current is not None
                                        else None
                                    )
                                    if (
                                        current_rank is None
                                        or candidate_rank > current_rank
                                    ):
                                        canonical_candidates[budget_class][
                                            equivalence_key
                                        ] = candidate
                                    inventory[
                                        "upper_bound_dominated_count"
                                    ] += int(current is not None)

    dominance_frontier = _dominance_frontier_projection(
        canonical_candidates=canonical_candidates,
        authority=authority,
        control_projections=control_projections,
    )
    consumer_boundary = dominance_frontier["consumer_boundary"]
    if not consumer_boundary["projection_only"]:
        errors.append(
            "dominance frontier must remain eval-only; runtime/build consumer found"
        )
    exact_measurement_cache: dict[
        tuple[str, tuple[tuple[str, str], ...]],
        dict[str, Any],
    ] = {}
    for budget_class, candidates_by_class in canonical_candidates.items():
        for equivalence_key, candidate in sorted(
            candidates_by_class.items(),
            key=lambda item: (
                -item[1]["component_upper_bound"],
                repr(item[0]),
            ),
        ):
            maximum = maxima[budget_class]
            if (
                maximum is not None
                and candidate["component_upper_bound"] <= maximum["tokens"]
            ):
                inventory["upper_bound_dominated_count"] += 1
                continue
            cache_key = (budget_class, candidate["render_signature"])
            measurement = exact_measurement_cache.get(cache_key)
            if measurement is None:
                measurement = _measure_context(
                    candidate["components"],
                    budget_class=budget_class,
                )
                exact_measurement_cache[cache_key] = measurement
                inventory["exact_measurement_count"] += 1
            result = {
                "tokens": measurement["total_tokens"],
                "sum_component_tokens": measurement["sum_component_tokens"],
                "component_upper_bound_tokens": candidate[
                    "component_upper_bound"
                ],
                "soft_target": measurement["soft_target"],
                "hard_ceiling": measurement["hard_ceiling"],
                "within_soft_target": measurement["within_soft_target"],
                "within_hard_ceiling": measurement["within_hard_ceiling"],
                "soft_margin_tokens": measurement["soft_margin_tokens"],
                "hard_margin_tokens": measurement["hard_margin_tokens"],
                "budget_signal": measurement["budget_signal"],
                "within_duplicate_budget": measurement[
                    "within_duplicate_budget"
                ],
                "route_obligations_preserved": True,
                "host": candidate["host"],
                "build_profile": candidate["build_profile"],
                "profile": candidate["profile"],
                "selection_owner": candidate["selection_owner"],
                "professional_skill": candidate["professional_skill"],
                "selected_layer3": candidate["selected_layer3"],
                "selected_layer3_references": candidate[
                    "selected_layer3_references"
                ],
                "selected_reference_union": candidate[
                    "selected_reference_union"
                ],
                "loaded_reference_union": candidate[
                    "loaded_reference_union"
                ],
                "stage": candidate["stage"],
                "stage_loaded_references": candidate[
                    "stage_loaded_references"
                ],
                "stage_carried_predecessors": candidate[
                    "stage_carried_predecessors"
                ],
                "stage_required_output_receipts": candidate[
                    "stage_required_output_receipts"
                ],
                "carrier_validated": candidate["carrier_validated"],
                "foundation": candidate["foundation"],
                "domain": candidate["domain"],
                "loaded_paths": candidate["loaded_paths"],
                "receipt_sha256": candidate["receipt_sha256"],
                "canonical_reduction_key": [
                    str(value) for value in equivalence_key
                ],
            }
            if maximum is None or result["tokens"] > maximum["tokens"]:
                maxima[budget_class] = result

    inventory["owner_surface_count"] = surface_count
    inventory["canonical_representative_count"] = sum(
        len(candidates) for candidates in canonical_candidates.values()
    )
    inventory["coverage_mapping_count"] = inventory[
        "candidate_composition_count"
    ]
    inventory["professional_reference_count"] = len(professional_reference_ids)
    inventory["nested_reference_count"] = len(nested_reference_ids)
    for name, covered in required_coverage.items():
        if not covered:
            errors.append(f"admissible composition coverage missing {name}")
    if forbidden["nearest_negative_leak_count"]:
        errors.append("admissible composition nearest-negative selection leaked")
    if forbidden["index_or_catalog_load_count"]:
        errors.append("admissible composition loaded an index or catalog")
    if forbidden["reference_conflict_leak_count"]:
        errors.append("admissible composition loaded conflicting References")
    if forbidden["over_max_rejection_count"] == 0:
        errors.append("admissible composition did not prove >3 fail-closed")
    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        maximum = maxima[budget_class]
        if maximum is None:
            errors.append(f"admissible composition lacks {budget_class} measurement")
            continue
        if not maximum["within_duplicate_budget"]:
            errors.append(
                f"admissible composition {budget_class} duplicate budget failed"
            )

    return {
        "contract": ADMISSIBLE_COMPOSITION_CONTRACT,
        "parallel_catalog": False,
        "source_scope": {
            "registries": [
                _relative(PROFESSIONAL_REGISTRY),
                _relative(FOUNDATION_REGISTRY),
                _relative(DOMAIN_REGISTRY),
            ],
            "selector_authority": (
                "scripts/validation_utils.py::layer3_selector_authority"
            ),
            "selector_consumer": (
                "scripts/validation_utils.py::"
                "layer3_selector_runtime_selection_receipt"
            ),
            "build_projection": "dist/*/.changeforge-build-manifest.json",
            "capsule_source": _relative(FIXTURES),
            "reference_reduction": (
                "every registry role-compatible non-index subset maps to a "
                "maximal legal selected union; independent References remain "
                "singleton resident stages and only reciprocal must-co-trigger "
                "components share residency"
            ),
            "canonical_reduction": (
                "professional/profile/owner, Layer 3 cardinality, "
                "Foundation/Domain shape, Professional Reference envelope, and "
                "nested Reference shape; each stratum retains the highest "
                "source-component token score"
            ),
        },
        "selector_authority_inventory": authority["inventory"],
        "inventory": inventory,
        "required_coverage": required_coverage,
        "max_by_budget_class": maxima,
        "dominance_frontier": dominance_frontier,
        "obligation_preservation": {
            "professional_preserved": all(
                maximum is not None and bool(maximum["professional_skill"])
                for maximum in maxima.values()
            ),
            "domain_authorization_preserved": all(
                maximum is not None
                and set(maximum["domain"])
                <= set(
                    authority["runtime_professionals"][
                        maximum["professional_skill"]
                    ]["domain_authorization"]
                )
                for maximum in maxima.values()
            ),
            "review_selection_independent": all(
                surface["selection_basis"] == "review-risk"
                for document in control_projections.values()
                for surface in document["selection_surfaces"]
                if surface["profile"] == "review-agent"
            ),
            "receipts_replayed": receipt_replay_count == surface_count,
            "route_once_input_only": True,
            "routing_classification_calls": 0,
            "staged_reference_obligations_preserved": (
                inventory["dropped_reference_obligation_count"] == 0
                and inventory["required_output_receipt_failure_count"] == 0
                and inventory["carrier_failure_count"] == 0
            ),
        },
        "forbidden_combinations": forbidden,
        "proof_limits": [
            "Selector equivalence classes use declarative positive and nearest-negative signals; the evaluator does not classify task prose.",
            "Reference subset coverage is a conservative role-compatible upper envelope; registry indexes and catalogs are forbidden and mode contracts remain isolated.",
            "Capsule contribution uses the largest validated checked-in fixture Capsule per budget class, not arbitrary future user prose.",
            "Every legal render candidate maps to one source-derived reduction stratum; exact tokenization is memoized by ordered component fingerprint and applied to the highest component-token representative of every stratum.",
            "Sequenced Reference stages are source-owned; only canonically replayed engineering-brief Task/Review carriers may replace a predecessor body, while other owner surfaces conservatively co-load.",
            "Reported maxima are exact for the deterministic canonical representatives; the full inventory count and dominance mapping remain available separately.",
        ],
        "errors": errors,
    }


def _budget_governance_report(
    *,
    mode: str,
    main_contexts: list[dict[str, Any]],
    dispatch_measurements: list[dict[str, Any]],
    admissible_context_compositions: dict[str, Any],
) -> dict[str, Any]:
    if mode not in {"calibration", "conformance"}:
        raise ValueError("rendered context mode must be calibration or conformance")

    populations: dict[str, dict[str, int | None]] = {
        "main": _token_distribution(
            [measurement["total_tokens"] for measurement in main_contexts]
        ),
        "utility": _token_distribution(
            [
                measurement["total_tokens"]
                for measurement in dispatch_measurements
                if measurement["budget_class"] == "utility"
            ]
        ),
    }
    dominance_rows = admissible_context_compositions["dominance_frontier"][
        "budget_classes"
    ]
    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        populations[budget_class] = dominance_rows[budget_class][
            "token_distribution"
        ]

    maxima: dict[str, dict[str, Any] | None] = {
        "main": max(
            main_contexts,
            key=lambda measurement: measurement["total_tokens"],
            default=None,
        ),
        "utility": max(
            (
                measurement
                for measurement in dispatch_measurements
                if measurement["budget_class"] == "utility"
            ),
            key=lambda measurement: measurement["total_tokens"],
            default=None,
        ),
        **admissible_context_compositions["max_by_budget_class"],
    }
    advisories: list[dict[str, Any]] = []
    hard_overages: list[dict[str, Any]] = []
    for budget_class in CONTEXT_BUDGET_LIMITS:
        maximum = maxima.get(budget_class)
        if maximum is None:
            continue
        tokens = maximum.get("total_tokens", maximum.get("tokens"))
        if not isinstance(tokens, int):
            continue
        limit = CONTEXT_BUDGET_LIMITS[budget_class]
        if tokens > limit["soft_target"]:
            advisories.append(
                {
                    "budget_class": budget_class,
                    "tokens": tokens,
                    "soft_target": limit["soft_target"],
                    "overage_tokens": tokens - limit["soft_target"],
                }
            )
        if tokens > limit["hard_ceiling"]:
            hard_overages.append(
                {
                    "budget_class": budget_class,
                    "tokens": tokens,
                    "hard_ceiling": limit["hard_ceiling"],
                    "overage_tokens": tokens - limit["hard_ceiling"],
                }
            )

    distributions = {
        budget_class: populations[budget_class]
        for budget_class in CONTEXT_BUDGET_LIMITS
    }
    dominance_frontier = admissible_context_compositions["dominance_frontier"]
    main_utility_rows = _main_utility_selection_rows(
        main_contexts,
        dispatch_measurements,
    )
    population_identity = {
        "admissible_composition_candidates": {
            "budget_classes": list(ADMISSIBLE_BUDGET_CLASSES),
            "mapping_row_count": dominance_frontier["mapping_row_count"],
            "mapping_digest": dominance_frontier["mapping_digest"],
        },
        "main_and_utility_candidates": main_utility_rows,
    }
    selection_count = sum(
        int(distribution["count"] or 0) for distribution in distributions.values()
    )
    bound_selection_count = (
        dominance_frontier["mapping_row_count"] + len(main_utility_rows)
    )
    if bound_selection_count != selection_count:
        raise ValueError(
            "selection identity coverage does not match measured valid-candidate count: "
            f"bound={bound_selection_count}, measured={selection_count}"
        )
    return {
        "mode": mode,
        "source": "src/control-model/core-contracts.json#/context_budget_contract",
        "policy_status": CONTEXT_BUDGET_MODEL["policy_status"],
        "soft_targets": {
            key: value["soft_target"]
            for key, value in CONTEXT_BUDGET_LIMITS.items()
        },
        "hard_ceilings": {
            key: value["hard_ceiling"]
            for key, value in CONTEXT_BUDGET_LIMITS.items()
        },
        "selection_contract": {
            "otherwise_valid_candidates_only": True,
            "budget_applied_to_candidate_selection": False,
            "budget_applied_to_frontier": False,
            "soft_target_applied_to_exit": False,
            "hard_ceiling_applied_to_exit": mode == "conformance",
            "selection_count": selection_count,
            "selection_identity_sha256": _calibration_selection_identity(
                population_identity,
                CONTEXT_BUDGET_MODEL,
            ),
            "identity_excludes_budget_fields": ["soft_target", "hard_ceiling"],
        },
        "distributions": distributions,
        "growth_distributions": {
            budget_class: _unavailable_growth_distribution()
            for budget_class in CONTEXT_BUDGET_LIMITS
        },
        "growth_advisories": advisories,
        "hard_ceiling_overages": hard_overages,
        "conformance_failures": hard_overages if mode == "conformance" else [],
        "duplicate_rule_token_ratio_max": DUPLICATE_TOKEN_RATIO_MAX,
    }


def evaluate(mode: str = "conformance") -> dict[str, Any]:
    errors: list[str] = []
    try:
        document = json.loads(FIXTURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read trajectory fixture {FIXTURES}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("trajectory fixture root must be a mapping")
    if document.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        raise ValueError(
            f"trajectory fixture schema_version must be {FIXTURE_SCHEMA_VERSION}"
        )
    cases = _fixture_cases(document)
    expected_case_ids = {str(case.get("id") or "") for _group, case in cases}
    long_task_ids, semantic_equality = _load_lightweight_prerequisite(
        expected_case_ids
    )
    layer3_entries = _layer3_registry_entries()
    manifests = _load_manifests(errors)
    if set(manifests) != set(BUILD_PROFILES):
        raise ValueError("all recommended/full/dev build manifests are required")

    prompt_tokens = count_o200k_base_tokens(CONTROL_PROMPT.read_text(encoding="utf-8"))
    main_contexts: list[dict[str, Any]] = []
    for host in HOST_PROFILE_ROOTS:
        profile_path = _profile_path(host, "main-control-agent")
        if not profile_path.is_file():
            errors.append(f"missing rendered Profile {_relative(profile_path)}")
            continue
        for build_profile in BUILD_PROFILES:
            _validate_profile_digest(
                host,
                "main-control-agent",
                profile_path,
                manifests[build_profile],
                errors,
            )
            control_skill = DIST_SKILLS / build_profile / "engineering-control-plane" / "SKILL.md"
            if not control_skill.is_file():
                errors.append(f"missing built Control Skill {_relative(control_skill)}")
                continue
            measurement = _measure_context(
                [
                    _file_component("rendered_main_profile", profile_path),
                    _file_component("control_skill", control_skill),
                ],
                budget_class="main",
            )
            measurement.update(
                {
                    "host": host,
                    "build_profile": build_profile,
                    "embedded_control_prompt_tokens": prompt_tokens,
                    "control_prompt_accounting": (
                        "included in rendered_main_profile and not added as a separate component"
                    ),
                }
            )
            if not measurement["within_duplicate_budget"]:
                errors.append(
                    f"main:{host}:{build_profile} duplicate ratio "
                    f"{measurement['duplicate_rule_token_ratio']:.3f} exceeds "
                    f"{DUPLICATE_TOKEN_RATIO_MAX:.2f}"
                )
            main_contexts.append(measurement)

    case_results: list[dict[str, Any]] = []
    dispatch_count = 0
    measurement_count = 0
    for fixture_group, case in cases:
        case_id = str(case.get("id") or "")
        if not case_id:
            errors.append(f"{fixture_group} fixture has no id")
            continue
        steps = case.get("steps")
        if not isinstance(steps, list):
            errors.append(f"{case_id}: steps must be a list")
            continue
        dispatch_results: list[dict[str, Any]] = []
        for index, raw_step in enumerate(steps):
            if not isinstance(raw_step, dict) or raw_step.get("action") != "dispatch":
                continue
            dispatch_count += 1
            step_errors = _dispatch_metadata_errors(case_id, index, raw_step)
            step_errors.extend(
                f"{case_id}: dispatch step {index} {error}"
                for error in trace_execution_level_migration_errors(steps, index)
            )
            step_errors.extend(
                _layer3_reference_registry_errors(
                    case_id, index, raw_step, layer3_entries
                )
            )
            errors.extend(step_errors)
            if step_errors:
                continue
            canonical_capsule = validate_and_render_fixture_capsule(raw_step)
            role = str(raw_step.get("profile"))
            primary = str(raw_step.get("primary_skill") or "")
            layer3 = raw_step.get("layer3_skills", [])
            if not isinstance(layer3, list):
                errors.append(f"{case_id}: dispatch step {index} layer3_skills must be a list")
                continue
            layer3_references = raw_step.get("layer3_references")
            if "utility_capsule" in raw_step:
                layer3_references = []
            elif not isinstance(layer3_references, list):
                errors.append(
                    f"{case_id}: dispatch step {index} layer3_references must be a list"
                )
                continue
            references = raw_step["professional_references"]
            budget_class = _budget_class(
                raw_step,
                str(case.get("kind") or ""),
                steps,
            )
            for host in HOST_PROFILE_ROOTS:
                profile_path = _profile_path(host, role)
                if not profile_path.is_file():
                    errors.append(f"missing rendered Profile {_relative(profile_path)}")
                    continue
                for build_profile in BUILD_PROFILES:
                    _validate_profile_digest(
                        host,
                        role,
                        profile_path,
                        manifests[build_profile],
                        errors,
                    )
                    components = [_file_component("worker_profile", profile_path)]
                    manifest = manifests[build_profile]
                    if primary:
                        primary_path = DIST_SKILLS / build_profile / primary / "SKILL.md"
                        if not primary_path.is_file():
                            errors.append(f"missing primary Skill {_relative(primary_path)}")
                            continue
                        components.append(_file_component("primary_skill", primary_path))
                        reference_failed = False
                        for reference in references:
                            try:
                                reference_path = _professional_reference_path(
                                    build_profile, primary, reference
                                )
                            except ValueError as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                reference_failed = True
                                break
                            if not reference_path.is_file():
                                errors.append(
                                    f"{case_id}: dispatch step {index} missing reference "
                                    f"{_relative(reference_path)}"
                                )
                                reference_failed = True
                                break
                            reference_kind = (
                                "mode_reference"
                                if primary == "engineering-change-analysis"
                                and reference == MODE_REFERENCES.get(raw_step.get("mode"))
                                else "targeted_reference"
                            )
                            components.append(_file_component(reference_kind, reference_path))
                        if reference_failed:
                            continue
                        layer3_failed = False
                        for name in layer3:
                            try:
                                layer3_path = _layer3_path(
                                    build_profile, primary, str(name), manifest
                                )
                            except ValueError as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                layer3_failed = True
                                break
                            if not layer3_path.is_file():
                                errors.append(
                                    f"{case_id}: dispatch step {index} missing Layer 3 artifact "
                                    f"{_relative(layer3_path)}"
                                )
                                layer3_failed = True
                                break
                            components.append(_file_component("layer3", layer3_path))
                        if layer3_failed:
                            continue
                        layer3_reference_failed = False
                        for logical_id in layer3_references:
                            try:
                                nested_path = _layer3_reference_path(
                                    build_profile,
                                    primary,
                                    str(logical_id),
                                    manifest,
                                )
                            except (FixtureCapsuleError, ValueError) as exc:
                                errors.append(f"{case_id}: dispatch step {index}: {exc}")
                                layer3_reference_failed = True
                                break
                            if not nested_path.is_file() or _uses_symlink(
                                nested_path, DIST_SKILLS / build_profile
                            ):
                                errors.append(
                                    f"{case_id}: dispatch step {index} missing or symlinked "
                                    f"Layer 3 Reference {_relative(nested_path)}"
                                )
                                layer3_reference_failed = True
                                break
                            components.append(
                                _file_component("layer3_reference", nested_path)
                            )
                        if layer3_reference_failed:
                            continue
                    components.append(
                        _component(
                            "dispatch_capsule",
                            f"fixture:{case_id}:step:{index}:canonical-capsule",
                            canonical_capsule,
                        )
                    )
                    measurement = _measure_context(
                        components,
                        budget_class=budget_class,
                    )
                    measurement.update(
                        {
                            "host": host,
                            "build_profile": build_profile,
                            "step": index,
                            "role": role,
                            "mode": raw_step["mode"],
                            "primary_skill": primary or None,
                            "layer3_skills": [str(item) for item in layer3],
                            "layer3_references": [
                                str(item) for item in layer3_references
                            ],
                            "loaded_layer3_reference_count": len(layer3_references),
                            "loaded_layer3_reference_logical_ids": [
                                str(item) for item in layer3_references
                            ],
                            "professional_references": list(references),
                            "capsule_contract_version": FIXTURE_CAPSULE_CONTRACT_VERSION,
                            "canonical_capsule_sha256": raw_step["fixture_capsule"][
                                "canonical_sha256"
                            ],
                            "canonical_capsule_tokens": count_o200k_base_tokens(
                                canonical_capsule
                            ),
                        }
                    )
                    if not measurement["within_duplicate_budget"]:
                        errors.append(
                            f"{case_id}:step:{index}:{host}:{build_profile} duplicate ratio "
                            f"{measurement['duplicate_rule_token_ratio']:.3f} exceeds "
                            f"{DUPLICATE_TOKEN_RATIO_MAX:.2f}"
                        )
                    dispatch_results.append(measurement)
                    measurement_count += 1
        case_results.append(
            {
                "id": case_id,
                "fixture_group": fixture_group,
                "dispatch_count": sum(
                    isinstance(step, dict) and step.get("action") == "dispatch"
                    for step in steps
                ),
                "measurements": dispatch_results,
            }
        )

    discovery = [
        _discovery_metadata(build_profile, errors)
        for build_profile in BUILD_PROFILES
    ]
    all_dispatch_measurements = [
        item
        for case in case_results
        for item in case["measurements"]
    ]
    fixture_layer3_reference_ids = [
        str(logical_id)
        for _fixture_group, case in cases
        for step in case.get("steps", [])
        if isinstance(step, dict) and step.get("action") == "dispatch"
        for logical_id in step.get("layer3_references", [])
    ]
    max_by_class: dict[str, dict[str, Any] | None] = {}
    for budget_class in ("analysis", "task", "analyzed_task", "review", "utility"):
        candidates = [
            item for item in all_dispatch_measurements if item["budget_class"] == budget_class
        ]
        maximum = max(candidates, key=lambda item: item["total_tokens"], default=None)
        max_by_class[budget_class] = _maximum_summary(
            maximum,
            include_dispatch=True,
        )
    max_main = max(main_contexts, key=lambda item: item["total_tokens"], default=None)
    duplicate_candidates = [*main_contexts, *all_dispatch_measurements]
    max_duplicate = max(
        duplicate_candidates,
        key=lambda item: item["duplicate_rule_token_ratio"],
        default=None,
    )
    duplicate_block_examples = (
        list(max_duplicate.get("duplicate_blocks", []))[:10]
        if max_duplicate
        else []
    )
    transfer_rows = [
        _case_transfer_measurement(case)
        for _fixture_group, case in cases
        if case.get("kind") != "utility"
    ]
    transfer_by_id = {row["id"]: row for row in transfer_rows}
    if not long_task_ids.issubset(transfer_by_id):
        missing = sorted(long_task_ids - set(transfer_by_id))
        raise ValueError(
            "lightweight long-task selection includes unmeasured transfer cases: "
            f"{missing}"
        )
    transfer_aggregate = _aggregate_transfer_rows(transfer_rows)
    long_task_rows = []
    for case_id in sorted(long_task_ids):
        row = dict(transfer_by_id[case_id])
        row["required_progress_for_multi_agent"] = True
        long_task_rows.append(row)
    transferred_context = {
        "source_scope": {
            "trajectory_fixture": _relative(FIXTURES),
            "lightweight_long_task_selector": (
                f"{_relative(LIGHTWEIGHT_REPORT)}"
                "#/cases/*/metrics/required_progress_for_multi_agent"
            ),
            "canonical_capsule_renderer": "scripts/fixture_capsule_contract.py",
            "implementation_handoff_template": _relative(
                IMPLEMENTATION_HANDOFF_TEMPLATE
            ),
            "review_handoff_template": _relative(REVIEW_HANDOFF_TEMPLATE),
        },
        "accounting": {
            "denominator": "exclusive transfer occurrence token sum",
            "exclusive_categories": list(TRANSFER_EXCLUSIVE_CATEGORIES),
            "overlap_views": list(TRANSFER_OVERLAP_VIEWS),
            "category_views_do_not_sum_to_gross": True,
            "skill_reference_scope": "dispatch selectors, not loaded Skill bodies",
            "compressible_rule": (
                "post-compaction gross contains only accepted boundary projections; "
                "Authority, selectors, and authoritative task Capsules remain unchanged"
            ),
        },
        "semantic_baseline": semantic_equality,
        "measurement_kind": "candidate-subject-only",
        **transfer_aggregate,
        "measured_case_count": len(transfer_rows),
        "long_task_selector_join_count": len(long_task_rows),
        "long_task_rows": long_task_rows,
        "proof_limits": list(TRANSFER_PROOF_LIMITS),
    }
    if transfer_aggregate["categories"]["superseded_evidence"]["gross_tokens"]:
        errors.append("superseded evidence must not cross a transfer boundary")
    admissible_context_compositions = _evaluate_admissible_context_compositions(
        cases=cases,
        manifests=manifests,
    )
    errors.extend(admissible_context_compositions["errors"])
    budget_governance = _budget_governance_report(
        mode=mode,
        main_contexts=main_contexts,
        dispatch_measurements=all_dispatch_measurements,
        admissible_context_compositions=admissible_context_compositions,
    )
    component_catalog = _compact_component_catalog(duplicate_candidates)
    errors.extend(
        f"{item['budget_class']} context maximum {item['tokens']} exceeds Core hard ceiling {item['hard_ceiling']}"
        for item in budget_governance["conformance_failures"]
    )
    return {
        "schema_version": 2,
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-rendered-artifacts",
        "compiled_layer3_format": COMPILED_LAYER3_FORMAT,
        "tokenizer": "o200k_base",
        "fixture_capsule_contract": {
            "version": FIXTURE_CAPSULE_CONTRACT_VERSION,
            "source": "scripts/fixture_capsule_contract.py",
            "placement": "evaluator-only; excluded from build and installation artifacts",
            "hash_role": "detects unsynchronized canonical rendered text",
            "semantic_gate": (
                "field-specific prose, repository path/glob, command, input, "
                "explicit Layer 3 Reference logical ID, and Utility-schema minimums"
            ),
        },
        "limitations": list(LIMITATIONS),
        "build_profiles": list(BUILD_PROFILES),
        "hosts": list(HOST_PROFILE_ROOTS),
        "budget_governance": budget_governance,
        "fixture_count": len(case_results),
        "fixture_schema_version": document.get("schema_version"),
        "dispatch_count": dispatch_count,
        "measurement_count": measurement_count,
        "main_contexts": main_contexts,
        "discovery_metadata": discovery,
        "component_catalog": component_catalog,
        "cases": case_results,
        "transferred_context": transferred_context,
        "admissible_context_compositions": admissible_context_compositions,
        "aggregate": {
            "max_main": (
                _maximum_summary(max_main, include_dispatch=False)
            ),
            "max_by_budget_class": max_by_class,
            "max_duplicate_rule_token_ratio": (
                max_duplicate["duplicate_rule_token_ratio"] if max_duplicate else None
            ),
            "duplicate_rule_token_ratio_margin": (
                round(
                    DUPLICATE_TOKEN_RATIO_MAX
                    - max_duplicate["duplicate_rule_token_ratio"],
                    6,
                )
                if max_duplicate
                else None
            ),
            "max_discovery_metadata_tokens": max(
                (item["tokens"] for item in discovery), default=None
            ),
            "loaded_layer3_reference_count": len(fixture_layer3_reference_ids),
            "measured_layer3_reference_component_count": sum(
                item.get("loaded_layer3_reference_count", 0)
                for item in all_dispatch_measurements
            ),
            "loaded_layer3_reference_logical_ids": sorted(
                set(fixture_layer3_reference_ids)
            ),
            "duplicate_block_examples_from_max_ratio_context": duplicate_block_examples,
        },
        "errors": errors,
    }


def _selection_authority_projection_summary(
    cases: list[dict[str, Any]], subject: str
) -> dict[str, Any]:
    bundles: list[dict[str, Any]] = []
    loads = {
        "selector_load_count": 0,
        "reference_partition_load_count": 0,
        "reference_load_count": 0,
    }
    for case in cases:
        subject_bundles = case.get("selection_authority_bundles", {}).get(subject)
        structural = case.get("structural")
        if not isinstance(subject_bundles, list) or not isinstance(structural, dict):
            raise ValueError(
                f"end-to-end case omits {subject} selection authority projection"
            )
        for bundle in subject_bundles:
            if not isinstance(bundle, dict) or not isinstance(bundle.get("schema"), str):
                raise ValueError(
                    f"end-to-end case has invalid {subject} selection authority bundle"
                )
            bundles.append(bundle)
        for field in loads:
            values = structural.get(field)
            value = values.get(subject) if isinstance(values, dict) else None
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(
                    f"end-to-end case omits {subject} structural field {field}"
                )
            loads[field] += value
    schemas: dict[str, int] = {}
    for bundle in bundles:
        schema = bundle["schema"]
        schemas[schema] = schemas.get(schema, 0) + 1
    return {
        "bundle_count": len(bundles),
        "bundle_digest": _sha256_text(_canonical_json_text(bundles)),
        "schemas": dict(sorted(schemas.items())),
        **loads,
    }


def _end_to_end_projection_binding(comparison: dict[str, Any]) -> dict[str, Any]:
    payload = _canonical_json_text(comparison)
    aggregate = comparison.get("aggregate")
    cases = comparison.get("cases")
    subjects = comparison.get("subjects")
    host_matrix = comparison.get("host_matrix")
    if (
        not isinstance(aggregate, dict)
        or not isinstance(cases, list)
        or not isinstance(subjects, dict)
        or not isinstance(host_matrix, dict)
    ):
        raise ValueError("end-to-end comparison projection is incomplete")
    normalized_cases: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("end-to-end comparison case is not an object")
        normalized_cases.append(case)
    ordinary_regressions = comparison.get("ordinary_route_regressions", [])
    if not isinstance(ordinary_regressions, list) or any(
        not isinstance(row, dict) for row in ordinary_regressions
    ):
        raise ValueError("end-to-end ordinary route regressions are malformed")
    quality_cost_gate = comparison.get("quality_cost_gate")
    if not isinstance(quality_cost_gate, dict):
        quality_cost_gate = {
            "status": "not-collected",
            "verdict": "not_enough_evidence",
            "claim_boundary": "structural-only",
            "quality_preserved": False,
            "candidate_rejected": False,
            "cost_frontier": {"eligible": False, "status": "not-evaluated"},
            "live_evidence": {
                "behavior": "not_collected",
                "codegen": "not_collected",
                "elapsed_ms": "not_collected",
            },
        }
    return {
        "contract": "changeforge.end-to-end-cost-projection/v1",
        "comparison_sha256": _sha256_text(payload),
        "case_count": len(cases),
        "status": comparison.get("status"),
        "aggregate": dict(aggregate),
        "host_matrix": copy.deepcopy(host_matrix),
        "host_matrix_sha256": _sha256_text(_canonical_json_text(host_matrix)),
        "subject_identity_sha256": _sha256_text(_canonical_json_text(subjects)),
        "selection_authority_summary": {
            subject: _selection_authority_projection_summary(
                normalized_cases, subject
            )
            for subject in ("baseline", "candidate")
        },
        "ordinary_route_gate": {
            "rule": comparison.get("ordinary_route_comparison_rule"),
            "regression_count": len(ordinary_regressions),
            "regression_digest": _sha256_text(
                _canonical_json_text(ordinary_regressions)
            ),
            "regressions": copy.deepcopy(ordinary_regressions),
        },
        "quality_cost_gate": copy.deepcopy(quality_cost_gate),
    }


def _render_end_to_end_projection_markdown(comparison: dict[str, Any]) -> str:
    binding = _end_to_end_projection_binding(comparison)
    aggregate = binding["aggregate"]
    authority = binding["selection_authority_summary"]
    host_matrix = binding["host_matrix"]
    ordinary_gate = binding["ordinary_route_gate"]
    quality_gate = binding["quality_cost_gate"]
    authority_lines: list[str] = []
    for subject in ("baseline", "candidate"):
        summary = authority[subject]
        schemas = ", ".join(
            f"{schema}={count}" for schema, count in summary["schemas"].items()
        ) or "none"
        authority_lines.append(
            f"Selection authority {subject}: bundles **{summary['bundle_count']}**; "
            f"schemas **{schemas}**; selector/partition/reference loads "
            f"**{summary['selector_load_count']} / "
            f"{summary['reference_partition_load_count']} / "
            f"{summary['reference_load_count']}**."
        )
    ordinary_lines = [
        "Ordinary raw-route-equal regression "
        f"`{row.get('id')}` ({row.get('host')}): "
        f"**{row.get('total_task_tokens', {}).get('delta')} token(s)**."
        for row in ordinary_gate["regressions"]
    ]
    return "\n".join(
        [
            "## End-to-End Cost Gate",
            "",
            f"Contract: **{binding['contract']}**.",
            f"Comparison SHA-256: `{binding['comparison_sha256']}`.",
            f"Subject identity SHA-256: `{binding['subject_identity_sha256']}`.",
            f"Comparable cases: **{binding['case_count']}**; status: **{binding['status']}**.",
            "Quality-first verdict/boundary/frontier: "
            f"**{quality_gate.get('verdict')} / {quality_gate.get('claim_boundary')} / "
            f"{quality_gate.get('cost_frontier', {}).get('status')}**.",
            "Live behavior/codegen/elapsed evidence: "
            f"**{quality_gate.get('live_evidence', {}).get('behavior')} / "
            f"{quality_gate.get('live_evidence', {}).get('codegen')} / "
            f"{quality_gate.get('live_evidence', {}).get('elapsed_ms')}**.",
            "Host matrix logical/physical rows: "
            f"**{host_matrix.get('logical_case_count')} / "
            f"{host_matrix.get('host_pair_count')}**; digest "
            f"`{binding['host_matrix_sha256']}`.",
            "Host matrix reconciliation baseline/candidate/rows: "
            f"**{host_matrix.get('reconciliation', {}).get('baseline')} / "
            f"{host_matrix.get('reconciliation', {}).get('candidate')} / "
            f"{host_matrix.get('reconciliation', {}).get('host_pair_count')}**.",
            "Selection authority bundle digests: "
            f"baseline `{authority['baseline']['bundle_digest']}`; "
            f"candidate `{authority['candidate']['bundle_digest']}`.",
            *authority_lines,
            "Ordinary raw-route-equal gate regressions/digest: "
            f"**{ordinary_gate['regression_count']}** / "
            f"`{ordinary_gate['regression_digest']}`.",
            *ordinary_lines,
            "Aggregate baseline/candidate/delta: "
            f"**{aggregate.get('baseline')} / {aggregate.get('candidate')} / "
            f"{aggregate.get('delta')}**.",
            "",
        ]
    )


def _end_to_end_projection_binding_errors(
    comparison: dict[str, Any], markdown: str, binding: object
) -> list[str]:
    expected = _end_to_end_projection_binding(comparison)
    errors: list[str] = []
    if binding != expected:
        errors.append("rendered-context JSON end-to-end binding is stale")
    expected_markdown = _render_end_to_end_projection_markdown(comparison)
    if expected_markdown not in markdown:
        errors.append("rendered-context Markdown end-to-end binding is stale")
    return errors


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
    comparison = report.get("end_to_end_cost_gate")
    if comparison is not None:
        if not isinstance(comparison, dict):
            raise ValueError("end-to-end cost gate must be an object")
        report["end_to_end_projection_binding"] = _end_to_end_projection_binding(
            comparison
        )
    report_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    aggregate = report["aggregate"]
    lines = [
        "# Rendered Context Budget Evaluation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Evidence scope: **{report['evidence_scope']}**",
        "",
        f"Compiled Layer 3 format: **{report['compiled_layer3_format']}**",
        "",
        f"Tokenizer: **{report['tokenizer']}**",
        "",
        f"Fixtures: **{report['fixture_count']}**; dispatches: **{report['dispatch_count']}**; "
        f"host/profile measurements: **{report['measurement_count']}**.",
        f"Explicit nested Layer 3 Reference loads: "
        f"**{aggregate['loaded_layer3_reference_count']}**; logical IDs: "
        f"**{', '.join(aggregate['loaded_layer3_reference_logical_ids']) or 'none'}**.",
        f"Measured nested Reference components across host/profile combinations: "
        f"**{aggregate['measured_layer3_reference_component_count']}**.",
        "",
        f"Fixture Capsule contract: **{report['fixture_capsule_contract']['version']}**. "
        "Its hash detects drift, its typed semantic gate rejects synchronized "
        "placeholder/low-diversity forgeries, and its deterministic renderer is "
        "evaluator-only and excluded from build/install artifacts.",
        "",
        "The Control Prompt is embedded in each rendered Main Profile and is not added a second time.",
        "",
        "## Authoritative Limits and Observed Maxima",
        "",
        "Soft targets and hard ceilings come only from the Core Model and are "
        "provisional migration values, not calibrated optima. Soft overage is an "
        "advisory; hard overage fails Conformance without truncating required context.",
        "",
        f"Mode: **{report['budget_governance']['mode']}**.",
        "",
        "| Context | Soft target | Hard ceiling | Observed maximum | Soft margin | Hard margin | Soft status | Hard status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    main = aggregate["max_main"]
    lines.append(
        f"| Main always-loaded | {main['soft_target'] if main else 'n/a'} | "
        f"{main['hard_ceiling'] if main else 'n/a'} | "
        f"{main['tokens'] if main else 'n/a'} | "
        f"{main['soft_margin_tokens'] if main else 'n/a'} | "
        f"{main['hard_margin_tokens'] if main else 'n/a'} | "
        f"{'within' if main and main['within_soft_target'] else 'advisory'} | "
        f"{'within' if main and main['within_hard_ceiling'] else 'fail'} |"
    )
    for budget_class in ("task", "analyzed_task", "analysis", "review", "utility"):
        maximum = aggregate["max_by_budget_class"].get(budget_class)
        lines.append(
            f"| {CONTEXT_BUDGET_LIMITS[budget_class]['label']} | "
            f"{maximum['soft_target'] if maximum else 'n/a'} | "
            f"{maximum['hard_ceiling'] if maximum else 'n/a'} | "
            f"{maximum['tokens'] if maximum else 'n/a'} | "
            f"{maximum['soft_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['hard_margin_tokens'] if maximum else 'n/a'} | "
            f"{'within' if maximum and maximum['within_soft_target'] else 'advisory'} | "
            f"{'within' if maximum and maximum['within_hard_ceiling'] else 'fail'} |"
        )
    governance = report["budget_governance"]
    lines.extend(
        [
            "",
            "## Calibration Distribution",
            "",
            "Calibration candidate selection and frontier construction do not apply "
            "soft targets or hard ceilings. Percentiles use nearest rank.",
            "",
            "| Context | Count | P50 | P90 | P95 | P99 | Max | Growth distribution |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            *[
                f"| {CONTEXT_BUDGET_LIMITS[budget_class]['label']} | "
                f"{distribution['count']} | {distribution['p50']} | "
                f"{distribution['p90']} | {distribution['p95']} | "
                f"{distribution['p99']} | {distribution['max']} | unavailable |"
                for budget_class, distribution in governance["distributions"].items()
            ],
            "",
            f"Valid-candidate selection identity: "
            f"`{governance['selection_contract']['selection_identity_sha256']}`. "
            "Temporal growth is unavailable because this run has one comparable snapshot.",
        ]
    )
    admissible = report["admissible_context_compositions"]
    admissible_inventory = admissible["inventory"]
    lines.extend(
        [
            "",
            "## Admissible Context Composition Gate",
            "",
            f"Contract: **{admissible['contract']}**; selector owner surfaces: "
            f"**{admissible_inventory['owner_surface_count']}**; canonical legal "
            f"selection equivalence classes: "
            f"**{admissible_inventory['legal_selection_equivalence_class_count']}**; "
            f"exact measurements: **{admissible_inventory['exact_measurement_count']}**.",
            "",
            "| Context | Soft target | Hard ceiling | Reachable maximum | Professional | Layer 3 | Owner | Build | Host |",
            "| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    if comparison is not None:
        lines.extend(
            _render_end_to_end_projection_markdown(comparison).splitlines()
        )
    for budget_class in ADMISSIBLE_BUDGET_CLASSES:
        maximum = admissible["max_by_budget_class"].get(budget_class)
        lines.append(
            f"| {budget_class} | {CONTEXT_BUDGET_LIMITS[budget_class]['soft_target']} | "
            f"{CONTEXT_BUDGET_LIMITS[budget_class]['hard_ceiling']} | "
            f"{maximum['tokens'] if maximum else 'n/a'} | "
            f"{maximum['professional_skill'] if maximum else 'n/a'} | "
            f"{', '.join(maximum['selected_layer3']) if maximum else 'n/a'} | "
            f"{maximum['selection_owner'] if maximum else 'n/a'} | "
            f"{maximum['build_profile'] if maximum else 'n/a'} | "
            f"{maximum['host'] if maximum else 'n/a'} |"
        )
    dominance = admissible["dominance_frontier"]
    global_frontier = dominance["global_task_review_union"]
    lines.extend(
        [
            "",
            "### Dominance Frontier Projection",
            "",
            "| Context | Canonical candidates | Exact render signatures | Over target |",
            "| --- | ---: | ---: | ---: |",
            *[
                f"| {budget_class} | {row['candidate_count']} | "
                f"{row['exact_render_signature_count']} | "
                f"{row['over_target_candidate_count']} |"
                for budget_class, row in dominance["budget_classes"].items()
            ],
            "",
            "Global Task/Review frontier counts: "
            + ", ".join(
                f"{member_kind}={count}"
                for member_kind, count in global_frontier[
                    "frontier_counts"
                ].items()
            )
            + "; safe complement: "
            + ", ".join(
                f"{member_kind}={count}"
                for member_kind, count in global_frontier[
                    "safe_complement_counts"
                ].items()
            )
            + ".",
            "",
            f"Mapping digest: `{dominance['mapping_digest']}`; runtime consumers: "
            f"**{len(dominance['consumer_boundary']['runtime_consumers'])}**; "
            f"build consumers: "
            f"**{len(dominance['consumer_boundary']['build_consumers'])}**.",
        ]
    )
    lines.extend(
        [
            "",
            "Coverage: "
            + ", ".join(
                f"{name}={'yes' if covered else 'no'}"
                for name, covered in admissible["required_coverage"].items()
            )
            + ".",
            "",
            "Forbidden-combination evidence: "
            f">3 rejected={admissible['forbidden_combinations']['over_max_rejection_count']}; "
            f"unauthorized exact rejected={admissible['forbidden_combinations']['unauthorized_exact_rejection_count']}; "
            f"duplicate exact rejected={admissible['forbidden_combinations']['duplicate_exact_rejection_count']}; "
            f"silent truncations={admissible['forbidden_combinations']['silent_truncation_count']}; "
            f"nearest-negative leaks={admissible['forbidden_combinations']['nearest_negative_leak_count']}.",
            "",
            "### Composition Proof Limits",
            "",
            *[f"- {item}" for item in admissible["proof_limits"]],
        ]
    )
    lines.extend(
        [
            "",
            f"Maximum exact normalized duplicate-rule ratio: "
            f"**{aggregate['max_duplicate_rule_token_ratio']}** "
            f"(gate: **{DUPLICATE_TOKEN_RATIO_MAX}**; margin: "
            f"**{aggregate['duplicate_rule_token_ratio_margin']}**).",
            "",
            "Discovery metadata is reported separately because actual host discovery injection is not observed.",
            "",
            "## Transferred Context Measurement",
            "",
            f"Gross exclusive transferred-context tokens: **{report['transferred_context']['gross_tokens']}**; "
            f"non-compressible: **{report['transferred_context']['non_compressible_tokens']}**; "
            f"compressible: **{report['transferred_context']['compressible_tokens']}**; "
            f"ratio: **{report['transferred_context']['compressible_ratio']}**.",
            "",
            f"Long tasks joined from lightweight required progress: "
            f"**{report['transferred_context']['long_task_selector_join_count']}**. "
            "Candidate-only transfer measurements carry no baseline claim.",
            "",
            "Overlap views (Evidence Ledger, Diff, Validation, duplicate context, and superseded evidence) are reported outside the gross denominator.",
            "",
            "### Transfer Proof Limits",
            "",
            *[
                f"- {item}"
                for item in report["transferred_context"]["proof_limits"]
            ],
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in report["limitations"]],
            "",
        ]
    )
    if report["errors"]:
        lines.extend(["## Errors", "", *[f"- {item}" for item in report["errors"]], ""])
    if release_projection:
        markdown = "\n".join(lines)
        binding_errors = _end_to_end_projection_binding_errors(
            comparison,
            markdown,
            report.get("end_to_end_projection_binding"),
        ) if comparison is not None else []
        if binding_errors:
            raise ValueError("; ".join(binding_errors))
        report_markdown.write_text(markdown, encoding="utf-8")


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument(
        "--mode",
        choices=("calibration", "conformance"),
        default="conformance",
    )
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    parser.add_argument("--ab-baseline-ref")
    parser.add_argument("--expected-baseline-commit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    try:
        comparison = None
        if args.ab_baseline_ref:
            comparison = evaluate_end_to_end_ab(
                baseline_ref=args.ab_baseline_ref,
                expected_baseline_commit=args.expected_baseline_commit,
            )
            report = comparison.pop("_candidate_rendered_report")
            report["end_to_end_cost_gate"] = comparison
        else:
            report = evaluate(mode=args.mode)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"eval-rendered-context-budget: ERROR: {exc}", file=sys.stderr)
        return 1
    _write_reports(
        report,
        release_projection=args.release_projection,
        reports_dir=args.reports_dir,
    )
    if report["errors"]:
        for error in report["errors"]:
            print(f"eval-rendered-context-budget: ERROR: {error}", file=sys.stderr)
        return 1
    if comparison is not None and comparison["status"] != "pass":
        for error in comparison["errors"]:
            print(f"eval-rendered-context-budget: COST-GATE: {error}", file=sys.stderr)
        return 1
    print(
        "eval-rendered-context-budget: validated "
        f"{report['dispatch_count']} dispatches across "
        f"{len(report['hosts'])} hosts and {len(report['build_profiles'])} build profiles."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
