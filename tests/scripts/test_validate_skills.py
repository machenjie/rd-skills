from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock


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


def _section_contract_body(*, authoring_details: tuple[str, ...] = ()) -> str:
    sections = [
        ("Role", "Support `task-agent` for bounded work."),
        ("When To Use", "- bounded work"),
        ("Do Not Use", "- unrelated work"),
        ("Required Inputs", "- accepted scope"),
        ("Professional Decision Rules", "- Preserve the accepted boundary."),
        *[(heading, "- Retain source-backed detail.") for heading in authoring_details],
        ("Stop / Escalation Conditions", "- Stop on unknown ownership."),
        ("Output Contract", "- bounded result"),
        ("Targeted References", "No named References are required."),
    ]
    return "# test\n\n" + "\n\n".join(
        f"## {heading}\n\n{content}" for heading, content in sections
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

    def test_professional_section_contract_accepts_compact_and_full_roots(
        self,
    ) -> None:
        for authoring_details in (
            (),
            ("High-Value Gotchas", "Execution Checklist"),
        ):
            with self.subTest(authoring_details=authoring_details):
                errors: list[str] = []
                self.module._validate_professional_section_contract(
                    _section_contract_body(authoring_details=authoring_details),
                    "test/SKILL.md",
                    errors,
                )
                self.assertEqual([], errors)

    def test_professional_section_contract_rejects_partial_authoring_details(
        self,
    ) -> None:
        for authoring_details in (
            ("High-Value Gotchas",),
            ("Execution Checklist",),
        ):
            with self.subTest(authoring_details=authoring_details):
                errors: list[str] = []
                self.module._validate_professional_section_contract(
                    _section_contract_body(authoring_details=authoring_details),
                    "test/SKILL.md",
                    errors,
                )
                self.assertTrue(
                    any("must appear together" in error for error in errors),
                    errors,
                )

    def test_professional_section_contract_rejects_missing_kernel_heading(
        self,
    ) -> None:
        errors: list[str] = []
        body = _section_contract_body().replace(
            "## Professional Decision Rules\n\n"
            "- Preserve the accepted boundary.\n\n",
            "",
        )
        self.module._validate_professional_section_contract(
            body,
            "test/SKILL.md",
            errors,
        )
        self.assertIn(
            "test/SKILL.md: missing required section 'Professional Decision Rules'",
            errors,
        )

    def test_compact_multi_role_contract_does_not_require_execution_markers(
        self,
    ) -> None:
        body = _body(
            "**Analysis mode (`analysis-agent`):** decide the boundary.\n"
            "**Task mode (`task-agent`):** apply the accepted decision.",
            "",
            "common output\n"
            "- **Analysis mode (`analysis-agent`):** analysis-agent output.\n"
            "- **Task mode (`task-agent`):** task-agent output.",
            "common input\n"
            "- **Analysis mode (`analysis-agent`):** analysis-agent input.\n"
            "- **Task mode (`task-agent`):** task-agent input.",
        ).replace("## Execution Checklist\n\n\n\n", "")
        errors = self._errors(
            ["analysis-agent", "task-agent"],
            "Analyze with `analysis-agent` or implement with `task-agent`.",
            body,
        )
        self.assertEqual([], errors)

    def test_full_multi_role_contract_requires_execution_markers(self) -> None:
        errors = self._errors(
            ["analysis-agent", "task-agent"],
            "Analyze with `analysis-agent` or implement with `task-agent`.",
            _body(
                "**Analysis mode (`analysis-agent`):** decide the boundary.\n"
                "**Task mode (`task-agent`):** apply the accepted decision.",
                "Close the accepted work.",
                "common output\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent output.\n"
                "- **Task mode (`task-agent`):** task-agent output.",
                "common input\n"
                "- **Analysis mode (`analysis-agent`):** analysis-agent input.\n"
                "- **Task mode (`task-agent`):** task-agent input.",
            ),
        )
        self.assertTrue(
            any("Execution Checklist must define" in error for error in errors),
            errors,
        )

    def test_routing_maintenance_is_authoring_only_not_professional(self) -> None:
        professional = self.module.load_yaml_file(self.module.REGISTRY)[
            "professional_skills"
        ]
        foundation_path = ROOT / "src/registry/foundation-skills.yaml"
        foundation = self.module.load_yaml_file(foundation_path)["foundation_skills"]
        owner = next(
            item for item in foundation if item["name"] == "skill-authoring-expert"
        )
        reference = next(
            item
            for item in owner["reference_index"]
            if item["path"] == "references/routing-maintenance-checklist.md"
        )

        self.assertNotIn(
            "routing-quality-review",
            {item["name"] for item in professional},
        )
        self.assertFalse(
            (
                ROOT
                / "src/professional-skills/routing-quality-review/SKILL.md"
            ).exists()
        )
        self.assertEqual("authoring-only", owner["delivery_scope"])
        self.assertEqual("decision-checklist", reference["type"])
        self.assertTrue(
            (
                ROOT
                / "src/foundation/capabilities/skill-authoring-expert"
                / reference["path"]
            ).is_file()
        )

    def test_ai_review_output_discloses_reviewed_and_unreviewed_files(self) -> None:
        skill_file = (
            ROOT / "src/professional-skills/ai-code-review-refactor/SKILL.md"
        )
        _metadata, _raw, body = self.module.parse_frontmatter(skill_file)
        output = self.module._section(body, "Output Contract")
        example = (
            skill_file.parent / "examples/example-output.md"
        ).read_text(encoding="utf-8")

        self.assertIn("- reviewed/unreviewed scope", output)
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


class ProfessionalIndependenceReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        import validation_utils

        cls.validation_utils = validation_utils

    @staticmethod
    def _canonical_targeted_reference_body() -> str:
        return (
            "# example\n\n"
            "## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [security output and gates](references/security-output-and-gates.md) "
            "| targeted | L3-L5 work needs mode-specific closure and targeted gates "
            "for a selected authorization risk | A compact L1/L2 result is sufficient "
            "and no selected risk needs the extended proof contract | analysis-agent, "
            "task-agent, review-agent | gate-decision, residual-risk |"
        )

    @staticmethod
    def _frontmatter_source(body: str) -> str:
        return f"---\nname: example\n---\n{body}\n"

    def test_confirmed_self_coupling_requires_internal_semantic_context(self) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": (
                    "Project Task Contract v2 nodes with one Primary Professional Skill "
                    "and Layer 3 selectors.\n"
                    "Return `blocked` through Main for redispatch.\n"
                    "<!-- BEGIN CHANGEFORGE CONTROL PROJECTION -->\n"
                    "Load this contract only for an L5 review.\n"
                    "Route release approval to `delivery-release-gate`.\n"
                ),
                "line_offset": 4,
            }
        ]

        findings = self.module.professional_independence_findings(
            documents,
            registered_skill_names={"delivery-release-gate", "example"},
        )

        self.assertEqual(
            {
                "branded-control-schema",
                "control-role-dependency",
                "execution-level-protocol",
                "internal-routing-object",
                "sibling-skill-route",
                "versioned-internal-contract",
            },
            {finding["category"] for finding in findings},
        )
        self.assertTrue(
            all(
                set(finding) == {"path", "category", "line", "excerpt"}
                for finding in findings
            )
        )
        self.assertIn(5, {finding["line"] for finding in findings})

    def test_generic_concepts_and_domain_homonyms_are_not_findings(self) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": (
                    "An Engineering Brief may define a Task Contract, Task DAG, First "
                    "Executable Slice, Review Boundary, and Evidence Ledger.\n"
                    "The Electron main process coordinates renderer shutdown.\n"
                    "Keep core domain rules in their business owner.\n"
                    "Kubernetes control-plane behavior can differ from recorded state.\n"
                    "Tune the L3 cache only after measuring misses.\n"
                    "Publish the package to a registry after validation.\n"
                    "The delivery-release-gate example discusses release evidence.\n"
                    "A route change must preserve focus; `quality-test-gate` documents "
                    "test evidence.\n"
                    "| Focus | final route | proof tied to the diff | "
                    "`quality-test-gate` |\n"
                    "A direct task may use a source registry selected by the "
                    "application.\n"
                    "A source-owned registry can be a domain system of record.\n"
                ),
                "line_offset": 0,
            }
        ]

        self.assertEqual(
            [],
            self.module.professional_independence_findings(
                documents,
                registered_skill_names={"delivery-release-gate", "example"},
            ),
        )

    def test_known_sibling_asserted_as_owner_is_a_finding_even_when_autoload_is_denied(
        self,
    ) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": (
                    "`quality-test-gate` owns final validation approval; do not "
                    "auto-load that Skill.\n"
                ),
                "line_offset": 0,
            }
        ]

        findings = self.module.professional_independence_findings(
            documents,
            registered_skill_names={"example", "quality-test-gate"},
        )

        self.assertEqual(1, len(findings), findings)
        self.assertEqual("sibling-skill-owner", findings[0]["category"])

    def test_wrapped_logical_units_detect_coupling_at_the_first_physical_line(
        self,
    ) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": (
                    "- Route release approval to\n"
                    "  `delivery-release-gate`.\n\n"
                    "Project Task Contract\n"
                    "v2 nodes from accepted scope.\n"
                ),
                "line_offset": 10,
            }
        ]

        findings = self.module.professional_independence_findings(
            documents,
            registered_skill_names={"delivery-release-gate", "example"},
        )

        self.assertEqual(
            [
                (
                    "sibling-skill-route",
                    11,
                    "Route release approval to `delivery-release-gate`.",
                ),
                (
                    "versioned-internal-contract",
                    14,
                    "Project Task Contract v2 nodes from accepted scope.",
                ),
            ],
            [
                (finding["category"], finding["line"], finding["excerpt"])
                for finding in findings
            ],
        )

    def test_internal_execution_paths_require_contextual_internal_forms(self) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": (
                    "- Use a Direct Task when ownership is already established.\n"
                    "- Skip no-repo direct-answer mode.\n"
                    "- Load the named Reference selected from the source-owned "
                    "registry.\n"
                ),
                "line_offset": 2,
            }
        ]

        findings = self.module.professional_independence_findings(
            documents,
            registered_skill_names={"example"},
        )

        self.assertEqual(3, len(findings), findings)
        self.assertEqual(
            {"internal-execution-path"},
            {finding["category"] for finding in findings},
        )
        self.assertEqual([3, 4, 5], [finding["line"] for finding in findings])

    def test_generic_owner_and_load_language_is_not_a_sibling_finding(self) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": (
                    "Record the decision owner and evidence needed; do not expand "
                    "or auto-load another capability.\n"
                    "Load `quality-test-gate` examples only when comparing generic "
                    "test strategies.\n"
                ),
                "line_offset": 0,
            }
        ]

        self.assertEqual(
            [],
            self.module.professional_independence_findings(
                documents,
                registered_skill_names={"example", "quality-test-gate"},
            ),
        )

    def test_exact_canonical_l3_l5_adapter_projection_is_excluded(self) -> None:
        body = self._canonical_targeted_reference_body()
        governed = (
            self.validation_utils.strip_frontmatter_body_targeted_reference_projection(
                body,
                self._frontmatter_source(body),
            )
        )

        self.assertNotIn("L3-L5", governed)
        self.assertEqual(len(body.splitlines()), len(governed.splitlines()))
        self.assertEqual(
            [],
            self.module.professional_independence_findings(
                [
                    {
                        "path": "src/professional-skills/example/SKILL.md",
                        "owner": "example",
                        "text": body,
                        "governed_text": governed,
                        "line_offset": 3,
                    }
                ],
                registered_skill_names={"example"},
            ),
        )

    def test_identical_l3_l5_control_semantics_remain_governed_outside_projection(
        self,
    ) -> None:
        sentence = (
            "L3-L5 work needs mode-specific closure and targeted gates for a "
            "selected authorization risk."
        )
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": f"# example\n\n{sentence}\n",
                "line_offset": 3,
            },
            {
                "path": "src/professional-skills/example/references/proof.md",
                "owner": "example",
                "document_part": "reference",
                "text": f"# proof\n\n{sentence}\n",
                "line_offset": 0,
            },
        ]

        findings = self.module.professional_independence_findings(
            documents,
            registered_skill_names={"example"},
        )

        self.assertEqual(2, len(findings), findings)
        self.assertEqual(
            {"execution-level-protocol"},
            {finding["category"] for finding in findings},
        )
        self.assertEqual(
            {document["path"] for document in documents},
            {finding["path"] for finding in findings},
        )

    def test_manual_or_malformed_targeted_reference_projection_is_not_exempt(
        self,
    ) -> None:
        canonical = self._canonical_targeted_reference_body()
        candidates = {
            "manual": (
                "# example\n\n## Targeted References\n\n"
                "- L3-L5 work needs mode-specific closure and targeted gates."
            ),
            "malformed": canonical.replace(
                "| Path | Type | Load when | Do not load when | Required by | Required output |",
                "| Path | Type | Load when | Do not load when | Required by | Outputs |",
            ),
        }

        for label, body in candidates.items():
            with self.subTest(label=label):
                governed = self.validation_utils.strip_frontmatter_body_targeted_reference_projection(
                    body,
                    self._frontmatter_source(body),
                )
                self.assertEqual(body, governed)
                findings = self.module.professional_independence_findings(
                    [
                        {
                            "path": "src/professional-skills/example/SKILL.md",
                            "owner": "example",
                            "text": body,
                            "governed_text": governed,
                            "line_offset": 3,
                        }
                    ],
                    registered_skill_names={"example"},
                )
                self.assertTrue(
                    any(
                        finding["category"] == "execution-level-protocol"
                        for finding in findings
                    ),
                    findings,
                )

    def test_projection_exclusion_fails_closed_when_body_and_source_are_not_synced(
        self,
    ) -> None:
        body = self._canonical_targeted_reference_body()
        unsynced_source = self._frontmatter_source(
            body.replace("selected authorization risk", "selected privacy risk")
        )

        governed = self.validation_utils.strip_frontmatter_body_targeted_reference_projection(
            body,
            unsynced_source,
        )

        self.assertEqual(body, governed)
        findings = self.module.professional_independence_findings(
            [
                {
                    "path": "src/professional-skills/example/SKILL.md",
                    "owner": "example",
                    "text": body,
                    "governed_text": governed,
                    "line_offset": 3,
                }
            ],
            registered_skill_names={"example"},
        )
        self.assertTrue(
            any(
                finding["category"] == "execution-level-protocol"
                for finding in findings
            ),
            findings,
        )

    def test_findings_have_stable_path_line_category_order(self) -> None:
        documents = [
            {
                "path": "z/SKILL.md",
                "owner": "z",
                "text": "Core owns routing authority.\nTask Contract v2 is required.\n",
                "line_offset": 0,
            },
            {
                "path": "a/SKILL.md",
                "owner": "a",
                "text": "Review Round ID is a required field.\n",
                "line_offset": 0,
            },
        ]

        first = self.module.professional_independence_findings(
            documents,
            registered_skill_names=set(),
        )
        second = self.module.professional_independence_findings(
            list(reversed(documents)),
            registered_skill_names=set(),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            sorted(
                first,
                key=lambda finding: (
                    finding["path"],
                    finding["line"],
                    finding["category"],
                    finding["excerpt"],
                ),
            ),
            first,
        )

    def test_report_mode_is_advisory_and_writes_only_stdout(self) -> None:
        documents = [
            {
                "path": "example/SKILL.md",
                "owner": "example",
                "text": "Task Contract v2 is required.\n",
                "line_offset": 0,
            }
        ]
        stdout = io.StringIO()
        with (
            mock.patch.object(
                self.module,
                "_professional_independence_documents",
                return_value=documents,
            ),
            mock.patch.object(
                self.module,
                "_registered_skill_names",
                return_value={"example"},
            ),
            contextlib.redirect_stdout(stdout),
        ):
            status = self.module.main(["--professional-independence-report"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(0, status)
        self.assertEqual("report-only", payload["mode"])
        self.assertEqual(1, payload["finding_count"])
        self.assertIn("authored governed Professional content", payload["scope"])
        self.assertIn(
            "canonical Registry-generated Targeted References projection",
            payload["scope"],
        )
        self.assertIn(
            "exact current Registry/package/root equality",
            payload["scope"],
        )
        self.assertTrue(
            any(
                "not every source byte" in limit
                for limit in payload["proof_limits"]
            ),
            payload["proof_limits"],
        )
        self.assertTrue(
            any(
                "may select only optional Reference and depth" in limit
                and "domain verdict" in limit
                and "proof obligation" in limit
                for limit in payload["proof_limits"]
            ),
            payload["proof_limits"],
        )
        self.assertTrue(
            any(
                "current Registry names, package paths, root membership" in limit
                and "rendered source bytes are exactly equal" in limit
                for limit in payload["proof_limits"]
            ),
            payload["proof_limits"],
        )
        self.assertEqual(
            {"versioned-internal-contract": 1},
            payload["category_counts"],
        )

    def test_registry_projection_authority_failure_is_fatal_in_both_modes(
        self,
    ) -> None:
        for argv in ([], ["--professional-independence-report"]):
            with self.subTest(argv=argv):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    mock.patch.object(
                        self.module,
                        "_professional_independence_documents",
                        side_effect=self.module.ValidationProblem(
                            "Professional Registry projection authority failed"
                        ),
                    ),
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    status = self.module.main(argv)

                self.assertNotEqual(0, status)
                self.assertEqual("", stdout.getvalue())
                self.assertIn(
                    "Professional Registry projection authority failed",
                    stderr.getvalue(),
                )

    def test_normal_mode_fails_on_confirmed_independence_finding(self) -> None:
        documents = [
            {
                "path": "src/professional-skills/example/SKILL.md",
                "owner": "example",
                "text": "Task Contract v2 is required.\n",
                "line_offset": 0,
            }
        ]
        stderr = io.StringIO()
        with (
            mock.patch.object(
                self.module,
                "_professional_independence_documents",
                return_value=documents,
            ),
            mock.patch.object(
                self.module,
                "_registered_skill_names",
                return_value={"example"},
            ),
            mock.patch.object(
                self.module,
                "validate_capability_coverage_matrix",
                return_value=[],
            ),
            contextlib.redirect_stderr(stderr),
        ):
            status = self.module.main([])

        self.assertNotEqual(0, status)
        self.assertIn("versioned-internal-contract", stderr.getvalue())

    def test_core_affected_graph_derives_validator_and_contract_test_owner(self) -> None:
        core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        producer = next(
            item
            for item in core["principle_acceptance_contract"]["producers"]
            if item["id"] == "validate-skills"
        )
        owning_rules = [
            item
            for item in core["impact_graph_contract"]["rules"]
            if "validate-skills" in item["producer_ids"]
            and "tests/scripts/test_validate_skills.py" in item["test_modules"]
        ]

        self.assertIn("scripts/validate-skills.py", producer["argv"])
        self.assertTrue(owning_rules)


if __name__ == "__main__":
    unittest.main()
