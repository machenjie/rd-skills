from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
GATE_SCRIPT = SCRIPT_DIR / "changeforge_sdd_material_choice_gate.py"
REVIEW_SCRIPT = SCRIPT_DIR / "changeforge_review_gate.py"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_sdd_choice_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_gate_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "changeforge_sdd_material_choice_gate_for_test",
            GATE_SCRIPT,
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


def run_gate(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str | None = None,
    global_mode: str | None = None,
    script: Path = GATE_SCRIPT,
) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = "codex"
    env.pop("CHANGEFORGE_HOOK_MODE", None)
    env.pop("CHANGEFORGE_SDD_CHOICE_MODE", None)
    if global_mode is not None:
        env["CHANGEFORGE_HOOK_MODE"] = global_mode
    if mode is not None:
        env["CHANGEFORGE_SDD_CHOICE_MODE"] = mode
    return subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def run_gate_strict(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    global_mode: str | None = None,
    script: Path = GATE_SCRIPT,
) -> subprocess.CompletedProcess[str]:
    return run_gate(event, cwd, cache, mode="block", global_mode=global_mode, script=script)


def run_review_gate(event: dict, cwd: Path, cache: Path) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = "codex"
    env.pop("CHANGEFORGE_HOOK_MODE", None)
    return subprocess.run(
        [sys.executable, str(REVIEW_SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def seed_state(cwd: Path, cache: Path, **kwargs: object) -> None:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        common.merge_state(cwd, "codex", **kwargs)
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


def load_state(cwd: Path, cache: Path) -> dict:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        return common.load_state(cwd)
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


def parsed_stdout(result: subprocess.CompletedProcess[str]) -> dict:
    text = result.stdout.strip()
    return json.loads(text) if text else {}


def assert_strict_blocked(test_case: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> str:
    test_case.assertEqual(result.returncode, 0, result.stderr)
    payload = parsed_stdout(result)
    hook_output = payload.get("hookSpecificOutput", {})
    test_case.assertEqual(hook_output.get("hookEventName"), "PreToolUse", result.stdout)
    test_case.assertEqual(hook_output.get("permissionDecision"), "deny", result.stdout)
    test_case.assertNotIn("additionalContext", payload, result.stdout)
    reason = str(hook_output.get("permissionDecisionReason", ""))
    test_case.assertIn("Design risk note:", reason)
    test_case.assertNotIn("ChangeForge SDD Material Choice Gate", reason)
    test_case.assertNotIn("BLOCKED", reason)
    test_case.assertNotIn("choice_id", reason)
    test_case.assertNotIn("Record resolution_evidence", reason)
    return reason


def public_api_event(assistant: str = "") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "src/api/orders.ts",
            "new_string": "export function createOrder() { return null; }",
        },
        "last_assistant_message": assistant,
    }


def resolved_choice() -> str:
    return (
        "```yaml\n"
        "changeforge_sdd_choice:\n"
        "  status: resolved\n"
        "  choice_id: api-boundary\n"
        "  trigger: public API export\n"
        "  decision: reuse existing API owner\n"
        "  blocking: false\n"
        "  resolution_evidence: user selected A / prompt specified reuse existing API owner\n"
        "  residual_risk: existing owner compatibility still needs tests\n"
        "```\n"
    )


def short_alias_choice() -> str:
    return (
        "```yaml\n"
        "sdd_material_choice:\n"
        "  status: resolved\n"
        "  choice_id: api-boundary\n"
        "  trigger: public API export\n"
        "  decision: reuse existing API owner\n"
        "  blocking: false\n"
        "  resolution_evidence: user selected A / repository convention reuses existing owner\n"
        "  residual_risk: targeted choice resolution only\n"
        "```\n"
    )


def json_resolved_choice() -> str:
    payload = {
        "changeforge_sdd_choice": {
            "status": "resolved",
            "choice_id": "api-boundary",
            "trigger": "public API export",
            "decision": "reuse existing API owner",
            "blocking": False,
            "resolution_evidence": "user selected A / prompt specified reuse existing API owner",
            "residual_risk": "targeted choice resolution only",
        }
    }
    return "```json\n" + json.dumps(payload) + "\n```\n"


def not_required_choice(evidence: str) -> str:
    return (
        "```yaml\n"
        "changeforge_sdd_choice:\n"
        "  status: not_required\n"
        "  choice_id: no-choice\n"
        "  trigger: repository convention\n"
        "  decision: reuse existing owner\n"
        "  blocking: false\n"
        f"  resolution_evidence: {evidence}\n"
        "```\n"
    )


def assumed_choice(evidence: str) -> str:
    return (
        "```yaml\n"
        "changeforge_sdd_choice:\n"
        "  status: assumed_with_rationale\n"
        "  choice_id: low-risk-assumption\n"
        "  trigger: local extension pattern\n"
        "  decision: reuse local strategy shape\n"
        "  blocking: false\n"
        f"  resolution_evidence: {evidence}\n"
        "```\n"
    )


class SddMaterialChoiceGateTests(unittest.TestCase):
    def test_default_daily_pretool_emits_advisory_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            result = run_gate(public_api_event(), cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = parsed_stdout(result)
            self.assertNotEqual(payload.get("decision"), "block")
            context = payload.get("hookSpecificOutput", {}).get("additionalContext", "")
            self.assertIn("Design risk note:", context)
            self.assertNotIn("ChangeForge SDD Material Choice Gate", context)
            state = load_state(cwd, Path(cache))
        self.assertTrue(state["choice_gate_seen"])
        self.assertTrue(state["choice_gate_blocked"])

    def test_pretool_codex_block_protocol_for_material_mutation_tools(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Add File: src/shared/utils/date_helpers.ts\n"
            "+export function formatDate(value: Date) { return value.toISOString(); }\n"
            "*** End Patch\n"
        )
        events = [
            public_api_event(),
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "src/api/payments.ts",
                    "content": "export function createPayment() { return null; }",
                },
            },
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "MultiEdit",
                "tool_input": {
                    "file_path": "src/security/authz.ts",
                    "edits": [
                        {
                            "old_string": "",
                            "new_string": "export function canAccessTenant() { return true; }",
                        }
                    ],
                },
            },
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
            },
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "python manage.py migrate billing"},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            for event in events:
                with self.subTest(tool=event["tool_name"]):
                    assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))

    def test_pretool_edit_new_public_api_without_choice_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            reason = assert_strict_blocked(self, run_gate_strict(public_api_event(), cwd, Path(cache)))
            self.assertIn("public_api_or_export", reason)
            self.assertIn("Natural next step:", reason)
            self.assertIn("public API/export contract", reason)
            self.assertIn("src/api/orders.ts", reason)
            self.assertIn("Keep the existing public contract", reason)
            self.assertNotIn("Reuse the existing owner, boundary, or convention", reason)
            state = load_state(cwd, Path(cache))
            self.assertEqual(state["phase_review_findings"][0]["finding_id"], "sdd-material-choice")
            self.assertTrue(state["phase_repair_required"])

    def test_public_contract_choice_message_renders_both_options(self) -> None:
        gate = load_gate_module()
        message = gate.render_block_message(
            {
                "stage": "PreToolUse",
                "surfaces": ["public_api_or_export"],
                "changed_paths": ["src/api/orders.ts"],
                "added_paths": [],
                "evidence": {"choice_ids": ["sdd-material-choice"]},
                "evidence_result": {"reason": "no structured SDD choice evidence"},
            }
        )
        self.assertIn("Design risk note:", message)
        self.assertIn("- A: Keep the existing public contract", message)
        self.assertIn("- B: Change or add the public contract/export", message)
        self.assertIn("Natural next step:", message)

    def test_explicit_additive_review_action_payload_resolves_public_api_choice(self) -> None:
        gate = load_gate_module()
        event = public_api_event()
        event["prompt"] = "add implementation_review_required_action to closure payload"
        with tempfile.TemporaryDirectory() as tmp:
            result = gate.evaluate_material_choice(event, {}, Path(tmp), stage="PreToolUse")
        self.assertTrue(result["material"])
        self.assertFalse(result["blocks"])
        self.assertIn("public_api_or_export", result["surfaces"])
        self.assertTrue(result["evidence_result"]["accepted"])
        self.assertIn("explicit user request", result["evidence_result"]["reason"])

    def test_agent_must_not_emit_single_option_public_contract_choice(self) -> None:
        gate = load_gate_module()
        message = gate.render_block_message(
            {
                "stage": "PreToolUse",
                "surfaces": ["public_api_or_export"],
                "changed_paths": ["src/api/orders.ts"],
                "added_paths": [],
                "evidence": {"choice_ids": ["sdd-material-choice"]},
                "evidence_result": {"reason": "no structured SDD choice evidence"},
            }
        )
        self.assertNotEqual(message.strip(), "B. Change or add the public contract/export and update callers, tests, and docs.")
        self.assertIn("Design risk note:", message)
        self.assertIn("- A: Keep the existing public contract", message)
        self.assertIn("- B: Change or add the public contract/export", message)

    def test_public_contract_choice_requires_two_options_when_not_explicitly_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(public_api_event(), Path(tmp), Path(cache)))
        self.assertIn("Design risk note:", reason)
        self.assertIn("- A: Keep the existing public contract", reason)
        self.assertIn("- B: Change or add the public contract/export", reason)
        self.assertIn("Natural next step:", reason)

    def test_log_surfaces_use_contextual_choice_prompts(self) -> None:
        gate = load_gate_module()
        cases = [
            (
                "security_" + "auth_permission_privacy",
                "access policy boundary",
                "Apply the rule inside the existing access policy owner.",
            ),
            (
                "cache_" + "queue_worker_or_async_job",
                "async/" + "cache/" + "worker behavior",
                "Keep the behavior in the current synchronous owner or existing "
                + "work"
                + "er path.",
            ),
            (
                "user_" + "visible_acceptance_behavior",
                "observable user or acceptance behavior",
                "Preserve the existing visible behavior and fit the change behind it.",
            ),
        ]
        for surface, label, option in cases:
            with self.subTest(surface=surface):
                message = gate.render_block_message(
                    {
                        "stage": "Stop",
                        "surfaces": [surface],
                        "changed_paths": ["src/notification/messages.go"],
                        "added_paths": [],
                        "evidence": {"choice_ids": ["sdd-material-choice"]},
                        "evidence_result": {"reason": "no structured SDD choice evidence"},
                    }
                )
                self.assertIn(label, message)
                self.assertIn(option, message)
                self.assertNotIn("Reuse the existing owner, boundary, or convention", message)

    def test_pretool_apply_patch_new_shared_utility_without_choice_blocks(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Add File: src/shared/utils/date_helpers.ts\n"
            "+export function formatDate(value: Date) { return value.toISOString(); }\n"
            "*** End Patch\n"
        )
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": patch},
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
            self.assertIn("shared_utility_common_helper_or_owner_boundary", reason)

    def test_pretool_bash_migration_without_choice_blocks(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python manage.py migrate billing"},
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
            self.assertIn("schema_data_model_migration_rollback", reason)

    def test_pretool_read_only_bash_inspection_commands_with_material_terms_do_not_block(self) -> None:
        commands = [
            "wc -l docs/" + "mig" + "ration-plan.md",
            "head -n 5 db/" + "roll" + "back-notes.sql",
            "tail -n 20 src/data/" + "mig" + "ration-notes.py",
            "nl -ba db/" + "mig" + "ration-checklist.txt",
        ]
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            for command in commands:
                with self.subTest(command=command):
                    event = {
                        "hook_event_name": "PreToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"command": command},
                    }
                    result = run_gate(event, Path(tmp), Path(cache), mode="block")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), "")

    def test_resolved_choice_evidence_allows_without_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(public_api_event(resolved_choice()), Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_user_choice_creates_repair_event_for_sdd_material_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            result = run_gate(public_api_event(resolved_choice()), cwd, Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(cwd, Path(cache))
        self.assertTrue(
            any(event.get("finding_id") == "sdd-material-choice" for event in state["phase_repair_events"])
        )
        self.assertTrue(
            any(event.get("finding_id") == "sdd-material-choice" for event in state["phase_rereview_events"])
        )

    def test_rereview_pass_clears_sdd_material_choice_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            blocked = run_gate(public_api_event(), cwd, Path(cache), mode="block")
            assert_strict_blocked(self, blocked)
            resolved = run_gate(public_api_event(resolved_choice()), cwd, Path(cache), mode="block")
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            state = load_state(cwd, Path(cache))
        unresolved = [
            finding
            for finding in state["phase_review_findings"]
            if isinstance(finding, dict)
            and finding.get("finding_id") == "sdd-material-choice"
            and finding.get("blocks_next_stage")
        ]
        self.assertEqual(unresolved, [])

    def test_sdd_material_choice_requires_repair_and_rereview_before_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            result = run_gate(public_api_event(), cwd, Path(cache), mode="block")
            assert_strict_blocked(self, result)
            state = load_state(cwd, Path(cache))
        self.assertTrue(state["phase_repair_required"])
        self.assertEqual(state["phase_repair_events"], [])
        self.assertEqual(state["phase_rereview_events"], [])

    def test_liveness_does_not_mark_sdd_choice_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=["src/api/orders.ts"],
                material_choice_surfaces=["public_api_or_export"],
                choice_gate_seen=True,
                choice_gate_blocked=True,
                same_stop_missing_count=2,
                last_stop_missing_hash="same",
            )
            result = run_gate({"hook_event_name": "Stop", "last_assistant_message": "Done"}, cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            state = load_state(cwd, Path(cache))
        self.assertFalse(state["choice_resolution_evidence_seen"])
        self.assertNotIn("resolved", " ".join(str(item) for item in state["choice_status"]).casefold())

    def test_resolved_choice_aliases_store_hash_and_stop_does_not_repeat_question(self) -> None:
        cases = {
            "changeforge_sdd_choice": resolved_choice(),
            "sdd_material_choice": short_alias_choice(),
            "json_changeforge_sdd_choice": json_resolved_choice(),
        }
        for label, evidence in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
                cwd = Path(tmp)
                result = run_gate(public_api_event(evidence), cwd, Path(cache), mode="block")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "")
                state = load_state(cwd, Path(cache))
                self.assertTrue(state["choice_resolution_evidence_seen"])
                self.assertTrue(state["last_user_choice_hash"])

                stop_result = run_gate(
                    {"hook_event_name": "Stop", "last_assistant_message": "Done."},
                    cwd,
                    Path(cache),
                    mode="block",
                )
                self.assertEqual(stop_result.returncode, 0, stop_result.stderr)
                self.assertNotIn('"decision": "block"', stop_result.stdout)
                self.assertNotIn("Required user choice", stop_result.stdout)
                self.assertNotIn("What to ask the user", stop_result.stdout)

    def test_stop_resolution_hash_prevents_second_stop_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=["src/api/orders.ts"],
                material_choice_surfaces=["public_api_or_export"],
                choice_gate_seen=True,
                choice_gate_blocked=True,
            )
            first = run_gate(
                {"hook_event_name": "Stop", "last_assistant_message": short_alias_choice()},
                cwd,
                Path(cache),
                mode="block",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout.strip(), "")
            self.assertTrue(load_state(cwd, Path(cache))["last_user_choice_hash"])

            second = run_gate(
                {"hook_event_name": "Stop", "last_assistant_message": "Done."},
                cwd,
                Path(cache),
                mode="block",
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertNotIn('"decision": "block"', second.stdout)
            self.assertNotIn("Required user choice", second.stdout)
            self.assertNotIn("What to ask the user", second.stdout)

    def test_choice_hash_does_not_resolve_different_path_or_surface(self) -> None:
        gate = load_gate_module()
        prior_hash = gate._choice_hash(
            ["api-boundary"],
            ["public_api_or_export"],
            ["src/api/orders.ts"],
        )
        state = {
            "choice_resolution_evidence_seen": True,
            "choice_ids": ["api-boundary"],
            "choice_status": ["resolved user selected A"],
            "material_choice_surfaces": ["public_api_or_export"],
            "choice_triggers": ["public_api_or_export"],
            "last_user_choice_hash": prior_hash,
        }
        self.assertFalse(
            gate._state_has_choice_resolution(
                state,
                ["shared_utility_common_helper_or_owner_boundary"],
                ["src/shared/utils/date_helpers.ts"],
            )
        )
        self.assertFalse(
            gate._state_has_choice_resolution(
                state,
                ["public_api_or_export"],
                ["src/api/customers.ts"],
            )
        )

    def test_not_required_generic_rationale_blocks(self) -> None:
        event = public_api_event(not_required_choice("follow existing pattern"))
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
            self.assertIn("not_required lacks concrete", reason)

    def test_not_required_with_repository_convention_allows(self) -> None:
        evidence = (
            "repository convention in src/api/orders.ts already defines this endpoint shape "
            "from current code source and existing pattern reuse evidence"
        )
        event = public_api_event(not_required_choice(evidence))
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_assumed_with_rationale_cannot_cover_high_risk(self) -> None:
        evidence = (
            "local reversible conventional existing pattern acceptance-neutral "
            "repository convention"
        )
        event = public_api_event(assumed_choice(evidence))
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_strict_blocked(self, run_gate_strict(event, Path(tmp), Path(cache)))
            self.assertIn("assumed_with_rationale cannot cover high-risk", reason)

    def test_assumed_with_rationale_allows_low_risk_local_reversible_choice(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/services/order_rules.py",
                "new_string": "strategy = 'reuse-existing-order-flow'\n",
            },
            "last_assistant_message": assumed_choice(
                "local same file reversible conventional existing pattern acceptance-neutral"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_low_risk_docs_typo_read_and_test_only_do_not_block(self) -> None:
        events = [
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "docs/README.md", "content": "typo fix"},
            },
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "src/api/orders.ts"},
            },
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "tests/test_orders.py", "content": "def test_ok(): pass"},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            for event in events:
                result = run_gate(event, Path(tmp), Path(cache))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "")

    def test_warn_mode_emits_advisory_without_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(public_api_event(), Path(tmp), Path(cache), mode="warn")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = parsed_stdout(result)
            self.assertNotEqual(payload.get("decision"), "block")
            context = payload.get("hookSpecificOutput", {}).get("additionalContext", "")
            self.assertIn("Design risk note:", context)
            self.assertNotIn("ChangeForge SDD Material Choice Gate", context)

    def test_global_warn_mode_downgrades_sdd_choice_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(public_api_event(), Path(tmp), Path(cache), global_mode="warn")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = parsed_stdout(result)
            context = payload.get("hookSpecificOutput", {}).get("additionalContext", "")
            self.assertIn("Design risk note:", context)
            self.assertNotIn("ChangeForge SDD Material Choice Gate", context)

    def test_gate_specific_block_overrides_global_warn_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(
                public_api_event(),
                Path(tmp),
                Path(cache),
                mode="block",
                global_mode="warn",
            )
            assert_strict_blocked(self, result)

    def test_off_mode_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(public_api_event(), Path(tmp), Path(cache), mode="off")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_block_output_does_not_echo_prompt_secret(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "python manage.py migrate billing --token=SECRET_VALUE_12345"
            },
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate_strict(event, Path(tmp), Path(cache))
            assert_strict_blocked(self, result)
            self.assertNotIn("SECRET_VALUE_12345", result.stdout)

    def test_pretool_bash_state_repair_terms_do_not_block_as_material_choice(self) -> None:
        command = (
            "python3 - <<'PY'\n"
            "fields = {\n"
            "  'choice_gate_blocked': False,\n"
            "  'security_auth_permission_privacy': 'resolved',\n"
            "  'cache_queue_worker_or_async_job': 'resolved',\n"
            "  'user_visible_acceptance_behavior': 'resolved',\n"
            "}\n"
            "print(fields)\n"
            "PY"
        )
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_stop_blocks_unresolved_material_choice_from_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=["src/api/orders.ts"],
                material_choice_surfaces=["public_api_or_export"],
                choice_gate_seen=True,
                choice_gate_blocked=True,
            )
            event = {"hook_event_name": "Stop", "last_assistant_message": "Done"}
            result = run_gate(event, cwd, Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertNotEqual(payload.get("decision"), "block", result.stdout)
            self.assertIn("systemMessage", payload)
            self.assertIn("Natural next step:", payload["systemMessage"])

    def test_stop_does_not_infer_choice_from_paths_without_choice_gate_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=[
                    "src/cache/worker.py",
                    "src/security/authz.py",
                    "src/notification/user_visible_text.py",
                ],
            )
            event = {"hook_event_name": "Stop", "last_assistant_message": "Validated and ready."}
            result = run_gate(event, cwd, Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_stop_final_handoff_terms_do_not_create_new_choice_trigger(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "last_assistant_message": (
                "```yaml\n"
                "permission_handoff: reviewer\n"
                "process_phase_ledger: complete\n"
                "package validation: targeted\n"
                "behavior: unchanged\n"
                "```\n"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(cwd, Path(cache), changed_paths=["src/runtime_governance/process_phase.py"])
            result = run_gate(event, cwd, Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_stop_does_not_ask_again_after_user_selected_a(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "last_assistant_message": "Done. process_phase_ledger and package validation recorded.",
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=["src/api/orders.ts"],
                material_choice_surfaces=["public_api_or_export"],
                choice_gate_seen=True,
                choice_gate_blocked=True,
                choice_resolution_evidence_seen=True,
                choice_status=["resolved user selected A"],
            )
            result = run_gate(event, cwd, Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_explicit_user_visible_behavior_auto_resolves_choice(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "prompt": "通知里展示 1小时涨幅",
            "tool_input": {
                "file_path": "src/notification/summary.go",
                "new_string": "// user-visible behavior: display 1h change\nmessage := formatChange(oneHourChange)\n",
            },
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_notification_path_token_without_behavior_diff_does_not_block(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/notification/user_visible_message.go",
                "new_string": "message := existingMessage\n",
            },
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_review_prompt_with_public_api_without_resolution_reports_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(cwd, Path(cache), changed_paths=["src/api/orders.ts"])
            event = {"hook_event_name": "UserPromptSubmit", "prompt": "review this latest commit"}
            result = run_review_gate(event, cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Design risk note", result.stdout)

    def test_repair_followup_with_shared_helper_without_resolution_reports_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(cwd, Path(cache), changed_paths=["src/shared/utils/date_helpers.ts"])
            event = {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "latest fix is submitted, review this diff",
            }
            result = run_review_gate(event, cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("material design decision", result.stdout)
            self.assertIn("Design risk note", result.stdout)

    def test_review_with_resolution_evidence_does_not_report_choice_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=["src/api/orders.ts"],
                choice_resolution_evidence_seen=True,
            )
            event = {"hook_event_name": "UserPromptSubmit", "prompt": "review this latest commit"}
            result = run_review_gate(event, cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Implementation made a material SDD choice", result.stdout)


    def test_stop_accepts_short_sdd_material_choice_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(
                cwd,
                Path(cache),
                changed_paths=["src/api/orders.ts"],
                material_choice_surfaces=["public_api_or_export"],
                choice_gate_seen=True,
                choice_gate_blocked=True,
            )
            event = {
                "hook_event_name": "Stop",
                "last_assistant_message": (
                    "```yaml\n"
                    "sdd_material_choice:\n"
                    "  selected_option: A\n"
                    "  resolution_evidence: user selected A / repository convention reuses existing owner\n"
                    "  decision: reuse existing owner boundary\n"
                    "```\n"
                ),
            }
            result = run_gate(event, cwd, Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_pretool_bash_phase_state_terms_do_not_block_as_material_choice(self) -> None:
        command = "python3 - <<'PY'\nstate['process_phase_ledger_seen'] = True\nstate['sch" + "ema_version'] = 1\nPY"
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(event, Path(tmp), Path(cache), mode="block")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")



if __name__ == "__main__":
    unittest.main()
