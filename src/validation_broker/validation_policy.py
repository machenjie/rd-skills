"""Policy checks for validation closure evidence."""

from __future__ import annotations

from typing import Iterable

from .command_resolver import resolve_validation_plan
from .validation_freshness import apply_freshness
from .validation_result_parser import parse_validation_result


def assess_validation_closure(
    final_text: str,
    state: dict | None = None,
    *,
    changed_paths: Iterable[str] = (),
    risk_surfaces: Iterable[str] = (),
    stage: str = "",
    block_mode: bool = False,
) -> dict[str, object]:
    """Assess whether closure validation is fresh, covered, and strong."""
    state = state if isinstance(state, dict) else {}
    paths = _paths(changed_paths) or _paths(state.get("changed_paths", []))
    surfaces = _paths(risk_surfaces) or _paths(
        state.get("closure_risk_surfaces", []) or state.get("risk_surfaces", [])
    )
    finish_index = _state_int(state.get("last_validation_command_index"))
    result = parse_validation_result(
        final_text,
        finished_index=finish_index,
        changed_paths=paths,
        risk_surfaces=surfaces,
    )
    result = apply_freshness(
        result,
        material_edit_cutoff=_state_int(state.get("last_material_edit_index")),
        validation_finish=finish_index,
    )
    result = _normalize_result_for_policy(result)
    plan = resolve_validation_plan(paths, surfaces, stage=stage or str(state.get("turn_stage", "")))
    issues = _issues(result, paths, surfaces)
    high_confidence = _high_confidence(issues, result)
    return {
        "schema_version": 1,
        "validation_result": result,
        "validation_plan": plan,
        "strong_evidence": not issues and result.get("evidence_strength") == "strong",
        "issues": issues,
        "warnings": issues,
        "should_block": bool(block_mode and high_confidence and issues),
        "high_confidence": high_confidence,
        "next_route": _next_route(result),
    }


def _normalize_result_for_policy(result: dict[str, object]) -> dict[str, object]:
    normalized = dict(result)
    outcome = normalized.get("outcome")
    if outcome == "unknown" and normalized.get("validation_looking"):
        normalized["evidence_strength"] = "weak"
        normalized["negative_evidence_reason"] = "no_outcome"
    if outcome == "fail":
        normalized["evidence_strength"] = "negative"
        normalized["negative_evidence_reason"] = "failed"
    return normalized


def _issues(
    result: dict[str, object],
    changed_paths: list[str],
    risk_surfaces: list[str],
) -> list[str]:
    issues: list[str] = []
    reason = str(result.get("negative_evidence_reason") or "")
    if result.get("outcome") == "not_run":
        issues.append(reason or "not_run")
    elif not result.get("validation_looking"):
        issues.append("validation_missing")
    elif result.get("outcome") == "unknown":
        issues.append("command_without_outcome")
    elif result.get("outcome") == "fail":
        issues.append("validation_failed")
    if result.get("fresh_after_last_edit") is False and "validation_stale" not in issues:
        issues.append("validation_stale")
    if result.get("fresh_after_last_edit") == "unknown" and changed_paths:
        issues.append("freshness_unknown")
    if result.get("coverage_aligned") is False and (changed_paths or risk_surfaces):
        issues.append("coverage_mismatch")
    if reason and reason not in issues:
        issues.append(reason)
    return _dedupe(issues)


def _high_confidence(issues: list[str], result: dict[str, object]) -> bool:
    if any(issue in issues for issue in ("validation_stale", "validation_failed", "not_run")):
        return True
    if result.get("validation_looking") and result.get("outcome") == "unknown":
        return True
    return False


def _next_route(result: dict[str, object]) -> list[str]:
    if result.get("outcome") == "fail":
        return ["failure-diagnosis", "quality-test-gate"]
    if result.get("fresh_after_last_edit") is False:
        return ["quality-test-gate"]
    if result.get("evidence_strength") != "strong":
        return ["quality-test-gate"]
    return []


def _paths(values: object) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _state_int(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
