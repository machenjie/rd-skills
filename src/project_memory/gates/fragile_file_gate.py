"""Fragile File Gate for Project Memory Governance."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from project_memory.privacy import clean_paths
from project_memory.source_evidence import memory_hit_from_event, residual_risk_for_hit


FRAGILE_SIGNAL_TYPES = {"review_finding", "repair_attempt", "fragile_file"}
REQUIRED_EVIDENCE = (
    "read_file_evidence",
    "owner_source_of_truth_check",
    "same_pattern_scan",
    "validator_mapping",
    "nearby_test_evidence",
    "memory_summary_evidence",
    "implementation_preflight",
    "source_freshness_current",
)


def fragile_file_counts(events: Iterable[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for event in events:
        if not _is_fragile_signal(event):
            continue
        for path in _paths(event):
            counts[str(path)] += 1
    return counts


def evaluate_fragile_file_gate(
    events: Iterable[dict[str, Any]],
    *,
    paths: Iterable[str],
    evidence: dict[str, bool] | None = None,
    threshold: int = 2,
    mode: str = "warn",
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Require preflight evidence before editing historically fragile files."""
    event_list = [event for event in events if isinstance(event, dict)]
    counts = fragile_file_counts(event_list)
    requested = clean_paths(list(paths))
    current_counts: Counter[str] = Counter()
    source_status_by_path: dict[str, str] = {}
    evidence_role_by_path: dict[str, str] = {}
    residual_risk: list[str] = []
    for event in event_list:
        if not _is_fragile_signal(event):
            continue
        hit = memory_hit_from_event(event, repo_root=repo_root)
        risk = residual_risk_for_hit(hit)
        if risk:
            residual_risk.append(risk)
        for path in _paths(event):
            if path not in requested:
                continue
            _prefer_status(source_status_by_path, path, hit["source_status"])
            _prefer_status(evidence_role_by_path, path, hit["evidence_role"])
            if hit["source_status"] == "current" and hit["confidence"] == "strong":
                current_counts[path] += 1
    matched = [path for path in requested if current_counts.get(path, 0) >= threshold]
    historical = [
        path
        for path in requested
        if counts.get(path, 0) >= threshold and path not in matched
    ]
    effective_evidence = dict(evidence or {})
    if matched:
        effective_evidence["source_freshness_current"] = True
    missing = [name for name in REQUIRED_EVIDENCE if not bool(effective_evidence.get(name))]
    fragile = bool(matched or historical)
    can_block = bool(matched)
    return {
        "fragile_file_gate": {
            "fragile": fragile,
            "matched_paths": matched,
            "historical_hint_paths": historical,
            "warning_only_paths": historical,
            "source_status_by_path": source_status_by_path,
            "evidence_role_by_path": evidence_role_by_path,
            "required_preflight": list(REQUIRED_EVIDENCE),
            "missing": missing if fragile else [],
            "allowed_to_continue": not (can_block and missing and mode == "block"),
            "residual_risk": _unique(residual_risk),
        }
    }


def _is_fragile_signal(event: dict[str, Any]) -> bool:
    kind = str(event.get("kind") or "").strip()
    event_type = str(event.get("type") or "").strip()
    if kind in {"fragile_file", "review_finding_pattern"}:
        return True
    if event_type in FRAGILE_SIGNAL_TYPES:
        return True
    return event_type == "validation_result" and event.get("outcome") in {"failed", "blocked"}


def _paths(event: dict[str, Any]) -> list[str]:
    values = event.get("bounded_paths")
    if not isinstance(values, list):
        values = event.get("paths")
    if not isinstance(values, list):
        return []
    return [str(path) for path in values if str(path).strip()][:50]


def _prefer_status(target: dict[str, str], path: str, value: str) -> None:
    priority = {
        "current": 5,
        "closure_evidence": 5,
        "stale": 4,
        "warning_only": 4,
        "unknown": 3,
        "historical_hint": 3,
        "missing": 2,
        "deleted": 2,
        "generated": 1,
    }
    existing = target.get(path)
    if existing is None or priority.get(value, 0) > priority.get(existing, 0):
        target[path] = value


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
