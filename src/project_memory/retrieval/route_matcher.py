"""Skill and task matching helpers for deterministic memory retrieval."""

from __future__ import annotations


def route_match_score(query: dict, event: dict) -> int:
    score = 0
    if query.get("task_fingerprint") and query.get("task_fingerprint") == event.get("task_fingerprint"):
        score += 35
    if query.get("owner_skill") and query.get("owner_skill") == event.get("owner_skill"):
        score += 20
    if query.get("reviewer_skill") and query.get("reviewer_skill") == event.get("reviewer_skill"):
        score += 12
    return score

