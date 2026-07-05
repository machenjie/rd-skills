"""Relevance scoring for graph-backed context packs."""

from __future__ import annotations

import re
from pathlib import Path


ROLE_WEIGHT = {
    "registry": 8,
    "validator": 7,
    "test": 6,
    "capability": 5,
    "skill": 5,
    "hook_runtime": 5,
    "docs": 3,
    "eval": 3,
    "script": 2,
    "unknown": 0,
}


def tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9_/-]+", text.lower()) if len(token) >= 3}


def score_file(
    file_node: dict[str, object],
    task_terms: set[str],
    changed_paths: set[str],
    graph_distance: int | None,
) -> int:
    """Score one file node for task-local context selection."""
    path = str(file_node.get("path") or "")
    score = 0
    if path in changed_paths:
        score += 100
    if graph_distance is not None:
        score += max(0, 40 - (graph_distance * 12))
    score += ROLE_WEIGHT.get(str(file_node.get("role") or "unknown"), 0)

    haystack = path.lower()
    for symbol in file_node.get("symbols", []):
        if isinstance(symbol, dict):
            haystack += " " + str(symbol.get("name") or "").lower()
    for ref in file_node.get("references", []):
        if isinstance(ref, dict):
            haystack += " " + str(ref.get("value") or "").lower()

    path_terms = tokenize(haystack)
    score += 7 * len(task_terms & path_terms)
    if Path(path).stem.lower() in task_terms:
        score += 10
    return score


def rank_files(
    files: list[dict[str, object]],
    task_goal: str,
    changed_paths: list[str],
    distances: dict[str, int],
) -> list[tuple[str, int]]:
    """Return repository paths ordered by decreasing relevance score."""
    task_terms = tokenize(task_goal)
    changed_set = set(changed_paths)
    scored: list[tuple[str, int]] = []
    for file_node in files:
        path = str(file_node.get("path") or "")
        score = score_file(file_node, task_terms, changed_set, distances.get(path))
        if score > 0:
            scored.append((path, score))
    return sorted(scored, key=lambda item: (-item[1], item[0]))
