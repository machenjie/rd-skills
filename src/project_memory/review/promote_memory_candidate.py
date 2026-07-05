"""Human-approved Project Memory candidate promotion helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from project_memory.privacy import contains_forbidden_key, contains_sensitive_value
from project_memory.source_evidence import memory_hit_from_event


ALLOWED_TARGETS = {
    "evals/agent-behavior/samples",
    "evals/pressure",
    "tests/fixtures/hooks",
    "tests/project_memory/fixtures",
}
PROMOTION_TARGET_ALIASES = {
    "memory": "tests/project_memory/fixtures",
    "hook_fixture": "tests/fixtures/hooks",
    "eval": "evals/agent-behavior/samples",
}
FORBIDDEN_TARGET_TOKENS = (
    "SKILL.md",
    "src/registry",
    "routing-rules",
    "capabilities.yaml",
    "domain-extensions.yaml",
    "src/professional-skills",
    "src/foundation",
    "dist/",
)
PROMOTION_TYPES = {
    "success_rule",
    "failure_pattern",
    "fragile_file",
    "anti_pattern",
    "routing_hint",
}


def supported_target(target: str) -> bool:
    """Return True only for human-review candidate skeleton targets."""
    normalized = _canonical_target(target)
    if any(token.casefold() in normalized.casefold() for token in FORBIDDEN_TARGET_TOKENS):
        return False
    return normalized in ALLOWED_TARGETS


def candidate_output_path(repo_root: Path, suggestion: dict[str, Any], target: str | None = None) -> Path:
    """Return the deterministic candidate path for a selected suggestion."""
    selected_target = _canonical_target(target or str(suggestion.get("promotion_target", "")))
    if not supported_target(selected_target):
        raise ValueError(f"unsupported promotion_target: {selected_target}")
    suggestion_id = str(suggestion.get("id", "")).strip()
    if not suggestion_id:
        raise ValueError("suggestion is missing id")
    suffix = ".json" if selected_target == "tests/project_memory/fixtures" else ".yaml"
    return repo_root / selected_target / f"memory-{_safe_id(suggestion_id)}{suffix}"


def render_candidate(suggestion: dict[str, Any], target: str) -> str:
    """Render a skeleton candidate that must be completed by a human."""
    suggestion_id = str(suggestion.get("id", "")).strip()
    suggestion_type = str(suggestion.get("type", "memory_candidate")).strip()
    if target == "evals/pressure":
        return _pressure_candidate(suggestion_id, suggestion_type)
    if target == "evals/agent-behavior/samples":
        return _agent_behavior_candidate(suggestion_id, suggestion_type)
    if target == "tests/fixtures/hooks":
        return _hook_fixture_candidate(suggestion_id, suggestion_type)
    if target == "tests/project_memory/fixtures":
        return _memory_gate_fixture_candidate(suggestion_id, suggestion_type)
    raise ValueError(f"unsupported promotion_target: {target}")


def write_candidate(
    repo_root: Path,
    suggestion: dict[str, Any],
    *,
    target: str | None = None,
    write: bool = False,
) -> Path:
    """Write or dry-run a candidate skeleton; never promote directly."""
    output = candidate_output_path(repo_root, suggestion, target)
    validation = validate_promotion_candidate(repo_root, suggestion)
    if not validation["allowed"]:
        reasons = ", ".join(validation["reasons"])
        raise ValueError(f"promotion evidence gate failed: {reasons}")
    if write:
        output.parent.mkdir(parents=True, exist_ok=True)
        selected_target = _canonical_target(target or str(suggestion.get("promotion_target", "")))
        output.write_text(render_candidate(suggestion, selected_target), encoding="utf-8")
    return output


def validate_promotion_candidate(repo_root: Path, suggestion: dict[str, Any]) -> dict[str, Any]:
    """Validate human-review promotion evidence before writing a skeleton."""
    source = suggestion if isinstance(suggestion, dict) else {}
    reasons: list[str] = []
    promotion_type = str(source.get("promotion_type") or "").strip()
    if promotion_type not in PROMOTION_TYPES:
        reasons.append("promotion_type must be explicit and allowed")
    if contains_forbidden_key(source) or contains_sensitive_value(source):
        reasons.append("candidate contains forbidden raw prompt/output/secret-like data")
    if not source.get("requires_human_review"):
        reasons.append("requires_human_review must be true")
    residual = source.get("residual_risk")
    if not residual:
        reasons.append("residual_risk classification is required")

    event_like = _event_like(source)
    hit = memory_hit_from_event(event_like, repo_root=repo_root)
    if hit["source_status"] != "current":
        reasons.append(f"source_status must be current, got {hit['source_status']}")
    if hit["confidence"] != "strong":
        reasons.append("current validation/review evidence is required")
    if promotion_type in {"failure_pattern", "anti_pattern", "fragile_file"} and not _has_failure_or_review_evidence(source):
        reasons.append("failure/review evidence is required for failure-derived promotions")
    if promotion_type == "success_rule" and not _has_validation_evidence(source):
        reasons.append("verified validation evidence is required for success_rule promotion")
    if hit["source_status"] == "generated" and not _has_source_of_truth(source):
        reasons.append("generated artifacts require source_of_truth evidence")
    return {
        "allowed": not reasons,
        "reasons": reasons,
        "promotion_type": promotion_type,
        "source_status": hit["source_status"],
        "evidence_role": hit["evidence_role"],
        "confidence": hit["confidence"],
    }


def _canonical_target(target: str) -> str:
    normalized = str(target or "").strip().replace("\\", "/").strip("/")
    return PROMOTION_TARGET_ALIASES.get(normalized, normalized)


def _event_like(suggestion: dict[str, Any]) -> dict[str, Any]:
    evidence = suggestion.get("source_evidence") if isinstance(suggestion.get("source_evidence"), dict) else {}
    path = str(evidence.get("repo_rel_path") or suggestion.get("path") or suggestion.get("affected_path") or "").strip()
    return {
        "event_id": str(suggestion.get("id") or ""),
        "kind": str(suggestion.get("type") or suggestion.get("promotion_type") or ""),
        "type": str(suggestion.get("type") or ""),
        "paths": [path] if path else [],
        "bounded_paths": [path] if path else [],
        "source_evidence": evidence,
        "evidence_refs": _evidence_refs(suggestion),
    }


def _evidence_refs(suggestion: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    raw = suggestion.get("evidence_refs")
    if isinstance(raw, list):
        refs.extend(str(item) for item in raw)
    for key in ("validation_evidence", "review_evidence", "failure_evidence", "source_of_truth"):
        value = suggestion.get(key)
        if isinstance(value, list):
            refs.extend(f"{key}:{item}" for item in value)
        elif value:
            refs.append(f"{key}:{value}")
    return refs[:50]


def _has_validation_evidence(suggestion: dict[str, Any]) -> bool:
    return bool(suggestion.get("validation_evidence") or _contains_evidence_ref(suggestion, "validation"))


def _has_failure_or_review_evidence(suggestion: dict[str, Any]) -> bool:
    return bool(
        suggestion.get("failure_evidence")
        or suggestion.get("review_evidence")
        or _contains_evidence_ref(suggestion, "review")
        or _contains_evidence_ref(suggestion, "failure")
        or _contains_evidence_ref(suggestion, "validation")
    )


def _contains_evidence_ref(suggestion: dict[str, Any], token: str) -> bool:
    return any(token in str(ref).casefold() for ref in suggestion.get("evidence_refs") or [])


def _has_source_of_truth(suggestion: dict[str, Any]) -> bool:
    return bool(suggestion.get("source_of_truth") or _contains_evidence_ref(suggestion, "source_of_truth"))


def _pressure_candidate(suggestion_id: str, suggestion_type: str) -> str:
    return f"""generated_from_project_memory: true
requires_human_review: true
source_suggestion_id: {suggestion_id}
id: TODO-memory-pressure-{_safe_id(suggestion_id)}
pressure_type: {suggestion_type}
prompt: TODO human-reviewed pressure prompt
expected_route:
  skills:
    - TODO
  capabilities:
    - TODO
required_capabilities:
  - TODO
required_evidence:
  - validation evidence
forbidden_behaviors:
  - TODO
rationalizations_to_reject:
  - TODO
completion_claim_allowed: false
expected_handoff_fields:
  - residual risk
notes: TODO complete before treating as formal eval input.
"""


def _agent_behavior_candidate(suggestion_id: str, suggestion_type: str) -> str:
    return f"""generated_from_project_memory: true
requires_human_review: true
source_suggestion_id: {suggestion_id}
id: TODO-memory-behavior-{_safe_id(suggestion_id)}
description: TODO human-reviewed memory-derived behavior sample for {suggestion_type}
prompt: TODO bounded prompt summary, not raw private prompt
expected:
  selected_skills:
    - TODO
  selected_capabilities:
    - TODO
  required_references:
    - references/routing-rules.md
  required_quality_gates:
    - TODO
actual:
  validation_evidence: false
  residual_risk: true
"""


def _hook_fixture_candidate(suggestion_id: str, suggestion_type: str) -> str:
    return f"""generated_from_project_memory: true
requires_human_review: true
source_suggestion_id: {suggestion_id}
fixture_type: hook
memory_candidate_type: {suggestion_type}
event:
  hook_event_name: TODO
  runtime: codex
expected:
  warning_contains:
    - TODO
"""


def _memory_gate_fixture_candidate(suggestion_id: str, suggestion_type: str) -> str:
    return """{
  "generated_from_project_memory": true,
  "requires_human_review": true,
  "source_suggestion_id": "%s",
  "memory_candidate_type": "%s",
  "events": [],
  "query": {},
  "expected": {
    "gate": "TODO",
    "decision": "TODO"
  }
}
""" % (suggestion_id, suggestion_type)


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)[:120]
