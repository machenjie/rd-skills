from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory
from trajectory.trajectory_promotions import promotion_skeletons

from tests.trajectory.test_trajectory_builder import complete_records


class TrajectoryCandidateGenerationTests(unittest.TestCase):
    def test_report_candidate_fixtures_are_human_review_only(self) -> None:
        records = complete_records()
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:30Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "edit",
                "tool_name": "apply_patch",
                "changed_paths": ["src/app.py"],
            },
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        candidates = report["candidate_fixtures"]
        self.assertEqual(
            {candidate["type"] for candidate in candidates},
            {
                "pressure_scenario",
                "agent_behavior_sample",
                "hook_fixture",
                "validation_broker_fixture",
                "trajectory_fixture",
            },
        )
        self.assertTrue(all(candidate["generated_from_telemetry"] for candidate in candidates))
        self.assertTrue(all(candidate["requires_human_review"] for candidate in candidates))
        self.assertTrue(all(candidate["source_suggestion_id"] for candidate in candidates))

    def test_skeleton_json_candidates_keep_candidate_headers(self) -> None:
        trajectory = build_trajectory(complete_records(), repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = {
            "issues": [
                {
                    "type": "edit_before_read",
                    "severity": "high",
                    "step_index": 1,
                    "message": "x",
                    "recommended_gate": "repository-context-map",
                }
            ]
        }
        skeletons = promotion_skeletons(trajectory, report)
        json_skeletons = [skeleton for skeleton in skeletons if str(skeleton["path"]).endswith(".json")]
        self.assertEqual(len(json_skeletons), 3)
        for skeleton in json_skeletons:
            payload = json.loads(str(skeleton["content"]))
            self.assertTrue(payload["generated_from_telemetry"])
            self.assertTrue(payload["requires_human_review"])
            self.assertTrue(payload["source_suggestion_id"])


if __name__ == "__main__":
    unittest.main()
