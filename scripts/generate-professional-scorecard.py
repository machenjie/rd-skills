#!/usr/bin/env python3
"""Generate a conservative professional scorecard from local evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    load_yaml_file,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
STATUSES = ("pass", "partial", "fail", "unknown", "not_collected")
STRICT_PROFILE_BUILD_DIMENSIONS = (
    "Registry source counts",
    "Profile build reproducibility",
    "Example coverage",
    "Productization assets",
)
PRODUCTIZATION_ASSETS = (
    "docs/QUICKSTART.md",
    "docs/BENCHMARKS.md",
    "docs/SCORECARD.md",
    "docs/SCORECARD_DASHBOARD.md",
    "docs/MARKETPLACE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
    "docs/COMPARISON.md",
    "docs/OPEN_SOURCE_READINESS.md",
    "docs/LICENSE_DECISION.md",
    "reports/README.md",
    "reports/professional-scorecard.md",
    "reports/professional-scorecard.json",
    "reports/public-benchmark-summary.md",
    "reports/public-benchmark-summary.json",
    "config/open-source-release.yaml",
    "schemas/marketplace-index.schema.json",
    "scripts/generate-professional-scorecard.py",
    "scripts/generate-public-benchmark-summary.py",
    "scripts/generate-examples-showcase.py",
    "scripts/generate-marketplace-catalog.py",
    "scripts/render-scorecard-dashboard.py",
    "scripts/quickstart.py",
    "scripts/validate-open-source-readiness.py",
    "scripts/export-marketplace-index.py",
    "scripts/validate-marketplace-index.py",
    "scripts/validate-examples.py",
)


VALIDATION_COMMANDS = [
    "python3 scripts/validate-skills.py",
    "python3 scripts/validate-capabilities.py",
    "python3 scripts/validate-domain-extensions.py",
    "python3 scripts/validate-registry.py",
    "python3 scripts/validate-skill-body-links.py",
    "python3 scripts/validate-skill-content-size.py",
    "python3 scripts/audit-skill-content.py",
    "python3 scripts/eval-routing.py",
    "python3 scripts/eval-agent-behavior.py",
    "python3 scripts/eval-skill-professionalism.py",
    "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
    "python3 scripts/eval-professional-benchmarks.py",
    "python3 scripts/validate-professionalism-regression.py",
    "python3 scripts/validate-professionalism-regression.py --strict",
    "python3 scripts/validate-professional-routing-coverage.py",
    "python3 scripts/validate-stage-routing-architecture.py",
    "python3 scripts/validate-hooks.py",
    "python3 scripts/eval-pressure-behavior.py",
    "python3 -m unittest discover -s tests",
    "python3 scripts/validate-codegen-benchmarks.py",
    "python3 scripts/run-codegen-benchmarks.py --limit 3",
    "python3 scripts/build.py --profile recommended",
    "python3 scripts/build.py --profile full",
    "python3 scripts/build.py --profile dev",
    "python3 scripts/validate-runtime-reference-links.py",
    "python3 scripts/validate-installation.py",
    "python3 scripts/validate-marketplace-index.py --profile recommended",
    "python3 scripts/validate-marketplace-index.py --profile full",
    "python3 scripts/validate-marketplace-index.py --profile dev",
    "python3 scripts/validate-examples.py",
    "python3 scripts/validate-productization-assets.py",
    "python3 scripts/validate-open-source-readiness.py",
    "python3 scripts/generate-public-benchmark-summary.py --check --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json",
    "python3 scripts/generate-examples-showcase.py --check --out docs/SHOWCASE.md",
    "python3 scripts/generate-marketplace-catalog.py --profile recommended --check --out docs/MARKETPLACE_CATALOG.md",
    "python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md --check",
]


@dataclass
class Dimension:
    name: str
    status: str
    source: str
    verification_command: str
    fix_hint: str
    detail: str

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"invalid status for {self.name}: {self.status}")


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _source_counts(root: Path) -> dict[str, int]:
    skills = load_yaml_file(root / "src" / "registry" / "skills.yaml").get("skills", [])
    capabilities = load_yaml_file(root / "src" / "registry" / "capabilities.yaml").get("capabilities", [])
    extensions = load_yaml_file(root / "src" / "registry" / "domain-extensions.yaml").get("domain_extensions", [])
    return {
        "professional_skills": len(skills),
        "foundation_capabilities": len(capabilities),
        "domain_extensions": len(extensions),
    }


def profile_manifest_status(manifest: dict[str, Any] | None, profile: str) -> tuple[str, str]:
    """Return status/detail for one build manifest without inferring missing data as pass."""
    if manifest is None:
        return "unknown", "build manifest not found"

    expected_top_level = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
    checks = {
        "profile": manifest.get("profile") == profile,
        "top_level": len(manifest.get("top_level_skills", [])) == expected_top_level,
        "professional_skills": len(manifest.get("professional_skills", [])) == EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "foundation_capabilities": len(manifest.get("foundation_capabilities", [])) == EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "compiled_foundation_capabilities": len(manifest.get("compiled_foundation_capabilities", []))
        == EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "domain_extensions": len(manifest.get("domain_extensions", [])) == EXPECTED_DOMAIN_EXTENSION_COUNT,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return "fail", "failed checks: " + ", ".join(failed)
    return "pass", f"{profile} top-level count is {expected_top_level}"


def _build_manifest(root: Path, profile: str) -> dict[str, Any] | None:
    return _read_json(root / "dist" / "universal" / "skills" / profile / ".changeforge-build-manifest.json")


def _load_open_source_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_open_source_readiness",
        ROOT / "scripts" / "validate-open-source-readiness.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-open-source-readiness.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def open_source_readiness_status(root: Path) -> tuple[str, str]:
    """Return conservative open-source readiness status and check details."""
    result = _load_open_source_validator().evaluate_open_source_readiness(root)
    return result.status, result.detail


def productization_assets_status(root: Path) -> tuple[str, str]:
    """Return status/detail for productization assets the scorecard depends on."""
    missing = [rel_path for rel_path in PRODUCTIZATION_ASSETS if not (root / rel_path).is_file()]
    if missing:
        return "fail", "missing: " + ", ".join(missing)
    return "pass", "required productization assets present"


def _load_validate_examples():
    spec = importlib.util.spec_from_file_location(
        "validate_examples",
        ROOT / "scripts" / "validate-examples.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-examples.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_validate_marketplace_index():
    spec = importlib.util.spec_from_file_location(
        "validate_marketplace_index",
        ROOT / "scripts" / "validate-marketplace-index.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-marketplace-index.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def examples_status(root: Path) -> tuple[str, str]:
    """Return status/detail from the same validator used by CI."""
    errors = _load_validate_examples().validate_examples(root)
    if errors:
        return "fail", "; ".join(errors[:5])
    return "pass", "showcase examples validate"


def marketplace_index_status(root: Path) -> tuple[str, str]:
    """Return status/detail from the marketplace index validator for all profiles."""
    validator = _load_validate_marketplace_index()
    errors_by_profile: dict[str, list[str]] = {}
    for profile in PROFILES:
        errors = validator.validate_profile(root, profile)
        if errors:
            errors_by_profile[profile] = errors
    if errors_by_profile:
        detail = {
            profile: errors[:3]
            for profile, errors in errors_by_profile.items()
        }
        return "fail", json.dumps(detail, sort_keys=True)
    return "pass", "recommended, full, and dev marketplace indexes validate"


def _summary_status(name: str, value: dict[str, Any]) -> str:
    if name == "Routing coverage":
        if value.get("hidden_risks_needing_manual_review", 0) or value.get("cases_without_forbidden", 0):
            return "partial"
        return "pass" if value.get("cases_checked") else "unknown"
    if name == "Professional benchmarks":
        if value.get("quality_failures", 0):
            return "fail"
        return "pass" if value.get("comparison_cases_checked") else "unknown"
    if name == "Foundation capability coverage":
        statuses = value.get("statuses", {})
        if statuses.get("fail") or statuses.get("missing"):
            return "fail"
        if statuses.get("needs-review"):
            return "partial"
        return "pass" if value.get("count") else "unknown"
    if name == "Professional skill coverage":
        statuses = value.get("statuses", {})
        if statuses.get("fail") or statuses.get("missing"):
            return "fail"
        if statuses.get("needs-review"):
            return "partial"
        return "pass" if value.get("count") == EXPECTED_PROFESSIONAL_SKILL_COUNT else "partial"
    return "partial"


def _release_readiness_dimension(reports_dir: Path, key: str, *, name: str, command: str, fix_hint: str) -> Dimension:
    readiness = _read_json(reports_dir / "professionalism-release-readiness.json")
    if readiness is None:
        return Dimension(name, "not_collected", "reports/professionalism-release-readiness.json missing", command, fix_hint, "Run the professionalism release checks first.")

    value = readiness.get(key)
    if isinstance(value, str):
        if value in {"pass", "ready", "strict-release-ready"}:
            status = "pass"
        elif value in {"blocked", "fail", "failed"}:
            status = "fail"
        else:
            status = "partial"
        return Dimension(name, status, "reports/professionalism-release-readiness.json", command, fix_hint, f"{key}: {value}")

    if isinstance(value, dict):
        return Dimension(name, _summary_status(name, value), "reports/professionalism-release-readiness.json", command, fix_hint, json.dumps(value, sort_keys=True))

    return Dimension(name, "unknown", "reports/professionalism-release-readiness.json", command, fix_hint, f"{key} not present")


def collect_dimensions(root: Path, reports_dir: Path) -> tuple[list[Dimension], dict[str, Any]]:
    """Collect scorecard dimensions from registries, build manifests, and reports."""
    counts = _source_counts(root)
    registry_status = "pass" if counts == {
        "professional_skills": EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "foundation_capabilities": EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "domain_extensions": EXPECTED_DOMAIN_EXTENSION_COUNT,
    } else "fail"

    dimensions = [
        Dimension(
            "Registry source counts",
            registry_status,
            "src/registry/*.yaml",
            "python3 scripts/validate-registry.py",
            "Fix registry entries or expected count constants so they agree.",
            json.dumps(counts, sort_keys=True),
        )
    ]

    profile_details: dict[str, Any] = {}
    profile_statuses: list[str] = []
    for profile in PROFILES:
        manifest = _build_manifest(root, profile)
        status, detail = profile_manifest_status(manifest, profile)
        profile_statuses.append(status)
        profile_details[profile] = {
            "status": status,
            "detail": detail,
            "manifest": str(
                Path("dist")
                / "universal"
                / "skills"
                / profile
                / ".changeforge-build-manifest.json"
            ),
        }

    if any(status == "fail" for status in profile_statuses):
        profile_status = "fail"
    elif any(status in {"unknown", "not_collected"} for status in profile_statuses):
        profile_status = "unknown"
    else:
        profile_status = "pass"
    dimensions.append(
        Dimension(
            "Profile build reproducibility",
            profile_status,
            "dist/universal/skills/*/.changeforge-build-manifest.json",
            "python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev",
            "Rebuild all profiles and investigate any manifest count mismatch.",
            json.dumps(profile_details, sort_keys=True),
        )
    )

    dimensions.extend(
        [
            _release_readiness_dimension(
                reports_dir,
                "routing_coverage_summary",
                name="Routing coverage",
                command="python3 scripts/validate-professional-routing-coverage.py",
                fix_hint="Add or repair routing fixtures for uncovered hidden risks.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "professional_skill_coverage_summary",
                name="Professional skill coverage",
                command="python3 scripts/eval-skill-professionalism.py",
                fix_hint="Repair weak professional skill sections without keyword stuffing.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "key_foundation_capability_coverage_summary",
                name="Foundation capability coverage",
                command="python3 scripts/eval-skill-professionalism.py --coverage-matrix",
                fix_hint="Improve selected capability evidence contracts and references.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "benchmark_coverage_summary",
                name="Professional benchmarks",
                command="python3 scripts/eval-professional-benchmarks.py",
                fix_hint="Repair failing benchmark cases or comparison fixtures.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "strict_regression_status",
                name="Professionalism regression",
                command="python3 scripts/validate-professionalism-regression.py --strict",
                fix_hint="Resolve release blockers or record reviewed baseline decisions.",
            ),
            _release_readiness_dimension(
                reports_dir,
                "promoted_agent_samples_strict_status",
                name="Promoted agent samples",
                command="python3 scripts/eval-professional-agent-samples.py --promoted-only --strict",
                fix_hint="Repair promoted samples that miss route, evidence, or residual risk obligations.",
            ),
        ]
    )

    example_status, example_detail = examples_status(root)
    dimensions.append(
        Dimension(
            "Example coverage",
            example_status,
            "examples/ and scripts/validate-examples.py",
            "python3 scripts/validate-examples.py",
            "Repair showcase scenario prompts, expected routes, evidence files, or routing fixture links.",
            example_detail,
        )
    )

    productization_status, productization_detail = productization_assets_status(root)
    dimensions.append(
        Dimension(
            "Productization assets",
            productization_status,
            "docs/productization assets, schemas, and scripts",
            "python3 scripts/validate-productization-assets.py",
            "Restore required productization docs, schema, or scripts.",
            productization_detail,
        )
    )

    marketplace_status, marketplace_detail = marketplace_index_status(root)
    dimensions.append(
        Dimension(
            "Marketplace index validation",
            marketplace_status,
            "scripts/validate-marketplace-index.py",
            "python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev",
            "Rebuild all profiles and repair marketplace index schema, visibility, or runtime path mismatches.",
            marketplace_detail,
        )
    )

    open_source_status, open_source_detail = open_source_readiness_status(root)
    dimensions.append(
        Dimension(
            "Open-source readiness",
            open_source_status,
            "config/open-source-release.yaml, docs/LICENSE_DECISION.md, docs/OPEN_SOURCE_READINESS.md, pyproject.toml, CONTRIBUTING.md, SECURITY.md, LICENSE",
            "python3 scripts/validate-open-source-readiness.py",
            "Owner must select an OSI license, update package metadata, confirm contribution licensing, and configure private vulnerability reporting before open-source publication.",
            open_source_detail,
        )
    )

    dimensions.append(
        Dimension(
            "Hook safety",
            "not_collected",
            "scripts/validate-hooks.py does not emit a machine-readable report",
            "python3 scripts/validate-hooks.py",
            "Run hook validation and inspect hook runtime changes; hooks must remain advisory and fail-open unless explicitly stricter.",
            "not collected by scorecard generator",
        )
    )
    dimensions.append(
        Dimension(
            "Installation validation",
            "not_collected",
            "scripts/validate-installation.py does not emit a machine-readable report",
            "python3 scripts/validate-installation.py",
            "Run installation validation after rebuilding all profiles.",
            "not collected by scorecard generator",
        )
    )

    metadata = {
        "source_counts": counts,
        "profile_counts": profile_details,
        "validation_commands": [
            {
                "command": command,
                "status": "not_collected",
                "note": "Run command directly; this scorecard does not infer pass/fail from stdout.",
            }
            for command in VALIDATION_COMMANDS
        ],
    }
    return dimensions, metadata


def _summary(dimensions: list[Dimension]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for dimension in dimensions:
        counts[dimension.status] += 1
    return counts


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the scorecard JSON payload as Markdown."""
    lines = [
        "# Professional Scorecard",
        "",
        "This scorecard is generated from local registry, build, and report evidence. Missing machine-readable evidence is shown as `not_collected` or `unknown`, not as pass.",
        "",
        "## Summary",
        "",
    ]
    for status, count in payload["status_summary"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Dimensions", "", "| Dimension | Status | Source | Verification |", "| --- | --- | --- | --- |"])
    for dimension in payload["dimensions"]:
        lines.append(
            f"| {dimension['name']} | `{dimension['status']}` | {dimension['source']} | `{dimension['verification_command']}` |"
        )
    lines.extend(["", "## Profile Counts", ""])
    for profile, detail in payload["profile_counts"].items():
        lines.append(f"- `{profile}`: `{detail['status']}` - {detail['detail']}")
    lines.extend(["", "## Repair Hints", ""])
    for dimension in payload["dimensions"]:
        if dimension["status"] != "pass":
            lines.append(f"- {dimension['name']}: {dimension['fix_hint']}")
    lines.append("")
    return "\n".join(lines)


def generate_scorecard(root: Path, reports_dir: Path) -> dict[str, Any]:
    """Generate the complete scorecard payload."""
    dimensions, metadata = collect_dimensions(root, reports_dir)
    dimension_payload = [asdict(dimension) for dimension in dimensions]
    return {
        "schema_version": 1,
        "generated_by": "scripts/generate-professional-scorecard.py",
        "status_summary": _summary(dimensions),
        "dimensions": dimension_payload,
        **metadata,
    }


def strict_profile_build_errors(payload: dict[str, Any]) -> list[str]:
    """Return strict profile-build smoke errors without requiring release-only reports."""
    dimensions = {
        str(dimension.get("name")): str(dimension.get("status"))
        for dimension in payload.get("dimensions", [])
        if isinstance(dimension, dict)
    }
    errors: list[str] = []
    for name in STRICT_PROFILE_BUILD_DIMENSIONS:
        status = dimensions.get(name)
        if status != "pass":
            errors.append(f"{name} must be pass for --strict-profile-builds, got {status or 'missing'}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for writing Markdown and JSON scorecards."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Markdown output path.")
    parser.add_argument("--json-out", required=True, help="JSON output path.")
    parser.add_argument("--reports-dir", default=str(ROOT / "reports"))
    parser.add_argument(
        "--strict-profile-builds",
        action="store_true",
        help="Fail when build/profile/productization smoke dimensions are missing or not passing.",
    )
    args = parser.parse_args(argv)

    payload = generate_scorecard(ROOT, Path(args.reports_dir))
    json_out = Path(args.json_out)
    md_out = Path(args.out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote professional scorecard to {md_out} and {json_out}")
    if args.strict_profile_builds:
        errors = strict_profile_build_errors(payload)
        if errors:
            for error in errors:
                print(f"generate-professional-scorecard: ERROR: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
