#!/usr/bin/env python3
"""Evaluate runtime route activation precision against deterministic fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from validation_utils import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
HOOK_RUNTIME = ROOT / "src" / "hook-runtime" / "scripts"
if str(HOOK_RUNTIME) not in sys.path:
    sys.path.insert(0, str(HOOK_RUNTIME))

from changeforge_action_classifier import classify_event  # noqa: E402
from changeforge_runtime_route_resolver import build_active_skill_context  # noqa: E402


DEFAULT_FIXTURE_DIR = ROOT / "evals" / "activation"
DEFAULT_REPORT_MD = ROOT / "reports" / "activation-precision.md"
DEFAULT_REPORT_JSON = ROOT / "reports" / "activation-precision.json"
REQUIRED_METRICS = (
    "stage_accuracy",
    "skill_precision",
    "skill_recall",
    "capability_precision",
    "capability_recall",
    "reference_precision",
    "reference_recall",
    "language_fp_rate",
    "language_fn_rate",
    "risk_surface_fp_rate",
    "risk_surface_fn_rate",
    "overroute_rate",
)


@dataclass
class SetStats:
    """Aggregate precision/recall counters for one activation field."""

    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0

    def add(self, expected: Iterable[str], actual: Iterable[str]) -> None:
        expected_set = set(expected)
        actual_set = set(actual)
        self.true_positive += len(expected_set & actual_set)
        self.false_positive += len(actual_set - expected_set)
        self.false_negative += len(expected_set - actual_set)

    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return 1.0 if denominator == 0 else self.true_positive / denominator

    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return 1.0 if denominator == 0 else self.true_positive / denominator


def _unique_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        item = item.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _case_paths(fixtures_dir: Path) -> list[Path]:
    return sorted(path for path in fixtures_dir.glob("*.yaml") if path.is_file())


def _load_cases(fixtures_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    cases: list[dict[str, Any]] = []
    if not fixtures_dir.is_dir():
        return [], [f"{fixtures_dir}: activation fixture directory missing"]
    for path in _case_paths(fixtures_dir):
        loaded = load_yaml_file(path)
        if not isinstance(loaded, Mapping):
            errors.append(f"{path}: fixture file must be a mapping")
            continue
        raw_cases = loaded.get("cases")
        if not isinstance(raw_cases, list):
            errors.append(f"{path}: cases must be a list")
            continue
        for index, raw_case in enumerate(raw_cases, start=1):
            if not isinstance(raw_case, Mapping):
                errors.append(f"{path}: case {index} must be a mapping")
                continue
            case = dict(raw_case)
            try:
                case["_path"] = path.relative_to(ROOT).as_posix()
            except ValueError:
                case["_path"] = path.as_posix()
            cases.append(case)
    if not cases:
        errors.append(f"{fixtures_dir}: no activation cases found")
    return cases, errors


def _expected(case: Mapping[str, Any]) -> dict[str, Any]:
    raw_expected = case.get("expected")
    return dict(raw_expected) if isinstance(raw_expected, Mapping) else {}


def _actual_for_case(case: Mapping[str, Any]) -> dict[str, Any]:
    event = case.get("event")
    event = dict(event) if isinstance(event, Mapping) else {}
    state = case.get("state")
    state = dict(state) if isinstance(state, Mapping) else {}
    classification = classify_event(event)
    context = build_active_skill_context(
        runtime=str(case.get("runtime") or "codex"),
        stage=str(classification.get("stage") or ""),
        surfaces=_unique_strings(classification.get("product_surfaces") or []),
        event_name=str(event.get("hook_event_name") or event.get("hookEventName") or ""),
        state=state,
        classification=classification,
    )
    return {
        "stage": str(context.get("stage") or ""),
        "selected_skills": _unique_strings(context.get("selected_skills")),
        "selected_capabilities": _unique_strings(context.get("selected_capabilities")),
        "required_references": _unique_strings(context.get("required_references")),
        "language_surfaces": _unique_strings(context.get("language_surfaces")),
        "risk_surfaces": _unique_strings(context.get("risk_surfaces")),
        "product_surfaces": _unique_strings(context.get("product_surfaces")),
        "classification": classification,
    }


def _set_delta(expected: Iterable[str], actual: Iterable[str]) -> dict[str, list[str]]:
    expected_set = set(expected)
    actual_set = set(actual)
    return {
        "missing": sorted(expected_set - actual_set),
        "extra": sorted(actual_set - expected_set),
    }


def _rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 6)


def evaluate_activation_precision(fixtures_dir: Path = DEFAULT_FIXTURE_DIR) -> dict[str, Any]:
    """Evaluate activation precision fixtures and return a machine-readable report."""
    fixture_cases, fixture_errors = _load_cases(fixtures_dir)
    skill_stats = SetStats()
    capability_stats = SetStats()
    reference_stats = SetStats()
    total_cases = len(fixture_cases)
    stage_hits = 0
    language_fp_cases = 0
    language_fn_cases = 0
    risk_fp_cases = 0
    risk_fn_cases = 0
    overroute_cases = 0
    errors = list(fixture_errors)
    results: list[dict[str, Any]] = []

    for case in fixture_cases:
        case_id = str(case.get("id") or "unnamed-case")
        expected = _expected(case)
        actual = _actual_for_case(case)
        case_errors: list[str] = []

        expected_stage = str(expected.get("stage") or "")
        stage_match = actual["stage"] == expected_stage
        if stage_match:
            stage_hits += 1
        else:
            case_errors.append(f"stage expected {expected_stage!r}, got {actual['stage']!r}")

        deltas: dict[str, dict[str, list[str]]] = {}
        for field, stats in (
            ("selected_skills", skill_stats),
            ("selected_capabilities", capability_stats),
            ("required_references", reference_stats),
        ):
            expected_values = _unique_strings(expected.get(field))
            actual_values = _unique_strings(actual.get(field))
            stats.add(expected_values, actual_values)
            delta = _set_delta(expected_values, actual_values)
            deltas[field] = delta
            if delta["missing"]:
                case_errors.append(f"{field} missing: {', '.join(delta['missing'])}")
            if delta["extra"]:
                case_errors.append(f"{field} extra: {', '.join(delta['extra'])}")

        for field in ("language_surfaces", "risk_surfaces", "product_surfaces"):
            expected_values = _unique_strings(expected.get(field))
            actual_values = _unique_strings(actual.get(field))
            delta = _set_delta(expected_values, actual_values)
            deltas[field] = delta
            if delta["missing"]:
                case_errors.append(f"{field} missing: {', '.join(delta['missing'])}")
            if delta["extra"]:
                case_errors.append(f"{field} extra: {', '.join(delta['extra'])}")

        if deltas["language_surfaces"]["extra"]:
            language_fp_cases += 1
        if deltas["language_surfaces"]["missing"]:
            language_fn_cases += 1
        if deltas["risk_surfaces"]["extra"]:
            risk_fp_cases += 1
        if deltas["risk_surfaces"]["missing"]:
            risk_fn_cases += 1

        if any(
            deltas[field]["extra"]
            for field in (
                "selected_skills",
                "selected_capabilities",
                "required_references",
                "language_surfaces",
                "risk_surfaces",
                "product_surfaces",
            )
        ):
            overroute_cases += 1

        if case_errors:
            errors.extend(f"{case_id}: {error}" for error in case_errors)

        results.append(
            {
                "id": case_id,
                "path": case.get("_path"),
                "status": "fail" if case_errors else "pass",
                "expected": expected,
                "actual": {key: value for key, value in actual.items() if key != "classification"},
                "classification": actual["classification"],
                "deltas": deltas,
                "errors": case_errors,
            }
        )

    summary = {
        "case_count": total_cases,
        "passed": sum(1 for case in results if case["status"] == "pass"),
        "failed": sum(1 for case in results if case["status"] != "pass"),
        "stage_accuracy": _rate(stage_hits, total_cases),
        "skill_precision": round(skill_stats.precision(), 6),
        "skill_recall": round(skill_stats.recall(), 6),
        "capability_precision": round(capability_stats.precision(), 6),
        "capability_recall": round(capability_stats.recall(), 6),
        "reference_precision": round(reference_stats.precision(), 6),
        "reference_recall": round(reference_stats.recall(), 6),
        "language_fp_rate": _rate(language_fp_cases, total_cases),
        "language_fn_rate": _rate(language_fn_cases, total_cases),
        "risk_surface_fp_rate": _rate(risk_fp_cases, total_cases),
        "risk_surface_fn_rate": _rate(risk_fn_cases, total_cases),
        "overroute_rate": _rate(overroute_cases, total_cases),
        "metric_definitions": {
            "precision_recall": "Set precision/recall aggregate true positives, false positives, and false negatives across all cases.",
            "language_fp_rate": "Share of cases with at least one unexpected language surface.",
            "language_fn_rate": "Share of cases with at least one missing expected language surface.",
            "risk_surface_fp_rate": "Share of cases with at least one unexpected risk surface.",
            "risk_surface_fn_rate": "Share of cases with at least one missing expected risk surface.",
            "overroute_rate": "Share of cases with any unexpected skill, capability, reference, product surface, language surface, or risk surface.",
        },
    }
    missing_metrics = [metric for metric in REQUIRED_METRICS if metric not in summary]
    if missing_metrics:
        errors.append("missing summary metrics: " + ", ".join(missing_metrics))

    status = "fail" if errors else "pass"
    return {
        "schema_version": 1,
        "generated_by": "scripts/eval-activation-precision.py",
        "claim_boundary": (
            "Deterministic activation fixtures validate route precision/recall for selected stage, "
            "skill, capability, reference, language, risk, and overroute cases. They are not live "
            "agent pass-rate or empirical performance proof."
        ),
        "status": status,
        "summary": summary,
        "errors": errors,
        "cases": results,
    }


def render_markdown(payload: Mapping[str, Any]) -> str:
    """Render a human-readable activation precision report."""
    summary = payload["summary"]
    lines = [
        "# Activation Precision Evaluation",
        "",
        "This generated report uses deterministic route activation fixtures. It measures resolver precision/recall for staged loading decisions; it is not live runtime pass-rate evidence.",
        "",
        "## Summary",
        "",
        f"- Status: `{payload['status']}`",
        f"- Cases: {summary['case_count']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for metric in REQUIRED_METRICS:
        lines.append(f"| `{metric}` | `{summary[metric]}` |")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Status | Stage | Product Surfaces | Languages | Risks |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case in payload["cases"]:
        actual = case["actual"]
        lines.append(
            f"| `{case['id']}` | `{case['status']}` | `{actual['stage']}` | "
            f"{', '.join(actual['product_surfaces']) or 'none'} | "
            f"{', '.join(actual['language_surfaces']) or 'none'} | "
            f"{', '.join(actual['risk_surfaces']) or 'none'} |"
        )
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in payload["errors"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for writing activation precision reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURE_DIR))
    parser.add_argument("--out", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--json-out", default=str(DEFAULT_REPORT_JSON))
    args = parser.parse_args(argv)

    payload = evaluate_activation_precision(Path(args.fixtures_dir))
    out = Path(args.out)
    json_out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(payload), encoding="utf-8")
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote activation precision eval to {out} and {json_out}")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
