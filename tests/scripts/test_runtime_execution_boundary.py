from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validation_utils as VALIDATION  # noqa: E402


TASK_ID = "runtime-capability-simplification-20260901"
CORE = VALIDATION.CORE_CONTRACTS
PROFILES = json.loads(
    (ROOT / "src/agent-profiles/role-agents.json").read_text(encoding="utf-8")
)


def _task_contract() -> dict[str, object]:
    return {
        "Task ID": TASK_ID,
        "Status": "in_progress",
        "Goal": "Change the bounded owner and prove the result.",
        "Owner": "owner.py",
        "Inputs": ["current source", "/tmp/readable-input.txt"],
        "Allowed Read Scope": ["owner.py", "/tmp/readable-input.txt"],
        "Allowed Write Scope": ["owner.py"],
        "Non-goals": ["No route or execution-level change."],
        "Dependencies": [],
        "Expected Output": ["Implementation Handoff"],
        "Acceptance": ["The owner behavior changes."],
        "Verification": ["targeted owner test"],
        "Evidence Requirements": ["fresh validation", "actual diff"],
        "Parallel Safety": "serialize shared-workspace writes",
        "Workspace Requirement": "shared workspace",
        "Integration Owner": "task-agent",
        "Review Owner": "review-agent",
        "Stop Conditions": ["actual host or tool failure"],
    }


class RuntimeExecutionBoundaryTests(unittest.TestCase):
    def test_ordinary_task_has_no_capability_preflight(self) -> None:
        task = CORE["task_contract"]
        review = CORE["review_discipline_contract"]
        self.assertNotIn("executor_substitution", task)
        self.assertNotIn("generic_capability_contract", review)
        boundary = task["execution_boundary"]
        self.assertEqual(["read", "search", "edit", "execute"], boundary["operations"])
        self.assertEqual("forbidden", boundary["preflight_capability_proof"])
        task_profile = next(
            profile for profile in PROFILES["profiles"]
            if profile["name"] == "task-agent"
        )["instructions"]
        for operation in ("read", "search", "edit", "execute"):
            self.assertIn(operation, task_profile)
        for obsolete in (
            "CAPABILITY_MISMATCH",
            "bounded-source-read",
            "workspace-mutation",
            "non-mutating-validation",
        ):
            self.assertNotIn(obsolete, task_profile)

    def test_successful_operations_continue_without_runtime_capability_facts(self) -> None:
        for operation, target in (
            ("read", "/tmp/readable-input.txt"),
            ("edit", "owner.py"),
            ("execute", "targeted owner test"),
        ):
            with self.subTest(operation=operation):
                outcome = VALIDATION.task_operation_outcome(
                    task_id=TASK_ID,
                    operation=operation,
                    target=target,
                    result="succeeded",
                )
                self.assertEqual(
                    {"status": "continue", "task_id": TASK_ID, "operation": operation},
                    outcome,
                )

    def test_actual_failures_return_observed_execution_blockers(self) -> None:
        cases = (
            (
                "read",
                "required-artifact-unavailable",
                "required artifact unavailable: /tmp/missing-input.txt",
            ),
            ("edit", "permission-denied", "permission denied: owner.py"),
            ("execute", "sandbox-denied", "sandbox denied: targeted owner test"),
            ("execute", "tool-unavailable", "tool unavailable: execute"),
        )
        for operation, failure_class, observed in cases:
            with self.subTest(operation=operation, failure_class=failure_class):
                outcome = VALIDATION.task_operation_outcome(
                    task_id=TASK_ID,
                    operation=operation,
                    target="bounded target",
                    result="failed",
                    failure_class=failure_class,
                    observed=observed,
                )
                self.assertEqual("blocked", outcome["status"])
                self.assertEqual(
                    f"EXECUTION_BLOCKED task={TASK_ID}; operation={operation}; "
                    f"observed={observed}",
                    outcome["blocker"],
                )
                self.assertEqual(
                    [],
                    VALIDATION.execution_blocker_errors(
                        outcome["blocker"], current_task_id=TASK_ID
                    ),
                )

    def test_unobserved_capability_names_cannot_create_a_blocker(self) -> None:
        with self.assertRaisesRegex(ValueError, "actual host or tool failure"):
            VALIDATION.task_operation_outcome(
                task_id=TASK_ID,
                operation="edit",
                target="owner.py",
                result="failed",
                failure_class="capability-unknown",
                observed="workspace-mutation is unknown",
            )

    def test_retry_preserves_task_id_and_complete_task_contract(self) -> None:
        original = _task_contract()
        retry = copy.deepcopy(original)
        self.assertEqual([], VALIDATION.task_retry_continuity_errors(original, retry))

        wrong_id = copy.deepcopy(retry)
        wrong_id["Task ID"] = "unspecified"
        errors = VALIDATION.task_retry_continuity_errors(original, wrong_id)
        self.assertTrue(any("Task ID" in error for error in errors), errors)

        incomplete = copy.deepcopy(retry)
        incomplete.pop("Acceptance")
        errors = VALIDATION.task_retry_continuity_errors(original, incomplete)
        self.assertTrue(any("complete Task Contract" in error for error in errors), errors)

    def test_review_without_actual_diff_remains_blocked(self) -> None:
        handoff = {
            "latest_changed_paths": ["owner.py"],
            "exact_change_evidence": {
                "kind": "changed-file-summary",
                "artifact": "owner.py changed",
                "generation": 3,
            },
            "reviewer_artifact_accessibility": {
                "reviewer": "review-agent",
                "generation": 3,
                "changed_paths": ["owner.py"],
                "readable": True,
            },
            "validation_after_latest_material_edit": {
                "evidence_id": "targeted-owner-test",
                "result": "passed",
                "generation": 3,
            },
            "fixed_review_scope": ["owner.py"],
        }
        self.assertFalse(VALIDATION.review_input_ready(handoff))
        handoff["exact_change_evidence"] = {
            "kind": "exact-change-content",
            "artifact": (
                "diff --git a/owner.py b/owner.py\n"
                "--- a/owner.py\n+++ b/owner.py\n@@ -1 +1 @@\n-old\n+new\n"
            ),
            "generation": 3,
        }
        self.assertTrue(VALIDATION.review_input_ready(handoff))


if __name__ == "__main__":
    unittest.main()
