#!/usr/bin/env python3
"""Validate Hookless Direct, Analyzed, and Review example contracts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from validation_utils import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ("prompt.md", "expected-route.md", "expected-evidence.md")
FORBIDDEN = (
    "selected_skills",
    "selected_capabilities",
    "required_quality_gates",
    "route manifest",
    "runtime id",
    "digest",
    "```yaml",
    "```json",
)


def _names(root: Path) -> tuple[dict[str, dict], set[str]]:
    professional_data = load_yaml_file(root / "src/registry/professional-skills.yaml")
    foundation_data = load_yaml_file(root / "src/registry/foundation-skills.yaml")
    domain_data = load_yaml_file(root / "src/registry/domain-skills.yaml")
    professional = {item["name"]: item for item in professional_data["professional_skills"]}
    layer3 = {
        item["name"]
        for item in [*foundation_data["foundation_skills"], *domain_data["domain_skills"]]
    }
    return professional, layer3


def validate_examples(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    professional, layer3 = _names(root)
    examples_root = root / "examples"
    scenarios = [path for path in sorted(examples_root.glob("[0-9][0-9]-*")) if path.is_dir()]
    if len(scenarios) < 4:
        errors.append(f"expected at least four numbered examples, found {len(scenarios)}")
    for scenario in scenarios:
        relative = scenario.relative_to(root)
        for name in REQUIRED_FILES:
            if not (scenario / name).is_file():
                errors.append(f"{relative}: missing {name}")
        route_path = scenario / "expected-route.md"
        evidence_path = scenario / "expected-evidence.md"
        if not route_path.is_file() or not evidence_path.is_file():
            continue
        route = route_path.read_text(encoding="utf-8")
        evidence = evidence_path.read_text(encoding="utf-8")
        folded = route.casefold()
        if "## path" not in folded:
            errors.append(f"{relative}: expected route must declare Path")
        if not any(marker in folded for marker in ("task assignment", "analysis assignment", "review assignment")):
            errors.append(f"{relative}: expected route needs a bounded assignment")
        for token in FORBIDDEN:
            if token in folded:
                errors.append(f"{relative}: obsolete route token {token}")

        profiles = re.findall(r"Profile:\s*`([^`]+)`", route)
        for profile in profiles:
            if profile not in {"analysis-agent", "task-agent", "review-agent"}:
                errors.append(f"{relative}: unknown Profile {profile}")
        primary = re.findall(r"(?:Primary Professional Skill|Review Skill):\s*`([^`]+)`", route)
        for name in primary:
            if name not in professional:
                errors.append(f"{relative}: unknown Professional Skill {name}")
        selected_layer3 = [name for name in layer3 if f"`{name}`" in route]
        if len(selected_layer3) > 3:
            errors.append(f"{relative}: route loads more than three Layer 3 Skills")
        available = {
            candidate
            for name in primary
            for candidate in professional.get(name, {}).get("layer3_candidates", [])
        }
        unavailable = sorted(set(selected_layer3) - available)
        if unavailable:
            errors.append(
                f"{relative}: Layer 3 Skills are not available from the named primary/review Skills: "
                + ", ".join(unavailable)
            )

        evidence_folded = evidence.casefold()
        for phrase in ("validation evidence", "independent review", "residual risk", "unverified scope"):
            if phrase not in evidence_folded:
                errors.append(f"{relative}: evidence is missing {phrase}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    errors = validate_examples(Path(args.root))
    if errors:
        for error in errors:
            print(f"validate-examples: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-examples: Direct, Analyzed, and Review examples are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
