from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.adapters import CopilotAdapter  # noqa: E402
from runtime_governance.gates import GateOutcome  # noqa: E402


class CopilotAdapterTests(unittest.TestCase):
    def test_pre_tool_is_supported_without_fake_context(self) -> None:
        adapter = CopilotAdapter()
        result = adapter.normalize_event({"eventName": "PreToolUse", "toolName": "Bash"})
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(result.normalized_event.event_kind, "pre_tool_use")
        self.assertEqual(result.normalized_event.capability_degradation, [])
        self.assertIsNone(adapter.advisory_context_for("PreToolUse", "context"))

    def test_stop_block_requires_configuration_and_capability(self) -> None:
        adapter = CopilotAdapter()
        self.assertFalse(adapter.stop_block_allowed(configured_block=False))
        self.assertTrue(adapter.stop_block_allowed(configured_block=True))


if __name__ == "__main__":
    unittest.main()
