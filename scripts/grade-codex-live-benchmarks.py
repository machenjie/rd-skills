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


EXCERPT_MAX_CHARS = 1200


def _case_dir(benchmark: str, root: Path) -> Path:
    category, case_id = benchmark.split("/", 1)
    return root / "evals" / "codegen" / category / case_id


def _real_assertion_files(case_dir: Path) -> list[Path]:
    category = case_dir.parent.name
    case_name = case_dir.name
    return list(case_assertion_files(category, case_name, case_dir.parents[3]))


def _redact_output(text: str, *, root: Path, candidate_dir: Path) -> str:
    """Remove host-specific paths and credentials from persisted grading logs."""
    redacted = text
    for candidate_label in {str(candidate_dir), str(candidate_dir.resolve())}:
        redacted = redacted.replace(candidate_label, "<candidate>")
    for root_label in {str(root), str(root.resolve())}:
        redacted = redacted.replace(root_label, "<repo>")
    redacted = re.sub(r"/Users/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"/home/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"/private/var/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"/var/folders/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"/tmp/[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"[A-Za-z]:\\Users\\[^\s\"'<>]+", "<local-path>", redacted)
    redacted = re.sub(r"auth\.json", "<redacted-auth-file>", redacted, flags=re.IGNORECASE)
    redacted = re.sub(
        r"(?i)(api[_-]?key|access[_-]?token|bearer[_-]?token|refresh[_-]?token)\s*[:=]\s*"
        r"[^\s\"'<>]+",
        r"\1=<redacted>",
        redacted,
    )
    redacted = re.sub(r"sk-(?=[A-Za-z0-9_-]{10,})[A-Za-z0-9_-]+", "<redacted-token>", redacted)
    return redact_report_text(redacted)


def _excerpt(text: str) -> str:
    """Return a bounded diagnostic excerpt."""
    stripped = text.strip()
    if len(stripped) <= EXCERPT_MAX_CHARS:
        return stripped
    return stripped[:EXCERPT_MAX_CHARS] + "...<truncated>"


def _first_failure_excerpt(text: str) -> str:
    """Return the first useful failure block from combined grader output."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "run-codegen-benchmarks: ERROR:" in line or "Traceback" in line or "AssertionError" in line:
            return _excerpt("\n".join(lines[index : index + 40]))
    return _excerpt(text)


def _stage_excerpt(text: str, stage: str, *, fallback: str) -> str:
    """Return an excerpt for one grader stage."""
    labels = {
        "setup": ("setup exited", "setup.sh is missing", "starter-repo/setup.sh"),
        "test_suite": ("test-suite exited", "/test-suite/", "assertion"),
        "security_checks": ("security-checks exited", "/security-checks/"),
    }
    lines = text.splitlines()
    needles = labels[stage]
    for index, line in enumerate(lines):
        if any(needle in line for needle in needles):
            return _excerpt("\n".join(lines[index : index + 40]))
    return fallback


def _stage_failures(text: str, *, returncode: int) -> dict[str, bool]:
    """Classify which codegen benchmark stages failed from runner diagnostics."""
    setup_failed = bool(
        re.search(
            r"(?i)(setup exited|setup\.sh is missing|starter-repo/setup\.sh: missing|required script.*starter-repo/setup\.sh)",
            text,
        )
    )
    test_failed = bool(
        re.search(
            r"(?i)(test-suite exited|candidate evaluation requires real assertion|assertion .*/test-suite/|"
            r"assertion .*test_.*\.py exited|test-suite/run\.sh: missing)",
            text,
        )
    )
    security_failed = bool(
        re.search(
            r"(?i)(security-checks exited|assertion .*/security-checks/|security-checks/run\.sh: missing)",
            text,
        )
    )
    if returncode != 0 and not (setup_failed or test_failed or security_failed):
        test_failed = True
    return {
        "setup": setup_failed,
        "test_suite": test_failed,
        "security_checks": security_failed,
    }


def _setup_failure_reason(text: str, *, failed: bool) -> str:
    if not failed:
        return "none"
    lowered = text.casefold()
    if "setup.sh is missing" in lowered or "starter-repo/setup.sh: missing" in lowered:
        return "setup_script_missing"
    if (
        "codegen_benchmark_harness.py" in lowered
        and ("no such file" in lowered or "can't open file" in lowered or "not found" in lowered)
    ) or ("can't open file" in lowered and "no such file" in lowered):
        return "harness_path_unresolved"
    if re.search(r"(?i)(pip install|npm install|module not found|modulenotfounderror|dependency)", text):
        return "dependency_install_failed"
    if re.search(r"(?i)(syntaxerror|compileall|py_compile|python compile)", text):
        return "python_compile_failed"
    return "setup_script_failed"


def _test_suite_failure_reason(text: str, *, failed: bool) -> str:
    if not failed:
        return "none"
    if re.search(r"(?i)assertion .*(test-suite|test_.*\.py) .*exited", text):
        return "assertion_failed"
    if "expected starter-repo cwd" in text or "codegen-benchmark-harness: ERROR:" in text:
        return "harness_contract_failed"
    return "test_runner_failed"


def _security_failure_reason(text: str, *, failed: bool) -> str:
    if not failed:
        return "none"
    if re.search(r"(?i)assertion .*security-checks.*exited", text):
        return "assertion_failed"
    if "expected starter-repo cwd" in text or "codegen-benchmark-harness: ERROR:" in text:
        return "harness_contract_failed"
    return "security_runner_failed"


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
    stages = _stage_failures(combined, returncode=completed.returncode)
    first_failure_excerpt = "" if all_passed else _first_failure_excerpt(combined)
    setup_passed = all_passed or not stages["setup"]
    test_suite_passed = all_passed or not stages["test_suite"]
    security_checks_passed = all_passed or not stages["security_checks"]
    result: dict[str, Any] = {
        "schema_version": 2,
        "generated_by": "scripts/grade-codex-live-benchmarks.py",
        "benchmark": benchmark,
        "candidate_dir": "<candidate>",
        "returncode": completed.returncode,
        "grading_status": "passed" if all_passed else "failed",
        "all_passed": all_passed,
        "setup_passed": setup_passed,
        "test_suite_passed": test_suite_passed,
        "security_checks_passed": security_checks_passed,
        "setup_failure_reason": _setup_failure_reason(combined, failed=not setup_passed),
        "test_suite_failure_reason": _test_suite_failure_reason(combined, failed=not test_suite_passed),
        "security_failure_reason": _security_failure_reason(combined, failed=not security_checks_passed),
        "first_failure_excerpt": first_failure_excerpt,
        "setup_log_excerpt": ""
        if setup_passed
        else _stage_excerpt(combined, "setup", fallback=first_failure_excerpt),
        "test_suite_log_excerpt": ""
        if test_suite_passed
        else _stage_excerpt(combined, "test_suite", fallback=first_failure_excerpt),
        "security_log_excerpt": ""
        if security_checks_passed
        else _stage_excerpt(combined, "security_checks", fallback=first_failure_excerpt),
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
        "setup_failure_reason": "none",
        "test_suite_failure_reason": "none",
        "security_failure_reason": "none",
        "first_failure_excerpt": _excerpt(message),
        "setup_log_excerpt": "",
        "test_suite_log_excerpt": "",
        "security_log_excerpt": "",
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
