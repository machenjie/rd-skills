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
            if isinstance(symbol.get("path"), str) and _is_user_absolute_path(symbol["path"]):
                errors.append(f"symbols[{index}].path must be repository-relative")
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
