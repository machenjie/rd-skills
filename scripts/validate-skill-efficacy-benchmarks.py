#!/usr/bin/env python3
"""Validate ChangeForge skill efficacy benchmark definitions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from validation_utils import (
    NAME_RE,
    ValidationProblem,
    fail_many,
    load_yaml_file,
    registry_items,
    relpath,
    validate_no_personal_references,
)


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = ROOT / "evals" / "skill-efficacy"
REGISTRY_PATH = ROOT / "src" / "registry" / "capabilities.yaml"

VALID_RISK_LEVELS = {"L1", "L2", "L3", "L4", "L5"}
VALID_VERDICTS = {
    "structural_pass",
    "measured_pass",
    "inconclusive",
    "blocked",
}
VALID_CHANGED_SURFACES = {
    "skill",
    "capability",
    "router",
    "hook",
    "memory",
    "graph",
    "validation",
    "trajectory",
    "adapter",
    "docs-only",
}
BEHAVIOR_SURFACES = VALID_CHANGED_SURFACES - {"docs-only"}
VALID_TOKEN_BUDGET_MODES = {"minimal", "single-stage", "staged-plan", "full"}
REQUIRED_ROOT_FIELDS = (
    "id",
    "capability",
    "task",
    "baseline",
    "treatment",
    "metrics",
    "skill_efficacy_benchmark",
    "verdict",
)
REQUIRED_RUN_FIELDS = (
    "description",
    "selected_capabilities",
    "token_cost",
    "turn_count",
)


def _load_capability_names(errors: list[str]) -> set[str]:
    try:
        loaded = load_yaml_file(REGISTRY_PATH)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return set()
    names: set[str] = set()
    for entry in registry_items(loaded, "capabilities", REGISTRY_PATH, errors):
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            names.add(entry["name"])
    return names


def _as_string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        values.append(item.strip())
    return values


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_required_mapping(
    block: dict[str, Any],
    required: tuple[str, ...],
    label: str,
    rel: str,
    errors: list[str],
) -> None:
    for field in required:
        if field not in block:
            errors.append(f"{rel}: {label}.{field} is required")


def _invalid_reference_selector(value: str) -> bool:
    folded = value.casefold().strip()
    return folded in {"*", "all", "all references", "every reference"} or "all references" in folded


def _validate_skipped_references(value: Any, rel: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{rel}: skill_efficacy_benchmark.treatment_case.skipped_references must be a list")
        return
    for index, item in enumerate(value):
        label = f"{rel}: skill_efficacy_benchmark.treatment_case.skipped_references[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping with reference and reason")
            continue
        if not _non_empty_string(item.get("reference")):
            errors.append(f"{label}.reference is required")
        if not _non_empty_string(item.get("reason")):
            errors.append(f"{label}.reason is required")


def _validate_plan_string_list(
    value: Any,
    label: str,
    rel: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
    reject_all_references: bool = False,
) -> list[str]:
    values = _as_string_list(value)
    if values is None or (not allow_empty and not values):
        errors.append(f"{rel}: {label} must be a {'possibly empty ' if allow_empty else ''}string list")
        return []
    if reject_all_references:
        for item in values:
            if _invalid_reference_selector(item):
                errors.append(f"{rel}: {label} must be an explicit allow-list, not '{item}'")
    return values


def _cost_value_is_valid(value: Any) -> bool:
    if value == "not_collected":
        return True
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _validate_run_block(
    data: dict[str, Any],
    field: str,
    rel: str,
    capabilities: set[str],
    errors: list[str],
) -> list[str]:
    block = data.get(field)
    if not isinstance(block, dict):
        errors.append(f"{rel}: '{field}' must be a mapping")
        return []

    for required in REQUIRED_RUN_FIELDS:
        if required not in block:
            errors.append(f"{rel}: {field}.{required} is required")

    description = block.get("description")
    if not isinstance(description, str) or len(description.strip()) < 40:
        errors.append(f"{rel}: {field}.description must be a specific sentence")

    selected = _as_string_list(block.get("selected_capabilities"))
    if selected is None or not selected:
        errors.append(f"{rel}: {field}.selected_capabilities must be a non-empty string list")
        selected = []
    for capability in selected:
        if capability not in capabilities:
            errors.append(
                f"{rel}: {field}.selected_capabilities contains unknown capability '{capability}'"
            )

    for cost_field in ("token_cost", "turn_count"):
        if not _cost_value_is_valid(block.get(cost_field)):
            errors.append(
                f"{rel}: {field}.{cost_field} must be a non-negative number or 'not_collected'"
            )

    return selected


def _validate_metrics(
    data: dict[str, Any],
    rel: str,
    errors: list[str],
) -> None:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{rel}: 'metrics' must be a mapping")
        return

    behavior_delta = _as_string_list(metrics.get("behavior_delta"))
    if behavior_delta is None or len(behavior_delta) < 2:
        errors.append(f"{rel}: metrics.behavior_delta must contain at least two strings")

    for field in ("token_overhead_pct", "turn_overhead_pct"):
        if field not in metrics:
            errors.append(f"{rel}: metrics.{field} is required")
        elif not _cost_value_is_valid(metrics.get(field)):
            errors.append(f"{rel}: metrics.{field} must be a non-negative number or 'not_collected'")


def _validate_benchmark_plan(
    data: dict[str, Any],
    rel: str,
    capabilities: set[str],
    errors: list[str],
) -> None:
    plan = data.get("skill_efficacy_benchmark")
    if not isinstance(plan, dict):
        errors.append(f"{rel}: 'skill_efficacy_benchmark' must be a mapping")
        return

    _validate_required_mapping(
        plan,
        ("changed_surface", "baseline_case", "treatment_case", "metrics", "regression_commands", "caveats"),
        "skill_efficacy_benchmark",
        rel,
        errors,
    )

    changed_surface = plan.get("changed_surface")
    if changed_surface not in VALID_CHANGED_SURFACES:
        errors.append(
            f"{rel}: skill_efficacy_benchmark.changed_surface must be one of {sorted(VALID_CHANGED_SURFACES)}"
        )
    if changed_surface == "docs-only":
        caveats = _as_string_list(plan.get("caveats")) or []
        if not any("no behavior impact" in caveat.casefold() for caveat in caveats):
            errors.append(
                f"{rel}: docs-only benchmark plan must explain no behavior impact in caveats"
            )
    elif changed_surface not in BEHAVIOR_SURFACES:
        errors.append(
            f"{rel}: skill_efficacy_benchmark.changed_surface cannot be docs-only or unknown for behavior fixtures"
        )

    baseline = plan.get("baseline_case")
    if not isinstance(baseline, dict):
        errors.append(f"{rel}: skill_efficacy_benchmark.baseline_case must be a mapping")
    else:
        _validate_required_mapping(
            baseline,
            ("task", "expected_current_behavior", "known_gap"),
            "skill_efficacy_benchmark.baseline_case",
            rel,
            errors,
        )
        for field in ("task", "expected_current_behavior", "known_gap"):
            if field in baseline and not _non_empty_string(baseline.get(field)):
                errors.append(f"{rel}: skill_efficacy_benchmark.baseline_case.{field} must be a non-empty string")

    treatment = plan.get("treatment_case")
    required_references: list[str] = []
    if not isinstance(treatment, dict):
        errors.append(f"{rel}: skill_efficacy_benchmark.treatment_case must be a mapping")
    else:
        _validate_required_mapping(
            treatment,
            (
                "expected_new_behavior",
                "selected_skills",
                "selected_capabilities",
                "required_references",
                "skipped_references",
            ),
            "skill_efficacy_benchmark.treatment_case",
            rel,
            errors,
        )
        if "expected_new_behavior" in treatment and not _non_empty_string(treatment.get("expected_new_behavior")):
            errors.append(
                f"{rel}: skill_efficacy_benchmark.treatment_case.expected_new_behavior must be a non-empty string"
            )
        _validate_plan_string_list(
            treatment.get("selected_skills"),
            "skill_efficacy_benchmark.treatment_case.selected_skills",
            rel,
            errors,
        )
        selected_capabilities = _validate_plan_string_list(
            treatment.get("selected_capabilities"),
            "skill_efficacy_benchmark.treatment_case.selected_capabilities",
            rel,
            errors,
        )
        for capability in selected_capabilities:
            if capability not in capabilities:
                errors.append(
                    f"{rel}: skill_efficacy_benchmark.treatment_case.selected_capabilities contains unknown capability '{capability}'"
                )
        required_references = _validate_plan_string_list(
            treatment.get("required_references"),
            "skill_efficacy_benchmark.treatment_case.required_references",
            rel,
            errors,
            reject_all_references=True,
        )
        _validate_skipped_references(treatment.get("skipped_references"), rel, errors)

    plan_metrics = plan.get("metrics")
    if not isinstance(plan_metrics, dict):
        errors.append(f"{rel}: skill_efficacy_benchmark.metrics must be a mapping")
    else:
        _validate_required_mapping(
            plan_metrics,
            (
                "over_routing",
                "under_routing",
                "selected_reference_count",
                "token_budget_mode",
                "turn_overhead",
                "closure_evidence_required",
            ),
            "skill_efficacy_benchmark.metrics",
            rel,
            errors,
        )
        for field in ("over_routing", "under_routing"):
            if field in plan_metrics and not _non_empty_string(plan_metrics.get(field)):
                errors.append(f"{rel}: skill_efficacy_benchmark.metrics.{field} must be an explicit judgment string")
        selected_reference_count = plan_metrics.get("selected_reference_count")
        if not isinstance(selected_reference_count, int) or selected_reference_count < 0:
            errors.append(
                f"{rel}: skill_efficacy_benchmark.metrics.selected_reference_count must be a non-negative integer"
            )
        elif selected_reference_count != len(required_references):
            errors.append(
                f"{rel}: skill_efficacy_benchmark.metrics.selected_reference_count must equal required_references count"
            )
        token_budget_mode = plan_metrics.get("token_budget_mode")
        if token_budget_mode not in VALID_TOKEN_BUDGET_MODES:
            errors.append(
                f"{rel}: skill_efficacy_benchmark.metrics.token_budget_mode must be one of {sorted(VALID_TOKEN_BUDGET_MODES)}"
            )
        if "turn_overhead" in plan_metrics and not (
            _cost_value_is_valid(plan_metrics.get("turn_overhead"))
            or _non_empty_string(plan_metrics.get("turn_overhead"))
        ):
            errors.append(
                f"{rel}: skill_efficacy_benchmark.metrics.turn_overhead must be a number, 'not_collected', or an explicit string"
            )
        if "closure_evidence_required" in plan_metrics and not isinstance(
            plan_metrics.get("closure_evidence_required"), (bool, list, str)
        ):
            errors.append(
                f"{rel}: skill_efficacy_benchmark.metrics.closure_evidence_required must be boolean, list, or string"
            )

    regression_commands = _validate_plan_string_list(
        plan.get("regression_commands"),
        "skill_efficacy_benchmark.regression_commands",
        rel,
        errors,
    )
    for command in regression_commands:
        if not command.startswith(("python ", "python3 ", "bash ", "scripts/")):
            errors.append(
                f"{rel}: skill_efficacy_benchmark.regression_commands contains non-reproducible command '{command}'"
            )
    _validate_plan_string_list(plan.get("caveats"), "skill_efficacy_benchmark.caveats", rel, errors)


def _all_costs_collected(data: dict[str, Any]) -> bool:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return False
    run_blocks = [data.get("baseline"), data.get("treatment")]
    for block in run_blocks:
        if not isinstance(block, dict):
            return False
        if block.get("token_cost") == "not_collected":
            return False
        if block.get("turn_count") == "not_collected":
            return False
    return (
        metrics.get("token_overhead_pct") != "not_collected"
        and metrics.get("turn_overhead_pct") != "not_collected"
    )


def _validate_verdict(data: dict[str, Any], rel: str, errors: list[str]) -> None:
    verdict = data.get("verdict")
    if not isinstance(verdict, dict):
        errors.append(f"{rel}: 'verdict' must be a mapping")
        return
    status = verdict.get("status")
    if status not in VALID_VERDICTS:
        errors.append(f"{rel}: verdict.status must be one of {sorted(VALID_VERDICTS)}")
    rationale = verdict.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < 40:
        errors.append(f"{rel}: verdict.rationale must explain the evidence limits")
    if status == "measured_pass" and not _all_costs_collected(data):
        errors.append(f"{rel}: measured_pass requires numeric baseline, treatment, and overhead data")


def _validate_benchmark(path: Path, capabilities: set[str], errors: list[str]) -> None:
    rel = relpath(ROOT, path)
    if not NAME_RE.fullmatch(path.stem):
        errors.append(f"{rel}: benchmark filename must be lowercase kebab-case")

    text = path.read_text(encoding="utf-8")
    validate_no_personal_references(text, rel, errors)

    try:
        data = load_yaml_file(path)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return
    if not isinstance(data, dict):
        errors.append(f"{rel}: benchmark must be a mapping")
        return

    for field in REQUIRED_ROOT_FIELDS:
        if field not in data:
            errors.append(f"{rel}: '{field}' is required")

    if data.get("id") != path.stem:
        errors.append(f"{rel}: id must match filename stem")
    if data.get("risk_level") is not None and data.get("risk_level") not in VALID_RISK_LEVELS:
        errors.append(f"{rel}: risk_level must be one of {sorted(VALID_RISK_LEVELS)}")

    capability = data.get("capability")
    if not isinstance(capability, str) or capability not in capabilities:
        errors.append(f"{rel}: capability must reference a capability in src/registry/capabilities.yaml")
        capability = ""

    _validate_run_block(data, "baseline", rel, capabilities, errors)
    treatment_capabilities = _validate_run_block(data, "treatment", rel, capabilities, errors)
    if capability and capability not in treatment_capabilities:
        errors.append(f"{rel}: treatment.selected_capabilities must include '{capability}'")

    _validate_metrics(data, rel, errors)
    _validate_benchmark_plan(data, rel, capabilities, errors)
    _validate_verdict(data, rel, errors)


def main() -> int:
    """Validate all skill efficacy benchmark definitions."""
    errors: list[str] = []
    if not BENCHMARK_DIR.is_dir():
        print("validate-skill-efficacy-benchmarks: missing evals/skill-efficacy directory.", file=sys.stderr)
        return 1

    capabilities = _load_capability_names(errors)
    benchmark_paths = sorted(BENCHMARK_DIR.glob("*.yaml"))
    if len(benchmark_paths) < 3:
        errors.append("evals/skill-efficacy: expected at least 3 benchmark YAML files")

    for path in benchmark_paths:
        _validate_benchmark(path, capabilities, errors)

    readme = BENCHMARK_DIR / "README.md"
    if not readme.is_file():
        errors.append("evals/skill-efficacy/README.md: missing benchmark README")
    else:
        validate_no_personal_references(readme.read_text(encoding="utf-8"), relpath(ROOT, readme), errors)

    if errors:
        return fail_many("validate-skill-efficacy-benchmarks", errors)

    print(f"validate-skill-efficacy-benchmarks: validated {len(benchmark_paths)} benchmark(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
