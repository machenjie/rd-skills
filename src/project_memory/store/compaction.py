"""Compaction helpers for generated memory projections."""

from __future__ import annotations

from typing import Any, Iterable

from project_memory.store.projection import build_memory_summary


def compact_events_to_summary(
    events: Iterable[dict[str, Any]],
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compact raw events into the same bounded summary projection used by review."""
    return build_memory_summary(events, query)

