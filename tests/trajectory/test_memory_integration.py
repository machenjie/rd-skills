from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory


class TrajectoryMemoryIntegrationTests(unittest.TestCase):
    def test_memory_event_uses_kind_and_bounded_paths(self) -> None:
        trajectory = build_trajectory(
            [],
            repo_hash="repo",
            session_id="sess",
            memory_events=[
                {
                    "timestamp": "2026-06-01T00:00:00Z",
                    "repo_hash": "repo",
                    "session_id": "sess",
                    "kind": "fragile_file",
                    "type": "fragile_file",
                    "bounded_paths": ["src/app.py"],
                    "outcome": "unknown",
                }
            ],
        )
        self.assertIsNotNone(trajectory)
        assert trajectory is not None
        step = trajectory["steps"][0]
        self.assertEqual(step["paths"], ["src/app.py"])
        self.assertIn("fragile-file", step["risk_surfaces"])
        self.assertEqual(step["facts"]["memory_event_kind"], "fragile_file")

    def test_stale_project_memory_context_is_reported(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "Stop",
                    "runtime": "codex",
                    "project_memory_available": True,
                    "project_memory_projection_key": "projection",
                    "project_memory_stale_context_gate": "warn",
                    "project_memory_residual_risk": ["stale_context_gate:warn"],
                    "residual_risk_detected": True,
                }
            ],
            repo_hash="repo",
            session_id="sess",
        )
        self.assertIsNotNone(trajectory)
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("stale_context_memory", report["issue_counts"])
        self.assertEqual(report["closure_status"], "warn")


if __name__ == "__main__":
    unittest.main()
