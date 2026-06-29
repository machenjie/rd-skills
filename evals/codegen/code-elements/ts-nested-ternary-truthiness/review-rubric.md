# Review Rubric

## Passing Standard

The solution must make UI branch semantics explicit and prove falsey values are
rendered correctly without creating shared helper sprawl.

## Scoring

- 30 percent expression clarity.
- 25 percent truthiness/nullish correctness.
- 25 percent user-visible tests.
- 10 percent feature-local placement.
- 10 percent evidence quality.

## Automatic Failure Conditions

- Keeping nested ternary truthiness behavior.
- Moving local label behavior into a shared helper without consumers.
- Reporting completion without falsey UI tests.
- Testing only private helper internals.

## Reviewer Notes

Strong answers name UI states and test the rendered behavior.

