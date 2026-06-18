from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.privacy import repo_hash_for_path, sanitize_memory_event


class PrivacySanitizationTests(unittest.TestCase):
    def test_sanitizer_drops_prompt_env_secret_full_stdout_and_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            repo = Path(tmp_s)
            (repo / "src").mkdir()
            event = sanitize_memory_event(
                {
                    "repo_hash": "",
                    "task_fingerprint": "task",
                    "type": "implementation_attempt",
                    "paths": [str(repo / "src" / "app.py"), "/Users/me/private.py"],
                    "symbols": ["OrderService"],
                    "prompt": "raw user prompt",
                    "env": {"API_KEY": "secret"},
                    "stdout": "full command stdout",
                    "evidence_refs": ["cmd:pytest -q", "password=secret"],
                },
                repo=repo,
            )
        text = json.dumps(event)
        self.assertEqual(event["repo_hash"], repo_hash_for_path(repo))
        self.assertEqual(event["paths"], ["src/app.py"])
        self.assertNotIn("raw user prompt", text)
        self.assertNotIn("API_KEY", text)
        self.assertNotIn("full command stdout", text)
        self.assertNotIn("/Users/me", text)
        self.assertEqual(event["evidence_refs"], ["cmd:pytest -q"])


if __name__ == "__main__":
    unittest.main()

