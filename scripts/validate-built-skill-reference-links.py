#!/usr/bin/env python3
"""Validate local Markdown links in built Skill profiles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    FOUNDATION_DELIVERY_SCOPES,
    ValidationProblem,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    relpath,
    validate_ai_readability,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILT_ROOT = ROOT / "dist" / "universal" / "skills"
PROFILES = ("recommended", "full", "dev")
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


def _validate_profile(
    profile_root: Path,
    errors: list[str],
    *,
    enforce_source_mapping: bool = True,
) -> None:
    if not profile_root.is_dir():
        errors.append(f"{_display_path(profile_root)}: missing built profile")
        return
    markdown_files = sorted(profile_root.rglob("*.md"))
    if not markdown_files:
        errors.append(f"{_display_path(profile_root)}: no Markdown files found")
        return
    for markdown_file in markdown_files:
        for line_no, target, root_relative in _iter_local_targets(markdown_file):
            if not _target_exists(markdown_file, profile_root, target, root_relative):
                errors.append(
                    f"{_display_path(markdown_file)}:{line_no}: "
                    f"missing local built Skill reference '{target}'"
                )
    _validate_compiled_layer3_entrypoints(
        profile_root,
        errors,
        enforce_source_mapping=enforce_source_mapping,
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

    profile = str(manifest.get("profile") or "")
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
    expected_compiled_foundation = (
        set() if profile == "dev" else product_foundation_names
    )
    if set(compiled_foundation) != expected_compiled_foundation:
        errors.append(
            f"{_display_path(manifest_path)}: compiled Foundation list does not match "
            f"the {profile} product delivery contract"
        )
    if profile in {"recommended", "full"} and top_names & foundation_names:
        errors.append(
            f"{_display_path(manifest_path)}: {profile} exposes Foundation Skills at top level"
        )
    if profile == "recommended" and top_names & domain_names:
        errors.append(
            f"{_display_path(manifest_path)}: recommended exposes Domain Skills at top level"
        )
    if profile == "full" and not domain_names <= top_names:
        errors.append(
            f"{_display_path(manifest_path)}: full must expose every Domain Skill at top level"
        )
    if profile == "dev" and not (foundation_names | domain_names) <= top_names:
        errors.append(
            f"{_display_path(manifest_path)}: dev must expose every Foundation and Domain Skill at top level"
        )

    professional_names = [str(name) for name in professional]
    if set(compiled) != set(professional_names):
        errors.append(
            f"{_display_path(manifest_path)}: compiled Layer 3 mapping must cover exactly all Professional Skills"
        )
    if enforce_source_mapping:
        errors.extend(
            _source_compiled_mapping_errors(
                profile,
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
        if profile == "full" and set(expected) & domain_names:
            errors.append(
                f"{_display_path(manifest_path)}: {name} duplicates top-level Domain Skills in compiled references"
            )
        if profile == "dev" and expected:
            errors.append(
                f"{_display_path(manifest_path)}: {name} must use top-level Layer 3 Skills without compiled references in dev"
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
        if profile == "recommended":
            expected_delivery = (
                "Foundation and Domain items are compiled at "
                "`references/layer3/<name>.md`."
                if expected
                else "No Foundation or Domain Layer 3 items are assigned to this Skill."
            )
        elif profile == "full":
            expected_delivery = (
                "Foundation items are compiled at `references/layer3/<name>.md`; "
                "Domain items are top-level Skills."
                if expected
                else "Domain items are top-level Skills; no Foundation items are "
                "compiled for this Skill."
            )
        elif profile == "dev":
            expected_delivery = (
                "Foundation and Domain items are top-level Skills; no Layer 3 "
                "references are compiled."
            )
        else:
            expected_delivery = ""
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
            "JIT Reference Delivery",
        ],
        "domain": [
            "Decision Boundary",
            "Professional Decision Rules",
            "High-Value Gotchas",
            "Stop / Escalation Conditions",
            "JIT Reference Delivery",
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
    selector_anchor = "Current-Professional JIT"
    if text.count(selector_anchor) != 1:
        errors.append(
            f"{_display_path(path)}: compact compiled projection must contain "
            "exactly one current-Professional selector anchor"
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
    selector_path = (
        profile_root
        / "engineering-control-plane"
        / "references"
        / "selectors"
        / f"{professional}.json"
    )
    try:
        selector = json.loads(selector_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            f"{_display_path(path)}: missing or invalid current-Professional "
            f"selector projection: {exc}"
        )
        return
    surfaces = selector.get("selection_surfaces")
    if (
        selector.get("professional_skill") != professional
        or not isinstance(surfaces, list)
        or not surfaces
    ):
        errors.append(
            f"{_display_path(selector_path)}: selector owner or surfaces are invalid"
        )
        return
    observed_records: dict[tuple[str, str], dict[str, object]] = {}
    for surface in surfaces:
        records = surface.get("reference_records") if isinstance(surface, dict) else None
        if not isinstance(records, list):
            errors.append(
                f"{_display_path(selector_path)}: selector surface lacks Reference records"
            )
            continue
        for record in records:
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
            physical = path.parent / candidate / record_path
            if not physical.is_file():
                errors.append(
                    f"{_display_path(selector_path)}: {candidate} Reference record "
                    f"{record_path!r} has no compiled physical file"
                )


def _expected_source_compiled_mapping(profile: str) -> dict[str, list[str]]:
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
        if profile == "recommended":
            result[entry["name"]] = selected
        elif profile == "full":
            result[entry["name"]] = [
                candidate for candidate in selected if candidate not in domain_names
            ]
        elif profile == "dev":
            result[entry["name"]] = []
        else:
            raise ValidationProblem(f"unsupported build profile {profile!r}")
    return result


def _source_compiled_mapping_errors(
    profile: str,
    professional_names: list[str],
    compiled: dict[str, object],
    label: str,
) -> list[str]:
    try:
        expected = _expected_source_compiled_mapping(profile)
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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate local Markdown links in built Skill profiles."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_BUILT_ROOT,
        help="Built Skills root containing profile directories.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        choices=PROFILES,
        help="Profile to validate. May be passed multiple times. Defaults to all profiles.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root if args.root.is_absolute() else ROOT / args.root
    profiles = tuple(args.profile or PROFILES)
    errors: list[str] = []
    for profile in profiles:
        _validate_profile(root / profile, errors)
    if errors:
        return fail_many("validate-built-skill-reference-links", errors)
    print(
        "validate-built-skill-reference-links: validated local Markdown links in "
        + ", ".join(profiles)
        + "."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
