"""Repeat Failure Gate for Project Memory Governance."""

from __future__ import annotations

from typing import Any, Iterable

from project_memory.privacy import clean_path


FAILURE_OUTCOMES = {"failed", "blocked"}


def evaluate_repeat_failure_gate(
    events: Iterable[dict[str, Any]],
    *,
    repo_hash: str,
    task_fingerprint: str,
    primary_path: str,
    owner_skill: str,
    mode: str = "warn",
    has_new_evidence: bool = False,
    has_route_repair_manifest: bool = False,
) -> dict[str, Any]:
    """Evaluate whether a third same-path same-strategy attempt should pause."""
    path = clean_path(primary_path)
    event_list = list(events)
    exact = _matching_events(
        event_list,
        repo_hash=repo_hash,
        task_fingerprint=task_fingerprint,
        path=path,
        owner_skill=owner_skill,
    )
    matched = exact if len(exact) >= 2 else _matching_events(
        event_list,
        repo_hash=repo_hash,
        task_fingerprint="",
        path=path,
        owner_skill=owner_skill,
    )
    matched.sort(key=_timestamp, reverse=True)
    failure_count = 0
    matched_paths: list[str] = []
    for event in matched:
        if event.get("outcome") in FAILURE_OUTCOMES:
            failure_count += 1
            for item in _paths(event):
                if item not in matched_paths:
                    matched_paths.append(item)
            continue
        if event.get("outcome") == "success":
            break
    repeated = failure_count >= 2
    required_next_gate = _required_next_gate(matched[:failure_count])
    allowed = True
    if repeated and mode == "block" and not (has_new_evidence or has_route_repair_manifest):
        allowed = False
    return {
        "repeat_failure_gate": {
            "repeated": repeated,
            "failure_count": min(failure_count, 2) if repeated else failure_count,
            "matched_paths": matched_paths[:50],
            "required_next_gate": required_next_gate,
            "allowed_to_continue": allowed,
        }
    }


def _matching_events(
    events: Iterable[dict[str, Any]],
    *,
    repo_hash: str,
    task_fingerprint: str,
    path: str,
    owner_skill: str,
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for event in events:
        if event.get("repo_hash") != repo_hash:
            continue
        if task_fingerprint and event.get("task_fingerprint") != task_fingerprint:
            continue
        if event.get("owner_skill") != owner_skill:
            continue
        if path not in _paths(event):
            continue
        matched.append(event)
    return matched


def _required_next_gate(events: list[dict[str, Any]]) -> str:
    if any(_type(event) == "validation_result" or _kind(event) == "validation_pattern" for event in events):
        return "quality-test-gate"
    if any("architecture" in str(event.get("owner_skill", "")) for event in events):
        return "architecture-impact-reviewer"
    return "failure-diagnosis"


def _paths(event: dict[str, Any]) -> list[str]:
    values = event.get("bounded_paths")
    if not isinstance(values, list):
        values = event.get("paths")
    if not isinstance(values, list):
        return []
    return [str(path) for path in values if str(path).strip()][:50]


def _timestamp(event: dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("created_at") or "").strip()


def _type(event: dict[str, Any]) -> str:
    return str(event.get("type") or "").strip()


def _kind(event: dict[str, Any]) -> str:
    return str(event.get("kind") or "").strip()
