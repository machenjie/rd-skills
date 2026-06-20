from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-public-benchmark-summary.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("generate_public_benchmark_summary", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GeneratePublicBenchmarkSummaryTests(unittest.TestCase):
    def test_missing_evidence_is_unknown_or_not_collected(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            payload = module.generate_summary(root)

        statuses = {item["name"]: item["status"] for item in payload["items"]}
        self.assertEqual(statuses["Release readiness"], "unknown")
        self.assertEqual(statuses["Installation validation"], "not_collected")
        self.assertEqual(statuses["Marketplace index validation"], "unknown")
        self.assertNotIn("pass", {statuses["Release readiness"], statuses["Installation validation"]})

    def test_committed_summary_uses_stable_source_commit_label(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            payload = module.generate_summary(root)

        # Regression: committed snapshots must not go stale when HEAD changes after generation.
        self.assertEqual(payload["repository"]["source_commit"], module.COMMITTED_SOURCE_COMMIT)

    def test_release_artifact_can_supply_source_commit(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            payload = module.generate_summary(root, source_commit="abc1234")

        self.assertEqual(payload["repository"]["source_commit"], "abc1234")

    def test_marketplace_status_comes_from_scorecard(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            (root / "reports").mkdir()
            (root / "reports" / "professional-scorecard.json").write_text(
                "{\n"
                "  \"dimensions\": [\n"
                "    {\n"
                "      \"name\": \"Marketplace index validation\",\n"
                "      \"status\": \"pass\",\n"
                "      \"detail\": \"all profiles validate\",\n"
                "      \"verification_command\": \"python3 scripts/validate-marketplace-index.py --profile recommended\"\n"
                "    }\n"
                "  ]\n"
                "}\n",
                encoding="utf-8",
            )
            payload = module.generate_summary(root)

        # Regression: public summary and scorecard dashboard must report the same marketplace dimension.
        marketplace = next(item for item in payload["items"] if item["name"] == "Marketplace index validation")
        self.assertEqual(marketplace["status"], "pass")
        self.assertEqual(marketplace["source"], "reports/professional-scorecard.json")
        self.assertIn("all profiles validate", marketplace["detail"])

    def test_executor_adapter_statuses_come_from_scorecard_without_live_claims(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            (root / "reports").mkdir()
            (root / "reports" / "professional-scorecard.json").write_text(
                json.dumps(
                    {
                        "dimensions": [
                            {
                                "name": "Executor adapter structural fixtures",
                                "status": "pass",
                                "detail": "case_count=15",
                                "verification_command": "python3 scripts/eval-executor-adapters.py",
                            },
                            {
                                "name": "Activation precision benchmark",
                                "status": "pass",
                                "detail": "all activation metrics pass",
                                "verification_command": "python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks",
                            },
                            {
                                "name": "Runtime telemetry fixture sample",
                                "status": "pass",
                                "detail": "sanitized sample generated",
                                "verification_command": "python3 scripts/eval-executor-adapters.py",
                            },
                            {
                                "name": "Live runtime telemetry sample",
                                "status": "not_collected",
                                "detail": "not collected",
                                "verification_command": "manual live runtime collection",
                            },
                            {
                                "name": "Executor adapter live pass-rate",
                                "status": "not_collected",
                                "detail": "not measured",
                                "verification_command": "python3 scripts/eval-executor-adapters.py",
                            },
                            {
                                "name": "Executor adapter token overhead",
                                "status": "not_collected",
                                "detail": "not measured",
                                "verification_command": "python3 scripts/eval-executor-adapters.py",
                            },
                            {
                                "name": "Executor adapter turn overhead",
                                "status": "not_collected",
                                "detail": "not measured",
                                "verification_command": "python3 scripts/eval-executor-adapters.py",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            payload = module.generate_summary(root)

        items = {item["name"]: item for item in payload["items"]}
        self.assertEqual(items["Executor adapter structural fixtures"]["status"], "pass")
        self.assertEqual(items["Activation precision benchmark"]["status"], "pass")
        self.assertEqual(items["Runtime telemetry fixture sample"]["evidence_level"], "runtime telemetry fixture sample")
        self.assertEqual(items["Runtime telemetry fixture sample"]["status"], "pass")
        self.assertEqual(items["Live runtime telemetry sample"]["evidence_level"], "live runtime telemetry sample")
        self.assertEqual(items["Live runtime telemetry sample"]["status"], "not_collected")
        self.assertEqual(items["Executor adapter live pass-rate"]["status"], "not_collected")
        self.assertEqual(items["Executor adapter live pass-rate"]["evidence_level"], "live pass-rate")
        self.assertEqual(items["Executor adapter token overhead"]["evidence_level"], "token overhead")
        self.assertEqual(items["Executor adapter turn overhead"]["evidence_level"], "turn overhead")
        self.assertEqual(items["Installation validation"]["evidence_level"], "structural fixture")

    def test_known_unknowns_include_evidence_level_statuses(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            (root / "reports").mkdir()
            (root / "reports" / "professional-scorecard.json").write_text(
                json.dumps(
                    {
                        "dimensions": [
                            {"name": "Hook safety", "status": "pass", "detail": "ok"},
                            {
                                "name": "Installation validation",
                                "status": "not_collected",
                                "detail": "report missing",
                            },
                            {"name": "Skill efficacy structural fixtures", "status": "pass", "detail": "ok"},
                            {"name": "Runtime governance structural fixtures", "status": "pass", "detail": "ok"},
                            {"name": "Executor adapter structural fixtures", "status": "pass", "detail": "ok"},
                            {"name": "Activation precision benchmark", "status": "pass", "detail": "ok"},
                            {"name": "Runtime telemetry fixture sample", "status": "pass", "detail": "ok"},
                            {"name": "Live runtime telemetry sample", "status": "not_collected", "detail": "not collected"},
                            {
                                "name": "Executor adapter live pass-rate",
                                "status": "not_collected",
                                "detail": "not measured",
                            },
                            {
                                "name": "Executor adapter token overhead",
                                "status": "not_collected",
                                "detail": "not measured",
                            },
                            {
                                "name": "Executor adapter turn overhead",
                                "status": "not_collected",
                                "detail": "not measured",
                            },
                            {"name": "Marketplace index validation", "status": "pass", "detail": "ok"},
                        ],
                        "evidence_levels": {
                            "structural fixture": {"status": "pass", "meaning": "local fixtures"},
                            "runtime telemetry fixture sample": {"status": "pass", "meaning": "fixture sample present"},
                            "live runtime telemetry sample": {"status": "not_collected", "meaning": "sample missing"},
                            "promoted golden case": {"status": "pass", "meaning": "promoted"},
                            "live pass-rate": {"status": "not_collected", "meaning": "not measured"},
                            "token overhead": {"status": "not_collected", "meaning": "not measured"},
                            "turn overhead": {"status": "not_collected", "meaning": "not measured"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            payload = module.generate_summary(root)

        self.assertIn("Live runtime telemetry sample", payload["known_unknowns"])
        self.assertNotIn("Runtime telemetry fixture sample", payload["known_unknowns"])
        self.assertIn("Live pass-rate", payload["known_unknowns"])
        self.assertIn("Token overhead", payload["known_unknowns"])
        self.assertIn("Turn overhead", payload["known_unknowns"])
        self.assertIn("Installation validation", payload["known_unknowns"])
        self.assertNotIn("Executor adapter live pass-rate", payload["known_unknowns"])

    def test_cli_scorecard_argument_controls_scorecard_source(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            out = root / "summary.md"
            json_out = root / "summary.json"
            external_scorecard = Path(tmp) / "professional-scorecard.json"
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            (root / "reports").mkdir()
            (root / "reports" / "professional-scorecard.json").write_text(
                "{\n"
                "  \"dimensions\": [\n"
                "    {\n"
                "      \"name\": \"Marketplace index validation\",\n"
                "      \"status\": \"pass\",\n"
                "      \"detail\": \"committed snapshot\",\n"
                "      \"verification_command\": \"python3 scripts/validate-marketplace-index.py --profile recommended\"\n"
                "    }\n"
                "  ]\n"
                "}\n",
                encoding="utf-8",
            )
            external_scorecard.write_text(
                "{\n"
                "  \"dimensions\": [\n"
                "    {\n"
                "      \"name\": \"Marketplace index validation\",\n"
                "      \"status\": \"fail\",\n"
                "      \"detail\": \"current CI scorecard\",\n"
                "      \"verification_command\": \"python3 scripts/validate-marketplace-index.py --profile dev\"\n"
                "    }\n"
                "  ]\n"
                "}\n",
                encoding="utf-8",
            )
            old_root = module.ROOT
            module.ROOT = root
            try:
                self.assertEqual(
                    module.main(
                        [
                            "--scorecard",
                            str(external_scorecard),
                            "--out",
                            str(out),
                            "--json-out",
                            str(json_out),
                        ]
                    ),
                    0,
                )
            finally:
                module.ROOT = old_root

            # Regression: CI must be able to base public benchmark output on the freshly generated scorecard.
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            marketplace = next(item for item in payload["items"] if item["name"] == "Marketplace index validation")
            self.assertEqual(marketplace["status"], "fail")
            self.assertEqual(marketplace["source"], str(external_scorecard))
            self.assertIn("current CI scorecard", marketplace["detail"])

    def test_markdown_states_claim_boundary(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            markdown = module.render_markdown(module.generate_summary(root))

        self.assertIn("local deterministic ChangeForge evidence", markdown)
        self.assertIn("does not claim external popularity", markdown)
        self.assertIn("## Known Unknowns / Not Collected", markdown)

    def test_check_mode_catches_stale_outputs(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "summary.md"
            json_out = root / "summary.json"
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            out.write_text("stale\n", encoding="utf-8")
            json_out.write_text("{}\n", encoding="utf-8")
            old_root = module.ROOT
            module.ROOT = root
            try:
                self.assertEqual(
                    module.main(["--check", "--out", str(out), "--json-out", str(json_out)]),
                    1,
                )
                self.assertEqual(module.main(["--out", str(out), "--json-out", str(json_out)]), 0)
                self.assertEqual(
                    module.main(["--check", "--out", str(out), "--json-out", str(json_out)]),
                    0,
                )
            finally:
                module.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
