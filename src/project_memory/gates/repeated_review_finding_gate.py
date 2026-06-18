"""Repeated review finding aggregation gate."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def evaluate_repeated_review_finding_gate(
    events: Iterable[dict[str, Any]],
    *,
    threshold: int = 2,
) -> dict[str, Any]:
    """Surface review findings that recur across memory events."""
    counts: Counter[tuple[str, str]] = Counter()
    for event in events:
        if event.get("type") != "review_finding":
            continue
        refs = event.get("evidence_refs") or ["review_finding"]
        key = str(refs[0]) if refs else "review_finding"
        for path in event.get("paths") or []:
            counts[(str(path), key)] += 1
    findings = [
        {"path": path, "finding_key": key, "count": count}
        for (path, key), count in sorted(counts.items())
        if count >= threshold
    ]
    return {
        "repeated_review_finding_gate": {
            "repeated": bool(findings),
            "findings": findings[:50],
        }
    }

