"""Deterministic retrieval ranking for Project Memory Governance."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from project_memory.privacy import sanitize_memory_query
from project_memory.retrieval.freshness_ranker import recency_score
from project_memory.retrieval.path_matcher import path_match_score
from project_memory.retrieval.route_matcher import route_match_score
from project_memory.retrieval.symbol_matcher import symbol_match_score
from project_memory.source_evidence import memory_hit_from_event


OUTCOME_SEVERITY = {"blocked": 14, "failed": 12, "partial": 6, "unknown": 1, "success": 0}
PROMOTION_WEIGHT = {"approved": 8, "candidate": 5, "raw": 0, "rejected": -5}


def rank_memory_events(
    events: Iterable[dict[str, Any]],
    query: dict[str, Any],
    *,
    now: datetime | None = None,
    limit: int | None = None,
    repo_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Rank events with explainable, deterministic factors only."""
    clean_query = sanitize_memory_query(query)
    max_items = limit or int(clean_query.get("limit") or 20)
    ranked: list[dict[str, Any]] = []
    for event in events:
        score = _score_event(event, clean_query, now=now)
        if score <= 0:
            continue
        hit = memory_hit_from_event(event, repo_root=repo_root)
        row = dict(event)
        row["retrieval_score"] = score
        row["memory_hit"] = hit
        row["source_status"] = hit["source_status"]
        row["evidence_role"] = hit["evidence_role"]
        row["retrieval_confidence"] = hit["confidence"]
        ranked.append(row)
    ranked.sort(
        key=lambda event: (
            -int(event.get("retrieval_score", 0)),
            str(event.get("created_at", "")),
            str(event.get("event_id", "")),
        )
    )
    return ranked[:max_items]


def _score_event(event: dict[str, Any], query: dict[str, Any], *, now: datetime | None) -> int:
    score = 0
    score += path_match_score(query.get("paths") or [], event.get("paths") or [])
    score += symbol_match_score(query.get("symbols") or [], event.get("symbols") or [])
    score += route_match_score(query, event)
    score += OUTCOME_SEVERITY.get(event.get("outcome"), 0)
    score += PROMOTION_WEIGHT.get(event.get("promotion_status"), 0)
    score += recency_score(event.get("created_at"), now=now)
    if query.get("repo_hash") and query.get("repo_hash") != event.get("repo_hash"):
        return 0
    return score
