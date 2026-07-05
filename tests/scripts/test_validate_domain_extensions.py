from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate-domain-extensions.py"
SCRIPTS_DIR = ROOT / "scripts"


def _load_validate_domain_extensions() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("validate_domain_extensions", VALIDATOR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import validate-domain-extensions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATE_DOMAIN_EXTENSIONS = _load_validate_domain_extensions()


class ValidateDomainExtensionSemanticsTests(unittest.TestCase):
    def test_domain_reference_policy_must_index_references(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            extension_dir = Path(raw) / "payment-trading-extension"
            (extension_dir / "references").mkdir(parents=True)
            (extension_dir / "references" / "checklist.md").write_text("# Checklist\n", encoding="utf-8")
            body = """
## Strong Domain Signals
- payment flow changes
- subscription state changes
- refund behavior changes
- ledger entry changes
- webhook processing changes

## Weak Signals That Are Not Enough
Do not load only because a word matches unless domain behavior can change.

## Required Professional Owner Skill
- backend-change-builder

## Domain Reference Loading Policy
Do not load all domain references by default. Load only after a primary professional owner and strong domain signal. Do not load for keyword-only mentions.
"""

            errors: list[str] = []
            VALIDATE_DOMAIN_EXTENSIONS._validate_domain_section_semantics(
                body,
                "domain/SKILL.md",
                extension_dir,
                {"backend-change-builder"},
                errors,
            )

        self.assertTrue(any("references/checklist.md" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
