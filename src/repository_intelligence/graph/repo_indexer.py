"""Repository graph indexer for rd-skills source artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repository_intelligence.cache.freshness import freshness_metadata
from repository_intelligence.cache.repo_hash import iter_indexed_files
from repository_intelligence.graph.file_classifier import classify_kind, classify_role
from repository_intelligence.graph.generated_artifact_graph import (
    build_generated_artifact_edges,
    build_generated_artifact_payload,
)
from repository_intelligence.graph.import_graph import build_import_edges
from repository_intelligence.graph.markdown_reference_extractor import extract_markdown_file
from repository_intelligence.graph.ownership_graph import (
    build_module_boundaries,
    build_ownership_edges,
    build_ownership_payload,
)
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


def _lightweight_node_symbols(relative_path: str, kind: str) -> list[dict[str, object]]:
    if kind in {"python", "markdown", "yaml", "json"}:
        return []
    return [
        {
            "name": Path(relative_path).stem,
            "kind": "unknown",
            "path": relative_path,
            "line": 1,
            "line_start": 1,
            "line_end": 1,
            "visibility": "public" if not Path(relative_path).name.startswith("_") else "private",
            "owner_object": None,
            "parent_symbol": None,
            "language": kind if kind != "unknown" else "unknown",
            "confidence": "low",
        }
    ]


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
        else:
            node["symbols"] = _lightweight_node_symbols(relative_path, kind)
    except Exception as exc:
        node["references"] = [{"kind": "index_error", "error_kind": type(exc).__name__, "value": str(exc), "line": 0}]
    return node


def _normalize_symbol(symbol: dict[str, object], file_node: dict[str, Any]) -> dict[str, object]:
    path = str(file_node.get("path") or symbol.get("path") or "")
    kind = str(symbol.get("kind") or "unknown")
    if kind not in {"function", "class", "method", "constant", "heading", "config_key", "unknown"}:
        kind = "unknown"
    language = str(symbol.get("language") or file_node.get("kind") or "unknown")
    line = symbol.get("line") or symbol.get("line_start") or 0
    return {
        "name": str(symbol.get("name") or ""),
        "kind": kind,
        "path": path,
        "line": line,
        "line_start": symbol.get("line_start") or line,
        "line_end": symbol.get("line_end") or line,
        "visibility": str(symbol.get("visibility") or _visibility_for_name(str(symbol.get("name") or ""))),
        "owner_object": symbol.get("owner_object"),
        "parent_symbol": symbol.get("parent_symbol"),
        "language": language,
        "confidence": str(symbol.get("confidence") or _confidence_for_kind(language)),
    }


def _flatten_symbols(files: list[dict[str, Any]]) -> list[dict[str, object]]:
    symbols: list[dict[str, object]] = []
    for file_node in files:
        for symbol in file_node.get("symbols", []):
            if isinstance(symbol, dict):
                normalized = _normalize_symbol(symbol, file_node)
                if normalized["name"]:
                    symbols.append(normalized)
    return symbols


def _visibility_for_name(name: str) -> str:
    if name.startswith("__") and name.endswith("__"):
        return "dunder"
    if name.startswith("_"):
        return "private"
    return "public"


def _confidence_for_kind(language: str) -> str:
    return "high" if language in {"python", "markdown", "yaml", "json", "structured"} else "low"


def _validation_candidates() -> list[dict[str, object]]:
    try:
        from validation_broker.command_registry import registry_commands
    except Exception:
        return [
            {
                "command": "unknown",
                "scope": "unknown",
                "category": "unknown",
                "reason": "validation broker command registry could not be imported",
                "covered_path_patterns": [],
                "covered_risk_surfaces": ["unknown"],
            }
        ]
    return [
        {
            "command": command.command,
            "scope": command.level,
            "category": command.category,
            "reason": command.reason,
            "covered_path_patterns": list(command.covered_path_patterns),
            "covered_risk_surfaces": list(command.covered_risk_surfaces),
        }
        for command in registry_commands()
    ]


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
    ownership = build_ownership_payload(files_by_path)
    freshness = {
        "status": "current",
        "repo_hash": metadata.get("repo_hash"),
        "artifact_hash": metadata.get("artifact_hash"),
        "created_at": metadata.get("indexed_at"),
        "commit_sha": metadata.get("indexed_commit"),
        "indexed_at": metadata.get("indexed_at"),
        "indexed_commit": metadata.get("indexed_commit"),
        **({"fallback_mtime": metadata.get("fallback_mtime")} if metadata.get("fallback_mtime") is not None else {}),
    }

    return {
        "repository_graph": {
            "schema_version": 2,
            **metadata,
            "created_at": metadata.get("indexed_at"),
            "commit_sha": metadata.get("indexed_commit"),
            "files": files,
            "symbols": _flatten_symbols(files),
            "edges": dedupe_edges(edges),
            "module_boundaries": build_module_boundaries(files_by_path),
            "ownership": ownership,
            "generated_artifacts": build_generated_artifact_payload(files_by_path),
            "validation_candidates": _validation_candidates(),
            "freshness": freshness,
        }
    }
