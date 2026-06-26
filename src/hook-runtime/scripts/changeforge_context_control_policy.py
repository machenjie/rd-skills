#!/usr/bin/env python3
"""Deterministic context budget policy for ChangeForge hook runtime."""

from __future__ import annotations

from typing import Any, Iterable


BUDGET_LIMITS: dict[str, dict[str, int]] = {
    "minimal": {
        "max_selected_skills": 2,
        "max_selected_capabilities": 5,
        "max_required_references": 8,
    },
    "single-stage": {
        "max_selected_skills": 3,
        "max_selected_capabilities": 8,
        "max_required_references": 12,
    },
    "staged-plan": {
        "max_selected_skills": 4,
        "max_selected_capabilities": 12,
        "max_required_references": 16,
    },
    "full": {
        "max_selected_skills": 6,
        "max_selected_capabilities": 18,
        "max_required_references": 24,
    },
}

ROUTER_SELF_REFERENCES = (
    "references/routing-rules.md",
    "references/skill-registry.md",
    "references/capability-index.md",
    "references/domain-extension-index.md",
)

CONTEXT_RISK_SURFACES = {
    "skill-authoring",
    "agent-runtime-governance",
    "repository-intelligence",
    "project-memory",
    "validation-broker",
    "execution-trajectory",
}
CONTEXT_RISK_TERMS = (
    "context budget",
    "reference bloat",
    "selected references",
    "skipped references",
    "jit retrieval",
    "just in time retrieval",
    "tool output boundary",
    "compaction snapshot",
    "generated artifact",
    "source of truth",
    "broad system audit",
    "hook runtime",
)
FORBIDDEN_RECORD_KEYS = {
    "prompt",
    "prompt_text",
    "raw_prompt",
    "stdout",
    "stderr",
    "command_output",
    "raw_output",
    "raw_command_output",
    "full_output",
    "full_diff",
    "full_file",
    "file_contents",
    "environment",
    "env",
    "secret",
    "secrets",
    "password",
    "api_key",
    "apikey",
    "access_token",
    "bearer_token",
    "credential",
    "credentials",
}
FORBIDDEN_RECORD_KEY_TOKENS = (
    "raw_prompt",
    "prompt_text",
    "raw_output",
    "raw_command_output",
    "command_output",
    "stdout",
    "stderr",
    "full_output",
    "full_diff",
    "full_file",
    "file_contents",
    "environment",
    "access_token",
    "bearer_token",
    "api_key",
    "apikey",
    "password",
    "secret",
    "credential",
)


def context_budget_mode(
    stage: str,
    risk_surfaces: list[str],
    product_surfaces: list[str],
    classification: dict | None = None,
) -> str:
    """Return a deterministic context budget mode from bounded route facts."""
    classification = classification if isinstance(classification, dict) else {}
    stage_text = str(stage or classification.get("stage") or "").strip()
    risks = set(_strings(risk_surfaces))
    products = set(_strings(product_surfaces))
    signals = _classification_text(classification)

    explicit = str(classification.get("context_budget_mode") or "").strip()
    if explicit in BUDGET_LIMITS:
        return explicit
    if stage_text == "compaction":
        return "minimal"
    if "broad system audit" in signals or "full context" in signals:
        return "staged-plan"
    if products & CONTEXT_RISK_SURFACES:
        return "staged-plan"
    if {"delivery", "reliability", "security", "data-api"} & risks and len(products) > 1:
        return "staged-plan"
    if len(products) >= 3 or len(risks) >= 2:
        return "staged-plan"
    if any(term in signals for term in CONTEXT_RISK_TERMS):
        return "single-stage"
    if stage_text in {"implementation-planning", "coding", "code-review", "testing", "refactoring"}:
        return "single-stage"
    return "minimal"


def context_budget_limits(mode: str) -> dict[str, int]:
    """Return budget limits for a known mode, falling back to minimal."""
    return dict(BUDGET_LIMITS.get(str(mode or ""), BUDGET_LIMITS["minimal"]))


def build_context_control_record(
    active_context: dict,
    state: dict | None = None,
    classification: dict | None = None,
) -> dict:
    """Build a bounded context-control record from active route facts."""
    active_context = active_context if isinstance(active_context, dict) else {}
    state = state if isinstance(state, dict) else {}
    classification = classification if isinstance(classification, dict) else {}
    stage = str(active_context.get("current_stage") or active_context.get("stage") or classification.get("stage") or "")
    risk_surfaces = _strings(active_context.get("risk_surfaces") or classification.get("risk_surfaces"))
    product_surfaces = _strings(active_context.get("product_surfaces") or classification.get("product_surfaces"))
    capabilities = _strings(active_context.get("selected_capabilities"))
    skills = _strings(active_context.get("selected_skills"))
    raw_references = _strings(active_context.get("required_references"))
    mode = context_budget_mode(stage, risk_surfaces, product_surfaces, classification)
    limits = context_budget_limits(mode)
    kept_references, skipped_references = apply_reference_budget(
        raw_references,
        mode,
        always_keep=ROUTER_SELF_REFERENCES,
    )
    selected_refs = [
        {"reference": reference, "reason": _reference_reason(reference)}
        for reference in kept_references
    ]
    compaction_required = stage == "compaction" or _has_signal(classification, "compaction")
    jit_required = bool(
        set(product_surfaces) & {"repository-intelligence", "project-memory"}
        or "repository-graph-analysis" in capabilities
        or _has_signal(classification, "source of truth")
        or _has_signal(classification, "generated artifact")
        or _has_signal(classification, "jit retrieval")
    )
    output_boundary_required = bool(
        set(product_surfaces) & {"validation-broker", "execution-trajectory"}
        or "validation-broker" in capabilities
        or state.get("validation_results")
        or state.get("command_risks")
        or _has_signal(classification, "tool output boundary")
        or _has_signal(classification, "output truncation")
    )
    overhead_required = bool("context-control-plane" in capabilities or skipped_references)
    record = {
        "schema_version": 1,
        "route_id": str(active_context.get("route_id") or active_context.get("route") or "active-runtime-route")[:120],
        "current_stage": stage,
        "budget_mode": mode,
        "budget_rationale": _budget_rationale(mode, stage, product_surfaces, risk_surfaces, classification),
        **limits,
        "selected_skill_count": len(skills),
        "selected_capability_count": len(capabilities),
        "raw_required_reference_count": len(raw_references),
        "selected_reference_count": len(selected_refs),
        "skipped_reference_count": len(skipped_references),
        "selected_references": selected_refs,
        "skipped_references": skipped_references,
        "jit_retrieval_required": jit_required,
        "jit_retrieval_plan": "read current source paths selected by route/graph only" if jit_required else "not required",
        "tool_output_boundary_required": output_boundary_required,
        "tool_output_boundary": (
            "summarize command, outcome, relevant excerpt, artifact path, and excluded-output rationale"
            if output_boundary_required
            else "bounded hook context only"
        ),
        "compaction_snapshot_required": compaction_required,
        "compaction_snapshot_fields": (
            ["route", "stage", "selected references", "skipped references", "validation", "residual risk"]
            if compaction_required
            else []
        ),
        "branch_route_repair_summary_required": _has_signal(classification, "branch")
        or _has_signal(classification, "route repair"),
        "overhead_evidence_required": overhead_required,
        "overhead_evidence": {
            "selected_skills": len(skills),
            "selected_capabilities": len(capabilities),
            "selected_references": len(selected_refs),
            "skipped_references": len(skipped_references),
            "token_overhead": "not_collected",
            "turn_overhead": "not_collected",
        },
        "privacy_exclusions": [
            "raw prompts",
            "secrets",
            "environment variables",
            "full command output",
            "full diffs",
            "full file contents",
        ],
        "residual_context_risk": _residual_context_risk(skipped_references, overhead_required),
    }
    record["over_budget_findings"] = over_budget_findings(record)
    return _sanitize_record(record)


def apply_reference_budget(
    required_references: list[str],
    mode: str,
    always_keep: list[str] | tuple[str, ...] = (),
) -> tuple[list[str], list[dict]]:
    """Return kept references and explicit skipped-reference records."""
    refs = _unique(_strings(required_references))
    keep_first = _unique([*always_keep, *[ref for ref in ROUTER_SELF_REFERENCES if ref in refs]])
    limit = context_budget_limits(mode)["max_required_references"]
    kept: list[str] = []
    for reference in keep_first:
        if reference in refs and reference not in kept and len(kept) < limit:
            kept.append(reference)
    for reference in refs:
        if reference in kept:
            continue
        if len(kept) >= limit:
            break
        kept.append(reference)
    skipped = [
        {
            "reference": reference,
            "reason": f"omitted by {mode} max_required_references={limit}; use JIT retrieval if needed",
        }
        for reference in refs
        if reference not in kept
    ]
    return kept, skipped


def over_budget_findings(record: dict) -> list[str]:
    """Return deterministic findings for any selected context count above budget."""
    if not isinstance(record, dict):
        return ["invalid context_control record"]
    findings: list[str] = []
    for count_field, limit_field, label in (
        ("selected_skill_count", "max_selected_skills", "selected_skills"),
        ("selected_capability_count", "max_selected_capabilities", "selected_capabilities"),
        ("selected_reference_count", "max_required_references", "required_references"),
    ):
        count = _int(record.get(count_field))
        limit = _int(record.get(limit_field))
        if limit >= 0 and count > limit:
            findings.append(f"{label} {count}/{limit} over budget")
    skipped_count = _int(record.get("skipped_reference_count"))
    if skipped_count:
        findings.append(f"skipped_references {skipped_count} require JIT retrieval rationale")
    return findings


def _budget_rationale(
    mode: str,
    stage: str,
    product_surfaces: list[str],
    risk_surfaces: list[str],
    classification: dict,
) -> str:
    if mode == "minimal":
        return "minimal route or no-injection event with no context-risk expansion"
    if mode == "single-stage":
        return f"single active stage {stage or 'unknown'} with bounded route references"
    signals = _classification_text(classification)
    if "broad system audit" in signals:
        return "broad system audit requires staged context with skipped-reference rationale"
    if product_surfaces:
        return "context-risk product surfaces require staged context: " + ", ".join(product_surfaces[:4])
    if risk_surfaces:
        return "multiple or high-impact risk surfaces require staged context: " + ", ".join(risk_surfaces[:4])
    return "staged context required by route complexity"


def _reference_reason(reference: str) -> str:
    if reference in ROUTER_SELF_REFERENCES:
        return "router self-reference kept"
    return "selected capability reference within budget"


def _residual_context_risk(skipped_references: list[dict], overhead_required: bool) -> list[str]:
    risks: list[str] = []
    if skipped_references:
        risks.append("skipped references require JIT retrieval before use")
    if overhead_required:
        risks.append("live token and turn overhead not collected by deterministic runtime policy")
    return risks or ["no residual context budget risk detected"]


def _classification_text(classification: dict) -> str:
    parts: list[str] = []
    for key in ("stage", "tool", "command_program"):
        value = classification.get(key)
        if isinstance(value, str):
            parts.append(value)
    for key in ("prompt_signals", "conditional_capabilities", "paths", "product_surfaces", "risk_surfaces"):
        parts.extend(_strings(classification.get(key)))
    return " ".join(parts).casefold()


def _has_signal(classification: dict, signal: str) -> bool:
    return signal.casefold() in _classification_text(classification)


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, Iterable):
        raw_values = list(value)
    else:
        raw_values = [value]
    return _unique(str(item).strip() for item in raw_values if str(item).strip())


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sanitize_record(value: Any) -> dict:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        if not key or _forbidden_record_key(key):
            continue
        if isinstance(raw_value, dict):
            child = _sanitize_record(raw_value)
            if child:
                cleaned[key] = child
        elif isinstance(raw_value, (list, tuple)):
            cleaned[key] = [_sanitize_item(item) for item in raw_value[:50]]
        elif isinstance(raw_value, bool) or isinstance(raw_value, int):
            cleaned[key] = raw_value
        else:
            cleaned[key] = str(raw_value).strip()[:300]
    return cleaned


def _forbidden_record_key(key: str) -> bool:
    lowered = key.casefold()
    return lowered in FORBIDDEN_RECORD_KEYS or any(token in lowered for token in FORBIDDEN_RECORD_KEY_TOKENS)


def _sanitize_item(value: Any) -> Any:
    if isinstance(value, dict):
        return _sanitize_record(value)
    if isinstance(value, bool) or isinstance(value, int):
        return value
    return str(value).strip()[:300]


__all__ = [
    "BUDGET_LIMITS",
    "ROUTER_SELF_REFERENCES",
    "apply_reference_budget",
    "build_context_control_record",
    "context_budget_limits",
    "context_budget_mode",
    "over_budget_findings",
]
