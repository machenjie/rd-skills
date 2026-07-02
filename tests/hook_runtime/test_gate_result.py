from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_gate_result import GateResult  # noqa: E402
from changeforge_hook_policy import gate_result, should_block, should_emit_context  # noqa: E402


class GateResultTests(unittest.TestCase):
    def test_gate_result_respects_warn_and_block_modes(self) -> None:
        warn = GateResult.from_policy("pre_edit_structure", mode="warn", confidence="high")
        block = GateResult.from_policy("pre_edit_structure", mode="block", confidence="high")
        monitor = GateResult.from_policy("pre_edit_structure", mode="monitor", confidence="high")
        self.assertTrue(warn.should_emit)
        self.assertFalse(warn.should_block)
        self.assertTrue(block.should_block)
        self.assertFalse(monitor.should_emit)

    def test_hook_policy_legacy_helpers_use_gate_result(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(should_emit_context("stop_closure"))
            self.assertTrue(should_block("stop_closure", confidence="high"))
            result = gate_result("stop_closure", confidence="high", message="missing route")
        self.assertEqual(result.gate_name, "stop_closure")
        self.assertEqual(result.message, "missing route")
        self.assertTrue(result.should_block)

    def test_hook_policy_stop_mode_block_uses_gate_result(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_STOP_MODE": "block"}, clear=True):
            self.assertTrue(should_emit_context("stop_closure"))
            self.assertTrue(should_block("stop_closure", confidence="high"))
            self.assertFalse(should_block("stop_closure", confidence="medium"))
            result = gate_result("stop_closure", confidence="high", message="missing route")
        self.assertEqual(result.gate_name, "stop_closure")
        self.assertEqual(result.message, "missing route")
        self.assertTrue(result.should_block)

    def test_hook_policy_global_warn_downgrades_stop_closure(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "warn"}, clear=True):
            self.assertTrue(should_emit_context("stop_closure"))
            self.assertFalse(should_block("stop_closure", confidence="high"))


if __name__ == "__main__":
    unittest.main()
