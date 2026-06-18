from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory
from trajectory.trajectory_promotions import promotion_skeletons, write_skeletons

from tests.trajectory.test_trajectory_builder import complete_records


class TrajectoryPromotionTests(unittest.TestCase):
    def test_high_severity_generates_human_review_skeletons(self) -> None:
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
        skeletons = promotion_skeletons(trajectory, report)
        self.assertEqual(len(skeletons), 5)
        self.assertTrue(all(skeleton["requires_human_review"] for skeleton in skeletons))
        self.assertTrue(all("generated_from_telemetry" in str(skeleton["content"]) for skeleton in skeletons))
        self.assertTrue(all("source_suggestion_id" in str(skeleton["content"]) for skeleton in skeletons))
        self.assertTrue(
            all(
                str(skeleton["path"]).startswith(
                    (
                        "evals/pressure",
                        "evals/agent-behavior",
                        "tests/fixtures/hooks",
                        "tests/fixtures/validation_broker",
                        "tests/fixtures/trajectory",
                    )
                )
                for skeleton in skeletons
            )
        )

    def test_write_skeletons_is_explicit_and_bounded(self) -> None:
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
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            paths = write_skeletons(tmp, skeletons, write=False)
            self.assertFalse(any(path.exists() for path in paths))
            paths = write_skeletons(tmp, skeletons, write=True)
            self.assertTrue(all(path.exists() for path in paths))
            self.assertFalse((tmp / "src").exists())

    def test_write_skeletons_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            with self.assertRaises(ValueError):
                write_skeletons(
                    Path(tmp_s),
                    [
                        {
                            "path": "evals/pressure/../../src/registry/routing-rules.yaml",
                            "content": "x",
                        }
                    ],
                    write=True,
                )


if __name__ == "__main__":
    unittest.main()
