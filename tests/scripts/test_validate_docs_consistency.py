from __future__ import annotations

import copy
import io
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validation_utils import CORE_CONTRACTS, validate_core_contracts  # noqa: E402


def _load_validator():
    path = ROOT / "scripts" / "validate-docs-consistency.py"
    spec = importlib.util.spec_from_file_location("validate_docs_consistency", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DocsCoreProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = _load_validator()

    def _projected_docs(self, root: Path) -> None:
        docs_contract = CORE_CONTRACTS["docs_contract"]
        for projection in (
            *docs_contract["projections"],
            *docs_contract["context_budget_projections"],
        ):
            source = ROOT / projection["path"]
            target = root / projection["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def _installation_docs(self, root: Path) -> None:
        for relative in (
            "README.md",
            "docs/QUICKSTART.md",
            "docs/INSTALLATION.md",
            "docs/USAGE.md",
        ):
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def _governance_budget_inputs(self, root: Path) -> None:
        for relative in (
            "GOVERNANCE.md",
            "reports/rendered-context-budget.json",
        ):
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    def _governance_evidence_input(self, root: Path) -> Path:
        source = ROOT / "GOVERNANCE.md"
        target = root / "GOVERNANCE.md"
        target.write_bytes(source.read_bytes())
        return target

    def _copy_paths(self, root: Path, relatives: tuple[str, ...]) -> None:
        for relative in relatives:
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    def _volatile_fact_inputs(self, root: Path) -> None:
        self._copy_paths(
            root,
            (
                "src/registry/control-skills.yaml",
                "src/registry/professional-skills.yaml",
                "src/registry/foundation-skills.yaml",
                "src/registry/domain-skills.yaml",
                "evals/routing/cases.yaml",
                "evals/routing/capability-coverage-cases.yaml",
                "evals/capability-coverage/admission-cases.yaml",
                "evals/capability-coverage/matrix.yaml",
                "config/skill-content-exceptions.yaml",
                "config/professionalism-release-review.yaml",
                "AGENTS.md",
                "CHANGELOG.md",
                ".github/pull_request_template.md",
                "docs/BUILD_PROFILES.md",
                "docs/QUICKSTART.md",
                "docs/VALIDATION.md",
                "docs/SCORECARD.md",
                "docs/BENCHMARKS.md",
                "src/foundation/capabilities/README.md",
            ),
        )
        for relative in (
            "src/control-skills",
            "src/professional-skills",
            "src/foundation/capabilities",
            "src/domain-extensions",
        ):
            shutil.copytree(ROOT / relative, root / relative, dirs_exist_ok=True)

    def _current_evidence_inputs(self, root: Path) -> None:
        self._copy_paths(
            root,
            (
                "src/registry/control-skills.yaml",
                "src/registry/professional-skills.yaml",
                "src/registry/foundation-skills.yaml",
                "src/registry/domain-skills.yaml",
                "config/skill-content-exceptions.yaml",
                "config/professionalism-release-review.yaml",
                "GOVERNANCE.md",
                "docs/RELEASE.md",
                "docs/VALIDATION.md",
                "docs/SKILL_CONTENT_GOVERNANCE.md",
                "README.md",
                "docs/QUALITY_MODEL.md",
                "docs/BENCHMARKS.md",
                "docs/README.md",
                "docs/SCORECARD.md",
                "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
            ),
        )

    def test_current_projected_docs_match_core_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)

            self.assertEqual(
                [],
                self.validator._core_projection_errors(root, CORE_CONTRACTS),
            )

    def test_local_link_validation_ignores_fenced_projection_examples(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "docs" / "example.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "```markdown\n"
                "[fixture](references/not-a-doc-link.md)\n"
                "```\n",
                encoding="utf-8",
            )
            self.assertEqual([], self.validator._local_link_errors(root, path))

            path.write_text(
                path.read_text(encoding="utf-8")
                + "[missing](references/real-doc-link.md)\n",
                encoding="utf-8",
            )
            self.assertTrue(
                any(
                    "references/real-doc-link.md" in error
                    for error in self.validator._local_link_errors(root, path)
                )
            )

    def test_current_human_documentation_boundary_has_56_files(self) -> None:
        files = self.validator._markdown_files(ROOT)

        self.assertEqual(56, len(files))
        relative = {path.relative_to(ROOT).as_posix() for path in files}
        self.assertIn("CODE_OF_CONDUCT.md", relative)
        self.assertIn(".github/pull_request_template.md", relative)
        self.assertIn("reports/README.md", relative)
        self.assertIn("evals/codegen/README.md", relative)
        self.assertIn("docs/AGENT_LIGHT_ARCHITECTURE.md", relative)

    def test_legacy_architecture_path_is_a_minimal_compatibility_redirect(self) -> None:
        path = ROOT / "docs/AGENT_LIGHT_ARCHITECTURE.md"
        text = path.read_text(encoding="utf-8")

        self.assertIn("deprecated filename", text)
        self.assertIn("external-link compatibility", text)
        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertLessEqual(len(text.split()), 70)
        self.assertEqual(
            {
                "docs/HOOKLESS_ARCHITECTURE.md",
                "docs/AI_CONTROL_BOUNDARIES.md",
                "docs/OPERATING_MODEL.md",
                "docs/SUBAGENT_MODEL.md",
            },
            self.validator._resolved_local_links(ROOT, path),
        )

    def test_local_heading_anchor_validation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "guide.md"
            source = root / "README.md"
            target.write_text(
                "# Guide\n\n## Recovery And Rollback\n",
                encoding="utf-8",
            )
            source.write_text(
                "[recovery](guide.md#recovery-and-rollback)\n",
                encoding="utf-8",
            )
            self.assertEqual([], self.validator._local_link_errors(root, source))

            source.write_text(
                "[missing](guide.md#automatic-restore)\n",
                encoding="utf-8",
            )
            errors = self.validator._local_link_errors(root, source)
            self.assertTrue(any("missing local heading anchor" in error for error in errors))

    def test_heading_anchor_matches_numbered_standard_sections(self) -> None:
        anchors = self.validator._heading_anchors(
            "## 1. Purpose\n## Task, Evidence, and Completion Contracts\n"
        )

        self.assertIn("1-purpose", anchors)
        self.assertIn("task-evidence-and-completion-contracts", anchors)

    def test_installer_and_script_command_targets_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "README.md"
            path.write_text(
                "`python3 scripts/exists.py`\n"
                "`python3 installers/missing.py --dry-run`\n",
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "exists.py").write_text("", encoding="utf-8")

            errors = self.validator._command_target_errors(root, path)

            self.assertEqual(
                ["README.md: command references missing installers/missing.py"],
                errors,
            )

    def test_command_validation_reports_target_existence_not_flag_validation(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = self.validator.main(["--root", str(ROOT)])

        self.assertEqual(0, result)
        self.assertIn(
            "documented Python script/installer targets exist; "
            "command flags are not validated",
            output.getvalue(),
        )

    def test_current_stale_terms_fail_but_historical_changelog_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = root / "README.md"
            current.write_text("ChangeForge Skill Mesh\n", encoding="utf-8")
            historical = root / "CHANGELOG.md"
            historical.write_text("Historical ChangeForge Skill Mesh\n", encoding="utf-8")

            self.assertTrue(self.validator._current_term_errors(root, current))
            self.assertEqual([], self.validator._current_term_errors(root, historical))

    def test_current_volatile_documentation_facts_match_authorities(self) -> None:
        self.assertEqual([], self.validator._volatile_fact_errors(ROOT))

    def test_seeded_stale_domain_and_capability_counts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            benchmarks = root / "docs/BENCHMARKS.md"
            benchmarks.write_text(
                benchmarks.read_text(encoding="utf-8").replace(
                    "all 13 Domain Skills",
                    "all seven Domain Skills",
                    1,
                ),
                encoding="utf-8",
            )
            validation = root / "docs/VALIDATION.md"
            validation.write_text(
                validation.read_text(encoding="utf-8").replace(
                    "125 entries classify as 81 covered",
                    "124 entries classify as 80 covered",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any("docs/BENCHMARKS.md" in error and "Domain" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("docs/VALIDATION.md" in error and "125 entries" in error for error in errors),
                errors,
            )

    def test_stale_indexed_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            profiles = root / "docs/BUILD_PROFILES.md"
            changed, replacements = re.subn(
                r"\d+ registry-indexed Markdown files",
                "524 registry-indexed Markdown files",
                profiles.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any(
                    "docs/BUILD_PROFILES.md" in error
                    and "525 registry-indexed Markdown files" in error
                    for error in errors
                ),
                errors,
            )

    def test_stale_physical_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            profiles = root / "docs/BUILD_PROFILES.md"
            changed, replacements = re.subn(
                r"\d+(\s+physical Markdown files)",
                r"525\1",
                profiles.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any(
                    "docs/BUILD_PROFILES.md" in error
                    and "526 physical Markdown files" in error
                    for error in errors
                ),
                errors,
            )

    def test_stale_unindexed_template_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            profiles = root / "docs/BUILD_PROFILES.md"
            text = profiles.read_text(encoding="utf-8")
            changed, replacements = re.subn(
                r"The extra physical file is the intentionally\s+unindexed "
                r"Foundation authoring template Reference\.|"
                r"Exactly \d+ physical References? (?:is|are) unindexed",
                "Exactly 2 physical References are unindexed",
                text,
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any(
                    "docs/BUILD_PROFILES.md" in error
                    and "Exactly 1 physical Reference is unindexed" in error
                    for error in errors
                ),
                errors,
            )

    def test_reference_inventory_collector_failure_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            with mock.patch.object(
                self.validator,
                "_canonical_reference_content",
                side_effect=RuntimeError("fixture collector failure"),
            ):
                errors = self.validator._volatile_fact_errors(root)

            self.assertEqual(
                [
                    "volatile documentation authority is invalid: "
                    "canonical Reference inventory collector failed: "
                    "fixture collector failure"
                ],
                errors,
            )

    def test_historical_changelog_facts_do_not_satisfy_unreleased_projection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            changelog = root / "CHANGELOG.md"
            current = changelog.read_text(encoding="utf-8")
            stale, replacements = re.subn(
                r"233 canonical entries and 62 capability\s+entries",
                "232 canonical entries and 62 capability entries",
                current,
                count=1,
            )
            self.assertEqual(1, replacements)
            changelog.write_text(
                stale
                + "\n## Historical fixture\n\n"
                + "233 canonical entries and 62 capability entries\n",
                encoding="utf-8",
            )

            errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any(
                    "CHANGELOG.md" in error
                    and "233 canonical entries and 62 capability entries" in error
                    for error in errors
                ),
                errors,
            )

    def test_slash_skill_onboarding_is_current(self) -> None:
        self.assertEqual([], self.validator._slash_invocation_errors(ROOT))

    def test_old_non_slash_onboarding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                ("README.md", "docs/QUICKSTART.md", "docs/USAGE.md"),
            )
            usage = root / "docs/USAGE.md"
            usage.write_text(
                usage.read_text(encoding="utf-8").replace(
                    "/engineering-control-plane",
                    "Use engineering-control-plane",
                ),
                encoding="utf-8",
            )

            errors = self.validator._slash_invocation_errors(root)

            self.assertTrue(any("docs/USAGE.md" in error for error in errors), errors)

    def test_shell_fences_have_no_usage_placeholders(self) -> None:
        errors = []
        for path in self.validator._markdown_files(ROOT):
            errors.extend(self.validator._shell_fence_placeholder_errors(ROOT, path))
        self.assertEqual([], errors)

    def test_shell_fence_usage_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "README.md"
            path.write_text(
                "```bash\npython3 scripts/tool.py --reviewer <reviewer>\n```\n",
                encoding="utf-8",
            )

            errors = self.validator._shell_fence_placeholder_errors(root, path)

            self.assertTrue(any("non-executable placeholder" in error for error in errors), errors)

    def test_release_process_checks_before_refreshing_evidence(self) -> None:
        self.assertEqual([], self.validator._release_process_errors(ROOT))

    def test_unconditional_expert_panel_creation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(root, ("docs/RELEASE.md",))
            release = root / "docs/RELEASE.md"
            release.write_text(
                release.read_text(encoding="utf-8")
                + "\n## Always Refresh\n\nProduce independent expert evidence for every release.\n",
                encoding="utf-8",
            )

            errors = self.validator._release_process_errors(root)

            self.assertTrue(any("unconditionally" in error for error in errors), errors)

    def test_current_evidence_selectors_match_authoritative_configs(self) -> None:
        self.assertEqual([], self.validator._current_evidence_projection_errors(ROOT))

    def test_stale_current_evidence_selector_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            governance = root / "GOVERNANCE.md"
            current = governance.read_text(encoding="utf-8")
            self.assertIn("r26 Root lifecycle", current)
            stale = current.replace(
                "r26 Root lifecycle",
                "r25 Root lifecycle",
                1,
            )
            self.assertNotEqual(current, stale)
            governance.write_text(stale, encoding="utf-8")

            errors = self.validator._current_evidence_projection_errors(root)

            self.assertTrue(any("GOVERNANCE.md" in error for error in errors), errors)

    def test_configured_provider_behavior_proof_limit_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            validation = root / "docs/VALIDATION.md"
            validation.write_text(
                validation.read_text(encoding="utf-8").replace(
                    "provider behavior",
                    "provider semantics",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._current_evidence_projection_errors(root)

            self.assertTrue(
                any("provider behavior" in error for error in errors),
                errors,
            )

    def test_provider_proof_limit_is_derived_from_review_config(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            config = root / "config/professionalism-release-review.yaml"
            config.write_text(
                config.read_text(encoding="utf-8").replace(
                    "provider behavior",
                    "provider API behavior",
                ),
                encoding="utf-8",
            )
            for relative in (
                "README.md",
                "docs/QUALITY_MODEL.md",
                "docs/BENCHMARKS.md",
                "docs/README.md",
                "docs/RELEASE.md",
                "docs/VALIDATION.md",
                "docs/SCORECARD.md",
                "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
            ):
                path = root / relative
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "provider behavior",
                        "provider API behavior",
                    ),
                    encoding="utf-8",
                )
            quality_model = root / "docs/QUALITY_MODEL.md"
            quality_model.write_text(
                quality_model.read_text(encoding="utf-8").replace(
                    "provider API behavior",
                    "provider semantics",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._current_evidence_projection_errors(root)

            self.assertTrue(
                any("provider API behavior" in error for error in errors),
                errors,
            )

    def test_proof_limit_check_ignores_historical_documents(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            changelog = root / "CHANGELOG.md"
            changelog.write_text(
                "# Changelog\n\nHistorical fixture without provider wording.\n",
                encoding="utf-8",
            )

            errors = self.validator._current_evidence_projection_errors(root)

            self.assertFalse(
                any("CHANGELOG.md" in error for error in errors),
                errors,
            )

    def test_current_core_navigation_and_required_content_are_complete(self) -> None:
        self.assertEqual([], self.validator._navigation_errors(ROOT))
        self.assertEqual([], self.validator._required_content_errors(ROOT))

    def test_installation_matrix_is_derived_from_installer_authority(self) -> None:
        installation = (ROOT / "docs/INSTALLATION.md").read_text(encoding="utf-8")

        self.assertEqual(
            self.validator._expected_installation_matrix_rows(),
            self.validator._installation_matrix_rows(installation),
        )

    def test_wrong_supported_scope_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._installation_docs(root)
            target = root / "docs/INSTALLATION.md"
            text = target.read_text(encoding="utf-8")
            original = "| Claude | `user` | `~/.claude/skills` | `~/.claude/agents` |"
            self.assertIn(original, text)
            target.write_text(
                text.replace(
                    original,
                    "| Claude | `admin` | `~/.claude/skills` | `~/.claude/agents` |",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._required_content_errors(root)

            self.assertTrue(any("host/scope/default-target matrix" in error for error in errors), errors)

    def test_wrong_default_target_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._installation_docs(root)
            target = root / "docs/INSTALLATION.md"
            text = target.read_text(encoding="utf-8")
            original = "| Cline | `project` | `<project>/.cline/skills` | none |"
            self.assertIn(original, text)
            target.write_text(
                text.replace(
                    original,
                    "| Cline | `project` | `<project>/.cline/rules` | none |",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._required_content_errors(root)

            self.assertTrue(any("host/scope/default-target matrix" in error for error in errors), errors)

    def test_wrong_target_meaning_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._installation_docs(root)
            target = root / "docs/INSTALLATION.md"
            text = target.read_text(encoding="utf-8")
            original = "For `project`, `--target` means the project root and is required."
            self.assertIn(original, text)
            target.write_text(
                text.replace(
                    original,
                    "For `project`, `--target` means the Skill directory and is optional.",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._required_content_errors(root)

            self.assertTrue(any("missing source-backed installation fact" in error for error in errors), errors)

    def test_wrong_profile_delivery_claim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._installation_docs(root)
            target = root / "docs/INSTALLATION.md"
            text = target.read_text(encoding="utf-8")
            original = "Cline\ninstalls Skills without native Agent Profile files."
            self.assertIn(original, text)
            target.write_text(
                text.replace(
                    original,
                    "Cline\ninstalls Skills with four native Agent Profile files.",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._required_content_errors(root)

            self.assertTrue(any("missing source-backed installation fact" in error for error in errors), errors)

    def test_validation_path_surfaces_are_consistent(self) -> None:
        self.assertEqual([], self.validator._validation_path_consistency_errors(ROOT))

    def test_out_of_order_validation_path_command_is_rejected(self) -> None:
        command_sets = (
            (
                self.validator.DEVELOPMENT_AFFECTED_COMMANDS,
                "Development Affected",
            ),
            (self.validator.FULL_REGRESSION_COMMANDS, "local Full Regression"),
        )
        for source_commands, label in command_sets:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "AGENTS.md"
                commands = list(source_commands)
                commands[0], commands[1] = commands[1], commands[0]
                path.write_text("\n".join(commands), encoding="utf-8")

                errors = self.validator._ordered_command_errors(
                    path, tuple(source_commands), label
                )

                self.assertTrue(
                    any("out-of-order" in error for error in errors), errors
                )

    def _ci_errors(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ci.yml"
            path.write_text(text, encoding="utf-8")
            return self.validator._ci_affected_check_errors(path)

    def test_ci_requires_one_minimal_pull_request_job(self) -> None:
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertEqual([], self._ci_errors(text))

        mutations = {
            "push-only flow trigger": (
                text.replace("on:\n  pull_request: {}\n", "on: [push]\n", 1),
                "pull_request only",
            ),
            "block schedule trigger": (
                text.replace(
                    "on:\n  pull_request: {}\n",
                    "on:\n  pull_request: {}\n  schedule:\n",
                    1,
                ),
                "pull_request only",
            ),
            "flow workflow_dispatch trigger": (
                text.replace(
                    "on:\n  pull_request: {}\n",
                    "on: {pull_request: null, workflow_dispatch: null}\n",
                    1,
                ),
                "pull_request only",
            ),
            "pull-request path filter": (
                text.replace(
                    "on:\n  pull_request: {}\n",
                    "on:\n  pull_request:\n    paths: ['src/**']\n",
                    1,
                ),
                "must not define path filters",
            ),
            "job-name pull_request lookalike": (
                text.replace("on:\n  pull_request: {}\n", "on: {}\n", 1).replace(
                    "  pr-ci:\n", "  pull_request:\n", 1
                ),
                "pull_request only",
            ),
            "wrong job id": (
                text.replace("  pr-ci:\n", "  other:\n", 1),
                "exactly the pr-ci job",
            ),
            "matrix": (
                text.replace(
                    "    runs-on: ubuntu-latest\n",
                    "    runs-on: ubuntu-latest\n"
                    "    strategy:\n"
                    "      matrix:\n"
                    "        python-version: ['3.11']\n",
                    1,
                ),
                "must not define a matrix",
            ),
            "duplicate affected runner": (
                text.replace(
                    "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n",
                    "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n"
                    "      - run: python3 scripts/run-ci-tests.py run\n",
                    1,
                ),
                "exactly one unsharded affected-test runner",
            ),
            "duplicate affected gate": (
                text.replace(
                    "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n",
                    "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n"
                    "      - run: python3 scripts/eval-core-principles.py --gate affected "
                    "--base \"$CI_BASE_SHA\" --head \"$CI_HEAD_SHA\"\n",
                    1,
                ),
                "exactly one affected producer gate",
            ),
            "unconditional full suite": (
                text.replace(
                    "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n",
                    "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n"
                    "      - run: python3 -m unittest discover -s tests\n",
                    1,
                ),
                "unconditional Full Regression",
            ),
            "sharded runner": (
                text.replace(
                    "python3 scripts/run-ci-tests.py run",
                    "python3 scripts/run-ci-tests.py run --shard 0",
                    1,
                ),
                "unsharded",
            ),
        }
        for label, (mutated, expected) in mutations.items():
            with self.subTest(label=label):
                errors = self._ci_errors(mutated)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_ci_requires_exact_pull_request_sha_wiring(self) -> None:
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        mutations = {
            "wrong base": text.replace(
                "CI_BASE_SHA: ${{ github.event.pull_request.base.sha }}",
                "CI_BASE_SHA: ${{ github.event.pull_request.head.sha }}",
                1,
            ),
            "missing head": text.replace(
                "          CI_HEAD_SHA: ${{ github.event.pull_request.head.sha }}\n",
                "",
                1,
            ),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label):
                errors = self._ci_errors(mutated)
                self.assertTrue(
                    any("exact pull-request base/head environment" in error for error in errors),
                    errors,
                )

    def test_ci_requires_only_read_contents_permission(self) -> None:
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        permission_block = "permissions:\n  contents: read\n\n"
        mutations = {
            "absent": text.replace(permission_block, "", 1),
            "write": text.replace("  contents: read\n", "  contents: write\n", 1),
            "broader": text.replace(
                "  contents: read\n", "  contents: read\n  issues: read\n", 1
            ),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label):
                errors = self._ci_errors(mutated)
                self.assertTrue(any("contents: read only" in error for error in errors), errors)

        job_level = text.replace(permission_block, "", 1).replace(
            "  pr-ci:\n",
            "  pr-ci:\n    permissions:\n      contents: read\n",
            1,
        )
        self.assertEqual([], self._ci_errors(job_level))

    def test_ci_top_level_and_pull_request_config_are_closed(self) -> None:
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        mutations = {
            "empty sequence": (
                text.replace(
                    "on:\n  pull_request: {}\n",
                    "on:\n  pull_request: []\n",
                    1,
                ),
                "pull_request configuration must be empty",
            ),
            "opened type": (
                text.replace(
                    "on:\n  pull_request: {}\n",
                    "on:\n  pull_request:\n    types: [opened]\n",
                    1,
                ),
                "pull_request configuration must be empty",
            ),
            "main branch": (
                text.replace(
                    "on:\n  pull_request: {}\n",
                    "on:\n  pull_request:\n    branches: [main]\n",
                    1,
                ),
                "pull_request configuration must be empty",
            ),
            "top-level env": (
                text.replace(
                    "jobs:\n",
                    "env:\n  PYTHONPATH: scripts\n\njobs:\n",
                    1,
                ),
                "closed top-level workflow keys",
            ),
            "top-level defaults": (
                text.replace(
                    "jobs:\n",
                    "defaults:\n  run:\n    shell: python\n\njobs:\n",
                    1,
                ),
                "closed top-level workflow keys",
            ),
        }
        for label, (mutated, expected) in mutations.items():
            with self.subTest(label=label):
                errors = self._ci_errors(mutated)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_ci_steps_are_a_closed_ordered_six_step_sequence(self) -> None:
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        no_write = "        run: git diff --exit-code --no-ext-diff --no-textconv HEAD --\n"
        checkout = (
            "      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 0\n"
            "          ref: ${{ github.event.pull_request.head.sha }}\n"
        )
        setup = (
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: \"3.11\"\n"
        )
        mutations = {
            "extra vendor action": (
                text.replace(
                no_write,
                no_write + "      - uses: vendor/extra-action@v1\n",
                1,
                ),
                "exact closed six-step order",
            ),
            "extra run": (
                text.replace(
                no_write,
                no_write + "      - run: echo unexpected\n",
                1,
                ),
                "exact closed six-step order",
            ),
            "wrong order": (
                text.replace(checkout + setup, setup + checkout, 1),
                "exact closed six-step order",
            ),
            "wrong checkout action ref": (
                text.replace("actions/checkout@v4", "actions/checkout@feature", 1),
                "exact closed six-step order",
            ),
            "wrong setup action ref": (
                text.replace("actions/setup-python@v5", "actions/setup-python@main", 1),
                "exact closed six-step order",
            ),
            "job if": (
                text.replace(
                    "    runs-on: ubuntu-latest\n",
                    "    runs-on: ubuntu-latest\n    if: false\n",
                    1,
                ),
                "closed pr-ci job keys",
            ),
            "job continue-on-error": (
                text.replace(
                    "    runs-on: ubuntu-latest\n",
                    "    runs-on: ubuntu-latest\n    continue-on-error: true\n",
                    1,
                ),
                "closed pr-ci job keys",
            ),
            "step if": (
                text.replace(no_write, no_write + "        if: false\n", 1),
                "exact closed six-step order",
            ),
            "step continue-on-error": (
                text.replace(
                    no_write,
                    no_write + "        continue-on-error: true\n",
                    1,
                ),
                "exact closed six-step order",
            ),
        }
        for label, (mutated, expected) in mutations.items():
            with self.subTest(label=label):
                errors = self._ci_errors(mutated)
                self.assertTrue(
                    any(expected in error for error in errors),
                    errors,
                )

    def test_completion_term_drift_fails_docs_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            target = root / "docs" / "SUBAGENT_MODEL.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace(
                    "validation-failed -> blocked | partial",
                    "validation-failed -> partial",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._core_projection_errors(root, CORE_CONTRACTS)

            self.assertTrue(
                any(
                    "exact ordered Core Model rendering" in error
                    for error in errors
                ),
                errors,
            )

    def test_conflicting_completion_rule_outside_projection_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            target = root / "docs" / "SUBAGENT_MODEL.md"
            target.write_text(
                target.read_text(encoding="utf-8")
                + "\nContradictory policy: validation-failed -> completed.\n",
                encoding="utf-8",
            )

            errors = self.validator._core_projection_errors(root, CORE_CONTRACTS)

            self.assertTrue(
                any("validation-failed" in error and "duplicated" in error for error in errors),
                errors,
            )

    def test_extra_task_field_outside_projection_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            target = root / "docs" / "SUBAGENT_MODEL.md"
            target.write_text(
                target.read_text(encoding="utf-8")
                + "\nExtra task field: Runtime Identity.\n",
                encoding="utf-8",
            )

            errors = self.validator._core_projection_errors(root, CORE_CONTRACTS)

            self.assertTrue(
                any("field declarations are forbidden" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("runtime identity is forbidden" in error for error in errors),
                errors,
            )

    def test_duplicate_managed_projection_block_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            projection = CORE_CONTRACTS["docs_contract"]["projections"][0]
            target = root / projection["path"]
            begin = (
                "<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: "
                f"{projection['id']} -->"
            )
            end = (
                "<!-- END CHANGEFORGE CORE DOCS PROJECTION: "
                f"{projection['id']} -->"
            )
            text = target.read_text(encoding="utf-8")
            block = text[text.index(begin) : text.index(end) + len(end)]
            target.write_text(text + "\n" + block + "\n", encoding="utf-8")

            errors = self.validator._core_projection_errors(root, CORE_CONTRACTS)

            self.assertTrue(
                any("markers must each appear exactly once" in error for error in errors),
                errors,
            )

    def test_canonical_block_plus_reviewer_attack_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            target = root / "docs" / "OPERATING_MODEL.md"
            target.write_text(
                target.read_text(encoding="utf-8")
                + "\nContradictory policy: validation-failed -> completed.\n"
                + "Extra task field: Runtime Identity.\n",
                encoding="utf-8",
            )

            errors = self.validator._core_projection_errors(root, CORE_CONTRACTS)

            self.assertTrue(
                any("exact ordered Core Model rendering" in error for error in errors),
                errors,
            )

    def test_paraphrased_outside_conflicts_fail_whole_document_binding(self) -> None:
        additions = (
            "If tests fail, the work may still be completed.",
            "When review is absent, closure can still report completed.",
            "A task additionally carries Runtime ID.",
        )
        for addition in additions:
            with self.subTest(addition=addition), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._projected_docs(root)
                target = root / "docs" / "SUBAGENT_MODEL.md"
                target.write_text(
                    target.read_text(encoding="utf-8") + f"\n{addition}\n",
                    encoding="utf-8",
                )

                errors = self.validator._core_projection_errors(
                    root, CORE_CONTRACTS
                )

                self.assertTrue(
                    any("whole-document SHA-256" in error for error in errors),
                    errors,
                )

    def test_document_fingerprint_must_be_lowercase_sha256(self) -> None:
        mutated = copy.deepcopy(CORE_CONTRACTS)
        mutated["docs_contract"]["projections"][0]["document_sha256"] = "ABC"

        errors = validate_core_contracts(mutated)

        self.assertTrue(
            any("document_sha256 must be lowercase SHA-256" in error for error in errors),
            errors,
        )

    def test_context_budget_projection_derives_main_evolution_target(self) -> None:
        contract = CORE_CONTRACTS["context_budget_contract"]
        self.assertNotIn("release_target", contract["budget_classes"]["main"])
        self.assertNotIn("evolution_target", contract["budget_classes"]["main"])
        self.assertEqual(
            80,
            contract["budget_classes"]["main"][
                "minimum_release_margin_tokens"
            ],
        )
        projection = CORE_CONTRACTS["docs_contract"][
            "context_budget_projections"
        ][0]
        rendered = self.validator.context_budget_docs_projection_block(
            CORE_CONTRACTS,
            projection,
        )
        self.assertIn(
            "| Main always-loaded | 2200 | 0.10 | 220 | 1980 | 80 | 1900 |",
            rendered,
        )

    def test_context_budget_projection_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            target = root / "docs" / "VALIDATION.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "| Main always-loaded | 2200 | 0.10 | 220 | 1980 | 80 | 1900 |",
                    "| Main always-loaded | 2200 | 0.10 | 220 | 1980 | 0 | 1980 |",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._core_projection_errors(root, CORE_CONTRACTS)

            self.assertTrue(
                any("context budget projection" in error for error in errors),
                errors,
            )

    def test_governance_budget_authority_uses_current_report_ssot(self) -> None:
        self.assertEqual(
            [],
            self.validator._governance_context_budget_errors(
                ROOT,
                CORE_CONTRACTS,
            ),
        )

    def test_governance_current_budget_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._governance_budget_inputs(root)
            governance = root / "GOVERNANCE.md"
            governance.write_text(
                governance.read_text(encoding="utf-8")
                + "\nCurrent rendered Main maximum is 9999/1900 tokens.\n",
                encoding="utf-8",
            )

            errors = self.validator._governance_context_budget_errors(
                root,
                CORE_CONTRACTS,
            )

            self.assertTrue(
                any("must not copy current rendered measurements" in error for error in errors),
                errors,
            )

    def test_governance_fixed_ceiling_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._governance_budget_inputs(root)
            governance = root / "GOVERNANCE.md"
            governance.write_text(
                governance.read_text(encoding="utf-8").replace(
                    "| Main always-loaded | 2200 |",
                    "| Main always-loaded | 2199 |",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._governance_context_budget_errors(
                root,
                CORE_CONTRACTS,
            )

            self.assertTrue(
                any("fixed ceiling authority block" in error for error in errors),
                errors,
            )

    def test_governance_budget_report_must_exist_pass_and_match_core(self) -> None:
        mutations = ("missing", "failed-status", "wrong-ceiling")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._governance_budget_inputs(root)
                report_path = root / "reports" / "rendered-context-budget.json"
                if mutation == "missing":
                    report_path.unlink()
                else:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    if mutation == "failed-status":
                        report["status"] = "fail"
                    else:
                        report["budget_calibration"]["capacity_ceilings"]["main"] = 2199
                    report_path.write_text(
                        json.dumps(report),
                        encoding="utf-8",
                    )

                errors = self.validator._governance_context_budget_errors(
                    root,
                    CORE_CONTRACTS,
                )

                self.assertTrue(
                    any("rendered context budget report" in error for error in errors),
                    errors,
                )

    def test_governance_current_evidence_uses_source_test_and_report_authorities(
        self,
    ) -> None:
        self.assertEqual(
            [],
            self.validator._governance_evidence_freshness_errors(ROOT),
        )

    def test_governance_volatile_current_evidence_snapshots_are_rejected(self) -> None:
        snapshots = (
            "The Core contract projects through 8 exact rules.",
            "The Task Profile has 25 action-first rules.",
            "The Task Profile remains at 25 rules.",
            "The Task Profile contains 25 rules.",
            "The Task Profile uses 25 rules.",
            "The complete lightweight utility module passed all 84 tests.",
            "The current mutation matrix covers 2-path × 6-guard combinations.",
        )
        for snapshot in snapshots:
            with self.subTest(snapshot=snapshot), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                governance = self._governance_evidence_input(root)
                governance.write_text(
                    governance.read_text(encoding="utf-8") + f"\n{snapshot}\n",
                    encoding="utf-8",
                )

                errors = self.validator._governance_evidence_freshness_errors(root)

                self.assertTrue(
                    any("volatile current evidence snapshot" in error for error in errors),
                    errors,
                )

    def test_governance_freshness_authority_links_are_required(self) -> None:
        authority_targets = (
            "src/control-model/core-contracts.json",
            "src/agent-profiles/role-agents.json",
            "tests/scripts/test_validate_agent_profiles.py",
            "tests/scripts/test_eval_agent_lightweight_utility.py",
            "reports/installation-validation.json",
        )
        for target in authority_targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                governance = self._governance_evidence_input(root)
                governance.write_text(
                    governance.read_text(encoding="utf-8").replace(
                        f"]({target})",
                        "](GOVERNANCE.md)",
                    ),
                    encoding="utf-8",
                )

                errors = self.validator._governance_evidence_freshness_errors(root)

                self.assertTrue(
                    any(target in error for error in errors),
                    errors,
                )

    def test_governance_digest_evidence_must_remain_historical_and_non_current(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            governance = self._governance_evidence_input(root)
            governance.write_text(
                governance.read_text(encoding="utf-8").replace(
                    "**Historical, non-current resolution evidence:**",
                    "**Resolution evidence:**",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._governance_evidence_freshness_errors(root)

            self.assertTrue(
                any("historical, non-current" in error.casefold() for error in errors),
                errors,
            )

    def test_projection_cannot_drop_a_required_contract_binding(self) -> None:
        mutated = copy.deepcopy(CORE_CONTRACTS)
        projection = mutated["docs_contract"]["projections"][0]
        projection["bindings"] = [
            binding
            for binding in projection["bindings"]
            if not binding["source_path"].startswith("completion_state.")
        ]

        errors = validate_core_contracts(mutated)

        self.assertTrue(
            any("bindings must cover exactly" in error for error in errors),
            errors,
        )

    def test_projection_rejects_an_unknown_renderer(self) -> None:
        mutated = copy.deepcopy(CORE_CONTRACTS)
        mutated["docs_contract"]["projections"][0]["bindings"][0][
            "render"
        ] = "copied-text"

        errors = validate_core_contracts(mutated)

        self.assertTrue(
            any(".render is invalid" in error for error in errors),
            errors,
        )

    def test_single_source_acceptance_cannot_drop_docs_validation(self) -> None:
        mutated = copy.deepcopy(CORE_CONTRACTS)
        principle = next(
            item
            for item in mutated["core_principles"]
            if item["id"] == "single-source-of-truth"
        )
        principle["required_outcomes"]["authoring"].remove("docs-exact-valid")

        errors = validate_core_contracts(mutated)

        self.assertTrue(
            any("outcomes contain orphans" in error for error in errors),
            errors,
        )

    def test_professional_formal_docs_do_not_regress_to_schema_two(self) -> None:
        paths = (
            ROOT / "AGENTS.md",
            ROOT / ".github/pull_request_template.md",
            ROOT / "docs/RELEASE.md",
            ROOT / "docs/SKILL_CONTENT_GOVERNANCE.md",
            ROOT / "docs/VALIDATION.md",
            ROOT
            / "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
            ROOT / "reports/professionalism-regression-report.md",
        )
        forbidden = (
            "professional completeness panel is schema 2",
            "professional-completeness schema-2 review is current",
            "professional completeness is schema-2 panel-majority-current",
            "professional completeness schema-2 evidence binds",
            "formal release requires a checked-in schema-2 professional",
            "schema 2 has no arbitration or override",
        )
        failures = []
        for path in paths:
            text = path.read_text(encoding="utf-8").casefold()
            for phrase in forbidden:
                if phrase in text:
                    failures.append(f"{path.relative_to(ROOT)}: {phrase}")
        self.assertEqual([], failures)

    def test_packaging_and_lifecycle_authorities_are_required(self) -> None:
        self.assertTrue(
            {
                "docs/BUILD_PROFILES.md",
                "docs/INSTALLATION.md",
                "docs/RELEASE.md",
                "docs/SKILL_CONTENT_GOVERNANCE.md",
                "docs/VALIDATION.md",
            }.issubset(self.validator.REQUIRED_DOCS)
        )


if __name__ == "__main__":
    unittest.main()
