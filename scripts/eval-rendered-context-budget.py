#!/usr/bin/env python3
"""Measure deterministic rendered instruction context with exact token budgets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path, PurePosixPath
from typing import Any

from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    CONTEXT_BUDGET_MODEL,
    ValidationProblem,
    count_o200k_base_tokens,
    derived_context_budget_limits,
    layer3_selector_authority,
    layer3_selector_control_projections,
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
CONTEXT_BUDGET_LIMITS = derived_context_budget_limits(CONTEXT_BUDGET_MODEL)
FROZEN_GATES = {
    budget_class: limit["evolution_target"]
    for budget_class, limit in CONTEXT_BUDGET_LIMITS.items()
}
PHASE3_CONTEXT_TARGETS = {
    "analysis": 4_500,
    "task": 3_000,
    "analyzed_task": 6_000,
    "review": 3_700,
}
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
TRANSFER_MEASUREMENT_CONTRACT = {
    "baseline_gross_tokens": 47_302,
    "category_baseline_gross_tokens": {
        "authority": 7_148,
        "skill_reference": 1_421,
        "task_capsule": 4_348,
        "implementation_handoff": 11_200,
        "evidence_ledger": 2_551,
        "diff": 618,
        "validation": 915,
        "review_handoff": 27_118,
        "repair_context": 329,
        "duplicate_context": 3_297,
        "superseded_evidence": 876,
    },
    "long_task_baseline_gross_tokens": {
        "api-contract-change": 3_664,
        "cache-stampede-reliability": 3_670,
        "data-migration": 3_750,
        "isolated-write-parallel-contract": 6_023,
        "release-rollback": 3_671,
        "repair-and-rereview": 6_434,
        "security-ssrf-boundary": 3_647,
        "shared-workspace-serial-write": 4_957,
        "single-module-feature": 3_460,
    },
    "minimum_realized_reduction_ratio": 0.25,
    "target_realized_reduction_ratio": 0.30,
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
        "blocking_findings",
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


def _registered_long_task_baselines(
    long_task_ids: set[str],
) -> dict[str, int]:
    baselines = TRANSFER_MEASUREMENT_CONTRACT[
        "long_task_baseline_gross_tokens"
    ]
    missing = sorted(long_task_ids - set(baselines))
    if missing:
        raise ValueError(f"unregistered long-task transfer baseline: {missing}")
    return {case_id: int(baselines[case_id]) for case_id in sorted(long_task_ids)}


def _context_compaction_classification(ratio: float) -> str:
    minimum = TRANSFER_MEASUREMENT_CONTRACT[
        "minimum_realized_reduction_ratio"
    ]
    target = TRANSFER_MEASUREMENT_CONTRACT["target_realized_reduction_ratio"]
    if ratio < minimum:
        return "stop-below-threshold"
    if ratio < target:
        return "marginal"
    return "continue"


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
    blockers = [
        step
        for step in steps[review_index + 1 : index]
        if isinstance(step, dict)
        and step.get("action") == "finding"
        and step.get("relation") == "current-task"
        and step.get("material") is True
    ]
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
    return [
        (index, step)
        for index, step in enumerate(steps[start + 1 :], start + 1)
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
                    f"{_relative(IMPLEMENTATION_HANDOFF_TEMPLATE)}; {_relative(FIXTURES)}#/{case_id}/tasks/{task_id}",
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
                repair = {
                    "blocking_findings": [
                        {
                            "claim": item.get("evidence_id"),
                            "relation": item.get("relation"),
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
    token_budget: int,
) -> dict[str, Any]:
    limit = CONTEXT_BUDGET_LIMITS[budget_class]
    if token_budget != limit["evolution_target"]:
        raise ValueError(
            f"{budget_class} token budget must equal its derived evolution target"
        )
    combined = "\n\n".join(component["_text"].rstrip() for component in components)
    total_tokens = count_o200k_base_tokens(combined)
    duplicates = _duplicate_block_metrics(components)
    duplicate_tokens = duplicates["duplicate_rule_tokens"]
    ratio = duplicate_tokens / total_tokens if total_tokens else 0.0
    public_components = [
        {key: value for key, value in component.items() if key != "_text"}
        for component in components
    ]
    return {
        "budget_class": budget_class,
        "capacity_ceiling": limit["capacity_ceiling"],
        "minimum_headroom_ratio": limit["minimum_headroom_ratio"],
        "required_reserve_tokens": limit["required_reserve_tokens"],
        "release_target": limit["release_target"],
        "minimum_release_margin_tokens": limit[
            "minimum_release_margin_tokens"
        ],
        "evolution_target": limit["evolution_target"],
        "token_budget": token_budget,
        "total_tokens": total_tokens,
        "sum_component_tokens": sum(item["tokens"] for item in public_components),
        "duplicate_rule_tokens": duplicate_tokens,
        "duplicate_rule_token_ratio": round(ratio, 6),
        "within_token_budget": total_tokens <= token_budget,
        "within_duplicate_budget": ratio <= DUPLICATE_TOKEN_RATIO_MAX,
        "components": public_components,
        "duplicate_blocks": duplicates["duplicate_blocks"],
    }


def evaluate_route_obligation_context(
    components: list[dict[str, Any]],
    *,
    required_route_obligations: dict[str, Any],
    budget_class: str,
    token_budget: int,
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
        token_budget=token_budget,
    )
    overflow = measurement["within_token_budget"] is False
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
    """Expose both release margin and capacity headroom for one maximum."""

    if maximum is None:
        return None
    ceiling = maximum["capacity_ceiling"]
    observed = maximum["total_tokens"]
    result = {
        "tokens": observed,
        "capacity_ceiling": ceiling,
        "minimum_headroom_ratio": maximum["minimum_headroom_ratio"],
        "required_reserve_tokens": maximum["required_reserve_tokens"],
        "release_target": maximum["release_target"],
        "minimum_release_margin_tokens": maximum[
            "minimum_release_margin_tokens"
        ],
        "evolution_target": maximum["evolution_target"],
        "release_margin_tokens": maximum["release_target"] - observed,
        "evolution_margin_tokens": maximum["evolution_target"] - observed,
        "capacity_headroom_tokens": ceiling - observed,
        "capacity_headroom_ratio": round((ceiling - observed) / ceiling, 6),
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
            if budget_class not in PHASE3_CONTEXT_TARGETS:
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

    for budget_class in ("analysis", "task", "analyzed_task", "review"):
        target = PHASE3_CONTEXT_TARGETS[budget_class]
        candidates_by_key = canonical_candidates[budget_class]
        signatures: set[tuple[tuple[str, str], ...]] = set()
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
            active_references = _active_reference_ids(candidate)
            members = {
                "professional": [candidate["professional_skill"]],
                "layer3": sorted(candidate["selected_layer3"]),
                "active_reference": active_references,
            }
            over_target = tokens > target
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
            "target_tokens": target,
            "candidate_count": len(candidates_by_key),
            "exact_render_signature_count": len(signatures),
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
        budget_class: None for budget_class in PHASE3_CONTEXT_TARGETS
    }
    canonical_candidates: dict[
        str,
        dict[tuple[Any, ...], dict[str, Any]],
    ] = {budget_class: {} for budget_class in PHASE3_CONTEXT_TARGETS}
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
                    token_budget=FROZEN_GATES[budget_class],
                )
                exact_measurement_cache[cache_key] = measurement
                inventory["exact_measurement_count"] += 1
            result = {
                "tokens": measurement["total_tokens"],
                "sum_component_tokens": measurement["sum_component_tokens"],
                "component_upper_bound_tokens": candidate[
                    "component_upper_bound"
                ],
                "within_hard_evolution_target": (
                    measurement["total_tokens"]
                    <= PHASE3_CONTEXT_TARGETS[budget_class]
                ),
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
    for budget_class, target in PHASE3_CONTEXT_TARGETS.items():
        maximum = maxima[budget_class]
        if maximum is None:
            errors.append(f"admissible composition lacks {budget_class} measurement")
            continue
        if maximum["tokens"] > target:
            errors.append(
                f"admissible composition {budget_class} maximum "
                f"{maximum['tokens']} exceeds Phase 3 target {target}"
            )
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


def evaluate() -> dict[str, Any]:
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
    long_task_baselines = _registered_long_task_baselines(long_task_ids)
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
                token_budget=FROZEN_GATES["main"],
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
            if not measurement["within_token_budget"]:
                errors.append(
                    f"main:{host}:{build_profile} uses {measurement['total_tokens']} tokens; "
                    f"budget is {measurement['token_budget']}"
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
                        token_budget=FROZEN_GATES[budget_class],
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
                    if not measurement["within_token_budget"]:
                        errors.append(
                            f"{case_id}:step:{index}:{host}:{build_profile} uses "
                            f"{measurement['total_tokens']} {budget_class} tokens; "
                            f"budget is {measurement['token_budget']}"
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
    component_catalog = _compact_component_catalog(duplicate_candidates)
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
    category_baselines = TRANSFER_MEASUREMENT_CONTRACT[
        "category_baseline_gross_tokens"
    ]
    for category, measurement in transfer_aggregate["categories"].items():
        before = category_baselines[category]
        after = measurement["gross_tokens"]
        measurement["before_gross_tokens"] = before
        measurement["after_gross_tokens"] = after
        measurement["realized_reduction_tokens"] = before - after
        measurement["realized_reduction_ratio"] = round((before - after) / before, 6)
    long_task_rows = []
    for case_id in sorted(long_task_ids):
        row = dict(transfer_by_id[case_id])
        row["required_progress_for_multi_agent"] = True
        row["after_gross_tokens"] = row["gross_tokens"]
        row["before_gross_tokens"] = long_task_baselines[case_id]
        row["realized_reduction_tokens"] = (
            row["before_gross_tokens"] - row["after_gross_tokens"]
        )
        row["realized_reduction_ratio"] = round(
            row["realized_reduction_tokens"] / row["before_gross_tokens"], 6
        )
        long_task_rows.append(row)
    conservative_long_task_ratio = min(
        row["realized_reduction_ratio"] for row in long_task_rows
    )
    after_gross_tokens = transfer_aggregate["gross_tokens"]
    before_gross_tokens = TRANSFER_MEASUREMENT_CONTRACT["baseline_gross_tokens"]
    realized_reduction_tokens = before_gross_tokens - after_gross_tokens
    realized_reduction_ratio = round(
        realized_reduction_tokens / before_gross_tokens, 6
    )
    minimum_reduction = TRANSFER_MEASUREMENT_CONTRACT[
        "minimum_realized_reduction_ratio"
    ]
    target_reduction = TRANSFER_MEASUREMENT_CONTRACT[
        "target_realized_reduction_ratio"
    ]
    compaction_decision = {
        "classification": _context_compaction_classification(
            conservative_long_task_ratio
        ),
        "observed_conservative_ratio": conservative_long_task_ratio,
        "minimum_realized_reduction_ratio": minimum_reduction,
        "target_realized_reduction_ratio": target_reduction,
    }
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
        **transfer_aggregate,
        "before_gross_tokens": before_gross_tokens,
        "after_gross_tokens": after_gross_tokens,
        "realized_reduction_tokens": realized_reduction_tokens,
        "realized_reduction_ratio": realized_reduction_ratio,
        "minimum_realized_reduction_ratio": minimum_reduction,
        "target_realized_reduction_ratio": target_reduction,
        "context_compaction_decision": compaction_decision,
        "measured_case_count": len(transfer_rows),
        "long_task_selector_join_count": len(long_task_rows),
        "long_task_rows": long_task_rows,
        "conservative_long_task_ratio": conservative_long_task_ratio,
        "proof_limits": list(TRANSFER_PROOF_LIMITS),
    }
    if realized_reduction_ratio < minimum_reduction:
        errors.append("aggregate transferred-context realized reduction is below 0.25")
    for row in long_task_rows:
        if row["realized_reduction_ratio"] < minimum_reduction:
            errors.append(
                f"{row['id']}: long-task realized reduction is below 0.25"
            )
    for protected_category in ("authority", "skill_reference", "task_capsule"):
        if transfer_aggregate["categories"][protected_category]["gross_tokens"] != (
            category_baselines[protected_category]
        ):
            errors.append(
                f"{TRANSFER_CATEGORY_LABELS[protected_category]} transfer changed "
                "during derived-context compaction"
            )
    duplicate_before = category_baselines["duplicate_context"]
    duplicate_after = transfer_aggregate["categories"]["duplicate_context"][
        "gross_tokens"
    ]
    duplicate_reduction_ratio = round(
        (duplicate_before - duplicate_after) / duplicate_before, 6
    )
    if duplicate_reduction_ratio < minimum_reduction:
        errors.append("duplicate context did not decrease by at least 25 percent")
    if transfer_aggregate["categories"]["superseded_evidence"]["gross_tokens"]:
        errors.append("superseded evidence must not cross a transfer boundary")
    admissible_context_compositions = _evaluate_admissible_context_compositions(
        cases=cases,
        manifests=manifests,
    )
    errors.extend(admissible_context_compositions["errors"])
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
        "budget_calibration": {
            "method": (
                "Capacity ceilings and minimum headroom ratios come from the Core Model; "
                "release and evolution targets are derived without calibration relaxation."
            ),
            "source": "src/control-model/core-contracts.json#/context_budget_contract",
            "capacity_ceilings": {
                key: value["capacity_ceiling"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "minimum_headroom_ratios": {
                key: value["minimum_headroom_ratio"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "required_reserve_tokens": {
                key: value["required_reserve_tokens"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "release_targets": {
                key: value["release_target"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "minimum_release_margin_tokens": {
                key: value["minimum_release_margin_tokens"]
                for key, value in CONTEXT_BUDGET_LIMITS.items()
            },
            "evolution_targets": dict(FROZEN_GATES),
            "frozen_gates": dict(FROZEN_GATES),
            "relaxations": [],
            "duplicate_rule_token_ratio_max": DUPLICATE_TOKEN_RATIO_MAX,
        },
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
        "Capacity ceilings, minimum headroom ratios, and minimum release margins "
        "come from the Core Model. Release and evolution targets are derived; "
        "calibration relaxations: **none**.",
        "",
        "| Context | Capacity ceiling | Required reserve | Release target | Minimum release margin | Evolution target | Observed maximum | Release margin | Evolution margin | Capacity headroom ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    main = aggregate["max_main"]
    lines.append(
        f"| Main always-loaded | {main['capacity_ceiling'] if main else 'n/a'} | "
        f"{main['required_reserve_tokens'] if main else 'n/a'} | "
        f"{main['release_target'] if main else 'n/a'} | "
        f"{main['minimum_release_margin_tokens'] if main else 'n/a'} | "
        f"{main['evolution_target'] if main else 'n/a'} | "
        f"{main['tokens'] if main else 'n/a'} | "
        f"{main['release_margin_tokens'] if main else 'n/a'} | "
        f"{main['evolution_margin_tokens'] if main else 'n/a'} | "
        f"{main['capacity_headroom_ratio'] if main else 'n/a'} |"
    )
    for budget_class in ("task", "analyzed_task", "analysis", "review", "utility"):
        maximum = aggregate["max_by_budget_class"].get(budget_class)
        lines.append(
            f"| {CONTEXT_BUDGET_LIMITS[budget_class]['label']} | "
            f"{maximum['capacity_ceiling'] if maximum else 'n/a'} | "
            f"{maximum['required_reserve_tokens'] if maximum else 'n/a'} | "
            f"{maximum['release_target'] if maximum else 'n/a'} | "
            f"{maximum['minimum_release_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['evolution_target'] if maximum else 'n/a'} | "
            f"{maximum['tokens'] if maximum else 'n/a'} | "
            f"{maximum['release_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['evolution_margin_tokens'] if maximum else 'n/a'} | "
            f"{maximum['capacity_headroom_ratio'] if maximum else 'n/a'} |"
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
            "| Context | Phase 3 target | Reachable maximum | Professional | Layer 3 | Owner | Build | Host |",
            "| --- | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for budget_class in ("task", "analyzed_task", "analysis", "review"):
        maximum = admissible["max_by_budget_class"].get(budget_class)
        lines.append(
            f"| {budget_class} | {PHASE3_CONTEXT_TARGETS[budget_class]} | "
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
            f"**{report['transferred_context']['long_task_selector_join_count']}**; "
            f"conservative ratio: "
            f"**{report['transferred_context']['conservative_long_task_ratio']}**.",
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
        report_markdown.write_text("\n".join(lines), encoding="utf-8")


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    try:
        report = evaluate()
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
    print(
        "eval-rendered-context-budget: validated "
        f"{report['dispatch_count']} dispatches across "
        f"{len(report['hosts'])} hosts and {len(report['build_profiles'])} build profiles."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
