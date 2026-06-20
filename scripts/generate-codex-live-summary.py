#!/usr/bin/env python3
"""Generate a bounded summary for an opt-in Codex CLI live benchmark run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import LIVE_EVIDENCE_LEVEL, ROOT, read_json, validate_status, write_json


def generate_summary(run_dir: Path) -> dict[str, Any]:
    """Aggregate run-manifest and result.json files into one summary payload."""
    manifest = read_json(run_dir / "run-manifest.json")
    if not isinstance(manifest, dict):
        manifest = {}
    results = [
        payload
        for payload in (read_json(path) for path in sorted(run_dir.glob("cases/*/*/run-*/result.json")))
        if isinstance(payload, dict)
    ]
    real_results = [result for result in results if result.get("status") in {"collected", "failed", "partial"}]
    if not real_results:
        status = validate_status(manifest.get("status", "not_collected"))
    elif any(result.get("status") == "failed" for result in real_results):
        status = "partial" if any(result.get("status") == "collected" for result in real_results) else "failed"
    elif all((result.get("grading") or {}).get("all_passed") for result in real_results):
        status = "collected"
    else:
        status = "partial"

    passed = sum(1 for result in real_results if (result.get("grading") or {}).get("all_passed"))
    security_passed = sum(1 for result in real_results if (result.get("grading") or {}).get("security_checks_passed"))
    usage = _average_usage(real_results)
    variants = sorted({str(result.get("variant")) for result in real_results if result.get("variant")})
    cases = sorted({str(result.get("case_id")) for result in real_results if result.get("case_id")})
    summary = {
        "schema_version": 1,
        "generated_by": "scripts/generate-codex-live-summary.py",
        "status": status,
        "evidence_level": LIVE_EVIDENCE_LEVEL,
        "run_id": str(manifest.get("run_id") or run_dir.name),
        "run_dir": str(run_dir),
        "case_count": len(cases),
        "variant_count": len(variants),
        "result_count": len(real_results),
        "variants": variants,
        "cases": cases,
        "pass_rate": _rate(passed, len(real_results)),
        "security_pass_rate": _rate(security_passed, len(real_results)),
        "average_usage": usage,
        "telemetry": {
            "event_count": sum(int((result.get("metrics") or {}).get("event_count", 0)) for result in real_results),
            "parse_error_count": sum(len((result.get("metrics") or {}).get("parse_errors", [])) for result in real_results),
        },
        "limitations": [
            "Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.",
            "Parsed telemetry excludes raw command bodies and assistant/user message content.",
            "Pass rates cover the selected benchmark cases and variants only.",
        ],
    }
    return summary


def _average_usage(results: list[dict[str, Any]]) -> dict[str, float]:
    keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
    totals = {key: 0 for key in keys}
    for result in results:
        usage = ((result.get("metrics") or {}).get("usage") or {})
        for key in keys:
            totals[key] += int(usage.get(key, 0) or 0)
    divisor = max(len(results), 1)
    return {key: round(value / divisor, 2) for key, value in totals.items()}


def _rate(numerator: int, denominator: int) -> float | str:
    if denominator == 0:
        return "not_collected"
    return round(numerator / denominator, 4)


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a concise Markdown summary."""
    return "\n".join(
        [
            "# Codex CLI Live Benchmark Summary",
            "",
            f"- Status: `{summary['status']}`",
            f"- Evidence level: `{summary['evidence_level']}`",
            f"- Run id: `{summary['run_id']}`",
            f"- Results: `{summary['result_count']}`",
            f"- Cases: `{summary['case_count']}`",
            f"- Variants: `{summary['variant_count']}`",
            f"- Pass rate: `{summary['pass_rate']}`",
            f"- Security pass rate: `{summary['security_pass_rate']}`",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in summary["limitations"]],
            "",
        ]
    )


def publish_summary(summary: dict[str, Any], markdown: str, *, root: Path = ROOT) -> None:
    """Publish a validated live summary into reports for scorecard ingestion."""
    if summary.get("status") in {"not_collected", "skipped_not_opted_in"}:
        raise ValueError("dry-run, skipped, or not-collected summaries cannot be published")
    write_json(root / "reports" / "codex-live-benchmark-summary.json", summary)
    (root / "reports" / "codex-live-benchmark-summary.md").write_text(markdown, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)

    summary = generate_summary(args.run_dir)
    markdown = render_markdown(summary)
    json_out = args.json_out or args.run_dir / "summary.json"
    md_out = args.out or args.run_dir / "summary.md"
    write_json(json_out, summary)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(markdown, encoding="utf-8")
    if args.publish:
        try:
            publish_summary(summary, markdown)
        except ValueError as exc:
            print(f"generate-codex-live-summary: ERROR: {exc}", file=sys.stderr)
            return 1
    print(f"wrote Codex live benchmark summary to {md_out} and {json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
