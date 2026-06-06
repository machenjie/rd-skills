#!/usr/bin/env python3
"""Validate the stage-aware routing architecture.

This is an offline structural check. It does not access the network and does
not call any model. It verifies that the engineering-stage launch architecture
is present and wired:

1. docs/ENGINEERING_STAGE_MODEL.md exists with the stage, product, and language
   surface selectors.
2. The engineering-stage-professionalism foundation capability exists and is
   registered.
3. The skill-authoring-expert foundation capability exists.
4. change-forge-router declares the Stage Professionalism output contract.
5. routing-rules.yaml declares a stage-specific route and stage signals.
6. The router declares a machine-readable stage route manifest.
7. No long language-deep checklist is copied into the router or the stage
   launcher body.
8. The full Stage Launch Matrix is not copied into skill bodies (it is owned by
   docs/ENGINEERING_STAGE_MODEL.md and referenced, not duplicated).
9. The recommended/full/dev profile count math is intact.
10. The authored capability count matches scripts/validation_utils.
11. Prose counts in docs and routing-rules match the canonical foundation
    capability count and the dev profile top-level count (no stale 102/128).
"""

from __future__ import annotations

import re
from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    ValidationProblem,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
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
ROUTER_SKILL = PROFESSIONAL_SKILLS_DIR / "change-forge-router" / "SKILL.md"

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
    for field in ROUTER_STAGE_FIELDS:
        if field.casefold() not in folded:
            errors.append(
                f"{relpath(ROOT, ROUTER_SKILL)}: router is missing Stage Professionalism "
                f"output field '{field}'"
            )
    if "changeforge_stage_route" not in folded:
        errors.append(
            f"{relpath(ROOT, ROUTER_SKILL)}: router is missing the changeforge_stage_route manifest"
        )
    if STAGE_CAPABILITY not in folded:
        errors.append(
            f"{relpath(ROOT, ROUTER_SKILL)}: router does not reference '{STAGE_CAPABILITY}'"
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

    _check_stage_model_doc(errors)
    _check_capability_present(STAGE_CAPABILITY, errors)
    _check_capability_present(AUTHORING_CAPABILITY, errors)
    _check_capability_registered(STAGE_CAPABILITY, errors)
    _check_router_stage_contract(errors)
    _check_routing_rules(errors)
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
