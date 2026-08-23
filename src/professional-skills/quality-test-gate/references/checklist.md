# Quality Checklist

- Map each acceptance criterion and material failure path to one proving signal.
- Map each acceptance criterion to evidence.
- Choose unit tests for pure logic and edge cases.
- Choose integration tests for persistence, services, permissions, and jobs.
- Choose contract tests for API and external boundaries.
- Choose E2E tests for critical user flows.
- Include migration, rollback, and data repair tests when needed.
- Review fixture realism and mock boundaries.
- Consume exact commands, expected signals, and combined coverage from `targeted-validation-selection`; keep proof admissibility and pass criteria with this gate.
- Record residual risk and manual verification.

## Professional Decision Rules

- Own proof strategy and acceptance-to-signal mapping before command selection.
- Use `targeted-validation-selection` only after strategy selection, and only for repository-defined command and coverage selection.
- Leave evidence timing and refresh decisions to Core Guard G and the validation-freshness contract.
- Map scoped acceptance and material risk to the smallest test levels that exercise the regression and negative mechanisms under deterministic controls.

## High-Value Gotchas

- A broad green suite can miss the changed mechanism.
- A result becomes stale after a material source, test, fixture, schema, or config edit.
- Lint, type checks, and manual inspection do not substitute for behavior proof.

## Execution Checklist

1. Select strategy before commands.
2. **Analysis mode:** Map acceptance to proof.
3. **Task mode:** Add the smallest proving test.
4. **Review mode:** Judge coverage and freshness.
5. Stop when changed behavior or acceptance remains unverified.
