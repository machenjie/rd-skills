# Starter Repo

## Stack

Language-agnostic utility module for formatting one UTC date string. No package
installation is required for the starter repository.

## Initial State

The repository has a small reporting utility area and may already have a date
formatting helper. The requested behavior is deterministic UTC formatting for a
fixed timestamp.

## Files

- `reports/date_format.*` or equivalent utility owner.
- `tests/` for public behavior tests.
- Lockfiles should remain unchanged unless a dependency is justified.

## Constraints

Use standard library or native runtime support when sufficient. Avoid local
timezone assumptions, new packages, and lockfile churn for convenience.
