from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.adapters import (  # noqa: E402
    adapter_capabilities_for,
    coverage_matrix,
    strict_adapter_capabilities_for,
)


class AdapterCapabilitiesProtocolTests(unittest.TestCase):
    def test_supported_runtime_matrix_is_explicit(self) -> None:
        rows = {row["adapter"]: row for row in coverage_matrix()}
        for runtime in ("codex", "claude", "copilot"):
            with self.subTest(runtime=runtime):
                capabilities = adapter_capabilities_for(runtime)
                self.assertEqual(capabilities.adapter_name, runtime)
                self.assertIn("Stop", capabilities.supported_events)
                self.assertTrue(capabilities.path_observable)
                self.assertEqual(capabilities.default_failure_mode, "fail_open")
                self.assertIn(runtime, rows)

    def test_copilot_advisory_gaps_are_declared(self) -> None:
        capabilities = adapter_capabilities_for("copilot")
        self.assertIn("PreToolUse", capabilities.unsupported_events)
        self.assertIn("pre_tool_advisory_context", capabilities.unsupported_checks)
        self.assertFalse(capabilities.supports_context_event("PreToolUse"))
        self.assertEqual(capabilities.default_gate_mode("stop"), "block")

    def test_future_runtime_placeholders_do_not_claim_support(self) -> None:
        for runtime in ("cline", "openhands", "gemini-cli", "goose"):
            with self.subTest(runtime=runtime):
                capabilities = adapter_capabilities_for(runtime)
                self.assertTrue(capabilities.placeholder)
                self.assertEqual(capabilities.supported_events, ())
                self.assertIn("Stop", capabilities.unsupported_events)

    def test_unknown_runtime_strictly_degrades(self) -> None:
        capabilities = strict_adapter_capabilities_for("new-runtime")
        self.assertEqual(capabilities.adapter_name, "new-runtime")
        self.assertTrue(capabilities.placeholder)
        self.assertFalse(capabilities.supports_event("Stop"))


if __name__ == "__main__":
    unittest.main()
