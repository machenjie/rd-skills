from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
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


def _historical_professional_schema1_header(panel) -> dict[str, object]:
    """Return the bounded legacy header consumed by affected planning."""

    accepted = {
        "accepted-current-professional-completeness": 162,
        "requires-professional-correction": 0,
        "unresolved-professional-disagreement": 0,
    }
    empty = {key: 0 for key in accepted}
    return {
        "axis": panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
        "decided_on": "2026-08-01",
        "findings": [],
        "kind": (
            panel.panel_attestation
            .PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND
        ),
        "rationale": "Bounded historical schema-1 affected-planning fixture.",
        "review_contract_fingerprint": "a" * 64,
        "review_cost_input": {},
        "review_id": "historical-professional-schema1-fixture",
        "reviewers": [],
        "schema_version": 1,
        "source_fingerprints": {
            "professional_packages": "b" * 64,
            "professional_review_bindings": "c" * 64,
            "professional_review_contract": "d" * 64,
        },
        "summary": {
            "evidence": {},
            "ordinary_criterion_majority": {},
            "overall_ballot_majority_audit": {},
            "partition": {
                "carried_target_count": 0,
                "effective_target_count": 162,
                "fresh_target_count": 162,
            },
            "professional_completeness": {
                "carried": empty,
                "effective": accepted,
                "fresh": accepted,
            },
            "qualification": {},
            "review_cost": {},
        },
        "verdict": "accepted-current-professional-completeness",
    }


@contextmanager
def _historical_professional_schema1_file(
    panel,
    *,
    value: dict[str, object] | None = None,
):
    """Bind affected planning to a canonical temporary legacy file."""

    current_path = (
        ROOT
        / panel.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
    )
    historical = copy.deepcopy(
        value if value is not None else _historical_professional_schema1_header(panel)
    )
    raw = (
        json.dumps(historical, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode("utf-8")
    with tempfile.TemporaryDirectory() as directory:
        fixture_path = Path(directory) / "professional-schema1-baseline.json"
        fixture_path.write_bytes(raw)
        if fixture_path.resolve() == current_path.resolve():
            raise AssertionError("historical fixture resolved to current fixed evidence")
        read_bound_regular_file = (
            panel.reviewer_manifest.read_bound_regular_file
        )
        with mock.patch.object(
            panel.panel_attestation,
            "PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH",
            str(fixture_path),
        ), mock.patch.object(
            panel.reviewer_manifest,
            "read_bound_regular_file",
            wraps=read_bound_regular_file,
        ) as read_bound:
            yield historical, fixture_path, current_path
        if read_bound.call_count != 1:
            raise AssertionError("historical fixture was not read exactly once")
        read_path = Path(read_bound.call_args.args[0])
        if read_path.resolve() != fixture_path.resolve():
            raise AssertionError("historical test read current fixed evidence")


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
        direct_package_id = "engineering-change-analysis"
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
        context = json.loads(
            _context(ids=[direct_package_id])
        )
        with tempfile.TemporaryDirectory() as raw:
            repository = Path(raw) / "repository"
            shutil.copytree(
                ROOT,
                repository,
                ignore=shutil.ignore_patterns(
                    ".git", "dist", "__pycache__", ".pytest_cache"
                ),
            )
            panel = EVALUATOR._load_evaluator(
                EVALUATOR.EXPERT_PANEL_REVIEW,
                "affected-professional-real-chain-expected-bindings",
            )
            expected_bindings = (
                panel.professional_carry.professional_review_bindings(
                    panel._professional_package_targets(root=repository)
                )
            )
            expected_direct_fresh = sorted(
                {
                    direct_package_id,
                    *(
                        skill_id
                        for skill_id, binding in expected_bindings.items()
                        if direct_package_id
                        in binding["dependency_material_bindings"]
                    ),
                }
            )
            contract = json.loads(
                (repository / "src/control-model/core-contracts.json").read_text()
            )
            maximum_fresh_target_count = contract["final_goal_contract"][
                "professional_review_cost_fixtures"
            ]["thresholds"]["maximum_fresh_target_count"]
            self.assertEqual(
                maximum_fresh_target_count,
                len(expected_direct_fresh),
            )
            expected_fresh = expected_direct_fresh
            expected_carried = sorted(
                set(expected_bindings) - set(expected_fresh)
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
            affected_reports = {
                name: json.loads((repository / "reports" / name).read_text())
                for name in (
                    "skill-professionalism-eval.json",
                    "skill-professionalism-depth.json",
                    "professional-coverage-matrix.json",
                )
            }
            markdown_after = {
                path.relative_to(repository).as_posix(): path.read_bytes()
                for path in (repository / "reports").glob("*.md")
            }
        self.assertEqual("pass", result["status"], result)
        self.assertEqual(8, result["command_execution_count"])
        professionalism = next(
            row
            for row in result["producers"]
            if row["id"] == "eval-skill-professionalism"
        )
        self.assertEqual("pass", professionalism["status"])
        self.assertEqual(0, professionalism["exit_code"])
        self.assertEqual(
            sorted(f"reports/{name}" for name in affected_reports),
            sorted(report["path"] for report in professionalism["reports"]),
        )
        self.assertTrue(
            all(report["fresh"] for report in professionalism["reports"])
        )
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
        execution_scopes = {
            json.dumps(payload["execution_scope"], sort_keys=True)
            for payload in affected_reports.values()
        }
        self.assertEqual(1, len(execution_scopes))
        execution_scope = next(iter(affected_reports.values()))[
            "execution_scope"
        ]
        self.assertEqual("affected", execution_scope["mode"])
        self.assertEqual(
            [direct_package_id],
            execution_scope["direct_package_ids"],
        )
        self.assertEqual(expected_fresh, execution_scope["fresh_package_ids"])
        self.assertEqual(
            expected_carried,
            execution_scope["carried_package_ids"],
        )
        self.assertEqual([], execution_scope["unevaluated_package_ids"])
        self.assertEqual(
            (
                len(expected_fresh),
                len(expected_carried),
                0,
            ),
            (
                len(execution_scope["fresh_package_ids"]),
                len(execution_scope["carried_package_ids"]),
                len(execution_scope["unevaluated_package_ids"]),
            ),
        )
        self.assertFalse(execution_scope["baseline_stale_no_carry"])
        self.assertIn(
            direct_package_id,
            execution_scope["fresh_package_ids"],
        )
        self.assertEqual(execution_scope, regression["execution_scope"])
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
            mock.patch.object(
                CORE, "input_tree_digest", return_value={"tree": "x"}
            ) as digest,
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
        self.assertEqual(2, digest.call_count)
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

    def test_compact_schema1_baseline_selects_exact_affected_closure_without_carry(
        self,
    ) -> None:
        direct = "repository-tooling-change-builder"
        entries = EVALUATOR._load_entries()
        panel = EVALUATOR._load_evaluator(
            EVALUATOR.EXPERT_PANEL_REVIEW,
            "affected-professional-expected-bindings",
        )
        with _historical_professional_schema1_file(panel) as (
            historical,
            fixture_path,
            current_path,
        ), mock.patch.dict(
            os.environ,
            {EVALUATOR.AFFECTED_CONTEXT_ENV: _context(ids=[direct])},
            clear=True,
        ), mock.patch.object(EVALUATOR, "_load_evaluator", return_value=panel):
            scope, selected = EVALUATOR._execution_scope(
                entries,
                release_review_config=EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
            )
            self.assertNotEqual(current_path.resolve(), fixture_path.resolve())
            self.assertEqual(1, historical["schema_version"])
            self.assertEqual(
                "historical-professional-schema1-fixture",
                historical["review_id"],
            )
            self.assertIn("source_fingerprints", historical)
            self.assertEqual(str(fixture_path), scope["baseline_decision"])
        targets = panel._professional_package_targets(root=ROOT)
        bindings, _snapshot = panel._professional_v3_binding_state(
            targets,
            review_contract_fingerprint=(
                panel._professional_evidence_review_contract_fingerprint()
            ),
        )
        reverse_dependencies = sorted(
            skill_id
            for skill_id, binding in bindings.items()
            if direct in binding["dependency_material_bindings"]
        )
        self.assertIn(direct, bindings)
        self.assertTrue(reverse_dependencies)
        expected_fresh = sorted({direct, *reverse_dependencies})
        self.assertTrue(scope["baseline_stale_no_carry"])
        self.assertEqual(expected_fresh, scope["fresh_package_ids"])
        self.assertEqual([], scope["carried_package_ids"])
        self.assertEqual(
            sorted(set(bindings) - set(expected_fresh)),
            scope["unevaluated_package_ids"],
        )
        self.assertEqual(
            expected_fresh,
            sorted(entry["name"] for _kind, entry in selected),
        )
        for skill_id in reverse_dependencies:
            self.assertIn(
                direct,
                bindings[skill_id]["dependency_material_bindings"],
            )
        self.assertEqual(
            (
                len(expected_fresh),
                0,
                len(bindings) - len(expected_fresh),
            ),
            (
                len(scope["fresh_package_ids"]),
                len(scope["carried_package_ids"]),
                len(scope["unevaluated_package_ids"]),
            ),
        )
        self.assertEqual(
            "baseline-stale-no-carry",
            scope["reasons_by_package"][direct][0],
        )

    def test_compact_schema1_baseline_never_invokes_carry_packet_builder(self) -> None:
        panel = EVALUATOR._load_evaluator(
            EVALUATOR.EXPERT_PANEL_REVIEW,
            "affected-professional-no-historical-carry",
        )
        with _historical_professional_schema1_file(panel) as (
            _historical,
            fixture_path,
            current_path,
        ), mock.patch.object(
            panel,
            "prepare_professional_completeness_packet_v3",
            side_effect=AssertionError("historical baseline entered carry builder"),
        ), mock.patch.object(EVALUATOR, "_load_evaluator", return_value=panel):
            plan = EVALUATOR._affected_review_plan(
                EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
                direct_package_ids=["repository-tooling-change-builder"],
            )
        self.assertNotEqual(current_path.resolve(), fixture_path.resolve())
        self.assertTrue(plan["baseline_stale_no_carry"])
        self.assertEqual([], plan["carry_target_ids"])

    def test_unsupported_compact_schema3_baseline_fails_closed(self) -> None:
        panel = EVALUATOR._load_evaluator(
            EVALUATOR.EXPERT_PANEL_REVIEW,
            "affected-professional-unsupported-storage-schema",
        )
        baseline = json.loads(
            (
                ROOT
                / panel.panel_attestation
                .PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            ).read_text(encoding="utf-8")
        )
        for schema_version in (3, 0, 2.0, 1.0, "1", True, None):
            with self.subTest(schema_version=schema_version):
                unsupported = copy.deepcopy(baseline)
                unsupported["schema_version"] = schema_version
                with mock.patch.object(
                    panel.reviewer_manifest,
                    "parse_json_object_bytes",
                    return_value=unsupported,
                ), mock.patch.object(
                    panel,
                    "prepare_professional_completeness_packet_v3",
                    side_effect=AssertionError(
                        "unsupported schema entered current packet builder"
                    ),
                ) as prepare_packet, mock.patch.object(
                    panel,
                    "_professional_package_targets",
                    side_effect=AssertionError(
                        "unsupported schema entered package catalog builder"
                    ),
                ) as build_catalog, mock.patch.object(
                    panel,
                    "_professional_v3_binding_state",
                    side_effect=AssertionError(
                        "unsupported schema entered binding builder"
                    ),
                ) as build_bindings, mock.patch.object(
                    EVALUATOR, "_load_evaluator", return_value=panel
                ), mock.patch.object(
                    panel.reviewer_manifest,
                    "recheck_bound_file",
                    side_effect=AssertionError(
                        "unsupported schema entered historical byte recheck"
                    ),
                ) as recheck_bound, self.assertRaisesRegex(
                    EVALUATOR.ValidationProblem,
                    "unsupported compact storage schema_version",
                ):
                    EVALUATOR._affected_review_plan(
                        EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
                        direct_package_ids=[
                            "repository-tooling-change-builder"
                        ],
                    )
                prepare_packet.assert_not_called()
                build_catalog.assert_not_called()
                build_bindings.assert_not_called()
                recheck_bound.assert_not_called()

    def test_historical_compact_baseline_requires_summary_mapping(self) -> None:
        panel = EVALUATOR._load_evaluator(
            EVALUATOR.EXPERT_PANEL_REVIEW,
            "affected-professional-historical-summary",
        )
        baseline = _historical_professional_schema1_header(panel)
        for label, mutation in (
            ("missing", lambda value: value.pop("summary")),
            ("non-mapping", lambda value: value.__setitem__("summary", [])),
            (
                "invalid-review-id",
                lambda value: value.__setitem__("review_id", "not valid"),
            ),
        ):
            with self.subTest(label=label):
                malformed = copy.deepcopy(baseline)
                mutation(malformed)
                with _historical_professional_schema1_file(
                    panel,
                    value=malformed,
                ) as (_historical, fixture_path, current_path), mock.patch.object(
                    EVALUATOR, "_load_evaluator", return_value=panel
                ), self.assertRaisesRegex(
                    EVALUATOR.ValidationProblem,
                    "historical Professional baseline is malformed",
                ):
                    EVALUATOR._affected_review_plan(
                        EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
                        direct_package_ids=[
                            "repository-tooling-change-builder"
                        ],
                    )
                self.assertNotEqual(current_path.resolve(), fixture_path.resolve())

    def test_malformed_historical_professional_baseline_still_fails_closed(
        self,
    ) -> None:
        panel = EVALUATOR._load_evaluator(
            EVALUATOR.EXPERT_PANEL_REVIEW,
            "affected-professional-malformed-historical",
        )
        malformed = _historical_professional_schema1_header(panel)
        malformed["axis"] = "semantic-disposition"
        malformed["kind"] = (
            panel.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND
        )
        malformed["review_id"] = "wrong-axis"
        with _historical_professional_schema1_file(
            panel,
            value=malformed,
        ) as (_historical, fixture_path, current_path), mock.patch.object(
            EVALUATOR, "_load_evaluator", return_value=panel
        ), self.assertRaisesRegex(
            EVALUATOR.ValidationProblem,
            "historical Professional baseline is malformed",
        ):
            EVALUATOR._affected_review_plan(
                EVALUATOR.DEFAULT_RELEASE_REVIEW_CONFIG,
                direct_package_ids=["repository-tooling-change-builder"],
            )
        self.assertNotEqual(current_path.resolve(), fixture_path.resolve())

    def test_stale_contract_evaluates_exact_one_hop_without_carry(self) -> None:
        bindings = {
            "dependent": {
                "dependency_material_bindings": {"direct": "a" * 64}
            },
            "direct": {"dependency_material_bindings": {}},
            "transitive": {
                "dependency_material_bindings": {"dependent": "b" * 64}
            },
            "unaffected": {"dependency_material_bindings": {}},
        }
        panel = mock.Mock()
        panel.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH = (
            "evals/expert-panel/professional-completeness.json"
        )
        panel.panel_attestation.ATTESTATION_SCHEMA_VERSION = 2
        panel.prepare_professional_completeness_packet_v3.return_value = {
            "professional_targets": [],
            "review_plan": {
                "baseline": {
                    "attestation": {
                        "path": "evals/expert-panel/professional-completeness.json"
                    }
                },
                "fresh_targets": [
                    {
                        "skill_id": skill_id,
                        "reason_codes": ["review-contract-changed"],
                    }
                    for skill_id in bindings
                ],
                "carried_targets": [],
            },
        }
        panel._professional_v3_base_targets.return_value = []
        panel.professional_carry.professional_review_bindings.return_value = bindings
        panel.reviewer_manifest.parse_json_object_bytes.return_value = {
            "schema_version": 2
        }

        with mock.patch.object(
            EVALUATOR,
            "load_yaml_file",
            return_value={"reviewed_at": "2026-08-11"},
        ), mock.patch.object(EVALUATOR, "_load_evaluator", return_value=panel):
            plan = EVALUATOR._affected_review_plan(
                Path("release.yaml"), direct_package_ids=["direct"]
            )

        self.assertTrue(plan["baseline_stale_no_carry"])
        self.assertEqual(["dependent", "direct"], plan["fresh_target_ids"])
        self.assertEqual([], plan["carry_target_ids"])
        self.assertEqual(
            ["transitive", "unaffected"], plan["unevaluated_target_ids"]
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
        self.assertEqual(188, len(selected_entries))
        self.assertEqual(188, len(execution_scope["fresh_package_ids"]))
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

    def test_affected_regression_does_not_require_git_storage_precheck(self) -> None:
        context = _context(ids=["direct"])
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_partial_reports(
                directory,
                direct=["direct"],
                fresh=["direct"],
                carried=[],
            )
            coverage_evaluator = mock.Mock()
            coverage_evaluator._load_entries.return_value = [
                ("professional", {"name": "direct"}),
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
                mock.patch.object(
                    REGRESSION,
                    "_validate_current_expert_panel_storage",
                    side_effect=AssertionError(
                        "affected archive must not inspect Git storage"
                    ),
                ) as validate_storage,
            ):
                code = REGRESSION.main(
                    ["--reports-dir", str(directory), "--strict", "--report-only"]
                )

        self.assertEqual(0, code)
        validate_storage.assert_not_called()

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

    def test_affected_professional_lifecycle_paths_select_focused_tests_without_producers(self) -> None:
        canonical = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        paths = (
            "scripts/expert_panel_review.py",
            "scripts/professional_completeness_carry_forward.py",
            "scripts/validate-professionalism-regression.py",
            "config/professionalism-release-review.yaml",
            "evals/expert-panel/professional-completeness.json",
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
                self.assertEqual([], selection["changed_paths"][0]["direct_producer_ids"])
                self.assertEqual([], selected_ids)
                self.assertTrue(selection["selected_test_modules"])
                self.assertEqual(
                    "soft-stale", selection["expert_panel_evidence"]["status"]
                )
                self.assertEqual(
                    [], selection["selected_test_modules_by_layer"]["release"]
                )
                self.assertNotIn("fallback", selection)



del _CORE_FIXTURES


if __name__ == "__main__":
    unittest.main()
