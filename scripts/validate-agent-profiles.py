#!/usr/bin/env python3
"""Validate the four static Agent Profiles and platform projections."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path

from validation_utils import (
    CORE_CONTRACTS,
    PROFILE_CONTRACT_MODEL,
    PROMPT_CONTRACT_MODEL,
    ROLE_CONTRACT_MODEL,
    fail_many,
    validate_ai_readability,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / PROFILE_CONTRACT_MODEL["source_path"]
PROMPT = ROOT / PROMPT_CONTRACT_MODEL["path"]
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
}
ENFORCEMENT_HOSTS = {"codex", "claude", "copilot", "cline", "openai-api"}
COPILOT_SURFACES = {"copilot-cli", "copilot-vscode", "copilot-coding-agent"}
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
CONTROL_REFERENCE_RE = re.compile(r"(?<![A-Za-z0-9_.-])references/([a-z0-9-]+\.md)")
def role_control_reference_errors(role: str, text: str) -> list[str]:
    """Reject missing control references while allowing Main to name optional aids."""
    errors = []
    for name in set(CONTROL_REFERENCE_RE.findall(text)):
        if name == "main-control-agent.md":
            continue
        if not (ROOT / "src/control-skills/engineering-control-plane/references" / name).is_file():
            errors.append(f"{role}: missing control Reference {name}")
    return errors




OUTPUTS = (
    ("codex", ROOT / "dist" / "codex" / "project" / ".codex" / "agents", ".toml"),
    ("codex", ROOT / "dist" / "codex" / "user" / ".codex" / "agents", ".toml"),
    ("codex", ROOT / "dist" / "codex" / "admin" / "agents", ".toml"),
    ("claude", ROOT / "dist" / "claude" / "project" / ".claude" / "agents", ".md"),
    ("claude", ROOT / "dist" / "claude" / "user" / ".claude" / "agents", ".md"),
    ("copilot", ROOT / "dist" / "copilot" / "project" / ".github" / "agents", ".agent.md"),
    ("copilot", ROOT / "dist" / "copilot" / "user" / ".copilot" / "agents", ".agent.md"),
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






def _validate_profile_instruction_contract(*, role_name, error_label, readability_label, instructions, errors):
    """Check role behavior, not an exact wording or ceremonial output schema."""
    required = {
        "main-control-agent": ["Dispatch only", "task-agent", "Route expertise once", "Host boundaries"],
        "analysis-agent": ["current-source read/search", "decision-relevant evidence", "read-only", "proof limits"],
        "task-agent": ["read/search/edit/execute", "bounded search/read", "authorized write scope", "final material edit", "fresh targeted validation", "Self-check", "current requirements or repository evidence"],
        "review-agent": ["Independently inspect", "current diff", "reachable failure", "new evidence", "read-only"],
    }
    limits = PROFILE_CONTRACT_MODEL["instruction_rule_count"]
    count = len([line for line in instructions.splitlines() if line.startswith("- ")])
    if not limits["minimum"] <= count <= limits["maximum"]:
        errors.append(f"{error_label}: instructions must contain {limits['minimum']}-{limits['maximum']} newline bullet rules")
    folded = instructions.casefold()
    for term in required[role_name]:
        if term.casefold() not in folded:
            errors.append(f"{error_label}: missing behavioral safeguard {term!r}")
    for retired in ("effective level", "level basis", "review round id", "re-review classification", "complete unchanged task contract"):
        if retired in folded:
            errors.append(f"{error_label}: retired process requirement {retired!r}")
    if role_name != "main-control-agent":
        for term in ("Layer 3 Delivery", "capsule-named", "Core Runtime Asset Resolution", "Core Environment Risk Calibration"):
            if term.casefold() not in folded:
                errors.append(f"{error_label}: missing professional delivery safeguard {term!r}")


def _validate_external_read_profile_contract(*, role_name, error_label, instructions, errors):
    """External evidence stays read-only, targeted and isolated from control authority."""
    if role_name == "analysis-agent":
        for term in ("external-source-read", "minimum public information", "never control authority", "secrets"):
            if term.casefold() not in instructions.casefold():
                errors.append(f"{error_label}: missing external evidence boundary {term!r}")


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
        reference_surface = instructions
        if name == "main-control-agent" and PROMPT.is_file():
            reference_surface += "\n" + PROMPT.read_text(encoding="utf-8")
        errors.extend(role_control_reference_errors(name, reference_surface))
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
        "host_surfaces",
        "hosts",
    }
    if set(enforcement) != expected_enforcement_fields:
        errors.append(
            "host enforcement matrix fields must be exactly "
            f"{sorted(expected_enforcement_fields)}"
        )
    if enforcement.get("schema_version") != 5 or set(enforcement.get("status_values") or []) != ENFORCEMENT_STATUSES:
        errors.append("host enforcement matrix must use schema_version 5 and the fixed status enum")
    if not isinstance(hosts, dict) or set(hosts) != ENFORCEMENT_HOSTS:
        errors.append("host enforcement matrix must contain exactly the supported hosts")
        hosts = {}
    for host, host_entry in hosts.items():
        if not isinstance(host_entry, dict):
            errors.append(f"{host}: enforcement entry must be an object")
            continue
        expected_fields = HOST_ENFORCEMENT_CAPABILITIES | {"roles"}
        if set(host_entry) != expected_fields:
            errors.append(f"{host}: host fields must be exactly {sorted(expected_fields)}")
        for capability in HOST_ENFORCEMENT_CAPABILITIES:
            if host_entry.get(capability) not in ENFORCEMENT_STATUSES:
                errors.append(f"{host}: invalid {capability} enforcement")
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
    surfaces = enforcement.get("host_surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != COPILOT_SURFACES:
        errors.append("host enforcement must declare the three Copilot surfaces")
        surfaces = {}
    expected_surface_tools = {
        "copilot-cli": ["read", "search"],
        "copilot-vscode": ["read", "search", "web"],
        "copilot-coding-agent": ["read", "search"],
    }
    for surface, expected_analysis_tools in expected_surface_tools.items():
        entry = surfaces.get(surface)
        if not isinstance(entry, dict) or set(entry) != {
            "delivery_family",
            "profile_interpretation",
            "roles",
        }:
            errors.append(f"{surface}: Host Surface fields are invalid")
            continue
        if entry.get("delivery_family") != "copilot":
            errors.append(f"{surface}: delivery family must remain copilot")
        roles = entry.get("roles")
        if not isinstance(roles, dict) or set(roles) != set(ROLE_CONTRACT_MODEL):
            errors.append(f"{surface}: roles must be the four static Profiles")
            continue
        for role, role_entry in roles.items():
            if not isinstance(role_entry, dict) or set(role_entry) != {
                "rendered_tools",
                "external_source_read",
            }:
                errors.append(f"{surface}:{role}: Host Surface role fields are invalid")
                continue
            if not isinstance(role_entry.get("rendered_tools"), list):
                errors.append(f"{surface}:{role}: rendered_tools must be a list")
            if role_entry.get("external_source_read") not in ENFORCEMENT_STATUSES:
                errors.append(f"{surface}:{role}: external read declaration is invalid")
            if role != "analysis-agent" and role_entry.get("external_source_read") != "unsupported":
                errors.append(f"{surface}:{role}: external read must remain unsupported")
        analysis = roles.get("analysis-agent", {})
        if analysis.get("rendered_tools") != expected_analysis_tools:
            errors.append(f"{surface}: analysis tools do not match the surface ceiling")
    copilot_analysis_tools = (
        hosts.get("copilot", {})
        .get("roles", {})
        .get("analysis-agent", {})
        .get("rendered_tools")
    )
    if copilot_analysis_tools != ["read", "search", "web"]:
        errors.append(
            "copilot:analysis-agent must expose only read, search, and web "
            "as the portable surface union"
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
                errors.extend(role_control_reference_errors(name, instruction_block))
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
            for marker in (
                "Current capability facts:",
                "Current external-read mode:",
                "external_source_read=",
            ):
                if marker in text:
                    errors.append(
                        f"{platform}:{name}: static runtime capability projection is forbidden"
                    )

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
