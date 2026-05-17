# Example Output

```markdown
## Service Logic Plan

Use case:
- Cancel subscription.

Service:
- CancelSubscriptionService owns orchestration for one cancellation request.

Responsibilities:
- Load subscription by id.
- Check actor can cancel this subscription.
- Start transaction.
- Call Subscription.cancel(reason, requestedAt) for invariant enforcement.
- Persist subscription and write SubscriptionCanceled event to outbox.
- Commit transaction.

Not owned by service:
- HTTP status mapping.
- Lifecycle invariant definitions.
- Storage-specific query construction.

Failure handling:
- Already canceled maps to domain conflict.
- Permission denial happens before state mutation.
```
