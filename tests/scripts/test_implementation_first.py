"""Adjacent behavioral controls for the simplified runtime and routing oracle.

These are deterministic source/fixture checks, not evidence of live agent behavior.
"""
from __future__ import annotations
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from deterministic_route_oracle import route
from validation_utils import CORE_CONTRACTS, validate_main_assignment


def selected(prompt):
    return route(prompt, main_execution={'producer': 'main-control-agent', 'task_id': 'implementation-first'})['route_result']


class ImplementationFirstTests(unittest.TestCase):
    def test_owner_and_test_discovery_stays_with_implementation(self):
        result = selected('Fix the backend service method handling invalid input. Owner and verification are unknown.')
        self.assertEqual('task-agent', result['start_profile'])
        self.assertEqual('backend-change-builder', result['primary_skill'])
        self.assertIsNone(result['review_skill'])

    def test_local_change_does_not_acquire_concurrency_protocol(self):
        result = selected('Fix the backend service method handling invalid input. Its single owner is serialized; concurrency and transaction behavior remain unchanged.')
        self.assertNotIn('concurrency-control', result['layer3_skills'])
        self.assertNotIn('transaction-consistency', result['layer3_skills'])
        self.assertIsNone(result['review_skill'])

    def test_reachable_stale_worker_effect_retains_required_expertise(self):
        result = selected('Implement backend lease fencing so stale workers cannot commit duplicate external effects.')
        self.assertEqual('task-agent', result['start_profile'])
        self.assertEqual({'concurrency-control', 'idempotency-retry-design'}, set(result['layer3_skills']))

    def test_transaction_and_concurrent_write_effects_retain_required_expertise(self):
        result = selected('Implement backend transaction rollback after concurrent writes fail.')
        self.assertEqual('task-agent', result['start_profile'])
        self.assertEqual({'concurrency-control', 'transaction-consistency'}, set(result['layer3_skills']))

    def test_explicit_independent_review_still_routes_review_expertise(self):
        result = selected('Review the actual diff for generated helper misuse.')
        self.assertEqual('review-agent', result['start_profile'])
        self.assertEqual('ai-code-review-refactor', result['review_skill'])
        self.assertIn('code-review', result['layer3_skills'])

    def test_levels_are_not_dispatch_inputs(self):
        self.assertNotIn('execution_level_contract', CORE_CONTRACTS)
        self.assertEqual([], validate_main_assignment({'producer': 'main-control-agent', 'task_id': 'local-change'}))
        self.assertTrue(validate_main_assignment({'producer': 'main-control-agent', 'task_id': 'local-change', 'effective_level': 'L3'}))

    def test_runtime_preserves_optional_depth_and_final_edit_validation(self):
        spec = importlib.util.spec_from_file_location('prompt_validation', ROOT / 'scripts/validate-control-plane-prompt.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        prompt = module.PROMPT.read_text()
        self.assertEqual([], module.validate_prompt(prompt))
        for protected in ('After the final material edit, require fresh validation', 'Independent review is optional', 'current requirements or repository evidence', 'Normal repository read/search may expand as needed'):
            with self.subTest(protected=protected):
                self.assertTrue(module.validate_prompt(prompt.replace(protected, '')))


if __name__ == '__main__':
    unittest.main()
