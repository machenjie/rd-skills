from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate-capabilities.py"
SCRIPTS_DIR = ROOT / "scripts"
CAPABILITY_117 = (
    ROOT / "src" / "foundation" / "capabilities" / "minimal-correct-implementation" / "SKILL.md"
)


def _load_validate_capabilities() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("validate_capabilities", VALIDATOR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import validate-capabilities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATE_CAPABILITIES = _load_validate_capabilities()


def _capability_117_body() -> str:
    _metadata, _raw_frontmatter, body = VALIDATE_CAPABILITIES.parse_frontmatter(CAPABILITY_117)
    return body


def _remove_top_level_section(body: str, title: str) -> str:
    lines = body.splitlines()
    start = next(
        index for index, line in enumerate(lines) if line.strip() == f"# {title}"
    )
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("# "):
            end = index
            break
    return "\n".join(lines[:start] + lines[end:]) + "\n"


def _run_capability_117_deep_checks(body: str) -> list[str]:
    errors: list[str] = []
    context = str(CAPABILITY_117.relative_to(ROOT))
    VALIDATE_CAPABILITIES._validate_structured_code_correctness_sections(
        "117",
        body,
        context,
        errors,
    )
    VALIDATE_CAPABILITIES._validate_reference_loading_policy(
        "117",
        body,
        context,
        errors,
    )
    return errors


class ValidateCapabilitiesDeepChecksTests(unittest.TestCase):
    def test_capability_117_current_body_satisfies_deep_checks(self) -> None:
        errors = _run_capability_117_deep_checks(_capability_117_body())
        self.assertEqual(errors, [])

    def test_capability_117_missing_reference_loading_policy_fails(self) -> None:
        body = _remove_top_level_section(_capability_117_body(), "Reference Loading Policy")
        errors = _run_capability_117_deep_checks(body)
        self.assertTrue(
            any("Reference Loading Policy" in error for error in errors),
            errors,
        )

    def test_capability_117_missing_evidence_contract_fails(self) -> None:
        body = _remove_top_level_section(_capability_117_body(), "Evidence Contract")
        errors = _run_capability_117_deep_checks(body)
        self.assertTrue(
            any("Evidence Contract" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
