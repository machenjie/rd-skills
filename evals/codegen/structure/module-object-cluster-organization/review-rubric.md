# Review Rubric

## Passing Standard

The solution passes when the order cancellation module is a cohesive object
graph with a minimal public facade, private internals, explicit dependency
direction, and public behavior tests.

## Scoring

- 30 percent module internal composition plan.
- 25 percent module object graph and internal dependency direction.
- 20 percent public facade and private internals discipline.
- 15 percent public behavior and contract tests.
- 10 percent next-change location and local convention fit.

## Automatic Failure Conditions

- Creates one directory per object without module cohesion.
- Puts business logic in shared/common.
- Exposes internals as public API.
- Module contains unrelated object families.
- No object graph or internal dependency direction is declared.

## Reviewer Notes

Reward structures that make the next cancellation rule obvious. Penalize clean
folder shapes that have no coherent module ownership or leak internals.
