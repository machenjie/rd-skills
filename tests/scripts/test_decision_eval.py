import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('decision_eval', ROOT / 'scripts/eval-routing.py')
EVAL = importlib.util.module_from_spec(spec); spec.loader.exec_module(EVAL)
from validation_utils import decision_eval_contract_errors


class DecisionTests(unittest.TestCase):
    def test_compatibility_inventory_matches_unique_current_fixture_ids(self):
        expected = {'routing_cases': 307, 'capability_cases': 62}
        actual = {}
        for key, path in (('routing_cases', EVAL.CASES), ('capability_cases', EVAL.CAPABILITY_CASES)):
            with self.subTest(fixture=key):
                cases = EVAL.load_yaml_file(path)['cases']
                ids = [case['id'] for case in cases]
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in ids))
                self.assertEqual(len(ids), len(set(ids)))
                actual[key] = len(ids)
        self.assertEqual(expected, actual)
        self.assertEqual(expected, EVAL.decision_eval_authority(EVAL.CORE_CONTRACTS)['compatibility_baseline'])

    def test_compatibility_declaration_rejects_missing_or_forged_counts(self):
        for baseline in (
            {}, {'routing_cases': 307}, {'capability_cases': 62},
            {'routing_cases': 249, 'capability_cases': 62},
            {'routing_cases': 308, 'capability_cases': 62},
            {'routing_cases': 307, 'capability_cases': 61},
            {'routing_cases': 307, 'capability_cases': 63},
        ):
            with self.subTest(baseline=baseline):
                data = copy.deepcopy(EVAL.CORE_CONTRACTS)
                data['decision_eval_contract']['compatibility_baseline'] = baseline
                self.assertTrue(any('compatibility_baseline' in error for error in decision_eval_contract_errors(data)))
        data = copy.deepcopy(EVAL.CORE_CONTRACTS)
        del data['decision_eval_contract']['compatibility_baseline']
        self.assertTrue(decision_eval_contract_errors(data))

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

    def test_required_expertise_is_checked_without_pinning_combination(self):
        case = {'id': 'required', 'prompt': 'Review the actual diff.',
                'expected': {'start_profile': 'review-agent'}, 'required_skills': ['offline-sync-conflict-resolution']}
        self.assertEqual('fail', EVAL.evaluate_decision_document({'cases': [case]})['status'])
        case['required_skills'] = ['code-review']
        self.assertEqual('pass', EVAL.evaluate_decision_document({'cases': [case]})['status'])

    def test_excluded_expertise_is_checked(self):
        case = {'id': 'excluded', 'prompt': 'Review the actual diff.',
                'expected': {'start_profile': 'review-agent'}, 'excluded_skills': ['code-review']}
        self.assertEqual('fail', EVAL.evaluate_decision_document({'cases': [case]})['status'])


if __name__ == '__main__':
    unittest.main()
