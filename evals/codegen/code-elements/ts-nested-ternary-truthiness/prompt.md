# Benchmark Prompt

## Task

Replace a nested TypeScript ternary that also relies on truthiness defaults.

## Context

The starter repo has UI label logic that uses nested ternaries and `value ||`
fallback behavior. A valid empty label and zero count are being misrendered.

## Requirements

- Split or name the conditional branches so the UI states are explicit.
- Preserve valid falsey values.
- Add tests for empty label, zero count, missing value, and disabled state.
- Include code-element and frontend test evidence.

## Constraints

- Do not move the logic into a global shared UI helper.
- Do not change visual states outside the label behavior.
- Do not add a dependency.

## Deliverables

- Updated TypeScript implementation.
- User-visible behavior tests.
- Handoff with expression and truthiness review.

## Completion Evidence

- Test output for falsey and missing values.
- Review note showing each conditional branch.

