from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory, load_memory_events, load_telemetry_records


class TrajectoryBuilderTests(unittest.TestCase):
    def test_builds_complete_loop_from_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            root = Path(tmp_s)
            sessions = root / "repo" / "sessions"
            sessions.mkdir(parents=True)
            (sessions / "sample.jsonl").write_text(
                "\n".join(json.dumps(record) for record in complete_records()) + "\n",
                encoding="utf-8",
            )
            records = load_telemetry_records(root, "repo", "sess")
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        self.assertIsNotNone(trajectory)
        assert trajectory is not None
        self.assertEqual([step["stage"] for step in trajectory["steps"]], ["route", "read", "plan", "edit", "test", "review", "stop"])
        report = analyze_trajectory(trajectory)
        self.assertEqual(report["closure_status"], "pass")
        self.assertEqual(report["validation_freshness"], "fresh")

    def test_no_samples_found_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "inspect-trajectory.py"),
                    "--telemetry-root",
                    tmp_s,
                    "--repo-hash",
                    "missing",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("no samples found", result.stdout)

    def test_loads_memory_events_as_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            root = Path(tmp_s)
            events = root / "repo" / "events"
            events.mkdir(parents=True)
            (events / "2026-06-01.jsonl").write_text(
                json.dumps(
                    {
                        "created_at": "2026-06-01T00:00:00Z",
                        "repo_hash": "repo",
                        "session_id": "sess",
                        "task_fingerprint": "task",
                        "type": "validation_result",
                        "paths": ["src/app.py"],
                        "outcome": "passed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            memory_events = load_memory_events(root, "repo", "sess")
        trajectory = build_trajectory([], repo_hash="repo", session_id="sess", memory_events=memory_events)
        self.assertIsNotNone(trajectory)
        assert trajectory is not None
        self.assertEqual(trajectory["steps"][0]["stage"], "test")


def complete_records() -> list[dict[str, object]]:
    return [
        {
            "timestamp_utc": "2026-06-01T00:00:00Z",
            "session_id": "sess",
            "event_name": "UserPromptSubmit",
            "runtime": "codex",
            "route_manifest_detected": True,
            "manifest_selected_skills": ["backend-change-builder"],
            "manifest_selected_capabilities": ["implementation-structure-design"],
            "manifest_required_references": ["docs/TELEMETRY.md"],
            "manifest_required_quality_gates": ["test gate"],
        },
        {
            "timestamp_utc": "2026-06-01T00:01:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "read",
            "tool_name": "rg",
            "read_paths": ["src/app.py"],
            "read_evidence_seen": True,
            "repository_context_seen": True,
        },
        {
            "timestamp_utc": "2026-06-01T00:02:00Z",
            "session_id": "sess",
            "event_name": "PreToolUse",
            "runtime": "codex",
            "turn_stage": "plan",
            "implementation_preflight_seen": True,
            "implementation_preflight_complete": True,
        },
        {
            "timestamp_utc": "2026-06-01T00:03:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "edit",
            "tool_name": "apply_patch",
            "changed_paths": ["src/app.py"],
        },
        {
            "timestamp_utc": "2026-06-01T00:04:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "test",
            "command_program": "python3",
            "validation_command_detected": True,
            "validation_evidence_detected": True,
            "validation_result_outcome": "pass",
        },
        {
            "timestamp_utc": "2026-06-01T00:05:00Z",
            "session_id": "sess",
            "event_name": "PostToolUse",
            "runtime": "codex",
            "turn_stage": "review",
            "review_evidence_seen": True,
            "owner_skill": "backend-change-builder",
            "reviewer_skill": "ai-code-review-refactor",
        },
        {
            "timestamp_utc": "2026-06-01T00:06:00Z",
            "session_id": "sess",
            "event_name": "Stop",
            "runtime": "codex",
            "residual_risk_detected": True,
        },
    ]


if __name__ == "__main__":
    unittest.main()
