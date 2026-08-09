from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from tests.scripts.affected_test_support import core_fixture_symbols


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVALUATOR = _load(
    "affected_skill_professionalism",
    SCRIPTS / "eval-skill-professionalism.py",
)
REGRESSION = _load(
    "affected_professionalism_regression",
    SCRIPTS / "validate-professionalism-regression.py",
)
CORE = _load(
    "affected_core_principles_context",
    SCRIPTS / "eval-core-principles.py",
)
import impact_graph  # noqa: E402


_CORE_FIXTURES, PROCESS_PASS = core_fixture_symbols()


def _context(*, scope: str = "packages", ids: list[str] | None = None) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "mode": "affected",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "professionalism": {
                "scope": scope,
                "direct_package_ids": ids or [],
                "reason_chains": [],
            },
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _write_partial_reports(
    directory: Path,
    *,
    direct: list[str],
    fresh: list[str],
    carried: list[str],
    baseline_stale_no_carry: bool = False,
    unevaluated: list[str] | None = None,
) -> dict[str, object]:
    unevaluated = unevaluated or []
    execution_scope = {
        "mode": "affected",
        "direct_package_ids": direct,
        "fresh_package_ids": fresh,
        "carried_package_ids": carried,
        "unevaluated_package_ids": unevaluated,
        "baseline_stale_no_carry": baseline_stale_no_carry,
        "baseline_decision": "evals/expert-panel/prior/panel/decision.json",
        "reasons_by_package": {
            package_id: (["own-material-changed"] if package_id in fresh else [])
            for package_id in sorted(fresh + carried + unevaluated)
        },
        "reason_chains": [],
        "control_skill_checked": False,
    }
    results = [
        {"name": package_id, "status": "pass", "errors": []}
        for package_id in fresh
    ]
    payloads = {
        "skill-professionalism-eval.json": {
            "schema_version": 2,
            "architecture": "hookless-control-plane",
            "execution_scope": execution_scope,
            "skills_checked": len(fresh),
            "error_count": 0,
            "errors": [],
            "results": results,
        },
        "skill-professionalism-depth.json": {
            "schema_version": 2,
            "execution_scope": execution_scope,
            "errors": [],
            "results": results,
        },
        "professional-coverage-matrix.json": {
            "schema_version": 3,
            "architecture": "hookless-control-plane",
            "evaluation_kind": "affected-static-authoring-evidence",
            "execution_scope": execution_scope,
            "errors": [],
            "rows": [],
            "gate_summary": {
                "required_skill_count": 0,
                "pass_count": 0,
                "fail_count": 0,
                "not_required_count": len(fresh),
            },
        },
    }
    for name, payload in payloads.items():
        (directory / name).write_text(json.dumps(payload), encoding="utf-8")
    return execution_scope


class AffectedProfessionalismTests(unittest.TestCase):
    def test_real_eight_producer_chain_accepts_isolated_partial_evidence_once(self) -> None:
        selected_ids = [
            "audit-skill-content",
            "eval-skill-professionalism",
            "eval-professional-benchmarks",
            "eval-routing",
            "validate-professional-routing",
            "eval-professional-samples",
            "eval-pressure-behavior",
            "validate-professionalism-regression",
        ]
        context = json.loads(_context(scope="full"))
        with tempfile.TemporaryDirectory() as raw:
            repository = Path(raw) / "repository"
            shutil.copytree(
                ROOT,
                repository,
                ignore=shutil.ignore_patterns(
                    ".git", "dist", "__pycache__", ".pytest_cache"
                ),
            )
            contract = json.loads(
                (repository / "src/control-model/core-contracts.json").read_text()
            )
            audit_fixture = repository / "scripts/fixture-pass-content-audit.py"
            audit_fixture.write_text(
                "from pathlib import Path\n"
                "path = Path('reports/skill-content-audit.json')\n"
                "path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')\n",
                encoding="utf-8",
            )
            audit_producer = next(
                row
                for row in contract["principle_acceptance_contract"]["producers"]
                if row["id"] == "audit-skill-content"
            )
            audit_producer["argv"] = [
                "python3",
                "scripts/fixture-pass-content-audit.py",
            ]
            markdown_before = {
                path.relative_to(repository).as_posix(): path.read_bytes()
                for path in (repository / "reports").glob("*.md")
            }
            result = CORE.evaluate_affected(
                repository,
                contract,
                selected_ids,
                affected_context=context,
            )
            regression = json.loads(
                (
                    repository / "reports/professionalism-regression-report.json"
                ).read_text()
            )
            markdown_after = {
                path.relative_to(repository).as_posix(): path.read_bytes()
                for path in (repository / "reports").glob("*.md")
            }
        self.assertEqual("pass", result["status"], result)
        self.assertEqual(8, result["command_execution_count"])
        self.assertEqual(
            1,
            sum(
                row["id"] == "validate-professionalism-regression"
                for row in result["producers"]
            ),
        )
        self.assertFalse(
            any(
                row["producer"] == "validate-professionalism-regression"
                for row in result["outcomes"]
            )
        )
        self.assertEqual("affected", regression["execution_scope"]["mode"])
        self.assertEqual("affected-partial-json", regression["evidence_scope"])
        self.assertEqual(markdown_before, markdown_after)

    def test_core_passes_only_canonical_affected_context_to_selected_producers(self) -> None:
        context = json.loads(_context(ids=["direct"]))
        producer = {
            "id": "eval-skill-professionalism",
            "depends_on": [],
        }
        contract = {
            "principle_acceptance_contract": {
                "producers": [producer],
                "outcomes": [],
                "authorities": [],
            },
            "core_principles": [],
        }
        producer_result = {
            "id": producer["id"],
            "status": "pass",
            "exit_code": 0,
        }
        with (
            mock.patch.object(CORE, "input_tree_digest", return_value={"tree": "x"}),
            mock.patch.object(
                CORE,
                "_run_producers",
                return_value=(
                    [producer_result],
                    {producer["id"]: producer_result},
                    {"tree": "x"},
                ),
            ) as run,
        ):
            result = CORE.evaluate_affected(
                Path("unused"),
                contract,
                [producer["id"]],
                affected_context=context,
            )
        self.assertEqual("pass", result["status"])
        passed = json.loads(
            run.call_args.kwargs["producer_environment"][
                "CHANGEFORGE_AFFECTED_CONTEXT"
            ]
        )
        self.assertEqual(context, passed)

    def test_default_full_checks_control_and_all_packages_but_affected_full_checks_189_only(self) -> None:
        entries = [
            ("control", {"name": "control", "path": "control"}),
            ("professional", {"name": "professional", "path": "professional"}),
            ("foundation", {"name": "foundation", "path": "foundation"}),
            ("domain", {"name": "domain", "path": "domain"}),
        ]
        with mock.patch.dict(os.environ, {}, clear=True):
            full_scope, full_entries = EVALUATOR._execution_scope(
                entries,
                release_review_config=Path("unused"),
            )
        self.assertEqual("full", full_scope["mode"])
        self.assertTrue(full_scope["control_skill_checked"])
        self.assertEqual(4, len(full_entries))

        with mock.patch.dict(
            os.environ,
            {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(scope="full")},
            clear=True,
        ):
            affected_scope, affected_entries = EVALUATOR._execution_scope(
                entries,
                release_review_config=Path("unused"),
            )
        self.assertEqual("affected", affected_scope["mode"])
        self.assertFalse(affected_scope["control_skill_checked"])
        self.assertEqual(
            ["domain", "foundation", "professional"],
            [entry["name"] for _kind, entry in affected_entries],
        )

    def test_removed_base_package_full_context_evaluates_only_head_inventory(self) -> None:
        head_entries = [
            ("control", {"name": "control", "path": "control"}),
            ("professional", {"name": "surviving", "path": "surviving"}),
        ]
        with mock.patch.dict(
            os.environ,
            {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(scope="full")},
            clear=True,
        ):
            affected_scope, affected_entries = EVALUATOR._execution_scope(
                head_entries,
                release_review_config=Path("unused"),
            )
        self.assertEqual([], affected_scope["direct_package_ids"])
        self.assertEqual(["surviving"], affected_scope["fresh_package_ids"])
        self.assertEqual(
            ["surviving"],
            [entry["name"] for _kind, entry in affected_entries],
        )

    def test_current_stale_baseline_evaluates_direct_and_exact_one_hop_without_carry(self) -> None:
        direct = "repository-tooling-change-builder"
        entries = EVALUATOR._load_entries()
        with mock.patch.dict(
            os.environ,
            {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(ids=[direct])},
            clear=True,
        ):
            execution_scope, selected_entries = EVALUATOR._execution_scope(
                entries,
                release_review_config=EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
            )
        panel = EVALUATOR._load_evaluator(
            EVALUATOR.EXPERT_PANEL_REVIEW,
            "affected_professional_expected_one_hop",
        )
        targets = panel._professional_package_targets(root=ROOT)
        bindings = panel.professional_carry.professional_review_bindings(targets)
        dependents = sorted(
            skill_id
            for skill_id, binding in bindings.items()
            if direct
            in {
                row["skill_id"]
                for row in binding["required_candidate_material_bindings"]
            }
        )
        expected = sorted({direct, *dependents})
        self.assertLess(len(expected), len(bindings))
        self.assertTrue(execution_scope["baseline_stale_no_carry"])
        self.assertEqual(expected, execution_scope["fresh_package_ids"])
        self.assertEqual([], execution_scope["carried_package_ids"])
        self.assertEqual(
            sorted(set(bindings) - set(expected)),
            execution_scope["unevaluated_package_ids"],
        )
        self.assertEqual(
            expected,
            sorted(entry["name"] for _kind, entry in selected_entries),
        )

    def test_current_full_impact_still_evaluates_all_189_without_stale_baseline_mode(self) -> None:
        entries = EVALUATOR._load_entries()
        with mock.patch.dict(
            os.environ,
            {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(scope="full")},
            clear=True,
        ):
            execution_scope, selected_entries = EVALUATOR._execution_scope(
                entries,
                release_review_config=EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
            )
        self.assertEqual(189, len(selected_entries))
        self.assertEqual(189, len(execution_scope["fresh_package_ids"]))
        self.assertEqual([], execution_scope["carried_package_ids"])
        self.assertEqual([], execution_scope["unevaluated_package_ids"])
        self.assertFalse(execution_scope["baseline_stale_no_carry"])

    def test_affected_evaluator_only_calls_fresh_package_closure_and_writes_json(self) -> None:
        entries = [
            ("professional", {"name": "direct", "path": "direct"}),
            ("foundation", {"name": "dependent", "path": "dependent"}),
            ("domain", {"name": "carried", "path": "carried"}),
        ]
        plan = {
            "baseline_decision": "evals/expert-panel/prior/panel/decision.json",
            "fresh_target_ids": ["dependent", "direct"],
            "carry_target_ids": ["carried"],
            "reasons_by_target": {
                "dependent": ["required-candidate-material-changed"],
                "direct": ["own-material-changed"],
                "carried": [],
            },
        }
        with tempfile.TemporaryDirectory() as raw:
            reports = Path(raw)
            with (
                mock.patch.dict(
                    os.environ,
                    {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(ids=["direct"])},
                    clear=False,
                ),
                mock.patch.object(EVALUATOR, "_load_entries", return_value=entries),
                mock.patch.object(EVALUATOR, "_affected_review_plan", return_value=plan),
                mock.patch.object(EVALUATOR, "_evaluate") as evaluate,
            ):
                evaluate.side_effect = lambda kind, entry: EVALUATOR.SkillResult(
                    name=entry["name"],
                    kind=kind,
                    path=f"{entry['path']}/SKILL.md",
                    status="pass",
                    authoring_score=100,
                    required_sections=[],
                )
                code = EVALUATOR.main(["--reports-dir", str(reports)])

            self.assertEqual(0, code)
            self.assertEqual(
                ["dependent", "direct"],
                sorted(call.args[1]["name"] for call in evaluate.call_args_list),
            )
            payload = json.loads(
                (reports / "skill-professionalism-eval.json").read_text()
            )
            self.assertEqual("affected", payload["execution_scope"]["mode"])
            self.assertEqual(["direct"], payload["execution_scope"]["direct_package_ids"])
            self.assertEqual(
                ["dependent", "direct"], payload["execution_scope"]["fresh_package_ids"]
            )
            self.assertFalse(any(reports.glob("*.md")))

    def test_malformed_unknown_and_direct_not_fresh_context_fail_closed(self) -> None:
        entries = [("professional", {"name": "known", "path": "known"})]
        cases = (
            ("{", None),
            (_context(ids=["unknown"]), None),
            (
                _context(ids=["known"]),
                {
                    "baseline_decision": "prior.json",
                    "fresh_target_ids": [],
                    "carry_target_ids": ["known"],
                    "reasons_by_target": {"known": []},
                },
            ),
        )
        for context, plan in cases:
            with self.subTest(context=context[:20]), tempfile.TemporaryDirectory() as raw:
                with ExitStack() as stack:
                    stack.enter_context(
                        mock.patch.dict(
                            os.environ,
                            {EVALUATOR.AFFECTED_CONTEXT_ENV: context},
                            clear=False,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            EVALUATOR, "_load_entries", return_value=entries
                        )
                    )
                    if plan is not None:
                        stack.enter_context(
                            mock.patch.object(
                                EVALUATOR,
                                "_affected_review_plan",
                                return_value=plan,
                            )
                        )
                    self.assertEqual(
                        1, EVALUATOR.main(["--reports-dir", raw])
                    )

    def test_full_regression_loader_rejects_affected_partial_reports(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            names = (
                "skill-professionalism-eval.json",
                "skill-professionalism-depth.json",
                "professional-coverage-matrix.json",
                "professional-benchmarks-report.json",
                "professional-agent-samples-report.json",
                "skill-content-audit.json",
            )
            for name in names:
                payload = {"execution_scope": {"mode": "full"}}
                if name == "professional-agent-samples-report.json":
                    payload.update(
                        {"strict": True, "promoted_only": True, "candidates_only": False}
                    )
                (directory / name).write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                set(names),
                {
                    path.name
                    for path in directory.iterdir()
                    if path.is_file()
                },
            )
            REGRESSION._reports(directory)
            partial = directory / "skill-professionalism-eval.json"
            partial.write_text(
                json.dumps({"execution_scope": {"mode": "affected"}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "full professionalism evidence"):
                REGRESSION._reports(directory)

    def test_affected_regression_validates_direct_fresh_carried_and_context_binding(self) -> None:
        context = _context(ids=["direct"])
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            execution_scope = _write_partial_reports(
                directory,
                direct=["direct"],
                fresh=["dependent", "direct"],
                carried=["carried"],
            )
            coverage_evaluator = mock.Mock()
            coverage_evaluator._load_entries.return_value = [
                ("professional", {"name": "direct"}),
                ("foundation", {"name": "dependent"}),
                ("domain", {"name": "carried"}),
            ]
            with (
                mock.patch.dict(
                    os.environ,
                    {REGRESSION.AFFECTED_CONTEXT_ENV: context},
                    clear=False,
                ),
                mock.patch.object(
                    REGRESSION,
                    "_load_coverage_evaluator",
                    return_value=coverage_evaluator,
                ),
            ):
                code = REGRESSION.main(
                    ["--reports-dir", str(directory), "--strict", "--report-only"]
                )
            report = json.loads(
                (directory / "professionalism-regression-report.json").read_text()
            )

        self.assertEqual(0, code)
        self.assertEqual("affected-partial-json", report["evidence_scope"])
        self.assertEqual(json.loads(context), report["affected_context"])
        self.assertEqual(execution_scope, report["execution_scope"])
        self.assertEqual("not-evaluated", report["release_gate"])

    def test_affected_regression_accepts_stale_baseline_without_carry_as_partial_only(self) -> None:
        context = _context(ids=["direct"])
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            execution_scope = _write_partial_reports(
                directory,
                direct=["direct"],
                fresh=["dependent", "direct"],
                carried=[],
                baseline_stale_no_carry=True,
                unevaluated=["unevaluated"],
            )
            coverage_evaluator = mock.Mock()
            coverage_evaluator._load_entries.return_value = [
                ("professional", {"name": "direct"}),
                ("foundation", {"name": "dependent"}),
                ("domain", {"name": "unevaluated"}),
            ]
            with (
                mock.patch.dict(
                    os.environ,
                    {REGRESSION.AFFECTED_CONTEXT_ENV: context},
                    clear=False,
                ),
                mock.patch.object(
                    REGRESSION,
                    "_load_coverage_evaluator",
                    return_value=coverage_evaluator,
                ),
            ):
                code = REGRESSION.main(
                    ["--reports-dir", str(directory), "--strict", "--report-only"]
                )
            report = json.loads(
                (directory / "professionalism-regression-report.json").read_text()
            )

        self.assertEqual(0, code)
        self.assertEqual([], execution_scope["carried_package_ids"])
        self.assertEqual("affected-partial-json", report["evidence_scope"])
        self.assertEqual("not-evaluated", report["release_gate"])
        self.assertTrue(report["execution_scope"]["baseline_stale_no_carry"])
        self.assertEqual(1, report["summary"]["unevaluated_package_count"])
        self.assertTrue(
            any("stale baseline" in item for item in report["limitations"])
        )

    def test_affected_regression_rejects_context_or_partition_mismatch_without_projection(self) -> None:
        context = _context(ids=["direct"])
        cases = (
            "direct_package_ids",
            "fresh_package_ids",
            "unevaluated_package_ids",
            "execution_scope",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as raw:
                directory = Path(raw)
                _write_partial_reports(
                    directory,
                    direct=["direct"],
                    fresh=["dependent", "direct"],
                    carried=["carried"],
                )
                target = directory / "skill-professionalism-eval.json"
                payload = json.loads(target.read_text())
                if case == "direct_package_ids":
                    payload["execution_scope"][case] = ["dependent"]
                elif case == "fresh_package_ids":
                    payload["execution_scope"][case] = ["direct"]
                elif case == "unevaluated_package_ids":
                    payload["execution_scope"][case] = ["unknown"]
                else:
                    for name in (
                        "skill-professionalism-eval.json",
                        "skill-professionalism-depth.json",
                        "professional-coverage-matrix.json",
                    ):
                        report_path = directory / name
                        report = json.loads(report_path.read_text())
                        report["execution_scope"]["reason_chains"] = [
                            ["wrong-context"]
                        ]
                        report_path.write_text(
                            json.dumps(report), encoding="utf-8"
                        )
                    payload = None
                if payload is not None:
                    target.write_text(json.dumps(payload), encoding="utf-8")
                coverage_evaluator = mock.Mock()
                coverage_evaluator._load_entries.return_value = [
                    ("professional", {"name": "direct"}),
                    ("foundation", {"name": "dependent"}),
                    ("domain", {"name": "carried"}),
                ]
                with (
                    mock.patch.dict(
                        os.environ,
                        {REGRESSION.AFFECTED_CONTEXT_ENV: context},
                        clear=False,
                    ),
                    mock.patch.object(
                        REGRESSION,
                        "_load_coverage_evaluator",
                        return_value=coverage_evaluator,
                    ),
                ):
                    self.assertEqual(
                        1,
                        REGRESSION.main(
                            ["--reports-dir", str(directory), "--report-only"]
                        ),
                    )
                self.assertFalse(
                    (directory / "professionalism-regression-report.json").exists()
                )
                self.assertFalse(any(directory.glob("*.md")))

    def test_invalid_baseline_fails_before_any_partial_report_is_written(self) -> None:
        entries = [("professional", {"name": "known", "path": "known"})]
        with tempfile.TemporaryDirectory() as raw:
            reports = Path(raw)
            with (
                mock.patch.dict(
                    os.environ,
                    {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(ids=["known"])},
                    clear=False,
                ),
                mock.patch.object(EVALUATOR, "_load_entries", return_value=entries),
                mock.patch.object(
                    EVALUATOR,
                    "_affected_review_plan",
                    side_effect=EVALUATOR.ValidationProblem(
                        "affected Professional baseline is invalid"
                    ),
                ),
            ):
                self.assertEqual(1, EVALUATOR.main(["--reports-dir", raw]))
            self.assertEqual([], list(reports.iterdir()))


class AffectedProfessionalLifecycleTests(unittest.TestCase):
    _root = _CORE_FIXTURES._root
    _script = _CORE_FIXTURES._script
    _contract = _CORE_FIXTURES._contract
    _producer = _CORE_FIXTURES._producer

    def test_affected_professional_lifecycle_path_executes_json_owner_once(self) -> None:
        canonical = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        canonical_producers = {
            row["id"]: row
            for row in canonical["principle_acceptance_contract"]["producers"]
        }
        expected_closure = {
            "audit-skill-content",
            "eval-professional-benchmarks",
            "eval-professional-samples",
            "eval-pressure-behavior",
            "eval-routing",
            "eval-skill-professionalism",
            "validate-professional-routing",
            "validate-professionalism-regression",
        }
        paths = (
            "scripts/expert_panel_review.py",
            "scripts/professional_completeness_carry_forward.py",
            "scripts/validate-professionalism-regression.py",
            "config/professionalism-release-review.yaml",
            "evals/expert-panel/review/packet.json",
        )
        for path in paths:
            with self.subTest(path=path):
                selection = impact_graph.resolve_entries(
                    copy.deepcopy(canonical),
                    [("M", path)],
                    base_sha="a" * 40,
                    head_sha="b" * 40,
                )
                selected_ids = selection["selected_producer_ids"]
                self.assertEqual(
                    ["validate-professionalism-regression"],
                    selection["changed_paths"][0]["direct_producer_ids"],
                )
                self.assertEqual(expected_closure, set(selected_ids))
                self.assertEqual(len(selected_ids), len(set(selected_ids)))
                self.assertNotIn("fallback", selection)

                temporary, root = self._root()
                self.addCleanup(temporary.cleanup)
                json_report = root / "reports/professionalism-regression-report.json"
                markdown_report = root / "reports/professionalism-regression-report.md"
                json_report.write_text('{"schema_version":0}\n', encoding="utf-8")
                markdown_report.write_text("release sentinel\n", encoding="utf-8")
                producers = []
                for producer_id in selected_ids:
                    body = (
                        "from pathlib import Path\n"
                        "execution_log = Path('reports/executions.log')\n"
                        "with execution_log.open('a', encoding='utf-8') as stream:\n"
                        f"    stream.write({producer_id!r} + '\\n')\n"
                    )
                    reports: list[str] = []
                    release_reports: list[str] = []
                    if producer_id == "validate-professionalism-regression":
                        body += (
                            "Path('reports/professionalism-regression-report.json')"
                            ".write_text('{\"schema_version\":3}\\n', encoding='utf-8')\n"
                        )
                        reports = ["reports/professionalism-regression-report.json"]
                        release_reports = [
                            "reports/professionalism-regression-report.md"
                        ]
                    script = self._script(root, producer_id, body)
                    producers.append(
                        self._producer(
                            producer_id,
                            script,
                            depends_on=canonical_producers[producer_id]["depends_on"],
                            reports=reports,
                            release_reports=release_reports,
                        )
                    )
                contract = self._contract(
                    producers,
                    [
                        {
                            "id": "professional-json-owner-executed",
                            "producer": "validate-professionalism-regression",
                            "predicates": [PROCESS_PASS],
                        }
                    ],
                )

                result = CORE.evaluate_affected(root, contract, selected_ids)

                executions = (root / "reports/executions.log").read_text(
                    encoding="utf-8"
                ).splitlines()
                self.assertEqual(expected_closure, set(executions))
                self.assertTrue(
                    all(executions.count(producer_id) == 1 for producer_id in expected_closure)
                )
                self.assertEqual(len(expected_closure), result["command_execution_count"])
                professional = [
                    row
                    for row in result["producers"]
                    if row["id"] == "validate-professionalism-regression"
                ]
                self.assertEqual(1, len(professional))
                self.assertEqual("pass", professional[0]["status"])
                self.assertEqual([], professional[0]["release_reports"])
                self.assertEqual("release sentinel\n", markdown_report.read_text())
                self.assertTrue(result["input_tree"]["unchanged"])



del _CORE_FIXTURES


if __name__ == "__main__":
    unittest.main()
