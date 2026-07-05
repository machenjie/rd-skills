from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import (  # noqa: E402
    classify_user_requested_gate,
    find_internal_unawareness_violations,
    observation_from_mapping,
    reduce_execution_evidence,
    validate_repair_rereview_text,
    validate_task_review_text,
)


class ExecutionEvidenceReducerTests(unittest.TestCase):
    def test_user_gate_distinguishes_ordered_proof_from_bare_verify(self) -> None:
        gate = classify_user_requested_gate("先在一个样本上证明成功，再推广到所有样本，不要跳过这个 gate。")
        self.assertEqual(gate.status, "user_requested_gate")
        self.assertEqual(gate.gate_scope, "one first, then all")

        bare = classify_user_requested_gate("实现后 verify 一下。")
        self.assertEqual(bare.status, "normal_validation")

    def test_task_review_rejects_generic_looks_good(self) -> None:
        result = validate_task_review_text("Reviewed, looks good.")
        self.assertEqual(result.status, "fail")
        self.assertIn("spec_compliance", result.missing)
        self.assertIn("code_quality", result.missing)
        self.assertIn("reviewed_scope", result.missing)

    def test_repair_requires_rereview_for_important_findings(self) -> None:
        result = validate_repair_rereview_text(
            "Reviewer found Important issue in validation mapping. Implementer fixed it. Final says done."
        )
        self.assertEqual(result.status, "fail")
        self.assertIn("re_review_after_repair", result.missing)

    def test_repair_requires_rereview_for_important_label_without_issue_word(self) -> None:
        result = validate_repair_rereview_text("Important: validation mapping is missing. Fixed it.")

        self.assertEqual(result.status, "fail")
        self.assertIn("re_review_after_repair", result.missing)

    def test_repair_rereview_ignores_negated_high_severity_findings(self) -> None:
        result = validate_repair_rereview_text("No Critical or Important findings. Fixed minor typo.")

        self.assertTrue(result.passed)

    def test_repair_rereview_passes_when_targeted_rereview_is_visible(self) -> None:
        result = validate_repair_rereview_text("Critical finding F1 fixed. Re-review approved F1.")

        self.assertTrue(result.passed)

    def test_internal_unawareness_phrases_are_flagged(self) -> None:
        violations = find_internal_unawareness_violations(
            "I updated the rd-skills task ledger and fixed process_phase_ledgers."
        )
        self.assertIn("rd-skills task ledger", violations)
        self.assertIn("process_phase_ledgers", violations)

    def test_internal_unawareness_does_not_flag_ordinary_progress_ledger(self) -> None:
        violations = find_internal_unawareness_violations("I updated the progress ledger for the release.")

        self.assertEqual(violations, ())

    def test_reducer_reports_public_advisory_gaps(self) -> None:
        observation = observation_from_mapping(
            {
                "current_task": "Task 2",
                "planned_files": ["src/a.py"],
                "changed_files": ["src/a.py", "src/b.py"],
                "validation_commands": [],
                "review_text": "",
                "user_gate_text": "first on one sample, then all samples before proceeding",
                "final_handoff": "Done.",
            }
        )

        report = reduce_execution_evidence(observation)
        self.assertEqual(report.status, "advisory_risk")
        public_text = report.to_public_text()
        self.assertIn("outside the accepted plan", public_text)
        self.assertIn("no validation command", public_text)
        self.assertIn("Review evidence is missing", public_text)
        self.assertIn("AC -> PROVEN BY", public_text)

    def test_reducer_reports_when_plan_consistency_cannot_be_checked(self) -> None:
        observation = observation_from_mapping(
            {
                "changed_files": ["src/a.py"],
                "validation_commands": ["python3 -m unittest tests.test_a"],
                "validation_fresh_after_last_edit": True,
                "review_text": (
                    "Spec Compliance: pass\n"
                    "Code Quality: pass\n"
                    "Review scope: src/a.py\n"
                    "Findings: none by severity\n"
                    "Required next action: proceed\n"
                    "Residual Risk: none"
                ),
                "final_handoff": "AC: behavior works - PROVEN BY python3 -m unittest tests.test_a passed",
            }
        )

        report = reduce_execution_evidence(observation)

        self.assertEqual(report.status, "advisory_risk")
        self.assertIn("could not be checked because accepted plan files were not visible", report.to_public_text())

    def test_reducer_passes_bounded_complete_evidence(self) -> None:
        observation = observation_from_mapping(
            {
                "current_task": "Task 1",
                "planned_files": ["src/a.py"],
                "changed_files": ["src/a.py"],
                "validation_commands": ["python3 -m unittest tests.test_a"],
                "validation_fresh_after_last_edit": True,
                "review_text": (
                    "Spec Compliance: pass\n"
                    "Code Quality: pass\n"
                    "Review scope: src/a.py\n"
                    "Findings: none by severity\n"
                    "Required next action: proceed\n"
                    "Residual Risk: none"
                ),
                "final_handoff": "AC: behavior works - PROVEN BY python3 -m unittest tests.test_a passed",
            }
        )

        self.assertTrue(reduce_execution_evidence(observation).passed)


if __name__ == "__main__":
    unittest.main()
