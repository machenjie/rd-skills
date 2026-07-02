from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_reducer():
    spec = importlib.util.spec_from_file_location(
        "changeforge_state_reducer_degraded_test",
        SCRIPT_DIR / "changeforge_state_reducer.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StateReducerDegradedFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reducer = load_reducer()

    def test_degraded_adapter_facts_are_not_cleared_by_later_pass(self) -> None:
        state = self.reducer.reduce_state_update(
            {},
            {
                "runtime_adapter": {
                    "adapter": "copilot",
                    "active_degradation": ["copilot_pre_tool_advisory_context_unsupported"],
                    "degraded_capabilities": ["copilot_pre_tool_advisory_context_unsupported"],
                    "unsupported_checks": ["pre_tool_advisory_context"],
                    "visibility": {"validation_outcome": "partial"},
                }
            },
        )
        state = self.reducer.reduce_state_update(
            state,
            {
                "runtime_adapter": {
                    "adapter": "copilot",
                    "supported_checks": ["validation_broker"],
                    "active_degradation": [],
                    "degraded_capabilities": [],
                }
            },
        )

        adapter = state["runtime_adapter"]
        self.assertIn("copilot_pre_tool_advisory_context_unsupported", adapter["active_degradation"])
        self.assertIn("copilot_pre_tool_advisory_context_unsupported", adapter["degraded_capabilities"])
        self.assertIn("pre_tool_advisory_context", adapter["unsupported_checks"])
        self.assertEqual(adapter["supported_checks"], ["validation_broker"])

    def test_active_skill_context_empty_update_does_not_overwrite(self) -> None:
        state = {"active_skill_context": {"current_stage": "coding", "owner_skill": "backend-change-builder"}}
        result = self.reducer.reduce_state_update(state, {"active_skill_context": {}})

        self.assertEqual(result["active_skill_context"], state["active_skill_context"])

    def test_material_edit_after_validation_preserves_stale_fact(self) -> None:
        state = self.reducer.reduce_state_update({}, {"validation_results": ["pass:current:pytest"]})
        state = self.reducer.reduce_state_update(
            state,
            {"validation_results": ["stale_after_material_change:validation_before_latest_edit"]},
        )
        state = self.reducer.reduce_state_update(state, {"validation_results": ["pass:current:pytest"]})

        self.assertEqual(
            state["validation_results"][0],
            "stale_after_material_change:validation_before_latest_edit",
        )

    def test_normalized_event_summaries_are_additive_and_capped(self) -> None:
        state = self.reducer.reduce_state_update({}, {"normalized_events": ["event=PostToolUse;paths=1"]})
        state = self.reducer.reduce_state_update(state, {"normalized_events": ["event=Stop", "event=PostToolUse;paths=1"]})

        self.assertEqual(state["normalized_events"], ["event=PostToolUse;paths=1", "event=Stop"])


if __name__ == "__main__":
    unittest.main()
