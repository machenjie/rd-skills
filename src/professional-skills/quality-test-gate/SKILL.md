---
name: quality-test-gate
description: "Use `analysis-agent` to map acceptance to validation, `task-agent` to add or run bounded tests, and `review-agent` to assess proof coverage. Skip work with no material change or already-fresh complete validation."
---

# quality-test-gate

## Role

Support `analysis-agent`, `task-agent`, and `review-agent` for bounded acceptance-to-validation work.

- **Analysis mode (`analysis-agent`):** Map acceptance and failure paths to proving signals.
- **Task mode (`task-agent`):** Add or repair the smallest proving test.
- **Review mode (`review-agent`):** Judge proof coverage and freshness for changed behavior.

## When To Use

- changed behavior needs proof
- validation freshness required

## Do Not Use

- no material change
- validation already fresh and complete

## Required Inputs

- observable acceptance and non-goals
- validation entry points material risks and execution constraints
- **Analysis mode (`analysis-agent`):** current behavior, existing tests, and uncovered acceptance risks.
- **Task mode (`task-agent`):** changed paths, regression mechanism, and repository validation entry points.
- **Review mode (`review-agent`):** changed behavior, supplied proof, and freshness marker.

## Professional Decision Rules

- Own proof strategy and acceptance-to-signal mapping before command selection.
- Use `targeted-validation-selection` only after strategy selection, and only for repository-defined command and coverage selection.
- Leave evidence timing and refresh decisions to Core Guard G and the validation-freshness contract.
- For scoped acceptance and material risks, define an acceptance-and-risk-to-test-level mapping using the smallest sufficient levels.
- Test the regression mechanism and relevant negative path, not only the happy path.
- Control time, randomness, concurrency, data, network, and global state.
- Add broader validation only for a concrete shared boundary or escape risk.

## High-Value Gotchas

- A broad green suite can miss the changed mechanism.
- A result becomes stale after a material source, test, fixture, schema, or config edit.
- Mock-heavy tests can prove the mock instead of the real boundary.
- Lint, type checks, and manual inspection do not substitute for behavior proof.

## Execution Checklist

1. Map each acceptance criterion and material failure path to one proving signal.
2. Choose the smallest sufficient test level from the real boundary and regression mechanism.
3. Verify freshness, deterministic control, changed-file coverage, and negative-path evidence.
4. **Analysis mode:** select the smallest sufficient test level.
5. **Task mode:** add the smallest proving test at the regression boundary.
6. **Review mode:** judge changed-file, negative-path, and acceptance coverage.
7. Stop closure when any changed behavior or acceptance remains unverified.

## Stop / Escalation Conditions

- Stop before validation that mutates production data or exceeds authority.
- Escalate when money, permission, migration, public contract, external effects,
  concurrency, rollback, or security lacks a specific negative or boundary test.
- Escalate flaky, skipped, or partial evidence without an owner and release consequence.
- Flag every unverified changed file or acceptance criterion.

## Output Contract

- **Analysis mode (`analysis-agent`):** validation strategy; acceptance-to-signal mapping; uncovered acceptance.
- **Task mode (`task-agent`):** proving test change; covered behavior; remaining regression risk.
- **Review mode (`review-agent`):** coverage verdict; uncovered changed behavior; stale or missing proof.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Ordinary acceptance-to-test mapping needs a compact checklist | The root checklist already covers the bounded change | analysis-agent, task-agent, review-agent | checklist-result, validation-plan |
| [index](references/index.md) | index | competing quality test gate references require dependency, conflict, or output-fragment selection | the quality test gate root or a task-named reference already resolves selection | analysis-agent, task-agent, review-agent | reference-selection |
| [test output and gates](references/test-output-and-gates.md) | targeted | Migration, security, release, concurrency, or multi-boundary proof needs deeper calibration | A local targeted test is sufficient | analysis-agent, task-agent, review-agent | gate-decision, residual-risk |
| [test structure boundaries](references/test-structure-boundaries.md) | targeted | Fixtures, mocks, golden data, shared helpers, private access, or test placement affect correctness | No test-structure decision exists | analysis-agent, task-agent, review-agent | validation-plan, proof-limit |
