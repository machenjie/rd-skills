from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.hook_safe import adapter
from project_memory.source_evidence import sha256_file


class ProjectMemoryHookSafeAdapterTests(unittest.TestCase):
    def test_current_strong_fragile_memory_returns_blockable_source_status(self) -> None:
        with _memory_env() as (repo, _cache):
            _write(repo, "src/app.py", "value = 1\n")
            _seed_fragile_events(repo)
            advice = adapter.pre_edit_advice(repo, ["src/app.py"], {}, "")
        self.assertEqual(advice["status"], "available")
        self.assertEqual(advice["source_status"], "current")
        self.assertEqual(advice["fragile_paths"], ["src/app.py"])
        self.assertEqual(advice["current_fragile_paths"], ["src/app.py"])
        self.assertIn("read_file_evidence", advice["missing"])

    def test_stale_fragile_memory_is_warning_only_with_residual_risk(self) -> None:
        with _memory_env() as (repo, _cache):
            source = _write(repo, "src/app.py", "value = 1\n")
            _seed_fragile_events(repo)
            source.write_text("value = 2\n", encoding="utf-8")
            advice = adapter.pre_edit_advice(repo, ["src/app.py"], {}, "")
        self.assertEqual(advice["status"], "available")
        self.assertEqual(advice["source_status"], "stale")
        self.assertEqual(advice["fragile_paths"], [])
        self.assertEqual(advice["historical_fragile_paths"], ["src/app.py"])
        self.assertEqual(advice["warning_only_paths"], ["src/app.py"])
        self.assertIn("project_memory_stale_source", advice["residual_risk"])
        self.assertTrue(advice["warnings"])
        self.assertEqual(advice["missing"], [])

    def test_pre_edit_advice_fails_open_with_residual_risk(self) -> None:
        with _memory_env() as (repo, _cache):
            with mock.patch.object(adapter, "_read_events", side_effect=RuntimeError("boom")):
                advice = adapter.pre_edit_advice(repo, ["src/app.py"], {}, "")
        self.assertEqual(advice["status"], "unavailable_due_error")
        self.assertEqual(advice["source_status"], "unknown")
        self.assertIn("project_memory_unavailable", advice["residual_risk"])
        self.assertEqual(advice["fragile_paths"], [])


class _memory_env:
    def __enter__(self) -> tuple[Path, Path]:
        self._repo_tmp = tempfile.TemporaryDirectory()
        self._cache_tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._repo_tmp.name)
        self.cache = Path(self._cache_tmp.name)
        self.previous = {
            "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME"),
            "CHANGEFORGE_MEMORY": os.environ.get("CHANGEFORGE_MEMORY"),
            "CHANGEFORGE_TELEMETRY": os.environ.get("CHANGEFORGE_TELEMETRY"),
        }
        os.environ["XDG_CACHE_HOME"] = str(self.cache)
        os.environ.pop("CHANGEFORGE_MEMORY", None)
        os.environ.pop("CHANGEFORGE_TELEMETRY", None)
        return self.repo, self.cache

    def __exit__(self, *_args: object) -> None:
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._repo_tmp.cleanup()
        self._cache_tmp.cleanup()


def _write(repo: Path, rel_path: str, body: str) -> Path:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _seed_fragile_events(repo: Path) -> None:
    for event_id in ("fragile-1", "fragile-2"):
        adapter.write_event(
            repo,
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
        )


if __name__ == "__main__":
    unittest.main()
