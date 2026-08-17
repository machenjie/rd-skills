from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-skills.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _body(role: str, execution: str, output: str, required: str = "") -> str:
    return (
        "# test\n\n"
        f"## Role\n\n{role}\n\n"
        f"## Required Inputs\n\n{required}\n\n"
        f"## Execution Checklist\n\n{execution}\n\n"
        f"## Output Contract\n\n{output}\n"
    )


def _ai_review_example_scope_errors(markdown: str) -> list[str]:
    errors: list[str] = []

    def section(title: str) -> str | None:
        match = re.search(
            rf"^### {re.escape(title)}\s*$\n(.*?)(?=^### |^## |\Z)",
            markdown,
            flags=re.MULTILINE | re.DOTALL,
        )
        return match.group(1).strip() if match else None

    reviewed = section("Reviewed files")
    if reviewed is None:
        errors.append("example must disclose reviewed files")
    elif not any(line.startswith("- ") for line in reviewed.splitlines()):
        errors.append("example must list at least one reviewed file")

    unreviewed = section("Unreviewed files")
    if unreviewed is None:
        errors.append("example must disclose unreviewed files or explicitly state none")
    elif unreviewed.casefold() not in {"none", "none."}:
        entries = re.split(r"(?m)^- ", unreviewed)[1:]
        if not entries:
            errors.append("example unreviewed-files section is incomplete")
        for entry in entries:
            file_name = entry.splitlines()[0].strip()
            if not re.search(r"(?m)^  - Reason:\s+\S", entry):
                errors.append(f"unreviewed file {file_name!r} must include a reason")
            if not re.search(r"(?m)^  - Residual risk:\s+\S", entry):
                errors.append(
                    f"unreviewed file {file_name!r} must include residual risk"
                )
    return errors


class ValidateProfessionalSkillRoleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _errors(
        self,
        roles: list[str],
        description: str,
        body: str,
    ) -> list[str]:
        errors: list[str] = []
        entry = {"role_support": roles}
        if len(roles) > 1:
            entry["required_inputs"] = ["common input"]
            entry["required_inputs_by_role"] = {
                role: [f"{role} input"] for role in roles
            }
            entry["output_contract"] = ["common output"]
            entry["output_contract_by_role"] = {
                role: [f"{role} output"] for role in roles
            }
        self.module._validate_role_contract(
            entry,
            {"description": description},
            body,
            "test/SKILL.md",
            errors,
        )
        return errors

    def test_professional_root_hard_gate_is_120_lines(self) -> None:
        self.assertEqual(self.module.MAX_ROOT_SKILL_LINES, 120)

    def test_routing_review_assignment_is_a_positive_trigger_not_an_anti_trigger(
        self,
    ) -> None:
        registry = self.module.load_yaml_file(self.module.REGISTRY)[
            "professional_skills"
        ]
        entry = next(
            item for item in registry if item["name"] == "routing-quality-review"
        )
        skill_file = (
            ROOT / "src/professional-skills/routing-quality-review/SKILL.md"
        )
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        when_to_use = self.module._section(body, "When To Use")
        do_not_use = self.module._section(body, "Do Not Use")
        decision_rules = self.module._section(body, "Professional Decision Rules")
        root_triggers = [
            line.removeprefix("- ")
            for line in when_to_use.splitlines()
            if line.startswith("- ")
        ]
        root_anti_triggers = [
            line.removeprefix("- ")
            for line in do_not_use.splitlines()
            if line.startswith("- ")
        ]
        positive_trigger = (
            "independently assigned post-authoring review of a changed "
            "rd-skills routing asset"
        )

        self.assertEqual(entry["trigger_signals"], root_triggers)
        self.assertEqual(entry["anti_trigger_signals"], root_anti_triggers)
        self.assertIn(positive_trigger, root_triggers)
        self.assertNotIn(positive_trigger, root_anti_triggers)
        self.assertNotIn("not a task owner", do_not_use.casefold())
        self.assertNotIn("independently assigned", do_not_use.casefold())
        self.assertIn(
            "do not select this skill as an implementation owner",
            decision_rules.casefold(),
        )
        self.assertFalse(entry["task_routable"])

    def test_ai_review_output_discloses_reviewed_and_unreviewed_files(self) -> None:
        skill_file = (
            ROOT / "src/professional-skills/ai-code-review-refactor/SKILL.md"
        )
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        output = self.module._section(body, "Output Contract")
        example = (
            skill_file.parent / "examples/example-output.md"
        ).read_text(encoding="utf-8")

        self.assertIn("- reviewed files", output)
        self.assertIn("- unreviewed files with reason and residual risk", output)
        self.assertEqual([], _ai_review_example_scope_errors(example))

        missing_scope = example.replace("### Unreviewed files\n\nNone.\n\n", "")
        self.assertIn(
            "example must disclose unreviewed files or explicitly state none",
            _ai_review_example_scope_errors(missing_scope),
        )

        incomplete_entry = example.replace(
            "None.",
            "- `docs/project-archive.md`\n"
            "  - Reason: Generated documentation was unavailable.",
        )
        self.assertTrue(
            any(
                "must include residual risk" in error
                for error in _ai_review_example_scope_errors(incomplete_entry)
            )
        )

    def test_three_role_contract_accepts_professional_mode_boundaries(self) -> None:
        errors = self._errors(
            ["analysis-agent", "task-agent", "review-agent"],
            "Analyze with `analysis-agent`, implement with `task-agent`, or independently assess with `review-agent`.",
            _body(
                "**Analysis mode (`analysis-agent`):** decide the compatibility boundary.\n"
                "**Task mode (`task-agent`):** implement the accepted transition.\n"
                "**Review mode (`review-agent`):** assess contract risk independently.",
                "**Analysis mode:** derive the migration decision.\n"
                "**Task mode:** preserve the selected compatibility contract.\n"
                "**Review mode:** prove affected consumers remain covered.",
                "common output\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent output.\n"
                "- **Task mode (`task-agent`):** task-agent output.\n"
                "- **Review mode (`review-agent`):** review-agent output.",
                "common input\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent input.\n"
                "- **Task mode (`task-agent`):** task-agent input.\n"
                "- **Review mode (`review-agent`):** review-agent input.",
            ),
        )
        self.assertEqual(errors, [])

    def test_multi_role_contract_rejects_missing_role_inputs(self) -> None:
        errors = self._errors(
            ["analysis-agent", "task-agent"],
            "Analyze with `analysis-agent` or implement with `task-agent`.",
            _body(
                "**Analysis mode (`analysis-agent`):** read/search-only.\n"
                "**Task mode (`task-agent`):** implement bounded work.",
                "**Analysis mode:** remain read/search-only.\n"
                "**Task mode:** run post-edit validation.",
                "common output\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent output.\n"
                "- **Task mode (`task-agent`):** task-agent output.",
            ),
        )
        self.assertTrue(any("Required Inputs must define" in error for error in errors))

    def test_multi_role_contract_rejects_swapped_output_blocks(self) -> None:
        errors = self._errors(
            ["analysis-agent", "task-agent"],
            "Analyze with `analysis-agent` or implement with `task-agent`.",
            _body(
                "**Analysis mode (`analysis-agent`):** read/search-only.\n"
                "**Task mode (`task-agent`):** implement bounded work.",
                "**Analysis mode:** remain read/search-only.\n"
                "**Task mode:** run post-edit validation.",
                "common output\n"
                "- **Analysis mode (`analysis-agent`):** task-agent output.\n"
                "- **Task mode (`task-agent`):** analysis-agent output.",
                "common input\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent input.\n"
                "- **Task mode (`task-agent`):** task-agent input.",
            ),
        )
        self.assertTrue(any("analysis-agent block" in error for error in errors), errors)
        self.assertTrue(any("task-agent block" in error for error in errors), errors)

    def test_description_rejects_generic_and_unsupported_role_triggers(self) -> None:
        errors = self._errors(
            ["analysis-agent"],
            "Use when implementing, reviewing, planning, or validating with `task-agent`.",
            _body(
                "Support `analysis-agent`; work read/search-only.",
                "Remain read/search-only.",
                "Return analysis.",
            ),
        )
        self.assertTrue(any("all-role trigger phrase" in error for error in errors))
        self.assertTrue(any("must name supported profile analysis-agent" in error for error in errors))
        self.assertTrue(any("unsupported profile task-agent" in error for error in errors))

    def test_single_role_contract_does_not_repeat_profile_permissions(self) -> None:
        errors = self._errors(
            ["analysis-agent"],
            "Analyze ambiguous behavior with `analysis-agent` using source-backed evidence.",
            _body(
                "Support `analysis-agent` for ambiguity and ownership decisions.",
                "Derive acceptance from current behavior and affected contracts.",
                "Return analysis.",
            ),
        )
        self.assertEqual([], errors)

    def test_task_only_contract_does_not_require_generic_close_scaffold(self) -> None:
        errors = self._errors(
            ["task-agent"],
            "Implement a bounded backend change with `task-agent` and provide validation evidence.",
            _body(
                "Support `task-agent`; implement the accepted scope.",
                "Run post-edit validation.",
                "Return the diff.",
            ),
        )
        self.assertEqual([], errors)

    def test_generic_profile_permission_scaffold_is_rejected(self) -> None:
        errors = self._errors(
            ["analysis-agent", "task-agent", "review-agent"],
            "Analyze with `analysis-agent`, implement with `task-agent`, or assess with `review-agent`.",
            _body(
                "**Analysis mode (`analysis-agent`):** read/search-only.\n"
                "**Task mode (`task-agent`):** do not claim final independent review.\n"
                "**Review mode (`review-agent`):** read-only assessment.",
                "**Analysis mode:** remain read/search-only.\n"
                "**Task mode:** run post-edit validation.\n"
                "**Review mode:** use non-modifying checks and never edit.",
                "common output\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent output.\n"
                "- **Task mode (`task-agent`):** task-agent output.\n"
                "- **Review mode (`review-agent`):** review-agent output.",
                "common input\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent input.\n"
                "- **Task mode (`task-agent`):** task-agent input.\n"
                "- **Review mode (`review-agent`):** review-agent input.",
            ),
        )
        self.assertTrue(any("generic Profile permission scaffold" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
