from __future__ import annotations

import copy
import ctypes
import errno
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "eval_core_principles", SCRIPTS / "eval-core-principles.py"
)
assert SPEC is not None and SPEC.loader is not None
EVALUATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EVALUATOR
SPEC.loader.exec_module(EVALUATOR)

import impact_graph  # noqa: E402


PROCESS_PASS = {
    "source": "process",
    "pointer": "/exit_code",
    "operator": "equals",
    "expected": 0,
}
REPORT_SCHEMA = {
    "source": "reports/result.json",
    "pointer": "/schema_version",
    "operator": "equals",
    "expected": 1,
}


def assert_core_producer_outcomes_passed(
    root: Path,
    *producer_ids: str,
) -> None:
    report_path = root / EVALUATOR.JSON_REPORT
    if not report_path.is_file():
        raise AssertionError(
            f"Core saved report is missing: {EVALUATOR.JSON_REPORT}; "
            "run the owning Core gate before consuming producer outcomes"
        )
    original = report_path.read_bytes()
    try:
        report = json.loads(original)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Core saved report is invalid: {EVALUATOR.JSON_REPORT}: {exc}"
        ) from exc
    errors = EVALUATOR.validate_saved_report(root, report)
    if original != report_path.read_bytes():
        raise AssertionError("Core outcome consumer mutated the saved report")
    if errors:
        raise AssertionError(
            "Core saved report contract/tree is invalid: " + "; ".join(errors)
        )
    producers = {
        row.get("id"): row
        for row in report.get("producers", [])
        if isinstance(row, dict)
    }
    for producer_id in producer_ids:
        producer = producers.get(producer_id)
        if producer is None:
            raise AssertionError(
                f"Core saved report does not own producer outcome: {producer_id}"
            )
        if producer.get("status") != "pass":
            raise AssertionError(f"Core producer outcome did not pass: {producer_id}")


class CorePrinciplesOutcomeTests(unittest.TestCase):
    def _root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "scripts").mkdir()
        (root / "src/control-model").mkdir(parents=True)
        (root / "reports").mkdir()
        return temporary, root

    def _script(self, root: Path, name: str, body: str) -> str:
        relative = f"scripts/{name}.py"
        (root / relative).write_text(body, encoding="utf-8")
        return relative

    def _contract(
        self,
        producers: list[dict],
        outcomes: list[dict],
        *,
        formal_outcomes: list[str] | None = None,
    ) -> dict:
        formal = set(formal_outcomes or [])
        authoring = [row["id"] for row in outcomes if row["id"] not in formal]
        self.assertTrue(authoring)
        identities = list(EVALUATOR.CANONICAL_CORE_PRINCIPLE_IDENTITIES)
        dimensions = [
            {
                "id": f"{principle_id}-fixture-coverage",
                "principle": principle_id,
                "capabilities": ["fixture-validation"],
            }
            for principle_id, _ in identities
        ]
        principles = []
        for index, (principle_id, principle_name) in enumerate(identities):
            principles.append(
                {
                    "id": principle_id,
                    "name": principle_name,
                    "required_dimensions": [dimensions[index]["id"]],
                    "required_outcomes": {
                        "authoring": authoring if index == 0 else [authoring[0]],
                        "formal_release": sorted(formal) if index == 0 else [],
                    },
                }
            )
        normalized_outcomes = []
        for row in outcomes:
            tagged_dimensions = (
                [dimension["id"] for dimension in dimensions]
                if row["id"] == authoring[0]
                else [dimensions[0]["id"]]
            )
            normalized_outcomes.append(
                {
                    "id": row["id"],
                    "producer": row["producer"],
                    "dimensions": tagged_dimensions,
                    "capabilities": ["fixture-validation"],
                    "predicates": row["predicates"],
                }
            )
        return {
            "authority_data": {"limit": 5},
            "core_principles": principles,
            "principle_acceptance_contract": {
                "schema_version": 3,
                "dimensions": dimensions,
                "authorities": [
                    {
                        "id": "fixture-authority",
                        "pointer": "/authority_data",
                        "scope": "Fixture authority.",
                    }
                ],
                "producers": producers,
                "outcomes": normalized_outcomes,
            },
        }

    def _producer(
        self,
        producer_id: str,
        script: str,
        *,
        depends_on: list[str] | None = None,
        reports: list[str] | None = None,
        release_reports: list[str] | None = None,
        authority_inputs: list[str] | None = None,
    ) -> dict:
        return {
            "id": producer_id,
            "argv": ["python3", script],
            "depends_on": depends_on or [],
            "reports": reports or [],
            "release_reports": release_reports or [],
            "authority_inputs": (
                ["fixture-authority"]
                if authority_inputs is None
                else authority_inputs
            ),
            "timeout_seconds": 30,
        }

    def _passing_report(
        self,
        outcome: dict,
        authority_values: dict[str, object] | None = None,
    ) -> dict:
        authorities = authority_values or {}
        payload: dict = {}
        for predicate in outcome["predicates"]:
            if predicate["source"] == "process":
                continue
            if "expected" in predicate:
                expected = predicate["expected"]
            else:
                provenance = predicate["expected_from"]
                expected = EVALUATOR.resolve_json_pointer(
                    authorities[provenance["authority"]],
                    provenance["pointer"],
                )
            cursor = payload
            parts = [part for part in predicate["pointer"].split("/") if part]
            for part in parts[:-1]:
                cursor = cursor.setdefault(part, {})
            cursor[parts[-1]] = copy.deepcopy(expected)
        return payload

    def test_core_outcome_consumer_is_read_only_and_fails_closed(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "reports").mkdir()
        helper = globals().get("assert_core_producer_outcomes_passed")
        self.assertTrue(callable(helper), "narrow Core outcome helper is missing")

        with self.assertRaisesRegex(AssertionError, "Core saved report is missing"):
            helper(root, "producer-a")

        report_path = root / EVALUATOR.JSON_REPORT
        report_path.write_text(
            json.dumps(
                {
                    "producers": [
                        {
                            "id": "producer-a",
                            "status": "pass",
                            "reports": [],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        original = report_path.read_bytes()
        with mock.patch.object(
            EVALUATOR,
            "validate_saved_report",
            return_value=["input tree digest is stale"],
        ):
            with self.assertRaisesRegex(
                AssertionError, "Core saved report contract/tree is invalid"
            ):
                helper(root, "producer-a")
        self.assertEqual(original, report_path.read_bytes())

        with mock.patch.object(
            EVALUATOR, "validate_saved_report", return_value=[]
        ):
            helper(root, "producer-a")
        self.assertEqual(original, report_path.read_bytes())

    def test_repository_professional_injection_is_surface_scoped(self) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(encoding="utf-8")
        )
        principles = {item["id"]: item for item in contract["core_principles"]}
        professional = set(
            principles["professional-skill-injection"]["required_outcomes"][
                "authoring"
            ]
        )
        expected_layer_surfaces = {
            "root-professional-content-valid",
            "root-foundation-content-valid",
            "root-domain-content-valid",
            "reference-professional-content-valid",
            "reference-foundation-content-valid",
            "reference-domain-content-valid",
        }
        self.assertTrue(expected_layer_surfaces <= professional)
        self.assertTrue(
            {"root-content-valid", "reference-content-valid"}.isdisjoint(
                professional
            )
        )
        ai_first = set(principles["ai-first"]["required_outcomes"]["authoring"])
        self.assertTrue(
            {
                "root-control-content-valid",
                "root-professional-content-valid",
                "root-foundation-content-valid",
                "root-domain-content-valid",
                "root-description-content-valid",
                "reference-control-content-valid",
                "reference-professional-content-valid",
                "reference-foundation-content-valid",
                "reference-domain-content-valid",
            }
            <= ai_first
        )
        self.assertNotIn("root-lifecycle-current", ai_first)
        self.assertEqual(
            [
                "readability-review-current",
                "content-audit-formal-release-current",
            ],
            principles["ai-first"]["required_outcomes"]["formal_release"],
        )
        self.assertTrue(
            all(
                "root-lifecycle-current"
                not in principle["required_outcomes"]["authoring"]
                for principle in principles.values()
            )
        )

    def test_c_repository_audit_application_is_formal_only(self) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        acceptance = contract["principle_acceptance_contract"]
        producers = {row["id"]: row for row in acceptance["producers"]}
        outcomes = {row["id"]: row for row in acceptance["outcomes"]}
        principles = {row["id"]: row for row in contract["core_principles"]}

        self.assertEqual(
            [
                "python3",
                "scripts/audit-skill-content.py",
                "--gate",
                "authoring",
            ],
            producers["audit-skill-content"]["argv"],
        )
        formal_id = "content-audit-formal-release-current"
        self.assertEqual(
            ["readability-review-current", formal_id],
            principles["ai-first"]["required_outcomes"]["formal_release"],
        )
        self.assertTrue(
            all(
                formal_id not in principle["required_outcomes"]["authoring"]
                for principle in principles.values()
            )
        )
        self.assertEqual(
            {
                (
                    "process",
                    "/exit_code",
                    "equals",
                    0,
                ),
                (
                    "reports/skill-content-audit.json",
                    "/gate_status/formal_release/status",
                    "equals",
                    "pass",
                ),
                (
                    "reports/skill-content-audit.json",
                    "/semantic_disposition_application/status",
                    "equals",
                    "current",
                ),
            },
            {
                (
                    row["source"],
                    row["pointer"],
                    row["operator"],
                    row["expected"],
                )
                for row in outcomes[formal_id]["predicates"]
            },
        )
        authoring_ids = {
            outcome_id
            for principle in principles.values()
            for outcome_id in principle["required_outcomes"]["authoring"]
        }
        self.assertTrue(
            all(
                not any(
                    predicate["pointer"]
                    in {
                        "/gate_status/formal_release/status",
                        "/semantic_disposition_application/status",
                    }
                    for predicate in outcomes[outcome_id]["predicates"]
                )
                for outcome_id in authoring_ids
            )
        )
        professionalism = outcomes["professionalism-authoring-valid"]
        professionalism_pointers = {
            predicate["pointer"]: predicate["expected"]
            for predicate in professionalism["predicates"]
            if predicate["source"]
            == "reports/professionalism-regression-report.json"
        }
        self.assertEqual(
            {
                "/schema_version": 4,
                "/authoring_gate": "current-contract-pass",
                "/root_content_summary/readiness_scope": "agent-facing-root-content",
                "/root_content_summary/structural_strict_ready": True,
                "/root_content_summary/semantic_triage_complete": True,
                "/root_content_summary/strict_ready": True,
                "/root_content_summary/semantic_unresolved_candidates": 0,
                "/root_content_summary/semantic_disposition_errors": 0,
            },
            professionalism_pointers,
        )
        self.assertTrue(
            all(
                "semantic_lifecycle" not in predicate["pointer"]
                for predicate in professionalism["predicates"]
            )
        )

    def test_formal_professionalism_has_one_aggregate_release_outcome(self) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        acceptance = contract["principle_acceptance_contract"]
        principles = {row["id"]: row for row in contract["core_principles"]}
        dimensions = {row["id"]: row for row in acceptance["dimensions"]}
        outcomes = {row["id"]: row for row in acceptance["outcomes"]}

        outcome_id = "professionalism-formal-release-ready"
        self.assertEqual(
            ["professional-review-cost-current", outcome_id],
            principles["final-goal"]["required_outcomes"]["formal_release"],
        )
        self.assertTrue(
            {
                "readability-review-current",
                "content-audit-formal-release-current",
                "professional-completeness-review-current",
                "professional-review-cost-current",
                outcome_id,
            }
            <= {
                required
                for principle in principles.values()
                for required in principle["required_outcomes"]["formal_release"]
            }
        )
        self.assertIn(
            "professionalism-formal-release-readiness",
            dimensions["final-goal-verification-and-professionalism-cost"][
                "capabilities"
            ],
        )
        formal = outcomes[outcome_id]
        self.assertEqual(
            "validate-professionalism-regression", formal["producer"]
        )
        manifest_pointers = {
            predicate["pointer"]
            for predicate in formal["predicates"]
            if predicate["source"]
            == "reports/professionalism-regression-report.json"
            and predicate["pointer"].startswith(
                "/expert_panel_release_manifest/"
            )
        }
        self.assertTrue(
            {
                "/expert_panel_release_manifest/schema_version",
                "/expert_panel_release_manifest/status",
                "/expert_panel_release_manifest/verification_toolchain/head_commit_matches_current",
                "/expert_panel_release_manifest/verification_toolchain/artifact_count",
                "/expert_panel_release_manifest/verification_toolchain/accepted_artifact_count",
                "/expert_panel_release_manifest/verification_toolchain/head_byte_equal_count",
                "/expert_panel_release_manifest/verification_toolchain/clean_artifact_count",
                "/expert_panel_release_manifest/artifacts/0/path",
                "/expert_panel_release_manifest/artifacts/1/path",
                "/expert_panel_release_manifest/artifacts/2/path",
            }
            <= manifest_pointers
        )

    def _write_contract(self, root: Path, contract: dict) -> str:
        path = root / "src/control-model/core-contracts.json"
        path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_static_graph_rejects_schema_refs_orphans_duplicate_argv_self_cycle_and_pointer_consumer(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        first = self._script(root, "first", "raise SystemExit(0)\n")
        second = self._script(root, "second", "raise SystemExit(0)\n")
        producers = [self._producer("first", first)]
        outcomes = [
            {"id": "first-pass", "producer": "first", "predicates": [PROCESS_PASS]}
        ]
        baseline = self._contract(producers, outcomes)
        self.assertEqual(
            [], EVALUATOR.validate_principle_acceptance_contract(baseline, root)
        )

        mutations: list[tuple[str, dict, str]] = []
        bad_schema = copy.deepcopy(baseline)
        bad_schema["principle_acceptance_contract"]["schema_version"] = 2
        mutations.append(("schema", bad_schema, "schema_version must be 3"))

        bad_ref = copy.deepcopy(baseline)
        bad_ref["principle_acceptance_contract"]["outcomes"][0]["producer"] = "missing"
        mutations.append(("ref", bad_ref, "declared producer"))

        orphan = copy.deepcopy(baseline)
        orphan["principle_acceptance_contract"]["outcomes"].append(
            {
                "id": "orphan",
                "producer": "first",
                "dimensions": ["ai-first-fixture-coverage"],
                "capabilities": ["fixture-validation"],
                "predicates": [PROCESS_PASS],
            }
        )
        mutations.append(("orphan", orphan, "outcomes contain orphans"))

        duplicate = copy.deepcopy(baseline)
        duplicate["principle_acceptance_contract"]["producers"].append(
            self._producer("second", first, authority_inputs=[])
        )
        mutations.append(("duplicate", duplicate, "canonical argv must be unique"))

        recursive = copy.deepcopy(baseline)
        recursive["principle_acceptance_contract"]["producers"][0]["argv"][1] = (
            "scripts/eval-core-principles.py"
        )
        (root / "scripts/eval-core-principles.py").write_text("", encoding="utf-8")
        mutations.append(("self", recursive, "recursively execute"))

        cycle = copy.deepcopy(baseline)
        cycle["principle_acceptance_contract"]["producers"] = [
            self._producer("first", first, depends_on=["second"]),
            self._producer("second", second, depends_on=["first"]),
        ]
        cycle["principle_acceptance_contract"]["outcomes"].append(
            {
                "id": "second-pass",
                "producer": "second",
                "dimensions": ["ai-first-fixture-coverage"],
                "capabilities": ["fixture-validation"],
                "predicates": [PROCESS_PASS],
            }
        )
        cycle["core_principles"][0]["required_outcomes"]["authoring"].append(
            "second-pass"
        )
        mutations.append(("cycle", cycle, "dependency cycle"))

        pointer = copy.deepcopy(baseline)
        pointer["principle_acceptance_contract"]["authorities"][0]["pointer"] = (
            "/missing"
        )
        mutations.append(("pointer", pointer, "does not resolve"))

        consumer = copy.deepcopy(baseline)
        consumer["principle_acceptance_contract"]["producers"][0][
            "authority_inputs"
        ] = []
        mutations.append(("consumer", consumer, "no actual producer consumer"))

        for label, mutation, marker in mutations:
            with self.subTest(label=label):
                errors = EVALUATOR.validate_principle_acceptance_contract(
                    mutation, root
                )
                self.assertTrue(any(marker in error for error in errors), errors)

    def test_process_failure_marks_dependency_not_run(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        fail = self._script(root, "fail", "raise SystemExit(7)\n")
        dependent = self._script(
            root,
            "dependent",
            "from pathlib import Path\nPath('reports/dependent-ran').write_text('yes')\n",
        )
        producers = [
            self._producer("fail", fail),
            self._producer("dependent", dependent, depends_on=["fail"]),
        ]
        outcomes = [
            {"id": "fail-pass", "producer": "fail", "predicates": [PROCESS_PASS]},
            {
                "id": "dependent-pass",
                "producer": "dependent",
                "predicates": [PROCESS_PASS],
            },
        ]
        contract = self._contract(producers, outcomes)
        report = EVALUATOR.evaluate(root, contract)
        by_id = {item["id"]: item for item in report["producers"]}
        outcome_by_id = {item["id"]: item for item in report["outcomes"]}
        self.assertEqual("fail", by_id["fail"]["status"])
        self.assertEqual("not_run", by_id["dependent"]["status"])
        self.assertEqual("fail", outcome_by_id["fail-pass"]["status"])
        self.assertEqual("not_run", outcome_by_id["dependent-pass"]["status"])
        self.assertFalse((root / "reports/dependent-ran").exists())

    def test_professionalism_timeout_ceiling_is_exact_and_bounded(self) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        producer = next(
            row
            for row in contract["principle_acceptance_contract"]["producers"]
            if row["id"] == "validate-professionalism-regression"
        )
        self.assertEqual(1200, producer["timeout_seconds"])
        self.assertEqual(3600, EVALUATOR._producer_timeout_seconds(producer))

        for field, value in (
            ("id", "another-producer"),
            ("argv", ["python3", "scripts/validate-professionalism-regression.py"]),
            ("timeout_seconds", 1199),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(producer)
                changed[field] = value
                self.assertEqual(
                    changed["timeout_seconds"],
                    EVALUATOR._producer_timeout_seconds(changed),
                )

    def test_formal_timeout_kills_producer_settles_tree_and_propagates_not_run(
        self,
    ) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        slow = self._script(
            root,
            "slow",
            "import time\nprint('partial output', flush=True)\ntime.sleep(10)\n",
        )
        dependent = self._script(
            root,
            "after_timeout",
            "from pathlib import Path\nPath('reports/should-not-run').write_text('yes')\n",
        )
        producers = [
            self._producer("slow", slow),
            self._producer("after-timeout", dependent, depends_on=["slow"]),
        ]
        producers[0]["timeout_seconds"] = 1
        outcomes = [
            {"id": "slow-pass", "producer": "slow", "predicates": [PROCESS_PASS]},
            {
                "id": "after-timeout-pass",
                "producer": "after-timeout",
                "predicates": [PROCESS_PASS],
            },
        ]
        with mock.patch.object(
            EVALUATOR,
            "input_tree_digest",
            wraps=EVALUATOR.input_tree_digest,
        ) as digest:
            report = EVALUATOR.evaluate(
                root,
                self._contract(producers, outcomes),
                release_projection=True,
            )
        by_id = {item["id"]: item for item in report["producers"]}
        self.assertEqual(3, digest.call_count)
        self.assertEqual("timeout", by_id["slow"]["status"])
        self.assertEqual(1, by_id["slow"]["timeout_seconds"])
        self.assertTrue(by_id["slow"]["timed_out"])
        self.assertEqual(["process-timeout"], by_id["slow"]["failure_reason_codes"])
        self.assertEqual("not_run", by_id["after-timeout"]["status"])
        self.assertEqual(
            ["dependency-not-pass"],
            by_id["after-timeout"]["failure_reason_codes"],
        )
        self.assertFalse((root / "reports/should-not-run").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX process-tree contract")
    def test_timeout_kills_normal_group_and_escaped_session_children(self) -> None:
        for escaped in (False, True):
            with self.subTest(escaped=escaped):
                temporary, root = self._root()
                self.addCleanup(temporary.cleanup)
                child = self._script(
                    root,
                    "late_child",
                    "from pathlib import Path\n"
                    "import os\nimport time\n"
                    "Path('reports/child.pid').write_text(str(os.getpid()))\n"
                    "time.sleep(1.8)\n"
                    "Path('src/late-mutation.txt').write_text('escaped')\n",
                )
                parent = self._script(
                    root,
                    "tree_parent",
                    "import subprocess\nimport sys\nimport time\n"
                    f"subprocess.Popen([sys.executable, {child!r}], "
                    f"start_new_session={escaped!r})\n"
                    "time.sleep(30)\n",
                )
                producer = self._producer("tree-parent", parent)
                producer["timeout_seconds"] = 1
                contract = self._contract(
                    [producer],
                    [
                        {
                            "id": "tree-parent-pass",
                            "producer": "tree-parent",
                            "predicates": [PROCESS_PASS],
                        }
                    ],
                )

                report = EVALUATOR.evaluate(root, contract)
                result = report["producers"][0]
                self.assertEqual("timeout", result["status"])
                self.assertEqual(["process-timeout"], result["failure_reason_codes"])
                self.assertTrue(result["source_unchanged"])
                time.sleep(1.0)
                self.assertFalse((root / "src/late-mutation.txt").exists())
                child_pid = int((root / "reports/child.pid").read_text())
                snapshot = EVALUATOR._known_posix_process_snapshot({child_pid})
                self.assertIsNotNone(snapshot)
                assert snapshot is not None
                self.assertTrue(
                    child_pid not in snapshot
                    or snapshot[child_pid][1].startswith("Z")
                )

    def test_process_tree_cleanup_platform_dispatch_is_closed(self) -> None:
        process = mock.Mock()
        with mock.patch.object(
            EVALUATOR, "_terminate_windows_process_tree", return_value=True
        ) as windows, mock.patch.object(
            EVALUATOR, "_terminate_posix_process_tree", return_value=True
        ) as posix:
            self.assertTrue(
                EVALUATOR._terminate_process_tree(process, platform_name="nt")
            )
            windows.assert_called_once_with(process)
            posix.assert_not_called()

        process = mock.Mock()
        process.kill.side_effect = OSError("unsupported")
        self.assertFalse(
            EVALUATOR._terminate_process_tree(process, platform_name="unknown")
        )

    def test_darwin_pid_list_fails_closed_after_repeated_full_buffers(self) -> None:
        libproc = mock.Mock()

        def fill_buffer(_selector, _value, buffer, size):
            if buffer is None:
                return ctypes.sizeof(ctypes.c_int)
            return size

        libproc.proc_listpids.side_effect = fill_buffer
        self.assertIsNone(
            EVALUATOR._darwin_list_pids(
                libproc,
                EVALUATOR.DARWIN_PROC_PPID_ONLY,
                123,
            )
        )
        self.assertEqual(
            1 + EVALUATOR.DARWIN_PID_LIST_ATTEMPTS,
            libproc.proc_listpids.call_count,
        )

    def test_darwin_descendant_snapshot_preserves_edges_and_fails_closed(self) -> None:
        root_pid = 100
        child_pid = 101
        libproc = mock.Mock()
        with mock.patch.object(
            EVALUATOR, "_darwin_libproc", return_value=libproc
        ), mock.patch.object(
            EVALUATOR,
            "_darwin_list_pids",
            side_effect=[{child_pid}, set()],
        ), mock.patch.object(
            EVALUATOR,
            "_darwin_process_info",
            side_effect=[(True, (1, "2")), (True, (999, "2"))],
        ):
            snapshot, complete = EVALUATOR._darwin_descendant_snapshot(root_pid)
        self.assertTrue(complete)
        self.assertEqual((root_pid, "2"), snapshot[child_pid])

        for failed_child_info in ((False, None), (True, None)):
            with self.subTest(failed_child_info=failed_child_info), mock.patch.object(
                EVALUATOR, "_darwin_libproc", return_value=libproc
            ), mock.patch.object(
                EVALUATOR,
                "_darwin_list_pids",
                return_value={child_pid},
            ), mock.patch.object(
                EVALUATOR,
                "_darwin_process_info",
                side_effect=[(True, (1, "2")), failed_child_info],
            ):
                snapshot, complete = EVALUATOR._darwin_descendant_snapshot(root_pid)
            self.assertFalse(complete)
            self.assertEqual((root_pid, "?"), snapshot[child_pid])
            with mock.patch.object(
                EVALUATOR,
                "_darwin_descendant_snapshot",
                return_value=(snapshot, complete),
            ):
                self.assertIsNone(EVALUATOR._darwin_process_snapshot(root_pid))

    def test_darwin_esrch_and_survivor_permission_are_fail_closed(self) -> None:
        libproc = mock.Mock()

        def exited_process(*_args):
            ctypes.set_errno(errno.ESRCH)
            return 0

        libproc.proc_pidinfo.side_effect = exited_process
        self.assertEqual((True, None), EVALUATOR._darwin_process_info(libproc, 123))

        def denied_process(*_args):
            ctypes.set_errno(errno.EPERM)
            return 0

        libproc.proc_pidinfo.side_effect = denied_process
        with mock.patch.object(EVALUATOR.os, "kill") as kill:
            self.assertEqual(
                (False, None),
                EVALUATOR._darwin_process_info(libproc, 123),
            )
        kill.assert_not_called()

        libproc.proc_pidinfo.side_effect = None
        libproc.proc_pidinfo.return_value = 20
        self.assertEqual(
            (False, None),
            EVALUATOR._darwin_process_info(libproc, 123),
        )
        with mock.patch.object(EVALUATOR.os, "kill", side_effect=PermissionError):
            self.assertEqual(
                {123},
                EVALUATOR._surviving_posix_pids({123}, {}),
            )
        libproc.proc_pidinfo.return_value = 0
        with mock.patch.object(EVALUATOR.os, "kill", side_effect=OSError):
            self.assertEqual(
                (False, None),
                EVALUATOR._darwin_process_info(libproc, 123),
            )
            self.assertEqual(
                {123},
                EVALUATOR._surviving_posix_pids({123}, {}),
            )

    def test_windows_process_tree_uses_taskkill_and_fails_closed_to_kill(self) -> None:
        process = mock.Mock(pid=4321)
        process.poll.side_effect = [None, 1]
        completed = mock.Mock(returncode=1)
        with mock.patch.object(
            EVALUATOR.subprocess, "run", return_value=completed
        ) as run:
            self.assertFalse(EVALUATOR._terminate_windows_process_tree(process))
        run.assert_called_once_with(
            ["taskkill", "/PID", "4321", "/T", "/F"],
            check=False,
            stdout=EVALUATOR.subprocess.DEVNULL,
            stderr=EVALUATOR.subprocess.DEVNULL,
            timeout=EVALUATOR.TIMEOUT_FINAL_WAIT_SECONDS,
        )
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(
            timeout=EVALUATOR.TIMEOUT_FINAL_WAIT_SECONDS
        )

    def test_canonical_identity_and_dimension_coverage_fail_closed(self) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )

        swapped = copy.deepcopy(contract)
        first, second = swapped["core_principles"][:2]
        first["required_dimensions"], second["required_dimensions"] = (
            second["required_dimensions"],
            first["required_dimensions"],
        )
        first["required_outcomes"], second["required_outcomes"] = (
            second["required_outcomes"],
            first["required_outcomes"],
        )
        errors = EVALUATOR.validate_principle_acceptance_contract(swapped, ROOT)
        self.assertTrue(
            any("allowed dimension catalog" in error for error in errors), errors
        )

        identity_drift = copy.deepcopy(contract)
        identity_drift["core_principles"][0]["name"] = "AI Oriented"
        errors = EVALUATOR.validate_principle_acceptance_contract(
            identity_drift, ROOT
        )
        self.assertTrue(
            any("canonical identities" in error for error in errors), errors
        )

        missing_dimension = copy.deepcopy(contract)
        dimension_id = missing_dimension["core_principles"][0][
            "required_dimensions"
        ][0]
        for outcome in missing_dimension["principle_acceptance_contract"][
            "outcomes"
        ]:
            if dimension_id in outcome["dimensions"]:
                outcome["dimensions"].remove(dimension_id)
        errors = EVALUATOR.validate_principle_acceptance_contract(
            missing_dimension, ROOT
        )
        self.assertTrue(
            any("exactly cover required_dimensions" in error for error in errors),
            errors,
        )

    def test_canonical_expert_outcomes_are_independent_and_cross_axis_safe(self) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        principles = {row["id"]: row for row in contract["core_principles"]}
        self.assertEqual(
            [
                "readability-review-current",
                "content-audit-formal-release-current",
            ],
            principles["ai-first"]["required_outcomes"]["formal_release"],
        )
        self.assertEqual(
            ["professional-completeness-review-current"],
            principles["professional-skill-injection"]["required_outcomes"][
                "formal_release"
            ],
        )
        self.assertEqual(
            [
                "professional-review-cost-current",
                "professionalism-formal-release-ready",
            ],
            principles["final-goal"]["required_outcomes"]["formal_release"],
        )
        outcomes = {
            row["id"]: row
            for row in contract["principle_acceptance_contract"]["outcomes"]
        }
        readability = outcomes["readability-review-current"]
        completeness = outcomes["professional-completeness-review-current"]
        review_cost = outcomes["professional-review-cost-current"]
        self.assertEqual(["ai-first-expert-disposition"], readability["dimensions"])
        self.assertEqual(
            ["professional-skill-injection-expert-disposition"],
            completeness["dimensions"],
        )
        readability_pointers = {row["pointer"] for row in readability["predicates"]}
        completeness_pointers = {row["pointer"] for row in completeness["predicates"]}
        self.assertTrue(
            all("professional_completeness" not in item for item in readability_pointers)
        )
        self.assertTrue(all("/readability/" not in item for item in completeness_pointers))

        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        report_path = root / "reports/professionalism-regression-report.json"
        report_path.write_text(
            json.dumps(
                {
                    "content_readiness": {
                        "schema_version": 9,
                        "aggregate": {
                            "readability_review_current": True,
                            "professional_completeness_review_current": False,
                        },
                        "expert": {
                            "readability": {
                                "decision_complete": True,
                                "storage_current": True,
                                "source_current": True,
                                "accepted_for_formal": True,
                                "panel_artifact_schema_version": 2,
                                "tracked_tightening_count": 0,
                                "detector_false_positive_count": 0,
                                "rewrite_required_count": 0,
                                "blocker_count": 0,
                            },
                            "professional_completeness": {
                                "decision_complete": False,
                                "storage_current": False,
                                "source_current": False,
                                "accepted_for_formal": False,
                                "panel_artifact_schema_version": None,
                                "evidence_contract_satisfied": False,
                                "qualification_summary": None,
                                "evidence_summary": None,
                                "required_target_count": 189,
                                "applied_target_count": 0,
                                "accepted_current_count": None,
                                "correction_count": None,
                            },
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        results, _by_id = EVALUATOR._evaluate_outcomes(
            root,
            [readability, completeness],
            {
                "validate-professionalism-regression": {
                    "exit_code": 0,
                    "status": "pass",
                }
            },
            {},
        )
        self.assertEqual(
            {"readability-review-current": "pass", "professional-completeness-review-current": "fail"},
            {row["id"]: row["status"] for row in results},
        )

        schema_two = self._passing_report(completeness)
        schema_two["content_readiness"]["expert"][
            "professional_completeness"
        ]["panel_artifact_schema_version"] = 2
        report_path.write_text(json.dumps(schema_two), encoding="utf-8")
        schema_results, _ = EVALUATOR._evaluate_outcomes(
            root,
            [completeness],
            {
                "validate-professionalism-regression": {
                    "exit_code": 0,
                    "status": "pass",
                }
            },
            {},
        )
        self.assertEqual("fail", schema_results[0]["status"])
        failed_schema_predicates = [
            row
            for row in schema_results[0]["predicates"]
            if row["status"] != "pass"
        ]
        self.assertEqual(1, len(failed_schema_predicates))
        self.assertEqual(
            "/content_readiness/expert/professional_completeness/panel_artifact_schema_version",
            failed_schema_predicates[0]["pointer"],
        )

        authority_values = {
            "final-goal-authority": contract["final_goal_contract"]
        }
        missing_cost_current = self._passing_report(
            review_cost,
            authority_values,
        )
        missing_cost_current["content_readiness"]["expert"][
            "professional_completeness"
        ]["review_cost_current"] = False
        report_path.write_text(json.dumps(missing_cost_current), encoding="utf-8")
        cost_results, _ = EVALUATOR._evaluate_outcomes(
            root,
            [review_cost],
            {
                "validate-professionalism-regression": {
                    "exit_code": 0,
                    "status": "pass",
                }
            },
            authority_values,
        )
        self.assertEqual("fail", cost_results[0]["status"])
        self.assertEqual(
            [
                "/content_readiness/expert/professional_completeness/review_cost_current"
            ],
            [
                row["pointer"]
                for row in cost_results[0]["predicates"]
                if row["status"] != "pass"
            ],
        )

    def test_professional_review_cost_authoring_and_formal_policy_are_separate(
        self,
    ) -> None:
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        outcomes = {
            row["id"]: row
            for row in contract["principle_acceptance_contract"]["outcomes"]
        }
        authoring_cost = outcomes["professional-review-cost-fixtures-valid"]
        formal_cost = outcomes["professional-review-cost-current"]
        report_source = "reports/professionalism-regression-report.json"
        sensitivity_pointer = (
            "/professional_review_cost_fixtures/"
            "routing_neutral_isolated_material_binding_sensitivity"
        )

        self.assertEqual(
            [
                {
                    "source": "process",
                    "pointer": "/exit_code",
                    "operator": "equals",
                    "expected": 0,
                },
                {
                    "source": report_source,
                    "pointer": "/professional_review_cost_fixtures/schema_version",
                    "operator": "equals",
                    "expected": 1,
                },
            ],
            authoring_cost["predicates"],
        )
        pointers = {
            predicate["pointer"]: predicate
            for predicate in formal_cost["predicates"]
            if predicate["source"] == report_source
        }
        self.assertEqual(
            {
                "/content_readiness/expert/professional_completeness/panel_artifact_schema_version",
                "/content_readiness/expert/professional_completeness/panel_size",
                "/content_readiness/expert/professional_completeness/required_target_count",
                "/content_readiness/expert/professional_completeness/review_cost_current",
                "/content_readiness/expert/professional_completeness/review_cost/effective_vote_count",
                "/content_readiness/expert/professional_completeness/review_cost/effective_criterion_result_count",
                "/professional_review_cost_fixtures/status",
                f"{sensitivity_pointer}/case_count",
                f"{sensitivity_pointer}/fresh_target_count/max",
                f"{sensitivity_pointer}/input_ratio_ppm/max",
            },
            set(pointers),
        )
        self.assertFalse(
            any(
                "locked_current_catalog" in json.dumps(predicate)
                for predicate in formal_cost["predicates"]
            )
        )
        authority_values = {
            "final-goal-authority": contract["final_goal_contract"]
        }
        self.assertEqual(
            {"thresholds", "formal_round_policy"},
            set(
                authority_values["final-goal-authority"][
                    "professional_review_cost_fixtures"
                ]
            ),
        )
        positive_report = self._passing_report(formal_cost, authority_values)
        positive_report["professional_review_cost_fixtures"][
            "schema_version"
        ] = 1
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        synthetic_report_path = root / report_source
        producer_results = {
            "validate-professionalism-regression": {
                "exit_code": 0,
                "status": "pass",
            }
        }

        def outcome_status(candidate: dict) -> str:
            synthetic_report_path.write_text(
                json.dumps(candidate),
                encoding="utf-8",
            )
            results, _ = EVALUATOR._evaluate_outcomes(
                root,
                [formal_cost],
                producer_results,
                authority_values,
            )
            return results[0]["status"]

        self.assertEqual("pass", outcome_status(positive_report))

        digest_only = copy.deepcopy(positive_report)
        digest_only["professional_review_cost_fixtures"][
            "routing_neutral_isolated_material_binding_sensitivity"
        ]["cases_fingerprint"] = "f" * 64
        self.assertEqual("pass", outcome_status(digest_only))

        mutations = {
            "status": lambda report: report[
                "professional_review_cost_fixtures"
            ].update({"status": "formal-non-current"}),
            "case-count": lambda report: report[
                "professional_review_cost_fixtures"
            ]["routing_neutral_isolated_material_binding_sensitivity"].update(
                {"case_count": 188}
            ),
            "float-count": lambda report: report[
                "professional_review_cost_fixtures"
            ]["routing_neutral_isolated_material_binding_sensitivity"].update(
                {"case_count": 189.0}
            ),
            "panel-size": lambda report: report["content_readiness"]["expert"][
                "professional_completeness"
            ].update({"panel_size": 2}),
            "currentness": lambda report: report["content_readiness"]["expert"][
                "professional_completeness"
            ].update({"review_cost_current": False}),
            "fresh-threshold": lambda report: report[
                "professional_review_cost_fixtures"
            ]["routing_neutral_isolated_material_binding_sensitivity"][
                "fresh_target_count"
            ].update({"max": 57}),
            "ratio-threshold": lambda report: report[
                "professional_review_cost_fixtures"
            ]["routing_neutral_isolated_material_binding_sensitivity"][
                "input_ratio_ppm"
            ].update({"max": 450001}),
        }
        for label, mutate in mutations.items():
            candidate = copy.deepcopy(positive_report)
            mutate(candidate)
            with self.subTest(label=label):
                self.assertEqual("fail", outcome_status(candidate))

    def test_report_must_be_fresh_json_without_scalar_hashes(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        stale_script = self._script(root, "stale", "raise SystemExit(0)\n")
        report_path = root / "reports/result.json"
        report_path.write_text('{"schema_version": 1, "status": "pass"}\n')
        producers = [
            self._producer(
                "stale", stale_script, reports=["reports/result.json"]
            )
        ]
        outcomes = [
            {
                "id": "stale-pass",
                "producer": "stale",
                "predicates": [
                    PROCESS_PASS,
                    REPORT_SCHEMA,
                    {
                        "source": "reports/result.json",
                        "pointer": "/status",
                        "operator": "equals",
                        "expected": "pass",
                    },
                ],
            }
        ]
        contract = self._contract(producers, outcomes)
        stale = EVALUATOR.evaluate(root, contract)
        self.assertEqual("fail", stale["producers"][0]["status"])
        self.assertFalse(stale["producers"][0]["reports"][0]["fresh"])
        self.assertEqual(
            ["report-not-refreshed"],
            stale["producers"][0]["failure_reason_codes"],
        )

        writer = self._script(
            root,
            "writer",
            "from pathlib import Path\n"
            "Path('reports/result.json').write_text('{\"schema_version\":1,\"status\":\"pass\"}\\n')\n",
        )
        contract["principle_acceptance_contract"]["producers"][0]["argv"] = [
            "python3",
            writer,
        ]
        fresh = EVALUATOR.evaluate(root, contract)
        artifact = fresh["producers"][0]["reports"][0]
        self.assertEqual("pass", fresh["producers"][0]["status"])
        self.assertNotIn("stdout_sha256", fresh["producers"][0])
        self.assertNotIn("stderr_sha256", fresh["producers"][0])
        self.assertTrue(artifact["fresh"])
        self.assertTrue(artifact["json_object"])
        self.assertNotIn("sha256", artifact)

    def test_report_schema_missing_wrong_type_and_wrong_version_fail_closed(self) -> None:
        cases = (
            ("missing", {"status": "pass"}, "pointer-error", None),
            ("wrong-type", {"schema_version": "1"}, "resolved", "string"),
            ("wrong-version", {"schema_version": 2}, "resolved", "integer"),
        )
        for label, payload, resolution_status, actual_type in cases:
            with self.subTest(case=label):
                temporary, root = self._root()
                self.addCleanup(temporary.cleanup)
                writer = self._script(
                    root,
                    f"schema_{label.replace('-', '_')}",
                    "from pathlib import Path\n"
                    f"Path('reports/result.json').write_text({json.dumps(payload)!r} + '\\n')\n",
                )
                report = EVALUATOR.evaluate(
                    root,
                    self._contract(
                        [
                            self._producer(
                                f"schema-{label}",
                                writer,
                                reports=["reports/result.json"],
                            )
                        ],
                        [
                            {
                                "id": f"schema-{label}-valid",
                                "producer": f"schema-{label}",
                                "predicates": [PROCESS_PASS, REPORT_SCHEMA],
                            }
                        ],
                    ),
                )
                producer = report["producers"][0]
                schema_predicate = report["outcomes"][0]["predicates"][1]
                self.assertEqual("pass", producer["status"])
                self.assertEqual("fail", report["outcomes"][0]["status"])
                self.assertEqual(resolution_status, schema_predicate["resolution_status"])
                self.assertEqual("fail", schema_predicate["status"])
                if actual_type is None:
                    self.assertIsNone(schema_predicate["actual_metadata"])
                else:
                    self.assertEqual(
                        actual_type,
                        schema_predicate["actual_metadata"]["type"],
                    )

    def test_report_must_be_a_json_object(self) -> None:
        cases = (("array", []), ("string", "report"), ("null", None))
        for label, payload in cases:
            with self.subTest(case=label):
                temporary, root = self._root()
                self.addCleanup(temporary.cleanup)
                writer = self._script(
                    root,
                    f"non_object_{label}",
                    "from pathlib import Path\n"
                    f"Path('reports/result.json').write_text({json.dumps(payload)!r} + '\\n')\n",
                )
                report = EVALUATOR.evaluate(
                    root,
                    self._contract(
                        [
                            self._producer(
                                f"non-object-{label}",
                                writer,
                                reports=["reports/result.json"],
                            )
                        ],
                        [
                            {
                                "id": f"non-object-{label}-valid",
                                "producer": f"non-object-{label}",
                                "predicates": [PROCESS_PASS, REPORT_SCHEMA],
                            }
                        ],
                    ),
                )
                producer = report["producers"][0]
                artifact = producer["reports"][0]
                self.assertEqual("fail", producer["status"])
                self.assertTrue(artifact["fresh"])
                self.assertFalse(artifact["json_object"])
                self.assertEqual(
                    ["report-not-json-object"],
                    producer["failure_reason_codes"],
                )
                self.assertEqual("fail", report["outcomes"][0]["status"])

    def test_source_mutation_fails_even_when_process_passes(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        mutate = self._script(
            root,
            "mutate",
            "from pathlib import Path\n"
            "Path('src/mutated.txt').write_text('changed')\n",
        )
        contract = self._contract(
            [self._producer("mutate", mutate)],
            [{"id": "mutate-pass", "producer": "mutate", "predicates": [PROCESS_PASS]}],
        )
        report = EVALUATOR.evaluate(root, contract)
        self.assertEqual("fail", report["producers"][0]["status"])
        self.assertFalse(report["producers"][0]["source_unchanged"])
        self.assertFalse(report["input_tree"]["unchanged"])

    def test_ordinary_source_mutation_is_deferred_until_all_producers_finish(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        mutate = self._script(
            root,
            "ordinary_mutate",
            "from pathlib import Path\n"
            "Path('src/mutated.txt').write_text('changed')\n",
        )
        successor = self._script(
            root,
            "ordinary_successor",
            "from pathlib import Path\n"
            "Path('reports/successor-ran').write_text('yes')\n",
        )
        producers = [
            self._producer("mutate", mutate),
            self._producer("successor", successor, depends_on=["mutate"]),
        ]
        contract = self._contract(
            producers,
            [
                {
                    "id": "mutate-pass",
                    "producer": "mutate",
                    "predicates": [PROCESS_PASS],
                },
                {
                    "id": "successor-pass",
                    "producer": "successor",
                    "predicates": [PROCESS_PASS],
                },
            ],
        )

        with mock.patch.object(
            EVALUATOR,
            "input_tree_digest",
            wraps=EVALUATOR.input_tree_digest,
        ) as digest:
            report = EVALUATOR.evaluate(root, contract)

        self.assertEqual(2, digest.call_count)
        self.assertEqual(2, report["command_execution_count"])
        self.assertTrue((root / "reports/successor-ran").is_file())
        self.assertEqual("fail", report["authoring_principles_status"])
        self.assertFalse(report["input_tree"]["unchanged"])
        for producer in report["producers"]:
            self.assertEqual("fail", producer["status"])
            self.assertFalse(producer["source_unchanged"])
            self.assertIn("source-tree-mutated", producer["failure_reason_codes"])

    def test_formal_source_mutation_prevents_dependent_successor(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        mutate = self._script(
            root,
            "formal_mutate",
            "from pathlib import Path\n"
            "Path('src/mutated.txt').write_text('changed')\n",
        )
        successor = self._script(
            root,
            "formal_successor",
            "from pathlib import Path\n"
            "Path('reports/successor-ran').write_text('yes')\n",
        )
        producers = [
            self._producer("mutate", mutate),
            self._producer("successor", successor, depends_on=["mutate"]),
        ]
        contract = self._contract(
            producers,
            [
                {
                    "id": "mutate-pass",
                    "producer": "mutate",
                    "predicates": [PROCESS_PASS],
                },
                {
                    "id": "successor-pass",
                    "producer": "successor",
                    "predicates": [PROCESS_PASS],
                },
            ],
        )

        report = EVALUATOR.evaluate(root, contract, release_projection=True)

        by_id = {producer["id"]: producer for producer in report["producers"]}
        self.assertEqual("fail", by_id["mutate"]["status"])
        self.assertFalse(by_id["mutate"]["source_unchanged"])
        self.assertEqual("not_run", by_id["successor"]["status"])
        self.assertFalse((root / "reports/successor-ran").exists())

    def test_tree_digest_cost_is_constant_for_ordinary_and_linear_for_formal(
        self,
    ) -> None:
        for release_projection, expected_calls in ((False, 2), (True, 4)):
            with self.subTest(release_projection=release_projection):
                temporary, root = self._root()
                self.addCleanup(temporary.cleanup)
                producers = []
                outcomes = []
                previous: str | None = None
                for index in range(3):
                    producer_id = f"producer-{index}"
                    script = self._script(
                        root,
                        producer_id,
                        "raise SystemExit(0)\n",
                    )
                    producers.append(
                        self._producer(
                            producer_id,
                            script,
                            depends_on=[] if previous is None else [previous],
                        )
                    )
                    outcomes.append(
                        {
                            "id": f"{producer_id}-pass",
                            "producer": producer_id,
                            "predicates": [PROCESS_PASS],
                        }
                    )
                    previous = producer_id
                with mock.patch.object(
                    EVALUATOR,
                    "input_tree_digest",
                    wraps=EVALUATOR.input_tree_digest,
                ) as digest:
                    report = EVALUATOR.evaluate(
                        root,
                        self._contract(producers, outcomes),
                        release_projection=release_projection,
                    )
                self.assertEqual("pass", report["authoring_principles_status"])
                self.assertEqual(expected_calls, digest.call_count)

    def test_all_closed_predicate_operators(self) -> None:
        cases = (
            (3, "equals", 3, True),
            (3, "not_equals", 4, True),
            (3, "greater_than_or_equal", 2, True),
            (3, "less_than_or_equal", 4, True),
            (["a", "b"], "contains", "a", True),
            ({"a": 1}, "not_contains", "b", True),
            (True, "equals", 1, False),
            ("a", "greater_than_or_equal", "a", False),
        )
        for actual, operator, expected, result in cases:
            with self.subTest(operator=operator, actual=actual):
                self.assertEqual(
                    result,
                    EVALUATOR.evaluate_operator(actual, operator, expected),
                )

    def test_one_command_supplies_multiple_outcomes_without_rerun(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "once",
            "from pathlib import Path\nimport json\n"
            "counter=Path('reports/counter.txt')\n"
            "value=int(counter.read_text())+1 if counter.exists() else 1\n"
            "counter.write_text(str(value))\n"
            "Path('reports/result.json').write_text(json.dumps({'schema_version':1,'value':value})+'\\n')\n",
        )
        producer = self._producer(
            "once", script, reports=["reports/result.json"]
        )
        predicates = [
            PROCESS_PASS,
            REPORT_SCHEMA,
            {
                "source": "reports/result.json",
                "pointer": "/value",
                "operator": "equals",
                "expected": 1,
            },
        ]
        outcomes = [
            {"id": "one", "producer": "once", "predicates": predicates},
            {"id": "two", "producer": "once", "predicates": predicates},
        ]
        contract = self._contract([producer], outcomes)
        report = EVALUATOR.evaluate(root, contract)
        self.assertEqual(1, report["command_execution_count"])
        self.assertEqual("1", (root / "reports/counter.txt").read_text())
        self.assertTrue(all(item["status"] == "pass" for item in report["outcomes"]))
        authority = report["authorities"][0]
        self.assertNotIn("status", authority)
        self.assertNotIn("value_sha256", authority)
        self.assertEqual("once", authority["consumer_results"][0]["producer"])
        self.assertEqual("pass", authority["consumer_results"][0]["producer_status"])

    def test_authoring_pass_and_formal_release_blocked_is_partial(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "formal",
            "from pathlib import Path\nimport json\n"
            "Path('reports/result.json').write_text(json.dumps({'schema_version':1,'authoring':True,'formal':False})+'\\n')\n",
        )
        producer = self._producer(
            "formal", script, reports=["reports/result.json"]
        )
        authoring = {
            "id": "authoring-pass",
            "producer": "formal",
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/authoring",
                    "operator": "equals",
                    "expected": True,
                },
            ],
        }
        formal = {
            "id": "formal-pass",
            "producer": "formal",
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/formal",
                    "operator": "equals",
                    "expected": True,
                },
            ],
        }
        contract = self._contract(
            [producer], [authoring, formal], formal_outcomes=["formal-pass"]
        )
        report = EVALUATOR.evaluate(root, contract)
        self.assertEqual("pass", report["authoring_principles_status"])
        self.assertEqual("blocked", report["formal_principles_status"])
        self.assertEqual("partial", report["principles_status"])

    def test_local_core_reports_exclude_retired_remote_release_gate(self) -> None:
        expected_gates = [
            "examples-validation",
            "showcase-freshness",
            "marketplace-catalog-freshness",
            "marketplace-index-validation",
            "productization-assets-validation",
            "open-source-readiness",
            "unit-tests",
            "codegen-benchmark-validation",
            "codegen-benchmark-sample-run",
            "quickstart-dry-runs",
        ]
        remote_limitation = (
            "Local Core evidence does not provide hosted CI, remote workflow "
            "execution, remote artifact upload, remote tag or object binding, or "
            "remote branch or check-state evidence; none is a required, pending, "
            "or mandatory local gate."
        )
        self.assertEqual(
            expected_gates,
            EVALUATOR.UNCOVERED_MANDATORY_RELEASE_GATES,
        )
        self.assertIn(remote_limitation, EVALUATOR.EVIDENCE_LIMITATIONS)

        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "local",
            "from pathlib import Path\n"
            "Path('reports/result.json').write_text('{\"schema_version\":1,\"status\":\"pass\"}\\n')\n",
        )
        outcome = {
            "id": "local-pass",
            "producer": "local",
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/status",
                    "operator": "equals",
                    "expected": "pass",
                },
            ],
        }
        ordinary = EVALUATOR.evaluate(
            root,
            self._contract(
                [self._producer("local", script, reports=["reports/result.json"])],
                [outcome],
            ),
        )
        failure = EVALUATOR._invalid_report(root, None, ["fixture-invalid"])
        for report in (ordinary, failure):
            self.assertEqual(expected_gates, report["uncovered_mandatory_release_gates"])
            self.assertEqual(EVALUATOR.EVIDENCE_LIMITATIONS, report["limitations"])
            self.assertIn(remote_limitation, report["limitations"])

    def test_authoring_predicate_failure_is_fail(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "authoring",
            "from pathlib import Path\n"
            "Path('reports/result.json').write_text('{\"schema_version\":1,\"status\":\"fail\"}\\n')\n",
        )
        outcome = {
            "id": "authoring-pass",
            "producer": "authoring",
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/status",
                    "operator": "equals",
                    "expected": "pass",
                },
            ],
        }
        contract = self._contract(
            [self._producer("authoring", script, reports=["reports/result.json"])],
            [outcome],
        )
        report = EVALUATOR.evaluate(root, contract)
        self.assertEqual("fail", report["authoring_principles_status"])
        self.assertEqual("fail", report["principles_status"])

    def test_failure_report_contains_only_closed_reason_codes(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "noisy",
            "print('x'*5000+'SECRET_END')\nraise SystemExit(1)\n",
        )
        contract = self._contract(
            [self._producer("noisy", script)],
            [{"id": "noisy-pass", "producer": "noisy", "predicates": [PROCESS_PASS]}],
        )
        report = EVALUATOR.evaluate(root, contract)
        producer = report["producers"][0]
        self.assertEqual(["process-exit-nonzero"], producer["failure_reason_codes"])
        serialized = json.dumps(report)
        self.assertNotIn("SECRET_END", serialized)
        self.assertNotIn("failure_summary", producer)
        self.assertNotIn("stdout_sha256", producer)
        self.assertNotIn("stderr_sha256", producer)
        self.assertNotIn("stdout", producer)
        self.assertNotIn("stderr", producer)

    def test_predicate_actual_and_pointer_errors_never_persist_secret_values(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        secret = "DO_NOT_PERSIST_9f2a7f"
        script = self._script(
            root,
            "secret_report",
            "from pathlib import Path\nimport json\n"
            f"payload={{'schema_version':1,'errors':{{'detail':{secret!r}}}}}\n"
            "Path('reports/result.json').write_text(json.dumps(payload)+'\\n')\n",
        )
        outcome = {
            "id": "secret-pass",
            "producer": "secret-report",
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/errors/detail",
                    "operator": "equals",
                    "expected": "closed-public-value",
                },
                {
                    "source": "reports/result.json",
                    "pointer": "/errors/missing",
                    "operator": "equals",
                    "expected": "closed-public-value",
                },
            ],
        }
        report = EVALUATOR.evaluate(
            root,
            self._contract(
                [
                    self._producer(
                        "secret-report", script, reports=["reports/result.json"]
                    )
                ],
                [outcome],
            ),
        )
        serialized = json.dumps(report)
        self.assertNotIn(secret, serialized)
        predicates = report["outcomes"][0]["predicates"]
        resolved = predicates[2]
        self.assertNotIn("actual", resolved)
        self.assertNotIn("error", resolved)
        self.assertEqual("string", resolved["actual_metadata"]["type"])
        self.assertEqual(len(secret), resolved["actual_metadata"]["length"])
        self.assertEqual("pointer-error", predicates[3]["resolution_status"])
        self.assertIsNone(predicates[3]["actual_metadata"])

    def test_ssot_requires_both_exact_prompt_and_profile_producers(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        prompt = self._script(root, "prompt", "raise SystemExit(0)\n")
        profile = self._script(root, "profile", "raise SystemExit(1)\n")
        producers = [
            self._producer("prompt", prompt),
            self._producer("profile", profile),
        ]
        outcomes = [
            {"id": "prompt-exact", "producer": "prompt", "predicates": [PROCESS_PASS]},
            {"id": "profile-exact", "producer": "profile", "predicates": [PROCESS_PASS]},
        ]
        contract = self._contract(producers, outcomes)
        report = EVALUATOR.evaluate(root, contract)
        self.assertEqual("pass", report["outcomes"][0]["status"])
        self.assertEqual("fail", report["outcomes"][1]["status"])
        self.assertEqual("fail", report["authoring_principles_status"])

    def test_evaluation_writes_reports_before_nonzero_formal_gate_exit(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "formal",
            "from pathlib import Path\n"
            "Path('reports/result.json').write_text('{\"schema_version\":1,\"formal\":false}\\n')\n",
        )
        authoring = {
            "id": "authoring-pass",
            "producer": "formal",
            "predicates": [PROCESS_PASS],
        }
        formal = {
            "id": "formal-pass",
            "producer": "formal",
            "predicates": [
                PROCESS_PASS,
                REPORT_SCHEMA,
                {
                    "source": "reports/result.json",
                    "pointer": "/formal",
                    "operator": "equals",
                    "expected": True,
                },
            ],
        }
        contract = self._contract(
            [self._producer("formal", script, reports=["reports/result.json"])],
            [authoring, formal],
            formal_outcomes=["formal-pass"],
        )
        self._write_contract(root, contract)
        authoring_exit = EVALUATOR.main(
            ["--root", str(root), "--gate", "authoring"]
        )
        self.assertEqual(0, authoring_exit)
        authoring_json = (root / EVALUATOR.JSON_REPORT).read_bytes()
        self.assertFalse((root / EVALUATOR.MARKDOWN_REPORT).exists())
        formal_report = EVALUATOR.evaluate(
            root,
            contract,
            contract_sha256=EVALUATOR._sha256_bytes(
                (root / EVALUATOR.CANONICAL_CONTRACT_SOURCE).read_bytes()
            ),
            release_projection=True,
        )
        EVALUATOR.write_reports(root, formal_report, release_projection=True)
        formal_exit = (
            0 if formal_report["formal_principles_status"] == "pass" else 1
        )
        self.assertEqual(1, formal_exit)
        self.assertTrue((root / EVALUATOR.JSON_REPORT).is_file())
        self.assertTrue((root / EVALUATOR.MARKDOWN_REPORT).is_file())
        self.assertNotEqual(
            authoring_json, (root / EVALUATOR.JSON_REPORT).read_bytes()
        )
        report = json.loads((root / EVALUATOR.JSON_REPORT).read_text())
        self.assertEqual("partial", report["principles_status"])
        self.assertEqual([], EVALUATOR.validate_saved_report(root, report))
        tampered = copy.deepcopy(report)
        tampered["outcomes"][-1]["status"] = "pass"
        errors = EVALUATOR.validate_saved_report(root, tampered)
        self.assertTrue(
            any("outcome predicates are stale or inconsistent" in item for item in errors),
            errors,
        )

        schema_mutations = []
        for bad_contract_errors in (0, {}):
            schema_mutations.append(
                (
                    f"contract-errors-{type(bad_contract_errors).__name__}",
                    lambda value, bad=bad_contract_errors: value.__setitem__(
                        "contract_errors", bad
                    ),
                    "contract_errors must be a list",
                )
            )
        schema_mutations.extend(
            [
                (
                    "producer-reports-type",
                    lambda value: value["producers"][0].__setitem__(
                        "reports", {}
                    ),
                    "producers[0].reports must be a list",
                ),
                (
                    "authorities-type",
                    lambda value: value.__setitem__("authorities", {}),
                    "authorities must be a list",
                ),
                (
                    "artifact-unknown-field",
                    lambda value: value["producers"][0]["reports"][0].__setitem__(
                        "unknown", True
                    ),
                    "reports[0] fields do not match the closed schema",
                ),
                (
                    "predicate-missing-field",
                    lambda value: value["outcomes"][0]["predicates"][0].pop(
                        "resolution_status"
                    ),
                    "predicates[0] fields do not match the closed schema",
                ),
                (
                    "actual-metadata-unknown-field",
                    lambda value: value["outcomes"][0]["predicates"][0][
                        "actual_metadata"
                    ].__setitem__("raw", "forbidden"),
                    "actual_metadata fields do not match the closed schema",
                ),
                (
                    "authority-consumer-shape",
                    lambda value: value["authorities"][0][
                        "consumer_results"
                    ].__setitem__(0, []),
                    "consumer_results[0] must be an object",
                ),
                (
                    "principle-required-outcomes-unknown-field",
                    lambda value: value["principles"][0][
                        "required_outcomes"
                    ].__setitem__("unknown", []),
                    "required_outcomes fields do not match the closed schema",
                ),
            ]
        )
        for label, mutate, marker in schema_mutations:
            with self.subTest(schema=label):
                tampered = copy.deepcopy(report)
                mutate(tampered)
                errors = EVALUATOR.validate_saved_report(root, tampered)
                self.assertTrue(any(marker in item for item in errors), errors)
                self.assertLessEqual(
                    len(errors), EVALUATOR.MAX_SAVED_REPORT_SCHEMA_ERRORS
                )

        alternate = root / "src/control-model/alternate-contract.json"
        alternate.write_bytes((root / EVALUATOR.CANONICAL_CONTRACT_SOURCE).read_bytes())
        tampered = copy.deepcopy(report)
        tampered["contract_source"] = "src/control-model/alternate-contract.json"
        errors = EVALUATOR.validate_saved_report(root, tampered)
        self.assertTrue(
            any("must be the canonical" in item for item in errors),
            errors,
        )

    def test_ordinary_saved_report_is_historical_and_skips_current_tree_digest(
        self,
    ) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "historical",
            "from pathlib import Path\n"
            "Path('reports/result.json').write_text('{\"schema_version\":1}\\n')\n",
        )
        contract = self._contract(
            [
                self._producer(
                    "historical", script, reports=["reports/result.json"]
                )
            ],
            [
                {
                    "id": "historical-pass",
                    "producer": "historical",
                    "predicates": [PROCESS_PASS, REPORT_SCHEMA],
                }
            ],
        )
        self._write_contract(root, contract)
        report = EVALUATOR.evaluate(
            root,
            contract,
            contract_sha256=EVALUATOR._sha256_bytes(
                (root / EVALUATOR.CANONICAL_CONTRACT_SOURCE).read_bytes()
            ),
        )
        (root / "docs").mkdir()
        (root / "docs/unrelated.md").write_text("changed\n", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests/test_unrelated.py").write_text(
            "# changed\n", encoding="utf-8"
        )
        (root / "scripts/unrelated-runner.py").write_text(
            "raise SystemExit(0)\n", encoding="utf-8"
        )

        with mock.patch.object(
            EVALUATOR,
            "input_tree_digest",
            side_effect=AssertionError("ordinary validation hashed the current tree"),
        ) as digest:
            self.assertEqual([], EVALUATOR.validate_saved_report(root, report))
        self.assertEqual(0, digest.call_count)

        tampered_tree = copy.deepcopy(report)
        tampered_tree["input_tree"]["post"]["sha256"] = "0" * 64
        with mock.patch.object(
            EVALUATOR,
            "input_tree_digest",
            side_effect=AssertionError("ordinary validation hashed the current tree"),
        ):
            errors = EVALUATOR.validate_saved_report(root, tampered_tree)
        self.assertTrue(
            any("records an input tree mutation" in item for item in errors),
            errors,
        )

        semantic_tampering = (
            (
                "contract hash",
                lambda value: value.__setitem__("contract_sha256", "0" * 64),
                "contract hash is stale",
            ),
            (
                "producer identity",
                lambda value: value["producers"][0]["argv"].append("--changed"),
                "producer contract is stale",
            ),
            (
                "artifact evidence",
                lambda value: value["producers"][0]["reports"][0].__setitem__(
                    "fresh", False
                ),
                "was not fresh JSON",
            ),
            (
                "outcome predicate",
                lambda value: value["outcomes"][0].__setitem__("status", "fail"),
                "outcome predicates are stale or inconsistent",
            ),
            (
                "principle projection",
                lambda value: value["principles"][0].__setitem__(
                    "name", "tampered"
                ),
                "principle statuses are stale or inconsistent",
            ),
            (
                "authority projection",
                lambda value: value["authorities"][0].__setitem__(
                    "source", "tampered"
                ),
                "authority consumers are stale or inconsistent",
            ),
        )
        for label, mutate, marker in semantic_tampering:
            with self.subTest(tamper=label), mock.patch.object(
                EVALUATOR,
                "input_tree_digest",
                side_effect=AssertionError(
                    "ordinary validation hashed the current tree"
                ),
            ):
                tampered = copy.deepcopy(report)
                mutate(tampered)
                errors = EVALUATOR.validate_saved_report(root, tampered)
                self.assertTrue(any(marker in item for item in errors), errors)

    def test_formal_saved_report_still_requires_the_current_tree_digest(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(root, "formal-current", "raise SystemExit(0)\n")
        contract = self._contract(
            [self._producer("formal-current", script)],
            [
                {
                    "id": "formal-current-pass",
                    "producer": "formal-current",
                    "predicates": [PROCESS_PASS],
                }
            ],
        )
        self._write_contract(root, contract)
        report = EVALUATOR.evaluate(
            root,
            contract,
            contract_sha256=EVALUATOR._sha256_bytes(
                (root / EVALUATOR.CANONICAL_CONTRACT_SOURCE).read_bytes()
            ),
            release_projection=True,
        )
        (root / "docs").mkdir()
        (root / "docs/formal-stale.md").write_text("changed\n", encoding="utf-8")

        with mock.patch.object(
            EVALUATOR,
            "input_tree_digest",
            wraps=EVALUATOR.input_tree_digest,
        ) as digest:
            errors = EVALUATOR.validate_saved_report(root, report)
        self.assertEqual(1, digest.call_count)
        self.assertTrue(
            any("input tree digest is stale" in item for item in errors),
            errors,
        )

    def test_formal_report_graph_uses_only_head_scoped_staging(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        source = self._script(
            root,
            "source-report",
            "import argparse, json\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--reports-dir', type=Path, default=Path('reports'))\n"
            "parser.add_argument('--release-projection', action='store_true')\n"
            "args = parser.parse_args()\n"
            "args.reports_dir.mkdir(parents=True, exist_ok=True)\n"
            "(args.reports_dir / 'source.json').write_text(json.dumps("
            "{'schema_version': 1, 'value': 'staging-source'}) + '\\n')\n"
            "if args.release_projection:\n"
            "    (args.reports_dir / 'source.md').write_text('# staging source\\n')\n",
        )
        consumer = self._script(
            root,
            "consumer-report",
            "import argparse, json\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--reports-dir', type=Path, default=Path('reports'))\n"
            "parser.add_argument('--release-projection', action='store_true')\n"
            "args = parser.parse_args()\n"
            "source = json.loads((args.reports_dir / 'source.json').read_text())\n"
            "args.reports_dir.mkdir(parents=True, exist_ok=True)\n"
            "value = 'staging-consumer' if source.get('value') == 'staging-source' else 'wrong'\n"
            "(args.reports_dir / 'consumer.json').write_text(json.dumps("
            "{'schema_version': 1, 'value': value}) + '\\n')\n"
            "if args.release_projection:\n"
            "    (args.reports_dir / 'consumer.md').write_text('# staging consumer\\n')\n",
        )
        docs_consumer = self._script(
            root,
            "validate-docs-consistency",
            "import argparse, json\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--reports-dir', type=Path, required=True)\n"
            "args = parser.parse_args()\n"
            "source = json.loads((args.reports_dir / 'source.json').read_text())\n"
            "raise SystemExit(0 if source.get('value') == 'staging-source' else 1)\n",
        )
        self._script(
            root,
            "validate-professionalism-regression",
            "import argparse, json, os\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--strict', action='store_true')\n"
            "parser.add_argument('--report-only', action='store_true')\n"
            "parser.add_argument('--release-projection', action='store_true')\n"
            "parser.add_argument('--reports-dir', type=Path, default=Path('reports'))\n"
            "parser.add_argument('--output-dir', type=Path)\n"
            "args = parser.parse_args()\n"
            "consumer = json.loads((args.reports_dir / 'consumer.json').read_text())\n"
            "output = args.output_dir or args.reports_dir\n"
            "output.mkdir(parents=True, exist_ok=True)\n"
            "payload = {'schema_version': 1, 'formal': consumer.get('value') == "
            "'staging-consumer', 'captured_head': os.environ.get("
            "'CHANGEFORGE_FORMAL_HEAD_COMMIT')}\n"
            "(output / 'professionalism-regression-report.json').write_text("
            "json.dumps(payload) + '\\n')\n"
            "if args.release_projection:\n"
            "    (output / 'professionalism-regression-report.md').write_text("
            "'# Formal professionalism\\n')\n",
        )
        professionalism = {
            "id": EVALUATOR.PROFESSIONALISM_PRODUCER_ID,
            "argv": list(EVALUATOR.PROFESSIONALISM_PRODUCER_ARGV),
            "depends_on": ["consumer-report", "validate-docs-consistency"],
            "reports": [EVALUATOR.PROFESSIONALISM_JSON_REPORT],
            "release_reports": [EVALUATOR.PROFESSIONALISM_MARKDOWN_REPORT],
            "authority_inputs": ["fixture-authority"],
            "timeout_seconds": EVALUATOR.PROFESSIONALISM_DECLARED_TIMEOUT_SECONDS,
        }
        producers = [
            self._producer(
                "source-report",
                source,
                reports=["reports/source.json"],
                release_reports=["reports/source.md"],
            ),
            self._producer(
                "consumer-report",
                consumer,
                depends_on=["source-report"],
                reports=["reports/consumer.json"],
                release_reports=["reports/consumer.md"],
            ),
            self._producer(
                "validate-docs-consistency",
                docs_consumer,
                depends_on=["source-report"],
            ),
            professionalism,
        ]
        outcomes = [
            {
                "id": "source-current",
                "producer": "source-report",
                "predicates": [
                    PROCESS_PASS,
                    {
                        "source": "reports/source.json",
                        "pointer": "/schema_version",
                        "operator": "equals",
                        "expected": 1,
                    },
                    {
                        "source": "reports/source.json",
                        "pointer": "/value",
                        "operator": "equals",
                        "expected": "staging-source",
                    },
                ],
            },
            {
                "id": "consumer-current",
                "producer": "consumer-report",
                "predicates": [
                    PROCESS_PASS,
                    {
                        "source": "reports/consumer.json",
                        "pointer": "/schema_version",
                        "operator": "equals",
                        "expected": 1,
                    },
                    {
                        "source": "reports/consumer.json",
                        "pointer": "/value",
                        "operator": "equals",
                        "expected": "staging-consumer",
                    },
                ],
            },
            {
                "id": "docs-current",
                "producer": "validate-docs-consistency",
                "predicates": [PROCESS_PASS],
            },
            {
                "id": "professionalism-authoring-current",
                "producer": EVALUATOR.PROFESSIONALISM_PRODUCER_ID,
                "predicates": [PROCESS_PASS],
            },
            {
                "id": "professionalism-formal-current",
                "producer": EVALUATOR.PROFESSIONALISM_PRODUCER_ID,
                "predicates": [
                    PROCESS_PASS,
                    {
                        "source": EVALUATOR.PROFESSIONALISM_JSON_REPORT,
                        "pointer": "/schema_version",
                        "operator": "equals",
                        "expected": 1,
                    },
                    {
                        "source": EVALUATOR.PROFESSIONALISM_JSON_REPORT,
                        "pointer": "/formal",
                        "operator": "equals",
                        "expected": True,
                    },
                ],
            },
        ]
        contract = self._contract(
            producers,
            outcomes,
            formal_outcomes=["professionalism-formal-current"],
        )
        self._write_contract(root, contract)
        tracked = {
            EVALUATOR.JSON_REPORT: b'{"ordinary":"core"}\n',
            "reports/source.json": b'{"value":"tracked-wrong"}\n',
            "reports/source.md": b"tracked source markdown\n",
            "reports/consumer.json": b'{"value":"tracked-wrong"}\n',
            "reports/consumer.md": b"tracked consumer markdown\n",
            EVALUATOR.PROFESSIONALISM_JSON_REPORT: b'{"ordinary":"professionalism"}\n',
            EVALUATOR.PROFESSIONALISM_MARKDOWN_REPORT: b"tracked professionalism markdown\n",
        }
        for relative, content in tracked.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (root / ".gitignore").write_text(
            ".rd-skills/formal-release/\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=root, check=True
        )
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
        head = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()

        self.assertEqual(
            0,
            EVALUATOR.main(["--root", str(root), "--gate", "formal-release"]),
        )

        formal_root = root / EVALUATOR.FORMAL_EVIDENCE_ROOT / head
        staging = formal_root / "producer-reports"
        evidence = formal_root / "reports"
        self.assertEqual(
            {"source.json", "source.md", "consumer.json", "consumer.md"},
            {path.name for path in staging.iterdir() if path.is_file()},
        )
        self.assertEqual(
            EVALUATOR.FORMAL_EVIDENCE_FILENAMES,
            {path.name for path in evidence.iterdir() if path.is_file()},
        )
        core = json.loads((evidence / "core-principles-outcomes.json").read_text())
        self.assertEqual("pass", core["formal_principles_status"])
        self.assertNotIn(str(staging), json.dumps(core))
        for producer in core["producers"]:
            for artifact in [*producer["reports"], *producer["release_reports"]]:
                self.assertTrue(artifact["path"].startswith("reports/"))
        for relative, content in tracked.items():
            self.assertEqual(content, (root / relative).read_bytes())
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
        self.assertEqual("", status)
        self.assertEqual(
            0,
            EVALUATOR.main(["--root", str(root), "--gate", "formal-release"]),
        )
        for relative, content in tracked.items():
            self.assertEqual(content, (root / relative).read_bytes())

    def test_formal_report_directory_injection_fails_closed(self) -> None:
        cases = (
            (
                "unsupported",
                "import argparse, json\n"
                "from pathlib import Path\n"
                "parser = argparse.ArgumentParser()\n"
                "parser.add_argument('--release-projection', action='store_true')\n"
                "parser.parse_args()\n"
                "Path('reports/result.json').write_text(json.dumps("
                "{'schema_version': 1}) + '\\n')\n",
                "process-exit-nonzero",
            ),
            (
                "ignored",
                "raise SystemExit(0)\n",
                "report-not-refreshed",
            ),
        )
        for label, body, expected_reason in cases:
            with self.subTest(case=label):
                temporary, root = self._root()
                self.addCleanup(temporary.cleanup)
                script = self._script(root, label, body)
                tracked = b'{"schema_version":0,"sentinel":true}\n'
                (root / "reports/result.json").write_bytes(tracked)
                (root / ".gitignore").write_text(
                    ".rd-skills/formal-release/\n", encoding="utf-8"
                )
                subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                subprocess.run(
                    ["git", "config", "user.email", "test@example.invalid"],
                    cwd=root,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test"],
                    cwd=root,
                    check=True,
                )
                subprocess.run(["git", "add", "."], cwd=root, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "fixture"],
                    cwd=root,
                    check=True,
                )
                producer = self._producer(
                    label,
                    script,
                    reports=["reports/result.json"],
                )
                staging = (
                    root
                    / EVALUATOR.FORMAL_EVIDENCE_ROOT
                    / ("a" * 40)
                    / "producer-reports"
                )
                results, _by_id, _post_tree = EVALUATOR._run_producers(
                    root,
                    [producer],
                    EVALUATOR.input_tree_digest(root),
                    release_projection=True,
                    report_path_overrides={
                        "reports/result.json": staging / "result.json"
                    },
                    reports_directory_override=staging,
                )
                result = results[0]
                self.assertEqual("fail", result["status"])
                self.assertIn(expected_reason, result["failure_reason_codes"])
                self.assertEqual(
                    tracked, (root / "reports/result.json").read_bytes()
                )
                status = subprocess.run(
                    [
                        "git",
                        "status",
                        "--porcelain=v1",
                        "--untracked-files=all",
                    ],
                    cwd=root,
                    check=True,
                    stdout=subprocess.PIPE,
                    text=True,
                ).stdout
                self.assertEqual("", status)

    def test_ordinary_authoring_preserves_default_reports_directory(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        writer = self._script(
            root,
            "ordinary-report",
            "import argparse, json\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--reports-dir', type=Path, default=Path('reports'))\n"
            "args = parser.parse_args()\n"
            "args.reports_dir.mkdir(parents=True, exist_ok=True)\n"
            "(args.reports_dir / 'result.json').write_text(json.dumps("
            "{'schema_version': 1, 'reports_dir': str(args.reports_dir)}) + '\\n')\n",
        )
        report = EVALUATOR.evaluate(
            root,
            self._contract(
                [
                    self._producer(
                        "ordinary-report",
                        writer,
                        reports=["reports/result.json"],
                    )
                ],
                [
                    {
                        "id": "ordinary-current",
                        "producer": "ordinary-report",
                        "predicates": [PROCESS_PASS, REPORT_SCHEMA],
                    }
                ],
            ),
        )
        self.assertEqual("pass", report["producers"][0]["status"])
        payload = json.loads((root / "reports/result.json").read_text())
        self.assertEqual("reports", payload["reports_dir"])
        self.assertFalse((root / EVALUATOR.FORMAL_EVIDENCE_ROOT).exists())

    def test_formal_core_writes_head_scoped_ephemeral_evidence_and_keeps_tracked_clean(
        self,
    ) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        self._script(
            root,
            "validate-professionalism-regression",
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "reports = Path('reports')\n"
            "if '--output-dir' in sys.argv:\n"
            "    reports = Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
            "reports.mkdir(parents=True, exist_ok=True)\n"
            "payload = {'schema_version': 1, 'formal': True, "
            "'captured_head': os.environ.get('CHANGEFORGE_FORMAL_HEAD_COMMIT')}\n"
            "(reports / 'professionalism-regression-report.json').write_text("
            "json.dumps(payload) + '\\n')\n"
            "if '--release-projection' in sys.argv:\n"
            "    (reports / 'professionalism-regression-report.md').write_text("
            "'# Formal professionalism\\n')\n",
        )
        producer = {
            "id": EVALUATOR.PROFESSIONALISM_PRODUCER_ID,
            "argv": list(EVALUATOR.PROFESSIONALISM_PRODUCER_ARGV),
            "depends_on": [],
            "reports": [EVALUATOR.PROFESSIONALISM_JSON_REPORT],
            "release_reports": [EVALUATOR.PROFESSIONALISM_MARKDOWN_REPORT],
            "authority_inputs": ["fixture-authority"],
            "timeout_seconds": EVALUATOR.PROFESSIONALISM_DECLARED_TIMEOUT_SECONDS,
        }
        authoring = {
            "id": "professionalism-process-current",
            "producer": EVALUATOR.PROFESSIONALISM_PRODUCER_ID,
            "predicates": [PROCESS_PASS],
        }
        formal = {
            "id": "professionalism-formal-current",
            "producer": EVALUATOR.PROFESSIONALISM_PRODUCER_ID,
            "predicates": [
                PROCESS_PASS,
                {
                    "source": EVALUATOR.PROFESSIONALISM_JSON_REPORT,
                    "pointer": "/schema_version",
                    "operator": "equals",
                    "expected": 1,
                },
                {
                    "source": EVALUATOR.PROFESSIONALISM_JSON_REPORT,
                    "pointer": "/formal",
                    "operator": "equals",
                    "expected": True,
                },
            ],
        }
        contract = self._contract(
            [producer],
            [authoring, formal],
            formal_outcomes=[formal["id"]],
        )
        self._write_contract(root, contract)
        tracked_professionalism = b'{"schema_version":4,"ordinary_authoring":true}\n'
        tracked_core = b'{"schema_version":4,"ordinary_authoring":true}\n'
        (root / EVALUATOR.JSON_REPORT).write_bytes(tracked_core)
        (root / EVALUATOR.PROFESSIONALISM_JSON_REPORT).write_bytes(
            tracked_professionalism
        )
        (root / ".gitignore").write_text(
            ".rd-skills/formal-release/\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=root, check=True
        )
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "fixture"], cwd=root, check=True
        )
        head = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()

        exit_code = EVALUATOR.main(
            ["--root", str(root), "--gate", "formal-release"]
        )

        evidence = root / EVALUATOR.FORMAL_EVIDENCE_ROOT / head / "reports"
        self.assertEqual(0, exit_code)
        self.assertEqual(
            head,
            json.loads(
                (evidence / "professionalism-regression-report.json").read_text()
            )["captured_head"],
        )
        core = json.loads(
            (evidence / "core-principles-outcomes.json").read_text()
        )
        self.assertEqual(head, core["formal_evidence_head_commit"])
        self.assertEqual([], EVALUATOR._saved_report_schema_errors(core))
        self.assertTrue((evidence / "professionalism-regression-report.md").is_file())
        self.assertTrue((evidence / "core-principles-outcomes.md").is_file())
        self.assertEqual(
            tracked_professionalism,
            (root / EVALUATOR.PROFESSIONALISM_JSON_REPORT).read_bytes(),
        )
        self.assertEqual(tracked_core, (root / EVALUATOR.JSON_REPORT).read_bytes())
        self.assertFalse((root / EVALUATOR.MARKDOWN_REPORT).exists())
        self.assertFalse((root / EVALUATOR.PROFESSIONALISM_MARKDOWN_REPORT).exists())
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
        self.assertEqual("", status)
        self.assertEqual(
            0,
            EVALUATOR.main(
                ["--root", str(root), "--gate", "formal-release"]
            ),
        )
        self.assertEqual(
            EVALUATOR.FORMAL_EVIDENCE_FILENAMES,
            {path.name for path in evidence.iterdir() if path.is_file()},
        )

    def test_formal_contract_drift_fails_only_in_head_scoped_evidence(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(root, "drifted", "raise SystemExit(0)\n")
        contract = self._contract(
            [self._producer("drifted", script)],
            [
                {
                    "id": "drifted-pass",
                    "producer": "drifted",
                    "predicates": [PROCESS_PASS],
                }
            ],
        )
        self._write_contract(root, contract)
        tracked_core = b'{"schema_version":4,"ordinary_authoring":true}\n'
        (root / EVALUATOR.JSON_REPORT).write_bytes(tracked_core)
        (root / ".gitignore").write_text(
            ".rd-skills/formal-release/\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=root, check=True
        )
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
        head = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()

        exit_code = EVALUATOR.main(
            ["--root", str(root), "--gate", "formal-release"]
        )

        evidence = root / EVALUATOR.FORMAL_EVIDENCE_ROOT / head / "reports"
        self.assertEqual(1, exit_code)
        self.assertEqual(tracked_core, (root / EVALUATOR.JSON_REPORT).read_bytes())
        self.assertFalse((root / EVALUATOR.MARKDOWN_REPORT).exists())
        formal_core = json.loads(
            (evidence / "core-principles-outcomes.json").read_text()
        )
        self.assertEqual(head, formal_core["formal_evidence_head_commit"])
        self.assertTrue(formal_core["contract_errors"])
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
        self.assertEqual("", status)

    def test_formal_atomic_writer_rejects_symlinked_ancestor(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        outside = root / "outside"
        outside.mkdir()
        (root / ".rd-skills").symlink_to(outside, target_is_directory=True)
        destination = (
            root
            / EVALUATOR.FORMAL_EVIDENCE_ROOT
            / ("a" * 40)
            / "reports"
            / "core-principles-outcomes.json"
        )

        with self.assertRaisesRegex(ValueError, "symlink|safe directory"):
            EVALUATOR._atomic_write(
                destination,
                "{}\n",
                trusted_root=root,
            )

        self.assertFalse((outside / "formal-release").exists())
        (root / ".rd-skills").unlink()
        destination.parent.mkdir(parents=True)
        outside_file = outside / "sentinel.json"
        outside_file.write_text("unchanged\n", encoding="utf-8")
        destination.symlink_to(outside_file)
        with self.assertRaisesRegex(ValueError, "regular file|safe directory"):
            EVALUATOR._atomic_write(
                destination,
                "changed\n",
                trusted_root=root,
            )
        self.assertEqual("unchanged\n", outside_file.read_text(encoding="utf-8"))

    def test_formal_scene_rejects_residue_before_execution(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        head = "a" * 40
        reports = root / EVALUATOR.FORMAL_EVIDENCE_ROOT / head / "reports"
        reports.mkdir(parents=True)
        (reports / ".core-principles-outcomes.json.stale.tmp").write_text(
            "stale\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "unexpected formal evidence"):
            EVALUATOR._prepare_formal_evidence_scene(root, head)

    def test_cli_success_preserves_summary_without_diagnostics(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(root, "pass", "raise SystemExit(0)\n")
        contract = self._contract(
            [self._producer("pass", script)],
            [{"id": "pass", "producer": "pass", "predicates": [PROCESS_PASS]}],
        )
        self._write_contract(root, contract)

        with mock.patch.object(sys, "stdout", io.StringIO()) as stdout, mock.patch.object(
            sys, "stderr", io.StringIO()
        ) as stderr:
            exit_code = EVALUATOR.main(
                ["--root", str(root), "--gate", "authoring"]
            )

        self.assertEqual(0, exit_code)
        self.assertEqual(
            "eval-core-principles: authoring_principles=pass; "
            "formal_principles=pass; selected_gate=authoring:pass; commands=1\n",
            stdout.getvalue(),
        )
        self.assertEqual("", stderr.getvalue())

    def test_cli_failure_emits_ordered_redacted_nonpass_producers(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        secret = "DO_NOT_PRINT_CHILD_OUTPUT_41d9"
        failing = self._script(
            root,
            "fail",
            "import sys\n"
            f"print({secret!r})\n"
            f"print({secret!r}, file=sys.stderr)\n"
            "raise SystemExit(7)\n",
        )
        dependent = self._script(root, "dependent", "raise SystemExit(0)\n")
        passing = self._script(root, "pass", "raise SystemExit(0)\n")
        contract = self._contract(
            [
                self._producer("fail", failing),
                self._producer("dependent", dependent, depends_on=["fail"]),
                self._producer("pass", passing),
            ],
            [
                {"id": "fail", "producer": "fail", "predicates": [PROCESS_PASS]},
                {
                    "id": "dependent",
                    "producer": "dependent",
                    "predicates": [PROCESS_PASS],
                },
                {"id": "pass", "producer": "pass", "predicates": [PROCESS_PASS]},
            ],
        )
        self._write_contract(root, contract)

        expected_diagnostics = (
            "eval-core-principles: producer_nonpass="
            '{"id":"fail","status":"fail","exit_code":7,"timed_out":false,'
            '"failure_reason_codes":["process-exit-nonzero"],"depends_on":[]}\n'
            "eval-core-principles: producer_nonpass="
            '{"id":"dependent","status":"not_run","exit_code":null,'
            '"timed_out":false,"failure_reason_codes":["dependency-not-pass"],'
            '"depends_on":["fail"]}\n'
        )
        for gate, selected_status in (("authoring", "fail"),):
            with self.subTest(gate=gate), mock.patch.object(
                sys, "stdout", io.StringIO()
            ) as stdout, mock.patch.object(sys, "stderr", io.StringIO()) as stderr:
                exit_code = EVALUATOR.main(
                    ["--root", str(root), "--gate", gate]
                )

            self.assertEqual(1, exit_code)
            self.assertEqual(
                "eval-core-principles: authoring_principles=fail; "
                "formal_principles=blocked; "
                f"selected_gate={gate}:{selected_status}; commands=2\n",
                stdout.getvalue(),
            )
            self.assertEqual(expected_diagnostics, stderr.getvalue())
            self.assertNotIn(secret, stdout.getvalue())
            self.assertNotIn(secret, stderr.getvalue())
            self.assertNotIn('"id":"pass"', stderr.getvalue())

    def test_cli_rejects_arbitrary_contract_option(self) -> None:
        with mock.patch.object(sys, "stderr"):
            with self.assertRaises(SystemExit) as raised:
                EVALUATOR._args(["--contract", "alternate.json"])
        self.assertEqual(2, raised.exception.code)

    def test_success_evidence_omits_same_run_and_scalar_hashes(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        script = self._script(
            root,
            "hash-free",
            "from pathlib import Path\n"
            "Path('reports/result.json').write_text('{\"schema_version\":1}\\n')\n",
        )
        outcome = {
            "id": "hash-free-pass",
            "producer": "hash-free",
            "predicates": [PROCESS_PASS, REPORT_SCHEMA],
        }
        report = EVALUATOR.evaluate(
            root,
            self._contract(
                [self._producer("hash-free", script, reports=["reports/result.json"])],
                [outcome],
            ),
        )

        producer = report["producers"][0]
        self.assertNotIn("stdout_sha256", producer)
        self.assertNotIn("stderr_sha256", producer)
        self.assertNotIn("sha256", producer["reports"][0])
        self.assertNotIn("value_sha256", report["authorities"][0])
        self.assertNotIn(
            "canonical_sha256",
            report["outcomes"][0]["predicates"][1]["actual_metadata"],
        )


if __name__ == "__main__":
    unittest.main()
