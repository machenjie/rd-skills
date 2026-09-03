from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval-agent-lightweight.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "eval_agent_lightweight_utility_tests",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL = _load_module()
FIXTURE = sys.modules["fixture_capsule_contract"]


def _materialize_runtime_dist(dist: Path) -> None:
    professional, layer3 = EVAL._skill_registries()
    runtime_root = dist / EVAL.RUNTIME_NAME
    compiled = {
        primary: list(entry.get("layer3_candidates", []))
        for primary, entry in sorted(professional.items())
    }
    manifest = {
        "profile": EVAL.RUNTIME_NAME,
        "compiled_layer3_format": EVAL.COMPILED_LAYER3_FORMAT,
        "professional_skills": sorted(professional),
        "top_level_skills": [
            "engineering-control-plane",
            *sorted(professional),
        ],
        "compiled_layer3_references": compiled,
    }
    for primary, owners in compiled.items():
        for owner in owners:
            entry = layer3[owner]
            for relative in EVAL.reference_paths(
                entry.get("reference_index"),
                f"{owner}.reference_index",
                owner=owner,
            ):
                source = ROOT / str(entry["path"]) / relative
                destination = (
                    runtime_root
                    / primary
                    / "references/layer3"
                    / owner
                    / relative
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / ".changeforge-build-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )


def setUpModule() -> None:
    runtime = tempfile.TemporaryDirectory(prefix="rd-skills-lightweight-runtime-")
    try:
        dist = Path(runtime.name)
        _materialize_runtime_dist(dist)
        dist_patcher = patch.object(EVAL, "DIST_SKILLS", dist)
        dist_patcher.start()
    except BaseException:
        runtime.cleanup()
        raise
    unittest.addModuleCleanup(runtime.cleanup)
    unittest.addModuleCleanup(dist_patcher.stop)


CANONICAL_LEDGER_FIELDS = (
    "Claim",
    "Owner",
    "Artifact",
    "Command",
    "Result",
    "Freshness",
    "Scope",
    "Proof Limit",
    "State",
)
RETIRED_LEDGER_FIELDS = (
    "Evidence ID",
    "Task ID",
    "Action",
    "Freshness Marker",
    "Evidence State",
    "Supersedes",
)
LEGACY_NEGATIVE_TAG = "legacy-negative"


class LightweightUtilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        document = EVAL._load_json(EVAL.FIXTURES)
        cls.document = document
        cls.release_cases = document["cases"]
        cls.scheduling_cases = document["scheduling_cases"]
        cls.utility_cases = document["utility_cases"]
        cls.evidence_continuation_cases = document["evidence_continuation_cases"]
        cls.adaptive_testing_cases = document["adaptive_testing_cases"]
        cls.review_discipline_cases = document["review_discipline_cases"]
        cls.task_focus_cases = document["task_focus_cases"]
        cls.orchestration_cases = document["orchestration_cases"]
        cls.completion_state_cases = document["completion_state_cases"]
        cls.external_read_cases = document["external_read_cases"]
        cls.evidence_localization_cases = document["evidence_localization_cases"]
        cls.professional, cls.layer3 = EVAL._skill_registries()

    def _errors(self, case: dict) -> list[str]:
        _metrics, errors = EVAL._metrics(
            case,
            self.professional,
            self.layer3,
            utility_case=True,
        )
        return errors

    def _trajectory_errors(self, case: dict) -> list[str]:
        _metrics, errors = EVAL._metrics(
            case,
            self.professional,
            self.layer3,
        )
        return errors

    @staticmethod
    def _canonical_hash(value: dict) -> str:
        return hashlib.sha256(
            json.dumps(
                {key: item for key, item in value.items() if key != "canonical_sha256"},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _rehash(cls, value: dict) -> None:
        value["canonical_sha256"] = cls._canonical_hash(value)

    @classmethod
    def _sync_request(cls, case: dict) -> None:
        request = case["request"]
        case["assignment"]["inputs"] = copy.deepcopy(request)
        request_sha256 = hashlib.sha256(
            json.dumps(
                request,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        for attempt in case["attempts"]:
            attempt["request_sha256"] = request_sha256

    @classmethod
    def _sync_host_evidence(cls, case: dict) -> None:
        for attempt in case["attempts"]:
            cls._rehash(attempt["host_evidence"])
        evidence = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]
        evidence["outcome"]["host_evidence"] = [
            copy.deepcopy(attempt["host_evidence"]) for attempt in case["attempts"]
        ]
        cls._rehash(evidence["outcome"])

    def _evidence_case(self, case_id: str) -> dict:
        return next(
            copy.deepcopy(case)
            for case in self.evidence_continuation_cases
            if case["id"] == case_id
        )

    def _assert_evidence_case_rejected(self, check_id: str, case: dict) -> None:
        with self.subTest(check_id=check_id):
            results, errors = EVAL._evidence_continuation_fixture_results([case])
            self.assertTrue(errors, (check_id, results))
            self.assertFalse(results[0]["matches_expected"], (check_id, results))

    def test_b01_b48_evidence_fixture_contract_is_canonical(self) -> None:
        results, errors = EVAL._evidence_continuation_fixture_results(
            copy.deepcopy(self.evidence_continuation_cases)
        )
        self.assertEqual([], errors)
        self.assertEqual(8, len(results))
        no_triggers = self.evidence_continuation_cases[:3]
        self.assertTrue(all(case["request"] is None for case in no_triggers))
        for case in self.evidence_continuation_cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    tuple(case["analysis_identity"]),
                    tuple(case["continuation_identity"]),
                )
                self.assertEqual(
                    {key: value for key, value in case["analysis_identity"].items() if key != "canonical_sha256"},
                    {key: value for key, value in case["continuation_identity"].items() if key != "canonical_sha256"},
                )
                self.assertEqual(
                    self._canonical_hash(case["analysis_identity"]),
                    case["analysis_identity"]["canonical_sha256"],
                )
                self.assertEqual(
                    self._canonical_hash(case["continuation_identity"]),
                    case["continuation_identity"]["canonical_sha256"],
                )
        for case in self.evidence_continuation_cases[3:]:
            with self.subTest(case=case["id"]):
                request = case["request"]
                self.assertEqual("evidence-observation-operation", request["operation"])
                self.assertEqual("tests/fixture-subject.txt", request["allowed_scope"])
                self.assertEqual(request, case["assignment"]["inputs"])
                self.assertEqual([request["allowed_scope"]], case["assignment"]["allowed_scope"]["paths"])
                artifact = case["utility_return"]["artifact_or_check_outcomes"]
                self.assertEqual("fresh after this immutable Evidence Request", artifact["freshness"])
                self.assertEqual(request["allowed_scope"], artifact["scope"])
                self.assertEqual(
                    "Deterministic fixture evidence does not prove live Host or provider behavior.",
                    artifact["proof_limit"],
                )
                self.assertEqual(
                    ["live Host and provider behavior"],
                    case["utility_return"]["unverified_scope"],
                )
                self.assertEqual(
                    ["bounded observation may leave the material claim unproved"],
                    case["utility_return"]["residual_risk"],
                )
                self.assertEqual(
                    {
                        "professional_skill_load": 0,
                        "layer3_load": 0,
                        "diagnose": 0,
                        "edit": 0,
                        "repair": 0,
                        "reroute": 0,
                        "generic_execute": 0,
                    },
                    results[[row["id"] for row in results].index(case["id"])]["forbidden_operation_counts"],
                )

    def test_b01_b45_evidence_fixture_mutations_are_rejected(self) -> None:
        self.assertEqual(
            [],
            EVAL._evidence_continuation_fixture_results(
                copy.deepcopy(self.evidence_continuation_cases)
            )[1],
        )
        self.assertTrue(
            all("continuation_identity" in case for case in self.evidence_continuation_cases),
            "P1: evidence cases require an independently hashed continuation identity",
        )

        case = self._evidence_case("evidence-static-sufficient")
        case["request"] = copy.deepcopy(self._evidence_case("evidence-completed")["request"])
        self._assert_evidence_case_rejected("B01", case)

        case = self._evidence_case("evidence-completed")
        case["request"] = None
        self._assert_evidence_case_rejected("B02", case)

        for check_id, operation in (
            ("B03", "python3 arbitrary.py"),
            ("B04", "evidence-observation-operation; repair"),
        ):
            case = self._evidence_case("evidence-completed")
            case["request"]["operation"] = operation
            self._sync_request(case)
            self._assert_evidence_case_rejected(check_id, case)

        case = self._evidence_case("evidence-completed")
        case["request"]["allowed_scope"] = "elsewhere/private.txt"
        self._sync_request(case)
        case["utility_return"]["artifact_or_check_outcomes"]["scope"] = "elsewhere/private.txt"
        self._assert_evidence_case_rejected("B05", case)

        case = self._evidence_case("evidence-completed")
        case["assignment"]["allowed_scope"]["paths"] = ["."]
        self._assert_evidence_case_rejected("B06", case)

        case = self._evidence_case("evidence-completed")
        case["analysis_identity"]["professional_skill"] = "quality-test-gate"
        self._rehash(case["analysis_identity"])
        self._assert_evidence_case_rejected("B07", case)

        case = self._evidence_case("evidence-completed")
        case["analysis_identity"]["layer3_skills"] = ["test-strategy"]
        self._rehash(case["analysis_identity"])
        self._assert_evidence_case_rejected("B08", case)

        case = self._evidence_case("evidence-completed")
        case["continuation_identity"]["effective_level"] = "L3"
        self._rehash(case["continuation_identity"])
        self._assert_evidence_case_rejected("B09", case)

        case = self._evidence_case("evidence-completed")
        case["request"]["extra"] = "forbidden"
        self._sync_request(case)
        self._assert_evidence_case_rejected("B10", case)

        case = self._evidence_case("evidence-completed")
        analysis_task_id = case["analysis_identity"]["task_id"]
        case["assignment"]["task_id"] = analysis_task_id
        case["utility_return"]["task_id"] = analysis_task_id
        for attempt in case["attempts"]:
            attempt["utility_task_id"] = analysis_task_id
        self._assert_evidence_case_rejected("B11", case)

        case = self._evidence_case("evidence-permission-retry")
        case["attempts"][1]["utility_task_id"] = "replacement-utility-task"
        self._assert_evidence_case_rejected("B12", case)

        for check_id, fields in (
            ("B13", {"professional_skill": "quality-test-gate", "professional_references": []}),
            ("B14", {"layer3_skills": [], "layer3_references": []}),
        ):
            case = self._evidence_case("evidence-completed")
            case["assignment"].update(fields)
            self._assert_evidence_case_rejected(check_id, case)

        case = self._evidence_case("evidence-completed")
        case["assignment"]["no_edit_enforcement"] = "self-declared"
        case["utility_return"]["no_edit_enforcement"] = "self-declared"
        self._assert_evidence_case_rejected("B15", case)

        case = self._evidence_case("evidence-permission-retry")
        third = copy.deepcopy(case["attempts"][1])
        third["ordinal"] = 3
        case["attempts"].append(third)
        self._sync_host_evidence(case)
        self._assert_evidence_case_rejected("B16", case)

        case = self._evidence_case("evidence-permission-retry")
        case["attempts"][0]["status"] = "partial"
        raw = case["attempts"][0]["host_evidence"]["raw_fixture"]
        raw["status"] = "partial"
        raw["observation_produced"] = True
        self._sync_host_evidence(case)
        self._assert_evidence_case_rejected("B17", case)

        case = self._evidence_case("evidence-permission-retry")
        case["attempts"][0]["status"] = "completed"
        case["attempts"][0]["host_evidence"]["raw_fixture"]["status"] = "completed"
        self._sync_host_evidence(case)
        self._assert_evidence_case_rejected("B18", case)

        for variant, commands in (
            ("missing", ["evidence-observation-operation", "evidence-workspace-postflight"]),
            ("extra", ["evidence-workspace-preflight", "evidence-observation-operation", "validation-check", "evidence-workspace-postflight"]),
            ("reordered", ["evidence-observation-operation", "evidence-workspace-preflight", "evidence-workspace-postflight"]),
        ):
            case = self._evidence_case("evidence-completed")
            case["attempts"][0]["commands"] = commands
            case["utility_return"]["commands_run"] = list(commands)
            self._assert_evidence_case_rejected(f"B19-{variant}", case)

        case = self._evidence_case("evidence-permission-retry")
        for attempt in case["attempts"]:
            attempt["host_evidence"]["raw_fixture"]["observed_requirement"] = "whole workspace access"
        authority = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["authority"]
        authority["allowed_scope"] = "."
        authority["observed_requirement"] = "whole workspace access"
        self._rehash(authority)
        self._sync_host_evidence(case)
        self._assert_evidence_case_rejected("B20", case)

        case = self._evidence_case("evidence-completed")
        authority = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["authority"]
        authority["operation"] = "validation-check"
        self._rehash(authority)
        self._assert_evidence_case_rejected("B21", case)

        case = self._evidence_case("evidence-completed")
        authority = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["authority"]
        authority["kind"] = "host-support"
        authority["disposition"] = "unavailable"
        self._rehash(authority)
        self._assert_evidence_case_rejected("B22", case)

        case = self._evidence_case("evidence-permission-retry")
        authority = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["authority"]
        authority["observed_requirement"] = "different exact authority"
        self._rehash(authority)
        self._assert_evidence_case_rejected("B23", case)

        case = self._evidence_case("evidence-completed")
        decision = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["decision"]
        decision["evidence"] = "Root cause found; edit, repair, and reroute"
        self._rehash(decision)
        self._assert_evidence_case_rejected("B24", case)

        case = self._evidence_case("evidence-completed")
        decision = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["decision"]
        decision["extra"] = True
        self._rehash(decision)
        self._assert_evidence_case_rejected("B25", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["artifact_or_check_outcomes"]["freshness"] = "fresh/old"
        self._assert_evidence_case_rejected("B26", case)

        for variant in ("empty", "deleted"):
            case = self._evidence_case("evidence-completed")
            artifact = case["utility_return"]["artifact_or_check_outcomes"]
            if variant == "empty":
                artifact["proof_limit"] = ""
            else:
                del artifact["proof_limit"]
            self._assert_evidence_case_rejected(f"B27-{variant}", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["artifact_or_check_outcomes"]["proof_limit"] = "No known limitations."
        self._assert_evidence_case_rejected("B28", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["artifact_or_check_outcomes"]["scope"] = "elsewhere/private.txt"
        self._assert_evidence_case_rejected("B29", case)

        case = self._evidence_case("evidence-completed")
        case["assignment"]["evidence_ledger"][0]["Scope"] = "elsewhere/private.txt"
        self._assert_evidence_case_rejected("B30", case)

        for index in range(3):
            case = self._evidence_case("evidence-completed")
            case["utility_return"]["evidence_ledger"][index]["Scope"] = "elsewhere/private.txt"
            self._assert_evidence_case_rejected(f"B31{'abc'[index]}", case)

        for check_id, ledger_name, index in (
            ("B32a", "assignment", 0),
            ("B32b", "utility_return", 0),
            ("B32c", "utility_return", 1),
            ("B32d", "utility_return", 2),
        ):
            case = self._evidence_case("evidence-completed")
            case[ledger_name]["evidence_ledger"][index]["Proof Limit"] = "None"
            self._assert_evidence_case_rejected(check_id, case)

        for variant, ledger_name, index, value in (
            ("assignment", "assignment", 0, 1),
            ("return-low", "utility_return", 1, 0),
            ("return-high", "utility_return", 2, 2),
        ):
            case = self._evidence_case("evidence-completed")
            case[ledger_name]["evidence_ledger"][index]["Freshness"] = value
            self._assert_evidence_case_rejected(f"B33-{variant}", case)

        for variant in ("deleted", "changed"):
            case = self._evidence_case("evidence-completed")
            ledger = case["utility_return"]["evidence_ledger"]
            if variant == "deleted":
                ledger.pop(0)
            else:
                ledger[0]["Result"] = "different baseline"
            self._assert_evidence_case_rejected(f"B34-{variant}", case)

        for variant in ("removed", "reordered", "different"):
            case = self._evidence_case("evidence-permission-retry")
            outcome = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["outcome"]
            if variant == "removed":
                outcome["host_evidence"].pop()
            elif variant == "reordered":
                outcome["host_evidence"].reverse()
            else:
                outcome["host_evidence"][0]["raw_fixture"]["raw_output"] = "different"
                self._rehash(outcome["host_evidence"][0])
            self._rehash(outcome)
            self._assert_evidence_case_rejected(f"B35-{variant}", case)

        case = self._evidence_case("evidence-partial")
        case["continuation"]["proof_limit"] = "None"
        self._assert_evidence_case_rejected("B36", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["unverified_scope"] = []
        self._assert_evidence_case_rejected("B37", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["residual_risk"] = []
        self._assert_evidence_case_rejected("B38", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["scope"] = "tests/fixture-subject.txt"
        self._assert_evidence_case_rejected("B39", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["artifact_or_check_outcomes"]["extra"] = True
        self._assert_evidence_case_rejected("B40", case)

        for check_id, status in (("B41", "changed"), ("B42", "unavailable")):
            case = self._evidence_case("evidence-completed")
            case["utility_return"]["workspace_diff_check"]["status"] = status
            self._assert_evidence_case_rejected(check_id, case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["workspace_diff_check"]["after"] = ["tracked:changed", "staged:none", "untracked:none"]
        self._assert_evidence_case_rejected("B43", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["workspace_diff_check"]["before"] = ["tracked:changed", "staged:none", "untracked:none"]
        case["utility_return"]["workspace_diff_check"]["after"] = list(case["utility_return"]["workspace_diff_check"]["before"])
        self._assert_evidence_case_rejected("B44", case)

        for variant, change_set in (
            ("missing", ["tracked:none", "staged:none"]),
            ("reordered", ["staged:none", "tracked:none", "untracked:none"]),
        ):
            case = self._evidence_case("evidence-completed")
            case["assignment"]["workspace_baseline"]["change_set"] = change_set
            case["utility_return"]["workspace_diff_check"]["before"] = list(change_set)
            case["utility_return"]["workspace_diff_check"]["after"] = list(change_set)
            self._assert_evidence_case_rejected(f"B45-{variant}", case)

    def test_b46_b48_forbidden_counts_route_source_and_raw_boundary(self) -> None:
        if not all(
            "continuation_identity" in case
            for case in self.evidence_continuation_cases
        ):
            self.fail(
                "P1: evidence cases require an independently hashed continuation identity"
            )
        case = self._evidence_case("evidence-completed")
        case["assignment"]["professional_skill"] = "quality-test-gate"
        results, errors = EVAL._evidence_continuation_fixture_results([case])
        with self.subTest(check_id="B46"):
            self.assertTrue(errors)
            self.assertIn("forbidden_operation_counts", results[0])
            self.assertGreater(
                sum(results[0]["forbidden_operation_counts"].values()),
                0,
            )
            self.assertEqual(
                results[0]["forbidden_operation_counts"],
                EVAL._sum_evidence_forbidden_operation_counts(results),
            )
            literal_zero = {
                key: 0 for key in results[0]["forbidden_operation_counts"]
            }
            self.assertTrue(
                EVAL._evidence_forbidden_operation_count_errors(
                    results,
                    literal_zero,
                )
            )

        case = self._evidence_case("evidence-completed")
        case["continuation_identity"]["effective_level"] = "L3"
        self._rehash(case["continuation_identity"])
        results, errors = EVAL._evidence_continuation_fixture_results([case])
        with self.subTest(check_id="B47"):
            self.assertTrue(errors)
            self.assertFalse(results[0]["route_frozen"])
            self.assertTrue(case["expected"]["route_frozen"])

        case = self._evidence_case("evidence-completed")
        case["attempts"][0]["host_evidence"]["raw_fixture"]["raw_output"] = "fixture repair value confirmed"
        self._sync_host_evidence(case)
        results, errors = EVAL._evidence_continuation_fixture_results([case])
        with self.subTest(check_id="B48"):
            self.assertEqual([], errors)
            self.assertEqual(
                0,
                sum(results[0]["forbidden_operation_counts"].values()),
            )

    def test_latest_evidence_renderer_rejects_invalid_semantic_fields(self) -> None:
        base = self._evidence_case("evidence-completed")["assignment"]

        def invalid_goal(value: dict) -> None:
            value["goal"] = "Diagnose and repair the repository after observing evidence."

        def invalid_expected(value: dict) -> None:
            value["expected_evidence"] = ["raw Host evidence"]

        def invalid_stops(value: dict) -> None:
            value["stop_conditions"] = ["continue after partial output"]

        def one_token_freshness(value: dict) -> None:
            value["inputs"]["freshness_requirement"] = "fresh"

        controls = (
            ("R01-invalid-goal", invalid_goal),
            ("R02-invalid-expected-evidence", invalid_expected),
            ("R03-invalid-stop-conditions", invalid_stops),
            ("R04-one-token-freshness", one_token_freshness),
        )
        for control_id, mutate in controls:
            with self.subTest(control_id=control_id):
                assignment = copy.deepcopy(base)
                mutate(assignment)
                step = {
                    "mode": "evidence-observation/no-edit",
                    "profile": "task-agent",
                    "utility_capsule": assignment,
                }
                with self.assertRaises(FIXTURE.FixtureCapsuleError):
                    FIXTURE._render_utility(step)

    def test_latest_evidence_route_and_outcome_mutations_fail_closed(self) -> None:
        case = self._evidence_case("evidence-completed")
        case["trigger"] = "unknown-evidence-trigger"
        self._assert_evidence_case_rejected("R05-unknown-trigger-dispatch", case)

        case = self._evidence_case("evidence-completed")
        case["trigger"] = "generic-environment-unknown"
        self._assert_evidence_case_rejected("R06-environment-trigger-dispatch", case)

        route_mutations = (
            ("R07-professional", "professional_skill", "backend-change-builder"),
            ("R08-level", "effective_level", "L3"),
            ("R09-layer3", "layer3_skills", ["test-strategy"]),
            (
                "R10-four-layer3",
                "layer3_skills",
                [
                    "test-strategy",
                    "regression-testing",
                    "targeted-validation-selection",
                    "contract-testing",
                ],
            ),
        )
        for control_id, field, value in route_mutations:
            case = self._evidence_case("evidence-completed")
            for endpoint in ("analysis_identity", "continuation_identity"):
                case[endpoint][field] = copy.deepcopy(value)
                self._rehash(case[endpoint])
            with self.subTest(check_id=control_id):
                results, errors = EVAL._evidence_continuation_fixture_results([case])
                self.assertTrue(errors, (control_id, results))
                self.assertFalse(results[0]["matches_expected"], (control_id, results))
                self.assertFalse(results[0]["route_frozen"], (control_id, results))

        case = self._evidence_case("evidence-completed")
        replacement_task_id = "analysis-evidence-replaced"
        for endpoint in ("analysis_identity", "continuation_identity"):
            case[endpoint]["task_id"] = replacement_task_id
            self._rehash(case[endpoint])
        case["request"]["analysis_task_id"] = replacement_task_id
        self._sync_request(case)
        case["continuation"]["analysis_task_id"] = replacement_task_id
        self._assert_evidence_case_rejected("R11-analysis-task-id", case)

        observation_controls = (
            ("R12-completed-false", "evidence-completed", False),
            ("R13-partial-false", "evidence-partial", False),
            ("R14-unsupported-true", "evidence-host-unsupported", True),
            ("R15-refusal-true", "evidence-authority-refused", True),
        )
        for control_id, case_id, observation_produced in observation_controls:
            case = self._evidence_case(case_id)
            if case_id == "evidence-authority-refused":
                host_evidence = case["utility_return"]["artifact_or_check_outcomes"][
                    "evidence"
                ]["outcome"]["host_evidence"][0]
                host_evidence["raw_fixture"][
                    "observation_produced"
                ] = observation_produced
                self._rehash(host_evidence)
                self._rehash(
                    case["utility_return"]["artifact_or_check_outcomes"][
                        "evidence"
                    ]["outcome"]
                )
            else:
                case["attempts"][-1]["host_evidence"]["raw_fixture"][
                    "observation_produced"
                ] = observation_produced
            case["expected"]["observation_count"] = int(observation_produced)
            if case_id != "evidence-authority-refused":
                self._sync_host_evidence(case)
            self._assert_evidence_case_rejected(control_id, case)

        refusal = self._evidence_case("evidence-authority-refused")
        with self.subTest(control_id="R16-refusal-zero-attempts"):
            self.assertEqual(0, len(refusal["attempts"]))

    def test_latest_evidence_request_level_commands_and_results_are_derived(self) -> None:
        pre = "evidence-workspace-preflight"
        operation = "evidence-observation-operation"
        post = "evidence-workspace-postflight"
        retry = self._evidence_case("evidence-permission-retry")

        with self.subTest(control_id="R17-request-level-command-layout"):
            self.assertEqual(
                [[operation], [operation]],
                [attempt["commands"] for attempt in retry["attempts"]],
            )
            self.assertEqual(
                [pre, operation, operation, post],
                retry["utility_return"]["commands_run"],
            )

        for control_id, commands in (
            ("R18-retry-missing-operation", [pre, operation, post]),
            ("R19-retry-extra-preflight", [pre, pre, operation, operation, post]),
            ("R20-retry-extra-postflight", [pre, operation, operation, post, post]),
        ):
            case = copy.deepcopy(retry)
            case["utility_return"]["commands_run"] = commands
            self._assert_evidence_case_rejected(control_id, case)

        case = copy.deepcopy(retry)
        case["attempts"][0]["commands"] = ["validation-check"]
        case["utility_return"]["commands_run"] = [
            pre,
            "validation-check",
            operation,
            post,
        ]
        self._assert_evidence_case_rejected("R21-attempt-operation-drift", case)

        case = self._evidence_case("evidence-completed")
        case["utility_return"]["commands_run"] = [pre, operation, operation, post]
        self._assert_evidence_case_rejected("R22-commands-run-formula", case)

        case = self._evidence_case("evidence-completed")
        del case["utility_return"]["evidence_ledger"][2]["Command"]
        self._assert_evidence_case_rejected("R23-ledger-command-missing", case)

        refusal = self._evidence_case("evidence-authority-refused")
        with self.subTest(control_id="R24-refusal-ledger-has-no-operation"):
            self.assertNotIn(
                operation,
                [row["Command"] for row in refusal["utility_return"]["evidence_ledger"]],
            )

        case = self._evidence_case("evidence-completed")
        case["expected"]["host_attempt_count"] = 2
        results, errors = EVAL._evidence_continuation_fixture_results([case])
        with self.subTest(control_id="R25-expected-cannot-author-metrics"):
            self.assertTrue(errors)
            self.assertEqual(1, results[0]["host_attempt_count"])

        case = self._evidence_case("evidence-completed")
        decision = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["decision"]
        decision["evidence"] = "repair"
        self._rehash(decision)
        results, errors = EVAL._evidence_continuation_fixture_results([case])
        with self.subTest(control_id="R26-forbidden-event-cannot-use-expected-zero"):
            self.assertTrue(errors)
            self.assertEqual(1, results[0]["forbidden_operation_counts"]["repair"])

        case = self._evidence_case("evidence-completed")
        decision = case["utility_return"]["artifact_or_check_outcomes"]["evidence"]["decision"]
        decision["evidence"] = "observation accepted for a replacement Analysis continuation"
        self._rehash(decision)
        self._assert_evidence_case_rejected("R27-rehashed-decision-enum", case)

        case = self._evidence_case("evidence-completed")
        case["attempts"][0]["host_evidence"]["raw_fixture"]["raw_output"] = (
            "fixture repair value confirmed"
        )
        self._sync_host_evidence(case)
        with self.subTest(control_id="R-positive-raw-repair-boundary"):
            results, errors = EVAL._evidence_continuation_fixture_results([case])
            self.assertEqual([], errors)
            self.assertEqual(0, sum(results[0]["forbidden_operation_counts"].values()))

    def test_route_frozen_evidence_continuations_are_closed_and_terminal(self) -> None:
        results, errors = EVAL._evidence_continuation_fixture_results(
            copy.deepcopy(self.evidence_continuation_cases)
        )
        self.assertEqual([], errors)
        self.assertEqual(8, len(results))
        by_id = {row["id"]: row for row in results}
        self.assertEqual(
            {
                "evidence-static-sufficient": (False, "not-dispatched"),
                "evidence-environment-unknown": (False, "not-dispatched"),
                "evidence-runtime-asset-failure": (False, "not-dispatched"),
                "evidence-completed": (True, "completed"),
                "evidence-permission-retry": (True, "completed"),
                "evidence-partial": (True, "partial"),
                "evidence-host-unsupported": (True, "blocked"),
                "evidence-authority-refused": (True, "blocked"),
            },
            {
                case_id: (row["utility_dispatched"], row["terminal_status"])
                for case_id, row in by_id.items()
            },
        )
        self.assertTrue(all(row["route_frozen"] for row in results))
        self.assertTrue(all(row["utility_return_count"] <= 1 for row in results))
        self.assertTrue(all(row["observation_count"] <= 1 for row in results))
        self.assertTrue(all(row["host_attempt_count"] <= 2 for row in results))

    def test_route_frozen_evidence_continuation_rejects_identity_and_hash_forgery(self) -> None:
        original = next(
            copy.deepcopy(case)
            for case in self.evidence_continuation_cases
            if case["id"] == "evidence-completed"
        )
        canonical_results, canonical_errors = (
            EVAL._evidence_continuation_fixture_results([original])
        )
        self.assertEqual([], canonical_errors)
        self.assertTrue(canonical_results[0]["matches_expected"])
        self.assertTrue(canonical_results[0]["route_frozen"])

        identity_mutations = []

        case = copy.deepcopy(original)
        case["analysis_identity"]["canonical_sha256"] = "0" * 64
        identity_mutations.append(("single-endpoint-hash", case))

        case = copy.deepcopy(original)
        case["analysis_identity"]["canonical_sha256"] = "0" * 64
        case["continuation_identity"]["canonical_sha256"] = "0" * 64
        identity_mutations.append(("both-endpoint-hash", case))

        case = copy.deepcopy(original)
        case["analysis_identity"]["extra"] = "forbidden"
        identity_mutations.append(("extra-field", case))

        case = copy.deepcopy(original)
        case["analysis_identity"] = {
            key: case["analysis_identity"][key]
            for key in reversed(tuple(case["analysis_identity"]))
        }
        identity_mutations.append(("reordered-fields", case))

        for mutation_id, mutated in identity_mutations:
            with self.subTest(mutation=mutation_id):
                results, errors = EVAL._evidence_continuation_fixture_results(
                    [mutated]
                )
                self.assertTrue(errors)
                self.assertFalse(results[0]["matches_expected"])
                self.assertFalse(results[0]["route_frozen"])

        mutations = []

        case = copy.deepcopy(original)
        case["assignment"]["inputs"]["analysis_task_id"] = case["assignment"][
            "task_id"
        ]
        mutations.append(case)

        case = copy.deepcopy(original)
        case["assignment"]["task_id"] = case["analysis_identity"]["task_id"]
        case["utility_return"]["task_id"] = case["assignment"]["task_id"]
        mutations.append(case)

        case = copy.deepcopy(original)
        case["utility_return"]["artifact_or_check_outcomes"]["extra"] = True
        mutations.append(case)

        case = copy.deepcopy(original)
        case["utility_return"]["artifact_or_check_outcomes"]["evidence"][
            "decision"
        ]["canonical_sha256"] = "f" * 64
        mutations.append(case)

        for mutated in mutations:
            with self.subTest(mutation=mutated):
                _results, errors = EVAL._evidence_continuation_fixture_results(
                    [mutated]
                )
                self.assertTrue(errors)

    def test_evidence_mode_attempts_enforce_pre_operation_post_and_retry_boundary(self) -> None:
        original = next(
            copy.deepcopy(case)
            for case in self.evidence_continuation_cases
            if case["id"] == "evidence-permission-retry"
        )
        self.assertEqual(
            [], EVAL._evidence_continuation_fixture_results([original])[1]
        )
        variants = []
        case = copy.deepcopy(original)
        case["attempts"][0]["commands"].pop()
        variants.append(case)
        case = copy.deepcopy(original)
        case["attempts"][1]["utility_task_id"] = "replacement-utility-task"
        variants.append(case)
        case = copy.deepcopy(original)
        case["attempts"].append(copy.deepcopy(case["attempts"][1]))
        variants.append(case)
        for mutated in variants:
            with self.subTest(mutation=mutated):
                _results, errors = EVAL._evidence_continuation_fixture_results(
                    [mutated]
                )
                self.assertTrue(errors)

    def test_copilot_evidence_trace_is_deterministic_fixture_evidence_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rd-skills-evidence-trace-") as raw:
            self.assertEqual(0, EVAL.main(["--reports-dir", raw]))
            report = json.loads(
                (Path(raw) / "hookless-control-plane-eval.json").read_text(
                    encoding="utf-8"
                )
            )
        trace = report["copilot_evidence_trace"]
        summary = report["integration_evidence_summary"]
        self.assertEqual("copilot", trace["host"])
        self.assertFalse(trace["live_host"])
        self.assertEqual(0, sum(trace["forbidden_operation_counts"].values()))
        self.assertEqual(trace["canonical_sha256"], summary["copilot_trace_sha256"])
        self.assertEqual(2, summary["utility_fixture_count"])
        self.assertEqual(8, summary["evidence_continuation_fixture_count"])

    def _trajectory_metrics(self, case: dict) -> tuple[dict, list[str]]:
        return EVAL._metrics(
            case,
            self.professional,
            self.layer3,
        )

    @staticmethod
    def _implementation_errors(case: dict) -> list[str]:
        return EVAL._implementation_discipline_errors(
            case["id"],
            case["steps"],
            case.get("implementation_oracle"),
        )

    @staticmethod
    def _rebind_authority_digest(case: dict) -> None:
        authority = case["implementation_oracle"]
        authority["canonical_sha256"] = EVAL._implementation_oracle_digest(
            authority
        )

    def _release_case(self, case_id: str) -> dict:
        return copy.deepcopy(
            next(item for item in self.release_cases if item["id"] == case_id)
        )

    def _review_convergence_case(self) -> dict:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "dedup-scoped-repair-subsumes-final"
            )
        )
        case["id"] = "review-convergence-complete-pass"
        case.pop("retained_semantics", None)
        return case

    @staticmethod
    def _semantic_canonical_finding(
        finding_id: str,
        *,
        task_id: str = "C",
        review_round_id: str = "R-C-1",
        scope: str = "src/retry/a.py",
        defect: str = "retry may publish twice",
        invariant: str = "publish is at-most-once",
        mechanism: str = "retry repeats publish after uncertain completion",
        fix_path: str = "guard publish with the existing idempotency key",
        category: str = "correctness-or-invariant",
    ) -> dict:
        return {
            "canonical_finding_id": finding_id,
            "source_finding_ids": [finding_id],
            "task_id": task_id,
            "review_round_id": review_round_id,
            "finding_relation": "current-task",
            "protected_decision_boundary": "accepted-retry-contract",
            "categories": [category],
            "descriptions": [defect],
            "defect": defect,
            "violated_invariant": invariant,
            "failure_mechanism": mechanism,
            "fix_path": fix_path,
            "source_reviewer_evidence": [
                {
                    "reviewer_result_id": f"review-{review_round_id}",
                    "evidence": f"current source evidence at {scope}",
                }
            ],
            "affected_scope": [scope],
            "acceptance_or_risk_impacts": [invariant],
            "required_validation": ["retry-publish-negative-control"],
            "required_covering_rereview": {
                "covered_task_ids": [task_id],
                "same_or_stronger": True,
            },
            "freshness": [f"current-{review_round_id}"],
            "proof_limits": [f"bounded to {scope}"],
            "repair_required": True,
        }

    @classmethod
    def _semantic_convergence_evidence(
        cls,
        history: list[list[dict]],
        **overrides: object,
    ) -> dict:
        packet = {
            "task_id": "C",
            "original_task_scope": [
                scope
                for findings in history
                for finding in findings
                for scope in finding["affected_scope"]
            ],
            "protected_decision_boundary": "accepted-retry-contract",
            "canonical_finding_history": [
                {
                    "review_round_id": findings[0]["review_round_id"],
                    "canonical_findings": findings,
                    "current_source_evidence": [
                        f"reviewed current source for {findings[0]['review_round_id']}"
                    ],
                }
                for findings in history
            ],
            "inherited_resolution_evidence": [],
            "independent_new_defect_evidence": [],
            "finite_sibling_scope": None,
            "rebroken_verified_invariant_evidence": [],
            "explicit_failure_set_cycle_evidence": [],
        }
        packet.update(overrides)
        return packet

    @staticmethod
    def _complete_initial_analysis_event() -> dict:
        return {
            "actor": "analysis-agent",
            "action": "first_executable_slice",
            "analysis_kind": "initial",
            "brief_id": "brief-single-module-feature-1",
            "brief_status": "accepted",
            "target_authority": {
                "desired_behavior": "Implement the accepted module-a service behavior.",
                "observable_acceptance": [
                    "The module-a service preserves its owner and existing consumers.",
                    "The module-test command passes after the material edit.",
                ],
                "observed_behavior": "The requested module-a behavior is absent.",
                "observed_behavior_role": "failure-evidence-only",
            },
            "acceptance": [
                "Preserve existing consumers and satisfy the Engineering Brief."
            ],
            "owner_placement_invariant": {
                "owner": "module-a/service.py",
                "placement": "existing module-a service owner",
                "invariant": "existing module-a consumers remain compatible",
            },
            "verification": ["module-test"],
            "downstream_task": {
                "task_id": "task-single-module-feature-1",
                "professional_skill": "backend-change-builder",
                "layer3_skills": [],
            },
            "review_projection": {
                "profile": "review-agent",
                "professional_skill": "architecture-impact-reviewer",
                "layer3_skills": [],
            },
        }

    @classmethod
    def _post_acceptance_delta_event(cls) -> dict:
        initial = cls._complete_initial_analysis_event()
        return {
            "actor": "analysis-agent",
            "action": "brief",
            "analysis_kind": "delta",
            "accepted_brief_id": initial["brief_id"],
            "protected_decision_invalidated": True,
            "invalidated_decisions": ["Acceptance-or-Non-goals"],
            "reroute_trigger": "none",
            "downstream_task": copy.deepcopy(initial["downstream_task"]),
            "review_projection": copy.deepcopy(initial["review_projection"]),
        }

    def test_required_behavior_coverage_manifest_is_exact_and_machine_checked(
        self,
    ) -> None:
        results, errors = EVAL._required_behavior_coverage_results(
            copy.deepcopy(self.document),
            self.professional,
            self.layer3,
        )
        self.assertEqual([], errors)
        self.assertEqual(17, len(results))
        grouped = {
            group: [item for item in results if item["group"] == group]
            for group in EVAL.REQUIRED_BEHAVIOR_GROUPS
        }
        self.assertEqual(
            {
                "ai-reading-ownership": 5,
                "adaptive-testing": 6,
                "engineering-closure": 6,
            },
            {group: len(items) for group, items in grouped.items()},
        )
        self.assertTrue(
            all(
                item["status"] == "covered"
                and item["positive_valid"]
                and item["full_path_valid"]
                and item["mutation_applied"]
                and item["bypass_rejected"]
                for item in results
            )
        )
        self.assertEqual(
            EVAL.REQUIRED_BEHAVIOR_DIMENSIONS,
            {
                dimension
                for group in self.document["required_behavior_coverage"]["groups"]
                for entry in group["entries"]
                for dimension in entry["dimensions"]
            },
        )

    def test_evidence_localization_quality_gate_and_cost_observation_are_separate(
        self,
    ) -> None:
        results, errors = EVAL._evidence_localization_fixture_results(
            copy.deepcopy(self.document["evidence_localization_cases"])
        )
        self.assertEqual([], errors)
        self.assertEqual(38, len(results))
        required_cost_fields = {
            "search_count",
            "exact_read_count",
            "broad_or_full_file_read_count",
            "repeated_read_count",
            "search_result_volume",
            "truncated_search_count",
            "evidence_byte_proxy",
            "time_to_owner_proof_step",
            "time_to_first_edit_step",
        }
        for result in results:
            with self.subTest(case=result["id"]):
                self.assertEqual(
                    required_cost_fields, set(result["cost_observation"])
                )
                self.assertIn("passed", result["quality_gate"])
                self.assertIn("errors", result["quality_gate"])
                self.assertEqual(
                    result["expected_valid"], result["quality_gate"]["passed"]
                )
                self.assertTrue(result["matches_expected"])

        cheap_invalid = next(
            item for item in results if item["id"] == "localization-cost-cannot-hide-quality"
        )
        self.assertEqual(0, cheap_invalid["cost_observation"]["search_count"])
        self.assertFalse(cheap_invalid["quality_gate"]["passed"])
        self.assertTrue(cheap_invalid["matches_expected"])

    def test_evidence_closure_positive_and_negative_controls_match_oracles(self) -> None:
        results, errors = EVAL._evidence_localization_fixture_results(
            copy.deepcopy(self.evidence_localization_cases)
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        expected = {
            "localization-missing-close-before-edit": (
                False,
                "evidence-closure-before-action",
            ),
            "closure-known-exact-extra-discovery": (
                False,
                "discovery-after-evidence-closure",
            ),
            "closure-unrelated-nearby-search": (
                False,
                "discovery-after-evidence-closure",
            ),
            "closure-unclosed-contract-bounded-discovery": (True, None),
            "closure-top-k-only-completeness": (False, "selector-as-proof"),
            "closure-claim-local-reopening": (True, None),
            "closure-material-invalidation-continued-edit": (
                False,
                "material-before-edit",
            ),
            "closure-material-invalidation-main-delta": (True, None),
        }
        for case_id, (valid, error_code) in expected.items():
            with self.subTest(case=case_id):
                result = by_id[case_id]
                self.assertEqual(valid, result["quality_gate"]["passed"])
                self.assertTrue(result["matches_expected"])
                if error_code is not None:
                    self.assertIn(error_code, result["quality_gate"]["error_codes"])
        for case_id in (
            "localization-known-exact-zero-search",
            "localization-stable-owner-direct",
            "localization-minimum-complete-evidence",
        ):
            self.assertTrue(by_id[case_id]["evidence_closed"], case_id)
        for case_id in (
            "localization-indirect-consumer-proof-limit",
            "localization-top-k-proof-limit",
        ):
            self.assertEqual("return-main-analysis", by_id[case_id]["worker_action"])

    def test_edit_continue_and_material_proof_limit_require_closed_routing(self) -> None:
        missing_close = copy.deepcopy(next(
            item for item in self.evidence_localization_cases
            if item["id"] == "localization-known-exact-zero-search"
        ))
        missing_close["id"] = "localization-missing-close-before-edit"
        missing_close["expected_valid"] = False
        missing_close["expected_error"] = "evidence-closure-before-action"
        missing_close["operations"] = [
            operation for operation in missing_close["operations"]
            if operation["action"] != "close"
        ]

        material_limit = copy.deepcopy(next(
            item for item in self.evidence_localization_cases
            if item["id"] == "localization-indirect-consumer-proof-limit"
        ))
        material_limit["id"] = "localization-material-proof-limit-continued"
        material_limit["worker_action"] = "continue"
        material_limit["expected_valid"] = False
        material_limit["expected_error"] = "material-proof-limit-return-main"

        results, errors = EVAL._evidence_localization_fixture_results(
            [missing_close, material_limit]
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        self.assertIn(
            "evidence-closure-before-action",
            by_id[missing_close["id"]]["quality_gate"]["error_codes"],
        )
        self.assertIn(
            "material-proof-limit-return-main",
            by_id[material_limit["id"]]["quality_gate"]["error_codes"],
        )

    def test_nonmaterial_legitimate_proof_limit_closes_and_continues(self) -> None:
        case = copy.deepcopy(next(
            item for item in self.evidence_localization_cases
            if item["id"] == "localization-stable-owner-direct"
        ))
        case["id"] = "localization-stable-nonmaterial-contract-proof-limit"
        case["required_evidence"].append("contract")
        case["not_applicable"].remove("contract")
        close_index = next(
            index for index, operation in enumerate(case["operations"])
            if operation["action"] == "close"
        )
        case["operations"].insert(
            close_index,
            {
                "id": "limit-contract",
                "action": "claim",
                "kind": "proof-limit",
                "status": "proof-limit",
                "basis": ["read-owner"],
                "scope": "contract",
                "bytes": 24,
            },
        )
        next(
            operation for operation in case["operations"]
            if operation["action"] == "close"
        )["requirement_statuses"]["contract"] = "legitimate-proof-limit"

        results, errors = EVAL._evidence_localization_fixture_results([case])
        self.assertEqual([], errors)
        self.assertTrue(results[0]["quality_gate"]["passed"])
        self.assertTrue(results[0]["evidence_closed"])
        self.assertEqual("continue", results[0]["worker_action"])

    def test_analysis_review_convergence_and_engineering_choice_controls(self) -> None:
        orchestration_results, orchestration_errors = EVAL._orchestration_fixture_results(
            copy.deepcopy(self.orchestration_cases)
        )
        self.assertEqual([], orchestration_errors)
        orchestration = {item["id"]: item for item in orchestration_results}
        for case_id in (
            "accepted-brief-noninvalidation-events-no-analysis",
            "review-convergence-second-repair",
            "adjacent-finding-no-analysis",
            "preparation-review-loop-forbidden",
            "pre-review-complete-finding-frontier",
            "pre-review-delta-scoped-verification",
        ):
            with self.subTest(case=case_id):
                self.assertTrue(orchestration[case_id]["matches_expected"])

        focus_results, focus_errors = EVAL._task_focus_fixture_results(
            copy.deepcopy(self.task_focus_cases)
        )
        self.assertEqual([], focus_errors)
        focus = {item["id"]: item for item in focus_results}
        for case_id in (
            "l4-risk-depth-not-frequency",
            "engineering-choice-not-user-choice",
        ):
            with self.subTest(case=case_id):
                self.assertTrue(focus[case_id]["matches_expected"])

    def test_l4_boundary_expansion_prereview_fixtures_are_exact(self) -> None:
        results, errors = EVAL._orchestration_fixture_results(
            copy.deepcopy(self.orchestration_cases)
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        self.assertTrue(
            by_id["l4-expanded-material-boundary-second-prereview"][
                "matches_expected"
            ]
        )
        unchanged = by_id["l4-unchanged-boundary-second-prereview"]
        self.assertTrue(unchanged["matches_expected"])
        self.assertTrue(
            any(
                "[preparation-review-loop]" in error
                for error in unchanged["errors"]
            ),
            unchanged["errors"],
        )

    def test_delta_requires_a_legitimate_preceding_invalidation_source(self) -> None:
        review_delta = copy.deepcopy(next(
            event
            for case in self.orchestration_cases
            if case["id"] == "review-post-dispatch-authority-delta"
            for event in case["events"]
            if event.get("analysis_kind") == "delta"
        ))
        evidence_delta = copy.deepcopy(next(
            event
            for case in self.orchestration_cases
            if case["id"] == "pre-review-delta-scoped-verification"
            for event in case["events"]
            if event.get("analysis_kind") == "delta"
        ))
        adjacent = copy.deepcopy(next(
            item for item in self.orchestration_cases
            if item["id"] == "adjacent-finding-no-analysis"
        ))
        current_task = copy.deepcopy(adjacent)
        current_task["id"] = "current-task-finding-delta-forbidden"
        next(
            event for event in current_task["events"]
            if event.get("action") == "finding"
        )["relation"] = "current-task"
        non_invalidation = copy.deepcopy(next(
            item for item in self.orchestration_cases
            if item["id"] == "accepted-brief-noninvalidation-events-no-analysis"
        ))
        cases = (
            (adjacent, review_delta, "complete"),
            (current_task, review_delta, "complete"),
            (non_invalidation, evidence_delta, "non-invalidation"),
        )
        for case, delta, source_action in cases:
            case_id = case["id"]
            with self.subTest(case=case_id):
                source_index = next(
                    index for index, event in enumerate(case["events"])
                    if event.get("action") == source_action
                )
                insertion = source_index if source_action == "complete" else source_index + 1
                case["events"].insert(insertion, copy.deepcopy(delta))
                errors = EVAL._orchestration_case_errors(case)
                self.assertTrue(
                    any("delta-invalidation-source" in error for error in errors),
                    errors,
                )

    def test_pre_review_order_level_and_finding_frontier_are_structural(self) -> None:
        base = copy.deepcopy(next(
            item for item in self.orchestration_cases
            if item["id"] == "pre-review-complete-finding-frontier"
        ))
        pre_index = next(
            index for index, event in enumerate(base["events"])
            if event.get("action") == "pre-review"
        )
        edit_index = next(
            index for index, event in enumerate(base["events"])
            if event.get("action") == "edit"
        )

        post_edit = copy.deepcopy(base)
        pre_review = post_edit["events"].pop(pre_index)
        post_edit["events"].insert(edit_index + 1, pre_review)
        self.assertTrue(any(
            "pre-review-order" in error
            for error in EVAL._orchestration_case_errors(post_edit)
        ))

        incomplete_frontier = copy.deepcopy(base)
        next(
            event for event in incomplete_frontier["events"]
            if event.get("action") == "pre-review"
        )["finding_ids"] = []
        self.assertTrue(any(
            "pre-review-finding-frontier" in error
            for error in EVAL._orchestration_case_errors(incomplete_frontier)
        ))

        keyword_only = copy.deepcopy(base)
        next(
            event for event in keyword_only["events"]
            if event.get("analysis_kind") == "initial"
        ).pop("material_intermediate_review_triggers")
        self.assertTrue(any(
            "pre-review-trigger" in error
            for error in EVAL._orchestration_case_errors(keyword_only)
        ))

        l3 = copy.deepcopy(base)
        l3["review_boundary"]["effective_level"] = "L3"
        next(
            event for event in l3["events"]
            if event.get("action") == "pre-review"
        )["effective_level"] = "L3"
        self.assertTrue(any(
            "pre-review-frequency" in error
            for error in EVAL._orchestration_case_errors(l3)
        ))

        l5_missing = copy.deepcopy(base)
        l5_missing["review_boundary"]["effective_level"] = "L5"
        l5_missing["events"] = [
            event for event in l5_missing["events"]
            if event.get("action") not in {"pre-review", "finding"}
        ]
        self.assertTrue(any(
            "pre-review-mandatory" in error
            for error in EVAL._orchestration_case_errors(l5_missing)
        ))

        triggered_l4_missing = copy.deepcopy(base)
        triggered_l4_missing["events"] = [
            event for event in triggered_l4_missing["events"]
            if event.get("action") not in {"pre-review", "finding"}
        ]
        self.assertTrue(any(
            "pre-review-mandatory" in error
            for error in EVAL._orchestration_case_errors(triggered_l4_missing)
        ))

    def test_global_structural_ceilings_exclude_only_explicit_per_case_bounds(self) -> None:
        self.assertEqual(
            {
                "control_turn_count": 11,
                "subagent_count": 5,
                "duplicate_read_count": 0,
                "verification_action_count": 4,
            },
            EVAL.CORE_CONTRACTS["final_goal_contract"][
                "maximum_structural_proxies"
            ],
        )
        results = [
            {
                "id": "ordinary",
                "metrics": {
                    "control_turn_count": 9,
                    "subagent_count": 4,
                    "duplicate_read_count": 0,
                    "verification_action_count": 4,
                },
            },
            {
                "id": "repair-and-rereview",
                "metrics": {
                    "control_turn_count": 19,
                    "subagent_count": 8,
                    "duplicate_read_count": 0,
                    "verification_action_count": 8,
                    "repair_has_rereview": True,
                },
            },
        ]
        expectations = {
            "ordinary": {
                "control_turns_max": 11,
                "subagents": 4,
                "duplicate_reads_max": 0,
                "verification_actions_max": 4,
            },
            "repair-and-rereview": {
                "control_turns_max": 20,
                "subagents": 8,
                "duplicate_reads_max": 0,
                "verification_actions_max": 8,
                "repair_requires_rereview": True,
            },
        }
        aggregate = EVAL._aggregate(results, expectations)
        for metric, expected_max in {
            "control_turn_count": 9,
            "subagent_count": 4,
            "verification_action_count": 4,
        }.items():
            with self.subTest(metric=metric):
                self.assertEqual(expected_max, aggregate[metric]["max"])
                self.assertEqual(
                    ["repair-and-rereview"],
                    aggregate[metric]["per_case_exception_ids"],
                )
        self.assertEqual(19, aggregate["control_turn_count"]["observed_max"])
        self.assertEqual(8, aggregate["subagent_count"]["observed_max"])
        self.assertEqual(8, aggregate["verification_action_count"]["observed_max"])

        ordinary_over_cap = copy.deepcopy(results)
        ordinary_over_cap[0]["metrics"]["control_turn_count"] = 19
        over_cap_expectations = copy.deepcopy(expectations)
        over_cap_expectations["ordinary"]["control_turns_max"] = 20
        over_cap = EVAL._aggregate(ordinary_over_cap, over_cap_expectations)
        self.assertEqual(19, over_cap["control_turn_count"]["max"])
        self.assertNotIn(
            "ordinary", over_cap["control_turn_count"]["per_case_exception_ids"]
        )

    def test_known_exact_and_stable_direct_localization_costs(self) -> None:
        results, errors = EVAL._evidence_localization_fixture_results(
            copy.deepcopy(self.document["evidence_localization_cases"])
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        known = by_id["localization-known-exact-zero-search"]
        self.assertEqual(0, known["cost_observation"]["search_count"])
        self.assertGreater(known["cost_observation"]["exact_read_count"], 0)
        self.assertEqual(0, known["cost_observation"]["repeated_read_count"])
        stable = by_id["localization-stable-owner-direct"]
        self.assertTrue(stable["quality_gate"]["passed"])
        self.assertEqual("continue", stable["worker_action"])
        self.assertTrue(stable["authority_preserved"])
        escalated = by_id["localization-material-risk-return"]
        self.assertEqual("return-main-analysis", escalated["worker_action"])
        self.assertEqual(0, escalated["cost_observation"]["time_to_first_edit_step"])

    def test_unknown_location_requires_candidate_search(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.document["evidence_localization_cases"]
                if item["id"] == "localization-read-search-fallback"
            )
        )
        case["operations"] = [
            operation
            for operation in case["operations"]
            if operation["action"] != "search"
        ]
        results, _errors = EVAL._evidence_localization_fixture_results([case])
        self.assertFalse(results[0]["quality_gate"]["passed"])
        self.assertIn(
            "unknown-location-search",
            results[0]["quality_gate"]["error_codes"],
        )

    def test_unknown_location_search_must_precede_current_source_reads(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.document["evidence_localization_cases"]
                if item["id"] == "localization-stable-owner-direct"
            )
        )
        search = next(
            operation for operation in case["operations"] if operation["action"] == "search"
        )
        operations_without_search = [
            operation for operation in case["operations"] if operation is not search
        ]
        first_claim_index = next(
            index
            for index, operation in enumerate(operations_without_search)
            if operation["action"] == "claim"
        )
        operations_without_search.insert(first_claim_index, search)
        case["operations"] = operations_without_search

        results, _errors = EVAL._evidence_localization_fixture_results([case])

        self.assertFalse(results[0]["quality_gate"]["passed"])
        self.assertIn(
            "unknown-location-order",
            results[0]["quality_gate"]["error_codes"],
        )

    def test_known_exact_review_anchor_uses_independent_exact_read_without_search(
        self,
    ) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.document["evidence_localization_cases"]
                if item["id"] == "localization-known-exact-review-anchor"
            )
        )
        results, errors = EVAL._evidence_localization_fixture_results([case])
        self.assertEqual([], errors)
        self.assertTrue(results[0]["quality_gate"]["passed"])
        self.assertEqual(0, results[0]["cost_observation"]["search_count"])
        self.assertGreater(results[0]["cost_observation"]["exact_read_count"], 0)

    def test_exact_search_and_one_consumer_read_cannot_prove_absence(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.document["evidence_localization_cases"]
                if item["id"] == "localization-top-k-cannot-prove-absence"
            )
        )
        search = next(
            operation for operation in case["operations"] if operation["action"] == "search"
        )
        search["mode"] = "exact"
        search["result_volume"] = 1
        results, _errors = EVAL._evidence_localization_fixture_results([case])
        self.assertFalse(results[0]["quality_gate"]["passed"])
        self.assertIn(
            "completeness-coverage",
            results[0]["quality_gate"]["error_codes"],
        )

    def test_indirect_consumer_gap_requires_visible_proof_limit(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.document["evidence_localization_cases"]
                if item["id"] == "localization-indirect-consumer-proof-limit"
            )
        )
        results, errors = EVAL._evidence_localization_fixture_results([case])
        self.assertEqual([], errors)
        self.assertTrue(results[0]["quality_gate"]["passed"])
        self.assertTrue(results[0]["proof_limit_recorded"])

    def test_localization_negative_controls_reject_selector_and_inherited_proof(
        self,
    ) -> None:
        results, errors = EVAL._evidence_localization_fixture_results(
            copy.deepcopy(self.document["evidence_localization_cases"])
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        for case_id, code in (
            ("localization-nearby-is-not-owner", "owner-current-source-proof"),
            ("localization-same-pattern-exact-misses-variant", "completeness-coverage"),
            ("localization-top-k-cannot-prove-absence", "selector-as-proof"),
            ("localization-truncation-cannot-prove-complete", "selector-as-proof"),
            ("localization-indirect-consumer-not-closed", "completeness-coverage"),
            ("localization-task-cannot-inherit-correctness", "inherited-proof"),
            ("localization-review-independent-required", "review-independent-localization"),
            ("localization-cost-cannot-hide-quality", "selector-as-proof"),
        ):
            with self.subTest(case=case_id):
                item = by_id[case_id]
                self.assertFalse(item["quality_gate"]["passed"])
                self.assertIn(code, item["quality_gate"]["error_codes"])
                self.assertTrue(item["matches_expected"])

    def test_structural_fallback_minimum_complete_evidence_and_authority_invariance(
        self,
    ) -> None:
        results, errors = EVAL._evidence_localization_fixture_results(
            copy.deepcopy(self.document["evidence_localization_cases"])
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        fallback = by_id["localization-read-search-fallback"]
        self.assertTrue(fallback["quality_gate"]["passed"])
        self.assertTrue(fallback["fallback_used"])
        complete = by_id["localization-minimum-complete-evidence"]
        self.assertTrue(complete["quality_gate"]["passed"])
        self.assertEqual(
            {
                "owner",
                "consumer",
                "invariant",
                "test",
                "contract",
                "validation-boundary",
            },
            set(complete["covered_evidence"]),
        )
        for item in results:
            self.assertTrue(item["authority_preserved"], item)

    def test_exact_locator_trust_fixtures_cover_declared_boundaries(self) -> None:
        results, errors = EVAL._evidence_localization_fixture_results(
            copy.deepcopy(self.evidence_localization_cases)
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        expected_ids = {
            "locator-exact-caller-not-owner",
            "locator-exact-delegator-not-owner",
            "locator-confirmed-owner-stops-discovery",
            "locator-same-owner-symbol-move-bounded-correction",
            "locator-direct-material-contradiction-main-initial-analysis",
            "locator-stale-brief-owner-main-delta",
            "locator-review-fix-moved-finding-still-valid",
            "locator-generated-target-traces-authoring-source",
            "locator-multiple-enforcement-points",
            "locator-zero-static-refs-dynamic-consumer-proof-limit",
            "locator-structural-unavailable-read-search-fallback",
        }
        self.assertEqual(expected_ids, {case_id for case_id in by_id if case_id.startswith("locator-")})
        self.assertEqual(38, len(results))
        for case_id in expected_ids:
            with self.subTest(case=case_id):
                self.assertTrue(by_id[case_id]["matches_expected"], by_id[case_id])

        for case_id in (
            "locator-exact-caller-not-owner",
            "locator-exact-delegator-not-owner",
        ):
            self.assertIn(
                "owner-current-source-proof",
                by_id[case_id]["quality_gate"]["error_codes"],
            )
        self.assertEqual(
            0,
            by_id["locator-confirmed-owner-stops-discovery"]["cost_observation"][
                "search_count"
            ],
        )
        self.assertEqual(
            "return-main-analysis",
            by_id["locator-direct-material-contradiction-main-initial-analysis"][
                "worker_action"
            ],
        )
        self.assertEqual(
            "return-main-delta",
            by_id["locator-stale-brief-owner-main-delta"]["worker_action"],
        )
        structural = by_id["locator-same-owner-symbol-move-bounded-correction"]
        self.assertIn("structural-search", structural["host_capabilities"])
        self.assertTrue(structural["bounded_structural_correction"])
        self.assertFalse(
            by_id["locator-multiple-enforcement-points"][
                "bounded_structural_correction"
            ]
        )
        self.assertTrue(
            by_id["locator-zero-static-refs-dynamic-consumer-proof-limit"][
                "proof_limit_recorded"
            ]
        )
        self.assertTrue(
            by_id["locator-structural-unavailable-read-search-fallback"][
                "fallback_used"
            ]
        )

    def test_bounded_structural_correction_report_requires_validated_sequence(
        self,
    ) -> None:
        by_id = {case["id"]: case for case in self.evidence_localization_cases}
        structural = copy.deepcopy(
            by_id["locator-same-owner-symbol-move-bounded-correction"]
        )
        symbol = copy.deepcopy(structural)
        symbol["id"] = "mutation-symbol-correction-positive"
        symbol["host_capabilities"].remove("structural-search")
        symbol["host_capabilities"].append("symbol-search")
        next(
            operation
            for operation in symbol["operations"]
            if operation["action"] == "search"
        )["mode"] = "symbol"

        unknown = copy.deepcopy(by_id["locator-multiple-enforcement-points"])

        invalid_cases = []
        undeclared = copy.deepcopy(structural)
        undeclared["id"] = "mutation-report-undeclared-structural"
        undeclared["host_capabilities"].remove("structural-search")
        undeclared["expected_valid"] = False
        undeclared["expected_error"] = "locator-correction-capability"
        invalid_cases.append(undeclared)

        truncated = copy.deepcopy(structural)
        truncated["id"] = "mutation-report-truncated-structural"
        next(
            operation
            for operation in truncated["operations"]
            if operation["action"] == "search"
        )["truncated"] = True
        truncated["expected_valid"] = False
        truncated["expected_error"] = "locator-correction-capability"
        invalid_cases.append(truncated)

        broad = copy.deepcopy(structural)
        broad["id"] = "mutation-report-broad-correction"
        next(
            operation
            for operation in broad["operations"]
            if operation["action"] == "search"
        )["mode"] = "expanded"
        broad["expected_valid"] = False
        broad["expected_error"] = "known-exact-discovery"
        invalid_cases.append(broad)

        repeated = copy.deepcopy(structural)
        repeated["id"] = "mutation-report-repeated-correction-read"
        repeated_read = copy.deepcopy(
            next(
                operation
                for operation in repeated["operations"]
                if operation.get("coverage") == "owner"
            )
        )
        repeated_read["id"] = "repeated-owner-read"
        claim_index = next(
            index
            for index, operation in enumerate(repeated["operations"])
            if operation["action"] == "claim"
        )
        repeated["operations"].insert(claim_index, repeated_read)
        repeated["expected_valid"] = False
        repeated["expected_error"] = "known-exact-discovery"
        invalid_cases.append(repeated)

        results, errors = EVAL._evidence_localization_fixture_results(
            [structural, symbol, unknown, *invalid_cases]
        )
        self.assertEqual([], errors)
        results_by_id = {item["id"]: item for item in results}
        self.assertTrue(
            results_by_id[structural["id"]]["bounded_structural_correction"]
        )
        self.assertTrue(results_by_id[symbol["id"]]["bounded_structural_correction"])
        self.assertFalse(results_by_id[unknown["id"]]["bounded_structural_correction"])
        for case in invalid_cases:
            with self.subTest(case=case["id"]):
                result = results_by_id[case["id"]]
                self.assertFalse(result["quality_gate"]["passed"])
                self.assertFalse(result["bounded_structural_correction"])

    def test_exact_locator_trust_mutation_controls_fail_closed_generically(self) -> None:
        by_id = {case["id"]: case for case in self.evidence_localization_cases}

        broad_after_confirmation = copy.deepcopy(
            by_id["locator-confirmed-owner-stops-discovery"]
        )
        broad_after_confirmation["id"] = "mutation-confirmed-owner-broad-search"
        broad_after_confirmation["operations"].insert(
            -1,
            {
                "id": "broad-search",
                "action": "search",
                "mode": "expanded",
                "target": "repository owners",
                "result_volume": 9,
                "truncated": False,
                "bytes": 96,
            },
        )

        brief_mutation = copy.deepcopy(
            by_id["locator-same-owner-symbol-move-bounded-correction"]
        )
        brief_mutation["id"] = "mutation-local-correction-rewrites-brief"
        next(
            operation
            for operation in brief_mutation["operations"]
            if operation["action"] == "correction"
        )["brief_mutation"] = True

        correction_before_search = copy.deepcopy(
            by_id["locator-same-owner-symbol-move-bounded-correction"]
        )
        correction_before_search["id"] = "mutation-correction-before-bounded-search"
        correction_index = next(
            index
            for index, operation in enumerate(correction_before_search["operations"])
            if operation["action"] == "correction"
        )
        correction = correction_before_search["operations"].pop(correction_index)
        correction_before_search["operations"].insert(correction_index - 1, correction)

        stale_owner_edit = copy.deepcopy(by_id["locator-stale-brief-owner-main-delta"])
        stale_owner_edit["id"] = "mutation-material-owner-contradiction-edits"
        stale_owner_edit["operations"].append(
            {"id": "unsafe-edit", "action": "edit", "target": "caller.py", "bytes": 0}
        )
        stale_owner_edit["worker_action"] = "continue"

        generated_without_trace = copy.deepcopy(
            by_id["locator-generated-target-traces-authoring-source"]
        )
        generated_without_trace["id"] = "mutation-generated-without-authoring-trace"
        generated_without_trace["operations"] = [
            operation
            for operation in generated_without_trace["operations"]
            if operation["action"] != "trace"
        ]

        dynamic_without_limit = copy.deepcopy(
            by_id["locator-zero-static-refs-dynamic-consumer-proof-limit"]
        )
        dynamic_without_limit["id"] = "mutation-dynamic-consumer-without-proof-limit"
        dynamic_without_limit["operations"] = [
            operation
            for operation in dynamic_without_limit["operations"]
            if operation.get("kind") != "proof-limit"
        ]
        next(
            operation
            for operation in dynamic_without_limit["operations"]
            if operation["action"] == "close"
        )["requirement_statuses"]["consumer"] = "proved"

        no_fallback = copy.deepcopy(
            by_id["locator-structural-unavailable-read-search-fallback"]
        )
        no_fallback["id"] = "mutation-structural-unavailable-no-fallback"
        next(
            operation
            for operation in no_fallback["operations"]
            if operation["action"] == "search"
        )["mode"] = "exact"

        direct_wrong_delta = copy.deepcopy(
            by_id["locator-direct-material-contradiction-main-initial-analysis"]
        )
        direct_wrong_delta["id"] = "mutation-direct-without-brief-wrong-delta"
        direct_wrong_delta["worker_action"] = "return-main-delta"

        brief_wrong_analysis = copy.deepcopy(
            by_id["locator-stale-brief-owner-main-delta"]
        )
        brief_wrong_analysis["id"] = "mutation-accepted-brief-wrong-initial-analysis"
        brief_wrong_analysis["worker_action"] = "return-main-analysis"

        undeclared_structural = copy.deepcopy(
            by_id["locator-same-owner-symbol-move-bounded-correction"]
        )
        undeclared_structural["id"] = "mutation-undeclared-structural-correction"
        undeclared_structural["host_capabilities"].remove("structural-search")

        truncated_structural = copy.deepcopy(
            by_id["locator-same-owner-symbol-move-bounded-correction"]
        )
        truncated_structural["id"] = "mutation-truncated-structural-correction"
        next(
            operation
            for operation in truncated_structural["operations"]
            if operation["action"] == "search"
        )["truncated"] = True

        controls = (
            (broad_after_confirmation, "known-exact-discovery"),
            (brief_mutation, "locator-correction"),
            (correction_before_search, "locator-correction"),
            (stale_owner_edit, "material-before-edit"),
            (generated_without_trace, "generated-authoring-source"),
            (dynamic_without_limit, "dynamic-consumer-proof-limit"),
            (no_fallback, "structural-fallback"),
            (direct_wrong_delta, "material-return-outcome"),
            (brief_wrong_analysis, "material-return-outcome"),
            (undeclared_structural, "locator-correction-capability"),
            (truncated_structural, "locator-correction-capability"),
        )
        for case, expected_code in controls:
            case["expected_valid"] = False
            case["expected_error"] = expected_code
            with self.subTest(case=case["id"]):
                results, errors = EVAL._evidence_localization_fixture_results([case])
                self.assertEqual([], errors)
                self.assertIn(expected_code, results[0]["quality_gate"]["error_codes"])
                self.assertTrue(results[0]["matches_expected"])

    def test_remaining_twelve_behaviors_use_full_path_machine_mutations(self) -> None:
        results, errors = EVAL._required_behavior_coverage_results(
            copy.deepcopy(self.document),
            self.professional,
            self.layer3,
        )
        self.assertEqual([], errors)
        remaining = [
            item for item in results if item["group"] != "ai-reading-ownership"
        ]
        self.assertEqual(12, len(remaining))
        self.assertTrue(
            all(
                item["status"] == "covered"
                and item["full_path_valid"]
                and item["mutation_applied"]
                and item["bypass_rejected"]
                for item in remaining
            )
        )

    def test_required_behavior_manifest_equals_immutable_per_id_oracle(self) -> None:
        manifest_entries = {
            entry["id"]: entry
            for group in self.document["required_behavior_coverage"]["groups"]
            for entry in group["entries"]
        }
        self.assertEqual(
            set(EVAL.REQUIRED_BEHAVIOR_CONTRACTS), set(manifest_entries)
        )
        for behavior_id, contract in EVAL.REQUIRED_BEHAVIOR_CONTRACTS.items():
            with self.subTest(behavior=behavior_id):
                self.assertEqual(
                    EVAL._required_behavior_manifest_entry(behavior_id, contract),
                    manifest_entries[behavior_id],
                )

    def test_required_behavior_oracle_rejects_every_one_field_swap(self) -> None:
        fields = (
            "positive_case",
            "validator_family",
            "bypass_mutation",
            "expected_error",
            "dimensions",
        )
        contracts = EVAL.REQUIRED_BEHAVIOR_CONTRACTS
        for behavior_id, contract in contracts.items():
            for field in fields:
                donor = next(
                    candidate
                    for candidate in contracts.values()
                    if getattr(candidate, field) != getattr(contract, field)
                )
                with self.subTest(behavior=behavior_id, field=field):
                    document = copy.deepcopy(self.document)
                    entry = next(
                        entry
                        for group in document["required_behavior_coverage"]["groups"]
                        for entry in group["entries"]
                        if entry["id"] == behavior_id
                    )
                    if field == "positive_case":
                        entry["positive_trajectory"]["case_id"] = donor.positive_case
                    elif field == "validator_family":
                        entry["positive_trajectory"]["validator_family"] = (
                            donor.validator_family
                        )
                    elif field == "bypass_mutation":
                        entry["bypass_mutation"]["kind"] = donor.bypass_mutation
                    elif field == "expected_error":
                        entry["expected_error"]["code"] = donor.expected_error
                    else:
                        entry["dimensions"] = list(donor.dimensions)
                    _results, errors = EVAL._required_behavior_coverage_results(
                        document,
                        self.professional,
                        self.layer3,
                    )
                    self.assertTrue(
                        any("immutable contract oracle" in error for error in errors),
                        errors,
                    )

    def test_scheduling_positive_still_requires_full_implementation_discipline(
        self,
    ) -> None:
        document = copy.deepcopy(self.document)
        case = next(
            case
            for case in document["cases"]
            if case["id"] == "isolated-write-parallel-contract"
        )
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "implementation-discipline"
        ]
        results, errors = EVAL._required_behavior_coverage_results(
            document,
            self.professional,
            self.layer3,
        )
        parallel = next(
            result
            for result in results
            if result["id"] == "closure-parallel-writes-require-isolation"
        )
        self.assertFalse(parallel["full_path_valid"])
        self.assertTrue(
            any("positive full trajectory" in error for error in errors), errors
        )

    def test_required_behavior_coverage_rejects_missing_duplicate_and_unknown_ids(
        self,
    ) -> None:
        variants = {}
        missing = copy.deepcopy(self.document)
        missing["required_behavior_coverage"]["groups"][0]["entries"].pop()
        variants["missing"] = missing

        duplicate = copy.deepcopy(self.document)
        duplicate["required_behavior_coverage"]["groups"][0]["entries"].append(
            copy.deepcopy(
                duplicate["required_behavior_coverage"]["groups"][0]["entries"][0]
            )
        )
        variants["duplicate"] = duplicate

        unknown = copy.deepcopy(self.document)
        unknown["required_behavior_coverage"]["groups"][0]["entries"][0][
            "id"
        ] = "ai-reading-unknown-substitute"
        variants["unknown"] = unknown

        replaced = copy.deepcopy(self.document)
        replaced_entry = replaced["required_behavior_coverage"]["groups"][1][
            "entries"
        ][0]
        replaced_entry["bypass_mutation"] = {
            "kind": "existing-structured-negative",
            "fixture_group": "adaptive_testing_cases",
            "case_id": "adaptive-rejects-high-risk-downgrade",
        }
        variants["replaced-with-isolated-negative"] = replaced

        for label, document in variants.items():
            with self.subTest(label=label):
                _results, errors = EVAL._required_behavior_coverage_results(
                    document,
                    self.professional,
                    self.layer3,
                )
                self.assertTrue(
                    any(
                        "exact required behavior ids" in error
                        or "covered bypass mutation is invalid" in error
                        or "immutable contract oracle" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_required_behavior_coverage_rejects_keyword_only_substitution(self) -> None:
        document = copy.deepcopy(self.document)
        entry = document["required_behavior_coverage"]["groups"][0]["entries"][0]
        entry["observed_behaviors"] = [entry.pop("positive_trajectory")]
        _results, errors = EVAL._required_behavior_coverage_results(
            document,
            self.professional,
            self.layer3,
        )
        self.assertTrue(
            any("observed_behaviors" in error for error in errors),
            errors,
        )

    def test_ai_reading_bypass_mutations_fail_at_the_named_structured_guard(
        self,
    ) -> None:
        results, errors = EVAL._required_behavior_coverage_results(
            copy.deepcopy(self.document),
            self.professional,
            self.layer3,
        )
        self.assertEqual([], errors)
        ai_results = [
            item for item in results if item["group"] == "ai-reading-ownership"
        ]
        self.assertEqual(5, len(ai_results))
        for item in ai_results:
            with self.subTest(behavior=item["id"]):
                self.assertTrue(item["mutation_applied"])
                self.assertTrue(item["bypass_rejected"])
                self.assertIn(item["expected_error"], item["error_codes"])

    def test_documentation_full_path_uses_only_non_test_validation(self) -> None:
        case = self._release_case("release-rollback")
        event = self._discipline_event(case)
        guard = next(
            item
            for item in event["evidence"]
            if item["guard"] == EVAL.IMPLEMENTATION_GUARD_CODES["G"]
        )
        self.assertEqual("non-behavior", guard["change_kind"])
        self.assertEqual("non-test-validation", guard["approach"])
        records = [
            step
            for step in case["steps"]
            if step.get("action") == EVAL.ADAPTIVE_TEST_EVIDENCE_ACTION
        ]
        self.assertEqual(["non-test"], [record["evidence_kind"] for record in records])
        self.assertEqual([], self._trajectory_errors(case))

        EVAL._apply_required_behavior_bypass_mutation(
            case, "misclassify-documentation-as-behavior"
        )
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["G"],
            self._error_codes(self._trajectory_errors(case)),
        )

    def test_parallel_coverage_uses_scheduling_validator_family(self) -> None:
        manifest_entry = next(
            entry
            for group in self.document["required_behavior_coverage"]["groups"]
            for entry in group["entries"]
            if entry["id"] == "closure-parallel-writes-require-isolation"
        )
        self.assertEqual(
            "scheduling",
            manifest_entry["positive_trajectory"]["validator_family"],
        )
        case = self._release_case("isolated-write-parallel-contract")
        operational, _internal = EVAL._operational_steps(case["steps"])
        conflict, reduction = EVAL._parallel_metrics(operational)
        self.assertFalse(conflict)
        self.assertGreaterEqual(reduction, 1)

        EVAL._apply_required_behavior_bypass_mutation(
            case, "remove-parallel-workspace-isolation"
        )
        operational, _internal = EVAL._operational_steps(case["steps"])
        conflict, _reduction = EVAL._parallel_metrics(operational)
        self.assertTrue(conflict)

    def test_authoritative_dag_positive_fixtures_start_downstream_direct(
        self,
    ) -> None:
        fixtures = (
            self._release_case("isolated-write-parallel-contract"),
            copy.deepcopy(
                next(
                    item
                    for item in self.scheduling_cases
                    if item["id"] == "shared-workspace-serial-write"
                )
            ),
        )
        accepted_input = (
            "Accepted, artifact-reviewed authoritative Task DAG and downstream "
            "Task Capsule"
        )
        for case in fixtures:
            with self.subTest(case=case["id"]):
                self.assertEqual("direct", case["kind"])
                self.assertFalse(case["expected"]["requires_analysis"])
                serialized = EVAL.json.dumps(case).casefold()
                self.assertNotIn('"actor": "analysis-agent"', serialized)
                self.assertNotIn('"action": "search"', serialized)
                self.assertNotIn('"action": "first_executable_slice"', serialized)
                self.assertNotIn("analysis-handoff", serialized)
                self.assertNotIn("isolation-analysis", serialized)
                task_dispatches = [
                    step
                    for step in case["steps"]
                    if step.get("action") == "dispatch"
                    and step.get("profile") == "task-agent"
                ]
                self.assertGreaterEqual(len(task_dispatches), 2)
                for dispatch in task_dispatches:
                    capsule = dispatch["fixture_capsule"]
                    self.assertIn(accepted_input, capsule["inputs"])
                    self.assertTrue(
                        any(
                            "authoritative Task DAG" in dependency
                            or "completed" in dependency.casefold()
                            for dependency in capsule["dependencies"]
                        )
                    )

    def test_review_discipline_fixture_matrix_is_complete_and_green(self) -> None:
        results, errors = EVAL._review_discipline_fixture_results(
            self.review_discipline_cases
        )
        self.assertEqual([], errors)
        self.assertEqual(35, len(results))
        self.assertTrue(all(result["matches_expected"] for result in results))

        level_results = {
            result["level"]
            for result in results
            if result["id"].startswith("review-level-")
        }
        self.assertEqual({"L1", "L2", "L3", "L4", "L5"}, level_results)
        missing_dimensions = {
            case["mutation"]["dimension"]
            for case in self.review_discipline_cases
            if case["mutation"]["kind"] == "drop-dimension"
        }
        self.assertEqual(set(EVAL.REVIEW_BASE_DIMENSIONS), missing_dimensions)

    def test_professional_risk_matrix_accepts_complete_and_rejects_invalid_rows(
        self,
    ) -> None:
        valid = {
            "id": "professional-risks-complete",
            "level": "L3",
            "mutation": {"kind": "none"},
        }
        valid_steps = EVAL._review_fixture_steps(valid)
        event = next(
            step
            for step in valid_steps
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        self.assertEqual(
            list(EVAL.REVIEW_PROFESSIONAL_RISK_DIMENSIONS),
            [decision["dimension"] for decision in event["professional_risks"]],
        )
        self.assertEqual(
            [], EVAL._review_discipline_errors(valid["id"], valid_steps)
        )

        invalid = {
            "missing-professional-dimension": "missing professional-risk dimensions",
            "unsupported-professional-status": "unsupported professional-risk status",
            "unevidenced-not-applicable": "source-backed reason and evidence",
            "incomplete-delegation": "named registered Review Skill, scope, and reason",
            "duplicate-professional-dimension": "duplicate professional-risk dimensions",
        }
        for mutation_kind, expected in invalid.items():
            with self.subTest(mutation=mutation_kind):
                steps = EVAL._review_fixture_steps(
                    {
                        "id": f"professional-risks-{mutation_kind}",
                        "level": "L3",
                        "mutation": {"kind": mutation_kind},
                    }
                )
                errors = EVAL._review_discipline_errors(mutation_kind, steps)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_review_kind_is_derived_from_actual_material_actions(self) -> None:
        repair_steps = EVAL._review_fixture_steps(
            {
                "id": "repair-as-implementation-reproduction",
                "level": "L3",
                "mutation": {"kind": "repair-as-implementation"},
            }
        )
        repair_errors = EVAL._review_discipline_errors(
            "repair-as-implementation-reproduction", repair_steps
        )
        self.assertTrue(
            any(
                "actual material actions require repair review" in error
                for error in repair_errors
            ),
            repair_errors,
        )

        valid_repair_steps = copy.deepcopy(repair_steps)
        event = next(
            step
            for step in valid_repair_steps
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        event["review_kind"] = "repair"
        valid_repair_steps[-1].update(
            action="re-review",
            rereview_checks=list(EVAL.REREVIEW_CHECKS),
            rereview_scope_expanded=False,
            frozen_boundary_status="preserved",
            frozen_professional_risk_boundary_status="preserved",
        )
        self.assertEqual(
            [],
            EVAL._review_discipline_errors(
                "valid-repair-reproduction", valid_repair_steps
            ),
        )

        disguised_edit_steps = copy.deepcopy(valid_repair_steps)
        disguised_edit_steps[0]["action"] = "edit"
        disguised_edit_errors = EVAL._review_discipline_errors(
            "edit-as-repair-reproduction", disguised_edit_steps
        )
        self.assertTrue(
            any(
                "actual material actions require implementation review" in error
                for error in disguised_edit_errors
            ),
            disguised_edit_errors,
        )

    def test_normal_review_rejects_missing_handoff_and_main_readiness_gate(
        self,
    ) -> None:
        case = self._release_case("single-file-bug-fix")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action")
            not in {"implementation-handoff", "review-input-ready"}
        ]
        for step in case["steps"]:
            if step.get("action") == "dispatch" and step.get("profile") == "review-agent":
                step.pop("review_input_binding", None)

        errors = self._trajectory_errors(case)
        self.assertTrue(
            any("normal review requires one current Implementation Handoff" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("review dispatch requires one derived Main readiness gate" in error for error in errors),
            errors,
        )

    def test_normal_review_rejects_placeholder_exact_change_evidence(self) -> None:
        case = self._release_case("single-file-bug-fix")
        handoff = next(
            step for step in case["steps"]
            if step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
        )
        handoff["exact_change_evidence"]["artifact"] = "actual.diff"
        dispatch = next(
            step for step in case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "review-agent"
        )
        dispatch["review_input_binding"]["artifact"] = "actual.diff"
        event = next(
            step for step in case["steps"]
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        event["diff"]["artifact"] = "actual.diff"
        errors = self._trajectory_errors(case)
        self.assertTrue(
            any("[review-input-evidence-payload]" in error for error in errors),
            errors,
        )

    def test_analyzed_work_requires_initial_first_and_target_authority(self) -> None:
        case = copy.deepcopy(next(
            item for item in self.orchestration_cases
            if item["id"] == "dedup-protected-delta-preserves-skill"
        ))
        initial_index = next(
            index for index, event in enumerate(case["events"])
            if event.get("analysis_kind") == "initial"
        )
        delta_index = next(
            index for index, event in enumerate(case["events"])
            if event.get("analysis_kind") == "delta"
        )
        case["events"][initial_index], case["events"][delta_index] = (
            case["events"][delta_index],
            case["events"][initial_index],
        )
        errors = EVAL._orchestration_case_errors(case)
        self.assertTrue(
            any("[analysis-initial-order]" in error for error in errors),
            errors,
        )

        authority = copy.deepcopy(next(
            item for item in self.orchestration_cases if item["expected_valid"]
        ))
        initial = next(
            event for event in authority["events"]
            if event.get("analysis_kind") == "initial"
        )
        initial["target_authority"] = {
            "desired_behavior": "preserve the observed failure",
            "observable_acceptance": ["preserve the observed failure"],
            "observed_behavior": "preserve the observed failure",
            "observed_behavior_role": "target-authority",
        }
        errors = EVAL._orchestration_case_errors(authority)
        self.assertTrue(
            any("[analysis-target-authority]" in error for error in errors),
            errors,
        )

    def test_normal_review_input_binding_mutations_fail_closed(self) -> None:
        def locate(case: dict) -> tuple[dict, dict, dict, dict]:
            handoff = next(
                step
                for step in case["steps"]
                if step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
            )
            gate = next(
                step
                for step in case["steps"]
                if step.get("action") == EVAL.REVIEW_INPUT_READY_ACTION
            )
            dispatch = next(
                step
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "review-agent"
            )
            event = next(
                step
                for step in case["steps"]
                if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
            )
            return handoff, gate, dispatch, event

        mutations: dict[str, tuple[str, object]] = {
            "missing-handoff": ("review-input-handoff", None),
            "missing-gate": ("review-input-gate", None),
            "missing-field": ("review-input-handoff-shape", None),
            "wrong-field-order": ("review-input-handoff-shape", None),
            "forbidden-evidence-kind": ("review-input-evidence-kind", None),
            "unreadable-artifact": ("review-input-artifact-access", None),
            "stale-validation": ("review-input-validation", None),
            "duplicate-validation": ("review-input-validation", None),
            "changed-path-mismatch": ("review-input-changed-paths", None),
            "dispatch-artifact-mismatch": ("review-input-dispatch-binding", None),
            "dispatch-generation-mismatch": ("review-input-dispatch-binding", None),
            "reviewer-artifact-mismatch": ("review-input-reviewer-binding", None),
            "gate-false-still-dispatches": ("review-input-dispatch-before-ready", None),
            "post-review-recovery": ("review-input-post-review-recovery", None),
            "task-review-task-review-recovery": ("review-input-recovery", None),
        }
        for mutation, (expected_code, _unused) in mutations.items():
            with self.subTest(mutation=mutation):
                case = self._release_case("single-file-bug-fix")
                handoff, gate, dispatch, event = locate(case)
                if mutation == "missing-handoff":
                    case["steps"].remove(handoff)
                elif mutation == "missing-gate":
                    case["steps"].remove(gate)
                elif mutation == "missing-field":
                    handoff.pop("fixed_review_scope")
                elif mutation == "wrong-field-order":
                    reordered = {
                        key: handoff[key]
                        for key in (
                            "actor",
                            "action",
                            "handoff_id",
                            "task_id",
                            "fixed_review_scope",
                            "latest_changed_paths",
                            "exact_change_evidence",
                            "reviewer_artifact_accessibility",
                            "validation_after_latest_material_edit",
                        )
                    }
                    handoff.clear()
                    handoff.update(reordered)
                elif mutation == "forbidden-evidence-kind":
                    handoff["exact_change_evidence"]["kind"] = "changed-file-summary"
                elif mutation == "unreadable-artifact":
                    handoff["reviewer_artifact_accessibility"]["readable"] = False
                elif mutation == "stale-validation":
                    handoff["validation_after_latest_material_edit"]["generation"] = 0
                elif mutation == "duplicate-validation":
                    validation = next(
                        step
                        for step in case["steps"]
                        if step.get("actor") == "task-agent"
                        and step.get("action") == "validate"
                    )
                    case["steps"].insert(
                        case["steps"].index(handoff),
                        {
                            **copy.deepcopy(validation),
                            "evidence_id": "duplicate-validation",
                        },
                    )
                elif mutation == "changed-path-mismatch":
                    handoff["latest_changed_paths"] = ["other.py"]
                elif mutation == "dispatch-artifact-mismatch":
                    dispatch["review_input_binding"]["artifact"] = "other.diff"
                elif mutation == "dispatch-generation-mismatch":
                    dispatch["review_input_binding"]["generation"] = 0
                elif mutation == "reviewer-artifact-mismatch":
                    event["diff"]["artifact"] = "other.diff"
                elif mutation == "gate-false-still-dispatches":
                    gate["ready"] = False
                elif mutation == "post-review-recovery":
                    case["steps"].insert(
                        -1,
                        {
                            "actor": "task-agent",
                            "action": "export-diff",
                            "artifact_ref": "late-recovery.diff",
                        },
                    )
                elif mutation == "task-review-task-review-recovery":
                    review = next(
                        step
                        for step in case["steps"]
                        if step.get("actor") == "review-agent"
                        and step.get("action") == "review"
                    )
                    case["steps"][-1:-1] = [
                        {
                            "actor": "task-agent",
                            "action": "export-diff",
                            "artifact_ref": "late-recovery.diff",
                        },
                        copy.deepcopy(dispatch),
                        copy.deepcopy(event),
                        copy.deepcopy(review),
                    ]
                errors = self._trajectory_errors(case)
                self.assertTrue(
                    any(f"[{expected_code}]" in error for error in errors),
                    errors,
                )

    def test_normal_review_rounds_bind_one_current_handoff_end_to_end(self) -> None:
        normal_cases = [
            *copy.deepcopy(self.release_cases),
            *copy.deepcopy(self.scheduling_cases),
        ]
        handoffs: list[dict] = []
        for case in normal_cases:
            with self.subTest(case=case["id"]):
                self.assertEqual([], self._trajectory_errors(case))
            handoffs.extend(
                step
                for step in case["steps"]
                if step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
            )
        self.assertEqual(12, len(handoffs))
        self.assertTrue(
            all(tuple(handoff) == EVAL.IMPLEMENTATION_HANDOFF_FIELDS for handoff in handoffs)
        )
        self.assertEqual(
            tuple(EVAL.REVIEW_INPUT_READINESS_MODEL["required_fields"]),
            EVAL.IMPLEMENTATION_HANDOFF_FIELDS[4:],
        )

        repair = self._release_case("repair-and-rereview")
        repair_handoffs = [
            step
            for step in repair["steps"]
            if step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
        ]
        self.assertEqual(
            [1, 2, 3],
            [
                handoff["exact_change_evidence"]["generation"]
                for handoff in repair_handoffs
            ],
        )
        self.assertEqual(3, len({handoff["handoff_id"] for handoff in repair_handoffs}))
        task_dispatches = [
            step
            for step in repair["steps"]
            if step.get("action") == "dispatch" and step.get("profile") == "task-agent"
        ]
        self.assertEqual(
            [
                "task-repair-and-rereview-1",
                "task-repair-and-rereview-1",
                "task-repair-and-rereview-1",
            ],
            [step["fixture_capsule"]["task_id"] for step in task_dispatches],
        )
        self.assertEqual(
            task_dispatches[-1]["finding_ids"],
            [
                obligation["finding_id"]
                for obligation in task_dispatches[-1]["finding_obligations"]
            ],
        )
        repair_dispatches = [
            step
            for step in task_dispatches
            if step.get("mode") == "repair" and step.get("finding_ids")
        ]
        self.assertEqual(2, len(repair_dispatches))
        self.assertEqual(
            [
                "review-repair-and-rereview-1",
                "review-repair-and-rereview-2",
            ],
            [step["review_round_id"] for step in repair_dispatches],
        )
        self.assertEqual(
            ["review-repair-and-rereview-3"],
            [
                step["review_round_id"]
                for step in repair["steps"]
                if step.get("action") == "re-review"
                and step.get("outcome") == "pass"
            ],
        )

    def test_normal_review_rejects_every_unconsumed_late_handoff_gate_pair(
        self,
    ) -> None:
        for insertion_action in (
            "dispatch",
            EVAL.REVIEW_DISCIPLINE_ACTION,
            "review",
        ):
            with self.subTest(insertion_action=insertion_action):
                case = self._release_case("single-file-bug-fix")
                handoff = next(
                    step
                    for step in case["steps"]
                    if step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
                )
                gate = next(
                    step
                    for step in case["steps"]
                    if step.get("action") == EVAL.REVIEW_INPUT_READY_ACTION
                )
                if insertion_action == "dispatch":
                    insertion_index = next(
                        index
                        for index, step in enumerate(case["steps"])
                        if step.get("action") == "dispatch"
                        and step.get("profile") == "review-agent"
                    )
                else:
                    insertion_index = next(
                        index
                        for index, step in enumerate(case["steps"])
                        if step.get("action") == insertion_action
                        and step.get("actor") == "review-agent"
                    )
                case["steps"][insertion_index + 1 : insertion_index + 1] = [
                    copy.deepcopy(handoff),
                    copy.deepcopy(gate),
                ]

                errors = self._trajectory_errors(case)
                self.assertTrue(
                    any("[review-input-occurrence]" in error for error in errors),
                    errors,
                )

    def test_supplied_artifact_and_legacy_utility_do_not_require_normal_handoff(
        self,
    ) -> None:
        review_only = self._release_case("review-only")
        supplied_utility = copy.deepcopy(
            next(
                case
                for case in self.utility_cases
                if case["id"] == "review-supplied-artifact-missing-diff"
            )
        )
        self.assertFalse(
            any(
                step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
                for step in review_only["steps"]
            )
        )
        self.assertEqual([], self._trajectory_errors(review_only))
        self.assertEqual([], self._errors(supplied_utility))

    def test_task_focus_relation_review_repair_and_cost_matrix_is_closed(self) -> None:
        results, errors = EVAL._task_focus_fixture_results(self.task_focus_cases)
        self.assertEqual([], errors)
        self.assertEqual(59, len(results))
        self.assertTrue(all(result["matches_expected"] for result in results))
        self.assertEqual(
            {
                "finding",
                "same-pattern",
                "repair",
                "review-level",
                "cost",
                "analysis-level",
                "review-readiness",
                "direct-confirmation",
                "task-execution",
                "engineering-choice",
            },
            {result["scenario"] for result in results},
        )

    def test_task_execution_preserves_contract_and_blocks_only_actual_failures(self) -> None:
        cases = {
            case["id"]: case
            for case in self.task_focus_cases
            if case["scenario"] == "task-execution"
        }
        positive = cases["focus-task-edit-direct"]
        core_fields = tuple(EVAL.CORE_CONTRACTS["task_contract"]["fields"])
        self.assertEqual(core_fields, EVAL.RUNTIME_TASK_CONTRACT_FIELDS)
        self.assertEqual(core_fields, tuple(positive["inputs"]["original_contract"]))
        self.assertEqual([], EVAL._task_focus_case_errors(positive))
        for case_id in (
            "focus-task-search-direct",
            "focus-task-execute-direct",
            "focus-task-tmp-read-direct",
            "focus-task-retry-preserves-contract",
        ):
            self.assertEqual([], EVAL._task_focus_case_errors(cases[case_id]))
        for case_id in (
            "focus-task-read-actual-failure",
            "focus-task-edit-host-denied",
            "focus-task-execute-sandbox-denied",
        ):
            errors = EVAL._task_focus_case_errors(cases[case_id])
            self.assertTrue(
                any("[untrusted-operation-failure]" in error for error in errors),
                errors,
            )
        retry = cases["focus-task-retry-preserves-contract"]
        self.assertEqual(
            retry["inputs"]["original_contract"],
            retry["inputs"]["retry_contract"],
        )
        changed_retry = copy.deepcopy(retry)
        changed_retry["inputs"]["retry_contract"]["Task ID"] = "different-task"
        self.assertTrue(
            any(
                "Retry must preserve the same real Task ID" in error
                for error in EVAL._task_focus_case_errors(changed_retry)
            )
        )

    def test_task_execution_fixture_preflights_scope_and_rejects_static_failure_proof(self) -> None:
        edit = next(
            copy.deepcopy(case)
            for case in self.task_focus_cases
            if case["id"] == "focus-task-edit-direct"
        )
        edit["inputs"]["target"] = "src/outside.py"
        edit["decision"] = {
            "status": "blocked",
            "blocker": (
                "TASK_CONTRACT_BLOCKED task=task-execution-boundary; "
                "operation=edit; target=src/outside.py; "
                "observed=outside Allowed Write Scope"
            ),
            "edit_count": 0,
            "retry_dispatches": 0,
        }
        self.assertEqual([], EVAL._task_focus_case_errors(edit))

        execute = next(
            copy.deepcopy(case)
            for case in self.task_focus_cases
            if case["id"] == "focus-task-execute-direct"
        )
        execute["inputs"]["write_targets"] = ["src/generated.py"]
        execute["decision"] = {
            "status": "blocked",
            "blocker": (
                "TASK_CONTRACT_BLOCKED task=task-execution-boundary; "
                "operation=execute; target=src/generated.py; "
                "observed=outside Allowed Write Scope"
            ),
            "edit_count": 0,
            "retry_dispatches": 0,
        }
        self.assertEqual([], EVAL._task_focus_case_errors(execute))

        forged = copy.deepcopy(
            next(
                case
                for case in self.task_focus_cases
                if case["id"] == "focus-task-edit-host-denied"
            )
        )
        errors = EVAL._task_focus_case_errors(forged)
        self.assertTrue(
            any("static fixture result cannot prove" in error for error in errors),
            errors,
        )

        success_with_blocker = copy.deepcopy(edit)
        success_with_blocker["inputs"]["target"] = "src/owner.py"
        success_with_blocker["decision"] = {
            "status": "blocked",
            "blocker": (
                "EXECUTION_BLOCKED task=task-execution-boundary; operation=edit; "
                "observed=permission denied by Host"
            ),
            "edit_count": 0,
            "retry_dispatches": 0,
        }
        self.assertTrue(EVAL._task_focus_case_errors(success_with_blocker))

    def test_direct_confirmation_requires_complete_bounded_proof(self) -> None:
        direct = next(
            copy.deepcopy(case)
            for case in self.task_focus_cases
            if case["id"] == "focus-direct-candidate-confirmed-edit-l3"
        )
        direct["inputs"]["confirmation_evidence"] = {
            "owner": "proven",
            "placement": "proven",
            "relevant-test": "proven",
            "consumer-boundary": "proven",
            "executable-validation": "proven",
            "bounded-evidence-closure": "proven",
        }
        direct["decision"].update({"outcome": "main-initial-analysis", "edit_count": 0})
        self.assertEqual([], EVAL._task_focus_case_errors(direct))

    def test_orchestration_dedup_structural_positive_and_negative_controls(self) -> None:
        results, errors = EVAL._orchestration_fixture_results(
            self.orchestration_cases
        )
        self.assertEqual([], errors)
        self.assertTrue(all(result["matches_expected"] for result in results))
        result_by_id = {result["id"]: result for result in results}
        semantic_mutations = {
            "duplicate-same-scope-analysis": "analysis-decision-invalidation",
            "review-every-edit-task": "review-boundary-frequency",
            "skip-final-review-boundary": "completion-current-evidence",
            "extra-final-review-after-covering-rereview": "obligation-subsumption",
            "rerun-valid-validation-without-invalidation": "validation-evidence-reuse",
            "reuse-validation-after-material-edit": "review-validation-binding",
            "repair-without-fresh-validation": "review-validation-binding",
            "repair-without-rereview": "completion-current-evidence",
        }
        for case_id, expected_error in semantic_mutations.items():
            with self.subTest(semantic_mutation=case_id):
                result = result_by_id[case_id]
                self.assertFalse(result["actual_valid"])
                self.assertTrue(result["matches_expected"])
                self.assertTrue(
                    any(expected_error in error for error in result["errors"]),
                    result["errors"],
                )
        fixture_by_id = {case["id"]: case for case in self.orchestration_cases}
        self.assertTrue(any(
            "finding-identity" in error
            for error in EVAL._orchestration_case_errors(
                fixture_by_id["dedup-reject-reused-finding-id-after-repair"]
            )
        ))
        self.assertEqual(
            [],
            EVAL._orchestration_case_errors(
                fixture_by_id["dedup-terminal-blocked-review"]
            ),
        )
        blocked_scope_probes = [
            ("reviewed_scope", []),
            ("unreviewed_scope", []),
            ("reviewed_scope", [None]),
            ("unreviewed_scope", [None]),
            ("reviewed_scope", [""]),
            ("unreviewed_scope", [""]),
            ("reviewed_scope", ["   "]),
            ("unreviewed_scope", ["   "]),
            ("reviewed_scope", [1]),
            ("unreviewed_scope", [1]),
        ]
        for case_id, expected_error in (
            ("dedup-terminal-blocked-review", "review-blocked-scope"),
            ("dedup-fail-fast-blocked-scope", "review-fail-fast"),
        ):
            self.assertEqual(
                [], EVAL._orchestration_case_errors(fixture_by_id[case_id])
            )
            for field, value in blocked_scope_probes:
                malformed_scope = copy.deepcopy(fixture_by_id[case_id])
                malformed_scope["events"][-1][field] = value
                with self.subTest(case=case_id, field=field, value=value):
                    self.assertTrue(any(
                        expected_error in error
                        for error in EVAL._orchestration_case_errors(malformed_scope)
                    ))
        self.assertTrue(any(
            "orchestration-terminal" in error
            for error in EVAL._orchestration_case_errors(
                fixture_by_id["dedup-reject-complete-after-blocked-review"]
            )
        ))

        valid = {
            "id": "combined-multi-task",
            "tasks": [
                {"id": "A", "primary_skill": "backend-change-builder", "layer3_skills": [], "review_skills": ["ai-code-review-refactor"]},
                {"id": "B", "primary_skill": "data-middleware-change-builder", "layer3_skills": [], "review_skills": ["quality-test-gate"]},
                {"id": "C", "primary_skill": "security-privacy-gate", "layer3_skills": [], "review_skills": ["security-privacy-gate"]},
            ],
            "review_boundary": {
                "effective_level": "L3",
                "primary_review_skill": "ai-code-review-refactor",
                "required_review_skills": [
                    "ai-code-review-refactor",
                    "quality-test-gate",
                    "security-privacy-gate",
                ],
                "specialist_obligations": ["security"],
                "covered_task_ids": ["A", "B", "C"],
                "required_changed_scope": ["A", "B", "C"],
                "professional_risk_dimensions": ["correctness", "data", "security"],
                "required_validation_evidence_binding": {
                    "generation": "current",
                    "coverage": "covered-task-ids",
                },
            },
            "events": [
                {
                    "action": "analysis",
                    "analysis_kind": "initial",
                    "target_authority": {
                        "desired_behavior": "complete all three accepted tasks",
                        "observable_acceptance": ["all three task validations pass"],
                        "observed_behavior": "one or more task validations may fail",
                        "observed_behavior_role": "failure-evidence-only",
                    },
                    "brief_closed_sections": list(
                        EVAL.CORE_CONTRACTS["task_contract"]
                        ["analyzed_work_authority"]["authoritative_sections"]
                    ),
                    "first_executable_slice": {
                        "task_id": "A",
                        "status": "in_progress",
                        "professional_skill": "backend-change-builder",
                        "layer3_skills": [],
                        "all_required_fields_complete": True,
                    },
                },
                {"action": "edit", "task_id": "A", "generation": 1},
                {"action": "validate", "task_id": "A", "generation": 1, "evidence_id": "v-A"},
                {"action": "edit", "task_id": "B", "generation": 1},
                {"action": "validate", "task_id": "B", "generation": 1, "evidence_id": "v-B"},
                {"action": "edit", "task_id": "C", "generation": 1},
                {"action": "validate", "task_id": "C", "generation": 1, "evidence_id": "v-C"},
                {
                    "action": "review",
                    "covered_task_ids": ["A", "B", "C"],
                    "effective_level": "L3",
                    "review_skills": [
                        "ai-code-review-refactor",
                        "quality-test-gate",
                        "security-privacy-gate",
                    ],
                    "layer3_skills": [],
                    "specialist_obligations": ["security"],
                    "risk_dimensions": ["correctness", "data", "security"],
                    "validation_evidence_ids": ["v-A", "v-B", "v-C"],
                    "independent": True,
                    "verdict": "pass",
                    "review_round_id": "R-ABC-TEST-1",
                    "required_changed_scope_complete": True,
                    "base_dimensions_complete": True,
                    "professional_risk_dimensions_complete": True,
                    "finding_ids": [],
                },
                {"action": "complete"},
            ],
        }
        self.assertEqual([], EVAL._orchestration_case_errors(valid))

        boundary_mutations = {
            "effective_level": "L0",
            "primary_review_skill": [],
            "required_review_skills": [],
            "specialist_obligations": "security",
            "covered_task_ids": [],
            "required_changed_scope": [],
            "professional_risk_dimensions": "correctness",
            "required_validation_evidence_binding": {
                "generation": "previous",
                "coverage": "covered-task-ids",
            },
        }
        for field, invalid_value in boundary_mutations.items():
            for operation in ("remove", "mutate"):
                probe = copy.deepcopy(valid)
                if operation == "remove":
                    del probe["review_boundary"][field]
                else:
                    probe["review_boundary"][field] = invalid_value
                with self.subTest(boundary_field=field, operation=operation):
                    self.assertTrue(EVAL._orchestration_case_errors(probe))

        for category in EVAL.FINDING_RELATION_MODEL["material_current_task_criteria"]:
            unresolved = copy.deepcopy(valid)
            unresolved["events"].insert(
                -1,
                {"action": "finding", "finding_id": f"F-{category}", "task_id": "C", "relation": "current-task", "category": category, "repair_required": True},
            )
            with self.subTest(material_finding=category):
                self.assertTrue(any(
                    "material-finding-repair" in error
                    for error in EVAL._orchestration_case_errors(unresolved)
                ))

        scoped_repair = copy.deepcopy(next(
            case for case in self.orchestration_cases
            if case["id"] == "dedup-scoped-repair-subsumes-final"
        ))
        finding_events = [
            event for event in scoped_repair["events"]
            if event["action"] == "finding"
        ]
        finding_event = finding_events[0]
        repair_event = next(
            event for event in scoped_repair["events"]
            if event["action"] == "repair"
        )
        self.assertEqual(
            {
                event["finding_id"]: event["relation"]
                for event in finding_events
            },
            repair_event["finding_relations"],
        )
        for relation, category in (
            ("adjacent", "adjacent-issue"),
            ("scope-blocker", "acceptance"),
        ):
            invalid_repair = copy.deepcopy(scoped_repair)
            invalid_finding = next(
                event for event in invalid_repair["events"]
                if event["action"] == "finding"
            )
            invalid_repair_event = next(
                event for event in invalid_repair["events"]
                if event["action"] == "repair"
            )
            invalid_finding["relation"] = relation
            invalid_finding["category"] = category
            invalid_finding["repair_required"] = False
            invalid_repair_event["finding_relations"] = {
                invalid_finding["finding_id"]: relation
            }
            with self.subTest(repair_finding_relation=relation):
                self.assertTrue(any(
                    "repair-finding-relation" in error
                    for error in EVAL._orchestration_case_errors(invalid_repair)
                ))
        for field in ("specialist_obligations", "risk_dimensions"):
            missing_obligation = copy.deepcopy(scoped_repair)
            missing_obligation["events"][-2][field] = []
            with self.subTest(scoped_rereview=field):
                self.assertTrue(any(
                    "repair-review-obligation-preservation" in error
                    for error in EVAL._orchestration_case_errors(missing_obligation)
                ))

        delta_case = copy.deepcopy(next(
            case for case in self.orchestration_cases
            if case["id"] == "dedup-protected-delta-preserves-skill"
        ))
        delta_event = next(
            event for event in delta_case["events"]
            if event.get("analysis_kind") == "delta"
        )
        self.assertEqual("preserved", delta_event["delta_impact"]["unlisted"])
        self.assertEqual(
            ["A", "B"], delta_event["delta_impact"]["affected"]["tasks"]
        )

        omitted = copy.deepcopy(delta_case)
        next(
            event for event in omitted["events"]
            if event.get("analysis_kind") == "delta"
        )["delta_impact"]["affected"]["tasks"] = ["A"]
        self.assertTrue(any(
            "delta-impact-exact" in error
            for error in EVAL._orchestration_case_errors(omitted)
        ))

        for update, affected_field in (
            ("affected-brief-sections", "brief"),
            ("affected-tasks", "tasks"),
            ("affected-dependencies", "dependencies"),
            ("affected-review-boundaries", "reviews"),
        ):
            coupled_removal = copy.deepcopy(delta_case)
            coupled_delta = next(
                event for event in coupled_removal["events"]
                if event.get("analysis_kind") == "delta"
            )
            coupled_delta["transitive_updates"].remove(update)
            coupled_delta["delta_impact"]["affected"][affected_field] = []
            with self.subTest(coupled_removal=update):
                self.assertTrue(any(
                    "delta-impact-exact" in error
                    for error in EVAL._orchestration_case_errors(coupled_removal)
                ))

        rerouted = copy.deepcopy(delta_case)
        rerouted_delta = next(
            event for event in rerouted["events"]
            if event.get("analysis_kind") == "delta"
        )
        rerouted_delta["work_type_changed"] = True
        rerouted_delta["skill_assignments"]["B"] = (
            "data-middleware-change-builder"
        )
        rerouted_delta["delta_impact"]["affected"]["skills"] = ["B"]
        self.assertEqual([], EVAL._orchestration_case_errors(rerouted))

        coupled_skill_removal = copy.deepcopy(rerouted)
        coupled_skill_delta = next(
            event for event in coupled_skill_removal["events"]
            if event.get("analysis_kind") == "delta"
        )
        coupled_skill_delta["transitive_updates"].remove(
            "affected-skill-assignments"
        )
        coupled_skill_delta["delta_impact"]["affected"]["skills"] = []
        self.assertTrue(any(
            "delta-impact-exact" in error
            for error in EVAL._orchestration_case_errors(coupled_skill_removal)
        ))

        false_fanout = copy.deepcopy(delta_case)
        next(task for task in false_fanout["tasks"] if task["id"] == "B")[
            "dependencies"
        ] = []
        self.assertTrue(any(
            "delta-impact-exact" in error
            for error in EVAL._orchestration_case_errors(false_fanout)
        ))

        unproved_empty = copy.deepcopy(delta_case)
        delta_index = next(
            index for index, event in enumerate(unproved_empty["events"])
            if event.get("analysis_kind") == "delta"
        )
        unproved_empty["events"] = [
            event
            for index, event in enumerate(unproved_empty["events"])
            if not (
                index < delta_index
                and event.get("action") in {"edit", "validate"}
            )
        ]
        next(
            event for event in unproved_empty["events"]
            if event.get("analysis_kind") == "delta"
        )["delta_impact"]["affected"]["tasks"] = []
        self.assertTrue(any(
            "delta-impact-proof-limit" in error
            for error in EVAL._orchestration_case_errors(unproved_empty)
        ))

        finding_index = next(
            index for index, event in enumerate(scoped_repair["events"])
            if event["action"] == "finding"
        )
        repair_index = next(
            index for index, event in enumerate(scoped_repair["events"])
            if event["action"] == "repair"
        )
        finding_probes = {
            "material-finding-task-missing": ("task_id", None, "material-finding-task"),
            "material-finding-task-unknown": ("task_id", "UNKNOWN", "material-finding-task"),
            "finding-relation": ("relation", "unknown", "finding-relation"),
            "finding-category": ("category", "unknown", "finding-category"),
            "finding-identity": ("finding_id", None, "finding-identity"),
        }
        for name, (field, value, expected) in finding_probes.items():
            probe = copy.deepcopy(scoped_repair)
            if value is None:
                probe["events"][finding_index].pop(field, None)
            else:
                probe["events"][finding_index][field] = value
            with self.subTest(finding_probe=name):
                self.assertTrue(any(
                    expected in error for error in EVAL._orchestration_case_errors(probe)
                ))

        unknown_verdict = copy.deepcopy(valid)
        unknown_verdict["events"][7]["verdict"] = "approved"
        self.assertTrue(any(
            "review-verdict" in error
            for error in EVAL._orchestration_case_errors(unknown_verdict)
        ))

        unresolved_identity = copy.deepcopy(scoped_repair)
        unresolved_identity["events"][repair_index]["resolved_finding_ids"] = []
        self.assertTrue(any(
            "repair-finding-identity" in error
            for error in EVAL._orchestration_case_errors(unresolved_identity)
        ))

        for field in ("affected_specialist_obligations", "affected_risk_dimensions"):
            underdeclared = copy.deepcopy(scoped_repair)
            underdeclared["events"][repair_index][field] = []
            with self.subTest(derived_repair_obligation=field):
                self.assertTrue(any(
                    "repair-review-obligation-binding" in error
                    for error in EVAL._orchestration_case_errors(underdeclared)
                ))

        skill_probes = {
            "task-skill-registry": lambda case: case["tasks"][0].update(primary_skill="unknown-skill"),
            "task-skill-role": lambda case: case["tasks"][0].update(primary_skill="ai-code-review-refactor"),
            "review-skill-routing": lambda case: case["tasks"][1].update(review_skills=["data-middleware-change-builder"]),
            "task-layer3-registry": lambda case: case["tasks"][0].update(layer3_skills=["unknown-layer3"]),
            "task-layer3-routing": lambda case: case["tasks"][0].update(layer3_skills=["targeted-validation-selection"]),
        }
        for expected, mutate in skill_probes.items():
            probe = copy.deepcopy(valid)
            mutate(probe)
            with self.subTest(skill_probe=expected):
                self.assertTrue(any(
                    expected in error for error in EVAL._orchestration_case_errors(probe)
                ))

        merged_task_primary = copy.deepcopy(valid)
        merged_task_primary["tasks"][0]["primary_skill"] = [
            "backend-change-builder", "security-privacy-gate"
        ]
        self.assertTrue(any(
            "task-primary-skill" in error
            for error in EVAL._orchestration_case_errors(merged_task_primary)
        ))

        merged_review_primary = copy.deepcopy(valid)
        merged_review_primary["review_boundary"]["primary_review_skill"] = [
            "ai-code-review-refactor", "quality-test-gate"
        ]
        self.assertTrue(any(
            "review-boundary-primary-skill" in error
            for error in EVAL._orchestration_case_errors(merged_review_primary)
        ))

        too_many_layer3 = copy.deepcopy(valid)
        too_many_layer3["tasks"][0]["layer3_skills"] = [
            "minimal-correct-implementation", "regression-testing",
            "logging-error-handling", "observability",
        ]
        self.assertTrue(any(
            "task-layer3-routing" in error
            for error in EVAL._orchestration_case_errors(too_many_layer3)
        ))

        independent_review_layer3 = copy.deepcopy(valid)
        independent_review_layer3["tasks"][0]["layer3_skills"] = [
            "concurrency-control",
            "idempotency-retry-design",
        ]
        independent_review_layer3["events"][0]["first_executable_slice"][
            "layer3_skills"
        ] = [
            "concurrency-control",
            "idempotency-retry-design",
        ]
        independent_review_layer3["tasks"][0]["review_skills"] = [
            "reliability-observability-gate"
        ]
        independent_review_layer3["review_boundary"][
            "primary_review_skill"
        ] = "reliability-observability-gate"
        independent_review_layer3["review_boundary"][
            "required_review_skills"
        ] = [
            "reliability-observability-gate",
            "quality-test-gate",
            "security-privacy-gate",
        ]
        review_event = independent_review_layer3["events"][7]
        review_event["review_skills"] = [
            "reliability-observability-gate",
            "quality-test-gate",
            "security-privacy-gate",
        ]
        review_event["layer3_skills"] = ["concurrency-control"]
        self.assertEqual(
            [],
            EVAL._orchestration_case_errors(independent_review_layer3),
            "Review Layer3 must be selected independently from review risk, "
            "not copied or unioned from Task implementation Layer3",
        )

        unauthorized_review_layer3 = copy.deepcopy(independent_review_layer3)
        unauthorized_review_layer3["events"][7]["layer3_skills"] = [
            "repository-context-map"
        ]
        self.assertTrue(any(
            "review-layer3-routing" in error
            for error in EVAL._orchestration_case_errors(
                unauthorized_review_layer3
            )
        ))

        altered_layer3 = copy.deepcopy(self.layer3)
        altered_layer3["minimal-correct-implementation"] = copy.deepcopy(
            altered_layer3["minimal-correct-implementation"]
        )
        altered_layer3["minimal-correct-implementation"]["role_support"] = [
            "analysis-agent", "review-agent"
        ]
        unsupported_layer3 = copy.deepcopy(valid)
        unsupported_layer3["tasks"][0]["layer3_skills"] = [
            "minimal-correct-implementation"
        ]
        with patch.object(
            EVAL,
            "_skill_registries",
            return_value=(self.professional, altered_layer3),
        ):
            self.assertTrue(any(
                "task-layer3-role" in error
                for error in EVAL._orchestration_case_errors(unsupported_layer3)
            ))

        runtime_manifest, _manifest_errors = EVAL._load_runtime_manifest()
        assert runtime_manifest is not None
        undelivered = copy.deepcopy(runtime_manifest)
        undelivered["professional_skills"].remove("backend-change-builder")
        with patch.object(EVAL, "_load_runtime_manifest", return_value=(undelivered, [])):
            self.assertTrue(any(
                "skill-built-delivery" in error
                for error in EVAL._orchestration_case_errors(copy.deepcopy(valid))
            ))

        missing_skill = copy.deepcopy(valid)
        missing_skill["events"][7]["review_skills"].remove("security-privacy-gate")
        self.assertTrue(
            any(
                "review-skill-preservation" in error
                for error in EVAL._orchestration_case_errors(missing_skill)
            )
        )

    def test_review_convergence_complete_pass_batches_all_same_task_findings(self) -> None:
        case = self._review_convergence_case()

        errors, trace = EVAL._orchestration_case_result(case)

        self.assertEqual([], errors)
        self.assertEqual(1, trace["repair_flow"]["repair_count"])
        self.assertEqual(
            ["F-C-A", "F-C-B"],
            trace["repair_flow"]["resolved_finding_ids"],
        )
        self.assertEqual([["R-C-1", "C"]], trace["repair_flow"]["batch_keys"])
        self.assertEqual(["C"], trace["repair_flow"]["fresh_validation_task_ids"])
        self.assertEqual(["C"], trace["repair_flow"]["rereviewed_task_ids"])
        initial_review = next(
            event for event in case["events"] if event["action"] == "review"
        )
        self.assertTrue(initial_review["required_changed_scope_complete"])
        self.assertTrue(initial_review["base_dimensions_complete"])
        self.assertTrue(initial_review["professional_risk_dimensions_complete"])
        rereview = next(
            event for event in case["events"] if event["action"] == "re-review"
        )
        self.assertEqual(list(EVAL.REREVIEW_CHECKS), rereview["rereview_checks"])
        self.assertFalse(rereview["rereview_scope_expanded"])
        self.assertTrue(trace["completion"]["current_evidence"])

    def test_rereview_finding_creates_a_second_same_task_repair_round(self) -> None:
        case = self._review_convergence_case()
        case["id"] = "review-convergence-second-repair"
        events = case["events"]
        second_review_index = next(
            index
            for index, event in enumerate(events)
            if event["action"] == "re-review"
        )
        second_review = events[second_review_index]
        finding = {
            "action": "finding",
            "finding_id": "F-C-C",
            "task_id": "C",
            "review_round_id": "R-C-2",
            "relation": "current-task",
            "rereview_classification": "repair-regression",
            "classification_evidence": "repair diff regresses correctness",
            "category": "correctness-or-invariant",
            "impact_dimensions": ["correctness"],
            "repair_required": True,
            "affected_scope": ["C"],
            "acceptance_or_risk_impact": "correctness",
            "required_validation": ["current-generation-scoped-validation"],
            "required_covering_rereview": {
                "covered_task_ids": ["C"],
                "same_or_stronger": True,
            },
        }
        events.insert(second_review_index, finding)
        second_review.update(verdict="findings", finding_ids=["F-C-C"])
        events[-1:-1] = [
            {
                "action": "repair",
                "task_id": "C",
                "generation": 3,
                "affected_task_ids": ["C"],
                "resolved_finding_ids": ["F-C-C"],
                "finding_relations": {"F-C-C": "current-task"},
                "impact_boundaries": [],
                "affected_specialist_obligations": [],
                "affected_risk_dimensions": ["correctness"],
                "invalidated_claims": ["validation:C", "review:C"],
                "review_round_id": "R-C-2",
                "finding_obligations": [
                    {
                        "finding_id": "F-C-C",
                        "relation": "current-task",
                        "affected_scope": ["C"],
                        "acceptance_or_risk_impact": "correctness",
                        "required_validation": [
                            "current-generation-scoped-validation"
                        ],
                        "required_covering_rereview": {
                            "covered_task_ids": ["C"],
                            "same_or_stronger": True,
                        },
                    }
                ],
            },
            {
                "action": "validate",
                "task_id": "C",
                "generation": 3,
                "evidence_id": "v-C3",
            },
            {
                **copy.deepcopy(second_review),
                "evidence_id": "r-C3",
                "verdict": "pass",
                "review_round_id": "R-C-3",
                "validation_evidence_ids": ["v-C3"],
                "finding_ids": [],
            },
        ]

        errors, trace = EVAL._orchestration_case_result(case)

        self.assertEqual([], errors)
        self.assertEqual(2, trace["repair_flow"]["repair_count"])
        self.assertEqual({"C": 2}, trace["repair_flow"]["repair_counts_by_task"])
        self.assertEqual({"C": "within-budget"}, trace["repair_flow"]["cap_dispositions"])
        self.assertEqual(
            [["R-C-1", "C"], ["R-C-2", "C"]],
            trace["repair_flow"]["batch_keys"],
        )
        self.assertEqual(
            ["review", "re-review", "re-review"], trace["review"]["actions"]
        )
        self.assertTrue(trace["completion"]["current_evidence"])

        third = copy.deepcopy(case)
        third["id"] = "review-convergence-third-repair-rejected"
        final_review_index = max(
            index
            for index, event in enumerate(third["events"])
            if event.get("action") == "re-review"
        )
        final_review = third["events"][final_review_index]
        third_finding = {
            "action": "finding",
            "finding_id": "F-C-D",
            "task_id": "C",
            "review_round_id": final_review["review_round_id"],
            "relation": "current-task",
            "rereview_classification": "repair-regression",
            "classification_evidence": "second repair regresses security",
            "category": "security-or-reliability",
            "impact_dimensions": ["security"],
            "repair_required": True,
            "affected_scope": ["C"],
            "acceptance_or_risk_impact": "security",
            "required_validation": ["current-generation-scoped-validation"],
            "required_covering_rereview": {
                "covered_task_ids": ["C"],
                "same_or_stronger": True,
            },
        }
        third["events"].insert(final_review_index, third_finding)
        final_review = third["events"][final_review_index + 1]
        final_review.update(verdict="findings", finding_ids=["F-C-D"])
        capped = copy.deepcopy(third)
        capped["id"] = "review-convergence-cap-blocks-security-defect"
        capped["events"][-1] = {
            "action": "blocked",
            "task_id": "C",
            "reason": "repair-round-limit-non-converged",
            "reviewed_scope": ["C repair diff and affected dependents"],
            "unreviewed_scope": ["unresolved security blocker F-C-D"],
        }
        capped_errors, capped_trace = EVAL._orchestration_case_result(capped)
        self.assertEqual([], capped_errors)
        self.assertEqual("blocked", capped_trace["completion"]["state"])
        self.assertEqual(
            "blocked-non-converged",
            capped_trace["repair_flow"]["cap_dispositions"]["C"],
        )

        third["events"].insert(
            final_review_index + 2,
            {
                "action": "repair",
                "task_id": "C",
                "generation": 4,
                "affected_task_ids": ["C"],
                "resolved_finding_ids": ["F-C-D"],
                "finding_relations": {"F-C-D": "current-task"},
                "impact_boundaries": [],
                "affected_specialist_obligations": ["security"],
                "affected_risk_dimensions": ["security"],
                "invalidated_claims": ["validation:C", "review:C"],
                "review_round_id": final_review["review_round_id"],
                "finding_obligations": [
                    {
                        "finding_id": "F-C-D",
                        "relation": "current-task",
                        "affected_scope": ["C"],
                        "acceptance_or_risk_impact": "security",
                        "required_validation": [
                            "current-generation-scoped-validation"
                        ],
                        "required_covering_rereview": {
                            "covered_task_ids": ["C"],
                            "same_or_stronger": True,
                        },
                    }
                ],
            },
        )
        third_errors = EVAL._orchestration_case_errors(third)
        self.assertTrue(
            any("repair-round-cap" in error for error in third_errors),
            third_errors,
        )

    def test_rereview_requires_focused_frozen_boundary_checks(self) -> None:
        case = self._review_convergence_case()
        rereview = next(
            event for event in case["events"] if event["action"] == "re-review"
        )
        rereview.pop("rereview_checks")
        errors = EVAL._orchestration_case_errors(case)
        self.assertTrue(any("rereview-focus" in error for error in errors), errors)

    def test_rereview_uses_focused_completion_without_reopening_initial_scope(
        self,
    ) -> None:
        case = self._review_convergence_case()
        rereview = next(
            event for event in case["events"] if event["action"] == "re-review"
        )
        for field in (
            "required_changed_scope_complete",
            "base_dimensions_complete",
            "professional_risk_dimensions_complete",
        ):
            rereview.pop(field, None)
        rereview["frozen_professional_risk_boundary_status"] = "preserved"
        self.assertEqual([], EVAL._orchestration_case_errors(case))

        weakened_initial = self._review_convergence_case()
        initial_review = next(
            event for event in weakened_initial["events"]
            if event["action"] == "review"
        )
        initial_review.pop("professional_risk_dimensions_complete")
        errors = EVAL._orchestration_case_errors(weakened_initial)
        self.assertTrue(any("review-complete-pass" in error for error in errors), errors)

        invalid_frozen_risk = self._review_convergence_case()
        invalid_rereview = next(
            event for event in invalid_frozen_risk["events"]
            if event["action"] == "re-review"
        )
        invalid_rereview["frozen_professional_risk_boundary_status"] = "invalidated"
        errors = EVAL._orchestration_case_errors(invalid_frozen_risk)
        self.assertTrue(any("rereview-focus" in error for error in errors), errors)

    def test_rereview_scope_blocker_closes_round_then_routes_delta_without_repair(
        self,
    ) -> None:
        case = self._review_convergence_case()
        case["id"] = "review-convergence-rereview-scope-blocker"
        events = case["events"]
        second_review_index = next(
            index
            for index, event in enumerate(events)
            if event["action"] == "re-review"
        )
        scope_finding = {
            "action": "finding",
            "finding_id": "F-C-SCOPE-R2",
            "task_id": "C",
            "review_round_id": "R-C-2",
            "relation": "scope-blocker",
            "rereview_classification": "protected-invalidation",
            "classification_evidence": "current evidence invalidates Acceptance",
            "category": "acceptance",
            "repair_required": False,
        }
        events.insert(second_review_index, scope_finding)
        events[second_review_index + 1].update(
            verdict="findings",
            finding_ids=["F-C-SCOPE-R2"],
            frozen_boundary_status="preserved",
        )
        events[-1:-1] = [
            {
                "action": "analysis",
                "analysis_kind": "delta",
                "protected_decision_invalidated": True,
                "invalidated_decisions": ["scope-blocker"],
                "transitive_updates": [
                    "affected-brief-sections",
                    "affected-tasks",
                    "affected-review-boundaries",
                ],
                "analysis_scope": "delta",
                "path_change_evidence": {
                    "changed-hypothesis": False,
                    "changed-material": True,
                    "changed-gap": False,
                    "changed-transition": False,
                },
                "professional_domain_changed": False,
                "work_type_changed": False,
                "material_risk_trigger_changed": False,
                "skill_assignments": {
                    task["id"]: task["primary_skill"] for task in case["tasks"]
                },
                "delta_impact": {
                    "invalidated": ["scope-blocker"],
                    "affected": {
                        "brief": [
                            "Acceptance and Non-goals",
                            "Ownership and Invariants",
                            "Placement and Reuse",
                            "Contract / Data / Failure Impact",
                        ],
                        "tasks": ["C"],
                        "dependencies": [],
                        "skills": [],
                        "reviews": ["security-privacy-gate"],
                    },
                    "unlisted": "preserved",
                },
            }
        ]

        errors = EVAL._orchestration_case_errors(case)
        self.assertTrue(
            any("rereview-protected-invalidation" in error for error in errors),
            errors,
        )

        rereview = next(
            event for event in case["events"] if event["action"] == "re-review"
        )
        rereview["frozen_boundary_status"] = "invalidated"
        errors = EVAL._orchestration_case_errors(case)
        self.assertTrue(
            any("completion-current-evidence" in error for error in errors),
            errors,
        )

        case["events"].pop()
        case["events"].extend(
            [
                {"action": "edit", "task_id": "C", "generation": 3},
                {
                    "action": "validate",
                    "task_id": "C",
                    "generation": 3,
                    "evidence_id": "v-C-post-delta",
                },
            ]
        )
        case["events"].extend(
            [
                {
                    **copy.deepcopy(rereview),
                    "frozen_boundary_status": "preserved",
                    "frozen_professional_risk_boundary_status": "preserved",
                    "evidence_id": "r-ABC-post-delta",
                    "covered_task_ids": ["C"],
                    "review_skills": ["security-privacy-gate"],
                    "specialist_obligations": ["security"],
                    "risk_dimensions": ["correctness", "security"],
                    "validation_evidence_ids": ["v-C-post-delta"],
                    "verdict": "pass",
                    "review_round_id": "R-ABC-POST-DELTA",
                    "finding_ids": [],
                },
                {"action": "complete"},
            ]
        )
        errors, trace = EVAL._orchestration_case_result(case)
        self.assertEqual([], errors)
        self.assertEqual(["F-C-SCOPE-R2"], trace["finding_routes"]["scope_blocker"])
        self.assertEqual(1, trace["repair_flow"]["repair_count"])
        self.assertEqual(["initial", "delta"], trace["analysis"]["kinds"])

    def test_rereview_classification_fields_fail_closed_and_initial_is_optional(
        self,
    ) -> None:
        valid = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "review-convergence-second-repair"
            )
        )
        valid.pop("retained_semantics", None)
        self.assertEqual([], EVAL._orchestration_case_errors(valid))
        finding = next(
            event
            for event in valid["events"]
            if event.get("rereview_classification") == "repair-regression"
        )

        for field, expected in (
            ("rereview_classification", "rereview-finding-classification"),
            ("classification_evidence", "rereview-classification-evidence"),
        ):
            with self.subTest(missing=field):
                probe = copy.deepcopy(valid)
                next(
                    event
                    for event in probe["events"]
                    if event.get("finding_id") == finding["finding_id"]
                ).pop(field)
                errors = EVAL._orchestration_case_errors(probe)
                self.assertTrue(any(expected in error for error in errors), errors)

        frozen = copy.deepcopy(valid)
        frozen_finding = next(
            event
            for event in frozen["events"]
            if event.get("finding_id") == finding["finding_id"]
        )
        frozen_finding["rereview_classification"] = "frozen-boundary-violation"
        frozen_finding.pop("classification_evidence")
        next(
            event
            for event in frozen["events"]
            if event.get("action") == "re-review"
            and event.get("review_round_id") == frozen_finding["review_round_id"]
        )["frozen_boundary_status"] = "violation"
        errors = EVAL._orchestration_case_errors(frozen)
        self.assertTrue(
            any("rereview-frozen-boundary-evidence" in error for error in errors),
            errors,
        )
        frozen_finding["classification_evidence"] = (
            "the repair diff violates the frozen accepted contract"
        )
        self.assertEqual([], EVAL._orchestration_case_errors(frozen))
        frozen_review = next(
            event
            for event in frozen["events"]
            if event.get("action") == "re-review"
            and event.get("review_round_id") == frozen_finding["review_round_id"]
        )
        frozen_review["frozen_boundary_status"] = "preserved"
        errors = EVAL._orchestration_case_errors(frozen)
        self.assertTrue(
            any("rereview-frozen-boundary-violation" in error for error in errors),
            errors,
        )

        preserved_review = next(
            event
            for event in valid["events"]
            if event.get("action") == "re-review"
            and event.get("review_round_id") == finding["review_round_id"]
        )
        self.assertEqual("preserved", preserved_review["frozen_boundary_status"])
        self.assertEqual([], EVAL._orchestration_case_errors(valid))

        initial = self._review_convergence_case()
        initial_finding = next(
            event
            for event in initial["events"]
            if event.get("action") == "finding"
        )
        self.assertNotIn("rereview_classification", initial_finding)
        self.assertEqual([], EVAL._orchestration_case_errors(initial))
        initial_finding["rereview_classification"] = "not-applicable"
        self.assertEqual([], EVAL._orchestration_case_errors(initial))
        initial_finding["rereview_classification"] = "inherited"
        errors = EVAL._orchestration_case_errors(initial)
        self.assertTrue(
            any("initial-review-classification" in error for error in errors),
            errors,
        )

    def test_repeated_review_delta_without_path_change_blocks_after_two(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "review-convergence-rereview-scope-blocker"
            )
        )
        case["id"] = "review-delta-two-unchanged-blocked"
        case.pop("retained_semantics", None)
        first_delta = next(
            event
            for event in case["events"]
            if event.get("analysis_kind") == "delta"
        )
        no_change = {
            "changed-hypothesis": False,
            "changed-material": False,
            "changed-gap": False,
            "changed-transition": False,
        }
        first_delta["path_change_evidence"] = copy.deepcopy(no_change)
        case["events"].pop()
        case["events"].pop()
        second_round = "R-C-3"
        case["events"].extend(
            [
                {
                    "action": "finding",
                    "finding_id": "F-C-SCOPE-R3",
                    "task_id": "C",
                    "review_round_id": second_round,
                    "relation": "scope-blocker",
                    "rereview_classification": "protected-invalidation",
                    "classification_evidence": "protected decision remains invalidated",
                    "category": "acceptance",
                    "repair_required": False,
                },
                {
                    **copy.deepcopy(
                        next(
                            event
                            for event in case["events"]
                            if event.get("action") == "re-review"
                        )
                    ),
                    "evidence_id": "r-C3-protected",
                    "review_round_id": second_round,
                    "finding_ids": ["F-C-SCOPE-R3"],
                    "frozen_boundary_status": "invalidated",
                    "validation_evidence_ids": ["v-C3-post-delta"],
                },
                {
                    **copy.deepcopy(first_delta),
                    "path_change_evidence": copy.deepcopy(no_change),
                    "delta_impact": {
                        **copy.deepcopy(first_delta["delta_impact"]),
                        "affected": {
                            **copy.deepcopy(
                                first_delta["delta_impact"]["affected"]
                            ),
                            "tasks": ["C"],
                            "reviews": ["security-privacy-gate"],
                        },
                    },
                },
                {
                    "action": "blocked",
                    "task_id": "C",
                    "reason": "review-delta-same-path-non-converged",
                    "reviewed_scope": ["two protected invalidations"],
                    "unreviewed_scope": ["no changed implementation path"],
                },
            ]
        )

        errors, trace = EVAL._orchestration_case_result(case)

        self.assertEqual([], errors)
        self.assertEqual("blocked", trace["completion"]["state"])
        self.assertEqual(2, trace["analysis"]["same_path_failures_by_task"]["C"])
        self.assertEqual(2, len(trace["analysis"]["review_delta_path_changes"]))

    def test_post_dispatch_blocked_review_requires_narrow_reason_and_proof(self) -> None:
        fixture = {
            "id": "post-dispatch-blocked-review",
            "expected_valid": True,
            "expected_error": None,
            "level": "L3",
            "mutation": {"kind": "none"},
        }
        for reason in (
            "required-review-evidence-or-surface-unavailable",
            "required-current-evidence-stale",
            "protected-authority-or-engineering-brief-invalidated",
        ):
            with self.subTest(reason=reason):
                steps = EVAL._review_fixture_steps(fixture)
                discipline = next(
                    step
                    for step in steps
                    if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
                )
                closing = next(
                    step
                    for step in steps
                    if step.get("actor") == "review-agent"
                    and step.get("action") == "review"
                )
                discipline["verdict"] = "blocked"
                discipline["dimensions"]["unverified-scope"] = "blocked"
                closing.update(
                    reason=reason,
                    reviewed_scope=["owner.py"],
                    unreviewed_scope=["required current review evidence"],
                    proof_limit="review cannot prove the unreviewed required surface",
                )
                if reason == "required-review-evidence-or-surface-unavailable":
                    discipline["diff"] = {
                        "kind": "unavailable",
                        "artifact": None,
                        "generation": None,
                        "changed_files": [],
                    }
                    discipline["evidence_source"] = "unavailable"
                    closing["changed_paths"] = []
                elif reason == "required-current-evidence-stale":
                    discipline["validation"]["generation"] = 0
                else:
                    closing["invalidated_decisions"] = [
                        "Engineering Brief: Acceptance and Non-goals"
                    ]

                self.assertEqual(
                    [], EVAL._review_discipline_errors(fixture["id"], steps)
                )

                missing_proof = copy.deepcopy(steps)
                next(
                    step
                    for step in missing_proof
                    if step.get("actor") == "review-agent"
                    and step.get("action") == "review"
                )["proof_limit"] = ""
                self.assertTrue(
                    any(
                        "review-post-dispatch-block" in error
                        for error in EVAL._review_discipline_errors(
                            fixture["id"], missing_proof
                        )
                    )
                )

    def test_post_dispatch_unavailable_uses_proven_readiness_snapshot(self) -> None:
        fixture = {
            "id": "post-dispatch-unavailable-snapshot",
            "expected_valid": True,
            "expected_error": None,
            "level": "L3",
            "mutation": {"kind": "none"},
        }

        artifact_unavailable = EVAL._review_fixture_steps(fixture)
        discipline = next(
            step
            for step in artifact_unavailable
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        closing = next(
            step
            for step in artifact_unavailable
            if step.get("actor") == "review-agent"
            and step.get("action") == "review"
        )
        dispatch_index = next(
            index
            for index, step in enumerate(artifact_unavailable)
            if step.get("action") == "dispatch"
            and step.get("profile") == "review-agent"
        )
        artifact_unavailable[:] = [
            step
            for index, step in enumerate(artifact_unavailable)
            if not (
                index > dispatch_index
                and step.get("actor") == "review-agent"
                and step.get("action") == "read"
            )
        ]
        discipline["verdict"] = "blocked"
        discipline["dimensions"]["unverified-scope"] = "blocked"
        discipline["diff"] = {
            "kind": "unavailable",
            "artifact": None,
            "generation": None,
            "changed_files": [],
        }
        discipline["evidence_source"] = "unavailable"
        closing.update(
            reason="required-review-evidence-or-surface-unavailable",
            reviewed_scope=["owner.py"],
            unreviewed_scope=["dispatched exact change artifact"],
            proof_limit="artifact became unavailable after dispatch before first read",
            changed_paths=[],
        )
        self.assertEqual(
            [], EVAL._review_discipline_errors(fixture["id"], artifact_unavailable)
        )

        validation_unavailable = EVAL._review_fixture_steps(fixture)
        discipline = next(
            step
            for step in validation_unavailable
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        closing = next(
            step
            for step in validation_unavailable
            if step.get("actor") == "review-agent"
            and step.get("action") == "review"
        )
        discipline["verdict"] = "blocked"
        discipline["dimensions"]["unverified-scope"] = "blocked"
        discipline["validation"].update(
            source="unavailable",
            evidence_id=None,
            result="unavailable",
            generation=None,
        )
        closing.update(
            reason="required-review-evidence-or-surface-unavailable",
            reviewed_scope=["owner.py"],
            unreviewed_scope=["required current validation"],
            proof_limit="current validation became unavailable after readiness",
        )
        self.assertEqual(
            [], EVAL._review_discipline_errors(fixture["id"], validation_unavailable)
        )

        pre_dispatch_unavailable = EVAL._review_fixture_steps(fixture)
        handoff = next(
            step
            for step in pre_dispatch_unavailable
            if step.get("action") == EVAL.IMPLEMENTATION_HANDOFF_ACTION
        )
        handoff["exact_change_evidence"]["artifact"] = None
        errors = EVAL._review_discipline_errors(
            fixture["id"], pre_dispatch_unavailable
        )
        self.assertTrue(
            any(
                code in error
                for error in errors
                for code in (
                    "review-input-evidence-payload",
                    "review-input-dispatch-before-ready",
                )
            ),
            errors,
        )

        false_unavailable = EVAL._review_fixture_steps(fixture)
        discipline = next(
            step
            for step in false_unavailable
            if step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
        )
        closing = next(
            step
            for step in false_unavailable
            if step.get("actor") == "review-agent"
            and step.get("action") == "review"
        )
        discipline["verdict"] = "blocked"
        discipline["dimensions"]["unverified-scope"] = "blocked"
        closing.update(
            reason="required-review-evidence-or-surface-unavailable",
            reviewed_scope=["owner.py"],
            unreviewed_scope=["claimed unavailable evidence"],
            proof_limit="the claimed unavailable evidence would bound proof",
        )
        errors = EVAL._review_discipline_errors(fixture["id"], false_unavailable)
        self.assertTrue(
            any("review-post-dispatch-block" in error for error in errors), errors
        )

    def test_progress_policy_enforces_two_repair_rounds_per_task(self) -> None:
        for cycle_count, expected_valid in ((2, True), (3, False)):
            with self.subTest(cycle_count=cycle_count):
                case_id = f"unbounded-repair-progress-{cycle_count}"
                steps = [
                    {
                        "actor": "main-control-agent",
                        "action": "progress",
                        "checkpoint_type": "start/path",
                        "evidence": "accepted repair path selected",
                        "evidence_anchor": f"fixture:{case_id}:path",
                    },
                    {
                        "actor": "main-control-agent",
                        "action": "dispatch",
                        "task_id": "repair-task",
                        "batch_id": "repair-task",
                    },
                    {
                        "actor": "main-control-agent",
                        "action": "progress",
                        "checkpoint_type": "dispatch/batch",
                        "evidence": "repair batch dispatched",
                        "evidence_anchor": "batch:repair-task",
                    },
                ]
                for cycle in range(1, cycle_count + 1):
                    evidence_id = f"repair-validation-{cycle}"
                    steps.extend(
                        [
                            {
                                "actor": "task-agent",
                                "action": "repair",
                                "task_id": "repair-task",
                            },
                            {
                                "actor": "task-agent",
                                "action": "validate",
                                "evidence_id": evidence_id,
                                "outcome": "passed",
                            },
                            {
                                "actor": "main-control-agent",
                                "action": "progress",
                                "checkpoint_type": "validation",
                                "evidence": f"repair cycle {cycle} validation passed",
                                "evidence_anchor": f"validation:{evidence_id}:passed",
                            },
                            {
                                "actor": "review-agent",
                                "action": "re-review",
                                "evidence_id": f"repair-review-{cycle}",
                                "outcome": "findings",
                            },
                        ]
                    )
                steps.append({"actor": "main-control-agent", "action": "close"})

                errors = EVAL._progress_errors(case_id, steps)
                if expected_valid:
                    self.assertEqual([], errors)
                else:
                    self.assertTrue(
                        any("repair-round-cap" in error for error in errors),
                        errors,
                    )
                metrics = EVAL._progress_metrics(
                    {"id": case_id, "risk": "high"}, steps
                )
                self.assertTrue(
                    metrics["required_multi_agent_progress_satisfied"], metrics
                )

    def test_repair_budget_is_independent_by_task_and_survives_delta(self) -> None:
        steps = [
            {"actor": "task-agent", "action": "repair", "task_id": "A"},
            {
                "actor": "analysis-agent",
                "action": "analysis",
                "analysis_kind": "delta",
            },
            {"actor": "task-agent", "action": "repair", "task_id": "A"},
            {"actor": "task-agent", "action": "repair", "task_id": "B"},
            {
                "actor": "review-agent",
                "action": "re-review",
                "review_round_id": "R-new-boundary",
            },
            {"actor": "task-agent", "action": "repair", "task_id": "B"},
        ]
        errors = EVAL._progress_errors("per-task-repair-budget", steps)
        self.assertFalse(
            any("repair-round-cap" in error for error in errors), errors
        )

        third_a = copy.deepcopy(steps)
        third_a.append(
            {"actor": "task-agent", "action": "repair", "task_id": "A"}
        )
        cap_errors = [
            error
            for error in EVAL._progress_errors(
                "per-task-repair-budget-third-a", third_a
            )
            if "repair-round-cap" in error
        ]
        self.assertEqual(1, len(cap_errors), cap_errors)
        self.assertIn("Task ID 'A'", cap_errors[0])

    def test_review_input_ready_missing_each_fact_dispatches_zero_reviewers(self) -> None:
        base = copy.deepcopy(
            next(
                case
                for case in self.task_focus_cases
                if case["id"] == "focus-review-ready-dispatch-once"
            )
        )
        mutations = {
            "latest-changed-paths": lambda inputs: inputs.update(
                latest_changed_paths=False
            ),
            "exact-change-evidence": lambda inputs: inputs.update(
                change_evidence_kind="unavailable"
            ),
            "post-latest-edit-validation": lambda inputs: inputs.update(
                validation_generation=inputs["latest_material_edit_generation"] - 1
            ),
            "fixed-review-scope": lambda inputs: inputs.update(
                review_scope_fixed=False
            ),
            "reviewer-artifact-readability": lambda inputs: inputs[
                "reviewer_artifact_accessibility"
            ].update(readable=False),
        }
        for name, mutate in mutations.items():
            negative = copy.deepcopy(base)
            negative["id"] = f"focus-review-missing-{name}"
            mutate(negative["inputs"])
            negative["decision"] = {
                "review_input_ready": False,
                "review_dispatches": 0,
                "completion": "blocked-before-review",
            }
            with self.subTest(missing=name):
                self.assertEqual([], EVAL._task_focus_case_errors(negative))

    def test_post_dispatch_authority_invalidation_routes_main_delta_analysis(
        self,
    ) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "dedup-terminal-blocked-review"
            )
        )
        case["id"] = "review-post-dispatch-authority-delta"
        case.pop("retained_semantics", None)
        blocked = next(
            event for event in case["events"] if event["action"] == "review"
        )
        blocked.update(
            reason="protected-authority-or-engineering-brief-invalidated",
            proof_limit="current evidence invalidates protected Acceptance",
            invalidated_decisions=["Acceptance-or-Non-goals"],
        )
        case["events"].append(
            {
                "action": "analysis",
                "analysis_kind": "delta",
                "protected_decision_invalidated": True,
                "invalidated_decisions": ["Acceptance-or-Non-goals"],
                "transitive_updates": [
                    "affected-brief-sections",
                    "affected-tasks",
                    "affected-review-boundaries",
                ],
                "analysis_scope": "delta",
                "path_change_evidence": {
                    "changed-hypothesis": False,
                    "changed-material": True,
                    "changed-gap": False,
                    "changed-transition": False,
                },
                "professional_domain_changed": False,
                "work_type_changed": False,
                "material_risk_trigger_changed": False,
                "skill_assignments": {"A": "backend-change-builder"},
                "delta_impact": {
                    "invalidated": ["Acceptance-or-Non-goals"],
                    "affected": {
                        "brief": ["Acceptance and Non-goals"],
                        "tasks": ["A"],
                        "dependencies": [],
                        "skills": [],
                        "reviews": ["ai-code-review-refactor"],
                    },
                    "unlisted": "preserved",
                },
            }
        )

        self.assertEqual([], EVAL._orchestration_case_errors(case))

        missing_route = copy.deepcopy(case)
        missing_route["events"].pop()
        self.assertTrue(
            any(
                "[review-authority-route]" in error
                for error in EVAL._orchestration_case_errors(missing_route)
            )
        )

    def test_repair_batch_identity_is_structural_for_delimiter_bearing_ids(
        self,
    ) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "review-repair-structural-batch-key-collision"
            )
        )

        errors, trace = EVAL._orchestration_case_result(case)

        self.assertEqual([], errors)
        self.assertEqual(
            [["R", "A:B"], ["R:A", "B"]],
            trace["repair_flow"]["batch_keys"],
        )

        duplicate = copy.deepcopy(self._review_convergence_case())
        duplicate.pop("retained_semantics", None)
        repair_index = next(
            index
            for index, event in enumerate(duplicate["events"])
            if event["action"] == "repair"
        )
        repeated = copy.deepcopy(duplicate["events"][repair_index])
        repeated["generation"] = 3
        duplicate["events"].insert(repair_index + 1, repeated)
        duplicate_errors = EVAL._orchestration_case_errors(duplicate)
        self.assertTrue(
            any("[repair-batch-cardinality]" in error for error in duplicate_errors),
            duplicate_errors,
        )

    def test_review_convergence_negative_controls_reject_batch_drift(self) -> None:
        def merge_cross_task(case: dict) -> None:
            review = next(
                event for event in case["events"] if event["action"] == "review"
            )
            finding = copy.deepcopy(
                next(
                    event
                    for event in case["events"]
                    if event.get("finding_id") == "F-C-A"
                )
            )
            finding.update(
                {
                    "finding_id": "F-B-X",
                    "task_id": "B",
                    "affected_scope": ["B"],
                    "required_covering_rereview": {
                        "covered_task_ids": ["B"],
                        "same_or_stronger": True,
                    },
                }
            )
            case["events"].insert(case["events"].index(review), finding)
            review["finding_ids"].insert(0, "F-B-X")
            repair = next(
                event for event in case["events"] if event["action"] == "repair"
            )
            repair["resolved_finding_ids"].insert(0, "F-B-X")
            repair["finding_relations"] = {
                "F-B-X": "current-task",
                **repair["finding_relations"],
            }
            repair["finding_obligations"].insert(
                0,
                {
                    "finding_id": finding["finding_id"],
                    "relation": finding["relation"],
                    "affected_scope": finding["affected_scope"],
                    "acceptance_or_risk_impact": finding[
                        "acceptance_or_risk_impact"
                    ],
                    "required_validation": finding["required_validation"],
                    "required_covering_rereview": finding[
                        "required_covering_rereview"
                    ],
                },
            )

        def remove_review_field(case: dict, field: str) -> None:
            next(
                event for event in case["events"] if event["action"] == "review"
            ).pop(field)

        def remove_finding_obligation_field(case: dict, field: str) -> None:
            repair = next(
                event for event in case["events"] if event["action"] == "repair"
            )
            repair["finding_obligations"][0].pop(field)

        mutations: dict[str, tuple[str, object]] = {
            "missing-review-round": (
                "review-complete-pass",
                lambda case: remove_review_field(case, "review_round_id"),
            ),
            "missing-required-scope-complete": (
                "review-complete-pass",
                lambda case: remove_review_field(
                    case, "required_changed_scope_complete"
                ),
            ),
            "missing-base-dimensions-complete": (
                "review-complete-pass",
                lambda case: remove_review_field(case, "base_dimensions_complete"),
            ),
            "missing-risk-dimensions-complete": (
                "review-complete-pass",
                lambda case: remove_review_field(
                    case, "professional_risk_dimensions_complete"
                ),
            ),
            "missing-review-finding-membership": (
                "review-complete-pass",
                lambda case: remove_review_field(case, "finding_ids"),
            ),
            "dropped-finding": (
                "repair-batch-completeness",
                lambda case: next(
                    event for event in case["events"] if event["action"] == "repair"
                )["resolved_finding_ids"].remove("F-C-B"),
            ),
            "split-repair": (
                "repair-batch-cardinality",
                lambda case: next(
                    event for event in case["events"] if event["action"] == "repair"
                ).update(repair_batch_count=2),
            ),
            "changed-task-id": (
                "repair-task-id-continuity",
                lambda case: next(
                    event for event in case["events"] if event["action"] == "repair"
                ).update(task_id="B"),
            ),
            "cross-task-merge": (
                "repair-cross-task-batch",
                merge_cross_task,
            ),
            "lost-finding-obligation": (
                "repair-finding-obligation",
                lambda case: next(
                    event for event in case["events"] if event["action"] == "repair"
                )["finding_obligations"].pop(),
            ),
            **{
                f"lost-finding-{field}": (
                    "repair-finding-obligation",
                    lambda case, field=field: remove_finding_obligation_field(
                        case, field
                    ),
                )
                for field in (
                    "relation",
                    "affected_scope",
                    "acceptance_or_risk_impact",
                    "required_validation",
                    "required_covering_rereview",
                )
            },
            "stale-validation": (
                "review-validation-binding",
                lambda case: next(
                    event
                    for event in case["events"]
                    if event["action"] == "re-review"
                ).update(validation_evidence_ids=["v-C1"]),
            ),
            "stale-rereview": (
                "repair-rereview-freshness",
                lambda case: next(
                    event
                    for event in case["events"]
                    if event["action"] == "re-review"
                ).update(review_round_id="R-C-1"),
            ),
        }
        for name, (code, mutate) in mutations.items():
            with self.subTest(mutation=name):
                case = self._review_convergence_case()
                mutate(case)
                errors = EVAL._orchestration_case_errors(case)
                self.assertTrue(any(f"[{code}]" in error for error in errors), errors)

    def test_review_convergence_rejects_pass_without_complete_boundary(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "dedup-direct-work-zero-analysis"
            )
        )
        case.pop("retained_semantics", None)
        next(
            event for event in case["events"] if event["action"] == "review"
        ).pop("required_changed_scope_complete")

        errors = EVAL._orchestration_case_errors(case)

        self.assertTrue(
            any("[review-complete-pass]" in error for error in errors), errors
        )

    def test_review_convergence_rejects_duplicate_canonical_repair_dispatch(self) -> None:
        case = self._release_case("repair-and-rereview")
        repair_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("action") == "dispatch"
            and step.get("mode") == "repair"
            and step.get("finding_ids")
        )
        case["steps"].insert(repair_index + 1, copy.deepcopy(case["steps"][repair_index]))

        errors = EVAL._profile_errors(
            case["id"], case["steps"], self.professional, self.layer3
        )

        self.assertTrue(
            any("duplicate Repair batch" in error for error in errors), errors
        )

    def test_review_convergence_mixed_relations_keep_routes_separate(self) -> None:
        case = self._review_convergence_case()
        case["id"] = "review-convergence-mixed-relations"
        review = next(event for event in case["events"] if event["action"] == "review")
        first = next(event for event in case["events"] if event["action"] == "finding")
        second = next(
            event
            for event in case["events"]
            if event.get("finding_id") == "F-C-B"
        )
        second.update(
            {
                "finding_id": "F-C-SCOPE",
                "relation": "scope-blocker",
                "repair_required": False,
            }
        )
        for field in (
            "affected_scope",
            "acceptance_or_risk_impact",
            "required_validation",
            "required_covering_rereview",
        ):
            second.pop(field, None)
        adjacent = copy.deepcopy(second)
        adjacent.update(
            {
                "finding_id": "F-C-ADJ",
                "relation": "adjacent",
                "category": "adjacent-issue",
            }
        )
        case["events"].insert(case["events"].index(review), adjacent)
        review["finding_ids"] = ["F-C-A", "F-C-SCOPE", "F-C-ADJ"]
        repair = next(event for event in case["events"] if event["action"] == "repair")
        repair["resolved_finding_ids"] = ["F-C-A"]
        repair["finding_relations"] = {"F-C-A": "current-task"}
        repair["finding_obligations"] = repair["finding_obligations"][:1]
        repair["affected_risk_dimensions"] = ["security"]

        analysis = {
            "action": "analysis",
            "analysis_kind": "delta",
            "protected_decision_invalidated": True,
            "invalidated_decisions": ["scope-blocker"],
            "transitive_updates": [
                "affected-brief-sections",
                "affected-tasks",
                "affected-review-boundaries",
            ],
            "analysis_scope": "delta",
            "path_change_evidence": {
                "changed-hypothesis": False,
                "changed-material": True,
                "changed-gap": False,
                "changed-transition": False,
            },
            "professional_domain_changed": False,
            "work_type_changed": False,
            "material_risk_trigger_changed": False,
            "skill_assignments": {
                task["id"]: task["primary_skill"] for task in case["tasks"]
            },
            "delta_impact": {
                "invalidated": ["scope-blocker"],
                "affected": {
                    "brief": [
                        "Acceptance and Non-goals",
                        "Ownership and Invariants",
                        "Placement and Reuse",
                        "Contract / Data / Failure Impact",
                    ],
                    "tasks": ["C"],
                    "dependencies": [],
                    "skills": [],
                    "reviews": ["security-privacy-gate"],
                },
                "unlisted": "preserved",
            },
        }
        case["events"].insert(case["events"].index(repair), analysis)

        errors, trace = EVAL._orchestration_case_result(case)

        self.assertEqual([], errors)
        actions = [event["action"] for event in case["events"]]
        self.assertLess(actions.index("review"), actions.index("analysis", 1))
        self.assertLess(actions.index("analysis", 1), actions.index("repair"))
        self.assertLess(actions.index("repair"), actions.index("re-review"))
        self.assertEqual(["F-C-A"], trace["repair_flow"]["resolved_finding_ids"])
        self.assertEqual(["F-C-SCOPE"], trace["finding_routes"]["scope_blocker"])
        self.assertEqual(["F-C-ADJ"], trace["finding_routes"]["adjacent"])
        self.assertTrue(
            trace["analysis"]["review_delta_path_changes"][0][
                "path_change_evidence"
            ]["changed-material"]
        )
        self.assertEqual("complete", trace["completion"]["state"])

    def test_review_convergence_rejects_scope_blocker_analysis_before_close(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "review-convergence-mixed-relations"
            )
        )
        case.pop("retained_semantics", None)
        review_index = next(
            index
            for index, event in enumerate(case["events"])
            if event["action"] == "review"
        )
        analysis_index = next(
            index
            for index, event in enumerate(case["events"])
            if event.get("analysis_kind") == "delta"
        )
        analysis = case["events"].pop(analysis_index)
        case["events"].insert(review_index, analysis)

        errors = EVAL._orchestration_case_errors(case)

        self.assertTrue(
            any("[scope-blocker-route]" in error for error in errors), errors
        )

    def test_review_convergence_adjacent_only_can_pass_both_review_paths(self) -> None:
        release = self._release_case("single-file-bug-fix")
        review_index = next(
            index
            for index, step in enumerate(release["steps"])
            if step.get("actor") == "review-agent" and step.get("action") == "review"
        )
        closing = release["steps"][review_index]
        adjacent = {
            "actor": "review-agent",
            "action": "finding",
            "task_id": closing["task_id"],
            "review_round_id": closing["review_round_id"],
            "evidence_id": "adjacent-release-only",
            "relation": "adjacent",
            "material": False,
        }
        release["steps"].insert(review_index, adjacent)
        closing["finding_ids"] = [adjacent["evidence_id"]]
        self.assertEqual([], EVAL._review_discipline_errors(release["id"], release["steps"]))

        orchestration = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "dedup-direct-work-zero-analysis"
            )
        )
        orchestration["id"] = "review-convergence-adjacent-only-pass"
        orchestration.pop("retained_semantics", None)
        closing = next(
            event for event in orchestration["events"] if event["action"] == "review"
        )
        adjacent_event = {
            "action": "finding",
            "finding_id": "F-A-ADJACENT",
            "task_id": "A",
            "review_round_id": closing["review_round_id"],
            "relation": "adjacent",
            "category": "adjacent-issue",
            "repair_required": False,
        }
        orchestration["events"].insert(
            orchestration["events"].index(closing), adjacent_event
        )
        closing["finding_ids"] = [adjacent_event["finding_id"]]

        errors, trace = EVAL._orchestration_case_result(orchestration)

        self.assertEqual([], errors)
        self.assertEqual(["F-A-ADJACENT"], trace["finding_routes"]["adjacent"])
        self.assertEqual(0, trace["repair_flow"]["repair_count"])
        self.assertTrue(trace["completion"]["current_evidence"])

    def test_review_convergence_current_task_finding_still_rejects_pass(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "review-convergence-adjacent-only-pass"
            )
        )
        case.pop("retained_semantics", None)
        finding = next(event for event in case["events"] if event["action"] == "finding")
        finding.update(
            relation="current-task",
            category="correctness-or-invariant",
            impact_dimensions=["correctness"],
            repair_required=True,
            affected_scope=["A"],
            acceptance_or_risk_impact="correctness",
            required_validation=["current-generation-scoped-validation"],
            required_covering_rereview={
                "covered_task_ids": ["A"],
                "same_or_stronger": True,
            },
        )

        errors = EVAL._orchestration_case_errors(case)

        self.assertTrue(any("[review-verdict]" in error for error in errors), errors)

    def test_review_convergence_malformed_membership_fields_fail_without_exceptions(self) -> None:
        finding_id_values = (None, 7, "F-C-SCOPE", ["F-C-CURRENT", []])
        for value in finding_id_values:
            with self.subTest(field="finding_ids", value=value):
                case = copy.deepcopy(
                    next(
                        item
                        for item in self.orchestration_cases
                        if item["id"] == "review-convergence-mixed-relations"
                    )
                )
                case.pop("retained_semantics", None)
                next(
                    event for event in case["events"] if event["action"] == "review"
                )["finding_ids"] = value
                errors = EVAL._orchestration_case_errors(case)
                self.assertTrue(
                    any("[review-complete-pass]" in error for error in errors), errors
                )

        invalidated_values = (None, 7, "scope-blocker", [["scope-blocker"]], [7])
        for value in invalidated_values:
            with self.subTest(field="invalidated_decisions", value=value):
                case = copy.deepcopy(
                    next(
                        item
                        for item in self.orchestration_cases
                        if item["id"] == "review-convergence-mixed-relations"
                    )
                )
                case.pop("retained_semantics", None)
                next(
                    event
                    for event in case["events"]
                    if event.get("analysis_kind") == "delta"
                )["invalidated_decisions"] = value
                errors = EVAL._orchestration_case_errors(case)
                self.assertTrue(
                    any(
                        "[analysis-decision-invalidation]" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_ready_blocked_review_requires_exact_core_reason(self) -> None:
        triggers = {
            "fundamental-architecture-error",
            "invalid-public-contract",
            "major-security-defect",
            "acceptance-fundamentally-unmet",
        }
        base = copy.deepcopy(
            next(
                item
                for item in self.orchestration_cases
                if item["id"] == "dedup-terminal-blocked-review"
            )
        )
        base.pop("retained_semantics", None)
        review = next(event for event in base["events"] if event["action"] == "review")
        for reason in sorted(triggers):
            with self.subTest(path="orchestration", reason=reason):
                probe = copy.deepcopy(base)
                next(
                    event for event in probe["events"] if event["action"] == "review"
                )["reason"] = reason
                self.assertEqual([], EVAL._orchestration_case_errors(probe))
        for reason in (None, "unknown", "ordinary-material-finding"):
            with self.subTest(path="orchestration-invalid", reason=reason):
                probe = copy.deepcopy(base)
                blocked = next(
                    event for event in probe["events"] if event["action"] == "review"
                )
                if reason is None:
                    blocked.pop("reason", None)
                else:
                    blocked["reason"] = reason
                errors = EVAL._orchestration_case_errors(probe)
                self.assertTrue(
                    any("[review-fail-fast]" in error for error in errors), errors
                )

        release = self._release_case("single-file-bug-fix")
        discipline = next(
            step for step in release["steps"] if step.get("action") == "review-discipline"
        )
        closing = next(
            step
            for step in release["steps"]
            if step.get("actor") == "review-agent" and step.get("action") == "review"
        )
        discipline["dimensions"]["observable-acceptance"] = "blocked"
        discipline["verdict"] = "blocked"
        closing.update(
            reason="fundamental-architecture-error",
            reviewed_scope=["owner.py"],
            unreviewed_scope=["dependent consumer"],
        )
        for reason in sorted(triggers):
            with self.subTest(path="ready-review", reason=reason):
                probe = copy.deepcopy(release)
                next(
                    step
                    for step in probe["steps"]
                    if step.get("actor") == "review-agent"
                    and step.get("action") == "review"
                )["reason"] = reason
                self.assertEqual(
                    [], EVAL._review_discipline_errors(probe["id"], probe["steps"])
                )
        for reason in (None, "unknown", "ordinary-material-finding"):
            with self.subTest(path="ready-review-invalid", reason=reason):
                probe = copy.deepcopy(release)
                blocked = next(
                    step
                    for step in probe["steps"]
                    if step.get("actor") == "review-agent"
                    and step.get("action") == "review"
                )
                if reason is None:
                    blocked.pop("reason", None)
                else:
                    blocked["reason"] = reason
                errors = EVAL._review_discipline_errors(probe["id"], probe["steps"])
                self.assertTrue(
                    any("[review-fail-fast]" in error for error in errors), errors
                )
        for field in ("reviewed_scope", "unreviewed_scope"):
            with self.subTest(path="ready-review-scope", field=field):
                probe = copy.deepcopy(release)
                next(
                    step
                    for step in probe["steps"]
                    if step.get("actor") == "review-agent"
                    and step.get("action") == "review"
                )[field] = []
                errors = EVAL._review_discipline_errors(probe["id"], probe["steps"])
                self.assertTrue(
                    any("[review-fail-fast]" in error for error in errors), errors
                )

    def test_orchestration_semantic_trace_is_bounded_reducer_state(self) -> None:
        results, errors = EVAL._orchestration_fixture_results(
            self.orchestration_cases
        )
        self.assertEqual([], errors)
        by_id = {result["id"]: result for result in results}

        combined = by_id["dedup-combined-multi-task"]["semantic_trace"]
        self.assertEqual("analyzed", combined["work_kind"])
        self.assertEqual(
            {"count": 1, "kinds": ["initial"]}, combined["analysis"]
        )
        self.assertEqual(
            ["A", "B", "C"],
            [task["task_id"] for task in combined["task_dispatch"]],
        )
        self.assertTrue(
            all(task["primary_skill"] for task in combined["task_dispatch"])
        )
        self.assertTrue(
            all("layer3_skills" in task for task in combined["task_dispatch"])
        )
        self.assertEqual(3, combined["validation"]["fresh_count"])
        self.assertEqual(3, combined["validation"]["reuse_count"])
        self.assertEqual(0, combined["validation"]["rerun_count"])
        self.assertEqual(1, combined["review"]["count"])
        self.assertEqual("complete", combined["completion"]["state"])
        self.assertTrue(combined["completion"]["current_evidence"])
        self.assertEqual(
            ["A", "B", "C"],
            combined["completion"]["current_validation_task_ids"],
        )
        self.assertEqual(
            ["A", "B", "C"],
            combined["completion"]["current_review_task_ids"],
        )
        self.assertEqual("serialized-events", combined["parallel_isolation"])
        self.assertEqual(
            "deterministic-structural-fixture-only", combined["proof_limit"]
        )

        direct = by_id["dedup-direct-work-zero-analysis"]["semantic_trace"]
        self.assertEqual("direct", direct["work_kind"])
        self.assertEqual({"count": 0, "kinds": []}, direct["analysis"])
        self.assertTrue(direct["completion"]["current_evidence"])

        positive_ids = {
            case["id"] for case in self.orchestration_cases if case["expected_valid"]
        }
        for case_id in positive_ids:
            trace = by_id[case_id]["semantic_trace"]
            with self.subTest(initial_analysis=case_id):
                if trace["work_kind"] == "analyzed":
                    self.assertEqual(1, trace["analysis"]["kinds"].count("initial"))

        reuse = by_id["dedup-reuse-fresh-validation"]["semantic_trace"]
        self.assertEqual(["v-A"], reuse["validation"]["reused_evidence_ids"])
        self.assertEqual(0, reuse["validation"]["rerun_count"])

        routed = by_id["duplicate-same-scope-analysis"]["semantic_trace"]
        self.assertEqual(
            ["minimal-correct-implementation"],
            routed["task_dispatch"][0]["layer3_skills"],
        )

        repair = by_id["dedup-scoped-repair-subsumes-final"]["semantic_trace"]
        self.assertEqual(
            {
                "repair_count": 1,
                "affected_task_ids": ["C"],
                "invalidated_claims": ["review:C", "validation:C"],
                "fresh_validation_task_ids": ["C"],
                "rereviewed_task_ids": ["C"],
                "repair_counts_by_task": {"C": 1},
                "cap_dispositions": {"C": "within-budget"},
                "rereview_finding_classifications": [],
                "current_review_round_ids": {
                    "A": "R-C-1",
                    "B": "R-C-1",
                    "C": "R-C-2",
                },
                "resolved_finding_ids": ["F-C-A", "F-C-B"],
                "batch_keys": [["R-C-1", "C"]],
            },
            repair["repair_flow"],
        )
        self.assertTrue(repair["completion"]["current_evidence"])
        self.assertEqual(
            ["A", "B", "C"],
            [
                item["task_id"]
                for item in repair["completion"]["current_validation_evidence"]
            ],
        )
        self.assertEqual(
            ["A", "B", "C"],
            [
                item["task_id"]
                for item in repair["completion"]["current_review_evidence"]
            ],
        )

        justified_rerun = copy.deepcopy(
            next(
                case
                for case in self.orchestration_cases
                if case["id"] == "dedup-reject-mechanical-revalidation"
            )
        )
        justified_rerun["id"] = "justified-validation-rerun"
        review = next(
            event for event in justified_rerun["events"] if event["action"] == "review"
        )
        review["reproduction_triggers"] = ["concrete-reviewer-doubt"]
        review.update(
            review_round_id="R-A-JUSTIFIED-RERUN-1",
            required_changed_scope_complete=True,
            base_dimensions_complete=True,
            professional_risk_dimensions_complete=True,
            finding_ids=[],
        )
        reducer_errors, justified_trace = EVAL._orchestration_case_result(
            justified_rerun
        )
        self.assertEqual([], reducer_errors)
        self.assertEqual(1, justified_trace["validation"]["rerun_count"])
        self.assertEqual(0, justified_trace["validation"]["reuse_count"])

        forbidden_trace_fields = {
            "prompt",
            "brief",
            "capsule",
            "handoff",
            "analysis_history",
            "task_dag",
        }
        for result in results:
            trace = result["semantic_trace"]
            with self.subTest(bounded_trace=result["id"]):
                self.assertTrue(trace)
                self.assertTrue(forbidden_trace_fields.isdisjoint(trace))

    def test_tracked_hookless_report_matches_current_evaluator_and_orchestration_fixtures(
        self,
    ) -> None:
        results, evaluator_errors = EVAL._orchestration_fixture_results(
            copy.deepcopy(self.orchestration_cases)
        )
        self.assertEqual([], evaluator_errors)
        report = json.loads(EVAL.REPORT_JSON.read_text(encoding="utf-8"))
        self.assertEqual(
            [],
            EVAL._hookless_report_currentness_errors(
                report,
                results,
                evaluator_errors,
            ),
        )
        mutations = []
        status = copy.deepcopy(report)
        status["status"] = "fail"
        mutations.append(("status", status))
        count = copy.deepcopy(report)
        count["orchestration_fixture_count"] += 1
        mutations.append(("orchestration_fixture_count", count))
        trace_ids = copy.deepcopy(report)
        trace_ids["semantic_traces"][0]["id"] = "stale-semantic-trace"
        mutations.append(("semantic_trace_ids", trace_ids))
        repair_counts = copy.deepcopy(report)
        repair_trace = next(
            trace
            for trace in repair_counts["semantic_traces"]
            if trace["repair_flow"]["repair_count"]
        )
        repair_trace["repair_flow"]["repair_count"] += 1
        mutations.append(("repair_counts", repair_counts))
        review_actions = copy.deepcopy(report)
        rereview_trace = next(
            trace
            for trace in review_actions["semantic_traces"]
            if "re-review" in trace["review"]["actions"]
        )
        rereview_trace["review"]["actions"] = ["review"]
        mutations.append(("review_actions", review_actions))
        cap_dispositions = copy.deepcopy(report)
        cap_trace = next(
            trace
            for trace in cap_dispositions["semantic_traces"]
            if trace["repair_flow"].get("cap_dispositions")
        )
        cap_trace["repair_flow"]["cap_dispositions"] = {}
        mutations.append(("cap_dispositions", cap_dispositions))
        for expected, stale in mutations:
            with self.subTest(stale=expected):
                errors = EVAL._hookless_report_currentness_errors(
                    stale,
                    results,
                    evaluator_errors,
                )
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_hookless_currentness_closes_classification_and_evidence_payloads(
        self,
    ) -> None:
        results, evaluator_errors = EVAL._orchestration_fixture_results(
            copy.deepcopy(self.orchestration_cases)
        )
        self.assertEqual([], evaluator_errors)
        report = {
            "status": "pass",
            "orchestration_fixture_count": len(results),
            "semantic_traces": [
                copy.deepcopy(result["semantic_trace"]) for result in results
            ],
        }
        self.assertEqual(
            [],
            EVAL._hookless_report_currentness_errors(
                report,
                results,
                evaluator_errors,
            ),
        )
        classification_trace = next(
            trace
            for trace in report["semantic_traces"]
            if trace.get("rereview_finding_classifications")
        )
        self.assertTrue(classification_trace["rereview_finding_classifications"])

        mutations = []
        stale_classification = copy.deepcopy(report)
        stale_classification_trace = next(
            trace
            for trace in stale_classification["semantic_traces"]
            if trace.get("rereview_finding_classifications")
        )
        stale_classification_trace["rereview_finding_classifications"][0][
            "classification"
        ] = "inherited"
        mutations.append(stale_classification)
        stale_evidence = copy.deepcopy(report)
        stale_evidence_trace = next(
            trace
            for trace in stale_evidence["semantic_traces"]
            if trace.get("rereview_finding_classifications")
        )
        stale_evidence_trace["rereview_finding_classifications"][0][
            "classification_evidence"
        ] = "stale classification evidence"
        mutations.append(stale_evidence)
        stale_current_evidence = copy.deepcopy(report)
        current_evidence_trace = next(
            trace
            for trace in stale_current_evidence["semantic_traces"]
            if trace.get("completion", {}).get("current_evidence") is True
        )
        current_evidence_trace["completion"]["current_evidence"] = False
        mutations.append(stale_current_evidence)

        for stale in mutations:
            errors = EVAL._hookless_report_currentness_errors(
                stale,
                results,
                evaluator_errors,
            )
            self.assertTrue(
                any("semantic_traces" in error for error in errors),
                errors,
            )

    def test_orchestration_direct_work_has_zero_analysis(self) -> None:
        direct = copy.deepcopy(
            next(
                case
                for case in self.orchestration_cases
                if case["id"] == "dedup-reuse-fresh-validation"
            )
        )
        direct["id"] = "direct-work-zero-analysis"
        direct["events"] = [
            event for event in direct["events"] if event["action"] != "analysis"
        ]

        errors, trace = EVAL._orchestration_case_result(direct)

        self.assertEqual([], errors)
        self.assertEqual("direct", trace["work_kind"])
        self.assertEqual({"count": 0, "kinds": []}, trace["analysis"])

    def test_orchestration_parallel_isolation_is_fixture_derived(self) -> None:
        isolated = copy.deepcopy(
            next(
                case
                for case in self.orchestration_cases
                if case["id"] == "dedup-combined-multi-task"
            )
        )
        isolated["id"] = "isolated-parallel-orchestration"
        edits = [event for event in isolated["events"] if event["action"] == "edit"]
        for event, workspace, scope in zip(
            edits[:2],
            ("workspace-a", "workspace-b"),
            (["src/a/**"], ["src/b/**"]),
        ):
            event.update(
                {
                    "parallel_batch": "batch-1",
                    "workspace": workspace,
                    "workspace_isolation": "host-provided",
                    "write_scope": scope,
                }
            )

        errors, trace = EVAL._orchestration_case_result(isolated)
        self.assertEqual([], errors)
        self.assertEqual("isolated-parallel-events", trace["parallel_isolation"])

        conflicting = copy.deepcopy(isolated)
        conflicting["id"] = "conflicting-parallel-orchestration"
        next(
            event
            for event in conflicting["events"]
            if event.get("workspace") == "workspace-b"
        )["workspace_isolation"] = "shared"
        errors, _trace = EVAL._orchestration_case_result(conflicting)
        self.assertTrue(
            any("parallel-write-isolation" in error for error in errors), errors
        )

    def test_positive_orchestration_retained_semantics_equal_trace_projection(
        self,
    ) -> None:
        results, errors = EVAL._orchestration_fixture_results(
            self.orchestration_cases
        )
        self.assertEqual([], errors)
        by_id = {result["id"]: result for result in results}
        positives = [case for case in self.orchestration_cases if case["expected_valid"]]

        for case in positives:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    case["retained_semantics"],
                    EVAL._retained_semantic_projection(
                        by_id[case["id"]]["semantic_trace"]
                    ),
                )
                self.assertTrue(
                    by_id[case["id"]]["retained_semantic_equality"]
                )

        drifted = copy.deepcopy(positives[0])
        drifted["id"] = "retained-semantic-baseline-drift"
        drifted["retained_semantics"]["work_kind"] = "direct"
        drifted_results, drifted_errors = EVAL._orchestration_fixture_results(
            [drifted]
        )
        self.assertFalse(drifted_results[0]["retained_semantic_equality"])
        self.assertTrue(
            any("semantic-trace-retention" in error for error in drifted_errors),
            drifted_errors,
        )

    def test_task_focus_negative_controls_reject_scope_and_review_drift(self) -> None:
        expected = {
            "focus-rejects-adjacent-repair": "adjacent findings cannot block or enter repair",
            "focus-rejects-read-scope-write": "Allowed Read Scope does not grant write authority",
            "focus-rejects-l4-default-prereview": "L4 does not default to pre-implementation review",
            "focus-rejects-stale-repair-evidence": "fresh validation, latest actual diff, and fresh independent review",
            "focus-rejects-unrelated-repair-file": "revert the unrelated changed file",
            "focus-task-read-actual-failure": "static fixture result cannot prove",
        }
        by_id = {case["id"]: case for case in self.task_focus_cases}
        for case_id, message in expected.items():
            with self.subTest(case=case_id):
                errors = EVAL._task_focus_case_errors(by_id[case_id])
                self.assertTrue(any(message in error for error in errors), errors)

    def test_analysis_level_review_readiness_and_task_execution_cases_are_covered(self) -> None:
        results, errors = EVAL._task_focus_fixture_results(self.task_focus_cases)
        self.assertEqual([], errors)
        by_id = {result["id"]: result for result in results}
        required = {
            "focus-direct-candidate-confirmed-edit-l3",
            "focus-direct-candidate-wrong-owner-zero-edit-analysis",
            "focus-direct-candidate-shared-contract-zero-edit-analysis",
            "focus-task-edit-direct",
            "focus-task-execute-direct",
            "focus-task-tmp-read-direct",
            "focus-task-read-actual-failure",
            "focus-task-edit-host-denied",
            "focus-task-execute-sandbox-denied",
            "focus-task-retry-preserves-contract",
            "focus-analysis-owner-unresolved-task-l2",
            "focus-analysis-explicit-repair-task-level",
            "focus-analysis-standard-task-l3",
            "focus-analysis-material-risk-task-l4",
            "focus-direct-task-level-unchanged",
            "focus-analysis-history-unchanged",
            "focus-review-ready-dispatch-once",
            "focus-review-missing-change-evidence-blocked",
            "focus-review-readonly-reviewer-accessible",
            "focus-review-summary-is-not-evidence",
            "focus-review-stale-validation-blocked",
            "focus-review-native-reference-ready",
            "focus-review-supplied-artifact-ready",
            "focus-repair-fresh-latest-evidence",
        }
        self.assertTrue(required <= set(by_id), required - set(by_id))
        self.assertTrue(all(by_id[case_id]["matches_expected"] for case_id in required))

    def test_vue_copilot_supplied_evidence_counts_and_negatives_are_exact(self) -> None:
        case = self._release_case("single-module-feature")
        self.assertEqual("copilot", case["host"])
        self.assertEqual([], self._trajectory_errors(case))
        steps = case["steps"]
        first_review = next(
            (index for index, step in enumerate(steps)
             if step.get("actor") == "review-agent"
             and step.get("action") in {"review", "review-discipline"}),
            len(steps),
        )
        actual = {
            "analysis_dispatches": sum(
                step.get("action") == "dispatch"
                and step.get("profile") == "analysis-agent" for step in steps
            ),
            "initial_analysis_events": sum(
                step.get("actor") == "analysis-agent"
                and step.get("analysis_kind") == "initial" for step in steps
            ),
            "task_dispatches": sum(
                step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
                and step.get("mode") != "diff-export/no-edit" for step in steps
            ),
            "material_edits": sum(
                step.get("actor") == "task-agent" and step.get("action") == "edit"
                for step in steps
            ),
            "post_edit_validations": sum(
                step.get("actor") == "task-agent" and step.get("action") == "validate"
                for step in steps
            ),
            "exact_change_captures": sum(
                step.get("action") == "capture-change-evidence" for step in steps
            ),
            "implementation_handoffs": sum(
                step.get("action") == "implementation-handoff" for step in steps
            ),
            "main_readiness_gates": sum(
                step.get("action") == "review-input-ready" and step.get("ready") is True
                for step in steps
            ),
            "review_dispatches": sum(
                step.get("action") == "dispatch"
                and step.get("profile") == "review-agent" for step in steps
            ),
            "reviewer_artifact_reads": sum(
                step.get("actor") == "review-agent" and step.get("action") == "read"
                for step in steps
            ),
            "review_actions": sum(
                step.get("actor") == "review-agent" and step.get("action") == "review"
                for step in steps
            ),
            "recovery_task_dispatches": sum(
                index > first_review and step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
                for index, step in enumerate(steps)
            ),
            "diff_export_utility_dispatches": sum(
                step.get("action") == "dispatch"
                and step.get("mode") == "diff-export/no-edit" for step in steps
            ),
            "reviewer_execute_actions": sum(
                step.get("actor") == "review-agent" and step.get("action") == "execute"
                for step in steps
            ),
        }
        self.assertEqual(
            case["review_evidence_contract"]["expected_counts"], actual
        )

        negative_ids = {
            "focus-review-digest-placeholder-blocked",
            "focus-review-command-output-placeholder-blocked",
            "focus-review-opaque-reference-blocked",
            "focus-review-path-only-blocked",
        }
        negatives = {
            item["id"]: item for item in self.task_focus_cases
            if item["id"] in negative_ids
        }
        self.assertEqual(negative_ids, set(negatives))
        for case_id, negative in negatives.items():
            with self.subTest(case=case_id):
                self.assertEqual([], EVAL._task_focus_case_errors(negative))
                self.assertEqual(0, negative["decision"]["review_dispatches"])

    def test_review_readiness_requires_readable_artifact_and_fresh_validation(self) -> None:
        case = {
            "id": "review-reference-unsupported-boundary",
            "scenario": "review-readiness",
            "inputs": {
                "latest_changed_paths": True,
                "change_evidence_kind": "exact-change-content",
                "change_evidence_artifact": "diff --git a/owner.py b/owner.py\n--- a/owner.py\n+++ b/owner.py\n@@ -1 +1 @@\n-old\n+new\n",
                "reviewer_artifact_accessibility": {
                    "reviewer": "review-agent",
                    "generation": 9,
                    "changed_paths": ["owner.py"],
                    "readable": False,
                },
                "validation_generation": 9,
                "latest_material_edit_generation": 9,
                "review_scope_fixed": True,
                "reviewer_mutation": False,
                "post_review_change_export": False,
            },
            "decision": {
                "review_input_ready": False,
                "review_dispatches": 0,
                "completion": "blocked-before-review",
            },
            "expected_valid": True,
            "expected_error": None,
        }
        self.assertEqual([], EVAL._task_focus_case_errors(case))

    def test_native_change_reference_self_report_always_fails_closed(self) -> None:
        base = copy.deepcopy(
            next(
                item
                for item in self.task_focus_cases
                if item["id"] == "focus-review-native-reference-ready"
            )
        )
        base["inputs"]["change_evidence_artifact"] = {
            "reference": "native-change://codex/worktree-9",
            "generation": 4,
            "reviewer": "review-agent",
            "changed_paths": ["owner.py"],
            "readable": True,
        }
        self.assertEqual([], EVAL._task_focus_case_errors(base))

        mutations = {
            "opaque": "native-change:fixture-current",
            "stale": {
                **base["inputs"]["change_evidence_artifact"],
                "generation": 3,
            },
            "wrong-reviewer": {
                **base["inputs"]["change_evidence_artifact"],
                "reviewer": "analysis-agent",
            },
            "unreadable": {
                **base["inputs"]["change_evidence_artifact"],
                "readable": False,
            },
        }
        for name, artifact in mutations.items():
            with self.subTest(mutation=name):
                negative = copy.deepcopy(base)
                negative["id"] = f"native-reference-{name}-blocked"
                negative["inputs"]["change_evidence_artifact"] = artifact
                negative["decision"] = {
                    "review_input_ready": False,
                    "review_dispatches": 0,
                    "completion": "blocked-before-review",
                }
                self.assertEqual([], EVAL._task_focus_case_errors(negative))

    def test_unified_diff_parser_rejects_pseudo_hunks_and_mismatched_paths(self) -> None:
        malformed = {
            "mismatched-path": (
                "diff --git a/owner.py b/owner.py\n"
                "--- a/other.py\n+++ b/owner.py\n"
                "@@ -1 +1 @@\n-old\n+new\n"
            ),
            "garbage-hunk": (
                "diff --git a/owner.py b/owner.py\n"
                "--- a/owner.py\n+++ b/owner.py\n"
                "@@ garbage\n-old\n+new\n"
            ),
            "wrong-hunk-count": (
                "diff --git a/owner.py b/owner.py\n"
                "--- a/owner.py\n+++ b/owner.py\n"
                "@@ -1,2 +1 @@\n-old\n+new\n"
            ),
            "empty-first-section": (
                "diff --git a/empty.py b/empty.py\nindex 1111111..2222222 100644\n"
                "diff --git a/owner.py b/owner.py\n"
                "--- a/owner.py\n+++ b/owner.py\n"
                "@@ -1 +1 @@\n-old\n+new\n"
            ),
        }
        for name, payload in malformed.items():
            with self.subTest(case=name):
                self.assertIsNone(EVAL._unified_diff_paths(payload))

    def test_unified_diff_parser_accepts_git_non_text_and_boundary_forms(self) -> None:
        valid = {
            "new-file": (
                "diff --git a/new.py b/new.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/new.py\n"
                "@@ -0,0 +1 @@\n+new\n",
                ["new.py"],
            ),
            "deleted-file": (
                "diff --git a/old.py b/old.py\ndeleted file mode 100644\n"
                "--- a/old.py\n+++ /dev/null\n"
                "@@ -1 +0,0 @@\n-old\n",
                ["old.py"],
            ),
            "rename": (
                "diff --git a/old.py b/new.py\nsimilarity index 100%\n"
                "rename from old.py\nrename to new.py\n",
                ["new.py"],
            ),
            "copy": (
                "diff --git a/source.py b/copy.py\nsimilarity index 100%\n"
                "copy from source.py\ncopy to copy.py\n",
                ["copy.py"],
            ),
            "mode-only": (
                "diff --git a/tool.sh b/tool.sh\n"
                "old mode 100644\nnew mode 100755\n",
                ["tool.sh"],
            ),
            "binary": (
                "diff --git a/image.png b/image.png\n"
                "index 1111111..2222222 100644\n"
                "Binary files a/image.png and b/image.png differ\n",
                ["image.png"],
            ),
        }
        for name, (payload, paths) in valid.items():
            with self.subTest(case=name):
                self.assertEqual(paths, EVAL._unified_diff_paths(payload))

    def test_unified_diff_parser_rejects_mixed_duplicate_or_inconsistent_metadata(self) -> None:
        invalid = {
            "mixed-rename-copy": (
                "diff --git a/old.py b/new.py\n"
                "similarity index 100%\n"
                "rename from old.py\nrename to new.py\n"
                "copy from old.py\ncopy to new.py\n"
            ),
            "duplicate-index": (
                "diff --git a/owner.py b/owner.py\n"
                "index 1111111..2222222 100644\n"
                "index 1111111..2222222 100644\n"
                "--- a/owner.py\n+++ b/owner.py\n"
                "@@ -1 +1 @@\n-old\n+new\n"
            ),
            "duplicate-similarity": (
                "diff --git a/old.py b/new.py\n"
                "similarity index 100%\nsimilarity index 100%\n"
                "rename from old.py\nrename to new.py\n"
            ),
            "new-and-deleted": (
                "diff --git a/item.py b/item.py\n"
                "new file mode 100644\ndeleted file mode 100644\n"
                "--- /dev/null\n+++ /dev/null\n"
                "@@ -0,0 +0,0 @@\n+new\n"
            ),
            "rename-plus-new-file": (
                "diff --git a/old.py b/new.py\nnew file mode 100644\n"
                "similarity index 100%\n"
                "rename from old.py\nrename to new.py\n"
            ),
            "mode-only-with-index": (
                "diff --git a/tool.sh b/tool.sh\n"
                "old mode 100644\nnew mode 100755\n"
                "index 1111111..2222222 100644\n"
            ),
        }
        for name, payload in invalid.items():
            with self.subTest(case=name):
                self.assertIsNone(EVAL._unified_diff_paths(payload))

    def test_unified_diff_parser_distinguishes_file_headers_from_changed_hunk_lines(self) -> None:
        changed_header_like_lines = (
            "diff --git a/guide.md b/guide.md\n"
            "index 1111111..2222222 100644\n"
            "--- a/guide.md\n+++ b/guide.md\n"
            "@@ -1 +1 @@\n--- heading\n+++ heading\n"
        )
        self.assertEqual(
            ["guide.md"], EVAL._unified_diff_paths(changed_header_like_lines)
        )

        context_only = (
            "diff --git a/guide.md b/guide.md\n"
            "--- a/guide.md\n+++ b/guide.md\n"
            "@@ -1 +1 @@\n unchanged\n"
        )
        self.assertIsNone(EVAL._unified_diff_paths(context_only))

    def test_canonical_analyzed_trajectory_requires_complete_accepted_initial_brief(self) -> None:
        case = self._release_case("single-module-feature")
        initial_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "analysis-agent"
            and step.get("action") == "first_executable_slice"
        )
        self.assertEqual(
            self._complete_initial_analysis_event(),
            case["steps"][initial_index],
        )

        mutations = {}
        missing_kind = copy.deepcopy(case)
        missing_kind["steps"][initial_index].pop("analysis_kind")
        mutations["missing-kind"] = (missing_kind, "analysis-initial-kind")
        missing_field = copy.deepcopy(case)
        missing_field["steps"][initial_index].pop("owner_placement_invariant")
        mutations["missing-field"] = (missing_field, "analysis-initial-shape")
        altered_route = copy.deepcopy(case)
        altered_route["steps"][initial_index]["downstream_task"][
            "professional_skill"
        ] = "repository-tooling-change-builder"
        mutations["altered-route"] = (altered_route, "analysis-task-projection")
        for name, (mutation, expected) in mutations.items():
            with self.subTest(mutation=name):
                errors = self._trajectory_errors(mutation)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_delta_requires_accepted_brief_binding_and_cannot_self_reroute(self) -> None:
        base = self._release_case("single-module-feature")
        initial_index = next(
            index
            for index, step in enumerate(base["steps"])
            if step.get("actor") == "analysis-agent"
            and step.get("action") == "first_executable_slice"
        )
        delta = self._post_acceptance_delta_event()

        legitimate = copy.deepcopy(base)
        legitimate["steps"].insert(initial_index + 1, copy.deepcopy(delta))
        legitimate_errors = self._trajectory_errors(legitimate)
        self.assertFalse(
            any("analysis-" in error for error in legitimate_errors),
            legitimate_errors,
        )

        pre_acceptance = copy.deepcopy(base)
        pre_acceptance["steps"].insert(initial_index, copy.deepcopy(delta))
        errors = self._trajectory_errors(pre_acceptance)
        self.assertTrue(any("analysis-delta-acceptance" in error for error in errors), errors)

        rerouted = copy.deepcopy(legitimate)
        rerouted_delta = next(
            step for step in rerouted["steps"] if step.get("analysis_kind") == "delta"
        )
        rerouted_delta["downstream_task"]["professional_skill"] = (
            "repository-tooling-change-builder"
        )
        errors = self._trajectory_errors(rerouted)
        self.assertTrue(any("analysis-delta-routing" in error for error in errors), errors)

    def test_analysis_mode_owns_read_only_bypass_and_blocked_slice_authority(self) -> None:
        def analysis_dispatch(mode: str) -> dict:
            return {
                "actor": "main-control-agent",
                "action": "dispatch",
                "profile": "analysis-agent",
                "mode": mode,
            }

        for mode in ("diagnosis-only", "source-backed-answer"):
            with self.subTest(read_only_mode=mode):
                self.assertEqual(
                    [],
                    EVAL._analyzed_trajectory_authority_errors(
                        f"read-only-{mode}",
                        "analyzed",
                        [analysis_dispatch(mode)],
                    ),
                )

        implementation = [analysis_dispatch("implementation-preparation")]
        errors = EVAL._analyzed_trajectory_authority_errors(
            "implementation-missing-initial",
            "analyzed",
            implementation,
        )
        self.assertTrue(any("analysis-initial-kind" in error for error in errors), errors)

        blocked_at_slice = [
            analysis_dispatch("implementation-preparation"),
            self._complete_initial_analysis_event(),
        ]
        self.assertEqual(
            [],
            EVAL._analyzed_trajectory_authority_errors(
                "implementation-blocked-at-slice",
                "analyzed",
                blocked_at_slice,
            ),
        )

        mutated = copy.deepcopy(blocked_at_slice)
        mutated[0]["mode"] = "diagnosis-only"
        mutated.pop()
        self.assertEqual(
            [],
            EVAL._analyzed_trajectory_authority_errors(
                "diagnosis-mode-positive", "analyzed", mutated
            ),
        )
        mutated[0]["mode"] = "implementation-preparation"
        errors = EVAL._analyzed_trajectory_authority_errors(
            "implementation-mode-mutation", "analyzed", mutated
        )
        self.assertTrue(any("analysis-initial-kind" in error for error in errors), errors)

    def test_initial_analysis_event_must_follow_its_unique_dispatch(self) -> None:
        event_before_dispatch = [
            self._complete_initial_analysis_event(),
            {
                "actor": "main-control-agent",
                "action": "dispatch",
                "profile": "analysis-agent",
                "mode": "implementation-preparation",
            },
        ]
        errors = EVAL._analyzed_trajectory_authority_errors(
            "initial-before-dispatch", "analyzed", event_before_dispatch
        )
        self.assertTrue(any("analysis-initial-order" in error for error in errors), errors)

    def test_adapter_metadata_does_not_participate_in_task_execution(self) -> None:
        case = next(
            item
            for item in self.task_focus_cases
            if item["id"] == "focus-task-edit-direct"
        )
        self.assertNotIn("adapter_metadata", case["inputs"])
        self.assertEqual([], EVAL._task_focus_case_errors(case))

    def test_release_reviews_use_one_typed_guard_per_review_outcome(self) -> None:
        for case in [*self.release_cases, *self.scheduling_cases, *self.utility_cases]:
            review_count = sum(
                step.get("actor") == "review-agent"
                and step.get("action") in EVAL.REVIEW_ACTIONS
                for step in case["steps"]
            )
            guard_count = sum(
                step.get("action") == EVAL.REVIEW_DISCIPLINE_ACTION
                for step in case["steps"]
            )
            with self.subTest(case=case["id"]):
                self.assertEqual(review_count, guard_count)
                self.assertEqual(
                    [], EVAL._review_discipline_errors(case["id"], case["steps"])
                )

    @staticmethod
    def _discipline_event(case: dict) -> dict:
        return next(
            step
            for step in case["steps"]
            if step.get("action") == "implementation-discipline"
        )

    @staticmethod
    def _error_codes(errors: list[str]) -> set[str]:
        return {
            error.split("[", 1)[1].split("]", 1)[0]
            for error in errors
            if "[" in error and "]" in error
        }

    def _adaptive_case(self, approach: str) -> tuple[dict, dict, dict[str, dict]]:
        base_case_ids = {
            "test-first": "single-file-bug-fix",
            "test-after": "single-module-feature",
            "existing-proof-only": "single-module-feature",
            "non-test-validation": "release-rollback",
        }
        case = self._release_case(base_case_ids[approach])
        authority = case.get("implementation_oracle")
        anchored_assertion = next(
            (
                step["assertion"]
                for step in case["steps"]
                if step.get("action") == "adaptive-test-evidence"
                and step.get("evidence_kind") == "red"
            ),
            None,
        )
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "adaptive-test-evidence"
        ]
        event = self._discipline_event(case)
        variants = {
            "test-first": (
                "behavior",
                ["reproducible-bug"],
                ("red", "green"),
                "the reproducible owner bug reaches the accepted result",
                "owner.py public result",
                "the targeted assertion rejects the reproduced bug",
            ),
            "test-after": (
                "behavior",
                ["existing-primary-coverage"],
                ("green",),
                "a bounded local branch changes under existing primary coverage",
                "module-a/service.py local branch",
                "the module feature test observes the accepted branch result",
            ),
            "existing-proof-only": (
                "behavior",
                ["existing-regression-mechanism", "no-new-uncovered-behavior"],
                ("existing-proof",),
                "the edit preserves behavior already covered by the regression mechanism",
                "module-a/service.py existing covered behavior",
                "the existing regression assertion observes the unchanged behavior",
            ),
            "non-test-validation": (
                "non-behavior",
                ["documentation"],
                ("non-test",),
                "the release-plan documentation changes without runtime behavior",
                "release-plan.md documentation boundary",
                "the documentation check observes the rendered static plan",
            ),
        }
        (
            change_kind,
            risk_triggers,
            evidence_kinds,
            failure_mechanism,
            boundary,
            oracle,
        ) = variants[approach]
        if isinstance(authority, dict):
            failure_mechanism = authority["failure_mechanism"]
            oracle = authority["oracle"]
        evidence_ids = [f"{event['task_id']}-{kind}" for kind in evidence_kinds]
        guard = {
            "guard": "guard-g-adaptive-testing",
            "change_kind": change_kind,
            "approach": approach,
            "reason": f"{approach} matches the changed mechanism and oracle.",
            "failure_mechanism": failure_mechanism,
            "boundary": boundary,
            "oracle": oracle,
            "risk_triggers": risk_triggers,
            "evidence": evidence_ids,
            "proof_boundary": boundary,
        }
        guard_index = next(
            index
            for index, item in enumerate(event["evidence"])
            if item.get("guard") == "guard-g-adaptive-testing"
        )
        event["evidence"][guard_index] = guard
        records: dict[str, dict] = {}
        for evidence_id, kind in zip(evidence_ids, evidence_kinds):
            assertion = (
                "not-applicable"
                if kind == "non-test"
                else anchored_assertion
                if isinstance(authority, dict)
                else "the owner result matches the accepted behavior"
            )
            if isinstance(authority, dict):
                binding = authority["validation_binding"]
                record = {
                    "actor": "task-agent",
                    "action": "adaptive-test-evidence",
                    "task_id": event["task_id"],
                    "acceptance_id": authority["acceptance_id"],
                    "evidence_id": evidence_id,
                    "artifact_id": binding["artifact_id"],
                    "source_anchor": binding["source_anchor"],
                    "evidence_kind": kind,
                    "result": "failed" if kind == "red" else "passed",
                    "failure_class": {
                        "red": "target-behavior-missing",
                        "green": "none",
                        "existing-proof": "target-mechanism-covered",
                        "non-test": "testing-not-applicable",
                    }[kind],
                    "oracle_id": authority["oracle_id"],
                    "mechanism_id": authority["mechanism_id"],
                    "assertion_fingerprint": authority["assertion_fingerprint"],
                    "oracle": guard["oracle"],
                    "assertion": assertion,
                    "freshness": 0 if kind == "red" else 1,
                }
            else:
                record = {
                    "actor": "task-agent",
                    "action": "adaptive-test-evidence",
                    "task_id": event["task_id"],
                    "evidence_id": evidence_id,
                    "evidence_kind": kind,
                    "result": "failed" if kind == "red" else "passed",
                    "failure_class": {
                        "red": "target-behavior-missing",
                        "green": "none",
                        "existing-proof": "target-mechanism-covered",
                        "non-test": "testing-not-applicable",
                    }[kind],
                    "oracle": guard["oracle"],
                    "assertion": assertion,
                    "freshness": 0 if kind == "red" else 1,
                }
            records[kind] = record
        event_index = case["steps"].index(event)
        if "red" in records:
            case["steps"].insert(event_index, records["red"])
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        post_edit = [record for kind, record in records.items() if kind != "red"]
        case["steps"][edit_index + 1 : edit_index + 1] = post_edit
        return case, guard, records

    def test_implementation_discipline_accepts_direct_bugfix(self) -> None:
        self.assertEqual(
            [],
            self._trajectory_errors(self._release_case("single-file-bug-fix")),
        )

    def test_source_bound_bugfix_requires_structured_same_pattern_scan(self) -> None:
        case = self._release_case("single-file-bug-fix")
        guard = self._discipline_event(case)["evidence"][3]
        self.assertIn("same_pattern_scan", guard)
        guard.pop("same_pattern_scan")
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["D"],
            self._error_codes(errors),
        )

    def test_source_bound_reuse_rejects_placeholder_reason(self) -> None:
        case = self._release_case("single-file-bug-fix")
        reuse = self._discipline_event(case)["evidence"][4]["reuse_decision"]
        reuse["reason"] = "x"
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["E"],
            self._error_codes(errors),
        )

    def test_case_oracle_rejects_synchronized_weak_red_green(self) -> None:
        case = self._release_case("single-file-bug-fix")
        guard = self._discipline_event(case)["evidence"][-1]
        guard["oracle"] = "x"
        for step in case["steps"]:
            if step.get("action") == "adaptive-test-evidence":
                step["oracle"] = "x"
                step["assertion"] = "x"
        errors = self._trajectory_errors(case)
        self.assertIn(
            "implementation-oracle-authority",
            self._error_codes(errors),
        )

    def test_validation_rejects_cross_task_acceptance(self) -> None:
        case = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["acceptance_id"] = "acceptance.other-task"
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["C"],
            self._error_codes(errors),
        )

    def test_validation_rejects_oracle_artifact_mismatch(self) -> None:
        case = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["artifact_id"] = "artifact:other-test"
        errors = self._trajectory_errors(case)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["C"],
            self._error_codes(errors),
        )

    def test_source_bound_bugfix_accepts_explicit_zero_match_scan(self) -> None:
        case = self._release_case("single-file-bug-fix")
        scan = self._discipline_event(case)["evidence"][3].get(
            "same_pattern_scan"
        )
        self.assertIsInstance(scan, dict)
        assert isinstance(scan, dict)
        self.assertEqual([], scan["matches"])
        self.assertTrue(scan["explicit_zero"])
        self.assertEqual(
            [],
            EVAL._implementation_discipline_errors(
                case["id"],
                case["steps"],
                case["implementation_oracle"],
            ),
        )

    def test_evaluator_owns_hardened_oracle_digest(self) -> None:
        case = self._release_case("single-file-bug-fix")
        expected = EVAL.IMPLEMENTATION_ORACLE_CONTRACTS[case["id"]]
        self.assertEqual(
            case["implementation_oracle"]["canonical_sha256"],
            expected["canonical_sha256"],
        )

    def test_coordinated_oracle_rewrite_cannot_replace_external_authority(
        self,
    ) -> None:
        case = self._release_case("single-file-bug-fix")
        authority = case["implementation_oracle"]
        assertion = "coordinated replacement accepted behavior"
        authority["mechanism_id"] = "mechanism.coordinated-replacement"
        authority["failure_mechanism"] = "coordinated replacement mechanism"
        authority["oracle_id"] = "oracle.coordinated-replacement"
        authority["oracle"] = "coordinated replacement oracle"
        authority["assertion_fingerprint"] = EVAL._evidence_fingerprint(assertion)
        guard = self._discipline_event(case)["evidence"][-1]
        guard["failure_mechanism"] = authority["failure_mechanism"]
        guard["oracle"] = authority["oracle"]
        for record in case["steps"]:
            if record.get("action") != "adaptive-test-evidence":
                continue
            record["mechanism_id"] = authority["mechanism_id"]
            record["oracle_id"] = authority["oracle_id"]
            record["oracle"] = authority["oracle"]
            record["assertion"] = assertion
            record["assertion_fingerprint"] = authority[
                "assertion_fingerprint"
            ]
        self._rebind_authority_digest(case)
        self.assertNotEqual(
            case["implementation_oracle"]["canonical_sha256"],
            EVAL.IMPLEMENTATION_ORACLE_CONTRACTS[case["id"]][
                "canonical_sha256"
            ],
        )
        self.assertIn(
            "implementation-oracle-authority",
            self._error_codes(self._implementation_errors(case)),
        )

    def test_authority_bindings_require_exact_typed_bijection(self) -> None:
        variants: dict[str, dict] = {}

        extra = self._release_case("single-file-bug-fix")
        added = copy.deepcopy(
            extra["implementation_oracle"]["source_bindings"][-1]
        )
        added.update(
            {
                "evidence_id": "extra-unconsumed-source",
                "artifact_id": "artifact:extra.py",
                "path": "extra.py",
                "source_anchor": "extra.py#unconsumed",
            }
        )
        extra["implementation_oracle"]["source_bindings"].append(added)
        self._rebind_authority_digest(extra)
        variants["extra-binding"] = extra

        unconsumed = self._release_case("single-file-bug-fix")
        unconsumed["steps"] = [
            step
            for step in unconsumed["steps"]
            if step.get("evidence_id") != "bugfix-reuse-candidate"
        ]
        variants["unconsumed-binding"] = unconsumed

        multiuse = self._release_case("single-file-bug-fix")
        read = next(
            step
            for step in multiuse["steps"]
            if step.get("evidence_id") == "bugfix-reuse-candidate"
        )
        event_index = multiuse["steps"].index(self._discipline_event(multiuse))
        multiuse["steps"].insert(event_index, copy.deepcopy(read))
        variants["multiuse-binding"] = multiuse

        wrong_type = self._release_case("single-file-bug-fix")
        read = next(
            step
            for step in wrong_type["steps"]
            if step.get("evidence_id") == "bugfix-owner-source"
        )
        read["evidence_id"] = wrong_type["implementation_oracle"][
            "validation_binding"
        ]["evidence_id"]
        variants["wrong-type-binding"] = wrong_type

        for label, case in variants.items():
            with self.subTest(variant=label):
                self.assertIn(
                    "implementation-oracle-binding",
                    self._error_codes(self._implementation_errors(case)),
                )

    def test_coordinated_zero_scan_rewrite_cannot_replace_external_authority(
        self,
    ) -> None:
        case = self._release_case("single-file-bug-fix")
        authority = case["implementation_oracle"]
        binding = authority["same_pattern_binding"]
        binding["pattern_id"] = "pattern.coordinated-replacement"
        binding["scope"] = ["replacement.py"]
        binding["artifact_id"] = "artifact:replacement-scan"
        binding["source_anchor"] = "replacement.py#scan"
        scan = self._discipline_event(case)["evidence"][3][
            "same_pattern_scan"
        ]
        for field in ("pattern_id", "scope", "artifact_id", "source_anchor"):
            scan[field] = copy.deepcopy(binding[field])
        self._rebind_authority_digest(case)
        self.assertIn(
            "implementation-oracle-authority",
            self._error_codes(self._implementation_errors(case)),
        )

    def test_zero_match_is_fixture_structural_proof_only(self) -> None:
        case = self._release_case("single-file-bug-fix")
        authority = case["implementation_oracle"]["same_pattern_binding"]
        scan = self._discipline_event(case)["evidence"][3][
            "same_pattern_scan"
        ]
        self.assertEqual("fixture-structured-zero", authority["proof_kind"])
        self.assertEqual(authority["proof_kind"], scan["proof_kind"])
        self.assertNotIn("host", authority["proof_kind"])

    def test_adaptive_test_first_requires_ordered_valid_red_and_green(self) -> None:
        case = self._release_case("single-file-bug-fix")
        event = self._discipline_event(case)
        guard = next(
            item
            for item in event["evidence"]
            if item.get("guard") == "guard-g-adaptive-testing"
        )
        evidence_records = [
            step
            for step in case["steps"]
            if step.get("action") == "adaptive-test-evidence"
            and step.get("task_id") == event["task_id"]
        ]
        expected_ids = [
            "task-single-file-bug-fix-1-red",
            "task-single-file-bug-fix-1-green",
        ]
        self.assertEqual(expected_ids, guard["evidence"])
        self.assertEqual(expected_ids, [record["evidence_id"] for record in evidence_records])
        self.assertEqual(["red", "green"], [record["evidence_kind"] for record in evidence_records])
        red_index, green_index = [case["steps"].index(record) for record in evidence_records]
        event_index = case["steps"].index(event)
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        self.assertLess(red_index, event_index)
        self.assertLess(event_index, edit_index)
        self.assertLess(edit_index, green_index)
        self.assertEqual(
            [],
            self._implementation_errors(case),
        )

    def test_adaptive_testing_accepts_each_qualified_approach(self) -> None:
        for approach in (
            "test-first",
            "test-after",
            "existing-proof-only",
            "non-test-validation",
        ):
            with self.subTest(approach=approach):
                case, _guard, _records = self._adaptive_case(approach)
                self.assertEqual(
                    [],
                    self._implementation_errors(case),
                )

    def test_adaptive_testing_rejects_invalid_red_failure_classes(self) -> None:
        for failure_class in ("environment", "fixture", "import", "syntax", "unrelated"):
            with self.subTest(failure_class=failure_class):
                case, _guard, records = self._adaptive_case("test-first")
                records["red"]["failure_class"] = failure_class
                errors = self._implementation_errors(case)
                self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_adaptive_testing_rejects_weakened_assertion_and_wrong_order(self) -> None:
        case, _guard, records = self._adaptive_case("test-first")
        records["green"]["assertion"] = "the process returned"
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

        case, _guard, records = self._adaptive_case("test-first")
        case["steps"].remove(records["red"])
        edit_index = next(i for i, step in enumerate(case["steps"]) if step.get("action") == "edit")
        case["steps"].insert(edit_index + 1, records["red"])
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_adaptive_testing_rejects_stale_existing_proof_and_non_test_excuses(self) -> None:
        case, _guard, records = self._adaptive_case("existing-proof-only")
        records["existing-proof"]["freshness"] = 0
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

        case, guard, _records = self._adaptive_case("non-test-validation")
        guard["change_kind"] = "behavior"
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_adaptive_testing_rejects_fabricated_non_behavior_red_and_high_risk_downgrade(self) -> None:
        case, guard, _records = self._adaptive_case("non-test-validation")
        guard["approach"] = "test-first"
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

        case, guard, _records = self._adaptive_case("test-after")
        guard["risk_triggers"] = ["permission"]
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_persistent_adaptive_testing_fixture_matrix_matches_expectations(self) -> None:
        results, errors = EVAL._adaptive_testing_fixture_results(
            copy.deepcopy(self.adaptive_testing_cases)
        )
        self.assertEqual([], errors)
        self.assertEqual(15, len(results))
        self.assertTrue(all(result["matches_expected"] for result in results))
        self.assertEqual(4, sum(result["actual_valid"] for result in results))
        ids = {result["id"] for result in results}
        self.assertTrue(
            {
                "adaptive-test-first-valid",
                "adaptive-test-after-valid",
                "adaptive-existing-proof-valid",
                "adaptive-non-test-valid",
                "adaptive-rejects-weakened-assertion",
                "adaptive-rejects-red-after-edit",
                "adaptive-rejects-stale-existing-proof",
                "adaptive-rejects-non-test-excuse",
                "adaptive-rejects-non-behavior-red-green",
                "adaptive-rejects-high-risk-downgrade",
            }
            <= ids
        )

    def test_full_edit_trajectory_requires_guard_g(self) -> None:
        case = self._release_case("single-file-bug-fix")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "adaptive-test-evidence"
        ]
        event = self._discipline_event(case)
        event["evidence"] = [
            item
            for item in event["evidence"]
            if item.get("guard") != "guard-g-adaptive-testing"
        ]
        errors = self._implementation_errors(case)
        self.assertEqual(
            [
                f"{case['id']}: [implementation-discipline-missing-evidence] "
                f"missing guard evidence {[EVAL.IMPLEMENTATION_GUARD_CODES['G']]}"
            ],
            errors,
        )

    def test_adaptive_proof_must_follow_the_final_material_edit(self) -> None:
        case, _guard, records = self._adaptive_case("test-first")
        green_index = case["steps"].index(records["green"])
        case["steps"].insert(
            green_index + 1,
            {
                "actor": "task-agent",
                "action": "edit",
                "task_id": self._discipline_event(case)["task_id"],
                "path": "owner.py",
            },
        )
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_migration_cannot_hide_high_risk_with_low_risk_test_after(self) -> None:
        case = self._release_case("data-migration")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "adaptive-test-evidence"
        ]
        event = self._discipline_event(case)
        event["evidence"] = [
            item
            for item in event["evidence"]
            if item.get("guard") != "guard-g-adaptive-testing"
        ]
        event["evidence"].append(
            {
                "guard": "guard-g-adaptive-testing",
                "change_kind": "behavior",
                "approach": "test-after",
                "reason": "reported as low-risk local exploration",
                "failure_mechanism": "migration compatibility changes",
                "boundary": "schema migration boundary",
                "oracle": "migration compatibility result",
                "risk_triggers": ["low-risk-local-exploration"],
                "evidence": ["migration-green"],
                "proof_boundary": "migration fixture only",
            }
        )
        final_edit = max(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") in EVAL.EDIT_ACTIONS
        )
        case["steps"].insert(
            final_edit + 1,
            {
                "actor": "task-agent",
                "action": "adaptive-test-evidence",
                "task_id": event["task_id"],
                "evidence_id": "migration-green",
                "evidence_kind": "green",
                "result": "passed",
                "failure_class": "none",
                "oracle": "migration compatibility result",
                "assertion": "migration remains compatible",
                "freshness": 1,
            },
        )
        errors = self._implementation_errors(case)
        self.assertIn(EVAL.IMPLEMENTATION_GUARD_CODES["G"], self._error_codes(errors))

    def test_implementation_discipline_accepts_post_analysis_implementation(
        self,
    ) -> None:
        self.assertEqual(
            [],
            self._trajectory_errors(self._release_case("single-module-feature")),
        )

    def test_internal_discipline_evidence_does_not_emit_user_feedback(self) -> None:
        expectations = {
            "single-file-bug-fix": {
                "time_to_first_productive_action_step": 2,
                "time_to_first_edit_step": 3,
                "control_turn_count": 4,
                "progress_count": 0,
            },
            "single-module-feature": {
                "time_to_first_productive_action_step": 3,
                "time_to_first_edit_step": 8,
                "control_turn_count": 8,
                "progress_count": 3,
            },
        }
        for case_id, expected in expectations.items():
            with self.subTest(case=case_id):
                case = self._release_case(case_id)
                metrics, errors = self._trajectory_metrics(case)
                self.assertEqual([], errors)
                adaptive_indexes = {
                    index
                    for index, step in enumerate(case["steps"])
                    if step.get("action") == "adaptive-test-evidence"
                }
                operational_steps, internal_indexes = EVAL._operational_steps(case["steps"])
                self.assertTrue(adaptive_indexes <= internal_indexes)
                self.assertFalse(
                    any(
                        step.get("action") == "adaptive-test-evidence"
                        for step in operational_steps
                    )
                )
                expected_implementation_internal_indexes = {
                    index
                    for index, step in enumerate(case["steps"])
                    if step.get("actor") == "task-agent"
                    and (
                        step.get("action") in EVAL.INTERNAL_EVIDENCE_ACTIONS
                        or (
                            step.get("action") == "read"
                            and step.get("read_kind")
                            in EVAL.IMPLEMENTATION_SOURCE_READ_KINDS
                        )
                    )
                }
                actual_implementation_internal_indexes = {
                    index
                    for index in internal_indexes
                    if case["steps"][index].get("actor") == "task-agent"
                }
                self.assertEqual(
                    expected_implementation_internal_indexes,
                    actual_implementation_internal_indexes,
                )
                self.assertEqual(
                    len(expected_implementation_internal_indexes),
                    metrics["implementation_internal_evidence_event_count"],
                )
                self.assertFalse(
                    any(
                        step.get("action") in EVAL.INTERNAL_EVIDENCE_ACTIONS
                        or (
                            step.get("action") == "read"
                            and step.get("read_kind")
                            in EVAL.IMPLEMENTATION_SOURCE_READ_KINDS
                        )
                        for step in operational_steps
                    )
                )
                self.assertEqual(
                    len(case["steps"]) - len(internal_indexes),
                    metrics["total_completion_steps"],
                )
                for metric, value in expected.items():
                    self.assertEqual(value, metrics[metric])
                maximum_silence = case["expected"].get("max_silent_steps_max")
                if maximum_silence is not None:
                    self.assertLessEqual(
                        metrics["max_silent_steps"],
                        maximum_silence,
                    )

    def test_anchored_typed_evidence_remains_internal(self) -> None:
        case = self._release_case("single-file-bug-fix")
        operational, internal = EVAL._operational_steps(case["steps"])
        anchored_indexes = {
            index
            for index, step in enumerate(case["steps"])
            if (
                tuple(step)
                in {
                    EVAL.IMPLEMENTATION_ANCHORED_READ_FIELDS,
                    EVAL.IMPLEMENTATION_ANCHORED_TEST_READ_FIELDS,
                    EVAL.ADAPTIVE_TEST_ANCHORED_EVIDENCE_FIELDS,
                }
            )
        }
        self.assertTrue(anchored_indexes)
        self.assertTrue(anchored_indexes <= internal)
        self.assertFalse(
            any(
                id(step)
                in {id(case["steps"][index]) for index in anchored_indexes}
                for step in operational
            )
        )
        metrics, errors = self._trajectory_metrics(case)
        self.assertEqual([], errors)
        self.assertEqual(3, metrics["time_to_first_edit_step"])
        self.assertEqual(0, metrics["duplicate_read_count"])

    def test_operational_reads_still_count_for_silence_and_duplication(self) -> None:
        case = self._release_case("single-module-feature")
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        case["steps"][edit_index:edit_index] = [
            {"actor": "task-agent", "action": "read", "path": "module-a/service.py"},
            {"actor": "task-agent", "action": "read", "path": "module-a/service.py"},
        ]
        metrics, _errors = self._trajectory_metrics(case)
        self.assertEqual(2, metrics["duplicate_read_count"])
        self.assertEqual(6, metrics["max_silent_steps"])
        self.assertFalse(metrics["required_multi_agent_progress_satisfied"])

    def test_structural_load_transfer_counters_are_derived_from_trajectory(self) -> None:
        case = self._release_case("single-module-feature")
        metrics, errors = self._trajectory_metrics(case)
        self.assertEqual([], errors)
        dispatches = [
            step for step in case["steps"] if step.get("action") == "dispatch"
        ]
        expected_selectors = sum(
            bool(step.get("primary_skill") or step.get("layer3_skills"))
            for step in dispatches
        )
        expected_references = sum(
            len(step.get("professional_references", []))
            + len(step.get("layer3_references", []))
            for step in dispatches
        )
        self.assertEqual(expected_selectors, metrics["selector_load_count"])
        self.assertEqual(expected_references, metrics["reference_load_count"])
        self.assertEqual(0, metrics["same_assignment_duplicate_read_count"])
        self.assertGreater(metrics["handoff_count"], 0)
        self.assertEqual(
            metrics["selector_load_count"]
            + metrics["reference_load_count"]
            + metrics["handoff_count"],
            metrics["end_to_end_context_occurrence_count"],
        )

    def test_minimal_transfer_projection_omits_recomputable_policy_payloads(self) -> None:
        case = self._release_case("single-module-feature")
        task_dispatch = next(
            step
            for step in case["steps"]
            if step.get("action") == "dispatch" and step.get("profile") == "task-agent"
        )
        task_transfer = EVAL._minimal_transfer_projection(task_dispatch)
        self.assertEqual("task-agent", task_transfer["profile"])
        serialized = json.dumps(task_transfer, sort_keys=True)
        for forbidden in (
            "trigger_evaluations",
            "l1_eligibility",
            "l2_eligibility",
            "l5_assurance_eligibility",
            "engineering_brief",
            "task_dag",
            "superseded_evidence",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("execution_level_role_projection", serialized)

        handoff = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "implementation-handoff"
        )
        projected_handoff = EVAL._minimal_transfer_projection(handoff)
        self.assertEqual(
            {
                "actor",
                "action",
                "handoff_id",
                "task_id",
                "latest_changed_paths",
                "exact_change_evidence",
                "reviewer_artifact_accessibility",
                "validation_after_latest_material_edit",
                "fixed_review_scope",
            },
            set(projected_handoff),
        )

    def test_utility_dispatch_omits_execution_level_projection_only_for_typed_modes(self) -> None:
        for case in self.utility_cases:
            dispatch = next(
                step
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
            )
            projected = EVAL._minimal_transfer_projection(dispatch)
            capsule = projected["fixture_capsule"]
            with self.subTest(case=case["id"]):
                self.assertEqual("utility", capsule["contract_type"])
                self.assertNotIn("execution_level_role_projection", capsule)
                self.assertEqual(
                    dispatch["mode"], projected["utility_capsule"]["mode"]
                )
                self.assertNotIn(
                    "execution_level_role_projection", projected["utility_capsule"]
                )

            for mutation in (
                "implementation-mode",
                "task-contract",
                "task-template",
                "primary-skill",
            ):
                changed = copy.deepcopy(dispatch)
                if mutation == "implementation-mode":
                    changed["mode"] = "implementation"
                elif mutation == "task-contract":
                    changed["fixture_capsule"]["contract_type"] = "task"
                elif mutation == "task-template":
                    changed["fixture_capsule"]["template"] = "implementation-task"
                else:
                    changed["primary_skill"] = "repository-tooling-change-builder"
                with self.subTest(case=case["id"], mutation=mutation):
                    with self.assertRaisesRegex(
                        ValueError,
                        "worker dispatch requires Main Level projection source",
                    ):
                        EVAL._minimal_transfer_projection(changed)

            changed = copy.deepcopy(dispatch)
            changed["utility_capsule"]["mode"] = "unknown/no-edit"
            with self.subTest(case=case["id"], mutation="capsule-mode-mismatch"):
                with self.assertRaisesRegex(
                    ValueError,
                    "worker dispatch requires Main Level projection source",
                ):
                    EVAL._minimal_transfer_projection(changed)

    def test_native_structural_measurement_fails_closed_on_incomplete_dispatch(self) -> None:
        case = self._release_case("single-module-feature")
        metrics = EVAL._native_structural_metrics(case)
        self.assertEqual(
            metrics["selector_load_count"]
            + metrics["reference_load_count"]
            + metrics["handoff_count"],
            metrics["end_to_end_context_occurrence_count"],
        )

        for mutation in ("missing-profile", "missing-capsule", "malformed-capsule"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(case)
                dispatch = next(
                    step for step in changed["steps"] if step.get("action") == "dispatch"
                )
                if mutation == "missing-profile":
                    dispatch.pop("profile")
                elif mutation == "missing-capsule":
                    dispatch.pop("fixture_capsule", None)
                    dispatch.pop("utility_capsule", None)
                else:
                    dispatch["utility_capsule"] = "not-a-native-capsule"
                with self.assertRaises(ValueError):
                    EVAL._native_structural_metrics(changed)

    def test_same_assignment_duplicate_reads_do_not_cross_task_boundaries(self) -> None:
        base = [
            {
                "actor": "task-agent",
                "action": "read",
                "task_id": "task-a",
                "path": "owner.py",
            },
            {
                "actor": "task-agent",
                "action": "read",
                "task_id": "task-b",
                "path": "owner.py",
            },
        ]
        self.assertEqual(1, EVAL._duplicate_reads(base))
        self.assertEqual(0, EVAL._same_assignment_duplicate_reads(base))
        base[1]["task_id"] = "task-a"
        self.assertEqual(1, EVAL._same_assignment_duplicate_reads(base))

    def test_native_structural_selection_requires_reference_pair_and_deduplicates_assignment(self) -> None:
        case = self._release_case("single-module-feature")
        dispatch = next(
            step for step in case["steps"] if step.get("action") == "dispatch"
        )
        for missing in ("professional_references", "layer3_references"):
            changed = copy.deepcopy(case)
            target = next(
                step
                for step in changed["steps"]
                if step.get("action") == "dispatch"
            )
            target.pop(missing)
            with self.subTest(missing=missing):
                self.assertEqual(
                    EVAL._selector_load_count(changed["steps"]),
                    EVAL._native_structural_metrics(changed)["selector_load_count"],
                )

        repeated = [copy.deepcopy(dispatch), copy.deepcopy(dispatch)]
        self.assertEqual(1, EVAL._selector_load_count(repeated))
        assignment_field = next(
            field
            for field in (
                "task_id",
                "review_round_id",
                "analysis_id",
                "canonical_sha256",
            )
            if field in repeated[1]["fixture_capsule"]
        )
        repeated[1]["fixture_capsule"][assignment_field] += "-next"
        self.assertEqual(2, EVAL._selector_load_count(repeated))

    def test_all_normal_edit_trajectories_have_typed_discipline(self) -> None:
        for original in self.release_cases:
            if not any(
                step.get("actor") == "task-agent"
                and step.get("action") in EVAL.EDIT_ACTIONS
                for step in original["steps"]
            ):
                continue
            with self.subTest(case=original["id"]):
                case = copy.deepcopy(original)
                self.assertEqual(
                    [],
                    self._implementation_errors(case),
                )

    def test_implementation_discipline_mutation_matrix_rejects_each_guard_on_both_paths(
        self,
    ) -> None:
        guard_codes = EVAL.IMPLEMENTATION_GUARD_CODES
        mutations = (
            (
                "A",
                lambda event: event["evidence"][0]["read_evidence"].pop(1),
            ),
            (
                "B",
                lambda event: event["evidence"][1].__setitem__(
                    "owner_verified", False
                ),
            ),
            (
                "C",
                lambda event: event["evidence"][2]["outcome_matrix"].pop(
                    "forbidden"
                ),
            ),
            (
                "D",
                lambda event: event["evidence"][3].__setitem__(
                    "applies", not event["evidence"][3]["applies"]
                ),
            ),
            (
                "E",
                lambda event: event["evidence"][4].__setitem__(
                    "dependency_direction_resolved", False
                ),
            ),
            (
                "F",
                lambda event: event["evidence"][5].__setitem__(
                    "unrelated_refactor", True
                ),
            ),
        )
        paths = ("single-file-bug-fix", "single-module-feature")
        observed: set[tuple[str, str]] = set()
        for case_id in paths:
            for guard_key, mutate in mutations:
                with self.subTest(path=case_id, guard=guard_key):
                    case = self._release_case(case_id)
                    mutate(self._discipline_event(case))
                    errors = self._trajectory_errors(case)
                    self.assertIn(guard_codes[guard_key], self._error_codes(errors))
                    observed.add((case_id, guard_key))
        self.assertEqual(12, len(observed))

    def test_implementation_discipline_rejects_missing_event_before_edit(self) -> None:
        case = self._release_case("single-file-bug-fix")
        case["steps"] = [
            step
            for step in case["steps"]
            if step.get("action") != "implementation-discipline"
        ]
        errors = self._trajectory_errors(case)
        self.assertIn(
            "implementation-discipline-missing-event",
            self._error_codes(errors),
        )

    def test_implementation_discipline_evidence_is_closed_unique_and_ordered(
        self,
    ) -> None:
        variants = (
            (
                "implementation-discipline-missing-evidence",
                lambda event: event["evidence"].pop(),
            ),
            (
                "implementation-discipline-duplicate-evidence",
                lambda event: event["evidence"].__setitem__(
                    5, copy.deepcopy(event["evidence"][0])
                ),
            ),
            (
                "implementation-discipline-unknown-evidence",
                lambda event: event["evidence"][5].__setitem__(
                    "guard", "unknown-guard"
                ),
            ),
            (
                "implementation-discipline-evidence-order",
                lambda event: event["evidence"].__setitem__(
                    slice(0, 2), list(reversed(event["evidence"][0:2]))
                ),
            ),
            (
                "implementation-discipline-event-schema",
                lambda event: event.__setitem__("unknown_field", True),
            ),
            (
                EVAL.IMPLEMENTATION_GUARD_CODES["B"],
                lambda event: event["evidence"][1].__setitem__(
                    "unknown_field", True
                ),
            ),
        )
        for expected_code, mutate in variants:
            with self.subTest(code=expected_code):
                case = self._release_case("single-file-bug-fix")
                mutate(self._discipline_event(case))
                self.assertIn(
                    expected_code,
                    self._error_codes(self._trajectory_errors(case)),
                )

    def test_implementation_discipline_rejects_edit_before_evidence(self) -> None:
        case = self._release_case("single-file-bug-fix")
        event_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("action") == "implementation-discipline"
        )
        event = case["steps"].pop(event_index)
        edit_index = next(
            index
            for index, step in enumerate(case["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        case["steps"].insert(edit_index + 1, event)
        self.assertIn(
            EVAL.IMPLEMENTATION_GUARD_CODES["order"],
            self._error_codes(self._trajectory_errors(case)),
        )

    def test_guard_c_binds_exact_validation_evidence_id_or_command(self) -> None:
        for case_id in ("single-file-bug-fix", "single-module-feature"):
            with self.subTest(case=case_id):
                case = self._release_case(case_id)
                self.assertNotIn(
                    EVAL.IMPLEMENTATION_GUARD_CODES["C"],
                    self._error_codes(
                        self._implementation_errors(case)
                    ),
                )

    def test_guard_c_rejects_ambiguous_stale_and_nonpassing_validation(self) -> None:
        variants: dict[str, dict] = {}

        ambiguous = self._release_case("single-file-bug-fix")
        validation_index = next(
            index
            for index, step in enumerate(ambiguous["steps"])
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        ambiguous["steps"].insert(
            validation_index + 1,
            copy.deepcopy(ambiguous["steps"][validation_index]),
        )
        variants["ambiguous"] = ambiguous

        stale = self._release_case("single-file-bug-fix")
        validation_index = next(
            index
            for index, step in enumerate(stale["steps"])
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation = stale["steps"].pop(validation_index)
        edit_index = next(
            index
            for index, step in enumerate(stale["steps"])
            if step.get("actor") == "task-agent" and step.get("action") == "edit"
        )
        stale["steps"].insert(edit_index, validation)
        variants["pre-final-edit"] = stale

        nonpassing = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in nonpassing["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["outcome"] = "failed"
        variants["nonpassing"] = nonpassing

        for label, case in variants.items():
            with self.subTest(variant=label):
                errors = self._implementation_errors(case)
                self.assertIn(
                    EVAL.IMPLEMENTATION_GUARD_CODES["C"],
                    self._error_codes(errors),
                )

    def test_shared_validation_uses_one_closed_multi_task_binding(self) -> None:
        case = self._release_case("isolated-write-parallel-contract")
        shared = [
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
            and step.get("evidence_id") == "isolated-module-tests"
        ]
        self.assertEqual(1, len(shared))
        self.assertNotIn("task_id", shared[0])
        self.assertEqual(
            [
                "task-isolated-write-parallel-contract-1",
                "task-isolated-write-parallel-contract-2",
            ],
            shared[0]["task_ids"],
        )
        self.assertEqual(
            [],
            self._implementation_errors(case),
        )

    def test_validation_task_binding_rejects_duplicate_unknown_empty_and_both_forms(
        self,
    ) -> None:
        variants = {
            "duplicate": [
                "task-single-file-bug-fix-1",
                "task-single-file-bug-fix-1",
            ],
            "unknown": [
                "task-single-file-bug-fix-1",
                "unknown-task",
            ],
            "empty": [],
        }
        for label, task_ids in variants.items():
            with self.subTest(variant=label):
                case = self._release_case("single-file-bug-fix")
                validation = next(
                    step
                    for step in case["steps"]
                    if step.get("actor") == "task-agent"
                    and step.get("action") == "validate"
                )
                validation.pop("task_id")
                validation["task_ids"] = task_ids
                self.assertIn(
                    "validation-task-binding",
                    self._error_codes(
                        self._implementation_errors(case)
                    ),
                )

        case = self._release_case("single-file-bug-fix")
        validation = next(
            step
            for step in case["steps"]
            if step.get("actor") == "task-agent"
            and step.get("action") == "validate"
        )
        validation["task_ids"] = ["task-single-file-bug-fix-1"]
        self.assertIn(
            "validation-task-binding",
            self._error_codes(
                self._implementation_errors(case)
            ),
        )

    def test_fixture_groups_include_release_scheduling_and_utility_contracts(self) -> None:
        self.assertEqual(13, len(self.release_cases))
        self.assertEqual(1, len(self.scheduling_cases))
        self.assertEqual(2, len(self.utility_cases))
        expected_scopes = {
            "review-supplied-artifact-missing-diff": "requested utility workspace scope",
            "validation-task-no-edit": "named validation workspace scope",
        }
        for case in self.utility_cases:
            with self.subTest(case=case["id"]):
                assignment = case["steps"][1]["utility_capsule"]
                self.assertEqual(1, len(assignment["evidence_ledger"]))
                row = assignment["evidence_ledger"][0]
                self.assertEqual(CANONICAL_LEDGER_FIELDS, tuple(row))
                self.assertTrue(set(RETIRED_LEDGER_FIELDS).isdisjoint(row))
                self.assertEqual(
                    {
                        "Claim": "workspace baseline captured",
                        "Owner": assignment["owner"],
                        "Artifact": "workspace baseline evidence",
                        "Command": "declared read-only workspace checks",
                        "Result": "tracked staged and untracked baseline recorded",
                        "Freshness": 0,
                        "Scope": expected_scopes[case["id"]],
                        "Proof Limit": (
                            "baseline does not prove post-operation workspace state"
                        ),
                        "State": "current",
                    },
                    row,
                )
                self.assertEqual([], self._errors(copy.deepcopy(case)))

    def test_assignment_baseline_claim_requires_current_canonical_state(self) -> None:
        original = copy.deepcopy(self.utility_cases[0])
        self.assertEqual([], self._errors(copy.deepcopy(original)))

        for state in ("superseded", "invalid"):
            with self.subTest(state=state):
                case = copy.deepcopy(original)
                row = case["steps"][1]["utility_capsule"]["evidence_ledger"][0]
                row["State"] = state
                errors = self._errors(case)
                self.assertTrue(
                    any(
                        "Utility Assignment missing current evidence for "
                        "'workspace baseline captured'" in error
                        for error in errors
                    ),
                    errors,
                )

        case = copy.deepcopy(original)
        case["steps"][1]["utility_capsule"]["evidence_ledger"] = []
        errors = self._errors(case)
        self.assertTrue(
            any(
                "Utility Assignment missing current evidence for "
                "'workspace baseline captured'" in error
                for error in errors
            ),
            errors,
        )

    def test_completion_state_negative_controls_match_static_contract(self) -> None:
        results, errors = EVAL._completion_fixture_errors(
            copy.deepcopy(self.completion_state_cases),
            copy.deepcopy(self.release_cases),
        )
        self.assertEqual([], errors)
        self.assertEqual(30, len(results))
        self.assertTrue(all(item["matches_expected"] for item in results))
        expected_rules = {
            "validation-failed",
            "validation-unavailable",
            "high-risk-review-missing",
            "blocking-finding-unresolved",
            "changed-scope-unreviewed",
            "evidence-stale-after-edit",
        }
        observed_rules = {
            case["expected_error"]
            for case in self.completion_state_cases
            if case.get("expected_error") in expected_rules
        }
        self.assertEqual(expected_rules, observed_rules)

    def test_evidence_ledger_negative_controls_are_enforced(self) -> None:
        results, errors = EVAL._completion_fixture_errors(
            copy.deepcopy(self.completion_state_cases),
            copy.deepcopy(self.release_cases),
        )
        self.assertEqual([], errors)
        by_id = {item["id"]: item for item in results}
        expected_negative_ids = {
            "completed-rejects-validation-not-required",
            "completed-rejects-missing-validation-evidence",
            "completed-rejects-erased-latest-edit-marker",
            "completed-rejects-review-self-attestation",
            "completed-rejects-single-review-owner-for-all-evidence",
            "ledger-rejects-legacy-evidence-id",
            "ledger-rejects-invalid-state",
            "ledger-rejects-legacy-task-id",
            "ledger-rejects-legacy-action",
            "ledger-rejects-legacy-freshness-marker",
            "ledger-rejects-support-from-superseded-evidence",
            "ledger-rejects-legacy-evidence-state",
            "ledger-rejects-legacy-supersedes",
            "ledger-rejects-support-from-invalid-evidence",
            "ledger-rejects-artifact-scope-mismatch",
            "ledger-rejects-proof-limit-scope-mismatch",
        }
        self.assertTrue(expected_negative_ids <= set(by_id))
        for case_id in expected_negative_ids:
            with self.subTest(case_id=case_id):
                self.assertFalse(by_id[case_id]["actual_valid"])
                self.assertTrue(by_id[case_id]["matches_expected"])

    def test_completion_freshness_is_derived_from_ledger_rows(self) -> None:
        for case in self.completion_state_cases:
            self.assertNotIn("evidence_fresh", case["claim"])

    def test_fixture_ledgers_are_canonical_except_tagged_legacy_negatives(
        self,
    ) -> None:
        tagged_case_ids: set[str] = set()
        for case in self.completion_state_cases:
            tags = case.get("tags", [])
            self.assertIn(tags, ([], [LEGACY_NEGATIVE_TAG]))
            if tags:
                tagged_case_ids.add(case["id"])
                self.assertFalse(case["expected_valid"])
                self.assertIn(
                    "retired Evidence Ledger field",
                    case["expected_error"],
                )
            for row in case["claim"]["evidence_ledger"]:
                retired = [field for field in RETIRED_LEDGER_FIELDS if field in row]
                with self.subTest(case=case["id"], claim=row.get("Claim")):
                    if tags:
                        self.assertEqual(1, len(retired))
                        self.assertEqual(
                            CANONICAL_LEDGER_FIELDS,
                            tuple(field for field in row if field not in retired),
                        )
                        self.assertEqual(
                            set(CANONICAL_LEDGER_FIELDS) | set(retired),
                            set(row),
                        )
                    else:
                        self.assertEqual([], retired)
                        self.assertEqual(CANONICAL_LEDGER_FIELDS, tuple(row))

        self.assertEqual(
            {
                "ledger-rejects-legacy-evidence-id",
                "ledger-rejects-legacy-task-id",
                "ledger-rejects-legacy-action",
                "ledger-rejects-legacy-freshness-marker",
                "ledger-rejects-legacy-evidence-state",
                "ledger-rejects-legacy-supersedes",
            },
            tagged_case_ids,
        )

        ledgers = []
        for case in self.utility_cases:
            ledgers.extend(
                (
                    case["steps"][1]["utility_capsule"]["evidence_ledger"],
                    case["steps"][2]["utility_evidence"]["evidence_ledger"],
                )
            )
        for ledger in ledgers:
            for row in ledger:
                with self.subTest(claim=row.get("Claim")):
                    self.assertEqual(CANONICAL_LEDGER_FIELDS, tuple(row))
                    self.assertTrue(set(RETIRED_LEDGER_FIELDS).isdisjoint(row))

    def test_negative_fixtures_encode_structured_ledger_invariants(self) -> None:
        by_id = {case["id"]: case for case in self.completion_state_cases}
        legacy_fields = {
            "ledger-rejects-legacy-evidence-id": "Evidence ID",
            "ledger-rejects-legacy-task-id": "Task ID",
            "ledger-rejects-legacy-action": "Action",
            "ledger-rejects-legacy-freshness-marker": "Freshness Marker",
            "ledger-rejects-legacy-evidence-state": "Evidence State",
            "ledger-rejects-legacy-supersedes": "Supersedes",
        }
        for case_id, field in legacy_fields.items():
            with self.subTest(case=case_id):
                case = by_id[case_id]
                self.assertEqual([LEGACY_NEGATIVE_TAG], case["tags"])
                self.assertIn(field, case["claim"]["evidence_ledger"][0])

        stale = by_id["completed-rejects-stale-evidence"]["claim"]
        self.assertEqual(stale["latest_material_edit_marker"], 2)
        self.assertLess(
            stale["evidence_ledger"][0]["Freshness"],
            stale["latest_material_edit_marker"],
        )
        self.assertEqual("current", stale["evidence_ledger"][0]["State"])
        self.assertEqual(
            "fresh",
            by_id["ledger-rejects-invalid-state"]["claim"]["evidence_ledger"][0][
                "State"
            ],
        )
        self.assertEqual(
            "superseded",
            by_id["ledger-rejects-support-from-superseded-evidence"]["claim"][
                "evidence_ledger"
            ][0]["State"],
        )
        self.assertEqual(
            "invalid",
            by_id["ledger-rejects-support-from-invalid-evidence"]["claim"][
                "evidence_ledger"
            ][0]["State"],
        )

        artifact_scope = by_id["ledger-rejects-artifact-scope-mismatch"]["claim"][
            "evidence_ledger"
        ][0]
        self.assertEqual("other.py", artifact_scope["Artifact"])
        self.assertEqual("owner.py", artifact_scope["Scope"])
        proof_scope = by_id["ledger-rejects-proof-limit-scope-mismatch"]["claim"][
            "evidence_ledger"
        ][0]
        self.assertIn("other.py", proof_scope["Proof Limit"])
        self.assertEqual("owner.py", proof_scope["Scope"])

    def test_retired_ledger_fields_cannot_be_reintroduced(self) -> None:
        base = copy.deepcopy(self.completion_state_cases[0]["claim"])
        retired_values = {
            "Evidence ID": "legacy-evidence-id",
            "Task ID": base["task_id"],
            "Action": "validate",
            "Freshness Marker": 2,
            "Evidence State": "current",
            "Supersedes": [],
        }
        for field, value in retired_values.items():
            with self.subTest(field=field):
                claim = copy.deepcopy(base)
                claim["evidence_ledger"][0][field] = value
                errors = EVAL.completion_claim_errors(claim)
                self.assertTrue(
                    any(
                        "retired Evidence Ledger field" in error and field in error
                        for error in errors
                    ),
                    errors,
                )

        claim = copy.deepcopy(base)
        row = claim["evidence_ledger"][0]
        claim["evidence_ledger"][0] = {
            "Evidence ID": "legacy-evidence-id",
            "Task ID": claim["task_id"],
            "Owner": row["Owner"],
            "Claim": row["Claim"],
            "Action": "validate",
            "Artifact": row["Artifact"],
            "Command": row["Command"],
            "Result": row["Result"],
            "Freshness Marker": row["Freshness"],
            "Scope": row["Scope"],
            "Proof Limit": row["Proof Limit"],
            "Evidence State": row["State"],
            "Supersedes": [],
        }
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("retired Evidence Ledger fields" in error for error in errors),
            errors,
        )

    def test_artifact_scope_and_proof_limit_paths_must_match_scope(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        row = next(
            item for item in claim["evidence_ledger"] if item["Claim"] == "requested-result"
        )
        row["Scope"] = "other.py"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("evidence Scope mismatch" in error for error in errors), errors)

        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        row = next(
            item for item in claim["evidence_ledger"] if item["Claim"] == "requested-result"
        )
        row["Proof Limit"] = "proof covers other.py only"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("evidence Proof Limit mismatch" in error for error in errors),
            errors,
        )

    def test_canonical_ledger_fields_are_structurally_validated(self) -> None:
        base = next(
            case["claim"]
            for case in self.completion_state_cases
            if case["id"] == "diagnosis-completed-when-fully-delivered"
        )
        for field in (
            "Claim",
            "Owner",
            "Artifact",
            "Command",
            "Result",
            "Scope",
            "Proof Limit",
        ):
            with self.subTest(field=field):
                claim = copy.deepcopy(base)
                claim["evidence_ledger"][0][field] = ""
                errors = EVAL.completion_claim_errors(claim)
                self.assertTrue(
                    any(f"{field} must be non-empty text" in error for error in errors),
                    errors,
                )

        claim = copy.deepcopy(base)
        claim["evidence_ledger"][0]["Claim"] = "unrequired-claim"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("missing current evidence for required claim" in error for error in errors),
            errors,
        )

        claim = copy.deepcopy(base)
        claim["evidence_ledger"][0]["Owner"] = "another-agent"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("Owner must equal" in error for error in errors), errors)

    def test_completed_implementation_requires_current_independent_review_rows(self) -> None:
        by_id = {case["id"]: case for case in self.completion_state_cases}
        valid = copy.deepcopy(
            by_id["implementation-completed-with-current-evidence"]["claim"]
        )
        owners = {row["Owner"] for row in valid["evidence_ledger"]}
        self.assertEqual({"task-agent", "review-agent"}, owners)
        self.assertEqual([], EVAL.completion_claim_errors(valid))

        self_attested = copy.deepcopy(
            by_id["completed-rejects-review-self-attestation"]["claim"]
        )
        errors = EVAL.completion_claim_errors(self_attested)
        self.assertTrue(
            any("independent review evidence" in error for error in errors),
            errors,
        )

    def test_completed_implementation_rejects_review_before_latest_edit(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        for row in claim["evidence_ledger"]:
            if row["Owner"] == "review-agent":
                row["Freshness"] = 1
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("independent review evidence" in error for error in errors),
            errors,
        )

    def test_completed_implementation_requires_current_validation_evidence(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["validation"] = "not-required"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("requires validation='passed'" in error for error in errors),
            errors,
        )

        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["evidence_ledger"] = [
            row
            for row in claim["evidence_ledger"]
            if row["Claim"] != "validation-passed"
        ]
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("validation-passed" in error for error in errors), errors)

    def test_completed_implementation_rejects_erased_or_lowered_edit_marker(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["latest_material_edit_marker"] = None
        claim["required_freshness_marker"] = 1
        for row in claim["evidence_ledger"]:
            if row["Owner"] == "review-agent":
                row["Freshness"] = 1
                row["Artifact"] = "previous diff before repair"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("latest_material_edit_marker" in error for error in errors),
            errors,
        )

        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["required_freshness_marker"] = 1
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("required_freshness_marker" in error for error in errors),
            errors,
        )

    def test_completed_implementation_rejects_unassigned_evidence_owner(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["evidence_ledger"][-1]["Owner"] = "another-agent"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("Owner must be one of" in error for error in errors), errors)

    def test_completed_implementation_requires_distinct_task_and_review_owners(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim["owner"] = "review-agent"
        for row in claim["evidence_ledger"]:
            row["Owner"] = "review-agent"
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(
            any("owner must equal 'task-agent'" in error for error in errors),
            errors,
        )

    def test_completion_state_allows_fully_delivered_diagnosis_and_answer(self) -> None:
        by_id = {case["id"]: case for case in self.completion_state_cases}
        for case_id in (
            "diagnosis-completed-when-fully-delivered",
            "answer-completed-when-fully-delivered",
        ):
            with self.subTest(case_id=case_id):
                claim = by_id[case_id]["claim"]
                self.assertEqual([], EVAL.completion_claim_errors(claim))

    def test_completion_claim_rejects_unknown_or_incomplete_shape(self) -> None:
        claim = copy.deepcopy(self.completion_state_cases[0]["claim"])
        claim.pop("proof_limits_stated")
        errors = EVAL.completion_claim_errors(claim)
        self.assertTrue(any("exact ordered fields" in error for error in errors), errors)

    def test_nested_reference_resolution_uses_runtime_compiled_delivery(self) -> None:
        self.assertNotEqual(
            (ROOT / "dist/universal/skills").resolve(),
            EVAL.DIST_SKILLS.resolve(),
        )
        runtime_manifest, errors = EVAL._load_runtime_manifest()
        self.assertEqual([], errors)
        assert runtime_manifest is not None
        rows = (
            ("recommended", "engineering-change-analysis", "test-strategy", "references/checklist.md", "compiled"),
            ("recommended", "engineering-change-analysis", "payment-trading-extension", "references/provider-venue-event-authentication.md", "compiled"),
            ("recommended", "high-risk-design-review", "module-boundary-design", "references/benchmarks-and-enforcement.md", "compiled"),
        )
        for profile, primary, owner, relative, delivery in rows:
            with self.subTest(profile=profile, owner=owner):
                resolved = EVAL._layer3_reference_build_path(
                    profile,
                    primary,
                    owner,
                    relative,
                    runtime_manifest,
                )
                compiled_path = (
                    EVAL.DIST_SKILLS
                    / profile
                    / primary
                    / "references"
                    / "layer3"
                    / owner
                    / relative
                )
                top_level_path = EVAL.DIST_SKILLS / profile / owner / relative
                expected = compiled_path if delivery == "compiled" else top_level_path
                alternate = top_level_path if delivery == "compiled" else compiled_path
                self.assertEqual(expected, resolved)
                self.assertTrue(resolved.is_file())
                self.assertFalse(alternate.exists())

    def test_lightweight_reference_resolution_requires_one_delivery_path(self) -> None:
        base = {
            "compiled_layer3_references": {"primary": []},
            "top_level_skills": [],
        }
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_build_path(
                "test",
                "primary",
                "owner",
                "references/checklist.md",
                copy.deepcopy(base),
            )

        dual = copy.deepcopy(base)
        dual["compiled_layer3_references"]["primary"] = ["owner"]
        dual["top_level_skills"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_build_path(
                "test",
                "primary",
                "owner",
                "references/checklist.md",
                dual,
            )

    def test_utility_dispatch_rejects_skill_and_layer3_selection(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        dispatch = case["steps"][1]
        dispatch["primary_skill"] = "backend-change-builder"
        dispatch["layer3_skills"] = []
        self.assertTrue(
            any("must not select a Professional Skill" in error for error in self._errors(case))
        )

    def test_utility_dispatch_rejects_layer3_reference_field_even_when_empty(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][1]["layer3_references"] = []
        errors = self._errors(case)
        self.assertTrue(
            any("Layer 3 Reference" in error or "layer3_references" in error for error in errors),
            errors,
        )

    def test_utility_capsule_and_evidence_require_exact_field_order(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        capsule = case["steps"][1]["utility_capsule"]
        capsule["goal"] = capsule.pop("goal")
        evidence = case["steps"][2]["utility_evidence"]
        evidence["commands_run"] = evidence.pop("commands_run")
        errors = self._errors(case)
        self.assertTrue(any("exact ordered fields" in error for error in errors), errors)

    def test_utility_rejects_unknown_mode(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        case["steps"][1]["utility_capsule"]["mode"] = "unknown/no-edit"
        case["steps"][2]["utility_evidence"]["mode"] = "unknown/no-edit"
        self.assertTrue(any("invalid mode" in error for error in self._errors(case)))

    def test_utility_return_must_match_assignment_identity_and_mode(self) -> None:
        mutations = (
            ("owner", "another utility owner", "Owner must match"),
            ("mode", "validation-only/no-edit", "mode must match"),
            ("no_edit_enforcement", "unsupported", "enforcement must match"),
        )
        for field, value, expected in mutations:
            with self.subTest(field=field):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][2]["utility_evidence"][field] = value
                self.assertTrue(
                    any(expected in error for error in self._errors(case)),
                    self._errors(case),
                )

    def test_utility_assignment_and_return_statuses_are_contract_gated(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][1]["utility_capsule"]["status"] = "partial"
        errors = self._errors(case)
        self.assertTrue(any("Utility Assignment Status" in error for error in errors), errors)

        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["utility_evidence"]["status"] = "in_progress"
        errors = self._errors(case)
        self.assertTrue(any("Utility Return Status" in error for error in errors), errors)

    def test_utility_task_id_stays_outside_ledger_and_owner_is_bound(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        capsule = case["steps"][1]["utility_capsule"]
        evidence = case["steps"][2]["utility_evidence"]
        self.assertEqual(capsule["task_id"], evidence["task_id"])
        self.assertTrue(all("Task ID" not in row for row in capsule["evidence_ledger"]))
        self.assertTrue(all("Task ID" not in row for row in evidence["evidence_ledger"]))
        evidence["task_id"] = "another-utility-task"
        errors = self._errors(case)
        self.assertTrue(any("Task ID must match" in error for error in errors), errors)
        self.assertFalse(any("Evidence ID" in error for error in errors), errors)

        case = copy.deepcopy(self.utility_cases[0])
        row = case["steps"][2]["utility_evidence"]["evidence_ledger"][-1]
        row["Owner"] = "another utility owner"
        errors = self._errors(case)
        self.assertTrue(any("Owner must equal" in error for error in errors), errors)

        case = copy.deepcopy(self.utility_cases[0])
        row = case["steps"][2]["utility_evidence"]["evidence_ledger"][-1]
        row["Task ID"] = case["steps"][2]["utility_evidence"]["task_id"]
        errors = self._errors(case)
        self.assertTrue(
            any("retired Evidence Ledger field" in error for error in errors),
            errors,
        )

    def test_completed_utility_requires_current_evidence_closure(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        result_row = case["steps"][2]["utility_evidence"]["evidence_ledger"][-1]
        self.assertEqual("utility result delivered", result_row["Claim"])
        result_row["State"] = "invalid"
        errors = self._errors(case)
        self.assertTrue(
            any("supported only by superseded or invalid evidence" in error for error in errors),
            errors,
        )

    def test_utility_case_rejects_any_edit(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        case["steps"].insert(
            2,
            {"actor": "task-agent", "action": "edit", "path": "owner.py"},
        )
        self.assertTrue(any("must not edit or repair" in error for error in self._errors(case)))

    def test_diff_export_must_precede_review(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2], case["steps"][3] = case["steps"][3], case["steps"][2]
        self.assertTrue(
            any("must precede review dispatch, read, and review" in error for error in self._errors(case))
        )

    def test_utility_rejects_network_command(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        command = "git fetch origin"
        case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
        case["steps"][2]["utility_evidence"]["commands_run"][1] = command
        self.assertTrue(any("unsafe command" in error for error in self._errors(case)))

    def test_validation_utility_rejects_mutating_command(self) -> None:
        case = copy.deepcopy(self.utility_cases[1])
        command = "touch owner.py"
        case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = command
        case["steps"][2]["utility_evidence"]["commands_run"][1] = command
        self.assertTrue(
            any("other than the declared validation check" in error for error in self._errors(case))
        )

    def test_generic_utility_rejects_native_tool_command_or_shell_identifiers(self) -> None:
        identifiers = (
            "git --no-pager diff --no-ext-diff --no-textconv HEAD~1..HEAD",
            "native-diff-tool",
            "change-evidence-export; mutate",
        )
        for identifier in identifiers:
            with self.subTest(identifier=identifier):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][1]["utility_capsule"]["commands_allowed"][-1] = identifier
                case["steps"][2]["utility_evidence"]["commands_run"][1] = identifier
                self.assertTrue(any("unsafe" in error for error in self._errors(case)))

    def test_generic_utility_accepts_only_normalized_operations(self) -> None:
        self.assertEqual(
            {
                "workspace-state-observation",
                "change-evidence-export",
                "validation-check",
                "evidence-workspace-preflight",
                "evidence-observation-operation",
                "evidence-workspace-postflight",
            },
            EVAL.UTILITY_OPERATIONS,
        )
        for operation in EVAL.UTILITY_OPERATIONS:
            with self.subTest(operation=operation):
                self.assertTrue(EVAL._utility_command_is_safe(operation))

    def test_workspace_observation_is_a_direct_declared_operation(self) -> None:
        for case in self.utility_cases:
            self.assertNotIn("host_modes", case)
            self.assertNotIn("capability_facts", case)
            checks = case["steps"][1]["utility_capsule"]["workspace_baseline"]["check_commands"]
            self.assertEqual(["workspace-state-observation"], checks)
            self.assertNotIn("git", " ".join(checks).casefold())

    def test_utility_workspace_changed_or_unavailable_blocks_downstream(self) -> None:
        for status in ("changed", "unavailable"):
            with self.subTest(status=status):
                case = copy.deepcopy(self.utility_cases[0])
                evidence = case["steps"][2]["utility_evidence"]
                evidence["status"] = "blocked"
                evidence["workspace_diff_check"]["status"] = status
                errors = self._errors(case)
                self.assertTrue(
                    any("invalid unless workspace diff status is unchanged" in error for error in errors),
                    errors,
                )
                self.assertTrue(
                    any("must not continue to review or closure" in error for error in errors),
                    errors,
                )

    def test_utility_requires_exact_pre_operation_post_observation_order(self) -> None:
        variants = {
            "operation-first": [
                "change-evidence-export",
                "workspace-state-observation",
                "workspace-state-observation",
            ],
            "operation-last": [
                "workspace-state-observation",
                "workspace-state-observation",
                "change-evidence-export",
            ],
            "interleaved": [
                "workspace-state-observation",
                "change-evidence-export",
                "validation-check",
                "workspace-state-observation",
            ],
            "missing-post": [
                "workspace-state-observation",
                "change-evidence-export",
            ],
        }
        for label, commands in variants.items():
            with self.subTest(label=label):
                case = copy.deepcopy(self.utility_cases[0])
                case["steps"][2]["utility_evidence"]["commands_run"] = commands
                errors = self._errors(case)
                self.assertTrue(
                    any(
                        "adjacent ordered pre-check group" in error
                        or "exactly one mode operation" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_diff_export_must_use_supplied_or_host_native_artifact(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["artifact_ref"] = "actual.diff"
        self.assertTrue(
            any("supplied content or a host-native artifact" in error for error in self._errors(case))
        )

    def test_utility_result_actor_must_be_task_agent(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        case["steps"][2]["actor"] = "review-agent"
        self.assertTrue(
            any("utility result actor must be task-agent" in error for error in self._errors(case))
        )

    def test_extra_professional_task_dispatch_breaks_exact_immediate_pair(self) -> None:
        case = copy.deepcopy(self.utility_cases[0])
        extra_dispatch = copy.deepcopy(self.release_cases[0]["steps"][1])
        case["steps"].insert(
            2,
            extra_dispatch,
        )
        errors = self._errors(case)
        self.assertTrue(
            any("exactly one task-agent dispatch" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("followed immediately by its result" in error for error in errors),
            errors,
        )

    def test_external_read_fixtures_cover_offline_allow_and_deny_paths(self) -> None:
        results, errors = EVAL._external_read_fixture_results(
            copy.deepcopy(self.external_read_cases)
        )
        self.assertEqual([], errors)
        self.assertEqual(14, len(results))
        self.assertEqual(
            {"external-source-read"},
            {
                item["operation"]
                for item in results
                if item["actual_valid"] and item["external_read_triggered"]
            },
        )
        by_id = {item["id"]: item for item in results}
        for case_id in (
            "external-read-no-material-claim",
            "external-read-local-evidence-sufficient",
            "external-read-noncritical-proof-limit",
            "external-read-unsupported-local-continue",
        ):
            self.assertFalse(by_id[case_id]["external_read_triggered"])
        for case_id in (
            "external-read-task-agent-denied",
            "external-read-review-agent-denied",
            "external-read-private-query-denied",
            "external-read-raw-instruction-denied",
        ):
            self.assertFalse(by_id[case_id]["expected_valid"])
            self.assertTrue(by_id[case_id]["matches_expected"])

    def test_external_read_generic_contract_is_capability_driven(self) -> None:
        contract = EVAL.EXTERNAL_READ_MODEL
        self.assertEqual("external-source-read", contract["capability_field"])
        self.assertEqual(["supported", "unsupported"], contract["capability_states"])
        self.assertNotIn("tool", contract)
        self.assertNotIn("capability_modes", contract)
        self.assertNotIn("supported_operations", contract)
        self.assertEqual(
            ["external-source-read"],
            contract["ledger_projection"]["capability_values"],
        )
        for case in self.external_read_cases:
            self.assertNotIn("host_mode", case)
            self.assertIn(
                case["external_read_capability"],
                {"supported", "unsupported"},
            )
            self.assertIn(
                case["operation"],
                {"external-source-read", "not-applicable"},
            )
            if case["operation"] == "external-source-read":
                self.assertEqual("external-source-read", case["ledger"]["Command"])

    def test_external_read_mutations_reject_prompt_execution_and_disclosure(self) -> None:
        base = copy.deepcopy(
            next(
                case
                for case in self.external_read_cases
                if case["id"] == "external-read-prompt-injection-ignored"
            )
        )
        mutations = (
            ("instruction_executed", True, "external-content-control"),
            ("raw_instruction_propagated", True, "external-content-control"),
        )
        for field, value, expected in mutations:
            with self.subTest(field=field):
                case = copy.deepcopy(base)
                case["response"][field] = value
                case["expected_valid"] = True
                case["expected_error"] = None
                _results, errors = EVAL._external_read_fixture_results([case])
                self.assertTrue(any(expected in error for error in errors), errors)

        leak = copy.deepcopy(base)
        leak["request"]["contains_protected_content"] = True
        leak["expected_valid"] = True
        leak["expected_error"] = None
        _results, errors = EVAL._external_read_fixture_results([leak])
        self.assertTrue(any("external-read-disclosure" in error for error in errors), errors)

    def test_external_read_mutations_reject_role_and_jit_drift(self) -> None:
        base = copy.deepcopy(
            next(
                case
                for case in self.external_read_cases
                if case["id"] == "external-read-official-source"
            )
        )
        task_case = copy.deepcopy(base)
        task_case["role"] = "task-agent"
        task_case["expected_valid"] = True
        task_case["expected_error"] = None
        _results, errors = EVAL._external_read_fixture_results([task_case])
        self.assertTrue(any("external-read-role" in error for error in errors), errors)

        no_claim = copy.deepcopy(base)
        no_claim["evidence_state"] = "no-material-claim"
        no_claim["expected_valid"] = True
        no_claim["expected_error"] = None
        _results, errors = EVAL._external_read_fixture_results([no_claim])
        self.assertTrue(any("external-read-jit" in error for error in errors), errors)


class CanonicalFindingCompilerTests(unittest.TestCase):
    @staticmethod
    def _finding(
        finding_id: str,
        *,
        description: str = "retry may publish twice",
        task_id: str = "task-retry",
        review_round_id: str = "round-1",
        relation: str = "current-task",
        protected_boundary: str = "none",
        defect: str = "retry duplicate publish",
        violated_invariant: str = "publish is at most once",
        failure_mechanism: str = "retry re-enters publish after an ambiguous acknowledgement",
        fix_path: str = "bind one idempotency key before publish",
        evidence: str | None = None,
    ) -> dict:
        return {
            "finding_identity": finding_id,
            "task_id": task_id,
            "review_round_id": review_round_id,
            "relation": relation,
            "protected_decision_boundary": protected_boundary,
            "category": "correctness-or-invariant",
            "repair_required": relation == "current-task",
            "description": description,
            "defect": defect,
            "violated_invariant": violated_invariant,
            "failure_mechanism": failure_mechanism,
            "fix_path": fix_path,
            "source_reviewer_evidence": [
                {
                    "reviewer_result_id": f"reviewer-{finding_id}",
                    "evidence": evidence or f"src/retry.py:{finding_id}",
                }
            ],
            "affected_scope": ["src/retry.py"],
            "acceptance_or_risk_impact": "duplicate externally visible publish",
            "required_validation": ["retry-idempotency-regression"],
            "required_covering_rereview": {
                "covered_task_ids": [task_id],
                "same_or_stronger": True,
            },
            "freshness": "current-review-round",
            "proof_limit": "bounded retry publish path",
        }

    @staticmethod
    def _rendered_review_handoff_finding(identity: str = "F-visible-1") -> str:
        return f"""# Review Handoff

## Findings

Finding Identity: {identity}
Finding Relation: current-task
Re-review Classification: not-applicable
Classification Evidence: not-applicable
Review Round ID: round-1
Task ID: task-retry
Category: correctness-or-invariant
Repair required: true
Severity: high
Blocker: true
Description: retry may publish twice
Protected Decision Boundary: none
Defect: retry duplicate publish
Violated invariant: publish is at most once
Failure mechanism: retry re-enters publish after an ambiguous acknowledgement
Fix path: bind one idempotency key before publish
Source reviewer evidence: reviewer-1 | src/retry.py:41
Affected scope: src/retry.py
Acceptance or risk impact: duplicate externally visible publish
Required validation: retry-idempotency-regression
Required covering re-review: task-retry | same-or-stronger
Freshness: current-review-round
Proof Limit: bounded retry publish path
"""

    def test_public_review_handoff_parses_visible_identity_into_compiler(self) -> None:
        raw, errors = EVAL._parse_review_handoff_findings(
            self._rendered_review_handoff_finding()
        )
        self.assertEqual([], errors)
        self.assertEqual("F-visible-1", raw[0]["finding_identity"])
        self.assertEqual("correctness-or-invariant", raw[0]["category"])
        self.assertTrue(raw[0]["repair_required"])
        canonical, compiler_errors = EVAL._compile_canonical_findings(raw)
        self.assertEqual([], compiler_errors)
        self.assertEqual(["F-visible-1"], canonical[0]["source_finding_ids"])

    def test_public_review_handoff_rejects_missing_or_duplicate_visible_identity(self) -> None:
        missing = self._rendered_review_handoff_finding().replace(
            "Finding Identity: F-visible-1\n", ""
        )
        _raw, errors = EVAL._parse_review_handoff_findings(missing)
        self.assertTrue(any("identity" in error.casefold() for error in errors), errors)
        duplicate = (
            self._rendered_review_handoff_finding()
            + "\n"
            + self._rendered_review_handoff_finding()
        )
        _raw, errors = EVAL._parse_review_handoff_findings(duplicate)
        self.assertTrue(any("duplicate" in error.casefold() for error in errors), errors)

    def test_exact_duplicate_compiles_to_one_stable_canonical_finding(self) -> None:
        first = self._finding("F-1")
        second = self._finding("F-2")
        canonical, errors = EVAL._compile_canonical_findings([first, second])
        self.assertEqual([], errors)
        self.assertEqual(1, len(canonical))
        self.assertEqual("F-1", canonical[0]["canonical_finding_id"])
        self.assertEqual(["F-1", "F-2"], canonical[0]["source_finding_ids"])

    def test_wording_difference_merges_only_with_same_complete_semantic_basis(self) -> None:
        first = self._finding("F-1", description="retry may publish twice")
        second = self._finding(
            "F-2",
            description="retry lacks idempotency before publish",
        )
        canonical, errors = EVAL._compile_canonical_findings([first, second])
        self.assertEqual([], errors)
        self.assertEqual(1, len(canonical))
        self.assertEqual(
            ["retry may publish twice", "retry lacks idempotency before publish"],
            canonical[0]["descriptions"],
        )

    def test_same_location_retry_and_rollback_failure_modes_stay_separate(self) -> None:
        retry = self._finding("F-retry")
        rollback = self._finding(
            "F-rollback",
            description="retry loses rollback state",
            defect="retry rollback state loss",
            violated_invariant="rollback state survives retry",
            failure_mechanism="retry clears rollback state before recovery",
            fix_path="retain rollback state until recovery commits",
        )
        canonical, errors = EVAL._compile_canonical_findings([retry, rollback])
        self.assertEqual([], errors)
        self.assertEqual(2, len(canonical))

    def test_partition_boundaries_never_merge(self) -> None:
        findings = [
            self._finding("F-base"),
            self._finding("F-task", task_id="task-other"),
            self._finding("F-round", review_round_id="round-2"),
            self._finding("F-relation", relation="adjacent"),
            self._finding(
                "F-protected",
                protected_boundary="Acceptance-or-Non-goals",
            ),
        ]
        canonical, errors = EVAL._compile_canonical_findings(findings)
        self.assertEqual([], errors)
        self.assertEqual(5, len(canonical))

    def test_merge_preserves_every_source_evidence_and_obligation(self) -> None:
        first = self._finding("F-1", evidence="retry branch at src/retry.py:41")
        second = self._finding(
            "F-2",
            description="retry lacks idempotency before publish",
            evidence="publish call at src/retry.py:58",
        )
        second["affected_scope"].append("tests/test_retry.py")
        second["required_validation"].append("publish-count-negative-control")
        second["acceptance_or_risk_impact"] = "retry violates at-most-once acceptance"
        second["proof_limit"] = "bounded retry and publish call path"
        canonical, errors = EVAL._compile_canonical_findings([first, second])
        self.assertEqual([], errors)
        self.assertEqual(1, len(canonical))
        merged = canonical[0]
        self.assertEqual(2, len(merged["source_reviewer_evidence"]))
        self.assertEqual(
            ["src/retry.py", "tests/test_retry.py"], merged["affected_scope"]
        )
        self.assertEqual(
            ["retry-idempotency-regression", "publish-count-negative-control"],
            merged["required_validation"],
        )
        self.assertEqual(
            [
                "duplicate externally visible publish",
                "retry violates at-most-once acceptance",
            ],
            merged["acceptance_or_risk_impacts"],
        )
        self.assertEqual(
            ["bounded retry publish path", "bounded retry and publish call path"],
            merged["proof_limits"],
        )

    def test_missing_source_backed_semantic_basis_fails_closed(self) -> None:
        incomplete = self._finding("F-incomplete")
        incomplete["failure_mechanism"] = ""
        canonical, errors = EVAL._compile_canonical_findings([incomplete])
        self.assertEqual([], canonical)
        self.assertTrue(
            any("finding-compiler-semantic-basis" in error for error in errors),
            errors,
        )

    def test_semantic_repair_convergence_classifies_progressing_from_canonical_evidence(
        self,
    ) -> None:
        prior = LightweightUtilityContractTests._semantic_canonical_finding("F-A")
        current = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-B",
            review_round_id="R-C-2",
            scope="src/retry/b.py",
            defect="rollback state is lost after retry",
            invariant="rollback state survives retry",
            mechanism="retry clears rollback state before recovery",
            fix_path="retain rollback state until recovery commits",
        )
        evidence = LightweightUtilityContractTests._semantic_convergence_evidence(
            [[prior], [current]],
            inherited_resolution_evidence=[
                {
                    "canonical_finding_id": "F-A",
                    "resolved": True,
                    "current_source_evidence": "negative control now publishes once",
                }
            ],
            independent_new_defect_evidence=[
                {
                    "canonical_finding_id": "F-B",
                    "independent": True,
                    "current_source_evidence": "rollback branch is distinct from publish",
                }
            ],
        )

        result, errors = EVAL._classify_semantic_repair_trajectory(evidence)

        self.assertEqual([], errors)
        self.assertEqual("progressing", result["classification"])
        self.assertEqual(
            "continue-existing-repair-path-only", result["disposition"]
        )
        self.assertFalse(result["pass_authority"])

    def test_semantic_repair_convergence_classifies_source_proven_finite_siblings(
        self,
    ) -> None:
        first = LightweightUtilityContractTests._semantic_canonical_finding("F-A")
        second = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-B",
            review_round_id="R-C-2",
            scope="src/retry/b.py",
        )
        sites = ["src/retry/a.py", "src/retry/b.py"]
        evidence = LightweightUtilityContractTests._semantic_convergence_evidence(
            [[first], [second]],
            original_task_scope=sites,
            finite_sibling_scope={
                "sites": sites,
                "treatment": first["fix_path"],
                "current_source_evidence": [
                    "current registry proves a.py and b.py are the finite retry handlers"
                ],
            },
        )

        result, errors = EVAL._classify_semantic_repair_trajectory(evidence)

        self.assertEqual([], errors)
        self.assertEqual("bounded-class", result["classification"])
        self.assertEqual(sites, result["bounded_scope"])
        self.assertEqual(
            "reshape-next-repair-to-source-proven-finite-class",
            result["disposition"],
        )

        outside = copy.deepcopy(evidence)
        outside["original_task_scope"] = ["src/retry/a.py"]
        result, errors = EVAL._classify_semantic_repair_trajectory(outside)
        self.assertEqual("indeterminate", result["classification"])
        self.assertTrue(
            any("semantic-convergence-bounded-scope" in error for error in errors),
            errors,
        )

    def test_semantic_repair_convergence_requires_proven_oscillation(self) -> None:
        finding_a1 = LightweightUtilityContractTests._semantic_canonical_finding("F-A1")
        finding_b = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-B",
            review_round_id="R-C-2",
            defect="rollback state is lost after retry",
            invariant="rollback state survives retry",
            mechanism="retry clears rollback state before recovery",
            fix_path="retain rollback state until recovery commits",
        )
        finding_a2 = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-A2", review_round_id="R-C-3"
        )
        cycle = LightweightUtilityContractTests._semantic_convergence_evidence(
            [[finding_a1], [finding_b], [finding_a2]]
        )
        result, errors = EVAL._classify_semantic_repair_trajectory(cycle)
        self.assertEqual([], errors)
        self.assertEqual("oscillating", result["classification"])
        self.assertEqual(
            "may-block-non-converged-and-stop-same-path",
            result["disposition"],
        )

        rebroken = LightweightUtilityContractTests._semantic_convergence_evidence(
            [[finding_a1], [finding_b]],
            rebroken_verified_invariant_evidence=[
                {
                    "invariant": finding_a1["violated_invariant"],
                    "current_source_evidence": "latest repair again permits duplicate publish",
                }
            ],
        )
        result, errors = EVAL._classify_semantic_repair_trajectory(rebroken)
        self.assertEqual([], errors)
        self.assertEqual("oscillating", result["classification"])

        explicit = LightweightUtilityContractTests._semantic_convergence_evidence(
            [[finding_a1], [finding_b]],
            explicit_failure_set_cycle_evidence=[
                "current review evidence proves the failure set repeats R1 after R2"
            ],
        )
        result, errors = EVAL._classify_semantic_repair_trajectory(explicit)
        self.assertEqual([], errors)
        self.assertEqual("oscillating", result["classification"])

    def test_semantic_repair_convergence_forbidden_solo_heuristics_stay_indeterminate(
        self,
    ) -> None:
        repeated_once = LightweightUtilityContractTests._semantic_canonical_finding("F-A1")
        repeated_twice = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-A2", review_round_id="R-C-2"
        )
        result, errors = EVAL._classify_semantic_repair_trajectory(
            LightweightUtilityContractTests._semantic_convergence_evidence([[repeated_once], [repeated_twice]])
        )
        self.assertEqual([], errors)
        self.assertEqual("indeterminate", result["classification"])

        independent_count_same = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-B",
            review_round_id="R-C-2",
            defect="new independent failure",
            invariant="new invariant",
            mechanism="new mechanism",
            fix_path="new repair",
        )
        result, errors = EVAL._classify_semantic_repair_trajectory(
            LightweightUtilityContractTests._semantic_convergence_evidence(
                [[repeated_once], [independent_count_same]]
            )
        )
        self.assertEqual([], errors)
        self.assertEqual("indeterminate", result["classification"])

        same_file_new_category = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-C",
            review_round_id="R-C-2",
            category="regression",
            defect="another defect in the same file",
            invariant="another invariant",
            mechanism="another mechanism",
            fix_path="another repair",
        )
        result, errors = EVAL._classify_semantic_repair_trajectory(
            LightweightUtilityContractTests._semantic_convergence_evidence(
                [[repeated_once], [same_file_new_category]]
            )
        )
        self.assertEqual([], errors)
        self.assertEqual("indeterminate", result["classification"])

    def test_semantic_repair_convergence_fails_closed_on_noncanonical_or_cross_boundary_evidence(
        self,
    ) -> None:
        prior = LightweightUtilityContractTests._semantic_canonical_finding("F-A")
        current = LightweightUtilityContractTests._semantic_canonical_finding(
            "F-B", review_round_id="R-C-2"
        )
        malformed = LightweightUtilityContractTests._semantic_convergence_evidence([[prior], [current]])
        malformed["canonical_finding_history"][1]["canonical_findings"][0][
            "task_id"
        ] = "OTHER"

        result, errors = EVAL._classify_semantic_repair_trajectory(malformed)

        self.assertEqual("indeterminate", result["classification"])
        self.assertTrue(
            any("semantic-convergence-boundary" in error for error in errors),
            errors,
        )

    def test_compiler_runs_after_complete_initial_review_and_repairs_canonical_only(
        self,
    ) -> None:
        document = EVAL._load_json(EVAL.FIXTURES)
        case = copy.deepcopy(
            next(
                item
                for item in document["orchestration_cases"]
                if item["id"] == "dedup-scoped-repair-subsumes-final"
            )
        )
        case["id"] = "canonical-finding-compiler-integration"
        case.pop("retained_semantics", None)
        findings = [
            event for event in case["events"] if event.get("action") == "finding"
        ]
        for index, finding in enumerate(findings, 1):
            structured = self._finding(
                str(finding["finding_id"]),
                description=(
                    "retry may publish twice"
                    if index == 1
                    else "retry lacks idempotency before publish"
                ),
                task_id=str(finding["task_id"]),
                review_round_id=str(finding["review_round_id"]),
                evidence=f"reviewer evidence {index}",
            )
            finding["finding_identity"] = structured["finding_identity"]
            for field in (
                "protected_decision_boundary",
                "description",
                "defect",
                "violated_invariant",
                "failure_mechanism",
                "fix_path",
                "source_reviewer_evidence",
                "freshness",
                "proof_limit",
            ):
                finding[field] = structured[field]

        repair = next(
            event for event in case["events"] if event.get("action") == "repair"
        )
        repair["resolved_finding_ids"] = [str(findings[0]["finding_id"])]
        repair["finding_relations"] = {
            str(findings[0]["finding_id"]): "current-task"
        }
        canonical, errors = EVAL._compile_canonical_findings(findings)
        self.assertEqual([], errors)
        repair["finding_obligations"] = [
            EVAL._canonical_repair_obligation(canonical[0])
        ]
        self.assertEqual([], EVAL._orchestration_case_errors(case))

        incomplete = copy.deepcopy(case)
        closing = next(
            event
            for event in incomplete["events"]
            if event.get("action") == "review"
        )
        closing["required_changed_scope_complete"] = False
        errors = EVAL._orchestration_case_errors(incomplete)
        self.assertTrue(any("review-complete-pass" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
