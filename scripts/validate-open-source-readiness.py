#!/usr/bin/env python3
"""Validate conservative open-source publication readiness."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from validation_utils import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("config/open-source-release.yaml")
ALLOWED_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-3-Clause",
    "MPL-2.0",
    "GPL-3.0-only",
    "AGPL-3.0-only",
}
DIST_RELEASE_POLICIES = {
    "ignored-generated-output",
    "release-artifact-only",
    "committed-snapshot",
}


@dataclass(frozen=True)
class OpenSourceReadiness:
    """Structured readiness result consumed by the validator and scorecard."""

    status: str
    selected_license: str | None
    checks: dict[str, bool]
    errors: list[str]
    warnings: list[str]
    detail: str


def _load_config(root: Path) -> dict[str, Any]:
    path = root / CONFIG_PATH
    if not path.exists():
        return {}
    loaded = load_yaml_file(path)
    return loaded if isinstance(loaded, dict) else {}


def _pyproject_license_text(root: Path) -> str:
    path = root / "pyproject.toml"
    if not path.exists():
        return ""
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return ""
    project = parsed.get("project", parsed)
    license_value = project.get("license") if isinstance(project, dict) else None
    if isinstance(license_value, dict):
        return str(license_value.get("text") or license_value.get("file") or "").strip()
    if isinstance(license_value, str):
        return license_value.strip()
    return ""


def _contribution_evidence_found(root: Path) -> bool:
    path = root / "CONTRIBUTING.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").casefold()
    unresolved = (
        "proprietary license metadata",
        "maintainers must choose",
        "before accepting external contributions",
        "pending owner decision",
        "owner decision",
    )
    return "contribution licensing" in text and "repository license" in text and not any(
        marker in text for marker in unresolved
    )


def _security_contact_evidence_found(root: Path) -> bool:
    path = root / "SECURITY.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").casefold()
    return (
        "private vulnerability reporting is enabled" in text
        or "mailto:" in text
        or "security@" in text
    )


def evaluate_open_source_readiness(root: Path) -> OpenSourceReadiness:
    """Evaluate readiness without inferring owner decisions from prose alone."""
    config = _load_config(root)
    selected_license_raw = config.get("selected_license")
    selected_license = (
        str(selected_license_raw).strip() if selected_license_raw is not None else None
    )
    if selected_license == "":
        selected_license = None

    contribution_confirmed = config.get("contribution_licensing_confirmed") is True
    security_confirmed = config.get("security_contact_confirmed") is True
    dist_release_policy = config.get("dist_release_policy")
    license_text = _pyproject_license_text(root)
    license_file_exists = (root / "LICENSE").is_file()
    pyproject_non_proprietary = bool(license_text) and "proprietary" not in license_text.casefold()
    contribution_evidence = _contribution_evidence_found(root)
    security_evidence = _security_contact_evidence_found(root)
    dist_policy_valid = dist_release_policy in DIST_RELEASE_POLICIES
    selected_license_valid = selected_license is None or selected_license in ALLOWED_LICENSES

    checks = {
        "config_present": (root / CONFIG_PATH).is_file(),
        "selected_license_non_null": selected_license is not None,
        "selected_license_allowed": selected_license_valid,
        "license_file": license_file_exists,
        "pyproject_license_not_proprietary": pyproject_non_proprietary,
        "contribution_licensing_confirmed": contribution_confirmed,
        "contribution_licensing_evidence": contribution_evidence,
        "security_contact_confirmed": security_confirmed,
        "security_contact_evidence": security_evidence,
        "dist_release_policy_explicit": isinstance(dist_release_policy, str),
        "dist_release_policy_valid": dist_policy_valid,
    }

    errors: list[str] = []
    warnings: list[str] = []
    if not checks["config_present"]:
        errors.append(f"missing {CONFIG_PATH}")
    if not selected_license_valid:
        errors.append(f"selected_license must be one of {sorted(ALLOWED_LICENSES)} or null")
    if not dist_policy_valid:
        errors.append(
            f"dist_release_policy must be one of {sorted(DIST_RELEASE_POLICIES)}"
        )
    if license_file_exists and not pyproject_non_proprietary:
        errors.append("root LICENSE exists but pyproject.toml license metadata is proprietary")
    if selected_license is not None and not license_file_exists:
        errors.append("selected_license is set but root LICENSE is missing")
    if selected_license is not None and not pyproject_non_proprietary:
        errors.append("selected_license is set but pyproject.toml license metadata is proprietary")
    # Config booleans are owner decisions. The matching docs must still carry
    # enough evidence that the confirmation is reviewable in the repository.
    if contribution_confirmed and not contribution_evidence:
        errors.append("contribution_licensing_confirmed is true but CONTRIBUTING.md does not confirm it")
    if security_confirmed and not security_evidence:
        errors.append("security_contact_confirmed is true but SECURITY.md lacks private reporting/contact evidence")

    if not license_file_exists:
        warnings.append("root LICENSE is missing; open-source readiness is partial")
    if selected_license is None:
        warnings.append("owner license decision is still required")
    if not contribution_confirmed:
        warnings.append("contribution licensing is not owner-confirmed")
    if not security_confirmed:
        warnings.append("security contact/private vulnerability reporting is not owner-confirmed")

    pass_checks = (
        license_file_exists
        and pyproject_non_proprietary
        and selected_license is not None
        and contribution_confirmed
        and contribution_evidence
        and security_confirmed
        and security_evidence
        and dist_policy_valid
    )
    if errors:
        status = "fail"
    elif pass_checks:
        status = "pass"
    else:
        status = "partial"

    detail = ", ".join(f"{name}={value}" for name, value in checks.items())
    return OpenSourceReadiness(
        status=status,
        selected_license=selected_license,
        checks=checks,
        errors=errors,
        warnings=warnings,
        detail=detail,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for open-source readiness validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json-out", help="Optional JSON output path.")
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Fail unless all open-source publication gates pass.",
    )
    args = parser.parse_args(argv)

    result = evaluate_open_source_readiness(Path(args.root))
    print(f"validate-open-source-readiness: status={result.status}")
    for warning in result.warnings:
        print(f"validate-open-source-readiness: WARNING: {warning}")
    for error in result.errors:
        print(f"validate-open-source-readiness: ERROR: {error}", file=sys.stderr)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if result.errors:
        return 1
    if args.require_pass and result.status != "pass":
        print(
            "validate-open-source-readiness: ERROR: open-source publication gates are not all passing",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
