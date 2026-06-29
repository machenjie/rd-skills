# Benchmark Prompt

## Task

Fix a JavaScript defaulting bug where a valid falsey value is overwritten.

## Context

The starter repo contains account preference code that uses `value || fallback`.
The product allows `0`, `false`, and empty string in specific fields, so missing
and falsey values must not be conflated.

## Requirements

- Replace truthiness defaulting with semantics that preserve valid falsey values.
- Name the missing-value rule clearly near the owning code.
- Add regression tests for missing, zero, false, and empty string cases.
- Include a Code Element Professionalism Review in the handoff.

## Constraints

- Do not introduce a new dependency for defaulting logic.
- Do not move the preference code to shared utilities.
- Do not change unrelated API or storage behavior.

## Deliverables

- Updated JavaScript implementation.
- Focused regression tests.
- Short evidence note listing the changed expression and validation command.

## Completion Evidence

- Test output showing falsey values are preserved.
- Review note explaining why missing and falsey states differ.

