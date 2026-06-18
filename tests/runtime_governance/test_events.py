from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import EventKind, NormalizedEvent  # noqa: E402


class NormalizedEventTests(unittest.TestCase):
    def test_from_telemetry_fact_sanitizes_paths_and_command(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {
                "event_name": "PreToolUse",
                "runtime": "codex",
                "tool_name": "Bash",
                "changed_paths": ["/Users/example/repo/src/app.py", "tests/test_app.py"],
                "command_program": "python3 scripts/test.py --secret value",
                "timestamp_utc": "2026-06-18T00:00:00+00:00",
            },
            base_path="/Users/example/repo",
        )
        self.assertEqual(event.event_kind, EventKind.PRE_TOOL_USE.value)
        self.assertEqual(event.bounded_paths, ["src/app.py", "tests/test_app.py"])
        self.assertEqual(event.command_kind, "python3")
        self.assertEqual(event.adapter, "codex")

    def test_unknown_event_degrades_without_crashing(self) -> None:
        event = NormalizedEvent.from_telemetry_fact({"event_name": "RuntimeThing", "runtime": "copilot"})
        self.assertEqual(event.event_kind, EventKind.UNKNOWN.value)
        self.assertIn("unsupported_event:RuntimeThing", event.capability_degradation)

    def test_permission_request_maps_to_pre_tool_without_degradation(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {"event_name": "PermissionRequest", "runtime": "codex"}
        )
        self.assertEqual(event.event_kind, EventKind.PRE_TOOL_USE.value)
        self.assertEqual(event.capability_degradation, [])

    def test_json_round_trip(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {"event_name": "Stop", "runtime": "codex", "hook_name": "stop_closure_gate"}
        )
        self.assertEqual(NormalizedEvent.from_json(event.to_json()), event)


if __name__ == "__main__":
    unittest.main()
