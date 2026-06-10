# Review Rubric

## Passing Standard

The solution passes when it adds the small rule through the existing cohesive
owner or through one clearly justified boundary, keeps private helpers
co-located when cohesive, avoids navigation cost regression, and proves behavior
through public tests.

## Scoring

- 30 percent file granularity: keep-in-existing-file alternative considered,
  private helpers co-located when cohesive, and no one-function file artifacts.
- 25 percent boundary rationale: any new file names a real owner, lifecycle,
  invariant, collaborator, side-effect, public contract, test, generated, or
  external protocol boundary.
- 20 percent clarity: main cancellation flow remains readable and navigation
  cost before/after does not regress.
- 15 percent tests: public behavior tests cover new, existing, denied, and edge
  cancellation outcomes without importing private helpers.
- 10 percent local convention: names, placement, and test structure match the
  existing service/use-case module.

## Automatic Failure Conditions

- Creates micro-file sprawl: several tiny policy/helper/adapter/options files
  for one cohesive cancellation rule.
- Creates an excessive file split where a private helper, predicate, mapper, or
  constant becomes its own file without a real boundary.
- Creates a one-function file without boundary.
- Creates a trivial class file or pass-through glue file that only delegates
  back to the original service or policy.
- Exports or tests private helpers instead of proving public behavior.
- Makes the main business decision require more file jumps with no independent
  owner, lifecycle, invariant, public contract, side-effect boundary, or change
  reason.

## Reviewer Notes

Reward small, readable co-location when the owner is real and cohesive. Penalize
code that looks neatly decomposed but forces maintainers to navigate through
tiny files to understand one rule. A new file is acceptable only when its
boundary would still be obvious during the next adjacent change.
