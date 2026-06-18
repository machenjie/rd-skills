from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.gates.fragile_file_gate import evaluate_fragile_file_gate


class FragileFileGateTests(unittest.TestCase):
    def test_fragile_file_requires_read_test_memory_and_preflight(self) -> None:
        events = [
            {"type": "review_finding", "paths": ["src/app.py"]},
            {"type": "validation_result", "outcome": "failed", "paths": ["src/app.py"]},
        ]
        decision = evaluate_fragile_file_gate(
            events,
            paths=["src/app.py"],
            evidence={"read_file_evidence": True},
            mode="warn",
        )["fragile_file_gate"]
        self.assertTrue(decision["fragile"])
        self.assertIn("nearby_test_evidence", decision["missing"])
        self.assertIn("memory_summary_evidence", decision["missing"])
        self.assertIn("implementation_preflight", decision["missing"])
        self.assertTrue(decision["allowed_to_continue"])


if __name__ == "__main__":
    unittest.main()

