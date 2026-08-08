from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def load_subject():
    path = ROOT / "profile_paths.py"
    spec = importlib.util.spec_from_file_location("candidate_profile_paths", path)
    if spec is None or spec.loader is None:
        raise AssertionError("profile_paths.py is required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BugfixSamePatternScanAssertions(unittest.TestCase):
    def test_reported_and_sibling_public_paths_handle_missing_profile(self) -> None:
        subject = load_subject()
        user = {"id": "u-1", "profile": None}
        self.assertEqual(subject.public_profile(user, authorized=True), {"display_name": None})
        self.assertEqual(subject.notification_preview(user), "Welcome")

    def test_authorization_and_strict_data_quality_boundaries_remain_distinct(self) -> None:
        subject = load_subject()
        with self.assertRaises(PermissionError):
            subject.public_profile({"profile": None}, authorized=False)
        with self.assertRaises(ValueError):
            subject.strict_export({"profile": None})
        self.assertEqual(subject.strict_export({"profile": {"name": "Ada"}}), "Ada")

    def test_scan_record_is_structured_and_accounts_for_every_match(self) -> None:
        record = json.loads((ROOT / "same_pattern_scan.json").read_text(encoding="utf-8"))
        self.assertEqual(record["scope"], ["profile_paths.py"])
        self.assertEqual(
            set(record["matches"]),
            {"public_profile", "notification_preview", "strict_export"},
        )
        self.assertIn("dereference", record["pattern_signature"])
        by_symbol = record["finding_relations"]
        self.assertEqual(by_symbol["public_profile"]["relation"], "current-task")
        self.assertEqual(by_symbol["public_profile"]["action"], "fixed")
        self.assertEqual(by_symbol["notification_preview"]["relation"], "current-task")
        self.assertEqual(by_symbol["notification_preview"]["action"], "fixed")
        self.assertEqual(by_symbol["strict_export"]["relation"], "adjacent")
        self.assertEqual(by_symbol["strict_export"]["action"], "record-do-not-edit")
        self.assertIn("data quality", by_symbol["strict_export"]["rationale"])
        self.assertTrue(by_symbol["strict_export"]["residual_risk"])


if __name__ == "__main__":
    unittest.main()
