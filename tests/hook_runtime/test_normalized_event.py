from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_action_classifier import classify_event, normalize_event  # noqa: E402


class NormalizedEventTests(unittest.TestCase):
    def test_edit_event_preserves_classifier_dict_shape(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "patch": (
                    "*** Begin Patch\n"
                    "*** Update File: src/services/order_service.py\n"
                    "+def save_order(): pass\n"
                    "*** End Patch\n"
                )
            },
        }
        normalized = normalize_event(event)
        legacy = classify_event(event)
        self.assertEqual(normalized.event_name, "PreToolUse")
        self.assertEqual(normalized.event_kind, "pre_tool_use")
        self.assertEqual(normalized.stage, "edit")
        self.assertEqual(normalized.changed_paths, ["src/services/order_service.py"])
        self.assertIn("src/services/order_service.py", normalized.bounded_paths)
        self.assertEqual(legacy["stage"], "edit")
        self.assertEqual(legacy["paths"], ["src/services/order_service.py"])
        self.assertIn("backend-product", legacy["product_surfaces"])

    def test_read_event_records_read_paths_and_patterns(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Grep",
            "tool_input": {"pattern": "adapter_for", "path": "src/hook-runtime/scripts"},
        }
        normalized = normalize_event(event)
        self.assertEqual(normalized.stage, "read")
        self.assertIn("src/hook-runtime/scripts", normalized.read_paths)
        self.assertIn("adapter_for", normalized.searched_patterns)

    def test_test_review_and_repair_stages_are_stable(self) -> None:
        test_event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python3 -m unittest discover -s tests"},
        }
        review_event = {"hook_event_name": "UserPromptSubmit", "prompt": "review latest commit"}
        repair_event = {"hook_event_name": "UserPromptSubmit", "prompt": "fix the null path bug"}
        self.assertEqual(normalize_event(test_event).stage, "test")
        self.assertEqual(normalize_event(review_event).stage, "review")
        self.assertEqual(normalize_event(repair_event).stage, "repair")

    def test_hook_compatibility_exposes_new_canonical_fields(self) -> None:
        event = {
            "hookEventName": "PostToolBatch",
            "toolName": "Bash",
            "toolInput": {"command": "python3 -m unittest discover -s tests"},
        }
        normalized = normalize_event(event)
        data = normalized.to_dict()
        self.assertEqual(normalized.event_name, "PostToolBatch")
        self.assertEqual(normalized.event_kind, "post_tool_batch")
        self.assertEqual(data["lifecycle_cadence"], "tool")
        self.assertEqual(data["executor_event_phase"], "after")
        self.assertIn(data["command_outcome"], {"not_observable", "pass", "fail"})
        for field in (
            "deleted_paths",
            "generated_paths",
            "validation_candidate",
            "validation_outcome",
            "validation_freshness",
            "permission_decision",
            "checkpoint_id",
            "rollback_available",
            "privacy_redaction",
        ):
            self.assertIn(field, data)


if __name__ == "__main__":
    unittest.main()
