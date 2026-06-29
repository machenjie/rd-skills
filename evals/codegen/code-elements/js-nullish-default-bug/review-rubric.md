# Review Rubric

## Passing Standard

The implementation must preserve valid falsey values while still applying the
fallback for truly missing values. It must include focused regression evidence
and avoid broad helper or dependency additions.

## Scoring

- 35 percent default/nullish semantic correctness.
- 25 percent focused regression tests.
- 20 percent local expression readability.
- 10 percent no unnecessary helper or dependency.
- 10 percent handoff evidence quality.

## Automatic Failure Conditions

- Keeping value-or-fallback truthiness defaulting.
- Adding a generic helper in shared utils for one local expression.
- Reporting completion without a falsey-value regression test.
- Changing unrelated API or storage behavior.

## Reviewer Notes

Strong answers make missing versus falsey semantics explicit and keep the fix
close to the owning preference code.

