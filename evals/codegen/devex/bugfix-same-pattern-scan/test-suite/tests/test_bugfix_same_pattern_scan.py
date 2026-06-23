from __future__ import annotations

import os
import re
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
TEXT_SUFFIXES = {".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml"}


def candidate_texts() -> list[tuple[Path, str]]:
    return [
        (path.relative_to(ROOT), path.read_text(encoding="utf-8", errors="ignore"))
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    ]


def joined_text() -> str:
    return "\n".join(text for _, text in candidate_texts())


def test_text() -> str:
    return "\n".join(text for rel, text in candidate_texts() if "test" in rel.name.casefold())


class BugfixSamePatternScanAssertions(unittest.TestCase):
    def test_same_pattern_scan_record_has_scope_matches_and_decisions(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)same.?pattern scan|pattern search|inspected files")
        self.assertRegex(text, r"(?i)pattern signature|defect pattern|dereference")
        self.assertRegex(text, r"(?i)scope")
        self.assertRegex(text, r"(?i)matches")
        self.assertRegex(text, r"(?i)decision|covered|excluded|out of scope")

    def test_public_missing_profile_paths_have_regression_tests(self) -> None:
        tests = test_text()

        self.assertRegex(tests, r"(?i)missing profile|no profile|null profile|undefined profile")
        self.assertRegex(tests, r"(?i)GET /users|profileController|profile controller|public endpoint")
        self.assertRegex(tests, r"(?i)serializer|export|notification|preview|sibling")

    def test_fix_does_not_hide_authorization_or_data_quality_errors(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)authorization|permission|auth")
        self.assertRegex(text, r"(?i)data quality|absence is invalid|invalid profile|residual risk")
        self.assertNotRegex(text, r"(?i)catch\s*\([^)]*\)\s*\{[^}]*return\s+")


if __name__ == "__main__":
    unittest.main()
