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
    sanitize_phase_artifact,
    sanitize_phase_ledger,
    validate_phase_artifact,
    validate_process_phase_ledger,
)


def _digest(phase: str) -> str:
    return artifact_digest({"phase": phase, "facts": [phase, "source-backed"]})


def _review(phase: str, *, score: int = 5, verdict: str = "pass", digest: str | None = None) -> dict:
    digest = digest or _digest(phase)
    return {
        "schema_version": 1,
        "review_id": f"{phase}-review-1",
        "phase": phase,
        "reviewer_skill": "ai-code-review-refactor",
        "owner_skill": "development-process-orchestrator",
        "reviewed_artifact_digest": digest,
        "review_source": "subagent_review_gate",
        "capsule_id": f"{phase}-capsule-1",
        "expected_artifact_digest": digest,
        "review_context_strength": "strong",
        "reviewer_boundary": "subagent",
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

    def test_tdd_without_validation_signal_allows_implementation(self) -> None:
        ledger = _full_ledger()
        ledger["validation_signal_present"] = False

        self.assertTrue(phase_ready_for_implementation(ledger))
        self.assertFalse(any("TDD" in blocker and "validation_signal" in blocker for blocker in phase_blockers(ledger)))

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

    def test_phase_review_without_review_source_cannot_pass(self) -> None:
        digest = _digest("pdd")
        review = _review("pdd", digest=digest)
        review.pop("review_source")

        self.assertFalse(phase_review_passes(review, artifact_digest=digest))

    def test_phase_review_final_handoff_disclosure_cannot_pass(self) -> None:
        digest = _digest("pdd")
        review = _review("pdd", digest=digest)
        review["review_source"] = "final_handoff_disclosure"
        review["review_context_strength"] = "weak"
        review["reviewer_boundary"] = "unknown"

        self.assertFalse(phase_review_passes(review, artifact_digest=digest))

    def test_parent_independent_review_with_strong_provenance_can_pass(self) -> None:
        digest = _digest("pdd")
        review = _review("pdd", digest=digest)
        review["review_source"] = "parent_independent_review_gate"
        review["reviewer_boundary"] = "parent_context"

        self.assertTrue(phase_review_passes(review, artifact_digest=digest))

    def test_weak_review_context_blocks_phase(self) -> None:
        digest = _digest("pdd")
        review = _review("pdd", digest=digest)
        review["review_context_strength"] = "weak"

        self.assertFalse(phase_review_passes(review, artifact_digest=digest))

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
        self.assertTrue(any("did not pass" in item["reason"] or "stale" in item["reason"] for item in merged["blockers"]))

    def test_apply_phase_reviews_rejects_missing_provenance(self) -> None:
        digest = _digest("pdd")
        ledger = normalize_process_phase_ledger(
            {"artifact_digests": {"pdd": digest}, "phase_status": {"pdd": "review_pending"}}
        )
        review = _review("pdd", digest=digest)
        review.pop("review_source")

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[review])

        self.assertEqual(merged["phase_status"]["pdd"], "failed")

    def test_apply_phase_reviews_rejects_final_handoff_source(self) -> None:
        digest = _digest("pdd")
        ledger = normalize_process_phase_ledger(
            {"artifact_digests": {"pdd": digest}, "phase_status": {"pdd": "review_pending"}}
        )
        review = _review("pdd", digest=digest)
        review["review_source"] = "final_handoff_disclosure"
        review["review_context_strength"] = "weak"

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[review])

        self.assertEqual(merged["phase_status"]["pdd"], "failed")

    def test_apply_phase_reviews_accepts_subagent_review_gate_source(self) -> None:
        digest = _digest("pdd")
        ledger = normalize_process_phase_ledger(
            {"artifact_digests": {"pdd": digest}, "phase_status": {"pdd": "review_pending"}}
        )

        merged = merge_process_phase_ledger(ledger, {}, phase_review_results=[_review("pdd", digest=digest)])

        self.assertEqual(merged["phase_status"]["pdd"], "reviewed")

    def test_reviewed_phase_without_digest_is_invalid(self) -> None:
        ledger = _full_ledger()
        ledger["artifact_digests"].pop("pdd")

        errors = validate_process_phase_ledger(ledger)

        self.assertIn("pdd reviewed status requires artifact digest", errors)

    def test_phase_artifact_placeholder_summary_is_invalid(self) -> None:
        artifact = sanitize_phase_artifact(
            {
                "phase": "pdd",
                "artifact_summary": {
                    "problem": "todo",
                    "impact": "generic",
                    "acceptance_criteria": [],
                    "constraints": "unknown",
                    "non_goals": "n/a",
                    "risk_surfaces": "none",
                },
                "traceability": {"acceptance_ids": []},
            }
        )

        errors = validate_phase_artifact(artifact)

        self.assertTrue(any("artifact_summary.problem" in error for error in errors), errors)
        self.assertTrue(any("traceability.acceptance_ids" in error for error in errors), errors)

    def test_tdd_phase_artifact_requires_plan_not_execution_result(self) -> None:
        artifact = sanitize_phase_artifact(
            {
                "phase": "tdd",
                "artifact_summary": {
                    "acceptance_to_tests": ["AC-1 -> test_notification_summary_includes_1h_change"],
                    "invariant_to_tests": ["INV-1 -> test_no_empty_exchange_symbol"],
                    "failure_mode_tests": ["network timeout -> degraded notification omitted"],
                    "validation_commands": ["go test -count=1 ./processor/cryptoai/app/notification"],
                    "tests_do_not_prove": ["live integration timing"],
                },
                "source_evidence": {"read_files": ["processor/cryptoai/app/notification/render.go"]},
                "traceability": {"acceptance_ids": ["AC-1"], "invariant_ids": ["INV-1"], "test_ids": ["T-1"]},
            }
        )

        self.assertEqual(validate_phase_artifact(artifact), [])


if __name__ == "__main__":
    unittest.main()
