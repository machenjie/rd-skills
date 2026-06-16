# Review Rubric

## Passing Standard

The solution passes when it uses standard library, native runtime support, an
existing utility, or local direct code for simple UTC formatting, or fully
justifies a new dependency with supply-chain evidence.

## Scoring

- 35 percent dependency ladder completeness.
- 25 percent deterministic UTC behavior.
- 20 percent supply-chain and lockfile discipline.
- 15 percent public behavior test coverage.
- 5 percent concise handoff.

## Automatic Failure Conditions

- Date formatting dependency is added without checking the standard library.
- Lockfile changes appear without transitive, license, and vulnerability review.
- Local timezone affects the output.
- Convenience is the only dependency justification.

## Reviewer Notes

The benchmark is intentionally small: a correct answer should usually avoid new
dependency surface while still proving the behavior with a test.
