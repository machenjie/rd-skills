from __future__ import annotations

import os
import re
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
TEXT_SUFFIXES = {".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".go", ".java"}


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


class LockHeldAcrossIoAssertions(unittest.TestCase):
    def test_lock_invariant_and_io_boundary_are_explicit(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)invariant")
        self.assertRegex(text, r"(?i)critical section|lock scope|mutex scope|synchronized")
        self.assertRegex(text, r"(?i)(release|unlock).*before.*(io|repository|network|notify)|io.*outside.*lock")

    def test_timeout_deadlock_and_contention_are_analyzed(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)timeout")
        self.assertRegex(text, r"(?i)deadlock")
        self.assertRegex(text, r"(?i)contention|race|stress")
        self.assertRegex(text, r"(?i)outbox|optimistic|transaction|queue|after commit|post-commit")

    def test_concurrent_evidence_is_not_serial_only(self) -> None:
        tests = test_text()

        self.assertRegex(tests, r"(?i)concurrent|parallel|goroutine|thread|race|stress|contention")
        self.assertRegex(tests, r"(?i)timeout|deadlock")
        self.assertNotRegex(tests, r"(?i)serial only|single threaded only")


if __name__ == "__main__":
    unittest.main()
