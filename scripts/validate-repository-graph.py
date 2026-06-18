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

    if graph.get("schema_version") != 1:
        errors.append("repository_graph.schema_version must be 1")
    repo_hash = graph.get("repo_hash")
    if not isinstance(repo_hash, str) or not repo_hash:
        errors.append("repository_graph.repo_hash must be present")
    elif _is_user_absolute_path(repo_hash):
        errors.append("repository_graph.repo_hash must not contain an absolute path")
    if not graph.get("indexed_at"):
        errors.append("repository_graph.indexed_at must be present")

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
