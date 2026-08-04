from __future__ import annotations

import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-control-skills.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "validate_control_skills_tests",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_module()


class ControlSkillHostModeBranchTests(unittest.TestCase):
    def test_plain_prose_host_mode_mutations_fail_the_full_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            skill_root = (
                root / "src/control-skills/engineering-control-plane"
            )
            shutil.copytree(VALIDATOR.SKILL.parent, skill_root)
            prompt = root / "src/control-prompts/main-control-agent.md"
            prompt.parent.mkdir(parents=True)
            shutil.copy2(VALIDATOR.PROMPT, prompt)
            skill = skill_root / "SKILL.md"
            source = skill.read_text(encoding="utf-8").rstrip()

            with mock.patch.multiple(
                VALIDATOR,
                ROOT=root,
                SKILL=skill,
                PROMPT=prompt,
            ):
                for literal in VALIDATOR.FORBIDDEN_HOST_MODE_BRANCH_LITERALS:
                    with self.subTest(literal=literal):
                        skill.write_text(
                            f"{source}\n\nPlain host branch selects {literal}.\n",
                            encoding="utf-8",
                        )
                        output = io.StringIO()
                        with contextlib.redirect_stderr(output):
                            result = VALIDATOR.main()
                        self.assertEqual(1, result)
                        self.assertIn(
                            f"host branch value '{literal}'",
                            output.getvalue(),
                        )

    def test_markdown_formatting_cannot_hide_host_mode_values(self) -> None:
        wrappers = ("{}", "`{}`", "_{}_", "**{}**", "~~{}~~")
        for literal in VALIDATOR.FORBIDDEN_HOST_MODE_BRANCH_LITERALS:
            for wrapper in wrappers:
                with self.subTest(literal=literal, wrapper=wrapper):
                    errors: list[str] = []
                    VALIDATOR._validate_no_host_mode_branches(
                        "Host branch selects " + wrapper.format(literal) + ".",
                        errors,
                    )
                    self.assertTrue(errors)


class ControlSkillThinRouterTests(unittest.TestCase):
    def test_numbered_control_rules_fail_the_full_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            skill_root = root / "src/control-skills/engineering-control-plane"
            shutil.copytree(VALIDATOR.SKILL.parent, skill_root)
            prompt = root / "src/control-prompts/main-control-agent.md"
            prompt.parent.mkdir(parents=True)
            shutil.copy2(VALIDATOR.PROMPT, prompt)
            skill = skill_root / "SKILL.md"
            source = skill.read_text(encoding="utf-8")
            start = source.index("## Decision Rules")
            end = source.index("## Targeted References")
            expanded = """## Decision Rules

1. Choose a dispatch path.
2. Prepare the first slice.
3. Interpret host modes.
4. Serialize shared writes.
5. Run review and repair.
6. Report progress and closure.

"""
            skill.write_text(source[:start] + expanded + source[end:], encoding="utf-8")

            with mock.patch.multiple(
                VALIDATOR,
                ROOT=root,
                SKILL=skill,
                PROMPT=prompt,
            ):
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    result = VALIDATOR.main()

            self.assertEqual(1, result)
            self.assertIn("one concise prose delegation", output.getvalue())

    def test_current_control_skill_is_one_bounded_delegation(self) -> None:
        _metadata, _raw, body = VALIDATOR.parse_frontmatter(VALIDATOR.SKILL)
        errors: list[str] = []

        VALIDATOR._validate_thin_decision_rules(body, errors)

        self.assertEqual([], errors)


class ControlSkillProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        _metadata, _raw, self.body = VALIDATOR.parse_frontmatter(VALIDATOR.SKILL)

    def test_heading_swap_duplicate_and_h1_change_are_rejected(self) -> None:
        swapped = self.body.replace("## Role\n", "## __SWAP__\n", 1)
        swapped = swapped.replace("## Decision Rules\n", "## Role\n", 1)
        swapped = swapped.replace("## __SWAP__\n", "## Decision Rules\n", 1)
        mutations = (
            swapped,
            self.body.replace("## Role\n", "## Role\n\n## Role\n", 1),
            self.body.replace(
                "# Engineering Control Plane\n",
                "# Engineering Control Router\n",
                1,
            ),
        )
        for mutation in mutations:
            with self.subTest():
                errors: list[str] = []
                VALIDATOR._validate_heading_structure(mutation, errors)
                self.assertTrue(errors)

    def test_each_forbidden_storage_projection_is_required(self) -> None:
        for rule in VALIDATOR.EVIDENCE_LEDGER_MODEL["forbidden_storage"]:
            term = rule["projection_terms"][0]
            with self.subTest(rule=rule["id"]):
                self.assertIn(term, self.body)
                errors: list[str] = []
                VALIDATOR._validate_concepts(
                    self.body.replace(term, "REMOVED_STORAGE_TERM", 1),
                    errors,
                )
                self.assertTrue(
                    any(f"forbidden storage rule {rule['id']!r}" in error for error in errors),
                    errors,
                )

    def test_runtime_contract_is_registered_exact_and_missing_copy_fails(self) -> None:
        runtime = VALIDATOR.SKILL.parent / "references/execution-level-contract.md"
        self.assertEqual(
            [],
            VALIDATOR.execution_level_runtime_reference_errors(
                runtime.read_text(encoding="utf-8")
            ),
        )
        self.assertIn(
            "[execution level contract](references/execution-level-contract.md)",
            self.body,
        )
        self.assertIn("check execution level before routing", self.body)
        with tempfile.TemporaryDirectory() as raw:
            skill_root = Path(raw) / "engineering-control-plane"
            shutil.copytree(VALIDATOR.SKILL.parent, skill_root)
            (skill_root / "references/execution-level-contract.md").unlink()
            skill = skill_root / "SKILL.md"
            _metadata, _frontmatter, body = VALIDATOR.parse_frontmatter(skill)
            errors: list[str] = []
            with mock.patch.object(VALIDATOR, "SKILL", skill):
                VALIDATOR._validate_references(body, errors)
            self.assertTrue(
                any("missing control reference execution-level-contract.md" in error for error in errors),
                errors,
            )

    def test_context_budget_requires_raw_eof_proof_before_projection_exclusion(self) -> None:
        body = (
            "# Fixture\n\n## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [checklist](references/checklist.md) | decision-checklist | "
            "cache invalidation changes need failure coverage | "
            "no cache behavior or ownership changes | task-agent | checklist-result |"
        )
        prefix = "---\nname: fixture\ndescription: Fixture.\n---\n"
        with mock.patch.object(
            VALIDATOR,
            "count_o200k_base_tokens",
            side_effect=lambda text: 501 if "cache invalidation" in text else 1,
        ):
            canonical_errors: list[str] = []
            _lines, canonical_tokens = VALIDATOR._validate_context_budget(
                body,
                prefix + body + "\n",
                canonical_errors,
            )
            self.assertEqual(1, canonical_tokens)
            self.assertEqual([], canonical_errors)

            missing_eof_errors: list[str] = []
            _lines, missing_eof_tokens = VALIDATOR._validate_context_budget(
                body,
                prefix + body,
                missing_eof_errors,
            )
            self.assertEqual(501, missing_eof_tokens)
            self.assertTrue(
                any("maximum is 500" in error for error in missing_eof_errors),
                missing_eof_errors,
            )

    def test_full_validator_keeps_crlf_projection_in_context_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            skill_root = root / "src/control-skills/engineering-control-plane"
            shutil.copytree(VALIDATOR.SKILL.parent, skill_root)
            prompt = root / "src/control-prompts/main-control-agent.md"
            prompt.parent.mkdir(parents=True)
            shutil.copy2(VALIDATOR.PROMPT, prompt)
            skill = skill_root / "SKILL.md"
            source = VALIDATOR.SKILL.read_text(encoding="utf-8")

            with (
                mock.patch.multiple(
                    VALIDATOR,
                    ROOT=root,
                    SKILL=skill,
                    PROMPT=prompt,
                ),
                mock.patch.object(
                    VALIDATOR,
                    "count_o200k_base_tokens",
                    side_effect=lambda text: (
                        501 if "## Targeted References" in text else 1
                    ),
                ),
            ):
                skill.write_bytes(source.encode("utf-8"))
                canonical_output = io.StringIO()
                with contextlib.redirect_stderr(canonical_output):
                    canonical_result = VALIDATOR.main()
                self.assertEqual(0, canonical_result, canonical_output.getvalue())

                crlf_source = source.replace("\n", "\r\n")
                skill.write_bytes(crlf_source.encode("utf-8"))
                crlf_output = io.StringIO()
                with contextlib.redirect_stderr(crlf_output):
                    crlf_result = VALIDATOR.main()
                self.assertEqual(1, crlf_result)
                self.assertIn("maximum is 500", crlf_output.getvalue())


if __name__ == "__main__":
    unittest.main()
