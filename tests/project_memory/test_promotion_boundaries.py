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
from project_memory.source_evidence import sha256_file


class PromotionBoundaryTests(unittest.TestCase):
    def test_promotion_refuses_skill_routing_and_capability_targets(self) -> None:
        self.assertFalse(supported_target("SKILL.md"))
        self.assertFalse(supported_target("src/registry/routing-rules.yaml"))
        self.assertFalse(supported_target("src/registry/capabilities.yaml"))
        self.assertFalse(supported_target("docs"))
        self.assertFalse(supported_target("none"))

    def test_promotion_target_aliases_resolve_to_allowed_skeleton_dirs(self) -> None:
        self.assertTrue(supported_target("memory"))
        self.assertTrue(supported_target("hook_fixture"))
        self.assertTrue(supported_target("eval"))

    def test_promotion_writes_only_candidate_fixture_when_explicit(self) -> None:
        suggestion = {
            "id": "memory-repeat-failure-1",
            "type": "repeat_failure",
            "promotion_type": "failure_pattern",
            "promotion_target": "tests/project_memory/fixtures",
            "requires_human_review": True,
            "failure_evidence": "two failed validation attempts",
            "validation_evidence": "validation:pytest",
            "residual_risk": ["memory-derived candidate requires source validation"],
        }
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            source = tmp / "src" / "app.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("value = 1\n", encoding="utf-8")
            suggestion["source_evidence"] = {
                "repo_rel_path": "src/app.py",
                "source_hash": sha256_file(source),
                "hash_algorithm": "sha256",
                "observed_at_event_id": "memory-repeat-failure-1",
                "observed_at_timestamp": "2026-06-01T00:00:00Z",
                "graph_freshness": "current",
                "validation_freshness": "current",
            }
            output = write_candidate(tmp, suggestion, write=True)
            self.assertTrue(output.is_file())
            self.assertIn("requires_human_review", output.read_text(encoding="utf-8"))
            self.assertFalse((tmp / "src" / "registry").exists())


if __name__ == "__main__":
    unittest.main()
