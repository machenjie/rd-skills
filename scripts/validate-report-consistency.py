#!/usr/bin/env python3
"""Validate published benchmark report consistency."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate-codex-live-benchmark-reports.py"
CONTEXT_CONTROL_REPORT = ROOT / "reports" / "context-control-plane-eval.json"
CONTEXT_CONTROL_ROW = "context_control_overhead"


def _default(path: str) -> Path:
    return ROOT / path


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_codex_live_benchmark_reports", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _find_named(items: Any, name: str) -> dict[str, Any] | None:
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def _context_control_expected_status(report: dict[str, Any] | None) -> str:
    if not isinstance(report, dict):
        return "not_collected"
    overhead = report.get("context_control_overhead")
    if report.get("status") != "pass":
        return "fail"
    if not isinstance(overhead, dict):
        return "fail"
    status = str(overhead.get("status") or "unknown")
    if status not in {"pass", "partial", "fail", "not_collected"}:
        return "fail"
    if _high_overhead_neutral_pass_rate(overhead) and status == "pass":
        return "fail"
    return status


def _high_overhead_neutral_pass_rate(overhead: dict[str, Any]) -> bool:
    input_overhead = overhead.get("input_token_overhead_pct")
    output_overhead = overhead.get("output_token_overhead_pct")
    pass_rate_delta = overhead.get("pass_rate_delta")
    high_overhead = (
        (isinstance(input_overhead, int | float) and float(input_overhead) > 100)
        or (isinstance(output_overhead, int | float) and float(output_overhead) > 75)
    )
    neutral = not isinstance(pass_rate_delta, int | float) or float(pass_rate_delta) <= 0
    return high_overhead and neutral


def context_control_report_consistency_errors(
    *,
    context_report_path: Path = CONTEXT_CONTROL_REPORT,
    scorecard_path: Path | None = None,
    public_summary_path: Path | None = None,
) -> list[str]:
    """Validate that scorecard/public reports mirror context-control overhead evidence."""
    errors: list[str] = []
    report = _read_json(context_report_path)
    expected_status = _context_control_expected_status(report if isinstance(report, dict) else None)
    if isinstance(report, dict):
        overhead = report.get("context_control_overhead")
        if isinstance(overhead, dict) and _high_overhead_neutral_pass_rate(overhead):
            verdict = str(overhead.get("overhead_policy_verdict") or "").casefold()
            if "not success" not in verdict and "do not claim" not in verdict:
                errors.append("context_control_overhead high-overhead neutral case must document no-success boundary")
        if expected_status == "fail":
            errors.append("context-control eval failure blocks pass")

    if scorecard_path is not None and scorecard_path.exists():
        scorecard = _read_json(scorecard_path)
        item = _find_named(scorecard.get("dimensions") if isinstance(scorecard, dict) else None, CONTEXT_CONTROL_ROW)
        if item is None:
            errors.append("scorecard missing context_control_overhead dimension")
        elif item.get("status") != expected_status:
            errors.append(
                f"scorecard context_control_overhead status {item.get('status')!r} "
                f"does not match expected {expected_status!r}"
            )

    if public_summary_path is not None and public_summary_path.exists():
        public = _read_json(public_summary_path)
        item = _find_named(public.get("items") if isinstance(public, dict) else None, CONTEXT_CONTROL_ROW)
        if item is None:
            errors.append("public summary missing context_control_overhead evidence row")
        elif item.get("status") != expected_status:
            errors.append(
                f"public summary context_control_overhead status {item.get('status')!r} "
                f"does not match expected {expected_status!r}"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=_default("reports/codex-live-benchmark-summary.json"))
    parser.add_argument("--scorecard", type=Path, default=_default("reports/professional-scorecard.json"))
    parser.add_argument("--public-summary", type=Path, default=_default("reports/public-benchmark-summary.json"))
    parser.add_argument("--dashboard", type=Path, default=_default("docs/SCORECARD_DASHBOARD.md"))
    parser.add_argument("--readme", type=Path, default=_default("README.md"))
    args = parser.parse_args(argv)

    validator = _load_validator()
    errors = validator.validate_report_consistency(
        args.summary,
        scorecard_path=args.scorecard if args.scorecard.exists() else None,
        public_summary_path=args.public_summary if args.public_summary.exists() else None,
        dashboard_path=args.dashboard if args.dashboard.exists() else None,
        readme_path=args.readme if args.readme.exists() else None,
    )
    errors.extend(
        context_control_report_consistency_errors(
            scorecard_path=args.scorecard if args.scorecard.exists() else None,
            public_summary_path=args.public_summary if args.public_summary.exists() else None,
        )
    )
    if errors:
        for error in errors:
            print(f"validate-report-consistency: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-report-consistency: reports are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
