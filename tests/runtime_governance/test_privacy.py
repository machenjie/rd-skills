from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import (  # noqa: E402
    cap_list,
    normalize_relative_path,
    redact_sensitive_value,
    sanitize_command_kind,
    validate_bounded_fact,
)


class PrivacyTests(unittest.TestCase):
    def test_absolute_path_is_not_saved(self) -> None:
        absolute = "/Users/example/work/repo/src/app.py"
        normalized = normalize_relative_path(absolute)
        self.assertTrue(normalized.startswith("sha256:"))
        self.assertNotIn("/Users", normalized)

    def test_absolute_path_under_base_becomes_relative(self) -> None:
        normalized = normalize_relative_path(
            "/Users/example/work/repo/src/app.py",
            base="/Users/example/work/repo",
        )
        self.assertEqual(normalized, "src/app.py")

    def test_command_arguments_are_not_saved(self) -> None:
        command = "OPENAI_API_KEY=dummy-value python3 scripts/validate-hooks.py --token value"
        self.assertEqual(sanitize_command_kind(command), "python3")

    def test_secret_like_values_are_redacted_or_rejected(self) -> None:
        self.assertEqual(redact_sensitive_value("API_TOKEN=abcd1234"), "[REDACTED]")
        self.assertFalse(validate_bounded_fact("API_TOKEN=abcd1234"))

    def test_long_paths_and_lists_are_capped(self) -> None:
        long_path = "src/" + ("verylong/" * 80) + "file.py"
        self.assertLessEqual(len(normalize_relative_path(long_path)), 300)
        capped = cap_list([f"item-{index}" for index in range(100)], max_items=3)
        self.assertEqual(capped, ["item-0", "item-1", "item-2"])


if __name__ == "__main__":
    unittest.main()
