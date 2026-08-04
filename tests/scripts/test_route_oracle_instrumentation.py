from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import deterministic_route_oracle as ORACLE
from tests.scripts import test_route_candidate_cohorts as COHORTS
from validation_utils import (
    load_yaml_file,
    professional_routing_authority,
    validate_route_decision,
)


def _load_eval_routing():
    path = ROOT / "scripts" / "eval-routing.py"
    spec = importlib.util.spec_from_file_location(
        "eval_routing_instrumentation_tests",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL_ROUTING = _load_eval_routing()
ORACLE_PATH = ROOT / "scripts" / "deterministic_route_oracle.py"
EVAL_ROUTING_PATH = ROOT / "scripts" / "eval-routing.py"
CASES_PATH = ROOT / "evals" / "routing" / "cases.yaml"
ROUTE_FIELDS = {
    "path",
    "profile",
    "primary_skill",
    "layer3_skills",
    "review_skill",
}
ENVELOPE_FIELDS = {
    "path",
    "route_result",
    "selection_evidence",
    "main_execution_provenance",
    "route_once",
}
ROUTE_RESULT_FIELDS = {
    "start_profile",
    "primary_skill",
    "layer3_skills",
    "review_skill",
    "execution_level",
    "level_basis",
}
ACTIVATION_V2_139A_LAYER3_FIELDS = (
    "eligible_foundation_layer3_skills",
    "eligible_domain_layer3_skills",
    "eligible_layer3_skills",
    "reserved_domain_capacity",
    "layer3_overflow",
)
ACTIVATION_V2_139C_DIRECT_STAGES = (
    "_normalize_route_prompt",
    "_build_route_candidates",
    "_enrich_route_candidates",
    "_compose_foundation_activation_candidates",
    "_select_route_cohort_candidate",
    "_project_route_selection",
    "validate_route_decision",
)


def _main_execution(task_id: str) -> dict[str, object]:
    return {
        "producer": "main-control-agent",
        "task_id": task_id,
        "execution_level": "L4",
        "level_basis": {
            "trigger_evaluations": [
                {
                    "id": "public-api-event-schema-compatibility",
                    "status": "matched",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": f"task:{task_id}:routing-api",
                    "plausible_critical": False,
                }
            ],
            "l2_eligibility": [],
            "obligations": ["high-risk pre-implementation evidence"],
            "unresolved": [],
            "edit_status": "allowed",
        },
    }


def _compatibility_projection(decision: dict[str, object]) -> dict[str, object]:
    result = decision["route_result"]
    assert isinstance(result, dict)
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }


class RouteOracleInstrumentationTests(unittest.TestCase):
    def test_public_route_requires_main_execution_without_a_default(self) -> None:
        signature = inspect.signature(ORACLE.route)
        parameter = signature.parameters.get("main_execution")
        self.assertIsNotNone(parameter)
        assert parameter is not None
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, parameter.kind)
        self.assertIs(inspect.Parameter.empty, parameter.default)
        with self.assertRaises(TypeError):
            ORACLE.route("Implement an accepted backend service change.")

    def test_public_route_returns_exact_valid_core_envelope_for_every_fixture(
        self,
    ) -> None:
        authority = professional_routing_authority()
        cases = load_yaml_file(CASES_PATH)["cases"]
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(case=case["id"]):
                main_execution = case["main_execution"]
                decision = ORACLE.route(
                    case["prompt"],
                    main_execution=main_execution,
                )
                self.assertEqual(ENVELOPE_FIELDS, set(decision))
                self.assertEqual(
                    ROUTE_RESULT_FIELDS,
                    set(decision["route_result"]),
                )
                self.assertEqual(
                    case["expected"],
                    _compatibility_projection(decision),
                )
                self.assertEqual(
                    [],
                    validate_route_decision(
                        decision,
                        main_execution=main_execution,
                        routing_authority=authority,
                    ),
                )

    def test_main_level_basis_and_provenance_are_canonical_byte_equivalent(
        self,
    ) -> None:
        main_execution = _main_execution("t2g-byte-equivalence")
        decision = ORACLE.route(
            "Implement an accepted backend service change.",
            main_execution=main_execution,
        )
        result = decision["route_result"]
        for actual, expected in (
            (decision["main_execution_provenance"], main_execution),
            (result["level_basis"], main_execution["level_basis"]),
        ):
            self.assertEqual(
                json.dumps(
                    expected,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8"),
                json.dumps(
                    actual,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8"),
            )
        self.assertEqual(
            main_execution["execution_level"],
            result["execution_level"],
        )

    def test_activation_v3_ordinary_route_keeps_public_contract_and_provenance(
        self,
    ) -> None:
        main_execution = _main_execution("activation-v3-ordinary-provenance")
        decision = ORACLE.route(
            "Implement an accepted backend service change.",
            main_execution=main_execution,
        )
        self.assertEqual(ENVELOPE_FIELDS, set(decision))
        self.assertEqual(ROUTE_RESULT_FIELDS, set(decision["route_result"]))
        self.assertNotIn(
            "artifact_binding_id",
            COHORTS._nested_mapping_keys(decision),
        )
        self.assertEqual(main_execution, decision["main_execution_provenance"])

    def test_activation_v3_binding_record_is_closed_and_digest_bound(
        self,
    ) -> None:
        errors: list[str] = []
        record = COHORTS.FOUR_FOUNDATION_BINDING
        prefix, claimed_digest = record.rsplit("|binding_sha256=", 1)

        def signed(parts: list[str]) -> str:
            unsigned = "|".join(parts)
            digest = hashlib.sha256(unsigned.encode("utf-8")).hexdigest()
            return f"{unsigned}|binding_sha256={digest}"

        canonical_parts = prefix.split("|")
        if (
            signed(canonical_parts) != record
            or hashlib.sha256(prefix.encode("utf-8")).hexdigest()
            != claimed_digest
        ):
            errors.append("Brief159 fixture digest is not canonical")

        def with_record(value: str) -> dict[str, object]:
            main_execution = copy.deepcopy(
                COHORTS._four_foundation_main_execution()
            )
            main_execution["level_basis"]["trigger_evaluations"][0][
                "source_anchor"
            ] = value
            return main_execution

        try:
            ORACLE.route(
                "Review the engineering brief and task plan.",
                main_execution=with_record(record),
            )
        except Exception as exc:  # pragma: no cover - aggregate Red evidence
            errors.append(f"canonical record rejected: {type(exc).__name__}")

        def replaced(field: str, value: str) -> list[str]:
            return [
                f"{field}={value}" if part.startswith(f"{field}=") else part
                for part in canonical_parts
            ]

        missing = [
            part
            for part in canonical_parts
            if not part.startswith("artifact_id=")
        ]
        extra = [*canonical_parts, "unexpected=field"]
        duplicate = [
            *canonical_parts[:5],
            canonical_parts[4],
            *canonical_parts[5:],
        ]
        reordered = list(canonical_parts)
        reordered[4], reordered[5] = reordered[5], reordered[4]
        delimiter = replaced("artifact_id", "brief|injected=value")
        wrong_digest = (
            f"{prefix}|binding_sha256="
            f"{claimed_digest[:-1]}{'0' if claimed_digest[-1] != '0' else '1'}"
        )
        invalid_records = {
            "missing": signed(missing),
            "extra": signed(extra),
            "duplicate": signed(duplicate),
            "reordered": signed(reordered),
            "empty": signed(replaced("assignment_id", "")),
            "whitespace": signed(
                replaced("artifact_id", " brief-four-foundation")
            ),
            "delimiter": signed(delimiter),
            "uppercase-hex": signed(
                replaced("artifact_sha256", "A" * 64)
            ),
            "wrong-review-skill": signed(
                replaced(
                    "review_skill",
                    "engineering-artifact-review",
                )
            ),
            "wrong-artifact-kind": signed(
                replaced("artifact_kind", "task-plan")
            ),
            "wrong-currentness": signed(
                replaced("currentness_status", "stale")
            ),
            "wrong-acceptance": signed(
                replaced("acceptance_status", "rejected")
            ),
            "wrong-digest": wrong_digest,
            "missing-digest": prefix,
            "wrong-version": signed(
                [
                    "cf.brief-review-binding/v2",
                    *canonical_parts[1:],
                ]
            ),
            "near-prefix": signed(
                [
                    "cf.brief-review-bindings/v1",
                    *canonical_parts[1:],
                ]
            ),
        }
        for label, invalid_record in invalid_records.items():
            rejected = False
            with mock.patch.object(
                ORACLE,
                "_normalize_route_prompt",
                wraps=ORACLE._normalize_route_prompt,
            ) as normalize:
                try:
                    ORACLE.route(
                        "Review the engineering brief and task plan.",
                        main_execution=with_record(invalid_record),
                    )
                except ORACLE.RoutingIntegrityError:
                    rejected = True
                except Exception as exc:  # pragma: no cover - aggregate Red evidence
                    errors.append(
                        f"{label} raised {type(exc).__name__}, not routing integrity"
                    )
            if not rejected:
                errors.append(f"{label} record was accepted")
            if normalize.call_count != 0:
                errors.append(
                    f"{label} normalized the prompt before rejection"
                )
        self.assertEqual(
            [],
            errors,
            "[activation-v3-binding-record] canonical digest records must use "
            "the exact closed Brief159 serialization and reject invalid Main "
            "before normalization",
        )

    def test_activation_v3_binding_authority_context_is_exact(self) -> None:
        errors: list[str] = []

        def routed(main_execution: dict[str, object]) -> None:
            ORACLE.route(
                "Review the engineering brief and task plan.",
                main_execution=main_execution,
            )

        for level in ("L4", "L5"):
            valid = copy.deepcopy(COHORTS._four_foundation_main_execution())
            valid["execution_level"] = level
            try:
                routed(valid)
            except Exception as exc:  # pragma: no cover - aggregate Red evidence
                errors.append(
                    f"valid {level} authority rejected: {type(exc).__name__}"
                )

        invalid_contexts: dict[str, dict[str, object]] = {}

        def mutated(label: str) -> dict[str, object]:
            value = copy.deepcopy(COHORTS._four_foundation_main_execution())
            invalid_contexts[label] = value
            return value

        mutated("task-mismatch")["task_id"] = "different-main-task"
        mutated("wrong-level")["execution_level"] = "L3"
        mutated("missing-obligation")["level_basis"]["obligations"] = []
        mutated("wrong-trigger")["level_basis"]["trigger_evaluations"][0][
            "id"
        ] = "public-api-event-schema-compatibility"
        mutated("not-matched")["level_basis"]["trigger_evaluations"][0][
            "status"
        ] = "not_matched"
        mutated("wrong-evidence-kind")["level_basis"][
            "trigger_evaluations"
        ][0]["evidence_kind"] = "user_fact"
        mutated("critical-marker")["level_basis"]["trigger_evaluations"][0][
            "plausible_critical"
        ] = True
        misplaced = mutated("record-on-wrong-row")
        source_anchor = misplaced["level_basis"]["trigger_evaluations"][0][
            "source_anchor"
        ]
        misplaced["level_basis"]["trigger_evaluations"][0][
            "source_anchor"
        ] = "task:activation-v3-four-foundation:architecture"
        misplaced["level_basis"]["trigger_evaluations"][1][
            "source_anchor"
        ] = source_anchor
        duplicate = mutated("duplicate-binding-authority")
        duplicate["level_basis"]["trigger_evaluations"].append(
            copy.deepcopy(
                duplicate["level_basis"]["trigger_evaluations"][0]
            )
        )
        canonical_prefix = COHORTS.FOUR_FOUNDATION_BINDING.rsplit(
            "|binding_sha256=",
            1,
        )[0]
        second_parts = [
            (
                "artifact_id=brief-four-foundation-second"
                if part.startswith("artifact_id=")
                else part
            )
            for part in canonical_prefix.split("|")
        ]
        second_prefix = "|".join(second_parts)
        second_record = (
            f"{second_prefix}|binding_sha256="
            f"{hashlib.sha256(second_prefix.encode('utf-8')).hexdigest()}"
        )
        for label, record in (
            ("first", COHORTS.FOUR_FOUNDATION_BINDING),
            ("second", second_record),
        ):
            record_prefix, record_digest = record.rsplit(
                "|binding_sha256=",
                1,
            )
            if (
                hashlib.sha256(record_prefix.encode("utf-8")).hexdigest()
                != record_digest
            ):
                errors.append(
                    f"{label} distinct authority record is not digest-valid"
                )
        distinct = mutated("distinct-binding-authorities")
        distinct["level_basis"]["trigger_evaluations"].append(
            {
                "id": "major-architecture-or-physical-safety",
                "status": "matched",
                "evidence_kind": "analysis_handoff",
                "source_anchor": second_record,
                "plausible_critical": False,
            }
        )

        for label, invalid in invalid_contexts.items():
            rejected = False
            with mock.patch.object(
                ORACLE,
                "_normalize_route_prompt",
                wraps=ORACLE._normalize_route_prompt,
            ) as normalize:
                try:
                    routed(invalid)
                except ORACLE.RoutingIntegrityError:
                    rejected = True
                except Exception as exc:  # pragma: no cover - aggregate Red evidence
                    errors.append(
                        f"{label} raised {type(exc).__name__}, "
                        "not routing integrity"
                    )
            if not rejected:
                errors.append(f"{label} authority was accepted")
            if normalize.call_count != 0:
                errors.append(
                    f"{label} normalized the prompt before rejection"
                )
        self.assertEqual(
            [],
            errors,
            "[activation-v3-binding-authority] binding authority requires one "
            "matched major-architecture analysis handoff at L4/L5 with its "
            "high-risk evidence obligation and must reject before normalization",
        )

    def test_selection_evidence_is_the_full_current_registry_partition(
        self,
    ) -> None:
        authority = professional_routing_authority()
        main_execution = _main_execution("t2g-full-partition")
        decision = ORACLE.route(
            "Implement an accepted backend service change.",
            main_execution=main_execution,
        )
        result = decision["route_result"]
        selection = decision["selection_evidence"]
        primary = [row["skill"] for row in selection["primary_candidates"]]
        review = [row["skill"] for row in selection["review_candidates"]]
        layer3 = [row["skill"] for row in selection["layer3_candidates"]]
        self.assertEqual(
            set(authority["primary_skills_by_profile"][result["start_profile"]]),
            set(primary),
        )
        self.assertEqual(set(authority["review_skills"]), set(review))
        self.assertEqual(
            set(
                authority["layer3_candidates_by_primary"][
                    result["primary_skill"]
                ]
            ),
            set(layer3),
        )
        self.assertEqual(len(primary), len(set(primary)))
        self.assertEqual(len(review), len(set(review)))
        self.assertEqual(len(layer3), len(set(layer3)))
        self.assertEqual(1, selection["eligible_primary_count"])
        self.assertTrue(decision["route_once"])

    def test_activation_v2_139a_private_field_constant_is_exact(self) -> None:
        self.assertEqual(
            ACTIVATION_V2_139A_LAYER3_FIELDS,
            getattr(ORACLE, "ROUTE_CANDIDATE_LAYER3_FIELDS", None),
            "[activation-v2-139a-missing-constant] "
            "ROUTE_CANDIDATE_LAYER3_FIELDS is absent or not exact",
        )

    def test_activation_v2_139a_enrichment_signature_is_exact(self) -> None:
        enricher = getattr(ORACLE, "_enrich_route_candidates", None)
        self.assertTrue(
            callable(enricher),
            "[activation-v2-139a-missing-helper] "
            "_enrich_route_candidates is absent",
        )
        assert callable(enricher)
        parameters = inspect.signature(enricher).parameters
        expected_names = (
            "candidates",
            "domain_specs",
            "domain_authority",
            "layer3_authority_by_primary",
            "maximum_layer3",
            "admission_authority",
        )
        self.assertEqual(expected_names, tuple(parameters))
        self.assertEqual(
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            parameters["candidates"].kind,
        )
        self.assertEqual(
            "list[dict[str, Any]]",
            parameters["candidates"].annotation,
        )
        expected_annotations = {
            "domain_specs": "dict[str, dict[str, Any]]",
            "domain_authority": "dict[str, Any]",
            "layer3_authority_by_primary": "dict[str, list[str]]",
            "maximum_layer3": "int",
            "admission_authority": "OracleAdmissionAuthority | None",
        }
        for name in expected_names[1:]:
            self.assertEqual(
                inspect.Parameter.KEYWORD_ONLY,
                parameters[name].kind,
            )
            expected_default = (
                None
                if name == "admission_authority"
                else inspect.Parameter.empty
            )
            self.assertIs(expected_default, parameters[name].default)
            self.assertEqual(
                expected_annotations[name],
                parameters[name].annotation,
            )
        self.assertEqual(
            "list[dict[str, Any]]",
            inspect.signature(enricher).return_annotation,
        )

    def test_invalid_main_fails_before_every_routing_stage(self) -> None:
        stage_names = (
            "_validated_brief_review_binding",
            "_normalize_route_prompt",
            "_build_route_candidates",
            "_enrich_route_candidates",
            "_compose_foundation_activation_candidates",
            "_select_route_cohort_candidate",
            "_project_route_selection",
            "validate_route_decision",
        )
        for stage_name in stage_names:
            self.assertTrue(
                callable(getattr(ORACLE, stage_name, None)),
                stage_name,
            )
        invalid_inputs = (
            {},
            {
                **_main_execution("t2g-invalid-producer"),
                "producer": "analysis-agent",
            },
            {
                **_main_execution("t2g-invalid-fields"),
                "unexpected": True,
            },
        )
        for index, invalid in enumerate(invalid_inputs):
            with self.subTest(index=index):
                patches = [
                    mock.patch.object(
                        ORACLE,
                        name,
                        wraps=getattr(ORACLE, name),
                    )
                    for name in stage_names
                ]
                spies = [patch.start() for patch in patches]
                try:
                    with self.assertRaises(ORACLE.RoutingIntegrityError):
                        ORACLE.route(
                            "Implement an accepted backend service change.",
                            main_execution=invalid,
                        )
                finally:
                    for patch in reversed(patches):
                        patch.stop()
                self.assertTrue(
                    all(spy.call_count == 0 for spy in spies),
                    {
                        name: spy.call_count
                        for name, spy in zip(stage_names, spies, strict=True)
                    },
                )

    def test_each_public_call_runs_every_route_once_stage_once(self) -> None:
        stage_names = (
            "_validated_main_execution_copy",
            "_validated_brief_review_binding",
        )
        missing = [
            name
            for name in stage_names
            if not callable(getattr(ORACLE, name, None))
        ]
        self.assertEqual(
            [],
            missing,
            "[activation-v3-route-once-missing-stage] every instrumented stage "
            "must exist before dynamic call-count proof",
        )
        for api_name in ("route", "route_with_trace"):
            with self.subTest(api=api_name):
                patches = [
                    mock.patch.object(
                        ORACLE,
                        name,
                        wraps=getattr(ORACLE, name),
                    )
                    for name in stage_names
                ]
                spies = [patch.start() for patch in patches]
                try:
                    getattr(ORACLE, api_name)(
                        "Implement an accepted backend service change.",
                        main_execution=_main_execution(f"t2g-once-{api_name}"),
                    )
                finally:
                    for patch in reversed(patches):
                        patch.stop()
                self.assertEqual(
                    {name: 1 for name in stage_names},
                    {
                        name: spy.call_count
                        for name, spy in zip(stage_names, spies, strict=True)
                    },
                )

    def test_activation_v3_binding_validation_has_one_route_once_call(
        self,
    ) -> None:
        tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
        route_impl = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_route_impl"
        )
        stage_calls = [
            (node.func.id, node.lineno)
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id
            in {
                "_validated_main_execution_copy",
                "_validated_brief_review_binding",
                "_normalize_route_prompt",
            }
        ]
        by_name = {
            name: [
                lineno
                for candidate_name, lineno in stage_calls
                if candidate_name == name
            ]
            for name in {
                "_validated_main_execution_copy",
                "_validated_brief_review_binding",
                "_normalize_route_prompt",
            }
        }
        self.assertEqual(
            1,
            len(by_name["_validated_brief_review_binding"]),
            "[activation-v3-route-once] _route_impl must call the binding "
            "validator exactly once",
        )
        self.assertEqual(1, len(by_name["_validated_main_execution_copy"]))
        self.assertEqual(1, len(by_name["_normalize_route_prompt"]))
        self.assertLess(
            by_name["_validated_main_execution_copy"][0],
            by_name["_validated_brief_review_binding"][0],
        )
        self.assertLess(
            by_name["_validated_brief_review_binding"][0],
            by_name["_normalize_route_prompt"][0],
        )

    def test_route_with_trace_returns_canonical_decision_and_winner_trace(
        self,
    ) -> None:
        observed = ORACLE.route_with_trace(
            "Implement an accepted backend service change.",
            main_execution=_main_execution("t2g-trace"),
        )
        self.assertEqual({"route_decision", "winner_trace"}, set(observed))
        self.assertEqual(ENVELOPE_FIELDS, set(observed["route_decision"]))
        self.assertEqual("full", observed["winner_trace"]["candidate_coverage"])
        self.assertEqual("proven", observed["winner_trace"]["route_once"])
        self.assertNotIn("route", observed)
        self.assertNotIn(
            "main_execution_provenance",
            observed["winner_trace"],
        )

    def test_eval_route_calls_canonical_route_once_and_projects_five_fields(
        self,
    ) -> None:
        main_execution = _main_execution("t2g-eval-wrapper")
        expected_decision = ORACLE.route(
            "Implement an accepted backend service change.",
            main_execution=main_execution,
        )
        with mock.patch.object(
            EVAL_ROUTING,
            "canonical_route",
            return_value=copy.deepcopy(expected_decision),
        ) as canonical:
            actual = EVAL_ROUTING.route(
                "Implement an accepted backend service change.",
                main_execution=main_execution,
            )
        canonical.assert_called_once()
        self.assertEqual(ROUTE_FIELDS, set(actual))
        self.assertEqual(
            _compatibility_projection(expected_decision),
            actual,
        )

    def test_route_impl_uses_shared_action_intent_for_decision_polarity(
        self,
    ) -> None:
        tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
        route_impl = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_route_impl"
        )
        decision_expressions = [
            node.test
            for node in ast.walk(route_impl)
            if isinstance(node, (ast.If, ast.IfExp))
        ]
        assignments: dict[str, list[ast.expr]] = {}
        for node in ast.walk(route_impl):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments.setdefault(target.id, []).append(node.value)
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None
            ):
                assignments.setdefault(node.target.id, []).append(node.value)
        decision_names = {
            node.id
            for expression in decision_expressions
            for node in ast.walk(expression)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        expanded_names: set[str] = set()
        while decision_names - expanded_names:
            name = (decision_names - expanded_names).pop()
            expanded_names.add(name)
            for expression in assignments.get(name, []):
                decision_expressions.append(expression)
                decision_names.update(
                    node.id
                    for node in ast.walk(expression)
                    if isinstance(node, ast.Name)
                    and isinstance(node.ctx, ast.Load)
                )

        violations: set[tuple[int, str]] = set()
        for expression in decision_expressions:
            for node in ast.walk(expression):
                if not isinstance(node, ast.Constant) or not isinstance(
                    node.value,
                    str,
                ):
                    continue
                tokens = re.findall(
                    r"[a-z]+",
                    node.value.casefold().replace("\\b", " "),
                )
                raw_audit_action = any(
                    tokens[index : index + 2]
                    in (["change", "audit"], ["update", "audit"])
                    for index in range(len(tokens) - 1)
                )
                if (
                    set(tokens).intersection({"implement", "implementing"})
                    or raw_audit_action
                ):
                    violations.add((node.lineno, node.value))
        self.assertEqual([], sorted(violations))

    def test_owner_internal_critical_suppression_is_source_scoped(
        self,
    ) -> None:
        route_impl_source = inspect.getsource(ORACLE._route_impl)
        tree = ast.parse(route_impl_source)
        critical_assignments = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "critical_evidence"
                for target in node.targets
            )
        ]
        self.assertEqual(1, len(critical_assignments))
        assignment = critical_assignments[0]
        self.assertIsInstance(assignment.value, ast.Call)
        assert isinstance(assignment.value, ast.Call)
        self.assertIsInstance(assignment.value.func, ast.Name)
        assert isinstance(assignment.value.func, ast.Name)
        self.assertEqual(
            "_critical_unknown_evidence",
            assignment.value.func.id,
        )
        self.assertFalse(
            any(
                isinstance(node, ast.ListComp)
                for node in ast.walk(assignment.value)
            )
        )

        critical_source = inspect.getsource(
            ORACLE._critical_unknown_evidence
        )
        self.assertIn(
            "owner_internal_structure_evidence",
            critical_source,
        )
        self.assertIn(
            "critical-source:module-boundary",
            critical_source,
        )

    def test_evaluator_case_count_is_derived_from_authoritative_fixture(
        self,
    ) -> None:
        cases = load_yaml_file(CASES_PATH)["cases"]
        report = EVAL_ROUTING.evaluate_routes()
        self.assertEqual(len(cases), report["case_count"])
        self.assertEqual(len(cases), report["passed_count"])
        self.assertEqual(6, report["schema_version"])
        self.assertEqual("full", report["candidate_coverage"])
        self.assertEqual("proven", report["route_once"])

        integrity_error = "injected duplicate route stage"
        with mock.patch.object(
            EVAL_ROUTING,
            "route_once_pipeline_errors",
            return_value=[integrity_error],
        ), mock.patch.object(
            EVAL_ROUTING,
            "canonical_route",
        ) as canonical, mock.patch.object(
            EVAL_ROUTING,
            "route_with_trace",
        ) as traced, mock.patch.object(
            EVAL_ROUTING,
            "_domain_metadata",
            wraps=EVAL_ROUTING._domain_metadata,
        ) as case_loop:
            failed = EVAL_ROUTING.evaluate_routes(
                _validate_capability_matrix=False,
            )
        canonical.assert_not_called()
        traced.assert_not_called()
        case_loop.assert_not_called()
        self.assertEqual("fail", failed["status"])
        self.assertEqual(0, failed["case_count"])
        self.assertEqual(0, failed["passed_count"])
        self.assertEqual([], failed["results"])
        self.assertEqual("unavailable", failed["candidate_coverage"])
        self.assertEqual("unavailable", failed["route_once"])
        self.assertIsNone(failed["legacy_route_count"])
        self.assertTrue(
            any(
                "routing-integrity-failure" in error
                and integrity_error in error
                for error in failed["errors"]
            )
        )

    def test_139c_build_signature_has_prompt_authority_and_no_snapshot(
        self,
    ) -> None:
        parameters = inspect.signature(
            ORACLE._build_route_candidates
        ).parameters
        expected_names = (
            "raw_candidates",
            "route_candidates",
            "normalized_text",
            "implementation_policy",
            "domain_specs",
            "admission_authority",
        )
        self.assertEqual(
            expected_names,
            tuple(parameters),
            "[activation-v2-139c-build-signature] builder must receive the "
            "normalized prompt and current authority, never a classifier "
            "snapshot",
        )
        for forbidden in (
            "domain_classification",
            "domain_authority",
            "layer3_authority_by_primary",
            "maximum_layer3",
            "snapshot",
            "text",
            "prompt",
        ):
            self.assertNotIn(forbidden, parameters)
        for name in expected_names[:2]:
            self.assertEqual(
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                parameters[name].kind,
            )
        for name in expected_names[2:]:
            self.assertEqual(
                inspect.Parameter.KEYWORD_ONLY,
                parameters[name].kind,
            )
            expected_default = (
                None
                if name == "admission_authority"
                else inspect.Parameter.empty
            )
            self.assertIs(
                expected_default,
                parameters[name].default,
            )
        self.assertEqual(
            "OracleAdmissionAuthority | None",
            parameters["admission_authority"].annotation,
        )

    def test_139c_build_calls_domain_classifier_exactly_once(self) -> None:
        normalized_text = "sentinel normalized routing text"
        domain_specs = ORACLE.domain_route_specs(
            load_yaml_file(
                ROOT / "src" / "registry" / "domain-skills.yaml"
            )
        )
        professional_data = load_yaml_file(
            ROOT / "src" / "registry" / "professional-skills.yaml"
        )
        implementation_policy = (
            ORACLE.professional_automatic_routing_authority(
                professional_data,
                context="activation-v2-139c-builder-policy",
            )["policy"]["implementation_owner"]
        )
        real_classifier = ORACLE.classify_domain_modifiers

        with mock.patch.object(
            ORACLE,
            "classify_domain_modifiers",
            wraps=real_classifier,
        ) as classifier:
            try:
                built = ORACLE._build_route_candidates(
                    [],
                    [],
                    normalized_text=normalized_text,
                    implementation_policy=implementation_policy,
                    domain_specs=domain_specs,
                )
            except TypeError as exc:
                self.fail(
                    "[activation-v2-139c-classifier-owner] builder rejected "
                    f"its accepted prompt-authority contract: {exc}"
                )
        self.assertEqual([], built)
        classifier.assert_called_once_with(
            normalized_text,
            specs=domain_specs,
        )
        self.assertIs(
            domain_specs,
            classifier.call_args.kwargs["specs"],
            "[activation-v2-139c-classifier-authority] classifier must receive "
            "the exact Domain specs object supplied to candidate construction",
        )

    def test_139c_pipeline_order_and_dynamic_counts(self) -> None:
        tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
        route_impl = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_route_impl"
        )
        stage_calls = sorted(
            (
                node.lineno,
                node.func.id,
            )
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ACTIVATION_V2_139C_DIRECT_STAGES
        )
        self.assertEqual(
            list(ACTIVATION_V2_139C_DIRECT_STAGES),
            [name for _lineno, name in stage_calls],
            "[activation-v2-139c-stage-order] _route_impl must directly call "
            "normalize/build/enrich/compose/select/project/validate exactly "
            "once and in order",
        )
        direct_compose_calls = [
            node.lineno
            for node in ast.walk(route_impl)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "compose_domain_extensions"
        ]
        self.assertEqual(
            [],
            direct_compose_calls,
            "[activation-v2-139c-no-direct-compose] _route_impl must not "
            "retain a direct post-selection Domain composition stage",
        )
        for api_name in ("route", "route_with_trace"):
            with self.subTest(api=api_name):
                patches = [
                    mock.patch.object(
                        ORACLE,
                        stage,
                        wraps=getattr(ORACLE, stage),
                    )
                    for stage in ACTIVATION_V2_139C_DIRECT_STAGES
                ]
                spies = [patch.start() for patch in patches]
                try:
                    getattr(ORACLE, api_name)(
                        "Implement an accepted backend service change.",
                        main_execution=_main_execution(
                            f"activation-v2-139c-stage-{api_name}"
                        ),
                    )
                finally:
                    for patch in reversed(patches):
                        patch.stop()
                self.assertEqual(
                    {
                        stage: 1
                        for stage in ACTIVATION_V2_139C_DIRECT_STAGES
                    },
                    {
                        stage: spy.call_count
                        for stage, spy in zip(
                            ACTIVATION_V2_139C_DIRECT_STAGES,
                            spies,
                            strict=True,
                        )
                    },
                )

    def test_139c_invalid_main_calls_no_pipeline_stage(self) -> None:
        invalid = {
            **_main_execution("activation-v2-139c-invalid-main"),
            "producer": "analysis-agent",
        }
        patches = [
            mock.patch.object(
                ORACLE,
                stage,
                wraps=getattr(ORACLE, stage),
            )
            for stage in ACTIVATION_V2_139C_DIRECT_STAGES
        ]
        spies = [patch.start() for patch in patches]
        try:
            with self.assertRaises(ORACLE.RoutingIntegrityError):
                ORACLE.route(
                    "Implement an accepted backend service change.",
                    main_execution=invalid,
                )
        finally:
            for patch in reversed(patches):
                patch.stop()
        self.assertEqual(
            {
                stage: 0
                for stage in ACTIVATION_V2_139C_DIRECT_STAGES
            },
            {
                stage: spy.call_count
                for stage, spy in zip(
                    ACTIVATION_V2_139C_DIRECT_STAGES,
                    spies,
                    strict=True,
                )
            },
        )

    def test_139c_static_guard_rejects_missing_duplicate_reordered_enrichment(
        self,
    ) -> None:
        guard_source = inspect.getsource(ORACLE.route_once_pipeline_errors)
        self.assertIn(
            '"_enrich_route_candidates"',
            guard_source,
            "[activation-v2-139c-static-guard] route-once guard must own the "
            "enrichment stage",
        )
        self.assertIn(
            '"_compose_foundation_activation_candidates"',
            guard_source,
            "[activation-v2-139c-static-guard] route-once guard must own the "
            "Foundation composition stage",
        )
        self.assertNotIn('"compose_domain_extensions"', guard_source)
        canonical_source = (
            "def _route_impl():\n"
            "    _normalize_route_prompt()\n"
            "    _build_route_candidates()\n"
            "    _enrich_route_candidates()\n"
            "    _compose_foundation_activation_candidates()\n"
            "    _select_route_cohort_candidate()\n"
            "    _project_route_selection()\n"
            "    validate_route_decision()\n"
            "\n"
            "def route():\n"
            "    return _route_impl()\n"
            "\n"
            "def route_with_trace():\n"
            "    return _route_impl()\n"
        )
        eval_source = (
            "def route():\n"
            "    return canonical_route()\n"
        )
        checker = ORACLE.route_once_pipeline_errors
        self.assertEqual([], checker(canonical_source, eval_source))
        self.assertEqual(
            [],
            checker(
                ORACLE_PATH.read_text(encoding="utf-8"),
                EVAL_ROUTING_PATH.read_text(encoding="utf-8"),
            ),
            "[activation-v2-139c-static-current] the actual route-once "
            "pipeline must satisfy the final seven-stage static contract",
        )
        mutations = {
            "missing": canonical_source.replace(
                "    _enrich_route_candidates()\n",
                "",
                1,
            ),
            "duplicate": canonical_source.replace(
                "    _enrich_route_candidates()\n",
                "    _enrich_route_candidates()\n"
                "    _enrich_route_candidates()\n",
                1,
            ),
            "reordered": canonical_source.replace(
                "    _build_route_candidates()\n"
                "    _enrich_route_candidates()\n",
                "    _enrich_route_candidates()\n"
                "    _build_route_candidates()\n",
                1,
            ),
        }
        for label, mutation in mutations.items():
            with self.subTest(mutation=label):
                self.assertTrue(
                    checker(mutation, eval_source),
                    f"{label} enrichment mutation must fail closed",
                )


if __name__ == "__main__":
    unittest.main()
