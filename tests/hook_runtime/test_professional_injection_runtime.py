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


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_professional_runtime_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_hook(script_name: str, event: dict, cwd: Path, cache: Path, **env_vars: str) -> subprocess.CompletedProcess[str]:
    event = {**event, "cwd": str(cwd)}
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env.update(env_vars)
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


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


class ProfessionalInjectionRuntimeTests(unittest.TestCase):
    def test_professional_injector_records_prompt_free_active_context(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "review auth token handling and secret leakage",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            common = load_common()
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                state = common.load_state(cwd)
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache

        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Professional Skill Injection", result.stdout)
        self.assertEqual(state["turn_stage"], "review")
        self.assertEqual(state["owner_skill"], "ai-code-review-refactor")
        self.assertNotIn("auth token handling", json.dumps(state))
        self.assertIn("security_or_permission", state["prompt_signals"])

    def test_question_prompt_does_not_create_closure_surface(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "请解释一下这个概念"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(state["turn_stage"], "")
        self.assertEqual(state["professional_injections"], [])

    def test_user_prompt_review_chinese_intent_detected(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "请仔细审查最新提交"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Professional Skill Injection", result.stdout)
        self.assertEqual(state["turn_stage"], "review")
        self.assertIn("review_intent", state["prompt_signals"])

    def test_user_prompt_repair_followup_chinese_detected(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "修复已经提交，请审查"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Professional Skill Injection", result.stdout)
        self.assertEqual(state["turn_stage"], "repair")
        self.assertIn("repair_followup", state["prompt_signals"])

    def test_professional_injector_does_not_set_stage_route_present(self) -> None:
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "review latest commit"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertFalse(state["stage_route_present"])

    def test_read_gate_detects_mcp_filesystem_read_file(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcpfilesystemreadfile",
            "tool_input": {"path": "src/hook-runtime/scripts/changeforge_common.py"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_read_context_gate.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertTrue(state["read_evidence_seen"])
        self.assertIn("src/hook-runtime/scripts/changeforge_common.py", state["read_paths"])

    def test_read_gate_detects_github_pr_diff(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "get_pr_diff",
            "tool_input": {"query": "pull request diff"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_read_context_gate.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertTrue(state["read_evidence_seen"])
        self.assertTrue(state["reviewed_diff_evidence_seen"])
        self.assertTrue(state["review_artifact_seen"])

    def test_permission_gate_blocks_destructive_command_in_block_mode(self) -> None:
        event = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf dist"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_hook(
                "changeforge_permission_policy_gate.py",
                event,
                Path(cwd_s),
                Path(cache_s),
                CHANGEFORGE_AGENT="codex",
                CHANGEFORGE_HOOK_MODE="block",
            )

        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("destructive", payload["reason"])

    def test_permission_gate_pretooluse_warns_for_kubectl_apply(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "kubectl apply -f deploy.yaml"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_permission_policy_gate.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
                CHANGEFORGE_HOOK_MODE="block",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertNotIn("decision", payload)
        self.assertIn("hookSpecificOutput", payload)
        self.assertTrue(state["permission_gate_seen"])
        self.assertIn("warn:kubectl", state["permission_decisions"])

    def test_permission_gate_uses_summarize_command_program(self) -> None:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "FOO=bar kubectl apply -f deploy.yaml"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            result = run_hook(
                "changeforge_permission_policy_gate.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
                CHANGEFORGE_HOOK_MODE="warn",
            )
            state = load_state(cwd, cache)

        self.assertEqual(result.returncode, 0)
        self.assertIn("warn:kubectl", state["permission_decisions"])
        self.assertNotIn("warn:FOO=bar", state["permission_decisions"])

    def test_compaction_snapshot_runs_before_reinject_without_overwriting_active_context(self) -> None:
        common = load_common()
        active_context = {
            "stage": "review",
            "owner_skill": "ai-code-review-refactor",
            "reviewer_skill": "agent-execution-discipline",
            "selected_capabilities": ["implementation-structure-design"],
            "required_quality_gates": ["quality-test-gate"],
        }
        compact_event = {"hook_event_name": "SessionStart", "source": "compact"}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = str(cache)
            try:
                common.merge_state(
                    cwd,
                    "codex",
                    turn_stage="review",
                    active_skill_context=active_context,
                    owner_skill="ai-code-review-refactor",
                    reviewer_skill="agent-execution-discipline",
                )
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
            snapshot = run_hook(
                "changeforge_compaction_snapshot.py",
                compact_event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            injector = run_hook(
                "changeforge_professional_injector.py",
                compact_event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(snapshot.returncode, 0)
        self.assertEqual(injector.returncode, 0)
        self.assertEqual(injector.stdout, "")
        self.assertEqual(state["active_skill_context"]["stage"], "review")
        self.assertTrue(any("stage=review" in item for item in state["compaction_snapshots"]))


if __name__ == "__main__":
    unittest.main()
