from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import validate_visible_plan  # noqa: E402


VALID_PLAN = """# Implementation Plan

## Task 1: Add visible plan validator

Goal:
Validate visible Markdown task contracts without asking ordinary agents to read internal schemas.

Files:
- Inspect: src/runtime_governance/visible_plan_parser.py
- Modify: src/runtime_governance/visible_plan_validator.py
- Test: tests/runtime_governance/test_visible_plan_validator.py

Acceptance Criteria:
- Missing task fields produce human-readable findings.
- Placeholder task language is rejected with exact replacement guidance.

Verify:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_validator

Expected:
- unittest reports OK.

Review:
- Check validator precision, over-trigger risk, and report wording.

Stop Conditions:
- Stop if validation requires the agent to edit internal metadata, hook state, or ledgers.

Rollback:
- Remove the validator module, export, and focused tests.
"""


class VisiblePlanValidatorTests(unittest.TestCase):
    def test_complete_visible_plan_passes(self) -> None:
        report = validate_visible_plan(VALID_PLAN)

        self.assertTrue(report.passed)
        self.assertEqual(report.task_count, 1)
        self.assertEqual(report.to_human_readable_text(), "Implementation plan quality: pass.")

    def test_missing_required_fields_are_human_readable(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Incomplete task
Goal:
Add a validator.
"""
        )

        messages = "\n".join(finding.message for finding in report.findings)
        self.assertFalse(report.passed)
        self.assertIn("has no Files section", messages)
        self.assertIn("has no Acceptance Criteria section", messages)
        self.assertIn("has no observable Verify command or check", messages)

    def test_rejects_placeholder_plan_text(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Fill in broad tasks
Goal:
Add proper error handling and write tests.
Files:
- src/runtime_governance/visible_plan_validator.py
Acceptance Criteria:
- Handle edge cases.
Verify:
- Command: validate it works
Expected:
- Similar to above.
Review:
- Review as needed.
Stop Conditions:
- Stop on unclear scope.
"""
        )

        self.assertFalse(report.passed)
        codes = {finding.code for finding in report.findings}
        self.assertIn("placeholder_text", codes)

    def test_flags_multi_risk_task_for_splitting(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Change API schema auth rollout
Goal:
Change the API response contract, migrate schema data, update authorization, and deploy the rollout.
Files:
- src/registry/routing-rules.yaml
Acceptance Criteria:
- API clients keep compatible behavior during migration.
Verify:
- Command: python3 scripts/eval-routing.py
Expected:
- route eval passes.
Review:
- Review API, schema, auth, and release behavior.
Stop Conditions:
- Stop if consumer compatibility is unknown.
"""
        )

        codes = {finding.code for finding in report.findings}
        self.assertIn("multi_risk_task", codes)
        self.assertIn("missing_rollback_note", codes)

    def test_human_report_does_not_expose_internal_control_plane_terms(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Incomplete visible task
Goal:
Keep the visible contract natural language.
"""
        )

        text = report.to_human_readable_text()
        forbidden_terms = (
            "InternalTaskNode",
            "InternalTaskGraph",
            "schema path",
            "digest",
            "ledger",
            "hook event",
            "hook state",
            "node id",
        )
        for term in forbidden_terms:
            self.assertNotIn(term, text)

    def test_minimal_plan_handoff_passes_with_minimal_required_fields(self) -> None:
        report = validate_visible_plan(
            """# Plan Handoff

Files:
- Inspect: `src/runtime_governance/visible_plan_parser.py`
- Modify: `src/runtime_governance/visible_plan_validator.py`
- Test: `tests/runtime_governance/test_visible_plan_validator.py`

Verify:
- Command: `python3 -m unittest tests.runtime_governance.test_visible_plan_validator`

Residual Risk:
- Does not prove full release packaging.
""",
            mode="minimal",
        )

        self.assertTrue(report.passed)
        self.assertEqual(report.task_count, 1)

    def test_auto_mode_recognizes_minimal_plan_handoff(self) -> None:
        report = validate_visible_plan(
            """# Plan Handoff

Files:
- Modify: `src/runtime_governance/visible_plan_validator.py`
Verify:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_validator
Residual Risk:
- Limited to validator behavior.
"""
        )

        self.assertTrue(report.passed)

    def test_auto_mode_recognizes_minimal_task_handoff_shape(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Small change
Files:
- Modify: `src/runtime_governance/visible_plan_validator.py`
Verify:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_validator
Residual Risk:
- Limited to validator mode selection.
"""
        )

        self.assertTrue(report.passed)
        self.assertEqual(report.task_count, 1)

    def test_auto_mode_keeps_full_task_validation_when_full_sections_appear(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Incomplete full task
Goal:
Change full-plan behavior.
Files:
- Modify: `src/runtime_governance/visible_plan_validator.py`
Verify:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_validator
Residual Risk:
- Limited to validator mode selection.
"""
        )

        self.assertFalse(report.passed)
        self.assertIn("missing_acceptance_criteria", {finding.code for finding in report.findings})

    def test_auto_mode_recognizes_chinese_minimal_task_handoff_shape(self) -> None:
        report = validate_visible_plan(
            """# Implementation Plan

## Task 1: Small change
文件：
- 修改：`src/runtime_governance/visible_plan_validator.py`
验证：
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_validator
残余风险：
- Limited to validator mode selection.
"""
        )

        self.assertTrue(report.passed)

    def test_minimal_plan_handoff_requires_residual_risk(self) -> None:
        report = validate_visible_plan(
            """# Plan Handoff

Files:
- Modify: src/runtime_governance/visible_plan_validator.py
Verify:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_validator
""",
            mode="minimal",
        )

        self.assertFalse(report.passed)
        self.assertIn("missing_residual_risk", {finding.code for finding in report.findings})


if __name__ == "__main__":
    unittest.main()
