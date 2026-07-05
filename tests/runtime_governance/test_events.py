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

    def test_permission_request_uses_its_own_canonical_kind(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {"event_name": "PermissionRequest", "runtime": "codex"}
        )
        self.assertEqual(event.event_kind, EventKind.PERMISSION_REQUEST.value)
        self.assertEqual(event.capability_degradation, [])

    def test_json_round_trip(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {"event_name": "Stop", "runtime": "codex", "hook_name": "stop_closure_gate"}
        )
        self.assertEqual(NormalizedEvent.from_json(event.to_json()), event)

    def test_new_canonical_events_round_trip(self) -> None:
        for event_name, expected in (
            ("UserPromptExpansion", EventKind.USER_PROMPT_EXPANSION.value),
            ("PostToolUseFailure", EventKind.POST_TOOL_USE_FAILURE.value),
            ("PostToolBatch", EventKind.POST_TOOL_BATCH.value),
            ("StopFailure", EventKind.STOP_FAILURE.value),
            ("SessionEnd", EventKind.SESSION_END.value),
            ("TaskCreated", EventKind.TASK_CREATED.value),
            ("TaskCompleted", EventKind.TASK_COMPLETED.value),
            ("FileChanged", EventKind.FILE_CHANGED.value),
            ("ConfigChanged", EventKind.CONFIG_CHANGED.value),
            ("WorktreeCreate", EventKind.WORKTREE_CREATE.value),
            ("WorktreeRemove", EventKind.WORKTREE_REMOVE.value),
            ("PreCompact", EventKind.PRE_COMPACT.value),
            ("PostCompact", EventKind.POST_COMPACT.value),
            ("Compact", EventKind.COMPACT.value),
        ):
            with self.subTest(event_name=event_name):
                event = NormalizedEvent.from_telemetry_fact({"event_name": event_name})
                self.assertEqual(event.event_kind, expected)
                self.assertEqual(NormalizedEvent.from_json(event.to_json()), event)

    def test_path_fields_are_normalized_and_capped(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {
                "event_name": "FileChanged",
                "read_paths": ["/repo/src/read.py"],
                "changed_paths": [f"/repo/src/changed_{index}.py" for index in range(60)],
                "deleted_paths": ["/repo/src/old.py"],
                "generated_paths": ["/repo/dist/new.py"],
            },
            base_path="/repo",
        )
        self.assertEqual(event.read_paths, ["src/read.py"])
        self.assertEqual(event.deleted_paths, ["src/old.py"])
        self.assertEqual(event.generated_paths, ["dist/new.py"])
        self.assertEqual(len(event.changed_paths), 50)
        self.assertTrue(all(path.startswith("src/changed_") for path in event.changed_paths))
        self.assertLessEqual(len(event.bounded_paths), 50)

    def test_prompt_like_and_output_fields_are_ignored_with_redaction_marker(self) -> None:
        event = NormalizedEvent.from_telemetry_fact(
            {
                "event_name": "PostToolUse",
                "runtime": "codex",
                "prompt": "summarize the secret plan",
                "user_prompt": "raw user prompt should not persist",
                "command_output": "full output should not persist",
                "full_command": "python3 script.py --token SECRET123",
                "command_program": "python3 -m unittest discover -s tests",
                "exit_code": 0,
            }
        )
        encoded = event.to_json()
        self.assertNotIn("secret plan", encoded)
        self.assertNotIn("raw user prompt", encoded)
        self.assertNotIn("full output", encoded)
        self.assertNotIn("SECRET123", encoded)
        self.assertIn("prompt:ignored", event.privacy_redaction)
        self.assertIn("command_output:ignored", event.privacy_redaction)
        self.assertTrue(event.validation_candidate)
        self.assertEqual(event.command_outcome, "pass")


if __name__ == "__main__":
    unittest.main()
