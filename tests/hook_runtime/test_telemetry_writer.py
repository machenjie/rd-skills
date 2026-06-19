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
            "repository_context_seen",
            "workflow_state_seen",
            "tool_permission_sandbox_seen",
            "skill_efficacy_benchmark_seen",
            "plan_execution_consistency_seen",
            "validation_freshness_seen",
        ):
            self.assertIn(field, record)
        self.assertRegex(record["session_id"], r"^sess-1:[0-9a-f]{12}$")
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

    def test_writes_bounded_changeforge_closure_object(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            repo = Path(cwd)
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="stop_closure_gate",
                event_name="Stop",
                mode="warn",
                closure_contract_verdict="needs_review",
                changeforge_closure={
                    "adapter": "codex",
                    "verdict": "needs_review",
                    "supported_checks": ["validation"],
                    "unsupported_checks": [],
                    "present_evidence": ["route_manifest"],
                    "missing_evidence": ["review"],
                    "negative_evidence": [],
                    "validation": {
                        "outcome": "pass",
                        "freshness": "current",
                        "scope": "module",
                        "command_kind": "module",
                    },
                    "review": {
                        "review_outcome": "finding",
                        "repair_present": True,
                        "rereview_present": False,
                    },
                    "changed_files": {
                        "changed": ["src/runtime_governance/closure.py"],
                        "deleted": [],
                        "generated": [],
                    },
                    "residual_risk": ["repair requires re-review"],
                    "next_owner": "agent",
                },
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["closure_contract_verdict"], "needs_review")
        self.assertEqual(record["changeforge_closure"]["verdict"], "needs_review")
        self.assertEqual(
            record["changeforge_closure"]["changed_files"]["changed"],
            ["src/runtime_governance/closure.py"],
        )
        self.assertEqual(record["changeforge_closure"]["validation"]["scope"], "module")

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

    def test_extract_manifest_fields_parses_route_and_stage(self) -> None:
        common = load_common()
        text = (
            "Routing result.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "  selected_capabilities:\n"
            "    - implementation-structure-design\n"
            "    - authentication-authorization\n"
            "  selected_domain_extensions: []\n"
            "  required_references:\n"
            "    - references/routing-rules.md\n"
            "  required_quality_gates:\n"
            "    - security gate\n"
            "  skipped_quality_gates:\n"
            "    - gate: delivery gate\n"
            "      reason: no deploy\n"
            "```\n\n"
            "```yaml\n"
            "changeforge_stage_route:\n"
            "  current_stage: coding\n"
            "  selected_capabilities: []\n"
            "```\n"
        )
        result = common.extract_manifest_fields(text)
        self.assertTrue(result["route_present"])
        self.assertTrue(result["stage_present"])
        self.assertEqual(result["current_stage"], "coding")
        self.assertEqual(
            result["selected_capabilities"],
            ["implementation-structure-design", "authentication-authorization"],
        )
        self.assertEqual(result["selected_skills"], ["backend-change-builder"])
        self.assertEqual(result["required_references"], ["references/routing-rules.md"])
        self.assertEqual(result["required_quality_gates"], ["security gate"])
        self.assertEqual(result["skipped_quality_gates"], ["delivery gate"])

    def test_extract_manifest_fields_empty_on_no_manifest(self) -> None:
        common = load_common()
        result = common.extract_manifest_fields("just prose, no manifest here")
        self.assertFalse(result["route_present"])
        self.assertFalse(result["stage_present"])
        self.assertEqual(result["selected_capabilities"], [])
        self.assertEqual(result["current_stage"], "")

    def test_extract_manifest_fields_route_token_is_not_manifest(self) -> None:
        common = load_common()
        result = common.extract_manifest_fields(
            "The handoff mentions changeforge_route but emits no YAML block."
        )
        self.assertFalse(result["route_present"])

    def test_extract_manifest_fields_requires_route_contract_fields(self) -> None:
        common = load_common()
        text = (
            "```yaml\n"
            "changeforge_route:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "```\n"
        )
        result = common.extract_manifest_fields(text)
        self.assertFalse(result["route_present"])
        self.assertEqual(result["selected_skills"], ["backend-change-builder"])
        self.assertEqual(result["selected_capabilities"], [])

    def test_extract_manifest_fields_route_not_triggered_by_stage_only(self) -> None:
        common = load_common()
        text = "```yaml\nchangeforge_stage_route:\n  current_stage: testing\n```\n"
        result = common.extract_manifest_fields(text)
        self.assertFalse(result["route_present"])
        self.assertTrue(result["stage_present"])
        self.assertEqual(result["current_stage"], "testing")

    def test_fallback_session_id_groups_one_turn_not_a_day(self) -> None:
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
            )
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="stop_closure_gate",
                event_name="Stop",
                mode="warn",
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 2)
        session_id = records[0]["session_id"]
        # Both hooks in one turn share a session id (so review can correlate them).
        self.assertEqual(records[0]["session_id"], records[1]["session_id"])
        # The fallback id carries a per-turn component, not just the date.
        self.assertRegex(session_id, r"^[0-9a-f]{8}-\d{4}-\d{2}-\d{2}-[0-9a-f]{12}$")

    def test_runtime_session_id_is_scoped_per_turn(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            repo = Path(cwd)
            # Two hooks in one turn share the stable runtime CLI session id ...
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="post_edit_structure_gate",
                event_name="PostToolUse",
                mode="warn",
                session_id="cli-uuid",
            )
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="stop_closure_gate",
                event_name="Stop",
                mode="warn",
                session_id="cli-uuid",
            )
            # ... the Stop boundary clears per-turn state ...
            common.clear_state(repo, "codex")
            # ... so the next turn under the same CLI session id is a new session.
            common.write_telemetry_event(
                repo,
                runtime="codex",
                hook_name="post_edit_structure_gate",
                event_name="PostToolUse",
                mode="warn",
                session_id="cli-uuid",
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 3)
        first, second, third = (record["session_id"] for record in records)
        # Same turn -> same scoped id; the runtime id stays a traceable prefix.
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("cli-uuid:"))
        # A stable runtime session id must not merge unrelated turns.
        self.assertNotEqual(first, third)
        self.assertTrue(third.startswith("cli-uuid:"))

    def test_manifest_fields_recorded_when_provided(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            common.write_telemetry_event(
                Path(cwd),
                runtime="codex",
                hook_name="stop_closure_gate",
                event_name="Stop",
                mode="warn",
                session_id="sess-9",
                stage_manifest_detected=True,
                manifest_current_stage="coding",
                manifest_selected_capabilities=["implementation-structure-design"],
                manifest_skipped_quality_gates=["delivery gate"],
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertTrue(record["stage_manifest_detected"])
        self.assertEqual(record["manifest_current_stage"], "coding")
        self.assertEqual(
            record["manifest_selected_capabilities"], ["implementation-structure-design"]
        )
        self.assertEqual(record["manifest_skipped_quality_gates"], ["delivery gate"])

    def test_implementation_preflight_telemetry_fields_recorded(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            common.write_telemetry_event(
                Path(cwd),
                runtime="codex",
                hook_name="pre_edit_structure_gate",
                event_name="PreToolUse",
                mode="block",
                implementation_preflight_required=True,
                implementation_preflight_seen=False,
                implementation_preflight_complete=False,
                implementation_preflight_blocked=True,
                edit_without_preflight_seen=True,
                post_edit_confirmed_preflight_gap=True,
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertTrue(record["implementation_preflight_required"])
        self.assertFalse(record["implementation_preflight_seen"])
        self.assertFalse(record["implementation_preflight_complete"])
        self.assertTrue(record["implementation_preflight_blocked"])
        self.assertTrue(record["edit_without_preflight_seen"])
        self.assertTrue(record["post_edit_confirmed_preflight_gap"])

    def test_workflow_signal_telemetry_fields_recorded(self) -> None:
        common = load_common()
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            os.environ["XDG_CACHE_HOME"] = cache
            os.environ.pop("CHANGEFORGE_TELEMETRY", None)
            common.write_telemetry_event(
                Path(cwd),
                runtime="codex",
                hook_name="stop_closure_gate",
                event_name="Stop",
                mode="warn",
                repository_context_seen=True,
                workflow_state_seen=True,
                tool_permission_sandbox_seen=True,
                skill_efficacy_benchmark_seen=True,
                plan_execution_consistency_seen=True,
                validation_freshness_seen=True,
            )
            records = read_records(Path(cache))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertTrue(record["repository_context_seen"])
        self.assertTrue(record["workflow_state_seen"])
        self.assertTrue(record["tool_permission_sandbox_seen"])
        self.assertTrue(record["skill_efficacy_benchmark_seen"])
        self.assertTrue(record["plan_execution_consistency_seen"])
        self.assertTrue(record["validation_freshness_seen"])


if __name__ == "__main__":
    unittest.main()
