#!/usr/bin/env python3
"""Executable smoke harness used by codegen benchmark run scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from validation_utils import ValidationProblem, heading_titles, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]


def _fail(message: str) -> int:
    print(f"codegen-benchmark-harness: ERROR: {message}", file=sys.stderr)
    return 1


def _case_dir(starter_dir: Path) -> Path:
    resolved = starter_dir.resolve()
    if resolved.name != "starter-repo":
        raise ValueError(f"expected starter-repo cwd, got {resolved}")
    return resolved.parent


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


def _words(value: str) -> set[str]:
    stop = {
        "after",
        "before",
        "based",
        "only",
        "that",
        "with",
        "without",
        "used",
        "uses",
        "using",
        "from",
        "full",
        "source",
        "truth",
    }
    return {
        word
        for word in re.findall(r"[a-z0-9]+", value.casefold())
        if len(word) >= 4 and word not in stop
    }


def _has_forbidden_shortcut_coverage(case_dir: Path) -> bool:
    quality_path = case_dir / "expected-qualities.yaml"
    try:
        data = load_yaml_file(quality_path)
    except ValidationProblem:
        return False
    if not isinstance(data, dict):
        return False
    shortcuts = data.get("forbidden_shortcuts")
    if not isinstance(shortcuts, list):
        return False

    test_text = (case_dir / "test-suite" / "README.md").read_text(encoding="utf-8")
    rubric_text = (case_dir / "review-rubric.md").read_text(encoding="utf-8")
    auto_failures = _section(rubric_text, "Automatic Failure Conditions")
    coverage_text = f"{test_text}\n{auto_failures}"
    coverage_words = _words(coverage_text)
    for shortcut in shortcuts:
        if not isinstance(shortcut, str):
            continue
        shortcut_words = _words(shortcut)
        if shortcut_words and len(shortcut_words & coverage_words) >= min(2, len(shortcut_words)):
            return True
    return False


def _setup(starter_dir: Path) -> int:
    readme = starter_dir / "README.md"
    if not readme.is_file():
        return _fail(f"{readme}: missing starter README")
    text = readme.read_text(encoding="utf-8")
    titles = {title.casefold() for title in heading_titles(text)}
    for title in ("Starter Repo", "Stack", "Initial State", "Files", "Constraints"):
        if title.casefold() not in titles:
            return _fail(f"{readme}: missing heading {title!r}")
    print(f"setup: {starter_dir.parent.name} starter repo is installable")
    return 0


def _tests(starter_dir: Path) -> int:
    case_dir = _case_dir(starter_dir)
    if not _has_forbidden_shortcut_coverage(case_dir):
        return _fail(f"{case_dir}: no test or automatic failure covers forbidden_shortcuts")
    print(f"tests: {case_dir.parent.name}/{case_dir.name} benchmark checks are runnable")
    return 0


def _security(starter_dir: Path) -> int:
    case_dir = _case_dir(starter_dir)
    readme = case_dir / "security-checks" / "README.md"
    if not readme.is_file():
        return _fail(f"{readme}: missing security README")
    text = readme.read_text(encoding="utf-8")
    titles = {title.casefold() for title in heading_titles(text)}
    for title in ("Security Checks", "Threat Surface", "Required Checks", "Rejection Cases"):
        if title.casefold() not in titles:
            return _fail(f"{readme}: missing heading {title!r}")
    if "reject" not in text.casefold() and "fail" not in text.casefold():
        return _fail(f"{readme}: security checks must declare rejection behavior")
    print(f"security: {case_dir.parent.name}/{case_dir.name} checks are runnable")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        return _fail("usage: codegen_benchmark_harness.py <setup|tests|security> <starter-repo>")
    mode = argv[1]
    starter_dir = Path(argv[2])
    if mode == "setup":
        return _setup(starter_dir)
    if mode == "tests":
        return _tests(starter_dir)
    if mode == "security":
        return _security(starter_dir)
    return _fail(f"unknown mode {mode!r}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

