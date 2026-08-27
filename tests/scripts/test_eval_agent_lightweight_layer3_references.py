from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval-agent-lightweight.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "eval_agent_lightweight_layer3_reference_tests", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL = _load_module()

from fixture_capsule_contract import canonical_capsule_sha256
from validation_utils import load_yaml_file


class LightweightLayer3ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        cls.case = next(case for case in cls.document["cases"] if case["id"] == "data-migration")
        cls.step = cls.case["steps"][6]
        cls.professional, cls.layer3 = EVAL._skill_registries()
        cls.rag_authority = load_yaml_file(
            ROOT
            / "evals/codegen/ai/rag-tenant-permission-filter/expected-qualities.yaml"
        )

    @classmethod
    def _dispatch(
        cls,
        case_id: str,
        profile: str,
        *,
        task_id: str | None = None,
    ) -> dict:
        groups = (
            cls.document["cases"],
            cls.document["scheduling_cases"],
            cls.document["utility_cases"],
        )
        case = next(
            case
            for group in groups
            for case in group
            if case["id"] == case_id
        )
        return next(
            step
            for step in case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == profile
            and (task_id is None or step.get("task_id") == task_id)
        )

    def test_fixture_covers_exact_nested_reference_contracts(self) -> None:
        groups = (
            self.document["cases"],
            self.document["scheduling_cases"],
            self.document["utility_cases"],
        )
        cases = [case for group in groups for case in group]
        dispatches = [
            step
            for case in cases
            for step in case["steps"]
            if step.get("action") == "dispatch"
        ]
        logical_ids = [
            logical_id
            for step in dispatches
            for logical_id in step.get("layer3_references", [])
        ]
        fixture_dispatch_count = sum(
            step.get("action") == "dispatch"
            for case in cases
            for step in case["steps"]
        )
        self.assertEqual(16, len(cases))
        self.assertEqual(fixture_dispatch_count, len(dispatches))
        self.assertEqual(8, len(logical_ids))
        self.assertLessEqual(
            max(len(step.get("layer3_references", [])) for step in dispatches),
            2,
        )

        security = self._dispatch("security-ssrf-boundary", "task-agent")
        self.assertEqual(
            ["web-security/references/checklist.md"],
            security["layer3_references"],
        )
        self.assertEqual(
            ["threat-modeling", "web-security"],
            security["layer3_skills"],
        )
        self.assertNotIn("ai-product-extension", security["layer3_skills"])

        for direct_dag_case_id in (
            "isolated-write-parallel-contract",
            "shared-workspace-serial-write",
        ):
            with self.subTest(direct_dag_case_id=direct_dag_case_id):
                direct_dag_case = next(
                    case for case in cases if case["id"] == direct_dag_case_id
                )
                self.assertEqual("direct", direct_dag_case["kind"])
                self.assertFalse(
                    any(
                        step.get("actor") == "analysis-agent"
                        or step.get("profile") == "analysis-agent"
                        for step in direct_dag_case["steps"]
                    )
                )

        rag_task = self._dispatch(
            "shared-workspace-serial-write",
            "task-agent",
            task_id="task-shared-workspace-serial-write-2",
        )
        authority = self.rag_authority["route_hints"]
        self.assertEqual(
            authority["primary_skill"],
            rag_task["primary_skill"],
        )
        self.assertEqual(
            authority["layer3_skills"],
            rag_task["layer3_skills"],
        )
        self.assertEqual(
            ["ai-product-extension/references/checklist.md"],
            rag_task["layer3_references"],
        )
        rag_capsule = json.dumps(rag_task["fixture_capsule"]).casefold()
        for phrase in (
            "ai product surface",
            "tenant and object permission filters",
            "before prompt context assembly",
            "revoked-access",
        ):
            self.assertIn(phrase, rag_capsule)
        rag_review = self._dispatch(
            "shared-workspace-serial-write",
            "review-agent",
        )
        self.assertEqual(
            authority["review_skill"],
            rag_review["primary_skill"],
        )
        self.assertEqual(
            ["references/security-output-and-gates.md"],
            rag_review["professional_references"],
        )
        self.assertIn(
            "ai-product-extension",
            self.professional["integration-change-builder"]["layer3_candidates"],
        )

        reliability = self._dispatch(
            "cache-stampede-reliability", "review-agent"
        )
        self.assertEqual(
            ["references/evidence-patterns.md"],
            reliability["professional_references"],
        )

        release = self._dispatch("release-rollback", "task-agent")
        self.assertEqual(
            [
                "release-rollback/references/benchmarks-and-patterns.md",
                "release-rollback/references/evidence-patterns.md",
            ],
            release["layer3_references"],
        )

        source_backed = self._dispatch(
            "source-backed-payment-retry-proof", "analysis-agent"
        )
        self.assertEqual(
            ["references/source-backed-answer.md"],
            source_backed["professional_references"],
        )

    def test_module_boundary_benchmark_review_has_exact_owner_contract(
        self,
    ) -> None:
        case = next(
            case
            for case in self.document["cases"]
            if case["id"] == "module-boundary-benchmark-review"
        )
        review = self._dispatch(
            "module-boundary-benchmark-review",
            "review-agent",
        )
        self.assertEqual(
            {
                "kind": "direct",
                "profile": "review-agent",
                "primary_skill": "architecture-impact-reviewer",
                "review_skill": "architecture-impact-reviewer",
                "mode": "implementation-review",
                "layer3_skills": ["module-boundary-design"],
                "layer3_references": [
                    "module-boundary-design/references/benchmarks-and-enforcement.md"
                ],
                "professional_references": [],
                "execution_level": "L4",
            },
            {
                "kind": case["kind"],
                "profile": review["profile"],
                "primary_skill": review["primary_skill"],
                "review_skill": review["primary_skill"],
                "mode": review["mode"],
                "layer3_skills": review["layer3_skills"],
                "layer3_references": review["layer3_references"],
                "professional_references": review["professional_references"],
                "execution_level": review["fixture_capsule"][
                    "execution_level_extension"
                ]["effective_level"],
            },
        )
        self.assertEqual(
            "065d07de9cff56cc7866265bc3d593eac4057cc21a8368b1043d5beb80400008",
            review["fixture_capsule"]["canonical_sha256"],
        )
        self.assertEqual(
            review["fixture_capsule"]["canonical_sha256"],
            canonical_capsule_sha256(review, review["fixture_capsule"]),
        )

    def test_positive_selection_is_valid_and_does_not_inflate_skill_count(self) -> None:
        metrics, errors = EVAL._metrics(
            copy.deepcopy(self.case), self.professional, self.layer3
        )
        without_nested = copy.deepcopy(self.case)
        without_nested["steps"][6]["layer3_references"] = []
        changed = without_nested["steps"][6]
        changed["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            changed, changed["fixture_capsule"]
        )
        without_metrics, without_errors = EVAL._metrics(
            without_nested, self.professional, self.layer3
        )
        self.assertEqual([], errors)
        self.assertEqual([], without_errors)
        self.assertEqual(1, metrics["loaded_layer3_reference_count"])
        self.assertEqual(0, without_metrics["loaded_layer3_reference_count"])
        self.assertEqual(
            metrics["loaded_skill_count"], without_metrics["loaded_skill_count"]
        )

    def test_owner_must_be_selected_in_same_dispatch(self) -> None:
        step = copy.deepcopy(self.step)
        step["layer3_references"] = [
            "cache-design/references/evidence-patterns.md"
        ]
        errors = EVAL._profile_errors(
            "owner-mismatch", [step], self.professional, self.layer3
        )
        self.assertTrue(any("must be selected" in error for error in errors), errors)

    def test_reference_must_be_registry_indexed(self) -> None:
        step = copy.deepcopy(self.step)
        step["layer3_references"] = [
            "transaction-consistency/references/not-indexed.md"
        ]
        step["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            step, step["fixture_capsule"]
        )
        errors = EVAL._profile_errors(
            "unindexed", [step], self.professional, self.layer3
        )
        self.assertTrue(any("not indexed" in error for error in errors), errors)

    def test_duplicates_and_more_than_three_are_rejected(self) -> None:
        duplicate = copy.deepcopy(self.step)
        duplicate["layer3_references"] *= 2
        errors = EVAL._layer3_reference_errors(
            "duplicate",
            0,
            duplicate,
            str(duplicate["primary_skill"]),
            duplicate["layer3_skills"],
            self.layer3,
        )
        self.assertTrue(any("repeats" in error for error in errors), errors)

        over = copy.deepcopy(self.step)
        over["layer3_references"] = [
            "transaction-consistency/references/evidence-patterns.md",
            "transaction-consistency/references/checklist.md",
            "transaction-consistency/references/benchmarks-and-patterns.md",
            "data-migration-design/references/evidence-patterns.md",
        ]
        errors = EVAL._layer3_reference_errors(
            "over",
            0,
            over,
            str(over["primary_skill"]),
            over["layer3_skills"],
            self.layer3,
        )
        self.assertTrue(any("more than three" in error for error in errors), errors)

    def test_missing_or_symlinked_built_reference_fails_closed(self) -> None:
        step = copy.deepcopy(self.step)
        owner = "transaction-consistency"
        logical_id = step["layer3_references"][0]
        manifest = {
            "profile": "recommended",
            "compiled_layer3_references": {
                "data-middleware-change-builder": [owner]
            },
            "top_level_skills": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            built = (
                dist
                / "recommended/data-middleware-change-builder/references/layer3"
                / owner
                / "references/evidence-patterns.md"
            )
            built.parent.mkdir(parents=True)
            with (
                mock.patch.object(EVAL, "DIST_SKILLS", dist),
                mock.patch.object(EVAL, "BUILD_PROFILES", ("recommended",)),
                mock.patch.object(
                    EVAL,
                    "_load_build_manifests",
                    return_value=({"recommended": manifest}, []),
                ),
            ):
                errors = EVAL._layer3_reference_errors(
                    "missing",
                    0,
                    step,
                    "data-middleware-change-builder",
                    step["layer3_skills"],
                    self.layer3,
                )
                self.assertTrue(any("missing or symlinked" in error for error in errors), errors)

                source = (
                    ROOT
                    / "src/foundation/capabilities/transaction-consistency"
                    / "references/evidence-patterns.md"
                )
                built.symlink_to(source)
                errors = EVAL._layer3_reference_errors(
                    "symlink",
                    0,
                    step,
                    "data-middleware-change-builder",
                    step["layer3_skills"],
                    self.layer3,
                )
                self.assertTrue(any("missing or symlinked" in error for error in errors), errors)
                self.assertEqual(logical_id, step["layer3_references"][0])

    def test_build_manifest_loader_requires_ai_consumption_format(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            profile_root = dist / "recommended"
            profile_root.mkdir(parents=True)
            manifest_path = profile_root / ".changeforge-build-manifest.json"
            for value in (None, "authoring-root-v1"):
                with self.subTest(value=value):
                    manifest = {"profile": "recommended"}
                    if value is not None:
                        manifest["compiled_layer3_format"] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with (
                        mock.patch.object(EVAL, "DIST_SKILLS", dist),
                        mock.patch.object(EVAL, "BUILD_PROFILES", ("recommended",)),
                    ):
                        manifests, errors = EVAL._load_build_manifests()
                    self.assertEqual({}, manifests)
                    self.assertTrue(
                        any("compiled_layer3_format must equal" in error for error in errors),
                        errors,
                    )


if __name__ == "__main__":
    unittest.main()
