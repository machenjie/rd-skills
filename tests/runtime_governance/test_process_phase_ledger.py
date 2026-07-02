from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.process_phase import (  # noqa: E402
    artifact_digest,
    merge_process_phase_ledger,
    normalize_process_phase_ledger,
    phase_blockers,
    phase_ready_for_implementation,
    phase_review_passes,
    sanitize_phase_ledger,
    validate_process_phase_ledger,
)


def _digest(phase: str) -> str:
    return artifact_digest({"phase": phase, "facts": [phase, "source-backed"]})


def _review(phase: str, *, score: int = 5, verdict: str = "pass", digest: str | None = None) -> dict:
    return {
        "schema_version": 1,
        "review_id": f"{phase}-review-1",
        "phase": phase,
        "reviewer_skill": "ai-code-review-refactor",
        "owner_skill": "development-process-orchestrator",
        "reviewed_artifact_digest": digest or _digest(phase),
        "verdict": verdict,
        "score": score,
        "findings": [],
        "approved_scope": {"files": ["src/runtime_governance/process_phase.py"]},
        "required_next_action": ["proceed"],
        "residual_risk": [],
    }


def _full_ledger() -> dict:
    digests = {phase: _digest(phase) for phase in ("pdd", "ddd", "sdd", "tdd")}
    return {
        "schema_version": 1,
        "route_id": "active-runtime-route",
        "current_phase": "implementation",
        "required_phases": ["pdd", "ddd", "sdd", "tdd"],
        "phase_status": {phase: "reviewed" for phase in ("pdd", "ddd", "sdd", "tdd")},
        "phase_scores": {phase: 5 for phase in ("pdd", "ddd", "sdd", "tdd")},
        "artifact_digests": digests,
        "review_ids": {phase: f"{phase}-review-1" for phase in ("pdd", "ddd", "sdd", "tdd")},
        "blockers": [],
        "unresolved_blocking_choices": 0,
        "validation_signal_present": True,
        "updated_by_hook": "changeforge_process_phase_gate",
    }


class ProcessPhaseLedgerTests(unittest.TestCase):
    def test_valid_full_ledger_allows_implementation(self) -> None:
        ledger = normalize_process_phase_ledger(_full_ledger())

        self.assertEqual(validate_process_phase_ledger(ledger), [])
        self.assertTrue(phase_ready_for_implementation(ledger))
        self.assertEqual(phase_blockers(ledger), [])

    def test_missing_pdd_blocks_implementation(self) -> None:
        ledger = _full_ledger()
        ledger["phase_status"]["pdd"] = "pending"

        self.assertFalse(phase_ready_for_implementation(ledger))
        self.assertTrue(any("PDD" in blocker for blocker in phase_blockers(ledger)))

    def test_pdd_reviewed_but_ddd_missing_blocks_implementation(self) -> None:
        ledger = _full_ledger()
        ledger["phase_status"]["ddd"] = "pending"

        self.assertFalse(phase_ready_for_implementation(ledger))
        self.assertTrue(any("DDD" in blocker for blocker in phase_blockers(ledger)))

    def test_sdd_reviewed_with_unresolved_choice_blocks_implementation(self) -> None:
        ledger = _full_ledger()
        ledger["unresolved_blocking_choices"] = 1

        self.assertFalse(phase_ready_for_implementation(ledger))
        self.assertTrue(any("SDD" in blocker and "choice" in blocker for blocker in phase_blockers(ledger)))

    def test_tdd_without_validation_signal_blocks_implementation(self) -> None:
        ledger = _full_ledger()
        ledger["validation_signal_present"] = False

        self.assertFalse(phase_ready_for_implementation(ledger))
        self.assertTrue(any("TDD" in blocker and "validation_signal" in blocker for blocker in phase_blockers(ledger)))

    def test_not_applicable_without_reason_fails(self) -> None:
        ledger = _full_ledger()
        ledger["phase_status"]["ddd"] = "not_applicable"
        ledger["not_applicable_reasons"] = {}

        errors = validate_process_phase_ledger(ledger)
        self.assertTrue(any("not_applicable requires" in error for error in errors))

    def test_raw_prompt_and_secret_like_fields_are_dropped(self) -> None:
        ledger = sanitize_phase_ledger(
            {
                "route_id": "phase-route",
                "current_phase": "pdd",
                "required_phases": ["pdd", "ddd", "sdd", "tdd"],
                "phase_status": {"pdd": "pending"},
                "raw_prompt": "do not persist",
                "token": "do not persist",
                "blockers": [{"phase": "pdd", "reason": "API_TOKEN=value"}],
            }
        )

        self.assertNotIn("raw_prompt", ledger)
        self.assertNotIn("token", ledger)
        self.assertEqual(ledger["blockers"], [])

    def test_review_result_must_match_digest_and_pass_score(self) -> None:
        digest = _digest("pdd")
        passing = _review("pdd", digest=digest)
        stale = _review("pdd", digest=_digest("ddd"))
        low_score = _review("pdd", score=3, digest=digest)

        self.assertTrue(phase_review_passes(passing, artifact_digest=digest))
        self.assertFalse(phase_review_passes(stale, artifact_digest=digest))
        self.assertFalse(phase_review_passes(low_score, artifact_digest=digest))

    def test_merge_applies_latest_passing_review(self) -> None:
        digest = _digest("pdd")
        ledger = normalize_process_phase_ledger(
            {
                "artifact_digests": {"pdd": digest},
                "phase_status": {"pdd": "review_pending"},
            }
        )

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[_review("pdd", digest=digest)])

        self.assertEqual(merged["phase_status"]["pdd"], "reviewed")
        self.assertEqual(merged["review_ids"]["pdd"], "pdd-review-1")

    def test_passing_review_populates_missing_artifact_digest(self) -> None:
        digest = _digest("pdd")
        ledger = normalize_process_phase_ledger({"phase_status": {"pdd": "review_pending"}})

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[_review("pdd", digest=digest)])

        self.assertEqual(merged["phase_status"]["pdd"], "reviewed")
        self.assertEqual(merged["artifact_digests"]["pdd"], digest)
        self.assertEqual(merged["review_ids"]["pdd"], "pdd-review-1")

    def test_passing_review_with_matching_existing_digest_keeps_reviewed(self) -> None:
        digest = _digest("pdd")
        ledger = normalize_process_phase_ledger(
            {"artifact_digests": {"pdd": digest}, "phase_status": {"pdd": "review_pending"}}
        )

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[_review("pdd", digest=digest)])

        self.assertEqual(merged["phase_status"]["pdd"], "reviewed")
        self.assertEqual(merged["artifact_digests"]["pdd"], digest)

    def test_passing_review_with_stale_digest_marks_phase_failed(self) -> None:
        digest = _digest("pdd")
        stale_digest = _digest("ddd")
        ledger = normalize_process_phase_ledger(
            {"artifact_digests": {"pdd": digest}, "phase_status": {"pdd": "review_pending"}}
        )

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[_review("pdd", digest=stale_digest)])

        self.assertEqual(merged["phase_status"]["pdd"], "failed")
        self.assertEqual(merged["artifact_digests"]["pdd"], digest)
        self.assertTrue(any("did not pass" in item["reason"] for item in merged["blockers"]))

    def test_reviewed_phase_without_digest_is_invalid(self) -> None:
        ledger = _full_ledger()
        ledger["artifact_digests"].pop("pdd")

        errors = validate_process_phase_ledger(ledger)

        self.assertIn("pdd reviewed status requires artifact digest", errors)


if __name__ == "__main__":
    unittest.main()
