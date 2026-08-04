#!/usr/bin/env python3
"""Validate focused Domain Layer 3 Skills."""

from __future__ import annotations

from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    ValidationProblem,
    domain_registry_contract_errors,
    empty_markdown_headings,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    reference_contracts,
    validate_ai_readability,
    validate_ai_markdown_format,
    validate_required_sections,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "src" / "domain-extensions"
REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"
SECTIONS = (
    "Role", "When To Use", "Do Not Use", "Required Inputs",
    "Professional Decision Rules", "High-Value Gotchas", "Execution Checklist",
    "Stop / Escalation Conditions", "Output Contract", "Targeted References",
)
FORBIDDEN = (
    "task context compiler", "runtime dispatch bridge", "private evidence ledger",
    "runtime evidence ledger", "hidden evidence ledger",
    "runtime identity", "runtime digest", "hidden pack", ".changeforge-packs",
    "phase artifact", "finding id",
)
DOMAIN_NEIGHBOR_ANTI_MARKERS = {
    "ai-product-extension": ("static algorithm", "ordinary search", "model decision"),
    "bigdata-product-extension": ("distributed pipeline", "replay"),
    "iot-embedded-extension": ("device", "firmware"),
    "low-level-systems-extension": ("native", "abi", "os", "resource boundary"),
    "payment-trading-extension": ("price", "ordinary order", "fund", "execution state"),
    "web3-product-extension": ("hash", "signature", "chain", "custody"),
}


def _section(body: str, heading: str) -> str:
    marker = f"## {heading}"
    start = body.find(marker)
    if start < 0:
        return ""
    content_start = start + len(marker)
    end = body.find("\n## ", content_start)
    return body[content_start:] if end < 0 else body[content_start:end]


def _neighbor_anti_errors(
    entry: dict, body: str, contracts: list[dict[str, str]], context: str
) -> list[str]:
    name = entry.get("name")
    markers = DOMAIN_NEIGHBOR_ANTI_MARKERS.get(str(name), ())
    anti_signals = " ".join(
        value
        for value in (entry.get("anti_trigger_signals") or [])
        if isinstance(value, str)
    ).casefold()
    do_not_use = _section(body, "Do Not Use").casefold()
    checklist = next(
        (
            contract
            for contract in contracts
            if contract.get("path") == "references/checklist.md"
        ),
        None,
    )
    checklist_skip = (
        str(checklist.get("do_not_load_when", "")).casefold()
        if isinstance(checklist, dict)
        else ""
    )
    errors: list[str] = []
    for marker in markers:
        for surface, text in (
            ("registry anti_trigger_signals", anti_signals),
            ("root Do Not Use", do_not_use),
            ("checklist do_not_load_when", checklist_skip),
        ):
            if marker not in text:
                errors.append(
                    f"{context}: {surface} must preserve neighboring anti-trigger marker {marker!r}"
                )
    return errors


def main() -> int:
    errors: list[str] = []
    try:
        data = load_yaml_file(REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return fail_many("validate-domain-extensions", errors)
    entries = data.get("domain_skills") if isinstance(data, dict) else None
    errors.extend(domain_registry_contract_errors(data))
    if not isinstance(entries, list):
        errors.append("domain-skills.yaml:domain_skills must be a list")
        return fail_many("validate-domain-extensions", errors)
    if len(entries) != EXPECTED_DOMAIN_EXTENSION_COUNT:
        errors.append(f"expected {EXPECTED_DOMAIN_EXTENSION_COUNT} Domain Skills, found {len(entries)}")
    registered: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name, path_value = entry.get("name"), entry.get("path")
        if not isinstance(name, str) or not isinstance(path_value, str):
            continue
        registered.add(name)
        skill_file = ROOT / path_value / "SKILL.md"
        context = str(skill_file.relative_to(ROOT))
        try:
            metadata, _raw, body = parse_frontmatter(skill_file)
        except (ValidationProblem, OSError) as exc:
            errors.append(str(exc).replace(str(ROOT) + "/", ""))
            continue
        if set(metadata) != {"name", "description"}:
            errors.append(f"{context}: frontmatter must contain only name and description")
        if metadata.get("name") != name:
            errors.append(f"{context}: name must match registry")
        description = metadata.get("description")
        if isinstance(description, str):
            validate_ai_readability(
                description,
                f"{context}#description",
                errors,
                check_bullets=False,
            )
        validate_required_sections(body, SECTIONS, context, errors, require_order=True)
        for line_number, _level, title in empty_markdown_headings(body):
            errors.append(f"{context}: empty heading '{title}' at line {line_number}")
        validate_ai_markdown_format(body, context, errors)
        if len(body.splitlines()) > 120:
            errors.append(f"{context}: root Domain Skill exceeds 120 lines")
        folded = body.casefold()
        for term in FORBIDDEN:
            if term in folded:
                errors.append(f"{context}: contains obsolete mechanism {term!r}")
        if "focused layer 3 domain skill" not in folded:
            errors.append(f"{context}: Role must identify a focused Layer 3 Domain boundary")
        role_section = _section(body, "Role")
        for role in entry.get("role_support") or []:
            if f"`{role}`" not in role_section:
                errors.append(f"{context}: Role must name supported profile {role}")
        try:
            contracts = reference_contracts(
                entry.get("reference_index"),
                f"{context}.reference_index",
                owner=name,
            )
        except ValidationProblem as exc:
            errors.append(str(exc))
            contracts = []
        for contract in contracts:
            reference = contract["path"]
            if not (skill_file.parent / reference).is_file():
                errors.append(f"{context}: missing targeted reference {reference}")
        errors.extend(_neighbor_anti_errors(entry, body, contracts, context))
    actual = {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if actual != registered:
        errors.append(f"Domain Skill directory/registry mismatch: {sorted(actual ^ registered)}")
    if errors:
        return fail_many("validate-domain-extensions", errors)
    print(f"validate-domain-extensions: validated {len(registered)} focused Domain Skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
