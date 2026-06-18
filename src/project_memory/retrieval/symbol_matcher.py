"""Symbol matching helpers for deterministic memory retrieval."""

from __future__ import annotations


def symbol_match_score(query_symbols: list[str], event_symbols: list[str]) -> int:
    if not query_symbols or not event_symbols:
        return 0
    return 40 if set(query_symbols) & set(event_symbols) else 0

