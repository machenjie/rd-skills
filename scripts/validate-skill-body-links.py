#!/usr/bin/env python3
"""Validate authored skill body links against ChangeForge registries."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Callable

from validation_utils import (
    NAME_RE,
    ValidationProblem,
    extract_section_body,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    registry_items,
    relpath,
)


ROOT = Path(__file__).resolve().parents[1]
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
REGISTRY_DIR = ROOT / "src" / "registry"
SKILLS_REGISTRY = REGISTRY_DIR / "skills.yaml"
CAPABILITIES_REGISTRY = REGISTRY_DIR / "capabilities.yaml"
DOMAIN_EXTENSIONS_REGISTRY = REGISTRY_DIR / "domain-extensions.yaml"
ROUTING_RULES_REGISTRY = REGISTRY_DIR / "routing-rules.yaml"
ROUTER_SKILL = PROFESSIONAL_SKILLS_DIR / "change-forge-router" / "SKILL.md"

LIST_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
LABEL_RE = re.compile(r"^[A-Z][A-Za-z0-9 ,/+.-]+:\s*$")
ROUTER_QUALITY_GATES_RE = re.compile(
    r"(?ms)^## 10\. Quality Gates\s*\n(?P<body>.*?)(?=^## 11\. Next Actions\s*$)"
)
ROUTER_RISK_TRIGGER_RE = re.compile(r"Risk triggers include (?P<triggers>.+?)\.")

EXTERNAL_TERM_ALLOWLIST = {
    "OAuth 2.0",
    "PCI DSS",
    "RFC 7807",
    "OpenAPI",
    "A/B",
    "at-least-once",
    "at-most-once",
    "exactly-once",
    "read-your-writes",
    "pt-online-schema-change",
    "copy-and-swap",
    "soft-delete",
    "blue-green",
    "dead-letter",
}


@dataclass(frozen=True)
class RegistryNames:
    skills: set[str]
    capabilities: set[str]
    extensions: set[str]
    quality_gates: set[str]
    risk_triggers: set[str]

    @property
    def all_body_links(self) -> set[str]:
        return (
            self.skills
            | self.capabilities
            | self.extensions
            | self.quality_gates
            | self.risk_triggers
        )

    @property
    def all_skill_entities(self) -> set[str]:
        return self.skills | self.capabilities | self.extensions


def _registry_names_from_entries(entries: list[object]) -> set[str]:
    names: set[str] = set()
    for entry in entries:
        if isinstance(entry, str) and entry.strip():
            names.add(entry.strip())
        elif isinstance(entry, dict):
            name = entry.get("name")
            if isinstance(name, str) and name.strip():
                names.add(name.strip())
    return names


def _string_list(value: object, context: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list):
        errors.append(f"{context}: must be a list")
        return set()

    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{context}[{index}]: must be a non-empty string")
            continue
        names.add(item.strip())
    return names


def load_registry_names() -> tuple[RegistryNames, list[str]]:
    errors: list[str] = []

    registry_data: dict[Path, object] = {}
    for path in (
        SKILLS_REGISTRY,
        CAPABILITIES_REGISTRY,
        DOMAIN_EXTENSIONS_REGISTRY,
        ROUTING_RULES_REGISTRY,
    ):
        if not path.is_file():
            errors.append(f"missing registry file: {relpath(ROOT, path)}")
            registry_data[path] = {}
            continue
        try:
            registry_data[path] = load_yaml_file(path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            registry_data[path] = {}

    skills = _registry_names_from_entries(
        registry_items(registry_data[SKILLS_REGISTRY], "skills", SKILLS_REGISTRY, errors)
    )
    capabilities = _registry_names_from_entries(
        registry_items(
            registry_data[CAPABILITIES_REGISTRY],
            "capabilities",
            CAPABILITIES_REGISTRY,
            errors,
        )
    )
    extensions = _registry_names_from_entries(
        registry_items(
            registry_data[DOMAIN_EXTENSIONS_REGISTRY],
            "domain_extensions",
            DOMAIN_EXTENSIONS_REGISTRY,
            errors,
        )
    )

    routing_rules = registry_data[ROUTING_RULES_REGISTRY]
    if not isinstance(routing_rules, dict):
        errors.append(f"{relpath(ROOT, ROUTING_RULES_REGISTRY)}: registry must be a mapping")
        routing_rules = {}

    quality_gates = _string_list(
        routing_rules.get("quality_gates"),
        "routing-rules.yaml:quality_gates",
        errors,
    )
    risk_triggers = _string_list(
        routing_rules.get("risk_escalation_triggers"),
        "routing-rules.yaml:risk_escalation_triggers",
        errors,
    )

    return (
        RegistryNames(
            skills=skills,
            capabilities=capabilities,
            extensions=extensions,
            quality_gates=quality_gates,
            risk_triggers=risk_triggers,
        ),
        errors,
    )


def _without_fenced_code(markdown: str) -> list[str]:
    lines: list[str] = []
    in_fence = False
    fence_marker: str | None = None

    for line in markdown.splitlines():
        stripped = line.strip()
        fence_match = re.match(r"^(```+|~~~+)", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[:3]
            elif fence_marker and marker.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            continue
        if not in_fence:
            lines.append(line)

    return lines


def extract_markdown_list_items(section_body: str) -> list[str]:
    """Return top-level Markdown list item text from a section body."""

    items: list[str] = []
    for line in _without_fenced_code(section_body):
        match = LIST_ITEM_RE.match(line)
        if match:
            items.append(match.group(1).strip())
    return items


def _normalize_reference_value(value: str) -> str | None:
    reference = value.strip()
    if reference.startswith("`") and reference.endswith("`"):
        reference = reference[1:-1].strip()
    if NAME_RE.fullmatch(reference) or reference.endswith(" gate"):
        return reference
    return None


def _split_description(value: str) -> str:
    for separator in ("\u2014", "\u2013", " - "):
        if separator in value:
            return value.split(separator, 1)[0].strip()
    if ":" in value:
        return value.split(":", 1)[0].strip()
    return value.strip()


def _list_item_reference(item: str) -> str | None:
    value = " ".join(item.strip().split())
    if not value:
        return None

    for pattern in (
        r"^\*\*([^*]+)\*\*",
        r"^__([^_]+)__",
        r"^`([^`]+)`",
        r"^\[([^\]]+)\]",
    ):
        match = re.match(pattern, value)
        if match:
            return _normalize_reference_value(match.group(1))

    head = _split_description(value)
    return _normalize_reference_value(head)


def _inline_reference_items(section_body: str) -> list[str]:
    lines = [
        line.strip()
        for line in _without_fenced_code(section_body)
        if line.strip() and LIST_ITEM_RE.match(line) is None
    ]
    if not lines:
        return []

    text = " ".join(lines)
    if "," not in text:
        return []

    references: list[str] = []
    for item in text.split(","):
        reference = _normalize_reference_value(item.strip().strip("."))
        if reference:
            references.append(reference)
    return references


def _is_external_term(value: str) -> bool:
    folded = value.casefold()
    return any(term.casefold() == folded for term in EXTERNAL_TERM_ALLOWLIST)


def _looks_like_body_link(value: str) -> bool:
    if value.endswith(" gate"):
        return True
    return bool(NAME_RE.fullmatch(value) and "-" in value)


def _clean_backtick_token(value: str) -> str | None:
    candidate = value.strip().strip(".,;()[]{}")
    if not candidate:
        return None
    if "\n" in candidate:
        return None
    return candidate


def _extract_backtick_tokens(section_body: str) -> list[str]:
    tokens: list[str] = []
    for match in BACKTICK_RE.finditer(section_body):
        token = _clean_backtick_token(match.group(1))
        if token:
            tokens.append(token)
    return tokens


def validate_section_links(
    file_path: Path,
    section_name: str,
    allowed_names: set[str],
    allowed_label: str,
    errors: list[str],
    *,
    require_list_items: bool = False,
    allow_inline_list: bool = False,
) -> None:
    try:
        _metadata, _raw_frontmatter, body = parse_frontmatter(file_path)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return

    section_body = extract_section_body(body, section_name)
    if section_body is None:
        return

    context = f"{relpath(ROOT, file_path)}:{section_name}"
    for item in extract_markdown_list_items(section_body):
        reference = _list_item_reference(item)
        if reference is None:
            if require_list_items:
                errors.append(f"{context}: list item is not a registry reference: {item}")
            continue
        if reference not in allowed_names:
            errors.append(
                f"{context}: unknown {allowed_label} '{reference}' in list item"
            )

    if allow_inline_list:
        for reference in _inline_reference_items(section_body):
            if reference not in allowed_names:
                errors.append(f"{context}: unknown {allowed_label} '{reference}' in inline list")


def _validate_backtick_links(
    file_path: Path,
    section_name: str,
    allowed_names: set[str],
    errors: list[str],
    *,
    strict_unknowns: bool,
) -> None:
    try:
        _metadata, _raw_frontmatter, body = parse_frontmatter(file_path)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return

    section_body = extract_section_body(body, section_name)
    if section_body is None:
        return

    context = f"{relpath(ROOT, file_path)}:{section_name}"
    for token in _extract_backtick_tokens(section_body):
        if token in allowed_names:
            continue
        if _is_external_term(token):
            continue
        if _looks_like_body_link(token):
            if strict_unknowns or token.endswith(("-skill", "-capability", "-extension", "-gate")):
                errors.append(f"{context}: unknown registry link `{token}`")


def _extract_labeled_block(markdown: str, label: str) -> str | None:
    wanted = f"{label}:".casefold()
    lines = markdown.splitlines()
    captured: list[str] = []
    capturing = False

    for line in lines:
        stripped = line.strip()
        if not capturing:
            if stripped.casefold() == wanted:
                capturing = True
            continue

        if stripped.startswith("#"):
            break
        if stripped and LABEL_RE.match(stripped):
            break
        captured.append(line)

    if not capturing:
        return None
    return "\n".join(captured).strip()


def _validate_router_backtick_block(
    body: str,
    file_path: Path,
    label: str,
    allowed_names: set[str],
    allowed_label: str,
    errors: list[str],
) -> None:
    block = _extract_labeled_block(body, label)
    context = f"{relpath(ROOT, file_path)}:{label}"
    if block is None:
        errors.append(f"{context}: missing router block")
        return

    for token in _extract_backtick_tokens(block):
        if token not in allowed_names:
            errors.append(f"{context}: unknown {allowed_label} `{token}`")


def _extract_router_quality_gates(body: str) -> list[str] | None:
    match = ROUTER_QUALITY_GATES_RE.search(body)
    if not match:
        return None

    gates: list[str] = []
    for line in match.group("body").splitlines():
        item_match = LIST_ITEM_RE.match(line)
        if item_match:
            gate = _split_description(item_match.group(1).strip())
            if gate:
                gates.append(gate)
    return gates


def _split_router_risk_triggers(trigger_text: str) -> list[str]:
    normalized = trigger_text.replace(", and ", ", ")
    return [
        item.strip().removeprefix("and ").strip()
        for item in normalized.split(",")
        if item.strip()
    ]


def _validate_router_quality_gates(
    body: str,
    file_path: Path,
    registry_names: RegistryNames,
    errors: list[str],
) -> None:
    context = f"{relpath(ROOT, file_path)}:Router quality gates"
    gates = _extract_router_quality_gates(body)
    if gates is None:
        errors.append(f"{context}: missing quality gate list in Output Contract")
        return

    for gate in gates:
        if gate not in registry_names.quality_gates:
            errors.append(f"{context}: unknown quality gate '{gate}'")


def _validate_router_risk_triggers(
    body: str,
    file_path: Path,
    registry_names: RegistryNames,
    errors: list[str],
) -> None:
    matches = list(ROUTER_RISK_TRIGGER_RE.finditer(body))
    context = f"{relpath(ROOT, file_path)}:Router risk triggers"
    if not matches:
        errors.append(f"{context}: missing risk trigger list")
        return

    for match in matches:
        for trigger in _split_router_risk_triggers(match.group("triggers")):
            if trigger not in registry_names.risk_triggers:
                errors.append(f"{context}: unknown risk trigger '{trigger}'")


def _validate_router_body(
    file_path: Path,
    body: str,
    registry_names: RegistryNames,
    errors: list[str],
) -> None:
    _validate_router_backtick_block(
        body,
        file_path,
        "Professional skill routing",
        registry_names.skills,
        "professional skill",
        errors,
    )
    _validate_router_backtick_block(
        body,
        file_path,
        "Foundation capability groups",
        registry_names.capabilities,
        "foundation capability",
        errors,
    )
    _validate_router_backtick_block(
        body,
        file_path,
        "Domain extension routing",
        registry_names.extensions,
        "domain extension",
        errors,
    )
    _validate_router_quality_gates(body, file_path, registry_names, errors)
    _validate_router_risk_triggers(body, file_path, registry_names, errors)


def _skill_files() -> list[Path]:
    roots = (PROFESSIONAL_SKILLS_DIR, CAPABILITIES_DIR, DOMAIN_EXTENSIONS_DIR)
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        files.extend(sorted(root.glob("*/SKILL.md")))
    return sorted(files)


def _validate_file_body(
    file_path: Path,
    registry_names: RegistryNames,
    errors: list[str],
) -> None:
    try:
        _metadata, _raw_frontmatter, body = parse_frontmatter(file_path)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return

    list_validators: tuple[
        tuple[str, Callable[[RegistryNames], set[str]], str, bool],
        ...,
    ] = (
        (
            "Linked Foundation Capabilities",
            lambda names: names.capabilities,
            "foundation capability",
            True,
        ),
        (
            "Linked Professional Skills",
            lambda names: names.skills,
            "professional skill",
            True,
        ),
        (
            "Used By",
            lambda names: names.all_skill_entities,
            "registered skill, capability, or domain extension",
            True,
        ),
        (
            "Handoff",
            lambda names: names.all_skill_entities,
            "registered skill, capability, or domain extension",
            False,
        ),
    )

    for section_name, allowed, allowed_label, require_list_items in list_validators:
        validate_section_links(
            file_path,
            section_name,
            allowed(registry_names),
            allowed_label,
            errors,
            require_list_items=require_list_items,
            allow_inline_list=section_name == "Used By",
        )

    for section_name in (
        "Linked Foundation Capabilities",
        "Linked Professional Skills",
        "Handoff",
        "Used By",
        "Selection Rules",
        "Critical Details",
    ):
        _validate_backtick_links(
            file_path,
            section_name,
            registry_names.all_body_links,
            errors,
            strict_unknowns=section_name != "Critical Details",
        )

    if file_path == ROUTER_SKILL:
        _validate_router_body(file_path, body, registry_names, errors)


def main() -> int:
    registry_names, errors = load_registry_names()
    if errors:
        return fail_many("validate-skill-body-links", errors)

    skill_files = _skill_files()
    if not skill_files:
        return fail_many(
            "validate-skill-body-links",
            ["no SKILL.md files found under src skill roots"],
        )

    for file_path in skill_files:
        _validate_file_body(file_path, registry_names, errors)

    if errors:
        return fail_many("validate-skill-body-links", errors)

    print(f"validate-skill-body-links: validated {len(skill_files)} skill body file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
