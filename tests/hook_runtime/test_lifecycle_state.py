from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_lifecycle_state import LifecycleState  # noqa: E402
from changeforge_state_reducer import reduce_state_update  # noqa: E402


class LifecycleStateTests(unittest.TestCase):
    def test_wraps_state_reducer_semantics_without_mutating_them(self) -> None:
        state = reduce_state_update(
            {"read_evidence_seen": True, "turn_stage": "read", "changed_paths": ["a.py"]},
            {
                "read_evidence_seen": False,
                "turn_stage": "edit",
                "changed_paths": ["a.py", "b.py"],
                "risk_surfaces": ["security"],
            },
        )
        lifecycle = LifecycleState.from_state(state)
        self.assertTrue(lifecycle.read_evidence_seen)
        self.assertEqual(lifecycle.turn_stage, "edit")
        self.assertEqual(lifecycle.changed_paths, ["a.py", "b.py"])
        self.assertEqual(lifecycle.risk_surfaces, ["security"])

    def test_to_dict_has_expected_lifecycle_fields(self) -> None:
        data = LifecycleState.from_state(
            {
                "owner_skill": "backend-change-builder",
                "reviewer_skill": "ai-code-review-refactor",
                "implementation_preflight_complete": True,
            }
        ).to_dict()
        self.assertEqual(data["owner_skill"], "backend-change-builder")
        self.assertEqual(data["reviewer_skill"], "ai-code-review-refactor")
        self.assertTrue(data["implementation_preflight_complete"])


if __name__ == "__main__":
    unittest.main()
