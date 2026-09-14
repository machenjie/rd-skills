"""Actual Profile, selected owner and exact nested Reference authorization."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from fixture_capsule_contract import FixtureCapsuleError, validate_and_render_fixture_capsule


class Layer3ReferenceTests(unittest.TestCase):
    def step(self):
        return dict(profile='review-agent', primary_skill='ai-code-review-refactor',
                    goal='Inspect changed failure behavior and reachable consumers.',
                    layer3_skills=['code-review'],
                    layer3_references=['references/layer3/code-review/references/finding-taxonomy.md'])

    def test_selected_current_reference_is_rendered(self):
        self.assertIn('finding-taxonomy.md', validate_and_render_fixture_capsule(self.step()))

    def test_both_reference_owners_have_direct_host_paths(self):
        step = dict(profile='task-agent', primary_skill='repository-tooling-change-builder',
                    goal='Repair the generator.', layer3_skills=[], layer3_references=[],
                    professional_references=['references/generator-and-plugin-contracts.md'])
        rendered = validate_and_render_fixture_capsule(step)
        host_root = ROOT / 'dist/universal/skills/recommended/repository-tooling-change-builder'
        self.assertIn(str(host_root / 'SKILL.md'), rendered)
        self.assertIn(str(host_root / step['professional_references'][0]), rendered)
        nested = self.step()
        host_root = ROOT / 'dist/universal/skills/recommended/ai-code-review-refactor'
        rendered = validate_and_render_fixture_capsule(nested)
        self.assertIn(str(host_root / 'references/layer3/code-review.md'), rendered)
        self.assertIn(str(host_root / nested['layer3_references'][0]), rendered)

    def test_exact_layer3_does_not_imply_exact_references(self):
        step = self.step()
        del step['layer3_references']
        rendered = validate_and_render_fixture_capsule(step)
        self.assertIn('References unresolved', rendered)
        self.assertIn('references/runtime/reference-records/ai-code-review-refactor.json', rendered)
        self.assertIn('references/runtime/reference-records/code-review.json', rendered)
        step.update(professional_references=[], layer3_references=[])
        rendered = validate_and_render_fixture_capsule(step)
        self.assertIn('References exact: []', rendered)
        self.assertNotIn('References unresolved', rendered)

    def test_owner_must_be_selected(self):
        step = self.step(); step['layer3_skills'] = []
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(step)

    def test_missing_reference_is_rejected(self):
        step = self.step(); step['layer3_references'] = ['references/layer3/code-review/references/missing.md']
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(step)

    def test_reference_lists_reject_unknown_duplicate_and_malformed_values(self):
        for field in ('professional_references', 'layer3_references'):
            for value in ('references/checklist.md', {}, [None], ['references/missing.md'],
                          ['references/checklist.md', 'references/checklist.md']):
                step = self.step()
                step[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(FixtureCapsuleError):
                    validate_and_render_fixture_capsule(step)

    def test_role_authorization_is_itemwise(self):
        step = dict(profile='review-agent', primary_skill='architecture-impact-reviewer',
                    goal='Inspect the module boundary.', layer3_skills=['architecture-style-selection'])
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(step)

    def test_duplicate_selection_is_rejected_at_multiple_cardinalities(self):
        for selection in (['code-review', 'code-review'], ['code-review'] * 4):
            step = self.step(); step['layer3_skills'] = selection
            with self.assertRaises(FixtureCapsuleError):
                validate_and_render_fixture_capsule(step)

    def test_reference_path_cannot_escape_or_load_catalog(self):
        for suffix in ('../SKILL.md', 'index.md', 'catalog.md', '/absolute.md'):
            step = self.step(); step['layer3_references'] = ['references/layer3/code-review/references/' + suffix]
            with self.assertRaises(FixtureCapsuleError):
                validate_and_render_fixture_capsule(step)


if __name__ == '__main__':
    unittest.main()
