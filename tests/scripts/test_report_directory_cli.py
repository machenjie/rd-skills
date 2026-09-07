from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load("report_dir_audit", "audit-skill-content.py")
INSTALLATION = _load("report_dir_installation", "validate-installation.py")
ROUTING = _load("report_dir_routing", "eval-routing.py")
LIGHTWEIGHT = _load("report_dir_lightweight", "eval-agent-lightweight.py")
RENDERED = _load("report_dir_rendered", "eval-rendered-context-budget.py")
CONTEXT = _load("report_dir_context", "eval-context-control-plane.py")
DOCS = _load("report_dir_docs", "validate-docs-consistency.py")


class ReportDirectoryCliTests(unittest.TestCase):
    def test_new_report_directory_cli_defaults_and_overrides(self) -> None:
        cases = (
            (AUDIT, ["--gate", "authoring"]),
            (INSTALLATION, []),
            (ROUTING, []),
            (RENDERED, []),
            (DOCS, []),
        )
        with tempfile.TemporaryDirectory() as raw:
            custom = Path(raw) / "producer-reports"
            for module, required in cases:
                with self.subTest(module=module.__name__):
                    default = module._args(required).reports_dir
                    self.assertEqual(module.ROOT, default.parent)
                    self.assertEqual("reports", default.name)
                    self.assertEqual(
                        custom,
                        module._args([*required, "--reports-dir", str(custom)]).reports_dir,
                    )

    def test_behavior_and_context_main_forward_report_directory(self) -> None:
        report = {
            "fixture_count": 1, "negative_fixture_count": 1,
            "status": "pass", "errors": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            paths = (output / "report.json", output / "report.md")
            for module in (LIGHTWEIGHT, CONTEXT):
                for argv, expected in (
                    ([], module.REPORT_JSON.parent),
                    (["--reports-dir", str(output / "custom")], output / "custom"),
                ):
                    with self.subTest(module=module.__name__, argv=argv), mock.patch.object(
                        module, "evaluate", return_value=report
                    ), mock.patch.object(
                        module, "report_output_paths", return_value=paths
                    ) as output_paths:
                        self.assertEqual(0, module.main(argv))
                        self.assertEqual(expected, output_paths.call_args.args[0])
                        self.assertTrue(paths[0].is_file())

    def test_new_producer_output_paths_follow_reports_directory(self) -> None:
        expected = (
            (AUDIT, "skill-content-audit.json", "skill-content-audit.md"),
            (INSTALLATION, "installation-validation.json", "installation-validation.md"),
            (ROUTING, "routing-eval.json", "routing-eval.md"),
            (LIGHTWEIGHT, "hookless-control-plane-eval.json", "hookless-control-plane-eval.md"),
            (RENDERED, "rendered-context-budget.json", "rendered-context-budget.md"),
            (CONTEXT, "context-control-plane-eval.json", "context-control-plane-eval.md"),
        )
        with tempfile.TemporaryDirectory() as raw:
            reports_dir = Path(raw) / "producer-reports"
            for module, json_name, markdown_name in expected:
                with self.subTest(module=module.__name__):
                    self.assertEqual(
                        (reports_dir / json_name, reports_dir / markdown_name),
                        module.report_output_paths(
                            reports_dir,
                            module.REPORT_JSON.name
                            if hasattr(module, "REPORT_JSON")
                            else module.JSON_REPORT.name,
                            module.REPORT_MD.name
                            if hasattr(module, "REPORT_MD")
                            else module.MARKDOWN_REPORT.name,
                        ),
                    )

    def test_docs_consumer_report_path_follows_reports_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir = Path(raw) / "producer-reports"
            self.assertEqual(
                reports_dir / "rendered-context-budget.json",
                DOCS._governance_budget_report_path(reports_dir),
            )


if __name__ == "__main__":
    unittest.main()
