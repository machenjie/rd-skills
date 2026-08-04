from __future__ import annotations

import importlib.util
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


SKILL_DIR = (
    ROOT / "src/foundation/capabilities/agent-tool-permission-sandbox"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCE_FILE = SKILL_DIR / "references/profile-permission-checklist.md"
REGISTRY = ROOT / "src/registry/foundation-skills.yaml"

EXPECTED_OUTPUT = (
    "task-level command risk decision with exact target, mutation surface, "
    "reversibility and recovery, external effects, capability facts, "
    "authorization facts, unresolved ambiguity, and residual risk"
)


def _load_capability_validator():
    spec = importlib.util.spec_from_file_location(
        "rds_006_agent_tool_capability_validator",
        SCRIPTS / "validate-capabilities.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-capabilities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAPABILITY_VALIDATOR = _load_capability_validator()


class AgentToolPermissionSandboxContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SKILL_FILE.read_text(encoding="utf-8")
        cls.metadata, _raw, cls.body = parse_frontmatter(SKILL_FILE)
        cls.reference = REFERENCE_FILE.read_text(encoding="utf-8")
        entries = load_yaml_file(REGISTRY)["foundation_skills"]
        cls.entry = next(
            entry
            for entry in entries
            if entry["name"] == "agent-tool-permission-sandbox"
        )

    def test_description_uses_real_frontmatter_and_capability_boundaries(self) -> None:
        description = self.metadata["description"].strip()
        trigger_section = CAPABILITY_VALIDATOR._section(
            self.body,
            "Registry Trigger",
        )
        self.assertEqual(self.entry["name"], self.metadata["name"])
        self.assertLessEqual(len(description), 180)
        self.assertEqual(
            [],
            CAPABILITY_VALIDATOR._registry_trigger_errors(trigger_section),
        )
        self.assertEqual(
            ["analysis-agent", "task-agent", "review-agent"],
            self.entry["role_support"],
        )

    def test_unique_command_risk_decision_remains(self) -> None:
        source = f"{self.body}\n{self.reference}".casefold()
        for term in (
            "exact target",
            "mutation surface",
            "reversibility",
            "recovery",
            "external effects",
            "capability facts",
            "authorization facts",
            "unresolved ambiguity",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)
        self.assertEqual([EXPECTED_OUTPUT], self.entry["output_contract"])
        self.assertIn(f"- {EXPECTED_OUTPUT}", self.body)

    def test_control_and_profile_ownership_rules_are_absent(self) -> None:
        source = "\n".join(
            (
                self.body,
                self.reference,
                json.dumps(self.entry, sort_keys=True),
            )
        ).casefold()
        for forbidden in (
            "select a static agent profile",
            "define one static tool-permission boundary",
            "analysis: read and search only",
            "task: bounded read, search, edit, and execute",
            "route review repairs",
            "host-native permissions",
            "prompt-enforced",
            "ask the user",
            "ordinary bounded subagents",
            "approval",
            "parallel writes",
            "same-path failures",
            "fresh validation",
            "re-review",
            "evidence ledger",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_root_uses_concise_progressive_disclosure_order(self) -> None:
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

    def test_reference_table_exactly_matches_registry_contract(self) -> None:
        contracts = reference_contracts(
            self.entry["reference_index"],
            "foundation-skills.yaml:agent-tool-permission-sandbox.reference_index",
            owner="agent-tool-permission-sandbox",
        )
        self.assertEqual(
            self.source,
            render_targeted_reference_section(
                self.source,
                contracts,
                "agent-tool-permission-sandbox",
            ),
        )
        self.assertEqual(
            ["checklist-result", "residual-risk"],
            contracts[0]["required_output"],
        )


if __name__ == "__main__":
    unittest.main()
