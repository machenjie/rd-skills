# Example Output

```markdown
## Query Optimization Plan

Query: List open support tickets for an account ordered by last_activity_at desc.

Predicates:
- account_id equals current account.
- status in open, pending.
- order by last_activity_at desc with keyset cursor.

Index:
- Create composite index on account_id, status, last_activity_at desc, id.
- Reject index on status alone because status cardinality is low.

Cost:
- Adds one write-maintained index to tickets.
- Build online during low traffic and monitor lock waits.

Verification:
- Confirm plan uses composite index and rows scanned stays near page size.
```
