from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_adapter_capabilities import (  # noqa: E402
    adapter_capabilities_for,
    unsupported_events_for,
)
from changeforge_runtime_adapters import adapter_for  # noqa: E402


class AdapterCapabilitiesTests(unittest.TestCase):
    def test_codex_claude_copilot_generic_are_explicit(self) -> None:
        for runtime in ("codex", "claude", "copilot", "generic"):
            with self.subTest(runtime=runtime):
                capabilities = adapter_capabilities_for(runtime)
                data = capabilities.to_dict()
                self.assertEqual(data["runtime"], runtime)
                self.assertEqual(data["default_failure_mode"], "fail_open")
                self.assertIn("supports_stop", data)
                self.assertIn("supports_context_injection", data)

    def test_copilot_unsupported_advisory_events_are_centralized(self) -> None:
        capabilities = adapter_capabilities_for("copilot")
        self.assertEqual(
            tuple(capabilities.unsupported_events),
            ("UserPromptSubmit", "PreToolUse", "SubagentStop"),
        )
        self.assertEqual(unsupported_events_for("copilot"), capabilities.unsupported_events)
        for event in capabilities.unsupported_events:
            self.assertFalse(capabilities.supports_event(event))
            self.assertFalse(capabilities.supports_context_event(event))

    def test_runtime_adapter_uses_capabilities_without_changing_old_support(self) -> None:
        self.assertTrue(adapter_for("codex").supports_context_event("PreToolUse"))
        self.assertTrue(adapter_for("claude").supports_permission_event())
        self.assertFalse(adapter_for("copilot").supports_context_event("PreToolUse"))
        self.assertTrue(adapter_for("copilot").supports_stop_block())
        self.assertEqual(adapter_for("unknown").runtime, "generic")


if __name__ == "__main__":
    unittest.main()
