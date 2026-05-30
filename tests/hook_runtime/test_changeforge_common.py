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
            "hookEventName": "PostToolUse",
            "toolName": "apply_patch",
            "toolInput": {"file_path": "src/services/order_service.py"},
        }
        self.assertEqual(common.detect_runtime(event), "codex")
        self.assertEqual(common.event_name(event), "PostToolUse")
        self.assertEqual(common.tool_name(event), "apply_patch")

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


if __name__ == "__main__":
    unittest.main()
