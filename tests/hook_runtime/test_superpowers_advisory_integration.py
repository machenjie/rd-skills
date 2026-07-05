from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
SRC = ROOT / "src"


def load_stop_gate():
    for path in (str(SCRIPT_DIR), str(SRC)):
        if path not in sys.path:
            sys.path.insert(0, path)
    spec = importlib.util.spec_from_file_location(
        "changeforge_stop_closure_gate_superpowers_test",
        SCRIPT_DIR / "changeforge_stop_closure_gate.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SuperpowersAdvisoryIntegrationTests(unittest.TestCase):
    def test_stop_gate_renders_advisory_quality_note_without_internal_protocol(self) -> None:
        gate = load_stop_gate()
        message = gate._superpowers_advisory_text(
            {
                "changed_paths": ["src/a.py"],
                "planned_files": ["src/a.py"],
                "validation_command_seen": False,
                "review_evidence_seen": False,
            },
            "Done.",
        )

        self.assertIn("Engineering quality note:", message)
        self.assertIn("no validation command", message)
        self.assertIn("Review evidence is missing", message)
        self.assertNotIn("process_phase_ledgers", message)
        self.assertNotIn(".changeforge hook state", message)

    def test_stop_gate_advisory_passes_when_evidence_is_complete(self) -> None:
        gate = load_stop_gate()
        message = gate._superpowers_advisory_text(
            {
                "changed_paths": ["src/a.py"],
                "planned_files": ["src/a.py"],
                "validation_results": ["python3 -m unittest tests.test_a passed"],
                "validation_freshness_seen": True,
                "review_evidence_seen": True,
            },
            (
                "Spec Compliance: pass\n"
                "Code Quality: pass\n"
                "Review scope: src/a.py\n"
                "Findings: none by severity\n"
                "Required next action: proceed\n"
                "Residual Risk: none\n"
                "AC: behavior works - PROVEN BY python3 -m unittest tests.test_a passed"
            ),
        )

        self.assertEqual(message, "")

    def test_stop_gate_derives_planned_files_from_visible_plan_handoff(self) -> None:
        gate = load_stop_gate()
        message = gate._superpowers_advisory_text(
            {
                "changed_paths": ["src/a.py"],
                "validation_results": ["python3 -m unittest tests.test_a passed"],
                "validation_freshness_seen": True,
                "review_evidence_seen": True,
            },
            (
                "# Plan Handoff\n"
                "Files:\n"
                "- Modify: `src/a.py`\n"
                "Verify:\n"
                "- Command: python3 -m unittest tests.test_a\n"
                "Residual Risk:\n"
                "- none\n"
                "Spec Compliance: pass\n"
                "Code Quality: pass\n"
                "Review scope: src/a.py\n"
                "Findings: none by severity\n"
                "Required next action: proceed\n"
                "Residual Risk: none\n"
                "AC: behavior works - PROVEN BY python3 -m unittest tests.test_a passed"
            ),
        )

        self.assertEqual(message, "")

    def test_stop_gate_reports_missing_plan_files_when_unavailable(self) -> None:
        gate = load_stop_gate()
        message = gate._superpowers_advisory_text(
            {
                "changed_paths": ["src/a.py"],
                "validation_results": ["python3 -m unittest tests.test_a passed"],
                "validation_freshness_seen": True,
                "review_evidence_seen": True,
            },
            (
                "Spec Compliance: pass\n"
                "Code Quality: pass\n"
                "Review scope: src/a.py\n"
                "Findings: none by severity\n"
                "Required next action: proceed\n"
                "Residual Risk: none\n"
                "AC: behavior works - PROVEN BY python3 -m unittest tests.test_a passed"
            ),
        )

        self.assertIn("plan files were not visible", message)


if __name__ == "__main__":
    unittest.main()
