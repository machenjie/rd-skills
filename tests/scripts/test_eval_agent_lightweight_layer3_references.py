"""Actual Profile, selected owner and exact nested Reference authorization."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from fixture_capsule_contract import FIXTURE_HOST_SKILLS_ROOT, FixtureCapsuleError, validate_and_render_fixture_capsule


class Layer3ReferenceTests(unittest.TestCase):
    def step(self):
        return dict(profile='review-agent', primary_skill='ai-code-review-refactor',
                    goal='Inspect changed failure behavior and reachable consumers.',
                    layer3_skills=['code-review'],
                    layer3_references=['references/layer3/code-review/references/finding-taxonomy.md'])

    def test_expanded_references_reach_exact_owners_and_reject_unselected_or_wrong_roles(self):
        # Independent assignments exercise role/owner authorization and Host paths.
        # They prove legal delivery, not a model's conditional-loading judgment.
        groups = {
            "java-jvm-professional-usage": ("backend-change-builder", "spring-runtime-wiring-and-advice scala-types-collections-and-effects"),
            "python-professional-usage": ("backend-change-builder", "asgi-request-resource-lifecycle django-orm-evaluation-and-transactions sqlalchemy-session-and-loading"),
            "test-strategy": ("quality-test-gate", "load-model-and-capacity-evidence"),
            "unit-testing": ("quality-test-gate", "generative-invariant-testing"),
            "ai-product-extension": ("backend-change-builder", "ai-evaluation-design-and-analysis llm-inference-performance ml-training-and-experiment-engineering rag-quality-and-retrieval-design"),
            "data-format-contract-usage": ("library-tool-product-builder", "incremental-stream-codecs"),
            "search-analytics-design": ("quality-test-gate", "experiment-decision-validity"),
            "commerce-fulfillment-extension": ("backend-change-builder", "reservation-fulfillment-and-return-transitions"),
            "game-simulation-extension": ("installed-client-change-builder", "scene-assets-and-save-migration simulation-clock-authority-and-replay"),
            "graphics-compute-extension": ("installed-client-change-builder", "cuda-hip-execution-and-memory metal-resource-synchronization vulkan-synchronization-and-layouts webgpu-device-and-render-contracts"),
            "hosted-app-extension": ("installed-client-change-builder", "browser-extension-lifecycle-and-messaging ide-extension-host-and-workspace mini-program-lifecycle-and-bridge"),
            "realtime-media-extension": ("installed-client-change-builder", "media-processing-completeness-and-seek timing-buffering-and-track-lifecycle"),
            "saas-product-extension": ("backend-change-builder", "subscription-entitlement-timelines usage-seats-and-corrections"),
            "scientific-computing-extension": ("library-tool-product-builder", "solver-validity-and-reproducibility"),
            "beam-professional-usage": ("backend-change-builder", "process-messages-and-supervision"),
            "dart-professional-usage": ("backend-change-builder", "async-streams-and-isolates"),
            "julia-professional-usage": ("library-tool-product-builder", "arrays-dispatch-and-randomness"),
            "numerical-correctness": ("library-tool-product-builder", "error-budget-and-oracles"),
            "php-professional-usage": ("backend-change-builder", "values-errors-and-worker-lifetime"),
            "r-professional-usage": ("library-tool-product-builder", "shape-missing-values-and-reproducibility"),
            "ruby-professional-usage": ("backend-change-builder", "dispatch-blocks-and-concurrency"),
        }
        for owner, (task_primary, names) in groups.items():
            for name in names.split():
                reference = f"references/layer3/{owner}/references/{name}.md"
                for role, primary in (
                    ("task-agent", task_primary),
                    ("analysis-agent", "quality-test-gate" if owner in {"unit-testing", "test-strategy"} else "engineering-change-analysis"),
                    ("review-agent", "quality-test-gate" if owner in {"unit-testing", "test-strategy", "search-analytics-design"} else "ai-code-review-refactor"),
                ):
                    with self.subTest(reference=reference, role=role):
                        step = dict(profile=role, primary_skill=primary, goal="Examine the assigned mechanism and its failure boundary.", layer3_skills=[owner], professional_references=[], layer3_references=[reference])
                        text = validate_and_render_fixture_capsule(step)
                        self.assertIn(str(FIXTURE_HOST_SKILLS_ROOT / primary / reference), text)
                        step["layer3_skills"] = []
                        with self.assertRaises(FixtureCapsuleError):
                            validate_and_render_fixture_capsule(step)
        for primary, names in {
            "frontend-change-builder": "react-render-effects-and-identity server-client-rendering-contracts vue-reactivity-and-effect-lifetime",
            "integration-change-builder": "mcp-protocol-contracts",
        }.items():
            for name in names.split():
                step = dict(profile="task-agent", primary_skill=primary, goal="Implement the bounded framework or protocol behavior.", layer3_skills=[], professional_references=[f"references/{name}.md"], layer3_references=[])
                self.assertIn(name, validate_and_render_fixture_capsule(step))
                step["profile"] = "review-agent"
                with self.assertRaises(FixtureCapsuleError):
                    validate_and_render_fixture_capsule(step)

    def test_selected_current_reference_is_rendered(self):
        self.assertIn('finding-taxonomy.md', validate_and_render_fixture_capsule(self.step()))

    def test_both_reference_owners_have_direct_host_paths(self):
        step = dict(profile='task-agent', primary_skill='repository-tooling-change-builder',
                    goal='Repair the generator.', layer3_skills=[], layer3_references=[],
                    professional_references=['references/generator-and-plugin-contracts.md'])
        rendered = validate_and_render_fixture_capsule(step)
        host_root = FIXTURE_HOST_SKILLS_ROOT / 'repository-tooling-change-builder'
        self.assertIn(str(host_root / 'SKILL.md'), rendered)
        self.assertIn(str(host_root / step['professional_references'][0]), rendered)
        nested = self.step()
        host_root = FIXTURE_HOST_SKILLS_ROOT / 'ai-code-review-refactor'
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
        self.assertNotIn('references/runtime/selector.json', rendered)
        self.assertIn('Read these owner partitions directly for Reference loading rules', rendered)
        step.update(professional_references=[], layer3_references=[])
        rendered = validate_and_render_fixture_capsule(step)
        self.assertIn('References exact: []', rendered)
        self.assertNotIn('References unresolved', rendered)

    def test_explicit_host_root_remains_verbatim_and_unsafe_roots_fail(self):
        step = self.step()
        actual = Path('/actual-host/installed/ai-code-review-refactor')
        rendered = validate_and_render_fixture_capsule(step, professional_root=actual)
        self.assertIn(str(actual / 'SKILL.md'), rendered)
        self.assertNotIn(str(FIXTURE_HOST_SKILLS_ROOT), rendered)
        for unsafe in (Path('relative/ai-code-review-refactor'),
                       Path('/host/../ai-code-review-refactor'), Path('/host/wrong-primary')):
            with self.subTest(root=unsafe), self.assertRaises(FixtureCapsuleError):
                validate_and_render_fixture_capsule(step, professional_root=unsafe)

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
