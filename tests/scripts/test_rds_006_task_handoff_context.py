from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_utils import (  # noqa: E402
    load_yaml_file,
    parse_frontmatter,
    reference_contracts,
    render_targeted_reference_section,
)


SKILL_DIR = ROOT / "src/foundation/capabilities/task-handoff-context"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCE_FILE = SKILL_DIR / "references/task-context-checklist.md"
EXAMPLE_FILE = SKILL_DIR / "examples/example-output.md"
WORKING_CONTEXT_FILE = (
    ROOT / "src/foundation/capabilities/task-context-selection/SKILL.md"
)
REGISTRY = ROOT / "src/registry/foundation-skills.yaml"

EXPECTED_OUTPUT = (
    "downstream-context transfer decision with consumer, purpose, included "
    "claims, exact artifacts and latest diff, fresh validation, unresolved "
    "decisions, constraints, owner, next action, findings, proof limits, "
    "exclusions, omissions, staleness and reload triggers, contradictions, "
    "lossy-transfer risks, and residual uncertainty"
)


class TaskHandoffContextContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SKILL_FILE.read_text(encoding="utf-8")
        _metadata, _raw, cls.body = parse_frontmatter(SKILL_FILE)
        cls.reference = REFERENCE_FILE.read_text(encoding="utf-8")
        cls.working_context = WORKING_CONTEXT_FILE.read_text(encoding="utf-8")
        entries = load_yaml_file(REGISTRY)["foundation_skills"]
        cls.entry = next(
            entry for entry in entries if entry["name"] == "task-handoff-context"
        )

    def test_unique_downstream_transfer_decision_remains(self) -> None:
        source = f"{self.body}\n{self.reference}".casefold()
        for term in (
            "downstream consumer",
            "purpose",
            "decision-changing claims",
            "exact artifacts",
            "latest diff",
            "fresh validation",
            "unresolved decisions",
            "constraints",
            "owner",
            "next action",
            "findings",
            "proof limits",
            "exclusions",
            "omissions",
            "staleness",
            "reload triggers",
            "contradictory evidence",
            "lossy transfer",
            "residual uncertainty",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)
        self.assertEqual([EXPECTED_OUTPUT], self.entry["output_contract"])
        self.assertIn(f"- {EXPECTED_OUTPUT}", self.body)

    def test_template_control_and_profile_responsibilities_are_absent(self) -> None:
        source = "\n".join(
            (self.body, self.reference, json.dumps(self.entry, sort_keys=True))
        ).casefold()
        for forbidden in (
            "task contract v2",
            "bounded markdown",
            "status and visible",
            "evidence ledger",
            "goal, allowed scope, observable acceptance",
            "verify command",
            "one primary professional skill",
            "layer 3 skill when",
            "natural-language markdown",
            "one isolated",
            "task capsule",
            "review handoff",
            "current task contract",
            "task-local trigger evidence",
            "completion",
            "retry",
            "read and search only",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_boundary_with_working_context_owner_is_bidirectional(self) -> None:
        normalized = re.sub(r"\s+", " ", self.body.casefold())
        self.assertIn("after work", normalized)
        self.assertIn("working context before or during", normalized)
        self.assertIn("`task-context-selection` owns", normalized)
        self.assertIn(
            "`task-handoff-context` owns packaging context for another agent",
            re.sub(r"\s+", " ", self.working_context.casefold()),
        )

    def test_registry_and_reference_projection_are_exact(self) -> None:
        contracts = reference_contracts(
            self.entry["reference_index"],
            "foundation-skills.yaml:task-handoff-context.reference_index",
            owner="task-handoff-context",
        )
        self.assertEqual(
            ["references/task-context-checklist.md"],
            [contract["path"] for contract in contracts],
        )
        self.assertEqual(
            self.source,
            render_targeted_reference_section(
                self.source,
                contracts,
                "task-handoff-context",
            ),
        )
        headings = re.findall(r"(?m)^## (.+?)\s*$", self.body)
        self.assertEqual(
            [
                "Registry Trigger",
                "Skill Role",
                "Inputs",
                "High-Value Rules",
                "Anti-Patterns",
                "Execution Checklist",
                "Stop Conditions",
                "Output Contract",
                "Targeted References",
            ],
            headings,
        )
        self.assertLessEqual(len(self.body.splitlines()), 90)
        self.assertEqual([], self.entry["used_by"])
        self.assertEqual("dev-only", self.entry["delivery_scope"])
        self.assertFalse(EXAMPLE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
