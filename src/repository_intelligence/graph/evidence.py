"""Evidence metadata for repository graph nodes and edges."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from repository_intelligence.graph.file_classifier import classify_role


FRESHNESS_VALUES = {"current", "stale", "unknown", "not_applicable"}
CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}

_CONFIDENCE_SCORE = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
_FRESHNESS_SCORE = {"current": 3, "not_applicable": 2, "unknown": 1, "stale": 0}


@dataclass(frozen=True)
class GraphNodeEvidence:
    node_id: str
    path: str
    symbol: str | None
    node_type: str
    language: str
    extractor: str
    source_hash: str | None
    freshness: str
    confidence: str
    generated_artifact: bool
    source_of_truth: str | list[str] | None
    unknown_reason: str | None
    last_indexed_at: str | None

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class GraphEdgeEvidence:
    edge_type: str
    from_node: str
    to_node: str
    confidence: str
    freshness: str
    extractor: str
    unknown_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def file_source_hash(path: str | Path) -> str | None:
    """Return a SHA-256 hash for one file without embedding path content."""
    candidate = Path(path)
    if not candidate.is_file():
        return None
    digest = hashlib.sha256()
    digest.update(candidate.read_bytes())
    return digest.hexdigest()


def extractor_for_kind(kind: str) -> str:
    if kind == "python":
        return "python_symbol_extractor"
    if kind == "markdown":
        return "markdown_reference_extractor"
    if kind in {"yaml", "json"}:
        return "yaml_reference_extractor"
    if kind in {"javascript", "go", "rust", "java", "shell", "toml"}:
        return "file_heuristic"
    return "unknown"


def confidence_for_file(kind: str, *, has_index_error: bool = False, generated_artifact: bool = False) -> str:
    if generated_artifact:
        return "medium"
    if has_index_error:
        return "low"
    if kind == "python":
        return "high"
    if kind in {"yaml", "json"}:
        return "high"
    if kind == "markdown":
        return "medium"
    if kind in {"javascript", "go", "rust", "java", "shell", "toml"}:
        return "low"
    return "unknown"


def unknown_reason_for_kind(kind: str, *, has_index_error: bool = False) -> str | None:
    if has_index_error:
        return "extractor_error"
    if kind in {"javascript", "go", "rust", "java", "shell", "toml"}:
        return "unsupported_language_uses_file_heuristic"
    if kind == "unknown":
        return "unsupported_file_type"
    return None


def node_type_for_file(path: str, role: str) -> str:
    if role == "test":
        return "test"
    if role == "generated_artifact" or classify_role(path) == "generated_artifact":
        return "generated_artifact"
    return "file"


def node_type_for_symbol(kind: str) -> str:
    if kind in {"class", "function", "method", "config_key"}:
        return kind
    if kind == "heading":
        return "reference"
    return "unknown"


def build_file_node_evidence(
    *,
    repo_root: str | Path,
    relative_path: str,
    kind: str,
    role: str,
    last_indexed_at: str | None,
    source_of_truth: str | list[str] | None = None,
    unknown_reason: str | None = None,
    confidence: str | None = None,
) -> GraphNodeEvidence:
    source_hash = file_source_hash(Path(repo_root) / relative_path)
    generated_artifact = role == "generated_artifact"
    reason = unknown_reason or unknown_reason_for_kind(kind)
    inferred_confidence = confidence or confidence_for_file(kind, generated_artifact=generated_artifact)
    if generated_artifact and not source_of_truth:
        inferred_confidence = "low"
        reason = reason or "generated_source_of_truth_unknown"
    return GraphNodeEvidence(
        node_id=relative_path,
        path=relative_path,
        symbol=None,
        node_type=node_type_for_file(relative_path, role),
        language=kind,
        extractor=extractor_for_kind(kind),
        source_hash=source_hash,
        freshness="current" if source_hash else "unknown",
        confidence=_normalize_confidence(inferred_confidence),
        generated_artifact=generated_artifact,
        source_of_truth=source_of_truth,
        unknown_reason=reason,
        last_indexed_at=last_indexed_at,
    )


def build_symbol_node_evidence(
    *,
    symbol: dict[str, object],
    file_node: dict[str, Any],
) -> GraphNodeEvidence:
    path = str(file_node.get("path") or symbol.get("path") or "")
    name = str(symbol.get("name") or "")
    kind = str(symbol.get("kind") or "unknown")
    file_evidence = evidence_from_node(file_node)
    confidence = _normalize_confidence(str(symbol.get("confidence") or file_evidence.get("confidence") or "unknown"))
    return GraphNodeEvidence(
        node_id=f"{path}::{name}" if name else path,
        path=path,
        symbol=name or None,
        node_type=node_type_for_symbol(kind),
        language=str(symbol.get("language") or file_node.get("kind") or "unknown"),
        extractor=str(file_evidence.get("extractor") or extractor_for_kind(str(file_node.get("kind") or "unknown"))),
        source_hash=_optional_str(file_evidence.get("source_hash")),
        freshness=_normalize_freshness(str(file_evidence.get("freshness") or "unknown")),
        confidence=confidence,
        generated_artifact=bool(file_evidence.get("generated_artifact")),
        source_of_truth=file_evidence.get("source_of_truth"),
        unknown_reason=_optional_str(file_evidence.get("unknown_reason")),
        last_indexed_at=_optional_str(file_evidence.get("last_indexed_at")),
    )


def evidence_from_node(node: dict[str, Any]) -> dict[str, object]:
    evidence = node.get("evidence")
    if isinstance(evidence, dict):
        return evidence
    return {
        "node_id": node.get("node_id") or node.get("path") or "",
        "path": node.get("path") or "",
        "node_type": node.get("node_type") or "unknown",
        "language": node.get("language") or node.get("kind") or "unknown",
        "extractor": node.get("extractor") or extractor_for_kind(str(node.get("kind") or "unknown")),
        "source_hash": node.get("source_hash"),
        "freshness": node.get("freshness") or "unknown",
        "confidence": node.get("confidence") or "unknown",
        "generated_artifact": bool(node.get("generated_artifact")),
        "source_of_truth": node.get("source_of_truth"),
        "unknown_reason": node.get("unknown_reason"),
        "last_indexed_at": node.get("last_indexed_at"),
    }


def attach_node_evidence(node: dict[str, Any], evidence: GraphNodeEvidence | dict[str, object]) -> dict[str, Any]:
    data = evidence.to_dict() if isinstance(evidence, GraphNodeEvidence) else dict(evidence)
    node["evidence"] = data
    for field in (
        "node_id",
        "node_type",
        "language",
        "extractor",
        "source_hash",
        "freshness",
        "confidence",
        "generated_artifact",
        "source_of_truth",
        "unknown_reason",
        "last_indexed_at",
    ):
        if field in data:
            node[field] = data[field]
    return node


def attach_edge_evidence(edge: dict[str, Any], evidence: GraphEdgeEvidence | dict[str, object]) -> dict[str, Any]:
    data = evidence.to_dict() if isinstance(evidence, GraphEdgeEvidence) else dict(evidence)
    edge["evidence"] = data
    for field in ("confidence", "freshness", "extractor", "unknown_reason"):
        if field in data:
            edge[field] = data[field]
    edge["edge_type"] = data.get("edge_type", "unknown")
    return edge


def build_edge_evidence(edge: dict[str, Any], files_by_path: dict[str, dict[str, Any]]) -> GraphEdgeEvidence:
    source = str(edge.get("from") or "")
    target = str(edge.get("to") or "")
    old_type = str(edge.get("type") or "unknown")
    source_node = files_by_path.get(source)
    target_node = files_by_path.get(target)
    source_ev = evidence_from_node(source_node) if source_node else {}
    target_ev = evidence_from_node(target_node) if target_node else {}
    edge_type = _normalize_edge_type(old_type)
    extractor = _edge_extractor(old_type)
    confidence = _edge_confidence(old_type, source_ev, target_ev, bool(source_node), bool(target_node))
    freshness = _edge_freshness(source_ev, target_ev, edge_type, bool(source_node), bool(target_node))
    unknown_reason = _edge_unknown_reason(old_type, source_node, target_node, edge_type, freshness)
    return GraphEdgeEvidence(
        edge_type=edge_type,
        from_node=source,
        to_node=target,
        confidence=confidence,
        freshness=freshness,
        extractor=extractor,
        unknown_reason=unknown_reason,
    )


def refresh_node_evidence(node: dict[str, Any], repo_root: str | Path | None) -> dict[str, Any]:
    """Refresh one graph file node against the current filesystem state."""
    if repo_root is None:
        return node
    current = dict(node)
    evidence = dict(evidence_from_node(current))
    path = str(current.get("path") or evidence.get("path") or "")
    if not path:
        evidence["freshness"] = "unknown"
        evidence["unknown_reason"] = "missing_path"
        return attach_node_evidence(current, evidence)
    current_hash = file_source_hash(Path(repo_root) / path)
    if current_hash is None:
        evidence["freshness"] = "stale"
        evidence["unknown_reason"] = "source_file_missing"
    elif evidence.get("source_hash") and evidence.get("source_hash") != current_hash:
        evidence["freshness"] = "stale"
        evidence["current_source_hash"] = current_hash
        evidence["unknown_reason"] = "source_hash_mismatch"
    elif not evidence.get("source_hash"):
        evidence["freshness"] = "unknown"
        evidence["current_source_hash"] = current_hash
        evidence["unknown_reason"] = evidence.get("unknown_reason") or "source_hash_unknown"
    else:
        evidence["freshness"] = "current"
        evidence.pop("current_source_hash", None)
        if evidence.get("unknown_reason") == "source_hash_mismatch":
            evidence.pop("unknown_reason", None)

    if bool(evidence.get("generated_artifact")) and not evidence.get("source_of_truth"):
        evidence["confidence"] = "low"
        evidence["unknown_reason"] = evidence.get("unknown_reason") or "generated_source_of_truth_unknown"
    return attach_node_evidence(current, evidence)


def closure_eligible(evidence: dict[str, object] | None) -> bool:
    if not isinstance(evidence, dict):
        return False
    return evidence.get("freshness") == "current" and evidence.get("confidence") in {"high", "medium"}


def confidence_score(value: object) -> int:
    return _CONFIDENCE_SCORE.get(str(value or "unknown"), 0)


def freshness_score(value: object) -> int:
    return _FRESHNESS_SCORE.get(str(value or "unknown"), 0)


def _normalize_confidence(value: str) -> str:
    return value if value in CONFIDENCE_VALUES else "unknown"


def _normalize_freshness(value: str) -> str:
    return value if value in FRESHNESS_VALUES else "unknown"


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _normalize_edge_type(edge_type: str) -> str:
    if edge_type == "import":
        return "imports"
    if edge_type == "test_reference":
        return "tests"
    if edge_type in {"generated_artifact", "hook_template_reference"}:
        return "generates"
    if edge_type in {"registry_entry", "capability_used_by", "skill_selects_capability"}:
        return "depends_on"
    if edge_type in {"doc_reference", "routing_rule_reference", "validator_reference", "skill_reference"}:
        return "references"
    return "unknown"


def _edge_extractor(edge_type: str) -> str:
    if edge_type == "import":
        return "import_graph"
    if edge_type == "test_reference":
        return "test_graph"
    if edge_type in {"generated_artifact", "hook_template_reference"}:
        return "generated_artifact_graph"
    if edge_type in {"registry_entry", "capability_used_by", "skill_selects_capability", "doc_reference", "routing_rule_reference", "validator_reference", "skill_reference"}:
        return "reference_graph"
    return "unknown"


def _edge_confidence(
    edge_type: str,
    source_ev: dict[str, object],
    target_ev: dict[str, object],
    has_source: bool,
    has_target: bool,
) -> str:
    if edge_type == "import":
        return "high" if source_ev.get("language") == "python" and has_target else "medium"
    if edge_type in {"registry_entry", "capability_used_by", "skill_selects_capability"}:
        return "high"
    if edge_type in {"doc_reference", "routing_rule_reference", "validator_reference", "skill_reference"}:
        return "medium"
    if edge_type == "test_reference":
        return "medium"
    if edge_type in {"generated_artifact", "hook_template_reference"}:
        return "medium" if has_source else "low"
    if has_source and has_target:
        return "low"
    return "unknown"


def _edge_freshness(
    source_ev: dict[str, object],
    target_ev: dict[str, object],
    edge_type: str,
    has_source: bool,
    has_target: bool,
) -> str:
    source_freshness = str(source_ev.get("freshness") or "unknown")
    target_freshness = str(target_ev.get("freshness") or "unknown")
    if edge_type == "generates" and has_source and not has_target:
        return source_freshness if source_freshness in FRESHNESS_VALUES else "unknown"
    if has_source and has_target:
        if "stale" in {source_freshness, target_freshness}:
            return "stale"
        if source_freshness == "current" and target_freshness == "current":
            return "current"
        return "unknown"
    if edge_type == "generates":
        return "not_applicable"
    return "unknown"


def _edge_unknown_reason(
    edge_type: str,
    source_node: dict[str, Any] | None,
    target_node: dict[str, Any] | None,
    normalized_edge_type: str,
    freshness: str,
) -> str | None:
    if normalized_edge_type == "unknown":
        return f"unsupported_edge_type:{edge_type}"
    if freshness == "unknown":
        missing: list[str] = []
        if source_node is None:
            missing.append("from_node_not_indexed")
        if target_node is None and normalized_edge_type != "generates":
            missing.append("to_node_not_indexed")
        return ",".join(missing) or "edge_freshness_unknown"
    return None
