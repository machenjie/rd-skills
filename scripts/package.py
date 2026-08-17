#!/usr/bin/env python3
"""Package built rd-skills Skills for hosted agent surfaces."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from validation_utils import (
    NAME_RE,
    authoritative_build_input_snapshot_errors,
    validate_no_personal_references,
)


ROOT = Path(__file__).resolve().parents[1]
BUILT_SKILLS_ROOT = ROOT / "dist" / "universal" / "skills"
ZIP_DIR = ROOT / "dist" / "openai-api" / "zips"
PROFILES = ("recommended", "full", "dev")
ZIP_TIMESTAMP = (2024, 1, 1, 0, 0, 0)
MAX_ZIP_FILES = 500
MAX_ZIP_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILE_BYTES = 2 * 1024 * 1024


class PackageError(Exception):
    """Raised when a built skill cannot be packaged safely."""


def main() -> int:
    parser = argparse.ArgumentParser(description="Package rd-skills skills as zip bundles.")
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="recommended",
        help="Built profile to package.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Optional built profile skills directory. Defaults to dist/universal/skills/<profile>.",
    )
    parser.add_argument(
        "--zip-dir",
        type=Path,
        default=ZIP_DIR,
        help="Output directory for OpenAI API compatible zips.",
    )
    args = parser.parse_args()

    source_root = (
        args.source if args.source is not None else BUILT_SKILLS_ROOT / args.profile
    ).expanduser().absolute()

    zip_dir = args.zip_dir.expanduser().absolute()
    default_output = zip_dir == ZIP_DIR.expanduser().absolute()
    if default_output:
        zip_dir = ZIP_DIR / args.profile

    try:
        zip_count = package_profile(
            source_root,
            zip_dir,
            require_build_manifest=args.source is None,
        )
        if default_output and zip_count:
            _cleanup_legacy_zips(ZIP_DIR)
    except PackageError as exc:
        print(f"package: ERROR: {exc}", file=sys.stderr)
        return 1

    if zip_count == 0:
        print(f"package: no built Skills found in {source_root}; nothing to package.")
        return 0

    print(f"package: packaged {zip_count} skill zip(s) from {source_root} into {zip_dir}.")
    return 0


def package_profile(
    source_root: Path,
    zip_dir: Path = ZIP_DIR,
    *,
    require_build_manifest: bool = False,
) -> int:
    source_root = source_root.expanduser().absolute()
    zip_dir = zip_dir.expanduser().absolute()

    # Validate lexical path chains before resolve() or mkdir(). Resolving first
    # would hide an ancestor symlink and could redirect writes outside the
    # requested output tree.
    _reject_symlink_chain(source_root, "built source")
    _reject_symlink_chain(zip_dir, "zip output")
    if _paths_overlap(source_root, zip_dir):
        raise PackageError(
            f"source/output overlap is forbidden: {_display(source_root)} and {_display(zip_dir)}"
        )

    if not source_root.exists():
        return 0
    if source_root.is_symlink() or not source_root.is_dir():
        raise PackageError(f"{_display(source_root)} must be a regular built profile directory")
    _reject_tree_symlinks(source_root, "built source tree")
    _validate_build_manifest_freshness(
        source_root,
        require_manifest=require_build_manifest,
    )

    skill_dirs = [
        path
        for path in sorted(source_root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]

    if not skill_dirs:
        return 0

    for skill_dir in skill_dirs:
        if skill_dir.is_symlink():
            raise PackageError(f"{_display(skill_dir)} must not be a symlink")
        if not NAME_RE.fullmatch(skill_dir.name):
            raise PackageError(f"{_display(skill_dir)} must use a safe Skill name")
        _validate_zip_source(skill_dir)

    expected_zip_names = {f"{skill_dir.name}.zip" for skill_dir in skill_dirs}
    if zip_dir.exists():
        if zip_dir.is_symlink() or not zip_dir.is_dir():
            raise PackageError(f"{_display(zip_dir)} must be a regular output directory")
        _reject_tree_symlinks(zip_dir, "zip output tree")
        unexpected = sorted(
            path.name
            for path in zip_dir.glob("*.zip")
            if path.name not in expected_zip_names
        )
        if unexpected:
            raise PackageError(
                f"{_display(zip_dir)} contains unrelated zip files: {', '.join(unexpected)}"
            )

    for name in sorted(expected_zip_names):
        stale_zip = zip_dir / name
        if stale_zip.is_symlink():
            raise PackageError(f"{_display(stale_zip)} must not be a symlink")

    # Build and validate every archive outside the managed output. Existing
    # zips remain byte-for-byte untouched if any source or archive check fails.
    with tempfile.TemporaryDirectory(prefix="changeforge-package-") as raw:
        staging = Path(raw)
        for skill_dir in skill_dirs:
            _write_skill_zip(skill_dir, staging / f"{skill_dir.name}.zip")
        _validate_written_zips(staging)

        zip_dir.mkdir(parents=True, exist_ok=True)
        for name in sorted(expected_zip_names):
            os.replace(staging / name, zip_dir / name)

    return len(skill_dirs)


def _validate_build_manifest_freshness(
    source_root: Path,
    *,
    require_manifest: bool,
) -> None:
    manifest_path = source_root / ".changeforge-build-manifest.json"
    if not manifest_path.is_file():
        if require_manifest:
            raise PackageError(
                f"{_display(source_root)} is missing .changeforge-build-manifest.json"
            )
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"{_display(manifest_path)} is invalid: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PackageError(f"{_display(manifest_path)} must contain a JSON object")
    try:
        errors = authoritative_build_input_snapshot_errors(
            manifest.get("authoritative_build_inputs"),
            ROOT,
        )
    except (OSError, ValueError) as exc:
        raise PackageError(
            f"cannot compare {_display(manifest_path)} with authoritative inputs: {exc}"
        ) from exc
    if errors:
        raise PackageError(f"{_display(manifest_path)}: {'; '.join(errors)}")


def _cleanup_legacy_zips(zip_root: Path) -> None:
    zip_root = zip_root.expanduser().absolute()
    _reject_symlink_chain(zip_root, "legacy zip root")
    zip_root.mkdir(parents=True, exist_ok=True)
    managed_names: set[str] = set()
    for profile in PROFILES:
        manifest = BUILT_SKILLS_ROOT / profile / ".changeforge-build-manifest.json"
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        managed_names.update(
            f"{name}.zip"
            for name in data.get("top_level_skills", [])
            if isinstance(name, str) and NAME_RE.fullmatch(name)
        )
    for stale_zip in zip_root.glob("*.zip"):
        if stale_zip.name in managed_names and not stale_zip.is_symlink():
            stale_zip.unlink()


def _validate_zip_source(skill_dir: Path) -> None:
    symlinks = [path for path in sorted(skill_dir.rglob("*")) if path.is_symlink()]
    if symlinks:
        raise PackageError(f"{_display(symlinks[0])} must not be a symlink")
    files = [path for path in sorted(skill_dir.rglob("*")) if path.is_file()]
    if len(files) > MAX_ZIP_FILES:
        raise PackageError(
            f"{_display(skill_dir)} has {len(files)} files; max is {MAX_ZIP_FILES}"
        )
    if not (skill_dir / "SKILL.md").is_file():
        raise PackageError(f"{_display(skill_dir)} is missing root SKILL.md")
    skill_md_files = [path for path in files if path.name == "SKILL.md"]
    if skill_md_files != [skill_dir / "SKILL.md"]:
        raise PackageError(f"{_display(skill_dir)} must contain exactly one SKILL.md")

    total_size = 0
    for file_path in files:
        relative = file_path.relative_to(skill_dir)
        errors: list[str] = []
        validate_no_personal_references(
            relative.as_posix(),
            f"{skill_dir.name}/{relative.as_posix()}",
            errors,
        )
        if errors:
            raise PackageError("; ".join(errors))

        size = file_path.stat().st_size
        if size > MAX_ZIP_FILE_BYTES:
            raise PackageError(
                f"{_display(file_path)} is {size} bytes; max is {MAX_ZIP_FILE_BYTES}"
            )
        total_size += size

    if total_size > MAX_ZIP_BYTES:
        raise PackageError(
            f"{_display(skill_dir)} is {total_size} bytes; max is {MAX_ZIP_BYTES}"
        )


def _write_skill_zip(skill_dir: Path, zip_path: Path) -> None:
    files = [path for path in sorted(skill_dir.rglob("*")) if path.is_file()]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            relative_path = file_path.relative_to(skill_dir)
            archive_name = f"{skill_dir.name}/{relative_path.as_posix()}"
            info = zipfile.ZipInfo(archive_name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, file_path.read_bytes())


def _validate_written_zips(zip_dir: Path) -> None:
    for zip_path in sorted(zip_dir.glob("*.zip")):
        try:
            archive = zipfile.ZipFile(zip_path)
        except (OSError, zipfile.BadZipFile) as exc:
            raise PackageError(f"{_display(zip_path)} is not a readable zip: {exc}") from exc
        with archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise PackageError(f"{_display(zip_path)} contains corrupt member {corrupt!r}")
            names = [name for name in archive.namelist() if name and not name.endswith("/")]
            for name in names:
                parts = PurePosixPath(name).parts
                if "\\" in name or not parts or any(part in {"", ".", ".."} for part in parts):
                    raise PackageError(f"{_display(zip_path)} contains unsafe member {name!r}")
            top_levels = {name.split("/", 1)[0] for name in names}
            if len(top_levels) != 1:
                raise PackageError(f"{_display(zip_path)} has multiple top-level folders")
            top_level = next(iter(top_levels))
            if any("/" not in name for name in names):
                raise PackageError(f"{_display(zip_path)} contains top-level files")
            skill_md_entries = [name for name in names if name.endswith("/SKILL.md")]
            if skill_md_entries != [f"{top_level}/SKILL.md"]:
                raise PackageError(
                    f"{_display(zip_path)} must contain exactly one root SKILL.md"
                )
            if len(names) > MAX_ZIP_FILES:
                raise PackageError(
                    f"{_display(zip_path)} has {len(names)} files; max is {MAX_ZIP_FILES}"
                )
            total_size = sum(archive.getinfo(name).file_size for name in names)
            if total_size > MAX_ZIP_BYTES:
                raise PackageError(
                    f"{_display(zip_path)} is {total_size} bytes; max is {MAX_ZIP_BYTES}"
                )


def _reject_symlink_chain(path: Path, label: str) -> None:
    absolute = path.expanduser().absolute()
    anchor = Path(absolute.anchor)
    cursor = anchor
    if cursor.is_symlink():
        raise PackageError(f"{label} {_display(cursor)} must not be a symlink")
    for part in absolute.parts[1:]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PackageError(f"{label} {_display(cursor)} must not be a symlink")


def _reject_tree_symlinks(root: Path, label: str) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise PackageError(f"{label} {_display(path)} must not be a symlink")


def _paths_overlap(left: Path, right: Path) -> bool:
    left_resolved = left.resolve(strict=False)
    right_resolved = right.resolve(strict=False)
    return (
        left_resolved == right_resolved
        or left_resolved in right_resolved.parents
        or right_resolved in left_resolved.parents
    )


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
