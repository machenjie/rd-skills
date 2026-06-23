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


class BackwardCompatibleApiFieldAssertions(unittest.TestCase):
    def test_preferred_contact_method_is_additive_nullable_and_validated(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"\bpreferred_contact_method\b")
        for existing_field in ("name", "email", "phone", "marketing"):
            self.assertRegex(text, rf"(?i)\b{existing_field}\b")
        self.assertRegex(text, r"(?i)null|nullable|optional")
        for value in ("email", "phone", "sms"):
            self.assertRegex(text, rf"(?i)\b{value}\b")
        self.assertRegex(text, r"(?i)invalid|allowed values|enum|validation")

    def test_contract_tests_cover_old_and_new_clients(self) -> None:
        tests = test_text()

        self.assertRegex(tests, r"(?i)old client|legacy client|omit|omitted|without preferred")
        self.assertRegex(tests, r"(?i)ignore|extra field|backward compatible|compatible")
        self.assertRegex(tests, r"(?i)preferred_contact_method")
        self.assertRegex(tests, r"(?i)invalid|reject|400|validation")

    def test_docs_and_migration_note_are_present(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)openapi|schema|api documentation|docs")
        self.assertRegex(text, r"(?i)migration|existing profiles|existing customers|data default|backfill")
        self.assertNotRegex(text, r"(?i)remove.*marketing|rename.*marketing")


if __name__ == "__main__":
    unittest.main()
