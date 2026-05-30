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
        "changeforge_common_for_stop_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_stop(event: dict, cwd: Path, cache: Path) -> subprocess.CompletedProcess[str]:
    event["cwd"] = str(cwd)
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    env.pop("CHANGEFORGE_HOOK_MODE", None)
    env.pop("CHANGEFORGE_AGENT", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "changeforge_stop_closure_gate.py")],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


class StopClosureGateTests(unittest.TestCase):
    def test_empty_state_is_silent(self) -> None:
        event = json.loads((FIXTURE_DIR / "codex_stop_with_changes.json").read_text())
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            result = run_stop(event, Path(cwd), Path(cache))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_changed_paths_emit_closure_reminder(self) -> None:
        common = load_common()
        event = json.loads((FIXTURE_DIR / "claude_stop_with_changes.json").read_text())
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = cache
            try:
                common.save_state(
                    Path(cwd),
                    {
                        "runtime": "claude",
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
            result = run_stop(event, Path(cwd), Path(cache))
        self.assertEqual(result.returncode, 0)
        self.assertIn("ChangeForge Closure Gate reminder", result.stdout)
        self.assertIn("changed files", result.stdout)


if __name__ == "__main__":
    unittest.main()
