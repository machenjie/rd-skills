#!/usr/bin/env python3
"""Validate the four static Agent Profiles and platform projections."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

from validation_utils import (
    COMPLETION_STATE_MODEL,
    CORE_CONTRACTS,
    EVIDENCE_LEDGER_MODEL,
    IMPLEMENTATION_DISCIPLINE_MODEL,
    REVIEW_DISCIPLINE_MODEL,
    PROFILE_CONTRACT_MODEL,
    PROMPT_CONTRACT_MODEL,
    ROLE_CONTRACT_MODEL,
    fail_many,
    validate_ai_readability,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / PROFILE_CONTRACT_MODEL["source_path"]
ENFORCEMENT_SOURCE = ROOT / "src" / "agent-profiles" / "host-enforcement.json"
ENFORCEMENT_STATUSES = {
    "native-enforced",
    "sandbox-enforced",
    "prompt-enforced",
    "unsupported",
}
ENFORCEMENT_CAPABILITIES = {
    "tool_allowlist",
    "workspace_write_protection",
    "read_only_command_semantics",
    "external_source_read",
}
HOST_ENFORCEMENT_CAPABILITIES = {
    "profile_delivery",
    "skill_loading",
    "subagent_dispatch",
    "partial_handoff",
    "isolated_workspace",
    "utility_no_edit",
}
GENERIC_CAPABILITY_CONTRACT = REVIEW_DISCIPLINE_MODEL["generic_capability_contract"]
DECISION_CAPABILITY_FIELDS = tuple(GENERIC_CAPABILITY_CONTRACT["injected_fields"])
DECISION_CAPABILITY_STATES = set(GENERIC_CAPABILITY_CONTRACT["states"])
HOST_MODE_VALUES = {
    "diff_input_mode": ("native", "supplied-artifact", "unsupported"),
    "validation_mode": ("native-read-only", "task-no-edit", "unsupported"),
}
NATIVE_DIFF_SAFEGUARDS = ["--no-pager", "--no-ext-diff", "--no-textconv"]
ENFORCEMENT_HOSTS = {"codex", "claude", "copilot", "cline", "openai-api"}
EXTERNAL_READ_MODEL = CORE_CONTRACTS["external_read_contract"]
EXTERNAL_READ_HOST_MODES = {
    "codex": "prompt-enforced",
    "claude": "native-enforced",
    "copilot": "prompt-enforced",
    "cline": "unsupported",
    "openai-api": "unsupported",
}
OLD_NAMES = {
    "analysis-worker", "specialist-worker", "validation-agent", "independent-reviewer",
    "integration-worker", "pdd-freezer", "ddd-freezer", "sdd-contract-freezer",
    "tdd-behavior-freezer", "task-implementer", "phase-reviewer",
}


def _normalized_decision_capabilities(entry: dict[str, object]) -> dict[str, str]:
    profile_supported = entry.get("profile_delivery") in ENFORCEMENT_STATUSES - {"unsupported"}
    roles = entry.get("roles")
    roles = roles if isinstance(roles, dict) else {}

    def rendered_tools(role: str) -> set[str]:
        facts = roles.get(role)
        tools = facts.get("rendered_tools") if isinstance(facts, dict) else None
        return set(tools) if isinstance(tools, list) else set()

    diff_input_mode = entry.get("diff_input_mode")
    native_change_read = profile_supported and diff_input_mode == "native"
    change_evidence_export = profile_supported and bool(
        rendered_tools("task-agent") & {"execute", "Bash"}
    )
    supplied_change_delivery = (
        profile_supported and diff_input_mode == "supplied-artifact"
    )
    reviewer_change_consume = profile_supported and bool(
        rendered_tools("review-agent")
        & {"read", "Read", "search", "Grep", "Glob", "execute-read-only"}
    )
    validation_supported = entry.get("validation_mode") in {"native-read-only", "task-no-edit"}
    observation_supported = entry.get("utility_no_edit") in ENFORCEMENT_STATUSES - {"unsupported"}
    return {
        "bounded-source-read": "supported" if profile_supported else "unsupported",
        "workspace-mutation": "supported" if profile_supported else "unsupported",
        "non-mutating-validation": "supported" if validation_supported else "unsupported",
        "native-change-read": "supported" if native_change_read else "unsupported",
        "change-evidence-export": "supported" if change_evidence_export else "unsupported",
        "supplied-change-delivery": "supported" if supplied_change_delivery else "unsupported",
        "reviewer-change-consume": "supported" if reviewer_change_consume else "unsupported",
        "workspace-state-observation": "supported" if observation_supported else "unsupported",
    }


def _render_decision_capability_facts(capabilities: dict[str, str]) -> str:
    groups = {
        state: [
            field
            for field in DECISION_CAPABILITY_FIELDS
            if capabilities[field] == state
        ]
        for state in ("supported", "unsupported")
    }
    return (
        "Current capability facts: supported "
        + ("/".join(groups["supported"]) or "none")
        + "; unsupported "
        + ("/".join(groups["unsupported"]) or "none")
        + "."
    )
OUTPUTS = (
    ("codex", ROOT / "dist" / "codex" / "project" / ".codex" / "agents", ".toml"),
    ("claude", ROOT / "dist" / "claude" / "project" / ".claude" / "agents", ".md"),
    ("copilot", ROOT / "dist" / "copilot" / "project" / ".github" / "agents", ".agent.md"),
)
BUILT_MANIFESTS = (
    ROOT / "dist/codex/project/.agents/skills/recommended/.changeforge-build-manifest.json",
    ROOT / "dist/claude/project/.claude/skills/recommended/.changeforge-build-manifest.json",
    ROOT / "dist/copilot/project/.github/skills/recommended/.changeforge-build-manifest.json",
)


def _load_json_object(
    path: Path,
    label: str,
    errors: list[str],
) -> dict[str, object] | None:
    """Load one JSON object while keeping parse and shape failures controlled."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: invalid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}: JSON top level must be an object")
        return None
    return value


def _validate_profile_description(
    profile: dict[str, object],
    name: str,
    errors: list[str],
) -> None:
    description = profile.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{name}: description must be non-empty")
        return
    validate_ai_readability(
        description,
        f"src/agent-profiles/role-agents.json#{name}#description",
        errors,
        check_bullets=False,
    )


def _rule_group_matches(rules: list[str], required_terms: list[str]) -> list[int]:
    folded_terms = [term.casefold() for term in required_terms]
    return [
        index
        for index, rule in enumerate(rules)
        if all(term in rule.casefold() for term in folded_terms)
    ]


def _validate_instruction_rule_groups(
    *,
    role_name: str,
    contract_label: str,
    groups: list[dict[str, object]],
    rules: list[str],
    errors: list[str],
) -> bool:
    all_present = True
    for group in groups:
        required_terms = group.get("required_terms")
        rule_id = group.get("rule_id")
        if not isinstance(required_terms, list):
            continue
        matches = _rule_group_matches(rules, required_terms)
        if len(matches) != 1:
            all_present = False
            errors.append(
                f"{role_name}: {contract_label} rule {rule_id!r} must appear in "
                f"exactly one instruction bullet, found {len(matches)}"
            )
        if "exact_rule" not in group:
            continue
        exact_rule = group["exact_rule"]
        if not isinstance(exact_rule, str) or not exact_rule:
            all_present = False
            errors.append(
                f"{role_name}: {contract_label} rule {rule_id!r} has an invalid "
                "exact canonical bullet"
            )
            continue
        exact_matches = [
            index for index, rule in enumerate(rules) if rule == exact_rule
        ]
        if len(exact_matches) != 1:
            all_present = False
            errors.append(
                f"{role_name}: {contract_label} rule {rule_id!r} must equal "
                f"its exact canonical bullet once, found {len(exact_matches)}"
            )
    return all_present


def _validate_profile_instruction_contract(
    *,
    role_name: str,
    error_label: str,
    readability_label: str,
    instructions: str,
    errors: list[str],
) -> None:
    """Validate one source or decoded built Profile instruction block."""

    limits = PROFILE_CONTRACT_MODEL["instruction_rule_count"]
    maximum = limits["maximum_by_role"].get(role_name, limits["maximum"])
    rules = instructions.splitlines()
    if not limits["minimum"] <= len(rules) <= maximum or any(
        not rule.startswith("- ") for rule in rules
    ):
        errors.append(
            f"{error_label}: instructions must contain {limits['minimum']}-"
            f"{maximum} newline bullet rules"
        )
    validate_ai_readability(instructions, readability_label, errors)
    for obsolete in PROFILE_CONTRACT_MODEL["forbidden_instruction_terms"]:
        if obsolete in instructions:
            errors.append(
                f"{error_label}: instructions contain forbidden term {obsolete!r}"
            )

    capability_groups = dict(PROFILE_CONTRACT_MODEL["capability_terms"])
    capability_groups[IMPLEMENTATION_DISCIPLINE_MODEL["profile_capability_id"]] = (
        IMPLEMENTATION_DISCIPLINE_MODEL["profile_projection"]
    )
    capability_groups[REVIEW_DISCIPLINE_MODEL["profile_capability_id"]] = (
        REVIEW_DISCIPLINE_MODEL["profile_projection"]
    )
    capability_contract = PROFILE_CONTRACT_MODEL["role_capabilities"][role_name]
    required_ids = capability_contract["required_capability_ids"]
    for capability_id in required_ids:
        _validate_instruction_rule_groups(
            role_name=error_label,
            contract_label=f"capability {capability_id!r}",
            groups=capability_groups[capability_id],
            rules=rules,
            errors=errors,
        )
    for capability_id, groups in capability_groups.items():
        if capability_id in required_ids:
            continue
        if all(_rule_group_matches(rules, group["required_terms"]) for group in groups):
            errors.append(
                f"{error_label}: contains capability {capability_id!r} owned by "
                "another role"
            )

    handoff_id = capability_contract["handoff_contract"]
    _validate_instruction_rule_groups(
        role_name=error_label,
        contract_label=f"handoff {handoff_id!r}",
        groups=PROFILE_CONTRACT_MODEL["handoff_contracts"][handoff_id],
        rules=rules,
        errors=errors,
    )
    forbidden_storage_rules = {
        rule["id"]: rule for rule in EVIDENCE_LEDGER_MODEL["forbidden_storage"]
    }
    for rule_id in capability_contract["forbidden_storage_projection_ids"]:
        matches = _rule_group_matches(
            rules,
            forbidden_storage_rules[rule_id]["projection_terms"],
        )
        if len(matches) != 1:
            errors.append(
                f"{error_label}: forbidden storage projection {rule_id!r} must "
                f"appear in exactly one instruction bullet, found {len(matches)}"
            )

    completion_proof = EVIDENCE_LEDGER_MODEL["completion_proof"]["implementation"]
    for projection in completion_proof["projections"]:
        if projection["target"] != f"profile:{role_name}":
            continue
        missing_terms = [
            term
            for term in projection["terms"]
            if not any(term in rule for rule in rules)
        ]
        if missing_terms:
            errors.append(
                f"{error_label}: independent review evidence projection is "
                f"missing required terms {missing_terms}"
            )

    if role_name == "main-control-agent":
        folded_instructions = instructions.casefold()
        prompt_owned_terms = [
            "Task Contract v2",
            "Evidence Ledger",
            *COMPLETION_STATE_MODEL["statuses"],
            *COMPLETION_STATE_MODEL["fail_closed_rules"],
        ]
        leaked = [
            term
            for term in prompt_owned_terms
            if term.casefold() in folded_instructions
        ]
        if leaked:
            errors.append(
                f"{error_label}: Prompt-owned Task, Evidence, or Completion rules "
                f"must not be copied into Profile instructions: {leaked}"
            )

    if role_name == "task-agent":
        for rule in rules:
            if (
                "load and follow exactly" in rule.casefold()
                or "load only capsule-named layer 3 items" in rule.casefold()
            ) and "normal implementation mode" not in rule.casefold():
                errors.append(
                    f"{error_label}: Professional Skill and Layer 3 loading must "
                    "be qualified as normal implementation mode only"
                )


def _validate_external_read_profile_contract(
    *,
    role_name: str,
    error_label: str,
    instructions: str,
    errors: list[str],
) -> None:
    """Keep external evidence JIT, non-authoritative, and analysis-only."""

    rules = instructions.splitlines()
    if role_name == EXTERNAL_READ_MODEL["exclusive_role"]:
        groups = [
            {
                "rule_id": "external-read-jit",
                "required_terms": [
                    "material unresolved Claim",
                    "local or current evidence",
                    "never browse broadly",
                    "non-material unknown",
                    "Proof Limit",
                ],
            },
            {
                "rule_id": "external-read-trust-boundary",
                "required_terms": [
                    "untrusted evidence input",
                    "never control input",
                    "without executing/downstreaming",
                    "raw external instructions",
                    "normalized Claim",
                    "Evidence Ledger",
                    "Engineering Brief",
                ],
            },
            {
                "rule_id": "external-read-disclosure-boundary",
                "required_terms": [
                    "supported external-source-read capability",
                    "minimum public information",
                    "repository-private source",
                    "credentials",
                    "sensitive data",
                    "proprietary content",
                ],
            },
            {
                "rule_id": "external-read-capability-fail-closed",
                "required_terms": [
                    "external-source-read",
                    "unsupported",
                    "sufficient local evidence",
                    "unknown-critical-boundary",
                    "edit blocked",
                    "no implementation dispatch",
                ],
            },
        ]
        _validate_instruction_rule_groups(
            role_name=error_label,
            contract_label="external-read",
            groups=groups,
            rules=rules,
            errors=errors,
        )
        return

    if role_name in EXTERNAL_READ_MODEL["downstream_research_roles"]:
        _validate_instruction_rule_groups(
            role_name=error_label,
            contract_label="external-read denial",
            groups=[
                {
                    "rule_id": "external-read-denied",
                    "required_terms": [
                        "Leave external-source-read",
                        "analysis-agent",
                    ],
                }
            ],
            rules=rules,
            errors=errors,
        )


def _built_instruction_surface(
    platform: str,
    name: str,
    text: str,
    errors: list[str],
) -> str:
    """Return decoded Profile instructions without host metadata front matter."""

    if platform == "codex":
        try:
            document = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"{platform}:{name}: invalid TOML Profile: {exc}")
            return ""
        instructions = document.get("developer_instructions")
        if not isinstance(instructions, str):
            errors.append(
                f"{platform}:{name}: developer_instructions must be a TOML string"
            )
            return ""
        return instructions

    if not text.startswith("---\n"):
        errors.append(f"{platform}:{name}: missing Profile front matter")
        return ""
    front_matter_end = text.find("\n---\n", 4)
    if front_matter_end < 0:
        errors.append(f"{platform}:{name}: unterminated Profile front matter")
        return ""
    return text[front_matter_end + len("\n---\n") :].lstrip("\n")


def _built_instruction_block(
    platform: str,
    name: str,
    surface: str,
    errors: list[str],
) -> str:
    """Extract the leading newline-bullet block from decoded instructions."""

    lines = surface.splitlines()
    if not lines or not lines[0].startswith("- "):
        errors.append(
            f"{platform}:{name}: decoded instructions must start with Profile rules"
        )
        return ""
    end = next(
        (index for index, line in enumerate(lines) if not line.startswith("- ")),
        len(lines),
    )
    return "\n".join(lines[:end])


def _expected_built_instruction_surface(
    platform: str,
    name: str,
    profile: dict[str, object],
    hosts: dict[str, object],
) -> str | None:
    """Render the only allowed decoded instruction-section sequence."""

    instructions = profile.get("instructions")
    tools = profile.get("tools")
    if not isinstance(instructions, str) or not instructions.strip():
        return None
    if not isinstance(tools, list) or any(
        not isinstance(tool, str) or not tool for tool in tools
    ):
        return None

    sections = [instructions.strip()]
    if name == "main-control-agent":
        prompt_path = ROOT / PROMPT_CONTRACT_MODEL["path"]
        try:
            canonical_prompt = prompt_path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            return None
        sections.append(canonical_prompt)

    sections.append(f"Declared tool boundary: {', '.join(tools)}.")
    if name == "main-control-agent":
        host_entry = hosts.get(platform)
        if not isinstance(host_entry, dict):
            return None
        capability_facts = _normalized_decision_capabilities(host_entry)
        sections.append(_render_decision_capability_facts(capability_facts))
    elif name == "analysis-agent":
        host_entry = hosts.get(platform)
        if not isinstance(host_entry, dict):
            return None
        roles = host_entry.get("roles")
        if not isinstance(roles, dict):
            return None
        role_entry = roles.get("analysis-agent")
        if not isinstance(role_entry, dict):
            return None
        external_mode = role_entry.get("external_source_read")
        if not isinstance(external_mode, str):
            return None
        sections.append(
            "Current external-read mode: "
            f"external_source_read={external_mode}."
        )

    expected = "\n\n".join(sections)
    return expected if platform == "codex" else expected + "\n"


def _validate_built_instruction_surface(
    *,
    platform: str,
    name: str,
    profile: dict[str, object],
    hosts: dict[str, object],
    surface: str,
    errors: list[str],
) -> None:
    """Reject any instruction outside the canonical block and generated sections."""

    expected = _expected_built_instruction_surface(
        platform,
        name,
        profile,
        hosts,
    )
    if expected is not None and surface != expected:
        errors.append(
            f"{platform}:{name}: decoded instruction surface must equal the "
            "canonical Profile rule block followed immediately by only the known "
            "generated sections"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate source Agent Profile contracts and built projections."
    )
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="validate source contracts without requiring regenerated dist projections",
    )
    args = parser.parse_args(argv)
    errors: list[str] = []
    if not SOURCE.is_file():
        errors.append("missing src/agent-profiles/role-agents.json")
        return fail_many("validate-agent-profiles", errors)
    data = _load_json_object(SOURCE, "Agent Profile source", errors)
    if data is None:
        return fail_many("validate-agent-profiles", errors)
    profiles = data.get("profiles")
    if data.get("schema_version") != 1 or not isinstance(profiles, list):
        errors.append("Agent Profiles require schema_version 1 and a profiles list")
        return fail_many("validate-agent-profiles", errors)
    by_name = {profile.get("name"): profile for profile in profiles if isinstance(profile, dict)}
    if len(by_name) != len(profiles):
        errors.append("profiles must be objects with unique names")
    if set(by_name) != set(ROLE_CONTRACT_MODEL):
        errors.append(f"profiles must be exactly {sorted(ROLE_CONTRACT_MODEL)}")
    for name, role_contract in ROLE_CONTRACT_MODEL.items():
        profile = by_name.get(name, {})
        expected_fields = set(PROFILE_CONTRACT_MODEL["profile_fields"]) | set(
            PROFILE_CONTRACT_MODEL["optional_fields_by_role"][name]
        )
        if set(profile) != expected_fields:
            errors.append(f"{name}: fields must be exactly {sorted(expected_fields)}")
        if profile.get("sandbox") != role_contract["sandbox"]:
            errors.append(f"{name}: sandbox must match the core role contract")
        if profile.get("tools") != role_contract["tools"]:
            errors.append(f"{name}: tools must match the core role contract")
        tools = profile.get("tools") if isinstance(profile.get("tools"), list) else []
        projected_capabilities = {
            "may_dispatch": "dispatch" in tools,
            "may_edit": {"edit", "execute"} <= set(tools),
            "may_review": "execute-read-only" in tools,
        }
        for capability, projected in projected_capabilities.items():
            if projected != role_contract[capability]:
                errors.append(f"{name}: {capability} projection disagrees with core role")
        _validate_profile_description(profile, name, errors)
        if not isinstance(profile.get("instructions"), str) or not profile.get("instructions", "").strip():
            errors.append(f"{name}: instructions must be non-empty")
            continue
        instructions = profile["instructions"]
        _validate_profile_instruction_contract(
            role_name=name,
            error_label=name,
            readability_label=f"src/agent-profiles/role-agents.json#{name}",
            instructions=instructions,
            errors=errors,
        )
        _validate_external_read_profile_contract(
            role_name=name,
            error_label=name,
            instructions=instructions,
            errors=errors,
        )

    main_profile = by_name.get("main-control-agent", {})
    if main_profile.get("prompt") != PROMPT_CONTRACT_MODEL["path"]:
        errors.append("main-control-agent must load the authoritative control prompt")

    enforcement: dict = {}
    if not ENFORCEMENT_SOURCE.is_file():
        errors.append("missing src/agent-profiles/host-enforcement.json")
    else:
        loaded_enforcement = _load_json_object(
            ENFORCEMENT_SOURCE,
            "host enforcement source",
            errors,
        )
        if loaded_enforcement is not None:
            enforcement = loaded_enforcement
    hosts = enforcement.get("hosts")
    expected_enforcement_fields = {
        "schema_version",
        "source_summary",
        "status_values",
        "mode_values",
        "hosts",
    }
    if set(enforcement) != expected_enforcement_fields:
        errors.append(
            "host enforcement matrix fields must be exactly "
            f"{sorted(expected_enforcement_fields)}"
        )
    if enforcement.get("schema_version") != 4 or set(enforcement.get("status_values") or []) != ENFORCEMENT_STATUSES:
        errors.append("host enforcement matrix must use schema_version 4 and the fixed status enum")
    if enforcement.get("mode_values") != {
        field: list(values) for field, values in HOST_MODE_VALUES.items()
    }:
        errors.append("host enforcement mode_values must match the adapter contract")
    if not isinstance(hosts, dict) or set(hosts) != ENFORCEMENT_HOSTS:
        errors.append("host enforcement matrix must contain exactly the supported hosts")
        hosts = {}
    for host, host_entry in hosts.items():
        if not isinstance(host_entry, dict):
            errors.append(f"{host}: enforcement entry must be an object")
            continue
        expected_fields = HOST_ENFORCEMENT_CAPABILITIES | {
            "diff_input_mode",
            "validation_mode",
            "native_diff_safeguards",
            "roles",
        }
        if set(host_entry) != expected_fields:
            errors.append(f"{host}: host fields must be exactly {sorted(expected_fields)}")
        for capability in HOST_ENFORCEMENT_CAPABILITIES:
            if host_entry.get(capability) not in ENFORCEMENT_STATUSES:
                errors.append(f"{host}: invalid {capability} enforcement")
        if host_entry.get("diff_input_mode") not in HOST_MODE_VALUES["diff_input_mode"]:
            errors.append(f"{host}: invalid diff_input_mode")
        if host_entry.get("validation_mode") not in HOST_MODE_VALUES["validation_mode"]:
            errors.append(f"{host}: invalid validation_mode")
        expected_safeguards = (
            NATIVE_DIFF_SAFEGUARDS
            if host_entry.get("diff_input_mode") == "native"
            else []
        )
        if host_entry.get("native_diff_safeguards") != expected_safeguards:
            errors.append(f"{host}: native diff safeguards do not match adapter mode")
        if tuple(_normalized_decision_capabilities(host_entry)) != DECISION_CAPABILITY_FIELDS:
            errors.append(f"{host}: normalized decision capabilities drift from Core")
        roles = host_entry.get("roles")
        if not isinstance(roles, dict) or set(roles) != set(ROLE_CONTRACT_MODEL):
            errors.append(f"{host}: enforcement roles must be the exact four profiles")
            continue
        for role, role_entry in roles.items():
            if not isinstance(role_entry, dict):
                errors.append(f"{host}:{role}: enforcement entry must be an object")
                continue
            expected_role_fields = ENFORCEMENT_CAPABILITIES | {
                "rendered_tools",
                "limitations",
            }
            if set(role_entry) != expected_role_fields:
                errors.append(
                    f"{host}:{role}: enforcement fields must be exactly "
                    f"{sorted(expected_role_fields)}"
                )
            for capability in ENFORCEMENT_CAPABILITIES:
                if role_entry.get(capability) not in ENFORCEMENT_STATUSES:
                    errors.append(f"{host}:{role}: invalid {capability} enforcement")
            if not isinstance(role_entry.get("rendered_tools"), list):
                errors.append(f"{host}:{role}: rendered_tools must be a list")
    codex_main = hosts.get("codex", {}).get("roles", {}).get("main-control-agent", {})
    if codex_main.get("tool_allowlist") != "prompt-enforced":
        errors.append("codex:main-control-agent tool allowlist must be prompt-enforced")
    for host, expected_mode in EXTERNAL_READ_HOST_MODES.items():
        roles = hosts.get(host, {}).get("roles", {})
        analysis = roles.get("analysis-agent", {})
        if analysis.get("external_source_read") != expected_mode:
            errors.append(
                f"{host}:analysis-agent external_source_read must be {expected_mode}"
            )
        for role in set(ROLE_CONTRACT_MODEL) - {"analysis-agent"}:
            if roles.get(role, {}).get("external_source_read") != "unsupported":
                errors.append(
                    f"{host}:{role} external_source_read must be unsupported"
                )
    claude_analysis_tools = (
        hosts.get("claude", {})
        .get("roles", {})
        .get("analysis-agent", {})
        .get("rendered_tools")
    )
    if claude_analysis_tools != [
        "Skill",
        "Read",
        "Grep",
        "Glob",
        "WebSearch",
        "WebFetch",
    ]:
        errors.append(
            "claude:analysis-agent must expose only the native read and Web read tools"
        )
    copilot_analysis_tools = (
        hosts.get("copilot", {})
        .get("roles", {})
        .get("analysis-agent", {})
        .get("rendered_tools")
    )
    if copilot_analysis_tools != ["read", "search", "web"]:
        errors.append(
            "copilot:analysis-agent must expose only read, search, and web"
        )
    for host in ("claude", "copilot"):
        review = hosts.get(host, {}).get("roles", {}).get("review-agent", {})
        if review.get("read_only_command_semantics") != "unsupported":
            errors.append(f"{host}:review-agent read-only command semantics must be unsupported")
        if set(review.get("rendered_tools") or []) & {"Bash", "execute"}:
            errors.append(f"{host}:review-agent cannot receive Bash or execute")
    for host in ("cline", "openai-api"):
        entry = hosts.get(host, {})
        if any(
            entry.get(capability) != "unsupported"
            for capability in HOST_ENFORCEMENT_CAPABILITIES
        ):
            errors.append(f"{host}: all status-valued host capabilities must be unsupported")

    for platform, root, extension in (() if args.source_only else OUTPUTS):
        if not root.is_dir():
            continue
        actual = {path.name.removesuffix(extension) for path in root.glob(f"*{extension}")}
        if actual & OLD_NAMES:
            errors.append(f"{platform}: obsolete Agent Profiles remain: {sorted(actual & OLD_NAMES)}")
        if actual != set(ROLE_CONTRACT_MODEL):
            errors.append(f"{platform}: built Agent Profiles must be exactly the four roles")
        for name in ROLE_CONTRACT_MODEL:
            path = root / f"{name}{extension}"
            raw = path.read_bytes() if path.is_file() else b""
            if b"\r" in raw:
                errors.append(
                    f"{platform}:{name}: built Agent Profile must use canonical LF bytes"
                )
            text = raw.decode("utf-8")
            instruction_surface = _built_instruction_surface(
                platform, name, text, errors
            )
            _validate_built_instruction_surface(
                platform=platform,
                name=name,
                profile=by_name.get(name, {}),
                hosts=hosts,
                surface=instruction_surface,
                errors=errors,
            )
            instruction_block = _built_instruction_block(
                platform, name, instruction_surface, errors
            )
            if instruction_block:
                _validate_profile_instruction_contract(
                    role_name=name,
                    error_label=f"{platform}:{name}",
                    readability_label=f"{platform}:{name}#decoded-instructions",
                    instructions=instruction_block,
                    errors=errors,
                )
                _validate_external_read_profile_contract(
                    role_name=name,
                    error_label=f"{platform}:{name}",
                    instructions=instruction_block,
                    errors=errors,
                )
            if "Declared tool boundary" not in text:
                errors.append(f"{platform}:{name}: missing declared tool boundary")
            if name == "review-agent" and "execute-read-only" not in text:
                errors.append(f"{platform}:{name}: must preserve read-only execution intent")
            if name == "main-control-agent":
                canonical_prompt = (
                    (ROOT / PROMPT_CONTRACT_MODEL["path"])
                    .read_text(encoding="utf-8")
                    .strip()
                )
                if instruction_surface.count(canonical_prompt) != 1:
                    errors.append(
                        f"{platform}:{name}: canonical authoritative prompt must be "
                        "embedded exactly once"
                    )
            else:
                canonical_prompt = (
                    (ROOT / PROMPT_CONTRACT_MODEL["path"])
                    .read_text(encoding="utf-8")
                    .strip()
                )
                if canonical_prompt in instruction_surface:
                    errors.append(
                        f"{platform}:{name}: worker Profile must not embed the control prompt"
                    )
            if platform == "codex" and "permission_enforcement" in text:
                errors.append(f"{platform}:{name}: contains an unsupported Codex TOML field")
            if platform == "copilot" and name != "main-control-agent" and "disable-model-invocation: true" in text:
                errors.append(f"{platform}:{name}: worker Profile cannot disable subagent invocation")
            if platform == "claude" and "tools: " in text and "Skill" not in text.splitlines()[3]:
                errors.append(f"{platform}:{name}: Claude Profile must allow named Skill loading")
            if platform == "claude" and name == "review-agent":
                tools_line = next((line for line in text.splitlines() if line.startswith("tools: ")), "")
                if "Bash" in tools_line or tools_line != "tools: Skill, Read, Grep, Glob":
                    errors.append("claude:review-agent must omit Bash and use read-only artifact tools")
            if platform == "copilot" and name == "review-agent":
                tools_line = next((line for line in text.splitlines() if line.startswith("tools: ")), "")
                expected_tools_line = "tools: " + json.dumps(
                    hosts["copilot"]["roles"]["review-agent"]["rendered_tools"],
                    separators=(",", ":"),
                )
                if '"execute"' in tools_line or tools_line != expected_tools_line:
                    errors.append("copilot:review-agent must omit execute and use read/search")
            if name == "main-control-agent":
                host_entry = hosts.get(platform, {})
                capability_facts = _normalized_decision_capabilities(host_entry)
                expected_modes = _render_decision_capability_facts(capability_facts)
                if expected_modes not in text:
                    errors.append(f"{platform}:{name}: missing exact capability facts")
            elif name == "analysis-agent":
                expected_mode = (
                    hosts.get(platform, {})
                    .get("roles", {})
                    .get("analysis-agent", {})
                    .get("external_source_read")
                )
                expected_external_mode = (
                    "Current external-read mode: "
                    f"external_source_read={expected_mode}."
                )
                if expected_external_mode not in text:
                    errors.append(
                        f"{platform}:{name}: missing exact external-read mode"
                    )
                if (
                    text.count("Current external-read mode:") != 1
                    or text.count("external_source_read=") != 1
                ):
                    errors.append(
                        f"{platform}:{name}: external-read mode must be injected exactly once"
                    )
            elif any(
                marker in text
                for marker in (
                    "Current capability facts:",
                    "bounded-source-read=",
                    "workspace-mutation=",
                    "native-change-read=",
                    "supplied-change-delivery=",
                    "reviewer-change-consume=",
                    "Current external-read mode:",
                    "external_source_read=",
                )
            ):
                errors.append(f"{platform}:{name}: worker Profile must not receive control capability facts")

    if ENFORCEMENT_SOURCE.is_file():
        expected_digest = hashlib.sha256(ENFORCEMENT_SOURCE.read_bytes()).hexdigest()
        manifests = () if args.source_only else BUILT_MANIFESTS
        for manifest_path in manifests:
            if not manifest_path.is_file():
                continue
            manifest = _load_json_object(
                manifest_path,
                f"{manifest_path}: build manifest",
                errors,
            )
            if manifest is None:
                continue
            if manifest.get("agent_profile_enforcement") != hosts:
                errors.append(f"{manifest_path.relative_to(ROOT)}: stale enforcement matrix")
            source = manifest.get("agent_profile_enforcement_source")
            if not isinstance(source, dict) or source.get("sha256") != expected_digest:
                errors.append(f"{manifest_path.relative_to(ROOT)}: stale enforcement source digest")
    if errors:
        return fail_many("validate-agent-profiles", errors)
    print("validate-agent-profiles: four static profiles and platform projections are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
