# Example Output

```markdown
## Data Model Proposal

Entity: Subscription
Owner: Subscription Management module.

Invariants:
- One active subscription per account.
- canceled_at is required when status is canceled.
- plan_id must reference an active plan at activation time.

Relationships:
- account_id one-to-many subscription history.
- current_plan_snapshot is stored for historical billing accuracy.

Query patterns:
- Fetch active subscription by account_id.
- List subscription history by account_id ordered by effective_at.

Contract separation:
- API returns SubscriptionDTO.
- Internal table names and historical snapshots are not public contract.

Migration risk:
- Existing accounts require backfill with guarded uniqueness checks.
```
