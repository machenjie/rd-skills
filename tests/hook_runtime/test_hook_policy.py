from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_policy():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "changeforge_hook_policy_for_test",
            SCRIPT_DIR / "changeforge_hook_policy.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(SCRIPT_DIR))
        except ValueError:
            pass


def load_permission_gate():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "changeforge_permission_policy_gate_for_test",
            SCRIPT_DIR / "changeforge_permission_policy_gate.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(SCRIPT_DIR))
        except ValueError:
            pass


class HookPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy()

    def test_default_enforcement_modes(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.policy.gate_mode("sdd_material_choice"), "warn")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "warn")
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "warn")
            self.assertEqual(self.policy.gate_mode("process_phase"), "monitor")
            self.assertEqual(self.policy.gate_mode("stop_closure"), "warn")
            self.assertEqual(self.policy.gate_mode("permission_policy"), "warn")
            self.assertTrue(self.policy.should_emit_context("pre_edit_structure"))
            self.assertFalse(self.policy.should_block("process_phase", confidence="high"))
            self.assertFalse(self.policy.should_block("stop_closure", confidence="high"))

    def test_global_block_mode_does_not_upgrade_stop_closure(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode("sdd_material_choice"), "warn")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "warn")
            self.assertEqual(self.policy.gate_mode_for_stage("sdd_material_choice", "pretool"), "warn")
            self.assertEqual(self.policy.gate_mode("stop_closure"), "warn")
            self.assertEqual(self.policy.gate_mode_for_stage("sdd_material_choice", "stop"), "warn")
            self.assertFalse(self.policy.should_block("stop_closure", confidence="high"))
            self.assertFalse(self.policy.should_block("stop_closure", confidence="medium"))

    def test_global_warn_mode_downgrades_default_block_gates(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "warn"}, clear=True):
            self.assertEqual(self.policy.gate_mode("sdd_material_choice"), "warn")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "warn")
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "warn")
            self.assertEqual(self.policy.gate_mode("stop_closure"), "warn")
            self.assertEqual(self.policy.gate_mode("process_phase"), "warn")

    def test_gate_specific_mode_overrides_global_warn(self) -> None:
        with patch.dict(
            os.environ,
            {"CHANGEFORGE_HOOK_MODE": "warn", "CHANGEFORGE_SDD_CHOICE_MODE": "block"},
            clear=True,
        ):
            self.assertEqual(self.policy.gate_mode("sdd_material_choice"), "block")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "warn")
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "warn")
            self.assertEqual(self.policy.gate_mode("stop_closure"), "warn")
            self.assertEqual(self.policy.gate_mode("process_phase"), "warn")

    def test_gate_specific_mode_overrides_default(self) -> None:
        with patch.dict(
            os.environ,
            {"CHANGEFORGE_HOOK_MODE": "warn", "CHANGEFORGE_PRE_EDIT_MODE": "monitor"},
            clear=True,
        ):
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "monitor")
            self.assertEqual(self.policy.gate_mode("permission_policy"), "warn")

    def test_stop_specific_block_mode_blocks_high_confidence(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_STOP_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode("stop_closure"), "block")
            self.assertTrue(self.policy.should_block("stop_closure", confidence="high"))

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

    def test_run_gate_with_policy_defaults_to_fail_open(self) -> None:
        calls: list[str] = []

        def fail_closed(exc: Exception) -> None:
            calls.append(f"closed:{exc}")

        def fail_open(exc: Exception) -> None:
            calls.append(f"open:{exc}")

        with patch.dict(os.environ, {}, clear=True):
            result = self.policy.run_gate_with_policy(
                "permission_policy",
                lambda: (_ for _ in ()).throw(RuntimeError("boom")),
                fail_closed=fail_closed,
                fail_open=fail_open,
            )
        self.assertEqual(result, 0)
        self.assertEqual(calls, ["open:boom"])

    def test_run_gate_with_policy_uses_fail_closed(self) -> None:
        calls: list[str] = []

        def fail_closed(exc: Exception) -> None:
            calls.append(f"closed:{exc}")

        with patch.dict(
            os.environ,
            {"CHANGEFORGE_PERMISSION_POLICY_FAILURE_MODE": "fail_closed"},
            clear=True,
        ):
            result = self.policy.run_gate_with_policy(
                "permission_policy",
                lambda: (_ for _ in ()).throw(RuntimeError("boom")),
                fail_closed=fail_closed,
            )
        self.assertEqual(result, 0)
        self.assertEqual(calls, ["closed:boom"])

    def test_global_block_mode_can_force_professional_gates_in_strict_mode(self) -> None:
        env = {"CHANGEFORGE_HOOK_MODE": "block", "CHANGEFORGE_STRICT_BLOCKING": "1"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.policy.gate_mode("process_phase"), "block")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "block")
            self.assertEqual(self.policy.gate_mode_for_stage("process_phase", "pretool"), "block")
            self.assertTrue(self.policy.should_block("process_phase", confidence="high"))

    def test_global_block_mode_can_force_professional_gates_in_ci_mode(self) -> None:
        env = {"CHANGEFORGE_HOOK_MODE": "block", "CHANGEFORGE_CI_MODE": "ci"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.policy.gate_mode("process_phase"), "block")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "block")
            self.assertEqual(
                self.policy.gate_mode_for_stage("process_phase", "pretool"),
                "block",
            )

    def test_plain_ci_env_does_not_force_professional_gate_blocking(self) -> None:
        # Regression: ordinary CI runners set CI=true, but strict hook blocking
        # must require an explicit ChangeForge strictness variable.
        env = {"CHANGEFORGE_HOOK_MODE": "block", "CI": "true"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.policy.gate_mode("process_phase"), "monitor")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "warn")
            self.assertEqual(
                self.policy.gate_mode_for_stage("process_phase", "pretool"),
                "monitor",
            )

    def test_global_block_mode_can_force_professional_gates_in_benchmark(self) -> None:
        env = {
            "CHANGEFORGE_HOOK_MODE": "block",
            "CHANGEFORGE_BENCHMARK_MODE": "benchmark",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.policy.gate_mode("sdd_material_choice"), "block")
            self.assertEqual(self.policy.gate_mode("process_phase"), "block")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "block")

    def test_invalid_mode_falls_back_to_warn(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "explode"}, clear=True):
            self.assertEqual(self.policy.gate_mode("pre_edit_structure"), "warn")
            self.assertEqual(self.policy.gate_mode("risk_surface"), "warn")
            self.assertEqual(self.policy.gate_mode("process_phase"), "monitor")
            self.assertEqual(self.policy.gate_mode("stop_closure"), "warn")
            self.assertEqual(self.policy.gate_mode("permission_policy"), "warn")

    def test_stage_specific_modes_split_pretool_and_stop(self) -> None:
        env = {
            "CHANGEFORGE_PROCESS_PHASE_PRETOOL_MODE": "block",
            "CHANGEFORGE_PROCESS_PHASE_STOP_MODE": "warn",
            "CHANGEFORGE_SDD_CHOICE_PRETOOL_MODE": "block",
            "CHANGEFORGE_SDD_CHOICE_STOP_MODE": "warn",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("process_phase", "pretool"), "block")
            self.assertEqual(self.policy.gate_mode_for_stage("process_phase", "stop"), "warn")
            self.assertEqual(self.policy.gate_mode_for_stage("sdd_material_choice", "pretool"), "block")
            self.assertEqual(self.policy.gate_mode_for_stage("sdd_material_choice", "stop"), "warn")

    def test_stop_stage_ignores_global_hook_block(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("process_phase", "stop"), "warn")

    def test_stop_stage_ignores_generic_process_phase_block(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_PROCESS_PHASE_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("process_phase", "stop"), "warn")

    def test_stop_stage_uses_process_phase_stop_block(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_PROCESS_PHASE_STOP_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("process_phase", "stop"), "block")

    def test_stop_stage_ignores_generic_sdd_choice_block(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_SDD_CHOICE_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("sdd_material_choice", "stop"), "warn")

    def test_stop_stage_uses_sdd_choice_stop_block(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_SDD_CHOICE_STOP_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("sdd_material_choice", "stop"), "block")

    def test_stop_closure_uses_stop_mode_only(self) -> None:
        with patch.dict(os.environ, {"CHANGEFORGE_HOOK_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("stop_closure", "stop"), "warn")
        with patch.dict(os.environ, {"CHANGEFORGE_STOP_MODE": "block"}, clear=True):
            self.assertEqual(self.policy.gate_mode_for_stage("stop_closure", "stop"), "block")

    def test_permission_gate_fail_closed_blocks_on_unhandled_exception(self) -> None:
        gate = load_permission_gate()
        output = StringIO()
        with patch.dict(
            os.environ,
            {
                "CHANGEFORGE_AGENT": "codex",
                "CHANGEFORGE_PERMISSION_POLICY_FAILURE_MODE": "fail_closed",
            },
            clear=True,
        ), patch.object(gate, "_main", side_effect=RuntimeError("boom")), redirect_stdout(output):
            self.assertEqual(gate.main(), 0)
        payload = json.loads(output.getvalue())
        hook_output = payload["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn("failed closed", hook_output["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
