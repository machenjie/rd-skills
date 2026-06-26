#!/usr/bin/env python3
"""Evaluate deterministic Context Control Plane fixtures."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from validation_utils import fail_many, load_yaml_file, parse_frontmatter


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "evals" / "context-control"
REPORT_JSON = ROOT / "reports" / "context-control-plane-eval.json"
REPORT_MD = ROOT / "reports" / "context-control-plane-eval.md"
CAPABILITY_NAME = "context-control-plane"
CAPABILITY_ID = "128"
LIVE_SUMMARY = ROOT / "reports" / "codex-live-benchmark-summary.json"

REQUIRED_FIXTURES = (
    "routing-budget-minimal.yaml",
    "routing-budget-broad-audit.yaml",
    "reference-signal-density.yaml",
    "jit-context-pack-runtime-budget.yaml",
    "tool-output-boundary-large-output.yaml",
    "compaction-snapshot-v2.yaml",
    "branch-route-repair-summary.yaml",
    "negative-small-typo-no-context-control.yaml",
)
VALID_STATUSES = {"pass", "partial", "fail", "not_collected"}
VALID_BUDGET_MODES = {"minimal", "single-stage", "staged-plan", "full"}
MODE_REFERENCE_LIMITS = {
    "minimal": 8,
    "single-stage": 12,
    "staged-plan": 16,
    "full": 24,
}
FORBIDDEN_RAW_FIELDS = {
    "raw_prompt",
    "prompt",
    "stdout",
    "stderr",
    "command_output",
    "raw_output",
    "full_output",
    "full_diff",
    "file_contents",
    "environment",
    "env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "password",
    "api_key",
    "apikey",
    "token",
}
SECRET_VALUE_RE = re.compile(
    r"(sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+|"
    r"(?i:(api[_-]?key|access[_-]?token|bearer[_-]?token|password|secret)"
    r"\s*[:=]\s*[A-Za-z0-9_./+=-]{8,})|"
    r"(?i:bearer\s+[A-Za-z0-9._/-]{12,}))"
)
ABSOLUTE_PATH_RE = re.compile(r"^(/Users/|/home/|/private/var/|/var/folders/|/tmp/|[A-Za-z]:[\\/])")


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_runtime_policy():
    path = ROOT / "src" / "hook-runtime" / "scripts" / "changeforge_context_control_policy.py"
    spec = importlib.util.spec_from_file_location("changeforge_context_control_policy", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _capability_registry_errors(root: Path) -> list[str]:
    errors: list[str] = []
    skill_path = root / "src" / "foundation" / "capabilities" / CAPABILITY_NAME / "SKILL.md"
    if not skill_path.exists():
        return [f"{skill_path.relative_to(root)} missing"]
    frontmatter, _, _ = parse_frontmatter(skill_path)
    if frontmatter.get("name") != CAPABILITY_NAME:
        errors.append("context-control-plane SKILL.md frontmatter name mismatch")
    if str(frontmatter.get("changeforge_capability_id")) != CAPABILITY_ID:
        errors.append("context-control-plane SKILL.md capability id mismatch")

    registry = load_yaml_file(root / "src" / "registry" / "capabilities.yaml")
    capabilities = registry.get("capabilities") if isinstance(registry, dict) else None
    match = None
    if isinstance(capabilities, list):
        for item in capabilities:
            if isinstance(item, dict) and item.get("name") == CAPABILITY_NAME:
                match = item
                break
    if not isinstance(match, dict):
        errors.append("context-control-plane missing from src/registry/capabilities.yaml")
    else:
        if str(match.get("id")) != CAPABILITY_ID:
            errors.append("context-control-plane registry id mismatch")
        if match.get("path") != "src/foundation/capabilities/context-control-plane":
            errors.append("context-control-plane registry path mismatch")
    return errors


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _fixture_schema_errors(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    expected = _mapping(data.get("expected"))
    input_payload = _mapping(data.get("input"))
    budget = _mapping(data.get("context_budget"))
    for field in ("id",):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{rel}: {field} is required")
    if not isinstance(input_payload.get("scenario"), str) or not input_payload["scenario"].strip():
        errors.append(f"{rel}: input.scenario is required")
    if not isinstance(input_payload.get("context_risk"), bool):
        errors.append(f"{rel}: input.context_risk must be boolean")
    for field in ("selected_skills", "selected_capabilities", "forbidden_raw_fields", "skipped_references"):
        if not isinstance(expected.get(field), list):
            errors.append(f"{rel}: expected.{field} must be a list")
    if expected.get("context_control_selected") is None or not isinstance(expected.get("context_control_selected"), bool):
        errors.append(f"{rel}: expected.context_control_selected must be boolean")
    if expected.get("context_control_selected") != input_payload.get("context_risk"):
        errors.append(f"{rel}: context-control selection must match context_risk signal")
    if expected.get("budget_mode") not in VALID_BUDGET_MODES:
        errors.append(f"{rel}: expected.budget_mode must be one of {sorted(VALID_BUDGET_MODES)}")
    for field in ("selected_reference_count", "selected_reference_count_max", "skipped_reference_count"):
        if not isinstance(expected.get(field), int) or expected.get(field) < 0:
            errors.append(f"{rel}: expected.{field} must be a non-negative integer")
    for field in ("safety_result", "closure_result"):
        if expected.get(field) not in VALID_STATUSES:
            errors.append(f"{rel}: expected.{field} must be one of {sorted(VALID_STATUSES)}")
    if not budget:
        errors.append(f"{rel}: context_budget is required")
    return errors


def _context_budget_errors(path: Path, data: dict[str, Any]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    expected = _mapping(data.get("expected"))
    budget = _mapping(data.get("context_budget"))
    errors: list[str] = []
    required = (
        "budget_mode",
        "budget_profile",
        "budget_rationale",
        "context_budget_tokens",
        "selected_capability_count",
        "selected_reference_count",
        "skipped_reference_count",
        "over_budget",
        "residual_context_risk",
    )
    for field in required:
        if field not in budget:
            errors.append(f"{rel}: context_budget.{field} is required")
    if budget.get("budget_mode") != expected.get("budget_mode"):
        errors.append(f"{rel}: context_budget.budget_mode must match expected.budget_mode")
    if budget.get("selected_reference_count") != expected.get("selected_reference_count"):
        errors.append(f"{rel}: selected_reference_count mismatch")
    if budget.get("skipped_reference_count") != expected.get("skipped_reference_count"):
        errors.append(f"{rel}: skipped_reference_count mismatch")
    if not isinstance(budget.get("context_budget_tokens"), int) or budget.get("context_budget_tokens") < 0:
        errors.append(f"{rel}: context_budget.context_budget_tokens must be a non-negative integer")
    if not isinstance(budget.get("over_budget"), bool):
        errors.append(f"{rel}: context_budget.over_budget must be boolean")
    mode = expected.get("budget_mode")
    limit = MODE_REFERENCE_LIMITS.get(str(mode), 0)
    selected_count = expected.get("selected_reference_count")
    max_count = expected.get("selected_reference_count_max")
    if isinstance(selected_count, int) and isinstance(max_count, int) and selected_count > max_count:
        errors.append(f"{rel}: selected references exceed fixture max")
    if isinstance(selected_count, int) and selected_count > limit:
        errors.append(f"{rel}: selected references exceed {mode} mode limit {limit}")
    for index, item in enumerate(expected.get("skipped_references") or []):
        if not isinstance(item, dict):
            errors.append(f"{rel}: expected.skipped_references[{index}] must be an object")
            continue
        for field in ("reference", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{rel}: expected.skipped_references[{index}].{field} is required")
    return errors


def _routing_fixture_errors(path: Path, data: dict[str, Any]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    input_payload = _mapping(data.get("input"))
    expected = _mapping(data.get("expected"))
    errors: list[str] = []

    fixture_path = input_payload.get("routing_fixture_path")
    if isinstance(fixture_path, str) and fixture_path.strip():
        route_fixture = load_yaml_file(ROOT / fixture_path)
        route_expected = _mapping(_mapping(route_fixture).get("expected"))
        route_forbidden = _mapping(_mapping(route_fixture).get("forbidden"))
        expected_selected = bool(expected.get("context_control_selected"))
        route_caps = set(_string_list(route_expected.get("capabilities")))
        forbidden_caps = set(_string_list(route_forbidden.get("capabilities")))
        if expected_selected and CAPABILITY_NAME not in route_caps:
            errors.append(f"{rel}: routing fixture does not select context-control-plane")
        if not expected_selected and CAPABILITY_NAME in route_caps:
            errors.append(f"{rel}: negative routing fixture unexpectedly selects context-control-plane")
        if not expected_selected and CAPABILITY_NAME not in forbidden_caps:
            errors.append(f"{rel}: negative routing fixture must forbid context-control-plane")

    actual_path = input_payload.get("routing_actual_path")
    if isinstance(actual_path, str) and actual_path.strip():
        actual_payload = load_yaml_file(ROOT / actual_path)
        actual = _mapping(_mapping(actual_payload).get("actual"))
        expected_selected = bool(expected.get("context_control_selected"))
        actual_caps = set(_string_list(actual.get("capabilities")))
        if expected_selected != (CAPABILITY_NAME in actual_caps):
            errors.append(f"{rel}: actual route context-control selection mismatch")
        missing_skills = sorted(set(_string_list(expected.get("selected_skills"))) - set(_string_list(actual.get("skills"))))
        if missing_skills:
            errors.append(f"{rel}: actual route missing expected skills {missing_skills}")
        missing_caps = sorted(set(_string_list(expected.get("selected_capabilities"))) - actual_caps)
        if missing_caps:
            errors.append(f"{rel}: actual route missing expected capabilities {missing_caps}")
        context_control = _mapping(actual.get("context_control"))
        if expected_selected and not context_control:
            errors.append(f"{rel}: actual.context_control is required")
        elif context_control:
            if context_control.get("budget_mode") != expected.get("budget_mode"):
                errors.append(f"{rel}: actual.context_control budget_mode mismatch")
            for field in ("selected_reference_count", "skipped_reference_count"):
                if context_control.get(field) != expected.get(field):
                    errors.append(f"{rel}: actual.context_control {field} mismatch")
            for index, item in enumerate(context_control.get("skipped_references") or []):
                if not isinstance(item, dict) or not item.get("reference") or not item.get("reason"):
                    errors.append(f"{rel}: actual.context_control skipped_references[{index}] needs reference and reason")
            max_refs = context_control.get("max_required_references", expected.get("selected_reference_count_max"))
            if isinstance(max_refs, int) and isinstance(context_control.get("selected_reference_count"), int):
                if context_control["selected_reference_count"] > max_refs:
                    errors.append(f"{rel}: actual.context_control exceeds max_required_references")
    return errors


def _runtime_resolver_errors(path: Path, data: dict[str, Any], runtime_policy: Any) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    resolver = _mapping(_mapping(data.get("input")).get("runtime_resolver"))
    if not resolver:
        return []
    mode = runtime_policy.context_budget_mode(
        str(resolver.get("stage") or ""),
        _string_list(resolver.get("risk_surfaces")),
        _string_list(resolver.get("product_surfaces")),
        _mapping(resolver.get("classification")),
    )
    expected_mode = _mapping(data.get("expected")).get("budget_mode")
    if mode != expected_mode:
        return [f"{rel}: runtime resolver budget mode {mode!r} does not match {expected_mode!r}"]
    return []


def _jit_context_pack_errors(path: Path, data: dict[str, Any], schema_required: list[str]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    payload = _mapping(data.get("jit_context_pack"))
    if not payload:
        return []
    errors: list[str] = []
    if payload.get("required") is not True:
        errors.append(f"{rel}: jit_context_pack.required must be true when present")
    record = _mapping(payload.get("record"))
    pack = _mapping(record.get("task_context_pack"))
    if not pack:
        return [*errors, f"{rel}: jit_context_pack.record.task_context_pack is required"]
    missing = [field for field in schema_required if field not in pack]
    if missing:
        errors.append(f"{rel}: TaskContextPack v3 missing required fields {missing}")
    if pack.get("schema_version") != 3:
        errors.append(f"{rel}: TaskContextPack schema_version must be 3")
    control = _mapping(pack.get("context_control"))
    if control.get("budget_profile") != "runtime":
        errors.append(f"{rel}: context_control.budget_profile must be runtime")
    if control.get("context_budget_tokens") != payload.get("budget_max_tokens"):
        errors.append(f"{rel}: context_control.context_budget_tokens must match budget_max_tokens")
    if isinstance(control.get("selected_file_count"), int) and isinstance(control.get("max_file_count"), int):
        if control["selected_file_count"] > control["max_file_count"]:
            errors.append(f"{rel}: selected_file_count exceeds max_file_count")
    plan = _mapping(pack.get("jit_retrieval_plan"))
    for field in ("targeted_reads", "deferred_reads", "forbidden_reads"):
        if not isinstance(plan.get(field), list):
            errors.append(f"{rel}: jit_retrieval_plan.{field} must be a list")
    for field in ("targeted_reads", "deferred_reads", "forbidden_reads"):
        for index, item in enumerate(plan.get(field) or []):
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                errors.append(f"{rel}: jit_retrieval_plan.{field}[{index}].path is required")
                continue
            if ABSOLUTE_PATH_RE.search(item["path"]):
                errors.append(f"{rel}: jit_retrieval_plan.{field}[{index}].path must be repository-relative")
    artifact_policy = _mapping(pack.get("artifact_policy"))
    if artifact_policy.get("full_graph_dump") != "forbidden":
        errors.append(f"{rel}: artifact_policy.full_graph_dump must be forbidden")
    return errors


def _tool_output_boundary_errors(path: Path, data: dict[str, Any]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    payload = _mapping(data.get("tool_output_boundary"))
    if not payload:
        return []
    record = _mapping(payload.get("record"))
    errors = _forbidden_key_errors(record, f"{rel}: tool_output_boundary.record")
    if record.get("output_size_class") != "large":
        errors.append(f"{rel}: tool_output_boundary output_size_class must be large")
    if record.get("privacy_status") != "pass":
        errors.append(f"{rel}: tool_output_boundary privacy_status must be pass")
    if record.get("llm_context_policy") not in {"artifact_reference_only", "rerun_with_redirect"}:
        errors.append(f"{rel}: tool_output_boundary llm_context_policy must be artifact/reference bounded")
    return errors


def _compaction_snapshot_errors(path: Path, data: dict[str, Any]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    payload = _mapping(data.get("compaction_snapshot_v2"))
    if not payload:
        return []
    record = _mapping(payload.get("record"))
    errors = _forbidden_key_errors(record, f"{rel}: compaction_snapshot_v2.record")
    if record.get("schema_version") != 2:
        errors.append(f"{rel}: compaction snapshot schema_version must be 2")
    for field in _string_list(payload.get("required_fields")):
        value = record.get(field)
        if value is None or value == "" or value == [] or value == {}:
            errors.append(f"{rel}: compaction snapshot missing required field {field}")
    if record.get("missing_required_fields") not in ([], None):
        errors.append(f"{rel}: compaction snapshot missing_required_fields must be empty")
    if record.get("privacy_redaction_status") != "pass":
        errors.append(f"{rel}: compaction snapshot privacy_redaction_status must be pass")
    context_control = _mapping(record.get("context_control"))
    for field in ("budget_mode", "selected_reference_count", "skipped_reference_count", "jit_retrieval_required", "tool_output_boundary_required"):
        if field not in context_control:
            errors.append(f"{rel}: compaction snapshot context_control.{field} is required")
    return errors


def _branch_route_repair_errors(path: Path, data: dict[str, Any]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    payload = _mapping(data.get("branch_route_repair_summary"))
    if not payload:
        return []
    record = _mapping(payload.get("record"))
    errors = _forbidden_key_errors(record, f"{rel}: branch_route_repair_summary.record")
    required = (
        "schema_version",
        "summary_id",
        "trigger",
        "abandoned_or_repaired_route",
        "reusable_findings",
        "forbidden_retries",
        "new_route",
        "residual_risk",
        "privacy_status",
    )
    for field in required:
        value = record.get(field)
        if value is None or value == "" or value == [] or value == {}:
            errors.append(f"{rel}: branch_route_repair_summary.{field} is required")
    if record.get("privacy_status") != "pass":
        errors.append(f"{rel}: branch_route_repair_summary privacy_status must be pass")
    return errors


def _forbidden_key_errors(value: Any, label: str) -> list[str]:
    errors: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                key_text = str(key)
                if key_text.casefold() in FORBIDDEN_RAW_FIELDS:
                    errors.append(f"{path}: forbidden raw field {key_text!r}")
                walk(child, f"{path}.{key_text}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")

    walk(value, label)
    return errors


def _secret_like_errors(path: Path, data: dict[str, Any]) -> list[str]:
    text = json.dumps(data, sort_keys=True)
    if SECRET_VALUE_RE.search(text):
        return [f"{path.relative_to(ROOT).as_posix()}: secret-like value found"]
    return []


def _schema_required_fields(root: Path) -> list[str]:
    schema = _read_json(root / "src" / "repository_intelligence" / "schemas" / "repository-context-pack.v3.schema.json")
    pack = (((schema or {}).get("properties") or {}).get("task_context_pack") or {})
    required = pack.get("required")
    return _string_list(required)


def _context_control_overhead(
    *,
    fixtures_pass: bool,
    raw_leak_count: int,
    live_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    base = {
        "status": "partial" if fixtures_pass else "fail",
        "input_token_overhead_pct": None,
        "output_token_overhead_pct": None,
        "turn_overhead": None,
        "command_delta": None,
        "pass_rate_delta": None,
        "overhead_policy_verdict": "",
        "evidence_boundary": (
            "Evidence separates structural fixture pass, live pass-rate, live runtime telemetry, "
            "token overhead, and turn overhead. High overhead without pass-rate improvement is not success."
        ),
    }
    if not fixtures_pass:
        base["overhead_policy_verdict"] = "fail: context-control fixtures failed"
        return base
    if raw_leak_count:
        base["status"] = "fail"
        base["overhead_policy_verdict"] = "fail: raw content leak detected"
        return base
    if not isinstance(live_summary, dict):
        base["status"] = "partial"
        base["overhead_policy_verdict"] = "partial: structural fixtures pass but live overhead is not collected"
        return base

    delta = (((live_summary.get("cost_summary") or {}).get("cost_adjusted_delta") or {}).get(
        "skills_with_hooks_clean_vs_baseline_clean"
    ) or {})
    if not isinstance(delta, dict):
        delta = ((live_summary.get("delta") or {}).get("skills_with_hooks_clean_vs_baseline_clean") or {})
    input_overhead = _ratio_to_percent(delta.get("average_input_token_overhead_pct", delta.get("input_tokens_delta_pct")))
    output_overhead = _ratio_to_percent(delta.get("average_output_token_overhead_pct", delta.get("output_tokens_delta_pct")))
    command_delta = delta.get("average_command_execution_delta", delta.get("command_execution_count_delta"))
    pass_rate_delta = delta.get("pass_rate_delta")
    base.update(
        {
            "input_token_overhead_pct": input_overhead,
            "output_token_overhead_pct": output_overhead,
            "command_delta": command_delta if isinstance(command_delta, int | float) else None,
            "pass_rate_delta": pass_rate_delta if isinstance(pass_rate_delta, int | float) else None,
        }
    )
    quality = live_summary.get("quality_improvement_summary") if isinstance(live_summary.get("quality_improvement_summary"), dict) else {}
    improvement_claim = bool(quality.get("large_quality_improvement_claim")) or bool(quality.get("efficiency_improvement_claim"))
    improvement_claim = improvement_claim or str(live_summary.get("effect_status") or "").casefold() == "improved"
    improvement_claim = improvement_claim or str(live_summary.get("effect_verdict") or "").casefold() == "positive"
    high_input = isinstance(input_overhead, int | float) and input_overhead > 100
    high_output = isinstance(output_overhead, int | float) and output_overhead > 75
    neutral_or_worse = not isinstance(pass_rate_delta, int | float) or pass_rate_delta <= 0
    collected = any(isinstance(value, int | float) for value in (input_overhead, output_overhead, command_delta, pass_rate_delta))
    if improvement_claim and neutral_or_worse and (high_input or high_output):
        base["status"] = "fail"
        base["overhead_policy_verdict"] = (
            "fail: live report claims improvement while pass-rate delta is neutral or negative and overhead is high"
        )
    elif collected and (high_input or high_output) and neutral_or_worse:
        base["status"] = "partial"
        base["overhead_policy_verdict"] = (
            "partial: structural fixtures pass, but live input/output overhead is high without pass-rate improvement; "
            "do not claim Context Control Plane quality improvement"
        )
    elif collected:
        base["status"] = "pass"
        base["overhead_policy_verdict"] = "pass: structural fixtures pass and collected overhead is within policy threshold"
    else:
        base["status"] = "partial"
        base["overhead_policy_verdict"] = "partial: structural fixtures pass but live overhead is not collected"
    return base


def _ratio_to_percent(value: Any) -> float | None:
    if not isinstance(value, int | float):
        return None
    return round(float(value) * 100, 2)


def evaluate(root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    runtime_policy = _load_runtime_policy()
    schema_required = _schema_required_fields(root)
    global_errors = _capability_registry_errors(root)
    cases: list[dict[str, Any]] = []
    raw_leak_count = 0

    if not (FIXTURE_DIR / "README.md").exists():
        global_errors.append("evals/context-control/README.md missing")

    for fixture in REQUIRED_FIXTURES:
        path = FIXTURE_DIR / fixture
        case_errors: list[str] = []
        data: dict[str, Any] = {}
        if not path.exists():
            case_errors.append(f"evals/context-control/{fixture} missing")
        else:
            loaded = load_yaml_file(path)
            if not isinstance(loaded, dict):
                case_errors.append(f"{path.relative_to(root).as_posix()}: fixture must be a mapping")
            else:
                data = loaded
                case_errors.extend(_fixture_schema_errors(path, data))
                case_errors.extend(_context_budget_errors(path, data))
                case_errors.extend(_routing_fixture_errors(path, data))
                case_errors.extend(_runtime_resolver_errors(path, data, runtime_policy))
                case_errors.extend(_jit_context_pack_errors(path, data, schema_required))
                case_errors.extend(_tool_output_boundary_errors(path, data))
                case_errors.extend(_compaction_snapshot_errors(path, data))
                case_errors.extend(_branch_route_repair_errors(path, data))
                case_errors.extend(_secret_like_errors(path, data))
        leak_errors = [error for error in case_errors if "forbidden raw field" in error or "secret-like value" in error]
        raw_leak_count += len(leak_errors)
        expected = _mapping(data.get("expected"))
        cases.append(
            {
                "id": data.get("id", fixture.removesuffix(".yaml")),
                "fixture": f"evals/context-control/{fixture}",
                "status": "fail" if case_errors else "pass",
                "errors": case_errors,
                "context_control_selected": expected.get("context_control_selected"),
                "budget_mode": expected.get("budget_mode"),
                "selected_reference_count": expected.get("selected_reference_count"),
                "skipped_reference_count": expected.get("skipped_reference_count"),
                "safety_result": expected.get("safety_result"),
                "closure_result": expected.get("closure_result"),
            }
        )

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed
    fixtures_pass = not global_errors and failed == 0
    live_summary = _read_json(LIVE_SUMMARY)
    overhead = _context_control_overhead(
        fixtures_pass=fixtures_pass,
        raw_leak_count=raw_leak_count,
        live_summary=live_summary if isinstance(live_summary, dict) else None,
    )
    status = "pass" if fixtures_pass and overhead.get("status") != "fail" else "fail"
    report = {
        "schema_version": 1,
        "generated_by": "scripts/eval-context-control-plane.py",
        "status": status,
        "summary": {
            "case_count": len(cases),
            "passed": passed,
            "failed": failed,
            "global_error_count": len(global_errors),
            "raw_leak_count": raw_leak_count,
            "capability": CAPABILITY_NAME,
            "capability_id": CAPABILITY_ID,
            "fixture_directory": "evals/context-control",
            "live_codex_executed": False,
        },
        "global_errors": global_errors,
        "cases": cases,
        "context_control_overhead": overhead,
    }
    errors = [*global_errors, *(error for case in cases for error in case["errors"])]
    if overhead.get("status") == "fail":
        errors.append(str(overhead.get("overhead_policy_verdict")))
    return report, errors


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    overhead = report.get("context_control_overhead", {})
    lines = [
        "# Context Control Plane Eval",
        "",
        f"- status: `{report.get('status')}`",
        f"- cases: `{summary.get('passed')}/{summary.get('case_count')}`",
        f"- raw_leak_count: `{summary.get('raw_leak_count')}`",
        f"- live_codex_executed: `{summary.get('live_codex_executed')}`",
        "",
        "## Context Control Overhead",
        "",
    ]
    for field in (
        "status",
        "input_token_overhead_pct",
        "output_token_overhead_pct",
        "turn_overhead",
        "command_delta",
        "pass_rate_delta",
        "overhead_policy_verdict",
        "evidence_boundary",
    ):
        lines.append(f"- {field}: `{overhead.get(field)}`")
    lines.extend(["", "## Cases", "", "| Case | Status | Budget | Selected refs | Skipped refs |", "| --- | --- | --- | --- | --- |"])
    for case in report.get("cases", []):
        lines.append(
            f"| {case.get('id')} | `{case.get('status')}` | `{case.get('budget_mode')}` | "
            f"`{case.get('selected_reference_count')}` | `{case.get('skipped_reference_count')}` |"
        )
    if report.get("global_errors"):
        lines.extend(["", "## Global Errors", ""])
        lines.extend(f"- {error}" for error in report["global_errors"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=REPORT_JSON)
    parser.add_argument("--out", type=Path, default=REPORT_MD)
    args = parser.parse_args(argv)

    report, errors = evaluate(ROOT)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    if errors:
        return fail_many("eval-context-control-plane", errors)
    print(f"eval-context-control-plane: pass ({report['summary']['passed']}/{report['summary']['case_count']} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
