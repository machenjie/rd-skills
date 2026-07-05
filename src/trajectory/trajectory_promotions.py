"""Human-review-only promotion skeletons for trajectory issues."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any


ALLOWED_TARGETS = (
    "evals/pressure",
    "evals/agent-behavior/samples",
    "tests/fixtures/hooks",
    "tests/fixtures/validation_broker",
    "tests/fixtures/trajectory",
)


def promotion_skeletons(trajectory: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return candidate skeletons for the first high-severity issue."""
    high_issue = next((issue for issue in report.get("issues", []) if issue.get("severity") == "high"), None)
    if not high_issue:
        return []
    session_id = str(trajectory.get("session_id") or "unknown-session")
    issue_type = str(high_issue.get("type") or "trajectory_issue")
    slug = _slug(f"{session_id}-{issue_type}")
    source_suggestion_id = f"trajectory-{session_id}-{issue_type}-{high_issue.get('step_index', 0)}"
    return [
        {
            "target": "evals/pressure",
            "path": f"evals/pressure/candidates/{slug}.yaml",
            "requires_human_review": True,
            "content": _pressure_content(trajectory, high_issue, source_suggestion_id),
        },
        {
            "target": "evals/agent-behavior/samples",
            "path": f"evals/agent-behavior/samples/candidates/{slug}.yaml",
            "requires_human_review": True,
            "content": _behavior_content(trajectory, high_issue, source_suggestion_id),
        },
        {
            "target": "tests/fixtures/hooks",
            "path": f"tests/fixtures/hooks/trajectory-{slug}.json",
            "requires_human_review": True,
            "content": _hook_fixture_content(trajectory, high_issue, source_suggestion_id),
        },
        {
            "target": "tests/fixtures/validation_broker",
            "path": f"tests/fixtures/validation_broker/trajectory-{slug}.json",
            "requires_human_review": True,
            "content": _validation_broker_fixture_content(trajectory, high_issue, source_suggestion_id),
        },
        {
            "target": "tests/fixtures/trajectory",
            "path": f"tests/fixtures/trajectory/{slug}.json",
            "requires_human_review": True,
            "content": _trajectory_fixture_content(trajectory, high_issue, source_suggestion_id),
        },
    ]


def write_skeletons(root: Path, skeletons: list[dict[str, Any]], *, write: bool = False) -> list[Path]:
    """Write skeleton files only when explicitly requested."""
    paths: list[Path] = []
    for skeleton in skeletons:
        target = str(skeleton.get("path") or "")
        if not _allowed_path(target):
            raise ValueError(f"unsupported trajectory promotion target: {target}")
        path = root / target
        paths.append(path)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(skeleton.get("content") or ""), encoding="utf-8")
    return paths


def _pressure_content(trajectory: dict[str, Any], issue: dict[str, Any], source_suggestion_id: str) -> str:
    return "\n".join(
        [
            "schema_version: 1",
            "generated_from_telemetry: true",
            "requires_human_review: true",
            f"source_suggestion_id: {source_suggestion_id}",
            "status: skeleton",
            f"source_session_id: {trajectory.get('session_id', '')}",
            f"issue_type: {issue.get('type', '')}",
            "scenario:",
            "  title: TODO trajectory pressure scenario",
            "  setup: TODO summarize bounded facts only",
            "  pressure: TODO describe the rationalization pressure",
            "  expected_behavior: TODO cite required gate behavior",
            "evidence:",
            "  trajectory_step_index: " + str(issue.get("step_index", "")),
            "  source: trajectory-inspector",
            "",
        ]
    )


def _behavior_content(trajectory: dict[str, Any], issue: dict[str, Any], source_suggestion_id: str) -> str:
    return "\n".join(
        [
            "schema_version: 1",
            "generated_from_telemetry: true",
            "requires_human_review: true",
            f"source_suggestion_id: {source_suggestion_id}",
            "status: skeleton",
            f"source_session_id: {trajectory.get('session_id', '')}",
            "expected:",
            "  route_manifest: TODO",
            "  runtime_prompt_flow: TODO",
            "  validation_evidence: TODO",
            "  residual_risk: TODO",
            "observed_issue:",
            f"  type: {issue.get('type', '')}",
            f"  recommended_gate: {issue.get('recommended_gate', '')}",
            "",
        ]
    )


def _hook_fixture_content(trajectory: dict[str, Any], issue: dict[str, Any], source_suggestion_id: str) -> str:
    payload = {
        "schema_version": 1,
        "generated_from_telemetry": True,
        "requires_human_review": True,
        "source_suggestion_id": source_suggestion_id,
        "status": "skeleton",
        "source": "trajectory-inspector",
        "source_session_id": trajectory.get("session_id", ""),
        "issue_type": issue.get("type", ""),
        "step_index": issue.get("step_index", 0),
        "event": {
            "event_name": "TODO",
            "hook_name": "TODO",
            "runtime": "generic",
            "bounded_facts_only": True,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _validation_broker_fixture_content(
    trajectory: dict[str, Any],
    issue: dict[str, Any],
    source_suggestion_id: str,
) -> str:
    payload = {
        "schema_version": 1,
        "generated_from_telemetry": True,
        "requires_human_review": True,
        "source_suggestion_id": source_suggestion_id,
        "status": "skeleton",
        "source": "trajectory-inspector",
        "source_session_id": trajectory.get("session_id", ""),
        "issue_type": issue.get("type", ""),
        "validation_broker_fixture": {
            "changed_path_mapping": {},
            "command_ledger": [],
            "closure_outcome": "TODO",
            "negative_evidence": ["TODO"],
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _trajectory_fixture_content(
    trajectory: dict[str, Any],
    issue: dict[str, Any],
    source_suggestion_id: str,
) -> str:
    payload = {
        "schema_version": 1,
        "generated_from_telemetry": True,
        "requires_human_review": True,
        "source_suggestion_id": source_suggestion_id,
        "status": "skeleton",
        "source": "trajectory-inspector",
        "source_session_id": trajectory.get("session_id", ""),
        "issue_type": issue.get("type", ""),
        "trajectory_fixture": {
            "ordered_events": [],
            "expected_verdict": "TODO",
            "expected_findings": [issue.get("type", "")],
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _allowed_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    return any(path == target or path.startswith(f"{target}/") for target in ALLOWED_TARGETS)


def _slug(value: str) -> str:
    chars = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:80] or "trajectory-issue"
