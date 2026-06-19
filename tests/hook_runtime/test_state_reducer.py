from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_reducer():
    spec = importlib.util.spec_from_file_location(
        "changeforge_state_reducer_for_test",
        SCRIPT_DIR / "changeforge_state_reducer.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StateReducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reducer = load_reducer()

    def test_list_additive_dedupe(self) -> None:
        state = {"changed_paths": ["a.py"]}
        result = self.reducer.reduce_state_update(state, {"changed_paths": ["a.py", "b.py"]})
        self.assertEqual(result["changed_paths"], ["a.py", "b.py"])

    def test_bool_or_false_does_not_overwrite_true(self) -> None:
        state = {"read_evidence_seen": True}
        result = self.reducer.reduce_state_update(state, {"read_evidence_seen": False})
        self.assertTrue(result["read_evidence_seen"])

    def test_scalar_last_non_empty(self) -> None:
        state = {"turn_stage": "read"}
        result = self.reducer.reduce_state_update(state, {"turn_stage": ""})
        self.assertEqual(result["turn_stage"], "read")
        result = self.reducer.reduce_state_update(result, {"turn_stage": "edit"})
        self.assertEqual(result["turn_stage"], "edit")

    def test_active_skill_context_mapping_replace(self) -> None:
        state = {"active_skill_context": {"stage": "read"}}
        result = self.reducer.reduce_state_update(
            state, {"active_skill_context": {"stage": "edit", "refs": ["a", "b"]}}
        )
        self.assertEqual(result["active_skill_context"]["stage"], "edit")
        self.assertEqual(result["active_skill_context"]["refs"], ["a", "b"])

    def test_runtime_adapter_mapping_replace_preserves_empty_update(self) -> None:
        state = {"runtime_adapter": {"adapter": "codex"}}
        result = self.reducer.reduce_state_update(
            state,
            {
                "runtime_adapter": {
                    "adapter": "claude",
                    "supported_checks": ["stop_closure"],
                }
            },
        )
        self.assertEqual(result["runtime_adapter"]["adapter"], "claude")
        self.assertEqual(result["runtime_adapter"]["supported_checks"], ["stop_closure"])
        result = self.reducer.reduce_state_update(result, {"runtime_adapter": {}})
        self.assertEqual(result["runtime_adapter"]["adapter"], "claude")

    def test_compaction_preserves_old_active_context_on_empty_update(self) -> None:
        state = {"active_skill_context": {"stage": "review"}}
        result = self.reducer.reduce_state_update(state, {"active_skill_context": {}})
        self.assertEqual(result["active_skill_context"], {"stage": "review"})

    def test_unknown_field_ignored(self) -> None:
        result = self.reducer.reduce_state_update({}, {"raw_prompt": "secret"})
        self.assertNotIn("raw_prompt", result)

    def test_bounded_list_length(self) -> None:
        values = [f"path-{index}" for index in range(80)]
        result = self.reducer.reduce_state_update({}, {"changed_paths": values})
        self.assertEqual(len(result["changed_paths"]), 50)

    def test_new_evidence_fields_are_bounded_lists(self) -> None:
        result = self.reducer.reduce_state_update(
            {},
            {
                "normalized_events": ["event=PostToolUse"],
                "deleted_paths": ["old.py"],
                "generated_paths": ["dist/out.py"],
                "external_file_changes": ["outside.py"],
                "config_changes": ["settings.json"],
                "validation_results": ["pass:current:pytest"],
                "repair_events": ["repair:fix-1"],
                "rereview_events": ["rereview:fix-1"],
                "command_risks": ["safe:pytest"],
                "rollback_points": ["checkpoint:abc"],
                "post_edit_structure_findings": ["file_naming:count=0"],
            },
        )
        self.assertEqual(result["deleted_paths"], ["old.py"])
        self.assertEqual(result["validation_results"], ["pass:current:pytest"])
        self.assertEqual(result["post_edit_structure_findings"], ["file_naming:count=0"])


if __name__ == "__main__":
    unittest.main()
