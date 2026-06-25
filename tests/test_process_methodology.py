from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

PROCESS_SKILL = ROOT / "src" / "professional-skills" / "development-process-orchestrator" / "SKILL.md"
LOGGING_SKILL = ROOT / "src" / "professional-skills" / "logging-design-gate" / "SKILL.md"
COMMAND = "python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"
CORE_PHASES = ("pdd", "ddd", "sdd", "tdd")


def _load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _has_trace_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_trace_value(item) for item in value)
    if isinstance(value, dict):
        return any(not str(key).startswith("_") and _has_trace_value(item) for key, item in value.items())
    return value is True or value not in {None, False}


def _with_field_sources(trace: dict[str, Any], source: str = "final.md:compact-process-trace") -> dict[str, Any]:
    facts = trace.get("process_facts")
    if not isinstance(facts, dict):
        return trace
    for phase in CORE_PHASES:
        payload = facts.get(phase)
        if not isinstance(payload, dict):
            continue
        payload["_evidence_source"] = source
        payload["_field_sources"] = {
            field: source
            for field, value in payload.items()
            if not str(field).startswith("_") and _has_trace_value(value)
        }
        payload.setdefault("_inferred_fields", [])
    return trace


def test_process_skill_has_professional_pdd_ddd_sdd_tdd_methodology() -> None:
    text = _text(PROCESS_SKILL)
    for term in (
        "PDD - Problem / Product / Purpose Definition Discipline",
        '"problem": "one sentence"',
        "PDD pass criteria",
        "PDD anti-patterns",
        "DDD - Domain-Driven Design Discipline",
        '"domain_terms": []',
        "DDD rules",
        "DDD pass criteria",
        "SDD - System / Software / Structure Design Discipline",
        '"logging_decision"',
        "SDD logging decision rules",
        "SDD pass criteria",
        "TDD - Test-Driven Development Discipline",
        '"acceptance_to_tests": {}',
        "TDD pass criteria",
        "TDD anti-patterns",
    ):
        assert term in text


def test_stage_ownership_and_prompts_include_professional_process_method() -> None:
    ownership = {
        "change-intake-compiler": "PDD slice",
        "domain-impact-modeler": "DDD slice",
        "architecture-impact-reviewer": "SDD slice",
        "quality-test-gate": "TDD slice",
        "ai-code-review-refactor": "cross-stage review",
    }
    for skill, phrase in ownership.items():
        assert phrase in _text(ROOT / "src" / "professional-skills" / skill / "SKILL.md")
    wrapper = _text(ROOT / "evals" / "codex-live" / "prompts" / "task-wrapper.md")
    system = _text(ROOT / "evals" / "codex-live" / "prompts" / "changeforge-system.md")
    for phrase in (
        '"process_trace"',
        '"acceptance_criteria"',
        '"ownership_decision"',
        '"logging_decision"',
        '"validation_commands"',
        "placeholders such as",
        "strict traceability is required",
        "`log_types`, `placement`, `events`, `levels`",
        "`tdd.logging_or_security_tests`",
        "separate sink and retention rationale",
    ):
        assert phrase in wrapper
    for phrase in (
        "Problem / Product / Purpose Definition Discipline",
        "Domain-Driven Design Discipline",
        "System / Software / Structure Design Discipline",
        "Test-Driven Development Discipline",
    ):
        assert phrase in system


def test_process_and_logging_skills_match_strict_logging_trace_contract() -> None:
    process_text = _text(PROCESS_SKILL)
    logging_text = _text(LOGGING_SKILL)
    for phrase in (
        '"placement": []',
        '"events": []',
        '"correlation": []',
        '"tests_or_validation": []',
        "`log_types`, `placement`, `events`, `levels`, `fields`",
        "separate sink and",
    ):
        assert phrase in process_text
    for phrase in (
        "without log type, placement, event, level, fields, or redaction",
        "placement, events, level, fields, redaction",
        "separate audit from diagnostic logs",
    ):
        assert phrase in logging_text


def _valid_trace(*, logging_needed: bool = True) -> dict[str, Any]:
    acceptance = ["deny private, metadata, and loopback URLs"]
    invariants = ["unsafe URL is never fetched"]
    public_api = ["public URL validation/fetch entrypoint used by tests"]
    error_contract = ["deny unsafe URLs with a stable error category"]
    failure_modes = ["metadata URL denial"]
    logging_decision: dict[str, Any]
    logging_tests: list[str]
    if logging_needed:
        logging_decision = {
            "needed": True,
            "log_types": ["security"],
            "placement": ["security boundary"],
            "events": ["url_denied"],
            "levels": ["WARN"],
            "fields": ["operation", "error_category", "policy", "trace_id"],
            "redaction": ["raw URL query", "token"],
            "correlation": ["trace_id", "request_id"],
            "cardinality_controls": ["policy category instead of raw URL"],
            "rationale": "Security denial diagnostics must not leak query secrets.",
        }
        logging_tests = ["metadata denied and token redacted"]
    else:
        logging_decision = {
            "needed": False,
            "rationale": "Validation command and public behavior tests are sufficient; no product log is required.",
        }
        logging_tests = []
    return _with_field_sources({
        "schema_version": 1,
        "run_id": "unit-run",
        "case_id": "security/ssrf-url-allowlist",
        "variant": "skills_only_clean",
        "run_index": 1,
        "phase_status": {
            "pdd": "present",
            "ddd": "present",
            "sdd": "present",
            "tdd": "present",
            "implementation": "present",
            "validation": "present",
            "review": "missing",
        },
        "traceability": {
            "pdd_acceptance_to_tdd_tests": True,
            "ddd_invariants_to_tdd_tests": True,
            "sdd_public_api_to_tdd_tests": True,
            "sdd_failure_modes_to_tdd_tests": True,
            "sdd_logging_to_tdd_tests": True,
        },
        "process_facts": {
            "case_specific": True,
            "pdd": {
                "problem": "Prevent SSRF with URL allowlist and safe diagnostics.",
                "user_or_system_impact": ["protect metadata services"],
                "acceptance_criteria": acceptance,
                "constraints": ["preserve setup"],
                "non_goals": ["private corpus"],
                "risk_surfaces": ["security"],
                "validation_signal": [COMMAND],
            },
            "ddd": {
                "domain_terms": ["URL candidate", "network boundary"],
                "entities": ["URL validation decision"],
                "value_objects": ["normalized URL"],
                "domain_services": [],
                "application_services": [],
                "adapters": [],
                "invariants": invariants,
                "ownership_decision": ["URL safety policy belongs before network fetch"],
                "side_effect_boundaries": ["unsafe URL is not fetched"],
            },
            "sdd": {
                "modules": ["URL validation module"],
                "files_to_change": ["candidate files selected by inspection"],
                "public_api": public_api,
                "data_flow": ["raw URL -> validation -> optional fetch"],
                "error_contract": error_contract,
                "failure_modes": failure_modes,
                "logging_decision": logging_decision,
                "metrics_traces_alerts": ["grading-result.json"],
                "performance_or_concurrency_constraints": ["security"],
                "compatibility_and_migration": ["preserve harness"],
                "rollback_or_recovery": ["revert candidate change"],
            },
            "tdd": {
                "acceptance_to_tests": {acceptance[0]: [COMMAND]},
                "invariant_to_tests_or_code": {invariants[0]: [COMMAND]},
                "public_api_to_tests": {public_api[0]: [COMMAND]},
                "failure_mode_tests": [
                    {"failure_mode": error_contract[0], "tests": [COMMAND]},
                    {"failure_mode": failure_modes[0], "tests": [COMMAND]},
                ],
                "logging_or_security_tests": logging_tests,
                "validation_commands": [COMMAND],
                "red_green_refactor_trace": ["recorded"],
            },
        },
        "validation_commands": [COMMAND],
        "evidence_sources": ["final.md:compact-process-trace"],
        "artifacts": ["cases/security__ssrf-url-allowlist/skills_only_clean/run-01/result.json"],
    })


def _run_trace_errors(trace: dict[str, Any], *, require_present: bool = False) -> list[str]:
    validator = _load_script("validate_process_traces_unit", "scripts/validate-process-traces.py")
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        result_dir = run_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
        result_dir.mkdir(parents=True)
        result_dir.joinpath("result.json").write_text(
            json.dumps({"schema_version": 2, "artifact_status": "collected", "status": "collected"}),
            encoding="utf-8",
        )
        result_dir.joinpath("process-trace.json").write_text(json.dumps(trace), encoding="utf-8")
        return validator.validate_process_traces(run_dir, require_present=require_present)


def _trace_case(case_id: str = "security/ssrf-url-allowlist") -> SimpleNamespace:
    category, codegen_case = case_id.split("/", 1)
    return SimpleNamespace(
        id=case_id,
        category=category,
        codegen_case=codegen_case,
        grading_benchmark=case_id,
        tier="core",
        coverage_dimensions=(category,),
    )


def test_final_json_process_trace_populates_process_facts_and_present_status() -> None:
    runner = _load_script("run_codex_live_json_process_trace_unit", "scripts/run-codex-live-benchmarks.py")
    case = _trace_case()
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "run"
        run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
        run_dir.mkdir(parents=True)
        run_dir.joinpath("final.md").write_text(
            """Result

```json
{
  "process_trace": {
    "pdd": {
      "problem": "Block SSRF metadata URLs",
      "acceptance_criteria": ["deny metadata URL"],
      "constraints": ["preserve harness"],
      "validation_signal": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]
    },
    "ddd": {
      "domain_terms": ["URL candidate", "network boundary"],
      "invariants": ["unsafe URL is never fetched"],
      "ownership_decision": ["URL safety policy owns deny decision"],
      "side_effect_boundaries": ["no fetch before allowlist"]
    },
    "sdd": {
      "modules": ["URL validation module"],
      "public_api": ["URL validation public entrypoint"],
      "error_contract": ["deny unsafe URLs with stable error"],
      "failure_modes": ["metadata URL denial"],
      "logging_decision": {"needed": false, "rationale": "public tests cover denial"}
    },
    "tdd": {
      "acceptance_to_tests": {"deny metadata URL": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]},
      "invariant_to_tests_or_code": {"unsafe URL is never fetched": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]},
      "public_api_to_tests": {"URL validation public entrypoint": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]},
      "failure_mode_tests": ["metadata URL denial covered"],
      "validation_commands": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]
    }
  }
}
```
""",
            encoding="utf-8",
        )
        trace = runner._process_trace_payload(
            out_dir,
            run_dir,
            case=case,
            variant="skills_only_clean",
            run_index=1,
            result={"status": "collected", "grading_status": "passed"},
        )
    for phase in CORE_PHASES:
        assert trace["phase_status"][phase] == "present"
        for field in runner._required_process_fields(phase):
            assert trace["process_facts"][phase]["_field_sources"][field] == "final.md:process-trace-json"
            assert field not in trace["process_facts"][phase].get("_inferred_fields", [])
    assert _run_trace_errors(trace) == []


def test_final_multiline_process_trace_populates_process_facts() -> None:
    runner = _load_script("run_codex_live_compact_process_trace_unit", "scripts/run-codex-live-benchmarks.py")
    case = _trace_case()
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "run"
        run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
        run_dir.mkdir(parents=True)
        run_dir.joinpath("final.md").write_text(
            """Process Trace:
PDD:
  problem: Block SSRF metadata URLs
  acceptance: deny metadata URL
  constraints: preserve harness
  validation_signal: python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>
DDD:
  domain_terms: URL candidate and network boundary
  invariants: unsafe URL is never fetched
  ownership_decision: URL safety policy owns deny decision
  side_effect_boundaries: no fetch before allowlist
SDD:
  modules: URL validation module
  public_api: URL validation public entrypoint
  error_contract: deny unsafe URLs with stable error
  failure_modes: metadata URL denial
  logging_decision: public tests cover denial
TDD:
  acceptance_to_tests: deny metadata URL -> benchmark command
  invariant_to_tests_or_code: unsafe URL is never fetched -> benchmark command
  public_api_to_tests: URL validation public entrypoint -> benchmark command
  failure_mode_tests: metadata URL denial covered
  validation_commands: python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>
""",
            encoding="utf-8",
        )
        trace = runner._process_trace_payload(
            out_dir,
            run_dir,
            case=case,
            variant="skills_only_clean",
            run_index=1,
            result={"status": "collected", "grading_status": "passed"},
        )
    assert all(trace["phase_status"][phase] == "present" for phase in CORE_PHASES)
    assert trace["process_facts"]["pdd"]["problem"] == "Block SSRF metadata URLs"
    assert trace["process_facts"]["pdd"]["acceptance_criteria"] == ["deny metadata URL"]
    assert trace["process_facts"]["ddd"]["invariants"] == ["unsafe URL is never fetched"]
    assert trace["process_facts"]["sdd"]["public_api"] == ["URL validation public entrypoint"]
    assert trace["process_facts"]["sdd"]["logging_decision"] == {
        "needed": False,
        "rationale": "public tests cover denial",
    }
    assert trace["process_facts"]["tdd"]["acceptance_to_tests"] == {"deny metadata URL": ["benchmark command"]}
    assert trace["process_facts"]["tdd"]["validation_commands"] == [COMMAND]
    assert trace["traceability"]["sdd_failure_modes_to_tdd_tests"] is True
    assert all(trace["process_facts"][phase]["_field_sources"] for phase in CORE_PHASES)
    assert all(trace["phase_status"][phase] != "inferred" for phase in CORE_PHASES)
    assert _run_trace_errors(trace) == []


def test_present_status_requires_real_required_field_shapes() -> None:
    runner = _load_script("run_codex_live_invalid_shape_process_trace_unit", "scripts/run-codex-live-benchmarks.py")
    case = _trace_case()
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "run"
        run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
        run_dir.mkdir(parents=True)
        run_dir.joinpath("final.md").write_text(
            """Result

```json
{
  "process_trace": {
    "pdd": {
      "problem": "Block SSRF metadata URLs",
      "acceptance_criteria": "deny metadata URL",
      "constraints": ["preserve harness"],
      "validation_signal": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]
    },
    "ddd": {
      "domain_terms": ["URL candidate", "network boundary"],
      "invariants": ["unsafe URL is never fetched"],
      "ownership_decision": ["URL safety policy owns deny decision"],
      "side_effect_boundaries": ["no fetch before allowlist"]
    },
    "sdd": {
      "modules": ["URL validation module"],
      "public_api": ["URL validation public entrypoint"],
      "error_contract": ["deny unsafe URLs with stable error"],
      "failure_modes": ["metadata URL denial"],
      "logging_decision": {"needed": false, "rationale": "public tests cover denial"}
    },
    "tdd": {
      "acceptance_to_tests": {"deny metadata URL": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]},
      "invariant_to_tests_or_code": {"unsafe URL is never fetched": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]},
      "public_api_to_tests": {"URL validation public entrypoint": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]},
      "failure_mode_tests": ["metadata URL denial covered"],
      "validation_commands": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]
    }
  }
}
```
""",
            encoding="utf-8",
        )
        trace = runner._process_trace_payload(
            out_dir,
            run_dir,
            case=case,
            variant="skills_only_clean",
            run_index=1,
            result={"status": "collected", "grading_status": "passed"},
        )
    assert trace["process_facts"]["pdd"]["_field_sources"]["acceptance_criteria"] == "final.md:process-trace-json"
    assert trace["phase_status"]["pdd"] == "degraded"
    assert trace["phase_status"]["ddd"] == "present"
    assert trace["phase_status"]["sdd"] == "present"
    assert trace["phase_status"]["tdd"] == "present"


def test_partial_final_trace_with_fallback_required_fields_becomes_degraded() -> None:
    runner = _load_script("run_codex_live_partial_process_trace_unit", "scripts/run-codex-live-benchmarks.py")
    case = _trace_case()
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "run"
        run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
        run_dir.mkdir(parents=True)
        run_dir.joinpath("final.md").write_text(
            """Process Trace:
PDD:
  problem: Block SSRF metadata URLs
DDD:
  invariants: unsafe URL is never fetched
SDD:
  public_api: URL validation public entrypoint
TDD:
  validation_commands: python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>
""",
            encoding="utf-8",
        )
        trace = runner._process_trace_payload(
            out_dir,
            run_dir,
            case=case,
            variant="skills_only_clean",
            run_index=1,
            result={"status": "collected", "grading_status": "passed"},
        )
    assert all(trace["phase_status"][phase] == "degraded" for phase in CORE_PHASES)
    assert trace["process_facts"]["pdd"]["_field_sources"]["problem"] == "final.md:compact-process-trace"
    assert trace["process_facts"]["ddd"]["_field_sources"]["invariants"] == "final.md:compact-process-trace"
    assert trace["process_facts"]["sdd"]["_field_sources"]["public_api"] == "final.md:compact-process-trace"
    assert trace["process_facts"]["tdd"]["_field_sources"]["validation_commands"] == "final.md:compact-process-trace"
    assert "constraints" in trace["process_facts"]["pdd"]["_inferred_fields"]
    assert "ownership_decision" in trace["process_facts"]["ddd"]["_inferred_fields"]
    assert "error_contract" in trace["process_facts"]["sdd"]["_inferred_fields"]
    assert "acceptance_to_tests" in trace["process_facts"]["tdd"]["_inferred_fields"]
    assert "case_metadata_fallback:missing-fields" in trace["evidence_sources"]
    errors = _run_trace_errors(trace, require_present=True)
    assert any("--require-present requires phase pdd to be present" in error for error in errors)


def test_candidate_process_trace_artifact_overrides_partial_final_trace() -> None:
    runner = _load_script("run_codex_live_candidate_artifact_trace_unit", "scripts/run-codex-live-benchmarks.py")
    case = _trace_case()
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "run"
        run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
        run_dir.mkdir(parents=True)
        run_dir.joinpath("final.md").write_text(
            """Process Trace:
PDD:
  problem: Block SSRF metadata URLs
""",
            encoding="utf-8",
        )
        artifact_dir = run_dir / "candidate-artifacts"
        artifact_dir.mkdir()
        artifact_dir.joinpath("process-trace.json").write_text(
            json.dumps({"process_trace": _valid_trace()["process_facts"]}),
            encoding="utf-8",
        )
        trace = runner._process_trace_payload(
            out_dir,
            run_dir,
            case=case,
            variant="skills_only_clean",
            run_index=1,
            result={"status": "collected", "grading_status": "passed"},
        )
    assert all(trace["phase_status"][phase] == "present" for phase in CORE_PHASES)
    assert "candidate-artifacts/process-trace.json:process-trace-json" in trace["evidence_sources"]
    assert "case_metadata_fallback:missing-fields" not in trace["evidence_sources"]
    assert (
        trace["process_facts"]["pdd"]["_field_sources"]["acceptance_criteria"]
        == "candidate-artifacts/process-trace.json:process-trace-json"
    )


def test_no_final_or_hook_trace_becomes_inferred() -> None:
    runner = _load_script("run_codex_live_fallback_only_process_trace_unit", "scripts/run-codex-live-benchmarks.py")
    summary_module = _load_script("generate_codex_live_summary_fallback_only_unit", "scripts/generate-codex-live-summary.py")
    case = _trace_case("experimental/no-final-trace")
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "run"
        run_dir = out_dir / "cases" / "experimental__no-final-trace" / "skills_only_clean" / "run-01"
        run_dir.mkdir(parents=True)
        trace = runner._process_trace_payload(
            out_dir,
            run_dir,
            case=case,
            variant="skills_only_clean",
            run_index=1,
            result={"status": "collected", "grading_status": "passed"},
        )
        run_dir.joinpath("process-trace.json").write_text(json.dumps(trace), encoding="utf-8")
        summary = summary_module._process_compliance_summary([{"_result_dir": run_dir}])
    assert all(trace["phase_status"][phase] == "inferred" for phase in CORE_PHASES)
    assert trace["evidence_sources"] == ["case_metadata_fallback"]
    assert trace["process_facts"]["pdd"]["_evidence_source"] == "case_metadata_fallback"
    assert summary["pdd_present_rate"] == 0.0
    assert summary["pdd_inferred_rate"] == 1.0
    assert summary["all_core_phases_inferred_only_rate"] == 1.0
    assert summary["all_core_phases_present_rate"] == 0.0
    assert summary["pdd_required_field_fallback_rate"] == 1.0


def test_present_status_with_inferred_required_field_fails_validator() -> None:
    trace = _valid_trace()
    trace["process_facts"]["pdd"]["_field_sources"]["constraints"] = "case_metadata_fallback"
    trace["process_facts"]["pdd"]["_inferred_fields"].append("constraints")
    errors = _run_trace_errors(trace)
    assert any("phase pdd is present but required field constraints comes from fallback source" in error for error in errors)


def test_present_status_with_invalid_required_field_shape_fails_validator() -> None:
    trace = _valid_trace()
    # Regression: forged present status must not hide a scalar required field with a real source.
    trace["process_facts"]["pdd"]["acceptance_criteria"] = "scalar but source=final.md"
    trace["process_facts"]["tdd"]["acceptance_to_tests"] = {
        "scalar but source=final.md": [COMMAND],
    }
    errors = _run_trace_errors(trace)
    assert any(
        "phase pdd is present but required field acceptance_criteria has invalid shape" in error
        for error in errors
    )


def test_generic_synthetic_trace_fails() -> None:
    trace = _valid_trace()
    trace["process_facts"].pop("case_specific")
    trace["case_id"] = "security/another-case"
    trace["process_facts"]["pdd"]["acceptance_criteria"] = [
        "requested benchmark behavior is observable through public API or documented setup/test contract"
    ]
    trace["process_facts"]["tdd"]["acceptance_to_tests"] = {
        trace["process_facts"]["pdd"]["acceptance_criteria"][0]: [COMMAND]
    }
    errors = _run_trace_errors(trace)
    assert any("generic template-only process trace" in error for error in errors)


def test_case_specific_flag_does_not_rescue_generic_trace() -> None:
    trace = _valid_trace()
    trace["process_facts"]["case_specific"] = True
    trace["process_facts"]["pdd"]["acceptance_criteria"] = [
        "requested benchmark behavior is observable through public API or documented setup/test contract"
    ]
    trace["process_facts"]["ddd"]["invariants"] = ["business rules remain in the owning domain"]
    trace["process_facts"]["sdd"]["public_api"] = ["candidate public API"]
    trace["process_facts"]["sdd"]["failure_modes"] = ["setup_failed"]
    trace["process_facts"]["tdd"]["acceptance_to_tests"] = {
        trace["process_facts"]["pdd"]["acceptance_criteria"][0]: [COMMAND]
    }
    trace["process_facts"]["tdd"]["invariant_to_tests_or_code"] = {
        "business rules remain in the owning domain": [COMMAND]
    }
    trace["process_facts"]["tdd"]["public_api_to_tests"] = {"candidate public API": [COMMAND]}
    trace["process_facts"]["tdd"]["failure_mode_tests"] = [{"failure_mode": "setup_failed", "tests": [COMMAND]}]
    errors = _run_trace_errors(trace)
    assert any("generic template-only process trace" in error for error in errors)


def test_require_present_rejects_inferred_core_phases() -> None:
    trace = _valid_trace()
    trace["phase_status"]["pdd"] = "inferred"
    errors = _run_trace_errors(trace, require_present=True)
    assert any("--require-present requires phase pdd to be present" in error for error in errors)


def test_pdd_without_tdd_mapping_fails() -> None:
    trace = _valid_trace()
    trace["process_facts"]["tdd"]["acceptance_to_tests"] = {}
    errors = _run_trace_errors(trace)
    assert any("PDD.acceptance_criteria" in error for error in errors)


def test_ddd_invariant_without_test_or_code_mapping_fails() -> None:
    trace = _valid_trace()
    trace["process_facts"]["tdd"]["invariant_to_tests_or_code"] = {}
    errors = _run_trace_errors(trace)
    assert any("DDD.invariants" in error for error in errors)


def test_sdd_logging_needed_without_redaction_or_tests_fails() -> None:
    trace = _valid_trace()
    trace["process_facts"]["sdd"]["logging_decision"]["redaction"] = []
    trace["process_facts"]["tdd"]["logging_or_security_tests"] = []
    trace["validation_commands"] = ["python3 tests/run.py"]
    trace["process_facts"]["tdd"]["validation_commands"] = ["python3 tests/run.py"]
    errors = _run_trace_errors(trace)
    assert any("logging_decision.redaction" in error for error in errors)
    assert any("logging_or_security_tests" in error for error in errors)


def test_process_trace_context_can_back_audit_diagnostic_separation() -> None:
    trace = _valid_trace()
    separation = "Audit logs and diagnostic logs have separate sinks and separate retention rationale."
    trace["process_facts"]["ddd"]["invariants"].append(separation)
    trace["process_facts"]["tdd"]["invariant_to_tests_or_code"][separation] = [
        "python3 tests/test_logging.py::test_audit_diagnostic_separation"
    ]
    trace["process_facts"]["sdd"]["logging_decision"] = {
        "needed": True,
        "log_types": ["audit", "diagnostic"],
        "placement": ["audit sink boundary", "diagnostic failure boundary"],
        "events": ["security_audit_decision", "terminal_diagnostic_failure"],
        "levels": ["INFO", "ERROR"],
        "fields": ["operation", "result", "error_category", "trace_id"],
        "redaction": ["raw request body", "token"],
        "correlation": ["trace_id"],
        "cardinality_controls": ["route_template"],
        "tests_or_validation": ["python3 tests/test_logging.py::test_audit_diagnostic_separation"],
        "rationale": "Audit and diagnostic events are both required for this case.",
    }
    trace["process_facts"]["tdd"]["logging_or_security_tests"] = [
        "python3 tests/test_logging.py::test_audit_diagnostic_separation"
    ]
    assert _run_trace_errors(trace) == []


def test_forbidden_text_scan_allows_safety_terms_but_rejects_real_leaks() -> None:
    trace = _valid_trace()
    trace["process_facts"]["ddd"]["ownership_decision"].append(
        "compaction_workflow.py owns task-state counting and tests reject /Users/ and /home/ path fragments"
    )
    assert _run_trace_errors(trace) == []

    trace["process_facts"]["ddd"]["ownership_decision"].append("/Users/example/private/auth.json")
    trace["process_facts"]["sdd"]["failure_modes"].append("secret token sk-Abcdef12345 leaked")
    trace["process_facts"]["tdd"]["failure_mode_tests"].append(
        "secret token sk-Abcdef12345 leaked -> python3 tests/test_privacy.py"
    )
    errors = _run_trace_errors(trace)
    assert any("forbidden pattern" in error for error in errors)


def test_no_log_rationale_allows_logging_decision_false() -> None:
    trace = _valid_trace(logging_needed=False)
    assert _run_trace_errors(trace) == []


def test_security_case_specific_trace_passes() -> None:
    assert _run_trace_errors(_valid_trace()) == []


def test_reliability_case_specific_trace_passes() -> None:
    trace = _valid_trace()
    trace["case_id"] = "reliability/redis-cache-stampede-protection"
    trace["process_facts"]["pdd"]["problem"] = "Prevent Redis cache stampede."
    trace["process_facts"]["pdd"]["acceptance_criteria"] = ["concurrent same-key miss causes one backend refresh"]
    trace["process_facts"]["ddd"]["domain_terms"] = ["cache key", "in-flight refresh", "source-of-truth"]
    trace["process_facts"]["ddd"]["invariants"] = ["same key shares an in-flight refresh"]
    trace["process_facts"]["sdd"]["public_api"] = ["cache get/load public API used by tests"]
    trace["process_facts"]["sdd"]["error_contract"] = ["refresh failure is retryable or fallback-classified"]
    trace["process_facts"]["sdd"]["failure_modes"] = ["cache miss storm", "refresh failure fallback"]
    trace["process_facts"]["sdd"]["logging_decision"] = {
        "needed": True,
        "log_types": ["diagnostic", "integration/dependency"],
        "placement": ["cache service", "backend dependency seam"],
        "events": ["cache_miss_storm", "refresh_fallback", "lock_contention"],
        "levels": ["WARN"],
        "fields": [
            "operation",
            "dependency",
            "status",
            "error_category",
            "entity_id_hash",
            "attempt",
            "retryable",
            "duration_ms",
        ],
        "redaction": ["raw cache key when it contains user input", "PII"],
        "correlation": ["trace_id", "request_id"],
        "cardinality_controls": ["hash cache key", "prefer metrics for high-frequency misses"],
        "rationale": "Stampede/fallback diagnostics need safe cache context.",
    }
    trace["process_facts"]["tdd"]["acceptance_to_tests"] = {
        "concurrent same-key miss causes one backend refresh": [COMMAND]
    }
    trace["process_facts"]["tdd"]["invariant_to_tests_or_code"] = {
        "same key shares an in-flight refresh": [COMMAND]
    }
    trace["process_facts"]["tdd"]["public_api_to_tests"] = {"cache get/load public API used by tests": [COMMAND]}
    trace["process_facts"]["tdd"]["failure_mode_tests"] = [
        {"failure_mode": "refresh failure is retryable or fallback-classified", "tests": [COMMAND]},
        {"failure_mode": "cache miss storm", "tests": [COMMAND]},
        {"failure_mode": "refresh failure fallback", "tests": [COMMAND]},
    ]
    trace["process_facts"]["tdd"]["logging_or_security_tests"] = ["backend.calls == 1", "fallback observable"]
    assert _run_trace_errors(trace) == []


class ProcessMethodologyTests(unittest.TestCase):
    def test_process_skill_has_professional_pdd_ddd_sdd_tdd_methodology(self) -> None:
        test_process_skill_has_professional_pdd_ddd_sdd_tdd_methodology()

    def test_stage_ownership_and_prompts_include_professional_process_method(self) -> None:
        test_stage_ownership_and_prompts_include_professional_process_method()

    def test_final_json_process_trace_populates_process_facts_and_present_status(self) -> None:
        test_final_json_process_trace_populates_process_facts_and_present_status()

    def test_final_multiline_process_trace_populates_process_facts(self) -> None:
        test_final_multiline_process_trace_populates_process_facts()

    def test_present_status_requires_real_required_field_shapes(self) -> None:
        test_present_status_requires_real_required_field_shapes()

    def test_partial_final_trace_with_fallback_required_fields_becomes_degraded(self) -> None:
        test_partial_final_trace_with_fallback_required_fields_becomes_degraded()

    def test_candidate_process_trace_artifact_overrides_partial_final_trace(self) -> None:
        test_candidate_process_trace_artifact_overrides_partial_final_trace()

    def test_no_final_or_hook_trace_becomes_inferred(self) -> None:
        test_no_final_or_hook_trace_becomes_inferred()

    def test_present_status_with_invalid_required_field_shape_fails_validator(self) -> None:
        test_present_status_with_invalid_required_field_shape_fails_validator()

    def test_generic_synthetic_trace_fails(self) -> None:
        test_generic_synthetic_trace_fails()

    def test_case_specific_flag_does_not_rescue_generic_trace(self) -> None:
        test_case_specific_flag_does_not_rescue_generic_trace()

    def test_require_present_rejects_inferred_core_phases(self) -> None:
        test_require_present_rejects_inferred_core_phases()

    def test_pdd_without_tdd_mapping_fails(self) -> None:
        test_pdd_without_tdd_mapping_fails()

    def test_ddd_invariant_without_test_or_code_mapping_fails(self) -> None:
        test_ddd_invariant_without_test_or_code_mapping_fails()

    def test_sdd_logging_needed_without_redaction_or_tests_fails(self) -> None:
        test_sdd_logging_needed_without_redaction_or_tests_fails()

    def test_no_log_rationale_allows_logging_decision_false(self) -> None:
        test_no_log_rationale_allows_logging_decision_false()

    def test_security_case_specific_trace_passes(self) -> None:
        test_security_case_specific_trace_passes()

    def test_reliability_case_specific_trace_passes(self) -> None:
        test_reliability_case_specific_trace_passes()


if __name__ == "__main__":
    unittest.main()
