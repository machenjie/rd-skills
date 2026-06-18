from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.gates.repeat_failure_gate import evaluate_repeat_failure_gate


class RepeatFailureGateTests(unittest.TestCase):
    def test_third_same_path_attempt_triggers_after_two_failures(self) -> None:
        events = [
            _event("e1", "failed", "2026-06-01T00:00:00Z"),
            _event("e2", "blocked", "2026-06-02T00:00:00Z"),
        ]
        decision = evaluate_repeat_failure_gate(
            events,
            repo_hash="repo",
            task_fingerprint="task",
            primary_path="src/app.py",
            owner_skill="backend-change-builder",
            mode="block",
        )["repeat_failure_gate"]
        self.assertTrue(decision["repeated"])
        self.assertEqual(decision["failure_count"], 2)
        self.assertFalse(decision["allowed_to_continue"])
        self.assertEqual(decision["required_next_gate"], "failure-diagnosis")

    def test_block_mode_allows_new_evidence(self) -> None:
        decision = evaluate_repeat_failure_gate(
            [_event("e1", "failed", "2026-06-01T00:00:00Z"), _event("e2", "failed", "2026-06-02T00:00:00Z")],
            repo_hash="repo",
            task_fingerprint="task",
            primary_path="src/app.py",
            owner_skill="backend-change-builder",
            mode="block",
            has_new_evidence=True,
        )["repeat_failure_gate"]
        self.assertTrue(decision["allowed_to_continue"])

    def test_path_owner_fallback_catches_stage_specific_fingerprints(self) -> None:
        events = [
            _event("e1", "failed", "2026-06-01T00:00:00Z", task_fingerprint="edit-task"),
            _event("e2", "failed", "2026-06-02T00:00:00Z", task_fingerprint="repair-task"),
        ]
        decision = evaluate_repeat_failure_gate(
            events,
            repo_hash="repo",
            task_fingerprint="new-turn-task",
            primary_path="src/app.py",
            owner_skill="backend-change-builder",
            mode="block",
        )["repeat_failure_gate"]
        self.assertTrue(decision["repeated"])
        self.assertEqual(decision["failure_count"], 2)
        self.assertFalse(decision["allowed_to_continue"])

    def test_new_kind_and_bounded_paths_are_repeat_failure_evidence(self) -> None:
        events = [
            _event("e1", "failed", "2026-06-01T00:00:00Z", use_new_fields=True),
            _event("e2", "blocked", "2026-06-02T00:00:00Z", use_new_fields=True),
        ]
        decision = evaluate_repeat_failure_gate(
            events,
            repo_hash="repo",
            task_fingerprint="task",
            primary_path="src/app.py",
            owner_skill="backend-change-builder",
            mode="warn",
        )["repeat_failure_gate"]
        self.assertTrue(decision["repeated"])
        self.assertEqual(decision["matched_paths"], ["src/app.py"])


def _event(
    event_id: str,
    outcome: str,
    created_at: str,
    *,
    task_fingerprint: str = "task",
    use_new_fields: bool = False,
) -> dict:
    event = {
        "event_id": event_id,
        "repo_hash": "repo",
        "task_fingerprint": task_fingerprint,
        "type": "implementation_attempt",
        "paths": ["src/app.py"],
        "owner_skill": "backend-change-builder",
        "outcome": outcome,
        "created_at": created_at,
    }
    if use_new_fields:
        event["kind"] = "repeat_failure"
        event["bounded_paths"] = ["src/app.py"]
        event["timestamp"] = created_at
    return event


if __name__ == "__main__":
    unittest.main()
