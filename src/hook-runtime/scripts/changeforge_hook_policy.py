#!/usr/bin/env python3
"""Per-gate policy helpers for ChangeForge hook runtime scripts."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from changeforge_gate_result import GateResult


HOOK_MODES = {"off", "observe", "monitor", "advisor", "report", "warn", "block"}
FAILURE_MODES = {"fail_open", "fail_closed"}
CONFIDENCE_BLOCK_VALUES = {"high"}

DEFAULT_TIMEOUT_MS = 10000
DEFAULT_RETRIES = 0
DEFAULT_RETRY_DELAY_MS = 100
DEFAULT_MAX_CONCURRENCY = 1
DEFAULT_QUEUE_LIMIT = 10

GATE_MODE_ENV = {
    "risk_surface": "CHANGEFORGE_RISK_SURFACE_MODE",
    "sdd_material_choice": "CHANGEFORGE_SDD_CHOICE_MODE",
    "pre_edit_structure": "CHANGEFORGE_PRE_EDIT_MODE",
    "permission_policy": "CHANGEFORGE_PERMISSION_MODE",
    "process_phase": "CHANGEFORGE_PROCESS_PHASE_MODE",
    "subagent_review": "CHANGEFORGE_SUBAGENT_REVIEW_MODE",
    "stop_closure": "CHANGEFORGE_STOP_MODE",
}
STAGE_GATE_MODE_ENV = {
    ("sdd_material_choice", "pretool"): "CHANGEFORGE_SDD_CHOICE_PRETOOL_MODE",
    ("sdd_material_choice", "stop"): "CHANGEFORGE_SDD_CHOICE_STOP_MODE",
    ("process_phase", "pretool"): "CHANGEFORGE_PROCESS_PHASE_PRETOOL_MODE",
    ("process_phase", "stop"): "CHANGEFORGE_PROCESS_PHASE_STOP_MODE",
    ("stop_closure", "stop"): "CHANGEFORGE_STOP_MODE",
}
STOP_STAGE_MODE_ENV = {
    "sdd_material_choice": (
        "CHANGEFORGE_SDD_CHOICE_STOP_MODE",
        "CHANGEFORGE_STOP_MODE",
    ),
    "process_phase": (
        "CHANGEFORGE_PROCESS_PHASE_STOP_MODE",
        "CHANGEFORGE_STOP_MODE",
    ),
    "stop_closure": (
        "CHANGEFORGE_STOP_CLOSURE_MODE",
        "CHANGEFORGE_STOP_MODE",
    ),
}
DEFAULT_GATE_MODES = {
    "risk_surface": "warn",
    "sdd_material_choice": "warn",
    "sdd_material_choice_pretool": "warn",
    "sdd_material_choice_stop": "warn",
    "pre_edit_structure": "warn",
    "process_phase": "monitor",
    "process_phase_pretool": "monitor",
    "process_phase_stop": "warn",
    "stop_closure": "warn",
}
PROFESSIONAL_PROCESS_GATES = {
    "risk_surface",
    "sdd_material_choice",
    "pre_edit_structure",
    "process_phase",
    "stop_closure",
}
STRICT_BLOCKING_ENV = (
    "CHANGEFORGE_STRICT_BLOCKING",
    "CHANGEFORGE_BENCHMARK_MODE",
    "CHANGEFORGE_CI_MODE",
)
STRICT_BLOCKING_VALUES = {
    "1",
    "true",
    "yes",
    "strict",
    "benchmark",
    "ci",
}


def policy_for(gate_name: str, event: dict | None = None) -> dict:
    """Return a normalized policy for one gate.

    ``event`` is accepted for future adapter-specific policy data. The current
    implementation is intentionally environment-only so the runtime never reads
    prompts, credentials, or project files to decide policy.
    """
    _ = event
    mode = gate_mode(gate_name)
    return {
        "mode": mode,
        "failure_mode": failure_mode(gate_name),
        "timeout_ms": _int_env("CHANGEFORGE_HOOK_TIMEOUT_MS", DEFAULT_TIMEOUT_MS),
        "retries": _int_env("CHANGEFORGE_HOOK_RETRIES", DEFAULT_RETRIES),
        "retry_delay_ms": _int_env(
            "CHANGEFORGE_HOOK_RETRY_DELAY_MS", DEFAULT_RETRY_DELAY_MS
        ),
        "max_concurrency": _int_env(
            "CHANGEFORGE_HOOK_MAX_CONCURRENCY", DEFAULT_MAX_CONCURRENCY
        ),
        "queue_limit": _int_env("CHANGEFORGE_HOOK_QUEUE_LIMIT", DEFAULT_QUEUE_LIMIT),
    }


def gate_mode(gate_name: str) -> str:
    """Return off / monitor / warn / block for the gate."""
    gate_key = _normalize_gate(gate_name)
    if gate_key == "stop_closure":
        return gate_mode_for_stage(gate_key, "stop")
    specific = GATE_MODE_ENV.get(gate_key, "")
    if specific:
        mode = _mode_from_env(specific)
        if mode:
            return mode
    global_mode = _mode_from_env("CHANGEFORGE_HOOK_MODE")
    if global_mode:
        if (
            global_mode == "block"
            and gate_key in PROFESSIONAL_PROCESS_GATES
            and not strict_process_blocking_enabled()
        ):
            return DEFAULT_GATE_MODES.get(gate_key, "warn")
        return global_mode
    return DEFAULT_GATE_MODES.get(gate_key, "warn")


def gate_mode_for_stage(gate_name: str, stage: str) -> str:
    """Return a gate mode with stage-specific Stop/PreTool defaults.

    Stop gates are intentionally not upgraded by CHANGEFORGE_HOOK_MODE=block.
    They require CHANGEFORGE_STOP_MODE, a stage-specific *_STOP_MODE, or a
    gate-specific Stop variable. This keeps IDE Stop/Close liveness independent
    from stricter PreTool enforcement.
    """
    gate_key = _normalize_gate(gate_name)
    stage_key = _normalize_stage(stage)
    default_key = f"{gate_key}_{stage_key}" if stage_key else gate_key
    if _is_stop_stage(gate_key, stage_key):
        for env_name in STOP_STAGE_MODE_ENV.get(gate_key, ("CHANGEFORGE_STOP_MODE",)):
            mode = _mode_from_env(env_name)
            if mode:
                return mode
        return DEFAULT_GATE_MODES.get(
            default_key, DEFAULT_GATE_MODES.get(gate_key, "warn")
        )
    stage_specific = STAGE_GATE_MODE_ENV.get((gate_key, stage_key), "")
    if stage_specific:
        mode = _mode_from_env(stage_specific)
        if mode:
            return mode
    gate_specific = GATE_MODE_ENV.get(gate_key, "")
    if gate_specific:
        mode = _mode_from_env(gate_specific)
        if mode:
            return mode
    global_mode = _mode_from_env("CHANGEFORGE_HOOK_MODE")
    if global_mode:
        if (
            global_mode == "block"
            and gate_key in PROFESSIONAL_PROCESS_GATES
            and not strict_process_blocking_enabled()
        ):
            return DEFAULT_GATE_MODES.get(default_key, DEFAULT_GATE_MODES.get(gate_key, "warn"))
        return global_mode
    return DEFAULT_GATE_MODES.get(default_key, DEFAULT_GATE_MODES.get(gate_key, "warn"))


def failure_mode(gate_name: str) -> str:
    """Return fail_open / fail_closed for the gate; default is fail_open."""
    gate_key = _normalize_gate(gate_name).upper()
    specific = _failure_from_env(f"CHANGEFORGE_{gate_key}_FAILURE_MODE")
    if specific:
        return specific
    global_failure = _failure_from_env("CHANGEFORGE_HOOK_FAILURE_MODE")
    return global_failure or "fail_open"


def run_gate_with_policy(
    gate_name: str,
    main_fn: Callable[[], int],
    *,
    fail_closed: Callable[[Exception], None],
    fail_open: Callable[[Exception], None] | None = None,
) -> int:
    """Run one gate and apply its configured exception strategy."""
    try:
        result = main_fn()
    except Exception as exc:
        if failure_mode(gate_name) == "fail_closed":
            fail_closed(exc)
        elif fail_open is not None:
            fail_open(exc)
        return 0
    return result if isinstance(result, int) else 0


def should_block(gate_name: str, confidence: str = "high") -> bool:
    """Block only when the gate is configured to block and confidence is high."""
    return gate_result(gate_name, confidence=confidence).should_block


def should_emit_context(gate_name: str) -> bool:
    """Return true when the gate should emit advisory context."""
    return gate_result(gate_name).should_emit


def gate_result(
    gate_name: str,
    *,
    confidence: str = "medium",
    severity: str = "warning",
    message: str = "",
    facts: dict | None = None,
    residual_risk: str = "",
) -> GateResult:
    """Return the normalized GateResult for legacy policy helpers."""
    confidence_value = str(confidence).strip().casefold()
    if confidence_value not in {"low", "medium", *CONFIDENCE_BLOCK_VALUES}:
        confidence_value = "medium"
    return GateResult.from_policy(
        gate_name,
        mode=gate_mode(gate_name),
        confidence=confidence_value,
        severity=severity,
        message=message,
        facts=facts,
        residual_risk=residual_risk,
    )


def _normalize_gate(value: str) -> str:
    return str(value or "").strip().casefold().replace("-", "_")


def _normalize_stage(value: str) -> str:
    stage = str(value or "").strip().casefold().replace("-", "_")
    if stage in {"pre_tool", "pretooluse", "pre_tool_use"}:
        return "pretool"
    if stage in {"stopuse", "stop_hook", "closure"}:
        return "stop"
    return stage


def _is_stop_stage(gate_key: str, stage_key: str) -> bool:
    return stage_key == "stop" or gate_key == "stop_closure"


def _mode_from_env(name: str) -> str:
    mode = os.environ.get(name, "").strip().casefold()
    return mode if mode in HOOK_MODES else ""


def _failure_from_env(name: str) -> str:
    mode = os.environ.get(name, "").strip().casefold()
    return mode if mode in FAILURE_MODES else ""


def strict_process_blocking_enabled() -> bool:
    """Return whether global block mode may affect professional process gates."""
    return any(
        os.environ.get(name, "").strip().casefold() in STRICT_BLOCKING_VALUES
        for name in STRICT_BLOCKING_ENV
    )


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, "").strip())
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


__all__ = [
    "failure_mode",
    "gate_result",
    "gate_mode",
    "gate_mode_for_stage",
    "policy_for",
    "run_gate_with_policy",
    "should_block",
    "should_emit_context",
    "strict_process_blocking_enabled",
]
