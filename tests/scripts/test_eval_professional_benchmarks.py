from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval-professional-benchmarks.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "eval_professional_benchmarks_contract",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_case(
    directory: Path,
    *,
    coverage_class: str | None = None,
    expected_status: str = "pass",
    baseline: str,
    with_skill: str,
) -> None:
    class_line = f"coverage_class: {coverage_class}\n" if coverage_class else ""
    (directory / "expected.yaml").write_text(
        class_line
        + "expected_stage: implementation-review\n"
        "expected_professional_skill: primary-skill\n"
        "expected_capabilities: [layer3-skill]\n"
        "expected_hidden_risks: [hidden risk one, hidden risk two]\n"
        "expected_evidence: [evidence one, evidence two]\n"
        "forbidden_behaviors: [unsafe shortcut one, unsafe shortcut two]\n"
        "expected_output_obligations: [output one, output two, output three]\n"
        f"expected_with_skill_status: {expected_status}\n",
        encoding="utf-8",
    )
    (directory / "prompt.md").write_text(
        "Review a concrete production boundary with enough detail to exercise the fixture contract.",
        encoding="utf-8",
    )
    (directory / "baseline_output.md").write_text(baseline, encoding="utf-8")
    (directory / "with_skill_output.md").write_text(with_skill, encoding="utf-8")


class ProfessionalBenchmarkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.professional = {"primary-skill": {"layer3-skill"}}
        cls.layer3 = {"layer3-skill"}
        cls.routable = {"primary-skill"}

    def test_positive_forbidden_behavior_hit_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_case(
                directory,
                baseline="unsafe shortcut one",
                with_skill=(
                    "primary-skill layer3-skill hidden risk one hidden risk two "
                    "evidence one evidence two output one output two output three "
                    "unsafe shortcut one"
                ),
            )
            result = self.module._case(
                directory,
                self.professional,
                self.layer3,
                self.routable,
                "comparison",
            )
        self.assertEqual("fail", result.comparison_status)
        self.assertTrue(result.forbidden_behavior_hits)
        self.assertTrue(any("forbidden behavior" in item for item in result.errors))

    def test_release_critical_requires_full_coverage_and_unsafe_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_case(
                directory,
                coverage_class="release-critical",
                baseline="plausible but incomplete baseline",
                with_skill=(
                    "primary-skill layer3-skill hidden risk one "
                    "evidence one evidence two output one output two output three"
                ),
            )
            result = self.module._case(
                directory,
                self.professional,
                self.layer3,
                self.routable,
                "comparison",
            )
        self.assertEqual("fail", result.comparison_status)
        joined = "\n".join(result.errors)
        self.assertIn("every expected hidden risk", joined)
        self.assertIn("baseline must contain at least one forbidden behavior", joined)

    def test_adversarial_negative_control_is_classified_separately(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_case(
                directory,
                expected_status="fail",
                baseline="unsafe shortcut one",
                with_skill="unsafe shortcut two",
            )
            result = self.module._case(
                directory,
                self.professional,
                self.layer3,
                self.routable,
                "comparison",
            )
        self.assertEqual("adversarial-negative-control", result.coverage_class)
        self.assertEqual("fail", result.expected_status)
        self.assertEqual("expected-fail-detected", result.comparison_status)

    def test_schema_rejects_repeated_or_cross_group_obligations(self) -> None:
        mutations = (
            ("evidence two", "Evidence-one", "must not repeat normalized obligations"),
            ("output three", "hidden risk one", "distinct across"),
            (
                "unsafe shortcut one",
                "hidden risk one",
                "forbidden behaviors must be distinct",
            ),
        )
        for before, after, message in mutations:
            with self.subTest(mutation=(before, after)), tempfile.TemporaryDirectory() as raw:
                directory = Path(raw)
                _write_case(
                    directory,
                    baseline="unsafe shortcut one",
                    with_skill="complete captured output",
                )
                path = directory / "expected.yaml"
                path.write_text(
                    path.read_text(encoding="utf-8").replace(before, after),
                    encoding="utf-8",
                )
                result = self.module._case(
                    directory,
                    self.professional,
                    self.layer3,
                    self.routable,
                    "comparison",
                )
            self.assertEqual("fail", result.schema_status)
            self.assertTrue(any(message in item for item in result.errors), result.errors)

    def test_schema_requires_expected_stage(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_case(
                directory,
                baseline="unsafe shortcut one",
                with_skill="complete captured output",
            )
            path = directory / "expected.yaml"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "expected_stage: implementation-review\n", ""
                ),
                encoding="utf-8",
            )
            result = self.module._case(
                directory,
                self.professional,
                self.layer3,
                self.routable,
                "comparison",
            )
        self.assertEqual("fail", result.schema_status)
        self.assertIn("expected_stage must be a non-blank string", result.errors)

    def test_repository_release_critical_cases_pass(self) -> None:
        payload = self.module.evaluate_benchmarks()
        release = [
            row
            for row in payload["results"]
            if row["coverage_class"] == "release-critical"
        ]
        self.assertEqual(4, len(release))
        self.assertTrue(all(row["comparison_status"] == "pass" for row in release))
        self.assertTrue(all(row["baseline_forbidden_behavior_hits"] for row in release))
        self.assertTrue(all(not row["forbidden_behavior_hits"] for row in release))

    def test_repository_domain_cases_are_unique_complete_and_passing(self) -> None:
        payload = self.module.evaluate_benchmarks()
        domain_names = {
            "ai-product-extension",
            "bigdata-product-extension",
            "iot-embedded-extension",
            "low-level-systems-extension",
            "android-platform-extension",
            "payment-trading-extension",
            "web3-product-extension",
        }
        domain_cases = [
            row
            for row in payload["results"]
            if domain_names.intersection(row["layer3_skills"])
        ]

        self.assertEqual(7, len(domain_cases))
        self.assertEqual(
            7,
            len({row["case_id"] for row in domain_cases}),
        )
        selected_domains = [
            name
            for row in domain_cases
            for name in row["layer3_skills"]
            if name in domain_names
        ]
        self.assertEqual(domain_names, set(selected_domains))
        self.assertEqual(7, len(selected_domains))

        for row in domain_cases:
            with self.subTest(case=row["case_id"]):
                expected = self.module.load_yaml_file(
                    ROOT / row["case_id"] / "expected.yaml"
                )
                self.assertEqual("standard", row["coverage_class"])
                self.assertEqual("pass", row["schema_status"])
                self.assertEqual("pass", row["comparison_status"])
                self.assertTrue(row["baseline_forbidden_behavior_hits"])
                self.assertFalse(row["forbidden_behavior_hits"])
                self.assertEqual(
                    expected["expected_hidden_risks"],
                    row["covered_hidden_risks"],
                )
                self.assertEqual(
                    expected["expected_evidence"],
                    row["covered_evidence"],
                )
                self.assertEqual(
                    expected["expected_output_obligations"],
                    row["covered_output_obligations"],
                )
                for field in (
                    "expected_hidden_risks",
                    "expected_evidence",
                    "forbidden_behaviors",
                    "expected_output_obligations",
                ):
                    self.assertGreaterEqual(len(expected[field]), 3)


if __name__ == "__main__":
    unittest.main()
