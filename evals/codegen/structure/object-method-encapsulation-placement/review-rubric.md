# Review Rubric

## Passing Standard

The solution passes when it classifies object candidates first, moves only
invariant/lifecycle/state behavior into objects, keeps orchestration and side
effects in the proper boundaries, and proves behavior through public tests.

## Scoring

- 30 percent object candidate classification and rejected alternatives.
- 25 percent method placement evidence tied to state, invariant, lifecycle, or
  collaborator ownership.
- 20 percent side-effect boundary preservation for adapters and repositories.
- 15 percent public behavior tests without private helper exports.
- 10 percent clarity and naming consistency with local conventions.

## Automatic Failure Conditions

- Creates a helper-bag object.
- Creates an anemic object with getters/setters only.
- Moves a method to an object without state, invariant, lifecycle, or
  collaborator evidence.
- Exports private helpers for tests.
- Hides infrastructure dependency in a domain object.

## Reviewer Notes

Reward small local helpers when they are the honest structure. Penalize object
ceremony that hides procedural code or moves infrastructure inward.
