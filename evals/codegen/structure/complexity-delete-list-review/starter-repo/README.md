# Starter Repo

## Stack

Language-agnostic billing rule module with generated-review pressure. No
external service, database, or package install is required.

## Initial State

The repository has one public billing rule. A generated patch may introduce
delegating wrappers, unused config options, and speculative interfaces.

## Files

- `billing/rules.*` or equivalent public billing rule owner.
- `tests/` for regression behavior.
- Review artifacts may be Markdown or structured comments.

## Constraints

Do not remove behavior without caller search and regression evidence. Do not
keep wrapper-only delegation, one-implementation interfaces, or future-proof
factories without current force.
