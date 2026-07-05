#!/usr/bin/env python3
"""Run and aggregate multi-dimensional ChangeForge skill evaluations."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DIR = ROOT / "reports"
SKILL_EVALUATION_MARKDOWN = "skill-evaluation.md"
SKILL_EVALUATION_JSON = "skill-evaluation.json"

DIMENSION_WEIGHTS = {
    "professionalism_depth": 0.6,
    "efficacy": 0.4,
}


@dataclass
class SkillEvaluationDimension:
    name: str
    score: float | None
    status: str
    source: str
    verification_command: str
    detail: str
    weight: float


@dataclass
class SkillEvaluationReport:
    generated_at: str
    dimensions_checked: int
    overall_score: float | None
    overall_status: str
    dimensions: list[SkillEvaluationDimension]


def _load_script(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def _run_dimension_generators(reports_dir: Path, selected: set[str]) -> None:
    if "efficacy" in selected:
        efficacy = _load_script("eval_skill_efficacy", ROOT / "scripts" / "eval-skill-efficacy.py")
        exit_code = efficacy.main(["--reports-dir", str(reports_dir), "--format", "json"])
        if exit_code != 0:
            raise RuntimeError("eval-skill-efficacy.py failed")
    if "professionalism_depth" in selected:
        professionalism = _load_script(
            "eval_skill_professionalism",
            ROOT / "scripts" / "eval-skill-professionalism.py",
        )
        exit_code = professionalism.main(["--reports-dir", str(reports_dir), "--format", "json"])
        if exit_code != 0:
            raise RuntimeError("eval-skill-professionalism.py failed")


def build_skill_evaluation_report(
    reports_dir: Path,
    selected_dimensions: list[str],
    *,
    run_generators: bool = True,
) -> SkillEvaluationReport:
    selected = set(selected_dimensions)
    if run_generators:
        _run_dimension_generators(reports_dir, selected)

    dimensions: list[SkillEvaluationDimension] = []
    if "professionalism_depth" in selected:
        dimensions.append(_professionalism_depth_dimension(reports_dir))
    if "efficacy" in selected:
        dimensions.append(_efficacy_dimension(reports_dir))

    scored = [dimension for dimension in dimensions if dimension.score is not None]
    total_weight = sum(dimension.weight for dimension in scored)
    overall_score = None
    if total_weight:
        overall_score = round(
            sum(float(dimension.score) * dimension.weight for dimension in scored) / total_weight,
            2,
        )
    return SkillEvaluationReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        dimensions_checked=len(dimensions),
        overall_score=overall_score,
        overall_status=_overall_status(dimensions),
        dimensions=dimensions,
    )


def _professionalism_depth_dimension(reports_dir: Path) -> SkillEvaluationDimension:
    source = reports_dir / "skill-professionalism-depth.json"
    payload = _read_json(source)
    if not payload:
        return _missing_dimension("professionalism_depth", source, "python3 scripts/eval-skill-professionalism.py")
    score = _number_or_none(payload.get("average_professionalism_score"))
    blocking = _warning_count(payload, {"release-blocking"})
    review = _warning_count(payload, {"review-required"})
    status = "unknown"
    if score is not None:
        if score >= 85 and blocking == 0:
            status = "pass"
        elif score >= 75 and blocking == 0:
            status = "partial"
        else:
            status = "fail"
    return SkillEvaluationDimension(
        name="professionalism_depth",
        score=score,
        status=status,
        source=_rel(source),
        verification_command="python3 scripts/eval-skill-professionalism.py",
        detail=f"items={payload.get('items_checked')}; release_blocking={blocking}; review_required={review}",
        weight=DIMENSION_WEIGHTS["professionalism_depth"],
    )


def _efficacy_dimension(reports_dir: Path) -> SkillEvaluationDimension:
    source = reports_dir / "skill-efficacy-eval.json"
    payload = _read_json(source)
    if not payload:
        return _missing_dimension("efficacy", source, "python3 scripts/eval-skill-efficacy.py")
    score = _number_or_none(payload.get("average_efficacy_score"))
    warnings = int(payload.get("warning_count") or 0)
    measured = int(payload.get("measured_count") or 0)
    status = "unknown"
    if score is not None:
        if score >= 85 and warnings == 0:
            status = "pass"
        elif score >= 75:
            status = "partial"
        else:
            status = "fail"
    return SkillEvaluationDimension(
        name="efficacy",
        score=score,
        status=status,
        source=_rel(source),
        verification_command="python3 scripts/eval-skill-efficacy.py",
        detail=(
            f"benchmarks={payload.get('benchmarks_checked')}; measured={measured}; "
            f"structural={payload.get('structural_count')}; warnings={warnings}"
        ),
        weight=DIMENSION_WEIGHTS["efficacy"],
    )


def _missing_dimension(name: str, source: Path, command: str) -> SkillEvaluationDimension:
    return SkillEvaluationDimension(
        name=name,
        score=None,
        status="not_collected",
        source=_rel(source),
        verification_command=command,
        detail="dimension report is missing; run the verification command",
        weight=DIMENSION_WEIGHTS.get(name, 0.0),
    )


def _warning_count(payload: dict[str, Any], severities: set[str]) -> int:
    count = 0
    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        for warning in item.get("warnings") or []:
            if isinstance(warning, dict) and warning.get("severity") in severities:
                count += 1
    return count


def _number_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _overall_status(dimensions: list[SkillEvaluationDimension]) -> str:
    if not dimensions:
        return "not_collected"
    statuses = {dimension.status for dimension in dimensions}
    if "fail" in statuses:
        return "fail"
    if statuses <= {"pass"}:
        return "pass"
    if statuses & {"partial", "unknown", "not_collected"}:
        return "partial"
    return "unknown"


def _write_report(report: SkillEvaluationReport, reports_dir: Path, report_format: str) -> list[Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if report_format in {"all", "markdown"}:
        path = reports_dir / SKILL_EVALUATION_MARKDOWN
        path.write_text(_render_markdown(report), encoding="utf-8")
        written.append(path)
    if report_format in {"all", "json"}:
        path = reports_dir / SKILL_EVALUATION_JSON
        path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _render_markdown(report: SkillEvaluationReport) -> str:
    score = "not_collected" if report.overall_score is None else f"{report.overall_score:.2f}/100"
    lines = [
        "# Skill Evaluation",
        "",
        f"- Generated: {report.generated_at}",
        f"- Dimensions checked: {report.dimensions_checked}",
        f"- Overall score: {score}",
        f"- Overall status: {report.overall_status}",
        "",
        "| Dimension | Score | Status | Weight | Source | Verification | Detail |",
        "| --- | ---: | --- | ---: | --- | --- | --- |",
    ]
    for dimension in report.dimensions:
        dimension_score = "not_collected" if dimension.score is None else f"{dimension.score:.2f}/100"
        lines.append(
            f"| `{dimension.name}` | {dimension_score} | {dimension.status} | "
            f"{dimension.weight:.2f} | `{dimension.source}` | `{dimension.verification_command}` | "
            f"{dimension.detail} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dimensions",
        default="professionalism_depth,efficacy",
        help="comma-separated dimensions to aggregate; currently professionalism_depth and efficacy",
    )
    parser.add_argument(
        "--format",
        choices=("all", "markdown", "json"),
        default="all",
        help="aggregate report format to write",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="directory for generated reports; defaults to reports/",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="read existing dimension reports instead of running dimension evaluators first",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args([] if argv is None else argv)
    selected = [item.strip() for item in args.dimensions.split(",") if item.strip()]
    unknown = sorted(set(selected) - set(DIMENSION_WEIGHTS))
    if unknown:
        print(f"eval-skills: unknown dimension(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    report = build_skill_evaluation_report(
        args.reports_dir,
        selected,
        run_generators=not args.no_run,
    )
    written = _write_report(report, args.reports_dir, args.format)
    print(
        f"eval-skills: dimensions={report.dimensions_checked}; "
        f"overall_status={report.overall_status}; overall_score={report.overall_score}"
    )
    for path in written:
        print(f"- report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
