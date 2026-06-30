#!/usr/bin/env python3
"""Deterministic structural eval for Business Semantic routing fixtures."""

from __future__ import annotations

from pathlib import Path

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "business-semantic"
REQUIRED_GATES_FOR_BSP = {"domain gate", "test gate"}


def main() -> int:
    errors: list[str] = []
    cases = [load_yaml_file(path) for path in sorted(EVAL_DIR.glob("*.yaml"))]
    if len(cases) != 10:
        errors.append(f"expected 10 fixtures, found {len(cases)}")
    bsp_required = 0
    bsp_selected = 0
    overroute_cases = 0
    for case in cases:
        case_id = str(case.get("case_id", "unknown"))
        route = case.get("expected_route", {})
        capabilities = set(case.get("expected_capabilities", []) or [])
        gates = set(case.get("expected_quality_gates", []) or [])
        sections = set(case.get("expected_bsp_sections", []) or [])
        required = bool(isinstance(route, dict) and route.get("business_semantic_pack_required") is True)
        if required:
            bsp_required += 1
            if "business-semantic-control-plane" in capabilities:
                bsp_selected += 1
            else:
                errors.append(f"{case_id}: missing business-semantic-control-plane")
            if not REQUIRED_GATES_FOR_BSP & gates:
                errors.append(f"{case_id}: BSP route lacks domain or test gate")
            if not sections:
                errors.append(f"{case_id}: BSP route must expect BSP sections")
        else:
            overroute_cases += 1
            if "business-semantic-control-plane" in capabilities:
                errors.append(f"{case_id}: over-routed simple case selects BSP")
        if "stage" not in route:
            errors.append(f"{case_id}: expected_route must name stage")
    if errors:
        return fail_many("eval-business-semantic-routing", errors)
    print(
        "eval-business-semantic-routing: OK "
        f"cases={len(cases)} bsp_required={bsp_required} "
        f"bsp_selected={bsp_selected} skip_cases={overroute_cases}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
