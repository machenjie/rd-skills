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

    def test_owner_must_be_selected(self):
        step = self.step(); step['layer3_skills'] = []
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(step)

    def test_missing_reference_is_rejected(self):
        step = self.step(); step['layer3_references'] = ['references/layer3/code-review/references/missing.md']
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(step)

    def test_role_authorization_is_itemwise(self):
        step = dict(profile='review-agent', primary_skill='architecture-impact-reviewer',
                    goal='Inspect the module boundary.', layer3_skills=['architecture-style-selection'])
        with self.assertRaises(FixtureCapsuleError):
            validate_and_render_fixture_capsule(step)

    def test_duplicate_or_over_budget_selection_is_rejected(self):
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
