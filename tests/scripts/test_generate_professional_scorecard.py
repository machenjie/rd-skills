from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-professional-scorecard.py"


def _write_release_config(
    root: Path,
    *,
    selected_license: str | None = None,
    contribution: bool = False,
    security: bool = False,
) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    license_value = "null" if selected_license is None else selected_license
    (root / "config" / "open-source-release.yaml").write_text(
        "schema_version: 1\n"
        "kind: changeforge.open_source_release\n"
        f"selected_license: {license_value}\n"
        f"contribution_licensing_confirmed: {str(contribution).lower()}\n"
        f"security_contact_confirmed: {str(security).lower()}\n"
        "dist_release_policy: release-artifact-only\n",
        encoding="utf-8",
    )


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("generate_professional_scorecard", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateProfessionalScorecardTests(unittest.TestCase):
    def test_missing_manifest_is_unknown_not_pass(self) -> None:
        module = _load_module()
        status, detail = module.profile_manifest_status(None, "recommended")
        self.assertEqual(status, "unknown")
        self.assertIn("not found", detail)

    def test_profile_manifest_count_mismatch_fails(self) -> None:
        module = _load_module()
        status, detail = module.profile_manifest_status(
            {
                "profile": "recommended",
                "top_level_skills": [],
                "professional_skills": [],
                "foundation_capabilities": [],
                "compiled_foundation_capabilities": [],
                "domain_extensions": [],
            },
            "recommended",
        )
        self.assertEqual(status, "fail")
        self.assertIn("top_level", detail)

    def test_foundation_needs_review_is_partial(self) -> None:
        module = _load_module()
        status = module._summary_status(
            "Foundation capability coverage",
            {"count": 40, "statuses": {"acceptable": 39, "needs-review": 1}},
        )
        self.assertEqual(status, "partial")

    def test_foundation_sample_grade_is_partial(self) -> None:
        module = _load_module()
        # Regression: public benchmark and scorecard must agree that sample-grade is partial evidence.
        status = module._summary_status(
            "Foundation capability coverage",
            {"count": 40, "statuses": {"acceptable": 39, "sample-grade": 1}},
        )
        self.assertEqual(status, "partial")

    def test_professional_sample_grade_is_partial(self) -> None:
        module = _load_module()
        # Regression: public benchmark and scorecard must agree that sample-grade is partial evidence.
        status = module._summary_status(
            "Professional skill coverage",
            {"count": 21, "statuses": {"sample-grade": 21}},
        )
        self.assertEqual(status, "partial")

    def test_professional_explicit_partial_status_is_partial(self) -> None:
        module = _load_module()
        status = module._summary_status(
            "Professional skill coverage",
            {"count": 21, "statuses": {"partial": 1, "acceptable": 20}},
        )
        self.assertEqual(status, "partial")

    def test_cli_writes_markdown_and_json(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "scorecard.md"
            json_path = Path(tmp) / "scorecard.json"
            result = module.main(["--out", str(md_path), "--json-out", str(json_path)])
            self.assertEqual(result, 0)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("dimensions", payload)
            self.assertIn("not_collected", payload["status_summary"])
            self.assertIn("# Professional Scorecard", md_path.read_text(encoding="utf-8"))

    def test_generated_scorecard_contains_runtime_evidence_dimensions(self) -> None:
        module = _load_module()
        payload = module.generate_scorecard(ROOT, ROOT / "reports")
        dimension_names = {dimension["name"] for dimension in payload["dimensions"]}

        # Regression: release evidence must keep runtime evidence gaps visible.
        self.assertIn("Executor adapter structural fixtures", dimension_names)
        self.assertIn("Activation precision benchmark", dimension_names)
        self.assertIn("Runtime telemetry fixture sample", dimension_names)
        self.assertIn("Live runtime telemetry sample", dimension_names)
        self.assertIn("Executor adapter live pass-rate", dimension_names)
        self.assertIn("Executor adapter token overhead", dimension_names)
        self.assertIn("Executor adapter turn overhead", dimension_names)

    def test_strict_profile_builds_rejects_unknown_manifest_dimension(self) -> None:
        module = _load_module()
        payload = {
            "dimensions": [
                {"name": "Registry source counts", "status": "pass"},
                {"name": "Profile build reproducibility", "status": "unknown"},
                {"name": "Example coverage", "status": "pass"},
                {"name": "Productization assets", "status": "pass"},
                {"name": "Hook safety", "status": "not_collected"},
                {"name": "Installation validation", "status": "not_collected"},
            ]
        }
        errors = module.strict_profile_build_errors(payload)
        self.assertTrue(any("Profile build reproducibility" in error for error in errors))

    def test_strict_profile_builds_allows_not_collected_release_dimensions(self) -> None:
        module = _load_module()
        payload = {
            "dimensions": [
                {"name": "Registry source counts", "status": "pass"},
                {"name": "Profile build reproducibility", "status": "pass"},
                {"name": "Example coverage", "status": "pass"},
                {"name": "Productization assets", "status": "pass"},
                {"name": "Hook safety", "status": "not_collected"},
                {"name": "Installation validation", "status": "not_collected"},
            ]
        }
        self.assertEqual(module.strict_profile_build_errors(payload), [])

    def test_example_coverage_uses_validate_examples_result(self) -> None:
        module = _load_module()
        module._load_validate_examples = lambda: SimpleNamespace(
            validate_examples=lambda root: ["examples/01 broken"]
        )
        with tempfile.TemporaryDirectory() as tmp:
            dimensions, _metadata = module.collect_dimensions(ROOT, Path(tmp))
        example_dimension = next(
            dimension for dimension in dimensions if dimension.name == "Example coverage"
        )
        self.assertEqual(example_dimension.status, "fail")
        self.assertIn("examples/01 broken", example_dimension.detail)

    def test_marketplace_index_status_uses_profile_validator(self) -> None:
        module = _load_module()
        module._load_validate_marketplace_index = lambda: SimpleNamespace(
            validate_profile=lambda root, profile: ["runtime path missing"] if profile == "dev" else []
        )
        status, detail = module.marketplace_index_status(ROOT)
        self.assertEqual(status, "fail")
        self.assertIn("dev", detail)
        self.assertIn("runtime path missing", detail)

    def test_executor_adapter_eval_status_preserves_not_collected_metrics(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "executor-adapter-eval.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "summary": {
                            "case_count": 15,
                            "passed": 15,
                            "failed": 0,
                            "coverage_targets": ["event_recognition"],
                            "pressure_cases": ["unknown_event"],
                            "live_pass_rate": {"status": "not_collected", "detail": "not measured"},
                            "token_overhead": {"status": "not_collected", "detail": "not measured"},
                            "turn_overhead": {"status": "not_collected", "detail": "not measured"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            status, detail = module.executor_adapter_eval_status(root)
            token_status, token_detail = module.executor_adapter_metric_status(root, "token_overhead")

        self.assertEqual(status, "pass")
        self.assertIn('"token_overhead": "not_collected"', detail)
        self.assertEqual(token_status, "not_collected")
        self.assertIn("not measured", token_detail)

    def test_runtime_telemetry_fixture_sample_status_requires_bounded_fields(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            missing_status, _missing_detail = module.runtime_telemetry_fixture_sample_status(root)
            (reports / "runtime-telemetry-sample.json").write_text(
                json.dumps(
                    {
                        "source": "deterministic-fixture-bounded-facts",
                        "sample_kind": "runtime_telemetry_fixture_sample",
                        "evidence_level": "runtime telemetry fixture sample",
                        "runtime": "mixed-fixture-runtime-sample",
                        "event_count": 15,
                        "normalized_event_kinds": ["edit"],
                        "degraded_event_count": 3,
                        "validation_freshness_cases": [],
                        "closure_verdicts": {"complete": 1},
                        "unsupported_checks": [],
                        "privacy_redaction_count": 2,
                        "token_overhead": {"status": "not_collected"},
                        "turn_overhead": {"status": "not_collected"},
                    }
                ),
                encoding="utf-8",
            )
            status, detail = module.runtime_telemetry_fixture_sample_status(root)

        self.assertEqual(missing_status, "not_collected")
        self.assertEqual(status, "pass")
        self.assertIn('"evidence_level": "runtime telemetry fixture sample"', detail)
        self.assertIn('"privacy_redaction_count": 2', detail)
        self.assertIn('"token_overhead": "not_collected"', detail)

    def test_live_runtime_telemetry_sample_rejects_fixture_source(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            missing_status, _missing_detail = module.live_runtime_telemetry_sample_status(root)
            (reports / "live-runtime-telemetry-sample.json").write_text(
                json.dumps(
                    {
                        "source": "deterministic-fixture-bounded-facts",
                        "sample_kind": "live_runtime_telemetry_sample",
                        "evidence_level": "live runtime telemetry sample",
                        "runtime": "codex",
                        "event_count": 1,
                        "normalized_event_kinds": ["edit"],
                        "privacy_redaction_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            status, detail = module.live_runtime_telemetry_sample_status(root)

        self.assertEqual(missing_status, "not_collected")
        self.assertEqual(status, "fail")
        self.assertIn("cannot use deterministic fixture source", detail)

    def test_validation_report_status_reads_machine_report(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            missing_status, _missing_detail = module.validation_report_status(
                root,
                "reports/hook-validation.json",
            )
            (reports / "hook-validation.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_by": "scripts/validate-hooks.py",
                        "status": "pass",
                        "errors": [],
                        "summary": {"error_count": 0},
                    }
                ),
                encoding="utf-8",
            )
            status, detail = module.validation_report_status(root, "reports/hook-validation.json")

        self.assertEqual(missing_status, "not_collected")
        self.assertEqual(status, "pass")
        self.assertIn('"error_count": 0', detail)

    def test_validation_report_status_fails_on_missing_fields(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "installation-validation.json").write_text(
                json.dumps({"status": "pass"}),
                encoding="utf-8",
            )
            status, detail = module.validation_report_status(
                root,
                "reports/installation-validation.json",
            )

        self.assertEqual(status, "fail")
        self.assertIn("missing validation report fields", detail)

    def test_validation_report_status_fails_on_inconsistent_status_and_errors(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "hook-validation.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_by": "scripts/validate-hooks.py",
                        "status": "pass",
                        "errors": ["stale manual report"],
                        "summary": {"error_count": 1},
                    }
                ),
                encoding="utf-8",
            )
            pass_status, pass_detail = module.validation_report_status(
                root,
                "reports/hook-validation.json",
            )
            (reports / "hook-validation.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_by": "scripts/validate-hooks.py",
                        "status": "fail",
                        "errors": [],
                        "summary": {"error_count": 0},
                    }
                ),
                encoding="utf-8",
            )
            fail_status, fail_detail = module.validation_report_status(
                root,
                "reports/hook-validation.json",
            )

        self.assertEqual(pass_status, "fail")
        self.assertIn("errors is non-empty", pass_detail)
        self.assertEqual(fail_status, "fail")
        self.assertIn("errors is empty", fail_detail)

    def test_evidence_levels_include_fixture_and_live_runtime_samples(self) -> None:
        module = _load_module()
        dimensions = [
            module.Dimension("Promoted agent samples", "pass", "report", "cmd", "fix", "detail"),
            module.Dimension("Runtime telemetry fixture sample", "pass", "report", "cmd", "fix", "detail"),
            module.Dimension("Live runtime telemetry sample", "not_collected", "report", "cmd", "fix", "detail"),
            module.Dimension("Executor adapter live pass-rate", "not_collected", "report", "cmd", "fix", "detail"),
            module.Dimension("Executor adapter token overhead", "not_collected", "report", "cmd", "fix", "detail"),
            module.Dimension("Executor adapter turn overhead", "not_collected", "report", "cmd", "fix", "detail"),
        ]
        levels = module._evidence_levels(dimensions)

        self.assertEqual(levels["runtime telemetry fixture sample"]["status"], "pass")
        self.assertEqual(levels["live runtime telemetry sample"]["status"], "not_collected")
        self.assertEqual(levels["live pass-rate"]["status"], "not_collected")
        self.assertEqual(levels["token overhead"]["status"], "not_collected")
        self.assertEqual(levels["turn overhead"]["status"], "not_collected")

    def test_open_source_readiness_no_license_is_partial(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_release_config(root)
            (root / "pyproject.toml").write_text('license = { text = "Proprietary" }\n', encoding="utf-8")
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "partial")
        self.assertIn("license_file=False", detail)

    def test_open_source_readiness_license_only_with_proprietary_metadata_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_release_config(root)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('license = { text = "Proprietary" }\n', encoding="utf-8")
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "fail")
        self.assertIn("pyproject_license_not_proprietary=False", detail)

    def test_open_source_readiness_license_and_metadata_without_security_is_partial(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_release_config(root)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('license = { text = "MIT" }\n', encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text(
                "## Contribution Licensing\nContributions are accepted under the repository license.\n",
                encoding="utf-8",
            )
            (root / "SECURITY.md").write_text(
                "Use GitHub private vulnerability reporting when it is enabled.\n",
                encoding="utf-8",
            )
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "partial")
        self.assertIn("security_contact_confirmed=False", detail)

    def test_open_source_readiness_license_pyproject_and_security_pass(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_release_config(root, selected_license="MIT", contribution=True, security=True)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('license = { text = "MIT" }\n', encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text(
                "## Contribution Licensing\nContributions are accepted under the repository license.\n",
                encoding="utf-8",
            )
            (root / "SECURITY.md").write_text(
                "GitHub private vulnerability reporting is enabled for this repository.\n",
                encoding="utf-8",
            )
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "pass")
        self.assertIn("security_contact_confirmed=True", detail)


if __name__ == "__main__":
    unittest.main()
