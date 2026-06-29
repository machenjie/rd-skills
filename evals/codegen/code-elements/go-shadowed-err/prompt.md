# Benchmark Prompt

## Task

Fix a Go `err` shadowing bug in a transactional write path.

## Context

The starter repo has an outer `err` checked after a transaction block, but an
inner `err :=` shadows it inside the block.

## Requirements

- Remove or justify shadowing so write failures cannot be missed.
- Preserve transaction rollback behavior.
- Add a regression test for a failed save.
- Include code-element and Go idiom evidence.

## Constraints

- Do not broaden the transaction scope.
- Do not swallow errors or return success on failure.
- Do not introduce a new transaction wrapper.

## Deliverables

- Updated Go implementation.
- Regression test for failed save.
- Handoff with shadowing and validation evidence.

## Completion Evidence

- Test output proving failed save returns an error and rolls back.
- Review note naming the shadowed variable and scope.

