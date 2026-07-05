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


class ServiceMethodPlacementAssertions(unittest.TestCase):
    def test_cancellation_flow_reuses_order_service_and_policy(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertIn("OrderService", joined)
        self.assertIn("cancelOrder", joined)
        self.assertIn("OrderPolicy", joined)
        self.assertRegex(joined, r"canCancelBeforeDeadline|cancellation deadline|cancel.*deadline")

    def test_order_service_exposes_public_cancel_order_method(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(
            joined,
            r"(?s)(class\s+OrderService\b|export\s+class\s+OrderService\b).{0,2500}"
            r"(?:public\s+)?(?:async\s+)?cancelOrder\s*\(",
        )

    def test_no_order_business_rule_is_added_to_shared_utils(self) -> None:
        for rel, text in candidate_texts():
            normalized = rel.as_posix().casefold()
            if "/shared/" not in normalized and "/common/" not in normalized and "/utils/" not in normalized:
                continue
            self.assertNotRegex(
                text,
                r"(?i)\b(validateCancellationDeadline|OrderPolicy|cancelOrder|order cancellation)\b",
                f"{rel} contains order cancellation business logic outside order ownership",
            )

    def test_deadline_boundary_tests_are_present_on_public_behavior(self) -> None:
        test_text = "\n".join(
            text for rel, text in candidate_texts() if "__tests__" in rel.as_posix() or "test" in rel.name.casefold()
        )

        self.assertRegex(test_text, r"(?i)\bbefore\b")
        self.assertRegex(test_text, r"(?i)\b(at|exact)\b")
        self.assertRegex(test_text, r"(?i)\bafter\b")
        self.assertRegex(test_text, r"(?i)cancelOrder|cancel order|cancellation")
        self.assertNotRegex(test_text, r"(?i)validateCancellationDeadline\(")

    def test_structure_rationale_rejects_detached_helper(self) -> None:
        joined = "\n".join(text for _, text in candidate_texts())

        self.assertRegex(joined, r"(?i)Implementation Structure|Structure Plan|placement rationale")
        self.assertRegex(joined, r"(?i)shared util|shared/utils|detached helper|new helper")


if __name__ == "__main__":
    unittest.main()
