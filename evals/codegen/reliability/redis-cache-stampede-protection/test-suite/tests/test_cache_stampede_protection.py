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


class CacheStampedeProtectionAssertions(unittest.TestCase):
    def test_stampede_protection_and_ttl_jitter_are_implemented(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(joined, r"(?i)single.?flight|lock|mutex|lease")
        self.assertRegex(joined, r"(?i)jitter")
        self.assertRegex(joined, r"(?i)timeout|expires|ttl")

    def test_cache_key_preserves_correctness_dimensions(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        for dimension in ("tenant", "permission", "variant"):
            self.assertRegex(joined, rf"(?i){dimension}")
        self.assertRegex(joined, r"(?i)cache.?key|key shape")

    def test_observability_covers_hot_key_miss_storm_and_fallback(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        for signal in ("hot", "miss", "fallback", "contention"):
            self.assertRegex(joined, rf"(?i){signal}")
        self.assertRegex(joined, r"(?i)metric|counter|histogram|gauge")

    def test_redis_outage_degrades_without_external_network_dependency(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())
        test_text = "\n".join(
            text for rel, text in candidate_texts() if "test" in rel.name.casefold() or "/tests/" in rel.as_posix()
        )

        self.assertRegex(joined, r"(?i)redis.*down|redis.*unavailable|outage|degrad")
        self.assertRegex(test_text, r"(?i)redis.*down|redis.*unavailable|outage|fallback")
        self.assertNotRegex(joined, r"(?i)socket\.create_connection|requests\.|http://|https://")


if __name__ == "__main__":
    unittest.main()
