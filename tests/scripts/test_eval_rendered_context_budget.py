from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
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
            (enforcement, original_text.replace("prompt-enforced", "host-enforced", 1))
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
                "payment-trading-extension/references/checklist.md",
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
                "payment-trading-extension/references/checklist.md",
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

        rows = (
            ("recommended", "engineering-change-analysis", "test-strategy", "references/checklist.md", "compiled"),
            ("full", "engineering-change-analysis", "test-strategy", "references/checklist.md", "compiled"),
            ("dev", "engineering-change-analysis", "test-strategy", "references/checklist.md", "top-level"),
            ("recommended", "engineering-change-analysis", "payment-trading-extension", "references/checklist.md", "compiled"),
            ("full", "engineering-change-analysis", "payment-trading-extension", "references/checklist.md", "top-level"),
            ("dev", "engineering-change-analysis", "payment-trading-extension", "references/checklist.md", "top-level"),
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

        domain_id = "bigdata-product-extension/references/checklist.md"
        recommended_domain = EVAL._layer3_reference_path(
            "recommended",
            "data-middleware-change-builder",
            domain_id,
            manifests["recommended"],
        )
        full_domain = EVAL._layer3_reference_path(
            "full",
            "data-middleware-change-builder",
            domain_id,
            manifests["full"],
        )
        dev_domain = EVAL._layer3_reference_path(
            "dev",
            "data-middleware-change-builder",
            domain_id,
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
                        "/payment-trading-extension/references/checklist.md"
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


if __name__ == "__main__":
    unittest.main()
