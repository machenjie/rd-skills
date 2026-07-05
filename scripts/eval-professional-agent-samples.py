#!/usr/bin/env python3
"""Evaluate professional agent-output samples without calling an LLM.

Samples under evals/agent-behavior/professional-samples/ capture real or
realistic agent outputs and the professional obligations they should satisfy.
The evaluator treats raw output as untrusted text: it only performs deterministic
coverage checks against the sample expectation and writes advisory reports by
default. Use --strict to fail on missing obligations.
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

from telemetry_utils import extract_route_manifest, manifest_string_list
from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLES_DIR = ROOT / "evals" / "agent-behavior" / "professional-samples"
DEFAULT_REPORTS_DIR = ROOT / "reports"
MARKDOWN_REPORT = "professional-agent-samples-report.md"
JSON_REPORT = "professional-agent-samples-report.json"
PROMOTION_STATUSES = {"candidate", "promoted", "rejected"}


@dataclass
class SampleResult:
    sample_id: str
    path: str
    promotion_status: str = ""
    human_review_required: bool | None = None
    selected_skills_missing: list[str] = field(default_factory=list)
    selected_capabilities_missing: list[str] = field(default_factory=list)
    required_references_missing: list[str] = field(default_factory=list)
    required_quality_gates_missing: list[str] = field(default_factory=list)
    professional_obligations_missing: list[str] = field(default_factory=list)
    forbidden_behavior_hits: list[str] = field(default_factory=list)
    missing_actual_fields: list[str] = field(default_factory=list)
    schema_errors: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def ok(self) -> bool:
        return not (
            self.selected_skills_missing
            or self.selected_capabilities_missing
            or self.required_references_missing
            or self.required_quality_gates_missing
            or self.professional_obligations_missing
            or self.forbidden_behavior_hits
            or self.missing_actual_fields
            or self.schema_errors
        )


@dataclass
class AgentSampleReport:
    generated_at: str
    samples_checked: int
    mode: str
    strict: bool
    warnings: int
    failures: int
    results: list[SampleResult]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    sample_files = _collect_sample_files(args.samples_dir)
    results: list[SampleResult] = []
    for path in sample_files:
        try:
            data = load_yaml_file(path)
        except (OSError, ValidationProblem) as exc:
            results.append(
                SampleResult(
                    sample_id=_rel(path),
                    path=_rel(path),
                    schema_errors=[f"failed to load sample: {exc}"],
                )
            )
            continue
        result = _evaluate_sample(path, data)
        if _matches_filter(result, args):
            results.append(result)

    failures = sum(1 for result in results if not result.ok)
    report = AgentSampleReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        samples_checked=len(results),
        mode=_mode(args),
        strict=bool(args.strict),
        warnings=failures,
        failures=failures if args.strict else 0,
        results=results,
    )
    written = _write_reports(report, args.reports_dir, args.format)
    print(
        f"eval-professional-agent-samples: checked {report.samples_checked} sample(s); "
        f"warnings={report.warnings}; strict={str(report.strict).lower()}"
    )
    for path in written:
        print(f"- report: {path}")
    if args.strict and failures:
        for result in results:
            if not result.ok:
                print(
                    f"eval-professional-agent-samples: ERROR: {result.path}: "
                    + "; ".join(_result_findings(result)),
                    file=sys.stderr,
                )
        return 1
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-dir", type=Path, default=DEFAULT_SAMPLES_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--promoted-only", action="store_true")
    parser.add_argument("--candidates-only", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--format",
        choices=("all", "markdown", "json"),
        default="all",
        help="report format to write; default writes Markdown and JSON",
    )
    args = parser.parse_args(argv)
    if args.promoted_only and args.candidates_only:
        parser.error("--promoted-only and --candidates-only are mutually exclusive")
    return args


def _collect_sample_files(samples_dir: Path) -> list[Path]:
    if not samples_dir.is_dir():
        return []
    return sorted(
        path
        for path in samples_dir.rglob("*.yaml")
        if path.is_file() and not path.name.startswith(".")
    )


def _matches_filter(result: SampleResult, args: argparse.Namespace) -> bool:
    if args.promoted_only:
        return result.promotion_status == "promoted"
    if args.candidates_only:
        return result.promotion_status == "candidate"
    return True


def _evaluate_sample(path: Path, data: Any) -> SampleResult:
    result = SampleResult(sample_id=_rel(path), path=_rel(path))
    if not isinstance(data, dict):
        result.schema_errors.append("sample must be a mapping")
        return result

    sample_id = _string(data.get("id"))
    result.sample_id = sample_id or _rel(path)
    for field_name in ("id", "description", "prompt"):
        if not _string(data.get(field_name)):
            result.schema_errors.append(f"missing string '{field_name}'")

    expected = data.get("expected")
    actual = data.get("actual")
    review = data.get("review")
    if not isinstance(expected, dict):
        result.schema_errors.append("missing 'expected' mapping")
        expected = {}
    if not isinstance(actual, dict):
        result.schema_errors.append("missing 'actual' mapping")
        actual = {}
    if not isinstance(review, dict):
        result.schema_errors.append("missing 'review' mapping")
        review = {}

    result.promotion_status = _string(review.get("promotion_status"))
    if result.promotion_status not in PROMOTION_STATUSES:
        result.schema_errors.append(
            "review.promotion_status must be candidate, promoted, or rejected"
        )
    human_review = review.get("human_review_required")
    if isinstance(human_review, bool):
        result.human_review_required = human_review
    else:
        result.schema_errors.append("review.human_review_required must be true or false")
    result.notes = _string(review.get("notes"))

    manifest = _actual_manifest(actual)
    if manifest is None:
        result.schema_errors.append("actual must include route_manifest or raw_output with changeforge_route")
        manifest = {}

    actual_text = _actual_text(actual, manifest)
    result.selected_skills_missing = _missing(
        _string_list(expected.get("selected_skills")),
        manifest_string_list(manifest, "selected_skills"),
    )
    result.selected_capabilities_missing = _missing(
        _string_list(expected.get("selected_capabilities")),
        manifest_string_list(manifest, "selected_capabilities"),
    )
    result.required_references_missing = _missing(
        _string_list(expected.get("required_references")),
        manifest_string_list(manifest, "required_references"),
    )
    result.required_quality_gates_missing = _missing(
        _string_list(expected.get("required_quality_gates")),
        manifest_string_list(manifest, "required_quality_gates"),
    )
    result.professional_obligations_missing = [
        obligation
        for obligation in _string_list(expected.get("required_professional_obligations"))
        if not _meaning_present(actual_text, obligation)
    ]
    result.forbidden_behavior_hits = [
        behavior
        for behavior in _string_list(expected.get("forbidden_behaviors"))
        if _forbidden_present(actual_text, behavior)
    ]
    result.missing_actual_fields = _missing_actual_fields(actual_text, actual)
    return result


def _actual_manifest(actual: dict[str, Any]) -> dict[str, Any] | None:
    manifest = actual.get("route_manifest")
    if isinstance(manifest, dict):
        return manifest
    raw_output = actual.get("raw_output")
    if isinstance(raw_output, str):
        return extract_route_manifest(raw_output)
    return None


def _actual_text(actual: dict[str, Any], manifest: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("raw_output", "validation_evidence", "residual_risk", "inspected_boundaries", "next_gate"):
        value = actual.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.append(json.dumps(value, sort_keys=True))
        elif value is True:
            parts.append(key.replace("_", " "))
    if manifest:
        parts.append(json.dumps(manifest, sort_keys=True))
    return "\n".join(parts)


def _missing_actual_fields(actual_text: str, actual: dict[str, Any]) -> list[str]:
    required = {
        "validation_evidence": ("validation evidence", "validation command", "not verified", "not-verified"),
        "residual_risk": ("residual risk",),
        "inspected_boundaries": ("inspected boundaries", "boundaries inspected"),
        "next_gate": ("next gate", "handoff"),
    }
    missing: list[str] = []
    for field_name, fallback_terms in required.items():
        if _field_present(actual.get(field_name)):
            continue
        if _mentions(actual_text, fallback_terms):
            continue
        missing.append(field_name)
    return missing


def _field_present(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return False


def _missing(expected: list[str], actual: list[str]) -> list[str]:
    actual_set = set(actual)
    return [item for item in expected if item not in actual_set]


def _meaning_present(text: str, phrase: str) -> bool:
    folded_text = _fold(text)
    folded_phrase = _fold(phrase)
    if not folded_phrase:
        return True
    if folded_phrase in folded_text:
        return True
    tokens = [token for token in folded_phrase.split() if len(token) >= 4]
    if len(tokens) < 2:
        return False
    hits = sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", folded_text))
    return hits >= max(2, len(tokens) - 1)


def _forbidden_present(text: str, phrase: str) -> bool:
    folded_phrase = _fold(phrase)
    return bool(folded_phrase and folded_phrase in _fold(text))


def _mentions(text: str, terms: tuple[str, ...]) -> bool:
    folded = _fold(text)
    return any(_fold(term) in folded for term in terms)


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", " ", str(text).casefold()).strip()


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _write_reports(report: AgentSampleReport, reports_dir: Path, report_format: str) -> list[Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if report_format in {"all", "markdown"}:
        path = reports_dir / MARKDOWN_REPORT
        path.write_text(_render_markdown(report), encoding="utf-8")
        written.append(path)
    if report_format in {"all", "json"}:
        path = reports_dir / JSON_REPORT
        path.write_text(json.dumps(_payload(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _payload(report: AgentSampleReport) -> dict[str, Any]:
    payload = asdict(report)
    payload["results"] = [
        {
            **asdict(result),
            "ok": result.ok,
            "findings": _result_findings(result),
        }
        for result in report.results
    ]
    return payload


def _render_markdown(report: AgentSampleReport) -> str:
    lines = [
        "# Professional Agent Samples Evaluation",
        "",
        f"- Generated: {report.generated_at}",
        f"- Mode: {report.mode}",
        f"- Strict: {str(report.strict).lower()}",
        f"- Samples checked: {report.samples_checked}",
        f"- Warnings: {report.warnings}",
        f"- Failures: {report.failures}",
        "",
        "| Sample | Promotion | OK | Findings |",
        "| --- | --- | --- | ---: |",
    ]
    for result in report.results:
        lines.append(
            f"| `{result.path}` | {result.promotion_status or '-'} | "
            f"{str(result.ok).lower()} | {len(_result_findings(result))} |"
        )
    lines.extend(["", "## Findings", ""])
    failing = [result for result in report.results if not result.ok]
    if not failing:
        lines.append("- None")
    for result in failing:
        lines.append(f"### `{result.path}`")
        for finding in _result_findings(result):
            lines.append(f"- {finding}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _result_findings(result: SampleResult) -> list[str]:
    findings: list[str] = []
    groups = (
        ("missing selected skills", result.selected_skills_missing),
        ("missing selected capabilities", result.selected_capabilities_missing),
        ("missing required references", result.required_references_missing),
        ("missing required quality gates", result.required_quality_gates_missing),
        ("missing professional obligations", result.professional_obligations_missing),
        ("forbidden behavior hits", result.forbidden_behavior_hits),
        ("missing actual fields", result.missing_actual_fields),
        ("schema errors", result.schema_errors),
    )
    for label, values in groups:
        if values:
            findings.append(f"{label}: {', '.join(values)}")
    return findings


def _mode(args: argparse.Namespace) -> str:
    if args.promoted_only:
        return "promoted-only"
    if args.candidates_only:
        return "candidates-only"
    return "all"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
