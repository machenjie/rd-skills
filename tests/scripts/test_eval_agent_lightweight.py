"""Direct behavior controls for implementation and evidence boundaries."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('lightweight', ROOT / 'scripts/eval-agent-lightweight.py')
EVAL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EVAL)
DOCUMENT = json.loads((ROOT / 'evals/agent-light-trajectories/cases.yaml').read_text())
OWNER_DOCUMENT = {'schema_version': 2, **{
    group: [case for case in DOCUMENT[group] if 'repository' in case]
    for group in ('cases', 'negative_cases')
}}


class BehaviorTests(unittest.TestCase):
    def test_adjacent_authored_controls(self):
        self.assertEqual([], EVAL.evaluate(DOCUMENT)['errors'])

    def test_reading_every_source_does_not_confirm_caller_ownership(self):
        case = copy.deepcopy(DOCUMENT['cases'][0])
        case.pop('needed_sources')
        case['repository'] = {
            'src/owner.py': 'def normalize(items):\n    return list(items)\n',
            'src/caller.py': 'from src.owner import normalize\ndef run(items):\n    return normalize(items)\n',
            'tests/test_owner.py': 'from src.owner import normalize\nassert normalize(()) == []\n',
        }
        case['owner_oracle'] = {
            'owners': ['src/owner.py'],
            'authority': [{'path': 'src/owner.py', 'quote': 'return list(items)'}],
            'impact': ['src/caller.py', 'tests/test_owner.py'],
            'max_reads': 3, 'max_searches': 1,
        }
        case['steps'] = [case['steps'][0],
            {'action': 'candidate-owner', 'agent_id': 'worker', 'path': 'src/caller.py'},
            *({'action': 'read', 'agent_id': 'worker', 'path': path, 'current': True,
               'content': source} for path, source in case['repository'].items()),
            {'action': 'owner-decision', 'agent_id': 'worker', 'owners': ['src/caller.py'],
             'outcome': 'edit', 'evidence': [{'path': 'src/caller.py', 'quote': 'return normalize(items)'}]},
            {'action': 'edit', 'agent_id': 'worker', 'path': 'src/caller.py'},
            case['steps'][-1],
        ]
        case['steps'][0]['write_scope'] = ['src/*']
        self.assertIn('wrong-owner-decision', EVAL.evaluate_case(case)[1])

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


class OwnerDiscoveryTests(unittest.TestCase):
    def case(self, name):
        return copy.deepcopy(next(c for c in OWNER_DOCUMENT['cases'] if c['id'] == name))

    def probe(self, case):
        # Execute only the committed tiny Python fixtures in isolated temporary
        # repositories. This checks the oracle, not live Agent behavior.
        with tempfile.TemporaryDirectory(prefix='owner-discovery-') as raw:
            for path, source in case['repository'].items():
                destination = Path(raw) / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(source)
            result = subprocess.run(
                [sys.executable, '-I', '-c',
                 'import os, sys; sys.path.insert(0, os.getcwd())\n'
                 + case['owner_oracle']['probe']['code']],
                cwd=raw, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            return result.stdout.strip()

    def test_source_backed_positive_and_negative_decisions(self):
        self.assertEqual([], EVAL.evaluate(OWNER_DOCUMENT)['errors'])
        self.assertEqual([], EVAL.evaluate(DOCUMENT)['errors'])

    def test_oracle_is_not_an_agent_input_or_needed_source_list(self):
        from fixture_capsule_contract import validate_and_render_fixture_capsule
        for case in OWNER_DOCUMENT['cases']:
            with self.subTest(case=case['id']):
                self.assertNotIn('needed_sources', case)
                for step in case['steps']:
                    self.assertNotIn('needed_sources', step)
                    if step['action'] == 'dispatch':
                        rendered = str(validate_and_render_fixture_capsule(step))
                        for owner in case['owner_oracle']['owners']:
                            self.assertNotIn(owner, rendered)

    def test_oracle_agrees_with_executed_source_behavior(self):
        for case in OWNER_DOCUMENT['cases']:
            with self.subTest(case=case['id']):
                self.assertEqual(case['owner_oracle']['probe']['stdout'], self.probe(case))

    def test_registry_di_and_factory_source_change_moves_owner(self):
        for mechanism in ('registry', 'di', 'factory'):
            case = self.case('owner-' + mechanism + '-binding-selects-implementation')
            with self.subTest(mechanism=mechanism):
                self.assertEqual('[]', self.probe(case))
                path = 'pkg/bindings.py'
                case['repository'][path] = case['repository'][path].replace('current.normalize', 'old.normalize')
                self.assertEqual('None', self.probe(case))
                self.assertIn('owner-source-not-current', EVAL.evaluate_case(case)[1])
                # Re-extract current binding evidence; do not preserve the old
                # answer just because names, search hits and read set agree.
                oracle = case['owner_oracle']
                oracle['owners'] = ['pkg/old.py']
                oracle['authority'][0] = {'path': 'pkg/old.py', 'quote': 'return None'}
                oracle['authority'][1]['quote'] = oracle['authority'][1]['quote'].replace('current.normalize', 'old.normalize')
                for step in case['steps']:
                    if step['action'] == 'read':
                        step['content'] = case['repository'][step['path']]
                    if step['action'] == 'owner-decision':
                        step['evidence'] = copy.deepcopy(oracle['authority'])
                self.assertIn('wrong-owner-decision', EVAL.evaluate_case(case)[1])
                for step in case['steps']:
                    if step['action'] == 'owner-decision':
                        step['owners'] = ['pkg/old.py']
                    if step['action'] == 'edit':
                        step['path'] = 'pkg/old.py'
                self.assertEqual([], EVAL.evaluate_case(case)[1])

    def test_generator_input_changes_behavior_but_generated_edit_is_overwritten(self):
        case = self.case('owner-generated-follows-authoring-source')
        case['repository']['pkg/generated.py'] = 'def normalize(items):\n    return None\n'
        self.assertEqual('[]', self.probe(case))
        case['repository']['pkg/template.py'] = case['repository']['pkg/template.py'].replace('list(items)', 'tuple(items)')
        self.assertEqual('()', self.probe(case))

    def test_generator_writer_can_become_authoring_owner(self):
        case = self.case('owner-generated-follows-authoring-source')
        path = 'build/emit.py'
        source = 'SOURCE = "def normalize(items):\\n    return tuple(items)\\n"'
        case['repository'][path] = case['repository'][path].replace('from pkg.template import SOURCE', source)
        self.assertEqual('()', self.probe(case))
        self.assertIn('owner-oracle-source-mismatch', EVAL.evaluate_case(case)[1])
        oracle = case['owner_oracle']
        oracle['owners'] = [path]
        oracle['authority'] = [
            {'path': path, 'quote': source},
            {'path': path, 'quote': 'Path("pkg/generated.py").write_text(SOURCE)'},
        ]
        for step in case['steps']:
            if step['action'] == 'read':
                step['content'] = case['repository'][step['path']]
            if step['action'] == 'owner-decision':
                step['evidence'] = copy.deepcopy(oracle['authority'])
        self.assertIn('wrong-owner-decision', EVAL.evaluate_case(case)[1])
        for step in case['steps']:
            if step['action'] == 'owner-decision':
                step['owners'] = [path]
            if step['action'] == 'edit':
                step['path'] = path
        self.assertEqual([], EVAL.evaluate_case(case)[1])

    def test_multiple_enforcement_points_each_affect_a_distinct_entrypoint(self):
        for path, expected in [('pkg/http.py', '(None, [])'), ('pkg/queue.py', '([], None)')]:
            case = self.case('owner-multiple-necessary-enforcement-points')
            case['repository'][path] = case['repository'][path].replace('list(items)', 'None')
            self.assertEqual(expected, self.probe(case))
        case = self.case('owner-multiple-necessary-enforcement-points')
        case['steps'] = [s for s in case['steps'] if not (s['action'] == 'edit' and s['path'] == 'pkg/queue.py')]
        self.assertIn('owner-enforcement-not-edited', EVAL.evaluate_case(case)[1])

    def test_first_hit_order_cannot_change_confirmed_owner(self):
        case = self.case('owner-first-search-hit-is-decoy')
        first_search = next(s for s in case['steps'] if s['action'] == 'search')
        self.assertEqual('pkg/a_hint.py', first_search['results'][0])
        for hit in list(first_search['results']):
            with self.subTest(first_hit=hit):
                first_search['results'].remove(hit)
                first_search['results'].insert(0, hit)
                self.assertEqual([], EVAL.evaluate_case(case)[1])

    def test_distinct_search_queries_in_one_scope_are_not_duplicate_reads(self):
        case = self.case('owner-first-search-hit-is-decoy')
        self.assertEqual(0, EVAL.evaluate_case(case)[0]['duplicate_read_count'])

    def test_repeated_query_still_counts_despite_a_different_search_purpose(self):
        case = self.case('owner-first-search-hit-is-decoy')
        repeated = copy.deepcopy(next(s for s in case['steps'] if s['action'] == 'search'))
        repeated['purpose'] = 'competing-owner'
        case['steps'].insert(2, repeated)
        self.assertEqual(1, EVAL.evaluate_case(case)[0]['duplicate_read_count'])

    def test_repeated_current_source_read_still_counts(self):
        case = self.case('owner-simple-local')
        case['steps'].insert(3, copy.deepcopy(case['steps'][2]))
        self.assertEqual(1, EVAL.evaluate_case(case)[0]['duplicate_read_count'])

    def test_current_read_authority_and_impact_are_independently_required(self):
        original = self.case('owner-registry-binding-selects-implementation')
        for mutation, expected in (
            ('stale', 'owner-source-not-current'),
            ('unread-binding', 'owner-evidence-not-read'),
            ('quote-mismatch', 'owner-evidence-not-read'),
            ('unread-test', 'owner-impact-not-closed'),
            ('no-confirmation', 'missing-owner-decision'),
            ('no-competing-scan', 'competing-owner-scan-missing'),
        ):
            case = copy.deepcopy(original)
            if mutation == 'stale':
                next(s for s in case['steps'] if s['action'] == 'read' and s['path'] == 'pkg/bindings.py')['current'] = False
            elif mutation in {'unread-binding', 'unread-test'}:
                path = 'pkg/bindings.py' if mutation == 'unread-binding' else 'tests/test_values.py'
                case['steps'] = [s for s in case['steps'] if not (s['action'] == 'read' and s['path'] == path)]
            elif mutation == 'quote-mismatch':
                next(s for s in case['steps'] if s['action'] == 'owner-decision')['evidence'][0]['quote'] = 'filename proves ownership'
            elif mutation == 'no-confirmation':
                case['steps'] = [s for s in case['steps'] if s['action'] != 'owner-decision']
            else:
                case['steps'] = [s for s in case['steps'] if s.get('purpose') != 'competing-owner']
            with self.subTest(mutation=mutation):
                self.assertIn(expected, EVAL.evaluate_case(case)[1])

    def test_search_must_follow_current_signal_and_report_actual_hits(self):
        case = self.case('owner-registry-binding-selects-implementation')
        scan = next(s for s in case['steps'] if s.get('purpose') == 'competing-owner')
        scan['results'].remove('pkg/current.py')
        self.assertIn('owner-search-not-source-backed', EVAL.evaluate_case(case)[1])
        case = self.case('owner-registry-binding-selects-implementation')
        scan = next(s for s in case['steps'] if s.get('purpose') == 'competing-owner')
        case['steps'].remove(scan)
        case['steps'].insert(1, scan)
        self.assertIn('competing-owner-scan-missing', EVAL.evaluate_case(case)[1])

    def test_known_local_owner_needs_no_competing_scan_or_extra_agent(self):
        case = self.case('owner-simple-local')
        metrics, errors = EVAL.evaluate_case(case)
        self.assertEqual([], errors)
        self.assertEqual((1, 0, 0, 3, 0, 1), tuple(metrics[k] for k in (
            'subagent_count', 'analysis_dispatch_count', 'review_dispatch_count',
            'source_read_count', 'source_search_count', 'verification_action_count')))
        self.assertEqual([[]], [s['layer3_skills'] for s in case['steps'] if s['action'] == 'dispatch'])
        case['steps'].insert(3, dict(action='search', agent_id='worker', path='pkg/*',
            query='def normalize', purpose='competing-owner', results=['pkg/values.py']))
        self.assertIn('unsignaled-competing-owner-scan', EVAL.evaluate_case(case)[1])

    def test_bounded_search_and_read_budgets_reject_repository_enumeration(self):
        case = self.case('owner-first-search-hit-is-decoy')
        scan = next(s for s in case['steps'] if s.get('purpose') == 'competing-owner')
        scan['path'] = '**/*'
        self.assertIn('owner-search-unbounded', EVAL.evaluate_case(case)[1])
        case = self.case('owner-simple-local')
        case['steps'].insert(3, copy.deepcopy(case['steps'][2]))
        self.assertIn('owner-discovery-budget-exceeded', EVAL.evaluate_case(case)[1])

    def test_only_unresolved_conflict_escalates(self):
        for case in OWNER_DOCUMENT['cases']:
            with self.subTest(case=case['id']):
                metrics, errors = EVAL.evaluate_case(case)
                self.assertEqual([], errors)
                self.assertEqual(int(case['owner_oracle'].get('outcome') == 'analysis'), metrics['analysis_dispatch_count'])
                self.assertEqual(0, metrics['review_dispatch_count'])

    def test_unresolved_conflict_cannot_edit_or_skip_analysis(self):
        case = self.case('owner-competing-active-invariants-need-analysis')
        case['steps'] = [s for s in case['steps'] if s.get('agent_id') != 'analyst']
        self.assertIn('unresolved-owner-not-escalated', EVAL.evaluate_case(case)[1])


if __name__ == '__main__':
    unittest.main()
