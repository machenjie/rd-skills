#!/usr/bin/env python3
"""Validate optional cross-agent aids without imposing a task protocol."""
from pathlib import Path
from validation_utils import CORE_CONTRACTS, fail_many, validate_core_contracts
ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "src/control-skills/engineering-control-plane/references"

def validate_templates(reference_root=REFERENCE_ROOT):
    errors = []
    required = {
        "direct-task-template.md": ["optional", "authorized write scope", "bounded search/read"],
        "engineering-brief-template.md": ["only when complex cross-agent", "## Goal", "## Important Constraints and Invariants", "## Key Decisions", "## Validation", "## Unresolved Issues"],
        "implementation-handoff-template.md": ["optional", "final material edit", "skipped", "proof limits"],
        "review-handoff-template.md": ["concrete defect", "reachable failure mechanism", "required action", "new material question"],
        "task-dag-template.md": ["real dependencies", "blocking edge", "serial writes", "Host-provided isolation"],
        "utility-capsule-template.md": ["observable result", "workspace state before and after", "Partial observations remain partial"],
    }
    for name, terms in required.items():
        path = reference_root / name
        if not path.is_file():
            errors.append(f"missing optional aid {name}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in terms:
            if term not in text:
                errors.append(f"{name}: missing {term!r}")
        if any(term in text for term in ("execution-level/v2", "Effective Level", "Scope Lineage", "Canonical Finding")):
            errors.append(f"{name}: retired execution protocol")
    return errors

def main():
    return fail_many("validate-task-contracts", [*validate_core_contracts(CORE_CONTRACTS), *validate_templates()])

if __name__ == "__main__":
    raise SystemExit(main())
