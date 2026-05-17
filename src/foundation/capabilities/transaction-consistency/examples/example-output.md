# Example Output

```markdown
## Consistency Plan

Invariant: An account balance must not go below zero when reserving funds.

Transaction Boundary:
- Read account balance for update.
- Insert reservation row.
- Decrement available balance.
- Commit before publishing reservation_created event.

Isolation and Locks:
- Use row-level lock on account balance.
- Timeout after 2 seconds and return retryable conflict.

Distributed Work:
- Do not call payment provider inside the transaction.
- Publish event through outbox after local commit.

Tests:
- Concurrent reservations cannot overdraw the account.
```
