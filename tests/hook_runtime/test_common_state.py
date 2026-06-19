from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"


def load_common():
    spec = importlib.util.spec_from_file_location(
        "changeforge_common_for_common_state_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CommonStateTests(unittest.TestCase):
    def test_validation_results_go_stale_after_material_change(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            previous_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CACHE_HOME"] = cache_s
            try:
                common.merge_state(
                    cwd,
                    "codex",
                    validation_command_seen=True,
                    validation_results=["pass:current:pytest"],
                )
                state = common.merge_state(cwd, "codex", changed_paths=["src/app.py"])
            finally:
                if previous_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = previous_cache
        self.assertIn("pass:current:pytest", state["validation_results"])
        self.assertIn(
            "stale_after_material_change:validation_before_latest_edit",
            state["validation_results"],
        )


if __name__ == "__main__":
    unittest.main()
