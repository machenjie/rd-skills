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


SKILL_DIR = ROOT / "src/foundation/capabilities/agent-execution-discipline"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REGISTRY = ROOT / "src/registry/foundation-skills.yaml"
AI_REVIEW_FILE = ROOT / "src/professional-skills/ai-code-review-refactor/SKILL.md"
PROFESSIONAL_REGISTRY = ROOT / "src/registry/professional-skills.yaml"
CORE_EXECUTION_CONTRACT = (
    ROOT
    / "src/control-skills/engineering-control-plane/references/execution-level-contract.md"
)
CORE_CONTRACTS = ROOT / "src/control-model/core-contracts.json"
LIGHTWEIGHT_EVALUATOR = ROOT / "scripts/eval-agent-lightweight.py"
PRESSURE_EVALUATOR = ROOT / "scripts/eval-pressure-behavior.py"
BENCHMARK_REFERENCE = (
    ROOT
    / "src/foundation/capabilities/skill-efficacy-benchmark/references/benchmarks-and-patterns.md"
)

EXPECTED_OUTPUT = (
    "execution-evidence assessment with claim, source, freshness, scope, "
    "reproducibility, reuse decision, invalid evidence, reusable evidence, "
    "contradictions, proof limit, and residual uncertainty"
)
EXPECTED_REFERENCES = {
    "references/checklist.md",
    "references/evidence-reuse-patterns.md",
}


def _load_capability_validator():
    spec = importlib.util.spec_from_file_location(
        "rds_006_agent_execution_capability_validator",
        SCRIPTS / "validate-capabilities.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-capabilities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAPABILITY_VALIDATOR = _load_capability_validator()


class AgentExecutionDisciplineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SKILL_FILE.read_text(encoding="utf-8")
        cls.metadata, _raw, cls.body = parse_frontmatter(SKILL_FILE)
        cls.reference_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((SKILL_DIR / "references").glob("*.md"))
        )
        entries = load_yaml_file(REGISTRY)["foundation_skills"]
        cls.entry = next(
            entry
            for entry in entries
            if entry["name"] == "agent-execution-discipline"
        )
        cls.foundation_entries = {entry["name"]: entry for entry in entries}
        cls.ai_review_source = AI_REVIEW_FILE.read_text(encoding="utf-8")
        cls.core_execution_contract = CORE_EXECUTION_CONTRACT.read_text(
            encoding="utf-8"
        )
        cls.core_contracts = CORE_CONTRACTS.read_text(encoding="utf-8")
        cls.benchmark_reference = BENCHMARK_REFERENCE.read_text(encoding="utf-8")
        professional_entries = load_yaml_file(PROFESSIONAL_REGISTRY)[
            "professional_skills"
        ]
        cls.ai_review_entry = next(
            entry
            for entry in professional_entries
            if entry["name"] == "ai-code-review-refactor"
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

    def test_unique_execution_evidence_assessment_remains(self) -> None:
        source = f"{self.body}\n{self.reference_text}".casefold()
        for term in (
            "claim",
            "source",
            "freshness",
            "scope",
            "reproducibility",
            "reuse decision",
            "invalid evidence",
            "reusable evidence",
            "contradictions",
            "proof limit",
            "residual uncertainty",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)
        self.assertEqual([EXPECTED_OUTPUT], self.entry["output_contract"])
        self.assertIn(f"- {EXPECTED_OUTPUT}", self.body)

    def test_duplicate_control_and_profile_semantics_are_absent(self) -> None:
        source = "\n".join(
            (
                self.body,
                self.reference_text,
                json.dumps(self.entry, sort_keys=True),
            )
        ).casefold()
        for forbidden in (
            "complete/all checks pass",
            "verified cause before accepting",
            "change route after two",
            "same-pattern scan",
            "same defect pattern",
            "reuse and placement rationale",
            "after the last material edit",
            "fresh validation",
            "re-review",
            "implementation handoff",
            "execution handoff",
            "task contract",
            "commands run",
            "route the result",
            "review repairs",
            "read and search only",
            "bounded read, search, edit, and execute",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_only_evidence_assessment_references_remain(self) -> None:
        paths = {
            contract["path"]
            for contract in reference_contracts(
                self.entry["reference_index"],
                "foundation-skills.yaml:agent-execution-discipline.reference_index",
                owner="agent-execution-discipline",
            )
        }
        self.assertEqual(EXPECTED_REFERENCES, paths)
        self.assertFalse(
            (SKILL_DIR / "references/execution-report-and-gates.md").exists()
        )
        self.assertFalse((SKILL_DIR / "examples/example-output.md").exists())

    def test_root_and_registry_projections_are_exact(self) -> None:
        trigger_section = CAPABILITY_VALIDATOR._section(
            self.body,
            "Registry Trigger",
        )
        self.assertEqual(
            [],
            CAPABILITY_VALIDATOR._registry_trigger_errors(trigger_section),
        )
        contracts = reference_contracts(
            self.entry["reference_index"],
            "foundation-skills.yaml:agent-execution-discipline.reference_index",
            owner="agent-execution-discipline",
        )
        self.assertEqual(
            self.source,
            render_targeted_reference_section(
                self.source,
                contracts,
                "agent-execution-discipline",
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

    def test_ai_review_consumer_keeps_control_and_regression_owners(self) -> None:
        source = self.ai_review_source.casefold()
        normalized_source = re.sub(r"\s+", " ", source)
        self.assertNotIn("agent-execution-discipline", source)
        self.assertNotIn("twice-failed route", source)
        self.assertIn("inaccessible diff", source)
        self.assertIn("stale evidence", source)
        self.assertIn("reachable failure path", source)
        self.assertNotIn("core `retry_policy`", source)
        self.assertIn("return out-of-boundary risk to main", normalized_source)
        self.assertIn("block on inaccessible diff", normalized_source)
        self.assertIn(
            '"unchanged_retry_after_limit":"return-to-main-or-block"',
            self.core_execution_contract,
        )
        self.assertNotIn("`regression-testing`", source)

        candidates = self.ai_review_entry["layer3_candidates"]
        self.assertIn("regression-testing", candidates)
        regression_owner = self.foundation_entries["regression-testing"]
        self.assertEqual("product", regression_owner["delivery_scope"])
        self.assertIn("review-agent", regression_owner["role_support"])
        self.assertIn("ai-code-review-refactor", regression_owner["used_by"])

    def test_benchmark_routes_control_behaviors_to_core_and_evaluators(self) -> None:
        source = self.benchmark_reference.casefold()
        self.assertNotIn(
            "completion/pressure behavior to `agent-execution-discipline`",
            source,
        )
        self.assertNotIn("agent-execution-discipline", source)
        self.assertIn(
            "context-boundary questions to `task-context-selection`",
            source,
        )
        for term in (
            "completion",
            "execution-level",
            "retry",
            "review",
            "`src/control-model/core-contracts.json`",
            "`scripts/eval-agent-lightweight.py`",
            "`scripts/eval-pressure-behavior.py`",
        ):
            with self.subTest(term=term):
                self.assertIn(term, source)

        for path in (CORE_CONTRACTS, LIGHTWEIGHT_EVALUATOR, PRESSURE_EVALUATOR):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
        for key in (
            '"completion_state"',
            '"execution_level_contract"',
            '"retry_policy"',
            '"review_discipline_contract"',
        ):
            with self.subTest(key=key):
                self.assertIn(key, self.core_contracts)


if __name__ == "__main__":
    unittest.main()
