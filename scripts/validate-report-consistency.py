#!/usr/bin/env python3
"""Validate published benchmark report consistency."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate-codex-live-benchmark-reports.py"


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
    if errors:
        for error in errors:
            print(f"validate-report-consistency: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-report-consistency: reports are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
