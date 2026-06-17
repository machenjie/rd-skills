#!/usr/bin/env python3
"""Validate the stage-aware routing architecture.

This is an offline structural check. It does not access the network and does
not call any model. It verifies that the engineering-stage launch architecture
is present and wired:

1. src/registry/stage-model.yaml is the canonical machine-readable stage,
   product-surface, language-surface, transition, and conflict-resolution
   source.
2. docs/ENGINEERING_STAGE_MODEL.md exists with a projection of the stage,
   product, and language surface selectors.
3. The engineering-stage-professionalism foundation capability exists and is
   registered.
4. The skill-authoring-expert foundation capability exists.
5. change-forge-router points to the route result template, which declares the
   Stage Professionalism output contract.
6. routing-rules.yaml declares a stage-specific route and stage signals.
7. The router declares a machine-readable stage route manifest.
8. No long language-deep checklist is copied into the router or the stage
   launcher body.
9. The full Stage Launch Matrix is not copied into skill bodies.
10. The recommended/full/dev profile count math is intact.
11. The authored capability count matches scripts/validation_utils.
12. Prose counts in docs and routing-rules match the canonical foundation
    capability count and the dev profile top-level count (no stale 102/128).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    ValidationProblem,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    registry_items,
    relpath,
    visible_child_dirs,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
STAGE_MODEL_DOC = DOCS_DIR / "ENGINEERING_STAGE_MODEL.md"
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
REGISTRY_DIR = ROOT / "src" / "registry"
CAPABILITIES_REGISTRY = REGISTRY_DIR / "capabilities.yaml"
ROUTING_RULES_REGISTRY = REGISTRY_DIR / "routing-rules.yaml"
SKILLS_REGISTRY = REGISTRY_DIR / "skills.yaml"
DOMAIN_EXTENSIONS_REGISTRY = REGISTRY_DIR / "domain-extensions.yaml"
STAGE_MODEL_REGISTRY = REGISTRY_DIR / "stage-model.yaml"
RUNTIME_ROUTE_RESOLVER = (
    ROOT / "src" / "hook-runtime" / "scripts" / "changeforge_runtime_route_resolver.py"
)
ROUTER_SKILL = PROFESSIONAL_SKILLS_DIR / "change-forge-router" / "SKILL.md"
ROUTER_RESULT_TEMPLATE = (
    PROFESSIONAL_SKILLS_DIR
    / "change-forge-router"
    / "references"
    / "route-result-template.md"
)

STAGE_CAPABILITY = "engineering-stage-professionalism"
AUTHORING_CAPABILITY = "skill-authoring-expert"

REQUIRED_DOC_MARKERS = (
    "Stage Launch Matrix",
    "Product Surface Selector",
    "Language Surface Selector",
)

REQUIRED_STAGES = (
    "requirement-intake",
    "architecture-design",
    "implementation-planning",
    "coding",
    "debugging-diagnosis",
    "bug-fix",
    "code-review",
    "refactoring",
    "testing",
    "release-delivery",
    "documentation-handoff",
    "skill-authoring",
)

ROUTER_STAGE_FIELDS = (
    "Stage Professionalism",
    "Current engineering stage",
    "Capabilities explicitly skipped",
    "Skip rationale",
    "Context budget decision",
    "Next stage handoff",
    "Required quality gates",
    "Stage transition condition",
    "Stage selection evidence",
    "Stage conflicts ruled out",
)

# Markers that only appear when a per-language deep checklist is copied wholesale
# into a body that should merely reference the language capability.
LANGUAGE_DEEP_MARKERS = (
    "goroutine",
    "borrow checker",
    "errgroup",
    "raii",
    "monkeypatch",
    "context.todo",
    "strings.builder",
)
LANGUAGE_DEEP_MARKER_LIMIT = 2

# Distinctive marker of the canonical full stage matrix. It must live only in the
# stage-model document, never copied into a SKILL body.
FULL_MATRIX_MARKER = "do not launch by default"

# Files whose prose counts must track the canonical foundation-capability count
# and the dev profile top-level count. Stale 102/128 prose drifts from the
# enforced constants in scripts/validation_utils and is a documentation defect.
DOC_COUNT_FILES = (
    "README.md",
    "docs/RUNTIME_PROFILES.md",
    "docs/OPERATING_MODEL.md",
    "docs/USAGE.md",
    "docs/INSTALLATION.md",
    "docs/RELEASE.md",
    "docs/PACKAGING.md",
    "docs/SKILL_CONTENT_GOVERNANCE.md",
    "src/registry/routing-rules.yaml",
    "src/professional-skills/change-forge-router/SKILL.md",
    "src/professional-skills/change-forge-router/references/route-result-template.md",
    "src/foundation/capabilities/README.md",
)

# A number immediately tied to "foundation capabilities" (or the composite
# "+ N foundation" / "foundation capability count is N") is a count, not an id.
# Capability id references ("id 102", "102 `agent-execution-discipline`") put the
# number before a backtick name or punctuation, never before "foundation".
_FOUNDATION_COUNT_RES = (
    re.compile(r"(\d+)\s+(?:implemented\s+)?foundation\s+capabilit(?:y|ies)"),
    re.compile(r"(\d+)\s+implemented\s+capabilities"),
    re.compile(r"\+\s*(\d+)\s+foundation\b"),
    re.compile(r"[Ff]oundation capability count is (\d+)"),
)
# Dev profile total phrasings: "`dev` = N" and "N for `dev`".
_DEV_COUNT_RES = (
    re.compile(r"`dev`\s*=\s*(\d+)"),
    re.compile(r"(\d+)\s+for\s+`dev`"),
)
# "Top-level count: N" appears once per profile in RUNTIME_PROFILES.md.
_TOP_LEVEL_COUNT_RE = re.compile(r"Top-level count:\s*(\d+)")


def _read_body(path: Path, errors: list[str]) -> str | None:
    if not path.is_file():
        errors.append(f"missing required file: {relpath(ROOT, path)}")
        return None
    try:
        _metadata, _raw, body = parse_frontmatter(path)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return None
    return body


def _registry_names(path: Path, key: str, ref_keys: tuple[str, ...]) -> set[str]:
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return set()
    names: set[str] = set()
    for entry in registry_items(data, key, path, []):
        if not isinstance(entry, dict):
            continue
        for ref_key in ref_keys:
            value = entry.get(ref_key)
            if isinstance(value, str) and value.strip():
                names.add(value.strip())
                break
    return names


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _stage_entries(stage_model: dict[str, object]) -> dict[str, dict[str, object]]:
    stages: dict[str, dict[str, object]] = {}
    for entry in stage_model.get("stages", []) or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            stages[name.strip()] = entry
    return stages


def _load_stage_model(errors: list[str]) -> dict[str, object] | None:
    if not STAGE_MODEL_REGISTRY.is_file():
        errors.append(f"missing stage model registry: {relpath(ROOT, STAGE_MODEL_REGISTRY)}")
        return None
    try:
        data = load_yaml_file(STAGE_MODEL_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return None
    if not isinstance(data, dict):
        errors.append(f"{relpath(ROOT, STAGE_MODEL_REGISTRY)}: registry must be a mapping")
        return None
    if data.get("kind") != "changeforge.stage_model":
        errors.append(
            f"{relpath(ROOT, STAGE_MODEL_REGISTRY)}: kind must be changeforge.stage_model"
        )
    return data


def _load_quality_gates(errors: list[str]) -> set[str]:
    try:
        data = load_yaml_file(ROUTING_RULES_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return set()
    if not isinstance(data, dict):
        return set()
    return {
        item.strip().casefold()
        for item in data.get("quality_gates", []) or []
        if isinstance(item, str) and item.strip()
    }


def _load_runtime_resolver(errors: list[str]) -> ModuleType | None:
    if not RUNTIME_ROUTE_RESOLVER.is_file():
        errors.append(f"missing runtime route resolver: {relpath(ROOT, RUNTIME_ROUTE_RESOLVER)}")
        return None
    spec = importlib.util.spec_from_file_location(
        "changeforge_runtime_route_resolver_validation",
        RUNTIME_ROUTE_RESOLVER,
    )
    if spec is None or spec.loader is None:
        errors.append(f"{relpath(ROOT, RUNTIME_ROUTE_RESOLVER)}: cannot load module spec")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_stage_model_registry(stage_model: dict[str, object], errors: list[str]) -> None:
    rel = relpath(ROOT, STAGE_MODEL_REGISTRY)
    capability_names = _registry_names(
        CAPABILITIES_REGISTRY,
        "capabilities",
        ("name", "changeforge_capability_id", "id"),
    )
    skill_names = _registry_names(SKILLS_REGISTRY, "skills", ("name", "skill", "id"))
    extension_names = _registry_names(
        DOMAIN_EXTENSIONS_REGISTRY,
        "domain_extensions",
        ("name", "domain_extension", "id"),
    )
    quality_gates = _load_quality_gates(errors)

    stages = _stage_entries(stage_model)
    if tuple(stages) != REQUIRED_STAGES:
        errors.append(
            f"{rel}: stages must be declared in canonical order "
            f"{list(REQUIRED_STAGES)}, found {list(stages)}"
        )

    for stage in REQUIRED_STAGES:
        entry = stages.get(stage)
        if entry is None:
            continue
        for field in (
            "purpose",
            "default_capabilities",
            "skip_by_default",
            "required_evidence",
            "required_quality_gates",
            "allowed_next_stages",
            "forbidden_default_capabilities",
        ):
            value = entry.get(field)
            if field == "purpose":
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{rel}: stage '{stage}' field '{field}' is required")
            elif not _string_list(value):
                errors.append(
                    f"{rel}: stage '{stage}' field '{field}' must be a non-empty list"
                )
        for field in ("default_capabilities", "conditional_capabilities", "forbidden_default_capabilities"):
            for capability in _string_list(entry.get(field)):
                if capability not in capability_names:
                    errors.append(
                        f"{rel}: stage '{stage}' {field} references unknown capability "
                        f"'{capability}'"
                    )
        for gate in _string_list(entry.get("required_quality_gates")):
            if gate.casefold() not in quality_gates:
                errors.append(
                    f"{rel}: stage '{stage}' required_quality_gates contains unknown "
                    f"gate '{gate}'"
                )
        for next_stage in _string_list(entry.get("allowed_next_stages")):
            if next_stage != "closed" and next_stage not in REQUIRED_STAGES:
                errors.append(
                    f"{rel}: stage '{stage}' allowed_next_stages contains unknown "
                    f"stage '{next_stage}'"
                )

    transitions: dict[str, list[str]] = {}
    for entry in stage_model.get("stage_transitions", []) or []:
        if not isinstance(entry, dict):
            errors.append(f"{rel}: stage_transitions entries must be mappings")
            continue
        source = entry.get("from")
        targets = _string_list(entry.get("to"))
        if not isinstance(source, str) or source not in REQUIRED_STAGES:
            errors.append(f"{rel}: stage_transitions contains unknown source {source!r}")
            continue
        transitions[source] = targets
        for target in targets:
            if target != "closed" and target not in REQUIRED_STAGES:
                errors.append(
                    f"{rel}: transition from '{source}' contains unknown target '{target}'"
                )
    for stage, entry in stages.items():
        if transitions.get(stage) != _string_list(entry.get("allowed_next_stages")):
            errors.append(
                f"{rel}: stage '{stage}' allowed_next_stages must match "
                "stage_transitions"
            )

    surfaces = stage_model.get("product_surfaces")
    seen_surfaces: set[str] = set()
    if not isinstance(surfaces, list) or not surfaces:
        errors.append(f"{rel}: product_surfaces must be a non-empty list")
    else:
        for entry in surfaces:
            if not isinstance(entry, dict):
                errors.append(f"{rel}: product_surfaces entries must be mappings")
                continue
            surface = entry.get("surface")
            if not isinstance(surface, str) or not surface.strip():
                errors.append(f"{rel}: product surface missing surface name")
                continue
            if surface in seen_surfaces:
                errors.append(f"{rel}: duplicate product surface '{surface}'")
            seen_surfaces.add(surface)
            required_skill = entry.get("required_skill")
            if not isinstance(required_skill, str) or required_skill not in skill_names | extension_names:
                errors.append(
                    f"{rel}: product surface '{surface}' references unknown "
                    f"required_skill '{required_skill}'"
                )
            for capability in _string_list(entry.get("default_capabilities")):
                if capability not in capability_names:
                    errors.append(
                        f"{rel}: product surface '{surface}' references unknown "
                        f"capability '{capability}'"
                    )
            if not _string_list(entry.get("signals")):
                errors.append(f"{rel}: product surface '{surface}' needs signals")

    languages = stage_model.get("language_surfaces")
    seen_extensions: dict[str, str] = {}
    language_extensions: dict[str, tuple[str, ...]] = {}
    if not isinstance(languages, list) or not languages:
        errors.append(f"{rel}: language_surfaces must be a non-empty list")
    else:
        seen_languages: set[str] = set()
        for entry in languages:
            if not isinstance(entry, dict):
                errors.append(f"{rel}: language_surfaces entries must be mappings")
                continue
            language = entry.get("language")
            if not isinstance(language, str) or not language.strip():
                errors.append(f"{rel}: language surface missing language")
                continue
            if language in seen_languages:
                errors.append(f"{rel}: duplicate language surface '{language}'")
            seen_languages.add(language)
            capability = entry.get("capability")
            if not isinstance(capability, str) or capability not in capability_names:
                errors.append(
                    f"{rel}: language surface '{language}' references unknown "
                    f"capability '{capability}'"
                )
            for stage in _string_list(entry.get("stages")):
                if stage not in REQUIRED_STAGES:
                    errors.append(
                        f"{rel}: language surface '{language}' references unknown "
                        f"stage '{stage}'"
                    )
            if not _string_list(entry.get("signals")):
                errors.append(f"{rel}: language surface '{language}' needs signals")
            for signal in _string_list(entry.get("signals")):
                if len(signal.strip()) == 1:
                    errors.append(
                        f"{rel}: language surface '{language}' has weak one-character "
                        f"signal '{signal}'"
                    )
            extensions = _string_list(entry.get("file_extensions"))
            if not extensions:
                errors.append(
                    f"{rel}: language surface '{language}' needs file_extensions"
                )
            normalized_extensions: list[str] = []
            for extension in extensions:
                if not extension.startswith(".") or extension.strip() != extension:
                    errors.append(
                        f"{rel}: language surface '{language}' invalid file extension "
                        f"'{extension}'"
                    )
                existing = seen_extensions.get(extension)
                if existing and existing != language:
                    errors.append(
                        f"{rel}: file extension '{extension}' is assigned to both "
                        f"'{existing}' and '{language}'"
                    )
                seen_extensions[extension] = language
                normalized_extensions.append(extension)
            if isinstance(language, str) and language.strip():
                language_extensions[language.strip()] = tuple(normalized_extensions)

    resolver = _load_runtime_resolver(errors)
    if resolver is not None:
        resolver_surfaces = tuple(getattr(resolver, "PRODUCT_SURFACE_ORDER", ()))
        missing_surfaces = sorted(seen_surfaces - set(resolver_surfaces))
        if missing_surfaces:
            errors.append(
                f"{rel}: runtime resolver does not cover product surface(s): "
                f"{', '.join(missing_surfaces)}"
            )
        resolver_language_extensions = getattr(resolver, "LANGUAGE_FILE_EXTENSIONS", {})
        if not isinstance(resolver_language_extensions, dict):
            errors.append(
                f"{relpath(ROOT, RUNTIME_ROUTE_RESOLVER)}: LANGUAGE_FILE_EXTENSIONS must be a mapping"
            )
        else:
            missing_languages = sorted(set(language_extensions) - set(resolver_language_extensions))
            if missing_languages:
                errors.append(
                    f"{rel}: runtime resolver does not cover language surface(s): "
                    f"{', '.join(missing_languages)}"
                )
            for language, extensions in language_extensions.items():
                resolver_extensions = tuple(resolver_language_extensions.get(language, ()))
                if resolver_extensions != extensions:
                    errors.append(
                        f"{rel}: runtime resolver extensions for '{language}' must match "
                        f"stage model {list(extensions)}, found {list(resolver_extensions)}"
                    )

    resolution = stage_model.get("stage_resolution")
    if not isinstance(resolution, dict):
        errors.append(f"{rel}: stage_resolution must be a mapping")
        return
    expected_precedence = [
        "explicit_user_stage",
        "active_action_verb",
        "evidence_state",
        "artifact_type",
        "risk_trigger",
    ]
    if _string_list(resolution.get("precedence")) != expected_precedence:
        errors.append(f"{rel}: stage_resolution.precedence has drifted")
    conflict_rules = resolution.get("conflict_rules")
    if not isinstance(conflict_rules, list) or len(conflict_rules) < 12:
        errors.append(f"{rel}: stage_resolution.conflict_rules needs at least 12 rules")
    else:
        for index, rule in enumerate(conflict_rules):
            if not isinstance(rule, dict):
                errors.append(f"{rel}: conflict_rules[{index}] must be a mapping")
                continue
            current_stage = rule.get("current_stage")
            if not isinstance(current_stage, str) or current_stage not in REQUIRED_STAGES:
                errors.append(
                    f"{rel}: conflict_rules[{index}] references unknown stage "
                    f"'{current_stage}'"
                )
            if not _string_list(rule.get("when")):
                errors.append(f"{rel}: conflict_rules[{index}] needs when signals")
            reason = rule.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{rel}: conflict_rules[{index}] needs reason")


def _markdown_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^### {re.escape(heading)}\s*$([\s\S]*?)(?=^### |\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _markdown_h2_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _check_stage_model_doc_consistency(
    stage_model: dict[str, object],
    errors: list[str],
) -> None:
    if not STAGE_MODEL_DOC.is_file():
        return
    text = STAGE_MODEL_DOC.read_text(encoding="utf-8")
    folded = text.casefold()
    if "src/registry/stage-model.yaml" not in text:
        errors.append(
            f"{relpath(ROOT, STAGE_MODEL_DOC)}: document must name "
            "src/registry/stage-model.yaml as the machine source"
        )
    for stage, entry in _stage_entries(stage_model).items():
        section = _markdown_section(text, stage)
        if not section:
            errors.append(f"{relpath(ROOT, STAGE_MODEL_DOC)}: missing stage section '{stage}'")
            continue
        section_folded = section.casefold()
        for field in ("default_capabilities", "required_evidence", "required_quality_gates", "allowed_next_stages"):
            for value in _string_list(entry.get(field)):
                if value.casefold() not in section_folded:
                    errors.append(
                        f"{relpath(ROOT, STAGE_MODEL_DOC)}: stage '{stage}' section "
                        f"missing {field} value '{value}'"
                    )
        for value in _string_list(entry.get("skip_by_default")):
            if value.casefold() not in section_folded:
                errors.append(
                    f"{relpath(ROOT, STAGE_MODEL_DOC)}: stage '{stage}' section "
                    f"missing skip_by_default value '{value}'"
                )

    for entry in stage_model.get("product_surfaces", []) or []:
        if not isinstance(entry, dict):
            continue
        values = [entry.get("surface"), entry.get("required_skill")]
        values.extend(_string_list(entry.get("default_capabilities")))
        for value in values:
            if isinstance(value, str) and value.casefold() not in folded:
                errors.append(
                    f"{relpath(ROOT, STAGE_MODEL_DOC)}: product surface projection "
                    f"missing '{value}'"
                )

    for entry in stage_model.get("language_surfaces", []) or []:
        if not isinstance(entry, dict):
            continue
        values = [entry.get("language"), entry.get("capability")]
        values.extend(_string_list(entry.get("stages")))
        for value in values:
            if isinstance(value, str) and value.casefold() not in folded:
                errors.append(
                    f"{relpath(ROOT, STAGE_MODEL_DOC)}: language surface projection "
                    f"missing '{value}'"
                )


def _check_stage_capability_compact_matrix(
    stage_model: dict[str, object],
    errors: list[str],
) -> None:
    body = _read_body(CAPABILITIES_DIR / STAGE_CAPABILITY / "SKILL.md", errors)
    if body is None:
        return
    folded = body.casefold()
    if "stage model registry" not in body.casefold():
        errors.append(
            f"{relpath(ROOT, CAPABILITIES_DIR / STAGE_CAPABILITY / 'SKILL.md')}: "
            "stage capability must reference the stage model registry"
        )
    for stage, entry in _stage_entries(stage_model).items():
        row_match = re.search(
            rf"^\| {re.escape(stage)} \|(.+)$",
            body,
            flags=re.MULTILINE,
        )
        if not row_match:
            errors.append(
                f"{relpath(ROOT, CAPABILITIES_DIR / STAGE_CAPABILITY / 'SKILL.md')}: "
                f"compact matrix missing stage '{stage}'"
            )
            continue
        row = row_match.group(0).casefold()
        for capability in _string_list(entry.get("default_capabilities")):
            if capability.casefold() not in row:
                errors.append(
                    f"{relpath(ROOT, CAPABILITIES_DIR / STAGE_CAPABILITY / 'SKILL.md')}: "
                    f"compact matrix stage '{stage}' missing default capability "
                    f"'{capability}'"
                )
    for marker in ("Stage transition condition", "Stage selection evidence", "Stage conflicts ruled out"):
        if marker.casefold() not in folded:
            errors.append(
                f"{relpath(ROOT, CAPABILITIES_DIR / STAGE_CAPABILITY / 'SKILL.md')}: "
                f"output contract missing '{marker}'"
            )


def _check_stage_model_doc(errors: list[str]) -> None:
    if not STAGE_MODEL_DOC.is_file():
        errors.append(f"missing stage model doc: {relpath(ROOT, STAGE_MODEL_DOC)}")
        return
    text = STAGE_MODEL_DOC.read_text(encoding="utf-8")
    folded = text.casefold()
    for marker in REQUIRED_DOC_MARKERS:
        if marker.casefold() not in folded:
            errors.append(
                f"{relpath(ROOT, STAGE_MODEL_DOC)}: missing required section '{marker}'"
            )
    for stage in REQUIRED_STAGES:
        if stage.casefold() not in folded:
            errors.append(
                f"{relpath(ROOT, STAGE_MODEL_DOC)}: missing stage '{stage}'"
            )


def _check_capability_present(name: str, errors: list[str]) -> None:
    capability_dir = CAPABILITIES_DIR / name
    skill_file = capability_dir / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"missing capability: {relpath(ROOT, skill_file)}")
        return
    try:
        metadata, _raw, _body = parse_frontmatter(skill_file)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return
    if metadata.get("changeforge_kind") != "foundation-capability":
        errors.append(
            f"{relpath(ROOT, skill_file)}: changeforge_kind must be foundation-capability"
        )


def _check_capability_registered(name: str, errors: list[str]) -> None:
    try:
        data = load_yaml_file(CAPABILITIES_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return
    entries = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        errors.append(f"{relpath(ROOT, CAPABILITIES_REGISTRY)}: missing capabilities list")
        return
    names = {
        entry.get("name")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    if name not in names:
        errors.append(
            f"{relpath(ROOT, CAPABILITIES_REGISTRY)}: capability '{name}' is not registered"
        )


def _check_router_stage_contract(errors: list[str]) -> None:
    body = _read_body(ROUTER_SKILL, errors)
    if body is None:
        return
    folded = body.casefold()
    if "references/route-result-template.md" not in folded:
        errors.append(
            f"{relpath(ROOT, ROUTER_SKILL)}: router must point to "
            "references/route-result-template.md"
        )
    if not ROUTER_RESULT_TEMPLATE.is_file():
        errors.append(
            f"{relpath(ROOT, ROUTER_RESULT_TEMPLATE)}: missing route result template"
        )
        template = ""
    else:
        template = ROUTER_RESULT_TEMPLATE.read_text(encoding="utf-8")
    template_folded = template.casefold()
    for field in ROUTER_STAGE_FIELDS:
        if field.casefold() not in template_folded:
            errors.append(
                f"{relpath(ROOT, ROUTER_RESULT_TEMPLATE)}: route result template is "
                f"missing Stage Professionalism output field '{field}'"
            )
    if "changeforge_stage_route" not in folded:
        errors.append(
            f"{relpath(ROOT, ROUTER_SKILL)}: router is missing the changeforge_stage_route manifest"
        )
    if STAGE_CAPABILITY not in folded:
        errors.append(
            f"{relpath(ROOT, ROUTER_SKILL)}: router does not reference '{STAGE_CAPABILITY}'"
        )
    policy = _markdown_h2_section(body, "Reference Loading Policy")
    policy_folded = policy.casefold()
    if len(policy.strip()) < 500:
        errors.append(
            f"{relpath(ROOT, ROUTER_SKILL)}: Reference Loading Policy must be complete, not empty"
        )
    for keyword in (
        "l1",
        "l2",
        "l3",
        "l4",
        "l5",
        "recommended",
        "full",
        "dev",
        "selected",
        "skipped",
        "references",
        "required_references",
        "skipped_references",
    ):
        if keyword not in policy_folded:
            errors.append(
                f"{relpath(ROOT, ROUTER_SKILL)}: Reference Loading Policy missing "
                f"keyword '{keyword}'"
            )


def _check_routing_rules(errors: list[str]) -> None:
    try:
        data = load_yaml_file(ROUTING_RULES_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return
    if not isinstance(data, dict):
        errors.append(f"{relpath(ROOT, ROUTING_RULES_REGISTRY)}: registry must be a mapping")
        return

    routes = data.get("routing_rules")
    route_targets = {
        entry.get("route_to")
        for entry in routes
        if isinstance(entry, dict)
    } if isinstance(routes, list) else set()
    if STAGE_CAPABILITY not in route_targets:
        errors.append(
            f"{relpath(ROOT, ROUTING_RULES_REGISTRY)}: missing stage route "
            f"'route_to: {STAGE_CAPABILITY}'"
        )

    stage_signals = data.get("engineering_stage_signals")
    if not isinstance(stage_signals, list) or not stage_signals:
        errors.append(
            f"{relpath(ROOT, ROUTING_RULES_REGISTRY)}: missing non-empty "
            "engineering_stage_signals list"
        )
        return
    declared_stages = {
        entry.get("stage")
        for entry in stage_signals
        if isinstance(entry, dict)
    }
    for stage in REQUIRED_STAGES:
        if stage not in declared_stages:
            errors.append(
                f"{relpath(ROOT, ROUTING_RULES_REGISTRY)}: engineering_stage_signals "
                f"missing stage '{stage}'"
            )


def _check_risk_trigger_rules(errors: list[str]) -> None:
    try:
        data = load_yaml_file(ROUTING_RULES_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return
    if not isinstance(data, dict):
        errors.append(f"{relpath(ROOT, ROUTING_RULES_REGISTRY)}: registry must be a mapping")
        return

    rel = relpath(ROOT, ROUTING_RULES_REGISTRY)
    triggers = data.get("risk_escalation_triggers")
    rules = data.get("risk_trigger_rules")
    if not isinstance(triggers, list) or not triggers:
        errors.append(f"{rel}: missing non-empty risk_escalation_triggers list")
        return
    if not isinstance(rules, list) or not rules:
        errors.append(f"{rel}: missing non-empty risk_trigger_rules list")
        return

    trigger_names = {
        trigger.strip().casefold(): trigger.strip()
        for trigger in triggers
        if isinstance(trigger, str) and trigger.strip()
    }
    rule_names: dict[str, str] = {}
    duplicate_rules: set[str] = set()
    for entry in rules:
        if not isinstance(entry, dict):
            errors.append(f"{rel}: risk_trigger_rules entries must be mappings")
            continue
        trigger = entry.get("trigger")
        if not isinstance(trigger, str) or not trigger.strip():
            errors.append(f"{rel}: risk_trigger_rules entries must include trigger")
            continue
        normalized = trigger.strip().casefold()
        if normalized in rule_names:
            duplicate_rules.add(trigger.strip())
        rule_names[normalized] = trigger.strip()

    for trigger in trigger_names:
        if trigger not in rule_names:
            errors.append(
                f"{rel}: risk_escalation_triggers entry "
                f"'{trigger_names[trigger]}' has no matching risk_trigger_rules entry"
            )
    for trigger in rule_names:
        if trigger not in trigger_names:
            errors.append(
                f"{rel}: risk_trigger_rules trigger "
                f"'{rule_names[trigger]}' is not declared in risk_escalation_triggers"
            )
    for trigger in sorted(duplicate_rules):
        errors.append(f"{rel}: duplicate risk_trigger_rules trigger '{trigger}'")

    skill_names = _registry_names(SKILLS_REGISTRY, "skills", ("name", "skill", "id"))
    capability_names = _registry_names(
        CAPABILITIES_REGISTRY,
        "capabilities",
        ("name", "changeforge_capability_id", "id"),
    )
    extension_names = _registry_names(
        DOMAIN_EXTENSIONS_REGISTRY,
        "domain_extensions",
        ("name", "domain_extension", "id"),
    )
    quality_gates = {
        item.strip().casefold()
        for item in data.get("quality_gates", []) or []
        if isinstance(item, str) and item.strip()
    }
    reference_fields = (
        ("required_skills", skill_names, "skill"),
        ("required_capabilities", capability_names, "capability"),
        ("required_domain_extensions", extension_names, "domain extension"),
        ("required_quality_gates", quality_gates, "quality gate"),
    )
    for entry in rules:
        if not isinstance(entry, dict):
            continue
        trigger = entry.get("trigger")
        if not isinstance(trigger, str) or not trigger.strip():
            continue
        for field, allowed, label in reference_fields:
            value = entry.get(field)
            if value is None:
                continue
            if not isinstance(value, list):
                errors.append(
                    f"{rel}: risk_trigger_rules trigger '{trigger}' field "
                    f"{field} must be a list"
                )
                continue
            for item in _string_list(value):
                lookup = item.casefold() if field == "required_quality_gates" else item
                if lookup not in allowed:
                    errors.append(
                        f"{rel}: risk_trigger_rules trigger '{trigger}' references "
                        f"unknown {label} '{item}' in {field}"
                    )


def _check_no_language_deep_copy(errors: list[str]) -> None:
    targets = (
        ROUTER_SKILL,
        CAPABILITIES_DIR / STAGE_CAPABILITY / "SKILL.md",
    )
    for path in targets:
        body = _read_body(path, errors)
        if body is None:
            continue
        folded = body.casefold()
        hits = [marker for marker in LANGUAGE_DEEP_MARKERS if marker in folded]
        if len(hits) > LANGUAGE_DEEP_MARKER_LIMIT:
            errors.append(
                f"{relpath(ROOT, path)}: language-deep checklist content appears copied "
                f"into this body ({', '.join(hits)}); reference the language capability instead"
            )


def _check_matrix_not_duplicated(errors: list[str]) -> None:
    offenders: list[str] = []
    for root in (PROFESSIONAL_SKILLS_DIR, CAPABILITIES_DIR, DOMAIN_EXTENSIONS_DIR):
        if not root.is_dir():
            continue
        for skill_file in sorted(root.glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8").casefold()
            if FULL_MATRIX_MARKER in text:
                offenders.append(relpath(ROOT, skill_file))
    if len(offenders) > 1:
        errors.append(
            "Stage Launch Matrix appears copied into multiple skill bodies "
            f"({', '.join(offenders)}); it must be owned by docs/ENGINEERING_STAGE_MODEL.md "
            "and referenced"
        )


def _check_profile_count_logic(errors: list[str]) -> None:
    expected = {
        "recommended": EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "full": EXPECTED_PROFESSIONAL_SKILL_COUNT + EXPECTED_DOMAIN_EXTENSION_COUNT,
        "dev": (
            EXPECTED_PROFESSIONAL_SKILL_COUNT
            + EXPECTED_FOUNDATION_CAPABILITY_COUNT
            + EXPECTED_DOMAIN_EXTENSION_COUNT
        ),
    }
    if EXPECTED_PROFILE_TOP_LEVEL_COUNTS != expected:
        errors.append(
            "profile top-level count logic is broken: "
            f"{EXPECTED_PROFILE_TOP_LEVEL_COUNTS} != {expected}"
        )


def _check_capability_count_consistency(errors: list[str]) -> None:
    capability_dirs = visible_child_dirs(CAPABILITIES_DIR, excluded_prefixes=(".", "_"))
    if len(capability_dirs) != EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        errors.append(
            f"{relpath(ROOT, CAPABILITIES_DIR)}: found {len(capability_dirs)} capabilities "
            f"but validation_utils expects {EXPECTED_FOUNDATION_CAPABILITY_COUNT}"
        )


def _check_doc_count_consistency(errors: list[str]) -> None:
    """Scan curated docs and routing-rules for stale foundation/dev counts.

    The enforced constants live in scripts/validation_utils. Prose copies of the
    counts ("102 foundation capabilities", "128 for `dev`") drift silently; this
    check fails when a count in scanned prose no longer matches the canonical
    foundation capability count or the dev profile top-level count.
    """
    foundation = EXPECTED_FOUNDATION_CAPABILITY_COUNT
    dev_total = EXPECTED_PROFILE_TOP_LEVEL_COUNTS["dev"]
    allowed_top_level = set(EXPECTED_PROFILE_TOP_LEVEL_COUNTS.values())
    for rel in DOC_COUNT_FILES:
        path = ROOT / rel
        if not path.is_file():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            snippet = line.strip()[:80]
            for pattern in _FOUNDATION_COUNT_RES:
                for match in pattern.finditer(line):
                    value = int(match.group(1))
                    if value != foundation:
                        errors.append(
                            f"{rel}:{line_no}: stale foundation capability count {value} "
                            f"(expected {foundation}): {snippet}"
                        )
            for pattern in _DEV_COUNT_RES:
                for match in pattern.finditer(line):
                    value = int(match.group(1))
                    if value != dev_total:
                        errors.append(
                            f"{rel}:{line_no}: stale dev profile top-level count {value} "
                            f"(expected {dev_total}): {snippet}"
                        )
            for match in _TOP_LEVEL_COUNT_RE.finditer(line):
                value = int(match.group(1))
                if value not in allowed_top_level:
                    errors.append(
                        f"{rel}:{line_no}: stale top-level count {value} "
                        f"(expected one of {sorted(allowed_top_level)}): {snippet}"
                    )


def main() -> int:
    errors: list[str] = []
    stage_model = _load_stage_model(errors)

    _check_stage_model_doc(errors)
    if stage_model is not None:
        _check_stage_model_registry(stage_model, errors)
        _check_stage_model_doc_consistency(stage_model, errors)
        _check_stage_capability_compact_matrix(stage_model, errors)
    _check_capability_present(STAGE_CAPABILITY, errors)
    _check_capability_present(AUTHORING_CAPABILITY, errors)
    _check_capability_registered(STAGE_CAPABILITY, errors)
    _check_router_stage_contract(errors)
    _check_routing_rules(errors)
    _check_risk_trigger_rules(errors)
    _check_no_language_deep_copy(errors)
    _check_matrix_not_duplicated(errors)
    _check_profile_count_logic(errors)
    _check_capability_count_consistency(errors)
    _check_doc_count_consistency(errors)

    if errors:
        return fail_many("validate-stage-routing-architecture", errors)

    print(
        "validate-stage-routing-architecture: stage architecture is present and wired "
        f"({len(REQUIRED_STAGES)} stages, capability {STAGE_CAPABILITY}, "
        "router Stage Professionalism contract, stage route, and stage manifest)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
