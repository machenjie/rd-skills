from __future__ import annotations

import os
import re
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
TEXT_SUFFIXES = {".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".json"}


def candidate_texts() -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = []
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            items.append((path.relative_to(ROOT), path.read_text(encoding="utf-8", errors="ignore")))
    return items


class HelperReuseSearchAssertions(unittest.TestCase):
    def test_reuse_search_names_existing_formatter_candidates(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(joined, r"(?i)reuse search|searched files|inspected files|reuse candidates")
        self.assertRegex(joined, r"(?i)orderFormatter|order formatter")
        self.assertRegex(joined, r"(?i)customerFormatter|customer formatter")

    def test_order_display_logic_stays_out_of_shared_utils(self) -> None:
        for rel, text in candidate_texts():
            normalized = rel.as_posix().casefold()
            if "/shared/" not in normalized and "/common/" not in normalized and "/utils/" not in normalized:
                continue
            self.assertNotRegex(
                text,
                r"(?i)\b(formatOrderDisplayName|order display|archived order|customer display)\b",
                f"{rel} contains order display business logic in a shared utility boundary",
            )

    def test_public_order_display_cases_are_covered(self) -> None:
        test_text = "\n".join(
            text for rel, text in candidate_texts() if "__tests__" in rel.as_posix() or "test" in rel.name.casefold()
        )

        self.assertRegex(test_text, r"(?i)display.?name|display name")
        self.assertRegex(test_text, r"(?i)\bnormal\b|standard|active")
        self.assertRegex(test_text, r"(?i)missing.?customer|unknown.?customer|no customer")
        self.assertRegex(test_text, r"(?i)archived")
        self.assertNotRegex(test_text, r"(?i)formatOrderDisplayName\(")

    def test_order_display_helper_is_not_duplicated(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())
        helper_defs = re.findall(
            r"(?i)(?:function\s+formatOrderDisplayName|const\s+formatOrderDisplayName\s*=|"
            r"def\s+format_order_display_name|def\s+formatOrderDisplayName)",
            joined,
        )

        self.assertLessEqual(len(helper_defs), 1)

    def test_execution_evidence_and_structure_plan_are_recorded(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(joined, r"(?i)Execution Discipline|evidence inventory|validation command")
        self.assertRegex(joined, r"(?i)Implementation Structure|Structure Plan|placement rationale")


if __name__ == "__main__":
    unittest.main()
