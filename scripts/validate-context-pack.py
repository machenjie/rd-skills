#!/usr/bin/env python3
"""Validate ChangeForge TaskContextPack JSON documents."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk_live_[A-Za-z0-9]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|token|secret|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}"),
]

CONTEXT_BUDGET_MODES = {"minimal", "single-stage", "staged-plan", "full"}
EXPECTED_OUTPUT_POLICIES = {"bounded_summary", "artifact_reference", "read_slice"}
READ_POLICIES = {"read_slice", "read_full_if_small", "read_heading_only"}
SOURCE_TRUTH_STATUSES = {"source", "generated", "unknown"}


def _payload(document: dict[str, Any]) -> dict[str, Any]:
    if "task_context_pack" not in document or not isinstance(document["task_context_pack"], dict):
        raise ValueError("missing task_context_pack object")
    return document["task_context_pack"]


def _has_secret_like(value: Any) -> bool:
    text = json.dumps(value, sort_keys=True)
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _is_user_absolute_path(path: str) -> bool:
    return path.startswith(("/Users/", "/home/")) or re.match(r"^[A-Za-z]:\\\\Users\\\\", path) is not None


def _is_absolute_path(path: str) -> bool:
    return path.startswith("/") or re.match(r"^[A-Za-z]:[\\\\/]", path) is not None


def _path_values(items: list[Any], key: str = "path") -> set[str]:
    values: set[str] = set()
    for item in items:
        if isinstance(item, dict) and isinstance(item.get(key), str):
            values.add(item[key])
    return values


def _list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _validate_repo_relative_path(errors: list[str], path: Any, context: str) -> None:
    if not isinstance(path, str) or not path:
        errors.append(f"{context}.path must be a non-empty repository-relative string")
        return
    if _is_absolute_path(path):
        errors.append(f"{context}.path must be repository-relative: {path}")
    if _has_secret_like(path):
        errors.append(f"{context}.path contains secret-like content")


def _validate_v3_context_control(pack: dict[str, Any], errors: list[str]) -> None:
    context_control = pack.get("context_control")
    if not isinstance(context_control, dict):
        errors.append("task_context_pack.context_control is required for schema_version=3")
        return
    required_fields = (
        "budget_mode",
        "context_budget_tokens",
        "selected_file_count",
        "omitted_file_count",
        "selected_symbol_count",
        "selected_graph_node_count",
        "skipped_graph_node_count",
        "signal_density_rationale",
    )
    for field in required_fields:
        if field not in context_control:
            errors.append(f"context_control.{field} is required for schema_version=3")
    if context_control.get("budget_mode") not in CONTEXT_BUDGET_MODES:
        errors.append(f"context_control.budget_mode must be one of {sorted(CONTEXT_BUDGET_MODES)}")
    for field in (
        "context_budget_tokens",
        "selected_file_count",
        "omitted_file_count",
        "selected_symbol_count",
        "selected_graph_node_count",
        "skipped_graph_node_count",
    ):
        value = context_control.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"context_control.{field} must be a non-negative integer")
    if not isinstance(context_control.get("signal_density_rationale"), str) or not context_control.get("signal_density_rationale"):
        errors.append("context_control.signal_density_rationale must be a non-empty string")

    selected_files = _list_value(pack.get("selected_files"))
    if isinstance(context_control.get("selected_file_count"), int) and context_control["selected_file_count"] != len(selected_files):
        errors.append("context_control.selected_file_count must match selected_files length")
    selected_symbols = _list_value(pack.get("selected_symbols"))
    if isinstance(context_control.get("selected_symbol_count"), int) and context_control["selected_symbol_count"] != len(selected_symbols):
        errors.append("context_control.selected_symbol_count must match selected_symbols length")
    selected_graph_nodes = _list_value(pack.get("selected_graph_nodes"))
    if (
        isinstance(context_control.get("selected_graph_node_count"), int)
        and context_control["selected_graph_node_count"] != len(selected_graph_nodes)
    ):
        errors.append("context_control.selected_graph_node_count must match selected_graph_nodes length")
    skipped_graph_nodes = _list_value(pack.get("skipped_graph_nodes"))
    if (
        isinstance(context_control.get("skipped_graph_node_count"), int)
        and context_control["skipped_graph_node_count"] != len(skipped_graph_nodes)
    ):
        errors.append("context_control.skipped_graph_node_count must match skipped_graph_nodes length")

    anti_bloat = pack.get("anti_bloat_decision") if isinstance(pack.get("anti_bloat_decision"), dict) else {}
    max_file_count = context_control.get("max_file_count", anti_bloat.get("max_files"))
    if not isinstance(max_file_count, int):
        errors.append("context_control.max_file_count or anti_bloat_decision.max_files is required for budget validation")
    elif isinstance(context_control.get("selected_file_count"), int) and context_control["selected_file_count"] > max_file_count:
        errors.append("context_control.selected_file_count must not exceed selected budget")


def _validate_v3_jit_retrieval_plan(pack: dict[str, Any], errors: list[str]) -> None:
    plan = pack.get("jit_retrieval_plan")
    if not isinstance(plan, dict):
        errors.append("task_context_pack.jit_retrieval_plan is required for schema_version=3")
        return
    for field in ("discovery", "targeted_reads", "deferred_reads", "forbidden_reads"):
        if not isinstance(plan.get(field), list):
            errors.append(f"jit_retrieval_plan.{field} must be a list")
    discovery = _list_value(plan.get("discovery"))
    targeted_reads = _list_value(plan.get("targeted_reads"))
    if not discovery and not targeted_reads:
        errors.append("jit_retrieval_plan must include at least one discovery or targeted_reads item")
    for index, item in enumerate(discovery):
        if not isinstance(item, dict):
            errors.append(f"jit_retrieval_plan.discovery[{index}] must be an object")
            continue
        if not isinstance(item.get("command"), str) or not item.get("command"):
            errors.append(f"jit_retrieval_plan.discovery[{index}].command is required")
        if not isinstance(item.get("purpose"), str) or not item.get("purpose"):
            errors.append(f"jit_retrieval_plan.discovery[{index}].purpose is required")
        if item.get("expected_output_policy") not in EXPECTED_OUTPUT_POLICIES:
            errors.append(
                f"jit_retrieval_plan.discovery[{index}].expected_output_policy must be one of {sorted(EXPECTED_OUTPUT_POLICIES)}"
            )
    for index, item in enumerate(targeted_reads):
        if not isinstance(item, dict):
            errors.append(f"jit_retrieval_plan.targeted_reads[{index}] must be an object")
            continue
        _validate_repo_relative_path(errors, item.get("path"), f"jit_retrieval_plan.targeted_reads[{index}]")
        if not isinstance(item.get("reason"), str) or not item.get("reason"):
            errors.append(f"jit_retrieval_plan.targeted_reads[{index}].reason is required")
        line_hint = item.get("line_hint")
        if line_hint is not None and not isinstance(line_hint, str):
            errors.append(f"jit_retrieval_plan.targeted_reads[{index}].line_hint must be string or null")
        if item.get("read_policy") not in READ_POLICIES:
            errors.append(f"jit_retrieval_plan.targeted_reads[{index}].read_policy must be one of {sorted(READ_POLICIES)}")
        if item.get("source_truth_status") not in SOURCE_TRUTH_STATUSES:
            errors.append(
                f"jit_retrieval_plan.targeted_reads[{index}].source_truth_status must be one of {sorted(SOURCE_TRUTH_STATUSES)}"
            )
    for field in ("deferred_reads", "forbidden_reads"):
        for index, item in enumerate(_list_value(plan.get(field))):
            if not isinstance(item, dict):
                errors.append(f"jit_retrieval_plan.{field}[{index}] must be an object")
                continue
            _validate_repo_relative_path(errors, item.get("path"), f"jit_retrieval_plan.{field}[{index}]")
            if not isinstance(item.get("reason"), str) or not item.get("reason"):
                errors.append(f"jit_retrieval_plan.{field}[{index}].reason is required")

    generated_involved = bool(pack.get("generated_artifacts")) or any(
        isinstance(path, str) and path.startswith("dist/") for path in pack.get("changed_paths", [])
    )
    if generated_involved:
        forbidden = _list_value(plan.get("forbidden_reads"))
        has_generated_policy = any(
            isinstance(item, dict)
            and (
                str(item.get("path") or "").startswith("dist/")
                or "generated" in str(item.get("reason") or "").lower()
            )
            for item in forbidden
        )
        if not has_generated_policy:
            errors.append("jit_retrieval_plan.forbidden_reads must include dist/ or generated-output handling")


def _validate_v3_artifact_policy(pack: dict[str, Any], errors: list[str]) -> None:
    policy = pack.get("artifact_policy")
    if not isinstance(policy, dict):
        errors.append("task_context_pack.artifact_policy is required for schema_version=3")
        return
    expected = {
        "large_outputs": "artifact_reference_only",
        "full_graph_dump": "forbidden",
        "full_test_log_dump": "forbidden",
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            errors.append(f"artifact_policy.{field} must be {value}")
    if "repository_graph" in pack or "repository_graph" in policy:
        errors.append("context pack must not include a full repository_graph dump")


def validate_context_pack(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        pack = _payload(document)
    except ValueError as exc:
        return [str(exc)]

    schema_version = pack.get("schema_version")
    if schema_version not in {1, 2, 3}:
        errors.append("task_context_pack.schema_version must be 1, 2, or 3")
    if not pack.get("task_goal") and not pack.get("task"):
        errors.append("task_context_pack.task_goal or task must be present")

    freshness = pack.get("freshness") if schema_version in {2, 3} else pack.get("freshness_markers")
    if not isinstance(freshness, dict):
        freshness = pack.get("freshness_markers")
    if not isinstance(freshness, dict):
        errors.append("task_context_pack.freshness or freshness_markers must be present")
        freshness = {}
    if not freshness.get("repo_hash"):
        errors.append("freshness_markers.repo_hash must be present")
    elif _is_user_absolute_path(str(freshness.get("repo_hash"))):
        errors.append("freshness_markers.repo_hash must not contain an absolute path")
    if not freshness.get("indexed_at"):
        errors.append("freshness_markers.indexed_at must be present")

    source_paths = _path_values(pack.get("source_of_truth", []))
    evidence_text = "\n".join(str(item) for item in pack.get("evidence_limits", []))
    for path in pack.get("changed_paths", []):
        if not isinstance(path, str):
            errors.append("changed_paths entries must be strings")
            continue
        if _is_user_absolute_path(path):
            errors.append(f"changed path must be repository-relative: {path}")
        if path.startswith("dist/"):
            if path not in evidence_text:
                errors.append(f"generated changed path needs evidence limit: {path}")
        elif path not in source_paths and path not in evidence_text:
            errors.append(f"changed path needs source_of_truth or evidence_limits explanation: {path}")

    validations = pack.get("validation_candidates")
    if not isinstance(validations, list) or not validations:
        errors.append("validation_candidates must include at least one command or unknown explanation")
    else:
        for index, item in enumerate(validations):
            if not isinstance(item, dict) or not item.get("command") or not item.get("proves"):
                errors.append(f"validation_candidates[{index}] must include command and proves")
            if schema_version in {2, 3} and isinstance(item, dict) and not item.get("scope"):
                errors.append(f"validation_candidates[{index}] must include scope for schema_version={schema_version}")

    for collection_name in (
        "source_of_truth",
        "relevant_files",
        "selected_files",
        "affected_tests",
        "related_tests",
        "excluded_context",
        "reuse_candidates",
        "rejected_locations",
        "omitted_nodes",
    ):
        collection = pack.get(collection_name, [])
        if not isinstance(collection, list):
            errors.append(f"{collection_name} must be a list")
            continue
        for item in collection:
            if isinstance(item, dict) and isinstance(item.get("path"), str) and _is_user_absolute_path(item["path"]):
                errors.append(f"{collection_name}.path must be repository-relative: {item['path']}")

    if any(
        isinstance(item, dict) and str(item.get("path", "")).startswith("dist/")
        for item in pack.get("source_of_truth", [])
    ):
        errors.append("dist must not appear as source_of_truth")
    if schema_version in {2, 3}:
        for field in (
            "graph_source",
            "selected_files",
            "selected_graph_nodes",
            "skipped_graph_nodes",
            "closure_evidence",
            "assumptions",
            "selected_symbols",
            "caller_callee_edges",
            "imports",
            "references",
            "related_tests",
            "generated_artifacts",
            "ownership",
            "reuse_candidates",
            "rejected_locations",
            "anti_bloat_decision",
            "omitted_nodes",
            "residual_risk",
            "graph_validation_candidates",
        ):
            if field not in pack:
                errors.append(f"task_context_pack.{field} is required for schema_version={schema_version}")
        if not isinstance(pack.get("anti_bloat_decision"), dict):
            errors.append(f"anti_bloat_decision must be an object for schema_version={schema_version}")
        for index, item in enumerate(pack.get("ownership", []) if isinstance(pack.get("ownership"), list) else []):
            if not isinstance(item, dict):
                errors.append(f"ownership[{index}] must be an object")
                continue
            for field in ("path", "owner_surface", "owner_module", "public_private_boundary"):
                if not item.get(field):
                    errors.append(f"ownership[{index}].{field} is required")
        for index, item in enumerate(pack.get("closure_evidence", []) if isinstance(pack.get("closure_evidence"), list) else []):
            if not isinstance(item, dict):
                errors.append(f"closure_evidence[{index}] must be an object")
                continue
            if item.get("freshness") != "current":
                errors.append(f"closure_evidence[{index}] must be current")
            if item.get("confidence") not in {"high", "medium"}:
                errors.append(f"closure_evidence[{index}] must be medium/high confidence")
        for index, item in enumerate(pack.get("graph_validation_candidates", []) if isinstance(pack.get("graph_validation_candidates"), list) else []):
            if not isinstance(item, dict):
                errors.append(f"graph_validation_candidates[{index}] must be an object")
                continue
            for field in ("changed_path", "candidate_tests", "confidence", "source", "freshness", "reason", "strength"):
                if field not in item:
                    errors.append(f"graph_validation_candidates[{index}].{field} is required")
            if item.get("strength") == "strong" and (
                item.get("freshness") != "current" or item.get("confidence") not in {"high", "medium"}
            ):
                errors.append(f"graph_validation_candidates[{index}] strong candidates must be current medium/high")
    if schema_version == 3:
        _validate_v3_context_control(pack, errors)
        _validate_v3_jit_retrieval_plan(pack, errors)
        _validate_v3_artifact_policy(pack, errors)
    if _has_secret_like(document):
        errors.append("context pack contains secret-like content")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-pack", required=True, help="TaskContextPack JSON path.")
    args = parser.parse_args(argv)
    document = json.loads(Path(args.context_pack).read_text(encoding="utf-8"))
    errors = validate_context_pack(document)
    if errors:
        for error in errors:
            print(f"validate-context-pack: ERROR: {error}")
        return 1
    pack = document["task_context_pack"]
    print(
        "validate-context-pack: validated "
        f"{len(pack.get('relevant_files', []))} relevant files and "
        f"{len(pack.get('validation_candidates', []))} validation candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
