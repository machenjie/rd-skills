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
    EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT,
    RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH,
    authoritative_build_input_snapshot_errors,
    execution_level_runtime_reference_errors,
    fail_many,
    report_output_paths,
    runtime_asset_bundle_metadata_errors,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_NAME = "recommended"
RETIRED_RUNTIME_NAMES = ("full", "dev")
HISTORICAL_RUNTIME_PROFILES = ("recommended", "full", "dev")
HISTORICAL_RETIRED_PROFESSIONAL_SKILLS = {"routing-quality-review"}
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
REPORT_JSON = ROOT / "reports" / "installation-validation.json"
REPORT_MD = ROOT / "reports" / "installation-validation.md"


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    return parser.parse_args(argv)


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
    args = _args(argv)
    errors: list[str] = []
    built_count = _validate_skill_roots(errors)
    profile_count = _validate_profile_roots(errors)
    zip_count = _validate_zips(errors)
    residue_start = len(errors)
    _validate_no_residue(errors)
    residue_count = len(errors) - residue_start
    _validate_cli_surface(errors)
    migration_count = _validate_install_cycle(errors)
    _write_report(
        errors,
        built_count=built_count,
        profile_count=profile_count,
        zip_count=zip_count,
        residue_count=residue_count,
        migration_count=migration_count,
        release_projection=args.release_projection,
        reports_dir=args.reports_dir,
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
    migration_count: int,
    release_projection: bool = False,
    reports_dir: Path = ROOT / "reports",
) -> None:
    json_report, markdown_report = report_output_paths(
        reports_dir, REPORT_JSON.name, REPORT_MD.name
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "architecture": "hookless-control-plane-v1",
        "generated_by": "scripts/validate-installation.py",
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-fixtures",
        "measurement_scope": "built Skill roots, static Agent Profiles, OpenAI Skill zips, and local install lifecycle",
        "limitations": list(EVIDENCE_LIMITATIONS),
        "runtime_top_level_skill_count": EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT,
        "summary": {
            "skill_roots": len(SKILL_ROOTS),
            "built_skill_directories": built_count,
            "agent_profile_roots": len(PROFILE_ROOTS),
            "agent_profile_files": profile_count,
            "zip_count": zip_count,
            "obsolete_runtime_artifacts": residue_count,
            "legacy_profile_migrations": migration_count,
            "error_count": len(errors),
        },
        "errors": errors,
    }
    json_report.write_text(
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
        f"- Legacy Profile migrations: `{summary['legacy_profile_migrations']}`",
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
    markdown_report.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _validate_skill_roots(errors: list[str]) -> int:
    total = 0
    for root in SKILL_ROOTS:
        runtime_root = root / RUNTIME_NAME
        if not runtime_root.is_dir():
            errors.append(f"missing built Runtime {runtime_root.relative_to(ROOT)}")
            continue
        manifest_path = runtime_root / BUILD_MANIFEST
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
        if manifest.get("profile") != RUNTIME_NAME:
            errors.append(f"{manifest_path.relative_to(ROOT)}: wrong Runtime identity")
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
            path for path in runtime_root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ]
        if len(skill_dirs) != EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT:
            errors.append(
                f"{runtime_root.relative_to(ROOT)}: expected "
                f"{EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT} Skills, found {len(skill_dirs)}"
            )
        total += len(skill_dirs)
        manifest_names = set(manifest.get("top_level_skills") or [])
        actual_names = {path.name for path in skill_dirs}
        if manifest_names != actual_names:
            errors.append(f"{runtime_root.relative_to(ROOT)}: manifest Skill list differs from directories")
        layer3_names = set(manifest.get("foundation_skills") or []) | set(
            manifest.get("domain_skills") or []
        )
        leaked = actual_names & layer3_names
        if leaked:
            errors.append(
                f"{runtime_root.relative_to(ROOT)}: Layer 3 Skills leaked into Host discovery: "
                f"{sorted(leaked)}"
            )
        for skill_dir in skill_dirs:
            if not (skill_dir / "SKILL.md").is_file():
                errors.append(f"{skill_dir.relative_to(ROOT)}: missing root SKILL.md")
        control = runtime_root / "engineering-control-plane"
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
        for name in manifest.get("professional_skills") or []:
            if not (runtime_root / name / "SKILL.md").is_file():
                errors.append(f"{runtime_root.relative_to(ROOT)}: Professional Skill {name} is not installable")
            else:
                errors.extend(
                    _runtime_bundle_errors(runtime_root / name, manifest, name)
                )
        for retired in RETIRED_RUNTIME_NAMES:
            retired_root = root / retired
            if retired_root.exists():
                errors.append(f"retired built Runtime remains: {retired_root.relative_to(ROOT)}")
    return total


def _runtime_bundle_errors(
    professional_root: Path,
    manifest: dict[str, object],
    professional: object,
) -> list[str]:
    if not isinstance(professional, str):
        return [f"{professional_root.relative_to(ROOT)}: invalid Professional name"]
    integrity_path = professional_root / RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH
    try:
        integrity_bytes = integrity_path.read_bytes()
        delivery_assets = {
            path.relative_to(professional_root).as_posix(): path.read_bytes()
            for path in sorted(professional_root.rglob("*"))
            if path.is_file() and path != integrity_path
        }
    except OSError as exc:
        return [f"{professional_root.relative_to(ROOT)}: Runtime metadata unavailable: {exc}"]
    source_inputs = manifest.get("authoritative_build_inputs")
    full_digest = (
        source_inputs.get("sha256") if isinstance(source_inputs, dict) else None
    )
    bindings = manifest.get("runtime_asset_bindings")
    binding = bindings.get(professional) if isinstance(bindings, dict) else None
    return [
        f"{professional_root.relative_to(ROOT)}: {error}"
        for error in runtime_asset_bundle_metadata_errors(
            integrity_bytes,
            delivery_assets,
            binding,
            expected_source_version=str(manifest.get("source_version", "")),
            expected_authoritative_build_inputs_sha256=full_digest,
            expected_professional_skill=professional,
        )
    ]


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
    root = ROOT / "dist" / "openai-api" / "zips" / RUNTIME_NAME
    zips = sorted(root.glob("*.zip")) if root.is_dir() else []
    if len(zips) != EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT:
        errors.append(
            f"{root.relative_to(ROOT)}: expected "
            f"{EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT} zips, found {len(zips)}"
        )
    for path in zips:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name and not name.endswith("/")]
            top = {name.split("/", 1)[0] for name in names}
            if top != {path.stem} or f"{path.stem}/SKILL.md" not in names:
                errors.append(f"{path.relative_to(ROOT)}: invalid standard Skill zip layout")
            if any(".changeforge-packs" in name or "runtime_governance" in name for name in names):
                errors.append(f"{path.relative_to(ROOT)}: contains forbidden runtime content")
    for retired in RETIRED_RUNTIME_NAMES:
        retired_root = root.parent / retired
        if retired_root.exists():
            errors.append(f"retired zip Runtime remains: {retired_root.relative_to(ROOT)}")
    return len(zips)


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
    forbidden = (
        "--profile", "--with-hooks", "--without-hooks", "--hook-profile",
        "--professional-injection", "activation-level",
    )
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


def _validate_install_cycle(errors: list[str]) -> int:
    migration_count = 0
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
        install = _run(
            "install.py", "--agent", "codex", "--scope", "project",
            "--target", str(project),
        )
        if install.returncode != 0:
            errors.append(f"installer smoke failed: {install.stderr.strip()}")
            return migration_count
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
        if len([path for path in skills.iterdir() if path.is_dir() and not path.name.startswith(".")]) != EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT:
            errors.append("installer smoke: Runtime Skill count mismatch")
        if {path.stem for path in profiles.glob("*.toml")} != AGENT_PROFILES:
            errors.append("installer smoke: Agent Profile set mismatch")
        if legacy_script.exists() or legacy_pack.exists():
            errors.append("installer smoke: legacy pre-hookless residue was not removed")
        if not user_marker.is_file() or "user-owned.py" not in config.read_text(encoding="utf-8"):
            errors.append("installer smoke: user-owned interception configuration was not preserved")
        if "changeforge_hook.py" in config.read_text(encoding="utf-8"):
            errors.append("installer smoke: pre-hookless command remains in shared config")
        doctor = _run(
            "doctor.py", "--agent", "codex", "--scope", "project",
            "--target", str(project),
        )
        if doctor.returncode != 0:
            errors.append(f"doctor smoke failed: {doctor.stdout.strip()} {doctor.stderr.strip()}")
        upgrade = _run(
            "upgrade.py", "--agent", "codex", "--scope", "project",
            "--target", str(project),
        )
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
        migration_count += _validate_legacy_profile_upgrades(
            Path(temporary), errors
        )
        uninstall = _run("uninstall.py", "--agent", "codex", "--scope", "project", "--target", str(project))
        if uninstall.returncode != 0:
            errors.append(f"uninstall smoke failed: {uninstall.stderr.strip()}")
        if any((skills / name).exists() for name in AGENT_PROFILES):
            errors.append("uninstall smoke: unexpected Agent Profile under Skill root")
        if any(path.stem in AGENT_PROFILES for path in profiles.glob("*.toml")):
            errors.append("uninstall smoke: managed Agent Profiles remain")
        if not user_marker.is_file():
            errors.append("uninstall smoke: user-owned file was removed")
    return migration_count


def _validate_legacy_profile_upgrades(
    temporary_root: Path,
    errors: list[str],
) -> int:
    source_manifest_path = (
        ROOT
        / "dist/codex/project/.agents/skills"
        / RUNTIME_NAME
        / BUILD_MANIFEST
    )
    try:
        source_manifest = json.loads(
            source_manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"legacy migration smoke: invalid build manifest: {exc}")
        return 0
    inventories = {
        "control": set(source_manifest.get("control_skills") or []),
        "professional": set(source_manifest.get("professional_skills") or []),
        "foundation": set(source_manifest.get("foundation_skills") or []),
        "domain": set(source_manifest.get("domain_skills") or []),
    }
    if {name: len(values) for name, values in inventories.items()} != {
        "control": 1,
        "professional": 25,
        "foundation": 150,
        "domain": 13,
    }:
        errors.append("legacy migration smoke: build inventories are incomplete")
        return 0

    passed = 0
    historical_professional = (
        inventories["professional"] | HISTORICAL_RETIRED_PROFESSIONAL_SKILLS
    )
    if len(historical_professional) != 26:
        errors.append(
            "legacy migration smoke: historical Professional inventory is incomplete"
        )
        return 0

    for legacy_profile in HISTORICAL_RUNTIME_PROFILES:
        project = temporary_root / f"legacy-{legacy_profile}"
        project.mkdir()
        install = _run(
            "install.py", "--agent", "codex", "--scope", "project",
            "--target", str(project),
        )
        if install.returncode != 0:
            errors.append(
                f"legacy {legacy_profile} migration setup failed: "
                f"{install.stderr.strip()}"
            )
            continue
        skills = project / ".agents/skills"
        manifest_path = skills / ".changeforge-install-manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                f"legacy {legacy_profile} migration manifest is invalid: {exc}"
            )
            continue
        legacy_layer3: set[str] = set()
        if legacy_profile in {"full", "dev"}:
            legacy_layer3 |= inventories["domain"]
        if legacy_profile == "dev":
            legacy_layer3 |= inventories["foundation"]
        retired_skills = legacy_layer3 | HISTORICAL_RETIRED_PROFESSIONAL_SKILLS
        for name in sorted(retired_skills):
            legacy_skill = skills / name
            legacy_skill.mkdir()
            (legacy_skill / "SKILL.md").write_text(
                f"# legacy managed {name}\n", encoding="utf-8"
            )
        legacy_skills = (
            inventories["control"]
            | historical_professional
            | legacy_layer3
        )
        manifest.update(
            {
                "profile": legacy_profile,
                "installed_skills": sorted(legacy_skills),
                "installed_control_skills": sorted(inventories["control"]),
                "installed_professional_skills": sorted(
                    historical_professional
                ),
                "installed_foundation_skills": (
                    sorted(inventories["foundation"])
                    if legacy_profile == "dev"
                    else []
                ),
                "installed_domain_skills": (
                    sorted(inventories["domain"])
                    if legacy_profile in {"full", "dev"}
                    else []
                ),
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        user_skill = skills / f"user-owned-{legacy_profile}"
        user_skill.mkdir()
        (user_skill / "SKILL.md").write_text(
            "# preserve user Skill\n", encoding="utf-8"
        )
        upgrade = _run(
            "upgrade.py", "--agent", "codex", "--scope", "project",
            "--target", str(project),
        )
        if upgrade.returncode != 0:
            errors.append(
                f"legacy {legacy_profile} migration failed: {upgrade.stderr.strip()}"
            )
            continue
        try:
            upgraded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                f"legacy {legacy_profile} upgraded manifest is invalid: {exc}"
            )
            continue
        remaining_legacy = sorted(
            name for name in retired_skills if (skills / name).exists()
        )
        if remaining_legacy:
            errors.append(
                f"legacy {legacy_profile} migration retained managed retired "
                f"Skills: {remaining_legacy}"
            )
            continue
        if not (user_skill / "SKILL.md").is_file():
            errors.append(
                f"legacy {legacy_profile} migration removed a user-owned Skill"
            )
            continue
        if (
            upgraded.get("profile") != RUNTIME_NAME
            or len(upgraded.get("installed_skills") or [])
            != EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT
            or upgraded.get("installed_foundation_skills") != []
            or upgraded.get("installed_domain_skills") != []
        ):
            errors.append(
                f"legacy {legacy_profile} migration did not converge to the Runtime manifest"
            )
            continue
        passed += 1
    return passed


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
