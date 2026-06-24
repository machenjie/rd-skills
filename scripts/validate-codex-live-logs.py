#!/usr/bin/env python3
"""Validate sanitized Codex live benchmark structured logs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import read_json


FORBIDDEN_TEXT = ("/Users/", "/home/", "C:\\Users\\", "auth.json", "CODEX_API_KEY", "OPENAI_API_KEY", "sk-")
FORBIDDEN_KEYS = {"raw_prompt", "raw_command", "prompt_body", "command_body", "aggregated_output", "raw_output"}
PHASES = {"pdd", "ddd", "sdd", "tdd", "implementation", "validation", "review", "grading", "summary"}
EVENTS = {
    "phase_started",
    "phase_completed",
    "process_trace_evaluation_started",
    "process_trace_evaluation_completed",
    "process_phase_evaluated",
    "artifact_written",
    "validation_failed",
    "degraded",
    "retry",
    "skipped",
}
STATUSES = {"ok", "failed", "degraded", "skipped", "collected", "partial", "inferred", "missing", "present"}
MAX_EVENT_BYTES = 4096


def validate_run_logs(run_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest = read_json(run_dir / "run-manifest.json")
    live_effective = isinstance(manifest, dict) and bool(manifest.get("live_execution_effective"))
    if live_effective or (run_dir / "run.log.jsonl").exists() or (run_dir / "timeline.jsonl").exists():
        for name in ("run.log.jsonl", "timeline.jsonl"):
            path = run_dir / name
            if not path.exists():
                errors.append(f"{name} is missing")
                continue
            errors.extend(_validate_jsonl(path, run_dir))
    for trace_path in sorted(run_dir.glob("cases/*/*/run-*/process-trace.json")):
        errors.extend(_validate_json_file(trace_path, run_dir))
    return errors


def _validate_jsonl(path: Path, run_dir: Path) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > MAX_EVENT_BYTES:
            errors.append(f"{_rel(run_dir, path)}:{line_number}: event exceeds {MAX_EVENT_BYTES} bytes")
        errors.extend(_forbidden_text_errors(_rel(run_dir, path), line))
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{_rel(run_dir, path)}:{line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"{_rel(run_dir, path)}:{line_number}: event must be an object")
            continue
        errors.extend(_event_errors(f"{_rel(run_dir, path)}:{line_number}", payload))
    return errors


def _validate_json_file(path: Path, run_dir: Path) -> list[str]:
    label = _rel(run_dir, path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors = _forbidden_text_errors(label, text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return [*errors, f"{label}: invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        errors.append(f"{label}: payload must be an object")
        return errors
    errors.extend(_forbidden_key_errors(label, payload))
    for artifact in payload.get("artifacts", []):
        if not isinstance(artifact, str) or artifact.startswith("/") or artifact.startswith(".."):
            errors.append(f"{label}: artifact paths must be relative")
    return errors


def _event_errors(label: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ("schema_version", "ts", "run_id", "phase", "event", "status")
    for field in required:
        if field not in payload:
            errors.append(f"{label}: missing {field}")
    if payload.get("phase") not in PHASES:
        errors.append(f"{label}: invalid phase {payload.get('phase')!r}")
    if payload.get("event") not in EVENTS:
        errors.append(f"{label}: invalid event {payload.get('event')!r}")
    if payload.get("status") not in STATUSES:
        errors.append(f"{label}: invalid status {payload.get('status')!r}")
    artifact = payload.get("artifact")
    if isinstance(artifact, str) and (artifact.startswith("/") or artifact.startswith("..")):
        errors.append(f"{label}: artifact paths must be relative")
    errors.extend(_forbidden_key_errors(label, payload))
    return errors


def _forbidden_text_errors(label: str, text: str) -> list[str]:
    return [f"{label}: contains forbidden marker {marker}" for marker in FORBIDDEN_TEXT if marker in text]


def _forbidden_key_errors(label: str, payload: Any) -> list[str]:
    errors: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"{label}: contains forbidden raw field {key}")
            errors.extend(_forbidden_key_errors(label, value))
    elif isinstance(payload, list):
        for item in payload:
            errors.extend(_forbidden_key_errors(label, item))
    return errors


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    errors = validate_run_logs(args.run_dir)
    if errors:
        for error in errors:
            print(f"validate-codex-live-logs: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-codex-live-logs: logs are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
