#!/usr/bin/env python3
"""Evaluate runtime route activation precision against deterministic fixtures."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from validation_utils import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUNTIME_ROOT = ROOT / "src" / "hook-runtime" / "scripts"
DEFAULT_BUILT_RUNTIME_ROOT = ROOT / "dist" / "codex" / "project" / ".codex" / "hooks"
DEFAULT_FIXTURE_DIR = ROOT / "evals" / "activation"
DEFAULT_REPORT_MD = ROOT / "reports" / "activation-precision.md"
DEFAULT_REPORT_JSON = ROOT / "reports" / "activation-precision.json"
RUNTIME_MODULE_PREFIXES = ("changeforge_",)
RUNTIME_REQUIRED_FILES = (
    "changeforge_action_classifier.py",
    "changeforge_runtime_route_resolver.py",
)
RUNTIME_ROUTE_INDEX_NAME = "changeforge_runtime_route_index.json"
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
SET_FIELDS = (
    "selected_skills",
    "selected_capabilities",
    "required_references",
    "language_surfaces",
    "risk_surfaces",
    "product_surfaces",
    "selected_domain_extensions",
)
STAT_FIELDS = {
    "selected_skills",
    "selected_capabilities",
    "required_references",
}


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


@dataclass(frozen=True)
class RuntimeModules:
    """Runtime modules loaded from either source authoring files or built hooks."""

    mode: str
    runtime_root: Path
    classify_event: Callable[[dict], dict[str, Any]]
    build_active_skill_context: Callable[..., dict[str, Any]]


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


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _runtime_root(mode: str, runtime_root: Path | None = None) -> Path:
    if runtime_root is not None:
        root = runtime_root
        if (root / "scripts").is_dir() and not (root / "changeforge_action_classifier.py").is_file():
            return root / "scripts"
        return root
    if mode == "source":
        return SOURCE_RUNTIME_ROOT
    return DEFAULT_BUILT_RUNTIME_ROOT


def _clear_runtime_modules() -> None:
    for module_name in list(sys.modules):
        if module_name.startswith(RUNTIME_MODULE_PREFIXES):
            sys.modules.pop(module_name, None)


def _load_runtime_modules(mode: str, runtime_root: Path | None = None) -> RuntimeModules:
    root = _runtime_root(mode, runtime_root).resolve()
    if mode not in {"source", "built"}:
        raise ValueError(f"unsupported activation precision mode: {mode}")
    if not root.is_dir():
        raise FileNotFoundError(f"{root}: runtime root missing for {mode} mode")
    missing = [name for name in RUNTIME_REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"{root}: runtime files missing: {', '.join(missing)}")
    if mode == "built" and not (root / RUNTIME_ROUTE_INDEX_NAME).is_file():
        raise FileNotFoundError(f"{root / RUNTIME_ROUTE_INDEX_NAME}: built runtime route index missing")

    root_text = str(root)
    sys.path = [path for path in sys.path if path != root_text]
    sys.path.insert(0, root_text)
    _clear_runtime_modules()
    classifier = importlib.import_module("changeforge_action_classifier")
    resolver = importlib.import_module("changeforge_runtime_route_resolver")
    return RuntimeModules(
        mode=mode,
        runtime_root=root,
        classify_event=classifier.classify_event,
        build_active_skill_context=resolver.build_active_skill_context,
    )


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


def _actual_for_case(case: Mapping[str, Any], runtime_modules: RuntimeModules) -> dict[str, Any]:
    event = case.get("event")
    event = dict(event) if isinstance(event, Mapping) else {}
    state = case.get("state")
    state = dict(state) if isinstance(state, Mapping) else {}
    classification = runtime_modules.classify_event(event)
    context = runtime_modules.build_active_skill_context(
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
        "selected_domain_extensions": _unique_strings(context.get("selected_domain_extensions")),
        "context_budget_mode": str(context.get("context_budget_mode") or ""),
        "context_control": context.get("context_control") if isinstance(context.get("context_control"), dict) else {},
        "skipped_references": [
            str(item.get("reference"))
            for item in context.get("skipped_references", [])
            if isinstance(item, dict) and item.get("reference")
        ],
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


def _empty_summary() -> dict[str, Any]:
    return {
        "case_count": 0,
        "passed": 0,
        "failed": 0,
        "stage_accuracy": 0.0,
        "skill_precision": 0.0,
        "skill_recall": 0.0,
        "capability_precision": 0.0,
        "capability_recall": 0.0,
        "reference_precision": 0.0,
        "reference_recall": 0.0,
        "language_fp_rate": 0.0,
        "language_fn_rate": 0.0,
        "risk_surface_fp_rate": 0.0,
        "risk_surface_fn_rate": 0.0,
        "overroute_rate": 0.0,
        "metric_definitions": _metric_definitions(),
    }


def _metric_definitions() -> dict[str, str]:
    return {
        "precision_recall": "Set precision/recall aggregate true positives, false positives, and false negatives across exact-set cases.",
        "language_fp_rate": "Share of cases with at least one unexpected language surface.",
        "language_fn_rate": "Share of cases with at least one missing expected language surface.",
        "risk_surface_fp_rate": "Share of cases with at least one unexpected risk surface.",
        "risk_surface_fn_rate": "Share of cases with at least one missing expected risk surface.",
        "overroute_rate": "Share of cases with any unexpected exact-set value or any forbidden *_not_contains value.",
    }


def _claim_boundary(mode: str) -> str:
    if mode == "built":
        return (
            "Deterministic activation fixtures validate the built hook runtime resolver and its "
            "co-located generated route index for stage, skill, capability, reference, language, "
            "risk, and overroute cases. They are primary local runtime evidence, not live agent "
            "pass-rate or empirical performance proof."
        )
    return (
        "Deterministic activation fixtures validate source authoring resolver behavior as a smoke "
        "check. Source mode is not primary runtime evidence because installed hooks load the built "
        "resolver with a co-located generated route index."
    )


def evaluate_activation_precision(
    fixtures_dir: Path = DEFAULT_FIXTURE_DIR,
    *,
    mode: str = "built",
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    """Evaluate activation precision fixtures and return a machine-readable report."""
    fixture_cases, fixture_errors = _load_cases(fixtures_dir)
    try:
        runtime_modules = _load_runtime_modules(mode, runtime_root)
    except Exception as exc:
        resolved_root = _runtime_root(mode, runtime_root)
        return {
            "schema_version": 1,
            "generated_by": "scripts/eval-activation-precision.py",
            "mode": mode,
            "runtime_root": _display_path(resolved_root),
            "runtime_index": (
                _display_path(resolved_root / RUNTIME_ROUTE_INDEX_NAME)
                if mode == "built"
                else None
            ),
            "claim_boundary": _claim_boundary(mode),
            "status": "fail",
            "summary": _empty_summary(),
            "errors": [str(exc), *fixture_errors],
            "cases": [],
        }
    skill_stats = SetStats()
    capability_stats = SetStats()
    reference_stats = SetStats()
    stats_by_field = {
        "selected_skills": skill_stats,
        "selected_capabilities": capability_stats,
        "required_references": reference_stats,
    }
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
        actual = _actual_for_case(case, runtime_modules)
        case_errors: list[str] = []

        expected_stage = str(expected.get("stage") or "")
        stage_match = actual["stage"] == expected_stage
        if stage_match:
            stage_hits += 1
        else:
            case_errors.append(f"stage expected {expected_stage!r}, got {actual['stage']!r}")

        deltas: dict[str, dict[str, list[str]]] = {}
        for field in SET_FIELDS:
            exact_expected = field in expected
            expected_values = _unique_strings(expected.get(field)) if exact_expected else []
            actual_values = _unique_strings(actual.get(field))
            if exact_expected and field in STAT_FIELDS:
                stats_by_field[field].add(expected_values, actual_values)
            delta = _set_delta(expected_values, actual_values) if exact_expected else {"missing": [], "extra": []}
            contains_missing = sorted(
                set(_unique_strings(expected.get(f"{field}_contains"))) - set(actual_values)
            )
            forbidden_present = sorted(
                set(_unique_strings(expected.get(f"{field}_not_contains"))) & set(actual_values)
            )
            if contains_missing:
                delta["missing_contains"] = contains_missing
            if forbidden_present:
                delta["forbidden"] = forbidden_present
            deltas[field] = delta
            if delta["missing"]:
                case_errors.append(f"{field} missing: {', '.join(delta['missing'])}")
            if delta["extra"]:
                case_errors.append(f"{field} extra: {', '.join(delta['extra'])}")
            if contains_missing:
                case_errors.append(f"{field} required by contains missing: {', '.join(contains_missing)}")
            if forbidden_present:
                case_errors.append(f"{field} forbidden by not_contains present: {', '.join(forbidden_present)}")

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
                "selected_domain_extensions",
            )
        ) or any(deltas[field].get("forbidden") for field in SET_FIELDS):
            overroute_cases += 1

        expected_budget_mode = expected.get("context_budget_mode")
        if isinstance(expected_budget_mode, str) and expected_budget_mode:
            if actual.get("context_budget_mode") != expected_budget_mode:
                case_errors.append(
                    f"context_budget_mode expected {expected_budget_mode!r}, got {actual.get('context_budget_mode')!r}"
                )
        contains_missing = sorted(
            set(_unique_strings(expected.get("skipped_references_contains")))
            - set(_unique_strings(actual.get("skipped_references")))
        )
        forbidden_present = sorted(
            set(_unique_strings(expected.get("skipped_references_not_contains")))
            & set(_unique_strings(actual.get("skipped_references")))
        )
        if contains_missing:
            case_errors.append(f"skipped_references required by contains missing: {', '.join(contains_missing)}")
        if forbidden_present:
            case_errors.append(f"skipped_references forbidden by not_contains present: {', '.join(forbidden_present)}")
        if expected.get("context_control_required") is True and not actual.get("context_control"):
            case_errors.append("context_control required but missing")
        if "context_control_skipped_reference_min" in expected:
            minimum = int(expected.get("context_control_skipped_reference_min") or 0)
            control = actual.get("context_control") if isinstance(actual.get("context_control"), dict) else {}
            observed = int(control.get("skipped_reference_count") or 0)
            if observed < minimum:
                case_errors.append(
                    f"context_control skipped_reference_count expected >= {minimum}, got {observed}"
                )
        control = actual.get("context_control") if isinstance(actual.get("context_control"), dict) else {}
        for expected_key, control_key in (
            ("context_control_jit_required", "jit_retrieval_required"),
            ("context_control_tool_output_boundary_required", "tool_output_boundary_required"),
            ("context_control_compaction_snapshot_required", "compaction_snapshot_required"),
        ):
            if expected_key not in expected:
                continue
            expected_value = bool(expected.get(expected_key))
            observed_value = bool(control.get(control_key))
            if observed_value != expected_value:
                case_errors.append(
                    f"{control_key} expected {expected_value!r}, got {observed_value!r}"
                )

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
        "metric_definitions": _metric_definitions(),
    }
    missing_metrics = [metric for metric in REQUIRED_METRICS if metric not in summary]
    if missing_metrics:
        errors.append("missing summary metrics: " + ", ".join(missing_metrics))

    status = "fail" if errors else "pass"
    return {
        "schema_version": 1,
        "generated_by": "scripts/eval-activation-precision.py",
        "mode": mode,
        "runtime_root": _display_path(runtime_modules.runtime_root),
        "runtime_index": (
            _display_path(runtime_modules.runtime_root / RUNTIME_ROUTE_INDEX_NAME)
            if mode == "built"
            else None
        ),
        "claim_boundary": _claim_boundary(mode),
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
        f"- Mode: `{payload.get('mode', 'unknown')}`",
        f"- Runtime root: `{payload.get('runtime_root', 'unknown')}`",
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
    parser.add_argument("--mode", choices=("built", "source"), default="built")
    parser.add_argument(
        "--runtime-root",
        default=None,
        help="Runtime hook directory to import; defaults to dist/codex/project/.codex/hooks for built mode.",
    )
    parser.add_argument("--out", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--json-out", default=str(DEFAULT_REPORT_JSON))
    args = parser.parse_args(argv)

    payload = evaluate_activation_precision(
        Path(args.fixtures_dir),
        mode=args.mode,
        runtime_root=Path(args.runtime_root) if args.runtime_root else None,
    )
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
