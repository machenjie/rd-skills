"""Freshness scoring for deterministic memory retrieval."""

from __future__ import annotations

from datetime import datetime, timezone

from project_memory.store.append_log import parse_iso_datetime


def recency_score(created_at: object, *, now: datetime | None = None) -> int:
    """Return a small deterministic recency score from 0 to 10."""
    created = parse_iso_datetime(created_at)
    if created is None:
        return 0
    current = now or datetime.now(timezone.utc)
    days = max(0.0, (current - created).total_seconds() / 86400)
    if days <= 1:
        return 10
    if days <= 7:
        return 7
    if days <= 30:
        return 4
    if days <= 90:
        return 2
    return 0

