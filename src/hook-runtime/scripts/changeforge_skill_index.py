#!/usr/bin/env python3
"""Static professional skill index used by the hook runtime."""

from __future__ import annotations

from typing import Any


SKILL_INDEX = {
    "question": ("change-forge-router", "agent-execution-discipline"),
    "plan": ("change-impact-analyzer", "task-dag-planner"),
    "read": ("change-impact-analyzer", "ai-code-review-refactor"),
    "edit": ("backend-change-builder", "ai-code-review-refactor"),
    "review": ("ai-code-review-refactor", "agent-execution-discipline"),
    "repair": ("backend-change-builder", "ai-code-review-refactor"),
    "refactor": ("ai-code-review-refactor", "quality-test-gate"),
    "test": ("quality-test-gate", "ai-code-review-refactor"),
    "skill_authoring": ("change-forge-router", "quality-test-gate"),
    "hook_runtime": ("backend-change-builder", "ai-code-review-refactor"),
    "permission": ("security-privacy-gate", "delivery-release-gate"),
    "release": ("delivery-release-gate", "security-privacy-gate"),
    "compaction": ("agent-execution-discipline", "change-forge-router"),
    "subagent": ("task-dag-planner", "agent-execution-discipline"),
    "unknown": ("change-forge-router", "agent-execution-discipline"),
}

SURFACE_CAPABILITIES = {
    "hook_runtime": ["cli-daemon-interface-design", "configuration-runtime-policy"],
    "skill_authoring": ["skill-authoring-expert", "implementation-structure-design"],
    "capability_authoring": ["skill-authoring-expert", "agent-execution-discipline"],
    "data_api_contract": ["dto-schema-design", "version-compatibility", "contract-testing"],
    "security": ["secret-configuration-security"],
    "delivery": ["ci-cd", "release-rollback"],
    "documentation": ["documentation-generation"],
    "build_install_validation": ["test-strategy", "regression-testing"],
    "review": ["code-clarity-maintainability"],
    "test": ["unit-testing", "regression-testing"],
    "context_read": ["context-packaging"],
}

FOUNDATION_REFERENCES = {
    "context-packaging": "src/foundation/capabilities/context-packaging/SKILL.md",
    "task-dag-decomposition": "src/foundation/capabilities/task-dag-decomposition/SKILL.md",
    "implementation-structure-design": (
        "src/foundation/capabilities/implementation-structure-design/SKILL.md"
    ),
    "agent-execution-discipline": (
        "src/foundation/capabilities/agent-execution-discipline/SKILL.md"
    ),
    "skill-authoring-expert": "src/foundation/capabilities/skill-authoring-expert/SKILL.md",
    "cli-daemon-interface-design": (
        "src/foundation/capabilities/cli-daemon-interface-design/SKILL.md"
    ),
    "configuration-runtime-policy": (
        "src/foundation/capabilities/configuration-runtime-policy/SKILL.md"
    ),
    "dto-schema-design": "src/foundation/capabilities/dto-schema-design/SKILL.md",
    "version-compatibility": "src/foundation/capabilities/version-compatibility/SKILL.md",
    "contract-testing": "src/foundation/capabilities/contract-testing/SKILL.md",
    "test-strategy": "src/foundation/capabilities/test-strategy/SKILL.md",
    "unit-testing": "src/foundation/capabilities/unit-testing/SKILL.md",
    "regression-testing": "src/foundation/capabilities/regression-testing/SKILL.md",
    "ci-cd": "src/foundation/capabilities/ci-cd/SKILL.md",
    "release-rollback": "src/foundation/capabilities/release-rollback/SKILL.md",
    "secret-configuration-security": (
        "src/foundation/capabilities/secret-configuration-security/SKILL.md"
    ),
    "documentation-generation": (
        "src/foundation/capabilities/documentation-generation/SKILL.md"
    ),
    "code-clarity-maintainability": (
        "src/foundation/capabilities/code-clarity-maintainability/SKILL.md"
    ),
}

MISSING_SKILL_ALIASES = {
    "code-review-discipline": "ai-code-review-refactor",
    "implementation-structure-design": "foundation capability, not professional skill",
    "agent-execution-discipline": "foundation capability, not professional skill",
}


def build_active_skill_context(
    *,
    runtime: str,
    stage: str,
    surfaces: list[str],
    event_name: str,
    state: dict | None = None,
) -> dict[str, Any]:
    """Build a bounded active-skill context without loading reference bodies."""
    owner, reviewer = SKILL_INDEX.get(stage, SKILL_INDEX["unknown"])
    capabilities = _capabilities(stage, surfaces)
    references = [FOUNDATION_REFERENCES[item] for item in capabilities if item in FOUNDATION_REFERENCES]
    gates = _quality_gates(stage, surfaces)
    return {
        "runtime": runtime,
        "event": event_name,
        "stage": stage,
        "surfaces": surfaces[:8],
        "owner_skill": owner,
        "reviewer_skill": reviewer,
        "selected_capabilities": capabilities,
        "required_references": references,
        "required_quality_gates": gates,
        "next_gate": gates[0] if gates else "quality-test-gate",
        "missing_skill_aliases": _active_alias_notes(capabilities),
        "prior_stage": (state or {}).get("turn_stage", ""),
    }


def context_lines(context: dict[str, Any]) -> list[str]:
    """Render the active context as stable, line-oriented guidance."""
    lines = [
        "ChangeForge Professional Skill Injection",
        f"- stage: {context.get('stage', '')}",
        f"- owner_skill: {context.get('owner_skill', '')}",
        f"- reviewer_skill: {context.get('reviewer_skill', '')}",
        f"- surfaces: {', '.join(context.get('surfaces', []))}",
        f"- selected_capabilities: {', '.join(context.get('selected_capabilities', []))}",
        f"- required_quality_gates: {', '.join(context.get('required_quality_gates', []))}",
        "- privacy: prompt text, environment variables, secrets, and full command output are not stored",
    ]
    refs = context.get("required_references", [])
    if refs:
        lines.append(f"- required_references: {', '.join(refs[:6])}")
    aliases = context.get("missing_skill_aliases", [])
    if aliases:
        lines.append(f"- alias_notes: {', '.join(aliases)}")
    return lines


def _capabilities(stage: str, surfaces: list[str]) -> list[str]:
    values = ["implementation-structure-design", "agent-execution-discipline"]
    if stage == "plan":
        values.extend(["context-packaging", "task-dag-decomposition"])
    if stage == "subagent":
        values.extend(["task-dag-decomposition", "context-packaging"])
    if stage in {"edit", "refactor", "hook_runtime", "skill_authoring"}:
        values.extend(["code-clarity-maintainability"])
    for surface in surfaces:
        values.extend(SURFACE_CAPABILITIES.get(surface, []))
    return _unique(values)[:10]


def _quality_gates(stage: str, surfaces: list[str]) -> list[str]:
    gates = ["quality-test-gate"]
    if "data_api_contract" in surfaces:
        gates.append("data-api-contract-changer")
    if "security" in surfaces or stage == "permission":
        gates.append("security-privacy-gate")
    if "delivery" in surfaces or stage == "release":
        gates.append("delivery-release-gate")
    if "documentation" in surfaces:
        gates.append("change-documentation-gate")
    if stage in {"review", "repair"}:
        gates.append("ai-code-review-refactor")
    return _unique(gates)


def _active_alias_notes(capabilities: list[str]) -> list[str]:
    notes: list[str] = []
    for name, target in MISSING_SKILL_ALIASES.items():
        if name in capabilities:
            notes.append(f"{name} -> {target}")
    return notes


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out
