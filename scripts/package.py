#!/usr/bin/env python3
"""Package built rd-skills Skills for hosted agent surfaces."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from validation_utils import (
    NAME_RE,
    RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH,
    authoritative_build_input_snapshot_errors,
    load_yaml_file,
    runtime_asset_bundle_metadata_errors,
    validate_no_personal_references,
)


ROOT = Path(__file__).resolve().parents[1]
BUILT_SKILLS_ROOT = ROOT / "dist" / "universal" / "skills"
ZIP_DIR = ROOT / "dist" / "openai-api" / "zips"
RUNTIME_PROFILE = "recommended"
RETIRED_PROFILES = ("full", "dev")
EXPECTED_RUNTIME_COUNTS = {
    "control": 1,
    "professional": 25,
    "foundation": 150,
    "domain": 13,
}
ZIP_TIMESTAMP = (2024, 1, 1, 0, 0, 0)
MAX_ZIP_FILES = 500
MAX_ZIP_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILE_BYTES = 2 * 1024 * 1024


class PackageError(Exception):
    """Raised when a built skill cannot be packaged safely."""


def main() -> int:
    parser = argparse.ArgumentParser(description="Package rd-skills skills as zip bundles.")
    parser.parse_args()

    try:
        zip_count = package_profile()
    except PackageError as exc:
        print(f"package: ERROR: {exc}", file=sys.stderr)
        return 1

    source_root = BUILT_SKILLS_ROOT / RUNTIME_PROFILE
    zip_dir = ZIP_DIR / RUNTIME_PROFILE
    print(f"package: packaged {zip_count} skill zip(s) from {source_root} into {zip_dir}.")
    return 0


def package_profile() -> int:
    source_root = (BUILT_SKILLS_ROOT / RUNTIME_PROFILE).expanduser().absolute()
    zip_dir = (ZIP_DIR / RUNTIME_PROFILE).expanduser().absolute()

    _preflight_managed_profile_roots()
    _reject_symlink_chain(source_root, "built source")
    _reject_symlink_chain(zip_dir, "zip output")
    if _paths_overlap(source_root, zip_dir):
        raise PackageError(
            f"source/output overlap is forbidden: {_display(source_root)} and {_display(zip_dir)}"
        )

    if not source_root.exists():
        raise PackageError(f"{_display(source_root)} is missing; run scripts/build.py first")
    if source_root.is_symlink() or not source_root.is_dir():
        raise PackageError(f"{_display(source_root)} must be a regular built profile directory")
    _reject_tree_symlinks(source_root, "built source tree")
    manifest = _validate_build_manifest(source_root)

    skill_dirs = [
        path
        for path in sorted(source_root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]

    actual_names = [path.name for path in skill_dirs]
    expected_names = manifest["top_level_skills"]
    expected_children = {*expected_names, ".changeforge-build-manifest.json"}
    actual_children = {path.name for path in source_root.iterdir()}
    if actual_names != sorted(expected_names) or actual_children != expected_children:
        raise PackageError(
            "built Skill names must exactly match the current Runtime manifest"
        )

    for skill_dir in skill_dirs:
        if skill_dir.is_symlink():
            raise PackageError(f"{_display(skill_dir)} must not be a symlink")
        if not NAME_RE.fullmatch(skill_dir.name):
            raise PackageError(f"{_display(skill_dir)} must use a safe Skill name")
        _validate_zip_source(skill_dir)
        if skill_dir.name in set(manifest["professional_skills"]):
            _validate_runtime_bundle(skill_dir, manifest)

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

        _cleanup_retired_profile_outputs()
        zip_dir.mkdir(parents=True, exist_ok=True)
        for name in sorted(expected_zip_names):
            os.replace(staging / name, zip_dir / name)

    return len(skill_dirs)


def _validate_runtime_bundle(
    professional_root: Path,
    manifest: dict[str, object],
) -> None:
    integrity_path = professional_root / RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH
    try:
        integrity_bytes = integrity_path.read_bytes()
        delivery_assets = {
            path.relative_to(professional_root).as_posix(): path.read_bytes()
            for path in sorted(professional_root.rglob("*"))
            if path.is_file() and path != integrity_path
        }
    except OSError as exc:
        raise PackageError(
            f"{_display(professional_root)}: Runtime metadata unavailable: {exc}"
        ) from exc
    source_inputs = manifest.get("authoritative_build_inputs")
    full_digest = (
        source_inputs.get("sha256") if isinstance(source_inputs, dict) else None
    )
    bindings = manifest.get("runtime_asset_bindings")
    binding = (
        bindings.get(professional_root.name) if isinstance(bindings, dict) else None
    )
    errors = runtime_asset_bundle_metadata_errors(
        integrity_bytes,
        delivery_assets,
        binding,
        expected_source_version=str(manifest.get("source_version", "")),
        expected_authoritative_build_inputs_sha256=full_digest,
        expected_professional_skill=professional_root.name,
    )
    if errors:
        raise PackageError(
            f"{_display(professional_root)}: invalid Runtime bundle: "
            + "; ".join(errors)
        )


def _authoritative_runtime_inventory() -> dict[str, object]:
    registries = {
        layer: load_yaml_file(ROOT / "src" / "registry" / filename)[key]
        for layer, filename, key in (
            ("control", "control-skills.yaml", "control_skills"),
            ("professional", "professional-skills.yaml", "professional_skills"),
            ("foundation", "foundation-skills.yaml", "foundation_skills"),
            ("domain", "domain-skills.yaml", "domain_skills"),
        )
    }
    names = {
        layer: [entry.get("name") for entry in entries]
        for layer, entries in registries.items()
    }
    for layer, expected_count in EXPECTED_RUNTIME_COUNTS.items():
        layer_names = names[layer]
        if (
            len(layer_names) != expected_count
            or any(
                not isinstance(name, str) or not NAME_RE.fullmatch(name)
                for name in layer_names
            )
            or len(set(layer_names)) != len(layer_names)
        ):
            raise PackageError(
                f"authoritative {layer} registry must contain exactly "
                f"{expected_count} unique safe Skill names"
            )

    foundation_entries = {
        entry["name"]: entry for entry in registries["foundation"]
    }
    allowed_layer3 = set(names["domain"]) | {
        name
        for name, entry in foundation_entries.items()
        if entry.get("delivery_scope") == "product"
    }
    compiled = {
        entry["name"]: list(
            dict.fromkeys(
                name
                for name in entry.get("layer3_candidates", [])
                if name in allowed_layer3
            )
        )
        for entry in registries["professional"]
    }
    return {
        **names,
        "top_level": [*names["control"], *names["professional"]],
        "compiled": compiled,
    }


def _validate_build_manifest(source_root: Path) -> dict[str, object]:
    manifest_path = source_root / ".changeforge-build-manifest.json"
    if not manifest_path.is_file():
        raise PackageError(
            f"{_display(source_root)} is missing .changeforge-build-manifest.json"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"{_display(manifest_path)} is invalid: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PackageError(f"{_display(manifest_path)} must contain a JSON object")

    inventory = _authoritative_runtime_inventory()
    expected_fields = {
        "profile": RUNTIME_PROFILE,
        "top_level_skills": inventory["top_level"],
        "control_skills": inventory["control"],
        "professional_skills": inventory["professional"],
        "foundation_skills": inventory["foundation"],
        "domain_skills": inventory["domain"],
        "compiled_layer3_references": inventory["compiled"],
        "foundation_mode": "targeted-product-references",
        "domain_mode": "targeted-references",
        "agent_profiles": [
            "main-control-agent",
            "analysis-agent",
            "task-agent",
            "review-agent",
        ],
    }
    for field, expected in expected_fields.items():
        if manifest.get(field) != expected:
            raise PackageError(
                f"{_display(manifest_path)}: {field} does not match the current Runtime"
            )
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
    return manifest


def _managed_profile_roots() -> tuple[Path, Path]:
    return (
        BUILT_SKILLS_ROOT.expanduser().absolute(),
        ZIP_DIR.expanduser().absolute(),
    )


def _retired_profile_output_paths() -> tuple[Path, ...]:
    return tuple(
        root / profile
        for root in _managed_profile_roots()
        for profile in RETIRED_PROFILES
    )


def _preflight_managed_profile_roots() -> None:
    for root in _managed_profile_roots():
        _reject_symlink_chain(root, "managed profile root")
        if root.exists() and (root.is_symlink() or not root.is_dir()):
            raise PackageError(
                f"managed profile root {_display(root)} must be a regular directory"
            )
    for retired in _retired_profile_output_paths():
        _reject_symlink_chain(retired, "retired profile output")
        if retired.exists() and (retired.is_symlink() or not retired.is_dir()):
            raise PackageError(
                f"retired profile output {_display(retired)} must be a regular directory"
            )
        if retired.exists():
            _reject_tree_symlinks(retired, "retired profile output")


def _cleanup_retired_profile_outputs() -> None:
    for path in _retired_profile_output_paths():
        if path.exists():
            shutil.rmtree(path)


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
