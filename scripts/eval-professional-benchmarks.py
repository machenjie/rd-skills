#!/usr/bin/env python3
"""Validate captured professional-skill benchmark deltas for Hookless skills.

The Markdown outputs are repository fixtures, not fresh model runs.  The report
therefore proves fixture quality and deterministic obligation coverage only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals/professional-benchmarks"
DEFAULT_REPORTS = ROOT / "reports"

LIST_FIELDS = (
    "expected_capabilities",
    "expected_hidden_risks",
    "expected_evidence",
    "forbidden_behaviors",
    "expected_output_obligations",
)
DECISION_OBLIGATION_FIELDS = (
    "expected_hidden_risks",
    "expected_evidence",
    "expected_output_obligations",
)
COVERAGE_CLASSES = {
    "standard",
    "release-critical",
    "adversarial-negative-control",
}


@dataclass
class CaseResult:
    case_id: str
    path: str
    expected_stage: str = ""
    primary_skill: str = ""
    layer3_skills: list[str] = field(default_factory=list)
    coverage_class: str = "standard"
    expected_status: str = "pass"
    schema_status: str = "fail"
    comparison_status: str = "not-run"
    baseline_score: int = 0
    with_skill_score: int = 0
    obligation_delta: int = 0
    covered_hidden_risks: list[str] = field(default_factory=list)
    covered_evidence: list[str] = field(default_factory=list)
    covered_output_obligations: list[str] = field(default_factory=list)
    baseline_forbidden_behavior_hits: list[str] = field(default_factory=list)
    forbidden_behavior_hits: list[str] = field(default_factory=list)
    detected_adversarial_defects: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    cases_dir = args.benchmarks_dir or DEFAULT_CASES
    reports_dir = args.reports_dir or DEFAULT_REPORTS
    try:
        payload = evaluate_benchmarks(cases_dir, args.mode)
    except ValidationProblem as exc:
        print(f"eval-professional-benchmarks: ERROR: {exc}", file=sys.stderr)
        return 1
    errors = payload["errors"]
    _write(
        reports_dir,
        payload,
        "all"
        if args.release_projection or args.format in {"all", "markdown"}
        else "json",
    )
    print(
        "eval-professional-benchmarks: "
        f"checked {payload['cases_checked']} cases; "
        f"comparisons={payload['comparison_cases_checked']}; "
        f"errors={len(errors)}; evidence=captured-fixture"
    )
    for error in errors:
        print(f"eval-professional-benchmarks: ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


def evaluate_benchmarks(
    cases_dir: Path = DEFAULT_CASES,
    mode: str = "auto",
) -> dict[str, Any]:
    """Evaluate all captured benchmark fixtures without writing reports."""

    professional, layer3, routable = _registries()
    case_dirs = sorted(path.parent for path in cases_dir.rglob("expected.yaml"))
    results = [_case(path, professional, layer3, routable, mode) for path in case_dirs]
    errors = [f"{row.path}: {message}" for row in results for message in row.errors]
    if len(results) < 10:
        errors.append(f"{_rel(cases_dir)}: expected at least 10 professional benchmark cases")
    return {
        "schema_version": 3,
        "architecture": "hookless-control-plane",
        "evaluation_kind": "captured-fixture-comparison",
        "evidence_limitations": [
            "baseline_output.md and with_skill_output.md are checked-in captured fixtures, not fresh model runs",
            "phrase coverage is deterministic and cannot establish live model accuracy",
            "no efficiency or adoption threshold is evaluated",
        ],
        "mode": mode,
        "cases_checked": len(results),
        "comparison_cases_checked": sum(
            row.comparison_status in {"pass", "expected-fail-detected"} for row in results
        ),
        "counts_by_coverage_class": {
            name: sum(row.coverage_class == name for row in results)
            for name in sorted(COVERAGE_CLASSES)
        },
        "errors": errors,
        "results": [asdict(row) for row in results],
    }


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmarks-dir", type=Path)
    parser.add_argument("--reports-dir", type=Path)
    parser.add_argument("--format", choices=("all", "markdown", "json"), default="json")
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--mode", choices=("auto", "schema-only", "comparison"), default="auto")
    parser.add_argument("--actual-output-dir", type=Path, help="deprecated; captured outputs live beside each case")
    return parser.parse_args(argv)


def _registries() -> tuple[dict[str, set[str]], set[str], set[str]]:
    professional_data = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
    foundation_data = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain_data = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    if not all(isinstance(item, dict) for item in (professional_data, foundation_data, domain_data)):
        raise ValidationProblem("three-layer Skill registries must be mappings")
    rows = professional_data.get("professional_skills", [])
    professional = {
        str(row.get("name", "")): set(_strings(row.get("layer3_candidates")))
        for row in rows
        if isinstance(row, dict)
    }
    routable = {
        str(row.get("name", ""))
        for row in rows
        if isinstance(row, dict) and bool(row.get("task_routable", True))
    }
    layer3 = {
        str(row.get("name", ""))
        for row in foundation_data.get("foundation_skills", [])
        if isinstance(row, dict)
    } | {
        str(row.get("name", ""))
        for row in domain_data.get("domain_skills", [])
        if isinstance(row, dict)
    }
    return professional, layer3, routable


def _case(
    directory: Path,
    professional: dict[str, set[str]],
    layer3: set[str],
    routable: set[str],
    mode: str,
) -> CaseResult:
    result = CaseResult(case_id=_rel(directory), path=_rel(directory))
    expected_path = directory / "expected.yaml"
    prompt_path = directory / "prompt.md"
    try:
        expected = load_yaml_file(expected_path)
    except ValidationProblem as exc:
        result.errors.append(str(exc))
        return result
    if not isinstance(expected, dict):
        result.errors.append("expected.yaml must be a mapping")
        return result
    prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else ""
    if len(prompt.strip()) < 40:
        result.errors.append("prompt.md must contain a concrete scenario")

    raw_stage = expected.get("expected_stage")
    if isinstance(raw_stage, str) and raw_stage.strip():
        result.expected_stage = raw_stage.strip()
    else:
        result.errors.append("expected_stage must be a non-blank string")
    result.primary_skill = str(expected.get("expected_professional_skill", "")).strip()
    result.layer3_skills = _strings(expected.get("expected_capabilities"))
    result.expected_status = str(
        expected.get("expected_with_skill_status", "pass")
    ).strip().casefold()
    if result.expected_status not in {"pass", "fail"}:
        result.errors.append("expected_with_skill_status must equal 'pass' or 'fail'")
    raw_coverage_class = expected.get("coverage_class")
    if raw_coverage_class is None:
        result.coverage_class = (
            "adversarial-negative-control"
            if result.expected_status == "fail"
            else "standard"
        )
    elif isinstance(raw_coverage_class, str):
        result.coverage_class = raw_coverage_class.strip().casefold()
    else:
        result.coverage_class = ""
    if result.coverage_class not in COVERAGE_CLASSES:
        result.errors.append(
            "coverage_class must equal standard, release-critical, or "
            "adversarial-negative-control"
        )
    if (
        result.coverage_class == "adversarial-negative-control"
        and result.expected_status != "fail"
    ):
        result.errors.append(
            "adversarial-negative-control requires expected_with_skill_status=fail"
        )
    if result.coverage_class != "adversarial-negative-control" and result.expected_status == "fail":
        result.errors.append(
            "expected_with_skill_status=fail requires adversarial-negative-control"
        )
    if result.primary_skill not in professional:
        result.errors.append(f"unknown primary Professional Skill '{result.primary_skill}'")
    elif result.primary_skill not in routable:
        result.errors.append(f"primary Professional Skill is not task-routable: '{result.primary_skill}'")
    if len(result.layer3_skills) > 3:
        result.errors.append("benchmark loads more than three Layer 3 Skills; narrow the risk surface")
    if len(result.layer3_skills) != len(set(result.layer3_skills)):
        result.errors.append("benchmark repeats a Layer 3 Skill")
    for name in result.layer3_skills:
        if name not in layer3:
            result.errors.append(f"unknown Layer 3 Skill '{name}'")
        elif result.primary_skill in professional and name not in professional[result.primary_skill]:
            result.errors.append(
                f"Layer 3 Skill '{name}' is not a candidate of primary Skill "
                f"'{result.primary_skill}'"
            )
    validated_lists: dict[str, list[str]] = {}
    normalized_lists: dict[str, list[str]] = {}
    for field in LIST_FIELDS:
        raw_values = expected.get(field)
        if (
            not isinstance(raw_values, list)
            or not raw_values
            or not all(isinstance(item, str) and item.strip() for item in raw_values)
        ):
            result.errors.append(f"{field} must be a non-empty list of non-blank strings")
            validated_lists[field] = []
            normalized_lists[field] = []
            continue
        values = [item.strip() for item in raw_values]
        normalized = [_fold(item) for item in values]
        if any(not item for item in normalized):
            result.errors.append(f"{field} contains an obligation with no searchable text")
        if len(normalized) != len(set(normalized)):
            result.errors.append(
                f"{field} must not repeat normalized obligations"
            )
        validated_lists[field] = values
        normalized_lists[field] = normalized

    obligation_origins: dict[str, str] = {}
    for field in DECISION_OBLIGATION_FIELDS:
        for obligation in normalized_lists[field]:
            previous = obligation_origins.get(obligation)
            if previous is not None:
                result.errors.append(
                    "decision obligations must be distinct across "
                    f"{previous} and {field}"
                )
            else:
                obligation_origins[obligation] = field
    if result.expected_status == "pass":
        forbidden = set(normalized_lists["forbidden_behaviors"])
        overlap = sorted(forbidden & set(obligation_origins))
        if overlap:
            result.errors.append(
                "positive benchmark forbidden behaviors must be distinct from "
                "required decision obligations"
            )

    if len(validated_lists["expected_hidden_risks"]) < 2:
        result.errors.append("expected_hidden_risks must name at least two concrete risks")
    if len(validated_lists["expected_evidence"]) < 2:
        result.errors.append("expected_evidence must name at least two concrete proof obligations")
    if len(validated_lists["forbidden_behaviors"]) < 2:
        result.errors.append("forbidden_behaviors must name at least two unsafe shortcuts")
    if len(validated_lists["expected_output_obligations"]) < 3:
        result.errors.append("expected_output_obligations must name at least three handoff obligations")
    result.schema_status = "pass" if not result.errors else "fail"
    if result.errors or mode == "schema-only":
        result.comparison_status = "schema-only"
        return result

    baseline_path = directory / "baseline_output.md"
    with_path = directory / "with_skill_output.md"
    if not baseline_path.is_file() or not with_path.is_file():
        if mode == "comparison":
            result.errors.append("comparison mode requires baseline_output.md and with_skill_output.md")
        result.comparison_status = "schema-only"
        return result
    baseline = baseline_path.read_text(encoding="utf-8")
    with_skill = with_path.read_text(encoding="utf-8")
    expected_groups = {
        "hidden": _strings(expected.get("expected_hidden_risks")),
        "evidence": _strings(expected.get("expected_evidence")),
        "output": _strings(expected.get("expected_output_obligations")),
    }
    baseline_hits = sum(_contains(baseline, item) for values in expected_groups.values() for item in values)
    result.baseline_forbidden_behavior_hits = [
        item
        for item in _strings(expected.get("forbidden_behaviors"))
        if _contains(baseline, item)
    ]
    result.covered_hidden_risks = [item for item in expected_groups["hidden"] if _contains(with_skill, item)]
    result.covered_evidence = [item for item in expected_groups["evidence"] if _contains(with_skill, item)]
    result.covered_output_obligations = [item for item in expected_groups["output"] if _contains(with_skill, item)]
    result.forbidden_behavior_hits = [
        item for item in _strings(expected.get("forbidden_behaviors")) if _contains(with_skill, item)
    ]
    result.baseline_score = baseline_hits
    result.with_skill_score = (
        len(result.covered_hidden_risks)
        + len(result.covered_evidence)
        + len(result.covered_output_obligations)
    )
    result.obligation_delta = result.with_skill_score - result.baseline_score
    comparison_errors: list[str] = []
    if not _contains(with_skill, result.primary_skill):
        comparison_errors.append("captured with-skill output does not name the selected primary Skill")
    missing_layer3 = [name for name in result.layer3_skills if not _contains(with_skill, name)]
    if missing_layer3:
        comparison_errors.append("captured with-skill output omits Layer 3 Skill(s): " + ", ".join(missing_layer3))
    if len(result.covered_hidden_risks) < 2:
        comparison_errors.append("captured output covers fewer than two expected hidden risks")
    if len(result.covered_evidence) < 2:
        comparison_errors.append("captured output covers fewer than two expected evidence obligations")
    if len(result.covered_output_obligations) < 2:
        comparison_errors.append("captured output covers fewer than two expected handoff obligations")
    if result.obligation_delta <= 0:
        comparison_errors.append("captured with-skill output has no positive obligation-coverage delta")
    if result.forbidden_behavior_hits:
        comparison_errors.append(
            "captured with-skill output contains forbidden behavior(s): "
            + ", ".join(result.forbidden_behavior_hits)
        )
    if result.coverage_class == "release-critical":
        if len(result.covered_hidden_risks) != len(expected_groups["hidden"]):
            comparison_errors.append(
                "release-critical output does not cover every expected hidden risk"
            )
        if len(result.covered_evidence) != len(expected_groups["evidence"]):
            comparison_errors.append(
                "release-critical output does not cover every expected evidence obligation"
            )
        if len(result.covered_output_obligations) != len(expected_groups["output"]):
            comparison_errors.append(
                "release-critical output does not cover every expected handoff obligation"
            )
        if not result.baseline_forbidden_behavior_hits:
            comparison_errors.append(
                "release-critical baseline must contain at least one forbidden behavior"
            )
    if result.expected_status == "fail":
        result.detected_adversarial_defects = comparison_errors
        if not comparison_errors:
            result.errors.append("adversarial captured output was incorrectly accepted")
            result.comparison_status = "fail"
        else:
            result.comparison_status = "expected-fail-detected"
    else:
        result.errors.extend(comparison_errors)
        result.comparison_status = "pass" if not comparison_errors else "fail"
    return result


def _contains(text: str, phrase: str) -> bool:
    return _fold(phrase) in _fold(text)


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _strings(value: Any) -> list[str]:
    return [str(item).strip() for item in value] if isinstance(value, list) else []


def _write(directory: Path, payload: dict[str, Any], report_format: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if report_format in {"all", "json"}:
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        (directory / "professional-benchmarks-report.json").write_text(text, encoding="utf-8")
        (directory / "professional-benchmarks-eval.json").write_text(text, encoding="utf-8")
    if report_format in {"all", "markdown"}:
        lines = [
            "# Hookless Professional Benchmarks",
            "",
            "> Checked-in captured outputs only; this report is not a fresh live-agent evaluation.",
            "",
            f"- Cases checked: {payload['cases_checked']}",
            f"- Captured comparisons passed: {payload['comparison_cases_checked']}",
            "- Release-critical cases: "
            f"{payload['counts_by_coverage_class']['release-critical']}",
            f"- Errors: {len(payload['errors'])}",
            "",
            "| Case | Class | Primary Skill | Layer 3 count | Baseline | With Skill | Delta | Status |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
        for row in payload["results"]:
            lines.append(
                f"| `{row['case_id']}` | {row['coverage_class']} | `{row['primary_skill']}` | "
                f"{len(row['layer3_skills'])} | "
                f"{row['baseline_score']} | {row['with_skill_score']} | {row['obligation_delta']} | "
                f"{row['comparison_status']} |"
            )
        if payload["errors"]:
            lines.extend(["", "## Errors", ""] + [f"- {item}" for item in payload["errors"]])
        text = "\n".join(lines) + "\n"
        (directory / "professional-benchmarks-report.md").write_text(text, encoding="utf-8")
        (directory / "professional-benchmarks-eval.md").write_text(text, encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
