from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.review.promote_memory_candidate import supported_target, write_candidate


class PromotionBoundaryTests(unittest.TestCase):
    def test_promotion_refuses_skill_routing_and_capability_targets(self) -> None:
        self.assertFalse(supported_target("SKILL.md"))
        self.assertFalse(supported_target("src/registry/routing-rules.yaml"))
        self.assertFalse(supported_target("src/registry/capabilities.yaml"))

    def test_promotion_writes_only_candidate_fixture_when_explicit(self) -> None:
        suggestion = {
            "id": "memory-repeat-failure-1",
            "type": "repeat_failure",
            "promotion_target": "tests/project_memory/fixtures",
        }
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            output = write_candidate(tmp, suggestion, write=True)
            self.assertTrue(output.is_file())
            self.assertIn("requires_human_review", output.read_text(encoding="utf-8"))
            self.assertFalse((tmp / "src" / "registry").exists())


if __name__ == "__main__":
    unittest.main()

