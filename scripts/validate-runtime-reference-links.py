#!/usr/bin/env python3
"""Validate local Markdown reference links in built runtime profiles."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from validation_utils import fail_many, relpath


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_ROOT = ROOT / "dist" / "universal" / "skills"
PROFILES = ("recommended", "full", "dev")

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
                targets.append((line_no, target, False))
        ref_match = REFERENCE_LINK_RE.match(line)
        if ref_match:
            target = _normalize_target(ref_match.group(1))
            if target is not None:
                targets.append((line_no, target, False))
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


def _validate_profile(profile_root: Path, errors: list[str]) -> None:
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
                    f"missing local runtime reference '{target}'"
                )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate local Markdown links in built runtime profiles."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_RUNTIME_ROOT,
        help="Runtime skills root containing profile directories.",
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
        return fail_many("validate-runtime-reference-links", errors)
    print(
        "validate-runtime-reference-links: validated local Markdown links in "
        + ", ".join(profiles)
        + "."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
