# Review Rubric

## Passing Standard

The solution must eliminate shared mutable default state while preserving the
documented public behavior and proving repeated calls are isolated.

## Scoring

- 35 percent default/lifetime correctness.
- 25 percent regression tests for repeated calls.
- 20 percent Python idiom and simplicity.
- 10 percent caller-owned list semantics.
- 10 percent handoff evidence.

## Automatic Failure Conditions

- Keeping a mutable list or dict as a default argument.
- Adding a new class or helper module for the local default fix.
- Reporting completion without repeated-call regression evidence.
- Changing public API shape without compatibility rationale.

## Reviewer Notes

Strong answers keep the fix local and state whether explicit caller lists are
copied, extended, or returned unchanged.

