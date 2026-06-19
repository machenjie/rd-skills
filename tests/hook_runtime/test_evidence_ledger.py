from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_action_classifier import normalize_event  # noqa: E402
from changeforge_evidence_ledger import EvidenceLedger  # noqa: E402


class EvidenceLedgerTests(unittest.TestCase):
    def test_from_state_collects_closure_safe_evidence(self) -> None:
        event = normalize_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest tests/hook_runtime"},
            }
        )
        ledger = EvidenceLedger.from_state(
            {
                "read_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
                "changed_paths": ["src/hook-runtime/scripts/changeforge_runtime_adapters.py"],
                "validation_command_seen": True,
                "validation_freshness_seen": True,
                "review_targets": ["src/hook-runtime/scripts/changeforge_runtime_adapters.py"],
                "reviewer_skill": "ai-code-review-refactor",
            },
            normalized_event=event,
            route_manifest_complete=True,
            residual_risk_present=True,
        )
        data = ledger.to_dict()
        self.assertEqual(
            data["read_evidence"]["paths"],
            ["src/hook-runtime/scripts/changeforge_common.py"],
        )
        self.assertIn("pytest", data["validation_evidence"]["commands"])
        self.assertTrue(data["validation_evidence"]["outcome_seen"])
        self.assertTrue(data["validation_evidence"]["fresh_after_last_edit"])
        self.assertTrue(data["closure_evidence"]["route_manifest_complete"])

    def test_repair_evidence_without_explicit_re_review_stays_open(self) -> None:
        ledger = EvidenceLedger.from_state(
            {
                "repair_findings": ["src/app.py: fixed null path"],
                "repair_evidence_seen": True,
                "review_evidence_seen": True,
            }
        )
        self.assertFalse(ledger.repair_evidence.re_review_seen)
        self.assertEqual(ledger.repair_evidence.repaired_paths, ["src/app.py: fixed null path"])

    def test_repair_evidence_tracks_explicit_re_review_signal(self) -> None:
        ledger = EvidenceLedger.from_state(
            {
                "repair_findings": ["src/app.py: fixed null path"],
                "repair_evidence_seen": True,
                "review_after_repair_seen": True,
            }
        )
        self.assertTrue(ledger.repair_evidence.re_review_seen)


if __name__ == "__main__":
    unittest.main()
