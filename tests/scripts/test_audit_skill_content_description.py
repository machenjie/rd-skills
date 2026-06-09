from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
AUDIT_SCRIPT = SCRIPTS_DIR / "audit-skill-content.py"


def _load_audit() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("audit_skill_content", AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import audit-skill-content.py")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass processing can resolve the module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load_audit()


class DescriptionAuditTests(unittest.TestCase):
    def _findings(self, description: str) -> list[str]:
        return AUDIT._description_findings(description)

    def _joined(self, description: str) -> str:
        return " | ".join(self._findings(description))

    def test_long_description_flagged(self) -> None:
        long_desc = (
            "Reviews code for correctness and structure across many surfaces, "
            * 6
        )
        self.assertIn("long", self._joined(long_desc))

    def test_workflow_summary_flagged(self) -> None:
        desc = (
            "Reviews a change: first inspect the diff, then run the tests, then "
            "approve the result for the team."
        )
        self.assertIn("workflow summary", self._joined(desc))

    def test_catch_all_flagged(self) -> None:
        desc = "Handles anything and everything for all changes in the repository at any time."
        self.assertIn("catch-all", self._joined(desc))

    def test_missing_trigger_flagged(self) -> None:
        # No capability-verb opening, no trigger preposition, no scope noun.
        desc = "The helper that gets stuff working and keeps it nice and tidy always."
        self.assertIn("no trigger condition", self._joined(desc))

    def test_capability_verb_opening_is_not_missing_trigger(self) -> None:
        desc = (
            "Designs minimal transaction boundaries that preserve named business "
            "invariants while avoiding distributed transactions."
        )
        self.assertNotIn("no trigger condition", self._joined(desc))

    def test_clean_description_has_no_findings(self) -> None:
        desc = "Reviews generated or modified code for correctness, boundaries, and hallucinated APIs."
        self.assertEqual(self._findings(desc), [])

    def test_missing_description_flagged(self) -> None:
        self.assertIn("missing", self._joined(""))


if __name__ == "__main__":
    unittest.main()
