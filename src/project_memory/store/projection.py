"""Generated projections over append-only project memory events."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from project_memory import MEMORY_SCHEMA_VERSION
from project_memory.privacy import now_utc, sanitize_memory_query


FAILURE_OUTCOMES = {"failed", "blocked", "partial"}
FRAGILE_TYPES = {"review_finding", "repair_attempt", "fragile_file"}
DECISION_TYPES = {"accepted_decision", "rejected_decision", "route_decision"}


def build_memory_summary(
    events: Iterable[dict[str, Any]],
    query: dict[str, Any] | None = None,
    *,
    fragile_threshold: int = 2,
    max_items: int = 50,
) -> dict[str, Any]:
    """Build a bounded MemorySummary projection for a task/path query."""
    sanitized_query = sanitize_memory_query(query or {})
    relevant = [
        event for event in events if _matches_query(event, sanitized_query, include_empty_query=True)
    ]
    relevant.sort(key=lambda event: str(event.get("created_at", "")), reverse=True)
    path_counts: Counter[str] = Counter()
    review_counts: Counter[tuple[str, str]] = Counter()
    review_refs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for event in relevant:
        for path in event.get("paths", []) or []:
            if _fragile_signal(event):
                path_counts[path] += 1
            if event.get("type") == "review_finding":
                key = (path, _finding_key(event))
                review_counts[key] += 1
                review_refs[key].extend(_refs(event))
    summary = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "repo_hash": sanitized_query.get("repo_hash") or _first_value(relevant, "repo_hash"),
        "task_fingerprint": sanitized_query.get("task_fingerprint")
        or _first_value(relevant, "task_fingerprint"),
        "generated_at": now_utc(),
        "relevant_prior_decisions": _bounded(
            (
                _event_brief(event)
                for event in relevant
                if event.get("type") in DECISION_TYPES
            ),
            max_items,
        ),
        "prior_failures": _bounded(
            (
                _event_brief(event)
                for event in relevant
                if event.get("outcome") in FAILURE_OUTCOMES
            ),
            max_items,
        ),
        "fragile_files": _bounded(
            (
                {
                    "path": path,
                    "signal_count": count,
                    "required_preflight": [
                        "read_file_evidence",
                        "nearby_test_evidence",
                        "memory_summary_evidence",
                        "implementation_preflight",
                    ],
                }
                for path, count in sorted(path_counts.items())
                if count >= fragile_threshold
            ),
            max_items,
        ),
        "validated_commands": _bounded(
            (
                _event_brief(event)
                for event in relevant
                if event.get("type") == "validated_command"
                or (
                    event.get("type") == "validation_result"
                    and event.get("outcome") == "success"
                )
            ),
            max_items,
        ),
        "repeated_review_findings": _bounded(
            (
                {
                    "path": path,
                    "finding_key": finding,
                    "count": count,
                    "evidence_refs": sorted(set(review_refs[(path, finding)]))[:10],
                }
                for (path, finding), count in sorted(review_counts.items())
                if count >= 2
            ),
            max_items,
        ),
        "stale_context_warnings": _bounded(
            (
                _event_brief(event)
                for event in relevant
                if event.get("type") == "context_pack"
                and (
                    event.get("outcome") in {"failed", "blocked", "partial"}
                    or any("stale" in ref.casefold() for ref in _refs(event))
                )
            ),
            max_items,
        ),
        "promotion_candidates": _bounded(
            (
                _event_brief(event)
                for event in relevant
                if event.get("promotion_status") == "candidate"
            ),
            max_items,
        ),
        "evidence_limits": _evidence_limits(relevant, max_items),
    }
    return {"project_memory_summary": summary}


def _matches_query(event: dict[str, Any], query: dict[str, Any], *, include_empty_query: bool) -> bool:
    if not query and include_empty_query:
        return True
    for key in ("repo_hash", "task_fingerprint", "owner_skill", "reviewer_skill"):
        expected = query.get(key)
        if expected and event.get(key) != expected:
            return False
    paths = set(query.get("paths") or [])
    if paths and not (paths & set(event.get("paths") or [])):
        return False
    symbols = set(query.get("symbols") or [])
    if symbols and not (symbols & set(event.get("symbols") or [])):
        return False
    return True


def _fragile_signal(event: dict[str, Any]) -> bool:
    if event.get("type") in FRAGILE_TYPES:
        return True
    return event.get("type") == "validation_result" and event.get("outcome") in {"failed", "blocked"}


def _event_brief(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id", ""),
        "type": event.get("type", ""),
        "outcome": event.get("outcome", ""),
        "paths": list(event.get("paths") or [])[:10],
        "symbols": list(event.get("symbols") or [])[:10],
        "owner_skill": event.get("owner_skill", ""),
        "reviewer_skill": event.get("reviewer_skill", ""),
        "evidence_refs": _refs(event)[:10],
        "confidence": event.get("confidence", ""),
        "promotion_status": event.get("promotion_status", ""),
        "created_at": event.get("created_at", ""),
    }


def _finding_key(event: dict[str, Any]) -> str:
    refs = _refs(event)
    return refs[0] if refs else event.get("event_id", "review_finding")


def _refs(event: dict[str, Any]) -> list[str]:
    return [str(ref) for ref in event.get("evidence_refs", []) or [] if str(ref).strip()]


def _first_value(events: list[dict[str, Any]], key: str) -> str:
    for event in events:
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def _bounded(items: Iterable[dict[str, Any]], max_items: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        result.append(item)
        if len(result) >= max_items:
            break
    return result


def _evidence_limits(events: list[dict[str, Any]], max_items: int) -> list[str]:
    limits: list[str] = []
    if len(events) > max_items:
        limits.append(f"summary truncated to {max_items} items per section")
    if any(event.get("repo_hash") == "unknown" for event in events):
        limits.append("some events lacked a repo_hash")
    return limits[:50]
