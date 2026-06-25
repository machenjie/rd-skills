from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.gates.fragile_file_gate import evaluate_fragile_file_gate
from project_memory.privacy import sanitize_memory_event
from project_memory.source_evidence import sha256_file


class FragileFileGateSourceFreshnessTests(unittest.TestCase):
    def test_current_strong_fragile_memory_can_block_when_preflight_evidence_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            _write(repo, "src/app.py", "value = 1\n")
            events = [_event(repo, "fragile-1"), _event(repo, "fragile-2")]
            decision = evaluate_fragile_file_gate(
                events,
                paths=["src/app.py"],
                evidence={},
                mode="block",
                repo_root=repo,
            )["fragile_file_gate"]
        self.assertTrue(decision["fragile"])
        self.assertEqual(decision["matched_paths"], ["src/app.py"])
        self.assertEqual(decision["source_status_by_path"]["src/app.py"], "current")
        self.assertIn("read_file_evidence", decision["missing"])
        self.assertNotIn("source_freshness_current", decision["missing"])
        self.assertFalse(decision["allowed_to_continue"])

    def test_stale_fragile_memory_is_warning_only_and_cannot_block(self) -> None:
        with tempfile.TemporaryDirectory() as repo_s:
            repo = Path(repo_s)
            source = _write(repo, "src/app.py", "value = 1\n")
            events = [_event(repo, "fragile-1"), _event(repo, "fragile-2")]
            source.write_text("value = 2\n", encoding="utf-8")
            decision = evaluate_fragile_file_gate(
                events,
                paths=["src/app.py"],
                evidence={},
                mode="block",
                repo_root=repo,
            )["fragile_file_gate"]
        self.assertTrue(decision["fragile"])
        self.assertEqual(decision["matched_paths"], [])
        self.assertEqual(decision["historical_hint_paths"], ["src/app.py"])
        self.assertEqual(decision["source_status_by_path"]["src/app.py"], "stale")
        self.assertIn("project_memory_stale_source", decision["residual_risk"])
        self.assertTrue(decision["allowed_to_continue"])


def _write(repo: Path, rel_path: str, body: str) -> Path:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _event(repo: Path, event_id: str) -> dict:
    return sanitize_memory_event(
        {
            "repo_hash": "repo",
            "event_id": event_id,
            "timestamp": "2026-06-01T00:00:00Z",
            "kind": "fragile_file",
            "type": "review_finding",
            "paths": ["src/app.py"],
            "summary": "Repeated review finding.",
            "outcome": "failed",
            "evidence_refs": ["validation:pytest", "review:rereview"],
            "source_evidence": {
                "repo_rel_path": "src/app.py",
                "source_hash": sha256_file(repo / "src/app.py"),
                "hash_algorithm": "sha256",
                "observed_at_event_id": event_id,
                "observed_at_timestamp": "2026-06-01T00:00:00Z",
                "graph_freshness": "current",
                "validation_freshness": "current",
            },
        },
        repo=repo,
    )


if __name__ == "__main__":
    unittest.main()
