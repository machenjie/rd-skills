# Data And API Checklist

- Identify contract consumers and producers.
- Define request, response, DTO, and error model changes.
- Check pagination, sorting, filtering, idempotency, and versioning.
- Plan expand, migrate, backfill, contract, and cleanup phases.
- Check migration locks, table size, indexes, defaults, and nullability.
- Define compatibility tests and contract tests.
- Define rollback for code and data.
- Document deprecation and client migration notes.
- Verify observability for migration and API errors.

## Professional Decision Rules

- Treat the accepted API, event, schema, error, or data-format delta as one producer-to-consumer transition; load the named Reference for compatibility, migration, null/default, version, generated-surface, replay, or rollback decisions.
