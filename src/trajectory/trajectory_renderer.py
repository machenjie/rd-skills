"""Render trajectory inspection reports."""

from __future__ import annotations

import json
from typing import Any

from .trajectory_analyzer import attach_issues


def render_json(trajectory: dict[str, Any], report: dict[str, Any]) -> str:
    """Render machine-readable trajectory inspection output."""
    payload = {
        "trajectory": attach_issues(trajectory, report),
        "trajectory_report": report,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_markdown(trajectory: dict[str, Any], report: dict[str, Any]) -> str:
    """Render a concise markdown trajectory report."""
    steps = trajectory.get("steps", []) if isinstance(trajectory.get("steps"), list) else []
    issues = report.get("issues", []) if isinstance(report.get("issues"), list) else []
    lines: list[str] = [
        f"# Trajectory Inspection: {trajectory.get('session_id', '') or 'unknown-session'}",
        "",
        f"- Closure status: {report.get('closure_status', 'unknown')}",
        f"- Highest severity: {report.get('highest_severity', 'none')}",
        f"- Validation freshness: {report.get('validation_freshness', 'unknown')}",
        f"- Review integrity: {report.get('review_integrity', 'unknown')}",
        "",
        "## Stage Timeline",
    ]
    if not steps:
        lines.append("- No steps.")
    for step in steps:
        path_text = ", ".join(step.get("paths", [])[:4]) if isinstance(step.get("paths"), list) else ""
        suffix = f" paths={path_text}" if path_text else ""
        lines.append(
            f"- {step.get('index')}. {step.get('stage')} "
            f"`{step.get('event_type', '') or 'event'}` "
            f"tool=`{step.get('tool_name', '') or '-'}` "
            f"cmd=`{step.get('command_program', '') or '-'}` "
            f"outcome={step.get('outcome', 'unknown')}{suffix}"
        )

    read_paths, changed_paths = _path_summary(steps)
    lines.extend(
        [
            "",
            "## Changed/Read Paths",
            f"- Read paths: {_format_list(read_paths)}",
            f"- Changed paths: {_format_list(changed_paths)}",
            "",
            "## Validation Freshness",
            f"- Status: {report.get('validation_freshness', 'unknown')}",
            f"- Skipped stages: {_format_list(report.get('skipped_stages', []))}",
            "",
            "## Review/Repair",
            f"- Review integrity: {report.get('review_integrity', 'unknown')}",
            f"- Repair evidence seen: {'yes' if _repair_seen(steps) else 'no'}",
            "",
            "## Issues",
        ]
    )
    if not issues:
        lines.append("- None.")
    else:
        for issue in issues:
            lines.append(
                f"- [{issue.get('severity')}] {issue.get('type')} "
                f"at step {issue.get('step_index')}: {issue.get('message')} "
                f"Gate: `{issue.get('recommended_gate')}`."
            )

    next_gates = _next_gates(issues)
    lines.extend(
        [
            "",
            "## Suggested Next Gates",
            f"- {_format_list(next_gates) if next_gates else 'No additional gates suggested.'}",
        ]
    )
    skeletons = report.get("promotion_skeletons", []) if isinstance(report.get("promotion_skeletons"), list) else []
    if skeletons:
        lines.extend(["", "## Promotion Skeletons"])
        for skeleton in skeletons:
            lines.append(
                f"- {skeleton.get('target')}: `{skeleton.get('path')}` "
                f"human_review={skeleton.get('requires_human_review')}"
            )
    return "\n".join(lines) + "\n"


def _path_summary(steps: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    read_paths: list[str] = []
    changed_paths: list[str] = []
    for step in steps:
        facts = step.get("facts", {}) if isinstance(step.get("facts"), dict) else {}
        for path in facts.get("read_paths", []) or []:
            if path not in read_paths:
                read_paths.append(path)
        for field in ("changed_paths", "added_paths"):
            for path in facts.get(field, []) or []:
                if path not in changed_paths:
                    changed_paths.append(path)
    return read_paths, changed_paths


def _repair_seen(steps: list[dict[str, Any]]) -> bool:
    for step in steps:
        evidence = step.get("evidence", {}) if isinstance(step.get("evidence"), dict) else {}
        if step.get("stage") == "repair" or evidence.get("repair_seen"):
            return True
    return False


def _next_gates(issues: list[dict[str, Any]]) -> list[str]:
    gates: list[str] = []
    for issue in issues:
        gate = str(issue.get("recommended_gate") or "")
        if gate and gate not in gates:
            gates.append(gate)
    return gates


def _format_list(values: Any) -> str:
    if not values:
        return "none"
    if not isinstance(values, list):
        return str(values)
    return ", ".join(str(value) for value in values[:12]) or "none"
