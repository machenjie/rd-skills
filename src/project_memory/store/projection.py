"""Generated projections over append-only project memory events."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from project_memory import MEMORY_SCHEMA_VERSION
from project_memory.privacy import now_utc, sanitize_memory_query
from project_memory.source_evidence import memory_hit_from_event, residual_risk_for_hit
from project_memory.store.append_log import parse_iso_datetime


FAILURE_OUTCOMES = {"failed", "blocked", "partial"}
FRAGILE_TYPES = {"review_finding", "repair_attempt", "fragile_file"}
DECISION_TYPES = {"accepted_decision", "rejected_decision", "route_decision"}
BUSINESS_MEMORY_KINDS = {
    "business_rule_changed",
    "business_rule_rejected",
    "business_object_ownership_changed",
    "business_term_ambiguous",
    "workflow_transition_bug",
    "missing_entry_point_bug",
    "hidden_sql_rule_bug",
    "stale_business_context",
    "golden_case_added",
    "golden_case_failed",
    "owner_decision_superseded",
}


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
    relevant.sort(key=lambda event: _timestamp(event), reverse=True)
    path_counts: Counter[str] = Counter()
    review_counts: Counter[tuple[str, str]] = Counter()
    review_refs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for event in relevant:
        for path in _paths(event):
            if _fragile_signal(event):
                path_counts[path] += 1
            if _type(event) == "review_finding" or _kind(event) == "review_finding_pattern":
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
                if _type(event) in DECISION_TYPES or _kind(event) in {"route_correction", "module_convention"}
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
                if _type(event) == "validated_command"
                or _kind(event) == "validation_pattern"
                or (
                    _type(event) == "validation_result"
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
                if (
                    _type(event) == "context_pack"
                    or _kind(event) == "generated_source_mapping"
                )
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


def build_memory_projection(
    events: Iterable[dict[str, Any]],
    query: dict[str, Any] | None = None,
    *,
    max_events: int = 50,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the Batch 04 deterministic Project Memory projection.

    The projection is a retrieval and gate input only. It always cites included
    event ids and marks source inspection as required because memory summaries
    are never current repository facts.
    """
    sanitized_query = sanitize_memory_query(query or {})
    event_list = [event for event in events if isinstance(event, dict)]
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    residual_risk: list[str] = []
    changed_times = _changed_times(sanitized_query)

    for event in sorted(event_list, key=_event_sort_key):
        event_id = str(event.get("event_id") or "")
        if event.get("privacy_class") == "rejected_sensitive":
            excluded.append(_excluded(event, "rejected_sensitive"))
            residual_risk.append("sensitive_memory_event_excluded")
            continue
        reason = _projection_exclusion_reason(event, sanitized_query)
        if reason:
            excluded.append(_excluded(event, reason))
            continue
        stale = _event_stale_for_changed_paths(event, changed_times)
        hit = memory_hit_from_event(event, repo_root=repo_root)
        included.append(_projection_event(event, stale=stale, hit=hit))
        if stale:
            residual_risk.append(f"stale_memory_event:{event_id}")
        source_risk = residual_risk_for_hit(hit)
        if source_risk:
            residual_risk.append(source_risk)
        if len(included) >= max_events:
            break

    if len(event_list) > len(included) + len(excluded):
        residual_risk.append("projection_truncated")
    graph_freshness = sanitized_query.get("graph_freshness") or "unknown"
    stale_status = _projection_stale_status(graph_freshness, included)
    if stale_status != "pass":
        residual_risk.append(f"stale_context_gate:{stale_status}")
    projection = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "retrieval_key": _retrieval_key(sanitized_query, event_list),
        "included_events": included,
        "excluded_events": excluded[:max_events],
        "summary": _projection_summary(included),
        "source_check_required": True,
        "stale_context_gate": stale_status,
        "residual_risk": _unique(residual_risk)[:max_events],
    }
    return {"project_memory_projection": projection}


def _matches_query(event: dict[str, Any], query: dict[str, Any], *, include_empty_query: bool) -> bool:
    if not query and include_empty_query:
        return True
    for key in ("repo_hash", "task_fingerprint", "owner_skill", "reviewer_skill"):
        expected = query.get(key)
        if expected and event.get(key) != expected:
            return False
    paths = set(query.get("paths") or [])
    if paths and not _paths_overlap(paths, set(_paths(event))):
        return False
    symbols = set(query.get("symbols") or [])
    if symbols and not (symbols & set(event.get("symbols") or [])):
        return False
    return True


def _fragile_signal(event: dict[str, Any]) -> bool:
    if _type(event) in FRAGILE_TYPES or _kind(event) in {"fragile_file", "review_finding_pattern"}:
        return True
    return _type(event) == "validation_result" and event.get("outcome") in {"failed", "blocked"}


def _event_brief(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id", ""),
        "kind": _kind(event),
        "type": _type(event),
        "outcome": event.get("outcome", ""),
        "bounded_paths": _paths(event)[:10],
        "paths": _paths(event)[:10],
        "symbols": list(event.get("symbols") or [])[:10],
        "owner_skill": event.get("owner_skill", ""),
        "reviewer_skill": event.get("reviewer_skill", ""),
        "evidence_refs": _refs(event)[:10],
        "confidence": event.get("confidence", ""),
        "promotion_status": event.get("promotion_status", ""),
        "timestamp": _timestamp(event),
        "created_at": _timestamp(event),
        "source_check_required": True,
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


def _kind(event: dict[str, Any]) -> str:
    kind = str(event.get("kind") or "").strip()
    if kind:
        return kind
    mapping = {
        "fragile_file": "fragile_file",
        "repeat_failure": "repeat_failure",
        "validation_result": "validation_pattern",
        "validated_command": "validation_pattern",
        "review_finding": "review_finding_pattern",
        "repair_attempt": "review_finding_pattern",
        "context_pack": "generated_source_mapping",
            "route_decision": "route_correction",
            "hook_false_positive": "false_positive_hook",
            "hook_false_negative": "false_negative_hook",
            "business_rule_changed": "business_rule_changed",
            "business_rule_rejected": "business_rule_rejected",
            "business_object_ownership_changed": "business_object_ownership_changed",
            "business_term_ambiguous": "business_term_ambiguous",
            "workflow_transition_bug": "workflow_transition_bug",
            "missing_entry_point_bug": "missing_entry_point_bug",
            "hidden_sql_rule_bug": "hidden_sql_rule_bug",
            "stale_business_context": "stale_business_context",
            "golden_case_added": "golden_case_added",
            "golden_case_failed": "golden_case_failed",
            "owner_decision_superseded": "owner_decision_superseded",
        }
    return mapping.get(_type(event), "module_convention")


def _type(event: dict[str, Any]) -> str:
    return str(event.get("type") or "").strip()


def _paths(event: dict[str, Any]) -> list[str]:
    values = event.get("bounded_paths")
    if not isinstance(values, list):
        values = event.get("paths")
    if not isinstance(values, list):
        return []
    return [str(path) for path in values if str(path).strip()][:50]


def _timestamp(event: dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("created_at") or "").strip()


def _event_sort_key(event: dict[str, Any]) -> tuple[str, str]:
    return (_timestamp(event), str(event.get("event_id") or ""))


def _projection_exclusion_reason(event: dict[str, Any], query: dict[str, Any]) -> str:
    repo_hash = str(query.get("repo_hash") or "").strip()
    if repo_hash and event.get("repo_hash") and event.get("repo_hash") != repo_hash:
        return "repo_hash_mismatch"
    paths = set(query.get("paths") or [])
    capabilities = set(query.get("capabilities") or [])
    task = str(query.get("task") or query.get("task_fingerprint") or "").casefold()
    if paths and _paths_overlap(paths, set(_paths(event))):
        return ""
    if capabilities and capabilities & {
        str(event.get("owner_skill") or ""),
        str(event.get("reviewer_skill") or ""),
    }:
        return ""
    if task and task in _event_text(event).casefold():
        return ""
    if not paths and not capabilities and not task:
        return ""
    return "not_relevant_to_query"


def _event_text(event: dict[str, Any]) -> str:
    return " ".join(
        [
            str(event.get("summary") or ""),
            " ".join(_refs(event)),
            str(event.get("task_fingerprint") or ""),
            str(event.get("owner_skill") or ""),
            str(event.get("reviewer_skill") or ""),
        ]
    )


def _paths_overlap(query_paths: set[str], event_paths: set[str]) -> bool:
    if query_paths & event_paths:
        return True
    for left in query_paths:
        for right in event_paths:
            if left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                return True
    return False


def _projection_event(event: dict[str, Any], *, stale: bool, hit: dict[str, str]) -> dict[str, Any]:
    return {
        "event_id": str(event.get("event_id") or ""),
        "kind": _kind(event),
        "bounded_paths": _paths(event),
        "summary": str(event.get("summary") or "")[:240],
        "evidence_refs": _refs(event)[:10],
        "confidence": str(event.get("confidence") or ""),
        "timestamp": _timestamp(event),
        "source": str(event.get("source") or ""),
        "promotion_status": str(event.get("promotion_status") or ""),
        "source_check_required": True,
        "stale_relative_to_source": stale,
        "memory_hit": hit,
        "source_status": hit["source_status"],
        "evidence_role": hit["evidence_role"],
        "retrieval_confidence": hit["confidence"],
        "source_status_reason": hit["reason"],
    }


def _excluded(event: dict[str, Any], reason: str) -> dict[str, str]:
    return {
        "event_id": str(event.get("event_id") or ""),
        "kind": _kind(event),
        "reason": reason,
    }


def _projection_summary(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "fragile_files": [
            _summary_item(event)
            for event in events
            if event.get("kind") == "fragile_file"
        ],
        "repeat_failures": [
            _summary_item(event)
            for event in events
            if event.get("kind") == "repeat_failure"
        ],
        "validation_hints": [
            _summary_item(event)
            for event in events
            if event.get("kind") == "validation_pattern"
        ],
        "review_patterns": [
            _summary_item(event)
            for event in events
            if event.get("kind") == "review_finding_pattern"
        ],
        "business_memory": {
            "accepted": [
                _summary_item(event)
                for event in events
                if _business_memory_verdict(event) == "accepted"
            ],
            "rejected": [
                _summary_item(event)
                for event in events
                if _business_memory_verdict(event) == "rejected"
            ],
            "stale": [
                _summary_item(event)
                for event in events
                if _business_memory_verdict(event) == "stale"
            ],
            "not_verified": [
                _summary_item(event)
                for event in events
                if _business_memory_verdict(event) == "not_verified"
            ],
        },
    }


def _summary_item(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id", ""),
        "bounded_paths": event.get("bounded_paths", []),
        "summary": event.get("summary", ""),
        "source_check_required": True,
        "source_status": event.get("source_status", ""),
        "evidence_role": event.get("evidence_role", ""),
    }


def _business_memory_verdict(event: dict[str, Any]) -> str:
    kind = str(event.get("kind") or "")
    if kind not in BUSINESS_MEMORY_KINDS:
        return ""
    if event.get("source_status") == "stale" or kind == "stale_business_context":
        return "stale"
    if kind in {"business_rule_rejected", "golden_case_failed", "owner_decision_superseded"}:
        return "rejected"
    if event.get("source_status") == "current" and event.get("promotion_status") in {"approved", "candidate"}:
        return "accepted"
    return "not_verified"


def _changed_times(query: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in query.get("changed_files") or []:
        if not isinstance(item, dict):
            continue
        parsed = parse_iso_datetime(item.get("changed_at"))
        path = str(item.get("path") or "")
        if path and parsed is not None:
            result[path] = parsed
    return result


def _event_stale_for_changed_paths(event: dict[str, Any], changed_times: dict[str, Any]) -> bool:
    event_time = parse_iso_datetime(_timestamp(event))
    if event_time is None or not changed_times:
        return False
    for path in _paths(event):
        for changed_path, changed_at in changed_times.items():
            if _paths_overlap({path}, {changed_path}) and event_time < changed_at:
                return True
    return False


def _projection_stale_status(graph_freshness: str, included: list[dict[str, Any]]) -> str:
    if graph_freshness == "stale":
        return "warn"
    if any(event.get("stale_relative_to_source") for event in included):
        return "warn"
    if graph_freshness == "unknown":
        return "warn"
    return "pass"


def _retrieval_key(query: dict[str, Any], events: list[dict[str, Any]]) -> str:
    payload = {
        "query": query,
        "event_ids": sorted(str(event.get("event_id") or "") for event in events),
        "determinism_version": 1,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
