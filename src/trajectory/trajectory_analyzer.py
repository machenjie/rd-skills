"""Deterministic trajectory analyzer."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .trajectory_issue_classifier import classify_issue, highest_severity


STAGE_ORDER = ("user_prompt", "route", "read", "plan", "edit", "test", "review", "repair", "re_review", "stop")


def analyze_trajectory(trajectory: dict[str, Any]) -> dict[str, Any]:
    """Analyze a trajectory and return a report without mutating input."""
    steps = [step for step in trajectory.get("steps", []) if isinstance(step, dict)]
    issues: list[dict[str, Any]] = []

    issues.extend(_route_manifest_issues(steps))
    issues.extend(_edit_before_read_issues(steps))
    issues.extend(_plan_before_repo_context_issues(steps))
    issues.extend(_preflight_issues(steps))
    issues.extend(_validation_issues(steps))
    issues.extend(_review_issues(steps))
    issues.extend(_stop_issues(steps))
    issues.extend(_repeat_failure_issues(steps))
    issues.extend(_fragile_file_issues(steps))

    counts = dict(Counter(str(issue.get("type")) for issue in issues))
    highest = highest_severity(issues)
    validation_freshness = _validation_freshness(steps)
    review_integrity = _review_integrity(steps, issues)
    closure_status = _closure_status(highest, validation_freshness)

    return {
        "schema_version": 1,
        "session_id": str(trajectory.get("session_id") or ""),
        "closure_status": closure_status,
        "issue_counts": counts,
        "highest_severity": highest,
        "skipped_stages": _skipped_stages(steps),
        "validation_freshness": validation_freshness,
        "review_integrity": review_integrity,
        "recommended_promotions": _recommended_promotions(issues),
        "issues": issues,
    }


def attach_issues(trajectory: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow trajectory copy with report issues attached."""
    copied = dict(trajectory)
    copied["steps"] = list(trajectory.get("steps", []))
    copied["issues"] = list(report.get("issues", []))
    return copied


def _route_manifest_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    route_candidates = [step for step in steps if step.get("stage") in {"route", "stop"}]
    for step in route_candidates:
        facts = _facts(step)
        if not facts.get("route_manifest_detected") and step.get("stage") == "route":
            issues.append(
                classify_issue(
                    "route_manifest_incomplete",
                    int(step.get("index") or 0),
                    "Route stage did not include a complete route manifest.",
                )
            )
            continue
        if not facts.get("route_manifest_detected"):
            continue
        required_fields = (
            "selected_skills",
            "selected_capabilities",
            "required_references",
            "required_quality_gates",
        )
        missing = [field for field in required_fields if not facts.get(field)]
        if missing:
            issues.append(
                classify_issue(
                    "route_manifest_incomplete",
                    int(step.get("index") or 0),
                    "Route manifest is missing: " + ", ".join(missing) + ".",
                )
            )
    return _dedupe_issues(issues)


def _edit_before_read_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    read_seen = False
    for step in steps:
        evidence = _evidence(step)
        read_seen = read_seen or bool(evidence.get("read_evidence_seen")) or step.get("stage") == "read"
        if _material_edit(step) and not read_seen:
            issues.append(
                classify_issue(
                    "edit_before_read",
                    int(step.get("index") or 0),
                    "Material edit occurred before any read evidence was seen.",
                )
            )
            break
    return issues


def _plan_before_repo_context_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    repo_context_seen = False
    for step in steps:
        evidence = _evidence(step)
        repo_context_seen = repo_context_seen or bool(evidence.get("repository_context_seen"))
        if step.get("stage") == "plan" or evidence.get("implementation_preflight_seen"):
            if not repo_context_seen:
                issues.append(
                    classify_issue(
                        "plan_before_repo_context",
                        int(step.get("index") or 0),
                        "Plan or implementation preflight appeared before repository context evidence.",
                    )
                )
                break
    return issues


def _preflight_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    preflight_seen = False
    for step in steps:
        evidence = _evidence(step)
        facts = _facts(step)
        preflight_seen = preflight_seen or bool(evidence.get("implementation_preflight_seen"))
        if not _material_edit(step):
            continue
        if preflight_seen and not facts.get("edit_without_preflight_seen") and not facts.get("post_edit_confirmed_preflight_gap"):
            continue
        if facts.get("implementation_preflight_required") or facts.get("edit_without_preflight_seen") or facts.get(
            "post_edit_confirmed_preflight_gap"
        ) or facts.get("added_paths"):
            issues.append(
                classify_issue(
                    "missing_implementation_preflight",
                    int(step.get("index") or 0),
                    "Structural or preflight-required edit did not have complete implementation preflight evidence.",
                )
            )
            break
    return issues


def _validation_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    material_edit_indexes = [int(step.get("index") or 0) for step in steps if _material_edit(step)]
    if not material_edit_indexes:
        return issues
    final_edit = max(material_edit_indexes)
    validation_steps = [step for step in steps if _validation_command_or_evidence(step)]
    evidence_steps = [step for step in validation_steps if _step_validation_seen(step)]

    if not validation_steps:
        issues.append(
            classify_issue(
                "missing_validation",
                final_edit,
                "Material edit reached stop without validation evidence.",
            )
        )
        return issues

    for step in validation_steps:
        evidence = _evidence(step)
        if _step_validation_command_seen(step) and not evidence.get("validation_outcome_seen"):
            issues.append(
                classify_issue(
                    "validation_without_outcome",
                    int(step.get("index") or 0),
                    "Validation command was observed without a pass/fail outcome.",
                )
            )

    latest_evidence_index = max((int(step.get("index") or 0) for step in evidence_steps), default=0)
    if latest_evidence_index == 0:
        issues.append(
            classify_issue(
                "missing_validation",
                final_edit,
                "Material edit had validation commands but no validation evidence with outcome.",
            )
        )
    elif latest_evidence_index < final_edit:
        issues.append(
            classify_issue(
                "stale_validation",
                latest_evidence_index,
                "Latest validation evidence occurred before the final material edit.",
            )
        )
    return _dedupe_issues(issues)


def _review_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for step in steps:
        facts = _facts(step)
        owner = str(facts.get("owner_skill") or "")
        reviewer = str(facts.get("reviewer_skill") or "")
        if owner and reviewer and owner == reviewer:
            issues.append(
                classify_issue(
                    "self_review",
                    int(step.get("index") or 0),
                    "Owner skill and reviewer skill are identical.",
                )
            )
            break

    repair_indexes = [int(step.get("index") or 0) for step in steps if step.get("stage") == "repair" or _evidence(step).get("repair_seen")]
    if repair_indexes:
        latest_repair = max(repair_indexes)
        rereview_seen = any(
            int(step.get("index") or 0) > latest_repair
            and (step.get("stage") in {"review", "re_review"} or _evidence(step).get("review_seen"))
            for step in steps
        )
        if not rereview_seen:
            issues.append(
                classify_issue(
                    "repair_without_rereview",
                    latest_repair,
                    "Repair evidence was seen without later independent re-review evidence.",
                )
            )
    return issues


def _stop_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not any(_material_edit(step) for step in steps):
        return []
    stop_steps = [step for step in steps if step.get("stage") == "stop"]
    if not stop_steps:
        return []
    latest_stop = stop_steps[-1]
    if not _evidence(latest_stop).get("residual_risk_seen"):
        return [
            classify_issue(
                "stop_without_residual_risk",
                int(latest_stop.get("index") or 0),
                "Final handoff did not include residual risk evidence.",
            )
        ]
    return []


def _repeat_failure_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    failures_by_key: dict[tuple[str, str], list[int]] = {}
    for step in steps:
        if step.get("stage") in {"route", "repair"}:
            failures_by_key.clear()
            continue
        if step.get("outcome") != "fail":
            continue
        key = (_primary_path(step), str(step.get("command_program") or step.get("stage") or ""))
        failures_by_key.setdefault(key, []).append(int(step.get("index") or 0))
        if len(failures_by_key[key]) >= 2:
            issues.append(
                classify_issue(
                    "repeat_failure_without_route_repair",
                    int(step.get("index") or 0),
                    "Repeated same-path failure was not followed by route repair before another attempt.",
                )
            )
            break
    return issues


def _fragile_file_issues(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for step in steps:
        risk = {str(item) for item in step.get("risk_surfaces", []) or []}
        facts = _facts(step)
        if "fragile-file" not in risk and facts.get("memory_event_type") != "fragile_file":
            continue
        evidence = _evidence(step)
        missing = []
        if not evidence.get("memory_summary_seen"):
            missing.append("memory")
        if not evidence.get("implementation_preflight_seen"):
            missing.append("preflight")
        if not evidence.get("read_evidence_seen"):
            missing.append("read")
        if not evidence.get("nearby_test_seen") and not evidence.get("validation_seen"):
            missing.append("test")
        if missing:
            issues.append(
                classify_issue(
                    "fragile_file_without_preflight",
                    int(step.get("index") or 0),
                    "Fragile-file evidence missing: " + ", ".join(missing) + ".",
                )
            )
            break
    return issues


def _validation_freshness(steps: list[dict[str, Any]]) -> str:
    material_edit_indexes = [int(step.get("index") or 0) for step in steps if _material_edit(step)]
    if not material_edit_indexes:
        return "not_applicable"
    validation_steps = [step for step in steps if _step_validation_seen(step)]
    if not validation_steps:
        return "not_run"
    if max(int(step.get("index") or 0) for step in validation_steps) > max(material_edit_indexes):
        return "fresh"
    return "stale"


def _review_integrity(steps: list[dict[str, Any]], issues: list[dict[str, Any]]) -> str:
    issue_types = {str(issue.get("type")) for issue in issues}
    if "repair_without_rereview" in issue_types:
        return "fail"
    if "self_review" in issue_types:
        return "warn"
    if any(step.get("stage") in {"review", "re_review"} or _evidence(step).get("review_seen") for step in steps):
        return "pass"
    return "warn" if any(_material_edit(step) for step in steps) else "pass"


def _closure_status(highest: str, validation_freshness: str) -> str:
    if highest == "high":
        return "fail"
    if highest in {"medium", "low"} or validation_freshness in {"stale", "not_run"}:
        return "warn"
    return "pass"


def _recommended_promotions(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    promotions: list[dict[str, Any]] = []
    for issue in issues:
        if issue.get("severity") != "high":
            continue
        issue_type = str(issue.get("type"))
        promotions.append(
            {
                "type": "pressure_scenario",
                "issue_type": issue_type,
                "requires_human_review": True,
                "reason": "High severity trajectory issue should be considered for pressure behavior coverage.",
            }
        )
        promotions.append(
            {
                "type": "agent_behavior_sample",
                "issue_type": issue_type,
                "requires_human_review": True,
                "reason": "High severity trajectory issue may need a promoted behavior eval sample.",
            }
        )
        promotions.append(
            {
                "type": "hook_fixture",
                "issue_type": issue_type,
                "requires_human_review": True,
                "reason": "High severity trajectory issue may need a bounded hook fixture.",
            }
        )
        break
    return promotions


def _skipped_stages(steps: list[dict[str, Any]]) -> list[str]:
    present = {str(step.get("stage")) for step in steps}
    required = ("route", "read", "plan", "edit", "test", "review", "stop")
    if not any(_material_edit(step) for step in steps):
        required = ("route", "read", "stop")
    return [stage for stage in required if stage not in present]


def _validation_command_or_evidence(step: dict[str, Any]) -> bool:
    return bool(_step_validation_seen(step) or _step_validation_command_seen(step) or step.get("stage") == "test")


def _step_validation_seen(step: dict[str, Any]) -> bool:
    facts = _facts(step)
    if facts.get("validation_evidence_detected"):
        return True
    return step.get("stage") == "test" and step.get("outcome") in {"pass", "fail"} and _step_validation_command_seen(step)


def _step_validation_command_seen(step: dict[str, Any]) -> bool:
    facts = _facts(step)
    evidence = _evidence(step)
    return bool(facts.get("validation_command_detected") or evidence.get("validation_command_seen"))


def _material_edit(step: dict[str, Any]) -> bool:
    facts = _facts(step)
    return bool(facts.get("material_edit"))


def _primary_path(step: dict[str, Any]) -> str:
    paths = step.get("paths", []) or []
    return str(paths[0]) if paths else ""


def _evidence(step: dict[str, Any]) -> dict[str, Any]:
    value = step.get("evidence")
    return value if isinstance(value, dict) else {}


def _facts(step: dict[str, Any]) -> dict[str, Any]:
    value = step.get("facts")
    return value if isinstance(value, dict) else {}


def _dedupe_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int]] = set()
    result: list[dict[str, Any]] = []
    for issue in issues:
        key = (str(issue.get("type")), int(issue.get("step_index") or 0))
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result
