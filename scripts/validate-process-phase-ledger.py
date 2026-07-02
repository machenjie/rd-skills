#!/usr/bin/env python3
"""Validate ChangeForge process phase ledger and review result contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.process_phase import (  # noqa: E402
    phase_review_passes,
    validate_phase_review_result,
    validate_process_phase_ledger,
)


def _valid_ledger() -> dict[str, Any]:
    digest = "sha256:" + ("a" * 64)
    return {
        "schema_version": 1,
        "route_id": "self-test-route",
        "current_phase": "implementation",
        "required_phases": ["pdd", "ddd", "sdd", "tdd"],
        "phase_status": {
            "pdd": "reviewed",
            "ddd": "reviewed",
            "sdd": "reviewed",
            "tdd": "reviewed",
        },
        "phase_scores": {"pdd": 5, "ddd": 5, "sdd": 5, "tdd": 5},
        "artifact_digests": {"pdd": digest, "ddd": digest, "sdd": digest, "tdd": digest},
        "review_ids": {
            "pdd": "pdd-review-1",
            "ddd": "ddd-review-1",
            "sdd": "sdd-review-1",
            "tdd": "tdd-review-1",
        },
        "blockers": [],
        "unresolved_blocking_choices": 0,
        "validation_signal_present": True,
        "updated_by_hook": "changeforge_process_phase_gate",
    }


def _valid_review() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "review_id": "sdd-review-1",
        "phase": "sdd",
        "reviewer_skill": "development-process-orchestrator",
        "owner_skill": "architecture-impact-reviewer",
        "reviewed_artifact_digest": "sha256:" + ("a" * 64),
        "verdict": "pass",
        "score": 5,
        "findings": [],
        "approved_scope": {"files": ["src/runtime_governance/process_phase.py"]},
        "not_reviewed": [],
        "required_next_action": ["proceed"],
        "residual_risk": [],
    }


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _self_test() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_process_phase_ledger(_valid_ledger()))
    missing_pdd = _valid_ledger()
    missing_pdd["phase_status"] = {**missing_pdd["phase_status"], "pdd": "pending"}
    missing_errors = validate_process_phase_ledger(missing_pdd)
    if not any("pdd" in error.lower() for error in missing_errors):
        errors.append("self-test expected missing PDD review to fail")
    errors.extend(validate_phase_review_result(_valid_review()))
    failed_review = {**_valid_review(), "verdict": "fail", "score": 2}
    errors.extend(validate_phase_review_result(failed_review))
    if phase_review_passes(failed_review, artifact_digest=failed_review["reviewed_artifact_digest"]):
        errors.append("self-test expected failed review to block phase pass")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSON ledger or phase review result files")
    parser.add_argument("--self-test", action="store_true", help="run built-in positive and negative checks")
    args = parser.parse_args(argv)

    errors: list[str] = []
    if args.self_test:
        errors.extend(_self_test())
    for path in args.paths:
        data = _load_json(path)
        if isinstance(data, dict) and "phase_review_result" in data:
            data = data["phase_review_result"]
        if isinstance(data, dict) and "process_phase_ledger" in data:
            data = data["process_phase_ledger"]
        if isinstance(data, dict) and "review_id" in data:
            item_errors = validate_phase_review_result(data)
        else:
            item_errors = validate_process_phase_ledger(data)
        errors.extend(f"{path}: {error}" for error in item_errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("process phase ledger validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
