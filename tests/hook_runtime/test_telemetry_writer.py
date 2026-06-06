from __future__ import annotations

import glob
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
        "changeforge_common_for_telemetry_test",
        SCRIPT_DIR / "changeforge_common.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_records(cache: Path) -> list[dict]:
    files = glob.glob(str(cache / "changeforge" / "telemetry" / "*" / "sessions" / "*.jsonl"))
    records: list[dict] = []
    for file_path in files:
        for line in Path(file_path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


class TelemetryWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {
            key: os.environ.get(key)
            for key in ("XDG_CACHE_HOME", "CHANGEFORGE_TELEMETRY")
        }

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_writes_jsonl_record_with_required_fields(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            repo = Path(cwd)
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="post_edit_structure_gate",
                event_name="PostToolUse",
                mode="warn",
                session_id="sess-1",
                cwd=str(repo),
                tool_name="apply_patch",
                changed_paths=["src/services/order_service.py"],
                hook_findings={"reuse_findings": ["x"]},
                suggested_skills=["backend-change-builder"],
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 1)
        record = records[0]
        for field in (
            "schema_version",
            "timestamp_utc",
            "repo_hash",
            "cwd_hash",
            "runtime",
            "hook_name",
            "event_name",
            "session_id",
            "mode",
            "tool_name",
            "changed_paths",
            "hook_findings",
            "suggested_skills",
            "suggested_capabilities",
            "route_manifest_detected",
            "required_references_detected",
            "validation_evidence_detected",
            "residual_risk_detected",
        ):
            self.assertIn(field, record)
        self.assertEqual(record["session_id"], "sess-1")
        self.assertEqual(record["changed_paths"], ["src/services/order_service.py"])

    def test_no_absolute_paths_recorded(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            repo = Path(cwd)
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="risk_surface_gate",
                event_name="PostToolUse",
                mode="warn",
                cwd=str(repo),
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 1)
        serialized = json.dumps(records[0])
        self.assertNotIn(str(Path(cwd).resolve()), serialized)

    def test_command_program_redacts_secrets(self) -> None:
        common = load_common()
        program = common.summarize_command_program(
            "CHANGEFORGE_AGENT=codex kubectl apply -f s.yaml --token=SUPERSECRET"
        )
        self.assertEqual(program, "kubectl")
        self.assertNotIn("SUPERSECRET", program)

    def test_session_id_from_event_prefers_known_keys(self) -> None:
        common = load_common()
        self.assertEqual(common.session_id_from_event({"session_id": "abc"}), "abc")
        self.assertEqual(common.session_id_from_event({"turnId": "t1"}), "t1")
        self.assertEqual(common.session_id_from_event({}), "")

    def test_disabled_switch_skips_writing(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ["CHANGEFORGE_TELEMETRY"] = "off"
            common.write_telemetry_event(
                Path(cwd),
                runtime="codex",
                hook_name="stop_closure_gate",
                event_name="Stop",
                mode="warn",
            )
            self.assertEqual(read_records(Path(cache)), [])

    def test_write_failure_is_fail_open(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd:
            os.environ["XDG_CACHE_HOME"] = os.path.join(cwd, "missing")
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            # Should not raise even if anything goes wrong internally.
            common.write_telemetry_event(
                Path(cwd),
                runtime="unknown-runtime",
                hook_name="post_edit_structure_gate",
                event_name="PostToolUse",
                mode="warn",
            )

    def test_hook_run_emits_telemetry(self) -> None:
        # Running a real gate over a watched event should append telemetry.
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_apply_patch.json").read_text())
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd, cache = Path(cwd_s), Path(cache_s)
            event["cwd"] = str(cwd)
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = str(cache)
            env.pop("CHANGEFORGE_HOOK_MODE", None)
            env.pop("CHANGEFORGE_AGENT", None)
            env.pop("CHANGEFORGE_TELEMETRY", None)
            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "changeforge_post_edit_structure_gate.py")],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                cwd=str(cwd),
                env=env,
                check=False,
            )
            records = read_records(cache)
        self.assertTrue(records)
        self.assertEqual(records[0]["hook_name"], "post_edit_structure_gate")


if __name__ == "__main__":
    unittest.main()
