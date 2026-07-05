from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-report-consistency.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_report_consistency_test", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TimestampOnlyReportDiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()

    def test_json_timestamp_only_diff_fails(self) -> None:
        diff = """diff --git a/reports/example.json b/reports/example.json
--- a/reports/example.json
+++ b/reports/example.json
@@ -1,3 +1,3 @@
-  "generated_at": "2026-01-01T00:00:00Z",
+  "generated_at": "2026-01-02T00:00:00Z",
"""
        self.assertEqual(
            self.module.timestamp_only_report_diff_errors(diff),
            ["reports/example.json has timestamp-only report diff"],
        )

    def test_markdown_timestamp_only_diff_fails(self) -> None:
        diff = """diff --git a/reports/example.md b/reports/example.md
--- a/reports/example.md
+++ b/reports/example.md
@@ -1,3 +1,3 @@
-- Generated: 2026-01-01T00:00:00Z
+- Generated: 2026-01-02T00:00:00Z
"""
        self.assertEqual(
            self.module.timestamp_only_report_diff_errors(diff),
            ["reports/example.md has timestamp-only report diff"],
        )

    def test_substantive_report_diff_is_allowed(self) -> None:
        diff = """diff --git a/reports/example.json b/reports/example.json
--- a/reports/example.json
+++ b/reports/example.json
@@ -1,4 +1,4 @@
-  "generated_at": "2026-01-01T00:00:00Z",
+  "generated_at": "2026-01-02T00:00:00Z",
-  "status": "fail"
+  "status": "pass"
"""
        self.assertEqual(self.module.timestamp_only_report_diff_errors(diff), [])


if __name__ == "__main__":
    unittest.main()
