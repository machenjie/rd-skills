#!/usr/bin/env python3
"""Grade a Codex live benchmark candidate with the existing codegen harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import ROOT, case_assertion_files, redact_report_text, write_json


EXCERPT_MAX_CHARS = 1200
SETUP_CONTRACT_FIELDS = (
    "candidate_setup_exists",
    "candidate_setup_hash_changed",
    "candidate_setup_mentions_changeforge_codegen_root",
    "candidate_setup_uses_fixed_parent_traversal",
    "candidate_setup_invokes_codegen_harness",
)


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
    redacted = re.sub(r"(?i)\b(CODEX_API_KEY|OPENAI_API_KEY)\b", "<redacted-api-key-name>", redacted)
    redacted = re.sub(r"sk-(?=[A-Za-z0-9_-]{10,})[A-Za-z0-9_-]+", "<redacted-token>", redacted)
    return redact_report_text(redacted)


def _excerpt(text: str) -> str:
    """Return a bounded diagnostic excerpt."""
    stripped = text.strip()
    if len(stripped) <= EXCERPT_MAX_CHARS:
        return stripped
    suffix = "...<truncated>"
    return stripped[: EXCERPT_MAX_CHARS - len(suffix)] + suffix


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


def _stage_failures_from_records(records: list[dict[str, Any]], text: str, *, returncode: int) -> dict[str, bool]:
    failures = _stage_failures(text, returncode=returncode)
    stage_map = {
        "setup": "setup",
        "test-suite": "test_suite",
        "security-checks": "security_checks",
    }
    for record in records:
        stage = stage_map.get(str(record.get("stage")))
        if not stage:
            continue
        if record.get("passed") is False:
            failures[stage] = True
        elif record.get("passed") is True and not failures.get(stage):
            failures[stage] = False
    return failures


def _first_failure_stage(stages: dict[str, bool], *, all_passed: bool) -> str:
    if all_passed:
        return "none"
    for stage in ("setup", "test_suite", "security_checks"):
        if stages.get(stage):
            return stage
    return "assertion_files"


def _setup_failure_reason(text: str, *, failed: bool) -> str:
    if not failed:
        return "none"
    lowered = text.casefold()
    fixed_parent_harness_missing = (
        "codegen_benchmark_harness.py" in lowered
        and ("../../.." in lowered or "..\\..\\.." in lowered)
        and ("no such file" in lowered or "can't open file" in lowered or "not found" in lowered)
    )
    missing_env_root = (
        "changeforge_codegen_root is unset" in lowered
        or "changeforge_codegen_root is empty" in lowered
        or "set changeforge_codegen_root" in lowered
        or ("changeforge_codegen_root" in lowered and ("unset" in lowered or "empty" in lowered or "not set" in lowered))
    )
    harness_missing = (
        "codegen_benchmark_harness.py" in lowered
        and ("no such file" in lowered or "can't open file" in lowered or "not found" in lowered)
    )
    if (
        "setup.sh is missing" in lowered
        or "candidate/setup.sh missing" in lowered
        or "setup.sh: no such file" in lowered
        or "starter-repo/setup.sh: missing" in lowered
    ):
        return "setup_script_missing"
    if "candidate lacks required starter file" in lowered or (
        "missing starter readme" in lowered or "starter readme" in lowered and "missing" in lowered
    ):
        return "candidate_removed_required_file"
    if fixed_parent_harness_missing:
        return "setup_script_modified_bad_path"
    if missing_env_root:
        return "missing_env_root"
    if harness_missing:
        return "missing_harness"
    if re.search(
        r"(?i)(ModuleNotFoundError:\s*No module named|ImportError:\s*(cannot import|No module named)|"
        r"No module named ['\"][^'\"]+['\"]|package install failed|dependency install failed)",
        text,
    ):
        return "dependency_install_failed"
    if re.search(r"(?i)(syntaxerror|compileall|py_compile|python compile)", text):
        return "python_compile_failed"
    if re.search(
        r"(?im)(^(?:bash|sh): [^\n]*permission denied|"
        r"PermissionError:\s*\[Errno 13\][^\n]*permission denied|"
        r"OSError:\s*\[Errno 13\][^\n]*permission denied|errno 13[^\n]*permission denied)",
        text,
    ):
        return "permission_denied"
    if re.search(r"(?im)(^[^\n:]+: command not found|bad interpreter:)", text):
        return "shell_error"
    return "unknown"


def _file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _setup_contract(benchmark: str, candidate_dir: Path, *, root: Path) -> dict[str, bool]:
    case_dir = _case_dir(benchmark, root)
    starter_setup = case_dir / "starter-repo" / "setup.sh"
    candidate_setup = candidate_dir / "setup.sh"
    exists = candidate_setup.is_file()
    text = candidate_setup.read_text(encoding="utf-8", errors="ignore") if exists else ""
    starter_hash = _file_hash(starter_setup)
    candidate_hash = _file_hash(candidate_setup)
    return {
        "candidate_setup_exists": exists,
        "candidate_setup_hash_changed": bool(exists and starter_hash and candidate_hash and starter_hash != candidate_hash),
        "candidate_setup_mentions_changeforge_codegen_root": "CHANGEFORGE_CODEGEN_ROOT" in text,
        "candidate_setup_uses_fixed_parent_traversal": bool(
            re.search(r"(\.\./){2,}|(\.\.\\){2,}|parents\[[1-9]", text)
        ),
        "candidate_setup_invokes_codegen_harness": "codegen_benchmark_harness.py" in text,
    }


def _setup_failure_subreason(
    text: str,
    *,
    failed: bool,
    setup_failure_reason: str,
    setup_contract: dict[str, bool],
) -> str:
    if not failed:
        return "none"
    lowered = text.casefold()
    if setup_failure_reason == "missing_env_root":
        return "missing_env_root"
    if setup_failure_reason == "missing_harness":
        return "missing_harness"
    if setup_failure_reason != "setup_script_modified_bad_path":
        return "unknown"
    if "expected starter-repo cwd" in lowered or "wrong cwd" in lowered:
        return "wrong_cwd"
    if setup_contract.get("candidate_setup_hash_changed") and setup_contract.get(
        "candidate_setup_uses_fixed_parent_traversal"
    ):
        return "candidate_modified_setup"
    if setup_contract.get("candidate_setup_uses_fixed_parent_traversal") or "../../.." in lowered or "..\\..\\.." in lowered:
        return "starter_fragile_path"
    return "classifier_uncertain"


def _load_stage_records(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _redacted_stage_log(
    raw_stage_dir: Path,
    stage: str,
    *,
    fallback: str,
    root: Path,
    candidate_dir: Path,
) -> str:
    path = raw_stage_dir / f"{stage}.log"
    if path.is_file():
        raw = path.read_text(encoding="utf-8", errors="replace")
    else:
        raw = fallback
    return _redact_output(raw, root=root, candidate_dir=candidate_dir)


def _single_stage_dir(raw_stage_dir: Path) -> Path:
    """Return the one per-case stage directory written by the runner."""
    if not raw_stage_dir.is_dir():
        return raw_stage_dir
    candidates = sorted(path for path in raw_stage_dir.iterdir() if path.is_dir())
    return candidates[0] if candidates else raw_stage_dir


def _test_suite_failure_reason(text: str, *, failed: bool) -> str:
    if not failed:
        return "none"
    lowered = text.casefold()
    if "test-suite/run.sh: missing" in lowered or "missing_test_script" in lowered:
        return "missing_test_script"
    if re.search(r"(?i)(modulenotfounderror|importerror)", text):
        return "python_import_failed"
    if re.search(r"(?i)(syntaxerror|compileall|py_compile|python compile)", text):
        return "python_compile_failed"
    if re.search(r"(?i)assertion .*(test-suite|test_.*\.py) .*exited", text):
        return "assertion_failed"
    if "expected starter-repo cwd" in text or "codegen-benchmark-harness: ERROR:" in text or "test-suite exited" in lowered:
        return "behavior_failed"
    return "unknown"


def _security_failure_reason(text: str, *, failed: bool) -> str:
    if not failed:
        return "none"
    lowered = text.casefold()
    if "security-checks/run.sh: missing" in lowered or "missing_security_script" in lowered:
        return "missing_security_script"
    if re.search(r"(?i)(sensitive.*log|secret-token|token=|credential|query values)", text):
        return "sensitive_log_leak"
    if re.search(r"(?i)(ssrf|metadata|private address|loopback|link local|unsafe network|redirect.*revalidat)", text):
        return "unsafe_network_policy"
    if re.search(r"(?i)assertion .*security-checks.*exited", text):
        return "assertion_failed"
    return "unknown"


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
    raw_stage_dir = out_dir / "_raw-stage-logs"
    if raw_stage_dir.exists():
        shutil.rmtree(raw_stage_dir)
    command.extend(["--stage-log-dir", str(raw_stage_dir)])
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
    raw_combined = (
        f"returncode: {completed.returncode}\n\n"
        "stdout:\n"
        f"{completed.stdout}\n\n"
        "stderr:\n"
        f"{completed.stderr}\n"
    )
    combined = (
        f"command: {' '.join(redacted_command)}\n"
        f"returncode: {completed.returncode}\n\n"
        "stdout:\n"
        f"{stdout_text}\n\n"
        "stderr:\n"
        f"{stderr_text}\n"
    )
    stage_record_dir = _single_stage_dir(raw_stage_dir)
    stage_records = _load_stage_records(stage_record_dir / "stage-results.json")
    setup_log = _redacted_stage_log(
        _single_stage_dir(raw_stage_dir),
        "setup",
        fallback=combined,
        root=root,
        candidate_dir=candidate_dir,
    )
    test_suite_log = _redacted_stage_log(
        _single_stage_dir(raw_stage_dir),
        "test-suite",
        fallback=combined,
        root=root,
        candidate_dir=candidate_dir,
    )
    security_log = _redacted_stage_log(
        _single_stage_dir(raw_stage_dir),
        "security-checks",
        fallback=combined,
        root=root,
        candidate_dir=candidate_dir,
    )
    (out_dir / "setup.log").write_text(setup_log, encoding="utf-8")
    (out_dir / "test-suite.log").write_text(test_suite_log, encoding="utf-8")
    (out_dir / "security-checks.log").write_text(security_log, encoding="utf-8")

    all_passed = completed.returncode == 0
    stages = _stage_failures_from_records(stage_records, raw_combined, returncode=completed.returncode)
    first_failure_stage = _first_failure_stage(stages, all_passed=all_passed)
    first_failure_excerpt = "" if all_passed else _first_failure_excerpt(combined)
    setup_passed = all_passed or not stages["setup"]
    test_suite_passed = all_passed or not stages["test_suite"]
    security_checks_passed = all_passed or not stages["security_checks"]
    setup_contract = _setup_contract(benchmark, candidate_dir, root=root)
    setup_failure_reason = _setup_failure_reason(raw_combined, failed=not setup_passed)
    setup_failure_subreason = _setup_failure_subreason(
        raw_combined,
        failed=not setup_passed,
        setup_failure_reason=setup_failure_reason,
        setup_contract=setup_contract,
    )
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
        "setup_failure_reason": setup_failure_reason,
        "setup_failure_subreason": setup_failure_subreason,
        "setup_contract": setup_contract,
        "test_suite_failure_reason": _test_suite_failure_reason(raw_combined, failed=not test_suite_passed),
        "security_failure_reason": _security_failure_reason(raw_combined, failed=not security_checks_passed),
        "first_failure_stage": first_failure_stage,
        "first_failure_excerpt": first_failure_excerpt,
        "setup_log_excerpt": "" if setup_passed else _excerpt(setup_log),
        "test_suite_log_excerpt": ""
        if test_suite_passed
        else _stage_excerpt(test_suite_log, "test_suite", fallback=first_failure_excerpt),
        "security_log_excerpt": ""
        if security_checks_passed
        else _stage_excerpt(security_log, "security_checks", fallback=first_failure_excerpt),
        "logs": {
            "stdout": _grading_path(out_dir, stdout_path),
            "stderr": _grading_path(out_dir, stderr_path),
            "setup": _grading_path(out_dir, out_dir / "setup.log"),
            "test_suite": _grading_path(out_dir, out_dir / "test-suite.log"),
            "security_checks": _grading_path(out_dir, out_dir / "security-checks.log"),
        },
    }
    shutil.rmtree(raw_stage_dir, ignore_errors=True)
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
        "setup_failure_subreason": "none",
        "setup_contract": {field: False for field in SETUP_CONTRACT_FIELDS},
        "test_suite_failure_reason": "none",
        "security_failure_reason": "none",
        "first_failure_stage": "assertion_files",
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
