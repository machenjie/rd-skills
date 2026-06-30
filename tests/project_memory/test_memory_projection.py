from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.privacy import sanitize_memory_event
from project_memory.source_evidence import sha256_file
from project_memory.store.projection import build_memory_projection


class MemoryProjectionTests(unittest.TestCase):
    def test_projection_includes_relevant_events_and_excludes_mismatches(self) -> None:
        events = [
            sanitize_memory_event(
                {
                    "repo_hash": "repo",
                    "timestamp": "2026-06-05T10:00:00Z",
                    "kind": "fragile_file",
                    "bounded_paths": ["src/app.py"],
                    "summary": "Fragile edit pattern.",
                    "source": "validator",
                }
            ),
            sanitize_memory_event(
                {
                    "repo_hash": "other",
                    "timestamp": "2026-06-05T10:00:00Z",
                    "kind": "repeat_failure",
                    "bounded_paths": ["src/app.py"],
                    "summary": "Other repository event.",
                }
            ),
        ]
        query = {
            "repo_hash": "repo",
            "paths": ["src/app.py"],
            "graph_freshness": "current",
        }
        projection = build_memory_projection(events, query)["project_memory_projection"]
        self.assertTrue(projection["source_check_required"])
        self.assertEqual(len(projection["included_events"]), 1)
        self.assertEqual(projection["included_events"][0]["kind"], "fragile_file")
        self.assertEqual(projection["excluded_events"][0]["reason"], "repo_hash_mismatch")

    def test_projection_marks_memory_stale_against_changed_file_time(self) -> None:
        event = sanitize_memory_event(
            {
                "repo_hash": "repo",
                "timestamp": "2026-06-05T10:00:00Z",
                "kind": "validation_pattern",
                "bounded_paths": ["src/app.py"],
                "summary": "Previous validator mapping.",
            }
        )
        query = {
            "repo_hash": "repo",
            "paths": ["src/app.py"],
            "graph_freshness": "current",
            "changed_files": [{"path": "src/app.py", "changed_at": "2026-06-05T12:00:00Z"}],
        }
        projection = build_memory_projection([event], query)["project_memory_projection"]
        self.assertEqual(projection["stale_context_gate"], "warn")
        self.assertTrue(projection["included_events"][0]["stale_relative_to_source"])
        self.assertIn(f"stale_memory_event:{event['event_id']}", projection["residual_risk"])

    def test_projection_groups_business_memory_verdicts(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = repo / "src/order.py"
            source.parent.mkdir(parents=True)
            source.write_text("def can_cancel(order):\n    return order.status == 'draft'\n", encoding="utf-8")
            accepted = sanitize_memory_event(
                {
                    "repo_hash": "repo",
                    "timestamp": "2026-06-05T10:00:00Z",
                    "kind": "business_rule_changed",
                    "bounded_paths": ["src/order.py"],
                    "summary": "Cancellation rule changed.",
                    "promotion_status": "approved",
                    "source_evidence": {
                        "repo_rel_path": "src/order.py",
                        "source_hash": sha256_file(source),
                        "hash_algorithm": "sha256",
                        "observed_at_event_id": "business-source",
                        "observed_at_timestamp": "2026-06-05T10:00:00Z",
                        "graph_freshness": "current",
                        "validation_freshness": "current",
                    },
                },
                repo=repo,
            )
            rejected = sanitize_memory_event(
                {
                    "repo_hash": "repo",
                    "timestamp": "2026-06-05T10:00:00Z",
                    "kind": "business_rule_rejected",
                    "bounded_paths": ["src/order.py"],
                    "summary": "Rejected old cancellation rule.",
                },
                repo=repo,
            )
            stale = sanitize_memory_event(
                {
                    "repo_hash": "repo",
                    "timestamp": "2026-06-05T10:00:00Z",
                    "kind": "stale_business_context",
                    "bounded_paths": ["src/order.py"],
                    "summary": "Prior owner decision may be stale.",
                },
                repo=repo,
            )
            projection = build_memory_projection(
                [accepted, rejected, stale],
                {"repo_hash": "repo", "paths": ["src/order.py"], "graph_freshness": "current"},
                repo_root=repo,
            )["project_memory_projection"]
        business_memory = projection["summary"]["business_memory"]
        self.assertEqual([item["event_id"] for item in business_memory["accepted"]], [accepted["event_id"]])
        self.assertEqual([item["event_id"] for item in business_memory["rejected"]], [rejected["event_id"]])
        self.assertEqual([item["event_id"] for item in business_memory["stale"]], [stale["event_id"]])


if __name__ == "__main__":
    unittest.main()
