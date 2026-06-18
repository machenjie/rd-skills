"""Fragile File Gate for Project Memory Governance."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from project_memory.privacy import clean_paths


FRAGILE_SIGNAL_TYPES = {"review_finding", "repair_attempt", "fragile_file"}
REQUIRED_EVIDENCE = (
    "read_file_evidence",
    "owner_source_of_truth_check",
    "same_pattern_scan",
    "validator_mapping",
    "nearby_test_evidence",
    "memory_summary_evidence",
    "implementation_preflight",
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
) -> dict[str, Any]:
    """Require preflight evidence before editing historically fragile files."""
    counts = fragile_file_counts(events)
    requested = clean_paths(list(paths))
    matched = [path for path in requested if counts.get(path, 0) >= threshold]
    evidence = evidence or {}
    missing = [name for name in REQUIRED_EVIDENCE if not bool(evidence.get(name))]
    fragile = bool(matched)
    return {
        "fragile_file_gate": {
            "fragile": fragile,
            "matched_paths": matched,
            "required_preflight": list(REQUIRED_EVIDENCE),
            "missing": missing if fragile else [],
            "allowed_to_continue": not (fragile and missing and mode == "block"),
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
