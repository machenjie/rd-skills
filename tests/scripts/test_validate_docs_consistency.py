from __future__ import annotations

import copy
import io
import importlib.util
import json
import os
import re
import shlex
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

    def test_retry_carries_domain_and_full_contract_bindings(
        self,
    ) -> None:
        operating_model = (ROOT / "docs" / "OPERATING_MODEL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "complete unchanged Task Contract, including Professional Skill, Domain, "
            "Layer3",
            " ".join(operating_model.split()),
        )

    def _copy_paths(self, root: Path, relatives: tuple[str, ...]) -> None:
        for relative in relatives:
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    def _synthetic_volatile_authority(self) -> dict[str, object]:
        return {
            "counts": {
                "control": 1,
                "professional": 2,
                "foundation": 3,
                "domain": 2,
            },
            "total": 8,
            "non_control": 7,
            "runtime_top_level_count": 3,
            "runtime_delivery": {"targeted": 4, "routing_only": 1},
            "routing_case_count": 5,
            "capability_routing_case_count": 2,
            "admission_case_count": 4,
            "admission_counts": {
                "professional": 1,
                "foundation": 2,
                "domain": 1,
            },
            "foundation_candidate_count": 2,
            "layer3_catalog_count": 5,
            "matrix_entry_count": 4,
            "coverage_counts": {
                "covered": 1,
                "partial": 1,
                "missing": 1,
                "intentionally-unsupported": 1,
            },
            "reference_inventory": {
                "indexed": 2,
                "physical": 3,
                "unindexed_templates": 1,
            },
        }

    def _volatile_fact_inputs(
        self, root: Path, authority: dict[str, object]
    ) -> dict[str, tuple[str, ...]]:
        projections = self.validator._required_volatile_projections(authority)
        for relative, facts in projections.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            body = "\n".join(facts) + "\n"
            if relative == "CHANGELOG.md":
                body = "# Changelog\n\n## Unreleased\n\n" + body
            path.write_text(body, encoding="utf-8")
        return projections

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

    def test_human_documentation_boundary_keeps_required_owners(self) -> None:
        files = self.validator._markdown_files(ROOT)

        relative = {path.relative_to(ROOT).as_posix() for path in files}
        self.assertIn("CODE_OF_CONDUCT.md", relative)
        self.assertIn(".github/pull_request_template.md", relative)
        self.assertIn("reports/README.md", relative)
        self.assertIn("evals/codegen/README.md", relative)
        self.assertIn("docs/AGENT_LIGHT_ARCHITECTURE.md", relative)
        self.assertNotIn("docs/ROUTING_EXAMPLES.md", relative)

    def test_beginner_product_surface_hides_internal_protocol(self) -> None:
        self.assertEqual([], self.validator._product_surface_errors(ROOT))

    def test_readme_first_surface_internal_term_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(root, ("README.md",))
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "rd-skills",
                    "rd-skills Runtime",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._product_surface_errors(root)

            self.assertTrue(any("first product surface" in error for error in errors), errors)

    def test_readme_first_surface_boundary_does_not_require_an_image(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            readme = root / "README.md"
            readme.write_text(
                "# rd-skills\n\n"
                "A plain-language engineering assistant.\n\n"
                "## Why it helps\n\n"
                "It scopes and verifies changes.\n\n"
                "## Maintainer details\n\n"
                "Runtime internals live outside the beginner surface.\n",
                encoding="utf-8",
            )

            self.assertEqual([], self.validator._product_surface_errors(root))

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

    def test_generated_document_ownership_uses_declared_producer(self) -> None:
        self.assertEqual([], self.validator._generated_document_ownership_errors(ROOT))

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                (
                    "docs/SHOWCASE.md",
                    "docs/MARKETPLACE_CATALOG.md",
                    "scripts/generate-examples-showcase.py",
                    "scripts/generate-marketplace-catalog.py",
                ),
            )
            showcase = root / "docs/SHOWCASE.md"
            showcase.write_text(
                showcase.read_text(encoding="utf-8").replace(
                    "Do not edit by hand.",
                    "Generated output.",
                    1,
                ),
                encoding="utf-8",
            )
            errors = self.validator._generated_document_ownership_errors(root)
            self.assertTrue(any("SHOWCASE.md" in error for error in errors), errors)

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
        with mock.patch.object(
            self.validator,
            "validate_docs_consistency",
            return_value=[],
        ), mock.patch.object(
            self.validator,
            "_markdown_files",
            return_value=[Path("README.md")],
        ), redirect_stdout(output):
            result = self.validator.main(["--root", str(ROOT)])

        self.assertEqual(0, result)
        self.assertIn(
            "documented Python script/installer targets exist; retired Runtime "
            "flags are rejected on public and authoring surfaces",
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
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authority = self._synthetic_volatile_authority()
            self._volatile_fact_inputs(root, authority)
            with mock.patch.object(
                self.validator, "_volatile_fact_authority", return_value=authority
            ):
                self.assertEqual([], self.validator._volatile_fact_errors(root))

    def test_current_runtime_surfaces_are_profile_choice_free(self) -> None:
        self.assertEqual([], self.validator._runtime_surface_errors(ROOT))

    def test_public_profile_selection_is_rejected_but_legacy_migration_input_is_allowed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            readme = root / "README.md"
            readme.write_text(
                "Run `python3 scripts/build.py --profile full`.\n",
                encoding="utf-8",
            )
            migration = root / "docs/MIGRATING_TO_HOOKLESS.md"
            migration.parent.mkdir(parents=True)
            migration.write_text(
                "Legacy `full` and `dev` manifests are accepted migration inputs.\n",
                encoding="utf-8",
            )

            errors = self.validator._runtime_surface_errors(root)

            self.assertEqual(
                ["README.md: removed Runtime flag remains: --profile"],
                errors,
            )

    def test_pull_request_template_cannot_restore_runtime_profile_choices(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            template = root / ".github/pull_request_template.md"
            template.parent.mkdir(parents=True)
            template.write_text(
                "Build profiles affected: `recommended` / `full` / `dev` / none\n",
                encoding="utf-8",
            )

            errors = self.validator._runtime_surface_errors(root)

            self.assertEqual(
                [
                    ".github/pull_request_template.md: retired user-facing "
                    "Runtime Profile choice remains"
                ],
                errors,
            )

    def test_all_public_and_authoring_runtime_surfaces_reject_profile_choices(
        self,
    ) -> None:
        stale = {
            "pyproject.toml": (
                "[tool.changeforge.profiles]\n"
                'recommended = "runtime"\nfull = "runtime"\ndev = "runtime"\n'
            ),
            "Makefile": (
                "doctor-codex:\n"
                "\tpython3 installers/doctor.py --agent codex --scope user "
                "--profile recommended\n"
            ),
            "SUPPORT.md": "Selected profile: recommended, full, or dev.\n",
            ".github/ISSUE_TEMPLATE/bug_report.md": (
                "Profile: recommended / full / dev\n"
            ),
            ".github/ISSUE_TEMPLATE/feature_request.md": (
                "Profile impact: recommended / full / dev / none\n"
            ),
            ".github/ISSUE_TEMPLATE/skill_change.md": (
                "## Routing or Build Profile Impact\n"
            ),
            "src/foundation/capabilities/README.md": (
                "Foundation entries are emitted by the recommended, full, and "
                "dev build profiles.\n"
            ),
            (
                "src/foundation/capabilities/repository-context-map/references/"
                "source-generated-boundary-map.md"
            ): "| Build profile | Recommended, full, dev, or installed output. |\n",
            (
                "src/foundation/capabilities/skill-authoring-expert/references/"
                "evidence-patterns.md"
            ): "Run the dev/recommended build when the build profile matters.\n",
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for relative, text in stale.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

            errors = self.validator._runtime_surface_errors(root)

            self.assertEqual(
                set(stale),
                {error.split(":", 1)[0] for error in errors},
                errors,
            )

    def test_retired_runtime_surface_guard_names_each_profile_authority(self) -> None:
        required = {
            "src/foundation/capabilities/skill-authoring-expert/SKILL.md",
            (
                "src/foundation/capabilities/skill-efficacy-benchmark/"
                "references/benchmarks-and-patterns.md"
            ),
            (
                "src/foundation/capabilities/skill-efficacy-benchmark/"
                "references/evidence-patterns.md"
            ),
        }

        self.assertTrue(
            required.issubset(set(self.validator.RUNTIME_SURFACE_FILES)),
            set(self.validator.RUNTIME_SURFACE_FILES),
        )

    def test_each_profile_authority_rejects_restored_ambiguous_runtime_wording(
        self,
    ) -> None:
        stale = {
            "src/foundation/capabilities/skill-authoring-expert/SKILL.md": (
                "Change routing, references, registries, profile delivery, or "
                "Skill validation.\n"
            ),
            (
                "src/foundation/capabilities/skill-efficacy-benchmark/"
                "references/benchmarks-and-patterns.md"
            ): "Same task, profile, build profile, and source-vs-dist boundary.\n",
            (
                "src/foundation/capabilities/skill-efficacy-benchmark/"
                "references/evidence-patterns.md"
            ): "Test the final build-profile output rather than source alone.\n",
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for relative, text in stale.items():
                with self.subTest(relative=relative):
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")

                    errors = self.validator._runtime_surface_errors(root)

                    self.assertEqual(
                        [
                            f"{relative}: retired user-facing Runtime Profile "
                            "choice remains"
                        ],
                        errors,
                    )
                    path.unlink()

    def test_every_removed_runtime_flag_is_rejected_on_public_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            makefile = root / "Makefile"
            for flag in (
                "--profile",
                "--with-hooks",
                "--without-hooks",
                "--hook-profile",
                "--professional-injection",
                "--activation-level",
            ):
                with self.subTest(flag=flag):
                    makefile.write_text(
                        "doctor-codex:\n"
                        "\tpython3 installers/doctor.py --agent codex "
                        f"--scope user {flag}\n",
                        encoding="utf-8",
                    )
                    errors = self.validator._runtime_surface_errors(root)
                    self.assertTrue(
                        any(flag in error for error in errors),
                        errors,
                    )

    def test_make_doctor_recipe_is_accepted_by_current_doctor_parser(self) -> None:
        dry_run = subprocess.run(
            ["make", "-n", "doctor-codex"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(0, dry_run.returncode, dry_run.stderr)
        argv = shlex.split(dry_run.stdout.strip())
        self.assertTrue(argv)
        if argv[0] == "python3":
            argv[0] = sys.executable
        parsed = subprocess.run(
            argv,
            cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertNotEqual(2, parsed.returncode, parsed.stderr)
        self.assertNotIn("unrecognized arguments", parsed.stderr)

    def test_seeded_stale_domain_and_capability_counts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authority = self._synthetic_volatile_authority()
            projections = self._volatile_fact_inputs(root, authority)
            benchmarks = root / "docs/BENCHMARKS.md"
            domain_fact = projections["docs/BENCHMARKS.md"][0]
            benchmarks.write_text(
                benchmarks.read_text(encoding="utf-8").replace(
                    domain_fact,
                    "all 3 Domain Skills",
                    1,
                ),
                encoding="utf-8",
            )
            validation = root / "docs/VALIDATION.md"
            matrix_fact = projections["docs/VALIDATION.md"][-2]
            validation.write_text(
                validation.read_text(encoding="utf-8").replace(
                    matrix_fact,
                    "4 entries classify as 2 covered, 1 partial, 1 missing, "
                    "and 0 intentionally unsupported",
                    1,
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                self.validator, "_volatile_fact_authority", return_value=authority
            ):
                errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any("docs/BENCHMARKS.md" in error and domain_fact in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("docs/VALIDATION.md" in error and matrix_fact in error for error in errors),
                errors,
            )

    def test_stale_indexed_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authority = self._synthetic_volatile_authority()
            projections = self._volatile_fact_inputs(root, authority)
            profiles = root / "docs/BUILD_PROFILES.md"
            expected = projections["docs/BUILD_PROFILES.md"][-2]
            changed, replacements = re.subn(
                r"\d+ registry-indexed Markdown files",
                "1 registry-indexed Markdown files",
                profiles.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            with mock.patch.object(
                self.validator, "_volatile_fact_authority", return_value=authority
            ):
                errors = self.validator._volatile_fact_errors(root)

            self.assertIn(
                "docs/BUILD_PROFILES.md: missing authority-derived current fact "
                f"{expected!r}",
                errors,
            )

    def test_stale_physical_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authority = self._synthetic_volatile_authority()
            projections = self._volatile_fact_inputs(root, authority)
            profiles = root / "docs/BUILD_PROFILES.md"
            expected = projections["docs/BUILD_PROFILES.md"][-2]
            changed, replacements = re.subn(
                r"\d+(\s+physical Markdown files)",
                r"2\1",
                profiles.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, replacements)
            profiles.write_text(changed, encoding="utf-8")

            with mock.patch.object(
                self.validator, "_volatile_fact_authority", return_value=authority
            ):
                errors = self.validator._volatile_fact_errors(root)

            self.assertIn(
                "docs/BUILD_PROFILES.md: missing authority-derived current fact "
                f"{expected!r}",
                errors,
            )

    def test_stale_unindexed_template_reference_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authority = self._synthetic_volatile_authority()
            projections = self._volatile_fact_inputs(root, authority)
            profiles = root / "docs/BUILD_PROFILES.md"
            expected = projections["docs/BUILD_PROFILES.md"][-1]
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

            with mock.patch.object(
                self.validator, "_volatile_fact_authority", return_value=authority
            ):
                errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any(
                    "docs/BUILD_PROFILES.md" in error
                    and expected in error
                    for error in errors
                ),
                errors,
            )

    def test_reference_inventory_collector_failure_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            authority = self._synthetic_volatile_authority()
            self._volatile_fact_inputs(root, authority)

            def failed_authority(_root: Path) -> dict[str, object]:
                self.validator._reference_inventory_authority(root)
                raise AssertionError("collector failure did not propagate")

            with mock.patch.object(
                self.validator,
                "_canonical_reference_content",
                side_effect=RuntimeError("fixture collector failure"),
            ), mock.patch.object(
                self.validator,
                "_volatile_fact_authority",
                side_effect=failed_authority,
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
            authority = self._synthetic_volatile_authority()
            projections = self._volatile_fact_inputs(root, authority)
            changelog = root / "CHANGELOG.md"
            current = changelog.read_text(encoding="utf-8")
            expected = projections["CHANGELOG.md"][0]
            stale = current.replace(
                expected,
                "4 canonical entries and 2 capability entries",
                1,
            )
            changelog.write_text(
                stale
                + "\n## Historical fixture\n\n"
                + expected
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(
                self.validator, "_volatile_fact_authority", return_value=authority
            ):
                errors = self.validator._volatile_fact_errors(root)

            self.assertTrue(
                any(
                    "CHANGELOG.md" in error
                    and expected in error
                    for error in errors
                ),
                errors,
            )

    def test_host_specific_skill_invocation_is_current(self) -> None:
        self.assertEqual([], self.validator._host_product_surface_errors(ROOT))

    def test_copilot_user_label_projects_from_host_authority(self) -> None:
        authority = json.loads(
            (ROOT / "src/agent-profiles/host-product-surfaces.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("Copilot CLI", authority["surfaces"]["copilot"]["label"])
        for relative in ("README.md", "docs/QUICKSTART.md"):
            with self.subTest(relative=relative):
                self.assertIn(
                    "| Copilot CLI | Skills + Agent Profiles |",
                    (ROOT / relative).read_text(encoding="utf-8"),
                )

    def test_explicit_invocation_examples_are_bound_to_host_authority(self) -> None:
        for relative in ("README.md", "docs/QUICKSTART.md", "docs/USAGE.md"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._copy_paths(
                    root,
                    (
                        "README.md",
                        "docs/QUICKSTART.md",
                        "docs/USAGE.md",
                        "src/agent-profiles/host-product-surfaces.json",
                    ),
                )
                target = root / relative
                text = target.read_text(encoding="utf-8")
                task_start = "$engineering-control-plane\n\nPayment callbacks"
                self.assertIn(task_start, text)
                target.write_text(
                    text.replace(
                        task_start,
                        "$wrong-skill\n\nPayment callbacks",
                        1,
                    ),
                    encoding="utf-8",
                )

                errors = self.validator._host_product_surface_errors(root)

                self.assertTrue(
                    any("invocation token" in error for error in errors),
                    errors,
                )

    def test_copilot_every_surface_limit_claim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                (
                    "README.md",
                    "docs/QUICKSTART.md",
                    "docs/USAGE.md",
                    "src/agent-profiles/host-product-surfaces.json",
                ),
            )
            readme = root / "README.md"
            current = readme.read_text(encoding="utf-8")
            original = "Copilot CLI only"
            self.assertIn(original, current)
            readme.write_text(
                current.replace(
                    original,
                    "Available on every Copilot surface.",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._host_product_surface_errors(root)

            self.assertTrue(
                any("Host delivery/invocation/workflow table" in error for error in errors),
                errors,
            )

    def test_cline_install_target_does_not_claim_live_host_behavior(self) -> None:
        quickstart = (ROOT / "docs/QUICKSTART.md").read_text(encoding="utf-8")
        self.assertIn(
            "| Cline | Skills only | Not established | Not established | "
            "Artifact delivery only |",
            quickstart,
        )
        self.assertEqual([], self.validator._host_product_surface_errors(ROOT))

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                (
                    "README.md",
                    "docs/QUICKSTART.md",
                    "docs/USAGE.md",
                    "src/agent-profiles/host-product-surfaces.json",
                ),
            )
            target = root / "docs/QUICKSTART.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "| Cline | Skills only | Not established | Not established | "
                    "Artifact delivery only |",
                    "| Cline | Skills only | `/engineering-control-plane` | Available | "
                    "Artifact delivery only |",
                    1,
                ),
                encoding="utf-8",
            )
            errors = self.validator._host_product_surface_errors(root)
            self.assertTrue(
                any("Host delivery/invocation/workflow table" in error for error in errors),
                errors,
            )

    def test_cline_full_workflow_prose_claim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                (
                    "README.md",
                    "docs/QUICKSTART.md",
                    "docs/USAGE.md",
                    "src/agent-profiles/host-product-surfaces.json",
                ),
            )
            usage = root / "docs/USAGE.md"
            usage.write_text(
                usage.read_text(encoding="utf-8")
                + "\nThe full rd-skills workflow is available in Cline.\n",
                encoding="utf-8",
            )

            errors = self.validator._host_product_surface_errors(root)

            self.assertTrue(any("unsupported Host workflow claim" in error for error in errors), errors)

    def test_quickstart_codex_task_rejects_slash_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                (
                    "README.md",
                    "docs/QUICKSTART.md",
                    "docs/USAGE.md",
                    "src/agent-profiles/host-product-surfaces.json",
                ),
            )
            quickstart = root / "docs/QUICKSTART.md"
            current = quickstart.read_text(encoding="utf-8")
            task_start = "$engineering-control-plane\n\nPayment callbacks"
            self.assertIn(task_start, current)
            quickstart.write_text(
                current.replace(
                    task_start,
                    "/engineering-control-plane\n\nPayment callbacks",
                    1,
                ),
                encoding="utf-8",
            )

            errors = self.validator._host_product_surface_errors(root)

            self.assertTrue(
                any(
                    "docs/QUICKSTART.md" in error and "invocation token" in error
                    for error in errors
                ),
                errors,
            )

    def test_slash_invocation_examples_are_bound_to_host_authority(self) -> None:
        for relative in ("README.md", "docs/QUICKSTART.md", "docs/USAGE.md"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._copy_paths(
                    root,
                    (
                        "README.md",
                        "docs/QUICKSTART.md",
                        "docs/USAGE.md",
                        "src/agent-profiles/host-product-surfaces.json",
                    ),
                )
                target = root / relative
                current = target.read_text(encoding="utf-8")
                task_start = "$engineering-control-plane\n\nPayment callbacks"
                self.assertIn(task_start, current)
                target.write_text(
                    current.replace(
                        task_start,
                        "/wrong-skill\n\nPayment callbacks",
                        1,
                    ),
                    encoding="utf-8",
                )

                errors = self.validator._host_product_surface_errors(root)

                self.assertTrue(
                    any(
                        relative in error and "invocation token" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_universal_slash_invocation_claim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_paths(
                root,
                (
                    "README.md",
                    "docs/QUICKSTART.md",
                    "docs/USAGE.md",
                    "src/agent-profiles/host-product-surfaces.json",
                ),
            )
            usage = root / "docs/USAGE.md"
            usage.write_text(
                usage.read_text(encoding="utf-8")
                + "\nAll supported hosts use `/engineering-control-plane`.\n",
                encoding="utf-8",
            )

            errors = self.validator._host_product_surface_errors(root)

            self.assertTrue(
                any("universal Slash" in error for error in errors),
                errors,
            )

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
                    "  schema_version: 8\n",
                    "  schema_version: 8\n  lifecycle: {}\n",
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

    def test_current_timeout_class_guidance_matches_runner_contract(self) -> None:
        errors = self.validator._required_content_errors(ROOT)

        self.assertFalse(
            any(
                fact in error
                for fact in self.validator.TEST_TIMEOUT_GUIDANCE_FACTS
                for error in errors
            ),
            errors,
        )

    def test_authoritative_layer3_guidance_rejects_softened_cardinality(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            professional = (
                root
                / "docs/skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md"
            )
            governance = root / "docs/SKILL_CONTENT_GOVERNANCE.md"
            professional.parent.mkdir(parents=True)
            governance.parent.mkdir(parents=True, exist_ok=True)
            professional.write_text(
                "# Professional\n\n"
                "A Direct Task normally uses zero to three Layer 3 Skills. "
                "Higher-risk work may use more only with a concrete risk rationale.\n",
                encoding="utf-8",
            )
            governance.write_text(
                "# Governance\n\n"
                "Use this strict order for a stable, independent Primary Route. "
                "Foundation is a capability-modifier layer and Domain is `modifier-only`.\n\n"
                "Each task normally selects zero to three Layer 3 items; a "
                "fixture-specific risk rationale permits more.\n",
                encoding="utf-8",
            )

            errors = self.validator._required_content_errors(root)

            self.assertEqual(
                {
                    "docs/SKILL_CONTENT_GOVERNANCE.md",
                    (
                        "docs/skill_authoring_standard/"
                        "PROFESSIONAL_SKILL_AUTHORING_STANDARD.md"
                    ),
                },
                {
                    error.split(":", 1)[0]
                    for error in errors
                    if "Layer 3 cardinality guidance" in error
                },
                errors,
            )

    def test_layer3_cardinality_guard_ignores_historical_prose(self) -> None:
        canonical = (
            "Layer 3 selection is an ordered unique list of zero to three items.\n"
            "More than three items or any duplicate fails closed; never truncate "
            "the selection.\n"
            "Higher risk changes which Layer 3 items are selected, not the "
            "maximum count.\n"
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            professional = (
                root
                / "docs/skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md"
            )
            governance = root / "docs/SKILL_CONTENT_GOVERNANCE.md"
            professional.parent.mkdir(parents=True)
            governance.parent.mkdir(parents=True, exist_ok=True)
            professional.write_text(canonical, encoding="utf-8")
            governance.write_text(
                "Use this strict order for a stable, independent Primary Route. "
                "Foundation is a capability-modifier layer and Domain is `modifier-only`.\n"
                + canonical,
                encoding="utf-8",
            )
            (root / "CHANGELOG.md").write_text(
                "Historical note: higher-risk work may use more Layer 3 Skills "
                "with a risk rationale.\n",
                encoding="utf-8",
            )

            errors = self.validator._required_content_errors(root)

            self.assertEqual([], errors)

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

    def test_validation_path_surfaces_are_consistent(self) -> None:
        self.assertEqual([], self.validator._validation_path_consistency_errors(ROOT))

    def test_parallel_full_runner_is_the_unique_official_unittest_command(self) -> None:
        official = (
            "python3 scripts/run-ci-tests.py full --jobs 4 --timeout 900"
        )
        legacy = "python3 -m unittest discover -s tests"
        self.assertEqual(official, self.validator.FULL_REGRESSION_COMMANDS[7])
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

    def test_context_budget_projection_uses_core_soft_and_hard_limits(self) -> None:
        contract = CORE_CONTRACTS["context_budget_contract"]
        main = contract["budget_classes"]["main"]
        self.assertLess(main["soft_target"], main["hard_ceiling"])
        projection = CORE_CONTRACTS["docs_contract"][
            "context_budget_projections"
        ][0]
        rendered = self.validator.context_budget_docs_projection_block(
            CORE_CONTRACTS,
            projection,
        )
        self.assertIn(
            f"| Resident Runtime Budget | Main always-loaded | {main['soft_target']} | {main['hard_ceiling']} | provisional-migration-value |",
            rendered,
        )

    def test_context_budget_projection_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._projected_docs(root)
            target = root / "docs" / "VALIDATION.md"
            main = CORE_CONTRACTS["context_budget_contract"]["budget_classes"]["main"]
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    f"| Resident Runtime Budget | Main always-loaded | {main['soft_target']} | {main['hard_ceiling']} | provisional-migration-value |",
                    f"| Resident Runtime Budget | Main always-loaded | {main['soft_target']} | {main['hard_ceiling'] - 1} | provisional-migration-value |",
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
                + "\nCurrent rendered Main maximum is 9999/"
                + str(
                    CORE_CONTRACTS["context_budget_contract"]["budget_classes"]
                    ["main"]["hard_ceiling"]
                )
                + " tokens.\n",
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
            main = CORE_CONTRACTS["context_budget_contract"]["budget_classes"]["main"]
            governance.write_text(
                governance.read_text(encoding="utf-8").replace(
                    f"| Main always-loaded | {main['soft_target']} | {main['hard_ceiling']} |",
                    f"| Main always-loaded | {main['soft_target']} | {main['hard_ceiling'] - 1} |",
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
                        report["budget_governance"]["hard_ceilings"]["main"] -= 1
                    report_path.write_text(
                        json.dumps(report),
                        encoding="utf-8",
                    )

                errors = self.validator._governance_context_budget_errors(
                    root,
                    CORE_CONTRACTS,
                )

                self.assertTrue(
                    any("rendered context" in error for error in errors),
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
