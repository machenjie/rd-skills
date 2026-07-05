# Example Output

```markdown
## Migration Plan

Goal: Backfill subscription.current_plan_snapshot.

Phases:
- Expand: Add nullable current_plan_snapshot column.
- Migrate: Backfill in batches of 1,000 subscriptions ordered by id.
- Contract: Require new writes to populate snapshot after validation passes.
- Cleanup: Add not-null constraint after old writers are gone.

Guards:
- Skip rows with existing snapshot.
- Store last processed id checkpoint.

Observability:
- Emit processed, updated, skipped, failed, and duration metrics.
- Alert on error rate above threshold.

Rollback:
- Disable reader flag to ignore snapshot.
- Preserve column until cleanup window.

Validation:
- Count active subscriptions missing snapshot by tenant.
```
