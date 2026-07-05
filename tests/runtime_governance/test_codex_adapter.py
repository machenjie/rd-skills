from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.adapters import CodexAdapter  # noqa: E402
from runtime_governance.gates import GateOutcome  # noqa: E402


class CodexAdapterTests(unittest.TestCase):
    def test_normalizes_pre_tool_without_full_command_args(self) -> None:
        result = CodexAdapter().normalize_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {
                    "command": "pytest tests --token SECRET123",
                    "file_path": "/repo/tests/test_adapter.py",
                },
                "prompt": "do not capture this prompt",
            },
            base_path="/repo",
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(event.command_kind, "pytest")
        self.assertEqual(event.bounded_paths, ["tests/test_adapter.py"])
        encoded = json.dumps(event.to_json_dict(), sort_keys=True)
        self.assertNotIn("SECRET123", encoded)
        self.assertNotIn("do not capture", encoded)

    def test_compact_session_keeps_compaction_signal(self) -> None:
        result = CodexAdapter().normalize_event(
            {"hook_event_name": "SessionStart", "source": "compact"}
        )
        self.assertEqual(result.normalized_event.event_kind, "session_start")
        self.assertEqual(result.normalized_event.stage_signal, "compaction")
        self.assertTrue(CodexAdapter().capabilities.supports_context_event("SessionStart"))

    def test_pre_and_post_compact_are_supported_events(self) -> None:
        for event_name in ("PreCompact", "PostCompact"):
            with self.subTest(event_name=event_name):
                result = CodexAdapter().normalize_event({"hook_event_name": event_name, "trigger": "manual"})
                self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
                self.assertTrue(CodexAdapter().capabilities.supports_event(event_name))
        self.assertFalse(CodexAdapter().capabilities.supports_event("Compact"))


if __name__ == "__main__":
    unittest.main()
