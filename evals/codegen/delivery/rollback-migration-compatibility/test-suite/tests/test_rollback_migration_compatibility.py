from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def load_subject():
    path = ROOT / "status_migration.py"
    spec = importlib.util.spec_from_file_location("candidate_status_migration", path)
    if spec is None or spec.loader is None:
        raise AssertionError("status_migration.py is required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RollbackMigrationCompatibilityAssertions(unittest.TestCase):
    def test_old_and_new_writers_remain_readable_by_both_versions(self) -> None:
        subject = load_subject()
        row = {"id": 1, "legacy_status": "P", "audit": []}
        old_write = subject.write_status(row, "S", writer="old")
        self.assertEqual(subject.read_status(old_write, reader="old"), "S")
        self.assertEqual(subject.read_status(old_write, reader="new"), "shipped")
        new_write = subject.write_status(old_write, "cancelled", writer="new")
        self.assertEqual(subject.read_status(new_write, reader="old"), "C")
        self.assertEqual(subject.read_status(new_write, reader="new"), "cancelled")
        self.assertEqual(len(new_write["audit"]), 2)

    def test_backfill_is_bounded_resumable_idempotent_and_preserves_audit(self) -> None:
        subject = load_subject()
        rows = [
            {"id": 1, "legacy_status": "P", "audit": ["created"]},
            {"id": 2, "legacy_status": "S", "normalized_status": "manual", "audit": ["corrected"]},
            {"id": 3, "legacy_status": "C", "audit": []},
        ]
        cursor, count = subject.backfill_batch(rows, 0, 2)
        self.assertEqual((cursor, count), (2, 2))
        self.assertEqual(rows[0]["normalized_status"], "pending")
        self.assertEqual(rows[1]["normalized_status"], "manual")
        self.assertEqual(rows[0]["audit"], ["created"])
        cursor, count = subject.backfill_batch(rows, cursor, 2)
        self.assertEqual((cursor, count), (3, 1))
        self.assertEqual(subject.backfill_batch(rows, cursor, 2), (3, 0))

    def test_rollback_recovers_legacy_value_and_cleanup_is_gated(self) -> None:
        subject = load_subject()
        row = {"id": 1, "normalized_status": "shipped", "audit": ["preserve"]}
        rolled_back = subject.rollback_to_legacy(row)
        self.assertEqual(rolled_back["legacy_status"], "S")
        self.assertEqual(rolled_back["audit"], ["preserve"])
        with self.assertRaises(RuntimeError):
            subject.cleanup([rolled_back], approved=False)
        gates = json.loads((ROOT / "release_gates.json").read_text(encoding="utf-8"))
        self.assertEqual(gates["phases"], ["expand", "backfill", "cutover", "cleanup"])
        self.assertTrue(gates["rollback"])
        self.assertTrue(gates["stop_conditions"])


if __name__ == "__main__":
    unittest.main()
