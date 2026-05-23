# Review Rubric

## Passing Standard

The implementation must show a safe expand and contract migration path with
working API compatibility during transition. It must avoid production scale
locking risks and provide observable, resumable backfill behavior.

## Scoring

- 25 percent migration safety for phased schema changes, bounded locks, and rollback points.
- 25 percent API compatibility for old client, new client, and mixed write behavior.
- 20 percent backfill quality for batching, checkpoints, idempotency, and restart tests.
- 15 percent observability and delivery planning for progress, stop conditions, and rollback.
- 15 percent data integrity for parsing uncertainty, tenant scope, and source preservation.

## Automatic Failure Conditions

- Full table update runs in one blocking transaction.
- Existing full name clients break during the first release.
- Source full name is dropped or overwritten before cleanup approval.
- Backfill cannot resume safely after interruption.

## Reviewer Notes

Strong solutions separate schema expansion, application compatibility, backfill,
read cutover, and cleanup. Award credit for explicit uncertainty handling in
name parsing and clear stop conditions before risky phases.