from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.gates.stale_context_gate import evaluate_stale_context_gate


class StaleContextGateTests(unittest.TestCase):
    def test_stale_context_cannot_be_used_as_fact(self) -> None:
        decision = evaluate_stale_context_gate(
            {"freshness_markers": {"indexed_at": "2026-06-01T00:00:00Z"}},
            changed_files=[{"path": "src/app.py", "changed_at": "2026-06-02T00:00:00Z"}],
            drift_triggers=["route-manifest-changed"],
        )["stale_context_gate"]
        self.assertTrue(decision["stale"])
        self.assertFalse(decision["allowed_as_fact"])
        self.assertEqual(decision["required_action"], "refresh_repository_graph_or_mark_stale_assumption")


if __name__ == "__main__":
    unittest.main()

