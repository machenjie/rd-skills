"""Optional coordination artifacts preserve evidence without mandatory ceremony."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('task_templates', ROOT / 'scripts/validate-task-contracts.py')
VALIDATOR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(VALIDATOR)


class OptionalArtifactTests(unittest.TestCase):
    def test_current_optional_templates_pass(self):
        self.assertEqual(0, VALIDATOR.main())

    def test_brief_has_decision_content_without_process_lock(self):
        text = (ROOT / 'src/control-skills/engineering-control-plane/references/engineering-brief-template.md').read_text()
        for section in ('Goal', 'Important Constraints and Invariants', 'Key Decisions', 'Validation', 'Unresolved Issues'):
            self.assertIn(section, text)
        for retired in ('effective_level', 'Signature', 'Fingerprint', 'Review Round'):
            self.assertNotIn(retired, text)

    def test_ordinary_assignment_allows_discovery(self):
        text = (ROOT / 'src/control-skills/engineering-control-plane/references/direct-task-template.md').read_text()
        self.assertIn('bounded search/read', text)
        self.assertIn('write', text.lower())
        self.assertIn('validation', text.lower())


if __name__ == '__main__':
    unittest.main()
