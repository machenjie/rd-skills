#!/usr/bin/env python3
"""Measure complete native-schema Expert Panel storage currentness validation.

Run this file from the repository revision under measurement. Fixture creation,
Git setup, imports, and correctness controls are excluded from timing; only
``_validate_current_expert_panel_storage(formal=False)`` is sampled.
"""

from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock


def _canonical_bytes(value: dict) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _fixture(case: str):
    repository_root = Path.cwd().resolve()
    if not (repository_root / "tests" / "scripts").is_dir():
        raise RuntimeError("run the benchmark from the repository root")
    sys.path.insert(0, str(repository_root))
    from tests.scripts.test_professionalism_expert_panel import (
        REGRESSION,
        ProfessionalismExpertPanelTests,
        _current_semantic_attestation,
    )

    audit, _packet, selector, raw = _current_semantic_attestation(
        ("root", "reference")
    )
    if case == "stale":
        audit = copy.deepcopy(audit)
        if selector["schema_version"] == 1:
            audit["root_content"]["semantic_advisories"]["candidates"][0][
                "preview"
            ] += " changed-local-context"
        else:
            entry = audit["root_content"]["semantic_advisories"][
                "disposition_contract"
            ]["entries"][0]
            entry["disposition"] = next(
                disposition
                for disposition in (
                    "false-positive",
                    "valid-contextual-rule",
                    "time-bounded-exception",
                )
                if disposition != entry["disposition"]
            )
    elif case == "tampered":
        selector = copy.deepcopy(selector)
        selector["verdict"] = "tampered-derived-verdict"
        raw = _canonical_bytes(selector)
    elif case != "current":
        raise ValueError(f"unsupported case: {case}")
    return (
        REGRESSION,
        ProfessionalismExpertPanelTests(),
        audit,
        selector,
        raw,
    )


def _prepared_case(case: str):
    regression, test_case, audit, selector, raw = _fixture(case)
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    semantic_path = (
        regression.expert_panel.panel_attestation
        .SEMANTIC_DISPOSITION_ATTESTATION_PATH
    )
    test_case._storage_repo(
        root,
        tracked={
            "reports/skill-content-audit.json": _canonical_bytes(audit),
            semantic_path: raw,
        },
    )
    patches = (
        mock.patch.object(regression, "ROOT", root),
        mock.patch.object(regression.expert_panel, "ROOT", root),
    )
    return regression, temporary, patches, selector


def _observe(case: str) -> dict:
    regression, temporary, patches, selector = _prepared_case(case)
    try:
        with patches[0], patches[1]:
            try:
                statuses = regression._validate_current_expert_panel_storage(
                    formal=False
                )
            except Exception as exc:  # The tamper oracle records exact rejection.
                return {
                    "outcome": "rejected",
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                    "storage_schema": selector["schema_version"],
                    "target_count": len(selector["findings"]),
                }
            return {
                "outcome": "statuses",
                "statuses": statuses,
                "storage_schema": selector["schema_version"],
                "target_count": len(selector["findings"]),
            }
    finally:
        temporary.cleanup()


def _measure(*, warmups: int, repetitions: int) -> tuple[dict, list[float]]:
    regression, temporary, patches, selector = _prepared_case("current")
    try:
        with patches[0], patches[1]:
            result = None
            for _ in range(warmups):
                result = regression._validate_current_expert_panel_storage(
                    formal=False
                )
            samples = []
            for _ in range(repetitions):
                started = time.perf_counter()
                result = regression._validate_current_expert_panel_storage(
                    formal=False
                )
                samples.append(time.perf_counter() - started)
        return {
            "statuses": result,
            "storage_schema": selector["schema_version"],
            "target_count": len(selector["findings"]),
        }, samples
    finally:
        temporary.cleanup()


def _assert_oracles(cases: dict, timed: dict) -> None:
    semantic = "semantic-disposition"
    expected_current = {
        "professional-completeness": "missing",
        "readability": "missing",
        semantic: "current",
    }
    expected_stale = {**expected_current, semantic: "stale"}
    if cases["current"].get("statuses") != expected_current:
        raise RuntimeError("current compact fixture did not validate as current")
    if cases["stale"].get("statuses") != expected_stale:
        raise RuntimeError("stale compact fixture did not validate as stale")
    if cases["tampered"].get("outcome") != "rejected":
        raise RuntimeError("tampered compact fixture was not rejected")
    if timed["statuses"] != expected_current:
        raise RuntimeError("timed workload did not retain the current oracle")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.warmups < 1 or args.repetitions < 3:
        parser.error("require at least one warmup and three repetitions")

    cases = {case: _observe(case) for case in ("current", "stale", "tampered")}
    timed, samples = _measure(
        warmups=args.warmups,
        repetitions=args.repetitions,
    )
    _assert_oracles(cases, timed)
    result = {
        "schema_version": 1,
        "workload": (
            "native compact Semantic full-axis storage validation through "
            "_validate_current_expert_panel_storage(formal=False)"
        ),
        "setup_excluded": [
            "module imports",
            "fixture construction",
            "temporary Git repository creation",
            "warmup runs",
        ],
        "warmups": args.warmups,
        "repetitions": args.repetitions,
        "cases": cases,
        "timed_oracle": timed,
        "samples_seconds": samples,
        "median_seconds": statistics.median(samples),
        "limitations": [
            "Each revision uses its native compact schema, so this compares equivalent trust checks rather than identical serialized bytes.",
            "The full-axis target set may differ when detector contracts change between revisions.",
            "Host-local elapsed time does not prove CI, real-host, provider, or production latency.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
