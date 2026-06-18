"""Repository graph indexer for rd-skills source artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repository_intelligence.cache.freshness import freshness_metadata
from repository_intelligence.cache.repo_hash import iter_indexed_files
from repository_intelligence.graph.file_classifier import classify_kind, classify_role
from repository_intelligence.graph.generated_artifact_graph import build_generated_artifact_edges
from repository_intelligence.graph.import_graph import build_import_edges
from repository_intelligence.graph.markdown_reference_extractor import extract_markdown_file
from repository_intelligence.graph.ownership_graph import build_ownership_edges
from repository_intelligence.graph.python_symbol_extractor import extract_python_file
from repository_intelligence.graph.reference_graph import build_reference_edges, dedupe_edges
from repository_intelligence.graph.test_graph import build_test_edges
from repository_intelligence.graph.yaml_reference_extractor import extract_structured_file


def _empty_node(relative_path: str, kind: str, role: str) -> dict[str, Any]:
    return {
        "path": relative_path,
        "kind": kind,
        "role": role,
        "symbols": [],
        "frontmatter": {},
        "headings": [],
        "references": [],
    }


def _index_file(path: Path, relative_path: str, repo_root: Path) -> dict[str, Any]:
    kind = classify_kind(relative_path)
    role = classify_role(relative_path)
    node = _empty_node(relative_path, kind, role)
    try:
        if kind == "python":
            extracted = extract_python_file(path, repo_root)
            node["symbols"] = extracted.get("symbols", [])
            node["imports"] = extracted.get("imports", [])
            node["references"] = extracted.get("references", [])
        elif kind == "markdown":
            extracted = extract_markdown_file(path, repo_root)
            node["frontmatter"] = extracted.get("frontmatter", {})
            node["headings"] = extracted.get("headings", [])
            node["symbols"] = extracted.get("headings", [])
            node["references"] = extracted.get("references", [])
        elif kind in {"yaml", "json"}:
            extracted = extract_structured_file(path, repo_root)
            node["frontmatter"] = extracted.get("frontmatter", {})
            node["symbols"] = extracted.get("symbols", [])
            node["references"] = extracted.get("references", [])
    except Exception as exc:
        node["references"] = [{"kind": "index_error", "value": str(exc), "line": 0}]
    return node


def build_repository_graph(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    metadata = freshness_metadata(root)
    files: list[dict[str, Any]] = []
    for relative in iter_indexed_files(root):
        relative_path = relative.as_posix()
        files.append(_index_file(root / relative, relative_path, root))

    files_by_path = {str(file_node["path"]): file_node for file_node in files}
    edges: list[dict[str, str]] = []
    for file_node in files:
        if file_node.get("kind") == "python":
            edges.extend(build_import_edges(file_node, root))
        edges.extend(build_reference_edges(file_node, files_by_path))
    edges.extend(build_test_edges(files_by_path))
    edges.extend(build_ownership_edges(files_by_path))
    edges.extend(build_generated_artifact_edges(files_by_path))

    return {
        "repository_graph": {
            "schema_version": 1,
            **metadata,
            "files": files,
            "edges": dedupe_edges(edges),
        }
    }
