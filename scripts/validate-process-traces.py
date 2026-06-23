#!/usr/bin/env python3
"""Validate Codex live benchmark PDD/DDD/SDD/TDD process traces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import read_json


PHASES = ("pdd", "ddd", "sdd", "tdd", "implementation", "validation", "review")
FORBIDDEN_TEXT = ("/Users/", "/home/", "C:\\Users\\", "auth.json", "CODEX_API_KEY", "OPENAI_API_KEY", "sk-")


def validate_process_traces(run_dir: Path) -> list[str]:
    errors: list[str] = []
    result_paths = sorted(run_dir.glob("cases/*/*/run-*/result.json"))
    for result_path in result_paths:
        result = read_json(result_path)
        if not isinstance(result, dict):
            continue
        if result.get("artifact_status", result.get("status")) not in {"collected", "failed", "partial"}:
            continue
        trace_path = result_path.parent / "process-trace.json"
        if not trace_path.exists():
            errors.append(f"{_rel(run_dir, trace_path)} is missing")
            continue
        trace = read_json(trace_path)
        if not isinstance(trace, dict):
            errors.append(f"{_rel(run_dir, trace_path)} must be a JSON object")
            continue
        errors.extend(_trace_errors(trace_path, run_dir, trace))
    return errors


def _trace_errors(path: Path, run_dir: Path, trace: dict[str, Any]) -> list[str]:
    label = _rel(run_dir, path)
    errors = _forbidden_text_errors(label, path.read_text(encoding="utf-8", errors="ignore"))
    for field in ("schema_version", "run_id", "case_id", "variant", "run_index", "phase_status", "traceability"):
        if field not in trace:
            errors.append(f"{label}: missing {field}")
    phase_status = trace.get("phase_status")
    if not isinstance(phase_status, dict):
        errors.append(f"{label}: phase_status must be an object")
    else:
        for phase in PHASES:
            if phase_status.get(phase) != "present":
                errors.append(f"{label}: phase {phase} must be present")
    facts = trace.get("process_facts")
    if not isinstance(facts, dict):
        errors.append(f"{label}: process_facts must be an object")
        facts = {}
    errors.extend(_pdd_errors(label, facts.get("pdd")))
    errors.extend(_ddd_errors(label, facts.get("ddd")))
    errors.extend(_sdd_errors(label, facts.get("sdd")))
    errors.extend(_tdd_errors(label, facts.get("tdd"), trace))
    traceability = trace.get("traceability")
    if not isinstance(traceability, dict):
        errors.append(f"{label}: traceability must be an object")
    else:
        for field in (
            "pdd_to_tests",
            "ddd_invariants_to_code_or_tests",
            "sdd_public_api_to_tests",
            "tdd_validation_commands_present",
        ):
            if traceability.get(field) is not True:
                errors.append(f"{label}: traceability.{field} must be true")
    for artifact in trace.get("artifacts", []):
        if not isinstance(artifact, str) or artifact.startswith("/") or artifact.startswith(".."):
            errors.append(f"{label}: artifact paths must be relative")
    return errors


def _pdd_errors(label: str, pdd: Any) -> list[str]:
    if not isinstance(pdd, dict):
        return [f"{label}: PDD facts are missing"]
    return _non_empty_list_errors(label, pdd, ("acceptance_criteria", "constraints", "non_goals", "risk_surfaces", "expected_behavior"), "PDD")


def _ddd_errors(label: str, ddd: Any) -> list[str]:
    if not isinstance(ddd, dict):
        return [f"{label}: DDD facts are missing"]
    errors = _non_empty_list_errors(label, ddd, ("domain_terms", "side_effect_boundaries"), "DDD")
    invariants = ddd.get("invariants")
    rationale = ddd.get("no_domain_state_rationale")
    if not (isinstance(invariants, list) and invariants) and not isinstance(rationale, str):
        errors.append(f"{label}: DDD requires invariants or explicit no-domain-state rationale")
    return errors


def _sdd_errors(label: str, sdd: Any) -> list[str]:
    if not isinstance(sdd, dict):
        return [f"{label}: SDD facts are missing"]
    return _non_empty_list_errors(label, sdd, ("modules", "public_api", "data_flow", "failure_modes"), "SDD")


def _tdd_errors(label: str, tdd: Any, trace: dict[str, Any]) -> list[str]:
    if not isinstance(tdd, dict):
        return [f"{label}: TDD facts are missing"]
    errors = _non_empty_list_errors(label, tdd, ("target_tests", "validation_commands", "red_green_refactor_trace"), "TDD")
    if not trace.get("validation_commands"):
        errors.append(f"{label}: top-level validation_commands are required")
    return errors


def _non_empty_list_errors(label: str, payload: dict[str, Any], fields: tuple[str, ...], prefix: str) -> list[str]:
    errors: list[str] = []
    for field in fields:
        value = payload.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"{label}: {prefix}.{field} must be a non-empty list")
    return errors


def _forbidden_text_errors(label: str, text: str) -> list[str]:
    return [f"{label}: contains forbidden marker {marker}" for marker in FORBIDDEN_TEXT if marker in text]


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    errors = validate_process_traces(args.run_dir)
    if errors:
        for error in errors:
            print(f"validate-process-traces: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-process-traces: process traces are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
