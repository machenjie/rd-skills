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


SKILL_DIR = ROOT / "src/foundation/capabilities/targeted-validation-selection"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
CONSUMER_FILE = ROOT / "src/professional-skills/quality-test-gate/SKILL.md"
ROUTER_FILE = (
    ROOT
    / "src/control-skills/engineering-control-plane/references/professional-skill-router.md"
)
OLD_REFERENCE = SKILL_DIR / "references/validation-selection-checklist.md"

EXPECTED_INPUTS = [
    "accepted proof strategy and observable acceptance",
    "changed paths and material risk surfaces",
    "repository guidance command definitions and existing tests",
    "command targets mutation surfaces hooks/subprocesses credentials external "
    "effects authority recovery cleanup and retained-output constraints",
    "available command results and freshness input/hash/time facts",
]
EXPECTED_REFERENCES = ["references/repository-command-entry-evidence.md"]
EXPECTED_OUTPUT_FIELDS = [
    "Repository-entrypoint inspection evidence covering "
    "test/build/schema/lint/static/generator entrypoints and existing tests.",
    "Record exact smallest-sufficient commands.",
    "Map observable-acceptance and risk-surface coverage per command.",
    "Record the expected signal.",
    "Record command target, working directory, mutation/external-effect "
    "classification, credentials/authority, stop condition, recovery, cleanup, "
    "and retained-output boundary before execution.",
    "Record the actual result when run.",
    "Record freshness input/hash/time facts.",
    "Record the unavailable-entry fallback.",
    "State unverified scope, proof limits, and residual risk.",
]


def _load_capability_validator():
    spec = importlib.util.spec_from_file_location(
        "rds_006_targeted_validation_capability_validator",
        SCRIPTS / "validate-capabilities.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-capabilities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAPABILITY_VALIDATOR = _load_capability_validator()


class TargetedValidationSelectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SKILL_FILE.read_text(encoding="utf-8")
        cls.metadata, _raw, cls.body = parse_frontmatter(SKILL_FILE)
        cls.reference_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((SKILL_DIR / "references").glob("*.md"))
        )
        foundation_entries = load_yaml_file(REGISTRY)["foundation_skills"]
        cls.entry = next(
            entry
            for entry in foundation_entries
            if entry["name"] == "targeted-validation-selection"
        )
        professional_entries = load_yaml_file(PROFESSIONAL_REGISTRY)[
            "professional_skills"
        ]
        cls.consumer_entry = next(
            entry for entry in professional_entries if entry["name"] == "quality-test-gate"
        )
        cls.consumer = CONSUMER_FILE.read_text(encoding="utf-8")
        cls.router = ROUTER_FILE.read_text(encoding="utf-8")

    def test_unique_repository_command_entry_selection_remains(self) -> None:
        source = f"{self.body}\n{self.reference_text}".casefold()
        for term in (
            "repository-defined",
            "test/build/schema/lint/static/generator entrypoints",
            "existing tests",
            "observable acceptance",
            "risk surface",
            "smallest-sufficient commands",
            "command coverage",
            "expected signal",
            "actual result when run",
            "freshness input/hash/time facts",
            "unavailable-entry fallback",
            "unverified scope",
            "proof limits",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)
        self.assertEqual(EXPECTED_OUTPUT_FIELDS, self.entry["output_contract"])
        output_section = CAPABILITY_VALIDATOR._section(
            self.body,
            "Output Contract",
        )
        parsed_outputs, output_errors = CAPABILITY_VALIDATOR._output_contract_items(
            output_section
        )
        self.assertEqual([], output_errors)
        self.assertEqual(
            EXPECTED_OUTPUT_FIELDS,
            parsed_outputs,
        )

    def test_strategy_control_profile_and_closure_duplicates_are_absent(self) -> None:
        source = "\n".join(
            (self.body, self.reference_text, json.dumps(self.entry, sort_keys=True))
        ).casefold()
        for forbidden in (
            "test-first",
            "test strategy",
            "test hierarchy",
            "smallest sufficient test level",
            "regression mechanism",
            "negative path",
            "test pyramid",
            "active profile",
            "profile's",
            "execute capability",
            "task contract",
            "workspace-writing",
            "non-modifying",
            "permission",
            "approval",
            "destructive",
            "privileged",
            "production-facing",
            "irreversible",
            "last material edit",
            "final material edit",
            "review execution",
            "closure",
            "retry",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertIn(
            "keep a safely selected but unauthorized command unrun and record "
            "the missing execution authority",
            source,
        )
        for forbidden_authority_claim in (
            "grant authority",
            "approve authority",
            "supply authority",
            "authorize an external action",
            "perform an external action",
        ):
            with self.subTest(
                forbidden_authority_claim=forbidden_authority_claim
            ):
                self.assertNotIn(forbidden_authority_claim, source)

    def test_consumer_owns_strategy_acceptance_freshness_and_final_verdict(self) -> None:
        self.assertEqual(
            ["quality-test-gate", "repository-tooling-change-builder"],
            self.entry["used_by"],
        )
        self.assertIn(
            "targeted-validation-selection",
            self.consumer_entry["layer3_candidates"],
        )
        decision_section = re.search(
            r"(?ms)^## Professional Decision Rules\s*$\n(?P<body>.*?)(?=^## )",
            self.consumer,
        )
        self.assertIsNotNone(decision_section)
        consumer_rules = {
            re.sub(r"\s+", " ", line[2:].strip())
            for line in decision_section.group("body").splitlines()
            if line.startswith("- ")
        }
        layer3_rule = (
            "Use `targeted-validation-selection` only after strategy selection, "
            "and only for repository-defined command and coverage selection."
        )
        self.assertIn(
            "Own proof strategy and acceptance-to-signal mapping before command "
            "selection.",
            consumer_rules,
        )
        self.assertIn(layer3_rule, consumer_rules)
        self.assertIn(
            "Leave evidence timing and refresh decisions to Core Guard G and the "
            "validation-freshness contract.",
            consumer_rules,
        )
        layer3_mentions = [
            re.sub(r"\s+", " ", line.strip())
            for line in self.consumer.splitlines()
            if "targeted-validation-selection" in line
        ]
        self.assertEqual([f"- {layer3_rule}"], layer3_mentions)
        self.assertRegex(
            self.router,
            r"\| explicit test-data or test-strategy analysis \| analysis-agent "
            r"\| quality-test-gate \|",
        )

    def test_registry_and_reference_projection_are_exact(self) -> None:
        self.assertEqual(EXPECTED_INPUTS, self.entry["required_inputs"])
        contracts = reference_contracts(
            self.entry["reference_index"],
            "foundation-skills.yaml:targeted-validation-selection.reference_index",
            owner="targeted-validation-selection",
        )
        self.assertEqual(
            EXPECTED_REFERENCES,
            [contract["path"] for contract in contracts],
        )
        self.assertEqual(
            self.source,
            render_targeted_reference_section(
                self.source,
                contracts,
                "targeted-validation-selection",
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
                "Stop Conditions",
                "Output Contract",
                "Targeted References",
            ],
            headings,
        )
        description_words = re.findall(
            r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?",
            self.metadata["description"],
        )
        self.assertLessEqual(len(description_words), 24)
        self.assertLessEqual(len(self.body.splitlines()), 90)
        self.assertEqual("product", self.entry["delivery_scope"])
        self.assertFalse(OLD_REFERENCE.exists())


if __name__ == "__main__":
    unittest.main()
