from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "runtime_payloads"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.adapters import (  # noqa: E402
    ClaudeAdapter,
    ClineAdapter,
    CodexAdapter,
    CopilotAdapter,
    OpenHandsAdapter,
    RooAdapter,
    runtime_adapter_for,
)
from executor_backends.openhands import BackendEvent, FakeOpenHandsBackend  # noqa: E402
from runtime_governance.gates import GateOutcome  # noqa: E402


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class RuntimeAdapterTranslatorTests(unittest.TestCase):
    def assert_no_leak(self, encoded: str, *blocked: str) -> None:
        for text in blocked:
            self.assertNotIn(text, encoded)

    def test_factory_returns_concrete_runtime_translators(self) -> None:
        self.assertIsInstance(runtime_adapter_for("codex"), CodexAdapter)
        self.assertIsInstance(runtime_adapter_for("claude"), ClaudeAdapter)
        self.assertIsInstance(runtime_adapter_for("copilot"), CopilotAdapter)
        self.assertIsInstance(runtime_adapter_for("cline"), ClineAdapter)
        self.assertIsInstance(runtime_adapter_for("roo"), RooAdapter)
        self.assertIsInstance(runtime_adapter_for("openhands"), OpenHandsAdapter)
        self.assertEqual(runtime_adapter_for("unknown-runtime").capabilities.runtime, "generic")

    def test_codex_pre_tool_edit_extracts_changed_paths_without_prompt_leak(self) -> None:
        result = runtime_adapter_for("codex").normalize_event(
            load_fixture("codex_pre_tool_edit_without_preflight.json"),
            base_path="/repo",
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(event.event_kind, "pre_tool_use")
        self.assertEqual(event.tool_category, "edit")
        self.assertEqual(event.command_risk, "mutation")
        self.assertEqual(event.changed_paths, ["src/runtime_governance/adapters/base.py"])
        self.assertIn("src/runtime_governance/adapters/base.py", event.bounded_paths)
        encoded = event.to_json()
        self.assert_no_leak(encoded, "raw user request should not persist")

    def test_codex_post_tool_pytest_pass_is_safe_validation_command(self) -> None:
        result = runtime_adapter_for("codex").normalize_event(
            load_fixture("codex_post_tool_bash_pytest_pass.json"),
            base_path="/repo",
        )
        event = result.normalized_event
        self.assertEqual(event.event_kind, "post_tool_use")
        self.assertEqual(event.tool_category, "test")
        self.assertEqual(event.command_kind, "pytest")
        self.assertEqual(event.command_risk, "safe")
        self.assertEqual(event.command_outcome, "pass")
        self.assertTrue(event.validation_candidate)
        self.assert_no_leak(event.to_json(), "TOKEN=abc123", "abc123")

    def test_codex_permission_request_records_destructive_denial(self) -> None:
        result = runtime_adapter_for("codex").normalize_event(
            load_fixture("codex_permission_destructive_git_reset.json")
        )
        event = result.normalized_event
        self.assertEqual(event.event_kind, "permission_request")
        self.assertEqual(event.command_kind, "git")
        self.assertEqual(event.command_risk, "destructive")
        self.assertEqual(event.permission_decision, "deny")
        self.assertEqual(event.permission_reason, "destructive git command denied")
        self.assert_no_leak(event.to_json(), "reset --hard")

    def test_codex_compact_session_records_compaction_stage_signal(self) -> None:
        result = runtime_adapter_for("codex").normalize_event(load_fixture("codex_compact_session.json"))
        self.assertEqual(result.normalized_event.event_kind, "session_start")
        self.assertEqual(result.normalized_event.stage_signal, "compaction")

    def test_claude_post_tool_failure_records_failed_release_command_without_secret(self) -> None:
        result = runtime_adapter_for("claude").normalize_event(
            load_fixture("claude_post_tool_failure.json")
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(event.event_kind, "post_tool_use_failure")
        self.assertEqual(event.command_kind, "python3")
        self.assertEqual(event.command_risk, "release")
        self.assertEqual(event.command_outcome, "fail")
        self.assert_no_leak(event.to_json(), "sk-fake-not-real", "--token")

    def test_claude_file_change_after_validation_stales_validation(self) -> None:
        result = runtime_adapter_for("claude").normalize_event(
            load_fixture("claude_file_changed_after_validation.json"),
            base_path="/repo",
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(event.event_kind, "file_changed")
        self.assertEqual(event.changed_paths, ["src/api/schema.py"])
        self.assertEqual(event.validation_outcome, "stale")
        self.assertEqual(event.validation_freshness, "stale")

    def test_claude_permission_denial_keeps_reason_and_destructive_risk(self) -> None:
        result = runtime_adapter_for("claude").normalize_event(
            load_fixture("claude_permission_denied_destructive_command.json")
        )
        event = result.normalized_event
        self.assertEqual(event.event_kind, "permission_request")
        self.assertEqual(event.command_kind, "git")
        self.assertEqual(event.command_risk, "destructive")
        self.assertEqual(event.permission_decision, "deny")
        self.assertEqual(event.permission_reason, "destructive cleanup denied")
        self.assert_no_leak(event.to_json(), "clean -fd")

    def test_claude_precompact_and_postcompact_are_directional_supported_events(self) -> None:
        fixture = load_fixture("claude_precompact_postcompact.json")
        adapter = runtime_adapter_for("claude")
        events = [adapter.normalize_event(event).normalized_event for event in fixture["events"]]
        self.assertEqual([event.event_kind for event in events], ["pre_compact", "post_compact"])
        self.assertTrue(all(not event.capability_degradation for event in events))

    def test_copilot_pretool_unsupported_degrades_without_fake_pre_edit_confidence(self) -> None:
        adapter = runtime_adapter_for("copilot")
        result = adapter.normalize_event(load_fixture("copilot_pretool_unsupported_degrades.json"))
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.DEGRADED.value)
        self.assertEqual(event.event_kind, "pre_tool_use")
        self.assertIn("copilot_pre_tool_use_unsupported", event.capability_degradation)
        self.assertFalse(adapter.capabilities.supports_context_event("PreToolUse"))

    def test_copilot_posttool_edit_is_post_edit_compensation(self) -> None:
        result = runtime_adapter_for("copilot").normalize_event(
            load_fixture("copilot_posttool_edit_compensation.json")
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(event.event_kind, "post_tool_use")
        self.assertEqual(event.tool_category, "edit")
        self.assertEqual(event.command_risk, "mutation")
        self.assertEqual(event.command_outcome, "pass")
        self.assertEqual(event.changed_paths, ["src/auth/login.py"])

    def test_copilot_stop_is_supported_but_pretool_checks_remain_residual_risk(self) -> None:
        adapter = runtime_adapter_for("copilot")
        result = adapter.normalize_event(load_fixture("copilot_stop_closure_unsupported_checks.json"))
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(result.normalized_event.event_kind, "stop")
        self.assertEqual(adapter.capabilities.default_gate_mode("stop"), "block")
        self.assertIn("pre_tool_advisory_context", adapter.capabilities.unsupported_checks)
        self.assertIn("pre_tool_block", adapter.capabilities.unsupported_checks)

    def test_cline_plan_mode_edit_evidence_degrades(self) -> None:
        result = runtime_adapter_for("cline").normalize_event(
            {
                "event_name": "mode_change",
                "mode": "Plan",
                "changeforge_stage": "implementation-planning",
                "tool_name": "write",
                "path": "src/app.py",
            }
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.DEGRADED.value)
        self.assertEqual(event.event_kind, "user_prompt_submit")
        self.assertEqual(event.stage_signal, "implementation-planning")
        self.assertIn("cline_user_prompt_submit_unsupported", event.capability_degradation)
        self.assertIn("cline_plan_mode_edit_evidence_unsupported", event.capability_degradation)

    def test_roo_review_mode_does_not_expose_edit_tools(self) -> None:
        result = runtime_adapter_for("roo").normalize_event(
            {
                "event_name": "tool_use",
                "mode": "review",
                "tool_name": "write",
                "path": "src/security.py",
            }
        )
        event = result.normalized_event
        self.assertEqual(result.gate_result.outcome, GateOutcome.DEGRADED.value)
        self.assertEqual(event.stage_signal, "code-review")
        self.assertIn("roo_post_tool_use_unsupported", event.capability_degradation)
        self.assertIn("roo_review_mode_edit_tools_unsupported", event.capability_degradation)

    def test_openhands_fake_backend_maps_file_and_test_events(self) -> None:
        backend = FakeOpenHandsBackend(
            events=(
                BackendEvent("file_write", {"path": "/repo/src/app.py"}),
                BackendEvent(
                    "test_command",
                    {
                        "command": "python3 -m unittest",
                        "exit_code": 0,
                        "changed_paths": ["tests/test_app.py"],
                    },
                ),
            ),
            changed_paths=("src/app.py",),
            validation_results=({"validation_outcome": "pass"},),
        )
        handle = backend.start_task({"task_id": "task-1", "sandbox_id": "sandbox-1"})
        adapter = runtime_adapter_for("openhands")
        events = [
            adapter.normalize_event(event.to_adapter_payload(), base_path="/repo").normalized_event
            for event in backend.observe_events(handle)
        ]
        backend.stop_task(handle)

        self.assertEqual([event.event_kind for event in events], ["file_changed", "post_tool_use"])
        self.assertEqual(events[0].changed_paths, ["src/app.py"])
        self.assertEqual(events[1].tool_category, "test")
        self.assertEqual(events[1].command_kind, "python3")
        self.assertEqual(events[1].command_outcome, "pass")
        self.assertEqual(events[1].validation_outcome, "pass")
        self.assertEqual(events[1].validation_freshness, "current")
        self.assertEqual(backend.collect_changed_paths(handle), ("src/app.py",))
        self.assertEqual(backend.collect_validation_results(handle), ({"validation_outcome": "pass"},))
        self.assertTrue(backend.stopped)

    def test_openhands_unknown_backend_event_degrades(self) -> None:
        result = runtime_adapter_for("openhands").normalize_event({"event_type": "network_probe"})
        self.assertEqual(result.gate_result.outcome, GateOutcome.DEGRADED.value)
        self.assertEqual(result.normalized_event.event_kind, "unknown")
        self.assertIn("openhands_unknown_event", result.normalized_event.capability_degradation)


if __name__ == "__main__":
    unittest.main()
