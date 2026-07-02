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


def run_gate(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str | None = None,
    script: Path = GATE_SCRIPT,
) -> subprocess.CompletedProcess[str]:
    payload = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env["CHANGEFORGE_AGENT"] = "codex"
    env.pop("CHANGEFORGE_HOOK_MODE", None)
    env.pop("CHANGEFORGE_SDD_CHOICE_MODE", None)
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


def parsed_stdout(result: subprocess.CompletedProcess[str]) -> dict:
    text = result.stdout.strip()
    return json.loads(text) if text else {}


def assert_blocked(test_case: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> str:
    test_case.assertEqual(result.returncode, 0, result.stderr)
    payload = parsed_stdout(result)
    test_case.assertEqual(payload.get("decision"), "block", result.stdout)
    reason = str(payload.get("reason", ""))
    test_case.assertIn("ChangeForge SDD Material Choice Gate: BLOCKED", reason)
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
    def test_pretool_edit_new_public_api_without_choice_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_blocked(self, run_gate(public_api_event(), Path(tmp), Path(cache)))
            self.assertIn("public_api_or_export", reason)
            self.assertIn("What to ask the user", reason)

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
            reason = assert_blocked(self, run_gate(event, Path(tmp), Path(cache)))
            self.assertIn("shared_utility_common_helper_or_owner_boundary", reason)

    def test_pretool_bash_migration_without_choice_blocks(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python manage.py migrate billing"},
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_blocked(self, run_gate(event, Path(tmp), Path(cache)))
            self.assertIn("schema_data_model_migration_rollback", reason)

    def test_resolved_choice_evidence_allows_without_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            result = run_gate(public_api_event(resolved_choice()), Path(tmp), Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_not_required_generic_rationale_blocks(self) -> None:
        event = public_api_event(not_required_choice("follow existing pattern"))
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            reason = assert_blocked(self, run_gate(event, Path(tmp), Path(cache)))
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
            reason = assert_blocked(self, run_gate(event, Path(tmp), Path(cache)))
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
            self.assertIn("ChangeForge SDD Material Choice Gate: advisory", context)

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
            result = run_gate(event, Path(tmp), Path(cache))
            assert_blocked(self, result)
            self.assertNotIn("SECRET_VALUE_12345", result.stdout)

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
            reason = assert_blocked(self, run_gate(event, cwd, Path(cache)))
            self.assertIn("How to continue after user chooses", reason)

    def test_review_prompt_with_public_api_without_resolution_reports_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
            cwd = Path(tmp)
            seed_state(cwd, Path(cache), changed_paths=["src/api/orders.ts"])
            event = {"hook_event_name": "UserPromptSubmit", "prompt": "review this latest commit"}
            result = run_review_gate(event, cwd, Path(cache))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Implementation made a material SDD choice", result.stdout)

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
            self.assertIn("agent silently made a user-owned design choice", result.stdout)

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


if __name__ == "__main__":
    unittest.main()
