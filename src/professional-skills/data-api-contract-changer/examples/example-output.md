# Example Output

Contract change: Add optional `archived_at` timestamp to project responses.

Compatibility: Field is additive and nullable. Existing clients can ignore it.

Migration: Expand schema with nullable column, deploy writer, backfill historical archived records, then expose field.

Tests: migration test, response contract test, idempotent archive retry test.

Rollback: Leave column in place and disable response serialization if needed.
