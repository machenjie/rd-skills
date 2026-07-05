from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker.validation_freshness import apply_freshness, fresh_after_cutoff


class ValidationFreshnessTests(unittest.TestCase):
    def test_validation_before_final_edit_is_stale(self) -> None:
        result = {
            "outcome": "pass",
            "evidence_strength": "strong",
            "negative_evidence_reason": "",
        }
        updated = apply_freshness(
            result,
            material_edit_cutoff=5,
            validation_finish=4,
        )
        self.assertFalse(updated["fresh_after_last_edit"])
        self.assertEqual(updated["evidence_strength"], "negative")
        self.assertEqual(updated["negative_evidence_reason"], "stale")

    def test_validation_after_edit_is_fresh(self) -> None:
        self.assertTrue(fresh_after_cutoff(6, 5))

    def test_missing_order_is_unknown(self) -> None:
        self.assertEqual(fresh_after_cutoff("", 5), "unknown")


if __name__ == "__main__":
    unittest.main()
