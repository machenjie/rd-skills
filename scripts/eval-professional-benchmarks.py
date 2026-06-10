#!/usr/bin/env python3
"""Validate offline professional benchmark case specifications and fixtures.

Benchmarks under evals/professional-benchmarks/ are schema fixtures for
professional engineering behavior. This script validates fixture structure,
registry references, and optional baseline-vs-with-skill captured outputs. It
does not call an LLM, access the network, or mutate benchmark sources.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from telemetry_utils import load_registry_names
from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
ROUTING_RULES = REGISTRY_DIR / "routing-rules.yaml"
DEFAULT_BENCHMARKS_DIR = ROOT / "evals" / "professional-benchmarks"
DEFAULT_REPORTS_DIR = ROOT / "reports"
MARKDOWN_REPORT = "professional-benchmarks-eval.md"
JSON_REPORT = "professional-benchmarks-eval.json"
PRIMARY_MARKDOWN_REPORT = "professional-benchmarks-report.md"
PRIMARY_JSON_REPORT = "professional-benchmarks-report.json"

REQUIRED_EXPECTED_FIELDS = (
    "expected_stage",
    "expected_professional_skill",
    "expected_capabilities",
    "expected_hidden_risks",
    "expected_evidence",
    "forbidden_behaviors",
    "expected_output_obligations",
)
REQUIRED_LIST_FIELDS = (
    "expected_capabilities",
    "expected_hidden_risks",
    "expected_evidence",
    "forbidden_behaviors",
    "expected_output_obligations",
)

MIN_LIST_COUNTS = {
    "expected_capabilities": 1,
    "expected_hidden_risks": 2,
    "expected_evidence": 2,
    "forbidden_behaviors": 2,
    "expected_output_obligations": 3,
}

GENERIC_EXPECTED_PHRASES = (
    "add tests",
    "check security",
    "do validation",
    "ensure quality",
    "handle errors",
    "make it robust",
    "review code",
    "run tests",
    "use best practices",
)


@dataclass
class ProfessionalDeltaSummary:
    baseline_missing: list[str] = field(default_factory=list)
    with_skill_present: list[str] = field(default_factory=list)
    remaining_gaps: list[str] = field(default_factory=list)
    forbidden_behavior_hits: list[str] = field(default_factory=list)
    delta_score: int = 0
    note: str = "deterministic rule heuristic; not an LLM judge"


@dataclass
class BenchmarkResult:
    case_id: str
    path: str
    expected_stage: str = ""
    expected_skills: list[str] = field(default_factory=list)
    expected_capabilities: list[str] = field(default_factory=list)
    expected_with_skill_status: str = "pass"
    adversarial_detection_status: str = "not-applicable"
    schema_status: str = "not-run"
    comparison_status: str = "schema-only"
    benchmark_quality_status: str = "not-run"
    baseline_defect_hits: list[str] = field(default_factory=list)
    with_skill_obligation_coverage: list[str] = field(default_factory=list)
    delta_score: int = 0
    remaining_gaps: list[str] = field(default_factory=list)
    missing_expected_items: list[str] = field(default_factory=list)
    forbidden_behavior_hits: list[str] = field(default_factory=list)
    professional_delta_summary: ProfessionalDeltaSummary = field(default_factory=ProfessionalDeltaSummary)
    errors: list[str] = field(default_factory=list)
    comparison: "ComparisonResult | None" = None

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class BenchmarkReport:
    generated_at: str
    cases_checked: int
    mode: str
    errors: list[str]
    results: list[BenchmarkResult]
    comparison_cases_checked: int = 0
    actual_output_comparison: str = (
        "deterministic rule heuristic; auto mode compares baseline_output.md "
        "and with_skill_output.md when both exist"
    )


@dataclass
class OutputCoverage:
    selected_stage: bool = False
    selected_professional_skill: bool = False
    selected_capabilities: bool = False
    expected_hidden_risks: bool = False
    forbidden_behaviors_absent: bool = False
    expected_evidence: bool = False
    expected_output_obligations: bool = False
    inspected_boundaries: bool = False
    evidence_limits: bool = False
    residual_risk: bool = False
    residual_risk_owner: bool = False
    next_gate: bool = False
    validation_or_not_verified: bool = False
    validation_outcome: bool = False
    route_relevance: bool = False
    score: int = 0
    matched_hidden_risks: list[str] = field(default_factory=list)
    matched_evidence: list[str] = field(default_factory=list)
    matched_obligations: list[str] = field(default_factory=list)
    forbidden_hits: list[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    mode: str
    baseline_path: str = ""
    with_skill_path: str = ""
    baseline_score: int = 0
    with_skill_score: int = 0
    improvement: int = 0
    baseline_defect_hits: list[str] = field(default_factory=list)
    baseline_coverage: OutputCoverage | None = None
    with_skill_coverage: OutputCoverage | None = None
    errors: list[str] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    benchmarks_dir = args.benchmarks_dir or DEFAULT_BENCHMARKS_DIR
    reports_dir = args.reports_dir or DEFAULT_REPORTS_DIR

    registry = load_registry_names(REGISTRY_DIR)
    stages = _stage_names()
    case_dirs = _collect_case_dirs(benchmarks_dir)
    results = [_evaluate_case(path, registry, stages, args.mode) for path in case_dirs]
    errors = [f"{result.path}: {error}" for result in results for error in result.errors]
    if len(case_dirs) < 10:
        errors.append(
            f"{_rel(benchmarks_dir)}: expected at least 10 benchmark cases, found {len(case_dirs)}"
        )
    comparison_count = sum(
        1 for result in results if result.comparison and result.comparison.mode == "comparison"
    )
    if args.mode == "comparison" and comparison_count == 0:
        errors.append("comparison mode requires at least one case with baseline_output.md and with_skill_output.md")
    if args.actual_output_dir is not None:
        if not args.actual_output_dir.exists():
            errors.append(f"{_rel(args.actual_output_dir)}: actual output directory does not exist")

    report = BenchmarkReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        cases_checked=len(case_dirs),
        mode=args.mode,
        errors=errors,
        results=results,
        comparison_cases_checked=comparison_count,
    )
    written = _write_reports(report, reports_dir, args.format)
    print(f"eval-professional-benchmarks: checked {len(case_dirs)} case(s); errors={len(errors)}")
    for path in written:
        print(f"- report: {path}")
    if errors:
        for error in errors:
            print(f"eval-professional-benchmarks: ERROR: {error}", file=sys.stderr)
        return 1
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmarks-dir", type=Path, default=None)
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument(
        "--format",
        choices=("all", "markdown", "json"),
        default="all",
        help="report format to write; default writes both Markdown and JSON",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "schema-only", "comparison"),
        default="auto",
        help=(
            "schema-only validates case structure; comparison compares cases with "
            "baseline_output.md and with_skill_output.md; auto compares only cases with both files"
        ),
    )
    parser.add_argument(
        "--actual-output-dir",
        type=Path,
        default=None,
        help="deprecated compatibility option; comparison fixtures live beside each case",
    )
    return parser.parse_args(argv)


def _collect_case_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path.parent
        for path in root.rglob("expected.yaml")
        if path.is_file() and (path.parent / "prompt.md").is_file()
    )


def _evaluate_case(
    case_dir: Path,
    registry: dict[str, set[str]],
    stages: set[str],
    mode: str,
) -> BenchmarkResult:
    result = BenchmarkResult(_rel(case_dir), _rel(case_dir))
    prompt_path = case_dir / "prompt.md"
    expected_path = case_dir / "expected.yaml"
    if not prompt_path.is_file():
        result.errors.append("missing prompt.md")
    if not expected_path.is_file():
        result.errors.append("missing expected.yaml")
        return result

    prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else ""
    if len(prompt.strip()) < 40:
        result.errors.append("prompt.md must contain a concrete scenario prompt")
    if _contains_forbidden_scope(prompt):
        result.errors.append("prompt.md contains forbidden non-professional scope")

    try:
        data = load_yaml_file(expected_path)
    except ValidationProblem as exc:
        result.errors.append(str(exc))
        return result
    if not isinstance(data, dict):
        result.errors.append("expected.yaml must be a mapping")
        return result

    for field_name in REQUIRED_EXPECTED_FIELDS:
        if field_name not in data:
            result.errors.append(f"missing required field '{field_name}'")

    result.expected_stage = _string(data.get("expected_stage"))
    result.expected_skills = _string_list(data.get("expected_professional_skill"))
    result.expected_capabilities = _string_list(data.get("expected_capabilities"))
    result.expected_with_skill_status = _string(data.get("expected_with_skill_status")) or "pass"
    if result.expected_with_skill_status not in {"pass", "fail"}:
        result.errors.append("expected_with_skill_status must be pass or fail")

    if not result.expected_stage:
        result.errors.append("expected_stage must be non-empty")
    elif stages and result.expected_stage not in stages:
        result.errors.append(f"unknown expected_stage '{result.expected_stage}'")

    if not result.expected_skills:
        result.errors.append("expected_professional_skill must include at least one skill")
    for skill in result.expected_skills:
        if skill not in registry["skills"]:
            result.errors.append(f"unknown professional skill '{skill}'")

    if not result.expected_capabilities:
        result.errors.append("expected_capabilities must include at least one capability")
    for capability in result.expected_capabilities:
        if capability not in registry["capabilities"]:
            result.errors.append(f"unknown capability '{capability}'")

    for field_name in REQUIRED_LIST_FIELDS:
        values = _string_list(data.get(field_name))
        if not values:
            result.errors.append(f"{field_name} must be a non-empty list")
            continue
        minimum = MIN_LIST_COUNTS[field_name]
        if len(values) < minimum:
            result.errors.append(
                f"{field_name} must include at least {minimum} concrete item(s)"
            )
        vague_values = (
            field_name != "expected_capabilities"
            and any(_looks_vague_expected_item(value) for value in values)
        )
        if any(_looks_placeholder(value) for value in values) or vague_values:
            result.errors.append(f"{field_name} contains placeholder or vague content")

    obligations = _string_list(data.get("expected_output_obligations"))
    if not any("evidence" in item.casefold() or "validation" in item.casefold() for item in obligations):
        result.errors.append("expected_output_obligations must include at least one evidence or validation obligation")

    schema_errors = list(result.errors)
    result.schema_status = "pass" if not schema_errors else "fail"
    result.comparison = _evaluate_comparison(case_dir, data, result, mode, registry)
    result.comparison_status = _comparison_status(result.comparison)
    result.missing_expected_items = _missing_expected_items(data, result, schema_errors)
    result.forbidden_behavior_hits = _forbidden_behavior_hits(result.comparison)
    result.professional_delta_summary = _professional_delta_summary(
        result.comparison,
        result.missing_expected_items,
        result.forbidden_behavior_hits,
    )
    comparison_errors = list(result.comparison.errors)
    if result.expected_with_skill_status == "fail" and result.comparison.mode == "comparison":
        if comparison_errors:
            result.adversarial_detection_status = "detected"
            result.comparison_status = "expected-fail"
            comparison_errors = []
        else:
            result.adversarial_detection_status = "missed"
            comparison_errors.append("adversarial with_skill_output.md unexpectedly passed")
    elif result.expected_with_skill_status == "fail":
        result.adversarial_detection_status = "missing-comparison"
        comparison_errors.append("adversarial benchmark requires paired baseline_output.md and with_skill_output.md")
    else:
        result.adversarial_detection_status = "not-applicable"
    result.errors.extend(comparison_errors)
    result.baseline_defect_hits = _baseline_defect_hits(result.comparison)
    result.with_skill_obligation_coverage = _with_skill_obligation_coverage(result.comparison)
    result.delta_score = result.professional_delta_summary.delta_score
    result.remaining_gaps = list(result.professional_delta_summary.remaining_gaps)
    result.benchmark_quality_status = "pass" if not result.errors else "fail"

    return result


def _evaluate_comparison(
    case_dir: Path,
    expected: dict[str, Any],
    schema_result: BenchmarkResult,
    mode: str,
    registry: dict[str, set[str]],
) -> ComparisonResult:
    baseline_path = case_dir / "baseline_output.md"
    with_skill_path = case_dir / "with_skill_output.md"
    has_pair = baseline_path.is_file() and with_skill_path.is_file()
    comparison = ComparisonResult(mode="schema-only")
    if mode == "schema-only":
        return comparison
    if not has_pair:
        comparison.mode = "missing-pair"
        if not baseline_path.is_file():
            comparison.errors.append("missing baseline_output.md")
        if not with_skill_path.is_file():
            comparison.errors.append("missing with_skill_output.md")
        return comparison

    comparison.mode = "comparison"
    comparison.baseline_path = _rel(baseline_path)
    comparison.with_skill_path = _rel(with_skill_path)
    baseline_text = baseline_path.read_text(encoding="utf-8")
    with_skill_text = with_skill_path.read_text(encoding="utf-8")
    if len(baseline_text.strip()) < 40:
        comparison.errors.append("baseline_output.md must contain a concrete simulated output")
    if len(with_skill_text.strip()) < 80:
        comparison.errors.append("with_skill_output.md must contain a concrete simulated output")

    baseline = _coverage_for_output(baseline_text, expected, schema_result, registry)
    with_skill = _coverage_for_output(with_skill_text, expected, schema_result, registry)
    comparison.baseline_coverage = baseline
    comparison.with_skill_coverage = with_skill
    comparison.baseline_score = baseline.score
    comparison.with_skill_score = with_skill.score
    comparison.improvement = with_skill.score - baseline.score
    max_score = _coverage_dimension_count(with_skill)
    comparison.baseline_defect_hits = [
        item for item in _string_list(expected.get("forbidden_behaviors"))
        if _meaning_present(_fold(baseline_text), item)
    ]

    if comparison.improvement <= 0:
        comparison.errors.append(
            f"with_skill_output.md must cover more professional obligations than baseline_output.md "
            f"({with_skill.score} <= {baseline.score})"
        )
    if baseline.score > 3:
        comparison.errors.append(
            f"baseline_output.md is too professional for a negative fixture ({baseline.score}/{max_score} > 3/{max_score})"
        )
    if with_skill.score < 8:
        comparison.errors.append(
            f"with_skill_output.md must cover core professional obligations ({with_skill.score}/{max_score} < 8/{max_score})"
        )
    if comparison.improvement < 4:
        comparison.errors.append(
            f"professional delta is too small to prove skill value ({comparison.improvement:+d} < +4)"
        )
    if not comparison.baseline_defect_hits:
        comparison.errors.append("baseline_output.md must demonstrate at least one forbidden behavior")
    for field_name, ok in asdict(with_skill).items():
        if field_name in {
            "score",
            "matched_hidden_risks",
            "matched_evidence",
            "matched_obligations",
            "forbidden_hits",
        }:
            continue
        if not ok:
            comparison.errors.append(f"with_skill_output.md missing comparison dimension '{field_name}'")
    return comparison


def _coverage_dimension_count(coverage: OutputCoverage) -> int:
    return sum(
        1
        for key in asdict(coverage)
        if key
        not in {
            "score",
            "matched_hidden_risks",
            "matched_evidence",
            "matched_obligations",
            "forbidden_hits",
        }
    )


def _coverage_for_output(
    text: str,
    expected: dict[str, Any],
    schema_result: BenchmarkResult,
    registry: dict[str, set[str]],
) -> OutputCoverage:
    folded = _fold(text)
    hidden_risks = _string_list(expected.get("expected_hidden_risks"))
    evidence = _string_list(expected.get("expected_evidence"))
    forbidden = _string_list(expected.get("forbidden_behaviors"))
    obligations = _string_list(expected.get("expected_output_obligations"))

    matched_hidden = [item for item in hidden_risks if _meaning_present(folded, item)]
    matched_evidence = [item for item in evidence if _meaning_present(folded, item)]
    matched_obligations = [item for item in obligations if _meaning_present(folded, item)]
    forbidden_hits = [item for item in forbidden if _forbidden_present(folded, item)]

    selected_stage = bool(
        schema_result.expected_stage
        and schema_result.expected_stage.casefold() in folded
        and ("selected stage" in folded or "stage:" in folded or "current_stage" in folded)
    )
    expected_skills = schema_result.expected_skills
    selected_professional_skill = bool(expected_skills) and all(
        skill.casefold() in folded for skill in expected_skills
    ) and ("selected professional skill" in folded or "selected skill" in folded or "selected_skills" in folded)
    expected_capabilities = schema_result.expected_capabilities
    selected_capabilities = bool(expected_capabilities) and all(
        capability.casefold() in folded for capability in expected_capabilities
    ) and ("selected capabilities" in folded or "selected_capabilities" in folded)
    validation_or_not_verified = bool(
        re.search(r"\b(pytest|npm test|go test|mvn test|cargo test|python3|unittest|validate-|eval-|not[- ]verified|not verified|validation command)\b", folded)
    )
    validation_outcome = _validation_has_outcome(text)
    route_relevance = _route_relevance(text, schema_result, registry)
    coverage = OutputCoverage(
        selected_stage=selected_stage,
        selected_professional_skill=selected_professional_skill,
        selected_capabilities=selected_capabilities,
        expected_hidden_risks=bool(hidden_risks) and len(matched_hidden) == len(hidden_risks),
        forbidden_behaviors_absent=not forbidden_hits,
        expected_evidence=bool(evidence) and len(matched_evidence) == len(evidence),
        expected_output_obligations=bool(obligations)
        and len(matched_obligations) == len(obligations),
        inspected_boundaries=bool(
            re.search(r"\b(inspected boundaries|boundaries inspected|boundary scan|files and boundaries inspected)\b", folded)
        ),
        evidence_limits=bool(
            re.search(r"\b(what evidence does not prove|what it does not prove|evidence limits|does not prove)\b", folded)
        ),
        residual_risk="residual risk" in folded or "residual-risk" in folded,
        residual_risk_owner=_residual_risk_has_owner(text),
        next_gate="next gate" in folded or "handoff" in folded or "next professional gate" in folded,
        validation_or_not_verified=validation_or_not_verified,
        validation_outcome=validation_outcome,
        route_relevance=route_relevance,
        matched_hidden_risks=matched_hidden,
        matched_evidence=matched_evidence,
        matched_obligations=matched_obligations,
        forbidden_hits=forbidden_hits,
    )
    coverage.score = sum(
        1
        for key, value in asdict(coverage).items()
        if key
        not in {
            "score",
            "matched_hidden_risks",
            "matched_evidence",
            "matched_obligations",
            "forbidden_hits",
        }
        and bool(value)
    )
    return coverage


def _validation_has_outcome(text: str) -> bool:
    folded = _fold(text)
    if "validation command" not in folded and not re.search(
        r"\b(pytest|npm test|go test|mvn test|cargo test|python3|unittest|validate-|eval-)\b",
        folded,
    ):
        return False
    validation_chunks = [
        line
        for line in text.splitlines()
        if "validation" in line.casefold()
        or re.search(
            r"\b(pytest|npm test|go test|mvn test|cargo test|python3|unittest|validate-|eval-)\b",
            line.casefold(),
        )
    ]
    outcome_terms = (
        "exit code",
        "failed",
        "failure",
        "not run",
        "not verified",
        "output",
        "outcome",
        "pass",
        "passed",
        "warning",
    )
    return any(any(term in line.casefold() for term in outcome_terms) for line in validation_chunks)


def _residual_risk_has_owner(text: str) -> bool:
    for line in text.splitlines():
        folded = line.casefold()
        if "residual risk" not in folded:
            continue
        if any(
            token in folded
            for token in (
                "maintainer",
                "on-call",
                "owned by",
                "owner",
                "platform",
                "qa",
                "release",
                "security",
                "sre",
                "team",
            )
        ):
            return True
    return False


def _route_relevance(
    text: str,
    schema_result: BenchmarkResult,
    registry: dict[str, set[str]],
) -> bool:
    route_lines = [line for line in text.splitlines() if "route to" in line.casefold()]
    if not route_lines:
        return True
    known_names = set(registry.get("skills", set())) | set(registry.get("capabilities", set()))
    expected_names = set(schema_result.expected_skills) | set(schema_result.expected_capabilities)
    routed_names: set[str] = set()
    unknown_names: set[str] = set()
    for line in route_lines:
        for name in re.findall(r"`([^`]+)`", line):
            if name in known_names:
                routed_names.add(name)
            elif re.fullmatch(r"[a-z0-9][a-z0-9_-]+", name):
                unknown_names.add(name)
    if unknown_names:
        return False
    if routed_names and not routed_names.intersection(expected_names):
        return False
    return True


def _comparison_status(comparison: ComparisonResult | None) -> str:
    if comparison is None or comparison.mode != "comparison":
        if comparison is not None and comparison.errors:
            return "fail"
        return "schema-only"
    return "pass" if not comparison.errors else "fail"


def _missing_expected_items(
    expected: dict[str, Any],
    result: BenchmarkResult,
    schema_errors: list[str],
) -> list[str]:
    missing = list(schema_errors)
    comparison = result.comparison
    if not comparison or comparison.mode != "comparison" or not comparison.with_skill_coverage:
        return missing

    missing.extend(_coverage_missing_items(expected, result, comparison.with_skill_coverage))
    return missing


def _forbidden_behavior_hits(comparison: ComparisonResult | None) -> list[str]:
    if not comparison or comparison.mode != "comparison" or not comparison.with_skill_coverage:
        return []
    return list(comparison.with_skill_coverage.forbidden_hits)


def _baseline_defect_hits(comparison: ComparisonResult | None) -> list[str]:
    if not comparison or comparison.mode != "comparison":
        return []
    return list(comparison.baseline_defect_hits)


def _with_skill_obligation_coverage(comparison: ComparisonResult | None) -> list[str]:
    if not comparison or comparison.mode != "comparison" or not comparison.with_skill_coverage:
        return []
    return _coverage_present_items_for_result(comparison.with_skill_coverage)


def _professional_delta_summary(
    comparison: ComparisonResult | None,
    missing_expected_items: list[str],
    forbidden_behavior_hits: list[str],
) -> ProfessionalDeltaSummary:
    if not comparison or comparison.mode != "comparison":
        return ProfessionalDeltaSummary(
            note="schema-only: no paired baseline_output.md and with_skill_output.md comparison"
        )
    baseline_missing: list[str] = []
    with_skill_present: list[str] = []
    if comparison.baseline_coverage:
        baseline_missing = _coverage_missing_items_for_result(comparison.baseline_coverage)
    if comparison.with_skill_coverage:
        with_skill_present = _coverage_present_items_for_result(comparison.with_skill_coverage)
    return ProfessionalDeltaSummary(
        baseline_missing=baseline_missing,
        with_skill_present=with_skill_present,
        remaining_gaps=missing_expected_items,
        forbidden_behavior_hits=forbidden_behavior_hits,
        delta_score=comparison.improvement,
    )


def _coverage_missing_items(
    expected: dict[str, Any],
    result: BenchmarkResult,
    coverage: OutputCoverage,
) -> list[str]:
    missing: list[str] = []
    if not coverage.selected_stage:
        missing.append(f"selected stage: {result.expected_stage}")
    if not coverage.selected_professional_skill:
        missing.append("selected professional skill: " + ", ".join(result.expected_skills))
    if not coverage.selected_capabilities:
        missing.append("selected capabilities: " + ", ".join(result.expected_capabilities))
    for item in _string_list(expected.get("expected_hidden_risks")):
        if item not in coverage.matched_hidden_risks:
            missing.append(f"hidden risk: {item}")
    for item in _string_list(expected.get("expected_evidence")):
        if item not in coverage.matched_evidence:
            missing.append(f"evidence: {item}")
    for item in _string_list(expected.get("expected_output_obligations")):
        if item not in coverage.matched_obligations:
            missing.append(f"output obligation: {item}")
    if not coverage.inspected_boundaries:
        missing.append("inspected boundaries")
    if not coverage.evidence_limits:
        missing.append("what evidence does not prove")
    if not coverage.residual_risk:
        missing.append("residual risk")
    if not coverage.residual_risk_owner:
        missing.append("residual risk owner")
    if not coverage.next_gate:
        missing.append("next gate")
    if not coverage.validation_or_not_verified:
        missing.append("validation command or not-verified disclosure")
    if not coverage.validation_outcome:
        missing.append("validation command outcome")
    if not coverage.route_relevance:
        missing.append("route relevance")
    if not coverage.forbidden_behaviors_absent:
        missing.append("forbidden behaviors absent")
    return missing


def _coverage_missing_items_for_result(coverage: OutputCoverage) -> list[str]:
    labels = {
        "selected_stage": "selected stage",
        "selected_professional_skill": "selected professional skill",
        "selected_capabilities": "selected capabilities",
        "expected_hidden_risks": "expected hidden risks",
        "forbidden_behaviors_absent": "forbidden behaviors absent",
        "expected_evidence": "expected evidence",
        "expected_output_obligations": "expected output obligations",
        "inspected_boundaries": "inspected boundaries",
        "evidence_limits": "what evidence does not prove",
        "residual_risk": "residual risk",
        "residual_risk_owner": "residual risk owner",
        "next_gate": "next gate",
        "validation_or_not_verified": "validation command or not-verified disclosure",
        "validation_outcome": "validation command outcome",
        "route_relevance": "route relevance",
    }
    return [label for key, label in labels.items() if not bool(getattr(coverage, key))]


def _coverage_present_items_for_result(coverage: OutputCoverage) -> list[str]:
    labels = {
        "selected_stage": "selected stage",
        "selected_professional_skill": "selected professional skill",
        "selected_capabilities": "selected capabilities",
        "expected_hidden_risks": "expected hidden risks",
        "forbidden_behaviors_absent": "forbidden behaviors avoided",
        "expected_evidence": "expected evidence",
        "expected_output_obligations": "expected output obligations",
        "inspected_boundaries": "inspected boundaries",
        "evidence_limits": "what evidence does not prove",
        "residual_risk": "residual risk",
        "residual_risk_owner": "residual risk owner",
        "next_gate": "next gate",
        "validation_or_not_verified": "validation command or not-verified disclosure",
        "validation_outcome": "validation command outcome",
        "route_relevance": "route relevance",
    }
    return [label for key, label in labels.items() if bool(getattr(coverage, key))]


def _stage_names() -> set[str]:
    if not ROUTING_RULES.is_file():
        return set()
    try:
        data = load_yaml_file(ROUTING_RULES)
    except ValidationProblem:
        return set()
    if not isinstance(data, dict):
        return set()
    raw = data.get("engineering_stage_signals")
    if isinstance(raw, dict):
        return {str(key).strip() for key in raw if str(key).strip()}
    if isinstance(raw, list):
        names = set()
        for item in raw:
            if isinstance(item, dict) and isinstance(item.get("stage"), str):
                names.add(item["stage"].strip())
            elif isinstance(item, str):
                names.add(item.strip())
        return names
    return set()


def _write_reports(report: BenchmarkReport, reports_dir: Path, report_format: str) -> list[Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if report_format in {"all", "markdown"}:
        path = reports_dir / PRIMARY_MARKDOWN_REPORT
        path.write_text(_render_markdown(report), encoding="utf-8")
        written.append(path)
        legacy = reports_dir / MARKDOWN_REPORT
        legacy.write_text(_render_markdown(report), encoding="utf-8")
        written.append(legacy)
    if report_format in {"all", "json"}:
        path = reports_dir / PRIMARY_JSON_REPORT
        path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
        legacy = reports_dir / JSON_REPORT
        legacy.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(legacy)
    return written


def _render_markdown(report: BenchmarkReport) -> str:
    lines = [
        "# Professional Benchmarks Evaluation",
        "",
        f"- Generated: {report.generated_at}",
        f"- Mode: {report.mode}",
        f"- Cases checked: {report.cases_checked}",
        f"- Comparison cases checked: {report.comparison_cases_checked}",
        f"- Errors: {len(report.errors)}",
        f"- Actual output comparison: {report.actual_output_comparison}",
        "- Comparison note: this is a deterministic rule heuristic; it cannot replace human review or a real agent eval.",
        "",
        "| Case | Schema Status | Comparison Status | Stage | Skills | Missing Expected Items | Forbidden Behavior Hits | Professional Delta Summary | Errors |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |",
    ]
    for result in report.results:
        skills = ", ".join(result.expected_skills)
        summary = _format_delta_summary(result.professional_delta_summary)
        lines.append(
            f"| `{result.path}` | {result.schema_status} | {result.comparison_status} | "
            f"`{result.expected_stage}` | {skills} | {len(result.missing_expected_items)} | "
            f"{len(result.forbidden_behavior_hits)} | {summary} | {len(result.errors)} |"
        )
    lines.extend(
        [
            "",
            "## Benchmark Quality Details",
            "",
            "| Case | Benchmark Quality Status | Baseline Defect Hits | With-Skill Obligation Coverage | Delta Score | Remaining Gaps |",
            "| --- | --- | ---: | --- | ---: | ---: |",
        ]
    )
    for result in report.results:
        lines.append(
            f"| `{result.path}` | {result.benchmark_quality_status} | "
            f"{len(result.baseline_defect_hits)} | "
            f"{', '.join(result.with_skill_obligation_coverage) or '-'} | "
            f"{result.delta_score:+d} | {len(result.remaining_gaps)} |"
        )
    if report.errors:
        lines.extend(["", "## Errors", ""])
        for error in report.errors:
            lines.append(f"- {error}")
    return "\n".join(lines).rstrip() + "\n"


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _looks_placeholder(value: str) -> bool:
    folded = value.strip().casefold()
    return folded in {"todo", "tbd", "placeholder", "n/a", "none"} or "similar to above" in folded


def _looks_vague_expected_item(value: str) -> bool:
    folded = re.sub(r"\s+", " ", value.strip().casefold())
    if any(phrase == folded or phrase in folded for phrase in GENERIC_EXPECTED_PHRASES):
        return True
    meaningful_tokens = [
        token
        for token in re.findall(r"[a-z0-9_-]+", folded)
        if len(token) >= 4
        and token
        not in {
            "with",
            "without",
            "must",
            "should",
            "expected",
            "output",
            "risk",
        }
    ]
    return len(meaningful_tokens) < 2


def _format_delta_summary(summary: ProfessionalDeltaSummary) -> str:
    return (
        f"baseline_missing: {len(summary.baseline_missing)}; "
        f"with_skill_present: {len(summary.with_skill_present)}; "
        f"remaining_gaps: {len(summary.remaining_gaps)}; "
        f"forbidden_behavior_hits: {len(summary.forbidden_behavior_hits)}; "
        f"delta_score: {summary.delta_score:+d}"
    )


def _contains_forbidden_scope(text: str) -> bool:
    folded = text.casefold()
    forbidden = (
        "marketplace",
        "persona",
        "slash command",
        "plugin catalog",
        "badge",
        "personal knowledge base",
        "src/toolbox",
        "registry/toolbox.yaml",
    )
    return any(token in folded for token in forbidden)


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", " ", text.casefold())


def _meaning_present(folded_text: str, phrase: str) -> bool:
    folded_phrase = _fold(phrase)
    if folded_phrase and folded_phrase in folded_text:
        return True
    tokens = [
        token
        for token in folded_phrase.split()
        if len(token) >= 4
        and token
        not in {
            "with",
            "without",
            "from",
            "that",
            "this",
            "must",
            "claim",
            "output",
            "evidence",
            "validation",
        }
    ]
    if not tokens:
        return False
    required = max(1, min(len(tokens), (len(tokens) + 1) // 2))
    return sum(1 for token in tokens if token in folded_text) >= required


def _forbidden_present(folded_text: str, phrase: str) -> bool:
    folded_phrase = _fold(phrase)
    return bool(folded_phrase and folded_phrase in folded_text)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
