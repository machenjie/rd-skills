from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validation_utils as VALIDATION_UTILS  # noqa: E402


CORE_CONTRACTS = VALIDATION_UTILS.CORE_CONTRACTS


SPEC = importlib.util.spec_from_file_location(
    "test_eval_agent_behavior_module",
    SCRIPTS / "eval-agent-behavior.py",
)
assert SPEC is not None and SPEC.loader is not None
BEHAVIOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BEHAVIOR
SPEC.loader.exec_module(BEHAVIOR)


COMPARISON_MANIFEST = (
    ROOT / "evals" / "agent-behavior" / "comparison-fixtures" / "structural.yaml"
)
SKILL_EFFICACY_PATH = (
    ROOT
    / "src"
    / "foundation"
    / "capabilities"
    / "skill-efficacy-benchmark"
    / "SKILL.md"
)


class AgentBehaviorComparisonTests(unittest.TestCase):
    def _load(self) -> BEHAVIOR.ComparisonSuite:
        return BEHAVIOR._load_comparison_suite(COMPARISON_MANIFEST)

    def _verified_live_suite(self) -> BEHAVIOR.ComparisonSuite:
        suite = copy.deepcopy(self._load())
        suite.evidence_class = "live_agent"
        suite.live_evidence_status = "collected"
        verifier_captures = {}
        for case_index, case in enumerate(suite.cases, 1):
            captures = {}
            for arm_index, arm_id in enumerate(case.arm_ids, 1):
                observation = case.observations[arm_id]
                capture_bytes = json.dumps(
                    observation["actual_behavior"], sort_keys=True
                )
                digest = hashlib.sha256(capture_bytes.encode()).hexdigest()
                observation["artifact_sha256"] = digest
                bindings = observation["controlled_bindings"]
                treatment = (
                    "baseline"
                    if arm_id == case.reveal["old_arm_id"]
                    else "candidate"
                )
                captures[arm_id] = {
                    "capture_bytes": capture_bytes,
                    "artifact_sha256": digest,
                    "capture_sequence": observation["capture_sequence"],
                    "treatment_source": treatment,
                    "controlled_bindings": copy.deepcopy(bindings),
                    "provenance": {
                        "verifier_id": "opaque-901",
                        "source_execution_id": f"execution-{case_index:03d}-{arm_index}",
                        "treatment_source": treatment,
                        "host_id": bindings["host_id"],
                        "model_id": bindings["model_id"],
                        "agent_profile": bindings["agent_profile"],
                        "repository_state_sha": bindings["repository_state_sha"],
                        "capture_sequence": observation["capture_sequence"],
                        "reveal_sequence": case.reveal["reveal_sequence"],
                        "observed_before_reveal": True,
                    },
                }
            verifier_captures[case.case_id] = captures
        suite.verifier_captures = verifier_captures
        return suite

    def test_core_owns_comparison_closed_sets_and_dev_only_boundary(self) -> None:
        contract = CORE_CONTRACTS["behavior_eval_contract"]
        self.assertEqual(
            [], VALIDATION_UTILS.behavior_eval_contract_errors(CORE_CONTRACTS)
        )
        self.assertFalse(contract["runtime_dependency"])
        self.assertEqual(
            "evals/agent-behavior/comparison-fixtures/structural.yaml",
            contract["comparison_manifest_path"],
        )
        self.assertEqual(
            set(contract["artifact_roles"]),
            {"agent_packet", "oracle", "observations", "verifier_capture", "reveal"},
        )
        self.assertEqual(
            set(contract["verdicts"]),
            {
                "improved",
                "hardening_only",
                "no_effect",
                "regression",
                "not_enough_evidence",
            },
        )
        self.assertIn("path_accuracy", contract["routing_metrics"])
        self.assertIn("review_boundary_correctness", contract["review_metrics"])
        self.assertEqual(
            {
                "decision_actor_profile": "main-control-agent",
                "review_candidate_profile": "review-agent",
                "decision": "review-input-ready",
                "evaluated_before_review_execution": True,
                "reviewer_executed": False,
                "dispatch_count": 0,
            },
            contract["main_dispatch_surface_contract"],
        )
        self.assertEqual(
            "integrity-only",
            contract["live_capture_contract"]["caller_supplied_authority"],
        )
        self.assertEqual(
            "not_collected",
            contract["live_capture_contract"]["effective_live_evidence_status"],
        )

    def test_skill_distinguishes_incomplete_structural_and_live_evidence(self) -> None:
        contract = CORE_CONTRACTS["behavior_eval_contract"]
        structural_class = next(
            item for item in contract["evidence_classes"] if item.startswith("structural")
        )
        live_class = next(
            item for item in contract["evidence_classes"] if item.startswith("live")
        )
        missing_live_verdict = contract["verdict_policy"]["missing-live-agent-data"]
        source = SKILL_EFFICACY_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "A comparison missing its baseline or treatment is incomplete, has no "
            "evidence class, and supports no efficacy claim.",
            source,
        )
        self.assertIn(
            "A complete structural baseline/treatment comparison with live behavior "
            f"not collected has evidence class `{structural_class}` and final verdict "
            f"`{missing_live_verdict}`.",
            source,
        )
        self.assertIn(
            "A valid complete live comparison has evidence class "
            f"`{live_class}` and uses the Core behavior-evaluation verdict mapping.",
            source,
        )
        self.assertNotIn(
            "Classify missing-baseline evidence as `structural-only`",
            source,
        )

    def test_contract_rejects_runtime_dependency_and_duplicate_metric(self) -> None:
        runtime = copy.deepcopy(CORE_CONTRACTS)
        runtime["behavior_eval_contract"]["runtime_dependency"] = True
        self.assertTrue(VALIDATION_UTILS.behavior_eval_contract_errors(runtime))

        duplicate = copy.deepcopy(CORE_CONTRACTS)
        duplicate["behavior_eval_contract"]["routing_metrics"].append(
            duplicate["behavior_eval_contract"]["routing_metrics"][0]
        )
        self.assertTrue(VALIDATION_UTILS.behavior_eval_contract_errors(duplicate))

    def test_contract_rejects_semantically_weakened_closed_sets(self) -> None:
        mutations = []
        replacements = {
            "modes": ["captured_handoff", "metadata_only"],
            "artifact_roles": ["agent_packet", "oracle", "observations", "reveal"],
            "controlled_bindings": [
                "task_id", "host_id", "model_id", "agent_profile",
                "repository_state_sha", "evidence_boundary_id", "evaluator_id",
                "unverified_definition",
            ],
            "evidence_classes": ["live_agent", "claimed_live"],
            "live_evidence_statuses": ["collected", "assumed"],
            "review_input_ready_fields": [
                "latest_changed_scope", "latest_diff_or_reference",
                "post_latest_edit_validation", "fixed_review_boundary", "optional_evidence",
            ],
            "reviewer_forbidden_actions": [
                "edited", "repaired", "rerouted", "write_scope_expanded", "trusted_implementer",
                "requested_diff_export",
            ],
            "finding_relations": ["current-task", "scope-blocker", "nearby"],
        }
        for field, replacement in replacements.items():
            mutation = copy.deepcopy(CORE_CONTRACTS)
            mutation["behavior_eval_contract"][field] = replacement
            mutations.append((field, mutation))
        for label, mutation in mutations:
            with self.subTest(label=label):
                self.assertTrue(
                    VALIDATION_UTILS.behavior_eval_contract_errors(mutation)
                )

    def test_contract_rejects_metric_direction_disposition_and_verdict_weakening(self) -> None:
        mutations = []
        for label, mutate in (
            ("routing-metric", lambda c: c["routing_metrics"].remove("path_accuracy")),
            ("review-metric", lambda c: c["review_metrics"].remove("review_boundary_correctness")),
            ("direction", lambda c: c["metric_directions"].__setitem__("domain_extension_fpr", "higher_is_better")),
            ("disposition", lambda c: c["finding_dispositions"].__setitem__("adjacent", "repair-if-material")),
            ("observation", lambda c: c["observation_contract"].__setitem__("boolean_semantics", "truthy")),
            ("capture", lambda c: c["live_capture_contract"].__setitem__("copied_arm_capture", "accept")),
            ("capture-trust", lambda c: c["live_capture_contract"].__setitem__("caller_supplied_authority", "host-proof")),
            ("dispatch-actor", lambda c: c["main_dispatch_surface_contract"].__setitem__("decision_actor_profile", "review-agent")),
            ("agent-visible", lambda c: c["agent_visible_contract"].__setitem__("semantic_answer_leakage", "warn")),
            ("verdict", lambda c: c["verdict_policy"].__setitem__("quality_regression", "no_effect")),
        ):
            mutation = copy.deepcopy(CORE_CONTRACTS)
            mutate(mutation["behavior_eval_contract"])
            mutations.append((label, mutation))
        for label, mutation in mutations:
            with self.subTest(label=label):
                self.assertTrue(
                    VALIDATION_UTILS.behavior_eval_contract_errors(mutation)
                )

    def test_structural_suite_is_blind_physically_separated_and_non_live(self) -> None:
        suite = self._load()
        contract = CORE_CONTRACTS["behavior_eval_contract"]
        self.assertEqual("structural_only", suite.evidence_class)
        self.assertEqual("not_collected", suite.live_evidence_status)
        self.assertEqual([], suite.hardening_evidence_refs)
        self.assertEqual(
            set(contract["artifact_roles"]), set(suite.artifact_paths)
        )
        self.assertEqual(5, len(set(suite.artifact_paths.values())))
        self.assertTrue(all(path.is_file() for path in suite.artifact_paths.values()))

        report = BEHAVIOR._evaluate_comparison_suite(suite)
        self.assertEqual(1, report["schema_version"])
        self.assertEqual("blind-old-new-agent-behavior", report["evaluation_kind"])
        self.assertEqual("not_enough_evidence", report["verdict"])
        self.assertEqual("not_collected", report["live_evidence_status"])
        self.assertEqual(
            set(contract["routing_metrics"]),
            set(report["old"]["routing_metrics"]),
        )
        self.assertEqual(
            set(contract["review_metrics"]),
            set(report["new"]["review_metrics"]),
        )
        for arm in ("old", "new"):
            self.assertEqual(
                {metric: "not_collected" for metric in contract["cost_metrics"]},
                report[arm]["cost_metrics"],
            )
        folded = json.dumps(report, sort_keys=True).casefold()
        self.assertNotIn("demonstrated behavior improvement", folded)
        self.assertNotIn("live elapsed", folded)

    def test_live_metadata_without_verified_capture_cannot_promote_evidence(self) -> None:
        suite = copy.deepcopy(self._load())
        suite.evidence_class = "live_agent"
        suite.live_evidence_status = "collected"
        report = BEHAVIOR._evaluate_comparison_suite(suite)
        self.assertEqual("not_enough_evidence", report["verdict"])
        self.assertFalse(report["host_executed"])
        self.assertFalse(report["live_capture_verification"]["verified"])
        self.assertNotEqual("bounded-live-agent-comparison", report["claim_boundary"])

    def test_caller_supplied_captures_prove_integrity_but_never_live_execution(self) -> None:
        suite = self._verified_live_suite()
        report = BEHAVIOR._evaluate_comparison_suite(suite)
        self.assertTrue(report["live_capture_verification"]["integrity_verified"])
        self.assertFalse(report["live_capture_verification"]["verified"])
        self.assertEqual("not_collected", report["live_evidence_status"])
        self.assertFalse(report["host_executed"])
        self.assertEqual("not-enough-evidence", report["claim_boundary"])
        self.assertEqual("not_enough_evidence", report["verdict"])

        for field, invalid in (
            ("treatment_source", "candidate"),
            ("host_id", "opaque-999"),
            ("model_id", "opaque-999"),
            ("agent_profile", "analysis-agent"),
            ("repository_state_sha", "f" * 64),
            ("observed_before_reveal", False),
        ):
            with self.subTest(provenance=field):
                candidate = copy.deepcopy(suite)
                case = candidate.cases[0]
                old_arm = case.reveal["old_arm_id"]
                candidate.verifier_captures[case.case_id][old_arm]["provenance"][field] = invalid
                invalid_report = BEHAVIOR._evaluate_comparison_suite(candidate)
                self.assertFalse(
                    invalid_report["live_capture_verification"]["integrity_verified"]
                )
                self.assertEqual("not_enough_evidence", invalid_report["verdict"])
                self.assertFalse(invalid_report["host_executed"])
                self.assertNotEqual(
                    "bounded-live-agent-comparison",
                    invalid_report["claim_boundary"],
                )

    def test_fake_copied_or_arbitrary_live_evidence_is_not_enough(self) -> None:
        suite = copy.deepcopy(self._load())
        suite.evidence_class = "live_agent"
        suite.live_evidence_status = "collected"
        case = suite.cases[0]
        captures = {}
        for arm_id in case.arm_ids:
            content = json.dumps(
                case.observations[arm_id]["actual_behavior"], sort_keys=True
            ).encode()
            captures[arm_id] = {
                "capture_bytes": content.decode(),
                "artifact_sha256": hashlib.sha256(content).hexdigest(),
                "capture_sequence": case.observations[arm_id]["capture_sequence"],
                "treatment_source": (
                    "baseline"
                    if arm_id == case.reveal["old_arm_id"]
                    else "candidate"
                ),
                "controlled_bindings": copy.deepcopy(
                    case.observations[arm_id]["controlled_bindings"]
                ),
                "provenance": {
                    "verifier_id": "verifier-001",
                    "source_execution_id": f"execution-{arm_id}",
                    "observed_before_reveal": True,
                },
            }
            case.observations[arm_id]["artifact_sha256"] = captures[arm_id][
                "artifact_sha256"
            ]
        suite.verifier_captures = {case.case_id: captures}

        fake = copy.deepcopy(suite)
        fake.verifier_captures[case.case_id][case.arm_ids[0]][
            "artifact_sha256"
        ] = "f" * 64
        self.assertEqual(
            "not_enough_evidence",
            BEHAVIOR._evaluate_comparison_suite(fake)["verdict"],
        )

        copied = copy.deepcopy(suite)
        copied.verifier_captures[case.case_id][case.arm_ids[1]] = copy.deepcopy(
            copied.verifier_captures[case.case_id][case.arm_ids[0]]
        )
        self.assertEqual(
            "not_enough_evidence",
            BEHAVIOR._evaluate_comparison_suite(copied)["verdict"],
        )

        arbitrary = copy.deepcopy(suite)
        arbitrary.hardening_evidence_refs = ["looks-hardened"]
        self.assertEqual(
            "not_enough_evidence",
            BEHAVIOR._evaluate_comparison_suite(arbitrary)["verdict"],
        )

    def test_comparison_bindings_are_identical_across_both_opaque_arms(self) -> None:
        suite = self._load()
        required = set(CORE_CONTRACTS["behavior_eval_contract"]["controlled_bindings"])
        for case in suite.cases:
            self.assertEqual(required, set(case.agent_packet["controlled_bindings"]))
            self.assertNotRegex(
                " ".join(case.arm_ids).casefold(), r"(?:old|new|baseline|treatment)"
            )
            for arm_id in case.arm_ids:
                self.assertEqual(
                    case.agent_packet["controlled_bindings"],
                    case.observations[arm_id]["controlled_bindings"],
                )

    def test_binding_drift_is_rejected_before_scoring(self) -> None:
        suite = self._load()
        case = suite.cases[0]
        mutated = copy.deepcopy(case.observations)
        mutated[case.arm_ids[1]]["controlled_bindings"]["model_id"] = "other-model"
        with self.assertRaisesRegex(ValueError, "controlled bindings"):
            BEHAVIOR._validate_case_parts(
                case.agent_packet["id"],
                case.agent_packet,
                case.oracle,
                mutated,
                case.reveal,
            )

    def test_agent_packet_answer_leakage_is_rejected(self) -> None:
        suite = self._load()
        case = suite.cases[0]
        packet = copy.deepcopy(case.agent_packet)
        expected_primary = case.oracle["expected_behavior"]["routing"][
            "primary_professional_skill"
        ]
        packet["agent_input"]["prompt"] += f" Select {expected_primary}."
        with self.assertRaisesRegex(ValueError, "answer leakage"):
            BEHAVIOR._validate_case_parts(
                case.agent_packet["id"],
                packet,
                case.oracle,
                case.observations,
                case.reveal,
            )

    def test_complete_pre_reveal_agent_packet_is_opaque_and_leakage_checked(self) -> None:
        suite = self._load()
        for case in suite.cases:
            packet = case.agent_packet
            self.assertRegex(packet["id"], r"^opaque-[0-9]{3}$")
            self.assertNotIn("relationship", packet)
            for field in ("task_id", "host_id", "model_id", "evidence_boundary_id", "evaluator_id"):
                self.assertRegex(
                    packet["controlled_bindings"][field], r"^opaque-[0-9]{3}$"
                )

        case = suite.cases[0]
        semantic_id = copy.deepcopy(case.agent_packet)
        semantic_oracle = copy.deepcopy(case.oracle)
        semantic_reveal = copy.deepcopy(case.reveal)
        semantic_id["id"] = "direct-path"
        semantic_oracle["id"] = "direct-path"
        semantic_reveal["id"] = "direct-path"
        with self.assertRaisesRegex(ValueError, "opaque|leakage"):
            BEHAVIOR._validate_case_parts(
                "direct-path", semantic_id, semantic_oracle,
                case.observations, semantic_reveal,
            )

        boundary = copy.deepcopy(case.agent_packet)
        observations = copy.deepcopy(case.observations)
        boundary["controlled_bindings"]["evidence_boundary_id"] = "direct-path"
        for arm in observations.values():
            arm["controlled_bindings"]["evidence_boundary_id"] = "direct-path"
        with self.assertRaisesRegex(ValueError, "opaque|leakage"):
            BEHAVIOR._validate_case_parts(
                boundary["id"], boundary, case.oracle, observations, case.reveal
            )

    def test_agent_visible_path_fallback_review_and_disposition_leakage_is_rejected(self) -> None:
        suite = self._load()
        case = suite.cases[0]
        for leaked_text in (
            "Take the direct path.",
            "Use safe fallback.",
            "The review boundary decision is not-required.",
            "Send adjacent findings to Repair.",
        ):
            with self.subTest(leaked_text=leaked_text):
                packet = copy.deepcopy(case.agent_packet)
                packet["agent_input"]["prompt"] += " " + leaked_text
                with self.assertRaisesRegex(ValueError, "answer leakage"):
                    BEHAVIOR._validate_case_parts(
                        case.agent_packet["id"], packet, case.oracle, case.observations, case.reveal
                    )

    def test_reveal_must_follow_both_blind_observations(self) -> None:
        suite = self._load()
        case = suite.cases[0]
        reveal = copy.deepcopy(case.reveal)
        reveal["reveal_sequence"] = max(
            arm["capture_sequence"] for arm in case.observations.values()
        )
        with self.assertRaisesRegex(ValueError, "reveal sequence"):
            BEHAVIOR._validate_case_parts(
                case.agent_packet["id"],
                case.agent_packet,
                case.oracle,
                case.observations,
                reveal,
            )

    def test_structural_suite_covers_requested_routing_and_review_failures(self) -> None:
        suite = self._load()
        case_ids = {case.case_id for case in suite.cases}
        required_case_ids = {
            "private-local-no-structure",
            "material-structure-change",
            "generic-cloud-no-domain",
            "confirmed-cloud-boundary",
            "security-wording-no-security-route",
            "real-security-boundary",
            "paraphrase-local-a",
            "paraphrase-local-b",
            "boundary-transition-local",
            "boundary-transition-structural",
            "review-input-not-ready",
            "initial-review-complete-boundary",
            "repair-focused-rereview-fresh",
            "unnecessary-specialist-review-guard",
        }
        self.assertTrue(required_case_ids <= case_ids)

    def test_metrics_detect_over_under_route_and_review_regression(self) -> None:
        suite = self._load()
        report = BEHAVIOR._evaluate_comparison_suite(suite)
        self.assertEqual(0.0, report["new"]["routing_metrics"]["domain_extension_fpr"])
        self.assertEqual(0.0, report["new"]["routing_metrics"]["domain_extension_fnr"])
        self.assertEqual(
            0.0,
            report["new"]["routing_metrics"]["unnecessary_layer3_load_rate"],
        )
        self.assertEqual(
            0.0,
            report["new"]["review_metrics"][
                "unnecessary_specialist_review_rate"
            ],
        )
        self.assertEqual(
            1.0,
            report["new"]["review_metrics"]["review_boundary_correctness"],
        )

        over = copy.deepcopy(suite)
        case = next(
            item for item in over.cases if item.case_id == "private-local-no-structure"
        )
        new_arm = case.reveal["new_arm_id"]
        case.observations[new_arm]["actual_behavior"]["routing"][
            "layer3_skills"
        ].append("implementation-structure-design")
        over_report = BEHAVIOR._evaluate_comparison_suite(over)
        self.assertGreater(
            over_report["new"]["routing_metrics"]["unnecessary_layer3_load_rate"],
            0.0,
        )

        under = copy.deepcopy(suite)
        case = next(
            item for item in under.cases if item.case_id == "real-security-boundary"
        )
        new_arm = case.reveal["new_arm_id"]
        case.observations[new_arm]["actual_behavior"]["routing"][
            "primary_professional_skill"
        ] = "backend-change-builder"
        under_report = BEHAVIOR._evaluate_comparison_suite(under)
        self.assertLess(
            under_report["new"]["routing_metrics"][
                "primary_professional_skill_accuracy"
            ],
            1.0,
        )

    def test_required_specialist_omission_is_review_under_routing(self) -> None:
        suite = copy.deepcopy(self._load())
        case = next(
            item for item in suite.cases
            if item.case_id == "initial-review-complete-boundary"
        )
        case.oracle["expected_behavior"]["review"]["specialist_reviews"] = [
            "security-privacy-gate"
        ]
        old_review = case.observations[case.reveal["old_arm_id"]]["actual_behavior"]["review"]
        old_review["specialist_reviews"] = ["security-privacy-gate"]
        report = BEHAVIOR._evaluate_comparison_suite(suite)
        self.assertLess(
            report["new"]["review_metrics"]["required_specialist_review_recall"],
            1.0,
        )
        self.assertGreater(
            report["new"]["review_metrics"]["required_specialist_review_fnr"],
            0.0,
        )
        self.assertLess(
            report["new"]["review_metrics"]["review_boundary_correctness"],
            1.0,
        )

        over = copy.deepcopy(self._load())
        over_case = next(
            item for item in over.cases
            if item.case_id == "initial-review-complete-boundary"
        )
        over_review = over_case.observations[over_case.reveal["new_arm_id"]][
            "actual_behavior"
        ]["review"]
        over_review["specialist_reviews"] = ["security-privacy-gate"]
        over_report = BEHAVIOR._evaluate_comparison_suite(over)
        self.assertGreater(
            over_report["new"]["review_metrics"]["unnecessary_specialist_review_rate"],
            0.0,
        )
        self.assertEqual(
            1.0,
            over_report["new"]["review_metrics"]["required_specialist_review_recall"],
        )
        self.assertLess(
            over_report["new"]["review_metrics"]["review_boundary_correctness"],
            1.0,
        )

    def test_structured_finding_relation_materiality_and_disposition_are_exact(self) -> None:
        suite = copy.deepcopy(self._load())
        case = next(
            item for item in suite.cases
            if item.case_id == "repair-focused-rereview-fresh"
        )
        expected_review = case.oracle["expected_behavior"]["review"]
        expected_review["expected_findings"] = [
            {
                "finding_identity": "nearby-cleanup",
                "relation": "adjacent",
                "material": False,
                "repair_eligible": False,
                "disposition": "record-only",
                "fresh": True,
                "affected_scope": ["src/nearby.py"],
            },
            {
                "finding_identity": "protected-boundary",
                "relation": "scope-blocker",
                "material": True,
                "repair_eligible": False,
                "disposition": "main-delta-analysis",
                "fresh": True,
                "affected_scope": ["src/worker.py"],
            },
        ]
        actual = case.observations[case.reveal["new_arm_id"]]["actual_behavior"]["review"]
        mutations = (
            ("nearby-cleanup", "relation", "current-task"),
            ("nearby-cleanup", "material", True),
            ("nearby-cleanup", "disposition", "repair-if-material"),
            ("fixed-current-task", "fresh", False),
            ("protected-boundary", "fresh", False),
            ("protected-boundary", "affected_scope", ["src/other.py"]),
        )
        for identity, field, value in mutations:
            with self.subTest(identity=identity, field=field):
                candidate = copy.deepcopy(suite)
                finding = next(
                    item
                    for item in next(
                        case for case in candidate.cases
                        if case.case_id == "repair-focused-rereview-fresh"
                    ).observations[case.reveal["new_arm_id"]]["actual_behavior"]["review"]["findings"]
                    if item["finding_identity"] == identity
                )
                finding[field] = value
                report = BEHAVIOR._evaluate_comparison_suite(candidate)
                self.assertLess(
                    report["new"]["review_metrics"]["review_boundary_correctness"], 1.0
                )
        omitted = copy.deepcopy(suite)
        omitted_case = next(
            item for item in omitted.cases
            if item.case_id == "repair-focused-rereview-fresh"
        )
        findings = omitted_case.observations[omitted_case.reveal["new_arm_id"]][
            "actual_behavior"
        ]["review"]["findings"]
        findings[:] = [
            finding for finding in findings
            if finding["finding_identity"] != "protected-boundary"
        ]
        report = BEHAVIOR._evaluate_comparison_suite(omitted)
        self.assertLess(
            report["new"]["review_metrics"]["review_boundary_correctness"], 1.0
        )

    def test_review_readiness_independence_completeness_and_freshness_are_enforced(self) -> None:
        suite = self._load()
        mutations = [
            ("review-input-not-ready", ("dispatch_count",), 1),
            (
                "initial-review-complete-boundary",
                ("reviewer_actions", "edited"),
                True,
            ),
            (
                "initial-review-complete-boundary",
                ("initial_review", "stopped_after_ordinary_finding"),
                True,
            ),
            (
                "initial-review-complete-boundary",
                ("initial_review", "covered_review_dimensions"),
                ["required-changed-scope"],
            ),
            (
                "initial-review-complete-boundary",
                ("reviewer_actions", "rerouted"),
                True,
            ),
            (
                "initial-review-complete-boundary",
                ("reviewer_actions", "requested_diff_export"),
                True,
            ),
            (
                "repair-focused-rereview-fresh",
                ("repair_re_review", "validation_after_latest_edit"),
                False,
            ),
            (
                "repair-focused-rereview-fresh",
                ("repair_re_review", "uses_latest_repair_diff"),
                False,
            ),
            (
                "repair-focused-rereview-fresh",
                ("repair_re_review", "duplicate_final_review_dispatched"),
                True,
            ),
        ]
        for case_id, path, value in mutations:
            with self.subTest(case_id=case_id, path=path):
                candidate = copy.deepcopy(suite)
                case = next(item for item in candidate.cases if item.case_id == case_id)
                actual = case.observations[case.reveal["new_arm_id"]][
                    "actual_behavior"
                ]["review"]
                target = actual
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                result = BEHAVIOR._evaluate_comparison_suite(candidate)
                self.assertLess(
                    result["new"]["review_metrics"][
                        "review_boundary_correctness"
                    ],
                    1.0,
                )

    def test_adjacent_finding_entering_repair_is_a_review_failure(self) -> None:
        suite = copy.deepcopy(self._load())
        case = next(
            item for item in suite.cases if item.case_id == "repair-focused-rereview-fresh"
        )
        review = case.observations[case.reveal["new_arm_id"]]["actual_behavior"][
            "review"
        ]
        adjacent = next(
            finding
            for finding in review["findings"]
            if finding["relation"] == "adjacent"
        )
        adjacent["entered_repair"] = True
        report = BEHAVIOR._evaluate_comparison_suite(suite)
        self.assertLess(
            report["new"]["review_metrics"]["review_boundary_correctness"],
            1.0,
        )

    def test_verdict_policy_never_allows_cost_to_override_quality(self) -> None:
        contract = CORE_CONTRACTS["behavior_eval_contract"]
        quality_keys = contract["quality_metrics"]
        perfect = {key: 1.0 for key in quality_keys}
        old_failure = dict(perfect, path_accuracy=0.0)
        new_regression = dict(perfect, review_boundary_correctness=0.0)

        self.assertEqual(
            "improved",
            BEHAVIOR._comparison_verdict(
                old_failure,
                perfect,
                evidence_class="live_agent",
                live_evidence_status="collected",
                hardening_only=False,
            ),
        )
        self.assertEqual(
            "no_effect",
            BEHAVIOR._comparison_verdict(
                perfect,
                perfect,
                evidence_class="live_agent",
                live_evidence_status="collected",
                hardening_only=False,
            ),
        )
        self.assertEqual(
            "hardening_only",
            BEHAVIOR._comparison_verdict(
                perfect,
                perfect,
                evidence_class="live_agent",
                live_evidence_status="collected",
                hardening_only=True,
            ),
        )
        self.assertEqual(
            "regression",
            BEHAVIOR._comparison_verdict(
                perfect,
                new_regression,
                evidence_class="live_agent",
                live_evidence_status="collected",
                hardening_only=False,
            ),
        )
        self.assertEqual(
            "not_enough_evidence",
            BEHAVIOR._comparison_verdict(
                old_failure,
                perfect,
                evidence_class="structural_only",
                live_evidence_status="not_collected",
                hardening_only=False,
            ),
        )

    def test_case_level_regression_dominates_aggregate_offset_and_partial_success(self) -> None:
        metrics = CORE_CONTRACTS["behavior_eval_contract"]["quality_metrics"]
        perfect = {key: 1.0 for key in metrics}
        old_cases = [dict(perfect), dict(perfect, path_accuracy=0.0)]
        new_cases = [dict(perfect, path_accuracy=0.0), dict(perfect)]
        self.assertEqual(
            "regression",
            BEHAVIOR._comparison_verdict_from_case_quality(
                old_cases,
                new_cases,
                live_evidence_verified=True,
                hardening_evidence_verified=False,
            ),
        )
        partial = [dict(perfect, path_accuracy=0.5)]
        self.assertEqual(
            "no_effect",
            BEHAVIOR._comparison_verdict_from_case_quality(
                [dict(perfect, path_accuracy=0.0)],
                partial,
                live_evidence_verified=True,
                hardening_evidence_verified=False,
            ),
        )

    def test_main_dispatch_gate_blocks_each_missing_review_input_before_execution(self) -> None:
        suite = self._load()
        case = next(item for item in suite.cases if item.case_id == "review-input-not-ready")
        contract = CORE_CONTRACTS["behavior_eval_contract"]
        expected_fields = [
            "latest_changed_scope",
            "latest_diff_or_reference",
            "post_latest_edit_validation",
            "fixed_review_boundary",
            "required_evidence",
        ]
        self.assertEqual(expected_fields, contract["review_dispatch_gate_fields"])
        for blocker in expected_fields:
            with self.subTest(blocker=blocker):
                expected = copy.deepcopy(case.oracle["expected_behavior"]["review"])
                expected["dispatch_blockers"] = [blocker]
                actual = copy.deepcopy(
                    case.observations[case.reveal["new_arm_id"]]["actual_behavior"]["review"]
                )
                actual["main_dispatch_gate"] = {
                    field: True for field in expected_fields
                }
                actual["main_dispatch_surface"] = copy.deepcopy(
                    contract["main_dispatch_surface_contract"]
                )
                actual["main_dispatch_gate"][blocker] = False
                self.assertTrue(
                    BEHAVIOR._review_boundary_correct(expected, actual, contract)
                )
                wrong = copy.deepcopy(actual)
                wrong["main_dispatch_gate"][blocker] = True
                self.assertFalse(
                    BEHAVIOR._review_boundary_correct(expected, wrong, contract)
                )
                for surface_field, invalid in (
                    ("decision_actor_profile", "review-agent"),
                    ("review_candidate_profile", "main-control-agent"),
                    ("reviewer_executed", True),
                    ("dispatch_count", 1),
                ):
                    wrong_surface = copy.deepcopy(actual)
                    wrong_surface["main_dispatch_surface"][surface_field] = invalid
                    self.assertFalse(
                        BEHAVIOR._review_boundary_correct(
                            expected, wrong_surface, contract
                        )
                    )
                for mutation in ("omitted", "wrong-type"):
                    malformed = copy.deepcopy(case.observations)
                    arm = malformed[case.reveal["new_arm_id"]]["actual_behavior"]["review"]
                    arm["main_dispatch_gate"] = {field: True for field in expected_fields}
                    arm["main_dispatch_gate"][blocker] = False
                    arm["main_dispatch_surface"] = copy.deepcopy(actual["main_dispatch_surface"])
                    if mutation == "omitted":
                        arm["main_dispatch_gate"].pop(blocker)
                    else:
                        arm["main_dispatch_gate"][blocker] = "false"
                    with self.assertRaisesRegex(ValueError, "gate|schema|boolean"):
                        BEHAVIOR._validate_case_parts(
                            case.agent_packet["id"], case.agent_packet,
                            case.oracle, malformed, case.reveal,
                        )

        for forbidden in ("reviewer_actions", "findings", "result", "capture"):
            with self.subTest(zero_dispatch_forbidden=forbidden):
                malformed = copy.deepcopy(case.observations)
                review = malformed[case.reveal["new_arm_id"]]["actual_behavior"][
                    "review"
                ]
                review[forbidden] = {} if forbidden != "findings" else []
                with self.assertRaisesRegex(ValueError, "review schema"):
                    BEHAVIOR._validate_case_parts(
                        case.agent_packet["id"], case.agent_packet,
                        case.oracle, malformed, case.reveal,
                    )

    def test_oracle_and_observation_scalar_identities_and_mappings_are_core_closed(self) -> None:
        suite = self._load()
        case = suite.cases[0]
        mutations = (
            ("path-type", "actual", "path", False),
            ("path-value", "actual", "path", "sideways"),
            ("profile-type", "actual", "start_profile", []),
            ("profile-value", "actual", "start_profile", "unknown-agent"),
            ("path-profile-map", "actual", "start_profile", "analysis-agent"),
            ("skill-type", "actual", "primary_professional_skill", []),
            ("skill-value", "actual", "primary_professional_skill", "unknown-skill"),
            ("skill-profile-map", "actual", "primary_professional_skill", "engineering-change-analysis"),
            ("oracle-path", "expected", "path", "sideways"),
            ("oracle-profile-map", "expected", "start_profile", "analysis-agent"),
        )
        for label, owner, field, value in mutations:
            with self.subTest(label=label):
                oracle = copy.deepcopy(case.oracle)
                observations = copy.deepcopy(case.observations)
                if owner == "actual":
                    observations[case.arm_ids[0]]["actual_behavior"]["routing"][field] = value
                else:
                    oracle["expected_behavior"]["routing"][field] = value
                with self.assertRaisesRegex(ValueError, "routing|profile|skill|Core|identity|mapping"):
                    BEHAVIOR._validate_case_parts(
                        case.agent_packet["id"], case.agent_packet,
                        oracle, observations, case.reveal,
                    )

        review_case = next(
            item for item in suite.cases
            if item.case_id == "initial-review-complete-boundary"
        )
        for field, value in (
            ("primary_review_skill", []),
            ("primary_review_skill", "backend-change-builder"),
            ("boundary_decision", False),
            ("boundary_decision", "unknown-review"),
            ("boundary_decision", "not-required"),
        ):
            with self.subTest(review_field=field, value=value):
                observations = copy.deepcopy(review_case.observations)
                observations[review_case.arm_ids[0]]["actual_behavior"]["review"][field] = value
                with self.assertRaisesRegex(ValueError, "review|skill|boundary|mapping"):
                    BEHAVIOR._validate_case_parts(
                        review_case.agent_packet["id"], review_case.agent_packet,
                        review_case.oracle, observations, review_case.reveal,
                    )

    def test_observation_schema_rejects_truthy_strings_bool_counts_and_shape_drift(self) -> None:
        suite = self._load()
        case = suite.cases[0]
        mutations = []
        truthy = copy.deepcopy(case.observations)
        truthy[case.arm_ids[0]]["actual_behavior"]["routing"]["safe_fallback"] = "false"
        mutations.append(truthy)
        bool_count = copy.deepcopy(case.observations)
        bool_count[case.arm_ids[0]]["actual_behavior"]["review"]["dispatch_count"] = False
        mutations.append(bool_count)
        extra = copy.deepcopy(case.observations)
        extra[case.arm_ids[0]]["actual_behavior"]["routing"]["extra"] = []
        mutations.append(extra)
        duplicate = copy.deepcopy(case.observations)
        duplicate[case.arm_ids[0]]["actual_behavior"]["routing"]["layer3_skills"] = ["x", "x"]
        mutations.append(duplicate)
        omitted = copy.deepcopy(case.observations)
        omitted[case.arm_ids[0]]["actual_behavior"]["review"].pop("boundary_decision")
        mutations.append(omitted)
        nested = copy.deepcopy(self._load())
        review_case = next(
            item for item in nested.cases
            if item.case_id == "initial-review-complete-boundary"
        )
        nested_observations = review_case.observations
        nested_observations[review_case.arm_ids[0]]["actual_behavior"]["review"]["initial_review"]["completed_fixed_boundary"] = "false"
        with self.assertRaisesRegex(ValueError, "schema|boolean"):
            BEHAVIOR._validate_case_parts(
                review_case.agent_packet["id"],
                review_case.agent_packet,
                review_case.oracle,
                nested_observations,
                review_case.reveal,
            )
        for observation in mutations:
            with self.assertRaisesRegex(ValueError, "schema|boolean|dispatch|unique"):
                BEHAVIOR._validate_case_parts(
                    case.agent_packet["id"], case.agent_packet, case.oracle, observation, case.reveal
                )

    def test_legacy_captured_handoff_oracle_remains_available(self) -> None:
        sample_path = (
            ROOT
            / "evals"
            / "agent-behavior"
            / "professional-samples"
            / "backend"
            / "queue-consumer-idempotency.yaml"
        )
        data = BEHAVIOR.load_yaml_file(sample_path)
        professional, layer3 = BEHAVIOR._registries()
        result = BEHAVIOR._score(sample_path, data, professional, layer3)
        self.assertTrue(result.ok)
        self.assertEqual(set(BEHAVIOR.SCORE_KEYS), set(result.scores))

    def test_comparison_cli_writes_separate_report_without_running_a_host(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "eval-agent-behavior.py"),
                    "--comparison-spec",
                    str(COMPARISON_MANIFEST),
                    "--format",
                    "json",
                    "--output-dir",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            outputs = list(Path(temp_dir).glob("*-agent-behavior-comparison.json"))
            self.assertEqual(1, len(outputs))
            report = json.loads(outputs[0].read_text(encoding="utf-8"))
            self.assertEqual("not_enough_evidence", report["verdict"])
            self.assertFalse(report["host_executed"])


if __name__ == "__main__":
    unittest.main()
