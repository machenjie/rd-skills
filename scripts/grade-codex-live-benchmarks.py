#!/usr/bin/env python3
"""Grade a Codex live benchmark candidate with the existing codegen harness."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import ROOT, case_assertion_files, redact_report_text, write_json


def _case_dir(benchmark: str, root: Path) -> Path:
    category, case_id = benchmark.split("/", 1)
    return root / "evals" / "codegen" / category / case_id


def _real_assertion_files(case_dir: Path) -> list[Path]:
    category = case_dir.parent.name
    case_name = case_dir.name
    return list(case_assertion_files(category, case_name, case_dir.parents[3]))


def _redact_output(text: str, *, root: Path, candidate_dir: Path) -> str:
    """Remove host-specific paths from persisted grading logs."""
    redacted = text
    for candidate_label in {str(candidate_dir), str(candidate_dir.resolve())}:
        redacted = redacted.replace(candidate_label, "<candidate>")
    for root_label in {str(root), str(root.resolve())}:
        redacted = redacted.replace(root_label, "<repo>")
    redacted = re.sub(r"/Users/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"/home/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"[A-Za-z]:\\Users\\[^\s\"'<>]+", "<local-path>", redacted)
    return redact_report_text(redacted)


def _grading_path(out_dir: Path, path: Path) -> str:
    """Return a grading-directory-relative artifact label."""
    try:
        rel = path.resolve().relative_to(out_dir.resolve()).as_posix()
    except ValueError:
        return "<grading>"
    return f"<grading>/{rel}"


def grade_candidate(
    benchmark: str,
    candidate_dir: Path,
    out_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Run the existing codegen benchmark harness against a candidate repo."""
    out_dir.mkdir(parents=True, exist_ok=True)
    case_dir = _case_dir(benchmark, root)
    if not _real_assertion_files(case_dir):
        return _write_not_collected_grading(benchmark, candidate_dir, out_dir, root)
    command = [
        sys.executable,
        str(root / "scripts" / "run-codegen-benchmarks.py"),
        "--benchmark",
        benchmark,
        "--candidate-dir",
        str(candidate_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    stdout_path = out_dir / "run-codegen-benchmarks.stdout.log"
    stderr_path = out_dir / "run-codegen-benchmarks.stderr.log"
    stdout_text = _redact_output(completed.stdout, root=root, candidate_dir=candidate_dir)
    stderr_text = _redact_output(completed.stderr, root=root, candidate_dir=candidate_dir)
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")

    redacted_command = [
        "<python>",
        "scripts/run-codegen-benchmarks.py",
        "--benchmark",
        benchmark,
        "--candidate-dir",
        "<candidate>",
    ]
    combined = (
        f"command: {' '.join(redacted_command)}\n"
        f"returncode: {completed.returncode}\n\n"
        "stdout:\n"
        f"{stdout_text}\n\n"
        "stderr:\n"
        f"{stderr_text}\n"
    )
    for log_name in ("setup.log", "test-suite.log", "security-checks.log"):
        (out_dir / log_name).write_text(combined, encoding="utf-8")

    all_passed = completed.returncode == 0
    result: dict[str, Any] = {
        "schema_version": 2,
        "generated_by": "scripts/grade-codex-live-benchmarks.py",
        "benchmark": benchmark,
        "candidate_dir": "<candidate>",
        "returncode": completed.returncode,
        "grading_status": "passed" if all_passed else "failed",
        "all_passed": all_passed,
        "setup_passed": all_passed,
        "test_suite_passed": all_passed,
        "security_checks_passed": all_passed,
        "logs": {
            "stdout": _grading_path(out_dir, stdout_path),
            "stderr": _grading_path(out_dir, stderr_path),
            "setup": _grading_path(out_dir, out_dir / "setup.log"),
            "test_suite": _grading_path(out_dir, out_dir / "test-suite.log"),
            "security_checks": _grading_path(out_dir, out_dir / "security-checks.log"),
        },
    }
    write_json(out_dir / "grading-result.json", result)
    return result


def _write_not_collected_grading(
    benchmark: str,
    candidate_dir: Path,
    out_dir: Path,
    root: Path,
) -> dict[str, Any]:
    message = (
        f"{benchmark}: candidate grading not collected because this codegen case "
        "does not provide real assertion files under test-suite/tests or "
        "security-checks/security_tests.\n"
    )
    for log_name in (
        "setup.log",
        "test-suite.log",
        "security-checks.log",
        "run-codegen-benchmarks.stdout.log",
        "run-codegen-benchmarks.stderr.log",
    ):
        (out_dir / log_name).write_text(message, encoding="utf-8")
    result: dict[str, Any] = {
        "schema_version": 2,
        "generated_by": "scripts/grade-codex-live-benchmarks.py",
        "benchmark": benchmark,
        "candidate_dir": "<candidate>",
        "returncode": None,
        "grading_status": "not_collected",
        "all_passed": False,
        "setup_passed": False,
        "test_suite_passed": False,
        "security_checks_passed": False,
        "logs": {
            "stdout": _grading_path(out_dir, out_dir / "run-codegen-benchmarks.stdout.log"),
            "stderr": _grading_path(out_dir, out_dir / "run-codegen-benchmarks.stderr.log"),
            "setup": _grading_path(out_dir, out_dir / "setup.log"),
            "test_suite": _grading_path(out_dir, out_dir / "test-suite.log"),
            "security_checks": _grading_path(out_dir, out_dir / "security-checks.log"),
        },
    }
    write_json(out_dir / "grading-result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    result = grade_candidate(args.benchmark, args.candidate_dir, args.out_dir)
    print(f"grade-codex-live-benchmarks: all_passed={result['all_passed']}")
    if result.get("grading_status") == "not_collected":
        return 0
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
