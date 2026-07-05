"""Retention helpers for cache-side memory events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from project_memory.store.append_log import parse_iso_datetime


def retain_recent_events(
    events: Iterable[dict[str, Any]],
    *,
    max_age_days: int = 90,
    max_events: int = 5000,
) -> list[dict[str, Any]]:
    """Return a deterministic retained event slice without mutating storage."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    retained: list[dict[str, Any]] = []
    for event in sorted(events, key=lambda item: str(item.get("created_at", "")), reverse=True):
        created = parse_iso_datetime(event.get("created_at"))
        if created is not None and created < cutoff:
            continue
        retained.append(event)
        if len(retained) >= max_events:
            break
    return list(reversed(retained))

