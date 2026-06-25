"""Repository graph indexer for rd-skills source artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repository_intelligence.cache.freshness import freshness_metadata
from repository_intelligence.cache.repo_hash import iter_indexed_files
from repository_intelligence.graph.evidence import (
    attach_edge_evidence,
    attach_node_evidence,
    build_edge_evidence,
    build_file_node_evidence,
    build_symbol_node_evidence,
    confidence_for_file,
    unknown_reason_for_kind,
)
from repository_intelligence.graph.file_classifier import classify_kind, classify_role
from repository_intelligence.graph.generated_artifact_graph import (
    build_generated_artifact_edges,
    build_generated_artifact_payload,
    generated_source_of_truth,
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


def _index_file(path: Path, relative_path: str, repo_root: Path, indexed_at: str | None) -> dict[str, Any]:
    kind = classify_kind(relative_path)
    role = classify_role(relative_path)
    node = _empty_node(relative_path, kind, role)
    source_of_truth = generated_source_of_truth(relative_path, {}) if role == "generated_artifact" else None
    has_index_error = False
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
        has_index_error = True
        node["references"] = [{"kind": "index_error", "error_kind": type(exc).__name__, "value": str(exc), "line": 0}]
    if any(isinstance(ref, dict) and ref.get("kind") == "index_error" for ref in node.get("references", [])):
        has_index_error = True
    evidence = build_file_node_evidence(
        repo_root=repo_root,
        relative_path=relative_path,
        kind=kind,
        role=role,
        last_indexed_at=indexed_at,
        source_of_truth=source_of_truth,
        unknown_reason=unknown_reason_for_kind(kind, has_index_error=has_index_error),
        confidence=confidence_for_file(kind, has_index_error=has_index_error, generated_artifact=role == "generated_artifact"),
    )
    attach_node_evidence(node, evidence)
    return node


def _normalize_symbol(symbol: dict[str, object], file_node: dict[str, Any]) -> dict[str, object]:
    path = str(file_node.get("path") or symbol.get("path") or "")
    kind = str(symbol.get("kind") or "unknown")
    if kind not in {"function", "class", "method", "constant", "heading", "config_key", "unknown"}:
        kind = "unknown"
    language = str(symbol.get("language") or file_node.get("kind") or "unknown")
    line = symbol.get("line") or symbol.get("line_start") or 0
    normalized = {
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
    evidence = build_symbol_node_evidence(symbol=normalized, file_node=file_node).to_dict()
    normalized["evidence"] = evidence
    for field in (
        "node_id",
        "node_type",
        "extractor",
        "source_hash",
        "freshness",
        "generated_artifact",
        "source_of_truth",
        "unknown_reason",
        "last_indexed_at",
    ):
        if field in evidence:
            normalized[field] = evidence[field]
    return normalized


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
                "confidence": "unknown",
                "freshness": "unknown",
                "extractor": "validation_broker.command_registry",
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
            "confidence": "medium",
            "freshness": "not_applicable",
            "extractor": "validation_broker.command_registry",
        }
        for command in registry_commands()
    ]


def _attach_edge_evidence(edges: list[dict[str, str]], files_by_path: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for edge in edges:
        edge_payload: dict[str, Any] = dict(edge)
        attach_edge_evidence(edge_payload, build_edge_evidence(edge_payload, files_by_path))
        enriched.append(edge_payload)
    return enriched


def _refresh_generated_file_evidence(files_by_path: dict[str, dict[str, Any]]) -> None:
    for path, file_node in files_by_path.items():
        if file_node.get("role") != "generated_artifact":
            continue
        source_of_truth = generated_source_of_truth(path, files_by_path)
        evidence = dict(file_node.get("evidence") if isinstance(file_node.get("evidence"), dict) else {})
        evidence["source_of_truth"] = source_of_truth or None
        evidence["confidence"] = "medium" if source_of_truth else "low"
        if source_of_truth:
            evidence.pop("unknown_reason", None)
        else:
            evidence["unknown_reason"] = "generated_source_of_truth_unknown"
        attach_node_evidence(file_node, evidence)


def build_repository_graph(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    metadata = freshness_metadata(root)
    files: list[dict[str, Any]] = []
    for relative in iter_indexed_files(root):
        relative_path = relative.as_posix()
        files.append(_index_file(root / relative, relative_path, root, str(metadata.get("indexed_at") or "")))

    files_by_path = {str(file_node["path"]): file_node for file_node in files}
    _refresh_generated_file_evidence(files_by_path)
    edges: list[dict[str, str]] = []
    for file_node in files:
        if file_node.get("kind") == "python":
            edges.extend(build_import_edges(file_node, root))
        edges.extend(build_reference_edges(file_node, files_by_path))
    edges.extend(build_test_edges(files_by_path))
    edges.extend(build_ownership_edges(files_by_path))
    edges.extend(build_generated_artifact_edges(files_by_path))
    enriched_edges = _attach_edge_evidence(dedupe_edges(edges), files_by_path)
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
            "edges": enriched_edges,
            "module_boundaries": build_module_boundaries(files_by_path),
            "ownership": ownership,
            "generated_artifacts": build_generated_artifact_payload(files_by_path),
            "validation_candidates": _validation_candidates(),
            "freshness": freshness,
        }
    }
