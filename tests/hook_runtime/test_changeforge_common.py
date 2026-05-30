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
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_hook(script_name: str, stdin: str, cwd: Path, cache: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env.pop("CHANGEFORGE_HOOK_MODE", None)
    env.pop("CHANGEFORGE_AGENT", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        input=stdin,
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


class ChangeForgeCommonTests(unittest.TestCase):
    def test_invalid_json_stdin_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            result = run_hook(
                "changeforge_post_edit_structure_gate.py",
                "not json",
                Path(cwd),
                Path(cache),
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_runtime_and_tool_normalization(self) -> None:
        common = load_common()
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "apply_patch",
            "toolInput": {"file_path": "src/services/order_service.py"},
        }
        self.assertEqual(common.detect_runtime(event), "codex")
        self.assertEqual(common.event_name(event), "PostToolUse")
        self.assertEqual(common.tool_name(event), "apply_patch")

    def test_runtime_detection_prefers_env_override_and_codex_snake_case(self) -> None:
        common = load_common()
        previous_agent = os.environ.get("CHANGEFORGE_AGENT")
        os.environ["CHANGEFORGE_AGENT"] = "codex"
        try:
            self.assertEqual(common.detect_runtime({"hookEventName": "Stop"}), "codex")
        finally:
            if previous_agent is None:
                os.environ.pop("CHANGEFORGE_AGENT", None)
            else:
                os.environ["CHANGEFORGE_AGENT"] = previous_agent

        self.assertEqual(common.detect_runtime({"hook_event_name": "PostToolUse"}), "codex")
        self.assertEqual(common.detect_runtime({"hookEventName": "PostToolUse"}), "claude")

    def test_extract_changed_paths_from_apply_patch(self) -> None:
        common = load_common()
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_apply_patch.json").read_text())
        self.assertEqual(common.extract_changed_paths(event), ["src/services/order_service.py"])

    def test_extract_bash_command(self) -> None:
        common = load_common()
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_bash_kubectl.json").read_text())
        self.assertEqual(
            common.extract_bash_command(event),
            "kubectl apply -f deploy/helm/values.yaml",
        )

    def test_debug_log_writes_to_cache_when_enabled(self) -> None:
        common = load_common()
        previous_cache = os.environ.get("XDG_CACHE_HOME")
        previous_debug = os.environ.get("CHANGEFORGE_HOOK_DEBUG")
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ["CHANGEFORGE_HOOK_DEBUG"] = "1"
            try:
                common.debug_log(Path(cwd), "structure gate runtime=codex")
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
                if previous_debug is None:
                    os.environ.pop("CHANGEFORGE_HOOK_DEBUG", None)
                else:
                    os.environ["CHANGEFORGE_HOOK_DEBUG"] = previous_debug

            debug_logs = list(Path(cache).glob("changeforge/hooks/*/debug.log"))
            self.assertEqual(len(debug_logs), 1)
            self.assertIn("structure gate runtime=codex", debug_logs[0].read_text())


if __name__ == "__main__":
    unittest.main()
