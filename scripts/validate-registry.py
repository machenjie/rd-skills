#!/usr/bin/env python3
"""Validate the four hookless rd-skills Skill registries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from validation_utils import (
    CORE_CONTRACTS,
    EXPECTED_CONTROL_SKILL_COUNT,
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    REGISTRY_SCHEMA_VERSIONS,
    ROLE_CONTRACT_MODEL,
    ValidationProblem,
    domain_modifier_routing_authority,
    fail_many,
    domain_registry_contract_errors,
    foundation_content_class_errors,
    foundation_ownership_errors,
    foundation_registry_field_errors,
    layer3_selector_authority,
    load_yaml_file,
    parse_frontmatter,
    path_is_within,
    professional_automatic_routing_contract_errors,
    professional_review_skill_ids,
    reference_contract_has_owner_anchor,
    reference_context_admissibility_authority,
    reference_contracts,
    reference_type_for_path,
    required_expertise_tag_errors,
    role_contract_map_errors,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
SPECS = {
    "control-skills.yaml": (
        "changeforge.control_skills",
        "control_skills",
        ROOT / "src" / "control-skills",
        EXPECTED_CONTROL_SKILL_COUNT,
        REGISTRY_SCHEMA_VERSIONS["control"],
    ),
    "professional-skills.yaml": (
        "changeforge.professional_skills",
        "professional_skills",
        ROOT / "src" / "professional-skills",
        EXPECTED_PROFESSIONAL_SKILL_COUNT,
        REGISTRY_SCHEMA_VERSIONS["professional"],
    ),
    "foundation-skills.yaml": (
        "changeforge.foundation_skills",
        "foundation_skills",
        ROOT / "src" / "foundation" / "capabilities",
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        REGISTRY_SCHEMA_VERSIONS["foundation"],
    ),
    "domain-skills.yaml": (
        "changeforge.domain_skills",
        "domain_skills",
        ROOT / "src" / "domain-extensions",
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        REGISTRY_SCHEMA_VERSIONS["domain"],
    ),
}
REQUIRED_FIELDS = (
    "name",
    "path",
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
    "reference_index",
)
ROLES = set(ROLE_CONTRACT_MODEL)
ROLE_IMPOSSIBLE_INPUT_PHRASES = {
    "analysis-agent": (
        "actual diff",
        "all changed paths",
        "material edit marker",
        "post edit validation",
        "post-edit validation",
        "validation evidence and freshness",
    ),
    "task-agent": ("bounded architecture artifact", "decision criteria and supporting source evidence"),
    "review-agent": ("accepted task capsule", "accepted integration task capsule"),
}
OLD_REGISTRIES = (
    "skills.yaml",
    "capabilities.yaml",
    "domain-extensions.yaml",
    "specialist-packs.yaml",
    "review-packs.yaml",
    "routing-rules.yaml",
    "stage-model.yaml",
)
FORBIDDEN_FIELDS = {
    "consumer_role",
    "consumer_roles",
    "stage",
    "allowed_actions",
    "forbidden_actions",
    "handoff_to",
    "review_pair",
    "parallel_safety",
    "context_budget",
    "runtime_role",
    "digest",
    "runtime_identity",
}


def main() -> int:
    errors: list[str] = []
    for name in OLD_REGISTRIES:
        if (REGISTRY_DIR / name).exists():
            errors.append(f"obsolete registry remains: src/registry/{name}")
    if (ROOT / "registry" / "toolbox.yaml").exists() or (REGISTRY_DIR / "toolbox.yaml").exists():
        errors.append("toolbox registry is forbidden")

    loaded: dict[str, list[dict[str, Any]]] = {}
    for file_name, (
        kind,
        key,
        source_root,
        expected_count,
        expected_schema_version,
    ) in SPECS.items():
        entries = _validate_registry(
            file_name,
            kind,
            key,
            source_root,
            expected_count,
            expected_schema_version,
            errors,
        )
        loaded[key] = entries
        if file_name == "professional-skills.yaml":
            errors.extend(
                professional_automatic_routing_contract_errors(
                    load_yaml_file(REGISTRY_DIR / file_name),
                    file_name,
                )
            )

    layer3_names = _names(loaded.get("foundation_skills", [])) | _names(loaded.get("domain_skills", []))
    for index, entry in enumerate(loaded.get("professional_skills", [])):
        context = f"professional-skills.yaml:professional_skills[{index}]"
        candidates = _string_list(entry.get("layer3_candidates"), f"{context}.layer3_candidates", errors)
        if len(candidates) != len(set(candidates)):
            errors.append(f"{context}: duplicate Layer 3 candidate")
        for name in candidates:
            if name not in layer3_names:
                errors.append(f"{context}: unknown Layer 3 candidate {name!r}")
        if not isinstance(entry.get("task_routable"), bool):
            errors.append(f"{context}: task_routable must be boolean")

    try:
        covered_review_skills = professional_review_skill_ids(
            loaded.get("professional_skills", []),
            CORE_CONTRACTS["review_discipline_contract"]["professional_risk_matrix"],
        )
    except ValidationProblem as exc:
        errors.append(str(exc))
    else:
        if not covered_review_skills:
            errors.append(
                "professional review risk matrix selector must cover at least one Skill"
            )

    for index, entry in enumerate(loaded.get("foundation_skills", [])):
        context = f"foundation-skills.yaml:foundation_skills[{index}]"
        errors.extend(foundation_registry_field_errors(entry, context))
        errors.extend(foundation_content_class_errors(entry, context))
        if not isinstance(entry.get("group"), str) or not entry.get("group", "").strip():
            errors.append(f"{context}: group must be a non-empty string")
    errors.extend(
        foundation_ownership_errors(
            loaded.get("foundation_skills", []),
            loaded.get("professional_skills", []),
        )
    )
    try:
        reference_context_admissibility_authority(
            load_yaml_file(REGISTRY_DIR / "professional-skills.yaml"),
            load_yaml_file(REGISTRY_DIR / "foundation-skills.yaml"),
            load_yaml_file(REGISTRY_DIR / "domain-skills.yaml"),
            context="registry Reference context admissibility",
        )
    except ValidationProblem as exc:
        errors.append(str(exc))
    try:
        layer3_selector_authority(
            load_yaml_file(REGISTRY_DIR / "foundation-skills.yaml"),
            load_yaml_file(REGISTRY_DIR / "professional-skills.yaml"),
            load_yaml_file(REGISTRY_DIR / "domain-skills.yaml"),
            context="registry Layer 3 selector authority",
        )
    except ValidationProblem as exc:
        errors.append(str(exc))
    try:
        domain_modifier_routing_authority(
            load_yaml_file(REGISTRY_DIR / "domain-skills.yaml"),
            load_yaml_file(REGISTRY_DIR / "professional-skills.yaml"),
        )
    except ValidationProblem as exc:
        errors.append(str(exc))

    if errors:
        return fail_many("validate-registry", errors)
    print("validate-registry: three-layer Skill registries and references are valid.")
    return 0


def _validate_registry(
    file_name: str,
    kind: str,
    key: str,
    source_root: Path,
    expected_count: int,
    expected_schema_version: int,
    errors: list[str],
) -> list[dict[str, Any]]:
    path = REGISTRY_DIR / file_name
    if not path.is_file():
        errors.append(f"missing src/registry/{file_name}")
        return []
    try:
        data = load_yaml_file(path)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return []
    if not isinstance(data, dict):
        errors.append(f"{file_name}: must be a mapping")
        return []
    if (
        type(data.get("schema_version")) is not int
        or data.get("schema_version") != expected_schema_version
        or data.get("kind") != kind
    ):
        errors.append(
            f"{file_name}: expected schema_version {expected_schema_version} "
            f"and kind {kind}"
        )
    if key == "domain_skills":
        errors.extend(domain_registry_contract_errors(data, file_name))
    entries = data.get(key)
    if not isinstance(entries, list):
        errors.append(f"{file_name}:{key} must be a list")
        return []
    if len(entries) != expected_count:
        errors.append(f"{file_name}:{key} expected {expected_count} entries, found {len(entries)}")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        context = f"{file_name}:{key}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{context}: must be a mapping")
            continue
        normalized.append(entry)
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{context}: missing {field}")
        forbidden = FORBIDDEN_FIELDS & set(entry)
        if forbidden:
            errors.append(f"{context}: forbidden runtime fields {sorted(forbidden)}")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{context}: name must be a non-empty string")
            continue
        if name in seen:
            errors.append(f"{context}: duplicate name {name!r}")
        seen.add(name)
        roles = _string_list(entry.get("role_support"), f"{context}.role_support", errors)
        if not roles or not set(roles) <= ROLES:
            errors.append(f"{context}: role_support must use the four static profiles")
        if key == "control_skills" and roles != ["main-control-agent"]:
            errors.append(f"{context}: control Skill must support only main-control-agent")
        if key != "control_skills" and "main-control-agent" in roles:
            errors.append(f"{context}: non-control Skill cannot support main-control-agent")
        if key != "control_skills":
            errors.extend(
                required_expertise_tag_errors(
                    entry.get("required_expertise_tags"),
                    context,
                    layer={
                        "professional_skills": "professional",
                        "foundation_skills": "foundation",
                        "domain_skills": "domain",
                    }[key],
                    skill_name=name,
                    foundation_group=entry.get("group"),
                )
            )
        common_inputs = _string_list(
            entry.get("required_inputs"), f"{context}.required_inputs", errors
        )
        if key == "professional_skills" and len(roles) > 1:
            by_role = entry.get("required_inputs_by_role")
            errors.extend(role_contract_map_errors(by_role, roles, f"{context}.required_inputs_by_role"))
            errors.extend(
                role_contract_map_errors(
                    entry.get("output_contract_by_role"),
                    roles,
                    f"{context}.output_contract_by_role",
                )
            )
            if isinstance(by_role, dict):
                for role in roles:
                    values = _string_list(
                        by_role.get(role),
                        f"{context}.required_inputs_by_role.{role}",
                        errors,
                    )
                    if not values:
                        errors.append(
                            f"{context}.required_inputs_by_role.{role}: must be non-empty"
                        )
                    _reject_impossible_role_inputs(
                        [*common_inputs, *values], role, context, errors
                    )
        elif key == "professional_skills":
            errors.extend(role_contract_map_errors(entry.get("required_inputs_by_role"), roles, f"{context}.required_inputs_by_role"))
            errors.extend(role_contract_map_errors(entry.get("output_contract_by_role"), roles, f"{context}.output_contract_by_role"))
        registry_fields = (
            "trigger_signals",
            "anti_trigger_signals",
            "required_inputs",
            "output_contract",
            "escalation_signals",
        )
        if key == "domain_skills":
            registry_fields = (*registry_fields, "boundary_signals")
        for field in registry_fields:
            values = _string_list(entry.get(field), f"{context}.{field}", errors)
            if not values:
                errors.append(f"{context}.{field}: must be non-empty")
        try:
            references = reference_contracts(
                entry.get("reference_index"),
                f"{context}.reference_index",
                owner=name,
            )
        except ValidationProblem as exc:
            errors.append(str(exc))
            references = []
        if key != "control_skills":
            supported_roles = set(roles)
            for reference in references:
                consumers = set(reference["required_by"])
                if not consumers <= supported_roles:
                    errors.append(
                        f"{context}.reference_index: {reference['path']!r} required_by "
                        f"{sorted(consumers)} exceeds owner role_support {sorted(supported_roles)}"
                    )
        if key == "foundation_skills":
            seen_load_conditions: dict[str, str] = {}
            for reference in references:
                normalized_load = " ".join(
                    re.findall(r"[a-z0-9]+", reference["load_when"].casefold())
                )
                previous = seen_load_conditions.get(normalized_load)
                if previous is not None:
                    errors.append(
                        f"{context}.reference_index: {reference['path']!r} and "
                        f"{previous!r} must not use equivalent load conditions"
                    )
                else:
                    seen_load_conditions[normalized_load] = reference["path"]
        source_value = entry.get("path")
        if not isinstance(source_value, str):
            errors.append(f"{context}: path must be a string")
            continue
        source = (ROOT / source_value).resolve()
        if not path_is_within(source_root, source) or not (source / "SKILL.md").is_file():
            errors.append(f"{context}: invalid source path {source_value!r}")
            continue
        try:
            metadata, _raw, body = parse_frontmatter(source / "SKILL.md")
        except ValidationProblem as exc:
            errors.append(str(exc).replace(str(ROOT) + "/", ""))
            continue
        if metadata.get("name") != name:
            errors.append(f"{context}: name does not match {source_value}/SKILL.md")
        for reference in references:
            reference_path = reference["path"]
            expected_type = reference_type_for_path(reference_path)
            if reference["type"] != expected_type:
                errors.append(
                    f"{context}.reference_index: {reference_path!r} must use type "
                    f"{expected_type!r}, found {reference['type']!r}"
                )
            candidate = (source / reference_path).resolve()
            if not path_is_within(source, candidate) or not candidate.is_file():
                errors.append(f"{context}: missing reference {reference_path!r}")
                continue
            if key == "foundation_skills":
                owner_context_parts = [name, body]
                for field in (
                    "trigger_signals",
                    "anti_trigger_signals",
                    "required_inputs",
                    "output_contract",
                    "escalation_signals",
                ):
                    value = entry.get(field)
                    if isinstance(value, list):
                        owner_context_parts.extend(
                            item for item in value if isinstance(item, str)
                        )
                try:
                    owner_context_parts.append(candidate.read_text(encoding="utf-8"))
                except (OSError, UnicodeError):
                    pass
                if not reference_contract_has_owner_anchor(
                    reference,
                    name,
                    "\n".join(owner_context_parts),
                ):
                    errors.append(
                        f"{context}.reference_index: {reference_path!r} JIT conditions "
                        "do not anchor to the Foundation owner or Reference subject"
                    )
    return normalized


def _string_list(value: object, context: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{context}: must be a list")
        return []
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{context}: entries must be non-empty strings")
            continue
        values.append(item.strip())
    return values


def _names(entries: list[dict[str, Any]]) -> set[str]:
    return {str(entry.get("name")) for entry in entries if isinstance(entry.get("name"), str)}


def _reject_impossible_role_inputs(
    values: list[str], role: str, context: str, errors: list[str]
) -> None:
    forbidden = ROLE_IMPOSSIBLE_INPUT_PHRASES.get(role, ())
    for value in values:
        folded = value.casefold()
        for phrase in forbidden:
            if phrase in folded:
                errors.append(
                    f"{context}.required_inputs_by_role.{role}: input {value!r} "
                    f"requires an artifact unavailable to {role}"
                )


if __name__ == "__main__":
    raise SystemExit(main())
