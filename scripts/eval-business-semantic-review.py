#!/usr/bin/env python3
"""Deterministic structural eval for Business Semantic review fixtures."""

from __future__ import annotations

from pathlib import Path

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "business-semantic"
REVIEW_DIMENSIONS = {
    "hidden_rule_detection",
    "semantic_diff_detection",
    "memory_verdict",
    "golden_case_detection",
    "underroute_detection",
    "overrouting_avoidance",
}


def main() -> int:
    errors: list[str] = []
    cases = [load_yaml_file(path) for path in sorted(EVAL_DIR.glob("*.yaml"))]
    dimension_hits: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id", "unknown"))
        findings = case.get("expected_review_findings", [])
        if not isinstance(findings, list) or not findings:
            errors.append(f"{case_id}: expected_review_findings must be non-empty")
        forbidden = case.get("forbidden_behavior", [])
        if not isinstance(forbidden, list) or not forbidden:
            errors.append(f"{case_id}: forbidden_behavior must be non-empty")
        scoring = {str(item) for item in case.get("scoring", []) or []}
        dimension_hits.update(scoring & REVIEW_DIMENSIONS)
        if "business_semantic_pack_required" not in (case.get("expected_route") or {}):
            errors.append(f"{case_id}: missing BSP required/skip route decision")
    missing = REVIEW_DIMENSIONS - dimension_hits
    if missing:
        errors.append("review fixtures do not cover dimensions: " + ", ".join(sorted(missing)))
    if errors:
        return fail_many("eval-business-semantic-review", errors)
    print(
        "eval-business-semantic-review: OK "
        f"cases={len(cases)} dimensions={len(dimension_hits)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
