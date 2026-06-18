from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.store.append_log import append_memory_event, iter_memory_events


class AppendLogTests(unittest.TestCase):
    def test_append_writes_one_jsonl_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            root = Path(tmp_s) / "memory"
            event = append_memory_event(
                {
                    "repo_hash": "repo",
                    "task_fingerprint": "task",
                    "type": "implementation_attempt",
                    "paths": ["src/app.py"],
                    "outcome": "failed",
                },
                root=root,
                fail_open=False,
            )
            events = list(iter_memory_events(root))
        self.assertIsNotNone(event)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["paths"], ["src/app.py"])

    def test_append_log_fails_open_by_default(self) -> None:
        result = append_memory_event(
            {"repo_hash": "repo", "task_fingerprint": "task"},
            root=Path("/dev/null/not-a-dir"),
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

