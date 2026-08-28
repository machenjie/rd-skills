#!/usr/bin/env python3
"""Score captured Hookless agent handoffs against observable task contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validation_utils import (
    CORE_CONTRACTS,
    ValidationProblem,
    behavior_eval_authority,
    load_yaml_file,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLES = ROOT / "evals/agent-behavior/professional-samples"
DEFAULT_OUTPUT = ROOT / "evals/agent-behavior/outputs"
SCORE_KEYS = (
    "route_once",
    "profile_boundary",
    "layer3_jit",
    "independent_review_boundary",
    "handoff_contract",
    "obligation_coverage",
    "validation_honesty",
    "forbidden_behavior_absence",
)
HANDOFF_FIELDS = (
    "result",
    "changed_files",
    "commands_run",
    "validation_results",
    "findings",
    "unverified_scope",
    "residual_risk",
    "recommended_next_step",
)


@dataclass
class Result:
    sample_id: str
    path: str
    ok: bool
    scores: dict[str, float]
    errors: list[str] = field(default_factory=list)


@dataclass
class ComparisonCase:
    case_id: str
    agent_packet: dict[str, Any]
    oracle: dict[str, Any]
    observations: dict[str, dict[str, Any]]
    reveal: dict[str, Any]
    arm_ids: tuple[str, str]


@dataclass
class ComparisonSuite:
    suite_id: str
    evidence_class: str
    live_evidence_status: str
    hardening_evidence_refs: list[str]
    artifact_paths: dict[str, Path]
    cases: list[ComparisonCase]
    verifier_captures: dict[str, dict[str, dict[str, Any]]]


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    if args.comparison_spec is not None:
        try:
            suite = _load_comparison_suite(args.comparison_spec)
            payload = _evaluate_comparison_suite(suite)
            output = _write_comparison(
                args.output_dir or DEFAULT_OUTPUT, args.format, payload
            )
        except (OSError, UnicodeError, ValueError, ValidationProblem) as exc:
            print(f"eval-agent-behavior: ERROR: {exc}", file=sys.stderr)
            return 1
        print(
            "eval-agent-behavior: "
            f"evaluated {len(suite.cases)} blind comparison case(s); "
            f"evidence={suite.evidence_class}; verdict={payload['verdict']}; "
            f"report={output}"
        )
        return 0
    samples = args.samples_dir or DEFAULT_SAMPLES
    try:
        professional, layer3 = _registries()
    except ValidationProblem as exc:
        print(f"eval-agent-behavior: ERROR: {exc}", file=sys.stderr)
        return 1
    paths = sorted(path for path in samples.rglob("*.yaml") if "raw" not in path.parts)
    results: list[Result] = []
    for path in paths:
        data = load_yaml_file(path)
        if isinstance(data, dict) and isinstance(data.get("expected"), dict):
            results.append(_score(path, data, professional, layer3))
    if not results:
        print("eval-agent-behavior: no Hookless captured samples found", file=sys.stderr)
        return 1
    aggregate = {
        key: sum(row.scores[key] for row in results) / len(results) for key in SCORE_KEYS
    }
    errors = [f"{row.path}: {message}" for row in results for message in row.errors]
    if args.min_score is not None:
        below = [key for key, value in aggregate.items() if value < args.min_score]
        if below:
            errors.append(
                f"static captured-score floor {args.min_score:.2f} missed: {', '.join(below)}"
            )
    payload = {
        "schema_version": 2,
        "architecture": "hookless-control-plane",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_kind": "captured-observable-handoff",
        "evidence_limitations": [
            "No agent was executed; samples are checked-in captures.",
            "Scores measure fixture conformance, not host performance, production accuracy, or adoption.",
        ],
        "samples_checked": len(results),
        "errors": errors,
        "aggregate": aggregate,
        "results": [asdict(row) for row in results],
    }
    output = _write(args.output_dir or DEFAULT_OUTPUT, args.format, payload)
    print(
        "eval-agent-behavior: "
        f"evaluated {len(results)} captured sample(s); errors={len(errors)}; "
        f"evidence=captured; report={output}"
    )
    for error in errors:
        print(f"eval-agent-behavior: ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-dir", type=Path)
    parser.add_argument(
        "--comparison-spec",
        type=Path,
        help=(
            "evaluate a physically separated blind OLD/NEW comparison manifest; "
            "this command scores supplied observations and never executes a host"
        ),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--format", choices=("markdown", "json", "yaml"), default="markdown")
    parser.add_argument(
        "--min-score",
        type=float,
        help="optional floor for static captured-fixture conformance; not a host-performance or product-quality threshold",
    )
    return parser.parse_args(argv)


def _load_comparison_suite(path: Path) -> ComparisonSuite:
    """Load one physically separated comparison suite and fail closed on drift."""

    contract = behavior_eval_authority(CORE_CONTRACTS)
    manifest = _mapping(_load_structured_file(path))
    manifest_fields = {
        "schema_version",
        "suite_id",
        "evidence_class",
        "live_evidence_status",
        "hardening_evidence_refs",
        "artifacts",
    }
    if set(manifest) != manifest_fields or manifest.get("schema_version") != 1:
        raise ValueError(
            f"{_rel(path)}: comparison manifest must use schema 1 fields "
            f"{sorted(manifest_fields)}"
        )
    suite_id = _nonempty_id(manifest.get("suite_id"), "comparison suite id")
    evidence_class = str(manifest.get("evidence_class", ""))
    live_status = str(manifest.get("live_evidence_status", ""))
    if evidence_class not in contract["evidence_classes"]:
        raise ValueError(f"{_rel(path)}: unknown evidence class {evidence_class!r}")
    if live_status not in contract["live_evidence_statuses"]:
        raise ValueError(f"{_rel(path)}: unknown live evidence status {live_status!r}")
    if evidence_class == "structural_only" and live_status != "not_collected":
        raise ValueError("structural-only comparison cannot claim collected live evidence")
    hardening_evidence_refs = manifest.get("hardening_evidence_refs")
    if (
        not isinstance(hardening_evidence_refs, list)
        or any(not isinstance(item, str) or not item.strip() for item in hardening_evidence_refs)
    ):
        raise ValueError(
            f"{_rel(path)}: hardening_evidence_refs must be a string list"
        )

    artifact_values = _mapping(manifest.get("artifacts"))
    roles = contract["artifact_roles"]
    if set(artifact_values) != set(roles):
        raise ValueError(
            f"{_rel(path)}: artifacts must be the Core roles {sorted(roles)}"
        )
    base = path.resolve().parent
    artifact_paths: dict[str, Path] = {}
    for role in roles:
        value = artifact_values[role]
        candidate = (base / str(value)).resolve()
        try:
            candidate.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"{_rel(path)}: artifact path escapes suite: {value}") from exc
        if not candidate.is_file():
            raise ValueError(f"{_rel(path)}: missing {role} artifact {value}")
        artifact_paths[role] = candidate
    if len(set(artifact_paths.values())) != len(roles):
        raise ValueError("comparison artifact roles must be physically separate files")

    artifacts = {
        role: _mapping(_load_structured_file(artifact_path))
        for role, artifact_path in artifact_paths.items()
    }
    role_cases: dict[str, list[dict[str, Any]]] = {}
    for role, artifact in artifacts.items():
        expected_fields = {"schema_version", "suite_id", "cases"}
        if (
            set(artifact) != expected_fields
            or artifact.get("schema_version") != 1
            or artifact.get("suite_id") != suite_id
            or not isinstance(artifact.get("cases"), list)
            or not artifact["cases"]
            or any(not isinstance(item, dict) for item in artifact["cases"])
        ):
            raise ValueError(
                f"{_rel(artifact_paths[role])}: malformed {role} suite artifact"
            )
        role_cases[role] = artifact["cases"]
    ids_by_role = {
        role: [str(item.get("id", "")) for item in rows]
        for role, rows in role_cases.items()
    }
    first_ids = ids_by_role[roles[0]]
    if (
        not all(ids_by_role[role] == first_ids for role in roles)
        or len(first_ids) != len(set(first_ids))
        or any(not item for item in first_ids)
    ):
        raise ValueError("comparison artifact roles must contain identical ordered case ids")

    cases: list[ComparisonCase] = []
    verifier_captures: dict[str, dict[str, dict[str, Any]]] = {}
    scenario_ids: set[str] = set()
    for index, artifact_id in enumerate(first_ids):
        packet = role_cases["agent_packet"][index]
        oracle = role_cases["oracle"][index]
        observation_row = role_cases["observations"][index]
        reveal = role_cases["reveal"][index]
        observations = _mapping(observation_row.get("arms"))
        arm_ids = _validate_case_parts(
            artifact_id, packet, oracle, observations, reveal
        )
        case_id = _nonempty_id(oracle.get("scenario_id"), "comparison scenario id")
        if case_id in scenario_ids:
            raise ValueError("comparison evaluator scenario ids must be unique")
        scenario_ids.add(case_id)
        cases.append(
            ComparisonCase(
                case_id=case_id,
                agent_packet=packet,
                oracle=oracle,
                observations=observations,
                reveal=reveal,
                arm_ids=arm_ids,
            )
        )
        verifier_captures[case_id] = _mapping(
            role_cases["verifier_capture"][index].get("arms")
        )
    return ComparisonSuite(
        suite_id=suite_id,
        evidence_class=evidence_class,
        live_evidence_status=live_status,
        hardening_evidence_refs=hardening_evidence_refs,
        artifact_paths=artifact_paths,
        cases=cases,
        verifier_captures=verifier_captures,
    )


def _validate_case_parts(
    case_id: str,
    packet: dict[str, Any],
    oracle: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    reveal: dict[str, Any],
) -> tuple[str, str]:
    contract = behavior_eval_authority(CORE_CONTRACTS)
    visible_contract = contract["agent_visible_contract"]
    packet_fields = set(visible_contract["packet_fields"])
    if set(packet) != packet_fields or packet.get("id") != case_id:
        raise ValueError(f"{case_id}: malformed agent packet")
    if re.fullmatch(visible_contract["opaque_id_pattern"], case_id) is None:
        raise ValueError(f"{case_id}: agent-visible packet id must be opaque")
    oracle_fields = {"id", "scenario_id", "relationship", "expected_behavior"}
    if set(oracle) != oracle_fields or oracle.get("id") != case_id:
        raise ValueError(f"{case_id}: malformed evaluator-only oracle")
    if not isinstance(observations, dict) or len(observations) != 2:
        raise ValueError(f"{case_id}: observations must contain exactly two blind arms")
    reveal_fields = {"id", "old_arm_id", "new_arm_id", "reveal_sequence"}
    if set(reveal) != reveal_fields or reveal.get("id") != case_id:
        raise ValueError(f"{case_id}: malformed post-capture reveal")

    agent_input = _mapping(packet.get("agent_input"))
    if set(agent_input) != set(visible_contract["payload_fields"]):
        raise ValueError(f"{case_id}: agent input fields are malformed")
    if re.fullmatch(
        visible_contract["opaque_id_pattern"],
        str(agent_input.get("task_id", "")),
    ) is None:
        raise ValueError(f"{case_id}: agent-visible task id must be opaque")
    if not isinstance(agent_input.get("prompt"), str) or not agent_input["prompt"].strip():
        raise ValueError(f"{case_id}: agent prompt must be non-empty")
    if not isinstance(agent_input.get("evidence_refs"), list):
        raise ValueError(f"{case_id}: agent evidence refs must be a list")
    if (
        any(not isinstance(value, str) or not value.strip() for value in agent_input["evidence_refs"])
        or len(agent_input["evidence_refs"]) != len(set(agent_input["evidence_refs"]))
        or any(
            re.fullmatch(r"evidence://opaque-[0-9]{3}", value) is None
            for value in agent_input["evidence_refs"]
        )
    ):
        raise ValueError(f"{case_id}: agent evidence refs must be neutral opaque ids")
    relationship = _mapping(oracle.get("relationship"))
    if set(relationship) != {"kind", "group_id"} or relationship.get("kind") not in {
        "standalone",
        "paraphrase",
        "boundary_transition",
    }:
        raise ValueError(f"{case_id}: relationship must be a supported comparison kind")
    _nonempty_id(relationship.get("group_id"), f"{case_id} relationship group")

    bindings = _mapping(packet.get("controlled_bindings"))
    if set(bindings) != set(contract["controlled_bindings"]):
        raise ValueError(f"{case_id}: controlled bindings do not match Core authority")
    if any(not isinstance(value, str) or not value.strip() for value in bindings.values()):
        raise ValueError(f"{case_id}: controlled bindings must be non-empty strings")
    if re.fullmatch(
        r"[0-9a-f]{64}", bindings["expected_behavior_definition_digest"]
    ) is None:
        raise ValueError(f"{case_id}: expected behavior binding must be digest-only")
    if bindings.get("task_id") != agent_input.get("task_id"):
        raise ValueError(f"{case_id}: controlled bindings do not bind the agent task")
    for field in visible_contract["opaque_binding_fields"]:
        if re.fullmatch(visible_contract["opaque_id_pattern"], bindings[field]) is None:
            raise ValueError(f"{case_id}: controlled binding {field} must be opaque")
    if bindings["agent_profile"] not in _profile_names(contract):
        raise ValueError(f"{case_id}: controlled agent profile is not Core-registered")

    raw_arm_ids = packet.get("blind_arm_ids")
    if (
        not isinstance(raw_arm_ids, list)
        or len(raw_arm_ids) != 2
        or len(set(raw_arm_ids)) != 2
        or any(not isinstance(item, str) for item in raw_arm_ids)
    ):
        raise ValueError(f"{case_id}: blind arm ids must be two unique strings")
    arm_ids = (raw_arm_ids[0], raw_arm_ids[1])
    for arm_id in arm_ids:
        if (
            re.fullmatch(r"arm-[a-z0-9]+", arm_id) is None
            or re.search(r"old|new|baseline|treatment|control", arm_id)
        ):
            raise ValueError(f"{case_id}: blind arm id {arm_id!r} is not opaque")
    if set(observations) != set(arm_ids):
        raise ValueError(f"{case_id}: observations do not match blind arm ids")
    captures: list[int] = []
    for arm_id, arm in observations.items():
        arm_fields = {
            "artifact_sha256",
            "capture_sequence",
            "controlled_bindings",
            "cost_metrics",
            "actual_behavior",
        }
        if set(arm) != arm_fields:
            raise ValueError(f"{case_id}/{arm_id}: observation fields are malformed")
        if re.fullmatch(r"[0-9a-f]{64}", str(arm.get("artifact_sha256", ""))) is None:
            raise ValueError(f"{case_id}/{arm_id}: artifact digest must be SHA-256")
        if arm.get("controlled_bindings") != bindings:
            raise ValueError(
                f"{case_id}/{arm_id}: controlled bindings differ between OLD/NEW runs"
            )
        sequence = arm.get("capture_sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            raise ValueError(f"{case_id}/{arm_id}: capture sequence must be positive")
        captures.append(sequence)
        cost = _mapping(arm.get("cost_metrics"))
        if set(cost) != set(contract["cost_metrics"]):
            raise ValueError(f"{case_id}/{arm_id}: cost metrics must derive from Core")
        for metric, value in cost.items():
            if value != "not_collected" and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{case_id}/{arm_id}: {metric} must be non-negative or not_collected"
                )
        actual = _mapping(arm.get("actual_behavior"))
        if set(actual) != {"routing", "review"}:
            raise ValueError(f"{case_id}/{arm_id}: actual behavior is malformed")
        _validate_actual_behavior(case_id, arm_id, actual, contract)
    if len(set(captures)) != 2:
        raise ValueError(f"{case_id}: blind observations need unique capture sequences")
    if {
        reveal.get("old_arm_id"),
        reveal.get("new_arm_id"),
    } != set(arm_ids):
        raise ValueError(f"{case_id}: reveal must map both opaque arms exactly once")
    reveal_sequence = reveal.get("reveal_sequence")
    if (
        not isinstance(reveal_sequence, int)
        or isinstance(reveal_sequence, bool)
        or reveal_sequence <= max(captures)
    ):
        raise ValueError(f"{case_id}: reveal sequence must follow both captures")

    expected = _mapping(oracle.get("expected_behavior"))
    if set(expected) != {"routing", "review"}:
        raise ValueError(f"{case_id}: expected behavior must define routing and review")
    _validate_expected_behavior(case_id, expected, contract)
    leaked_values = _oracle_leakage_values(expected)
    folded_packet = _fold(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    allowed_visible_facts = {str(bindings["agent_profile"])}
    leaked = [
        value
        for value in leaked_values
        if value not in allowed_visible_facts and _fold(value) in folded_packet
    ]
    if leaked:
        raise ValueError(
            f"{case_id}: agent packet contains evaluator answer leakage: {leaked}"
        )
    return arm_ids


def _oracle_leakage_values(expected: dict[str, Any]) -> list[str]:
    values: list[str] = []
    routing = _mapping(expected.get("routing"))
    review = _mapping(expected.get("review"))
    for field in (
        "start_profile",
        "primary_professional_skill",
        "primary_review_skill",
    ):
        value = routing.get(field) if field in routing else review.get(field)
        if isinstance(value, str) and "-" in value:
            values.append(value)
    for field, owner in (
        ("layer3_skills", routing),
        ("domain_extensions", routing),
        ("layer3_skills", review),
        ("specialist_reviews", review),
        ("required_findings", review),
    ):
        for value in _strings(owner.get(field)):
            if "-" in value or len(value) >= 12:
                values.append(value)
    for value in (
        routing.get("path"),
        routing.get("safe_fallback"),
        review.get("boundary_decision"),
        *contract_disposition_terms(),
    ):
        if isinstance(value, str):
            values.append(value)
    values.append("safe fallback")
    return sorted(set(values))


def contract_disposition_terms() -> list[str]:
    contract = behavior_eval_authority(CORE_CONTRACTS)
    return list(contract["finding_relations"]) + list(
        contract["finding_dispositions"].values()
    )


def _validate_string_list(value: Any, context: str) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"{context} must be a typed unique string list")
    return value


def _validate_expected_behavior(
    case_id: str, expected: dict[str, Any], contract: dict[str, Any]
) -> None:
    routing = _mapping(expected.get("routing"))
    if set(routing) != set(contract["observation_contract"]["routing_fields"]):
        raise ValueError(f"{case_id}: expected routing schema is malformed")
    for field in ("layer3_skills", "domain_extensions"):
        _validate_string_list(routing.get(field), f"{case_id}: expected routing {field}")
    if not isinstance(routing.get("safe_fallback"), bool):
        raise ValueError(f"{case_id}: expected safe_fallback must be a real boolean")
    review = _mapping(expected.get("review"))
    required = {
        "dispatch_expected", "primary_review_skill", "layer3_skills",
        "specialist_reviews", "boundary_decision", "initial_review_required",
        "repair_re_review_required", "frozen_scope",
        "covering_focused_re_review", "required_findings",
    }
    allowed = required | {"required_review_dimensions", "expected_findings", "dispatch_blockers"}
    if not required <= set(review) or not set(review) <= allowed:
        raise ValueError(f"{case_id}: expected review schema is malformed")
    for field in (
        "layer3_skills", "specialist_reviews", "frozen_scope",
        "required_findings", "required_review_dimensions", "dispatch_blockers",
    ):
        if field in review:
            _validate_string_list(review[field], f"{case_id}: expected review {field}")
    for field in (
        "dispatch_expected", "initial_review_required",
        "repair_re_review_required", "covering_focused_re_review",
    ):
        if not isinstance(review.get(field), bool):
            raise ValueError(f"{case_id}: expected review {field} must be a real boolean")
    _validate_scalar_authorities(
        routing,
        review,
        1 if review["dispatch_expected"] else 0,
        contract,
        f"{case_id}: expected behavior",
    )
    if "expected_findings" in review:
        _validate_findings(
            review["expected_findings"], contract["finding_oracle_fields"],
            contract, observed=False, context=f"{case_id}: expected findings",
        )


def _validate_actual_behavior(
    case_id: str, arm_id: str, actual: dict[str, Any], contract: dict[str, Any]
) -> None:
    context = f"{case_id}/{arm_id}"
    routing = _mapping(actual.get("routing"))
    if set(routing) != set(contract["observation_contract"]["routing_fields"]):
        raise ValueError(f"{context}: routing schema is malformed")
    for field in ("layer3_skills", "domain_extensions"):
        _validate_string_list(routing.get(field), f"{context}: routing {field}")
    if not isinstance(routing.get("safe_fallback"), bool):
        raise ValueError(f"{context}: routing safe_fallback must be a real boolean")
    review = _mapping(actual.get("review"))
    count = review.get("dispatch_count")
    if not isinstance(count, int) or isinstance(count, bool) or count not in {0, 1}:
        raise ValueError(f"{context}: review dispatch count must be integer zero or one")
    _validate_scalar_authorities(routing, review, count, contract, context)
    observation = contract["observation_contract"]
    expected_fields = (
        observation["dispatch_review_fields"]
        if count == 1
        else observation[
            "gated_no_dispatch_review_fields"
            if "main_dispatch_gate" in review
            else "no_dispatch_review_fields"
        ]
    )
    if set(review) != set(expected_fields):
        raise ValueError(f"{context}: review schema is malformed")
    for field in ("layer3_skills", "specialist_reviews"):
        _validate_string_list(review.get(field), f"{context}: review {field}")
    if count == 0:
        if "main_dispatch_gate" in review:
            gate = _mapping(review["main_dispatch_gate"])
            if set(gate) != set(contract["review_dispatch_gate_fields"]) or any(
                not isinstance(value, bool) for value in gate.values()
            ):
                raise ValueError(f"{context}: Main dispatch gate schema is malformed")
            if review.get("main_dispatch_surface") != contract[
                "main_dispatch_surface_contract"
            ]:
                raise ValueError(f"{context}: Main dispatch surface is malformed")
        return
    readiness = _mapping(review.get("review_input_ready"))
    actions = _mapping(review.get("reviewer_actions"))
    if (
        set(readiness) != set(contract["review_input_ready_fields"])
        or any(not isinstance(value, bool) for value in readiness.values())
        or set(actions) != set(contract["reviewer_forbidden_actions"])
        or any(not isinstance(value, bool) for value in actions.values())
    ):
        raise ValueError(f"{context}: review readiness/action boolean schema is malformed")
    initial = _mapping(review.get("initial_review"))
    if initial:
        if (
            set(initial) != set(observation["initial_review_fields"])
            or any(
                not isinstance(initial.get(field), bool)
                for field in ("completed_fixed_boundary", "stopped_after_ordinary_finding")
            )
        ):
            raise ValueError(f"{context}: initial review schema is malformed")
        for field in ("covered_review_dimensions", "returned_findings"):
            _validate_string_list(initial.get(field), f"{context}: initial review {field}")
    repair = _mapping(review.get("repair_re_review"))
    if repair:
        if set(repair) != set(observation["repair_rereview_fields"]):
            raise ValueError(f"{context}: repair re-review schema is malformed")
        for field in observation["repair_rereview_fields"]:
            if field == "frozen_scope":
                _validate_string_list(repair.get(field), f"{context}: repair {field}")
            elif not isinstance(repair.get(field), bool):
                raise ValueError(f"{context}: repair {field} must be a real boolean")
    _validate_findings(
        review.get("findings"), contract["finding_observation_fields"],
        contract, observed=True, context=f"{context}: findings",
    )


def _profile_names(contract: dict[str, Any]) -> set[str]:
    source = CORE_CONTRACTS["profile_contract"]["source_path"]
    profile_data = _mapping(_load_structured_file(ROOT / source))
    rows = profile_data.get("profiles")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Core profile source is malformed")
    names = {row.get("name") for row in rows}
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("Core profile source contains an invalid identity")
    return {str(name) for name in names}


def _validate_scalar_authorities(
    routing: dict[str, Any],
    review: dict[str, Any],
    dispatch_count: int,
    contract: dict[str, Any],
    context: str,
) -> None:
    scalar = contract["scalar_authority_contract"]
    route_contract = CORE_CONTRACTS["route_decision_contract"]
    path = routing.get("path")
    profile = routing.get("start_profile")
    primary = routing.get("primary_professional_skill")
    if not isinstance(path, str) or path not in route_contract["path_values"]:
        raise ValueError(f"{context}: routing path is outside Core authority")
    if (
        not isinstance(profile, str)
        or profile not in _profile_names(contract)
        or profile not in route_contract["path_start_profiles"].get(path, [])
    ):
        raise ValueError(f"{context}: routing start profile is outside Core mapping")
    registry_data = _mapping(
        load_yaml_file(ROOT / scalar["professional_registry_path"])
    )
    rows = registry_data.get("professional_skills")
    if not isinstance(rows, list):
        raise ValueError("Core professional registry is malformed")
    professional = {
        row.get("name"): row for row in rows if isinstance(row, dict)
    }
    primary_row = professional.get(primary) if isinstance(primary, str) else None
    if (
        not isinstance(primary, str)
        or not isinstance(primary_row, dict)
        or profile not in primary_row.get(scalar["professional_role_field"], [])
    ):
        raise ValueError(
            f"{context}: primary professional skill is outside the profile mapping"
        )
    allowed_boundaries = scalar["review_boundary_by_dispatch"][str(dispatch_count)]
    boundary = review.get("boundary_decision")
    if not isinstance(boundary, str) or boundary not in allowed_boundaries:
        raise ValueError(f"{context}: review boundary is outside Core dispatch mapping")
    review_skill = review.get("primary_review_skill")
    if dispatch_count == 0:
        if review_skill is not scalar["zero_dispatch_review_skill"]:
            raise ValueError(f"{context}: zero-dispatch review skill is invalid")
        return
    review_row = (
        professional.get(review_skill) if isinstance(review_skill, str) else None
    )
    if (
        not isinstance(review_skill, str)
        or not isinstance(review_row, dict)
        or "review-agent" not in review_row.get(scalar["professional_role_field"], [])
    ):
        raise ValueError(f"{context}: primary review skill is outside Core mapping")


def _validate_findings(
    value: Any,
    fields: list[str],
    contract: dict[str, Any],
    *,
    observed: bool,
    context: str,
) -> None:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{context} schema is malformed")
    identities: list[str] = []
    for finding in value:
        if set(finding) != set(fields):
            raise ValueError(f"{context} fields are malformed")
        identity = finding.get("finding_identity")
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError(f"{context} identity is malformed")
        identities.append(identity)
        relation = finding.get("relation")
        if relation not in contract["finding_relations"]:
            raise ValueError(f"{context} relation is malformed")
        if finding.get("disposition") != contract["finding_dispositions"][relation]:
            raise ValueError(f"{context} disposition is malformed")
        for field in ("material", "repair_eligible", "fresh"):
            if not isinstance(finding.get(field), bool):
                raise ValueError(f"{context} {field} must be a real boolean")
        _validate_string_list(finding.get("affected_scope"), f"{context} scope")
        if observed and not isinstance(finding.get("entered_repair"), bool):
            raise ValueError(f"{context} entered_repair must be a real boolean")
    if len(identities) != len(set(identities)):
        raise ValueError(f"{context} identities must be unique")


def _evaluate_comparison_suite(suite: ComparisonSuite) -> dict[str, Any]:
    contract = behavior_eval_authority(CORE_CONTRACTS)
    capture_verification = _verify_live_captures(suite, contract)
    old = _score_comparison_version(suite, "old")
    new = _score_comparison_version(suite, "new")
    old_quality = _quality_projection(old, contract)
    new_quality = _quality_projection(new, contract)
    live_verified = capture_verification["verified"]
    effective_live_status = contract["live_capture_contract"][
        "effective_live_evidence_status"
    ]
    verdict = _comparison_verdict_from_case_quality(
        old["case_quality"],
        new["case_quality"],
        live_evidence_verified=live_verified,
        hardening_evidence_verified=_hardening_evidence_verified(
            suite, capture_verification
        ),
    )
    return {
        "schema_version": 1,
        "architecture": "hookless-control-plane",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_kind": "blind-old-new-agent-behavior",
        "suite_id": suite.suite_id,
        "evidence_class": suite.evidence_class,
        "live_evidence_status": effective_live_status,
        "host_executed": live_verified,
        "live_capture_verification": capture_verification,
        "verdict": verdict,
        "claim_boundary": (
            contract["claim_boundaries"]["structural_only"]
            if suite.evidence_class == "structural_only"
            else contract["claim_boundaries"]["caller_supplied_capture"]
        ),
        "evidence_limitations": [
            "The evaluator scores supplied observations and does not execute a host.",
            "Caller-supplied captures can prove byte integrity but not host execution.",
            "Structural fixtures validate comparison plumbing and represented cases only.",
            "Token and turn proxies are not latency; elapsed is live evidence only when collected.",
        ],
        "cases_checked": len(suite.cases),
        "old": old,
        "new": new,
    }


def _score_comparison_version(
    suite: ComparisonSuite, version: str
) -> dict[str, Any]:
    contract = behavior_eval_authority(CORE_CONTRACTS)
    routing_rows: dict[str, list[float]] = {
        key: [] for key in contract["routing_metrics"]
    }
    review_rows: dict[str, list[float]] = {
        key: [] for key in contract["review_metrics"]
    }
    case_quality: list[dict[str, float]] = []
    version_cases: list[tuple[ComparisonCase, dict[str, Any], dict[str, Any]]] = []
    for case in suite.cases:
        arm_id = str(case.reveal[f"{version}_arm_id"])
        actual = _mapping(case.observations[arm_id]["actual_behavior"])
        expected = _mapping(case.oracle["expected_behavior"])
        version_cases.append((case, expected, actual))
        expected_route = _mapping(expected.get("routing"))
        actual_route = _mapping(actual.get("routing"))
        row: dict[str, float] = {}
        row["path_accuracy"] = float(actual_route.get("path") == expected_route.get("path"))
        row["start_profile_accuracy"] = float(
            actual_route.get("start_profile") == expected_route.get("start_profile")
        )
        row["primary_professional_skill_accuracy"] = float(
            actual_route.get("primary_professional_skill")
            == expected_route.get("primary_professional_skill")
        )
        layer_precision, layer_recall, layer_f1 = _set_scores(
            _strings(expected_route.get("layer3_skills")),
            _strings(actual_route.get("layer3_skills")),
        )
        row["layer3_precision"] = layer_precision
        row["layer3_recall"] = layer_recall
        row["layer3_f1"] = layer_f1
        expected_domains = set(_strings(expected_route.get("domain_extensions")))
        actual_domains = set(_strings(actual_route.get("domain_extensions")))
        row["domain_extension_fpr"] = len(actual_domains - expected_domains) / max(len(actual_domains), 1)
        row["domain_extension_fnr"] = len(expected_domains - actual_domains) / max(len(expected_domains), 1)
        expected_layers = set(_strings(expected_route.get("layer3_skills")))
        actual_layers = set(_strings(actual_route.get("layer3_skills")))
        row["unnecessary_layer3_load_rate"] = len(actual_layers - expected_layers) / max(len(actual_layers), 1)
        row["safe_fallback_accuracy"] = float(
            actual_route.get("safe_fallback") == expected_route.get("safe_fallback")
        )

        expected_review = _mapping(expected.get("review"))
        actual_review = _mapping(actual.get("review"))
        row["primary_review_skill_accuracy"] = float(
            actual_review.get("primary_review_skill")
            == expected_review.get("primary_review_skill")
        )
        review_precision, review_recall, review_f1 = _set_scores(
            _strings(expected_review.get("layer3_skills")),
            _strings(actual_review.get("layer3_skills")),
        )
        row["review_layer3_precision"] = review_precision
        row["review_layer3_recall"] = review_recall
        row["review_layer3_f1"] = review_f1
        expected_specialists = set(
            _strings(expected_review.get("specialist_reviews"))
        )
        actual_specialists = set(_strings(actual_review.get("specialist_reviews")))
        specialist_recall = (
            len(actual_specialists & expected_specialists) / len(expected_specialists)
            if expected_specialists else 1.0
        )
        row["required_specialist_review_recall"] = specialist_recall
        row["required_specialist_review_fnr"] = 1.0 - specialist_recall
        row["specialist_review_set_accuracy"] = float(actual_specialists == expected_specialists)
        row["unnecessary_specialist_review_rate"] = (
            len(actual_specialists - expected_specialists) / max(len(actual_specialists), 1)
        )
        row["review_boundary_correctness"] = float(
            _review_boundary_correct(expected_review, actual_review, contract)
        )
        route_exact = float(_route_signature(actual_route) == _route_signature(expected_route))
        row["paraphrase_stability"] = route_exact
        row["boundary_transition_accuracy"] = route_exact
        for metric in contract["routing_metrics"]:
            routing_rows[metric].append(row[metric])
        for metric in contract["review_metrics"]:
            review_rows[metric].append(row[metric])
        case_quality.append(
            {
                metric: (
                    1.0 - row[metric]
                    if contract["metric_directions"][metric] == "lower_is_better"
                    else row[metric]
                )
                for metric in contract["quality_metrics"]
            }
        )

    # Aggregate relationship metrics retain the existing group oracle. Per-case
    # rows above remain conservative and cannot hide an individual NEW regression.
    routing_rows["paraphrase_stability"] = _relationship_scores(version_cases, "paraphrase", expect_transition=False)
    routing_rows["boundary_transition_accuracy"] = _relationship_scores(version_cases, "boundary_transition", expect_transition=True)
    routing_metrics = {key: _mean(values) for key, values in routing_rows.items()}
    review_metrics = {key: _mean(values) for key, values in review_rows.items()}
    cost_metrics: dict[str, float | str] = {}
    for metric in contract["cost_metrics"]:
        values: list[float] = []
        not_collected = False
        for case in suite.cases:
            arm_id = str(case.reveal[f"{version}_arm_id"])
            value = case.observations[arm_id]["cost_metrics"][metric]
            if value == "not_collected":
                not_collected = True
                break
            values.append(float(value))
        cost_metrics[metric] = "not_collected" if not_collected else _mean(values)
    return {
        "routing_metrics": routing_metrics,
        "review_metrics": review_metrics,
        "cost_metrics": cost_metrics,
        "case_quality": case_quality,
    }


def _verify_live_captures(
    suite: ComparisonSuite, contract: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    capture_contract = contract["live_capture_contract"]
    seen_execution_ids: set[str] = set()
    for case in suite.cases:
        captures = _mapping(suite.verifier_captures.get(case.case_id))
        if set(captures) != set(case.arm_ids):
            errors.append(f"{case.case_id}: missing verifier-owned arm captures")
            continue
        for arm_id in case.arm_ids:
            capture = _mapping(captures.get(arm_id))
            if set(capture) != set(capture_contract["capture_fields"]):
                errors.append(f"{case.case_id}/{arm_id}: capture fields are malformed")
                continue
            raw = capture.get("capture_bytes")
            digest = capture.get("artifact_sha256")
            expected_digest = (
                hashlib.sha256(raw.encode("utf-8")).hexdigest()
                if isinstance(raw, str) else ""
            )
            try:
                captured_behavior = json.loads(raw) if isinstance(raw, str) else None
            except json.JSONDecodeError:
                captured_behavior = None
            observation = case.observations[arm_id]
            treatment = (
                "baseline" if arm_id == case.reveal["old_arm_id"] else "candidate"
            )
            provenance = _mapping(capture.get("provenance"))
            execution_id = provenance.get("source_execution_id")
            valid = (
                isinstance(raw, str)
                and captured_behavior == observation.get("actual_behavior")
                and re.fullmatch(r"[0-9a-f]{64}", str(digest or "")) is not None
                and digest == expected_digest == observation.get("artifact_sha256")
                and capture.get("capture_sequence") == observation.get("capture_sequence")
                and capture.get("controlled_bindings") == observation.get("controlled_bindings")
                and capture.get("treatment_source") == treatment
                and set(provenance) == set(capture_contract["provenance_fields"])
                and isinstance(provenance.get("verifier_id"), str)
                and bool(provenance.get("verifier_id"))
                and isinstance(execution_id, str)
                and bool(execution_id)
                and provenance.get("treatment_source") == treatment
                and provenance.get("host_id")
                == observation.get("controlled_bindings", {}).get("host_id")
                and provenance.get("model_id")
                == observation.get("controlled_bindings", {}).get("model_id")
                and provenance.get("agent_profile")
                == observation.get("controlled_bindings", {}).get("agent_profile")
                and provenance.get("repository_state_sha")
                == observation.get("controlled_bindings", {}).get(
                    "repository_state_sha"
                )
                and provenance.get("capture_sequence")
                == capture.get("capture_sequence")
                and provenance.get("reveal_sequence")
                == case.reveal["reveal_sequence"]
                and provenance.get("observed_before_reveal") is True
                and capture.get("capture_sequence") < case.reveal["reveal_sequence"]
            )
            if not valid or execution_id in seen_execution_ids:
                errors.append(f"{case.case_id}/{arm_id}: verifier capture binding is invalid")
                continue
            seen_execution_ids.add(str(execution_id))
    return {
        "verified": False,
        "integrity_verified": not errors,
        "authority": capture_contract["caller_supplied_authority"],
        "errors": errors,
    }


def _hardening_evidence_verified(
    suite: ComparisonSuite, capture_verification: dict[str, Any]
) -> bool:
    refs = suite.hardening_evidence_refs
    if not capture_verification.get("verified") or not refs:
        return False
    artifact_digest = hashlib.sha256(
        suite.artifact_paths["verifier_capture"].read_bytes()
    ).hexdigest()
    return refs == [f"sha256:{artifact_digest}"]


def _quality_projection(
    result: dict[str, Any], contract: dict[str, Any]
) -> dict[str, float]:
    raw = _mapping(result.get("routing_metrics")) | _mapping(
        result.get("review_metrics")
    )
    projection: dict[str, float] = {}
    for metric in contract["quality_metrics"]:
        value = float(raw[metric])
        projection[metric] = (
            1.0 - value
            if contract["metric_directions"][metric] == "lower_is_better"
            else value
        )
    return projection


def _comparison_verdict(
    old_quality: dict[str, float],
    new_quality: dict[str, float],
    *,
    evidence_class: str,
    live_evidence_status: str,
    hardening_only: bool,
) -> str:
    contract = behavior_eval_authority(CORE_CONTRACTS)
    policy = contract["verdict_policy"]
    if evidence_class != "live_agent" or live_evidence_status != "collected":
        return str(policy["missing-live-agent-data"])
    metrics = contract["quality_metrics"]
    if set(old_quality) != set(metrics) or set(new_quality) != set(metrics):
        return str(policy["missing-live-agent-data"])
    epsilon = 1e-12
    if any(new_quality[key] + epsilon < old_quality[key] for key in metrics):
        return str(policy["quality_regression"])
    old_correct = all(old_quality[key] >= 1.0 - epsilon for key in metrics)
    new_correct = all(new_quality[key] >= 1.0 - epsilon for key in metrics)
    if old_correct and new_correct:
        choices = policy["old-correct-new-correct"]
        return str(choices[1] if hardening_only else choices[0])
    if new_correct and not old_correct:
        return str(policy["old-fail-new-complete-succeed"])
    return str(policy["old-correct-new-correct"][0])


def _comparison_verdict_from_case_quality(
    old_cases: list[dict[str, float]],
    new_cases: list[dict[str, float]],
    *,
    live_evidence_verified: bool,
    hardening_evidence_verified: bool,
) -> str:
    contract = behavior_eval_authority(CORE_CONTRACTS)
    policy = contract["verdict_policy"]
    metrics = contract["quality_metrics"]
    if (
        not live_evidence_verified
        or not old_cases
        or len(old_cases) != len(new_cases)
        or any(set(row) != set(metrics) for row in old_cases + new_cases)
    ):
        return str(policy["missing-live-agent-data"])
    epsilon = 1e-12
    if any(
        new[metric] + epsilon < old[metric]
        for old, new in zip(old_cases, new_cases)
        for metric in metrics
    ):
        return str(policy["quality_regression"])
    old_complete = all(
        row[metric] >= 1.0 - epsilon for row in old_cases for metric in metrics
    )
    new_complete = all(
        row[metric] >= 1.0 - epsilon for row in new_cases for metric in metrics
    )
    if new_complete and not old_complete:
        return str(policy["old-fail-new-complete-succeed"])
    if old_complete and new_complete:
        choices = policy["old-correct-new-correct"]
        return str(choices[1] if hardening_evidence_verified else choices[0])
    return str(policy["incomplete-non-regressing"])


def _relationship_scores(
    rows: list[tuple[ComparisonCase, dict[str, Any], dict[str, Any]]],
    kind: str,
    *,
    expect_transition: bool,
) -> list[float]:
    groups: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for case, expected, actual in rows:
        relationship = _mapping(case.oracle.get("relationship"))
        if relationship.get("kind") == kind:
            groups.setdefault(str(relationship.get("group_id")), []).append(
                (_mapping(expected.get("routing")), _mapping(actual.get("routing")))
            )
    scores: list[float] = []
    for group in groups.values():
        if len(group) < 2:
            scores.append(0.0)
            continue
        expected_signatures = [_route_signature(expected) for expected, _ in group]
        actual_signatures = [_route_signature(actual) for _, actual in group]
        all_match = all(
            actual == expected
            for actual, expected in zip(actual_signatures, expected_signatures)
        )
        expected_changed = len(set(expected_signatures)) > 1
        actual_changed = len(set(actual_signatures)) > 1
        relation_ok = (
            expected_changed and actual_changed
            if expect_transition
            else not expected_changed and not actual_changed
        )
        scores.append(float(all_match and relation_ok))
    return scores or [0.0]


def _route_signature(route: dict[str, Any]) -> tuple[Any, ...]:
    return (
        route.get("path"),
        route.get("start_profile"),
        route.get("primary_professional_skill"),
        tuple(_strings(route.get("layer3_skills"))),
        tuple(_strings(route.get("domain_extensions"))),
        route.get("safe_fallback"),
    )


def _review_boundary_correct(
    expected: dict[str, Any],
    actual: dict[str, Any],
    contract: dict[str, Any],
) -> bool:
    dispatch_expected = expected.get("dispatch_expected") is True
    dispatch_count = actual.get("dispatch_count")
    if _strings(actual.get("specialist_reviews")) != _strings(
        expected.get("specialist_reviews")
    ):
        return False
    if not dispatch_expected:
        if dispatch_count != 0 or actual.get("boundary_decision") != expected.get(
            "boundary_decision"
        ):
            return False
        blockers = set(_strings(expected.get("dispatch_blockers")))
        if blockers:
            gate = _mapping(actual.get("main_dispatch_gate"))
            if set(gate) != set(contract["review_dispatch_gate_fields"]):
                return False
            return (
                actual.get("main_dispatch_surface")
                == contract["main_dispatch_surface_contract"]
                and all(isinstance(value, bool) for value in gate.values())
                and {field for field, value in gate.items() if value is False}
                == blockers
            )
        return "main_dispatch_gate" not in actual
    if dispatch_count != 1:
        return False
    readiness = _mapping(actual.get("review_input_ready"))
    if set(readiness) != set(contract["review_input_ready_fields"]) or not all(
        readiness.values()
    ):
        return False
    actions = _mapping(actual.get("reviewer_actions"))
    if set(actions) != set(contract["reviewer_forbidden_actions"]) or any(
        actions.values()
    ):
        return False
    if actual.get("boundary_decision") != expected.get("boundary_decision"):
        return False
    initial = _mapping(actual.get("initial_review"))
    if expected.get("initial_review_required") is True:
        if (
            initial.get("completed_fixed_boundary") is not True
            or initial.get("stopped_after_ordinary_finding") is not False
            or not set(_strings(expected.get("required_findings"))).issubset(
                set(_strings(initial.get("returned_findings")))
            )
            or not set(
                _strings(expected.get("required_review_dimensions"))
            ).issubset(set(_strings(initial.get("covered_review_dimensions"))))
        ):
            return False
    repair = _mapping(actual.get("repair_re_review"))
    if expected.get("repair_re_review_required") is True:
        if (
            repair.get("validation_after_latest_edit") is not True
            or repair.get("uses_latest_repair_diff") is not True
            or repair.get("uses_initial_review_diff") is not False
            or repair.get("focused_scope_only") is not True
            or _strings(repair.get("frozen_scope"))
            != _strings(expected.get("frozen_scope"))
            or repair.get("covering_focused_re_review")
            is not expected.get("covering_focused_re_review")
            or repair.get("duplicate_final_review_dispatched") is not False
        ):
            return False
    for finding in actual.get("findings", []):
        if not isinstance(finding, dict):
            return False
        relation = finding.get("relation")
        if relation not in contract["finding_relations"]:
            return False
        if relation in {"adjacent", "scope-blocker"} and finding.get(
            "entered_repair"
        ) is not False:
            return False
        expected_disposition = contract["finding_dispositions"].get(relation)
        if finding.get("disposition") != expected_disposition:
            return False
        if finding.get("fresh") is not True:
            return False
        if relation == "current-task":
            should_repair = (
                finding.get("material") is True
                and finding.get("repair_eligible") is True
            )
            if finding.get("entered_repair") is not should_repair:
                return False
        elif finding.get("repair_eligible") is not False:
            return False
    expected_findings = expected.get("expected_findings")
    if expected_findings is not None:
        projected = [
            {key: finding.get(key) for key in contract["finding_oracle_fields"]}
            for finding in actual.get("findings", [])
            if isinstance(finding, dict)
        ]
        if projected != expected_findings:
            return False
    return True


def _set_scores(expected: list[str], actual: list[str]) -> tuple[float, float, float]:
    expected_set = set(expected)
    actual_set = set(actual)
    true_positive = len(expected_set & actual_set)
    precision = true_positive / len(actual_set) if actual_set else float(not expected_set)
    recall = true_positive / len(expected_set) if expected_set else float(not actual_set)
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return precision, recall, f1


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _nonempty_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is None:
        raise ValueError(f"{context} must be a non-empty kebab-case id")
    return value


def _load_structured_file(path: Path) -> Any:
    """Load JSON-compatible YAML exactly even without an optional YAML package."""

    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return load_yaml_file(path)


def _registries() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    pro = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
    foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    if not all(isinstance(item, dict) for item in (pro, foundation, domain)):
        raise ValidationProblem("three-layer Skill registries must be mappings")
    professional = {
        str(row.get("name", "")): row
        for row in pro.get("professional_skills", [])
        if isinstance(row, dict)
    }
    layer3 = {
        str(row.get("name", "")): row
        for row in foundation.get("foundation_skills", [])
        if isinstance(row, dict)
    } | {
        str(row.get("name", "")): row
        for row in domain.get("domain_skills", [])
        if isinstance(row, dict)
    }
    return professional, layer3


def _score(
    path: Path,
    data: dict[str, Any],
    professional: dict[str, dict[str, Any]],
    layer3: dict[str, dict[str, Any]],
) -> Result:
    expected = _mapping(data.get("expected"))
    actual = _mapping(data.get("actual"))
    profile = str(actual.get("profile", ""))
    primary = str(actual.get("primary_skill", ""))
    review = str(actual.get("review_skill", ""))
    selected_layer3 = _strings(actual.get("layer3_skills"))
    scores = {key: 0.0 for key in SCORE_KEYS}
    errors: list[str] = []

    route_match = all(
        actual.get(field) == expected.get(field)
        for field in ("profile", "primary_skill", "layer3_skills", "review_skill")
    )
    scores["route_once"] = float(route_match and primary in professional)
    if not scores["route_once"]:
        errors.append("actual route does not match the one-primary expected route")

    primary_roles = _strings(_mapping(professional.get(primary)).get("role_support"))
    scores["profile_boundary"] = float(profile in primary_roles)
    if not scores["profile_boundary"]:
        errors.append(f"profile '{profile}' is not supported by primary Skill '{primary}'")

    scores["layer3_jit"] = float(
        len(selected_layer3) <= 3
        and len(selected_layer3) == len(set(selected_layer3))
        and all(name in layer3 for name in selected_layer3)
        and all(
            name
            in set(_strings(_mapping(professional.get(primary)).get("layer3_candidates")))
            for name in selected_layer3
        )
        and all(
            profile in _strings(_mapping(layer3.get(name)).get("role_support"))
            for name in selected_layer3
        )
    )
    if not scores["layer3_jit"]:
        errors.append(
            "Layer 3 selection is unknown, duplicated, exceeds the JIT budget, "
            "is not declared by the primary Skill, or is incompatible with the dispatch profile"
        )

    review_roles = _strings(_mapping(professional.get(review)).get("role_support"))
    scores["independent_review_boundary"] = float("review-agent" in review_roles)
    if not scores["independent_review_boundary"]:
        errors.append(f"Review Skill '{review}' does not support review-agent")

    handoff = _mapping(actual.get("handoff"))
    scores["handoff_contract"] = float(
        all(field in handoff and handoff[field] is not None and handoff[field] != "" for field in HANDOFF_FIELDS)
    )
    if not scores["handoff_contract"]:
        errors.append("natural-language handoff is missing required observable fields")

    folded_handoff = _fold(json.dumps(handoff, ensure_ascii=False))
    obligations = _strings(expected.get("required_professional_obligations"))
    scores["obligation_coverage"] = (
        sum(_fold(item) in folded_handoff for item in obligations) / len(obligations)
        if obligations
        else 0.0
    )
    if scores["obligation_coverage"] < 1.0:
        errors.append("captured handoff misses a professional obligation")

    validation = _fold(str(handoff.get("validation_results", "")))
    honest_unverified = (
        "not run" not in validation
        and "not verified" not in validation
        or bool(str(handoff.get("unverified_scope", "")).strip())
        and bool(str(handoff.get("residual_risk", "")).strip())
    )
    scores["validation_honesty"] = float(bool(validation) and honest_unverified)
    if not scores["validation_honesty"]:
        errors.append("validation result is absent or an unverified result lacks proof limits")

    forbidden = _strings(expected.get("forbidden_behaviors"))
    scores["forbidden_behavior_absence"] = float(
        not any(_fold(item) in folded_handoff for item in forbidden)
    )
    if not scores["forbidden_behavior_absence"]:
        errors.append("captured handoff contains a forbidden shortcut")
    return Result(
        sample_id=str(data.get("id", _rel(path))),
        path=_rel(path),
        ok=not errors,
        scores=scores,
        errors=errors,
    )


def _write(directory: Path, report_format: str, payload: dict[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[report_format]
    path = directory / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-agent-behavior-eval.{extension}"
    if report_format == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif report_format == "yaml":
        # JSON is valid YAML and avoids a serializer dependency.
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        lines = [
            "# Hookless Agent Behavior Captures",
            "",
            "> Checked-in captures only; no host-performance, production-accuracy, or adoption claim.",
            "",
            f"- Samples checked: {payload['samples_checked']}",
            f"- Errors: {len(payload['errors'])}",
            "",
            "| Sample | OK | " + " | ".join(SCORE_KEYS) + " |",
            "|---|---|" + "---:|" * len(SCORE_KEYS),
        ]
        for row in payload["results"]:
            scores = " | ".join(f"{row['scores'][key]:.2f}" for key in SCORE_KEYS)
            lines.append(f"| `{row['sample_id']}` | {row['ok']} | {scores} |")
        text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _write_comparison(
    directory: Path, report_format: str, payload: dict[str, Any]
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[
        report_format
    ]
    path = directory / (
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        f"-agent-behavior-comparison.{extension}"
    )
    if report_format in {"json", "yaml"}:
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        lines = [
            "# Blind OLD / NEW Agent Behavior Comparison",
            "",
            "> The evaluator scores supplied observations; it does not execute a host.",
            "",
            f"- Suite: `{payload['suite_id']}`",
            f"- Evidence class: `{payload['evidence_class']}`",
            f"- Live evidence: `{payload['live_evidence_status']}`",
            f"- Verdict: `{payload['verdict']}`",
            f"- Cases checked: {payload['cases_checked']}",
            "",
            "| Side | Routing metrics | Review metrics | Cost metrics |",
            "|---|---|---|---|",
        ]
        for side in ("old", "new"):
            lines.append(
                f"| {side.upper()} | "
                f"`{json.dumps(payload[side]['routing_metrics'], sort_keys=True)}` | "
                f"`{json.dumps(payload[side]['review_metrics'], sort_keys=True)}` | "
                f"`{json.dumps(payload[side]['cost_metrics'], sort_keys=True)}` |"
            )
        text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strings(value: Any) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _fold(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
