from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
        result = self.run_script("scripts/eval-routing.py")
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        report = json.loads((ROOT / "reports/routing-eval.json").read_text())
        self.assertEqual(6, report["schema_version"])
        self.assertEqual("pass", report["status"])
        self.assertEqual(report["case_count"], report["passed_count"])
        self.assertEqual(report["case_count"], len(report["results"]))
        self.assertEqual(69, report["negative_case_count"])
        self.assertEqual(44, report["domain_family_case_count"])
        self.assertEqual(26, report["domain_anti_case_count"])
        self.assertEqual(13, report["domain_transition_case_count"])
        self.assertEqual(14, report["domain_unchanged_case_count"])
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

    def test_observable_trajectory_and_context_evaluations(self) -> None:
        for script in (
            "scripts/eval-agent-lightweight.py",
            "scripts/eval-rendered-context-budget.py",
            "scripts/eval-context-control-plane.py",
        ):
            result = self.run_script(script)
            self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        report = json.loads((ROOT / "reports/hookless-control-plane-eval.json").read_text())
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
        self.assertEqual("deterministic-fixtures", report["evidence_scope"])
        self.assertTrue(any("wall-clock performance" in item for item in report["limitations"]))
        self.assertTrue(any("real-host accuracy" in item for item in report["limitations"]))
        self.assertTrue(any("installed user experience" in item for item in report["limitations"]))
        self.assertNotIn("live_observations", report)
        self.assertNotIn("adoption_threshold_status", report)
        self.assertNotIn("efficiency_improvement_claim", report)

        rendered = json.loads((ROOT / "reports/rendered-context-budget.json").read_text())
        self.assertEqual("pass", rendered["status"])
        self.assertEqual("deterministic-rendered-artifacts", rendered["evidence_scope"])
        self.assertEqual("ai-consumption-v1", rendered["compiled_layer3_format"])
        self.assertEqual("o200k_base", rendered["tokenizer"])
        self.assertEqual(report["fixture_count"], rendered["fixture_count"])
        self.assertEqual(rendered["dispatch_count"] * 9, rendered["measurement_count"])
        self.assertEqual([], rendered["budget_calibration"]["relaxations"])
        self.assertEqual(
            1980,
            rendered["budget_calibration"]["release_targets"]["main"],
        )
        self.assertEqual(
            80,
            rendered["budget_calibration"]["minimum_release_margin_tokens"][
                "main"
            ],
        )
        self.assertEqual(
            1900,
            rendered["budget_calibration"]["evolution_targets"]["main"],
        )
        self.assertEqual(
            rendered["budget_calibration"]["evolution_targets"],
            rendered["budget_calibration"]["frozen_gates"],
        )
        self.assertGreaterEqual(
            rendered["aggregate"]["max_main"]["release_margin_tokens"],
            rendered["aggregate"]["max_main"][
                "minimum_release_margin_tokens"
            ],
        )
        self.assertLessEqual(
            rendered["aggregate"]["max_duplicate_rule_token_ratio"],
            rendered["budget_calibration"]["duplicate_rule_token_ratio_max"],
        )

        context = json.loads((ROOT / "reports/context-control-plane-eval.json").read_text())
        self.assertEqual("pass", context["status"])
        self.assertEqual("deterministic-fixtures", context["evidence_scope"])
        self.assertTrue(set(report["limitations"]).issubset(context["limitations"]))
        self.assertEqual(rendered["aggregate"], context["rendered_context_summary"])
        self.assertNotIn("safe_parallel_writes", context["checks"])
        self.assertTrue(context["checks"]["current_read_only_parallelism_declared"])
        self.assertTrue(context["checks"]["current_write_parallelism_unsupported"])
        self.assertTrue(context["checks"]["shared_workspace_serial_write"])
        self.assertTrue(context["checks"]["conditional_isolated_write_contract"])
        self.assertTrue(context["checks"]["utility_no_edit_workspace_gate"])
        self.assertNotIn("live_metrics", context)

    def test_removed_observations_option_is_rejected(self) -> None:
        result = self.run_script("scripts/eval-agent-lightweight.py", "--observations", "unused.json")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_professional_static_evaluation_contract(self) -> None:
        result = self.run_script("scripts/eval-skill-professionalism.py")
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        report = json.loads((ROOT / "reports/skill-professionalism-eval.json").read_text())
        self.assertEqual("static-authoring-structure", report["evaluation_kind"])
        self.assertEqual(190, report["skills_checked"])
        self.assertEqual(0, report["error_count"])


if __name__ == "__main__":
    unittest.main()
