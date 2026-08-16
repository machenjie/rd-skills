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
from pathlib import Path, PurePosixPath
from typing import Any

from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    CONTEXT_BUDGET_MODEL,
    ValidationProblem,
    count_o200k_base_tokens,
    derived_context_budget_limits,
    load_yaml_file,
    parse_frontmatter,
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
        "authority": 4_784,
        "skill_reference": 1_419,
        "task_capsule": 2_452,
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
        text = _canonical_json_text(projection)
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
