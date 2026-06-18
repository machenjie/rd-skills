"""Issue classification helpers for deterministic trajectory analysis."""

from __future__ import annotations

from typing import Any


ISSUE_SEVERITIES = {
    "edit_before_read": "high",
    "plan_before_repo_context": "medium",
    "missing_implementation_preflight": "medium",
    "missing_validation": "high",
    "stale_validation": "high",
    "validation_without_outcome": "high",
    "self_review": "medium",
    "repair_without_rereview": "high",
    "stop_without_residual_risk": "medium",
    "route_manifest_incomplete": "high",
    "repeat_failure_without_route_repair": "high",
    "fragile_file_without_preflight": "high",
}

ISSUE_GATES = {
    "edit_before_read": "repository-context-map",
    "plan_before_repo_context": "repository-context-map",
    "missing_implementation_preflight": "implementation-structure-design",
    "missing_validation": "quality-test-gate",
    "stale_validation": "quality-test-gate",
    "validation_without_outcome": "quality-test-gate",
    "self_review": "code-review",
    "repair_without_rereview": "code-review",
    "stop_without_residual_risk": "agent-execution-discipline",
    "route_manifest_incomplete": "change-forge-router",
    "repeat_failure_without_route_repair": "failure-diagnosis",
    "fragile_file_without_preflight": "implementation-structure-design",
}


def classify_issue(
    issue_type: str,
    step_index: int,
    message: str,
    *,
    severity: str | None = None,
    recommended_gate: str | None = None,
) -> dict[str, Any]:
    """Build one trajectory issue using the canonical severity/gate mapping."""
    return {
        "type": issue_type,
        "severity": severity or ISSUE_SEVERITIES.get(issue_type, "medium"),
        "step_index": step_index,
        "message": message,
        "recommended_gate": recommended_gate or ISSUE_GATES.get(issue_type, "agent-execution-discipline"),
    }


def highest_severity(issues: list[dict[str, Any]]) -> str:
    """Return the highest issue severity in stable order."""
    order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    result = "none"
    for issue in issues:
        severity = str(issue.get("severity", "medium"))
        if order.get(severity, 0) > order[result]:
            result = severity
    return result
