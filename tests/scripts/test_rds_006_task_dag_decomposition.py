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
import build as BUILD  # noqa: E402


SKILL_DIR = ROOT / "src/foundation/capabilities/task-dag-decomposition"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
PLANNER_FILE = ROOT / "src/professional-skills/task-dag-planner/SKILL.md"
ROUTER_FILE = (
    ROOT
    / "src/control-skills/engineering-control-plane/references/professional-skill-router.md"
)
ROUTING_SCENARIOS = ROOT / "src/registry/release-routing-scenarios.yaml"
EXAMPLE_FILE = SKILL_DIR / "examples/example-output.md"

EXPECTED_OUTPUT = (
    "candidate-graph evidence with acceptance-linked nodes, produced outputs, "
    "evidence-backed data/control/contract/order edges, rejected edges, "
    "collision/shared-write/resource surfaces, candidate critical path, "
    "parallel opportunity, cycles, uncertainty, proof limits, and residual "
    "risk for consumer acceptance or rejection"
)
EXPECTED_REFERENCES = ["references/candidate-graph-evidence.md"]


class TaskDagDecompositionContractTests(unittest.TestCase):
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
            if entry["name"] == "task-dag-decomposition"
        )
        professional_entries = load_yaml_file(PROFESSIONAL_REGISTRY)[
            "professional_skills"
        ]
        cls.professional_entries = {
            entry["name"]: entry for entry in professional_entries
        }
        cls.planner = PLANNER_FILE.read_text(encoding="utf-8")
        cls.router = ROUTER_FILE.read_text(encoding="utf-8")
        cls.routing_scenarios = ROUTING_SCENARIOS.read_text(encoding="utf-8")

    def test_unique_candidate_graph_evidence_remains(self) -> None:
        source = f"{self.body}\n{self.reference_text}".casefold()
        for term in (
            "candidate nodes",
            "acceptance-linked",
            "produced outputs",
            "data edge",
            "control edge",
            "contract edge",
            "order edge",
            "evidence-backed",
            "rejected edges",
            "collision surfaces",
            "shared-write surfaces",
            "resource surfaces",
            "candidate critical path",
            "parallel opportunity",
            "cycles",
            "uncertainty",
            "proof limits",
            "consumer acceptance or rejection",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)
        self.assertEqual([EXPECTED_OUTPUT], self.entry["output_contract"])
        self.assertIn(f"- {EXPECTED_OUTPUT}", self.body)

    def test_control_profile_and_final_dag_semantics_are_absent(self) -> None:
        source = "\n".join(
            (self.body, self.reference_text, json.dumps(self.entry, sort_keys=True))
        ).casefold()
        for forbidden in (
            "first executable slice",
            "direct task",
            "task contract v2",
            "host provides isolated",
            "host-isolated",
            "shared or unknown workspace",
            "serialize",
            "serial when",
            "integration owner",
            "merge owner",
            "conflict resolution owner",
            "combined validation",
            "combined review",
            "fresh validation",
            "re-review",
            "review blocker",
            "workspace isolation capability",
            "final validation",
            "closure",
            "retry",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_final_dag_boundary_and_consumers_remain_registered(self) -> None:
        normalized = re.sub(r"\s+", " ", self.body.casefold())
        self.assertIn("pre-dag candidate graph", normalized)
        self.assertIn("does not emit the final task dag", normalized)
        self.assertIn("consumer accepts or rejects", normalized)
        self.assertEqual(
            ["task-dag-planner"],
            self.entry["used_by"],
        )
        for owner in self.entry["used_by"]:
            with self.subTest(owner=owner):
                self.assertIn(
                    "task-dag-decomposition",
                    self.professional_entries[owner]["layer3_candidates"],
                )
        decision_section = re.search(
            r"(?ms)^## Professional Decision Rules\s*$\n(?P<body>.*?)(?=^## )",
            self.planner,
        )
        self.assertIsNotNone(decision_section)
        planner_rules = {
            re.sub(r"\s+", " ", line[2:].strip())
            for line in decision_section.group("body").splitlines()
            if line.startswith("- ")
        }
        layer3_rule = (
            "Inspect `task-dag-decomposition` candidate-graph evidence for "
            "nodes, edges, blockers, critical path, collisions, uncertainty, "
            "and proof limits."
        )
        self.assertEqual(
            [layer3_rule],
            sorted(rule for rule in planner_rules if "task-dag-decomposition" in rule),
        )
        layer3_mentions = [
            re.sub(r"\s+", " ", line.strip())
            for line in self.planner.splitlines()
            if "task-dag-decomposition" in line
        ]
        self.assertEqual([f"- {layer3_rule}"], layer3_mentions)
        self.assertNotRegex(
            " ".join(layer3_mentions).casefold(),
            r"first executable slice|\bfes\b",
        )
        self.assertIn(
            "Accept or reject each node and edge with an evidence-backed "
            "reason before construction.",
            planner_rules,
        )
        self.assertTrue(
            {
                "Preserve its First Executable Slice verbatim.",
                "Never select the First Executable Slice.",
                "Never replace the First Executable Slice.",
                "Never reinterpret the First Executable Slice.",
            }.issubset(planner_rules),
            planner_rules,
        )
        self.assertIn(
            "never modify acceptance, non-goals, owner, invariants, placement, "
            "contract semantics, or rollback. a task dag and its nodes are "
            "derived artifacts, not a parallel analysis authority.",
            decision_section.group("body").casefold().replace("\n  ", " "),
        )
        self.assertIn("task-dag-decomposition", self.router)
        self.assertNotIn("layer3: [task-dag-decomposition]", self.routing_scenarios)
        self.assertIn("control_path: direct", self.routing_scenarios)
        self.assertIn("analysis: null", self.routing_scenarios)

    def test_registry_and_reference_projection_are_exact(self) -> None:
        h1_titles, _sections = BUILD._markdown_heading_sections(self.body)
        self.assertEqual(["task-dag-decomposition"], h1_titles)
        contracts = reference_contracts(
            self.entry["reference_index"],
            "foundation-skills.yaml:task-dag-decomposition.reference_index",
            owner="task-dag-decomposition",
        )
        self.assertEqual(EXPECTED_REFERENCES, [
            contract["path"] for contract in contracts
        ])
        self.assertEqual(
            self.source,
            render_targeted_reference_section(
                self.source,
                contracts,
                "task-dag-decomposition",
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
        description_words = re.findall(
            r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?",
            self.metadata["description"],
        )
        self.assertLessEqual(len(description_words), 24)
        self.assertLessEqual(len(self.body.splitlines()), 90)
        self.assertEqual("product", self.entry["delivery_scope"])
        self.assertFalse(EXAMPLE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
