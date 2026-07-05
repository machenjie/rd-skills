# Starter Repo

## Stack

Mixed Python and TypeScript monorepo with API, domain, persistence, UI, and generated client packages.

## Initial State

Architecture rules exist in docs but no CI command enforces import direction, cycle detection, public exports, generated-code exceptions, or forbidden dependencies.

## Files

- `docs/architecture.md`
- `pyproject.toml`
- `package.json`
- `src/domain`
- `src/api`
- `generated/clients`

## Constraints

The starting point intentionally has documented but unenforced module rules. The benchmark expects tool-backed architecture enforcement with migration and exception policy.
