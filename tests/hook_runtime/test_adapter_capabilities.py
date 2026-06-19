from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_adapter_capabilities import (  # noqa: E402
    CANONICAL_EVENTS,
    adapter_capabilities_for,
    runtime_adapter_for,
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
                self.assertIn("supports_tool_batch", data)
                self.assertIn("command_output_visibility", data)
                self.assertIn("validation_output_visibility", data)
                self.assertIn(data["command_output_visibility"], {"none", "partial", "full"})
                for event in CANONICAL_EVENTS[:-1]:
                    self.assertTrue(
                        event in capabilities.supported_events
                        or event in capabilities.unsupported_events
                    )

    def test_copilot_unsupported_advisory_events_are_centralized(self) -> None:
        capabilities = adapter_capabilities_for("copilot")
        for event in ("UserPromptSubmit", "PreToolUse", "SubagentStop"):
            self.assertIn(event, capabilities.unsupported_events)
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
        self.assertEqual(runtime_adapter_for("codex").__class__.__name__, "CodexAdapter")
        self.assertEqual(runtime_adapter_for("claude").__class__.__name__, "ClaudeAdapter")
        self.assertEqual(runtime_adapter_for("copilot").__class__.__name__, "CopilotAdapter")
        self.assertEqual(runtime_adapter_for("cline").__class__.__name__, "ClineAdapter")
        self.assertEqual(runtime_adapter_for("roo").__class__.__name__, "RooAdapter")
        self.assertEqual(runtime_adapter_for("openhands").__class__.__name__, "OpenHandsAdapter")

    def test_staged_runtimes_degrade_unsupported_lifecycle(self) -> None:
        for runtime in ("cline", "roo"):
            with self.subTest(runtime=runtime):
                capabilities = adapter_capabilities_for(runtime)
                self.assertFalse(capabilities.placeholder)
                self.assertEqual(capabilities.supported_events, ())
                self.assertIn("PreToolUse", capabilities.unsupported_events)
                self.assertFalse(adapter_for(runtime).supports_stop_block())
        openhands = adapter_capabilities_for("openhands")
        self.assertFalse(openhands.placeholder)
        self.assertTrue(openhands.supports_event("FileChanged"))
        self.assertFalse(openhands.supports_event("PreToolUse"))


if __name__ == "__main__":
    unittest.main()
