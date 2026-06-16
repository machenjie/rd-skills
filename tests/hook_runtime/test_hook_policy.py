from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_policy():
    spec = importlib.util.spec_from_file_location(
        "changeforge_hook_policy_for_test",
        SCRIPT_DIR / "changeforge_hook_policy.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HookPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy()

    def test_default_warn(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "warn")
            self.assertTrue(self.policy.should_emit_context("pre_edit_structure"))

    def test_global_block_mode(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode("stop_closure"), "block")
            self.assertTrue(self.policy.should_block("stop_closure", confidence="high"))
            self.assertFalse(self.policy.should_block("stop_closure", confidence="medium"))

    def test_pre_edit_mode_overrides_default(self) -> None:
        with patch.dict(
            os.environ,
            {"CHANGEFORGE_HOOK_MODE": "warn", "CHANGEFORGE_PRE_EDIT_MODE": "block"},
            clear=True,
        ):
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "block")
            self.assertEqual(self.policy.gate_mode("permission_policy"), "warn")

    def test_failure_mode_default_fail_open(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.policy.failure_mode("pre_edit_structure"), "fail_open")
            self.assertEqual(
                self.policy.policy_for("pre_edit_structure")["failure_mode"], "fail_open"
            )

    def test_gate_specific_failure_mode(self) -> None:
        with patch.dict(
            os.environ,
            {"CHANGEFORGE_PRE_EDIT_STRUCTURE_FAILURE_MODE": "fail_closed"},
            clear=True,
        ):
            self.assertEqual(self.policy.failure_mode("pre_edit_structure"), "fail_closed")

    def test_invalid_mode_falls_back_to_warn(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "explode"}, clear=True):
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "warn")


if __name__ == "__main__":
    unittest.main()
