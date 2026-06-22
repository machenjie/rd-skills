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


class ObjectMethodPlacementAssertions(unittest.TestCase):
    def test_object_method_decision_classifies_candidates(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(joined, r"(?i)Object-Method Encapsulation Decision|object candidates")
        self.assertRegex(joined, r"(?i)value object|domain object")
        self.assertRegex(joined, r"(?i)rejected alternatives|rejected object|module-local")
        self.assertRegex(joined, r"(?i)pure decision|side.?effect.?free|no side effects")

    def test_no_helper_bag_or_anemic_object_is_introduced(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertNotRegex(joined, r"(?i)class\s+\w*Helper\b")
        self.assertNotRegex(joined, r"(?i)HelperBag|helper bag")
        self.assertNotRegex(joined, r"(?i)anemic object")

    def test_payment_side_effect_stays_out_of_domain_objects(self) -> None:
        for rel, text in candidate_texts():
            normalized = rel.as_posix().casefold()
            if "order.py" not in normalized and "domain" not in normalized and "value" not in normalized:
                continue
            self.assertNotRegex(
                text,
                r"(?i)payment provider|PaymentAdapter|refund_payment|chargeback|requests\.",
                f"{rel} hides payment provider side effects inside a domain/value object",
            )

    def test_payment_side_effect_is_delegated_to_adapter_boundary(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(joined, r"(?i)payment adapter|PaymentAdapter|refund adapter|payment provider")

    def test_public_behavior_tests_cover_decision_and_adapter_paths(self) -> None:
        test_text = "\n".join(
            text for rel, text in candidate_texts() if "test" in rel.name.casefold() or "/tests/" in rel.as_posix()
        )

        for expected in ("allowed", "denied", "expired"):
            self.assertRegex(test_text, rf"(?i){expected}")
        self.assertRegex(test_text, r"(?i)refund.?hold|refund hold")
        self.assertRegex(test_text, r"(?i)payment failure|payment.*fail")
        self.assertNotRegex(test_text, r"(?m)^\s*from\s+\S+\s+import\s+_\w+")


if __name__ == "__main__":
    unittest.main()
