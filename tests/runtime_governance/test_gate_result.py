from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import GateOutcome, GateResult, NormalizedEvent  # noqa: E402


class GateResultTests(unittest.TestCase):
    def test_outcomes_are_distinct_and_round_trip(self) -> None:
        results = [
            GateResult.pass_result("g"),
            GateResult.warn("g", "warn"),
            GateResult.block("g", "block", explicit=True, high_confidence=True),
            GateResult.fail_open("g", "unsupported adapter"),
            GateResult.degraded("g", "unknown event"),
        ]
        self.assertEqual([result.outcome for result in results], [item.value for item in GateOutcome])
        self.assertEqual(GateResult.from_json(results[-1].to_json()), results[-1])

    def test_unsupported_runtime_event_degrades(self) -> None:
        event = NormalizedEvent.from_telemetry_fact({"event_name": "NotSupported"})
        result = GateResult.from_event_support(
            "event_gate",
            event,
            supported_events=["pre_tool_use", "post_tool_use"],
        )
        self.assertEqual(result.outcome, GateOutcome.DEGRADED.value)

    def test_fail_open_is_not_reported_as_pass(self) -> None:
        result = GateResult.fail_open("advisory", "adapter unavailable")
        self.assertEqual(result.outcome, GateOutcome.FAIL_OPEN.value)
        self.assertNotEqual(result.outcome, GateOutcome.PASS.value)

    def test_block_requires_explicit_high_confidence(self) -> None:
        result = GateResult.block("g", "missing", explicit=False, high_confidence=True)
        self.assertEqual(result.outcome, GateOutcome.WARN.value)


if __name__ == "__main__":
    unittest.main()
