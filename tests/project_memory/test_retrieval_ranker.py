from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.retrieval.deterministic_ranker import rank_memory_events


class RetrievalRankerTests(unittest.TestCase):
    def test_ranker_prefers_exact_path_symbol_task_and_promotion(self) -> None:
        events = [
            _event("old", ["src/other.py"], ["Other"], "task", "raw", "2026-01-01T00:00:00Z"),
            _event("best", ["src/app.py"], ["OrderService"], "task", "approved", "2026-06-01T00:00:00Z"),
            _event("path", ["src/app.py"], [], "other", "raw", "2026-06-01T00:00:00Z"),
        ]
        ranked = rank_memory_events(
            events,
            {
                "repo_hash": "repo",
                "paths": ["src/app.py"],
                "symbols": ["OrderService"],
                "task_fingerprint": "task",
                "owner_skill": "backend-change-builder",
            },
            now=datetime(2026, 6, 2, tzinfo=timezone.utc),
        )
        self.assertEqual(ranked[0]["event_id"], "best")
        self.assertGreater(ranked[0]["retrieval_score"], ranked[1]["retrieval_score"])


def _event(
    event_id: str,
    paths: list[str],
    symbols: list[str],
    task: str,
    promotion: str,
    created_at: str,
) -> dict:
    return {
        "event_id": event_id,
        "repo_hash": "repo",
        "task_fingerprint": task,
        "type": "implementation_attempt",
        "paths": paths,
        "symbols": symbols,
        "owner_skill": "backend-change-builder",
        "reviewer_skill": "",
        "outcome": "failed",
        "promotion_status": promotion,
        "created_at": created_at,
    }


if __name__ == "__main__":
    unittest.main()

