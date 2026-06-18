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
    matched = [
        event
        for event in events
        if event.get("repo_hash") == repo_hash
        and event.get("task_fingerprint") == task_fingerprint
        and event.get("owner_skill") == owner_skill
        and path in (event.get("paths") or [])
    ]
    matched.sort(key=lambda event: str(event.get("created_at", "")), reverse=True)
    failure_count = 0
    matched_paths: list[str] = []
    for event in matched:
        if event.get("outcome") in FAILURE_OUTCOMES:
            failure_count += 1
            for item in event.get("paths") or []:
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


def _required_next_gate(events: list[dict[str, Any]]) -> str:
    if any(event.get("type") == "validation_result" for event in events):
        return "quality-test-gate"
    if any("architecture" in str(event.get("owner_skill", "")) for event in events):
        return "architecture-impact-reviewer"
    return "failure-diagnosis"

