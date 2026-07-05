# Review Rubric

## Passing Standard

The solution must make Go error scope unambiguous and prove failed writes return
errors without expanding transaction behavior.

## Scoring

- 35 percent shadowing fix correctness.
- 25 percent failed-save regression proof.
- 20 percent transaction behavior preservation.
- 10 percent Go idiom quality.
- 10 percent simplicity.

## Automatic Failure Conditions

- Leaving a shadowed err that can hide write failure.
- Swallowing errors or returning success on failure.
- Adding a new transaction wrapper for a local shadowing bug.
- Reporting completion without failed-save test evidence.

## Reviewer Notes

Strong answers keep the patch small and make the exact `err` scope visible.

