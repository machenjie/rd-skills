from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval-agent-lightweight.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "eval_agent_lightweight_utility_tests",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL = _load_module()
CANONICAL_LEDGER_FIELDS = (
    "Claim",
    "Owner",
    "Artifact",
    "Command",
    "Result",
    "Freshness",
    "Scope",
    "Proof Limit",
    "State",
)
RETIRED_LEDGER_FIELDS = (
    "Evidence ID",
    "Task ID",
    "Action",
    "Freshness Marker",
    "Evidence State",
    "Supersedes",
)
LEGACY_NEGATIVE_TAG = "legacy-negative"


class LightweightUtilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        document = EVAL._load_json(EVAL.FIXTURES)
        cls.document = document
        cls.release_cases = document["cases"]
        cls.scheduling_cases = document["scheduling_cases"]
        cls.utility_cases = document["utility_cases"]
        cls.adaptive_testing_cases = document["adaptive_testing_cases"]
        cls.review_discipline_cases = document["review_discipline_cases"]
        cls.task_focus_cases = document["task_focus_cases"]
        cls.completion_state_cases = document["completion_state_cases"]
        cls.external_read_cases = document["external_read_cases"]
        cls.professional, cls.layer3 = EVAL._skill_registries()

    def _errors(self, case: dict) -> list[str]:
        _metrics, errors = EVAL._metrics(
            case,
            self.professional,
            self.layer3,
            utility_case=True,
        )
        return errors

    def _trajectory_errors(self, case: dict) -> list[str]:
        _metrics, errors = EVAL._metrics(
            case,
            self.professional,
            self.layer3,
        )
        return errors

    def _trajectory_metrics(self, case: dict) -> tuple[dict, list[str]]:
        return EVAL._metrics(
            case,
            self.professional,
            self.layer3,
        )

    @staticmethod
    def _implementation_errors(case: dict) -> list[str]:
        return EVAL._implementation_discipline_errors(
            case["id"],
            case["steps"],
            case.get("implementation_oracle"),
        )

    @staticmethod
    def _rebind_authority_digest(case: dict) -> None:
        authority = case["implementation_oracle"]
        authority["canonical_sha256"] = EVAL._implementation_oracle_digest(
            authority
        )

    def _release_case(self, case_id: str) -> dict:
        return copy.deepcopy(
            next(item for item in self.release_cases if item["id"] == case_id)
        )

    def test_required_behavior_coverage_manifest_is_exact_and_machine_checked(
        self,
    ) -> None:
        results, errors = EVAL._required_behavior_coverage_results(
            copy.deepcopy(self.document),
            self.professional,
            self.layer3,
        )
        self.assertEqual([], errors)
        self.assertEqual(17, len(results))
        grouped = {
            group: [item for item in results if item["group"] == group]
            for group in EVAL.REQUIRED_BEHAVIOR_GROUPS
        }
        self.assertEqual(
            {
                "ai-reading-ownership": 5,
                "adaptive-testing": 6,
                "engineering-closure": 6,
            },
            {group: len(items) for group, items in grouped.items()},
        )
        self.assertTrue(
            all(
                item["status"] == "covered"
                and item["positive_valid"]
                and item["full_path_valid"]
                and item["mutation_applied"]
                and item["bypass_rejected"]
                for item in results
            )
        )
        self.assertEqual(
            EVAL.REQUIRED_BEHAVIOR_DIMENSIONS,
            {
                dimension
                for group in self.document["required_behavior_coverage"]["groups"]
                for entry in group["entries"]
                for dimension in entry["dimensions"]
            },
        )

    def test_remaining_twelve_behaviors_use_full_path_machine_mutations(self) -> None:
        results, errors = EVAL._required_behavior_coverage_results(
            copy.deepcopy(self.document),
            self.professional,
            self.layer3,
        )
        self.assertEqual([], errors)
        remaining = [
            item for item in results if item["group"] != "ai-reading-ownership"
        ]
        self.assertEqual(12, len(remaining))
        self.assertTrue(
            all(
                item["status"] == "covered"
                and item["full_path_valid"]
                and item["mutation_applied"]
                and item["bypass_rejected"]
                for item in remaining
            )
        )

    def test_required_behavior_manifest_equals_immutable_per_id_oracle(self) -> None:
        manifest_entries = {
            entry["id"]: entry
            for group in self.document["required_behavior_coverage"]["groups"]
            for entry in group["entries"]
        }
        self.assertEqual(
            set(EVAL.REQUIRED_BEHAVIOR_CONTRACTS), set(manifest_entries)
        )
        for behavior_id, contract in EVAL.REQUIRED_BEHAVIOR_CONTRACTS.items():
            with self.subTest(behavior=behavior_id):
                self.assertEqual(
                    EVAL._required_behavior_manifest_entry(behavior_id, contract),
                    manifest_entries[behavior_id],
                )

    def test_required_behavior_oracle_rejects_every_one_field_swap(self) -> None:
        fields = (
            "positive_case",
            "validator_family",
            "bypass_mutation",
            "expected_error",
            "dimensions",
        )
        contracts = EVAL.REQUIRED_BEHAVIOR_CONTRACTS
        for behavior_id, contract in contracts.items():
            for field in fields:
                donor = next(
                    candidate
                    for candidate in contracts.values()
                    if getattr(candidate, field) != getattr(contract, field)
                )
                with self.subTest(behavior=behavior_id, field=field):
                    document = copy.deepcopy(self.document)
                    entry = next(
                        entry
                        for group in document["required_behavior_coverage"]["groups"]
                        for entry in group["entries"]
                        if entry["id"] == behavior_id
                    )
                    if field == "positive_case":
                        entry["positive_trajectory"]["case_id"] = donor.positive_case
                    elif field == "validator_family":
                        entry["positive_trajectory"]["validator_family"] = (
                            donor.validator_family
                        )
                    elif field == "bypass_mutation":
                        entry["bypass_mutation"]["kind"] = donor.bypass_mutation
                    elif field == "expected_error":
                        entry["expected_error"]["code"] = donor.expected_error
                    else:
                        entry["dimensions"] = list(donor.dimensions)
                    _results, errors = EVAL._required_behavior_coverage_results(
                        document,
                        self.professional,
                        self.layer3,
                    )
                    self.assertTrue(
                        any("immutable contract oracle" in error for error in errors),
                        errors,
                    )

    def test_scheduling_positive_still_requires_full_implementation_discipline(
        self,
    ) -> None:
        document = copy.deepcopy(self.document)
        case = next(
            case
            for case in document["cases"]
            if case["id"] == "isolated-write-parallel-contract"
        )
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "implementation-discipline"
        ]
        results, errors = EVAL._required_behavior_coverage_results(
            document,
            self.professional,
            self.layer3,
        )
        parallel = next(
            result
            for result in results
            if result["id"] == "closure-parallel-writes-require-isolation"
        )
        self.assertFalse(parallel["full_path_valid"])
        self.assertTrue(
            any("positive full trajectory" in error for error in errors), errors
        )

    def test_required_behavior_coverage_rejects_missing_duplicate_and_unknown_ids(
        self,
    ) -> None:
        variants = {}
        missing = copy.deepcopy(self.document)
        missing["required_behavior_coverage"]["groups"][0]["entries"].pop()
        variants["missing"] = missing

        duplicate = copy.deepcopy(self.document)
        duplicate["required_behavior_coverage"]["groups"][0]["entries"].append(
            copy.deepcopy(
                duplicate["required_behavior_coverage"]["groups"][0]["entries"][0]
            )
        )
        variants["duplicate"] = duplicate

        unknown = copy.deepcopy(self.document)
        unknown["required_behavior_coverage"]["groups"][0]["entries"][0][
            "id"
        ] = "ai-reading-unknown-substitute"
        variants["unknown"] = unknown

        replaced = copy.deepcopy(self.document)
        replaced_entry = replaced["required_behavior_coverage"]["groups"][1][
            "entries"
        ][0]
        replaced_entry["bypass_mutation"] = {
            "kind": "existing-structured-negative",
            "fixture_group": "adaptive_testing_cases",
            "case_id": "adaptive-rejects-high-risk-downgrade",
        }
        variants["replaced-with-isolated-negative"] = replaced

        for label, document in variants.items():
            with self.subTest(label=label):
                _results, errors = EVAL._required_behavior_coverage_results(
                    document,
                    self.professional,
                    self.layer3,
                )
                self.assertTrue(
                    any(
                        "exact required behavior ids" in error
                        or "covered bypass mutation is invalid" in error
                        or "immutable contract oracle" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_required_behavior_coverage_rejects_keyword_only_substitution(self) -> None:
        document = copy.deepcopy(self.document)
        entry = document["required_behavior_coverage"]["groups"][0]["entries"][0]
        entry["observed_behaviors"] = [entry.pop("positive_trajectory")]
        _results, errors = EVAL._required_behavior_coverage_results(
            document,
            self.professional,
            self.layer3,
        )
        self.assertTrue(
            any("observed_behaviors" in error for error in errors),
            errors,
        )

    def test_ai_reading_bypass_mutations_fail_at_the_named_structured_guard(
        self,
    ) -> None:
        results, errors = EVAL._required_behavior_coverage_results(
            copy.deepcopy(self.document),
            self.professional,
            self.layer3,
        )
        self.assertEqual([], errors)
        ai_results = [
            item for item in results if item["group"] == "ai-reading-ownership"
        ]
        self.assertEqual(5, len(ai_results))
        for item in ai_results:
            with self.subTest(behavior=item["id"]):
                self.assertTrue(item["mutation_applied"])
                self.assertTrue(item["bypass_rejected"])
                self.assertIn(item["expected_error"], item["error_codes"])

    def test_documentation_full_path_uses_only_non_test_validation(self) -> None:
        case = self._release_case("release-rollback")
        event = self._discipline_event(case)
        guard = next(
            item
            for item in event["evidence"]
            if item["guard"] == EVAL.IMPLEMENTATION_GUARD_CODES["G"]
        )
        self.assertEqual("non-behavior", guard["change_kind"])
        self.assertEqual("non-test-validation", guard["approach"])
        records = [
            step
            for step in case["steps"]
            if step.get("action") == EVAL.ADAPTIVE_TEST_EVIDENCE_ACTION
        ]
        self.assertEqual(["non-test"], [record["evidence_kind"] for record in records])
        self.assertEqual([], self._trajectory_errors(case))

        EVAL._apply_required_behavior_bypass_mutation(
            case, "misclassify-documentation-as-behavior"
        )
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["G"],
            self._error_codes(self._trajectory_errors(case)),
        )

    def test_parallel_coverage_uses_scheduling_validator_family(self) -> None:
        manifest_entry = next(
            entry
            for group in self.document["required_behavior_coverage"]["groups"]
            for entry in group["entries"]
            if entry["id"] == "closure-parallel-writes-require-isolation"
        )
        self.assertEqual(
            "scheduling",
            manifest_entry["positive_trajectory"]["validator_family"],
        )
        case = self._release_case("isolated-write-parallel-contract")
        operational, _internal = EVAL._operational_steps(case["steps"])
        conflict, reduction = EVAL._parallel_metrics(operational)
        self.assertFalse(conflict)
        self.assertGreaterEqual(reduction, 1)

        EVAL._apply_required_behavior_bypass_mutation(
            case, "remove-parallel-workspace-isolation"
        )
        operational, _internal = EVAL._operational_steps(case["steps"])
        conflict, _reduction = EVAL._parallel_metrics(operational)
        self.assertTrue(conflict)

    def test_authoritative_dag_positive_fixtures_start_downstream_direct(
        self,
    ) -> None:
        fixtures = (
            self._release_case("isolated-write-parallel-contract"),
            copy.deepcopy(
                next(
                    item
                    for item in self.scheduling_cases
                    if item["id"] == "shared-workspace-serial-write"
                )
            ),
        )
        accepted_input = (
            "Accepted, artifact-reviewed authoritative Task DAG and downstream "
            "Task Capsule"
        )
        for case in fixtures:
            with self.subTest(case=case["id"]):
                self.assertEqual("direct", case["kind"])
                self.assertFalse(case["expected"]["requires_analysis"])
                serialized = EVAL.json.dumps(case).casefold()
                self.assertNotIn('"actor": "analysis-agent"', serialized)
                self.assertNotIn('"action": "search"', serialized)
                self.assertNotIn('"action": "first_executable_slice"', serialized)
                self.assertNotIn("analysis-handoff", serialized)
                self.assertNotIn("isolation-analysis", serialized)
                task_dispatches = [
                    step
                    for step in case["steps"]
                    if step.get("action") == "dispatch"
                    and step.get("profile") == "task-agent"
                ]
                self.assertGreaterEqual(len(task_dispatches), 2)
                for dispatch in task_dispatches:
                    capsule = dispatch["fixture_capsule"]
                    self.assertIn(accepted_input, capsule["inputs"])
                    self.assertTrue(
                        any(
                            "authoritative Task DAG" in dependency
                            or "completed" in dependency.casefold()
                            for dependency in capsule["dependencies"]
                        )
                    )

    def test_review_discipline_fixture_matrix_is_complete_and_green(self) -> None:
        results, errors = EVAL._review_discipline_fixture_results(
            self.review_discipline_cases
        )
        self.assertEqual([], errors)
        self.assertEqual(30, len(results))
        self.assertTrue(all(result["matches_expected"] for result in results))

        level_results = {
            result["level"]
            for result in results
            if result["id"].startswith("review-level-")
        }
        self.assertEqual({"L1", "L2", "L3", "L4", "L5"}, level_results)
        missing_dimensions = {
            case["mutation"]["dimension"]
            for case in self.review_discipline_cases
            if case["mutation"]["kind"] == "drop-dimension"
        }
        self.assertEqual(set(EVAL.REVIEW_BASE_DIMENSIONS), missing_dimensions)

    def test_professional_risk_matrix_accepts_complete_and_rejects_invalid_rows(
        self,
    ) -> None:
        valid = {
            "id": "professional-risks-complete",
            "level": "L3",
            "mutation": {"kind": "none"},
        }
        valid_steps = EVAL._review_fixture_steps(valid)
        event = next(
            step
            for step in valid_steps
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        self.assertEqual(
            list(EVAL.REVIEW_PROFESSIONAL_RISK_DIMENSIONS),
            [decision["dimension"] for decision in event["professional_risks"]],
        )
        self.assertEqual(
            [], EVAL._review_discipline_errors(valid["id"], valid_steps)
        )

        invalid = {
            "missing-professional-dimension": "missing professional-risk dimensions",
            "unsupported-professional-status": "unsupported professional-risk status",
            "unevidenced-not-applicable": "source-backed reason and evidence",
            "incomplete-delegation": "named registered Review Skill, scope, and reason",
            "duplicate-professional-dimension": "duplicate professional-risk dimensions",
        }
        for mutation_kind, expected in invalid.items():
            with self.subTest(mutation=mutation_kind):
                steps = EVAL._review_fixture_steps(
                    {
                        "id": f"professional-risks-{mutation_kind}",
                        "level": "L3",
                        "mutation": {"kind": mutation_kind},
                    }
                )
                errors = EVAL._review_discipline_errors(mutation_kind, steps)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_review_kind_is_derived_from_actual_material_actions(self) -> None:
        repair_steps = EVAL._review_fixture_steps(
            {
                "id": "repair-as-implementation-reproduction",
                "level": "L3",
                "mutation": {"kind": "repair-as-implementation"},
            }
        )
        repair_errors = EVAL._review_discipline_errors(
            "repair-as-implementation-reproduction", repair_steps
        )
        self.assertTrue(
            any(
                "actual material actions require repair review" in error
                for error in repair_errors
            ),
            repair_errors,
        )

        valid_repair_steps = copy.deepcopy(repair_steps)
        event = next(
            step
            for step in valid_repair_steps
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        event["review_kind"] = "repair"
        valid_repair_steps[-1]["action"] = "re-review"
        self.assertEqual(
            [],
            EVAL._review_discipline_errors(
                "valid-repair-reproduction", valid_repair_steps
            ),
        )

        disguised_edit_steps = copy.deepcopy(valid_repair_steps)
        disguised_edit_steps[0]["action"] = "edit"
        disguised_edit_errors = EVAL._review_discipline_errors(
            "edit-as-repair-reproduction", disguised_edit_steps
        )
        self.assertTrue(
            any(
                "actual material actions require implementation review" in error
                for error in disguised_edit_errors
            ),
            disguised_edit_errors,
        )

    def test_task_focus_relation_review_repair_and_cost_matrix_is_closed(self) -> None:
        results, errors = EVAL._task_focus_fixture_results(self.task_focus_cases)
        self.assertEqual([], errors)
        self.assertEqual(25, len(results))
        self.assertTrue(all(result["matches_expected"] for result in results))
        self.assertEqual(
            {"finding", "same-pattern", "repair", "review-level", "cost"},
            {result["scenario"] for result in results},
        )

    def test_task_focus_negative_controls_reject_scope_and_review_drift(self) -> None:
        expected = {
            "focus-rejects-adjacent-repair": "adjacent findings cannot block or enter repair",
            "focus-rejects-read-scope-write": "Allowed Read Scope does not grant write authority",
            "focus-rejects-l4-default-prereview": "L4 does not default to pre-implementation review",
            "focus-rejects-stale-repair-evidence": "fresh validation, latest actual diff, and fresh independent review",
            "focus-rejects-unrelated-repair-file": "revert the unrelated changed file",
        }
        by_id = {case["id"]: case for case in self.task_focus_cases}
        for case_id, message in expected.items():
            with self.subTest(case=case_id):
                errors = EVAL._task_focus_case_errors(by_id[case_id])
                self.assertTrue(any(message in error for error in errors), errors)

    def test_release_reviews_use_one_typed_guard_per_review_outcome(self) -> None:
        for case in [*self.release_cases, *self.scheduling_cases, *self.utility_cases]:
            review_count = sum(
                step.get("actor") == "review-agent"
                and step.get("action") in EVAL.REVIEW_ACTIONS | {"finding"}
                for step in case["steps"]
            )
            guard_count = sum(
                step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
                for step in case["steps"]
            )
            with self.subTest(case=case["id"]):
                self.assertEqual(review_count, guard_count)
                self.assertEqual(
                    [], EVAL._review_discipline_errors(case["id"], case["steps"])
                )

    @staticmethod
    def _discipline_event(case: dict) -> dict:
        return next(
            step
            for step in case["steps"]
            if step.get("action") == "implementation-discipline"
        )

    @staticmethod
    def _error_codes(errors: list[str]) -> set[str]:
        return {
            error.split("[", 1)[1].split("]", 1)[0]
            for error in errors
            if "[" in error and "]" in error
        }

    def _adaptive_case(self, approach: str) -> tuple[dict, dict, dict[str, dict]]:
        base_case_ids = {
            "test-first": "single-file-bug-fix",
            "test-after": "single-module-feature",
            "existing-proof-only": "single-module-feature",
            "non-test-validation": "release-rollback",
        }
        case = self._release_case(base_case_ids[approach])
        authority = case.get("implementation_oracle")
        anchored_assertion = next(
            (
                step["assertion"]
                for step in case["steps"]
                if step.get("action") == "adaptive-test-evidence"
                and step.get("evidence_kind") == "red"
            ),
            None,
        )
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "adaptive-test-evidence"
        ]
        event = self._discipline_event(case)
        variants = {
            "test-first": (
                "behavior",
                ["reproducible-bug"],
                ("red", "green"),
                "the reproducible owner bug reaches the accepted result",
                "owner.py public result",
                "the targeted assertion rejects the reproduced bug",
            ),
            "test-after": (
                "behavior",
                ["existing-primary-coverage"],
                ("green",),
                "a bounded local branch changes under existing primary coverage",
                "module-a/service.py local branch",
                "the module feature test observes the accepted branch result",
            ),
            "existing-proof-only": (
                "behavior",
                ["existing-regression-mechanism", "no-new-uncovered-behavior"],
                ("existing-proof",),
                "the edit preserves behavior already covered by the regression mechanism",
                "module-a/service.py existing covered behavior",
                "the existing regression assertion observes the unchanged behavior",
            ),
            "non-test-validation": (
                "non-behavior",
                ["documentation"],
                ("non-test",),
                "the release-plan documentation changes without runtime behavior",
                "release-plan.md documentation boundary",
                "the documentation check observes the rendered static plan",
            ),
        }
        (
            change_kind,
            risk_triggers,
            evidence_kinds,
            failure_mechanism,
            boundary,
            oracle,
        ) = variants[approach]
        if isinstance(authority, dict):
            failure_mechanism = authority["failure_mechanism"]
            oracle = authority["oracle"]
        evidence_ids = [f"{event['task_id']}-{kind}" for kind in evidence_kinds]
        guard = {
            "guard": "guard-g-adaptive-testing",
            "change_kind": change_kind,
            "approach": approach,
            "reason": f"{approach} matches the changed mechanism and oracle.",
            "failure_mechanism": failure_mechanism,
            "boundary": boundary,
            "oracle": oracle,
            "risk_triggers": risk_triggers,
            "evidence": evidence_ids,
            "proof_boundary": boundary,
        }
        guard_index = next(
            index
            for index, item in enumerate(event["evidence"])
            if item.get("guard") == "guard-g-adaptive-testing"
        )
        event["evidence"][guard_index] = guard
        records: dict[str, dict] = {}
        for evidence_id, kind in zip(evidence_ids, evidence_kinds):
            assertion = (
                "not-applicable"
                if kind == "non-test"
                else anchored_assertion
                if isinstance(authority, dict)
                else "the owner result matches the accepted behavior"
            )
            if isinstance(authority, dict):
                binding = authority["validation_binding"]
                record = {
                    "actor": "task-agent",
                    "action": "adaptive-test-evidence",
                    "task_id": event["task_id"],
                    "acceptance_id": authority["acceptance_id"],
                    "evidence_id": evidence_id,
                    "artifact_id": binding["artifact_id"],
                    "source_anchor": binding["source_anchor"],
                    "evidence_kind": kind,
                    "result": "failed" if kind == "red" else "passed",
                    "failure_class": {
                        "red": "target-behavior-missing",
                        "green": "none",
                        "existing-proof": "target-mechanism-covered",
                        "non-test": "testing-not-applicable",
                    }[kind],
                    "oracle_id": authority["oracle_id"],
                    "mechanism_id": authority["mechanism_id"],
                    "assertion_fingerprint": authority["assertion_fingerprint"],
                    "oracle": guard["oracle"],
                    "assertion": assertion,
                    "freshness": 0 if kind == "red" else 1,
                }
            else:
                record = {
                    "actor": "task-agent",
                    "action": "adaptive-test-evidence",
                    "task_id": event["task_id"],
                    "evidence_id": evidence_id,
                    "evidence_kind": kind,
                    "result": "failed" if kind == "red" else "passed",
                    "failure_class": {
                        "red": "target-behavior-missing",
                        "green": "none",
                        "existing-proof": "target-mechanism-covered",
                        "non-test": "testing-not-applicable",
                    }[kind],
                    "oracle": guard["oracle"],
                    "assertion": assertion,
                    "freshness": 0 if kind == "red" else 1,
                }
            records[kind] = record
        event_index = case["steps"].index(event)
        if "red" in records:
            case["steps"].insert(event_index, records["red"])
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        post_edit = [record for kind, record in records.items() if kind != "red"]
        case["steps"][edit_index + 1 : edit_index + 1] = post_edit
        return case, guard, records

    def test_implementation_discipline_accepts_direct_bugfix(self) -> None:
        self.assertEqual(
            [],
            self._trajectory_errors(self._release_case("single-file-bug-fix")),
        )

    def test_source_bound_bugfix_requires_structured_same_pattern_scan(self) -> None:
        case = self._release_case("single-file-bug-fix")
        guard = self._discipline_event(case)["evidence"][3]
        self.assertIn("same_pattern_scan", guard)
        guard.pop("same_pattern_scan")
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["D"],
            self._error_codes(errors),
        )

    def test_source_bound_reuse_rejects_placeholder_reason(self) -> None:
        case = self._release_case("single-file-bug-fix")
        reuse = self._discipline_event(case)["evidence"][4]["reuse_decision"]
        reuse["reason"] = "x"
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["E"],
            self._error_codes(errors),
        )

    def test_case_oracle_rejects_synchronized_weak_red_green(self) -> None:
        case = self._release_case("single-file-bug-fix")
        guard = self._discipline_event(case)["evidence"][-1]
        guard["oracle"] = "x"
        for step in case["steps"]:
            if step.get("action") == "adaptive-test-evidence":
                step["oracle"] = "x"
                step["assertion"] = "x"
        errors = self._trajectory_errors(case)
        self.assertIn(
            "implementation-oracle-authority",
            self._error_codes(errors),
        )

    def test_validation_rejects_cross_task_acceptance(self) -> None:
        case = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["acceptance_id"] = "acceptance.other-task"
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["C"],
            self._error_codes(errors),
        )

    def test_validation_rejects_oracle_artifact_mismatch(self) -> None:
        case = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["artifact_id"] = "artifact:other-test"
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["C"],
            self._error_codes(errors),
        )

    def test_source_bound_bugfix_accepts_explicit_zero_match_scan(self) -> None:
        case = self._release_case("single-file-bug-fix")
        scan = self._discipline_event(case)["evidence"][3].get(
            "same_pattern_scan"
        )
        self.assertIsInstance(scan, dict)
        assert isinstance(scan, dict)
        self.assertEqual([], scan["matches"])
        self.assertTrue(scan["explicit_zero"])
        self.assertEqual(
            [],
            EVAL._implementation_discipline_errors(
                case["id"],
                case["steps"],
                case["implementation_oracle"],
            ),
        )

    def test_evaluator_owns_hardened_oracle_digest(self) -> None:
        case = self._release_case("single-file-bug-fix")
        expected = EVAL.IMPLEMENTATION_ORACLE_CONTRACTS[case["id"]]
        self.assertEqual(
            case["implementation_oracle"]["canonical_sha256"],
            expected["canonical_sha256"],
        )

    def test_coordinated_oracle_rewrite_cannot_replace_external_authority(
        self,
    ) -> None:
        case = self._release_case("single-file-bug-fix")
        authority = case["implementation_oracle"]
        assertion = "coordinated replacement accepted behavior"
        authority["mechanism_id"] = "mechanism.coordinated-replacement"
        authority["failure_mechanism"] = "coordinated replacement mechanism"
        authority["oracle_id"] = "oracle.coordinated-replacement"
        authority["oracle"] = "coordinated replacement oracle"
        authority["assertion_fingerprint"] = EVAL._evidence_fingerprint(assertion)
        guard = self._discipline_event(case)["evidence"][-1]
        guard["failure_mechanism"] = authority["failure_mechanism"]
        guard["oracle"] = authority["oracle"]
        for record in case["steps"]:
            if record.get("action") != "adaptive-test-evidence":
                continue
            record["mechanism_id"] = authority["mechanism_id"]
            record["oracle_id"] = authority["oracle_id"]
            record["oracle"] = authority["oracle"]
            record["assertion"] = assertion
            record["assertion_fingerprint"] = authority[
                "assertion_fingerprint"
            ]
        self._rebind_authority_digest(case)
        self.assertNotEqual(
            case["implementation_oracle"]["canonical_sha256"],
            EVAL.IMPLEMENTATION_ORACLE_CONTRACTS[case["id"]][
                "canonical_sha256"
            ],
        )
        self.assertIn(
            "implementation-oracle-authority",
            self._error_codes(self._implementation_errors(case)),
        )

    def test_authority_bindings_require_exact_typed_bijection(self) -> None:
        variants: dict[str, dict] = {}

        extra = self._release_case("single-file-bug-fix")
        added = copy.deepcopy(
            extra["implementation_oracle"]["source_bindings"][-1]
        )
        added.update(
            {
                "evidence_id": "extra-unconsumed-source",
                "artifact_id": "artifact:extra.py",
                "path": "extra.py",
                "source_anchor": "extra.py#unconsumed",
            }
        )
        extra["implementation_oracle"]["source_bindings"].append(added)
        self._rebind_authority_digest(extra)
        variants["extra-binding"] = extra

        unconsumed = self._release_case("single-file-bug-fix")
        unconsumed["steps"] = [
            step
            for step in unconsumed["steps"]
            if step.get("evidence_id") != "bugfix-reuse-candidate"
        ]
        variants["unconsumed-binding"] = unconsumed

        multiuse = self._release_case("single-file-bug-fix")
        read = next(
            step
            for step in multiuse["steps"]
            if step.get("evidence_id") == "bugfix-reuse-candidate"
        )
        event_index = multiuse["steps"].index(self._discipline_event(multiuse))
        multiuse["steps"].insert(event_index, copy.deepcopy(read))
        variants["multiuse-binding"] = multiuse

        wrong_type = self._release_case("single-file-bug-fix")
        read = next(
            step
            for step in wrong_type["steps"]
            if step.get("evidence_id") == "bugfix-owner-source"
        )
        read["evidence_id"] = wrong_type["implementation_oracle"][
            "validation_binding"
        ]["evidence_id"]
        variants["wrong-type-binding"] = wrong_type

        for label, case in variants.items():
            with self.subTest(variant=label):
                self.assertIn(
                    "implementation-oracle-binding",
                    self._error_codes(self._implementation_errors(case)),
                )

    def test_coordinated_zero_scan_rewrite_cannot_replace_external_authority(
        self,
    ) -> None:
        case = self._release_case("single-file-bug-fix")
        authority = case["implementation_oracle"]
        binding = authority["same_pattern_binding"]
        binding["pattern_id"] = "pattern.coordinated-replacement"
        binding["scope"] = ["replacement.py"]
        binding["artifact_id"] = "artifact:replacement-scan"
        binding["source_anchor"] = "replacement.py#scan"
        scan = self._discipline_event(case)["evidence"][3][
            "same_pattern_scan"
        ]
        for field in ("pattern_id", "scope", "artifact_id", "source_anchor"):
            scan[field] = copy.deepcopy(binding[field])
        self._rebind_authority_digest(case)
        self.assertIn(
            "implementation-oracle-authority",
            self._error_codes(self._implementation_errors(case)),
        )

    def test_zero_match_is_fixture_structural_proof_only(self) -> None:
        case = self._release_case("single-file-bug-fix")
        authority = case["implementation_oracle"]["same_pattern_binding"]
        scan = self._discipline_event(case)["evidence"][3][
            "same_pattern_scan"
        ]
        self.assertEqual("fixture-structured-zero", authority["proof_kind"])
        self.assertEqual(authority["proof_kind"], scan["proof_kind"])
        self.assertNotIn("host", authority["proof_kind"])

    def test_adaptive_test_first_requires_ordered_valid_red_and_green(self) -> None:
        case = self._release_case("single-file-bug-fix")
        event = self._discipline_event(case)
        guard = next(
            item
            for item in event["evidence"]
            if item.get("guard") == "guard-g-adaptive-testing"
        )
        evidence_records = [
            step
            for step in case["steps"]
            if step.get("action") == "adaptive-test-evidence"
            and step.get("task_id") == event["task_id"]
        ]
        expected_ids = [
            "task-single-file-bug-fix-1-red",
            "task-single-file-bug-fix-1-green",
        ]
        self.assertEqual(expected_ids, guard["evidence"])
        self.assertEqual(expected_ids, [record["evidence_id"] for record in evidence_records])
        self.assertEqual(["red", "green"], [record["evidence_kind"] for record in evidence_records])
        red_index, green_index = [case["steps"].index(record) for record in evidence_records]
        event_index = case["steps"].index(event)
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        self.assertLess(red_index, event_index)
        self.assertLess(event_index, edit_index)
        self.assertLess(edit_index, green_index)
        self.assertEqual(
            [],
            self._implementation_errors(case),
        )

    def test_adaptive_testing_accepts_each_qualified_approach(self) -> None:
        for approach in (
            "test-first",
            "test-after",
            "existing-proof-only",
            "non-test-validation",
        ):
            with self.subTest(approach=approach):
                case, _guard, _records = self._adaptive_case(approach)
                self.assertEqual(
                    [],
                    self._implementation_errors(case),
                )

    def test_adaptive_testing_rejects_invalid_red_failure_classes(self) -> None:
        for failure_class in ("environment", "fixture", "import", "syntax", "unrelated"):
            with self.subTest(failure_class=failure_class):
                case, _guard, records = self._adaptive_case("test-first")
                records["red"]["failure_class"] = failure_class
                errors = self._implementation_errors(case)
                self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_adaptive_testing_rejects_weakened_assertion_and_wrong_order(self) -> None:
        case, _guard, records = self._adaptive_case("test-first")
        records["green"]["assertion"] = "the process returned"
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

        case, _guard, records = self._adaptive_case("test-first")
        case["steps"].remove(records["red"])
        edit_index = next(i for i, step in enumerate(case["steps"]) if step.get("action") == "edit")
        case["steps"].insert(edit_index + 1, records["red"])
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_adaptive_testing_rejects_stale_existing_proof_and_non_test_excuses(self) -> None:
        case, _guard, records = self._adaptive_case("existing-proof-only")
        records["existing-proof"]["freshness"] = 0
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

        case, guard, _records = self._adaptive_case("non-test-validation")
        guard["change_kind"] = "behavior"
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_adaptive_testing_rejects_fabricated_non_behavior_red_and_high_risk_downgrade(self) -> None:
        case, guard, _records = self._adaptive_case("non-test-validation")
        guard["approach"] = "test-first"
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

        case, guard, _records = self._adaptive_case("test-after")
        guard["risk_triggers"] = ["permission"]
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_persistent_adaptive_testing_fixture_matrix_matches_expectations(self) -> None:
        results, errors = EVAL._adaptive_testing_fixture_results(
            copy.deepcopy(self.adaptive_testing_cases)
        )
        self.assertEqual([], errors)
        self.assertEqual(15, len(results))
        self.assertTrue(all(result["matches_expected"] for result in results))
        self.assertEqual(4, sum(result["actual_valid"] for result in results))
        ids = {result["id"] for result in results}
        self.assertTrue(
            {
                "adaptive-test-first-valid",
                "adaptive-test-after-valid",
                "adaptive-existing-proof-valid",
                "adaptive-non-test-valid",
                "adaptive-rejects-weakened-assertion",
                "adaptive-rejects-red-after-edit",
                "adaptive-rejects-stale-existing-proof",
                "adaptive-rejects-non-test-excuse",
                "adaptive-rejects-non-behavior-red-green",
                "adaptive-rejects-high-risk-downgrade",
            }
            <= ids
        )

    def test_full_edit_trajectory_requires_guard_g(self) -> None:
        case = self._release_case("single-file-bug-fix")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "adaptive-test-evidence"
        ]
        event = self._discipline_event(case)
        event["evidence"] = [
            item
            for item in event["evidence"]
            if item.get("guard") != "guard-g-adaptive-testing"
        ]
        errors = self._implementation_errors(case)
        self.assertEqual(
            [
                f"{case['id']}: [implementation-discipline-missing-evidence] "
                f"missing guard evidence {[EVAL.IMPLEMENTATION_GUARD_CODES['G']]}"
            ],
            errors,
        )

    def test_adaptive_proof_must_follow_the_final_material_edit(self) -> None:
        case, _guard, records = self._adaptive_case("test-first")
        green_index = case["steps"].index(records["green"])
        case["steps"].insert(
            green_index + 1,
            {
                "actor": "task-agent",
                "action": "edit",
                "task_id": self._discipline_event(case)["task_id"],
                "path": "owner.py",
            },
        )
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_migration_cannot_hide_high_risk_with_low_risk_test_after(self) -> None:
        case = self._release_case("data-migration")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "adaptive-test-evidence"
        ]
        event = self._discipline_event(case)
        event["evidence"] = [
            item
            for item in event["evidence"]
            if item.get("guard") != "guard-g-adaptive-testing"
        ]
        event["evidence"].append(
            {
                "guard": "guard-g-adaptive-testing",
                "change_kind": "behavior",
                "approach": "test-after",
                "reason": "reported as low-risk local exploration",
                "failure_mechanism": "migration compatibility changes",
                "boundary": "schema migration boundary",
                "oracle": "migration compatibility result",
                "risk_triggers": ["low-risk-local-exploration"],
                "evidence": ["migration-green"],
                "proof_boundary": "migration fixture only",
            }
        )
        final_edit = max(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") in EVAL.EDIT_ACTIONS
        )
        case["steps"].insert(
            final_edit + 1,
            {
                "actor": "task-agent",
                "action": "adaptive-test-evidence",
                "task_id": event["task_id"],
                "evidence_id": "migration-green",
                "evidence_kind": "green",
                "result": "passed",
                "failure_class": "none",
                "oracle": "migration compatibility result",
                "assertion": "migration remains compatible",
                "freshness": 1,
            },
        )
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_implementation_discipline_accepts_post_analysis_implementation(
        self,
    ) -> None:
        self.assertEqual(
            [],
            self._trajectory_errors(self._release_case("single-module-feature")),
        )

    def test_internal_discipline_evidence_does_not_emit_user_feedback(self) -> None:
        expectations = {
            "single-file-bug-fix": {
                "time_to_first_productive_action_step": 2,
                "time_to_first_edit_step": 3,
                "control_turn_count": 4,
                "progress_count": 0,
            },
            "single-module-feature": {
                "time_to_first_productive_action_step": 3,
                "time_to_first_edit_step": 8,
                "control_turn_count": 8,
                "progress_count": 3,
            },
        }
        for case_id, expected in expectations.items():
            with self.subTest(case=case_id):
                case = self._release_case(case_id)
                metrics, errors = self._trajectory_metrics(case)
                self.assertEqual([], errors)
                adaptive_indexes = {
                    index
                    for index, step in enumerate(case["steps"])
                    if step.get("action") == "adaptive-test-evidence"
                }
                operational_steps, internal_indexes = EVAL._operational_steps(case["steps"])
                self.assertTrue(adaptive_indexes <= internal_indexes)
                self.assertFalse(
                    any(
                        step.get("action") == "adaptive-test-evidence"
                        for step in operational_steps
                    )
                )
                expected_implementation_internal_indexes = {
                    index
                    for index, step in enumerate(case["steps"])
                    if step.get("actor") == "task-agent"
                    and (
                        step.get("action") in EVAL.INTERNAL_EVIDENCE_ACTIONS
                        or (
                            step.get("action") == "read"
                            and step.get("read_kind")
                            in EVAL.IMPLEMENTATION_SOURCE_READ_KINDS
                        )
                    )
                }
                actual_implementation_internal_indexes = {
                    index
                    for index in internal_indexes
                    if case["steps"][index].get("actor") == "task-agent"
                }
                self.assertEqual(
                    expected_implementation_internal_indexes,
                    actual_implementation_internal_indexes,
                )
                self.assertEqual(
                    len(expected_implementation_internal_indexes),
                    metrics["implementation_internal_evidence_event_count"],
                )
                self.assertFalse(
                    any(
                        step.get("action") in EVAL.INTERNAL_EVIDENCE_ACTIONS
                        or (
                            step.get("action") == "read"
                            and step.get("read_kind")
                            in EVAL.IMPLEMENTATION_SOURCE_READ_KINDS
                        )
                        for step in operational_steps
                    )
                )
                self.assertEqual(
                    len(case["steps"]) - len(internal_indexes),
                    metrics["total_completion_steps"],
                )
                for metric, value in expected.items():
                    self.assertEqual(value, metrics[metric])
                maximum_silence = case["expected"].get("max_silent_steps_max")
                if maximum_silence is not None:
                    self.assertLessEqual(
                        metrics["max_silent_steps"],
                        maximum_silence,
                    )

    def test_anchored_typed_evidence_remains_internal(self) -> None:
        case = self._release_case("single-file-bug-fix")
        operational, internal = EVAL._operational_steps(case["steps"])
        anchored_indexes = {
            index
            for index, step in enumerate(case["steps"])
            if (
                tuple(step)
                in {
                    EVAL.IMPLEMENTATION_ANCHORED_READ_FIELDS,
                    EVAL.IMPLEMENTATION_ANCHORED_TEST_READ_FIELDS,
                    EVAL.ADAPTIVE_TEST_ANCHORED_EVIDENCE_FIELDS,
                }
            )
        }
        self.assertTrue(anchored_indexes)
        self.assertTrue(anchored_indexes <= internal)
        self.assertFalse(
            any(
                id(step)
                in {id(case["steps"][index]) for index in anchored_indexes}
                for step in operational
            )
        )
        metrics, errors = self._trajectory_metrics(case)
        self.assertEqual([], errors)
        self.assertEqual(3, metrics["time_to_first_edit_step"])
        self.assertEqual(0, metrics["duplicate_read_count"])

    def test_operational_reads_still_count_for_silence_and_duplication(self) -> None:
        case = self._release_case("single-module-feature")
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        case["steps"][edit_index:edit_index] = [
            {"actor": "task-agent", "action": "read", "path": "module-a/service.py"},
            {"actor": "task-agent", "action": "read", "path": "module-a/service.py"},
        ]
        metrics, _errors = self._trajectory_metrics(case)
        self.assertEqual(2, metrics["duplicate_read_count"])
        self.assertEqual(6, metrics["max_silent_steps"])
        self.assertFalse(metrics["required_multi_agent_progress_satisfied"])

    def test_all_normal_edit_trajectories_have_typed_discipline(self) -> None:
        for original in self.release_cases:
            if not any(
                step.get("actor") == "task-agent"
                and step.get("action") in EVAL.EDIT_ACTIONS
                for step in original["steps"]
            ):
                continue
            with self.subTest(case=original["id"]):
                case = copy.deepcopy(original)
                self.assertEqual(
                    [],
                    self._implementation_errors(case),
                )

    def test_implementation_discipline_mutation_matrix_rejects_each_guard_on_both_paths(
        self,
    ) -> None:
        guard_codes = EVAL.IMPLEMENTATION_GUARD_CODES
        mutations = (
            (
                "A",
                lambda event: event["evidence"][0]["read_evidence"].pop(1),
            ),
            (
                "B",
                lambda event: event["evidence"][1].__setitem__(
                    "owner_verified", False
                ),
            ),
            (
                "C",
                lambda event: event["evidence"][2]["outcome_matrix"].pop(
                    "forbidden"
                ),
            ),
            (
                "D",
                lambda event: event["evidence"][3].__setitem__(
                    "applies", not event["evidence"][3]["applies"]
                ),
            ),
            (
                "E",
                lambda event: event["evidence"][4].__setitem__(
                    "dependency_direction_resolved", False
                ),
            ),
            (
                "F",
                lambda event: event["evidence"][5].__setitem__(
                    "unrelated_refactor", True
                ),
            ),
        )
        paths = ("single-file-bug-fix", "single-module-feature")
        observed: set[tuple[str, str]] = set()
        for case_id in paths:
            for guard_key, mutate in mutations:
                with self.subTest(path=case_id, guard=guard_key):
                    case = self._release_case(case_id)
                    mutate(self._discipline_event(case))
                    errors = self._trajectory_errors(case)
                    self.assertIn(guard_codes[guard_key], self._error_codes(errors))
                    observed.add((case_id, guard_key))
        self.assertEqual(12, len(observed))

    def test_implementation_discipline_rejects_missing_event_before_edit(self) -> None:
        case = self._release_case("single-file-bug-fix")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "implementation-discipline"
        ]
        errors = self._trajectory_errors(case)
        self.assertIn(
            "implementation-discipline-missing-event",
            self._error_codes(errors),
        )

    def test_implementation_discipline_evidence_is_closed_unique_and_ordered(
        self,
    ) -> None:
        variants = (
            (
                "implementation-discipline-missing-evidence",
                lambda event: event["evidence"].pop(),
            ),
            (
                "implementation-discipline-duplicate-evidence",
                lambda event: event["evidence"].__setitem__(
                    5, copy.deepcopy(event["evidence"][0])
                ),
            ),
            (
                "implementation-discipline-unknown-evidence",
                lambda event: event["evidence"][5].__setitem__(
                    "guard", "unknown-guard"
                ),
            ),
            (
                "implementation-discipline-evidence-order",
                lambda event: event["evidence"].__setitem__(
                    slice(0, 2), list(reversed(event["evidence"][0:2]))
                ),
            ),
            (
                "implementation-discipline-event-schema",
                lambda event: event.__setitem__("unknown_field", True),
            ),
            (
                EVAL.IMPLEMENTATION_GUARD_CODES["B"],
                lambda event: event["evidence"][1].__setitem__(
                    "unknown_field", True
                ),
            ),
        )
        for expected_code, mutate in variants:
            with self.subTest(code=expected_code):
                case = self._release_case("single-file-bug-fix")
                mutate(self._discipline_event(case))
                self.assertIn(
                    expected_code,
                    self._error_codes(self._trajectory_errors(case)),
                )

    def test_implementation_discipline_rejects_edit_before_evidence(self) -> None:
        case = self._release_case("single-file-bug-fix")
        event_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("action") == "implementation-discipline"
        )
        event = case["steps"].pop(event_index)
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        case["steps"].insert(edit_index + 1, event)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["order"],
            self._error_codes(self._trajectory_errors(case)),
        )

    def test_guard_c_binds_exact_validation_evidence_id_or_command(self) -> None:
        for case_id in ("single-file-bug-fix", "single-module-feature"):
            with self.subTest(case=case_id):
                case = self._release_case(case_id)
                self.assertNotIn(
                    EVAL.IMPLEMENTATION_GUARD_CODES["C"],
                    self._error_codes(
                        self._implementation_errors(case)
                    ),
                )

    def test_guard_c_rejects_ambiguous_stale_and_nonpassing_validation(self) -> None:
        variants: dict[str, dict] = {}

        ambiguous = self._release_case("single-file-bug-fix")
        validation_index = next(
            index
            for index, step in enumerate(ambiguous["steps"])
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        ambiguous["steps"].insert(
            validation_index + 1,
            copy.deepcopy(ambiguous["steps"][validation_index]),
        )
        variants["ambiguous"] = ambiguous

        stale = self._release_case("single-file-bug-fix")
        validation_index = next(
            index
            for index, step in enumerate(stale["steps"])
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation = stale["steps"].pop(validation_index)
        edit_index = next(
            index
            for index, step in enumerate(stale["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        stale["steps"].insert(edit_index, validation)
        variants["pre-final-edit"] = stale

        nonpassing = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in nonpassing["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["outcome"] = "failed"
        variants["nonpassing"] = nonpassing

        for label, case in variants.items():
            with self.subTest(variant=label):
                errors = self._implementation_errors(case)
                self.assertIn(
                    EVAL.IMPLEMENTATION_GUARD_CODES["C"],
                    self._error_codes(errors),
                )

    def test_shared_validation_uses_one_closed_multi_task_binding(self) -> None:
        case = self._release_case("isolated-write-parallel-contract")
        shared = [
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
            and step.get("evidence_id") == "isolated-module-tests"
        ]
        self.assertEqual(1, len(shared))
        self.assertNotIn("task_id", shared[0])
        self.assertEqual(
            [
                "task-isolated-write-parallel-contract-1",
                "task-isolated-write-parallel-contract-2",
            ],
            shared[0]["task_ids"],
        )
        self.assertEqual(
            [],
            self._implementation_errors(case),
        )

    def test_validation_task_binding_rejects_duplicate_unknown_empty_and_both_forms(
        self,
    ) -> None:
        variants = {
            "duplicate": [
                "task-single-file-bug-fix-1",
                "task-single-file-bug-fix-1",
            ],
            "unknown": [
                "task-single-file-bug-fix-1",
                "unknown-task",
            ],
            "empty": [],
        }
        for label, task_ids in variants.items():
            with self.subTest(variant=label):
                case = self._release_case("single-file-bug-fix")
                validation = next(
                    step
                    for step in case["steps"]
                    if step.get("actor") == "task-agent"
                    and step.get("action") == "validate"
                )
                validation.pop("task_id")
                validation["task_ids"] = task_ids
                self.assertIn(
                    "validation-task-binding",
                    self._error_codes(
                        self._implementation_errors(case)
                    ),
                )

        case = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["task_ids"] = ["task-single-file-bug-fix-1"]
        self.assertIn(
            "validation-task-binding",
            self._error_codes(
                self._implementation_errors(case)
            ),
        )

    def test_fixture_groups_include_release_scheduling_and_utility_contracts(self) -> None:
        self.assertEqual(13, len(self.release_cases))
        self.assertEqual(1, len(self.scheduling_cases))
        self.assertEqual(2, len(self.utility_cases))
        expected_scopes = {
            "review-supplied-artifact-missing-diff": "requested utility workspace scope",
            "validation-task-no-edit": "named validation workspace scope",
        }
        for case in self.utility_cases:
            with self.subTest(case=case["id"]):
                assignment = case["steps"][1]["utility_capsule"]
                self.assertEqual(1, len(assignment["evidence_ledger"]))
                row = assignment["evidence_ledger"][0]
                self.assertEqual(CANONICAL_LEDGER_FIELDS, tuple(row))
                self.assertTrue(set(RETIRED_LEDGER_FIELDS).isdisjoint(row))
                self.assertEqual(
                    {
                        "Claim": "workspace baseline captured",
                        "Owner": assignment["owner"],
                        "Artifact": "workspace baseline evidence",
                        "Command": "declared read-only workspace checks",
                        "Result": "tracked staged and untracked baseline recorded",
                        "Freshness": 0,
                        "Scope": expected_scopes[case["id"]],
                        "Proof Limit": (
                            "baseline does not prove post-operation workspace state"
                        ),
                        "State": "current",
                    },
                    row,
                )
                self.assertEqual([], self._errors(copy.deepcopy(case)))

    def test_assignment_baseline_claim_requires_current_canonical_state(self) -> None:
        original = copy.deepcopy(self.utility_cases[0])
        self.assertEqual([], self._errors(copy.deepcopy(original)))

        for state in ("superseded", "invalid"):
            with self.subTest(state=state):
                case = copy.deepcopy(original)
                row = case["steps"][1]["utility_capsule"]["evidence_ledger"][0]
                row["State"] = state
                errors = self._errors(case)
                self.assertTrue(
                    any(
                        "Utility Assignment missing current evidence for "
                        "'workspace baseline captured'" in error
                        for error in errors
                    ),
                    errors,
                )

        case = copy.deepcopy(original)
        case["steps"][1]["utility_capsule"]["evidence_ledger"] = []
        errors = self._errors(case)
        self.assertTrue(
            any(
                "Utility Assignment missing current evidence for "
                "'workspace baseline captured'" in error
                for error in errors
            ),
            errors,
        )

    def test_completion_state_negative_controls_match_static_contract(self) -> None:
        results, errors = EVAL._completion_fixture_errors(
            copy.deepcopy(self.completion_state_cases),
            copy.deepcopy(self.release_cases),
        )
        self.assertEqual([], errors)
        self.assertEqual(30, len(results))
        self.assertTrue(all(item["matches_expected"] for item in results))
        expected_rules = {
            "validation-failed",
            "validation-unavailable",
            "high-risk-review-missing",
            "blocking-finding-unresolved",
            "changed-scope-unreviewed",
            "evidence-stale-after-edit",
        }
        observed_rules = {
            case["expected_error"]
            for case in self.completion_state_cases
            if case.get("expected_error") in expected_rules
        }
        self.assertEqual(expected_rules, observed_rules)

    def test_evidence_ledger_negative_controls_are_enforced(self) -> None:
        results, errors = EVAL._completion_fixture_errors(
            copy.deepcopy(self.completion_state_cases),
            copy.deepcopy(self.release_cases),
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        expected_negative_ids = {
            "completed-rejects-validation-not-required",
            "completed-rejects-missing-validation-evidence",
            "completed-rejects-erased-latest-edit-marker",
            "completed-rejects-review-self-attestation",
            "completed-rejects-single-review-owner-for-all-evidence",
            "ledger-rejects-legacy-evidence-id",
            "ledger-rejects-invalid-state",
            "ledger-rejects-legacy-task-id",
            "ledger-rejects-legacy-action",
            "ledger-rejects-legacy-freshness-marker",
            "ledger-rejects-support-from-superseded-evidence",
            "ledger-rejects-legacy-evidence-state",
            "ledger-rejects-legacy-supersedes",
            "ledger-rejects-support-from-invalid-evidence",
            "ledger-rejects-artifact-scope-mismatch",
            "ledger-rejects-proof-limit-scope-mismatch",
        }
        self.assertTrue(expected_negative_ids <= set(by_id))
        for case_id in expected_negative_ids:
            with self.subTest(case_id=case_id):
                self.assertFalse(by_id[case_id]["actual_valid"])
                self.assertTrue(by_id[case_id]["matches_expected"])

    def test_completion_freshness_is_derived_from_ledger_rows(self) -> None:
        for case in self.completion_state_cases:
            self.assertNotIn("evidence_fresh", case["claim"])

    def test_fixture_ledgers_are_canonical_except_tagged_legacy_negatives(
        self,
    ) -> None:
        tagged_case_ids: set[str] = set()
        for case in self.completion_state_cases:
            tags = case.get("tags", [])
            self.assertIn(tags, ([], [LEGACY_NEGATIVE_TAG]))
            if tags:
                tagged_case_ids.add(case["id"])
                self.assertFalse(case["expected_valid"])
                self.assertIn(
                    "retired Evidence Ledger field",
                    case["expected_error"],
                )
            for row in case["claim"]["evidence_ledger"]:
                retired = [field for field in RETIRED_LEDGER_FIELDS if field in row]
                with self.subTest(case=case["id"], claim=row.get("Claim")):
                    if tags:
                        self.assertEqual(1, len(retired))
                        self.assertEqual(
                            CANONICAL_LEDGER_FIELDS,
                            tuple(field for field in row if field not in retired),
                        )
                        self.assertEqual(
                            set(CANONICAL_LEDGER_FIELDS) | set(retired),
                            set(row),
                        )
                    else:
                        self.assertEqual([], retired)
                        self.assertEqual(CANONICAL_LEDGER_FIELDS, tuple(row))

        self.assertEqual(
            {
                "ledger-rejects-legacy-evidence-id",
                "ledger-rejects-legacy-task-id",
                "ledger-rejects-legacy-action",
                "ledger-rejects-legacy-freshness-marker",
                "ledger-rejects-legacy-evidence-state",
                "ledger-rejects-legacy-supersedes",
            },
            tagged_case_ids,
        )

        ledgers = []
        for case in self.utility_cases:
            ledgers.extend(
                (
                    case["steps"][1]["utility_capsule"]["evidence_ledger"],
                    case["steps"][2]["utility_evidence"]["evidence_ledger"],
                )
            )
        for ledger in ledgers:
            for row in ledger:
                with self.subTest(claim=row.get("Claim")):
                    self.assertEqual(CANONICAL_LEDGER_FIELDS, tuple(row))
                    self.assertTrue(set(RETIRED_LEDGER_FIELDS).isdisjoint(row))

    def test_negative_fixtures_encode_structured_ledger_invariants(self) -> None:
        by_id = {case["id"]: case for case in self.completion_state_cases}
        legacy_fields = {
            "ledger-rejects-legacy-evidence-id": "Evidence ID",
            "ledger-rejects-legacy-task-id": "Task ID",
            "ledger-rejects-legacy-action": "Action",
            "ledger-rejects-legacy-freshness-marker": "Freshness Marker",
            "ledger-rejects-legacy-evidence-state": "Evidence State",
            "ledger-rejects-legacy-supersedes": "Supersedes",
        }
        for case_id, field in legacy_fields.items():
            with self.subTest(case=case_id):
                case = by_id[case_id]
                self.assertEqual([LEGACY_NEGATIVE_TAG], case["tags"])
                self.assertIn(field, case["claim"]["evidence_ledger"][0])

        stale = by_id["completed-rejects-stale-evidence"]["claim"]
        self.assertEqual(stale["latest_material_edit_marker"], 2)
        self.assertLess(
            stale["evidence_ledger"][0]["Freshness"],
            stale["latest_material_edit_marker"],
        )
        self.assertEqual("current", stale["evidence_ledger"][0]["State"])
        self.assertEqual(
            "fresh",
            by_id["ledger-rejects-invalid-state"]["claim"]["evidence_ledger"][0][
                "State"
            ],
        )
        self.assertEqual(
            "superseded",
            by_id["ledger-rejects-support-from-superseded-evidence"]["claim"][
                "evidence_ledger"
            ][0]["State"],
        )
        self.assertEqual(
            "invalid",
            by_id["ledger-rejects-support-from-invalid-evidence"]["claim"][
                "evidence_ledger"
            ][0]["State"],
        )

        artifact_scope = by_id["ledger-rejects-artifact-scope-mismatch"]["claim"][
            "evidence_ledger"
        ][0]
        self.assertEqual("other.py", artifact_scope["Artifact"])
        self.assertEqual("owner.py", artifact_scope["Scope"])
        proof_scope = by_id["ledger-rejects-proof-limit-scope-mismatch"]["claim"][
            "evidence_ledger"
        ][0]
        self.assertIn("other.py", proof_scope["Proof Limit"])
        self.assertEqual("owner.py", proof_scope["Scope"])

    def test_retired_ledger_fields_cannot_be_reintroduced(self) -> None:
        base = copy.deepcopy(self.completion_state_cases[0]["claim"])
        retired_values = {
            "Evidence ID": "legacy-evidence-id",
            "Task ID": base["task_id"],
            "Action": "validate",
            "Freshness Marker": 2,
            "Evidence State": "current",
            "Supersedes": [],
        }
        for field, value in retired_values.items():
            with self.subTest(field=field):
                claim = copy.deepcopy(base)
                claim["evidence_ledger"][0][field] = value
                errors = EVAL.completion_claim_errors(claim)
                self.assertTrue(
                    any(
                        "retired Evidence Ledger field" in error and field in error
                        for error in errors
                    ),
                    errors,
                )

        claim = copy.deepcopy(base)
        row = claim["evidence_ledger"][0]
        claim["evidence_ledger"][0] = {
            "Evidence ID": "legacy-evidence-id",
            "Task ID": claim["task_id"],
            "Owner": row["Owner"],
            "Claim": row["Claim"],
            "Action": "validate",
            "Artifact": row["Artifact"],
            "Command": row["Command"],
            "Result": row["Result"],
            "Freshness Marker": row["Freshness"],
            "Scope": row["Scope"],
            "Proof Limit": row["Proof Limit"],
            "Evidence State": row["State"],
            "Supersedes": [],
        }
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("retired Evidence Ledger fields" in error for error in errors),
            errors,
        )

    def test_artifact_scope_and_proof_limit_paths_must_match_scope(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        row = next(
            item for item in claim["evidence_ledger"] if item["Claim"] == "requested-result"
        )
        row["Scope"] = "other.py"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("evidence Scope mismatch" in error for error in errors), errors)

        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        row = next(
            item for item in claim["evidence_ledger"] if item["Claim"] == "requested-result"
        )
        row["Proof Limit"] = "proof covers other.py only"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("evidence Proof Limit mismatch" in error for error in errors),
            errors,
        )

    def test_canonical_ledger_fields_are_structurally_validated(self) -> None:
        base = next(
            case["claim"]
            for case in self.completion_state_cases
            if case["id"] == "diagnosis-completed-when-fully-delivered"
        )
        for field in (
            "Claim",
            "Owner",
            "Artifact",
            "Command",
            "Result",
            "Scope",
            "Proof Limit",
        ):
            with self.subTest(field=field):
                claim = copy.deepcopy(base)
                claim["evidence_ledger"][0][field] = ""
                errors = EVAL.completion_claim_errors(claim)
                self.assertTrue(
                    any(f"{field} must be non-empty text" in error for error in errors),
                    errors,
                )

        claim = copy.deepcopy(base)
        claim["evidence_ledger"][0]["Claim"] = "unrequired-claim"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("missing current evidence for required claim" in error for error in errors),
            errors,
        )

        claim = copy.deepcopy(base)
        claim["evidence_ledger"][0]["Owner"] = "another-agent"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("Owner must equal" in error for error in errors), errors)

    def test_completed_implementation_requires_current_independent_review_rows(self) -> None:
        by_id = {case["id"]: case for case in self.completion_state_cases}
        valid = copy.deepcopy(
            by_id["implementation-completed-with-current-evidence"]["claim"]
        )
        owners = {row["Owner"] for row in valid["evidence_ledger"]}
        self.assertEqual({"task-agent", "review-agent"}, owners)
        self.assertEqual([], EVAL.completion_claim_errors(valid))

        self_attested = copy.deepcopy(
            by_id["completed-rejects-review-self-attestation"]["claim"]
        )
        errors = EVAL.completion_claim_errors(self_attested)
        self.assertTrue(
            any("independent review evidence" in error for error in errors),
            errors,
        )

    def test_completed_implementation_rejects_review_before_latest_edit(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        for row in claim["evidence_ledger"]:
            if row["Owner"] == "review-agent":
                row["Freshness"] = 1
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("independent review evidence" in error for error in errors),
            errors,
        )

    def test_completed_implementation_requires_current_validation_evidence(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["validation"] = "not-required"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("requires validation='passed'" in error for error in errors),
            errors,
        )

        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["evidence_ledger"] = [
            row
            for row in claim["evidence_ledger"]
            if row["Claim"] != "validation-passed"
        ]
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("validation-passed" in error for error in errors), errors)

    def test_completed_implementation_rejects_erased_or_lowered_edit_marker(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["latest_material_edit_marker"] = None
        claim["required_freshness_marker"] = 1
        for row in claim["evidence_ledger"]:
            if row["Owner"] == "review-agent":
                row["Freshness"] = 1
                row["Artifact"] = "previous diff before repair"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("latest_material_edit_marker" in error for error in errors),
            errors,
        )

        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["required_freshness_marker"] = 1
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("required_freshness_marker" in error for error in errors),
            errors,
        )

    def test_completed_implementation_rejects_unassigned_evidence_owner(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["evidence_ledger"][-1]["Owner"] = "another-agent"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("Owner must be one of" in error for error in errors), errors)

    def test_completed_implementation_requires_distinct_task_and_review_owners(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["owner"] = "review-agent"
        for row in claim["evidence_ledger"]:
            row["Owner"] = "review-agent"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("owner must equal 'task-agent'" in error for error in errors),
            errors,
        )

    def test_completion_state_allows_fully_delivered_diagnosis_and_answer(self) -> None:
        by_id = {case["id"]: case for case in self.completion_state_cases}
        for case_id in (
            "diagnosis-completed-when-fully-delivered",
            "answer-completed-when-fully-delivered",
        ):
            with self.subTest(case_id=case_id):
                claim = by_id[case_id]["claim"]
                self.assertEqual([], EVAL.completion_claim_errors(claim))

    def test_completion_claim_rejects_unknown_or_incomplete_shape(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim.pop("proof_limits_stated")
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("exact ordered fields" in error for error in errors), errors)

    def test_nested_reference_resolution_is_symmetric_across_build_profiles(self) -> None:
        manifests, errors = EVAL._load_build_manifests()
        self.assertEqual([], errors)
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
        )
        for profile, primary, owner, relative, delivery in rows:
            with self.subTest(profile=profile, owner=owner):
                resolved = EVAL._layer3_reference_build_path(
                    profile,
                    primary,
                    owner,
                    relative,
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

    def test_lightweight_reference_resolution_requires_one_delivery_path(self) -> None:
        base = {
            "compiled_layer3_references": {"primary": []},
            "top_level_skills": [],
        }
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_build_path(
                "test",
                "primary",
                "owner",
                "references/checklist.md",
                copy.deepcopy(base),
            )

        dual = copy.deepcopy(base)
        dual["compiled_layer3_references"]["primary"] = ["owner"]
        dual["top_level_skills"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_build_path(
                "test",
                "primary",
                "owner",
                "references/checklist.md",
                dual,
            )

    def test_utility_dispatch_rejects_skill_and_layer3_selection(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        dispatch = case["steps"][1]
        dispatch["primary_skill"] = "backend-change-builder"
        dispatch["layer3_skills"] = []
        self.assertTrue(
            any("must not select a Professional Skill" in error for error in self._errors(case))
        )

    def test_utility_dispatch_rejects_layer3_reference_field_even_when_empty(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][1]["layer3_references"] = []
        errors = self._errors(case)
        self.assertTrue(
            any("Layer 3 Reference" in error or "layer3_references" in error for error in errors),
            errors,
        )

    def test_utility_capsule_and_evidence_require_exact_field_order(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        capsule = case["steps"][1]["utility_capsule"]
        capsule["goal"] = capsule.pop("goal")
        evidence = case["steps"][2]["utility_evidence"]
        evidence["commands_run"] = evidence.pop("commands_run")
        errors = self._errors(case)
        self.assertTrue(any("exact ordered fields" in error for error in errors), errors)

    def test_utility_rejects_unknown_mode(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        case["steps"][1]["utility_capsule"]["mode"] = "unknown/no-edit"
        case["steps"][2]["utility_evidence"]["mode"] = "unknown/no-edit"
        self.assertTrue(any("invalid mode" in error for error in self._errors(case)))

    def test_utility_return_must_match_assignment_identity_and_mode(self) -> None:
        mutations = (
            ("owner", "another utility owner", "Owner must match"),
            ("mode", "validation-only/no-edit", "mode must match"),
            ("no_edit_enforcement", "unsupported", "enforcement must match"),
        )
        for field, value, expected in mutations:
            with self.subTest(field=field):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][2]["utility_evidence"][field] = value
                self.assertTrue(
                    any(expected in error for error in self._errors(case)),
                    self._errors(case),
                )

    def test_utility_assignment_and_return_statuses_are_contract_gated(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][1]["utility_capsule"]["status"] = "partial"
        errors = self._errors(case)
        self.assertTrue(any("Utility Assignment Status" in error for error in errors), errors)

        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["utility_evidence"]["status"] = "in_progress"
        errors = self._errors(case)
        self.assertTrue(any("Utility Return Status" in error for error in errors), errors)

    def test_utility_task_id_stays_outside_ledger_and_owner_is_bound(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        capsule = case["steps"][1]["utility_capsule"]
        evidence = case["steps"][2]["utility_evidence"]
        self.assertEqual(capsule["task_id"], evidence["task_id"])
        self.assertTrue(all("Task ID" not in row for row in capsule["evidence_ledger"]))
        self.assertTrue(all("Task ID" not in row for row in evidence["evidence_ledger"]))
        evidence["task_id"] = "another-utility-task"
        errors = self._errors(case)
        self.assertTrue(any("Task ID must match" in error for error in errors), errors)
        self.assertFalse(any("Evidence ID" in error for error in errors), errors)

        case = copy.deepcopy(self.utility_cases[0])
        row = case["steps"][2]["utility_evidence"]["evidence_ledger"][-1]
        row["Owner"] = "another utility owner"
        errors = self._errors(case)
        self.assertTrue(any("Owner must equal" in error for error in errors), errors)

        case = copy.deepcopy(self.utility_cases[0])
        row = case["steps"][2]["utility_evidence"]["evidence_ledger"][-1]
        row["Task ID"] = case["steps"][2]["utility_evidence"]["task_id"]
        errors = self._errors(case)
        self.assertTrue(
            any("retired Evidence Ledger field" in error for error in errors),
            errors,
        )

    def test_completed_utility_requires_current_evidence_closure(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        result_row = case["steps"][2]["utility_evidence"]["evidence_ledger"][-1]
        self.assertEqual("utility result delivered", result_row["Claim"])
        result_row["State"] = "invalid"
        errors = self._errors(case)
        self.assertTrue(
            any("supported only by superseded or invalid evidence" in error for error in errors),
            errors,
        )

    def test_utility_case_rejects_any_edit(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        case["steps"].insert(
            2,
            {"actor": "task-agent", "action": "edit", "path": "owner.py"},
        )
        self.assertTrue(any("must not edit or repair" in error for error in self._errors(case)))

    def test_diff_export_must_precede_review(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2], case["steps"][3] = case["steps"][3], case["steps"][2]
        self.assertTrue(
            any("must precede review dispatch, read, and review" in error for error in self._errors(case))
        )

    def test_utility_rejects_network_command(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        command = "git fetch origin"
        case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
        case["steps"][2]["utility_evidence"]["commands_run"][3] = command
        self.assertTrue(any("unsafe command" in error for error in self._errors(case)))

    def test_validation_utility_rejects_mutating_command(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        command = "touch owner.py"
        case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
        case["steps"][2]["utility_evidence"]["commands_run"][3] = command
        self.assertTrue(
            any("not declared as a non-modifying check" in error for error in self._errors(case))
        )

    def test_allowed_prefix_cannot_hide_shell_control_or_substitution(self) -> None:
        suffixes = (
            "; git push origin main",
            " && git push origin main",
            " || git push origin main",
            " | tee actual.diff",
            " > actual.diff",
            " < input.diff",
            " $(git push origin main)",
            " `git push origin main`",
        )
        for suffix in suffixes:
            with self.subTest(suffix=suffix):
                case = copy.deepcopy(self.utility_cases[0])
                command = (
                    "git --no-pager diff --no-ext-diff --no-textconv HEAD~1..HEAD"
                    + suffix
                )
                case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
                case["steps"][2]["utility_evidence"]["commands_run"][3] = command
                self.assertTrue(any("unsafe" in error for error in self._errors(case)))

    def test_changed_workspace_invalidates_utility_and_blocks_closure(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        check = case["steps"][2]["utility_evidence"]["workspace_diff_check"]
        check["status"] = "changed"
        check["after"] = ["tracked:owner.py", "staged:none", "untracked:none"]
        errors = self._errors(case)
        self.assertTrue(any("invalid unless workspace diff status is unchanged" in error for error in errors), errors)
        self.assertTrue(any("completed requires an unchanged" in error for error in errors), errors)
        self.assertTrue(any("must not continue to review or closure" in error for error in errors), errors)

    def test_unavailable_workspace_check_invalidates_diff_review(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["utility_evidence"]["workspace_diff_check"]["status"] = "unavailable"
        errors = self._errors(case)
        self.assertTrue(any("invalid unless workspace diff status is unchanged" in error for error in errors), errors)
        self.assertTrue(any("completed requires an unchanged" in error for error in errors), errors)
        self.assertTrue(any("must not continue to review or closure" in error for error in errors), errors)

    def test_workspace_checks_must_run_before_and_after_operation(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        case["steps"][2]["utility_evidence"]["commands_run"].pop()
        self.assertTrue(
            any("exactly before and after" in error for error in self._errors(case))
        )

    def test_operation_first_or_last_breaks_adjacent_workspace_groups(self) -> None:
        for placement in ("first", "last"):
            with self.subTest(placement=placement):
                case = copy.deepcopy(self.utility_cases[1])
                commands = case["steps"][2]["utility_evidence"]["commands_run"]
                operation = commands.pop(3)
                commands.insert(0 if placement == "first" else len(commands), operation)
                self.assertTrue(
                    any("adjacent ordered pre-check group" in error for error in self._errors(case))
                )

    def test_interleaved_workspace_checks_break_exact_sequence(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        commands = case["steps"][2]["utility_evidence"]["commands_run"]
        commands[1], commands[3] = commands[3], commands[1]
        self.assertTrue(
            any("adjacent ordered pre-check group" in error for error in self._errors(case))
        )

    def test_missing_operation_breaks_utility_sequence(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        case["steps"][2]["utility_evidence"]["commands_run"].pop(3)
        self.assertTrue(
            any("exactly one mode operation" in error for error in self._errors(case))
        )

    def test_diff_export_rejects_output_external_diff_and_textconv_options(self) -> None:
        commands = (
            "git --no-pager diff --no-ext-diff --no-textconv --output=actual.diff HEAD~1..HEAD",
            "git --no-pager diff --no-ext-diff --no-textconv --output actual.diff HEAD~1..HEAD",
            "git --no-pager diff --no-ext-diff --no-textconv -o actual.diff HEAD~1..HEAD",
            "git --no-pager diff --no-ext-diff --no-textconv -oactual.diff HEAD~1..HEAD",
            "git --no-pager diff --no-ext-diff --no-textconv --ext-diff HEAD~1..HEAD",
            "git --no-pager diff --no-ext-diff --no-textconv --textconv HEAD~1..HEAD",
        )
        for command in commands:
            with self.subTest(command=command):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
                case["steps"][2]["utility_evidence"]["commands_run"][3] = command
                self.assertTrue(any("unsafe command" in error for error in self._errors(case)))

    def test_diff_export_rejects_git_global_config_exec_and_pager_options(self) -> None:
        commands = (
            "git -c core.pager=cat diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "git --config-env=core.pager=PAGER diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "git --exec-path=/tmp diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "git --paginate diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "git --no-pager --paginate diff --no-ext-diff --no-textconv HEAD~1..HEAD",
        )
        for command in commands:
            with self.subTest(command=command):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
                case["steps"][2]["utility_evidence"]["commands_run"][3] = command
                self.assertTrue(any("unsafe command" in error for error in self._errors(case)))

    def test_diff_export_requires_pager_ext_diff_and_textconv_shutdowns(self) -> None:
        commands = (
            "git diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "git --no-pager diff --no-textconv HEAD~1..HEAD",
            "git --no-pager diff --no-ext-diff HEAD~1..HEAD",
        )
        for command in commands:
            with self.subTest(command=command):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
                case["steps"][2]["utility_evidence"]["commands_run"][3] = command
                self.assertTrue(any("unsafe command" in error for error in self._errors(case)))

    def test_diff_and_show_pass_only_with_all_three_safety_controls(self) -> None:
        commands = (
            "git --no-pager diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "git --no-pager show --no-ext-diff --no-textconv HEAD",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(EVAL._utility_command_is_safe(command))

    def test_workspace_diff_checks_disable_pager_ext_diff_and_textconv(self) -> None:
        for case in self.utility_cases:
            checks = case["steps"][1]["utility_capsule"]["workspace_baseline"]["check_commands"]
            self.assertEqual(list(EVAL.WORKSPACE_CHECK_COMMANDS), checks)
            for command in checks:
                if " diff " not in command:
                    continue
                self.assertIn("git --no-pager diff ", command)
                self.assertIn("--no-ext-diff", command)
                self.assertIn("--no-textconv", command)
                self.assertTrue(EVAL._utility_command_is_safe(command))

    def test_diff_export_must_use_supplied_or_host_native_artifact(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["artifact_ref"] = "actual.diff"
        self.assertTrue(
            any("supplied content or a host-native artifact" in error for error in self._errors(case))
        )

    def test_utility_result_actor_must_be_task_agent(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["actor"] = "review-agent"
        self.assertTrue(
            any("utility result actor must be task-agent" in error for error in self._errors(case))
        )

    def test_extra_professional_task_dispatch_breaks_exact_immediate_pair(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        extra_dispatch = copy.deepcopy(self.release_cases[0]["steps"][1])
        case["steps"].insert(
            2,
            extra_dispatch,
        )
        errors = self._errors(case)
        self.assertTrue(
            any("exactly one task-agent dispatch" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("followed immediately by its result" in error for error in errors),
            errors,
        )

    def test_external_read_fixtures_cover_offline_allow_and_deny_paths(self) -> None:
        results, errors = EVAL._external_read_fixture_results(
            copy.deepcopy(self.external_read_cases)
        )
        self.assertEqual([], errors)
        self.assertEqual(14, len(results))
        self.assertEqual(
            {"WebSearch", "WebFetch", "ConnectorRead"},
            {
                item["operation"]
                for item in results
                if item["actual_valid"] and item["external_read_triggered"]
            },
        )
        by_id = {item["id"]: item for item in results}
        for case_id in (
            "external-read-no-material-claim",
            "external-read-local-evidence-sufficient",
            "external-read-noncritical-proof-limit",
            "external-read-unsupported-local-continue",
        ):
            self.assertFalse(by_id[case_id]["external_read_triggered"])
        for case_id in (
            "external-read-task-agent-denied",
            "external-read-review-agent-denied",
            "external-read-private-query-denied",
            "external-read-raw-instruction-denied",
        ):
            self.assertFalse(by_id[case_id]["expected_valid"])
            self.assertTrue(by_id[case_id]["matches_expected"])

    def test_external_read_mutations_reject_prompt_execution_and_disclosure(self) -> None:
        base = copy.deepcopy(
            next(
                case
                for case in self.external_read_cases
                if case["id"] == "external-read-prompt-injection-ignored"
            )
        )
        mutations = (
            ("instruction_executed", True, "external-content-control"),
            ("raw_instruction_propagated", True, "external-content-control"),
        )
        for field, value, expected in mutations:
            with self.subTest(field=field):
                case = copy.deepcopy(base)
                case["response"][field] = value
                case["expected_valid"] = True
                case["expected_error"] = None
                _results, errors = EVAL._external_read_fixture_results([case])
                self.assertTrue(any(expected in error for error in errors), errors)

        leak = copy.deepcopy(base)
        leak["request"]["contains_protected_content"] = True
        leak["expected_valid"] = True
        leak["expected_error"] = None
        _results, errors = EVAL._external_read_fixture_results([leak])
        self.assertTrue(any("external-read-disclosure" in error for error in errors), errors)

    def test_external_read_mutations_reject_role_and_jit_drift(self) -> None:
        base = copy.deepcopy(
            next(
                case
                for case in self.external_read_cases
                if case["id"] == "external-read-websearch-official"
            )
        )
        task_case = copy.deepcopy(base)
        task_case["role"] = "task-agent"
        task_case["expected_valid"] = True
        task_case["expected_error"] = None
        _results, errors = EVAL._external_read_fixture_results([task_case])
        self.assertTrue(any("external-read-role" in error for error in errors), errors)

        no_claim = copy.deepcopy(base)
        no_claim["evidence_state"] = "no-material-claim"
        no_claim["expected_valid"] = True
        no_claim["expected_error"] = None
        _results, errors = EVAL._external_read_fixture_results([no_claim])
        self.assertTrue(any("external-read-jit" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
