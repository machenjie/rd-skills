# Review Rubric

## Passing Standard

The solution passes when it declares the object relationship type, keeps parent
and sibling roles honest, prevents internal access between peers, and proves
behavior through public tests.

## Scoring

- 30 percent relationship classification and direction.
- 25 percent parent-child or sibling responsibility evidence.
- 20 percent forbidden internal access and dependency-direction preservation.
- 15 percent public behavior tests across lifecycle outcomes.
- 10 percent clarity and local naming convention.

## Automatic Failure Conditions

- Parent becomes a pass-through dumping ground.
- Siblings call each other's internals.
- Split is based only on method names.
- No relationship type is declared.
- Shared behavior moves to shared/common without ownership.

## Reviewer Notes

Look for relationship evidence before file movement. A smaller service is not a
win if object collaboration becomes leaky or harder to reason about.
