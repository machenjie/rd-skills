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


class KafkaConsumerOffsetDlqAssertions(unittest.TestCase):
    def test_manual_commit_after_durable_side_effect_and_idempotency(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)manual.*commit|commit.*offset|enable\.auto\.commit.*false")
        self.assertRegex(text, r"(?i)durable.*(write|side effect)|side effect.*succeed")
        self.assertRegex(text, r"(?i)idempotent|deduplicat|processed message|message id")
        self.assertNotRegex(text, r"(?i)enable\.auto\.commit\s*[:=]\s*true")

    def test_bounded_retry_dlq_and_replay_metadata_are_present(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)bounded.*retr|retry.*limit|max.*attempt")
        self.assertRegex(text, r"(?i)\bdlq\b|dead.?letter")
        for field in ("topic", "partition", "offset", "key", "error", "replay"):
            self.assertRegex(text, rf"(?i)\b{field}\b")

    def test_local_tests_cover_duplicate_poison_and_lag_without_external_kafka(self) -> None:
        text = joined_text()
        tests = test_text()

        self.assertRegex(tests, r"(?i)duplicate|idempotent")
        self.assertRegex(tests, r"(?i)poison|dlq|dead.?letter")
        self.assertRegex(text, r"(?i)consumer lag|lag alert|dlq depth|depth alert")
        self.assertNotRegex(text, r"(?i)socket\.create_connection|bootstrap\.servers\s*[:=]\s*[A-Za-z0-9_.-]+:\d+")


if __name__ == "__main__":
    unittest.main()
