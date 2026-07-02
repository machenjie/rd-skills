"""Runtime process artifact and transition validators."""

from __future__ import annotations

import json
from typing import Any

from runtime_governance.process_phase import (
    phase_transition_allowed,
    validate_phase_review_result as _validate_phase_review_result,
    validate_process_phase_ledger as _validate_process_phase_ledger,
)

from .phase_contracts import (
    CORE_PHASES,
    GENERIC_DDD_MARKERS,
    GENERIC_PUBLIC_API_MARKERS,
    GENERIC_TRACE_MARKERS,
    REQUIRED_PROCESS_FIELDS,
    SDD_ASSUMPTION_POLICY_MARKER,
    SDD_CHOICE_STATUSES,
    SDD_GENERIC_RATIONALES,
    SDD_HIGH_RISK_SAFE_ASSUMPTION_KEYWORDS,
    SDD_MATERIAL_CHOICE_KEYWORDS,
    SDD_NO_CHOICE_RATIONALE_FIELDS,
    SDD_SAFE_ASSUMPTION_MARKER_GROUPS,
    SDD_SPECIFIC_RATIONALE_MARKERS,
)


def validate_phase_artifact(phase: str, artifact: Any) -> list[str]:
    """Validate one PDD, DDD, SDD, or TDD artifact."""
    normalized = str(phase or "").strip().casefold()
    if normalized not in CORE_PHASES:
        return [f"unknown phase {phase!r}"]
    if not isinstance(artifact, dict):
        return [f"{normalized.upper()} artifact must be an object"]
    errors: list[str] = []
    errors.extend(_required_field_errors(normalized, artifact))
    if normalized == "pdd":
        errors.extend(_pdd_errors(artifact))
    elif normalized == "ddd":
        errors.extend(_ddd_errors(artifact))
    elif normalized == "sdd":
        errors.extend(_sdd_errors(artifact))
    elif normalized == "tdd":
        errors.extend(_tdd_errors(artifact))
    return _unique(errors)


def validate_phase_review_result(review_result: dict[str, Any]) -> list[str]:
    return _validate_phase_review_result(review_result)


def validate_process_phase_ledger(ledger: dict[str, Any]) -> list[str]:
    return _validate_process_phase_ledger(ledger)


def validate_phase_transition(ledger: dict[str, Any], requested_next_phase: str) -> list[str]:
    allowed, blockers = phase_transition_allowed(ledger, requested_next_phase)
    return [] if allowed else blockers


def validate_process_trace_facts(facts: dict[str, Any]) -> list[str]:
    """Validate a compact process_facts object using runtime checks."""
    if not isinstance(facts, dict):
        return ["process_facts must be an object"]
    errors: list[str] = []
    for phase in CORE_PHASES:
        errors.extend(validate_phase_artifact(phase, facts.get(phase)))
    errors.extend(_cross_phase_mapping_errors(facts))
    errors.extend(_generic_trace_errors(facts))
    return _unique(errors)


def _required_field_errors(phase: str, artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_PROCESS_FIELDS.get(phase, ()):
        if not _has_evidence(artifact.get(field)):
            errors.append(f"{phase.upper()}.{field} is required")
    return errors


def _pdd_errors(pdd: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(pdd.get("problem"), str) or not pdd.get("problem", "").strip():
        errors.append("PDD.problem must be a non-empty string")
    for field in (
        "user_or_system_impact",
        "acceptance_criteria",
        "constraints",
        "non_goals",
        "risk_surfaces",
        "validation_signal",
    ):
        if not _string_list(pdd.get(field)):
            errors.append(f"PDD.{field} must be a non-empty list")
    acceptance = " ".join(_string_list(pdd.get("acceptance_criteria"))).casefold()
    if _contains_any(acceptance, GENERIC_TRACE_MARKERS):
        errors.append("PDD acceptance criteria are generic template content")
    return errors


def _ddd_errors(ddd: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("domain_terms", "ownership_decision", "side_effect_boundaries"):
        if not _string_list(ddd.get(field)):
            errors.append(f"DDD.{field} must be a non-empty list")
    invariants = _string_list(ddd.get("invariants"))
    if not invariants and not str(ddd.get("no_domain_state_rationale", "")).strip():
        errors.append("DDD requires invariants or explicit no-domain-state rationale")
    if invariants and all(_contains_any(item, GENERIC_DDD_MARKERS) for item in invariants):
        errors.append("DDD invariants are generic template content")
    return errors


def _sdd_errors(sdd: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("modules", "public_api", "error_contract", "failure_modes"):
        if not _string_list(sdd.get(field)):
            errors.append(f"SDD.{field} must be a non-empty list")
    if not isinstance(sdd.get("logging_decision"), dict):
        errors.append("SDD.logging_decision must be an object")
    errors.extend(_sdd_choice_errors(sdd))
    public_api = _string_list(sdd.get("public_api"))
    if public_api and all(_contains_any(item, GENERIC_PUBLIC_API_MARKERS) for item in public_api):
        errors.append("SDD public_api is generic template content")
    return errors


def _sdd_choice_errors(sdd: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    choices = sdd.get("design_decision_points")
    if not isinstance(choices, list):
        return ["SDD.design_decision_points must be a list"]
    policy = str(sdd.get("assumption_policy", "")).strip()
    if not policy or SDD_ASSUMPTION_POLICY_MARKER not in policy:
        errors.append(f"SDD.assumption_policy must include {SDD_ASSUMPTION_POLICY_MARKER!r}")
    material_terms = _keyword_hits(_sdd_scope_text(sdd), SDD_MATERIAL_CHOICE_KEYWORDS)
    if not choices:
        rationale = _sdd_no_choice_rationale(sdd)
        if not rationale:
            errors.append("SDD.design_decision_points empty requires no_design_choice_rationale")
        elif _is_generic_sdd_rationale(rationale):
            errors.append("SDD.no_design_choice_rationale is generic and must cite concrete evidence")
        if material_terms and not _sdd_rationale_has_specific_evidence(rationale):
            errors.append("SDD material design trigger requires source/user/repository/reuse evidence")
        return errors
    for index, point in enumerate(choices, start=1):
        if not isinstance(point, dict):
            errors.append(f"SDD.design_decision_points[{index}] must be an object")
            continue
        errors.extend(_sdd_decision_point_errors(point, index=index))
    return errors


def _sdd_decision_point_errors(point: dict[str, Any], *, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"SDD.design_decision_points[{index}]"
    for field in ("id", "decision", "trigger"):
        if not str(point.get(field, "")).strip():
            errors.append(f"{prefix}.{field} must be non-empty")
    status = str(point.get("user_choice_status", "")).strip()
    if status not in SDD_CHOICE_STATUSES:
        errors.append(f"{prefix}.user_choice_status is invalid")
    blocking = point.get("blocking")
    if not isinstance(blocking, bool):
        errors.append(f"{prefix}.blocking must be true or false")
    risk_text = json.dumps(
        {
            "decision": point.get("decision"),
            "trigger": point.get("trigger"),
            "options": point.get("options"),
            "safe_default_if_user_unavailable": point.get("safe_default_if_user_unavailable"),
        },
        sort_keys=True,
    ).casefold()
    material_terms = _keyword_hits(risk_text, SDD_MATERIAL_CHOICE_KEYWORDS)
    high_risk_terms = _keyword_hits(risk_text, SDD_HIGH_RISK_SAFE_ASSUMPTION_KEYWORDS)
    needs_options = blocking is True or status == "required" or bool(material_terms) or bool(high_risk_terms)
    if needs_options:
        errors.extend(_option_errors(point, prefix=prefix, require_two=blocking is True or status == "required"))
        if not str(point.get("recommended_option", "")).strip():
            errors.append(f"{prefix}.recommended_option must be non-empty")
        if not str(point.get("why_user_choice_is_needed", "")).strip():
            errors.append(f"{prefix}.why_user_choice_is_needed must be non-empty")
        if not str(point.get("residual_risk", "")).strip():
            errors.append(f"{prefix}.residual_risk must be non-empty")
    if blocking is True and status == "required":
        errors.append(f"{prefix} is blocking and requires user choice, so SDD cannot be reviewed")
    if status == "resolved" and not _resolved_evidence(point):
        errors.append(f"{prefix}.user_choice_status=resolved requires resolution_evidence")
    if status == "not_required":
        rationale = _decision_rationale(point)
        if _is_generic_sdd_rationale(rationale):
            errors.append(f"{prefix}.user_choice_status=not_required requires concrete rationale")
        if (material_terms or high_risk_terms) and not _sdd_rationale_has_specific_evidence(rationale):
            errors.append(f"{prefix}.user_choice_status=not_required for material choice requires evidence")
    if status == "assumed_with_rationale":
        text = json.dumps(point, sort_keys=True).casefold()
        if not _safe_assumption_rationale_ok(text):
            errors.append(f"{prefix}.assumed_with_rationale must state local, reversible, conventional, and acceptance-neutral rationale")
        if high_risk_terms:
            errors.append(f"{prefix}.assumed_with_rationale cannot cover high-risk material choice")
    return errors


def _option_errors(point: dict[str, Any], *, prefix: str, require_two: bool) -> list[str]:
    options = point.get("options")
    if not isinstance(options, list) or not options:
        return [f"{prefix}.options must be a non-empty list"]
    errors: list[str] = []
    if require_two and len(options) < 2:
        errors.append(f"{prefix}.options must include at least 2 options")
    for option_index, option in enumerate(options, start=1):
        if not isinstance(option, dict):
            errors.append(f"{prefix}.options[{option_index}] must be an object")
            continue
        if not str(option.get("label", "")).strip() or not str(option.get("summary", "")).strip():
            errors.append(f"{prefix}.options[{option_index}] must include label and summary")
        if require_two and not (_has_evidence(option.get("pros")) or _has_evidence(option.get("cons"))):
            errors.append(f"{prefix}.options[{option_index}] must include pros or cons")
    return errors


def _tdd_errors(tdd: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("acceptance_to_tests", "invariant_to_tests_or_code", "public_api_to_tests"):
        value = tdd.get(field)
        if isinstance(value, bool):
            errors.append(f"TDD.{field} must be a mapping, not a boolean")
        elif not isinstance(value, dict) or not _has_evidence(value):
            errors.append(f"TDD.{field} must be a non-empty mapping")
    for field in ("failure_mode_tests", "validation_commands"):
        if isinstance(tdd.get(field), bool):
            errors.append(f"TDD.{field} must be evidence, not a boolean")
        elif not _string_list(tdd.get(field)) and not _has_evidence(tdd.get(field)):
            errors.append(f"TDD.{field} must be non-empty")
    return errors


def _cross_phase_mapping_errors(facts: dict[str, Any]) -> list[str]:
    pdd = facts.get("pdd") if isinstance(facts.get("pdd"), dict) else {}
    ddd = facts.get("ddd") if isinstance(facts.get("ddd"), dict) else {}
    sdd = facts.get("sdd") if isinstance(facts.get("sdd"), dict) else {}
    tdd = facts.get("tdd") if isinstance(facts.get("tdd"), dict) else {}
    errors: list[str] = []
    errors.extend(_dict_mapping_errors("PDD.acceptance_criteria", _string_list(pdd.get("acceptance_criteria")), "TDD.acceptance_to_tests", tdd.get("acceptance_to_tests")))
    errors.extend(_dict_mapping_errors("DDD.invariants", _string_list(ddd.get("invariants")), "TDD.invariant_to_tests_or_code", tdd.get("invariant_to_tests_or_code")))
    errors.extend(_dict_mapping_errors("SDD.public_api", _string_list(sdd.get("public_api")), "TDD.public_api_to_tests", tdd.get("public_api_to_tests")))
    failure_modes = [*_string_list(sdd.get("error_contract")), *_string_list(sdd.get("failure_modes"))]
    if failure_modes and not _has_evidence(tdd.get("failure_mode_tests")):
        errors.append("SDD failure modes must map to TDD.failure_mode_tests")
    logging = sdd.get("logging_decision")
    if isinstance(logging, dict) and logging.get("needed") is True and not _has_evidence(tdd.get("logging_or_security_tests")):
        errors.append("SDD logging decision must map to logging/security tests or validation")
    return errors


def _dict_mapping_errors(source_name: str, source_items: list[str], mapping_name: str, mapping: Any) -> list[str]:
    if not source_items:
        return [f"{source_name} must not be empty"]
    if not isinstance(mapping, dict):
        return [f"{mapping_name} must be an object"]
    errors: list[str] = []
    for item in source_items:
        if not _has_evidence(mapping.get(item)):
            errors.append(f"{source_name} item {item!r} is not mapped in {mapping_name}")
    return errors


def _generic_trace_errors(facts: dict[str, Any]) -> list[str]:
    text = json.dumps(facts, sort_keys=True).casefold()
    if any(marker in text for marker in GENERIC_TRACE_MARKERS):
        return ["generic template-only process trace lacks case-specific mappings"]
    return []


def _sdd_no_choice_rationale(sdd: dict[str, Any]) -> str:
    for field in SDD_NO_CHOICE_RATIONALE_FIELDS:
        value = str(sdd.get(field, "")).strip()
        if value:
            return value
    return ""


def _sdd_scope_text(sdd: dict[str, Any]) -> str:
    scope = {
        key: value
        for key, value in sdd.items()
        if not str(key).startswith("_")
        and key not in {"design_decision_points", "assumption_policy", *SDD_NO_CHOICE_RATIONALE_FIELDS}
    }
    return json.dumps(scope, sort_keys=True).casefold()


def _decision_rationale(point: dict[str, Any]) -> str:
    for field in ("resolution_evidence", "why_user_choice_is_needed", "residual_risk", "trigger"):
        value = str(point.get(field, "")).strip()
        if value:
            return value
    return ""


def _resolved_evidence(point: dict[str, Any]) -> bool:
    evidence = str(point.get("resolution_evidence", "")).strip().casefold()
    return bool(evidence and evidence not in {"not resolved", "none", "n/a", "na"})


def _is_generic_sdd_rationale(rationale: str) -> bool:
    lowered = rationale.strip().casefold().strip(".")
    return not lowered or lowered in SDD_GENERIC_RATIONALES or len(lowered.split()) < 4


def _sdd_rationale_has_specific_evidence(rationale: str) -> bool:
    lowered = rationale.casefold()
    return any(marker in lowered for marker in SDD_SPECIFIC_RATIONALE_MARKERS)


def _safe_assumption_rationale_ok(text: str) -> bool:
    lowered = text.casefold()
    return all(any(marker in lowered for marker in group) for group in SDD_SAFE_ASSUMPTION_MARKER_GROUPS)


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    lowered = text.casefold()
    return [keyword for keyword in keywords if keyword in lowered]


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in markers)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _has_evidence(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_evidence(item) for item in value)
    if isinstance(value, dict):
        return any(_has_evidence(item) for item in value.values())
    return value is True


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


__all__ = [
    "validate_phase_artifact",
    "validate_phase_review_result",
    "validate_phase_transition",
    "validate_process_phase_ledger",
    "validate_process_trace_facts",
]
