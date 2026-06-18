from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.store.projection import build_memory_summary


class ProjectionTests(unittest.TestCase):
    def test_projection_aggregates_failures_fragile_files_and_commands(self) -> None:
        events = [
            _event("e1", "validation_result", "failed", ["src/app.py"]),
            _event("e2", "review_finding", "unknown", ["src/app.py"], refs=["finding:null"]),
            _event("e3", "repair_attempt", "blocked", ["src/app.py"]),
            _event("e4", "validated_command", "success", ["src/app.py"], refs=["cmd:pytest"]),
            _event("e5", "review_finding", "unknown", ["src/app.py"], refs=["finding:null"]),
        ]
        summary = build_memory_summary(events, {"repo_hash": "repo", "paths": ["src/app.py"]})
        body = summary["project_memory_summary"]
        self.assertEqual(len(body["prior_failures"]), 2)
        self.assertEqual(body["fragile_files"][0]["path"], "src/app.py")
        self.assertEqual(body["validated_commands"][0]["event_id"], "e4")
        self.assertEqual(body["repeated_review_findings"][0]["finding_key"], "finding:null")


def _event(event_id: str, kind: str, outcome: str, paths: list[str], refs: list[str] | None = None) -> dict:
    return {
        "schema_version": 1,
        "event_id": event_id,
        "repo_hash": "repo",
        "task_fingerprint": "task",
        "type": kind,
        "paths": paths,
        "symbols": ["OrderService"],
        "owner_skill": "backend-change-builder",
        "reviewer_skill": "quality-test-gate",
        "route_manifest_hash": "route",
        "outcome": outcome,
        "evidence_refs": refs or [],
        "confidence": "high",
        "promotion_status": "raw",
        "created_at": f"2026-06-0{event_id[-1]}T00:00:00Z",
    }


if __name__ == "__main__":
    unittest.main()

