---
name: quality-test-gate
description: "Use `analysis-agent` to map acceptance to validation, `task-agent` to add or run bounded tests, and `review-agent` to assess proof coverage. Skip work with no material change or already-fresh complete validation."
---

# quality-test-gate

## Role

Map acceptance and failure paths to proving signals.

- **Analysis mode (`analysis-agent`):** Select the proof strategy.
- **Task mode (`task-agent`):** Implement the smallest proving test.
- **Review mode (`review-agent`):** Judge coverage and freshness.

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

- Map each acceptance and material failure to one signal.
- Select the lowest level exercising the real boundary.
- Record stale, flaky, skipped, or partial evidence as limited.

## High-Value Gotchas

- A broad green suite can miss the changed mechanism.
- A mock or stale result can prove the harness instead of current behavior.

## Execution Checklist

- **Analysis mode:** Map acceptance and material failure paths to test levels.
- **Task mode:** Implement the smallest proving test and capture its current result.
- **Review mode:** Judge changed-file, negative-path, and freshness coverage.
- Record unproved scope with its owner and release consequence.

## Stop / Escalation Conditions

- Stop before production mutation or authority overrun.
- Escalate unowned flaky, skipped, or partial evidence.
- Flag uncovered changed files or acceptance.

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
