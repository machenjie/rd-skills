#!/usr/bin/env python3
"""Package built ChangeForge runtime skills for hosted runtimes."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from validation_utils import validate_no_personal_references


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SKILLS_ROOT = ROOT / "dist" / "universal" / "skills"
ZIP_DIR = ROOT / "dist" / "openai-api" / "zips"
PROFILES = ("recommended", "full", "dev")
ZIP_TIMESTAMP = (2024, 1, 1, 0, 0, 0)
MAX_ZIP_FILES = 500
MAX_ZIP_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILE_BYTES = 2 * 1024 * 1024


class PackageError(Exception):
    """Raised when a built skill cannot be packaged safely."""


def main() -> int:
    parser = argparse.ArgumentParser(description="Package ChangeForge skills as zip bundles.")
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

    source_root = args.source if args.source is not None else RUNTIME_SKILLS_ROOT / args.profile

    zip_dir = args.zip_dir
    if zip_dir.resolve() == ZIP_DIR.resolve():
        _cleanup_legacy_zips(ZIP_DIR)
        zip_dir = ZIP_DIR / args.profile

    try:
        zip_count = package_profile(source_root, zip_dir)
    except PackageError as exc:
        print(f"package: ERROR: {exc}", file=sys.stderr)
        return 1

    if zip_count == 0:
        print(f"package: no built runtime skills found in {source_root}; nothing to package.")
        return 0

    print(f"package: packaged {zip_count} skill zip(s) from {source_root} into {zip_dir}.")
    return 0


def package_profile(source_root: Path, zip_dir: Path = ZIP_DIR) -> int:
    zip_dir.mkdir(parents=True, exist_ok=True)
    for stale_zip in zip_dir.glob("*.zip"):
        stale_zip.unlink()

    if not source_root.exists():
        return 0

    skill_dirs = [
        path
        for path in sorted(source_root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]

    for skill_dir in skill_dirs:
        _validate_zip_source(skill_dir)
        _write_skill_zip(skill_dir, zip_dir / f"{skill_dir.name}.zip")

    _validate_written_zips(zip_dir)
    return len(skill_dirs)


def _cleanup_legacy_zips(zip_root: Path) -> None:
    zip_root.mkdir(parents=True, exist_ok=True)
    for stale_zip in zip_root.glob("*.zip"):
        stale_zip.unlink()


def _validate_zip_source(skill_dir: Path) -> None:
    files = [path for path in sorted(skill_dir.rglob("*")) if path.is_file()]
    if len(files) > MAX_ZIP_FILES:
        raise PackageError(
            f"{skill_dir.relative_to(ROOT)} has {len(files)} files; max is {MAX_ZIP_FILES}"
        )
    if not (skill_dir / "SKILL.md").is_file():
        raise PackageError(f"{skill_dir.relative_to(ROOT)} is missing root SKILL.md")
    skill_md_files = [path for path in files if path.name == "SKILL.md"]
    if skill_md_files != [skill_dir / "SKILL.md"]:
        raise PackageError(f"{skill_dir.relative_to(ROOT)} must contain exactly one SKILL.md")

    total_size = 0
    for file_path in files:
        relative = file_path.relative_to(ROOT)
        errors: list[str] = []
        validate_no_personal_references(relative.as_posix(), relative.as_posix(), errors)
        if errors:
            raise PackageError("; ".join(errors))

        size = file_path.stat().st_size
        if size > MAX_ZIP_FILE_BYTES:
            raise PackageError(
                f"{relative} is {size} bytes; max is {MAX_ZIP_FILE_BYTES}"
            )
        total_size += size

    if total_size > MAX_ZIP_BYTES:
        raise PackageError(
            f"{skill_dir.relative_to(ROOT)} is {total_size} bytes; max is {MAX_ZIP_BYTES}"
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
        with zipfile.ZipFile(zip_path) as archive:
            names = [name for name in archive.namelist() if name and not name.endswith("/")]
            top_levels = {name.split("/", 1)[0] for name in names}
            if len(top_levels) != 1:
                raise PackageError(f"{zip_path.relative_to(ROOT)} has multiple top-level folders")
            top_level = next(iter(top_levels))
            if any("/" not in name for name in names):
                raise PackageError(f"{zip_path.relative_to(ROOT)} contains top-level files")
            skill_md_entries = [name for name in names if name.endswith("/SKILL.md")]
            if skill_md_entries != [f"{top_level}/SKILL.md"]:
                raise PackageError(
                    f"{zip_path.relative_to(ROOT)} must contain exactly one root SKILL.md"
                )
            if len(names) > MAX_ZIP_FILES:
                raise PackageError(
                    f"{zip_path.relative_to(ROOT)} has {len(names)} files; max is {MAX_ZIP_FILES}"
                )
            total_size = sum(archive.getinfo(name).file_size for name in names)
            if total_size > MAX_ZIP_BYTES:
                raise PackageError(
                    f"{zip_path.relative_to(ROOT)} is {total_size} bytes; max is {MAX_ZIP_BYTES}"
                )


if __name__ == "__main__":
    raise SystemExit(main())
