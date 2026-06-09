from __future__ import annotations

import contextlib
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


NEW_FINDING_FIELDS = (
    "file_naming_findings",
    "reuse_findings",
    "extension_reuse_findings",
    "advanced_refactor_findings",
    "comment_findings",
    "structure_quality_findings",
)


@contextlib.contextmanager
def cache_env(cache: Path):
    previous = os.environ.get("XDG_CACHE_HOME")
    os.environ["XDG_CACHE_HOME"] = str(cache)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = previous


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

    def test_new_state_fields_initialized(self) -> None:
        common = load_common()
        state = common._empty_state()
        for field in NEW_FINDING_FIELDS:
            self.assertEqual(state[field], [])
        self.assertTrue(all(field in common.STATE_LIST_FIELDS for field in NEW_FINDING_FIELDS))

    def test_new_state_fields_round_trip(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                common.save_state(
                    Path(cwd),
                    {
                        "runtime": "codex",
                        "file_naming_findings": ["a.go: mismatch"],
                        "comment_findings": ["a.go: uncommented"],
                        "structure_quality_findings": ["a.go: weak signature"],
                    },
                )
                loaded = common.load_state(Path(cwd))
        self.assertEqual(loaded["file_naming_findings"], ["a.go: mismatch"])
        self.assertEqual(loaded["comment_findings"], ["a.go: uncommented"])
        self.assertEqual(loaded["structure_quality_findings"], ["a.go: weak signature"])

    def test_merge_state_supports_finding_fields(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                common.merge_state(
                    Path(cwd),
                    "codex",
                    file_naming_findings=["x"],
                    reuse_findings=["y"],
                    extension_reuse_findings=["z"],
                    advanced_refactor_findings=["w"],
                    comment_findings=["c"],
                    structure_quality_findings=["q"],
                )
                state = common.load_state(Path(cwd))
        self.assertEqual(state["file_naming_findings"], ["x"])
        self.assertEqual(state["reuse_findings"], ["y"])
        self.assertEqual(state["extension_reuse_findings"], ["z"])
        self.assertEqual(state["advanced_refactor_findings"], ["w"])
        self.assertEqual(state["comment_findings"], ["c"])
        self.assertEqual(state["structure_quality_findings"], ["q"])

    def test_legacy_state_file_missing_fields_is_compatible(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                path = common._state_path(Path(cwd))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps({"runtime": "codex", "changed_paths": ["a.py"]}),
                    encoding="utf-8",
                )
                loaded = common.load_state(Path(cwd))
        self.assertEqual(loaded["changed_paths"], ["a.py"])
        for field in NEW_FINDING_FIELDS:
            self.assertEqual(loaded[field], [])

    def test_state_written_to_cache_not_project_source(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            with cache_env(Path(cache)):
                common.merge_state(Path(cwd), "codex", changed_paths=["a.py"])
            cache_state = list(Path(cache).glob("changeforge/hooks/*/current-turn.json"))
            project_state = list(Path(cwd).rglob("current-turn.json"))
        self.assertEqual(len(cache_state), 1)
        self.assertEqual(project_state, [])


if __name__ == "__main__":
    unittest.main()
