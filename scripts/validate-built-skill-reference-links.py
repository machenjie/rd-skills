#!/usr/bin/env python3
"""Validate Runtime links plus a temporary complete Layer 3 projection."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import build as canonical_build
from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    FOUNDATION_DELIVERY_SCOPES,
    ValidationProblem,
    collect_skill_root_source,
    fail_many,
    layer3_selector_expand_runtime_projection,
    layer3_selector_resolve_control_projection,
    load_yaml_file,
    parse_frontmatter,
    relpath,
    validate_ai_readability,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILT_ROOT = ROOT / "dist" / "universal" / "skills"
RUNTIME_NAME = "recommended"
BUILD_MANIFEST_NAME = ".changeforge-build-manifest.json"
MAX_RENDERED_PROFESSIONAL_BODY_LINES = 120

INLINE_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s+(\S+)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def _without_fenced_code(markdown: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    in_fence = False
    fence_marker: str | None = None

    for line_no, line in enumerate(markdown.splitlines(), start=1):
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
            lines.append((line_no, line))
    return lines


def _first_link_target(raw: str) -> str:
    text = raw.strip()
    if text.startswith("<") and ">" in text:
        return text[1 : text.index(">")].strip()
    return text.split(None, 1)[0].strip()


def _is_external_or_anchor(target: str) -> bool:
    if not target or target.startswith("#"):
        return True
    if target.startswith(("http://", "https://", "mailto:", "tel:")):
        return True
    return bool(SCHEME_RE.match(target))


def _normalize_target(raw: str) -> str | None:
    target = unquote(_first_link_target(raw)).strip()
    if _is_external_or_anchor(target):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return None
    if "<" in target or ">" in target:
        return None
    return target


def _code_reference_target(raw: str) -> str | None:
    value = raw.strip().strip(".,;:()[]{}")
    if "&lt;" in value.casefold() or "&gt;" in value.casefold():
        return None
    if " " in value or "\t" in value:
        return None
    if ".md" not in value.casefold():
        return None
    return _normalize_target(value)


def _is_example_mapping(line: str) -> bool:
    return "->" in line or "=>" in line


def _iter_local_targets(path: Path) -> list[tuple[int, str, bool]]:
    targets: list[tuple[int, str, bool]] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in _without_fenced_code(text):
        if "source/dev-only" in line.casefold():
            continue
        for match in INLINE_LINK_RE.finditer(line):
            target = _normalize_target(match.group(1))
            if target is not None:
                targets.append(
                    (line_no, target, target.startswith(("references/", "examples/")))
                )
        ref_match = REFERENCE_LINK_RE.match(line)
        if ref_match:
            target = _normalize_target(ref_match.group(1))
            if target is not None:
                targets.append(
                    (line_no, target, target.startswith(("references/", "examples/")))
                )
        if _is_example_mapping(line):
            continue
        for match in BACKTICK_RE.finditer(line):
            target = _code_reference_target(match.group(1))
            if target is not None:
                root_relative = target.startswith("references/")
                if root_relative or target.startswith(("./references/", "../references/")):
                    targets.append((line_no, target, root_relative))
    return targets


def _skill_root(markdown_file: Path, profile_root: Path) -> Path:
    try:
        relative = markdown_file.relative_to(profile_root)
    except ValueError:
        return markdown_file.parent
    return profile_root / relative.parts[0] if relative.parts else profile_root


def _target_exists(
    markdown_file: Path,
    profile_root: Path,
    target: str,
    root_relative: bool,
) -> bool:
    if target.startswith("/"):
        candidate = profile_root / target.lstrip("/")
    elif root_relative:
        candidate = _skill_root(markdown_file, profile_root) / target
    else:
        candidate = markdown_file.parent / target
    try:
        resolved = candidate.resolve()
        profile_resolved = profile_root.resolve()
    except OSError:
        return False
    return resolved == profile_resolved or (
        profile_resolved in resolved.parents and resolved.exists()
    )


def _display_path(path: Path) -> str:
    try:
        return relpath(ROOT, path)
    except ValueError:
        return str(path)


def _validate_runtime(
    runtime_root: Path,
    errors: list[str],
    *,
    enforce_source_mapping: bool = True,
) -> None:
    if not runtime_root.is_dir():
        errors.append(f"{_display_path(runtime_root)}: missing built Runtime")
        return
    markdown_files = sorted(runtime_root.rglob("*.md"))
    if not markdown_files:
        errors.append(f"{_display_path(runtime_root)}: no Markdown files found")
        return
    for markdown_file in markdown_files:
        for line_no, target, root_relative in _iter_local_targets(markdown_file):
            if not _target_exists(markdown_file, runtime_root, target, root_relative):
                errors.append(
                    f"{_display_path(markdown_file)}:{line_no}: "
                    f"missing local built Skill reference '{target}'"
                )
    _validate_compiled_layer3_entrypoints(
        runtime_root,
        errors,
        enforce_source_mapping=enforce_source_mapping,
    )


def _empty_complete_layer3_result() -> dict[str, object]:
    return {
        "projected_count": 0,
        "foundation_count": 0,
        "domain_count": 0,
        "runtime_jit_count": 0,
        "non_runtime_count": 0,
        "projected_names": [],
        "non_runtime_names": [],
    }


def _validate_complete_layer3_temporary_projection(
    errors: list[str],
) -> dict[str, object]:
    """Validate the complete Layer 3 source inventory without a Runtime profile."""

    result = _empty_complete_layer3_result()
    temporary_root: Path | None = None
    try:
        with tempfile.TemporaryDirectory(
            prefix="changeforge-complete-layer3-validation-"
        ) as raw:
            temporary_root = Path(raw)
            result = _validate_complete_layer3_projection_at(temporary_root, errors)
    except OSError as exc:
        errors.append(f"complete Layer 3 temporary projection failed: {exc}")
    if temporary_root is not None and temporary_root.exists():
        errors.append(
            f"{_display_path(temporary_root)}: complete Layer 3 temporary projection "
            "was not cleaned up"
        )
    return result


def _validate_complete_layer3_projection_at(
    staging_root: Path,
    errors: list[str],
) -> dict[str, object]:
    """Render all Layer 3 sources once inside an already-created temp root."""

    result = _empty_complete_layer3_result()
    try:
        staging_resolved = staging_root.resolve(strict=False)
        repository_resolved = ROOT.resolve(strict=True)
    except OSError as exc:
        errors.append(
            f"{_display_path(staging_root)}: cannot resolve temporary validation root: {exc}"
        )
        return result
    if canonical_build._paths_overlap(staging_resolved, repository_resolved):
        errors.append(
            f"{_display_path(staging_root)}: temporary validation root must remain "
            "outside the repository and Runtime outputs"
        )
        return result
    if not staging_root.is_dir() or staging_root.is_symlink():
        errors.append(
            f"{_display_path(staging_root)}: temporary validation root must be a "
            "regular directory"
        )
        return result

    try:
        registries = canonical_build._load_registries()
        canonical_build._preflight_registry_entries(registries)
        items = {
            layer: canonical_build._load_items(layer, entries)
            for layer, entries in registries.items()
        }
        canonical_build._validate_global_skill_names(items)
    except (canonical_build.BuildError, OSError) as exc:
        errors.append(f"complete Layer 3 source authority is invalid: {exc}")
        return result

    foundation_items = items.get("foundation", [])
    domain_items = items.get("domain", [])
    layer3_items = [*foundation_items, *domain_items]
    foundation_names = {item.name for item in foundation_items}
    domain_names = {item.name for item in domain_items}
    projected_names = [item.name for item in layer3_items]
    result.update(
        {
            "projected_count": len(layer3_items),
            "foundation_count": len(foundation_items),
            "domain_count": len(domain_items),
            "projected_names": projected_names,
        }
    )
    if len(foundation_items) != EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        errors.append(
            "complete Layer 3 projection requires exactly "
            f"{EXPECTED_FOUNDATION_CAPABILITY_COUNT} Foundation Skills, found "
            f"{len(foundation_items)}"
        )
    if len(domain_items) != EXPECTED_DOMAIN_EXTENSION_COUNT:
        errors.append(
            "complete Layer 3 projection requires exactly "
            f"{EXPECTED_DOMAIN_EXTENSION_COUNT} Domain Skills, found "
            f"{len(domain_items)}"
        )
    if len(projected_names) != len(set(projected_names)):
        errors.append("complete Layer 3 projection contains duplicate Skill names")
    _validate_layer3_registry_source_inventory(items, errors)

    foundation_scopes = {
        item.name: item.registry.get("delivery_scope") for item in foundation_items
    }
    scope_counts = Counter(foundation_scopes.values())
    if scope_counts != Counter(EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS):
        errors.append(
            "complete Layer 3 projection Foundation delivery scope counts drift"
        )
    runtime_names = {
        *domain_names,
        *(
            name
            for name, scope in foundation_scopes.items()
            if scope == "product"
        ),
    }
    non_runtime_names = sorted(foundation_names - runtime_names)
    result.update(
        {
            "runtime_jit_count": len(runtime_names),
            "non_runtime_count": len(non_runtime_names),
            "non_runtime_names": non_runtime_names,
        }
    )

    projection_root = staging_root / "expanded-layer3-validation"
    selector_profile_root = staging_root / "selector-authority"
    selector_control_root = selector_profile_root / "engineering-control-plane"
    projection_root.mkdir(parents=True, exist_ok=False)
    try:
        canonical_build._write_control_layer3_selector_projections(
            selector_control_root
        )
    except (canonical_build.BuildError, OSError) as exc:
        errors.append(f"complete Layer 3 selector projection failed: {exc}")
        return result

    for item in layer3_items:
        destination = projection_root / item.name
        try:
            collect_skill_root_source(item.path / "SKILL.md", root=ROOT)
            canonical_build._copy_skill_tree(item.path, destination)
            canonical_build._write_compact_layer3_root_projection(
                destination, item
            )
            canonical_build._validate_zip_source(destination)
        except (canonical_build.BuildError, OSError, ValueError) as exc:
            errors.append(f"{item.name}: temporary Layer 3 projection failed: {exc}")
            continue
        _validate_temporary_layer3_root(item, destination, projection_root, errors)

    try:
        canonical_build._reject_tree_symlinks(
            staging_root, "complete Layer 3 temporary projection"
        )
    except canonical_build.BuildError as exc:
        errors.append(str(exc))
    for path in sorted(staging_root.rglob("*")):
        try:
            path.resolve(strict=False).relative_to(staging_resolved)
        except (OSError, ValueError):
            errors.append(
                f"{_display_path(path)}: complete Layer 3 output escapes its "
                "temporary validation root"
            )
            break

    _validate_complete_layer3_selector_reachability(
        selector_profile_root,
        projection_root,
        items,
        runtime_names,
        set(non_runtime_names),
        errors,
    )
    return result


def _validate_layer3_registry_source_inventory(
    items: dict[str, list[canonical_build.SkillItem]],
    errors: list[str],
) -> None:
    for layer in ("foundation", "domain"):
        source_root = canonical_build.LAYER_SOURCE_ROOTS[layer]
        expected = {item.path.name for item in items.get(layer, [])}
        actual = {
            path.name
            for path in source_root.iterdir()
            if path.is_dir() and not path.name.startswith((".", "_"))
        }
        if actual != expected:
            errors.append(
                f"{_display_path(source_root)}: {layer} Registry/source inventory "
                f"disagrees; missing={sorted(expected - actual)}, "
                f"unregistered={sorted(actual - expected)}"
            )


def _validate_temporary_layer3_root(
    item: canonical_build.SkillItem,
    destination: Path,
    projection_root: Path,
    errors: list[str],
) -> None:
    skill_file = destination / "SKILL.md"
    try:
        _metadata, _frontmatter, body = parse_frontmatter(skill_file)
    except ValidationProblem as exc:
        errors.append(f"{_display_path(skill_file)}: invalid compact projection: {exc}")
        return
    _h1_titles, sections = canonical_build._markdown_heading_sections(body)
    expected_headings = (
        canonical_build.FOUNDATION_BUILT_KERNEL_HEADINGS
        if item.layer == "foundation"
        else canonical_build.PROFESSIONAL_BUILT_KERNEL_HEADINGS
    )
    if list(sections) != list(expected_headings):
        errors.append(
            f"{_display_path(skill_file)}: compact {item.layer} projection headings "
            f"{list(sections)} must equal {list(expected_headings)}"
        )

    for directory in ("references", "examples", "assets"):
        source_root = item.path / directory
        destination_root = destination / directory
        source_files = {
            path.relative_to(source_root).as_posix(): path.read_bytes()
            for path in sorted(source_root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        } if source_root.is_dir() else {}
        destination_files = {
            path.relative_to(destination_root).as_posix(): path.read_bytes()
            for path in sorted(destination_root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        } if destination_root.is_dir() else {}
        if source_files != destination_files:
            errors.append(
                f"{_display_path(destination_root)}: copied nested {directory} "
                "files do not match source authority"
            )

    for markdown_file in sorted(destination.rglob("*.md")):
        for line_no, target, root_relative in _iter_local_targets(markdown_file):
            if not _target_exists(
                markdown_file, projection_root, target, root_relative
            ):
                errors.append(
                    f"{_display_path(markdown_file)}:{line_no}: missing local "
                    f"temporary Layer 3 reference '{target}'"
                )


def _validate_complete_layer3_selector_reachability(
    selector_profile_root: Path,
    projection_root: Path,
    items: dict[str, list[canonical_build.SkillItem]],
    runtime_names: set[str],
    non_runtime_names: set[str],
    errors: list[str],
) -> None:
    expected_by_professional: dict[str, list[str]] = {}
    for professional in items.get("professional", []):
        candidates = professional.registry.get("layer3_candidates")
        expected_by_professional[professional.name] = [
            candidate
            for candidate in candidates
            if isinstance(candidate, str) and candidate in runtime_names
        ] if isinstance(candidates, list) else []

    reachable: set[str] = set()
    authorized_union: set[str] = set()
    selector_root = (
        selector_profile_root
        / "engineering-control-plane"
        / "references"
        / "selectors"
    )
    for professional, expected in expected_by_professional.items():
        selector_path = selector_root / f"{professional}.json"
        selector = _load_complete_selector_projection(selector_path, errors)
        if selector is None:
            continue
        profile_authority = selector.get("profile_authority")
        authorized = {
            candidate
            for row in profile_authority
            if isinstance(row, dict)
            for candidate in row.get("authorized_layer3", [])
            if isinstance(candidate, str)
        } if isinstance(profile_authority, list) else set()
        authorized_union.update(authorized)
        if authorized != set(expected):
            errors.append(
                f"{_display_path(selector_path)}: selector ownership does not match "
                f"the Professional Registry; expected={sorted(expected)}, "
                f"actual={sorted(authorized)}"
            )
        for candidate in expected:
            if _validate_selector_reference_reachability(
                selector_profile_root,
                professional,
                candidate,
                projection_root / candidate,
                errors,
                selector=selector,
            ):
                reachable.add(candidate)

    missing_runtime = runtime_names - reachable
    if missing_runtime:
        errors.append(
            "complete Layer 3 Runtime JIT inventory lacks Professional selector "
            f"reachability: {sorted(missing_runtime)}"
        )
    leaked_non_runtime = non_runtime_names & authorized_union
    if leaked_non_runtime:
        errors.append(
            "non-Runtime Foundation Skills entered selector authorization: "
            f"{sorted(leaked_non_runtime)}"
        )


def _validate_compiled_layer3_entrypoints(
    profile_root: Path,
    errors: list[str],
    *,
    enforce_source_mapping: bool = True,
) -> None:
    manifest_path = profile_root / BUILD_MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{_display_path(manifest_path)}: invalid or missing manifest: {exc}")
        return

    runtime_name = str(manifest.get("profile") or "")
    if runtime_name != RUNTIME_NAME:
        errors.append(
            f"{_display_path(manifest_path)}: Runtime identity must equal "
            f"{RUNTIME_NAME!r}, found {runtime_name!r}"
        )
    top_level = manifest.get("top_level_skills")
    professional = manifest.get("professional_skills")
    foundation = manifest.get("foundation_skills")
    foundation_scopes = manifest.get("foundation_delivery_scopes")
    compiled_foundation = manifest.get("compiled_foundation_skills")
    domain = manifest.get("domain_skills")
    compiled_format = manifest.get("compiled_layer3_format")
    compiled = manifest.get("compiled_layer3_references")
    if not all(isinstance(value, list) for value in (top_level, professional, foundation, domain)):
        errors.append(f"{_display_path(manifest_path)}: malformed Skill lists")
        return
    if not isinstance(compiled, dict):
        errors.append(f"{_display_path(manifest_path)}: malformed compiled Layer 3 mapping")
        return
    if compiled_format != COMPILED_LAYER3_FORMAT:
        errors.append(
            f"{_display_path(manifest_path)}: compiled_layer3_format must equal "
            f"{COMPILED_LAYER3_FORMAT!r}, found {compiled_format!r}"
        )

    top_names = {str(name) for name in top_level}
    foundation_names = {str(name) for name in foundation}
    domain_names = {str(name) for name in domain}
    if not isinstance(foundation_scopes, dict) or set(foundation_scopes) != foundation_names:
        errors.append(
            f"{_display_path(manifest_path)}: Foundation delivery scopes must cover "
            "exactly the Foundation inventory"
        )
        foundation_scopes = {}
    elif not set(foundation_scopes.values()) <= FOUNDATION_DELIVERY_SCOPES:
        errors.append(
            f"{_display_path(manifest_path)}: invalid Foundation delivery scope"
        )
    if len(foundation_names) == EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        counts = Counter(foundation_scopes.values())
        if counts != Counter(EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS):
            errors.append(
                f"{_display_path(manifest_path)}: Foundation delivery scope counts drift"
            )
    if not isinstance(compiled_foundation, list) or not all(
        isinstance(value, str) and value for value in compiled_foundation
    ):
        errors.append(
            f"{_display_path(manifest_path)}: malformed compiled Foundation list"
        )
        compiled_foundation = []
    elif len(compiled_foundation) != len(set(compiled_foundation)):
        errors.append(
            f"{_display_path(manifest_path)}: compiled Foundation list contains duplicates"
        )
    product_foundation_names = {
        name for name, scope in foundation_scopes.items() if scope == "product"
    }
    expected_compiled_foundation = product_foundation_names
    if set(compiled_foundation) != expected_compiled_foundation:
        errors.append(
            f"{_display_path(manifest_path)}: compiled Foundation list does not match "
            "the Runtime product delivery contract"
        )
    if top_names & foundation_names:
        errors.append(
            f"{_display_path(manifest_path)}: Runtime exposes Foundation Skills at top level"
        )
    if top_names & domain_names:
        errors.append(
            f"{_display_path(manifest_path)}: Runtime exposes Domain Skills at top level"
        )

    professional_names = [str(name) for name in professional]
    if set(compiled) != set(professional_names):
        errors.append(
            f"{_display_path(manifest_path)}: compiled Layer 3 mapping must cover exactly all Professional Skills"
        )
    if enforce_source_mapping:
        errors.extend(
            _source_compiled_mapping_errors(
                professional_names,
                compiled,
                _display_path(manifest_path),
            )
        )
    compiled_union = {
        candidate
        for candidates in compiled.values()
        if isinstance(candidates, list)
        for candidate in candidates
        if isinstance(candidate, str)
    }
    non_product_foundation = foundation_names - product_foundation_names
    if compiled_union & non_product_foundation:
        errors.append(
            f"{_display_path(manifest_path)}: compiled Layer 3 mapping contains "
            "non-product Foundation Skills"
        )
    for name in professional_names:
        expected_raw = compiled.get(name)
        if not isinstance(expected_raw, list) or not all(
            isinstance(value, str) and value for value in expected_raw
        ):
            errors.append(
                f"{_display_path(manifest_path)}: {name} compiled candidates must be a string list"
            )
            continue
        expected = list(dict.fromkeys(expected_raw))
        if expected != expected_raw:
            errors.append(
                f"{_display_path(manifest_path)}: {name} compiled candidates contain duplicates"
            )
        skill_root = profile_root / name
        skill_file = skill_root / "SKILL.md"
        skill_text = skill_file.read_text(encoding="utf-8") if skill_file.is_file() else ""
        _validate_rendered_professional_body(skill_file, errors)
        layer3_root = skill_root / "references" / "layer3"
        if skill_text.count("## Layer 3 Delivery") != 1:
            errors.append(
                f"{_display_path(skill_file)}: must contain exactly one generated Layer 3 Delivery section"
            )
        if "## Compiled Layer 3 References" in skill_text:
            errors.append(
                f"{_display_path(skill_file)}: contains the obsolete compiled-only Layer 3 heading"
            )
        expected_delivery = (
            "Foundation and Domain items are compiled at "
            "`references/layer3/<name>.md`."
            if expected
            else "No Foundation or Domain Layer 3 items are assigned to this Skill."
        )
        actual_delivery = (
            skill_text.split("## Layer 3 Delivery\n\n", 1)[1].strip()
            if "## Layer 3 Delivery\n\n" in skill_text
            else ""
        )
        if actual_delivery != expected_delivery:
            errors.append(
                f"{_display_path(skill_file)}: Layer 3 delivery must match the current-build projection"
            )
        duplicate_authority = (
            "Never preload Layer 3",
            "capsule-named",
            "Layer 3 index or catalog",
            "(references/layer3/index.md)",
        )
        if any(phrase in skill_text for phrase in duplicate_authority):
            errors.append(
                f"{_display_path(skill_file)}: duplicates Profile-owned Layer 3 load authority"
            )
        if not expected:
            if layer3_root.exists():
                errors.append(
                    f"{_display_path(skill_root)}: empty compiled mapping must not emit Layer 3 references"
                )
            continue
        if "`references/layer3/<name>.md`" not in skill_text:
            errors.append(
                f"{_display_path(skill_file)}: missing compiled Layer 3 physical mapping"
            )

        index_path = layer3_root / "index.md"
        index_text = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
        links = re.findall(
            r"^- \[([a-z0-9-]+)\]\(([a-z0-9-]+\.md)\)$",
            index_text,
            flags=re.MULTILINE,
        )
        linked_names = [linked_name for linked_name, _target in links]
        if linked_names != expected:
            errors.append(
                f"{_display_path(index_path)}: linked candidates {linked_names} do not match manifest {expected}"
            )
        if "- Trigger:" in index_text or "- Do not load:" in index_text:
            errors.append(
                f"{_display_path(index_path)}: discovery index must not embed trigger catalogs"
            )
        if len(index_text.encode("utf-8")) > 4096:
            errors.append(
                f"{_display_path(index_path)}: discovery index exceeds compact 4096-byte limit"
            )
        for linked_name, target in links:
            if target != f"{linked_name}.md":
                errors.append(
                    f"{_display_path(index_path)}: {linked_name} must link exactly to {linked_name}.md"
                )
        actual_files = {
            path.stem
            for path in layer3_root.glob("*.md")
            if path.name != "index.md"
        } if layer3_root.is_dir() else set()
        if actual_files != set(expected):
            errors.append(
                f"{_display_path(layer3_root)}: compiled files {sorted(actual_files)} do not match manifest {sorted(expected)}"
            )
        for candidate in expected:
            if candidate in foundation_names:
                layer = "foundation"
            elif candidate in domain_names:
                layer = "domain"
            else:
                errors.append(
                    f"{_display_path(manifest_path)}: compiled candidate {candidate!r} "
                    "is outside the Foundation and Domain inventories"
                )
                continue
            _validate_compiled_layer3_projection(
                layer3_root / f"{candidate}.md",
                candidate,
                layer,
                errors,
            )


def _validate_compiled_layer3_projection(
    path: Path,
    candidate: str,
    layer: str,
    errors: list[str],
) -> None:
    """Validate the exact ai-consumption-v1 section projection."""

    expected_headings = {
        "foundation": [
            "Decision Boundary",
            "High-Value Rules",
            "Anti-Patterns",
            "Stop Conditions",
        ],
        "domain": [
            "Decision Boundary",
            "Professional Decision Rules",
            "High-Value Gotchas",
            "Stop / Escalation Conditions",
        ],
    }.get(layer)
    if expected_headings is None:
        errors.append(f"{_display_path(path)}: unsupported Layer 3 layer {layer!r}")
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{_display_path(path)}: missing compiled Layer 3 projection: {exc}")
        return

    validate_ai_readability(text, _display_path(path), errors)

    h1_titles: list[str] = []
    h2_headings: list[str] = []
    for _line_no, line in _without_fenced_code(text):
        h1_match = re.fullmatch(r"#(?!#)[ \t]+(.+?)[ \t]*", line)
        if h1_match:
            h1_titles.append(h1_match.group(1).strip())
            continue
        h2_match = re.fullmatch(r"##(?!#)[ \t]+(.+?)[ \t]*", line)
        if h2_match:
            h2_headings.append(h2_match.group(1).strip())
    if h1_titles != [candidate]:
        errors.append(
            f"{_display_path(path)}: compiled projection H1 titles {h1_titles} "
            f"must equal [{candidate!r}]"
        )
    if h2_headings != expected_headings:
        errors.append(
            f"{_display_path(path)}: {layer} compiled projection headings "
            f"{h2_headings} must equal {expected_headings}"
        )
    if "## Targeted References" in text:
        errors.append(
            f"{_display_path(path)}: compact compiled projection must not repeat "
            "the source Targeted References table"
        )
    for forbidden in (
        "## JIT Reference Delivery",
        "Current-Professional JIT",
        "engineering-control-plane/references/selectors/",
        "never select/reroute/preload",
        "index/catalog",
    ):
        if forbidden in text:
            errors.append(
                f"{_display_path(path)}: Layer 3 JIT/control policy is forbidden: "
                f"{forbidden!r}"
            )
    decision_match = re.search(
        r"(?ms)^## Decision Boundary[ \t]*\n(?P<body>.*?)(?=^## |\Z)",
        text,
    )
    if decision_match is None or not decision_match.group("body").strip():
        errors.append(
            f"{_display_path(path)}: compiled projection needs a non-empty "
            "Decision Boundary"
        )
    professional = path.parents[2].name
    profile_root = path.parents[3]
    _validate_selector_reference_reachability(
        profile_root,
        professional,
        candidate,
        path.parent / candidate,
        errors,
    )


def _load_complete_selector_projection(
    selector_path: Path,
    errors: list[str],
) -> dict[str, object] | None:
    try:
        selector = json.loads(selector_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            f"{_display_path(selector_path)}: missing or invalid current-Professional "
            f"selector projection: {exc}"
        )
        return None
    if not isinstance(selector, dict):
        errors.append(
            f"{_display_path(selector_path)}: selector projection must be a mapping"
        )
        return None
    if (
        selector.get("contract")
        == "changeforge.layer3-selector-decision-envelope/v1"
    ):
        complete = selector.get("complete")
        if not isinstance(complete, dict) or not isinstance(
            complete.get("path"), str
        ):
            errors.append(
                f"{_display_path(selector_path)}: selector decision fallback is invalid"
            )
            return None
        complete_path = selector_path.parent / complete["path"]
        try:
            complete_document = json.loads(
                complete_path.read_text(encoding="utf-8")
            )
            decisions = selector.get("decisions")
            if not isinstance(decisions, list) or not decisions:
                raise ValidationProblem("selector decision bindings are unavailable")
            fallback_key = copy.deepcopy(decisions[0].get("runtime_key"))
            if not isinstance(fallback_key, dict) or not isinstance(
                fallback_key.get("route_source"), dict
            ):
                raise ValidationProblem("selector runtime key is unavailable")
            fallback_key["route_source"]["pointer"] = (
                "#built-reference-link-validation-complete-fallback"
            )
            resolution = layer3_selector_resolve_control_projection(
                selector,
                {complete["path"]: complete_document},
                runtime_key=fallback_key,
            )
        except (OSError, json.JSONDecodeError, ValidationProblem) as exc:
            errors.append(
                f"{_display_path(selector_path)}: selector complete fallback failed closed: {exc}"
            )
            return None
        for decision in selector.get("decisions", []):
            if not isinstance(decision, dict) or not isinstance(
                decision.get("path"), str
            ):
                errors.append(
                    f"{_display_path(selector_path)}: selector decision binding is invalid"
                )
                return None
            decision_path = selector_path.parent / decision["path"]
            try:
                decision_document = json.loads(
                    decision_path.read_text(encoding="utf-8")
                )
                layer3_selector_resolve_control_projection(
                    selector,
                    {decision["path"]: decision_document},
                    runtime_key=decision.get("runtime_key"),
                )
            except (OSError, json.JSONDecodeError, ValidationProblem) as exc:
                errors.append(
                    f"{_display_path(decision_path)}: selector decision failed closed: {exc}"
                )
                return None
        selector = resolution["projection"]
    return selector


def _validate_selector_reference_reachability(
    profile_root: Path,
    professional: str,
    candidate: str,
    physical_root: Path,
    errors: list[str],
    *,
    selector: dict[str, object] | None = None,
) -> bool:
    selector_path = (
        profile_root
        / "engineering-control-plane"
        / "references"
        / "selectors"
        / f"{professional}.json"
    )
    if selector is None:
        selector = _load_complete_selector_projection(selector_path, errors)
    if selector is None:
        return False
    partition_link = selector.get("reference_records_partition")
    if (
        selector.get("professional_skill") != professional
        or not isinstance(partition_link, dict)
        or partition_link.get("contract")
        != "changeforge.layer3-selector-reference-records-partition/v1"
        or not isinstance(partition_link.get("path_template"), str)
    ):
        errors.append(
            f"{_display_path(selector_path)}: selector owner or Reference partition template is invalid"
        )
        return False
    partitions: dict[str, dict[str, object]] = {}
    for owner in (professional, candidate):
        partition_path = selector_path.parent / partition_link["path_template"].format(
            owner_skill=owner
        )
        try:
            partition = json.loads(partition_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                f"{_display_path(partition_path)}: missing or invalid current-Professional "
                f"Reference partition: {exc}"
            )
            return False
        partitions[owner] = partition
    surfaces = selector.get("owner_surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append(
            f"{_display_path(selector_path)}: normalized selector owner surfaces are invalid"
        )
        return False
    observed_records: dict[tuple[str, str], dict[str, object]] = {}
    authorized = False
    for surface in surfaces:
        profile = surface.get("profile") if isinstance(surface, dict) else ""
        profile_authority = selector.get("profile_authority")
        matching_profiles = [
            row
            for row in profile_authority
            if isinstance(row, dict) and row.get("profile") == profile
        ] if isinstance(profile_authority, list) else []
        if len(matching_profiles) != 1:
            errors.append(
                f"{_display_path(selector_path)}: selector Profile authority is invalid"
            )
            continue
        if candidate not in matching_profiles[0].get("authorized_layer3", []):
            continue
        authorized = True
        try:
            expanded = layer3_selector_expand_runtime_projection(
                selector,
                partitions,
                profile=profile,
                selection_owner=(
                    surface.get("selection_owner")
                    if isinstance(surface, dict)
                    else ""
                ),
                exact_layer3=None,
                selected_layer3=[candidate],
                exact_references=None,
            )
        except ValidationProblem as exc:
            errors.append(
                f"{_display_path(selector_path)}: selector expansion failed closed: {exc}"
            )
            continue
        for record in expanded["reference_records"]:
            if not isinstance(record, dict) or record.get("owner_skill") != candidate:
                continue
            record_path = record.get("path")
            outputs = record.get("required_output")
            if (
                not isinstance(record_path, str)
                or not record_path
                or record.get("type") == "index"
                or not isinstance(outputs, list)
                or not outputs
                or not all(isinstance(output, str) and output for output in outputs)
            ):
                errors.append(
                    f"{_display_path(selector_path)}: {candidate} Reference record "
                    "has an invalid path, type, or required output"
                )
                continue
            identity = (candidate, record_path)
            previous = observed_records.get(identity)
            if previous is not None and previous != record:
                errors.append(
                    f"{_display_path(selector_path)}: {candidate} Reference record "
                    f"{record_path!r} differs across role surfaces"
                )
            observed_records[identity] = record
            physical = physical_root / record_path
            if not physical.is_file():
                errors.append(
                    f"{_display_path(selector_path)}: {candidate} Reference record "
                    f"{record_path!r} has no compiled physical file"
                )
    return authorized


def _expected_source_compiled_mapping() -> dict[str, list[str]]:
    professional_data = load_yaml_file(
        ROOT / "src/registry/professional-skills.yaml"
    )
    foundation_data = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain_data = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    professionals = professional_data.get("professional_skills")
    foundations = foundation_data.get("foundation_skills")
    domains = domain_data.get("domain_skills")
    if not all(isinstance(value, list) for value in (professionals, foundations, domains)):
        raise ValidationProblem("source Skill registries must contain list inventories")
    product_foundation_names = {
        str(entry.get("name"))
        for entry in foundations
        if isinstance(entry, dict) and entry.get("delivery_scope") == "product"
    }
    domain_names = {
        str(entry.get("name")) for entry in domains if isinstance(entry, dict)
    }
    allowed = product_foundation_names | domain_names
    result: dict[str, list[str]] = {}
    for entry in professionals:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ValidationProblem("source Professional registry entry is malformed")
        candidates = entry.get("layer3_candidates")
        if not isinstance(candidates, list) or not all(
            isinstance(candidate, str) and candidate for candidate in candidates
        ):
            raise ValidationProblem(
                f"{entry['name']}: source layer3_candidates must be a string list"
            )
        selected = [candidate for candidate in candidates if candidate in allowed]
        result[entry["name"]] = selected
    return result


def _source_compiled_mapping_errors(
    professional_names: list[str],
    compiled: dict[str, object],
    label: str,
) -> list[str]:
    try:
        expected = _expected_source_compiled_mapping()
    except ValidationProblem as exc:
        return [f"{label}: cannot derive source Layer 3 mapping: {exc}"]
    errors: list[str] = []
    if len(expected) != EXPECTED_PROFESSIONAL_SKILL_COUNT:
        errors.append(
            f"{label}: source Professional inventory must contain "
            f"{EXPECTED_PROFESSIONAL_SKILL_COUNT} Skills"
        )
    if set(professional_names) != set(expected):
        errors.append(
            f"{label}: manifest Professional inventory does not match source Registry"
        )
    for name in sorted(set(professional_names) & set(expected)):
        actual = compiled.get(name)
        if isinstance(actual, list) and actual != expected[name]:
            errors.append(
                f"{label}: {name} compiled Layer 3 mapping does not match source "
                f"Registry; expected={expected[name]}, actual={actual}"
            )
    return errors


def _validate_rendered_professional_body(
    skill_file: Path,
    errors: list[str],
) -> None:
    if not skill_file.is_file():
        errors.append(f"{_display_path(skill_file)}: missing rendered Professional SKILL.md")
        return
    try:
        _metadata, _raw_frontmatter, body = parse_frontmatter(skill_file)
    except ValidationProblem as exc:
        errors.append(
            f"{_display_path(skill_file)}: invalid rendered Professional SKILL.md: {exc}"
        )
        return
    line_count = len(body.splitlines())
    if line_count > MAX_RENDERED_PROFESSIONAL_BODY_LINES:
        errors.append(
            f"{_display_path(skill_file)}: rendered Professional SKILL.md body has "
            f"{line_count} lines; maximum is {MAX_RENDERED_PROFESSIONAL_BODY_LINES}"
        )
    skill_name = skill_file.parent.name
    selector_path = (
        "engineering-control-plane/references/selectors/"
        f"{skill_name}.json"
    )
    if (
        body.count("## JIT Reference Delivery") != 1
        or body.count(selector_path) != 1
    ):
        errors.append(
            f"{_display_path(skill_file)}: rendered root must contain exactly one "
            "Professional JIT Reference Delivery and selector path"
        )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Runtime Markdown links and complete Layer 3 proofs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_BUILT_ROOT,
        help="Built Skills root containing the recommended Runtime directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root if args.root.is_absolute() else ROOT / args.root
    errors: list[str] = []
    _validate_runtime(root / RUNTIME_NAME, errors)
    complete_layer3 = _validate_complete_layer3_temporary_projection(errors)
    if errors:
        return fail_many("validate-built-skill-reference-links", errors)
    print(
        "validate-built-skill-reference-links: validated local Markdown links in "
        + RUNTIME_NAME
        + f" and {complete_layer3['projected_count']} temporary Layer 3 projections."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
