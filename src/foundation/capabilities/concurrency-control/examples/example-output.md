# Example Output

```markdown
## Concurrency Plan

Resource: Subscription seat count.
Invariant: Active seats must not exceed purchased seats.

Control:
- Add unique active membership constraint per user and account.
- Use optimistic version on account_seat_summary.
- Retry once on version conflict, then return conflict with refresh guidance.

Duplicate submit:
- Client sends idempotency key for add-seat action.

Tests:
- Parallel integration test submits two adds for the final seat.
- Exactly one succeeds and summary count remains correct.
```
