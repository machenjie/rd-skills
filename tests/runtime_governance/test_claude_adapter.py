from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.adapters import ClaudeAdapter  # noqa: E402
from runtime_governance.gates import GateOutcome  # noqa: E402


class ClaudeAdapterTests(unittest.TestCase):
    def test_normalizes_post_tool_batch_as_supported_canonical_event(self) -> None:
        result = ClaudeAdapter().normalize_event(
            {
                "hookEventName": "PostToolBatch",
                "toolName": "Bash",
                "toolInput": {"command": "python3 -m unittest discover -s tests"},
            }
        )
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(result.normalized_event.event_kind, "post_tool_batch")
        self.assertEqual(result.normalized_event.command_kind, "python3")

    def test_unknown_event_degrades(self) -> None:
        result = ClaudeAdapter().normalize_event({"hookEventName": "NotARealEvent"})
        self.assertEqual(result.gate_result.outcome, GateOutcome.DEGRADED.value)
        self.assertIn("claude_unknown_event", result.normalized_event.capability_degradation)


if __name__ == "__main__":
    unittest.main()
