"""Fragile File Gate for Project Memory Governance."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from project_memory.privacy import clean_paths


FRAGILE_SIGNAL_TYPES = {"review_finding", "repair_attempt", "fragile_file"}
REQUIRED_EVIDENCE = (
    "read_file_evidence",
    "nearby_test_evidence",
    "memory_summary_evidence",
    "implementation_preflight",
)


def fragile_file_counts(events: Iterable[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for event in events:
        if not _is_fragile_signal(event):
            continue
        for path in event.get("paths") or []:
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
    if event.get("type") in FRAGILE_SIGNAL_TYPES:
        return True
    return event.get("type") == "validation_result" and event.get("outcome") in {"failed", "blocked"}

