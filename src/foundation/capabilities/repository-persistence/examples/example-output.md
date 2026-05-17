# Example Output

```markdown
## Repository Contract

Repository:
- SubscriptionRepository

Methods:
- getById(subscriptionId): returns Subscription or NotFound.
- save(subscription): persists aggregate changes inside caller transaction.
- listActiveByAccount(accountId, cursor): returns stable page ordered by renewal date and id.

Boundary:
- Does not return ORM entities.
- Does not expose query builders.
- Maps storage status values to SubscriptionStatus value object.

Transaction expectations:
- save must run inside CancelSubscriptionService transaction.
- getByIdForUpdate is required for cancellation to prevent concurrent transition races.

Errors:
- Unique constraint violation maps to DuplicateSubscription.
- Storage timeout maps to RetryablePersistenceFailure.
```
