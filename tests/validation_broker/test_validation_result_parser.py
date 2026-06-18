from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker.validation_result_parser import parse_validation_result


class ValidationResultParserTests(unittest.TestCase):
    def test_command_with_outcome_is_strong(self) -> None:
        result = parse_validation_result("Ran python3 scripts/validate-hooks.py, passed, exit 0.")
        self.assertEqual(result["outcome"], "pass")
        self.assertEqual(result["evidence_strength"], "strong")

    def test_command_without_outcome_is_weak(self) -> None:
        result = parse_validation_result("Ran python3 scripts/validate-hooks.py.")
        self.assertEqual(result["outcome"], "unknown")
        self.assertEqual(result["evidence_strength"], "weak")

    def test_negative_chinese_disclosure_is_negative(self) -> None:
        result = parse_validation_result("未验证，因为无法运行。")
        self.assertEqual(result["outcome"], "not_run")
        self.assertEqual(result["evidence_strength"], "negative")
        self.assertEqual(result["negative_evidence_reason"], "unable_to_run")


if __name__ == "__main__":
    unittest.main()
