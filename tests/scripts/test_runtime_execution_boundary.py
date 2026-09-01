from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
        self.assertEqual(
            "path-segment-aware; star-question-and-character-classes-never-cross-slash; "
            "standalone-double-star-matches-zero-or-more-directory-segments; "
            "src/**/*.py-matches-src/file.py-and-src/nested/file.py",
            boundary["scope_preflight"]["glob_matching"],
        )
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

    def test_successful_operations_preflight_then_call_host_without_capability_facts(self) -> None:
        for operation, target, write_targets in (
            ("read", "/tmp/readable-input.txt", []),
            ("edit", "owner.py", []),
            ("execute", "targeted owner test", []),
        ):
            with self.subTest(operation=operation):
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=_task_contract(),
                    operation=operation,
                    target=target,
                    workspace_root=ROOT,
                    write_targets=write_targets,
                )
                self.assertEqual("authorized", preflight["status"])
                host_tool = mock.Mock(return_value="ok")
                self.assertEqual("ok", host_tool())
                host_tool.assert_called_once_with()

    def test_actual_missing_file_read_can_be_formatted_after_host_failure(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            missing = Path(temporary) / "missing-input.txt"
            contract = _task_contract()
            contract["Allowed Read Scope"] = [str(missing)]
            preflight = VALIDATION.task_operation_preflight(
                task_contract=contract,
                operation="read",
                target=str(missing),
                workspace_root=ROOT,
            )
            self.assertEqual("authorized", preflight["status"])
            try:
                missing.read_text(encoding="utf-8")
            except FileNotFoundError as exc:
                raw_error = str(exc)
            else:  # pragma: no cover - the path is deliberately absent
                self.fail("missing-file read unexpectedly succeeded")
            blocker = VALIDATION.format_execution_blocker(
                task_id=TASK_ID,
                operation="read",
                observed=raw_error,
            )
        self.assertEqual(
            f"EXECUTION_BLOCKED task={TASK_ID}; operation=read; observed={raw_error}",
            blocker,
        )
        self.assertEqual(
            [],
            VALIDATION.execution_blocker_errors(
                blocker,
                current_task_id=TASK_ID,
                expected_operation="read",
            ),
        )

    def test_mock_bound_host_failures_are_invoked_before_syntax_formatting(self) -> None:
        cases = (
            ("edit", "owner.py", PermissionError("permission denied: owner.py")),
            ("execute", "targeted owner test", RuntimeError("sandbox denied: targeted owner test")),
            ("execute", "targeted owner test", FileNotFoundError("tool unavailable: execute")),
        )
        for operation, target, failure in cases:
            with self.subTest(operation=operation, failure=type(failure).__name__):
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=_task_contract(),
                    operation=operation,
                    target=target,
                    workspace_root=ROOT,
                )
                self.assertEqual("authorized", preflight["status"])
                host_tool = mock.Mock(side_effect=failure)
                with self.assertRaises(type(failure)) as caught:
                    host_tool()
                host_tool.assert_called_once_with()
                blocker = VALIDATION.format_execution_blocker(
                    task_id=TASK_ID,
                    operation=operation,
                    observed=str(caught.exception),
                )
                self.assertEqual(
                    f"EXECUTION_BLOCKED task={TASK_ID}; operation={operation}; "
                    f"observed={caught.exception}",
                    blocker,
                )

    def test_static_blocker_parser_is_syntax_only_not_failure_authority(self) -> None:
        forged = VALIDATION.format_execution_blocker(
            task_id=TASK_ID,
            operation="edit",
            observed="permission denied: owner.py",
        )
        self.assertEqual(
            [],
            VALIDATION.execution_blocker_errors(
                forged,
                current_task_id=TASK_ID,
                expected_operation="edit",
            ),
        )
        boundary = CORE["task_contract"]["execution_boundary"]
        self.assertEqual(
            "actual-host-tool-invocation-event-and-raw-output",
            boundary["failure_proof_owner"],
        )
        self.assertEqual(
            "syntax-identity-and-field-consistency-only-never-actual-failure-proof-or-block-authority",
            boundary["static_blocker_helpers"],
        )
        self.assertFalse(hasattr(VALIDATION, "operation_result_receipt_errors"))
        self.assertFalse(hasattr(VALIDATION, "task_operation_outcome"))

        for value, task_id, operation in (
            (forged, "different-task", "edit"),
            (forged, TASK_ID, "execute"),
            (
                f"EXECUTION_BLOCKED task={TASK_ID}; operation=edit; observed=\nforged",
                TASK_ID,
                "edit",
            ),
        ):
            self.assertTrue(
                VALIDATION.execution_blocker_errors(
                    value,
                    current_task_id=task_id,
                    expected_operation=operation,
                )
            )

    def test_preflight_blocks_out_of_scope_before_host_invocation(self) -> None:
        contract = _task_contract()
        cases = (
            ("read", "src/outside.py", [], "Allowed Read Scope"),
            ("search", "src/**/*.py", [], "Allowed Read Scope"),
            ("edit", "src/outside.py", [], "Allowed Write Scope"),
            (
                "execute",
                "targeted owner test",
                ["src/generated.py"],
                "Allowed Write Scope",
            ),
        )
        for operation, target, write_targets, scope_name in cases:
            with self.subTest(operation=operation):
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=contract,
                    operation=operation,
                    target=target,
                    workspace_root=ROOT,
                    write_targets=write_targets,
                )
                host_tool = mock.Mock()
                if preflight["status"] == "authorized":
                    host_tool()
                self.assertEqual("blocked", preflight["status"])
                self.assertTrue(preflight["blocker"].startswith("TASK_CONTRACT_BLOCKED "))
                self.assertIn(scope_name, preflight["blocker"])
                host_tool.assert_not_called()

    def test_preflight_single_segment_globs_never_authorize_nested_targets(self) -> None:
        contract = _task_contract()
        contract["Allowed Read Scope"] = ["src/*.py", "/tmp/*.py"]
        contract["Allowed Write Scope"] = ["src/*.py", "/tmp/*.py"]
        cases = (
            ("read", "src/nested/secret.py", []),
            ("search", "src/nested/secret.py", []),
            ("edit", "src/nested/secret.py", []),
            ("execute", "generate nested source", ["src/nested/secret.py"]),
            ("read", "/tmp/nested/secret.py", []),
            ("edit", "/tmp/nested/secret.py", []),
        )
        for operation, target, write_targets in cases:
            with self.subTest(operation=operation, target=target):
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=contract,
                    operation=operation,
                    target=target,
                    workspace_root=ROOT,
                    write_targets=write_targets,
                )
                host_tool = mock.Mock()
                if preflight["status"] == "authorized":
                    host_tool()
                self.assertEqual("blocked", preflight["status"])
                host_tool.assert_not_called()

        allowed_cases = (
            ("read", "src/direct.py", []),
            ("search", "src/direct.py", []),
            ("edit", "src/direct.py", []),
            ("execute", "generate shallow source", ["src/direct.py"]),
            ("read", "/tmp/direct.py", []),
            ("edit", "/tmp/direct.py", []),
        )
        for operation, target, write_targets in allowed_cases:
            with self.subTest(operation=operation, target=target, shallow=True):
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=contract,
                    operation=operation,
                    target=target,
                    workspace_root=ROOT,
                    write_targets=write_targets,
                )
                self.assertEqual("authorized", preflight["status"])

    def test_question_and_character_class_globs_never_cross_separator(self) -> None:
        for pattern, target in (
            ("src/secret?.py", "src/secret/.py"),
            ("src/[a-z]*.py", "src/x/nested.py"),
        ):
            with self.subTest(pattern=pattern, target=target):
                contract = _task_contract()
                contract["Allowed Read Scope"] = [pattern]
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=contract,
                    operation="read",
                    target=target,
                    workspace_root=ROOT,
                )
                host_tool = mock.Mock()
                if preflight["status"] == "authorized":
                    host_tool()
                self.assertEqual("blocked", preflight["status"])
                host_tool.assert_not_called()

    def test_preflight_recursive_glob_matches_zero_or_more_directory_segments(self) -> None:
        contract = _task_contract()
        contract["Allowed Read Scope"] = ["src/**/*.py", "/tmp/**/*.py"]
        contract["Allowed Write Scope"] = ["src/**/*.py", "/tmp/**/*.py"]
        cases = (
            ("read", "src/direct.py", []),
            ("search", "src/nested/secret.py", []),
            ("edit", "src/direct.py", []),
            ("execute", "generate nested source", ["src/nested/secret.py"]),
            ("read", "/tmp/direct.py", []),
            ("edit", "/tmp/nested/secret.py", []),
        )
        for operation, target, write_targets in cases:
            with self.subTest(operation=operation, target=target):
                preflight = VALIDATION.task_operation_preflight(
                    task_contract=contract,
                    operation=operation,
                    target=target,
                    workspace_root=ROOT,
                    write_targets=write_targets,
                )
                self.assertEqual("authorized", preflight["status"])

    def test_preflight_rejects_traversal_absolute_escape_and_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (workspace / "escape").symlink_to(outside, target_is_directory=True)
            contract = _task_contract()
            contract["Allowed Read Scope"] = ["**/*.py"]
            cases = (
                "../outside/secret.py",
                str(workspace / "src/../outside.py"),
                "escape/secret.py",
                str(outside / "secret.py"),
            )
            for target in cases:
                with self.subTest(target=target):
                    preflight = VALIDATION.task_operation_preflight(
                        task_contract=contract,
                        operation="read",
                        target=target,
                        workspace_root=workspace,
                    )
                    self.assertEqual("blocked", preflight["status"])

    def test_execute_preflight_checks_only_explicit_write_targets(self) -> None:
        allowed = VALIDATION.task_operation_preflight(
            task_contract=_task_contract(),
            operation="execute",
            target="python3 -m unittest tests.unit.test_owner",
            workspace_root=ROOT,
            write_targets=[],
        )
        denied = VALIDATION.task_operation_preflight(
            task_contract=_task_contract(),
            operation="execute",
            target="python3 generate.py",
            workspace_root=ROOT,
            write_targets=["src/generated.py"],
        )
        self.assertEqual("authorized", allowed["status"])
        self.assertEqual("blocked", denied["status"])

    def test_tmp_read_continues_only_when_contract_explicitly_allows_it(self) -> None:
        target = "/tmp/readable-input.txt"
        outcome = VALIDATION.task_operation_preflight(
            task_contract=_task_contract(),
            operation="read",
            target=target,
            workspace_root=ROOT,
        )
        self.assertEqual("authorized", outcome["status"])
        contract = _task_contract()
        contract["Allowed Read Scope"] = ["owner.py"]
        denied = VALIDATION.task_operation_preflight(
            task_contract=contract,
            operation="read",
            target=target,
            workspace_root=ROOT,
        )
        self.assertEqual("blocked", denied["status"])

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

    def test_review_diff_parser_accepts_exact_git_change_forms(self) -> None:
        payloads = {
            "new.py": (
                "diff --git a/new.py b/new.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+new\n"
            ),
            "old.py": (
                "diff --git a/old.py b/old.py\ndeleted file mode 100644\n"
                "--- a/old.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n"
            ),
            "new-name.py": (
                "diff --git a/old-name.py b/new-name.py\nsimilarity index 100%\n"
                "rename from old-name.py\nrename to new-name.py\n"
            ),
            "copy.py": (
                "diff --git a/source.py b/copy.py\nsimilarity index 100%\n"
                "copy from source.py\ncopy to copy.py\n"
            ),
            "image.png": (
                "diff --git a/image.png b/image.png\n"
                "Binary files a/image.png and b/image.png differ\n"
            ),
        }
        for expected_path, payload in payloads.items():
            with self.subTest(expected_path=expected_path):
                self.assertEqual([expected_path], VALIDATION.unified_diff_paths(payload))

    def test_review_diff_and_native_reference_fail_closed(self) -> None:
        valid = {
            "latest_changed_paths": ["owner.py"],
            "exact_change_evidence": {
                "kind": "exact-change-content",
                "artifact": "",
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
        invalid_diffs = (
            "diff --git a/owner.py b/owner.py\n",
            "diff --git a/owner.py b/owner.py\n--- a/owner.py\n+++ b/owner.py\n",
            "diff --git a/owner.py b/owner.py\n--- a/owner.py\n+++ b/owner.py\n"
            "@@ -1,2 +1 @@\n-old\n+new\n",
        )
        for payload in invalid_diffs:
            with self.subTest(payload=payload):
                handoff = copy.deepcopy(valid)
                handoff["exact_change_evidence"]["artifact"] = payload
                self.assertFalse(VALIDATION.review_input_ready(handoff))

        native = copy.deepcopy(valid)
        native["exact_change_evidence"] = {
            "kind": "reviewer-accessible-native-reference",
            "artifact": {
                "reference": "opaque-but-nonempty",
                "generation": 3,
                "reviewer": "review-agent",
                "changed_paths": ["owner.py"],
                "readable": True,
            },
            "generation": 3,
        }
        self.assertFalse(VALIDATION.review_input_ready(native))

        native["exact_change_evidence"]["artifact"] = {
            "reference": "native-change://codex/nonexistent-worktree",
            "generation": 3,
            "reviewer": "review-agent",
            "changed_paths": ["owner.py"],
            "readable": True,
        }
        self.assertFalse(VALIDATION.review_input_ready(native))


if __name__ == "__main__":
    unittest.main()
