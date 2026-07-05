from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.review.promote_memory_candidate import (
    validate_promotion_candidate,
    write_candidate,
)
from project_memory.source_evidence import sha256_file


class MemoryPromotionEvidenceTests(unittest.TestCase):
    def test_missing_promotion_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            suggestion = _suggestion(source)
            suggestion.pop("promotion_type")
            with self.assertRaises(ValueError):
                write_candidate(repo, suggestion, write=False)

    def test_stale_source_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            suggestion = _suggestion(source)
            source.write_text("value = 2\n", encoding="utf-8")
            result = validate_promotion_candidate(repo, suggestion)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["source_status"], "stale")

    def test_current_failure_pattern_with_validation_and_residual_risk_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            result = validate_promotion_candidate(repo, _suggestion(source))
        self.assertTrue(result["allowed"], result["reasons"])
        self.assertEqual(result["source_status"], "current")
        self.assertEqual(result["confidence"], "strong")


def _write(repo: Path, rel_path: str, body: str) -> Path:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _suggestion(source: Path) -> dict:
    return {
        "id": "memory-failure-pattern-1",
        "type": "repeat_failure",
        "promotion_type": "failure_pattern",
        "promotion_target": "tests/project_memory/fixtures",
        "requires_human_review": True,
        "failure_evidence": "two failed validation attempts",
        "validation_evidence": "validation:pytest tests/project_memory",
        "residual_risk": ["candidate requires maintainer review before source promotion"],
        "source_evidence": {
            "repo_rel_path": "src/app.py",
            "source_hash": sha256_file(source),
            "hash_algorithm": "sha256",
            "observed_at_event_id": "memory-failure-pattern-1",
            "observed_at_timestamp": "2026-06-01T00:00:00Z",
            "graph_freshness": "current",
            "validation_freshness": "current",
        },
    }


if __name__ == "__main__":
    unittest.main()
