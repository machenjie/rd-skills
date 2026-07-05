# Review Rubric

## Passing Standard

The solution passes when tests verify public pricing behavior, private helpers remain private, external seams are explicit, and deterministic inputs prevent flaky results.

## Scoring

- 30 percent public behavior boundary: tests cover observable quote outcomes rather than private helper implementation.
- 25 percent seam design: dependency injection or equivalent seam controls customer tier and clock behavior.
- 20 percent test-double selection: fake, stub, mock, spy, contract, and integration choices match the boundary.
- 15 percent fixture ownership: fixtures have local owner, purpose, and change reason.
- 10 percent refactor safety: characterization tests protect existing behavior before structural edits.

## Automatic Failure Conditions

- Private helper is exported, renamed, or made public only for tests.
- Tests mock private call order or assert internal helper calls.
- Tests depend on uncontrolled clock, randomness, UUID, HTTP, file, or environment behavior.
- Shared business fixtures have no owner or reason to change.

## Reviewer Notes

Reward small, explicit seams with production purpose. Penalize broad service locator test hooks or dependency overrides that change production wiring semantics.
