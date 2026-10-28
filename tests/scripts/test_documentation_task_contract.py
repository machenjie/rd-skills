"""Static delivery regressions; these fixtures do not simulate an LLM writer."""

from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build
import deterministic_route_oracle as ORACLE
from fixture_capsule_contract import (
    FIXTURE_HOST_SKILLS_ROOT,
    FixtureCapsuleError,
    validate_and_render_fixture_capsule,
)
from validation_utils import load_yaml_file, reference_contracts


OWNER = "change-documentation-gate"
DIAGRAM = "references/engineering-diagrams.md"
SOURCE = ROOT / "src/professional-skills" / OWNER

# Assigned contexts are test inputs, not live captures or a new routing oracle.
DOCUMENT_TASKS = (
    ("typo", "Correct the misspelling in the supplied README sentence; behavior is unchanged.", []),
    ("three-steps", "Draw the supplied steps: receive request, validate input, return result. No new decisions are needed.", [DIAGRAM]),
    ("calls", "Document accepted client/API/worker calls, including asynchronous acknowledgement, retry and failure responses.", [DIAGRAM]),
    ("deployment", "Document the accepted deployment of API and worker replicas to hosts, preserving the network boundary and labelled dependencies.", [DIAGRAM]),
    ("async-state", "Document the accepted queued/running/succeeded/failed/cancelled job states, timeout transition and late completion rule.", [DIAGRAM]),
)


class DocumentationTaskContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        cls.owner = next(row for row in cls.registry["professional_skills"] if row["name"] == OWNER)
        cls.cases = {
            case["id"]: case
            for case in load_yaml_file(ROOT / "evals/routing/cases.yaml")["cases"]
        }

    def test_existing_docs_only_routes_are_not_rejected_by_owner_inputs(self) -> None:
        for case_id in (
            "structure-pattern-word-comment-only",
            "structure-documentation-only-module-wording",
        ):
            case = self.cases[case_id]
            with self.subTest(case=case_id):
                routed = ORACLE.route(case["prompt"], main_execution=case["main_execution"])
                self.assertEqual(OWNER, routed["route_result"]["primary_skill"])
        # These old unconditional requirements contradicted both existing routes.
        self.assertNotIn("no audience facing change", self.owner["anti_trigger_signals"])
        self.assertNotIn("changed behavior summary", self.owner["required_inputs"])
        self.assertNotIn("behavior mapping", self.owner["output_contract_by_role"]["task-agent"])

    def test_supplied_docs_tasks_need_no_layer3_or_extra_artifacts(self) -> None:
        for role in ("task-agent", "review-agent"):
            for case_id, goal, references in DOCUMENT_TASKS:
                with self.subTest(role=role, case=case_id):
                    rendered = validate_and_render_fixture_capsule({
                        "profile": role,
                        "primary_skill": OWNER,
                        "goal": goal,
                        "layer3_skills": [],
                        "professional_references": references,
                        "layer3_references": [],
                    })
                    self.assertIn("Layer 3 exact: []", rendered)
                    self.assertNotIn("References unresolved", rendered)
                    self.assertNotIn("engineering-brief-template", rendered)
                    self.assertNotIn("documentation-generation", rendered)
                    self.assertEqual(bool(references), DIAGRAM in rendered)

    def test_reference_is_local_jit_delivery_with_both_documentation_roles(self) -> None:
        contracts = reference_contracts(self.owner["reference_index"], OWNER, owner=OWNER)
        diagram = next((item for item in contracts if item["path"] == DIAGRAM), None)
        self.assertIsNotNone(diagram, "the documentation owner has no diagram Reference")
        assert diagram is not None
        self.assertEqual("targeted", diagram["type"])
        self.assertEqual(["task-agent", "review-agent"], diagram["required_by"])
        self.assertTrue((SOURCE / DIAGRAM).is_file())
        for row in self.registry["professional_skills"]:
            if row["name"] != OWNER:
                self.assertNotIn(DIAGRAM, [item["path"] for item in row["reference_index"]])

        # Exercise the actual authoring -> Runtime record projection; the same
        # conditions and outputs must survive without importing a Layer 3 owner.
        payload = {
            "professional_skill": OWNER,
            "reference_records": [dict(diagram, owner_skill=OWNER, owner_layer="professional")],
        }
        before = copy.deepcopy(payload)
        projected = build._project_runtime_reference_partition(payload, OWNER, "fixture-build")
        self.assertEqual(before, payload)
        self.assertEqual({"reference_records": [diagram]}, projected)
        payload["professional_skill"] = "backend-change-builder"
        with self.assertRaisesRegex(build.BuildError, "not local"):
            build._project_runtime_reference_partition(payload, "backend-change-builder", "fixture-build")

    def test_compact_root_keeps_owner_rules_without_eager_reference_body(self) -> None:
        source = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw)
            (destination / "SKILL.md").write_text(source, encoding="utf-8")
            build._write_compact_professional_projection(destination, SimpleNamespace(name=OWNER))
            rendered = (destination / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn(DIAGRAM, rendered)
        self.assertIn(f"references/runtime/reference-records/{OWNER}.json", rendered)
        for heading in build.PROFESSIONAL_BUILT_KERNEL_HEADINGS:
            self.assertIn(f"## {heading}\n", rendered)
        self.assertNotIn("otherwise require a source-backed no-docs decision", rendered)

    def test_implementation_and_unresolved_architecture_keep_existing_owners(self) -> None:
        architecture = self.cases["structure-documentation-with-runtime-architecture-change"]
        routed = ORACLE.route(architecture["prompt"], main_execution=architecture["main_execution"])
        self.assertEqual("architecture-impact-reviewer", routed["route_result"]["primary_skill"])
        for primary, goal in (
            ("backend-change-builder", "Implement the accepted API change and update its documentation."),
            ("backend-change-builder", "Fix the backend calculation; no documentation deliverable is requested."),
            ("architecture-impact-reviewer", "Resolve the service boundary before documenting a proposed deployment."),
        ):
            role = "analysis-agent" if primary == "architecture-impact-reviewer" else "task-agent"
            step = dict(profile=role, primary_skill=primary, goal=goal,
                        layer3_skills=[], professional_references=[], layer3_references=[])
            with self.subTest(primary=primary, goal=goal):
                rendered = validate_and_render_fixture_capsule(step)
                self.assertIn(str(FIXTURE_HOST_SKILLS_ROOT / primary / "SKILL.md"), rendered)
                self.assertNotIn(DIAGRAM, rendered)
                step["professional_references"] = [DIAGRAM]
                with self.assertRaisesRegex(FixtureCapsuleError, "current and authorized"):
                    validate_and_render_fixture_capsule(step)


if __name__ == "__main__":
    unittest.main()
