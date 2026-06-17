#!/usr/bin/env python3
"""Validate productization showcase examples."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from validation_utils import load_yaml_file, load_yaml_text


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ("prompt.md", "expected-route.md", "expected-evidence.md")
REQUIRED_ROUTE_TERMS = ("selected_skills", "selected_capabilities", "required_quality_gates")
REQUIRED_EVIDENCE_TERMS = (
    "read before plan",
    "TDD",
    "validation evidence",
    "independent review",
    "residual risk",
    "handoff",
)
SHORT_CIRCUIT_PATTERNS = (
    re.compile(r"\bjust\s+edit\b", re.IGNORECASE),
    re.compile(r"\bskip\s+(the\s+)?(tests|validation|review)\b", re.IGNORECASE),
    re.compile(r"\bno\s+need\s+to\s+(read|inspect|test|review)\b", re.IGNORECASE),
    re.compile(r"直接改代码"),
)
ROUTE_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


def _known_names(root: Path) -> tuple[set[str], set[str]]:
    skills = load_yaml_file(root / "src" / "registry" / "skills.yaml").get("skills", [])
    extensions = load_yaml_file(root / "src" / "registry" / "domain-extensions.yaml").get("domain_extensions", [])
    capabilities = load_yaml_file(root / "src" / "registry" / "capabilities.yaml").get("capabilities", [])
    skill_names = {item["name"] for item in skills} | {item["name"] for item in extensions}
    capability_names = {item["name"] for item in capabilities}
    return skill_names, capability_names


def _route_payload(route_text: str, path: Path) -> dict[str, object]:
    match = ROUTE_BLOCK_RE.search(route_text)
    if not match:
        return {}
    loaded = load_yaml_text(match.group(1), path)
    return loaded if isinstance(loaded, dict) else {}


def _list_value(payload: dict[str, object], key: str) -> list[str]:
    value = payload.get(key)
    return [str(item) for item in value] if isinstance(value, list) else []


def validate_examples(root: Path) -> list[str]:
    """Return validation errors for showcase scenario structure and evidence."""
    errors: list[str] = []
    known_skills, known_capabilities = _known_names(root)
    examples_root = root / "examples"
    if not (examples_root / "README.md").is_file():
        errors.append("examples/README.md is missing")
    scenario_dirs = [
        path
        for path in sorted(examples_root.glob("[0-9][0-9]-*"))
        if path.is_dir()
    ]
    if len(scenario_dirs) < 5:
        errors.append(f"expected at least 5 numbered example scenarios, found {len(scenario_dirs)}")

    for scenario in scenario_dirs:
        for filename in REQUIRED_FILES:
            if not (scenario / filename).is_file():
                errors.append(f"{scenario.relative_to(root)} missing {filename}")
        prompt = (scenario / "prompt.md").read_text(encoding="utf-8") if (scenario / "prompt.md").exists() else ""
        route = (scenario / "expected-route.md").read_text(encoding="utf-8") if (scenario / "expected-route.md").exists() else ""
        evidence = (scenario / "expected-evidence.md").read_text(encoding="utf-8") if (scenario / "expected-evidence.md").exists() else ""
        for pattern in SHORT_CIRCUIT_PATTERNS:
            if pattern.search(prompt + "\n" + route + "\n" + evidence):
                errors.append(f"{scenario.relative_to(root)} contains short-circuit wording: {pattern.pattern}")
        for term in REQUIRED_ROUTE_TERMS:
            if term not in route:
                errors.append(f"{scenario.relative_to(root)}/expected-route.md missing {term}")
        payload = _route_payload(route, scenario / "expected-route.md")
        for skill in _list_value(payload, "selected_skills"):
            if skill not in known_skills:
                errors.append(f"{scenario.relative_to(root)}/expected-route.md references unknown skill: {skill}")
        for capability in _list_value(payload, "selected_capabilities"):
            if capability not in known_capabilities:
                errors.append(f"{scenario.relative_to(root)}/expected-route.md references unknown capability: {capability}")
        for term in REQUIRED_EVIDENCE_TERMS:
            if term not in evidence:
                errors.append(f"{scenario.relative_to(root)}/expected-evidence.md missing {term}")

    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for example validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    errors = validate_examples(Path(args.root))
    if errors:
        for error in errors:
            print(f"validate-examples: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-examples: validated showcase examples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
