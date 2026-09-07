from __future__ import annotations
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from routing_scenarios import load_release_routing_scenarios, project_release_route_hints, release_routing_scenario_errors

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ROUTING = load('release_routing_validator_test', 'scripts/validate-skill-routing.py')
CODEGEN = load('release_routing_codegen_test', 'scripts/validate-codegen-benchmarks.py')

class ReleaseRoutingScenarioAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_release_routing_scenarios(ROOT / 'src/registry/release-routing-scenarios.yaml')

    def test_current_expertise_has_one_matching_router_row(self):
        self.assertEqual([], ROUTING._release_routing_projection_errors(self.rows, ROUTING.ROUTER.read_text()))

    def test_wrong_primary_cannot_match_current_router(self):
        self.rows[0]['router']['expected']['primary'] = 'frontend-change-builder'
        self.assertTrue(ROUTING._release_routing_projection_errors(self.rows, ROUTING.ROUTER.read_text()))

    def test_codegen_identity_is_existing_unique_nonempty_text(self):
        for value in ('', [], 'missing/case', self.rows[1]['codegen_case_id']):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[0]['codegen_case_id'] = value
                self.assertTrue(release_routing_scenario_errors(rows))

    def test_layer3_cannot_overflow_duplicate_or_be_malformed(self):
        for value in (None, 'threat-modeling', ['x'] * 2, ['a', 'b', 'c', 'd'], [[]]):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[0]['router']['expected']['layer3'] = value
                self.assertTrue(release_routing_scenario_errors(rows))

    def test_implementation_examples_need_no_fixed_phases_or_review(self):
        for row in self.rows:
            self.assertTrue({'tasks','analysis','review','control_path','light_case_id'}.isdisjoint(row))
            hints = project_release_route_hints(row)
            if hints['agent_profile'] == 'task-agent':
                self.assertIsNone(hints['review_skill'])

    def test_real_security_and_concurrency_keep_professional_knowledge(self):
        rows = {row['id']: row for row in self.rows}
        self.assertTrue({'threat-modeling','web-security'} <= set(project_release_route_hints(rows['security-ssrf-boundary'])['layer3_skills']))
        self.assertIn('concurrency-control', project_release_route_hints(rows['cache-stampede-reliability'])['layer3_skills'])

    def test_codegen_duplicate_cannot_silently_overwrite_first_owner(self):
        rows = copy.deepcopy(self.rows[:2])
        rows[1]['codegen_case_id'] = rows[0]['codegen_case_id']
        errors = []
        with patch.object(CODEGEN, 'load_release_routing_scenarios', return_value=rows):
            projected = CODEGEN._load_release_routing_projections(errors)
        self.assertTrue(any('duplicate codegen_case_id' in error for error in errors))
        self.assertEqual(project_release_route_hints(rows[0]), projected[rows[0]['codegen_case_id']]['route_hints'])

    def test_codegen_consumes_current_knowledge_and_rejects_projection_drift(self):
        errors = []
        projected = CODEGEN._load_release_routing_projections(errors)
        for row in self.rows:
            category, case = row['codegen_case_id'].split('/')
            path = ROOT / 'evals/codegen' / category / case / 'expected-qualities.yaml'
            CODEGEN._validate_expected_qualities(path, category, case, CODEGEN._load_registry_entries(), projected, errors)
        self.assertEqual([], errors)
        row = self.rows[0]
        category, case = row['codegen_case_id'].split('/')
        projected[row['codegen_case_id']]['route_hints']['primary_skill'] = 'frontend-change-builder'
        CODEGEN._validate_expected_qualities(ROOT / 'evals/codegen' / category / case / 'expected-qualities.yaml', category, case, CODEGEN._load_registry_entries(), projected, errors)
        self.assertTrue(any('route_hints disagree' in error for error in errors), errors)

if __name__ == '__main__':
    unittest.main()
