from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_owned_eval_report(
    test_case: unittest.TestCase,
    root: Path,
    relative: str,
    expected_fields: dict[str, object],
) -> dict:
    path = root / relative
    test_case.assertTrue(path.is_file(), f"owned eval report is missing: {relative}")
    report = json.loads(path.read_text(encoding="utf-8"))
    test_case.assertIsInstance(report, dict, relative)
    for field, expected in expected_fields.items():
        test_case.assertIn(field, report, f"required field is missing: {relative}:{field}")
        test_case.assertEqual(expected, report[field], (relative, field))
    return report


class HooklessEvaluationTests(unittest.TestCase):
    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_routing_evaluation(self) -> None:
        report = load_owned_eval_report(
            self,
            ROOT,
            "reports/routing-eval.json",
            {
                "schema_version": 6,
                "status": "pass",
                "negative_case_count": 69,
                "domain_family_case_count": 44,
                "domain_anti_case_count": 26,
                "domain_transition_case_count": 13,
                "domain_unchanged_case_count": 14,
            },
        )
        self.assertEqual(report["case_count"], report["passed_count"])
        self.assertEqual(report["case_count"], len(report["results"]))
        self.assertTrue(
            all(
                item["negative_passed"]
                for item in report["results"]
                if item["excluded_skills"]
            )
        )
        self.assertEqual("full", report["candidate_coverage"])
        self.assertEqual("proven", report["route_once"])
        self.assertEqual(0, report["legacy_route_count"])
        boundary_relations = report["boundary_relations"]
        self.assertEqual("pass", boundary_relations["status"])
        self.assertEqual(8, boundary_relations["relation_count"])
        self.assertEqual(8, boundary_relations["passed_count"])
        self.assertEqual(32, boundary_relations["role_count"])
        self.assertEqual("full", boundary_relations["candidate_coverage"])
        self.assertEqual("proven", boundary_relations["route_once"])
        self.assertEqual([], boundary_relations["errors"])
        self.assertTrue(
            all(
                isinstance(item.get("route_decision"), dict)
                for item in report["results"]
            )
        )
        by_id = {item["id"]: item for item in report["results"]}
        expected_negative_owners = {
            "security-anti-credential-session-internal-refactor": "backend-change-builder",
            "security-anti-reliability-only": "reliability-observability-gate",
            "security-anti-input-shape": "data-api-contract-changer",
            "security-anti-scanner-report": "change-documentation-gate",
            "reliability-anti-unit-local-performance": "quality-test-gate",
            "reliability-anti-logging-field": "logging-design-gate",
            "reliability-anti-release-ordering": "delivery-release-gate",
            "reliability-anti-data-correctness": "data-middleware-change-builder",
            "ai-anti-static-search": "engineering-change-analysis",
            "ai-anti-database-model-evaluation": "engineering-change-analysis",
            "bigdata-anti-single-database-table": "data-middleware-change-builder",
            "bigdata-anti-single-table-without-pipeline": "data-middleware-change-builder",
            "iot-anti-cloud-device-api": "engineering-change-analysis",
            "iot-anti-cloud-only-no-firmware-physical": "engineering-change-analysis",
            "iot-anti-cloud-network-protocol-timing": "engineering-change-analysis",
            "low-level-anti-rust-business-service": "backend-change-builder",
            "mobile-anti-responsive-pwa": "frontend-change-builder",
            "payment-anti-authorization-copy": "frontend-change-builder",
            "payment-anti-order-copy": "frontend-change-builder",
            "payment-anti-order-display-unchanged-state": "frontend-change-builder",
            "web3-anti-hash-signature": "backend-change-builder",
            "web3-anti-payment-wallet-recovery": "frontend-change-builder",
        }
        for case_id, adjacent_owner in expected_negative_owners.items():
            with self.subTest(case=case_id):
                row = by_id[case_id]
                self.assertTrue(row["passed"])
                self.assertTrue(row["negative_passed"])
                self.assertEqual(adjacent_owner, row["actual"]["primary_skill"])
        positive_domain_cases = {
            "ai-rag-tool-authority": "ai-product-extension",
            "bigdata-cdc-stream-replay": "bigdata-product-extension",
            "iot-firmware-actuator-rollout": "iot-embedded-extension",
            "low-level-ffi-ownership": "low-level-systems-extension",
            "mobile-native-lifecycle-permission": "android-platform-extension",
            "payment-security": "payment-trading-extension",
            "web3-chain-contract-finality": "web3-product-extension",
        }
        negative_domain_cases = {
            "ai-anti-static-search": "ai-product-extension",
            "ai-anti-database-model-evaluation": "ai-product-extension",
            "bigdata-anti-single-database-table": "bigdata-product-extension",
            "bigdata-anti-single-table-without-pipeline": "bigdata-product-extension",
            "iot-anti-cloud-device-api": "iot-embedded-extension",
            "iot-anti-cloud-only-no-firmware-physical": "iot-embedded-extension",
            "iot-anti-cloud-network-protocol-timing": "iot-embedded-extension",
            "low-level-anti-rust-business-service": "low-level-systems-extension",
            "mobile-anti-responsive-pwa": "android-platform-extension",
            "payment-anti-authorization-copy": "payment-trading-extension",
            "payment-anti-order-copy": "payment-trading-extension",
            "payment-anti-order-display-unchanged-state": "payment-trading-extension",
            "web3-anti-hash-signature": "web3-product-extension",
            "web3-anti-payment-wallet-recovery": "web3-product-extension",
        }
        for case_id, domain in positive_domain_cases.items():
            with self.subTest(positive_domain_case=case_id):
                self.assertIn(domain, by_id[case_id]["actual"]["layer3_skills"])
        for case_id, domain in negative_domain_cases.items():
            with self.subTest(negative_domain_case=case_id):
                row = by_id[case_id]
                selected = {
                    row["actual"]["primary_skill"],
                    row["actual"]["review_skill"],
                    *row["actual"]["layer3_skills"],
                }
                self.assertIn(domain, row["excluded_skills"])
                self.assertNotIn(domain, selected)
        family_variants: dict[tuple[str, str], set[str]] = {}
        for row in report["results"]:
            family = row.get("domain_family")
            if not family:
                continue
            key = (family["domain"], family["family"])
            family_variants.setdefault(key, set()).add(family["variant"])
            self.assertIn(family["domain"], row["actual"]["layer3_skills"])
            self.assertEqual(
                {"domain": family["domain"], "family": family["family"]},
                row["matched_domain_family"],
            )
        self.assertEqual(21, len(family_variants))
        self.assertTrue(
            all(
                variants == {"canonical", "paraphrase"}
                for variants in family_variants.values()
            )
        )
        transitions = [
            row for row in report["results"] if row.get("domain_transition")
        ]
        unchanged = [
            row
            for row in report["results"]
            if row.get("domain_anti_variant") == "unchanged-paraphrase"
        ]
        self.assertEqual(
            {domain for domain, _family in family_variants},
            {row["domain_transition"]["domain"] for row in transitions},
        )
        self.assertEqual(
            {domain for domain, _family in family_variants},
            {row["domain_anti"] for row in unchanged},
        )
        for row in transitions:
            self.assertIn(
                row["domain_transition"]["domain"],
                row["actual"]["layer3_skills"],
            )
        for row in unchanged:
            self.assertIn(row["domain_anti"], row["excluded_skills"])
        lifecycle = by_id["security-credential-session-lifecycle-change"]
        self.assertTrue(lifecycle["passed"])
        self.assertEqual(
            "security-privacy-gate", lifecycle["actual"]["primary_skill"]
        )
        self.assertEqual(
            ["authentication-security"], lifecycle["actual"]["layer3_skills"]
        )
        self.assertLessEqual(report["max_layer3_per_case"], 3)
        self.assertEqual("deterministic-fixtures", report["evidence_scope"])
        folded = " ".join(report["limitations"])
        self.assertIn("wall-clock performance", folded)
        self.assertIn("real-host accuracy", folded)
        self.assertIn("installed user experience", folded)
        self.assertIn("deterministic regression oracle", folded)

    def test_owned_eval_report_consumer_rejects_required_field_mutation_only(
        self,
    ) -> None:
        consumer = globals().get("load_owned_eval_report")
        self.assertTrue(callable(consumer), "owned eval report consumer is missing")
        source = json.loads(
            (ROOT / "reports/routing-eval.json").read_text(encoding="utf-8")
        )
        expected = {
            "schema_version": 6,
            "status": "pass",
            "negative_case_count": 69,
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            path = root / "reports/routing-eval.json"
            mutated = dict(source)
            mutated.pop("status")
            path.write_text(json.dumps(mutated), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "required field"):
                consumer(self, root, "reports/routing-eval.json", expected)

            with_extra = dict(source)
            with_extra["unconsumed_future_field"] = {"value": "out-of-scope"}
            path.write_text(json.dumps(with_extra), encoding="utf-8")
            loaded = consumer(
                self, root, "reports/routing-eval.json", expected
            )
            self.assertEqual(with_extra, loaded)

    def test_observable_trajectory_and_context_evaluations(self) -> None:
        report = load_owned_eval_report(
            self,
            ROOT,
            "reports/hookless-control-plane-eval.json",
            {"status": "pass", "fixture_count": 16},
        )
        self.assertEqual("pass", report["status"])
        self.assertEqual(16, report["fixture_count"])
        self.assertEqual(13, report["release_fixture_count"])
        self.assertEqual(1, report["scheduling_fixture_count"])
        self.assertEqual(2, report["utility_fixture_count"])
        self.assertEqual(
            report["fixture_count"],
            report["release_fixture_count"]
            + report["scheduling_fixture_count"]
            + report["utility_fixture_count"],
        )
        self.assertEqual(
            "unsupported-on-declared-hosts",
            report["parallelism_contract"]["current_write_parallelism"],
        )
        self.assertTrue(report["parallelism_contract"]["shared_workspace_serial_write"])
        self.assertEqual(
            report["orchestration_fixture_count"], len(report["semantic_traces"])
        )
        self.assertTrue(
            all(
                fixture["retained_semantic_equality"] is True
                for fixture in report["orchestration_fixtures"]
                if fixture["expected_valid"]
            )
        )
        direct = next(
            trace
            for trace in report["semantic_traces"]
            if trace["id"] == "dedup-direct-work-zero-analysis"
        )
        self.assertEqual("direct", direct["work_kind"])
        self.assertEqual({"count": 0, "kinds": []}, direct["analysis"])
        mutation_ids = {
            "duplicate-same-scope-analysis",
            "review-every-edit-task",
            "skip-final-review-boundary",
            "extra-final-review-after-covering-rereview",
            "rerun-valid-validation-without-invalidation",
            "reuse-validation-after-material-edit",
            "repair-without-fresh-validation",
            "repair-without-rereview",
        }
        self.assertTrue(
            mutation_ids <= {trace["id"] for trace in report["semantic_traces"]}
        )
        self.assertTrue(
            all(
                trace["proof_limit"] == "deterministic-structural-fixture-only"
                for trace in report["semantic_traces"]
            )
        )
        self.assertEqual("deterministic-fixtures", report["evidence_scope"])
        self.assertTrue(any("wall-clock performance" in item for item in report["limitations"]))
        self.assertTrue(any("real-host accuracy" in item for item in report["limitations"]))
        self.assertTrue(any("installed user experience" in item for item in report["limitations"]))
        self.assertNotIn("live_observations", report)
        self.assertNotIn("adoption_threshold_status", report)
        self.assertNotIn("efficiency_improvement_claim", report)

        rendered = load_owned_eval_report(
            self,
            ROOT,
            "reports/rendered-context-budget.json",
            {
                "status": "pass",
                "evidence_scope": "deterministic-rendered-artifacts",
                "compiled_layer3_format": "ai-consumption-v1",
                "tokenizer": "o200k_base",
            },
        )
        self.assertEqual("pass", rendered["status"])
        self.assertEqual("deterministic-rendered-artifacts", rendered["evidence_scope"])
        self.assertEqual("ai-consumption-v1", rendered["compiled_layer3_format"])
        self.assertEqual("o200k_base", rendered["tokenizer"])
        self.assertEqual(report["fixture_count"], rendered["fixture_count"])
        self.assertEqual(
            rendered["dispatch_count"] * len(rendered["hosts"]),
            rendered["measurement_count"],
        )
        budget = rendered["budget_governance"]
        core_budget = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )["context_budget_contract"]
        self.assertEqual("conformance", budget["mode"])
        self.assertEqual([], budget["conformance_failures"])
        self.assertFalse(
            budget["selection_contract"]["budget_applied_to_candidate_selection"]
        )
        self.assertEqual(
            {
                key: value["soft_target"]
                for key, value in core_budget["budget_classes"].items()
            },
            budget["soft_targets"],
        )
        self.assertEqual(
            {
                key: value["hard_ceiling"]
                for key, value in core_budget["budget_classes"].items()
            },
            budget["hard_ceilings"],
        )
        self.assertTrue(rendered["aggregate"]["max_main"]["within_hard_ceiling"])
        self.assertLessEqual(
            rendered["aggregate"]["max_duplicate_rule_token_ratio"],
            budget["duplicate_rule_token_ratio_max"],
        )
        transferred = rendered["transferred_context"]
        self.assertEqual(
            {
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
            },
            set(transferred["categories"]),
        )
        self.assertEqual(9, transferred["long_task_selector_join_count"])
        self.assertEqual(
            transferred["gross_tokens"],
            transferred["non_compressible_tokens"]
            + transferred["compressible_tokens"],
        )
        self.assertEqual(
            "candidate-subject-only",
            transferred["measurement_kind"],
        )
        self.assertTrue(
            transferred["semantic_baseline"]["retained_semantic_equality"]
        )
        self.assertEqual(
            report["orchestration_fixture_count"],
            transferred["semantic_baseline"]["orchestration_fixture_count"],
        )
        self.assertNotIn("realized_reduction_ratio", transferred)
        self.assertNotIn("context_compaction_decision", transferred)
        repair_rows = [
            row["projection"]
            for task in transferred["long_task_rows"]
            for row in task["boundary_rows"]
            if row["boundary"] == "review_to_repair"
        ]
        self.assertTrue(repair_rows)
        for repair in repair_rows:
            self.assertEqual(2, len(repair["repair_batch_key"]))
            self.assertTrue(
                all(
                    isinstance(item, str) and item
                    for item in repair["repair_batch_key"]
                )
            )
            self.assertTrue(
                all(
                    obligation["required_covering_rereview"][
                        "covered_task_ids"
                    ]
                    == [repair["repair_batch_key"][1]]
                    for obligation in repair["finding_obligations"]
                )
            )

        context = load_owned_eval_report(
            self,
            ROOT,
            "reports/context-control-plane-eval.json",
            {"status": "pass", "evidence_scope": "deterministic-fixtures"},
        )
        self.assertEqual("pass", context["status"])
        self.assertEqual("deterministic-fixtures", context["evidence_scope"])
        self.assertTrue(set(report["limitations"]).issubset(context["limitations"]))
        self.assertEqual(rendered["aggregate"], context["rendered_context_summary"])
        self.assertEqual(
            "candidate-subject-only",
            context["transferred_context_summary"]["measurement_kind"],
        )
        self.assertNotIn("context_compaction_decision", context)
        self.assertNotIn("safe_parallel_writes", context["checks"])
        self.assertTrue(context["checks"]["current_write_parallelism_unsupported"])
        self.assertTrue(context["checks"]["shared_workspace_serial_write"])
        self.assertTrue(context["checks"]["conditional_isolated_write_contract"])
        self.assertTrue(context["checks"]["utility_workspace_unchanged_gate"])
        self.assertTrue(context["checks"]["transferred_context_measurement_valid"])
        self.assertNotIn("live_metrics", context)

    def test_removed_observations_option_is_rejected(self) -> None:
        result = self.run_script("scripts/eval-agent-lightweight.py", "--observations", "unused.json")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_pressure_output_denies_real_host_and_copilot_execution_evidence(self) -> None:
        result = self.run_script(
            "scripts/eval-pressure-behavior.py",
            "--format",
            "json",
            "--output-dir",
            "none",
        )
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        source = (ROOT / "scripts/eval-pressure-behavior.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("fixture conformance only", source)
        self.assertIn("not real-host or Copilot execution evidence", source)

    def test_professional_static_evaluation_contract(self) -> None:
        report = load_owned_eval_report(
            self,
            ROOT,
            "reports/skill-professionalism-eval.json",
            {
                "evaluation_kind": "static-authoring-structure",
                "skills_checked": 189,
                "error_count": 0,
            },
        )
        self.assertEqual("static-authoring-structure", report["evaluation_kind"])
        self.assertEqual(189, report["skills_checked"])
        self.assertEqual(0, report["error_count"])


if __name__ == "__main__":
    unittest.main()
