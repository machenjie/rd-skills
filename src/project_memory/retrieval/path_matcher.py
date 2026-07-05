"""Path matching helpers for deterministic memory retrieval."""

from __future__ import annotations


def path_match_score(query_paths: list[str], event_paths: list[str]) -> int:
    """Score exact and ancestor path overlap without fuzzy search."""
    if not query_paths or not event_paths:
        return 0
    query = set(query_paths)
    event = set(event_paths)
    if query & event:
        return 50
    for left in query:
        for right in event:
            if left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                return 20
    return 0

