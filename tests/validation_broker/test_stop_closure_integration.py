from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
SRC = ROOT / "src"
for path in (str(SCRIPT_DIR), str(SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)


def load_stop_gate():
    spec = importlib.util.spec_from_file_location(
        "changeforge_stop_closure_gate_validation_broker_test",
        SCRIPT_DIR / "changeforge_stop_closure_gate.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StopClosureIntegrationTests(unittest.TestCase):
    def test_stale_validation_is_not_strong_evidence(self) -> None:
        gate = load_stop_gate()
        state = {
            "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
            "risk_surfaces": ["hook-runtime"],
            "last_material_edit_index": 5,
            "last_validation_command_index": 4,
        }
        text = "Done. Ran python3 scripts/validate-hooks.py, passed, exit 0."
        self.assertFalse(gate._has_validation_evidence(text, state))
        assessment = gate._validation_broker_assessment(text, state, "warn")
        self.assertIn("validation_stale", assessment["issues"])
        self.assertEqual(
            assessment["validation_result"]["negative_evidence_reason"],
            "stale",
        )


if __name__ == "__main__":
    unittest.main()
