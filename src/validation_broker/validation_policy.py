"""Policy checks for validation closure evidence."""

from __future__ import annotations

from fnmatch import fnmatch
import re
from typing import Iterable

from .command_registry import commands_for_categories, matching_categories
from .command_resolver import resolve_validation_plan
from .validation_freshness import apply_freshness
from .validation_result_parser import parse_validation_result


FULL_SCOPE_CLAIM_RE = re.compile(
    r"\b("
    r"full\s+(?:regression|suite|pass|validation)|"
    r"all\s+(?:tests|checks|validation|regression)|"
    r"entire\s+(?:suite|regression)|"
    r"complete\s+regression"
    r")\b",
    re.IGNORECASE,
)
RESIDUAL_RISK_RE = re.compile(r"\b(residual\s+risk|risk|caveat|limitation|not\s+covered)\b", re.IGNORECASE)
REREVIEW_RE = re.compile(r"\b(re-?review|reviewed\s+again|second\s+review)\b", re.IGNORECASE)


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
    broker_result = _validation_broker_result(
        final_text=final_text,
        state=state,
        result=result,
        plan=plan,
        changed_paths=paths,
        risk_surfaces=surfaces,
        issues=issues,
    )
    all_issues = _dedupe([*issues, *broker_result.get("negative_evidence", [])])
    high_confidence = _high_confidence(all_issues, result)
    return {
        "schema_version": 1,
        "validation_result": result,
        "validation_plan": plan,
        "validation_broker_result": broker_result,
        "strong_evidence": not all_issues and result.get("evidence_strength") == "strong",
        "issues": all_issues,
        "warnings": all_issues,
        "should_block": bool(block_mode and high_confidence and all_issues),
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
    validation_required = bool(changed_paths or risk_surfaces)
    reason = str(result.get("negative_evidence_reason") or "")
    if result.get("outcome") == "not_run" and validation_required:
        issues.append(reason or "not_run")
    elif not result.get("validation_looking") and validation_required:
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


def _validation_broker_result(
    *,
    final_text: str,
    state: dict,
    result: dict[str, object],
    plan: dict[str, object],
    changed_paths: list[str],
    risk_surfaces: list[str],
    issues: list[str],
) -> dict[str, object]:
    path_mapping = _changed_path_mapping(changed_paths)
    coverage = _coverage_alignment(final_text, result, plan, changed_paths, risk_surfaces)
    negative = _negative_evidence(final_text, state, result, plan, changed_paths, risk_surfaces, issues, coverage)
    residual = _residual_risk(final_text, state, negative, path_mapping)
    return {
        "schema_version": 1,
        "changed_path_mapping": path_mapping,
        "selected_scope": _selected_scope(result, changed_paths, risk_surfaces),
        "selection_rationale": _selection_rationale(result, plan, changed_paths, risk_surfaces),
        "command_ledger": [
            _command_ledger_entry(result, coverage, negative, changed_paths, risk_surfaces)
        ],
        "freshness": _freshness_summary(result),
        "coverage_alignment": coverage,
        "negative_evidence": negative,
        "closure_outcome": _closure_outcome(changed_paths, risk_surfaces, negative, residual),
        "residual_risk": residual,
    }


def _changed_path_mapping(changed_paths: list[str]) -> list[dict[str, object]]:
    mapping: list[dict[str, object]] = []
    for path in changed_paths:
        categories = matching_categories([path])
        commands = commands_for_categories(categories, level="narrow") if categories else []
        mapping.append(
            {
                "path": path,
                "matched_categories": categories,
                "validator_candidates": [
                    {
                        "command_kind": command.level,
                        "command_display_safe": command.command,
                        "category": command.category,
                        "reason": command.reason,
                    }
                    for command in commands[:5]
                ],
                "validator_decision": "matched" if categories else "conservative_fallback",
            }
        )
    return mapping


def _selected_scope(
    result: dict[str, object],
    changed_paths: list[str],
    risk_surfaces: list[str],
) -> str:
    if not changed_paths and not risk_surfaces:
        return "none"
    kind = str(result.get("command_kind") or "").strip()
    if kind in {"narrow", "module", "full"}:
        return kind
    return "none"


def _selection_rationale(
    result: dict[str, object],
    plan: dict[str, object],
    changed_paths: list[str],
    risk_surfaces: list[str],
) -> str:
    if not changed_paths and not risk_surfaces:
        return "no changed paths or closure risk surfaces required validation"
    if result.get("validation_looking"):
        return "selected scope is based on the parsed validation command kind"
    categories = ", ".join(str(item) for item in plan.get("matched_categories", []) or [])
    return f"no validated command outcome; candidates came from matched categories: {categories or 'unknown'}"


def _command_ledger_entry(
    result: dict[str, object],
    coverage: dict[str, object],
    negative: list[str],
    changed_paths: list[str],
    risk_surfaces: list[str],
) -> dict[str, object]:
    outcome = _ledger_outcome(result, coverage, negative, changed_paths, risk_surfaces)
    strength = str(result.get("evidence_strength") or "")
    if outcome in {"failed", "stale", "not_run", "not_verified"}:
        strength = "negative"
    elif outcome == "partial":
        strength = "partial"
    return {
        "command_kind": str(result.get("command_kind") or "unknown"),
        "command_display_safe": _command_display_safe(result),
        "scope": str(result.get("command_kind") or "unknown"),
        "outcome": outcome,
        "finished_at_or_order": result.get("finished_index") or result.get("finished_at") or "",
        "covered_paths": _paths(result.get("covered_paths", [])),
        "covered_risk_surfaces": _paths(result.get("covered_risk_surfaces", [])),
        "evidence_strength": strength or "weak",
    }


def _ledger_outcome(
    result: dict[str, object],
    coverage: dict[str, object],
    negative: list[str],
    changed_paths: list[str],
    risk_surfaces: list[str],
) -> str:
    if result.get("fresh_after_last_edit") is False:
        return "stale"
    outcome = str(result.get("outcome") or "")
    reason = str(result.get("negative_evidence_reason") or "")
    if outcome == "fail":
        return "failed"
    if outcome == "not_run" and (changed_paths or risk_surfaces):
        return "not_verified" if reason in {"unable_to_run", "not_run"} else "not_run"
    if outcome == "unknown" and result.get("validation_looking"):
        return "not_verified"
    if coverage.get("aligned") is False or any(
        item in negative for item in ("targeted_check_reported_as_full", "coverage_mismatch")
    ):
        return "partial"
    if outcome == "pass" and result.get("evidence_strength") == "strong":
        return "passed"
    if not result.get("validation_looking") and (changed_paths or risk_surfaces):
        return "not_run"
    return "unknown"


def _command_display_safe(result: dict[str, object]) -> str:
    command = str(result.get("command") or "").strip()
    kind = str(result.get("command_kind") or "unknown").strip() or "unknown"
    if not command:
        return "no validation command"
    if kind in {"narrow", "module", "full"}:
        return command
    return f"validation command ({kind})"


def _freshness_summary(result: dict[str, object]) -> dict[str, object]:
    fresh = result.get("fresh_after_last_edit")
    status = "unknown"
    if fresh is True:
        status = "current"
    elif fresh is False:
        status = "stale"
    elif fresh == "not_applicable":
        status = "not_applicable"
    return {
        "status": status,
        "fresh_after_last_material_edit": fresh,
        "validation_finished": result.get("finished_index") or result.get("finished_at") or "",
        "last_material_edit": result.get("material_edit_cutoff") or "",
    }


def _coverage_alignment(
    final_text: str,
    result: dict[str, object],
    plan: dict[str, object],
    changed_paths: list[str],
    risk_surfaces: list[str],
) -> dict[str, object]:
    issues: list[str] = []
    aligned = result.get("coverage_aligned")
    if aligned is False and (changed_paths or risk_surfaces):
        issues.append("coverage_mismatch")
    covered_patterns = _paths(result.get("covered_paths", []))
    if changed_paths and covered_patterns and not _paths_covered(changed_paths, covered_patterns):
        aligned = False
        issues.append("coverage_mismatch")
    if _claims_full_scope(final_text) and str(result.get("command_kind") or "") in {"narrow", "module"}:
        aligned = False
        issues.append("targeted_check_reported_as_full")
    unknown_paths = _paths(plan.get("unknown_paths", []))
    if unknown_paths:
        aligned = False
        issues.append("changed_path_without_validator")
    return {
        "aligned": aligned,
        "issues": _dedupe(issues),
        "selected_scope": _selected_scope(result, changed_paths, risk_surfaces),
        "required_paths": changed_paths,
        "required_risk_surfaces": risk_surfaces,
        "covered_paths": _paths(result.get("covered_paths", [])),
        "covered_risk_surfaces": _paths(result.get("covered_risk_surfaces", [])),
        "unknown_paths": unknown_paths,
    }


def _negative_evidence(
    final_text: str,
    state: dict,
    result: dict[str, object],
    plan: dict[str, object],
    changed_paths: list[str],
    risk_surfaces: list[str],
    issues: list[str],
    coverage: dict[str, object],
) -> list[str]:
    negative: list[str] = []
    validation_required = bool(changed_paths or risk_surfaces)
    for issue in issues:
        negative.append(_canonical_negative(issue))
    if validation_required and not result.get("validation_looking"):
        negative.append("missing_validation")
    if result.get("validation_looking") and result.get("outcome") == "unknown":
        negative.append("validation_command_without_outcome")
    if result.get("fresh_after_last_edit") is False:
        negative.append("stale_validation")
    if _paths(plan.get("unknown_paths", [])):
        negative.append("changed_path_without_validator")
    negative.extend(str(item) for item in coverage.get("issues", []) or [])
    if _repair_without_rereview(final_text, state):
        negative.append("repair_without_rereview")
    if _unsupported_adapter_degradation(state):
        negative.append("unsupported_adapter_check")
    if validation_required and not _residual_risk_disclosed(final_text, state):
        negative.append("missed_residual_risk")
    return _dedupe(item for item in negative if item)


def _canonical_negative(issue: str) -> str:
    return {
        "command_without_outcome": "validation_command_without_outcome",
        "validation_stale": "stale_validation",
        "validation_missing": "missing_validation",
        "not_run": "validation_not_run",
        "unable_to_run": "validation_not_run",
        "validation_failed": "validation_failed",
    }.get(issue, issue)


def _residual_risk(
    final_text: str,
    state: dict,
    negative: list[str],
    path_mapping: list[dict[str, object]],
) -> list[str]:
    residual: list[str] = []
    for item in negative:
        if item in {
            "changed_path_without_validator",
            "targeted_check_reported_as_full",
            "coverage_mismatch",
            "unsupported_adapter_check",
            "missed_residual_risk",
        }:
            residual.append(item)
    for item in path_mapping:
        if item.get("validator_decision") == "conservative_fallback":
            residual.append(f"no_validator:{item.get('path')}")
    if _unsupported_adapter_degradation(state):
        residual.extend(_unsupported_adapter_degradation(state))
    if residual and not _residual_risk_disclosed(final_text, state):
        residual.append("residual_risk_not_disclosed")
    return _dedupe(residual)


def _closure_outcome(
    changed_paths: list[str],
    risk_surfaces: list[str],
    negative: list[str],
    residual: list[str],
) -> str:
    if not changed_paths and not risk_surfaces and not negative:
        return "ready"
    if any(item in negative for item in ("validation_failed", "stale_validation", "repair_without_rereview")):
        return "blocked"
    validation_blockers = {
        "missing_validation",
        "validation_command_without_outcome",
        "validation_not_run",
        "coverage_mismatch",
        "targeted_check_reported_as_full",
        "changed_path_without_validator",
        "missed_residual_risk",
    }
    if any(item in validation_blockers for item in negative):
        return "needs_validation"
    if any("unsupported" in item for item in [*negative, *residual]):
        return "degraded_ready"
    return "ready"


def _claims_full_scope(final_text: str) -> bool:
    return bool(FULL_SCOPE_CLAIM_RE.search(final_text or ""))


def _paths_covered(changed_paths: list[str], covered_patterns: list[str]) -> bool:
    for path in changed_paths:
        if not any(pattern == "**" or fnmatch(path, pattern) for pattern in covered_patterns):
            return False
    return True


def _residual_risk_disclosed(final_text: str, state: dict) -> bool:
    if state.get("residual_risk_detected") or state.get("residual_risk_seen"):
        return True
    return bool(RESIDUAL_RISK_RE.search(final_text or ""))


def _repair_without_rereview(final_text: str, state: dict) -> bool:
    repair_seen = bool(state.get("repair_evidence_seen") or state.get("repair_findings"))
    if not repair_seen:
        return False
    return not bool(
        state.get("review_after_repair_seen")
        or state.get("re_review_evidence_seen")
        or REREVIEW_RE.search(final_text or "")
    )


def _unsupported_adapter_degradation(state: dict) -> list[str]:
    candidates = (
        state.get("unsupported_adapter_events")
        or state.get("adapter_unsupported_events")
        or state.get("capability_degradation")
        or []
    )
    return [f"unsupported_adapter:{item}" for item in _paths(candidates)]


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
