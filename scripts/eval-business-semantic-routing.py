#!/usr/bin/env python3
"""Compare Business Semantic routing fixtures with deterministic actual outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = ROOT / "evals" / "business-semantic"
DEFAULT_OUTPUT_DIR = ROOT / "evals" / "business-semantic-outputs"
EVAL_DIR = DEFAULT_EVAL_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR

EXPECTED_METADATA = {
    "generated_by": "scripts/generate-business-semantic-actuals.py",
    "generation_mode": "deterministic",
    "route_source": "current deterministic route resolver / fixture route adapter",
    "review_source": "deterministic source/diff/prompt/trigger review skeleton",
}


def main() -> int:
    errors: list[str] = []
    cases = [(path, load_yaml_file(path)) for path in sorted(EVAL_DIR.glob("*.yaml"))]
    if _using_default_dirs() and len(cases) != 10:
        errors.append(f"expected 10 fixtures, found {len(cases)}")
    metrics = {
        "cases": len(cases),
        "bsp_required_expected": 0,
        "bsp_required_actual": 0,
        "skill_expected": 0,
        "skill_hit": 0,
        "capability_expected": 0,
        "capability_hit": 0,
        "gate_expected": 0,
        "gate_hit": 0,
        "scope_expected": 0,
        "scope_hit": 0,
        "trigger_expected": 0,
        "trigger_hit": 0,
        "overroute_failures": 0,
        "underroute_failures": 0,
    }
    for path, case in cases:
        _validate_case(path, case, metrics, errors)
    if errors:
        return fail_many("eval-business-semantic-routing", errors)
    skill_recall = _ratio(metrics["skill_hit"], metrics["skill_expected"])
    capability_recall = _ratio(metrics["capability_hit"], metrics["capability_expected"])
    gate_recall = _ratio(metrics["gate_hit"], metrics["gate_expected"])
    scope_match = _ratio(metrics["scope_hit"], metrics["scope_expected"])
    trigger_recall = _ratio(metrics["trigger_hit"], metrics["trigger_expected"])
    print(
        "eval-business-semantic-routing: OK "
        f"cases={metrics['cases']} "
        f"bsp_required_expected={metrics['bsp_required_expected']} "
        f"bsp_required_actual={metrics['bsp_required_actual']} "
        f"skill_recall={skill_recall:.2f} "
        f"capability_recall={capability_recall:.2f} "
        f"gate_recall={gate_recall:.2f} "
        f"scope_match={scope_match:.2f} "
        f"trigger_recall={trigger_recall:.2f} "
        f"overroute_failures={metrics['overroute_failures']} "
        f"underroute_failures={metrics['underroute_failures']}"
    )
    return 0


def _validate_case(
    path: Path,
    case: dict[str, Any],
    metrics: dict[str, int],
    errors: list[str],
) -> None:
    case_id = str(case.get("case_id") or path.stem)
    actual_path = OUTPUT_DIR / f"{case_id}.actual.yaml"
    if not actual_path.is_file():
        errors.append(f"{case_id}: missing actual output {actual_path.relative_to(ROOT)}")
        return
    actual_doc = load_yaml_file(actual_path)
    _validate_actual_metadata(case_id, actual_doc, errors)
    actual = actual_doc.get("actual_route") if isinstance(actual_doc, dict) else None
    if not isinstance(actual, dict):
        errors.append(f"{case_id}: actual output must contain actual_route")
        return
    expected_route = case.get("expected_route", {})
    if not isinstance(expected_route, dict):
        errors.append(f"{case_id}: expected_route must be a mapping")
        return
    expected_stage = expected_route.get("stage")
    actual_stage = actual.get("stage")
    if expected_stage != actual_stage:
        errors.append(f"{case_id}: stage expected {expected_stage!r}, actual {actual_stage!r}")
    expected_bsp = bool(expected_route.get("business_semantic_pack_required"))
    actual_bsp = bool(actual.get("business_semantic_pack_required"))
    if expected_bsp:
        metrics["bsp_required_expected"] += 1
    if actual_bsp:
        metrics["bsp_required_actual"] += 1
    if expected_bsp != actual_bsp:
        errors.append(f"{case_id}: business_semantic_pack_required expected {expected_bsp}, actual {actual_bsp}")
    expected_scope = expected_route.get("business_semantic_scope")
    actual_scope = actual.get("business_semantic_scope")
    metrics["scope_expected"] += 1
    if expected_scope == actual_scope:
        metrics["scope_hit"] += 1
    else:
        errors.append(f"{case_id}: business_semantic_scope expected {expected_scope!r}, actual {actual_scope!r}")
    expected_triggers = set(_as_list(case.get("routing_triggers")))
    actual_triggers = set(_as_list(actual.get("detected_triggers")))
    if not case.get("routing_triggers_optional"):
        metrics["trigger_expected"] += len(expected_triggers)
        metrics["trigger_hit"] += len(expected_triggers & actual_triggers)
        missing_triggers = sorted(expected_triggers - actual_triggers)
        if missing_triggers:
            errors.append(f"{case_id}: missing expected detected triggers {missing_triggers}")
    expected_skills = set(_as_list(case.get("expected_skills")))
    actual_skills = set(_as_list(actual.get("selected_skills")))
    metrics["skill_expected"] += len(expected_skills)
    metrics["skill_hit"] += len(expected_skills & actual_skills)
    missing_skills = sorted(expected_skills - actual_skills)
    if missing_skills:
        errors.append(f"{case_id}: missing expected skills {missing_skills}")
    expected_capabilities = set(_as_list(case.get("expected_capabilities")))
    actual_capabilities = set(_as_list(actual.get("selected_capabilities")))
    metrics["capability_expected"] += len(expected_capabilities)
    metrics["capability_hit"] += len(expected_capabilities & actual_capabilities)
    missing_capabilities = sorted(expected_capabilities - actual_capabilities)
    if missing_capabilities:
        errors.append(f"{case_id}: missing expected capabilities {missing_capabilities}")
    expected_gates = set(_as_list(case.get("expected_quality_gates")))
    actual_gates = set(_as_list(actual.get("required_quality_gates")))
    metrics["gate_expected"] += len(expected_gates)
    metrics["gate_hit"] += len(expected_gates & actual_gates)
    missing_gates = sorted(expected_gates - actual_gates)
    if missing_gates:
        errors.append(f"{case_id}: missing expected quality gates {missing_gates}")
    expected_sections = set(_as_list(case.get("expected_bsp_sections")))
    actual_sections = set(_as_list(actual.get("selected_bsp_sections")))
    missing_sections = sorted(expected_sections - actual_sections)
    if missing_sections:
        errors.append(f"{case_id}: missing expected BSP sections {missing_sections}")
    _validate_reference_decisions(case_id, actual, errors)
    _validate_forbidden_route_behavior(case_id, case, actual, metrics, errors)


def _validate_reference_decisions(case_id: str, actual: dict[str, Any], errors: list[str]) -> None:
    for field in ("selected_references", "skipped_references"):
        refs = actual.get(field, [])
        if not isinstance(refs, list):
            errors.append(f"{case_id}: actual_route.{field} must be a list")
            continue
        for index, item in enumerate(refs):
            if not isinstance(item, dict):
                errors.append(f"{case_id}: actual_route.{field}[{index}] must be an object")
                continue
            for required in ("reference", "reason", "evidence_limit"):
                if not item.get(required):
                    errors.append(f"{case_id}: actual_route.{field}[{index}] missing {required}")
            if "residual_risk" not in item:
                errors.append(f"{case_id}: actual_route.{field}[{index}] missing residual_risk")


def _validate_forbidden_route_behavior(
    case_id: str,
    case: dict[str, Any],
    actual: dict[str, Any],
    metrics: dict[str, int],
    errors: list[str],
) -> None:
    forbidden = " ".join(_as_list(case.get("forbidden_behavior"))).casefold()
    selected_skills = set(_as_list(actual.get("selected_skills")))
    selected_capabilities = set(_as_list(actual.get("selected_capabilities")))
    actual_bsp = bool(actual.get("business_semantic_pack_required"))
    forbidden_skills = set(_as_list(case.get("forbidden_skills")))
    forbidden_capabilities = set(_as_list(case.get("forbidden_capabilities")))
    forbidden_skill_hits = sorted(forbidden_skills & selected_skills)
    forbidden_capability_hits = sorted(forbidden_capabilities & selected_capabilities)
    failed_overroute = False
    if forbidden_skill_hits:
        errors.append(f"{case_id}: forbidden skills selected {forbidden_skill_hits}")
        failed_overroute = True
    if forbidden_capability_hits:
        errors.append(f"{case_id}: forbidden capabilities selected {forbidden_capability_hits}")
        failed_overroute = True
    allow_broad_route = case.get("allow_broad_route") is True
    if not allow_broad_route:
        max_skills = case.get("max_selected_skills")
        if isinstance(max_skills, int) and len(selected_skills) > max_skills:
            errors.append(f"{case_id}: selected skills count {len(selected_skills)} exceeds max_selected_skills {max_skills}")
            failed_overroute = True
        max_capabilities = case.get("max_selected_capabilities")
        if isinstance(max_capabilities, int) and len(selected_capabilities) > max_capabilities:
            errors.append(
                f"{case_id}: selected capabilities count {len(selected_capabilities)} exceeds "
                f"max_selected_capabilities {max_capabilities}"
            )
            failed_overroute = True
    if failed_overroute:
        metrics["overroute_failures"] += 1
    if case_id == "over-routing-simple-local-change":
        failed = False
        forbidden_skills = {"domain-impact-modeler", "ai-code-review-refactor", "quality-test-gate"}
        unexpected_skills = sorted(forbidden_skills & selected_skills)
        if unexpected_skills:
            errors.append(f"{case_id}: overroute selected high-risk skills {unexpected_skills}")
            failed = True
        if "business-semantic-control-plane" in selected_capabilities:
            errors.append(f"{case_id}: overroute selected business-semantic-control-plane")
            failed = True
        if actual_bsp:
            errors.append(f"{case_id}: overroute required BSP")
            failed = True
        if failed:
            metrics["overroute_failures"] += 1
    if case_id == "under-routing-high-risk-business-change":
        needed = {"domain gate", "test gate", "AI review gate"}
        needed_skills = {"domain-impact-modeler", "quality-test-gate", "ai-code-review-refactor"}
        gates = set(_as_list(actual.get("required_quality_gates")))
        failed = False
        if not actual_bsp:
            errors.append(f"{case_id}: underroute did not require BSP")
            failed = True
        missing_skills = sorted(needed_skills - selected_skills)
        if missing_skills:
            errors.append(f"{case_id}: underroute missing high-risk skills {missing_skills}")
            failed = True
        missing = sorted(needed - gates)
        if missing:
            errors.append(f"{case_id}: underroute missing high-risk gates {missing}")
            failed = True
        if failed:
            metrics["underroute_failures"] += 1
    if "select business-semantic-control-plane" in forbidden and "business-semantic-control-plane" in selected_capabilities:
        errors.append(f"{case_id}: forbidden behavior selected business-semantic-control-plane")
    if "require full bsp" in forbidden and actual_bsp and case_id == "over-routing-simple-local-change":
        errors.append(f"{case_id}: forbidden behavior required full BSP")


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    return [str(value)]


def _ratio(hit: int, expected: int) -> float:
    return 1.0 if expected == 0 else hit / expected


def _validate_actual_metadata(case_id: str, actual_doc: Any, errors: list[str]) -> None:
    metadata = actual_doc.get("actual_metadata") if isinstance(actual_doc, dict) else None
    if not isinstance(metadata, dict):
        errors.append(f"{case_id}: actual output missing actual_metadata")
        return
    for key, expected in EXPECTED_METADATA.items():
        if metadata.get(key) != expected:
            errors.append(f"{case_id}: actual_metadata.{key} expected {expected!r}, actual {metadata.get(key)!r}")
    if not metadata.get("source_fixture"):
        errors.append(f"{case_id}: actual_metadata.source_fixture must be non-empty")


def _using_default_dirs() -> bool:
    return EVAL_DIR == DEFAULT_EVAL_DIR and OUTPUT_DIR == DEFAULT_OUTPUT_DIR


if __name__ == "__main__":
    raise SystemExit(main())
