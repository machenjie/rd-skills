# Starter Repo

## Stack

Python API service with SQL migration files, repository layer, batch job module,
and pytest tests. The database target is relational and the benchmark assumes
large table operational constraints even when tests use a local fixture.

## Initial State

The `customers` table has `id`, `full_name`, `email`, `updated_at`, and tenant
fields. API serializers read and write only `full_name`. There is no migration
phase plan, no backfill job, and no compatibility tests for split fields.

## Files

- `db/migrations/` contains existing linear migration files.
- `customers/api.py` handles old profile request and response shapes.
- `customers/repository.py` reads and writes customer records.
- `jobs/backfill_customer_names.py` is a placeholder batch job.
- `tests/test_customer_name_contract.py` covers current full name behavior.

## Constraints

Keep source `full_name` data until the final contract phase. Any parsing logic
must preserve original value and expose uncertainty for manual or product level
resolution instead of silently corrupting names.