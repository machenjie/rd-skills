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
from runtime_governance.adapters.base import CANONICAL_EVENTS  # noqa: E402


NEW_BOOLEAN_FIELDS = (
    "supports_context_injection",
    "supports_pre_tool_block",
    "supports_permission_decision",
    "supports_post_tool_success",
    "supports_post_tool_failure",
    "supports_tool_batch",
    "supports_file_changed_event",
    "supports_config_changed_event",
    "supports_worktree_lifecycle",
    "supports_pre_compact",
    "supports_post_compact",
    "supports_session_end",
    "supports_task_lifecycle",
    "supports_checkpoint_or_rollback",
    "supports_plan_act_mode",
    "supports_codebase_index",
    "supports_mode_or_role_switch",
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
                data = capabilities.to_dict()
                for field in NEW_BOOLEAN_FIELDS:
                    self.assertIn(field, data)
                    self.assertIsInstance(data[field], bool)
                for field in (
                    "command_output_visibility",
                    "changed_path_visibility",
                    "validation_output_visibility",
                ):
                    self.assertIn(data[field], {"none", "partial", "full"})
                for event in CANONICAL_EVENTS[:-1]:
                    self.assertTrue(
                        event in capabilities.supported_events
                        or event in capabilities.unsupported_events
                    )

    def test_copilot_advisory_gaps_are_declared(self) -> None:
        capabilities = adapter_capabilities_for("copilot")
        self.assertIn("PreToolUse", capabilities.unsupported_events)
        self.assertIn("pre_tool_advisory_context", capabilities.unsupported_checks)
        self.assertFalse(capabilities.supports_context_event("PreToolUse"))
        self.assertEqual(capabilities.default_gate_mode("stop"), "block")

    def test_staged_runtime_targets_are_explicit_without_hook_overclaim(self) -> None:
        cline = adapter_capabilities_for("cline")
        self.assertFalse(cline.placeholder)
        self.assertEqual(cline.supported_events, ())
        self.assertTrue(cline.supports_plan_act_mode)
        self.assertTrue(cline.supports_mode_or_role_switch)
        self.assertFalse(cline.stop_block_supported)
        self.assertIn("PreToolUse", cline.unsupported_events)
        self.assertIn("pre_tool_advisory_context", cline.unsupported_checks)

        roo = adapter_capabilities_for("roo")
        self.assertFalse(roo.placeholder)
        self.assertEqual(roo.supported_events, ())
        self.assertTrue(roo.supports_mode_or_role_switch)
        self.assertIn("tool_permission_boundary", roo.supported_checks)
        self.assertIn("codebase_index", roo.unsupported_checks)

        openhands = adapter_capabilities_for("openhands")
        self.assertFalse(openhands.placeholder)
        self.assertIn("PostToolUse", openhands.supported_events)
        self.assertIn("FileChanged", openhands.supported_events)
        self.assertIn("PreToolUse", openhands.unsupported_events)
        self.assertEqual(openhands.command_output_visibility, "partial")
        self.assertTrue(openhands.supports_checkpoint_or_rollback)

    def test_future_runtime_placeholders_do_not_claim_support(self) -> None:
        for runtime in ("gemini-cli", "goose"):
            with self.subTest(runtime=runtime):
                capabilities = adapter_capabilities_for(runtime)
                self.assertTrue(capabilities.placeholder)
                self.assertEqual(capabilities.supported_events, ())
                for event in CANONICAL_EVENTS[:-1]:
                    self.assertIn(event, capabilities.unsupported_events)

    def test_runtime_visibility_and_template_backed_support_are_conservative(self) -> None:
        codex = adapter_capabilities_for("codex")
        claude = adapter_capabilities_for("claude")
        copilot = adapter_capabilities_for("copilot")
        generic = adapter_capabilities_for("generic")
        self.assertFalse(codex.supports_tool_batch)
        self.assertIn("PostToolBatch", codex.unsupported_events)
        self.assertTrue(claude.supports_tool_batch)
        self.assertEqual(copilot.command_output_visibility, "partial")
        self.assertEqual(generic.command_output_visibility, "none")

    def test_unknown_runtime_strictly_degrades(self) -> None:
        capabilities = strict_adapter_capabilities_for("new-runtime")
        self.assertEqual(capabilities.adapter_name, "new-runtime")
        self.assertTrue(capabilities.placeholder)
        self.assertFalse(capabilities.supports_event("Stop"))


if __name__ == "__main__":
    unittest.main()
