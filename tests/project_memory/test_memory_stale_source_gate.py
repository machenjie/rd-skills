from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.privacy import sanitize_memory_event
from project_memory.retrieval.deterministic_ranker import rank_memory_events
from project_memory.source_evidence import sha256_file


class MemoryStaleSourceGateTests(unittest.TestCase):
    def test_current_source_hash_and_validation_can_be_strong_closure_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            event = _event(repo, "src/app.py", "success")
            hit = _rank_one(event, repo)
        self.assertEqual(hit["source_status"], "current")
        self.assertEqual(hit["confidence"], "strong")
        self.assertEqual(hit["evidence_role"], "closure_evidence")

    def test_changed_source_hash_downgrades_memory_to_historical_hint(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            event = _event(repo, "src/app.py", "success")
            source.write_text("value = 2\n", encoding="utf-8")
            hit = _rank_one(event, repo)
        self.assertEqual(hit["source_status"], "stale")
        self.assertEqual(hit["evidence_role"], "historical_hint")
        self.assertEqual(hit["confidence"], "weak")

    def test_legacy_event_without_source_hash_is_unknown_not_closure_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            _write(repo, "src/app.py", "value = 1\n")
            event = {
                "event_id": "legacy",
                "repo_hash": "repo",
                "kind": "validation_pattern",
                "type": "validation_result",
                "paths": ["src/app.py"],
                "bounded_paths": ["src/app.py"],
                "outcome": "success",
                "evidence_refs": ["validation:pytest"],
                "created_at": "2026-06-01T00:00:00Z",
            }
            hit = _rank_one(event, repo)
        self.assertEqual(hit["source_status"], "unknown")
        self.assertEqual(hit["evidence_role"], "historical_hint")

    def test_deleted_source_path_is_historical_hint(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            event = _event(repo, "src/app.py", "failed")
            source.unlink()
            hit = _rank_one(event, repo)
        self.assertEqual(hit["source_status"], "deleted")
        self.assertEqual(hit["evidence_role"], "historical_hint")

    def test_generated_artifact_requires_source_of_truth(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            _write(repo, "dist/app.py", "value = 1\n")
            event = _event(repo, "dist/app.py", "failed")
            hit = _rank_one(event, repo, path="dist/app.py")
        self.assertEqual(hit["source_status"], "generated")
        self.assertEqual(hit["evidence_role"], "warning_only")
        self.assertIn("source_of_truth", hit["reason"])


def _write(repo: Path, rel_path: str, body: str) -> Path:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _event(repo: Path, rel_path: str, outcome: str) -> dict:
    return sanitize_memory_event(
        {
            "repo_hash": "repo",
            "timestamp": "2026-06-01T00:00:00Z",
            "kind": "validation_pattern",
            "type": "validation_result",
            "bounded_paths": [rel_path],
            "paths": [rel_path],
            "summary": "Validated path behavior.",
            "outcome": outcome,
            "evidence_refs": ["validation:pytest", "review:rereview"],
            "source_evidence": {
                "repo_rel_path": rel_path,
                "source_hash": sha256_file(repo / rel_path),
                "hash_algorithm": "sha256",
                "observed_at_event_id": "source-event",
                "observed_at_timestamp": "2026-06-01T00:00:00Z",
                "graph_freshness": "current",
                "validation_freshness": "current",
            },
        },
        repo=repo,
    )


def _rank_one(event: dict, repo: Path, *, path: str = "src/app.py") -> dict:
    ranked = rank_memory_events(
        [event],
        {"repo_hash": "repo", "paths": [path]},
        repo_root=repo,
    )
    return ranked[0]["memory_hit"]


if __name__ == "__main__":
    unittest.main()
