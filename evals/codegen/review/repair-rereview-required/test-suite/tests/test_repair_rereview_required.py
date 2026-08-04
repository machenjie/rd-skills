from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def load_subject():
    path = ROOT / "calculator.py"
    spec = importlib.util.spec_from_file_location("candidate_calculator", path)
    if spec is None or spec.loader is None:
        raise AssertionError("calculator.py is required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepairRereviewAssertions(unittest.TestCase):
    def test_repair_preserves_every_cent_and_rejects_invalid_partition_count(self) -> None:
        allocate = load_subject().allocate
        self.assertEqual(allocate(10.00, 3), [3.34, 3.33, 3.33])
        self.assertEqual(allocate(0.05, 2), [0.03, 0.02])
        self.assertEqual(round(sum(allocate(123.45, 7)), 2), 123.45)
        with self.assertRaises(ValueError):
            allocate(10.00, 0)

    def test_repair_and_rereview_are_linked_to_the_same_finding(self) -> None:
        evidence = json.loads((ROOT / "repair_evidence.json").read_text(encoding="utf-8"))
        finding_id = evidence["review_finding"]["id"]
        self.assertEqual(evidence["repair"]["finding_id"], finding_id)
        self.assertEqual(evidence["re_review"]["finding_id"], finding_id)
        self.assertEqual(evidence["re_review"]["status"], "passed")
        self.assertEqual(evidence["validation_evidence"]["status"], "passed")
        self.assertEqual(
            set(evidence["changed_files"]), {"calculator.py", "repair_evidence.json"}
        )
        for field in ("final_diff", "plan_vs_actual", "residual_risk"):
            self.assertTrue(evidence[field].strip())


if __name__ == "__main__":
    unittest.main()
