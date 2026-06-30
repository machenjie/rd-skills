#!/usr/bin/env python3
"""Compare Business Semantic routing fixtures with deterministic actual outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "business-semantic"
OUTPUT_DIR = ROOT / "evals" / "business-semantic-outputs"


def main() -> int:
    errors: list[str] = []
    cases = [(path, load_yaml_file(path)) for path in sorted(EVAL_DIR.glob("*.yaml"))]
    if len(cases) != 10:
        errors.append(f"expected 10 fixtures, found {len(cases)}")
    metrics = {
        "cases": len(cases),
        "bsp_required_expected": 0,
        "bsp_required_actual": 0,
        "capability_expected": 0,
        "capability_hit": 0,
        "gate_expected": 0,
        "gate_hit": 0,
        "overroute_failures": 0,
        "underroute_failures": 0,
    }
    for path, case in cases:
        _validate_case(path, case, metrics, errors)
    if errors:
        return fail_many("eval-business-semantic-routing", errors)
    capability_recall = _ratio(metrics["capability_hit"], metrics["capability_expected"])
    gate_recall = _ratio(metrics["gate_hit"], metrics["gate_expected"])
    print(
        "eval-business-semantic-routing: OK "
        f"cases={metrics['cases']} "
        f"bsp_required_expected={metrics['bsp_required_expected']} "
        f"bsp_required_actual={metrics['bsp_required_actual']} "
        f"capability_recall={capability_recall:.2f} "
        f"gate_recall={gate_recall:.2f} "
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


def _validate_forbidden_route_behavior(
    case_id: str,
    case: dict[str, Any],
    actual: dict[str, Any],
    metrics: dict[str, int],
    errors: list[str],
) -> None:
    forbidden = " ".join(_as_list(case.get("forbidden_behavior"))).casefold()
    selected_capabilities = set(_as_list(actual.get("selected_capabilities")))
    actual_bsp = bool(actual.get("business_semantic_pack_required"))
    if case_id == "over-routing-simple-local-change":
        failed = False
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
        gates = set(_as_list(actual.get("required_quality_gates")))
        failed = False
        if not actual_bsp:
            errors.append(f"{case_id}: underroute did not require BSP")
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


if __name__ == "__main__":
    raise SystemExit(main())
