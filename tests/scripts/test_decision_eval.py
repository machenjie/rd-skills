import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('decision_eval', ROOT / 'scripts/eval-routing.py')
EVAL = importlib.util.module_from_spec(spec); spec.loader.exec_module(EVAL)


class DecisionTests(unittest.TestCase):
    def test_adjacent_cases_use_real_oracle(self):
        self.assertEqual([], EVAL.evaluate_decision_cases()['errors'])

    def test_wrong_expertise_is_rejected(self):
        case = {'id': 'wrong', 'prompt': 'Implement a bounded backend service fix.',
                'expected': {'primary_skill': 'frontend-change-builder'}}
        self.assertEqual('fail', EVAL.evaluate_decision_document({'cases': [case]})['status'])

    def test_empty_or_unknown_expectation_cannot_pass(self):
        for expected in ({}, {'missing-field': None}):
            case = {'id': 'empty', 'prompt': 'Implement a bounded backend service fix.', 'expected': expected}
            self.assertEqual('fail', EVAL.evaluate_decision_document({'cases': [case]})['status'])

    def test_excluded_expertise_is_checked(self):
        case = {'id': 'excluded', 'prompt': 'Review the actual diff.',
                'expected': {'start_profile': 'review-agent'}, 'excluded_skills': ['code-review']}
        self.assertEqual('fail', EVAL.evaluate_decision_document({'cases': [case]})['status'])


if __name__ == '__main__':
    unittest.main()
