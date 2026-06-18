#!/usr/bin/env python3
"""Validate professional benchmark risk coverage in routing fixtures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
DEFAULT_ROUTING_DIR = ROOT / "evals" / "routing"
DEFAULT_BENCHMARKS_DIR = ROOT / "evals" / "professional-benchmarks"
DEFAULT_REPORTS_DIR = ROOT / "reports"
DEFAULT_BASELINE = ROOT / "config" / "professionalism-baseline.yaml"
JSON_REPORT = "professional-routing-coverage.json"
MARKDOWN_REPORT = "professional-routing-coverage.md"
RUNTIME_FIXTURE_SUITES = {
    "executor-adapters": "executor-adapter-protocol",
    "repository-intelligence": "repository-graph-analysis",
    "project-memory": "project-memory-governance",
    "validation-broker": "validation-broker",
    "trajectory": "execution-trajectory-analysis",
}
RUNTIME_FIXTURE_REQUIRED_FIELDS = (
    "id",
    "scenario",
    "expected_capabilities",
    "expected_evidence",
    "forbidden_claims",
    "privacy_boundary",
)

EXPECTED_FIELDS = ("skills", "capabilities", "domain_extensions", "quality_gates")
MIN_L1_ANTI_OVER_ROUTING_CASES = 8
L1_OVER_ROUTING_SKILLS = {
    "change-intake-compiler",
    "change-impact-analyzer",
    "task-dag-planner",
    "domain-impact-modeler",
    "architecture-impact-reviewer",
    "data-api-contract-changer",
    "data-middleware-change-builder",
    "integration-change-builder",
    "security-privacy-gate",
    "reliability-observability-gate",
    "delivery-release-gate",
}

STOPWORDS = {
    "about",
    "after",
    "auth",
    "before",
    "behavior",
    "builder",
    "case",
    "change",
    "claim",
    "code",
    "contract",
    "coverage",
    "evidence",
    "expected",
    "from",
    "gate",
    "hidden",
    "into",
    "local",
    "must",
    "output",
    "professional",
    "required",
    "risk",
    "selected",
    "state",
    "test",
    "that",
    "this",
    "validation",
    "with",
    "without",
}

GENERIC_MATCH_TOKENS = STOPWORDS | {
    "action",
    "agent",
    "capability",
    "capabilities",
    "design",
    "fix",
    "gate",
    "review",
    "route",
    "skill",
    "skills",
}

RISK_TOKENS = {
    "backlog",
    "break",
    "breakage",
    "collision",
    "corruption",
    "crash",
    "deadlock",
    "duplicate",
    "exfiltration",
    "forged",
    "idor",
    "inconsistent",
    "leak",
    "missing",
    "outage",
    "poison",
    "replay",
    "rollback",
    "stale",
    "storm",
    "unbounded",
    "unrecoverable",
    "unverified",
}

ACRONYM_RISK_TOKENS = {"csrf", "cve", "dlq", "idor", "pii", "rce", "sqli", "slo", "ssrf", "xss"}


@dataclass
class Finding:
    category: str
    target: str
    message: str
    detail: Any = None
    severity: str = "error"


@dataclass
class RoutingCase:
    case_id: str
    path: str
    text: str
    risk_text: str
    complexity: str = ""
    risk_level: str = ""
    skills: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    domain_extensions: list[str] = field(default_factory=list)
    quality_gates: list[str] = field(default_factory=list)
    risk_triggers: list[str] = field(default_factory=list)
    forbidden_counts: dict[str, int] = field(default_factory=dict)

    @property
    def forbidden_present(self) -> bool:
        return any(count > 0 for count in self.forbidden_counts.values())


@dataclass
class CoverageReport:
    generated_at: str
    status: str
    routing_cases_checked: int
    benchmark_cases_checked: int
    hidden_risks_checked: int
    hidden_risks_covered: int
    hidden_risks_not_required: int
    hidden_risks_weak_only: int
    hidden_risks_uncovered: int
    strong_matches: int
    weak_matches: int
    matched_by_expected_route_only: int
    expected_route_only_supplemental: int
    needs_manual_review: int
    hidden_risks_with_weak_matches: int
    hidden_risks_matched_by_expected_route_only: int
    hidden_risks_needing_manual_review: int
    l1_anti_over_routing_count: int
    runtime_fixture_dirs_checked: int
    runtime_fixture_cases_checked: int
    findings: list[Finding]
    benchmark_risk_coverage: list[dict[str, Any]]
    runtime_fixture_coverage: list[dict[str, Any]]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    try:
        report = validate(
            routing_dir=args.routing_dir,
            benchmarks_dir=args.benchmarks_dir,
            baseline_path=args.baseline,
        )
    except (ValidationProblem, OSError) as exc:
        finding = Finding("input-error", "routing coverage", str(exc))
        report = CoverageReport(
            generated_at=_now(),
            status="fail",
            routing_cases_checked=0,
            benchmark_cases_checked=0,
            hidden_risks_checked=0,
            hidden_risks_covered=0,
            hidden_risks_not_required=0,
            hidden_risks_weak_only=0,
            hidden_risks_uncovered=0,
            strong_matches=0,
            weak_matches=0,
            matched_by_expected_route_only=0,
            expected_route_only_supplemental=0,
            needs_manual_review=0,
            hidden_risks_with_weak_matches=0,
            hidden_risks_matched_by_expected_route_only=0,
            hidden_risks_needing_manual_review=0,
            l1_anti_over_routing_count=0,
            runtime_fixture_dirs_checked=0,
            runtime_fixture_cases_checked=0,
            findings=[finding],
            benchmark_risk_coverage=[],
            runtime_fixture_coverage=[],
        )
        _write_reports(report, args.reports_dir)
        print(f"validate-professional-routing-coverage: ERROR: {exc}", file=sys.stderr)
        return 1
    _write_reports(report, args.reports_dir)
    print(
        "validate-professional-routing-coverage: "
        f"status={report.status}; routing_cases={report.routing_cases_checked}; "
        f"benchmark_hidden_risks_strong={report.hidden_risks_covered}/{report.hidden_risks_checked}; "
        f"runtime_fixtures={report.runtime_fixture_cases_checked}; "
        f"not_required={report.hidden_risks_not_required}; "
        f"findings={len(report.findings)}"
    )
    if report.findings:
        for finding in report.findings:
            print(
                f"validate-professional-routing-coverage: ERROR: "
                f"{finding.target}: {finding.message}",
                file=sys.stderr,
            )
        return 1
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing-dir", type=Path, default=DEFAULT_ROUTING_DIR)
    parser.add_argument("--benchmarks-dir", type=Path, default=DEFAULT_BENCHMARKS_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    return parser.parse_args(argv)


def validate(*, routing_dir: Path, benchmarks_dir: Path, baseline_path: Path) -> CoverageReport:
    skills, capabilities, domain_extensions, capability_used_by = _load_registry()
    routing_cases = _load_routing_cases(routing_dir)
    benchmark_cases = _load_benchmark_cases(benchmarks_dir)
    findings: list[Finding] = []

    _check_routing_cases(routing_cases, skills, capabilities, domain_extensions, capability_used_by, findings)
    runtime_rows, runtime_dirs, runtime_cases = _check_runtime_fixture_coverage(capabilities, findings)
    l1_count = sum(1 for case in routing_cases if _is_l1_anti_over_routing_case(case))
    baseline_l1 = _baseline_l1_count(baseline_path)
    if baseline_l1 is not None and l1_count < baseline_l1:
        findings.append(Finding("l1-anti-over-routing-regression", "evals/routing", "L1 anti-over-routing case count decreased", {"baseline": baseline_l1, "current": l1_count}))
    elif baseline_l1 is None and l1_count < MIN_L1_ANTI_OVER_ROUTING_CASES:
        findings.append(Finding("l1-anti-over-routing-floor", "evals/routing", "L1 anti-over-routing case count is below floor", {"minimum": MIN_L1_ANTI_OVER_ROUTING_CASES, "current": l1_count}))

    coverage_rows, checked, covered = _check_benchmark_hidden_risk_coverage(
        benchmark_cases,
        routing_cases,
        findings,
    )
    not_required_count = sum(1 for row in coverage_rows if row.get("coverage_status") == "not-required")
    weak_only_count = sum(1 for row in coverage_rows if row.get("coverage_status") == "weak-only")
    uncovered_count = sum(1 for row in coverage_rows if row.get("coverage_status") == "uncovered")
    weak_count = sum(1 for row in coverage_rows if row.get("weak_matches"))
    route_only_count = sum(1 for row in coverage_rows if row.get("matched_by_expected_route_only"))
    manual_review_count = sum(1 for row in coverage_rows if row.get("needs_manual_review"))
    strong_count = sum(1 for row in coverage_rows if row.get("strong_matches"))
    status = "fail" if findings else "pass"
    return CoverageReport(
        generated_at=_now(),
        status=status,
        routing_cases_checked=len(routing_cases),
        benchmark_cases_checked=len(benchmark_cases),
        hidden_risks_checked=checked,
        hidden_risks_covered=covered,
        hidden_risks_not_required=not_required_count,
        hidden_risks_weak_only=weak_only_count,
        hidden_risks_uncovered=uncovered_count,
        strong_matches=strong_count,
        weak_matches=weak_count,
        matched_by_expected_route_only=route_only_count,
        expected_route_only_supplemental=route_only_count,
        needs_manual_review=manual_review_count,
        hidden_risks_with_weak_matches=weak_count,
        hidden_risks_matched_by_expected_route_only=route_only_count,
        hidden_risks_needing_manual_review=manual_review_count,
        l1_anti_over_routing_count=l1_count,
        runtime_fixture_dirs_checked=runtime_dirs,
        runtime_fixture_cases_checked=runtime_cases,
        findings=findings,
        benchmark_risk_coverage=coverage_rows,
        runtime_fixture_coverage=runtime_rows,
    )


def _check_runtime_fixture_coverage(
    capabilities: set[str],
    findings: list[Finding],
) -> tuple[list[dict[str, Any]], int, int]:
    rows: list[dict[str, Any]] = []
    total_cases = 0
    for suite, required_capability in RUNTIME_FIXTURE_SUITES.items():
        suite_dir = ROOT / "evals" / suite
        paths = sorted(suite_dir.glob("*.yaml")) if suite_dir.is_dir() else []
        suite_errors: list[str] = []
        if not suite_dir.is_dir():
            suite_errors.append("directory missing")
        if len(paths) < 3:
            suite_errors.append(f"fixtures={len(paths)}, expected_at_least=3")
        required_hits = 0
        valid_cases = 0
        for path in paths:
            total_cases += 1
            case_errors = _runtime_fixture_case_errors(path, required_capability, capabilities)
            if case_errors:
                suite_errors.extend(f"{path.name}: {error}" for error in case_errors)
            else:
                valid_cases += 1
                required_hits += 1
        if required_hits < min(3, len(paths)) or required_hits < 3:
            suite_errors.append(
                f"required_capability_hits={required_hits}, expected_at_least=3 for {required_capability}"
            )
        status = "pass" if not suite_errors else "fail"
        rows.append(
            {
                "suite": suite,
                "required_capability": required_capability,
                "fixtures": len(paths),
                "valid_cases": valid_cases,
                "status": status,
                "errors": suite_errors,
            }
        )
        for error in suite_errors:
            findings.append(
                Finding(
                    "runtime-fixture-coverage",
                    f"evals/{suite}",
                    error,
                )
            )
    return rows, len(RUNTIME_FIXTURE_SUITES), total_cases


def _runtime_fixture_case_errors(
    path: Path,
    required_capability: str,
    capabilities: set[str],
) -> list[str]:
    errors: list[str] = []
    try:
        data = load_yaml_file(path)
    except ValidationProblem as exc:
        return [str(exc)]
    if not isinstance(data, dict):
        return ["fixture must be a mapping"]
    for field_name in RUNTIME_FIXTURE_REQUIRED_FIELDS:
        if field_name not in data:
            errors.append(f"missing field '{field_name}'")
    for field_name in ("id", "scenario", "privacy_boundary"):
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"field '{field_name}' must be a non-empty string")
    for field_name in ("expected_capabilities", "expected_evidence", "forbidden_claims"):
        values = _string_list(data.get(field_name))
        if not values:
            errors.append(f"field '{field_name}' must be a non-empty list of strings")
    expected_capabilities = _string_list(data.get("expected_capabilities"))
    for capability in expected_capabilities:
        if capability not in capabilities:
            errors.append(f"unknown capability '{capability}'")
    if required_capability not in expected_capabilities:
        errors.append(f"expected_capabilities must include '{required_capability}'")
    return errors


def _load_registry() -> tuple[set[str], set[str], set[str], dict[str, set[str]]]:
    skills = _registry_names(REGISTRY_DIR / "skills.yaml", "skills")
    extensions = _registry_names(REGISTRY_DIR / "domain-extensions.yaml", "domain_extensions")
    capability_path = REGISTRY_DIR / "capabilities.yaml"
    data = load_yaml_file(capability_path)
    if not isinstance(data, dict):
        raise ValidationProblem(f"{capability_path}: expected mapping")
    capabilities: set[str] = set()
    used_by: dict[str, set[str]] = {}
    for entry in data.get("capabilities", []) or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        capabilities.add(name.strip())
        owners = entry.get("used_by")
        used_by[name.strip()] = {
            str(item).strip()
            for item in owners
            if isinstance(owners, list) and str(item).strip()
        } if isinstance(owners, list) else set()
    return skills, capabilities, extensions, used_by


def _registry_names(path: Path, key: str) -> set[str]:
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise ValidationProblem(f"{path}: expected mapping")
    names: set[str] = set()
    for entry in data.get(key, []) or []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            names.add(entry["name"].strip())
    return names


def _load_routing_cases(routing_dir: Path) -> list[RoutingCase]:
    cases: list[RoutingCase] = []
    if not routing_dir.is_dir():
        raise ValidationProblem(f"{routing_dir}: routing directory does not exist")
    for path in sorted(routing_dir.glob("*.yaml")):
        data = load_yaml_file(path)
        if not isinstance(data, dict):
            continue
        expected = data.get("expected")
        if not isinstance(expected, dict):
            expected = {}
        forbidden = data.get("forbidden")
        if not isinstance(forbidden, dict):
            forbidden = {}
        case_id = _string(data.get("id") or path.stem)
        text = _case_text(data)
        hidden_risk_phrases = _string_list(expected.get("hidden_risk_phrases"))
        risk_text = f"{_top_case_text(data, expected)} {' '.join(hidden_risk_phrases)}"
        cases.append(
            RoutingCase(
                case_id=case_id,
                path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                text=text,
                risk_text=risk_text,
                complexity=_string(expected.get("complexity")),
                risk_level=_string(expected.get("risk_level")),
                skills=_string_list(expected.get("skills")),
                capabilities=_string_list(expected.get("capabilities")),
                domain_extensions=_string_list(expected.get("domain_extensions")),
                quality_gates=_string_list(expected.get("quality_gates")),
                risk_triggers=_string_list(expected.get("risk_triggers")),
                forbidden_counts={field: len(_string_list(forbidden.get(field))) for field in EXPECTED_FIELDS},
            )
        )
    return cases


def _load_benchmark_cases(benchmarks_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    cases: list[tuple[Path, dict[str, Any]]] = []
    if not benchmarks_dir.is_dir():
        return cases
    for path in sorted(benchmarks_dir.rglob("expected.yaml")):
        data = load_yaml_file(path)
        if isinstance(data, dict):
            cases.append((path, data))
    return cases


def _check_routing_cases(
    routing_cases: list[RoutingCase],
    skills: set[str],
    capabilities: set[str],
    domain_extensions: set[str],
    capability_used_by: dict[str, set[str]],
    findings: list[Finding],
) -> None:
    for case in routing_cases:
        if _is_professional_routing_case(case) and not case.forbidden_present:
            findings.append(Finding("routing-case-without-forbidden", case.path, "professional routing case has no forbidden.* coverage", case.forbidden_counts))
        _check_membership(case.path, "expected.skills", case.skills, skills, findings)
        _check_membership(case.path, "expected.capabilities", case.capabilities, capabilities, findings)
        _check_membership(case.path, "expected.domain_extensions", case.domain_extensions, domain_extensions, findings)
        _check_overrouting(case, findings)
        _check_capability_used_by(case, capability_used_by, findings)
        _check_high_risk_gates(case, findings)


def _check_membership(
    path: str,
    field_name: str,
    values: list[str],
    allowed: set[str],
    findings: list[Finding],
) -> None:
    for value in values:
        if value not in allowed:
            findings.append(Finding("unknown-routing-reference", path, f"{field_name} contains unknown name '{value}'"))


def _check_overrouting(case: RoutingCase, findings: list[Finding]) -> None:
    skill_count = len(case.skills)
    limits = {"L1": 2, "L2": 5, "L3": 8, "L4": 11, "L5": 12}
    limit = limits.get(case.complexity)
    if limit is not None and skill_count > limit:
        findings.append(Finding("obvious-over-routing", case.path, f"{case.complexity} case selects {skill_count} skills, above limit {limit}", case.skills))
    if case.complexity == "L1":
        heavy = sorted(set(case.skills).intersection(L1_OVER_ROUTING_SKILLS))
        if heavy:
            findings.append(Finding("l1-over-routing", case.path, "L1 case selects heavyweight professional skills", heavy))


def _check_capability_used_by(
    case: RoutingCase,
    capability_used_by: dict[str, set[str]],
    findings: list[Finding],
) -> None:
    selected_owners = set(case.skills) | set(case.domain_extensions)
    for capability in case.capabilities:
        owners = capability_used_by.get(capability, set())
        if owners and not owners.intersection(selected_owners):
            findings.append(
                Finding(
                    "capability-used-by-mismatch",
                    case.path,
                    f"selected capability '{capability}' is not used_by any selected skill or domain extension",
                    {"used_by": sorted(owners), "selected": sorted(selected_owners)},
                )
            )


def _check_high_risk_gates(case: RoutingCase, findings: list[Finding]) -> None:
    if case.risk_level not in {"high", "critical"} and case.complexity not in {"L4", "L5"}:
        return
    text = f"{case.risk_text} {' '.join(case.risk_triggers)}".casefold()
    gate_text = " ".join(case.quality_gates).casefold()
    skill_set = set(case.skills)
    required: list[tuple[str, str, str, tuple[str, ...]]] = [
        ("security", "security-privacy-gate", "security gate", ("auth", "authorization", "permission", "pii", "user data", "webhook", "secret", "public exposure", "security", "saml", "wallet", "private key")),
        ("reliability", "reliability-observability-gate", "reliability gate", ("incident", "outage", "latency", "lag", "retry storm", "queue", "cache stampede", "slo", "production writes")),
        ("delivery", "delivery-release-gate", "delivery gate", ("deploy", "release", "migration", "rollback", "production deployment", "kubernetes", "terraform")),
        ("documentation", "change-documentation-gate", "documentation gate", ("compliance", "audit evidence", "postmortem", "customer update", "release note", "documentation")),
    ]
    for label, skill, gate, keywords in required:
        if any(_contains_keyword_phrase(text, keyword) for keyword in keywords):
            if skill not in skill_set and gate not in gate_text:
                findings.append(
                    Finding(
                        "missing-high-risk-gate",
                        case.path,
                        f"high-risk routing case mentions {label} risk but lacks {skill} or {gate}",
                    )
                )


def _contains_keyword_phrase(text: str, keyword: str) -> bool:
    folded_keyword = keyword.casefold()
    if " " in folded_keyword:
        return folded_keyword in text
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(folded_keyword)}(?![a-z0-9])", text))


def _check_benchmark_hidden_risk_coverage(
    benchmark_cases: list[tuple[Path, dict[str, Any]]],
    routing_cases: list[RoutingCase],
    findings: list[Finding],
) -> tuple[list[dict[str, Any]], int, int]:
    coverage_rows: list[dict[str, Any]] = []
    checked = 0
    strongly_covered = 0
    for path, expected in benchmark_cases:
        skip_reason = _string(expected.get("routing_not_required_reason"))
        hidden_risks = _string_list(expected.get("expected_hidden_risks"))
        expected_skills = _string_list(expected.get("expected_professional_skill"))
        expected_capabilities = _string_list(expected.get("expected_capabilities"))
        for risk in hidden_risks:
            checked += 1
            strong_matches: list[str] = []
            weak_matches: list[str] = []
            expected_route_only_matches: list[str] = []
            for case in routing_cases:
                strength = _risk_match_strength(risk, case)
                if strength == "strong":
                    strong_matches.append(case.case_id)
                elif strength == "weak":
                    weak_matches.append(case.case_id)
                if _benchmark_route_matches_expected(
                    risk,
                    expected_skills,
                    expected_capabilities,
                    case,
                ) and strength != "strong":
                    expected_route_only_matches.append(case.case_id)
            coverage_status = _coverage_status(
                strong_matches=strong_matches,
                weak_matches=weak_matches,
                expected_route_only_matches=expected_route_only_matches,
                skip_reason=skip_reason,
            )
            is_strongly_covered = coverage_status == "covered"
            needs_manual_review = coverage_status == "manual-review"
            if is_strongly_covered:
                strongly_covered += 1
            elif coverage_status != "not-required":
                findings.append(
                    Finding(
                        "benchmark-hidden-risk-uncovered",
                        str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                        f"expected_hidden_risk has {coverage_status} routing coverage: {risk}",
                    )
                )
            coverage_rows.append(
                {
                    "benchmark": str(path.parent.relative_to(ROOT)) if path.parent.is_relative_to(ROOT) else str(path.parent),
                    "hidden_risk": risk,
                    "coverage_status": coverage_status,
                    "covered": is_strongly_covered,
                    "strong_matches": strong_matches,
                    "weak_matches": weak_matches,
                    "matched_by_expected_route_only": expected_route_only_matches,
                    "needs_manual_review": needs_manual_review,
                    "routing_cases": strong_matches,
                    "routing_not_required_reason": skip_reason,
                }
            )
    return coverage_rows, checked, strongly_covered


def _coverage_status(
    *,
    strong_matches: list[str],
    weak_matches: list[str],
    expected_route_only_matches: list[str],
    skip_reason: str,
) -> str:
    if strong_matches:
        return "covered"
    if skip_reason:
        return "not-required"
    if weak_matches:
        return "weak-only"
    if expected_route_only_matches:
        return "manual-review"
    return "uncovered"


def _benchmark_route_matches_expected(
    risk: str,
    expected_skills: list[str],
    expected_capabilities: list[str],
    case: RoutingCase,
) -> bool:
    if not set(expected_skills).intersection(case.skills):
        return False
    if expected_capabilities and not set(expected_capabilities).intersection(case.capabilities):
        return False
    return _has_route_relevant_risk_signal(risk, case)


def _risk_matches_case(risk: str, case: RoutingCase) -> bool:
    return _risk_match_strength(risk, case) == "strong"


def _risk_match_strength(risk: str, case: RoutingCase) -> str:
    folded_risk = _fold(risk)
    folded_case = _fold_for_phrase(case.text)
    if folded_risk and _fold_for_phrase(folded_risk) in folded_case:
        return "strong"

    risk_tokens = _signal_tokens(risk)
    if not risk_tokens:
        return "none"
    case_tokens = set(_signal_tokens(case.text))
    top_case_tokens = set(_signal_tokens(case.risk_text))
    if _strong_phrase_match(risk, case):
        return "strong"

    risk_token_hits = set(risk_tokens).intersection(RISK_TOKENS | ACRONYM_RISK_TOKENS)
    domain_tokens = [token for token in risk_tokens if token not in RISK_TOKENS | ACRONYM_RISK_TOKENS]
    domain_hits = set(domain_tokens).intersection(case_tokens)
    top_domain_hits = set(domain_tokens).intersection(top_case_tokens)
    if risk_token_hits.intersection(case_tokens) and len(top_domain_hits) >= min(2, len(domain_tokens)):
        return "weak"
    if risk_token_hits.intersection(case_tokens) and len(domain_hits) >= min(3, len(domain_tokens)):
        return "weak"
    return "none"


def _strong_phrase_match(risk: str, case: RoutingCase) -> bool:
    haystacks = [
        _fold_for_phrase(case.case_id),
        _fold_for_phrase(case.risk_text),
        _fold_for_phrase(" ".join(case.risk_triggers)),
        _fold_for_phrase(" ".join(case.capabilities)),
    ]
    phrases = _normalized_risk_phrases(risk)
    if any(phrase in haystack for phrase in phrases for haystack in haystacks):
        return True
    tokens = _signal_tokens(risk)
    acronym_hits = [token for token in tokens if token in ACRONYM_RISK_TOKENS]
    if acronym_hits:
        top_tokens = set(_signal_tokens(f"{case.case_id} {case.risk_text} {' '.join(case.risk_triggers)}"))
        domain_tokens = [
            token for token in tokens
            if token not in ACRONYM_RISK_TOKENS and token not in RISK_TOKENS
        ]
        if set(acronym_hits).intersection(top_tokens) and set(domain_tokens).intersection(top_tokens):
            return True
    return False


def _normalized_risk_phrases(risk: str) -> list[str]:
    folded = _fold_for_phrase(risk)
    tokens = _signal_tokens(risk)
    phrases = [folded] if len(folded.split()) >= 2 else []
    if len(tokens) >= 2:
        phrases.append(" ".join(tokens))
    risk_hits = [token for token in tokens if token in RISK_TOKENS | ACRONYM_RISK_TOKENS]
    domain_hits = [token for token in tokens if token not in RISK_TOKENS | ACRONYM_RISK_TOKENS]
    for risk_token in risk_hits:
        for domain_token in domain_hits:
            phrases.append(f"{domain_token} {risk_token}")
            phrases.append(f"{risk_token} {domain_token}")
    chunks = re.split(r"\b(?:from|without|with|and|or|after|before)\b", folded)
    for chunk in chunks:
        phrase = " ".join(_signal_tokens(chunk))
        if len(phrase.split()) >= 2:
            phrases.append(phrase)
    return sorted(set(phrase for phrase in phrases if len(phrase.split()) >= 2), key=len, reverse=True)


def _has_route_relevant_risk_signal(risk: str, case: RoutingCase) -> bool:
    risk_tokens = set(_signal_tokens(risk))
    if not risk_tokens:
        return False
    route_text = f"{case.case_id} {case.risk_text} {' '.join(case.risk_triggers)} {' '.join(case.capabilities)}"
    route_tokens = set(_signal_tokens(route_text))
    domain_tokens = risk_tokens - RISK_TOKENS - ACRONYM_RISK_TOKENS
    risk_hits = risk_tokens.intersection(RISK_TOKENS | ACRONYM_RISK_TOKENS).intersection(route_tokens)
    domain_hits = domain_tokens.intersection(route_tokens)
    return bool(risk_hits) and len(domain_hits) >= min(1, len(domain_tokens))


def _baseline_l1_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return None
    if not isinstance(data, dict):
        return None
    routing = data.get("routing")
    if isinstance(routing, dict) and isinstance(routing.get("l1_anti_over_routing_count"), int):
        return routing["l1_anti_over_routing_count"]
    return None


def _is_professional_routing_case(case: RoutingCase) -> bool:
    return (
        case.complexity in {"L2", "L3", "L4", "L5"}
        or case.risk_level in {"medium", "high", "critical"}
        or "hidden-risk" in case.case_id
    )


def _is_l1_anti_over_routing_case(case: RoutingCase) -> bool:
    if case.complexity != "L1":
        return False
    forbidden_text = " ".join(f"{key}:{value}" for key, value in case.forbidden_counts.items()).casefold()
    case_text = case.text.casefold()
    return any(token in case_text for token in ("over-routing", "must not pull", "minimum-sufficient", "not infer")) or any(count > 0 for count in case.forbidden_counts.values()) and bool(set(case.skills).isdisjoint(L1_OVER_ROUTING_SKILLS))


def _case_text(data: dict[str, Any]) -> str:
    expected = data.get("expected") if isinstance(data.get("expected"), dict) else {}
    forbidden = data.get("forbidden") if isinstance(data.get("forbidden"), dict) else {}
    parts: list[str] = []
    for key in ("id", "description", "prompt", "notes"):
        value = data.get(key)
        if isinstance(value, str):
            parts.append(value)
    for value in expected.values():
        parts.extend(_flatten_strings(value))
    for value in forbidden.values():
        parts.extend(_flatten_strings(value))
    return " ".join(parts)


def _top_case_text(data: dict[str, Any], expected: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("id", "description", "prompt"):
        value = data.get(key)
        if isinstance(value, str):
            parts.append(value)
    parts.extend(_string_list(expected.get("risk_triggers")))
    return " ".join(parts)


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_flatten_strings(item))
        return out
    return []


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9_-]+", text.casefold())
        if len(token) >= 4 and token not in STOPWORDS
    ]


def _signal_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", _fold_for_phrase(text))
        if len(token) >= 3 and token not in GENERIC_MATCH_TOKENS
    ]


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", " ", text.casefold()).strip()


def _fold_for_phrase(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_reports(report: CoverageReport, reports_dir: Path) -> None:
    payload = asdict(report)
    (reports_dir / JSON_REPORT).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / MARKDOWN_REPORT).write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: CoverageReport) -> str:
    lines = [
        "# Professional Routing Coverage",
        "",
        f"- Generated: {report.generated_at}",
        f"- Status: {report.status}",
        f"- Routing cases checked: {report.routing_cases_checked}",
        f"- Benchmark cases checked: {report.benchmark_cases_checked}",
        f"- Hidden risks checked: {report.hidden_risks_checked}",
        f"- Strongly covered: {report.hidden_risks_covered}",
        f"- Not required: {report.hidden_risks_not_required}",
        f"- Weak-only: {report.hidden_risks_weak_only}",
        f"- Expected-route-only supplemental: {report.expected_route_only_supplemental}",
        f"- Uncovered: {report.hidden_risks_uncovered}",
        f"- Manual review: {report.needs_manual_review}",
        f"- L1 anti-over-routing cases: {report.l1_anti_over_routing_count}",
        f"- Runtime fixture suites checked: {report.runtime_fixture_dirs_checked}",
        f"- Runtime fixture cases checked: {report.runtime_fixture_cases_checked}",
        f"- Findings: {len(report.findings)}",
        "",
        "## Benchmark Hidden Risk Coverage",
        "",
        "| Benchmark | Coverage Status | Hidden Risk | Strong Matches |",
        "| --- | --- | --- | --- |",
    ]
    for row in report.benchmark_risk_coverage:
        lines.append(
            f"| `{row['benchmark']}` | {row['coverage_status']} | "
            f"{row['hidden_risk']} | "
            f"{', '.join(row['strong_matches']) or '-'} |"
        )
    debug_rows = [
        row for row in report.benchmark_risk_coverage
        if row.get("weak_matches") or row.get("matched_by_expected_route_only")
    ]
    lines.extend(["", "<details>", "<summary>Supplemental debug matches</summary>", ""])
    if debug_rows:
        lines.extend(
            [
                "| Benchmark | Hidden Risk | Weak Matches | Expected-Route-Only |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in debug_rows:
            lines.append(
                f"| `{row['benchmark']}` | {row['hidden_risk']} | "
                f"{', '.join(row['weak_matches']) or '-'} | "
                f"{', '.join(row['matched_by_expected_route_only']) or '-'} |"
            )
    else:
        lines.append("- None")
    lines.extend(["", "</details>"])
    lines.extend(
        [
            "",
            "## Runtime Governance Fixture Coverage",
            "",
            "| Suite | Status | Fixtures | Required Capability |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report.runtime_fixture_coverage:
        lines.append(
            f"| `evals/{row['suite']}` | {row['status']} | "
            f"{row['fixtures']} | `{row['required_capability']}` |"
        )
    lines.extend(["", "## Findings", ""])
    if report.findings:
        for finding in report.findings:
            lines.append(f"- `{finding.category}` `{finding.target}`: {finding.message}")
    else:
        lines.append("- None")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
