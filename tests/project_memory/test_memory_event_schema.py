from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class MemoryEventSchemaTests(unittest.TestCase):
    def test_memory_schemas_are_strict_json_objects(self) -> None:
        schema_dir = ROOT / "src" / "project_memory" / "schemas"
        for name in (
            "memory-event.v1.schema.json",
            "memory-summary.v1.schema.json",
            "memory-query.v1.schema.json",
            "memory-decision.v1.schema.json",
        ):
            with self.subTest(name=name):
                data = json.loads((schema_dir / name).read_text(encoding="utf-8"))
                self.assertEqual(data["type"], "object")
                self.assertFalse(data["additionalProperties"])

    def test_memory_event_schema_has_required_governance_fields(self) -> None:
        data = json.loads(
            (ROOT / "src" / "project_memory" / "schemas" / "memory-event.v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required = set(data["required"])
        self.assertIn("task_fingerprint", required)
        self.assertIn("promotion_status", required)
        self.assertIn("route_decision", data["properties"]["type"]["enum"])
        self.assertIn("repeat_failure", data["properties"]["type"]["enum"])


if __name__ == "__main__":
    unittest.main()

