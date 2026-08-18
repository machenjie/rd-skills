from __future__ import annotations

import copy
import io
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
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
                "AGENTS.md",
                "GOVERNANCE.md",
                ".github/pull_request_template.md",
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
                "526 registry-indexed Markdown files",
                profiles.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            errors = self.validator._volatile_fact_errors(root)

            self.assertIn(
                "docs/BUILD_PROFILES.md: missing authority-derived current fact "
                "'527 registry-indexed Markdown files and 528 physical Markdown files'",
                errors,
            )

    def test_stale_physical_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._volatile_fact_inputs(root)
            profiles = root / "docs/BUILD_PROFILES.md"
            changed, replacements = re.subn(
                r"\d+(\s+physical Markdown files)",
                r"527\1",
                profiles.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            errors = self.validator._volatile_fact_errors(root)

            self.assertIn(
                "docs/BUILD_PROFILES.md: missing authority-derived current fact "
                "'527 registry-indexed Markdown files and 528 physical Markdown files'",
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

    def test_public_project_metadata_uses_rd_skills_brand(self) -> None:
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertEqual("rd-skills", project["name"])
        self.assertEqual([{"name": "rd-skills"}], project["authors"])
        self.assertEqual(
            "Authoring, validation, build, packaging, and installation tools "
            "for rd-skills professional skills.",
            project["description"],
        )

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

    def test_fixed_current_evidence_requires_all_three_exact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)

            authority = self.validator._current_evidence_authority(root)

            self.assertEqual(
                {
                    "non_control",
                    "canonical_fixed_paths",
                    "migration_state",
                    "fixed_paths",
                },
                set(authority),
            )
            self.assertEqual("current", authority["migration_state"])
            self.assertTrue(authority["canonical_fixed_paths"])
            self.assertEqual(
                {
                    "readability": "evals/expert-panel/readability.json",
                    "semantic-disposition": (
                        "evals/expert-panel/semantic-disposition.json"
                    ),
                    "professional-completeness": (
                        "evals/expert-panel/professional-completeness.json"
                    ),
                },
                authority["fixed_paths"],
            )

    def test_fixed_current_evidence_rejects_reintroduced_root_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            exceptions = root / "config/skill-content-exceptions.yaml"
            text = exceptions.read_text(encoding="utf-8")
            exceptions.write_text(
                text.replace(
                    "  schema_version: 7\n",
                    "  schema_version: 7\n  lifecycle: {}\n",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._current_evidence_projection_errors(root)

            self.assertTrue(
                any("current evidence authority is invalid" in error for error in errors),
                errors,
            )

    def test_malformed_or_incomplete_evidence_authority_is_rejected(self) -> None:
        cases = (
            (
                "missing panel identity",
                "config/professionalism-release-review.yaml",
                "  panel_kind: readability\n",
                "  panel_kind: \n",
            ),
        )
        for label, relative, value_key, malformed in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._current_evidence_inputs(root)
                original = "  panel_kind: readability\n"
                replacement = "  panel_kind: \n"
                path = root / relative
                text = path.read_text(encoding="utf-8")
                self.assertIn(original, text)
                path.write_text(
                    text.replace(original, replacement, 1),
                    encoding="utf-8",
                )

                errors = self.validator._current_evidence_projection_errors(root)

                self.assertTrue(
                    any("current evidence authority is invalid" in error for error in errors),
                    errors,
                )

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            review_config = root / "config/professionalism-release-review.yaml"
            text = review_config.read_text(encoding="utf-8")
            anchor = "  scope: ai-readability-and-density\n"
            self.assertIn(anchor, text)
            review_config.write_text(
                text.replace(
                    anchor,
                    anchor + "  extra_authority: unexpected\n",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._current_evidence_projection_errors(root)

            self.assertTrue(
                any("selector-free schema 5" in error for error in errors),
                errors,
            )

    def test_stale_current_evidence_projection_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._current_evidence_inputs(root)
            governance = root / "GOVERNANCE.md"
            current = governance.read_text(encoding="utf-8")
            authority = "Canonical fixed-attestation paths"
            self.assertIn(authority, current)
            stale = current.replace(
                authority,
                "Legacy configured evidence paths",
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

    def test_parallel_full_runner_is_the_unique_official_unittest_command(self) -> None:
        official = (
            "python3 scripts/run-ci-tests.py full --jobs 4 --timeout 900"
        )
        legacy = "python3 -m unittest discover -s tests"
        self.assertEqual(official, self.validator.FULL_REGRESSION_COMMANDS[9])
        for relative in ("AGENTS.md", "docs/VALIDATION.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(1, text.count(official), relative)
            self.assertNotIn(legacy, text, relative)

        validation = (ROOT / "docs/VALIDATION.md").read_text(encoding="utf-8")
        stale_marker = "opt" + "-in"
        self.assertNotIn(stale_marker, validation.casefold())
        self.assertNotIn("replace `python3 -m unittest discover -s tests`", validation)
        self.assertIn("`full-regression`", validation)

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

    def test_duplicate_validation_path_command_is_rejected(self) -> None:
        commands = self.validator.FULL_REGRESSION_COMMANDS
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "AGENTS.md"
            path.write_text(
                "\n".join((*commands, commands[-1])),
                encoding="utf-8",
            )

            errors = self.validator._ordered_command_errors(
                path, commands, "local Full Regression"
            )

            self.assertTrue(
                any("exactly once" in error for error in errors), errors
            )

    def test_retired_workflow_paths_must_remain_absent(self) -> None:
        self.assertEqual([], self.validator._retired_workflow_contract_errors(ROOT))

        for relative in self.validator.RETIRED_WORKFLOW_PATHS:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("name: forbidden\n", encoding="utf-8")

                errors = self.validator._retired_workflow_contract_errors(root)

                self.assertTrue(
                    any(f"retired workflow must remain absent: {relative}" in error for error in errors),
                    errors,
                )

    def test_retired_remote_required_claims_are_rejected(self) -> None:
        claims = {
            "CONTRIBUTING.md": "Pull-request CI applies Development Affected in one pr-ci job.\n",
            "docs/RELEASE.md": "The remote `Formal Release` workflow must pass for the same object ID.\n",
        }
        for relative, claim in claims.items():
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(claim, encoding="utf-8")

                errors = self.validator._retired_workflow_contract_errors(root)

                self.assertTrue(
                    any("retired remote-execution claim" in error for error in errors),
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

    def test_ordinary_prose_outside_managed_sections_does_not_drift(self) -> None:
        projections = (
            *CORE_CONTRACTS["docs_contract"]["projections"],
            *CORE_CONTRACTS["docs_contract"]["context_budget_projections"],
        )
        for projection in projections:
            with (
                self.subTest(path=projection["path"]),
                tempfile.TemporaryDirectory() as raw,
            ):
                root = Path(raw)
                self._projected_docs(root)
                target = root / projection["path"]
                text = target.read_text(encoding="utf-8")
                heading = f"## {projection['section']}"
                self.assertIn(heading, text)
                target.write_text(
                    text.replace(
                        heading,
                        "## Ordinary Maintenance Note\n\n"
                        "This explanatory prose is outside the managed projection.\n\n"
                        + heading,
                        1,
                    ),
                    encoding="utf-8",
                )

                self.assertEqual(
                    [],
                    self.validator._core_projection_errors(root, CORE_CONTRACTS),
                )

    def test_governed_docs_reject_legacy_whole_document_hash_keys(self) -> None:
        mutated = copy.deepcopy(CORE_CONTRACTS)
        projections = (
            *mutated["docs_contract"]["projections"],
            *mutated["docs_contract"]["context_budget_projections"],
        )
        for projection in projections:
            projection["document_sha256"] = "0" * 64

        errors = validate_core_contracts(mutated)

        self.assertTrue(
            any(
                "fields must be exactly" in error and "document_sha256" in error
                for error in errors
            ),
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

    def test_compact_expert_panel_storage_contract_is_canonical(self) -> None:
        paths = (
            ROOT / "AGENTS.md",
            ROOT / "GOVERNANCE.md",
            ROOT / ".github/pull_request_template.md",
            ROOT / "docs/RELEASE.md",
            ROOT / "docs/SKILL_CONTENT_GOVERNANCE.md",
            ROOT / "docs/VALIDATION.md",
            ROOT
            / "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md",
        )
        current_inventory = (
            "`evals/expert-panel/readability.json`",
            "`evals/expert-panel/semantic-disposition.json`",
            "`evals/expert-panel/professional-completeness.json`",
        )
        runtime_root = "`.rd-skills/expert-panel/<run-id>/`"
        forbidden = (
            "full round chain",
            "round-chain closure",
            "one unforked checked-in round chain",
            "never overwrite an accepted ballot or predecessor",
            "evals/expert-panel/review_id/",
            "evals/expert-panel/prior_",
        )
        failures = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            normalized = text.casefold()
            if any(item not in text for item in current_inventory):
                failures.append(
                    f"{path.relative_to(ROOT)}: missing exact compact inventory"
                )
            if runtime_root not in text:
                failures.append(
                    f"{path.relative_to(ROOT)}: missing ignored runtime root"
                )
            for phrase in forbidden:
                if phrase in normalized:
                    failures.append(f"{path.relative_to(ROOT)}: {phrase}")

        owner = (ROOT / "docs/SKILL_CONTENT_GOVERNANCE.md").read_text(
            encoding="utf-8"
        )
        for term in (
            "4 MiB",
            "replacement, not append",
            "Git history",
            "optional CI or Release artifact",
            "no keep-last-N",
            "origin_review_id",
            "origin_commit",
            "origin_verdict_digest",
            "source_fingerprint",
        ):
            if term not in owner:
                failures.append(f"docs/SKILL_CONTENT_GOVERNANCE.md: {term}")
        authority = self.validator._current_evidence_authority(ROOT)
        tracked = set(
            subprocess.run(
                ["git", "ls-files", "--", "evals/expert-panel"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
        canonical = {
            "evals/expert-panel/readability.json",
            "evals/expert-panel/semantic-disposition.json",
            "evals/expert-panel/professional-completeness.json",
        }
        if authority["migration_state"] != "current":
            failures.append("expert evidence selectors are not current")
        if tracked != canonical:
            failures.append(
                "tracked expert-panel inventory is not the exact current set"
            )
        self.assertEqual([], failures)

    def test_packaging_and_release_authorities_are_required(self) -> None:
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
