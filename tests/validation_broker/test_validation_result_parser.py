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

    def test_zero_errors_is_pass_not_fail(self) -> None:
        result = parse_validation_result("Ran python3 scripts/validate-hooks.py: 0 errors.")
        self.assertEqual(result["outcome"], "pass")
        self.assertEqual(result["evidence_strength"], "strong")

    def test_zero_failures_and_zero_errors_is_pass_not_fail(self) -> None:
        result = parse_validation_result(
            "Ran python3 scripts/validate-hooks.py: 0 failures, 0 errors."
        )
        self.assertEqual(result["outcome"], "pass")

    def test_zero_tests_failed_is_pass_not_fail(self) -> None:
        result = parse_validation_result(
            "Ran python3 scripts/validate-hooks.py: 0 tests failed."
        )
        self.assertEqual(result["outcome"], "pass")

    def test_mixed_zero_errors_and_nonzero_failure_is_fail(self) -> None:
        result = parse_validation_result(
            "Ran python3 scripts/validate-hooks.py: 0 errors, 1 failure."
        )
        self.assertEqual(result["outcome"], "fail")

    def test_mixed_no_errors_and_failed_count_is_fail(self) -> None:
        result = parse_validation_result(
            "Ran python3 scripts/validate-hooks.py: no errors, 1 failed."
        )
        self.assertEqual(result["outcome"], "fail")

    def test_mixed_zero_failures_and_nonzero_error_is_fail(self) -> None:
        result = parse_validation_result(
            "Ran python3 scripts/validate-hooks.py: 0 failures, 1 error."
        )
        self.assertEqual(result["outcome"], "fail")

    def test_no_errors_without_command_is_not_fail(self) -> None:
        result = parse_validation_result("No errors.")
        self.assertNotEqual(result["outcome"], "fail")
        self.assertEqual(result["evidence_strength"], "weak")

    def test_nonzero_error_count_is_fail(self) -> None:
        result = parse_validation_result("Ran python3 scripts/validate-hooks.py: 1 error.")
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["evidence_strength"], "negative")

    def test_nonzero_exit_code_is_fail(self) -> None:
        result = parse_validation_result("Ran python3 scripts/validate-hooks.py, exit code 1.")
        self.assertEqual(result["outcome"], "fail")

    def test_negative_chinese_disclosure_is_negative(self) -> None:
        result = parse_validation_result("未验证，因为无法运行。")
        self.assertEqual(result["outcome"], "not_run")
        self.assertEqual(result["evidence_strength"], "negative")
        self.assertEqual(result["negative_evidence_reason"], "unable_to_run")


if __name__ == "__main__":
    unittest.main()
