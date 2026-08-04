#!/usr/bin/env python3
"""Validate the hookless ChangeForge source boundary as one composite gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ALLOWED_SOURCE_ROOTS = {
    "agent-profiles",
    "control-prompts",
    "control-model",
    "control-skills",
    "domain-extensions",
    "foundation",
    "professional-skills",
    "registry",
}
VALIDATORS = (
    "validate-registry.py",
    "validate-control-skills.py",
    "validate-agent-profiles.py",
    "validate-control-plane-prompt.py",
    "validate-task-contracts.py",
    "validate-skill-routing.py",
    "validate-hookless-residue.py",
)


def main() -> int:
    actual = {path.name for path in SRC.iterdir() if path.is_dir()}
    errors: list[str] = []
    unexpected = sorted(actual - ALLOWED_SOURCE_ROOTS)
    missing = sorted(ALLOWED_SOURCE_ROOTS - actual)
    if unexpected:
        errors.append(f"unexpected src roots: {', '.join(unexpected)}")
    if missing:
        errors.append(f"missing src roots: {', '.join(missing)}")
    for path in SRC.rglob("__pycache__"):
        errors.append(f"generated cache in source: {path.relative_to(ROOT)}")

    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / validator)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            errors.append(f"{validator} failed: {detail}")

    if errors:
        for error in errors:
            print(f"validate-src-invariants: ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "validate-src-invariants: hookless source contains only static control models, "
        "prompts, profiles, registries, and three-layer Skill authoring assets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
