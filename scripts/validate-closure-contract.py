#!/usr/bin/env python3
"""Validate ChangeForge closure contract behavior."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def _load_hook_closure_contract():
    spec = importlib.util.spec_from_file_location(
        "changeforge_closure_contract_for_validator",
        SCRIPT_DIR / "changeforge_closure_contract.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _contract(state: dict[str, Any], *, runtime: str = "codex"):
    module = _load_hook_closure_contract()
    return module.ClosureContract.from_state(
        state,
        route_manifest_complete=True,
        stage_route_present=True,
        repository_context_present=True,
        implementation_preflight_complete=True,
        validation_evidence_present=True,
        review_evidence_present=True,
        residual_risk_present=True,
        runtime=runtime,
    )


def _phase_state(**overrides: object) -> dict[str, object]:
    digest = "sha256:" + ("a" * 64)
    phases = ("pdd", "ddd", "sdd", "tdd")
    state: dict[str, object] = {
        "runtime": "codex",
        "turn_stage": "repair",
        "changed_paths": ["src/runtime_governance/process_phase.py"],
        "validation_freshness_seen": True,
        "process_phase_ledger_seen": True,
        "process_phase_ledgers": [
            {
                "route_id": "active-runtime-route",
                "current_phase": "implementation",
                "required_phases": list(phases),
                "phase_status": {phase: "reviewed" for phase in phases},
                "artifact_digests": {phase: digest for phase in phases},
                "review_ids": {phase: f"{phase}-review-1" for phase in phases},
                "validation_signal_present": True,
            }
        ],
        "pdd_reviewed": True,
        "ddd_reviewed": True,
        "sdd_reviewed": True,
        "tdd_reviewed": True,
        "phase_review_findings": [
            {
                "finding_id": "sdd-001",
                "phase": "sdd",
                "severity": "high",
                "evidence": "material choice missing",
                "required_fix": "add choice evidence",
                "blocks_next_stage": True,
            }
        ],
    }
    state.update(overrides)
    return state


def _self_test() -> list[str]:
    errors: list[str] = []
    no_repair = _contract(_phase_state())
    if no_repair.verdict != "needs_repair" or "phase_repair" not in no_repair.missing_items:
        errors.append("expected blocking phase finding without repair to require phase_repair")
    no_rereview = _contract(
        _phase_state(phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}])
    )
    if no_rereview.verdict != "needs_review" or "phase_rereview" not in no_rereview.missing_items:
        errors.append("expected phase repair without rereview to require phase_rereview")
    closed = _contract(
        _phase_state(
            phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
            phase_rereview_events=[{"finding_id": "sdd-001", "verdict": "pass"}],
        )
    )
    if "phase_repair" in closed.missing_items or "phase_rereview" in closed.missing_items:
        errors.append("expected matching repair and pass rereview to close phase finding")
    stale = _contract(
        _phase_state(
            validation_freshness_seen=False,
            phase_repair_events=[{"finding_id": "sdd-001", "repair_summary": "fixed"}],
            phase_rereview_events=[{"finding_id": "sdd-001", "verdict": "pass"}],
        )
    )
    if stale.verdict != "needs_validation":
        errors.append("expected phase repair closure without fresh validation to need validation")
    missing_ledger = _contract(
        {
            "runtime": "codex",
            "turn_stage": "coding",
            "changed_paths": ["src/runtime_governance/process_phase.py"],
            "pdd_reviewed": True,
            "ddd_reviewed": True,
            "sdd_reviewed": True,
            "tdd_reviewed": True,
        }
    )
    if "phase_ledger" not in missing_ledger.missing_items:
        errors.append("expected engineering closure without phase ledger to fail")
    missing_reviews = _contract(
        {
            "runtime": "codex",
            "turn_stage": "coding",
            "changed_paths": ["src/runtime_governance/process_phase.py"],
            "process_phase_ledger_seen": True,
            "pdd_reviewed": True,
        }
    )
    if "phase_reviews" not in missing_reviews.missing_items:
        errors.append("expected engineering closure without phase reviews to fail")
    unsupported = _contract(
        {
            "runtime": "generic",
            "turn_stage": "coding",
            "changed_paths": ["src/runtime_governance/process_phase.py"],
        },
        runtime="generic",
    )
    if unsupported.adapter_supports_blocking or not unsupported.missing_items:
        errors.append("expected unsupported adapter closure to be degraded and not pass")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run built-in closure contract checks")
    args = parser.parse_args(argv)
    errors = _self_test() if args.self_test else []
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("closure contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
