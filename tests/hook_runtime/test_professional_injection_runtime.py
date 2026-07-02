from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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


def load_injector():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(
        "changeforge_professional_injector_for_runtime_test",
        SCRIPT_DIR / "changeforge_professional_injector.py",
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


def additional_context(stdout: str) -> str:
    payload = json.loads(stdout)
    return payload["hookSpecificOutput"]["additionalContext"]


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
        self.assertEqual(state["turn_stage"], "code-review")
        self.assertEqual(state["active_skill_context"]["action_stage"], "review")
        self.assertEqual(state["owner_skill"], "security-privacy-gate")
        self.assertNotIn("auth token handling", json.dumps(state))
        self.assertIn("security_or_permission", state["prompt_signals"])
        self.assertEqual(len(state["professional_injection_digests"]), 1)
        self.assertTrue(state["professional_injection_digest"].startswith("sha256:"))
        self.assertEqual(state["last_professional_injection_event"], "UserPromptSubmit")

    def test_professional_injector_fail_opens_when_internal_context_builder_raises(self) -> None:
        injector = load_injector()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            old_cwd = os.getcwd()
            old_cache = os.environ.get("XDG_CACHE_HOME")
            os.chdir(cwd_s)
            os.environ["XDG_CACHE_HOME"] = cache_s
            try:
                with patch.object(injector, "_main", side_effect=RuntimeError("boom")):
                    result = injector.main()
            finally:
                os.chdir(old_cwd)
                if old_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = old_cache

        self.assertEqual(result, 0)

    def test_codex_professional_injection_output_is_bounded(self) -> None:
        long_prompt = "implement " + ("redis cache stampede protection " * 400)
        event = {"hook_event_name": "UserPromptSubmit", "prompt": long_prompt}
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                Path(cwd_s),
                Path(cache_s),
                CHANGEFORGE_AGENT="codex",
            )

        self.assertEqual(result.returncode, 0)
        context = additional_context(result.stdout)
        self.assertLessEqual(len(context), 6000)

    def test_security_focus_guidance_covers_ssrf_redirect_and_redaction(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": (
                "Implement server-side URL fetch validation with allowlist, redirect "
                "revalidation, private metadata address denial, and token redaction."
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                Path(cwd_s),
                Path(cache_s),
                CHANGEFORGE_AGENT="codex",
            )

        self.assertEqual(result.returncode, 0)
        context = additional_context(result.stdout).casefold()
        self.assertIn("security_focus", context)
        self.assertIn("allowlist", context)
        self.assertIn("redirect", context)
        self.assertIn("metadata", context)
        self.assertIn("redact", context)

    def test_cache_focus_guidance_covers_stampede_local_proof(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Implement Redis cache stampede protection for hot keys with TTL jitter and fallback.",
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                Path(cwd_s),
                Path(cache_s),
                CHANGEFORGE_AGENT="codex",
            )

        self.assertEqual(result.returncode, 0)
        context = additional_context(result.stdout).casefold()
        self.assertIn("reliability gate", context)
        self.assertIn("cache_focus", context)
        self.assertIn("per-key coordination", context)
        self.assertIn("ttl jitter", context)
        self.assertIn("no live redis/network", context)
        self.assertIn("fake-cache tests", context)

    def test_structure_focus_guidance_covers_object_method_placement(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": (
                "Refactor scattered order cancellation helpers into a value object, "
                "domain object, service, adapter, or module-local helper without helper bags."
            ),
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            result = run_hook(
                "changeforge_professional_injector.py",
                event,
                Path(cwd_s),
                Path(cache_s),
                CHANGEFORGE_AGENT="codex",
            )

        self.assertEqual(result.returncode, 0)
        context = additional_context(result.stdout).casefold()
        self.assertIn("structure_focus", context)
        self.assertIn("existing object/module owner", context)
        self.assertIn("object-method ownership", context)
        self.assertIn("candidate-visible evidence", context)
        self.assertIn("reject shared utilities/helper bags", context)
        self.assertIn("sdd_choice_gate", context)
        self.assertIn("public api tests", context)
        self.assertIn("adapters", context)
        self.assertIn("helpers private", context)

    def test_question_prompt_does_not_create_closure_surface(self) -> None:
        prompts = (
            "请解释一下这个概念",
            "what is code review?",
            "解释 code review 是什么",
            "什么是 test gate？",
            "fix 是什么意思？",
            "read-before-plan 是什么？",
            "review gate 是干嘛的？",
        )
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                event = {"hook_event_name": "UserPromptSubmit", "prompt": prompt}
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
                self.assertFalse(state["implementation_preflight_required"])
                self.assertFalse(state["implementation_preflight_seen"])
                self.assertFalse(state["implementation_preflight_complete"])

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
        self.assertEqual(state["turn_stage"], "code-review")
        self.assertEqual(state["active_skill_context"]["action_stage"], "review")
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
        self.assertEqual(state["turn_stage"], "debugging-diagnosis")
        self.assertEqual(state["active_skill_context"]["action_stage"], "repair")
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

    def test_professional_injector_suppresses_duplicate_active_context(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python3 -m unittest discover -s tests"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            first = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            second = run_hook(
                "changeforge_professional_injector.py",
                event,
                cwd,
                cache,
                CHANGEFORGE_AGENT="codex",
            )
            state = load_state(cwd, cache)

        self.assertEqual(first.returncode, 0)
        self.assertIn("ChangeForge Professional Skill Injection", first.stdout)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(second.stdout, "")
        self.assertEqual(len(state["professional_injections"]), 1)
        self.assertEqual(len(state["professional_injection_digests"]), 1)
        self.assertTrue(state["professional_injection_digest"].startswith("sha256:"))

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
        self.assertEqual(payload["decision"], "block")
        self.assertIn("destructive", payload["reason"])
        self.assertTrue(state["permission_gate_seen"])
        self.assertIn("block:kubectl", state["permission_decisions"])

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

    def test_session_compact_does_not_write_snapshot_or_overwrite_active_context(self) -> None:
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
        self.assertEqual(state["compaction_snapshots"], [])


if __name__ == "__main__":
    unittest.main()
