#!/usr/bin/env python3
"""Validate bounded ChangeForge review capsule contracts."""

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

from runtime_governance.review_capsule import validate_review_capsule  # noqa: E402


def _valid_capsule() -> dict[str, Any]:
    digest = "sha256:" + ("a" * 64)
    return {
        "schema_version": 1,
        "capsule_id": "sdd-capsule-1",
        "review_type": "sdd",
        "user_request_summary": "Bounded summary of the engineering request.",
        "accepted_constraints": ["No raw prompt or command output."],
        "source_evidence": {
            "read_files": [
                {
                    "path": "src/runtime_governance/process_phase.py",
                    "digest": digest,
                    "excerpt_summary": "Process ledger normalization and validation.",
                }
            ],
            "searched_patterns": ["process_phase_ledger"],
        },
        "artifact_under_review": {
            "phase": "sdd",
            "artifact_digest": digest,
            "artifact_summary": "Bounded SDD summary.",
        },
        "allowed_context": [
            "user_request_summary",
            "accepted_constraints",
            "source_evidence",
            "artifact_under_review",
        ],
        "forbidden_inputs": [
            "raw prompt",
            "raw secrets",
            "full command output",
            "implementer self-approval",
            "unverified completion claims",
        ],
    }


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _self_test() -> list[str]:
    errors = validate_review_capsule(_valid_capsule())
    bad = {**_valid_capsule(), "raw_prompt": "must not persist"}
    bad_errors = validate_review_capsule(bad)
    if not any("forbidden" in error.lower() for error in bad_errors):
        errors.append("self-test expected raw prompt key to fail")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSON review capsule files")
    parser.add_argument("--self-test", action="store_true", help="run built-in positive and negative checks")
    args = parser.parse_args(argv)

    errors: list[str] = []
    if args.self_test:
        errors.extend(_self_test())
    for path in args.paths:
        data = _load_json(path)
        if isinstance(data, dict) and "review_capsule" in data:
            data = data["review_capsule"]
        errors.extend(f"{path}: {error}" for error in validate_review_capsule(data))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("review capsule validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
