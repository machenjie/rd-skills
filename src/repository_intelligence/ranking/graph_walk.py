"""Small graph-walk helpers for repository context selection."""

from __future__ import annotations

from collections import deque


def build_adjacency(edges: list[dict[str, str]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    outgoing: dict[str, set[str]] = {}
    incoming: dict[str, set[str]] = {}
    for edge in edges:
        source = edge.get("from")
        target = edge.get("to")
        if not source or not target:
            continue
        outgoing.setdefault(source, set()).add(target)
        incoming.setdefault(target, set()).add(source)
    return outgoing, incoming


def walk_related_paths(
    seeds: list[str],
    edges: list[dict[str, str]],
    max_depth: int = 2,
) -> dict[str, int]:
    """Return paths reachable from seeds with the shortest graph distance."""
    outgoing, incoming = build_adjacency(edges)
    distances: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque((seed, 0) for seed in seeds)
    while queue:
        path, depth = queue.popleft()
        if path in distances and distances[path] <= depth:
            continue
        distances[path] = depth
        if depth >= max_depth:
            continue
        for neighbor in sorted(outgoing.get(path, set()) | incoming.get(path, set())):
            if neighbor not in distances or distances[neighbor] > depth + 1:
                queue.append((neighbor, depth + 1))
    return distances
