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
        "changeforge_common_for_codex_protocol_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_hook(
    script_name: str,
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str = "warn",
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CHANGEFORGE_AGENT"] = "codex"
    env["CHANGEFORGE_HOOK_MODE"] = mode
    env["XDG_CACHE_HOME"] = str(cache)
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


def seed_state(cwd: Path, cache: Path) -> None:
    common = load_common()
    previous_cache = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        common.save_state(
            cwd,
            {
                "runtime": "codex",
                "changed_paths": ["src/services/order_service.py"],
                "structure_findings": ["src/services/order_service.py: new file"],
                "risk_surfaces": [],
                "suggested_skills": ["change-forge-router"],
                "suggested_capabilities": ["implementation-structure-design"],
                "suggested_domain_extensions": [],
                "suggested_gates": ["code-review"],
                "validation_seen": False,
            },
        )
    finally:
        if previous_cache is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous_cache


class CodexOutputProtocolTests(unittest.TestCase):
    def test_post_tool_use_warning_outputs_hook_specific_json(self) -> None:
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "command": (
                    "*** Begin Patch\n"
                    "*** Add File: internal/services/foo_service.go\n"
                    "+package services\n"
                    "*** End Patch"
                )
            },
            "turn_id": "t1",
        }
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            event["cwd"] = cwd
            result = run_hook(
                "changeforge_post_edit_structure_gate.py",
                event,
                Path(cwd),
                Path(cache),
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        hook_output = payload["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PostToolUse")
        self.assertIn("additionalContext", hook_output)
        self.assertIn("ChangeForge Structure Gate triggered", hook_output["additionalContext"])

    def test_stop_warn_outputs_system_message_json(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": "Done",
            "turn_id": "t1",
        }
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            event["cwd"] = cwd
            seed_state(Path(cwd), Path(cache))
            result = run_hook(
                "changeforge_stop_closure_gate.py",
                event,
                Path(cwd),
                Path(cache),
                mode="warn",
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("systemMessage", payload)
        self.assertIn("ChangeForge Closure Gate reminder", payload["systemMessage"])

    def test_stop_block_outputs_continuation_decision(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": "Done",
            "turn_id": "t1",
        }
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            event["cwd"] = cwd
            seed_state(Path(cwd), Path(cache))
            result = run_hook(
                "changeforge_stop_closure_gate.py",
                event,
                Path(cwd),
                Path(cache),
                mode="block",
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("reason", payload)

    def test_stop_block_with_active_stop_hook_does_not_continue(self) -> None:
        event = {
            "hook_event_name": "Stop",
            "stop_hook_active": True,
            "last_assistant_message": "Done",
            "turn_id": "t1",
        }
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            event["cwd"] = cwd
            seed_state(Path(cwd), Path(cache))
            result = run_hook(
                "changeforge_stop_closure_gate.py",
                event,
                Path(cwd),
                Path(cache),
                mode="block",
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertNotEqual(payload.get("decision"), "block")
        self.assertIn("systemMessage", payload)


if __name__ == "__main__":
    unittest.main()
