"""Source freshness helpers for Project Memory Governance."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


SOURCE_STATUSES = {"current", "stale", "missing", "unknown", "deleted", "generated"}
EVIDENCE_ROLES = {"closure_evidence", "historical_hint", "warning_only"}
RETRIEVAL_CONFIDENCES = {"strong", "partial", "weak"}
FRESHNESS_VALUES = {"current", "stale", "unknown", "not_applicable"}
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
GENERATED_PREFIXES = ("dist/", "build/", "generated/", "src/generated/")


def sha256_file(path: str | Path) -> str:
    """Return a full sha256 hash for the current file contents."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: object) -> bool:
    """Return True when a value is a lowercase or uppercase full sha256 hex digest."""
    return bool(HASH_RE.fullmatch(str(value or "").strip().casefold()))


def is_generated_artifact_path(path: object) -> bool:
    """Return True for repository-relative paths that look generated."""
    normalized = _normalize_rel_path(path)
    if not normalized:
        return False
    return (
        normalized.startswith(GENERATED_PREFIXES)
        or "/generated/" in normalized
        or normalized.endswith(".generated.py")
        or normalized.endswith(".generated.ts")
        or normalized.endswith(".generated.js")
    )


def memory_hit_from_event(
    event: dict[str, Any],
    *,
    repo_root: str | Path | None = None,
) -> dict[str, str]:
    """Return the public retrieval-hit status for one memory event."""
    status = source_status_for_event(event, repo_root=repo_root)
    source_status = status["source_status"]
    if source_status == "current":
        if _has_current_closure_evidence(event):
            confidence = "strong"
            role = "closure_evidence"
            reason = "current source hash and current validation/review evidence"
        else:
            confidence = "partial"
            role = "warning_only"
            reason = "current source hash without current validation/review evidence"
    elif source_status == "generated":
        confidence = "weak"
        role = "warning_only"
        reason = status["reason"]
    else:
        confidence = "weak"
        role = "historical_hint"
        reason = status["reason"]
    path = status.get("repo_rel_path") or _first_event_path(event)
    return {
        "event_id": str(event.get("event_id") or ""),
        "path": path,
        "kind": str(event.get("kind") or event.get("type") or ""),
        "confidence": confidence,
        "source_status": source_status,
        "evidence_role": role,
        "reason": reason,
    }


def source_status_for_event(
    event: dict[str, Any],
    *,
    repo_root: str | Path | None = None,
) -> dict[str, str]:
    """Evaluate a memory event against current source without reading raw content."""
    evidence = event.get("source_evidence") if isinstance(event, dict) else None
    evidence = evidence if isinstance(evidence, dict) else {}
    path = _normalize_rel_path(evidence.get("repo_rel_path") or _first_event_path(event))
    stored_hash = str(evidence.get("source_hash") or "").strip().casefold()
    graph_freshness = _freshness(evidence.get("graph_freshness"))
    validation_freshness = _freshness(evidence.get("validation_freshness"))

    if path and is_generated_artifact_path(path) and not _has_source_of_truth(event):
        return {
            "repo_rel_path": path,
            "source_status": "generated",
            "reason": "generated artifact requires source_of_truth evidence",
        }
    if not evidence:
        return {
            "repo_rel_path": path,
            "source_status": "unknown",
            "reason": "missing source_evidence",
        }
    if not path:
        return {
            "repo_rel_path": "",
            "source_status": "missing",
            "reason": "missing source path",
        }
    if not is_sha256(stored_hash):
        return {
            "repo_rel_path": path,
            "source_status": "unknown",
            "reason": "missing source hash",
        }
    if repo_root is None:
        return {
            "repo_rel_path": path,
            "source_status": "unknown",
            "reason": "current source unavailable for hash check",
        }
    source_path = Path(repo_root) / path
    if not source_path.exists():
        return {
            "repo_rel_path": path,
            "source_status": "deleted",
            "reason": "source path no longer exists",
        }
    if not source_path.is_file():
        return {
            "repo_rel_path": path,
            "source_status": "missing",
            "reason": "source path is not a file",
        }
    current_hash = sha256_file(source_path)
    if current_hash != stored_hash:
        return {
            "repo_rel_path": path,
            "source_status": "stale",
            "reason": "source hash mismatch",
        }
    if graph_freshness == "stale" or validation_freshness == "stale":
        return {
            "repo_rel_path": path,
            "source_status": "stale",
            "reason": "source freshness marker is stale",
        }
    return {
        "repo_rel_path": path,
        "source_status": "current",
        "reason": "source hash matches current file",
    }


def residual_risk_for_hit(hit: dict[str, str]) -> str:
    """Return the residual-risk label implied by a non-current memory hit."""
    status = str(hit.get("source_status") or "")
    if status == "current":
        return ""
    if status == "generated":
        return "project_memory_generated_artifact_requires_source_of_truth"
    return f"project_memory_{status}_source"


def _has_current_closure_evidence(event: dict[str, Any]) -> bool:
    evidence = event.get("source_evidence") if isinstance(event, dict) else None
    evidence = evidence if isinstance(evidence, dict) else {}
    if _freshness(evidence.get("graph_freshness")) not in {"current", "not_applicable"}:
        return False
    if _freshness(evidence.get("validation_freshness")) != "current":
        return False
    refs = " ".join(str(ref).casefold() for ref in event.get("evidence_refs") or [])
    kind = str(event.get("kind") or "").casefold()
    event_type = str(event.get("type") or "").casefold()
    return any(
        token in refs
        for token in ("validation", "review", "rereview", "re-review", "fresh_after_last_edit:true")
    ) or kind in {"validation_pattern", "review_finding_pattern"} or event_type in {
        "validation_result",
        "validated_command",
        "review_finding",
    }


def _has_source_of_truth(event: dict[str, Any]) -> bool:
    evidence = event.get("source_evidence") if isinstance(event, dict) else None
    if isinstance(evidence, dict) and str(evidence.get("source_of_truth") or "").strip():
        return True
    refs = [str(ref).casefold() for ref in event.get("evidence_refs") or []]
    return any("source_of_truth:" in ref or "source-of-truth:" in ref for ref in refs)


def _freshness(value: object) -> str:
    text = str(value or "").strip().casefold()
    return text if text in FRESHNESS_VALUES else "unknown"


def _first_event_path(event: dict[str, Any]) -> str:
    values = event.get("bounded_paths")
    if not isinstance(values, list):
        values = event.get("paths")
    if not isinstance(values, list):
        return ""
    for value in values:
        path = _normalize_rel_path(value)
        if path:
            return path
    return ""


def _normalize_rel_path(value: object) -> str:
    text = str(value or "").strip().replace("\\", "/").lstrip("./")
    if not text or text.startswith("../") or "/../" in text or text == "..":
        return ""
    return text[:200]
