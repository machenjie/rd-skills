from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_executor_adapter_core import (  # noqa: E402
    snapshot_from_event_state,
    state_update_from_snapshot,
)


class ExecutorAdapterCoreTests(unittest.TestCase):
    def test_snapshot_state_update_is_bounded_and_adapter_aware(self) -> None:
        snapshot = snapshot_from_event_state(
            {
                "runtime": "codex",
                "hook_event_name": "PostToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": "src/app.py"},
            },
            {},
            classification={"stage": "edit", "paths": ["src/app.py"], "tool": "Edit"},
            gate_name="post_edit_structure",
        )
        update = state_update_from_snapshot(snapshot)

        self.assertEqual(update["runtime_adapter"]["adapter"], "codex")
        self.assertEqual(update["changed_paths"], ["src/app.py"])
        self.assertIn("event=PostToolUse", update["normalized_events"][0])
        self.assertIn("supported_checks", update["runtime_adapter"])
        self.assertNotIn("tool_input", str(update))

    def test_snapshot_includes_gate_result(self) -> None:
        snapshot = snapshot_from_event_state(
            {"runtime": "copilot", "hook_event_name": "PreToolUse"},
            {},
            classification={"stage": "permission"},
            gate_name="permission_policy",
            gate_mode="warn",
        )
        data = snapshot.to_dict()
        self.assertIn("gate_result", data)
        self.assertEqual(data["gate_result"]["gate_name"], "permission_policy")
        self.assertEqual(data["adapter_capabilities"]["runtime"], "copilot")

    def test_snapshot_preserves_new_adapter_runtime_names(self) -> None:
        snapshot = snapshot_from_event_state(
            {
                "runtime": "openhands",
                "event_type": "file_write",
                "path": "src/app.py",
            },
            {},
            classification={"stage": "edit"},
            gate_name="executor_adapter",
        )
        update = state_update_from_snapshot(snapshot)

        self.assertEqual(snapshot.capabilities.runtime, "openhands")
        self.assertEqual(update["runtime_adapter"]["adapter"], "openhands")
        self.assertEqual(update["changed_paths"], ["src/app.py"])

        snapshot = snapshot_from_event_state(
            {
                "runtime": "roo",
                "event_name": "tool_use",
                "mode": "review",
                "tool_name": "write",
            },
            {},
            classification={"stage": "review"},
            gate_name="executor_adapter",
        )
        self.assertEqual(snapshot.capabilities.runtime, "roo")
        self.assertIn("roo:pre_tool_block:unsupported", state_update_from_snapshot(snapshot)["runtime_adapter"]["degraded_capabilities"])


if __name__ == "__main__":
    unittest.main()
