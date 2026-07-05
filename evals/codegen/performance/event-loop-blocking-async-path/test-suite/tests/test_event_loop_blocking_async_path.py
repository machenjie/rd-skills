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


class EventLoopBlockingAsyncPathAssertions(unittest.TestCase):
    def test_cpu_and_blocking_io_are_offloaded_from_async_path(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)cpu.?bound|parse.*large|worker|executor|bounded pool")
        self.assertRegex(text, r"(?i)async io|non.?blocking|dedicated.*pool|isolated.*pool")
        self.assertNotRegex(text, r"(?i)readFileSync|requests\.|time\.sleep\(|fs\.readFileSync")

    def test_fanout_has_timeout_cancellation_and_backpressure(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)bounded.*fan.?out|semaphore|concurrency limit|p-limit")
        self.assertRegex(text, r"(?i)timeout")
        self.assertRegex(text, r"(?i)cancellation|abortsignal|cancelled|cancel")
        self.assertRegex(text, r"(?i)backpressure|queue limit|overload")
        self.assertNotRegex(text, r"(?i)Promise\.all\s*\(|asyncio\.gather\s*\(")

    def test_measurement_and_runtime_tests_are_present(self) -> None:
        text = joined_text()
        tests = test_text()

        self.assertRegex(text, r"(?i)event.?loop lag|runtime assessment|profil")
        self.assertRegex(tests, r"(?i)timeout")
        self.assertRegex(tests, r"(?i)cancell|abort")
        self.assertRegex(tests, r"(?i)overload|bounded|backpressure|fan.?out")


if __name__ == "__main__":
    unittest.main()
