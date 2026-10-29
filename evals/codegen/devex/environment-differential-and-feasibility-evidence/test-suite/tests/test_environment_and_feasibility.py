from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import unittest

ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def subject():
    spec = importlib.util.spec_from_file_location("candidate_evidence_checks", ROOT / "evidence_checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment(terminal="fail"):
    return {
        "code": "app-v1", "case": "integration-7", "input": "payload-v2",
        "resolved_executable": "/tool/bin/runtime", "path": ["/tool/bin", "/usr/bin"],
        "cwd": "/workspace", "architecture": "arm64", "runtime": "3.11", "compiler": "clang-17",
        "dependency_graph": [["app", "parser@2"], ["parser@2", "codec@1"]],
        "env_layers": [{"source": "base", "values": {"MODE": "strict", "PORT": "8080"}},
                       {"source": "job", "values": {"MODE": "legacy"}}],
        "env_precedence": ["base", "job"], "certificates": ["root-a", "root-b"],
        "proxy": "none", "ports": {"api": 8080}, "permissions": ["read:data", "bind:8080"],
        "services": {"database": "ready-v1"}, "terminal": terminal, "failure": "parse-empty",
    }


def intervention(before, after, method="controlled"):
    return {"method": method, "before": deepcopy(before), "after": deepcopy(after), "replay": deepcopy(before)}


def feasibility():
    plan = {
        "hypothesis": {"metric": "latency", "maximum_ratio": 0.8, "refutation": "ratio-above-limit"},
        "independent_variable": "transport", "baseline_value": "poll", "candidate_value": "stream",
        "fixed_factors": {"dataset": "fixture-v3", "architecture": "arm64"},
        "versions": {"app": "v1", "compiler": "17"}, "input_ids": ["small", "large"],
        "required_boundaries": ["serialize", "real-wire", "receive"],
        "minimum_pairs": 2, "maximum_pairs": 2, "stop_on_refutation": True,
        "budget": {"elapsed": 20, "cost": 12, "memory": 64},
        "limits": ["No production load evidence.", "No architecture suitability decision."],
    }
    def run(role, input_id, latency):
        return {
            "input": input_id, "factors": dict(plan["fixed_factors"], transport=role),
            "versions": dict(plan["versions"]), "boundary_trace": ["serialize", "real-wire", "receive"],
            "terminal": "completed", "metrics": {"latency": latency},
            "elapsed": 4 if role == "poll" else 3, "cost": 2 if role == "poll" else 3, "memory": 32,
        }
    pairs = [{"id": str(i), "baseline": run("poll", name, baseline),
              "candidate": run("stream", name, candidate)}
             for i, (name, baseline, candidate) in enumerate([("small", 20, 12), ("large", 100, 70)])]
    return plan, {"pairs": pairs, "stop_reason": "planned"}


class EnvironmentFeasibilityAssertions(unittest.TestCase):
    def test_one_person_ci_delta_is_hypothesis_until_isolated_and_replayed(self):
        local, ci = environment(), environment("pass")
        ci["runtime"] = "3.12"
        original = deepcopy((local, ci))
        unproved = subject().diagnose_environment(local, ci, [])
        self.assertEqual(unproved["differences"], {"runtime"})
        self.assertEqual(unproved["hypotheses"], {"toolchain"})
        self.assertEqual(unproved["status"], "inconclusive")
        self.assertIsNone(unproved["verified_cause"])
        proved = subject().diagnose_environment(local, ci, [intervention(local, ci)])
        self.assertEqual((proved["status"], proved["verified_cause"], proved["verified_change"]),
                         ("verified", "toolchain", "runtime"))
        self.assertEqual((local, ci), original)

    def test_code_minimal_reproduction_and_environment_precedence_are_distinct(self):
        bad, good = environment(), environment("pass")
        good["code"] = "app-v2"
        trial = intervention(bad, good, "minimal-reproduction")
        for key in ("before", "after", "replay"):
            trial[key].update(case="minimal-parse", input="empty-bytes")
        result = subject().diagnose_environment(bad, good, [trial])
        self.assertEqual((result["verified_cause"], result["verified_change"]), ("application", "code"))
        configured = environment("pass")
        configured["env_precedence"] = ["job", "base"]
        result = subject().diagnose_environment(bad, configured, [intervention(bad, configured)])
        self.assertEqual(result["differences"], {"env:MODE"})
        self.assertEqual(result["verified_cause"], "configuration")
        normalized = deepcopy(bad)
        normalized["env_layers"].reverse()
        normalized["dependency_graph"].reverse()
        normalized["permissions"].reverse()
        normalized["certificates"].reverse()
        self.assertEqual(subject().diagnose_environment(bad, normalized, [])["status"], "equivalent")
        normalized["env_precedence"] = ["base", "missing"]
        with self.assertRaises(ValueError):
            subject().diagnose_environment(bad, normalized, [])

    def test_observed_execution_dependencies_and_external_configuration_are_compared(self):
        variants = {
            "resolved_executable": ("/other/bin/runtime", "toolchain"),
            "path": (["/usr/bin", "/tool/bin"], "configuration"),
            "cwd": ("/other-workspace", "configuration"),
            "architecture": ("x86_64", "toolchain"),
            "compiler": ("clang-18", "toolchain"),
            "dependency_graph": ([["app", "parser@3"], ["parser@3", "codec@1"]], "toolchain"),
            "certificates": (["root-c"], "configuration"),
            "proxy": ("fixture-proxy", "configuration"),
            "ports": ({"api": 9090}, "configuration"),
            "permissions": (["read:data"], "configuration"),
            "services": ({"database": "unavailable"}, "configuration"),
        }
        for key, (value, category) in variants.items():
            with self.subTest(field=key):
                left, right = environment(), environment("pass")
                right[key] = value
                result = subject().diagnose_environment(left, right, [])
                self.assertEqual(result["differences"], {key})
                self.assertEqual(result["hypotheses"], {category})
                self.assertIsNone(result["verified_cause"])
                # The category follows the changed observed fact, not an input cause flag.
                result = subject().diagnose_environment(left, right, [intervention(left, right)])
                self.assertEqual((result["verified_cause"], result["verified_change"]), (category, key))

    def test_uncontrolled_changes_cleanup_actions_and_unlinked_trials_remain_inconclusive(self):
        left, right = environment(), environment("pass")
        right.update(runtime="3.12", cwd="/other-workspace")
        result = subject().diagnose_environment(left, right, [intervention(left, right)])
        self.assertEqual(result["status"], "inconclusive")
        self.assertIn("uncontrolled-change", result["issues"])
        for action in ("reinstall", "delete-lock", "clear-cache"):
            trial = intervention(left, environment("pass"))
            trial["operation"] = action
            result = subject().diagnose_environment(left, environment("pass"), [trial])
            self.assertIsNone(result["verified_cause"])
        right = environment("pass")
        right["runtime"] = "3.12"
        trial = intervention(left, right)
        trial["replay"]["terminal"] = "pass"
        self.assertIn("unreproduced-intervention", subject().diagnose_environment(left, right, [trial])["issues"])
        trial = intervention(left, right)
        trial["before"]["code"] = "unrelated-app"
        self.assertIsNone(subject().diagnose_environment(left, right, [trial])["verified_cause"])
        right["input"] = "different-payload"
        self.assertIn("incomparable-workload", subject().diagnose_environment(left, right, [])["issues"])

    def test_bounded_positive_uses_paired_ratios_resource_arithmetic_and_prototype_limits(self):
        plan, record = feasibility()
        before = deepcopy((plan, record))
        result = subject().evaluate_feasibility(plan, record)
        self.assertEqual(result["ratios"], [12 / 20, 70 / 100])
        self.assertEqual((result["elapsed"], result["cost"], result["memory"]), (4 + 3 + 4 + 3, 2 + 3 + 2 + 3, 32))
        self.assertEqual((result["decision"], result["issues"]), ("promote", set()))
        self.assertEqual(result["scope"], "prototype-only")
        self.assertEqual(result["limits"], tuple(plan["limits"]))
        self.assertEqual((plan, record), before)
        plan["budget"] = {"elapsed": 14, "cost": 10, "memory": 32}
        self.assertEqual(subject().evaluate_feasibility(plan, record)["decision"], "promote")

    def test_runnable_demo_must_cross_the_declared_boundary_with_comparable_inputs(self):
        changes = [
            ("factors", {"dataset": "different-data", "architecture": "arm64", "transport": "stream"}, "incomparable-baseline"),
            ("versions", {"app": "v2", "compiler": "17"}, "version-drift"),
            ("boundary_trace", ["serialize", "mock-wire", "receive"], "missing-boundary"),
            ("input", "other-input", "incomparable-input"),
            ("terminal", "aborted", "incomplete-trial"),
            ("metrics", {"latency": float("nan")}, "invalid-measurement"),
        ]
        for field, value, issue in changes:
            with self.subTest(field=field):
                plan, record = feasibility()
                record["pairs"][0]["candidate"][field] = value
                result = subject().evaluate_feasibility(plan, record)
                self.assertEqual(result["decision"], "retain")
                self.assertIn(issue, result["issues"])
        plan, record = feasibility()
        plan["hypothesis"]["refutation"] = "looks-promising"
        with self.assertRaises(ValueError):
            subject().evaluate_feasibility(plan, record)

    def test_budget_exhaustion_and_unplanned_early_stop_do_not_promote(self):
        plan, record = feasibility()
        record["pairs"] = record["pairs"][:1]
        record["stop_reason"] = "budget"
        plan["budget"]["elapsed"] = 7
        result = subject().evaluate_feasibility(plan, record)
        self.assertEqual(result["decision"], "retain")
        self.assertTrue({"budget-exhausted", "insufficient-pairs", "missing-input"} <= result["issues"])
        plan, record = feasibility()
        record["pairs"] = record["pairs"][:1]
        result = subject().evaluate_feasibility(plan, record)
        self.assertEqual(result["decision"], "retain")
        self.assertIn("early-stop", result["issues"])
        for field, limit in [("elapsed", 13), ("cost", 9), ("memory", 31)]:
            plan, record = feasibility()
            plan["budget"][field] = limit
            self.assertIn("over-budget", subject().evaluate_feasibility(plan, record)["issues"])

    def test_falsification_can_stop_early_but_later_observations_violate_the_plan(self):
        plan, record = feasibility()
        record["pairs"][0]["candidate"]["metrics"]["latency"] = 18
        first = {"pairs": record["pairs"][:1], "stop_reason": "refuted"}
        result = subject().evaluate_feasibility(plan, first)
        self.assertGreater(18 / 20, plan["hypothesis"]["maximum_ratio"])
        self.assertEqual((result["decision"], result["issues"]), ("discard", set()))
        record["stop_reason"] = "refuted"
        result = subject().evaluate_feasibility(plan, record)
        self.assertEqual(result["decision"], "retain")
        self.assertIn("continued-after-stop", result["issues"])
        plan, record = feasibility()
        record["pairs"].append(deepcopy(record["pairs"][0]))
        result = subject().evaluate_feasibility(plan, record)
        self.assertTrue({"continued-after-stop", "duplicate-pair"} <= result["issues"])
        self.assertEqual(result["decision"], "retain")


if __name__ == "__main__":
    unittest.main()
