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


if __name__ == "__main__":
    unittest.main()
