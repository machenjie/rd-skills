#!/usr/bin/env python3
"""Validate the behavioral safeguards in the authoritative control prompt."""
from pathlib import Path
from validation_utils import fail_many, count_o200k_base_tokens

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "src/control-prompts/main-control-agent.md"
PROMPT_MAX_O200K_BASE_TOKENS = 1750
REQUIRED_BEHAVIOR = (
    "Implementation requests default to task-agent with read/search/edit/execute",
    "Unknown local owner, files, tests, or callers require bounded discovery",
    "exactly one Primary Professional Skill and zero to three authorized Layer 3 Skills",
    "positive and anti-trigger routing",
    "Do not repeat analysis or redesign without new decision-relevant evidence",
    "Engineering Brief only when complex cross-agent work needs stable engineering decisions",
    "Formalize only when a real consumer or hard boundary needs it",
    "Normal repository read/search may expand as needed",
    "write scope and destructive, production, privileged",
    "untrusted input reaching executable sinks",
    "current requirements or repository evidence",
    "After the final material edit, require fresh validation",
    "Independent review is optional",
    "Re-review only if the repair introduces a new question",
    "No mandatory professional-risk matrix",
)
RETIRED_REQUIREMENTS = ("effective_level", "scope-lineage", "L5 confirmation", "Review Round ID", "Re-review Classification", "Canonical Finding", "Semantic Repair Convergence")

def validate_prompt(text: str) -> list[str]:
    errors = []
    for term in REQUIRED_BEHAVIOR:
        if term not in text:
            errors.append(f"control prompt lacks behavioral safeguard: {term}")
    for term in RETIRED_REQUIREMENTS:
        if term.casefold() in text.casefold():
            errors.append(f"control prompt includes retired machinery: {term}")
    if count_o200k_base_tokens(text) > PROMPT_MAX_O200K_BASE_TOKENS:
        errors.append("control prompt exceeds its runtime context budget")
    return errors

def main() -> int:
    return fail_many("validate-control-plane-prompt", validate_prompt(PROMPT.read_text(encoding="utf-8")))

if __name__ == "__main__":
    raise SystemExit(main())
