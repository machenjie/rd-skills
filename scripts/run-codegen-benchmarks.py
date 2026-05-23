#!/usr/bin/env python3
"""Run executable ChangeForge code generation benchmark smoke checks."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from validation_utils import relpath


ROOT = Path(__file__).resolve().parents[1]
CODEGEN_DIR = ROOT / "evals" / "codegen"


def _expected_case_dirs() -> list[tuple[str, str, Path]]:
    cases: list[tuple[str, str, Path]] = []
    for category, case_ids in EXPECTED_BENCHMARKS.items():
        for case_id in case_ids:
            cases.append((category, case_id, CODEGEN_DIR / category / case_id))
    return cases


def _section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    level: int | None = None
    pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        if match.group(2).strip().casefold() == heading.casefold():
            start = index + 1
            level = len(match.group(1))
            break
    if start is None or level is None:
        return ""
    out: list[str] = []
    for line in lines[start:]:
        match = pattern.match(line)
        if match and len(match.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def _expected_commands_from_readme(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    section = _section(text, "Expected Commands")
    return [match.strip() for match in re.findall(r"`([^`]+)`", section)]


def _expected_commands_from_script(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    commands: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*#\s*expected-command:\s*(.+?)\s*$", line)
        if match:
            commands.append(match.group(1).strip())
    return commands


def _validate_scripts(case_dir: Path) -> list[str]:
    errors: list[str] = []
    required_scripts = (
        case_dir / "starter-repo" / "setup.sh",
        case_dir / "test-suite" / "run.sh",
        case_dir / "security-checks" / "run.sh",
    )
    for path in required_scripts:
        if not path.is_file():
            errors.append(f"{relpath(ROOT, path)}: missing required script")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"{relpath(ROOT, path)}: script must not be empty")

    test_readme = case_dir / "test-suite" / "README.md"
    test_run = case_dir / "test-suite" / "run.sh"
    if test_readme.is_file() and test_run.is_file():
        readme_commands = _expected_commands_from_readme(test_readme)
        script_commands = _expected_commands_from_script(test_run)
        if not readme_commands:
            errors.append(f"{relpath(ROOT, test_readme)}: Expected Commands must declare run.sh")
        elif readme_commands != script_commands:
            errors.append(
                f"{relpath(ROOT, test_readme)}: Expected Commands {readme_commands!r} "
                f"do not match {relpath(ROOT, test_run)} metadata {script_commands!r}"
            )
    return errors


def _run_script(label: str, script: Path, cwd: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        ["bash", str(script)],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode == 0:
        return True, completed.stdout
    return False, f"{label} exited {completed.returncode}\n{completed.stdout}"


def _run_case(category: str, case_id: str, case_dir: Path) -> list[str]:
    errors = _validate_scripts(case_dir)
    if errors:
        return errors

    starter_dir = case_dir / "starter-repo"
    steps = (
        ("setup", starter_dir / "setup.sh"),
        ("test-suite", Path("../test-suite/run.sh")),
        ("security-checks", Path("../security-checks/run.sh")),
    )
    for label, script in steps:
        ok, output = _run_script(label, script, starter_dir)
        if not ok:
            errors.append(f"{category}/{case_id}: {output.rstrip()}")
    return errors


def _select_cases(args: argparse.Namespace) -> list[tuple[str, str, Path]]:
    cases = _expected_case_dirs()
    if args.category:
        cases = [case for case in cases if case[0] == args.category]
    if args.benchmark:
        requested = set(args.benchmark)
        cases = [
            case
            for case in cases
            if case[1] in requested or f"{case[0]}/{case[1]}" in requested
        ]
    if args.limit is not None:
        cases = cases[: args.limit]
    return cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=sorted(EXPECTED_BENCHMARKS))
    parser.add_argument(
        "--benchmark",
        action="append",
        help="Benchmark id or category/id. May be provided more than once.",
    )
    parser.add_argument("--limit", type=int, help="Run only the first N selected benchmarks.")
    parser.add_argument("--list", action="store_true", help="List selected benchmarks and exit.")
    args = parser.parse_args(argv)

    cases = _select_cases(args)
    if args.list:
        for category, case_id, _case_dir in cases:
            print(f"{category}/{case_id}")
        return 0
    if not cases:
        print("run-codegen-benchmarks: no benchmarks selected.", file=sys.stderr)
        return 1

    errors: list[str] = []
    for category, case_id, case_dir in cases:
        errors.extend(_run_case(category, case_id, case_dir))

    if errors:
        for message in errors:
            print(f"run-codegen-benchmarks: ERROR: {message}", file=sys.stderr)
        return 1
    print(f"run-codegen-benchmarks: executed {len(cases)} benchmark(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
