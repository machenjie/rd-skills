"""Human-approved Project Memory candidate promotion helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


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
    if write:
        output.parent.mkdir(parents=True, exist_ok=True)
        selected_target = _canonical_target(target or str(suggestion.get("promotion_target", "")))
        output.write_text(render_candidate(suggestion, selected_target), encoding="utf-8")
    return output


def _canonical_target(target: str) -> str:
    normalized = str(target or "").strip().replace("\\", "/").strip("/")
    return PROMOTION_TARGET_ALIASES.get(normalized, normalized)


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
