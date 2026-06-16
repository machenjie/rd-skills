#!/usr/bin/env python3
"""Per-gate policy helpers for ChangeForge hook runtime scripts."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any


HOOK_MODES = {"off", "monitor", "warn", "block"}
FAILURE_MODES = {"fail_open", "fail_closed"}
CONFIDENCE_BLOCK_VALUES = {"high"}

DEFAULT_TIMEOUT_MS = 10000
DEFAULT_RETRIES = 0
DEFAULT_RETRY_DELAY_MS = 100
DEFAULT_MAX_CONCURRENCY = 1
DEFAULT_QUEUE_LIMIT = 10

GATE_MODE_ENV = {
    "pre_edit_structure": "CHANGEFORGE_PRE_EDIT_MODE",
    "permission_policy": "CHANGEFORGE_PERMISSION_MODE",
    "stop_closure": "CHANGEFORGE_STOP_MODE",
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
    specific = GATE_MODE_ENV.get(_normalize_gate(gate_name), "")
    if specific:
        mode = _mode_from_env(specific)
        if mode:
            return mode
    global_mode = _mode_from_env("CHANGEFORGE_HOOK_MODE")
    return global_mode or "warn"


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
    return (
        gate_mode(gate_name) == "block"
        and str(confidence).strip().casefold() in CONFIDENCE_BLOCK_VALUES
    )


def should_emit_context(gate_name: str) -> bool:
    """Return true when the gate should emit advisory context."""
    return gate_mode(gate_name) in {"warn", "block"}


def _normalize_gate(value: str) -> str:
    return str(value or "").strip().casefold().replace("-", "_")


def _mode_from_env(name: str) -> str:
    mode = os.environ.get(name, "").strip().casefold()
    return mode if mode in HOOK_MODES else ""


def _failure_from_env(name: str) -> str:
    mode = os.environ.get(name, "").strip().casefold()
    return mode if mode in FAILURE_MODES else ""


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, "").strip())
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


__all__ = [
    "failure_mode",
    "gate_mode",
    "policy_for",
    "run_gate_with_policy",
    "should_block",
    "should_emit_context",
]
