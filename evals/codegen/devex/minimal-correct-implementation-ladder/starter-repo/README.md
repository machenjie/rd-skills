# Starter Repo

## Stack

Language-agnostic backend module with an order label function and a small test
surface. The benchmark does not require network, database, or package installs.

## Initial State

One owner module contains order label behavior. There may be an existing
formatter helper in the same module. The requested archived suffix is local to
order label rendering.

## Files

- `orders/labels.*` or equivalent owner file for public label behavior.
- `tests/` for public behavior tests.
- Existing helper files may be inspected but should not be widened without evidence.

## Constraints

Keep order behavior in the order owner. Do not create shared utilities, service
classes, factories, registries, or config switches unless current boundary
evidence proves they are necessary.
