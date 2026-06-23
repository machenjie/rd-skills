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


class WebhookHmacRawBodyAssertions(unittest.TestCase):
    def test_signature_verifies_raw_body_with_constant_time_compare(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)raw (body|bytes)|body bytes|request\.body")
        self.assertRegex(text, r"(?i)hmac|sha256|signature")
        self.assertRegex(text, r"(?i)compare_digest|timingSafeEqual|constant.?time")
        self.assertRegex(text, r"(?i)before parsing|before json|verify.*before")

    def test_fail_closed_rotation_and_side_effect_order_are_covered(self) -> None:
        text = joined_text()
        tests = test_text()

        self.assertRegex(text, r"(?i)active.*secret|previous.*secret|secret rotation|rotat")
        self.assertRegex(text, r"(?i)missing.*(secret|header)|fail closed|unsigned")
        self.assertRegex(text, r"(?i)before.*side effect|before.*idempotenc|no side effect")
        self.assertRegex(tests, r"(?i)whitespace|tamper|raw byte|raw body")
        self.assertRegex(tests, r"(?i)missing.*(secret|header)|unsigned|fail closed")

    def test_secret_material_is_not_logged_or_networked(self) -> None:
        text = joined_text()

        self.assertRegex(text, r"(?i)log.*(reason|event id)|rejection reason")
        self.assertNotRegex(text, r"(?i)webhook[_-]?secret\s*[:=]\s*[A-Za-z0-9_./+=-]{12,}")
        self.assertNotRegex(text, r"(?i)requests\.|socket\.create_connection|http://|https://")


if __name__ == "__main__":
    unittest.main()
