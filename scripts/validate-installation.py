#!/usr/bin/env python3
"""Validate hookless build, package, install, upgrade, doctor, and uninstall."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from validation_utils import (
    COMPILED_LAYER3_FORMAT,
    CORE_CONTRACTS,
    CORE_CONTRACTS_PATH,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    authoritative_build_input_snapshot_errors,
    execution_level_runtime_reference_errors,
    fail_many,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
BUILD_MANIFEST = ".changeforge-build-manifest.json"
EVIDENCE_LIMITATIONS = (
    "Simulated local installation does not prove real-host Profile startup or wall-clock performance.",
    "Static Profile and local lifecycle checks do not prove real-host accuracy or the installed user experience.",
)
SKILL_ROOTS = (
    ROOT / "dist" / "universal" / "skills",
    ROOT / "dist" / "codex" / "project" / ".agents" / "skills",
    ROOT / "dist" / "codex" / "user" / ".agents" / "skills",
    ROOT / "dist" / "codex" / "admin" / "skills",
    ROOT / "dist" / "claude" / "project" / ".claude" / "skills",
    ROOT / "dist" / "claude" / "user" / ".claude" / "skills",
    ROOT / "dist" / "copilot" / "project" / ".github" / "skills",
    ROOT / "dist" / "copilot" / "user" / ".copilot" / "skills",
    ROOT / "dist" / "cline" / "project" / ".cline" / "skills",
    ROOT / "dist" / "cline" / "user" / ".cline" / "skills",
)
PROFILE_ROOTS = (
    (ROOT / "dist" / "codex" / "project" / ".codex" / "agents", ".toml"),
    (ROOT / "dist" / "codex" / "user" / ".codex" / "agents", ".toml"),
    (ROOT / "dist" / "codex" / "admin" / "agents", ".toml"),
    (ROOT / "dist" / "claude" / "project" / ".claude" / "agents", ".md"),
    (ROOT / "dist" / "claude" / "user" / ".claude" / "agents", ".md"),
    (ROOT / "dist" / "copilot" / "project" / ".github" / "agents", ".agent.md"),
    (ROOT / "dist" / "copilot" / "user" / ".copilot" / "agents", ".agent.md"),
)
AGENT_PROFILES = {
    "main-control-agent",
    "analysis-agent",
    "task-agent",
    "review-agent",
}


def _expected_core_model_metadata() -> dict[str, object]:
    return {
        "path": CORE_CONTRACTS_PATH.relative_to(ROOT).as_posix(),
        "schema_version": CORE_CONTRACTS["schema_version"],
        "kind": CORE_CONTRACTS["kind"],
        "sha256": hashlib.sha256(CORE_CONTRACTS_PATH.read_bytes()).hexdigest(),
    }


def _build_input_freshness_errors(
    manifest: dict[str, object],
    manifest_path: Path,
    *,
    repository_root: Path = ROOT,
) -> list[str]:
    try:
        errors = authoritative_build_input_snapshot_errors(
            manifest.get("authoritative_build_inputs"),
            repository_root,
        )
    except (OSError, ValueError) as exc:
        errors = [f"cannot compare authoritative build inputs: {exc}"]
    return [f"{manifest_path}: {error}" for error in errors]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-projection", action="store_true")
    args = parser.parse_args(argv)
    errors: list[str] = []
    built_count = _validate_skill_roots(errors)
    profile_count = _validate_profile_roots(errors)
    zip_count = _validate_zips(errors)
    residue_start = len(errors)
    _validate_no_residue(errors)
    residue_count = len(errors) - residue_start
    _validate_cli_surface(errors)
    _validate_install_cycle(errors)
    _write_report(
        errors,
        built_count=built_count,
        profile_count=profile_count,
        zip_count=zip_count,
        residue_count=residue_count,
        release_projection=args.release_projection,
    )
    if errors:
        return fail_many("validate-installation", errors)
    print(
        "validate-installation: validated "
        f"{len(SKILL_ROOTS)} Skill root(s), {built_count} built Skill directorie(s), "
        f"{profile_count} Agent Profile file(s), 0 obsolete runtime artifact(s), and {zip_count} zip(s)."
    )
    return 0


def _write_report(
    errors: list[str],
    *,
    built_count: int,
    profile_count: int,
    zip_count: int,
    residue_count: int,
    release_projection: bool = False,
) -> None:
    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "architecture": "hookless-control-plane-v1",
        "generated_by": "scripts/validate-installation.py",
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-fixtures",
        "measurement_scope": "built Skill roots, static Agent Profiles, OpenAI Skill zips, and local install lifecycle",
        "limitations": list(EVIDENCE_LIMITATIONS),
        "profile_top_level_skill_counts": EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
        "summary": {
            "skill_roots": len(SKILL_ROOTS),
            "built_skill_directories": built_count,
            "agent_profile_roots": len(PROFILE_ROOTS),
            "agent_profile_files": profile_count,
            "zip_count": zip_count,
            "obsolete_runtime_artifacts": residue_count,
            "error_count": len(errors),
        },
        "errors": errors,
    }
    (report_dir / "installation-validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not release_projection:
        return
    summary = payload["summary"]
    lines = [
        "# Hookless Installation Validation",
        "",
        f"- Status: `{payload['status']}`",
        f"- Architecture: `{payload['architecture']}`",
        f"- Generated by: `{payload['generated_by']}`",
        f"- Evidence scope: `{payload['evidence_scope']}`",
        f"- Measurement scope: {payload['measurement_scope']}",
        "",
        "## Summary",
        "",
        f"- Skill roots: `{summary['skill_roots']}`",
        f"- Built Skill directories: `{summary['built_skill_directories']}`",
        f"- Agent Profile roots: `{summary['agent_profile_roots']}`",
        f"- Agent Profile files: `{summary['agent_profile_files']}`",
        f"- OpenAI Skill zips: `{summary['zip_count']}`",
        f"- Obsolete runtime artifacts: `{summary['obsolete_runtime_artifacts']}`",
        f"- Errors: `{summary['error_count']}`",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in payload["limitations"]],
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {error}" for error in errors)
    if not errors:
        lines.append("- None")
    (report_dir / "installation-validation.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _validate_skill_roots(errors: list[str]) -> int:
    total = 0
    for root in SKILL_ROOTS:
        for profile in PROFILES:
            profile_root = root / profile
            if not profile_root.is_dir():
                errors.append(f"missing built profile {profile_root.relative_to(ROOT)}")
                continue
            manifest_path = profile_root / BUILD_MANIFEST
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{manifest_path.relative_to(ROOT)}: invalid manifest: {exc}")
                continue
            errors.extend(
                _build_input_freshness_errors(
                    manifest,
                    manifest_path.relative_to(ROOT),
                )
            )
            if manifest.get("architecture") != "hookless-control-plane-v1":
                errors.append(f"{manifest_path.relative_to(ROOT)}: wrong architecture")
            if manifest.get("profile") != profile:
                errors.append(f"{manifest_path.relative_to(ROOT)}: wrong profile")
            if manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
                errors.append(
                    f"{manifest_path.relative_to(ROOT)}: compiled_layer3_format must "
                    f"equal {COMPILED_LAYER3_FORMAT!r}"
                )
            if manifest.get("core_model") != _expected_core_model_metadata():
                errors.append(
                    f"{manifest_path.relative_to(ROOT)}: core model digest is stale or invalid"
                )
            for field in ("runtime_engine", "hidden_role_packs", "executable_interception"):
                if field in manifest:
                    errors.append(f"{manifest_path.relative_to(ROOT)}: obsolete field remains: {field}")
            skill_dirs = [
                path for path in profile_root.iterdir()
                if path.is_dir() and not path.name.startswith(".")
            ]
            expected = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
            if len(skill_dirs) != expected:
                errors.append(f"{profile_root.relative_to(ROOT)}: expected {expected} Skills, found {len(skill_dirs)}")
            total += len(skill_dirs)
            manifest_names = set(manifest.get("top_level_skills") or [])
            actual_names = {path.name for path in skill_dirs}
            if manifest_names != actual_names:
                errors.append(f"{profile_root.relative_to(ROOT)}: manifest Skill list differs from directories")
            for skill_dir in skill_dirs:
                if not (skill_dir / "SKILL.md").is_file():
                    errors.append(f"{skill_dir.relative_to(ROOT)}: missing root SKILL.md")
            control = profile_root / "engineering-control-plane"
            for name in (
                "main-control-agent.md", "execution-level-contract.md", "professional-skill-router.md", "direct-task-template.md",
                "engineering-brief-template.md", "task-dag-template.md",
                "implementation-handoff-template.md", "utility-capsule-template.md",
                "review-handoff-template.md",
            ):
                if not (control / "references" / name).is_file():
                    errors.append(f"{control.relative_to(ROOT)}: missing reference {name}")
            runtime_reference = control / "references" / "execution-level-contract.md"
            if runtime_reference.is_file():
                source_reference = (
                    ROOT
                    / "src/control-skills/engineering-control-plane/references/execution-level-contract.md"
                )
                if runtime_reference.read_bytes() != source_reference.read_bytes():
                    errors.append(
                        f"{control.relative_to(ROOT)}: execution-level runtime Reference copy drifted"
                    )
                errors.extend(
                    f"{control.relative_to(ROOT)}: {error}"
                    for error in execution_level_runtime_reference_errors(
                        runtime_reference.read_text(encoding="utf-8")
                    )
                )
            if profile == "recommended":
                for name in manifest.get("professional_skills") or []:
                    if not (profile_root / name / "SKILL.md").is_file():
                        errors.append(f"{profile_root.relative_to(ROOT)}: Professional Skill {name} is not standard/installable")
    return total


def _validate_profile_roots(errors: list[str]) -> int:
    total = 0
    for root, suffix in PROFILE_ROOTS:
        if not root.is_dir():
            errors.append(f"missing built Agent Profile root {root.relative_to(ROOT)}")
            continue
        files = [path for path in root.iterdir() if path.is_file()]
        names = {path.name.removesuffix(suffix) for path in files if path.name.endswith(suffix)}
        if names != AGENT_PROFILES:
            errors.append(f"{root.relative_to(ROOT)}: expected four Agent Profiles, found {sorted(names)}")
        total += len(files)
    return total


def _validate_zips(errors: list[str]) -> int:
    total = 0
    for profile in PROFILES:
        root = ROOT / "dist" / "openai-api" / "zips" / profile
        zips = sorted(root.glob("*.zip")) if root.is_dir() else []
        expected = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
        if len(zips) != expected:
            errors.append(f"{root.relative_to(ROOT)}: expected {expected} zips, found {len(zips)}")
        total += len(zips)
        for path in zips:
            with zipfile.ZipFile(path) as archive:
                names = [name for name in archive.namelist() if name and not name.endswith("/")]
                top = {name.split("/", 1)[0] for name in names}
                if top != {path.stem} or f"{path.stem}/SKILL.md" not in names:
                    errors.append(f"{path.relative_to(ROOT)}: invalid standard Skill zip layout")
                if any(".changeforge-packs" in name or "runtime_governance" in name for name in names):
                    errors.append(f"{path.relative_to(ROOT)}: contains forbidden runtime content")
    return total


def _validate_no_residue(errors: list[str]) -> None:
    legacy_copilot = ROOT / "dist" / "copilot" / "project" / ".github" / "copilot" / "agents"
    if legacy_copilot.exists():
        errors.append(f"built residue directory: {legacy_copilot.relative_to(ROOT)}")
    for path in (ROOT / "dist").rglob("*"):
        if path.is_dir() and path.name in {".changeforge-packs", ".changeforge-control", "hooks", "runtime_governance"}:
            errors.append(f"built residue directory: {path.relative_to(ROOT)}")
        if path.is_file() and (
            path.name == ".changeforge-hook-manifest.json"
            or path.name in {"changeforge-hooks.json", "settings.changeforge-hooks.fragment.json", "hooks.json"}
            or path.name.startswith("changeforge_") and path.suffix == ".py"
        ):
            errors.append(f"built residue file: {path.relative_to(ROOT)}")


def _validate_cli_surface(errors: list[str]) -> None:
    forbidden = ("--with-hooks", "--without-hooks", "--hook-profile", "--professional-injection", "activation-level")
    for script in ("install.py", "upgrade.py", "uninstall.py", "doctor.py"):
        result = subprocess.run(
            [sys.executable, str(ROOT / "installers" / script), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            errors.append(f"installers/{script} --help failed: {result.stderr.strip()}")
        for token in forbidden:
            if token in result.stdout:
                errors.append(f"installers/{script}: obsolete option remains: {token}")


def _validate_install_cycle(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary) / "project"
        project.mkdir()
        user_marker = project / ".codex" / "hooks" / "user-owned.py"
        user_marker.parent.mkdir(parents=True)
        user_marker.write_text("# preserve\n", encoding="utf-8")
        legacy_script = project / ".codex" / "hooks" / "changeforge_hook.py"
        legacy_script.write_text("# legacy\n", encoding="utf-8")
        legacy_pack = project / ".agents" / "skills" / ".changeforge-packs"
        legacy_pack.mkdir(parents=True)
        config = project / ".codex" / "hooks.json"
        config.write_text(
            json.dumps({
                "hooks": {
                    "Before": [{
                        "hooks": [
                            {"command": "python user-owned.py"},
                            {"command": "python changeforge_hook.py"},
                        ]
                    }]
                }
            }),
            encoding="utf-8",
        )
        install = _run("install.py", "--agent", "codex", "--scope", "project", "--target", str(project), "--profile", "recommended")
        if install.returncode != 0:
            errors.append(f"installer smoke failed: {install.stderr.strip()}")
            return
        skills = project / ".agents" / "skills"
        profiles = project / ".codex" / "agents"
        install_manifest_path = skills / ".changeforge-install-manifest.json"
        try:
            install_manifest = json.loads(
                install_manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"installer smoke: invalid install manifest: {exc}")
            install_manifest = {}
        if install_manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
            errors.append("installer smoke: installed Layer 3 format is stale or missing")
        if install_manifest.get("core_model") != _expected_core_model_metadata():
            errors.append("installer smoke: installed core model digest is stale or missing")
        if len([path for path in skills.iterdir() if path.is_dir() and not path.name.startswith(".")]) != EXPECTED_PROFILE_TOP_LEVEL_COUNTS["recommended"]:
            errors.append("installer smoke: recommended Skill count mismatch")
        if {path.stem for path in profiles.glob("*.toml")} != AGENT_PROFILES:
            errors.append("installer smoke: Agent Profile set mismatch")
        if legacy_script.exists() or legacy_pack.exists():
            errors.append("installer smoke: legacy ChangeForge residue was not removed")
        if not user_marker.is_file() or "user-owned.py" not in config.read_text(encoding="utf-8"):
            errors.append("installer smoke: user-owned interception configuration was not preserved")
        if "changeforge_hook.py" in config.read_text(encoding="utf-8"):
            errors.append("installer smoke: ChangeForge command remains in shared config")
        doctor = _run("doctor.py", "--agent", "codex", "--scope", "project", "--target", str(project), "--profile", "recommended")
        if doctor.returncode != 0:
            errors.append(f"doctor smoke failed: {doctor.stdout.strip()} {doctor.stderr.strip()}")
        upgrade = _run("upgrade.py", "--agent", "codex", "--scope", "project", "--target", str(project), "--profile", "full")
        if upgrade.returncode != 0:
            errors.append(f"upgrade smoke failed: {upgrade.stderr.strip()}")
        else:
            try:
                upgraded_manifest = json.loads(
                    install_manifest_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"upgrade smoke: invalid install manifest: {exc}")
                upgraded_manifest = {}
            if upgraded_manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
                errors.append("upgrade smoke: installed Layer 3 format is stale or missing")
            if upgraded_manifest.get("core_model") != _expected_core_model_metadata():
                errors.append("upgrade smoke: installed core model digest is stale or missing")
        uninstall = _run("uninstall.py", "--agent", "codex", "--scope", "project", "--target", str(project))
        if uninstall.returncode != 0:
            errors.append(f"uninstall smoke failed: {uninstall.stderr.strip()}")
        if any((skills / name).exists() for name in AGENT_PROFILES):
            errors.append("uninstall smoke: unexpected Agent Profile under Skill root")
        if any(path.stem in AGENT_PROFILES for path in profiles.glob("*.toml")):
            errors.append("uninstall smoke: managed Agent Profiles remain")
        if not user_marker.is_file():
            errors.append("uninstall smoke: user-owned file was removed")


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "installers" / script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
