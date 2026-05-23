# Security Checks

## Threat Surface

The migration touches customer identity data, tenant scoped records, operational
jobs, and deployment sequencing. Risks include data corruption, cross tenant
updates, accidental exposure in logs, and unsafe rollback decisions.

## Required Checks

- Ensure backfill queries preserve tenant boundaries and do not cross update records.
- Redact customer names from routine job logs and metrics labels.
- Validate migration and rollback commands target the intended database environment.
- Keep original full name until cleanup approval and compatibility evidence exists.
- Confirm job retries are idempotent and do not overwrite newer user edits.

## Rejection Cases

- Any migration that drops full name before compatibility and backfill evidence.
- Any backfill job that updates all tenants without scoped or resumable batching.
- Any routine log output that dumps customer names or full row payloads.
- Any rollback plan that depends on destructive restore for normal deployment failure.