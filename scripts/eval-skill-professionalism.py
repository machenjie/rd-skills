#!/usr/bin/env python3
"""Evaluate ChangeForge skill professionalism signals.

This is an offline, warning-only authoring evaluation. It scans professional
skills and foundation capabilities, scores them across the professionalism
dimensions defined in docs/PROFESSIONALISM_ENHANCEMENT_STANDARD.md, and writes
Markdown and JSON reports. It never calls a model, never reaches the network,
and never edits skill sources.
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

from validation_utils import ValidationProblem, extract_section_body, load_yaml_file, parse_frontmatter


ROOT = Path(__file__).resolve().parents[1]
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
REGISTRY_DIR = ROOT / "src" / "registry"
DEFAULT_REPORTS_DIR = ROOT / "reports"
MARKDOWN_REPORT = "skill-professionalism-eval.md"
JSON_REPORT = "skill-professionalism-eval.json"
COVERAGE_MARKDOWN_REPORT = "professional-coverage-matrix.md"
COVERAGE_JSON_REPORT = "professional-coverage-matrix.json"
ROUTING_EVALS_DIR = ROOT / "evals" / "routing"
PROFESSIONAL_BENCHMARKS_DIR = ROOT / "evals" / "professional-benchmarks"

DIMENSIONS = (
    "trigger_accuracy",
    "mode_coverage",
    "stage_fit",
    "professional_depth",
    "proactive_trigger_quality",
    "failure_mode_coverage",
    "evidence_contract_strength",
    "output_actionability",
    "boundary_clarity",
    "reference_precision",
    "validation_obligation",
    "anti_bloat_control",
)

PROFESSIONAL_BODY_REVIEW_LIMIT = 350
CAPABILITY_BODY_REVIEW_LIMIT = 250
TOTAL_WARNING_THRESHOLD = 42
DIMENSION_WARNING_THRESHOLD = 2

ENHANCED_FOUNDATION_CAPABILITIES = {
    "engineering-stage-professionalism",
    "agent-execution-discipline",
    "implementation-structure-design",
    "code-clarity-maintainability",
    "skill-authoring-expert",
}

KEY_FOUNDATION_CAPABILITIES = {
    "failure-diagnosis",
    "refactoring",
    "code-review",
    "test-strategy",
    "unit-testing",
    "integration-testing",
    "contract-testing",
    "e2e-testing",
    "regression-testing",
    "logging-error-handling",
    "idempotency-retry-design",
    "async-job-design",
    "transaction-consistency",
    "cache-design",
    "message-queue-design",
    "relational-database",
    "observability",
    "release-rollback",
    "language-idiom-enforcement",
    "language-testing-strategy",
    "language-performance-safety",
    "go-professional-usage",
    "python-professional-usage",
    "typescript-professional-usage",
    "java-jvm-professional-usage",
    "rust-professional-usage",
    "cpp-professional-usage",
    "sql-professional-usage",
    "shell-cli-professional-usage",
}

SECTION_ALIASES = {
    "Evidence Contract": ("Evidence Contract", "Evidence Contract Answer Set"),
}

REQUIRED_SECTIONS = (
    "Mission",
    "When To Use",
    "Do Not Use When",
    "Mode Matrix",
    "Proactive Professional Triggers",
    "Evidence Contract",
    "Output Contract",
    "Failure Modes",
    "Quality Gate",
    "Reference Loading Policy",
    "Handoff",
    "Completion Criteria",
)

TRIGGER_FIELDS = (
    "Signal:",
    "Hidden risk:",
    "Required professional action:",
    "Route to:",
    "Evidence required:",
)

MODE_REQUIRED_FIELDS = {
    "trigger signals": ("trigger signals", "trigger signal"),
    "professional focus": ("professional focus",),
    "required evidence": ("required evidence", "evidence required"),
    "companion capabilities / gates": (
        "companion capabilities / gates",
        "companion capabilities",
        "companion gates",
    ),
    "skip guidance": ("skip guidance", "skip by default"),
}

EVIDENCE_OBLIGATIONS = {
    "boundaries inspected": ("boundaries inspected", "files and boundaries inspected"),
    "validation evidence": ("validation evidence", "validation command", "validation commands"),
    "what evidence proves": ("what evidence proves", "what the evidence proves"),
    "what evidence does not prove": (
        "what evidence does not prove",
        "what the evidence does not prove",
        "does not prove",
    ),
    "residual risk": ("residual risk",),
    "next gate": ("next gate", "next professional gate"),
    "reuse / placement rationale": (
        "reuse / placement rationale",
        "reuse and placement rationale",
        "placement rationale",
    ),
    "behavior preservation": ("behavior preservation", "behavior-preserving"),
}

BOUNDARY_TERMS = (
    "boundary",
    "boundaries",
    "trust",
    "tenant",
    "object",
    "permission",
    "owner",
    "ownership",
    "public/private",
    "rollback",
    "contract",
)

VALIDATION_TERMS = (
    "command",
    "test",
    "validator",
    "evidence",
    "output",
    "exit code",
    "artifact",
    "screenshot",
    "report",
)

REFERENCE_HINT_TERMS = (
    "Reference Loading Policy",
    "Load [",
    "load [",
    "references/",
    "read `references/",
)

GENERIC_PHRASES = (
    "best practices",
    "robust solution",
    "proper handling",
    "as needed",
    "where appropriate",
    "ensure quality",
    "industry standard",
    "check security",
    "add tests",
    "run tests",
    "skip if not needed",
    "do validation",
    "handle errors",
    "make it professional",
)

CONCRETE_ANCHOR_TERMS = (
    "accessibility",
    "acknowledgement",
    "api",
    "auth",
    "authorization",
    "backfill",
    "cache",
    "caller",
    "compatibility",
    "contract",
    "controller",
    "dashboard",
    "dedupe",
    "denied",
    "deployment",
    "duplicate",
    "event",
    "experiment",
    "fixture",
    "focus",
    "idempotency",
    "invalidation",
    "keyboard",
    "migration",
    "permission",
    "query",
    "queue",
    "race",
    "repository",
    "rollback",
    "schema",
    "service",
    "state",
    "tenant",
    "transaction",
    "validation command",
    "webhook",
    "wcag",
)

DIMENSION_SECTIONS = {
    "trigger_accuracy": "When To Use / Technical Selection Criteria",
    "mode_coverage": "Mode Matrix",
    "stage_fit": "Stage Fit / Mode Matrix",
    "professional_depth": "Professional rules",
    "proactive_trigger_quality": "Proactive Professional Triggers",
    "failure_mode_coverage": "Failure Modes",
    "evidence_contract_strength": "Evidence Contract",
    "output_actionability": "Output Contract",
    "boundary_clarity": "Boundary language",
    "reference_precision": "Reference Loading Policy",
    "validation_obligation": "Output/Evidence/Quality Gate",
    "anti_bloat_control": "Anti-bloat",
}

DUPLICATE_IGNORE_FRAGMENTS = (
    "do not load every reference by default",
    "selected capability reference path format",
    "pinned versions are review baselines, not permanent recommendations",
    "all five canonical answers are concrete",
    "answer schema: `agent-execution-discipline`",
    "`42 idempotency-retry-design`",
    "`82 solution-optimality-evaluation`",
    "| mode | trigger signals | professional focus | required evidence | companion capabilities",
)


@dataclass
class SkillScore:
    path: str
    name: str
    kind: str
    total: int
    dimensions: dict[str, int]
    warnings: list[str] = field(default_factory=list)
    likely_missing_sections: list[str] = field(default_factory=list)
    recommended_fixes: list[str] = field(default_factory=list)
    status: str = "weak"
    body_lines: int = 0


@dataclass
class EvalReport:
    generated_at: str
    skills_checked: int
    warning_count: int
    average_score: float
    items: list[SkillScore]
    duplicate_template_warnings: list[str] = field(default_factory=list)


@dataclass
class CoverageRow:
    name: str
    path: str
    kind: str
    mode_matrix: str
    proactive_triggers: str
    evidence_contract: str
    output_contract: str
    failure_modes: str
    quality_gate: str
    reference_loading_hint: str
    routing_coverage: str
    benchmark_coverage: str
    anti_bloat_status: str
    status: str
    score: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class CoverageMatrixReport:
    generated_at: str
    rows_checked: int
    rows: list[CoverageRow]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    reports_dir = args.reports_dir or DEFAULT_REPORTS_DIR
    registry_names = _load_registry_names()
    items = _evaluate_all(registry_names)
    duplicate_warnings = _duplicate_template_warnings(items)
    for item in items:
        matched_duplicate_warnings = [
            warning for warning in duplicate_warnings if warning.startswith(item.path + ":")
        ]
        item.warnings.extend(matched_duplicate_warnings)
        if matched_duplicate_warnings:
            item.dimensions["anti_bloat_control"] = max(
                0,
                item.dimensions.get("anti_bloat_control", 0) - 1,
            )
            item.dimensions["professional_depth"] = max(
                0,
                item.dimensions.get("professional_depth", 0) - 1,
            )
            item.total = sum(item.dimensions.values())
            item.recommended_fixes = _recommended_fixes(item.warnings, item.dimensions)
            item.status = _status(item.total, item.warnings, item.dimensions, item.kind, item.name)

    report = EvalReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        skills_checked=len(items),
        warning_count=sum(len(item.warnings) for item in items),
        average_score=round(sum(item.total for item in items) / max(len(items), 1), 2),
        items=items,
        duplicate_template_warnings=duplicate_warnings,
    )
    coverage_matrix = _build_coverage_matrix(items)
    written: list[Path] = []
    if not args.coverage_matrix:
        written.extend(_write_reports(report, reports_dir, args.format))
    written.extend(_write_coverage_matrix(coverage_matrix, reports_dir, args.format))
    print(
        f"eval-skill-professionalism: checked {report.skills_checked} item(s); "
        f"warnings={report.warning_count}; average_score={report.average_score:.2f}"
    )
    for path in written:
        print(f"- report: {path}")
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("all", "markdown", "json"),
        default="all",
        help="report format to write; default writes both Markdown and JSON",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="directory for generated reports; defaults to reports/",
    )
    parser.add_argument(
        "--coverage-matrix",
        action="store_true",
        help=(
            "write only coverage matrix reports; default writes both the main eval "
            "and coverage matrix reports"
        ),
    )
    return parser.parse_args(argv)


def _evaluate_all(registry_names: set[str]) -> list[SkillScore]:
    items: list[SkillScore] = []
    roots = (
        (PROFESSIONAL_SKILLS_DIR, "professional-skill"),
        (CAPABILITIES_DIR, "foundation-capability"),
    )
    for root, kind in roots:
        for skill_path in sorted(root.glob("*/SKILL.md")):
            if _is_authoring_template_path(skill_path):
                continue
            items.append(_evaluate_skill(skill_path, kind, registry_names))
    return items


def _is_authoring_template_path(path: Path) -> bool:
    """Exclude authoring templates and fixtures from runtime professionalism scores."""
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        relative = path
    return any(part.startswith("_") for part in relative.parts)


def _evaluate_skill(path: Path, kind: str, registry_names: set[str]) -> SkillScore:
    try:
        metadata, _raw, body = parse_frontmatter(path)
    except ValidationProblem as exc:
        warnings = [f"frontmatter parse failed: {exc}"]
        dimensions = {name: 0 for name in DIMENSIONS}
        return SkillScore(_rel(path), path.parent.name, kind, 0, dimensions, warnings)

    name = str(metadata.get("name") or path.parent.name)
    sections = {
        title: _extract_section(body, title)
        for title in (
            "Mission",
            "When To Use",
            "Do Not Use When",
            "Stage Fit",
            "Selection Rules",
            "Technical Selection Criteria",
            "Mode Matrix",
            "Proactive Professional Triggers",
            "Risk Escalation Rules",
            "Critical Details",
            "Failure Modes",
            "Reference Loading Policy",
            "Output Contract",
            "Evidence Contract",
            "Quality Gate",
            "Handoff",
            "Completion Criteria",
        )
    }
    likely_missing_sections = _likely_missing_sections(sections)
    dimensions = _score_dimensions(body, sections, kind, path)
    warnings = _warnings(body, sections, kind, path, dimensions, registry_names)
    total = sum(dimensions.values())
    body_lines = len(body.splitlines())
    recommended_fixes = _recommended_fixes(warnings, dimensions)
    status = _status(total, warnings, dimensions, kind, name)
    return SkillScore(
        _rel(path),
        name,
        kind,
        total,
        dimensions,
        warnings,
        likely_missing_sections,
        recommended_fixes,
        status,
        body_lines,
    )


def _score_dimensions(
    body: str,
    sections: dict[str, str],
    kind: str,
    path: Path,
) -> dict[str, int]:
    trigger_text = "\n".join(
        [sections["When To Use"], sections["Technical Selection Criteria"], sections["Risk Escalation Rules"]]
    )
    mode_text = sections["Mode Matrix"]
    proactive_text = sections["Proactive Professional Triggers"]
    failure_text = sections["Failure Modes"]
    output_text = sections["Output Contract"]
    evidence_text = sections["Evidence Contract"]
    quality_text = sections["Quality Gate"]
    reference_text = sections["Reference Loading Policy"]
    all_output = "\n".join([output_text, evidence_text, quality_text])

    scores = {
        "trigger_accuracy": _score_trigger_accuracy(trigger_text, proactive_text),
        "mode_coverage": _score_mode_coverage(mode_text, sections, kind, path),
        "stage_fit": _score_stage_fit(body, sections, kind),
        "professional_depth": _score_professional_depth(body, sections),
        "proactive_trigger_quality": _score_proactive_trigger_quality(proactive_text, kind),
        "failure_mode_coverage": _score_failure_modes(failure_text, kind),
        "evidence_contract_strength": _score_evidence_contract_strength(all_output, kind, path),
        "output_actionability": _score_output_actionability(output_text, all_output),
        "boundary_clarity": _score_keyword_coverage(body, BOUNDARY_TERMS),
        "reference_precision": _score_reference_precision(body, reference_text, path),
        "validation_obligation": _score_keyword_coverage(all_output, VALIDATION_TERMS),
        "anti_bloat_control": _score_anti_bloat(body, kind, reference_text, sections, path),
    }
    return scores


def _score_trigger_accuracy(trigger_text: str, proactive_text: str) -> int:
    text = f"{trigger_text}\n{proactive_text}".casefold()
    concrete_terms = sum(
        1
        for term in (
            "when",
            "escalate",
            "signal",
            "trigger",
            "route",
            "evidence",
            "boundary",
            "risk",
        )
        if term in text
    )
    broad_penalty = 1 if re.search(r"\b(any|everything|all capabilities|every relevant)\b", text) else 0
    return _clamp(concrete_terms - broad_penalty, 0, 5)


def _score_mode_coverage(
    mode_text: str,
    sections: dict[str, str],
    kind: str,
    path: Path,
) -> int:
    if kind != "professional-skill":
        if path.parent.name in ENHANCED_FOUNDATION_CAPABILITIES:
            text = f"{mode_text}\n{sections['Stage Fit']}\n{sections['Selection Rules']}".casefold()
            return _clamp(
                ("stage" in text)
                + ("selection" in text or "launch" in text)
                + ("skip" in text)
                + ("handoff" in text)
                + ("evidence" in text),
                0,
                5,
            )
        return 4
    if not mode_text:
        return 0
    analysis = _mode_matrix_analysis(mode_text)
    return _clamp(
        (analysis["required_fields_present"] == len(MODE_REQUIRED_FIELDS))
        + (analysis["row_count"] >= 4)
        + (analysis["quality_rows"] >= 2)
        + (analysis["quality_rows"] >= 4)
        + (analysis["evidence_rows"] >= 3 and analysis["route_rows"] >= 3 and analysis["skip_rows"] >= 3),
        0,
        5,
    )


def _score_evidence_contract_strength(text: str, kind: str, path: Path) -> int:
    if kind != "professional-skill" and path.parent.name not in ENHANCED_FOUNDATION_CAPABILITIES:
        folded = text.casefold()
        capability_terms = (
            "evidence",
            "validation",
            "boundaries inspected",
            "what evidence proves",
            "does not prove",
            "residual risk",
            "handoff",
        )
        return _clamp(sum(1 for term in capability_terms if term in folded), 0, 5)
    hits = _evidence_obligation_hits(text)
    score = _clamp(
        (len(hits) >= 2)
        + (len(hits) >= 4)
        + (len(hits) >= 6)
        + (len(hits) >= 7)
        + (len(hits) == len(EVIDENCE_OBLIGATIONS)),
        0,
        5,
    )
    if score >= 4 and _concrete_anchor_count(text) < 3:
        score = 3
    if _generic_best_practice_warning(text):
        score -= 1
    return _clamp(score, 0, 5)


def _score_stage_fit(body: str, sections: dict[str, str], kind: str) -> int:
    text = f"{sections['Stage Fit']}\n{sections['Mode Matrix']}\n{body}".casefold()
    terms = (
        "coding",
        "bug-fix",
        "debugging",
        "code-review",
        "refactoring",
        "testing",
        "release",
        "stage",
        "handoff",
    )
    score = min(sum(1 for term in terms if term in text), 5)
    if kind == "foundation-capability" and sections["Stage Fit"]:
        score = max(score, 4)
    return score


def _score_professional_depth(body: str, sections: dict[str, str]) -> int:
    text = body.casefold()
    signals = (
        "non-negotiable",
        "risk escalation",
        "critical details",
        "anti-examples",
        "failure modes",
        "quality gate",
        "evidence",
        "residual risk",
        "validation",
        "compatibility",
    )
    signal_hits = sum(1 for signal in signals if signal in text)
    concrete_hits = _concrete_anchor_count(body)
    score = _clamp(
        (signal_hits >= 3)
        + (signal_hits >= 6)
        + (concrete_hits >= 4)
        + (concrete_hits >= 8)
        + bool(sections.get("Failure Modes") and sections.get("Quality Gate")),
        0,
        5,
    )
    if _generic_best_practice_warning(body) and concrete_hits < 6:
        score -= 1
    return _clamp(score, 0, 5)


def _score_proactive_trigger_quality(proactive_text: str, kind: str) -> int:
    if not proactive_text:
        return 0 if kind == "professional-skill" else 1
    analysis = _trigger_quality_analysis(proactive_text)
    return _clamp(
        (analysis["complete_items"] >= 1)
        + (analysis["complete_items"] >= 3)
        + (analysis["concrete_items"] >= 1)
        + (analysis["concrete_items"] >= 3)
        + (analysis["concrete_items"] >= 5 or (analysis["item_count"] >= 2 and analysis["concrete_items"] == analysis["item_count"])),
        0,
        5,
    )


def _score_failure_modes(failure_text: str, kind: str) -> int:
    if not failure_text:
        return 0
    bullets = len(re.findall(r"^\s*[-*]\s+", failure_text, re.MULTILINE))
    table_rows = len(_table_data_rows(failure_text))
    count = bullets + table_rows
    return _clamp((count >= 3) + (count >= 6) + (count >= 8) + ("**" in failure_text) + (len(failure_text) > 300), 0, 5)


def _score_keyword_coverage(text: str, terms: tuple[str, ...]) -> int:
    folded = text.casefold()
    return _clamp(sum(1 for term in terms if term.casefold() in folded), 0, 5)


def _score_output_actionability(output_text: str, all_output: str) -> int:
    bullets = len(
        re.findall(
            r"^\s*[-*]\s+(?:-?\s*\*\*|`[a-z0-9_-]+`|[a-z0-9_ -]+:)",
            output_text,
            re.IGNORECASE | re.MULTILINE,
        )
    )
    verbs = sum(
        1
        for term in ("return", "decision", "approved", "blocked", "required", "evidence", "residual", "handoff")
        if term in all_output.casefold()
    )
    return _clamp((bullets >= 5) + (bullets >= 8) + (bullets >= 10) + min(verbs, 2), 0, 5)


def _score_reference_precision(body: str, reference_text: str, path: Path) -> int:
    ref_files = _reference_files(path)
    if not ref_files:
        return 4 if reference_text or "references/" not in body else 2
    linked = sum(1 for ref in ref_files if ref.name in body or f"references/{ref.name}" in body)
    policy = 1 if reference_text else 0
    targeted = 1 if any(term.casefold() in body.casefold() for term in REFERENCE_HINT_TERMS) else 0
    return _clamp(policy + targeted + min(linked, 3), 0, 5)


def _score_anti_bloat(
    body: str,
    kind: str,
    reference_text: str,
    sections: dict[str, str],
    path: Path,
) -> int:
    line_count = len(body.splitlines())
    limit = PROFESSIONAL_BODY_REVIEW_LIMIT if kind == "professional-skill" else CAPABILITY_BODY_REVIEW_LIMIT
    has_hint = bool(reference_text) or any(term.casefold() in body.casefold() for term in REFERENCE_HINT_TERMS)
    score = 5
    if line_count > limit:
        score -= 1
    if line_count > limit + 75:
        score -= 1
    if line_count > limit and not has_hint:
        score -= 1
    if _long_table_warning(body):
        score -= 1
    if _long_section_warning(sections):
        score -= 1
    if _paragraph_duplicate_warnings(body):
        score -= 1
    if _generic_best_practice_warning(body):
        score -= 1
    if _reference_files(path) and not has_hint:
        score -= 1
    return _clamp(score, 0, 5)


def _warnings(
    body: str,
    sections: dict[str, str],
    kind: str,
    path: Path,
    dimensions: dict[str, int],
    registry_names: set[str],
) -> list[str]:
    warnings: list[str] = []
    name = path.parent.name
    total = sum(dimensions.values())
    if kind == "professional-skill" and total < TOTAL_WARNING_THRESHOLD:
        warnings.append(f"total score {total}/60 is below warning threshold {TOTAL_WARNING_THRESHOLD}")
    elif name in ENHANCED_FOUNDATION_CAPABILITIES and total < TOTAL_WARNING_THRESHOLD - 6:
        warnings.append(f"enhanced capability score {total}/60 is below warning threshold {TOTAL_WARNING_THRESHOLD - 6}")

    for dimension, score in dimensions.items():
        if dimension not in _applicable_warning_dimensions(kind, name):
            continue
        if score <= DIMENSION_WARNING_THRESHOLD:
            section = DIMENSION_SECTIONS.get(dimension, dimension)
            warnings.append(
                f"{section} weak: {dimension} score {score}/5 needs review"
            )

    if kind == "professional-skill":
        if not sections["Mode Matrix"]:
            warnings.append("professional skill is missing Mode Matrix")
        else:
            mode_warning = _mode_matrix_warning(sections["Mode Matrix"])
            if mode_warning:
                warnings.append(mode_warning)
        if not sections["Proactive Professional Triggers"]:
            warnings.append("professional skill is missing Proactive Professional Triggers")
        combined_output = f"{sections['Output Contract']}\n{sections['Evidence Contract']}".casefold()
        missing_evidence = sorted(set(EVIDENCE_OBLIGATIONS) - _evidence_obligation_hits(combined_output))
        for term in missing_evidence:
            warnings.append(f"Evidence Contract is missing '{term}'")
        warnings.extend(
            _trigger_quality_warnings(
                sections["Proactive Professional Triggers"],
                registry_names,
            )
        )
        if not sections["Failure Modes"]:
            warnings.append("professional skill is missing Failure Modes")
        if not sections["Quality Gate"]:
            warnings.append("professional skill is missing Quality Gate")
    else:
        if not sections["Failure Modes"]:
            warnings.append("capability is missing Failure Modes")
        if not sections["Quality Gate"]:
            warnings.append("capability is missing Quality Gate")

    limit = PROFESSIONAL_BODY_REVIEW_LIMIT if kind == "professional-skill" else CAPABILITY_BODY_REVIEW_LIMIT
    has_ref_hint = sections["Reference Loading Policy"] or any(
        term.casefold() in body.casefold() for term in REFERENCE_HINT_TERMS
    )
    if len(body.splitlines()) > limit and not has_ref_hint:
        warnings.append("SKILL.md body is over governance review limit and lacks a reference loading hint")

    long_table = _long_table_warning(body)
    if long_table:
        warnings.append(long_table)
    long_section = _long_section_warning(sections)
    if long_section:
        warnings.append(long_section)

    warnings.extend(_paragraph_duplicate_warnings(body))
    generic_warning = _generic_best_practice_warning(body)
    if generic_warning:
        warnings.append(generic_warning)
    warnings.extend(_reference_warnings(body, sections, path, kind))
    return warnings


def _status(
    total: int,
    warnings: list[str],
    dimensions: dict[str, int],
    kind: str,
    name: str,
) -> str:
    if kind == "foundation-capability" and name not in KEY_FOUNDATION_CAPABILITIES | ENHANCED_FOUNDATION_CAPABILITIES:
        return "acceptable" if total >= 30 else "weak"
    low_required = any(
        dimensions.get(dimension, 0) <= 2
        for dimension in (
            "mode_coverage",
            "proactive_trigger_quality",
            "evidence_contract_strength",
            "output_actionability",
            "reference_precision",
            "anti_bloat_control",
        )
        if kind == "professional-skill" or dimension not in {"mode_coverage", "proactive_trigger_quality"}
    )
    if total >= 54 and not warnings:
        return "sample-grade"
    if total >= 42 and not low_required:
        return "acceptable"
    if total >= 34 or warnings:
        return "needs-review"
    return "weak"


def _recommended_fixes(warnings: list[str], dimensions: dict[str, int]) -> list[str]:
    fixes: list[str] = []
    joined = "\n".join(warnings).casefold()
    if "mode matrix" in joined or dimensions.get("mode_coverage", 0) <= 2:
        fixes.append("Add or tighten a domain-specific Mode Matrix with evidence and skip guidance.")
    if "proactive professional triggers" in joined or dimensions.get("proactive_trigger_quality", 0) <= 2:
        fixes.append("Rewrite triggers as hidden-risk escalators with Signal, Hidden risk, Action, Route, and Evidence.")
    if "output/evidence contract" in joined or dimensions.get("evidence_contract_strength", 0) <= 2:
        fixes.append("Strengthen Output/Evidence Contract with boundaries, validation evidence, residual risk, and next gate.")
    if "reference" in joined or dimensions.get("reference_precision", 0) <= 2:
        fixes.append("Add targeted reference loading hints or link unreferenced skill references.")
    if "bloat" in joined or "duplicated" in joined or dimensions.get("anti_bloat_control", 0) <= 2:
        fixes.append("Move low-frequency tables/examples into owned references and remove duplicated template prose.")
    if not fixes and warnings:
        fixes.append("Review listed warnings and add concrete evidence, owner, or skip rationale.")
    return fixes[:5]


def _applicable_warning_dimensions(kind: str, name: str) -> set[str]:
    if kind == "professional-skill":
        return set(DIMENSIONS)
    if name not in ENHANCED_FOUNDATION_CAPABILITIES:
        return set()
    dimensions = {
        "professional_depth",
        "failure_mode_coverage",
        "output_actionability",
        "boundary_clarity",
        "reference_precision",
        "validation_obligation",
        "anti_bloat_control",
        "evidence_contract_strength",
    }
    if name == "engineering-stage-professionalism":
        dimensions |= {"mode_coverage", "stage_fit"}
    return dimensions


def _mode_matrix_warning(mode_text: str) -> str | None:
    analysis = _mode_matrix_analysis(mode_text)
    missing = sorted(set(MODE_REQUIRED_FIELDS) - set(analysis["fields"]))
    if missing:
        return "Mode Matrix lacks required professional columns: " + ", ".join(missing)
    if analysis["row_count"] < 4:
        return "Mode Matrix has too few mode rows to distinguish engineering contexts"
    if analysis["quality_rows"] < 3:
        return "Mode Matrix rows are too generic; trigger, focus, evidence, companion route, and skip guidance must be concrete"
    if min(analysis["evidence_rows"], analysis["route_rows"], analysis["skip_rows"]) < 3:
        return "Mode Matrix lacks concrete evidence, companion capability/gate, or skip-guidance cells"
    return None


def _trigger_quality_warnings(proactive_text: str, registry_names: set[str]) -> list[str]:
    if not proactive_text:
        return []
    warnings: list[str] = []
    triggers = _trigger_items(proactive_text)
    analysis = _trigger_quality_analysis(proactive_text)
    if len(triggers) < 3:
        warnings.append(f"Proactive Professional Triggers has too few trigger items: {len(triggers)}")
    if analysis["concrete_items"] < max(1, min(3, len(triggers))):
        warnings.append(
            "Proactive Professional Triggers are too generic; each trigger needs concrete hidden risk, route, and evidence"
        )
    for index, trigger in enumerate(triggers, start=1):
        folded = trigger.casefold()
        missing = [
            label
            for label in (
                "signal",
                "hidden risk",
                "required professional action",
                "route to",
                "evidence required",
            )
            if label not in folded
        ]
        if missing:
            warnings.append(
                f"Proactive Professional Trigger {index} missing fields: " + ", ".join(missing)
            )
        route = _route_field(trigger)
        if route and "`" not in route:
            warnings.append(f"Proactive Professional Trigger {index} route lacks explicit backticked names")
        if not _trigger_item_is_concrete(trigger):
            warnings.append(
                f"Proactive Professional Trigger {index} lacks concrete hidden risk, action, route, or evidence"
            )
        for route_name in re.findall(r"`([^`]+)`", route):
            if route_name not in registry_names:
                warnings.append(
                    f"Proactive Professional Trigger {index} routes to unknown skill/capability '{route_name}'"
                )
    folded = proactive_text.casefold()
    if "checklist" in folded and "hidden risk" not in folded:
        warnings.append("Proactive Professional Triggers reads like a checklist instead of hidden-risk escalation")
    return warnings


def _duplicate_template_warnings(items: list[SkillScore]) -> list[str]:
    line_to_paths: dict[str, set[str]] = {}
    evidence_to_paths: dict[str, set[str]] = {}
    for item in items:
        path = ROOT / item.path
        try:
            _meta, _raw, body = parse_frontmatter(path)
        except ValidationProblem:
            continue
        evidence_contract = _normalize_duplicate_section(_extract_section(body, "Evidence Contract"))
        if evidence_contract:
            evidence_to_paths.setdefault(evidence_contract, set()).add(item.path)
        for line in body.splitlines():
            normalized = _normalize_duplicate_line(line)
            if not normalized:
                continue
            line_to_paths.setdefault(normalized, set()).add(item.path)
    warnings: list[str] = []
    for normalized, paths in line_to_paths.items():
        if len(paths) < 7:
            continue
        if any(fragment in normalized for fragment in DUPLICATE_IGNORE_FRAGMENTS):
            continue
        for path in sorted(paths):
            warnings.append(f"{path}: large repeated template-like line appears in {len(paths)} files: {normalized[:90]}")
    for normalized, paths in evidence_to_paths.items():
        if len(paths) < 4:
            continue
        for path in sorted(paths):
            warnings.append(
                f"{path}: Evidence Contract appears mechanically duplicated across {len(paths)} files"
            )
    return warnings


def _trigger_items(proactive_text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for line in proactive_text.splitlines():
        if line.lstrip().startswith("- **Signal:**"):
            if current:
                items.append("\n".join(current).strip())
            current = [line]
        elif current:
            if re.match(r"^\s{0,3}#{1,6}\s+", line):
                break
            current.append(line)
    if current:
        items.append("\n".join(current).strip())
    return items


def _trigger_quality_analysis(proactive_text: str) -> dict[str, int]:
    items = _trigger_items(proactive_text)
    complete_items = 0
    concrete_items = 0
    for item in items:
        fields = {
            field_name.rstrip(":").casefold(): _trigger_field_value(item, field_name.rstrip(":"))
            for field_name in TRIGGER_FIELDS
        }
        if all(fields.values()):
            complete_items += 1
        if _trigger_item_is_concrete(item):
            concrete_items += 1
    return {
        "item_count": len(items),
        "complete_items": complete_items,
        "concrete_items": concrete_items,
    }


def _trigger_item_is_concrete(trigger: str) -> bool:
    signal = _trigger_field_value(trigger, "Signal")
    hidden_risk = _trigger_field_value(trigger, "Hidden risk")
    action = _trigger_field_value(trigger, "Required professional action")
    route = _trigger_field_value(trigger, "Route to")
    evidence = _trigger_field_value(trigger, "Evidence required")
    return all(
        (
            _is_concrete_signal(signal),
            _is_concrete_risk(hidden_risk),
            _is_concrete_action(action),
            bool(re.search(r"`[^`]+`", route)),
            _is_concrete_evidence(evidence),
        )
    )


def _trigger_field_value(trigger: str, field_name: str) -> str:
    next_fields = "|".join(
        re.escape(field.rstrip(":")) for field in TRIGGER_FIELDS if field.rstrip(":") != field_name
    )
    pattern = rf"\*\*{re.escape(field_name)}:\*\*(.*?)(?:\n\s*\*\*(?:{next_fields}):\*\*|\Z)"
    match = re.search(pattern, trigger, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def _route_field(trigger: str) -> str:
    match = re.search(
        r"\*\*Route to:\*\*(.*?)(?:\*\*Evidence required:\*\*|$)",
        trigger,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _mode_matrix_analysis(mode_text: str) -> dict[str, Any]:
    headers, rows = _table_parts(mode_text)
    folded_headers = [header.casefold() for header in headers]
    fields = {
        field_name
        for field_name, aliases in MODE_REQUIRED_FIELDS.items()
        if any(alias in header for alias in aliases for header in folded_headers)
    }
    indices = {
        field_name: _header_index(folded_headers, aliases)
        for field_name, aliases in MODE_REQUIRED_FIELDS.items()
    }
    quality_rows = 0
    evidence_rows = 0
    route_rows = 0
    skip_rows = 0
    for row in rows:
        values = {name: _cell_value(row, index) for name, index in indices.items()}
        evidence_ok = _is_concrete_evidence(values["required evidence"])
        route_ok = _is_concrete_route(values["companion capabilities / gates"])
        skip_ok = _is_concrete_skip(values["skip guidance"])
        if evidence_ok:
            evidence_rows += 1
        if route_ok:
            route_rows += 1
        if skip_ok:
            skip_rows += 1
        if all(
            (
                _is_concrete_signal(values["trigger signals"]),
                _is_concrete_focus(values["professional focus"]),
                evidence_ok,
                route_ok,
                skip_ok,
            )
        ):
            quality_rows += 1
    return {
        "fields": fields,
        "required_fields_present": len(fields),
        "row_count": len(rows),
        "quality_rows": quality_rows,
        "evidence_rows": evidence_rows,
        "route_rows": route_rows,
        "skip_rows": skip_rows,
    }


def _table_parts(text: str) -> tuple[list[str], list[list[str]]]:
    table_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    headers: list[str] = []
    rows: list[list[str]] = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not headers:
            headers = cells
            continue
        if set("".join(cells).strip()) <= {"-", ":", " "}:
            continue
        rows.append(cells)
    return headers, rows


def _header_index(headers: list[str], aliases: tuple[str, ...]) -> int | None:
    for index, header in enumerate(headers):
        if any(alias in header for alias in aliases):
            return index
    return None


def _cell_value(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def _evidence_obligation_hits(text: str) -> set[str]:
    folded = text.casefold()
    return {
        obligation
        for obligation, aliases in EVIDENCE_OBLIGATIONS.items()
        if any(alias in folded for alias in aliases)
    }


def _is_generic_text(text: str) -> bool:
    folded = re.sub(r"\s+", " ", text.casefold()).strip()
    if not folded:
        return True
    if folded in {"n/a", "none", "todo", "tbd", "same", "yes", "no"}:
        return True
    if len(folded) < 10:
        return True
    return any(phrase in folded for phrase in GENERIC_PHRASES)


def _is_concrete_signal(text: str) -> bool:
    return bool(text) and not _is_generic_text(text) and (len(text) >= 16 or _concrete_anchor_count(text) >= 1)


def _is_concrete_focus(text: str) -> bool:
    return bool(text) and not _is_generic_text(text) and (len(text) >= 18 or _concrete_anchor_count(text) >= 1)


def _is_concrete_risk(text: str) -> bool:
    folded = text.casefold()
    risk_terms = (
        "break",
        "collision",
        "corrupt",
        "duplicate",
        "forged",
        "hidden",
        "inconsistent",
        "leak",
        "loss",
        "missing",
        "pollution",
        "replay",
        "rollback",
        "silent",
        "stale",
        "unverified",
        "wrong",
    )
    return bool(text) and not _is_generic_text(text) and (
        _concrete_anchor_count(text) >= 1 or any(term in folded for term in risk_terms)
    )


def _is_concrete_action(text: str) -> bool:
    folded = text.casefold()
    action_terms = (
        "block",
        "classify",
        "compare",
        "document",
        "evaluate",
        "inspect",
        "model",
        "preserve",
        "prove",
        "require",
        "rewrite",
        "route",
        "scan",
        "split",
        "triage",
        "verify",
    )
    return bool(text) and not _is_generic_text(text) and any(term in folded for term in action_terms)


def _is_concrete_evidence(text: str) -> bool:
    folded = text.casefold()
    evidence_terms = (
        "command",
        "contract",
        "cve",
        "denied",
        "diff",
        "exit code",
        "fixture",
        "log",
        "map",
        "matrix",
        "metric",
        "owner",
        "output",
        "plan",
        "procedure",
        "report",
        "rollback",
        "scan",
        "schema",
        "screenshot",
        "test",
        "threshold",
        "trace",
        "typecheck",
        "validation",
        "walkthrough",
    )
    return bool(text) and not _is_generic_text(text) and (
        _concrete_anchor_count(text) >= 1 or any(term in folded for term in evidence_terms)
    )


def _is_concrete_route(text: str) -> bool:
    folded = text.casefold()
    return bool(text) and not _is_generic_text(text) and (
        bool(re.search(r"`[^`]+`", text))
        or "-gate" in folded
        or "-design" in folded
        or "-builder" in folded
        or "-reviewer" in folded
    )


def _is_concrete_skip(text: str) -> bool:
    folded = text.casefold()
    return bool(text) and not _is_generic_text(text) and (
        len(text.strip()) >= 18
        or any(
        term in folded
        for term in (
            "before",
            "defer",
            "do not",
            "only when",
            "not needed",
            "skip",
            "unless",
            "until",
        )
    )
    )


def _concrete_anchor_count(text: str) -> int:
    folded = text.casefold()
    return sum(1 for term in CONCRETE_ANCHOR_TERMS if term in folded)


def _reference_warnings(
    body: str,
    sections: dict[str, str],
    path: Path,
    kind: str,
) -> list[str]:
    refs = _reference_files(path)
    if not refs:
        return []
    warnings: list[str] = []
    has_loading_hint = bool(sections["Reference Loading Policy"]) or any(
        term.casefold() in body.casefold() for term in REFERENCE_HINT_TERMS
    )
    if kind == "professional-skill" and not has_loading_hint:
        warnings.append("skill has references but lacks a reference loading hint")
    for ref in refs:
        # Generic generated checklists exist across the mesh; warn only when the
        # skill has no loading hint at all. Non-checklist references must always
        # be cited from the body so they stay targeted.
        if ref.name == "checklist.md":
            if kind == "professional-skill" and not has_loading_hint:
                warnings.append(f"reference '{ref.relative_to(path.parent)}' is not governed by a loading hint")
            continue
        if ref.name not in body and f"references/{ref.name}" not in body:
            warnings.append(f"reference '{ref.relative_to(path.parent)}' is not linked from SKILL.md body")
    return warnings


def _long_table_warning(body: str) -> str | None:
    longest = 0
    current = 0
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    if longest >= 16:
        return f"long Markdown table in SKILL.md body ({longest} rows); consider moving deep table to references"
    return None


def _long_section_warning(sections: dict[str, str]) -> str | None:
    for title, text in sections.items():
        if not text:
            continue
        line_count = len(text.splitlines())
        if line_count >= 120:
            return f"long section '{title}' in SKILL.md body ({line_count} lines); move deep material to references"
    return None


def _paragraph_duplicate_warnings(body: str) -> list[str]:
    paragraphs = [
        _normalize_duplicate_section(paragraph)
        for paragraph in re.split(r"\n\s*\n", body)
    ]
    counts: dict[str, int] = {}
    for paragraph in paragraphs:
        if not paragraph:
            continue
        counts[paragraph] = counts.get(paragraph, 0) + 1
    return [
        "repeated paragraph-like content detected inside SKILL.md body"
        for count in counts.values()
        if count >= 2
    ][:1]


def _generic_best_practice_warning(body: str) -> str | None:
    folded = body.casefold()
    generic_hits = sum(
        1
        for phrase in (
            "best practices",
            "robust solution",
            "proper handling",
            "as needed",
            "where appropriate",
            "ensure quality",
            "industry standard",
        )
        if phrase in folded
    )
    evidence_hits = sum(1 for term in ("evidence", "risk", "boundary", "validation") if term in folded)
    if generic_hits >= 4 and evidence_hits < 3:
        return "generic best-practices wording dominates without enough evidence or boundary anchors"
    return None


def _extract_section(body: str, title: str) -> str:
    for candidate in SECTION_ALIASES.get(title, (title,)):
        text = extract_section_body(body, candidate)
        if text is not None:
            return text
    return ""


def _likely_missing_sections(sections: dict[str, str]) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if not sections.get(section)]


def _load_registry_names() -> set[str]:
    names: set[str] = set()
    for file_name, key in (
        ("skills.yaml", "skills"),
        ("capabilities.yaml", "capabilities"),
        ("domain-extensions.yaml", "domain_extensions"),
    ):
        path = REGISTRY_DIR / file_name
        if not path.is_file():
            continue
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            continue
        entries = data.get(key) if isinstance(data, dict) else None
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                names.add(entry["name"].strip())
    return names


def _normalize_duplicate_line(line: str) -> str:
    stripped = re.sub(r"\s+", " ", line.strip()).casefold()
    if len(stripped) < 90:
        return ""
    if stripped.startswith(("- l1 changes:", "- l2 changes:", "- l3 changes:", "- l4/l5 changes:")):
        return ""
    if any(fragment in stripped for fragment in DUPLICATE_IGNORE_FRAGMENTS):
        return ""
    return stripped


def _normalize_duplicate_section(text: str) -> str:
    stripped = re.sub(r"\s+", " ", text.strip()).casefold()
    if len(stripped) < 180:
        return ""
    if any(fragment in stripped for fragment in DUPLICATE_IGNORE_FRAGMENTS):
        return ""
    return stripped


def _build_coverage_matrix(items: list[SkillScore]) -> CoverageMatrixReport:
    routing_counts = _coverage_counts_from_routing()
    benchmark_counts = _coverage_counts_from_benchmarks()
    rows: list[CoverageRow] = []
    for item in sorted(items, key=lambda entry: (entry.kind, entry.name)):
        if item.kind == "foundation-capability" and item.name not in KEY_FOUNDATION_CAPABILITIES:
            continue
        path = ROOT / item.path
        try:
            _metadata, _raw, body = parse_frontmatter(path)
        except ValidationProblem:
            body = ""
        sections = {
            title: _extract_section(body, title)
            for title in (
                "Stage Fit",
                "Mode Matrix",
                "Proactive Professional Triggers",
                "Evidence Contract",
                "Output Contract",
                "Failure Modes",
                "Quality Gate",
                "Reference Loading Policy",
            )
        }
        if item.kind == "foundation-capability" and item.name not in ENHANCED_FOUNDATION_CAPABILITIES:
            mode_matrix = "n/a"
            proactive = "n/a"
        else:
            mode_matrix = _coverage_cell(
                _score_mode_coverage(sections["Mode Matrix"], sections, item.kind, path) >= 4,
                partial=bool(sections["Mode Matrix"]) or bool(sections["Stage Fit"]),
            )
            proactive = _coverage_cell(
                _score_proactive_trigger_quality(
                    sections["Proactive Professional Triggers"],
                    item.kind,
                )
                >= 4,
                partial=bool(sections["Proactive Professional Triggers"]),
            )
        evidence = _coverage_cell(
            _score_evidence_contract_strength(
                sections["Output Contract"] + "\n" + sections["Evidence Contract"],
                item.kind,
                path,
            )
            >= 4,
            partial=bool(sections["Evidence Contract"]) or bool(sections["Output Contract"]),
        )
        output_contract = _coverage_cell(
            _score_output_actionability(sections["Output Contract"], sections["Output Contract"]) >= 4,
            partial=bool(sections["Output Contract"]),
        )
        failure_modes = _coverage_cell(_score_failure_modes(sections["Failure Modes"], item.kind) >= 3)
        quality_gate = _coverage_cell(bool(sections["Quality Gate"]))
        reference_hint = _coverage_cell(
            bool(sections["Reference Loading Policy"])
            or any(term.casefold() in body.casefold() for term in REFERENCE_HINT_TERMS),
            partial=bool(_reference_files(path)),
        )
        routing_coverage = _coverage_count_cell(routing_counts.get(item.name, 0))
        benchmark_coverage = _coverage_count_cell(benchmark_counts.get(item.name, 0))
        if item.name == "change-forge-router":
            routing_coverage = (
                "n/a (router owns routing fixture corpus; "
                f"eval-routing cases={_routing_fixture_count()})"
            )
            benchmark_coverage = "n/a (covered by eval-routing and agent-behavior)"
        rows.append(
            CoverageRow(
                name=item.name,
                path=item.path,
                kind=item.kind,
                mode_matrix=mode_matrix,
                proactive_triggers=proactive,
                evidence_contract=evidence,
                output_contract=output_contract,
                failure_modes=failure_modes,
                quality_gate=quality_gate,
                reference_loading_hint=reference_hint,
                routing_coverage=routing_coverage,
                benchmark_coverage=benchmark_coverage,
                anti_bloat_status=_anti_bloat_status(item.dimensions.get("anti_bloat_control", 0)),
                status=item.status,
                score=item.total,
                warnings=item.warnings,
            )
        )
    return CoverageMatrixReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        rows_checked=len(rows),
        rows=rows,
    )


def _coverage_cell(ok: bool, partial: bool = False) -> str:
    if ok:
        return "yes"
    if partial:
        return "partial"
    return "no"


def _coverage_count_cell(count: int) -> str:
    return f"yes ({count})" if count else "no"


def _routing_fixture_count() -> int:
    if not ROUTING_EVALS_DIR.is_dir():
        return 0
    return sum(1 for path in ROUTING_EVALS_DIR.glob("*.yaml") if path.is_file())


def _anti_bloat_status(score: int) -> str:
    if score >= 4:
        return "ok"
    if score >= 3:
        return "needs-review"
    return "bloat-risk"


def _coverage_counts_from_routing() -> dict[str, int]:
    counts: dict[str, int] = {}
    if not ROUTING_EVALS_DIR.is_dir():
        return counts
    for path in ROUTING_EVALS_DIR.glob("*.yaml"):
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            continue
        expected = data.get("expected") if isinstance(data, dict) else None
        if not isinstance(expected, dict):
            continue
        for field_name in ("skills", "capabilities"):
            for name in _as_string_list(expected.get(field_name)):
                counts[name] = counts.get(name, 0) + 1
    return counts


def _coverage_counts_from_benchmarks() -> dict[str, int]:
    counts: dict[str, int] = {}
    if not PROFESSIONAL_BENCHMARKS_DIR.is_dir():
        return counts
    for path in PROFESSIONAL_BENCHMARKS_DIR.rglob("expected.yaml"):
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            continue
        if not isinstance(data, dict):
            continue
        for name in _as_string_list(data.get("expected_professional_skill")):
            counts[name] = counts.get(name, 0) + 1
        for name in _as_string_list(data.get("expected_capabilities")):
            counts[name] = counts.get(name, 0) + 1
    return counts


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _write_reports(report: EvalReport, reports_dir: Path, report_format: str) -> list[Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if report_format in {"all", "markdown"}:
        path = reports_dir / MARKDOWN_REPORT
        path.write_text(_render_markdown(report), encoding="utf-8")
        written.append(path)
    if report_format in {"all", "json"}:
        path = reports_dir / JSON_REPORT
        payload = asdict(report)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _write_coverage_matrix(
    report: CoverageMatrixReport,
    reports_dir: Path,
    report_format: str,
) -> list[Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if report_format in {"all", "markdown"}:
        path = reports_dir / COVERAGE_MARKDOWN_REPORT
        path.write_text(_render_coverage_markdown(report), encoding="utf-8")
        written.append(path)
    if report_format in {"all", "json"}:
        path = reports_dir / COVERAGE_JSON_REPORT
        path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _render_markdown(report: EvalReport) -> str:
    lines = [
        "# Skill Professionalism Evaluation",
        "",
        f"- Generated: {report.generated_at}",
        f"- Skills/capabilities checked: {report.skills_checked}",
        f"- Warning count: {report.warning_count}",
        f"- Average score: {report.average_score:.2f}/60",
        "",
        "## Scores",
        "",
        "| Item | Kind | Score | Status | Missing Sections | Warnings |",
        "| --- | --- | ---: | --- | ---: | ---: |",
    ]
    for item in sorted(report.items, key=lambda entry: (entry.total, entry.path)):
        lines.append(
            f"| `{item.path}` | {item.kind} | {item.total}/60 | {item.status} | "
            f"{len(item.likely_missing_sections)} | {len(item.warnings)} |"
        )

    lines.extend(["", "## Warnings", ""])
    any_warning = False
    for item in sorted(report.items, key=lambda entry: (entry.path)):
        if not item.warnings:
            continue
        any_warning = True
        lines.append(f"### `{item.path}`")
        if item.likely_missing_sections:
            lines.append("- likely missing sections: " + ", ".join(item.likely_missing_sections))
        for warning in item.warnings:
            lines.append(f"- {warning}")
        if item.recommended_fixes:
            lines.append("")
            lines.append("Recommended fixes:")
            for fix in item.recommended_fixes:
                lines.append(f"- {fix}")
        lines.append("")
    if not any_warning:
        lines.append("No warnings.")
    return "\n".join(lines).rstrip() + "\n"


def _render_coverage_markdown(report: CoverageMatrixReport) -> str:
    lines = [
        "# Professional Coverage Matrix",
        "",
        f"- Generated: {report.generated_at}",
        f"- Rows checked: {report.rows_checked}",
        "",
        "| Item | Kind | Mode Matrix | Proactive Triggers | Evidence Contract | Output Contract | Failure Modes | Quality Gate | Reference Loading Hint | Routing Coverage | Benchmark Coverage | Anti-bloat Status | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report.rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.name}`",
                    row.kind,
                    row.mode_matrix,
                    row.proactive_triggers,
                    row.evidence_contract,
                    row.output_contract,
                    row.failure_modes,
                    row.quality_gate,
                    row.reference_loading_hint,
                    row.routing_coverage,
                    row.benchmark_coverage,
                    row.anti_bloat_status,
                    row.status,
                ]
            )
            + " |"
        )
    weak = [
        row
        for row in report.rows
        if row.status in {"weak", "needs-review"} or row.anti_bloat_status == "bloat-risk"
    ]
    if weak:
        lines.extend(["", "## Weak Spots", ""])
        for row in weak:
            gaps = [
                label
                for label, value in (
                    ("Mode Matrix", row.mode_matrix),
                    ("Proactive Triggers", row.proactive_triggers),
                    ("Evidence Contract", row.evidence_contract),
                    ("Output Contract", row.output_contract),
                    ("Failure Modes", row.failure_modes),
                    ("Quality Gate", row.quality_gate),
                    ("Reference Loading Hint", row.reference_loading_hint),
                    ("Routing Coverage", row.routing_coverage),
                    ("Benchmark Coverage", row.benchmark_coverage),
                    ("Anti-bloat Status", row.anti_bloat_status),
                )
                if value in {"no", "weak", "bloat-risk"}
            ]
            lines.append(f"- `{row.name}`: {', '.join(gaps) if gaps else 'score/status needs review'}")
    return "\n".join(lines).rstrip() + "\n"


def _table_data_rows(text: str) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        if set(stripped.replace("|", "").strip()) <= {"-", ":", " "}:
            continue
        if "mode" in stripped.casefold() and "trigger" in stripped.casefold():
            continue
        rows.append(stripped)
    return rows


def _contains_all(text: str, terms: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return all(term in folded for term in terms)


def _reference_files(path: Path) -> list[Path]:
    refs_dir = path.parent / "references"
    if not refs_dir.is_dir():
        return []
    return sorted(ref for ref in refs_dir.glob("*.md") if ref.is_file())


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


if __name__ == "__main__":
    raise SystemExit(main())
