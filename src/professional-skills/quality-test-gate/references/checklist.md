# Quality Checklist

- Map each acceptance criterion and material failure path to one proving signal.
- Map each acceptance criterion to evidence.
- Choose unit tests for pure logic and edge cases.
- Choose integration tests for persistence, services, permissions, and jobs.
- Choose contract tests for API and external boundaries.
- Choose E2E tests for critical user flows.
- Include migration, rollback, and data repair tests when needed.
- Review fixture realism and mock boundaries.
- Consume repository-defined commands, expected signals, and combined coverage only after proof strategy is fixed; keep proof admissibility and pass criteria with this capability.
- Record residual risk and manual verification.

## Professional Decision Rules

- Own proof strategy and acceptance-to-signal mapping before command selection.
- Select repository-defined commands and coverage only after strategy selection.
- Treat any material source, test, fixture, schema, or configuration edit as invalidating earlier validation evidence; refresh affected checks after the latest edit.
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
