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


SKILL_DIR = ROOT / "src/foundation/capabilities/task-context-selection"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCE_FILE = SKILL_DIR / "references/context-selection-checklist.md"
REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
BENCHMARK_REFERENCE = (
    ROOT
    / "src/foundation/capabilities/skill-efficacy-benchmark/references/benchmarks-and-patterns.md"
)

EXPECTED_OUTPUT = (
    "working-context selection with current decision, selected facts and "
    "artifacts, source, freshness, decision use, selected Layer 3 Skills and "
    "References, excluded context, refresh triggers, omissions, uncertainty, "
    "context-budget tradeoff, and residual risk"
)


def _load_capability_validator():
    spec = importlib.util.spec_from_file_location(
        "rds_006_task_context_capability_validator",
        SCRIPTS / "validate-capabilities.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-capabilities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAPABILITY_VALIDATOR = _load_capability_validator()


class TaskContextSelectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SKILL_FILE.read_text(encoding="utf-8")
        cls.metadata, _raw, cls.body = parse_frontmatter(SKILL_FILE)
        cls.reference = REFERENCE_FILE.read_text(encoding="utf-8")
        entries = load_yaml_file(REGISTRY)["foundation_skills"]
        cls.entry = next(
            entry for entry in entries if entry["name"] == "task-context-selection"
        )
        cls.benchmark = BENCHMARK_REFERENCE.read_text(encoding="utf-8")

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

    def test_unique_working_context_decision_remains(self) -> None:
        source = f"{self.body}\n{self.reference}".casefold()
        for term in (
            "current decision",
            "facts and artifacts",
            "source identity",
            "freshness basis",
            "decision use",
            "layer 3 skills",
            "references",
            "irrelevant",
            "stale",
            "redundant",
            "material state change",
            "omissions",
            "uncertainty",
            "context-budget tradeoff",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)
        self.assertEqual([EXPECTED_OUTPUT], self.entry["output_contract"])
        self.assertIn(f"- {EXPECTED_OUTPUT}", self.body)

    def test_control_profile_and_transfer_responsibilities_are_absent(self) -> None:
        source = "\n".join(
            (self.body, self.reference, json.dumps(self.entry, sort_keys=True))
        ).casefold()
        for forbidden in (
            "one primary professional skill",
            "selected primary professional skill",
            "task-local trigger evidence",
            "for one isolated agent",
            "bounded dispatched task",
            "task capsule",
            "review handoff",
            "scope, acceptance, verification",
            "load a reference only when its trigger",
            "read and search only",
            "bounded read, search, edit",
            "complete/all checks pass",
            "twice-failed",
            "retry",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_working_context_boundary_precedes_downstream_transfer(self) -> None:
        normalized = re.sub(r"\s+", " ", self.body.casefold())
        self.assertIn("before or during one decision", normalized)
        self.assertIn("downstream transfer", normalized)
        self.assertIn("`task-handoff-context` owns", normalized)

    def test_registry_and_reference_projection_are_exact(self) -> None:
        contracts = reference_contracts(
            self.entry["reference_index"],
            "foundation-skills.yaml:task-context-selection.reference_index",
            owner="task-context-selection",
        )
        self.assertEqual(["references/context-selection-checklist.md"], [
            contract["path"] for contract in contracts
        ])
        self.assertEqual(
            self.source,
            render_targeted_reference_section(
                self.source,
                contracts,
                "task-context-selection",
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

    def test_direct_benchmark_route_remains_available(self) -> None:
        self.assertIn(
            "context-boundary questions to `task-context-selection`",
            self.benchmark,
        )


if __name__ == "__main__":
    unittest.main()
