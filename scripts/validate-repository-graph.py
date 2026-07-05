#!/usr/bin/env python3
"""Validate ChangeForge RepositoryGraph JSON documents."""

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
FRESHNESS_VALUES = {"current", "stale", "unknown", "not_applicable"}
CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}
NODE_TYPES = {
    "file",
    "module",
    "class",
    "function",
    "method",
    "config_key",
    "reference",
    "test",
    "generated_artifact",
    "unknown",
}
EDGE_TYPES = {
    "imports",
    "calls",
    "references",
    "tests",
    "owns",
    "generates",
    "generated_from",
    "depends_on",
    "object_defined_in",
    "rule_enforced_by",
    "rule_previewed_by",
    "rule_defended_by",
    "workflow_transition_implemented_by",
    "event_produced_by",
    "event_consumed_by",
    "golden_case_validates",
    "memory_warns_about",
    "unknown",
}
EXTRACTOR_VALUES = {
    "python_symbol_extractor",
    "markdown_reference_extractor",
    "yaml_reference_extractor",
    "file_heuristic",
    "import_graph",
    "test_graph",
    "generated_artifact_graph",
    "reference_graph",
    "business_semantic_graph",
    "validation_broker.command_registry",
    "unknown",
}


def _payload(document: dict[str, Any]) -> dict[str, Any]:
    if "repository_graph" not in document or not isinstance(document["repository_graph"], dict):
        raise ValueError("missing repository_graph object")
    return document["repository_graph"]


def _has_secret_like(value: Any) -> bool:
    text = json.dumps(value, sort_keys=True)
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _is_user_absolute_path(path: str) -> bool:
    return path.startswith(("/Users/", "/home/")) or re.match(r"^[A-Za-z]:\\\\Users\\\\", path) is not None


def validate_repository_graph(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        graph = _payload(document)
    except ValueError as exc:
        return [str(exc)]

    schema_version = graph.get("schema_version")
    if schema_version not in {1, 2}:
        errors.append("repository_graph.schema_version must be 1 or 2")
    repo_hash = graph.get("repo_hash")
    if not isinstance(repo_hash, str) or not repo_hash:
        errors.append("repository_graph.repo_hash must be present")
    elif _is_user_absolute_path(repo_hash):
        errors.append("repository_graph.repo_hash must not contain an absolute path")
    if not graph.get("indexed_at"):
        errors.append("repository_graph.indexed_at must be present")
    if schema_version == 2:
        if not graph.get("created_at"):
            errors.append("repository_graph.created_at must be present for schema_version=2")
        if "commit_sha" not in graph:
            errors.append("repository_graph.commit_sha must be present for schema_version=2")

    files = graph.get("files")
    if not isinstance(files, list):
        errors.append("repository_graph.files must be a list")
        files = []
    for index, file_node in enumerate(files):
        if not isinstance(file_node, dict):
            errors.append(f"files[{index}] must be an object")
            continue
        path = file_node.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"files[{index}].path must be present")
            continue
        if _is_user_absolute_path(path):
            errors.append(f"files[{index}].path must be repository-relative")
        if path == "dist" or path.startswith("dist/"):
            errors.append(f"files[{index}].path must not index dist as source-of-truth: {path}")
        for required in ("kind", "role", "symbols", "references"):
            if required not in file_node:
                errors.append(f"files[{index}].{required} is required")
        if schema_version == 2:
            for field in ("evidence", "source_hash", "freshness", "confidence", "extractor", "node_type"):
                if field not in file_node:
                    errors.append(f"files[{index}].{field} is required for schema_version=2")
            _validate_file_node_v2(file_node, index, errors)

    edges = graph.get("edges")
    if not isinstance(edges, list):
        errors.append("repository_graph.edges must be a list")
        edges = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edges[{index}] must be an object")
            continue
        for field in ("from", "to", "type"):
            if not edge.get(field):
                errors.append(f"edges[{index}].{field} is required")
        for field in ("from", "to"):
            value = edge.get(field)
            if isinstance(value, str) and _is_user_absolute_path(value):
                errors.append(f"edges[{index}].{field} must be repository-relative")
        if schema_version == 2:
            for field in ("edge_type", "evidence", "confidence", "freshness", "extractor"):
                if field not in edge:
                    errors.append(f"edges[{index}].{field} is required for schema_version=2")
            _validate_edge_v2(edge, index, errors)

    if schema_version == 2:
        for field in (
            "symbols",
            "module_boundaries",
            "ownership",
            "generated_artifacts",
            "validation_candidates",
        ):
            if not isinstance(graph.get(field), list):
                errors.append(f"repository_graph.{field} must be a list for schema_version=2")
        freshness = graph.get("freshness")
        if not isinstance(freshness, dict) or not freshness.get("repo_hash") or not freshness.get("created_at"):
            errors.append("repository_graph.freshness must include repo_hash and created_at for schema_version=2")
        for index, symbol in enumerate(graph.get("symbols", []) if isinstance(graph.get("symbols"), list) else []):
            if not isinstance(symbol, dict):
                errors.append(f"symbols[{index}] must be an object")
                continue
            for field in ("name", "kind", "path", "line", "visibility", "language", "confidence"):
                if field not in symbol:
                    errors.append(f"symbols[{index}].{field} is required")
            for field in ("evidence", "source_hash", "freshness", "extractor"):
                if field not in symbol:
                    errors.append(f"symbols[{index}].{field} is required for schema_version=2")
            if isinstance(symbol.get("path"), str) and _is_user_absolute_path(symbol["path"]):
                errors.append(f"symbols[{index}].path must be repository-relative")
            _validate_symbol_v2(symbol, index, errors)
        for index, item in enumerate(graph.get("generated_artifacts", []) if isinstance(graph.get("generated_artifacts"), list) else []):
            if not isinstance(item, dict):
                errors.append(f"generated_artifacts[{index}] must be an object")
                continue
            for field in ("generated_path", "source_of_truth", "edit_policy", "confidence", "freshness", "extractor"):
                if field not in item:
                    errors.append(f"generated_artifacts[{index}].{field} is required for schema_version=2")
            _validate_generated_artifact_v2(item, index, errors)
        candidates = graph.get("validation_candidates", [])
        for index, candidate in enumerate(candidates if isinstance(candidates, list) else []):
            if not isinstance(candidate, dict):
                errors.append(f"validation_candidates[{index}] must be an object")
                continue
            if not candidate.get("command") or not candidate.get("scope"):
                errors.append(f"validation_candidates[{index}] must include command and scope")

    if _has_secret_like(document):
        errors.append("repository graph contains secret-like content")
    return errors


def _validate_file_node_v2(node: dict[str, Any], index: int, errors: list[str]) -> None:
    _validate_value(f"files[{index}].freshness", node.get("freshness"), FRESHNESS_VALUES, errors)
    _validate_value(f"files[{index}].confidence", node.get("confidence"), CONFIDENCE_VALUES, errors)
    _validate_value(f"files[{index}].node_type", node.get("node_type"), NODE_TYPES, errors)
    _validate_value(f"files[{index}].extractor", node.get("extractor"), EXTRACTOR_VALUES, errors)
    evidence = node.get("evidence")
    if isinstance(evidence, dict):
        _validate_evidence_domains(f"files[{index}].evidence", evidence, errors)
        _validate_evidence_match(index, "files", node, evidence, ("freshness", "confidence", "node_type"), errors)


def _validate_edge_v2(edge: dict[str, Any], index: int, errors: list[str]) -> None:
    _validate_value(f"edges[{index}].edge_type", edge.get("edge_type"), EDGE_TYPES, errors)
    _validate_value(f"edges[{index}].freshness", edge.get("freshness"), FRESHNESS_VALUES, errors)
    _validate_value(f"edges[{index}].confidence", edge.get("confidence"), CONFIDENCE_VALUES, errors)
    _validate_value(f"edges[{index}].extractor", edge.get("extractor"), EXTRACTOR_VALUES, errors)
    if edge.get("edge_type") == "unknown" and not _nonempty_text(edge.get("unknown_reason")):
        errors.append(f"edges[{index}].unknown_reason is required when edge_type is unknown")
    evidence = edge.get("evidence")
    if isinstance(evidence, dict):
        _validate_evidence_domains(f"edges[{index}].evidence", evidence, errors)
        if "edge_type" in evidence:
            _validate_value(f"edges[{index}].evidence.edge_type", evidence.get("edge_type"), EDGE_TYPES, errors)
        _validate_evidence_match(index, "edges", edge, evidence, ("freshness", "confidence", "edge_type"), errors)


def _validate_symbol_v2(symbol: dict[str, Any], index: int, errors: list[str]) -> None:
    _validate_value(f"symbols[{index}].freshness", symbol.get("freshness"), FRESHNESS_VALUES, errors)
    _validate_value(f"symbols[{index}].confidence", symbol.get("confidence"), CONFIDENCE_VALUES, errors)
    _validate_value(f"symbols[{index}].extractor", symbol.get("extractor"), EXTRACTOR_VALUES, errors)
    evidence = symbol.get("evidence")
    if isinstance(evidence, dict):
        _validate_evidence_domains(f"symbols[{index}].evidence", evidence, errors)
        _validate_evidence_match(index, "symbols", symbol, evidence, ("freshness", "confidence"), errors)


def _validate_generated_artifact_v2(item: dict[str, Any], index: int, errors: list[str]) -> None:
    _validate_value(f"generated_artifacts[{index}].freshness", item.get("freshness"), FRESHNESS_VALUES, errors)
    _validate_value(f"generated_artifacts[{index}].confidence", item.get("confidence"), CONFIDENCE_VALUES, errors)
    _validate_value(f"generated_artifacts[{index}].extractor", item.get("extractor"), EXTRACTOR_VALUES, errors)
    source_of_truth = item.get("source_of_truth")
    has_source_of_truth = bool(source_of_truth)
    has_source_path = _nonempty_text(item.get("source_path"))
    confidence = str(item.get("confidence") or "")
    if not has_source_of_truth or not has_source_path:
        if confidence not in {"low", "unknown"}:
            errors.append(
                f"generated_artifacts[{index}].confidence must be low/unknown when source_of_truth or source_path is missing"
            )
        if not _nonempty_text(item.get("unknown_reason")):
            errors.append(
                f"generated_artifacts[{index}].unknown_reason is required when source_of_truth or source_path is missing"
            )
    if item.get("edit_policy") == "edit source / do not edit generated" and not has_source_of_truth:
        errors.append(
            f"generated_artifacts[{index}].source_of_truth is required when edit_policy is edit source / do not edit generated"
        )


def _validate_evidence_domains(context: str, evidence: dict[str, Any], errors: list[str]) -> None:
    if "freshness" in evidence:
        _validate_value(f"{context}.freshness", evidence.get("freshness"), FRESHNESS_VALUES, errors)
    if "confidence" in evidence:
        _validate_value(f"{context}.confidence", evidence.get("confidence"), CONFIDENCE_VALUES, errors)
    if "node_type" in evidence:
        _validate_value(f"{context}.node_type", evidence.get("node_type"), NODE_TYPES, errors)
    if "extractor" in evidence:
        _validate_value(f"{context}.extractor", evidence.get("extractor"), EXTRACTOR_VALUES, errors)


def _validate_evidence_match(
    index: int,
    collection: str,
    item: dict[str, Any],
    evidence: dict[str, Any],
    fields: tuple[str, ...],
    errors: list[str],
) -> None:
    for field in fields:
        if field in evidence and field in item and evidence.get(field) != item.get(field):
            errors.append(
                f"{collection}[{index}].{field} must match evidence.{field}: "
                f"{item.get(field)!r} != {evidence.get(field)!r}"
            )


def _validate_value(context: str, value: object, allowed: set[str], errors: list[str]) -> None:
    if str(value or "") not in allowed:
        errors.append(f"{context} must be one of {sorted(allowed)}")


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, help="RepositoryGraph JSON path.")
    args = parser.parse_args(argv)
    document = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    errors = validate_repository_graph(document)
    if errors:
        for error in errors:
            print(f"validate-repository-graph: ERROR: {error}")
        return 1
    graph = document["repository_graph"]
    print(
        "validate-repository-graph: validated "
        f"{len(graph.get('files', []))} files and {len(graph.get('edges', []))} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
