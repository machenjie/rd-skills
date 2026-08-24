from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-rendered-context-budget.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "eval_rendered_context_budget_tests",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL = _load_module()

import build as BUILD  # noqa: E402

from fixture_capsule_contract import (
    FixtureCapsuleError,
    canonical_capsule_sha256,
    parse_layer3_reference_id,
    validate_and_render_fixture_capsule,
)


AUTHORITATIVE_DAG_INPUTS = [
    "Accepted, artifact-reviewed authoritative Task DAG and downstream "
    "Task Capsule",
    "Current source, tests, routed Professional Skill, and named Layer 3 "
    "guidance",
]
AUTHORITATIVE_DAG_EVIDENCE_BY_CASE = {
    "isolated-write-parallel-contract": (
        "Accepted, artifact-reviewed authoritative Task DAG selects three "
        "downstream integration tasks and final review."
    ),
    "shared-workspace-serial-write": (
        "Accepted, artifact-reviewed authoritative Task DAG selects two "
        "serialized downstream tasks and final review."
    ),
}
AUTHORITATIVE_DAG_NODES = {
    ("isolated-write-parallel-contract", 2): (
        "implementation-task",
        "Accepted authoritative Task DAG node and engineering-artifact-review "
        "pass.",
    ),
    ("isolated-write-parallel-contract", 3): (
        "implementation-task",
        "Accepted authoritative Task DAG node and engineering-artifact-review "
        "pass.",
    ),
    ("isolated-write-parallel-contract", 20): (
        "integration-task",
        "Completed authoritative Task DAG predecessor outputs and their "
        "current evidence.",
    ),
    ("shared-workspace-serial-write", 2): (
        "implementation-task",
        "Accepted authoritative Task DAG node and engineering-artifact-review "
        "pass.",
    ),
    ("shared-workspace-serial-write", 12): (
        "implementation-task",
        "Accepted authoritative Task DAG dependency plus completed predecessor "
        "output and current evidence.",
    ),
}


class RenderedContextBudgetTests(unittest.TestCase):
    _admissible_report_cache: dict[str, object] | None = None

    @classmethod
    def _admissible_report(cls) -> dict[str, object]:
        if cls._admissible_report_cache is None:
            cls._admissible_report_cache = EVAL.evaluate()[
                "admissible_context_compositions"
            ]
        return cls._admissible_report_cache

    def test_phase3_profile_and_analysis_mode_owners_are_isolated(self) -> None:
        profiles = json.loads(
            (ROOT / "src/agent-profiles/role-agents.json").read_text(
                encoding="utf-8"
            )
        )["profiles"]
        instructions = {item["name"]: item["instructions"] for item in profiles}
        source_targets = {
            "main-control-agent": 70,
            "analysis-agent": 230,
            "task-agent": 650,
            "review-agent": 510,
        }
        for role, target in source_targets.items():
            with self.subTest(role=role):
                self.assertLessEqual(
                    EVAL.count_o200k_base_tokens(instructions[role]), target
                )

        task_rules = instructions["task-agent"].splitlines()
        core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        for projection in core["implementation_discipline_contract"][
            "profile_projection"
        ]:
            rule = projection["exact_rule"]
            with self.subTest(task_rule=projection["rule_id"]):
                self.assertEqual(1, task_rules.count(rule))

        analysis_root = (
            ROOT / "src/professional-skills/engineering-change-analysis/SKILL.md"
        ).read_text(encoding="utf-8")
        implementation = (
            ROOT
            / "src/professional-skills/engineering-change-analysis/references/implementation-preparation.md"
        ).read_text(encoding="utf-8")
        for mode_only_term in (
            "Task Contract v2",
            "Delta Impact:",
            "## First Executable Slice",
        ):
            with self.subTest(mode_only_term=mode_only_term):
                self.assertNotIn(mode_only_term, analysis_root)
                self.assertIn(mode_only_term, implementation)

    def test_transfer_compaction_round_trips_every_valid_boundary(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        for _group, case in EVAL._fixture_cases(document):
            for boundary, projection, source in EVAL._case_transfer_projection_rows(
                case
            ):
                with self.subTest(case=case["id"], boundary=boundary):
                    compact = EVAL._compact_transfer_projection(
                        boundary, projection, source
                    )
                    self.assertEqual(
                        projection,
                        EVAL._expand_transfer_projection(boundary, compact),
                    )
                    self.assertLess(
                        EVAL.count_o200k_base_tokens(
                            EVAL._canonical_json_text(compact)
                        ),
                        EVAL.count_o200k_base_tokens(
                            EVAL._canonical_json_text(projection)
                        ),
                    )

    def test_route_obligation_pressure_is_named_and_fails_closed(self) -> None:
        obligations = {
            "primary_professional_skill": "quality-test-gate",
            "implementation_layer3": ["regression-testing"],
            "domain": ["bigdata-product-extension"],
            "required_review_skills": ["ai-code-review-refactor"],
        }
        budget = EVAL.FROZEN_GATES["task"]
        components = [
            EVAL._component(
                "route-obligations",
                "decision-eval/route-obligations.json",
                json.dumps(obligations, sort_keys=True),
            ),
            EVAL._component(
                "pressure",
                "decision-eval/token-pressure.txt",
                "overflow-pressure-evidence " * (budget * 2),
            ),
        ]
        result = EVAL.evaluate_route_obligation_context(
            components,
            required_route_obligations=obligations,
            budget_class="task",
            token_budget=budget,
        )
        self.assertEqual("context-token-budget-overflow", result["failure_id"])
        self.assertEqual("fail-closed", result["outcome"])
        self.assertFalse(result["continue_allowed"])
        self.assertTrue(result["route_obligations_preserved"])

        dropped = copy.deepcopy(obligations)
        dropped["implementation_layer3"] = []
        mismatch = EVAL.evaluate_route_obligation_context(
            [
                EVAL._component(
                    "route-obligations",
                    "decision-eval/route-obligations.json",
                    json.dumps(dropped, sort_keys=True),
                )
            ],
            required_route_obligations=obligations,
            budget_class="task",
            token_budget=budget,
        )
        self.assertEqual("context-route-obligation-mismatch", mismatch["failure_id"])
        self.assertEqual("fail-closed", mismatch["outcome"])
        self.assertFalse(mismatch["continue_allowed"])

    def test_evolution_targets_derive_from_the_core_budget_contract(self) -> None:
        main_source = EVAL.CONTEXT_BUDGET_MODEL["budget_classes"]["main"]
        main_limit = EVAL.CONTEXT_BUDGET_LIMITS["main"]
        self.assertEqual(2200, main_source["capacity_ceiling"])
        self.assertEqual(0.10, main_source["minimum_headroom_ratio"])
        self.assertEqual(80, main_source["minimum_release_margin_tokens"])
        self.assertNotIn("release_target", main_source)
        self.assertNotIn("evolution_target", main_source)
        self.assertEqual(220, main_limit["required_reserve_tokens"])
        self.assertEqual(1980, main_limit["release_target"])
        self.assertEqual(80, main_limit["minimum_release_margin_tokens"])
        self.assertEqual(1900, main_limit["evolution_target"])
        self.assertEqual(
            {
                key: value["evolution_target"]
                for key, value in EVAL.CONTEXT_BUDGET_LIMITS.items()
            },
            EVAL.FROZEN_GATES,
        )
        self.assertEqual(
            EVAL.CONTEXT_BUDGET_MODEL["duplicate_rule_token_ratio_max"],
            EVAL.DUPLICATE_TOKEN_RATIO_MAX,
        )

        measurement = EVAL._measure_context(
            [EVAL._component("synthetic", "synthetic.md", "bounded context")],
            budget_class="main",
            token_budget=EVAL.FROZEN_GATES["main"],
        )
        measurement.update({"host": "test", "build_profile": "test"})
        maximum = EVAL._maximum_summary(measurement, include_dispatch=False)
        assert maximum is not None
        self.assertEqual(80, maximum["minimum_release_margin_tokens"])
        self.assertEqual(1900, maximum["evolution_target"])
        self.assertEqual(
            maximum["release_target"] - maximum["tokens"],
            maximum["release_margin_tokens"],
        )
        self.assertEqual(
            maximum["evolution_target"] - maximum["tokens"],
            maximum["evolution_margin_tokens"],
        )

    def test_main_release_margin_contract_fails_closed(self) -> None:
        mutations = []
        missing = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        del missing["budget_classes"]["main"]["minimum_release_margin_tokens"]
        mutations.append(missing)
        wrong_type = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        wrong_type["budget_classes"]["main"]["minimum_release_margin_tokens"] = True
        mutations.append(wrong_type)
        unreachable = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        unreachable["budget_classes"]["main"]["minimum_release_margin_tokens"] = 1980
        mutations.append(unreachable)
        unexpected_non_main = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        unexpected_non_main["budget_classes"]["task"][
            "minimum_release_margin_tokens"
        ] = 1
        mutations.append(unexpected_non_main)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    EVAL.derived_context_budget_limits(mutation)

    def test_all_fixture_dispatches_declare_rendered_context(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        cases = EVAL._fixture_cases(document)
        dispatches = [
            (case["id"], index, step)
            for _group, case in cases
            for index, step in enumerate(case["steps"])
            if step.get("action") == "dispatch"
        ]
        self.assertEqual(16, len(cases))
        self.assertEqual(38, len(dispatches))
        for case_id, index, step in dispatches:
            with self.subTest(case=case_id, step=index):
                self.assertNotIn("dispatch_capsule", step)
                if "utility_capsule" in step:
                    self.assertNotIn("layer3_references", step)
                else:
                    self.assertIsInstance(step.get("layer3_references"), list)
                self.assertEqual([], EVAL._dispatch_metadata_errors(case_id, index, step))

    def test_utility_assignment_requires_current_canonical_baseline_state(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["utility_cases"][0]["steps"][1])
        ledger = original["utility_capsule"]["evidence_ledger"]
        self.assertEqual("workspace baseline captured", ledger[0]["Claim"])
        self.assertEqual("current", ledger[0]["State"])
        self.assertNotIn("Evidence State", ledger[0])
        self.assertIn("# Utility Assignment", validate_and_render_fixture_capsule(original))

        mutations = []
        for state in ("superseded", "invalid"):
            step = copy.deepcopy(original)
            step["utility_capsule"]["evidence_ledger"][0]["State"] = state
            mutations.append((state, step))
        missing = copy.deepcopy(original)
        missing["utility_capsule"]["evidence_ledger"] = []
        mutations.append(("missing", missing))

        for label, step in mutations:
            with self.subTest(state=label):
                with self.assertRaisesRegex(
                    FixtureCapsuleError,
                    "missing current claims.*workspace baseline captured",
                ):
                    step["fixture_capsule"][
                        "canonical_sha256"
                    ] = canonical_capsule_sha256(
                        step,
                        step["fixture_capsule"],
                    )
                    validate_and_render_fixture_capsule(step)

    def test_nested_reference_selection_changes_capsule_hash(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        migration = next(case for case in document["cases"] if case["id"] == "data-migration")
        selected = copy.deepcopy(migration["steps"][6])
        without_nested = copy.deepcopy(selected)
        without_nested["layer3_references"] = []
        selected_text = validate_and_render_fixture_capsule(selected)
        without_hash = canonical_capsule_sha256(
            without_nested, without_nested["fixture_capsule"]
        )
        self.assertIn(
            "transaction-consistency/references/evidence-patterns.md",
            selected_text,
        )
        self.assertNotEqual(
            selected["fixture_capsule"]["canonical_sha256"], without_hash
        )

    def test_layer3_reference_logical_id_path_safety(self) -> None:
        self.assertEqual(
            ("transaction-consistency", "references/evidence-patterns.md"),
            parse_layer3_reference_id(
                "transaction-consistency/references/evidence-patterns.md"
            ),
        )
        invalid = (
            "/transaction-consistency/references/evidence-patterns.md",
            "transaction-consistency\\references\\evidence-patterns.md",
            "../transaction-consistency/references/evidence-patterns.md",
            "transaction-consistency/./evidence-patterns.md",
            "transaction-consistency/references/index.md",
            "transaction-consistency/references/catalog.md",
            "transaction-consistency/references/evidence-patterns.md?raw=1",
            "transaction-consistency/references/evidence-patterns.md#section",
            "transaction-consistency/references/*.md",
            "transaction-consistency/references/nested/evidence-patterns.md",
        )
        for logical_id in invalid:
            with self.subTest(logical_id=logical_id):
                with self.assertRaises(FixtureCapsuleError):
                    parse_layer3_reference_id(logical_id)

    def test_duplicate_blocks_count_only_extra_cross_component_copy(self) -> None:
        repeated = (
            "Never preload Layer 3 guidance or open a generated index before the "
            "capsule names the exact task-relevant item."
        )
        components = [
            EVAL._component("one", "one.md", repeated),
            EVAL._component("two", "two.md", repeated),
            EVAL._component("three", "three.md", "A distinct short statement."),
        ]

        result = EVAL._duplicate_block_metrics(components)

        self.assertEqual(EVAL.count_o200k_base_tokens(repeated.casefold()), result["duplicate_rule_tokens"])
        self.assertEqual(1, len(result["duplicate_blocks"]))
        self.assertEqual(1, result["duplicate_blocks"][0]["extra_copy_count"])
        self.assertEqual(2, result["duplicate_blocks"][0]["occurrence_count"])
        self.assertEqual(2, len(result["duplicate_blocks"][0]["sources"]))

    def test_duplicate_blocks_count_extra_copy_inside_one_component(self) -> None:
        repeated = (
            "Never preload Layer 3 guidance or open a generated index before the "
            "capsule names the exact task-relevant item."
        )
        component = EVAL._component(
            "one",
            "one.md",
            f"{repeated}\n\n{repeated}\n",
        )

        result = EVAL._duplicate_block_metrics([component])

        self.assertEqual(
            EVAL.count_o200k_base_tokens(repeated.casefold()),
            result["duplicate_rule_tokens"],
        )
        self.assertEqual(2, result["duplicate_blocks"][0]["occurrence_count"])
        self.assertEqual(
            [{"component": "one:one.md", "occurrences": 2}],
            result["duplicate_blocks"][0]["sources"],
        )

    def test_transferred_context_categories_are_source_bound_and_exclusive(self) -> None:
        report = EVAL.evaluate()
        transfer = report["transferred_context"]
        expected_categories = {
            "authority",
            "skill_reference",
            "task_capsule",
            "implementation_handoff",
            "evidence_ledger",
            "diff",
            "validation",
            "review_handoff",
            "repair_context",
            "duplicate_context",
            "superseded_evidence",
        }
        self.assertEqual(expected_categories, set(transfer["categories"]))
        exclusive = transfer["accounting"]["exclusive_categories"]
        self.assertEqual(
            transfer["gross_tokens"],
            sum(transfer["categories"][item]["gross_tokens"] for item in exclusive),
        )
        self.assertEqual(
            transfer["gross_tokens"],
            transfer["non_compressible_tokens"] + transfer["compressible_tokens"],
        )
        for category, measurement in transfer["categories"].items():
            with self.subTest(category=category):
                self.assertTrue(measurement["source_selectors"])
                if measurement["accounting_role"] == "exclusive-denominator":
                    self.assertEqual(
                        measurement["gross_tokens"],
                        measurement["non_compressible_tokens"]
                        + measurement["compressible_tokens"],
                    )

    def test_long_tasks_join_lightweight_required_progress_metric(self) -> None:
        report = EVAL.evaluate()
        lightweight = json.loads(EVAL.LIGHTWEIGHT_REPORT.read_text(encoding="utf-8"))
        expected = {
            item["id"]
            for item in lightweight["cases"]
            if item["metrics"]["required_progress_for_multi_agent"]
        }
        rows = report["transferred_context"]["long_task_rows"]

        self.assertEqual(expected, {item["id"] for item in rows})
        self.assertTrue(rows)
        self.assertTrue(
            all(item["required_progress_for_multi_agent"] is True for item in rows)
        )
        self.assertEqual(
            min(item["realized_reduction_ratio"] for item in rows),
            report["transferred_context"]["conservative_long_task_ratio"],
        )

    def test_compacted_transfer_meets_each_realized_reduction_boundary(self) -> None:
        transfer = EVAL.evaluate()["transferred_context"]

        contract = EVAL.TRANSFER_MEASUREMENT_CONTRACT
        category_baselines = contract["category_baseline_gross_tokens"]
        self.assertEqual(1_421, category_baselines["skill_reference"])
        self.assertEqual(contract["baseline_gross_tokens"], transfer["before_gross_tokens"])
        self.assertLessEqual(transfer["after_gross_tokens"], 14441)
        self.assertGreaterEqual(transfer["realized_reduction_ratio"], 0.694706)
        self.assertLessEqual(
            transfer["categories"]["repair_context"]["gross_tokens"],
            154,
        )
        self.assertEqual(
            transfer["before_gross_tokens"] - transfer["after_gross_tokens"],
            transfer["realized_reduction_tokens"],
        )
        for category in ("authority", "skill_reference", "task_capsule"):
            with self.subTest(protected_category=category):
                self.assertEqual(
                    category_baselines[category],
                    transfer["categories"][category]["gross_tokens"],
                )
        self.assertLessEqual(
            transfer["categories"]["duplicate_context"]["gross_tokens"],
            int(category_baselines["duplicate_context"] * 0.75),
        )
        self.assertEqual(0, transfer["categories"]["superseded_evidence"]["gross_tokens"])
        self.assertTrue(transfer["semantic_baseline"]["retained_semantic_equality"])
        self.assertEqual(
            "continue",
            transfer["context_compaction_decision"]["classification"],
        )
        for row in transfer["long_task_rows"]:
            with self.subTest(case=row["id"]):
                self.assertEqual(
                    contract["long_task_baseline_gross_tokens"][row["id"]],
                    row["before_gross_tokens"],
                )
                self.assertGreaterEqual(row["realized_reduction_ratio"], 0.25)

        isolated = next(
            row
            for row in transfer["long_task_rows"]
            if row["id"] == "isolated-write-parallel-contract"
        )
        task_rows = {
            item["task_id"]: item["projection"]
            for item in isolated["boundary_rows"]
            if item["boundary"] == "task_to_implementation"
        }
        first = "task-isolated-write-parallel-contract-1"
        second = "task-isolated-write-parallel-contract-2"
        self.assertEqual(["module-a/service.py"], task_rows[first]["changed_files"])
        self.assertEqual(["module-b/view.tsx"], task_rows[second]["changed_files"])
        self.assertEqual(
            "isolated-module-tests", task_rows[first]["validation_result"]["evidence_id"]
        )
        self.assertEqual(
            "isolated-module-tests", task_rows[second]["validation_result"]["evidence_id"]
        )

        repair_case = next(
            row
            for row in transfer["long_task_rows"]
            if row["id"] == "repair-and-rereview"
        )
        repair = next(
            item["projection"]
            for item in repair_case["boundary_rows"]
            if item["boundary"] == "review_to_repair"
        )
        self.assertEqual(
            ["initial-service-review"],
            [item["claim"] for item in repair["blocking_findings"]],
        )
        self.assertEqual(
            ["current-task"],
            [item["relation"] for item in repair["blocking_findings"]],
        )
        self.assertTrue(
            all(
                set(item) == {"claim", "relation"}
                for item in repair["blocking_findings"]
            )
        )
        self.assertTrue(
            all("outcome" not in item for item in repair["blocking_findings"])
        )
        self.assertEqual(["service.py"], repair["affected_scope"])
        self.assertEqual(
            {"initial-targeted-test", "previous-diff-review"},
            {item["claim"] for item in repair["invalidated_evidence"]},
        )
        self.assertEqual(
            ["owner-placement-inspection"],
            [item["claim"] for item in repair["reusable_evidence"]],
        )

    def test_boundary_projections_reject_lossy_or_expansive_transfer(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item for item in document["cases"] if item["id"] == "repair-and-rereview"
        )
        projections = EVAL._case_transfer_projections(case)

        for boundary, projection in projections.items():
            for field in EVAL.TRANSFER_PROJECTION_FIELDS[boundary]:
                with self.subTest(boundary=boundary, missing=field):
                    mutated = copy.deepcopy(projection)
                    mutated.pop(field)
                    self.assertTrue(EVAL._transfer_projection_errors(boundary, mutated))

        review = copy.deepcopy(projections["implementation_to_review"])
        review["latest_diff"] = {"changed_files": ["service.py"]}
        self.assertTrue(EVAL._transfer_projection_errors("implementation_to_review", review))

        review = copy.deepcopy(projections["implementation_to_review"])
        review["current_evidence"].append({"claim": "old", "state": "superseded"})
        self.assertTrue(EVAL._transfer_projection_errors("implementation_to_review", review))

        execution = copy.deepcopy(projections["task_to_implementation"])
        execution["validation_result"]["stdout"] = "full command log"
        self.assertTrue(EVAL._transfer_projection_errors("task_to_implementation", execution))

        repair = projections["review_to_repair"]
        self.assertTrue(repair["invalidated_evidence"])
        self.assertFalse(
            {
                item["claim"] for item in repair["invalidated_evidence"]
            }
            & {item["claim"] for item in repair["reusable_evidence"]}
        )
        for relation in ("adjacent", "scope-blocker"):
            with self.subTest(repair_relation=relation):
                invalid = copy.deepcopy(repair)
                invalid["blocking_findings"][0]["relation"] = relation
                self.assertTrue(
                    any(
                        "only material current-task findings" in error
                        for error in EVAL._transfer_projection_errors(
                            "review_to_repair", invalid
                        )
                    )
                )

    def test_consecutive_task_dispatches_use_canonical_task_identity(self) -> None:
        def dispatch(task_id: str) -> dict[str, object]:
            return {
                "action": "dispatch",
                "profile": "task-agent",
                "fixture_capsule": {
                    "contract_type": "task",
                    "task_id": task_id,
                    "status": "in_progress",
                    "acceptance": [f"complete {task_id}"],
                    "verification": ["shared-check"],
                    "review_owner": "review-agent",
                },
            }

        case = {
            "id": "consecutive-task-identity",
            "steps": [
                dispatch("task-A"),
                dispatch("task-B"),
                {"action": "edit", "task_id": "task-A", "path": "a.py"},
                {
                    "action": "adaptive-test-evidence",
                    "task_id": "task-A",
                    "evidence_id": "evidence-A",
                    "freshness": 1,
                    "oracle": "A oracle",
                },
                {"action": "edit", "task_id": "task-B", "path": "b.py"},
                {
                    "action": "adaptive-test-evidence",
                    "task_id": "task-B",
                    "evidence_id": "evidence-B",
                    "freshness": 1,
                    "oracle": "B oracle",
                },
                {
                    "action": "validate",
                    "task_ids": ["task-A", "task-B"],
                    "command": "shared-check",
                    "outcome": "passed",
                    "evidence_id": "shared-validation",
                },
            ],
        }

        rows = {
            projection["task_id"]: projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(case)
            if boundary == "task_to_implementation"
        }

        self.assertEqual({"task-A", "task-B"}, set(rows))
        self.assertEqual(["a.py"], rows["task-A"]["changed_files"])
        self.assertEqual(["b.py"], rows["task-B"]["changed_files"])
        self.assertEqual(
            ["evidence-A", "shared-validation"],
            [item["claim"] for item in rows["task-A"]["current_evidence"]],
        )
        self.assertEqual(
            ["evidence-B", "shared-validation"],
            [item["claim"] for item in rows["task-B"]["current_evidence"]],
        )
        self.assertEqual(
            "shared-validation", rows["task-A"]["validation_result"]["evidence_id"]
        )
        self.assertEqual(
            "shared-validation", rows["task-B"]["validation_result"]["evidence_id"]
        )

    def test_repair_projection_uses_complete_current_blocker_window(self) -> None:
        affected = ["a.py", "a_test.py", "b.py"]
        case = {
            "id": "multi-blocker-repair",
            "steps": [
                {
                    "action": "finding",
                    "path": "historical.py",
                    "evidence_id": "historical",
                    "relation": "current-task",
                    "material": True,
                },
                {
                    "action": "review-discipline",
                    "task_id": "original-task",
                    "verdict": "findings",
                    "diff": {
                        "kind": "actual-diff",
                        "artifact": "original.diff",
                        "generation": 1,
                        "changed_files": ["a.py", "b.py"],
                    },
                    "validation": {
                        "evidence_id": "original-validation",
                        "result": "passed",
                        "generation": 1,
                    },
                },
                {
                    "action": "finding",
                    "path": "a.py",
                    "dependent_scope": ["a_test.py"],
                    "evidence_id": "blocker-A",
                    "relation": "current-task",
                    "material": True,
                },
                {
                    "action": "finding",
                    "path": "b.py",
                    "evidence_id": "blocker-B",
                    "relation": "current-task",
                    "material": True,
                },
                {
                    "action": "finding",
                    "path": "noise.py",
                    "evidence_id": "non-material",
                    "relation": "current-task",
                    "material": False,
                },
                {
                    "action": "finding",
                    "path": "resolved.py",
                    "evidence_id": "resolved",
                    "relation": "adjacent",
                    "material": False,
                },
                {
                    "action": "dispatch",
                    "profile": "task-agent",
                    "fixture_capsule": {
                        "contract_type": "task",
                        "task_id": "repair-task",
                        "status": "in_progress",
                        "acceptance": ["resolve current blockers"],
                        "verification": ["repair-check"],
                        "review_owner": "review-agent",
                    },
                },
                {"action": "repair", "task_id": "repair-task", "path": "a.py"},
                {
                    "action": "validate",
                    "task_id": "repair-task",
                    "command": "repair-check",
                    "outcome": "passed",
                    "evidence_id": "repair-validation",
                },
            ],
        }

        repair = next(
            projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(case)
            if boundary == "review_to_repair"
        )

        self.assertEqual(
            ["blocker-A", "blocker-B"],
            [item["claim"] for item in repair["blocking_findings"]],
        )
        self.assertEqual(
            ["current-task", "current-task"],
            [item["relation"] for item in repair["blocking_findings"]],
        )
        self.assertTrue(
            all(
                set(item) == {"claim", "relation"}
                for item in repair["blocking_findings"]
            )
        )
        self.assertTrue(
            all("outcome" not in item for item in repair["blocking_findings"])
        )
        self.assertEqual(affected, repair["affected_scope"])
        self.assertEqual(
            {"original-validation", "previous-diff-review"},
            {item["claim"] for item in repair["invalidated_evidence"]},
        )
        self.assertTrue(
            all(item["scope"] == affected for item in repair["invalidated_evidence"])
        )
        self.assertEqual(
            ["owner-placement-inspection"],
            [item["claim"] for item in repair["reusable_evidence"]],
        )

    def test_adjacent_and_scope_blocker_findings_never_create_repair_projection(
        self,
    ) -> None:
        for relation in ("adjacent", "scope-blocker"):
            with self.subTest(relation=relation):
                case = {
                    "id": f"reject-{relation}-repair-projection",
                    "steps": [
                        {
                            "action": "review-discipline",
                            "task_id": "task-A",
                            "verdict": "findings",
                        },
                        {
                            "action": "finding",
                            "path": "a.py",
                            "evidence_id": f"{relation}-finding",
                            "relation": relation,
                            "material": True,
                        },
                        {
                            "action": "dispatch",
                            "profile": "task-agent",
                            "fixture_capsule": {
                                "contract_type": "task",
                                "task_id": "repair-task",
                            },
                        },
                    ],
                }
                self.assertIsNone(
                    EVAL._current_blocking_review_window(case["steps"], 2)
                )

    def test_missing_long_task_baseline_fails_before_report_write(self) -> None:
        baselines = EVAL.TRANSFER_MEASUREMENT_CONTRACT[
            "long_task_baseline_gross_tokens"
        ]
        selected = next(iter(baselines))
        with (
            mock.patch.dict(
                baselines,
                {selected: baselines[selected]},
                clear=True,
            ),
            mock.patch.object(EVAL, "_write_reports") as write_reports,
        ):
            self.assertEqual(1, EVAL.main([]))
        write_reports.assert_not_called()

    def test_context_compaction_threshold_classification_is_exact(self) -> None:
        self.assertEqual(
            "stop-below-threshold", EVAL._context_compaction_classification(0.249999)
        )
        self.assertEqual("marginal", EVAL._context_compaction_classification(0.25))
        self.assertEqual("marginal", EVAL._context_compaction_classification(0.299999))
        self.assertEqual("continue", EVAL._context_compaction_classification(0.30))

    def test_lightweight_join_requires_current_retained_semantic_equality(self) -> None:
        report = json.loads(EVAL.LIGHTWEIGHT_REPORT.read_text(encoding="utf-8"))
        expected_case_ids = {item["id"] for item in report["cases"]}
        positive = next(
            item for item in report["orchestration_fixtures"] if item["expected_valid"]
        )
        mutations = {}
        missing = copy.deepcopy(report)
        next(
            item
            for item in missing["orchestration_fixtures"]
            if item["id"] == positive["id"]
        ).pop("retained_semantic_equality")
        mutations["missing"] = missing
        unequal = copy.deepcopy(report)
        next(
            item
            for item in unequal["orchestration_fixtures"]
            if item["id"] == positive["id"]
        )["retained_semantic_equality"] = False
        mutations["unequal"] = unequal

        for label, mutation in mutations.items():
            with self.subTest(mutation=label):
                with self.assertRaisesRegex(ValueError, "retained semantic equality"):
                    EVAL._long_task_ids_from_lightweight(mutation, expected_case_ids)

    def test_lightweight_join_rejects_missing_required_progress_metric(self) -> None:
        source = {
            "schema_version": 2,
            "fixture_schema_version": 2,
            "status": "pass",
            "evidence_scope": "deterministic-fixtures",
            "fixture_count": 1,
            "cases": [{"id": "one", "metrics": {}}],
        }
        with self.assertRaisesRegex(ValueError, "required_progress_for_multi_agent"):
            EVAL._long_task_ids_from_lightweight(source, {"one"})

    def test_fixture_capsule_mutations_fail_closed(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["cases"][0]["steps"][1])
        mutations = []

        free_text = copy.deepcopy(original)
        free_text["dispatch_capsule"] = "x"
        mutations.append(free_text)

        placeholder = copy.deepcopy(original)
        placeholder["fixture_capsule"]["goal"] = "x"
        mutations.append(placeholder)

        drift = copy.deepcopy(original)
        drift["fixture_capsule"]["goal"] += "."
        mutations.append(drift)

        missing = copy.deepcopy(original)
        missing["fixture_capsule"].pop("verification")
        mutations.append(missing)

        wrong_version = copy.deepcopy(original)
        wrong_version["fixture_capsule"]["contract_version"] += "x"
        mutations.append(wrong_version)

        for index, step in enumerate(mutations):
            with self.subTest(mutation=index):
                errors = EVAL._dispatch_metadata_errors("mutated", 1, step)
                self.assertTrue(errors)
                self.assertTrue(any("invalid fixture Capsule" in item for item in errors))

    def test_analysis_modes_require_their_exact_templates(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item
            for item in document["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        original = case["steps"][1]

        mismatch = copy.deepcopy(original)
        mismatch["fixture_capsule"]["template"] = "engineering-brief"
        with self.assertRaisesRegex(
            FixtureCapsuleError,
            "requires template 'source-backed-answer'",
        ):
            validate_and_render_fixture_capsule(mismatch)

        unknown = copy.deepcopy(original)
        unknown["mode"] = "unknown-analysis-mode"
        with self.assertRaisesRegex(
            FixtureCapsuleError,
            "unsupported mode 'unknown-analysis-mode'",
        ):
            validate_and_render_fixture_capsule(unknown)

    def test_payment_retry_fixture_rebinds_to_the_exact_split_reference(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item
            for item in document["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        self.assertIn("selected References", case["prompt"])
        self.assertNotIn("indexed checklists", case["prompt"])
        step = case["steps"][1]
        expected = [
            "test-strategy/references/checklist.md",
            "payment-trading-extension/references/duplicate-financial-effect-control.md",
        ]
        self.assertEqual(expected, step["layer3_references"])
        capsule = step["fixture_capsule"]
        self.assertEqual(
            [
                "src/foundation/capabilities/test-strategy/references/checklist.md",
                "src/domain-extensions/payment-trading-extension/references/duplicate-financial-effect-control.md",
            ],
            capsule["scope"],
        )
        self.assertEqual(
            "21a62db2a192bec9c753b38b857260b112290ffab7b3351ed302fefcf01bb08b",
            capsule["canonical_sha256"],
        )
        rendered = validate_and_render_fixture_capsule(step)
        self.assertEqual(236, EVAL.count_o200k_base_tokens(rendered))
        selected = json.dumps(case, sort_keys=True)
        self.assertNotIn("financial-role-and-state-authority", selected)
        self.assertNotIn("provider-venue-event-authentication", selected)
        self.assertEqual(
            "src/domain-extensions/payment-trading-extension/references/duplicate-financial-effect-control.md",
            case["steps"][4]["path"],
        )

    def test_semantic_placeholders_fail_with_synchronized_hash(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["cases"][0]["steps"][1])
        original_text = validate_and_render_fixture_capsule(original)
        mutations = (
            ("goal", 0, "x" * 20),
            ("allowed_write_scope", 0, "xxx"),
            ("expected_output", 0, "x" * 10),
            ("verification", 0, "TBD..."),
            ("stop_conditions", 0, "placeholder_1"),
            ("acceptance", 0, "repeat " * 20),
            ("goal", 0, "ｘ" * 20),
        )

        for field, item, replacement in mutations:
            with self.subTest(field=field, replacement=replacement):
                step = copy.deepcopy(original)
                replacement = " ".join(replacement.split())
                previous = step["fixture_capsule"][field]
                if isinstance(previous, list):
                    previous_text = previous[item]
                    previous[item] = replacement
                else:
                    previous_text = previous
                    step["fixture_capsule"][field] = replacement
                forged_render = original_text.replace(previous_text, replacement, 1)
                self.assertNotEqual(original_text, forged_render)
                step["fixture_capsule"]["canonical_sha256"] = hashlib.sha256(
                    forged_render.encode("utf-8")
                ).hexdigest()

                errors = EVAL._dispatch_metadata_errors("mutated", 1, step)

                self.assertTrue(errors)
                self.assertTrue(
                    any("invalid fixture Capsule" in item for item in errors),
                    errors,
                )

    def test_typed_capsule_fields_accept_short_technical_values(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        task = copy.deepcopy(document["cases"][0]["steps"][1])
        task["mode"] = "go"
        task["primary_skill"] = "todo-service"
        task["fixture_capsule"]["goal"] = "Review AA mapping and BB contract evidence."
        task["fixture_capsule"]["allowed_read_scope"] = [
            "./x",
            "./go",
            "a.py",
            "Makefile",
            "README",
            "module-a/**",
            "src/{api,web}/**/*.ts",
            "c++/x.cc",
        ]
        task["fixture_capsule"]["allowed_write_scope"] = list(
            task["fixture_capsule"]["allowed_read_scope"]
        )
        task["fixture_capsule"]["inputs"] = [
            "HTTP_2",
            "HEAD~1",
            "R",
            "rg",
            "v1",
            "AA",
            "owner.py",
            "Run targeted checks",
        ]
        task["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            task,
            task["fixture_capsule"],
        )
        self.assertTrue(validate_and_render_fixture_capsule(task))

        utility = copy.deepcopy(document["utility_cases"][1]["steps"][1])
        utility["utility_capsule"]["inputs"] = {
            "validation_targets": ["HTTP_2", "a.py", "src/**"],
        }
        utility["utility_capsule"]["commands_allowed"].extend(
            ["pytest", "go test ./...", "rg TODO", "./scripts/check.sh"]
        )
        utility["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            utility,
            utility["fixture_capsule"],
        )
        self.assertTrue(validate_and_render_fixture_capsule(utility))

    def test_utility_semantics_reject_synchronized_schema_forgery(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["utility_cases"][0]["steps"][1])
        original_text = validate_and_render_fixture_capsule(original)
        mutations = []

        mode = copy.deepcopy(original)
        mode["mode"] = "unknown/no-edit"
        mode["utility_capsule"]["mode"] = "unknown/no-edit"
        mutations.append(
            (mode, original_text.replace("diff-export/no-edit", "unknown/no-edit", 1))
        )

        enforcement = copy.deepcopy(original)
        enforcement["utility_capsule"]["no_edit_enforcement"] = "host-enforced"
        mutations.append(
            (
                enforcement,
                original_text.replace(
                    "## No-edit Enforcement\n\nsupported\n\n",
                    "## No-edit Enforcement\n\nhost-enforced\n\n",
                    1,
                ),
            )
        )

        root = copy.deepcopy(original)
        root["utility_capsule"]["allowed_scope"]["workspace_root"] = "whole repository"
        mutations.append(
            (
                root,
                original_text.replace(
                    "Workspace Root: .",
                    "Workspace Root: whole repository",
                    1,
                ),
            )
        )

        inputs = copy.deepcopy(original)
        inputs["utility_capsule"]["inputs"] = {"anything": "some plausible value"}
        old_inputs = (
            '## Inputs\n\n- artifact_delivery: "supplied-content"\n'
            '- base: "HEAD~1"\n- head: "HEAD"\n'
        )
        new_inputs = '## Inputs\n\n- anything: "some plausible value"\n'
        mutations.append((inputs, original_text.replace(old_inputs, new_inputs, 1)))

        change_set = copy.deepcopy(original)
        change_set["utility_capsule"]["workspace_baseline"]["change_set"] = [
            "anything at all"
        ]
        mutations.append(
            (
                change_set,
                original_text.replace(
                    "Change Set:\n- tracked:none\n- staged:none\n- untracked:none",
                    "Change Set:\n- anything at all",
                    1,
                ),
            )
        )

        chained = copy.deepcopy(original)
        previous = chained["utility_capsule"]["commands_allowed"][-1]
        replacement = "git status && rm -rf ."
        chained["utility_capsule"]["commands_allowed"][-1] = replacement
        mutations.append((chained, original_text.replace(previous, replacement, 1)))

        for index, (step, forged_render) in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertNotEqual(original_text, forged_render)
                step["fixture_capsule"]["canonical_sha256"] = hashlib.sha256(
                    forged_render.encode("utf-8")
                ).hexdigest()

                errors = EVAL._dispatch_metadata_errors("mutated-utility", 1, step)

                self.assertTrue(errors)
                self.assertTrue(
                    any("invalid fixture Capsule" in item for item in errors),
                    errors,
                )

    def test_main_measurement_does_not_add_control_prompt_component(self) -> None:
        report = EVAL.evaluate()

        self.assertEqual(16, report["fixture_count"])
        self.assertEqual(report["dispatch_count"] * 9, report["measurement_count"])
        catalog = {item["id"]: item for item in report["component_catalog"]}
        for measurement in report["main_contexts"]:
            kinds = [catalog[item]["kind"] for item in measurement["component_ids"]]
            self.assertEqual(["rendered_main_profile", "control_skill"], kinds)
            self.assertIn("not added", measurement["control_prompt_accounting"])
        for case in report["cases"]:
            for measurement in case["measurements"]:
                capsule = next(
                    catalog[item]
                    for item in measurement["component_ids"]
                    if catalog[item]["kind"] == "dispatch_capsule"
                )
                self.assertEqual(
                    measurement["canonical_capsule_sha256"],
                    capsule["sha256"],
                )
                self.assertEqual(
                    measurement["canonical_capsule_tokens"],
                    capsule["tokens"],
                )
                self.assertGreater(measurement["canonical_capsule_tokens"], 0)

        self.assertEqual(8, report["aggregate"]["loaded_layer3_reference_count"])
        self.assertEqual(
            72,
            report["aggregate"]["measured_layer3_reference_component_count"],
        )
        self.assertEqual(
            [
                "ai-product-extension/references/checklist.md",
                "module-boundary-design/references/benchmarks-and-enforcement.md",
                "payment-trading-extension/references/duplicate-financial-effect-control.md",
                "release-rollback/references/benchmarks-and-patterns.md",
                "release-rollback/references/evidence-patterns.md",
                "test-strategy/references/checklist.md",
                "transaction-consistency/references/evidence-patterns.md",
                "web-security/references/checklist.md",
            ],
            report["aggregate"]["loaded_layer3_reference_logical_ids"],
        )
        migration = next(item for item in report["cases"] if item["id"] == "data-migration")
        measured = [
            item
            for item in migration["measurements"]
            if item["loaded_layer3_reference_count"] == 1
        ]
        self.assertEqual(9, len(measured))
        for item in measured:
            nested = [
                catalog[component_id]
                for component_id in item["component_ids"]
                if catalog[component_id]["kind"] == "layer3_reference"
            ]
            self.assertEqual(1, len(nested))
            self.assertNotIn("/index.md", nested[0]["path"])

        expected_by_case = {
            "source-backed-payment-retry-proof": {
                "payment-trading-extension/references/duplicate-financial-effect-control.md",
                "test-strategy/references/checklist.md",
            },
            "module-boundary-benchmark-review": {
                "module-boundary-design/references/benchmarks-and-enforcement.md",
            },
            "security-ssrf-boundary": {
                "web-security/references/checklist.md",
            },
            "shared-workspace-serial-write": {
                "ai-product-extension/references/checklist.md",
            },
            "release-rollback": {
                "release-rollback/references/benchmarks-and-patterns.md",
                "release-rollback/references/evidence-patterns.md",
            },
        }
        for case_id, expected_ids in expected_by_case.items():
            fixture = next(item for item in report["cases"] if item["id"] == case_id)
            selected = [
                measurement
                for measurement in fixture["measurements"]
                if measurement["loaded_layer3_reference_count"]
            ]
            self.assertEqual(9, len(selected))
            for measurement in selected:
                with self.subTest(case=case_id, host=measurement["host"], profile=measurement["build_profile"]):
                    self.assertEqual(
                        expected_ids,
                        set(measurement["loaded_layer3_reference_logical_ids"]),
                    )

        source_backed = next(
            item
            for item in report["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        for measurement in source_backed["measurements"]:
            mode_references = [
                catalog[component_id]
                for component_id in measurement["component_ids"]
                if catalog[component_id]["kind"] == "mode_reference"
            ]
            self.assertEqual(1, len(mode_references))
            self.assertTrue(
                mode_references[0]["path"].endswith(
                    "/engineering-change-analysis/references/source-backed-answer.md"
                )
            )

        reliability = next(
            item
            for item in report["cases"]
            if item["id"] == "cache-stampede-reliability"
        )
        evidence_measurements = [
            measurement
            for measurement in reliability["measurements"]
            if measurement["professional_references"]
            == ["references/evidence-patterns.md"]
        ]
        self.assertEqual(9, len(evidence_measurements))
        for measurement in evidence_measurements:
            targeted = [
                catalog[component_id]
                for component_id in measurement["component_ids"]
                if catalog[component_id]["kind"] == "targeted_reference"
            ]
            self.assertEqual(1, len(targeted))
            self.assertTrue(
                targeted[0]["path"].endswith(
                    "/reliability-observability-gate/references/evidence-patterns.md"
                )
            )

    def test_authoritative_dag_direct_task_nodes_use_analyzed_task_budget(
        self,
    ) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        fixture_cases = {
            str(case["id"]): case
            for key in ("cases", "scheduling_cases")
            for case in document[key]
        }
        expected_measurement_coordinates = {
            (host, build_profile)
            for host in EVAL.HOST_PROFILE_ROOTS
            for build_profile in EVAL.BUILD_PROFILES
        }

        for (case_id, step_index), (
            template,
            dependency,
        ) in AUTHORITATIVE_DAG_NODES.items():
            with self.subTest(case=case_id, step=step_index, contract="fixture"):
                case = fixture_cases[case_id]
                step = case["steps"][step_index]
                capsule = step["fixture_capsule"]
                self.assertEqual("direct", case["kind"])
                self.assertEqual("task-agent", step["profile"])
                self.assertNotIn("utility_capsule", step)
                self.assertEqual("task", capsule["contract_type"])
                self.assertEqual(template, capsule["template"])
                self.assertEqual(AUTHORITATIVE_DAG_INPUTS, capsule["inputs"])
                self.assertEqual([dependency], capsule["dependencies"])
                self.assertIn(
                    AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[case_id],
                    [
                        item.get("evidence")
                        for item in case["steps"]
                        if isinstance(item, dict)
                        and item.get("action") == "progress"
                    ],
                )
                self.assertFalse(
                    any(
                        isinstance(item, dict)
                        and item.get("action") == "dispatch"
                        and item.get("profile") == "analysis-agent"
                        for item in case["steps"]
                    )
                )

        report = EVAL.evaluate()
        measurements_by_case = {
            str(case["id"]): case["measurements"]
            for case in report["cases"]
        }
        selected = [
            measurement
            for case_id, step_index in AUTHORITATIVE_DAG_NODES
            for measurement in measurements_by_case[case_id]
            if measurement["step"] == step_index
        ]
        self.assertEqual(5 * 9, len(selected))
        for case_id, step_index in AUTHORITATIVE_DAG_NODES:
            node_measurements = [
                measurement
                for measurement in measurements_by_case[case_id]
                if measurement["step"] == step_index
            ]
            self.assertEqual(9, len(node_measurements))
            self.assertEqual(
                expected_measurement_coordinates,
                {
                    (
                        measurement["host"],
                        measurement["build_profile"],
                    )
                    for measurement in node_measurements
                },
            )
            for measurement in node_measurements:
                with self.subTest(
                    case=case_id,
                    step=step_index,
                    host=measurement["host"],
                    build_profile=measurement["build_profile"],
                ):
                    self.assertEqual(
                        "analyzed_task",
                        measurement["budget_class"],
                    )

    def test_authoritative_dag_analyzed_task_budget_predicate_is_closed(
        self,
    ) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        release_cases = {
            str(case["id"]): case for case in document["cases"]
        }
        positive_case = release_cases["isolated-write-parallel-contract"]
        base_step = copy.deepcopy(positive_case["steps"][2])
        analysis_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                if case["kind"] == "analyzed"
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "analysis-agent"
            )
        )
        analyzed_task_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                if case["kind"] == "analyzed"
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
            )
        )
        utility_step = copy.deepcopy(
            next(
                step
                for case in document["utility_cases"]
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
            )
        )
        direct_task_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
                and step.get("fixture_capsule", {}).get("template")
                == "direct-task"
            )
        )
        repair_task_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
                and step.get("fixture_capsule", {}).get("template")
                == "repair-task"
            )
        )

        progress = {
            "actor": "main-control-agent",
            "action": "progress",
            "checkpoint_type": "start/path",
            "evidence": AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "isolated-write-parallel-contract"
            ],
            "evidence_anchor": "fixture:budget-classification:path",
        }
        alternate_progress = {
            "actor": "main-control-agent",
            "action": "progress",
            "checkpoint_type": "start/path",
            "evidence": AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "shared-workspace-serial-write"
            ],
            "evidence_anchor": (
                "fixture:budget-classification:alternate-path"
            ),
        }

        def authoritative_fields(step: dict[str, object]) -> None:
            capsule = step["fixture_capsule"]
            assert isinstance(capsule, dict)
            capsule["contract_type"] = "task"
            capsule["inputs"] = list(AUTHORITATIVE_DAG_INPUTS)
            capsule["dependencies"] = [
                AUTHORITATIVE_DAG_NODES[
                    ("isolated-write-parallel-contract", 2)
                ][1]
            ]

        authoritative_fields(direct_task_step)
        authoritative_fields(repair_task_step)

        cases: list[tuple[str, dict[str, object], str]] = []

        def add_case(
            label: str,
            step: dict[str, object],
            *,
            expected: str = "task",
            kind: str = "direct",
            evidence: dict[str, object] | None = progress,
            preceding_dispatch: dict[str, object] | None = None,
            prefix_steps: list[dict[str, object]] | None = None,
        ) -> None:
            steps = copy.deepcopy(prefix_steps or [])
            if evidence is not None:
                steps.append(copy.deepcopy(evidence))
            if preceding_dispatch is not None:
                steps.append(copy.deepcopy(preceding_dispatch))
            steps.append(step)
            cases.append(
                (
                    label,
                    {
                        "id": f"budget-classification-{label}",
                        "kind": kind,
                        "steps": steps,
                    },
                    expected,
                )
            )

        add_case("direct-task-template", direct_task_step)
        add_case("repair-task-template", repair_task_step)

        def mutated_base() -> dict[str, object]:
            return copy.deepcopy(base_step)

        missing_inputs = mutated_base()
        missing_inputs["fixture_capsule"].pop("inputs")
        add_case("missing-inputs", missing_inputs)

        missing_input_item = mutated_base()
        missing_input_item["fixture_capsule"]["inputs"] = [
            AUTHORITATIVE_DAG_INPUTS[0]
        ]
        add_case("missing-input-item", missing_input_item)

        near_input = mutated_base()
        near_input["fixture_capsule"]["inputs"][0] += "."
        add_case("near-match-input", near_input)

        reversed_inputs = mutated_base()
        reversed_inputs["fixture_capsule"]["inputs"].reverse()
        add_case("reordered-inputs", reversed_inputs)

        extra_input = mutated_base()
        extra_input["fixture_capsule"]["inputs"].append(
            "Additional non-authoritative context."
        )
        add_case("extra-input", extra_input)

        missing_dependencies = mutated_base()
        missing_dependencies["fixture_capsule"].pop("dependencies")
        add_case("missing-dependencies", missing_dependencies)

        empty_dependencies = mutated_base()
        empty_dependencies["fixture_capsule"]["dependencies"] = []
        add_case("empty-dependencies", empty_dependencies)

        near_dependency = mutated_base()
        near_dependency["fixture_capsule"]["dependencies"][0] += "."
        add_case("near-match-dependency", near_dependency)

        multiple_dependencies = mutated_base()
        multiple_dependencies["fixture_capsule"]["dependencies"].append(
            "Another predecessor."
        )
        add_case("multiple-dependencies", multiple_dependencies)

        wrong_template_dependency = mutated_base()
        wrong_template_dependency["fixture_capsule"]["dependencies"] = [
            AUTHORITATIVE_DAG_NODES[
                ("isolated-write-parallel-contract", 20)
            ][1]
        ]
        add_case("wrong-template-dependency", wrong_template_dependency)

        missing_template = mutated_base()
        missing_template["fixture_capsule"].pop("template")
        add_case("missing-template", missing_template)

        near_template = mutated_base()
        near_template["fixture_capsule"]["template"] = "implementation-task-v2"
        add_case("near-match-template", near_template)

        missing_task_contract = mutated_base()
        missing_task_contract["fixture_capsule"].pop("contract_type")
        add_case("missing-task-contract", missing_task_contract)

        near_task_contract = mutated_base()
        near_task_contract["fixture_capsule"]["contract_type"] = "tasks"
        add_case("near-match-task-contract", near_task_contract)

        add_case("missing-evidence", mutated_base(), evidence=None)

        prepended_evidence = copy.deepcopy(progress)
        prepended_evidence["evidence"] = (
            "X"
            + AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "isolated-write-parallel-contract"
            ]
        )
        add_case(
            "near-match-evidence-prepend",
            mutated_base(),
            evidence=prepended_evidence,
        )

        appended_evidence = copy.deepcopy(progress)
        appended_evidence["evidence"] = (
            AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "isolated-write-parallel-contract"
            ]
            + "X"
        )
        add_case(
            "near-match-evidence-append",
            mutated_base(),
            evidence=appended_evidence,
        )

        add_case(
            "near-match-case-kind",
            mutated_base(),
            kind="direct-task",
        )
        add_case(
            "analysis-dispatch-present",
            mutated_base(),
            preceding_dispatch=analysis_step,
        )

        synthetic_dependencies = (
            (
                "synthetic-authority-node",
                "implementation-task",
                AUTHORITATIVE_DAG_NODES[
                    ("isolated-write-parallel-contract", 2)
                ][1],
                progress,
                3,
            ),
            (
                "synthetic-authority-predecessor",
                "implementation-task",
                AUTHORITATIVE_DAG_NODES[
                    ("shared-workspace-serial-write", 12)
                ][1],
                alternate_progress,
                5,
            ),
            (
                "synthetic-authority-integration",
                "integration-task",
                AUTHORITATIVE_DAG_NODES[
                    ("isolated-write-parallel-contract", 20)
                ][1],
                progress,
                8,
            ),
        )
        real_case_ids = {
            str(case["id"])
            for key in ("cases", "scheduling_cases", "utility_cases")
            for case in document[key]
        }
        synthetic_target_steps: dict[str, int] = {}
        for (
            label,
            template,
            dependency,
            evidence,
            filler_count,
        ) in synthetic_dependencies:
            synthetic_step = mutated_base()
            synthetic_step["fixture_capsule"]["template"] = template
            synthetic_step["fixture_capsule"]["dependencies"] = [dependency]
            if template == "integration-task":
                synthetic_step["mode"] = "integration"
            if label == "synthetic-authority-node":
                synthetic_step["primary_skill"] = "backend-change-builder"
                synthetic_step["professional_references"] = [
                    "references/checklist.md"
                ]
                synthetic_step["layer3_skills"] = []
                synthetic_step["layer3_references"] = []
                self.assertEqual(
                    "backend-change-builder",
                    synthetic_step["primary_skill"],
                )
                self.assertEqual(
                    ["references/checklist.md"],
                    synthetic_step["professional_references"],
                )
                self.assertEqual([], synthetic_step["layer3_skills"])
                self.assertEqual([], synthetic_step["layer3_references"])
                self.assertEqual("task-agent", synthetic_step["profile"])
                self.assertNotIn("utility_capsule", synthetic_step)
                self.assertEqual(
                    "task",
                    synthetic_step["fixture_capsule"]["contract_type"],
                )
                self.assertEqual(
                    AUTHORITATIVE_DAG_INPUTS,
                    synthetic_step["fixture_capsule"]["inputs"],
                )
                self.assertEqual(
                    "implementation-task",
                    synthetic_step["fixture_capsule"]["template"],
                )
                self.assertEqual(
                    [dependency],
                    synthetic_step["fixture_capsule"]["dependencies"],
                )
                self.assertEqual(
                    AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                        "isolated-write-parallel-contract"
                    ],
                    evidence["evidence"],
                )
            prefix_steps = [
                {
                    "actor": "task-agent",
                    "action": "read",
                    "path": f"synthetic/input-{index}.txt",
                }
                for index in range(filler_count)
            ]
            add_case(
                label,
                synthetic_step,
                expected="analyzed_task",
                evidence=evidence,
                prefix_steps=prefix_steps,
            )
            synthetic_case_id = f"budget-classification-{label}"
            self.assertNotIn(synthetic_case_id, real_case_ids)
            synthetic_target_steps[synthetic_case_id] = filler_count + 1
        self.assertEqual(
            {
                "budget-classification-synthetic-authority-node": 4,
                "budget-classification-synthetic-authority-predecessor": 6,
                "budget-classification-synthetic-authority-integration": 9,
            },
            synthetic_target_steps,
        )

        add_case(
            "analyzed-case-unchanged",
            analyzed_task_step,
            expected="analyzed_task",
            kind="analyzed",
            evidence=None,
        )
        add_case(
            "utility-unchanged",
            utility_step,
            expected="utility",
            kind="utility",
            evidence=None,
        )

        fixture_cases = [
            ("utility" if expected == "utility" else "release", case)
            for _label, case, expected in cases
        ]
        with (
            mock.patch.object(
                EVAL,
                "_fixture_cases",
                return_value=fixture_cases,
            ),
            mock.patch.object(
                EVAL,
                "_dispatch_metadata_errors",
                return_value=[],
            ),
            mock.patch.object(
                EVAL,
                "trace_execution_level_migration_errors",
                return_value=[],
            ),
            mock.patch.object(
                EVAL,
                "_layer3_reference_registry_errors",
                return_value=[],
            ),
            mock.patch.object(
                EVAL,
                "validate_and_render_fixture_capsule",
                return_value="# Classification capsule",
            ),
            mock.patch.object(
                EVAL,
                "_load_lightweight_prerequisite",
                return_value=(
                    {str(cases[0][1]["id"])},
                    {"retained_semantic_equality": True},
                ),
            ),
            mock.patch.object(
                EVAL,
                "_registered_long_task_baselines",
                return_value={str(cases[0][1]["id"]): 100_000},
            ),
        ):
            report = EVAL.evaluate()

        results = {
            str(case["id"]): case["measurements"]
            for case in report["cases"]
        }
        expected_coordinates = {
            (host, build_profile)
            for host in EVAL.HOST_PROFILE_ROOTS
            for build_profile in EVAL.BUILD_PROFILES
        }
        for label, case, expected in cases:
            case_id = str(case["id"])
            target_step = len(case["steps"]) - 1
            measurements = [
                measurement
                for measurement in results[case_id]
                if measurement["step"] == target_step
            ]
            with self.subTest(case=label, contract="measurement-count"):
                self.assertEqual(9, len(measurements))
                self.assertEqual(
                    expected_coordinates,
                    {
                        (
                            measurement["host"],
                            measurement["build_profile"],
                        )
                        for measurement in measurements
                    },
                )
            for measurement in measurements:
                with self.subTest(
                    case=label,
                    host=measurement["host"],
                    build_profile=measurement["build_profile"],
                ):
                    self.assertEqual(expected, measurement["budget_class"])

    def test_layer3_resolution_follows_each_build_manifest(self) -> None:
        errors: list[str] = []
        manifests = EVAL._load_manifests(errors)
        self.assertEqual([], errors)

        def selector_reference_id(
            profile: str,
            primary: str,
            owner: str,
            decision_problem: str,
        ) -> str:
            selector = json.loads(
                (
                    EVAL.DIST_SKILLS
                    / profile
                    / "engineering-control-plane/references/selectors"
                    / f"{primary}.json"
                ).read_text(encoding="utf-8")
            )
            records = {
                json.dumps(record, sort_keys=True, separators=(",", ":"))
                for surface in selector["selection_surfaces"]
                for record in surface["reference_records"]
                if record.get("owner_skill") == owner
                and (record.get("context_admissibility") or {}).get(
                    "decision_problem"
                )
                == decision_problem
            }
            self.assertEqual(1, len(records))
            record = json.loads(records.pop())
            return f"{owner}/{record['path']}"

        self.assertTrue(
            all(
                manifest["compiled_layer3_format"] == EVAL.COMPILED_LAYER3_FORMAT
                for manifest in manifests.values()
            )
        )
        recommended = EVAL._layer3_path(
            "recommended",
            "engineering-change-analysis",
            "failure-diagnosis",
            manifests["recommended"],
        )
        dev = EVAL._layer3_path(
            "dev",
            "engineering-change-analysis",
            "failure-diagnosis",
            manifests["dev"],
        )
        self.assertIn("references/layer3", recommended.as_posix())
        self.assertEqual("SKILL.md", dev.name)
        self.assertEqual("failure-diagnosis", dev.parent.name)

        payment_references = {
            profile: selector_reference_id(
                profile,
                "engineering-change-analysis",
                "payment-trading-extension",
                "financial-role-and-state-authority",
            ).split("/", 1)[1]
            for profile in EVAL.BUILD_PROFILES
        }

        rows = (
            ("recommended", "engineering-change-analysis", "test-strategy", "references/checklist.md", "compiled"),
            ("full", "engineering-change-analysis", "test-strategy", "references/checklist.md", "compiled"),
            ("dev", "engineering-change-analysis", "test-strategy", "references/checklist.md", "top-level"),
            ("recommended", "engineering-change-analysis", "payment-trading-extension", payment_references["recommended"], "compiled"),
            ("full", "engineering-change-analysis", "payment-trading-extension", payment_references["full"], "top-level"),
            ("dev", "engineering-change-analysis", "payment-trading-extension", payment_references["dev"], "top-level"),
            ("recommended", "high-risk-design-review", "module-boundary-design", "references/benchmarks-and-enforcement.md", "compiled"),
            ("full", "high-risk-design-review", "module-boundary-design", "references/benchmarks-and-enforcement.md", "compiled"),
            ("dev", "high-risk-design-review", "module-boundary-design", "references/benchmarks-and-enforcement.md", "top-level"),
            ("recommended", "security-privacy-gate", "web-security", "references/checklist.md", "compiled"),
            ("full", "security-privacy-gate", "web-security", "references/checklist.md", "compiled"),
            ("dev", "security-privacy-gate", "web-security", "references/checklist.md", "top-level"),
            ("recommended", "security-privacy-gate", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "security-privacy-gate", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "security-privacy-gate", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "backend-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "backend-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "backend-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "frontend-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "frontend-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "frontend-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "data-middleware-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "data-middleware-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "data-middleware-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "integration-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "integration-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "integration-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "installed-client-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "installed-client-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "installed-client-change-builder", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "ai-code-review-refactor", "ai-product-extension", "references/checklist.md", "compiled"),
            ("full", "ai-code-review-refactor", "ai-product-extension", "references/checklist.md", "top-level"),
            ("dev", "ai-code-review-refactor", "ai-product-extension", "references/checklist.md", "top-level"),
            ("recommended", "delivery-release-gate", "release-rollback", "references/benchmarks-and-patterns.md", "compiled"),
            ("full", "delivery-release-gate", "release-rollback", "references/benchmarks-and-patterns.md", "compiled"),
            ("dev", "delivery-release-gate", "release-rollback", "references/benchmarks-and-patterns.md", "top-level"),
            ("recommended", "delivery-release-gate", "release-rollback", "references/evidence-patterns.md", "compiled"),
            ("full", "delivery-release-gate", "release-rollback", "references/evidence-patterns.md", "compiled"),
            ("dev", "delivery-release-gate", "release-rollback", "references/evidence-patterns.md", "top-level"),
        )
        for profile, primary, owner, relative, delivery in rows:
            with self.subTest(profile=profile, owner=owner):
                logical_id = f"{owner}/{relative}"
                resolved = EVAL._layer3_reference_path(
                    profile,
                    primary,
                    logical_id,
                    manifests[profile],
                )
                compiled_path = (
                    EVAL.DIST_SKILLS
                    / profile
                    / primary
                    / "references"
                    / "layer3"
                    / owner
                    / relative
                )
                top_level_path = EVAL.DIST_SKILLS / profile / owner / relative
                expected = compiled_path if delivery == "compiled" else top_level_path
                alternate = top_level_path if delivery == "compiled" else compiled_path
                self.assertEqual(expected, resolved)
                self.assertTrue(resolved.is_file())
                self.assertFalse(alternate.exists())

        foundation_id = "transaction-consistency/references/evidence-patterns.md"
        recommended_nested = EVAL._layer3_reference_path(
            "recommended",
            "data-middleware-change-builder",
            foundation_id,
            manifests["recommended"],
        )
        full_nested = EVAL._layer3_reference_path(
            "full",
            "data-middleware-change-builder",
            foundation_id,
            manifests["full"],
        )
        dev_nested = EVAL._layer3_reference_path(
            "dev",
            "data-middleware-change-builder",
            foundation_id,
            manifests["dev"],
        )
        self.assertIn("references/layer3/transaction-consistency", recommended_nested.as_posix())
        self.assertIn("references/layer3/transaction-consistency", full_nested.as_posix())
        self.assertEqual(
            "dev/transaction-consistency/references/evidence-patterns.md",
            "/".join(dev_nested.parts[-4:]),
        )

        domain_ids = {
            profile: selector_reference_id(
                profile,
                "data-middleware-change-builder",
                "bigdata-product-extension",
                "consumer-and-schema-contracts",
            )
            for profile in EVAL.BUILD_PROFILES
        }
        recommended_domain = EVAL._layer3_reference_path(
            "recommended",
            "data-middleware-change-builder",
            domain_ids["recommended"],
            manifests["recommended"],
        )
        full_domain = EVAL._layer3_reference_path(
            "full",
            "data-middleware-change-builder",
            domain_ids["full"],
            manifests["full"],
        )
        dev_domain = EVAL._layer3_reference_path(
            "dev",
            "data-middleware-change-builder",
            domain_ids["dev"],
            manifests["dev"],
        )
        self.assertIn("references/layer3/bigdata-product-extension", recommended_domain.as_posix())
        self.assertNotIn("references/layer3", full_domain.as_posix())
        self.assertNotIn("references/layer3", dev_domain.as_posix())
        self.assertTrue(recommended_domain.is_file())
        self.assertTrue(full_domain.is_file())
        self.assertTrue(dev_domain.is_file())

    def test_task_context_loads_two_foundation_references_without_an_index(self) -> None:
        report = EVAL.evaluate()
        catalog = {item["id"]: item for item in report["component_catalog"]}
        foundation = EVAL.load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )
        foundation_names = {
            row["name"] for row in foundation["foundation_skills"]
        }
        case = next(
            item for item in report["cases"] if item["id"] == "release-rollback"
        )
        measurements = [
            item
            for item in case["measurements"]
            if item["role"] == "task-agent"
            and item["loaded_layer3_reference_count"] == 2
        ]
        self.assertEqual(9, len(measurements))
        for measurement in measurements:
            with self.subTest(
                host=measurement["host"],
                build_profile=measurement["build_profile"],
            ):
                logical_ids = measurement["loaded_layer3_reference_logical_ids"]
                self.assertEqual(2, len(logical_ids))
                self.assertTrue(
                    all(
                        parse_layer3_reference_id(logical_id)[0]
                        in foundation_names
                        for logical_id in logical_ids
                    )
                )
                nested = [
                    catalog[component_id]
                    for component_id in measurement["component_ids"]
                    if catalog[component_id]["kind"] == "layer3_reference"
                ]
                self.assertEqual(2, len(nested))
                self.assertEqual(2, len({item["path"] for item in nested}))
                self.assertTrue(
                    all(
                        not item["path"].endswith(("/index.md", "/catalog.md"))
                        for item in nested
                    )
                )

    def test_full_domain_root_and_checklist_match_recommended_compiled_delivery(self) -> None:
        report = EVAL.evaluate()
        catalog = {item["id"]: item for item in report["component_catalog"]}
        case = next(
            item
            for item in report["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        measurements = [
            item
            for item in case["measurements"]
            if item["build_profile"] in {"recommended", "full"}
        ]
        self.assertEqual(6, len(measurements))
        for measurement in measurements:
            with self.subTest(
                host=measurement["host"],
                build_profile=measurement["build_profile"],
            ):
                selected = [
                    catalog[component_id]
                    for component_id in measurement["component_ids"]
                ]
                domain_roots = [
                    item
                    for item in selected
                    if item["kind"] == "layer3"
                    and "payment-trading-extension" in item["path"]
                ]
                domain_checklists = [
                    item
                    for item in selected
                    if item["kind"] == "layer3_reference"
                    and item["path"].endswith(
                        "/payment-trading-extension/references/duplicate-financial-effect-control.md"
                    )
                ]
                self.assertEqual(1, len(domain_roots))
                self.assertEqual(1, len(domain_checklists))
                self.assertFalse(
                    any(item["path"].endswith("/index.md") for item in selected)
                )
                if measurement["build_profile"] == "full":
                    self.assertTrue(
                        domain_roots[0]["path"].endswith(
                            "/full/payment-trading-extension/SKILL.md"
                        )
                    )
                    self.assertNotIn(
                        "/references/layer3/", domain_checklists[0]["path"]
                    )
                else:
                    self.assertIn("/references/layer3/", domain_roots[0]["path"])
                    self.assertIn(
                        "/references/layer3/", domain_checklists[0]["path"]
                    )
                self.assertTrue(measurement["within_duplicate_budget"])

    def test_context_manifest_loader_requires_ai_consumption_format(self) -> None:
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
                        errors: list[str] = []
                        manifests = EVAL._load_manifests(errors)
                    self.assertEqual({}, manifests)
                    self.assertTrue(
                        any("compiled_layer3_format must equal" in error for error in errors),
                        errors,
                    )

    def test_layer3_skill_resolution_requires_exactly_one_delivery_path(self) -> None:
        base = {
            "compiled_layer3_references": {"primary": []},
            "top_level_skills": [],
        }
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_path("test", "primary", "owner", copy.deepcopy(base))

        dual = copy.deepcopy(base)
        dual["compiled_layer3_references"]["primary"] = ["owner"]
        dual["top_level_skills"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_path("test", "primary", "owner", dual)

    def test_layer3_reference_resolution_requires_exactly_one_delivery_path(self) -> None:
        logical_id = "owner/references/checklist.md"
        base = {
            "compiled_layer3_references": {"primary": []},
            "top_level_skills": [],
        }
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_path(
                "test",
                "primary",
                logical_id,
                copy.deepcopy(base),
            )

        dual = copy.deepcopy(base)
        dual["compiled_layer3_references"]["primary"] = ["owner"]
        dual["top_level_skills"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_path("test", "primary", logical_id, dual)

    def test_fixture_capsule_renderer_is_not_built(self) -> None:
        self.assertEqual(
            [],
            list((ROOT / "dist").rglob("fixture_capsule_contract.py")),
        )

    def test_admissible_composition_inventory_is_source_derived(self) -> None:
        composition = self._admissible_report()
        authority = EVAL._selector_authority()
        projections = EVAL.layer3_selector_control_projections(authority)

        self.assertEqual(
            "changeforge.admissible-context-composition-eval/v1",
            composition["contract"],
        )
        self.assertFalse(composition["parallel_catalog"])
        self.assertEqual(
            authority["inventory"],
            composition["selector_authority_inventory"],
        )
        self.assertEqual(len(projections), composition["inventory"]["professional_count"])
        self.assertEqual(
            sum(len(item["selection_surfaces"]) for item in projections.values()),
            composition["inventory"]["owner_surface_count"],
        )
        self.assertGreater(
            composition["inventory"]["legal_selection_equivalence_class_count"],
            composition["inventory"]["owner_surface_count"],
        )
        self.assertGreater(composition["inventory"]["positive_selector_case_count"], 0)
        self.assertEqual(
            composition["inventory"]["positive_selector_case_count"],
            composition["inventory"]["nearest_negative_case_count"],
        )
        self.assertGreater(composition["inventory"]["professional_reference_count"], 0)
        self.assertGreater(
            composition["inventory"]["professional_reference_conflict_count"],
            0,
        )
        self.assertGreater(composition["inventory"]["nested_reference_count"], 0)
        self.assertGreater(
            composition["inventory"]["legal_nested_reference_combination_count"],
            composition["inventory"]["nested_reference_count"],
        )
        self.assertGreater(composition["inventory"]["dominated_reference_subset_count"], 0)
        self.assertEqual(
            composition["inventory"]["candidate_composition_count"],
            composition["inventory"]["coverage_mapping_count"],
        )
        self.assertLess(
            composition["inventory"]["canonical_representative_count"],
            composition["inventory"]["coverage_mapping_count"],
        )
        self.assertLessEqual(
            composition["inventory"]["exact_measurement_count"],
            composition["inventory"]["canonical_representative_count"],
        )
        self.assertEqual(
            {
                "src/registry/professional-skills.yaml",
                "src/registry/foundation-skills.yaml",
                "src/registry/domain-skills.yaml",
            },
            set(composition["source_scope"]["registries"]),
        )

    def test_admissible_compositions_cover_required_owner_and_layer_shapes(self) -> None:
        composition = self._admissible_report()

        self.assertEqual(
            {
                "analysis_foundation_domain",
                "analyzed_task_three_layer3",
                "review_domain_foundation",
                "nested_targeted_references",
                "direct_main_owner",
                "initial_analysis_main_owner",
                "analyzed_brief_owner",
                "direct_false_worst_excluded",
            },
            {
                key
                for key, covered in composition["required_coverage"].items()
                if covered
            },
        )
        self.assertEqual(
            {"0", "1", "2", "3"},
            {
                cardinality
                for cardinality, count in composition["inventory"][
                    "layer3_cardinality_counts"
                ].items()
                if count
            },
        )
        obligations = composition["obligation_preservation"]
        self.assertTrue(obligations["professional_preserved"])
        self.assertTrue(obligations["domain_authorization_preserved"])
        self.assertTrue(obligations["review_selection_independent"])
        self.assertTrue(obligations["receipts_replayed"])
        self.assertTrue(obligations["route_once_input_only"])
        self.assertTrue(obligations["staged_reference_obligations_preserved"])
        self.assertEqual(0, obligations["routing_classification_calls"])
        inventory = composition["inventory"]
        self.assertGreater(inventory["stage_measurement_count"], 0)
        self.assertGreater(inventory["valid_carried_predecessor_count"], 0)
        self.assertEqual(0, inventory["carrier_failure_count"])
        self.assertEqual(0, inventory["dropped_reference_obligation_count"])
        self.assertEqual(0, inventory["required_output_receipt_failure_count"])
        self.assertGreater(inventory["required_output_receipt_count"], 0)
        self.assertGreaterEqual(inventory["maximum_selected_reference_count"], 4)

    def test_admissible_compositions_fail_closed_without_truncation(self) -> None:
        forbidden = self._admissible_report()["forbidden_combinations"]

        self.assertEqual(3, forbidden["maximum_layer3"])
        self.assertGreater(forbidden["over_max_rejection_count"], 0)
        self.assertGreater(forbidden["unauthorized_exact_rejection_count"], 0)
        self.assertGreater(forbidden["duplicate_exact_rejection_count"], 0)
        self.assertEqual(0, forbidden["silent_truncation_count"])
        self.assertEqual(0, forbidden["nearest_negative_leak_count"])
        self.assertEqual(0, forbidden["reference_conflict_leak_count"])
        self.assertEqual(0, forbidden["index_or_catalog_load_count"])
        inventory = self._admissible_report()["inventory"]
        self.assertEqual(1, inventory["maximum_loaded_reference_count"])
        self.assertEqual(0, inventory["four_plus_reference_measurement_count"])
        self.assertGreaterEqual(inventory["maximum_selected_reference_count"], 4)
        self.assertGreater(inventory["path_excluded_composition_count"], 0)
        self.assertEqual(
            "admissible-context-layer3-overflow",
            forbidden["overflow_failure_id"],
        )

    def test_admissible_composition_worst_cases_report_current_frontier(self) -> None:
        composition = self._admissible_report()
        targets = {
            "analysis": 4500,
            "task": 3000,
            "analyzed_task": 6000,
            "review": 3700,
        }

        for budget_class, target in targets.items():
            with self.subTest(budget_class=budget_class):
                maximum = composition["max_by_budget_class"][budget_class]
                self.assertEqual(
                    maximum["tokens"] <= target,
                    maximum["within_hard_evolution_target"],
                )
                matching_errors = [
                    error
                    for error in composition["errors"]
                    if f" {budget_class} maximum " in error
                ]
                self.assertEqual(maximum["tokens"] > target, bool(matching_errors))
                self.assertTrue(maximum["route_obligations_preserved"])
                self.assertLessEqual(
                    len(maximum["stage_loaded_references"]), 1
                )
                self.assertFalse(
                    any(
                        path.endswith(("/index.md", "/catalog.md"))
                        for path in maximum["loaded_paths"]
                    )
                )

    def test_global_dominance_frontier_is_complete_and_source_derived(self) -> None:
        composition = self._admissible_report()
        frontier = composition["dominance_frontier"]

        self.assertEqual(
            {
                "analysis": {
                    "candidate_count": 112_828,
                    "exact_render_signature_count": 46_158,
                    "over_target_candidate_count": 0,
                },
                "task": {
                    "candidate_count": 19_281,
                    "exact_render_signature_count": 19_281,
                    "over_target_candidate_count": 722,
                },
                "analyzed_task": {
                    "candidate_count": 66_150,
                    "exact_render_signature_count": 66_150,
                    "over_target_candidate_count": 0,
                },
                "review": {
                    "candidate_count": 37_819,
                    "exact_render_signature_count": 16_546,
                    "over_target_candidate_count": 0,
                },
            },
            {
                budget_class: {
                    key: row[key]
                    for key in (
                        "candidate_count",
                        "exact_render_signature_count",
                        "over_target_candidate_count",
                    )
                }
                for budget_class, row in frontier["budget_classes"].items()
            },
        )
        global_union = frontier["global_task_review_union"]
        self.assertEqual(
            {"professional": 8, "layer3": 49, "active_reference": 30},
            global_union["frontier_counts"],
        )
        self.assertEqual(
            {"professional": 9, "layer3": 19, "active_reference": 237},
            global_union["safe_complement_counts"],
        )
        self.assertEqual(
            [
                "change-documentation-gate",
                "data-api-contract-changer",
                "data-middleware-change-builder",
                "installed-client-change-builder",
                "integration-change-builder",
                "platform-infrastructure-change-builder",
                "repository-tooling-change-builder",
                "security-privacy-gate",
            ],
            global_union["frontier"]["professional"],
        )
        self.assertEqual(
            [
                "ai-code-review-refactor",
                "architecture-impact-reviewer",
                "delivery-release-gate",
                "engineering-artifact-review",
                "high-risk-design-review",
                "logging-design-gate",
                "quality-test-gate",
                "reliability-observability-gate",
                "routing-quality-review",
            ],
            global_union["safe_complement"]["professional"],
        )
        expected_membership_sha256 = {
            "frontier_professional": "96ce66a72080f6983fafaed55682fdce5f58d152bce2da14fdcda847d6fbd637",
            "frontier_layer3": "d51517ecf92d47fcec3f31b3c05666a311e4673dda16675ca4dda2939c76ef9b",
            "frontier_active_reference": "a793864c5bd30f8cd138da80fadeb1435dc152b8764b028e0a2b6446c39ed4fd",
            "safe_complement_professional": "c07dffc19c8a53524dae5a6c15eea6aab655397dab57cf7d4881fb1e02cdb08e",
            "safe_complement_layer3": "957107f6cebf787b5619cf1084b3d0db40709204e5ea6cdb229906cea12ff3b2",
            "safe_complement_active_reference": "f8bc98538a777e3e69449f5eac324b6316150964feb6e335f12432e5af736d8a",
        }
        actual_membership_sha256 = {
            f"{placement}_{member_kind}": EVAL._sha256_text(
                EVAL._canonical_json_text(global_union[placement][member_kind])
            )
            for placement in ("frontier", "safe_complement")
            for member_kind in ("professional", "layer3", "active_reference")
        }
        self.assertEqual(expected_membership_sha256, actual_membership_sha256)
        self.assertEqual(
            {
                "build_manifests": {
                    "dev": {
                        "path": "dist/universal/skills/dev/.changeforge-build-manifest.json",
                        "sha256": "bbdd2b5c67cddfd8b291d914121c83db3267101ec13bbbe51ec99119b1494afe",
                    },
                    "full": {
                        "path": "dist/universal/skills/full/.changeforge-build-manifest.json",
                        "sha256": "5e019808df71669a97ba2a113b01b54d2ae3e3785f8d69054463548f175d3b9e",
                    },
                    "recommended": {
                        "path": "dist/universal/skills/recommended/.changeforge-build-manifest.json",
                        "sha256": "0cfa21afa89853175a7506e864763aaeb726e335668ccbf7bfddd5aad0810e4e",
                    },
                },
                "capsule_source": {
                    "path": "evals/agent-light-trajectories/cases.yaml",
                    "sha256": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
                },
                "control_projection_sha256": "234f88e0957c619c431d83fcf6232acc17500296a824b1584999ff3ad44573a1",
                "registries": {
                    "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
                    "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
                    "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
                },
                "render_component_inventory": {
                    "count": 1_212,
                    "mapping_sha256": "812fccf58b07b307b38a7da243e08572c55dfe8c433021d3586c8f539f2ed989",
                },
                "selector_authority_sha256": "1b37e9e7b06ea375c418061ae89dd336ed1c703abf7b5c1d5c826fa93df63943",
            },
            frontier["source_fingerprints"],
        )
        self.assertEqual(236_078, frontier["mapping_row_count"])
        self.assertEqual(
            "92efce204a550daffc83b1ce0495c158da9b3088a6e1196cd0bcaca123acfc8d",
            frontier["mapping_digest"],
        )
        self.assertEqual(
            {
                "canonical_representatives_exhausted": True,
                "index_or_catalog_preload": False,
                "numeric_cap": None,
                "task_matcher": False,
                "truncation": False,
            },
            frontier["completeness"],
        )
        consumer_boundary = frontier["consumer_boundary"]
        self.assertTrue(consumer_boundary["projection_only"])
        self.assertEqual([], consumer_boundary["runtime_consumers"])
        self.assertEqual([], consumer_boundary["build_consumers"])
        self.assertEqual(
            {
                "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
                "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
                "src/control-prompts/main-control-agent.md": "c0377059d4b8d010344fc6a7e5377cda22fd70c781478f38239fa841c2a4501b",
                "src/control-skills/engineering-control-plane/references/professional-skill-router.md": "4b40d00ee6c58fed227c51f30e268183fe258ad858a6c95950ffb6b2d99963b3",
            },
            consumer_boundary["checked_path_fingerprints"],
        )
        direct = frontier["budget_classes"]["task"]
        review = frontier["budget_classes"]["review"]
        self.assertEqual(
            {"professional": 8, "layer3": 49, "active_reference": 30},
            direct["frontier_counts"],
        )
        self.assertEqual(
            {"professional": 0, "layer3": 0, "active_reference": 0},
            review["frontier_counts"],
        )
        self.assertEqual(
            2_997,
            max(item["maximum_tokens"] for item in direct["outside"]["active_reference"]),
        )
        self.assertEqual(
            3_598,
            max(item["maximum_tokens"] for item in review["outside"]["active_reference"]),
        )
        for row in frontier["budget_classes"].values():
            for member_kind, witnesses in row["frontier_witnesses"].items():
                self.assertEqual(row["frontier_counts"][member_kind], len(witnesses))
                self.assertTrue(
                    all(witness["maximum_tokens"] > row["target_tokens"] for witness in witnesses)
                )
                self.assertTrue(
                    all(
                        re.fullmatch(r"[0-9a-f]{64}", witness["canonical_reduction_key_sha256"])
                        for witness in witnesses
                    )
                )

    def test_current_frontier_preserves_obligations_with_one_known_overflow(self) -> None:
        composition = self._admissible_report()
        targets = {
            "analysis": 4500,
            "task": 3000,
            "analyzed_task": 6000,
            "review": 3700,
        }
        maxima = composition["max_by_budget_class"]
        self.assertEqual(
            {"analysis": 3_513, "task": 3_202, "analyzed_task": 4_301, "review": 3_598},
            {budget_class: maximum["tokens"] for budget_class, maximum in maxima.items()},
        )
        self.assertEqual(
            ["admissible composition task maximum 3202 exceeds Phase 3 target 3000"],
            composition["errors"],
        )
        self.assertEqual(0, composition["inventory"]["dropped_reference_obligation_count"])
        self.assertEqual(0, composition["inventory"]["required_output_receipt_failure_count"])
        for budget_class, target in targets.items():
            with self.subTest(budget_class=budget_class):
                maximum = maxima[budget_class]
                expected_overflow = budget_class == "task"
                self.assertEqual(expected_overflow, maximum["tokens"] > target)
                self.assertEqual(not expected_overflow, maximum["within_hard_evolution_target"])
                self.assertTrue(maximum["route_obligations_preserved"])

    def test_c1d_data_middleware_benchmark_witness_under_direct_target(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        selection_classes, _inventory, errors = (
            EVAL._admissible_selector_equivalence_classes(authority, projection)
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "data-migration-design",
            "release-rollback",
            "permission-boundary-modeling",
        ]
        selected_class = next(
            item
            for item in selection_classes
            if item["selected_layer3"] == expected_layer3
        )
        receipt = selected_class["receipt"]
        self.assertEqual(
            [],
            EVAL.layer3_selector_runtime_selection_receipt_errors(
                receipt,
                expected_owner="main-control-agent",
                expected_profile="task-agent",
                expected_professional="data-middleware-change-builder",
                expected_selection_kind="implementation-risk",
                expected_selected_layer3=expected_layer3,
            ),
        )
        self.assertEqual(
            "a4e5bbb9d94f00b18ab3a7dc8532bf671a6a69e2908fc5cccbaf7fdd92757f6e",
            receipt["receipt_sha256"],
        )

        selected_owners = {"data-middleware-change-builder", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(12, len(selected_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1D named witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        self.assertEqual(staged["selected_union"], staged["loaded_union"])
        self.assertEqual(12, len(staged["selected_union"]))
        benchmark = [
            "data-migration-design",
            "references/benchmarks-and-patterns.md",
        ]
        benchmark_stage = next(
            stage
            for stage in staged["stages"]
            if stage["loaded_references"] == [benchmark]
        )
        self.assertEqual(1, len(benchmark_stage["loaded_references"]))

        def source_professional_component() -> dict[str, object]:
            path = ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md"
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS:
                values = sections.get(heading, [])
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines("data-middleware-change-builder"))
            output.extend([
                "",
                "## Layer 3 Delivery",
                "",
                "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                "",
            ])
            return EVAL._component(
                "primary_skill",
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        self.assertEqual(
            "fixture:repair-and-rereview:step:18:canonical-capsule",
            capsule["path"],
        )
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_professional_component(),
            *[
                EVAL._file_component(
                    "layer3",
                    ROOT / f"dist/universal/skills/dev/{layer3}/SKILL.md",
                )
                for layer3 in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / "dist/universal/skills/dev/data-migration-design/references/benchmarks-and-patterns.md",
            ),
            capsule,
        ]
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(
            [697, 269, 230, 229, 233, 346, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            2_661,
            measurement["sum_component_tokens"],
        )
        self.assertEqual(2_660, measurement["total_tokens"])
        self.assertEqual(2_667, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])

    def test_frontend_named_direct_evidence_stays_singleton_and_under_target(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="frontend-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "interaction-state-modeling",
            "accessibility-inclusive-design",
            "web-platform-professional-usage",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            "77007dd093f4b9cd5e46dd953ba7982c1709ba32392e33091323bd01c7cc9484",
            selected["receipt"]["receipt_sha256"],
        )

        evidence_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if (record.get("context_admissibility") or {}).get("gap_class")
            == "repo-resolvable-fact"
            and record["owner_skill"]
            in {"frontend-change-builder", *expected_layer3}
        ]
        self.assertEqual(7, len(evidence_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="frontend named Direct evidence",
        )
        owner_roots = {
            "frontend-change-builder": ROOT
            / "src/professional-skills/frontend-change-builder",
            **{
                owner: ROOT / "src/foundation/capabilities" / owner
                for owner in expected_layer3
            },
        }
        for reference in evidence_references:
            with self.subTest(reference=reference):
                staged = EVAL.reference_context_staged_plan(
                    context_authority,
                    references=[reference],
                    path="direct",
                    profile="task-agent",
                    selection_owner="main-control-agent",
                    available_carrier_fields=[],
                    receipt_replayed=True,
                    brief_current=False,
                    review_fresh=True,
                )
                self.assertTrue(staged["reachable"])
                self.assertEqual([list(reference)], staged["selected_union"])
                self.assertEqual([list(reference)], staged["loaded_union"])
                self.assertEqual(1, len(staged["stages"]))
                self.assertEqual(
                    [list(reference)], staged["stages"][0]["loaded_references"]
                )
                tokens = EVAL.count_o200k_base_tokens(
                    (owner_roots[reference[0]] / reference[1]).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertLessEqual(tokens, 400)
                self.assertLessEqual(2_598 + tokens, 3_000)

    def test_review_architecture_named_evidence_stays_singleton_and_under_target(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="architecture-impact-reviewer",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "module-boundary-design",
            "implementation-structure-design",
            "technology-stack-selection",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            "ee2fbb10ab636724db615fb026229648289a1f821c2b78e23733f3f857d55900",
            selected["receipt"]["receipt_sha256"],
        )

        selected_owners = {"architecture-impact-reviewer", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(13, len(selected_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="Review architecture named evidence",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="analyzed",
            profile="review-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        self.assertEqual(
            sorted(staged["selected_union"]), sorted(staged["loaded_union"])
        )
        self.assertEqual(13, len(staged["selected_union"]))
        self.assertTrue(
            all(len(stage["loaded_references"]) == 1 for stage in staged["stages"])
        )

        owner_roots = {
            "architecture-impact-reviewer": ROOT
            / "src/professional-skills/architecture-impact-reviewer",
            **{
                owner: ROOT / "src/foundation/capabilities" / owner
                for owner in expected_layer3
            },
        }
        active_tokens = {
            (owner, path): EVAL.count_o200k_base_tokens(
                (owner_roots[owner] / path).read_text(encoding="utf-8")
            )
            for owner, path in selected_references
        }
        self.assertEqual(
            ("implementation-structure-design", "references/reuse-and-placement.md"),
            max(active_tokens, key=active_tokens.get),
        )
        self.assertLessEqual(max(active_tokens.values()), 807)
        self.assertLessEqual(561 + 785 + 578 + 370 + 290 + 270 + 807, 3_700)


    def test_c1f_repository_tooling_named_direct_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="repository-tooling-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "design-pattern-selection",
            "build-tool-professional-usage",
            "targeted-validation-selection",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            "9675e14cd6ed0e30fd85e02bf5ca9353d7e901d034632d15e1653ca976bc1056",
            selected["receipt"]["receipt_sha256"],
        )

        selected_owners = {"repository-tooling-change-builder", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(
            [
                ("repository-tooling-change-builder", "references/generator-and-plugin-contracts.md"),
                ("repository-tooling-change-builder", "references/harness-validity-contracts.md"),
                ("repository-tooling-change-builder", "references/repository-automation-contracts.md"),
                ("build-tool-professional-usage", "references/benchmarks-and-patterns.md"),
                ("build-tool-professional-usage", "references/checklist.md"),
                ("build-tool-professional-usage", "references/evidence-patterns.md"),
                ("design-pattern-selection", "references/pattern-evidence-record.md"),
                ("targeted-validation-selection", "references/repository-command-entry-evidence.md"),
            ],
            selected_references,
        )
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1F repository-tooling named Direct witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        expected_selected_union = [list(reference) for reference in selected_references]
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(8, len(staged["selected_union"]))
        self.assertEqual(8, len(staged["loaded_union"]))
        self.assertEqual(8, len(staged["stages"]))
        self.assertEqual(8, len(staged["required_output_receipts"]))
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        active_reference = [
            "repository-tooling-change-builder",
            "references/generator-and-plugin-contracts.md",
        ]
        active_stage = next(
            stage for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(4, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["boundary-decision", "selected-approach", "proof-limit"],
            }],
            active_stage["required_output_receipts"],
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/repository-tooling-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "repository-tooling-change-builder",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/professional-skills/repository-tooling-change-builder/references/generator-and-plugin-contracts.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 261, 222, 269, 223, 431, 657],
            [item["tokens"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_760, measurement["sum_component_tokens"])
        self.assertEqual(2_759, measurement["total_tokens"])
        self.assertEqual(2_766, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertEqual(3_001, EVAL._component_upper_bound(components) + 235)

    def test_c1f_reliability_named_review_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="reliability-observability-gate",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "degradation-circuit-breaking",
            "observability",
            "backup-recovery",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            "141c7fccec4e72d06d444554f3451465a7612a8128a176840bd80c51ed23b18a",
            selected["receipt"]["receipt_sha256"],
        )

        selected_owners = {"reliability-observability-gate", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        expected_selected_references = [
            ("reliability-observability-gate", "references/checklist.md"),
            ("reliability-observability-gate", "references/evidence-patterns.md"),
            ("reliability-observability-gate", "references/reliability-output-and-gates.md"),
            ("reliability-observability-gate", "references/solution-optimality.md"),
            ("degradation-circuit-breaking", "references/benchmarks-and-patterns.md"),
            ("degradation-circuit-breaking", "references/checklist.md"),
            ("degradation-circuit-breaking", "references/evidence-patterns.md"),
            ("observability", "references/benchmarks-and-patterns.md"),
            ("observability", "references/checklist.md"),
            ("observability", "references/evidence-patterns.md"),
            ("backup-recovery", "references/benchmarks-and-patterns.md"),
            ("backup-recovery", "references/checklist.md"),
            ("backup-recovery", "references/evidence-patterns.md"),
        ]
        self.assertEqual(expected_selected_references, selected_references)
        self.assertEqual(13, len(selected_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1F reliability named Review witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="analyzed",
            profile="review-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        expected_selected_union = [list(reference) for reference in selected_references]
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(13, len(staged["selected_union"]))
        self.assertEqual(13, len(staged["loaded_union"]))
        self.assertEqual(13, len(staged["stages"]))
        self.assertEqual(13, len(staged["required_output_receipts"]))
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        active_reference = [
            "reliability-observability-gate",
            "references/reliability-output-and-gates.md",
        ]
        active_stage = next(
            stage for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(11, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["gate-decision", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["review"]
        components = [
            EVAL._file_component(
                "review_profile",
                ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/reliability-observability-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "reliability-observability-gate",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/professional-skills/reliability-observability-gate/references/reliability-output-and-gates.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [561, 341, 209, 180, 224, 630, 785],
            [item["tokens"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="review",
            token_budget=EVAL.FROZEN_GATES["review"],
        )
        self.assertEqual(2_930, measurement["sum_component_tokens"])
        self.assertEqual(2_929, measurement["total_tokens"])
        self.assertEqual(2_936, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertEqual(3_701, EVAL._component_upper_bound(components) + 765)

    def test_c1g_delivery_release_named_task_and_review_witnesses_are_bounded(self) -> None:
        authority = EVAL._selector_authority()
        expected_layer3 = [
            "release-rollback",
            "version-compatibility",
            "configuration-runtime-policy",
        ]
        expected_selected_references = [
            ("delivery-release-gate", "references/checklist.md"),
            ("delivery-release-gate", "references/delivery-output-and-gates.md"),
            ("delivery-release-gate", "references/release-evidence-patterns.md"),
            ("release-rollback", "references/benchmarks-and-patterns.md"),
            ("release-rollback", "references/checklist.md"),
            ("release-rollback", "references/evidence-patterns.md"),
            ("version-compatibility", "references/checklist.md"),
            ("version-compatibility", "references/compatibility-benchmarks.md"),
            ("version-compatibility", "references/evidence-patterns.md"),
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"),
            ("configuration-runtime-policy", "references/checklist.md"),
            ("configuration-runtime-policy", "references/evidence-patterns.md"),
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(expected_selected_references)
        ]
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1G delivery-release named Task and Review witnesses",
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsules = EVAL._capsule_envelopes(EVAL._fixture_cases(document))
        cases = (
            {
                "budget_class": "task",
                "profile": "task-agent",
                "selection_owner": "main-control-agent",
                "path": "direct",
                "brief_current": False,
                "receipt": "ff2e40b9dac8df918ee255de792fe38e76b797daa2053634bfbb982f98a3448a",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
                "profile_kind": "worker_profile",
                "capsule": capsules["task"],
                "component_tokens": [697, 310, 229, 250, 183, 474, 657],
                "component_shas": [
                    "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                    "58d88e71ba05ce0b36336ac8ef70f3f13ded845a842ac99fcdc01a5911ae7e5c",
                    "3e2150a21b3997726207b6ac9317c8077856708c87a481ac818898779c78229a",
                    "989a93e84c8ba897bdc8ba69113da520c11207996f1d64b7ad59b4810284ae91",
                    "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237",
                    "af7766cecc9f29fad1063a16234c6bf69cc7fb62148a6934c7b498de7d5eb893",
                    "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
                ],
                "sum_component_tokens": 2_800,
                "total_tokens": 2_799,
                "upper_bound": 2_806,
                "negative_delta": 195,
            },
            {
                "budget_class": "review",
                "profile": "review-agent",
                "selection_owner": "engineering-brief",
                "path": "analyzed",
                "brief_current": True,
                "receipt": "a315f22c298373562a6f6d6120b954f95dbef726a57b7bc9b13572b0d9ff3a58",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
                "profile_kind": "review_profile",
                "capsule": capsules["review"],
                "component_tokens": [561, 310, 229, 250, 183, 474, 785],
                "component_shas": [
                    "fd175f897ff02b1a4b9d1acfb2eeec57f87a8a2e8de9a1716c45a710b141cfe9",
                    "58d88e71ba05ce0b36336ac8ef70f3f13ded845a842ac99fcdc01a5911ae7e5c",
                    "3e2150a21b3997726207b6ac9317c8077856708c87a481ac818898779c78229a",
                    "989a93e84c8ba897bdc8ba69113da520c11207996f1d64b7ad59b4810284ae91",
                    "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237",
                    "af7766cecc9f29fad1063a16234c6bf69cc7fb62148a6934c7b498de7d5eb893",
                    "3a1fe3cd1caea75f3aa1c7c9459d8a36de520f0e78a9ce9719b8f8ba13489e35",
                ],
                "sum_component_tokens": 2_792,
                "total_tokens": 2_791,
                "upper_bound": 2_798,
                "negative_delta": 903,
            },
        )
        for case in cases:
            with self.subTest(profile=case["profile"]):
                projection = EVAL.layer3_selector_runtime_projection(
                    authority,
                    professional_skill="delivery-release-gate",
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    exact_layer3=None,
                )
                classes, _inventory, errors = (
                    EVAL._admissible_selector_equivalence_classes(
                        authority, projection
                    )
                )
                self.assertEqual([], errors)
                selected = next(
                    item
                    for item in classes
                    if item["selected_layer3"] == expected_layer3
                )
                self.assertEqual(case["receipt"], selected["receipt"]["receipt_sha256"])
                self.assertTrue(
                    set(expected_layer3).isdisjoint(projection["domain_authorization"])
                )
                selected_owners = {"delivery-release-gate", *expected_layer3}
                selected_references = [
                    (record["owner_skill"], record["path"])
                    for record in projection["reference_records"]
                    if record["owner_skill"] in selected_owners
                ]
                self.assertEqual(expected_selected_references, selected_references)
                staged = EVAL.reference_context_staged_plan(
                    context_authority,
                    references=selected_references,
                    path=case["path"],
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    available_carrier_fields=[],
                    receipt_replayed=True,
                    brief_current=case["brief_current"],
                    review_fresh=True,
                )
                expected_selected_union = [
                    list(reference) for reference in selected_references
                ]
                self.assertTrue(staged["reachable"])
                self.assertEqual(expected_selected_union, staged["selected_union"])
                self.assertEqual(expected_loaded_union, staged["loaded_union"])
                self.assertEqual(
                    {tuple(reference) for reference in expected_selected_union},
                    {tuple(reference) for reference in expected_loaded_union},
                )
                self.assertEqual(12, len(staged["selected_union"]))
                self.assertEqual(12, len(staged["loaded_union"]))
                self.assertEqual(12, len(staged["stages"]))
                self.assertEqual(12, len(staged["required_output_receipts"]))
                self.assertEqual(
                    expected_loaded_union,
                    [stage["loaded_references"][0] for stage in staged["stages"]],
                )
                self.assertTrue(
                    all(
                        len(stage["loaded_references"]) == 1
                        and stage["carried_predecessors"] == []
                        for stage in staged["stages"]
                    )
                )
                self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
                self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
                active_reference = [
                    "version-compatibility",
                    "references/compatibility-benchmarks.md",
                ]
                active_stage = next(
                    stage
                    for stage in staged["stages"]
                    if stage["loaded_references"] == [active_reference]
                )
                self.assertEqual(10, active_stage["stage"])
                self.assertEqual([], active_stage["carried_predecessors"])
                self.assertEqual(
                    [{
                        "reference": active_reference,
                        "required_outputs": ["option-comparison", "selected-approach"],
                    }],
                    active_stage["required_output_receipts"],
                )
                components = [
                    EVAL._file_component(
                        case["profile_kind"], case["profile_path"]
                    ),
                    compact_source_component(
                        "primary_skill",
                        ROOT / "src/professional-skills/delivery-release-gate/SKILL.md",
                        BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                        "delivery-release-gate",
                    ),
                    *[
                        compact_source_component(
                            "layer3",
                            ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                            BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                            None,
                        )
                        for owner in expected_layer3
                    ],
                    EVAL._file_component(
                        "layer3_reference",
                        ROOT / "src/foundation/capabilities/version-compatibility/references/compatibility-benchmarks.md",
                    ),
                    case["capsule"],
                ]
                self.assertEqual(
                    case["component_tokens"],
                    [item["tokens"] for item in components],
                )
                self.assertEqual(
                    case["component_shas"],
                    [item["sha256"] for item in components],
                )
                measurement = EVAL._measure_context(
                    components,
                    budget_class=case["budget_class"],
                    token_budget=EVAL.FROZEN_GATES[case["budget_class"]],
                )
                self.assertEqual(
                    case["sum_component_tokens"],
                    measurement["sum_component_tokens"],
                )
                self.assertEqual(case["total_tokens"], measurement["total_tokens"])
                self.assertEqual(
                    case["upper_bound"], EVAL._component_upper_bound(components)
                )
                self.assertTrue(measurement["within_token_budget"])
                self.assertEqual(
                    EVAL.PHASE3_CONTEXT_TARGETS[case["budget_class"]] + 1,
                    EVAL._component_upper_bound(components) + case["negative_delta"],
                )

    def test_c1h_logging_named_task_and_review_witnesses_are_bounded(self) -> None:
        authority = EVAL._selector_authority()
        expected_layer3 = [
            "audit-evidence-integrity",
            "secret-configuration-security",
            "logging-error-handling",
        ]
        expected_selected_references = [
            ("logging-design-gate", "references/checklist.md"),
            ("logging-design-gate", "references/logging-output-and-gates.md"),
            ("logging-design-gate", "references/logging-selection-criteria.md"),
            ("logging-error-handling", "references/benchmarks-and-patterns.md"),
            ("logging-error-handling", "references/checklist.md"),
            ("logging-error-handling", "references/evidence-patterns.md"),
            ("secret-configuration-security", "references/benchmarks-and-patterns.md"),
            ("secret-configuration-security", "references/checklist.md"),
            ("secret-configuration-security", "references/evidence-patterns.md"),
            ("audit-evidence-integrity", "references/completeness-identity-and-time.md"),
            ("audit-evidence-integrity", "references/tamper-evidence-storage-and-access.md"),
            ("audit-evidence-integrity", "references/retention-export-and-chain-of-custody.md"),
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(expected_selected_references)
        ]
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1H logging named Task and Review witnesses",
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsules = EVAL._capsule_envelopes(EVAL._fixture_cases(document))
        cases = (
            {
                "budget_class": "task",
                "profile": "task-agent",
                "selection_owner": "main-control-agent",
                "path": "direct",
                "brief_current": False,
                "receipt": "847e3e393a0b788fde7fff1b6e1197b77f9c93645557ab028a12c251a05e2ed3",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
                "profile_kind": "worker_profile",
                "capsule": capsules["task"],
                "component_tokens": [697, 293, 236, 202, 226, 468, 657],
                "component_shas": [
                    "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                    "e6313187ef53df0de6bb2de88839d3589bff2a6f3585d808e0b7df2d922d5067",
                    "e31d6327abc44b7be5ba6887f0ca587d9289e35459d82d09cc4389be01f4e8c0",
                    "c0bddf002b385fddd4834ad4670cdc91cb539b22bfc3b1ed2870dff423439d2b",
                    "156956a35e90e36dff8c9fe49b8ac006c97ca16d3b78b775da3a5f618927d6b3",
                    "53aa82fd9b802487c4f5e92f999fa9ca96f4b8666f6054807cf106e07d5f6834",
                    "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
                ],
                "sum_component_tokens": 2_779,
                "total_tokens": 2_778,
                "upper_bound": 2_785,
                "negative_delta": 216,
            },
            {
                "budget_class": "review",
                "profile": "review-agent",
                "selection_owner": "engineering-brief",
                "path": "analyzed",
                "brief_current": True,
                "receipt": "68c159e1558c75166882b4559ece25fb3c5b0828f27b4df1dbc8b17f93eba78a",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
                "profile_kind": "review_profile",
                "capsule": capsules["review"],
                "component_tokens": [561, 293, 236, 202, 226, 468, 785],
                "component_shas": [
                    "fd175f897ff02b1a4b9d1acfb2eeec57f87a8a2e8de9a1716c45a710b141cfe9",
                    "e6313187ef53df0de6bb2de88839d3589bff2a6f3585d808e0b7df2d922d5067",
                    "e31d6327abc44b7be5ba6887f0ca587d9289e35459d82d09cc4389be01f4e8c0",
                    "c0bddf002b385fddd4834ad4670cdc91cb539b22bfc3b1ed2870dff423439d2b",
                    "156956a35e90e36dff8c9fe49b8ac006c97ca16d3b78b775da3a5f618927d6b3",
                    "53aa82fd9b802487c4f5e92f999fa9ca96f4b8666f6054807cf106e07d5f6834",
                    "3a1fe3cd1caea75f3aa1c7c9459d8a36de520f0e78a9ce9719b8f8ba13489e35",
                ],
                "sum_component_tokens": 2_771,
                "total_tokens": 2_770,
                "upper_bound": 2_777,
                "negative_delta": 924,
            },
        )
        for case in cases:
            with self.subTest(profile=case["profile"]):
                projection = EVAL.layer3_selector_runtime_projection(
                    authority,
                    professional_skill="logging-design-gate",
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    exact_layer3=None,
                )
                classes, _inventory, errors = (
                    EVAL._admissible_selector_equivalence_classes(
                        authority, projection
                    )
                )
                self.assertEqual([], errors)
                selected = next(
                    item
                    for item in classes
                    if item["selected_layer3"] == expected_layer3
                )
                self.assertEqual(case["receipt"], selected["receipt"]["receipt_sha256"])
                self.assertTrue(
                    set(expected_layer3).isdisjoint(projection["domain_authorization"])
                )
                self.assertEqual([], projection["domain_authorization"])
                selected_owners = {"logging-design-gate", *expected_layer3}
                selected_references = [
                    (record["owner_skill"], record["path"])
                    for record in projection["reference_records"]
                    if record["owner_skill"] in selected_owners
                ]
                self.assertEqual(expected_selected_references, selected_references)
                reference_components = [
                    EVAL._file_component(
                        "layer3_reference",
                        (
                            ROOT
                            / (
                                "src/professional-skills"
                                if owner == "logging-design-gate"
                                else "src/foundation/capabilities"
                            )
                            / owner
                            / path
                        ),
                    )
                    for owner, path in selected_references
                ]
                self.assertEqual(12, len(reference_components))
                self.assertTrue(
                    all(item["tokens"] <= 468 for item in reference_components)
                )
                self.assertEqual(
                    468, max(item["tokens"] for item in reference_components)
                )
                staged = EVAL.reference_context_staged_plan(
                    context_authority,
                    references=selected_references,
                    path=case["path"],
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    available_carrier_fields=[],
                    receipt_replayed=True,
                    brief_current=case["brief_current"],
                    review_fresh=True,
                )
                expected_selected_union = [
                    list(reference) for reference in selected_references
                ]
                self.assertTrue(staged["reachable"])
                self.assertEqual(expected_selected_union, staged["selected_union"])
                self.assertEqual(expected_loaded_union, staged["loaded_union"])
                self.assertEqual(
                    {tuple(reference) for reference in expected_selected_union},
                    {tuple(reference) for reference in expected_loaded_union},
                )
                self.assertEqual(12, len(staged["selected_union"]))
                self.assertEqual(12, len(staged["loaded_union"]))
                self.assertEqual(12, len(staged["stages"]))
                self.assertEqual(12, len(staged["required_output_receipts"]))
                self.assertEqual(
                    expected_loaded_union,
                    [stage["loaded_references"][0] for stage in staged["stages"]],
                )
                self.assertTrue(
                    all(
                        len(stage["loaded_references"]) == 1
                        and stage["carried_predecessors"] == []
                        for stage in staged["stages"]
                    )
                )
                self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
                self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
                active_reference = [
                    "logging-error-handling",
                    "references/benchmarks-and-patterns.md",
                ]
                active_stage = next(
                    stage
                    for stage in staged["stages"]
                    if stage["loaded_references"] == [active_reference]
                )
                self.assertEqual(6, active_stage["stage"])
                self.assertEqual([], active_stage["carried_predecessors"])
                self.assertEqual(
                    [{
                        "reference": active_reference,
                        "required_outputs": ["option-comparison", "selected-approach"],
                    }],
                    active_stage["required_output_receipts"],
                )
                components = [
                    EVAL._file_component(
                        case["profile_kind"], case["profile_path"]
                    ),
                    compact_source_component(
                        "primary_skill",
                        ROOT / "src/professional-skills/logging-design-gate/SKILL.md",
                        BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                        "logging-design-gate",
                    ),
                    *[
                        compact_source_component(
                            "layer3",
                            ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                            BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                            None,
                        )
                        for owner in expected_layer3
                    ],
                    EVAL._file_component(
                        "layer3_reference",
                        ROOT / "src/foundation/capabilities/logging-error-handling/references/benchmarks-and-patterns.md",
                    ),
                    case["capsule"],
                ]
                self.assertEqual(
                    case["component_tokens"],
                    [item["tokens"] for item in components],
                )
                self.assertEqual(
                    case["component_shas"],
                    [item["sha256"] for item in components],
                )
                measurement = EVAL._measure_context(
                    components,
                    budget_class=case["budget_class"],
                    token_budget=EVAL.FROZEN_GATES[case["budget_class"]],
                )
                self.assertEqual(
                    case["sum_component_tokens"],
                    measurement["sum_component_tokens"],
                )
                self.assertEqual(case["total_tokens"], measurement["total_tokens"])
                self.assertEqual(
                    case["upper_bound"], EVAL._component_upper_bound(components)
                )
                self.assertTrue(measurement["within_token_budget"])
                self.assertEqual(
                    EVAL.PHASE3_CONTEXT_TARGETS[case["budget_class"]] + 1,
                    EVAL._component_upper_bound(components) + case["negative_delta"],
                )

    def test_c1i_quality_task_and_review_projection_witnesses_are_bounded(self) -> None:
        authority = EVAL._selector_authority()
        professional = EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY)
        foundation = EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY)
        domain = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain["domain_skills"]}
        context_authority = EVAL.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="C1I named Task and Review projections",
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsules = EVAL._capsule_envelopes(EVAL._fixture_cases(document))

        task_layer3 = [
            "test-data-management",
            "targeted-validation-selection",
            "test-strategy",
        ]
        task_projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="quality-test-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        task_classes, _task_inventory, task_errors = (
            EVAL._admissible_selector_equivalence_classes(
                authority, task_projection
            )
        )
        self.assertEqual([], task_errors)
        task_selected = next(
            item
            for item in task_classes
            if item["selected_layer3"] == task_layer3
        )
        self.assertEqual(
            "0c9aa8b856780e9aecfa385003bc7f2b87167ed326e3863b570c79af4a7848a9",
            task_selected["receipt"]["receipt_sha256"],
        )
        self.assertTrue(
            set(task_layer3).isdisjoint(task_projection["domain_authorization"])
        )
        task_owners = {"quality-test-gate", *task_layer3}
        expected_task_selected_references = [
            ("quality-test-gate", "references/checklist.md"),
            ("quality-test-gate", "references/test-output-and-gates.md"),
            ("quality-test-gate", "references/test-structure-boundaries.md"),
            ("test-strategy", "references/benchmarks-and-patterns.md"),
            ("test-strategy", "references/checklist.md"),
            ("test-strategy", "references/evidence-patterns.md"),
            ("test-data-management", "references/benchmarks-and-patterns.md"),
            ("test-data-management", "references/checklist.md"),
            ("test-data-management", "references/evidence-patterns.md"),
            (
                "targeted-validation-selection",
                "references/repository-command-entry-evidence.md",
            ),
        ]
        task_selected_references = [
            (record["owner_skill"], record["path"])
            for record in task_projection["reference_records"]
            if record["owner_skill"] in task_owners
        ]
        self.assertEqual(
            expected_task_selected_references,
            task_selected_references,
        )
        self.assertEqual(
            set(),
            {owner for owner, _path in task_selected_references} & domain_names,
        )
        task_staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=task_selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_task_selected_union = [
            list(reference) for reference in expected_task_selected_references
        ]
        expected_task_loaded_union = [
            list(reference) for reference in sorted(task_selected_references)
        ]
        expected_task_stage_outputs = [
            (["quality-test-gate", "references/checklist.md"], ["checklist-result", "validation-plan"]),
            (["quality-test-gate", "references/test-output-and-gates.md"], ["gate-decision", "residual-risk"]),
            (["quality-test-gate", "references/test-structure-boundaries.md"], ["validation-plan", "proof-limit"]),
            (["targeted-validation-selection", "references/repository-command-entry-evidence.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["test-data-management", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["test-data-management", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["test-data-management", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["test-strategy", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["test-strategy", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["test-strategy", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
        ]
        self.assertTrue(task_staged["reachable"])
        self.assertEqual(
            expected_task_selected_union, task_staged["selected_union"]
        )
        self.assertEqual(
            expected_task_loaded_union, task_staged["loaded_union"]
        )
        self.assertEqual(10, len(task_staged["stages"]))
        self.assertEqual(10, len(task_staged["required_output_receipts"]))
        self.assertEqual([], task_staged["carried_predecessors"])
        for stage, (reference, required_outputs) in zip(
            task_staged["stages"],
            expected_task_stage_outputs,
            strict=True,
        ):
            self.assertEqual([reference], stage["loaded_references"])
            self.assertEqual([], stage["carried_predecessors"])
            self.assertEqual(
                [{"reference": reference, "required_outputs": required_outputs}],
                stage["required_output_receipts"],
            )
        task_reference_components = [
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / (
                    "src/professional-skills"
                    if owner == "quality-test-gate"
                    else "src/foundation/capabilities"
                )
                / owner
                / path,
            )
            for owner, path in task_selected_references
        ]
        self.assertEqual(10, len(task_reference_components))
        self.assertTrue(
            all(item["tokens"] <= 565 for item in task_reference_components)
        )
        self.assertEqual(
            565, max(item["tokens"] for item in task_reference_components)
        )
        task_active_reference = [
            "quality-test-gate",
            "references/test-output-and-gates.md",
        ]
        task_active_stage = next(
            stage
            for stage in task_staged["stages"]
            if stage["loaded_references"] == [task_active_reference]
        )
        self.assertEqual(1, task_active_stage["stage"])
        self.assertEqual([], task_active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": task_active_reference,
                "required_outputs": ["gate-decision", "residual-risk"],
            }],
            task_active_stage["required_output_receipts"],
        )
        task_components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/quality-test-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "quality-test-gate",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in task_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / "src/professional-skills/quality-test-gate/references/test-output-and-gates.md",
            ),
            capsules["task"],
        ]
        self.assertEqual(
            [697, 309, 257, 223, 232, 565, 657],
            [item["tokens"] for item in task_components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "a1b284bddfd1cdf9fed94e175d603e2db962ab597ba443ab58d3e1a8c3d543b6",
                "535ce74d430ee2cf20f237d416d8f0ec8b8f2c498cc7b262d2ab16624af16e65",
                "33361cbcacb5926d779a486126acb5d4f5edb211655effedee3b6053aa763730",
                "eb3ff8d61501d0a450aa9f72d60f5f96248791b06fb3b0cae7a57792d6780750",
                "c1bf533e04443976a6bbe8ee77121a9117e88ffb868c39402311e9aa016c3409",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in task_components],
        )
        task_measurement = EVAL._measure_context(
            task_components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_940, task_measurement["sum_component_tokens"])
        self.assertEqual(2_939, task_measurement["total_tokens"])
        self.assertEqual(2_946, EVAL._component_upper_bound(task_components))
        self.assertTrue(task_measurement["within_token_budget"])
        self.assertEqual(
            EVAL.PHASE3_CONTEXT_TARGETS["task"] + 1,
            EVAL._component_upper_bound(task_components) + 55,
        )
        review_layer3 = [
            "domain-object-identification",
            "implementation-structure-design",
            "refactoring",
        ]
        review_projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="ai-code-review-refactor",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        review_classes, _review_inventory, review_errors = (
            EVAL._admissible_selector_equivalence_classes(
                authority, review_projection
            )
        )
        self.assertEqual([], review_errors)
        review_selected = next(
            item
            for item in review_classes
            if item["selected_layer3"] == review_layer3
        )
        self.assertEqual(
            "ccdcc0383fe8a0956f5b801f66c9fb4173aa00336eed4ee10c252825ea2a3098",
            review_selected["receipt"]["receipt_sha256"],
        )
        self.assertTrue(
            set(review_layer3).isdisjoint(
                review_projection["domain_authorization"]
            )
        )
        review_owners = {"ai-code-review-refactor", *review_layer3}
        expected_review_selected_references = [
            ("ai-code-review-refactor", "references/ai-review-pattern-catalog.md"),
            ("ai-code-review-refactor", "references/review-output-and-gates.md"),
            ("ai-code-review-refactor", "references/solution-optimality.md"),
            ("domain-object-identification", "references/benchmarks-and-patterns.md"),
            ("domain-object-identification", "references/checklist.md"),
            ("domain-object-identification", "references/evidence-patterns.md"),
            ("implementation-structure-design", "references/object-module-decomposition.md"),
            ("implementation-structure-design", "references/reuse-and-placement.md"),
            ("implementation-structure-design", "references/evidence-patterns.md"),
            ("refactoring", "references/behavior-preservation-evidence.md"),
            ("refactoring", "references/checklist.md"),
            ("refactoring", "references/split-merge-cleanup-patterns.md"),
        ]
        review_selected_references = [
            (record["owner_skill"], record["path"])
            for record in review_projection["reference_records"]
            if record["owner_skill"] in review_owners
            and not (
                record["owner_skill"] == "ai-code-review-refactor"
                and record["path"] == "references/checklist.md"
            )
        ]
        self.assertEqual(
            expected_review_selected_references,
            review_selected_references,
        )
        self.assertEqual(
            set(),
            {owner for owner, _path in review_selected_references} & domain_names,
        )
        review_declarations = context_authority["owners"][
            "ai-code-review-refactor"
        ]["declarations"]
        self.assertEqual(
            [
                "references/ai-review-pattern-catalog.md",
                "references/review-output-and-gates.md",
            ],
            review_declarations["references/checklist.md"]["conflicts_with"],
        )
        self.assertNotIn(
            ("ai-code-review-refactor", "references/checklist.md"),
            review_selected_references,
        )
        expected_review_loaded_union = [
            list(reference) for reference in sorted(review_selected_references)
        ]
        review_records = {
            (record["owner_skill"], record["path"]): record
            for record in review_projection["reference_records"]
            if (record["owner_skill"], record["path"])
            in set(review_selected_references)
        }
        expected_review_stage_outputs = [
            (["ai-code-review-refactor", "references/ai-review-pattern-catalog.md"], ["option-comparison", "selected-approach"]),
            (["ai-code-review-refactor", "references/review-output-and-gates.md"], ["gate-decision", "residual-risk"]),
            (["ai-code-review-refactor", "references/solution-optimality.md"], ["selected-approach", "residual-risk"]),
            (["domain-object-identification", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["domain-object-identification", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["domain-object-identification", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["implementation-structure-design", "references/evidence-patterns.md"], ["evidence-record", "validation-plan", "proof-limit", "residual-risk"]),
            (["implementation-structure-design", "references/object-module-decomposition.md"], ["decision-record", "validation-plan", "proof-limit", "residual-risk"]),
            (["implementation-structure-design", "references/reuse-and-placement.md"], ["selected-approach", "validation-plan", "proof-limit", "residual-risk"]),
            (["refactoring", "references/behavior-preservation-evidence.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["refactoring", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["refactoring", "references/split-merge-cleanup-patterns.md"], ["option-comparison", "selected-approach"]),
        ]
        actual_review_stages = []
        for stage, reference in enumerate(expected_review_loaded_union):
            record = review_records[tuple(reference)]
            self.assertEqual("singleton", record["residency"])
            actual_review_stages.append(
                (
                    stage,
                    reference,
                    record["required_output"],
                    [],
                )
            )
        self.assertEqual(
            [
                (stage, reference, outputs, [])
                for stage, (reference, outputs) in enumerate(
                    expected_review_stage_outputs
                )
            ],
            actual_review_stages,
        )
        self.assertEqual(12, len(review_selected_references))
        self.assertEqual(12, len(expected_review_loaded_union))
        self.assertEqual(
            {tuple(reference) for reference in review_selected_references},
            {tuple(reference) for reference in expected_review_loaded_union},
        )
        self.assertNotEqual(
            review_selected_references, review_selected_references[:-1]
        )
        self.assertNotEqual(
            expected_review_loaded_union, expected_review_loaded_union[:-1]
        )
        review_active_reference = [
            "refactoring",
            "references/split-merge-cleanup-patterns.md",
        ]
        review_active_stage = next(
            item
            for item in actual_review_stages
            if item[1] == review_active_reference
        )
        self.assertEqual(
            (11, review_active_reference, ["option-comparison", "selected-approach"], []),
            review_active_stage,
        )
        review_components = [
            EVAL._file_component(
                "review_profile",
                ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
            ),
            EVAL._file_component(
                "primary_skill",
                ROOT
                / "dist/copilot/project/.github/skills/recommended/ai-code-review-refactor/SKILL.md",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in review_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / "src/foundation/capabilities/refactoring/references/split-merge-cleanup-patterns.md",
            ),
            capsules["review"],
        ]
        self.assertEqual(
            [561, 298, 369, 302, 336, 948, 785],
            [item["tokens"] for item in review_components],
        )
        self.assertEqual(
            [
                "fd175f897ff02b1a4b9d1acfb2eeec57f87a8a2e8de9a1716c45a710b141cfe9",
                "bc92739d0a17a4216e7710f19cb1e035fe59e48e2623c6441ccd9d82a43d997e",
                "5d3f4ac9f0add16b6dd447315930d17f0f5afb4dea035d2a6f089a142c8a8767",
                "c9981d67a0942008d538317d2fcec97cf41f3b3c6ad761d6efb48899df53f080",
                "e410a99956cdb0359b3ffec2602e8a67e8cc97b2fe94e0f237fab7a9c9331cf6",
                "96b49d2084c6c8834a044ce4700ea6135db4fede99f70a9a6a559c8dba10b2db",
                "3a1fe3cd1caea75f3aa1c7c9459d8a36de520f0e78a9ce9719b8f8ba13489e35",
            ],
            [item["sha256"] for item in review_components],
        )
        review_measurement = EVAL._measure_context(
            review_components,
            budget_class="review",
            token_budget=EVAL.FROZEN_GATES["review"],
        )
        self.assertEqual(3_599, review_measurement["sum_component_tokens"])
        self.assertEqual(3_598, review_measurement["total_tokens"])
        self.assertEqual(3_605, EVAL._component_upper_bound(review_components))
        self.assertTrue(review_measurement["within_token_budget"])
        self.assertEqual(
            EVAL.PHASE3_CONTEXT_TARGETS["review"] + 1,
            EVAL._component_upper_bound(review_components) + 96,
        )

    def test_c1j_data_middleware_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        professional = EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY)
        foundation = EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY)
        domain = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain["domain_skills"]}
        expected_layer3 = [
            "concurrency-control",
            "transaction-consistency",
            "distributed-workflow-consistency",
        ]
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = (
            EVAL._admissible_selector_equivalence_classes(authority, projection)
        )
        self.assertEqual([], errors)
        selected = next(
            item for item in classes
            if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            "781c2b9d96451b0dee91dfce30b51f91e692fee664219aa8a0c127e6a70f204e",
            selected["receipt"]["receipt_sha256"],
        )
        self.assertTrue(
            set(expected_layer3).isdisjoint(projection["domain_authorization"])
        )

        selected_owners = {"data-middleware-change-builder", *expected_layer3}
        expected_selected_references = [
            ("data-middleware-change-builder", "references/checklist.md"),
            ("data-middleware-change-builder", "references/evidence-patterns.md"),
            ("data-middleware-change-builder", "references/recovery-patterns.md"),
            ("transaction-consistency", "references/benchmarks-and-patterns.md"),
            ("transaction-consistency", "references/checklist.md"),
            ("transaction-consistency", "references/evidence-patterns.md"),
            ("concurrency-control", "references/benchmarks-and-patterns.md"),
            ("concurrency-control", "references/checklist.md"),
            ("concurrency-control", "references/evidence-patterns.md"),
            ("distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"),
            ("distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"),
            ("distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"),
        ]
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(expected_selected_references, selected_references)
        self.assertEqual(
            set(),
            {owner for owner, _path in selected_references} & domain_names,
        )

        context_authority = EVAL.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="C1J data-middleware named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected_union = [
            list(reference) for reference in expected_selected_references
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(expected_selected_references)
        ]
        expected_stage_outputs = [
            (["concurrency-control", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["concurrency-control", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["concurrency-control", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["data-middleware-change-builder", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["data-middleware-change-builder", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["data-middleware-change-builder", "references/recovery-patterns.md"], ["option-comparison", "selected-approach"]),
            (["distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"], ["failure-decision", "selected-approach", "residual-risk"]),
            (["distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"], ["boundary-decision", "failure-decision", "proof-limit"]),
            (["distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"], ["failure-decision", "validation-plan", "proof-limit"]),
            (["transaction-consistency", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["transaction-consistency", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["transaction-consistency", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(12, len(staged["selected_union"]))
        self.assertEqual(12, len(staged["loaded_union"]))
        self.assertEqual(12, len(staged["stages"]))
        self.assertEqual(12, len(staged["required_output_receipts"]))
        self.assertEqual([], staged["carried_predecessors"])
        for stage, (reference, required_outputs) in zip(
            staged["stages"], expected_stage_outputs, strict=True
        ):
            self.assertEqual([reference], stage["loaded_references"])
            self.assertEqual([], stage["carried_predecessors"])
            self.assertEqual(
                [{"reference": reference, "required_outputs": required_outputs}],
                stage["required_output_receipts"],
            )
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        owner_roots = {
            "data-middleware-change-builder": ROOT / "src/professional-skills/data-middleware-change-builder",
            **{
                owner: ROOT / "src/foundation/capabilities" / owner
                for owner in expected_layer3
            },
        }
        reference_components = [
            EVAL._file_component(
                "layer3_reference", owner_roots[owner] / path
            )
            for owner, path in selected_references
        ]
        self.assertEqual(12, len(reference_components))
        self.assertTrue(all(item["tokens"] <= 608 for item in reference_components))
        self.assertEqual(608, max(item["tokens"] for item in reference_components))

        active_reference = [
            "transaction-consistency",
            "references/evidence-patterns.md",
        ]
        active_stage = next(
            stage for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(11, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["evidence-record", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        worst_reference = (
            ROOT
            / "src/foundation/capabilities/transaction-consistency/references/benchmarks-and-patterns.md"
        )
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "data-middleware-change-builder",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component("layer3_reference", worst_reference),
            capsule,
        ]
        self.assertEqual(
            [697, 246, 214, 283, 246, 608, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "2b71a32f0a209286a10ca1e770882e487479dcfdde5737587dee4954fe55bd94",
                "3472b6ca5145616987527880780a6debd998414b3554cf85a6c43c1431ae3e5d",
                "e8c916c5260c27787c8ac9da1ce9b0f4eebe2972360ea6779f050721a2bd5c75",
                "c8d8f21a9a60dfe588db5a8157791781715b8293758a6d730ee38ad1dc3f65c6",
                "99a9f2e244e3083030ebd9b64a89be758208f1380787c0824236c4a83244518a",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_951, measurement["sum_component_tokens"])
        self.assertEqual(2_950, measurement["total_tokens"])
        self.assertEqual(2_957, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertEqual(
            EVAL.PHASE3_CONTEXT_TARGETS["task"] + 1,
            EVAL._component_upper_bound(components) + 44,
        )

    def test_c1l_data_api_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-api-contract-changer",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "model-boundary-mapping",
            "sdk-library-contract-design",
            "api-contract-design",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            (
                "b6f4ecd27fed13f1d570970b4a316d3a0c7c6128add25328b983318eafbe4f5b",
                ["accepted-brief", "input-shape-change"],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        selected_owners = {"data-api-contract-changer", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        expected_selected_union = [
            ["data-api-contract-changer", "references/checklist.md"],
            ["data-api-contract-changer", "references/evidence-patterns.md"],
            ["data-api-contract-changer", "references/solution-optimality.md"],
            ["api-contract-design", "references/api-style-and-semantics.md"],
            ["api-contract-design", "references/checklist.md"],
            ["api-contract-design", "references/evidence-patterns.md"],
            ["model-boundary-mapping", "references/benchmarks-and-patterns.md"],
            ["model-boundary-mapping", "references/checklist.md"],
            ["model-boundary-mapping", "references/evidence-patterns.md"],
            ["sdk-library-contract-design", "references/benchmarks-and-patterns.md"],
            ["sdk-library-contract-design", "references/checklist.md"],
            ["sdk-library-contract-design", "references/evidence-patterns.md"],
        ]
        self.assertEqual(
            [tuple(reference) for reference in expected_selected_union],
            selected_references,
        )
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1L data-api named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [12, 12, 12, 12],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual(
            staged["required_output_receipts"],
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "sdk-library-contract-design",
            "references/benchmarks-and-patterns.md",
        ]
        active_stage = staged["stages"][9]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["option-comparison", "selected-approach"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/data-api-contract-changer/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "data-api-contract-changer",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 300, 209, 198, 209, 536, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "f0779c57fb4c72eb1294eb7a4119070a16cab83b008dc25fa89420e7565d4211",
                "61061c8452d14599f435da37cf8c81d45a8d72ae437b30bc3a297f216f179263",
                "1c4dfac80199dd1aa80147237375786cefa9886621c10a7607d60bd0cbdc9d2a",
                "4bf5229519d767637f267538dad8e89249aa3620473267d7da1b2fcee143dcbb",
                "70e2a6d903a1d125c5f893206b670fb1578ba43031b11a7f67e84f9683f259a2",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_806, measurement["sum_component_tokens"])
        self.assertEqual(2_805, measurement["total_tokens"])
        self.assertEqual(2_812, EVAL._component_upper_bound(components))
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        self.assertEqual(3_001, EVAL._component_upper_bound(components) + 189)
        self.assertNotEqual(components, components[:-1])


    def test_c1m_security_cloud_tenant_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="security-privacy-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "permission-boundary-modeling",
            "tenant-isolation",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            (
                "ff438335ba459e33cfccf8dd2a9a3903ad3094ebef55562d5467d3e855e6d3b8",
                [
                    "cloud control plane",
                    "account authority",
                    "changed-surface",
                    "tenant-isolation",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual(
            ["cloud-platform-extension"],
            [owner for owner in expected_layer3 if owner in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[
                "cloud control plane",
                "account authority",
                "changed-surface",
            ],
        )
        self.assertEqual(
            ["cloud-platform-extension"],
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        selected_owners = {"security-privacy-gate", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        expected_selected_input = [
            ["security-privacy-gate", "references/checklist.md"],
            ["security-privacy-gate", "references/evidence-patterns.md"],
            ["security-privacy-gate", "references/security-output-and-gates.md"],
            ["permission-boundary-modeling", "references/benchmarks-and-patterns.md"],
            ["permission-boundary-modeling", "references/checklist.md"],
            ["permission-boundary-modeling", "references/evidence-patterns.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["tenant-isolation", "references/data-storage-cache-and-search-isolation.md"],
            ["tenant-isolation", "references/async-queue-and-execution-context-isolation.md"],
            ["tenant-isolation", "references/operations-telemetry-and-lifecycle-isolation.md"],
        ]
        self.assertEqual(
            [tuple(reference) for reference in expected_selected_input],
            selected_references,
        )
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1M security cloud tenant named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_input, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_input},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [14, 14, 14, 14],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("permission-boundary-modeling", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("permission-boundary-modeling", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("permission-boundary-modeling", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("security-privacy-gate", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("security-privacy-gate", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("security-privacy-gate", "references/security-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("tenant-isolation", "references/async-queue-and-execution-context-isolation.md"): ["boundary-decision", "validation-plan", "proof-limit"],
            ("tenant-isolation", "references/data-storage-cache-and-search-isolation.md"): ["boundary-decision", "validation-plan", "residual-risk"],
            ("tenant-isolation", "references/operations-telemetry-and-lifecycle-isolation.md"): ["boundary-decision", "validation-plan", "residual-risk"],
        }
        expected_output_receipts = [
            {
                "reference": reference,
                "required_outputs": expected_outputs[tuple(reference)],
            }
            for reference in expected_loaded_union
        ]
        self.assertEqual(expected_output_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_output_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "permission-boundary-modeling",
            "references/evidence-patterns.md",
        ]
        active_stage = staged["stages"][7]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["evidence-record", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_input, expected_selected_input[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if selector is not None:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                ])
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/security-privacy-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "security-privacy-gate",
            ),
            compact_source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3[1:]
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/permission-boundary-modeling/references/evidence-patterns.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 303, 250, 233, 217, 635, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "1f5f5d81f6dd59c74a1a43ed9e7710478b16a0657eaa5312fe623ee598fb300e",
                "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2",
                "b2e0f2942ce44f05e6e9df79b84ec2143d50cf2fdf774080a7426421dacbcd5d",
                "8ca8f4143c96cda353931bdead1f2fbdaaa3837b27497e9111bc2caf669bee81",
                "f876b57f88901fa11afcbbf60a549a0af4ca884a4b05df338534b85b49346d38",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_992, measurement["sum_component_tokens"])
        self.assertEqual(2_991, measurement["total_tokens"])
        self.assertEqual(2_998, EVAL._component_upper_bound(components))
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        self.assertEqual(3_001, EVAL._component_upper_bound(components) + 3)
        self.assertNotEqual(components, components[:-1])

    def test_c1n_quality_client_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="quality-test-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "test-data-management",
            "client-application-testing",
            "test-strategy",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            (
                "561a404c9f71b49fc1c15e727f8fe21e426622ed9224df71d0d21056513da9b4",
                [
                    "explicit-test-data-decision",
                    "changed installed-client behavior needs lifecycle os integration installation device configuration or accessibility proof",
                    "analysis-action",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual([], [owner for owner in expected_layer3 if owner in domain_names])
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=["explicit-test-data-decision", "analysis-action"],
        )
        self.assertNotIn("client-application-testing", negative_receipt["selected_layer3"])
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        expected_union = [
            ["client-application-testing", "references/client-test-matrix.md"],
            ["quality-test-gate", "references/checklist.md"],
            ["quality-test-gate", "references/test-output-and-gates.md"],
            ["quality-test-gate", "references/test-structure-boundaries.md"],
            ["test-data-management", "references/benchmarks-and-patterns.md"],
            ["test-data-management", "references/checklist.md"],
            ["test-data-management", "references/evidence-patterns.md"],
            ["test-strategy", "references/benchmarks-and-patterns.md"],
            ["test-strategy", "references/checklist.md"],
            ["test-strategy", "references/evidence-patterns.md"],
        ]
        projection_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"] in {"quality-test-gate", *expected_layer3}
        ]
        self.assertEqual(
            {tuple(reference) for reference in expected_union},
            {tuple(reference) for reference in projection_references},
        )
        self.assertEqual(10, len(projection_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1N quality client named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in expected_union],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_union, staged["selected_union"])
        self.assertEqual(expected_union, staged["loaded_union"])
        self.assertEqual(
            [10, 10, 10, 10],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("client-application-testing", "references/client-test-matrix.md"): ["validation-plan", "residual-risk"],
            ("quality-test-gate", "references/checklist.md"): ["checklist-result", "validation-plan"],
            ("quality-test-gate", "references/test-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("quality-test-gate", "references/test-structure-boundaries.md"): ["validation-plan", "proof-limit"],
            ("test-data-management", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("test-data-management", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("test-data-management", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("test-strategy", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("test-strategy", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("test-strategy", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        expected_receipts = [
            {"reference": reference, "required_outputs": expected_outputs[tuple(reference)]}
            for reference in expected_union
        ]
        self.assertEqual(expected_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        self.assertEqual(expected_union[0:1], staged["stages"][0]["loaded_references"])
        self.assertEqual(expected_receipts[0:1], staged["stages"][0]["required_output_receipts"])
        self.assertNotEqual(expected_union, expected_union[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                ])
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/quality-test-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "quality-test-gate",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/test-data-management/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/client-application-testing/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/test-strategy/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 332, 257, 215, 232, 592, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "8bea21744146360fc9d8a946c724f174b71723a28ce5960c1ff872b0e621f6dd",
                "535ce74d430ee2cf20f237d416d8f0ec8b8f2c498cc7b262d2ab16624af16e65",
                "6a82967cb4e768321dca47421353b4a3ced565841444e760fe1c6078da9558ae",
                "eb3ff8d61501d0a450aa9f72d60f5f96248791b06fb3b0cae7a57792d6780750",
                "02edd179aae452bb8d1c4663bc73fa8f7bff2b980def64c4c51ad086c18a7777",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_982, measurement["sum_component_tokens"])
        self.assertEqual(2_981, measurement["total_tokens"])
        self.assertEqual(2_988, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertEqual(3_001, EVAL._component_upper_bound(components) + 13)
        self.assertNotEqual(components, components[:-1])


    def test_c1o_platform_infrastructure_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="platform-infrastructure-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "configuration-runtime-policy",
            "powershell-professional-usage",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self.assertEqual(
            (
                "274ab034c0a7efd4d2986963b7774d8ac909c445b89f5c19e0e306a97fdfcdd4",
                [
                    "cloud control plane",
                    "account authority",
                    "changed-surface",
                    "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability",
                    "powershell pipeline binding errors native exit arguments encoding remoting credentials providers modules or administrative idempotency",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual(
            ["cloud-platform-extension"],
            [owner for owner in expected_layer3 if owner in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[
                "cloud control plane",
                "account authority",
                "changed-surface",
                "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability",
            ],
        )
        self.assertNotIn(
            "powershell-professional-usage",
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        for path, expected_sha256 in {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": "4d43548f48103571f863dc798d5023ae7ad18bd9a674cc74ec14557ee7a74d0a",
            "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": "ac76ff616b46e89bc3fbe32c02bb270161ae132d97162b38ba36866ae2148b29",
            "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md": "ab30d62d5e947340effe9918dd49546f2e69c47806b049c4f125673260833c8e",
            "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md": "97ce7438c774d56a64d46fd241c3d6876b97929b8294f43897818185ba812cd4",
        }.items():
            with self.subTest(source_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                )

        expected_selected_input = [
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
            ["powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"],
            ["powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"platform-infrastructure-change-builder", *expected_layer3}
        ]
        self.assertEqual(expected_selected_input, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1O platform infrastructure named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
            ["powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"],
            ["powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_input, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_input},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [12, 12, 12, 12],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("configuration-runtime-policy", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("configuration-runtime-policy", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("platform-infrastructure-change-builder", "references/iac-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
            ("platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
            ("powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"): ["decision-record", "residual-risk"],
            ("powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"): ["selected-approach", "proof-limit", "residual-risk"],
        }
        expected_receipts = [
            {
                "reference": reference,
                "required_outputs": expected_outputs[tuple(reference)],
            }
            for reference in expected_loaded_union
        ]
        self.assertEqual(expected_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "powershell-professional-usage",
            "references/remoting-provider-and-administration-contracts.md",
        ]
        active_stage = staged["stages"][11]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["selected-approach", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_input, expected_selected_input[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                ])
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/platform-infrastructure-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "platform-infrastructure-change-builder",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/configuration-runtime-policy/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/powershell-professional-usage/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 229, 250, 183, 197, 722, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "edf20265275b1afa37ecd528904f486436cfa88cd04b6ecacb773a0ed8105958",
                "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2",
                "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237",
                "8f5d6f6f82a18be75f0eca521865139c604e2e41cc73858b535285f026b5f094",
                "97ce7438c774d56a64d46fd241c3d6876b97929b8294f43897818185ba812cd4",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_935, measurement["sum_component_tokens"])
        self.assertEqual(2_934, measurement["total_tokens"])
        self.assertEqual(2_941, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        self.assertEqual(3_001, EVAL._component_upper_bound(components) + 60)
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1p_platform_iac_safety_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="platform-infrastructure-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "configuration-runtime-policy",
            "infrastructure-as-code-safety",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = [
            "cloud control plane",
            "account authority",
            "changed-surface",
            "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability",
            "desired-state infrastructure source with state identity drift destruction or recovery",
        ]
        self.assertEqual(
            (
                "434c91b6b2caf2b3b78ff6ffbfd86491a1d834746060092e516142467fcb6953",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual(
            ["cloud-platform-extension"],
            [owner for owner in expected_layer3 if owner in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=expected_signals[:-1],
        )
        self.assertNotIn(
            "infrastructure-as-code-safety",
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        protected_sources = {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": "4d43548f48103571f863dc798d5023ae7ad18bd9a674cc74ec14557ee7a74d0a",
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": "a0c6c4b122e76426256bc5deac35b741b32a406255992ac4c958ff10cfb2f9c6",
            "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md": "30c8a48b94f411059bb8e17e1670d1b5ca79db1c27b06394d5818f14de10c21c",
            "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md": "8cf0a2d5b85a83cd517a937059b28b243c2718e7da90dad405fd33a474e44b1f",
            "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md": "d1d0bbf5306aaa75e25a9ed6a08d0d7c5b0066b75dd091cb276b63da58892bc6",
        }
        for path, expected_sha256 in protected_sources.items():
            self.assertEqual(
                expected_sha256,
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            )

        expected_selected_input = [
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
            ["infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"],
            ["infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"platform-infrastructure-change-builder", *expected_layer3}
        ]
        self.assertEqual(expected_selected_input, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1P platform IaC safety named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
            ["infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"],
            ["infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"],
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_input, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_input},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [12, 12, 12, 12],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("configuration-runtime-policy", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("configuration-runtime-policy", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"): ["decision-record", "proof-limit", "residual-risk"],
            ("infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"): ["decision-record", "proof-limit", "residual-risk"],
            ("platform-infrastructure-change-builder", "references/iac-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
            ("platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
        }
        expected_receipts = [
            {
                "reference": reference,
                "required_outputs": expected_outputs[tuple(reference)],
            }
            for reference in expected_loaded_union
        ]
        self.assertEqual(expected_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "infrastructure-as-code-safety",
            "references/identity-destruction-and-recovery-contracts.md",
        ]
        active_stage = staged["stages"][8]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["decision-record", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_input, expected_selected_input[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                ])
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/platform-infrastructure-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "platform-infrastructure-change-builder",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/configuration-runtime-policy/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 229, 250, 183, 165, 812, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "edf20265275b1afa37ecd528904f486436cfa88cd04b6ecacb773a0ed8105958",
                "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2",
                "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237",
                "a0a06ad825967e548dc5eb817ce003a24519aa99a4c2262cc0bcbc0830a97b76",
                "8cf0a2d5b85a83cd517a937059b28b243c2718e7da90dad405fd33a474e44b1f",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_993, measurement["sum_component_tokens"])
        self.assertEqual(2_992, measurement["total_tokens"])
        self.assertEqual(2_999, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        negative = copy.deepcopy(components)
        negative[5]["tokens"] = 814
        self.assertEqual(3_001, EVAL._component_upper_bound(negative))
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1q_data_middleware_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "data-migration-design",
            "transaction-consistency",
            "distributed-workflow-consistency",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = ["database-migration", "distributed-effect-change"]
        self.assertEqual(
            (
                "6267555050601288125c263945346b3abdd3f22a54cb2a6337e3de44053e1298",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_names = {
            row["name"]
            for row in EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual([], [name for name in expected_layer3 if name in domain_names])
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection, evidence_signals=expected_signals[:-1]
        )
        self.assertNotIn("distributed-workflow-consistency", negative_receipt["selected_layer3"])
        self.assertNotEqual(selected["receipt"]["receipt_sha256"], negative_receipt["receipt_sha256"])

        protected = {
            "src/professional-skills/data-middleware-change-builder/SKILL.md": "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1",
            "src/foundation/capabilities/data-migration-design/SKILL.md": "8b3651ba9b7a7a97203fe2dee1806a74a34f74e2250c573e9cd786b0932cc8fa",
            "src/foundation/capabilities/transaction-consistency/SKILL.md": "076dff13a9468d13713ec106f5a96586f44635855f9600998209d197a8fb5308",
            "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md": "df3a7d24a62d3aabc74405abeb7ce98376da7a049c3ec8b36c43c25694a98b2e",
            "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md": "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        expected_selected = [
            ["data-middleware-change-builder", "references/checklist.md"],
            ["data-middleware-change-builder", "references/evidence-patterns.md"],
            ["data-middleware-change-builder", "references/recovery-patterns.md"],
            ["data-migration-design", "references/benchmarks-and-patterns.md"],
            ["data-migration-design", "references/checklist.md"],
            ["data-migration-design", "references/evidence-patterns.md"],
            ["transaction-consistency", "references/benchmarks-and-patterns.md"],
            ["transaction-consistency", "references/checklist.md"],
            ["transaction-consistency", "references/evidence-patterns.md"],
            ["distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"],
            ["distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"],
            ["distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"] in {"data-middleware-change-builder", *expected_layer3}
        ]
        self.assertEqual(expected_selected, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1Q data middleware named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded = [
            ["data-middleware-change-builder", "references/checklist.md"],
            ["data-middleware-change-builder", "references/evidence-patterns.md"],
            ["data-middleware-change-builder", "references/recovery-patterns.md"],
            ["data-migration-design", "references/benchmarks-and-patterns.md"],
            ["data-migration-design", "references/checklist.md"],
            ["data-migration-design", "references/evidence-patterns.md"],
            ["distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"],
            ["distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"],
            ["distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"],
            ["transaction-consistency", "references/benchmarks-and-patterns.md"],
            ["transaction-consistency", "references/checklist.md"],
            ["transaction-consistency", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual({tuple(x) for x in expected_selected}, {tuple(x) for x in expected_loaded})
        self.assertEqual([12, 12, 12, 12], [len(staged[key]) for key in ("selected_union", "loaded_union", "stages", "required_output_receipts")])
        self.assertEqual(expected_loaded, [stage["loaded_references"][0] for stage in staged["stages"]])
        self.assertTrue(all(len(stage["loaded_references"]) == 1 and stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        outputs = {
            ("data-middleware-change-builder", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("data-middleware-change-builder", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("data-middleware-change-builder", "references/recovery-patterns.md"): ["option-comparison", "selected-approach"],
            ("data-migration-design", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("data-migration-design", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("data-migration-design", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"): ["failure-decision", "selected-approach", "residual-risk"],
            ("distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"): ["boundary-decision", "failure-decision", "proof-limit"],
            ("distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"): ["failure-decision", "validation-plan", "proof-limit"],
            ("transaction-consistency", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("transaction-consistency", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("transaction-consistency", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        receipts = [{"reference": reference, "required_outputs": outputs[tuple(reference)]} for reference in expected_loaded]
        self.assertEqual(receipts, staged["required_output_receipts"])
        self.assertEqual(receipts, [stage["required_output_receipts"][0] for stage in staged["stages"]])
        active = ["data-migration-design", "references/evidence-patterns.md"]
        self.assertEqual(
            ([active], [], [{"reference": active, "required_outputs": ["evidence-record", "proof-limit", "residual-risk"]}]),
            (staged["stages"][5]["loaded_references"], staged["stages"][5]["carried_predecessors"], staged["stages"][5]["required_output_receipts"]),
        )
        self.assertNotEqual(expected_selected, expected_selected[:-1])
        self.assertNotEqual(expected_loaded, expected_loaded[:-1])

        def source_component(kind: str, path: Path, headings: tuple[str, ...], selector: str | None, *, layer3_delivery: bool = False) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend(["", "## Layer 3 Delivery", "", "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled."])
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component("worker_profile", ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md"),
            source_component("primary_skill", ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md", BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "data-middleware-change-builder", layer3_delivery=True),
            source_component("layer3", ROOT / "src/foundation/capabilities/data-migration-design/SKILL.md", BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None),
            source_component("layer3", ROOT / "src/foundation/capabilities/transaction-consistency/SKILL.md", BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None),
            source_component("layer3", ROOT / "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md", BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None),
            EVAL._file_component("layer3_reference", ROOT / "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md"),
            capsule,
        ]
        self.assertEqual([697, 269, 230, 283, 246, 611, 657], [item["tokens"] for item in components])
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "22a41125147da43b01da304168205b8840d7ec6649a16c7727bd7719943696f3",
                "f93f83da98b02b86460d186c6b3cb2187caa25234eaf64f2343799ee8bde7483",
                "e8c916c5260c27787c8ac9da1ce9b0f4eebe2972360ea6779f050721a2bd5c75",
                "c8d8f21a9a60dfe588db5a8157791781715b8293758a6d730ee38ad1dc3f65c6",
                "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(components, budget_class="task", token_budget=EVAL.FROZEN_GATES["task"])
        self.assertEqual(2_993, measurement["sum_component_tokens"])
        self.assertEqual(2_992, measurement["total_tokens"])
        self.assertEqual(2_999, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        negative = copy.deepcopy(components)
        negative[5]["tokens"] = 613
        self.assertEqual(3_001, EVAL._component_upper_bound(negative))
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1r_delivery_release_iot_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="delivery-release-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "iot-embedded-extension",
            "release-rollback",
            "version-compatibility",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = [
            "device",
            "recovery",
            "changed-surface",
            "production-apply-or-rollout",
        ]
        self.assertEqual(
            (
                "0a93ab092e22e6ce4b18a629db71817e23222ed5d89397c5be7434e10a85047a",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_names = {
            row["name"]
            for row in EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual(
            ["iot-embedded-extension"],
            [name for name in expected_layer3 if name in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection, evidence_signals=expected_signals[1:]
        )
        self.assertNotIn(
            "iot-embedded-extension", negative_receipt["selected_layer3"]
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        protected = {
            "src/professional-skills/delivery-release-gate/SKILL.md": "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda",
            "src/domain-extensions/iot-embedded-extension/SKILL.md": "b36832cb68c5d2611c1c055e9b9efa9eeac6ecd5dd34f5f6e4062180045c38d4",
            "src/foundation/capabilities/release-rollback/SKILL.md": "738e04c280576f5392d91f822c605e2eed1916444aef7bf99b0aae48e2f4d453",
            "src/foundation/capabilities/version-compatibility/SKILL.md": "008bb557182e152938008b0f5e7175f5c2fb32eb44b9a7352b2a28e7591cfd75",
            "src/domain-extensions/iot-embedded-extension/references/checklist.md": "771c35d891ee7662d60144c0bab45f6e6956007060d3ab6a97e69aef6051552e",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(
                expected_sha256,
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            )

        expected_selected = [
            ["delivery-release-gate", "references/checklist.md"],
            ["delivery-release-gate", "references/delivery-output-and-gates.md"],
            ["delivery-release-gate", "references/release-evidence-patterns.md"],
            ["release-rollback", "references/benchmarks-and-patterns.md"],
            ["release-rollback", "references/checklist.md"],
            ["release-rollback", "references/evidence-patterns.md"],
            ["version-compatibility", "references/checklist.md"],
            ["version-compatibility", "references/compatibility-benchmarks.md"],
            ["version-compatibility", "references/evidence-patterns.md"],
            ["iot-embedded-extension", "references/checklist.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"delivery-release-gate", *expected_layer3}
        ]
        self.assertEqual(expected_selected, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1R delivery release IoT named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded = [
            ["delivery-release-gate", "references/checklist.md"],
            ["delivery-release-gate", "references/delivery-output-and-gates.md"],
            ["delivery-release-gate", "references/release-evidence-patterns.md"],
            ["iot-embedded-extension", "references/checklist.md"],
            ["release-rollback", "references/benchmarks-and-patterns.md"],
            ["release-rollback", "references/checklist.md"],
            ["release-rollback", "references/evidence-patterns.md"],
            ["version-compatibility", "references/checklist.md"],
            ["version-compatibility", "references/compatibility-benchmarks.md"],
            ["version-compatibility", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected},
            {tuple(reference) for reference in expected_loaded},
        )
        self.assertEqual(
            [10, 10, 10, 10],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        outputs = {
            ("delivery-release-gate", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("delivery-release-gate", "references/delivery-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("delivery-release-gate", "references/release-evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("iot-embedded-extension", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("release-rollback", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("release-rollback", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("release-rollback", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("version-compatibility", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("version-compatibility", "references/compatibility-benchmarks.md"): ["option-comparison", "selected-approach"],
            ("version-compatibility", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        receipts = [
            {"reference": reference, "required_outputs": outputs[tuple(reference)]}
            for reference in expected_loaded
        ]
        self.assertEqual(receipts, staged["required_output_receipts"])
        self.assertEqual(
            receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active = ["iot-embedded-extension", "references/checklist.md"]
        self.assertEqual(
            (
                [active],
                [],
                [{
                    "reference": active,
                    "required_outputs": ["checklist-result", "residual-risk"],
                }],
            ),
            (
                staged["stages"][3]["loaded_references"],
                staged["stages"][3]["carried_predecessors"],
                staged["stages"][3]["required_output_receipts"],
            ),
        )
        self.assertNotEqual(expected_selected, expected_selected[:-1])
        self.assertNotEqual(expected_loaded, expected_loaded[:-1])

        owner_roots = {
            "delivery-release-gate": ROOT / "src/professional-skills/delivery-release-gate",
            "iot-embedded-extension": ROOT / "src/domain-extensions/iot-embedded-extension",
            "release-rollback": ROOT / "src/foundation/capabilities/release-rollback",
            "version-compatibility": ROOT / "src/foundation/capabilities/version-compatibility",
        }
        reference_components = [
            EVAL._file_component(
                "layer3_reference", owner_roots[owner] / relative_path
            )
            for owner, relative_path in [tuple(reference) for reference in expected_selected]
        ]
        self.assertEqual(10, len(reference_components))
        self.assertTrue(all(item["tokens"] <= 482 for item in reference_components))
        self.assertEqual(482, max(item["tokens"] for item in reference_components))

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                ])
            output.append("")
            return EVAL._component(
                kind, path.relative_to(ROOT).as_posix(), "\n".join(output)
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/delivery-release-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "delivery-release-gate",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/iot-embedded-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/release-rollback/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/version-compatibility/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/domain-extensions/iot-embedded-extension/references/checklist.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 333, 338, 229, 250, 482, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "cd91f6ea858e7b988fe1268c0e45d8f3cf38e501ff0a1cbb8d31a6ec0bcb4565",
                "94a3e7d66eebc7a8c5c154df3405449473ea05b75b4d072f6828cbca8d197923",
                "3e2150a21b3997726207b6ac9317c8077856708c87a481ac818898779c78229a",
                "989a93e84c8ba897bdc8ba69113da520c11207996f1d64b7ad59b4810284ae91",
                "771c35d891ee7662d60144c0bab45f6e6956007060d3ab6a97e69aef6051552e",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_986, measurement["sum_component_tokens"])
        self.assertEqual(2_985, measurement["total_tokens"])
        self.assertEqual(2_992, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        negative = copy.deepcopy(components)
        negative[5]["tokens"] = 491
        self.assertEqual(3_001, EVAL._component_upper_bound(negative))
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1s_security_web_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="security-privacy-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "threat-modeling",
            "web-security",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = [
            "cloud control plane",
            "account authority",
            "changed-surface",
            "ssrf",
        ]
        self.assertEqual(
            (
                "336dfef51f64a686fc616f4fc48cac5451ebd55fe61dee5e402d4e98ca5a90e4",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_names = {
            row["name"]
            for row in EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual(
            ["cloud-platform-extension"],
            [name for name in expected_layer3 if name in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection, evidence_signals=expected_signals[:-1]
        )
        self.assertEqual(
            ["cloud-platform-extension"], negative_receipt["selected_layer3"]
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        protected = {
            "src/professional-skills/security-privacy-gate/SKILL.md": "f11d7bdde385a27584a4b22e07cd389adc4c59d8933597433238c4ecc5ba7ae5",
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/foundation/capabilities/threat-modeling/SKILL.md": "90d1b45cc6cab690eb2861c3ec896cc742466223468a41aafd8b84674db7271d",
            "src/foundation/capabilities/web-security/SKILL.md": "4d9a6d9e61de16b63b62b4c5e19ff8857cc96f5661b32f4540aaa7f07960a191",
            "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md": "ba0d3b7172e4fce659dfce92653dfcbd628295d4714ab0b6b81a38e6bd2ab763",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(
                expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            )

        expected_selected = [
            ["security-privacy-gate", "references/checklist.md"],
            ["security-privacy-gate", "references/evidence-patterns.md"],
            ["security-privacy-gate", "references/security-output-and-gates.md"],
            ["threat-modeling", "references/benchmarks-and-patterns.md"],
            ["threat-modeling", "references/checklist.md"],
            ["threat-modeling", "references/evidence-patterns.md"],
            ["web-security", "references/benchmarks-and-patterns.md"],
            ["web-security", "references/checklist.md"],
            ["web-security", "references/evidence-patterns.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"security-privacy-gate", *expected_layer3}
        ]
        self.assertEqual(expected_selected, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1S security web named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded = [
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["security-privacy-gate", "references/checklist.md"],
            ["security-privacy-gate", "references/evidence-patterns.md"],
            ["security-privacy-gate", "references/security-output-and-gates.md"],
            ["threat-modeling", "references/benchmarks-and-patterns.md"],
            ["threat-modeling", "references/checklist.md"],
            ["threat-modeling", "references/evidence-patterns.md"],
            ["web-security", "references/benchmarks-and-patterns.md"],
            ["web-security", "references/checklist.md"],
            ["web-security", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual(
            {tuple(item) for item in expected_selected},
            {tuple(item) for item in expected_loaded},
        )
        self.assertEqual(
            [14, 14, 14, 14],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("security-privacy-gate", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("security-privacy-gate", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("security-privacy-gate", "references/security-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("threat-modeling", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("threat-modeling", "references/checklist.md"): ["checklist-result", "validation-plan"],
            ("threat-modeling", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("web-security", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("web-security", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("web-security", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        receipts = [
            {"reference": reference, "required_outputs": outputs[tuple(reference)]}
            for reference in expected_loaded
        ]
        self.assertEqual(receipts, staged["required_output_receipts"])
        self.assertEqual(
            receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active = ["web-security", "references/benchmarks-and-patterns.md"]
        self.assertEqual(
            (
                [active],
                [],
                [{
                    "reference": active,
                    "required_outputs": ["option-comparison", "selected-approach"],
                }],
            ),
            (
                staged["stages"][11]["loaded_references"],
                staged["stages"][11]["carried_predecessors"],
                staged["stages"][11]["required_output_receipts"],
            ),
        )
        self.assertNotEqual(expected_selected, expected_selected[:-1])
        self.assertNotEqual(expected_loaded, expected_loaded[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                ])
            output.append("")
            return EVAL._component(
                kind, path.relative_to(ROOT).as_posix(), "\n".join(output)
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/security-privacy-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "security-privacy-gate",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/threat-modeling/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/web-security/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
            ),
            capsule,
        ]
        self.assertEqual(
            [697, 303, 250, 311, 234, 532, 657],
            [item["tokens"] for item in components],
        )
        self.assertEqual(
            [
                "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
                "1f5f5d81f6dd59c74a1a43ed9e7710478b16a0657eaa5312fe623ee598fb300e",
                "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2",
                "559d0467c675e0e77803979cb8f132d547567d236c0dad97efe2a030c6a8225a",
                "ae1207804645b3af4968e354358fcc27b10aa76f9f20fabe31388494d3bf17f1",
                "ba0d3b7172e4fce659dfce92653dfcbd628295d4714ab0b6b81a38e6bd2ab763",
                "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
            ],
            [item["sha256"] for item in components],
        )
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
            token_budget=EVAL.FROZEN_GATES["task"],
        )
        self.assertEqual(2_984, measurement["sum_component_tokens"])
        self.assertEqual(2_983, measurement["total_tokens"])
        self.assertEqual(2_990, EVAL._component_upper_bound(components))
        self.assertTrue(measurement["within_token_budget"])
        self.assertLessEqual(EVAL._component_upper_bound(components), 3_000)
        negative = copy.deepcopy(components)
        negative[5]["tokens"] = 543
        self.assertEqual(3_001, EVAL._component_upper_bound(negative))
        self.assertNotEqual(components, components[:-1])


if __name__ == "__main__":
    unittest.main()
