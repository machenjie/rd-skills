from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def load_subject():
    path = ROOT / "migration.py"
    spec = importlib.util.spec_from_file_location("candidate_online_migration", path)
    if spec is None or spec.loader is None:
        raise AssertionError("migration.py is required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LargeTableOnlineMigrationAssertions(unittest.TestCase):
    def test_expand_and_dual_contracts_preserve_old_and_new_clients(self) -> None:
        subject = load_subject()
        old = {"id": 1, "tenant_id": "a", "full_name": "Prince"}
        expanded = subject.expand_row(old)
        self.assertEqual(expanded["full_name"], "Prince")
        self.assertIsNone(expanded["first_name"])
        self.assertEqual(subject.read_profile(old, "old"), {"full_name": "Prince"})
        self.assertEqual(
            subject.read_profile(old, "new"), {"first_name": "Prince", "last_name": None}
        )
        legacy_write = subject.write_profile(old, {"full_name": "Ada Lovelace"})
        self.assertEqual((legacy_write["first_name"], legacy_write["last_name"]), ("Ada", "Lovelace"))
        new_write = subject.write_profile(old, {"first_name": "Grace", "last_name": "Hopper"})
        self.assertEqual(new_write["full_name"], "Grace Hopper")

    def test_backfill_is_bounded_tenant_scoped_resumable_and_non_destructive(self) -> None:
        subject = load_subject()
        rows = [
            {"id": 1, "tenant_id": "a", "full_name": "Ada Lovelace", "first_name": None, "last_name": None},
            {"id": 2, "tenant_id": "b", "full_name": "Other Tenant", "first_name": None, "last_name": None},
            {"id": 3, "tenant_id": "a", "full_name": "Manual Value", "first_name": "Corrected", "last_name": "Name"},
            {"id": 4, "tenant_id": "a", "full_name": "Grace Hopper", "first_name": None, "last_name": None},
        ]
        cursor, count = subject.backfill_batch(rows, 0, 2, "a")
        self.assertEqual((cursor, count), (3, 2))
        self.assertEqual((rows[0]["first_name"], rows[0]["last_name"]), ("Ada", "Lovelace"))
        self.assertEqual((rows[1]["first_name"], rows[1]["last_name"]), (None, None))
        self.assertEqual((rows[2]["first_name"], rows[2]["last_name"]), ("Corrected", "Name"))
        cursor, count = subject.backfill_batch(rows, cursor, 2, "a")
        self.assertEqual((cursor, count), (4, 1))
        self.assertEqual(subject.backfill_batch(rows, cursor, 2, "a"), (4, 0))

    def test_rollback_and_cleanup_gate_protect_legacy_contract(self) -> None:
        subject = load_subject()
        split = {"id": 1, "tenant_id": "a", "full_name": "", "first_name": "Ada", "last_name": "Lovelace"}
        self.assertEqual(subject.rollback_before_cleanup(split)["full_name"], "Ada Lovelace")
        with self.assertRaises(RuntimeError):
            subject.contract_cleanup([split], approved=False)
        plan = json.loads((ROOT / "rollout_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["phases"], ["expand", "dual-write", "backfill", "cutover", "contract"])
        self.assertTrue(plan["cleanup_gate"])
        self.assertTrue(plan["stop_conditions"])


if __name__ == "__main__":
    unittest.main()
