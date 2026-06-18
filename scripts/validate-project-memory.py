#!/usr/bin/env python3
"""Validate Project Memory Governance schemas, privacy, and promotion bounds."""

from __future__ import annotations

import json
import py_compile
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.privacy import contains_forbidden_key, repo_hash_for_path, sanitize_memory_event
from project_memory.review.promote_memory_candidate import supported_target
from project_memory.store.append_log import append_memory_event, iter_memory_events


SCHEMA_DIR = SRC / "project_memory" / "schemas"
REQUIRED_SCHEMAS = (
    "memory-event.v1.schema.json",
    "memory-summary.v1.schema.json",
    "memory-query.v1.schema.json",
    "memory-decision.v1.schema.json",
)
FORBIDDEN_PATHS = (
    ROOT / "src" / "toolbox",
    ROOT / "registry" / "toolbox.yaml",
    ROOT / "src" / "registry" / "toolbox.yaml",
)


def main() -> int:
    errors: list[str] = []
    _validate_schema_files(errors)
    _validate_python_compile(errors)
    _validate_privacy_sanitization(errors)
    _validate_append_log(errors)
    _validate_promotion_bounds(errors)
    _validate_forbidden_paths(errors)
    if errors:
        for error in errors:
            print(f"validate-project-memory: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-project-memory: OK")
    return 0


def _validate_schema_files(errors: list[str]) -> None:
    for name in REQUIRED_SCHEMAS:
        path = SCHEMA_DIR / name
        if not path.is_file():
            errors.append(f"missing schema: {path.relative_to(ROOT)}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
            continue
        if data.get("additionalProperties") is not False:
            errors.append(f"{path.relative_to(ROOT)} must set additionalProperties=false")
        if contains_forbidden_key(data.get("properties", {})):
            errors.append(f"{path.relative_to(ROOT)} exposes forbidden raw-data fields")


def _validate_python_compile(errors: list[str]) -> None:
    for path in sorted((SRC / "project_memory").rglob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path.relative_to(ROOT)} does not compile: {exc.msg}")


def _validate_privacy_sanitization(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory() as repo_s:
        repo = Path(repo_s)
        (repo / "src").mkdir()
        event = sanitize_memory_event(
            {
                "repo_hash": "",
                "task_fingerprint": "task",
                "type": "implementation_attempt",
                "paths": [str(repo / "src" / "app.py"), "/Users/example/private.py", "../escape.py"],
                "symbols": ["OrderService"],
                "prompt": "raw prompt must not survive",
                "env": {"TOKEN": "secret"},
                "stdout": "full command output",
                "evidence_refs": ["cmd:pytest", "Bearer secret-token-value"],
            },
            repo=repo,
        )
    if event["repo_hash"] != repo_hash_for_path(repo):
        errors.append("sanitizer must hash repo/workdir instead of recording absolute path")
    if event["paths"] != ["src/app.py"]:
        errors.append("sanitizer must keep only bounded relative paths")
    serialized = json.dumps(event)
    for forbidden in ("raw prompt", "TOKEN", "full command output", "/Users/example"):
        if forbidden in serialized:
            errors.append(f"sanitizer leaked forbidden value: {forbidden}")


def _validate_append_log(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp_s:
        root = Path(tmp_s) / "memory"
        event = append_memory_event(
            {
                "repo_hash": "repo",
                "task_fingerprint": "task",
                "type": "validation_result",
                "paths": ["src/app.py"],
                "outcome": "failed",
            },
            root=root,
            fail_open=False,
        )
        events = list(iter_memory_events(root))
    if event is None or len(events) != 1:
        errors.append("append log must write one JSONL event")


def _validate_promotion_bounds(errors: list[str]) -> None:
    for target in (
        "evals/agent-behavior/samples",
        "evals/pressure",
        "tests/fixtures/hooks",
        "tests/project_memory/fixtures",
    ):
        if not supported_target(target):
            errors.append(f"promotion allowlist unexpectedly rejects {target}")
    for target in (
        "SKILL.md",
        "src/registry/routing-rules.yaml",
        "src/registry/capabilities.yaml",
        "dist/universal/skills",
    ):
        if supported_target(target):
            errors.append(f"promotion allowlist must reject {target}")


def _validate_forbidden_paths(errors: list[str]) -> None:
    for path in FORBIDDEN_PATHS:
        if path.exists():
            errors.append(f"forbidden path exists: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())

