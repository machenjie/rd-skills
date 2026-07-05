#!/usr/bin/env python3
"""Evaluate deterministic Superpowers integration fixtures.

The fixtures verify source-level ChangeForge contracts for Superpowers-derived
engineering behavior. They do not call an LLM, inspect hook state, or require
ordinary agents to operate internal schemas.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from validation_utils import ValidationProblem, fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
DEFAULT_FIXTURE_DIR = ROOT / "evals" / "superpowers-integration"

from runtime_governance import (  # noqa: E402
    classify_user_requested_gate,
    find_internal_unawareness_violations,
    observation_from_mapping,
    reduce_execution_evidence,
    validate_repair_rereview_text,
    validate_task_review_text,
    validate_visible_plan,
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    fixtures = sorted(args.fixture_dir.rglob("*.yaml"))
    if not fixtures:
        print("eval-superpowers-integration: no fixtures found")
        return 0

    errors: list[str] = []
    checked_contracts = 0
    for fixture in fixtures:
        try:
            data = load_yaml_file(fixture)
        except ValidationProblem as exc:
            errors.append(f"{_rel(fixture)}: {exc}")
            continue
        fixture_errors, contract_count = _evaluate_fixture(fixture, data)
        checked_contracts += contract_count
        errors.extend(fixture_errors)

    print(
        "eval-superpowers-integration: "
        f"checked {len(fixtures)} fixture(s), {checked_contracts} contract target(s)"
    )
    return fail_many("eval-superpowers-integration", errors)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Directory containing Superpowers integration fixtures.",
    )
    return parser.parse_args(argv)


def _evaluate_fixture(path: Path, data: Any) -> tuple[list[str], int]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{_rel(path)}: fixture must be a mapping"], 0

    fixture_id = str(data.get("id") or _rel(path))
    contracts = data.get("required_contracts")
    if not isinstance(contracts, list) or not contracts:
        return [f"{fixture_id}: missing non-empty required_contracts"], 0

    forbidden_terms = _string_list(data.get("forbidden_contract_terms"))
    checked = 0
    for contract in contracts:
        if not isinstance(contract, dict):
            errors.append(f"{fixture_id}: required_contracts entries must be mappings")
            continue
        rel_path = contract.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            errors.append(f"{fixture_id}: contract entry missing path")
            continue
        target = ROOT / rel_path
        if not target.is_file():
            errors.append(f"{fixture_id}: missing target file {rel_path}")
            continue
        checked += 1
        text = target.read_text(encoding="utf-8")
        for needle in _string_list(contract.get("must_contain")):
            if needle not in text:
                errors.append(f"{fixture_id}: {rel_path} missing required text: {needle}")
        for term in forbidden_terms:
            if term in text:
                errors.append(f"{fixture_id}: {rel_path} contains forbidden internal term: {term}")
    errors.extend(_evaluate_visible_plan_cases(fixture_id, data.get("visible_plan_cases")))
    errors.extend(_evaluate_user_gate_cases(fixture_id, data.get("user_gate_cases")))
    errors.extend(_evaluate_review_cases(fixture_id, data.get("review_cases")))
    errors.extend(_evaluate_repair_rereview_cases(fixture_id, data.get("repair_rereview_cases")))
    errors.extend(_evaluate_internal_unawareness_cases(fixture_id, data.get("internal_unawareness_cases")))
    errors.extend(_evaluate_evidence_reducer_cases(fixture_id, data.get("evidence_reducer_cases")))
    errors.extend(_evaluate_routing_cases(fixture_id, data.get("routing_cases")))
    return errors, checked


def _evaluate_visible_plan_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        name = str(case.get("name") or "visible-plan")
        report = validate_visible_plan(str(case.get("input") or ""))
        expected = str(case.get("expected_status") or "").strip()
        if expected and report.status != expected:
            errors.append(f"{fixture_id}/{name}: expected visible plan status {expected}, got {report.status}")
        codes = {finding.code for finding in report.findings}
        for code in _string_list(case.get("expected_finding_codes")):
            if code not in codes:
                errors.append(f"{fixture_id}/{name}: missing visible plan finding code {code}")
    return errors


def _evaluate_user_gate_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        name = str(case.get("name") or "user-gate")
        result = classify_user_requested_gate(str(case.get("input") or ""))
        expected = str(case.get("expected_status") or "").strip()
        if expected and result.status != expected:
            errors.append(f"{fixture_id}/{name}: expected gate status {expected}, got {result.status}")
        expected_scope = str(case.get("expected_scope") or "").strip()
        if expected_scope and result.gate_scope != expected_scope:
            errors.append(f"{fixture_id}/{name}: expected gate scope {expected_scope}, got {result.gate_scope}")
        for needle in _string_list(case.get("evidence_required_contains")):
            if not any(needle in item for item in result.evidence_required):
                errors.append(f"{fixture_id}/{name}: gate evidence requirement missing {needle}")
    return errors


def _evaluate_review_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        name = str(case.get("name") or "review")
        result = validate_task_review_text(str(case.get("input") or ""))
        expected = str(case.get("expected_status") or "").strip()
        if expected and result.status != expected:
            errors.append(f"{fixture_id}/{name}: expected review status {expected}, got {result.status}")
        missing = set(result.missing)
        for item in _string_list(case.get("expected_missing")):
            if item not in missing:
                errors.append(f"{fixture_id}/{name}: missing review gap {item}")
    return errors


def _evaluate_repair_rereview_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        name = str(case.get("name") or "repair-rereview")
        result = validate_repair_rereview_text(str(case.get("input") or ""))
        expected = str(case.get("expected_status") or "").strip()
        if expected and result.status != expected:
            errors.append(f"{fixture_id}/{name}: expected repair status {expected}, got {result.status}")
        missing = set(result.missing)
        for item in _string_list(case.get("expected_missing")):
            if item not in missing:
                errors.append(f"{fixture_id}/{name}: missing repair gap {item}")
    return errors


def _evaluate_internal_unawareness_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        name = str(case.get("name") or "internal-unawareness")
        violations = find_internal_unawareness_violations(str(case.get("input") or ""))
        for item in _string_list(case.get("expected_violations")):
            if not any(item in violation for violation in violations):
                errors.append(f"{fixture_id}/{name}: missing internal-unawareness violation {item}")
        for item in _string_list(case.get("expected_no_violations")):
            if any(item in violation for violation in violations):
                errors.append(f"{fixture_id}/{name}: unexpected internal-unawareness violation {item}")
    return errors


def _evaluate_evidence_reducer_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        name = str(case.get("name") or "evidence-reducer")
        observation = observation_from_mapping(case.get("observation") if isinstance(case.get("observation"), dict) else {})
        report = reduce_execution_evidence(observation)
        expected = str(case.get("expected_status") or "").strip()
        if expected and report.status != expected:
            errors.append(f"{fixture_id}/{name}: expected reducer status {expected}, got {report.status}")
        text = report.to_public_text()
        for needle in _string_list(case.get("observed_gaps_contain")):
            if needle not in text:
                errors.append(f"{fixture_id}/{name}: reducer report missing {needle}")
    return errors


def _evaluate_routing_cases(fixture_id: str, cases: Any) -> list[str]:
    errors: list[str] = []
    for case in _mapping_cases(cases):
        case_id = str(case.get("case_id") or "").strip()
        if not case_id:
            errors.append(f"{fixture_id}/routing: missing case_id")
            continue
        candidate = case.get("candidate_output")
        candidate_path = ROOT / "evals" / "routing-outputs" / f"{case_id}.actual.yaml"
        if isinstance(candidate, str) and candidate.strip():
            candidate_path = _repo_path(Path(candidate.strip()))
        args = [
            sys.executable,
            str(ROOT / "scripts" / "eval-routing.py"),
            "--case",
            case_id,
            "--candidate-output",
            str(candidate_path),
        ]
        result = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
            errors.append(f"{fixture_id}/{case_id}: routing eval failed: {output}")
    return errors


def _mapping_cases(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
