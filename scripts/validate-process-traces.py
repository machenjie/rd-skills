#!/usr/bin/env python3
"""Validate Codex live benchmark PDD/DDD/SDD/TDD process traces."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import read_json


PHASES = ("pdd", "ddd", "sdd", "tdd", "implementation", "validation", "review")
CORE_PHASES = ("pdd", "ddd", "sdd", "tdd")
ALLOWED_PHASE_STATUSES = {"present", "missing", "degraded", "inferred", "not_applicable"}
FALLBACK_FIELD_SOURCE = "case_metadata_fallback"
FALLBACK_SOURCE_ALIASES = {FALLBACK_FIELD_SOURCE, "inferred"}
REQUIRED_PROCESS_FIELDS = {
    "pdd": ("problem", "acceptance_criteria", "constraints", "validation_signal"),
    "ddd": ("domain_terms", "invariants", "ownership_decision", "side_effect_boundaries"),
    "sdd": ("modules", "public_api", "error_contract", "failure_modes", "logging_decision"),
    "tdd": (
        "acceptance_to_tests",
        "invariant_to_tests_or_code",
        "public_api_to_tests",
        "failure_mode_tests",
        "validation_commands",
    ),
}
FORBIDDEN_TEXT = ("/Users/", "/home/", "C:\\Users\\", "auth.json", "CODEX_API_KEY", "OPENAI_API_KEY", "sk-")
GENERIC_TRACE_MARKERS = (
    "requested benchmark behavior is observable through public api",
    "requested benchmark behavior is observable through public api or documented setup/test contract",
    "expected behavior is observable through public api or documented setup/test contract",
    "candidate passes deterministic assertion-backed grading benchmark",
    "candidate passes deterministic assertion-backed grading for the selected case",
    "business rules remain in the owning domain",
    "side effects remain outside pure domain",
    "candidate public api",
    "starter repository public api",
    "validation command recorded",
    "validation command recorded for the candidate result",
)
GENERIC_DDD_MARKERS = (
    "keeps business rules in the owning domain",
    "keeps side effects outside pure domain",
    "business rules remain in the owning domain",
    "side effects remain outside pure domain",
)
GENERIC_PUBLIC_API_MARKERS = ("candidate public api", "starter repository public api")
LOGGING_VALIDATOR_PATH = Path(__file__).with_name("validate-logging-design.py")
_LOGGING_VALIDATOR: Any = None


def validate_process_traces(run_dir: Path, *, require_present: bool = False) -> list[str]:
    errors: list[str] = []
    result_paths = sorted(run_dir.glob("cases/*/*/run-*/result.json"))
    for result_path in result_paths:
        result = read_json(result_path)
        if not isinstance(result, dict):
            continue
        if result.get("artifact_status", result.get("status")) not in {"collected", "failed", "partial"}:
            continue
        trace_path = result_path.parent / "process-trace.json"
        if not trace_path.exists():
            errors.append(f"{_rel(run_dir, trace_path)} is missing")
            continue
        trace = read_json(trace_path)
        if not isinstance(trace, dict):
            errors.append(f"{_rel(run_dir, trace_path)} must be a JSON object")
            continue
        errors.extend(_trace_errors(trace_path, run_dir, trace, require_present=require_present))
    return errors


def _trace_errors(path: Path, run_dir: Path, trace: dict[str, Any], *, require_present: bool = False) -> list[str]:
    label = _rel(run_dir, path)
    errors = _forbidden_text_errors(label, path.read_text(encoding="utf-8", errors="ignore"))
    for field in ("schema_version", "run_id", "case_id", "variant", "run_index", "phase_status", "traceability", "process_facts"):
        if field not in trace:
            errors.append(f"{label}: missing {field}")

    phase_status = trace.get("phase_status")
    errors.extend(_phase_status_errors(label, phase_status, trace.get("evidence_sources"), require_present=require_present))

    facts = trace.get("process_facts")
    if not isinstance(facts, dict):
        errors.append(f"{label}: process_facts must be an object")
        facts = {}
    errors.extend(_phase_provenance_errors(label, phase_status, facts))

    pdd = facts.get("pdd")
    ddd = facts.get("ddd")
    sdd = facts.get("sdd")
    tdd = facts.get("tdd")
    errors.extend(_pdd_errors(label, pdd))
    errors.extend(_ddd_errors(label, ddd))
    errors.extend(_sdd_errors(label, sdd))
    errors.extend(_tdd_errors(label, tdd, trace))
    if isinstance(pdd, dict) and isinstance(ddd, dict) and isinstance(sdd, dict) and isinstance(tdd, dict):
        errors.extend(_mapping_errors(label, trace, pdd, ddd, sdd, tdd))
        errors.extend(_generic_trace_errors(label, trace))

    traceability = trace.get("traceability")
    if not isinstance(traceability, dict):
        errors.append(f"{label}: traceability must be an object")
    for artifact in trace.get("artifacts", []):
        if not isinstance(artifact, str) or artifact.startswith("/") or artifact.startswith(".."):
            errors.append(f"{label}: artifact paths must be relative")
    return errors


def _phase_status_errors(label: str, phase_status: Any, evidence_sources: Any, *, require_present: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(phase_status, dict):
        return [f"{label}: phase_status must be an object"]
    fallback_only = evidence_sources == ["case_metadata_fallback"]
    for phase in PHASES:
        status = phase_status.get(phase)
        if status not in ALLOWED_PHASE_STATUSES:
            errors.append(f"{label}: phase {phase} has invalid status {status!r}")
        if phase in CORE_PHASES and status == "missing":
            errors.append(f"{label}: phase {phase} is missing")
        if phase in CORE_PHASES and status == "present" and fallback_only:
            errors.append(f"{label}: phase {phase} cannot be present from case metadata fallback only")
        if phase in CORE_PHASES and require_present and status != "present":
            errors.append(f"{label}: --require-present requires phase {phase} to be present, got {status!r}")
        if status == "not_applicable" and not _not_applicable_reason_present(phase_status, phase):
            errors.append(f"{label}: phase {phase} not_applicable requires a reason")
    return errors


def _phase_provenance_errors(label: str, phase_status: Any, facts: dict[str, Any]) -> list[str]:
    if not isinstance(phase_status, dict):
        return []
    errors: list[str] = []
    for phase in CORE_PHASES:
        status = phase_status.get(phase)
        if status not in {"present", "degraded", "inferred"}:
            continue
        payload = facts.get(phase)
        if not isinstance(payload, dict):
            errors.append(f"{label}: phase {phase} status {status} requires process_facts.{phase}")
            continue
        field_sources = payload.get("_field_sources")
        if status in {"present", "degraded"} and not isinstance(field_sources, dict):
            errors.append(f"{label}: phase {phase} status {status} requires process_facts.{phase}._field_sources")
            continue
        sources = field_sources if isinstance(field_sources, dict) else {}
        raw_inferred_fields = payload.get("_inferred_fields")
        inferred_fields = {str(field) for field in raw_inferred_fields} if isinstance(raw_inferred_fields, list) else set()
        real_required: list[str] = []
        fallback_or_missing_required: list[str] = []
        for field in _required_process_fields(phase):
            has_value = _has_evidence(payload.get(field))
            source = str(sources.get(field) or "")
            source_is_fallback = field in inferred_fields or _source_is_fallback(source)
            if status == "present":
                if not has_value:
                    errors.append(f"{label}: phase {phase} is present but required field {field} is missing")
                elif not source:
                    errors.append(f"{label}: phase {phase} is present but required field {field} has no field source")
                elif source_is_fallback:
                    errors.append(
                        f"{label}: phase {phase} is present but required field {field} comes from fallback source {source!r}"
                    )
            if has_value and source and not source_is_fallback:
                real_required.append(field)
            else:
                fallback_or_missing_required.append(field)
        if status == "degraded":
            if not real_required:
                errors.append(f"{label}: phase {phase} is degraded but has no required field from real trace evidence")
            if not fallback_or_missing_required:
                errors.append(f"{label}: phase {phase} is degraded but no required field is fallback, inferred, or missing")
        if status == "inferred" and any(not _source_is_fallback(str(source)) for source in sources.values()):
            errors.append(f"{label}: phase {phase} is inferred but contains real field sources")
    return errors


def _required_process_fields(phase: str) -> tuple[str, ...]:
    return REQUIRED_PROCESS_FIELDS.get(phase, ())


def _source_is_fallback(source: str) -> bool:
    normalized = str(source).split(":", 1)[0]
    return normalized in FALLBACK_SOURCE_ALIASES


def _not_applicable_reason_present(phase_status: dict[str, Any], phase: str) -> bool:
    reasons = phase_status.get("not_applicable_reasons")
    return isinstance(reasons, dict) and bool(str(reasons.get(phase, "")).strip())


def _pdd_errors(label: str, pdd: Any) -> list[str]:
    if not isinstance(pdd, dict):
        return [f"{label}: PDD facts are missing"]
    errors = _non_empty_string_errors(label, pdd, ("problem",), "PDD")
    errors.extend(
        _non_empty_list_errors(
            label,
            pdd,
            (
                "user_or_system_impact",
                "acceptance_criteria",
                "constraints",
                "non_goals",
                "risk_surfaces",
                "validation_signal",
            ),
            "PDD",
        )
    )
    return errors


def _ddd_errors(label: str, ddd: Any) -> list[str]:
    if not isinstance(ddd, dict):
        return [f"{label}: DDD facts are missing"]
    errors = _non_empty_list_errors(label, ddd, ("domain_terms", "ownership_decision", "side_effect_boundaries"), "DDD")
    invariants = _string_list(ddd.get("invariants"))
    rationale = str(ddd.get("no_domain_state_rationale", "")).strip()
    if not invariants and not rationale:
        errors.append(f"{label}: DDD requires invariants or explicit no-domain-state rationale")
    return errors


def _sdd_errors(label: str, sdd: Any) -> list[str]:
    if not isinstance(sdd, dict):
        return [f"{label}: SDD facts are missing"]
    errors = _non_empty_list_errors(
        label,
        sdd,
        ("modules", "files_to_change", "public_api", "data_flow", "error_contract", "failure_modes"),
        "SDD",
    )
    logging_decision = sdd.get("logging_decision")
    if not isinstance(logging_decision, dict):
        errors.append(f"{label}: SDD.logging_decision must be an object")
    return errors


def _tdd_errors(label: str, tdd: Any, trace: dict[str, Any]) -> list[str]:
    if not isinstance(tdd, dict):
        return [f"{label}: TDD facts are missing"]
    errors = []
    for field in ("acceptance_to_tests", "invariant_to_tests_or_code", "public_api_to_tests"):
        if not isinstance(tdd.get(field), dict) or not tdd.get(field):
            errors.append(f"{label}: TDD.{field} must be a non-empty object")
    errors.extend(_non_empty_list_errors(label, tdd, ("failure_mode_tests", "validation_commands", "red_green_refactor_trace"), "TDD"))
    if not trace.get("validation_commands"):
        errors.append(f"{label}: top-level validation_commands are required")
    return errors


def _mapping_errors(
    label: str,
    trace: dict[str, Any],
    pdd: dict[str, Any],
    ddd: dict[str, Any],
    sdd: dict[str, Any],
    tdd: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _dict_mapping_errors(
            label,
            "PDD.acceptance_criteria",
            _string_list(pdd.get("acceptance_criteria")),
            "TDD.acceptance_to_tests",
            tdd.get("acceptance_to_tests"),
        )
    )
    errors.extend(
        _dict_mapping_errors(
            label,
            "DDD.invariants",
            _string_list(ddd.get("invariants")),
            "TDD.invariant_to_tests_or_code",
            tdd.get("invariant_to_tests_or_code"),
        )
    )
    errors.extend(
        _dict_mapping_errors(
            label,
            "SDD.public_api",
            _string_list(sdd.get("public_api")),
            "TDD.public_api_to_tests",
            tdd.get("public_api_to_tests"),
        )
    )
    errors.extend(_failure_mode_mapping_errors(label, sdd, tdd))
    errors.extend(_logging_mapping_errors(label, sdd.get("logging_decision"), tdd, trace.get("validation_commands")))
    return errors


def _dict_mapping_errors(
    label: str,
    source_name: str,
    source_items: list[str],
    mapping_name: str,
    mapping: Any,
) -> list[str]:
    errors: list[str] = []
    if not source_items:
        return [f"{label}: {source_name} must not be empty"]
    if not isinstance(mapping, dict):
        return [f"{label}: {mapping_name} must be an object"]
    for item in source_items:
        value = mapping.get(item)
        if not _has_evidence(value):
            errors.append(f"{label}: {source_name} item {item!r} is not mapped in {mapping_name}")
    return errors


def _failure_mode_mapping_errors(label: str, sdd: dict[str, Any], tdd: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    modes = [*(_string_list(sdd.get("error_contract"))), *(_string_list(sdd.get("failure_modes")))]
    tests = tdd.get("failure_mode_tests")
    if not modes:
        return [f"{label}: SDD.error_contract/failure_modes must not be empty"]
    if not isinstance(tests, list) or not tests:
        return [f"{label}: TDD.failure_mode_tests must map SDD failure modes"]
    mapped: set[str] = set()
    wildcard = False
    for entry in tests:
        if isinstance(entry, dict):
            if _has_evidence(entry.get("tests")):
                mapped.add(str(entry.get("failure_mode", "")))
                for source in entry.get("maps", []) if isinstance(entry.get("maps"), list) else []:
                    mapped.add(str(source))
        elif isinstance(entry, str) and entry.strip():
            wildcard = True
    if wildcard:
        return []
    for mode in modes:
        if mode not in mapped:
            errors.append(f"{label}: SDD failure/error item {mode!r} is not mapped in TDD.failure_mode_tests")
    return errors


def _logging_mapping_errors(label: str, logging_decision: Any, tdd: dict[str, Any], validation_commands: Any) -> list[str]:
    if not isinstance(logging_decision, dict):
        return [f"{label}: SDD.logging_decision must be an object"]
    validator_errors = _logging_design_errors(label, logging_decision, tdd, validation_commands)
    if logging_decision.get("needed") is False:
        if not str(logging_decision.get("rationale", "")).strip():
            return [f"{label}: SDD.logging_decision.needed=false requires rationale"]
        return validator_errors
    if logging_decision.get("needed") is not True:
        return [f"{label}: SDD.logging_decision.needed must be true or false"]
    errors: list[str] = list(validator_errors)
    for field in ("log_types", "events", "levels", "fields", "redaction", "cardinality_controls"):
        if not _string_list(logging_decision.get(field)):
            errors.append(f"{label}: SDD.logging_decision.{field} must be non-empty when logging is needed")
    logging_tests = _string_list(tdd.get("logging_or_security_tests"))
    validation_text = " ".join(_string_list(validation_commands)).casefold()
    if not logging_tests and not any(marker in validation_text for marker in ("log", "redact", "security", "audit")):
        errors.append(f"{label}: logging_decision.needed=true requires logging_or_security_tests or log/security validation command")
    return errors


def _logging_design_errors(
    label: str,
    logging_decision: dict[str, Any],
    tdd: dict[str, Any],
    validation_commands: Any,
) -> list[str]:
    validator = _load_logging_validator()
    context = {
        "tests_or_validation": [
            *_string_list(tdd.get("logging_or_security_tests")),
            *_string_list(validation_commands),
        ]
    }
    return [
        f"{label}: {error}"
        for error in validator.validate_logging_decision(
            logging_decision,
            context=context,
            label="SDD.logging_decision",
        )
    ]


def _load_logging_validator() -> Any:
    global _LOGGING_VALIDATOR
    if _LOGGING_VALIDATOR is not None:
        return _LOGGING_VALIDATOR
    spec = importlib.util.spec_from_file_location("validate_logging_design", LOGGING_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LOGGING_VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _LOGGING_VALIDATOR = module
    return module


def _generic_trace_errors(label: str, trace: dict[str, Any]) -> list[str]:
    text = json.dumps(trace.get("process_facts", {}), sort_keys=True).casefold()
    if not any(marker in text for marker in GENERIC_TRACE_MARKERS):
        return []
    if _case_specific_mapping_present(trace):
        return []
    return [f"{label}: generic template-only process trace lacks case-specific mappings"]


def _case_specific_mapping_present(trace: dict[str, Any]) -> bool:
    facts = trace.get("process_facts")
    if not isinstance(facts, dict):
        return False
    if not _concrete_case_facts_present(trace, facts):
        return False
    if facts.get("case_specific") is True:
        return True
    return _case_specific_mapping_shape_present(facts)


def _concrete_case_facts_present(trace: dict[str, Any], facts: dict[str, Any]) -> bool:
    case_tokens = _case_domain_tokens(str(trace.get("case_id", "")))
    pdd = facts.get("pdd") if isinstance(facts.get("pdd"), dict) else {}
    ddd = facts.get("ddd") if isinstance(facts.get("ddd"), dict) else {}
    sdd = facts.get("sdd") if isinstance(facts.get("sdd"), dict) else {}
    tdd = facts.get("tdd") if isinstance(facts.get("tdd"), dict) else {}
    acceptance = _string_list(pdd.get("acceptance_criteria"))
    invariants = _string_list(ddd.get("invariants"))
    public_api = _string_list(sdd.get("public_api"))
    failure_modes = [*(_string_list(sdd.get("error_contract"))), *(_string_list(sdd.get("failure_modes")))]
    facts_text = json.dumps(facts, sort_keys=True).casefold()
    has_domain_term = bool(case_tokens and any(token in facts_text for token in case_tokens))
    concrete_acceptance = any(_is_concrete_case_text(item, case_tokens) for item in acceptance)
    concrete_invariant = bool(invariants) and not all(_contains_any(item, GENERIC_DDD_MARKERS) for item in invariants)
    concrete_public_api = bool(public_api) and not all(_contains_any(item, GENERIC_PUBLIC_API_MARKERS) for item in public_api)
    concrete_failure = any(_is_concrete_failure_mode(item) for item in failure_modes)
    tdd_references_validation = _tdd_references_validation(tdd)
    return all((has_domain_term, concrete_acceptance, concrete_invariant, concrete_public_api, concrete_failure, tdd_references_validation))


def _case_specific_mapping_shape_present(facts: dict[str, Any]) -> bool:
    text = json.dumps(facts.get("tdd", {}), sort_keys=True).casefold()
    return "acceptance_to_tests" in text and "public_api_to_tests" in text and "failure_mode_tests" in text


def _case_domain_tokens(case_id: str) -> set[str]:
    ignored = {"case", "test", "with", "and", "the", "data", "api"}
    return {
        token
        for token in [part.casefold() for part in re.split(r"[^A-Za-z0-9]+", case_id)]
        if len(token) >= 3 and token not in ignored
    }


def _is_concrete_case_text(value: str, case_tokens: set[str]) -> bool:
    lowered = value.casefold()
    if _contains_any(lowered, GENERIC_TRACE_MARKERS):
        return False
    return not case_tokens or any(token in lowered for token in case_tokens) or len(lowered.split()) >= 4


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in markers)


def _is_concrete_failure_mode(value: str) -> bool:
    lowered = value.casefold()
    if _contains_any(lowered, ("setup_failed", "test_suite_failed", "security_checks_failed", "codex_exec_failed", "grading result categorizes")):
        return False
    return bool(lowered.strip())


def _tdd_references_validation(tdd: dict[str, Any]) -> bool:
    text = json.dumps(tdd, sort_keys=True).casefold()
    return any(marker in text for marker in ("python", "pytest", "unittest", "test", "assert", "run-codegen-benchmarks", ".py", "validation"))


def _non_empty_list_errors(label: str, payload: dict[str, Any], fields: tuple[str, ...], prefix: str) -> list[str]:
    errors: list[str] = []
    for field in fields:
        if not _string_list(payload.get(field)):
            errors.append(f"{label}: {prefix}.{field} must be a non-empty list")
    return errors


def _non_empty_string_errors(label: str, payload: dict[str, Any], fields: tuple[str, ...], prefix: str) -> list[str]:
    errors: list[str] = []
    for field in fields:
        if not isinstance(payload.get(field), str) or not payload.get(field).strip():
            errors.append(f"{label}: {prefix}.{field} must be a non-empty string")
    return errors


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


def _forbidden_text_errors(label: str, text: str) -> list[str]:
    return [f"{label}: contains forbidden marker {marker}" for marker in FORBIDDEN_TEXT if marker in text]


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--require-present", action="store_true")
    args = parser.parse_args(argv)
    errors = validate_process_traces(args.run_dir, require_present=args.require_present)
    if errors:
        for error in errors:
            print(f"validate-process-traces: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-process-traces: process traces are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
