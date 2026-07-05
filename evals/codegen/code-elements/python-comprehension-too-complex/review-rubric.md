# Review Rubric

## Passing Standard

The solution must make the expression reviewable while preserving returned
record behavior and avoiding broad structural churn.

## Scoring

- 30 percent expression clarity.
- 25 percent behavior preservation.
- 25 percent edge-case tests.
- 10 percent local scope restraint.
- 10 percent evidence quality.

## Automatic Failure Conditions

- Keeping an unreadable nested comprehension with hidden defaults.
- Adding a class or shared helper for one local expression.
- Reporting completion without behavior-preservation tests.
- Changing returned record shape without approval.

## Reviewer Notes

Strong answers split the comprehension only enough to expose the decision rules.

