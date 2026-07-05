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

from project_memory.privacy import sanitize_memory_event


class PrivacyTests(unittest.TestCase):
    def test_new_memory_fields_are_bounded_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            repo = Path(tmp_s)
            (repo / "src").mkdir()
            event = sanitize_memory_event(
                {
                    "event_id": "unsafe-id",
                    "kind": "validation_pattern",
                    "bounded_paths": [str(repo / "src" / "app.py"), "/Users/me/private.py"],
                    "summary": "password=secret",
                    "env": {"TOKEN": "secret"},
                    "source": "telemetry",
                },
                repo=repo,
            )
        self.assertTrue(event["event_id"].startswith("mem_"))
        self.assertEqual(event["bounded_paths"], ["src/app.py"])
        self.assertEqual(event["paths"], ["src/app.py"])
        self.assertEqual(event["privacy_class"], "redacted")
        text = json.dumps(event)
        self.assertNotIn("/Users/me", text)
        self.assertNotIn("TOKEN", text)
        self.assertNotIn("password=secret", text)


if __name__ == "__main__":
    unittest.main()
