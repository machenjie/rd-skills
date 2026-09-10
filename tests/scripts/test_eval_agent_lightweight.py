"""Direct behavior controls for implementation and evidence boundaries."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('lightweight', ROOT / 'scripts/eval-agent-lightweight.py')
EVAL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EVAL)
DOCUMENT = json.loads((ROOT / 'evals/agent-light-trajectories/cases.yaml').read_text())


class BehaviorTests(unittest.TestCase):
    def test_adjacent_authored_controls(self):
        self.assertEqual([], EVAL.evaluate(DOCUMENT)['errors'])

    def test_empty_positive_and_negative_do_not_pass(self):
        document = {'schema_version': 2, 'cases': [{'id': 'empty', 'steps': []}],
                    'negative_cases': [{'id': 'negative', 'steps': [], 'expected_errors': []}]}
        self.assertEqual('fail', EVAL.evaluate(document)['status'])

    def test_positive_cannot_accept_a_defect(self):
        document = copy.deepcopy(DOCUMENT)
        case = document['cases'][0]
        case['steps'].append({'action': 'edit', 'agent_id': 'worker', 'path': 'src/owner.py'})
        case['expected_errors'] = ['missing-post-final-edit-validation']
        self.assertEqual('fail', EVAL.evaluate(document)['status'])

    def test_later_failure_invalidates_green(self):
        case = copy.deepcopy(DOCUMENT['cases'][0])
        case['steps'].append({'action': 'validate', 'result': 'fail', 'assertion': case['assertion'], 'output': 'assertion failed'})
        self.assertIn('latest-validation-failed', EVAL.evaluate_case(case)[1])

    def test_analysis_needs_own_current_source(self):
        case = copy.deepcopy(next(c for c in DOCUMENT['cases'] if c['id'] == 'competing-owner-needs-answer'))
        case['steps'] = [s for s in case['steps'] if not (s.get('action') == 'read' and s.get('agent_id') == 'analyst')]
        self.assertIn('analysis-missing-current-source', EVAL.evaluate_case(case)[1])

    def test_review_reads_changed_source(self):
        case = copy.deepcopy(next(c for c in DOCUMENT['cases'] if c['id'] == 'independent-semantic-review'))
        next(s for s in case['steps'] if s.get('action') == 'read' and s.get('agent_id') == 'reviewer')['path'] = 'unrelated.txt'
        self.assertIn('review-missing-current-source', EVAL.evaluate_case(case)[1])

    def test_review_requires_actual_diff_not_summary(self):
        original = next(c for c in DOCUMENT['cases'] if c['id'] == 'independent-semantic-review')
        for payload in [None, 'Two lines changed in src/owner.py', 'diff --git a/src/owner.py b/src/owner.py']:
            case = copy.deepcopy(original)
            read = next(s for s in case['steps'] if s.get('action') == 'read' and s.get('agent_id') == 'reviewer')
            read['diff'] = payload
            self.assertIn('review-missing-actual-diff', EVAL.evaluate_case(case)[1])

    def test_execute_effects_need_authorization(self):
        case = copy.deepcopy(DOCUMENT['cases'][0])
        case['steps'].append({'action': 'execute', 'agent_id': 'worker', 'production': True, 'authorized': False})
        self.assertIn('effect-not-authorized', EVAL.evaluate_case(case)[1])

    def test_external_read_uses_dispatched_role(self):
        case = copy.deepcopy(DOCUMENT['cases'][0])
        case['steps'].append({'action': 'external-read', 'agent_id': 'worker', 'profile': 'analysis-agent'})
        self.assertIn('external-read-boundary', EVAL.evaluate_case(case)[1])

    def test_write_scope_normalizes_parent_segments(self):
        self.assertFalse(EVAL._in_scope('src/../private.py', ['src/*']))

    def test_file_count_is_not_an_independent_review_reason(self):
        for request in ['', 'Analyze the ownership of an existing helper.',
                        'Design the helper boundary.', 'Diagnose the failing helper.']:
            with self.subTest(request=request):
                case = copy.deepcopy(next(c for c in DOCUMENT['negative_cases'] if c['id'] == 'ceremonial-review'))
                case['user_request'] = request
                next(s for s in case['steps'] if s.get('profile') == 'review-agent')['reason'] = 'Three files changed and implementation is complete.'
                self.assertIn('extra-agent-without-question', EVAL.evaluate_case(case)[1])

    def test_explicit_review_request_allows_independent_review(self):
        case = copy.deepcopy(next(c for c in DOCUMENT['negative_cases'] if c['id'] == 'ceremonial-review'))
        case['user_request'] = 'Review the implementation independently.'
        next(s for s in case['steps'] if s.get('profile') == 'review-agent')['reason'] = 'The user requested independent review.'
        self.assertEqual([], EVAL.evaluate_case(case)[1])

    def test_layer3_role_authorization_is_itemwise(self):
        from fixture_capsule_contract import FixtureCapsuleError, validate_and_render_fixture_capsule
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(dict(profile='review-agent', primary_skill='architecture-impact-reviewer', goal='Review dependency direction', layer3_skills=['architecture-style-selection']))

    def test_nested_reference_must_exist(self):
        from fixture_capsule_contract import FixtureCapsuleError, validate_and_render_fixture_capsule
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(dict(profile='review-agent', primary_skill='ai-code-review-refactor', goal='Review current source', layer3_skills=['code-review'], layer3_references=['references/layer3/code-review/references/does-not-exist.md']))


if __name__ == '__main__':
    unittest.main()
