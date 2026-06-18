#!/usr/bin/env python3
"""Validate ChangeForge trajectory inspector schemas and deterministic policy."""

from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TRAJECTORY = SRC / "trajectory"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory, render_json, render_markdown
from trajectory.trajectory_analyzer import attach_issues
from trajectory.trajectory_promotions import promotion_skeletons


def main() -> int:
    errors: list[str] = []
    _validate_files(errors)
    _validate_schemas(errors)
    _validate_policy(errors)
    if errors:
        for error in errors:
            print(f"validate-trajectory: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-trajectory: validated trajectory schemas, analyzer, renderer, and promotions.")
    return 0


def _validate_files(errors: list[str]) -> None:
    if not TRAJECTORY.is_dir():
        errors.append("missing src/trajectory package")
        return
    for path in sorted(TRAJECTORY.rglob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path.relative_to(ROOT)} does not compile: {exc.msg}")


def _validate_schemas(errors: list[str]) -> None:
    for name in ("trajectory.v1.schema.json", "trajectory-report.v1.schema.json"):
        path = TRAJECTORY / "schemas" / name
        if not path.is_file():
            errors.append(f"missing schema: {path.relative_to(ROOT)}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
            continue
        if data.get("additionalProperties") is not False:
            errors.append(f"{path.relative_to(ROOT)} must set additionalProperties=false")
        serialized = json.dumps(data)
        for forbidden in ('"stdout"', '"stderr"', '"prompt"', '"env"', '"secret"'):
            if forbidden in serialized:
                errors.append(f"{path.relative_to(ROOT)} exposes forbidden field {forbidden}")


def _validate_policy(errors: list[str]) -> None:
    trajectory = build_trajectory(_complete_records(), repo_hash="repo", session_id="sess")
    if trajectory is None:
        errors.append("complete sample did not build a trajectory")
        return
    report = analyze_trajectory(trajectory)
    if report["closure_status"] != "pass":
        errors.append(f"complete sample should pass, got {report['closure_status']} with {report['issues']}")
    if report.get("verdict") != "ready":
        errors.append(f"complete sample should be ready, got {report.get('verdict')}")
    if "Stage Timeline" not in render_markdown(trajectory, report):
        errors.append("markdown renderer omitted stage timeline")
    payload = json.loads(render_json(trajectory, report))
    if "trajectory_report" not in payload:
        errors.append("json renderer omitted trajectory_report")
    if attach_issues(trajectory, report).get("issues") != report.get("issues"):
        errors.append("attach_issues did not preserve report issues")

    stale = build_trajectory(_stale_records(), repo_hash="repo", session_id="sess-stale")
    if stale is None:
        errors.append("stale sample did not build a trajectory")
        return
    stale_report = analyze_trajectory(stale)
    if "stale_validation" not in stale_report["issue_counts"]:
        errors.append("stale validation sample was not detected")
    if stale_report.get("verdict") != "needs_validation":
        errors.append(f"stale validation should need validation, got {stale_report.get('verdict')}")
    if not promotion_skeletons(stale, stale_report):
        errors.append("high severity issue should generate promotion skeletons")
    for skeleton in promotion_skeletons(stale, stale_report):
        content = str(skeleton.get("content") or "")
        if "generated_from_telemetry" not in content or "requires_human_review" not in content:
            errors.append("promotion skeleton missing human-review-only candidate headers")

    route_gap = build_trajectory(_route_gap_records(), repo_hash="repo", session_id="sess-route-gap")
    if route_gap is None:
        errors.append("route-gap sample did not build a trajectory")
    else:
        route_gap_report = analyze_trajectory(route_gap)
        if route_gap_report.get("verdict") == "ready":
            errors.append("incomplete route manifest must not be ready")

    repair = build_trajectory(_repair_without_rereview_records(), repo_hash="repo", session_id="sess-repair")
    if repair is None:
        errors.append("repair sample did not build a trajectory")
    else:
        repair_report = analyze_trajectory(repair)
        if repair_report.get("verdict") != "needs_repair":
            errors.append(f"repair without re-review should need repair, got {repair_report.get('verdict')}")

    residual = build_trajectory(_missing_residual_risk_records(), repo_hash="repo", session_id="sess-risk")
    if residual is None:
        errors.append("missing residual risk sample did not build a trajectory")
    else:
        residual_report = analyze_trajectory(residual)
        if residual_report.get("verdict") == "ready":
            errors.append("stop without residual risk must not be ready")

    adapter = build_trajectory(_unsupported_adapter_records(), repo_hash="repo", session_id="sess-adapter")
    if adapter is None:
        errors.append("unsupported adapter sample did not build a trajectory")
    else:
        adapter_report = analyze_trajectory(adapter)
        if adapter_report.get("verdict") != "degraded_ready":
            errors.append(f"unsupported adapter should be degraded_ready, got {adapter_report.get('verdict')}")


def _complete_records() -> list[dict[str, object]]:
    return [
        {
            "timestamp_utc": "2026-06-01T00:00:00Z",
            "session_id": "sess",
            "event_name": "UserPromptSubmit",
            "runtime": "codex",
            "route_manifest_detected": True,
            "manifest_selected_skills": ["backend-change-builder"],
            "manifest_selected_capabilities": ["implementation-structure-design"],
            "manifest_required_references": ["docs/TELEMETRY.md"],
            "manifest_required_quality_gates": ["test gate"],
        },
        {
            "timestamp_utc": "2026-06-01T00:01:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "read",
            "tool_name": "rg",
            "read_paths": ["src/app.py"],
            "read_evidence_seen": True,
            "repository_context_seen": True,
        },
        {
            "timestamp_utc": "2026-06-01T00:02:00Z",
            "session_id": "sess",
            "event_name": "PreToolUse",
            "runtime": "codex",
            "turn_stage": "plan",
            "implementation_preflight_seen": True,
            "implementation_preflight_complete": True,
        },
        {
            "timestamp_utc": "2026-06-01T00:03:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "edit",
            "tool_name": "apply_patch",
            "changed_paths": ["src/app.py"],
        },
        {
            "timestamp_utc": "2026-06-01T00:04:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "test",
            "command_program": "python3",
            "validation_command_detected": True,
            "validation_evidence_detected": True,
            "validation_result_outcome": "pass",
        },
        {
            "timestamp_utc": "2026-06-01T00:05:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "review",
            "review_evidence_seen": True,
            "owner_skill": "backend-change-builder",
            "reviewer_skill": "ai-code-review-refactor",
        },
        {
            "timestamp_utc": "2026-06-01T00:06:00Z",
            "session_id": "sess",
            "event_name": "Stop",
            "runtime": "codex",
            "residual_risk_detected": True,
        },
    ]


def _stale_records() -> list[dict[str, object]]:
    records = _complete_records()
    records.insert(
        -1,
        {
            "timestamp_utc": "2026-06-01T00:05:30Z",
            "session_id": "sess-stale",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "edit",
            "tool_name": "apply_patch",
            "changed_paths": ["src/app.py"],
        },
    )
    for record in records:
        record["session_id"] = "sess-stale"
    return records


def _route_gap_records() -> list[dict[str, object]]:
    records = _complete_records()
    records[0] = dict(records[0])
    records[0]["manifest_selected_capabilities"] = []
    for record in records:
        record["session_id"] = "sess-route-gap"
    return records


def _repair_without_rereview_records() -> list[dict[str, object]]:
    records = _complete_records()
    records.insert(
        -1,
        {
            "timestamp_utc": "2026-06-01T00:05:30Z",
            "session_id": "sess-repair",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "repair",
            "tool_name": "apply_patch",
            "changed_paths": ["src/app.py"],
            "repair_evidence_seen": True,
            "validation_command_detected": True,
            "validation_evidence_detected": True,
            "validation_result_outcome": "pass",
        },
    )
    records.insert(
        -1,
        {
            "timestamp_utc": "2026-06-01T00:05:40Z",
            "session_id": "sess-repair",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "test",
            "command_program": "python3",
            "validation_command_detected": True,
            "validation_evidence_detected": True,
            "validation_result_outcome": "pass",
        },
    )
    for record in records:
        record["session_id"] = "sess-repair"
    return records


def _missing_residual_risk_records() -> list[dict[str, object]]:
    records = _complete_records()
    records[-1] = dict(records[-1])
    records[-1]["residual_risk_detected"] = False
    for record in records:
        record["session_id"] = "sess-risk"
    return records


def _unsupported_adapter_records() -> list[dict[str, object]]:
    records = _complete_records()
    records[-1] = dict(records[-1])
    records[-1].update(
        {
            "adapter_name": "copilot",
            "adapter_unsupported_checks": ["pre_tool_advisory_context"],
            "adapter_degraded_capabilities": ["copilot_pre_tool_advisory_unsupported"],
            "closure_contract_verdict": "degraded_ready",
            "closure_contract_residual_risk": ["unsupported adapter check"],
        }
    )
    for record in records:
        record["session_id"] = "sess-adapter"
    return records


if __name__ == "__main__":
    raise SystemExit(main())
