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
    return "\n".join(
        text for rel, text in candidate_texts() if "__tests__" in rel.as_posix() or "test" in rel.name.casefold()
    )


class AccessibleFormErrorStateAssertions(unittest.TestCase):
    def test_field_errors_are_programmatically_associated_and_announced(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)aria-invalid")
        self.assertRegex(text, r"(?i)aria-describedby|aria-errormessage")
        self.assertRegex(text, r"(?i)aria-live|role=[\"']alert|focus\(")

    def test_validation_server_mapping_and_accessibility_are_covered(self) -> None:
        tests = test_text()

        for signal in ("required", "email", "confirm", "match"):
            self.assertRegex(tests, rf"(?i){signal}")
        self.assertRegex(tests, r"(?i)server.*(error|reject)|api.*(error|reject)")
        self.assertRegex(tests, r"(?i)accessible name|aria|screen reader|description")

    def test_failed_submit_preserves_values_and_documents_state_matrix(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)preserve|keep.*values|does not clear|not erase")
        for state in ("empty", "invalid", "submitting", "success", "disabled", "retry"):
            self.assertRegex(text, rf"(?i){state}")


if __name__ == "__main__":
    unittest.main()
