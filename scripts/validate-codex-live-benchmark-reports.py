#!/usr/bin/env python3
"""Validate Codex CLI live benchmark reports and published summaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    LIVE_EVIDENCE_LEVEL,
    ROOT,
    load_case_registry,
    print_errors,
    read_json,
    scan_forbidden_secrets,
    validate_required_fields,
)


REAL_RESULT_REQUIRED_FILES = (
    "prompt.md",
    "codex-command.redacted.json",
    "events.jsonl",
    "final.md",
    "diff.patch",
    "git-status.txt",
    "grading/grading-result.json",
    "result.json",
)


def validate_run_dir(run_dir: Path) -> list[str]:
    """Validate a run directory without requiring dry-run reports to be publishable."""
    errors: list[str] = []
    try:
        load_case_registry()
    except Exception as exc:
        errors.append(f"case registry invalid: {exc}")
    manifest_path = run_dir / "run-manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        return [f"{manifest_path} missing or invalid"]
    errors.extend(validate_required_fields(manifest, "run-manifest"))
    errors.extend(scan_forbidden_secrets(manifest_path))
    cases_dir = run_dir / "cases"
    if cases_dir.exists():
        errors.extend(scan_forbidden_secrets(cases_dir))

    result_paths = sorted(run_dir.glob("cases/*/*/run-*/result.json"))
    live_effective = bool(manifest.get("live_execution_effective"))
    if live_effective and not result_paths:
        errors.append("live run manifest has no result.json files")
    for result_path in result_paths:
        result = read_json(result_path)
        if not isinstance(result, dict):
            errors.append(f"{result_path}: invalid JSON")
            continue
        errors.extend(f"{result_path}: {error}" for error in validate_required_fields(result, "case-result"))
        if result.get("status") in {"collected", "failed", "partial"}:
            case_dir = result_path.parent
            for rel_file in REAL_RESULT_REQUIRED_FILES:
                if not (case_dir / rel_file).exists():
                    errors.append(f"{case_dir}: missing required result artifact {rel_file}")
    return errors


def validate_summary(summary_path: Path, *, publishable: bool = True) -> list[str]:
    """Validate a summary JSON used by scorecard/public reporting."""
    summary = read_json(summary_path)
    if not isinstance(summary, dict):
        return [f"{summary_path} missing or invalid"]
    errors = validate_required_fields(summary, "summary")
    errors.extend(scan_forbidden_secrets(summary_path))
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"summary evidence_level must be {LIVE_EVIDENCE_LEVEL}")
    if publishable and summary.get("status") in {"not_collected", "skipped_not_opted_in"}:
        errors.append("dry-run, skipped, or not-collected summaries cannot be published")
    if "limitations" not in summary or not summary.get("limitations"):
        errors.append("summary limitations are required")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    if not args.run_dir and not args.summary:
        print("validate-codex-live-benchmark-reports: ERROR: --run-dir or --summary is required", file=sys.stderr)
        return 2
    errors: list[str] = []
    if args.run_dir:
        errors.extend(validate_run_dir(args.run_dir))
    if args.summary:
        errors.extend(validate_summary(args.summary))
    return print_errors("validate-codex-live-benchmark-reports", errors)


if __name__ == "__main__":
    sys.exit(main())
