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


def _event(event_id: str, outcome: str, created_at: str) -> dict:
    return {
        "event_id": event_id,
        "repo_hash": "repo",
        "task_fingerprint": "task",
        "type": "implementation_attempt",
        "paths": ["src/app.py"],
        "owner_skill": "backend-change-builder",
        "outcome": outcome,
        "created_at": created_at,
    }


if __name__ == "__main__":
    unittest.main()

