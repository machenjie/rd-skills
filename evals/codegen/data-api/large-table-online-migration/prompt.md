# Benchmark Prompt

## Task

Design and implement an online migration that splits `customers.full_name` into
`first_name` and `last_name` for a table with more than ten million rows while
keeping API clients compatible.

## Context

The customer table serves read and write traffic during business hours. Current
API clients send and receive `full_name`. New clients need `first_name` and
`last_name`. The migration must avoid long table locks, allow safe backfill,
and support rollback before final cleanup.

## Requirements

- Use an expand and contract migration sequence.
- Add nullable columns and write compatibility before backfill.
- Backfill in bounded batches with progress tracking and resumability.
- Support dual read and dual write during the transition.
- Preserve `full_name` behavior for existing API clients until final contract phase.
- Add tests for old clients, new clients, mixed writes, backfill restart, and rollback.

## Constraints

- Do not run a single blocking update across the full table.
- Do not drop `full_name` in the same release that introduces split fields.
- Do not make parsing assumptions that corrupt mononyms or complex names silently.

## Deliverables

- Migration files, backfill job, API compatibility changes, tests, and rollout notes.
- Observability plan for backfill progress, errors, and read or write mismatches.
- Rollback plan for each phase before final cleanup.

## Completion Evidence

- Passing migration, API contract, and backfill restart tests.
- Query or migration review showing bounded locks and batch behavior.
- Deployment sequence with stop conditions and rollback instructions.